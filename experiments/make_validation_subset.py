"""Sinh validation subset cố định seed cho pilot W3 (ticket 16 / 17).

P3 chưa khóa subset chính thức, nên đây là bản tạm: 8 đồ thị random liên thông
``n = 8..28`` vào ``benchmark/validation/`` và 2 đồ thị lớn ``n = 40, 50`` vào
``benchmark/large/``. Cùng seed cho ra đúng cùng byte, nên pilot tái lập được.
Không dùng subset RQ3 (chưa tồn tại).

    python -m experiments.make_validation_subset
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

if __package__ in (None, ""):  # cho phép `python experiments/make_validation_subset.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.models import Instance
from src.sat.loader import write_instance

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = "generator"
TIER = "validation"
DEFAULT_SEED = 20261026

VALIDATION_SIZES = (8, 10, 12, 14, 16, 20, 24, 28)
LARGE_SIZES = (40, 50)
# Số cạnh mục tiêu = 2n: đủ thưa để pilot còn giải được trong time limit nhỏ.
EDGE_FACTOR = 2


def random_connected(n: int, seed: int) -> Instance:
    """Đồ thị random liên thông ``n`` đỉnh, khoảng ``2n`` cạnh, cố định theo seed.

    Dựng cây khung ngẫu nhiên trước (bảo đảm liên thông), rồi thêm cạnh ngẫu
    nhiên tới mục tiêu ``min(2n, C(n, 2))``. Cạnh trùng bị loại, thứ tự cạnh
    chuẩn hóa ``u < v`` và sắp theo cặp.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError(f"random_connected cần n >= 2: {n!r}.")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError(f"seed phải là số nguyên: {seed!r}.")

    rng = random.Random(seed)
    order = list(range(n))
    rng.shuffle(order)

    edges: set[frozenset[int]] = set()
    for i in range(1, n):  # mỗi đỉnh nối vào một đỉnh trước đó -> liên thông
        edges.add(frozenset((order[i], order[rng.randrange(i)])))

    pairs = [frozenset((u, v)) for u in range(n) for v in range(u + 1, n)]
    rng.shuffle(pairs)
    target = min(EDGE_FACTOR * n, len(pairs))
    for pair in pairs:
        if len(edges) >= target:
            break
        edges.add(pair)

    return Instance(
        id=f"randconn{n}-seed{seed}",
        name=f"Seeded random connected graph n={n} seed={seed}",
        n=n,
        edges=tuple(sorted((min(e), max(e)) for e in edges)),
        source=SOURCE,
        tier=TIER,
    )


def build_subset(seed: int = DEFAULT_SEED) -> dict[str, list[Instance]]:
    """Instance của hai nhóm, sinh lại được từ ``seed``."""
    return {
        "validation": [random_connected(n, seed) for n in VALIDATION_SIZES],
        "large": [random_connected(n, seed) for n in LARGE_SIZES],
    }


def generate_subset(
    root: str | Path = REPO_ROOT, seed: int = DEFAULT_SEED
) -> dict[str, list[Path]]:
    """Ghi subset vào ``<root>/benchmark/{validation,large}``; trả danh sách file."""
    written: dict[str, list[Path]] = {}
    for group, instances in build_subset(seed).items():
        out_dir = Path(root) / "benchmark" / group
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for instance in instances:
            path = out_dir / f"{instance.id}.json"
            write_instance(path, instance)
            paths.append(path)
        written[group] = paths
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sinh validation subset cho pilot W3.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):  # Windows redirect mặc định cp1252
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    written = generate_subset(args.root, args.seed)
    for group, paths in written.items():
        print(f"{group}: {len(paths)} instance")
        for path in paths:
            print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
