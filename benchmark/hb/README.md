# Harwell–Boeing ABP benchmark inputs

## Canonical source

The Optsicom Antibandwidth Problem page describes the Harwell–Boeing benchmark as 24 graphs (12 smaller and 12 larger) and links its `hb.zip` download:

- Dataset page: https://grafo.etsii.urjc.es/optsicom/abp.html
- Download URL linked from that page: https://grafo.etsii.urjc.es/optsicom/abp/hb.zip

Download the archive through a browser and extract the 24 selected `.mtx.rnd` files into `benchmark/hb/raw/`. Do not substitute the raw MatrixMarket `.mtx.gz` files: the ABP experiment expects graph edge-list files and their own validated header/edge conventions.

## What the CSV means

`instances.csv` contains canonical names plus **published reference values** for `n`, edge count `m_table`, and literature bounds `ab_lb_ref`/`ab_ub_ref`. The `n,m` values are cross-referenced to the published Harwell–Boeing graph table in the matrix-bandwidth benchmark literature; the ABP reference bounds are from the published ABP table. They are not measurements of a locally downloaded file.

The byte-level input evidence is generated only after the actual `.mtx.rnd` files are present:

```powershell
python scripts/inspect_hb.py --data-dir benchmark/hb/raw
```

That command computes SHA-256, checks header and edge-row counts, checks endpoints, detects self-loops and duplicate undirected edges, computes `m_clean`, maximum degree `delta_max`, and `UB = n - delta_max`, and writes `benchmark/hb/MANIFEST.csv`. Missing or invalid files are reported as such rather than filled with reference values.
