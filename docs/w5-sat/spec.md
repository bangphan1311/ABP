# Technical Specification — w5-sat

## Architecture Overview & Tech Stack

Single analysis module `experiments/w5_final_analysis.py` reuses `experiments/analyze_rq1_rq2.py` (slice filters, `summarize_rq1/2`, `find_smaller_cnf_slower_solve_cases`, `normalize_row`, `load_csv_rows`), `experiments/pilot_common.py` (`REPO_ROOT`, `use_utf8_output`), `src/sat/triage.py` (`triage_directory`, `DEFAULT_RAW_DIR`), `src/sat/loader.py::read_instance`, and `src/sat/*` + `src/exact/*` (read-only for consistency checks). No new dependencies, no solver invocations: reads frozen CSVs + `results/raw/*.json` + `benchmark/{validation,large}/*.json`, writes four Markdown deliverables under `docs/w5-sat/`. Frozen inputs stay read-only; nothing under `results/` is written.

## Non-Functional Requirements (NFRs)

- Performance/Scalability: pure data reading over 70 raw JSON + 2 CSVs + 10 instance JSONs; target < 5 s wall-clock per CLI run. No indexing/caching needed at this scale. No solver subprocess is spawned; any import of Ortools/Gurobi/CPLEX is guarded so missing binaries cannot crash analysis (consistency checker inspects AST/source text only, never imports the exact modules).
- Security/Auth: no I/O beyond repo paths given on CLI; no network, no secrets. All paths validated with `Path.is_file()`/`is_dir()`; missing `results/runs.csv` falls back silently per BR-1 and the source note names the exact files used.
- Reliability/Concurrency: single-threaded, deterministic; identical inputs produce byte-identical report numbers (fixed float formatting, sorted iteration order). No writes to `results/`; output files written atomically via `mkdir(parents=True, exist_ok=True)` + `write_text`. Idempotent: rerun overwrites outputs with identical content.

## Data Model / Schema Changes

No DB, no tables. All state derives from two frozen schemas already in the repo:

Entity: `RawRunRecord` (`results/raw/*.json`) — consumed fields: `run_id`, `instance`, `status`, `lb`, `ub`, `gap`, `t_encode`, `t_solve`, `t_total`, `variables`, `clauses`, `peak_memory`, `wall_time`, `metadata.probes[]` (each probe: `k`, `status`, `b`, `t_encode`, `t_solve`, `variables`, `clauses`), `metadata.k_best`, `metadata.k_unsat`, `metadata.unsat_source`.

Entity: `PilotCsvRow` (`results/pilot_rq*.csv`, `results/runs.csv`) — consumed fields per `experiments.analyze_rq1_rq2.normalize_row` (`run_id`, `instance`, `abp_encoding`, `amo_encoding`, `solver`, `status`, `lb`, `ub`, `gap`, times, sizes, `peak_memory`). Control axes `search_mode/symmetry/warm_start` inferred from `run_id` tokens when absent.

Entity: `GraphMeta` (`benchmark/{validation,large}/*.json`) — derived, not stored:

- `n`: `int` (from JSON `n`)
- `m`: `int` = `len(edges)` after loader dedup (`src/sat/loader.py`)
- `density`: `float` = `2m / (n(n-1))`
- `max_degree`: `int` = `max` over vertices of incident-edge count
- `UB`: `int` = `n - max_degree` (trivial upper bound)

Migration / Backfill: `none`.

## API / Interface Contracts

### `python -m experiments.w5_final_analysis [--out-dir DIR] [--runs-csv PATH] [--raw-dir PATH] [--cap-mb 12288.0] [--check-only]`

- Auth: none (local CLI). Exit code `0` on PASS, `1` if consistency checks fail or G4 evidence missing.
- Input: optional flags override defaults `DEFAULT_W5_OUT = REPO_ROOT / "docs" / "w5-sat"`, `DEFAULT_RUNS_CSV = REPO_ROOT / "results" / "runs.csv"`, `DEFAULT_RQ1_CSV`, `DEFAULT_RQ2_CSV`, `DEFAULT_RAW_DIR`.
- Output: writes `docs/w5-sat/24-rq1-final.md`, `25-rq2-final.md`, `26-cross-review-consistency.md`, `27-paper-v09-sat-sections.md`; prints one-line status per artifact + final PASS/FAIL.
- Errors: `FileNotFoundError` when fallback CSVs are missing (`load_csv_rows`); `ValueError` from `triage_directory` when `--raw-dir` is not a directory.

### `load_sources(runs_csv: Path | None, rq1_csv: Path, rq2_csv: Path) -> tuple[list[dict], list[dict], str]`
- Returns `(rq1_rows, rq2_rows, source_note)`. Prefers `runs.csv` (both slices from one file); else pilot CSVs. `source_note` names exact files (BR-1).

### `load_graph_metadata(dirs: Sequence[Path]) -> dict[str, GraphMeta]`
- Keyed by instance id from `benchmark/validation/*.json` + `benchmark/large/*.json`; calls `read_instance`. Missing dir → `ValueError` naming the dir.

### `find_larger_cnf_faster_solve_cases(rows, *, solver="cadical195") -> list[dict]`
- Mirror of `find_smaller_cnf_slower_solve_cases`: groups RQ1 slice per instance, excludes `("order","seqcounter")`, returns every `(larger, smaller)` pair where `larger["clauses"] > smaller["clauses"]` and `larger["t_total"] < smaller["t_total"] - 0.005` and `larger["t_total"] * 1.05 < smaller["t_total"]`. Each item: instance + both configs' `clauses/variables/t_total/status`.

### `cross_size_runtime_inversion(rows, *, abp="order", amo="pairwise") -> list[dict]`
- On RQ2 slice, per solver compares `randconn50-seed20261026` vs `randconn40-seed20261026`; returns items where `n50_t_total < n40_t_total` with both numbers + statuses.

### `project_cnf_growth(n, m, *, abp_encoding, amo_encoding, k: int | None = None) -> dict`
- Pure arithmetic, no CNF build. `k` defaults to `n-1` (worst case).
- `variables`: `n*n` for `pairwise`; `n*(n-1)` for `order`.
- `clauses`: `pairwise`: `2n + 2n*C(n,2) + m*2*Σ_{d=1..k-1} max(0, n-d)`; `order`: `n(n-2) + n*C(n,2) + m*2*Σ_{d=1..k-1} max(0, n-d)`.
- `memory_est_mb` (pairwise only, labeled projection): `clauses * (126.53125 / 255400.0)` — anchor from frozen `randconn50` `pairwise/pairwise`.
- `exceeds_cap`: `bool` = `memory_est_mb > cap_mb` (cap parameterized, default `12288.0`).
- Errors: `ValueError` for `n < 2`, `m < 1`, unknown encoding/amo, or `k` out of `1..n-1`.

### `extract_feas_probe_trajectories(raw_dir, search_dirs) -> list[dict]`
- Iterates `triage_directory(raw_dir)` records + raw JSONs where `status == "FEAS"`; returns per run: `run_id`, `instance`, `lb`, `ub`, `gap`, `k_best`, `k_unsat`, `unsat_source`, and the full `probes` list (each `k/status/b/t_encode/t_solve/variables/clauses`).

### `solver_sensitivity_table(rq2_rows, graph_meta) -> list[dict]`
- Per instance on RQ2 slice: `n`, `m`, `density`, `max_degree`, `UB`, per-solver `t_total`, winner solver, `fastest`/`slowest` ratio, `max/min` ratio, and coefficient of variation `cv` across solvers. Sorted by instance.

### `verify_code_spec_paper_consistency() -> list[ConsistencyFinding]`
- See §Consistency Anchors below. Each finding `{check_id, status: "ok"|"fail", file, symbol, expected, actual, message}`. BR-9 message format.

### `evaluate_g4_gate(...) -> G4Summary`
- `{triaged_total, code_bugs, all_triaged, sat_discussion_complete, boxes_checked, passed, statement}`.

### `render_w5_markdown(...) -> dict[str, str]`
- Returns four Markdown strings keyed by output filename; each carries the `> **Lưu ý:** File này được sinh tự động bằng python -m experiments.w5_final_analysis, không chỉnh sửa tay.` + source-note banner.

## Consistency Anchors (implemented in `verify_code_spec_paper_consistency`)

Each anchor is live-derived from code + cross-checked against doc text. § numbers cite `docs/sat_spec.md` (`S`), `docs/w2-sat/14-sat-methodology.md` (`M`), `docs/technical_appendix_draft.md` (`A`), `docs/canonical_sat_config.md` (`C`).

- `C1` variable IDs: build `pairwise.build_cnf(path4, 1)` → `var_of[(v,p)] == v*4+p`, `n_vars == 16`; build `order.build_cnf(path4, 1)` → `var_of[(v,p)] == v*3+p`, `n_vars == 12`. Fail if doc `S §2` / `M §3.2` / `A §A.1/A.2` lack the literal formulas `v * n + p` / `v * (n - 1) + p` and counts `n²`/`n(n−1)`.
- `C2` path4 clause counts: `pairwise` K=1/2/3 → 56/74/86; `order` K=1/2/3 → 32/50/62, live from `len(cnf.clauses)`. Fail if `S §3` table (56/74/86) or `M §3.3` (both tables) mismatches, or appendix `A.1/A.2` contradicts.
- `C3` `_not_value` boundaries: assert `order._not_value(var_of, n, v, 1) == [-var_of[(v,1)]]`, `(…, n) == [var_of[(v,n-1)]]`, interior `1<q<n` → `[-var_of[(v,q)], var_of[(v,q-1)]]`. Fail if `A §A.5` wording diverges (single-literal at boundaries, two-literal interior).
- `C4` K-search: `grep` `k = lo + 1`, `lo, best_solution, best_cnf = value` (lo ← B đã verify), `hi, unsat_source = k` in `src/sat/solve.py`; assert `S §5` + `A §A.5` both state `K ← B + 1` and first-UNSAT stop.
- `C5` `trivial_unsat`: assert `pairwise.trivial_unsat(n, k)` is `k >= n`, and `_probe` checks it before `build_cnf`; assert `S §1` + `M §3.1` + `A` Corollary A.3.1 describe "UNSAT before CNF build".
- `C6` canonical config: `CANONICAL_SAT_CONFIG` fields (`method="sat"`, `abp_encoding="order"`, `amo_encoding="pairwise"`, `sat_solver="glucose4"`, `search_mode="multi"`, `symmetry=False`, `warm_start=False`, `seed=0`) equal `C` proposal table and `docs/w4-sat/21-m2-freeze-v1.md` code block.
- `C7` memory contract: `canonical_sat_config()` defaults to `memory_limit=12.0` GiB and `canonical_sat_config(memory_limit=None)` raises `ValueError` containing `memory_limit`. Assert `C` and `21-m2-freeze-v1.md` and `S/M` state the same default cap and rejection rule.
- `C8` P1 R1–R6 closure: source-text checks over `src/exact/*` + `tests/exact/*` + `docs/exact_models.md`, per `docs/w2-sat/13-review-p1-formulation.md`:
  - R1 → `tests/exact/test_exact_solvers.py` contains `_skip_if_backend_unavailable` + `pytest.skip` + `cpoptimizer.exe` engine guard.
  - R2 → `docs/exact_models.md` "Timing and memory-limit scope" mentions runner `wall_time` and `time_limit + 30 seconds`.
  - R3 → `src/exact/common.py::validate_exact_input` raises `ValueError` for bad input (present in all 4 solvers).
  - R4 → `src/exact/common.py::warn_ignored_config` + calls in `gurobi_mip/cplex_mip/cplex_cp`.
  - R5 → `src/exact/cp_sat_solver.py::_safe_upper_bound` returns `n - 1` on `UNKNOWN`/non-finite bound.
  - R6 → each of `gurobi_mip/cplex_mip/cplex_cp` returns `ERR` when `objective != model_objective`.
- `C9` deliverable hygiene: over `docs/w5-sat/*.md` + the four W5-`touched` legacy docs (see Module & File Plan), assert (a) no `TODO`/`TBD`/`FIXME` tokens, (b) zero `docs/handoff/` occurrences, (c) every relative markdown link target resolves in-repo.
- `C10` fairness statement: `docs/w2-sat/13-review-p1-formulation.md` + generated `27-*.md` state the five fairness points (`wall_time`, time-limit semantics, `ub` on TO, `MIPGap=0`/gap tolerances excluded, shared `verify()`).

## Module & File Plan

- `experiments/w5_final_analysis.py` — create — CLI + all `load_*`, projection, sensitivity, trajectory, consistency, G4, render functions.
- `tests/experiments/test_w5_final_analysis.py` — create — unit/integration spec below.
- `docs/w5-sat/24-rq1-final.md` — create (generated) — RQ1 conclusion + 3 case studies + source note.
- `docs/w5-sat/25-rq2-final.md` — create (generated) — RQ2 ranking + 2 case studies + Kissat exclusion.
- `docs/w5-sat/26-cross-review-consistency.md` — create (generated) — consistency findings table + P1 R1–R6 recheck table.
- `docs/w5-sat/27-paper-v09-sat-sections.md` — create (generated) — §3, RQ1, RQ2, appendix A.1–A.7 W5 text, trace table.
- `docs/sat_spec.md` — modify — §3 distance clauses wording already §2-consistent; confirm no `docs/handoff/` (zero, verify only).
- `docs/technical_appendix_draft.md` — modify — A.3/A.7 anchors refreshed to W5 measurements; confirm zero `docs/handoff/`.
- `docs/w2-sat/14-sat-methodology.md` — modify — repoint 5 `docs/handoff/` links → in-repo (`12-test-matrix.md`, `13-review-p1-formulation.md`).
- `docs/w2-sat/15-m1-gate-evidence.md` — modify — repoint 8 `docs/handoff/` links → `docs/w2-sat/12-test-matrix.md`, `docs/abp-sat-encoding/*`.
- `docs/canonical_sat_config.md` — modify — add "W5 final" status line referencing generated 24/25 (no content change to frozen tables).
- `docs/abp-sat-encoding/issues/W5/24..27-*.md` — modify — check checklist boxes only where evidence exists (manual step; module emits exact checkbox text).

## Test Plan (`tests/experiments/test_w5_final_analysis.py`)

All assertions must NOT require network/licensed backends. `project_cnf_growth` and consistency checks are pure.

- `test_project_growth_matches_build_cnf_path4`: for `path4` (n=4,m=3), pairwise/order × K=1..3, `project_cnf_growth(n,m,k=…)["clauses","variables"]` equals `len(build_cnf(...).clauses)`, `cnf.n_vars`.
- `test_project_growth_known_anchors`: n=50,m=100 → pairwise/pairwise `clauses == 255400`, `variables == 2500`; order `clauses == 196450`, `variables == 2450` (K=n-1=49 vs last-probe K; assert exact for the documented K=17 anchor `255400`/`196450`).
- `test_project_exceeds_cap_labeled`: n=118/420/715 with HB m returns `exceeds_cap=True` for pairwise/pairwise at `cap_mb=12288.0` (assert monotonic) and `False` for `order`.
- `test_load_sources_prefers_runs_csv`: tmp CSVs → `runs.csv` present selects it; absent → pilot fallback with named source.
- `test_graph_metadata_density_ub`: `randconn40` → `density == 2*m/(40*39)`, `UB == 40 - max_degree`, `m == len(edges)`.
- `test_find_larger_cnf_faster_and_inversion`: synthetic rows → larger-but-faster pair extracted; `cross_size_runtime_inversion` returns n50<n40 item for a fabricated solver.
- `test_extract_feas_trajectories`: tmp raw dir with a FEAS JSON → one entry, `probes` length == `n_probes`, `status=="FEAS"`, `k_best`, `k_unsat`.
- `test_solver_sensitivity_winner_and_cv`: synthetic 4-solver rows → correct winner, ratio, `cv` bounds.
- `test_consistency_c_anchors_pass`: `verify_code_spec_paper_consistency()` returns all `status=="ok"` for C1–C10 on clean repo (skip C9 doc-existence if `docs/w5-sat` outputs not yet generated: guard with `pytest.skip` when files absent).
- `test_consistency_perturb_reported`: monkeypatch `src.sat.order._not_value` boundary branch (or patch a returned formula constant) → checker reports a FAIL finding with BR-9 message (file + symbol + mismatch).
- `test_canonical_memory_contract`: `canonical_sat_config()` returns `memory_limit == 12.0`; `canonical_sat_config(memory_limit=None)` raises ValueError.
- `test_cli_writes_four_docs_and_exit_zero`: `main(["--check-only"])` on repo fixtures writes ≥4 files to tmp `--out-dir`, exits `0`, banners present, no `TODO/TBD/FIXME`, no `docs/handoff/` in emitted text.
- `test_p1_r1_to_r6_source_evidence`: each exact-source check (`src/exact/common.py`, `cp_sat_solver.py`, `tests/exact/test_exact_solvers.py`) matches its expected token/substring.

## Technical Risks & Rollout Notes

- `results/runs.csv` absence vs P3 delivery mid-W5 (OQ-1): loader picks one primary source and never mixes; report states which. Risk: numbers may shift if P3 re-runs differ → documented discrepancy note required.
- Paper v0.9 location (OQ-2): `27-paper-v09-sat-sections.md` is the SAT-section fragment; final paper path is a P1/P3 merge decision, not resolved here.
- OQ-3 canonical solver (`minisat22` eligibility) and OQ-4 final `memory_limit` (candidate `12288.0` MB) remain P1/P3 decisions; projection baseline parameterized via `--cap-mb`.
- OQ-5: any R1–R6 recheck found open → report, do not patch (per scope). Risk tracked in `26-*.md` findings table.
- Windows-only import risk: consistency checker must not `import src.exact.cp_sat_solver` (Ortools) or CPLEX/Gurobi; use `ast`/`Path.read_text` + `re` only.
- `--cap-mb` is a dev-only knob; production G4 statement always uses a finite capped projection baseline. The canonical SAT config always carries the `12.0` GiB cap and never `None`.