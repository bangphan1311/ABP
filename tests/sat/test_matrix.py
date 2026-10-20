"""Matrix test W2 (ticket 12): encoding × AMO × backend khớp oracle trên mọi cấu hình.

Ma trận Core (ruling controller): abp_encoding ∈ {pairwise, order} × amo_encoding ∈
{pairwise, seqcounter} × sat_solver ∈ {cadical195, glucose4} = 8 cấu hình.
Kissat N/A vĩnh viễn W2 — bị chặn ở backend và pipeline
(`tests/sat/test_backend.py`, `tests/sat/test_solve.py`; `docs/sat_tooling.md`
mục Kissat) nên không chạy trong matrix.

Lưu ý order encoding không có ràng buộc at-most-one (chuỗi đơn điệu thay AMO):
``amo_encoding`` vẫn được ghi nhận trong CNF, kết quả không đổi; matrix vẫn chạy
đủ 2 giá trị AMO cho order để khẳng định đường config hoạt động.

Mỗi cấu hình kiểm qua API công khai: (1) OPT khớp oracle brute-force, (2)
SAT/UNSAT tại mọi K ∈ 1..n khớp oracle, (3) nghiệm SAT qua verify(). Riêng ticket
08 closure: contract ``amo()`` kiểm exhaustive trên mọi tập con của 6 literal.
"""

from itertools import permutations

import pytest

from src.common.models import Config
from src.common.verify import verify
from src.exact.oracle import solve_oracle
from src.sat import generator, order, pairwise
from src.sat.backend import DEFAULT_SOLVER, SatBackend, new_id_pool
from src.sat.pairwise import amo
from src.sat.solve import solve_decision, solve_sat

# Toy W1 + tier0 họ T3 (star, binary tree, grid) + edge case rời rạc / đỉnh
# cô lập + random có seed. Toàn bộ n <= 9 để chạy được oracle brute-force
# (grid3x3 là toy W1, n = 9 = giới hạn oracle).
MATRIX_INSTANCES = [
    generator.path(4),
    generator.cycle(5),
    generator.grid(3, 3),
    generator.complete(5),
    generator.star(6),
    generator.binary_tree(3),
    generator.grid(2, 3),
    generator.disconnected(),
    generator.isolated(),
    generator.random_graph(8, 42),
]

# Tier 1 n <= 12, chỉ chạy cấu hình mặc định (brief): oracle brute-force giới
# hạn n <= 9 nên ở đây OPT được chứng minh bằng UNSAT của solver (tự chứng
# minh), nghiệm qua verify(), và hai encoding phải cùng B.
TIER1_INSTANCES = [
    generator.path(10),
    generator.grid(3, 4),
    generator.random_graph(12, 42),
]

# 2 × 2 × 2 = 8 cấu hình Core.
CONFIGS = [
    Config(method="sat", abp_encoding=abp, amo_encoding=amo_enc, sat_solver=solver)
    for abp in ("pairwise", "order")
    for amo_enc in ("pairwise", "seqcounter")
    for solver in ("cadical195", "glucose4")
]
CONFIG_IDS = [f"{c.abp_encoding}-{c.amo_encoding}-{c.sat_solver}" for c in CONFIGS]

# Instance cực nhỏ (n <= 6) để đếm model: SAT có nghiệm ít, và cả UNSAT (0).
COUNT_PAIRS = [
    (generator.path(4), 2),
    (generator.path(4), 3),  # UNSAT: B(path4) = 2
    (generator.cycle(5), 2),
    (generator.cycle(5), 3),  # UNSAT: B(cycle5) = 2
    (generator.disconnected(), 3),
    (generator.isolated(), 3),
]
COUNT_PAIR_IDS = [f"{g.id}-K{k}" for g, k in COUNT_PAIRS]

# Ticket 08: tập literal gốc để duyệt mọi tập con, n = 6.
AMO_BASE = [1, 2, 3, 4, 5, 6]

_B_OPT: dict[str, int] = {}


def b_opt(instance):
    """B tối ưu theo oracle brute-force, cache theo id (brute chỉ chạy 1 lần)."""
    if instance.id not in _B_OPT:
        _B_OPT[instance.id] = solve_oracle(instance).lb
    return _B_OPT[instance.id]


def _cid(config) -> str:
    return f"{config.abp_encoding}-{config.amo_encoding}-{config.sat_solver}"


@pytest.mark.parametrize("config", CONFIGS, ids=CONFIG_IDS)
@pytest.mark.parametrize("instance", MATRIX_INSTANCES, ids=lambda g: g.id)
def test_matrix_solve_sat_matches_oracle(instance, config):
    result = solve_sat(instance, config)
    expected = b_opt(instance)

    assert result.status == "OPT", (instance.id, _cid(config), result.metadata.get("error"))
    assert result.lb == result.ub == expected, (instance.id, _cid(config))
    assert verify(instance, result.solution) == expected, (instance.id, _cid(config))


@pytest.mark.parametrize("config", CONFIGS, ids=CONFIG_IDS)
@pytest.mark.parametrize("instance", MATRIX_INSTANCES, ids=lambda g: g.id)
def test_matrix_decision_matches_oracle_at_every_k(instance, config):
    expected = b_opt(instance)

    for k in range(1, instance.n + 1):
        status, labeling = solve_decision(instance, k, config)
        assert status == ("SAT" if k <= expected else "UNSAT"), (
            instance.id, k, _cid(config)
        )
        if status == "SAT":
            assert verify(instance, labeling) >= k, (instance.id, k, _cid(config))


def brute_count(instance, k):
    """Đếm trực tiếp số hoán vị 1..n thỏa mọi cạnh |f(u) - f(v)| >= k."""
    n = instance.n
    return sum(
        1
        for labels in permutations(range(1, n + 1))
        if all(abs(labels[u] - labels[v]) >= k for u, v in instance.edges)
    )


def count_by_blocking(instance, k, config):
    """Đếm nghiệm qua SatBackend như pipeline: giải, chặn model, giải lại.

    Blocking clause chặn trên các biến chính (``var_of``): một nghiệm = một
    hoán vị. Biến phụ (seqcounter) tự do nên cùng một hoán vị không bị đếm
    nhiều lần, và mỗi vòng luôn ra hoán vị mới cho tới UNSAT.
    """
    if config.abp_encoding == "order":
        build, decode = order.build_cnf, order.decode_model
    else:
        build, decode = pairwise.build_cnf, pairwise.decode_model

    amo_enc = config.amo_encoding or pairwise.DEFAULT_AMO_ENCODING
    cnf = build(instance, k, amo_encoding=amo_enc)
    primary = set(cnf.var_of.values())

    count = 0
    with SatBackend(config.sat_solver) as backend:
        backend.add_clauses(cnf.clauses)
        while backend.solve() == "SAT":
            model = backend.get_model()
            labeling = decode(cnf, model)
            assert verify(instance, labeling) >= k, (instance.id, k, _cid(config))
            backend.add_clause([-lit for lit in model if lit > 0 and lit in primary])
            count += 1
    return count


@pytest.mark.parametrize("config", CONFIGS, ids=CONFIG_IDS)
@pytest.mark.parametrize("instance, k", COUNT_PAIRS, ids=COUNT_PAIR_IDS)
def test_matrix_model_count_by_blocking_matches_permutations(instance, k, config):
    """Không thừa, không thiếu nghiệm: đếm blocking == đếm itertools (n <= 6).

    Chạy ở cả pairwise và order nên cùng bảng đếm phải bằng nhau ở mọi cấu hình.
    """
    assert count_by_blocking(instance, k, config) == brute_count(instance, k), (
        instance.id, k, _cid(config)
    )


@pytest.mark.parametrize("amo_encoding", ["pairwise", "seqcounter"])
def test_amo_exhaustive_closure_over_all_subsets(amo_encoding):
    """Ticket 08 closure: contract ``amo()`` kiểm exhaustive mọi tập con.

    Với mọi tập con của 6 literal và mọi assignment: assignment có <= 1 literal
    true phải thỏa toàn bộ clause AMO (CNF + assignment còn SAT), assignment
    có > 1 literal true phải bị chặn (UNSAT). Kiểm qua backend vì seqcounter
    sinh biến phụ: "thỏa toàn bộ clause" nghĩa là tồn tại cách gán biến phụ
    thỏa mọi clause đồng thời — semantics chuẩn của encoding AMO.
    """
    pool = new_id_pool(start_from=max(AMO_BASE) + 1)  # biến phụ không đè literal gốc

    for mask in range(2 ** len(AMO_BASE)):
        lits = [lit for i, lit in enumerate(AMO_BASE) if mask >> i & 1]
        clauses = amo(lits, amo_encoding, pool)
        if len(lits) < 2:
            assert clauses == []

        for bits in range(2 ** len(lits)):
            expected = "SAT" if sum(bits >> i & 1 for i in range(len(lits))) <= 1 else "UNSAT"
            with SatBackend(DEFAULT_SOLVER) as backend:
                backend.add_clauses(clauses)
                for i, lit in enumerate(lits):
                    backend.add_clause([lit] if bits >> i & 1 else [-lit])
                status = backend.solve()
            assert status == expected, (amo_encoding, lits, bits)


@pytest.mark.parametrize("instance", TIER1_INSTANCES, ids=lambda g: g.id)
def test_matrix_tier1_default_config_proves_optimum(instance):
    """Tier 1 (n <= 12) chỉ chạy cấu hình mặc định theo brief.

    OPT được chứng minh bằng UNSAT tại K = B + 1 (bằng chứng của solver),
    nghiệm qua verify(), và order encoding phải cho cùng B — hai encoding
    cùng giải một bài toán quyết định nên khác nhau là lỗi encoding.
    """
    default = Config(method="sat")  # pairwise + pairwise + cadical195
    order_cfg = Config(method="sat", abp_encoding="order")

    result = solve_sat(instance, default)
    order_result = solve_sat(instance, order_cfg)

    assert result.status == "OPT", (instance.id, result.metadata.get("error"))
    assert result.lb == result.ub, instance.id
    assert verify(instance, result.solution) == result.lb, instance.id
    assert order_result.status == "OPT", (
        instance.id, order_result.metadata.get("error")
    )
    assert order_result.lb == result.lb, instance.id
