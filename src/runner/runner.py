"""Runner: config -> mỗi run một subprocess -> raw JSON.

Một lần chạy = một (instance, config). Runner:
  1. đọc instance (đồng thời kiểm tra file hợp lệ),
  2. chạy worker trong subprocess có timeout cứng,
  3. verify lại nghiệm một lần nữa ở phía runner (không tin worker),
  4. ghi ``<out_dir>/<run_id>.json`` theo schema.
Hỗ trợ resume: chỉ skip raw JSON hợp lệ đã khớp run/config và kiểm chứng nghiệm; attempt lỗi được lưu riêng.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from time import perf_counter, time_ns
from typing import Any

from src.common.models import Config, Result
from src.common.checkpoint import load_valid_incumbent_checkpoint
from src.common.verify import verify
from src.runner.memory_limit import (
    WindowsMemoryJob,
    make_posix_memory_preexec,
    memory_limit_to_bytes,
)
from src.runner.schema import RUN_FIELDS, build_record, make_run_id
from src.sat.loader import read_instance

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = REPO_ROOT / "results" / "raw"
# Thời gian dư cho khởi động subprocess/import solver trước khi kill cứng.
KILL_GRACE_SECONDS = 30.0


def _valid_resume_record(path: Path, instance, config: Config, run_id: str) -> dict[str, Any] | None:
    """Validate an existing raw record before allowing resume to skip it."""
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            return None
        if not set(RUN_FIELDS).issubset(record):
            return None
        if record.get("run_id") != run_id or record.get("instance") != instance.id:
            return None
        if record.get("config") != asdict(config):
            return None

        status = record.get("status")
        # ERR is a failed attempt, not a reusable completed result.
        if status not in {"OPT", "FEAS", "TO", "MO"}:
            return None

        raw_solution = record.get("solution")
        if raw_solution is None:
            if status in {"OPT", "FEAS"}:
                return None
            if status in {"TO", "MO"} and record.get("lb") is not None:
                return None
        else:
            if not isinstance(raw_solution, dict):
                return None
            labeling = {int(k): v for k, v in raw_solution.items()}
            if len(labeling) != len(raw_solution):
                return None
            objective = verify(instance, labeling)
            if record.get("lb") != objective:
                return None
            if status == "OPT" and record.get("ub") != objective:
                return None
            if status == "FEAS":
                ub_value = record.get("ub")
                if isinstance(ub_value, bool) or not isinstance(ub_value, int) or ub_value < objective:
                    return None
            if status == "MO" and record.get("ub") is not None:
                if record["ub"] < objective:
                    return None
            if status == "TO":
                return None

        return record
    except (OSError, json.JSONDecodeError, ValueError, TypeError, KeyError):
        return None


def _archive_existing_record(path: Path) -> Path:
    """Move the old attempt outside the active raw-record directory before retry."""
    archive_dir = path.parent / "attempt_history"
    archive_dir.mkdir(parents=True, exist_ok=True)
    target = archive_dir / f"{path.stem}.{time_ns()}.json"
    while target.exists():
        target = archive_dir / f"{path.stem}.{time_ns()}.json"
    path.replace(target)
    return target


def run_one(
    instance_path: str | Path,
    config: Config,
    out_dir: str | Path = DEFAULT_OUT_DIR,
    *,
    resume: bool = False,
) -> dict[str, Any]:
    """Chạy một run, ghi raw JSON, trả về record."""
    instance = read_instance(instance_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(instance, config)
    out_file = out_dir / f"{run_id}.json"
    checkpoint_file = out_dir / "checkpoints" / f"{run_id}.json"
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    if out_file.exists():
        if resume:
            cached = _valid_resume_record(out_file, instance, config, run_id)
            if cached is not None:
                return cached
        # Preserve corrupted/ERR/forced-rerun attempts for audit instead of overwriting.
        _archive_existing_record(out_file)

    with tempfile.TemporaryDirectory() as tmp:
        cfg_file = Path(tmp) / "config.json"
        res_file = Path(tmp) / "result.json"
        cfg_file.write_text(json.dumps(asdict(config)), encoding="utf-8")

        hard_limit = None if config.time_limit is None else config.time_limit + KILL_GRACE_SECONDS
        limit_bytes = memory_limit_to_bytes(config.memory_limit)
        env = os.environ.copy()
        env["ABP_CHECKPOINT_PATH"] = str(checkpoint_file.resolve())
        env["ABP_CHECKPOINT_RUN_ID"] = run_id
        command = [
            sys.executable, "-m", "src.runner.worker",
            str(instance_path), str(cfg_file), str(res_file),
        ]
        popen_kwargs: dict[str, Any] = {
            "cwd": REPO_ROOT,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "env": env,
        }
        memory_job = None
        if limit_bytes is not None:
            if os.name == "nt":
                # Tạo suspended để không có bước chạy solver nào xảy ra trước khi
                # Job Object áp hard limit. Nếu gắn job thất bại, không chạy worker.
                memory_job = WindowsMemoryJob(limit_bytes)
                popen_kwargs["creationflags"] = 0x00000004  # Win32 CREATE_SUSPENDED
            elif os.name == "posix":
                popen_kwargs["preexec_fn"] = make_posix_memory_preexec(limit_bytes)
            else:
                raise OSError(
                    f"memory_limit chưa được hỗ trợ trên OS {os.name!r}; từ chối chạy không giới hạn."
                )

        start = perf_counter()
        timed_out_hard = False
        try:
            proc = subprocess.Popen(command, **popen_kwargs)
            if memory_job is not None:
                memory_job.assign_and_resume(proc)
            try:
                stdout, stderr = proc.communicate(timeout=hard_limit)
            except subprocess.TimeoutExpired:
                timed_out_hard = True
                if memory_job is not None:
                    memory_job.terminate()
                elif proc.poll() is None:
                    proc.kill()
                stdout, stderr = proc.communicate()
            completed = subprocess.CompletedProcess(
                command, proc.returncode, stdout, stderr
            )
            wall = perf_counter() - start
            record = _to_record(
                instance, config, completed, res_file, wall, timed_out_hard,
                checkpoint_file=checkpoint_file, run_id=run_id,
            )
        finally:
            if memory_job is not None:
                memory_job.close()

    out_file.write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return record


def _to_record(
    instance, config, proc, res_file: Path, wall: float, timed_out_hard: bool,
    *, checkpoint_file: Path | None = None, run_id: str | None = None,
):
    if timed_out_hard:
        checkpoint = (
            load_valid_incumbent_checkpoint(checkpoint_file, instance, config, run_id)
            if checkpoint_file is not None and run_id is not None
            else None
        )
        if checkpoint is not None:
            # Checkpoint chỉ cung cấp incumbent FEAS; runner không tự tuyên bố OPT.
            objective = checkpoint["objective"]
            upper_bound = instance.n - 1
            metrics = checkpoint["metrics"]
            result = Result(
                status="FEAS",
                lb=objective,
                ub=upper_bound,
                gap=float(upper_bound - objective),
                t_encode=float(metrics.get("t_encode", 0.0)),
                t_solve=float(metrics.get("t_solve", 0.0)),
                t_total=float(metrics.get("t_total", 0.0)),
                variables=metrics.get("variables"),
                clauses=metrics.get("clauses"),
                peak_memory=metrics.get("peak_memory"),
                solution=checkpoint["solution"],
                metadata={
                    "checkpoint_recovered": True,
                    "checkpoint_version": checkpoint["version"],
                    "checkpoint_updated_at": checkpoint["updated_at"],
                    "checkpoint_file": checkpoint_file.name,
                    "metrics_are_partial": True,
                    "recovery_reason": "worker bị kill cứng trước khi ghi result.json",
                },
            )
            return _recheck(instance, config, result, wall)

        # Không có checkpoint hợp lệ: chỉ khi đó mới trả TO vì chưa có incumbent.
        return build_record(
            instance, config, None, wall_time=wall, status_override="TO",
            error=f"Hết {config.time_limit}s + grace, worker bị kill; không có checkpoint hợp lệ.",
        )

    if not res_file.exists():
        tail = (proc.stderr or "")[-500:] if proc else ""
        return build_record(
            instance, config, None, wall_time=wall,
            error=f"Worker không ghi kết quả (exit={proc.returncode}). {tail}",
        )

    out = json.loads(res_file.read_text(encoding="utf-8"))
    if not out.get("ok"):
        return build_record(instance, config, None, wall_time=wall, error=out.get("error"))

    raw = out["result"]
    if raw.get("status") == "MO" and "t_total" not in raw:
        return build_record(instance, config, None, wall_time=wall,
                            status_override="MO", error="MemoryError")

    sol = raw.get("solution")
    raw["solution"] = {int(k): v for k, v in sol.items()} if sol else None
    result = Result(**raw)
    return _recheck(instance, config, result, wall)


def _recheck(instance, config, result: Result, wall: float) -> dict[str, Any]:
    """Verify độc lập ở runner: nghiệm sai hoặc lb không khớp -> ERR."""
    if result.status in ("OPT", "FEAS"):
        if not result.solution:
            return build_record(instance, config, result, wall_time=wall,
                                status_override="ERR",
                                error=f"{result.status} nhưng không có nghiệm.")
        try:
            value = verify(instance, result.solution)
        except ValueError as exc:
            return build_record(instance, config, result, wall_time=wall,
                                status_override="ERR", error=f"verify thất bại: {exc}")
        if result.lb != value:
            return build_record(
                instance, config, result, wall_time=wall, status_override="ERR",
                error=f"lb={result.lb} khác objective tính lại={value}.")
    return build_record(instance, config, result, wall_time=wall,
                        error=result.metadata.get("error") if result.status == "ERR" else None)
