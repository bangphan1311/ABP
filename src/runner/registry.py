"""Registry: tên method -> hàm solver ``(Instance, Config) -> Result``.

Import lazy để máy thiếu một solver (ví dụ chưa có license CPLEX) vẫn chạy được
các method còn lại. Thêm solver mới (W2: gurobi, cplex_mip, cplex_cp) chỉ cần
thêm một dòng vào ``METHODS``.

``method`` cũng có thể là ``"package.module:function"`` (dùng cho test).
"""

from __future__ import annotations

import importlib
from collections.abc import Callable

from src.common.models import Config, Instance, Result

SolverFn = Callable[[Instance, Config], Result]

# method -> "module:function". Hàm phải nhận (instance, config).
METHODS: dict[str, str] = {
    "oracle": "src.runner.registry:_oracle_adapter",
    "cp_sat": "src.exact.cp_sat_solver:solve_cp_sat",
    "sat": "src.sat.solve:solve_sat",
    # W2: "gurobi", "cplex_mip", "cplex_cp"
}


def _oracle_adapter(instance: Instance, config: Config) -> Result:
    """solve_oracle(instance, max_n) không nhận Config nên cần adapter."""
    from src.exact.oracle import solve_oracle

    return solve_oracle(instance)


def resolve(method: str) -> SolverFn:
    spec = METHODS.get(method, method)
    if ":" not in spec:
        raise ValueError(
            f"Method '{method}' không có trong registry. Hợp lệ: {sorted(METHODS)}."
        )
    module_name, func_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, func_name)
