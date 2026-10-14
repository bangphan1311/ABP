# Tooling SAT (W1)

Owner: P2. Đo trên PySAT `1.9.dev15`, Python `3.14.6`, Windows (msvc), `.venv` của repo.
Mỗi mục dưới đây có kết luận hoặc ghi rõ **"chưa hỗ trợ"** kèm lý do.

## 1. PySAT

- Pin trong `requirements.txt`: `python-sat==1.9.dev15` (kèm `six`).
- Kiểm tra PyPI ngày 2026-10-13 (`https://pypi.org/pypi/python-sat/json`): bản mới nhất là
  `1.9.dev15` và **không có bản stable nào** (không có release khác ngoài `dev`), nên giữ
  pin bản dev; đổi sang stable khi PySAT phát hành.
- PySAT là bản Python ship sẵn nhiều solver native; không cần cài solver ngoài cho W1
  (Kissat là ngoại lệ, xem mục 7).
- `pysat.solvers.Solver(name=...)` chọn solver. Tên hợp lệ và alias nằm trong
  `pysat.solvers.SolverNames` (ví dụ `glucose4 = ('g4', 'g41', 'glucose4', 'glucose41')`).
- Solver dựng được trong wheel này (đã thử `Solver(name=...)` rồi `delete()`):
  `cadical103/153/195/300`, `glucose3/4/42`, `gluecard3/4`, `lingeling`, `kissat`
  (= `kissat404`), `maplechrono`, `maplecm`, `maplesat`, `mergesat3`, `minisat22`,
  `minisat-gh` (alias `mgh`; tên `minisatgh` **không** được nhận), `minisat-ep`,
  `minicard`.
- **Chưa hỗ trợ**: family `cryptosat` (`cryptosat`, `cms`, `cryptominisat`, ...) —
  `NoSuchSolverError`/`AssertionError` khi dựng trong wheel này.
- `solver_family()` đọc `vars(SolverNames)` (thuộc tính nội bộ của PySAT) để map alias →
  family. Nếu PySAT đổi tên, family lạ sẽ không nằm trong hai danh sách timeout → `BackendError`
  khi có `time_limit`, không im lặng trả kết quả sai.
- Mặc định của backend: `cadical195` (`SatBackend.DEFAULT_SOLVER`), đổi qua
  `Config.sat_solver`. `sat_solver="kissat"` đi qua binary ngoài (mục 7).

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

`validate_clause(clause)` là hàm dùng chung kiểm tra clause (rỗng, literal `0`, không phải
`int`) cho mọi backend. `src/sat/kissat.py::KissatBackend` cài lại **cùng interface** đó cho
binary Kissat ngoài (mục 7), nên `src/sat/solve.py` không cần biết đang dùng backend nào.

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
- **Phạm vi của `time_limit`**: ngân sách cho **cả chuỗi K** (WORK BREAKDOWN §5), gồm
  `build_cnf` (encode), `add_clauses` (nạp clause) và `solve` của mọi lần dò. `_probe`
  kiểm phần thời gian còn lại trước khi encode và sau khi nạp clause thì truyền phần còn
  lại vào solver. Pha đang chạy khi hết giờ vẫn hoàn thành, nên `t_total` chỉ vượt
  `time_limit` một khoảng nhỏ — đo trên máy dev (`cadical195`, `.venv` Python 3.11):
  `grid(10,10)` limit 1.0 s → `t_total` **1.19 s** (`TO`); `grid(8,8)` limit 1.0 s →
  **1.10 s** (`FEAS`), limit 2.0 s → **2.29 s** (`FEAS`). Test dùng cận
  `t_total < 2 * time_limit + 0.5` (`tests/sat/test_solve.py`).
- `time_limit` ≤ 0 → hết ngân sách trước khi encode: không dựng CNF, `UNKNOWN` ngay
  (`TO` nếu chưa có nghiệm nào).

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

**Trạng thái: đã có adapter gọi binary ngoài; máy dev hiện không có binary Kissat nên
vẫn "chưa hỗ trợ" để chạy thật** — không giả lập hành vi.

### 7.1 Vì sao không dùng Kissat của PySAT

`Solver(name="kissat")` (alias của `kissat404`) **dựng được**, nhưng wheel PySAT
`1.9.dev15` trên Windows giết process khi nạp clause:
`Windows fatal exception: access violation` (exit code `-1073741819` = `0xC0000005`).

```
python -c "from pysat.solvers import Solver; s = Solver(name='kissat', bootstrap_with=[[1, 2], [-1]]); print(s.solve())"
```

Kết quả: không in gì, process thoát với `-1073741819`. Vì vậy `SatBackend.add_clause`
**chặn** family `kissat404` bằng `BackendError` (thay vì để native crash), `kissat`
không nằm trong `supported_solvers()`, và Kissat đi qua binary ngoài.

### 7.2 Adapter `src/sat/kissat.py`

Cùng interface với `SatBackend` (`add_clause(s)`, `solve(time_limit)`, `get_model`,
`status`, `n_vars`, `n_clauses`, `delete`), nên pipeline `src/sat/solve.py` không phải
sửa gì: `Config(sat_solver="kissat")` → `_open_backend()` trả `KissatBackend`.

| Việc | Cách làm |
|---|---|
| Nạp CNF | giữ clause trong RAM, `solve` ghi ra file DIMACS (`p cnf <maxvar> <nclauses>`) trong `TemporaryDirectory` |
| Chạy | `subprocess.run([binary, cnf_path])`, không truyền option nào của Kissat |
| Kết quả | mã thoát `10` = SAT (đọc model ở các dòng `v`), `20` = UNSAT, mã khác = `BackendError` → `ERR` |
| Timeout | `subprocess` timeout phía Python; hết giờ thì process bị cắt và trả `UNKNOWN`. **Không** dựa vào option `--time` của Kissat (chưa kiểm chứng được trên Windows) |
| Không có binary | `BackendError("Không tìm thấy binary Kissat...")` → status `ERR`, không crash |
| Đo thời gian | `io_time` = dựng + ghi file DIMACS (đo bằng `perf_counter`), **không** tính vào `solve_time`; `solve_time`/`t_solve` = `subprocess` (khởi động process + giải). Vì khởi động process **không** tách được khỏi phần giải, `t_solve` của Kissat **không** so sánh trực tiếp được với `t_solve` của PySAT: RQ2 chỉ so trạng thái và số ca OPT (`docs/sat_spec.md` mục 9). `t_encode` vẫn là `build_cnf` |

### 7.3 Cách cài / trỏ tới binary

1. Cài Kissat (cần trình biên dịch C):
   - Linux/WSL: `git clone https://github.com/arminbiere/kissat && cd kissat && ./configure && make` → binary `build/kissat`.
   - Windows + MSVC: build từ source (Visual Studio Build Tools; Kissat dùng `configure`/`make`, thực tế dễ nhất là WSL).
   - Kiểm tra: `kissat --version`.
2. Trỏ adapter: đặt `ABP_KISSAT` = đường dẫn đầy đủ tới binary, hoặc để `kissat` trên `PATH`.
   Biến `ABP_KISSAT` trỏ tới file không tồn tại bị coi là **không có** (không đoán).

### 7.4 Đã thử trên máy dev (2026-10-13) — kết luận: chưa chạy được

| Nguồn | Kết quả |
|---|---|
| Release upstream `arminbiere/kissat` (`rel-4.0.4`) | chỉ có `apple-amd64`, `apple-arm64`, `linux-amd64` — **không có bản Windows** |
| `winget search kissat` | `No package found matching input criteria` |
| scoop main bucket (`bucket/kissat.json`) | không có manifest; `scoop` còn bị ExecutionPolicy chặn trên máy này |
| conda-forge `kissat` | API trả về danh sách file rỗng (không có `win-64`) |
| PyPI `kissat` / `pykissat` | 404 |
| Build từ source | không có `cl`, `gcc`, `clang`, `conda` trên `PATH` |
| PySAT `kissat404` | access violation khi nạp clause (mục 7.1) |

Vì vậy W1/W2 vẫn dùng CaDiCaL (+ Glucose); Kissat **chưa hỗ trợ trên máy này**, lý do cụ
thể là không có binary Windows và không có toolchain để build. Khi có binary, đặt
`ABP_KISSAT` là chạy được: test `tests/sat/test_kissat.py::test_kissat_matches_oracle_on_toy_instances`
tự bỏ skip.

## 8. Đo `t_encode`, `t_solve`, memory

- `t_encode`: `perf_counter()` bọc `build_cnf(...)` trong `src/sat/solve.py::_probe`, cộng dồn
  qua các ngưỡng K, trả ở `Result.t_encode`. `t_solve` đo tương tự quanh `backend.solve(...)`;
  `t_total` bao cả hai cộng phần còn lại (nạp clause vào solver, vòng lặp tìm K).
  `t_encode` của PySAT (`CardEnc`) nằm trong `t_encode`; thời gian `add_clauses` hiện **không**
  nằm trong `t_encode` lẫn `t_solve`, chỉ có trong `t_total` — cần tách riêng ở W2 nếu muốn
  so sánh chi phí encode.
- Log từng lần dò: `Result.metadata["probes"] = [{"k", "status", "b", "t_encode",
  "t_solve", "t_io", "variables", "clauses"}, ...]`; `variables`/`clauses` của `Result` là
  của lần dò **cuối cùng** (`docs/sat_spec.md` mục 6). `metadata["t_io"]` là tổng thời gian
  I/O ngoài `solve`: `KissatBackend` ghi file DIMACS (không tính vào `t_solve`, xem mục 7),
  PySAT để `0.0` vì nạp clause nằm ở `add_clauses`.
- `peak_memory`: **chưa đo ở W1**, để `None`. Cách đo đề xuất cho chạy chính thức:
  `psutil.Process().memory_info().rss` (bắt cả bộ nhớ native của solver) hoặc
  `tracemalloc` (chỉ bộ nhớ Python — **không** thấy bộ nhớ native, nên không đủ). `psutil`
  chưa nằm trong `requirements.txt`; quyết định thêm hay không để P3 chốt ở `PROTOCOL.md`.

## 9. Chạy test (venv Python 3.11 của repo)

Lệnh (đúng như đã chạy, `.venv` của repo là Python `3.11.15`; `docs/ENV.md` ghi `3.11.17`
cho env conda của P1 — cùng minor, khác patch):

```
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-w1
```

Kết quả 2026-10-14 (review lần 2 — đã thêm test R1/R2): `80 passed, 2 skipped in 5.08s`.
Hai test skip là các test cần binary Kissat thật (`tests/sat/test_kissat.py`, mục 7.4); phần
còn lại của `tests/sat/test_kissat.py` (parser, DIMACS, đường lỗi, binary giả) vẫn chạy.

- `python-sat==1.9.dev15` trên venv này: import được, `pysat.__version__ = '1.9.dev15'`
  (khớp `requirements.txt`).