"""Exact ABP formulation with DOcplex CP Optimizer."""
from __future__ import annotations
from time import perf_counter

from src.common.models import Config, Instance, Result
from src.common.verify import verify


def solve_cplex_cp(instance: Instance, config: Config | None = None) -> Result:
    if config is None:
        config = Config(method="cplex_cp")
    start = perf_counter()
    try:
        from docplex.cp.model import CpoModel

        n = instance.n
        if n < 2 or not instance.edges:
            raise ValueError("ABP cần ít nhất 2 đỉnh và một cạnh.")
        for u, v in instance.edges:
            if not (0 <= u < n and 0 <= v < n) or u == v:
                raise ValueError(f"Cạnh không hợp lệ: ({u}, {v}).")

        encode_start = perf_counter()
        model = CpoModel(name="ABP_CPLEX_CP")
        x = [model.integer_var(min=1, max=n, name=f"x_{v}") for v in range(n)]
        k = model.integer_var(min=1, max=n - 1, name="K")
        model.add(model.all_diff(x))
        for u, v in instance.edges:
            model.add(model.abs(x[u] - x[v]) >= k)
        model.maximize(k)
        t_encode = perf_counter() - encode_start

        params = {"Workers": 1, "LogVerbosity": "Quiet"}
        if config.time_limit is not None:
            if config.time_limit <= 0:
                raise ValueError("time_limit phải lớn hơn 0.")
            params["TimeLimit"] = float(config.time_limit)
        solve_start = perf_counter()
        solved = model.solve(**params)
        t_solve = perf_counter() - solve_start
        if solved is None:
            return Result(status="ERR", t_encode=t_encode, t_solve=t_solve,
                          t_total=perf_counter() - start,
                          metadata={"solver": "CPLEX CP", "error": "CP Optimizer không trả kết quả."})

        status_text = str(solved.get_solve_status())
        norm = status_text.lower()
        try:
            labeling = {v: int(solved.get_var_solution(x[v]).get_value()) for v in range(n)}
            objective = verify(instance, labeling)
            has_solution = True
        except Exception:
            labeling, objective, has_solution = None, None, False

        if not has_solution:
            st = "MO" if "mem" in norm else ("TO" if any(s in norm for s in ("unknown", "stopped", "limit")) else "ERR")
            return Result(status=st, ub=n - 1 if st == "TO" else None,
                          t_encode=t_encode, t_solve=t_solve, t_total=perf_counter() - start,
                          metadata={"solver": "CPLEX CP", "solve_status": status_text,
                                    "error": None if st in ("TO", "MO") else status_text})

        if "optimal" in norm:
            st, lb_val, ub_val = "OPT", objective, objective
        else:
            # Preserve incumbent on stop; classify memory exhaustion as MO.
            st = "MO" if "mem" in norm else "FEAS"
            lb_val, ub_val = objective, n - 1
            try:
                bounds = solved.get_objective_bounds()
                if bounds:
                    # For maximization this API returns the best objective bound.
                    import math
                    ub_val = min(n - 1, max(objective, int(math.ceil(float(bounds[0]) - 1e-8))))
            except Exception:
                pass
        return Result(status=st, lb=lb_val, ub=ub_val, gap=float(max(0, ub_val - lb_val)),
                      t_encode=t_encode, t_solve=t_solve, t_total=perf_counter() - start,
                      variables=n + 1, clauses=None, solution=labeling,
                      metadata={"solver": "CPLEX CP", "solve_status": status_text,
                                "objective_verified": objective})
    except MemoryError as exc:
        return Result(status="MO", t_total=perf_counter() - start,
                      metadata={"solver": "CPLEX CP", "error": f"MemoryError: {exc}"})
    except Exception as exc:
        return Result(status="ERR", t_total=perf_counter() - start,
                      metadata={"solver": "CPLEX CP", "error": f"{type(exc).__name__}: {exc}"})
