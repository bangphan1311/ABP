# UAT — W2 dry-run (Product Manager sign-off)

Date: 2026-11-03 · Branch: `p2/w4-sat` · HEAD `6b6b8b5` (working tree,
uncommitted — same state QA and staging verified).

UAT role: user-level acceptance of the delivered W2 `--dry-run` work against
`scope.md` (P0/P1, A1–A11, D1–D6, contract alignment) and `qa-staging.md`.
Method: independent re-execution of observable criteria (suite, CLI probes,
git diffs), not a repeat of QA's internal probes.

## Verdict

**PASS — accepted.** All P0 and P1 scope items verified. All acceptance
criteria A1–A11 and D1–D6 observable and met. Contract alignment intact
(`CONTRACT.md` untouched, `DRY_RUN` never persisted). No blocking issues.
Two pre-existing low-severity observations from `qa-staging.md` are accepted
as documented (see §4).

---

## 1. UAT-ran commands and results

Interpreter `.venv\Scripts\python.exe` (3.11.15), repo root, 2026-11-03.

### 1.1 Full regression (A11)

```
.venv\Scripts\python.exe -m pytest tests -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp
```

**538 passed, 3 skipped in 18.87s** — green per scope definition (3 skips are
the baseline CPLEX CP engine skips). Runner-only re-check: `pytest tests/runner`
→ **30 passed**, 24 of them dry-run tests (matches dev-notes §1.3).

### 1.2 Happy-path CLI dry-run, toy instance (A9, P0 §4.1 reproduction)

```
.venv\Scripts\python.exe -m src.runner --instance benchmark/toy/path4.json --method sat --abp-encoding pairwise --amo-encoding seqcounter --sat-solver cadical195 --search-mode multi --time-limit 1800 --out results/raw --dry-run
```

Exit `0`, exactly 5 `DRY_RUN` lines, byte-identical to the stdout recorded in
`docs/handoff/w2-sat/15-m1-gate-evidence.md` §4.1: run_id suffix
`__tl1800.0__mlNone`, `hard_limit=1830.0`, `memory_limit=none`
`memory_limit_enforced=false`, relative `out_file` under `results\raw`,
`exists=false resume_would_skip=false`. Booleans render `true`/`false`
plain (B2), `None` renders `none`.

### 1.3 No-write proof (A2, C1/C14)

Before/after entry count under `results/raw`: **70 → 70**;
`git status --porcelain results/raw` empty. Dry-run with `--resume` composed
(R14): exit 0, same 5 lines. Non-ASCII `--out` (`...\đường`) with
`PYTHONIOENCODING=cp1252`: exit 0, 5 lines, lossy `???ng` rendering, no
`UnicodeEncodeError` (B1 fix confirmed at user level).

### 1.4 Error paths (A7, A10)

- Instance with `n>0`, empty edges → exit `2`, stderr
  `DRY_RUN ERROR: Instance is empty (n = 0 or no edges).` — exact expected
  message, no traceback.
- `--method nope` → exit `2`, `DRY_RUN ERROR: Method 'nope' không có trong
  registry...` (lossy Vietnamese through cp1252 pipe, no traceback).

### 1.5 Git hygiene (D3, D5, D6)

- `git status --porcelain`: exactly the 12 intended modified files + 1
  untracked dir (`docs/handoff/w2-dry-run/`). `docs/handoff/sat-g1/` clean.
  `CONTRACT.md` not modified.
- `git diff --numstat`: evidence doc **42+/0-** (pure additions);
  `tests/runner/test_runner.py` **441+/0-** (old tests untouched);
  `src/runner/runner.py` 37+/1- (the 1 deletion is the docstring line replaced
  by the expanded docstring — real-run code below it byte-identical);
  `src/runner/__main__.py` 71+/0- (try/except wraps only the dry-run branch).

---

## 2. Acceptance criteria — code (A1–A11)

| # | Criterion | Evidence | Result |
|---|---|---|---|
| A1 | Dry-run record shape: `RUN_FIELDS`+`config`+`solution`+`metadata`+`dry_run`; `status=="DRY_RUN"`; result fields/`solution`/`error` `None`; `dry_run` plain dict, `out_file` `str` | `test_dry_run_record_shape` (green); code read `runner.py:64–76` | PASS |
| A2 | No writes: absent dir stays absent; pre-existing dir untouched; no tempdir block | `test_dry_run_writes_nothing`, `test_dry_run_preexisting_dir_untouched`, `test_dry_run_does_not_enter_tempdir` + UAT probe (70→70) | PASS |
| A3 | `hard_limit = time_limit + KILL_GRACE_SECONDS`, constant read at call time, `None` → `None`, no hardcoded `30.0` | `test_dry_run_hard_limit_follows_grace_constant`; live `hard_limit=1830.0` | PASS |
| A4 | run_id == `make_run_id(instance, cfg)` == real run; type-sensitive suffix (`tl1800.0__mlNone` CLI float, `tl30__mlNone` API int) | `test_dry_run_run_id_matches_real_run`, `test_dry_run_run_id_ignores_edge_content` | PASS |
| A5 | Resume: garbage file at `out_file` → `resume_would_skip=True`, record still `DRY_RUN`; no file → `False` | `test_dry_run_resume_reports_without_parsing_garbage`, `test_dry_run_resume_absent_file` | PASS |
| A6 | No worker spawn; spy covers args+kwargs incl. `Popen` variants | `test_dry_run_spawns_no_worker` | PASS |
| A7 | Invalid instance raises same type+message as real run; `n>0` empty edges hits exact message; nothing written | `test_dry_run_validation_matches_real_run` + UAT probe (exact message) | PASS |
| A8 | Unknown registry method → `ValueError` "không có trong registry"; dotted path passes; `sys.modules` snapshot shows no new solver-module imports | `test_dry_run_method_check_imports_nothing`; code `runner.py:52–56` | PASS |
| A9 | CLI stdout exactly 5 lines per R12 format, bool `true`/`false`, `err==""`, exit 0, nothing written under `--out` | `test_cli_dry_run_prints_five_lines` + UAT probe §1.2 | PASS |
| A10 | CLI error: `DRY_RUN ERROR:` prefix, no traceback, exit 2, survives cp1252 and utf-8 | `test_cli_dry_run_failure_exits_2_cp1252_safe`, `test_cli_dry_run_unknown_method_exits_2` + UAT probe §1.4 | PASS |
| A11 | Old tests untouched, full suite green (passed+skipped) via venv + external basetemp | numstat 441+/0-; suite §1.1 | PASS |

Coverage beyond the letter of A1–A11: duplicate-edge dedup, `memory_limit`
verbatim, non-ASCII `instance.id`, CLI `--out` non-ASCII + cp1252, CLI
without `--dry-run` unchanged, dotted-path method via CLI — all present as
named tests and green.

## 3. Acceptance criteria — docs (D1–D6) and P1

| # | Criterion | Evidence | Result |
|---|---|---|---|
| D1 | Every box ticked by this task has a pointer in its file's `## Closure evidence (2026-11-03)` | All 8 ticket files inspected; diffs show Closure evidence added to each | PASS |
| D2 | Unticked boxes annotated; expected set = only 09 box 2; 13 box 3 ticked unconditionally | 09 box 2 `[ ]` + `*(N/A — xem Closure evidence)*`; 13 box 3 `[x]` with GH #20/#42, PR #48 pointers | PASS |
| D3 | Evidence doc diff touches only §4.1 (new) + 1 §6 bullet; §1–§5 and §6 decision byte-identical; §4.1 output parses per R12 | numstat 42+/0-, exactly 2 hunks (@@203 §4.1 insert, @@271 §6 pointer); §4.1 stdout reproduced byte-identically in §1.2 | PASS |
| D4 | Ticket 15 box 2 `[x]` + pointer §4.1 + §3; old parenthetical replaced; NO-GO lines byte-identical | Diff: parenthetical (3 lines) removed, pointer line added; "Kết quả (2026-10-20): **NO-GO Bonus**" untouched | PASS |
| D5 | `Status:`/`Owner:`/`Blocked by:` unchanged in all tickets; new prose Vietnamese | No such line in any ticket diff; new text Vietnamese | PASS |
| D6 | No task-caused change outside the intended file list; no stash/revert | git status = intended set only; `results/raw` 70→70; basetemp external | PASS |
| P1-6 | Ticks 08–14 per R17 mapping; 12 box 1 says 8/8 (Kissat N/A), not 2×2×3=12; `_validate_solver` pointer complete (`src/sat/solve.py` dòng 424 + 2 test files) | Diffs of 08/10/11/12/14 verified same pattern as 09/13; 12 Closure evidence wording confirmed | PASS |
| P1-7 | Closure evidence sections in every ticked file, heading as R15 | Present in all 8 | PASS |

**P0 items 1–5:** all verified (API shape/real-run unchanged via code read +
diff; CLI contract via §1.2–§1.4; tests via §1.1; §4.1 via reproduction;
ticket 15 via diff).

**Contract alignment:** `CONTRACT.md` §5 untouched (not in diff). `DRY_RUN` is
a runner-level status only: the dry-run branch returns before any write
(`runner.py:50–76`), no persistence path, `runs.csv` column comment in
`schema.py` untouched. `memory_limit_enforced=false` literal states current
truth as scoped (C2).

## 4. Issues and dispositions

None blocking. Recorded for the gate:

1. **`wall_time` in dry-run excludes `read_instance` time** (`runner.py:51`,
   timer starts after line 48) — carried from `qa-staging.md`. Accepted:
   cosmetic for a pre-flight report; fix only if a consumer compares dry-run
   vs real-run cost. Owner to pick up if reported again.
2. **`make_run_id` computed in both dry-run and real-run paths** — pure
   function, redundant not wrong. Accepted, no action.
3. **UAT tooling note (not a product defect):** piping `git diff -U0` through
   `Select-String` in this console initially hid the checkbox bracket lines;
   direct `git diff` per file was used as the authoritative check. Future
   reviewers: diff per file, don't filter through the console.

## 5. Not covered by UAT (inherited limits, accepted)

Same limits `qa-staging.md` §"Could not check": real solver runs (out of
dry-run scope), Linux/macOS `out_file` separator rendering, a true cp1252
console (probes used pipes), `--help` under cp1252 (pre-existing, out of
scope), `--dry-run` for `experiments/pilot_rq*.py` (out of scope).

## 6. Sign-off

Scope delivered as specified; M1 decision record (§6 NO-GO) preserved
byte-identical; the only closure this work claims is the `--dry-run` blocker
(ticket 15 box 2). Ready for Gate 2 handover on the dry-run contract.
