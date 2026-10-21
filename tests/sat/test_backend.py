"""Test cho `src/sat/backend.py`: SAT/UNSAT, model, giới hạn thời gian, input biên."""

import pytest
from pysat.examples.genhard import PHP

from src.sat import generator
from src.sat.backend import (
    DEFAULT_SOLVER,
    BackendError,
    SatBackend,
    supported_solvers,
)
from src.sat.pairwise import build_cnf, decode_model


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
    limit = 0.3
    backend = SatBackend(solver_name)
    try:
        backend.add_clauses(PHP(nof_holes=13).clauses)

        # Máy nhanh có thể giải xong trước limit (UNSAT): khi đó vẫn đúng, chỉ cần
        # không vượt limit. Không assert giây tuyệt đối.
        assert backend.solve(time_limit=limit) in ("UNKNOWN", "UNSAT")
        assert backend.solve_time < 2 * limit + 1.0
    finally:
        backend.delete()


def test_supported_solvers_are_constructible():
    for name in supported_solvers():
        with SatBackend(name) as backend:
            assert backend.status == "UNKNOWN"


def test_default_solver_supports_time_limit():
    assert DEFAULT_SOLVER in supported_solvers()


# Kissat của PySAT: model sai + abort process qua PySAT, không có binary ngoài.
# Hạn chế vĩnh viễn W2 (ticket 09): chặn ở khởi tạo, trước native crash.
@pytest.mark.parametrize("solver_name", ["kissat404", "kissat"])
def test_kissat_is_blocked_at_backend_construction(solver_name):
    with pytest.raises(ValueError, match="hạn chế vĩnh viễn W2"):
        SatBackend(solver_name)


class FakeBackend:
    """Backend giả: ghi lại clause, không giải. Đủ giao diện mà tầng trên dùng."""

    def __init__(self):
        self.clauses: list[list[int]] = []
        self._status = "UNKNOWN"

    @property
    def status(self):
        return self._status

    def add_clause(self, clause):
        self.clauses.append(list(clause))

    def add_clauses(self, clauses):
        for clause in clauses:
            self.add_clause(clause)

    def solve(self, time_limit=None):
        return self._status

    def get_model(self):
        return None


def test_encoding_is_identical_across_backends():
    # path(4): K=2 SAT (labels 2,4,1,3), K=3 UNSAT. Encoding không phụ thuộc backend.
    cnf = build_cnf(generator.path(4), 2)

    fake = FakeBackend()
    fake.add_clauses(cnf.clauses)
    assert fake.clauses == cnf.clauses

    with SatBackend("cadical195") as real:
        real.add_clauses(cnf.clauses)
        assert real.n_clauses == len(fake.clauses)
        assert real.solve() == "SAT"
        labeling = decode_model(cnf, real.get_model())
        assert set(labeling.values()) == {1, 2, 3, 4}

    unsat_cnf = build_cnf(generator.path(4), 3)
    with SatBackend("cadical195") as real:
        real.add_clauses(unsat_cnf.clauses)
        assert real.solve() == "UNSAT"
