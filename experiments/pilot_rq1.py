"""Pilot RQ1 (ticket 16 / #23): lưới 2x2 ``abp_encoding`` x ``amo_encoding``.

Cố định một solver (mặc định ``cadical195``), multi-run K search, symmetry OFF,
warm start OFF. Mỗi ô của lưới là một ``Config``; mọi kết quả đi qua
``src.runner.run_one`` nên raw JSON nằm ở ``results/raw/`` và metric ghi vào
``results/pilot_rq1.csv``.

    python -m experiments.pilot_rq1 --time-limit 60
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

if __package__ in (None, ""):  # cho phép `python experiments/pilot_rq1.py`
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
from src.sat.solve import ABP_ENCODINGS

# Hai trục của lưới. ``order`` không có ràng buộc AMO (ticket 05), nên hai ô
# order x {pairwise, seqcounter} phải giống nhau — đó là kết quả cần ghi lại.
AMO_ENCODINGS = ("pairwise", "seqcounter")
# Ba cấu hình CNF thực sự khác nhau theo Experimental Protocol §4 / §9.1.
UNIQUE_ENCODING_PAIRS = (
    ("pairwise", "pairwise"),
    ("pairwise", "seqcounter"),
    ("order", "pairwise"),
)


def build_rq1_grid(base: Config, *, unique_only: bool = False) -> list[Config]:
    """Lưới 2x2 (4 cấu hình) hoặc 3 cấu hình CNF duy nhất (``unique_only=True``)."""
    pairs = (
        UNIQUE_ENCODING_PAIRS
        if unique_only
        else tuple((abp, amo) for abp in ABP_ENCODINGS for amo in AMO_ENCODINGS)
    )
    return [
        replace(base, abp_encoding=abp, amo_encoding=amo) for abp, amo in pairs
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_pilot_args(
        parser, default_csv=REPO_ROOT / "results" / "pilot_rq1.csv"
    )
    parser.add_argument("--solver", default="cadical195")
    parser.add_argument(
        "--unique-cnf-only",
        action="store_true",
        help="Bỏ ô order x seqcounter trùng CNF với order x pairwise (Protocol §4).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    use_utf8_output()
    paths = instance_paths(args.validation_dir) + instance_paths(args.large_dir)
    configs = build_rq1_grid(
        base_config(time_limit=args.time_limit, sat_solver=args.solver),
        unique_only=args.unique_cnf_only,
    )
    print(
        f"RQ1: {len(paths)} instance x {len(configs)} cấu hình, "
        f"solver={args.solver}, time_limit={args.time_limit}s"
    )

    rows = run_pilot(
        paths,
        configs,
        args.out_dir,
        max_vars=args.max_vars,
        slow_encode=args.slow_encode,
    )
    print(f"CSV: {write_csv(args.csv, rows)}")
    for (abp, amo, status), count in group_counts(
        rows, ("abp_encoding", "amo_encoding", "status")
    ).items():
        print(f"  {abp}/{amo}: {status} = {count}")
    print(f"status: {status_counts(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
