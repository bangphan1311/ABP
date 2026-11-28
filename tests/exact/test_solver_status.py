from types import SimpleNamespace

import pytest

from src.common.models import Config, Instance
from src.exact.cplex_mip import _is_proven_optimal
from src.exact.cplex_cp import _classify_status, _extract_verified_solution
from src.exact.cp_sat_solver import solve_cp_sat


def _path4():
    return Instance(
        id="path4", name="path4", n=4,
        edges=((0, 1), (1, 2), (2, 3)),
        source="unit-test", tier="toy",
    )


def test_exact_optimal_status_is_accepted():
    statuses = SimpleNamespace(optimal=101, MIP_optimal=101, MIP_optimal_tolerance=102)
    assert _is_proven_optimal(statuses, 101)


def test_optimal_tolerance_is_not_exact_optimal():
    statuses = SimpleNamespace(optimal=101, MIP_optimal=101, MIP_optimal_tolerance=102)
    assert not _is_proven_optimal(statuses, 102)


def test_cplex_cp_optimal_with_solution():
    assert _classify_status("Optimal", "", "", has_solution=True) == "OPT"


def test_cplex_cp_feasible_without_optimality_proof():
    assert _classify_status("Feasible", "", "", has_solution=True) == "FEAS"


def test_cplex_cp_memory_stop_with_incumbent_is_mo():
    # The incumbent remains in Result, while status records the termination cause.
    assert _classify_status("Feasible", "", "Out of memory", has_solution=True) == "MO"


def test_cplex_cp_memory_failure_without_solution():
    assert _classify_status("Unknown", "Unknown", "Out of memory", has_solution=False) == "MO"


def test_cplex_cp_time_limit_without_solution():
    assert _classify_status("Unknown", "SearchStoppedByLimit", "", has_solution=False) == "TO"


def test_cplex_cp_unknown_failure_without_solution():
    assert _classify_status("Unknown", "Unknown", "", has_solution=False) == "ERR"


class _FakeVariableSolution:
    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value


class _FakeModelSolution:
    def __init__(self, values):
        self.values = values

    def get_var_solution(self, variable):
        value = self.values.get(variable)
        return None if value is None else _FakeVariableSolution(value)


class _FakeSolveResult:
    def __init__(self, solution):
        self.solution = solution

    def get_solution(self):
        return self.solution


def test_cplex_cp_complete_incumbent_is_independently_verified():
    solution = _FakeModelSolution({"x0": 2, "x1": 4, "x2": 1, "x3": 3})
    labeling, objective, error = _extract_verified_solution(
        _FakeSolveResult(solution), ["x0", "x1", "x2", "x3"], _path4()
    )
    assert labeling == {0: 2, 1: 4, 2: 1, 3: 3}
    assert objective == 2
    assert error is None


def test_cplex_cp_no_incumbent_is_not_an_extraction_error():
    labeling, objective, error = _extract_verified_solution(
        _FakeSolveResult(None), ["x0", "x1", "x2", "x3"], _path4()
    )
    assert labeling is None and objective is None and error is None


def test_cplex_cp_partial_incumbent_is_an_error():
    solution = _FakeModelSolution({"x0": 2, "x1": 4, "x2": 1})
    labeling, objective, error = _extract_verified_solution(
        _FakeSolveResult(solution), ["x0", "x1", "x2", "x3"], _path4()
    )
    assert labeling is None and objective is None
    assert isinstance(error, ValueError)


def test_cplex_cp_invalid_incumbent_is_an_error():
    solution = _FakeModelSolution({"x0": 1, "x1": 1, "x2": 2, "x3": 3})
    labeling, objective, error = _extract_verified_solution(
        _FakeSolveResult(solution), ["x0", "x1", "x2", "x3"], _path4()
    )
    assert labeling is None and objective is None and error is not None


def test_cp_sat_warns_when_ignoring_shared_config_fields():
    config = Config(method="cp_sat", symmetry=True, time_limit=5.0)
    with pytest.warns(UserWarning, match="symmetry"):
        result = solve_cp_sat(_path4(), config)
    assert result.status == "OPT"
