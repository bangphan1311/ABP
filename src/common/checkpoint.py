"""Checkpoint nguyên tử cho incumbent đã được verify.

Checkpoint chỉ là bằng chứng phục hồi khi worker bị kill; runner luôn xác minh lại
instance, config và nghiệm trước khi dùng nó.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.models import Config, Instance
from src.common.verify import verify

CHECKPOINT_VERSION = 1
CHECKPOINT_PATH_ENV = "ABP_CHECKPOINT_PATH"
CHECKPOINT_RUN_ID_ENV = "ABP_CHECKPOINT_RUN_ID"
_METRIC_FIELDS = ("t_encode", "t_solve", "t_total", "variables", "clauses", "peak_memory")
_FLOAT_METRICS = {"t_encode", "t_solve", "t_total", "peak_memory"}
_INT_METRICS = {"variables", "clauses"}


def instance_fingerprint(instance: Instance) -> str:
    """Hash đồ thị chuẩn hóa, không phụ thuộc thứ tự hay chiều ghi của cạnh."""
    edges = sorted((min(u, v), max(u, v)) for u, v in instance.edges)
    payload = json.dumps(
        {"n": instance.n, "edges": edges}, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _clean_metrics(metrics: dict[str, Any] | None) -> dict[str, int | float]:
    if metrics is None:
        return {}
    if not isinstance(metrics, dict):
        raise ValueError("metrics của checkpoint phải là object.")
    cleaned: dict[str, int | float] = {}
    for name in _METRIC_FIELDS:
        if name not in metrics or metrics[name] is None:
            continue
        value = metrics[name]
        if name in _FLOAT_METRICS:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or value < 0
            ):
                raise ValueError(f"Metric checkpoint không hợp lệ: {name}.")
            cleaned[name] = float(value)
        elif name in _INT_METRICS:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"Metric checkpoint không hợp lệ: {name}.")
            cleaned[name] = value
    return cleaned


def write_incumbent_checkpoint(
    instance: Instance,
    config: Config,
    *,
    objective: int,
    solution: dict[int, int],
    metrics: dict[str, Any] | None = None,
    path: str | Path | None = None,
    run_id: str | None = None,
) -> bool:
    """Ghi incumbent đã verify vào file tạm rồi atomically thay thế checkpoint.

    Trả False khi checkpoint không được bật (ví dụ chạy solver trực tiếp trong test).
    Lỗi ghi file được cố ý đẩy lên caller để không âm thầm tuyên bố run đã an toàn.
    """
    path_value = path if path is not None else os.environ.get(CHECKPOINT_PATH_ENV)
    run_id_value = run_id if run_id is not None else os.environ.get(CHECKPOINT_RUN_ID_ENV)
    if not path_value and not run_id_value:
        return False
    if not path_value or not run_id_value:
        raise ValueError("Checkpoint cần cả đường dẫn và run_id.")

    if isinstance(objective, bool) or not isinstance(objective, int):
        raise ValueError("Objective checkpoint phải là số nguyên.")
    verified_objective = verify(instance, solution)
    if verified_objective != objective:
        raise ValueError(
            f"Objective checkpoint={objective} khác objective verify={verified_objective}."
        )

    target = Path(path_value)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": CHECKPOINT_VERSION,
        "run_id": run_id_value,
        "instance_id": instance.id,
        "n": instance.n,
        "instance_sha256": instance_fingerprint(instance),
        "config": asdict(config),
        "objective": objective,
        "solution": {str(k): v for k, v in sorted(solution.items())},
        "metrics": _clean_metrics(metrics),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    }

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, target)
    finally:
        try:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        except OSError:
            pass
    return True


def load_valid_incumbent_checkpoint(
    path: str | Path,
    instance: Instance,
    config: Config,
    run_id: str,
) -> dict[str, Any] | None:
    """Đọc checkpoint theo nguyên tắc fail-closed; dữ liệu sai không được phục hồi."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        if payload.get("version") != CHECKPOINT_VERSION:
            return None
        if payload.get("run_id") != run_id or payload.get("instance_id") != instance.id:
            return None
        if payload.get("n") != instance.n:
            return None
        if payload.get("instance_sha256") != instance_fingerprint(instance):
            return None
        if payload.get("config") != asdict(config):
            return None

        objective = payload.get("objective")
        raw_solution = payload.get("solution")
        if isinstance(objective, bool) or not isinstance(objective, int):
            return None
        if not isinstance(raw_solution, dict):
            return None
        solution: dict[int, int] = {}
        for key, value in raw_solution.items():
            if not isinstance(key, str):
                return None
            vertex = int(key)
            if str(vertex) != key or vertex in solution:
                return None
            solution[vertex] = value
        if verify(instance, solution) != objective:
            return None

        metrics = payload.get("metrics")
        cleaned_metrics = _clean_metrics(metrics)
        if metrics != cleaned_metrics:
            # JSON giữ số thực dưới dạng float; chỉ chấp nhận trường metrics chuẩn hóa.
            if not isinstance(metrics, dict):
                return None
            for name, value in metrics.items():
                if name not in _METRIC_FIELDS or value is None:
                    return None
            cleaned_metrics = _clean_metrics(metrics)

        updated_at = payload.get("updated_at")
        if not isinstance(updated_at, str) or not updated_at:
            return None
        return {
            "objective": objective,
            "solution": solution,
            "metrics": cleaned_metrics,
            "updated_at": updated_at,
            "version": CHECKPOINT_VERSION,
        }
    except (OSError, json.JSONDecodeError, ValueError, TypeError, KeyError):
        return None
