> **Lưu ý:** File này được sinh tự động bằng `python -m experiments.w5_final_analysis`, không chỉnh sửa tay.
> Nguồn dữ liệu: `results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json` (W3/W4 frozen pilot; `results/runs.csv` chưa có tại thời điểm chạy)

# 24 — RQ1 final: encoding × AMO

> **Lát cắt cố định (BR-2):** solver = `cadical195`, `search_mode` ∈ {rỗng, `multi`}, `symmetry = false`, `warm_start = false`; chỉ `(abp_encoding, amo_encoding)` thay đổi.

## 1. Bảng tổng hợp RQ1

| `abp_encoding` | `amo_encoding` | Runs | OPT | FEAS | TO | MO | ERR | PAR2 (s) | Σ `t_encode` (s) | Σ `t_solve` (s) | Σ `t_total` (s) | Median Vars | Max Vars | Median Clauses | Max Clauses | Median Mem (MB) | Max Mem (MB) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `order` | `seqcounter` | 10 | 10 | 0 | 0 | 0 | 0 | 23.12 | 2.50 | 17.42 | 23.12 | 310 | 2450 | 8840 | 196450 | 25.99 | 112.99 |
| `order` | `pairwise` | 10 | 10 | 0 | 0 | 0 | 0 | 23.24 | 2.48 | 17.56 | 23.24 | 310 | 2450 | 8840 | 196450 | 25.78 | 111.41 |
| `pairwise` | `seqcounter` | 10 | 9 | 1 | 0 | 0 | 0 | 130.81 | 0.99 | 85.68 | 88.50 | 948 | 7400 | 7548 | 147500 | 24.84 | 87.62 |
| `pairwise` | `pairwise` | 10 | 9 | 1 | 0 | 0 | 0 | 133.76 | 2.03 | 80.64 | 86.43 | 328 | 2500 | 11444 | 255400 | 26.63 | 126.53 |

## 2. Kết luận RQ1

- **Encoding/AMO biểu diễn bài toán tốt hơn:** `order`/`pairwise` đứng đầu bảng theo thứ tự Protocol (OPT coverage → PAR2 → `peak_memory`).
- **Có giúp solving không:** có, trên tập frozen. `order`/`pairwise` đạt 10/10 OPT, PAR2 23.24 s, max `peak_memory` 111.41 MB.
- **So với `pairwise`/`pairwise`:** 9/10 OPT, PAR2 133.76 s, max clauses 255400, max `peak_memory` 126.53 MB. Chênh lệch OPT coverage là tiêu chí quyết định; thời gian chỉ là tiêu chí phụ.
- **Không ép chiều nhân quả:** CNF nhỏ hơn không đồng nghĩa giải nhanh hơn; cả hai chiều được liệt kê ở §3 từ dữ liệu frozen (BR-4).

## 3. Case study từ dữ liệu frozen

### 3.1. (a) CNF nhỏ hơn nhưng giải chậm hơn

| Instance | Cấu hình nhỏ hơn | Clauses | Vars | `t_total` (s) | Status | Cấu hình lớn hơn | Clauses | Vars | `t_total` (s) | Status |
|---|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `randconn20-seed20261026` | `pairwise/seqcounter` | 10200 | 1160 | 0.247 | `OPT` | `pairwise/pairwise` | 15560 | 400 | 0.233 | `OPT` |
| `randconn20-seed20261026` | `pairwise/seqcounter` | 10200 | 1160 | 0.247 | `OPT` | `order/pairwise` | 12080 | 380 | 0.147 | `OPT` |
| `randconn24-seed20261026` | `pairwise/seqcounter` | 16752 | 1680 | 1.414 | `OPT` | `order/pairwise` | 20592 | 552 | 0.695 | `OPT` |
| `randconn28-seed20261026` | `pairwise/seqcounter` | 27720 | 2296 | 2.218 | `OPT` | `order/pairwise` | 34496 | 756 | 1.302 | `OPT` |
| `randconn40-seed20261026` | `pairwise/seqcounter` | 82160 | 4720 | 77.684 | `FEAS` | `pairwise/pairwise` | 135280 | 1600 | 72.669 | `FEAS` |
| `randconn40-seed20261026` | `pairwise/seqcounter` | 82160 | 4720 | 77.684 | `FEAS` | `order/pairwise` | 105520 | 1560 | 16.249 | `OPT` |
| `randconn50-seed20261026` | `pairwise/seqcounter` | 147500 | 7400 | 6.862 | `OPT` | `pairwise/pairwise` | 255400 | 2500 | 5.279 | `OPT` |
| `randconn50-seed20261026` | `pairwise/seqcounter` | 147500 | 7400 | 6.862 | `OPT` | `order/pairwise` | 196450 | 2450 | 4.764 | `OPT` |

Mọi cặp thỏa đồng thời `smaller_clauses < larger_clauses` và `smaller_t_total > larger_t_total` trong CSV frozen.

### 3.2. (b) CNF lớn hơn nhưng giải nhanh hơn

| Instance | Cấu hình lớn hơn | Clauses | Vars | `t_total` (s) | Status | Cấu hình nhỏ hơn | Clauses | Vars | `t_total` (s) | Status |
|---|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `randconn20-seed20261026` | `pairwise/pairwise` | 15560 | 400 | 0.233 | `OPT` | `pairwise/seqcounter` | 10200 | 1160 | 0.247 | `OPT` |
| `randconn20-seed20261026` | `order/pairwise` | 12080 | 380 | 0.147 | `OPT` | `pairwise/seqcounter` | 10200 | 1160 | 0.247 | `OPT` |
| `randconn24-seed20261026` | `order/pairwise` | 20592 | 552 | 0.695 | `OPT` | `pairwise/seqcounter` | 16752 | 1680 | 1.414 | `OPT` |
| `randconn28-seed20261026` | `order/pairwise` | 34496 | 756 | 1.302 | `OPT` | `pairwise/seqcounter` | 27720 | 2296 | 2.218 | `OPT` |
| `randconn40-seed20261026` | `pairwise/pairwise` | 135280 | 1600 | 72.669 | `FEAS` | `pairwise/seqcounter` | 82160 | 4720 | 77.684 | `FEAS` |
| `randconn40-seed20261026` | `order/pairwise` | 105520 | 1560 | 16.249 | `OPT` | `pairwise/seqcounter` | 82160 | 4720 | 77.684 | `FEAS` |
| `randconn50-seed20261026` | `pairwise/pairwise` | 255400 | 2500 | 5.279 | `OPT` | `pairwise/seqcounter` | 147500 | 7400 | 6.862 | `OPT` |
| `randconn50-seed20261026` | `order/pairwise` | 196450 | 2450 | 4.764 | `OPT` | `pairwise/seqcounter` | 147500 | 7400 | 6.862 | `OPT` |

Điều kiện lọc: lớn hơn về clause nhưng `t_total` nhỏ hơn ít nhất 0,005 s và 5%.

**Đảo chiều kích thước phi đơn điệu (n=50 nhanh hơn n=40):**

| Solver | `n=50` `t_total` (s) | Status | `n=40` `t_total` (s) | Status | Tỷ lệ n40/n50 |
|---|---:|---|---:|---|---:|
| `cadical195` | 4.764 | `OPT` | 16.249 | `OPT` | 3.41× |
| `glucose4` | 4.121 | `OPT` | 11.462 | `OPT` | 2.78× |
| `glucose42` | 4.765 | `OPT` | 11.130 | `OPT` | 2.34× |
| `minisat22` | 4.105 | `OPT` | 11.025 | `OPT` | 2.69× |

### 3.3. (c) `pairwise`/`pairwise` bùng nổ kích thước và rủi ro MO

**Đo được (frozen):** `pairwise`/`pairwise` có đúng `n²` biến; nhóm AMO bậc hai theo số literal làm tổng clause `O(n³)`. Tại `n = 50`, cấu hình này đạt **255400 clauses** và **126.53 MB**; `order`/`pairwise` đạt **196450 clauses** và **111.41 MB**.

**Projection (không phải measurement):** ước lượng clause theo công thức đặc tả, mốc bộ nhớ quy đổi từ `randconn50` (`126.53125` MB / `255400` clause). `m` của mẫu HB dày lấy `n(n−1)/8`; cap tham chiếu `12288` MB.

| n | m | k | `pairwise`/`pairwise` clauses | `pairwise` mem (MB) | vượt cap | `order`/`pairwise` clauses | `order` mem |
|---:|---:|---:|---:|---:|---|---:|---|
| 50 | 100 | 17 | 255400 | 126.5 | không | 196450 | — |
| 118 | 1725 | 117 | 25441244 | 12604.2 | có | 24640142 | — |
| 420 | 21997 | 419 | 3944900506 | 1954397.8 | có | 3908119426 | — |
| 715 | 63813 | 714 | 32942063084 | 16320283.6 | có | 32760064124 | — |

- **MO hình thành thế nào (BR-7):** solver SAT không enforce `memory_limit` cap trong process. `MO` chỉ đến từ ánh xạ `MemoryError` ngoài process (`src/runner/worker.py`); cap official do runner áp (Protocol §6.3). Không có claim MO đo được cho `pairwise/pairwise` trong frozen data.
- **Hệ quả:** ở quy mô HB lớn, `pairwise`/`pairwise` là bất khả thi theo projection; `order` giữ số biến `n(n−1)` và không có nhóm AMO nên clause thấp hơn hẳn trên cùng `(n, m, K)`.

## 4. Kiểm tra nhất quán `order`/`seqcounter` ≡ `order`/`pairwise` (BR-3)

- Hai hàng `order` có cùng `max_clauses` = 196450 và cùng `max_vars` = 2450; `Σ t_total` lần lượt 23.24 s và 23.12 s. Đây là kiểm tra CNF trùng, không phải bằng chứng cho AMO encoder. `order/seqcounter` bị loại khỏi khai thác cặp đảo chiều.

## 5. Provenance

- Nguồn chính: `results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json` (W3/W4 frozen pilot; `results/runs.csv` chưa có tại thời điểm chạy).
- Mọi số trong bảng sinh trực tiếp bởi `experiments/w5_final_analysis.py`; không sửa tay.
- Lát cắt khớp `experiments/analyze_rq1_rq2.py` (`_filter_rq1_rows`).
