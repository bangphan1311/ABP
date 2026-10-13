"""Test pipeline `src/sat/solve.py`: khớp oracle, quyết định SAT/UNSAT, status."""

import random

import pytest

from src.common.models import Config, Instance
from src.common.verify import verify
from src.exact.oracle import solve_oracle
from src.sat import generator
from src.sat.solve import solve_decision, solve_sat
from src.sat.solve import _summarise

TOY_INSTANCES = (
    generator.path(4),
    generator.cycle(5),
    generator.complete(3),
    generator.path(6),
)


def test_sat_matches_oracle_on_toy_instances():
    for instance in TOY_INSTANCES:
        sat = solve_sat(instance)
        oracle = solve_oracle(instance)

        assert sat.status == "OPT", instance.id
        assert sat.lb == oracle.lb, instance.id
        assert sat.ub == oracle.ub, instance.id
        assert sat.gap == 0.0, instance.id
        assert verify(instance, sat.solution) == sat.lb, instance.id


def test_sat_reports_verified_value_and_encoding_size():
    instance = generator.path(4)

    result = solve_sat(instance)

    assert result.lb == 2
    assert verify(instance, result.solution) == 2
    assert result.variables == 16
    assert result.clauses == 74  # encoding của ngưỡng tốt nhất
    assert result.metadata["k_best"] == 2
    assert result.metadata["abp_encoding_stats"]["distance"] == 18
    assert [probe["k"] for probe in result.metadata["probes"]] == [2, 3]
    assert result.t_total > 0.0


def test_decision_problem_at_k():
    instance = generator.path(4)

    status, labeling = solve_decision(instance, 2)
    assert status == "SAT"
    assert verify(instance, labeling) >= 2

    assert solve_decision(instance, 3) == ("UNSAT", None)
    assert solve_decision(instance, 4) == ("UNSAT", None)  # ngưỡng tầm thường


def test_at_k_trivial_upper_threshold_is_unsat():
    instance = generator.cycle(5)

    # K = n luôn UNSAT nhưng vẫn dựng CNF và phải ra UNSAT thật.
    assert solve_decision(instance, instance.n) == ("UNSAT", None)


def _disconnected_with_isolated_vertex() -> Instance:
    # Hai đường rời 0-1-2 và 3-4-5, đỉnh 6 cô lập.
    return Instance(
        id="disjoint",
        name="Two paths plus isolated vertex",
        n=7,
        edges=((0, 1), (1, 2), (3, 4), (4, 5)),
        source="test",
        tier="toy",
    )


def _random_instance(seed: int, n: int, p: float) -> Instance:
    rng = random.Random(seed)
    edges = [
        (u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < p
    ]
    if not edges:  # đảm bảo có cạnh để ABP xác định
        edges = [(0, 1)]
    return Instance(
        id=f"random{seed}",
        name=f"Random graph seed={seed}",
        n=n,
        edges=tuple(edges),
        source="test",
        tier="toy",
    )


def test_sat_matches_oracle_on_disconnected_and_random_graphs():
    instances = [
        _disconnected_with_isolated_vertex(),
        _random_instance(seed=1, n=6, p=0.2),
        _random_instance(seed=2, n=7, p=0.4),
        _random_instance(seed=3, n=5, p=0.1),
    ]

    for instance in instances:
        sat = solve_sat(instance)
        oracle = solve_oracle(instance)

        assert sat.status == "OPT", instance.id
        assert sat.lb == oracle.lb, instance.id
        assert verify(instance, sat.solution) == sat.lb, instance.id


def test_tiny_time_limit_without_incumbent_returns_to():
    instance = generator.grid(6, 6)

    result = solve_sat(instance, Config(method="sat", time_limit=1e-9))

    assert result.status == "TO"
    assert result.lb is None
    assert result.solution is None


def test_time_limited_run_is_feas_or_to_and_consistent():
    instance = generator.grid(6, 6)

    result = solve_sat(instance, Config(method="sat", time_limit=0.05))

    assert result.status in ("FEAS", "TO")
    if result.status == "FEAS":
        assert verify(instance, result.solution) == result.lb
        assert result.ub > result.lb
        assert result.gap == result.ub - result.lb


def test_solution_never_violates_proven_unsat_threshold():
    # K = 3 là UNSAT trên path4, nên không được có OPT với lb >= 3.
    result = solve_sat(generator.path(4))

    assert result.lb < 3


def test_summarise_status_mapping():
    instance = generator.path(4)
    # Nhãn 2,4,1,3 cho objective min = 2.
    solution = {0: 2, 1: 4, 2: 1, 3: 3}
    assert verify(instance, solution) == 2

    assert _summarise(instance, 0, 4, None, True, False) == ("TO", None, None, None, None)
    assert _summarise(instance, 0, 4, None, False, False)[0] == "ERR"
    assert _summarise(instance, 4, 4, solution, False, True)[0] == "ERR"

    status, lb, ub, gap, value = _summarise(instance, 2, 3, solution, False, False)
    assert (status, lb, ub, gap, value) == ("OPT", 2, 2, 0.0, 2)

    status, lb, ub, gap, value = _summarise(instance, 2, 4, solution, True, False)
    assert (status, lb, ub, gap, value) == ("FEAS", 2, 4, 2.0, 2)


def test_unsupported_abp_encoding_raises():
    with pytest.raises(ValueError, match="abp_encoding"):
        solve_sat(generator.path(4), Config(method="sat", abp_encoding="order"))


@pytest.mark.parametrize(
    "edges",
    [
        ((0, 9),),  # đỉnh ngoài khoảng 0..n-1
        ((-1, 1),),  # đỉnh âm
        ((0, "1"),),  # đỉnh không phải số nguyên
        ((0, True),),  # bool không phải đỉnh hợp lệ
    ],
)
def test_invalid_edge_endpoint_raises_value_error(edges):
    # Instance dựng tay: phải ValueError (như loader và verify), không KeyError.
    instance = Instance(
        id="bad-edges", name="Bad edges", n=4, edges=edges, source="test", tier="toy"
    )

    with pytest.raises(ValueError):
        solve_sat(instance)
    with pytest.raises(ValueError):
        solve_decision(instance, 2)


def test_ignored_config_fields_emit_one_warning():
    # W1 chưa cài đặt memory_limit/search_mode/symmetry/warm_start/seed -> phải cảnh báo.
    config = Config(
        method="sat",
        memory_limit=1.0,
        search_mode="staircase",
        symmetry=True,
        warm_start=True,
        seed=7,
    )

    with pytest.warns(UserWarning, match="memory_limit") as record:
        solve_sat(generator.path(4), config)

    assert len(record) == 1
    message = str(record[0].message)
    for name in ("memory_limit", "search_mode", "symmetry", "warm_start", "seed"):
        assert name in message


def test_default_config_fields_emit_no_warning(recwarn):
    solve_sat(generator.path(4))

    assert not [w for w in recwarn.list if "bỏ qua" in str(w.message)]