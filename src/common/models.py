
"""Các kiểu dữ liệu dùng chung trong dự án ABP."""

from dataclasses import dataclass, field
from typing import Any, Literal


Status = Literal["OPT", "FEAS", "TO", "MO", "ERR"]


@dataclass
class Instance:
    """Mô tả một đồ thị đầu vào."""
    id: str
    name: str
    n: int
    edges: tuple[tuple[int, int], ...]
    source: str
    tier: str


@dataclass
class Config:
    """Cấu hình của một lần chạy solver."""
    method: str
    abp_encoding: str | None = None
    amo_encoding: str | None = None
    sat_solver: str | None = None
    search_mode: str | None = None
    symmetry: bool = False
    warm_start: bool = False
    seed: int = 0
    time_limit: float | None = None
    memory_limit: float | None = None


@dataclass
class Result:
    """Kết quả chuẩn hóa của một lần chạy solver."""
    status: Status
    lb: int | None = None
    ub: int | None = None
    gap: float | None = None
    t_encode: float = 0.0
    t_solve: float = 0.0
    t_total: float = 0.0
    variables: int | None = None
    clauses: int | None = None
    peak_memory: float | None = None
    solution: dict[int, int] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
