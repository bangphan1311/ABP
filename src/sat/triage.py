"""Trực lỗi SAT khi chạy thực nghiệm (W4, ticket 22 / #29).

Quy trình kiểm tra một run SAT từ raw JSON của runner:
  1. Đọc raw record → dựng lại ``Config`` và tìm ``Instance``.
  2. Kiểm tra nghiệm ``solution`` qua ``verify(instance, labeling)`` và đối chiếu
     với ``lb``, ``ub``, chuỗi ``metadata.probes`` (không chỉ nhìn exit code hay status).
  3. Phân loại nguyên nhân thành 3 nhóm chuẩn của ticket 22:
     - ``OK``: run bình thường (``OPT`` thỏa mọi điều kiện).
     - ``SOLVER_BEHAVIOR``: hành vi solver thật (``FEAS`` hoặc ``TO`` hết giờ bình thường,
       nghiệm nếu có vẫn qua ``verify()`` và ``lb < ub``).
     - ``ENV_ERROR``: lỗi môi trường / hệ thống (JSON hỏng, thiếu file instance,
       ``MO`` hết bộ nhớ, worker bị kill cứng chưa kịp ghi kết quả, lỗi giấy phép/backend).
     - ``CODE_BUG``: lỗi correctness trong encoding / decode / K-search (nghiệm không qua
       ``verify()``, ``lb`` khác giá trị tính lại, ``lb > ub``, ``OPT`` thiếu nghiệm hoặc
       mâu thuẫn ``probes``).
  4. Tái hiện trên máy dev (``reproduce_on_dev``): chạy trực tiếp ``solve_sat`` trong
     bộ nhớ với ``time_limit`` nhỏ, không ghi vào ``results/raw/`` để tránh làm bẩn
     dữ liệu official.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.common.models import Config, Instance, Result
from src.common.verify import verify
from src.sat.loader import read_instance
from src.sat.solve import solve_sat

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = REPO_ROOT / "results" / "raw"
DEFAULT_BENCHMARK_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "benchmark" / "validation",
    REPO_ROOT / "benchmark" / "large",
    REPO_ROOT / "benchmark" / "toy",
    REPO_ROOT / "benchmark" / "hb",
    REPO_ROOT / "docs" / "handoff" / "sat-g1" / "instances",
)

TriageCategory = Literal["OK", "SOLVER_BEHAVIOR", "ENV_ERROR", "CODE_BUG"]

_ENV_ERROR_MARKERS = (
    "MemoryError",
    "worker bị kill",
    "Worker không ghi kết quả",
    "BackendError",
    "PermissionError",
    "FileNotFoundError",
    "OSError",
    "license",
)


@dataclass
class TriageReport:
    """Báo cáo phân loại một run SAT."""

    run_id: str
    instance_id: str | None
    status: str | None
    category: TriageCategory
    is_anomaly: bool
    verified_objective: int | None = None
    recorded_lb: int | None = None
    recorded_ub: int | None = None
    reasons: list[str] = field(default_factory=list)
    reproduced_status: str | None = None
    reproduced_lb: int | None = None
    reproduced_ub: int | None = None


def find_instance(
    instance_id: str,
    search_dirs: Sequence[str | Path] = DEFAULT_BENCHMARK_DIRS,
) -> Instance | None:
    """Tìm và đọc ``Instance`` theo ``instance_id`` trong các thư mục benchmark."""
    for base in search_dirs:
        candidate = Path(base) / f"{instance_id}.json"
        if candidate.is_file():
            return read_instance(candidate)
    return None


def _parse_solution(raw_solution: Any) -> dict[int, int] | None:
    """Chuyển dict nghiệm JSON ``{"0": 1, ...}`` sang ``{0: 1, ...}``."""
    if raw_solution is None:
        return None
    if not isinstance(raw_solution, dict):
        raise ValueError(f"solution không phải dict: {type(raw_solution).__name__}")
    parsed: dict[int, int] = {}
    for k, v in raw_solution.items():
        if isinstance(k, bool) or isinstance(v, bool):
            raise ValueError("Khóa hoặc nhãn là bool, không hợp lệ.")
        parsed[int(k)] = int(v)
    return parsed


def _is_env_error_text(error_text: str) -> bool:
    lowered = error_text.lower()
    return any(marker.lower() in lowered for marker in _ENV_ERROR_MARKERS)


def inspect_record(
    record: dict[str, Any],
    *,
    instance: Instance | None = None,
    search_dirs: Sequence[str | Path] = DEFAULT_BENCHMARK_DIRS,
) -> TriageReport:
    """Kiểm tra sâu một raw record SAT: decode -> verify -> đối chiếu lb/ub/probes."""
    run_id = str(record.get("run_id") or "unknown")
    instance_id = record.get("instance")
    status = record.get("status")
    lb = record.get("lb")
    ub = record.get("ub")
    error_msg = str(record.get("error") or "")
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    probes = metadata.get("probes") if isinstance(metadata.get("probes"), list) else []

    reasons: list[str] = []

    if status not in ("OPT", "FEAS", "TO", "MO", "ERR"):
        return TriageReport(
            run_id=run_id,
            instance_id=instance_id,
            status=str(status),
            category="CODE_BUG",
            is_anomaly=True,
            recorded_lb=lb,
            recorded_ub=ub,
            reasons=[f"Trạng thái không hợp lệ theo CONTRACT: {status!r}."],
        )

    if instance is None and isinstance(instance_id, str):
        try:
            instance = find_instance(instance_id, search_dirs=search_dirs)
        except Exception as exc:
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="ENV_ERROR",
                is_anomaly=True,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[f"Không đọc được file instance '{instance_id}': {exc}"],
            )

    # Kiểm tra nghiệm nếu có hoặc nếu status đòi hỏi phải có nghiệm.
    verified_obj: int | None = None
    raw_sol = record.get("solution")
    if raw_sol is not None:
        try:
            solution = _parse_solution(raw_sol)
        except Exception as exc:
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="CODE_BUG",
                is_anomaly=True,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[f"Giải mã định dạng solution thất bại: {exc}"],
            )
        if instance is None:
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="ENV_ERROR",
                is_anomaly=True,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[f"Thiếu file instance '{instance_id}' để chạy verify()."],
            )
        try:
            verified_obj = verify(instance, solution)
        except Exception as exc:
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="CODE_BUG",
                is_anomaly=True,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[f"Nghiệm vi phạm verify(): {exc}"],
            )

    # Đối chiếu quy tắc bất biến của từng status.
    if status in ("OPT", "FEAS"):
        if raw_sol is None:
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="CODE_BUG",
                is_anomaly=True,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[f"Status {status} nhưng không có solution."],
            )
        if lb != verified_obj:
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="CODE_BUG",
                is_anomaly=True,
                verified_objective=verified_obj,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[
                    f"Objective tính lại ({verified_obj}) khác lb đã ghi ({lb})."
                ],
            )
        if ub is None or lb > ub:
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="CODE_BUG",
                is_anomaly=True,
                verified_objective=verified_obj,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[f"Cận mâu thuẫn: lb={lb}, ub={ub}."],
            )
        if status == "OPT" and lb != ub:
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="CODE_BUG",
                is_anomaly=True,
                verified_objective=verified_obj,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[f"Status OPT nhưng lb={lb} != ub={ub}."],
            )

    # Kiểm tra tính nhất quán của chuỗi probe K nếu là SAT.
    for probe in probes:
        if not isinstance(probe, dict):
            continue
        p_status = probe.get("status")
        p_k = probe.get("k")
        p_b = probe.get("b")
        if p_status == "SAT" and isinstance(p_k, int) and isinstance(p_b, int):
            if p_b < p_k:
                return TriageReport(
                    run_id=run_id,
                    instance_id=instance_id,
                    status=status,
                    category="CODE_BUG",
                    is_anomaly=True,
                    verified_objective=verified_obj,
                    recorded_lb=lb,
                    recorded_ub=ub,
                    reasons=[
                        f"Probe K={p_k} trả SAT nhưng đạt B={p_b} < K (lỗi encoding)."
                    ],
                )
        if (
            p_status == "UNSAT"
            and isinstance(p_k, int)
            and verified_obj is not None
            and p_k <= verified_obj
        ):
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="CODE_BUG",
                is_anomaly=True,
                verified_objective=verified_obj,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[
                    f"Probe K={p_k} trả UNSAT nhưng đã có nghiệm verify đạt {verified_obj} >= K."
                ],
            )

    if status == "MO":
        reasons.append(error_msg or "Vượt giới hạn bộ nhớ (MO).")
        return TriageReport(
            run_id=run_id,
            instance_id=instance_id,
            status=status,
            category="ENV_ERROR",
            is_anomaly=True,
            verified_objective=verified_obj,
            recorded_lb=lb,
            recorded_ub=ub,
            reasons=reasons,
        )

    if status == "ERR":
        meta_err = str(metadata.get("error") or "")
        combined_err = "; ".join(part for part in (error_msg, meta_err) if part)
        if _is_env_error_text(combined_err):
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="ENV_ERROR",
                is_anomaly=True,
                verified_objective=verified_obj,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[combined_err or "Lỗi môi trường / subprocess."],
            )
        return TriageReport(
            run_id=run_id,
            instance_id=instance_id,
            status=status,
            category="CODE_BUG",
            is_anomaly=True,
            verified_objective=verified_obj,
            recorded_lb=lb,
            recorded_ub=ub,
            reasons=[combined_err or "Status ERR từ solver/encoding."],
        )

    if status == "TO":
        if raw_sol is not None:
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="CODE_BUG",
                is_anomaly=True,
                verified_objective=verified_obj,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=["Status TO nhưng vẫn chứa solution (phải là FEAS hoặc None)."],
            )
        if "license" in error_msg.lower():
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="CODE_BUG",
                is_anomaly=True,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=[
                    f"Lỗi giấy phép bị ghi nhầm thành TO (vi phạm CONTRACT §5): {error_msg}"
                ],
            )
        if _is_env_error_text(error_msg):
            reasons.append(error_msg)
            return TriageReport(
                run_id=run_id,
                instance_id=instance_id,
                status=status,
                category="ENV_ERROR",
                is_anomaly=True,
                recorded_lb=lb,
                recorded_ub=ub,
                reasons=reasons,
            )
        reasons.append("Hết thời gian trước khi tìm được nghiệm đầu tiên.")
        return TriageReport(
            run_id=run_id,
            instance_id=instance_id,
            status=status,
            category="SOLVER_BEHAVIOR",
            is_anomaly=True,
            recorded_lb=lb,
            recorded_ub=ub,
            reasons=reasons,
        )

    if status == "FEAS":
        reasons.append(
            f"Hết giờ sau khi đã verify incumbent lb={lb}, ub={ub} (gap={ub - lb})."
        )
        return TriageReport(
            run_id=run_id,
            instance_id=instance_id,
            status=status,
            category="SOLVER_BEHAVIOR",
            is_anomaly=True,
            verified_objective=verified_obj,
            recorded_lb=lb,
            recorded_ub=ub,
            reasons=reasons,
        )

    # status == "OPT" và mọi kiểm tra đều đạt.
    return TriageReport(
        run_id=run_id,
        instance_id=instance_id,
        status=status,
        category="OK",
        is_anomaly=False,
        verified_objective=verified_obj,
        recorded_lb=lb,
        recorded_ub=ub,
        reasons=["Nghiệm hợp lệ, lb == ub == verify(solution)."],
    )


def inspect_raw_file(
    raw_path: str | Path,
    *,
    search_dirs: Sequence[str | Path] = DEFAULT_BENCHMARK_DIRS,
) -> TriageReport:
    """Đọc một file raw JSON và trả ``TriageReport`` (bắt cả lỗi JSON hỏng)."""
    path = Path(raw_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return TriageReport(
            run_id=path.stem,
            instance_id=None,
            status="ERR",
            category="ENV_ERROR",
            is_anomaly=True,
            reasons=[f"File JSON hỏng hoặc không đọc được ({path.name}): {exc}"],
        )
    if not isinstance(payload, dict):
        return TriageReport(
            run_id=path.stem,
            instance_id=None,
            status="ERR",
            category="ENV_ERROR",
            is_anomaly=True,
            reasons=[f"Nội dung JSON không phải object ({path.name})."],
        )
    return inspect_record(payload, search_dirs=search_dirs)


def reproduce_on_dev(
    record: dict[str, Any],
    *,
    instance: Instance | None = None,
    time_limit: float = 5.0,
    search_dirs: Sequence[str | Path] = DEFAULT_BENCHMARK_DIRS,
) -> Result:
    """Tái hiện một run SAT trực tiếp trong bộ nhớ trên máy dev (không ghi file official).

    Dùng lại đúng ``abp_encoding``, ``amo_encoding``, ``sat_solver`` của record
    với ``time_limit`` giới hạn để kiểm tra crash / lỗi decode / mâu thuẫn cận.
    """
    instance_id = record.get("instance")
    if instance is None:
        if not isinstance(instance_id, str):
            raise ValueError("Record không có tên instance hợp lệ.")
        instance = find_instance(instance_id, search_dirs=search_dirs)
        if instance is None:
            raise FileNotFoundError(f"Không tìm thấy instance '{instance_id}'.")

    raw_cfg = record.get("config") if isinstance(record.get("config"), dict) else {}
    config = Config(
        method="sat",
        abp_encoding=raw_cfg.get("abp_encoding") or record.get("abp_encoding"),
        amo_encoding=raw_cfg.get("amo_encoding") or record.get("amo_encoding"),
        sat_solver=raw_cfg.get("sat_solver") or record.get("solver"),
        search_mode=raw_cfg.get("search_mode") or record.get("search_mode") or "multi",
        symmetry=bool(raw_cfg.get("symmetry", record.get("symmetry", False))),
        warm_start=bool(raw_cfg.get("warm_start", record.get("warm_start", False))),
        seed=int(raw_cfg.get("seed", record.get("seed", 0)) or 0),
        time_limit=time_limit,
    )
    return solve_sat(instance, config)


def triage_directory(
    raw_dir: str | Path = DEFAULT_RAW_DIR,
    *,
    search_dirs: Sequence[str | Path] = DEFAULT_BENCHMARK_DIRS,
    reproduce_anomalies: bool = False,
    reproduce_time_limit: float = 5.0,
) -> list[TriageReport]:
    """Quét toàn bộ ``*.json`` trong ``raw_dir``, phân loại các run SAT."""
    raw_dir = Path(raw_dir)
    if not raw_dir.is_dir():
        raise ValueError(f"Không thấy thư mục raw: {raw_dir}")

    reports: list[TriageReport] = []
    for path in sorted(raw_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            reports.append(inspect_raw_file(path, search_dirs=search_dirs))
            continue

        if isinstance(payload, dict) and payload.get("method") not in (None, "sat"):
            continue

        report = inspect_record(payload, search_dirs=search_dirs)
        if reproduce_anomalies and report.is_anomaly and isinstance(payload, dict):
            try:
                dev_res = reproduce_on_dev(
                    payload,
                    time_limit=reproduce_time_limit,
                    search_dirs=search_dirs,
                )
                report.reproduced_status = dev_res.status
                report.reproduced_lb = dev_res.lb
                report.reproduced_ub = dev_res.ub
            except Exception as exc:
                report.reproduced_status = f"EXC:{type(exc).__name__}"
                report.reasons.append(f"Dev reproduce exception: {exc}")
        reports.append(report)
    return reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument(
        "--reproduce",
        action="store_true",
        help="Tái hiện các run bất thường trên máy dev (in-memory, không ghi file).",
    )
    parser.add_argument("--reproduce-time-limit", type=float, default=5.0)
    parser.add_argument(
        "--anomalies-only",
        action="store_true",
        help="Chỉ in các run khác OK.",
    )
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    reports = triage_directory(
        args.raw_dir,
        reproduce_anomalies=args.reproduce,
        reproduce_time_limit=args.reproduce_time_limit,
    )
    anomalies = [r for r in reports if r.is_anomaly]
    code_bugs = [r for r in reports if r.category == "CODE_BUG"]

    print(
        f"Triage SAT: tổng {len(reports)} run | "
        f"OK={sum(r.category == 'OK' for r in reports)} | "
        f"SOLVER_BEHAVIOR={sum(r.category == 'SOLVER_BEHAVIOR' for r in reports)} | "
        f"ENV_ERROR={sum(r.category == 'ENV_ERROR' for r in reports)} | "
        f"CODE_BUG={len(code_bugs)}"
    )

    shown = anomalies if args.anomalies_only else reports
    for r in shown:
        if not args.anomalies_only and not r.is_anomaly:
            continue
        reason_str = "; ".join(r.reasons)
        repro_str = (
            f" -> dev={r.reproduced_status}(lb={r.reproduced_lb},ub={r.reproduced_ub})"
            if r.reproduced_status
            else ""
        )
        print(
            f"  [{r.category}] {r.run_id}: status={r.status} "
            f"lb={r.recorded_lb} ub={r.recorded_ub} "
            f"verified={r.verified_objective} | {reason_str}{repro_str}"
        )

    return 1 if code_bugs else 0


if __name__ == "__main__":
    raise SystemExit(main())
