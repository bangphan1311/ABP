"""Audit W6: proofread thuật ngữ, verify claim, cross-read P3 và M3 sign-off.

Chỉ đọc tài liệu frozen (``docs/sat_spec.md``, appendix, ``docs/w5-sat/24..27``,
``docs/canonical_sat_config.md``, ``docs/sat_tooling.md``) và dựng vài CNF nhỏ
(``path4``); không chạy solver, không ghi ``results/``. Finding dùng chung schema
``experiments.w5_final_analysis.ConsistencyFinding`` (BR-9).

    python -m experiments.w6_signoff
    python -m experiments.w6_signoff --check-only
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.pilot_common import REPO_ROOT, use_utf8_output
from experiments.w5_final_analysis import (
    ConsistencyFinding,
    _compact,
    _finding,
    _read,
    _repo_relative,
    verify_code_spec_paper_consistency,
)
from src.sat import order, pairwise
from src.sat.loader import read_instance
from src.sat.triage import DEFAULT_RAW_DIR, TriageReport, triage_directory

DEFAULT_W6_OUT = REPO_ROOT / "docs" / "w6-sat"
REPORT_NAME = "signoff_report.md"
M3_CHECK_ID = "W6-M3"
GENERATED_NOTE = (
    "> **Lưu ý:** File này được sinh tự động bằng "
    "`python -m experiments.w6_signoff`, không chỉnh sửa tay."
)

SAT_SPEC = REPO_ROOT / "docs" / "sat_spec.md"
APPENDIX = REPO_ROOT / "docs" / "technical_appendix_draft.md"
W5_DIR = REPO_ROOT / "docs" / "w5-sat"
CANONICAL = REPO_ROOT / "docs" / "canonical_sat_config.md"
TOOLING = REPO_ROOT / "docs" / "sat_tooling.md"
REQUIREMENTS = REPO_ROOT / "requirements.txt"
BACKEND = REPO_ROOT / "src" / "sat" / "backend.py"
PATH4 = REPO_ROOT / "benchmark" / "toy" / "path4.json"
ISSUES_DIR = REPO_ROOT / "docs" / "abp-sat-encoding" / "issues"

W5_ARTIFACTS = (
    "24-rq1-final.md",
    "25-rq2-final.md",
    "26-cross-review-consistency.md",
    "27-paper-v09-sat-sections.md",
)
TERM_PATHS = (SAT_SPEC, APPENDIX, *(W5_DIR / name for name in W5_ARTIFACTS), CANONICAL, TOOLING)
CLAIM_PATHS = (APPENDIX, *(W5_DIR / name for name in W5_ARTIFACTS))
CORR_PATHS = (*(W5_DIR / name for name in W5_ARTIFACTS), CANONICAL)
TABLE_PATHS = TERM_PATHS

STATUS_CODES = ("OPT", "FEAS", "TO", "MO", "ERR")
FORBIDDEN_STATUS_CODES = ("TIMEOUT", "SATISFIABLE", "OOM")
CLAUSE_GROUPS = ("assignment", "permutation", "distance", "threshold")
VAR_FORMULAS = ("x[v][p]", "o[v][p]", "n²", "n(n-1)", "v*n+p", "v*(n-1)+p")
SOLVER_NAMES = ("cadical195", "glucose4", "glucose42", "minisat22")
PINNED_SAT_PACKAGE = "python-sat==1.9.dev15"

EXPECTED_LABELS = (
    "A.1", "A.2", "A.3", "A.3.1", "A.4", "A.5", "A.6",
    "A.7", "A.8", "A.9", "A.10", "A.11",
)
APPENDIX_SECTIONS = ("A.1", "A.2", "A.3", "A.4", "A.5", "A.6", "A.7")
PATH4_CLAUSES = {"pairwise": (56, 74, 86), "order": (32, 50, 62)}

FORBIDDEN_QUALITATIVE = (
    "clearly better",
    "obviously faster",
    "always faster",
    "clearly faster",
    "obviously better",
)
QUALITATIVE_CLAIMS = (
    "is faster",
    "is slower",
    "is better",
    "outperforms",
    "dominates",
    "superior",
)
EVIDENCE_ANCHOR = re.compile(
    r"(results/|docs/|tests/|src/|benchmark/|\d+(?:\.\d+)?\s*(?:s|MB|clauses|giây))"
)

STRICT_CAUSAL_PHRASES = ("determines", "causes", "therefore runtime is")
WEAK_CAUSAL_PHRASES = ("quyết định runtime", "gây ra")
CORRELATION_QUALIFIERS = (
    "correlation",
    "tương quan",
    "on this subset",
    "measured",
    "đo được",
    "subset",
)
FORBIDDEN_LABEL_RANGE = re.compile(r"p\s*∈\s*\{?0\.\.n\s*[-\u2212]\s*1")
FORBIDDEN_CLAUSE_GROUP = re.compile(r"\buniqueness\b", re.I)
APPENDIX_FORMULA_SECTIONS = (
    ("A.1", ("v*n+p", "n²")),
    ("A.2", ("v*(n-1)+p", "n(n-1)")),
)

LABEL_DEFINITION = re.compile(r"\*\*(?:Lemma|Theorem|Corollary)\s+(A\.\d+(?:\.\d+)?)")
ANY_LABEL = re.compile(r"\bA\.\d+(?:\.\d+)?\b")
EVIDENCE_INLINE = re.compile(r"\(evidence: `([^`]+)`\)")

W1_EVIDENCE: dict[str, tuple[str, ...]] = {
    "01-sat-spec-decision-problem.md": (
        "docs/sat_spec.md",
        "docs/sat_spec.md",
        "src/sat/pairwise.py",
        "src/sat/solve.py",
        "docs/sat_spec.md",
        "docs/sat_spec.md",
    ),
    "02-sat-tooling-check.md": ("docs/sat_tooling.md",) * 5,
    "03-satbackend-cadical.md": (
        "src/sat/backend.py",
        "src/sat/backend.py",
        "tests/sat/test_backend.py",
        "tests/sat/test_backend.py",
        "src/sat/backend.py",
    ),
    "04-pairwise-encoding.md": (
        "src/sat/pairwise.py",
        "src/common/models.py",
        "tests/sat/test_pairwise.py",
        "tests/sat/test_pairwise.py",
        "docs/sat_spec.md",
    ),
    "05-order-encoding.md": (
        "src/sat/order.py",
        "tests/sat/test_order.py",
        "tests/sat/test_order.py",
        "docs/w2-sat/14-sat-methodology.md",
    ),
    "06-loader-toy-generator.md": (
        "src/sat/loader.py",
        "src/sat/generator.py",
        "tests/sat/test_generator.py",
        "src/sat/loader.py",
    ),
    "07-g1-prototype-check.md": (
        "docs/sat-g1/run_g1.py",
        "tests/sat/test_g1_oracle.py",
        "src/sat/backend.py",
        "docs/sat_tooling.md",
        "docs/sat-g1/results.json",
    ),
}
W6_EVIDENCE: dict[str, tuple[str, ...]] = {
    "28-technical-proofread.md": ("tests/experiments/test_w6_signoff.py",) * 3,
    "29-claim-verification-appendix.md": ("tests/experiments/test_w6_signoff.py",) * 3,
    "30-cross-read-p3-latex.md": ("tests/experiments/test_w6_signoff.py",) * 4,
    "31-m3-technical-signoff.md": (
        "tests/experiments/test_w6_signoff.py",
        "tests/experiments/test_w6_signoff.py",
        "docs/w6-sat/signoff_report.md",
    ),
}
W1_ISSUES = tuple(ISSUES_DIR / "W1" / name for name in W1_EVIDENCE)
W6_ISSUES = tuple(ISSUES_DIR / "W6" / name for name in W6_EVIDENCE)


@dataclass
class M3Summary:
    """Điều kiện M3: W5 C1–C10, triage 70/70 CODE_BUG=0, W6 audit, checkbox W1/W6."""

    w5_ok: bool
    triaged_total: int
    code_bugs: int
    checks_ok: bool
    boxes_ok: bool
    passed: bool
    statement: str


def _token_text(text: str) -> str:
    """Chuẩn hóa để so token: bỏ code tick/khoảng trắng, quy ``≥``/``≤`` về ASCII."""
    return _compact(text.replace("≥", ">=").replace("≤", "<="))


def _table_rows(text: str) -> list[tuple[int, str]]:
    """Các dòng bảng Markdown (bỏ qua khối code fence)."""
    rows: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and line.lstrip().startswith("|"):
            rows.append((number, line))
    return rows


def _cell_count(line: str) -> int:
    """Số ô của một dòng bảng: bỏ code span trong dòng, tôn trọng ``\\|``."""
    text = re.sub(r"`[^`]*`", "CODE", line.strip())
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    return len(re.split(r"(?<!\\)\|", text))


def _closed_table_row(line: str) -> bool:
    """Dòng bảng phải kết thúc bằng ``|`` chưa escape."""
    stripped = line.rstrip()
    return stripped.endswith("|") and not stripped.endswith("\\|")


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _missing_file_finding(
    check_id: str, path: Path, symbol: str
) -> ConsistencyFinding:
    """File input không tồn tại: FAIL, không được bỏ qua im lặng."""
    return _finding(
        check_id,
        path,
        symbol,
        "file phải tồn tại trong repo",
        "thiếu file",
        [f"{_repo_relative(path)}: thiếu file"],
    )


def _appendix_sections(text: str) -> dict[str, str]:
    """Cắt appendix theo heading ``## A.x`` (giá trị = thân section)."""
    matches = list(re.finditer(r"^##\s+(A\.\d+)\b.*$", text, re.M))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.setdefault(match.group(1), text[match.start() : end])
    return sections


def _formula_missing(text: str, label: str) -> list[str]:
    """Công thức phải nằm đúng section: ``v*n+p``/``n²`` ở A.1, order ở A.2."""
    sections = _appendix_sections(text)
    missing: list[str] = []
    for name, tokens in APPENDIX_FORMULA_SECTIONS:
        body = _token_text(sections.get(name, ""))
        for token in tokens:
            if token not in body:
                missing.append(f"{label}:{name}:{token}")
    return missing


def audit_terminology(paths: Sequence[Path]) -> list[ConsistencyFinding]:
    """BR-1..BR-3: token thuật ngữ, mã trạng thái, tên/version solver (W6-T1..W6-T5)."""
    files = [Path(path) for path in paths]
    texts = {path: _read(path) for path in files}
    joined = _token_text("\n".join(texts.values()))
    findings = [
        _missing_file_finding("W6-T1", path, "file audit terminology")
        for path in files
        if not path.is_file()
    ]

    missing = [token for token in ("pairwise", "order", "1..n") if token not in joined]
    if not any(token in joined for token in ("0-based", "0..n-1")):
        missing.append("0-based/0..n-1")
    for path in files:
        for match in FORBIDDEN_LABEL_RANGE.finditer(texts[path]):
            missing.append(
                f"{_repo_relative(path)}:{_line_of(texts[path], match.start())}:"
                "p ∈ 0..n-1 (nhãn phải là 1..n)"
            )
    findings.append(
        _finding(
            "W6-T1",
            files[0],
            "tên encoding + miền nhãn/đỉnh",
            "pairwise, order, nhãn 1..n, đỉnh 0..n-1",
            "đủ" if not missing else "thiếu",
            missing,
        )
    )

    missing = [token for token in CLAUSE_GROUPS if token not in joined]
    for path in files:
        for match in FORBIDDEN_CLAUSE_GROUP.finditer(texts[path]):
            missing.append(
                f"{_repo_relative(path)}:{_line_of(texts[path], match.start())}:"
                "uniqueness (phải là 'permutation')"
            )
    findings.append(
        _finding(
            "W6-T2",
            files[0],
            "nhóm clause",
            "assignment, permutation, distance, threshold (không 'uniqueness')",
            "đủ" if not missing else "thiếu",
            missing,
        )
    )

    missing = [token for token in VAR_FORMULAS if token not in joined]
    findings.append(
        _finding(
            "W6-T3",
            files[0],
            "công thức biến",
            "x[v][p] (v*n+p, n²), o[v][p] (v*(n-1)+p, n(n-1))",
            "đủ" if not missing else "thiếu",
            missing,
        )
    )

    raw_joined = "\n".join(texts.values())
    missing = [
        code
        for code in ("OPT", "FEAS")
        if not re.search(rf"\b{code}\b", raw_joined)
    ]
    for path in files:
        for token in FORBIDDEN_STATUS_CODES:
            if re.search(rf"\b{token}\b", texts[path]):
                missing.append(f"{_repo_relative(path)}:{token}")
    findings.append(
        _finding(
            "W6-T4",
            files[0],
            "mã trạng thái",
            "chỉ OPT/FEAS/TO/MO/ERR, không SATISFIABLE/TIMEOUT/OOM",
            "đủ" if not missing else "thiếu",
            missing,
        )
    )

    missing: list[str] = []
    if PINNED_SAT_PACKAGE not in re.sub(r"\s+", "", _read(REQUIREMENTS)):
        missing.append(f"requirements.txt:{PINNED_SAT_PACKAGE}")
    if "1.9.dev15" not in _token_text(_read(TOOLING)):
        missing.append("sat_tooling.md:1.9.dev15")
    canonical_text = _token_text(_read(CANONICAL))
    missing.extend(
        f"canonical_sat_config.md:{name}"
        for name in SOLVER_NAMES
        if name not in canonical_text
    )
    if "PYSAT_KISSAT_FAMILIES" not in _read(BACKEND):
        missing.append("backend.py:PYSAT_KISSAT_FAMILIES")
    for path in files:
        # ``sat_tooling.md`` ghi bằng chứng chặn Kissat, không phải bảng ứng viên.
        if path.name == TOOLING.name:
            continue
        for number, row in _table_rows(texts[path]):
            if "kissat" in row.lower():
                missing.append(f"{_repo_relative(path)}:{number}:kissat")
    findings.append(
        _finding(
            "W6-T5",
            CANONICAL,
            "tên/version solver + Kissat bị chặn",
            "python-sat==1.9.dev15; cadical195/glucose4/glucose42/minisat22; Kissat không là ứng viên",
            "đủ" if not missing else "thiếu",
            missing,
        )
    )
    return findings


def audit_variable_conventions(
    *, spec: Path = SAT_SPEC, appendix: Path = APPENDIX
) -> list[ConsistencyFinding]:
    """W6-T6 (FR-2): công thức biến tài liệu phải khớp ``build_cnf`` live."""
    instance = read_instance(PATH4)
    n = instance.n
    pairwise_cnf = pairwise.build_cnf(instance, 1)
    order_cnf = order.build_cnf(instance, 1)
    live_ok = (
        all(
            pairwise_cnf.var_of[(v, p)] == v * n + p
            for v in range(n)
            for p in range(1, n + 1)
        )
        and pairwise_cnf.n_vars == n * n
        and all(
            order_cnf.var_of[(v, p)] == v * (n - 1) + p
            for v in range(n)
            for p in range(1, n)
        )
        and order_cnf.n_vars == n * (n - 1)
    )
    missing: list[str] = [] if live_ok else ["build_cnf var_of/n_vars lệch"]
    findings: list[ConsistencyFinding] = []
    for path in (spec, appendix):
        rel = _repo_relative(path)
        if not path.is_file():
            findings.append(_missing_file_finding("W6-T6", path, "file audit biến"))
            missing.append(f"{rel}: thiếu file")
            continue
        missing.extend(
            f"{rel}:{token}"
            for token in VAR_FORMULAS
            if token not in _token_text(_read(path))
        )
    if appendix.is_file():
        missing.extend(_formula_missing(_read(appendix), _repo_relative(appendix)))
    return [
        *findings,
        _finding(
            "W6-T6",
            spec,
            "var_of/n_vars live ↔ công thức tài liệu",
            "A.1: v*n+p (n²), A.2: v*(n-1)+p (n(n-1))",
            f"pairwise n_vars={pairwise_cnf.n_vars}, order n_vars={order_cnf.n_vars}",
            missing,
        ),
    ]


def audit_threshold_semantics(
    paths: Sequence[Path] | None = None,
) -> list[ConsistencyFinding]:
    """W6-T7 (FR-3): ``K >= n`` UNSAT trước CNF, ``K = 1`` luôn SAT (BR-4)."""
    files = [Path(path) for path in (paths if paths is not None else (SAT_SPEC, APPENDIX))]
    missing: list[str] = []
    live_ok = all(
        pairwise.trivial_unsat(n, k) == (k >= n)
        for n in range(2, 7)
        for k in range(1, 8)
    )
    if not live_ok:
        missing.append("trivial_unsat(n,k) != (k >= n)")
    instance = read_instance(PATH4)
    k1_ok = (
        pairwise.trivial_unsat(instance.n, 1) is False
        and not pairwise.build_cnf(instance, 1).stats["distance"]
        and not order.build_cnf(instance, 1).stats["distance"]
    )
    if not k1_ok:
        missing.append("K=1 không rỗng nhóm distance")
    for path in files:
        text = _token_text(_read(path))
        if "k>=n" not in text:
            missing.append(f"{_repo_relative(path)}:K >= n")
        if "k>n" in text:
            missing.append(f"{_repo_relative(path)}:K > n (sai)")
    return [
        _finding(
            "W6-T7",
            files[0],
            "ngữ nghĩa ngưỡng",
            "trivial_unsat(n,k)==(k>=n), K=1 luôn SAT, không tài liệu nào nói K > n",
            "đủ" if not missing else "thiếu",
            missing,
        )
    ]


def verify_claims(paths: Sequence[Path]) -> list[ConsistencyFinding]:
    """W6-C1 (FR-4 / BR-5): claim định tính phải có bằng chứng đi kèm."""
    findings: list[ConsistencyFinding] = []
    for path in paths:
        path = Path(path)
        if not path.is_file():
            findings.append(_missing_file_finding("W6-C1", path, "file claim scan"))
            continue
        lines = _read(path).splitlines()
        for index, line in enumerate(lines):
            low = line.lower()
            phrase = next((item for item in FORBIDDEN_QUALITATIVE if item in low), None)
            if phrase:
                findings.append(
                    _finding(
                        "W6-C1",
                        path,
                        f"dòng {index + 1}",
                        "claim định tính phải kèm bằng chứng (file + số đo)",
                        phrase,
                        [phrase],
                    )
                )
                continue
            claim = next((item for item in QUALITATIVE_CLAIMS if item in low), None)
            if claim is None:
                continue
            window = line + " " + (lines[index + 1] if index + 1 < len(lines) else "")
            if EVIDENCE_ANCHOR.search(window):
                continue
            findings.append(
                _finding(
                    "W6-C1",
                    path,
                    f"dòng {index + 1}",
                    "claim định tính phải có anchor (results/... hoặc số đo)",
                    claim,
                    [claim],
                )
            )
    return findings


def check_lemma_numbering(path: Path = APPENDIX) -> list[ConsistencyFinding]:
    """W6-C2 (FR-5 / BR-6): dãy nhãn ``A.1..A.8, A.3.1, A.9..A.11``, không trùng/thiếu."""
    path = Path(path)
    text = _read(path)
    defined = LABEL_DEFINITION.findall(text)
    defined_set = set(defined)
    missing: list[str] = []
    if tuple(defined) != EXPECTED_LABELS:
        missing.append(f"dãy nhãn: {'/'.join(defined) or 'thiếu'}")
    duplicates = [label for label in dict.fromkeys(defined) if defined.count(label) > 1]
    missing.extend(f"trùng:{label}" for label in duplicates)
    missing.extend(
        f"tham chiếu không có định nghĩa:{label}"
        for label in dict.fromkeys(ANY_LABEL.findall(text))
        if label not in defined_set
    )
    return [
        _finding(
            "W6-C2",
            path,
            "dãy nhãn Lemma/Corollary/Theorem",
            "A.1..A.8, A.3.1, A.9..A.11 không trùng/thiếu",
            f"{len(defined)} nhãn",
            missing,
        )
    ]


def check_appendix_integrity(
    *, appendix: Path = APPENDIX, spec: Path = SAT_SPEC
) -> list[ConsistencyFinding]:
    """W6-C3 (FR-6 / BR-7): section A.1–A.7 đúng thứ tự, số liệu khớp ``build_cnf``."""
    appendix, spec = Path(appendix), Path(spec)
    appendix_text = _read(appendix)
    headings = re.findall(r"^##\s+(A\.\d+)\b", appendix_text, re.M)
    missing: list[str] = []
    for section in APPENDIX_SECTIONS:
        if section not in headings:
            missing.append(f"missing-section:{section}")
    present = [section for section in headings if section in APPENDIX_SECTIONS]
    if present != [section for section in APPENDIX_SECTIONS if section in present]:
        missing.append(f"thứ tự section: {'/'.join(present)}")

    instance = read_instance(PATH4)
    live = {
        name: tuple(len(builder(instance, k).clauses) for k in (1, 2, 3))
        for name, builder in (("pairwise", pairwise.build_cnf), ("order", order.build_cnf))
    }
    if live != PATH4_CLAUSES:
        missing.append(f"live build_cnf: {live}")

    spec_text = _token_text(_read(spec))
    missing.extend(
        f"{_repo_relative(spec)}:{token}"
        for token in ("56", "74", "86", "32", "50", "62")
        if token not in spec_text
    )
    missing.extend(_formula_missing(appendix_text, _repo_relative(appendix)))
    if not appendix.is_file():
        missing.append(f"{_repo_relative(appendix)}: thiếu file")
    return [
        _finding(
            "W6-C3",
            appendix,
            "section A.1–A.7 + số liệu path4",
            "A.1..A.7 đúng thứ tự; pairwise 56/74/86, order 32/50/62",
            f"live={live}",
            missing,
        )
    ]


def audit_correlation_hygiene(paths: Sequence[Path]) -> list[ConsistencyFinding]:
    """W6-L1 (FR-7 / BR-8): tương quan không được viết thành nhân quả."""
    findings: list[ConsistencyFinding] = []
    for path in paths:
        path = Path(path)
        if not path.is_file():
            findings.append(_missing_file_finding("W6-L1", path, "file correlation scan"))
            continue
        for number, line in enumerate(_read(path).splitlines(), 1):
            low = line.lower()
            strict = next((item for item in STRICT_CAUSAL_PHRASES if item in low), None)
            if strict:
                # Khẳng định nhân quả trực tiếp: qualifier trên cùng dòng không cứu.
                findings.append(
                    _finding(
                        "W6-L1",
                        path,
                        f"dòng {number}",
                        "không khẳng định nhân quả; chỉ được nêu tương quan/đo đạc",
                        strict,
                        [f"dòng {number}: {strict}"],
                    )
                )
                continue
            weak = next((item for item in WEAK_CAUSAL_PHRASES if item in low), None)
            if weak is None:
                continue
            if any(item in low for item in CORRELATION_QUALIFIERS):
                continue
            findings.append(
                _finding(
                    "W6-L1",
                    path,
                    f"dòng {number}",
                    "quan hệ phải nêu correlation/measured, không nhân quả",
                    weak,
                    [f"dòng {number}: {weak}"],
                )
            )
    return findings


def lint_markdown_tables(paths: Sequence[Path]) -> list[ConsistencyFinding]:
    """W6-L2 (FR-8): bảng Markdown đủ cột, ``|`` cân, code span cân."""
    findings: list[ConsistencyFinding] = []
    for path in paths:
        path = Path(path)
        if not path.is_file():
            findings.append(_missing_file_finding("W6-L2", path, "file markdown scan"))
            continue
        in_fence = False
        expected_cells: int | None = None
        for number, line in enumerate(_read(path).splitlines(), 1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                expected_cells = None
                continue
            if in_fence:
                continue
            if line.count("`") % 2:
                findings.append(
                    _finding(
                        "W6-L2",
                        path,
                        f"dòng {number}",
                        "code span phải cân backtick",
                        "số backtick lẻ",
                        [f"dòng {number}: backtick lẻ"],
                    )
                )
                continue
            if not line.lstrip().startswith("|"):
                expected_cells = None
                continue
            if not _closed_table_row(line):
                findings.append(
                    _finding(
                        "W6-L2",
                        path,
                        f"dòng {number}",
                        "dòng bảng phải kết thúc bằng | chưa escape",
                        "thiếu | đóng",
                        [f"dòng {number}: thiếu | đóng"],
                    )
                )
                continue
            count = _cell_count(line)
            if expected_cells is None:
                expected_cells = count
            elif count != expected_cells:
                findings.append(
                    _finding(
                        "W6-L2",
                        path,
                        f"dòng {number}",
                        f"{expected_cells} cột",
                        f"{count} cột",
                        [f"dòng {number}: {count} cột != {expected_cells}"],
                    )
                )
    return findings


def record_deferred_items() -> list[dict[str, str]]:
    """FR-9: các hạng mục deferred/external, ghi rõ owner, không blocking."""
    return [
        {"item": "P3 LaTeX sections", "owner": "P3", "status": "deferred"},
        {"item": "final English copy-edit", "owner": "P3", "status": "deferred"},
        {"item": "paper/LaTeX prose", "owner": "P2+P1", "status": "deferred"},
        {"item": "P3 official 24-instance runs.csv", "owner": "P3", "status": "deferred"},
        {"item": "P3 manuscript merge", "owner": "P3", "status": "deferred"},
    ]


def _emit_checkbox_edits(
    issue_files: Sequence[Path], evidence: dict[str, tuple[str, ...]]
) -> list[dict[str, str]]:
    edits: list[dict[str, str]] = []
    for path in issue_files:
        path = Path(path)
        if not path.is_file():
            continue
        tokens = evidence.get(path.name, ())
        lines = _read(path).splitlines()
        out: list[str] = []
        cursor = 0
        for line in lines:
            if not line.lstrip().startswith("- ["):
                out.append(line)
                continue
            token = tokens[cursor] if cursor < len(tokens) else ""
            cursor += 1
            if not token or not (REPO_ROOT / token).is_file():
                out.append(line)
                continue
            if "- [ ]" in line:
                line = line.replace("- [ ]", "- [x]", 1)
            if not EVIDENCE_INLINE.search(line):
                line = f"{line} (evidence: `{token}`)"
            out.append(line)
        edits.append(
            {
                "file": _repo_relative(path),
                "merged_text": "\n".join(out).rstrip() + "\n",
            }
        )
    return edits


def emit_w1_checkbox_edits(issue_files: Sequence[Path]) -> list[dict[str, str]]:
    """FR-12: text ``[x]`` + ``(evidence: path)`` cho W1 01..07 (không ghi file)."""
    return _emit_checkbox_edits(issue_files, W1_EVIDENCE)


def emit_w6_checkbox_edits(issue_files: Sequence[Path]) -> list[dict[str, str]]:
    """FR-12: text ``[x]`` + ``(evidence: path)`` cho W6 28..31 (không ghi file)."""
    return _emit_checkbox_edits(issue_files, W6_EVIDENCE)


def open_boxes(issue_files: Sequence[Path] | None = None) -> list[str]:
    """Ô chưa đạt: ``[ ]``, ``[x]`` thiếu/không hợp lệ evidence, hoặc file thiếu."""
    files = (
        list(W1_ISSUES) + list(W6_ISSUES)
        if issue_files is None
        else [Path(path) for path in issue_files]
    )
    issues: list[str] = []
    for path in files:
        if not path.is_file():
            issues.append(f"{_repo_relative(path)}: thiếu file")
            continue
        for number, line in enumerate(_read(path).splitlines(), 1):
            stripped = line.lstrip()
            location = f"{_repo_relative(path)}:{number}"
            if stripped.startswith("- [ ]"):
                issues.append(location)
                continue
            if not stripped.startswith("- [x]"):
                continue
            evidence = EVIDENCE_INLINE.findall(line)
            if not evidence:
                issues.append(f"{location}: thiếu (evidence: path)")
                continue
            for token in evidence:
                if token.startswith("docs/handoff/") or not (REPO_ROOT / token).is_file():
                    issues.append(f"{location}: evidence không hợp lệ ({token})")
    return issues


def checkboxes_ok(issue_files: Sequence[Path] | None = None) -> bool:
    return not open_boxes(issue_files)


def evaluate_m3_gate(
    w5_findings: Sequence[ConsistencyFinding],
    triage_reports: Sequence[TriageReport],
    w6_findings: Sequence[ConsistencyFinding],
    boxes_ok: bool,
) -> M3Summary:
    """FR-10: M3 PASS (in-repo SAT scope) chỉ khi mọi thành phần đều đạt."""
    w5_ok = bool(w5_findings) and all(item.status == "ok" for item in w5_findings)
    code_bugs = sum(report.category == "CODE_BUG" for report in triage_reports)
    triaged_total = len(triage_reports)
    checks_ok = all(item.status == "ok" for item in w6_findings)
    passed = w5_ok and triaged_total >= 70 and code_bugs == 0 and checks_ok and boxes_ok

    failing = ""
    if not w5_ok:
        failing = next(
            (f"W5 {item.check_id}" for item in w5_findings if item.status != "ok"),
            "W5 C1–C10 thiếu finding",
        )
    elif triaged_total < 70:
        failing = f"triage {triaged_total}/70 run"
    elif code_bugs:
        failing = f"triage CODE_BUG={code_bugs}"
    elif not checks_ok:
        failing = next(
            item.check_id for item in w6_findings if item.status != "ok"
        )
    elif not boxes_ok:
        failing = "checkbox W1/W6"
    head = (
        "P2 SAT Technical Sign-off = PASS (in-repo SAT scope)"
        if passed
        else f"P2 SAT Technical Sign-off = FAIL (in-repo SAT scope): {failing}"
    )
    deferred = "; ".join(
        f"{entry['item']} ({entry['owner']}, deferred)"
        for entry in record_deferred_items()
    )
    statement = (
        f"{head}. Triage {triaged_total}/70 run frozen (CODE_BUG={code_bugs}); "
        f"consistency W5 C1–C10 {'PASS' if w5_ok else 'FAIL'} "
        f"({len(w5_findings)} finding); audit W6 {'PASS' if checks_ok else 'FAIL'} "
        f"({len(w6_findings)} finding); checkbox W1/W6 "
        f"{'PASS' if boxes_ok else 'FAIL'}. "
        f"Deferred/external (không blocking): {deferred}."
    )
    return M3Summary(
        w5_ok=w5_ok,
        triaged_total=triaged_total,
        code_bugs=code_bugs,
        checks_ok=checks_ok,
        boxes_ok=boxes_ok,
        passed=passed,
        statement=statement,
    )


def m3_finding(summary: M3Summary) -> ConsistencyFinding:
    """Finding tổng hợp ``W6-M3`` (Check ID Catalog): quyết định M3 + deferred list."""
    return _finding(
        M3_CHECK_ID,
        DEFAULT_W6_OUT / REPORT_NAME,
        "M3 aggregate (W5 C1–C10 + triage + W6 audit + checkbox)",
        "PASS (in-repo SAT scope) + danh sách deferred/external",
        "PASS" if summary.passed else "FAIL",
        [] if summary.passed else [summary.statement],
    )


def collect_w6_findings() -> list[ConsistencyFinding]:
    """Chạy toàn bộ FR-1..FR-8; check không có vi phạm vẫn phát một finding ``ok``."""
    claims = verify_claims(CLAIM_PATHS)
    correlations = audit_correlation_hygiene(CORR_PATHS)
    tables = lint_markdown_tables(TABLE_PATHS)
    return [
        *audit_terminology(TERM_PATHS),
        *audit_variable_conventions(),
        *audit_threshold_semantics(),
        *(
            claims
            or [
                _finding(
                    "W6-C1",
                    APPENDIX,
                    "claim verification",
                    "không claim định tính thiếu bằng chứng",
                    "0 vi phạm",
                    [],
                )
            ]
        ),
        *check_lemma_numbering(),
        *check_appendix_integrity(),
        *(
            correlations
            or [
                _finding(
                    "W6-L1",
                    CANONICAL,
                    "correlation hygiene",
                    "không viết tương quan thành nhân quả",
                    "0 vi phạm",
                    [],
                )
            ]
        ),
        *(
            tables
            or [
                _finding(
                    "W6-L2",
                    CANONICAL,
                    "markdown table lint",
                    "bảng đủ cột, code span cân backtick",
                    "0 vi phạm",
                    [],
                )
            ]
        ),
    ]


def _finding_table(findings: Sequence[ConsistencyFinding]) -> list[str]:
    lines = [
        "| Check | Status | File | Symbol | Expected | Actual | Message |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in findings:
        message = item.message.replace("|", "\\|") or "—"
        lines.append(
            f"| `{item.check_id}` | **{item.status.upper()}** | `{item.file}` | "
            f"`{item.symbol}` | {item.expected} | {item.actual} | {message} |"
        )
    return lines


def _verdict(findings: Sequence[ConsistencyFinding]) -> str:
    return "PASS" if all(item.status == "ok" for item in findings) else "FAIL"


def _status_by_check(
    findings: Sequence[ConsistencyFinding],
) -> list[tuple[str, str]]:
    order_: list[str] = []
    status: dict[str, str] = {}
    for item in findings:
        if item.check_id not in status:
            order_.append(item.check_id)
            status[item.check_id] = "ok"
        if item.status != "ok":
            status[item.check_id] = "fail"
    return [(check_id, status[check_id]) for check_id in order_]


def render_signoff_markdown(
    w5_findings: Sequence[ConsistencyFinding],
    triage_reports: Sequence[TriageReport],
    w6_findings: Sequence[ConsistencyFinding],
    m3: M3Summary,
    *,
    boxes_issues: Sequence[str] | None = None,
) -> str:
    """Sinh ``docs/w6-sat/signoff_report.md`` (banner + section 28/29/30/31)."""
    boxes_issues = list(boxes_issues or [])
    by_id = {check_id: status for check_id, status in _status_by_check(w6_findings)}
    term = [item for item in w6_findings if item.check_id in by_id and item.check_id.startswith("W6-T")]
    claims = [item for item in w6_findings if item.check_id == "W6-C1"]
    lemma = [item for item in w6_findings if item.check_id == "W6-C2"]
    appendix = [item for item in w6_findings if item.check_id == "W6-C3"]
    lint = [item for item in w6_findings if item.check_id.startswith("W6-L")]
    m3_rows = [item for item in w6_findings if item.check_id == M3_CHECK_ID]
    deferred = record_deferred_items()

    lines = [
        GENERATED_NOTE,
        "> Nguồn: `docs/sat_spec.md`, `docs/technical_appendix_draft.md`, "
        "`docs/w5-sat/24..27`, `docs/canonical_sat_config.md`, "
        "`docs/sat_tooling.md`, `requirements.txt`, `src/sat/*`, "
        "`results/raw/*.json` (chỉ đọc).",
        "> Phạm vi: in-repo SAT scope. Prose paper/LaTeX, P3 `runs.csv`, "
        "manuscript merge là deferred/external (mục 5).",
        "",
        "# W6 — P2 SAT technical sign-off (in-repo scope)",
        "",
        "## 1. Ticket 28 — Proofread thuật ngữ & ký hiệu SAT",
        "",
        f"Ticket 28 kết luận: **{_verdict(term)}** "
        f"trên {len(term)} check terminology/notation (W6-T1..W6-T7).",
        "",
        *_finding_table(term),
        "",
        "## 2. Ticket 29 — Claim verification + appendix audit",
        "",
        f"Ticket 29 kết luận: **{_verdict([*claims, *lemma, *appendix])}** "
        "(W6-C1 claim, W6-C2 lemma numbering, W6-C3 appendix integrity).",
        "",
        *_finding_table(claims + lemma + appendix),
        "",
        "## 3. Ticket 30 — Cross-read P3 + định dạng",
        "",
        f"Ticket 30 kết luận: **{_verdict(lint)}** "
        "(W6-L1 correlation≠causation, W6-L2 Markdown table/format). "
        "Phần chữ nghĩa P3 (LaTeX, English copy-edit, hình/bảng/reference) "
        "deferred — xem mục 5.",
        "",
        *_finding_table(lint),
        "",
        "## 4. Ticket 31 — M3 technical sign-off",
        "",
        f"- Consistency W5 C1–C10: **{'PASS' if m3.w5_ok else 'FAIL'}** "
        f"({len(w5_findings)} finding; nguồn `experiments/w5_final_analysis.py`, "
        "chi tiết `docs/w5-sat/26-cross-review-consistency.md` §1).",
        f"- Frozen triage: `{m3.triaged_total}` run, `CODE_BUG = {m3.code_bugs}` "
        "(`src/sat/triage.py`, `results/raw/*.json`).",
        f"- Audit W6 FR-1..FR-8: **{'PASS' if m3.checks_ok else 'FAIL'}** "
        f"({len([item for item in w6_findings if item.check_id != M3_CHECK_ID])} "
        "finding, bảng BR-9 ở mục 6).",
        f"- Checkbox W1 01–07 + W6 28–31: **{'PASS' if m3.boxes_ok else 'FAIL'}**"
        + (f" — ô còn mở: {', '.join(boxes_issues)}." if boxes_issues else "."),
        f"- **Statement:** {m3.statement}",
        "",
        "### Finding tổng hợp W6-M3",
        "",
        *_finding_table(m3_rows),
        "",
        "## 5. Deferred / external gates (không blocking)",
        "",
        "| Hạng mục | Owner | Trạng thái |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| {entry['item']} | {entry['owner']} | {entry['status']} |"
        for entry in deferred
    )
    lines.extend(
        [
            "",
            "### Trạng thái đã biết (pre-existing, không phải W6 FAIL)",
            "",
            "- `search_mode` stale-warning (`IGNORED_CONFIG_FIELDS` cảnh báo cho "
            "mode duy nhất đã cài đặt): ghi nhận tại "
            "`docs/canonical_sat_config.md` §Fixed axes, W2 resolve; W6 không mở lại.",
            "- Hàng CNF trùng `order/seqcounter` ≡ `order/pairwise`: kiểm tra nhất "
            "quán RQ1 (BR-3 W5), không phải lỗi dữ liệu, không bị W6-L2 flag.",
            "- Bằng chứng chặn Kissat nằm ở `docs/sat_tooling.md` mục Kissat; "
            "từ khoá `kissat` trong bảng incremental ở đó là evidence, không phải "
            "ứng viên.",
            "",
            "## 6. Findings W6 (schema BR-9)",
            "",
            *_finding_table(w6_findings),
            "",
            "## 7. Provenance",
            "",
            "- Module `experiments/w6_signoff.py` chỉ đọc text + dựng CNF `path4`; "
            "không chạy solver, không ghi `results/`.",
            "- Không import `src.exact.*` (tránh Ortools/Gurobi/CPLEX).",
            f"- Test: `tests/experiments/test_w6_signoff.py`; "
            f"checkbox W1/W6 do `emit_w1_checkbox_edits` / `emit_w6_checkbox_edits` sinh text.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        "--out-dir",
        dest="out",
        type=Path,
        default=DEFAULT_W6_OUT,
        help="Thư mục ghi signoff_report.md (mặc định docs/w6-sat).",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Chỉ tính check + exit code, không ghi signoff_report.md.",
    )
    args = parser.parse_args(argv)

    use_utf8_output()

    w5_findings = verify_code_spec_paper_consistency()
    triage_reports = triage_directory(DEFAULT_RAW_DIR)
    w6_findings = collect_w6_findings()
    boxes_issues = open_boxes()
    m3 = evaluate_m3_gate(w5_findings, triage_reports, w6_findings, not boxes_issues)
    report_findings = [*w6_findings, m3_finding(m3)]

    for check_id, status in _status_by_check(report_findings):
        print(f"{status.upper():4} {check_id}")
    for item in report_findings:
        if item.status != "ok":
            print(f"FAIL {item.check_id} :: {item.message}")
    for issue in boxes_issues:
        print(f"FAIL checkbox {issue}")

    if not args.check_only:
        args.out.mkdir(parents=True, exist_ok=True)
        report = args.out / REPORT_NAME
        report.write_text(
            render_signoff_markdown(
                w5_findings,
                triage_reports,
                report_findings,
                m3,
                boxes_issues=boxes_issues,
            ),
            encoding="utf-8",
        )
        print(f"Đã ghi {REPORT_NAME}: {report}")

    print(m3.statement)
    print("PASS" if m3.passed else "FAIL")
    return 0 if m3.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
