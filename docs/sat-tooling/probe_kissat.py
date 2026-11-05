"""Kissat via PySAT name kissat404. One probe per process: kissat may abort the process.

Run: .venv\\Scripts\\python.exe -u docs\\handoff\\sat-tooling\\probe_kissat.py <probe>
probes: solve | assumptions | add_after_solve | budget | interrupt
"""
import sys
import threading
import itertools
import time
import warnings

from pysat.solvers import Solver

SAT = [[1, 2], [-1, 2], [1, -2]]  # unique model x1=x2=1
PROBE = sys.argv[1]


def php(p, h):
    var = lambda i, j: i * h + j + 1
    cls = [[var(i, j) for j in range(h)] for i in range(p)]
    for j in range(h):
        for i1, i2 in itertools.combinations(range(p), 2):
            cls.append([-var(i1, j), -var(i2, j)])
    return cls


if PROBE == "solve":
    with Solver(name="kissat404", bootstrap_with=SAT) as s:
        r = s.solve()
        print("solve ->", r, "model", s.get_model())

elif PROBE == "assumptions":
    # clauses force x1=1 or x2=1; assumption -1 and -2 together is UNSAT
    with Solver(name="kissat404", bootstrap_with=SAT) as s:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            r = s.solve(assumptions=[-1, -2])
        print("solve(assumptions=[-1,-2]) ->", r, "expected False (UNSAT)")
        print("warnings:", [str(x.message)[:80] for x in w])
        print("supports incremental list:", type(s).__name__)

elif PROBE == "add_after_solve":
    with Solver(name="kissat404", bootstrap_with=SAT) as s:
        print("first solve ->", s.solve(), flush=True)
        s.add_clause([3])
        print("added clause, solving again", flush=True)
        print("second solve ->", s.solve(), flush=True)

elif PROBE == "budget":
    with Solver(name="kissat404", bootstrap_with=php(10, 9)) as s:
        try:
            s.conf_budget(2000)
            print("conf_budget ->", s.solve_limited(), flush=True)
        except Exception as e:
            print("conf_budget ERR", type(e).__name__, str(e)[:120], flush=True)
        try:
            s.prop_budget(20000)
            print("prop_budget ->", s.solve_limited(), flush=True)
        except Exception as e:
            print("prop_budget ERR", type(e).__name__, str(e)[:120], flush=True)

elif PROBE == "interrupt":
    with Solver(name="kissat404", bootstrap_with=php(10, 9)) as s:
        t = threading.Timer(0.5, s.interrupt)
        try:
            t.start()
            t0 = time.perf_counter()
            r = s.solve_limited(expect_interrupt=True)
            print("interrupt ->", r, f"t={time.perf_counter() - t0:.3f}s", flush=True)
        except Exception as e:
            print("interrupt ERR", type(e).__name__, str(e)[:120], flush=True)
        t.join()
else:
    raise SystemExit("unknown probe")
