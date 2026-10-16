"""Encoding ``pairwise`` cho bài toán ABP.

Biến: ``x[v][p] = 1`` khi đỉnh ``v`` (0-based) nhận nhãn ``p`` (1..n),
``x[v][p]`` có id ``v * n + p``. Bốn nhóm ràng buộc:

1. ``assignment``  — mỗi đỉnh nhận đúng một nhãn.
2. ``permutation`` — mỗi nhãn được gán cho đúng một đỉnh.
3. ``distance``    — với mọi cạnh ``(u, v)`` và mọi cặp nhãn ``p != q`` mà
   ``|p - q| < K``: ``¬x[u][p] ∨ ¬x[v][q]``.
4. ``threshold``   — ngưỡng ``K`` do bên gọi chọn; trường hợp tầm thường
   ``K >= n`` là UNSAT do lệch nhãn lớn nhất chỉ là ``n - 1``
   (xem ``trivial_unsat``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Sequence

from src.common.models import Instance
from src.sat.backend import atmost_one_encoding, new_id_pool

DEFAULT_ABP_ENCODING = "pairwise"
DEFAULT_AMO_ENCODING = "pairwise"

# Các encoding AMO lấy từ pysat.card; "native" bị loại vì cần CNFPlus.
SUPPORTED_AMO_ENCODINGS = (
    "pairwise",
    "seqcounter",
    "cardnetwrk",
    "totalizer",
    "mtotalizer",
    "kmtotalizer",
    "bitwise",
    "ladder",
    "sortnetwrk",
)


@dataclass
class CNF:
    """CNF đã dựng cho một ngưỡng K, kèm ánh xạ biến để decode."""

    n: int
    k: int
    n_vars: int
    clauses: list[list[int]]
    var_of: dict[tuple[int, int], int]
    stats: dict[str, int] = field(default_factory=dict)
    amo_encoding: str = DEFAULT_AMO_ENCODING


def amo(
    literals: Sequence[int],
    encoding: str = DEFAULT_AMO_ENCODING,
    pool: IDPool | None = None,
) -> list[list[int]]:
    """Ràng buộc at-most-one trên ``literals``, trả về danh sách clause."""
    lits = list(literals)

    if len(lits) < 2:
        return []

    if encoding == "pairwise":
        return [[-a, -b] for a, b in combinations(lits, 2)]

    if encoding not in SUPPORTED_AMO_ENCODINGS:
        raise ValueError(
            f"amo_encoding '{encoding}' không hỗ trợ; "
            f"chọn một trong {', '.join(SUPPORTED_AMO_ENCODINGS)}."
        )

    cnf = atmost_one_encoding(lits, encoding, pool)
    # Ràng buộc native không nằm trong clause -> sẽ mất ràng buộc nếu bỏ qua.
    if getattr(cnf, "atmosts", ()):
        raise ValueError(f"amo_encoding '{encoding}' trả ràng buộc native, chưa hỗ trợ.")

    return [list(clause) for clause in cnf.clauses]


def _check_k(k: int) -> None:
    """K phải là int (không phải bool) với K >= 1."""
    if isinstance(k, bool) or not isinstance(k, int):
        raise TypeError(f"K must be int, not {type(k).__name__}: {k!r}.")
    if k < 1:
        raise ValueError("K phải >= 1.")


def trivial_unsat(n: int, k: int) -> bool:
    """Nhóm ràng buộc 4: ``K >= n`` là UNSAT vì lệch nhãn tối đa là ``n - 1``."""
    _check_k(k)
    return k >= n


def build_cnf(
    instance: Instance, k: int, amo_encoding: str = DEFAULT_AMO_ENCODING
) -> CNF:
    """Dựng CNF cho bài toán quyết định ABP với ngưỡng ``k``."""
    n = instance.n

    if n < 1:
        raise ValueError("Đồ thị phải có ít nhất một đỉnh.")
    if not instance.edges:
        raise ValueError("ABP không xác định khi đồ thị không có cạnh.")
    if any(u == v for u, v in instance.edges):
        raise ValueError("self-loop (u, u) is not allowed.")
    _check_k(k)

    var_of = {(v, p): v * n + p for v in range(n) for p in range(1, n + 1)}
    # Aux var của pysat.card bắt đầu sau vùng biến chính -> không đè id.
    pool = new_id_pool(start_from=n * n + 1)

    assignment: list[list[int]] = []
    for v in range(n):
        lits = [var_of[(v, p)] for p in range(1, n + 1)]
        assignment.append(lits)  # ít nhất một nhãn
        assignment.extend(amo(lits, amo_encoding, pool))

    permutation: list[list[int]] = []
    for p in range(1, n + 1):
        lits = [var_of[(v, p)] for v in range(n)]
        permutation.append(lits)  # ít nhất một đỉnh
        permutation.extend(amo(lits, amo_encoding, pool))

    distance: list[list[int]] = []
    for u, v in instance.edges:
        for p in range(1, n + 1):
            for q in range(max(1, p - k + 1), min(n, p + k - 1) + 1):
                if p == q:
                    continue
                distance.append([-var_of[(u, p)], -var_of[(v, q)]])

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

    Raises:
        ValueError: Nếu model không phải hoán vị hợp lệ (encoding sai).
    """
    if model is None:
        raise ValueError("Không có model để decode.")

    positive = {literal for literal in model if literal > 0}
    labeling: dict[int, int] = {}

    for v in range(cnf.n):
        chosen = [p for p in range(1, cnf.n + 1) if cnf.var_of[(v, p)] in positive]
        if len(chosen) != 1:
            raise ValueError(f"Đỉnh {v} có {len(chosen)} nhãn trong model.")
        labeling[v] = chosen[0]

    if set(labeling.values()) != set(range(1, cnf.n + 1)):
        raise ValueError("Nhãn trong model không phải hoán vị của 1..n.")

    return labeling
