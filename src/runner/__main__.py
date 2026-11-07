"""CLI: python -m src.runner --instance FILE --method METHOD [...]"""

from __future__ import annotations

import argparse

from src.common.models import Config
from src.runner.runner import DEFAULT_OUT_DIR, run_one


def main() -> int:
    p = argparse.ArgumentParser(description="Chạy một solver trên một instance ABP.")
    p.add_argument("--instance", required=True, help="File instance JSON")
    p.add_argument("--method", required=True, help="oracle | cp_sat | sat | ...")
    p.add_argument("--abp-encoding")
    p.add_argument("--amo-encoding")
    p.add_argument("--sat-solver")
    p.add_argument("--search-mode")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--time-limit", type=float, default=1800.0)
    p.add_argument("--memory-limit", type=float, default=None, help="GiB; áp dụng hard limit cấp OS cho worker")
    p.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    p.add_argument("--resume", action="store_true")
    a = p.parse_args()

    config = Config(
        method=a.method, abp_encoding=a.abp_encoding, amo_encoding=a.amo_encoding,
        sat_solver=a.sat_solver, search_mode=a.search_mode, seed=a.seed,
        time_limit=a.time_limit, memory_limit=a.memory_limit,
    )
    rec = run_one(a.instance, config, a.out, resume=a.resume)
    print(f"{rec['run_id']}: {rec['status']} lb={rec['lb']} ub={rec['ub']} "
          f"t_total={rec['t_total']} wall={rec['wall_time']:.2f}s"
          + (f"  error={rec['error']}" if rec["error"] else ""))
    return 0 if rec["status"] != "ERR" else 1


if __name__ == "__main__":
    raise SystemExit(main())
