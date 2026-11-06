# P1 W5–W6 — RQ3 analysis and reporting plan

**Owner:** P1 (Exact + Oracle + RQ3 technical analysis)  
**Prepared:** 2026-11-06  
**Status:** Analysis framework prepared; official results not yet available  
**Depends on:** P3's validated official run export; P2's frozen canonical SAT configuration

This document prepares the analysis workflow and report structure before benchmark results exist. It is not a record of experimental findings. Do not fill placeholders with estimates or pilot outcomes.

## 1. Keep the three result sets separate

| Result set | Purpose | Allowed use |
|---|---|---|
| P1 Exact Pilot: 10 validation instances × 4 exact methods, 600 s/run | Check formulation, solver entitlement, input integration and host operation | Operational diagnosis only; **not RQ3 evidence** |
| Official RQ3: all 24 HB instances × canonical SAT + four exact methods, 1800 s/run | Main SAT-vs-Exact comparison | Primary RQ3 results |
| Remaining 14 instances outside the 10-instance validation subset | Additional view that was not used for the validation-subset configuration selection | Report separately as a sensitivity/descriptive view; **not an independent random test set** |

The 600-second Exact Pilot and 1800-second official runs must never be pooled in a single runtime or PAR2 comparison. The pilot can expose license or implementation problems, but it cannot establish that one solver is faster or better on the official benchmark.

## 2. W5 — Exact evidence validation

P3 remains the official queue operator and owner of the canonical export. P1 performs exact-side validation and the predeclared spot-check.

### 2.1. Run accounting

For the official RQ3 matrix, reconcile the expected 24 instances × 5 methods (one canonical SAT configuration and four exact methods) against the validated run records.

- [ ] Confirm the frozen protocol version, commit/tag, host and configuration used by the batch.
- [ ] Confirm one selected record per (instance, method, configuration); identify missing and duplicate attempts.
- [ ] Confirm official time_limit = 1800 s, memory_limit = 12 GiB, seed = 0, one worker, no warm start and no symmetry breaking.
- [ ] Preserve every raw attempt. A selected runs.csv row must be traceable to its raw JSON; do not overwrite or hand-edit raw evidence.
- [ ] Reconcile the actual number of completed, missing and retried runs. Do not present a planned count as an achieved count.

### 2.2. Exact correctness spot-check

Use the fixed 10-run sample in docs/p1/exact_spot_check_plan.md; do not replace it after seeing outcomes.

For every sampled run:

1. Load the original HB instance through the manifest-checked loader.
2. Read the raw JSON, not only the CSV export.
3. Re-run verify(instance, solution) on every OPT or FEAS incumbent.
4. Check that the recomputed objective equals lb and the reported solver objective.
5. Check lb <= ub; for OPT, require a verified solution, proof/status consistency and lb == ub.
6. Inspect wall_time, peak_memory, time_limit, memory_limit, host, commit, solver metadata and error text.
7. Record the check outcome and raw run ID. Investigate every anomaly outside the sample as well.

A license or edition failure is retained as ERR, with its raw reason. It is not a timeout and must not be used as evidence of slow solver performance.

### 2.3. Cross-method consistency checks

- [ ] For each instance, compare objective values from all methods that returned OPT. Conflicting OPT values require investigation before analysis.
- [ ] Compare every OPT objective with the literature reference interval recorded for that instance.
- [ ] For FEAS, compare only verified lower bounds and valid upper bounds; do not describe a feasible incumbent as an optimum.
- [ ] Investigate invalid solutions, impossible bounds, missing records, unexplained MO, and contradictory metadata before producing figures.

## 3. W5 — Metrics and aggregation rules

Use runner-measured wall_time as the primary end-to-end runtime. Keep solver-reported t_total as a diagnostic field; do not mix them in the same comparison.

| Metric | Definition / reporting rule |
|---|---|
| OPT coverage | Number of OPT runs divided by planned runs, reported per method and overall |
| Verified feasible coverage | OPT + FEAS; every incumbent must have passed verification |
| Status distribution | Separate counts of OPT, FEAS, TO, MO, ERR, and missing |
| Runtime | wall_time; show status alongside runtime and state the timeout budget |
| Memory | peak_memory, with missing values reported as unavailable rather than zero |
| Objective quality | Verified lb, valid ub, and absolute gap ub - lb where both bounds exist |
| PAR2 | For official 1800-second runs, each non-OPT or unresolved missing run receives 3600 seconds; retain the status breakdown beside PAR2 |

For the 600-second Exact Pilot only, the protocol's corresponding PAR2 penalty is 1200 seconds. Keep this pilot calculation separate from the official 3600-second penalty.

Report both coverage and runtime. A method that is fast only on the few instances it solves to OPT must not appear superior because timeouts and errors were silently omitted. Show license-blocked ERR separately from computational TO/MO; a license block is a tool-availability limitation, not a measured search-time failure.

Do not calculate a runtime average over OPT runs alone and present it as an overall solver ranking. It may be shown as a conditional descriptive statistic only when paired with OPT coverage and the full status distribution.

## 4. W5–W6 — RQ3 figures and tables to prepare

Create every figure and table from validated raw records using version-controlled scripts. Never type benchmark measurements into a figure by hand.

| Output | Purpose | Required safeguards |
|---|---|---|
| Status matrix (24 instances × 5 methods) | Expose coverage and per-instance failures | Distinguish OPT, FEAS, TO, MO, ERR, and missing |
| Status summary table | Compare completed/proven results | Show planned denominator and actual run count |
| PAR2 comparison | Combine proof coverage and timeout cost under the frozen rule | Label 1800 s budget and 3600 s penalty; show ERR causes separately |
| Runtime cactus plot | Show cumulative solved-instance coverage over time | State whether only OPT counts as solved; do not silently mix pilot and official runs |
| Pairwise runtime/objective scatter | Inspect agreement and relative behavior on matched instances | Compare only matched records; mark non-OPT cases distinctly |
| Scale/difficulty view | Explore runtime/status against n, m_clean, density and maximum degree | Treat as descriptive analysis, not a predictive model |

The main RQ3 table should include, at minimum, instance, n, m_clean, Δ, and each method's status, verified lb, valid ub, wall_time, and available peak_memory. Keep the status visible even when a metric is unavailable.

## 5. Reporting structure (fill only after validation)

### RQ3 — SAT versus exact methods

**Question.** How does the canonical SAT configuration compare with Gurobi MIP, CPLEX MIP, CPLEX CP and CP-SAT on the 24 Harwell–Boeing instances under the common experimental protocol?

**Experimental setup.** State the 24-instance dataset and its manifest validation; the canonical SAT configuration selected before official evaluation; the four exact methods; the common host; one worker; 1800-second time limit; 12-GiB process memory cap; seed and disabled options; and the runner's end-to-end wall_time measurement. Cite the exact commit/tag and protocol version used by the official batch.

**Results.** Insert the validated status table, objective/bound table, PAR2 summary and figures. State the planned denominator and actual number of valid records. Explicitly identify unavailable methods or license-blocked runs.

**Interpretation.** Discuss proof coverage (OPT), verified feasible incumbents (FEAS), timeout/memory patterns (TO/MO), and operational errors (ERR) separately. Relate observed difficulty to graph size and structure without claiming causation from a small benchmark.

**Validation and limitations.** Summarize P1's fixed spot-check and any anomaly investigations. State that each configuration has one seed/run, that results are host- and license-dependent, and that the 10-instance validation subset was involved in configuration selection. The remaining 14 instances are a descriptive supplementary slice, not an independent random test set.

### Reproducibility appendix

Record:
- repository URL, exact commit SHA and protocol version;
- Python version, OS/build, CPU, physical RAM and solver versions/entitlements;
- dataset source, manifest version and SHA-256 verification;
- complete solver configurations, time and memory limits;
- exact command lines and output directory structure;
- raw JSON archive, validated export and analysis-script version;
- known deviations, failed runs, retries and their reasons.

## 6. W6 — P1 completion checklist

- [ ] Complete the 10-run exact spot-check and anomaly follow-up.
- [ ] Reconcile all official exact records against P3's queue accounting.
- [ ] Verify cross-method OPT consistency and reference intervals.
- [ ] Generate RQ3 tables/figures from validated data.
- [ ] Write the RQ3 results and discussion without claiming beyond the evidence.
- [ ] Complete the reproducibility appendix and limitations.
- [ ] Cross-review P2's RQ1/RQ2 sections for consistent terminology, status semantics, time accounting and dataset description.
- [ ] Confirm every paper claim can be traced to a raw run, validation record, protocol rule or cited source.

## 7. Claims that must remain unwritten until evidence exists

Do not claim that a particular solver is fastest, most scalable, most memory-efficient or best overall before the official 24-instance results have been validated. Do not infer an optimum from UB = n - Δ alone. Do not treat an unavailable license as a timeout. Do not describe the 14-instance remainder as an independent test set. Do not use the Exact Pilot's 600-second results as official RQ3 results.
