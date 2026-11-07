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
