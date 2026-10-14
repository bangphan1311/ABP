import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
"""Sinh vài instance toy vào benchmark/toy/ để chạy thử runner."""

from pathlib import Path

from src.sat import generator
from src.sat.loader import write_instance

OUT = Path(__file__).resolve().parents[1] / "benchmark" / "toy"
OUT.mkdir(parents=True, exist_ok=True)
for inst in (generator.path(4), generator.cycle(5), generator.grid(3, 3), generator.complete(5)):
    write_instance(OUT / f"{inst.id}.json", inst)
    print("wrote", OUT / f"{inst.id}.json")
