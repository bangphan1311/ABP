"""Sinh instance ABP Tier 0/1 (W2 ticket 11): path, cycle, grid, complete, star,
cây nhị phân, random có seed, kèm instance rời rạc và đỉnh cô lập.

Đỉnh đánh số 0..n-1; ``grid`` đánh số ``r * cols + c``.

Quy ước tier: ``tier0`` = rất nhỏ (n <= 8, có instance rời rạc và đỉnh cô lập),
``tier1`` = cấu trúc 9 <= n <= 16 và random có seed (n <= 16).
"""

from __future__ import annotations

import random

from src.common.models import Instance

SOURCE = "generator"
TIER0 = "tier0"
TIER1 = "tier1"


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


def star(m: int) -> Instance:
    """Sao K(1,m): đỉnh 0 nối với mọi đỉnh 1..m."""
    _require(m >= 1, "star cần m >= 1.")
    edges = [(0, v) for v in range(1, m + 1)]
    return _instance(f"star{m}", f"Star graph K(1,{m})", m + 1, edges)


def binary_tree(levels: int) -> Instance:
    """Cây nhị phân đầy đủ ``levels`` tầng: đỉnh i có con 2i+1, 2i+2."""
    _require(levels >= 2, "binary_tree cần levels >= 2.")
    n = 2**levels - 1
    edges = [
        (i, c) for i in range((n - 1) // 2) for c in (2 * i + 1, 2 * i + 2)
    ]
    return _instance(
        f"bintree{levels}", f"Complete binary tree with {levels} levels", n, edges
    )


def disconnected() -> Instance:
    """Đồ thị rời rạc 2 thành phần (tier0): hai path P3 không nối nhau."""
    edges = [(0, 1), (1, 2), (3, 4), (4, 5)]
    return _instance("disconnected", "Disconnected: two P3 components", 6, edges)


def isolated() -> Instance:
    """Đồ thị có đỉnh cô lập (tier0): path P4 và đỉnh 4 không có cạnh."""
    edges = [(0, 1), (1, 2), (2, 3)]
    return _instance("isolated", "Path P4 plus isolated vertex 4", 5, edges)


def random_graph(n: int, seed: int) -> Instance:
    """Đồ thị random thưa, có seed bắt buộc: chọn 2n cạnh từ mọi cặp đỉnh.

    Cùng (n, seed) cho cùng đồ thị; seed ghi trong id. n <= 16 giữ instance nhỏ.
    """
    _require(2 <= n <= 16, "random_graph cần 2 <= n <= 16.")
    rng = random.Random(seed)
    pairs = [(u, v) for u in range(n) for v in range(u + 1, n)]
    rng.shuffle(pairs)
    edges = sorted(pairs[: 2 * n])
    return _instance(
        f"random{n}-seed{seed}", f"Seeded random graph n={n} seed={seed}", n, edges
    )


def _tier(n: int) -> str:
    """Tier theo quy ước W2: n <= 8 là tier0, n >= 9 là tier1."""
    return TIER0 if n <= 8 else TIER1


def _instance(instance_id: str, name: str, n: int, edges: list[tuple[int, int]]) -> Instance:
    return Instance(
        id=instance_id,
        name=name,
        n=n,
        edges=tuple(edges),
        source=SOURCE,
        tier=_tier(n),
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
