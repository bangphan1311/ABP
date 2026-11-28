# Requirements — w6-sat (W6 P2: terminology proofread, claim verification, cross-read, M3 sign-off)

## Business Need & Goal

W1–W5 produced code, specs, pilots, frozen analysis and generated deliverables, but W6 tickets 28–31 (GH #35–#38) — terminology/notation proofread, claim verification, cross-read with P3/LaTeX, and the M3 technical sign-off — are not yet executed, and W1 tickets 01–07 (GH #8–#14) have unchecked markdown checkboxes despite completed work. W6 must close these four tickets with **automated, reproducible audit code** (paper/LaTeX prose is deferred to next week per stakeholder decision) and mark **P2 SAT Technical Sign-off = PASS (in-repo SAT scope)**.

## User Stories

- As P2 (owner), I want a programmatic terminology/notation audit over `docs/sat_spec.md`, `docs/technical_appendix_draft.md`, `docs/w5-sat/24..27-*.md` and `src/sat/*` so that every SAT term, encoding name, variable formula, clause-group name and status code is used consistently everywhere.
- As P2, I want a claim-to-evidence verifier over the appendix and generated deliverables so that no unsubstantiated qualitative claim or broken lemma/theorem numbering ships in any in-repo SAT document.
- As P2, I want a cross-read lint over analysis outputs so that correlation variables (`n`, `m`, density, `Δ`) are never stated as strict causal predictors of runtime without qualification, and formatting stays intact.
- As P2, I want an `evaluate_m3_gate` aggregator so that the M3 sign-off decision is derived from checked evidence, not from reading tickets by hand.
- As P2, I want stale W1 checkboxes (`01..07-*.md`) synced to `[x]` with evidence paths so that issue tracker state matches reality.

## Scope

- **In scope:**
  - `experiments/w6_signoff.py` — CLI audit module (pure reads, no solver runs, no writes to `results/`), emitting `docs/w6-sat/signoff_report.md` (machine-generated) plus per-ticket findings.
  - `tests/experiments/test_w6_signoff.py` — pytest suite.
  - Checkbox sync: `docs/abp-sat-encoding/issues/W1/01..07-*.md` and `docs/abp-sat-encoding/issues/W6/28..31-*.md` — `[ ]` → `[x]` only where in-repo evidence exists (module emits exact checkbox text; edit is a manual/committed step).
  - Ticket 28 (#35): terminology & notation audit (see FR-1..FR-3).
  - Ticket 29 (#36): claim verification + appendix audit (see FR-4..FR-6).
  - Ticket 30 (#37): cross-read P3 / correlation-vs-causation + formatting lint (see FR-7..FR-9); record that P3 LaTeX sections and final English copy-edit are deferred to next week / owned by P3.
  - Ticket 31 (#38): `evaluate_m3_gate` aggregating W5 consistency `C1`–`C10`, W4/W5 triage (`70/70`, `CODE_BUG=0`), W6 checks, and W1–W6 checkbox sync; statement `P2 SAT Technical Sign-off = PASS (in-repo SAT scope)` with explicit deferred/external gates list.
- **Out of scope:**
  - No new `.tex` files, no long prose paper sections (deferred to next week per stakeholder decision).
  - No changes to `src/sat/*` logic, frozen `results/` data, or W5 deliverables `24..27-*.md` (read-only inputs).
  - No re-litigation of W5 decisions (canonical config, RQ1/RQ2 conclusions); W6 audits only.
  - No LaTeX compilation of the final manuscript appendix; no P3 `runs.csv` production; no P3 manuscript merge.
  - No fixing of findings inside the audit run: findings are reported, not patched (same rule as W5 OQ-5).

## Business Rules

- `BR-1`: Terminology must match `docs/sat_spec.md` exactly — criterion: audit greps the expected token set and reports a FAIL finding per mismatch. OK: `pairwise`, `order`, `assignment`, `permutation`, `distance`, `threshold`, `x[v][p]`, `o[v][p]`, `1..n` labels, `0..n-1` vertices. BAD: `uniqueness` as a clause-group name, 1-based vertices, `x[v][p]` with `p ∈ 0..n-1`.
- `BR-2`: Status codes are exactly `OPT`, `FEAS`, `TO`, `MO`, `ERR` — criterion: no `Result.status` value or deliverable prose uses `SATISFIABLE`, `TIMEOUT`, `OOM` or other invented statuses. OK: `status: "TO"`. BAD: `status: "TIMEOUT"`.
- `BR-3`: Solver names and pinned versions are exactly `python-sat==1.9.dev15`, `cadical195`, `glucose4`, `glucose42`, `minisat22`; Kissat is recorded as blocked (not a candidate) — criterion: audit cross-checks `docs/sat_tooling.md`, `requirements.txt`, `docs/canonical_sat_config.md` and `src/sat/backend.py` tokens. OK: `sat_solver="glucose4"`. BAD: `kissat` in any candidate table, `pysat` unversioned.
- `BR-4`: Threshold semantics are `|f(u) − f(v)| ≥ K` and `K ≥ n` (with `|E| ≥ 1`) is trivial UNSAT before CNF build — criterion: audit asserts `pairwise.trivial_unsat(n, k)` returns `k >= n` and docs state the same. OK: `K ≥ n: UNSAT`. BAD: `K > n: UNSAT` in any doc.
- `BR-5`: No unsubstantiated qualitative claim — criterion: forbidden phrases (`clearly better`, `obviously faster`, `always faster`, and similar) appear in no in-repo SAT deliverable without an attached evidence anchor (file + measurement). OK: "`order` is faster on `n = 28` (1.30 s vs 6.43 s, `results/pilot_rq1.csv`)". BAD: "`order` is clearly better".
- `BR-6`: Lemma/theorem/corollary numbering in `docs/technical_appendix_draft.md` is exactly `Lemma A.1`..`A.8`, `Corollary A.3.1`, `Theorem A.9`..`A.11` — criterion: parser extracts all labels and reports FAIL on gaps, duplicates, or out-of-sequence references. OK: `A.1, A.2, A.3, A.3.1, A.4, …, A.8, A.9, A.10, A.11`. BAD: two `Lemma A.5`, missing `A.6`.
- `BR-7`: Appendix structural integrity — criterion: sections `A.1`–`A.7` all present, in order; every formula in the appendix is checked against live `build_cnf` (path4 counts `56/74/86` pairwise, `32/50/62` order; variable formulas `v*n + p`, `v*(n-1) + p`). OK: `A.1`..`A.7` present and consistent. BAD: `A.6` missing, appendix claims `n(n-1)` variables for `pairwise`.
- `BR-8`: Correlation is not stated as causation — criterion: analysis outputs (`docs/w5-sat/24..27-*.md`, `docs/canonical_sat_config.md`) that state a relation between `n`/`m`/density/`Δ` and runtime must carry a qualification ("correlation", "on this subset", "measured") and must not use strict causal phrasing ("determines", "causes", "therefore runtime is") without a documented mechanism. OK: "`n` correlates with runtime on this subset". BAD: "`n` causes higher runtime".
- `BR-9`: Findings are reported verbatim, never silently fixed — criterion: every FAIL finding carries `{check_id, status, file, expected, actual, message}` (same schema as W5 `ConsistencyFinding`). OK: finding names file + line + mismatch. BAD: audit edits a doc to make a check pass.
- `BR-10`: Checkbox sync is evidence-gated — criterion: a `- [ ]` may be flipped to `- [x]` only with a concrete in-repo evidence path (test file, generated deliverable, docs section). OK: `- [x] … (evidence: tests/sat/test_g1_oracle.py)`. BAD: unchecked box with no evidence, or `[x]` with no path.
- `BR-11`: Sign-off statement must list deferred/external gates explicitly — criterion: the `evaluate_m3_gate` statement contains `PASS (in-repo SAT scope)` plus the deferred list. OK: statement names deferred paper/LaTeX writing (next week) and P3 `runs.csv` + manuscript merge. BAD: unqualified `PASS`.

## Functional Requirements & Acceptance Criteria

- `FR-1` (Ticket 28): `audit_terminology()` scans `docs/sat_spec.md`, `docs/technical_appendix_draft.md`, `docs/w5-sat/24..27-*.md`, `docs/canonical_sat_config.md`, `docs/sat_tooling.md` and returns findings per BR-1..BR-4 token sets: encoding names, clause-group names, variable formulas, label/vertex ranges, status codes, solver names + versions, Kissat exclusion. → AC: running `python -m experiments.w6_signoff --check-only` on the clean repo yields zero FAIL findings for terminology; injecting `TIMEOUT` into a copied doc yields exactly one FAIL finding naming the file.
- `FR-2` (Ticket 28): `audit_variable_conventions()` builds `pairwise.build_cnf(path4, 1)` and `order.build_cnf(path4, 1)` and asserts doc formulas match live `var_of` (`v*n + p`, `v*(n-1) + p`) and `n_vars` (`16`, `12`). → AC: checker reports `ok` on repo; perturbing the formula in the doc-check input produces a FAIL finding with file + symbol.
- `FR-3` (Ticket 28): `audit_threshold_semantics()` asserts `trivial_unsat` boundary (`k >= n`), `K = 1` always SAT, and doc statements in `S §1`, `A Corollary A.3.1` agree. → AC: `ok` on repo; any doc variant saying `K > n` fails.
- `FR-4` (Ticket 29): `verify_claims()` scans `docs/technical_appendix_draft.md` + `docs/w5-sat/24..27-*.md` for forbidden qualitative phrases (BR-5) and for qualitative claims lacking an adjacent evidence anchor (file path or measurement token). → AC: zero unsubstantiated claims on repo; seeding `"always faster"` without evidence yields one FAIL finding.
- `FR-5` (Ticket 29): `check_lemma_numbering()` parses the appendix label sequence and in-text references (BR-6). → AC: sequence `A.1..A.8, A.3.1, A.9..A.11` reports `ok`; a duplicate or gap fails with the offending label.
- `FR-6` (Ticket 29): `check_appendix_integrity()` asserts sections `A.1`–`A.7` present in order and formulas consistent with live `build_cnf` (BR-7 anchors). → AC: `ok` on repo; removing `A.6` heading from a copy fails with missing-section finding.
- `FR-7` (Ticket 30): `audit_correlation_hygiene()` lints `docs/w5-sat/24..27-*.md` + `docs/canonical_sat_config.md` for causal phrasing about `n`, `m`, density, `Δ` vs runtime (BR-8). → AC: zero findings on repo; adding "determines runtime" without mechanism yields a FAIL naming file + line.
- `FR-8` (Ticket 30): `lint_markdown_tables()` checks SAT deliverables' Markdown tables: consistent column counts per table, no unbalanced `|`, formulas/code spans balanced backticks. → AC: zero findings on repo; a broken table row yields one finding with line number.
- `FR-9` (Ticket 30): `record_deferred_items()` writes the deferred list (P3 LaTeX sections, final English copy-edit, paper/LaTeX prose deferred to next week, P3 official 24-instance `runs.csv`, P3 manuscript merge) into the sign-off report as explicit non-blocking entries. → AC: report contains all five items, each marked `deferred` with owner (`P3` / `P2+P1`).
- `FR-10` (Ticket 31): `evaluate_m3_gate()` aggregates: (a) W5 consistency `C1`–`C10` via `experiments.w5_final_analysis.verify_code_spec_paper_consistency()`, (b) W4/W5 triage from `src/sat/triage.py` (`70/70` runs, `CODE_BUG=0`), (c) all W6 audits (`FR-1`..`FR-9`), (d) W1–W6 checkbox sync state (all `01..07` and `28..31` boxes `[x]`). → AC: gate returns `passed=True`, statement `P2 SAT Technical Sign-off = PASS (in-repo SAT scope)` + deferred list (BR-11) on a clean repo; any single FAIL component flips `passed=False` and names the failing check.
- `FR-11`: CLI `python -m experiments.w6_signoff [--check-only] [--out-dir docs/w6-sat]` writes `docs/w6-sat/signoff_report.md` with the generated-note banner (same convention as W5 `GENERATED_NOTE`), per-ticket sections `28`/`29`/`30`/`31`, and exit code `0` on PASS / `1` on any FAIL. → AC: `--check-only` on clean repo exits `0` and the report contains all ticket sections; corrupting an input yields exit `1`.
- `FR-12` (W1 sync): `emit_w1_checkbox_edits()` produces the exact `[x]` lines with evidence paths for `docs/abp-sat-encoding/issues/W1/01..07-*.md` (GH #8–#14, closed in W1/W2; evidence: `tests/sat/test_g1_oracle.py`, `tests/sat/test_pairwise.py`, `tests/sat/test_order.py`, `tests/sat/test_glucose_e2e.py`, `docs/sat_tooling.md`, `docs/sat_spec.md`, `docs/handoff/sat-g1/` where files exist). → AC: emitted text contains no `docs/handoff/` link that does not resolve in-repo (C9-style link check); every flipped box carries ≥1 evidence path.

## Non-Functional Requirements (NFRs)

- Performance: pure file reads + small CNF builds (`path4`, `n ≤ 9`); target < 5 s wall-clock per CLI run. No solver subprocess, no network.
- Security/isolation: no imports of `src/exact/*` (Ortools/CPLEX/Gurobi guarded); `src/sat/*` imports only. No writes outside `docs/w6-sat/` (and no writes at all with `--check-only`); `results/` read-only.
- Reliability: deterministic, sorted iteration order, fixed float formatting; byte-identical report on rerun over identical inputs. Idempotent.
- Auditability: every finding carries check_id, file, expected, actual, message (BR-9 schema); report is machine-generated and marked as such.

## Edge Cases & Contradictions

- Duplicate CNF rows (`order`/`seqcounter` identical to `order`/`pairwise`): RQ1 tables intentionally contain duplicate rows — audit must not flag them as data errors (recorded as consistency check in `docs/canonical_sat_config.md`).
- `docs/handoff/` links: W5 `C9` forbids new `docs/handoff/` occurrences in generated deliverables; W1 ticket files may legitimately reference `docs/handoff/sat-g1/` (demo evidence). Checkbox evidence must verify path existence before emitting the link (FR-12).
- Appendix numbering `Corollary A.3.1` sits between `A.3` and `A.4`: parser must accept sub-numbered corollary (BR-6), not treat `.3.1` as a gap.
- `search_mode` stale-warning text (`IGNORED_CONFIG_FIELDS` warning for the only implemented mode) is a known recorded discrepancy — audit reports it as pre-existing known state, not a new W6 FAIL.
- Gate evaluation when a W5 deliverable is missing (e.g. `27-*.md` deleted): `evaluate_m3_gate` FAILs with missing-file finding; it does not skip or downgrade.
- Checkbox sync where a W1 item was explicitly deferred ("Nếu không kịp W1: ghi rõ trong G1 và chuyển sang W2"): box is `[x]` only if the documented deferral exists (ticket 05 item 4 → `docs/w2-sat/` evidence); otherwise the box stays `[ ]` and the gate names it.

## Open Questions

- `none` (blocking). Non-blocking: exact final `memory_limit` (candidate `12288.0` MB) and P3 `runs.csv` delivery remain P1/P3 decisions; both are recorded as deferred/external gates, not W6 blockers.
