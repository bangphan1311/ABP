"""G1 (#14): pipeline SAT khớp oracle brute-force và CP-SAT trên đồ thị nhỏ n <= 8.

So sánh B tối ưu và SAT/UNSAT tại từng K = 1..n. Chỉ dùng path, cycle, grid, complete.
"""

import pytest

from src.common.models import Config
from src.common.verify import verify
from src.exact.cp_sat_solver import solve_cp_sat
from src.exact.oracle import solve_oracle
from src.sat import generator
from src.sat.solve import solve_decision, solve_sat

SMALL_GRAPHS = [
    generator.path(4),
    generator.path(8),
    generator.cycle(3),
    generator.cycle(5),
    generator.cycle(8),
    generator.grid(2, 2),
    generator.grid(2, 4),
    generator.complete(3),
    generator.complete(5),
    generator.complete(8),
]


@pytest.mark.parametrize("instance", SMALL_GRAPHS, ids=lambda g: g.id)
def test_g1_matches_brute_force_and_cp_sat(instance):
    oracle = solve_oracle(instance)
    cp = solve_cp_sat(instance, Config(method="cp_sat", time_limit=30, seed=0))
    sat = solve_sat(instance)

    assert cp.status == "OPT" and cp.lb == oracle.lb, instance.id
    assert sat.status == "OPT", (instance.id, sat.metadata.get("error"))
    assert sat.lb == sat.ub == oracle.lb == cp.lb, instance.id
    assert verify(instance, sat.solution) == oracle.lb, instance.id


@pytest.mark.parametrize("instance", SMALL_GRAPHS, ids=lambda g: g.id)
def test_g1_sat_unsat_at_each_k_matches_oracle(instance):
    b_opt = solve_oracle(instance).lb

    for k in range(1, instance.n + 1):
        status, labeling = solve_decision(instance, k)
        expected = "SAT" if k <= b_opt else "UNSAT"
        assert status == expected, (instance.id, k)
        if status == "SAT":
            assert verify(instance, labeling) >= k, (instance.id, k)
