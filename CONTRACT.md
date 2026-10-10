# CONTRACT — Quy ước chung của dự án ABP

## 1. Định nghĩa bài toán

Cho đồ thị vô hướng G = (V, E), với n = |V|.

Bài toán Antibandwidth (ABP) yêu cầu tìm một hoán vị
f: V → {1, ..., n} để cực đại hóa:

    ab(f) = min {|f(u) - f(v)| : (u, v) ∈ E}

Với một ngưỡng K, bài toán quyết định là xác định xem có tồn tại
hoán vị f: V → {1, ..., n} sao cho:

    |f(u) - f(v)| ≥ K, với mọi cạnh (u, v) ∈ E.

## 2. Instance

`Instance` mô tả một đồ thị đầu vào.

Các trường:

- `id`
- `name`
- `n`
- `edges`
- `source`
- `tier`

## 3. Config

`Config` mô tả cấu hình của một lần chạy solver.

Các trường:

- `method`
- `abp_encoding`
- `amo_encoding`
- `sat_solver`
- `search_mode`
- `symmetry`
- `warm_start`
- `seed`
- `time_limit`
- `memory_limit`

Lưu ý: `abp_encoding` và `amo_encoding` là hai trường riêng biệt.
Không gộp chúng thành một trường `encoding` chung.

## 4. Result

`Result` là định dạng kết quả chung mà các solver phải trả về.

Các trường:

- `status`
- `lb`
- `ub`
- `gap`
- `t_encode`
- `t_solve`
- `t_total`
- `variables`
- `clauses`
- `peak_memory`
- `solution`
- `metadata`

## 5. Quy ước trạng thái

- `OPT`: nghiệm đã được kiểm chứng và có chứng nhận tối ưu.
- `FEAS`: nghiệm đã được kiểm chứng nhưng chưa chứng minh tối ưu
  trước khi hết thời gian.
- `TO`: hết thời gian mà chưa có nghiệm được kiểm chứng.
- `MO`: hết bộ nhớ.
- `ERR`: lỗi thực thi, lỗi giấy phép, lỗi backend hoặc đầu ra bị hỏng.

Lỗi giấy phép phải được ghi là `ERR`, không được ghi là `TO`.

## 6. Kiểm chứng nghiệm

Hàm dùng chung:

    verify(instance, labeling)

Hàm phải:

- Kiểm tra labeling có phải hoán vị hợp lệ hay không.
- Kiểm tra đã gán nhãn đầy đủ cho các đỉnh.
- Kiểm tra không có nhãn trùng lặp.
- Tính lại giá trị mục tiêu từ labeling và đồ thị đầu vào.

Không chấp nhận nghiệm chưa qua kiểm chứng.

## 7. Quy trình tích hợp solver

Các solver phải dùng chung contract và trả về cùng định dạng `Result`.

Luồng xử lý của prototype CP-SAT:

    Instance → CP-SAT → solution → verify() → Result

## 8. Quy trình thay đổi

- Các thay đổi đối với contract chung cần được thống nhất trước khi tích hợp.
- Mỗi thành viên làm việc trên feature branch.
- Thay đổi được đưa vào `main` thông qua pull request.
- P2 và P3 review contract trước khi merge.

Sau khi contract được thống nhất và merge, tạo tag:

    v0.1-contract
