# Experimental Protocol — Antibandwidth Problem (ABP)

**Phiên bản:** 1.0-rc **Trạng thái:** chờ review của P2, P3 và xử lý các mục chặn freeze (Mục 12–13) **Dataset:** chỉ Harwell–Boeing, 24 instance **Owner:** P1 (coordinator). **Review:** P2, P3

Tài liệu này là nguồn duy nhất cho thiết kế thực nghiệm. Khi các điều kiện ở Mục 12 được đáp ứng và nhóm xác nhận, protocol được khóa bằng tag `v1.0`.

---

## 1. Mục tiêu và phạm vi

ABP: tìm phép gán nhãn song ánh f: V → {1..n} sao cho giá trị nhỏ nhất của |f(u) − f(v)| trên các cạnh (u, v) là lớn nhất.

AB(G) = max over f of ( min over (u,v) in E of |f(u) − f(v)| )

Mục tiêu: so sánh phương pháp SAT và exact về tính đúng, hiệu năng và khả năng tái lập.

**Core (bắt buộc):**

- SAT: ABP encoding {pairwise, order}; AMO {pairwise, sequential counter}; solver {CaDiCaL, Glucose, Kissat}; search multi-run, non-incremental.
- Exact: Gurobi MIP, CPLEX MIP, CPLEX CP, CP-SAT.

Nếu Kissat khó tích hợp qua PySAT, gọi binary ngoài và ghi rõ cách đo; nếu vẫn không được, RQ2 chỉ so CaDiCaL và Glucose và nêu rõ hạn chế. Nếu một exact solver không chạy được do license hoặc công cụ, ghi `ERR` kèm lý do và báo cáo đúng phạm vi so sánh thực tế; không coi solver chưa chạy là đã hoàn thành.

**Bonus: NO-GO** (quyết định cuối W2). Không đưa staircase/SCL/Duplex, incremental, symmetry breaking hoặc warm start vào kết quả benchmark. Các công trình liên quan chỉ dùng cho Related Work và đối chiếu định tính. Mở lại Bonus chỉ khi có quyết định ghi nhận rõ ràng.

## 2. Dataset

### 2.1. Nguồn và danh sách

Chỉ dùng Harwell–Boeing Sparse Matrix Collection, bộ 24 đồ thị ABP chuẩn (12 nhỏ, 30–118 đỉnh; 12 lớn, 420–715 đỉnh). Danh sách quản lý tại `benchmark/hb/instances.csv` với các cột:

`id,name,file,size_group,n,m_table,ab_lb_ref,ab_ub_ref,pilot_role`

Có dòng trong CSV không có nghĩa file dữ liệu đã được tải và kiểm tra; việc đó ghi nhận riêng trong `MANIFEST.csv`.

Tên ma trận (ví dụ `bcsstk06`) là id dùng trong dữ liệu và paper; chữ cái A–X chỉ để trao đổi.

### 2.2. Định dạng file

Dự kiến `*.mtx.rnd`: dòng đầu `n n m`, các dòng sau mỗi dòng một cạnh `u v` (đánh số từ 1). Cần xác nhận định dạng thực tế của cả 24 file; ý nghĩa hậu tố `.rnd` được xác minh nếu cần mô tả trong Experimental setup.

### 2.3. Quy tắc chuyển thành đồ thị (loader)

1. Giữ nguyên tập đỉnh 1..n, kể cả đỉnh cô lập.
2. Bỏ self-loop.
3. Coi cạnh là vô hướng, loại cạnh trùng.
4. Ghi vào `MANIFEST.csv`: sha256 của file, `m` trong header, `m` sau làm sạch.

Kiểm tra bắt buộc: `n` khớp `instances.csv` cho cả 24 instance; `m` trong header khớp `m_table`; nếu `m` đổi sau làm sạch, ghi chênh lệch và giải thích trong Experimental setup. Không âm thầm sửa file nguồn hay bỏ đỉnh để dữ liệu khớp kỳ vọng.

### 2.4. Cận tham chiếu

`ab_lb_ref` và `ab_ub_ref` lấy từ literature, chỉ dùng kiểm tra phụ: giá trị `OPT` phải nằm trong [`ab_lb_ref`, `ab_ub_ref`], nếu không thì điều tra trước khi chấp nhận. Không dùng làm đầu vào cho solver.

### 2.5. Tier 0/1

Tier 0 (đồ thị rất nhỏ cho oracle và unit test) và Tier 1 (path, cycle, grid, complete...) chỉ dùng để kiểm tra tính đúng và sanity check, không báo cáo như kết quả benchmark. Benchmark chính thức chỉ gồm 24 instance Harwell–Boeing.

## 3. Các tập instance

| Tập | Instance | Mục đích |
|---|---|---|
| **Official** | cả 24 | RQ3 và phân tích độ khó |
| **Validation subset** (10) | pores_1, bcsstk01, bcspwr02, curtis54, will57, impcol_b, ash85, nos4, dwt_234, bcspwr03 | Pilot RQ1/RQ2, chỉ để chọn canonical config |
| **Pilot-large** (3) | bcsstk06, nos6, can_715 | Lộ sớm vấn đề trên instance lớn (CNF quá lớn, MIP yếu, memory); không dùng để chọn config |

Validation subset lấy từ 12 instance nhỏ/vừa (A–L), bỏ hai instance ít phân biệt nhất (ibm32 và bcspwr01, cận tham chiếu gần như trùng nhau). Subset trải n từ 30 đến 118 và bậc trung bình từ khoảng 2,4 đến 9,5, gồm instance dự kiến nhanh, trung bình và khó. Phân loại độ khó dựa trên một bài tham khảo dùng encoding khác nên chỉ mang tính gợi ý.

**Thời điểm khóa:** Validation subset khóa trước khi pilot bắt đầu. Danh sách 24 instance Official khóa cùng benchmark ở M2.

**Quy tắc báo cáo.** Work breakdown yêu cầu RQ3 chạy trên toàn bộ 24 instance, đồng thời validation subset không dùng để báo cáo RQ3; hai yêu cầu này không thể cùng đúng tuyệt đối vì validation subset nằm trong 24 instance. Cách xử lý (cần nhóm xác nhận):

- Canonical config được chọn và khóa trước khi xem kết quả official.
- RQ3 báo cáo trên cả 24 instance, và báo cáo thêm riêng trên 14 instance không thuộc Validation subset. Paper nêu rõ 10 instance đã dùng để chọn config.
- 14 instance này không phải tập test độc lập lấy mẫu ngẫu nhiên; chúng là phần còn lại của bộ benchmark.

## 4. Câu hỏi nghiên cứu

**RQ1 — Encoding (Validation subset).** ABP encoding và AMO encoding ảnh hưởng thế nào đến kích thước CNF và hiệu năng? Cố định CaDiCaL và search mode `multi`; đổi 2 × 2 = 4 cấu hình (ABP {pairwise, order} × AMO {pairwise, sequential counter}).

**RQ2 — SAT solver (Validation subset).** Với encoding và AMO tốt nhất từ RQ1, CaDiCaL, Glucose, Kissat khác nhau thế nào? Chỉ đổi solver.

**RQ3 — SAT vs Exact (Official, 24 instance).** Canonical SAT config so với Gurobi MIP, CPLEX MIP, CPLEX CP, CP-SAT dưới cùng protocol. Kèm phân tích độ khó: runtime và status theo n, |E|, density, bậc đỉnh; cactus plot, scatter, phân bố status. Không dùng từ "predict" vì dự án không xây dựng mô hình dự đoán.

Không có RQ4; Bonus không đánh số RQ. Mỗi RQ trình bày theo chuỗi: câu hỏi → thiết kế thí nghiệm → bằng chứng → kết luận. Không kết luận "A tốt hơn B" chỉ từ vài runtime.

## 5. Phương pháp giải

### 5.1. SAT (multi-run, non-incremental)

1. Bắt đầu từ cận dưới tầm thường hoặc nghiệm heuristic nhanh; thời gian heuristic tính vào `t_total`.
2. Với mỗi K, mã hóa CNF "tồn tại nhãn với antibandwidth ≥ K" và gọi solver.
3. Nếu SAT: giải mã nghiệm, verify, tính antibandwidth thực tế B, đặt K ← B + 1.
4. Nếu UNSAT sau một nghiệm đã verify có giá trị B: B là tối ưu (`OPT`).
5. Cận trên ban đầu tính từ n và bậc đỉnh (P1/P2 thống nhất cách tính, ghi vào `ub`); không dùng cận từ literature.
6. P1 và P2 review chéo ánh xạ giữa "antibandwidth ≥ K" và độ rộng cửa sổ trong encoding để tránh lệch một đơn vị.

### 5.2. Exact

P1 viết formulation, P2 review. MIP dùng biến nhị phân theo cạnh cho |f(u) − f(v)| ≥ K, tránh big-M yếu. Không tinh chỉnh riêng từng solver: dùng tham số mặc định, trừ các thiết lập chung (1 thread, time limit, memory limit, seed). Mọi khác biệt bắt buộc do API hoặc giới hạn solver phải được ghi nhận; không tuyên bố các solver chạy "giống hệt nhau" nếu thực tế không đúng.

## 6. Protocol chạy

### 6.1. Tài nguyên

- Cùng một máy cho mọi official run; 1 thread mỗi run; không warm start; không symmetry breaking.
- Mọi phương pháp nhận cùng một đồ thị đã qua loader (cùng format input).
- Số run song song sao cho tổng memory limit không vượt RAM vật lý.

### 6.2. Time limit

- Official: 1800 s mỗi (instance × phương pháp), đúng work breakdown.
- Pilot: 600 s mỗi run. Đây là bổ sung của protocol để tiết kiệm compute (work breakdown không quy định time limit riêng cho pilot), nên canonical config được chọn trong chế độ ngắn hơn official; nhóm xác nhận, hoặc chạy pilot ở 1800 s nếu ngân sách cho phép.
- Với SAT multi-run, 1800 s là ngân sách cho cả chuỗi K, không phải từng lần gọi solver.
- `t_total` gồm thời gian build model/encoding và mọi lần gọi solver. Với exact solver, time limit truyền cho solver là 1800 − t_build.
- Số liệu chính thức là wall-time do runner đo. Runner kill cứng tại time_limit + 30 s chỉ để dự phòng; 30 s này không phải ngân sách solve thêm.

### 6.3. Memory limit

Mức mục tiêu: 30 GB mỗi run. Chỉ dùng mức này sau khi xác minh RAM vật lý và khả năng thực thi giới hạn trên máy chạy; nếu không đáp ứng, chốt ngưỡng thấp hơn trước freeze, ghi rõ trong paper và giảm số run song song.

Runner phải thực thi giới hạn bộ nhớ thật, không chỉ ghi `memory_limit` trong config. Chỉ ghi `MO` khi có bằng chứng run vượt giới hạn; lỗi không rõ nguyên nhân thì điều tra, không tự gán `MO`.

### 6.4. Seed, lặp, resume

- Mỗi cặp (instance × phương pháp) chạy 1 lần, `seed = 0`. Hạn chế đã biết: runtime không có khoảng tin cậy từ nhiều lần chạy; nêu trong Limitations.
- Runner bỏ qua run đã có kết quả hợp lệ. Run thiếu hoặc `ERR` được chạy lại ở W5; mọi lần chạy lại được ghi nhận, không ghi đè lịch sử.

## 7. Status và validation

| Status | Định nghĩa |
|---|---|
| `OPT` | Nghiệm đã verify và có certificate tối ưu |
| `FEAS` | Nghiệm đã verify, chưa chứng minh tối ưu khi hết ngân sách |
| `TO` | Hết giờ, chưa có nghiệm verify |
| `MO` | Vượt memory limit đã cấu hình |
| `ERR` | Lỗi thực thi, license, output hỏng hoặc lỗi khác làm run không hoàn thành đúng quy trình |

Lỗi license ghi `ERR`, không ghi `TO`.

**Kiểm tra nghiệm:** là hoán vị hợp lệ của 1..n, không trùng nhãn; objective tính lại độc lập và khớp output solver.

**Kiểm tra nhất quán:** `lb ≤ ub`; `OPT` có certificate; `FEAS` có incumbent đã verify; `TO` không có incumbent; không trùng `run_id`; không thiếu run so với kế hoạch; `OPT` nằm trong khoảng tham chiếu (Mục 2.4).

**Kiểm tra chéo:** trên Tier 0/1, mọi solver Core khớp oracle; trên instance lớn, hai solver cùng `OPT` thì objective phải bằng nhau. Mâu thuẫn phải được điều tra trước khi dùng dữ liệu.

## 8. Metric và schema

Schema theo `CONTRACT.md`. Mỗi run lưu tối thiểu: `run_id, instance, method, abp_encoding, amo_encoding, solver, search_mode, status, lb, ub, t_encode, t_solve, t_total, variables, clauses, peak_memory, git_tag, host, timestamp`. Trường không áp dụng cho một phương pháp được biểu diễn nhất quán theo schema, không điền giá trị giả.

- RQ1: variables, clauses, `t_encode`, `t_solve`, `t_total`, `peak_memory`, `status`.
- RQ2: số instance theo status, runtime và memory từng instance, lỗi và run bất thường.
- RQ3: `status`, `lb/ub`, `t_total`, `peak_memory`.

Mọi bảng và hình sinh từ dữ liệu đã lưu bằng cnsplots; không sửa `runs.csv` bằng tay. Giữ raw output để truy vết. Paper theo cas-sc (yêu cầu đề).

Báo cáo kích thước CNF và status của mọi instance, kể cả khi `TO`/`MO` (ví dụ SAT trên instance lớn); không chọn lọc kết quả.

## 9. Pilot và chọn canonical config

### 9.1. Thứ tự

1. **RQ1:** 10 instance × 4 cấu hình (CaDiCaL) = 40 run → chọn (ABP encoding, AMO).
2. **RQ2:** thêm Glucose và Kissat với cấu hình vừa chọn = 20 run mới; 10 run CaDiCaL lấy lại từ RQ1. Tổng SAT pilot: 60 run.
3. **Pilot exact:** 10 instance × 4 exact solver = 40 run (kiểm tra formulation, license, tài nguyên).
4. **Pilot-large:** 3 instance × (4 cấu hình SAT của RQ1 với CaDiCaL + 4 exact solver) = 24 run, để lộ sớm CNF quá lớn, MIP yếu, vấn đề memory và kiểm tra kill/resume. Kết quả có thể kích hoạt sửa lỗi hoặc điều chỉnh giới hạn tài nguyên theo freeze policy, nhưng không thay đổi quy tắc chọn config ở Mục 9.2.

Nếu một solver không khả dụng, ghi lại số run thực tế và lý do; không giữ nguyên tổng dự kiến như thể mọi run đã xong.

### 9.2. Quy tắc chọn (ghi trước khi chạy official)

So sánh theo thứ tự:

1. Nhiều instance `OPT` hơn.
2. Hòa: PAR2 thấp hơn (run không `OPT` bị phạt 2 × time limit).
3. Hòa: `peak_memory` trung vị thấp hơn.
4. Hòa: `clauses` trung vị thấp hơn.

Xử lý run lỗi, thiếu hoặc chưa hoàn thành nhất quán giữa các cấu hình; không loại run bất lợi nếu không có lý do kỹ thuật được ghi nhận. Kết quả pilot, quy tắc đã áp dụng và lý do chọn lưu trong `docs/` trước M2.

Cố định toàn bộ benchmark: `search_mode = multi`, `symmetry = false`, `warm_start = false`.

## 10. Official run

Chỉ bắt đầu sau khi tag `v1.0`: 24 instance × 5 phương pháp (canonical SAT, CP-SAT, Gurobi MIP, CPLEX MIP, CPLEX CP) = 120 run dự kiến.

P3 vận hành official run và validation; P1 không vận hành queue chạy thực nghiệm (kiểm tra ngẫu nhiên khoảng 10 run exact).

Pipeline: configuration → runner → mỗi run một subprocess → raw JSON → validation → `runs.csv` → figure/table.

Run `ERR` hoặc thiếu được điều tra và chạy lại ở W5. Nếu license không cho phép chạy một instance, ghi `ERR` cùng lý do, không đổi thành `TO`.

## 11. Ngân sách và môi trường

Core-giờ worst case = (số run × time limit) / 3600.

| Giai đoạn | Số run | Time limit | Core-giờ |
|---|---:|---:|---:|
| Pilot RQ1 + RQ2 | 60 | 600 s | 10 |
| Pilot exact | 40 | 600 s | 6,7 |
| Pilot-large | 24 | 600 s | 4,0 |
| Official RQ3 | 120 | 1800 s | 60 |

Đây là ngân sách CPU, không phải cam kết thời gian lịch; thời gian thực còn phụ thuộc số run song song, license và overhead runner. Ở W3 chạy `--dry-run` và pilot để thay bằng số đo thật. Nếu vượt ngân sách: thu nhỏ pilot RQ1/RQ2 trước; không bỏ instance lớn hay thu hẹp RQ3.

**Môi trường (điền trước freeze, không để ở trạng thái giả định):** máy, CPU, RAM, hệ điều hành; phiên bản Python; OR-Tools, Gurobi, CPLEX/CP Optimizer; PySAT, CaDiCaL, Glucose, Kissat và cách gọi từng solver; git tag/commit; loại license và giới hạn kích thước model; memory limit, time limit, chính sách chạy song song.

## 12. Freeze policy

**Điều kiện tag `v1.0`** (dự kiến giữa W4; chỉ tag khi đủ tất cả):

1. Có đủ 24 file dữ liệu, `MANIFEST.csv` đã tạo, loader qua test cả 24 instance.
2. Correctness test và oracle/cross-solver check đạt.
3. Canonical SAT config đã chọn từ pilot, ghi lý do, đã review.
4. Runner thực thi memory limit thật; kill/resume đã kiểm thử.
5. Time limit của exact tính đúng cả thời gian build.
6. Tập con, RQ, time/memory limit, máy và version solver đã khóa; khả năng chạy và giới hạn license của từng solver đã ghi rõ.
7. P2 và P3 đã review các phần liên quan.

Nếu còn điều kiện chưa đạt, giữ `1.0-rc`; không tag chỉ để kịp mốc.

**Sau `v1.0`:**

- Được sửa: crash, bug, kết quả sai, validation fail, mất khả năng tái lập.
- Không sửa âm thầm: encoding, formulation, benchmark, RQ, cấu hình solver, time limit, protocol.
- Nếu buộc đổi methodology: ghi quyết định, tăng version, chạy lại toàn bộ phần bị ảnh hưởng.

## 13. Việc cần xong trước freeze

| Việc | Owner | Review | Xong khi |
|---|---|---|---|
| Xin thầy 24 file `.mtx.rnd` và hỏi ý nghĩa `.rnd` | P1 | — | Có đủ file, nguồn và định dạng được ghi nhận |
| Loader + `MANIFEST.csv` + test 24 instance | P2 | P3 | Đối chiếu n, m, chênh lệch sau làm sạch |
| Thực thi memory limit cứng trong runner | P3 | P1 | Có bằng chứng giới hạn được thực thi |
| Time limit của exact tính cả thời gian build | P1 | P3 | Test chứng minh tổng ngân sách đúng |
| Kiểm tra AMO pairwise có loại clause trùng | P2 | P1 | Có kết quả; rủi ro MO được xử lý hoặc ghi nhận |
| Kiểm tra license Gurobi/CPLEX và giới hạn kích thước model | P1 | — | Ghi rõ solver chạy được trên instance lớn |
| `--dry-run` và ước tính ngân sách thật | P3 | P1 | Bảng Mục 11 được cập nhật bằng số đo |
| Pilot RQ1/RQ2, chọn canonical config | P2 | P1 | Báo cáo trong `docs/` theo Mục 9.2 |
| Review protocol (Mục 3, 5, 9) và pipeline (Mục 7–8) | P2, P3 | P1 | Các điểm chặn freeze được xác nhận |

Phân công theo vai trò trong work breakdown; giao task chính thức thực hiện trên GitHub.

## 14. Tài liệu tham khảo

- Fazekas, Sinnl, Biere, Parragh (2020). Duplex encoding of staircase at-most-one constraints for the antibandwidth problem.
- Sinnl (2021). A note on computational approaches for the antibandwidth problem. CEJOR 29(3).
- Truong, Kieu, To (2025). Sequential Counter Encoding for Staircase At-Most-One Constraints. ICAART 2025.
- Rodriguez-Tello, Romero-Monsivais, Ramírez-Torres, Lardeux (2015). Harwell–Boeing graphs for the CB problem.

Các công trình trên dùng máy, symmetry breaking và cấu hình khác với protocol này, nên không so sánh trực tiếp số liệu runtime.
