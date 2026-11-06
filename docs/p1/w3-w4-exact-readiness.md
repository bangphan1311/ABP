# P1 W3–W4 execution record: Exact, protocol and M2 readiness

**Owner:** P1 (coordinator, Exact + Oracle + integration + RQ3)  
**Repository branch:** `p1/w3-experimental-protocol-rc`  
**Record date:** 2026-11-06  
**Status:** `W3 PARTIAL / W4 NOT READY TO FREEZE`

This file separates (a) work evidenced in the repository, (b) work that is
only planned, and (c) decisions that require the whole group. A tiny solver
probe, CI test, or written protocol is not an official benchmark result.

## 1. Scope from the agreed work breakdown

P1 owns the common core, Gurobi MIP, CPLEX MIP, CPLEX CP, CP-SAT, brute-force
oracle, exact correctness/license checks, exact pilot, formulation review,
protocol fairness review, exact spot-checks, and the technical ownership of
RQ3. P1 coordinates contracts, milestones, PR review and merge.

P1 does **not** operate the official benchmark queue. P3 owns official queue
operation, automatic validation, run accounting, raw-result collection and
the resulting figures/tables. P2 owns SAT implementation and the RQ1/RQ2
pilot/analysis. During W4, P1 checks exact correctness and reviews a
predeclared sample of exact runs; P1 does not take over P3's runner.

## 2. W3 — Exact pilot and freeze preparation

| P1 deliverable | Evidence currently recorded | Status |
|---|---|---|
| Four exact backends through the common interface | `src/exact/{gurobi_mip,cplex_mip,cplex_cp,cp_sat_solver}.py`; shared `Result`; oracle comparison tests on `path4`, `cycle5`, `complete5` | Implemented; latest full-suite evidence must be rebound to final commit |
| Formulation review | MIP uses pairwise orientation indicators for distinct labels and edge direction; CP uses `all_diff` and absolute-distance constraints; CP-SAT uses `all_different` and absolute-distance variables | Code-reviewed; retain small-oracle tests as correctness evidence |
| Whole-run exact time accounting | Exact backends subtract model-build elapsed time before passing the remaining budget to the optimizer; `tests/exact/test_time_budget.py` covers remaining-budget arithmetic | Implemented in code; protocol/documentation alignment needed |
| Upper bound audit | 24/24 manifest rows are `VALID`; each row records `delta_max` and `ub_n_minus_delta` | Values tabulated in §3 below |
| Gurobi/CPLEX entitlement check | Gurobi Academic small probe PASS; CPLEX MIP and CP Community Edition size/search limits confirmed; no CPLEX Academic entitlement verified | Partial; benchmark-scale Gurobi capacity and CPLEX entitlement remain unverified |
| Exact pilot on actual HB validation subset | `experiments/pilot_exact_p1.py` builds the 10 × 4 plan with 600 s/run, 12 GiB cap, sequential execution, resume, raw JSON and summary; CI pilot-plan/loader tests PASS on Ubuntu and Windows | **Script ready; actual 40 HB runs still not executed because raw files are absent from this workspace** |
| Pilot on large HB instances | P1 exact-pilot runner supports 12 additional exact runs on `bcsstk06`, `nos6`, `can_715` at 1800 s/run; host/cap selected, target-host memory gate still requires recheck | **Not executed; requires real raw HB files and target-host memory test** |
| Review SAT semantics/canonical candidate | P1 review agrees with `order / pairwise / glucose4` within the Core candidate set `{cadical195, glucose4}`; `minisat22` is outside that Core set | P1 proposal accepted within Core; synthetic-pilot transfer limitation must be reported |

### 2.1 Exact pilot that remains

P1's executable pilot command (run from repository root on the selected Windows host, after confirming the raw HB files and manifest are present):

```powershell
uv run python experiments/pilot_exact_p1.py
```

The script enforces one worker, 600 seconds per validation run, a 12 GiB Windows Job Object cap and resume. Use `--include-large` only for the additional 12 exact pilot-large runs (three large instances × four methods, 1800 seconds/run), after the host memory-limit test has been checked. It refuses to start if any selected raw file or manifest entry is missing/invalid.


The protocol plan is:

- Exact pilot: 10 locked validation instances × 4 exact methods
  (`gurobi_mip`, `cplex_mip`, `cplex_cp`, `cp_sat`), 600 seconds per
  run, 40 planned runs.
- Pilot-large: 3 locked large instances × (3 unique SAT CNFs + 4 exact
  methods), 1,800 seconds per run, 21 planned runs in total. Do not start
  until P3 has demonstrated hard memory enforcement on the selected host.

A pilot is an environment/formulation risk check, not evidence for RQ3.
Where a CPLEX Community Edition limit is hit, retain the raw error and
classify the affected run as `ERR`; do not rewrite it as `TO` or omit the
method from the audit trail. The pilot must record the actual run count if a solver is unavailable. CPLEX Community Edition errors remain raw `ERR` records and do not stop later methods. The script writes raw JSON through the shared runner plus a derived `results/pilot_exact/summary.csv`. No pilot result is asserted in this document until the script has run against the real HB raw files.


## 2.2 HB input → shared runner integration (implemented)

The shared `src.sat.loader.read_instance()` now accepts official
`.mtx.rnd` paths directly; `src.runner.run_one()` and its worker therefore
use the same shared `Instance` contract without an intermediate JSON file.
The loader:

- converts source vertex IDs from 1-based to the shared 0-based convention;
- preserves all `n` vertices, including isolated vertices;
- removes self-loops and repeated undirected edges using the policy in
  `scripts/inspect_hb.py`;
- requires sibling `MANIFEST.csv` and `instances.csv`;
- checks the source SHA-256, header dimensions, header/row edge counts,
  cleaned edge count, removed-edge counts, `delta_max`, `UB=n-Δ`, and
  the inventory's `n`/`m_table` before returning an `Instance`.

Regression tests in `tests/sat/test_hb_loader.py` cover parsing, one-based
index conversion, isolated-vertex preservation, edge cleaning, hash/manifest
mismatch, missing provenance files, continued JSON compatibility, and an
end-to-end `run_one()` subprocess test using the brute-force oracle on a
small fixture. The workflow `W3 checkpoint, runner and HB loader tests` was
expanded to execute these checks plus the P1 exact-pilot plan tests on Ubuntu
and Windows. GitHub Actions run `42156873444` completed successfully on the
final documented branch head: Ubuntu **23 passed**, Windows **23 passed**.
This is fixture/plan CI evidence, not an actual HB solver pilot.

This closes the **code integration** gap. It does not establish that the real
24 raw files are present in a given checkout: `benchmark/hb/raw/` is
gitignored. The 40-run HB exact pilot is still pending until the official raw
files and matching manifest are available on the machine where the pilot is
executed, and until the protocol's resource/host gates are met.

## 3. P1 degree-bound audit for the 24 HB instances

For `Δ = delta_max`, the safe bound is `UB_degree = n − Δ`. The proof is
in `docs/exact_models.md`. These are manifest-derived values, not solver
results and not optimality certificates.

| Instance | n | m_clean | Δ | UB = n − Δ |
|---|---:|---:|---:|---:|
| `pores_1` | 30 | 103 | 9 | 21 |
| `ibm32` | 32 | 90 | 11 | 21 |
| `bcspwr01` | 39 | 46 | 5 | 34 |
| `bcsstk01` | 48 | 176 | 11 | 37 |
| `bcspwr02` | 49 | 59 | 6 | 43 |
| `curtis54` | 54 | 124 | 15 | 39 |
| `will57` | 57 | 127 | 10 | 47 |
| `impcol_b` | 59 | 281 | 17 | 42 |
| `ash85` | 85 | 219 | 9 | 76 |
| `nos4` | 100 | 247 | 6 | 94 |
| `dwt__234` | 117 | 162 | 9 | 108 |
| `bcspwr03` | 118 | 179 | 9 | 109 |
| `bcsstk06` | 420 | 3,720 | 27 | 393 |
| `bcsstk07` | 420 | 3,720 | 27 | 393 |
| `impcol_d` | 425 | 1,267 | 15 | 410 |
| `can__445` | 445 | 1,682 | 12 | 433 |
| `494_bus` | 494 | 586 | 9 | 485 |
| `dwt__503` | 503 | 2,762 | 24 | 479 |
| `sherman4` | 546 | 1,341 | 6 | 540 |
| `dwt__592` | 592 | 2,256 | 14 | 578 |
| `662_bus` | 662 | 906 | 9 | 653 |
| `nos6` | 675 | 1,290 | 4 | 671 |
| `685_bus` | 685 | 1,282 | 12 | 673 |
| `can__715` | 715 | 2,975 | 104 | 611 |

**Interpretation:** `UB_degree` is a valid mathematical upper bound. It is
not a proven optimum and must not by itself turn a run into `OPT`. The
current protocol keeps the solver's proof requirement (including the SAT
UNSAT probe at the next threshold).

## 4. Exact formulation and status review

The current exact implementations have the following intended semantics:

- Gurobi MIP and CPLEX MIP: integer label variables; one orientation binary
  per vertex pair to enforce distinct labels; one orientation binary per
  graph edge to enforce distance at least `K`; indicator constraints.
- CPLEX CP: integer labels, global `all_diff`, and absolute-distance edge
  constraints.
- CP-SAT: integer labels, `all_different`, and absolute-distance variables.

Every incumbent must be decoded/extracted, independently checked by
`verify()`, and compared against the backend's objective. `OPT` requires
proven optimality; verified but unproven incumbent is `FEAS`; timeout
without a verified incumbent is `TO`; license/backend/output errors are
`ERR`; `MO` requires evidence of a memory-limit event.

The exact code has build-time-aware solver budgets. The runner separately
records `t_total` and `wall_time`; the official end-to-end metric is
runner-measured `wall_time` under Protocol §6.2. `docs/exact_models.md`
was updated with this distinction so its time-accounting text no longer
contradicts the current code.

## 5. W4 — P1 sign-off status

| M2 requirement | Current state | P1 action |
|---|---|---|
| Confirm exact configuration and formulations | Formulations are represented in code and small-oracle tests | Re-run correctness suite on the freeze candidate and retain log + commit SHA |
| Confirm canonical SAT configuration | P1 agrees with `order / pairwise / glucose4` within the Core set `{cadical195, glucose4}` | Keep this as the pre-official proposal; record that the pilot was synthetic (10 graphs, 60 s/run), not the HB validation subset |
| Protocol review | P1 has incorporated W3 review comments on K-search, UB, whole-run time budget, pilot budget, PAR2 and checkpoint semantics | Obtain final P2/P3 review; do not interpret earlier comments as final sign-off |
| Resource/host freeze | P1 selected Windows build `10.0.26200`, 12 logical CPUs, 15.21 GiB RAM; 12.0 GiB/run cap, one worker | Recheck the exact host before running; the script enforces Windows build and minimum RAM, and the shared runner applies the Job Object cap |
| Solver entitlement | Gurobi Academic tiny probe PASS; CPLEX Community limits confirmed; Kissat native not verified and protocol contingency excludes it from RQ2 | If CPLEX Academic is unavailable, retain CPLEX runs as `ERR` where entitlement blocks execution and state the limitation |
| P1/P2 SAT specification cross-review | Protocol now refers to the existing draft `docs/handoff/w2-sat/14-sat-methodology.md` for encoding/K-search semantics | P1 must complete the technical cross-review against that draft; P2 must confirm whether it is the binding freeze specification or supply the approved canonical spec |
| PR and release gates | PR #50 and PR #52 are open; P1 review on #52 is `CHANGES_REQUESTED`; P1 branch is diverged from `main` | Resolve #52 blockers, recheck compare and sync P1 branch after #52 settles, re-run tests, merge only after review gates |
| Git tag `v1.0` | No tag recorded; protocol freeze conditions remain open | **Do not tag yet** |

## 6. Required P1 work during W4 official execution

The predeclared 10-run sample is frozen in `docs/p1/exact_spot_check_plan.md` before official outcomes are inspected. The sample covers all four exact methods and both small/large tiers; use these exact run IDs after P3's official runner completes the corresponding runs.

P3 operates the queue. P1's exact-side responsibilities are:

1. Before official runs, create a deterministic spot-check list of 10 planned
   exact runs, selected across all four exact methods and both instance tiers
   without looking at outcomes. Record the sampling seed and run IDs.
2. When P3 completes each batch, inspect exact records for status, objective,
   `lb/ub`, verified solution, runtime, license and memory anomalies.
3. Independently call the project verifier on the 10 preselected runs. Check
   the raw JSON, not only the CSV summary. Add targeted checks for every
   anomaly in addition to the 10-run sample.
4. Report defects to P3 and fix only exact-side implementation defects in
   coordination with the group. Preserve the original raw attempt and rerun
   only affected records under the frozen protocol.
5. Own the RQ3 interpretation: OPT coverage, FEAS incumbent quality,
   TO/MO/ERR patterns, exact-vs-SAT differences, and limitations. Do not
   claim a method is inferior merely because a license-blocked run is `ERR`.

## 7. Decisions and remaining blockers

P1 has selected the candidate host, cap and solver fallback policy for the execution plan; this is not a claim that `v1.0` freeze conditions are complete.

- Candidate host and cap are set by P1 for the current run plan: Windows build `10.0.26200`, 15.21 GiB RAM, 12 GiB per run, one worker. Recheck before execution; the 0.125 GiB cap in tests is only a test fixture.
- A CPLEX Academic entitlement is not verified. P1's execution choice is to keep both CPLEX baselines in the plan and record Community Edition size/search/license blocks as `ERR` with raw reason, rather than waiting indefinitely for Academic entitlement or changing them to `TO`.
- The official HB raw data are locally held and ignored by Git. The manifest
  is present, but the raw files must be available on the selected official
  host and their hashes must match the manifest.
- The source page confirms the 24-instance ABP benchmark, but the semantic
  meaning of the `.rnd` suffix is still listed for confirmation in the
  preflight checklist. Do not invent that explanation in the paper.
- P3 remains official queue operator and must own official runner/schema/memory/checkpoint/resume validation and dry-run budget. P2 owns SAT-side changes/review; P1 has independently accepted `order/pairwise/glucose4` within the Core candidate set.

## 8. Freeze rule

Keep the protocol at `1.0-rc` until every gate in Experimental Protocol
§12 has evidence tied to the exact candidate commit, selected host,
configuration and raw results. Merging PRs is necessary but not sufficient.
No official RQ3 result, `data-final`, or `v1.0` tag is claimed by this file.
