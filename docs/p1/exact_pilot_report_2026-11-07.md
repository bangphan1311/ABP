# Exact Pilot Report — HB Validation Subset

**Run date:** 2026-11-07 (CSV timestamps: 2026-11-06T03:36:00Z through 2026-11-07T03:06:51Z)  
**Owner:** P1  
**Scope:** 10 locked validation instances × 4 exact backends = 40 runs  
**Classification:** completed engineering pilot; **not** the official RQ3 benchmark  
**Recorded runner revision:** `v0.1-contract-179-g6445ec9`

## 1. Execution configuration

| Setting | Recorded value |
|---|---|
| Host | `WINDOW-DEVICE-2022` |
| OS build | Windows `10.0.26200` |
| Physical RAM | 15.21 GiB |
| Workers | 1 (sequential) |
| Configured memory cap | 12.0 GiB |
| Per-run time limit | 600 s |
| Resume | Enabled |
| Planned / completed | 40 / 40 |

The branch `p1/w3-experimental-protocol-rc` contains all 40 individual raw JSON records under `results/pilot_exact/raw/` and the derived `results/pilot_exact/summary.csv`; the directory was checked on GitHub and contains exactly 40 JSON files. Preserve these original attempts as immutable audit evidence.

## 2. Overall outcomes

| Exact backend | OPT | FEAS | ERR | Completed |
|---|---:|---:|---:|---:|
| CP-SAT | 6 | 4 | 0 | 10 |
| Gurobi MIP | 0 | 1 | 9 | 10 |
| CPLEX MIP | 0 | 0 | 10 | 10 |
| CPLEX CP | 5 | 5 | 0 | 10 |
| **Total** | **11** | **10** | **19** | **40** |

No run was reported as `TO` or `MO`. The 10 `FEAS` records retain verified incumbents but do not establish optimality. The 19 `ERR` records are license/edition failures, not timeouts:

- Gurobi MIP: 9 `Model too large for size-limited license` errors; only `pores_1` returned a feasible incumbent (`lb=6, ub=8`).
- CPLEX MIP: 10 CPLEX error 1016 Community Edition problem-size-limit failures.
- CP-SAT and CPLEX CP completed all 10 instance runs.

Do not interpret the Gurobi/CPLEX MIP `ERR` counts as evidence of algorithmic weakness. They show that the currently installed license editions prevented those formulations from being evaluated on most or all of this subset.

## 3. Instance-level outcomes

Each cell is `STATUS (lb, ub)`; `ERR` means the backend did not produce a usable bound pair because execution was blocked by its license.

| Instance | CP-SAT | Gurobi MIP | CPLEX MIP | CPLEX CP |
|---|---|---|---|---|
| `pores_1` | OPT (6, 6) | FEAS (6, 8) | ERR | FEAS (6, 10) |
| `bcsstk01` | OPT (9, 9) | ERR | ERR | OPT (9, 9) |
| `bcspwr02` | OPT (21, 21) | ERR | ERR | OPT (21, 21) |
| `curtis54` | OPT (13, 13) | ERR | ERR | OPT (13, 13) |
| `will57` | OPT (13, 13) | ERR | ERR | OPT (13, 13) |
| `impcol_b` | OPT (8, 8) | ERR | ERR | FEAS (8, 22) |
| `ash85` | FEAS (21, 84) | ERR | ERR | FEAS (21, 35) |
| `nos4` | FEAS (31, 98) | ERR | ERR | FEAS (34, 47) |
| `dwt_234` | FEAS (38, 115) | ERR | ERR | FEAS (51, 58) |
| `bcspwr03` | FEAS (38, 76) | ERR | ERR | OPT (39, 39) |

The `lb/ub` pairs above are the values recorded by the runner for each method. In particular, a `FEAS` row must not be described as an optimum. The degree-based bound `n - Δ` documented in `docs/exact_models.md` is a separate safe external bound and is not asserted to have been injected into every exact model.


## 4. PAR2 under the frozen pilot rule

Experimental Protocol §9.2 assigns a 1,200 s penalty to every non-OPT exact-pilot run (including FEAS, TO, MO, ERR and an unreplaced missing run). OPT runs contribute their recorded runner `wall_time`.

| Exact backend | OPT wall-time sum (s) | Non-OPT runs | PAR2 (s) |
|---|---:|---:|---:|
| CP-SAT | 127.012 | 4 | 4,927.012 |
| Gurobi MIP | 0.000 | 10 | 12,000.000 |
| CPLEX MIP | 0.000 | 10 | 12,000.000 |
| CPLEX CP | 45.805 | 5 | 6,045.805 |

The computed values apply the protocol formula literally. Because Gurobi MIP and CPLEX MIP are predominantly or entirely blocked by the installed license editions, their PAR2 values are audit results under the protocol's penalty rule, **not an isolated measure of intrinsic solver speed or formulation quality**. Do not use this table alone to rank the mathematical formulations.

## 5. Interpretation and limitations

1. **Proof coverage:** CP-SAT proved optimality on 6/10 validation instances; CPLEX CP proved optimality on 5/10. The pilot alone is not a statistically broad performance comparison.
2. **Incumbent coverage:** both CP-SAT and CPLEX CP returned verified feasible incumbents on all 10 instances. Gurobi returned one feasible incumbent before its remaining nine runs were blocked by the size-limited license. CPLEX MIP returned no usable run under the installed Community Edition.
3. **Time-limited cases:** the 10 `FEAS` cases reached approximately the 600-second run budget while retaining a verified incumbent. They remain `FEAS`, not `OPT` or `TO`.
4. **License limitations:** CPLEX MIP's 10 errors and Gurobi MIP's 9 errors must be disclosed as environment/license constraints. Do not compare their error totals as solver performance, and do not relabel them as `TO`.
5. **Scope:** the subset pilot checks formulation, entitlement, runtime and incumbent behavior. It does not replace the 24-instance official benchmark, does not close the protocol freeze gates, and does not authorize claiming final RQ3 conclusions.

## 6. Required follow-up

- Preserve all 40 raw JSON attempts and the generated summary CSV as audit evidence; do not overwrite or discard the original attempts.
- Decide with the team whether an academic/appropriately sized Gurobi and CPLEX entitlement can be made available. If not, retain the recorded failures and state the resulting comparison limitation.
- P1 should independently verify the selected exact raw runs and investigate every anomalous result before the official run. P3 remains responsible for operating the official benchmark queue.
- Keep protocol version `1.0-rc` until every freeze gate in `docs/experimental_protocol.md` §12 is evidenced and reviewed; this pilot is not a freeze sign-off.
