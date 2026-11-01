"""Phần dùng chung của hai pilot W3: instance, metric, cảnh báo sớm, CSV.

Mỗi run đi qua ``src.runner.run_one`` (subprocess, schema thống nhất, resume),
nên số liệu pilot cùng nguồn với benchmark chính thức.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any
import argparse

from src.common.models import Config
from src.runner.runner import DEFAULT_OUT_DIR, run_one
from src.sat.backend import DEFAULT_SOLVER

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VALIDATION_DIR = REPO_ROOT / "benchmark" / "validation"
DEFAULT_LARGE_DIR = REPO_ROOT / "benchmark" / "large"
# Ngưỡng cảnh báo sớm: CNF lớn hơn mức này thì quá tải cho pilot/official run.
DEFAULT_MAX_VARS = 200_000
# Encode lâu hơn ngưỡng này (giây) là dấu hiệu encoding không dùng được ở quy mô lớn.
DEFAULT_SLOW_ENCODE = 5.0

# Thứ tự cột summary CSV của cả hai pilot.
FIELDS = (
    "run_id", "instance", "abp_encoding", "amo_encoding", "solver", "status",
    "lb", "ub", "gap", "t_encode", "t_solve", "t_total", "variables", "clauses",
    "peak_memory", "n_probes", "warnings", "error",
)


def base_config(
    *, time_limit: float = 60.0, sat_solver: str = DEFAULT_SOLVER
) -> Config:
    """Cấu hình cố định của pilot: SAT, multi-run K, symmetry/warm start OFF."""
    return Config(
        method="sat",
        sat_solver=sat_solver,
        search_mode="multi",
        symmetry=False,
        warm_start=False,
        seed=0,
        time_limit=time_limit,
    )


def use_utf8_output() -> None:
    """Đổi stdout/stderr sang UTF-8 (Windows redirect mặc định cp1252 sẽ lỗi khi in)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def instance_paths(directory: str | Path) -> list[Path]:
    """Mọi instance JSON trong một thư mục, sắp theo tên (thứ tự chạy cố định).

    Raises:
        ValueError: Nếu thư mục không tồn tại hoặc không có instance nào.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"Không thấy thư mục instance: {directory}.")
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise ValueError(f"Thư mục instance rỗng: {directory}.")
    return paths


def _round6(value: Any) -> float | None:
    return None if value is None else round(float(value), 6)


def add_common_pilot_args(
    parser: argparse.ArgumentParser, *, default_csv: Path
) -> argparse.ArgumentParser:
    """Thêm các cờ CLI dùng chung giữa pilot RQ1 và RQ2."""
    parser.add_argument("--validation-dir", type=Path, default=DEFAULT_VALIDATION_DIR)
    parser.add_argument("--large-dir", type=Path, default=DEFAULT_LARGE_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--csv", type=Path, default=default_csv)
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument("--max-vars", type=int, default=DEFAULT_MAX_VARS)
    parser.add_argument("--slow-encode", type=float, default=DEFAULT_SLOW_ENCODE)
    return parser


def collect_metrics(record: dict[str, Any]) -> dict[str, Any]:
    """Rút metric của một record runner thành một hàng CSV.

    ``gap = ub - lb`` khi có cả hai; ``n_probes`` là số lần dò K
    (``metadata.probes``), tức số lần gọi solver của chiến lược multi-run.
    """
    lb, ub = record.get("lb"), record.get("ub")
    gap = None if lb is None or ub is None else ub - lb
    return {
        "run_id": record.get("run_id"),
        "instance": record.get("instance"),
        "abp_encoding": record.get("abp_encoding"),
        "amo_encoding": record.get("amo_encoding"),
        "solver": record.get("solver"),
        "status": record.get("status"),
        "lb": lb,
        "ub": ub,
        "gap": gap,
        "t_encode": _round6(record.get("t_encode")),
        "t_solve": _round6(record.get("t_solve")),
        "t_total": _round6(record.get("t_total")),
        "variables": record.get("variables"),
        "clauses": record.get("clauses"),
        "peak_memory": _round6(record.get("peak_memory")),
        "n_probes": len((record.get("metadata") or {}).get("probes") or []),
        "warnings": "",
        "error": record.get("error"),
    }


def warning_flags(
    row: dict[str, Any],
    *,
    max_vars: int = DEFAULT_MAX_VARS,
    slow_encode: float = DEFAULT_SLOW_ENCODE,
) -> list[str]:
    """Cảnh báo sớm của pilot: CNF quá lớn, hết bộ nhớ (MO), encode chậm."""
    flags: list[str] = []
    if row.get("status") == "MO":
        flags.append("MO")
    variables = row.get("variables")
    if variables is not None and variables > max_vars:
        flags.append(f"CNF_TOO_LARGE(vars>{max_vars})")
    t_encode = row.get("t_encode")
    if t_encode is not None and t_encode > slow_encode:
        flags.append(f"SLOW_ENCODE(>{slow_encode}s)")
    return flags


def run_pilot(
    paths: Sequence[Path],
    configs: Sequence[Config],
    out_dir: str | Path = DEFAULT_OUT_DIR,
    *,
    max_vars: int = DEFAULT_MAX_VARS,
    slow_encode: float = DEFAULT_SLOW_ENCODE,
    resume: bool = True,
    log: Callable[[str], None] | None = None,
) -> list[dict[str, Any]]:
    """Chạy mọi cặp (instance, config) qua runner; trả các hàng metric.

    ``resume=True`` để raw JSON đã có được dùng lại. Mỗi cảnh báo sớm được ghi
    ngay qua ``log`` (mặc định stderr) thay vì đợi tới cuối.
    """
    emit = log or (lambda message: print(message, file=sys.stderr))
    rows: list[dict[str, Any]] = []
    for path in paths:
        for config in configs:
            row = collect_metrics(run_one(path, config, out_dir, resume=resume))
            flags = warning_flags(row, max_vars=max_vars, slow_encode=slow_encode)
            row["warnings"] = ";".join(flags)
            for flag in flags:
                emit(
                    f"WARNING {row['instance']} "
                    f"{row['abp_encoding']}/{row['amo_encoding']}/{row['solver']}: "
                    f"{flag}"
                )
            rows.append(row)
    return rows


def write_csv(path: str | Path, rows: Iterable[dict[str, Any]]) -> Path:
    """Ghi summary CSV theo ``FIELDS``; tạo thư mục đích nếu chưa có."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in FIELDS})
    return path


def group_counts(
    rows: Iterable[dict[str, Any]], keys: Sequence[str]
) -> dict[tuple[Any, ...], int]:
    """Đếm số run theo bộ cột ``keys`` (in nhanh để đọc kết quả sau pilot)."""
    counts = Counter(tuple(row.get(key) for key in keys) for row in rows)
    return dict(sorted(counts.items(), key=lambda item: str(item[0])))


def status_counts(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Số run theo status (OPT/FEAS/TO/MO/ERR)."""
    counts = Counter(row.get("status") for row in rows)
    return dict(sorted(counts.items()))
