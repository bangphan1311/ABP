"""Test pipeline `src/sat/solve.py`: khớp oracle, quyết định SAT/UNSAT, status."""

import random
from time import sleep

import pytest

from src.common.models import Config, Instance
from src.common.verify import verify
from src.exact.oracle import solve_oracle
from src.sat import generator
from src.sat.solve import summarise_result, solve_decision, solve_sat

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
    assert result.metadata["k_best"] == 2
    assert result.metadata["abp_encoding_stats"]["distance"] == 18
    probes = result.metadata["probes"]
    assert [probe["k"] for probe in probes] == [1, 2, 3]
    assert [probe["clauses"] for probe in probes] == [56, 74, 86]
    assert probes[0]["variables"] == 16
    assert probes[0]["t_encode"] > 0.0
    # R1: kích thước CNF của Result là của lần dò CUỐI (K=3), không phải K=1
    # (xem docs/sat_spec.md mục 6).
    assert result.variables == probes[-1]["variables"] == 16
    assert result.clauses == probes[-1]["clauses"] == 86
    assert result.t_total > 0.0


def test_cnf_size_is_reported_even_when_no_sat_probe(monkeypatch):
    # S2/RQ1: hết giờ trước khi solver kết luận vẫn phải có kích thước CNF.
    from src.sat.backend import SatBackend
    from src.sat.pairwise import build_cnf

    monkeypatch.setattr(SatBackend, "solve", lambda self, time_limit=None: "UNKNOWN")

    instance = generator.grid(6, 6)
    result = solve_sat(instance, Config(method="sat", time_limit=60.0))

    assert result.status == "TO"
    assert result.lb is None
    assert result.solution is None

    last_probe = result.metadata["probes"][-1]
    last_probe_cnf = build_cnf(instance, last_probe["k"])
    assert result.variables == last_probe_cnf.n_vars == last_probe["variables"]
    assert result.clauses == len(last_probe_cnf.clauses) == last_probe["clauses"]


def test_reported_cnf_size_comes_from_last_probed_k():
    # R1: Result.variables/clauses lấy từ CNF ở K cuối cùng đã dò — K đó có mệnh đề
    # khoảng cách, còn K=1 thì không (56 clause), nên hai số phải khác nhau.
    from src.sat.pairwise import build_cnf

    instance = generator.path(4)
    result = solve_sat(instance)
    last_k = result.metadata["probes"][-1]["k"]

    assert last_k == 3, "path4 dừng ở lần UNSAT đầu tiên K=3"
    last_cnf = build_cnf(instance, last_k)
    assert result.variables == last_cnf.n_vars
    assert result.clauses == len(last_cnf.clauses) == 86
    assert result.clauses != len(build_cnf(instance, 1).clauses)


def test_k_search_increases_from_lower_bound_and_stops_at_first_unsat():
    # Quang.md §3.3: K ← B + 1 từ cận dưới; UNSAT đầu tiên chốt B tối ưu.
    instance = generator.path(6)

    result = solve_sat(instance)

    probes = result.metadata["probes"]
    assert probes[0]["k"] == 1
    assert all(probe["status"] == "SAT" for probe in probes[:-1])
    assert probes[-1]["status"] == "UNSAT"  # dừng ngay ở UNSAT đầu tiên

    for previous, current in zip(probes, probes[1:]):
        assert current["k"] == previous["b"] + 1, "K kế tiếp phải là B + 1"

    assert result.status == "OPT"
    assert result.lb == result.ub == probes[-1]["k"] - 1


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

    # OPT cũng là kết quả hợp lệ: máy đủ nhanh thì kịp chứng minh tối ưu trong limit.
    assert result.status in ("OPT", "FEAS", "TO")
    if result.status == "FEAS":
        assert verify(instance, result.solution) == result.lb
        assert result.ub > result.lb
        assert result.gap == result.ub - result.lb


def test_time_limit_covers_encoding_and_solve():
    # B3: deadline là ngân sách cho cả build_cnf, add_clauses và solve của cả chuỗi K.
    # Encode của grid(8,8) K=1 (258k clause) đã lớn hơn limit này, nên lần dò đầu
    # không kịp vào solver.
    instance = generator.grid(8, 8)
    limit = 0.05

    result = solve_sat(instance, Config(method="sat", time_limit=limit))

    assert result.status in ("OPT", "TO", "FEAS")
    # Pha đang chạy khi hết giờ vẫn hoàn thành -> cho phép vượt, nhưng không vượt xa.
    assert result.t_total < 2 * limit + 2.0


def test_probe_passes_remaining_budget_to_solver_after_loading(monkeypatch):
    # Kiểm tra tất định: add_clauses tiêu hết ngân sách -> solve nhận số âm và
    # không chạy (UNKNOWN), dù CNF đã dựng xong.
    from src.sat import solve as solve_module
    from src.sat.backend import SatBackend

    budget_seen: list[float | None] = []
    original_solve = SatBackend.solve

    def slow_add_clauses(self, clauses):
        list(clauses)
        sleep(0.2)

    def spy_solve(self, time_limit=None):
        budget_seen.append(time_limit)
        return original_solve(self, time_limit=time_limit)

    monkeypatch.setattr(SatBackend, "add_clauses", slow_add_clauses)
    monkeypatch.setattr(SatBackend, "solve", spy_solve)

    status, solution, cnf, t_encode, t_solve = solve_module._probe(
        generator.path(4), 2, "pairwise", "pairwise", "cadical195", 0.05
    )

    assert status == "UNKNOWN"
    assert solution is None
    assert cnf is not None, "CNF vẫn phải được giữ lại cho số liệu RQ1"
    assert len(budget_seen) == 1 and budget_seen[0] < 0


def test_solution_never_violates_proven_unsat_threshold():
    # path4: ab = 2 và K = 3 đã chứng minh UNSAT -> OPT với lb = ub = 2, không hơn.
    instance = generator.path(4)

    result = solve_sat(instance)

    assert result.status == "OPT"
    assert (result.lb, result.ub, result.gap) == (2, 2, 0.0)
    assert verify(instance, result.solution) == 2
    assert solve_decision(instance, 3) == ("UNSAT", None)
    assert result.metadata["k_unsat"] == 3
    assert result.metadata["unsat_source"] == "solver"


def test_summarise_status_mapping():
    instance = generator.path(4)
    # Nhãn 2,4,1,3 cho objective min = 2.
    solution = {0: 2, 1: 4, 2: 1, 3: 3}
    assert verify(instance, solution) == 2

    assert summarise_result(instance, 0, 4, None, True, False) == (
        "TO",
        None,
        None,
        None,
        None,
    )
    assert summarise_result(instance, 0, 4, None, False, False)[0] == "ERR"
    assert summarise_result(instance, 4, 4, solution, False, True)[0] == "ERR"

    status, lb, ub, gap, value = summarise_result(instance, 2, 3, solution, False, False)
    assert (status, lb, ub, gap, value) == ("OPT", 2, 2, 0.0, 2)

    # hi = 4 đã chứng minh UNSAT -> ub = hi - 1 = 3.
    status, lb, ub, gap, value = summarise_result(instance, 2, 4, solution, True, False)
    assert (status, lb, ub, gap, value) == ("FEAS", 2, 3, 1.0, 2)


def test_unsupported_abp_encoding_raises():
    with pytest.raises(ValueError, match="abp_encoding"):
        solve_sat(generator.path(4), Config(method="sat", abp_encoding="bogus"))


def test_decision_unsupported_abp_encoding_raises():
    with pytest.raises(ValueError, match="abp_encoding"):
        solve_decision(generator.path(4), 2, Config(method="sat", abp_encoding="bogus"))


def test_kissat_solver_is_permanently_blocked():
    # Hạn chế vĩnh viễn W2 (ticket 09): qua PySAT kissat404 cho model sai và abort
    # process, không có binary ngoài -> ValueError rõ, không dựng backend.
    with pytest.raises(ValueError, match="hạn chế vĩnh viễn W2"):
        solve_sat(generator.path(4), Config(method="sat", sat_solver="kissat"))
    with pytest.raises(ValueError, match="hạn chế vĩnh viễn W2"):
        solve_decision(generator.path(4), 2, Config(method="sat", sat_solver="kissat"))


@pytest.mark.parametrize("bad_n", [True, 4.0])
def test_decision_non_integer_n_raises(bad_n):
    instance = Instance(
        id="bad-n", name="Bad n", n=bad_n, edges=((0, 1),), source="test", tier="toy"
    )

    with pytest.raises(ValueError, match="số nguyên"):
        solve_decision(instance, 2)


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


def test_self_loop_instance_raises_value_error():
    instance = Instance(
        id="loop", name="Loop", n=4, edges=((0, 0), (0, 1)), source="test", tier="toy"
    )
    with pytest.raises(ValueError, match="self-loop"):
        solve_sat(instance)
    with pytest.raises(ValueError, match="self-loop"):
        solve_decision(instance, 2)


@pytest.mark.parametrize("bad_ub", [0, -1, True, 2.0, "2"])
def test_invalid_external_ub_format_raises(bad_ub):
    with pytest.raises(ValueError, match="ub phải là số nguyên >= 1"):
        solve_sat(generator.path(4), ub=bad_ub)


def test_external_ub_below_verified_b_raises():
    # path4: B = 2 đã verify; ub = 1 sai -> ValueError (không phải ERR).
    with pytest.raises(ValueError, match="ub=1"):
        solve_sat(generator.path(4), ub=1)


def test_external_ub_equal_to_optimum_still_needs_solver_unsat():
    # ub không thay thế bằng chứng UNSAT: OPT vẫn do solver chứng minh ở K = 3.
    instance = generator.path(4)

    result = solve_sat(instance, ub=2)

    assert result.status == "OPT"
    assert (result.lb, result.ub, result.gap) == (2, 2, 0.0)
    assert result.metadata["unsat_source"] == "solver"
    assert [probe["k"] for probe in result.metadata["probes"]] == [1, 2, 3]


def test_absent_or_loose_external_ub_keeps_default_search():
    instance = generator.path(4)
    default = solve_sat(instance)

    for ub in (None, instance.n - 1, 100):
        result = solve_sat(instance, ub=ub)
        assert (result.status, result.lb, result.ub) == (default.status, 2, 2)
        assert [(p["k"], p["status"]) for p in result.metadata["probes"]] == [
            (p["k"], p["status"]) for p in default.metadata["probes"]
        ]
