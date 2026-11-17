"""Probe installed PySAT only. No project code is imported.

Run: .venv\\Scripts\\python.exe docs\\handoff\\sat-tooling\\check_pysat.py
"""
import itertools
import threading
import time
import tracemalloc

import pysat
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver, SolverNames

print("== version")
print("pysat.__version__", pysat.__version__)

print("== AMO/card encodings: n=6 lits, check every assignment against sum<=bound")
N = 6
ENC_NAMES = [n for n in vars(EncType) if not n.startswith("_")]
for enc_name in ENC_NAMES:
    for bound in (1, 2, 3):
        try:
            cnf = CardEnc.atmost(lits=list(range(1, N + 1)), bound=bound,
                                 top_id=N, encoding=getattr(EncType, enc_name))
        except Exception as e:  # record, do not hide
            print(f"{enc_name:12s} bound={bound} ERROR {type(e).__name__}: {e}")
            continue
        ok = True
        with Solver(name="cadical195", bootstrap_with=cnf.clauses) as s:
            for bits in itertools.product([0, 1], repeat=N):
                assum = [(i + 1) if b else -(i + 1) for i, b in enumerate(bits)]
                got = s.solve(assumptions=assum)
                want = sum(bits) <= bound
                if got != want:
                    ok = False
                    break
        print(f"{enc_name:12s} bound={bound} clauses={len(cnf.clauses)} "
              f"top_id={cnf.nv} semantic_ok={ok}")

def _safe_interrupt(s):
    try:
        s.interrupt()
    except NotImplementedError as e:
        print("interrupt NotImplementedError:", e)


print("== solver names, incremental / assumptions / budget / interrupt")
SAT_CLAUSES = [[1, 2], [-1, 2], [1, -2]]  # sat, model x1=x2=1
seen = set()
for name in sorted(vars(SolverNames)):
    if name.startswith("_") or name.startswith("kissat") or name in ("ks", "ks4", "kissat", "kissat4"):
        continue
    try:
        s = Solver(name=name, bootstrap_with=SAT_CLAUSES)
    except Exception as e:
        print(f"{name:12s} CTOR ERROR {type(e).__name__}: {e}")
        continue
    row = {}
    try:
        row["solve"] = s.solve()
        row["model"] = s.get_model() is not None
    except Exception as e:
        row["solve"] = f"ERR {type(e).__name__}: {e}"
    try:
        row["assumptions"] = s.solve(assumptions=[-1, -2])  # expect False
        row["core"] = s.get_core()
    except Exception as e:
        row["assumptions"] = f"ERR {type(e).__name__}: {str(e)[:60]}"
    try:
        s.add_clause([3])  # add after solve = incremental
        row["incremental_add"] = s.solve()
    except Exception as e:
        row["incremental_add"] = f"ERR {type(e).__name__}: {str(e)[:60]}"
    try:
        s.conf_budget(0)
        row["conf_budget0"] = s.solve_limited()
    except Exception as e:
        row["conf_budget0"] = f"ERR {type(e).__name__}: {str(e)[:60]}"
    try:
        s.conf_budget(-1)
        t = threading.Timer(0.0, _safe_interrupt, args=(s,))
        t.start()
        row["interrupt"] = s.solve_limited(expect_interrupt=True)
        t.join()
    except Exception as e:
        row["interrupt"] = f"ERR {type(e).__name__}: {str(e)[:60]}"
    print(name, row)
    s.delete()

print("== UNKNOWN via conf_budget on pigeonhole PHP(11,10) with minisat22 and cadical195")
def php(p, h):
    var = lambda i, j: i * h + j + 1
    cls = [[var(i, j) for j in range(h)] for i in range(p)]
    for j in range(h):
        for i1, i2 in itertools.combinations(range(p), 2):
            cls.append([-var(i1, j), -var(i2, j)])
    return cls
PHP = php(11, 10)
for name in ("minisat22", "cadical195"):
    with Solver(name=name, bootstrap_with=PHP) as s:
        s.conf_budget(200)
        t0 = time.perf_counter()
        r = s.solve_limited()
        print(name, "conf_budget=200 ->", r, f"{time.perf_counter() - t0:.3f}s")
        print(name, "accum_stats", s.accum_stats())

print("== t_encode vs t_solve vs memory: measurement primitives")
tracemalloc.start()
t0 = time.perf_counter()
cnf = CardEnc.atmost(lits=list(range(1, 2001)), bound=50, top_id=2000,
                     encoding=EncType.seqcounter)
t_enc = time.perf_counter() - t0
cur, peak = tracemalloc.get_traced_memory()
print(f"encode seqcounter n=2000 k=50 clauses={len(cnf.clauses)} t_encode={t_enc:.3f}s "
      f"py_heap_peak={peak/1e6:.2f}MB")
tracemalloc.stop()
t0 = time.perf_counter()
with Solver(name="cadical195", bootstrap_with=cnf.clauses) as s:
    t_load = time.perf_counter() - t0
    t0 = time.perf_counter()
    r = s.solve()
    t_solve = time.perf_counter() - t0
print(f"cadical195 load={t_load:.3f}s solve={t_solve:.3f}s result={r}")


