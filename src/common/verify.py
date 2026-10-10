
"""Các hàm kiểm chứng nghiệm cho bài toán ABP."""

from collections.abc import Mapping

from .models import Instance


def verify(instance: Instance, labeling: Mapping[int, int]) -> int:
    """Kiểm tra labeling và trả về antibandwidth của nghiệm.

    Quy ước:
    - Đỉnh được đánh số từ 0 đến n-1.
    - Nhãn được đánh số từ 1 đến n.
    - labeling ánh xạ mỗi đỉnh tới nhãn của nó.

    Raises:
        ValueError: Nếu labeling không hợp lệ hoặc đồ thị không có cạnh.
    """
    n = instance.n
    expected_vertices = set(range(n))

    # 1. Kiểm tra đã gán nhãn đầy đủ cho các đỉnh.
    if set(labeling.keys()) != expected_vertices:
        raise ValueError(
            f"Labeling phải chứa đúng các đỉnh 0..{n - 1}."
        )

    # 2. Kiểm tra nhãn là số nguyên.
    labels = list(labeling.values())
    if any(type(label) is not int for label in labels):
        raise ValueError("Mỗi nhãn phải là một số nguyên.")

    # 3. Kiểm tra nhãn không trùng và sử dụng đúng 1..n.
    if set(labels) != set(range(1, n + 1)):
        raise ValueError(
            f"Các nhãn phải là một hoán vị của 1..{n}."
        )

    # 4. Kiểm tra các cạnh tham chiếu tới đỉnh hợp lệ.
    for u, v in instance.edges:
        if u not in expected_vertices or v not in expected_vertices:
            raise ValueError(f"Cạnh ({u}, {v}) chứa đỉnh không hợp lệ.")

    # Antibandwidth không xác định nếu đồ thị không có cạnh.
    if not instance.edges:
        raise ValueError("Không thể tính antibandwidth khi đồ thị không có cạnh.")

    # 5. Tính lại objective từ labeling và danh sách cạnh gốc.
    return min(
        abs(labeling[u] - labeling[v])
        for u, v in instance.edges
    )
