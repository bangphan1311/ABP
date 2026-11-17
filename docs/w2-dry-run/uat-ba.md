# BA UAT — W2 gap closure: runner `--dry-run`, W2 checkboxes, M1 evidence

Date: 2026-11-03 · Branch `p2/w4-sat` · git_tag `v0.1-contract-126-g6b6b8b5-dirty`
Interpreter: `.venv\Scripts\python.exe` (3.11, pysat present).

Sources verified against: `requirements.md` (R1–R20, A1–A11, D1–D6, C1–C7),
`qa-staging.md`, `dev-notes.md`, `src/runner/runner.py`,
`src/runner/__main__.py`, `tests/runner/test_runner.py`,
`src/runner/registry.py`, `src/runner/schema.py`, W2 issues `08..15`,
`docs/handoff/w2-sat/15-m1-gate-evidence.md`.

## Verdict

**PASS — sign-off granted.** All 20 business rules, 11 acceptance criteria and
6 doc criteria verified. Zero blocking findings. Three non-blocking
observations (below), all already documented upstream or within spec
tolerance.

Evidence gathered live in this session (not copied from upstream claims):

- Full suite: `pytest tests -q --basetemp=...` → **538 passed, 3 skipped in
  18.37s** (3 skips = CPLEX CP engine absent, matches A11 baseline).
- §4.1 command replayed verbatim (read-only dry-run) → stdout **byte-identical**
  to the block recorded in `15-m1-gate-evidence.md` §4.1, exit `0`, empty
  stderr, `git status --porcelain results/raw` empty after the run.
- `git diff` inspected for every touched doc; `git status --porcelain` for D6.

## Rule-by-rule verification

### A. `run_one(..., dry_run=...)` — API

| Rule | Verdict | Evidence |
|---|---|---|
| R1 signature keyword-only `dry_run` after `resume`, default `False` | PASS | `src/runner/runner.py:34-41` exactly `run_one(instance_path, config, out_dir=DEFAULT_OUT_DIR, *, resume=False, dry_run=False)`; 6 pre-existing tests unmodified and green |
| R2 instance validation parity | PASS | `read_instance` at `runner.py:48` before the dry-run branch; test `test_dry_run_validation_matches_real_run` asserts same exception type + message (`"Instance is empty (n = 0 or no edges)."`); missing file → `FileNotFoundError` both modes; malformed JSON → identical `json.JSONDecodeError` both modes |
| R3 static method check, no `registry.resolve()` | PASS | `runner.py:52` is exactly `config.method not in METHODS and ":" not in config.method`; error message `runner.py:53-56` is the same wording as `registry.py:37-40` incl. `sorted(METHODS)`; test `test_dry_run_method_check_imports_nothing` proves dotted path passes, `nope` raises, and `set(sys.modules) - before == set()` after `platform.node()` pre-warm |
| R4 `make_run_id` untouched, deterministic | PASS | dry-run calls `make_run_id(instance, config)` (`runner.py:57`); `src/runner/schema.py` unmodified (not in `git status`); tests assert `__tl30__mlNone` / `__tl1800.0__mlNone` / `__tlNone__mlNone` renderings and edge-content independence (`test_dry_run_run_id_ignores_edge_content`) |
| R5 resume state, no dir creation, no content read | PASS | `runner.py:58-59,71`; garbage-bytes file at `out_file` with `resume=True` → `status == "DRY_RUN"`, file bytes unchanged (`test_dry_run_resume_reports_without_parsing_garbage`) |
| R6 budget formula, no hardcoded grace | PASS | `runner.py:60-63` uses `KILL_GRACE_SECONDS`; monkeypatch to `7.5` → `hard_limit=107.5` for `time_limit=100.0`; `time_limit=None` → `None`; `n`/`m` from post-dedup instance (`test_dry_run_duplicate_edges_dedup`: `m == 3` after `(0,1)/(1,0)` dedup) |
| R7 no side effects | PASS | dry-run returns before `mkdir`/`TemporaryDirectory`/`subprocess.run`; tests: `test_dry_run_writes_nothing`, `test_dry_run_preexisting_dir_untouched` (size+mtime unchanged), `test_dry_run_does_not_enter_tempdir`, `test_dry_run_spawns_no_worker` (recorder asserts no worker-pattern call; `git describe` permitted and present) |
| R8 record shape | PASS | `build_record(instance, config, None, wall_time=<measured>, status_override="DRY_RUN")` + one added key `dry_run` (`runner.py:64-75`); `solver_label(config, None)` = `config.sat_solver or config.method`; `schema.py` gives `error=None`, `metadata={}`, `solution=None`; shape test checks every `RUN_FIELDS` key + the 4 extras, `dry_run` is a plain dict with exactly the 6 Data-model keys |
| R9 wall_time real, no sleeps | PASS | `perf_counter()` around dry-run steps only (`runner.py:51,65`); no sleep anywhere in the branch |
| R10 no extra validation | PASS | `Config(method="sat", time_limit=0)` dry-runs, `hard_limit == 0 + KILL_GRACE_SECONDS` (covered in grace test, `rec_zero`) |

### B. CLI `python -m src.runner --dry-run`

| Rule | Verdict | Evidence |
|---|---|---|
| R11 flag + unchanged default path | PASS | `__main__.py:80-81` `store_true`; Config built identically (`:84-88`); real-run path `:102-106` untouched; `test_cli_without_dry_run_unchanged` asserts `DRY_RUN` absent and result line + file written as before |
| R12 exact 5 lines + rendering rules | PASS | `_render` (`:12-18`): `None → none`, `bool → true/false`, else `str(value)`; `_print_dry_run` (`:36-64`) emits lines 1–5 in R12 order; `memory_limit_enforced=false` is a fixed literal (`:57`); test compares `out.splitlines()` against computed `make_run_id` (not the R12 example), out_file split prefix/Path/tail, `err == ""`, nothing written under `--out` |
| R13 exit codes + cp1252-safe stderr | PASS | try/except `(ValueError, OSError)` only (`:95`), single stderr line `DRY_RUN ERROR: <msg>`, no traceback; `_make_stderr_lossy_safe` (`:32-33`) → `reconfigure(errors="replace")` when available; tests run subprocess with `PYTHONIOENCODING=cp1252` for both failure classes (empty graph, unknown method) and assert no `UnicodeEncodeError`, exit 2, and the Vietnamese `không có trong registry` survives lossily; success path exit 0 with empty stderr |
| R14 composes with `--resume` | PASS | `resume=a.resume` forwarded (`:93`); CLI test pre-creates `out_file`, asserts `exists=true resume_would_skip=true`, exit 0; argparse does not reject the combination |

### C. W2 checkboxes

| Rule | Verdict | Evidence |
|---|---|---|
| R15 tick rule + evidence pointers + two exceptions only | PASS | `git diff -U0` checkbox lines: 08 = 4×`[ ]→[x]` text-unchanged; 09 = boxes 1/3/4 ticked, box 2 stays `[ ]` with suffix `*(N/A — xem Closure evidence)*` and unchanged text; 10 = 6; 11 = 4; 12 = 5; 13 = 3; 14 = 3; 15 box 2 = stale 4-line parenthetical replaced by the §4.1/§3 pointer (exception b). Every `## Closure evidence (2026-11-03)` section present with per-box pointers |
| R16 unticked boxes keep reason, no box deleted/reordered | PASS | unticked set is exactly `{09 box 2}`; its Closure evidence entry gives the permanent-N/A reason with pointers (`PYSAT_KISSAT_FAMILIES`, `_validate_solver` `src/sat/solve.py:424`, tests, `docs/sat_tooling.md`, `14-sat-methodology.md` §3.6). All other boxes in same order as before |
| R17 expected per-file outcome | PASS | matches file-by-file: 08 all 4 (incl. verified-negative box 4 via `SUPPORTED_AMO_ENCODINGS`); 09 boxes 1/3/4; 10 all 6; 11 all 4; 12 all 5 (Kissat column N/A reason in 09's evidence, not inline); 13 all 3 with box 3 citing all five artifacts (GH #20, GH #42, PR #48, `13-review-p1-formulation.md`, `16-w2-acceptance.md`); 14 all 3; 15 box 2 ticked with pointer |
| R18 Status/Owner/Blocked unchanged, Vietnamese prose | PASS | diff filter over all 8 ticket files for `Tuần/Owner/Status/Blocked` lines → zero hits; Closure evidence prose is Vietnamese, technical identifiers verbatim; fixed heading and fixed suffix appear exactly as specified |

### D. M1 evidence doc

| Rule | Verdict | Evidence |
|---|---|---|
| R19 only §4.1 + one §6 bullet | PASS | `git diff -- docs/handoff/w2-sat/15-m1-gate-evidence.md` contains additions only (no removed lines): the whole §4.1 block and the single added §6 line `Đã hoàn tất 2026-11-03 — xem mục 4.1.` under the existing "Việc còn mở của gate" bullet; §4's "CHƯA thực hiện được" conclusion left in place as a dated historical record |
| R20 §4.1 content | PASS | titled `### 4.1 Cập nhật 2026-11-03: --dry-run đã có trên runner`; verbatim command names `.venv\Scripts\python.exe` and passes `--out results/raw`; verbatim stdout fenced block; reading covers run_id/`make_run_id`, `hard_limit = 1800.0 + 30.0 = 1830.0`, `memory_limit_enforced=false`, `n=4 m=3`, `exists/resume_would_skip`; explicit scope statement that M1 stays NO-GO. **Live replay this session reproduced the recorded stdout byte-identically** with exit 0 and a clean `results/raw` — the honesty rule ("không viết tay") is independently confirmed |

## Acceptance criteria A1–A11

| Criterion | Verdict | Evidence |
|---|---|---|
| A1 record shape | PASS | `test_dry_run_record_shape` (all RUN_FIELDS + 4 extras, `DRY_RUN`, Nones, `{}`, dict `dry_run` with exactly the 6 keys) |
| A2 no side effects | PASS | `test_dry_run_writes_nothing` + `test_dry_run_preexisting_dir_untouched` |
| A3 budget | PASS | `test_dry_run_hard_limit_follows_grace_constant` (incl. monkeypatch `7.5` and `None`) |
| A4 run_id parity + no collision | PASS | `test_dry_run_run_id_matches_real_run` (dry == real == `make_run_id`; real file written; dry dir absent) |
| A5 resume reporting | PASS | `test_dry_run_resume_reports_without_parsing_garbage` + `test_dry_run_resume_absent_file` |
| A6 no worker spawn | PASS | `test_dry_run_spawns_no_worker` |
| A7 validation parity | PASS | `test_dry_run_validation_matches_real_run` + `test_dry_run_validation_missing_and_malformed` |
| A8 method check + import snapshot | PASS | `test_dry_run_method_check_imports_nothing` (`sys.modules` delta empty after `platform.node()` pre-warm; no `src.exact.*`; dotted target absent) |
| A9 CLI success | PASS | `test_cli_dry_run_prints_five_lines` (computed run_id, `--out tmp_path`, split out_file compare, `stderr == ""`, nothing written) |
| A10 CLI failure | PASS | `test_cli_dry_run_failure_exits_2_cp1252_safe` + `test_cli_dry_run_unknown_method_exits_2` (both cp1252 and utf-8, no traceback) |
| A11 regression | PASS | Full suite this session: **538 passed, 3 skipped in 18.37s**; 3 skips = CPLEX CP engine (expected); 6 pre-existing runner tests unmodified |

## Doc criteria D1–D6

| Criterion | Verdict | Evidence |
|---|---|---|
| D1 tick ⇒ pointer | PASS with observation O2 | every box ticked by this task has a Closure evidence pointer; see O2 for ticket 15 boxes 1/3/4 |
| D2 unticked ⇒ reason | PASS | only 09 box 2 unticked, reason present; 13 box 3 resolved and ticked as required |
| D3 evidence doc diff scoped | PASS | diff shows additions only: §4.1 + one §6 line; §1–§3, §4 original, §5, §6 decision untouched; output parses against R12 and is self-consistent with the command (replayed live) |
| D4 ticket 15 item 2 | PASS | `[x]`, stale parenthetical replaced by §4.1/§3 pointer; `Kết quả (2026-10-20): **NO-GO Bonus**` lines and everything below unchanged (no `-` lines in the file diff besides the replaced parenthetical) |
| D5 Status/Owner/Blocked unchanged | PASS | zero diff hits on those lines across all 8 files |
| D6 no out-of-scope changes | PASS | `git status --porcelain`: exactly the Scope list (8 ticket files, `15-m1-gate-evidence.md`, `src/runner/__main__.py`, `src/runner/runner.py`, `tests/runner/test_runner.py`) + untracked `docs/handoff/w2-dry-run/` (allowed). No `docs/handoff/sat-g1/*` dirt, no `results/raw` changes, no `CONTRACT.md`, no `src/sat|exact|common` changes |

## Edge cases checked

- out_dir absent → `exists=false`, dir not created (A2). Verified.
- out_file exists, no `--resume` → `exists=true resume_would_skip=false`, content unread (A5 second half). Verified.
- out_file corrupt + `--resume` → `DRY_RUN` record returned, garbage bytes intact (A5). Verified.
- Missing / malformed / empty-graph instance → same exception class as real run; CLI exit 2 with `DRY_RUN ERROR:` (A7/A10). Verified.
- Duplicate `(u,v)/(v,u)` edges → `m` post-dedup, run_id unaffected (A4/edge test). Verified.
- `time_limit=None` → `hard_limit=none`; `time_limit=0` accepted, formula still applied (A3/R10). Verified.
- Unknown method / nonexistent dotted path → `ValueError` vs pass respectively; real-run divergence documented (R3, dev-notes §4). Verified.
- `KILL_GRACE_SECONDS` monkeypatched → `hard_limit` follows (A3). Verified.
- `--dry-run` without `--instance` → argparse exit 2 (pre-existing; not re-tested, unchanged code path).
- Non-ASCII `instance.id` / non-ASCII `--out` under cp1252 → exit 0, 5 lines, lossy rendering, no crash (`test_dry_run_non_ascii_id`, `test_cli_dry_run_non_ascii_out_cp1252_safe`; matches qa-staging B1). Verified.

## Contradictions

- **D1 vs R17 (ticket 15 boxes 1/3/4)**: D1 literally requires a Closure-evidence pointer for *every* ticked box, but ticket 15's section documents only box 2 — the only box this task ticked; boxes 1/3/4 were already `[x]` before this task (R17 states this explicitly). Specific rule (R17) wins over general rule (D1); box 1/3/4 evidence exists in `15-m1-gate-evidence.md` §1 and §6. **Resolved, non-blocking.** Recorded so a future auditor does not read the section as incomplete by accident.
- All other requirement-internal contradictions (C1–C7) were resolved at requirements level and the implementation follows the resolutions: `DRY_RUN` is runner-level only and never persisted; `memory_limit_enforced=false` is a fixed literal; no `registry.resolve()` call; dry-run fail-fast vs real-run `ERR` divergence is documented; every tick maps to named repo evidence; `make_run_id` untouched; checkbox edits limited to the two declared exceptions. `none` outstanding.

## Open questions

- Requirements open question "which instance file for §4.1" → resolved in practice: `benchmark/toy/path4.json`, canonical SAT config, exactly the R20 recommended shape.
- `experiments/pilot_rq1.py` / `pilot_rq2.py` gaining `--dry-run` remains out of scope (requirements Scope + qa-staging "could not check"); flagging only if the customer wants it later. | otherwise `none`.

## Non-blocking observations

- **O1 — `wall_time` excludes instance-read time** (`src/runner/runner.py:51` `start = perf_counter()` after `read_instance` at `:48`). R8's "measured elapsed of the dry-run steps" is ambiguous about whether `read_instance` counts; qa-staging already logged this as low-severity with a fix hint. `wall_time` stays well under the R9 `5.0` bound. Accept as documented; revisit only if `api-contract.md` §1.2 wording needs tightening.
- **O2 — ticket 15 Closure evidence covers only box 2** (see Contradictions above). Accept as the R17-intended shape.
- **O3 — qa-staging B4 probe (`--out` pointing at an existing file / `Z:\nope`) has no automated test**, manual probe only. The underlying behavior (`exists` on a file-path `--out`, nonexistent drive) is low-risk read-only logic; acceptable.

## Out of scope (confirmed untouched)

`CONTRACT.md`; `src/runner/worker.py`; `src/sat/**`, `src/exact/**`, `src/common/**` (except none touched); memory-limit enforcement (still not a hard cap, correctly reported as `memory_limit_enforced=false`); GitHub issue state sync; CNF-size/runtime estimation in dry-run; M1 GO/NO-GO re-decision (NO-GO with unchanged reasons and cut list, byte-identical).

## Sign-off

BA UAT: **PASS**. The implementation, tests, checkbox closures and M1 evidence
update satisfy R1–R20, A1–A11, D1–D6 as written. Ship.
