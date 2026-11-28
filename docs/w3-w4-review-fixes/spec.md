# Technical Specification — w3-w4-review-fixes

> **Superseded (2026-11-28):** the `allow_unbounded_memory` escape hatch described below was
> replaced when `main` merged the canonical `memory_limit=12.0` GiB default. The current
> contract is in `docs/canonical_sat_config.md`; keep this file as the historical record of
> blocker B3.

## Architecture Overview & Tech Stack

Fixes stay inside existing modules; no new dependencies or files beyond this spec.
Three pure-Python modules change: `src/sat/solve.py` (config validation), `src/sat/triage.py`
(missing-instance precedence), `experiments/analyze_rq1_rq2.py` (G3 pending semantics + RQ1/RQ2
axis slices). Reuse `src.common.models.Config`, `src.sat.triage.TriageReport`,
`experiments.pilot_common.REPO_ROOT`, and the existing `csv.DictReader` pipeline. Solver outcomes
from `solve_sat` are untouched; only config validation, triage classification, analysis slicing,
and docs change.

## Non-Functional Requirements (NFRs)

- Performance/Scalability: G3/RQ1/RQ2 computed on the two committed CSVs (`results/pilot_rq1.csv` =
  40 rows, `results/pilot_rq2.csv` = 40 rows). Only two new pure-Python row filters added; no new
  per-row parsing beyond `normalize_row`. Same order of magnitude as today.
- Security/Auth: none (local analysis/reporting tool). Validation is at the config trust boundary:
  `canonical_sat_config` rejects non-positive / bool / non-numeric `memory_limit`; explicit
  `allow_unbounded_memory=True` is the only path to `memory_limit=None`.
- Reliability/Concurrency: no shared mutable state; report generation is single-process,
  deterministic for a fixed input set. No writes outside the `--out` target path (report) and
  committed CSVs remain read-only inputs.
- Reproducibility: regenerated `docs/w4-sat/23-rq1-rq2-draft-analysis.md` must match a fresh
  `python -m experiments.analyze_rq1_rq2` run byte-for-byte given the same inputs; no hand-edited
  numbers.

---

## FR-3 — canonical config memory validation (`src/sat/solve.py`)

### Data Model / Schema Changes

`Config.memory_limit` (`src/common/models.py:34`) stays `float | None`. No schema change.
`CANONICAL_SAT_CONFIG` (`src/sat/solve.py:40-51`) attributes stay frozen verbatim
(`abp_encoding="order"`, `amo_encoding="pairwise"`, `sat_solver="glucose4"`,
`search_mode="multi"`, `symmetry=False`, `warm_start=False`, `seed=0`, `time_limit=1800.0`,
`memory_limit=None`).

Migration / Backfill: `none`

### Function Contract — `src/sat/solve.py::canonical_sat_config`

`canonical_sat_config(*, time_limit: float | None = 1800.0, memory_limit: float | None = None, sat_solver: str = "glucose4", allow_unbounded_memory: bool = False) -> Config`

- Auth: n/a.
- Validation order (runs before constructing the returned `Config`):
  1. If `not allow_unbounded_memory`: `memory_limit` must be a finite `int | float` (excluding
     `bool`) with `memory_limit > 0`. Raise `ValueError` if `memory_limit is None` or invalid.
  2. If `allow_unbounded_memory=True` and `memory_limit is None`: return a `Config` with
     `memory_limit=None` (dev/unit-test only).
  3. If `allow_unbounded_memory=True` and `memory_limit` is provided (not `None`): still validate
     `> 0` and non-`bool`; raise `ValueError` on invalid.
- Error message must contain the literal `memory_limit` (satisfies AC `match="memory_limit"`).
  Recommended: `f"memory_limit phải là số hữu hạn > 0 (int|float, không phải bool): {memory_limit!r}."`
- Output: `Config` copy; every non-`memory_limit`/`time_limit`/`sat_solver` field carried from
  `CANONICAL_SAT_CONFIG` exactly as today (`method="sat"`, frozen encodings/axes/`seed`).
- `CANONICAL_SAT_CONFIG` constant and `src/sat/__init__.py` exports unchanged.

### Module & File Plan

- `src/sat/solve.py` — modify — add `allow_unbounded_memory: bool = False` param + validation block to `canonical_sat_config`; keep `CANONICAL_SAT_CONFIG` verbatim.

---

## FR-4 — triage missing instance precedence (`src/sat/triage.py`)

### Data Model / Schema Changes

`TriageReport` unchanged. `DEFAULT_BENCHMARK_DIRS` (`src/sat/triage.py:40-46`) replaces the 5th
entry `REPO_ROOT / "docs" / "handoff" / "sat-g1" / "instances"` with
`REPO_ROOT / "docs" / "sat-g1" / "instances"`.

Migration / Backfill: `none`

### Function Contract — `src/sat/triage.py::inspect_record`

`inspect_record(record: dict[str, Any], *, instance: Instance | None = None, search_dirs: Sequence[str | Path] = DEFAULT_BENCHMARK_DIRS) -> TriageReport`

- Order of checks (strict):
  1. Invalid `status` → `CODE_BUG` (unchanged, `src/sat/triage.py:129-139`).
  2. NEW: if `instance is None and isinstance(instance_id, str)`, attempt
     `find_instance(instance_id, search_dirs=search_dirs)` (unreadable file still raises →
     `ENV_ERROR`, unchanged, `src/sat/triage.py:144-154`). **Immediately after** this attempt, if
     `instance is None` (either `instance_id` is not a non-empty `str`, or `find_instance` returned
     `None`), return:

     ```python
     TriageReport(
         run_id=run_id,
         instance_id=instance_id if isinstance(instance_id, str) else None,
         status=status,
         category="ENV_ERROR",
         is_anomaly=True,
         recorded_lb=lb,
         recorded_ub=ub,
         reasons=[f"Thiếu file instance '{instance_id}' để đối chiếu."],
     )
     ```

     This runs BEFORE any `raw_sol`/`OPT`/`FEAS`/`MO`/`ERR`/`TO` classification.
  3. All existing classification branches unchanged downstream.
- Effect: `status="TO"` + `solution=None` + missing instance → `ENV_ERROR` (not
  `SOLVER_BEHAVIOR`); `status="ERR"` + `solution=None` + missing instance → `ENV_ERROR` (not
  `CODE_BUG`); `status="MO"` unchanged classification; explicit `instance=` argument path
  (test path) skips the lookup and is unchanged.
- The existing `raw_sol is not None` + `instance is None` branch (`src/sat/triage.py:173-183`) is
  subsumed by step 2 and becomes dead; remove it or leave it unreachable (recommend remove to
  avoid duplicate `ENV_ERROR` reasons).

### Module & File Plan

- `src/sat/triage.py` — modify — fix `DEFAULT_BENCHMARK_DIRS` entry; insert missing-instance `ENV_ERROR` early-return after the `find_instance` try/except.

---

## FR-1 + FR-2 + B5 — analysis gating & slices (`experiments/analyze_rq1_rq2.py`)

### Data Model / Schema Changes

`G3GateSummary` dataclass (`experiments/analyze_rq1_rq2.py:135-145`) changes field types:

- `expected_runs: int | None` (was `int`; `None` means "no frozen plan supplied").
- `completion_ratio: float | None` (`None` when `expected_runs is None`).
- `passed_completion: bool` (explicitly `False` when `expected_runs is None`).
- `passed_gate: bool` (`False` when pending), and a new rendering keyword `gate_status: str`
  (`"PASS" | "FAIL" | "PENDING"`) or derive in render; spec: add `gate_status: str` field.

`normalize_row` (`experiments/analyze_rq1_rq2.py:58-84`) adds three keys: `search_mode`,
`symmetry`, `warm_start`, derived per row:

- If CSV cell `raw.get("search_mode")` present (non-empty), use `str(...)`; else fallback from
  `run_id` token: `"multi"` if `"__multi__"` in `run_id`, else `""`. Pilot CSVs have no
  `search_mode` column; their `run_id` carries `__multi__`.
- `symmetry`: CSV cell `raw.get("symmetry")` if present else `True` if `"__sym1__"` in `run_id`
  else `False` (pilot `run_id` has `__sym0__`).
- `warm_start`: CSV cell `raw.get("warm_start")` if present else `True` if `"__ws1__"` in `run_id`
  else `False` (pilot `run_id` has `__ws0__`).
- Default when neither column nor token is present: `("", False, False)` — but the RQ1/RQ2
  control filters accept `search_mode in ("", "multi")`, so `""` still passes; `symmetry=False`,
  `warm_start=False` pass.

Migration / Backfill: `none` (CSVs unmodified).

### Function Contracts

#### `summarize_rq1(rows, *, default_time_limit=60.0, solver: str | None = "cadical195")`

- Auth: n/a.
- Filter: `sat_rows = [r for r in rows if r.get("method", "sat") == "sat" and (solver is None or r["solver"] == solver) and r.get("search_mode", "") in ("", "multi") and r.get("symmetry") is False and r.get("warm_start") is False]`.
  Grouping/aggregation unchanged (line 168 onward).
- Rationale: pilot `pilot_rq1.csv` is entirely `cadical195`, `multi`, `sym0`, `ws0` → still 4
  `(abp, amo)` rows (BR-3, AC FR-2).

#### `find_smaller_cnf_slower_solve_cases(rows)`

- Apply the same RQ1 filter **before** computing `by_inst` (`experiments/analyze_rq1_rq2.py:206-213`),
  so counter-example pairs come only from the filtered single-solver slice. Signature unchanged.

#### `summarize_rq2(rows, *, default_time_limit=60.0, abp_encoding: str | None = "order", amo_encoding: str | None = "pairwise")`

- Filter: `sat_rows = [r for r in rows if r.get("method", "sat") == "sat" and (abp_encoding is None or r["abp_encoding"] == abp_encoding) and (amo_encoding is None or r["amo_encoding"] == amo_encoding) and r.get("search_mode", "") in ("", "multi") and r.get("symmetry") is False and r.get("warm_start") is False]`.
  Grouping unchanged.
- Pilot `pilot_rq2.csv` is entirely `order/pairwise`, `multi`, `sym0`, `ws0` → still 4 solver rows
  (`minisat22, glucose4, glucose42, cadical195`) (AC FR-2). Excludes `order/seqcounter` duplicate
  rows from combined `runs.csv` (RFC contradiction, `requirements.md:224`).

#### `evaluate_g3_gate(completed_runs: int, expected_runs: int | None, triage_reports: Sequence[TriageReport], *, threshold: float = G3_THRESHOLD) -> G3GateSummary`

- If `expected_runs is None`: do NOT raise, do NOT fallback to `completed_runs`; return summary
  with `expected_runs=None`, `completion_ratio=None`, `passed_completion=False`,
  `passed_gate=False`, `gate_status="PENDING"`, `total_triaged`/`anomalies_count`/
  `unclassified_anomalies`/`code_bugs_count` still computed from `triage_reports`.
- Else: `if isinstance(expected_runs, bool) or expected_runs <= 0: raise ValueError("expected_runs phải > 0.")`; compute `ratio = completed_runs / expected_runs`; `passed_completion = ratio >= threshold`; `passed_gate = passed_completion and len(unclassified) == 0 and len(code_bugs) == 0`; `gate_status = "PASS" if passed_gate else "FAIL"`; round `completion_ratio=round(ratio, 4)` as today.

#### `render_markdown_report(rq1_rows, rq2_rows, triage_reports, *, expected_core_runs: int | None = None, source_note: str = "", rq1_solver: str | None = "cadical195", rq2_abp_encoding: str | None = "order", rq2_amo_encoding: str | None = "pairwise") -> str`

- Replace `render_markdown_report`
  - `rq1_summaries = summarize_rq1(rq1_rows, solver=rq1_solver)`
  - `rq2_summaries = summarize_rq2(rq2_rows, abp_encoding=rq2_abp_encoding, amo_encoding=rq2_amo_encoding)`
  - `counterexamples = find_smaller_cnf_slower_solve_cases(rq1_rows)` (filter internal).
  - G3: remove `expected_count = expected_core_runs or max(completed_count, 1)`; call
    `evaluate_g3_gate(completed_count, expected_core_runs, triage_reports)` directly.
  - `completed_count = len({r["run_id"] for r in rq1_rows} | {r["run_id"] for r in rq2_rows})`
    (unchanged computation, but now unused for fallback).
- Section 2.2 per-instance table: iterate only the same filtered `rq2_rows` slice. Add an internal
  helper or inline filter before the `by_inst_solver` loop so `by_inst_solver` is built from
  `rq2_rows` filtered by `(rq2_abp_encoding, rq2_amo_encoding)` + control axes (`search_mode in
  ("", "multi")`, `symmetry is False`, `warm_start is False`). `solvers` list stays derived from
  `rq2_summaries`.
- §3 G3 section: when `g3.expected_runs is None`, render completion line as
  `**PENDING (chưa truyền --expected-runs từ kế hoạch đã khóa)**` and gate conclusion as
  `**PENDING**`; do NOT print `100.0%`. When `expected_runs is not None`, render
  `{completed_runs} / {expected_runs} ({completion_ratio*100:.1f}%, yêu cầu G3 ≥ 80.0%)` and
  conclusion `g3.gate_status` (`PASS`/`FAIL`) as before.

### CLI (module `main`)

- Add `--rq1-solver` (`default="cadical195"`), `--rq2-abp-encoding` (`default="order"`),
  `--rq2-amo-encoding` (`default="pairwise"`). Wire to `render_markdown_report(..., rq1_solver=args.rq1_solver, rq2_abp_encoding=args.rq2_abp_encoding, rq2_amo_encoding=args.rq2_amo_encoding)`. `--expected-runs` unchanged. `--out` default updated to `DEFAULT_REPORT_PATH`.
- `DEFAULT_REPORT_PATH` (`experiments/analyze_rq1_rq2.py:40-42`) → `REPO_ROOT / "docs" / "w4-sat" / "23-rq1-rq2-draft-analysis.md"`.
- Module docstring (`line 17`) → `python -m experiments.analyze_rq1_rq2 --out docs/w4-sat/23-rq1-rq2-draft-analysis.md`.

### Module & File Plan

- `experiments/analyze_rq1_rq2.py` — modify — `DEFAULT_REPORT_PATH`+docstring; `normalize_row` axis extraction; RQ1/RQ2 filters; `G3GateSummary` fields; `evaluate_g3_gate` `None` semantics; `render_markdown_report` pending+slice+2.2 filter; CLI flags.

---

## Test Plan (exact add/update)

### `tests/sat/test_solve.py`

Update `test_canonical_sat_config_emits_no_warning_and_matches_oracle` (line 360) — the sole prod
caller `canonical_sat_config(time_limit=10.0)` must now pass an explicit cap or the escape hatch.

Add:

1. `test_canonical_sat_config_requires_positive_memory_limit` — `pytest.raises(ValueError, match="memory_limit")` for each:
   `canonical_sat_config(time_limit=10.0)`, `canonical_sat_config(memory_limit=0.0)`,
   `canonical_sat_config(memory_limit=-1.0)`, `canonical_sat_config(memory_limit=True)`,
   `canonical_sat_config(memory_limit="12288")`.
2. `test_canonical_sat_config_accepts_explicit_cap` — `cfg = canonical_sat_config(memory_limit=12288.0)`; assert `cfg.memory_limit == 12288.0` and the frozen fields (`abp_encoding=="order"`, `amo_encoding=="pairwise"`, `sat_solver=="glucose4"`, `search_mode=="multi"`, `symmetry is False`, `warm_start is False`, `seed==0`) still hold; assert `CANONICAL_SAT_CONFIG.memory_limit is None` (constant unchanged).
3. `test_canonical_sat_config_unbounded_escape_hatch` — `cfg = canonical_sat_config(allow_unbounded_memory=True)`; assert `cfg.memory_limit is None`.
4. `test_canonical_sat_config_unbounded_still_validates_provided_limit` — `pytest.raises(ValueError, match="memory_limit")` for `canonical_sat_config(memory_limit=True, allow_unbounded_memory=True)` and `canonical_sat_config(memory_limit=0.0, allow_unbounded_memory=True)`; and `canonical_sat_config(memory_limit=12288.0, allow_unbounded_memory=True).memory_limit == 12288.0`.
5. Update existing oracle test: `cfg = canonical_sat_config(time_limit=10.0, memory_limit=12288.0)` (satisfies FR-3 without touching solver behavior).

### `tests/sat/test_triage.py`

Add (using `_valid_path4_record()` helper, no `instance=` arg, empty `search_dirs` so lookup fails):

1. `test_inspect_record_missing_instance_is_env_error_before_classification` — record
   `{"run_id": "...", "instance": "missing-1", "status": "TO", "solution": None, "lb": None, "ub": None}` with `search_dirs=()` → assert `category == "ENV_ERROR"`, `is_anomaly is True`, and `any("missing-1" in r for r in report.reasons)`.
2. `test_inspect_record_err_missing_instance_is_env_error` — same but `status="ERR"` → `ENV_ERROR` (not `CODE_BUG`), reason mentions `missing-1`.
3. `test_inspect_record_mo_missing_instance_still_env_error_with_reason` — `status="MO"` → `ENV_ERROR`, reason naming missing instance.
4. `test_inspect_record_resolvable_instance_keeps_solver_behavior` — write an instance `path4.json` in a `tmp_path` dir, `search_dirs=(that_dir,)`, `status="TO"`, `solution=None` → `category == "SOLVER_BEHAVIOR"` (regression: precedence only fires on miss).
5. `test_default_benchmark_dirs_points_to_docs_sat_g1` — import `DEFAULT_BENCHMARK_DIRS`; assert `REPO_ROOT / "docs" / "sat-g1" / "instances" in DEFAULT_BENCHMARK_DIRS` and the stale `docs/handoff/sat-g1/instances` path is NOT in it.

### `tests/experiments/test_analyze_rq1_rq2.py`

1. Extend `test_summarize_rq1_and_smaller_cnf_slower_solve` and add
   `test_summarize_rq1_filters_solver_and_control_axes` — build a combined CSV (or dict rows) with
   2 solvers × symmetric/warm axes; assert every `n_runs` counts only `cadical195`/control-axis
   rows, and `summarize_rq1(rows, solver="glucose4")` returns glucose4-only groups.
2. Extend `test_summarize_rq2_ranks_by_coverage_and_par2` and add
   `test_summarize_rq2_filters_encoding_pair` — combined rows with `order/seqcounter` and multi
   pairs; assert `summarize_rq2` default counts only `order/pairwise` control rows
   (`order/seqcounter` excluded); assert configurable `amo_encoding="seqcounter"` swaps the slice.
3. `test_evaluate_g3_gate_none_expected_is_pending` — `g = evaluate_g3_gate(70, None, ok_triage)`; assert `g.expected_runs is None`, `g.completion_ratio is None`, `g.passed_completion is False`, `g.passed_gate is False`, `g.gate_status == "PENDING"`; and `completed_count == 0, expected=None` also `PENDING` (no division by zero).
4. `test_evaluate_g3_gate_zero_expected_still_raises` — `pytest.raises(ValueError)` for `evaluate_g3_gate(0, 0, ok_triage)` and `evaluate_g3_gate(0, True, ok_triage)`.
5. `test_render_markdown_report_pending_without_expected_runs` — render with no `expected_core_runs`; assert text contains `PENDING` for G3 completion and conclusion, and does NOT contain `100.0%`.
6. Extend `test_analyze_cli_supports_single_runs_csv` — assert new flags parse: pass `--rq1-solver glucose4 --rq2-abp-encoding order --rq2-amo-encoding pairwise` and rc == 0.
7. Add `test_default_report_path_resolves` — assert `DEFAULT_REPORT_PATH == REPO_ROOT / "docs" / "w4-sat" / "23-rq1-rq2-draft-analysis.md"`.

---

## Documentation Updates (FR-5)

All evidence links must resolve in-repo at the closing commit; `grep docs/handoff/` must return no
match in the five touched doc groups below.

1. `docs/abp-sat-encoding/issues/W3/16-pilot-rq1.md` — mark boxes `[x]` with evidence:
   `results/pilot_rq1.csv`, `docs/canonical_sat_config.md`.
2. `docs/abp-sat-encoding/issues/W3/17-pilot-rq2.md` — `[x]`, evidence `results/pilot_rq2.csv`.
3. `docs/abp-sat-encoding/issues/W3/18-canonical-config-proposal.md` — `[x]`, evidence
   `docs/canonical_sat_config.md` + `src/sat/solve.py` `CANONICAL_SAT_CONFIG`.
4. `docs/abp-sat-encoding/issues/W3/19-correctness-suite-appendix-draft.md` — `[x]`, evidence
   `docs/technical_appendix_draft.md` + pytest count.
5. `docs/abp-sat-encoding/issues/W3/20-bonus-sat-prototype.md` — `[x]` via recorded M1 NO-GO
   rationale only (condition of ticket 15), consistent with
   `docs/abp-sat-encoding/issues/W2/15-m1-gate-bonus-decision.md`; no prototype written.
6. `docs/abp-sat-encoding/issues/W4/21-m2-freeze-v1.md` — sync pytest count to the same string as
   `docs/w4-sat/21-m2-freeze-v1.md` (re-run full suite at closing commit; `requirements.md:218-221`
   contradiction resolved by recording the actual fresh count in both).
7. `docs/abp-sat-encoding/issues/W4/23-rq1-rq2-draft-analysis.md` — replace
   `docs/handoff/w4-sat/23-...` with `docs/w4-sat/23-rq1-rq2-draft-analysis.md`.
8. `docs/w4-sat/21-m2-freeze-v1.md` — §4 remove stale `docs/handoff/w4-sat/23-...` reference →
   `docs/w4-sat/23-rq1-rq2-draft-analysis.md`; sync pytest count; §12 freeze-gate wording: tag
   `v1.0` only after all freeze gates (dataset, host, solver, resource enforcement, cross-review,
   evidence) pass; re-check cross-refs to `docs/sat_spec.md`, `docs/w2-sat/14-sat-methodology.md`,
   `docs/technical_appendix_draft.md`.
9. `docs/w4-sat/23-rq1-rq2-draft-analysis.md` — regenerate via
   `python -m experiments.analyze_rq1_rq2` after FR-1/FR-2 land (no `--expected-runs` → G3
   `PENDING`).
10. `docs/canonical_sat_config.md` — `memory_limit` row no longer presents plain `null` as the
    official value: state official runs must carry an explicit cap (candidate `12.0` GiB =
    `12288.0` MB from P1's protocol), in-process MO is not enforced by the solver (runner-layer
    Protocol §6.3), final number is a team decision (not P2's).

---

## Technical Risks & Rollout Notes

- `canonical_sat_config()` now raises by default (no `memory_limit`); only caller is
  `tests/sat/test_solve.py:361` (updated per test plan) plus docs examples. No production break.
- `G3GateSummary.completion_ratio` becomes `float | None`; renderer must branch on `None` before
  the `* 100` format, or a `TypeError` occurs. Add the branch in §3 rendering.
- `normalize_row` fallback relies on `run_id` tokens (`__multi__`, `__sym0__`, `__ws0__`). Pilot
  CSVs carry no `search_mode`/`symmetry`/`warm_start` columns but tokens are present (verified in
  `results/pilot_rq1.csv`/`pilot_rq2.csv` line 2). Combined `runs.csv` from P3 has explicit
  columns per `src/runner/schema.py:15-22`, so explicit-column path wins.
- Default `time_limit` in `normalize_row` is `60.0` (pilot); combined `runs.csv` carries explicit
  `time_limit`. Unchanged.
- Doc pytest-count sync depends on re-running the full suite at the closing commit; do not hand-edit
  the count (must equal actual output `N passed, M skipped`).
- `runtime memory cap` value (`12288.0`) is a candidate only; final value is P1/P3 decision —
  out of P2 scope.