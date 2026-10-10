# Môi trường phát triển ABP

## 1. Thông tin máy

- Hệ điều hành: Windows (check_env.py báo Windows-10-10.0.26200-SP0)
- Python: 3.11.17
- CPU: AMD Ryzen 5 7535HS with Radeon Graphics
- RAM: 15.2 GB
- Môi trường Python: Conda, environment `abp`

Đây là môi trường phát triển hiện tại của P1.
Máy chạy thực nghiệm chính thức sẽ được nhóm xác nhận sau.

## 2. Phiên bản thư viện

| Thành phần        | Phiên bản |
| ----------------- | --------- |
| OR-Tools / CP-SAT | 9.15.6755 |
| gurobipy / Gurobi | 13.0.3    |
| cplex             | 22.2.0.1  |
| docplex           | 2.32.264  |
| pytest            | 9.1.1     |

## 3. Kết quả kiểm tra môi trường

Script `experiments/check_env.py` đã chạy thành công với:

- CP-SAT: chạy được mô hình thử nghiệm.
- Gurobi: chạy được mô hình thử nghiệm với WLS Academic.
- CPLEX MIP: chạy được mô hình thử nghiệm.
- CPLEX CP: chạy được mô hình thử nghiệm.

## 4. Trạng thái giấy phép và giới hạn

### Gurobi

- WLS Academic đã chạy thành công trên máy Windows.
- File license được lưu bên ngoài repository.
- Khi sử dụng biến môi trường `GRB_LICENSE_FILE`, cần bảo đảm nó trỏ đến file license hợp lệ.
- Không đưa file license hoặc thông tin bí mật vào Git.

### CPLEX MIP

- Bản hiện tại báo giới hạn Promotional Edition.
- Kiểm tra kích thước mô hình cho thấy giới hạn khoảng 1.000 biến và 1.000 ràng buộc.
- Chưa xác nhận bản Academic không giới hạn đã được cấp và kích hoạt.

### CPLEX CP

- Bản hiện tại báo giới hạn Community Edition.
- Thông báo của solver nêu giới hạn không gian tìm kiếm đến 2^1000.
- Chưa xác nhận bản Academic không giới hạn đã được cấp và kích hoạt.

### CP-SAT

- Các bài kiểm tra môi trường đã chạy thành công.
- Script `experiments/check_limits.py` chạy được mô hình thử nghiệm đến n = 10.000.
- Kết quả này chỉ phản ánh mô hình kiểm tra tổng hợp, không phải kết quả benchmark ABP.

## 5. Lưu ý cho thực nghiệm chính thức

- Máy chạy official experiments và cấu hình tài nguyên chưa được chốt.
- Máy hiện tại có 15.2 GB RAM; không mặc định áp dụng giới hạn 16 GB cho riêng một tiến trình trên máy này.
- Giới hạn bộ nhớ và cấu hình chạy chính thức sẽ được thống nhất cùng P3 trong `PROTOCOL.md`.
- Cần ghi lại mọi thay đổi về phiên bản solver, Python và môi trường trước khi chạy thực nghiệm chính thức.
