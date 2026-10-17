"""Test encoding `pairwise`: đếm biến/clause khớp tính tay, AMO, decode, biên."""

import pytest

from src.common.verify import verify
from src.sat import generator
from src.sat.backend import SatBackend
from src.sat.pairwise import amo, build_cnf, decode_model, trivial_unsat

# path4 có 3 cạnh; n = 4.
# assignment = n + n * C(n,2) = 4 + 4*6 = 28
# permutation = 28
# distance cho mỗi cạnh = 2 * sum_{d=1..K-1} (n-d)
PATH4_ASSIGNMENT = 28
PATH4_PERMUTATION = 28


def test_variable_and_clause_counts_path4_k2():
    cnf = build_cnf(generator.path(4), 2)

    assert cnf.n == 4
    assert cnf.n_vars == 16  # n^2 biến x[v][p]
    assert cnf.stats["assignment"] == PATH4_ASSIGNMENT
    assert cnf.stats["permutation"] == PATH4_PERMUTATION
    assert cnf.stats["distance"] == 3 * 2 * (4 - 1)  # 3 cạnh, 6 cặp nhãn mỗi cạnh
    assert len(cnf.clauses) == 28 + 28 + 18
    assert cnf.n_vars == max(abs(lit) for clause in cnf.clauses for lit in clause)


def test_clause_counts_path4_k3():
    cnf = build_cnf(generator.path(4), 3)

    # distance mỗi cạnh = 2 * ((n-1) + (n-2)) = 2 * (3 + 2) = 10
    assert cnf.stats["distance"] == 3 * 10
    assert len(cnf.clauses) == 28 + 28 + 30


def test_clause_counts_path4_k1_has_no_distance_clause():
    cnf = build_cnf(generator.path(4), 1)

    assert cnf.stats["distance"] == 0
    assert len(cnf.clauses) == 28 + 28


def test_amo_pairwise_matches_hand_count():
    assert amo([1, 2, 3, 4], "pairwise") == [
        [-1, -2],
        [-1, -3],
        [-1, -4],
        [-2, -3],
        [-2, -4],
        [-3, -4],
    ]
    assert amo([1], "pairwise") == []


def test_amo_pairwise_and_seqcounter_both_forbid_two_true():
    instance = generator.path(4)

    for encoding in ("pairwise", "seqcounter"):
        cnf = build_cnf(instance, 2, amo_encoding=encoding)
        assert cnf.n_vars >= 16
        assert cnf.clauses

        with SatBackend("cadical195") as backend:
            backend.add_clauses(cnf.clauses)
            # Buộc đỉnh 0 nhận cả nhãn 1 và nhãn 2 -> phải UNSAT.
            backend.add_clauses([[cnf.var_of[(0, 1)]], [cnf.var_of[(0, 2)]]])
            assert backend.solve() == "UNSAT"

        # Đỉnh 0 nhận nhãn 2 (nhãn hợp lệ cho P4 với K=2) -> vẫn SAT.
        with SatBackend("cadical195") as backend:
            backend.add_clauses(cnf.clauses)
            backend.add_clause([cnf.var_of[(0, 2)]])
            assert backend.solve() == "SAT"
            labeling = decode_model(cnf, backend.get_model())
            assert verify(instance, labeling) >= 2


def test_distance_clauses_bite_on_infeasible_label():
    # Nhãn 1 cho đỉnh 0 của P4 là bất khả với K = 2.
    instance = generator.path(4)
    cnf = build_cnf(instance, 2)

    with SatBackend("cadical195") as backend:
        backend.add_clauses(cnf.clauses)
        backend.add_clause([cnf.var_of[(0, 1)]])
        assert backend.solve() == "UNSAT"


def test_amo_unknown_encoding_raises():
    with pytest.raises(ValueError, match="không hỗ trợ"):
        amo([1, 2], "khong-ton-tai")


def test_amo_native_encoding_is_rejected():
    with pytest.raises(ValueError, match="không hỗ trợ"):
        amo([1, 2, 3], "native")


def test_build_cnf_rejects_bad_input():
    with pytest.raises(ValueError, match="K phải"):
        build_cnf(generator.path(4), 0)

    empty = generator.path(4)
    empty.edges = ()
    with pytest.raises(ValueError, match="không có cạnh"):
        build_cnf(empty, 2)


def test_trivial_unsat_boundary():
    assert trivial_unsat(4, 4) is True
    assert trivial_unsat(4, 5) is True
    assert trivial_unsat(4, 3) is False
    with pytest.raises(ValueError, match="K phải"):
        trivial_unsat(4, 0)


def test_decode_model_builds_labeling():
    cnf = build_cnf(generator.path(4), 2)
    model = [cnf.var_of[(0, 3)], cnf.var_of[(1, 1)], cnf.var_of[(2, 4)], cnf.var_of[(3, 2)]]

    labeling = decode_model(cnf, model)

    assert labeling == {0: 3, 1: 1, 2: 4, 3: 2}


def test_decode_model_rejects_incomplete_or_duplicate_labels():
    cnf = build_cnf(generator.path(4), 2)

    with pytest.raises(ValueError, match="nhãn trong model"):
        decode_model(cnf, [cnf.var_of[(0, 1)]])

    with pytest.raises(ValueError, match="nhãn trong model"):
        # Đỉnh 0 có hai nhãn.
        decode_model(cnf, [cnf.var_of[(0, 1)], cnf.var_of[(0, 2)]])


def test_k_must_be_plain_int():
    for bad in (True, 2.0):
        with pytest.raises(TypeError):
            build_cnf(generator.path(4), bad)
        with pytest.raises(TypeError):
            trivial_unsat(4, bad)


def test_self_loop_is_rejected():
    instance = generator.path(4)
    instance.edges = ((0, 0), (0, 1))
    with pytest.raises(ValueError, match="self-loop"):
        build_cnf(instance, 2)
