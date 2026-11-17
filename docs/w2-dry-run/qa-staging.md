# QA — Staging (Phase 4)

Scope: re-test B1–B5 from `qa-dev.md`, then Phase 4 system/integration/regression
against `test-plan.md`, `requirements.md`, `scope.md`, `api-contract.md`.

Branch `p2/w4-sat`. Interpreter `.venv\Scripts\python.exe` (3.11.15, pysat present).

## Verdict

PASS — B1–B5 all resolved, full suite green (538 passed, 3 skipped), no side
effects on `results/raw/` or `docs/handoff/sat-g1/`.

## Tests written

No new test files. Re-ran the existing suite plus manual probes; the dry-run
behaviour is already covered by 24 tests in `tests/runner/test_runner.py`
(lines 81–509), which I read and executed rather than duplicated.

- `pytest tests -q` — full regression, 538 passed / 3 skipped in 20.50s. The 3
  skips are CPLEX CP tests (backend absent), expected.
- B1 probe — `PYTHONIOENCODING=cp1252` + non-ASCII `--out` (`...\đường`):
  exit 0, 5 `DRY_RUN` lines, lossy `???ng` rendering, no traceback.
- B2 probe — bare-interpreter import snapshot with `platform.node()` pre-warmed:
  `NEW: []` after dry-run. No module imported by the dry-run path.
- B3 probe — `--method nope` + cp1252: exit 2, `DRY_RUN ERROR:` with lossy
  Vietnamese, no traceback.
- B4 probe — `--out` = existing file → exit 0, `exists=false`; `--out Z:\nope`
  → exit 0, `exists=false`.
- B5 probe — `instance.id` with newline: block splits, documented, not fixed.
- Cleanliness — `git status --porcelain results/raw` and
  `git status --porcelain docs/handoff/sat-g1` both empty after all runs.

## Bugs

None blocking. Two low-severity observations, both non-blocking:

- `src/runner/runner.py:51` — `start = perf_counter()` is taken after
  `read_instance` (line 48), so the reported `wall_time` excludes instance
  parsing. `api-contract.md` §1.2 step 6 implies the timer covers the whole
  dry-run. Failure scenario: a huge instance makes the reported `wall_time`
  understate real pre-flight cost; a report reader comparing dry-run cost to
  real-run cost sees a gap. Fix hint: move `start` above line 48, or state in
  the contract that `wall_time` covers post-read work only.
- `src/runner/runner.py:57` and `:80` — `make_run_id(instance, config)` is
  computed in the dry-run branch and again in the real-run path; `build_record`
  also derives it. Redundant, not a bug (pure function, same inputs). No fix
  needed unless `make_run_id` ever gains side effects.

## Could not check

- Real solver runs (`sat`, `cp_sat`, `gurobi_mip`, `cplex_cp`, `cplex_mip`) —
  out of dry-run scope; only the dry-run pre-flight path was exercised.
- Linux/macOS path-separator rendering in the `out_file` line — Windows host only.
- A real cp1252 console — probes used pipes with `PYTHONIOENCODING=cp1252`, not a
  true console code page.
- `--help` under cp1252 — pre-existing crash, out of scope for this ticket.
- `--dry-run` for `experiments/pilot_rq*.py` — out of scope per `scope.md`.
