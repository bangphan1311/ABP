import json

import pytest

import src.runner.runner as runner_mod
from src.common.models import Config
from src.common.verify import verify
from src.runner.schema import RUN_FIELDS, make_run_id
from src.sat import generator
from src.sat.loader import write_instance


@pytest.fixture
def path4(tmp_path):
    f = tmp_path / "path4.json"
    write_instance(f, generator.path(4))
    return f


def test_oracle_run_saves_schema_record(path4, tmp_path):
    out = tmp_path / "raw"
    cfg = Config(method="oracle", time_limit=30)
    rec = runner_mod.run_one(path4, cfg, out)
    assert rec["status"] == "OPT" and rec["lb"] == 2 and rec["ub"] == 2
    for field in RUN_FIELDS:
        assert field in rec, field
    saved = json.loads((out / f"{rec['run_id']}.json").read_text(encoding="utf-8"))
    assert saved["run_id"] == rec["run_id"] == make_run_id(generator.path(4), cfg)
    assert saved["solution"] is not None


def test_resume_skips_existing(path4, tmp_path):
    out = tmp_path / "raw"
    cfg = Config(method="oracle", time_limit=30)
    first = runner_mod.run_one(path4, cfg, out)
    again = runner_mod.run_one(path4, cfg, out, resume=True)
    assert again["timestamp"] == first["timestamp"]  # không chạy lại


def test_resume_does_not_reuse_run_with_different_time_limit(path4, tmp_path):
    out = tmp_path / "raw"
    short = runner_mod.run_one(path4, Config(method="oracle", time_limit=30), out)
    long_ = runner_mod.run_one(path4, Config(method="oracle", time_limit=1800), out, resume=True)
    assert long_["run_id"] != short["run_id"]
    assert long_["time_limit"] == 1800
    assert len(list(out.glob("*.json"))) == 2


def test_solver_exception_becomes_err(path4, tmp_path):
    cfg = Config(method="tests.runner.slow_solver:solve_boom", time_limit=30)
    rec = runner_mod.run_one(path4, cfg, tmp_path / "raw")
    assert rec["status"] == "ERR"
    assert "license" in rec["error"]


def test_hard_timeout_becomes_to(path4, tmp_path, monkeypatch):
    monkeypatch.setattr(runner_mod, "KILL_GRACE_SECONDS", 0.0)
    cfg = Config(method="tests.runner.slow_solver:solve_slow", time_limit=1.0)
    rec = runner_mod.run_one(path4, cfg, tmp_path / "raw")
    assert rec["status"] == "TO"
    assert rec["lb"] is None


def test_wrong_solution_is_caught_by_runner(path4, tmp_path, monkeypatch):
    import tests.runner.slow_solver as m  # noqa: F401
    cfg = Config(method="tests.runner.liar:solve_liar", time_limit=30)
    rec = runner_mod.run_one(path4, cfg, tmp_path / "raw")
    assert rec["status"] == "ERR"
    assert "khác objective" in rec["error"]


def test_resume_archives_corrupted_json_before_rerunning(path4, tmp_path):
    out = tmp_path / "raw"
    cfg = Config(method="oracle", time_limit=30)
    first = runner_mod.run_one(path4, cfg, out)
    raw_path = out / f"{first['run_id']}.json"
    raw_path.write_text("{not valid json", encoding="utf-8")

    again = runner_mod.run_one(path4, cfg, out, resume=True)

    assert again["status"] == "OPT"
    archived = list((out / "attempt_history").glob("*.json"))
    assert len(archived) == 1
    assert archived[0].read_text(encoding="utf-8") == "{not valid json"


def test_resume_retries_err_and_preserves_previous_attempt(path4, tmp_path):
    out = tmp_path / "raw"
    cfg = Config(method="tests.runner.slow_solver:solve_boom", time_limit=30)
    first = runner_mod.run_one(path4, cfg, out)
    assert first["status"] == "ERR"

    again = runner_mod.run_one(path4, cfg, out, resume=True)

    assert again["status"] == "ERR"
    archived = list((out / "attempt_history").glob("*.json"))
    assert len(archived) == 1
    prior = json.loads(archived[0].read_text(encoding="utf-8"))
    assert prior["status"] == "ERR"



def test_hard_timeout_recovers_verified_checkpoint(path4, tmp_path, monkeypatch):
    # Worker ghi incumbent rồi bị runner kill; runner phải phục hồi FEAS và verify lại.
    monkeypatch.setattr(runner_mod, "KILL_GRACE_SECONDS", 0.0)
    cfg = Config(method="tests.runner.slow_solver:solve_checkpoint_slow", time_limit=3.0)

    rec = runner_mod.run_one(path4, cfg, tmp_path / "raw", resume=True)

    assert rec["status"] == "FEAS"
    assert rec["metadata"]["checkpoint_recovered"] is True
    assert rec["metadata"]["metrics_are_partial"] is True
    assert rec["lb"] == verify(
        generator.path(4), {int(k): v for k, v in rec["solution"].items()}
    )
    checkpoint = tmp_path / "raw" / "checkpoints" / f"{rec['run_id']}.json"
    assert checkpoint.is_file()



def test_os_memory_limit_returns_mo_when_worker_exceeds_cap(path4, tmp_path):
    # 128 MiB hard cap; solver thử giữ 192 MiB. Không có cap thì test phải fail.
    cfg = Config(
        method="tests.runner.slow_solver:solve_memory_hog",
        time_limit=30.0,
        memory_limit=0.125,
    )
    rec = runner_mod.run_one(path4, cfg, tmp_path / "raw")

    assert rec["status"] == "MO", rec
    assert rec["memory_limit"] == 0.125
    assert rec["error"] == "MemoryError"
