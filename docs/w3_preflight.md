# Kiểm tra trước thí nghiệm (W3) — ABP Harwell–Boeing

**Trạng thái:** `PARTIAL / NOT READY TO FREEZE`  
**Phụ trách:** P1 (điều phối)  
**Nhánh:** `p1/w3-experimental-protocol-rc`  
**Mục đích:** ghi bằng chứng hiện có và các điều kiện còn thiếu. Không khẳng định benchmark chính thức đã sẵn sàng cho đến khi các gate ở Mục 4 được đóng.

## 1. Tóm tắt bằng chứng hiện có

| Hạng mục | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Nguồn dữ liệu | `CONFIRMED_FROM_SOURCE` | Trang Optsicom mô tả bộ ABP Harwell–Boeing gồm 24 đồ thị, chia thành 12 đồ thị nhỏ và 12 đồ thị lớn: https://grafo.etsii.urjc.es/optsicom/abp.html |
| Tệp ZIP chính thức | `DOWNLOADED_AND_HASHED_LOCALLY` | Tệp được liên kết từ trang Optsicom: https://grafo.etsii.urjc.es/optsicom/abp/hb.zip. SHA-256 của ZIP đã tải: `C7B39A13A37707A09F36408273DB75D6A8BC1CB40E071AC960C724E1F58F6E7E`. |
| Kiểm tra 24 tệp dữ liệu | `PASS_LOCAL_CHECK` | `benchmark/hb/MANIFEST.csv` có 24 dòng, tất cả `VALID`; `n` và `m` khớp giá trị tham chiếu; không phát hiện self-loop hoặc cạnh vô hướng trùng lặp. Các tệp dữ liệu thô nằm cục bộ trong `benchmark/hb/raw/`, không commit lên Git. |
| Số liệu đồ thị thực tế | `RECORDED_IN_MANIFEST` | Manifest ghi SHA-256 từng tệp, header, số dòng cạnh, `m_clean`, số cạnh bị loại, `delta_max` và `ub_n_minus_delta = n - delta_max`. |
| Kiểm thử tự động | `LOCAL_FULL_SUITE_PASS_REPORTED` | Lần chạy mới nhất được báo cáo trên máy Windows: `uv run pytest tests -q` → **511 passed in 21.31s**. Đây là kết quả local; chạy lại trên commit/code cuối trước khi freeze và giữ log làm bằng chứng. |
| Kiểm tra nhanh solver | `TINY_PROBES_PASS; LARGE_MODEL_LIMITS_SEPARATELY_CHECKED` | Smoke test nhỏ PASS cho CP-SAT, CaDiCaL, Glucose, Gurobi MIP, CPLEX MIP và CPLEX CP. Tiny probe chỉ chứng minh mô hình nhỏ chạy được, không chứng minh năng lực xử lý instance benchmark. |
| Máy đã kiểm tra | `LOCAL_HOST_SNAPSHOT; OFFICIAL_HOST_NOT_DECLARED` | Windows 10.0.26200; Python 3.11.16; AMD64; 12 logical CPUs; RAM 15.21 GiB. Snapshot đã được ghi nhận; nhóm vẫn phải xác nhận đây có phải máy benchmark chính thức hay không. |
| Phiên bản gói ghi nhận | `LOCAL_ENVIRONMENT` | OR-Tools 9.15.6755; python-sat 1.9.dev15; pytest 9.1.1; gurobipy 13.0.3; cplex 22.2.0.1; docplex 2.32.264. `psutil` không có; script preflight có fallback đọc RAM trên Windows. |
| Gurobi MIP | `ACADEMIC_LICENSE_TINY_PROBE_PASS` | Đã cấu hình `GRB_LICENSE_FILE` trong PowerShell hiện tại và mô hình binary nhỏ trả `PROBE_OK`, license được nhận diện là Academic/non-commercial. Không ghi license ID, email, file license hoặc secret vào repository. Chưa có bằng chứng benchmark thực trên máy official. |
| CPLEX MIP | `COMMUNITY_EDITION_SIZE_LIMIT_CONFIRMED` | Tiny probe PASS; probe riêng với 1.001 biến nhị phân và 1.001 ràng buộc bị CPLEX báo lỗi 1016: Community Edition problem size limits exceeded. Chưa có CPLEX Academic license được xác minh. |
| CPLEX CP / CP Optimizer | `COMMUNITY_EDITION_SEARCH_LIMIT_CONFIRMED` | Tiny probe PASS; probe 1.001 biến nhị phân bị giới hạn search space vượt (2^{1000}). Chưa có CP Optimizer Academic license được xác minh. |
| Kissat native | `NOT_VERIFIED` | `kissat` không có trên PATH ở lần preflight. Không tính Kissat vào RQ2 cho đến khi một binary native riêng được xác minh; protocol cho phép giới hạn RQ2 ở CaDiCaL và Glucose nếu Kissat không khả dụng và ghi rõ limitation. |
| Giới hạn bộ nhớ cấp hệ điều hành | `CI_PASS; TARGET_HOST_EVIDENCE_PENDING` | Runner dùng Windows Job Object cho committed memory và POSIX `RLIMIT_AS` cho virtual address space. Test cố cấp phát 192 MiB dưới cap 128 MiB cùng test runner/checkpoint đã PASS trên CI Ubuntu/Windows (13/13 mỗi OS ở run [40447843675](https://github.com/bangphan1311/ABP/actions/runs/40447843675)). Hai OS giới hạn loại tài nguyên khác nhau. Chưa chứng minh cap và status `MO` trên máy benchmark đã chốt. |
| Checkpoint / kill / resume | `CI_PASS; TARGET_HOST_TEST_PENDING` | Checkpoint SAT lưu incumbent đã qua `verify()`; runner đối chiếu instance/config/run ID, xác minh lại nghiệm và giữ audit trail. CI runner/checkpoint tests PASS trên Ubuntu và Windows ở run [40448079864](https://github.com/bangphan1311/ABP/actions/runs/40448079864). Exact solvers chưa checkpoint incumbent trong quá trình tối ưu; không tuyên bố tính năng đó đã hoàn tất cho exact. |
| Ngân sách thời gian | `IMPLEMENTED_AND_TESTED; FINAL_REVIEW_PENDING` | Code exact truyền phần thời gian còn lại sau model build; nếu build đã dùng hết ngân sách thì không bắt đầu search. Có test ở `tests/exact/test_time_budget.py`; full local suite được báo cáo PASS. P2/P3 cần xác nhận contract, code và status accounting thống nhất trong review cuối. |
| Dry-run / ước lượng CNF | `PLAN_ONLY_TOOLS_AVAILABLE` | `scripts/dry_run_benchmark.py` sinh ma trận kế hoạch, không gọi solver và không enforce memory limit; `scripts/estimate_hb_cnf.py` là ước lượng công thức, không dựng CNF hoặc đo peak RAM. Trước freeze cần lưu đầu ra plan/estimate, kiểm tra số run và ghi rõ ước lượng không phải số đo thực nghiệm. |
| Canonical SAT config | `NOT_SELECTED` | Chưa có `docs/canonical_sat_config.md` với raw pilot results, validation, status/PAR2/memory/clauses và lý do chọn cấu hình. Chưa chạy pilot chính thức theo protocol. |
| Máy chính thức và phạm vi solver | `PENDING_GROUP_DECISION` | Cần chốt máy/OS/RAM/cap, xác nhận Gurobi sẽ dùng trên máy đó, xử lý giới hạn CPLEX MIP/CP (xin Academic hoặc nhóm chấp nhận ghi `ERR` và giới hạn phạm vi báo cáo), và loại Kissat khỏi RQ2 nếu không xác minh được. |

## 2. Cách tái tạo kiểm tra dữ liệu

Từ thư mục gốc repository, sau khi dữ liệu danh sách cạnh ABP được giải nén vào `benchmark/hb/raw/`, chạy:

```powershell
uv run python scripts/inspect_hb.py
```

Lệnh sẽ tạo/cập nhật `benchmark/hb/MANIFEST.csv`. Chỉ chấp nhận dữ liệu khi mọi instance có trạng thái hợp lệ và các sai khác so với giá trị tham chiếu đã được điều tra. Không đổi tên ma trận nguồn khác thành `.mtx.rnd` để ép qua kiểm tra.

Phân biệt:
- `instances.csv`: tên instance và số liệu tham chiếu đã công bố.
- `MANIFEST.csv`: số liệu được tính từ nội dung tệp thực tế, gồm SHA-256, header, số cạnh, bậc lớn nhất và cận `UB = n - Δ`.

Nguồn đối chiếu số liệu tham chiếu: Sinnl (2021), bảng tham chiếu lại Lozano et al. (2012): https://link.springer.com/article/10.1007/s10100-020-00688-4.

## 3. Tái tạo preflight môi trường

Chạy trong đúng môi trường dự định dùng để benchmark:

```powershell
uv run python scripts/w3_preflight_env.py
uv run python scripts/w3_preflight_env.py --probe-solvers
```

Không xuất toàn bộ biến môi trường và không commit license file, key, token, password hoặc email/license identifier. Tiny probe không thay thế việc xác minh giới hạn kích thước, quyền sử dụng, binary native và chạy thử trên host đã chốt.

## 4. Gates còn mở trước freeze

1. **Chốt máy benchmark chính thức:** nhóm xác nhận máy, OS, CPU, RAM, Python/package/solver versions, policy chạy song song và memory cap. Snapshot RAM 15.21 GiB đã có; không cần đo lại chỉ để điền tài liệu.
2. **Chốt khả năng dùng solver:** Gurobi Academic tiny probe đã PASS. CPLEX MIP/CP hiện bị chặn bởi Community Edition ở probe lớn; xin Academic license hoặc ghi quyết định nhóm về phạm vi/nhãn `ERR`. Xác minh Kissat native hoặc loại khỏi RQ2 theo phương án contingency trong protocol.
3. **Memory limit trên target host:** kiểm tra process vượt cap thực sự bị chặn, raw result được phân loại `MO`, và cap không vượt ngân sách RAM an toàn của máy đã chốt. CI PASS không thay thế host evidence.
4. **Checkpoint/resume trên target host:** kiểm tra hard kill, restore incumbent SAT đã verify, trường hợp không có incumbent, dữ liệu raw hỏng/ERR và audit trail. Exact incumbent checkpoint chưa được implement; nếu giữ nguyên ngoài phạm vi, ghi rõ đây là giới hạn và không khẳng định exact có khả năng resume incumbent.
5. **Final review của P2/P3:** P2 xác nhận `docs/sat_spec.md`, ánh xạ khoảng cách/K-search, cận `UB = n - Δ`, correctness và pilot design. P3 xác nhận runner/schema, kill/resume, memory/status, thời gian tổng và dry-run/budget. Ghi quyết định cho từng góp ý thay vì để trạng thái mơ hồ.
6. **Pilot và canonical config:** chạy pilot RQ1/RQ2 theo protocol trên target host; lưu raw JSON, kiểm tra nghiệm, tổng hợp status/PAR2/clauses/memory và chọn canonical config trong `docs/canonical_sat_config.md`. Nếu chưa có dữ liệu pilot thì không được giả định đã chọn config.
7. **Freeze evidence:** kiểm tra số run/budget từ output plan và CNF estimate; chạy lại full test suite trên code cuối; tất cả số liệu báo cáo phải gắn với commit, cấu hình, máy và raw evidence.

## 5. Quyết định hiện tại

**Giữ phiên bản `1.0-rc`; chưa tạo tag `v1.0`.** Những phần đã có bằng chứng gồm manifest 24 instance, snapshot máy/RAM, local test-suite report, tiny probes, Gurobi Academic tiny probe và CI checkpoint/memory-limit tương ứng. Các blocker còn lại là quyết định máy official/phạm vi solver, kiểm thử trên target host, re-review P2/P3 và pilot/canonical SAT config. Không đánh dấu benchmark chính thức sẵn sàng chỉ dựa trên CI hoặc mô hình nhỏ.

PR theo dõi: https://github.com/bangphan1311/ABP/pull/50
