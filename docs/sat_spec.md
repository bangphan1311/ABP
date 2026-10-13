# Đặc tả SAT cho ABP (W1)

Owner: P2. Phạm vi: một encoding `pairwise`, một backend PySAT, một chiến lược tìm K.
Tham chiếu: `CONTRACT.md` (Result/Config/Instance/verify), `docs/sat_tooling.md` (tooling).

## 1. Bài toán quyết định

Cho `G = (V, E)`, `n = |V|`, ngưỡng `K`:

> Có tồn tại hoán vị `f: V → {1..n}` sao cho `|f(u) - f(v)| ≥ K` với mọi `(u, v) ∈ E`?

- `K = 1`: luôn SAT (nhãn là hoán vị nên hai đỉnh khác nhau luôn lệch ≥ 1).
- `K ≥ n`: luôn UNSAT (lệch nhãn lớn nhất có thể là `n - 1`).
- Đồ thị không có cạnh: ABP không xác định → `ValueError` (giống `solve_oracle`
  và `verify`).

## 2. Biến

`x[v][p] = 1` khi đỉnh `v` (0-based) nhận nhãn `p` (1..n).
`id(x[v][p]) = v * n + p`, tức `n²` biến chính `1..n²`.
Biến phụ (aux) của `pysat.card` được cấp phát từ `n² + 1` qua một `IDPool` dùng chung,
nên không đè lên vùng biến chính.

## 3. Bốn nhóm ràng buộc

| Nhóm | Nội dung | Số clause (encoding pairwise) |
|---|---|---|
| `assignment` | Mỗi đỉnh nhận đúng một nhãn: ALO + AMO trên `{x[v][1..n]}` | `n + n * C(n,2)` |
| `permutation` | Mỗi nhãn gán cho đúng một đỉnh: ALO + AMO trên `{x[0..n-1][p]}` | `n + n * C(n,2)` |
| `distance` | Với mọi cạnh `(u,v)` và mọi cặp `p ≠ q`, `|p - q| < K`: `¬x[u][p] ∨ ¬x[v][q]` | `|E| * 2 * Σ_{d=1..K-1} (n - d)` |
| `threshold` | Ngưỡng `K`; trường hợp `K ≥ n` chốt UNSAT không cần dựng CNF | 0 |

`AMO` là interface `amo(literals, encoding, pool)`:
`encoding="pairwise"` (mặc định, tự sinh `C(m,2)` clause) hoặc một tên encoding của
`pysat.card.EncType` (`seqcounter`, `cardnetwrk`, `totalizer`, ...). `native` bị từ chối
vì ràng buộc không nằm trong clause.

Ví dụ đếm tay — `path4` (n=4, 3 cạnh), `K=2`, AMO pairwise: 16 biến,
`assignment = 28`, `permutation = 28`, `distance = 3 * 2 * (4-1) = 18`,
tổng 74 clause (khớp `tests/sat/test_pairwise.py`).

## 4. SAT/UNSAT và decode

- SAT → `backend.get_model()` → `decode_model(cnf, model)`:
  đỉnh `v` nhận nhãn `p` duy nhất với `x[v][p]` dương. Model phải cho đúng một nhãn
  cho mỗi đỉnh và nhãn là hoán vị của `1..n`; nếu không → `ValueError` (lỗi encoding,
  không được bỏ qua).
- Nghiệm sau decode bắt buộc đi qua `verify(instance, labeling)`. Không có đường nào
  trả nghiệm mà không verify.

## 5. Chiến lược duyệt K

Tìm kiếm nhị phân trên `[1, n]` dùng tính đơn điệu (SAT tại `K` ⇒ SAT tại mọi `K' ≤ K`):

```
lo = 0            # ngưỡng lớn nhất đã có nghiệm verify được
hi = n            # ngưỡng đã biết UNSAT (chặn trên bằng đếm nhãn)
while lo + 1 < hi:
    mid = (lo + hi) // 2
    giải bài toán quyết định tại mid
    SAT   -> lo = mid, lưu nghiệm
    UNSAT -> hi = mid
    UNKNOWN (hết giờ) -> dừng
```

Mỗi ngưỡng dựng CNF mới và dùng backend mới; không dùng incremental/assumption ở W1.
`hi = n` ban đầu là UNSAT theo lập luận đếm nhãn (`metadata["unsat_source"] =
"counting:lệch nhãn tối đa n-1"`), các lần `hi` về sau là bằng chứng solver
(`"solver"`).

## 6. Status, lb, ub, gap

| Tình huống | `status` | `lb` | `ub` | `gap` |
|---|---|---|---|---|
| `lo + 1 == hi` (đã chứng minh tối ưu) | `OPT` | `verify(solution)` | như `lb` | `0.0` |
| Hết giờ nhưng đã có nghiệm verify | `FEAS` | `verify(solution)` | `hi` | `ub - lb` |
| Hết giờ, chưa có nghiệm nào | `TO` | `None` | `None` | `None` |
| Lỗi backend/khởi tạo (kể cả lỗi giấy phép) | `ERR` | `None` | `None` | `None` |
| Nghiệm mâu thuẫn bằng chứng UNSAT/OPT | `ERR` | `None` | `None` | `None` |

`lb` luôn là giá trị `verify()` tính lại từ labeling và đồ thị gốc, không phải `K`.
Nghiệm chỉ được gán vào `Result.solution` khi status là `OPT` hoặc `FEAS`.
`variables`/`clauses` là kích thước CNF của ngưỡng tốt nhất (`lo`), khi chưa có nghiệm
thì là `None`. `peak_memory` chưa đo ở W1 (xem `docs/sat_tooling.md`).

## 7. Interface

```python
from src.common.models import Config, Instance, Result

from src.sat.solve import solve_sat, solve_decision

result: Result = solve_sat(instance, Config(method="sat", time_limit=60.0))
status, labeling = solve_decision(instance, k=5, config=cfg)  # ("SAT"|"UNSAT"|"UNKNOWN", labeling|None)
```

`Config` dùng: `abp_encoding` (mặc định `"pairwise"`, W1 chỉ có encoding này),
`amo_encoding` (mặc định `"pairwise"`), `sat_solver` (mặc định `"cadical195"`),
`time_limit` (giây, `None` = không giới hạn). `method` chỉ mang tính nhãn ở W1.

**Phạm vi `time_limit`**: chỉ chặn phần giải của solver. Thời gian encode CNF và nạp
clause vào solver không tính vào deadline, nên `t_total` có thể vượt `time_limit` — đo
được tới ~20 lần khi `time_limit` nhỏ (`grid(8,8)`, `time_limit=0.05` → `t_total ≈ 1.09 s`).
W1 không cắt cứng theo giây; xem `docs/sat_tooling.md` mục 4.

`memory_limit`, `search_mode`, `symmetry`, `warm_start`, `seed` **chưa được cài đặt** ở W1:
`memory_limit` để `None` nên status `MO` không bao giờ xuất hiện; ba field còn lại thuộc P3.
Đặt chúng khác giá trị mặc định thì `solve_sat`/`solve_decision` phát `UserWarning` một lần
(không bỏ qua im lặng).

## 8. Format instance (loader)

JSON, một file một instance:

```json
{
  "id": "path4",
  "name": "Path graph with 4 vertices",
  "n": 4,
  "edges": [[0, 1], [1, 2], [2, 3]],
  "source": "generator",
  "tier": "toy"
}
```

`read_instance` kiểm tra: đủ 6 trường, `n` là số nguyên ≥ 0, mỗi cạnh là cặp số nguyên
trong `0..n-1` và không tự khuyên. Trường lạ bị bỏ qua. `write_instance` ghi đúng schema
này; `read_instance(write_instance(x)) == x` (roundtrip, xem `tests/sat/test_io.py`).
