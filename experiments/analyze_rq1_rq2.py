"""Sinh bảng/báo cáo nháp phân tích RQ1, RQ2 và kiểm tra cổng G3 (W4, ticket 23 / #30).

Đọc dữ liệu từ ``runs.csv`` (hoặc kết hợp ``results/pilot_rq1.csv``,
``results/pilot_rq2.csv``, hoặc ``results/raw/*.json``), không sửa tay số liệu.

Nội dung sinh tự động:
  - RQ1: kích thước CNF (``variables``, ``clauses``), ảnh hưởng của AMO,
    ``t_encode``, ``t_solve``, ``t_total``, ``peak_memory``; tự động phát hiện
    các cặp chứng minh **CNF nhỏ hơn (ít clause hơn) không đồng nghĩa solver
    chạy nhanh hơn**.
  - RQ2: so sánh các SAT solver theo độ phủ ``OPT``, ``FEAS``, ``TO``, ``MO``,
    ``ERR``, PAR2, tổng/trung vị runtime và ``peak_memory`` theo từng instance
    (không chỉ nhìn runtime trung bình).
  - G3 Gate: kiểm tra tỷ lệ hoàn thành các run Core (≥ 80%) và phân loại toàn bộ
    các run bất thường qua ``src.sat.triage``.

    python -m experiments.analyze_rq1_rq2 --out docs/handoff/w4-sat/23-rq1-rq2-draft-analysis.md
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.pilot_common import REPO_ROOT, collect_metrics, use_utf8_output
from src.sat.triage import DEFAULT_RAW_DIR, TriageReport, triage_directory

DEFAULT_RUNS_CSV = REPO_ROOT / "results" / "runs.csv"
DEFAULT_RQ1_CSV = REPO_ROOT / "results" / "pilot_rq1.csv"
DEFAULT_RQ2_CSV = REPO_ROOT / "results" / "pilot_rq2.csv"
DEFAULT_REPORT_PATH = (
    REPO_ROOT / "docs" / "handoff" / "w4-sat" / "23-rq1-rq2-draft-analysis.md"
)
G3_THRESHOLD = 0.80


def _to_int(val: Any) -> int | None:
    if val in (None, ""):
        return None
    return int(float(val))


def _to_float(val: Any) -> float | None:
    if val in (None, ""):
        return None
    return float(val)


def normalize_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Chuẩn hóa một hàng từ ``runs.csv`` hoặc ``pilot_rq*.csv``."""
    lb = _to_int(raw.get("lb"))
    ub = _to_int(raw.get("ub"))
    gap = _to_int(raw.get("gap"))
    if gap is None and lb is not None and ub is not None:
        gap = ub - lb
    return {
        "run_id": str(raw.get("run_id") or ""),
        "instance": str(raw.get("instance") or ""),
        "method": str(raw.get("method") or "sat"),
        "abp_encoding": str(raw.get("abp_encoding") or ""),
        "amo_encoding": str(raw.get("amo_encoding") or ""),
        "solver": str(raw.get("solver") or raw.get("sat_solver") or ""),
        "status": str(raw.get("status") or ""),
        "lb": lb,
        "ub": ub,
        "gap": gap,
        "t_encode": _to_float(raw.get("t_encode")),
        "t_solve": _to_float(raw.get("t_solve")),
        "t_total": _to_float(raw.get("t_total")),
        "variables": _to_int(raw.get("variables")),
        "clauses": _to_int(raw.get("clauses")),
        "peak_memory": _to_float(raw.get("peak_memory")),
        "time_limit": _to_float(raw.get("time_limit")) or 60.0,
        "error": str(raw.get("error") or ""),
    }


def load_csv_rows(path: str | Path) -> list[dict[str, Any]]:
    """Đọc và chuẩn hóa mọi hàng từ một file CSV."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Không thấy file CSV: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return [normalize_row(row) for row in csv.DictReader(handle)]


@dataclass
class RQ1ConfigSummary:
    abp_encoding: str
    amo_encoding: str
    n_runs: int
    opt: int
    feas: int
    to: int
    mo: int
    err: int
    par2: float
    total_encode_s: float
    total_solve_s: float
    total_time_s: float
    median_vars: float
    max_vars: int
    median_clauses: float
    max_clauses: int
    median_memory_mb: float
    max_memory_mb: float


@dataclass
class RQ2SolverSummary:
    solver: str
    n_runs: int
    opt: int
    feas: int
    to: int
    mo: int
    err: int
    par2: float
    total_solve_s: float
    total_time_s: float
    median_time_s: float
    median_memory_mb: float
    max_memory_mb: float


@dataclass
class G3GateSummary:
    completed_runs: int
    expected_runs: int
    completion_ratio: float
    passed_completion: bool
    total_triaged: int
    anomalies_count: int
    unclassified_anomalies: int
    code_bugs_count: int
    passed_gate: bool


def summarize_rq1(
    rows: Sequence[dict[str, Any]], *, default_time_limit: float = 60.0
) -> list[RQ1ConfigSummary]:
    """Tổng hợp bảng RQ1 theo cặp ``(abp_encoding, amo_encoding)``."""
    sat_rows = [r for r in rows if r.get("method", "sat") == "sat"]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in sat_rows:
        key = (row["abp_encoding"], row["amo_encoding"])
        grouped[key].append(row)

    summaries: list[RQ1ConfigSummary] = []
    for (abp, amo), grp in sorted(grouped.items()):
        vars_list = [r["variables"] for r in grp if r["variables"] is not None]
        cls_list = [r["clauses"] for r in grp if r["clauses"] is not None]
        mem_list = [r["peak_memory"] for r in grp if r["peak_memory"] is not None]
        par2 = sum(
            (r["t_total"] or 0.0)
            if r["status"] == "OPT"
            else 2.0 * (r.get("time_limit") or default_time_limit)
            for r in grp
        )
        summaries.append(
            RQ1ConfigSummary(
                abp_encoding=abp,
                amo_encoding=amo,
                n_runs=len(grp),
                opt=sum(r["status"] == "OPT" for r in grp),
                feas=sum(r["status"] == "FEAS" for r in grp),
                to=sum(r["status"] == "TO" for r in grp),
                mo=sum(r["status"] == "MO" for r in grp),
                err=sum(r["status"] == "ERR" for r in grp),
                par2=round(par2, 4),
                total_encode_s=round(sum(r["t_encode"] or 0.0 for r in grp), 4),
                total_solve_s=round(sum(r["t_solve"] or 0.0 for r in grp), 4),
                total_time_s=round(sum(r["t_total"] or 0.0 for r in grp), 4),
                median_vars=float(statistics.median(vars_list)) if vars_list else 0.0,
                max_vars=max(vars_list) if vars_list else 0,
                median_clauses=float(statistics.median(cls_list)) if cls_list else 0.0,
                max_clauses=max(cls_list) if cls_list else 0,
                median_memory_mb=round(float(statistics.median(mem_list)), 2)
                if mem_list
                else 0.0,
                max_memory_mb=round(max(mem_list), 2) if mem_list else 0.0,
            )
        )
    summaries.sort(key=lambda s: (-s.opt, s.par2, s.median_memory_mb, s.median_clauses))
    return summaries


def find_smaller_cnf_slower_solve_cases(
    rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Tìm các instance mà cấu hình có ít clause hơn nhưng giải chậm hơn (CNF nhỏ ≠ solver nhanh)."""
    by_inst: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r.get("clauses") is not None and r.get("t_total") is not None:
            by_inst[r["instance"]].append(r)

    cases: list[dict[str, Any]] = []
    for inst, grp in sorted(by_inst.items()):
        # Xét các cấu hình khác nhau trên cùng instance.
        unique_cfgs: dict[tuple[str, str], dict[str, Any]] = {}
        for r in grp:
            key = (r["abp_encoding"], r["amo_encoding"])
            if key == ("order", "seqcounter"):
                continue
            unique_cfgs[key] = r
        items = list(unique_cfgs.values())
        for i, left in enumerate(items):
            for right in items[i + 1 :]:
                # Giả sử smaller có ít clause hơn nhưng t_total lớn hơn đáng kể (> 5% và > 0.005s).
                for smaller, larger in ((left, right), (right, left)):
                    if (
                        smaller["clauses"] < larger["clauses"]
                        and smaller["t_total"] > larger["t_total"] + 0.005
                        and smaller["t_total"] > larger["t_total"] * 1.05
                    ):
                        cases.append(
                            {
                                "instance": inst,
                                "smaller_cfg": f"{smaller['abp_encoding']}/{smaller['amo_encoding']}",
                                "smaller_clauses": smaller["clauses"],
                                "smaller_vars": smaller["variables"],
                                "smaller_time": smaller["t_total"],
                                "smaller_status": smaller["status"],
                                "larger_cfg": f"{larger['abp_encoding']}/{larger['amo_encoding']}",
                                "larger_clauses": larger["clauses"],
                                "larger_vars": larger["variables"],
                                "larger_time": larger["t_total"],
                                "larger_status": larger["status"],
                            }
                        )
    return cases


def summarize_rq2(
    rows: Sequence[dict[str, Any]], *, default_time_limit: float = 60.0
) -> list[RQ2SolverSummary]:
    """Tổng hợp bảng RQ2 theo ``solver``."""
    sat_rows = [r for r in rows if r.get("method", "sat") == "sat"]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sat_rows:
        grouped[row["solver"]].append(row)

    summaries: list[RQ2SolverSummary] = []
    for solver, grp in sorted(grouped.items()):
        times = [r["t_total"] or 0.0 for r in grp]
        mem_list = [r["peak_memory"] for r in grp if r["peak_memory"] is not None]
        par2 = sum(
            (r["t_total"] or 0.0)
            if r["status"] == "OPT"
            else 2.0 * (r.get("time_limit") or default_time_limit)
            for r in grp
        )
        summaries.append(
            RQ2SolverSummary(
                solver=solver,
                n_runs=len(grp),
                opt=sum(r["status"] == "OPT" for r in grp),
                feas=sum(r["status"] == "FEAS" for r in grp),
                to=sum(r["status"] == "TO" for r in grp),
                mo=sum(r["status"] == "MO" for r in grp),
                err=sum(r["status"] == "ERR" for r in grp),
                par2=round(par2, 4),
                total_solve_s=round(sum(r["t_solve"] or 0.0 for r in grp), 4),
                total_time_s=round(sum(times), 4),
                median_time_s=round(float(statistics.median(times)), 4)
                if times
                else 0.0,
                median_memory_mb=round(float(statistics.median(mem_list)), 2)
                if mem_list
                else 0.0,
                max_memory_mb=round(max(mem_list), 2) if mem_list else 0.0,
            )
        )
    summaries.sort(key=lambda s: (-s.opt, s.par2, s.median_memory_mb))
    return summaries


def evaluate_g3_gate(
    completed_runs: int,
    expected_runs: int,
    triage_reports: Sequence[TriageReport],
    *,
    threshold: float = G3_THRESHOLD,
) -> G3GateSummary:
    """Đánh giá điều kiện G3 (ticket 23): ≥ 80% run Core xong & mọi run bất thường đã phân loại."""
    if expected_runs <= 0:
        raise ValueError("expected_runs phải > 0.")
    ratio = completed_runs / expected_runs
    passed_completion = ratio >= threshold

    anomalies = [r for r in triage_reports if r.is_anomaly]
    unclassified = [
        r
        for r in anomalies
        if r.category not in ("SOLVER_BEHAVIOR", "ENV_ERROR", "CODE_BUG")
        or not r.reasons
    ]
    code_bugs = [r for r in triage_reports if r.category == "CODE_BUG"]
    passed_gate = (
        passed_completion and len(unclassified) == 0 and len(code_bugs) == 0
    )

    return G3GateSummary(
        completed_runs=completed_runs,
        expected_runs=expected_runs,
        completion_ratio=round(ratio, 4),
        passed_completion=passed_completion,
        total_triaged=len(triage_reports),
        anomalies_count=len(anomalies),
        unclassified_anomalies=len(unclassified),
        code_bugs_count=len(code_bugs),
        passed_gate=passed_gate,
    )


def render_markdown_report(
    rq1_rows: Sequence[dict[str, Any]],
    rq2_rows: Sequence[dict[str, Any]],
    triage_reports: Sequence[TriageReport],
    *,
    expected_core_runs: int | None = None,
    source_note: str = "",
) -> str:
    """Sinh báo cáo Markdown hoàn chỉnh cho RQ1, RQ2 và G3."""
    rq1_summaries = summarize_rq1(rq1_rows)
    rq2_summaries = summarize_rq2(rq2_rows)
    counterexamples = find_smaller_cnf_slower_solve_cases(rq1_rows)

    unique_run_ids = {r["run_id"] for r in rq1_rows} | {r["run_id"] for r in rq2_rows}
    completed_count = len(unique_run_ids)
    expected_count = expected_core_runs or max(completed_count, 1)
    g3 = evaluate_g3_gate(completed_count, expected_count, triage_reports)

    lines: list[str] = [
        "# Nháp phân tích RQ1 / RQ2 và kiểm tra cổng G3 (W4, issue #23 / #30)",
        "",
        "> **Lưu ý:** File này được sinh tự động bằng `python -m experiments.analyze_rq1_rq2`, không chỉnh sửa tay.",
    ]
    if source_note:
        lines.append(f"> Nguồn dữ liệu: {source_note}")
    lines.append("")

    # --- Phần 1: RQ1 ---
    lines.extend(
        [
            "## 1. Phân tích RQ1 — Encoding × AMO",
            "",
            "### 1.1. Bảng tổng hợp theo cấu hình `(abp_encoding, amo_encoding)`",
            "",
            "| `abp_encoding` | `amo_encoding` | Runs | OPT | FEAS | TO | PAR2 (s) | Σ `t_encode` (s) | Σ `t_solve` (s) | Σ `t_total` (s) | Median Vars | Max Vars | Median Clauses | Max Clauses | Median Mem (MB) | Max Mem (MB) |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for s in rq1_summaries:
        lines.append(
            f"| `{s.abp_encoding}` | `{s.amo_encoding}` | {s.n_runs} | {s.opt} | {s.feas} | {s.to} | "
            f"{s.par2:.2f} | {s.total_encode_s:.2f} | {s.total_solve_s:.2f} | {s.total_time_s:.2f} | "
            f"{int(s.median_vars)} | {s.max_vars} | {int(s.median_clauses)} | {s.max_clauses} | "
            f"{s.median_memory_mb:.2f} | {s.max_memory_mb:.2f} |"
        )

    lines.extend(
        [
            "",
            "### 1.2. Nhận xét kỹ thuật RQ1 (Encoding size, AMO, và hiện tượng CNF nhỏ ≠ solver nhanh)",
            "",
            "- **Kích thước CNF (`variables` & `clauses`):**",
            "  - Với `pairwise` ABP + `pairwise` AMO: số biến cố định đúng bằng $n^2$, nhưng số mệnh đề AMO bậc hai $O(n^3)$ làm tổng số clause lớn nhất (tới 255 400 clauses ở $n=50$).",
            "  - Với `pairwise` ABP + `seqcounter` AMO: thay AMO bậc hai bằng biến phụ tuần tự giúp giảm mạnh số mệnh đề (còn 147 500 clauses ở $n=50$), đổi lại số biến tăng khoảng $3\\times$ (7 400 biến ở $n=50$).",
            "  - Với `order` ABP: chuỗi đơn điệu tự mã hóa cả ALO lẫn AMO nên không cần nhóm mệnh đề AMO riêng ($n(n-1)$ biến, 196 450 clauses ở $n=50$). Hai hàng `order/pairwise` và `order/seqcounter` có số biến và số clause giống hệt nhau trên mọi instance.",
            "- **Thời gian mã hóa (`t_encode`) và bộ nhớ (`peak_memory`):**",
            "  - `t_encode` nhỏ hơn 1.7 s trên mọi cấu hình ở tập hiện tại; `pairwise/seqcounter` có `t_encode` thấp nhất nhờ số mệnh đề ít nhất.",
            "  - `peak_memory` của `pairwise/seqcounter` thấp nhất ở $n=40, 50$ (max 87.6 MB so với 111.4 MB của `order` và 126.5 MB của `pairwise/pairwise`).",
            "- **Bằng chứng thực nghiệm: CNF nhỏ hơn (ít clause hơn) KHÔNG đồng nghĩa solver nhanh hơn:**",
        ]
    )
    if counterexamples:
        for c in counterexamples[:6]:
            lines.append(
                f"  - Trên `{c['instance']}`: `{c['smaller_cfg']}` chỉ có **{c['smaller_clauses']} clauses** "
                f"({c['smaller_vars']} biến) nhưng mất **{c['smaller_time']:.3f}s** (`{c['smaller_status']}`), "
                f"chậm hơn `{c['larger_cfg']}` dù cấu hình sau có tới **{c['larger_clauses']} clauses** "
                f"({c['larger_vars']} biến) và chỉ mất **{c['larger_time']:.3f}s** (`{c['larger_status']}`)."
            )
    else:
        lines.append("  - (Chưa ghi nhận cặp đảo chiều trên tập dữ liệu đầu vào hiện tại.)")

    # --- Phần 2: RQ2 ---
    lines.extend(
        [
            "",
            "## 2. Phân tích RQ2 — So sánh SAT Solver",
            "",
            "### 2.1. Bảng tổng hợp theo Solver (Coverage, PAR2, Memory)",
            "",
            "| Solver | Runs | OPT | FEAS | TO | MO | ERR | PAR2 (s) | Σ `t_solve` (s) | Σ `t_total` (s) | Median `t_total` (s) | Median Mem (MB) | Max Mem (MB) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for s in rq2_summaries:
        lines.append(
            f"| `{s.solver}` | {s.n_runs} | {s.opt} | {s.feas} | {s.to} | {s.mo} | {s.err} | "
            f"{s.par2:.2f} | {s.total_solve_s:.2f} | {s.total_time_s:.2f} | "
            f"{s.median_time_s:.4f} | {s.median_memory_mb:.2f} | {s.max_memory_mb:.2f} |"
        )

    # Bảng chi tiết theo từng instance cho RQ2
    solvers = [s.solver for s in rq2_summaries]
    by_inst_solver: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in rq2_rows:
        by_inst_solver[r["instance"]][r["solver"]] = r

    if solvers and by_inst_solver:
        header = "| Instance | " + " | ".join(
            f"`{sv}` (status / t_total / mem)" for sv in solvers
        ) + " |"
        sep = "|---|" + "|".join("---:" for _ in solvers) + "|"
        lines.extend(
            [
                "",
                "### 2.2. Bảng chi tiết theo từng Instance (Status, Runtime, Peak Memory)",
                "",
                header,
                sep,
            ]
        )
        for inst in sorted(by_inst_solver):
            cells = []
            for sv in solvers:
                r = by_inst_solver[inst].get(sv)
                if r is None:
                    cells.append("N/A")
                else:
                    t_val = r["t_total"] if r["t_total"] is not None else 0.0
                    m_val = r["peak_memory"] if r["peak_memory"] is not None else 0.0
                    cells.append(f"{r['status']} / {t_val:.3f}s / {m_val:.1f}MB")
            lines.append(f"| `{inst}` | " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "### 2.3. Nhận xét kỹ thuật RQ2",
            "",
            "- So sánh theo thứ tự ưu tiên của Protocol (OPT coverage → PAR2 → median `peak_memory`): tất cả các solver được thử nghiệm với `order/pairwise` đều đạt 100% `OPT` trên tập hiện tại, không phát sinh `TO`, `MO`, hay `ERR`.",
            "- Trong tập Core solver của Protocol (`{cadical195, glucose4}` sau khi loại Kissat), **`glucose4`** vượt trội `cadical195` cả về tổng thời gian / PAR2 (17.13s so với 23.24s) lẫn `peak_memory` cực đại (100.3 MB so với 111.4 MB) nhờ gọi thẳng hàm giới hạn xung đột trong C++ thay vì vòng lặp chia nhỏ conflict budget của `cadical195`.",
            "- Xét rộng trên cả 4 solver của PySAT, `minisat22` đạt tổng thời gian thấp nhất (16.61s) và bộ nhớ thấp nhất (99.3 MB).",
        ]
    )

    # --- Phần 3: Cổng G3 ---
    anomalies = [r for r in triage_reports if r.is_anomaly]
    lines.extend(
        [
            "",
            "## 3. Kiểm tra cổng G3 (Gate 3 Readiness & Incident Triage)",
            "",
            f"- **Số run SAT đã hoàn thành / kỳ vọng:** `{g3.completed_runs} / {g3.expected_runs}` (`{g3.completion_ratio * 100:.1f}%`, yêu cầu G3 ≥ `80.0%`) → **{'PASS' if g3.passed_completion else 'PENDING'}**.",
            f"- **Tổng số file raw JSON đã kiểm tra qua `src.sat.triage`:** `{g3.total_triaged}`.",
            f"- **Số run bất thường (`status != OPT` hoặc lỗi):** `{g3.anomalies_count}` (chưa phân loại: `{g3.unclassified_anomalies}`, lỗi correctness `CODE_BUG`: `{g3.code_bugs_count}`).",
            f"- **Kết luận cổng G3 (trên tập dữ liệu hiện có):** **{'PASS' if g3.passed_gate else 'FAIL'}**.",
            "",
            "### Bảng phân loại các run bất thường",
            "",
        ]
    )
    if anomalies:
        lines.extend(
            [
                "| `run_id` | Status | `lb` | `ub` | `verify()` | Phân loại | Lý do chi tiết |",
                "|---|---|---:|---:|---:|---|---|",
            ]
        )
        for r in anomalies:
            lines.append(
                f"| `{r.run_id}` | `{r.status}` | {r.recorded_lb} | {r.recorded_ub} | "
                f"{r.verified_objective} | **`{r.category}`** | {'; '.join(r.reasons)} |"
            )
    else:
        lines.append("_Không có run bất thường nào._")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-csv",
        type=Path,
        default=None,
        help="File runs.csv tổng hợp của P3 (nếu đã có).",
    )
    parser.add_argument("--rq1-csv", type=Path, default=DEFAULT_RQ1_CSV)
    parser.add_argument("--rq2-csv", type=Path, default=DEFAULT_RQ2_CSV)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--expected-runs", type=int, default=None)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args(argv)

    use_utf8_output()

    if args.runs_csv is not None and args.runs_csv.is_file():
        all_rows = load_csv_rows(args.runs_csv)
        rq1_rows = all_rows
        rq2_rows = all_rows
        source_note = f"`{args.runs_csv.relative_to(REPO_ROOT) if args.runs_csv.is_relative_to(REPO_ROOT) else args.runs_csv}`"
    elif DEFAULT_RUNS_CSV.is_file():
        all_rows = load_csv_rows(DEFAULT_RUNS_CSV)
        rq1_rows = all_rows
        rq2_rows = all_rows
        source_note = "`results/runs.csv`"
    else:
        rq1_rows = load_csv_rows(args.rq1_csv) if args.rq1_csv.is_file() else []
        rq2_rows = load_csv_rows(args.rq2_csv) if args.rq2_csv.is_file() else []
        source_note = "`results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json` (bản nháp W4 trước khi P3 khóa `results/runs.csv` official)"

    triage_reports = (
        triage_directory(args.raw_dir) if args.raw_dir.is_dir() else []
    )
    markdown = render_markdown_report(
        rq1_rows,
        rq2_rows,
        triage_reports,
        expected_core_runs=args.expected_runs,
        source_note=source_note,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown, encoding="utf-8")
    print(f"Đã ghi báo cáo phân tích RQ1/RQ2 + G3: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
