# Canonical SAT configuration — proposal (W3, issue #18 / #25)

Status: proposed by P2, to be confirmed by P1/P3 before M2 freeze.
Decision is taken **before any official run**: only the two W3 pilots
(`results/pilot_rq1.csv`, `results/pilot_rq2.csv`) were read. No RQ3 / official
result exists yet, and none was inspected.

## Proposal

| Field | Value |
|---|---|
| `method` | `sat` |
| `abp_encoding` | `order` |
| `amo_encoding` | `pairwise` |
| `sat_solver` | `minisat22` |
| `search_mode` | `multi` |
| `symmetry` | `false` |
| `warm_start` | `false` |
| `seed` | `0` |
| `memory_limit` | `null` (not implemented, see review notes §4) |

Concretely, the canonical run is

```python
Config(
    method="sat",
    abp_encoding="order",
    amo_encoding="pairwise",
    sat_solver="minisat22",
    search_mode="multi",
    symmetry=False,
    warm_start=False,
    seed=0,
    time_limit=<protocol value>,
)
```

Selection order was fixed before the runs: **coverage first** (count of OPT at the
pilot time limit), **then total runtime** on instances solved by all candidates,
**then** CNF size (`variables`, `clauses`) and `peak_memory`. Instances:
`benchmark/validation/` (8 graphs, `n = 8..28`) plus `benchmark/large/` (2 graphs,
`n = 40, 50`), both seeded by `experiments/make_validation_subset.py`
(`seed = 20261026`). Time limit 60 s per run, one run per cell (no repetitions).

## RQ1 — encoding × AMO (`results/pilot_rq1.csv`)

Fixed: `cadical195`, `search_mode = multi`, `symmetry = false`,
`warm_start = false`. 10 instances × 4 configs = 40 runs.

| `abp_encoding` / `amo_encoding` | OPT | FEAS | TO | Σ `t_total` (s) | max `peak_memory` (MB) | max `variables` | max `clauses` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `order` / `pairwise` | 10 | 0 | 0 | **23.24** | 111.4 | 2 450 | 196 450 |
| `order` / `seqcounter` | 10 | 0 | 0 | 23.12 | 113.0 | 2 450 | 196 450 |
| `pairwise` / `pairwise` | 9 | 1 | 0 | 86.43 | 126.5 | 2 500 | 255 400 |
| `pairwise` / `seqcounter` | 9 | 1 | 0 | 88.50 | 87.6 | 7 400 | 147 500 |

Sizes per instance (`variables`/`clauses`; the order encoding has no AMO group, so
both AMO values give identical rows):

| `n` | `order` var/cls | `pairwise`/`pairwise` var/cls | `pairwise`/`seqcounter` var/cls |
|---:|---|---|---|
| 8 | 56 / 496 | 64 / 688 | 176 / 560 |
| 10 | 90 / 1 210 | 100 / 1 600 | 280 / 1 220 |
| 12 | 132 / 2 352 | 144 / 3 048 | 408 / 2 232 |
| 14 | 182 / 4 018 | 196 / 5 152 | 560 / 3 668 |
| 16 | 240 / 5 600 | 256 / 7 328 | 736 / 4 896 |
| 20 | 380 / 12 080 | 400 / 15 560 | 1 160 / 10 200 |
| 24 | 552 / 20 592 | 576 / 26 736 | 1 680 / 16 752 |
| 28 | 756 / 34 496 | 784 / 44 408 | 2 296 / 27 720 |
| 40 | 1 560 / 105 520 | 1 600 / 135 280 | 4 720 / 82 160 |
| 50 | 2 450 / 196 450 | 2 500 / 255 400 | 7 400 / 147 500 |

**`abp_encoding = order`, rationale.**

* Coverage: 10/10 OPT for both `order` rows; `pairwise` loses `randconn40` to
  FEAS in both AMO variants (`lb = 14`, `ub = 39`, i.e. the timeout bound is the
  trivial counting bound, not a tight one). Coverage is the primary criterion, so
  this alone decides the axis.
* Runtime: total 23.24 s vs 86.43 s; per instance `order` is faster from `n = 20`
  upward, e.g. `n = 28` 1.30 s vs 6.43 s and `n = 40` 16.25 s vs 72.67 s
  (the latter exceeds the 60 s limit because the CaDiCaL conflict-budget loop
  overshoots its deadline).
* Size: mean clause ratio `order/pairwise` = 0.77 (range 0.72–0.78 over all 10
  instances); `variables` are `n(n-1)` vs `n²`. `order` is smaller on every
  instance in the pilot.
* `peak_memory`: 111.4 MB max vs 126.5 MB.

Early-warning thresholds (variables > 200 000, `t_encode` > 5 s) never fired in
the pilot: the largest CNF has 2 500 variables / 255 400 clauses and the slowest
encode is 1.6 s. That is a statement about this subset only; the thresholds stay
as CLI flags (`--max-vars`, `--slow-encode`) for larger tiers.

**`amo_encoding = pairwise`, rationale.**

* For `abp_encoding = order` the AMO axis is inert: the monotone chain replaces
  ALO + AMO (`src/sat/order.py:19-21`), so `pairwise` and `seqcounter` produce
  byte-identical clause/variable counts and the same status and optimum. The two
  rows differ only in timing noise (23.24 s vs 23.12 s), which is the expected
  consistency check, not evidence for either encoder.
* Given the tie, `pairwise` keeps the default, adds no auxiliary variables, and
  is the cheaper encoding to explain in the appendix.
* Recorded for completeness (does **not** change the choice): inside the
  `pairwise` encoding, `seqcounter` trades variables for clauses (e.g. `n = 50`:
  7 400 vars / 147 500 clauses vs 2 500 / 255 400) and is faster at mid sizes
  (`n = 28`: 2.22 s vs 6.43 s) but slower at `n = 50` (6.86 s vs 5.28 s); both
  AMO variants fail `randconn40` the same way.

## RQ2 — solver (`results/pilot_rq2.csv`)

Fixed encoding pair = the RQ1 winner `order` / `pairwise`; 10 instances × 4
solvers = 40 runs. Kissat is excluded by design (see below).

| Solver | OPT | FEAS | TO | MO | ERR | Σ `t_total` (s) | Σ `t_solve` (s) | max `peak_memory` (MB) | instances best |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `minisat22` | 10 | 0 | 0 | 0 | 0 | **16.61** | 11.56 | 99.3 | 10/10 |
| `glucose4` | 10 | 0 | 0 | 0 | 0 | 17.13 | 12.06 | 100.3 | 0/10 |
| `glucose42` | 10 | 0 | 0 | 0 | 0 | 17.49 | 12.45 | 99.9 | 0/10 |
| `cadical195` | 10 | 0 | 0 | 0 | 0 | 23.24 | 17.56 | 111.4 | 0/10 |

Per-instance `t_total` (s); `minisat22` is fastest on every instance:

| `n` | minisat22 | glucose4 | glucose42 | cadical195 |
|---:|---:|---:|---:|---:|
| 8 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10 | 0.00 | 0.00 | 0.00 | 0.01 |
| 12 | 0.01 | 0.01 | 0.01 | 0.01 |
| 14 | 0.02 | 0.02 | 0.02 | 0.03 |
| 16 | 0.03 | 0.03 | 0.03 | 0.03 |
| 20 | 0.11 | 0.12 | 0.12 | 0.15 |
| 24 | 0.44 | 0.45 | 0.52 | 0.70 |
| 28 | 0.87 | 0.91 | 0.89 | 1.30 |
| 40 | 11.02 | 11.46 | 11.13 | 16.25 |
| 50 | 4.11 | 4.12 | 4.76 | 4.76 |

**`sat_solver = minisat22`, rationale.**

* Coverage: all four solvers reach OPT on all 10 instances (40/40 OPT); no
  differentiator, so runtime decides per the pre-registered order.
* Runtime: lowest total (16.61 s) and fastest on every single instance. Margins
  are small at the two largest instances (`n = 40`: 11.02 vs 11.13 s for
  `glucose42`; `n = 50`: 4.11 vs 4.12 s for `glucose4`), so the choice is
  "no solver is worse, one is never slower" rather than a large effect.
* Memory: 99.3 MB max, lowest of the four.
* Caveat to record with the result: `cadical195` runs through the
  conflict-budget timeout loop (`src/sat/backend.py:238-254`), which adds
  per-round overhead; its gap therefore mixes solver speed with wrapper
  overhead. This is a property of the implementation, not of CaDiCaL alone.
* Caveat to record with the result: the pilot produced no timeout under
  `order`, so the solver choice is decided on instances that all finish within
  60 s. Its timeout path was checked separately: at a 3 s limit on
  `randconn40` with `order`, `minisat22` returns FEAS (`lb = 13`,
  `t_total = 3.01 s`) like the other two families — no overshoot, no error.
* Risk accepted at freeze: a solver that is better only on hard instances would
  not be visible here. Re-deciding the solver after seeing official runs is not
  allowed; if P1/P3 prefer robustness on known-hard instances, that must be
  stated now, not after RQ2 final.

**Kissat.** Not a candidate. Through PySAT `kissat404` gives wrong models,
silently ignores assumptions and aborts the process after `add_clause`; there is
no external `kissat` binary on `PATH` (`docs/sat_tooling.md`, section "Kissat";
`src/sat/backend.py:44-53`, `src/sat/solve.py:383-391`). The RQ2 grid refuses any
kissat-family name and the CLI prints the exclusion note on start
(`experiments/pilot_rq2.py`). No "Kissat: not installed" row should appear in
the paper tables. No anomaly line was printed in this pilot: 40/40 runs are OPT
with no warning and no error, so there is nothing to classify.

## Fixed axes

* `search_mode = multi`: the K-search loop `K ← B + 1` from a verified lower
  bound, stopping at the first UNSAT, is the only implemented mode
  (`src/sat/solve.py:168-218`). Completeness argument:
  `docs/technical_appendix_draft.md` A.5. Note `Config.search_mode` is currently
  in `IGNORED_CONFIG_FIELDS` and warns when set to `"multi"`
  (`src/sat/solve.py:39-67`); the warning text is stale, the setting is
  nonetheless what the loop does (review notes §2).
* `symmetry = false`, `warm_start = false`: not implemented
  (`src/sat/solve.py:39-45`); they must be reported as "off by design", not as
  "tested and found not to help".
* `seed = 0`: no stochastic component in encoding or search; the field only
  appears in the run id.

## Consequences for the official run

1. All four pilot solvers are available here, so no environment dependency
   beyond `python-sat` for the canonical config.
2. Expect the canonical config to be dominated by the K-search loop, not by a
   single hard threshold: probes per run were 2 (`n = 8`) to 17 (`n = 50`) in the
   pilots, and `t_encode`/`t_solve` in `Result` are sums over the whole chain.
3. FEAS rows carry a loose `ub`: when the run times out before any UNSAT,
   `ub = hi - 1` is still the counting bound `n - 1` (e.g. `randconn40`:
   `lb = 14, ub = 39`). Report FEAS bounds as bounds, not as near-optimal gaps.
4. `time_limit` is a budget for the whole K chain, and the CaDiCaL budget loop can
   overshoot it (72.67 s observed at a 60 s limit for
   `pairwise/pairwise` on `n = 40`). If the protocol needs a hard wall-clock
   ceiling per run, that must be enforced by the runner, not by the solver.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m experiments.make_validation_subset
.\.venv\Scripts\python.exe -m experiments.pilot_rq1 --time-limit 60
.\.venv\Scripts\python.exe -m experiments.pilot_rq2 --abp-encoding order --amo-encoding pairwise --time-limit 60
```

Raw records for every cell are in `results/raw/` (resume-safe, one JSON per
`run_id`); the two CSVs are committed.
