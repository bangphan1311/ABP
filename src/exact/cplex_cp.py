"""Exact ABP formulation with DOcplex CP Optimizer."""
from __future__ import annotations

from time import perf_counter

from src.common.models import Config, Instance, Result
from src.common.verify import verify
from src.exact.common import remaining_time_budget, validate_exact_input, warn_ignored_config


def _is_memory_failure(*signals) -> bool:
    """Return True only when the available messages indicate a memory failure."""
    text = " ".join(str(signal) for signal in signals if signal is not None).lower()

    markers = (
        "out of memory",
        "memory exhausted",
        "insufficient memory",
        "memoryerror",
        "memory limit",
        "memlimit",
        "mem_limit",
    )
    return any(marker in text for marker in markers)


def _classify_status(
    solve_status,
    fail_status,
    stop_cause,
    has_solution: bool,
) -> str:
    """Map CP Optimizer outcomes to the project's result contract."""
    solve_text = str(solve_status or "").strip().casefold()
    fail_text = str(fail_status or "").strip().casefold()

    if has_solution:
        if solve_text == "optimal" or solve_text.endswith(".optimal"):
            return "OPT"
        return "FEAS"

    if _is_memory_failure(solve_status, fail_status, stop_cause):
        return "MO"

    if fail_text == "searchstoppedbylimit":
        return "TO"

    return "ERR"


def solve_cplex_cp(
    instance: Instance,
    config: Config | None = None,
) -> Result:
    if config is None:
        config = Config(method="cplex_cp")

    validate_exact_input(instance, config)
    warn_ignored_config(config, supported=())
    start = perf_counter()

    try:
        from docplex.cp.model import CpoModel

        n = instance.n

        if n < 2 or not instance.edges:
            raise ValueError("ABP cần ít nhất 2 đỉnh và một cạnh.")

        for u, v in instance.edges:
            if not (0 <= u < n and 0 <= v < n) or u == v:
                raise ValueError(f"Cạnh không hợp lệ: ({u}, {v}).")

        # Build the CP Optimizer model.
        encode_start = perf_counter()

        model = CpoModel(name="ABP_CPLEX_CP")
        x = [
            model.integer_var(min=1, max=n, name=f"x_{v}")
            for v in range(n)
        ]
        k = model.integer_var(min=1, max=n - 1, name="K")

        model.add(model.all_diff(x))

        for u, v in instance.edges:
            model.add(model.abs(x[u] - x[v]) >= k)

        model.maximize(k)

        t_encode = perf_counter() - encode_start

        # Configure the solver.
        params = {
            "Workers": 1,
            "LogVerbosity": "Quiet",
        }

        if config.time_limit is not None:
            if config.time_limit <= 0:
                raise ValueError("time_limit phải lớn hơn 0.")

            params["TimeLimit"] = float(config.time_limit)

        # Deduct build time from the whole-run budget before starting CP Optimizer.
        remaining = remaining_time_budget(config.time_limit, perf_counter() - start)
        if remaining is not None:
            if remaining <= 0:
                return Result(
                    status="TO", ub=n - 1, t_encode=t_encode, t_solve=0.0,
                    t_total=perf_counter() - start, variables=n + 1, clauses=None,
                    metadata={"solver": "CPLEX CP", "time_budget_exhausted_during_build": True},
                )
            params["TimeLimit"] = remaining

        # Solve the model.
        solve_start = perf_counter()
        solved = model.solve(**params)
        t_solve = perf_counter() - solve_start

        if solved is None:
            return Result(
                status="ERR",
                t_encode=t_encode,
                t_solve=t_solve,
                t_total=perf_counter() - start,
                metadata={
                    "solver": "CPLEX CP",
                    "error": "CP Optimizer không trả kết quả.",
                },
            )

        # Collect the solver's termination information.
        status_text = str(solved.get_solve_status() or "")

        try:
            fail_status = str(solved.get_fail_status() or "")
        except Exception:
            fail_status = ""

        try:
            stop_cause = str(solved.get_stop_cause() or "")
        except Exception:
            stop_cause = ""

        # Extract and independently verify the incumbent.
        try:
            labeling = {
                v: int(solved.get_var_solution(x[v]).get_value())
                for v in range(n)
            }

            objective = verify(instance, labeling)
            has_solution = True

        except Exception:
            labeling = None
            objective = None
            has_solution = False

        # Handle termination without a verified incumbent.
        if not has_solution:
            st = _classify_status(
                status_text,
                fail_status,
                stop_cause,
                has_solution=False,
            )

            return Result(
                status=st,
                ub=n - 1 if st == "TO" else None,
                t_encode=t_encode,
                t_solve=t_solve,
                t_total=perf_counter() - start,
                metadata={
                    "solver": "CPLEX CP",
                    "solve_status": status_text,
                    "fail_status": fail_status,
                    "stop_cause": stop_cause,
                    "error": (
                        None
                        if st in ("TO", "MO")
                        else status_text
                    ),
                },
            )

        try:
            model_objective = int(round(float(solved.get_objective_value())))
        except Exception as exc:
            return Result(
                status="ERR", t_encode=t_encode, t_solve=t_solve,
                t_total=perf_counter() - start,
                metadata={"solver": "CPLEX CP",
                          "error": f"Không đọc được objective native: {type(exc).__name__}: {exc}",
                          "objective_verified": objective},
            )
        if objective != model_objective:
            return Result(
                status="ERR", t_encode=t_encode, t_solve=t_solve,
                t_total=perf_counter() - start,
                metadata={"solver": "CPLEX CP",
                          "error": f"Objective native={model_objective} khác verify={objective}.",
                          "model_objective": model_objective,
                          "objective_verified": objective},
            )

        # A verified incumbent is OPT only when optimality is proven.
        st = _classify_status(
            status_text,
            fail_status,
            stop_cause,
            has_solution=True,
        )

        if st == "OPT":
            lb_val = objective
            ub_val = objective

        else:
            # Keep the verified incumbent without claiming optimality.
            lb_val = objective
            ub_val = n - 1

            try:
                bounds = solved.get_objective_bounds()

                if bounds:
                    import math

                    ub_val = min(
                        n - 1,
                        max(
                            objective,
                            int(
                                math.ceil(
                                    float(bounds[0]) - 1e-8
                                )
                            ),
                        ),
                    )

            except Exception:
                # Use the safe theoretical upper bound if unavailable.
                pass

        return Result(
            status=st,
            lb=lb_val,
            ub=ub_val,
            gap=float(max(0, ub_val - lb_val)),
            t_encode=t_encode,
            t_solve=t_solve,
            t_total=perf_counter() - start,
            variables=n + 1,
            clauses=None,
            solution=labeling,
            metadata={
                "solver": "CPLEX CP",
                "solve_status": status_text,
                "fail_status": fail_status,
                "stop_cause": stop_cause,
                "model_objective": model_objective,
                "objective_verified": objective,
            },
        )

    except MemoryError as exc:
        return Result(
            status="MO",
            t_total=perf_counter() - start,
            metadata={
                "solver": "CPLEX CP",
                "error": f"MemoryError: {exc}",
            },
        )

    except Exception as exc:
        st = (
            "MO"
            if _is_memory_failure(type(exc).__name__, str(exc))
            else "ERR"
        )

        return Result(
            status=st,
            t_total=perf_counter() - start,
            metadata={
                "solver": "CPLEX CP",
                "error": f"{type(exc).__name__}: {exc}",
            },
        )