"""Local machine, package and tiny solver smoke-test snapshot; no secret collection."""
import argparse,importlib.metadata,json,os,platform,shutil,sys

def version(name):
    try: return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError: return None
    except Exception as e: return f"ERROR:{type(e).__name__}"

def probe(name):
    try:
        if name=="CP-SAT":
            from ortools.sat.python import cp_model
            m=cp_model.CpModel(); x=m.new_bool_var("x"); m.add(x==1); s=cp_model.CpSolver()
            s.parameters.num_search_workers=1; st=s.solve(m); ok=st in (cp_model.OPTIMAL,cp_model.FEASIBLE) and s.value(x)==1
        elif name in ("CaDiCaL","Glucose"):
            from pysat.solvers import Solver
            backend="cadical195" if name=="CaDiCaL" else "glucose4"
            with Solver(name=backend,bootstrap_with=[[1]]) as s: ok=s.solve() is True and s.get_model() is not None
            st=backend
        elif name=="Gurobi MIP":
            import gurobipy as gp
            from gurobipy import GRB
            m=gp.Model("preflight_tiny"); m.Params.OutputFlag=0; m.Params.Threads=1; x=m.addVar(vtype=GRB.BINARY)
            m.addConstr(x==1); m.optimize(); st=int(m.Status); ok=st==GRB.OPTIMAL and int(round(x.X))==1; m.dispose()
        elif name=="CPLEX MIP":
            import cplex
            m=cplex.Cplex(); m.set_log_stream(None); m.set_error_stream(None); m.set_warning_stream(None); m.set_results_stream(None)
            m.variables.add(lb=[1],ub=[1],types=[m.variables.type.binary]); m.solve()
            st=m.solution.get_status_string(); ok=m.solution.is_primal_feasible(); m.end()
        elif name=="CPLEX CP":
            from docplex.cp.model import CpoModel
            m=CpoModel(); x=m.integer_var(min=1,max=1); m.add(x==1)
            r=m.solve(TimeLimit=5,LogVerbosity="Quiet"); st=str(r.get_solve_status()) if r else "no result"
            ok=bool(r) and st.lower().endswith("optimal")
        else: return {"status":"NOT_PROBED"}
        return {"status":"PASS" if ok else "FAIL","solver_result":str(st)}
    except Exception as e:
        return {"status":"FAIL","error_type":type(e).__name__,"message":str(e).replace("\n"," ")[:200]}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--probe-solvers",action="store_true"); p.add_argument("--output"); a=p.parse_args()
    pkgs=["ortools","python-sat","pytest","gurobipy","cplex","docplex","psutil"]
    try:
        import psutil
        ram=psutil.virtual_memory().total; ram_gib=round(ram/1024**3,2)
    except Exception: ram=ram_gib=None
    data={"python":{"version":sys.version,"executable":sys.executable},
          "machine":{"os":platform.platform(),"system":platform.system(),"release":platform.release(),
                     "architecture":platform.machine(),"processor":platform.processor() or None,
                     "logical_cpu_count":os.cpu_count(),"total_ram_bytes":ram,"total_ram_gib":ram_gib},
          "packages":{x:version(x) for x in pkgs},
          "executables_on_path":{x:shutil.which(x) for x in ["python","gurobi_cl","cplex","cpoptimizer","kissat"]},
          "solver_probes":"NOT_RUN",
          "notes":["Package import/version is not proof of license or benchmark-size entitlement.",
                   "Never attach license keys, passwords, tokens or a full environment-variable dump.",
                   "Kissat must be tested as a separately validated native binary; do not trust the historical kissat404 PySAT alias."]}
    if a.probe_solvers: data["solver_probes"]={x:probe(x) for x in ["CP-SAT","CaDiCaL","Glucose","Gurobi MIP","CPLEX MIP","CPLEX CP"]}
    text=json.dumps(data,indent=2,ensure_ascii=False)
    if a.output: open(a.output,"w",encoding="utf-8").write(text+"\n")
    else: print(text)

if __name__ == "__main__":
    main()
