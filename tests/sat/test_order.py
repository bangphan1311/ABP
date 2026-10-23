"""Test encoding `order`: cùng SAT/UNSAT với pairwise và oracle trên toy.

Ticket 05: cùng decision problem với pairwise, decode ra hoán vị hợp lệ,
verify() pass, đổi AMO không đổi kết quả. Toy: path4, cycle5, grid3x3, complete5
(theo brief; n <= 9 để chạy được oracle brute-force).
"""

import pytest

from src.common.models import Config
from src.common.verify import verify
from src.exact.oracle import solve_oracle
from src.sat import generator
from src.sat.backend import SatBackend
from src.sat.order import build_cnf, decode_model
from src.sat.pairwise import DEFAULT_ABP_ENCODING
from src.sat.solve import ABP_ENCODINGS, solve_decision, solve_sat

TOY_GRAPHS = [
    generator.path(4),
    generator.cycle(5),
    generator.grid(3, 3),
    generator.complete(5),
]

ORDER = Config(method="sat", abp_encoding="order")
ORDER_SEQCOUNTER = Config(method="sat", abp_encoding="order", amo_encoding="seqcounter")


@pytest.fixture(scope="module", params=TOY_GRAPHS, ids=lambda g: g.id)
def toy(request):
    """Instance kèm B tối ưu của oracle; tính một lần mỗi đồ thị cho cả module."""
    instance = request.param
    return instance, solve_oracle(instance).lb


def test_order_sat_unsat_at_each_k_matches_pairwise_and_oracle(toy):
    instance, b_opt = toy

    for k in range(1, instance.n + 1):
        expected = "SAT" if k <= b_opt else "UNSAT"

        status_pairwise, _ = solve_decision(instance, k)  # mặc định pairwise
        status_order, labeling = solve_decision(instance, k, ORDER)

        assert status_pairwise == expected, (instance.id, k, "pairwise")
        assert status_order == expected, (instance.id, k, "order")
        if status_order == "SAT":
            assert verify(instance, labeling) >= k, (instance.id, k)


def test_order_solve_sat_matches_oracle(toy):
    instance, b_opt = toy

    result = solve_sat(instance, ORDER)

    assert result.status == "OPT", (instance.id, result.metadata.get("error"))
    assert result.lb == result.ub == b_opt, instance.id
    assert verify(instance, result.solution) == b_opt, instance.id
    assert result.metadata["abp_encoding"] == "order", instance.id
    assert result.metadata["abp_encoding_stats"] is not None, instance.id


def test_order_variable_and_clause_counts_path4_k2():
    cnf = build_cnf(generator.path(4), 2)

    assert cnf.n == 4
    assert cnf.n_vars == 12  # n * (n - 1) biến o[v][p] với p ∈ 1..n-1
    assert cnf.stats["assignment"] == 4 * 2  # chuỗi đơn điệu: n * (n - 2)
    assert cnf.stats["permutation"] == 6 * 4  # C(4,2) cặp đỉnh × n nhãn
    assert cnf.stats["distance"] == 3 * 2 * (4 - 1)  # 3 cạnh, 6 cặp nhãn mỗi cạnh
    assert len(cnf.clauses) == 8 + 24 + 18
    assert cnf.n_vars == max(abs(lit) for clause in cnf.clauses for lit in clause)
    assert cnf.amo_encoding == "pairwise"


def test_order_clause_counts_path4_k1_and_k3():
    k1 = build_cnf(generator.path(4), 1)
    k3 = build_cnf(generator.path(4), 3)

    assert k1.stats["distance"] == 0
    assert len(k1.clauses) == 8 + 24

    # distance mỗi cạnh = 2 * ((n-1) + (n-2)) = 10, cùng công thức với pairwise.
    assert k3.stats["distance"] == 3 * 10
    assert len(k3.clauses) == 8 + 24 + 30


def test_order_change_amo_encoding_does_not_change_cnf():
    # Encoding order không có ràng buộc at-most-one (chuỗi thay AMO) nên AMO
    # chỉ được ghi nhận, không đổi clause — yêu cầu "đổi AMO không sửa encoding".
    instance = generator.path(4)

    default = build_cnf(instance, 2)
    seqcounter = build_cnf(instance, 2, amo_encoding="seqcounter")

    assert seqcounter.clauses == default.clauses
    assert seqcounter.n_vars == default.n_vars
    assert seqcounter.stats == default.stats
    assert seqcounter.amo_encoding == "seqcounter"


def test_order_seqcounter_amo_matches_oracle_at_each_k(toy):
    instance, b_opt = toy

    for k in range(1, instance.n + 1):
        expected = "SAT" if k <= b_opt else "UNSAT"
        status, labeling = solve_decision(instance, k, ORDER_SEQCOUNTER)
        assert status == expected, (instance.id, k)
        if status == "SAT":
            assert verify(instance, labeling) >= k, (instance.id, k)


def test_order_decode_model_builds_labeling():
    cnf = build_cnf(generator.path(4), 2)
    # f = {0: 3, 1: 1, 2: 4, 3: 2}; o[v][p] = (f(v) <= p) chỉ bật khi p >= f(v).
    model = [
        cnf.var_of[(0, 3)],
        cnf.var_of[(1, 1)],
        cnf.var_of[(1, 2)],
        cnf.var_of[(1, 3)],
        cnf.var_of[(3, 2)],
        cnf.var_of[(3, 3)],
    ]

    assert decode_model(cnf, model) == {0: 3, 1: 1, 2: 4, 3: 2}


def test_order_decode_model_rejects_non_permutation():
    cnf = build_cnf(generator.path(4), 2)

    with pytest.raises(ValueError, match="hoán vị"):
        # f(0) = f(1) = 1: hai đỉnh cùng nhãn, không phải hoán vị.
        decode_model(cnf, [cnf.var_of[(0, 1)], cnf.var_of[(1, 1)]])

    with pytest.raises(ValueError, match="Không có model"):
        decode_model(cnf, None)


def test_order_build_cnf_rejects_bad_input():
    with pytest.raises(ValueError, match="K phải"):
        build_cnf(generator.path(4), 0)
    with pytest.raises(TypeError):
        build_cnf(generator.path(4), True)

    empty = generator.path(4)
    empty.edges = ()
    with pytest.raises(ValueError, match="không có cạnh"):
        build_cnf(empty, 2)

    loop = generator.path(4)
    loop.edges = ((0, 0), (0, 1))
    with pytest.raises(ValueError, match="self-loop"):
        build_cnf(loop, 2)


def test_order_build_cnf_at_trivial_k_is_still_unsat():
    # Như pairwise: build_cnf không tự từ chối K >= n; CNF dựng ra phải UNSAT
    # (mọi cặp nhãn khác nhau đã bị cấm trên cạnh, cùng nhãn bị cấm bởi permutation).
    cnf = build_cnf(generator.path(4), 4)

    with SatBackend("cadical195") as backend:
        backend.add_clauses(cnf.clauses)
        assert backend.solve() == "UNSAT"


def test_order_encoding_registered_and_default_unchanged():
    assert "order" in ABP_ENCODINGS
    assert DEFAULT_ABP_ENCODING == "pairwise"
