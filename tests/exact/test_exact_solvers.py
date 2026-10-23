"""Small-instance exactness checks for the W2 exact solvers.

Run from the repository root:
    python -m pytest tests/exact/test_exact_solvers.py -q
"""
import importlib.util
import pytest

from src.common.models import Config
from src.common.verify import verify
from src.exact.oracle import solve_oracle
from src.exact.cp_sat_solver import solve_cp_sat
from src.exact.gurobi_mip import solve_gurobi_mip
from src.exact.cplex_mip import solve_cplex_mip
from src.exact.cplex_cp import solve_cplex_cp
from src.sat.generator import path, cycle, complete


INSTANCES = [path(4), cycle(5), complete(5)]
SOLVERS = [
    ("CP-SAT", solve_cp_sat),
    ("Gurobi MIP", solve_gurobi_mip),
    ("CPLEX MIP", solve_cplex_mip),
    ("CPLEX CP", solve_cplex_cp),
]


@pytest.mark.parametrize("instance", INSTANCES, ids=lambda inst: inst.id)
@pytest.mark.parametrize("solver_name,solve", SOLVERS, ids=[s[0] for s in SOLVERS])
def _skip_if_backend_unavailable(solver_name):
    module = {
        "CP-SAT": "ortools",
        "Gurobi MIP": "gurobipy",
        "CPLEX MIP": "cplex",
        "CPLEX CP": "docplex",
    }[solver_name]
    if importlib.util.find_spec(module) is None:
        pytest.skip(f"Optional backend {module} is not installed")


def _is_missing_engine_or_license(result):
    if result.status != "ERR":
        return False
    message = str(result.metadata.get("error", "")).lower()
    markers = (
        "executable file is not found",
        "cpoptimizer.exe",
        "license",
        "licence",
        "no gurobi license",
        "cplex error 1016",
        "cannot open cplex",
        "not available",
    )
    return any(marker in message for marker in markers)


def test_exact_solver_matches_oracle(instance, solver_name, solve):
    _skip_if_backend_unavailable(solver_name)
    expected = solve_oracle(instance)
    result = solve(instance, Config(method=solver_name.lower().replace(" ", "_"), time_limit=30, seed=0))

    if _is_missing_engine_or_license(result):
        pytest.skip(f"{solver_name} engine/license unavailable: {result.metadata}")
    assert result.status == "OPT", f"{solver_name} failed: {result.metadata}"
    assert result.lb == result.ub == expected.lb
    assert result.solution is not None
    assert verify(instance, result.solution) == expected.lb
