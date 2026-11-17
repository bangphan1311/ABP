# Requirements — W2 gap closure: runner `--dry-run`, W2 checkbox completion, M1 evidence update

Source task: finish the remaining W2 gap = (1) `--dry-run` flag in `src/runner`,
(2) complete W2 issue checkboxes `08..15`, (3) record real `--dry-run` output in
`docs/handoff/w2-sat/15-m1-gate-evidence.md` while keeping the M1 NO-GO decision
intact. Contract baseline: `CONTRACT.md` (repo root). Upstream evidence read:
`docs/handoff/w2-sat/12-test-matrix.md`, `13-review-p1-formulation.md`,
`14-sat-methodology.md`, `15-m1-gate-evidence.md`,
`docs/handoff/abp-sat-encoding/w3-review-notes.md`,
`docs/handoff/w2-exact/16-w2-acceptance.md`.

Revised 2026-11-03: findings from `review-qa.md` and `review-be.md` (same
directory) folded in — 6 blocking contradictions resolved (run_id examples,
bool rendering, checkbox-edit carve-outs, ticket 13 box 3, D6 paths,
no-new-imports wording + Windows CLI environment).

## Scope

In scope:

- `src/runner/runner.py`: `run_one(..., dry_run=...)`.
- `src/runner/__main__.py`: `python -m src.runner --dry-run`.
- `tests/runner/test_runner.py`: new tests for the above.
- `docs/handoff/abp-sat-encoding/issues/W2/08..15*.md`: checkbox completion with
  evidence pointers.
- `docs/handoff/w2-sat/15-m1-gate-evidence.md`: dated §4.1 update + §6 pointer.

Out of scope (must not be touched by this task):

- `CONTRACT.md` — no status vocabulary change (see Contradictions C1).
- `src/runner/worker.py`, `src/sat/**`, `src/exact/**`, `src/common/**`.
- Any memory-limit enforcement (W2 acceptance already records that
  `memory_limit` is not a hard cap; changing that is a separate decision).
- GitHub issue state sync (labels, GH checkboxes) — repo markdown only.
- CNF-size or runtime *estimation* in dry-run. Excluded deliberately: P2's
  compute estimate already exists in `15-m1-gate-evidence.md` §3 from matrix
  data; dry-run contributes measured facts (n, m, budgets, run_id, resume
  state), not new estimates.
- Re-deciding M1 GO/NO-GO.

## User stories

- **US1 — P2 closes ticket 15.** As P2, I run
  `python -m src.runner --instance ... --method sat ... --dry-run` and see,
  without any solver executing and without any file being written, the exact
  `run_id` the command maps to, the instance size (`n`, `m`), the effective
  budget (`time_limit`, hard-kill time, `memory_limit` and the fact that it is
  not enforced), and whether `--resume` would skip. I paste that output into
  the M1 evidence doc and tick ticket 15 item 2.
- **US2 — dev plans a batch.** As a dev, I call
  `run_one(path, cfg, out, dry_run=True)` from Python for each planned run to
  enumerate `run_id` / output path / already-exists state and detect duplicate
  `run_id`s before spending up to 1800 s per real run.
- **US3 — W2 closer.** As whoever closes W2 tickets, I tick a checkbox only
  when repo-verifiable evidence exists, annotate unticked boxes with a reason,
  and leave the recorded M1 decision text untouched.

## Business rules

### A. `run_one(..., dry_run=...)` — API

- **R1.** `run_one` gains a keyword-only parameter `dry_run: bool = False`,
  appended after `resume`. Default `False`; every existing caller and all
  existing behaviors are unchanged.
  — Criterion: signature is
  `run_one(instance_path, config, out_dir=DEFAULT_OUT_DIR, *, resume=False, dry_run=False)`.
  — OK: `run_one(p, cfg, out, dry_run=True)` returns a record, writes nothing.
  — BAD: `dry_run` as positional third arg, or default `True`.

- **R2.** Dry-run validates the instance file exactly like a real run:
  `read_instance(instance_path)` is called and its exceptions propagate
  unchanged (`ValueError` for schema/edge/empty-graph violations,
  `OSError`/`json.JSONDecodeError` for unreadable files). No new wrapping, no
  new error type.
  — Criterion: for every invalid instance, `run_one(..., dry_run=True)` and
  `run_one(..., dry_run=False)` raise the same exception type with the same
  message at the same point.
  — OK: empty graph → `ValueError("Instance is empty (n = 0 or no edges).")`
  in both modes.
  — BAD: dry-run returning an `ERR` record for an invalid instance (real run
  raises before any record exists; dry-run must match that).

- **R3.** Dry-run validates the config *statically, without importing the
  config's solver module*: the check is exactly
  `config.method in registry.METHODS or ":" in config.method` — no call to
  `registry.resolve()` — else `ValueError` whose message contains
  `không có trong registry` and the sorted valid method list (same wording as
  `registry.resolve`). Import-graph fact: importing `src.runner.runner`
  already loads the `src.sat` package (and pysat) via
  `from src.sat.loader import read_instance` → `src/sat/__init__.py` —
  pre-existing, out of scope. R3/R7 forbid only NEW imports and solver
  execution; never claim "pysat is unimported".
  — Criterion: unknown method → `ValueError`; dotted path
  `tests.runner.nonexistent_module:solve` passes validation; snapshot
  `set(sys.modules)` immediately before the dry-run call — no NEW module
  appears during the call.
  — OK: `Config(method="sat")` passes; `Config(method="tests.runner.slow_solver:solve_boom")`
  passes.
  — BAD: calling `registry.resolve()` inside dry-run (that imports the module —
  heavy deps and license errors would surface in a "no execution" check).

- **R4.** Dry-run computes the deterministic `run_id` with the existing
  `make_run_id(instance, config)`; it must not add host, timestamp, or path
  components. `make_run_id` stays untouched: it renders `tl{time_limit}` /
  `ml{memory_limit}` as raw strings — `None` → `tlNone`/`mlNone`, int `30` →
  `tl30`; the `na` substitution fires only for whole-`None` parts. Changing it
  would rename every existing `results/raw/*.json` and break `--resume`.
  — Criterion: two dry-runs of the same (`instance.id`, config) on the same
  or different machines produce the same `run_id` (`make_run_id` uses
  `instance.id`, not edge content).
  — OK: `path4` + `Config(method="oracle", time_limit=30)` →
  `path4__oracle__na__na__na__na__sym0__ws0__s0__tl30__mlNone` every time;
  `time_limit=1800.0` → `...__tl1800.0__mlNone` (matches existing
  `results/raw` filenames like `...__tl60.0__mlNone.json`).
  — BAD: appending a date/time suffix "to avoid collisions"; "fixing"
  `make_run_id` to match the old examples.

- **R5.** Dry-run reports resume state: `out_file = Path(out_dir) / f"{run_id}.json"`;
  `exists = out_file.exists()`; `resume_would_skip = resume and exists`.
  Dry-run does NOT create `out_dir` and does NOT read or parse the existing
  file's content.
  — Criterion: after `run_one(..., dry_run=True)` with a previously nonexistent
  `out_dir`, `out_dir` still does not exist; a corrupt/garbage file at
  `out_file` does not fail the dry-run and its content is not returned.
  — OK: garbage bytes at `out_file`, `resume=True` → record returned with
  `status == "DRY_RUN"`, not the garbage.
  — BAD: dry-run parsing the existing JSON (a corrupt old record must not
  break a read-only check).

- **R6.** Dry-run reports the budget with the exact runner formula:
  `hard_limit = None if config.time_limit is None else config.time_limit + KILL_GRACE_SECONDS`,
  referencing `src.runner.runner.KILL_GRACE_SECONDS` (no hardcoded `30.0` in
  new code). It reports `time_limit`, `hard_limit`, `memory_limit` as given in
  the config, plus instance `n = instance.n` and
  `m = len(instance.edges)` (edge count **after** loader dedup; the loader
  drops `(u,v)`/`(v,u)` duplicates and rejects self-loops).
  — Criterion: `monkeypatch.setattr(runner_mod, "KILL_GRACE_SECONDS", 7.5)` →
  `hard_limit == time_limit + 7.5`; `time_limit=None` → `hard_limit is None`.
  — OK: `time_limit=1800.0` → `hard_limit=1830.0`.
  — BAD: a second copy of the grace constant in the dry-run branch.

- **R7.** Dry-run performs NO side effects beyond reads:
  - does NOT spawn the worker subprocess (no
    `[sys.executable, "-m", "src.runner.worker", ...]` call). The read-only
    `git describe` subprocess inside `build_record.git_tag()` is allowed;
  - does NOT write `<out_dir>/<run_id>.json` or any other file;
  - does NOT create any directory (`out_dir` included);
  - executes no solver code and imports nothing NEW beyond what importing
    `src.runner.runner` already loads (the `src.sat` package incl. pysat is
    imported at module load — pre-existing; R3).
  — Criterion: a spy on `subprocess.run` records no worker-pattern call; no
  filesystem write occurs (check `out_dir` absent / unchanged).
  — OK: dry-run on a read-only checkout succeeds.
  — BAD: dry-run importing the config's solver module (a "warm-up" import of
    the dotted path) or touching `results/raw/`.

- **R8.** On success, `run_one(..., dry_run=True)` returns exactly the record
  shape defined under **Data model → DryRunRecord**: a `build_record(...)`
  record with `status_override="DRY_RUN"` plus one added key `dry_run`.
  `build_record` is called as
  `build_record(instance, config, None, wall_time=<measured elapsed of the dry-run steps>, status_override="DRY_RUN")`
  so `error=None`, all result-derived fields are `None`, `solution=None`,
  `metadata={}`, `solver=config.sat_solver or config.method`.
  — Criterion: every key of `RUN_FIELDS` plus `config`, `solution`,
  `metadata`, `dry_run` is present; `status == "DRY_RUN"`;
  `lb is ub is t_total is solution is None`.
  — BAD: inventing a second, divergent record shape for dry-run.

- **R9.** Dry-run uses no timers, sleeps, or budget waits; `wall_time` is the
  measured duration of the dry-run steps themselves (typically milliseconds,
  independent of `time_limit`).
  — Criterion: `wall_time < 5.0` for a small instance on the dev machine;
  changing `time_limit` does not change duration.
  — BAD: dry-run sleeping `time_limit` seconds or simulating a duration.

- **R10.** Dry-run adds no validation the real runner does not perform, except
  R3 (method-registry membership). In particular `time_limit <= 0`,
  negative `memory_limit`, unknown `abp_encoding` values etc. are **not**
  rejected: dry-run predicts what the runner would do, it does not police the
  config. (Known divergences are listed under Edge cases.)
  — Criterion: `Config(method="sat", time_limit=0)` dry-runs successfully with
  `hard_limit=30.0`.
  — BAD: dry-run rejecting `time_limit=0` while a real run would proceed and
  produce TO/ERR.

### B. CLI `python -m src.runner --dry-run`

- **R11.** New flag `--dry-run` (`action="store_true"`). All existing flags
  parse exactly as today; `Config` is built exactly as today; with
  `--dry-run`, the CLI calls `run_one(..., dry_run=True)` and prints the
  dry-run block instead of the normal result line. Without `--dry-run`,
  behavior is byte-identical to today.
  — Criterion: `python -m src.runner --instance p4.json --method oracle --dry-run`
  prints the 5-line block and exits 0; the same command without `--dry-run`
  behaves as before (existing tests stay green).

- **R12.** Dry-run stdout is exactly the following 5 lines, in this order, with
  no extra lines, no blank lines, nothing on stderr:
  ```
  DRY_RUN run_id={run_id}
  DRY_RUN instance={instance.id} n={n} m={m}
  DRY_RUN config method={method} abp_encoding={v} amo_encoding={v} sat_solver={v} search_mode={v} symmetry={v} warm_start={v} seed={v}
  DRY_RUN budget time_limit={v} hard_limit={v} memory_limit={v} memory_limit_enforced=false
  DRY_RUN output out_file={path} exists={true|false} resume_would_skip={true|false}
  ```
  Rendering rules: every value via `str(value)`, except `None` which renders
  as `none` and booleans which render as lowercase `true`/`false`;
  `out_file` as `str(Path(...))` (platform-native separators);
  `memory_limit_enforced=false` is a fixed literal that states the current
  runner truth (`memory_limit` is not a hard cap — `16-w2-acceptance.md`,
  `w3-review-notes.md` §4); if memory enforcement is ever added, the same
  change must update this literal.
  — OK (path4, oracle defaults, `--time-limit 1800`, `--out results/raw`;
  without `--out` the CLI default is the absolute `DEFAULT_OUT_DIR`, which
  R11 keeps unchanged for real runs):
  ```
  DRY_RUN run_id=path4__oracle__na__na__na__na__sym0__ws0__s0__tl1800.0__mlNone
  DRY_RUN instance=path4 n=4 m=3
  DRY_RUN config method=oracle abp_encoding=none amo_encoding=none sat_solver=none search_mode=none symmetry=false warm_start=false seed=0
  DRY_RUN budget time_limit=1800.0 hard_limit=1830.0 memory_limit=none memory_limit_enforced=false
  DRY_RUN output out_file=results\raw\path4__oracle__na__na__na__na__sym0__ws0__s0__tl1800.0__mlNone.json exists=false resume_would_skip=false
  ```
  — BAD: prose lines, banners, warnings, or a summary mixed into stdout;
  copying this example as an expected value (A4/A9/§4.1 compute `run_id`
  via `make_run_id` from the real command).

- **R13.** Exit codes: `0` = dry-run report printed; `2` = validation failure
  (instance unreadable/invalid, unknown method) with one line on stderr,
  `DRY_RUN ERROR: <exception message>`, and no traceback; any other exception
  is not caught (traceback + interpreter exit, as today). The stderr write in
  the dry-run branch must not crash on consoles whose codec cannot encode the
  message (the method-error text is Vietnamese; cp1252 consoles raise
  `UnicodeEncodeError`): before printing, make stderr lossy-safe — e.g.
  `sys.stderr.reconfigure(errors="replace")` when the attribute exists. The
  5 success lines are pure ASCII. The pre-existing cp1252 crash of argparse
  `--help`/usage text is unchanged (R11 keeps existing behavior).
  — Criterion: bad instance → exit 2 + `DRY_RUN ERROR:` on stderr;
  `--method nope` → exit 2; valid dry-run → exit 0; with
  `PYTHONIOENCODING=cp1252` in a subprocess run, the failure path still exits
  2 with `DRY_RUN ERROR:` on stderr and no `UnicodeEncodeError`/traceback.
  — BAD: reusing exit 1 (which today means "run produced an `ERR` record" —
  a different failure class: nothing ran here); letting the Vietnamese error
  message crash the error path on cp1252.

- **R14.** `--dry-run` composes with `--resume`: allowed, and
  `resume_would_skip` reflects what a real run with those flags would do. It
  never requires `out_dir` to exist.
  — OK: `--dry-run --resume` with existing `out_file` →
  `exists=true resume_would_skip=true`, exit 0.
  — BAD: making `--dry-run` + `--resume` an argparse error.

### C. W2 issue checkboxes (`docs/handoff/abp-sat-encoding/issues/W2/08..15*.md`)

- **R15.** Tick rule: a `[ ]` becomes `[x]` **only** if repo-verifiable
  evidence exists at edit time (an evidence doc under `docs/handoff/` or a
  named passing test). Every ticked box gets an evidence pointer in a new
  section appended at the bottom of the file:
  `## Closure evidence (2026-11-03)` listing item → evidence path(s) → one
  line on what the evidence shows. For tickets 08–14 the checkbox lines
  change only by `- [ ]` → `- [x]`; all reasons/annotations live in the
  Closure evidence section, not inline. Exactly two exceptions: (a) ticket 09
  box 2 stays `[ ]` and appends the fixed suffix `*(N/A — xem Closure
  evidence)*` after its unchanged text; (b) ticket 15 box 2's stale
  parenthetical is replaced per R17.
  — OK: ticket 12 box 2 ticked, pointer to `docs/handoff/w2-sat/12-test-matrix.md`
  (10 instance × 8 config OPT-oracle table).
  — BAD: ticking a box because "the work smells done".

- **R16.** Every checkbox that stays unticked gets a reason entry in its
  file's `## Closure evidence (2026-11-03)` section (why, with pointer); the
  checkbox line itself keeps `- [ ]`. No box is deleted or reordered.
  — OK: ticket 09 box 2 (Kissat solve/model/status/decode) stays `[ ]` with
  only the suffix `*(N/A — xem Closure evidence)*` appended; the Closure
  evidence entry reads: N/A vĩnh viễn W2 — Kissat bị loại, RQ2 giữ CaDiCaL +
  Glucose (`14-sat-methodology.md` §3.6); chặn tại `PYSAT_KISSAT_FAMILIES`
  (`src/sat/backend.py`) và `_validate_solver` (`src/sat/solve.py`); tests
  `tests/sat/test_backend.py`, `tests/sat/test_solve.py`; xem
  `docs/sat_tooling.md` mục Kissat.
  — BAD: silently ticking box 2 because box 4 (the fallback) is done;
  multi-line reasons inline in the checkbox line.

- **R17.** Expected per-file outcome (evidence verified 2026-11-03):
  - **08** — all 4 tick. Evidence: `12-test-matrix.md` section "Ticket 08
    closure — AMO exhaustive" (64 subsets × all assignments, both encodings,
    incl. 0/1-literal subsets), test
    `tests/sat/test_matrix.py::test_amo_exhaustive_closure_over_all_subsets`,
    8/8 config matrix (AMO change does not change ABP encoding or results),
    `SUPPORTED_AMO_ENCODINGS` in `src/sat/pairwise.py` contains no
    commander/product (box 4 is a verified negative).
  - **09** — boxes 1, 3, 4 tick; box 2 stays unticked (R16: inline suffix
    `*(N/A — xem Closure evidence)*`, reason in Closure evidence). Evidence:
    glucose4 columns all PASS in `12-test-matrix.md`;
    `tests/sat/test_glucose_e2e.py`; `INTERRUPTIBLE_FAMILIES` in
    `src/sat/backend.py`; Kissat limitation documented in
    `docs/sat_tooling.md`; RQ2 = CaDiCaL + Glucose per `14-sat-methodology.md`
    §3.6 (Closure evidence states the chosen branch: Kissat bị loại vĩnh viễn
    → giữ CaDiCaL + Glucose).
  - **10** — all 6 tick. Evidence: `14-sat-methodology.md` §3.5 (K ← B+1,
    UNSAT ⇒ OPT, `time_limit` budgets the whole K chain), §3.7 (metrics
    `variables, clauses, t_encode, t_solve, t_total, peak_memory` measured),
    `src/common/models.py` (`Config` has separate `abp_encoding`/`amo_encoding`;
    `Result` has no common `encoding` field — CONTRACT §4), matrix OPT-oracle
    tests for toy K-search.
  - **11** — all 4 tick. Evidence: `src/sat/generator.py` (path, cycle, grid,
    complete, star, binary_tree, disconnected, isolated, seeded
    `random_graph`, tier0 n ≤ 8 / tier1 9–16 per module docstring);
    `src/sat/loader.py` `read_instance`/`write_instance` (loader accepts every
    generator payload — same `Instance` shape, `REQUIRED_KEYS`); seeded
    random + `disconnected`/`isolated` instances present in the matrix run
    (`12-test-matrix.md` instance table); `Instance` fields match CONTRACT §2
    exactly (id, name, n, edges, source, tier).
  - **12** — all 5 tick. Evidence: `12-test-matrix.md` — 8/8 config matrix
    (8/8 = CaDiCaL + Glucose; the kissat column is documented N/A — not a
    2×2×3 = 12 grid; the N/A reason goes in Closure evidence, not inline)
    (box 1), 10/10 OPT-oracle per config (box 2), model counting table incl.
    two UNSAT rows (box 3), edge-case instances
    `disconnected`/`isolated`/`random8-seed42` (box 4), the pass/fail table
    itself is the output (box 5).
  - **13** — all 3 tick. Boxes 1 and 2: review verdict "đồng ý", indicator
    constraints not weak big-M; CP semantics agreed with a non-blocking
    note. Box 3 ("ghi kết luận vào ticket của P1"): ticked unconditionally —
    resolved 2026-11-03, verified via GH #20 (conclusion posted), GH #42,
    PR #48, `docs/handoff/w2-sat/13-review-p1-formulation.md`,
    `docs/handoff/w2-exact/16-w2-acceptance.md`; cite all five in Closure
    evidence.
  - **14** — all 3 tick. Evidence: `14-sat-methodology.md` §3.1–§3.5 (decision
    problem, variables, constraints, K-search), §3.2–§3.4 + §3.6 (pairwise,
    order, AMO, backend), trace table + explicit "no 2DBMP proof copied" note
    (§ header and §3.5).
  - **15** — box 2 is ticked **by this task** only after part D is done (flag
    merged + real output recorded in the evidence doc). Boxes 1, 3, 4 are
    already `[x]`. The stale parenthetical on box 2 ("chưa thể: runner không
    có cờ --dry-run …") is replaced by a short pointer: the flag exists, the
    real output is in `docs/handoff/w2-sat/15-m1-gate-evidence.md` §4.1, and
    the compute estimate remains in §3.
    The decision lines at the bottom of the file (NO-GO, date, cut list
    pointer) stay byte-identical.

- **R18.** Ticket `Status:` lines (`ready-for-human` etc.) and `Owner:` /
  `Blocked by:` lines are unchanged in this task (the triage label set has no
  done value; relabeling is a separate decision). New prose added to these
  Vietnamese files is written in Vietnamese, technical identifiers verbatim.
  Exempt technical labels: the fixed heading `## Closure evidence
  (2026-11-03)` and the fixed suffix `*(N/A — xem Closure evidence)*` stay
  as written.

### D. M1 evidence doc (`docs/handoff/w2-sat/15-m1-gate-evidence.md`)

- **R19.** Sections 1–3, 5, and the decision content of 6 are NOT edited. The
  NO-GO decision, its reasons, and the Bonus cut list remain byte-identical.
  Only two additions are allowed: a new subsection **§4.1** and a pointer
  appended to the §6 bullet "Việc còn mở của gate" (bullet text kept, pointer
  added: "đã hoàn tất <date> — xem mục 4.1").
  — Criterion: `git diff` on the file touches only §4.1 (new) and the one §6
  bullet.
  — BAD: rewriting §4's conclusion ("CHƯA thực hiện được") in place — §4 is a
  dated historical record; it stays, §4.1 supersedes it.

- **R20.** §4.1 is titled `### 4.1 Cập nhật <date>: --dry-run đã có trên runner`
  and contains, in Vietnamese (file language):
  1. the **verbatim command** actually executed (full flags, real instance
     file), with branch and `git_tag`;
  2. the **verbatim stdout** of that command in a fenced block — copied from
     a real execution, never hand-written (same honesty rule as
     `12-test-matrix.md`: "không viết tay");
  3. a reading of the result: `run_id` matches `make_run_id`; `hard_limit =
     time_limit + KILL_GRACE_SECONDS`; `memory_limit` reported and **not
     enforced** (`memory_limit_enforced=false`); `n`, `m`;
     `exists`/`resume_would_skip`;
  4. an explicit scope statement: this closes only the `--dry-run` blocker
     item (ticket 15 item 2); the M1 decision stays NO-GO with unchanged
     reasons and unchanged Bonus cut list.
  — Recommended command shape (substitute a real instance file from
  `benchmark/` or a generator-written file; the recorded verbatim command
  must name the real interpreter — global `python` (3.13) lacks pysat,
  `.venv\Scripts\python.exe` (3.11) has it — and pass `--out results/raw` so
  `out_file` is relative and portable):
  `.venv\Scripts\python.exe -m src.runner --instance <tier1-instance.json> --method sat --abp-encoding pairwise --amo-encoding seqcounter --sat-solver cadical195 --search-mode multi --time-limit 1800 --out results/raw --dry-run`
  — Criterion: the pasted output parses against R12's format (5 `DRY_RUN`
  lines) and its `run_id`/budget values are self-consistent with the command.
  — BAD: pasting an invented output block, or silently editing §6's reasons.

## Data model

Entity: **DryRunInfo** — returned under key `dry_run` of the record.

- `out_file`: `str` — `str(Path(out_dir) / f"{run_id}.json")`, path exactly as
  a real run would use (not resolved, not created).
- `exists`: `bool` — `out_file.exists()` at dry-run time.
- `resume_would_skip`: `bool` — `True` iff `resume and exists`; a real run
  with these arguments would return the existing record instead of running.
- `hard_limit`: `float | None` — `time_limit + KILL_GRACE_SECONDS`; `None`
  iff `time_limit is None` (means: worker subprocess has no hard timeout and
  can run forever — must be visible in the CLI line as `hard_limit=none`).
- `n`: `int` — `instance.n`, `>= 1` (loader rejects `n = 0`).
- `m`: `int` — `len(instance.edges)` after loader validation/dedup
  (`>= 1`; loader rejects edgeless graphs).

Entity: **DryRunRecord** — return value of `run_one(..., dry_run=True)`.

- All `RUN_FIELDS` keys (via `build_record`):
  - `run_id`: `str`, deterministic (R4).
  - `instance`: `str` (`instance.id`); `method`, `abp_encoding`,
    `amo_encoding`, `search_mode`, `symmetry`, `warm_start`, `seed`,
    `time_limit`, `memory_limit`: from `config`, types as in `Config`.
  - `solver`: `str` — `config.sat_solver or config.method`.
  - `status`: literal `"DRY_RUN"` (runner-level only — see C1).
  - `lb`, `ub`, `t_encode`, `t_solve`, `t_total`, `variables`, `clauses`,
    `peak_memory`: `None`.
  - `git_tag`: `str` (real `git describe --tags --always --dirty` output);
    `host`: `str`; `timestamp`: ISO-8601 UTC string (now).
  - `wall_time`: `float` — measured dry-run elapsed (R9).
  - `error`: `None` on success.
- `config`: `dict` — `asdict(config)`.
- `solution`: `None`.
- `metadata`: `{}`.
- `dry_run`: `DryRunInfo` (above).

Entity: **CLI surface**

- Flag: `--dry-run`, `store_true`.
- stdout: the 5 `DRY_RUN` lines (R12).
- stderr on validation failure: `DRY_RUN ERROR: <message>` (single line,
  cp1252-safe — R13).
- exit codes: `0` success, `2` validation failure, otherwise unhandled
  exception behavior unchanged (R13).

## Edge cases

- **out_dir does not exist** → `exists=false`, `resume_would_skip=false`; no
  directory is created (diff from real run, which mkdirs — intended).
- **out_file exists, `--resume` not set** → `exists=true`,
  `resume_would_skip=false`; dry-run does not read the file; a real run would
  overwrite it. Dry-run report stays factual.
- **out_file exists and is corrupt**, `--resume` set → `resume_would_skip=true`,
  dry-run succeeds and returns its own `DRY_RUN` record (file content is never
  parsed — R5). A real run would crash on `json.loads`; that divergence is
  accepted: dry-run is read-only and must not depend on file content.
- **Instance file missing** → API: `FileNotFoundError` propagates (same as
  real run). CLI: exit 2, `DRY_RUN ERROR: ...` on stderr.
- **Instance invalid (missing key / bad type / self-loop / out-of-range
  vertex / `n=0` / no edges)** → API: `ValueError` identical to real run
  (R2). CLI: exit 2.
- **Duplicate edges `(u,v)` and `(v,u)` in file** → loader keeps the first,
  `m` counts unique edges; `run_id` unaffected (it uses `instance.id`, not
  file content). Report `m` = post-dedup count; two files with the same `id`
  but different edges map to the same `run_id` — pre-existing `make_run_id`
  property, not changed here, but a dry-run batch (US2) is exactly where such
  a collision becomes visible.
- **`time_limit = None`** → `hard_limit=none` in CLI output; record
  `dry_run.hard_limit is None`. Meaning: no hard kill; report must make the
  unbounded run visible, not hide it.
- **`time_limit = 0` or negative** → not validated (R10); `hard_limit` computed
  by the same formula (`0.0 → 30.0`). What a real run then does (TO / ERR /
  raise, family-dependent per `13-review-p1-formulation.md` R3) is out of
  dry-run's scope.
- **`memory_limit` set** → reported verbatim in config + budget lines;
  `memory_limit_enforced=false` always (current runner truth).
- **Unknown method** (`nope`) → API `ValueError` (contains "không có trong
  registry"); CLI exit 2. Known divergence: a real run would produce an
  `ERR` record instead of failing — dry-run is deliberately stricter (R10).
- **Dotted-path method that does not exist** (e.g.
  `tests.runner.nonexistent_module:solve`) → dry-run passes (no import — R3);
  real run → `ERR` record from the worker. Documented limitation: dry-run
  cannot verify importability without importing.
- **Method in registry but backend unavailable** (gurobipy/cplex not
  installed) → dry-run succeeds; real run → `ERR` record. Same limitation.
- **`KILL_GRACE_SECONDS` changed/monkeypatched** → `hard_limit` follows; no
  hardcoded `30.0` anywhere in the new code (R6).
- **`--dry-run` without `--instance`** → argparse usage error, exit 2
  (pre-existing argparse behavior, unchanged by this task).
- **Non-ASCII `instance.id`** → stdout rendering follows `print()` on the
  host console; exposure is identical to the existing result line, not a new
  risk. Generator ids are ASCII.

## Acceptance criteria (testable)

Code (extend `tests/runner/test_runner.py`):

- **A1** Shape: dry-run record has all `RUN_FIELDS` + `config` + `solution` +
  `metadata` + `dry_run`; `status == "DRY_RUN"`; `lb`, `ub`, `t_encode`,
  `t_solve`, `t_total`, `variables`, `clauses`, `peak_memory` are `None`;
  `solution is None`; `metadata == {}`; `error is None`.
- **A2** Side effects: after `run_one(p, cfg, tmp/"raw", dry_run=True)` with
  no prior dir, `(tmp/"raw").exists() is False`; with a pre-existing dir
  containing files, no file is added or modified.
- **A3** Budget: `record["dry_run"]["hard_limit"] == cfg.time_limit +
  runner_mod.KILL_GRACE_SECONDS`; with `KILL_GRACE_SECONDS` monkeypatched to
  `7.5`, the value follows; `time_limit=None` → `hard_limit is None`.
- **A4** `run_id`: dry-run `run_id == make_run_id(read_instance(p), cfg)` and
  equals the `run_id` of a real run executed afterwards with the same args;
  the real run writes its file and does not collide.
- **A5** Resume reporting: pre-create `out_file` (garbage bytes) →
  `exists=True`; `resume=True` → `resume_would_skip=True` and the returned
  record is `status == "DRY_RUN"` (not the garbage); `resume=False` →
  `resume_would_skip=False`.
- **A6** No worker spawn: wrap `subprocess.run` with a recorder; call dry-run;
  assert no recorded call has args starting with
  `[sys.executable, "-m", "src.runner.worker"]` (the `git describe` call is
  permitted and must not fail the assertion).
- **A7** Validation parity: for an invalid instance, dry-run raises the same
  exception type and message as real `run_one` (e.g. empty graph →
  `"Instance is empty (n = 0 or no edges)."`) and writes nothing.
- **A8** Method check: `Config(method="nope")` → `ValueError` matching
  "không có trong registry"; `Config(method="tests.runner.nonexistent_module:solve")`
  passes; snapshot `set(sys.modules)` immediately before the dry-run call and
  assert no NEW module appears during it. A bare "module absent after the
  call" check on a nonexistent module is vacuous (`src.sat`/pysat are already
  imported when `src.runner.runner` is imported — the assertion covers new
  entries only).
- **A9** CLI success: pick one harness — `sys.argv` monkeypatched with
  `assert main() == 0`, or subprocess with exit-code 0. Pass
  `--out <tmp_path>` (never assert a repo-absolute default path); compute the
  expected `run_id` via `make_run_id` (never copy the R12 example); compare
  `out.splitlines()` against the 5 expected strings (first 4 exact; the
  output line split into prefix / `Path(out_file)` / `exists=` tail, so no
  separator brittleness); assert `err == ""`; nothing written under `--out`.
- **A10** CLI failure: bad instance or unknown method → stderr starts with
  `DRY_RUN ERROR:`, no traceback in stderr, return code 2, nothing written.
  Run the subprocess with `PYTHONIOENCODING=cp1252` to prove the stderr write
  survives a codec that cannot encode the Vietnamese message (no
  `UnicodeEncodeError` in stderr, still exit 2) — R13.
- **A11** Regression: all pre-existing tests in `tests/runner/test_runner.py`
  pass unmodified; green means `.venv\Scripts\python.exe -m pytest tests -q
  --basetemp=.pytest-tmp` → no failures (passed + skipped; 3 skips expected —
  CPLEX CP engine missing). Without `--basetemp` the default Windows temp
  root fails with `PermissionError: [WinError 5]`; without `.venv`, pysat is
  missing (global python = 3.13 without pysat; `.venv` = 3.11 with pysat).

Docs:

- **D1** Every ticked checkbox in `08..15` has an evidence pointer in that
  file's `## Closure evidence (2026-11-03)` section; no tick without pointer.
- **D2** Every unticked checkbox has a reason entry in its file's Closure
  evidence section (expected unticked set: 09 box 2 only — 13 box 3 is
  resolved and ticked, see R17).
- **D3** `15-m1-gate-evidence.md`: §1–§3, §5 and §6 decision text unchanged
  except the single §6 pointer addition; §4 original text unchanged; §4.1
  present with verbatim command + verbatim 5-line output; the output parses
  against R12 (format check — values come from the real run, never from the
  R12 example). Diff check is file-scoped:
  `git diff -- docs/handoff/w2-sat/15-m1-gate-evidence.md`.
- **D4** Ticket 15: item 2 `[x]` with pointer to §4.1; stale parenthetical
  replaced by the pointer; "NO-GO" decision lines byte-identical.
- **D5** `Status:`/`Owner:`/`Blocked by:` lines in all touched ticket files
  unchanged; new prose in those files is Vietnamese.
- **D6** No change **caused by this task** beyond the Scope list plus the
  `docs/handoff/w2-dry-run/*` handoff artifacts (`requirements.md`,
  `scope.md`, `review-qa.md`, `review-be.md`). Check: `git status` diff
  against the pre-task baseline — pre-existing dirty files
  (`docs/handoff/sat-g1/*` and friends) and the untracked handoff directory
  are allowed and not counted. Do not stash or revert unrelated work to make
  the check pass.

## Contradictions

- **C1: dry-run record status vs CONTRACT §5.** CONTRACT §5 enumerates exactly
  `OPT | FEAS | TO | MO | ERR`; the dry-run record carries `"DRY_RUN"`.
  Resolution: `"DRY_RUN"` is a runner-level record status only — it is never
  written to disk (dry-run writes nothing), never returned by a solver, never
  aggregated into `runs.csv`; `CONTRACT.md` §5 is not amended in this task.
  Alternative considered and rejected: `status="ERR"` (misleading — nothing
  failed).
- **C2: "estimate budget" vs memory reality.** The task says "estimate/report
  budget … `memory_limit`", but `memory_limit` is not enforced anywhere
  (`16-w2-acceptance.md`; `w3-review-notes.md` §4; `14-sat-methodology.md`
  §3.5 MO note). Resolution: dry-run **reports** `memory_limit` and prints the
  fixed fact `memory_limit_enforced=false`; it must not imply a hard cap. No
  runtime/CNF-size estimation is produced (see Scope).
- **C3: "validate config" vs no-import rule.** Full validation via
  `registry.resolve()` requires importing the solver module — heavy deps,
  license errors, and code execution inside a "nothing executes" check.
  Resolution: static membership check only (R3); importability is a
  documented limitation.
- **C4: dry-run fail-fast vs real-run lenience.** A real run turns a bad
  method into an `ERR` record; dry-run raises. Resolution: intended — dry-run
  is a pre-flight check; divergence is documented (R10, edge cases), not a
  bug.
- **C5: ticking P2's tickets from this task.** Tickets 08–14 are owned by P2,
  but this task is explicitly charged with W2 checkbox completion.
  Resolution: mitigate with the evidence rule (R15/R16/R17) — every tick maps
  to existing repo evidence; no judgment ticks.
- **C6: R4/R12 example `run_id`s vs actual `make_run_id` output.** Examples
  showed `tl30.0__mlna` / `tl1800.0__mlna`; `make_run_id` renders
  `tl{time_limit}` / `ml{memory_limit}` as raw strings (`None` →
  `tlNone`/`mlNone`, int `30` → `tl30`). Resolution: examples corrected
  (`tl30__mlNone` API, `tl1800.0__mlNone` CLI); `make_run_id` untouched —
  changing it would rename every `results/raw` file and break `--resume`.
- **C7: checkbox-line immutability vs required edits.** R15's "not edited
  beyond the bracket" collided with R16's inline annotations and R17/D4's
  parenthetical replacement. Resolution: reasons moved to the
  `## Closure evidence` section; two explicit exceptions only (09 box 2
  suffix `*(N/A — xem Closure evidence)*`; 15 box 2 parenthetical → §3/§4.1
  pointer) — now stated in R15/R16/R17.

## Open questions

- Which instance file is used for the recorded §4.1 dry-run run? Default:
  one tier-1 instance from `benchmark/` (or a generator-written file) with
  the canonical-config-shaped command in R20; the implementer may substitute
  any existing instance file as long as the real command + output are
  recorded verbatim.
- Should `experiments/pilot_rq1.py` / `pilot_rq2.py` also gain `--dry-run`?
  Assumed out of scope (task names `src/runner` only); flag if otherwise.
