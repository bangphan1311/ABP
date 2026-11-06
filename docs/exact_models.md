# Exact formulations for ABP (P1 W3 review)

Given an undirected simple graph `G=(V,E)`, let `n=|V|`. Assign each
vertex an integer label `x_v ∈ {1,...,n}`; the labels must form a
permutation. The antibandwidth is

```
AB(G) = max_x min_{(u,v) ∈ E} |x_u - x_v|.
```

The four exact backends solve this same optimization problem. Every returned
incumbent must pass the shared `verify(instance, labeling)`; a solver status
alone is not a certificate.

## Common optimization semantics

Maximize integer `K`, subject to:

- `1 ≤ x_v ≤ n` for every vertex;
- `x_u ≠ x_v` for every distinct pair of vertices (equivalently, the labels
  form a permutation of `1,...,n`);
- `|x_u - x_v| ≥ K` for every edge `(u,v)`;
- `1 ≤ K ≤ n-1` for an instance with at least one edge.

## Gurobi MIP and CPLEX MIP

Use integer label variables `x_v`, integer objective variable `K`, and
binary orientation variables:

- For every vertex pair `i<j`, one binary chooses either
  `x_i + 1 ≤ x_j` or `x_j + 1 ≤ x_i`. This enforces pairwise distinct
  labels.
- For every edge `(u,v)`, one binary chooses either
  `x_u - x_v ≥ K` or `x_v - x_u ≥ K`.

Both implementations use indicator constraints for these implications; they
do not rely on a manually selected big-M constant. The CPLEX MIP and Gurobi
MIP formulations therefore share the same mathematical semantics.

## CPLEX CP

Use integer variables `x_v ∈ {1,...,n}`, a global
`all_diff(x)` constraint, and `abs(x_u-x_v) ≥ K` for every edge. Maximize
`K`.

## CP-SAT

Use integer variables `x_v ∈ {1,...,n}`, `add_all_different(x)`, and
for each edge an integer distance variable `d_uv` with
`d_uv = abs(x_u-x_v)` and `K ≤ d_uv`. Maximize `K`. The solver is
configured with one search worker.

## Degree-based upper bound for the ABP objective

For every instance with at least one edge, let
`Δ = max_v deg(v)`. A safe upper bound is

```
UB_degree = n - Δ.
```

Reason: choose a vertex of degree `Δ`. If the antibandwidth is at least
`K`, the labels of all its `Δ` neighbours must be at distance at least
`K` from the label of that vertex. For any fixed label in `{1,...,n}`,
there are at most `n-K` other labels at distance at least `K`.
Therefore `Δ ≤ n-K`, hence `K ≤ n-Δ`.

The value is recorded in `benchmark/hb/MANIFEST.csv` as
`ub_n_minus_delta`. It is a safe external bound for the SAT K-search and
for checking reported results; it is **not** an optimality certificate.
Under the current protocol, an `OPT` claim still requires the solver's
prescribed proof (for SAT, the required UNSAT probe). The current exact
formulations retain the natural model domain `K ≤ n-1`; this document does
not claim that `UB_degree` is already passed into every exact model.

## Result semantics

- `OPT`: solver has proved optimality and the incumbent has passed
  `verify()`; the reported `lb` and `ub` must equal the verified objective.
- `FEAS`: a verified incumbent exists, but optimality was not proved before
  the time budget ended.
- `TO`: time budget ended without a verified incumbent.
- `MO`: the runner/process supervisor confirmed that the configured memory
  limit was exceeded.
- `ERR`: execution, backend, license, malformed output, invalid incumbent,
  or objective-consistency error. A license failure is never relabelled
  `TO`.

For non-optimal feasible runs, preserve the verified objective as `lb`;
use a solver bound when available and otherwise a safe upper bound. Never
promote an unverified labeling to an incumbent.

## Input validation and configuration scope

The shared exact validation rejects instances with fewer than two vertices,
no edges, invalid endpoints, self-loops, and invalid time limits before
solver error normalization. The exact backends warn when non-default shared
configuration fields are ignored. In particular, the exact solver functions
do not independently enforce `Config.memory_limit`; the process
supervisor/runner owns the common OS-level memory cap. Backend-specific
parameters such as Gurobi `SoftMemLimit` and CPLEX `WorkMem` have different
semantics and are not substitutes for the runner's cap.

## Time accounting

Each exact implementation starts its run timer before model construction.
After building the model, it computes the remaining whole-run budget:

```
remaining = max(0, time_limit - elapsed_since_run_start)
```

Only the remaining budget is passed to the optimizer. If construction has
already consumed the budget, the solver is not started and the result is
`TO` (there is no verified incumbent). The returned `Result.t_total`
includes model construction and optimization time for the exact solver call.

The runner separately records `wall_time`, measured around the subprocess.
Per Experimental Protocol §6.2, use this runner-measured `wall_time` as the
official end-to-end wall-clock metric; retain `t_encode`, `t_solve`, and
`t_total` as solver-reported diagnostic metrics. Do not mix `wall_time`
and `t_total` within the same comparison or PAR2 calculation.

The runner's hard kill at `time_limit + 30 seconds` is only startup/cleanup
grace. It does not grant the optimizer an extra 30 seconds: the solver itself
receives the remaining whole-run budget after model construction.

## Small-instance correctness evidence

`tests/exact/test_exact_solvers.py` compares CP-SAT, Gurobi MIP, CPLEX MIP,
and CPLEX CP with the brute-force oracle on `path4`, `cycle5`, and
`complete5`. These are correctness smoke tests, not benchmark-performance
results. The preflight record reports a local full-suite run of 511 passed
tests; that report is tied to its recorded commit/environment and must be
re-run on the final freeze candidate before tagging `v1.0`.

## Known environment limitations recorded in W3 preflight

- Gurobi Academic: a small license probe passed; this does not prove
  benchmark-scale capacity on the selected official host.
- CPLEX MIP Community Edition: the recorded 1,001-variable / 1,001-constraint
  probe exceeded the Community Edition problem-size limit (error 1016).
- CPLEX CP Community Edition: the recorded 1,001-binary-variable probe
  exceeded the documented 2^1000 search-space limit.
- No CPLEX Academic entitlement has been verified in the preflight record.
  Runs that fail because of license/edition limits must be recorded as
  `ERR` with the reason, not as `TO`.
