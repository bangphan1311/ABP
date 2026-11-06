# P1 W4 — Exact run spot-check plan

**Prepared:** 2026-11-06, before official outcomes are inspected  
**Owner:** P1  
**Sampling rule:** fixed stratified sample; every exact method is represented,
and both small and large HB tiers are included. The list is frozen before
official results so P1 cannot select only successful or suspicious runs.

## Frozen configuration used to derive run IDs

- Methods: `cp_sat`, `gurobi_mip`, `cplex_mip`, `cplex_cp`
- `time_limit = 1800.0` seconds
- `memory_limit = 12.0` GiB
- `seed = 0`; `symmetry = false`; `warm_start = false`
- Exact-only fields `abp_encoding`, `amo_encoding`, `sat_solver`,
  `search_mode` are null.
- Run ID format matches `src.runner.schema.make_run_id()`.

## Frozen sample (10 exact runs)

| # | Tier | Instance | Method | Run ID |
|---:|---|---|---|---|
| 1 | small | `pores_1` | `cp_sat` | `pores_1__cp_sat__na__na__na__na__sym0__ws0__s0__tl1800.0__ml12.0` |
| 2 | large | `can__715` | `cp_sat` | `can__715__cp_sat__na__na__na__na__sym0__ws0__s0__tl1800.0__ml12.0` |
| 3 | small | `will57` | `cp_sat` | `will57__cp_sat__na__na__na__na__sym0__ws0__s0__tl1800.0__ml12.0` |
| 4 | small | `bcsstk01` | `gurobi_mip` | `bcsstk01__gurobi_mip__na__na__na__na__sym0__ws0__s0__tl1800.0__ml12.0` |
| 5 | large | `can__445` | `gurobi_mip` | `can__445__gurobi_mip__na__na__na__na__sym0__ws0__s0__tl1800.0__ml12.0` |
| 6 | small | `bcspwr02` | `cplex_mip` | `bcspwr02__cplex_mip__na__na__na__na__sym0__ws0__s0__tl1800.0__ml12.0` |
| 7 | large | `bcsstk07` | `cplex_mip` | `bcsstk07__cplex_mip__na__na__na__na__sym0__ws0__s0__tl1800.0__ml12.0` |
| 8 | small | `ash85` | `cplex_cp` | `ash85__cplex_cp__na__na__na__na__sym0__ws0__s0__tl1800.0__ml12.0` |
| 9 | large | `685_bus` | `cplex_cp` | `685_bus__cplex_cp__na__na__na__na__sym0__ws0__s0__tl1800.0__ml12.0` |
| 10 | small | `nos4` | `cplex_cp` | `nos4__cplex_cp__na__na__na__na__sym0__ws0__s0__tl1800.0__ml12.0` |

## Inspection procedure

For each selected run, P1 will read the raw JSON (not only `runs.csv`),
reconstruct the source instance through the manifest-checked loader, call
`verify(instance, solution)` independently, compare the recomputed objective
with `lb` and the solver objective, check `lb ≤ ub`, validate `OPT`
certificate/status semantics, and inspect `wall_time`, license, memory and
error metadata. For `ERR` caused by CPLEX Community Edition, verify the raw
reason and retain the record; do not reinterpret it as a timeout.

This sample is additive to every anomaly investigation. Any result with
invalid solution, objective mismatch, contradictory bounds, or unexplained
status must be checked even when it is not in the ten-run sample.
