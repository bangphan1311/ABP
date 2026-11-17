# API Contract — W2 dry-run (`--dry-run`)

Binding implementation contract for the runner `--dry-run` capability. Restates
`requirements.md` R1–R14 (same directory) as an implementable interface. Where
this document and `requirements.md` differ, `requirements.md` wins; where both
are silent, `CONTRACT.md` (repo root) wins. Scope is `src/runner/runner.py` and
`src/runner/__main__.py` only — `src/runner/schema.py`, `make_run_id`, and
`src/runner/worker.py` are not modified.

Non-goals: CNF-size/runtime estimation, memory-limit enforcement, `runs.csv`
changes, `CONTRACT.md` §5 status-vocabulary changes, `--dry-run` for
`experiments/pilot_rq*.py`.

---

## 1. Python API

### 1.1 Exact signature

```python
def run_one(
    instance_path: str | Path,
    config: Config,
    out_dir: str | Path = DEFAULT_OUT_DIR,
    *,
    resume: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
```

Rules:

- `dry_run` is **keyword-only** (after `*`) and appended after `resume`;
  default `False`. It is never a positional third argument.
- Positional order and all existing call sites are unchanged:
  `run_one(p, cfg, out)` and `run_one(p, cfg, out, resume=True)` still work and
  keep today's behavior exactly.
- Return type stays `dict[str, Any]` for both modes. With `dry_run=True` the
  returned dict is a **`DryRunRecord`** (§1.3); the record is **not persisted**
  (no file is written) — this must be stated in a one-line docstring on the
  dry-run branch or on `run_one`.

### 1.2 Validation rules and order of operations

Order for the `dry_run=True` branch is fixed. It must execute **before** the
existing `out_dir.mkdir(parents=True, exist_ok=True)` call in `runner.py`
(today line 43), so that no directory is ever created in dry-run:

1. `instance = read_instance(instance_path)` — identical to a real run; its
   exceptions propagate **unwrapped and unchanged**: `ValueError` for
   schema/edge/empty-graph violations, `OSError`/`json.JSONDecodeError` for
   unreadable files. No new exception type, no `ERR` record substitution.
   A missing instance file therefore raises `FileNotFoundError` in both modes,
   at the same first step.
2. **Static method check** — exactly:
   `config.method in registry.METHODS or ":" in config.method`.
   If false, raise `ValueError` whose message contains
   `không có trong registry` and the sorted valid method list (same wording as
   `registry.resolve`). Do **not** call `registry.resolve()` and do **not**
   import the solver module. Importing `src.runner.registry` for the `METHODS`
   mapping is required by this check and is safe: `registry` imports solver
   modules lazily (`importlib` only inside `resolve`).
3. `run_id = make_run_id(instance, config)` — existing function, untouched.
   No host/timestamp/path components added; deterministic from
   `instance.id` + config only.
4. `out_dir = Path(out_dir)`;
   `out_file = out_dir / f"{run_id}.json"`;
   `exists = out_file.exists()`;
   `resume_would_skip = bool(resume and exists)`.
5. `hard_limit = None if config.time_limit is None else config.time_limit + KILL_GRACE_SECONDS`.
   `KILL_GRACE_SECONDS` is read **at call time** from the
   `src.runner.runner` module global (so monkeypatching it is observed). No
   second copy of the constant, no hardcoded `30.0`, no copy in
   `src/runner/__main__.py`.
6. `record = build_record(instance, config, None, wall_time=<measured elapsed of steps 1–5>, status_override="DRY_RUN")`.
   The `git describe` subprocess inside `build_record.git_tag()` is permitted
   and must not be blocked. `wall_time` is the measured duration of the
   dry-run steps themselves (typically milliseconds); no timers, sleeps, or
   budget waits — it is independent of `time_limit`.
7. `record["dry_run"] = {...}` — plain `dict` (no new dataclass), six keys per
   §1.3.
8. Return `record`. Nothing is written.

Prohibitions in the dry-run branch (each is an acceptance failure):

- no `out_dir.mkdir(...)` and no creation of `out_dir` or any other directory;
- no `tempfile.TemporaryDirectory` block;
- no worker spawn (`[sys.executable, "-m", "src.runner.worker", ...]`) and no
  `Popen`/`check_output` equivalent;
- no write of `<out_dir>/<run_id>.json` or any other file;
- no read/parse of an existing `out_file`, even when `resume=True` and the file
  contains garbage — `exists`/`resume_would_skip` are pure `Path.exists()`
  facts;
- no solver execution and no **new** solver-module import. "No new solver
  imports" means: no module under `src.sat`, `src.exact`, `pysat`, `gurobipy`,
  or `cplex` is imported by the dry-run branch. Importing
  `src.runner.registry` for the static method check is explicitly allowed.
  Stdlib modules that `build_record` touches lazily (e.g. `platform.node()`
  pulling in `socket`) are pre-existing `build_record` behavior, not a
  dry-run import, and are allowed.

`dry_run=False` path: byte-identical to today — `read_instance` → `mkdir` →
`run_id` → resume `json.loads` → tempdir + worker → `_to_record` → write. The
dry-run branch must not reorder or alter any of these steps for real runs.

### 1.3 `DryRunRecord` schema

`DryRunRecord` is the dict returned by `run_one(..., dry_run=True)`:

- **`build_record` output**, called exactly as in step 6 above. With
  `result=None` this yields:
  - `run_id`: `str` — `make_run_id(instance, config)`.
  - `instance`: `str` — `instance.id`.
  - `method`, `abp_encoding`, `amo_encoding`, `search_mode`, `symmetry`,
    `warm_start`, `seed`, `time_limit`, `memory_limit`: from `config`, types as
    in `Config`.
  - `solver`: `str` — `config.sat_solver or config.method`.
  - `status`: literal `"DRY_RUN"` (via `status_override`).
  - `lb`, `ub`, `t_encode`, `t_solve`, `t_total`, `variables`, `clauses`,
    `peak_memory`: `None`.
  - `git_tag`: `str` — real `git describe --tags --always --dirty` output.
  - `host`: `str`; `timestamp`: ISO-8601 UTC string (now).
  - `wall_time`: `float` — measured dry-run elapsed.
  - `error`: `None` on success.
  - `config`: `dict` — `asdict(config)`.
  - `solution`: `None`.
  - `metadata`: `{}`.
- **Added key `dry_run`**: plain `dict` (not a dataclass) with exactly these
  six keys:

  | key | type | value |
  |---|---|---|
  | `out_file` | `str` | `str(Path(out_dir) / f"{run_id}.json")` — not resolved, not created |
  | `exists` | `bool` | `out_file.exists()` at dry-run time |
  | `resume_would_skip` | `bool` | `True` iff `resume and exists` |
  | `hard_limit` | `float \| None` | `time_limit + KILL_GRACE_SECONDS`; `None` iff `time_limit is None` |
  | `n` | `int` | `instance.n` |
  | `m` | `int` | `len(instance.edges)` after loader dedup/validation |

Schema invariants:

- The full key set is every key of `RUN_FIELDS` (`src/runner/schema.py`) plus
  `config`, `solution`, `metadata`, `dry_run`. No divergent second record
  shape, no extra/removed keys.
- `"DRY_RUN"` is a **runner-level record status only**: never written to disk,
  never returned by a solver, never aggregated into `runs.csv`; `CONTRACT.md`
  §5 is not amended.
- `m` counts edges **after** loader dedup (loader drops `(u,v)`/`(v,u)`
  duplicates and rejects self-loops); `n >= 1`, `m >= 1` for valid instances.
- Dry-run adds no validation the real runner does not perform, except the
  static method check in step 2. In particular `time_limit <= 0`, negative
  `memory_limit`, and unknown `abp_encoding` values are **not** rejected:
  dry-run predicts, it does not police the config.

---

## 2. CLI contract (`src/runner/__main__.py`)

### 2.1 Flag

```python
p.add_argument("--dry-run", action="store_true")
```

- All existing flags parse exactly as today; `Config` is constructed exactly as
  today.
- With `--dry-run`: call
  `run_one(a.instance, config, a.out, resume=a.resume, dry_run=True)` and print
  the 5-line block (§2.2) instead of the normal result line.
- Without `--dry-run`: the call, the printed result line, and the return code
  are **byte-identical** to today (existing tests must stay green).

### 2.2 stdout — exact 5-line format

Exactly these five lines, in this order, one trailing newline at end of the
last line, no extra lines, no blank lines:

```text
DRY_RUN run_id={run_id}
DRY_RUN instance={instance.id} n={n} m={m}
DRY_RUN config method={method} abp_encoding={v} amo_encoding={v} sat_solver={v} search_mode={v} symmetry={v} warm_start={v} seed={v}
DRY_RUN budget time_limit={v} hard_limit={v} memory_limit={v} memory_limit_enforced=false
DRY_RUN output out_file={path} exists={true|false} resume_would_skip={true|false}
```

Rendering rules (binding):

- Every value rendered via `str(value)`, except:
  - `None` renders as `none` (lowercase, no quotes);
  - booleans render as lowercase `true` / `false` (Python's `str(True)` is not
    acceptable);
  - `out_file` renders as `str(Path(...))` with platform-native separators.
- `memory_limit_enforced=false` is a fixed literal stating the current runner
  truth (`memory_limit` is not a hard cap). If enforcement is ever added, the
  same change must update this literal.
- The five lines are pure ASCII **except** `instance.id` and `out_file`, which
  are user-controlled and may contain non-ASCII (e.g. a Vietnamese `--out`
  directory). The dry-run branch therefore makes stdout lossy-safe
  (`sys.stdout.reconfigure(errors="replace")` when available) before printing,
  so a cp1252 console renders unencodable characters as `?` instead of raising
  `UnicodeEncodeError`. This is a new exposure relative to the real result
  line, which never prints `out_file`.
- Line 5 suffix order is `exists=` then `resume_would_skip=`; both booleans.

Illustrative shape only — values must be computed by `make_run_id` and the real
config, never copied from this example:

```text
DRY_RUN run_id=path4__oracle__na__na__na__na__sym0__ws0__s0__tl1800.0__mlNone
DRY_RUN instance=path4 n=4 m=3
DRY_RUN config method=oracle abp_encoding=none amo_encoding=none sat_solver=none search_mode=none symmetry=false warm_start=false seed=0
DRY_RUN budget time_limit=1800.0 hard_limit=1830.0 memory_limit=none memory_limit_enforced=false
DRY_RUN output out_file=results\raw\path4__oracle__na__na__na__na__sym0__ws0__s0__tl1800.0__mlNone.json exists=false resume_would_skip=false
```

### 2.3 stderr — cp1252-safe handling

- Only the `--dry-run` branch is wrapped, in
  `try/except (ValueError, OSError)`; on a validation failure print **one**
  line to stderr: `DRY_RUN ERROR: <exception message>`, then return `2`.
- No traceback on this path. Any other exception type is **not** caught —
  traceback + interpreter exit as today.
- Before writing, make stderr lossy-safe so a codec that cannot encode the
  Vietnamese error text does not crash the error path, e.g.
  `sys.stderr.reconfigure(errors="replace")` when the attribute exists. The
  Vietnamese method-error message must not produce `UnicodeEncodeError`.
- Successful dry-run writes **nothing** to stderr.

### 2.4 Exit codes

| code | meaning |
|---|---|
| `0` | dry-run report printed successfully (also `--dry-run --resume` when the target file exists) |
| `2` | validation failure: instance unreadable/invalid or unknown method; one `DRY_RUN ERROR:` line, no traceback |

- Exit `1` (today's "run produced an `ERR` record") is **not** reused for
  dry-run failures — nothing ran, so it is a different failure class.
- Pre-existing argparse usage errors keep exit `2` (e.g. `--dry-run` without
  `--instance`).
- `--dry-run` composes with `--resume`: allowed, not an argparse error;
  `resume_would_skip` reflects what a real run with those flags would do; it
  never requires `out_dir` to exist.

### 2.5 Non-dry-run behavior is untouched

Without `--dry-run`, the CLI must keep today's exact behavior: same stdout
result line (`{run_id}: {status} lb=... ub=... t_total=... wall=...s` plus
`  error=...` when `error` is truthy), same return mapping (`0` when
`status != "ERR"`, `1` when `ERR`), same exceptions. The dry-run code path is
additive only.

---

## 3. Known divergences and limitations (accepted)

Documented, not bugs — dry-run is a read-only pre-flight check:

- **Unknown method**: dry-run raises `ValueError`; a real run would produce an
  `ERR` record. Intended (stricter pre-flight).
- **Dotted-path method that does not exist** (e.g.
  `tests.runner.nonexistent_module:solve`): dry-run passes (no import); real
  run → `ERR` record. Dry-run cannot verify importability without importing.
- **Method in registry but backend unavailable** (gurobipy/cplex not installed):
  dry-run succeeds; real run → `ERR` record. Same limitation.
- **Existing `out_file` is corrupt, `resume=True`**: dry-run reports
  `exists=true resume_would_skip=true` and returns its own `DRY_RUN` record;
  the file is never parsed. A real run would crash on `json.loads`.
- **`time_limit = None`** (API only; CLI `--time-limit` is always a float):
  `hard_limit` is `None`, meaning no hard kill — the report must make the
  unbounded run visible as `hard_limit=none`, not hide it.
- **`time_limit = 0` or negative**: not validated; `hard_limit` follows the same
  formula (`0.0 → 30.0`).
- **`memory_limit` set**: reported verbatim in config and budget lines;
  `memory_limit_enforced=false` always.
- **`KILL_GRACE_SECONDS` monkeypatched**: `hard_limit` follows it; no hardcoded
  `30.0` in new code.
- **`--out` is a file, a nonexistent drive, or a UNC path**: dry-run reports
  `exists=false` and exits `0`; a real run would fail at `out_dir.mkdir(...)`.
  Dry-run does not validate the output path (R10 forbids new validation).
- **`instance.id` contains a newline**: the 5-line block splits into more lines
  (`splitlines()` sees 7). Pre-existing exposure — the real result line also
  embeds `instance.id` verbatim. Generator ids are ASCII and newline-free.

---

## 4. Acceptance mapping

The contract is satisfied when `tests/runner/test_runner.py` proves A1–A11 of
`requirements.md`:

- A1 record shape/status/None fields; A2 no directory/file side effects; A3
  budget formula incl. monkeypatched `KILL_GRACE_SECONDS` and `None` limit; A4
  `run_id` equals `make_run_id` and a real run's `run_id`; A5 resume reporting
  with garbage file; A6 no worker spawn (`git describe` allowed); A7 validation
  parity for invalid instances; A8 static method check + no new solver modules;
  A9 CLI success 5-line output with no writes under `--out`; A10 CLI failure
  path with `PYTHONIOENCODING=cp1252`, exit `2`, no traceback; A11 pre-existing
  tests green.
