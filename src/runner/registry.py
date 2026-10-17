"""Registry: tên method -> hàm solver (Instance, Config) -> Result.

Import lazy để máy thiếu một solver hoặc license vẫn chạy được
các method còn lại.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable

from src.common.models import Config, Instance, Result

SolverFn = Callable[[Instance, Config], Result]

METHODS: dict[str, str] = {
    "oracle": "src.runner.registry:_oracle_adapter",
    "cp_sat": "src.exact.cp_sat_solver:solve_cp_sat",
    "sat": "src.sat.solve:solve_sat",
    "gurobi_mip": "src.exact.gurobi_mip:solve_gurobi_mip",
    "cplex_mip": "src.exact.cplex_mip:solve_cplex_mip",
    "cplex_cp": "src.exact.cplex_cp:solve_cplex_cp",
}


def _oracle_adapter(instance: Instance, config: Config) -> Result:
    """solve_oracle không nhận Config nên cần adapter."""
    from src.exact.oracle import solve_oracle

    return solve_oracle(instance)


def resolve(method: str) -> SolverFn:
    spec = METHODS.get(method, method)

    if ":" not in spec:
        raise ValueError(
            f"Method '{method}' không có trong registry. "
            f"Hợp lệ: {sorted(METHODS)}."
        )

    module_name, func_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, func_name)