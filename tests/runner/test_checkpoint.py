import json

from src.common.checkpoint import (
    load_valid_incumbent_checkpoint,
    write_incumbent_checkpoint,
)
from src.common.models import Config
from src.exact.oracle import solve_oracle
from src.sat import generator


def test_checkpoint_rejects_tampered_solution(tmp_path):
    instance = generator.path(4)
    config = Config(method="oracle", time_limit=30)
    solved = solve_oracle(instance)
    assert solved.solution is not None and solved.lb is not None
    path = tmp_path / "checkpoint.json"

    write_incumbent_checkpoint(
        instance,
        config,
        objective=solved.lb,
        solution=solved.solution,
        path=path,
        run_id="test-run",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    vertices = list(payload["solution"])
    payload["solution"][vertices[0]] = payload["solution"][vertices[1]]
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert load_valid_incumbent_checkpoint(path, instance, config, "test-run") is None


def test_checkpoint_rejects_different_config_and_instance(tmp_path):
    instance = generator.path(4)
    config = Config(method="oracle", time_limit=30)
    solved = solve_oracle(instance)
    assert solved.solution is not None and solved.lb is not None
    path = tmp_path / "checkpoint.json"

    write_incumbent_checkpoint(
        instance,
        config,
        objective=solved.lb,
        solution=solved.solution,
        path=path,
        run_id="test-run",
    )

    assert load_valid_incumbent_checkpoint(
        path, instance, Config(method="oracle", time_limit=31), "test-run"
    ) is None
    changed_instance = generator.cycle(4)
    assert load_valid_incumbent_checkpoint(
        path, changed_instance, config, "test-run"
    ) is None
