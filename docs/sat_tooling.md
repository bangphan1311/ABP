# Tooling SAT (W1)

Owner: P2. Đo trên PySAT `1.9.dev15`, Python `3.14.6`, Windows (msvc), `.venv` của repo.
Mỗi mục dưới đây có kết luận hoặc ghi rõ **"chưa hỗ trợ"** kèm lý do.

## 1. PySAT

- Pin trong `requirements.txt`: `python-sat==1.9.dev15` (kèm `six`).
- PySAT là bản Python ship sẵn nhiều solver native; không cần cài solver ngoài cho W1.
- `pysat.solvers.Solver(name=...)` chọn solver. Tên hợp lệ và alias nằm trong
  `pysat.solvers.SolverNames` (ví dụ `glucose4 = ('g4', 'g41', 'glucose4', 'glucose41')`).
- Solver dựng được trong wheel này (đã thử `Solver(name=...)` rồi `delete()`):
  `cadical103/153/195/300`, `glucose3/4/42`, `gluecard3/4`, `lingeling`, `kissat`
  (= `kissat404`), `maplechrono`, `maplecm`, `maplesat`, `mergesat3`, `minisat22`,
  `minisat-gh` (alias `mgh`; tên `minisatgh` **không** được nhận), `minisat-ep`,
  `minicard`.
- **Chưa hỗ trợ**: family `cryptosat` (`cryptosat`, `cms`, `cryptominisat`, ...) —
  `NoSuchSolverError`/`AssertionError` khi dựng trong wheel này.
- Mặc định của backend: `cadical195` (`SatBackend.DEFAULT_SOLVER`), đổi qua
  `Config.sat_solver`.

## 2. Interface backend

`src/sat/backend.py` — lớp duy nhất biết PySAT:

| Thành phần | Ý nghĩa |
|---|---|
| `SatBackend(solver_name=None, use_timer=False)` | Dựng solver; lỗi tên/build/giấy phép → `BackendError` |
| `add_clause(clause)` | Thêm một clause; từ chối clause rỗng, literal `0`, literal không phải `int` |
| `add_clauses(clauses)` | Thêm nhiều clause |
| `solve(time_limit=None) -> "SAT"\|"UNSAT"\|"UNKNOWN"` | Giải; `UNKNOWN` khi hết giờ |
| `status` | Trạng thái lần `solve` gần nhất |
| `get_model() -> list[int] \| None` | Model đầy đủ (literal có dấu) khi `status == "SAT"` |
| `n_vars`, `n_clauses` | Số biến solver đã biết, số clause đã nạp |
| `solve_time` | Thời gian giải lần gần nhất (giây) |
| `delete()`, `with` | Giải phóng solver native |

Lưu ý đã kiểm chứng: `Solver.nof_clauses()` trả số clause trong header DIMACS, **không**
phải số clause thêm tăng dần (trả `0` sau `add_clause`). `n_clauses` vì vậy tự đếm.
`Solver.nof_vars()` cập nhật đúng theo biến lớn nhất đã thấy.

## 3. Lấy model

- `Solver.get_model()` trả **đủ** biến (True/False dạng literal có dấu), kiểm chứng trên
  `path4` K=2: pairwise 16/16 biến, seqcounter 40/40 biến (kể cả aux var của `pysat.card`).
- Decode: `src/sat/pairwise.decode_model(cnf, model)` lấy literal dương, đòi mỗi đỉnh đúng
  một nhãn và nhãn là hoán vị `1..n`, nếu không → `ValueError` (không bỏ qua model sai).
- Model chỉ được dùng khi `status == "SAT"`; `get_model()` trả `None` ở trạng thái khác.

## 4. Timeout

PySAT **không** có một cơ chế timeout thống nhất; hai cơ chế dùng được, chọn theo family
solver (đọc mã nguồn `pysat/solvers.py` để xác nhận, không suy đoán):

| Cơ chế | Family | Cách làm |
|---|---|---|
| `interrupt()` | `glucose3/4/42`, `gluecard3/4`, `minisat22`, `minisat-gh`, `minisat-ep`, `maplesat`, `maplechrono`, `maplecm`, `mergesat3` | watchdog thread gọi `interrupt()`, giải bằng `solve_limited(expect_interrupt=True)`; chính xác theo đồng hồ |
| `conf_budget()` | `cadical103/153/195/300`, `kissat404` | vòng lặp: `conf_budget(budget)` → `solve_limited()`; `None` nghĩa là chưa kết luận → kiểm tra deadline, tăng gấp đôi budget, lặp lại |

- **Chưa hỗ trợ**: `lingeling` (`interrupt`, `solve_limited`, `conf_budget` đều
  `NotImplementedError`), `minicard` (không nằm trong hai family trên). Nếu
  `Config.time_limit` được đặt với family đó → `BackendError`, không im lặng bỏ qua.
- **Chưa hỗ trợ**: `prop_budget()` trên CaDiCaL và Kissat (`NotImplementedError`).
- Đo thực tế trên `pysat.examples.genhard.PHP(nof_holes=13)` với `time_limit=0.3`:
  `glucose4` → `UNKNOWN` sau **0.30 s**; `cadical195` → `UNKNOWN` sau **0.33 s**.
- Sai số của cơ chế `conf_budget`: budget là số xung đột, không phải giây, nên mỗi lần
  `solve_limited` có thể vượt deadline; độ vượt bị chặn bởi thời gian của vòng trước
  (budget tăng gấp đôi). Cần đo kỹ hơn ở W2 nếu dùng `time_limit` sát ngưỡng.
- Cờ interrupt còn sót: với family dùng `interrupt()`, nếu watchdog bắn đúng lúc solve
  vừa xong thì lần `solve` **kế tiếp trên cùng backend** có thể trả `UNKNOWN`. Pipeline
  W1 luôn dựng backend mới cho mỗi ngưỡng K nên ảnh hưởng cục bộ, và hướng sai là
  "thận trọng" (`FEAS`/`TO` thay vì `OPT`), không bao giờ cho nghiệm sai.
- `time_limit` ≤ 0 → `UNKNOWN` ngay, không gọi solver.

## 5. Assumptions

- `solve(assumptions=[...])` và `solve_limited(assumptions=[...])` hoạt động với CaDiCaL
  (kiểm chứng: `solve(assumptions=[-1, -2])` trên clause `(1 ∨ 2)` trả `False`).
- **Chưa hỗ trợ**: Kissat bỏ qua `assumptions` (PySAT phát `warnings.warn`).
- Danh sách assumption không được chứa literal trùng.
- W1 không dùng assumptions: mỗi ngưỡng K dựng CNF mới (rõ ràng hơn, chậm hơn).
  Incremental kèm assumption là hạng mục W2.

## 6. AMO có sẵn

`pysat.card.CardEnc.atmost(lits, bound=1, vpool=pool, encoding=EncType.<tên>)`.
Số clause cho `m = 3` literal (đo thực tế):

| `EncType` | pairwise | seqcounter | cardnetwrk | sortnetwrk | totalizer | mtotalizer | kmtotalizer | bitwise | ladder | native |
|---|---|---|---|---|---|---|---|---|---|---|
| clause (m=3) | 3 | 5 | 17 | 17 | 9 | 11 | 8 | 6 | 12 | 0 |

- `pairwise` (mặc định của ABP) do `src/sat/pairwise.amo` tự sinh: `C(m,2)` clause.
- Khi truyền `vpool`, `CardEnc` trả `CNFPlus`; với encoding không phải `native`, ràng buộc
  vẫn nằm đầy đủ trong `.clauses`.
- **Chưa hỗ trợ**: `native` — ràng buộc nằm trong `CNFPlus.atmosts` (không phải clause), chỉ
  solver MiniCard mới hiểu; backend chưa hỗ trợ clause native nên `amo(..., "native")` báo lỗi
  thay vì im lặng làm mất ràng buộc.

## 7. Kissat

- `Solver(name="kissat")` (alias của `kissat404`) **dựng được**, nhưng **chưa hỗ trợ** trong
  W1 vì wheel PySAT `1.9.dev15` trên Windows crash khi nạp clause:
  `Windows fatal exception: access violation` (exit code `-1073741819` = `0xC0000005`).
- Lệnh tái hiện (chạy trong process riêng, nó sẽ crash):

```
python -c "from pysat.solvers import Solver; s = Solver(name='kissat', bootstrap_with=[[1, 2], [-1]]); print(s.solve())"
```

  Kết quả: không in gì, process thoát với `-1073741819`. `add_clause` tăng dần crash tương
  tự; chỉ `Solver(name='kissat')` rồi `delete()` là an toàn.
- Vì vậy `docs/sat_spec.md` và `SatBackend` dùng CaDiCaL. `kissat` **không** nằm trong
  `supported_solvers()` (API công khai) vì P3 lặp qua danh sách đó sẽ mất process; chỉ
  `Solver(name='kissat')` rồi `delete()` là an toàn, không phải đường dùng được.
- Cách khác nếu W2 cần Kissat: gọi binary `kissat` bên ngoài (DIMACS vào/ra), đo thời gian
  bằng subprocess — **chưa làm ở W1**.

## 8. Đo `t_encode`, `t_solve`, memory

- `t_encode`: `perf_counter()` bọc `build_cnf(...)` trong `src/sat/solve.py::_probe`, cộng dồn
  qua các ngưỡng K, trả ở `Result.t_encode`. `t_solve` đo tương tự quanh `backend.solve(...)`;
  `t_total` bao cả hai cộng phần còn lại (nạp clause vào solver, vòng lặp tìm K).
  `t_encode` của PySAT (`CardEnc`) nằm trong `t_encode`; thời gian `add_clauses` hiện **không**
  nằm trong `t_encode` lẫn `t_solve`, chỉ có trong `t_total` — cần tách riêng ở W2 nếu muốn
  so sánh chi phí encode.
- Log từng lần dò: `Result.metadata["probes"] = [{"k", "status", "t_solve"}, ...]`.
- `peak_memory`: **chưa đo ở W1**, để `None`. Cách đo đề xuất cho chạy chính thức:
  `psutil.Process().memory_info().rss` (bắt cả bộ nhớ native của solver) hoặc
  `tracemalloc` (chỉ bộ nhớ Python — **không** thấy bộ nhớ native, nên không đủ). `psutil`
  chưa nằm trong `requirements.txt`; quyết định thêm hay không để P3 chốt ở `PROTOCOL.md`.