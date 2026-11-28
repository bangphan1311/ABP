# Requirements — w3-w4-review-fixes

> **Superseded (2026-11-28):** the `allow_unbounded_memory` escape hatch below was replaced
> by the canonical `memory_limit=12.0` GiB default merged on `main`. Current contract:
> `docs/canonical_sat_config.md`. This file stays as the historical record of blocker B3.

Source: P1's 6 W3/W4 review blockers on issues #25 / #49 / PR #52 (W3 closeout).
Code locations verified against `main` (2026-11-09).

## Business Need & Goal

P1's review found that W3/W4 evidence can mislead the freeze decision: the G3 gate
reports `PASS` (100% completion) even when no expected run plan was supplied, RQ1/RQ2
tables mix experimental axes, official runs can execute without any memory cap, the
triage tool misclassifies missing-instance records, and several docs reference paths
that no longer exist (`docs/handoff/...` moved by commit `6137bf3`). Goal: all six
blockers fixed so the `v1.0` SAT freeze gate is evaluated on trustworthy evidence.

## User Stories

- As reviewer (P1), I want G3 completion to show `PENDING` when no frozen run plan
  exists, so that a half-finished campaign is never reported as `PASS`.
- As analyst (P2), I want RQ1/RQ2 summaries computed on single-axis slices, so that
  each table answers exactly one research question.
- As operator of official runs, I want the canonical SAT config to refuse an unbounded
  memory limit, so that no official run executes without a team-approved cap.
- As triage user (P2/P3), I want records whose benchmark instance file is missing to be
  classified `ENV_ERROR`, so that solver behavior is not misread as a code bug.
- As reviewer (P1/P3), I want W3/W4 docs, paths, and test counts synced to the repo
  layout, so that every evidence link in the freeze checklist resolves.

## Scope

- **In scope:**
  - `experiments/analyze_rq1_rq2.py`: G3 expected-runs semantics (B1); RQ1/RQ2 axis
    filtering + new CLI flags (B2); `DEFAULT_REPORT_PATH` fix + report regeneration (B5).
  - `src/sat/solve.py`: `canonical_sat_config()` / `CANONICAL_SAT_CONFIG` memory-limit
    validation for official use (B3); `docs/canonical_sat_config.md` sync.
  - `src/sat/triage.py`: missing-instance `ENV_ERROR` precedence + `DEFAULT_BENCHMARK_DIRS`
    fix (B4).
  - Docs: `docs/abp-sat-encoding/issues/W3/16..20-*.md` check-off with evidence;
    `docs/abp-sat-encoding/issues/W4/*.md`; `docs/w4-sat/21-m2-freeze-v1.md`;
    `docs/w4-sat/23-rq1-rq2-draft-analysis.md` (regenerated).
  - Tests: update/extend `tests/sat/test_solve.py`, `tests/sat/test_triage.py`,
    `tests/experiments/test_analyze_rq1_rq2.py` for the behavior changes above.
- **Out of scope:**
  - Any change to encoding logic, K-search, solver backends, or solver results
    (`solve_sat` outputs unchanged).
  - Choosing the official memory-cap number (team decision per P1; candidate recorded
    value is host cap `12.0` GiB = `12288.0` MB from P1's protocol).
  - Implementing runner-level RSS enforcement (P3 runner layer; here we only require
    the config to carry the cap and refuse `None` for official use).
  - New pilots, RQ3 official runs, tagging `v1.0`, paper/LaTeX sections.

## Business Rules

- `BR-1`: `expected_runs` must never fall back to observed `completed_runs` — criterion:
  in `render_markdown_report()` the expression `expected_core_runs or max(completed_count, 1)`
  no longer exists and no default-to-observed fallback is reachable — OK: `--expected-runs 70`
  with 70 completed → ratio `1.0` / BAD: flag omitted → ratio `100.0% PASS` on 70 observed runs.
- `BR-2`: G3 pass rule — criterion: with explicit `expected_core_runs > 0`, gate passes iff
  `completed_runs / expected_core_runs >= 0.80` AND `unclassified_anomalies == 0` AND
  `code_bugs_count == 0` (current `evaluate_g3_gate` logic preserved).
- `BR-3`: RQ1 slice — criterion: every row counted in a `summarize_rq1` group has
  `solver == "cadical195"` (default; configurable) AND `search_mode in ("", "multi")` AND
  `symmetry` false AND `warm_start` false — OK: pilot RQ1 table has 4 rows of cadical195 runs /
  BAD: table mixes `glucose4` rows from a combined `runs.csv`.
- `BR-4`: RQ2 slice — criterion: every row counted in a `summarize_rq2` group has
  `abp_encoding == "order"` AND `amo_encoding == "pairwise"` (defaults; configurable) AND the
  same fixed control axes as `BR-3` — OK: pilot RQ2 table has 4 solver rows over
  `order/pairwise` only / BAD: table mixes `pairwise/seqcounter` rows into solver ranking.
- `BR-5`: Official canonical config requires an explicit positive `memory_limit` — criterion:
  building an official config with `memory_limit=None` raises `ValueError` mentioning
  `memory_limit`; dev/unit tests must pass an explicit `allow_unbounded_memory=True` escape
  hatch to get `None` — OK: `canonical_sat_config(memory_limit=12288.0, official=True)` succeeds /
  BAD: `canonical_sat_config(official=True)` silently returns `memory_limit=None`.
- `BR-6`: Triage missing-instance precedence — criterion: `inspect_record()` returns
  `category="ENV_ERROR"`, `is_anomaly=True` whenever `instance is None` after
  `find_instance()` or `instance_id` is missing/empty/non-string, before any
  `TO`/`ERR`/`MO`/`OPT`/`FEAS` classification, with a reason naming the instance id —
  OK: `TO` record with unknown instance → `ENV_ERROR` / BAD: `TO` + `solution=None` → `SOLVER_BEHAVIOR`.
- `BR-7`: Docs sync — criterion: every path cited in the touched docs resolves in the repo
  at the commit that closes this task; both `21-m2-freeze-v1.md` files cite one pytest count
  that equals the actual suite output — OK: `docs/w4-sat/23-rq1-rq2-draft-analysis.md` opens from
  `DEFAULT_REPORT_PATH` / BAD: doc still cites `docs/handoff/w4-sat/...` (directory does not exist).

## Functional Requirements & Acceptance Criteria

- `FR-1` (B1 — G3 expected runs, `experiments/analyze_rq1_rq2.py`):
  - When `--expected-runs` is omitted (`expected_core_runs is None`), the generated report's
    G3 section shows completion as `PENDING` and the overall gate conclusion as `PENDING`
    (neither `PASS` nor `FAIL`).
  - When `expected_core_runs > 0` is given, `evaluate_g3_gate` computes
    `completed_runs / expected_core_runs >= 0.80` with `0` unclassified anomalies and
    `0` `CODE_BUG`, exactly as today (`G3_THRESHOLD = 0.80` unchanged).
  - Explicit non-positive `--expected-runs 0` keeps raising the existing
    `ValueError("expected_runs phải > 0.")`; omitted vs `0` are distinct behaviors.
  - AC: given pilot data and no `--expected-runs`, when the report is generated, then the G3
    section contains `PENDING` for completion and for the gate conclusion and does not contain
    `100.0%` completion; given `--expected-runs 70` and 70 completed runs, then the report shows
    `70 / 70`, `100.0%`, `PASS` as before.
- `FR-2` (B2 — RQ1/RQ2 axis filtering, `experiments/analyze_rq1_rq2.py`):
  - `summarize_rq1()` (or an equivalent row-filter step applied before grouping) accepts a
    solver parameter, default `"cadical195"`, exposed as CLI `--rq1-solver`; rows with other
    solver values, or with `search_mode` not in `("", "multi")`, `symmetry` true, or
    `warm_start` true are excluded from every RQ1 group.
  - `summarize_rq2()` (or row filter) accepts `abp_encoding` (default `"order"`) and
    `amo_encoding` (default `"pairwise"`), exposed as CLI `--rq2-abp-encoding` /
    `--rq2-amo-encoding`; rows outside the pair or violating the fixed control axes are
    excluded from every RQ2 group.
  - The generated report states the fixed slice (fixed solver for RQ1; fixed encoding pair for
    RQ2) so tables are self-describing.
  - Existing pilot behavior is preserved: on `results/pilot_rq1.csv` RQ1 still yields the
    current 4 `(abp, amo)` rows; on `results/pilot_rq2.csv` RQ2 still yields the current
    4 solver rows (pilot CSVs fix these axes by construction).
  - AC: given a combined `runs.csv` containing 2 solvers over 3 encoding pairs, when
    `summarize_rq1` runs, then each group's `n_runs` counts only cadical195 / control-axis
    rows; when `summarize_rq2` runs, then each solver group counts only `order/pairwise`
    control-axis rows; when the CLI runs with `--rq1-solver glucose4`, then RQ1 groups
    reflect glucose4 rows only.
- `FR-3` (B3 — canonical config memory cap, `src/sat/solve.py` + `docs/canonical_sat_config.md`):
  - `canonical_sat_config()` validates `memory_limit`: for official use it must be an explicit
    `float > 0`; `memory_limit=None` is rejected with `ValueError` unless the caller passes an
    explicit `allow_unbounded_memory=True` escape hatch intended for dev/unit tests.
  - Zero, negative, or non-float `memory_limit` is rejected with `ValueError`
    (`Config.memory_limit` type is `float | None`, `src/common/models.py:34`).
  - Existing callers updated cleanly: sole production caller is
    `tests/sat/test_solve.py:361` (`canonical_sat_config(time_limit=10.0)`); all current unit
    tests either keep passing (dev path) or are updated to pass an explicit limit / escape
    hatch; `src/sat/__init__.py` exports unchanged.
  - `CANONICAL_SAT_CONFIG` constant and the frozen field values (encodings, `glucose4`,
    `multi`, `symmetry=False`, `warm_start=False`, `seed=0`, `time_limit=1800.0`) do not change.
  - `docs/canonical_sat_config.md` `memory_limit` row no longer presents plain `null` as the
    official value: it states that the official run must carry an explicit cap (candidate host
    cap `12.0` GiB = `12288.0` MB recorded by P1's protocol), that in-process MO is not
    enforced by the solver (cap enforced at runner layer, Protocol §6.3), and that the final
    cap number is a team decision, not chosen by P2.
  - AC: given `canonical_sat_config(official=True)` without `memory_limit`, when called, then
    `ValueError` mentioning `memory_limit` is raised; given `memory_limit=12288.0`, then the
    returned `Config` carries `memory_limit == 12288.0` and emits no ignored-field warning;
    given `allow_unbounded_memory=True`, then a `memory_limit=None` config is returned and this
    path is only used by dev/unit tests.
- `FR-4` (B4 — triage missing instance, `src/sat/triage.py`):
  - `inspect_record()` immediately returns `category="ENV_ERROR"`, `is_anomaly=True` with a
    reason naming the missing instance file when: (a) `instance_id` is missing, empty, or not a
    non-empty string and no `instance` object was supplied; or (b) `find_instance()` returns
    `None` (file not found). This check runs before the `TO`/`ERR`/`MO`/`OPT`/`FEAS`
    classification branches.
  - Effect: `status="TO"` with `solution=None` and a missing instance file is `ENV_ERROR`
    (not `SOLVER_BEHAVIOR`); `status="ERR"` with `solution=None` and a missing instance file is
    `ENV_ERROR` (not `CODE_BUG`); `status="MO"` unchanged (`ENV_ERROR`) but gains the missing
    -instance reason when applicable; `OPT`/`FEAS` keep today's behavior.
  - Existing exception path (unreadable instance file → `ENV_ERROR`) and the explicit
    `instance=` argument path (used by `tests/sat/test_triage.py`) are unchanged.
  - `DEFAULT_BENCHMARK_DIRS` replaces the stale
    `REPO_ROOT / "docs" / "handoff" / "sat-g1" / "instances"` entry with
    `REPO_ROOT / "docs" / "sat-g1" / "instances"` (directory exists since commit `6137bf3`);
    `benchmark/*` entries unchanged.
  - AC: given a raw record `{status: "TO", solution: null, instance: "missing-1"}` and empty
    search dirs, when `inspect_record()` runs, then the report is `ENV_ERROR` with a reason
    containing `missing-1`; the same record with instance `path4` resolvable still yields
    `SOLVER_BEHAVIOR`; a record `{status: "ERR", solution: null, instance: "missing-1"}`
    yields `ENV_ERROR` with reason mentioning the missing instance file.
- `FR-5` (B5 — W3/W4 docs, paths, test-count sync):
  - `docs/abp-sat-encoding/issues/W3/16-pilot-rq1.md` … `20-bonus-sat-prototype.md`: completed
    boxes checked `[x]` with concrete evidence links, matching the closure style of
    `docs/abp-sat-encoding/issues/W2/*.md` and `W4/*.md` (evidence:
    `results/pilot_rq1.csv`, `results/pilot_rq2.csv`, `docs/canonical_sat_config.md`,
    `docs/technical_appendix_draft.md`, M1 NO-GO decision). Ticket 20 stays checked only via
    the recorded NO-GO rationale (condition of ticket 15), consistent with
    `docs/abp-sat-encoding/issues/W2/15-m1-gate-bonus-decision.md`.
  - `experiments/analyze_rq1_rq2.py`: `DEFAULT_REPORT_PATH` and the module docstring point to
    `docs/w4-sat/23-rq1-rq2-draft-analysis.md` (not `docs/handoff/w4-sat/...`).
  - `docs/w4-sat/23-rq1-rq2-draft-analysis.md` regenerated by
    `python -m experiments.analyze_rq1_rq2` after `FR-1`/`FR-2` land (content must equal a
    fresh run; with no `--expected-runs` the G3 section is `PENDING`, per `FR-1`).
  - `docs/w4-sat/21-m2-freeze-v1.md`, `docs/abp-sat-encoding/issues/W4/*.md` (21/22/23), and
    `docs/canonical_sat_config.md` are synced: identical exact pytest count in both `21` files
    equal to the actual full-suite output of the closing commit; §12 freeze-gate wording —
    tag `v1.0` only after all freeze gates (dataset, host, solver, resource enforcement,
    cross-review, evidence) pass; cross-references to `docs/sat_spec.md`,
    `docs/w2-sat/14-sat-methodology.md`, `docs/technical_appendix_draft.md`.
  - Stale `docs/handoff/w4-sat/...` reference in `docs/w4-sat/21-m2-freeze-v1.md` §4 removed
    (points to `docs/w4-sat/23-rq1-rq2-draft-analysis.md`).
  - AC: given the touched docs, when grep runs for `docs/handoff/`, then no match remains in
    the five touched doc groups; when the pytest count in `docs/w4-sat/21-m2-freeze-v1.md` is
    compared with `docs/abp-sat-encoding/issues/W4/21-m2-freeze-v1.md`, then both show the
    same `N passed, M skipped` string produced by the closing commit's suite run.

## Non-Functional Requirements (NFRs)

- **Reproducibility:** the RQ1/RQ2/G3 report is generated only by
  `python -m experiments.analyze_rq1_rq2` from committed CSVs; no hand-edited numbers
  (regenerated file must match a fresh run byte-for-byte given the same inputs).
- **Data safety:** triage reproduction stays in-memory; no writes to `results/raw/`.
- **Performance:** G3/RQ1/RQ2 computation on the committed CSVs finishes in the same order of
  magnitude as today (no new per-row parsing beyond the two new filters).
- **Behavioral compatibility:** solver outcomes (`status`, `lb`, `ub`, timings, memory) of
  `solve_sat` unchanged; only config validation, analysis slicing, triage classification, and
  docs change.
- **Auditability:** every W3 issue box carries an evidence link that resolves in-repo; freeze
  -gate conditions are traceable to Experimental Protocol §12 wording.

## Edge Cases & Contradictions

- `--expected-runs` omitted vs `0`: omitted → `PENDING`; `0` → existing `ValueError` retained.
- `completed_count == 0` with `expected_core_runs=None` → `PENDING`, never division by zero,
  never `PASS`.
- Pilot CSVs carry no `search_mode`/`symmetry`/`warm_start` columns (axes are encoded in
  `run_id`, e.g. `...__multi__sym0__ws0__s0__...`): the RQ1/RQ2 filters must tolerate absent
  control-axis columns and still reproduce the current 4-row pilot tables (treat absent
  columns as canonical-default, or derive from `run_id` — implementation choice for architect).
- Combined `runs.csv` with an empty `solver` cell: excluded from RQ1 slice (does not match
  the fixed solver), never silently merged into a group.
- `inspect_record()` with an explicit `instance=` argument (test path) skips the lookup; the
  `ENV_ERROR` missing-instance rule applies only when the instance is not supplied.
- Contradiction (documented, both kept): `docs/canonical_sat_config.md` says `memory_limit`
  is `null` and "enforced by runner in Protocol §6.3", while P1 requires official configs to
  carry an explicit cap. Resolution: the solver still does not enforce the cap in-process
  (MO never appears from the solver), but the official-run config must record the runner
  -enforced cap value; `None` is acceptable only via the dev escape hatch.
- Contradiction: `docs/w4-sat/21-m2-freeze-v1.md` says `512 passed, 3 skipped`;
  `docs/abp-sat-encoding/issues/W4/21-m2-freeze-v1.md` says `513 passed, 3 skipped`.
  Resolution: re-run the suite at the closing commit and record that single count in both
  (new tests from `FR-1..FR-4` shift the number).
- `order` has no AMO group, so `order/pairwise` and `order/seqcounter` rows are CNF-identical;
  the RQ2 default pair stays `order/pairwise` and the duplicated `order/seqcounter` rows must
  not inflate RQ2 groups.

## Open Questions

- Final official memory-cap value: is `12288.0` MB (P1's protocol host cap) the team-frozen
  number, or does the batch/runner layer inject it? (P2 must not choose — P1/P3 decision.)
- Does P3's combined `results/runs.csv` include `search_mode` / `symmetry` / `warm_start`
  columns, or must the filters derive control axes from `run_id`?
- Should `evaluate_g3_gate()` accept `expected_runs=None` (returning a pending summary) or
  should `render_markdown_report()` short-circuit to `PENDING` before calling it? (Design —
  architect; observable requirement is `FR-1`.)
