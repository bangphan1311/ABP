"""Test bộ sinh W5: projection, nguồn dữ liệu, sensitivity, trajectory, consistency, G4."""

from __future__ import annotations

import csv
import json
import re

import pytest

from experiments.analyze_rq1_rq2 import normalize_row
from experiments.w5_final_analysis import (
    DEFAULT_W5_OUT,
    GraphMeta,
    cross_size_runtime_inversion,
    evaluate_g4_gate,
    extract_feas_probe_trajectories,
    find_larger_cnf_faster_solve_cases,
    load_graph_metadata,
    load_sources,
    main as w5_main,
    project_cnf_growth,
    render_w5_markdown,
    solver_sensitivity_table,
    verify_code_spec_paper_consistency,
)
from experiments.pilot_common import REPO_ROOT
from src.sat import order, pairwise
from src.sat.loader import read_instance
from src.sat.solve import canonical_sat_config

PATH4 = REPO_ROOT / "benchmark" / "toy" / "path4.json"
VALIDATION = REPO_ROOT / "benchmark" / "validation"
LARGE = REPO_ROOT / "benchmark" / "large"


def _row(**overrides) -> dict:
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


def test_project_growth_matches_build_cnf_path4():
    instance = read_instance(PATH4)
    for abp, builder in (("pairwise", pairwise.build_cnf), ("order", order.build_cnf)):
        for k in (1, 2, 3):
            cnf = builder(instance, k)
            projected = project_cnf_growth(
                4, 3, abp_encoding=abp, amo_encoding="pairwise", k=k
            )
            assert projected["clauses"] == len(cnf.clauses)
            assert projected["variables"] == cnf.n_vars


def test_project_growth_known_anchors():
    pairwise_projection = project_cnf_growth(
        50, 100, abp_encoding="pairwise", amo_encoding="pairwise", k=17
    )
    order_projection = project_cnf_growth(
        50, 100, abp_encoding="order", amo_encoding="pairwise", k=17
    )
    assert pairwise_projection["clauses"] == 255400
    assert pairwise_projection["variables"] == 2500
    assert order_projection["clauses"] == 196450
    assert order_projection["variables"] == 2450
    # Mặc định là worst case K = n - 1.
    worst_case = project_cnf_growth(
        50, 100, abp_encoding="pairwise", amo_encoding="pairwise"
    )
    assert worst_case["k"] == 49
    assert worst_case["clauses"] > pairwise_projection["clauses"]


def test_project_exceeds_cap_labeled():
    previous = 0
    for n in (118, 420, 715):
        m = n * (n - 1) // 8
        pairwise_projection = project_cnf_growth(
            n, m, abp_encoding="pairwise", amo_encoding="pairwise"
        )
        order_projection = project_cnf_growth(
            n, m, abp_encoding="order", amo_encoding="pairwise"
        )
        assert pairwise_projection["exceeds_cap"] is True
        assert pairwise_projection["memory_est_mb"] > previous
        previous = pairwise_projection["memory_est_mb"]
        assert order_projection["memory_est_mb"] is None
        assert order_projection["exceeds_cap"] is False


def test_project_growth_rejects_bad_input():
    with pytest.raises(ValueError):
        project_cnf_growth(1, 1, abp_encoding="pairwise", amo_encoding="pairwise")
    with pytest.raises(ValueError):
        project_cnf_growth(4, 0, abp_encoding="pairwise", amo_encoding="pairwise")
    with pytest.raises(ValueError):
        project_cnf_growth(4, 3, abp_encoding="staircase", amo_encoding="pairwise")
    with pytest.raises(ValueError):
        project_cnf_growth(4, 3, abp_encoding="pairwise", amo_encoding="mystery")
    with pytest.raises(ValueError):
        project_cnf_growth(
            4, 3, abp_encoding="pairwise", amo_encoding="pairwise", k=4
        )


def _write_csv(path, rows):
    fields = rows[0].keys() if rows else ("run_id",)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_load_sources_prefers_runs_csv(tmp_path):
    headers = {
        "run_id": "r1",
        "instance": "i1",
        "abp_encoding": "order",
        "amo_encoding": "pairwise",
        "solver": "cadical195",
        "status": "OPT",
        "lb": 1,
        "ub": 1,
        "t_encode": 0.1,
        "t_solve": 0.1,
        "t_total": 0.2,
        "variables": 12,
        "clauses": 62,
        "peak_memory": 20.0,
        "time_limit": 60.0,
    }
    runs = tmp_path / "runs.csv"
    rq1 = tmp_path / "rq1.csv"
    rq2 = tmp_path / "rq2.csv"
    _write_csv(runs, [headers])
    _write_csv(rq1, [dict(headers, run_id="rq1")])
    _write_csv(rq2, [dict(headers, run_id="rq2")])

    rq1_rows, rq2_rows, note = load_sources(runs, rq1, rq2)
    assert "runs.csv" in note
    assert [row["run_id"] for row in rq1_rows] == ["r1"]
    assert [row["run_id"] for row in rq2_rows] == ["r1"]

    rq1_rows, rq2_rows, note = load_sources(tmp_path / "missing_runs.csv", rq1, rq2)
    assert "rq1.csv" in note and "rq2.csv" in note
    assert [row["run_id"] for row in rq1_rows] == ["rq1"]
    assert [row["run_id"] for row in rq2_rows] == ["rq2"]


def test_graph_metadata_density_ub():
    meta = load_graph_metadata([VALIDATION, LARGE])
    instance = read_instance(LARGE / "randconn40-seed20261026.json")
    randconn40 = meta["randconn40-seed20261026"]
    assert randconn40.m == len(instance.edges)
    assert randconn40.density == 2 * randconn40.m / (40 * 39)
    assert randconn40.UB == 40 - randconn40.max_degree

    with pytest.raises(ValueError):
        load_graph_metadata([VALIDATION / "missing-dir"])


def test_find_larger_cnf_faster_and_inversion():
    rows = [
        _row(
            instance="i1",
            abp_encoding="order",
            run_id="i1__sat__order__pairwise__cadical195__multi__sym0__ws0__s0",
            clauses=200,
            t_total=1.0,
        ),
        _row(
            instance="i1",
            abp_encoding="pairwise",
            run_id="i1__sat__pairwise__pairwise__cadical195__multi__sym0__ws0__s0",
            clauses=100,
            t_total=2.0,
        ),
    ]
    cases = find_larger_cnf_faster_solve_cases(rows)
    assert len(cases) == 1
    assert cases[0]["larger_cfg"] == "order/pairwise"
    assert cases[0]["larger_clauses"] > cases[0]["smaller_clauses"]
    assert cases[0]["larger_time"] < cases[0]["smaller_time"]

    inversion_rows = [
        _row(
            instance="randconn50-seed20261026",
            solver="s1",
            run_id="randconn50-seed20261026__sat__order__pairwise__s1__multi__sym0__ws0__s0",
            t_total=1.0,
        ),
        _row(
            instance="randconn40-seed20261026",
            solver="s1",
            run_id="randconn40-seed20261026__sat__order__pairwise__s1__multi__sym0__ws0__s0",
            t_total=3.0,
        ),
        _row(
            instance="randconn50-seed20261026",
            solver="s2",
            run_id="randconn50-seed20261026__sat__order__pairwise__s2__multi__sym0__ws0__s0",
            t_total=5.0,
        ),
        _row(
            instance="randconn40-seed20261026",
            solver="s2",
            run_id="randconn40-seed20261026__sat__order__pairwise__s2__multi__sym0__ws0__s0",
            t_total=2.0,
        ),
        _row(
            instance="randconn50-seed20261026",
            solver="s3",
            run_id="randconn50-seed20261026__sat__order__pairwise__s3__multi__sym0__ws0__s0",
            t_total=0.0,
        ),
        _row(
            instance="randconn40-seed20261026",
            solver="s3",
            run_id="randconn40-seed20261026__sat__order__pairwise__s3__multi__sym0__ws0__s0",
            t_total=2.0,
        ),
    ]
    inversions = cross_size_runtime_inversion(inversion_rows)
    assert [item["solver"] for item in inversions] == ["s1"]
    assert inversions[0]["n50_time"] < inversions[0]["n40_time"]


def test_extract_feas_trajectories(tmp_path):
    record = {
        "run_id": "raw_feas",
        "instance": "path4",
        "method": "sat",
        "status": "FEAS",
        "lb": 1,
        "ub": 4,
        "solution": {"0": 1, "1": 3, "2": 2, "3": 4},
        "metadata": {
            "k_best": 1,
            "k_unsat": 4,
            "unsat_source": "counting",
            "probes": [
                {
                    "k": 1,
                    "status": "SAT",
                    "b": 1,
                    "t_encode": 0.001,
                    "t_solve": 0.002,
                    "variables": 16,
                    "clauses": 56,
                },
                {
                    "k": 2,
                    "status": "UNKNOWN",
                    "b": None,
                    "t_encode": 0.001,
                    "t_solve": 0.5,
                    "variables": 16,
                    "clauses": 74,
                },
            ],
        },
    }
    (tmp_path / "raw_feas.json").write_text(json.dumps(record), encoding="utf-8")

    entries = extract_feas_probe_trajectories(tmp_path)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["status"] == "FEAS"
    assert entry["k_best"] == 1
    assert entry["k_unsat"] == 4
    assert len(entry["probes"]) == 2
    assert entry["probes"][1]["status"] == "UNKNOWN"


def test_solver_sensitivity_winner_and_cv():
    rows = [
        _row(
            instance="i1",
            solver=solver,
            run_id=f"i1__sat__order__pairwise__{solver}__multi__sym0__ws0__s0",
            t_total=time_value,
        )
        for solver, time_value in (
            ("s1", 1.0),
            ("s2", 2.0),
            ("s3", 3.0),
            ("s4", 4.0),
        )
    ]
    meta = {"i1": GraphMeta(n=10, m=20, density=0.4, max_degree=5, UB=5)}
    table = solver_sensitivity_table(rows, meta)
    assert len(table) == 1
    item = table[0]
    assert item["winner"] == "s1"
    assert item["fast_over_slow"] == 0.25
    assert item["max_over_min"] == 4.0
    assert 0.0 <= item["cv"] <= 1.0
    assert item["n"] == 10 and item["m"] == 20 and item["UB"] == 5


def test_consistency_c_anchors_pass():
    if not (DEFAULT_W5_OUT / "24-rq1-final.md").is_file():
        pytest.skip("W5 generated docs not present yet")
    findings = verify_code_spec_paper_consistency()
    broken = [finding for finding in findings if finding.status != "ok"]
    assert broken == [], [f.message for f in broken]
    assert {finding.check_id for finding in findings} >= {
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8-R1",
        "C8-R2",
        "C8-R3",
        "C8-R4",
        "C8-R5",
        "C8-R6",
        "C9",
        "C10",
    }


def test_consistency_perturb_reported(monkeypatch):
    original = order._not_value

    def broken_not_value(var_of, n, v, q):
        if q == 1:
            return []
        return original(var_of, n, v, q)

    monkeypatch.setattr(order, "_not_value", broken_not_value)
    findings = verify_code_spec_paper_consistency()
    c3 = [finding for finding in findings if finding.check_id == "C3"]
    assert len(c3) == 1
    assert c3[0].status == "fail"
    assert "trivial" not in c3[0].message
    assert "_not_value" in c3[0].symbol or "_not_value" in c3[0].message
    assert "A.5" in c3[0].expected or "A.5" in c3[0].symbol


def test_canonical_memory_contract():
    assert canonical_sat_config().memory_limit == 12.0
    with pytest.raises(ValueError, match="memory_limit"):
        canonical_sat_config(memory_limit=None)
    with pytest.raises(ValueError, match="memory_limit"):
        canonical_sat_config(memory_limit=0)
    assert canonical_sat_config(memory_limit=12288.0).memory_limit == 12288.0


def test_cli_writes_four_docs_and_exit_zero(tmp_path):
    rc = w5_main(["--out-dir", str(tmp_path), "--check-only"])
    assert rc == 0
    for name in (
        "24-rq1-final.md",
        "25-rq2-final.md",
        "26-cross-review-consistency.md",
        "27-paper-v09-sat-sections.md",
    ):
        path = tmp_path / name
        assert path.is_file(), name
        text = path.read_text(encoding="utf-8")
        assert "sinh tự động" in text
        assert not re.search(r"(?i)\b(TODO|TBD|FIXME)\b", text)
        assert "docs/handoff/" not in text


def test_p1_r1_to_r6_source_evidence():
    exact = REPO_ROOT / "src" / "exact"
    common = (exact / "common.py").read_text(encoding="utf-8")
    tests = (REPO_ROOT / "tests" / "exact" / "test_exact_solvers.py").read_text(
        encoding="utf-8"
    )
    models = (REPO_ROOT / "docs" / "exact_models.md").read_text(encoding="utf-8")
    cp_sat = (exact / "cp_sat_solver.py").read_text(encoding="utf-8")

    assert "_skip_if_backend_unavailable" in tests
    assert "pytest.skip" in tests
    assert "cpoptimizer.exe" in tests
    assert "## Time accounting" in models
    assert "wall_time" in models
    assert "time_limit + 30 seconds" in models
    assert "def validate_exact_input" in common and "raise ValueError" in common
    assert "def warn_ignored_config" in common
    for name in ("gurobi_mip", "cplex_mip", "cplex_cp"):
        text = (exact / f"{name}.py").read_text(encoding="utf-8")
        assert "warn_ignored_config" in text
        assert "objective != model_objective" in text
    assert "def _safe_upper_bound" in cp_sat
    assert "return n - 1" in cp_sat
    assert "UNKNOWN" in cp_sat


def test_render_contains_source_note_and_banner():
    rows = [_row()]
    meta = load_graph_metadata([VALIDATION, LARGE])
    documents = render_w5_markdown(
        rows,
        rows,
        meta,
        [],
        [],
        evaluate_g4_gate([], [], expected_triaged=0),
        source_note="`results/pilot_rq1.csv`",
    )
    assert set(documents) == {
        "24-rq1-final.md",
        "25-rq2-final.md",
        "26-cross-review-consistency.md",
        "27-paper-v09-sat-sections.md",
    }
    for text in documents.values():
        assert "sinh tự động" in text
        assert "`results/pilot_rq1.csv`" in text
