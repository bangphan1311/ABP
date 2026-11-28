"""Test bộ audit W6: terminology, claim, appendix, correlation, table, M3 gate, CLI."""

from __future__ import annotations

import re

import pytest

from experiments.w5_final_analysis import ConsistencyFinding, verify_code_spec_paper_consistency
from experiments.w6_signoff import (
    APPENDIX,
    CANONICAL,
    CLAIM_PATHS,
    CORR_PATHS,
    SAT_SPEC,
    TABLE_PATHS,
    TERM_PATHS,
    W1_ISSUES,
    W6_ISSUES,
    audit_correlation_hygiene,
    audit_terminology,
    audit_threshold_semantics,
    audit_variable_conventions,
    check_appendix_integrity,
    check_lemma_numbering,
    checkboxes_ok,
    collect_w6_findings,
    emit_w1_checkbox_edits,
    emit_w6_checkbox_edits,
    evaluate_m3_gate,
    lint_markdown_tables,
    main as w6_main,
    m3_finding,
    open_boxes,
    record_deferred_items,
    verify_claims,
)
from experiments.pilot_common import REPO_ROOT
from src.sat import order
from src.sat.triage import DEFAULT_RAW_DIR, triage_directory

import experiments.w6_signoff as w6

TEST_FILE = "tests/experiments/test_w6_signoff.py"


def _broken(findings):
    return [finding for finding in findings if finding.status != "ok"]


def test_terminology_clean_repo_passes():
    findings = audit_terminology(TERM_PATHS)
    assert _broken(findings) == [], [finding.message for finding in _broken(findings)]
    assert {finding.check_id for finding in findings} == {
        "W6-T1",
        "W6-T2",
        "W6-T3",
        "W6-T4",
        "W6-T5",
    }


def test_terminology_seeded_TIMEOUT_names_file(tmp_path):
    copy = tmp_path / "sat_spec.md"
    copy.write_text(
        SAT_SPEC.read_text(encoding="utf-8") + '\nstatus: "TIMEOUT"\n',
        encoding="utf-8",
    )
    broken = _broken(audit_terminology([copy]))
    assert len(broken) == 1
    assert broken[0].check_id == "W6-T4"
    assert "sat_spec.md" in broken[0].message
    assert "TIMEOUT" in broken[0].message


def test_terminology_bad_solver_kissat_grid(tmp_path):
    copy = tmp_path / "canonical_sat_config.md"
    copy.write_text(
        CANONICAL.read_text(encoding="utf-8") + "\n| `sat_solver` | `kissat404` |\n",
        encoding="utf-8",
    )
    broken = _broken(audit_terminology(list(TERM_PATHS) + [copy]))
    assert len(broken) == 1
    assert broken[0].check_id == "W6-T5"
    assert "kissat" in broken[0].message.lower()


def test_variable_conventions_ok_and_perturb(monkeypatch):
    assert _broken(audit_variable_conventions()) == []

    original = order.build_cnf

    def wrong_var_of(instance, k, amo_encoding="pairwise"):
        cnf = original(instance, k, amo_encoding)
        cnf.var_of = {
            (v, p): v * (instance.n - 1)
            for v in range(instance.n)
            for p in range(1, instance.n)
        }
        return cnf

    monkeypatch.setattr(order, "build_cnf", wrong_var_of)
    broken = _broken(audit_variable_conventions())
    assert len(broken) == 1
    assert broken[0].check_id == "W6-T6"
    assert broken[0].file.endswith("sat_spec.md")
    assert "var_of" in broken[0].symbol
    assert "v*(n-1)+p" in broken[0].expected


def test_threshold_semantics_ok_and_K_gt_n_fails(tmp_path):
    assert _broken(audit_threshold_semantics()) == []
    copy = tmp_path / "spec_variant.md"
    copy.write_text("Ngưỡng: `K > n`: UNSAT.\n", encoding="utf-8")
    broken = _broken(audit_threshold_semantics([copy]))
    assert len(broken) == 1
    assert broken[0].check_id == "W6-T7"
    assert "spec_variant.md" in broken[0].message
    assert "K > n" in broken[0].message


def test_verify_claims_clean_and_seeded_phrase(tmp_path):
    assert verify_claims(CLAIM_PATHS) == []
    copy = tmp_path / "24-rq1-final.md"
    copy.write_text(
        APPENDIX.read_text(encoding="utf-8") + "\n`order` is always faster.\n",
        encoding="utf-8",
    )
    broken = _broken(verify_claims([copy]))
    assert len(broken) == 1
    assert broken[0].check_id == "W6-C1"
    assert "24-rq1-final.md" in broken[0].message
    assert "always faster" in broken[0].message


def test_lemma_numbering_ok_and_dup_gap(tmp_path):
    assert _broken(check_lemma_numbering()) == []

    text = APPENDIX.read_text(encoding="utf-8")
    duplicate = tmp_path / "duplicate.md"
    duplicate.write_text(text + "\n**Lemma A.5 (dup).**\n", encoding="utf-8")
    broken = _broken(check_lemma_numbering(duplicate))
    assert len(broken) == 1
    assert broken[0].check_id == "W6-C2"
    assert "A.5" in broken[0].message

    gap_text = re.sub(r"\*\*Lemma A\.6 \(permutation for order\)\.\*\*", "", text)
    gap = tmp_path / "gap.md"
    gap.write_text(gap_text, encoding="utf-8")
    broken = _broken(check_lemma_numbering(gap))
    assert len(broken) == 1
    assert "A.6" in broken[0].message


def test_appendix_integrity_ok_and_missing_section(tmp_path):
    assert _broken(check_appendix_integrity()) == []
    copy = tmp_path / "appendix.md"
    copy.write_text(
        APPENDIX.read_text(encoding="utf-8").replace(
            "## A.6 What this appendix does not claim", "## Not claimed"
        ),
        encoding="utf-8",
    )
    broken = _broken(check_appendix_integrity(appendix=copy))
    assert len(broken) == 1
    assert broken[0].check_id == "W6-C3"
    assert "missing-section:A.6" in broken[0].message


def test_correlation_hygiene_ok_and_determines(tmp_path):
    assert audit_correlation_hygiene(CORR_PATHS) == []
    copy = tmp_path / "24-rq1-final.md"
    copy.write_text("n determines runtime directly.\n", encoding="utf-8")
    broken = _broken(audit_correlation_hygiene([copy]))
    assert len(broken) == 1
    assert broken[0].check_id == "W6-L1"
    assert "24-rq1-final.md" in broken[0].message
    assert "determines" in broken[0].message
    assert "dòng 1" in broken[0].symbol

    # Qualifier trên cùng dòng không cứu khẳng định nhân quả trực tiếp (BR-8).
    qualified = tmp_path / "25-rq2-final.md"
    qualified.write_text(
        "n causes higher runtime on this subset; measured.\n", encoding="utf-8"
    )
    broken = _broken(audit_correlation_hygiene([qualified]))
    assert len(broken) == 1
    assert broken[0].check_id == "W6-L1"
    assert "causes" in broken[0].message


def test_markdown_tables_ok_and_broken_row(tmp_path):
    assert lint_markdown_tables(TABLE_PATHS) == []
    copy = tmp_path / "broken.md"
    copy.write_text(
        "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 |\n",
        encoding="utf-8",
    )
    broken = _broken(lint_markdown_tables([copy]))
    assert len(broken) == 1
    assert broken[0].check_id == "W6-L2"
    assert "dòng 4" in broken[0].symbol


def test_deferred_items_are_explicit():
    items = record_deferred_items()
    assert len(items) == 6
    assert all(entry["status"] == "deferred" for entry in items)
    assert {entry["owner"] for entry in items} == {"P1", "P1+P2", "P3"}
    assert any("runs.csv" in entry["item"] for entry in items)


def test_w1_w6_checkbox_edits_and_evidence_paths():
    w1 = emit_w1_checkbox_edits(W1_ISSUES)
    assert len(w1) == len(W1_ISSUES) == 7
    for edit in w1:
        assert "- [ ]" not in edit["merged_text"], edit["file"]
        checked = [
            line
            for line in edit["merged_text"].splitlines()
            if line.lstrip().startswith("- [x]")
        ]
        assert checked, edit["file"]
        for line in checked:
            found = re.search(r"\(evidence: `([^`]+)`\)", line)
            assert found, (edit["file"], line)
            token = found.group(1)
            assert (REPO_ROOT / token).is_file(), token
            assert "docs/handoff/" not in token

    w6_edits = emit_w6_checkbox_edits(W6_ISSUES)
    assert len(w6_edits) == len(W6_ISSUES) == 4
    for edit in w6_edits:
        assert "- [ ]" not in edit["merged_text"], edit["file"]
        assert TEST_FILE in edit["merged_text"]
    assert checkboxes_ok()


def test_m3_gate_pass_clean_repo():
    summary = evaluate_m3_gate(
        verify_code_spec_paper_consistency(),
        triage_directory(DEFAULT_RAW_DIR),
        collect_w6_findings(),
        boxes_ok=True,
    )
    assert summary.passed is True
    assert summary.w5_ok is True
    assert summary.checks_ok is True
    assert summary.triaged_total == 70
    assert summary.code_bugs == 0
    assert "PASS (in-repo SAT scope)" in summary.statement
    for entry in record_deferred_items():
        assert entry["item"] in summary.statement


def test_m3_gate_fails_on_component():
    seeded = ConsistencyFinding(
        check_id="W6-L1",
        status="fail",
        file="docs/w5-sat/24-rq1-final.md",
        symbol="dòng 1",
        expected="correlation",
        actual="determines",
        message="seeded regression",
    )
    summary = evaluate_m3_gate(
        verify_code_spec_paper_consistency(),
        triage_directory(DEFAULT_RAW_DIR),
        [*collect_w6_findings(), seeded],
        boxes_ok=True,
    )
    assert summary.passed is False
    assert summary.checks_ok is False
    assert "W6-L1" in summary.statement
    assert "FAIL (in-repo SAT scope)" in summary.statement


def test_cli_check_only_exit_zero(tmp_path):
    assert w6_main(["--check-only"]) == 0
    assert w6_main(["--out", str(tmp_path)]) == 0
    report = tmp_path / "signoff_report.md"
    assert report.is_file()
    text = report.read_text(encoding="utf-8")
    assert "sinh tự động" in text
    for number in ("28", "29", "30", "31"):
        assert f"Ticket {number}" in text
    assert "PASS (in-repo SAT scope)" in text
    assert not re.search(r"(?i)\b(TODO|TBD|FIXME)\b", text)


def test_cli_check_only_writes_nothing(tmp_path):
    # NFR: ``--check-only`` không ghi file nào.
    assert w6_main(["--check-only", "--out", str(tmp_path)]) == 0
    assert list(tmp_path.iterdir()) == []
    assert not (tmp_path / "signoff_report.md").exists()


def test_cli_seeded_fail_exit_one(tmp_path, monkeypatch):
    copy = tmp_path / "sat_spec.md"
    copy.write_text(
        SAT_SPEC.read_text(encoding="utf-8") + '\nstatus: "TIMEOUT"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(w6, "TERM_PATHS", (copy,))
    assert w6_main(["--check-only"]) == 1


def test_cli_out_dir_alias(tmp_path):
    # ``--out`` và ``--out-dir`` là cùng một option (dest="out").
    assert w6_main(["--out-dir", str(tmp_path)]) == 0
    assert (tmp_path / "signoff_report.md").is_file()
    other = tmp_path / "other"
    assert w6_main(["--out", str(other)]) == 0
    assert (other / "signoff_report.md").is_file()


def test_missing_w5_deliverable_fails_audit_and_gate(tmp_path, monkeypatch):
    missing = tmp_path / "27-paper-v09-sat-sections.md"
    assert not missing.exists()
    monkeypatch.setattr(w6, "CLAIM_PATHS", (APPENDIX, missing))
    monkeypatch.setattr(w6, "CORR_PATHS", (missing,))
    monkeypatch.setattr(w6, "TABLE_PATHS", (missing,))

    findings = collect_w6_findings()
    broken = _broken(findings)
    assert {finding.check_id for finding in broken} >= {"W6-C1", "W6-L1", "W6-L2"}
    assert all("thiếu file" in finding.message for finding in broken)

    summary = evaluate_m3_gate(
        verify_code_spec_paper_consistency(),
        triage_directory(DEFAULT_RAW_DIR),
        findings,
        boxes_ok=True,
    )
    assert summary.passed is False
    assert summary.checks_ok is False
    assert m3_finding(summary).status == "fail"


def test_markdown_tables_missing_trailing_pipe(tmp_path):
    copy = tmp_path / "broken.md"
    copy.write_text(
        "| A | B |\n|---|---|\n| 1 | 2\n",
        encoding="utf-8",
    )
    broken = _broken(lint_markdown_tables([copy]))
    assert len(broken) == 1
    assert broken[0].check_id == "W6-L2"
    assert "dòng 3" in broken[0].symbol
    assert "| đóng" in broken[0].message


def test_appendix_formula_swap_a1_fails(tmp_path):
    text = APPENDIX.read_text(encoding="utf-8")
    start = text.index("## A.1")
    end = text.index("## A.2")
    swapped = text[:start] + text[start:end].replace("n²", "n(n-1)") + text[end:]
    copy = tmp_path / "appendix.md"
    copy.write_text(swapped, encoding="utf-8")

    integrity = _broken(check_appendix_integrity(appendix=copy))
    assert len(integrity) == 1
    assert integrity[0].check_id == "W6-C3"
    assert "A.1:n²" in integrity[0].message

    variables = _broken(audit_variable_conventions(appendix=copy))
    assert len(variables) == 1
    assert variables[0].check_id == "W6-T6"
    assert "A.1:n²" in variables[0].message


def test_terminology_forbidden_uniqueness_and_zero_based_labels(tmp_path):
    text = "\n".join(
        [
            "`pairwise` và `order`; nhãn `1..n`; đỉnh 0-based.",
            "assignment, uniqueness, distance, threshold.",
            "`x[v][p]`, `o[v][p]`, `n²`, `v*n+p`, `v*(n-1)+p`, `n(n-1)`.",
            "Nhãn `p ∈ 0..n-1` là sai.",
            "status `OPT`/`FEAS`.",
            "",
        ]
    )
    copy = tmp_path / "spec_variant.md"
    copy.write_text(text, encoding="utf-8")
    broken = _broken(audit_terminology([copy]))
    assert {finding.check_id for finding in broken} == {"W6-T1", "W6-T2"}
    messages = " ".join(finding.message for finding in broken)
    assert "uniqueness" in messages
    assert "p ∈ 0..n-1" in messages


def test_open_boxes_flags_unverified_x(tmp_path):
    issue = tmp_path / "01-fake.md"
    issue.write_text(
        "- [x] không có evidence\n"
        "- [x] evidence trỏ file thiếu (evidence: `tests/missing-file.md`)\n"
        "- [x] evidence handoff (evidence: `docs/handoff/sat-g1/run_g1.py`)\n"
        "- [x] evidence hợp lệ (evidence: `docs/sat_spec.md`)\n"
        "- [ ] còn mở\n",
        encoding="utf-8",
    )
    issues = open_boxes([issue])
    assert len(issues) == 4
    assert any("thiếu (evidence: path)" in line for line in issues)
    assert any("tests/missing-file.md" in line for line in issues)
    assert any("docs/handoff/" in line for line in issues)
    assert issues[-1].endswith(":5")
    assert checkboxes_ok([issue]) is False
    assert open_boxes() == []
    assert checkboxes_ok() is True


def test_m3_finding_present_in_report(tmp_path):
    summary = evaluate_m3_gate(
        verify_code_spec_paper_consistency(),
        triage_directory(DEFAULT_RAW_DIR),
        collect_w6_findings(),
        boxes_ok=True,
    )
    finding = m3_finding(summary)
    assert finding.check_id == "W6-M3"
    assert finding.status == "ok"
    assert "docs/w6-sat/signoff_report.md" in finding.file

    failing = ConsistencyFinding(
        check_id="W6-L2",
        status="fail",
        file="docs/w5-sat/26-cross-review-consistency.md",
        symbol="dòng 1",
        expected="bảng cân cột",
        actual="lệch cột",
        message="seeded",
    )
    failed_summary = evaluate_m3_gate(
        verify_code_spec_paper_consistency(),
        triage_directory(DEFAULT_RAW_DIR),
        [*collect_w6_findings(), failing],
        boxes_ok=True,
    )
    failed_finding = m3_finding(failed_summary)
    assert failed_finding.check_id == "W6-M3"
    assert failed_finding.status == "fail"
    assert "Sign-off = PASS" not in failed_finding.message

    assert w6_main(["--out", str(tmp_path)]) == 0
    text = (tmp_path / "signoff_report.md").read_text(encoding="utf-8")
    assert "W6-M3" in text
    assert "Finding tổng hợp W6-M3" in text

