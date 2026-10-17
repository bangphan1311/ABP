"""Runner: config -> mỗi run một subprocess -> raw JSON.

Một lần chạy = một (instance, config). Runner:
  1. đọc instance (đồng thời kiểm tra file hợp lệ),
  2. chạy worker trong subprocess có timeout cứng,
  3. verify lại nghiệm một lần nữa ở phía runner (không tin worker),
  4. ghi ``<out_dir>/<run_id>.json`` theo schema.
Hỗ trợ resume: nếu raw JSON của run_id đã tồn tại thì bỏ qua.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

from src.common.models import Config, Result
from src.common.verify import verify
from src.runner.schema import build_record, make_run_id
from src.sat.loader import read_instance

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = REPO_ROOT / "results" / "raw"
# Thời gian dư cho khởi động subprocess/import solver trước khi kill cứng.
KILL_GRACE_SECONDS = 30.0


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

    if resume and out_file.exists():
        return json.loads(out_file.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        cfg_file = Path(tmp) / "config.json"
        res_file = Path(tmp) / "result.json"
        cfg_file.write_text(json.dumps(asdict(config)), encoding="utf-8")

        hard_limit = None if config.time_limit is None else config.time_limit + KILL_GRACE_SECONDS
        start = perf_counter()
        timed_out_hard = False
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "src.runner.worker",
                 str(instance_path), str(cfg_file), str(res_file)],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=hard_limit,
            )
        except subprocess.TimeoutExpired:
            timed_out_hard = True
            proc = None
        wall = perf_counter() - start

        record = _to_record(instance, config, proc, res_file, wall, timed_out_hard)

    out_file.write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return record


def _to_record(instance, config, proc, res_file: Path, wall: float, timed_out_hard: bool):
    if timed_out_hard:
        # Bị kill cứng, không có nghiệm đã verify -> TO (theo CONTRACT §5).
        return build_record(
            instance, config, None, wall_time=wall, status_override="TO",
            error=f"Hết {config.time_limit}s + grace, worker bị kill.",
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
