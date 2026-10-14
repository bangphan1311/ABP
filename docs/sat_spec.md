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

Theo `WORK BREAKDOWN.md` §5 và `Quang.md` §2.1, §3.3: duyệt K tăng dần từ cận dưới
(`K ← B + 1`), dừng ở lần UNSAT đầu tiên. Không dùng tìm kiếm nhị phân (các ngưỡng cao
là UNSAT khó nhất).

```
lo = 0            # B tốt nhất đã verify (0 = chưa có nghiệm)
hi = n            # ngưỡng đã biết UNSAT (đếm nhãn: lệch tối đa n - 1)
while lo + 1 < hi:
    K = lo + 1    # cận dưới: ngưỡng nhỏ nhất chưa bị bác
    giải bài toán quyết định tại K
    SAT     -> decode, verify, B = antibandwidth thực tế; lo = B  (K kế tiếp = B + 1)
    UNSAT   -> hi = K; B = K - 1 là tối ưu, dừng
    UNKNOWN (hết giờ) -> dừng, trả FEAS/TO
```

`K ← B + 1` (không phải `K ← K + 1`): model SAT tại `K` có thể đạt `B > K`, nên bước
nhảy tới `B + 1` không bỏ sót ngưỡng nào. Nếu `verify()` cho `B < K` thì model không
thỏa ràng buộc → `ERR` (mâu thuẫn encoding), không lặp vô hạn.

Mỗi ngưỡng dựng CNF mới và dùng backend mới; không dùng incremental/assumption ở W1.
`hi = n` ban đầu là UNSAT theo lập luận đếm nhãn (`metadata["unsat_source"] =
"counting:lệch nhãn tối đa n-1"`), các lần `hi` về sau là bằng chứng solver
(`"solver"`). Vì dừng ở UNSAT đầu tiên, `hi` chỉ nhận hai giá trị: `n` (chưa có lần dò
UNSAT nào, chỉ xảy ra khi hết giờ) hoặc `lo + 1` (đã chứng minh tối ưu → `OPT`).

Mỗi lần dò được ghi vào `Result.metadata["probes"]`:
`{"k", "status", "b", "t_encode", "t_solve", "variables", "clauses"}` (`b` = antibandwidth
thực tế của nghiệm, `None` khi không SAT).

## 6. Status, lb, ub, gap

| Tình huống | `status` | `lb` | `ub` | `gap` |
|---|---|---|---|---|
| `lo + 1 == hi` (đã chứng minh tối ưu) | `OPT` | `verify(solution)` | như `lb` | `0.0` |
| Hết giờ nhưng đã có nghiệm verify | `FEAS` | `verify(solution)` | `hi - 1` | `ub - lb` |
| Hết giờ, chưa có nghiệm nào | `TO` | `None` | `None` | `None` |
| Lỗi backend/khởi tạo (kể cả lỗi giấy phép) | `ERR` | `None` | `None` | `None` |
| Nghiệm mâu thuẫn bằng chứng UNSAT/OPT | `ERR` | `None` | `None` | `None` |

`lb` luôn là giá trị `verify()` tính lại từ labeling và đồ thị gốc, không phải `K`.
`hi` luôn là ngưỡng đã **chứng minh UNSAT** (đếm nhãn hoặc solver), nên cận trên hợp lệ là
`ub = hi - 1`; khi chưa có lần dò UNSAT nào thì `hi = n` và `ub = n - 1` (hệ quả của đếm nhãn).
Nghiệm chỉ được gán vào `Result.solution` khi status là `OPT` hoặc `FEAS`.

**Quy ước kích thước encoding (RQ1)**: `Result.variables`/`clauses` là kích thước CNF của
**lần dò cuối cùng có dựng CNF** (K cuối đã thử), **không** phải `K = 1` và không phải ngưỡng
tốt nhất. Ở `K = 1` không có mệnh đề khoảng cách (`distance = 0`), nên số của `K = 1` không đo
được đúng thứ RQ1 so sánh (pairwise và order khác nhau ở mệnh đề khoảng cách). Lần dò cuối là
nơi encoding thực sự làm việc: `OPT` → K = `hi` (ngưỡng vừa chứng minh UNSAT), `FEAS`/`TO` →
K lớn nhất đã thử. Quy ước này giữ số liệu kích thước có mặt **kể cả khi hết giờ**
(`FEAS`/`TO`). Nếu deadline hết trước khi dựng CNF (ví dụ `time_limit ≤ 0`) thì không lần dò
nào có CNF và hai trường là `None`.

`metadata["probes"]` giữ số liệu **từng** lần dò (`variables`, `clauses`, `t_encode`,
`t_solve`) nên vẫn phân tích được độ phức tạp encoding theo `K`;
`metadata["abp_encoding_stats"]` là phân bố clause theo nhóm ràng buộc của CNF tốt nhất (`lo`).
`peak_memory` chưa đo ở W1
(xem `docs/sat_tooling.md`).

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

`sat_solver="kissat"` **chưa được hỗ trợ** ở W1/W2: trả `ERR` với thông báo rõ, không crash.
Xem `docs/sat_tooling.md` mục 7.

**Phạm vi `time_limit`**: ngân sách cho **cả chuỗi K**, gồm encode CNF (`build_cnf`), nạp
clause (`add_clauses`) và giải (`solve`) của mọi lần dò. Deadline được kiểm tra trước mỗi
pha và phần thời gian còn lại được truyền vào solver. Pha đang chạy khi hết giờ vẫn hoàn
thành nên `t_total` có thể vượt `time_limit` một khoảng nhỏ (`grid(10,10)`, `time_limit=1.0`
→ `t_total ≈ 1.19 s`); xem `docs/sat_tooling.md` mục 4.

`memory_limit`, `search_mode`, `symmetry`, `warm_start`, `seed` **chưa được cài đặt** ở W1:
`memory_limit` để `None` nên status `MO` không bao giờ xuất hiện; bốn field còn lại thuộc P3.
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

## 9. Experimental setup — cách đo cho RQ1/RQ2

Quy ước số liệu cho phần thực nghiệm, để RQ1 và RQ2 đo đúng một đại lượng:

- **RQ1 (kích thước encoding)**: `Result.variables`/`clauses` là kích thước CNF của lần dò
  **cuối cùng** (mục 6) — tức K cuối đã thử, nơi có mệnh đề khoảng cách; per-K ở
  `metadata["probes"]`. Hai encoding (`pairwise`, `order`) phải so trên cùng một dãy K.
- **RQ2 (so solver)**: chỉ so **CaDiCaL và Glucose**, cùng cách đo `t_solve` (PySAT). Kissat
  đã bỏ khỏi phạm vi (`docs/sat_tooling.md` mục 7): đây là **hạn chế** của RQ2 và phải nêu
  trong bài viết. Không có cơ sở để so sánh thời gian với một solver không chạy được.
- **Ngân sách**: `time_limit` là ngân sách cho cả chuỗi K, gồm encode và mọi lần gọi solver
  (mục 5, mục 7).
- **Bộ nhớ**: `peak_memory = None` ở W1 (`docs/sat_tooling.md` mục 8).
