import json

import pytest

import src.runner.runner as runner_mod
from src.common.models import Config
from src.runner.schema import RUN_FIELDS, make_run_id
from src.sat import generator
from src.sat.loader import write_instance

import os
import platform
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from src.common.models import Instance
from src.sat.loader import read_instance


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


# --- dry-run: A1–A8 ---

def test_dry_run_record_shape(path4, tmp_path):
    cfg = Config(method="oracle", time_limit=30)
    rec = runner_mod.run_one(path4, cfg, tmp_path / "raw", dry_run=True)

    assert isinstance(rec, dict) and type(rec) is dict
    for field in RUN_FIELDS:
        assert field in rec, field
    for key in ("config", "solution", "metadata", "dry_run"):
        assert key in rec, key

    assert rec["status"] == "DRY_RUN"
    for field in ("lb", "ub", "t_encode", "t_solve", "t_total",
                  "variables", "clauses", "peak_memory"):
        assert rec[field] is None, field
    assert rec["solution"] is None
    assert rec["metadata"] == {}
    assert rec["error"] is None
    assert rec["solver"] == "oracle"
    assert rec["run_id"] == make_run_id(read_instance(path4), cfg)
    assert rec["instance"] == "path4"
    assert rec["git_tag"] and rec["host"] and rec["timestamp"]
    assert isinstance(rec["wall_time"], float)
    assert rec["time_limit"] == 30
    assert rec["memory_limit"] is None
    assert rec["seed"] == 0
    assert rec["symmetry"] is False and rec["warm_start"] is False
    assert rec["config"] == asdict(cfg)

    info = rec["dry_run"]
    assert type(info) is dict
    assert set(info) == {"out_file", "exists", "resume_would_skip",
                         "hard_limit", "n", "m"}
    assert isinstance(info["out_file"], str)
    assert info["n"] == 4 and info["m"] == 3
    assert not hasattr(info, "__dataclass_fields__")


def test_dry_run_writes_nothing(path4, tmp_path):
    out = tmp_path / "raw"
    runner_mod.run_one(path4, Config(method="oracle", time_limit=30), out,
                       dry_run=True)
    assert out.exists() is False
    leftovers = [p for p in tmp_path.iterdir() if p.name != "path4.json"]
    assert leftovers == []


def test_dry_run_preexisting_dir_untouched(path4, tmp_path):
    out = tmp_path / "raw"
    out.mkdir()
    (out / "sentinel.txt").write_text("keep", encoding="utf-8")
    before = {p.name: (p.stat().st_size, p.stat().st_mtime_ns)
              for p in out.iterdir()}
    runner_mod.run_one(path4, Config(method="oracle", time_limit=30), out,
                       dry_run=True)
    after = {p.name: (p.stat().st_size, p.stat().st_mtime_ns)
             for p in out.iterdir()}
    assert after == before


def test_dry_run_does_not_enter_tempdir(path4, tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("dry-run entered TemporaryDirectory")

    monkeypatch.setattr(runner_mod.tempfile, "TemporaryDirectory", boom)
    rec = runner_mod.run_one(path4, Config(method="oracle", time_limit=30),
                             tmp_path / "raw", dry_run=True)
    assert rec["status"] == "DRY_RUN"


def test_dry_run_branch_order(path4, tmp_path, monkeypatch):
    labels = []
    real_read = runner_mod.read_instance
    real_run_id = runner_mod.make_run_id

    def read_spy(*args, **kwargs):
        labels.append("read")
        return real_read(*args, **kwargs)

    def run_id_spy(*args, **kwargs):
        labels.append("run_id")
        return real_run_id(*args, **kwargs)

    def temp_spy(*args, **kwargs):
        labels.append("tempdir")
        raise AssertionError("dry-run entered TemporaryDirectory")

    monkeypatch.setattr(runner_mod, "read_instance", read_spy)
    monkeypatch.setattr(runner_mod, "make_run_id", run_id_spy)
    monkeypatch.setattr(runner_mod.tempfile, "TemporaryDirectory", temp_spy)

    runner_mod.run_one(path4, Config(method="oracle", time_limit=30),
                       tmp_path / "raw", dry_run=True)
    assert labels == ["read", "run_id"]


def test_dry_run_hard_limit_follows_grace_constant(path4, tmp_path, monkeypatch):
    monkeypatch.setattr(runner_mod, "KILL_GRACE_SECONDS", 7.5)
    rec = runner_mod.run_one(path4, Config(method="oracle", time_limit=100.0),
                             tmp_path / "a", dry_run=True)
    assert rec["dry_run"]["hard_limit"] == 107.5

    rec_none = runner_mod.run_one(
        path4, Config(method="oracle", time_limit=None), tmp_path / "b",
        dry_run=True)
    assert rec_none["dry_run"]["hard_limit"] is None

    rec_zero = runner_mod.run_one(
        path4, Config(method="oracle", time_limit=0), tmp_path / "c",
        dry_run=True)
    assert rec_zero["dry_run"]["hard_limit"] == 7.5


def test_dry_run_run_id_matches_real_run(path4, tmp_path):
    cfg = Config(method="oracle", time_limit=30)
    dry = runner_mod.run_one(path4, cfg, tmp_path / "dryout", dry_run=True)
    real = runner_mod.run_one(path4, cfg, tmp_path / "realout")

    assert dry["run_id"] == real["run_id"] == make_run_id(read_instance(path4), cfg)
    assert (tmp_path / "realout" / f"{real['run_id']}.json").exists()
    assert (tmp_path / "dryout").exists() is False

    int_rec = runner_mod.run_one(
        path4, Config(method="oracle", time_limit=30), tmp_path / "i",
        dry_run=True)
    float_rec = runner_mod.run_one(
        path4, Config(method="oracle", time_limit=1800.0), tmp_path / "f",
        dry_run=True)
    none_rec = runner_mod.run_one(
        path4, Config(method="oracle", time_limit=None), tmp_path / "n",
        dry_run=True)
    assert int_rec["run_id"].endswith("__tl30__mlNone")
    assert float_rec["run_id"].endswith("__tl1800.0__mlNone")
    assert none_rec["run_id"].endswith("__tlNone__mlNone")


def test_dry_run_run_id_ignores_edge_content(tmp_path):
    base = generator.path(4)
    other = Instance(id=base.id, name="other", n=4,
                     edges=((0, 1), (1, 2), (2, 3), (0, 3)),
                     source="test", tier="toy")
    f1, f2 = tmp_path / "a.json", tmp_path / "b.json"
    write_instance(f1, base)
    write_instance(f2, other)
    cfg = Config(method="oracle", time_limit=30)
    r1 = runner_mod.run_one(f1, cfg, tmp_path / "o1", dry_run=True)
    r2 = runner_mod.run_one(f2, cfg, tmp_path / "o2", dry_run=True)
    assert r1["run_id"] == r2["run_id"]


def test_dry_run_resume_reports_without_parsing_garbage(path4, tmp_path):
    cfg = Config(method="oracle", time_limit=30)
    out = tmp_path / "raw"
    out.mkdir()
    target = out / f"{make_run_id(read_instance(path4), cfg)}.json"
    target.write_bytes(b"not json {{{")

    rec = runner_mod.run_one(path4, cfg, out, resume=True, dry_run=True)
    assert rec["status"] == "DRY_RUN"
    assert rec["dry_run"]["exists"] is True
    assert rec["dry_run"]["resume_would_skip"] is True
    assert target.read_bytes() == b"not json {{{"

    rec2 = runner_mod.run_one(path4, cfg, out, dry_run=True)
    assert rec2["dry_run"]["exists"] is True
    assert rec2["dry_run"]["resume_would_skip"] is False


def test_dry_run_resume_absent_file(path4, tmp_path):
    cfg = Config(method="oracle", time_limit=30)
    out = tmp_path / "raw"
    out.mkdir()
    for resume in (True, False):
        rec = runner_mod.run_one(path4, cfg, out, resume=resume, dry_run=True)
        assert rec["dry_run"]["exists"] is False
        assert rec["dry_run"]["resume_would_skip"] is False


def test_dry_run_spawns_no_worker(path4, tmp_path, monkeypatch):
    calls = []
    real_run = subprocess.run

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        return real_run(*args, **kwargs)

    monkeypatch.setattr(runner_mod.subprocess, "run", spy)
    rec = runner_mod.run_one(path4, Config(method="oracle", time_limit=30),
                             tmp_path / "raw", dry_run=True)
    assert rec["status"] == "DRY_RUN"

    for args, _kwargs in calls:
        flat = [str(a) for a in args]
        assert "src.runner.worker" not in flat
        assert flat[:3] != [sys.executable, "-m", "src.runner.worker"]
    assert any("describe" in " ".join(str(a) for a in args)
               for args, _ in calls)


def test_dry_run_validation_matches_real_run(path4, tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({
        "id": "empty", "name": "empty", "n": 4, "edges": [],
        "source": "test", "tier": "toy",
    }), encoding="utf-8")
    cfg = Config(method="oracle", time_limit=30)
    out = tmp_path / "raw"

    with pytest.raises(ValueError) as dry_exc:
        runner_mod.run_one(empty, cfg, out, dry_run=True)
    with pytest.raises(ValueError) as real_exc:
        runner_mod.run_one(empty, cfg, out)

    assert str(dry_exc.value) == str(real_exc.value)
    assert "Instance is empty" in str(dry_exc.value)
    assert out.exists() is False


def test_dry_run_validation_missing_and_malformed(tmp_path):
    cfg = Config(method="oracle", time_limit=30)
    out = tmp_path / "raw"
    missing = tmp_path / "nope.json"
    for fn in (lambda: runner_mod.run_one(missing, cfg, out, dry_run=True),
               lambda: runner_mod.run_one(missing, cfg, out)):
        with pytest.raises(FileNotFoundError):
            fn()

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    types = []
    for fn in (lambda: runner_mod.run_one(bad, cfg, out, dry_run=True),
               lambda: runner_mod.run_one(bad, cfg, out)):
        with pytest.raises(json.JSONDecodeError) as exc:
            fn()
        types.append(type(exc.value))
    assert types[0] is types[1]
    assert out.exists() is False


def test_dry_run_method_check_imports_nothing(path4, tmp_path):
    cfg_bad = Config(method="nope", time_limit=30)
    with pytest.raises(ValueError, match="không có trong registry"):
        runner_mod.run_one(path4, cfg_bad, tmp_path / "raw", dry_run=True)
    assert (tmp_path / "raw").exists() is False

    # Pre-warm stdlib that build_record pulls in (platform.node -> socket), so
    # the snapshot measures the dry-run branch, not first-touch stdlib imports.
    platform.node()

    before = set(sys.modules)
    rec = runner_mod.run_one(
        path4, Config(method="tests.runner.nonexistent_module:solve",
                      time_limit=30), tmp_path / "raw2", dry_run=True)
    assert rec["status"] == "DRY_RUN"
    new = set(sys.modules) - before
    assert new == set()
    assert not any(m.startswith("src.exact") for m in new)
    assert "tests.runner.nonexistent_module" not in new
    assert (tmp_path / "raw2").exists() is False

    rec_sat = runner_mod.run_one(
        path4, Config(method="sat", time_limit=30), tmp_path / "raw3",
        dry_run=True)
    assert rec_sat["status"] == "DRY_RUN"


def test_dry_run_duplicate_edges_dedup(tmp_path):
    raw = {"id": "dup", "name": "dup", "n": 4,
           "edges": [[0, 1], [1, 0], [1, 2], [2, 3]],
           "source": "test", "tier": "toy"}
    f = tmp_path / "dup.json"
    f.write_text(json.dumps(raw), encoding="utf-8")
    rec = runner_mod.run_one(f, Config(method="oracle", time_limit=30),
                             tmp_path / "raw", dry_run=True)
    assert rec["dry_run"]["m"] == 3
    assert rec["run_id"].startswith("dup__oracle")


def test_dry_run_reports_memory_limit_verbatim(path4, tmp_path):
    rec = runner_mod.run_one(
        path4, Config(method="oracle", time_limit=30, memory_limit=2048),
        tmp_path / "raw", dry_run=True)
    assert rec["memory_limit"] == 2048
    assert "memory_limit_enforced" not in rec


def test_dry_run_non_ascii_id(path4, tmp_path):
    raw = json.loads(Path(path4).read_text(encoding="utf-8"))
    raw["id"] = "path4-đường"
    f = tmp_path / "unicode.json"
    f.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    rec = runner_mod.run_one(f, Config(method="oracle", time_limit=30),
                             tmp_path / "raw", dry_run=True)
    assert "path4-đường" in rec["run_id"]
    assert rec["status"] == "DRY_RUN"


# --- dry-run CLI: A9–A10 ---

def _run_cli(args, env_extra=None, encoding=None):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "src.runner", *args],
        cwd=str(runner_mod.REPO_ROOT), capture_output=True, text=True,
        encoding=encoding, env=env,
    )


def test_cli_dry_run_prints_five_lines(path4, tmp_path):
    out = tmp_path / "raw"
    cfg = Config(method="oracle", time_limit=1800.0)
    run_id = make_run_id(read_instance(path4), cfg)
    r = _run_cli(["--instance", str(path4), "--method", "oracle",
                  "--time-limit", "1800", "--out", str(out), "--dry-run"])

    assert r.returncode == 0
    assert r.stderr == ""
    lines = r.stdout.splitlines()
    assert len(lines) == 5
    assert lines[0] == f"DRY_RUN run_id={run_id}"
    assert lines[1] == "DRY_RUN instance=path4 n=4 m=3"
    assert lines[2] == (
        "DRY_RUN config method=oracle abp_encoding=none "
        "amo_encoding=none sat_solver=none search_mode=none "
        "symmetry=false warm_start=false seed=0"
    )
    assert lines[3] == (
        "DRY_RUN budget time_limit=1800.0 "
        f"hard_limit={1800.0 + runner_mod.KILL_GRACE_SECONDS} "
        "memory_limit=none memory_limit_enforced=false"
    )
    prefix = "DRY_RUN output out_file="
    tail = " exists=false resume_would_skip=false"
    assert lines[4].startswith(prefix) and lines[4].endswith(tail)
    assert Path(lines[4][len(prefix):-len(tail)]) == out / f"{run_id}.json"
    assert out.exists() is False


def test_cli_dry_run_memory_limit_and_resume(path4, tmp_path):
    out = tmp_path / "raw"
    out.mkdir()
    cfg = Config(method="oracle", time_limit=1800.0, memory_limit=2048.0)
    run_id = make_run_id(read_instance(path4), cfg)
    (out / f"{run_id}.json").write_text("{}", encoding="utf-8")

    r = _run_cli(["--instance", str(path4), "--method", "oracle",
                  "--time-limit", "1800", "--memory-limit", "2048",
                  "--out", str(out), "--resume", "--dry-run"])
    assert r.returncode == 0
    assert r.stderr == ""
    lines = r.stdout.splitlines()
    assert "memory_limit=2048.0 memory_limit_enforced=false" in lines[3]
    assert lines[4].endswith("exists=true resume_would_skip=true")


def test_cli_dry_run_non_ascii_out_cp1252_safe(path4, tmp_path):
    out = tmp_path / "kết_quả"
    r = _run_cli(["--instance", str(path4), "--method", "oracle",
                  "--time-limit", "1800", "--out", str(out), "--dry-run"],
                 env_extra={"PYTHONIOENCODING": "cp1252"}, encoding="cp1252")
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert r.stderr == ""
    lines = r.stdout.splitlines()
    assert len(lines) == 5
    assert all(line.startswith("DRY_RUN ") for line in lines)
    assert "Traceback" not in r.stderr
    assert "UnicodeEncodeError" not in r.stderr
    assert out.exists() is False


def test_cli_dry_run_failure_exits_2_cp1252_safe(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({
        "id": "empty", "name": "empty", "n": 4, "edges": [],
        "source": "test", "tier": "toy",
    }), encoding="utf-8")
    out = tmp_path / "raw"
    for codec in ("cp1252", "utf-8"):
        r = _run_cli(["--instance", str(bad), "--method", "oracle",
                      "--out", str(out), "--dry-run"],
                     env_extra={"PYTHONIOENCODING": codec}, encoding=codec)
        assert r.returncode == 2, (codec, r.stdout, r.stderr)
        assert r.stderr.startswith("DRY_RUN ERROR:")
        assert "Traceback" not in r.stderr
        assert "UnicodeEncodeError" not in r.stderr
        assert "codec can't encode" not in r.stderr
        assert "DRY_RUN run_id=" not in r.stdout
        assert out.exists() is False


def test_cli_dry_run_unknown_method_exits_2(path4, tmp_path):
    out = tmp_path / "raw"
    for codec in ("cp1252", "utf-8"):
        r = _run_cli(["--instance", str(path4), "--method", "nope",
                      "--out", str(out), "--dry-run"],
                     env_extra={"PYTHONIOENCODING": codec}, encoding=codec)
        assert r.returncode == 2, (codec, r.stdout, r.stderr)
        assert r.stderr.startswith("DRY_RUN ERROR:")
        assert "không có trong registry" in r.stderr
        assert "Traceback" not in r.stderr
        assert "UnicodeEncodeError" not in r.stderr
        assert "codec can't encode" not in r.stderr
        assert out.exists() is False


def test_cli_without_dry_run_unchanged(path4, tmp_path):
    out = tmp_path / "raw"
    cfg = Config(method="oracle", time_limit=30.0)
    run_id = make_run_id(read_instance(path4), cfg)
    r = _run_cli(["--instance", str(path4), "--method", "oracle",
                  "--time-limit", "30", "--out", str(out)])
    assert r.returncode == 0
    assert "DRY_RUN" not in r.stdout
    assert r.stdout.startswith(f"{run_id}: OPT")
    assert (out / f"{run_id}.json").exists()


def test_cli_dry_run_dotted_path_method(path4, tmp_path):
    out = tmp_path / "raw"
    r = _run_cli(["--instance", str(path4), "--method",
                  "tests.runner.nonexistent_module:solve",
                  "--out", str(out), "--dry-run"])
    assert r.returncode == 0
    assert r.stderr == ""
    assert len(r.stdout.splitlines()) == 5
    assert out.exists() is False
