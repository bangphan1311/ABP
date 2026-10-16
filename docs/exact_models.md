# Exact formulations for ABP (W2 draft)

Given an undirected graph `G=(V,E)`, `n=|V|`, assign each vertex an integer label
`x_v` in `1..n` and maximize the minimum label distance over all edges.

## Common optimization model

Maximize integer `K`, subject to:

- `x_v in {1, ..., n}` for every vertex;
- labels are all different (equivalently, the labels form a permutation of `1..n`);
- `|x_u - x_v| >= K` for each edge `(u,v)`;
- `K in {1, ..., n-1}` for a graph with at least one edge and at least two vertices.

## Gurobi MIP and CPLEX MIP

Use integer label variables `x_v`, integer objective variable `K`, and binary orientation
variables. For every vertex pair `i<j`, one binary chooses either `x_i+1 <= x_j`
or `x_j+1 <= x_i`, guaranteeing distinct labels. For every edge `(u,v)`, one binary
chooses either `x_u-x_v >= K` or `x_v-x_u >= K`. The implications are represented
with indicator constraints; no manually selected big-M constant is used.

## CPLEX CP

Use integer variables `x_v`, a global `all_diff(x)` constraint, and for each edge
`abs(x_u-x_v) >= K`. Maximize `K`.

## Result semantics

Every returned incumbent is checked using the shared `verify(instance, labeling)`.
`OPT` is returned only for a solver's proven-optimal status. A valid incumbent without
an optimality proof is `FEAS`; a time limit with no verified incumbent is `TO`;
execution, backend, and licensing errors are `ERR`. For non-optimal feasible runs,
`ub` records an available solver bound when possible, otherwise the safe generic bound
`n-1` is used.

## Small-instance validation

`tests/exact/test_exact_solvers.py` compares CP-SAT, Gurobi MIP, CPLEX MIP, and CPLEX CP
against the brute-force oracle on `path4`, `cycle5`, and `complete5`. These are correctness
smoke tests, not official performance benchmark results.


## Timing and memory-limit scope

`t_encode` measures model construction only; importing a backend and validating the input are outside this measurement. `t_solve` measures the solver call. `t_total` includes backend import, validation, model construction, and solving within the solver function. The runner's wall-clock time is a separate end-to-end measure.

The current exact solver functions do **not** enforce `Config.memory_limit`. The field is retained in the shared run contract, but a comparable hard memory ceiling must be enforced by the process supervisor/runner for every backend. Do not describe `memory_limit` as enforced, and do not use it as an official experimental control until that supervisor-level enforcement is implemented and tested. Backend-specific parameters such as Gurobi's `SoftMemLimit` and CPLEX's `WorkMem` have different semantics and should not be treated as equivalent caps. Native Gurobi/CPLEX memory-limit stops and Python `MemoryError` are normalized to `MO`; a verified incumbent is preserved when the backend exposes one.
