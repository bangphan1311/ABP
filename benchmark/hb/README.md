# Harwell–Boeing ABP benchmark inputs

## Canonical source

The Optsicom Antibandwidth Problem page describes the Harwell–Boeing benchmark as 24 graphs (12 smaller and 12 larger), derived from matrices by treating nonzero matrix entries as graph edges:

- Dataset page: https://grafo.etsii.urjc.es/optsicom/abp.html
- Download URL linked from that page: https://grafo.etsii.urjc.es/optsicom/abp/hb.zip

The official archive was downloaded and its 24 `.mtx.rnd` files were validated locally on 2026-10-27. The downloaded ZIP SHA-256 is `C7B39A13A37707A09F36408273DB75D6A8BC1CB40E071AC960C724E1F58F6E7E`. The raw payloads remain local under `benchmark/hb/raw/` and are not committed to Git. `MANIFEST.csv` records the SHA-256 and graph measurements of each file. To reproduce the validation, download the official archive from the URL above, extract the 24 graph files to `benchmark/hb/raw/`, and run `python scripts/inspect_hb.py`.

## What `instances.csv` and `MANIFEST.csv` mean

`instances.csv` is the source inventory of 24 canonical names with **published reference values** for `n`, edge count `m_table`, and historical literature ABP bounds. These are reference numbers only—not measurements from raw files. The references are cross-checked against Sinnl (2021), Table 1 and its appendix reproduction of Lozano et al. (2012): https://link.springer.com/article/10.1007/s10100-020-00688-4.

`MANIFEST.csv` carries both reference columns and separate file-derived fields. Right now each row is `MISSING`; `sha256`, header values, cleaned edge counts, `delta_max`, and `ub_n_minus_delta` remain blank until the matching raw file exists.

## Download, inspect, and plan commands

Extract only the ABP graph edge-list files to `benchmark/hb/raw/`. Do not rename MatrixMarket `.mtx`/`.mtx.gz` files to `.mtx.rnd`. Then run:

```powershell
python scripts/inspect_hb.py
python scripts/dry_run_benchmark.py --stage pilot-rq1 --output results/pilot-rq1-plan.csv
python scripts/dry_run_benchmark.py --stage pilot-exact --output results/pilot-exact-plan.csv
python scripts/dry_run_benchmark.py --stage pilot-large --output results/pilot-large-plan.csv
python scripts/dry_run_benchmark.py --stage official --output results/official-plan.csv
python scripts/estimate_hb_cnf.py --name can__715
```

`inspect_hb.py` is the real-file validator; it computes SHA-256 and checks the expected `n n m` header, edge row count, endpoints, self-loops and duplicate undirected edges. It then computes `m_clean`, `delta_max = max(degree(v))`, and `UB_degree = n − delta_max`. This header convention is the protocol's expectation and must be confirmed against the archive; an `INVALID_FORMAT` result is evidence to investigate, not a reason to rename or rewrite the file.

`dry_run_benchmark.py` is a **plan-only matrix checker**, not the execution queue and not a solver test. It checks run counts and duplicate plan IDs, reports whether raw input files exist, leaves canonical SAT config pending until provided, and does not launch a solver or enforce a memory cap. `estimate_hb_cnf.py` produces formula-only clause/variable counts from published `n,m`; it does not allocate the full CNF or estimate peak RAM.

Keep actual file-derived evidence separate from `instances.csv`: never copy reference `n,m_table` into `n_header`, `m_header`, or `m_clean` as a placeholder.
