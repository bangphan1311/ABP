# Release — w6-sat (W6 P2: terminology proofread, claim verification, cross-read, M3 sign-off)

**Branch:** `p2/w4-sat` · **Base commit:** `6137bf3` · **PR:** none yet (W6 tickets GH #35–#38)
**Environment touched:** `dev` only — no deploy, no push, no tag, no GitHub issue closure.

## What changed

Code and tests (untracked, new):

- `experiments/w6_signoff.py` — new — read-only audit CLI `python -m experiments.w6_signoff`
  with `audit_terminology` (`W6-T1`..`W6-T5`), `audit_variable_conventions` (`W6-T6`),
  `audit_threshold_semantics` (`W6-T7`), `verify_claims` (`W6-C1`),
  `check_lemma_numbering` (`W6-C2`), `check_appendix_integrity` (`W6-C3`),
  `audit_correlation_hygiene` (`W6-L1`), `lint_markdown_tables` (`W6-L2`),
  `record_deferred_items`, `emit_w1_checkbox_edits`/`emit_w6_checkbox_edits`/`open_boxes`,
  `evaluate_m3_gate`/`m3_finding` (`W6-M3`), `render_signoff_markdown`, `main`.
  Reuses `experiments.w5_final_analysis.ConsistencyFinding` and
  `verify_code_spec_paper_consistency()` (`C1`–`C10`), `src.sat.triage`, and live
  `src.sat.pairwise`/`src.sat.order` `build_cnf` on `benchmark/toy/path4.json`.
  No solver subprocess, no network, no `src.exact.*` import.
- `tests/experiments/test_w6_signoff.py` — new — 24 tests: clean-repo PASS for every audit,
  one seeded FAIL per audit (file + symbol/line), M3 gate pass/fail-on-component,
  CLI `--check-only` exit `0` and writes nothing, `--out`/`--out-dir` alias, seeded-fail
  exit `1`, missing W5 deliverable FAIL, checkbox evidence checks.

Generated deliverable:

- `docs/w6-sat/signoff_report.md` — new (generated, 8043 bytes) — generated-note banner,
  ticket sections `28`/`29`/`30`/`31`, `W6-M3` aggregate row, `C1`–`C10` summary line,
  deferred/external list, known pre-existing state, provenance.

Docs modified (checkbox sync, evidence-gated; emitted text from
`emit_w1_checkbox_edits` / `emit_w6_checkbox_edits`, never written by the module):

- `docs/abp-sat-encoding/issues/W1/01..07-*.md` — `[ ]` → `[x]` with `(evidence: <path>)`.
- `docs/abp-sat-encoding/issues/W6/28..31-*.md` — `[ ]` → `[x]` with `(evidence: <path>)`.
- Diff: 11 files, +47 / −47, no other doc touched.

Read-only inputs (unchanged, findings only): `docs/sat_spec.md`,
`docs/technical_appendix_draft.md`, `docs/canonical_sat_config.md`, `docs/sat_tooling.md`,
`docs/w5-sat/24..27-*.md`, `src/sat/*`, `results/`. `AGENTS.md` and
`docs/w3-w4-review-fixes/` belong to earlier change sets — **exclude both**.

## Environment

`dev` (local Windows, `.venv` Python `3.11.15`, pytest `9.1.1`). Config-only: no service,
container, database, or migration. Production not accessed. `results/` is read-only input
(70 JSONs under `results/raw`, no `results/runs.csv`). No `.github/workflows/` exists.

## Commands run

```powershell
.\.venv\Scripts\python.exe -m experiments.w6_signoff --check-only
```

→ exit `0`, `0.44 s` wall clock (NFR < 5 s). 13 check lines `OK` (`W6-T1`..`T7`,
`W6-C1`..`C3`, `W6-L1`, `W6-L2`, `W6-M3`), then:

```
P2 SAT Technical Sign-off = PASS (in-repo SAT scope). Triage 70/70 run frozen (CODE_BUG=0); consistency W5 C1–C10 PASS (15 finding); audit W6 PASS (12 finding); checkbox W1/W6 PASS. Deferred/external (không blocking): P3 LaTeX sections (P3, deferred); final English copy-edit (P3, deferred); paper/LaTeX prose (P2+P1, deferred); P3 official 24-instance runs.csv (P3, deferred); P3 manuscript merge (P3, deferred).
PASS
```

`--check-only` writes nothing (no report write, no `results/` write;
`test_cli_check_only_writes_nothing` guards it).

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp "C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-rel"
```

→ `592 passed, 3 skipped in 24.52s` — **PASS**. Baseline at `6137bf3` was
`553 passed, 3 skipped`; `+15` from W5, `+24` from W6, exact.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp "C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-rel-w6" tests/experiments/test_w6_signoff.py
```

→ `24 passed in 2.18s`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs --basetemp "C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-rel-skips"
```

→ 3 skips, all `tests\exact\test_exact_solvers.py:64` — `CPLEX CP engine/license unavailable:
Executable file 'cpoptimizer.exe' does not exists`. Environment, not a failure.

```powershell
.\.venv\Scripts\python.exe -m experiments.w5_final_analysis --check-only
```

→ exit `0`, `0.38 s`:

```
G4 PASS: triage 70/70 run frozen (CODE_BUG=0); consistency C1–C10 PASS (15 finding); checkbox W5 12/12.
PASS
check-only: không chạy solver, chỉ kiểm tra và ghi tài liệu.
```

Note: this command still rewrites the four `docs/w5-sat/24..27-*.md` files (W5 behaviour);
all four came back byte-identical (hashes below).

```powershell
.\.venv\Scripts\python.exe -m src.sat.triage
```

→ exit `0`:

```
Triage SAT: tổng 70 run | OK=68 | SOLVER_BEHAVIOR=2 | ENV_ERROR=0 | CODE_BUG=0
```

Both anomalies are the `randconn40-seed20261026` `FEAS` runs
(`pairwise/pairwise` and `pairwise/seqcounter`, `cadical195`), `lb=14`, `ub=39`,
`verified=14` — legitimate solver behaviour, zero code bugs.

Determinism check of the generated report:

```powershell
.\.venv\Scripts\python.exe -m experiments.w6_signoff --out-dir C:\Users\ducqu\AppData\Local\Temp\opencode\w6-regen
Get-FileHash docs\w6-sat\signoff_report.md -Algorithm SHA256
Get-FileHash C:\Users\ducqu\AppData\Local\Temp\opencode\w6-regen\signoff_report.md -Algorithm SHA256
```

→ byte-identical, both `35B331746832205E70DF9B9CE9C7EB27A76D9DDCC83124BFA9F37DC204E9A57E`
(8043 bytes). Hashes are over Windows CRLF working-tree bytes; on another platform compare
with `git diff --no-index <regen-dir> docs/w6-sat` instead.

W5 deliverables after the W5 regen (must match `docs/w5-sat/release.md`):

| File | SHA256 |
|---|---|
| `24-rq1-final.md` | `A6130E3084B78AA102647004F15F4D8670FCF594045D21052BE2A3FC6A981167` |
| `25-rq2-final.md` | `1440FD6527332AF04BBEE48C80A87842D80EAEA7A9BEF8A4204399C5D59B3454` |
| `26-cross-review-consistency.md` | `9BF1C7398624175165DD9FC638683B6AADCB9B72E6F0E37A57D65AA1B9BF4930` |
| `27-paper-v09-sat-sections.md` | `A055DAED380A89523D9A2B270B6BA7C3BBD832EEC347B6B8761F05CD1C1E1268` |

```powershell
git tag --list
git grep -n -E "^- \[ \]" -- docs/abp-sat-encoding/issues/W1 docs/abp-sat-encoding/issues/W6
Test-Path results\runs.csv; Test-Path .github\workflows
(Get-ChildItem results\raw\*.json).Count
```

→ tags: `v0.1-contract` only — **no `v1.0` tag exists and none was created**
(Protocol §12 gate still open).
→ zero open `- [ ]` boxes across W1 01–07 and W6 28–31; `docs/handoff/` links: none emitted.
→ `results/runs.csv` absent, `.github/workflows` absent (no CI), `results/raw` = `70`.
Change set is still uncommitted on `p2/w4-sat`.

## Verification results (M3 evidence)

| Condition | Evidence | Status |
|---|---|---|
| Terminology/notation consistent | `W6-T1`..`W6-T7` (encoding names, clause groups, `x[v][p]`/`o[v][p]` formulas, `1..n`/`0..n-1` ranges, `OPT/FEAS/TO/MO/ERR`, solver versions, Kissat excluded) all `OK` | PASS |
| Claims grounded, appendix sound | `W6-C1` 0 unsubstantiated claims, `W6-C2` 12 labels `A.1..A.8, A.3.1, A.9..A.11`, `W6-C3` `A.1..A.7` in order, path4 counts `pairwise 56/74/86`, `order 32/50/62` live-matched | PASS |
| Correlation ≠ causation, formatting intact | `W6-L1` 0 causal-phrasing violations, `W6-L2` 0 broken tables | PASS |
| W5 consistency `C1`–`C10` | `verify_code_spec_paper_consistency()` — 15 findings, all `ok` | PASS |
| Frozen dataset fully triaged | 70/70 raw runs, `CODE_BUG=0`, 2 `SOLVER_BEHAVIOR` | PASS |
| Checkbox sync W1 + W6 | 0 open boxes; every `[x]` carries a resolving `(evidence: <path>)`, no `docs/handoff/` reference | PASS |
| Reproducible generation | fresh `--out-dir` run byte-identical (`35B331…9A57E`) | PASS |
| Gate statement | `P2 SAT Technical Sign-off = PASS (in-repo SAT scope)` + 5 deferred/external entries (BR-11) | PASS |

Python tests: `592 passed, 3 skipped` (24 new W6 tests, all green).

## Security & Monitoring

- No secrets, no credentials, no network, no licensed backend import. `experiments/w6_signoff.py`
  reads repo text and builds two tiny CNFs; it never imports `src.exact.*`
  (Ortools/Gurobi/CPLEX) and never writes under `results/`.
- Trust boundaries: every audit input path is validated (`Path.is_file()`, else a
  `"<relpath>: thiếu file"` FAIL — never skipped); `--out`/`--out-dir` is the only write
  target; `--check-only` writes nothing; issue files are never written by the module
  (emitted text only, applied as a reviewed committed edit).
- Least privilege: audit is read-only over docs, `src/sat/*`, `requirements.txt`,
  `results/raw/*.json`; no `git`, no shell, no solver process spawned.
- Machine gates for automation: `python -m experiments.w6_signoff --check-only` exits `1` on
  any `W6-*`/`W6-M3` FAIL; `python -m experiments.w5_final_analysis --check-only` exits `1`
  on any `C*`/G4 fail; `python -m src.sat.triage` exits `1` on any `CODE_BUG`. These three
  plus `pytest -q --basetemp=<scratch>` are the full health signal set.
- Monitoring/alerts: none applicable (no long-running service). Freshness of
  `docs/w6-sat/signoff_report.md` is guarded by SHA256
  `35B331746832205E70DF9B9CE9C7EB27A76D9DDCC83124BFA9F37DC204E9A57E`; hand edits are a
  mismatch on the next run.
- No CI pipeline in this repo — the commands above are a manual release runbook. Adding
  `.github/workflows/` (pytest + the three `--check-only`/triage commands) is recommended
  **after** PR merge; not added here (no push, no pipeline ownership change).

## Rollback

Nothing was deployed and nothing was pushed, so rollback is source-only.

1. Nothing is committed yet, so nothing needs reverting in git history.

2. Discard the W6 run products (delete explicitly — do **not** remove `docs/w6-sat/`
   wholesale, because `requirements.md` and `spec.md` are separate work products):

   ```powershell
   Remove-Item experiments\w6_signoff.py, tests\experiments\test_w6_signoff.py
   Remove-Item docs\w6-sat\signoff_report.md, docs\w6-sat\release.md
   ```

3. Restore the 11 tracked issue files edited by the checkbox sync:

   ```powershell
   git restore docs/abp-sat-encoding/issues/W1/01-sat-spec-decision-problem.md docs/abp-sat-encoding/issues/W1/02-sat-tooling-check.md docs/abp-sat-encoding/issues/W1/03-satbackend-cadical.md docs/abp-sat-encoding/issues/W1/04-pairwise-encoding.md docs/abp-sat-encoding/issues/W1/05-order-encoding.md docs/abp-sat-encoding/issues/W1/06-loader-toy-generator.md docs/abp-sat-encoding/issues/W1/07-g1-prototype-check.md docs/abp-sat-encoding/issues/W6/28-technical-proofread.md docs/abp-sat-encoding/issues/W6/29-claim-verification-appendix.md docs/abp-sat-encoding/issues/W6/30-cross-read-p3-latex.md docs/abp-sat-encoding/issues/W6/31-m3-technical-signoff.md
   ```

4. Re-run the gate to see the remaining state:
   `python -m experiments.w6_signoff --check-only` plus `python -m src.sat.triage`
   (expect `CODE_BUG=0`). Reverting step 3 removes the checkbox sync, so the `W6-M3`
   aggregate is expected to name the checkbox component; the audit checks themselves are
   unaffected by the revert.

5. Already committed to `p2/w4-sat`: `git revert <closing-commit>` on the branch, then
   re-run `pytest -q --basetemp=<scratch>` (expect `568 passed, 3 skipped`) and
   `python -m experiments.w5_final_analysis --check-only`.

6. Already merged into `main`: revert the merge on a new branch
   (`git revert -m 1 <merge-commit>`), open a PR; do **not** force-push `main`.

No tag, no release artifact, no dataset mutation → no destructive step. `v1.0` remains
gated by Protocol §12: do not tag until PR merge, review by P1/P3, dataset/host/solver/
resource gates, and a decided `memory_limit` (`12288.0` MB is a candidate, not a decision).

## Next-week / P3 handoff notes (deferred items)

Recorded in `docs/w6-sat/signoff_report.md` §5 and in the gate statement; none is blocking
this in-repo sign-off.

| Item | Owner | Status | Handoff note |
|---|---|---|---|
| P3 LaTeX sections | P3 | deferred | Convert appendix `A.1`–`A.7` into LaTeX; keep label order `A.1..A.8, A.3.1, A.9..A.11` so `W6-C2` still parses if re-run on `.tex`. |
| final English copy-edit | P3 | deferred | Any reworded claim must keep an evidence anchor (`results/` path or `<num> s`), else `W6-C1` fails on re-run. |
| paper/LaTeX prose (next week) | P2+P1 | deferred | `docs/w5-sat/27-paper-v09-sat-sections.md` is a fragment, not the paper (W5 OQ-2); do not cite it as the paper. |
| P3 official 24-instance `runs.csv` | P3 | deferred | On arrival at `results/runs.csv`, regenerate W5 docs, record new SHA256s + source-note line, then re-run all six commands here. Keep the pilot freeze as the W5 record if numbers differ (W5 OQ-1). |
| P3 manuscript merge | P3 | deferred | `grep -n "docs/handoff"` must stay clean in generated deliverables; `C9`/`open_boxes` enforce it. |

Still open, owned by P1/P3, not frozen here: final `memory_limit`
(`12288.0` MB candidate, `canonical_sat_config()` requires it explicitly) and
`minisat22` eligibility (W5 OQ-3). Audit re-run cost is trivial (< 1 s), so re-verify with
`python -m experiments.w6_signoff --check-only` after any input doc changes.

## Risks

- Plain `pytest -q` may report `PermissionError` errors for `pytest-of-<user>`
  (host artifact) — signal: error count with `PermissionError`; mitigation: always pass
  `--basetemp`.
- Hand-edited `docs/w6-sat/signoff_report.md` breaks determinism — signal: SHA256 mismatch
  against `35B331…9A57E` on the next run; regenerate, never patch.
- Checkbox edit without a resolving evidence path — signal: `open_boxes()` non-empty,
  `W6-M3` FAIL naming the box; the gate also fails if a `docs/handoff/` link is emitted.
- `results/raw` pruned below 70 JSONs — signal: `triaged_total < 70` → `W6-M3` FAIL with
  missing-file finding (never skipped or downgraded).
- A W5 deliverable deleted (`27-*.md` etc.) — signal: `W6-T*`/`W6-C*`/`W6-L*` FAIL
  `"<relpath>: thiếu file"` and the gate fails.
- `w5_final_analysis --check-only` still rewrites the four W5 docs — signal: `git status`
  shows modified `docs/w5-sat/*` after a "check-only" run; verify the four hashes above
  instead of assuming nothing was written.
- `runs.csv` delivered mid-W6 silently shifts published numbers — signal: source-note line
  changed but report hash unchanged; re-run full comparison before sign-off.
- No CI guards these commands — signal: no check runs on the closing PR; every claim above
  depends on this manual runbook being repeated at the closing commit.
