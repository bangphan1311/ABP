# Đặc tả SAT cho ABP (W1)

Owner: P2. Phạm vi: một encoding `pairwise`, một backend PySAT, một chiến lược tìm K.
Tham chiếu: `CONTRACT.md` (Instance/Config/Result/verify), `docs/sat_tooling.md` (tooling).

## 1. Bài toán quyết định

Cho `G = (V, E)` đồ thị đơn, vô hướng, `n = |V|`, và ngưỡng `K`:

> Hỏi có tồn tại song ánh `f: V → {1, …, n}` sao cho `|f(u) − f(v)| ≥ K` với mọi cạnh `{u, v} ∈ E`?

Đồ thị đơn, vô hướng nên mỗi cạnh là cặp không thứ tự `{u, v}` với `u ≠ v`; điều kiện không phụ thuộc thứ tự `u, v`. Loader loại cạnh trùng ngay lúc đọc: `{u, v}` lặp hoặc `{v, u}` chỉ tính một cạnh; `m = |E|` đếm số cạnh `{u, v}` duy nhất (xem `src/sat/loader.py`).

Trường hợp biên:

- `K` phải là `int` (không phải `bool`) và `K ≥ 1`. Sai kiểu — `bool` (kể cả `True`/`False`) hoặc không nguyên (vd `2.5`) — → `TypeError`; `K` nguyên nhưng `K < 1` → `ValueError`. `K = 1`: luôn SAT (hai đỉnh kề nhau có nhãn khác nhau nên lệch ≥ 1).
- Kiểm tra đầu vào chạy trước mọi thứ: `|E| = 0` hoặc `n = 0` → `ValueError` trước `trivial_unsat`, nên đồ thị rỗng không bao giờ trả UNSAT. Về mặt toán học điều kiện trống là SAT, nhưng ABP không xác định — đây là kiểm tra đầu vào, không phải đáp án toán học.
- Sau kiểm tra đầu vào: `K ≥ n` (với `|E| ≥ 1`): UNSAT, vì lệch nhãn lớn nhất chỉ là `n − 1`. Chốt UNSAT trước khi dựng CNF (`trivial_unsat` trong `src/sat/pairwise.py`, được kiểm tra trước `build_cnf` trong `src/sat/solve.py`); `build_cnf` không tự từ chối `K ≥ n`.
- Đỉnh cô lập: vẫn nhận một nhãn, không có clause khoảng cách. Đồ thị không liên thông: không xử lý riêng, `f` là song ánh toàn cục.
- Cạnh tự khuyên `(u, u)`: bị từ chối bằng `ValueError` ở bước kiểm tra đầu vào, cả khi đọc qua loader (`src/sat/loader.py`) lẫn với `Instance` dựng tay trong bộ nhớ qua `_validate_instance` (`src/sat/solve.py`).

## 2. Biến SAT

- `x[v][p] = 1` khi đỉnh `v` (0-based) nhận nhãn `p` (`p ∈ {1..n}`). Ý nghĩa: "gán đỉnh `v` nhãn `p`".
- Mã số: `id(x[v][p]) = v * n + p` → `n²` biến chính với id từ `1` đến `n²`.
- Biến phụ (aux): chỉ xuất hiện khi `amo_encoding ≠ pairwise`; cấp phát từ `n² + 1` qua một `IDPool` dùng chung cho mọi AMO trong một CNF, không đè vùng biến chính.

### 2.2. Encoding `order`

- `o[v][p] = 1` khi nhãn của đỉnh `v` **≤ p** với `p ∈ 1..n−1`; biên `p = 0` luôn sai và `p = n` luôn đúng nên không cần biến (`src/sat/order.py`).
- Mã số: `id(o[v][p]) = v * (n - 1) + p` → `n(n−1)` biến chính, id từ `1` đến `n(n−1)`.
- Nhãn `f(v) = min{p : o[v][p] = 1}`, hoặc `n` khi cả chuỗi bằng 0 — mỗi cách gán chuỗi đơn điệu cho đúng một nhãn.

## 3. Ràng buộc

Đặt `m = |E|`. Bảng số clause cho AMO `pairwise` (mặc định):

| Nhóm | Điều kiện | Số clause |
|---|---|---|
| `assignment` | mỗi đỉnh nhận đúng một nhãn | `n + n · C(n,2)` |
| `permutation` | mỗi nhãn gán cho đúng một đỉnh | `n + n · C(n,2)` |
| `distance` | với mỗi cạnh `{u,v}` và mỗi cặp `(p,q)` với `1 ≤ |p−q| ≤ K−1`: `¬x[u][p] ∨ ¬x[v][q]` | `m · 2 · Σ_{d=1..K−1} max(0, n − d)` |
| `threshold` | ngưỡng `K`; `K ≥ n` chốt UNSAT, không dựng CNF | 0 |

- `assignment`: một clause ALO `(x[v][1] ∨ … ∨ x[v][n])` mỗi đỉnh `v`, cộng AMO `(¬x[v][p] ∨ ¬x[v][q])` với `p < q`, tức `C(n,2)` clause mỗi đỉnh.
- `permutation`: một clause ALO `(x[0][p] ∨ … ∨ x[n−1][p])` mỗi nhãn `p`, cộng AMO `(¬x[u][p] ∨ ¬x[w][p])` với `u < w`.
- `assignment` + `permutation` cùng nhau buộc `f` là song ánh: mỗi đỉnh một nhãn, mỗi nhãn một đỉnh.
- `distance`: mỗi cạnh có đúng `2 · Σ_{d=1..K−1} max(0, n − d)` clause (mỗi cặp `(p,q)` được duyệt theo cả hai thứ tự). Dạng tổng quát này đúng mọi `K ≥ 1`: với `K ≤ n` rút gọn thành `2 · Σ_{d=1..K−1} (n − d)`; gọi `build_cnf` trực tiếp với `K ≥ n` thì tổng chặn tại `d = n − 1` (mỗi nhãn chỉ cấm đúng `n − 1` nhãn còn lại), không bao giờ âm. Qua pipeline chỉ có `K ≤ n − 1` tới `build_cnf`, vì `K ≥ n` bị chặn ở `trivial_unsat`; tại `K = 1` tổng rỗng → 0 clause.
- `threshold` không sinh clause.

Ví dụ đếm tay `path4` (`n = 4`, `m = 3`), khớp `tests/sat/test_pairwise.py`:

| | K = 1 | K = 2 | K = 3 |
|---|---|---|---|
| biến | 16 | 16 | 16 |
| assignment | 28 | 28 | 28 |
| permutation | 28 | 28 | 28 |
| distance | 0 | 18 | 30 |
| tổng clause | 56 | 74 | 86 |

Tính tay: `assignment = 4 + 4·C(4,2) = 28`; `K = 2`: `distance = 3·2·(4−1) = 18`; `K = 3`: `distance = 3·2·((4−1)+(4−2)) = 30`.

Ghi chú AMO: mặc định `amo_encoding = "pairwise"`, tức `C(m,2)` clause cho `m` literal, không thêm biến. Các encoding từ `pysat.card` (`seqcounter`, `cardnetwrk`, `totalizer`, `mtotalizer`, `kmtotalizer`, `bitwise`, `ladder`, `sortnetwrk`) cho số clause khác và có thể thêm biến phụ; bảng trên chỉ đúng cho `pairwise`, phần ALO không đổi. `native` (ràng buộc native cần CNFPlus) và tên lạ đều `ValueError`.

### 3.2. Encoding `order`

`order` không có nhóm AMO: chuỗi đơn điệu thay ALO + AMO nên `amo_encoding` chỉ là metadata, không đổi clause (`src/sat/order.py`). Đặt `m = |E|`:

| Nhóm | Điều kiện | Số clause |
|---|---|---|
| `assignment` | chuỗi đơn điệu `o[v][p] → o[v][p+1]`, `p ∈ 1..n−2`, mỗi đỉnh | `n(n−2)` |
| `permutation` | mỗi cặp đỉnh `u < w`, mỗi nhãn `q`: `f(u) ≠ q ∨ f(w) ≠ q` | `n · C(n,2)` |
| `distance` | như `pairwise` trên mỗi cạnh, no-good trên nhãn | `m · 2 · Σ_{d=1..K−1} max(0, n − d)` |
| `threshold` | `K ≥ n` chốt UNSAT trước khi dựng CNF | 0 |

Ví dụ `path4` (`n = 4`, `m = 3`, `order`): K = 1: `8 + 24 + 0 = 32` clause; K = 2: `8 + 24 + 18 = 50`; K = 3: `8 + 24 + 30 = 62`.

## 4. SAT / UNSAT và decode

- SAT: solver trả model. `decode_model` (`src/sat/pairwise.py`) quét các `x[v][p]` dương: mỗi đỉnh phải có đúng một nhãn và tập nhãn phải là hoán vị của `1..n`; vi phạm → `ValueError` (lỗi encoding, không được bỏ qua). Model chưa phải nghiệm: nghiệm bắt buộc đi qua `verify(instance, labeling)` (CONTRACT §6). Verify tính lại giá trị mục tiêu từ labeling và đồ thị gốc. `solve_sat` luôn `verify` trước khi đưa nghiệm vào `Result`; `solve_decision` trả labeling từ `_probe` **không** qua `verify`. Caller phải tự gọi `verify`.
- UNSAT: solver chứng minh không có model → không tồn tại labeling thỏa ngưỡng `K`. UNSAT của solver là bằng chứng cho ngưỡng `K` đó (`K ≥ n`: UNSAT theo đếm từ `trivial_unsat`, không qua solver).
- UNKNOWN (hết giờ giữa chừng): không dùng làm bằng chứng theo cả hai chiều.

## 5. Chiến lược duyệt K

Duyệt `K` **tăng dần** từ cận dưới, dừng ở lần UNSAT đầu tiên:

```
lo = 0   # B tốt nhất đã verify (0 = chưa có nghiệm)
hi = n   # UNSAT theo đếm nhãn (lệch nhãn tối đa n − 1)
lặp khi lo + 1 < hi:
  K = lo + 1                       # cận dưới: ngưỡng nhỏ nhất chưa bị bác bỏ
  giải bài toán quyết định tại K
  SAT   → decode → verify → B = antibandwidth thực tế; lo = B; K kế tiếp = B + 1
  UNSAT → hi = K; B = K − 1 là tối ưu; dừng
  UNKNOWN (hết giờ) → dừng
```

- Cận dưới khởi đầu: `K = 1` (tầm thường). Heuristic tốt hơn chỉ đổi điểm khởi đầu, không đổi quy tắc dừng.
- `K ← B + 1`, không phải `K + 1`: model SAT tại `K` có thể đạt `B > K`; vì nghiệm `B` thỏa mọi ngưỡng `≤ B`, nhảy tới `B + 1` không bỏ sót ngưỡng nào.
- UNSAT đầu tiên → `B = K − 1` tối ưu; dừng.
- ERR (lỗi encoding, không phải UNSAT/OPT): model SAT tại `K` không đạt ngưỡng khi `verify`; nghiệm `OPT`/`FEAS` mâu thuẫn bằng chứng dò (giá trị khác ngưỡng đã chứng minh); hoặc không có nghiệm verify được dù chưa hết giờ. Ba trường hợp này `solve_sat` trả `ERR`.
- Không mượn hướng tìm kiếm của 2DBMP: không duyệt `K` từ trên xuống, không tìm kiếm nhị phân. Lý do: duyệt tăng dần đảm bảo lần dò UNSAT đầu tiên đồng thời chứng minh tối ưu, và mọi lần dò SAT trước đó đều cho nghiệm đã verify (giả thuyết chưa đo: các ngưỡng cao là UNSAT khó nhất).
- `solve_sat` nhận tham số `ub` ngoài tùy chọn do P2 tính. Không truyền `ub`: solver tự tính mặc định `ub = hi − 1` từ lần UNSAT đầu tiên (`summarise_result`, `src/sat/solve.py`); cận trên tầm thường của bài toán là `n − 1`, sau lần UNSAT đầu tiên `ub = B` tối ưu. `ub` ngoài không hợp lệ (vd: `ub` nhỏ hơn `B` đã verify SAT) → `ValueError`.
- Mỗi ngưỡng dựng CNF mới và dùng backend mới; không dùng incremental/assumption ở W1.

### 5.1. Canonical config và memory contract

`CANONICAL_SAT_CONFIG` (`src/sat/solve.py`) khóa `method="sat"`, `abp_encoding="order"`, `amo_encoding="pairwise"`, `sat_solver="glucose4"`, `search_mode="multi"`, `symmetry=False`, `warm_start=False`, `seed=0` (M2 freeze v1.0, `docs/w4-sat/21-m2-freeze-v1.md`).

`canonical_sat_config()` mặc định `memory_limit=12.0` GiB và từ chối `memory_limit=None`/giá trị không hợp lệ bằng `ValueError` nhắc `memory_limit` cho run official. Solver không enforce cap trong process; `MO` chỉ đến từ ánh xạ `MemoryError` ngoài process (`src/runner/worker.py`), cap official do runner áp (Protocol §6.3). `search_mode="multi"` là mode duy nhất đã cài đặt nên không phát warning giả; `symmetry`/`warm_start` khác mặc định vẫn warning.
