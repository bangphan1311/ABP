"""Test phân tích RQ1, RQ2 và kiểm tra cổng G3 (W4, ticket 23 / #30)."""

from __future__ import annotations

import csv

import pytest

from experiments.analyze_rq1_rq2 import (
    DEFAULT_REPORT_PATH,
    DEFAULT_RQ1_CSV,
    DEFAULT_RQ2_CSV,
    evaluate_g3_gate,
    find_smaller_cnf_slower_solve_cases,
    load_csv_rows,
    main as analyze_main,
    normalize_row,
    render_markdown_report,
    summarize_rq1,
    summarize_rq2,
)
from experiments.pilot_common import REPO_ROOT
from src.sat.triage import TriageReport


def _row(**overrides) -> dict:
    """Một hàng chuẩn hóa; đổi trục bằng ``overrides``."""
    raw = {
        "run_id": "i1__sat__order__pairwise__cadical195__multi__sym0__ws0__s0",
        "instance": "i1",
        "method": "sat",
        "abp_encoding": "order",
        "amo_encoding": "pairwise",
        "solver": "cadical195",
        "status": "OPT",
        "lb": 2,
        "ub": 2,
        "t_encode": 0.01,
        "t_solve": 0.02,
        "t_total": 0.03,
        "variables": 12,
        "clauses": 62,
        "peak_memory": 20.0,
        "time_limit": 60.0,
    }
    raw.update(overrides)
    return normalize_row(raw)


def _ok_triage() -> list[TriageReport]:
    return [
        TriageReport(
            run_id="r1",
            instance_id="p4",
            status="OPT",
            category="OK",
            is_anomaly=False,
            reasons=["ok"],
        ),
        TriageReport(
            run_id="r2",
            instance_id="p5",
            status="FEAS",
            category="SOLVER_BEHAVIOR",
            is_anomaly=True,
            reasons=["timeout after incumbent"],
        ),
    ]


def test_summarize_rq1_and_smaller_cnf_slower_solve():
    rows = load_csv_rows(DEFAULT_RQ1_CSV)
    summaries = summarize_rq1(rows)

    assert len(summaries) == 4
    by_pair = {(s.abp_encoding, s.amo_encoding): s for s in summaries}
    assert by_pair[("order", "pairwise")].opt == 10
    assert by_pair[("pairwise", "pairwise")].opt == 9
    assert by_pair[("pairwise", "seqcounter")].opt == 9

    # order/pairwise và order/seqcounter có cùng số biến & mệnh đề.
    assert (
        by_pair[("order", "pairwise")].max_clauses
        == by_pair[("order", "seqcounter")].max_clauses
    )

    # Kiểm tra bằng chứng CNF nhỏ hơn nhưng giải chậm hơn.
    cases = find_smaller_cnf_slower_solve_cases(rows)
    assert len(cases) >= 1
    assert all(c["smaller_clauses"] < c["larger_clauses"] for c in cases)
    assert all(c["smaller_time"] > c["larger_time"] for c in cases)


def test_summarize_rq2_ranks_by_coverage_and_par2():
    rows = load_csv_rows(DEFAULT_RQ2_CSV)
    summaries = summarize_rq2(rows)

    assert [s.solver for s in summaries] == [
        "minisat22",
        "glucose4",
        "glucose42",
        "cadical195",
    ]
    assert all(s.opt == 10 and s.to == 0 and s.err == 0 for s in summaries)


def test_evaluate_g3_gate_enforces_80_percent_and_zero_code_bugs():
    ok_triage = [
        TriageReport(
            run_id="r1",
            instance_id="p4",
            status="OPT",
            category="OK",
            is_anomaly=False,
            reasons=["ok"],
        ),
        TriageReport(
            run_id="r2",
            instance_id="p5",
            status="FEAS",
            category="SOLVER_BEHAVIOR",
            is_anomaly=True,
            reasons=["timeout after incumbent"],
        ),
    ]

    gate_pass = evaluate_g3_gate(80, 100, ok_triage)
    assert gate_pass.passed_completion is True
    assert gate_pass.passed_gate is True

    gate_low = evaluate_g3_gate(79, 100, ok_triage)
    assert gate_low.passed_completion is False
    assert gate_low.passed_gate is False

    bug_triage = ok_triage + [
        TriageReport(
            run_id="r3",
            instance_id="p6",
            status="OPT",
            category="CODE_BUG",
            is_anomaly=True,
            reasons=["lb != verified"],
        )
    ]
    gate_bug = evaluate_g3_gate(95, 100, bug_triage)
    assert gate_bug.code_bugs_count == 1
    assert gate_bug.passed_gate is False


def test_summarize_rq1_filters_solver_and_control_axes():
    rows = [
        _row(),
        _row(instance="i2", run_id="i2__sat__order__pairwise__cadical195__multi__sym0__ws0__s0"),
        _row(
            solver="glucose4",
            run_id="i1__sat__order__pairwise__glucose4__multi__sym0__ws0__s0",
        ),
        # Lệch trục điều khiển: symmetry ON, warm start ON, search mode khác multi.
        _row(instance="i3", run_id="i3__sat__order__pairwise__cadical195__multi__sym1__ws0__s0"),
        _row(instance="i4", run_id="i4__sat__order__pairwise__cadical195__multi__sym0__ws1__s0"),
        _row(
            instance="i5",
            run_id="i5__sat__order__pairwise__cadical195__multi__sym0__ws0__s0",
            search_mode="staircase",
        ),
    ]

    default = summarize_rq1(rows)
    assert [(s.abp_encoding, s.amo_encoding, s.n_runs) for s in default] == [
        ("order", "pairwise", 2)
    ]

    glucose = summarize_rq1(rows, solver="glucose4")
    assert [(s.abp_encoding, s.amo_encoding, s.n_runs) for s in glucose] == [
        ("order", "pairwise", 1)
    ]


def test_summarize_rq2_filters_encoding_pair():
    rows = [
        _row(),
        _row(
            solver="glucose4",
            run_id="i1__sat__order__pairwise__glucose4__multi__sym0__ws0__s0",
        ),
        # order/seqcounter trùng CNF với order/pairwise: phải bị loại khỏi lát cắt mặc định.
        _row(
            amo_encoding="seqcounter",
            run_id="i1__sat__order__seqcounter__cadical195__multi__sym0__ws0__s0",
        ),
        _row(
            abp_encoding="pairwise",
            amo_encoding="seqcounter",
            run_id="i1__sat__pairwise__seqcounter__cadical195__multi__sym0__ws0__s0",
        ),
    ]

    default = summarize_rq2(rows)
    assert [s.solver for s in default] == ["cadical195", "glucose4"]
    assert all(s.n_runs == 1 for s in default)

    swapped = summarize_rq2(rows, amo_encoding="seqcounter")
    assert [(s.solver, s.n_runs) for s in swapped] == [
        ("cadical195", 1),
    ]


def test_evaluate_g3_gate_none_expected_is_pending():
    ok_triage = _ok_triage()

    gate = evaluate_g3_gate(70, None, ok_triage)
    assert gate.expected_runs is None
    assert gate.completion_ratio is None
    assert gate.passed_completion is False
    assert gate.passed_gate is False
    assert gate.gate_status == "PENDING"

    empty = evaluate_g3_gate(0, None, ok_triage)
    assert empty.gate_status == "PENDING"
    assert empty.completion_ratio is None


def test_evaluate_g3_gate_zero_expected_still_raises():
    ok_triage = _ok_triage()

    with pytest.raises(ValueError):
        evaluate_g3_gate(0, 0, ok_triage)
    with pytest.raises(ValueError):
        evaluate_g3_gate(0, True, ok_triage)


def test_render_markdown_report_pending_without_expected_runs():
    rows = [_row()]
    text = render_markdown_report(rows, rows, _ok_triage())

    assert "PENDING" in text
    assert "100.0%" not in text
    assert "expected_runs phải > 0" not in text


def test_default_report_path_resolves():
    assert (
        DEFAULT_REPORT_PATH
        == REPO_ROOT / "docs" / "w4-sat" / "23-rq1-rq2-draft-analysis.md"
    )


def test_analyze_cli_supports_single_runs_csv(tmp_path):
    runs_csv = tmp_path / "runs.csv"
    with runs_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "run_id",
                "instance",
                "method",
                "abp_encoding",
                "amo_encoding",
                "solver",
                "status",
                "lb",
                "ub",
                "t_encode",
                "t_solve",
                "t_total",
                "variables",
                "clauses",
                "peak_memory",
                "time_limit",
                "error",
            ),
        )
        writer.writeheader()
        writer.writerow(
            {
                "run_id": "i1__sat__order__pairwise__glucose4",
                "instance": "i1",
                "method": "sat",
                "abp_encoding": "order",
                "amo_encoding": "pairwise",
                "solver": "glucose4",
                "status": "OPT",
                "lb": 2,
                "ub": 2,
                "t_encode": 0.01,
                "t_solve": 0.02,
                "t_total": 0.03,
                "variables": 12,
                "clauses": 62,
                "peak_memory": 20.0,
                "time_limit": 60.0,
                "error": "",
            }
        )

    out_md = tmp_path / "report.md"
    rc = analyze_main(
        [
            "--runs-csv",
            str(runs_csv),
            "--raw-dir",
            str(tmp_path / "empty_raw"),
            "--out",
            str(out_md),
            "--rq1-solver",
            "glucose4",
            "--rq2-abp-encoding",
            "order",
            "--rq2-amo-encoding",
            "pairwise",
        ]
    )
    assert rc == 0
    text = out_md.read_text(encoding="utf-8")
    assert "Phân tích RQ1" in text
    assert "Phân tích RQ2" in text
    assert "Kiểm tra cổng G3" in text
