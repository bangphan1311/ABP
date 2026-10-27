"""Shared validation and configuration warnings for exact ABP solvers."""
from __future__ import annotations

import math
import warnings

from src.common.models import Config, Instance

_IGNORED_FIELDS = ("memory_limit", "search_mode", "symmetry", "warm_start")


def validate_exact_input(instance: Instance, config: Config) -> None:
    """Raise ValueError for caller errors before entering solver error handling."""
    n = instance.n
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError("ABP cần ít nhất 2 đỉnh.")
    if not instance.edges:
        raise ValueError("ABP cần ít nhất một cạnh.")
    for edge in instance.edges:
        if not isinstance(edge, (tuple, list)) or len(edge) != 2:
            raise ValueError(f"Cạnh không hợp lệ: {edge!r}.")
        u, v = edge
        for endpoint in (u, v):
            if isinstance(endpoint, bool) or not isinstance(endpoint, int) or not 0 <= endpoint < n:
                raise ValueError(f"Cạnh {edge!r} chứa đỉnh không hợp lệ.")
        if u == v:
            raise ValueError(f"Cạnh tự khuyên không hợp lệ: ({u}, {v}).")
    limit = config.time_limit
    if limit is not None and (
        isinstance(limit, bool)
        or not isinstance(limit, (int, float))
        or not math.isfinite(limit)
        or limit <= 0
    ):
        raise ValueError("time_limit phải là số hữu hạn lớn hơn 0.")


def remaining_time_budget(total_limit: float | None, elapsed: float) -> float | None:
    """Return the remaining whole-run time budget after build/model construction.

    None means unlimited. elapsed is measured from the beginning of the
    solver run, rather than from the moment the optimizer starts.
    """
    if total_limit is None:
        return None
    return max(0.0, float(total_limit) - max(0.0, float(elapsed)))


def warn_ignored_config(config: Config, *, supported: tuple[str, ...] = ("seed",)) -> None:
    """Warn when a non-default shared Config field is ignored by this solver."""
    defaults = Config(method=config.method)
    ignored = [
        name for name in _IGNORED_FIELDS
        if name not in supported and getattr(config, name) != getattr(defaults, name)
    ]
    if "seed" not in supported and config.seed != defaults.seed:
        ignored.append("seed")
    if ignored:
        warnings.warn(
            "Exact solver bỏ qua các field Config: "
            + ", ".join(ignored)
            + ". memory_limit không được thực thi như hard cap; "
              "search_mode/symmetry/warm_start chưa được hỗ trợ ở exact solver.",
            UserWarning,
            stacklevel=2,
        )
