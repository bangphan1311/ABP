"""Test pilot W3: lưới 2x2, lưới solver (kissat bị loại), CSV, subset tất định."""

from __future__ import annotations

import csv
from dataclasses import replace

import pytest

from experiments import make_validation_subset as subset_mod
from experiments.pilot_common import (
    FIELDS,
    base_config,
    collect_metrics,
    instance_paths,
    run_pilot,
    status_counts,
    warning_flags,
    write_csv,
)
from experiments.pilot_rq1 import build_rq1_grid
from experiments.pilot_rq2 import RQ2_SOLVERS, build_rq2_grid, solver_note
from src.sat import generator
from src.sat.backend import KISSAT_LIMITATION, PYSAT_KISSAT_FAMILIES, solver_family
from src.sat.loader import read_instance, write_instance


def tiny_instance_file(tmp_path):
    path = tmp_path / "path4.json"
    write_instance(path, generator.path(4))
    return path


def test_rq1_grid_is_the_2x2_of_encodings():
    grid = build_rq1_grid(base_config(time_limit=5.0))

    assert len(grid) == 4
    assert {(cfg.abp_encoding, cfg.amo_encoding) for cfg in grid} == {
        ("pairwise", "pairwise"),
        ("pairwise", "seqcounter"),
        ("order", "pairwise"),
        ("order", "seqcounter"),
    }
    for cfg in grid:
        assert cfg.method == "sat"
        assert cfg.sat_solver == "cadical195"
        assert cfg.search_mode == "multi"
        assert cfg.symmetry is False
        assert cfg.warm_start is False
        assert cfg.time_limit == 5.0

    unique_grid = build_rq1_grid(base_config(time_limit=5.0), unique_only=True)
    assert len(unique_grid) == 3
    assert {(cfg.abp_encoding, cfg.amo_encoding) for cfg in unique_grid} == {
        ("pairwise", "pairwise"),
        ("pairwise", "seqcounter"),
        ("order", "pairwise"),
    }


def test_rq2_grid_varies_only_the_solver():
    base = replace(
        base_config(time_limit=5.0),
        abp_encoding="pairwise",
        amo_encoding="seqcounter",
    )

    grid = build_rq2_grid(base)

    assert [cfg.sat_solver for cfg in grid] == list(RQ2_SOLVERS)
    assert {(cfg.abp_encoding, cfg.amo_encoding) for cfg in grid} == {
        ("pairwise", "seqcounter")
    }
    assert {cfg.time_limit for cfg in grid} == {5.0}


def test_rq2_never_runs_kissat_and_explains_why():
    assert all(
        solver_family(name) not in PYSAT_KISSAT_FAMILIES for name in RQ2_SOLVERS
    )
    assert "kissat" not in RQ2_SOLVERS

    with pytest.raises(ValueError, match="kissat"):
        build_rq2_grid(base_config(), solvers=("cadical195", "kissat404"))

    note = solver_note()
    assert KISSAT_LIMITATION in note
    assert "Kissat không được chạy" in note


def test_collect_metrics_flattens_record():
    record = {
        "run_id": "r1",
        "instance": "path4",
        "abp_encoding": "pairwise",
        "amo_encoding": "pairwise",
        "solver": "cadical195",
        "status": "OPT",
        "lb": 2,
        "ub": 2,
        "t_encode": 0.25,
        "t_solve": 0.5,
        "t_total": 0.75,
        "variables": 16,
        "clauses": 86,
        "peak_memory": 40.125,
        "metadata": {"probes": [{"k": 1}, {"k": 2}, {"k": 3}]},
        "error": None,
    }

    row = collect_metrics(record)

    assert row["gap"] == 0
    assert row["n_probes"] == 3
    assert row["variables"] == 16 and row["clauses"] == 86
    assert warning_flags(row) == []
    assert warning_flags(row, max_vars=10, slow_encode=0.1) == [
        "CNF_TOO_LARGE(vars>10)",
        "SLOW_ENCODE(>0.1s)",
    ]


def test_warning_flags_report_memory_status():
    row = collect_metrics({"run_id": "r", "instance": "i", "status": "MO"})

    assert warning_flags(row) == ["MO"]


def test_rq1_pilot_writes_csv_on_toy_instance(tmp_path):
    instance = tiny_instance_file(tmp_path)
    # Hai ô đại diện: cả hai abp_encoding, mỗi bên một kiểu AMO.
    configs = [
        cfg
        for cfg in build_rq1_grid(base_config(time_limit=10.0))
        if (cfg.abp_encoding, cfg.amo_encoding)
        in {("pairwise", "pairwise"), ("order", "seqcounter")}
    ]

    rows = run_pilot([instance], configs, tmp_path / "raw", log=lambda _m: None)
    csv_path = write_csv(tmp_path / "out" / "pilot_rq1.csv", rows)

    assert len(rows) == 2
    assert status_counts(rows) == {"OPT": 2}
    assert all(row["lb"] == 2 and row["gap"] == 0 for row in rows)
    assert all(row["n_probes"] >= 2 for row in rows)

    with csv_path.open(newline="", encoding="utf-8") as handle:
        saved = list(csv.DictReader(handle))
    assert len(saved) == 2
    assert tuple(saved[0]) == FIELDS
    assert {row["abp_encoding"] for row in saved} == {"pairwise", "order"}


def test_rq2_pilot_runs_every_solver_and_writes_csv(tmp_path):
    instance = tiny_instance_file(tmp_path)
    base = replace(
        base_config(time_limit=10.0),
        abp_encoding="pairwise",
        amo_encoding="pairwise",
    )

    rows = run_pilot(
        [instance], build_rq2_grid(base), tmp_path / "raw", log=lambda _m: None
    )
    csv_path = write_csv(tmp_path / "out" / "pilot_rq2.csv", rows)

    assert [row["solver"] for row in rows] == list(RQ2_SOLVERS)
    assert status_counts(rows) == {"OPT": len(RQ2_SOLVERS)}
    assert all(row["lb"] == 2 for row in rows)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        saved = list(csv.DictReader(handle))
    assert tuple(saved[0]) == FIELDS
    assert {row["solver"] for row in saved} == set(RQ2_SOLVERS)


def test_instance_paths_rejects_missing_or_empty_dir(tmp_path):
    with pytest.raises(ValueError, match="Không thấy thư mục instance"):
        instance_paths(tmp_path / "missing")

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="rỗng"):
        instance_paths(empty)


def test_validation_subset_sizes_and_connectivity(tmp_path):
    written = subset_mod.generate_subset(tmp_path, seed=subset_mod.DEFAULT_SEED)
    paths = written["validation"] + written["large"]

    assert [read_instance(path).n for path in paths] == [8, 10, 12, 14, 16, 20, 24, 28, 40, 50]
    for path in paths:
        instance = read_instance(path)
        assert instance.source == "generator"
        assert instance.tier == "validation"
        assert _is_connected(instance)


def test_validation_subset_is_deterministic(tmp_path):
    first = subset_mod.generate_subset(tmp_path / "a", seed=5)
    second = subset_mod.generate_subset(tmp_path / "b", seed=5)
    other = subset_mod.generate_subset(tmp_path / "c", seed=6)

    def flat(written):
        return written["validation"] + written["large"]

    for left, right in zip(flat(first), flat(second)):
        assert left.read_bytes() == right.read_bytes()

    assert flat(first)[0].read_bytes() != flat(other)[0].read_bytes()


def test_random_connected_rejects_bad_size():
    with pytest.raises(ValueError, match="n >= 2"):
        subset_mod.random_connected(1, 0)


def _is_connected(instance) -> bool:
    adjacency: dict[int, list[int]] = {v: [] for v in range(instance.n)}
    for u, v in instance.edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    seen = {0}
    stack = [0]
    while stack:
        for neighbor in adjacency[stack.pop()]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == instance.n
