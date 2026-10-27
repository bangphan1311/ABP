# Kiểm tra trước thí nghiệm (W3) — ABP Harwell–Boeing

**Trạng thái:** `PARTIAL / NOT READY TO FREEZE`  
**Phụ trách:** P1 (điều phối)  
**Nhánh:** `p1/w3-experimental-protocol-rc`  
**Mục đích:** ghi lại bằng chứng đã có và các điều kiện còn thiếu. Tài liệu này không khẳng định toàn bộ benchmark đã sẵn sàng chạy chính thức.

## 1. Tóm tắt bằng chứng hiện có

| Hạng mục | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Nguồn dữ liệu | `CONFIRMED_FROM_SOURCE` | Trang Optsicom mô tả bộ ABP Harwell–Boeing gồm 24 đồ thị, chia thành 12 đồ thị nhỏ và 12 đồ thị lớn: https://grafo.etsii.urjc.es/optsicom/abp.html |
| Tệp ZIP chính thức | `DOWNLOADED_AND_HASHED_LOCALLY` | Tệp được liên kết từ trang Optsicom: https://grafo.etsii.urjc.es/optsicom/abp/hb.zip. SHA-256 của ZIP đã tải: `C7B39A13A37707A09F36408273DB75D6A8BC1CB40E071AC960C724E1F58F6E7E`. |
| Kiểm tra 24 tệp dữ liệu | `PASS_LOCAL_CHECK` | `benchmark/hb/MANIFEST.csv` có 24 dòng, tất cả `VALID`; `n` và `m` khớp giá trị tham chiếu; không phát hiện self-loop hoặc cạnh vô hướng trùng lặp. Các tệp dữ liệu thô vẫn nằm cục bộ trong `benchmark/hb/raw/`, không commit lên Git. |
| Số liệu đồ thị thực tế | `RECORDED_IN_MANIFEST` | Manifest ghi SHA-256 từng tệp, header, số dòng cạnh, `m_clean`, số cạnh bị loại, `delta_max` và `ub_n_minus_delta = n - delta_max`. |
| Kiểm thử tự động | `PASS_LOCAL_TEST_SUITE` | Lần chạy được báo cáo: `uv run pytest tests -q` → `506 passed`. Cần chạy lại trên commit cuối trước khi freeze. |
| Kiểm tra nhanh solver | `PASS_TINY_PROBES` | Các phép thử mô hình nhỏ đã PASS cho CP-SAT, CaDiCaL, Glucose, Gurobi MIP, CPLEX MIP và CPLEX CP. Đây chỉ là smoke test, không chứng minh license hoặc khả năng xử lý benchmark lớn. |
| Máy đã kiểm tra | `LOCAL_HOST_SNAPSHOT` | Windows 10.0.26200; Python 3.11.16; AMD64; 12 logical CPUs; RAM 15.21 GiB. Chưa xác nhận đây là máy chính thức dùng cho toàn bộ thí nghiệm. |
| Phiên bản gói ghi nhận | `LOCAL_ENVIRONMENT` | OR-Tools 9.15.6755; python-sat 1.9.dev15; pytest 9.1.1; gurobipy 13.0.3; cplex 22.2.0.1; docplex 2.32.264. `psutil` không có trong môi trường được kiểm tra. |
| Gurobi | `TINY_PROBE_PASS_LICENSE_LIMIT_UNRESOLVED` | Thông báo môi trường ghi nhận license restricted, non-production, hết hạn 2027-11-29. Phải xác minh giới hạn kích thước mô hình và quyền sử dụng cho benchmark; không suy ra từ tiny probe rằng mô hình lớn chạy được. |
| Kissat native | `NOT_VERIFIED` | Không tìm thấy executable `kissat` trên PATH tại lần kiểm tra. Không tính Kissat là solver đã sẵn sàng cho benchmark cho đến khi kiểm tra binary độc lập. |
| Giới hạn bộ nhớ cấp hệ điều hành | `CI_PASS; OFFICIAL_HOST_EVIDENCE_PENDING` | Runner đã có Windows Job Object giới hạn committed memory và POSIX `RLIMIT_AS` giới hạn virtual address space. Test cố cấp phát 192 MiB dưới cap 128 MiB cùng checkpoint/runner suite đã PASS trên GitHub Actions cho cả Linux và Windows: 13/13 mỗi OS ([CI run](https://github.com/bangphan1311/ABP/actions/runs/40447843675)). Hai OS giới hạn loại tài nguyên khác nhau; vẫn cần kiểm tra trên máy benchmark chính thức và khóa ngưỡng GiB phù hợp. |
| Checkpoint và khôi phục sau khi bị kill | `CI_PASS; OFFICIAL_HOST_TEST_PENDING` | Checkpoint nguyên tử cho incumbent SAT đã qua `verify()`; runner đối chiếu instance/config/run ID, xác minh lại nghiệm và chỉ phục hồi `FEAS` sau hard timeout. Bộ test checkpoint/runner hiện PASS 13/13 trên Linux và 13/13 trên Windows GitHub Actions: [run 40447843675](https://github.com/bangphan1311/ABP/actions/runs/40447843675). Còn cần test suite đầy đủ trên máy làm việc; exact solver chưa checkpoint incumbent trong quá trình tối ưu. |
| Dry-run của hàng đợi thực thi | `NOT_EQUIVALENT_TO_PLAN_CHECKER` | `scripts/dry_run_benchmark.py` kiểm tra ma trận kế hoạch, không phải hàng đợi thực thi tích hợp với runner; không chạy solver và không enforce giới hạn bộ nhớ. |
| License và máy chính thức | `PENDING_CONFIRMATION` | Cần xác nhận máy official, quyền dùng solver và giới hạn kích thước mô hình trước khi chạy benchmark chính thức. Không đưa license key, mật khẩu, token hoặc dump biến môi trường vào repository. |

## 2. Cách tái tạo kiểm tra dữ liệu

Từ thư mục gốc repository, sau khi tải và giải nén đúng các tệp danh sách cạnh ABP vào `benchmark/hb/raw/`, chạy:

```powershell
uv run python scripts/inspect_hb.py
```

Lệnh sẽ tạo/cập nhật `benchmark/hb/MANIFEST.csv`. Chỉ chấp nhận dữ liệu khi mọi instance có trạng thái hợp lệ và các sai khác so với giá trị tham chiếu đã được điều tra. Không đổi tên ma trận nguồn khác thành `.mtx.rnd` để ép qua kiểm tra.

Phân biệt:
- `instances.csv`: tên instance và số liệu tham chiếu đã công bố.
- `MANIFEST.csv`: số liệu được tính từ nội dung các tệp thực tế, bao gồm SHA-256, header, số cạnh, bậc lớn nhất và cận `UB = n - Δ`.

Nguồn đối chiếu số liệu tham chiếu: Sinnl (2021), bảng tham chiếu lại Lozano et al. (2012): https://link.springer.com/article/10.1007/s10100-020-00688-4.

## 3. Kiểm tra môi trường và solver

Chạy trong đúng môi trường dự định dùng để benchmark:

```powershell
uv run python scripts/w3_preflight_env.py
uv run python scripts/w3_preflight_env.py --probe-solvers
```

Lệnh thứ hai chạy các mô hình nhỏ cho CP-SAT, CaDiCaL, Glucose, Gurobi MIP, CPLEX MIP và CPLEX CP. Kết quả PASS chỉ chứng minh mô hình nhỏ đó chạy được ở môi trường hiện tại; không chứng minh license cho mô hình lớn, hiệu năng, hay máy hiện tại là máy official.

## 4. Điều kiện còn thiếu trước khi freeze

Các mục sau vẫn là blocker, không được đánh dấu hoàn tất chỉ dựa trên tiny probe hoặc trạng thái trong cấu hình:

1. **Xác nhận máy official:** chốt máy, hệ điều hành, CPU, RAM, Python, phiên bản solver và cách gọi solver; lưu bằng chứng kiểm tra từ chính máy đó.
2. **Xác minh license:** ghi loại license và giới hạn kích thước mô hình/quyền sử dụng của Gurobi, CPLEX MIP và CPLEX CP; nếu không chạy được, phải ghi rõ phạm vi thực nghiệm thực tế.
3. **Kissat:** cài/kiểm tra binary native độc lập hoặc ghi rõ Kissat không khả dụng; không tính là đã kiểm thử nếu chưa có bằng chứng.
4. **Hard memory limit:** Windows Job Object và POSIX `RLIMIT_AS` đã qua test cấp phát 192 MiB dưới cap 128 MiB trong GitHub Actions (13/13 test mỗi OS). Còn phải chạy trên máy benchmark official, kiểm tra record `MO`/lỗi `MemoryError`, rồi chốt cap thực tế theo GiB. Không đặt cap vượt RAM vật lý hoặc chạy pilot-large trước khi bằng chứng trên host official hoàn tất.
5. **Checkpoint/resume:** checkpoint SAT, khôi phục sau hard timeout, từ chối checkpoint bị sửa và không khớp cấu hình/instance đã qua 12 test tập trung trên Linux CI. Còn phải chạy test suite đầy đủ và xác minh trên máy Windows official; exact solver chưa checkpoint incumbent giữa quá trình tối ưu, nên không tuyên bố phần này đã hoàn tất cho chúng. Raw attempt cũ vẫn phải được giữ trong audit trail.
6. **Ngân sách thời gian:** xác minh `t_total` tính cả build/encoding và toàn bộ chuỗi K; mỗi solver nhận phần thời gian còn lại, không được khởi động lại time limit cho từng probe.
7. **Review và kiểm thử cuối:** chạy lại test suite trên commit chuẩn bị freeze; xử lý các nhận xét của P2/P3 trên PR #50 và ghi bằng chứng cho từng mục đã xử lý.

## 5. Quyết định hiện tại

**Giữ phiên bản `1.0-rc`; chưa tạo tag `v1.0`.** Dữ liệu 24 instance đã được kiểm tra và manifest đã có trên nhánh, nhưng các điều kiện về máy chính thức, license, hard memory limit, checkpoint/resume và review cuối chưa đủ bằng chứng để tuyên bố sẵn sàng chạy benchmark chính thức.

PR theo dõi: https://github.com/bangphan1311/ABP/pull/50
