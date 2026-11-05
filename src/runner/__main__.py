"""CLI: python -m src.runner --instance FILE --method METHOD [...]"""

from __future__ import annotations

import argparse
import sys

from src.common.models import Config
from src.runner.runner import DEFAULT_OUT_DIR, run_one


def _render(value: object) -> str:
    """Render giá trị cho dòng DRY_RUN: None -> none, bool -> true/false."""
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _make_lossy_safe(stream) -> None:
    """Console cp1252 không mã hoá được tiếng Việt: cho phép thay thế."""
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(errors="replace")
    except (ValueError, OSError):
        pass


def _make_stderr_lossy_safe() -> None:
    _make_lossy_safe(sys.stderr)


def _print_dry_run(rec: dict) -> None:
    info = rec["dry_run"]
    cfg = rec["config"]
    print(f"DRY_RUN run_id={rec['run_id']}")
    print(f"DRY_RUN instance={rec['instance']} n={info['n']} m={info['m']}")
    print(
        "DRY_RUN config "
        f"method={_render(cfg['method'])} "
        f"abp_encoding={_render(cfg['abp_encoding'])} "
        f"amo_encoding={_render(cfg['amo_encoding'])} "
        f"sat_solver={_render(cfg['sat_solver'])} "
        f"search_mode={_render(cfg['search_mode'])} "
        f"symmetry={_render(cfg['symmetry'])} "
        f"warm_start={_render(cfg['warm_start'])} "
        f"seed={_render(cfg['seed'])}"
    )
    print(
        "DRY_RUN budget "
        f"time_limit={_render(cfg['time_limit'])} "
        f"hard_limit={_render(info['hard_limit'])} "
        f"memory_limit={_render(cfg['memory_limit'])} "
        "memory_limit_enforced=false"
    )
    print(
        "DRY_RUN output "
        f"out_file={info['out_file']} "
        f"exists={_render(info['exists'])} "
        f"resume_would_skip={_render(info['resume_would_skip'])}"
    )


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
    p.add_argument("--memory-limit", type=float, default=None)
    p.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    p.add_argument("--resume", action="store_true")
    p.add_argument("--dry-run", action="store_true",
                   help="Chỉ báo cáo run_id/budget/resume; không chạy solver.")
    a = p.parse_args()

    config = Config(
        method=a.method, abp_encoding=a.abp_encoding, amo_encoding=a.amo_encoding,
        sat_solver=a.sat_solver, search_mode=a.search_mode, seed=a.seed,
        time_limit=a.time_limit, memory_limit=a.memory_limit,
    )
    if a.dry_run:
        # --out có thể chứa ký tự non-ASCII; console cp1252 phải không crash.
        _make_lossy_safe(sys.stdout)
        try:
            rec = run_one(a.instance, config, a.out, resume=a.resume,
                          dry_run=True)
        except (ValueError, OSError) as exc:
            _make_stderr_lossy_safe()
            print(f"DRY_RUN ERROR: {exc}", file=sys.stderr)
            return 2
        _print_dry_run(rec)
        return 0

    rec = run_one(a.instance, config, a.out, resume=a.resume)
    print(f"{rec['run_id']}: {rec['status']} lb={rec['lb']} ub={rec['ub']} "
          f"t_total={rec['t_total']} wall={rec['wall_time']:.2f}s"
          + (f"  error={rec['error']}" if rec["error"] else ""))
    return 0 if rec["status"] != "ERR" else 1


if __name__ == "__main__":
    raise SystemExit(main())
