# 14 — Nháp SAT methodology (paper §3)

Ticket 14 (GH #21) · Ngày: 2026-10-20 · Branch `p2/w2-sat` · Owner: P2 (Quang).

Bản nháp nội bộ của §3 "SAT methodology" cho paper. Quy ước biên soạn:

- Mọi khẳng định kỹ thuật trace được về `CONTRACT.md`, `docs/sat_spec.md`,
  `docs/sat_tooling.md`, `src/sat/*.py` hoặc kết quả test trong
  `docs/handoff/w2-sat/12-test-matrix.md`. Bảng trace § → nguồn ở cuối file.
- **Không sao chép chứng minh của 2DBMP** (yêu cầu ticket 14): toàn bộ §3 viết
  từ đặc tả và code của repo này; khi nói về lựa chọn thiết kế thì chỉ nêu
  quyết định của repo, không trích dẫn hay tái lập chứng minh bên ngoài.
- Không tạo số đo mới: mọi số dưới đây là (i) số đã ghi trong
  `12-test-matrix.md` từ lần chạy thật 2026-10-20, (ii) hằng số code, hoặc
  (iii) clause count được test assert trực tiếp.

## §3.1 Bài toán quyết định

Cho đồ thị đơn, vô hướng `G = (V, E)`, `n = |V|`, `m = |E|`. Bài toán
antibandwidth (ABP) tìm hoán vị `f: V → {1, …, n}` cực đại hóa
(CONTRACT.md §1):

```
ab(f) = min { |f(u) − f(v)| : {u, v} ∈ E }
```

Bài toán quyết định với ngưỡng `K` (CONTRACT.md §1, `docs/sat_spec.md` §1):

> Tồn tại song ánh `f: V → {1, …, n}` sao cho `|f(u) − f(v)| ≥ K` với mọi
> cạnh `{u, v} ∈ E`?

Bài toán tối ưu được giải bằng dãy bài toán quyết định (§3.5). Quy ước đầu vào
(`docs/sat_spec.md` §1, `src/sat/pairwise.py`, `src/sat/solve.py`):

- Đồ thị đơn, vô hướng: mỗi cạnh là cặp không thứ tự `{u, v}`, `u ≠ v`; điều
  kiện không phụ thuộc thứ tự. Loader loại cạnh trùng khi đọc (`{u, v}` lặp
  hoặc `{v, u}` tính một cạnh), `m` đếm cạnh duy nhất (`src/sat/loader.py`).
- `K` phải là `int` (không phải `bool`) và `K ≥ 1`: sai kiểu → `TypeError`,
  `K < 1` → `ValueError`. `K = 1` luôn SAT khi đồ thị có cạnh.
- `n = 0` hoặc `|E| = 0` → `ValueError` trước mọi thứ: ABP không xác định trên
  đồ thị rỗng; đây là kiểm tra đầu vào, không phải đáp án toán học, nên đồ thị
  rỗng không bao giờ trả UNSAT.
- Cạnh tự khuyên `(u, u)` bị từ chối `ValueError` (loader và
  `_validate_instance` trong `src/sat/solve.py`).
- `K ≥ n` (với `|E| ≥ 1`): UNSAT theo đếm — lệch nhãn lớn nhất chỉ là `n − 1`.
  Chốt UNSAT trước khi dựng CNF (`trivial_unsat`, `src/sat/pairwise.py`,
  được `_probe` kiểm trước `build_cnf`); nhóm ràng buộc `threshold` không sinh
  clause.
- Đỉnh cô lập vẫn nhận một nhãn, không có clause khoảng cách; đồ thị không liên
  thông không xử lý riêng — `f` là song ánh toàn cục.

## §3.2 Biến SAT

Hai encoding cùng giải một bài toán quyết định nên dùng chung pipeline
(`src/sat/solve.py::_probe` chọn build/decode theo `abp_encoding`).

### §3.2.1 Pairwise (`src/sat/pairwise.py`)

- `x[v][p] = 1` khi đỉnh `v` (0-based) nhận nhãn `p ∈ {1..n}`.
- Mã số: `id(x[v][p]) = v * n + p` → `n²` biến chính, id từ `1` đến `n²`.
- Biến phụ: chỉ xuất hiện khi `amo_encoding ≠ "pairwise"`; cấp phát từ `n² + 1`
  qua một `IDPool` dùng chung cho mọi AMO trong một CNF, không đè vùng biến
  chính (`build_cnf` gọi `new_id_pool(start_from=n*n+1)`).

### §3.2.2 Order (`src/sat/order.py`)

- `o[v][p] = 1` khi nhãn của `v` **≤ p**, với `p ∈ 1..n−1`;
  `id(o[v][p]) = v * (n − 1) + p` → `n(n−1)` biến.
- Hai biên không cần biến: `p = 0` luôn sai, `p = n` luôn đúng.
- Nhãn `f(v) = min{p : o[v][p] = 1}`, hoặc `n` khi cả chuỗi bằng 0 — mỗi cách
  gán chuỗi đơn điệu cho đúng một nhãn.

## §3.3 Ràng buộc

Cả hai encoding có cùng bốn nhóm: `assignment`, `permutation`, `distance`,
`threshold` (docstring hai file encoding).

### §3.3.1 Pairwise — bảng số clause (AMO `pairwise` mặc định, `docs/sat_spec.md` §3)

| Nhóm | Điều kiện | Số clause |
|---|---|---|
| `assignment` | mỗi đỉnh nhận đúng một nhãn | `n + n · C(n,2)` |
| `permutation` | mỗi nhãn gán cho đúng một đỉnh | `n + n · C(n,2)` |
| `distance` | mỗi cạnh `{u,v}`, mỗi cặp `(p,q)` với `1 ≤ |p−q| ≤ K−1`: `¬x[u][p] ∨ ¬x[v][q]` | `m · 2 · Σ_{d=1..K−1} max(0, n − d)` |
| `threshold` | `K ≥ n` chốt UNSAT trước khi dựng CNF | 0 |

- `assignment` = một clause ALO `(x[v][1] ∨ … ∨ x[v][n])` mỗi đỉnh, cộng AMO
  `(¬x[v][p] ∨ ¬x[v][q])`, `p < q`, tức `C(n,2)` clause mỗi đỉnh.
- `permutation` = ALO mỗi nhãn trên mọi đỉnh, cộng AMO `(¬x[u][p] ∨ ¬x[w][p])`,
  `u < w`.
- Cùng nhau, `assignment` + `permutation` buộc `f` là song ánh.
- `distance`: mỗi cặp `(p,q)` được duyệt theo cả hai thứ tự; tại `K = 1` tổng
  rỗng → 0 clause; qua pipeline chỉ có `K ≤ n − 1` tới `build_cnf`.

Ví dụ `path4` (`n = 4`, `m = 3`), khớp assert trong `tests/sat/test_pairwise.py`
và bảng trong `docs/sat_spec.md` §3:

| | K = 1 | K = 2 | K = 3 |
|---|---|---|---|
| biến | 16 | 16 | 16 |
| assignment | 28 | 28 | 28 |
| permutation | 28 | 28 | 28 |
| distance | 0 | 18 | 30 |
| tổng clause | 56 | 74 | 86 |

### §3.3.2 Order (`src/sat/order.py`)

| Nhóm | Cấu trúc (đọc trực tiếp từ vòng lặp trong code) | Số clause |
|---|---|---|
| `assignment` | chuỗi suy luận đơn điệu `o[v][p] → o[v][p+1]` với `p ∈ 1..n−2`, mỗi đỉnh | `n(n−2)` |
| `permutation` | với mỗi cặp đỉnh `u < w` và mỗi nhãn `q ∈ 1..n`: `f(u) ≠ q ∨ f(w) ≠ q` | `n · C(n,2)` |
| `distance` | cùng phép duyệt `(p,q)` như pairwise trên mỗi cạnh, mỗi clause là nối hai no-good trên nhãn | `m · 2 · Σ_{d=1..K−1} max(0, n − d)` |
| `threshold` | như pairwise: `K ≥ n` chốt UNSAT bởi `trivial_unsat`, không sinh clause | 0 |

- `assignment` của order **thay** ALO + AMO của pairwise bằng chuỗi đơn điệu —
  mỗi chuỗi đơn điệu mã hóa đúng một nhãn.
- `permutation`: `n` nhãn đôi một khác nhau trong `1..n` thì tự thành hoán vị.
- No-good trên nhãn dựng bởi `_not_value`: `f(v) ≠ q` nghĩa là `f(v) ≤ q−1`
  hoặc `f(v) ≥ q+1`; hai biên `q = 1`, `q = n` rút gọn còn một literal, bên
  trong còn hai literal. Clause `permutation`/`distance` của order vì thế rộng
  tối đa 4 literal (thay vì 2 như pairwise).
- Ví dụ `path4` (assert trong `tests/sat/test_order.py`): 12 biến; K = 1:
  8 + 24 = 32 clause; K = 2: 8 + 24 + 18 = 50; K = 3: 8 + 24 + 30 = 62.

## §3.4 Ràng buộc at-most-one (AMO)

Contract dùng chung: `amo(literals, encoding, pool)` (`src/sat/pairwise.py`),
đổi AMO không sửa encoding ABP (ticket 08).

- **Pairwise AMO**: `C(m,2)` clause `(¬a ∨ ¬b)` cho `m` literal, không thêm
  biến. Trên 6 literal: 15 clause (`docs/sat_tooling.md`, bảng EncType).
- **Sequential counter** (`seqcounter`): qua `pysat.card.CardEnc.atmost`
  bound = 1 (`atmost_one_encoding`, `src/sat/backend.py`), thêm biến phụ từ
  `IDPool` sau vùng biến chính. Trên 6 literal: 14 clause
  (`docs/sat_tooling.md`).
- Danh sách hỗ trợ `SUPPORTED_AMO_ENCODINGS` (code): `pairwise`, `seqcounter`,
  `cardnetwrk`, `totalizer`, `mtotalizer`, `kmtotalizer`, `bitwise`, `ladder`,
  `sortnetwrk` — lấy từ `pysat.card`; `native` (cần CNFPlus) và tên lạ đều
  `ValueError`.
- **Kiểm chứng closure (ticket 08)**: kiểm exhaustive mọi tập con của 6
  literal (64 tập con, gồm cả tập 0/1 literal), mọi assignment — 729 lần kiểm
  mỗi encoding; assignment có ≤ 1 literal true phải thỏa toàn bộ clause AMO,
  > 1 true phải bị chặn. Cả hai encoding PASS
  (`docs/handoff/w2-sat/12-test-matrix.md`, test
  `tests/sat/test_matrix.py::test_amo_exhaustive_closure_over_all_subsets`).
- **Order không dùng AMO**: chuỗi đơn điệu thay ALO + AMO, nên `amo_encoding`
  được chấp nhận và ghi nhận trong `CNF` nhưng không đổi clause, không đổi kết
  quả (`tests/sat/test_order.py` assert stats bằng nhau khi đổi AMO).
- **Commander/product AMO**: nằm ngoài phạm vi — ticket 08 ghi rõ "không làm
  commander/product (Bonus, sau khi Core ổn)"; hai encoding này không nằm
  trong `SUPPORTED_AMO_ENCODINGS` (pysat.card không cung cấp sẵn).

## §3.5 Chiến lược duyệt K

Duyệt `K` tăng dần từ cận dưới, dừng ở lần UNSAT đầu tiên (`docs/sat_spec.md`
§5, `solve_sat` trong `src/sat/solve.py`):

```
lo = 0   # B tốt nhất đã verify (0 = chưa có nghiệm)
hi = n   # UNSAT theo đếm nhãn (lệch nhãn tối đa n − 1)
lặp khi lo + 1 < hi:
  K = lo + 1                       # ngưỡng nhỏ nhất chưa bị bác bỏ
  giải bài toán quyết định tại K
  SAT   → decode → verify → B = antibandwidth thực tế; lo = B; K kế tiếp = B + 1
  UNSAT → hi = K; B = K − 1 là tối ưu; dừng
  UNKNOWN (hết giờ) → dừng
```

- **`K ← B + 1`, không phải `K + 1`**: model SAT tại `K` có thể đạt `B > K`;
  nghiệm có giá trị `B` thỏa mọi ngưỡng `≤ B`, nhảy tới `B + 1` không bỏ sót
  ngưỡng nào.
- **UNSAT đầu tiên chứng minh tối ưu**: `B = K − 1`, vòng dò dừng với
  `lo + 1 = hi`; nghiệm tốt nhất đã verify là OPT.
- Mỗi lần dò dựng CNF mới và dùng backend mới; không dùng incremental/assumption
  ở W1/W2 (`docs/sat_spec.md` §5; `_probe` tạo `SatBackend` mới mỗi lần).
- `Config.time_limit` là ngân sách cho **cả chuỗi K**: gồm `build_cnf`,
  `add_clauses` và `solve` của mọi lần dò; deadline được kiểm trước mỗi pha,
  phần còn lại truyền vào solver (docstring `solve_sat`, `_probe`).
- `ub` ngoài (tùy chọn) chỉ được kiểm tra, không dùng để chứng minh: OPT vẫn
  cần UNSAT của solver; `ub` nhỏ hơn `B` đã verify → `ValueError`.
- **Hướng tìm kiếm là quyết định thiết kế của repo, không mượn của 2DBMP**
  (`docs/sat_spec.md` §5): không duyệt `K` từ trên xuống, không tìm kiếm nhị
  phân. Lý do: duyệt tăng dần đảm bảo lần dò UNSAT đầu tiên đồng thời chứng
  minh tối ưu, và mọi lần dò SAT trước đó đều cho nghiệm đã verify. Giả thuyết
  (chưa đo): các ngưỡng cao là UNSAT khó nhất.

Phân loại kết quả theo CONTRACT §5, từ trạng thái vòng dò (`summarise_result`,
`src/sat/solve.py`):

- `OPT`: có nghiệm verify và UNSAT đã chứng minh `K = lo`; `lb = ub = B`,
  `gap = 0`.
- `FEAS`: hết giờ với nghiệm đã verify, chưa chứng minh tối ưu; `ub = hi − 1`
  (cận trên từ ngưỡng UNSAT đã biết), `gap = ub − B`.
- `TO`: hết giờ chưa có nghiệm verify được.
- `ERR` (không phải kết quả tối ưu, không dùng làm bằng chứng): model SAT tại
  `K` không đạt ngưỡng khi `verify`; nghiệm OPT/FEAS mâu thuẫn bằng chứng dò
  (giá trị verify khác ngưỡng đã chứng minh, hoặc ≥ ngưỡng UNSAT); không có
  nghiệm verify được dù chưa hết giờ; lỗi backend/giấy phép (`BackendError`).
- `MO` (hết bộ nhớ) theo CONTRACT §5 nhưng pipeline W2 chưa cài
  `memory_limit` nên MO không bao giờ xuất hiện; đặt field khác mặc định thì
  pipeline phát warning, không bỏ qua im lặng (`_warn_ignored_config`,
  `IGNORED_CONFIG_FIELDS = (memory_limit, search_mode, symmetry, warm_start,
  seed)`).
- UNKNOWN của solver không dùng làm bằng chứng theo cả hai chiều
  (`docs/sat_spec.md` §4).

## §3.6 Backend solver

`SatBackend` (`src/sat/backend.py`) là lớp mỏng bọc PySAT — chỉ module này biết
tới PySAT; tầng trên chỉ thấy `add_clauses` / `solve` / `get_model` / `status`.

- Solver mặc định: `cadical195` (`DEFAULT_SOLVER`). Danh sách tên gợi ý
  `SUPPORTED_SOLVERS` gồm 16 solver nạp được clause và giới hạn được thời gian.
- Timeout (`solve(time_limit)`), hai cơ chế theo family:
  - `INTERRUPTIBLE_FAMILIES` (glucose3/4/42, gluecard3/4, minisat22, minisatep,
    maplesat, maplechrono, maplecm, mergesat3): `interrupt()` + watchdog
    thread, `solve_limited(expect_interrupt=True)`.
  - `BUDGETED_FAMILIES` (cadical103/153/195/300 — CaDiCaL không hỗ trợ
    interrupt): vòng lặp `conf_budget` tăng gấp đôi từ
    `CONFLICT_BUDGET_START = 1000`, kiểm đồng hồ giữa các vòng.
  - Family khác đặt `time_limit` → `BackendError` (map sang ERR).
- **Kissat bị loại, hạn chế vĩnh viễn W2** — chặn tại khởi tạo backend
  (`PYSAT_KISSAT_FAMILIES = {"kissat404"}` trong `SatBackend.__init__`) và tại
  pipeline (`_validate_solver` trước khi dựng backend). Lý do
  (`docs/sat_tooling.md` mục Kissat, kiểm trên Windows): assumptions bị bỏ qua
  kèm cảnh báo — `solve(assumptions=[-1,-2])` trả kết quả sai im lặng trên
  instance có đáp án đúng là False; `add_clause` sau `solve` làm process thoát
  mã `-1073740791`; model sai — trên `[[1,2],[-1,2],[1,-2]]` hàm `get_model()`
  trả `[-1,-2]`, vi phạm mệnh đề `[1,2]`; crash access
  violation `-1073741819` trên 3-SAT ngẫu nhiên 20 biến; không có binary
  kissat ngoài trên PATH.
- **RQ2 dùng CaDiCaL + Glucose** (`docs/sat_tooling.md` kết luận W2): Glucose
  chạy qua cùng `SatBackend`, không pipeline riêng; E2E khớp oracle brute-force
  trên toy (B tối ưu, decode, status, K-search chứng minh OPT,
  `tests/sat/test_glucose_e2e.py`).
- Caveat timeout Glucose (`docs/sat_tooling.md`): budget không ổn định khi giải
  nhiều lần trong cùng một process; mỗi `_probe()` dựng backend mới nên E2E
  ổn định, nhưng test/pilot với glucose không được phụ thuộc timeout chặt —
  dùng ngân sách rộng.

## §3.7 Đo lường

Metric theo CONTRACT §4 (`Result`) và ticket 10; cách đo trong
`src/sat/solve.py` + `docs/sat_tooling.md`:

- `t_encode`: `time.perf_counter()` quanh `build_cnf` mỗi lần dò, cộng dồn.
- `t_solve`: `time.perf_counter()` quanh `backend.solve()` mỗi lần dò, cộng dồn.
- Thời gian nạp clause (`add_clauses`) không nằm trong `t_encode` hay
  `t_solve`, nhưng nằm trong `t_total` (đọc trực tiếp từ `_probe`).
- `t_total`: toàn bộ lời gọi `solve_sat` (mọi lần dò + decode + verify).
- `peak_memory`: working set lớn nhất của process, đơn vị MB (float), đo bằng
  `GetProcessMemoryInfo` (ctypes + psapi, không thêm dependency), chụp tại các
  mốc — trước khi giải, sau mỗi lần dò, và trong mỗi lần dò: trước solve (sau
  khi nạp clause), sau solve, sau decode — rồi lấy max. Là **max của các điểm
  chụp**, không phải peak liên tục. `None` khi ERR.
- Hạn chế nền tảng: `psapi` là API Windows nên số đo bộ nhớ chỉ chạy được trên
  Windows; working set gồm cả bộ nhớ C của solver và bộ nhớ Python
  (`docs/sat_tooling.md`).
- So sánh với exact solver: dùng runner `wall_time` của P3, không so `t_total`
  giữa hai family vì phạm vi import khác nhau (khuyến nghị R2 trong
  `docs/handoff/w2-sat/13-review-p1-formulation.md`).

## §3.8 Decode và kiểm chứng nghiệm

- `decode_model` (riêng cho từng encoding) biến model thành labeling:
  - pairwise: mỗi đỉnh phải có đúng một `x[v][p]` dương; tập nhãn phải là
    hoán vị của `1..n`; vi phạm → `ValueError` (lỗi encoding, không bỏ qua).
  - order: nhãn là `p` nhỏ nhất với `o[v][p] = 1` (chuỗi bằng 0 → nhãn `n`);
    labeling phải là hoán vị của `1..n`.
- Model chưa phải nghiệm: nghiệm bắt buộc qua `verify(instance, labeling)`
  (CONTRACT §6) — kiểm tra hoán vị hợp lệ, gán đủ đỉnh, không trùng nhãn, tính
  lại giá trị mục tiêu từ labeling và đồ thị gốc.
- `solve_sat` luôn `verify` trước khi đưa nghiệm vào `Result`;
  `solve_decision` trả labeling từ `_probe` **không** qua `verify` — caller
  phải tự gọi (`docs/sat_spec.md` §4).

## §3.9 Bằng chứng đúng đắn hiện có (W2)

Từ lần chạy thật 2026-10-20, chi tiết trong `docs/handoff/w2-sat/12-test-matrix.md`:

- Ma trận 2 abp_encoding × 2 amo_encoding × 2 solver = **8 cấu hình**, 213
  test trong `tests/sat/test_matrix.py`, toàn suite 422 test xanh trong
  15.58 s. Mỗi cấu hình: 10 test OPT khớp oracle + 10 test SAT/UNSAT tại mọi
  `K ∈ 1..n` + 6 test model counting — mọi nghiệm SAT qua `verify()` trước khi
  so oracle.
- Model counting bằng blocking clause (trên biến chính, biến phụ seqcounter
  không làm một hoán vị đếm hai lần) khớp đếm `itertools.permutations` trên 6
  cặp (instance, K), gồm cả UNSAT (0 nghiệm) — không thừa, không thiếu, ở cả
  8 cấu hình.
- AMO closure exhaustive (§3.4): cả `pairwise` lẫn `seqcounter` PASS.
- Tier 1 (`n ≤ 12`, cấu hình mặc định): OPT tự chứng minh bằng UNSAT của solver
  tại `K = B + 1`, nghiệm qua `verify()`, hai encoding cùng B — 3/3 PASS
  (path10 B = 5, grid3x4 B = 5, random12-seed42 B = 3).
- Bộ 10 instance có oracle (n ≤ 9) và B tối ưu: path4 B=2, cycle5 B=2,
  grid3x3 B=3, complete5 B=1, star6 B=1, bintree3 B=3, grid2x3 B=2,
  disconnected B=3, isolated B=3, random8-seed42 B=2.

## §3.10 Giới hạn của phương pháp (phạm vi W2)

- Hai encoding (pairwise, order) — không có encoding Bonus (staircase).
- Không incremental: mỗi ngưỡng dựng CNF mới + backend mới.
- Không symmetry breaking: `Config.symmetry` bị bỏ qua kèm warning
  (§3.5), pilot RQ1 đặt symmetry OFF (ticket 16).
- Đo bộ nhớ chỉ trên Windows, là max của điểm chụp không liên tục (§3.7).
- Số liệu đúng đắn mới phủ tới `n ≤ 12` (tier 1); hiệu năng chưa đo — thuộc
  pilot W3 (ticket 16, 17).

## Bảng trace § → nguồn

| Mục | Nguồn |
|---|---|
| §3.1 | CONTRACT.md §1; docs/sat_spec.md §1; src/sat/pairwise.py (trivial_unsat, _check_k); src/sat/solve.py (_probe, _validate_instance); src/sat/loader.py |
| §3.2 | src/sat/pairwise.py (build_cnf, var_of); src/sat/order.py (build_cnf, docstring) |
| §3.3 | docs/sat_spec.md §3; src/sat/pairwise.py; src/sat/order.py; tests/sat/test_pairwise.py; tests/sat/test_order.py |
| §3.4 | src/sat/pairwise.py (amo, SUPPORTED_AMO_ENCODINGS); src/sat/backend.py (atmost_one_encoding, new_id_pool); docs/sat_tooling.md (bảng EncType); 12-test-matrix.md (AMO closure); ticket 08 |
| §3.5 | docs/sat_spec.md §5; src/sat/solve.py (solve_sat, summarise_result, _probe, _warn_ignored_config); CONTRACT.md §5; ticket 10 |
| §3.6 | src/sat/backend.py (SatBackend, INTERRUPTIBLE_FAMILIES, BUDGETED_FAMILIES, PYSAT_KISSAT_FAMILIES, KISSAT_LIMITATION, CONFLICT_BUDGET_START); docs/sat_tooling.md (Kissat, kết luận W2); src/sat/solve.py (_validate_solver); ticket 09 |
| §3.7 | src/sat/solve.py (working_set_mb, solve_sat, _probe); docs/sat_tooling.md (đo t_encode/t_solve/peak_memory, kết luận W2 ticket 10); 13-review-p1-formulation.md (R2) |
| §3.8 | src/sat/pairwise.py (decode_model); src/sat/order.py (decode_model); CONTRACT.md §6; docs/sat_spec.md §4 |
| §3.9 | docs/handoff/w2-sat/12-test-matrix.md; tests/sat/test_matrix.py |
| §3.10 | docs/sat_spec.md §5; src/sat/solve.py (IGNORED_CONFIG_FIELDS); ticket 16 |
