import csv
import json
import subprocess
import sys

from src.runner.schema import RUN_FIELDS

SCRIPT = "scripts/export_runs_csv.py"


def make_record(run_id: str, instance: str = "pores_1", method: str = "sat", status: str = "OPT") -> dict:
    record = {field: None for field in RUN_FIELDS}
    record.update({"run_id": run_id, "instance": instance, "method": method, "status": status, "seed": 0})
    return record


def write_raw(raw_dir, records):
    raw_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        (raw_dir / f"{record['run_id']}.json").write_text(json.dumps(record), encoding="utf-8")


def test_export_writes_run_fields(tmp_path):
    write_raw(tmp_path / "raw", [make_record("a"), make_record("b", method="cplex_cp", status="TO")])

    result = subprocess.run(
        [sys.executable, SCRIPT, "--raw-dir", str(tmp_path / "raw"),
         "--output", str(tmp_path / "runs.csv"), "--expected-runs", "2"],
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    with (tmp_path / "runs.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert [r["run_id"] for r in rows] == ["b", "a"]
    assert list(rows[0]) == list(RUN_FIELDS)


def test_export_rejects_duplicate_run_id(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    for name in ("a", "b"):
        (raw_dir / f"{name}.json").write_text(json.dumps(make_record("dup")), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, SCRIPT, "--raw-dir", str(tmp_path / "raw"), "--output", str(tmp_path / "runs.csv")],
        capture_output=True, text=True,
    )

    assert result.returncode == 2
    assert "duplicate run_id" in result.stderr


def test_export_rejects_wrong_expected_count(tmp_path):
    write_raw(tmp_path / "raw", [make_record("a")])

    result = subprocess.run(
        [sys.executable, SCRIPT, "--raw-dir", str(tmp_path / "raw"),
         "--output", str(tmp_path / "runs.csv"), "--expected-runs", "2"],
        capture_output=True, text=True,
    )

    assert result.returncode == 2
    assert "expected 2 records, found 1" in result.stderr
