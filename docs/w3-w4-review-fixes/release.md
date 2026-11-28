# Release — w3-w4-review-fixes

**Branch:** `p2/w4-sat` · **Base commit:** `6137bf3` · **PR:** #52 (OPEN)
**Environment touched:** `dev` only — no deploy, no remote push, no tag.

## What changed

Code (review blockers B1–B4 from P1 on #25 / #49 / PR #52):

- `experiments/analyze_rq1_rq2.py` — G3 gate returns `PENDING` when `--expected-runs`
  is omitted (no fallback to observed count); RQ1/RQ2 grouped on single-axis slices
  (`--rq1-solver`, `--rq2-abp-encoding`, `--rq2-amo-encoding`); `normalize_row` derives
  `search_mode` / `symmetry` / `warm_start` from columns or `run_id` tokens;
  `DEFAULT_REPORT_PATH` → `docs/w4-sat/23-rq1-rq2-draft-analysis.md`.
- `src/sat/solve.py` — `canonical_sat_config()` validates `memory_limit` (finite,
  `> 0`, not `bool`); `memory_limit=None` raises `ValueError` unless
  `allow_unbounded_memory=True` (dev/unit-test escape hatch). `CANONICAL_SAT_CONFIG`
  frozen fields unchanged.
- `src/sat/triage.py` — missing benchmark instance now short-circuits to
  `ENV_ERROR` / `is_anomaly=True` before `TO`/`ERR`/`MO`/`OPT`/`FEAS` classification;
  `DEFAULT_BENCHMARK_DIRS` points at `docs/sat-g1/instances` (stale
  `docs/handoff/sat-g1/instances` removed).
- Tests — `tests/experiments/test_analyze_rq1_rq2.py`, `tests/sat/test_solve.py`,
  `tests/sat/test_triage.py` extended for the four behavior changes.
- Docs (B5) — `docs/abp-sat-encoding/issues/W3/16..20-*.md` check-offs with evidence,
  `docs/abp-sat-encoding/issues/W4/21-m2-freeze-v1.md`,
  `docs/abp-sat-encoding/issues/W4/23-rq1-rq2-draft-analysis.md`,
  `docs/w4-sat/21-m2-freeze-v1.md`, `docs/w4-sat/23-rq1-rq2-draft-analysis.md`
  (regenerated), `docs/canonical_sat_config.md`.

Diff: 17 files, +604 / −88. `AGENTS.md` is also modified in the working tree and is
**not** part of this change set — exclude it from the closing commit.

## Environment

`dev` (local Windows, `.venv` Python 3.11.15, pytest 9.1.1). Config-only change:
no service, container, database, or migration. No production access.

## Commands run

```powershell
.venv\Scripts\python.exe -m pytest -q
```
→ `475 passed, 3 skipped, 78 errors` — **host artifact, not a code failure**: pytest
`tmp_path` cannot create `C:\Users\ducqu\AppData\Local\Temp\pytest-of-ducqu`
(`PermissionError: [WinError 5]`). Re-run with an explicit writable basetemp:

```powershell
.venv\Scripts\python.exe -m pytest -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-bt
```
→ `553 passed, 3 skipped in 28.06s` — **PASS**.

```powershell
.venv\Scripts\python.exe -m pytest -q -rs --basetemp=<scratch>
```
→ 3 skips, all `tests/exact/test_exact_solvers.py:64` `CPLEX CP engine/license
unavailable: Executable file 'cpoptimizer.exe' does not exist` (environment, not a fail).

```powershell
.venv\Scripts\python.exe -m pytest -q --basetemp=<scratch> tests/experiments/test_analyze_rq1_rq2.py tests/sat/test_solve.py tests/sat/test_triage.py
```
→ `68 passed in 1.38s` — all touched modules green.

```powershell
.venv\Scripts\python.exe -m src.sat.triage
```
→ `Triage SAT: tổng 70 run | OK=68 | SOLVER_BEHAVIOR=2 | ENV_ERROR=0 | CODE_BUG=0`,
exit code 0. Both anomalies are `randconn40-seed20261026` `FEAS` runs
(`pairwise/pairwise` and `pairwise/seqcounter`, `cadical195`), verified `lb=14`,
`ub=39` — legitimate solver behavior, zero code bugs.

```powershell
.venv\Scripts\python.exe -m experiments.analyze_rq1_rq2 --out <scratch>\rq-tmp.md
```
→ `Đã ghi báo cáo phân tích RQ1/RQ2 + G3: ...`, generator deterministic:
SHA256 `026817C4F9F57FA4BAEC90D1D00880EDC18DA1BAD159BF8AB65BE178FE514199` for both the
fresh run and committed `docs/w4-sat/23-rq1-rq2-draft-analysis.md` (byte-identical).
G3 renders `PENDING` (no `--expected-runs`), never `100.0%`.

```powershell
git grep -n "docs/handoff" -- docs/w4-sat docs/abp-sat-encoding docs/canonical_sat_config.md
git tag --list
```
→ `docs/handoff` matches remain only in `docs/abp-sat-encoding/issues/W2/*` (7 files,
pre-existing, outside the five touched doc groups); touched groups clean.
→ tags: `v0.1-contract` only. **No `v1.0` tag exists and none was created.**

```powershell
.venv\Scripts\python.exe -m experiments.analyze_rq1_rq2 --help
```
→ `UnicodeEncodeError: 'charmap' codec can't encode character '\u1ea3'` on this Windows
console (cp1252). `src/sat/triage.py` already reconfigures stdout to UTF-8;
`analyze_rq1_rq2.main()` does not. Cosmetic, dev-host only, does not affect report
generation. Not fixed here (out of review scope).

## Security & Monitoring

- No secrets introduced or referenced. Analysis and triage are local, read-only over
  committed CSVs and `results/raw/*.json`; reproduction stays in memory and never
  writes `results/raw/`.
- Trust-boundary validation added: `canonical_sat_config()` rejects `None`, `0`,
  negative, `bool`, and non-finite `memory_limit` with a `ValueError` naming
  `memory_limit`. Official runs can no longer carry an accidental unbounded cap.
- Gate signal for automation: `python -m src.sat.triage` exits `1` when any
  `CODE_BUG` is found, `0` otherwise — the only machine-checkable health signal in
  this change set.
- No CI pipeline exists in this repo (`.github/workflows/` absent), so verification
  above is a manual runbook. A CI workflow using the two commands
  (`pytest -q` + `python -m src.sat.triage`) is recommended **after** PR #52 merges;
  it is not added here (no push, no pipeline ownership change).
- Monitoring/alerts: none applicable — no long-running service. Evidence freshness is
  checked by the determinism hash of
  `docs/w4-sat/23-rq1-rq2-draft-analysis.md`.

## Rollback

Nothing was deployed, so rollback is source-only. Changes are still uncommitted on
`p2/w4-sat`:

1. Uncommitted working tree (discard the whole change set):
   `git restore experiments/analyze_rq1_rq2.py src/sat/solve.py src/sat/triage.py tests/experiments/test_analyze_rq1_rq2.py tests/sat/test_solve.py tests/sat/test_triage.py docs/abp-sat-encoding/issues/W3/16-pilot-rq1.md docs/abp-sat-encoding/issues/W3/17-pilot-rq2.md docs/abp-sat-encoding/issues/W3/18-canonical-config-proposal.md docs/abp-sat-encoding/issues/W3/19-correctness-suite-appendix-draft.md docs/abp-sat-encoding/issues/W3/20-bonus-sat-prototype.md docs/abp-sat-encoding/issues/W4/21-m2-freeze-v1.md docs/abp-sat-encoding/issues/W4/23-rq1-rq2-draft-analysis.md docs/canonical_sat_config.md docs/w4-sat/21-m2-freeze-v1.md docs/w4-sat/23-rq1-rq2-draft-analysis.md`
   (`AGENTS.md` intentionally left untouched — not ours.)
2. Already committed to the branch: `git revert <closing-commit>` on `p2/w4-sat`, then
   re-run `pytest -q --basetemp=<scratch>` (expect the pre-fix count) and
   `python -m src.sat.triage`.
3. Already merged into `main` via PR #52: revert the merge on a new branch
   (`git revert -m 1 <merge-commit>`), open a PR; do **not** force-push `main`.
4. Regenerate after any rollback of `analyze_rq1_rq2.py`:
   `python -m experiments.analyze_rq1_rq2`, then confirm the report matches the
   reverted code (a stale generated report is the main inconsistency risk).

No tag, no release artifact, no dataset mutation → no destructive rollback step.

## M2 freeze gate policy (`v1.0`)

Effective until P1/P2/P3 sign-off. **Neither of these may happen:**

- No `v1.0` tag (or any release tag) on `main`, this branch, or any commit.
- No official RQ3 queue run from the canonical config.

Preconditions — all must hold, verified at the closing commit:

1. **PR #52 merged** (this change set) and reviewed by P1/P3.
2. **PR #50 merged** (`docs(protocol): add ABP experimental protocol v1.0-rc`) — the
   §12 gate wording must be in `main` before any evidence is declared final.
3. **Protocol §12 gates all pass:** dataset (frozen subset), host (uniform
   environment), solver (backend + version pinned), resource enforcement (runner-level
   memory cap, §6.3), cross-review (P1/P3 reviewed), evidence (every checklist link
   resolves at the closing commit).
4. **Memory cap decided by P1/P3** — `12288.0` MB (`12.0` GiB) is a candidate only;
   P2 does not choose it. `canonical_sat_config()` requires it explicitly.
5. **G3 must be `PASS`, not `PENDING`** — the official report must be generated with
   `--expected-runs` from the frozen run plan.
6. **Triage run must show `CODE_BUG=0`** at the closing commit.

Sign-off is recorded in `docs/w4-sat/21-m2-freeze-v1.md` (§5) and the protocol
checklist. Missing any single gate → not frozen, not tagged.

## Risks

- Host pytest `tmp_path` `PermissionError` makes a plain `pytest -q` look red
  (`78 errors`) — signal: error count with `PermissionError` on
  `pytest-of-<user>`; mitigation: always pass `--basetemp`.
- `canonical_sat_config()` now raises by default — any un-updated caller or doc example
  calling it without `memory_limit` breaks: signal `ValueError: memory_limit phải là
  số hữu hạn > 0`; grep callers before merge.
- Combined `runs.csv` rows whose `run_id` lacks `__multi__`/`__sym0__`/`__ws0__` tokens
  and lack the axis columns are treated as canonical defaults — signal: RQ1/RQ2
  `n_runs` larger than the frozen plan expects; re-check `search_mode`/`symmetry`/
  `warm_start` columns from the runner schema.
- Generated report drift: `docs/w4-sat/23-rq1-rq2-draft-analysis.md` must equal a fresh
  generator run — signal: SHA256 mismatch against
  `026817C4F9F57FA4BAEC90D1D00880EDC18DA1BAD159BF8AB65BE178FE514199`.
- Missing-instance `ENV_ERROR` precedence can mask a real solver bug when the instance
  file is absent — signal: `ENV_ERROR` count rising in triage summaries; verify
  `DEFAULT_BENCHMARK_DIRS` resolves before trusting the classification.
- No CI workflow guards these commands — signal: no check runs on PR #52; every
  evidence claim depends on the manual runs recorded above.
