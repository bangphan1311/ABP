# Experimental Protocol — Antibandwidth Problem (ABP)

- **Version:** 1.0-rc
- **Status:** Waiting for P2/P3 review; freeze blockers M12–13 remain open
- **Owner:** P1
- **Reviewers:** P2, P3
- **Dataset:** Harwell–Boeing only; 24 selected instances
- **Purpose:** Single source of truth for experimental design. This is a draft, not a frozen protocol. Once the freeze conditions in §12 are met and the group confirms, tag v1.0.

## 1. Scope and research questions

For a graph (G=(V,E)), ABP seeks a bijection (f:V\to\{1,\ldots,n\}) maximizing \(\min_{\{u,v\}\in E}|f(u)-f(v)|\).

Core SAT dimensions:
- Variable encoding: pairwise and order.
- At-most-one (AMO): pairwise and sequential counter.
- SAT search: multi-run, non-incremental K-search.
- SAT solvers: CaDiCaL and Glucose; include Kissat only if it is actually integrated and runnable in the project environment. If unavailable, RQ2 compares CaDiCaL/Glucose and documents the limitation.

Exact methods: Gurobi MIP, CPLEX MIP, CPLEX CP, and CP-SAT.

Excluded from the official core: staircase/SCL/Duplex bonus encoding, incremental solving, symmetry breaking, and warm starts. Bonus SAT prototype is NO-GO. If a required exact solver cannot run because of licensing/tooling, record ERR with the reason; do not relabel it as timeout.

- **RQ1:** How do variable encoding × AMO choice affect SAT performance?
- **RQ2:** How do available SAT solvers compare under the canonical SAT configuration?
- **RQ3:** How do the canonical SAT method and exact methods compare across the 24 official instances, including runtime/status against graph size and structure?
- No RQ4 and no predictive claims. Conclusions must follow question → design → evidence → conclusion and avoid generalizing beyond measured results.

## 2. Dataset and input contract

Use only the 24 selected Harwell–Boeing instances. The intended CSV is `benchmark/hb/instances.csv`, with columns:

`id,name,file,size_group,n,m_table,ab_lb_ref,ab_ub_ref,pilot_role`

The CSV is a planned manifest of the selected instances; it does **not** prove the data files have been downloaded. Track actual files and SHA256 hashes in `MANIFEST.csv`. Expected filenames end in `.mtx.rnd`; ask the instructor what `.rnd` means and confirm the actual file format before finalizing the loader. Expected input format: header `n n m`, then `u v) edge rows, 1-indexed; validate rather than assume.

Loader rules:
- Preserve vertices (1,\ldots,n), including isolated vertices.
- Reject self-loops; treat the graph as undirected; deduplicate repeated edges and reversed duplicates.
- Record source file SHA256, header (m), and edge count after cleaning.
- Verify (n) matches the selected table for all 24 instances and header (m) matches `m_table`. If cleaning changes the edge count, document the discrepancy.
- `ab_lb_ref` and `ab_ub_ref` are literature/reference checks only, never solver inputs. Every reported OPT objective must be within the reference bounds when those bounds are valid for the same instance definition.

### Selected instance table

| ID | Instance | n | m | Reference LB | Reference UB | Pilot role |
|---|---|---:|---:|---:|---:|---|
| A | pores_1 | 30 | 103 | 6 | 8 | config |
| B | ibm32 | 32 | 90 | 9 | 9 | — |
| C | bcspwr01 | 39 | 46 | 16 | 17 | — |
| D | bcsstk01 | 48 | 176 | 8 | 9 | — |
| E | bcspwr02 | 49 | 59 | 21 | 22 | config |
| F | curtis54 | 54 | 124 | 12 | 13 | — |
| G | will57 | 57 | 127 | 12 | 14 | config |
| H | impcol_b | 59 | 281 | 8 | 8 | config |
| I | ash85 | 85 | 219 | 19 | 27 | config |
| J | nos4 | 100 | 247 | 32 | 40 | config |
| K | dwt_234 | 117 | 162 | 46 | 58 | config |
| L | bcspwr03 | 118 | 179 | 39 | 39 | — |
| M | bcsstk06 | 420 | 3720 | 28 | 72 | stress |
| N | bcsstk07 | 420 | 3720 | 28 | 72 | — |
| O | impcol_d | 425 | 1267 | 91 | 173 | — |
| P | can_445 | 445 | 1682 | 78 | 120 | config |
| Q | 494_bus | 494 | 586 | 219 | 246 | — |
| R | dwt_503 | 503 | 2762 | 46 | 71 | — |
| S | sherman4 | 546 | 1341 | 256 | 272 | — |
| T | dwt_592 | 592 | 2256 | 103 | 150 | — |
| U | 662_bus | 662 | 906 | 219 | 220 | config |
| V | nos6 | 675 | 1290 | 326 | 337 | stress |
| W | 685_bus | 685 | 1282 | 136 | 136 | config |
| X | can_715 | 715 | 2975 | 112 | 142 | stress |

Use the exact supplied filenames when creating the CSV (for example, `A-pores_1.mtx.rnd`, `K-dwt__234.mtx.rnd`, `P-can__445.mtx.rnd`, `Q-494_bus.mtx.rnd`). Confirm every filename against the instructor-provided files; do not fabricate missing files.

There are 12 small instances (n=30–118) and 12 large instances (n=420–715).

## 3. Official and pilot subsets

- **Official:** all 24 selected instances.
- **Pilot-config:** A, E, G, H, I, J, K, P, U, W — 10 instances: pores_1, bcspwr02, will57, impcol_b, ash85, nos4, dwt_234, can_445, 662_bus, 685_bus.
- **Pilot-stress:** M, V, X — bcsstk06, nos6, can_715. Use for resource/kill/resume testing, not canonical configuration selection.
- The remaining 14 instances were not used to select the canonical configuration. Explicitly state that the 10 pilot-config instances informed configuration selection; the other 14 are not a randomly sampled independent test set.
- Freeze subsets at M2. Any change requires a documented methodology decision.

The pilot-config set spans n=30–685. Any difficulty classification based on literature is indicative only because prior work may use different encodings/settings.

## 4. Experimental design

### RQ1 — encoding × AMO
Run the 10 Pilot-config instances using CaDiCaL and multi-run search across the 2×2 combinations:
1. pairwise variable encoding + pairwise AMO
2. pairwise variable encoding + sequential-counter AMO
3. order variable encoding + pairwise AMO
4. order variable encoding + sequential-counter AMO

Record variables, clauses, encoding time, solver time, total time, peak memory, and status.

### RQ2 — SAT solver
Use the canonical configuration selected by RQ1 on the same 10 Pilot-config instances. Compare CaDiCaL, Glucose, and Kissat only if Kissat is runnable. Reuse CaDiCaL results from RQ1 when the configuration and run conditions match; otherwise rerun and explain why.

### RQ3 — SAT vs exact
Run the frozen canonical SAT method and the four exact methods on all 24 Official instances. Analyze status and runtime against n, |E|, density, and maximum degree. Suggested outputs: cactus plot, runtime scatter/plots, and status distribution. Report missing/failed methods transparently.

## 5. Solver protocol and objective verification

### SAT multi-run K-search
Use fresh, non-incremental CNF/backend instances per K. Start from the trivial lower bound or a quick heuristic; include heuristic time in `t_total`. For each K, encode ABP ≥ K and call the solver. On SAT, decode and independently verify the labeling, calculate its actual antibandwidth B, then set K ← B+1. The first UNSAT after a verified incumbent proves optimality. Do not treat UNKNOWN/timeout as SAT or UNSAT.

Use a valid graph-based upper bound agreed by P1/P2 and record the formula in the experiment configuration. Do not use literature reference bounds as solver input. P1/P2 must review off-by-one and K/window-width mapping before freeze.

### Exact methods
P1 drafts the exact formulation and P2 reviews it. For MIP, use edge binary variables for the condition `|f(u)-f(v)| >= K`; avoid weak big-M formulations where a stronger formulation is available. Keep default solver parameters except for common resource settings (one thread, time limit, memory limit, seed); document API differences and any solver-specific deviations.

## 6. Resource limits and reproducibility

- Run official experiments on the same documented machine/environment.
- One thread per run; no warm start or symmetry breaking.
- Total concurrent memory use must not exceed physical RAM.
- Pilot limit: 600 seconds per run. Official limit: 1800 seconds per instance × method. For SAT, 1800 seconds covers the entire multi-K chain.
- `t_total` includes model/encoding construction and all solver calls. For exact solvers, the time passed to the solver is 1800 seconds minus model-build time.
- Runner wall time is authoritative. A hard kill at `time_limit + 30s` is grace for shutdown only, not extra solve budget.
- Target 30 GB/run only if physical RAM and enforcement are verified. If RAM is insufficient, reduce this before freeze, document it, and reduce concurrency accordingly. Runner must enforce memory limits; config-only declarations are not enforcement.
- Use one run per instance × method, seed=0. Do not report confidence intervals from a single run; state this as a limitation.
- Skip valid existing runs. Investigate and rerun missing/ERR runs in W5 while preserving raw history.

## 7. Status and correctness contract

- **OPT:** verified solution and an optimality certificate/proof.
- **FEAS:** verified incumbent, but optimality not proven by the budget end.
- **TO:** timeout without a verified incumbent.
- **MO:** memory limit exceeded, supported by evidence.
- **ERR:** execution, licensing, invalid output, or other failure.
- A license error is ERR, not TO. Do not infer MO without evidence.

For every solution, validate that labels form a permutation of 1..n and independently recompute the objective from the graph. Check `lb <= ub`; OPT must have a valid certificate; FEAS must have a verified incumbent; TO must not have a verified incumbent. No duplicate `run_id`, and no missing expected runs in the final matrix. OPT objectives must be consistent with reference bounds when comparable.

Correctness gates:
- Tier 0/1 tests and oracle comparisons must pass for all core solvers.
- For large instances, if any two methods report OPT with different objectives, investigate before reporting.
- Preserve raw solver output and validation evidence.

## 8. Metrics, schema, and outputs

Each run should record:
`run_id, instance, method, abp_encoding, amo_encoding, solver, search_mode, status, lb, ub, t_encode, t_solve, t_total, variables, clauses, peak_memory, git_tag, host, timestamp`.

Use consistent N/A values when a metric does not apply; never invent measurements. RQ1 reports variables/clauses, encode/solve/total time, peak memory, and status. RQ2 reports status counts, per-instance runtime/memory, errors and anomalies. RQ3 reports status, bounds, total time and memory.

Pipeline: config → runner → subprocess per run → raw JSON/output → validation → `runs.csv` → figures/tables. Generate figures from saved data; do not manually edit `runs.csv`. Preserve raw outputs and run history.

## 9. Pilot size and canonical selection

- RQ1: 10 instances × 4 configurations × CaDiCaL = 40 runs.
- RQ2: add Glucose and, if runnable, Kissat on the chosen configuration = 20 additional runs; reuse the 10 matching CaDiCaL runs from RQ1. Expected SAT pilot total: 60 unique runs if all three solvers are available.
- Exact pilot: 10 instances × 4 exact methods = 40 runs.
- Stress checks: 3 instances × 5 core methods = 15 runs.
- If a solver is unavailable, record actual run count and reason; do not imply it ran.

Choose canonical config in this order:
1. More OPT results.
2. Tie: lower PAR2 (non-OPT runs penalized at 2 × time limit).
3. Tie: lower median peak memory.
4. Tie: lower median clause count.

Handle errors/missing runs consistently; do not exclude an adverse run without a technical reason. Save pilot results and the selection rationale in docs before M2. Freeze the canonical search settings as `search_mode=multi`, `symmetry=false`, `warm_start=false`.

## 10. Official run plan

After v1.0 freeze, run 24 instances × 5 methods (canonical SAT, CP-SAT, Gurobi MIP, CPLEX MIP, CPLEX CP) = 120 expected official runs. Investigate and rerun missing/ERR runs in W5. If a solver cannot run because of licensing/tooling, record ERR and the reason; do not relabel as TO.

## 11. Compute budget and environment record

Worst-case core-hour estimates (not wall-clock guarantees):
- SAT pilot: 60 × 600s = 10 core-hours.
- Exact pilot: 40 × 600s ≈ 6.7 core-hours.
- Stress checks: 15 × 600s = 2.5 core-hours.
- Official: 120 × 1800s = 60 core-hours.

Use W3 `--dry-run` and pilot evidence to update estimates. If the budget is too large, reduce RQ1/RQ2 pilot first; do not drop large official instances without a documented group decision.

Before freeze, record: machine/CPU/RAM/OS; Python and library versions; OR-Tools, Gurobi, CPLEX CP, PySAT and SAT solver versions/how invoked; Git tag/commit; licenses/model limits; time/memory limits and concurrency.

## 12. Freeze conditions (M2)

Freeze v1.0 only after all are true:
1. All 24 actual data files are present; manifest/SHA256 is complete; loader passes all files.
2. Correctness/oracle/cross-solver checks pass.
3. Canonical SAT configuration is selected and reviewed.
4. Memory enforcement and kill/resume have been tested.
5. Exact time limit correctly includes model-build time.
6. Subsets, RQs, time/memory limits, machine, versions and solver capabilities/licenses are documented and locked.
7. P2 and P3 have reviewed the protocol and blockers are resolved.

Until then, keep version 1.0-rc. After freeze, fixes for crashes, bugs, wrong results, validation and reproducibility are allowed. Do not silently change encoding, formulation, benchmark, RQ, solver set, limits or protocol; methodology changes must be documented, versioned, and affected runs repeated.

## 13. Pre-freeze action list

- **P1:** Ask the instructor for the 24 `.mtx.rnd` files and clarify the `.rnd` format; confirm Gurobi/CPLEX licenses and limits; document the machine/RAM; review the exact formulation and time accounting; coordinate final freeze.
- **P2:** Implement/verify loader and manifest against all 24 files; review P3 integration; check duplicate clauses in pairwise AMO; run RQ1/RQ2 pilots and document canonical selection; review correctness and proofs.
- **P3:** Enforce hard memory limits; test kill/resume; validate `--dry-run` and budget; review run schema, pipeline and status classification.
- **P2 + P3:** Review this protocol's dataset, subsets, metrics, resource limits and freeze conditions. Confirm formal ownership/assignment of tasks on GitHub.

## 14. References

- Fazekas et al. (2020), work on Duplex encoding and staircase AMO.
- Sinnl (2021), computational approaches for the Antibandwidth Problem, *Central European Journal of Operations Research*, 29(3).
- Truong et al. (2025), Sequential Counter Encoding for Staircase AMO, ICAART 2025.
- Rodriguez-Tello et al. (2015), Harwell–Boeing graphs for the Cutwidth/related graph-layout problem.

Published runtimes are not directly comparable unless hardware, encoding, symmetry settings, and solver configurations match. Verify complete bibliographic details before the final paper.
