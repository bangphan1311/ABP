# Experimental Protocol — Antibandwidth Problem (ABP)

**Phiên bản:** 1.0-rc  
**Trạng thái:** đã nhận review W3; chờ re-review sau cập nhật và xử lý các mục chặn freeze (Mục 12–13)  
**Dataset:** Harwell–Boeing, 24 instance  
**Owner:** P1 (coordinator)  
**Review:** P2, P3

Tài liệu này là nguồn duy nhất cho **thiết kế thực nghiệm**. [`docs/sat_spec.md`](sat_spec.md) ghi đặc tả W1 cho pairwise và K-search; [`docs/handoff/w2-sat/14-sat-methodology.md`](handoff/w2-sat/14-sat-methodology.md) mở rộng phần giải thích cho order encoding và AMO. Đây là tài liệu đặc tả/nháp methodology hiện có, phải được review đối chiếu với code và `CONTRACT.md`, không thay thế các giới hạn thực nghiệm trong protocol. P1/P2 phải review chéo ánh xạ `|p − q| < K` (cặp nhãn bị cấm) với `|f(u) − f(v)| ≥ K` (điều kiện cần thỏa) trước freeze. Khi các điều kiện ở Mục 12 được đáp ứng và nhóm xác nhận, protocol được khóa bằng tag `v1.0`.

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

**RQ1 — Encoding (Validation subset).** ABP encoding và AMO encoding ảnh hưởng thế nào đến kích thước CNF và hiệu năng? Cố định CaDiCaL và search mode `multi`. Trục thiết kế là ABP {pairwise, order} × AMO {pairwise, sequential counter}, nhưng chỉ có **3 CNF khác nhau**: (pairwise, pairwise), (pairwise, seqcounter), (order, pairwise). Order encoding không dùng AMO nên (order, seqcounter) tạo CNF giống hệt (order, pairwise); không chạy cấu hình trùng chỉ để thay metadata. Khi báo cáo, AMO chỉ là biến thực nghiệm có ý nghĩa với pairwise encoding; với order, ghi `N/A` trong diễn giải nhưng giữ `amo_encoding = pairwise` cố định trong cấu hình máy để tái lập.

**RQ2 — SAT solver (Validation subset).** Với encoding và AMO tốt nhất từ RQ1, CaDiCaL, Glucose, Kissat khác nhau thế nào? Chỉ đổi solver.

**RQ3 — SAT vs Exact (Official, 24 instance).** Canonical SAT config so với Gurobi MIP, CPLEX MIP, CPLEX CP, CP-SAT dưới cùng protocol. Kèm phân tích độ khó: runtime và status theo n, |E|, density, bậc đỉnh; cactus plot, scatter, phân bố status. Không dùng từ "predict" vì dự án không xây dựng mô hình dự đoán.

Không có RQ4; Bonus không đánh số RQ. Mỗi RQ trình bày theo chuỗi: câu hỏi → thiết kế thí nghiệm → bằng chứng → kết luận. Không kết luận "A tốt hơn B" chỉ từ vài runtime.

## 5. Phương pháp giải

### 5.1. SAT (multi-run, non-incremental)

1. Khởi tạo `LB = 0`; có thể dùng heuristic để lấy incumbent ban đầu, nhưng thời gian heuristic tính vào `t_total`. Mọi incumbent phải qua `verify()` độc lập.
2. Cận trên hợp lệ tính từ bậc lớn nhất `Δ = max_v deg(v)`: `UB = n − Δ` (với instance có ít nhất một cạnh). Lý do: một đỉnh bậc `Δ` phải có `Δ` nhãn hàng xóm cách nhãn của nó ít nhất K, trong khi có nhiều nhất `n − K` nhãn khả dụng ở khoảng cách đó; vì vậy `K ≤ n − Δ`. P1/P2 phải xác nhận lập luận và kiểm tra `1 ≤ UB ≤ n − 1` trên toàn bộ instance trước freeze. Không dùng cận từ literature làm đầu vào solver.
3. Nếu incumbent đã verify có giá trị `B = UB`, về mặt toán học incumbent đạt cận trên. Tuy nhiên, theo contract/SAT methodology hiện tại, `ub` ngoài chỉ được kiểm tra và `OPT` vẫn cần bằng chứng UNSAT tại ngưỡng tiếp theo; **không** tự trả `OPT` chỉ từ cận ngoài. Tiếp tục probe `K = B + 1` để lưu bằng chứng UNSAT theo cơ chế hiện hành. Chỉ thay đổi quy tắc này nếu P1/P2 cập nhật đồng bộ `CONTRACT.md`, implementation và correctness tests trước freeze.
4. Với mỗi K, mã hóa CNF bài toán quyết định `|f(u) − f(v)| ≥ K`. Trong encoding nhãn `p, q`, các cặp có `|p − q| < K` bị cấm; do đó P1/P2 phải review ánh xạ này cùng `docs/sat_spec.md` để tránh lệch một đơn vị.
5. Nếu SAT: giải mã nghiệm, chạy `verify()`, tính antibandwidth thực tế `B`, cập nhật incumbent và đặt `K ← B + 1` (không chỉ `K + 1`). Nếu UNSAT tại K sau một incumbent đã verify B, thì B là tối ưu (`OPT`).
6. Mỗi lần gọi solver nhận **thời gian còn lại của ngân sách toàn run**, không được khởi động lại toàn bộ time limit cho từng K. Nếu hết ngân sách mà đã có incumbent hợp lệ nhưng chưa chứng minh tối ưu, trả `FEAS`; nếu chưa có incumbent hợp lệ, trả `TO`.
7. Labeling trả về nhưng không qua `verify()` không được nhận làm incumbent. Ghi rõ lỗi validation vào raw evidence và phân loại `ERR` theo `CONTRACT.md` (đầu ra sai/hỏng), không giả định nó là `FEAS` hoặc `TO` rồi bỏ qua lỗi.
8. Nếu không dùng heuristic trong implementation, bỏ qua nhánh heuristic; không được tự gán rằng incumbent đạt UB. Thời gian build/encode, heuristic và mọi lần gọi solver đều tính vào `t_total`.

### 5.2. Exact

P1 viết formulation, P2 review. MIP dùng biến nhị phân theo cạnh cho |f(u) − f(v)| ≥ K, tránh big-M yếu. Không tinh chỉnh riêng từng solver: dùng tham số mặc định, trừ các thiết lập chung (1 thread, time limit, memory limit, seed). Mọi khác biệt bắt buộc do API hoặc giới hạn solver phải được ghi nhận; không tuyên bố các solver chạy "giống hệt nhau" nếu thực tế không đúng.

## 6. Protocol chạy

### 6.1. Tài nguyên

- Cùng một máy cho mọi official run; 1 thread mỗi run; không warm start; không symmetry breaking.
- Mọi phương pháp nhận cùng một đồ thị đã qua loader (cùng format input).
- Số run song song sao cho tổng memory limit không vượt RAM vật lý.

### 6.2. Time limit

- Official: 1800 s mỗi (instance × phương pháp), đúng work breakdown.
- Pilot RQ1/RQ2: 1800 s mỗi run để chọn canonical config dưới cùng ngân sách thời gian với official benchmark.
- Pilot exact: 600 s mỗi run để kiểm tra trước formulation, license và khả năng vận hành; đây không phải so sánh hiệu năng cuối cùng.
- Pilot-large: 1800 s mỗi run để kiểm tra sớm timeout/memory trên 3 instance lớn dưới ngân sách gần official. Chỉ chạy sau khi P3 đã kiểm chứng hard memory limit trên một process thử nghiệm; không chạy khi memory cap chưa được enforce.
- Với SAT multi-run, giới hạn của một run là ngân sách cho **toàn bộ chuỗi K**, không phải từng lần gọi solver. Mỗi probe nhận thời gian còn lại (`max(0, deadline − now)`).
- `t_total` gồm thời gian build model/encoding, heuristic và mọi lần gọi solver. Với exact solver, time limit dành cho optimizer là `max(0, time_limit của run − t_build)`; không được cộng thời gian build vượt quá ngân sách rồi vẫn báo run như đúng hạn.
- Số liệu official là wall-time do runner đo. Runner kill cứng tại `time_limit + 30 s` chỉ để dự phòng khởi động/cleanup; 30 s không phải ngân sách solve thêm.

### 6.3. Memory limit

Mức mục tiêu: 30 GB mỗi run. Chỉ dùng mức này sau khi xác minh RAM vật lý và khả năng thực thi giới hạn trên máy chạy; nếu không đáp ứng, chốt ngưỡng thấp hơn trước freeze, ghi rõ trong paper và giảm số run song song.

Runner phải thực thi giới hạn bộ nhớ thật, không chỉ ghi `memory_limit` trong config. Chỉ ghi `MO` khi có bằng chứng run vượt giới hạn; lỗi không rõ nguyên nhân thì điều tra, không tự gán `MO`.

### 6.4. Seed, lặp, resume

- Mỗi cặp (instance × phương pháp × cấu hình) chạy 1 lần, `seed = 0`. Hạn chế: runtime không có khoảng tin cậy từ nhiều lần chạy; nêu trong Limitations.
- `resume` chỉ được skip khi raw JSON đọc được, schema hợp lệ, `run_id` và cấu hình lưu khớp cấu hình được yêu cầu, và record qua validation. File hỏng/thiếu trường, `ERR` hoặc record không khớp phải được xem là cần điều tra/chạy lại, không skip im lặng.
- Khi chạy lại, giữ lịch sử attempt cũ (archive hoặc lưu tách theo attempt); không ghi đè raw evidence duy nhất. Chỉ `runs.csv` mới nhất được chọn sau validation, còn mọi attempt raw vẫn truy vết được.
- Worker/solver phải checkpoint incumbent **đã verify** sau mỗi probe K (ghi atomically). Nếu bị kill cứng, runner đọc checkpoint, tự verify lại trên instance gốc rồi ghi `FEAS` nếu incumbent còn hợp lệ; nếu không có incumbent hợp lệ thì `TO`. Checkpoint hỏng hoặc labeling không hợp lệ được ghi nhận là lỗi validation, không dùng làm nghiệm.

## 7. Status và validation

| Status | Định nghĩa |
|---|---|
| `OPT` | Nghiệm đã verify và có certificate tối ưu |
| `FEAS` | Nghiệm đã verify, chưa chứng minh tối ưu khi hết ngân sách |
| `TO` | Hết giờ, chưa có nghiệm verify |
| `MO` | Vượt memory limit đã cấu hình |
| `ERR` | Lỗi thực thi, license, output hỏng hoặc lỗi khác làm run không hoàn thành đúng quy trình |

Lỗi license ghi `ERR`, không ghi `TO`. Output có labeling không hợp lệ hoặc không khớp objective cũng là lỗi validation (`ERR`) theo `CONTRACT.md`; tuyệt đối không dùng labeling đó làm incumbent. Nếu chỉ hết giờ và không có labeling hợp lệ nào, status là `TO`.

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

1. **RQ1:** 10 instance × 3 cấu hình CNF khác nhau (CaDiCaL) = 30 run → chọn ABP encoding/AMO. Không chạy cấu hình order × seqcounter trùng CNF với order × pairwise.
2. **RQ2:** thêm Glucose và Kissat (chỉ nếu đã xác minh chạy đúng) với cấu hình vừa chọn. Nếu cả hai khả dụng: tối đa 20 run mới; 10 run CaDiCaL được tái sử dụng từ RQ1. Nếu Kissat không khả dụng: chỉ thêm 10 run Glucose và nêu rõ giới hạn so sánh.
3. **Pilot exact:** 10 instance × 4 exact solver = 40 run (600 s/run; kiểm tra formulation, license, tài nguyên).
4. **Pilot-large:** 3 instance × (3 cấu hình CNF khác nhau của RQ1 với CaDiCaL + 4 exact solver) = 21 run (1800 s/run), để lộ sớm CNF quá lớn, MIP yếu, vấn đề memory và kiểm tra kill/resume. Chỉ bắt đầu sau test hard memory limit; kết quả pilot-large không dùng để đổi quy tắc chọn canonical config.

Nếu một solver không khả dụng, ghi lại số run thực tế và lý do; không giữ nguyên tổng dự kiến như thể mọi run đã xong.

### 9.2. Quy tắc chọn (ghi trước khi chạy official)

So sánh theo thứ tự:

1. Nhiều instance `OPT` hơn.
2. Hòa: PAR2 thấp hơn. Với mỗi batch, run không `OPT` bị phạt `2 × time_limit` của chính batch đó: 3600 s cho RQ1/RQ2 (1800 s/run), 1200 s cho pilot exact (600 s/run); áp dụng nhất quán cho `FEAS`, `TO`, `MO`, `ERR` và run thiếu chưa được thay thế hợp lệ.
3. Hòa: `peak_memory` trung vị thấp hơn.
4. Hòa: `clauses` trung vị thấp hơn; với order encoding, `amo_encoding` là no-op và không dùng như chỉ số phân biệt cấu hình.

Không loại run bất lợi nếu không có lý do kỹ thuật được ghi nhận. Run lỗi/thiếu cần được lưu trong audit trail và chạy lại theo cùng cấu hình; khi tính PAR2, chỉ thay bằng attempt hợp lệ mới sau validation, không xóa dấu vết attempt cũ. Kết quả pilot, quy tắc đã áp dụng và lý do chọn lưu tại `docs/canonical_sat_config.md` trước M2.

Cố định toàn bộ benchmark: `search_mode = multi`, `symmetry = false`, `warm_start = false`.

## 10. Official run

Chỉ bắt đầu sau khi tag `v1.0`: 24 instance × 5 phương pháp (canonical SAT, CP-SAT, Gurobi MIP, CPLEX MIP, CPLEX CP) = 120 run dự kiến.

P3 vận hành official run và validation; P1 không vận hành queue chạy thực nghiệm (kiểm tra ngẫu nhiên khoảng 10 run exact).

Pipeline: configuration → runner → mỗi run một subprocess → raw JSON → validation → `runs.csv` → figure/table.

Run `ERR` hoặc thiếu được điều tra và chạy lại ở W5. Nếu license không cho phép chạy một instance, ghi `ERR` cùng lý do, không đổi thành `TO`.

## 11. Ngân sách và môi trường

Core-giờ worst case = (số run × time limit) / 3600.

| Giai đoạn | Số run | Time limit | Core-giờ worst case |
|---|---:|---:|---:|
| Pilot RQ1 (3 cấu hình CNF duy nhất) | 30 | 1800 s | 15,0 |
| Pilot RQ2 (run mới; nếu Glucose + Kissat đều dùng được) | tối đa 20 | 1800 s | tối đa 10,0 |
| Pilot exact | 40 | 600 s | 6,7 |
| Pilot-large (3 SAT + 4 exact × 3 instance) | 21 | 1800 s | 10,5 |
| Official RQ3 | 120 | 1800 s | 60,0 |
| **Tổng worst case** | **231** | — | **102,2** |

Nếu Kissat không qua xác minh và RQ2 chỉ dùng Glucose, RQ2 còn 10 run mới (5,0 core-giờ), tổng dự kiến giảm còn 97,2 core-giờ và 221 run bao gồm official. Đây là ngân sách CPU worst case, không phải cam kết thời gian lịch; thời gian thực còn phụ thuộc số run song song, license và overhead runner. Pilot-large chỉ chạy sau khi test hard memory limit pass. `--dry-run` phải cập nhật dự toán bằng số đo thật trước freeze; nếu vượt ngân sách, thu nhỏ RQ1/RQ2 trước, không bỏ instance lớn hay thu hẹp RQ3.

**Môi trường (điền trước freeze, không để ở trạng thái giả định):** máy, CPU, RAM, hệ điều hành; phiên bản Python; OR-Tools, Gurobi, CPLEX/CP Optimizer; PySAT, CaDiCaL, Glucose, Kissat và cách gọi từng solver; git tag/commit; loại license và giới hạn kích thước model; memory limit, time limit, chính sách chạy song song.

## 12. Freeze policy

**Điều kiện tag `v1.0`** (dự kiến giữa W4; chỉ tag khi đủ tất cả):

1. Có đủ 24 file dữ liệu, `MANIFEST.csv` đã tạo, loader qua test cả 24 instance.
2. Correctness test và oracle/cross-solver check đạt.
3. Canonical SAT config được chọn từ pilot RQ1/RQ2, có raw JSON + report lựa chọn tại `docs/canonical_sat_config.md`, và được P1/P2/P3 review.
4. Runner thực thi memory limit ở cấp process/OS; test process vượt ngưỡng bị chặn đúng và được phân loại `MO` đã lưu. Kill/resume test chứng minh checkpoint incumbent, validation lại và audit trail.
5. SAT và exact đều tính `t_total` theo toàn ngân sách run, bao gồm build/encoding; test xác minh thời gian còn lại truyền cho từng probe/optimizer.
6. Tập con, RQ, time/memory limit, máy và version solver đã khóa; khả năng chạy và giới hạn license của từng solver đã ghi rõ.
7. `docs/sat_spec.md` được review chéo P1/P2 cho semantics encoding/K-search; P2 và P3 xác nhận các góp ý protocol đã được xử lý hoặc có quyết định được ghi rõ.

Nếu còn điều kiện chưa đạt, giữ `1.0-rc`; không tag chỉ để kịp mốc.

**Sau `v1.0`:**

- Được sửa: crash, bug, kết quả sai, validation fail, mất khả năng tái lập.
- Không sửa âm thầm: encoding, formulation, benchmark, RQ, cấu hình solver, time limit, protocol.
- Nếu buộc đổi methodology: ghi quyết định, tăng version, chạy lại toàn bộ phần bị ảnh hưởng.

## 13. Việc cần xong trước freeze

| Đầu ra / việc cần làm | Owner | Review | Bằng chứng nghiệm thu bắt buộc |
|---|---|---|---|
| Xin thầy 24 file `.mtx.rnd`, xác minh ý nghĩa `.rnd`, xác nhận nguồn/định dạng | P1 | P2 | Cập nhật trạng thái từng file; lưu câu trả lời/nguồn vào `docs/w3_preflight.md`; không điền số liệu chưa xác minh |
| `instances.csv`, loader, `MANIFEST.csv` và test cả 24 instance | P2 | P3 + P1 | `benchmark/hb/instances.csv`, `benchmark/hb/MANIFEST.csv`; SHA-256, n/header m/cleaned m; test pass 24/24 hoặc danh sách lỗi cụ thể |
| Kiểm tra cận `UB = n − Δ` và review semantics encoding/K-search | P1 | P2 | Lập bảng `n, m, Δ, UB` cho 24 instance; P2 xác nhận lập luận và đối chiếu `docs/sat_spec.md` |
| Kiểm tra license Gurobi/CPLEX và inventory môi trường/máy/RAM | P1 | P2 + P3 | `docs/w3_preflight.md` có CPU, RAM, OS, Python, version solver, cách gọi, giới hạn license; không chứa secret/license key |
| Time limit SAT/exact tính cả build và toàn chuỗi K | P1 | P3 + P2 | Test xác nhận `t_total`, thời gian còn lại mỗi probe/optimizer, timeout và status theo contract |
| Kiểm tra AMO pairwise có clause trùng; xác nhận order AMO no-op | P2 | P1 | Test/report clause duplicate; bảng 3 cấu hình CNF khác nhau và lý do bỏ ô order × seqcounter khỏi pilot |
| Hard memory limit ở cấp process/OS | P3 | P1 | Test subprocess vượt cap bị kill; raw evidence chứng minh ngưỡng và status `MO`; xác nhận chạy trên đúng OS/máy official |
| Checkpoint incumbent + hard kill + resume/audit trail | P3 | P1 + P2 | Test kill sau một probe: incumbent được verify lại thành `FEAS`; không có incumbent hợp lệ thành `TO`; raw attempts cũ không bị ghi đè; resume không skip JSON hỏng/ERR |
| `--dry-run`, CNF estimate và budget | P3 | P1 + P2 | Lệnh không gọi solver; estimate vars/clauses/memory cho từng cấu hình trên n lớn (bao gồm n = 715) và budget được cập nhật trong Mục 11 |
| Pilot RQ1/RQ2 và chọn canonical config | P2 | P1 + P3 | Raw JSON cho từng run; validation pass; `docs/canonical_sat_config.md` ghi số OPT/status/PAR2/memory/clauses, khả năng solver và lý do chọn |
| Kiểm tra correctness suite + technical appendix | P2 | P1 | Test oracle/toy/random/edge cases pass; appendix giải thích assignment/permutation, AMO, distance và soundness/completeness của K-search |
| Review cuối protocol và freeze checklist | P1 điều phối; P2/P3 review | Cả nhóm | Mọi blocker được đóng bằng commit/test/evidence hoặc có quyết định nhóm được ghi; vẫn giữ `1.0-rc` nếu chưa đạt Mục 12 |

Phân công cụ thể theo vai trò trong work breakdown. Mỗi đầu ra phải có commit/PR hoặc raw test evidence gắn với issue; không đánh dấu xong chỉ dựa trên lời xác nhận miệng.

## 14. Tài liệu tham khảo

- Fazekas, Sinnl, Biere, Parragh (2020). Duplex encoding of staircase at-most-one constraints for the antibandwidth problem.
- Sinnl (2021). A note on computational approaches for the antibandwidth problem. CEJOR 29(3).
- Truong, Kieu, To (2025). Sequential Counter Encoding for Staircase At-Most-One Constraints. ICAART 2025.
- Rodriguez-Tello, Romero-Monsivais, Ramírez-Torres, Lardeux (2015). Harwell–Boeing graphs for the CB problem.

Các công trình trên dùng máy, symmetry breaking và cấu hình khác với protocol này, nên không so sánh trực tiếp số liệu runtime.
