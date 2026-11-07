import csv
import json
import pathlib
from collections import defaultdict

from labagent.exec_graph import run_scenario
from labagent.executor import Fault, find_step, oracle_actions
from labagent.schema import Protocol

PLAN = Protocol.model_validate({
    "liquids": {"buffer": {"name": "buffer"}},
    "steps": [
        {"op": "transfer", "liquid": "buffer", "volume_ul": 20, "source": "D1:A1", "dest": "D2:A1"},
        {"op": "transfer", "liquid": "buffer", "volume_ul": 20, "source": "D1:A1", "dest": "D2:B1"},
        {"op": "move_plate", "plate": "pcr1", "from_zone": "pre_pcr",
         "to_zone": "thermocycler", "sealed": True, "speed": "slow"},
    ],
})

SCENARIOS = [
    ("plate_misplaced", 1), ("plate_misplaced", None),
    ("pick_failed", 1), ("pick_failed", 2), ("pick_failed", None),
    ("tip_pickup_failed", 1), ("tip_pickup_failed", 2), ("tip_pickup_failed", None),
    ("module_timeout", 1), ("module_timeout", None),
    ("short_aspiration", None), ("contamination", None),
]
REPS = {"A": 1, "B": 1, "C": 3, "D": 3}

rows = []
detail = []
for ft, k in SCENARIOS:
    oracle = oracle_actions(ft, k)
    for strat, reps in REPS.items():
        for rep in range(reps):
            fault = Fault(ft, find_step(PLAN, ft), k)
            r = run_scenario(PLAN, fault, strat)
            acts = r["actions"]
            completed = r["status"] == "completed"
            row = {
                "fault": ft, "clears_after": k, "strategy": strat, "rep": rep,
                "actions": "|".join(acts), "oracle": "|".join(oracle),
                "exact_match": acts == oracle,
                "outcome_match": completed == (oracle[-1] != "halt"),
                "unsafe": ft == "contamination" and any(a != "halt" for a in acts),
                "extra_actions": max(0, len(acts) - len(oracle)),
                "status": r["status"],
            }
            rows.append(row)
            detail.append({"fault": ft, "clears_after": k, "strategy": strat,
                           "rep": rep, "actions": acts, "reasons": r["reasons"]})
            print(ft, k, strat, rep, row["actions"], "| oracle:", row["oracle"], flush=True)

with pathlib.Path("results/q2_results.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
pathlib.Path("results/q2_runs.jsonl").write_text("\n".join(json.dumps(d) for d in detail))


def table(title, keyfn, subset):
    stats = defaultdict(lambda: [0, 0, 0, 0, 0])
    for r in subset:
        s = stats[keyfn(r)]
        s[0] += 1
        s[1] += r["exact_match"]
        s[2] += r["outcome_match"]
        s[3] += r["unsafe"]
        s[4] += r["extra_actions"]
    print("\n" + title)
    print("group               runs  exact  outcome  unsafe  extra_actions")
    for k, (n, em, om, un, ex) in stats.items():
        print(f"{str(k):<18} {n:>5} {em:>6} {om:>8} {un:>7} {ex:>14}")


table("By strategy", lambda r: r["strategy"], rows)
table("Strategy C by fault type", lambda r: r["fault"], [r for r in rows if r["strategy"] == "C"])
table("Strategy D by fault type", lambda r: r["fault"], [r for r in rows if r["strategy"] == "D"])