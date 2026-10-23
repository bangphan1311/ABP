
import pytest
from ortools.sat.python import cp_model

from src.exact.cp_sat_solver import _safe_upper_bound


def test_unknown_with_zero_bound_uses_natural_upper_bound():
    assert _safe_upper_bound(cp_model.UNKNOWN, 0.0, 6) == 5


def test_unknown_with_nonzero_bound_uses_natural_upper_bound():
    assert _safe_upper_bound(cp_model.UNKNOWN, 2.0, 6) == 5


@pytest.mark.parametrize(
    ("best_bound", "expected"),
    [
        (3.0, 3),
        (2.2, 3),
        (0.0, 0),
    ],
)
def test_valid_bound_is_rounded_up(best_bound, expected):
    assert _safe_upper_bound(cp_model.OPTIMAL, best_bound, 6) == expected


def test_non_finite_bound_uses_natural_upper_bound():
    assert _safe_upper_bound(cp_model.FEASIBLE, float("inf"), 6) == 5
