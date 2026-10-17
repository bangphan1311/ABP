"""Check that the returned model satisfies the clauses, for kissat404 vs cadical195. PySAT only.

Run: .venv\\Scripts\\python.exe -u docs\\handoff\\sat-tooling\\probe_kissat_model.py <solver>
Each run is one solver; kissat may abort the process on later calls, so run it alone.
"""
import random
import sys

from pysat.solvers import Solver

NAME = sys.argv[1]
SAT = [[1, 2], [-1, 2], [1, -2]]


def satisfies(model, clauses):
    lits = set(model)
    return all(any(l in lits for l in c) for c in clauses)


print("hand-made instance, model:", end=" ")
with Solver(name=NAME, bootstrap_with=SAT) as s:
    r = s.solve()
    m = s.get_model()
    print(r, m, "satisfies:", satisfies(m, SAT) if r else None)

random.seed(1)
bad = 0
total = 0
for trial in range(30):
    nv, nc = 20, 60
    cls = [[random.choice([-1, 1]) * v for v in random.sample(range(1, nv + 1), 3)] for _ in range(nc)]
    with Solver(name=NAME, bootstrap_with=cls) as s:
        r = s.solve()
        if r:
            total += 1
            if not satisfies(s.get_model(), cls):
                bad += 1
print(f"random 3-SAT nv=20 nc=60: SAT results={total}, models violating clauses={bad}")
