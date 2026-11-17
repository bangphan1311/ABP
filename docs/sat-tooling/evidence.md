# Bằng chứng: công cụ SAT trong `.venv`

Mọi lệnh chạy từ `C:\Users\ducqu\workspace\ABP`. Chỉ dùng `.venv\Scripts\python.exe`, `requirements.txt` và hệ thống Windows. Không đọc `src/`, `tests/`, `docs/sat_spec.md`. Script probe nằm trong thư mục này. Kết quả thô nằm ở các file `raw_*.txt` cùng thư mục.

## Môi trường

Lệnh:

```
.venv\Scripts\python.exe -c "import importlib.metadata as m; print(sorted((d.metadata['Name'],d.version) for d in m.distributions()))"
.venv\Scripts\python.exe -m pip --version
.venv\Scripts\python.exe --version
Get-Command kissat; where.exe kissat
```

Dòng chính:

```
Python 3.11.15
No module named pip   (python -m pip)
('python-sat', '1.9.dev15'), ('ortools', '9.15.6755'), ('pytest', '9.1.1')
gurobipy, cplex, docplex: không có trong danh sách distributions
Get-Command kissat: không có kết quả; where.exe: INFO: Could not find files for the given pattern(s).
```

## Phiên bản PySAT và encoder

Lệnh: `.venv\Scripts\python.exe -u docs\handoff\sat-tooling\check_pysat.py` (ghi vào `raw_output.txt`).

Dòng chính:

```
pysat.__version__ 1.9.dev15
pairwise     bound=1 clauses=15 top_id=6 semantic_ok=True
pairwise     bound=2 ERROR UnsupportedBound: (0, 2)
seqcounter   bound=2 clauses=18 top_id=14 semantic_ok=True
bitwise      bound=2 ERROR UnsupportedBound: (4, 2)
ladder       bound=2 ERROR UnsupportedBound: (5, 2)
totalizer    bound=1 clauses=32 top_id=22 semantic_ok=True
native       bound=1 clauses=0 top_id=6 semantic_ok=False
```

Các dòng còn lại trong `raw_output.txt`: toàn bộ encoder đều `semantic_ok=True` trừ `native`.

## Solver: incremental, assumptions, budget

Lệnh: cùng `check_pysat.py`. Dòng chính:

```
cadical195 {'solve': True, 'model': True, 'assumptions': False, 'core': [-1], 'incremental_add': True, 'conf_budget0': True, 'interrupt': True}
minisat22 {'solve': True, 'model': True, 'assumptions': False, 'core': [-1], 'incremental_add': True, 'conf_budget0': True, 'interrupt': None}
cryptosat    CTOR ERROR NoSuchSolverError: cryptosat
minisatgh    CTOR ERROR NoSuchSolverError: minisatgh
lingeling {... 'conf_budget0': 'ERR NotImplementedError: Limited solve is currently unsupported by Lingeling.', 'interrupt': 'ERR NotImplementedError: ...Lingeling.'}
```

Ghi chú: `conf_budget0` và `interrupt` trong bảng này trên instance tầm thường, không có ý nghĩa. Bằng chứng timeout thật nằm ở phần dưới.

## Timeout trên PHP(10,9)

Lệnh: `.venv\Scripts\python.exe -u docs\handoff\sat-tooling\probe_timeout.py` (ghi vào `raw_timeout.txt`).

```
== conf_budget(2000): result None means UNKNOWN
minisat22    budget result=None t=0.014s
glucose4     budget result=False t=17.576s
maplesat     budget result=False t=5.931s
cadical195   budget result=None t=0.017s
lingeling    budget ERR NotImplementedError: Limited solve is currently unsupported by Lingeling.
== prop_budget(20000)
minisat22    prop budget result=False
cadical195   prop ERR NotImplementedError: Limit on propagations is currently unsupported by CaDiCaL.
== interrupt from Timer after 0.5s
minisat22    interrupt result=None t=0.503s
glucose4     interrupt result=None t=0.517s
maplesat     interrupt result=None t=0.509s
cadical195   interrupt result=False t=4.623s   (kèm: NotImplementedError: Limited solve is currently unsupported by CaDiCaL.)
lingeling    interrupt ERR NotImplementedError: Limited solve is currently unsupported by Lingeling.
```

Trên PHP(11,10), `check_pysat.py` cho `minisat22 conf_budget=200 -> None 0.001s` và `cadical195 conf_budget=200 -> None 0.002s`.

## Budget không ổn định giữa các lần giải trong cùng process

Lệnh: `.venv\Scripts\python.exe -u docs\handoff\sat-tooling\probe_budget_isolation.py <solver>` (ghi vào `raw_budget_isolation.txt` cho `minisat22`; các solver khác chạy trực tiếp).

```
minisat22:
trial 0 alone: conf_budget=2000 -> None, conflicts=2000
trial 1 alone: conf_budget=2000 -> False, conflicts=492993
trial 2 alone: conf_budget=2000 -> False, conflicts=778447
A (budget 2000) -> None 2000
B (budget 2000, after A) -> None 2001
glucose4:
trial 0 alone: conf_budget=2000 -> None, conflicts=2988
trial 1 alone: conf_budget=2000 -> False, conflicts=258231
trial 2 alone: conf_budget=2000 -> False, conflicts=258231
maplesat:
trial 0 alone: conf_budget=2000 -> None, conflicts=2001
trial 1 alone: conf_budget=2000 -> False, conflicts=115372
cadical195:
trial 0/1/2 alone: conf_budget=2000 -> None, conflicts=2001
A -> None 2001; B -> None 2001
```

Lần giải không budget (`probe_budget_check.py`): `glucose4 unlimited solve -> False t=17.294s conflicts=258231`, `minisat22 unlimited solve -> False t=6.103s conflicts=998326`, `maplesat unlimited solve -> False t=5.887s conflicts=115372`. Các số conflict khớp với lần "False" ở trên, nghĩa là budget bị bỏ qua.

## Kissat

Lệnh: `probe_kissat.py <assumptions|add_after_solve|budget|interrupt|solve>` và `probe_kissat_model.py <solver>`. Ghi vào `raw_kissat.txt`.

```
probe_kissat solve -> True model [-1, -2]
probe_kissat assumptions: solve(assumptions=[-1,-2]) -> True expected False (UNSAT)
warnings: ['Kissat does not support assumptions. The assumptions parameter will be ignored.']
probe_kissat add_after_solve: first solve -> True
solvers/kissat404/src\internal.c:361: kissat_add: Coverage goal `solver->level' reached.   exit=-1073740791
probe_kissat budget: (không in gì)   exit=-1073741819
probe_kissat interrupt: (không in gì)   exit=-1073741819
probe_kissat_model cadical195: model satisfies: True; random 3-SAT: models violating clauses=0
probe_kissat_model kissat404: hand-made instance, model: True [-1, -2] satisfies: False   exit=-1073741819
```

Lệnh bổ sung đã chạy trong shell (không lưu thành file):

```
.venv\Scripts\python.exe -u -c "from pysat.solvers import Solver; s=Solver(name='kissat404', bootstrap_with=[[1],[2,3]]); print(s.solve(), s.get_model())"
  → ctor ok / solve True / model [1, 2, 3] / exit=0
.venv\Scripts\python.exe -u -c "(random 3-SAT, seed 7, 20 vars, 40 clauses) Solver(name='kissat404', ...); s.solve()"
  → ctor ok / exit=-1073741819 (crash, chạy 2 lần, cùng kết quả)
.venv\Scripts\python.exe -u -c "Solver(name='kissat404', bootstrap_with=[[1,2],[-1,2],[1,-2]]); s.solve(); s.get_model()"
  → True [-1, -2] (2 lần, đều sai: vi phạm [1,2])
```

## Đo t_encode, t_solve, bộ nhớ

Lệnh: `.venv\Scripts\python.exe -u docs\handoff\sat-tooling\probe_measure.py` (ghi vào `raw_measure.txt`).

```
baseline rss/peak MB: (19.84512, 19.84512)
t_encode=1.173s clauses=196900 tracemalloc_peak_MB=25.60
rss after encode MB (ws, peak): (48.5376, 129.007616)
t_load (solver build/add clauses)=0.191s rss with solver alive MB (ws, peak): (94.12608, 129.007616)
t_solve=0.006s result=True stats={'restarts': 0, 'conflicts': 0, 'decisions': 0, 'propagations': 0}
rss after solve MB (ws, peak): (97.550336, 129.007616)
rss after delete MB (ws, peak): (49.491968, 129.007616)
```

Lần chạy `check_pysat.py` cho `t_encode=1.297s` (seqcounter n=2000 k=50, 196 900 mệnh đề, `py_heap_peak=25.60MB`), `cadical195 load=0.213s solve=0.007s result=True`.

## Chưa kiểm

- Binary kissat ngoài và tìm kiếm toàn ổ đĩa.
- Nguyên nhân budget bị bỏ qua giữa các lần giải.
- Nguồn đỉnh working set 129.0 MB.
- Lệnh gây crash cụ thể trong `kissat404` budget/interrupt.
- Gói `gurobipy`, `cplex`, `docplex` không có trong venv (chỉ xác nhận không có, không cài).
