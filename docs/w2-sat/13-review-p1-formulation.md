# Review P1 — Formulation exact MIP/CP cho ABP (ticket 13, GitHub issue #20)

- **Người review:** P2 (Quang)
- **Ngày:** 2026-10-20
- **Đối tượng review:** branch `origin/p1/w2-exact-solvers` (chưa merge vào main):
  `docs/exact_models.md`, `src/exact/gurobi_mip.py`, `src/exact/cplex_mip.py`,
  `src/exact/cplex_cp.py`, `src/exact/cp_sat_solver.py` (không đổi so main —
  `git diff main origin/p1/w2-exact-solvers -- src/exact/cp_sat_solver.py` rỗng),
  `tests/exact/test_exact_solvers.py`, `tests/exact/test_solver_status.py`,
  `src/runner/registry.py` (đăng ký 3 method mới).
- **Chuẩn so sánh:** `CONTRACT.md`, `docs/sat_spec.md`, `src/sat/pairwise.py`,
  `src/sat/solve.py`, `src/common/verify.py`, `src/exact/oracle.py`.

## Kết luận tổng quát

**Đồng ý formulation — không có sai sai sót về tính đúng đắn.** Cả ba model mới
(Gurobi MIP, CPLEX MIP, CPLEX CP) cùng CP-SAT cũ giải đúng ABP: cùng tối ưu
`K = min |f(u) − f(v)|` trên cạnh, cùng bài toán với SAT encoding, nghiệm bắt buộc
qua `verify()` dùng chung, quy ước status đúng CONTRACT §5. Kiểm chứng thực nghiệm
9/9 toy instance khớp oracle và khớp SAT. Các yêu cầu gửi P1 bên dưới thuộc mức
test/doc/đồng bộ quy ước, không chặn formulation.

## 1. Checklist ticket 13

### 1.1 MIP: biến nhị phân theo cặp/cạnh, không dùng big-M yếu — **đồng ý**

Cả Gurobi MIP và CPLEX MIP dùng:

- Biến nguyên `x_v ∈ [1, n]`, biến mục tiêu `K ∈ [1, n-1]` — đúng miền K.
- **Mỗi cặp đỉnh `i < j`** (không chỉ cạnh): một binary `z` chọn
  `x_i + 1 ≤ x_j` hoặc `x_j + 1 ≤ x_i` → nhãn khác nhau cho **mọi** cặp đỉnh
  (tổng cộng `C(n,2)` binary). Kiểm tra trong code: Gurobi vòng lặp
  `for i in range(n): for j in range(i+1, n)`; CPLEX dựng `pairs` tương tự.
  Đây chính là "permutation" của SAT (assignment + permutation) dưới dạng thứ tự.
- **Mỗi cạnh** `(u, v)`: một binary `y` chọn `x_u − x_v ≥ K` hoặc `x_v − x_u ≥ K`
  → đúng `|x_u − x_v| ≥ K` chỉ áp trên cạnh, không áp trên cặp không kề.
- Ràng buộc implication viết bằng **indicator constraints** (Gurobi `(z==1) >>`,
  CPLEX `indicator_constraints.add`) — **không có big-M chọn tay**; solver tự suy
  hằng số từ biên biến `[1, n]` (chặt vì biên chặt). Thỏa tinh thần "không dùng
  big-M yếu" của ticket.

Kiểm chứng thực nghiệm (venv máy này có gurobipy restricted license + CPLEX
community; script review chạy ngoài repo): Gurobi MIP và CPLEX MIP trả
`OPT, lb = ub = oracle.lb` trên cả 9 instance: path4, cycle5, complete5, path8,
grid2x4, complete6, star K1,5, đồ thị 2 thành phần + 2 đỉnh cô lập, random7.
Không đếm được trường hợp nào sai.

Chi tiết CPLEX MIP đã soi riêng: indexing biến (`k_idx = n`, `pair_start = n+1`,
`edge_start`) đúng; `types/lb/ub/obj` đúng; hai indicator mỗi binary đủ và không
mâu thuẫn. `MIP.get_best_objective()` — kiểm chứng bằng thực nghiệm trả về
**cận đối ngẫu** (grid3x4 tắt vì hết giờ: incumbent K=4, bound 9.92), nên
`ub = min(n−1, max(lb, ceil(bound)))` là cận trên hợp lệ (đo được incumbent=4,
ub=10 ≥ optimum). Không phải bug như nghi ngờ ban đầu khi đọc tên hàm.

### 1.2 CP model cùng semantic với SAT và MIP — **đồng ý, kèm 1 ghi chú nhỏ**

- **CP-SAT** (file main, P1 không đổi): `x_v ∈ [1,n]`, `add_all_different`,
  `k ≤ |x_u − x_v|` mỗi cạnh qua `add_abs_equality`, `maximize(k)`. Semantic
  giống hệt MIP và giống bài toán quyết định của SAT (all-diff trên n biến miền
  1..n ⇔ song ánh). Ghi chú nhỏ: `k` có miền `[0, n−1]` trong khi doc + 3 solver
  mới dùng `[1, n−1]`. Vô hại (đồ thị có cạnh thì tối ưu ≥ 1), chỉ lệch quy ước.
- **CPLEX CP** (docplex): `all_diff(x)`, `abs(x_u − x_v) ≥ K` mỗi cạnh,
  `maximize K`, `K ∈ [1, n−1]` — đúng spec trong `docs/exact_models.md`.
  **Lưu ý:** máy review không có binary `cpoptimizer.exe` (chỉ có package
  `docplex`), nên không chạy thực nghiệm được solver này; code được review tĩnh.
  Solved returned `ERR` đúng quy ước khi engine thiếu — hành vi đúng, nhưng xem
  yêu cầu R2 về test.

### 1.3 Độ công bằng so với SAT encoding — **đồng ý về bản chất, có 3 điểm cần chốt bằng văn bản trước khi benchmark**

**Đúng/công bằng:**

- Cùng bài toán, cùng mục tiêu: SAT duyệt K tăng dần đến UNSAT đầu tiên
  (`solve_sat`), exact tối ưu trực tiếp `K`. Thực nghiệm: 9/9 instance SAT và
  cả 3 solver chạy được đều ra **cùng optimum**.
- Cùng cổng kiểm chứng: cả 4 solver exact gọi `src.common.verify.verify()`
  trước khi trả nghiệm (CONTRACT §6); runner của P3 còn verify lại độc lập.
  CP-SAT còn chênh `ERR` khi objective solver ≠ objective verify.
- Quy ước status theo CONTRACT §5: OPT chỉ khi solver chứng minh tối ưu
  (Gurobi `OPTIMAL`, CPLEX `optimal/MIP_optimal` — `MIP_optimal_tolerance`
  chủ động bị loại, an toàn phía không khẳng định quá); FEAS = incumbent đã
  verify chưa chứng minh; TO = hết giờ không có incumbent đã verify; MO có marker
  memory riêng; **license lỗi → ERR không phải TO** (đúng yêu cầu đặc biệt của
  CONTRACT §5 — ImportError/RuntimeError rơi vào `except Exception` → ERR).
- MIPGap = 0 (Gurobi `MIPGap=0`, CPLEX mipgap + absmipgap = 0) — không "ăn" gap
  tolerances khi khẳng định OPT, công bằng so với UNSAT-proof của SAT.
- 1 thread mọi solver (Gurobi Threads=1, CPLEX threads=1, CP-SAT workers=1,
  CP Optimizer Workers=1), seed đặt cho Gurobi/CPLEX/CP-SAT — cùng chế độ
  deterministic như CaDiCaL của SAT.

**Cần chốt/khắc phục (xem danh sách yêu cầu R1–R6):**

1. **Phạm vi `t_total` lệch nhau:** exact `t_total` gồm import backend bên trong
   hàm solve (đo thực tế: lần gọi đầu gurobipy ≈ 0.41s, cplex ≈ 0.45s; runner
   spawn subprocess mỗi run nên **mọi** run đều trả chi phí này), còn SAT import
   pysat ở module-level nên `t_total` không gồm import. P1 đã khai báo trong
   `docs/exact_models.md` và chỉ rõ runner wall-clock là thước end-to-end —
   **yêu cầu: mọi bảng so sánh chính thức W2 dùng runner `wall_time`, không dùng
   `t_total` để so SAT vs exact.**
2. **`Config.time_limit` nghĩa khác nhau:** SAT: ngân sách cho **cả chuỗi K**
   (encode + nạp clause + solve mọi lần dò); exact: chỉ giới hạn pha solve của
   solver (dựng model không trừ vào). Runner bù bằng kill cứng
   `time_limit + 30s` cho mọi method nên so sánh wall-clock vẫn công bằng, nhưng
   cần 1 đoạn doc nêu rõ (hiện `exact_models.md` chưa viết).
3. **`ub` khi TO không thống nhất trong exact family:** Gurobi/CPLEX MIP trả
   `ub = n−1` (cận tổng quát an toàn); CP-SAT trả `ub = 0` — sai về toán học
   (complete6 optimum = 1 > 0; ortools `best_objective_bound = 0.0` khi UNKNOWN),
   vì `max(0, ceil(best_bound))` với bound = 0. Đây là **bug có sẵn của main**
   (P1 không gây ra, file không đổi trên branch P1), sẽ làm bẩn thống kê
   gap/cận nếu benchmark dùng ub. Xem R5.

Ngoài ra các điểm nhỏ về tính công bằng (không chặn): exact bỏ qua im lặng
`symmetry/warm_start/search_mode/memory_limit` trong khi SAT phát 1 warning;
`variables` mỗi backend đếm khác nhau (CP-SAT đếm cả biến aux abs, Gurobi/CPLEX
đếm đủ n+1+C(n,2)+m, CPLEX CP chỉ n+1) — không so trực tiếp được giữa các
paradigm, chỉ dùng nội bộ từng backend; `clauses=None` với exact là hợp lý.

### 1.4 Test của P1 — **đồng ý nội dung, yêu cầu sửa skip-guard**

`tests/exact/test_exact_solvers.py`: so 4 solver với oracle trên path4, cycle5,
complete5, assert OPT + `lb == ub == oracle.lb` + verify lại — đúng và đủ cho
smoke correctness. `tests/exact/test_solver_status.py`: chốt `_is_proven_optimal`
loại `MIP_optimal_tolerance`, map status CP Optimizer đủ 6 nhánh — tốt.

Nhưng: **không có skip-guard khi backend/engine/license vắng.** Trên chính máy
dev này, `cpoptimizer.exe` không tồn tại → test CPLEX CP fail đỏ (solver trả
ERR, test assert OPT). Trên máy không có gurobipy/cplex, 3 test fail tương tự.
`pytest tests -q` phải xanh theo ràng buộc W2. Xem R1.

## 2. Yêu cầu gửi P1

| # | Yêu cầu | Lý do | Mức độ |
|---|---|---|---|
| R1 | `tests/exact/test_exact_solvers.py`: skip (không fail) khi backend vắng — `pytest.importorskip("gurobipy"/"cplex"/"docplex")` và với CPLEX CP kiểm tra engine (ví dụ `shutil.which("cpoptimizer")` hoặc chạy 1 solve thử path4 rồi skip nếu ERR "executable file is not found") | `pytest tests -q` phải xanh trên máy thiếu license/engine; hiện fail đỏ | Nên làm trước merge W2 |
| R2 | `docs/exact_models.md`: thêm 1 đoạn về semantics `Config.time_limit` của exact (chỉ giới hạn pha solve, không gồm dựng model) khác SAT (ngân sách cả chuỗi dò), và khẳng định so sánh chính thức dùng runner `wall_time` + kill cứng `time_limit + 30s` của runner | Công bằng đo lường; tránh so `t_total`/`time_limit` giữa hai family khi hiểu khác nhau | Trước benchmark chính thức |
| R3 | Đồng bộ input không hợp lệ: 3 solver mới trả `Result(status="ERR")` cho đồ thị rỗng/self-loop/`time_limit=0`, trong khi `solve_cp_sat` và `solve_sat` raise `ValueError`. Chọn 1 quy ước (đề xuất: validation lỗi raise như SAT, vì là lỗi caller; hoặc thống nhất ERR và ghi vào doc) | Cùng một input, 2 hành vi khác nhau trong exact family lẫn so với SAT | Nên thống nhất |
| R4 | Thêm warning ignored-Config như `_warn_ignored_config` của SAT cho `symmetry/warm_start/search_mode/memory_limit` trong 3 solver mới | SAT warning, exact im lặng — caller không biết field bị bỏ qua | Nice-to-have |
| R5 | Sửa `ub` khi TO trong `src/exact/cp_sat_solver.py`: khi không có incumbent đã verify, trả `ub = n−1` (hoặc None) thay vì `max(0, ceil(best_bound))` — ortools trả bound 0.0 khi UNKNOWN nên hiện `ub=0 < optimum` là cận sai | Cận trên sai sẽ bẩn RQ về gap/cận; bug có sẵn từ main, P1 là owner exact family — quyết định fix trên branch nào do team | Nên fix trước benchmark |
| R6 | (Optional) Gurobi/CPLEX MIP/CP: thêm cross-check `model_objective == objective_verified` → ERR như CP-SAT đang làm (hiện chỉ lưu cả hai vào metadata) | Phòng lệch dung sai số học khi round nghiệm; thống nhất 4 backend | Nice-to-have |

Ghi chú nhỏ kèm R1: Gurobi restricted license trên máy dev đủ cho toy n≤16
(đã chạy tốt). CPLEX CP cần P1 ghi rõ trong doc/handoff là đã validate ở đâu,
vì máy dev hiện thiếu `cpoptimizer.exe` (review chỉ review tĩnh được code
CP Optimizer).

## 3. Bằng chứng thực nghiệm (máy dev, venv W2, ngoài repo)

- 9 instance (path4, cycle5, complete5, path8, grid2x4, complete6, star6, 2-thành
  phần + đỉnh cô lập, random7): CP-SAT, Gurobi MIP, CPLEX MIP đều `OPT` và
  `lb = ub = oracle.lb`, verify nghiệm khớp; `solve_sat` cũng OPT cùng giá trị.
- CPLEX CP: ERR "Solver executable file is not found" (thiếu engine binary) —
  phân loại ERR đúng quy ước backend thiếu.
- Edge case: đồ thị không cạnh / self-loop → cả 3 solver mới ERR (hoặc raise với
  CP-SAT, xem R3); `time_limit=0` → ERR với exact mới, TO với SAT, raise với
  CP-SAT; time limit rất nhỏ trên complete6 → TO/FEAS đều nhất quán, không có
  OPT giả, `lb == verify()` mọi nghiệm trả về.

Kết thúc review. Formulation được duyệt; R1–R3 và R5 cần xử lý trước khi W2
chạy benchmark so sánh SAT vs exact.
