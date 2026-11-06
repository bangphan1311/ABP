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
| Exact pilot on actual HB validation subset | Preflight records tiny probes, but no saved 10-instance × 4-exact pilot result set or raw evidence | **Not evidenced / still to run** |
| Pilot on large HB instances | Protocol plans a 3-instance early-warning pilot after memory enforcement is verified; no saved exact pilot-large result set is recorded | **Blocked by host and memory-cap sign-off** |
| Review SAT semantics/canonical candidate | P1 review agrees with `order / pairwise / glucose4` within the Core candidate set `{cadical195, glucose4}`; `minisat22` is outside that Core set | P1 proposal accepted within Core; synthetic-pilot transfer limitation must be reported |

### 2.1 Exact pilot that remains

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
method from the audit trail. The pilot must record the actual run count if
a solver is unavailable. No pilot result is asserted in this document.


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
expanded to execute this test on Ubuntu and Windows. CI was queued/in progress
at the time of this update; do not record it as PASS until GitHub reports a
completed successful run.

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
| Resource/host freeze | Windows snapshot: 15.21 GiB RAM; official host and benchmark memory cap are not declared | Whole group must name the host and choose a cap below physical RAM with OS headroom; 30 GB is not feasible on this snapshot |
| Solver entitlement | Gurobi Academic tiny probe PASS; CPLEX Community limits confirmed; Kissat native not verified and protocol contingency excludes it from RQ2 | If CPLEX Academic is unavailable, retain CPLEX runs as `ERR` where entitlement blocks execution and state the limitation |
| P1/P2 SAT specification cross-review | Protocol refers to `docs/sat_spec.md`; verify that the actual approved spec exists at that path and review it against K-search/encoding semantics | The referenced path returned 404 during this review; P2 must supply the canonical spec or P1 must update the protocol link to the approved existing document before freeze |
| PR and release gates | PR #50 and PR #52 are open; P1 review on #52 is `CHANGES_REQUESTED`; P1 branch is diverged from `main` | Resolve #52 blockers, recheck compare and sync P1 branch after #52 settles, re-run tests, merge only after review gates |
| Git tag `v1.0` | No tag recorded; protocol freeze conditions remain open | **Do not tag yet** |

## 6. Required P1 work during W4 official execution

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

## 7. Decisions and blockers that P1 cannot make alone

- Official host, operating system, parallel-run policy and benchmark memory
  cap require group confirmation. The 0.125 GiB cap in tests is a test fixture,
  not the benchmark cap.
- A CPLEX Academic entitlement is not verified. The agreed contract says
  license failures are `ERR`; the group should document whether it accepts
  this limitation or obtains Academic access.
- The official HB raw data are locally held and ignored by Git. The manifest
  is present, but the raw files must be available on the selected official
  host and their hashes must match the manifest.
- The source page confirms the 24-instance ABP benchmark, but the semantic
  meaning of the `.rnd` suffix is still listed for confirmation in the
  preflight checklist. Do not invent that explanation in the paper.
- P3 must confirm runner/schema/memory/checkpoint/resume and the dry-run
  budget. P2 must resolve the SAT-side review points on PR #52.

## 8. Freeze rule

Keep the protocol at `1.0-rc` until every gate in Experimental Protocol
§12 has evidence tied to the exact candidate commit, selected host,
configuration and raw results. Merging PRs is necessary but not sufficient.
No official RQ3 result, `data-final`, or `v1.0` tag is claimed by this file.
