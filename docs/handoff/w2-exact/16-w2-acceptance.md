# Week 2 acceptance — Exact solver integration

## Scope

This acceptance covers Week 2 core integration only: exact solver adapters, shared
result/validation contract, solver smoke tests, and documentation. It does not claim
the Week 3 research benchmark, 24-graph Tier 2 experiment, RQ1/RQ2 analysis, or
optional bonus work is complete.

## Acceptance checklist

- [x] PR #39 exact solver implementation merged into main.
- [x] PR #41 SAT core integration merged into main.
- [x] CP-SAT UNKNOWN upper-bound fix committed on the follow-up branch; UNKNOWN uses
  the safe natural upper bound (n-1).
- [x] Shared exact input validation raises `ValueError` for malformed graphs and
  non-positive/non-finite time limits.
- [x] Exact solver adapters warn when unsupported non-default configuration is ignored.
- [x] Gurobi MIP, CPLEX MIP and CPLEX CP compare native objective values with the
  independently verified objective before accepting a result.
- [x] Optional exact-backend tests skip when a backend package or its engine/license
  is unavailable; genuine unexpected solver failures remain test failures.
- [x] Documentation states the distinct SAT/exact `time_limit` scopes, the runner
  hard-timeout grace, the official timing metric (`wall_time`), and that
  `memory_limit` is not a hard cap.
- [x] Existing local smoke evidence (before these follow-up edits): 454 tests passed;
  15/15 solver-by-toy results were OPT and independently verified.
- [x] Re-run `uv run python -m pytest tests -q` on `p1/w2-review-closeout`: **490 passed in 19.21s** (2026-10-23, local Windows environment).
- [x] Re-run the 15-result smoke verification on this branch: **15/15 PASS**, all OPT and independently verified objective matches both `lb` and `ub`.
- [x] `git diff --check` clean.
- [ ] Confirm required GitHub CI checks (the commit status API currently reports no status entries) and complete maintainer review before merge.

## Limitations and release gate

The initial 454-pass result was superseded by the fresh 490-pass run on this follow-up
branch. The fresh 15/15 smoke check also ran on this branch. CPLEX CP passed the smoke
run in the user's local environment. GitHub's commit status API currently returns no
status entries, so do not claim a green remote CI run unless a separate check is visible. `Config.memory_limit` is not enforced as a hard cap and must
not be used as an official memory-limit control.

**Gate:** approve Week 2 core only after the two pending reruns and CI complete
successfully. Do not label Week 3 benchmark/research acceptance complete.
