# Bộ dữ liệu Harwell–Boeing cho bài toán ABP

## Nguồn dữ liệu chính thức

Trang Optsicom mô tả bộ benchmark Harwell–Boeing cho Antibandwidth Problem (ABP) gồm 24 đồ thị: 12 đồ thị nhỏ và 12 đồ thị lớn. Các cạnh được xây dựng từ các phần tử khác 0 của ma trận.

- Trang dữ liệu: https://grafo.etsii.urjc.es/optsicom/abp.html
- Tệp tải được liên kết từ trang chính thức: https://grafo.etsii.urjc.es/optsicom/abp/hb.zip

Tại máy chạy kiểm tra ngày 27/10/2026, tệp ZIP đã tải có SHA-256:

`C7B39A13A37707A09F36408273DB75D6A8BC1CB40E071AC960C724E1F58F6E7E`

24 tệp `.mtx.rnd` đã được kiểm tra bằng `scripts/inspect_hb.py`. Tất cả 24 dòng trong `MANIFEST.csv` có trạng thái `VALID`. Các tệp dữ liệu thô hiện được giữ cục bộ trong `benchmark/hb/raw/`, không được commit lên Git; manifest lưu SHA-256 và các số liệu được tính từ từng tệp.

## Phân biệt danh sách tham chiếu và kết quả kiểm tra

- `instances.csv`: danh sách 24 instance, gồm tên chuẩn và các giá trị tham chiếu từ tài liệu đã công bố (`n`, `m_table`, cận ABP tham khảo). Đây không phải số liệu được đọc trực tiếp từ tệp dữ liệu cục bộ.
- `MANIFEST.csv`: kết quả kiểm tra tệp thực tế, gồm SHA-256, kích thước header, số dòng cạnh, số cạnh sau làm sạch, số self-loop/cạnh trùng bị loại, bậc lớn nhất `delta_max` và cận `ub_n_minus_delta = n - delta_max`.

Kết quả hiện tại: 24/24 tệp `VALID`; tất cả đều khớp `n` và `m` tham chiếu, không có self-loop hoặc cạnh vô hướng trùng lặp. Giá trị `delta_max` và `UB` trong manifest được tính từ danh sách cạnh thực tế.

## Cách kiểm tra lại

Giải nén đúng các tệp danh sách cạnh ABP vào `benchmark/hb/raw/` (giữ nguyên tên chuẩn, bao gồm dấu gạch dưới kép), sau đó chạy tại thư mục gốc repository:

```powershell
uv run python scripts/inspect_hb.py
```

Lệnh sẽ tạo/cập nhật `benchmark/hb/MANIFEST.csv`. Các trạng thái `MISSING`, `INVALID_FORMAT`, `REFERENCE_MISMATCH` và `INVALID_GRAPH` cần được điều tra; không được thay bằng số tham chiếu để tạo kết quả có vẻ hợp lệ.

## Các lệnh liên quan khác

```powershell
uv run python scripts/dry_run_benchmark.py --stage pilot-rq1 --output results/pilot-rq1-plan.csv
uv run python scripts/dry_run_benchmark.py --stage pilot-exact --output results/pilot-exact-plan.csv
uv run python scripts/dry_run_benchmark.py --stage pilot-large --output results/pilot-large-plan.csv
uv run python scripts/dry_run_benchmark.py --stage official --output results/official-plan.csv
uv run python scripts/estimate_hb_cnf.py --name can__715
```

`dry_run_benchmark.py` chỉ kiểm tra ma trận kế hoạch, số run và sự hiện diện của dữ liệu; nó không phải hàng đợi thực thi, không chạy solver và không tự áp giới hạn bộ nhớ. `estimate_hb_cnf.py` tính số biến/mệnh đề theo công thức ước lượng, không dựng toàn bộ CNF và không đo RAM đỉnh. Không dựng CNF lớn trước khi giới hạn bộ nhớ ở cấp hệ điều hành đã được kiểm chứng.

Nguồn tham chiếu cho các giá trị trong `instances.csv`: Sinnl (2021), bao gồm bảng tham chiếu lại Lozano et al. (2012): https://link.springer.com/article/10.1007/s10100-020-00688-4
