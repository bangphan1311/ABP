
import random

from src.common.models import Config, Instance
from src.common.verify import verify
from src.exact.oracle import solve_oracle
from src.exact.cp_sat_solver import solve_cp_sat


def assert_cp_sat_matches_oracle(instance: Instance):
    """So sánh nghiệm tối ưu của CP-SAT với Oracle."""

    oracle_result = solve_oracle(instance)
    cp_result = solve_cp_sat(
        instance,
        Config(method="cp_sat", time_limit=30, seed=42),
    )

    assert oracle_result.status == "OPT"
    assert cp_result.status == "OPT", cp_result.metadata

    assert cp_result.lb == oracle_result.lb
    assert cp_result.ub == oracle_result.ub
    assert cp_result.solution is not None

    # Kiểm chứng độc lập nghiệm do CP-SAT trả về.
    assert verify(instance, cp_result.solution) == oracle_result.lb


def test_cp_sat_matches_oracle_on_path4():
    instance = Instance(
        id="path4",
        name="Path graph with 4 vertices",
        n=4,
        edges=((0, 1), (1, 2), (2, 3)),
        source="test",
        tier="small",
    )

    assert_cp_sat_matches_oracle(instance)


def test_cp_sat_matches_oracle_on_cycle5():
    instance = Instance(
        id="cycle5",
        name="Cycle graph with 5 vertices",
        n=5,
        edges=((0, 1), (1, 2), (2, 3), (3, 4), (4, 0)),
        source="test",
        tier="small",
    )

    assert_cp_sat_matches_oracle(instance)


def test_cp_sat_matches_oracle_on_grid2x2():
    # Đồ thị lưới 2x2: bốn đỉnh, bốn cạnh.
    instance = Instance(
        id="grid2x2",
        name="2x2 grid graph",
        n=4,
        edges=((0, 1), (0, 2), (1, 3), (2, 3)),
        source="test",
        tier="small",
    )

    assert_cp_sat_matches_oracle(instance)


def test_cp_sat_matches_oracle_on_random_small_graphs():
    # Dùng seed cố định để tái lập đúng các đồ thị khi chạy lại test.
    for seed in (10, 20, 30):
        rng = random.Random(seed)
        n = 6

        edges = tuple(
            (u, v)
            for u in range(n)
            for v in range(u + 1, n)
            if rng.random() < 0.4
        )

        # Đảm bảo đồ thị có ít nhất một cạnh.
        if not edges:
            edges = ((0, 1),)

        instance = Instance(
            id=f"random6_seed{seed}",
            name=f"Random graph with 6 vertices (seed={seed})",
            n=n,
            edges=edges,
            source="test",
            tier="small",
        )

        assert_cp_sat_matches_oracle(instance)
