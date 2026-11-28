"""Validate raw run JSON records and export the selected rows to runs.csv."""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.runner.schema import RUN_FIELDS

STATUSES = {"OPT", "FEAS", "TO", "MO", "ERR"}


def load_records(raw_dir: Path) -> list[dict]:
    rows = []
    for path in sorted(raw_dir.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError(f"{path.name}: record is not an object")
        missing = set(RUN_FIELDS) - set(record)
        if missing:
            raise ValueError(f"{path.name}: missing fields {sorted(missing)}")
        if record.get("status") not in STATUSES:
            raise ValueError(f"{path.name}: unexpected status {record.get('status')!r}")
        rows.append(record)
    run_ids = [r["run_id"] for r in rows]
    if len(run_ids) != len(set(run_ids)):
        raise ValueError("duplicate run_id in raw records")
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-dir", type=Path, default=ROOT / "results/rq3_official")
    p.add_argument("--output", type=Path, default=ROOT / "results/runs.csv")
    p.add_argument("--expected-runs", type=int)
    a = p.parse_args()

    try:
        rows = load_records(a.raw_dir)
        if a.expected_runs is not None and len(rows) != a.expected_runs:
            raise ValueError(f"expected {a.expected_runs} records, found {len(rows)}")
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    rows.sort(key=lambda r: (r["instance"], r["method"]))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RUN_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"# runs={len(rows)} status={counts} -> {a.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
