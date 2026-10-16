"""Check whether a budgeted solve that returns False is UNSAT or budget noise.

Run: .venv\\Scripts\\python.exe -u docs\\handoff\\sat-tooling\\probe_budget_check.py
"""
import itertools
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
for name in ("minisat22", "glucose4", "maplesat"):
    with Solver(name=name, bootstrap_with=HARD) as s:
        s.prop_budget(20000)
        r = s.solve_limited()
        print(name, "prop_budget=20000 ->", r, s.accum_stats())
    with Solver(name=name, bootstrap_with=HARD) as s:
        s.conf_budget(2000)
        r = s.solve_limited()
        print(name, "conf_budget=2000 ->", r, s.accum_stats())
    with Solver(name=name, bootstrap_with=HARD) as s:
        t0 = time.perf_counter()
        r = s.solve()
        print(name, "unlimited solve ->", r, f"t={time.perf_counter() - t0:.3f}s", s.accum_stats())
