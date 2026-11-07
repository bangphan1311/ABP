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
| Kiểm thử tự động | `LOCAL_FULL_SUITE_PASS_REPORTED; FINAL_CANDIDATE_RERUN_REQUIRED` | Bằng chứng cũ: `uv run pytest tests -q` → **511 passed in 21.31s** trên commit được ghi trong preflight. PR #52 báo cáo 514 passed/3 skipped nhưng review P1 phát hiện freeze doc ghi 512/3; P2 phải đối chiếu log và commit thật. Chạy lại suite trên freeze candidate sau khi PR #52 được sửa và nhánh được đồng bộ. |
| Kiểm tra nhanh solver | `TINY_PROBES_PASS; LARGE_MODEL_LIMITS_SEPARATELY_CHECKED` | Smoke test nhỏ PASS cho CP-SAT, CaDiCaL, Glucose, Gurobi MIP, CPLEX MIP và CPLEX CP. Tiny probe chỉ chứng minh mô hình nhỏ chạy được, không chứng minh năng lực xử lý instance benchmark. |
| Máy candidate do P1 chọn | `P1_SELECTED; RECHECK_BEFORE_RUN` | Windows 10.0.26200; Python 3.11.16; AMD64; 12 logical CPUs; RAM 15.21 GiB. P1 chọn cap 12.0 GiB/run và 1 worker tuần tự; script exact-pilot từ chối chạy nếu OS build/RAM không đạt điều kiện. |
| Phiên bản gói ghi nhận | `LOCAL_ENVIRONMENT` | OR-Tools 9.15.6755; python-sat 1.9.dev15; pytest 9.1.1; gurobipy 13.0.3; cplex 22.2.0.1; docplex 2.32.264. `psutil` không có; script preflight có fallback đọc RAM trên Windows. |
| Gurobi MIP | `ACADEMIC_LICENSE_TINY_PROBE_PASS` | Đã cấu hình `GRB_LICENSE_FILE` trong PowerShell hiện tại và mô hình binary nhỏ trả `PROBE_OK`, license được nhận diện là Academic/non-commercial. Không ghi license ID, email, file license hoặc secret vào repository. Chưa có bằng chứng benchmark thực trên máy official. |
| CPLEX MIP | `COMMUNITY_EDITION_SIZE_LIMIT_CONFIRMED` | Tiny probe PASS; probe riêng với 1.001 biến nhị phân và 1.001 ràng buộc bị CPLEX báo lỗi 1016: Community Edition problem size limits exceeded. Chưa có CPLEX Academic license được xác minh. |
| CPLEX CP / CP Optimizer | `COMMUNITY_EDITION_SEARCH_LIMIT_CONFIRMED` | Tiny probe PASS; probe 1.001 biến nhị phân bị giới hạn search space vượt (2^{1000}). Chưa có CP Optimizer Academic license được xác minh. |
| Kissat native | `NOT_VERIFIED` | `kissat` không có trên PATH ở lần preflight. Không tính Kissat vào RQ2 cho đến khi một binary native riêng được xác minh; protocol cho phép giới hạn RQ2 ở CaDiCaL và Glucose nếu Kissat không khả dụng và ghi rõ limitation. |
| Giới hạn bộ nhớ cấp hệ điều hành | `CI_PASS; LOCAL_WINDOWS_TEST_PASS_REPORTED; P3_OFFICIAL_HOST_SIGNOFF_PENDING` | Có CI Ubuntu/Windows (run [40622690634](https://github.com/bangphan1311/ABP/actions/runs/40622690634)) và local Windows test được báo cáo: cap test 0.125 GiB, worker cấp phát 192 MiB, assert `MO`/`MemoryError`. Điều này chứng minh đường kiểm thử Job Object hoạt động, nhưng không thay thế P3 sign-off hard-kill trên host/config official. Exact Pilot 40-run dùng cap cấu hình 12 GiB nhưng raw `peak_memory=null`; không có số đo peak RAM từ pilot. POSIX `RLIMIT_AS` và Windows Job Object giới hạn loại tài nguyên khác nhau. |
| Checkpoint / kill / resume | `CI_PASS; LOCAL_WINDOWS_FULL_SUITE_PASS_REPORTED; P3_OFFICIAL_SIGNOFF_PENDING` | Checkpoint SAT lưu incumbent đã qua `verify()`; runner đối chiếu instance/config/run ID, xác minh lại nghiệm và giữ audit trail. CI/local tests có bằng chứng cho SAT checkpoint, hard kill, resume và audit. P3 vẫn cần xác nhận theo host/config official, kể cả attempt history và nguyên tắc không ghi đè raw attempt cũ; lưu ý exact solvers chưa checkpoint incumbent trong quá trình tối ưu. |
| Ngân sách thời gian | `IMPLEMENTED_AND_TESTED; FINAL_REVIEW_PENDING` | Code exact truyền phần thời gian còn lại sau model build; nếu build đã dùng hết ngân sách thì không bắt đầu search. Có test ở `tests/exact/test_time_budget.py`; full local suite được báo cáo PASS. P2/P3 cần xác nhận contract, code và status accounting thống nhất trong review cuối. |
| Dry-run / ước lượng CNF | `PLAN_ONLY_TOOLS_AVAILABLE` | `scripts/dry_run_benchmark.py` sinh ma trận kế hoạch, không gọi solver và không enforce memory limit; `scripts/estimate_hb_cnf.py` là ước lượng công thức, không dựng CNF hoặc đo peak RAM. Trước freeze cần lưu đầu ra plan/estimate, kiểm tra số run và ghi rõ ước lượng không phải số đo thực nghiệm. |
| W3 pilot và canonical SAT config | `PILOT_COMPLETE_SYNTHETIC; GROUP_SIGNOFF_PENDING` | P2 đã merge PR #51 ngày 01/11/2026. Pilot chạy trên 10 đồ thị synthetic cố định (8 validation n=8..28, 2 large n=40,50), time limit 60 s/run; không phải 24 đồ thị Harwell–Boeing. RQ1: `order` 10/10 OPT; hai cấu hình `pairwise` 9/10 OPT + 1 FEAS. RQ2: cả 4 PySAT solver 10/10 OPT; trong Core `{cadical195, glucose4}`, `glucose4` có PAR2/tổng thời gian 17.13 s so với 23.24 s của CaDiCaL; `minisat22` nhanh nhất toàn bộ 4 solver (16.61 s) nhưng là baseline ngoài Core. `docs/canonical_sat_config.md` trên `main` đề xuất `order/pairwise/glucose4` theo Core; P1 đã xác nhận lựa chọn này trong review PR #52, còn sign-off P3 và việc cố định memory cap trong frozen run plan vẫn chờ. PR #52 đang đưa cấu hình này vào code. Không dùng pilot synthetic làm kết quả official RQ3. |
| Máy candidate và phạm vi solver | `P1_SELECTED; FINAL FREEZE GATES OPEN` | P1 chọn snapshot Windows build `10.0.26200`, 12 logical CPUs, RAM 15.21 GiB làm candidate host; cap 12.0 GiB/run, một worker tuần tự (headroom khoảng 3.21 GiB). Gurobi Academic được phép thử tiếp nhưng cần benchmark-scale evidence; CPLEX MIP/CP giữ trong kế hoạch, mọi Community Edition size/license failures ghi `ERR`; Kissat native chưa xác minh nên loại khỏi RQ2 Core; canonical SAT theo Core là `order/pairwise/glucose4`. Recheck host/version/license trước pilot và official; không tag v1.0 khi các gate khác còn mở. |


## 1.1. Cập nhật tích hợp GitHub (06/11/2026)

- P2 PR #51 (`p2/w3-pilots`) đã merge vào `main` ngày 01/11/2026, commit merge `276c6c0`; gồm pilot RQ1/RQ2, CSV kết quả và bản nháp technical appendix.
- P2 PR #52 (`p2/w4-sat`) vẫn mở. P1 review đang `CHANGES_REQUESTED` với sáu mục: G3 expected-run denominator; lọc trục RQ1/RQ2; default memory cap rỗng; triage thiếu instance; lệch test count 514/3 so với 512/3; PR summary chưa khai báo runner changes. P2 cần sửa và đính kèm test evidence trước re-review.
- PR P1 #50 vẫn mở; nhánh `p1/w3-experimental-protocol-rc` đang diverged so với `main` (compare mới nhất 07/11/2026: **87 ahead / 11 behind**). Đồng bộ sau khi PR #52 xử lý xong để tránh giải conflict nhiều lần; sau sync chạy lại full suite.
- PR #50 và #52 chưa được merge; chưa tạo tag `v1.0`.
- P1 đã cập nhật `docs/exact_models.md` về formulation, cận độ bậc và timing; thêm/cập nhật `docs/p1/w3-w4-exact-readiness.md` làm checklist W3–W4 và bảng UB cho 24 instance.
- Loader `.mtx.rnd` đã được tích hợp trực tiếp vào shared `read_instance()`; CI có parser/hash/manifest và `run_one()` fixture tests. Không còn blocker adapter HB ở mức code. P3 vẫn phải sign-off pipeline chính thức: raw output → validation → `runs.csv`, resource limits và checkpoint/resume.
- Đường dẫn `docs/sat_spec.md` được protocol viện dẫn không tồn tại trên nhánh PR hiện tại. Protocol đã được cập nhật để tham chiếu bản draft hiện có `docs/handoff/w2-sat/14-sat-methodology.md`; cần P2 xác nhận đây là spec ràng buộc trước freeze.

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


### Ước lượng kích thước CNF cho instance lớn nhất

Từ `MANIFEST.csv`, `can__715` có (n=715), (m=2975), (Delta=104), nên (UB=n-Delta=611). Đếm công thức (không dựng CNF, không đo RAM) tại (K=UB=611) cho thấy rủi ro kích thước rất lớn:

| Encoding | Biến ước lượng | Clause ước lượng tại K=611 |
|---|---:|---:|
| Pairwise ABP + AMO pairwise | 511,225 | 1,851,296,330 |
| Pairwise ABP + AMO sequential counter | 1,532,245 | 1,489,343,310 |
| Order encoding | 510,510 | 1,669,297,370 |

Trong cả ba cấu hình, riêng distance clauses ước lượng là 1,486,280,250 tại (K=611). Đây là **cận cảnh báo theo công thức**, không phải số đo RAM hoặc số liệu từ một CNF đã dựng; số clause thực tế của run phụ thuộc K từng lần dò. Dự toán sequential-counter dùng dạng chuẩn (n-1) biến phụ và (3n-4) clause mỗi ràng buộc AMO; phải xác minh lại bằng `scripts/estimate_hb_cnf.py --name can__715 --k 611` trong môi trường dự án có PySAT.

Hệ quả thực tế: không chạy pilot-large hoặc official SAT trên `can__715` chỉ vì CI pass. Trước hết P3 phải xác nhận worker bị chặn đúng bởi memory cap; sau đó pilot-large phải chạy tuần tự/kiểm soát tài nguyên và lưu raw evidence. Nếu estimate/tool output khác các số trên, điều tra công thức hoặc phiên bản encoder trước khi freeze.


## 4. Gates còn mở trước freeze

1. **Host candidate do P1 chọn:** dùng Windows build `10.0.26200`, 12 logical CPUs, RAM 15.21 GiB; cap 12.0 GiB/run và một worker tuần tự. Trước mỗi đợt, kiểm tra host còn khớp snapshot; nếu khác thì dừng và cập nhật protocol.
2. **Chốt khả năng dùng solver:** Gurobi Academic tiny probe đã PASS. CPLEX MIP/CP hiện bị chặn bởi Community Edition ở probe lớn; xin Academic license hoặc ghi quyết định nhóm về phạm vi/nhãn `ERR`. Xác minh Kissat native hoặc loại khỏi RQ2 theo phương án contingency trong protocol.
3. **Memory limit:** P1 chọn 12.0 GiB/run trên Windows, một worker. Local full-suite report 511 passed trước đó chứa test cap 0.125 GiB/worker 192 MiB và assert `MO`/`MemoryError`; CI W3 kiểm tra thêm runner trên Windows/Ubuntu. Đây là bằng chứng enforcement mức kiểm thử, không thay thế kiểm tra lần cuối trên đúng host trước pilot/official.
4. **Checkpoint/resume:** CI và local full-suite report bao gồm test hard kill, restore incumbent SAT đã verify, và audit trail/corrupt JSON. Nếu chọn máy Windows snapshot làm official host, ghi nhận evidence này. Exact incumbent checkpoint chưa được implement; giữ rõ giới hạn này, không tuyên bố exact có khả năng resume incumbent.
5. **Final review của P2/P3:** P2 xác nhận tài liệu SAT spec chính thức (hiện có bản draft `docs/handoff/w2-sat/14-sat-methodology.md`), ánh xạ khoảng cách/K-search, cận `UB = n - Δ`, correctness và pilot design. P3 xác nhận runner/schema, kill/resume, memory/status, thời gian tổng và dry-run/budget. Ghi quyết định cho từng góp ý thay vì để trạng thái mơ hồ.
6. **Pilot và canonical config:** pilot RQ1/RQ2 W3 đã được chạy và merge qua PR #51 trên tập synthetic (10 instance, 60 s/run), có CSV và raw evidence trong branch P2 trước khi merge. `docs/canonical_sat_config.md` đề xuất `order/pairwise/glucose4` cho Core `{cadical195, glucose4}`; P1/P3 vẫn phải xác nhận lựa chọn và phạm vi solver trước M2 freeze. Không coi pilot synthetic là benchmark 24 instance HB; official RQ3 vẫn phải chạy trên dữ liệu HB theo protocol và lưu raw JSON.
7. **Freeze evidence:** kiểm tra số run/budget từ output plan và CNF estimate; test report 511 passed là trên code ở commit `799cfa0` (các commit `b1f37ef` và `a11911d` sau đó chỉ cập nhật tài liệu). Nếu có sửa code nữa, chạy lại full suite; gắn mọi số liệu với commit, cấu hình, máy và raw evidence.

## 4.1. HB loader integration — implemented; focused CI passed

`src.sat.loader.read_instance()` now accepts `.mtx.rnd` directly and
validates each file against the sibling `MANIFEST.csv` and `instances.csv`
(hash, header, edge counts, cleaning counts, `delta_max`, `UB=n-Δ`, and
inventory reference values). `src.runner.run_one()` and its worker can use
the raw file path directly; no private P1 parser or intermediate JSON is
required. Tests cover the parser and an end-to-end runner subprocess using a
small fixture. The Linux/Windows workflow now includes these tests; its
result must be checked before calling this gate PASS.

The remaining data-level limitation is separate: `benchmark/hb/raw/` is gitignored, so the source files must be present on the machine selected by P3 for the official queue. The 40-run HB validation-subset Exact Pilot has since completed on 2026-11-07; see §4.3 below. This does not sign off the official resource/host gates.

## 4.2. CI bằng chứng HB loader và P1 exact-pilot plan (06/11/2026)

- Workflow `W3 checkpoint, runner and HB loader tests` chạy trên commit `5bbfbdc0dc4be9c1065837caa51bc5807d0699d5`.
- Ubuntu: **23 passed in 4.92s**; Windows: **23 passed in 5.95s**. GitHub Actions run [42156873444](https://github.com/bangphan1311/ABP/actions/runs/42156873444), head `538a50a1bda772df4afac1aed22f298d10aa89f4`.
- Sau đó run [42346018670](https://github.com/bangphan1311/ABP/actions/runs/42346018670) trên commit `f3e8fe6fda6185741997541c1f081cf79a72851d` tiếp tục PASS: Ubuntu **23 passed in 4.89s**, Windows **23 passed in 6.48s**. Đây là focused subset (HB loader, exact-pilot plan, checkpoint/runner), không phải full `pytest tests -q`.
- `experiments/pilot_exact_p1.py` đã chạy đủ **40/40 HB validation exact runs** ngày 07/11/2026 (10 instance × 4 exact backend, 600 s/run, tuần tự, cap cấu hình 12 GiB). Kết quả: 11 OPT / 10 FEAS / 19 ERR (license/edition errors; không có TO/MO). Chi tiết ở `docs/p1/exact_pilot_report_2026-11-07.md`. `--include-large` thêm 12 exact pilot-large runs nhưng **chưa thực hiện**.
- `docs/p1/exact_spot_check_plan.md` đóng băng trước danh sách 10 exact runs để P1 kiểm tra độc lập khi P3 hoàn tất official queue. Danh sách dùng canonical instance IDs `can_445` và `can_715` (display names `can__445`, `can__715`).
- 24 raw `.mtx.rnd` source files không nằm trong Git vì `benchmark/hb/raw/` được gitignore. Branch P1 hiện có đủ 40 raw JSON records trong `results/pilot_exact/raw/` và `summary.csv` (đã kiểm tra directory listing trên GitHub).

## 5. Quyết định hiện tại

**Giữ phiên bản `1.0-rc`; chưa tạo tag `v1.0`.** P1 đã hoàn thành code/integration, UB audit, formulation docs, vòng review protocol đầu và Exact Pilot 40/40. P1 còn: independent verify các pilot solutions; chốt cách trình bày giới hạn Gurobi/CPLEX; đồng bộ nhánh sau khi PR #52 ổn định; chạy full suite trên freeze candidate; và thực hiện 10-run spot-check exact khi P3 có official outputs. P2 còn: sửa sáu blocker PR #52 và xác nhận SAT spec/canonical config. P3 còn: sign-off runner/schema, hard memory cap/kill-resume/checkpoint, dry-run/budget, validation pipeline và vận hành official queue. Pilot-large chưa chạy vì chờ memory gate; official RQ3 chưa chạy. Không tag `v1.0` trước khi mọi điều kiện §12 có evidence.

PR theo dõi: https://github.com/bangphan1311/ABP/pull/50


## 4.3. HB Exact Pilot thực tế (07/11/2026)

| Backend | OPT | FEAS | ERR |
|---|---:|---:|---:|
| CP-SAT | 6 | 4 | 0 |
| Gurobi MIP | 0 | 1 | 9 |
| CPLEX MIP | 0 | 0 | 10 |
| CPLEX CP | 5 | 5 | 0 |
| **Total** | **11** | **10** | **19** |

Toàn bộ 19 `ERR` là license/edition blocks: 9 Gurobi size-limited-license và 10 CPLEX Community Edition error 1016. Không có `TO` hoặc `MO`. Raw JSON lưu `memory_limit=12.0`; tuy nhiên trường `peak_memory` không có số đo (null), nên không dùng pilot này làm bằng chứng đo peak RAM hoặc thay cho hard-memory kill test/sign-off của P3. Report chi tiết theo instance/backend và PAR2: `docs/p1/exact_pilot_report_2026-11-07.md`.

Đây là engineering pilot trên 10 HB validation instances, không phải official RQ3. Giữ nguyên toàn bộ raw attempts; không chuyển ERR thành TO.
