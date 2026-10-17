"""Worker: chạy MỘT solver trên MỘT instance trong subprocess riêng.

    python -m src.runner.worker <instance.json> <config.json> <out.json>

Ghi Result ra ``out.json`` (không dùng stdout vì solver hay in log).
Mọi exception -> status ERR kèm thông điệp lỗi, không làm crash runner.
"""

from __future__ import annotations

import json
import sys
import traceback
from dataclasses import asdict
from pathlib import Path

from src.common.models import Config
from src.runner.registry import resolve
from src.sat.loader import read_instance


def main(argv: list[str]) -> int:
    instance_path, config_path, out_path = argv
    out: dict
    try:
        instance = read_instance(instance_path)
        config = Config(**json.loads(Path(config_path).read_text(encoding="utf-8")))
        result = resolve(config.method)(instance, config)
        payload = asdict(result)
        payload["solution"] = (
            {str(k): v for k, v in result.solution.items()} if result.solution else None
        )
        out = {"ok": True, "result": payload}
    except MemoryError:
        out = {"ok": True, "result": {"status": "MO"}, "note": "MemoryError"}
    except Exception as exc:  # license, input hỏng, bug solver...
        out = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=5),
        }
    Path(out_path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
