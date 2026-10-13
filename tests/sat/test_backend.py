"""Test cho `src/sat/backend.py`: SAT/UNSAT, model, giới hạn thời gian, input biên."""

from time import monotonic

import pytest
from pysat.examples.genhard import PHP

from src.sat.backend import (
    DEFAULT_SOLVER,
    BackendError,
    SatBackend,
    supported_solvers,
)


def test_solve_toy_cnf_sat():
    with SatBackend("cadical195") as backend:
        backend.add_clause([1])
        backend.add_clauses([[-1, 2]])

        assert backend.solve() == "SAT"
        assert backend.status == "SAT"
        assert backend.n_vars == 2
        assert backend.n_clauses == 2

        model = backend.get_model()
        assert set(model) == {1, 2}


def test_solve_toy_cnf_unsat():
    with SatBackend("cadical195") as backend:
        backend.add_clauses([[1], [-1]])

        assert backend.solve() == "UNSAT"
        assert backend.status == "UNSAT"
        assert backend.get_model() is None


def test_unknown_solver_raises_backend_error():
    with pytest.raises(BackendError, match="Không khởi tạo được"):
        SatBackend("solver-khong-ton-tai")


def test_add_clause_rejects_invalid_literals():
    with SatBackend("cadical195") as backend:
        with pytest.raises(ValueError, match="rỗng"):
            backend.add_clause([])
        with pytest.raises(ValueError, match="Literal 0"):
            backend.add_clause([0])
        with pytest.raises(ValueError, match="số nguyên"):
            backend.add_clause([True])


def test_zero_time_limit_returns_unknown_without_solving():
    with SatBackend("cadical195") as backend:
        backend.add_clause([1])

        assert backend.solve(time_limit=0.0) == "UNKNOWN"
        assert backend.solve_time == 0.0


# PHP(13 lỗ) không giải được trong 0.3 giây: dùng để kiểm tra timeout thật.
@pytest.mark.parametrize("solver_name", ["glucose4", "cadical195"])
def test_time_limit_stops_hard_instance(solver_name):
    backend = SatBackend(solver_name)
    try:
        backend.add_clauses(PHP(nof_holes=13).clauses)

        start = monotonic()
        assert backend.solve(time_limit=0.3) == "UNKNOWN"
        assert monotonic() - start < 3.0
    finally:
        backend.delete()


def test_kissat_is_constructible_but_unusable_for_loading():
    # PySAT 1.9.dev15 (Windows/py3.14): Kissat crash access violation khi nạp
    # clause -> chỉ khởi tạo được, xem docs/sat_tooling.md mục Kissat.
    with SatBackend("kissat") as backend:
        assert backend.n_vars == 0


def test_supported_solvers_are_constructible():
    for name in supported_solvers():
        with SatBackend(name) as backend:
            assert backend.status == "UNKNOWN"


def test_default_solver_supports_time_limit():
    assert DEFAULT_SOLVER in supported_solvers()