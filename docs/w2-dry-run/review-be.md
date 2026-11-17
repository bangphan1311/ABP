# Backend review — W2 `--dry-run` (pre-Gate 1)

**Reviewer:** Backend Developer subagent
**Inputs read:** `docs/handoff/w2-dry-run/requirements.md`, `docs/handoff/w2-dry-run/scope.md`,
`src/runner/__main__.py`, `src/runner/runner.py`, `src/runner/schema.py`,
`src/runner/registry.py`; plus `src/common/models.py`, `src/sat/loader.py`,
`src/sat/__init__.py`, `src/sat/backend.py`, `src/sat/pairwise.py`,
`tests/runner/test_runner.py`, `docs/handoff/w2-sat/15-m1-gate-evidence.md`,
`docs/handoff/abp-sat-encoding/issues/W2/15-m1-gate-bonus-decision.md`.
**Written:** this file only. No code, no upstream doc was modified.

## Verdict

**Conditional pass.** The code plan is small and well-bounded: one keyword-only
parameter, one early-return branch in `run_one`, one flag + one print branch in
`main()`. Nothing needs a new module or abstraction.

But the requirements are **not shippable as written**. Six contradictions must be
fixed in the docs before Gate 1, and two implementation traps will silently break
acceptance criteria if missed. The most damaging one: **the example `run_id`s in
R4/R12 cannot be produced by the existing `make_run_id`** — an implementer who
copies them into A9's exact-string assertions, or "fixes" `make_run_id` to match,
breaks every existing file in `results/raw/` and every resume path.

## Verified facts (no action needed)

These were checked against the repo so the next agent does not re-litigate them:

- `read_instance` does dedup by `frozenset((u, v))` and rejects self-loops and
  empty graphs; empty-graph message is exactly
  `"Instance is empty (n = 0 or no edges)."` (`src/sat/loader.py:83-91`). R2's OK
  example and R6's "m after dedup" are factually correct.
- Checkbox counts match R17's mapping exactly: 08=4 open, 09=4, 10=6, 11=4,
  12=5, 13=3, 14=3, 15=3 done + 1 open. Ticket 15 box 2 text is the stale
  parenthetical R17 describes (`.../W2/15-m1-gate-bonus-decision.md:10-13`).
- All evidence pointers in R17 exist: `tests/sat/test_matrix.py:168`
  (`test_amo_exhaustive_closure_over_all_subsets`),
  `src/sat/pairwise.py:28` (`SUPPORTED_AMO_ENCODINGS`),
  `src/sat/backend.py:23` (`INTERRUPTIBLE_FAMILIES`), plus the four
  `docs/handoff/w2-sat/12..15*.md` files and `16-w2-acceptance.md`.
- `build_record(instance, config, None, wall_time=..., status_override="DRY_RUN")`
  already produces exactly the shape R8 wants: all `RUN_FIELDS`, `error=None`,
  result-derived fields `None`, `solution=None`, `metadata={}`,
  `solver=config.sat_solver or config.method`, `config=asdict(config)`
  (`src/runner/schema.py:63-107`). No second record builder is needed.
- `make_run_id` is deterministic and host/timestamp-free
  (`src/runner/schema.py:25-32`); `git_tag()` swallows every exception and
  returns `"unknown"` (`schema.py:35-44`), so a non-git checkout still works.
- Importing `src.runner.registry` is cheap: it imports only `importlib` and
  `models`, no solver (`src/runner/registry.py:9-14`). Reading `METHODS` from
  `runner.py` is safe.
- No dry-run code exists yet (`grep -i "dry"` over `src/`, `tests/` → 0 hits);
  this is greenfield, no partial implementation to reconcile.
- `tests/runner` is green when given a writable basetemp: **6 passed in 3.47s**
  (`.venv\Scripts\python.exe -m pytest tests/runner -q --basetemp=<fresh>`).
  The default run fails first on a Windows temp-dir permission error (see I10).

## Blocking doc contradictions (fix before Gate 1)

### B1 — R4/R12's example `run_id` is wrong: `mlna` → `mlNone`, `tl30.0` → `tl30`

`make_run_id` builds `f"tl{config.time_limit}"` and `f"ml{config.memory_limit}"`
*as pre-rendered strings*; the `"na" if p is None` substitution only fires when
the whole part is `None` (`src/runner/schema.py:26-32`). So `None` renders as
`None`, not `na`, for the `tl`/`ml` components. Measured with the repo's venv:

```
Config(method="oracle", time_limit=30)   -> path4__oracle__na__na__na__na__sym0__ws0__s0__tl30__mlNone
Config(method="oracle", time_limit=30.0) -> path4__oracle__na__na__na__na__sym0__ws0__s0__tl30.0__mlNone
Config(method="oracle", time_limit=1800.0)-> path4__oracle__na__na__na__na__sym0__ws0__s0__tl1800.0__mlNone
```

`results/raw/*.json` corroborates it: existing files are named `...__tl60.0__mlNone.json`.
Requirements claim `...tl30.0__mlna` (R4, line 96) and `...tl1800.0__mlna`
(R12, lines 192/196). Both are wrong. `Config.time_limit` is typed
`float | None` with no coercion (`src/common/models.py:33`), so the integer
literal `30` stays an int and renders `tl30`; the existing test at
`tests/runner/test_runner.py:21` passes exactly that int.

Impact: A9's "assert exact strings" and D3's "output parses against R12" fail
against real output if the doc example is used as the expected value. Fix the
two examples. **Do not change `make_run_id`** — that would rename every existing
`results/raw` file and make `--resume` re-run everything (S4).

### B2 — R12's rendering rule contradicts R12's own example for booleans

Rule: "every value via `str(value)`, except `None` → `none`" (lines 184-185).
Example line 3: `symmetry=False warm_start=False` (Python `str`, capitalised).
Example lines 4-5: `memory_limit_enforced=false`, `exists=false`,
`resume_would_skip=false` (lowercase literals). Pick one rule and make the
example match it. Recommended: "`None` → `none`; `bool` → `true`/`false`; all
else `str(value)`" and change line 3's example to `symmetry=false
warm_start=false`. As written, A9 cannot satisfy both the rule and the example.

### B3 — R12's example path is relative; the CLI default is absolute

R12's example shows `out_file=results\raw\...`, but `--out` defaults to
`str(DEFAULT_OUT_DIR)` where `DEFAULT_OUT_DIR = REPO_ROOT / "results" / "raw"`
and `REPO_ROOT` is `Path(...).resolve()` → **absolute**
(`src/runner/runner.py:27-28`, `src/runner/__main__.py:22`). So the default
dry-run prints `C:\Users\<user>\...\results\raw\<run_id>.json`, leaking the
machine layout and username into a committed evidence doc.

Fix in the doc, not the code: state that the §4.1 command must pass
`--out results/raw` (relative) to reproduce the example, and that A9's CLI test
should pass `--out <tmp_path>` so it never asserts a repo-absolute path. R11's
"without `--dry-run`, byte-identical" means the real-run default stays absolute —
do not change it.

### B4 — R15/R16 forbid checkbox-line edits; R17/D4 require one

R15: "The checkbox line text itself is not edited beyond the bracket"
(line 224). R16: "No box is deleted, reordered, or **reworded**" (line 230).
R17/D4: "The stale parenthetical on box 2 ... **is replaced** by a short pointer"
(lines 283-288; scope D4 lines 115-116). Ticket 15 box 2's parenthetical spans
lines 10-13 of the ticket file, so the replacement is a deletion + rewrite.

Same class of problem: R16 wants an "inline reason annotation" while R15 forbids
editing the line; R17's ticket-12 note says "tick with the N/A note" on box 1.

Resolution: add one carve-out sentence to R15/R16 — "original text is preserved;
annotations are appended after it; the sole exception is ticket 15 box 2's stale
parenthetical, replaced per R17/D4." Otherwise the docs half is unshippable
against its own rules.

### B5 — Ticket 13 box 3: requirements still conditional, scope resolved

Requirements R17 (lines 270-277) ticks box 3 **only if** the GH #20 posting is
verifiable at execution time, else leaves it open with an annotation; D2
(line 466) still lists "13 box 3 iff GH #20 posting unconfirmed"; Open questions
#1 (lines 508-511) still asks. Scope P1 item 6 (lines 59-63) and scope D2
(line 111) say **tick**, already verified 2026-11-03 via GH #20/#42 and PR #48.

Two acceptance criteria cannot both be satisfied. Resolution: amend requirements
to scope's resolved state (tick; cite GH #20/#42/PR #48; date 2026-11-03) and
delete the conditional text from D2 and Open questions #1. The scope version is
the better-founded one — it names the artifacts.

### B6 — D6's allowed-file list cannot pass in this working tree

D6 (requirements line 475; scope lines 119-122) allows only the listed files.
Reality: `git status` already shows 11 pre-existing modified files under
`docs/handoff/sat-g1/` plus an untracked `docs/handoff/w2-dry-run/` directory.
The directory itself contains `requirements.md`, `scope.md`, and this review —
only "file scope này" is listed. So D6 fails on day one for reasons unrelated to
the task.

Resolution: restate D6 as "no changes **caused by this task** beyond this list"
and include the whole `docs/handoff/w2-dry-run/` directory. Do not stash or revert
someone else's `sat-g1` work to make a status check pass (S7).

## Implementation risks (code)

### I1 — R7's "does NOT import ... any solver module" is unachievable in scope

`src/runner/runner.py:25` imports `src.sat.loader`, which executes
`src/sat/__init__.py:3` → `src.sat.solve` → `order` → `pairwise` → `backend`,
which imports `pysat` at module level (`src/sat/backend.py:14`). So merely
importing `src.runner.runner` already pulls the solver stack. Verified: system
Python fails with `ModuleNotFoundError: No module named 'pysat'` at that import.

This is pre-existing and `src/sat/**` is explicitly out of scope, so the literal
R7 bullet cannot be satisfied. Resolution: reword R7 to "imports no *new* solver
module beyond what importing `src.runner.runner` already loads, and executes no
solver code." The meaningful guarantee — no worker spawn, no solver call — still
holds and is what A6 tests. Also add a note to §4.1 that "no solver executes" is
the claim, not "no solver is imported".

### I2 — `run_one` mkdirs before it computes `out_file`

Current order: `read_instance` → `Path(out_dir)` → `mkdir` → `make_run_id` →
`out_file` → resume check (`src/runner/runner.py:41-48`). A dry-run must compute
`out_file` **without** creating the dir. Minimal restructure:

```
instance = read_instance(instance_path)
run_id = make_run_id(instance, config)
out_dir = Path(out_dir)
out_file = out_dir / f"{run_id}.json"
if dry_run: return _dry_run_record(...)   # no mkdir, no tempdir, no writes
out_dir.mkdir(parents=True, exist_ok=True)
if resume and out_file.exists(): ...
```

Keep `read_instance` first so R2's "same exception at the same point" holds. For
real runs this is behaviourally identical except error ordering when `out_dir`
is pathological; output bytes are unchanged. Do **not** enter the
`with tempfile.TemporaryDirectory()` block in the dry-run branch
(`runner.py:50`) — R7's literal "does NOT create any directory" covers it.

### I3 — The CLI try/except must be guarded by `--dry-run`, or R11 breaks

`main()` currently calls `run_one(...)` with no exception handling and returns
`0`/`1` (`src/runner/__main__.py:31-35`). R13 wants validation failures to become
`DRY_RUN ERROR:` + exit 2 — but R11 requires the *non*-dry-run path to stay
byte-identical. A shared `try/except` around the single call would change real-run
failure behaviour (today: traceback + interpreter exit) into exit 2. Trap.

Correct shape: branch on `a.dry_run` first; wrap only the dry-run call in
`except (ValueError, OSError)`; return 2. Leave the real-run call and its print
untouched. That catch covers `JSONDecodeError`, `UnicodeDecodeError`,
`PermissionError`, `FileNotFoundError`, `IsADirectoryError` — all subclass one of
the two. Note `print(..., file=sys.stderr)` needs `import sys` in `__main__.py`
(not currently imported).

### I4 — `DryRunInfo` must be a plain dict, not a dataclass

Requirements call it an "Entity" (lines 330-343) but every acceptance criterion
subscripts it: `record["dry_run"]["hard_limit"]` (A3, lines 431-433). A dataclass
fails A3. Lock it as `dict[str, Any]`, and keep `out_file` as `str` (datamodel
says `str`) so a US2 batch caller can `json.dumps(record)` without a `Path`
`TypeError`. Since dry-run records are never written to disk, serialisability is
not strictly required — but US2 collects records, so str is the safe default.

### I5 — `wall_time` must exclude `build_record`'s `git describe`

`build_record` calls `git_tag()`, which spawns `git describe` with
`timeout=10` (`schema.py:35-44`). Measure `wall_time` from function entry to just
before `build_record` and pass that value. If measured after, R9's "`wall_time <
5.0`" can fail on a slow/network FS. Note R9's criterion is **not mapped to any
A-item** — A1 checks keys only. Either add an assertion (A12) or drop the
criterion; leaving it as prose-only means "wall_time is bounded" is never tested.

### I6 — A9 under-specifies stdout/stderr assertions

R12 requires "no extra lines, no blank lines, nothing on stderr", but A9 only
says "prints exactly the 5 DRY_RUN lines". Add `assert err == ""` and compare
`out.splitlines() == [five strings]` (avoids trailing-newline brittleness).
Import-time warnings from pysat are a low risk for the stderr assertion; if they
appear, filter them in the test rather than relaxing R12.

### I7 — A6's `subprocess.run` recorder must tolerate kwargs

The allowed `git describe` call passes `capture_output=True, text=True,
timeout=10, cwd=...` (`schema.py:37-41`). A naive spy that only records positional
args crashes before the worker-pattern assertion runs. Record `args` and `kwargs`,
then assert no `args` starts with `[sys.executable, "-m", "src.runner.worker"]`.
The git call's `args[0]` is `"git"`, so the whitelist is satisfied.

### I8 — A8's "module absent from `sys.modules`" is vacuous

Because importing `src.runner.runner` already loaded `src.sat.solve` and friends
(I1), "absent after the call" is trivially true for
`tests.runner.nonexistent_module`. It proves nothing about import discipline.
Replace/augment with: snapshot `set(sys.modules)` immediately before the dry-run
call and assert no *new* module appears during it. That is satisfiable and
meaningful. Also note the test cannot run at all on an interpreter without
`pysat` installed.

### I9 — Environment: system Python lacks `pysat`; `.venv` has it

`python -m src.runner --dry-run` fails at import on the system interpreter
(`ModuleNotFoundError: No module named 'pysat'`); `.venv` has
`python-sat==1.9.dev15` (`requirements.txt:5`). US1's command and §4.1's verbatim
output must name the interpreter used (e.g.
`.venv\Scripts\python.exe -m src.runner ...`, or "activate `.venv` first"), or the
evidence is not reproducible. A9's subprocess variant needs the venv Python too.

### I10 — A11's "`pytest tests -q` green" is not reproducible as written here

Default pytest temp root is locked: `PermissionError: [WinError 5] Access is
denied: '...\Temp\pytest-of-ducqu'` → 6 errors. With
`--basetemp=<fresh dir>` → 6 passed. Fix: record the exact command with a fresh
basetemp in the handoff and in A11's criterion. Do not edit tests to work around
an OS permission problem.

### I11 — Nothing enforces C1's "never aggregated into runs.csv"

`build_record` happily stamps `status="DRY_RUN"`; a caller (US2's batch planner)
can append that record to `runs.csv` and nothing stops it. C1's claim is a
convention, not an invariant. Cheap mitigation: one docstring line in `run_one`
("dry-run records must not be persisted"). No new code.

## Minor / edge cases to document (not Gate 1 blockers)

- `hard_limit=none` is unreachable from the CLI: `--time-limit` is `type=float,
  default=1800.0` with no "none" spelling (`__main__.py:20`). The "none"
  rendering path exists only via the API. Requirements' edge case (lines 394-396)
  says "in CLI output" — correct it to "API only", or accept that it is untested
  end-to-end.
- `out_dir` existing as a *file*: a real run raises at `mkdir`; a dry-run's
  `out_file.exists()` returns `False` and prints a happy report. Same class as
  the corrupt-file divergence already documented; add it to the edge cases list
  rather than adding new validation (R10 forbids that).
- Malformed dotted paths (`":"`, `"a:"`, `"a:b:c"`) pass the static check and fail
  only in the worker. The edge cases list covers "nonexistent module" but not
  malformed specs; one sentence is enough.
- `run_id` is type-sensitive: `time_limit=30` vs `30.0` produce different IDs for
  "the same" config (B1). Document that API callers should pass floats, or that
  duplicate detection in US2 is only exact-match.
- §4 and §6 will read self-contradictory next to §4.1: §4 says "0 hit" and "CHƯA
  thực hiện được" (line 198); §6's open-item bullet says "vẫn chưa tick"
  (lines 271-273) and its decision reason says "blocker mục 4 chưa mở"
  (lines 259-260). R19 keeps all of that byte-identical and only appends the §6
  pointer. That is intentional (dated record), but flag it so the implementer does
  not "helpfully" edit the reasons and violate D3.
- §4.1's evidence is produced pre-merge; a review edit to the output format would
  invalidate the committed verbatim block. Produce §4.1 last, after code
  sign-off, or re-run before merge.
- §4.1 needs branch + `git_tag`, but `git_tag` is not in the 5-line output —
  record them as separate facts (`git branch --show-current`,
  `git describe --tags --always --dirty`).
- A4's "real run afterwards" must write into `tmp_path`, never `results/raw`, or
  D6's file list breaks.

## Simplifications (keep the diff small)

1. **Don't touch `make_run_id`.** The examples are wrong, not the code. Changing
   it renames every `results/raw` file and breaks resume/idempotency (B1).
2. **Don't add a helper module or a second record builder.** Branch inline in
   `run_one` after computing `out_file`; call the existing `build_record`
   exactly as R8 specifies. ~15 lines total.
3. **Don't add a `DryRunInfo` dataclass.** Plain dict; satisfies A3's subscripting
   and avoids serialisation surprises (I4).
4. **Don't duplicate `registry.resolve`'s full sentence.** R3's criterion only
   requires the substring `"không có trong registry"` plus the sorted list (A8
   checks the substring). Import `METHODS` from `registry` and raise a short
   message with a comment pointing at `registry.resolve`. Registry's own message
   (`registry.py:37-40`) stays untouched; no drift risk if you don't mirror it.
5. **Don't restructure the real-run path.** Keep the existing print/return lines
   byte-identical; add one `if a.dry_run:` branch above them (I3).
6. **Reuse `build_record`'s `run_id`.** Compute it once for `out_file`; let
   `build_record` recompute the same deterministic value. No new parameter, no
   assertion needed.
7. **Don't "fix" D6 by stashing unrelated `sat-g1` edits.** Restate the criterion
   instead (B6).

## Acceptance-criteria amendments (concrete)

- **A3:** `record["dry_run"]` is a dict; `out_file` is a `str`.
- **A4 / A9:** expected `run_id` must be computed via `make_run_id(...)` — never
  copied from R4's or R12's example. A9 must pass `--out <tmp_path>` and compare
  via `Path`.
- **A9:** add `err == ""` and `splitlines()` comparison (I6).
- **A11:** run with a writable `--basetemp`; record the command (I10).
- **A8:** add "no new `sys.modules` entries during the call"; note the `pysat`
  import already happened at module import (I1/I8).
- **R9:** either add an assertion for `wall_time < 5.0` (A12) or drop the
  criterion; measure before `build_record` (I5).
- **R7:** reword to "no new solver module imports; no solver execution" (I1).
- **R12:** fix the rendering rule for bools (B2), fix the `out_file` example to
  be conditional on `--out results/raw` (B3), and correct `mlna` → `mlNone` /
  `tl30.0` → `tl30` in R4 and R12 (B1).
- **R15/R16:** add the ticket-15-box-2 carve-out and clarify that annotations are
  appended after the original text (B4).
- **R17/D2/Open questions #1:** adopt scope's resolved ticket-13 state; delete the
  conditional (B5).
- **D6:** "no changes caused by this task" + include `docs/handoff/w2-dry-run/`
  (B6).

## Contradictions register (suggested additions to requirements §Contradictions)

The requirements list C1–C5 but miss two more that will bite during review:

- **C6 — run_id rendering vs examples.** `make_run_id` renders `tlNone`/`mlNone`
  for `None` time/memory limits, and `tl30` for an int time limit; R4/R12's
  examples show `tl30.0`/`mlna`. Resolution: examples are wrong; code stays.
- **C7 — checkbox-text immutability vs ticket 15's parenthetical.** R15/R16
  forbid rewording; R17/D4 require replacing. Resolution: explicit carve-out.

## Bottom line for Gate 1

The implementation is a small, low-risk diff in two files plus tests. The docs
plan (R15–R20) is well-founded — checkbox counts and evidence pointers all check
out — but six criteria are mutually inconsistent or factually wrong against the
code. Fix B1–B6 in the docs, and add I2/I3 to the implementation notes so the two
traps are not missed. After that, Gate 1 can pass.
