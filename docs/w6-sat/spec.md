# Technical Specification — w6-sat

## Architecture Overview & Tech Stack

Single audit module `experiments/w6_signoff.py` reads frozen inputs, runs no solver, writes nothing to `results/`. It reuses `experiments.w5_final_analysis.verify_code_spec_paper_consistency()` (W5 `ConsistencyFinding`, `C1`–`C10` anchors), `experiments.w5_final_analysis.ConsistencyFinding` for the finding schema, `experiments.pilot_common.REPO_ROOT`/`use_utf8_output`, and `src.sat.triage.triage_directory`/`TriageReport` for the `70/70` `CODE_BUG=0` gate component. `src.sat.pairwise`/`src.sat.order` `build_cnf` are imported for `path4` live formula checks (`audit_variable_conventions`, `audit_threshold_semantics`). No new dependency; pure `re`/`Path` text scanning plus tiny `build_cnf` calls.

## Non-Functional Requirements (NFRs)

- Performance/Scalability: pure file reads (`docs/*.md`, `src/sat/*.py`, `requirements.txt`), one `read_instance(benchmark/toy/path4.json)`, four `build_cnf(path4, k)` calls, and `triage_directory(results/raw)` (70 JSONs, no reproduce). Target < 5 s wall-clock per `python -m experiments.w6_signoff` run. No indexing/caching; no solver subprocess, no network.
- Security/Auth: none (local CLI, reads repo paths only). Guarded imports: never `import src.exact.*`; terminology/source checks read files as text only. No writes outside `--out` (default `docs/w6-sat/`); `--check-only` writes nothing. `results/` strictly read-only.
- Reliability/Concurrency: single-threaded, deterministic. Sorted file iteration, `re.finditer` per line for stable line numbers, fixed float formatting. Byte-identical `signoff_report.md` on rerun over identical inputs. Idempotent: rerun overwrites the report with identical content.

## Data Model / Schema Changes

No DB. One shared finding schema, reused from W5.

Entity: `<ConsistencyFinding>` (`experiments/w5_final_analysis.ConsistencyFinding`) — reused verbatim, fields `check_id`, `status` (`"ok"|"fail"`), `file`, `symbol`, `expected`, `actual`, `message` (BR-9 form: file + symbol + mismatch).

Entity: `M3Summary` (`experiments/w6_signoff.py`, new dataclass) — derived, not stored:
- `w5_ok`: `bool` — all W5 `C1`–`C10` findings `status=="ok"`
- `triaged_total`: `int` — `len(triage_reports)`
- `code_bugs`: `int` — count of `category=="CODE_BUG"`
- `checks_ok`: `bool` — all W6 `W6-*` findings ok
- `boxes_ok`: `bool` — every W1 01–07 and W6 28–31 checkbox `[x]` (after evidence-verified sync)
- `passed`: `bool` — `w5_ok and triaged_total>=70 and code_bugs==0 and checks_ok and boxes_ok`
- `statement`: `str` — `P2 SAT Technical Sign-off = PASS (in-repo SAT scope)` + deferred list (BR-11) + `FAIL` version naming first failing check

Migration / Backfill: `none`.

## API / Interface Contracts

### `python -m experiments.w6_signoff [--out PATH] [--out-dir PATH] [--check-only]`

- Auth: none (local CLI). Exit `0` on PASS, `1` on any FAIL.
- Input: `--out` and `--out-dir` are the same option (alias, `dest="out"`), optional, default `REPO_ROOT / "docs" / "w6-sat"`. `--check-only` optional flag: compute all checks + exit code but write no report.
- Output: writes `<out>/signoff_report.md` (default `docs/w6-sat/signoff_report.md`, unless `--check-only`); prints one status line per check id (including the aggregate `W6-M3`) + final `PASS`/`FAIL`.
- Errors: `FileNotFoundError` from `read_instance` if `benchmark/toy/path4.json` missing; `ValueError` from `triage_directory` if `results/raw` missing; missing audit input (e.g. a W5 deliverable `27-paper-v09-sat-sections.md`) → FAIL finding `"<relpath>: thiếu file"` from `audit_terminology`/`verify_claims`/`audit_correlation_hygiene`/`lint_markdown_tables` (never skip), and the M3 gate fails; missing W5/W6/W1 issue files → FAIL finding, matching W5 OQ-5 / FR-16 edge.

### `audit_terminology(paths: Sequence[Path]) -> list[ConsistencyFinding]`
Returns findings per BR-1..BR-4 token sets over `docs/sat_spec.md`, `docs/technical_appendix_draft.md`, `docs/w5-sat/24..27-*.md`, `docs/canonical_sat_config.md`, `docs/sat_tooling.md`, plus `src/sat/*.py` and `requirements.txt` for solver/version checks. Missing required token → `check_id="W6-T1..W6-T5"`, `status="fail"`, `file`+`symbol`+`expected`/`actual` (BR-9). Forbidden tokens also FAIL: clause-group name `\buniqueness\b` (must be `permutation`) in `W6-T2`, label range `p ∈ 0..n-1` (labels are `1..n`) in `W6-T1`. Missing input file → FAIL `"<relpath>: thiếu file"`. Does not flag `on this subset`/`measured` qualifiers; `search_mode` stale-warning text is recorded as pre-existing known state, not a W6 FAIL.

### `audit_variable_conventions() -> list[ConsistencyFinding]`
Builds `pairwise.build_cnf(path4, 1)` and `order.build_cnf(path4, 1)` live; asserts `var_of[(v,p)]==v*4+p` / `n_vars==16`, `var_of[(v,p)]==v*3+p` / `n_vars==12`; cross-checks doc literals by section — `v*n+p` and `n²` must appear inside appendix `## A.1` (pairwise), `v*(n-1)+p` and `n(n-1)` inside `## A.2` (order), plus all four in `docs/sat_spec.md`. Mismatch → `check_id="W6-T6"` FAIL with file + symbol; missing input file → FAIL `"<relpath>: thiếu file"`.

### `audit_threshold_semantics() -> list[ConsistencyFinding]`
Asserts `pairwise.trivial_unsat(n,k)==(k>=n)` for `n in 2..6`, `k in 1..7`; `K=1` always SAT. Cross-checks `docs/sat_spec.md` §1 and `docs/technical_appendix_draft.md` Corollary A.3.1 state `K >= n: UNSAT` (never `K > n`). `check_id="W6-T7"`.

### `verify_claims(paths: Sequence[Path]) -> list[ConsistencyFinding]`
Scans `docs/technical_appendix_draft.md` + `docs/w5-sat/24..27-*.md` for BR-5 forbidden phrases (`clearly better`, `obviously faster`, `always faster`, plus a configurable `FORBIDDEN_QUALITATIVE` token set) and for qualitative claims lacking an adjacency anchor (`results/` path, measurement token `<num> s`, or `(file, measurement)`). `check_id="W6-C1"` per finding with file + line + phrase; missing file → FAIL `"<relpath>: thiếu file"`.

### `check_lemma_numbering() -> list[ConsistencyFinding]`
Parses `docs/technical_appendix_draft.md` for labels `Lemma A.x`, `Corollary A.3.1`, `Theorem A.x` via `re`. Expected exactly `A.1..A.8`, `A.3.1`, `A.9..A.11`. Gap / duplicate / out-of-sequence reference → `check_id="W6-C2"` FAIL naming the offending label.

### `check_appendix_integrity() -> list[ConsistencyFinding]`
Asserts headings `A.1`..`A.7` present and in order; cross-checks live `build_cnf` path4 counts (`pairwise` 56/74/86, `order` 32/50/62) against `docs/sat_spec.md` §3 and the per-section formulas (`A.1`: `v*n+p`/`n²`; `A.2`: `v*(n-1)+p`/`n(n-1)`). Missing section or formula mismatch → `check_id="W6-C3"` with file + symbol; missing appendix file → FAIL `"<relpath>: thiếu file"`.

### `audit_correlation_hygiene(paths: Sequence[Path]) -> list[ConsistencyFinding]`
Per line of `docs/w5-sat/24..27-*.md` + `docs/canonical_sat_config.md`, flags BR-8 causal phrasing. Strict phrases (`determines`, `causes`, `therefore runtime is`) always FAIL — a qualifier such as `on this subset` or `measured` on the same line does not exempt them; weaker phrasings require the allowed qualifiers (`correlation`, `on this subset`, `measured`). Violation → `check_id="W6-L1"` with file + line number; missing file → FAIL `"<relpath>: thiếu file"`.

### `lint_markdown_tables(paths: Sequence[Path]) -> list[ConsistencyFinding]`
Checks SAT deliverable Markdown tables: consistent column counts per table (split on unescaped `|`), every table row closed by an unescaped `|` (`| 1 | 2` without the closing pipe is unbalanced), balanced backticks/code spans. Broken row → `check_id="W6-L2"` with file + line; missing file → FAIL `"<relpath>: thiếu file"`. Duplicate CNF rows (`order/seqcounter` ≡ `order/pairwise`) are never flagged (pre-existing RQ1 consistency check).

### `record_deferred_items() -> list[dict[str, str]]`
Returns the five deferred entries, each `{"item": ..., "owner": ..., "status": "deferred"}`:
1. `P3 LaTeX sections` — `P3`
2. `final English copy-edit` — `P3`
3. `paper/LaTeX prose` (deferred to next week) — `P2+P1`
4. `P3 official 24-instance runs.csv` — `P3`
5. `P3 manuscript merge` — `P3`

### `emit_w1_checkbox_edits(issue_files: Sequence[Path]) -> list[dict[str, str]]`
For each `docs/abp-sat-encoding/issues/W1/01..07-*.md`, reads current `- [ ]` lines, maps each to a verified in-repo evidence path, returns `{file, merged_text}` with `- [x]` + `(evidence: <path>)`. Only emits a `docs/handoff/` link preceded by a `Path.is_file()` check (FR-12 / C9-style). Ticket 05 item 4 deferral: flipped `[x]` only if the documented deferral exists (`docs/w2-sat/` evidence); otherwise stays `[ ]` and the gate names it. Emitted text is a manual/committed edit; module never writes issue files.

### `emit_w6_checkbox_edits(issue_files: Sequence[Path]) -> list[dict[str, str]]`
Same contract for `docs/abp-sat-encoding/issues/W6/28..31-*.md`; evidence paths are `tests/experiments/test_w6_signoff.py` and generated `docs/w6-sat/signoff_report.md` (per-check sections).

### `open_boxes(issue_files: Sequence[Path] | None = None) -> list[str]`
Flags every `- [ ]` line plus every `- [x]` line whose evidence is missing, does not match `(evidence: <path>)`, points to a path with `Path.is_file() == False`, or references `docs/handoff/` (FR-12 / C9-style). A missing issue file is flagged too. `checkboxes_ok()` is `not open_boxes()`.

### `evaluate_m3_gate(w5_findings, triage_reports, w6_findings, boxes_ok: bool) -> M3Summary`
Aggregates FR-10: (a) W5 `verify_code_spec_paper_consistency()` all ok, (b) `len(triage_reports)>=70` and `code_bugs==0`, (c) all W6 findings ok, (d) `boxes_ok`. Any single FAIL component → `passed=False` and `statement` names that check. `statement` always carries `PASS (in-repo SAT scope)` + the five `record_deferred_items()` entries (BR-11). `m3_finding(summary)` wraps the result as the single `check_id="W6-M3"` `ConsistencyFinding` printed by the CLI and rendered in the report (§4 + §6).

### `render_signoff_markdown(...) -> str`
Returns one Markdown string: `GENERATED_NOTE` banner (same convention as W5, exact text `"python -m experiments.w6_signoff"`), per-ticket sections `28`/`29`/`30`/`31` (section 31 carries the `W6-M3` finding row), W6 findings tables (BR-9 schema columns), W5 `C1`–`C10` summary line, deferred list, and the M3 statement.

## Check ID Catalog

| Group | IDs | Source FR/BR |
|---|---|---|
| terminology/notation | `W6-T1`..`W6-T7` | FR-1..FR-3 (BR-1..BR-4) |
| claim/lemma/appendix | `W6-C1`..`W6-C3` | FR-4..FR-6 (BR-5..BR-7) |
| correlation/tables | `W6-L1`, `W6-L2` | FR-7..FR-8 (BR-8) |
| M3 gate + checkbox audit | `W6-M3` (aggregate) | FR-10..FR-12 (BR-9..BR-11) |

Naming: each finding's `check_id` is exactly one of the above (no suffix). `W6-M3` is the single aggregate finding emitted by `evaluate_m3_gate` for the gate decision; per-component evidence is `W6-T*`/`W6-C*`/`W6-L*` plus W5 `C*`.

## Module & File Plan

- `experiments/w6_signoff.py` — create — CLI, dataclasses, all `audit_*`/`verify_*`/`check_*`/`lint_*`/`emit_*`/`evaluate_m3_gate`/`render_signoff_markdown`/`main`.
- `tests/experiments/test_w6_signoff.py` — create — pytest suite (`test_checklist`).
- `docs/w6-sat/signoff_report.md` — create (generated) — banner + sections 28/29/30/31 + M3 statement.
- `docs/abp-sat-encoding/issues/W1/01..07-*.md` — modify (manual committed step) — `[ ]` → `[x]` + evidence path where in-repo evidence exists; module emits exact text.
- `docs/abp-sat-encoding/issues/W6/28..31-*.md` — modify (manual committed step) — `[ ]` → `[x]` + evidence path; module emits exact text.

No changes to `src/sat/*`, `docs/sat_spec.md`, `docs/technical_appendix_draft.md`, `docs/canonical_sat_config.md`, `docs/sat_tooling.md`, `docs/w5-sat/*` — read-only inputs, findings only.

## Test Plan (`tests/experiments/test_w6_signoff.py`)

All plain-pytest; no network/licensed backends. Every test runs against the live repo (clean state PASS) or a perturbed copy/tmp file (exactly one FAIL with file+symbol). Perturbation lives in `tmp_path` / `monkeypatch`, never mutates committed files.

- `test_terminology_clean_repo_passes`: `audit_terminology(TERM_PATHS)` → all `status=="ok"`; assert found `check_id` set `{"W6-T1","W6-T2","W6-T3","W6-T4","W6-T5"}`.
- `test_terminology_seeded_TIMEOUT_names_file`: copy `docs/sat_spec.md` → `tmp_path`, inject `status: "TIMEOUT"` into copy; run `audit_terminology` with the copy substituted → exactly one `status=="fail"`, message contains the file and `TIMEOUT`.
- `test_terminology_bad_solver_kissat_grid`: copy a candidate-table text, inject `kissat` as candidate → one FAIL naming `kissat`.
- `test_variable_conventions_ok_and_perturb`: `audit_variable_conventions()` all ok on repo; monkeypatch `order.build_cnf`'s `var_of` formula via a fake `CNF` to `v*(n-1)` → `W6-T6` FAIL with file + symbol (mirror of W5 `test_consistency_perturb_reported`).
- `test_threshold_semantics_ok_and_K_gt_n_fails`: `audit_threshold_semantics()` ok on repo; a doc-variant string `K > n: UNSAT` (fed as input override) → one FAIL.
- `test_verify_claims_clean_and_seeded_phrase`: `verify_claims(CLAIM_PATHS)` zero failures on repo; seed `"always faster"` with no anchor into a tmp copy → exactly one `W6-C1` FAIL naming file + phrase.
- `test_lemma_numbering_ok_and_dup_gap`: `check_lemma_numbering()` ok on repo (sequence `A.1..A.8, A.3.1, A.9..A.11`); feed text with duplicate `Lemma A.5` or missing `A.6` → `W6-C2` FAIL with the offending label.
- `test_appendix_integrity_ok_and_missing_section`: `check_appendix_integrity()` ok on repo; copy `docs/technical_appendix_draft.md` minus the `## A.6` heading → `W6-C3` FAIL `missing-section`.
- `test_correlation_hygiene_ok_and_determines`: `audit_correlation_hygiene(CORR_PATHS)` zero findings on repo; line `n determines runtime` without mechanism → one `W6-L1` FAIL with file + line number.
- `test_markdown_tables_ok_and_broken_row`: `lint_markdown_tables(TABLE_PATHS)` zero on repo; a broken table row (unbalanced `|`) in a tmp file → one `W6-L2` FAIL with line.
- `test_deferred_items_five_entries`: `record_deferred_items()` returns 5 entries, each `status=="deferred"`, owners in `{"P3","P2+P1"}`.
- `test_w1_w6_checkbox_edits_and_evidence_paths`: `emit_w1_checkbox_edits(W1_ISSUES)` — every flipped `[x]` carries ≥1 evidence path; any emitted `docs/handoff/` link passes `Path.is_file()`; `emit_w6_checkbox_edits(W6_ISSUES)` flips 28..31 boxes with `tests/experiments/test_w6_signoff.py` evidence.
- `test_m3_gate_pass_clean_repo`: `evaluate_m3_gate(verify_code_spec_paper_consistency(), triage_directory(DEFAULT_RAW_DIR), all_w6_findings, boxes_ok=True)` → `passed is True`, `triaged_total==70`, `code_bugs==0`, `statement` contains `PASS (in-repo SAT scope)` and the five deferred items.
- `test_m3_gate_fails_on_component`: inject one FAIL finding into `w6_findings` → `passed is False`, `statement` names that check id.
- `test_cli_check_only_exit_zero`: `main(["--check-only"])` on clean repo → `rc==0`; `main(["--out", str(tmp_path)])` writes `signoff_report.md` containing banner (`"sinh tự động"`), sections for tickets 28/29/30/31, no `TODO|TBD|FIXME`.
- `test_cli_seeded_fail_exit_one`: corrupt an input copy via `--out` pointing at a directory containing an injected `TIMEOUT` doc → `rc==1`.

## Technical Risks & Rollout Notes

- `results/runs.csv` is absent on `main` (only `results/pilot_rq1.csv`/`pilot_rq2.csv` + 70 raw JSONs). W6 reads none of these CSVs for gate evidence: triage is over `results/raw` only, so the gate stays stable. P3 `runs.csv` delivery is deferred (external gate).
- `results/raw` currently holds exactly 70 JSONs; `triage_directory` counts them. If raw files are pruned, `triaged_total < 70` → gate FAIL with missing-file finding (FR-16 edge, never skip).
- Checkbox sync is a manual/committed edit: the module emits exact `[x]` text, never writes issue files. Backend must copy the emitted lines; tester verifies with `git diff`.
- `docs/sat-tooling/*` under `docs/handoff/sat-tooling/` (probe scripts, evidence) still contains `kissat` strings; these are W1 evidence artifacts and are NOT audit inputs (`audit_terminology` scans `docs/sat_tooling.md`, not `docs/handoff/sat-tooling/`).
- Windows import risk: never `import src.exact.*` (Ortools/Gurobi/CPLEX); all exact/P1 checks are text-only, consistent with W5 `C8`.
- Deferred/external items (P3 LaTeX, English copy-edit, paper prose, `runs.csv`, manuscript merge) are recorded, not blocking: the gate is `PASS (in-repo SAT scope)` and the report lists them explicitly (BR-11).