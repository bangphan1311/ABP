from types import SimpleNamespace

from src.common.checkpoint import load_valid_incumbent_checkpoint
from src.common.models import Config
from src.sat import generator
import src.sat.solve as solve_module


def test_sat_solver_persists_verified_incumbent_checkpoint(monkeypatch, tmp_path):
    instance = generator.path(4)
    config = Config(method="sat", time_limit=30)
    checkpoint_path = tmp_path / "checkpoints" / "sat-run.json"
    monkeypatch.setenv("ABP_CHECKPOINT_PATH", str(checkpoint_path))
    monkeypatch.setenv("ABP_CHECKPOINT_RUN_ID", "sat-run")

    # Mô phỏng hai probe để kiểm tra tích hợp checkpoint mà không phụ thuộc hiệu năng solver.
    solution = {0: 2, 1: 4, 2: 1, 3: 3}
    cnf = SimpleNamespace(n_vars=4, clauses=[[1]], stats={"distance": 1})

    def fake_probe(instance, k, *args):
        if k == 1:
            return "SAT", solution, cnf, 0.01, 0.01, 12.0
        assert k == 3
        return "UNSAT", None, cnf, 0.01, 0.01, 12.0

    monkeypatch.setattr(solve_module, "_probe", fake_probe)
    result = solve_module.solve_sat(instance, config)

    assert result.status == "OPT"
    checkpoint = load_valid_incumbent_checkpoint(
        checkpoint_path, instance, config, "sat-run"
    )
    assert checkpoint is not None
    assert checkpoint["objective"] == result.lb == 2
    assert checkpoint["solution"] == solution
