"""Schema một run (CONTRACT.md §7) và các hàm dựng record."""

from __future__ import annotations

import platform
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.models import Config, Instance, Result

# Thứ tự cột của runs.csv. Phần đầu đúng theo CONTRACT §7, phần sau là bổ sung.
RUN_FIELDS = (
    "run_id", "instance", "method", "abp_encoding", "amo_encoding", "solver",
    "search_mode", "status", "lb", "ub", "t_encode", "t_solve", "t_total",
    "variables", "clauses", "peak_memory", "git_tag", "host", "timestamp",
    # bổ sung
    "symmetry", "warm_start", "seed", "time_limit", "memory_limit",
    "wall_time", "error",
)


def make_run_id(instance: Instance, config: Config) -> str:
    """run_id xác định (deterministic): cùng instance + config -> cùng id.

    Nhờ vậy resume bỏ qua run đã xong, và validation phát hiện trùng run_id.
    """
    parts = [
        instance.id, config.method, config.abp_encoding, config.amo_encoding,
        config.sat_solver, config.search_mode,
        f"sym{int(config.symmetry)}", f"ws{int(config.warm_start)}",
        f"s{config.seed}",
    ]
    return "__".join("na" if p is None else str(p) for p in parts)


def git_tag() -> str:
    try:
        out = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True, text=True, timeout=10,
            cwd=Path(__file__).resolve().parents[2],
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def host_name() -> str:
    return platform.node() or "unknown"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def solver_label(config: Config, result: Result | None) -> str:
    """Cột `solver`: SAT thì tên SAT solver, còn lại là tên solver exact."""
    if config.sat_solver:
        return config.sat_solver
    if result is not None and result.metadata.get("solver"):
        return str(result.metadata["solver"])
    return config.method


def build_record(
    instance: Instance,
    config: Config,
    result: Result | None,
    *,
    wall_time: float,
    error: str | None = None,
    status_override: str | None = None,
) -> dict[str, Any]:
    """Gộp instance + config + result thành một record phẳng theo RUN_FIELDS."""
    status = status_override or (result.status if result else "ERR")
    record: dict[str, Any] = {
        "run_id": make_run_id(instance, config),
        "instance": instance.id,
        "method": config.method,
        "abp_encoding": config.abp_encoding,
        "amo_encoding": config.amo_encoding,
        "solver": solver_label(config, result),
        "search_mode": config.search_mode,
        "status": status,
        "lb": result.lb if result else None,
        "ub": result.ub if result else None,
        "t_encode": result.t_encode if result else None,
        "t_solve": result.t_solve if result else None,
        "t_total": result.t_total if result else None,
        "variables": result.variables if result else None,
        "clauses": result.clauses if result else None,
        "peak_memory": result.peak_memory if result else None,
        "git_tag": git_tag(),
        "host": host_name(),
        "timestamp": now_iso(),
        "symmetry": config.symmetry,
        "warm_start": config.warm_start,
        "seed": config.seed,
        "time_limit": config.time_limit,
        "memory_limit": config.memory_limit,
        "wall_time": wall_time,
        "error": error,
    }
    # Phần không phẳng: giữ trong raw JSON, không đưa vào CSV.
    record["config"] = asdict(config)
    record["solution"] = (
        {str(k): v for k, v in result.solution.items()}
        if result and result.solution else None
    )
    record["metadata"] = result.metadata if result else {}
    return record
