# RQ3 official run - raw records handoff (2026-11-28)

Status: batch executed on P3 host. This document records what exists, what deviates
from the protocol, and what is not yet produced. It is not an analysis.

## 1. Provenance

| Item | Value |
|---|---|
| Source commit | `09e8e3b` (`git describe`: `v0.1-contract-268-g09e8e3b`, present in all 120 records) |
| Runner | `python -m src.runner` via `run_rq3.ps1` / `run_rq3_parallel.ps1` |
| Plan | `results/official-plan.csv` (120 rows) |
| Raw records | `results/rq3_official/*.json` (120 files, one per instance x method) |
| Archived attempts | `results/rq3_official/attempt_history/` (5 `sat` attempts with status `MO`) |
| Checkpoints | `results/rq3_official/checkpoints/` (per `run_id`) |
| Seed | `0` |
| Time limit | `1800` s (all 120 records) |
| Memory limit | `12` GiB (all 120 records) |
| Record count | 120, no duplicate `(instance, method)` pair |

## 2. Host

| Item | Actual | Protocol candidate snapshot (docs/experimental_protocol.md 6.3) |
|---|---|---|
| Name | `DESKTOP-K0QBAQP` | - |
| OS | Windows 11 Home Single Language, build `10.0.26300` | build `10.0.26200` |
| CPU | Intel i7-13620H, 10 cores / 16 logical | 12 logical |
| RAM | 15.6 GiB | 15.21 GiB |
| Python | 3.11.15 | 3.11.16 |
| OR-Tools | 9.15.6755 | 9.15.6755 |
| python-sat | 1.9.dev15 | 1.9.dev15 |
| gurobipy | 13.0.3 | 13.0.3 |
| cplex | 22.2.0.0 | 22.2.0.1 |

## 3. Status matrix (120 records)

| Method | OPT | FEAS | TO | MO | Total |
|---|---|---|---|---|---|
| cp_sat | 10 | 14 | 0 | 0 | 24 |
| cplex_cp | 8 | 16 | 0 | 0 | 24 |
| cplex_mip | 1 | 11 | 12 | 0 | 24 |
| gurobi_mip | 5 | 15 | 4 | 0 | 24 |
| sat | 9 | 3 | 0 | 12 | 24 |
| **total** | **33** | **59** | **16** | **12** | **120** |

Usable records: 108. All 12 `MO` records are `sat` runs that raised `MemoryError`
during CNF build on `order` / `pairwise`; `t_total` is 0 for them.

Instances with `sat` = `MO`:

```
494_bus  662_bus  685_bus  can_445  can_715  dwt__503
dwt__592 sherman4 nos6     bcsstk06 bcsstk07 impcol_d
```

The 12 `sat` runs that completed used at most 1114 MB peak (`dwt_234`), so the
pairwise encoding does not fit the 12 GiB cap on the denser instances.

## 4. Protocol deviations (must be resolved by P1 before use)

1. **Host differs from the frozen candidate snapshot.** `docs/experimental_protocol.md`
   6.3 requires stopping before the benchmark when the actual host differs.
   Build, logical CPU count, RAM, Python patch and CPLEX version all differ (section 2).
2. **Three workers ran concurrently for part of the batch.** Records 1-83 were
   produced one at a time; the remainder were produced with up to 3 concurrent
   runner processes. Each worker is single-threaded (`Threads`/`Workers`/
   `num_search_workers` = 1), but 3 concurrent runs at a declared 12 GiB cap
   exceeds physical RAM, which contradicts 6.1 ("số run song song sao cho tổng
   memory limit không vượt RAM vật lý") and 6.3 ("một worker tại một thời điểm").
   `wall_time` of those records may be inflated by memory pressure.
3. **`peak_memory` is only populated for `sat` records.** Exact-solver records
   store `null`; report as unavailable, not as zero.

## 5. Not produced yet

- `results/runs.csv` export validated from raw JSON. No exporter exists in the
  repository at `09e8e3b`; `src/runner/schema.py` only defines `RUN_FIELDS`.
- The 10-run Exact spot-check in `docs/p1/exact_spot_check_plan.md` has not been run
  against these records.

## 6. Reproduce

```powershell
cd C:\Users\ducqu\workspace\ABP-rq3
.\run_rq3.ps1              # sequential, original
.\run_rq3_parallel.ps1     # same plan, max 3 concurrent workers
```

Both scripts archive `MO` records to `attempt_history/` on start and pass
`--resume` to the runner.
