"""Demo G1 (#14): chạy pipeline SAT trên test set nhỏ, ghi kết quả theo schema Result.

Chạy từ gốc repo:  .venv\\Scripts\\python.exe docs\\handoff\\sat-g1\\run_g1.py

Mỗi instance: ghi JSON -> đọc lại bằng loader -> solve_sat (CaDiCaL) -> verify.
Đối chiếu với brute-force oracle và CP-SAT. Ghi:
  - docs/handoff/sat-g1/instances/<id>.json
  - docs/handoff/sat-g1/results.json  (mỗi phần tử: trường của CONTRACT Result + cross_check)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.common.models import Config  # noqa: E402
from src.common.verify import verify  # noqa: E402
from src.exact.cp_sat_solver import solve_cp_sat  # noqa: E402
from src.exact.oracle import solve_oracle  # noqa: E402
from src.sat import generator  # noqa: E402
from src.sat.loader import read_instance, write_instance  # noqa: E402
from src.sat.solve import solve_sat  # noqa: E402

OUT = Path(__file__).resolve().parent
TEST_SET = [
    generator.path(4),
    generator.path(8),
    generator.cycle(3),
    generator.cycle(5),
    generator.cycle(8),
    generator.grid(2, 2),
    generator.grid(2, 4),
    generator.complete(3),
    generator.complete(5),
    generator.complete(8),
]
RESULT_FIELDS = (
    "status", "lb", "ub", "gap", "t_encode", "t_solve", "t_total",
    "variables", "clauses", "peak_memory", "solution", "metadata",
)


def main() -> int:
    (OUT / "instances").mkdir(exist_ok=True)
    records = []
    failures = 0

    for generated in TEST_SET:
        path = OUT / "instances" / f"{generated.id}.json"
        write_instance(path, generated)
        instance = read_instance(path)  # đi qua loader

        result = solve_sat(instance)
        oracle = solve_oracle(instance)
        cp = solve_cp_sat(instance, Config(method="cp_sat", time_limit=30, seed=0))

        verified = verify(instance, result.solution) if result.solution else None
        match = (
            result.status == "OPT"
            and result.lb == result.ub == oracle.lb == cp.lb == verified
        )
        failures += not match

        record = {"instance_id": instance.id, "n": instance.n, "m": len(instance.edges)}
        record.update({field: getattr(result, field) for field in RESULT_FIELDS})
        record["cross_check"] = {
            "oracle_lb": oracle.lb,
            "cp_sat_lb": cp.lb,
            "verified_value": verified,
            "match": match,
        }
        records.append(record)
        print(f"{instance.id:12s} {result.status} B={result.lb} "
              f"oracle={oracle.lb} cp_sat={cp.lb} match={match}")

    (OUT / "results.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"{len(records)} instances, mismatches: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
