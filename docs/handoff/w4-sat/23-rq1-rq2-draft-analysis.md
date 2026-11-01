# Nháp phân tích RQ1 / RQ2 và kiểm tra cổng G3 (W4, issue #23 / #30)

> **Lưu ý:** File này được sinh tự động bằng `python -m experiments.analyze_rq1_rq2`, không chỉnh sửa tay.
> Nguồn dữ liệu: `results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json` (bản nháp W4 trước khi P3 khóa `results/runs.csv` official)

## 1. Phân tích RQ1 — Encoding × AMO

### 1.1. Bảng tổng hợp theo cấu hình `(abp_encoding, amo_encoding)`

| `abp_encoding` | `amo_encoding` | Runs | OPT | FEAS | TO | PAR2 (s) | Σ `t_encode` (s) | Σ `t_solve` (s) | Σ `t_total` (s) | Median Vars | Max Vars | Median Clauses | Max Clauses | Median Mem (MB) | Max Mem (MB) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `order` | `seqcounter` | 10 | 10 | 0 | 0 | 23.12 | 2.50 | 17.42 | 23.12 | 310 | 2450 | 8840 | 196450 | 25.99 | 112.99 |
| `order` | `pairwise` | 10 | 10 | 0 | 0 | 23.24 | 2.48 | 17.56 | 23.24 | 310 | 2450 | 8840 | 196450 | 25.78 | 111.41 |
| `pairwise` | `seqcounter` | 10 | 9 | 1 | 0 | 130.81 | 0.99 | 85.68 | 88.50 | 948 | 7400 | 7548 | 147500 | 24.84 | 87.62 |
| `pairwise` | `pairwise` | 10 | 9 | 1 | 0 | 133.76 | 2.03 | 80.64 | 86.43 | 328 | 2500 | 11444 | 255400 | 26.63 | 126.53 |

### 1.2. Nhận xét kỹ thuật RQ1 (Encoding size, AMO, và hiện tượng CNF nhỏ ≠ solver nhanh)

- **Kích thước CNF (`variables` & `clauses`):**
  - Với `pairwise` ABP + `pairwise` AMO: số biến cố định đúng bằng $n^2$, nhưng số mệnh đề AMO bậc hai $O(n^3)$ làm tổng số clause lớn nhất (tới 255 400 clauses ở $n=50$).
  - Với `pairwise` ABP + `seqcounter` AMO: thay AMO bậc hai bằng biến phụ tuần tự giúp giảm mạnh số mệnh đề (còn 147 500 clauses ở $n=50$), đổi lại số biến tăng khoảng $3\times$ (7 400 biến ở $n=50$).
  - Với `order` ABP: chuỗi đơn điệu tự mã hóa cả ALO lẫn AMO nên không cần nhóm mệnh đề AMO riêng ($n(n-1)$ biến, 196 450 clauses ở $n=50$). Hai hàng `order/pairwise` và `order/seqcounter` có số biến và số clause giống hệt nhau trên mọi instance.
- **Thời gian mã hóa (`t_encode`) và bộ nhớ (`peak_memory`):**
  - `t_encode` nhỏ hơn 1.7 s trên mọi cấu hình ở tập hiện tại; `pairwise/seqcounter` có `t_encode` thấp nhất nhờ số mệnh đề ít nhất.
  - `peak_memory` của `pairwise/seqcounter` thấp nhất ở $n=40, 50$ (max 87.6 MB so với 111.4 MB của `order` và 126.5 MB của `pairwise/pairwise`).
- **Bằng chứng thực nghiệm: CNF nhỏ hơn (ít clause hơn) KHÔNG đồng nghĩa solver nhanh hơn:**
  - Trên `randconn20-seed20261026`: `pairwise/seqcounter` chỉ có **10200 clauses** (1160 biến) nhưng mất **0.247s** (`OPT`), chậm hơn `pairwise/pairwise` dù cấu hình sau có tới **15560 clauses** (400 biến) và chỉ mất **0.233s** (`OPT`).
  - Trên `randconn20-seed20261026`: `pairwise/seqcounter` chỉ có **10200 clauses** (1160 biến) nhưng mất **0.247s** (`OPT`), chậm hơn `order/pairwise` dù cấu hình sau có tới **12080 clauses** (380 biến) và chỉ mất **0.147s** (`OPT`).
  - Trên `randconn24-seed20261026`: `pairwise/seqcounter` chỉ có **16752 clauses** (1680 biến) nhưng mất **1.414s** (`OPT`), chậm hơn `order/pairwise` dù cấu hình sau có tới **20592 clauses** (552 biến) và chỉ mất **0.695s** (`OPT`).
  - Trên `randconn28-seed20261026`: `pairwise/seqcounter` chỉ có **27720 clauses** (2296 biến) nhưng mất **2.218s** (`OPT`), chậm hơn `order/pairwise` dù cấu hình sau có tới **34496 clauses** (756 biến) và chỉ mất **1.302s** (`OPT`).
  - Trên `randconn40-seed20261026`: `pairwise/seqcounter` chỉ có **82160 clauses** (4720 biến) nhưng mất **77.684s** (`FEAS`), chậm hơn `pairwise/pairwise` dù cấu hình sau có tới **135280 clauses** (1600 biến) và chỉ mất **72.669s** (`FEAS`).
  - Trên `randconn40-seed20261026`: `pairwise/seqcounter` chỉ có **82160 clauses** (4720 biến) nhưng mất **77.684s** (`FEAS`), chậm hơn `order/pairwise` dù cấu hình sau có tới **105520 clauses** (1560 biến) và chỉ mất **16.249s** (`OPT`).

## 2. Phân tích RQ2 — So sánh SAT Solver

### 2.1. Bảng tổng hợp theo Solver (Coverage, PAR2, Memory)

| Solver | Runs | OPT | FEAS | TO | MO | ERR | PAR2 (s) | Σ `t_solve` (s) | Σ `t_total` (s) | Median `t_total` (s) | Median Mem (MB) | Max Mem (MB) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `minisat22` | 10 | 10 | 0 | 0 | 0 | 0 | 16.61 | 11.56 | 16.61 | 0.0694 | 24.90 | 99.30 |
| `glucose4` | 10 | 10 | 0 | 0 | 0 | 0 | 17.13 | 12.06 | 17.13 | 0.0747 | 25.41 | 100.26 |
| `glucose42` | 10 | 10 | 0 | 0 | 0 | 0 | 17.49 | 12.45 | 17.49 | 0.0753 | 25.15 | 99.91 |
| `cadical195` | 10 | 10 | 0 | 0 | 0 | 0 | 23.24 | 17.56 | 23.24 | 0.0904 | 25.78 | 111.41 |

### 2.2. Bảng chi tiết theo từng Instance (Status, Runtime, Peak Memory)

| Instance | `minisat22` (status / t_total / mem) | `glucose4` (status / t_total / mem) | `glucose42` (status / t_total / mem) | `cadical195` (status / t_total / mem) |
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

### 2.3. Nhận xét kỹ thuật RQ2

- So sánh theo thứ tự ưu tiên của Protocol (OPT coverage → PAR2 → median `peak_memory`): tất cả các solver được thử nghiệm với `order/pairwise` đều đạt 100% `OPT` trên tập hiện tại, không phát sinh `TO`, `MO`, hay `ERR`.
- Trong tập Core solver của Protocol (`{cadical195, glucose4}` sau khi loại Kissat), **`glucose4`** vượt trội `cadical195` cả về tổng thời gian / PAR2 (17.13s so với 23.24s) lẫn `peak_memory` cực đại (100.3 MB so với 111.4 MB) nhờ gọi thẳng hàm giới hạn xung đột trong C++ thay vì vòng lặp chia nhỏ conflict budget của `cadical195`.
- Xét rộng trên cả 4 solver của PySAT, `minisat22` đạt tổng thời gian thấp nhất (16.61s) và bộ nhớ thấp nhất (99.3 MB).

## 3. Kiểm tra cổng G3 (Gate 3 Readiness & Incident Triage)

- **Số run SAT đã hoàn thành / kỳ vọng:** `70 / 70` (`100.0%`, yêu cầu G3 ≥ `80.0%`) → **PASS**.
- **Tổng số file raw JSON đã kiểm tra qua `src.sat.triage`:** `70`.
- **Số run bất thường (`status != OPT` hoặc lỗi):** `2` (chưa phân loại: `0`, lỗi correctness `CODE_BUG`: `0`).
- **Kết luận cổng G3 (trên tập dữ liệu hiện có):** **PASS**.

### Bảng phân loại các run bất thường

| `run_id` | Status | `lb` | `ub` | `verify()` | Phân loại | Lý do chi tiết |
|---|---|---:|---:|---:|---|---|
| `randconn40-seed20261026__sat__pairwise__pairwise__cadical195__multi__sym0__ws0__s0__tl60.0__mlNone` | `FEAS` | 14 | 39 | 14 | **`SOLVER_BEHAVIOR`** | Hết giờ sau khi đã verify incumbent lb=14, ub=39 (gap=25). |
| `randconn40-seed20261026__sat__pairwise__seqcounter__cadical195__multi__sym0__ws0__s0__tl60.0__mlNone` | `FEAS` | 14 | 39 | 14 | **`SOLVER_BEHAVIOR`** | Hết giờ sau khi đã verify incumbent lb=14, ub=39 (gap=25). |
