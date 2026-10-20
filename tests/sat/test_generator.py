"""Test generator Tier 0/1 (ticket 11): tier, đếm đỉnh/cạnh từng họ, random có
seed, roundtrip write -> read, và solve khớp oracle sau khi đọc lại từ file.
"""

import pytest

from src.common.verify import verify
from src.exact.oracle import solve_oracle
from src.sat import generator
from src.sat.loader import read_instance, write_instance
from src.sat.solve import solve_sat

TIER0 = [
    generator.path(4),
    generator.cycle(5),
    generator.grid(2, 3),
    generator.complete(5),
    generator.star(6),
    generator.binary_tree(3),
    generator.disconnected(),
    generator.isolated(),
]

TIER1 = [
    generator.path(10),
    generator.cycle(9),
    generator.grid(3, 4),
    generator.complete(9),
    generator.star(12),
    generator.binary_tree(4),
    generator.random_graph(16, 42),
]


@pytest.mark.parametrize("instance", TIER0, ids=lambda g: g.id)
def test_tier0_convention(instance):
    assert instance.source == "generator"
    assert instance.tier == "tier0"
    assert instance.n <= 8


@pytest.mark.parametrize("instance", TIER1, ids=lambda g: g.id)
def test_tier1_convention(instance):
    assert instance.source == "generator"
    assert instance.tier == "tier1"
    assert 9 <= instance.n <= 16


def test_tier_boundary():
    assert generator.path(8).tier == "tier0"
    assert generator.path(9).tier == "tier1"
    assert generator.grid(2, 4).tier == "tier0"  # n = 8
    assert generator.grid(3, 3).tier == "tier1"  # n = 9
    assert generator.complete(8).tier == "tier0"
    assert generator.complete(9).tier == "tier1"
    assert generator.random_graph(8, 5).tier == "tier0"
    assert generator.random_graph(9, 5).tier == "tier1"


@pytest.mark.parametrize(
    "instance, n, m",
    [
        (generator.path(4), 4, 3),
        (generator.path(10), 10, 9),
        (generator.cycle(5), 5, 5),
        (generator.cycle(10), 10, 10),
        (generator.grid(2, 3), 6, 7),  # 2*(3-1) + 3*(2-1)
        (generator.grid(3, 4), 12, 17),  # 3*(4-1) + 4*(3-1)
        (generator.complete(5), 5, 10),
        (generator.complete(10), 10, 45),
        (generator.star(6), 7, 6),
        (generator.star(12), 13, 12),
        (generator.binary_tree(3), 7, 6),
        (generator.binary_tree(4), 15, 14),
        (generator.disconnected(), 6, 4),
        (generator.isolated(), 5, 3),
    ],
)
def test_family_vertex_and_edge_counts(instance, n, m):
    assert instance.n == n
    assert len(instance.edges) == m
    assert len(set(instance.edges)) == m
    assert all(0 <= u < n and 0 <= v < n and u != v for u, v in instance.edges)


def test_star_and_binary_tree_structure():
    assert set(generator.star(6).edges) == {(0, v) for v in range(1, 7)}
    tree = generator.binary_tree(4)
    assert set(tree.edges) == {
        (i, c) for i in range(7) for c in (2 * i + 1, 2 * i + 2)
    }


def test_disconnected_has_two_components():
    g = generator.disconnected()
    comp_a, comp_b = {0, 1, 2}, {3, 4, 5}
    inside = lambda u, v, comp: u in comp and v in comp  # noqa: E731
    assert all(inside(u, v, comp_a) or inside(u, v, comp_b) for u, v in g.edges)
    assert any(inside(u, v, comp_a) for u, v in g.edges)
    assert any(inside(u, v, comp_b) for u, v in g.edges)


def test_isolated_vertex_has_no_edges():
    g = generator.isolated()
    endpoints = {x for u, v in g.edges for x in (u, v)}
    assert 4 not in endpoints
    assert endpoints == {0, 1, 2, 3}


def test_random_graph_same_seed_same_graph():
    a = generator.random_graph(12, 7)
    assert a == generator.random_graph(12, 7)
    assert a.id == "random12-seed7"  # seed ghi trong id
    assert a.n == 12


def test_random_graph_different_seed_differs():
    assert generator.random_graph(12, 7).edges != generator.random_graph(
        12, 9
    ).edges


def test_random_graph_is_simple():
    g = generator.random_graph(16, 0)
    assert g.n == 16
    assert all(u < v for u, v in g.edges)
    assert len(set(g.edges)) == len(g.edges)


@pytest.mark.parametrize("n", [1, 17])
def test_random_graph_rejects_out_of_range(n):
    with pytest.raises(ValueError):
        generator.random_graph(n, 0)


def test_random_graph_seed_is_mandatory():
    with pytest.raises(TypeError):
        generator.random_graph(10)


@pytest.mark.parametrize("instance", TIER0 + TIER1, ids=lambda g: g.id)
def test_roundtrip_write_read(tmp_path, instance):
    path = tmp_path / f"{instance.id}.json"
    write_instance(path, instance)

    loaded = read_instance(path)

    assert loaded == instance
    assert isinstance(loaded.edges, tuple)
    assert all(isinstance(edge, tuple) for edge in loaded.edges)


@pytest.mark.parametrize(
    "instance",
    [
        generator.path(4),
        generator.cycle(5),
        generator.grid(2, 3),
        generator.complete(5),
        generator.star(6),
        generator.binary_tree(3),
        generator.disconnected(),
        generator.isolated(),
    ],
    ids=lambda g: g.id,
)
def test_roundtrip_solve_matches_oracle(tmp_path, instance):
    path = tmp_path / f"{instance.id}.json"
    write_instance(path, instance)
    loaded = read_instance(path)

    result = solve_sat(loaded)
    oracle = solve_oracle(loaded)

    assert result.status == "OPT", (instance.id, result.metadata.get("error"))
    assert result.lb == result.ub == oracle.lb, instance.id
    assert verify(loaded, result.solution) == oracle.lb, instance.id