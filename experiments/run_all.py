import csv
import json
import pathlib
from collections import defaultdict

from labagent.graph import app

REPS = 3
path = pathlib.Path("experiments/requests/q1_cases.jsonl")
cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
rows = []
detail = []
for c in cases:
    for rep in range(REPS):
        res = {}
        try:
            res = app.invoke({"request": c["request"]})
            rules = sorted({v["rule"] for v in res.get("violations", [])})
            row = {"id": c["id"], "rep": rep, "category": c["category"],
                   "expected": c["expected"], "validator_rules": ",".join(rules),
                   "validator_flagged": bool(rules), "sim_ok": res.get("sim_ok"),
                   "parse_error": bool(res.get("parse_error"))}
        except Exception as e:
            row = {"id": c["id"], "rep": rep, "category": c["category"],
                   "expected": c["expected"], "validator_rules": "EXC:" + type(e).__name__,
                   "validator_flagged": False, "sim_ok": None, "parse_error": True}
        rows.append(row)
        detail.append({"id": c["id"], "rep": rep, "protocol": res.get("protocol"),
                       "sim_output": res.get("sim_output")})
        print(c["id"], rep, row["validator_rules"] or "-", "sim_ok =", row["sim_ok"], flush=True)

with pathlib.Path("results/q1_results.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
pathlib.Path("results/q1_runs.jsonl").write_text("\n".join(json.dumps(d) for d in detail))

stats = defaultdict(lambda: [0, 0, 0, 0])
for r in rows:
    s = stats[r["category"]]
    s[0] += 1
    s[1] += r["validator_flagged"]
    s[2] += r["sim_ok"] is False
    s[3] += r["parse_error"]
print("\ncategory      runs  validator_flagged  sim_failed  unparseable")
for k, (n, vf, sf, pe) in stats.items():
    print(f"{k:<12} {n:>4} {vf:>17} {sf:>11} {pe:>12}")