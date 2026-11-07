from labagent.exec_graph import run_traced
from labagent.executor import Fault, find_step
from labagent.schema import Protocol
from labagent.tracing import flush

PLAN = Protocol.model_validate({
    "liquids": {"buffer": {"name": "buffer"}},
    "steps": [
        {"op": "transfer", "liquid": "buffer", "volume_ul": 20, "source": "D1:A1", "dest": "D2:A1"},
        {"op": "transfer", "liquid": "buffer", "volume_ul": 20, "source": "D1:A1", "dest": "D2:B1"},
        {"op": "move_plate", "plate": "pcr1", "from_zone": "pre_pcr",
         "to_zone": "thermocycler", "sealed": True, "speed": "slow"},
    ],
})
CASES = [("module_timeout", 1, "D"), ("pick_failed", None, "D"),
         ("contamination", None, "C"), ("short_aspiration", None, "D")]
for ft, k, strat in CASES:
    r = run_traced(PLAN, Fault(ft, find_step(PLAN, ft), k), strat)
    print(ft, k, strat, r["status"], r["actions"])
flush()