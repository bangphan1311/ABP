
"""Prototype CP-SAT cho bài toán Antibandwidth Problem."""

from math import ceil, isfinite
from time import perf_counter

from ortools.sat.python import cp_model

from src.common.models import Config, Instance, Result
from src.common.verify import verify

def _safe_upper_bound(status_code: int, best_bound: float, n: int) -> int:
    """Return a safe integer upper bound for the ABP objective."""
    if status_code == cp_model.UNKNOWN or not isfinite(best_bound):
        return n - 1

    return min(n - 1, max(0, ceil(best_bound - 1e-6)))


def solve_cp_sat(instance: Instance, config: Config | None = None) -> Result:
    """Giải ABP bằng CP-SAT và trả về Result dùng chung."""

    if config is None:
        config = Config(method="cp_sat")

    if instance.n < 1:
        raise ValueError("Đồ thị phải có ít nhất một đỉnh.")

    if not instance.edges:
        raise ValueError("Đồ thị phải có ít nhất một cạnh.")

    n = instance.n

    for u, v in instance.edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"Cạnh ({u}, {v}) chứa đỉnh không hợp lệ.")

    start_total = perf_counter()

    # 1. Xây dựng mô hình
    start_encode = perf_counter()
    model = cp_model.CpModel()

    # x[v] là nhãn của đỉnh v, nằm trong [1, n].
    x = [
        model.new_int_var(1, n, f"x_{v}")
        for v in range(n)
    ]

    # Mỗi đỉnh nhận một nhãn khác nhau.
    model.add_all_different(x)

    # K là antibandwidth cần cực đại hóa.
    k = model.new_int_var(0, n - 1, "antibandwidth")

    # Với mọi cạnh (u, v):
    # |x[u] - x[v]| >= K.
    for u, v in instance.edges:
        distance = model.new_int_var(0, n - 1, f"dist_{u}_{v}")
        model.add_abs_equality(distance, x[u] - x[v])
        model.add(k <= distance)

    model.maximize(k)
    t_encode = perf_counter() - start_encode

    # 2. Chạy solver
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = config.seed

    if config.time_limit is not None:
        if config.time_limit <= 0:
            raise ValueError("time_limit phải lớn hơn 0.")
        solver.parameters.max_time_in_seconds = config.time_limit

    status_code = solver.solve(model)
    t_solve = solver.wall_time

    # Lấy cận trên nguyên cho bài toán tối đa hóa.
    best_bound = solver.best_objective_bound
    ub = _safe_upper_bound(status_code, best_bound, n)

    if (
        status_code == cp_model.UNKNOWN
        or not isfinite(best_bound)
    ):
        # Chưa có bound đáng tin cậy: dùng cận trên tự nhiên của ABP.
        ub = n - 1
    else:
        ub = min(n - 1, max(0, ceil(best_bound - 1e-6)))

    status_name = solver.status_name(status_code)
    labeling = None
    objective = None

    if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        labeling = {v: solver.value(x[v]) for v in range(n)}

        # Không nhận nghiệm nếu kiểm chứng thất bại.
        objective = verify(instance, labeling)

        reported_objective = round(solver.objective_value)
        if objective != reported_objective:
            return Result(
                status="ERR",
                t_encode=t_encode,
                t_solve=t_solve,
                t_total=perf_counter() - start_total,
                metadata={
                    "solver": "CP-SAT",
                    "error": "Objective không khớp verify().",
                    "cp_status": status_name,
                },
            )

    t_total = perf_counter() - start_total

    # 3. Chuẩn hóa trạng thái và kết quả
    if status_code == cp_model.OPTIMAL:
        status = "OPT"
        lb = objective
        ub = objective
    elif status_code == cp_model.FEASIBLE:
        status = "FEAS"
        lb = objective
    elif status_code == cp_model.UNKNOWN:
        status = "TO"
        lb = None
        labeling = None
    else:
        # Với ABP hợp lệ, INFEASIBLE là bất thường;
        # MODEL_INVALID cũng là lỗi mô hình.
        return Result(
            status="ERR",
            t_encode=t_encode,
            t_solve=t_solve,
            t_total=t_total,
            variables=len(model.proto.variables),
            clauses=None,
            metadata={
                "solver": "CP-SAT",
                "cp_status": status_name,
                "error": "Solver trả về trạng thái không mong đợi.",
            },
        )

    gap = None if lb is None else max(0.0, float(ub - lb))

    return Result(
        status=status,
        lb=lb,
        ub=ub,
        gap=gap,
        t_encode=t_encode,
        t_solve=t_solve,
        t_total=t_total,
        variables=len(model.proto.variables),
        clauses=None,
        solution=labeling,
        metadata={
            "solver": "CP-SAT",
            "cp_status": status_name,
            "best_objective_bound": best_bound,
        },
    )
