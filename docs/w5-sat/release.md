# Release — w5-sat (W5 P2: RQ1 final, RQ2 final, cross-review consistency, paper v0.9)

**Branch:** `p2/w4-sat` · **Base commit:** `6137bf3` · **PR:** none yet (W5 tickets GH #31–#34)
**Environment touched:** `dev` only — no deploy, no remote push, no tag, no GitHub issue closure.

## What changed

Code and tests:

- `experiments/w5_final_analysis.py` — new — CLI `python -m experiments.w5_final_analysis`
  with `load_sources`, `load_graph_metadata`, `find_larger_cnf_faster_solve_cases`,
  `cross_size_runtime_inversion`, `project_cnf_growth`, `extract_feas_probe_trajectories`,
  `solver_sensitivity_table`, `verify_code_spec_paper_consistency` (C1–C10),
  `evaluate_g4_gate`, `render_w5_markdown`. Reads frozen data only; no solver subprocess.
- `tests/experiments/test_w5_final_analysis.py` — new — 15 tests covering projection
  anchors, source preference, density/UB, larger-CNF-faster extraction, FEAS trajectories,
  sensitivity winner/cv, C1–C10 pass + perturbed-anchor FAIL with BR-9 message,
  canonical memory contract, CLI writes four docs and exits `0`, P1 R1–R6 source evidence.

Generated deliverables (ticket → GH issue):

- `docs/w5-sat/24-rq1-final.md` — #31 — RQ1 summary table, conclusion, three frozen
  case studies (smaller-CNF-slower, larger-CNF-faster, `pairwise` growth + MO projection).
- `docs/w5-sat/25-rq2-final.md` — #32 — RQ2 ranking (OPT → PAR2 → TO → memory →
  per-instance sensitivity), per-instance table, sensitivity + FEAS/`BR-8` case studies,
  Kissat exclusion.
- `docs/w5-sat/26-cross-review-consistency.md` — #33 — C1–C10 findings table, P1 R1–R6
  recheck (all `closed`), five fairness points, stale-link cleanup, G4 readiness.
- `docs/w5-sat/27-paper-v09-sat-sections.md` — #34 — §3.1–§3.10, RQ1 Final, RQ2 Final,
  Appendix A.1–A.7 (W5 state), fairness paragraph, trace table, G4 status.

Docs modified:

- `docs/sat_spec.md`, `docs/technical_appendix_draft.md`, `docs/w2-sat/14-sat-methodology.md`,
  `docs/w2-sat/15-m1-gate-evidence.md`, `docs/canonical_sat_config.md` — W5 anchors refreshed,
  stale handoff-folder links repointed in-repo (BR-11).
- `docs/abp-sat-encoding/issues/W5/{24,25,26,27}-*.md` — 12/12 checklist boxes checked with
  evidence (each box maps to a section of the generated deliverable).

Diff scope: 9 tracked files, +127 / −49; 6 new files (`docs/w5-sat/` ×6, code, tests).
`AGENTS.md` and `docs/w3-w4-review-fixes/` belong to earlier change sets — **exclude both**
from this commit.

## Environment

`dev` (local Windows, `.venv` Python `3.11.15`, pytest `9.1.1`). Config-only: no service,
container, database, or migration. Production not accessed. `results/` is read-only input.

## Commands run

```powershell
.\.venv\Scripts\python.exe -m experiments.w5_final_analysis --check-only
```

→ exit `0`. Writes all four docs, then:

```
G4 PASS: triage 70/70 run frozen (CODE_BUG=0); consistency C1–C10 PASS (15 finding); checkbox W5 12/12.
PASS
check-only: không chạy solver, chỉ kiểm tra và ghi tài liệu.
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp "C:\Users\ducqu\AppData\Local\Temp\opencode\pytest"
```

→ `568 passed, 3 skipped in 38.76s` — **PASS**. Baseline at `6137bf3` was `553 passed,
3 skipped`; delta is exactly the 15 new W5 tests.

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs --basetemp "C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-w5b"
```

→ 3 skips, all `tests\exact\test_exact_solvers.py:64` — `CPLEX CP engine/license unavailable:
Executable file 'cpoptimizer.exe' does not exist`. Environment, not a failure.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp <scratch> tests/experiments/test_w5_final_analysis.py
```

→ `15 passed in 0.46s`.

```powershell
.\.venv\Scripts\python.exe -m experiments.w5_final_analysis --out-dir C:\Users\ducqu\AppData\Local\Temp\opencode\w5-regen
Get-FileHash <dir>\*.md
```

→ regeneration is byte-identical to the committed deliverables:

| File | SHA256 |
|---|---|
| `24-rq1-final.md` | `A6130E3084B78AA102647004F15F4D8670FCF594045D21052BE2A3FC6A981167` |
| `25-rq2-final.md` | `1440FD6527332AF04BBEE48C80A87842D80EAEA7A9BEF8A4204399C5D59B3454` |
| `26-cross-review-consistency.md` | `9BF1C7398624175165DD9FC638683B6AADCB9B72E6F0E37A57D65AA1B9BF4930` |
| `27-paper-v09-sat-sections.md` | `A055DAED380A89523D9A2B270B6BA7C3BBD832EEC347B6B8761F05CD1C1E1268` |

Hashes are over the Windows (CRLF) working-tree bytes; on another platform compare with
`git diff --no-index <regen-dir> docs/w5-sat` instead of the hash list.

```powershell
.\.venv\Scripts\python.exe -m src.sat.triage
```

→ `Triage SAT: tổng 70 run | OK=68 | SOLVER_BEHAVIOR=2 | ENV_ERROR=0 | CODE_BUG=0`.
Both anomalies are the `randconn40-seed20261026` `FEAS` runs (`pairwise/pairwise` and
`pairwise/seqcounter`, `cadical195`), `lb=14`, `ub=39` — legitimate behaviour, zero bugs.

Placeholder-marker and legacy-handoff-path sweeps were run over the four generated docs plus
`docs/sat_spec.md`, `docs/technical_appendix_draft.md`, `docs/w2-sat/14-sat-methodology.md`
and `docs/w2-sat/15-m1-gate-evidence.md`.

→ no matches (BR-10, BR-11). Checker `C9` enforces the same two properties on every run and
reports `markers=[]`, `handoff=[]`, `broken=[]`.

```powershell
git tag --list; git status --porcelain
Test-Path results\runs.csv; Test-Path .github\workflows
```

→ tags: `v0.1-contract` only — **no `v1.0` tag exists and none was created**.
`results/runs.csv` absent; `.github/workflows/` absent (no CI). Change set is still
uncommitted on `p2/w4-sat`.

## Verification results (G4 evidence)

| Condition | Evidence | Status |
|---|---|---|
| Frozen dataset 100% analysed | 70/70 raw runs triaged, `CODE_BUG=0`, 2 `SOLVER_BEHAVIOR` | PASS |
| Code ↔ spec ↔ paper ↔ appendix consistent | `C1`–`C10`, 15 findings, all `ok` | PASS |
| P1 exact-family R1–R6 | all `closed` with `file:line` evidence in `26-*.md` §2 | PASS |
| Placeholders / stale links | zero placeholder markers, zero legacy handoff-path references, zero broken links | PASS |
| W5 checklist boxes | 12/12 checked in `docs/abp-sat-encoding/issues/W5/*` | PASS |
| Reproducible generation | four docs byte-identical on rerun | PASS |
| Gate statement | `G4 PASS: triage 70/70 run frozen (CODE_BUG=0); consistency C1–C10 PASS (15 finding); checkbox W5 12/12.` | PASS |

## Security & Monitoring

- No secrets, no network, no licensed backend import. The consistency checker inspects
  text/AST only (`ast` + `Path.read_text`), never imports `src.exact.*`.
- Trust-boundary checks: all CLI paths validated with `Path.is_file()`/`is_dir()`;
  `project_cnf_growth` raises `ValueError` for `n < 2`, `m < 1`, unknown encoding, or
  `k` outside `1..n-1`; `canonical_sat_config()` still requires an explicit positive
  `memory_limit` (`C7`).
- Data integrity: nothing is written under `results/`; frozen CSVs and raw JSON are
  read-only input (NFR).
- Machine gates for automation: `--check-only` exits `1` on any `C*` fail or G4 fail;
  `python -m src.sat.triage` exits `1` on any `CODE_BUG`. No other health signal exists.
- No CI pipeline in this repo, so the two commands above are a manual runbook. A workflow
  running `pytest -q` + `python -m experiments.w5_final_analysis --check-only` +
  `python -m src.sat.triage` is recommended **after** PR merge; not added here.
- Monitoring/alerts: none applicable (no long-running service). Freshness of the four
  generated docs is guarded by the SHA256 list above and by `C9` link/marker checks.

## Rollback

Nothing was deployed and nothing was pushed, so rollback is source-only.

1. Discard the W5 change set (untracked artefacts — delete explicitly, do **not**
   `rm -rf docs/w5-sat`, because `requirements.md` and `spec.md` are separate work
   products):

   ```powershell
   Remove-Item experiments\w5_final_analysis.py, tests\experiments\test_w5_final_analysis.py
   Remove-Item docs\w5-sat\24-rq1-final.md, docs\w5-sat\25-rq2-final.md, docs\w5-sat\26-cross-review-consistency.md, docs\w5-sat\27-paper-v09-sat-sections.md, docs\w5-sat\release.md
   ```

2. Restore the 9 tracked docs touched by W5 (leave `AGENTS.md`,
   `docs/w3-w4-review-fixes/`, and the W3/W4 review-fix files alone — they are not ours):

   ```powershell
   git restore docs/sat_spec.md docs/technical_appendix_draft.md docs/w2-sat/14-sat-methodology.md docs/w2-sat/15-m1-gate-evidence.md docs/canonical_sat_config.md docs/abp-sat-encoding/issues/W5/24-rq1-final.md docs/abp-sat-encoding/issues/W5/25-rq2-final.md docs/abp-sat-encoding/issues/W5/26-cross-review-consistency.md docs/abp-sat-encoding/issues/W5/27-paper-v09-sat-sections.md
   ```

3. Already committed to `p2/w4-sat`: `git revert <closing-commit>` on the branch, then
   re-run `pytest -q --basetemp=<scratch>` (expect `553 passed, 3 skipped`) and
   `python -m src.sat.triage` (expect `CODE_BUG=0`).

4. Already merged into `main`: revert the merge on a new branch (`git revert -m 1
   <merge-commit>`), open a PR; do **not** force-push `main`.

5. Regenerate after any rollback of `experiments/w5_final_analysis.py`:
   `python -m experiments.w5_final_analysis`, then compare against the SHA256 list.
   A stale generated doc against reverted code is the main inconsistency risk.

No tag, no release artifact, no dataset mutation → no destructive step. Same policy as
`docs/w3-w4-review-fixes/release.md`: no `v1.0` tag until Protocol §12 gates pass.

## W6 / P3 handoff notes (`results/runs.csv` integration)

- `results/runs.csv` does not exist today. `load_sources` prefers it automatically once it
  appears at the default path; a non-default path requires `--runs-csv PATH`. One source
  only — never mixed with the pilot CSVs (BR-1).
- On arrival, regenerate all four docs and record the new SHA256 list plus the changed
  source-note line (`Nguồn dữ liệu: ...`) in the W6 handoff. Every number in `24`/`25`/`27`
  and the paper §3/RQ1/RQ2 tables must then be re-checked against the new report; the
  trace table in `27-*.md` is the mapping.
- Rows without `search_mode`/`symmetry`/`warm_start` columns or matching `run_id` tokens are
  treated as canonical defaults (`normalize_row`). Verify RQ1 has 10 runs per config and RQ2
  10 runs per solver before trusting a slice.
- If official numbers differ from the pilot freeze, keep the pilot report as the W5 record
  and state the discrepancy explicitly (OQ-1); do not silently overwrite `docs/w5-sat/*`.
- Re-run after regeneration: `--check-only` (must exit `0`, `C9` re-validates links and
  markers) and `python -m src.sat.triage`. Re-check the 12 checklist boxes only where the
  new evidence exists.
- Open decisions still owned by P1/P3 and not frozen here: OQ-2 paper v0.9 final path
  (`27-*.md` is a SAT-section fragment), OQ-3 `minisat22` eligibility, OQ-4 final
  `memory_limit` (`12288.0` MB is a candidate; `--cap-mb` parameterises the projection).

## Risks

- Plain `pytest -q` may report `PermissionError` errors for `pytest-of-<user>`
  (host artifact, seen at `6137bf3`) — signal: error count with `PermissionError`;
  mitigation: always pass `--basetemp`.
- Hand-edited generated docs break determinism — signal: SHA256 mismatch against the list
  above on the next run; re-run the generator instead of editing.
- `runs.csv` delivered mid-W6 silently shifts published numbers — signal: source-note line
  changed but hashes/paper tables unchanged; re-run the full comparison before sign-off.
- `runs.csv` rows missing control axes inflate slice sizes — signal: RQ1/RQ2 `Runs` column
  ≠ 10; inspect the axis columns.
- No CI guards these commands — signal: no check runs on the closing PR; every claim above
  depends on this manual runbook being repeated at the closing commit.
- `27-*.md` is a fragment, not the paper — signal: P1 merge of the SAT sections into the
  final paper path is still pending (OQ-2); do not cite `27-*.md` as the paper.
