"""Test `src/sat/kissat.py`: parser DIMACS/model, thiếu binary, binary thật (nếu có).

Binary Kissat không có sẵn trên mọi máy, nên phần chạy thật được skip khi thiếu
(`ABP_KISSAT` hoặc `kissat` trên PATH); parser và đường lỗi luôn được test.
"""

import pytest

from src.common.models import Config
from src.common.verify import verify
from src.exact.oracle import solve_oracle
from src.sat import generator, kissat
from src.sat.backend import BackendError
from src.sat.kissat import KissatBackend, dimacs, kissat_path, parse_kissat_output
from src.sat.solve import solve_decision, solve_sat

requires_kissat = pytest.mark.skipif(
    kissat_path() is None,
    reason="Không có binary kissat (đặt ABP_KISSAT hoặc thêm vào PATH).",
)


def test_parse_kissat_output_maps_exit_codes_and_model():
    assert parse_kissat_output(20, "s UNSATISFIABLE\n") == ("UNSAT", None)

    status, model = parse_kissat_output(10, "s SATISFIABLE\nv 1 -2 3 0\n")
    assert status == "SAT"
    assert model == [1, -2, 3]


def test_parse_kissat_output_rejects_error_code_and_missing_model():
    with pytest.raises(BackendError, match="mã 1"):
        parse_kissat_output(1, "kissat: error: invalid option")

    with pytest.raises(BackendError, match="model"):
        parse_kissat_output(10, "s SATISFIABLE\n")


def test_dimacs_header_and_clauses():
    assert dimacs(3, [[1, -2], [-3]]) == "p cnf 3 2\n1 -2 0\n-3 0\n"


def test_env_override_must_point_to_existing_file(monkeypatch, tmp_path):
    monkeypatch.setenv(kissat.BINARY_ENV_VAR, str(tmp_path / "khong-ton-tai"))
    assert kissat_path() is None

    fake = tmp_path / "kissat.exe"
    fake.write_text("")
    monkeypatch.setenv(kissat.BINARY_ENV_VAR, str(fake))
    assert kissat_path() == str(fake)


def test_missing_binary_reports_err_not_crash(monkeypatch):
    monkeypatch.setattr(kissat, "kissat_path", lambda: None)

    with pytest.raises(BackendError, match="Không tìm thấy binary Kissat"):
        KissatBackend()

    result = solve_sat(generator.path(4), Config(method="sat", sat_solver="kissat"))

    assert result.status == "ERR"
    assert result.lb is None
    assert "Kissat" in result.metadata["error"]


def test_broken_binary_reports_err(tmp_path):
    # File tồn tại nhưng không phải chương trình chạy được -> ERR, không crash.
    broken = tmp_path / "kissat.exe"
    broken.write_text("not a binary")

    backend = KissatBackend(binary=str(broken))
    backend.add_clause([1])

    with pytest.raises(BackendError, match="Không chạy được binary kissat"):
        backend.solve()


def test_kissat_backend_keeps_clauses_without_binary():
    # Không cần binary: chỉ kiểm tra interface giữ clause đúng.
    backend = KissatBackend(binary="kissat-gia")
    try:
        backend.add_clauses([[1, -2], [-1]])
        assert backend.n_vars == 2
        assert backend.n_clauses == 2
        assert backend.get_model() is None
    finally:
        backend.delete()


@requires_kissat
def test_kissat_matches_oracle_on_toy_instances():
    for instance in (generator.path(4), generator.cycle(5), generator.complete(3)):
        result = solve_sat(instance, Config(method="sat", sat_solver="kissat"))
        oracle = solve_oracle(instance)

        assert result.status == "OPT", instance.id
        assert result.lb == oracle.lb, instance.id
        assert verify(instance, result.solution) == result.lb, instance.id


@requires_kissat
def test_kissat_unsat_threshold_is_reported_as_unsat():
    instance = generator.path(4)

    assert solve_decision(instance, 3, Config(method="sat", sat_solver="kissat")) == (
        "UNSAT",
        None,
    )
