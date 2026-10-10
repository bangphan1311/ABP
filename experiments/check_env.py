import sys, platform
print("Python", sys.version.split()[0], "|", platform.platform())

def check(name, fn):
    try:
        print(f"[OK]   {name}: {fn()}")
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {str(e)[:300]}")

def cpsat():
    from ortools.sat.python import cp_model
    m = cp_model.CpModel()
    x = m.NewIntVar(0, 5, "x")
    m.Maximize(x)
    s = cp_model.CpSolver()
    st = s.Solve(m)
    return s.StatusName(st), s.Value(x)

def gurobi():
    import gurobipy as gp
    from gurobipy import GRB
    m = gp.Model()
    m.Params.OutputFlag = 0
    x = m.addVar(vtype=GRB.INTEGER, lb=0, ub=5)
    m.setObjective(x, GRB.MAXIMIZE)
    m.optimize()
    return m.Status, x.X

def cplex_mip():
    from docplex.mp.model import Model
    m = Model()
    x = m.integer_var(0, 5)
    m.maximize(x)
    s = m.solve()
    return s.objective_value

def cplex_cp():
    from docplex.cp.model import CpoModel
    m = CpoModel()
    x = m.integer_var(0, 5)
    m.add(m.maximize(x))
    r = m.solve(LogVerbosity="Quiet", TimeLimit=10)
    return r.get_solve_status(), r.get_objective_values()

check("CP-SAT", cpsat)
check("Gurobi", gurobi)
check("CPLEX MIP", cplex_mip)
check("CPLEX CP", cplex_cp)
