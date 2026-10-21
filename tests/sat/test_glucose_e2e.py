"""Ticket 09: Glucose4 chạy end-to-end qua cùng pipeline SatBackend (không pipeline riêng).

Khớp oracle brute-force trên toy theo pattern `tests/sat/test_g1_oracle.py`.
Không phụ thuộc timeout chặt: budget của glucose không ổn định khi giải nhiều
lần trong cùng process (`docs/sat_tooling.md` mục Timeout), nên test có
time-limit dùng ngân sách rộng.
"""

import pytest

from src.common.models import Config
from src.common.verify import verify
from src.exact.oracle import solve_oracle
from src.sat import generator
from src.sat.solve import solve_decision, solve_sat

TOY_GRAPHS = [
    generator.path(4),
    generator.cycle(5),
    generator.grid(3, 3),
    generator.complete(5),
]

GLUCOSE = Config(method="sat", sat_solver="glucose4")


@pytest.mark.parametrize("instance", TOY_GRAPHS, ids=lambda g: g.id)
def test_glucose_e2e_matches_oracle_on_toy(instance):
    sat = solve_sat(instance, GLUCOSE)
    oracle = solve_oracle(instance)

    assert sat.status == "OPT", (instance.id, sat.metadata.get("error"))
    assert sat.lb == sat.ub == oracle.lb, instance.id
    assert verify(instance, sat.solution) == oracle.lb, instance.id
    assert sat.metadata["sat_solver"] == "glucose4"
    assert sat.peak_memory > 0.0


def test_glucose_k_search_proves_optimum_and_decodes():
    # path4: B = 2. K-search: K=1 SAT, K=2 SAT, K=3 UNSAT -> OPT = 2.
    instance = generator.path(4)
    result = solve_sat(instance, GLUCOSE)

    probes = result.metadata["probes"]
    assert [probe["k"] for probe in probes] == [1, 2, 3]
    assert [probe["status"] for probe in probes] == ["SAT", "SAT", "UNSAT"]
    assert result.status == "OPT"
    assert (result.lb, result.ub, result.gap) == (2, 2, 0.0)
    assert result.metadata["k_best"] == 2
    # decode đúng: nghiệm là hoán vị 1..n và verify lại đúng B tối ưu.
    assert set(result.solution) == set(range(instance.n))
    assert set(result.solution.values()) == {1, 2, 3, 4}
    assert verify(instance, result.solution) == 2


def test_glucose_decision_status_matches_thresholds():
    instance = generator.cycle(5)
    b_opt = solve_oracle(instance).lb

    for k in range(1, instance.n + 1):
        status, labeling = solve_decision(instance, k, GLUCOSE)
        assert status == ("SAT" if k <= b_opt else "UNSAT"), (instance.id, k)
        if status == "SAT":
            assert verify(instance, labeling) >= k


def test_glucose_wide_time_limit_solves_toy():
    # Caveat docs/sat_tooling.md: budget glucose không ổn định giữa các lần giải
    # trong cùng process -> không test timeout chặt, chỉ ngân sách rộng.
    config = Config(method="sat", sat_solver="glucose4", time_limit=30.0)

    result = solve_sat(generator.path(6), config)

    assert result.status == "OPT"
    assert result.t_total < 30.0
