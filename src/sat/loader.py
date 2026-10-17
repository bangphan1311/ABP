"""Đọc/ghi instance ABP ở dạng JSON (format tối thiểu cho W1).

Schema:

```json
{
  "id": "path4",
  "name": "Path graph with 4 vertices",
  "n": 4,
  "edges": [[0, 1], [1, 2], [2, 3]],
  "source": "generator",
  "tier": "toy"
}
```

Trường lạ bị bỏ qua; trường bắt buộc thiếu hoặc sai kiểu thì báo lỗi.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.common.models import Instance

REQUIRED_KEYS = ("id", "name", "n", "edges", "source", "tier")
STRING_KEYS = ("id", "name", "source", "tier")


def write_instance(path: str | Path, instance: Instance) -> None:
    """Ghi instance ra file JSON (cạnh giữ nguyên thứ tự)."""
    payload = {
        "id": instance.id,
        "name": instance.name,
        "n": instance.n,
        "edges": [[u, v] for u, v in instance.edges],
        "source": instance.source,
        "tier": instance.tier,
    }
    Path(path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def read_instance(path: str | Path) -> Instance:
    """Đọc instance từ file JSON, có kiểm tra biên.

    Raises:
        ValueError: Nếu file thiếu trường, sai kiểu, hoặc cạnh không hợp lệ.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise ValueError("Instance phải là một object JSON.")

    missing = [key for key in REQUIRED_KEYS if key not in raw]
    if missing:
        raise ValueError(f"Instance thiếu trường: {', '.join(missing)}.")

    for key in STRING_KEYS:
        if not isinstance(raw[key], str):
            raise ValueError(f"Trường '{key}' phải là chuỗi.")

    n = raw["n"]
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError("Trường 'n' phải là số nguyên >= 0.")

    raw_edges = raw["edges"]
    if not isinstance(raw_edges, list):
        raise ValueError("Trường 'edges' phải là danh sách.")

    edges: list[tuple[int, int]] = []
    seen: set[frozenset[int]] = set()
    for edge in raw_edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise ValueError(f"Cạnh phải là cặp [u, v]: {edge!r}.")
        u, v = edge
        for endpoint in (u, v):
            if isinstance(endpoint, bool) or not isinstance(endpoint, int):
                raise ValueError(f"Đỉnh trong cạnh phải là số nguyên: {edge!r}.")
            if not 0 <= endpoint < n:
                raise ValueError(f"Cạnh {edge!r} ngoài khoảng đỉnh 0..{n - 1}.")
        if u == v:
            raise ValueError(f"Cạnh tự khuyên {edge!r} không hợp lệ.")
        key = frozenset((u, v))  # {u, v} == {v, u}: keep one edge
        if key not in seen:
            seen.add(key)
            edges.append((u, v))

    if n == 0 or not edges:
        raise ValueError("Instance is empty (n = 0 or no edges).")

    return Instance(
        id=raw["id"],
        name=raw["name"],
        n=n,
        edges=tuple(edges),
        source=raw["source"],
        tier=raw["tier"],
    )
