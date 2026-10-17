"""Test `src/sat/generator.py` và `src/sat/loader.py`: số cạnh và roundtrip."""

import json

import pytest

from src.sat import generator
from src.sat.loader import read_instance, write_instance


def test_generator_edge_counts():
    assert generator.path(4).edges == ((0, 1), (1, 2), (2, 3))
    assert generator.path(6).n == 6
    assert len(generator.path(6).edges) == 5

    assert len(generator.cycle(5).edges) == 5
    assert (4, 0) in generator.cycle(5).edges

    assert generator.complete(3).edges == ((0, 1), (0, 2), (1, 2))
    assert len(generator.complete(5).edges) == 10

    grid = generator.grid(2, 3)
    assert grid.n == 6
    # 2 hàng: 2 cạnh ngang mỗi hàng; 3 cột: 1 cạnh dọc mỗi cột.
    assert len(grid.edges) == 2 * 2 + 3 * 1
    assert set(grid.edges) == {
        (0, 1), (1, 2), (3, 4), (4, 5),
        (0, 3), (1, 4), (2, 5),
    }


def test_generator_rejects_too_small_graphs():
    with pytest.raises(ValueError, match="path cần"):
        generator.path(1)
    with pytest.raises(ValueError, match="cycle cần"):
        generator.cycle(2)
    with pytest.raises(ValueError, match="grid cần"):
        generator.grid(1, 5)
    with pytest.raises(ValueError, match="complete cần"):
        generator.complete(1)


def test_loader_roundtrip(tmp_path):
    instance = generator.cycle(5)
    path = tmp_path / "cycle5.json"

    write_instance(path, instance)
    loaded = read_instance(path)

    assert loaded == instance
    assert isinstance(loaded.edges, tuple)
    assert all(isinstance(edge, tuple) for edge in loaded.edges)


def test_loader_roundtrip_with_hand_written_file(tmp_path):
    path = tmp_path / "path4.json"
    path.write_text(
        json.dumps(
            {
                "id": "path4",
                "name": "Path graph with 4 vertices",
                "n": 4,
                "edges": [[0, 1], [1, 2], [2, 3]],
                "source": "test",
                "tier": "toy",
            }
        ),
        encoding="utf-8",
    )

    loaded = read_instance(path)

    assert loaded.n == 4
    assert loaded.edges == ((0, 1), (1, 2), (2, 3))


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"id": "x"}, "thiếu trường"),
        ({"id": "x", "name": "n", "n": "4", "edges": [], "source": "s", "tier": "t"}, "'n'"),
        ({"id": "x", "name": "n", "n": -1, "edges": [], "source": "s", "tier": "t"}, "'n'"),
        ({"id": "x", "name": "n", "n": 3, "edges": "x", "source": "s", "tier": "t"}, "danh sách"),
        ({"id": "x", "name": "n", "n": 3, "edges": [[0, 1, 2]], "source": "s", "tier": "t"}, "cặp"),
        ({"id": "x", "name": "n", "n": 3, "edges": [[0, 5]], "source": "s", "tier": "t"}, "ngoài khoảng"),
        ({"id": "x", "name": "n", "n": 3, "edges": [[1, 1]], "source": "s", "tier": "t"}, "tự khuyên"),
        ({"id": "x", "name": "n", "n": 3, "edges": [["0", 1]], "source": "s", "tier": "t"}, "số nguyên"),
        ({"id": 1, "name": "n", "n": 3, "edges": [], "source": "s", "tier": "t"}, "'id'"),
    ],
)
def test_loader_rejects_invalid_files(tmp_path, payload, message):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        read_instance(path)


def test_generator_output_survives_roundtrip_and_solves(tmp_path):
    from src.exact.oracle import solve_oracle
    from src.sat.solve import solve_sat

    instance = generator.grid(2, 3)
    path = tmp_path / "grid.json"

    write_instance(path, instance)
    result = solve_sat(read_instance(path))
    oracle = solve_oracle(instance)

    assert result.status == "OPT"
    assert result.lb == oracle.lb


@pytest.mark.parametrize(
    "instance, n, m",
    [
        (generator.path(2), 2, 1),
        (generator.path(7), 7, 6),
        (generator.cycle(3), 3, 3),
        (generator.cycle(8), 8, 8),
        (generator.grid(2, 2), 4, 4),
        (generator.grid(3, 4), 12, 17),
        (generator.complete(2), 2, 1),
        (generator.complete(6), 6, 15),
    ],
)
def test_generator_vertex_and_edge_counts(instance, n, m):
    assert instance.n == n
    assert len(instance.edges) == m
    assert len(set(instance.edges)) == m
    assert all(0 <= u < n and 0 <= v < n and u != v for u, v in instance.edges)


def test_loader_dedupes_unordered_edges(tmp_path):
    path = tmp_path / "dup.json"
    payload = {
        "id": "dup", "name": "dup", "n": 3,
        "edges": [[0, 1], [1, 0], [1, 2], [2, 1], [0, 1]],
        "source": "test", "tier": "toy",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert read_instance(path).edges == ((0, 1), (1, 2))


@pytest.mark.parametrize("n, edges", [(0, []), (3, [])])
def test_loader_rejects_empty_graph(tmp_path, n, edges):
    path = tmp_path / "empty.json"
    payload = {"id": "e", "name": "e", "n": n, "edges": edges, "source": "s", "tier": "t"}
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        read_instance(path)
