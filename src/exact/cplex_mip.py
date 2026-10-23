"""Exact ABP formulation with CPLEX MIP indicator constraints."""
from __future__ import annotations
from math import ceil
from time import perf_counter

from src.common.models import Config, Instance, Result
from src.common.verify import verify
from src.exact.common import validate_exact_input, warn_ignored_config
def _is_proven_optimal(status_constants, code):
    exact_codes = {
        getattr(status_constants, name)
        for name in ("optimal", "MIP_optimal")
        if hasattr(status_constants, name)
    }
    return code in exact_codes

def solve_cplex_mip(instance: Instance, config: Config | None = None) -> Result:
    if config is None:
        config = Config(method="cplex_mip")
    validate_exact_input(instance, config)
    warn_ignored_config(config, supported=("seed",))
    start = perf_counter()
        import cplex

        n = instance.n
        if n < 2 or not instance.edges:
            raise ValueError("ABP cần ít nhất 2 đỉnh và một cạnh.")
        for u, v in instance.edges:
            if not (0 <= u < n and 0 <= v < n) or u == v:
                raise ValueError(f"Cạnh không hợp lệ: ({u}, {v}).")

        encode_start = perf_counter()
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        pair_start = n + 1
        edge_start = pair_start + len(pairs)
        k_idx = n
        total = edge_start + len(instance.edges)
        model = cplex.Cplex()
        model.set_log_stream(None)
        model.set_error_stream(None)
        model.set_warning_stream(None)
        model.set_results_stream(None)
        model.objective.set_sense(model.objective.sense.maximize)
        model.parameters.mip.tolerances.mipgap.set(0.0)
        model.parameters.mip.tolerances.absmipgap.set(0.0)
        types = [model.variables.type.integer] * (n + 1) + [model.variables.type.binary] * (len(pairs) + len(instance.edges))
        lb = [1] * n + [1] + [0] * (total - n - 1)
        ub = [n] * n + [n - 1] + [1] * (total - n - 1)
        obj = [0] * n + [1] + [0] * (total - n - 1)
        names = [f"x_{i}" for i in range(n)] + ["K"]
        names += [f"ord_{i}_{j}" for i, j in pairs]
        names += [f"dir_{e}" for e in range(len(instance.edges))]
        model.variables.add(obj=obj, lb=lb, ub=ub, types=types, names=names)

        if config.time_limit is not None:
            if config.time_limit <= 0:
                raise ValueError("time_limit phải lớn hơn 0.")
            model.parameters.timelimit.set(float(config.time_limit))
        model.parameters.threads.set(1)
        try:
            model.parameters.randomseed.set(max(0, int(config.seed)))
        except Exception:
            pass

        # Pairwise orientation: mỗi cặp đỉnh có nhãn khác nhau.
        for offset, (i, j) in enumerate(pairs):
            z = pair_start + offset
            model.indicator_constraints.add(
                indvar=z, complemented=0,
                lin_expr=cplex.SparsePair(ind=[i, j], val=[1.0, -1.0]),
                sense="L", rhs=-1.0, name=f"ord_a_{i}_{j}")  # z=1 -> x_i < x_j
            model.indicator_constraints.add(
                indvar=z, complemented=1,
                lin_expr=cplex.SparsePair(ind=[j, i], val=[1.0, -1.0]),
                sense="L", rhs=-1.0, name=f"ord_b_{i}_{j}")  # z=0 -> x_j < x_i

        # K <= |x_u-x_v|: biến nhị phân chọn hướng của mỗi cạnh.
        for e, (u, v) in enumerate(instance.edges):
            y = edge_start + e
            model.indicator_constraints.add(
                indvar=y, complemented=0,
                lin_expr=cplex.SparsePair(ind=[u, v, k_idx], val=[1.0, -1.0, -1.0]),
                sense="G", rhs=0.0, name=f"edge_a_{e}")
            model.indicator_constraints.add(
                indvar=y, complemented=1,
                lin_expr=cplex.SparsePair(ind=[v, u, k_idx], val=[1.0, -1.0, -1.0]),
                sense="G", rhs=0.0, name=f"edge_b_{e}")

        t_encode = perf_counter() - encode_start
        solve_start = perf_counter()
        model.solve()
        t_solve = perf_counter() - solve_start
        code = model.solution.get_status()
        status_text = model.solution.get_status_string()
        has_solution = model.solution.is_primal_feasible()
        status_constants = model.solution.status
        status_norm = status_text.lower()
        if not has_solution:
            if "memory" in status_norm or "out of memory" in status_norm:
                st = "MO"
            elif "time limit" in status_norm:
                st = "TO"
            else:
                st = "ERR"
            return Result(status=st, ub=n - 1 if st in ("TO", "MO") else None,
                          t_encode=t_encode, t_solve=t_solve, t_total=perf_counter() - start,
                          metadata={"solver": "CPLEX MIP", "cplex_status": code,
                                    "status_text": status_text,
                                    "error": None if st in ("TO", "MO") else status_text})

        values = model.solution.get_values(list(range(n)))
        labeling = {v: int(round(values[v])) for v in range(n)}
        objective = verify(instance, labeling)
        model_objective = int(round(model.solution.get_objective_value()))
        if objective != model_objective:
            return Result(status="ERR", t_encode=t_encode, t_solve=t_solve,
                          t_total=perf_counter() - start,
                          metadata={"solver": "CPLEX MIP",
                                    "error": f"Objective native={model_objective} khác verify={objective}.",
                                    "model_objective": model_objective,
                                    "objective_verified": objective})
        optimal = _is_proven_optimal(status_constants, code)
        if optimal:
            st, lb_val, ub_val = "OPT", objective, objective
        else:
            # Preserve the verified incumbent and upper bound if search stops early.
            st = "MO" if ("memory" in status_norm or "out of memory" in status_norm) else "FEAS"
            lb_val, ub_val = objective, n - 1
            try:
                best_bound = float(model.solution.MIP.get_best_objective())
                ub_val = min(n - 1, max(objective, int(ceil(best_bound - 1e-8))))
            except Exception:
                pass
        return Result(status=st, lb=lb_val, ub=ub_val, gap=float(max(0, ub_val - lb_val)),
                      t_encode=t_encode, t_solve=t_solve, t_total=perf_counter() - start,
                      variables=total, clauses=None, solution=labeling,
                      metadata={"solver": "CPLEX MIP", "cplex_status": code,
                                "status_text": status_text, "model_objective": model_objective, "objective_verified": objective})
    except MemoryError as exc:
        return Result(status="MO", t_total=perf_counter() - start,
                      metadata={"solver": "CPLEX MIP", "error": f"MemoryError: {exc}"})
    except Exception as exc:
        return Result(status="ERR", t_total=perf_counter() - start,
                      metadata={"solver": "CPLEX MIP", "error": f"{type(exc).__name__}: {exc}"})
