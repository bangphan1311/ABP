"""Does a conf_budget on one solver instance affect a later instance? PySAT only.

Run: .venv\\Scripts\\python.exe -u docs\\handoff\\sat-tooling\\probe_budget_isolation.py
"""
import itertools
import sys

from pysat.solvers import Solver


def php(p, h):
    var = lambda i, j: i * h + j + 1
    cls = [[var(i, j) for j in range(h)] for i in range(p)]
    for j in range(h):
        for i1, i2 in itertools.combinations(range(p), 2):
            cls.append([-var(i1, j), -var(i2, j)])
    return cls


HARD = php(10, 9)
NAME = sys.argv[1] if len(sys.argv) > 1 else "minisat22"
for trial in range(3):
    with Solver(name=NAME, bootstrap_with=HARD) as s:
        s.conf_budget(2000)
        r = s.solve_limited()
        print(f"trial {trial} alone: conf_budget=2000 -> {r}, conflicts={s.accum_stats()['conflicts']}")

with Solver(name=NAME, bootstrap_with=HARD) as a:
    a.conf_budget(2000)
    ra = a.solve_limited()
    print("A (budget 2000) ->", ra, a.accum_stats()["conflicts"])
with Solver(name=NAME, bootstrap_with=HARD) as b:
    b.conf_budget(2000)
    rb = b.solve_limited()
    print("B (budget 2000, after A) ->", rb, b.accum_stats()["conflicts"])

