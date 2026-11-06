"""Run P1's exact W3 pilot on the preflighted Windows host.

Default: 10 locked validation instances × 4 exact methods = 40 runs,
600 seconds per run, one worker at a time, 12 GiB OS-enforced cap.
Optional --include-large adds the four exact methods on the three large
pilot instances (12 more runs, 1800 seconds each). Those runs are separate
from the 40-run validation pilot and must only be enabled after the host's
hard memory-limit test has passed.

All raw records are written by the shared runner. No CSV is hand-edited.
"""
from __future__ import annotations

import argparse
import csv
import ctypes
import platform
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from src.common.models import Config
from src.runner.runner import run_one
from src.sat.loader import read_instance

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "benchmark" / "hb" / "instances.csv"
MANIFEST = ROOT / "benchmark" / "hb" / "MANIFEST.csv"
RAW_DIR = ROOT / "benchmark" / "hb" / "raw"
DEFAULT_OUT = ROOT / "results" / "pilot_exact" / "raw"
SUMMARY = ROOT / "results" / "pilot_exact" / "summary.csv"

VALIDATION_IDS = (
    "pores_1", "bcsstk01", "bcspwr02", "curtis54", "will57",
    "impcol_b", "ash85", "nos4", "dwt_234", "bcspwr03",
)
LARGE_IDS = ("bcsstk06", "nos6", "can_715")
EXACT_METHODS = ("cp_sat", "gurobi_mip", "cplex_mip", "cplex_cp")
PILOT_TIME_LIMIT = 600.0
PILOT_LARGE_TIME_LIMIT = 1800.0
MEMORY_LIMIT_GIB = 12.0
MIN_PHYSICAL_MEMORY_GIB = 15.0
REQUIRED_WINDOWS_BUILD_PREFIX = "10.0.26200"


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def total_physical_memory_gib() -> float:
    """Read physical RAM from Windows without adding a Python dependency."""
    if sys.platform != "win32":
        raise RuntimeError("P1 exact pilot đã khóa cho Windows; không chạy trên OS khác.")
    status = _MemoryStatusEx()
    status.dwLength = ctypes.sizeof(_MemoryStatusEx)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError()
    return status.ullTotalPhys / (1024 ** 3)


def validate_execution_host() -> float:
    """Fail closed if the machine differs materially from the preflighted host."""
    if sys.platform != "win32":
        raise RuntimeError("Official P1 pilot host phải là Windows.")
    if not platform.version().startswith(REQUIRED_WINDOWS_BUILD_PREFIX):
        raise RuntimeError(
            f"Windows build không khớp preflight ({platform.version()}); "
            "chạy preflight và quyết định lại trước khi benchmark."
        )
    ram_gib = total_physical_memory_gib()
    if ram_gib < MIN_PHYSICAL_MEMORY_GIB:
        raise RuntimeError(
            f"RAM chỉ có {ram_gib:.2f} GiB; cần ít nhất "
            f"{MIN_PHYSICAL_MEMORY_GIB:.1f} GiB cho cap {MEMORY_LIMIT_GIB:.1f} GiB "
            "và headroom hệ điều hành."
        )
    return ram_gib


def load_run_plan(*, include_large: bool = False) -> list[tuple[str, Path, str, float]]:
    """Validate the complete 24-row inventory/manifest before launching any solver."""
    with INVENTORY.open(encoding="utf-8-sig", newline="") as stream:
        inventory_rows = list(csv.DictReader(stream))
    with MANIFEST.open(encoding="utf-8-sig", newline="") as stream:
        manifest_rows = list(csv.DictReader(stream))

    if len(inventory_rows) != 24 or len({r["id"] for r in inventory_rows}) != 24:
        raise ValueError("instances.csv phải có đủ 24 instance ID duy nhất.")
    if len(manifest_rows) != 24 or len({r["id"] for r in manifest_rows}) != 24:
        raise ValueError("MANIFEST.csv phải có đủ 24 instance ID duy nhất.")

    inventory = {r["id"]: r for r in inventory_rows}
    manifest = {r["id"]: r for r in manifest_rows}
    selected = list(VALIDATION_IDS) + (list(LARGE_IDS) if include_large else [])
    plan: list[tuple[str, Path, str, float]] = []

    for instance_id in selected:
        if instance_id not in inventory or instance_id not in manifest:
            raise ValueError(f"Không tìm thấy {instance_id} trong inventory/manifest.")
        inv = inventory[instance_id]
        row = manifest[instance_id]
        if row.get("status") not in {"VALID", "VALID_WITH_CLEANING"}:
            raise ValueError(
                f"{instance_id}: manifest status={row.get('status')!r}; "
                "không được chạy pilot."
            )
        if row.get("file") != inv.get("file"):
            raise ValueError(f"{instance_id}: filename không khớp inventory/manifest.")

        source_path = RAW_DIR / inv["file"]
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Thiếu raw benchmark file: {source_path}. "
                "Giải nén đúng bộ Optsicom HB vào benchmark/hb/raw/."
            )

        # read_instance checks SHA-256, header, cleaning counts, degree, UB,
        # plus metadata identity before any solver subprocess is launched.
        instance = read_instance(source_path)
        if instance.id != instance_id or instance.n != int(inv["n"]):
            raise ValueError(
                f"{instance_id}: Instance object không khớp inventory "
                f"(id={instance.id}, n={instance.n})."
            )

        time_limit = (
            PILOT_LARGE_TIME_LIMIT if instance_id in LARGE_IDS else PILOT_TIME_LIMIT
        )
        for method in EXACT_METHODS:
            plan.append((instance_id, source_path, method, time_limit))

    return plan


def write_summary(records: list[dict[str, Any]], output: Path) -> None:
    fields = (
        "run_id", "instance", "method", "solver", "status", "lb", "ub",
        "t_encode", "t_solve", "t_total", "wall_time", "memory_limit",
        "git_tag", "host", "timestamp", "error",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field) for field in fields})
    temp.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-large",
        action="store_true",
        help="thêm 12 exact runs trên bcsstk06, nos6, can__715 sau khi memory gate PASS",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    args = parser.parse_args()

    try:
        ram_gib = validate_execution_host()
        plan = load_run_plan(include_large=args.include_large)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"PRECHECK FAILED: {exc}", file=sys.stderr)
        return 2

    worst_case_seconds = sum(item[3] for item in plan)
    print(
        f"Host={platform.node()} | Windows={platform.version()} | "
        f"RAM={ram_gib:.2f} GiB | workers=1 | memory cap={MEMORY_LIMIT_GIB:.1f} GiB"
    )
    print(
        f"Exact pilot plan: {len(plan)} runs, worst-case "
        f"{worst_case_seconds / 3600:.2f} core-hours; "
        "each run is sequential and resume-enabled."
    )

    records: list[dict[str, Any]] = []
    for index, (instance_id, source_path, method, time_limit) in enumerate(plan, start=1):
        config = Config(
            method=method,
            seed=0,
            time_limit=time_limit,
            memory_limit=MEMORY_LIMIT_GIB,
        )
        record = run_one(source_path, config, args.out_dir, resume=True)
        records.append(record)
        print(
            f"[{index:02d}/{len(plan):02d}] {instance_id:10s} {method:10s} "
            f"{record['status']:4s} lb={record.get('lb')} ub={record.get('ub')} "
            f"wall={record.get('wall_time')}s"
            + (f" error={record.get('error')}" if record.get("error") else "")
        )
        # Keep the derived report current if the process is interrupted.
        write_summary(records, args.summary)

    counts = Counter(record["status"] for record in records)
    print(f"Status counts: {dict(sorted(counts.items()))}")
    print(f"Raw JSON: {args.out_dir}")
    print(f"Derived summary: {args.summary}")
    print("License/edition failures remain ERR; they are never converted to TO.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
