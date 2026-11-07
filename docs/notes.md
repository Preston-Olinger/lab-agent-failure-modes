## Q1 results (30 requests x 3 runs)
v1 (original rules): simulator caught 0/60 lab-practice flaws; validator caught 58/60.
Simulator caught 10/12 API errors; 2 runs were empty plans (silent refusals).
Misses: t3 (AI labeled samples role=other, so R3 skipped them); a3 (empty plan).
v2 (R3 generalized, R9 added AFTER seeing v1): validator 60/60; API errors: 11 by simulator + 1 empty plan flagged by R9.
Caveat: rules were revised after seeing results and test cases were written around the rules, so v2 is optimistic.
