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
    split_combined_rq_rows,
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
    ok_triage.extend(
        TriageReport(
            run_id=f"r{i}",
            instance_id=f"p{i}",
            status="OPT",
            category="OK",
            is_anomaly=False,
            reasons=["ok"],
        )
        for i in range(3, 81)
    )

    gate_pass = evaluate_g3_gate(80, 100, ok_triage)
    assert gate_pass.passed_completion is True
    assert gate_pass.passed_gate is True

    gate_low = evaluate_g3_gate(79, 100, ok_triage[:79])
    assert gate_low.passed_completion is False
    assert gate_low.passed_gate is False

    bug_triage = ok_triage[:79] + [
        TriageReport(
            run_id="r81",
            instance_id="p81",
            status="OPT",
            category="CODE_BUG",
            is_anomaly=True,
            reasons=["lb != verified"],
        )
    ]
    gate_bug = evaluate_g3_gate(80, 100, bug_triage)
    assert gate_bug.code_bugs_count == 1
    assert gate_bug.passed_gate is False

    missing_raw = evaluate_g3_gate(80, 100, ok_triage, missing_raw_records=1)
    assert missing_raw.missing_raw_records_count == 1
    assert missing_raw.passed_gate is False

    with pytest.raises(ValueError, match="không khớp số triage report"):
        evaluate_g3_gate(80, 100, ok_triage[:2])


def test_evaluate_g3_gate_rejects_unrecognized_non_anomaly_category():
    bad_category = TriageReport(
        run_id="unexpected",
        instance_id="p1",
        status="OPT",
        category="UNRECOGNIZED",
        is_anomaly=False,
        reasons=[],
    )
    result = evaluate_g3_gate(1, 2, [bad_category])
    assert result.unclassified_anomalies == 1
    assert result.passed_gate is False


def test_render_g3_does_not_drop_invalid_status_rows_from_core_denominator():
    def row(run_id, instance, encoding, amo, solver, status):
        return {
            "run_id": run_id,
            "instance": instance,
            "method": "sat",
            "abp_encoding": encoding,
            "amo_encoding": amo,
            "solver": solver,
            "search_mode": "multi",
            "status": status,
            "lb": 2 if status == "OPT" else None,
            "ub": 2 if status == "OPT" else None,
            "t_encode": 0.01,
            "t_solve": 0.02,
            "t_total": 0.03,
            "variables": 12,
            "clauses": 62,
            "peak_memory": 20.0,
            "time_limit": 60.0,
        }

    invalid = row("r-invalid", "i1", "pairwise", "pairwise", "cadical195", "BROKEN")
    rq1_rows = [
        invalid,
        row("r2", "i2", "pairwise", "seqcounter", "cadical195", "OPT"),
        row("r3", "i3", "order", "pairwise", "cadical195", "OPT"),
    ]
    rq2_rows = [
        row("r4", "i4", "order", "pairwise", "glucose4", "OPT"),
        row("r5", "i5", "order", "pairwise", "glucose4", "OPT"),
    ]
    reports = [
        TriageReport(
            run_id="r-invalid", instance_id="i1", status="BROKEN",
            category="CODE_BUG", is_anomaly=True, reasons=["invalid status"],
        ),
        *[
            TriageReport(
                run_id=run_id, instance_id=instance, status="OPT",
                category="OK", is_anomaly=False, reasons=["ok"],
            )
            for run_id, instance in [
                ("r2", "i2"), ("r3", "i3"), ("r4", "i4"), ("r5", "i5")
            ]
        ],
    ]

    report = render_markdown_report(
        rq1_rows, rq2_rows, reports, expected_core_runs=5
    )
    assert "5 / 5" in report
    assert "lỗi correctness `CODE_BUG`: `1`" in report
    assert "**FAIL**" in report


def test_split_combined_runs_csv_keeps_rq1_and_rq2_axes_separate():
    def row(run_id, method, encoding, amo, solver, search_mode="multi"):
        return {
            "run_id": run_id, "method": method,
            "abp_encoding": encoding, "amo_encoding": amo,
            "solver": solver, "search_mode": search_mode,
        }

    rows = [
        row("r1", "sat", "pairwise", "pairwise", "cadical195"),
        row("r2", "sat", "pairwise", "seqcounter", "cadical195"),
        row("r3", "sat", "order", "pairwise", "cadical195"),
        row("r4", "sat", "order", "seqcounter", "cadical195"),  # CNF trùng, bỏ
        row("r5", "sat", "order", "pairwise", "glucose4"),
        row("r6", "sat", "order", "pairwise", "minisat22"),  # ngoài Core
        row("r7", "exact", "", "", "cp_sat"),
    ]
    rq1, rq2 = split_combined_rq_rows(rows)
    assert [r["run_id"] for r in rq1] == ["r1", "r2", "r3"]
    assert [r["run_id"] for r in rq2] == ["r3", "r5"]


def test_real_pilot_sources_produce_forty_unique_core_runs():
    pilot_rows = load_csv_rows(DEFAULT_RQ1_CSV) + load_csv_rows(DEFAULT_RQ2_CSV)
    rq1, rq2 = split_combined_rq_rows(pilot_rows)
    assert len(rq1) == 30  # 10 instances × 3 unique CNFs
    assert len(rq2) == 20  # 10 instances × 2 Protocol Core solvers
    assert len({r["run_id"] for r in rq1 + rq2}) == 40  # CaDiCaL reused

def test_shared_cadical_run_is_retained_in_both_rq_axes_once():
    pilot_rows = load_csv_rows(DEFAULT_RQ1_CSV) + load_csv_rows(DEFAULT_RQ2_CSV)
    rq1, rq2 = split_combined_rq_rows(pilot_rows)
    rq1_ids = {row["run_id"] for row in rq1}
    rq2_ids = {row["run_id"] for row in rq2}
    shared_ids = rq1_ids & rq2_ids

    assert len(rq1) == 30
    assert len(rq2) == 20
    assert len(shared_ids) == 10
    assert all("__cadical195__" in run_id for run_id in shared_ids)
    assert len(rq1_ids | rq2_ids) == 40


def test_split_rejects_conflicting_duplicate_run_id():
    row_a = {
        "run_id": "shared-1", "method": "sat", "search_mode": "multi",
        "solver": "cadical195", "abp_encoding": "order", "amo_encoding": "pairwise",
        "status": "OPT",
    }
    row_b = {**row_a, "status": "FEAS"}
    with pytest.raises(ValueError, match="payload mâu thuẫn"):
        split_combined_rq_rows([row_a, row_b])


def test_split_rejects_core_rows_without_run_id():
    row = {
        "method": "sat", "search_mode": "multi", "solver": "cadical195",
        "abp_encoding": "order", "amo_encoding": "pairwise", "status": "OPT",
    }
    with pytest.raises(ValueError, match="thiếu run_id"):
        split_combined_rq_rows([row])


def test_g3_rejects_completed_runs_above_expected_denominator():
    with pytest.raises(ValueError, match="lớn hơn expected_runs"):
        evaluate_g3_gate(41, 40, [])


def test_g3_rejects_invalid_denominator_and_threshold():
    with pytest.raises(ValueError, match="số nguyên > 0"):
        evaluate_g3_gate(1, True, [])
    with pytest.raises(ValueError, match="threshold"):
        evaluate_g3_gate(1, 10, [], threshold=1.1)


def test_render_report_rejects_expected_count_below_observed_core_ids():
    pilot_rows = load_csv_rows(DEFAULT_RQ1_CSV) + load_csv_rows(DEFAULT_RQ2_CSV)
    rq1, rq2 = split_combined_rq_rows(pilot_rows)
    with pytest.raises(ValueError, match="nhỏ hơn 40 unique Core run IDs"):
        render_markdown_report(rq1, rq2, [], expected_core_runs=39)


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
        writer.writerow(
            {
                "run_id": "i1__sat__pairwise__pairwise__cadical195",
                "instance": "i1", "method": "sat",
                "abp_encoding": "pairwise", "amo_encoding": "pairwise",
                "solver": "cadical195", "status": "OPT", "lb": 2, "ub": 2,
                "t_encode": 0.01, "t_solve": 0.02, "t_total": 0.03,
                "variables": 16, "clauses": 74, "peak_memory": 20.0,
                "time_limit": 60.0, "error": "",
            }
        )

    out_md = tmp_path / "report.md"
    rc = analyze_main(
        [
            "--runs-csv",
            str(runs_csv),
            "--raw-dir",
            str(tmp_path / "empty_raw"),
            "--expected-runs",
            "2",
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
