> **Lưu ý:** File này được sinh tự động bằng `python -m experiments.w5_final_analysis`, không chỉnh sửa tay.
> Nguồn dữ liệu: `results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json` (W3/W4 frozen pilot; `results/runs.csv` chưa có tại thời điểm chạy)

# 25 — RQ2 final: xếp hạng SAT solver

> **Lát cắt cố định (BR-2):** `abp_encoding = order`, `amo_encoding = pairwise`, `search_mode` ∈ {rỗng, `multi`}, `symmetry = false`, `warm_start = false`; chỉ `solver` thay đổi.
> **Thứ tự ưu tiên Protocol:** OPT coverage → PAR2 → số `TO` → `peak_memory` → độ nhạy theo instance.

## 1. Bảng xếp hạng RQ2

| Hạng | Solver | Vai trò | Runs | OPT | FEAS | TO | MO | ERR | PAR2 (s) | Σ `t_solve` (s) | Σ `t_total` (s) | Median `t_total` (s) | Median Mem (MB) | Max Mem (MB) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `minisat22` | PySAT baseline (bổ sung) | 10 | 10 | 0 | 0 | 0 | 0 | 16.61 | 11.56 | 16.61 | 0.0694 | 24.90 | 99.30 |
| 2 | `glucose4` | Protocol Core | 10 | 10 | 0 | 0 | 0 | 0 | 17.13 | 12.06 | 17.13 | 0.0747 | 25.41 | 100.26 |
| 3 | `glucose42` | PySAT baseline (bổ sung) | 10 | 10 | 0 | 0 | 0 | 0 | 17.49 | 12.45 | 17.49 | 0.0753 | 25.15 | 99.91 |
| 4 | `cadical195` | Protocol Core | 10 | 10 | 0 | 0 | 0 | 0 | 23.24 | 17.56 | 23.24 | 0.0904 | 25.78 | 111.41 |

## 2. Kết luận RQ2

- **Canonical solver (Protocol Core `{cadical195, glucose4}`):** `glucose4` — 10/10 OPT, PAR2 17.13 s, max `peak_memory` 100.26 MB.
- **Caveat CaDiCaL:** `cadical195` chạy qua vòng lặp conflict-budget `src/sat/backend.py:238-254`; phần chênh thời gian của nó là chi phí wrapper, không phải chỉ tốc độ solver.
- **Toàn bộ 4 solver PySAT:** `minisat22` nhanh nhất (PAR2 16.61 s). Đây là baseline bổ sung; quyết định canonical vẫn theo Protocol Core (OQ-3), trừ khi P1/P3 cho phép `minisat22`.
- **Giới hạn tập dữ liệu:** mọi run RQ2 đều `OPT`; không có `TO`/`MO`/`ERR`, nên tiêu chí timeout/memory là rỗng trên subset này. Quyết định được đưa trên 10 instance đều xong trong 60 s; rủi ro instance khó được ghi nhận tại freeze (`docs/canonical_sat_config.md`).

## 3. Bảng chi tiết theo instance

| Instance | `minisat22` (status / `t_total` / mem) | `glucose4` (status / `t_total` / mem) | `glucose42` (status / `t_total` / mem) | `cadical195` (status / `t_total` / mem) |
|---|---:|---:|---:|---:|
| `randconn10-seed20261026` | OPT / 0.005s / 21.5MB | OPT / 0.005s / 21.7MB | OPT / 0.005s / 21.5MB | OPT / 0.005s / 21.7MB |
| `randconn12-seed20261026` | OPT / 0.010s / 22.1MB | OPT / 0.011s / 22.2MB | OPT / 0.011s / 22.2MB | OPT / 0.013s / 22.5MB |
| `randconn14-seed20261026` | OPT / 0.022s / 22.8MB | OPT / 0.022s / 23.1MB | OPT / 0.022s / 23.1MB | OPT / 0.029s / 23.4MB |
| `randconn16-seed20261026` | OPT / 0.028s / 23.5MB | OPT / 0.030s / 24.0MB | OPT / 0.029s / 23.8MB | OPT / 0.034s / 24.4MB |
| `randconn20-seed20261026` | OPT / 0.111s / 26.3MB | OPT / 0.119s / 26.9MB | OPT / 0.122s / 26.5MB | OPT / 0.147s / 27.2MB |
| `randconn24-seed20261026` | OPT / 0.435s / 31.9MB | OPT / 0.452s / 31.9MB | OPT / 0.519s / 31.9MB | OPT / 0.695s / 32.9MB |
| `randconn28-seed20261026` | OPT / 0.865s / 37.3MB | OPT / 0.905s / 38.1MB | OPT / 0.889s / 37.5MB | OPT / 1.302s / 38.4MB |
| `randconn40-seed20261026` | OPT / 11.025s / 81.2MB | OPT / 11.462s / 72.8MB | OPT / 11.130s / 69.0MB | OPT / 16.249s / 75.1MB |
| `randconn50-seed20261026` | OPT / 4.105s / 99.3MB | OPT / 4.121s / 100.3MB | OPT / 4.765s / 99.9MB | OPT / 4.764s / 111.4MB |
| `randconn8-seed20261026` | OPT / 0.002s / 21.4MB | OPT / 0.003s / 21.3MB | OPT / 0.003s / 21.4MB | OPT / 0.003s / 21.5MB |

## 4. Case study (a) — độ nhạy solver theo mật độ/kích thước

| Instance | n | m | density | Δ | UB | `minisat22` (s) | `glucose4` (s) | `glucose42` (s) | `cadical195` (s) | Winner | slow/fast | cv |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| `randconn10-seed20261026` | 10 | 20 | 0.4444 | 7 | 3 | 0.0046 | 0.0048 | 0.0049 | 0.0052 | `minisat22` | 1.119× | 0.040 |
| `randconn12-seed20261026` | 12 | 24 | 0.3636 | 7 | 5 | 0.0103 | 0.0105 | 0.0107 | 0.0127 | `minisat22` | 1.237× | 0.088 |
| `randconn14-seed20261026` | 14 | 28 | 0.3077 | 7 | 7 | 0.0220 | 0.0225 | 0.0224 | 0.0286 | `minisat22` | 1.298× | 0.115 |
| `randconn16-seed20261026` | 16 | 32 | 0.2667 | 8 | 8 | 0.0276 | 0.0305 | 0.0285 | 0.0339 | `minisat22` | 1.231× | 0.081 |
| `randconn20-seed20261026` | 20 | 40 | 0.2105 | 8 | 12 | 0.1113 | 0.1190 | 0.1222 | 0.1470 | `minisat22` | 1.321× | 0.107 |
| `randconn24-seed20261026` | 24 | 48 | 0.1739 | 7 | 17 | 0.4353 | 0.4522 | 0.5190 | 0.6952 | `minisat22` | 1.597× | 0.196 |
| `randconn28-seed20261026` | 28 | 56 | 0.1481 | 8 | 20 | 0.8653 | 0.9051 | 0.8888 | 1.3022 | `minisat22` | 1.505× | 0.182 |
| `randconn40-seed20261026` | 40 | 80 | 0.1026 | 8 | 32 | 11.0248 | 11.4625 | 11.1299 | 16.2486 | `minisat22` | 1.474× | 0.176 |
| `randconn50-seed20261026` | 50 | 100 | 0.0816 | 9 | 41 | 4.1053 | 4.1215 | 4.7648 | 4.7641 | `minisat22` | 1.161× | 0.073 |
| `randconn8-seed20261026` | 8 | 16 | 0.5714 | 7 | 1 | 0.0024 | 0.0026 | 0.0028 | 0.0027 | `minisat22` | 1.170× | 0.057 |

- **Trả lời câu hỏi “solver A thắng thưa, B thắng dày”:** dữ liệu frozen **không tách được** hai solver theo mật độ — cùng một winner (`minisat22`) trên toàn subset; density chỉ trải 0.0816–0.5714. Đây là scope limitation, không phải kết luận ‘không có khác biệt’.
- Cột `slow/fast` là tỷ lệ thời gian solver chậm nhất / nhanh nhất trên cùng instance; `cv` là hệ số biến thiên quần thể giữa các solver.

## 5. Case study (b) — FEAS không OPT và ý nghĩa bound (BR-8)

### `randconn40-seed20261026__sat__pairwise__pairwise__cadical195__multi__sym0__ws0__s0__tl60.0__mlNone`

- Instance `randconn40-seed20261026`; status `FEAS`; `lb = 14`, `ub = 39`, `gap = 25`; `k_best = 14`, `k_unsat = 40`, `unsat_source = counting:lệch nhãn tối đa n-1`; triage = `SOLVER_BEHAVIOR`.
- `ub = 39` là **cận trên đếm nhãn** `n − 1`, không phải upper bound chặt; `gap` lớn không có nghĩa solver gần tối ưu.

| K | Status | B | `t_encode` (s) | `t_solve` (s) | Vars | Clauses |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `SAT` | 1 | 0.013045 | 0.000146 | 1600 | 62480 |
| 2 | `SAT` | 2 | 0.020346 | 0.000141 | 1600 | 68720 |
| 3 | `SAT` | 3 | 0.019569 | 0.000145 | 1600 | 74800 |
| 4 | `SAT` | 4 | 0.023576 | 0.000137 | 1600 | 80720 |
| 5 | `SAT` | 5 | 0.026385 | 0.000162 | 1600 | 86480 |
| 6 | `SAT` | 6 | 0.028415 | 0.000254 | 1600 | 92080 |
| 7 | `SAT` | 7 | 0.027311 | 0.000590 | 1600 | 97520 |
| 8 | `SAT` | 8 | 0.029027 | 0.000987 | 1600 | 102800 |
| 9 | `SAT` | 9 | 0.032965 | 0.001657 | 1600 | 107920 |
| 10 | `SAT` | 10 | 0.033202 | 0.009899 | 1600 | 112880 |
| 11 | `SAT` | 11 | 0.039701 | 0.002126 | 1600 | 117680 |
| 12 | `SAT` | 12 | 0.035520 | 0.060441 | 1600 | 122320 |
| 13 | `SAT` | 13 | 0.038903 | 0.129464 | 1600 | 126800 |
| 14 | `SAT` | 14 | 0.045494 | 50.018789 | 1600 | 131120 |
| 15 | `UNKNOWN` | — | 0.075063 | 20.921673 | 1600 | 135280 |

### `randconn40-seed20261026__sat__pairwise__seqcounter__cadical195__multi__sym0__ws0__s0__tl60.0__mlNone`

- Instance `randconn40-seed20261026`; status `FEAS`; `lb = 14`, `ub = 39`, `gap = 25`; `k_best = 14`, `k_unsat = 40`, `unsat_source = counting:lệch nhãn tối đa n-1`; triage = `SOLVER_BEHAVIOR`.
- `ub = 39` là **cận trên đếm nhãn** `n − 1`, không phải upper bound chặt; `gap` lớn không có nghĩa solver gần tối ưu.

| K | Status | B | `t_encode` (s) | `t_solve` (s) | Vars | Clauses |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `SAT` | 1 | 0.004768 | 0.000177 | 4720 | 9360 |
| 2 | `SAT` | 2 | 0.006480 | 0.000168 | 4720 | 15600 |
| 3 | `SAT` | 3 | 0.007976 | 0.000155 | 4720 | 21680 |
| 4 | `SAT` | 4 | 0.012307 | 0.000223 | 4720 | 27600 |
| 5 | `SAT` | 5 | 0.010759 | 0.000244 | 4720 | 33360 |
| 6 | `SAT` | 6 | 0.012566 | 0.000586 | 4720 | 38960 |
| 7 | `SAT` | 7 | 0.016407 | 0.001411 | 4720 | 44400 |
| 8 | `SAT` | 8 | 0.015449 | 0.003599 | 4720 | 49680 |
| 9 | `SAT` | 9 | 0.019908 | 0.003855 | 4720 | 54800 |
| 10 | `SAT` | 10 | 0.023368 | 0.015355 | 4720 | 59760 |
| 11 | `SAT` | 11 | 0.018644 | 0.019164 | 4720 | 64560 |
| 12 | `SAT` | 12 | 0.025079 | 0.646002 | 4720 | 69200 |
| 13 | `SAT` | 13 | 0.029363 | 0.909534 | 4720 | 73680 |
| 14 | `SAT` | 14 | 0.027615 | 15.428809 | 4720 | 78000 |
| 15 | `UNKNOWN` | — | 0.062896 | 59.818742 | 4720 | 82160 |


## 6. Kissat — loại vĩnh viễn (BR-6)

Kissat không phải ứng viên và không xuất hiện trong bảng. Qua PySAT `kissat404` cho model sai, bỏ qua assumption một cách im lặng và abort process sau `add_clause`; không có binary `kissat` ngoài trên `PATH` (`docs/sat_tooling.md` mục Kissat; `src/sat/backend.py` `PYSAT_KISSAT_FAMILIES`; `src/sat/solve.py` `_validate_solver`). Bảng RQ2 chỉ gồm `glucose4`, `cadical195` (Protocol Core) và `minisat22`, `glucose42` (PySAT baseline).

## 7. Provenance

- Nguồn chính: `results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json` (W3/W4 frozen pilot; `results/runs.csv` chưa có tại thời điểm chạy).
- Projection cap tham chiếu: `12288` MB (OQ-4, chưa phải số cuối).
- Không có solver subprocess nào được spawn bởi module này.
