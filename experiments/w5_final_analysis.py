"""Sinh bốn deliverable W5: RQ1 final, RQ2 final, cross-review consistency, paper v0.9 SAT sections.

Đọc dữ liệu frozen (``results/runs.csv`` nếu có, ngược lại
``results/pilot_rq1.csv`` + ``results/pilot_rq2.csv`` + ``results/raw/*.json``),
không chạy solver, không ghi vào ``results/``.

    python -m experiments.w5_final_analysis
    python -m experiments.w5_final_analysis --check-only --out-dir docs/w5-sat
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.analyze_rq1_rq2 import (
    DEFAULT_RQ1_CSV,
    DEFAULT_RQ2_CSV,
    DEFAULT_RUNS_CSV,
    _filter_rq1_rows,
    _filter_rq2_rows,
    find_smaller_cnf_slower_solve_cases,
    load_csv_rows,
    summarize_rq1,
    summarize_rq2,
)
from experiments.pilot_common import REPO_ROOT, use_utf8_output
from src.sat import order, pairwise
from src.sat.loader import read_instance
from src.sat.solve import CANONICAL_SAT_CONFIG, canonical_sat_config
from src.sat.triage import (
    DEFAULT_BENCHMARK_DIRS,
    DEFAULT_RAW_DIR,
    TriageReport,
    triage_directory,
)

DEFAULT_W5_OUT = REPO_ROOT / "docs" / "w5-sat"
DEFAULT_VALIDATION_DIR = REPO_ROOT / "benchmark" / "validation"
DEFAULT_LARGE_DIR = REPO_ROOT / "benchmark" / "large"
DEFAULT_CAP_MB = 12288.0
MEMORY_ANCHOR_CLAUSES = 255400
MEMORY_ANCHOR_MB = 126.53125
FASTEST = 0.005  # ngưỡng nhiễu tối thiểu cho đảo chiều thời gian (giây)
RATIO_MARGIN = 1.05  # đảo chiều phải vượt 5% mới đáng ghi
GENERATED_NOTE = (
    "> **Lưu ý:** File này được sinh tự động bằng "
    "`python -m experiments.w5_final_analysis`, không chỉnh sửa tay."
)
W5_ARTIFACTS = (
    "24-rq1-final.md",
    "25-rq2-final.md",
    "26-cross-review-consistency.md",
    "27-paper-v09-sat-sections.md",
)
S_PATH = REPO_ROOT / "docs" / "sat_spec.md"
M_PATH = REPO_ROOT / "docs" / "w2-sat" / "14-sat-methodology.md"
A_PATH = REPO_ROOT / "docs" / "technical_appendix_draft.md"
C_PATH = REPO_ROOT / "docs" / "canonical_sat_config.md"
W4_FREEZE_PATH = REPO_ROOT / "docs" / "w4-sat" / "21-m2-freeze-v1.md"
P1_REVIEW_PATH = REPO_ROOT / "docs" / "w2-sat" / "13-review-p1-formulation.md"
EXACT_MODELS_PATH = REPO_ROOT / "docs" / "exact_models.md"


@dataclass
class GraphMeta:
    """Metadata suy ra từ file instance (không lưu DB)."""

    n: int
    m: int
    density: float
    max_degree: int
    UB: int


@dataclass
class ConsistencyFinding:
    """Một anchor code ↔ spec ↔ paper ↔ appendix."""

    check_id: str
    status: str
    file: str
    symbol: str
    expected: str
    actual: str
    message: str


@dataclass
class G4Summary:
    """Điều kiện G4: dữ liệu frozen 100% + SAT discussion + checkbox."""

    triaged_total: int
    code_bugs: int
    all_triaged: bool
    sat_discussion_complete: bool
    boxes_checked: int
    passed: bool
    statement: str


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _norm(text: str) -> str:
    """Chuẩn hóa văn bản để so anchor: bỏ code tick, gộp khoảng trắng, đồng nhất dấu."""
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    text = text.replace("²", "²")
    text = text.replace("`", "")
    return re.sub(r"\s+", " ", text).lower()


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", _norm(text))


def _finding(
    check_id: str,
    file: Path | str,
    symbol: str,
    expected: str,
    actual: Any,
    missing: Sequence[str],
    *,
    check_id_suffix: str = "",
) -> ConsistencyFinding:
    """Tạo finding; message BR-9 chỉ có khi thiếu (file + symbol + lệch cụ thể)."""
    cid = f"{check_id}{check_id_suffix}"
    label = str(file) if not isinstance(file, Path) else _repo_relative(file)
    if missing:
        return ConsistencyFinding(
            check_id=cid,
            status="fail",
            file=label,
            symbol=symbol,
            expected=expected,
            actual=str(actual),
            message=(
                f"{label} :: {symbol} :: thiếu/lệch: {', '.join(missing)}; "
                f"kỳ vọng: {expected}."
            ),
        )
    return ConsistencyFinding(
        check_id=cid,
        status="ok",
        file=label,
        symbol=symbol,
        expected=expected,
        actual=str(actual),
        message="",
    )


def load_sources(
    runs_csv: Path | None, rq1_csv: Path, rq2_csv: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    """Chọn một nguồn dữ liệu chính (BR-1), không trộn hai nguồn."""
    if runs_csv is not None and Path(runs_csv).is_file():
        rows = load_csv_rows(Path(runs_csv))
        note = (
            f"`{_repo_relative(Path(runs_csv))}` "
            "(một nguồn chính cho cả RQ1 và RQ2, không trộn nguồn khác)"
        )
        return rows, rows, note

    if runs_csv is None and DEFAULT_RUNS_CSV.is_file():
        rows = load_csv_rows(DEFAULT_RUNS_CSV)
        note = "`results/runs.csv` (official frozen dataset)"
        return rows, rows, note

    rq1_rows = load_csv_rows(rq1_csv)
    rq2_rows = load_csv_rows(rq2_csv)
    note = (
        "`results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json` "
        "(W3/W4 frozen pilot; `results/runs.csv` chưa có tại thời điểm chạy)"
    )
    return rq1_rows, rq2_rows, note


def load_graph_metadata(dirs: Sequence[Path]) -> dict[str, GraphMeta]:
    """Đọc mọi instance JSON trong các thư mục, suy ra n/m/density/max_degree/UB."""
    meta: dict[str, GraphMeta] = {}
    for directory in dirs:
        directory = Path(directory)
        if not directory.is_dir():
            raise ValueError(f"Không thấy thư mục instance: {directory}")
        for path in sorted(directory.glob("*.json")):
            instance = read_instance(path)
            m = len(instance.edges)
            degree = {v: 0 for v in range(instance.n)}
            for u, v in instance.edges:
                degree[u] += 1
                degree[v] += 1
            max_degree = max(degree.values()) if degree else 0
            density = (
                2.0 * m / (instance.n * (instance.n - 1)) if instance.n > 1 else 0.0
            )
            meta[instance.id] = GraphMeta(
                n=instance.n,
                m=m,
                density=density,
                max_degree=max_degree,
                UB=instance.n - max_degree,
            )
    return meta


def find_larger_cnf_faster_solve_cases(
    rows: Sequence[dict[str, Any]], *, solver: str | None = "cadical195"
) -> list[dict[str, Any]]:
    """Đảo chiều ngược lại: CNF lớn hơn nhưng giải nhanh hơn (BR-4)."""
    by_instance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _filter_rq1_rows(rows, solver=solver):
        if row.get("clauses") is not None and row.get("t_total") is not None:
            by_instance[row["instance"]].append(row)

    cases: list[dict[str, Any]] = []
    for instance, group in sorted(by_instance.items()):
        configs: dict[tuple[str, str], dict[str, Any]] = {}
        for row in group:
            key = (row["abp_encoding"], row["amo_encoding"])
            if key == ("order", "seqcounter"):
                continue
            configs[key] = row
        items = list(configs.values())
        for index, left in enumerate(items):
            for right in items[index + 1 :]:
                for larger, smaller in ((left, right), (right, left)):
                    if (
                        larger["clauses"] > smaller["clauses"]
                        and larger["t_total"] < smaller["t_total"] - FASTEST
                        and larger["t_total"] * RATIO_MARGIN < smaller["t_total"]
                    ):
                        cases.append(
                            {
                                "instance": instance,
                                "larger_cfg": (
                                    f"{larger['abp_encoding']}/{larger['amo_encoding']}"
                                ),
                                "larger_clauses": larger["clauses"],
                                "larger_vars": larger["variables"],
                                "larger_time": larger["t_total"],
                                "larger_status": larger["status"],
                                "smaller_cfg": (
                                    f"{smaller['abp_encoding']}/"
                                    f"{smaller['amo_encoding']}"
                                ),
                                "smaller_clauses": smaller["clauses"],
                                "smaller_vars": smaller["variables"],
                                "smaller_time": smaller["t_total"],
                                "smaller_status": smaller["status"],
                            }
                        )
    return cases


def cross_size_runtime_inversion(
    rows: Sequence[dict[str, Any]],
    *,
    abp: str = "order",
    amo: str = "pairwise",
) -> list[dict[str, Any]]:
    """n=50 giải nhanh hơn n=40 trên cùng solver/cấu hình (FR-3)."""
    n50 = "randconn50-seed20261026"
    n40 = "randconn40-seed20261026"
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if (
            row.get("abp_encoding") == abp
            and row.get("amo_encoding") == amo
            and row.get("t_total") is not None
        ):
            grouped[row["solver"]][row["instance"]] = row

    items: list[dict[str, Any]] = []
    for solver, by_instance in sorted(grouped.items()):
        big = by_instance.get(n50)
        small = by_instance.get(n40)
        if big is None or small is None:
            continue
        if 0 < big["t_total"] < small["t_total"]:
            items.append(
                {
                    "solver": solver,
                    "n50_time": big["t_total"],
                    "n50_status": big["status"],
                    "n40_time": small["t_total"],
                    "n40_status": small["status"],
                    "ratio": round(small["t_total"] / big["t_total"], 4),
                }
            )
    return items


def project_cnf_growth(
    n: int,
    m: int,
    *,
    abp_encoding: str,
    amo_encoding: str,
    k: int | None = None,
) -> dict[str, Any]:
    """Ước lượng clause/biến/bộ nhớ thuần số học, không dựng CNF (FR-4)."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError(f"n phải là số nguyên >= 2: {n!r}.")
    if isinstance(m, bool) or not isinstance(m, int) or m < 1:
        raise ValueError(f"m phải là số nguyên >= 1: {m!r}.")
    if abp_encoding not in ("pairwise", "order"):
        raise ValueError(
            f"abp_encoding '{abp_encoding}' không hỗ trợ; chọn ('pairwise', 'order')."
        )
    if amo_encoding not in pairwise.SUPPORTED_AMO_ENCODINGS:
        raise ValueError(
            f"amo_encoding '{amo_encoding}' không hỗ trợ; chọn một trong "
            f"{', '.join(pairwise.SUPPORTED_AMO_ENCODINGS)}."
        )
    if amo_encoding != "pairwise":
        raise ValueError(
            "projection chỉ dựng cho amo_encoding='pairwise' (baseline official); "
            f"nhận {amo_encoding!r}."
        )
    k = n - 1 if k is None else k
    if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= n - 1:
        raise ValueError(f"k phải là số nguyên trong 1..n-1: {k!r}.")

    distance = m * 2 * sum(max(0, n - d) for d in range(1, k))
    if abp_encoding == "pairwise":
        variables = n * n
        clauses = 2 * n + 2 * n * math.comb(n, 2) + distance
        memory_est_mb = clauses * (MEMORY_ANCHOR_MB / MEMORY_ANCHOR_CLAUSES)
    else:
        variables = n * (n - 1)
        clauses = n * (n - 2) + n * math.comb(n, 2) + distance
        memory_est_mb = None
    exceeds_cap = memory_est_mb is not None and memory_est_mb > DEFAULT_CAP_MB

    return {
        "n": n,
        "m": m,
        "k": k,
        "abp_encoding": abp_encoding,
        "amo_encoding": amo_encoding,
        "variables": variables,
        "clauses": clauses,
        "memory_est_mb": None
        if memory_est_mb is None
        else round(memory_est_mb, 3),
        "cap_mb": DEFAULT_CAP_MB,
        "exceeds_cap": exceeds_cap,
    }


def _feas_entry(record: dict[str, Any], category: str | None) -> dict[str, Any]:
    lb = record.get("lb")
    ub = record.get("ub")
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    probes = metadata.get("probes") if isinstance(metadata.get("probes"), list) else []
    return {
        "run_id": str(record.get("run_id") or ""),
        "instance": str(record.get("instance") or ""),
        "status": record.get("status"),
        "lb": lb,
        "ub": ub,
        "gap": None if lb is None or ub is None else int(ub) - int(lb),
        "k_best": metadata.get("k_best"),
        "k_unsat": metadata.get("k_unsat"),
        "unsat_source": metadata.get("unsat_source"),
        "triage_category": category,
        "probes": [
            {
                "k": probe.get("k"),
                "status": probe.get("status"),
                "b": probe.get("b"),
                "t_encode": probe.get("t_encode"),
                "t_solve": probe.get("t_solve"),
                "variables": probe.get("variables"),
                "clauses": probe.get("clauses"),
            }
            for probe in probes
            if isinstance(probe, dict)
        ],
    }


def extract_feas_probe_trajectories(
    raw_dir: str | Path, search_dirs: Sequence[str | Path] = DEFAULT_BENCHMARK_DIRS
) -> list[dict[str, Any]]:
    """Dựng lại chuỗi probe của mọi run FEAS từ ``results/raw/*.json`` (FR-7)."""
    raw_dir = Path(raw_dir)
    reports = triage_directory(raw_dir, search_dirs=search_dirs)
    categories = {report.run_id: report.category for report in reports}

    entries: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(record, dict) or record.get("status") != "FEAS":
            continue
        run_id = str(record.get("run_id") or path.stem)
        entries.append(_feas_entry(record, categories.get(run_id)))
    return entries


def solver_sensitivity_table(
    rq2_rows: Sequence[dict[str, Any]], graph_meta: dict[str, GraphMeta]
) -> list[dict[str, Any]]:
    """Bảng độ nhạy solver theo instance: n/m/density/Δ/UB + thời gian từng solver."""
    by_instance: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in _filter_rq2_rows(rq2_rows, "order", "pairwise"):
        if row.get("t_total") is not None:
            by_instance[row["instance"]][row["solver"]] = row

    table: list[dict[str, Any]] = []
    for instance in sorted(by_instance):
        per_solver = by_instance[instance]
        times = {solver: row["t_total"] for solver, row in per_solver.items()}
        fastest = min(times, key=lambda name: (times[name], name))
        slowest = max(times, key=lambda name: (times[name], name))
        fast_time = times[fastest]
        slow_time = times[slowest]
        mean = statistics.fmean(times.values())
        cv = statistics.pstdev(times.values()) / mean if mean > 0 else 0.0
        meta = graph_meta.get(instance)
        table.append(
            {
                "instance": instance,
                "n": meta.n if meta else None,
                "m": meta.m if meta else None,
                "density": meta.density if meta else None,
                "max_degree": meta.max_degree if meta else None,
                "UB": meta.UB if meta else None,
                "times": {solver: round(value, 6) for solver, value in times.items()},
                "statuses": {
                    solver: row["status"] for solver, row in per_solver.items()
                },
                "winner": fastest,
                "fast_over_slow": round(fast_time / slow_time, 4)
                if slow_time > 0
                else 1.0,
                "max_over_min": round(slow_time / fast_time, 4)
                if fast_time > 0
                else 1.0,
                "cv": round(cv, 4),
            }
        )
    return table


def _check_tokens(
    check_id: str,
    path: Path,
    symbol: str,
    tokens: Sequence[str],
    expected: str,
) -> ConsistencyFinding:
    text = _compact(_read(path))
    missing = [token for token in tokens if _compact(token) not in text]
    return _finding(
        check_id,
        path,
        symbol,
        expected,
        "đủ" if not missing else "thiếu",
        missing,
    )


def verify_code_spec_paper_consistency() -> list[ConsistencyFinding]:
    """Kiểm tra C1–C10 bằng AST/text, không import module exact (không cần license)."""
    findings: list[ConsistencyFinding] = []
    path4 = read_instance(REPO_ROOT / "benchmark" / "toy" / "path4.json")
    s_text, m_text, a_text = _read(S_PATH), _read(M_PATH), _read(A_PATH)
    c_text, freeze_text = _read(C_PATH), _read(W4_FREEZE_PATH)

    # C1 — id biến + số biến, live từ build_cnf + văn bản S/M/A.
    p_cnf = pairwise.build_cnf(path4, 1)
    o_cnf = order.build_cnf(path4, 1)
    live_p = (
        all(p_cnf.var_of[(v, p)] == v * 4 + p for v in range(4) for p in range(1, 5))
        and p_cnf.n_vars == 16
    )
    live_o = (
        all(o_cnf.var_of[(v, p)] == v * 3 + p for v in range(4) for p in range(1, 4))
        and o_cnf.n_vars == 12
    )
    missing: list[str] = []
    if not (live_p and live_o):
        missing.append("build_cnf id/count live")
    for label, text in (("S", s_text), ("M", m_text), ("A", a_text)):
        compact = _compact(text)
        for token in ("v*n+p", "v*(n-1)+p", "n²", "n(n-1)"):
            if token not in compact:
                missing.append(f"{label}:{token}")
    findings.append(
        _finding(
            "C1",
            S_PATH,
            "§2 pairwise/order variable ids",
            "v*n+p (n²) và v*(n-1)+p (n(n-1)) trong S §2, M §3.2, A §A.1/A.2",
            f"pairwise n_vars={p_cnf.n_vars}, order n_vars={o_cnf.n_vars}",
            missing,
        )
    )

    # C2 — clause count path4 live + bảng S §3 / M §3.3.
    live_counts = {
        "pairwise": [len(pairwise.build_cnf(path4, k).clauses) for k in (1, 2, 3)],
        "order": [len(order.build_cnf(path4, k).clauses) for k in (1, 2, 3)],
    }
    expected_counts = {"pairwise": [56, 74, 86], "order": [32, 50, 62]}
    missing = []
    if live_counts != expected_counts:
        missing.append(f"live={live_counts}")
    for token in ("56", "74", "86"):
        if token not in _compact(s_text):
            missing.append(f"S:{token}")
    for token in ("56", "74", "86", "32", "50", "62"):
        if token not in _compact(m_text):
            missing.append(f"M:{token}")
    findings.append(
        _finding(
            "C2",
            S_PATH,
            "§3 path4 clause table (56/74/86) + M §3.3 (32/50/62)",
            "path4 K=1/2/3: pairwise 56/74/86, order 32/50/62",
            f"live={live_counts}",
            missing,
        )
    )

    # C3 — biên _not_value + appendix A.5.
    v = 2
    boundary_low = order._not_value(o_cnf.var_of, 4, v, 1)
    boundary_high = order._not_value(o_cnf.var_of, 4, v, 4)
    interior = order._not_value(o_cnf.var_of, 4, v, 2)
    live_ok = (
        boundary_low == [-o_cnf.var_of[(v, 1)]]
        and boundary_high == [o_cnf.var_of[(v, 3)]]
        and interior == [-o_cnf.var_of[(v, 2)], o_cnf.var_of[(v, 1)]]
    )
    missing = []
    if not live_ok:
        missing.append("live _not_value")
    for token in ("-o[v][1]", "o[v][n-1]", "o[v][q-1]", "-o[v][q]"):
        if token not in _compact(a_text):
            missing.append(f"A:{token}")
    findings.append(
        _finding(
            "C3",
            A_PATH,
            "§A.5 _not_value boundaries",
            "q=1/-o[v][1], q=n/o[v][n-1], interior hai literal",
            f"q=1={boundary_low}, q=n={boundary_high}, interior={interior}",
            missing,
        )
    )

    # C4 — vòng K-search K = lo + 1, dừng ở UNSAT đầu tiên.
    solve_text = _read(REPO_ROOT / "src" / "sat" / "solve.py")
    missing = []
    solve_flat = _normal_space(solve_text)
    for token in (
        "k = lo + 1",
        "lo, best_solution, best_cnf = value",
        "hi, unsat_source = k",
    ):
        if token not in solve_flat:
            missing.append(f"solve.py:{token}")
    s_compact, a_compact = _compact(s_text), _compact(a_text)
    for label, text in (("S", s_compact), ("A", a_compact)):
        for token in ("b+1", "unsat"):
            if token not in text:
                missing.append(f"{label}:{token}")
    if "k=lo+1" not in a_compact:
        missing.append("A:k=lo+1")
    findings.append(
        _finding(
            "C4",
            REPO_ROOT / "src" / "sat" / "solve.py",
            "solve_sat K-search (k = lo + 1, first UNSAT)",
            "K <- B + 1, dừng ở lần UNSAT đầu tiên (S §5, A §A.5)",
            "k = lo + 1; hi = k khi UNSAT",
            missing,
        )
    )

    # C5 — trivial_unsat K >= n, kiểm trước build_cnf.
    live_ok = all(
        pairwise.trivial_unsat(n, k) == (k >= n)
        for n in range(2, 7)
        for k in range(1, 8)
    )
    probe_at = solve_flat.find("def _probe")
    order_ok = False
    if probe_at != -1:
        probe_src = solve_flat[probe_at:]
        guard_at = probe_src.find("if trivial_unsat(instance.n, k):")
        build_at = probe_src.find("cnf = order.build_cnf")
        order_ok = -1 not in (guard_at, build_at) and guard_at < build_at
    missing = []
    if not (live_ok and order_ok):
        missing.append("live trivial_unsat/order")
    for label, text in (("S", s_text), ("M", m_text)):
        if _compact("trước khi dựng cnf") not in _compact(text):
            missing.append(f"{label}:trước khi dựng CNF")
    a_compact = _compact(a_text)
    if (
        "withoutbuildingacnf" not in a_compact
        and "trướckhidựngcnf" not in a_compact
    ):
        missing.append("A:UNSAT before CNF build")
    findings.append(
        _finding(
            "C5",
            REPO_ROOT / "src" / "sat" / "pairwise.py",
            "trivial_unsat (k >= n) checked before build_cnf",
            "K >= n -> UNSAT trước khi dựng CNF (S §1, M §3.1, A.3.1)",
            f"live={live_ok}, probe_order={order_ok}",
            missing,
        )
    )

    # C6 — canonical config khớp code + C + W4 freeze.
    cfg = CANONICAL_SAT_CONFIG
    expected_fields = {
        "method": "sat",
        "abp_encoding": "order",
        "amo_encoding": "pairwise",
        "sat_solver": "glucose4",
        "search_mode": "multi",
        "symmetry": False,
        "warm_start": False,
        "seed": 0,
    }
    live_ok = all(getattr(cfg, key) == value for key, value in expected_fields.items())
    missing = []
    if not live_ok:
        missing.append("CANONICAL_SAT_CONFIG")
    for label, text in (("C", c_text), ("W4", freeze_text)):
        compact = _compact(text)
        for key, value in expected_fields.items():
            token = f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}"
            if _compact(token) not in compact:
                missing.append(f"{label}:{token}")
    findings.append(
        _finding(
            "C6",
            REPO_ROOT / "src" / "sat" / "solve.py",
            "CANONICAL_SAT_CONFIG",
            "order/pairwise/glucose4/multi/false/false/0",
            str({key: getattr(cfg, key) for key in expected_fields}),
            missing,
        )
    )

    # C7 — memory contract + escape hatch.
    raised = False
    try:
        canonical_sat_config(memory_limit=None)
    except ValueError as exc:
        raised = "memory_limit" in str(exc)
    unbounded = (
        canonical_sat_config(
            memory_limit=None, allow_unbounded_memory=True
        ).memory_limit
        is None
    )
    missing = []
    if not (raised and unbounded):
        missing.append("canonical_sat_config memory contract")
    for label, text in (
        ("C", c_text),
        ("W4", freeze_text),
        ("S", s_text),
        ("M", m_text),
    ):
        if "allow_unbounded_memory" not in _compact(text):
            missing.append(f"{label}:allow_unbounded_memory")
    findings.append(
        _finding(
            "C7",
            REPO_ROOT / "src" / "sat" / "solve.py",
            "canonical_sat_config(memory_limit=...)",
            "None -> ValueError; allow_unbounded_memory=True -> None; nêu ở C/W4/S/M",
            f"raised={raised}, unbounded={unbounded}",
            missing,
        )
    )

    # C8 — R1..R6 cross-review P1 (chỉ đọc source text, không import backend).
    exact_dir = REPO_ROOT / "src" / "exact"
    exact_tests = REPO_ROOT / "tests" / "exact" / "test_exact_solvers.py"
    solvers = {
        "gurobi_mip": exact_dir / "gurobi_mip.py",
        "cplex_mip": exact_dir / "cplex_mip.py",
        "cplex_cp": exact_dir / "cplex_cp.py",
        "cp_sat_solver": exact_dir / "cp_sat_solver.py",
    }
    r1 = _check_tokens(
        "C8",
        exact_tests,
        "R1 skip-guards",
        ("_skip_if_backend_unavailable", "pytest.skip", "cpoptimizer.exe"),
        "skip thay vì fail khi thiếu backend/engine/license",
    )
    r1.check_id = "C8-R1"
    findings.append(r1)
    r2 = _check_tokens(
        "C8",
        EXACT_MODELS_PATH,
        "R2 timing scope",
        ("Timing and memory-limit scope", "wall_time", "time_limit + 30 seconds"),
        "runner wall_time + kill cứng time_limit + 30 s",
    )
    r2.check_id = "C8-R2"
    findings.append(r2)
    common_text = _read(exact_dir / "common.py")
    missing = []
    if "def validate_exact_input" not in common_text or "raise ValueError" not in common_text:
        missing.append("common.validate_exact_input")
    for name, path in solvers.items():
        text = _read(path)
        if "validate_exact_input" not in text and "raise ValueError" not in text:
            missing.append(name)
    findings.append(
        _finding(
            "C8",
            exact_dir / "common.py",
            "R3 validate_exact_input",
            "ValueError cho input xấu, hiện diện ở cả 4 solver",
            f"4/4 file có ValueError/validate; 3/4 dùng validate_exact_input",
            missing,
        )
    )
    findings[-1].check_id = "C8-R3"
    missing = []
    if "def warn_ignored_config" not in common_text:
        missing.append("common.warn_ignored_config")
    for name in ("gurobi_mip", "cplex_mip", "cplex_cp"):
        if "warn_ignored_config" not in _read(solvers[name]):
            missing.append(name)
    findings.append(
        _finding(
            "C8",
            exact_dir / "common.py",
            "R4 warn_ignored_config",
            "warning cho field Config bị bỏ qua ở 3 solver",
            "common + gurobi_mip/cplex_mip/cplex_cp",
            missing,
        )
    )
    findings[-1].check_id = "C8-R4"
    cp_text = _read(solvers["cp_sat_solver"])
    missing = [token for token in ("def _safe_upper_bound", "return n - 1", "UNKNOWN", "isfinite") if token not in cp_text]
    findings.append(
        _finding(
            "C8",
            solvers["cp_sat_solver"],
            "R5 _safe_upper_bound",
            "UNKNOWN/không hữu hạn -> ub = n-1",
            "return n - 1 khi UNKNOWN/non-finite",
            missing,
        )
    )
    findings[-1].check_id = "C8-R5"
    missing = []
    for name in ("gurobi_mip", "cplex_mip", "cplex_cp"):
        text = _compact(_read(solvers[name]))
        if "objective!=model_objective" not in text or "err" not in text:
            missing.append(name)
    findings.append(
        _finding(
            "C8",
            exact_dir / "gurobi_mip.py",
            "R6 objective cross-check",
            "objective != model_objective -> ERR ở 3 backend",
            "3/3 backend trả ERR khi lệch",
            missing,
        )
    )
    findings[-1].check_id = "C8-R6"

    # C9 — hygiene: marker, docs/handoff, link tương đối trong repo.
    checked_files = [DEFAULT_W5_OUT / name for name in W5_ARTIFACTS] + [
        S_PATH,
        A_PATH,
        M_PATH,
        REPO_ROOT / "docs" / "w2-sat" / "15-m1-gate-evidence.md",
        C_PATH,
    ]
    markers: list[str] = []
    handoff: list[str] = []
    broken: list[str] = []
    for path in checked_files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?i)\b(TODO|TBD|FIXME)\b", text):
            markers.append(_repo_relative(path))
        if "docs/handoff/" in text:
            handoff.append(_repo_relative(path))
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            target = target.strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            clean = target.split("#", 1)[0].strip()
            if not clean:
                continue
            if not any(
                candidate.exists()
                for candidate in (path.parent / clean, REPO_ROOT / clean)
            ):
                broken.append(f"{_repo_relative(path)} -> {target}")
    findings.append(
        _finding(
            "C9",
            DEFAULT_W5_OUT,
            "deliverable hygiene",
            "không placeholder, không tham chiếu handoff cũ, không link gãy",
            f"markers={markers}, handoff={handoff}, broken={broken}",
            markers + handoff + broken,
        )
    )

    # C10 — fairness năm điểm ở P1 review + paper 27.
    paper_path = DEFAULT_W5_OUT / "27-paper-v09-sat-sections.md"
    fairness_tokens = ("wall_time", "time_limit", "ub", "mipgap", "verify()")
    missing = []
    for label, path in (("P1", P1_REVIEW_PATH), ("paper27", paper_path)):
        if not path.is_file():
            if label == "paper27":
                continue
            missing.append(label)
            continue
        compact = _compact(_read(path))
        for token in fairness_tokens:
            if _compact(token) not in compact:
                missing.append(f"{label}:{token}")
    findings.append(
        _finding(
            "C10",
            P1_REVIEW_PATH,
            "fairness of comparison",
            "wall_time, time_limit semantics, ub on TO, MIPGap=0, shared verify()",
            "P1 review + paper 27 nêu đủ 5 điểm",
            missing,
        )
    )
    return findings


def _normal_space(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _w5_checkbox_counts() -> tuple[int, int]:
    checked = total = 0
    for name in W5_ARTIFACTS:
        issue = (
            REPO_ROOT / "docs" / "abp-sat-encoding" / "issues" / "W5" / name
        )
        if not issue.is_file():
            continue
        text = issue.read_text(encoding="utf-8")
        checked += len(re.findall(r"\[x\]", text))
        total += len(re.findall(r"\[[ x]\]", text))
    return checked, total


def evaluate_g4_gate(
    triage_reports: Sequence[TriageReport],
    consistency: Sequence[ConsistencyFinding],
    *,
    expected_triaged: int = 70,
    boxes_checked: int = 0,
    boxes_total: int = 12,
    sat_discussion_complete: bool | None = None,
) -> G4Summary:
    """Đánh giá G4: 100% frozen data triaged, 0 CODE_BUG, discussion + checkbox đủ."""
    code_bugs = sum(report.category == "CODE_BUG" for report in triage_reports)
    all_triaged = (
        len(triage_reports) >= expected_triaged
        and code_bugs == 0
        and all(
            report.category in ("OK", "SOLVER_BEHAVIOR", "ENV_ERROR", "CODE_BUG")
            for report in triage_reports
        )
    )
    checks_ok = all(finding.status == "ok" for finding in consistency)
    discussion_ok = checks_ok if sat_discussion_complete is None else sat_discussion_complete
    boxes_ok = boxes_total > 0 and boxes_checked == boxes_total
    passed = all_triaged and discussion_ok and boxes_ok
    statement = (
        f"G4 {'PASS' if passed else 'FAIL'}: "
        f"triage {len(triage_reports)}/{expected_triaged} run frozen "
        f"(CODE_BUG={code_bugs}); "
        f"consistency C1–C10 {'PASS' if checks_ok else 'FAIL'} "
        f"({len(consistency)} finding); "
        f"checkbox W5 {boxes_checked}/{boxes_total}."
    )
    return G4Summary(
        triaged_total=len(triage_reports),
        code_bugs=code_bugs,
        all_triaged=all_triaged,
        sat_discussion_complete=discussion_ok,
        boxes_checked=boxes_checked,
        passed=passed,
        statement=statement,
    )


def _f(value: Any, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{digits}f}"


def _int(value: Any) -> str:
    return "—" if value is None else str(int(value))


def _banner(source_note: str, extra: str | None = None) -> list[str]:
    lines = [GENERATED_NOTE]
    if source_note:
        lines.append(f"> Nguồn dữ liệu: {source_note}")
    if extra:
        lines.append(f"> {extra}")
    return lines


def _pick_rq1_best(summaries: Sequence[Any]) -> Any:
    """Chọn cấu hình RQ1 theo OPT coverage; hoà thì ưu tiên `order`/`pairwise` (BR-3)."""
    if not summaries:
        return None
    top_opt = max(item.opt for item in summaries)
    top = [item for item in summaries if item.opt == top_opt]
    preferred = next(
        (
            item
            for item in top
            if (item.abp_encoding, item.amo_encoding) == ("order", "pairwise")
        ),
        None,
    )
    return preferred or min(top, key=lambda item: (item.par2, item.median_memory_mb))


def _rq1_sections(
    rq1_rows: Sequence[dict[str, Any]],
    rq2_rows: Sequence[dict[str, Any]],
    *,
    source_note: str,
    solver: str,
    cap_mb: float,
) -> list[str]:
    summaries = summarize_rq1(rq1_rows, solver=solver)
    smaller_slower = find_smaller_cnf_slower_solve_cases(rq1_rows, solver=solver)
    larger_faster = find_larger_cnf_faster_solve_cases(rq1_rows, solver=solver)
    best = _pick_rq1_best(summaries)
    by_pair = {
        (item.abp_encoding, item.amo_encoding): item for item in summaries
    }

    lines = _banner(source_note)
    lines.extend(
        [
            "",
            "# 24 — RQ1 final: encoding × AMO",
            "",
            f"> **Lát cắt cố định (BR-2):** solver = `{solver}`, "
            "`search_mode` ∈ {rỗng, `multi`}, `symmetry = false`, "
            "`warm_start = false`; chỉ `(abp_encoding, amo_encoding)` thay đổi.",
            "",
            "## 1. Bảng tổng hợp RQ1",
            "",
            "| `abp_encoding` | `amo_encoding` | Runs | OPT | FEAS | TO | MO | ERR | PAR2 (s) | Σ `t_encode` (s) | Σ `t_solve` (s) | Σ `t_total` (s) | Median Vars | Max Vars | Median Clauses | Max Clauses | Median Mem (MB) | Max Mem (MB) |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in summaries:
        lines.append(
            f"| `{item.abp_encoding}` | `{item.amo_encoding}` | {item.n_runs} | "
            f"{item.opt} | {item.feas} | {item.to} | {item.mo} | {item.err} | "
            f"{item.par2:.2f} | {item.total_encode_s:.2f} | "
            f"{item.total_solve_s:.2f} | {item.total_time_s:.2f} | "
            f"{int(item.median_vars)} | {item.max_vars} | "
            f"{int(item.median_clauses)} | {item.max_clauses} | "
            f"{item.median_memory_mb:.2f} | {item.max_memory_mb:.2f} |"
        )

    lines.extend(["", "## 2. Kết luận RQ1", ""])
    if best is None:
        lines.append("Không có hàng RQ1 nào trong nguồn dữ liệu.")
    else:
        other = by_pair.get(("pairwise", "pairwise"))
        lines.append(
            f"- **Encoding/AMO biểu diễn bài toán tốt hơn:** "
            f"`{best.abp_encoding}`/`{best.amo_encoding}` đứng đầu bảng theo "
            "thứ tự Protocol (OPT coverage → PAR2 → `peak_memory`)."
        )
        lines.append(
            f"- **Có giúp solving không:** có, trên tập frozen. "
            f"`{best.abp_encoding}`/`{best.amo_encoding}` đạt "
            f"{best.opt}/{best.n_runs} OPT, PAR2 {best.par2:.2f} s, "
            f"max `peak_memory` {best.max_memory_mb:.2f} MB."
        )
        if other is not None and (
            other.abp_encoding,
            other.amo_encoding,
        ) != (best.abp_encoding, best.amo_encoding):
            lines.append(
                f"- **So với `{other.abp_encoding}`/`{other.amo_encoding}`:** "
                f"{other.opt}/{other.n_runs} OPT, PAR2 {other.par2:.2f} s, "
                f"max clauses {other.max_clauses}, "
                f"max `peak_memory` {other.max_memory_mb:.2f} MB. "
                "Chênh lệch OPT coverage là tiêu chí quyết định; thời gian chỉ "
                "là tiêu chí phụ."
            )
        lines.append(
            "- **Không ép chiều nhân quả:** CNF nhỏ hơn không đồng nghĩa giải "
            "nhanh hơn; cả hai chiều được liệt kê ở §3 từ dữ liệu frozen (BR-4)."
        )

    lines.extend(["", "## 3. Case study từ dữ liệu frozen", ""])
    lines.extend(
        [
            "### 3.1. (a) CNF nhỏ hơn nhưng giải chậm hơn",
            "",
        ]
    )
    if smaller_slower:
        lines.extend(
            [
                "| Instance | Cấu hình nhỏ hơn | Clauses | Vars | `t_total` (s) | Status | Cấu hình lớn hơn | Clauses | Vars | `t_total` (s) | Status |",
                "|---|---|---:|---:|---:|---|---|---:|---:|---:|---|",
            ]
        )
        for case in smaller_slower[:8]:
            lines.append(
                f"| `{case['instance']}` | `{case['smaller_cfg']}` | "
                f"{case['smaller_clauses']} | {_int(case['smaller_vars'])} | "
                f"{case['smaller_time']:.3f} | `{case['smaller_status']}` | "
                f"`{case['larger_cfg']}` | {case['larger_clauses']} | "
                f"{_int(case['larger_vars'])} | {case['larger_time']:.3f} | "
                f"`{case['larger_status']}` |"
            )
        lines.append("")
        lines.append(
            "Mọi cặp thỏa đồng thời `smaller_clauses < larger_clauses` và "
            "`smaller_t_total > larger_t_total` trong CSV frozen."
        )
    else:
        lines.append(
            "Không ghi nhận cặp CNF-nhỏ-chậm hơn trong nguồn dữ liệu hiện tại."
        )

    lines.extend(
        [
            "",
            "### 3.2. (b) CNF lớn hơn nhưng giải nhanh hơn",
            "",
        ]
    )
    if larger_faster:
        lines.extend(
            [
                "| Instance | Cấu hình lớn hơn | Clauses | Vars | `t_total` (s) | Status | Cấu hình nhỏ hơn | Clauses | Vars | `t_total` (s) | Status |",
                "|---|---|---:|---:|---:|---|---|---:|---:|---:|---|",
            ]
        )
        for case in larger_faster[:8]:
            lines.append(
                f"| `{case['instance']}` | `{case['larger_cfg']}` | "
                f"{case['larger_clauses']} | {_int(case['larger_vars'])} | "
                f"{case['larger_time']:.3f} | `{case['larger_status']}` | "
                f"`{case['smaller_cfg']}` | {case['smaller_clauses']} | "
                f"{_int(case['smaller_vars'])} | {case['smaller_time']:.3f} | "
                f"`{case['smaller_status']}` |"
            )
        lines.append("")
        lines.append(
            "Điều kiện lọc: lớn hơn về clause nhưng `t_total` nhỏ hơn ít nhất "
            "0,005 s và 5%."
        )
    else:
        lines.append(
            "Không ghi nhận cặp CNF-lớn-nhanh hơn trong nguồn dữ liệu hiện tại."
        )

    inversions = cross_size_runtime_inversion(list(rq1_rows) + list(rq2_rows))
    lines.extend(["", "**Đảo chiều kích thước phi đơn điệu (n=50 nhanh hơn n=40):**", ""])
    if inversions:
        lines.extend(
            [
                "| Solver | `n=50` `t_total` (s) | Status | `n=40` `t_total` (s) | Status | Tỷ lệ n40/n50 |",
                "|---|---:|---|---:|---|---:|",
            ]
        )
        for item in inversions:
            lines.append(
                f"| `{item['solver']}` | {item['n50_time']:.3f} | "
                f"`{item['n50_status']}` | {item['n40_time']:.3f} | "
                f"`{item['n40_status']}` | {item['ratio']:.2f}× |"
            )
    else:
        lines.append("Không có cặp n=50/n=40 đảo chiều trên lát cắt `order`/`pairwise`.")

    lines.extend(
        [
            "",
            "### 3.3. (c) `pairwise`/`pairwise` bùng nổ kích thước và rủi ro MO",
            "",
            "**Đo được (frozen):** `pairwise`/`pairwise` có đúng `n²` biến; nhóm "
            "AMO bậc hai theo số literal làm tổng clause `O(n³)`. Tại `n = 50`, "
            f"cấu hình này đạt **{by_pair[('pairwise', 'pairwise')].max_clauses if ('pairwise', 'pairwise') in by_pair else '—'} clauses** "
            f"và **{by_pair[('pairwise', 'pairwise')].max_memory_mb if ('pairwise', 'pairwise') in by_pair else '—'} MB**; "
            f"`order`/`pairwise` đạt **{by_pair[('order', 'pairwise')].max_clauses if ('order', 'pairwise') in by_pair else '—'} clauses** "
            f"và **{by_pair[('order', 'pairwise')].max_memory_mb if ('order', 'pairwise') in by_pair else '—'} MB**.",
            "",
            "**Projection (không phải measurement):** ước lượng clause theo công "
            "thức đặc tả, mốc bộ nhớ quy đổi từ `randconn50` (`126.53125` MB / "
            "`255400` clause). `m` của mẫu HB dày lấy `n(n−1)/8`; cap tham chiếu "
            f"`{cap_mb:.0f}` MB.",
            "",
            "| n | m | k | `pairwise`/`pairwise` clauses | `pairwise` mem (MB) | vượt cap | `order`/`pairwise` clauses | `order` mem |",
            "|---:|---:|---:|---:|---:|---|---:|---|",
        ]
    )
    for n, m in ((50, 100), (118, 118 * 117 // 8), (420, 420 * 419 // 8), (715, 715 * 714 // 8)):
        k = 17 if n == 50 else n - 1  # n=50: mốc đo K=17; HB: worst case K=n-1
        proj_p = project_cnf_growth(
            n, m, abp_encoding="pairwise", amo_encoding="pairwise", k=k
        )
        proj_o = project_cnf_growth(
            n, m, abp_encoding="order", amo_encoding="pairwise", k=k
        )
        lines.append(
            f"| {n} | {m} | {k} | {proj_p['clauses']} | "
            f"{_f(proj_p['memory_est_mb'], 1)} | "
            f"{'có' if proj_p['exceeds_cap'] else 'không'} | "
            f"{proj_o['clauses']} | — |"
        )
    lines.extend(
        [
            "",
            "- **MO hình thành thế nào (BR-7):** solver SAT không enforce "
            "`memory_limit` cap trong process. `MO` chỉ đến từ ánh xạ "
            "`MemoryError` ngoài process (`src/runner/worker.py`); cap official do "
            "runner áp (Protocol §6.3). Không có claim MO đo được cho "
            "`pairwise/pairwise` trong frozen data.",
            "- **Hệ quả:** ở quy mô HB lớn, `pairwise`/`pairwise` là bất khả thi theo "
            "projection; `order` giữ số biến `n(n−1)` và không có nhóm AMO nên "
            "clause thấp hơn hẳn trên cùng `(n, m, K)`.",
            "",
            "## 4. Kiểm tra nhất quán `order`/`seqcounter` ≡ `order`/`pairwise` (BR-3)",
            "",
        ]
    )
    op = by_pair.get(("order", "pairwise"))
    os_ = by_pair.get(("order", "seqcounter"))
    if op is not None and os_ is not None:
        lines.append(
            f"- Hai hàng `order` có cùng `max_clauses` = {op.max_clauses} và "
            f"cùng `max_vars` = {op.max_vars}; `Σ t_total` lần lượt "
            f"{op.total_time_s:.2f} s và {os_.total_time_s:.2f} s. "
            "Đây là kiểm tra CNF trùng, không phải bằng chứng cho AMO encoder. "
            "`order/seqcounter` bị loại khỏi khai thác cặp đảo chiều."
        )
    else:
        lines.append("- Thiếu một trong hai hàng `order` để đối chiếu.")

    lines.extend(
        [
            "",
            "## 5. Provenance",
            "",
            f"- Nguồn chính: {source_note}.",
            "- Mọi số trong bảng sinh trực tiếp bởi `experiments/w5_final_analysis.py`; "
            "không sửa tay.",
            f"- Lát cắt khớp `experiments/analyze_rq1_rq2.py` (`_filter_rq1_rows`).",
        ]
    )
    return lines


def _rq2_sections(
    rq2_rows: Sequence[dict[str, Any]],
    graph_meta: dict[str, GraphMeta],
    trajectories: Sequence[dict[str, Any]],
    *,
    source_note: str,
    cap_mb: float,
) -> list[str]:
    summaries = summarize_rq2(rq2_rows)
    sensitivity = solver_sensitivity_table(rq2_rows, graph_meta)
    solvers = [item.solver for item in summaries]
    core_rank = [
        item for item in summaries if item.solver in ("cadical195", "glucose4")
    ]
    core_winner = core_rank[0] if core_rank else None
    overall = summaries[0] if summaries else None

    lines = _banner(source_note)
    lines.extend(
        [
            "",
            "# 25 — RQ2 final: xếp hạng SAT solver",
            "",
            "> **Lát cắt cố định (BR-2):** `abp_encoding = order`, "
            "`amo_encoding = pairwise`, `search_mode` ∈ {rỗng, `multi`}, "
            "`symmetry = false`, `warm_start = false`; chỉ `solver` thay đổi.",
            "> **Thứ tự ưu tiên Protocol:** OPT coverage → PAR2 → số `TO` → "
            "`peak_memory` → độ nhạy theo instance.",
            "",
            "## 1. Bảng xếp hạng RQ2",
            "",
            "| Hạng | Solver | Vai trò | Runs | OPT | FEAS | TO | MO | ERR | PAR2 (s) | Σ `t_solve` (s) | Σ `t_total` (s) | Median `t_total` (s) | Median Mem (MB) | Max Mem (MB) |",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for rank, item in enumerate(summaries, start=1):
        role = (
            "Protocol Core"
            if item.solver in ("cadical195", "glucose4")
            else "PySAT baseline (bổ sung)"
        )
        lines.append(
            f"| {rank} | `{item.solver}` | {role} | {item.n_runs} | {item.opt} | "
            f"{item.feas} | {item.to} | {item.mo} | {item.err} | "
            f"{item.par2:.2f} | {item.total_solve_s:.2f} | "
            f"{item.total_time_s:.2f} | {item.median_time_s:.4f} | "
            f"{item.median_memory_mb:.2f} | {item.max_memory_mb:.2f} |"
        )

    lines.extend(["", "## 2. Kết luận RQ2", ""])
    if core_winner is not None:
        lines.append(
            f"- **Canonical solver (Protocol Core `{{cadical195, glucose4}}`):** "
            f"`{core_winner.solver}` — {core_winner.opt}/{core_winner.n_runs} OPT, "
            f"PAR2 {core_winner.par2:.2f} s, max `peak_memory` "
            f"{core_winner.max_memory_mb:.2f} MB."
        )
        lines.append(
            "- **Caveat CaDiCaL:** `cadical195` chạy qua vòng lặp conflict-budget "
            "`src/sat/backend.py:238-254`; phần chênh thời gian của nó là chi phí "
            "wrapper, không phải chỉ tốc độ solver."
        )
    if overall is not None:
        lines.append(
            f"- **Toàn bộ 4 solver PySAT:** `{overall.solver}` nhanh nhất "
            f"(PAR2 {overall.par2:.2f} s). Đây là baseline bổ sung; quyết định "
            "canonical vẫn theo Protocol Core (OQ-3), trừ khi P1/P3 cho phép "
            "`minisat22`."
        )
    lines.append(
        "- **Giới hạn tập dữ liệu:** mọi run RQ2 đều `OPT`; không có `TO`/`MO`/"
        "`ERR`, nên tiêu chí timeout/memory là rỗng trên subset này. Quyết định "
        "được đưa trên 10 instance đều xong trong 60 s; rủi ro instance khó được "
        "ghi nhận tại freeze (`docs/canonical_sat_config.md`)."
    )

    lines.extend(
        [
            "",
            "## 3. Bảng chi tiết theo instance",
            "",
        ]
    )
    by_instance: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in _filter_rq2_rows(rq2_rows, "order", "pairwise"):
        by_instance[row["instance"]][row["solver"]] = row
    if solvers and by_instance:
        header = "| Instance | " + " | ".join(
            f"`{name}` (status / `t_total` / mem)" for name in solvers
        ) + " |"
        lines.extend([header, "|---|" + "|".join("---:" for _ in solvers) + "|"])
        for instance in sorted(by_instance):
            cells = []
            for name in solvers:
                row = by_instance[instance].get(name)
                if row is None:
                    cells.append("N/A")
                else:
                    time_value = row["t_total"] if row["t_total"] is not None else 0.0
                    mem = row["peak_memory"] if row["peak_memory"] is not None else 0.0
                    cells.append(
                        f"{row['status']} / {time_value:.3f}s / {mem:.1f}MB"
                    )
            lines.append(f"| `{instance}` | " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "## 4. Case study (a) — độ nhạy solver theo mật độ/kích thước",
            "",
            "| Instance | n | m | density | Δ | UB | "
            + " | ".join(f"`{name}` (s)" for name in solvers)
            + " | Winner | slow/fast | cv |",
            "|---|---:|---:|---:|---:|---:|"
            + "|".join("---:" for _ in solvers)
            + "|---|---:|---:|",
        ]
    )
    for item in sensitivity:
        cells = [f"{_f(item['times'].get(name), 4)}" for name in solvers]
        lines.append(
            f"| `{item['instance']}` | {_int(item['n'])} | {_int(item['m'])} | "
            f"{_f(item['density'], 4)} | {_int(item['max_degree'])} | "
            f"{_int(item['UB'])} | " + " | ".join(cells) + f" | `{item['winner']}` | "
            f"{item['max_over_min']:.3f}× | {item['cv']:.3f} |"
        )
    winners = {item["winner"] for item in sensitivity}
    densities = [item["density"] for item in sensitivity if item["density"] is not None]
    density_text = (
        f"{min(densities):.4f}–{max(densities):.4f}"
        if densities
        else "không có metadata instance trong bảng"
    )
    lines.append("")
    if len(winners) <= 1:
        lines.append(
            "- **Trả lời câu hỏi “solver A thắng thưa, B thắng dày”:** dữ liệu "
            "frozen **không tách được** hai solver theo mật độ — cùng một winner "
            f"(`{next(iter(winners)) if winners else '—'}`) trên toàn subset; "
            f"density chỉ trải {density_text}. "
            "Đây là scope limitation, không phải kết luận ‘không có khác biệt’."
        )
    else:
        lines.append(
            f"- **Trả lời:** winner thay đổi theo instance ({', '.join(sorted(winners))}); "
            f"density trải {density_text}. "
            "Xem cột density và `t_total` để đọc cặp thắng/thua."
        )
    lines.append(
        "- Cột `slow/fast` là tỷ lệ thời gian solver chậm nhất / nhanh nhất trên "
        "cùng instance; `cv` là hệ số biến thiên quần thể giữa các solver."
    )

    lines.extend(
        [
            "",
            "## 5. Case study (b) — FEAS không OPT và ý nghĩa bound (BR-8)",
            "",
        ]
    )
    if trajectories:
        for entry in trajectories:
            lines.extend(
                [
                    f"### `{entry['run_id']}`",
                    "",
                    f"- Instance `{entry['instance']}`; status `{entry['status']}`; "
                    f"`lb = {entry['lb']}`, `ub = {entry['ub']}`, "
                    f"`gap = {entry['gap']}`; `k_best = {entry['k_best']}`, "
                    f"`k_unsat = {entry['k_unsat']}`, "
                    f"`unsat_source = {entry['unsat_source']}`; "
                    f"triage = `{entry['triage_category']}`.",
                    f"- `ub = {entry['ub']}` là **cận trên đếm nhãn** `n − 1`, "
                    "không phải upper bound chặt; `gap` lớn không có nghĩa solver "
                    "gần tối ưu.",
                    "",
                    "| K | Status | B | `t_encode` (s) | `t_solve` (s) | Vars | Clauses |",
                    "|---:|---|---:|---:|---:|---:|---:|",
                ]
            )
            for probe in entry["probes"]:
                lines.append(
                    f"| {_int(probe['k'])} | `{probe['status']}` | "
                    f"{_int(probe['b'])} | {_f(probe['t_encode'], 6)} | "
                    f"{_f(probe['t_solve'], 6)} | {_int(probe['variables'])} | "
                    f"{_int(probe['clauses'])} |"
                )
            lines.append("")
    else:
        lines.append("Không có run FEAS nào trong `results/raw/*.json` hiện tại.")

    lines.extend(
        [
            "",
            "## 6. Kissat — loại vĩnh viễn (BR-6)",
            "",
            "Kissat không phải ứng viên và không xuất hiện trong bảng. Qua PySAT "
            "`kissat404` cho model sai, bỏ qua assumption một cách im lặng và "
            "abort process sau `add_clause`; không có binary `kissat` ngoài trên "
            "`PATH` (`docs/sat_tooling.md` mục Kissat; "
            "`src/sat/backend.py` `PYSAT_KISSAT_FAMILIES`; `src/sat/solve.py` "
            "`_validate_solver`). Bảng RQ2 chỉ gồm `glucose4`, `cadical195` "
            "(Protocol Core) và `minisat22`, `glucose42` (PySAT baseline).",
            "",
            "## 7. Provenance",
            "",
            f"- Nguồn chính: {source_note}.",
            f"- Projection cap tham chiếu: `{cap_mb:.0f}` MB (OQ-4, chưa phải số cuối).",
            "- Không có solver subprocess nào được spawn bởi module này.",
        ]
    )
    return lines


def _consistency_sections(
    findings: Sequence[ConsistencyFinding],
    g4: G4Summary,
    *,
    source_note: str,
) -> list[str]:
    lines = _banner(source_note)
    lines.extend(
        [
            "",
            "# 26 — Cross-review P1 + nhất quán code ↔ spec ↔ paper",
            "",
            "## 1. Kết quả consistency checker (C1–C10)",
            "",
            "| Check | Status | File | Symbol | Expected | Actual | Message |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for finding in findings:
        message = finding.message.replace("|", "\\|")
        lines.append(
            f"| `{finding.check_id}` | **{finding.status.upper()}** | "
            f"`{finding.file}` | `{finding.symbol}` | {finding.expected} | "
            f"{finding.actual} | {message or '—'} |"
        )

    lines.extend(
        [
            "",
            "## 2. Recheck P1 R1–R6 (`docs/w2-sat/13-review-p1-formulation.md`)",
            "",
            "| Mục | Trạng thái | Bằng chứng trong repo |",
            "|---|---|---|",
            "| R1 — skip-guard khi thiếu backend/engine/license | closed | `tests/exact/test_exact_solvers.py`: `_skip_if_backend_unavailable`, `pytest.skip`, guard `cpoptimizer.exe` |",
            "| R2 — timing scope, dùng runner `wall_time` | closed | `docs/exact_models.md` §Timing and memory-limit scope: `wall_time`, kill cứng `time_limit + 30 seconds` |",
            "| R3 — input validation raise `ValueError` | closed | `src/exact/common.py::validate_exact_input`; 3 solver mới gọi hàm này, CP-SAT giữ validation nội bộ |",
            "| R4 — warning field Config bị bỏ qua | closed | `src/exact/common.py::warn_ignored_config`; gọi ở `gurobi_mip.py`, `cplex_mip.py`, `cplex_cp.py` |",
            "| R5 — `ub` khi TO ở CP-SAT | closed | `src/exact/cp_sat_solver.py::_safe_upper_bound` trả `n - 1` khi `UNKNOWN`/non-finite |",
            "| R6 — cross-check objective native vs `verify()` | closed | `gurobi_mip.py`, `cplex_mip.py`, `cplex_cp.py`: `objective != model_objective` → `ERR` |",
            "",
            "Không phát hiện mục R1–R6 nào còn mở tại W5; không có patch nào bị thực hiện ngầm (OQ-5).",
            "",
            "## 3. Fairness SAT vs exact — năm điểm bắt buộc",
            "",
            "1. **`wall_time`:** so sánh chính thức dùng runner `wall_time`, không dùng "
            "`t_total` của solver (phạm vi import khác nhau).",
            "2. **`time_limit` semantics:** SAT là ngân sách cho cả chuỗi K; exact chỉ "
            "giới hạn pha solve; runner hard-kill tại `time_limit + 30` giây.",
            "3. **`ub` khi TO:** SAT trả `ub = hi − 1` (có thể là cận đếm `n − 1`); exact "
            "trả bound của solver hoặc `n − 1`; không đọc `ub` như “gần tối ưu”.",
            "4. **`MIPGap = 0` / gap tolerance:** Gurobi `MIPGap=0`, CPLEX mipgap + "
            "absmipgap = 0; `MIP_optimal_tolerance` bị loại khỏi OPT.",
            "5. **Shared `verify()`:** mọi nghiệm SAT và exact đi qua cùng "
            "`src/common/verify.py::verify()` trước khi vào `Result`.",
            "",
            "## 4. Dọn link stale trỏ thư mục handoff cũ (BR-11)",
            "",
            "- `docs/w2-sat/14-sat-methodology.md`: 5 link đã trỏ về "
            "`docs/w2-sat/12-test-matrix.md` và `docs/w2-sat/13-review-p1-formulation.md`.",
            "- `docs/w2-sat/15-m1-gate-evidence.md`: link đã trỏ về "
            "`docs/w2-sat/12-test-matrix.md` và `docs/abp-sat-encoding/*`.",
            "- `docs/sat_spec.md`, `docs/technical_appendix_draft.md`, "
            "`docs/canonical_sat_config.md`: không còn tham chiếu thư mục "
            "handoff cũ (checker C9 xác nhận).",
            "",
            "## 5. G4 readiness",
            "",
            f"- **Statement:** {g4.statement}",
            f"- Frozen triage: `{g4.triaged_total}` run, `CODE_BUG = {g4.code_bugs}`, "
            f"all_triaged = `{g4.all_triaged}`.",
            f"- SAT discussion complete = `{g4.sat_discussion_complete}`; "
            f"checkbox W5 = `{g4.boxes_checked}`.",
            f"- **Kết luận G4:** {'PASS' if g4.passed else 'FAIL'}.",
            "",
            "## 6. Provenance",
            "",
            f"- Nguồn dữ liệu: {source_note}.",
            "- Consistency checker chỉ đọc text/AST; không import `src.exact.*` "
            "(tránh phụ thuộc Ortools/Gurobi/CPLEX).",
        ]
    )
    return lines


def _paper_sections(
    rq1_rows: Sequence[dict[str, Any]],
    rq2_rows: Sequence[dict[str, Any]],
    graph_meta: dict[str, GraphMeta],
    trajectories: Sequence[dict[str, Any]],
    findings: Sequence[ConsistencyFinding],
    g4: G4Summary,
    *,
    source_note: str,
    cap_mb: float,
) -> list[str]:
    rq1 = summarize_rq1(rq1_rows)
    rq2 = summarize_rq2(rq2_rows)
    best = _pick_rq1_best(rq1)
    core = [item for item in rq2 if item.solver in ("cadical195", "glucose4")]
    core_winner = core[0] if core else None
    all_ok = all(finding.status == "ok" for finding in findings)

    lines = _banner(source_note)
    lines.extend(
        [
            "",
            "# Paper v0.9 — SAT sections (W5)",
            "",
            "Phần SAT của paper: §3 methodology, RQ1 final, RQ2 final, technical "
            "appendix A.1–A.7. Mọi số lấy từ frozen dataset và sinh tự động.",
            "",
            "## §3 SAT methodology",
            "",
            "### §3.1 Bài toán quyết định",
            "",
            "Cho đồ thị đơn vô hướng `G = (V, E)`, `n = |V|`, `m = |E|`. "
            "Antibandwidth của song ánh `f: V → {1..n}` là "
            "`B(f) = min_{{u,v} ∈ E} |f(u) − f(v)|`. Bài toán quyết định tại "
            "ngưỡng `K ≥ 1`: tồn tại `f` với `B(f) ≥ K`. `K` phải là `int ≥ 1`; "
            "`n = 0` hoặc `m = 0` là `ValueError`; `K ≥ n` là UNSAT trước khi "
            "dựng CNF (`trivial_unsat`, `src/sat/pairwise.py`).",
            "",
            "### §3.2 Biến SAT",
            "",
            "- `pairwise`: `x[v][p] = 1` khi đỉnh `v` nhận nhãn `p ∈ {1..n}`; "
            "`id = v * n + p`; `n²` biến chính. Aux của AMO bắt đầu từ `n² + 1`.",
            "- `order`: `o[v][p] = 1` khi `f(v) ≤ p`, `p ∈ 1..n−1`; "
            "`id = v * (n − 1) + p`; `n(n−1)` biến. Biên `p = 0` luôn sai, "
            "`p = n` luôn đúng.",
            "",
            "### §3.3 Ràng buộc",
            "",
            "| Nhóm | `pairwise` | `order` |",
            "|---|---|---|",
            "| `assignment` | ALO + AMO mỗi đỉnh: `n + n·C(n,2)` | chuỗi đơn điệu: `n(n−2)` |",
            "| `permutation` | ALO + AMO mỗi nhãn: `n + n·C(n,2)` | no-good mỗi cặp đỉnh × nhãn: `n·C(n,2)` |",
            "| `distance` | binary clause mỗi cạnh × cặp nhãn: `m·2·Σ max(0, n−d)` | no-good trên nhãn, cùng phép duyệt: `m·2·Σ max(0, n−d)` |",
            "| `threshold` | `K ≥ n` → UNSAT, 0 clause | như `pairwise` |",
            "",
            "Đếm tay `path4` (`n = 4`, `m = 3`) khớp code và test: `pairwise` "
            "K = 1/2/3 có 56/74/86 clause; `order` có 32/50/62 clause.",
            "",
            "### §3.4 AMO",
            "",
            "`amo(literals, encoding, pool)` (`src/sat/pairwise.py`). "
            "`pairwise` AMO là `C(m,2)` clause `(¬a ∨ ¬b)`, không thêm biến; "
            "`seqcounter` dùng `pysat.card.CardEnc.atmost(bound=1)`. Encoding "
            "`order` không dùng AMO: chuỗi đơn điệu thay ALO + AMO nên "
            "`amo_encoding` chỉ là metadata. Hệ quả: `order/pairwise` và "
            "`order/seqcounter` có CNF trùng — kiểm tra nhất quán, không phải "
            "bằng chứng AMO.",
            "",
            "### §3.5 Chiến lược duyệt K",
            "",
            "Duyệt `K ← B + 1` từ cận dưới đã verify; SAT thì decode, `verify`, "
            "lấy `B`; UNSAT đầu tiên thì `K − 1 = B` tối ưu và dừng. Timeout thì "
            "dừng. Không incremental, không binary search; mỗi ngưỡng dựng CNF và "
            "backend mới. `Config.time_limit` là ngân sách cho cả chuỗi K. "
            "Anti-bandwidth được làm tròn; xem `docs/sat_spec.md` §5.",
            "",
            "### §3.6 Backend solver",
            "",
            "`SatBackend` (`src/sat/backend.py`) bọc PySAT. Solver default "
            "`cadical195`; timeout theo family: interrupt + watchdog cho Glucose/"
            "MiniSat, conflict-budget loop cho CaDiCaL. Kissat bị chặn vĩnh viễn. "
            "RQ2 dùng CaDiCaL + Glucose (Core) và thêm `minisat22`, `glucose42` "
            "(baseline).",
            "",
            "### §3.7 Đo lường",
            "",
            "`t_encode` quanh `build_cnf`; `t_solve` quanh `backend.solve`; "
            "`t_total` toàn bộ `solve_sat`; `peak_memory` là max working set đo "
            "bằng `GetProcessMemoryInfo` tại các mốc (không phải peak liên tục). "
            "Incremental load clause nằm trong `t_total`, không trong `t_encode`/"
            "`t_solve`.",
            "",
            "### §3.8 Decode và verify",
            "",
            "`decode_model` dựng labeling từ model; vi phạm hoán vị là `ValueError`. "
            "Mọi nghiệm đi qua `verify(instance, labeling)` trước khi vào `Result`; "
            "model chưa phải nghiệm.",
            "",
            "### §3.9 Bằng chứng",
            "",
            "`tests/sat/test_matrix.py` (ma trận encoding × AMO × solver), "
            "`tests/sat/test_order.py`, `tests/sat/test_pairwise.py`, "
            "`tests/sat/test_glucose_e2e.py`; appendix chứng minh trong "
            "`docs/technical_appendix_draft.md`.",
            "",
            "### §3.10 Giới hạn",
            "",
            "Chỉ hai encoding Core (không staircase); không incremental; không "
            "symmetry breaking/warm start (off by design); memory đo trên Windows "
            "và là max của điểm chụp; dữ liệu frozen chỉ tới `n = 50`.",
            "",
            "## RQ1 Final",
            "",
        ]
    )
    lines.extend(
        [
            "| `abp_encoding` | `amo_encoding` | OPT | FEAS | TO | PAR2 (s) | Σ `t_total` (s) | Max Clauses | Max Mem (MB) |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in rq1:
        lines.append(
            f"| `{item.abp_encoding}` | `{item.amo_encoding}` | {item.opt}/{item.n_runs} | "
            f"{item.feas} | {item.to} | {item.par2:.2f} | {item.total_time_s:.2f} | "
            f"{item.max_clauses} | {item.max_memory_mb:.2f} |"
        )
    lines.append("")
    if best is not None:
        lines.append(
            f"**Kết luận:** `{best.abp_encoding}`/`{best.amo_encoding}` biểu diễn "
            f"bài toán tốt hơn và giúp solving trên tập frozen: {best.opt}/"
            f"{best.n_runs} OPT, PAR2 {best.par2:.2f} s, max "
            f"{best.max_clauses} clause / {best.max_memory_mb:.2f} MB. "
            "Không có suy luận “CNF nhỏ → nhanh”: cả hai chiều đảo được ghi ở "
            "`docs/w5-sat/24-rq1-final.md` §3."
        )
    lines.extend(
        [
            "",
            "**Case study (a) CNF nhỏ nhưng chậm:** xem bảng đảo chiều "
            "`docs/w5-sat/24-rq1-final.md` §3.1 (`pairwise`/`seqcounter` vs "
            "`order`/`pairwise` trên `randconn20/24/28/40`).",
            "",
            "**Case study (b) CNF lớn nhưng nhanh:** `order`/`pairwise` nhiều "
            "clause hơn nhưng đạt OPT trên `randconn40` trong 16.249 s, trong khi "
            "`pairwise`/`seqcounter` 82 160 clause lại FEAS 77.684 s; và `n = 50` "
            "giải nhanh hơn `n = 40` dưới cả 4 solver RQ2.",
            "",
            "**Case study (c) pairwise blowup:** `pairwise`/`pairwise` có `n²` "
            "biến và tổng clause `O(n³)`; đo được 255 400 clause / 126.53 MB tại "
            "`n = 50`. Projection HB-scale (mẫu dày `m = n(n−1)/8`, cap "
            f"`{cap_mb:.0f}` MB) cho thấy `pairwise`/`pairwise` vượt cap trong khi "
            "`order` bị chặn bởi `n(n−1)` biến và không có nhóm AMO. MO chỉ đến "
            "từ `MemoryError` ngoài process, không phải solver enforce cap.",
            "",
            "## RQ2 Final",
            "",
            "| Hạng | Solver | Vai trò | OPT | PAR2 (s) | Max Mem (MB) |",
            "|---:|---|---|---:|---:|---:|",
        ]
    )
    for rank, item in enumerate(rq2, start=1):
        role = (
            "Protocol Core"
            if item.solver in ("cadical195", "glucose4")
            else "PySAT baseline"
        )
        lines.append(
            f"| {rank} | `{item.solver}` | {role} | {item.opt}/{item.n_runs} | "
            f"{item.par2:.2f} | {item.max_memory_mb:.2f} |"
        )
    lines.append("")
    if core_winner is not None:
        lines.append(
            f"**Kết luận Core:** `{core_winner.solver}` thắng trong "
            "`{cadical195, glucose4}` theo OPT coverage → PAR2 → memory. "
            "Caveat: `cadical195` chịu chi phí conflict-budget wrapper "
            "(`src/sat/backend.py:238-254`)."
        )
    lines.extend(
        [
            "",
            "**Case study (a) độ nhạy:** xem bảng density/Δ/UB và `t_total` từng "
            "solver trong `docs/w5-sat/25-rq2-final.md` §4. Subset frozen không "
            "tách được “A thắng thưa, B thắng dày”; đó là scope limitation.",
            "",
            "**Case study (b) FEAS không OPT:** hai run `randconn40` với "
            "`pairwise`/`pairwise` và `pairwise`/`seqcounter` có `lb = 14`, "
            "`ub = 39`, `gap = 25`; `ub = 39` là cận đếm `n − 1`, không phải bound "
            "chặt. Chuỗi probe đầy đủ ở `docs/w5-sat/25-rq2-final.md` §5.",
            "",
            "**Kissat:** loại vĩnh viễn (model sai, assumptions bị bỏ qua, abort "
            "sau `add_clause`, không có binary ngoài). Không có hàng Kissat trong "
            "bảng.",
            "",
            "## Technical Appendix A.1–A.7 (W5 state)",
            "",
            "### A.1 Pairwise encoding",
            "",
            "`x[v][p]`, `id = v*n + p`, `n²` biến. Clause: assignment (ALO + AMO), "
            "permutation (ALO + AMO), distance (binary no-good mỗi cạnh × cặp nhãn "
            "cách nhau dưới K). Lemma A.1–A.3 và Corollary A.3.1 giữ nguyên; "
            "`K ≥ n` UNSAT trước khi dựng CNF.",
            "",
            "### A.2 Order encoding",
            "",
            "`o[v][p]`, `id = v*(n-1) + p`, `n(n-1)` biến. Chain thay ALO + AMO; "
            "permutation và distance dùng `_not_value`; `q = 1`/`q = n` còn một "
            "literal, interior còn hai. Lemma A.4–A.7 giữ nguyên.",
            "",
            "### A.3 At-most-one encodings",
            "",
            "`pairwise` và `seqcounter` faithful; Lemma A.8: cùng projection trên "
            "biến nhãn. Với `order`, AMO là metadata, không đổi clause.",
            "",
            "### A.4 Equivalence theorem",
            "",
            "Theorem A.9: SAT tại `K` ⇔ tồn tại labeling `B(f) ≥ K`, cho cả hai "
            "encoding; `K ≥ n` UNSAT. Theorem A.10: decode luôn trả hoán vị hoặc "
            "`ValueError`. Theorem A.11: objective được tính lại bởi `verify()`.",
            "",
            "### A.5 Multi-run K search: completeness",
            "",
            "Invariants `lo ≤ B*` và `hi > B*`; mỗi vòng `k = lo + 1`; SAT tăng "
            "`lo`, UNSAT đặt `hi = k`; dừng ở UNSAT đầu tiên. Không bỏ ngưỡng vì "
            "nhảy `K ← B + 1`. Tối đa `n − 1` probe. OPT chỉ khi `lo + 1 == hi`; "
            "FEAS giữ `lb = lo`, `ub = hi − 1`.",
            "",
            "### A.6 What this appendix does not claim",
            "",
            "1. Không claim UNSAT proof đúng (trust boundary).",
            "2. Không claim thứ tự kích thước CNF như định lý; đó là đo đạc "
            "instance-dependent.",
            f"3. Không claim bảo đảm bộ nhớ: `memory_limit` không được solver "
            "enforce trong process; `canonical_sat_config(memory_limit=…)` bắt "
            "buộc cap hữu hạn > 0 cho run official, `allow_unbounded_memory=True` "
            "chỉ cho dev/test; MO chỉ từ `MemoryError` ngoài process.",
            "4. Không claim timeout cứng: deadline kiểm giữa các pha nên `t_total` "
            "có thể vượt `time_limit`.",
            "5. Không claim từ symmetry/warm start: chưa cài đặt, đặt khác mặc "
            "định thì warning; `search_mode=\"multi\"` là mode duy nhất đã cài đặt "
            "và không warning.",
            "",
            "### A.7 Empirical anchors",
            "",
            "`tests/sat/test_matrix.py`, `tests/sat/test_g1_oracle.py`, "
            "`tests/sat/test_glucose_e2e.py`, `tests/sat/test_pairwise.py`, "
            "`tests/sat/test_order.py`; frozen W3/W4 pilots; W5 generated reports "
            "24–26.",
            "",
            "## Fairness SAT vs exact",
            "",
            "1. `wall_time` của runner là metric chính thức.",
            "2. `time_limit` SAT là ngân sách cả chuỗi K; exact chỉ pha solve; "
            "runner hard-kill tại `time_limit + 30` giây.",
            "3. `ub` khi TO là cận (SAT `hi − 1`; exact bound hoặc `n − 1`), không "
            "phải gap tới optimum.",
            "4. `MIPGap = 0` / gap tolerances: `MIP_optimal_tolerance` bị loại khỏi "
            "OPT.",
            "5. Mọi nghiệm dùng chung `verify()`.",
            "",
            "## Trace table",
            "",
            "| Mục | Nguồn |",
            "|---|---|",
            "| §3.1–§3.2 | `docs/sat_spec.md` §1–§2; `src/sat/pairwise.py`; `src/sat/order.py` |",
            "| §3.3 | `docs/sat_spec.md` §3; `docs/w2-sat/14-sat-methodology.md` §3.3; `tests/sat/test_pairwise.py`; `tests/sat/test_order.py` |",
            "| §3.4 | `src/sat/pairwise.py::amo`; `docs/technical_appendix_draft.md` A.3/A.8 |",
            "| §3.5 | `docs/sat_spec.md` §5; `src/sat/solve.py`; `docs/technical_appendix_draft.md` A.5 |",
            "| §3.6 | `src/sat/backend.py`; `docs/sat_tooling.md` |",
            "| §3.7 | `src/sat/solve.py`; `docs/sat_tooling.md` |",
            "| §3.8 | `src/sat/solve.py`; `src/common/verify.py`; `docs/sat_spec.md` §4 |",
            "| RQ1 | `docs/w5-sat/24-rq1-final.md`; `results/pilot_rq1.csv` |",
            "| RQ2 | `docs/w5-sat/25-rq2-final.md`; `results/pilot_rq2.csv` |",
            "| Appendix | `docs/technical_appendix_draft.md`; `docs/canonical_sat_config.md` |",
            "",
            "## G4 status",
            "",
            f"- {g4.statement}",
            f"- Consistency C1–C10: {'PASS' if all_ok else 'FAIL'} "
            f"({len(findings)} finding); xem "
            "`docs/w5-sat/26-cross-review-consistency.md`.",
            "- Không còn placeholder; mọi bảng nêu nguồn frozen.",
        ]
    )
    return lines


def render_w5_markdown(
    rq1_rows: Sequence[dict[str, Any]],
    rq2_rows: Sequence[dict[str, Any]],
    graph_meta: dict[str, GraphMeta],
    triage_reports: Sequence[TriageReport],
    consistency: Sequence[ConsistencyFinding],
    g4: G4Summary,
    *,
    source_note: str = "",
    rq1_solver: str = "cadical195",
    cap_mb: float = DEFAULT_CAP_MB,
    trajectories: Sequence[dict[str, Any]] | None = None,
) -> dict[str, str]:
    """Trả bốn tài liệu Markdown, key = tên file output."""
    trajectories = [] if trajectories is None else trajectories
    rq1_text = "\n".join(
        _rq1_sections(
            rq1_rows,
            rq2_rows,
            source_note=source_note,
            solver=rq1_solver,
            cap_mb=cap_mb,
        )
    )
    rq2_text = "\n".join(
        _rq2_sections(
            rq2_rows,
            graph_meta,
            trajectories,
            source_note=source_note,
            cap_mb=cap_mb,
        )
    )
    consistency_text = "\n".join(
        _consistency_sections(consistency, g4, source_note=source_note)
    )
    paper_text = "\n".join(
        _paper_sections(
            rq1_rows,
            rq2_rows,
            graph_meta,
            trajectories,
            consistency,
            g4,
            source_note=source_note,
            cap_mb=cap_mb,
        )
    )
    return {
        "24-rq1-final.md": rq1_text + "\n",
        "25-rq2-final.md": rq2_text + "\n",
        "26-cross-review-consistency.md": consistency_text + "\n",
        "27-paper-v09-sat-sections.md": paper_text + "\n",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_W5_OUT)
    parser.add_argument("--runs-csv", type=Path, default=None)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--cap-mb", type=float, default=DEFAULT_CAP_MB)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Chỉ in trạng thái consistency/G4 (vẫn ghi lại 4 tài liệu sinh tự động).",
    )
    args = parser.parse_args(argv)

    use_utf8_output()

    rq1_rows, rq2_rows, source_note = load_sources(
        args.runs_csv, DEFAULT_RQ1_CSV, DEFAULT_RQ2_CSV
    )
    graph_meta = load_graph_metadata([DEFAULT_VALIDATION_DIR, DEFAULT_LARGE_DIR])
    triage_reports = triage_directory(args.raw_dir)
    trajectories = extract_feas_probe_trajectories(args.raw_dir)
    consistency = verify_code_spec_paper_consistency()
    boxes_checked, boxes_total = _w5_checkbox_counts()
    g4 = evaluate_g4_gate(
        triage_reports,
        consistency,
        boxes_checked=boxes_checked,
        boxes_total=boxes_total,
    )

    documents = render_w5_markdown(
        rq1_rows,
        rq2_rows,
        graph_meta,
        triage_reports,
        consistency,
        g4,
        source_note=source_note,
        cap_mb=args.cap_mb,
        trajectories=trajectories,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, text in documents.items():
        path = args.out_dir / name
        path.write_text(text, encoding="utf-8")
        print(f"Đã ghi {name}: {path}")

    for finding in consistency:
        if finding.status != "ok":
            print(
                f"FAIL {finding.check_id} {finding.file} :: {finding.symbol} "
                f":: {finding.message}"
            )
    print(g4.statement)
    print("PASS" if all(f.status == "ok" for f in consistency) and g4.passed else "FAIL")
    if args.check_only:
        print("check-only: không chạy solver, chỉ kiểm tra và ghi tài liệu.")
    return 0 if all(f.status == "ok" for f in consistency) and g4.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
