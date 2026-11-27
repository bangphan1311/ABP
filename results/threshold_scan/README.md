# ABP boundary scan

Seven Harwell–Boeing instances with pilot OPT references. For each optimum B, the scan tests B−2 through B+2 with a fresh CaDiCaL 1.9.5 process per threshold and encoding (pairwise with pairwise AMO, or order). The parent process enforces 120 seconds including startup and encoding. This supplementary script does not enforce a RAM cap. The solve_s field measures solve() only. Timeout records omit solver counters.

The raw directory contains 70 original measurements across seven graphs (42 SAT, 26 UNSAT, 2 TO). The opt_references.json file preserves the pilot run identifiers, bounds and labelings. The script checks the labeling before scanning. UNSAT here is the solver verdict.

With the project dependencies installed and HB input files available, run from the repository root:

    python experiments/scan_thresholds.py list
    python experiments/scan_thresholds.py scan pores_1 --seconds 120

Repeat the second command for each listed instance. Each invocation writes a fresh directory under results/threshold_scan/reruns/.
