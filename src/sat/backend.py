"""Backend SAT: lớp mỏng bọc PySAT, dùng chung cho mọi encoding ABP.

Chỉ nơi này được biết tới PySAT. Tầng trên (encoding, pipeline) chỉ thấy
``SatBackend`` với ``add_clause`` / ``add_clauses`` / ``solve`` / ``get_model`` /
``status``.
"""

from __future__ import annotations

from threading import Event, Thread
from time import monotonic
from typing import Iterable, Literal, Sequence

from pysat.solvers import Solver, SolverNames

SolveStatus = Literal["SAT", "UNSAT", "UNKNOWN"]

DEFAULT_SOLVER = "cadical195"

# Family solver (theo tên thuộc tính của SolverNames) hỗ trợ interrupt() -> timeout
# chính xác theo đồng hồ. Kiểm tra bằng cách đọc mã nguồn pysat.solvers.
INTERRUPTIBLE_FAMILIES = frozenset(
    {
        "glucose3",
        "glucose4",
        "glucose42",
        "gluecard3",
        "gluecard4",
        "minisat22",
        "minisatgh",
        "minisatep",
        "maplesat",
        "maplechrono",
        "maplecm",
        "mergesat3",
    }
)

# Family chỉ có conf_budget() (CaDiCaL): interrupt() ném NotImplementedError.
# Timeout thực hiện bằng vòng lặp ngân sách xung đột tăng dần (xem docs/sat_tooling.md).
# Kissat KHÔNG nằm ở đây: family kissat404 của PySAT crash khi nạp clause, đi qua
# binary ngoài ở src/sat/kissat.py (xem docs/sat_tooling.md mục 7).
BUDGETED_FAMILIES = frozenset({"cadical103", "cadical153", "cadical195", "cadical300"})

# Family Kissat trong PySAT 1.9.dev15: access violation khi nạp clause (giết process).
# Chặn ngay trong add_clause thay vì để native crash.
PYSAT_KISSAT_FAMILIES = frozenset({"kissat404"})

# Ngân sách xung đột khởi điểm cho mỗi lần gọi solve_limited; tăng gấp đôi mỗi vòng.
CONFLICT_BUDGET_START = 1000

# Tên solver gợi ý cho người dùng: tất cả đều dựng được bằng Solver(name=...) và
# nạp được clause trên PySAT 1.9.dev15. Lưu ý 'minisat-gh' phải gọi qua alias 'mgh'.
# 'kissat' cố ý KHÔNG có mặt: family kissat404 của PySAT crash process khi nạp clause
# (xem docs/sat_tooling.md mục 7); dùng binary ngoài qua src/sat/kissat.py.
SUPPORTED_SOLVERS = (
    "cadical103",
    "cadical153",
    "cadical195",
    "cadical300",
    "glucose3",
    "glucose4",
    "glucose42",
    "gluecard3",
    "gluecard4",
    "mgh",
    "minisat22",
    "minisatep",
    "maplesat",
    "maplechrono",
    "maplecm",
    "mergesat3",
)


class BackendError(RuntimeError):
    """Lỗi khởi tạo/điều khiển backend SAT (pipeline map sang status ERR)."""


def validate_clause(clause: Sequence[int]) -> list[int]:
    """Chuẩn hóa và kiểm tra một clause; dùng chung cho mọi backend.

    Raises:
        ValueError: Nếu clause rỗng, hoặc có literal ``0`` / không phải ``int``.
    """
    literals = list(clause)

    if not literals:
        raise ValueError("Clause rỗng không hợp lệ.")
    for literal in literals:
        if isinstance(literal, bool) or not isinstance(literal, int):
            raise ValueError(f"Literal phải là số nguyên khác 0: {literal!r}.")
        if literal == 0:
            raise ValueError("Literal 0 không hợp lệ.")

    return literals


def solver_family(solver_name: str) -> str:
    """Family của một tên/alias solver (``g4`` -> ``glucose4``)."""
    name = solver_name.lower()
    for family, aliases in vars(SolverNames).items():
        if family.startswith("_"):
            continue
        if name == family or (isinstance(aliases, tuple) and name in aliases):
            return family
    return name


def supported_solvers() -> tuple[str, ...]:
    """Tên solver gợi ý, tất cả đều nạp được clause và giới hạn được thời gian.

    Không gồm ``kissat``: family của PySAT crash process khi nạp clause. Kissat đi qua
    binary ngoài (``src/sat/kissat.py``) với ``Config(sat_solver='kissat')`` — xem
    ``docs/sat_tooling.md`` mục 7.
    """
    return SUPPORTED_SOLVERS


class SatBackend:
    """Bọc một solver PySAT: nạp CNF, giải có/không giới hạn thời gian, lấy model."""

    def __init__(self, solver_name: str | None = None, use_timer: bool = False):
        self.solver_name = (solver_name or DEFAULT_SOLVER).lower()
        self.family = solver_family(self.solver_name)

        try:
            self._solver = Solver(name=self.solver_name, use_timer=use_timer)
        except Exception as exc:  # tên sai, build native hỏng hoặc lỗi giấy phép -> ERR
            raise BackendError(
                f"Không khởi tạo được solver '{self.solver_name}': {exc}"
            ) from exc

        self._status: SolveStatus = "UNKNOWN"
        self._solve_time = 0.0
        # nof_clauses() chỉ là số clause trong header DIMACS -> tự đếm khi thêm.
        self._n_clauses = 0

    # --- trạng thái -----------------------------------------------------

    @property
    def status(self) -> SolveStatus:
        """Kết quả của lần gọi ``solve`` gần nhất."""
        return self._status

    @property
    def solve_time(self) -> float:
        """Thời gian (giây) của lần gọi ``solve`` gần nhất."""
        return self._solve_time

    @property
    def io_time(self) -> float:
        """Thời gian I/O ngoài ``solve``; PySAT nạp clause ở ``add_clauses`` nên là ``0.0``."""
        return 0.0

    @property
    def n_vars(self) -> int:
        return self._solver.nof_vars()

    @property
    def n_clauses(self) -> int:
        return self._n_clauses

    # --- nạp CNF --------------------------------------------------------

    def add_clause(self, clause: Sequence[int]) -> None:
        """Thêm một clause. Từ chối clause rỗng và literal 0/không nguyên.

        Family Kissat của PySAT bị chặn ở đây: nạp clause vào nó giết process
        (access violation) thay vì báo lỗi.
        """
        if self.family in PYSAT_KISSAT_FAMILIES:
            raise BackendError(
                f"PySAT family '{self.family}' crash process khi nạp clause; "
                "dùng binary ngoài: Config(sat_solver='kissat') "
                "(xem docs/sat_tooling.md mục 7)."
            )

        self._solver.add_clause(validate_clause(clause))
        self._n_clauses += 1

    def add_clauses(self, clauses: Iterable[Sequence[int]]) -> None:
        for clause in clauses:
            self.add_clause(clause)

    # --- giải -----------------------------------------------------------

    def solve(self, time_limit: float | None = None) -> SolveStatus:
        """Giải CNF đã nạp.

        ``time_limit`` là số giây; ``None`` là không giới hạn. Hết thời gian mà
        chưa có kết luận thì trả ``"UNKNOWN"``.
        """
        if time_limit is not None and time_limit <= 0:
            self._status = "UNKNOWN"
            self._solve_time = 0.0
            return self._status

        start = monotonic()
        try:
            if time_limit is None:
                result = self._solver.solve()
            elif self.family in INTERRUPTIBLE_FAMILIES:
                result = self._solve_with_interrupt(time_limit)
            elif self.family in BUDGETED_FAMILIES:
                result = self._solve_with_conflict_budget(time_limit)
            else:
                raise BackendError(
                    f"Solver '{self.solver_name}' (family '{self.family}') "
                    "không hỗ trợ time_limit."
                )
        except BackendError:
            raise
        except Exception as exc:  # lỗi native -> ERR, không nuốt
            raise BackendError(
                f"Solver '{self.solver_name}' lỗi khi giải: {exc}"
            ) from exc
        finally:
            self._solve_time = monotonic() - start

        self._status = (
            "SAT" if result is True else "UNSAT" if result is False else "UNKNOWN"
        )
        return self._status

    def _solve_with_interrupt(self, time_limit: float):
        """Timeout bằng ``interrupt()`` + watchdog (solver MiniSat-like)."""
        done = Event()

        def watch() -> None:
            # Cờ đã bật nghĩa là solve đã xong: không interrupt nữa (tránh cờ cũ).
            if not done.wait(time_limit) and not done.is_set():
                self._solver.interrupt()

        Thread(target=watch, daemon=True).start()
        try:
            return self._solver.solve_limited(expect_interrupt=True)
        finally:
            done.set()

    def _solve_with_conflict_budget(self, time_limit: float):
        """Timeout bằng ``conf_budget`` tăng dần (CaDiCaL, Kissat).

        Mỗi lần gọi chỉ bị chặn theo số xung đột, nên đồng hồ được kiểm tra
        giữa các vòng; độ vượt deadline bị chặn bởi thời gian của vòng trước.
        """
        deadline = monotonic() + time_limit
        budget = CONFLICT_BUDGET_START

        while True:
            self._solver.conf_budget(budget)
            result = self._solver.solve_limited(expect_interrupt=False)
            if result is not None:
                return result
            if monotonic() >= deadline:
                return None
            budget *= 2

    # --- model ----------------------------------------------------------

    def get_model(self) -> list[int] | None:
        """Model của lần giải SAT gần nhất; ``None`` nếu chưa SAT."""
        if self._status != "SAT":
            return None
        return self._solver.get_model()

    # --- vòng đời -------------------------------------------------------

    def delete(self) -> None:
        self._solver.delete()

    def __enter__(self) -> "SatBackend":
        return self

    def __exit__(self, *_exc) -> None:
        self.delete()
