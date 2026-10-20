"""Encoding ``order`` cho bài toán ABP.

Biến: ``o[v][p] = 1`` khi nhãn của đỉnh ``v`` (0-based) **≤ p** với
``p ∈ 1..n-1``; ``o[v][p]`` có id ``v * (n - 1) + p``. Biên ``p = 0`` luôn sai,
``p = n`` luôn đúng nên không cần biến. Nhãn ``f(v) = min{p : o[v][p] = 1}``,
hoặc ``n`` khi cả chuỗi bằng 0 — mỗi cách gán chuỗi đơn điệu cho đúng một nhãn.
Bốn nhóm ràng buộc (cùng nhóm với ``src/sat/pairwise.py``):

1. ``assignment``  — mỗi đỉnh nhận đúng một nhãn: chỉ là chuỗi suy luận
   ``o[v][p] → o[v][p+1]`` (chuỗi đơn điệu thay ALO + AMO của pairwise).
2. ``permutation`` — mỗi nhãn dùng đúng một đỉnh: cấm hai đỉnh cùng nhận
   nhãn ``q`` với mọi cặp đỉnh ``u < w`` (mệnh đề "``f(u) ≠ q`` hoặc
   ``f(w) ≠ q``"). n nhãn đôi một khác nhau trong ``1..n`` thì tự thành hoán vị.
3. ``distance``    — với mọi cạnh ``(u, v)`` và mọi cặp nhãn ``p != q`` mà
   ``|p - q| < K``: "``f(u) ≠ p`` hoặc ``f(v) ≠ q``" (no-good trên nhãn).
4. ``threshold``   — như pairwise: ``K >= n`` chốt UNSAT bởi ``trivial_unsat``
   trước khi dựng CNF (xem ``src/sat/solve.py``), không sinh clause.

Encoding order không có ràng buộc at-most-one nào (chuỗi suy luận thay AMO),
nên ``amo_encoding`` được ghi nhận trong ``CNF`` cho metadata nhưng không đổi
clause — đổi AMO không đổi kết quả (yêu cầu của ticket 05).
"""

from __future__ import annotations

from itertools import combinations
from typing import Sequence

from src.common.models import Instance
from src.sat.pairwise import CNF, DEFAULT_AMO_ENCODING, _check_k


def _not_value(
    var_of: dict[tuple[int, int], int], n: int, v: int, q: int
) -> list[int]:
    """Các literal mà disjunction đúng ⟺ ``f(v) != q``.

    ``f(v) != q`` nghĩa là ``f(v) <= q - 1`` hoặc ``f(v) >= q + 1``; hai biên
    ``q = 1`` và ``q = n`` rút gọn còn một literal.
    """
    if q == 1:
        return [-var_of[(v, 1)]]  # f(v) >= 2
    if q == n:
        return [var_of[(v, n - 1)]]  # f(v) <= n - 1
    return [-var_of[(v, q)], var_of[(v, q - 1)]]


def build_cnf(
    instance: Instance, k: int, amo_encoding: str = DEFAULT_AMO_ENCODING
) -> CNF:
    """Dựng CNF order cho bài toán quyết định ABP với ngưỡng ``k``."""
    n = instance.n

    if n < 1:
        raise ValueError("Đồ thị phải có ít nhất một đỉnh.")
    if not instance.edges:
        raise ValueError("ABP không xác định khi đồ thị không có cạnh.")
    if any(u == v for u, v in instance.edges):
        raise ValueError("self-loop (u, u) is not allowed.")
    _check_k(k)

    var_of = {(v, p): v * (n - 1) + p for v in range(n) for p in range(1, n)}

    assignment: list[list[int]] = []
    for v in range(n):
        for p in range(1, n - 1):
            assignment.append([-var_of[(v, p)], var_of[(v, p + 1)]])

    permutation: list[list[int]] = []
    for u, w in combinations(range(n), 2):
        for q in range(1, n + 1):
            permutation.append(_not_value(var_of, n, u, q) + _not_value(var_of, n, w, q))

    distance: list[list[int]] = []
    for u, v in instance.edges:
        for p in range(1, n + 1):
            for q in range(max(1, p - k + 1), min(n, p + k - 1) + 1):
                if p == q:
                    continue
                distance.append(_not_value(var_of, n, u, p) + _not_value(var_of, n, v, q))

    clauses = assignment + permutation + distance
    n_vars = max(abs(literal) for clause in clauses for literal in clause)

    return CNF(
        n=n,
        k=k,
        n_vars=n_vars,
        clauses=clauses,
        var_of=var_of,
        stats={
            "assignment": len(assignment),
            "permutation": len(permutation),
            "distance": len(distance),
        },
        amo_encoding=amo_encoding,
    )


def decode_model(cnf: CNF, model: Sequence[int]) -> dict[int, int]:
    """Biến model của solver thành labeling đỉnh -> nhãn.

    Nhãn của ``v`` là ``p`` nhỏ nhất với ``o[v][p] = 1``; cả chuỗi bằng 0 thì
    nhãn là ``n``.

    Raises:
        ValueError: Nếu model không phải hoán vị hợp lệ (encoding sai).
    """
    if model is None:
        raise ValueError("Không có model để decode.")

    positive = {literal for literal in model if literal > 0}
    labeling: dict[int, int] = {}

    for v in range(cnf.n):
        labeling[v] = next(
            (p for p in range(1, cnf.n) if cnf.var_of[(v, p)] in positive), cnf.n
        )

    if sorted(labeling.values()) != list(range(1, cnf.n + 1)):
        raise ValueError("Nhãn trong model không phải hoán vị của 1..n.")

    return labeling
