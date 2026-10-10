import time

def mip_gurobi(n):
    import gurobipy as gp
    from gurobipy import GRB
    m = gp.Model(); m.Params.OutputFlag = 0
    x = m.addVars(n, vtype=GRB.BINARY)
    for i in range(n - 1):
        m.addConstr(x[i] + x[i + 1] <= 1)
    m.setObjective(gp.quicksum(x.values()), GRB.MAXIMIZE)
    m.optimize()
    return m.Status

def mip_cplex(n):
    from docplex.mp.model import Model
    m = Model()
    x = m.binary_var_list(n)
    for i in range(n - 1):
        m.add_constraint(x[i] + x[i + 1] <= 1)
    m.maximize(m.sum(x))
    s = m.solve()
    return "solved" if s else "no solution"

def cp_cplex(n):
    from docplex.cp.model import CpoModel
    m = CpoModel()
    x = [m.integer_var(0, 1) for _ in range(n)]
    for i in range(n - 1):
        m.add(x[i] + x[i + 1] <= 1)
    m.add(m.maximize(sum(x)))
    r = m.solve(LogVerbosity="Quiet", TimeLimit=30)
    return r.get_solve_status()

def cpsat(n):
    from ortools.sat.python import cp_model
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{i}") for i in range(n)]
    for i in range(n - 1):
        m.Add(x[i] + x[i + 1] <= 1)
    m.Maximize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 30
    return s.StatusName(s.Solve(m))

for name, fn in [("Gurobi", mip_gurobi), ("CPLEX MIP", mip_cplex),
                 ("CPLEX CP", cp_cplex), ("CP-SAT", cpsat)]:
    print(f"--- {name}")
    for n in (500, 1500, 3000, 10000):
        t = time.time()
        try:
            res = fn(n)
            print(f"  n={n:>6}: OK   {res} ({time.time()-t:.1f}s)")
        except Exception as e:
            print(f"  n={n:>6}: FAIL {type(e).__name__}: {str(e)[:150]}")
