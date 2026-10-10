
"""Oracle brute-force cho các đồ thị ABP rất nhỏ.

Oracle chỉ dùng để kiểm thử tính đúng đắn của solver khác.
"""

from itertools import permutations
from math import factorial
from time import perf_counter

from src.common.models import Instance, Result
from src.common.verify import verify


def solve_oracle(instance: Instance, max_n: int = 9) -> Result:
    """Duyệt mọi labeling để tìm antibandwidth tối ưu."""

    n = instance.n

    if n < 1:
        raise ValueError("Đồ thị phải có ít nhất một đỉnh.")

    if n > max_n:
        raise ValueError(
            f"Oracle chỉ hỗ trợ tối đa {max_n} đỉnh; "
            f"đồ thị hiện có {n} đỉnh."
        )

    if not instance.edges:
        raise ValueError("Oracle không xử lý đồ thị không có cạnh.")

    start = perf_counter()

    best_objective = -1
    best_labeling = None
    labelings_checked = 0

    # Mỗi hoán vị gán các nhãn 1..n cho n đỉnh.
    for labels in permutations(range(1, n + 1)):
        labeling = dict(enumerate(labels))
        objective = verify(instance, labeling)
        labelings_checked += 1

        if objective > best_objective:
            best_objective = objective
            best_labeling = labeling

    elapsed = perf_counter() - start

    return Result(
        status="OPT",
        lb=best_objective,
        ub=best_objective,
        gap=0.0,
        t_encode=0.0,
        t_solve=elapsed,
        t_total=elapsed,
        solution=best_labeling,
        metadata={
            "method": "brute_force_oracle",
            "labelings_checked": labelings_checked,
            "expected_labelings": factorial(n),
        },
    )
