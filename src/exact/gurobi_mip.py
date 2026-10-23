"""Exact ABP formulation with Gurobi MIP and indicator constraints."""
from __future__ import annotations
from math import ceil
from time import perf_counter

from src.common.models import Config, Instance, Result
from src.common.verify import verify
from src.exact.common import validate_exact_input, warn_ignored_config


def solve_gurobi_mip(instance: Instance, config: Config | None = None) -> Result:
    if config is None:
        config = Config(method="gurobi_mip")
    validate_exact_input(instance, config)
    warn_ignored_config(config, supported=("seed",))
    start = perf_counter()
    try:
        import gurobipy as gp
        from gurobipy import GRB

        n = instance.n
        if n < 2 or not instance.edges:
            raise ValueError("ABP cần ít nhất 2 đỉnh và một cạnh.")
        for u, v in instance.edges:
            if not (0 <= u < n and 0 <= v < n) or u == v:
                raise ValueError(f"Cạnh không hợp lệ: ({u}, {v}).")

        encode_start = perf_counter()
        model = gp.Model("ABP_Gurobi_MIP")
        model.Params.OutputFlag = 0
        model.Params.Threads = 1
        model.Params.Seed = max(0, int(config.seed))
        model.Params.MIPGap = 0.0
        if config.time_limit is not None:
            if config.time_limit <= 0:
                raise ValueError("time_limit phải lớn hơn 0.")
            model.Params.TimeLimit = float(config.time_limit)

        x = model.addVars(n, vtype=GRB.INTEGER, lb=1, ub=n, name="x")
        k = model.addVar(vtype=GRB.INTEGER, lb=1, ub=n - 1, name="K")

        # Mỗi cặp đỉnh nhận thứ tự nghiêm ngặt, nên các nhãn là khác nhau.
        for i in range(n):
            for j in range(i + 1, n):
                z = model.addVar(vtype=GRB.BINARY, name=f"ord_{i}_{j}")
                model.addConstr((z == 1) >> (x[i] + 1 <= x[j]))
                model.addConstr((z == 0) >> (x[j] + 1 <= x[i]))

        # Với mỗi cạnh, chọn một trong hai hướng để buộc khoảng cách >= K.
        for e, (u, v) in enumerate(instance.edges):
            y = model.addVar(vtype=GRB.BINARY, name=f"dir_{e}")
            model.addConstr((y == 1) >> (x[u] - x[v] >= k))
            model.addConstr((y == 0) >> (x[v] - x[u] >= k))

        model.setObjective(k, GRB.MAXIMIZE)
        t_encode = perf_counter() - encode_start
        solve_start = perf_counter()
        model.optimize()
        t_solve = perf_counter() - solve_start
        status_code = model.Status
        has_solution = model.SolCount > 0
        bound = getattr(model, "ObjBound", n - 1) if has_solution or status_code == GRB.TIME_LIMIT else n - 1
        ub = min(n - 1, max(1, int(ceil(float(bound) - 1e-8)))) if bound is not None else n - 1

        mem_limit_code = getattr(GRB, "MEM_LIMIT", None)
        if not has_solution:
            if mem_limit_code is not None and status_code == mem_limit_code:
                status = "MO"
            elif status_code == GRB.TIME_LIMIT:
                status = "TO"
            else:
                status = "ERR"
            return Result(status=status, ub=ub if status in ("TO", "MO") else None,
                          t_encode=t_encode, t_solve=t_solve,
                          t_total=perf_counter() - start,
                          metadata={"solver": "Gurobi MIP", "gurobi_status": int(status_code),
                                    "error": None if status in ("TO", "MO") else "Solver kết thúc mà không có nghiệm."})

        labeling = {v: int(round(x[v].X)) for v in range(n)}
        objective = verify(instance, labeling)
        model_objective = int(round(model.ObjVal))
        if objective != model_objective:
            return Result(status="ERR", t_encode=t_encode, t_solve=t_solve,
                          t_total=perf_counter() - start,
                          metadata={"solver": "Gurobi MIP",
                                    "error": f"Objective native={model_objective} khác verify={objective}.",
                                    "model_objective": model_objective,
                                    "objective_verified": objective})
        if status_code == GRB.OPTIMAL:
            status, lb, ub = "OPT", objective, objective
        elif mem_limit_code is not None and status_code == mem_limit_code:
            status, lb = "MO", objective
            ub = max(lb, ub)
        else:
            # TIME_LIMIT with a verified incumbent is FEAS, not TO.
            status, lb = "FEAS", objective
            ub = max(lb, ub)
        return Result(status=status, lb=lb, ub=ub, gap=float(max(0, ub - lb)),
                      t_encode=t_encode, t_solve=t_solve, t_total=perf_counter() - start,
                      variables=model.NumVars, clauses=None, solution=labeling,
                      metadata={"solver": "Gurobi MIP", "gurobi_status": int(status_code),
                                "model_objective": model_objective,
                                "objective_verified": objective})
    except MemoryError as exc:
        return Result(status="MO", t_total=perf_counter() - start,
                      metadata={"solver": "Gurobi MIP", "error": f"MemoryError: {exc}"})
    except Exception as exc:
        return Result(status="ERR", t_total=perf_counter() - start,
                      metadata={"solver": "Gurobi MIP", "error": f"{type(exc).__name__}: {exc}"})
