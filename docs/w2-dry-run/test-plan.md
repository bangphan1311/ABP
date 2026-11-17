# Test Plan — W2 dry-run (`--dry-run`, W2 checkbox closure, M1 evidence)

Phase 2 Technical Prep. Authoritative sources: `requirements.md` and `scope.md`
(this directory). Code baseline read: `src/runner/runner.py`,
`src/runner/__main__.py`, `src/runner/schema.py`, `src/runner/registry.py`,
`src/common/models.py`, `src/sat/loader.py`, `tests/runner/test_runner.py`.

Only test cases are specified here. No production code is changed by this
document. Acceptance-criteria IDs (A1–A11, D1–D6) are the ones defined in
`requirements.md` §"Acceptance criteria (testable)"; the coverage matrix below
maps every ID to at least one executable check.

---

## 0. Environment and execution contract

- Interpreter: `.venv\Scripts\python.exe` (3.11, has pysat). Global `python`
  (3.13) lacks pysat and cannot run the suite — do not use it.
- Pytest command (Windows temp root is permission-locked; `--basetemp` must be
  outside the repo):

  ```
  .venv\Scripts\python.exe -m pytest tests -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp
  ```

- New tests go in `tests/runner/test_runner.py`; existing tests in that file are
  **not edited** (A11). No new test dependency; `pytest` + `monkeypatch` +
  `tmp_path` only.
- "Green" = passed + skipped; **3 skips expected** (CPLEX CP engine missing).
  Failures = red. Do not "fix" skips.
- CLI tests: run the module with `sys.executable` / the venv interpreter as a
  subprocess, always pass `--out <tmp_path>` — never assert the repo-absolute
  `DEFAULT_OUT_DIR`.
- Expected `run_id` values in every test are computed by calling
  `make_run_id(...)`; the R12 example block is a *format* sample, never a value
  source.

---

## 1. Coverage matrix

| ID | Requirement | Test(s) |
|---|---|---|
| A1 | Record shape (`RUN_FIELDS` + `config`/`solution`/`metadata`/`dry_run`), `status=="DRY_RUN"`, result-derived fields `None`, `dry_run` plain dict with `out_file: str` | U1, U1b |
| A2 | No side effects: `out_dir` not created; pre-existing dir untouched; no `tempfile.TemporaryDirectory` block | U2, U2b |
| A3 | `hard_limit == time_limit + KILL_GRACE_SECONDS`, constant read at call time, `None` propagation | U3, U3b |
| A4 | `run_id == make_run_id(instance, cfg)`; identical to real run; no collision; type-sensitive suffix | U4, U4b, U4c |
| A5 | Resume reporting: `exists`, `resume_would_skip`, garbage file never parsed/returned | U5, U5b |
| A6 | No worker spawn; `git describe` call allowed; spy captures args+kwargs | U6 |
| A7 | Validation parity with real run (same type/message), nothing written | U7, U7b |
| A8 | Static method check only; unknown method raises; dotted path passes; no new modules imported | U8, U8b |
| A9 | CLI success: 5-line stdout, `main()==0`, empty stderr, nothing written | C1, C1b, C2 |
| A10 | CLI failure: `DRY_RUN ERROR:` on stderr, no traceback, exit 2, cp1252-safe | C3, C3b, C4 |
| A11 | Pre-existing tests unmodified and green; full suite via venv + basetemp | R1, R2 |
| D1 | Every box ticked by this task has an evidence pointer in its `## Closure evidence (2026-11-03)` section | D1 |
| D2 | Every unticked box has a reason; expected unticked set = 09 box 2 only | D2 |
| D3 | Evidence-doc diff touches only §4.1 + one §6 pointer; §4.1 parses against R12 | D3 |
| D4 | Ticket 15 box 2 `[x]` + §4.1/§3 pointer; NO-GO lines byte-identical | D4 |
| D5 | `Status:`/`Owner:`/`Blocked by:` unchanged; new prose Vietnamese | D5 |
| D6 | No out-of-scope changes caused by the task; pre-existing dirt not counted | D6 |

Additional non-ID checks requested by the brief: **branch-order preservation**
(U2c) and **`DryRunRecord` type contract** (U1c — no dataclass).

---

## 2. Unit tests — `run_one(..., dry_run=True)` (API)

Shared fixture: reuse the existing `path4` fixture (writes
`generator.path(4)` to `tmp_path/"path4.json"`). New tests must not modify the
existing tests or the fixture. Typical config:
`Config(method="oracle", time_limit=30)`; for solver-independent checks prefer
`oracle`.

### U1 — A1: record shape and nulls
Call `rec = runner_mod.run_one(path4, Config(method="oracle", time_limit=30), tmp_path/"raw", dry_run=True)`.

Assert:
- `rec["status"] == "DRY_RUN"`;
- every name in `RUN_FIELDS` present (`for f in RUN_FIELDS: assert f in rec`);
- `rec["config"] == asdict(cfg)`-equivalent (dict, not dataclass);
- `rec["solution"] is None`, `rec["metadata"] == {}`, `rec["error"] is None`;
- `lb, ub, t_encode, t_solve, t_total, variables, clauses, peak_memory` all `None`;
- `rec["solver"] == "oracle"` (i.e. `config.sat_solver or config.method`);
- `rec["run_id"]`, `rec["instance"]`, `rec["git_tag"]`, `rec["host"]`,
  `rec["timestamp"]`, `rec["wall_time"]` are populated;
- `rec["time_limit"] == 30`, `rec["memory_limit"] is None`, `rec["seed"] == 0`,
  `symmetry is False`, `warm_start is False`;
- `isinstance(rec, dict)`.

### U1b — A1: `dry_run` sub-record is a plain dict of the right type
Assert `rec["dry_run"]` is a `dict` (not a dataclass), with keys exactly
`{"out_file", "exists", "resume_would_skip", "hard_limit", "n", "m"}`;
`isinstance(rec["dry_run"]["out_file"], str)`; `n == 4`, `m == 3` (loader
dedup counted).

### U1c — A1/I4: no new dataclass type escapes
Assert `type(rec) is dict`, `type(rec["dry_run"]) is dict`, and
`not hasattr(rec["dry_run"], "__dataclass_fields__")`. (This is the "no new
dataclass" carve-out from `scope.md` I4.)

### U2 — A2: no directory created
Fresh `out = tmp_path/"raw"` (absent). Dry-run. Assert `out.exists() is False`
and no file exists anywhere under `tmp_path` besides the fixture instance file.

### U2b — A2: pre-existing directory untouched
Create `out = tmp_path/"raw"`; write a sentinel file `out/"sentinel.txt"` and an
unrelated JSON; snapshot `{p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p
in out.iterdir()}` before; dry-run; snapshot after; assert identical set and no
new entries. (T5 in scope text: "no file added/modified under `out_dir`".)

### U2c — A2/I2: dry-run does not enter the tempdir block
Monkeypatch `runner_mod.tempfile.TemporaryDirectory` to a spy that raises
`AssertionError` if entered; dry-run must succeed without raising. Optionally
also spy on `Path.mkdir` calls made through the dry-run path and assert none
were invoked (note: unrelated `mkdir` in test setup must be counted before the
call or filtered by argument).

### U2d — branch order preservation (brief requirement)
Record call order with spies: wrap `runner_mod.read_instance`,
`runner_mod.make_run_id` (imported name in `runner.py`), and the temporary-dir
spy to append labels. Expected order for `dry_run=True`:
`read_instance` → method check (no call; proven by A8) → `make_run_id` →
build `out_file` → return. Assert `make_run_id` is called after
`read_instance`, and `TemporaryDirectory` never appears. Also assert the same
order holds for `dry_run=False` up to `make_run_id`, then the tempdir block is
entered — i.e. no branch reordering introduced.

### U3 — A3: budget formula
`cfg = Config(method="oracle", time_limit=1800.0)`; dry-run; assert
`rec["dry_run"]["hard_limit"] == 1800.0 + runner_mod.KILL_GRACE_SECONDS`
(currently 30.0, but read the module attribute, do not hardcode).

### U3b — A3: constant read at call time; `None` propagation
1. `monkeypatch.setattr(runner_mod, "KILL_GRACE_SECONDS", 7.5)`; dry-run with
   `time_limit=100.0` → `hard_limit == 107.5`.
2. `Config(method="oracle", time_limit=None)` → `hard_limit is None`.
3. `Config(method="oracle", time_limit=0)` → `hard_limit == 0.0 + KILL_GRACE_SECONDS`
   (R10: not rejected).
Assert no literal `30.0` in the new code path — mechanical check via grep on the
diff, not a runtime test (record as a review gate).

### U4 — A4: deterministic run_id
`rec["run_id"] == make_run_id(read_instance(path4), cfg)`. Run twice → identical
`run_id`. Vary `time_limit` int vs float:
`Config(time_limit=30)` → suffix `...__tl30__mlNone`; `Config(time_limit=1800.0)`
→ `...__tl1800.0__mlNone`; `None` → `...__tlNone__mlNone`. Assert suffix with
`rec["run_id"].endswith(...)` or `__` split — do not compare against the R12
example string wholesale.

### U4b — A4: dry-run and real run agree, no collision
1. `cfg = Config(method="oracle", time_limit=30)`;
2. `dry = run_one(path4, cfg, tmp_path/"dryout", dry_run=True)`;
3. `real = run_one(path4, cfg, tmp_path/"realout")` (clean dir);
4. assert `dry["run_id"] == real["run_id"] == make_run_id(...)`;
5. assert the real file exists at `tmp_path/"realout"/f"{real['run_id']}.json"`
   and `dry` wrote nothing under `tmp_path/"dryout"`;
6. assert no file under `results/raw` was touched by the test (tests must never
   target the repo `results/raw`; assert via explicit `--out`/`out_dir` args).

### U4c — A4/C13: run_id ignores edge content
Two instance files with the same `id` but different edge sets → same `run_id`
(documented pre-existing property of `make_run_id`). Assert equality; this
documents the duplicate-run_id hazard US2 relies on.

### U5 — A5: resume reporting, garbage file
Compute `run_id = make_run_id(...)`; `out = tmp_path/"raw"`;
`out.mkdir()`; `target = out/f"{run_id}.json"`; write `b"not json {{{"`.
1. `rec = run_one(path4, cfg, out, resume=True, dry_run=True)` →
   `rec["status"] == "DRY_RUN"`, `rec["dry_run"]["exists"] is True`,
   `rec["dry_run"]["resume_would_skip"] is True`; record is not the garbage;
   file bytes unchanged after the call.
2. same without `resume` → `exists True`, `resume_would_skip False`.

### U5b — A5: absent file
`out` exists but no target file → `exists False`, `resume_would_skip False`
regardless of `resume`.

### U6 — A6: no worker spawn
Spy `runner_mod.subprocess.run` with a recorder capturing `(args, kwargs)` and
delegating to the real function. Dry-run on `path4` with `method="oracle"`.
Assert:
- no recorded call whose `args[0:3] == [sys.executable, "-m", "src.runner.worker"]`;
- fallback: no recorded `args` element equals `"src.runner.worker"`;
- any `git describe` call is allowed and must not fail the assertion (it carries
  `capture_output=True`, `text=True`, `timeout=10`, `cwd=<repo root>`);
- if the implementation uses `Popen`/`check_output` for the worker, patch those
  too and assert no worker pattern — record this as "spy must cover the chosen
  spawn API" review gate.
Assert `rec["status"] == "DRY_RUN"` after the spy run.

### U7 — A7: validation parity (empty graph)
Instance with `n=4` and `edges=[]` (write via `json` or `write_instance`):
`n=0` + edges would hit the out-of-range message first; use `n>0` + empty edges
to hit the exact loader message.
- `with pytest.raises(ValueError, match="Instance is empty")` for both
  `dry_run=True` and `dry_run=False`; compare `str(exc.value)` equality between
  the two modes.
- assert no file/dir created under the target `out_dir` in either mode.

### U7b — A7: validation parity (missing file / malformed JSON)
`instance_path = tmp_path/"nope.json"` → both modes raise `FileNotFoundError`
(same type; message contains the path). Malformed JSON file → both raise
`json.JSONDecodeError` (subclass of `ValueError`; assert type equality between
modes, not just `ValueError`).

### U8 — A8: static method check
- `Config(method="nope")` → `pytest.raises(ValueError, match="không có trong registry")`
  and the message lists valid methods (`sorted(METHODS)`).
- `Config(method="tests.runner.nonexistent_module:solve")` → dry-run succeeds
  (`":" in method` passes); assert no import attempted via the `sys.modules`
  snapshot in U8b.
- nothing written in either case.

### U8b — A8: no new modules imported during dry-run
`before = set(sys.modules)` immediately before the call; dry-run; `after =
set(sys.modules)`; assert `after - before == set()`. Note in the test docstring:
`import src.runner.runner` already loads `src.sat` + pysat, so the assertion is
about **new** entries only; a "module absent" check on a nonexistent module is
vacuous. This test cannot run on an interpreter without pysat — the venv
interpreter is mandatory (same reason as A11).

### U9 — edge cases from requirements §Edge cases (unit level)
Add focused assertions (may be folded into U1–U8 where natural):
- duplicate edges `(u,v)`/`(v,u)` → `m` counts unique edges; `run_id` unaffected;
- `memory_limit` set (e.g. `2048`) → reported verbatim in the record and in
  `dry_run` does not imply enforcement (CLI literal checked in C1);
- non-ASCII `instance.id` → no crash at API level; `run_id` carries the id as
  given.

---

## 3. CLI subprocess tests — `python -m src.runner --dry-run`

Harness choice: one subprocess per case via
`subprocess.run([sys.executable, "-m", "src.runner", ...], capture_output=True,
text=True)`, because A10 needs a real stderr codec. For A9 either harness is
allowed; use subprocess for consistency with A10. Always pass
`--instance <tmp_path fixture>` and `--out <tmp_path/"raw">`.

Expected 5 lines for `path4`, `--method oracle`, defaults except
`--time-limit 1800` (float), `--out <tmp>`:

```
DRY_RUN run_id=<computed via make_run_id>
DRY_RUN instance=path4 n=4 m=3
DRY_RUN config method=oracle abp_encoding=none amo_encoding=none sat_solver=none search_mode=none symmetry=false warm_start=false seed=0
DRY_RUN budget time_limit=1800.0 hard_limit=<1800.0 + KILL_GRACE_SECONDS> memory_limit=none memory_limit_enforced=false
DRY_RUN output out_file=<str(Path(out)/"<run_id>.json")> exists=false resume_would_skip=false
```

Rendering rules under test: `None` → `none`; bool → lowercase `true`/`false`;
values via `str()`; `out_file` via `str(Path(...))` with platform separators
(Windows backslashes); no extra/blank lines; stderr empty.

### C1 — A9: CLI success, exact 5-line block
Run the command; assert:
- return code `0`;
- `err == ""` (empty stderr, no warnings);
- `out.splitlines()` has length exactly 5, no blank lines;
- lines 1–4 compare exact strings built from `make_run_id(...)` and the module
  constant `KILL_GRACE_SECONDS`;
- line 5 split into prefix `"DRY_RUN output out_file="`, middle `Path(...)`,
  and tail `" exists=false resume_would_skip=false"` — compare the middle via
  `Path(...)` equality (not string equality) to survive separator differences;
- nothing exists under `--out` after the run (`out_dir.exists() is False`).

### C1b — A9/B2: bool and `None` rendering
1. `--memory-limit 2048` → config line `memory_limit=2048.0` (argparse float)
   and budget line `memory_limit=2048.0 memory_limit_enforced=false`.
2. `--resume` with a pre-created `<run_id>.json` → last line
   `exists=true resume_would_skip=true` (lowercase literals).
3. `--dry-run` without `--time-limit` → default `1800.0`, `hard_limit=1830.0`
   only if the constant is 30.0 — instead assert `hard_limit ==
   str(1800.0 + KILL_GRACE_SECONDS)` computed in the test, so the constant may
   change without breaking the test.

### C2 — A9: no file written, no directory created (CLI)
After C1: `assert not Path(out_arg).exists()`. Also assert no new files appear
under the test's `tmp_path` except the fixture instance file. Do not assert
absence of `results/raw` changes globally — tests must never target it; assert
only the explicit `--out` path.

### C3 — A10: CLI failure — invalid instance
Instance with `n=4, edges=[]` (empty-graph message) or malformed JSON; run with
`--dry-run`. Assert:
- return code `2` (not 1, not 120);
- `err.startswith("DRY_RUN ERROR:")`;
- `"Traceback" not in err` and `"UnicodeEncodeError" not in err`;
- `out == ""` or contains no `DRY_RUN run_id=` line (no partial success block);
- nothing written under `--out`.

### C3b — A10: CLI failure — unknown method
`--method nope --dry-run`; assert same as C3: exit 2, stderr starts
`DRY_RUN ERROR:`, message contains `không có trong registry`, no traceback,
nothing written. (Vietnamese message exercises the codec path.)

### C4 — A10/R13: cp1252-safe stderr
Run the C3/C3b failure command with environment
`PYTHONIOENCODING=cp1252` (merge into `os.environ` copy; do not mutate the
parent process env permanently). Assert:
- return code `2`;
- stderr starts with `DRY_RUN ERROR:` (ASCII prefix survives; message may be
  lossy-replaced — that is the accepted contract, R13);
- no `UnicodeEncodeError`, no traceback, no "codec can't encode" text;
- nothing written under `--out`.
Also run one failure with `PYTHONIOENCODING=utf-8` as the baseline (message
intact) to prove the lossy path did not corrupt the normal path. Note: the
scope text's older A10 wording says "utf-8"; the revised requirements R13
requires cp1252 survival — follow R13 and record both runs.

### C5 — R11/R14: composition and unchanged real-run path
1. `--dry-run --resume` with an existing target file → exit 0,
   `resume_would_skip=true`, no argparse error (R14).
2. The same command **without** `--dry-run` still runs for real and prints the
   existing single result line; return code follows the existing rule
   (`0` non-ERR, `1` ERR). Assert the real-run output does **not** contain
   `DRY_RUN` and that a real record file is written. Use `--method oracle` and
   a clean `tmp_path` so no solver dependency is required. This is the
   byte-identical-behavior guard for R11.
3. `--dry-run` without `--instance` → argparse usage error, exit 2
   (pre-existing behavior; optional sanity check).

### C6 — CLI: `--dry-run` with dotted-path method
`--method tests.runner.nonexistent_module:solve --dry-run` → exit 0 and the
5-line block (no import attempted, R3/A8 parity at CLI level). This documents
the accepted divergence: a real run would produce an `ERR` record.

### C7 — CLI: `time_limit=None` is unreachable via CLI
Document as a review note, not a failing test: `--time-limit` is `type=float`
with default `1800.0`, so `hard_limit=none` cannot be printed by the CLI; the
`None` path is API-only (U3b). If the CLI later gains `--time-limit none`, add a
case here. Do not assert a bug where none exists.

---

## 4. Regression tests (A11)

### R1 — pre-existing tests unmodified and green
Assert `git diff -- tests/runner/test_runner.py` shows **additions only**
(new test functions appended), no edits to the six existing tests:
`test_oracle_run_saves_schema_record`, `test_resume_skips_existing`,
`test_resume_does_not_reuse_run_with_different_time_limit`,
`test_solver_exception_becomes_err`, `test_hard_timeout_becomes_to`,
`test_wrong_solution_is_caught_by_runner`. Run just this file:
`.venv\Scripts\python.exe -m pytest tests/runner/test_runner.py -q --basetemp=...`
→ no failures, no errors.

### R2 — full suite green
Run the full command from §0. Accept: no failures/errors; `3 skipped` (CPLEX CP
engine missing). Any additional skip must be explained; any new skip caused by
this change is a red flag. Do not "fix" the CPLEX skips by installing solvers.

### R3 — real-run behavior unchanged
Spot-check the existing behaviors still hold without `dry_run`:
- `run_one` default writes the record file and returns the same schema;
- `resume=True` with an existing valid record returns its content and does not
  re-run;
- a hard timeout (`KILL_GRACE_SECONDS=0.0`, `time_limit=1.0`) still yields
  `TO`;
- solver exception still yields `ERR` with the license message.
The pre-existing tests already cover these; R3 is the "did the signature change
break callers" gate — run them unmodified.

### R4 — no new imports in the runner module
Compare `sys.modules` before/after `import src.runner.runner` on a fresh
interpreter: no change caused by this task. (Import-graph facts are pre-existing;
only *new* imports are forbidden.) Mechanical diff review of the import block
plus U8b's in-call snapshot.

---

## 5. Documentation and checkbox verification (D1–D6)

Run these as a final gate after code + tests are green. Commands are read-only
(`git diff`, `grep`, `git status`); no stashing or reverting.

### D1 — ticked boxes have evidence pointers
For each of the 8 ticket files under
`docs/handoff/abp-sat-encoding/issues/W2/`
(`08-amo-pairwise-seqcounter.md`, `09-glucose-kissat-backend.md`,
`10-multi-run-k-search.md`, `11-loader-generator-full.md`,
`12-correctness-test-matrix.md`, `13-review-exact-formulation.md`,
`14-sat-methodology-draft.md`, `15-m1-gate-bonus-decision.md`):
- count boxes ticked **by this task** (diff `[ ]` → `[x]`);
- every such box has a pointer in that file's
  `## Closure evidence (2026-11-03)` section;
- the 3 pre-existing `[x]` boxes in ticket 15 need no new pointer (exempt).
Check: `git diff -- <file>` for the tick lines, plus `grep -n "Closure evidence"`
and manual read of the appended section. Fail if any tick has no pointer.

### D2 — unticked boxes have reasons
- Expected unticked set: **09 box 2 only**. It keeps `[ ]`, keeps its original
  text, and appends exactly `*(N/A — xem Closure evidence)*`; its reason entry
  cites `14-sat-methodology.md` §3.6, `src/sat/backend.py`
  (`PYSAT_KISSAT_FAMILIES`), `src/sat/solve.py` `_validate_solver`,
  `tests/sat/test_backend.py`, `tests/sat/test_solve.py`, `docs/sat_tooling.md`.
- 13 box 3 is ticked unconditionally (B5), citing GH #20/#42, PR #48,
  `docs/handoff/w2-sat/13-review-p1-formulation.md`,
  `docs/handoff/w2-exact/16-w2-acceptance.md`.
- No box deleted or reordered; no multi-line reasons inline in checkbox lines
  (exceptions only as above).
Check: `git diff -- docs/handoff/abp-sat-encoding/issues/W2/` and read each
Closure evidence section. Fail if the unticked set differs from `{09 box 2}` or a
reason is missing.

### D3 — M1 evidence doc diff scope and output format
`git diff -- docs/handoff/w2-sat/15-m1-gate-evidence.md`:
- only two changes: a new `### 4.1 ...` subsection and one appended pointer in
  the §6 bullet "Việc còn mở của gate" (bullet text kept);
- §1–§3, §4 original text, §5 and the §6 decision/NO-GO/cut-list text
  byte-identical (check with `git diff --word-diff=porcelain` or a
  "removed lines" grep — there must be none in those ranges);
- §4.1 contains the **verbatim** command actually executed, with the real
  interpreter (`.venv\Scripts\python.exe`), `--out results/raw`, a real
  instance file, branch name and `git describe --tags --always --dirty` output;
- §4.1's pasted stdout parses against R12: exactly 5 `DRY_RUN` lines, lowercase
  bools, `none` for `None`, and self-consistent values — `run_id` suffix
  `...__tl1800.0__mlNone` (never `mlna`), `hard_limit == time_limit +
  KILL_GRACE_SECONDS`, `memory_limit_enforced=false`, `n`/`m` matching the
  instance;
- §4.1 states the scope: only the `--dry-run` blocker closes; M1 stays NO-GO.
Fail if the block was hand-written (invented) or if §4/§6 were "fixed" to agree
with §4.1 — the dated record stays as-is.

### D4 — ticket 15 box 2
`git diff -- docs/handoff/abp-sat-encoding/issues/W2/15-m1-gate-bonus-decision.md`:
box 2 is `[x]`; its stale parenthetical is replaced by a pointer to §4.1 (real
output) **and** §3 (compute estimate); boxes 1, 3, 4 remain `[x]`; the NO-GO
decision lines at the bottom are byte-identical. Fail on any edited decision
line or a missing §3 pointer.

### D5 — metadata lines and language
Across all touched ticket files: `Status:`, `Owner:`, `Blocked by:` lines
unchanged (`git diff` shows no change on those lines); new prose in Vietnamese,
technical identifiers verbatim; fixed strings exempt (heading
`## Closure evidence (2026-11-03)`, suffix `*(N/A — xem Closure evidence)*`).

### D6 — no out-of-scope changes caused by the task
`git status --porcelain` compared to the pre-task baseline. Allowed changed
paths caused by this task:
- `src/runner/runner.py`, `src/runner/__main__.py`,
  `tests/runner/test_runner.py`;
- the 8 W2 ticket files listed in D1;
- `docs/handoff/w2-sat/15-m1-gate-evidence.md`;
- `docs/handoff/w2-dry-run/` artifacts (`requirements.md`, `scope.md`,
  `review-qa.md`, `review-be.md`, this `test-plan.md`).
Not counted as violations: pre-existing dirty `docs/handoff/sat-g1/*` (11 files)
and pre-existing untracked `.pytest-tmp/`, `docs/handoff/w2-dry-run/`. The pytest
`--basetemp` is outside the repo, so it creates no repo artifact. Fail if any
other path is modified/created by the task; never stash or revert unrelated work
to make the check pass.

---

## 6. Test hygiene and prohibitions (read before writing any test)

- Do **not** edit the six existing tests or the `path4` fixture (A11).
- Do **not** copy R12's example `run_id`/budget values as expected values —
  compute them with `make_run_id` and the module constant.
- Do **not** target the repo's default `results/raw` from tests; always pass an
  explicit `out_dir`/`--out` under `tmp_path`.
- Do **not** assert `hard_limit` against a literal `30.0`; read
  `runner_mod.KILL_GRACE_SECONDS` so a future constant change does not create a
  false failure (and does not mask a hardcoded copy — that is caught by diff
  review).
- Do **not** call `registry.resolve()` in a test that asserts "no import":
  calling it imports the solver module and would break A8's contract. Validate
  static membership only.
- Do **not** run the suite with global `python` or without `--basetemp` on
  Windows: both produce environmental failures unrelated to the change
  (`pysat` missing; `PermissionError: [WinError 5]`).
- Do **not** "fix" the 3 CPLEX skips or the pre-existing `--help` cp1252 issue
  (out of scope, unchanged by this task).
- Test names should be self-describing, e.g.
  `test_dry_run_record_shape`, `test_dry_run_writes_nothing`,
  `test_dry_run_hard_limit_follows_grace_constant`,
  `test_dry_run_run_id_matches_real_run`,
  `test_dry_run_resume_reports_without_parsing_garbage`,
  `test_dry_run_spawns_no_worker`, `test_dry_run_validation_matches_real_run`,
  `test_dry_run_method_check_imports_nothing`,
  `test_cli_dry_run_prints_five_lines`,
  `test_cli_dry_run_failure_exits_2_cp1252_safe`,
  `test_cli_without_dry_run_unchanged`.
  New tests are appended after the existing ones; grouping with a comment header
  (`# --- dry-run: A1–A8 ---`, `# --- dry-run CLI: A9–A10 ---`) is allowed.

---

## 7. Discrepancy note (record, do not silently resolve)

The Phase-2 brief phrase "`dry_run` return value must be a string representation
of a `DryRunRecord`, not a dataclass instance (R10)" does not match the
authoritative sources: `requirements.md` R8/Data model say
`run_one(..., dry_run=True)` returns a **plain `dict`** record (`build_record`
output) with a `dry_run` sub-`dict`, and `dry_run["out_file"]` is a `str`
(`scope.md` I4). This plan follows R8: U1/U1b/U1c assert the dict shape and the
string `out_file`. If the brief is meant to supersede R8, add one serialization
assertion (e.g. `json.dumps(rec)` succeeds and round-trips) and update R8/Data
model — but do not change `build_record` or add a dataclass without that
decision. Record the chosen resolution in the PR description.

Also note the A10 codec wording conflict: `scope.md` says
`PYTHONIOENCODING=utf-8`, while revised `requirements.md` R13 requires the
stderr path to survive cp1252 (lossy-safe). C4 follows R13 and runs both; this
is the superseding text per the revision note at the top of `requirements.md`.

---

## 8. Definition of done for this plan

- [ ] U1–U9 implemented and green; A1–A8 each mapped to at least one test.
- [ ] C1–C7 implemented and green; A9–A10 mapped; C5 proves the non-dry-run path
      is unchanged.
- [ ] R1–R4 green: pre-existing tests untouched; full suite via venv +
      `--basetemp` reports no failures and exactly 3 CPLEX skips.
- [ ] D1–D6 checks executed and recorded; no failing doc gate.
- [ ] Discrepancy note (§7) resolved or explicitly carried into the PR.
