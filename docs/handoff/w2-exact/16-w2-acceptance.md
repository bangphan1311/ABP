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
- [ ] Re-run `uv run python -m pytest tests -q` against this follow-up branch.
- [ ] Re-run the 15-result smoke verification against this follow-up branch.
- [ ] Review the resulting CI and local test outputs before approving/merging.

## Limitations and release gate

The earlier 454-pass result and 15/15 smoke verification predate this follow-up
branch; they are historical evidence, not proof that the new edits pass. CPLEX CP
must be verified in an environment with the CP Optimizer engine. If the engine or
license is unavailable, its optional test may skip, but the acceptance report must
record that limitation. `Config.memory_limit` is not enforced as a hard cap and must
not be used as an official memory-limit control.

**Gate:** approve Week 2 core only after the two pending reruns and CI complete
successfully. Do not label Week 3 benchmark/research acceptance complete.
