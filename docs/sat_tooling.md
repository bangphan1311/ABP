# Công cụ SAT: PySAT trong môi trường `.venv`

Tài liệu này chỉ mô tả những gì có thể kiểm chứng trong `.venv` đã cài các gói của `requirements.txt`, và trạng thái hệ thống Windows. Mỗi khẳng định đều đã chạy lại bằng `.venv\Scripts\python.exe`. Khẳng định chưa kiểm được ghi "chưa kiểm".

Kết quả thô và lệnh chạy nằm trong `docs/handoff/sat-tooling/evidence.md`.

## Môi trường

- Python: 3.11.15, `.venv\Scripts\python.exe`.
- Venv không có `pip` (`python -m pip` báo `No module named pip`). Danh sách gói lấy bằng `importlib.metadata`.
- Gói SAT: `python-sat` 1.9.dev15. Module đọc được là `pysat.__version__` = `1.9.dev15`, đúng với pin trong `requirements.txt`.
- Các gói khác có trong venv: `ortools` 9.15.6755, `pytest` 9.1.1, `numpy`, `pandas`, `protobuf`.
- Chưa kiểm: `gurobipy` 13.0.3, `cplex` 22.2.0.1 và `docplex` 2.32.264 có trong `requirements.txt` nhưng KHÔNG có trong venv. Không liên quan SAT, nhưng cần biết khi cài lại.
- Hệ thống: không có binary `kissat` trên PATH (`Get-Command kissat` và `where.exe kissat` đều không thấy). Chưa tìm kiếm toàn ổ đĩa.

## Giao diện backend PySAT

Import dùng: `from pysat.solvers import Solver`, `from pysat.card import CardEnc, EncType`.

- Tạo solver: `Solver(name="cadical195", bootstrap_with=clauses)`. `clauses` là list các list số nguyên, literal âm là phủ định. Hỗ trợ `with Solver(...) as s:` và `s.delete()`.
- Thêm mệnh đề: `s.add_clause([1, -2])`. Thêm sau khi đã `solve` rồi solve lại được (xem bảng incremental).
- Giải: `s.solve(assumptions=[...])` trả `True` (SAT), `False` (UNSAT). Không có budget thì không trả `None`.
- Model: `s.get_model()` trả list literal có dấu, hoặc `None`. Đã kiểm với `cadical195`: 30 instance 3-SAT ngẫu nhiên (20 biến, 60 mệnh đề), 0 model vi phạm mệnh đề.
- Core khi UNSAT dưới assumptions: `s.get_core()`. Ví dụ: assumptions `[-1, -2]` trên `[[1,2],[-1,2],[1,-2]]` cho core `[-1]`.
- Thống kê: `s.accum_stats()` trả dict có `conflicts`, `decisions`, `propagations`, `restarts`. Một số solver không ghi `propagations` đúng (ví dụ `maplesat` báo 0), chưa kiểm nguyên nhân.

## Timeout với PySAT thô

Dấu hiệu UNKNOWN là `solve_limited()` trả `None`.

- Budget theo conflict: `s.conf_budget(n)` rồi `s.solve_limited()`. Đã kiểm `cadical195` và `minisat22` trên PHP(11,10) với `n=200`: trả `None` trong khoảng 1 ms. `cadical195` cũng trả `None` với `n=2000` trên PHP(10,9).
- Budget không ổn định giữa các solver trong cùng một process. Với `minisat22`, `glucose4`, `maplesat`, solver đầu tiên trong process tôn trọng budget, các solver sau đôi khi bỏ qua budget và giải đủ tới kết quả (`False`, ví dụ `glucose4` 258 231 conflict, `minisat22` 998 326 conflict). `cadical195` cho kết quả nhất quán trong 3 lần chạy riêng và trong kịch bản hai solver liên tiếp. Nguyên nhân chưa kiểm.
- Budget theo propagation: `s.prop_budget(n)` có hiệu lực với `minisat22`, `glucose4`, `maplesat` (kết quả thiếu nhất quán như trên). `cadical195` ném `NotImplementedError: Limit on propagations is currently unsupported by CaDiCaL.`. `lingeling` ném `NotImplementedError`.
- Ngắt theo thời gian thực: `threading.Timer(0.5, s.interrupt)` cộng `s.solve_limited(expect_interrupt=True)`. Với `minisat22`, `glucose4`, `maplesat` trả `None` sau khoảng 0.5 s. Với `cadical195`, `interrupt()` ném `NotImplementedError: Limited solve is currently unsupported by CaDiCaL.` trong thread phụ, solver chạy tới hết và trả `False` sau 4.6 s. `lingeling` ném `NotImplementedError` ngay trên `solve_limited`.
- Kết luận cho PySAT thô: với `cadical195` chỉ có `conf_budget` là đường UNKNOWN đã kiểm. Với họ minisat (`minisat22`, `glucose4`, `maplesat`) có thể dùng `interrupt` đã kiểm cho một lần giải, nhưng không nên tin budget khi giải nhiều lần trong một process. Chưa kiểm các solver khác (`cadical103`, `cadical153`, `cadical300`, `gluecard3`, `gluecard4`, `maplechrono`, `maplecm`, `mergesat3`, `minicard`, `minisatep`) trên instance khó.

## Incremental và assumptions theo solver

Kiểm trên instance nhỏ `[[1,2],[-1,2],[1,-2]]`. Với mỗi solver: giải, giải với assumptions `[-1,-2]` (kỳ vọng `False`, core `[-1]`), thêm mệnh đề `[3]` rồi giải lại.

| Solver | Tạo được | assumptions có hiệu lực | thêm mệnh đề sau solve |
|---|---|---|---|
| cadical103, cadical153, cadical195, cadical300 | có | có | có |
| glucose3, glucose4, glucose42 | có | có | có |
| gluecard3, gluecard4 | có | có | có |
| lingeling | có | có | có |
| maplechrono, maplecm, maplesat | có | có | có |
| mergesat3, minicard, minisat22, minisatep | có | có | có |
| kissat404 (alias ks, ks4, kissat, kissat4) | có | KHÔNG: bỏ qua, cảnh báo, trả kết quả sai | KHÔNG: process bị abort |
| cryptosat, minisatgh | KHÔNG: `NoSuchSolverError` | - | - |

Lưu ý: kết quả assumptions chỉ kiểm trên instance 3 biến. Chưa kiểm trên instance lớn.

## Mã hóa AMO và at-most-k: `pysat.card.EncType`

Kiểm bằng `CardEnc.atmost` trên 6 literal, bound 1, 2, 3. Tính đúng được kiểm bằng cách thử 64 phép gán với `cadical195` và so với `sum <= bound`.

| Encoder (giá trị) | bound=1 | bound=2 | bound=3 | Ghi chú |
|---|---|---|---|---|
| pairwise (0) | đúng, 15 mệnh đề | `UnsupportedBound` | `UnsupportedBound` | chỉ AMO |
| seqcounter (1) | đúng, 14 mệnh đề | đúng, 18 | đúng, 18 | |
| sortnetwrk (2) | đúng, 59 | đúng, 59 | đúng, 59 | |
| cardnetwrk (3) | đúng, 28 | đúng, 56 | đúng, 56 | |
| bitwise (4) | đúng, 18 | `UnsupportedBound` | `UnsupportedBound` | chỉ AMO |
| ladder (5) | đúng, 24 | `UnsupportedBound` | `UnsupportedBound` | chỉ AMO |
| totalizer (6) | đúng, 32 | đúng, 32 | đúng, 32 | |
| mtotalizer (7) | đúng, 33 | đúng, 33 | đúng, 32 | |
| kmtotalizer (8) | đúng, 20 | đúng, 31 | đúng, 30 | |
| native (9) | 0 mệnh đề, sai | 0 mệnh đề, sai | 0 mệnh đề, sai | không sinh CNF, không dùng với `CardEnc` |

AMO là bound=1. Chưa kiểm tính đúng với n lớn hơn 6.

## Kissat

Cách tới Kissat:

- Qua PySAT: tên `kissat404`. Tạo được. Không có binary kissat ngoài trên PATH.
- Kết quả kiểm trên Windows, không đạt yêu cầu dùng được:
  - Assumptions bị bỏ qua. PySAT in cảnh báo `Kissat does not support assumptions. The assumptions parameter will be ignored.` và `solve(assumptions=[-1,-2])` trả `True` trên instance mà đáp án đúng là `False`. Đây là lỗi im lặng, dễ cho kết quả sai.
  - `add_clause` sau `solve` làm process thoát với mã `-1073740791`, in `kissat_add: Coverage goal 'solver->level' reached.`. Không incremental.
  - Model sai. Trên `[[1,2],[-1,2],[1,-2]]`, `get_model()` trả `[-1,-2]`, vi phạm mệnh đề `[1,2]`. Lặp lại được trong 2 lần chạy.
  - Crash (`access violation`, mã `-1073741819`) trên 3-SAT ngẫu nhiên 20 biến, 40 mệnh đề (seed 7), trước khi `solve` trả về. Cũng crash khi gọi `conf_budget`/`prop_budget`/`interrupt` trên PHP(10,9). Chưa tách được lệnh nào gây crash.
  - Trường hợp tầm thường `[[1],[2,3]]` cho `True`, model `[1,2,3]` đúng.
- Kết luận: Kissat qua PySAT `kissat404` không dùng được trong môi trường này. Không cần đưa vào W1. Chưa kiểm binary kissat ngoài (phải cài và đo riêng).

## Đo t_encode, t_solve và bộ nhớ

- `t_encode`: `time.perf_counter()` quanh `CardEnc.atmost`. Với `seqcounter`, n=2000, k=50: 1.17 s và 1.30 s qua 2 lần chạy, 196 900 mệnh đề.
- `t_load`: thời gian `Solver(name, bootstrap_with=...)`, gồm đưa mệnh đề vào solver. Với `cadical195` trên cùng CNF: 0.19 s đến 0.21 s. Đây là mục riêng, không gộp vào `t_encode`.
- `t_solve`: `time.perf_counter()` quanh `s.solve()`. Với `cadical195` trên CNF trên: 0.006 s đến 0.007 s, SAT, 0 conflict. Instance này dễ, không đại diện.
- Bộ nhớ, hai cách đo khác nhau:
  - `tracemalloc`: chỉ thấy heap của Python, không thấy bộ nhớ của solver C. Đỉnh 25.6 MB trong lúc encode.
  - Working set của process qua `GetProcessMemoryInfo` (ctypes, psapi): nền 19.8 MB. Sau encode 48.5 MB, đỉnh 129.0 MB. Khi solver `cadical195` còn sống 94.1 MB. Sau `delete()` 49.5 MB. Đỉnh 129.0 MB xảy ra trước lần đo sau encode. Chưa tách được encode với load trong đỉnh này.
- Khác biệt: `t_encode` và `tracemalloc` là phía Python. `t_solve` là thời gian C của solver. Working set gồm cả bộ nhớ C và bộ nhớ Python.

## Kết luận về Kissat

Không đưa Kissat vào W1. Lý do: qua PySAT `kissat404` có lỗi assumptions im lặng, model sai, crash, không incremental. Không có binary kissat ngoài để so sánh. Nếu cần Kissat sau này, phải cài binary kissat ngoài, kiểm model và kết quả trên bộ instance nhỏ trước khi dùng.

## Chưa kiểm

- Ngắt theo thời gian (`interrupt`) và budget với các solver chưa liệt kê trong mục timeout.
- Nguyên nhân budget bị bỏ qua giữa các lần giải trong cùng process.
- Tính đúng của assumptions và core trên instance lớn.
- Tính đúng của mã hóa AMO với n lớn hơn 6.
- Nguồn đỉnh bộ nhớ 129.0 MB.
- Binary kissat ngoài và tìm kiếm trên toàn ổ đĩa.
- Các gói `gurobipy`, `cplex`, `docplex` không có trong venv.
