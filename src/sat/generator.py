"""Sinh instance ABP nhỏ (toy): path, cycle, grid, complete.

Đỉnh đánh số 0..n-1; ``grid`` đánh số ``r * cols + c``.
"""

from __future__ import annotations

from src.common.models import Instance

SOURCE = "generator"
TIER = "toy"


def path(n: int) -> Instance:
    """Đường đi P_n: cạnh (i, i+1) với i = 0..n-2."""
    _require(n >= 2, "path cần n >= 2.")
    return _instance(f"path{n}", f"Path graph with {n} vertices", n,
                     [(i, i + 1) for i in range(n - 1)])


def cycle(n: int) -> Instance:
    """Chu trình C_n: P_n cộng cạnh (n-1, 0)."""
    _require(n >= 3, "cycle cần n >= 3.")
    edges = [(i, i + 1) for i in range(n - 1)] + [(n - 1, 0)]
    return _instance(f"cycle{n}", f"Cycle graph with {n} vertices", n, edges)


def grid(rows: int, cols: int) -> Instance:
    """Lưới rows x cols: đỉnh (r, c) có id r * cols + c."""
    _require(rows >= 2 and cols >= 2, "grid cần rows >= 2 và cols >= 2.")
    edges: list[tuple[int, int]] = []
    for r in range(rows):
        for c in range(cols):
            v = r * cols + c
            if c + 1 < cols:
                edges.append((v, v + 1))
            if r + 1 < rows:
                edges.append((v, v + cols))
    n = rows * cols
    return _instance(f"grid{rows}x{cols}", f"Grid graph {rows}x{cols}", n, edges)


def complete(n: int) -> Instance:
    """Đồ thị đầy đủ K_n: mọi cặp đỉnh đều có cạnh."""
    _require(n >= 2, "complete cần n >= 2.")
    edges = [(u, v) for u in range(n) for v in range(u + 1, n)]
    return _instance(f"complete{n}", f"Complete graph with {n} vertices", n, edges)


def _instance(instance_id: str, name: str, n: int, edges: list[tuple[int, int]]) -> Instance:
    return Instance(
        id=instance_id,
        name=name,
        n=n,
        edges=tuple(edges),
        source=SOURCE,
        tier=TIER,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)