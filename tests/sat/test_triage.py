"""Test công cụ trực lỗi SAT khi official run (W4, ticket 22 / #29)."""

from __future__ import annotations

import json

import pytest

from src.sat import generator
from src.sat.loader import write_instance
from src.sat.triage import (
    inspect_raw_file,
    inspect_record,
    reproduce_on_dev,
    triage_directory,
    main as triage_main,
)


def _valid_path4_record() -> dict:
    # path4: 0-1-2-3, labeling {0:2, 1:4, 2:1, 3:3} đạt antibandwidth = 2.
    return {
        "run_id": "path4__sat__order__pairwise__glucose4__multi",
        "instance": "path4",
        "method": "sat",
        "abp_encoding": "order",
        "amo_encoding": "pairwise",
        "solver": "glucose4",
        "search_mode": "multi",
        "status": "OPT",
        "lb": 2,
        "ub": 2,
        "t_encode": 0.001,
        "t_solve": 0.002,
        "t_total": 0.003,
        "variables": 12,
        "clauses": 62,
        "peak_memory": 21.0,
        "solution": {"0": 2, "1": 4, "2": 1, "3": 3},
        "metadata": {
            "probes": [
                {"k": 1, "status": "SAT", "b": 2},
                {"k": 3, "status": "UNSAT", "b": None},
            ]
        },
        "error": None,
    }


def test_inspect_record_accepts_valid_opt():
    instance = generator.path(4)
    report = inspect_record(_valid_path4_record(), instance=instance)

    assert report.category == "OK"
    assert report.is_anomaly is False
    assert report.verified_objective == 2
    assert report.recorded_lb == 2
    assert report.recorded_ub == 2


def test_inspect_record_classifies_feas_and_to_as_solver_behavior():
    instance = generator.path(4)
    feas = _valid_path4_record()
    feas["status"] = "FEAS"
    feas["ub"] = 3

    report_feas = inspect_record(feas, instance=instance)
    assert report_feas.category == "SOLVER_BEHAVIOR"
    assert report_feas.is_anomaly is True
    assert report_feas.verified_objective == 2

    to_rec = _valid_path4_record()
    to_rec["status"] = "TO"
    to_rec["lb"] = None
    to_rec["ub"] = None
    to_rec["solution"] = None
    report_to = inspect_record(to_rec, instance=instance)
    assert report_to.category == "SOLVER_BEHAVIOR"
    assert report_to.is_anomaly is True


def test_inspect_record_detects_wrong_objective_as_code_bug():
    instance = generator.path(4)
    bad = _valid_path4_record()
    bad["lb"] = 3  # solution thực tế chỉ đạt 2
    bad["ub"] = 3

    report = inspect_record(bad, instance=instance)
    assert report.category == "CODE_BUG"
    assert report.is_anomaly is True
    assert report.verified_objective == 2
    assert any("khác lb" in r for r in report.reasons)


def test_inspect_record_detects_invalid_permutation_as_code_bug():
    instance = generator.path(4)
    bad = _valid_path4_record()
    bad["solution"] = {"0": 1, "1": 1, "2": 2, "3": 3}  # trùng nhãn 1

    report = inspect_record(bad, instance=instance)
    assert report.category == "CODE_BUG"
    assert any("verify()" in r for r in report.reasons)


def test_inspect_record_detects_missing_solution_on_opt_as_code_bug():
    instance = generator.path(4)
    bad = _valid_path4_record()
    bad["solution"] = None

    report = inspect_record(bad, instance=instance)
    assert report.category == "CODE_BUG"
    assert any("không có solution" in r for r in report.reasons)


def test_inspect_record_detects_probe_contradiction_as_code_bug():
    instance = generator.path(4)
    bad = _valid_path4_record()
    bad["metadata"]["probes"] = [{"k": 3, "status": "SAT", "b": 2}]

    report = inspect_record(bad, instance=instance)
    assert report.category == "CODE_BUG"
    assert any("Probe K=3" in r for r in report.reasons)

    # UNSAT tại ngưỡng K=2 trong khi nghiệm đã verify đạt 2 >= K -> CODE_BUG
    bad_unsat = _valid_path4_record()
    bad_unsat["metadata"]["probes"] = [{"k": 2, "status": "UNSAT", "b": None}]
    report_unsat = inspect_record(bad_unsat, instance=instance)
    assert report_unsat.category == "CODE_BUG"
    assert any("trả UNSAT nhưng đã có nghiệm verify" in r for r in report_unsat.reasons)


def test_inspect_record_flags_license_error_recorded_as_to_as_code_bug():
    instance = generator.path(4)
    bad_to = _valid_path4_record()
    bad_to["status"] = "TO"
    bad_to["solution"] = None
    bad_to["lb"] = None
    bad_to["ub"] = None
    bad_to["error"] = "CPLEX error: license limit exceeded"

    report = inspect_record(bad_to, instance=instance)
    assert report.category == "CODE_BUG"
    assert any("CONTRACT §5" in r for r in report.reasons)


def test_inspect_record_classifies_mo_and_hard_kill_as_env_error():
    instance = generator.path(4)
    mo_rec = _valid_path4_record()
    mo_rec["status"] = "MO"
    mo_rec["solution"] = None
    mo_rec["lb"] = None
    mo_rec["ub"] = None
    mo_rec["error"] = "MemoryError"

    report_mo = inspect_record(mo_rec, instance=instance)
    assert report_mo.category == "ENV_ERROR"

    kill_rec = _valid_path4_record()
    kill_rec["status"] = "TO"
    kill_rec["solution"] = None
    kill_rec["lb"] = None
    kill_rec["ub"] = None
    kill_rec["error"] = "Hết 60.0s + grace, worker bị kill."

    report_kill = inspect_record(kill_rec, instance=instance)
    assert report_kill.category == "ENV_ERROR"


def test_inspect_raw_file_handles_corrupt_json(tmp_path):
    corrupt = tmp_path / "broken_run.json"
    corrupt.write_text("{not valid json", encoding="utf-8")

    report = inspect_raw_file(corrupt)
    assert report.category == "ENV_ERROR"
    assert report.is_anomaly is True
    assert any("JSON hỏng" in r for r in report.reasons)


def test_reproduce_on_dev_runs_in_memory_without_touching_raw_dir(tmp_path):
    inst_dir = tmp_path / "instances"
    inst_dir.mkdir()
    write_instance(inst_dir / "path4.json", generator.path(4))

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    rec = _valid_path4_record()
    rec["status"] = "FEAS"
    rec["ub"] = 3
    raw_file = raw_dir / f"{rec['run_id']}.json"
    raw_file.write_text(json.dumps(rec), encoding="utf-8")
    before_files = set(raw_dir.iterdir())

    dev_res = reproduce_on_dev(rec, time_limit=5.0, search_dirs=(inst_dir,))
    assert dev_res.status == "OPT"
    assert dev_res.lb == 2
    assert set(raw_dir.iterdir()) == before_files  # không tạo file mới trong raw/

    reports = triage_directory(
        raw_dir,
        search_dirs=(inst_dir,),
        reproduce_anomalies=True,
        reproduce_time_limit=5.0,
    )
    assert len(reports) == 1
    assert reports[0].category == "SOLVER_BEHAVIOR"
    assert reports[0].reproduced_status == "OPT"
    assert reports[0].reproduced_lb == 2


def test_triage_cli_returns_zero_when_no_code_bugs(tmp_path):
    inst_dir = tmp_path / "benchmark"
    inst_dir.mkdir()
    write_instance(inst_dir / "path4.json", generator.path(4))

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    rec = _valid_path4_record()
    (raw_dir / "ok.json").write_text(json.dumps(rec), encoding="utf-8")

    exit_code = triage_main(["--raw-dir", str(raw_dir), "--anomalies-only"])
    assert exit_code == 0
