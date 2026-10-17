from types import SimpleNamespace

from src.exact.cplex_mip import _is_proven_optimal
from src.exact.cplex_cp import _classify_status


def test_exact_optimal_status_is_accepted():
    statuses = SimpleNamespace(
        optimal=101,
        MIP_optimal=101,
        MIP_optimal_tolerance=102,
    )
    assert _is_proven_optimal(statuses, 101)


def test_optimal_tolerance_is_not_exact_optimal():
    statuses = SimpleNamespace(
        optimal=101,
        MIP_optimal=101,
        MIP_optimal_tolerance=102,
    )
    assert not _is_proven_optimal(statuses, 102)


def test_cplex_cp_optimal_with_solution():
    assert _classify_status(
        "Optimal", "", "", has_solution=True
    ) == "OPT"


def test_cplex_cp_feasible_without_optimality_proof():
    assert _classify_status(
        "Feasible", "", "", has_solution=True
    ) == "FEAS"


def test_cplex_cp_incumbent_preserved_after_memory_stop():
    assert _classify_status(
        "Feasible", "", "Out of memory", has_solution=True
    ) == "FEAS"


def test_cplex_cp_memory_failure_without_solution():
    assert _classify_status(
        "Unknown", "Unknown", "Out of memory", has_solution=False
    ) == "MO"


def test_cplex_cp_time_limit_without_solution():
    assert _classify_status(
        "Unknown",
        "SearchStoppedByLimit",
        "",
        has_solution=False,
    ) == "TO"


def test_cplex_cp_unknown_failure_without_solution():
    assert _classify_status(
        "Unknown", "Unknown", "", has_solution=False
    ) == "ERR"