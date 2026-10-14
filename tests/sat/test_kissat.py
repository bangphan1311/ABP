"""Test `src/sat/kissat.py`: parser DIMACS/model, thiếu binary, binary thật (nếu có).

Binary Kissat không có sẵn trên mọi máy, nên phần chạy thật được skip khi thiếu
(`ABP_KISSAT` hoặc `kissat` trên PATH); parser, đường lỗi và binary giả luôn được test.
"""

import os
from pathlib import Path

import pytest

from src.common.models import Config
from src.common.verify import verify
from src.exact.oracle import solve_oracle
from src.sat import generator, kissat
from src.sat.backend import BackendError
from src.sat.kissat import KissatBackend, dimacs, kissat_path, parse_kissat_output
from src.sat.pairwise import build_cnf
from src.sat.solve import solve_decision, solve_sat

requires_kissat = pytest.mark.skipif(
    kissat_path() is None,
    reason="Không có binary kissat (đặt ABP_KISSAT hoặc thêm vào PATH).",
)


def _fake_kissat_binary(tmp_path: Path, exit_code: int) -> str:
    """Binary giả bỏ qua tham số và thoát với ``exit_code`` (10 = SAT, 20 = UNSAT)."""
    if os.name == "nt":
        path = tmp_path / "kissat-gia.bat"
        path.write_text(f"@exit /b {exit_code}\r\n", encoding="ascii")
    else:
        path = tmp_path / "kissat-gia.sh"
        path.write_text(f"#!/bin/sh\nexit {exit_code}\n", encoding="ascii")
        path.chmod(0o755)
    return str(path)


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


def test_io_time_is_split_from_solve_time(monkeypatch, tmp_path):
    # R2: Kissat ghi DIMACS ra file -> thời gian ghi đó là ``io_time``, KHÔNG nằm
    # trong ``solve_time`` (PySAT nạp clause ở ``add_clauses``, t_solve chỉ có solver).
    fake = _fake_kissat_binary(tmp_path, kissat.UNSAT_EXIT_CODE)

    backend = KissatBackend(binary=fake)
    try:
        backend.add_clauses(build_cnf(generator.grid(6, 6), 1).clauses)
        assert backend.solve() == "UNSAT"
        assert backend.io_time > 0.0
        assert backend.solve_time > 0.0
    finally:
        backend.delete()

    # Binary giả luôn trả UNSAT nên pipeline kết thúc ERR; ở đây chỉ kiểm tra
    # ``t_io`` được mang vào metadata của Result.
    monkeypatch.setattr(kissat, "kissat_path", lambda: fake)
    result = solve_sat(generator.path(4), Config(method="sat", sat_solver="kissat"))

    assert result.metadata["t_io"] > 0.0
    assert result.metadata["probes"][0]["t_io"] > 0.0


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
