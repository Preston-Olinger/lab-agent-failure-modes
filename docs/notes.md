## Q1 results (30 requests x 3 runs)
v1 (original rules): simulator caught 0/60 lab-practice flaws; validator caught 58/60.
Simulator caught 10/12 API errors; 2 runs were empty plans (silent refusals).
Misses: t3 (AI labeled samples role=other, so R3 skipped them); a3 (empty plan).
v2 (R3 generalized, R9 added AFTER seeing v1): validator 60/60; API errors: 11 by simulator + 1 empty plan flagged by R9.
Caveat: rules were revised after seeing results and test cases were written around the rules, so v2 is optimistic.
## Q2 results (12 fault scenarios; strategy C x3 reps)
Exact match to oracle: A 1/12, B 6/12, C 21/36. Right final outcome: A 5/12, B 11/12, C 30/36.
Unsafe on contamination: B 1/1, C 3/3 (replan, then halt). Only A was safe.
C behaves like a uniform "retry once then halt"; it matched the oracle on plate/thermocycler faults mainly because their limit is 1 retry. It halted early on pick/tip faults that clear after 2 retries.
Only clearly fault-specific behavior: C chose replan for short aspiration (3/3).
Caveats: one plan, mock faults, oracle written by me, C was not shown the table, error text may have primed replan.
## Q2 round 2: strategy D (C + guardrail forcing halt on contamination)
D: exact 24/36, right outcome 30/36, unsafe 0/3. C replicated identically (21/36, 30/36, unsafe 3/3).
Remaining gap: pick/tip faults needing 2 retries; C and D both halt after 1 (6/9 outcome).
Takeaway: the LLM adds value interpreting errors (replan for short aspiration); hard limits and safety stops belong in rules.
## Q6 tracing findings
One trace per run (recovery_run) with execute/decide/apply spans; decide spans carry the model's action and reason, so a run can be reconstructed from the trace alone.
Trace showed why C replanned on contamination: its reason cited the aspiration rate as the likely cause of the splash, so my error wording and the replan option description primed it.
BUG TO FIX before final Q2 numbers: the retries counter increments on replan, so the model was told "retries: 1" after only a replan.
## Q2 after retries-counter fix
C unchanged (21/36 exact, 30/36 outcome, unsafe 3/3). D 23/36 exact (one plate_misplaced run differed), unsafe 0/3.
The counter bug did not drive the results; contamination finding stands. Priming caveat (error text, replan description) still applies.
