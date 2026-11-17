# AI handoff — ABP project (2026-11-17)

Purpose: continue the project from the current GitHub state without redoing the review or treating pending gates as completed.

## Repository and branch snapshot
- Repository: https://github.com/bangphan1311/ABP
- PR #50: https://github.com/bangphan1311/ABP/pull/50 — P1 protocol / benchmark integration, open; branch `p1/w3-experimental-protocol-rc`; head `f7f1b661a43f181952fd0678a5ef3b8dcbe26578`; compare vs main at review time: 97 ahead / 11 behind.
- PR #52: https://github.com/bangphan1311/ABP/pull/52 — P2 SAT W4 implementation/analysis, open; branch `p2/w4-sat`; latest observed head `acd9dd0068c7a168b9cca1b9c4e057a0c9266ca6`; compare vs main at review time: 25 ahead / 0 behind.
- Do not force-push or reset either branch. Reconcile P1 with main only after reviewing/merging P2, then rerun affected tests.

## Work added in this review round

### On `p2/w4-sat` (PR #52)
- Fixed the six review topics raised by P1 in PR #52: G3 expected denominator, RQ1/RQ2 axis separation, canonical memory cap, missing-instance triage, freeze evidence wording and PR blast-radius disclosure.
- RQ1 analysis now isolates CaDiCaL across the three distinct CNFs; RQ2 isolates canonical order/pairwise with Core CaDiCaL/Glucose. It does not treat order/seqcounter as a fourth distinct CNF.
- The analysis requires `--expected-runs`, no longer auto-reads official `results/runs.csv` as pilot input, and defaults to the two separate pilot CSVs. G3 only counts unique Core IDs with matching triaged raw evidence; absent raw evidence prevents a pass.
- Canonical SAT config records `order / pairwise / glucose4`, 1800 s official per-run time, and 12.0 GiB memory cap. Helper rejects explicit null/invalid caps. Shared runner/OS—not `solve_sat`—must enforce the hard cap.
- Triage classifies missing/unresolvable benchmark instances as `ENV_ERROR`, including TO/ERR records without a solution.
- Memory sampling was made importable on Linux (RSS fallback for tests/CI); Linux fallback is not official memory-cap enforcement.
- The legacy generated report saying `70/70 G3 PASS` is explicitly marked SUPERSEDED.
- Added tests for split axes, 40 unique pilot Core IDs, expected G3 denominator, missing raw records, memory cap and missing-instance triage.
- Updated W4 freeze/analysis docs, canonical config proposal and PR #52 description.

Important commits added during this round include `48b020b`, `1aa3caa`, `b0c32eb`, `f35081c`, `21b299d`, `15bfc74`, `e99c515`, `4ebbf8f`, `1f59a91`, `1bd9f65`; P2 then added `acd9dd0` to install OR-Tools in CI. Always inspect the live branch head before applying changes.

### On `p1/w3-experimental-protocol-rc` (PR #50)
- Updated official plan-only dry-run to SAT `order / pairwise / glucose4`, with planned 12.0 GiB cap as metadata only; added tests for the official plan and distinct RQ1/RQ2 solver choices.
- Added `paper/p2_sat_methodology.tex`: modular SAT methods section plus tables from the historical synthetic W3 pilot.
- Added `paper/p2_sat_appendix.tex`: proof sketches for pairwise/order encoding equivalence, AMO faithfulness and K-search completeness; includes the UNSAT trust boundary.
- Updated `paper/README.md` to say drafts are modular, not an integrated master paper.
- Added `docs/p1/sat-cross-review-2026-11-17.md` covering code/spec/paper consistency and unresolved gates.
- Updated PR #50 and issue #49 descriptions to show protocol status, host/dataset/budget blockers and review requests.

## CI evidence — do not overstate
- P1 workflow run #73: https://github.com/bangphan1311/ABP/actions/runs/44009085711 — PASS on Windows and Ubuntu, 23 tests per platform. This covers HB loader/checkpoint/shared runner, not the full suite and not P2's SAT-analysis tests.
- New P2 SAT CI workflow: `.github/workflows/sat-core-tests.yml`, matrix Ubuntu + Windows, command `python -m pytest tests/sat tests/experiments/test_analyze_rq1_rq2.py tests/experiments/test_pilot_scripts.py -q`.
- First P2 run #1: https://github.com/bangphan1311/ABP/actions/runs/44009690444 — FAILED on both OS during collection because `ortools` was missing (`tests/sat/test_g1_oracle.py` imports `src.exact.cp_sat_solver`).
- P2 then added commit `acd9dd0` to install `ortools==9.15.6755` alongside pytest and python-sat. Workflow run #2: https://github.com/bangphan1311/ABP/actions/runs/44010144573 — `action_required`; no test pass/fail result on that new SHA is available yet. Approve/enable/re-run it, then diagnose subsequent failures.
- Historical PR #52 test counts (513/514 passed) predate the current review fixes; they are not evidence for latest head.

## Unresolved methodology and data blockers

1. **Pilot time-budget mismatch:** committed `results/pilot_rq1.csv` and `results/pilot_rq2.csv` run IDs say `time_limit=60.0`, while current Experimental Protocol §6.2 specifies 1800 seconds for RQ1/RQ2 pilots. The paper and canonical-config docs disclose this. The group must either explicitly approve the historic 60 s pilot and amend the protocol, or rerun the pilots at 1800 s and revisit canonical selection. Do not quietly reconcile the difference.
2. **G3 raw evidence:** the planned Core pilot contains 40 unique IDs (30 RQ1 distinct-CNF runs plus 10 additional Glucose runs; CaDiCaL order/pairwise is shared). The matching 40 raw JSON records were not found in the Git tree. The CSV rows alone do not establish G3. Locate/obtain raw records, triage all 40, regenerate with `--expected-runs 40`; otherwise keep G3 pending.
3. **Official HB dataset:** the actual 24 Harwell–Boeing `.mtx.rnd` files were not available in the reviewed Git tree; inventory/manifest placeholders are not the dataset. Do not start official runs or report RQ3 until real files, hashes, headers and manifest validation are present on the selected host.
4. **P3 official-run ownership:** P3 must confirm the actual official host (candidate P1 snapshot: Windows build 10.0.26200, RAM 15.21 GiB), 12 GiB Windows Job Object kill/MO evidence, one-worker execution, checkpoint incumbent, hard-kill/resume, attempt history, raw JSON → validation → `runs.csv`, expected-run manifest, dry-run/budget and actual queue operation.
5. **Manuscript integration:** the SAT method and appendix now exist as modular `.tex` files, but no master manuscript root file was present in the repository. P3's experimental setup/results/discussion/conclusion/English editing and final LaTeX rendering are unavailable for review.

## Remaining open issues at review time
- #25 canonical SAT config: provisional choice documented; pilot budget decision and P3 host/cap sign-off pending.
- #26 correctness suite + appendix: appendix draft exists; latest correctness suite must pass and P2 must sign off the proof.
- #28 M2 freeze: not frozen; needs fresh tests, pilot-budget resolution, P3 hard-cap/runner sign-off and all PR review/integration gates.
- #29 SAT incident response: triage tool/tests exist, but latest tests and real official raw incidents are still pending.
- #30 RQ1/RQ2 draft + G3: pilot tables exist; corrected G3 is pending raw evidence; official results still absent.
- #31–32 RQ1/RQ2 final: blocked on validated official data.
- #33 cross-review: P1 review note exists; P2 reciprocal review and final integrated consistency pass are pending.
- #34 SAT paper v0.9: modular draft exists; official figures/results, integrated master document and G4 remain pending.
- #35–36 proofread/claim verification/appendix final: partial terminology pass and proof-sketch appendix only; P2 sign-off and integrated LaTeX build pending.
- #37 P3 section cross-read/final LaTeX: blocked on P3 material and master manuscript.
- #38 M3 technical sign-off: NOT READY.
- #49 protocol review: P2/P3 review and freeze sign-off pending.

## Recommended next actions for the next AI

1. Fetch live PR #52 head. Approve/re-run CI workflow run #2 (`44010144573`) and inspect logs. Fix all failures on Ubuntu and Windows; do not settle for only the workflow being queued or action-required.
2. Review every code change on PR #52 for correctness, especially the G3 logic and raw-run-ID matching. Run a full project suite, not just the focused SAT workflow, and publish fresh counts tied to the exact tested SHA.
3. Check whether P2 added the OR-Tools CI dependency commit `acd9dd0` or later. Do not duplicate it.
4. Review PR #52 with P2 and then merge only when its tests and P1 review conditions are satisfied. After merge, update P1 branch from main using a safe merge/update-branch operation (no force push), resolve any path/document conflicts and rerun the P1 tests.
5. Close issues only when their acceptance evidence exists. Do not close #28/#29/#30/#31–38/#49 just to reduce the issue count.
6. Obtain the team decision on 60 s vs 1800 s W3 pilot budget. If 1800 s is required, rerun the appropriate pilot and reassess canonical SAT choice.
7. Obtain the 40 Core pilot raw JSONs, validate/triage them and regenerate the analysis; no raw evidence means G3 remains pending.
8. Obtain the 24 real HB files and P3 sign-off, then run the benchmark queue under the frozen protocol, perform P1 exact spot checks, validate every record and build final RQ1/RQ2/RQ3 analyses.
9. Integrate modular P1/P2/P3 LaTeX into the actual master manuscript, compile, cross-read, validate all claims/citations and obtain M3 sign-off.

## Non-negotiable guardrails
- Never fabricate raw results, hashes, timings, memory measurements, dataset availability or member sign-offs.
- Do not present synthetic W3 pilot data as official HB RQ3 data.
- Do not call a 12 GiB config value proof that the OS-level cap is enforced.
- Do not tag `v1.0` or close freeze/sign-off issues until Protocol §12 evidence exists.
- Keep P1/P2/P3 ownership boundaries explicit. P1 can prepare code/docs/reviews but cannot invent P3's actual benchmark execution or host confirmation.