from types import SimpleNamespace

from src.exact.cplex_mip import _is_proven_optimal


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
