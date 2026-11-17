"""Timeout behavior on a hard instance (PHP 10 pigeons, 9 holes; kissat excluded, see probe_kissat.py). PySAT only.

Run: .venv\\Scripts\\python.exe -u docs\\handoff\\sat-tooling\\probe_timeout.py
"""
import itertools
import threading
import time

from pysat.solvers import Solver


def php(p, h):
    var = lambda i, j: i * h + j + 1
    cls = [[var(i, j) for j in range(h)] for i in range(p)]
    for j in range(h):
        for i1, i2 in itertools.combinations(range(p), 2):
            cls.append([-var(i1, j), -var(i2, j)])
    return cls


HARD = php(10, 9)
NAMES = ["minisat22", "glucose4", "maplesat", "cadical195", "lingeling"]

print("== conf_budget(2000): result None means UNKNOWN")
for name in NAMES:
    try:
        with Solver(name=name, bootstrap_with=HARD) as s:
            s.conf_budget(2000)
            t0 = time.perf_counter()
            r = s.solve_limited()
            print(f"{name:12s} budget result={r} t={time.perf_counter() - t0:.3f}s")
    except Exception as e:
        print(f"{name:12s} budget ERR {type(e).__name__}: {str(e)[:100]}")

print("== prop_budget(20000)")
for name in NAMES:
    try:
        with Solver(name=name, bootstrap_with=HARD) as s:
            s.prop_budget(20000)
            r = s.solve_limited()
            print(f"{name:12s} prop budget result={r}")
    except Exception as e:
        print(f"{name:12s} prop ERR {type(e).__name__}: {str(e)[:100]}")

print("== interrupt from Timer after 0.5s, solve_limited(expect_interrupt=True)")
for name in NAMES:
    try:
        with Solver(name=name, bootstrap_with=HARD) as s:
            t = threading.Timer(0.5, s.interrupt)
            t.start()
            t0 = time.perf_counter()
            r = s.solve_limited(expect_interrupt=True)
            dt = time.perf_counter() - t0
            t.join()
            print(f"{name:12s} interrupt result={r} t={dt:.3f}s")
    except Exception as e:
        print(f"{name:12s} interrupt ERR {type(e).__name__}: {str(e)[:100]}")

