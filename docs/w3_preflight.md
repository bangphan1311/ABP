# W3 preflight — ABP Harwell–Boeing

**State at preparation time:** `PARTIAL / NOT READY TO FREEZE`  
**Owner:** P1 (coordinator)  
**Branch target:** `p1/w3-experimental-protocol-rc`  
**Purpose:** record independently checkable evidence and leave unverified fields empty. This file is not proof that all benchmark prerequisites are satisfied.

## 1. Evidence summary

| Item | State | Evidence / note |
|---|---|---|
| Official dataset definition | `CONFIRMED_FROM_SOURCE` | Optsicom describes 24 Harwell–Boeing ABP graphs, 12 smaller and 12 larger; it defines an edge from a nonzero matrix entry. [Optsicom ABP page](https://grafo.etsii.urjc.es/optsicom/abp.html) |
| Canonical archive URL | `SOURCE_LINK_CONFIRMED; DOWNLOAD_NOT_COMPLETED_HERE` | [hb.zip](https://grafo.etsii.urjc.es/optsicom/abp/hb.zip), linked from Optsicom. The execution environment used to prepare this preflight could not resolve/download the archive; no claim is made that the 24 raw files were downloaded. |
| Repository input files | `NOT_PRESENT_ON_GITHUB_AT_CHECK` | The `main` branch `benchmark/` directory contained `.gitkeep` and `toy/`; `benchmark/hb/` was not present. This says nothing about untracked files on an individual's Windows machine. |
| 24-row instance inventory | `REFERENCE_INVENTORY_PREPARED` | `benchmark/hb/instances.csv`; `n,m` are cross-referenced to Table 1 of Sinnl (2021); `ab_lb_ref`/`ab_ub_ref` reproduce historical best-solution/upper-bound values in the appendix table reproducing Lozano et al. (2012). These are reference values, not measurements read from the local `.mtx.rnd` files. [Sinnl, 2021](https://link.springer.com/article/10.1007/s10100-020-00688-4) |
| Literature ABP bounds | `REFERENCE_VALUES_ONLY` | `ab_lb_ref` is the published best-known feasible value and `ab_ub_ref` is a published upper bound reproduced in the ABP literature. They are checks, not certified optimum values. [Sinnl, 2021 / reproduced Lozano et al. table](https://link.springer.com/article/10.1007/s10100-020-00688-4) |
| File hashes / headers / cleaned edge counts | `PENDING_RAW_FILES` | No SHA-256 or header values are supplied until the actual archive files are present. Run `python scripts/inspect_hb.py` afterward. |
| Maximum degree `Δ` and `UB = n − Δ` | `PENDING_RAW_FILES` | Not computable from published `n,m` alone. Do not infer degree distribution from matrix dimensions or edge count. The inspector fills these only from actual edge rows. |
| Solver license on official run machine | `NOT_CHECKED` | A historical tooling note records one contributor's venv without Gurobi/CPLEX/DOcplex installed; this is not a fresh test of the official machine and does not prove license state. Run `python scripts/w3_preflight_env.py --probe-solvers` locally. |
| Official machine CPU/RAM/OS/Python | `NOT_RECHECKED_ON_OFFICIAL_HOST` | Historical notes from the project mention Ryzen 5 7535HS, about 15.2 GB RAM, and Python 3.11.17; these are not treated as a current machine probe. The runtime snapshot script records actual current values locally. |
| Hard memory limit | `BLOCKER_IN_CODE` | The runner accepts `--memory-limit`, but current SAT code warns that `memory_limit` is ignored; catching Python `MemoryError` is not OS-level process memory enforcement. See current `src/sat/solve.py` and `src/runner/worker.py`. |
| Safe resume/checkpoint | `BLOCKER_IN_CODE` | Current `src/runner/runner.py` reuses any existing JSON for a run ID without validation; a hard kill returns `TO` without a saved incumbent checkpoint. Needs implementation and tests before freeze. |
| Exact-solver time accounting | `BLOCKER_REQUIRES_TEST` | CPLEX MIP, CPLEX CP and CP-SAT set search limits after model construction; Gurobi sets its limit before construction but still gives the optimizer the full limit after build. None deducts build time from total `t_total` consistently. Fix and test before official runs. |
| CNF estimate / plan-only dry-run | `TOOLS_ADDED; TARGET RUN PENDING` | `scripts/estimate_hb_cnf.py` computes formula-only counts from published reference `n,m`; it does not allocate a full CNF or estimate peak RAM. `scripts/dry_run_benchmark.py` checks the protocol run matrix and raw-file presence but is **not** the execution queue and launches no solvers. A queue-level dry-run integrated with the runner remains pending. For `can__715`, formulas at `K=n−1` predict an extremely large CNF; do not build that full CNF until process memory limiting has been tested. |

## 2. Data download and verification workflow

1. Open the [official Optsicom ABP page](https://grafo.etsii.urjc.es/optsicom/abp.html) and use its linked `hb.zip`. Preserve the original archive for provenance; record the downloaded archive's SHA-256 locally.
2. Extract the **ABP graph edge-list files** to `benchmark/hb/raw/`. Do not rename a MatrixMarket source matrix or other dataset to `.mtx.rnd` to make it appear to match. Expected canonical filenames are listed in `instances.csv` (including names with double underscores such as `dwt__234.mtx.rnd` and `can__715.mtx.rnd`).
3. Run:

   ```powershell
   python scripts/inspect_hb.py
   ```

   The script creates/replaces `benchmark/hb/MANIFEST.csv`. `MISSING`, `INVALID_FORMAT`, `REFERENCE_MISMATCH` and `INVALID_GRAPH` are not passes. `VALID_WITH_CLEANING` records that the actual file had self-loops or duplicate undirected edges that the graph loader would remove; review each such case rather than hiding it.
4. Only accept the actual-file metrics if all 24 rows have valid status and the `n`/header `m` values agree with their published references or every discrepancy is investigated and documented. Compare `m_header`, physical row count, `m_clean`, removed loops/duplicates, `Δ`, and `UB=n−Δ` separately.
5. Keep `instances.csv` as source reference metadata; keep file-derived evidence in `MANIFEST.csv`. Never copy `n,m_table` into `n_header,m_header,m_clean` as a placeholder.

## 3. Current reference table and unknown metrics

`benchmark/hb/instances.csv` contains published reference `n,m` and historical lower/upper ABP bounds. `MANIFEST.csv` carries `n_reference` and `m_reference` beside the file-derived fields. It deliberately leaves `Δ` and computed `UB=n−Δ` blank because raw edge files have not been verified here; they remain blank in `MISSING` rows until actual files are inspected.

Source table facts: there are 12 small instances (`n` from 30 to 118) and 12 large instances (`n` from 420 to 715); the largest published graph `can__715` is listed as `n=715, m=2975`. This is an estimate-input from literature, not proof of the corresponding local file contents.

## 4. CNF size estimate warning

Run a formula-only estimate without constructing the full formula:

```powershell
python scripts/estimate_hb_cnf.py --name can__715
```

For the published references `n=715,m=2975`, `K=714`, the script's closed-form counts are:

- Pairwise ABP + pairwise AMO: 511,225 primary variables and 1,883,777,380 clauses.
- Order encoding: 510,510 variables and 1,701,778,420 clauses.
- Pairwise ABP + sequential-counter AMO: full AMO/auxiliary totals require the installed PySAT encoder; the estimate reports unknown if PySAT cannot be imported. The distance-clause count under this formula is still 1,518,761,300.

These are **worst-case formula counts** from published reference `n,m`, assuming `K=n−1`; they are not measured CNF sizes from raw files, not solver results, and not a peak-memory estimate. Actual pilot probes use the solver's K path; do not treat this as a recommendation to build or solve the full largest-instance CNF without a tested memory cap.

## 5. Machine and solver inventory

Run on the intended official benchmark machine, inside the environment that will run the project:

```powershell
python scripts/w3_preflight_env.py > docs/w3_preflight_environment.json
python scripts/w3_preflight_env.py --probe-solvers > docs/w3_solver_probe.json
```

The first file records Python executable/version, OS, architecture, processor string, logical CPU count, physical RAM where detectable, installed package versions, and relevant executables on `PATH`. The second also runs tiny smoke models for CP-SAT, CaDiCaL, Glucose, Gurobi MIP, CPLEX MIP, and CP Optimizer. A tiny solver pass proves only that this small model ran; it does not establish support for a large model or the license's full size/usage entitlement. Never put license keys, passwords, tokens, or environment dumps into the repo.

Current repository dependency facts from `main`: `pyproject.toml` has `dependencies = []`; `requirements.txt` pins OR-Tools, Gurobi, CPLEX, DOcplex, PySAT, and pytest. Dependency pins do not establish that a package is installed or licensed on the machine.

## 6. Solver and runner risks visible in the repository

- `kissat404` through PySAT has historical repo evidence of ignored assumptions, invalid models and crashes on Windows; do **not** use it for RQ2. A native Kissat binary has not been verified. Scope RQ2 to CaDiCaL and Glucose unless a separate binary passes correctness tests.
- Current runner's `resume=True` reads and returns existing JSON when present, without schema/config/solution validation. Needs a safe-resume fix.
- The hard-timeout path records `TO` and cannot recover an incumbent after the worker is killed. Needs checkpoint/audit trail or explicitly documented behavior before freeze.
- `memory_limit` is not an actual OS-level memory cap in the current SAT/runner path. Do not run pilot-large expecting `MO` enforcement until this is implemented and tested on the target OS.
- Exact solvers do not consistently deduct build time from the optimizer allowance: CPLEX MIP, CPLEX CP and CP-SAT set limits after building, while Gurobi allows the full optimizer limit after building. The total budget must account for build time before official runs.
- These are source-code findings, not proof of which backend/license is available on the target machine today.

## 7. Freeze-readiness conclusion

**Not ready for `v1.0` at this point.** The official source and published inventory are identified, and tooling now exists to verify actual files and collect the target environment. The actual 24 raw files, SHA-256 manifest, `Δ`/computed `UB`, fresh solver-license probes, dry-run on the target host, hard memory enforcement, and checkpoint/resume tests remain pending. Keep all unknown actual-file and official-machine fields empty or explicitly pending until evidence is committed.
