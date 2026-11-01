"""Pilot RQ2 (ticket 17 / #24): cùng encoding + AMO, chỉ đổi solver.

Kissat không nằm trong lưới: hạn chế vĩnh viễn W2 (model sai, process abort
qua PySAT, không có binary ngoài). Script in lý do loại trừ khi khởi động và
từ chối mọi tên solver thuộc family kissat.

    python -m experiments.pilot_rq2 --time-limit 60
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

if __package__ in (None, ""):  # cho phép `python experiments/pilot_rq2.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.pilot_common import (
    REPO_ROOT,
    add_common_pilot_args,
    base_config,
    group_counts,
    instance_paths,
    run_pilot,
    status_counts,
    use_utf8_output,
    write_csv,
)
from src.common.models import Config
from src.sat.backend import KISSAT_LIMITATION, PYSAT_KISSAT_FAMILIES, solver_family

# Bốn solver dựng được bằng PySAT trong môi trường này và giới hạn được thời gian.
RQ2_SOLVERS = ("cadical195", "glucose4", "glucose42", "minisat22")
# Tập solver Core trong Experimental Protocol §1 / §4 khi Kissat bị loại.
PROTOCOL_CORE_SOLVERS = ("cadical195", "glucose4")


def solver_note() -> str:
    """Dòng ghi chú in đầu pilot: solver nào chạy, vì sao kissat bị loại."""
    return (
        f"RQ2 solvers: {', '.join(RQ2_SOLVERS)}.\n"
        f"Kissat không được chạy: {KISSAT_LIMITATION}"
    )


def build_rq2_grid(
    base: Config, solvers: tuple[str, ...] | list[str] = RQ2_SOLVERS
) -> list[Config]:
    """Một cấu hình cho mỗi solver; encoding + AMO giữ nguyên từ ``base``.

    Raises:
        ValueError: Nếu danh sách rỗng, hoặc có solver thuộc family kissat.
    """
    if not solvers:
        raise ValueError("RQ2 cần ít nhất một solver.")
    for name in solvers:
        if solver_family(name) in PYSAT_KISSAT_FAMILIES:
            raise ValueError(KISSAT_LIMITATION)
    return [replace(base, sat_solver=name) for name in solvers]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_pilot_args(
        parser, default_csv=REPO_ROOT / "results" / "pilot_rq2.csv"
    )
    parser.add_argument("--abp-encoding", default="pairwise")
    parser.add_argument("--amo-encoding", default="pairwise")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    use_utf8_output()
    print(solver_note())
    base = replace(
        base_config(time_limit=args.time_limit),
        abp_encoding=args.abp_encoding,
        amo_encoding=args.amo_encoding,
    )
    configs = build_rq2_grid(base)
    paths = instance_paths(args.validation_dir) + instance_paths(args.large_dir)
    print(
        f"RQ2: {len(paths)} instance x {len(configs)} solver, "
        f"encoding={args.abp_encoding}/{args.amo_encoding}, "
        f"time_limit={args.time_limit}s"
    )

    rows = run_pilot(
        paths,
        configs,
        args.out_dir,
        max_vars=args.max_vars,
        slow_encode=args.slow_encode,
    )
    print(f"CSV: {write_csv(args.csv, rows)}")
    for (solver, status), count in group_counts(rows, ("solver", "status")).items():
        print(f"  {solver}: {status} = {count}")
    print(f"status: {status_counts(rows)}")

    # Run bất thường để phân loại: không OPT/FEAS, hoặc có cảnh báo/ lỗi.
    for row in rows:
        if row["status"] not in ("OPT", "FEAS") or row["warnings"] or row["error"]:
            detail = "; ".join(
                str(part)
                for part in (row["status"], row["warnings"], row["error"])
                if part
            )
            print(f"  ANOMALY {row['instance']} {row['solver']}: {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
