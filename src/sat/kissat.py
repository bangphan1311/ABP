"""Adapter Kissat gọi qua binary ngoài (file DIMACS + subprocess).

PySAT 1.9.dev15 giết process khi nạp clause vào Kissat (access violation, xem
``docs/sat_tooling.md`` mục 7), nên backend này không đi qua PySAT: ghi CNF ra file
DIMACS, chạy binary ``kissat`` trong process riêng, đọc mã thoát (10 = SAT,
20 = UNSAT) và model ở các dòng ``v`` của stdout.

Binary được tìm theo thứ tự: biến môi trường ``ABP_KISSAT`` (đường dẫn đầy đủ), rồi
``kissat`` trên ``PATH``. Không tìm thấy -> ``BackendError`` (pipeline map sang status
``ERR``), không bao giờ crash. Cách cài: ``docs/sat_tooling.md`` mục 7.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from typing import Iterable, Sequence

from src.sat.backend import BackendError, SolveStatus, validate_clause

SOLVER_NAME = "kissat"
BINARY_ENV_VAR = "ABP_KISSAT"
SAT_EXIT_CODE = 10
UNSAT_EXIT_CODE = 20


def kissat_path() -> str | None:
    """Đường dẫn binary Kissat, hoặc ``None`` nếu không có.

    ``ABP_KISSAT`` trỏ tới file không tồn tại thì coi như không có (không đoán).
    """
    override = os.environ.get(BINARY_ENV_VAR)
    if override:
        return override if Path(override).is_file() else None
    return shutil.which(SOLVER_NAME)


def dimacs(n_vars: int, clauses: Sequence[Sequence[int]]) -> str:
    """Chuỗi DIMACS (``p cnf <n_vars> <n_clauses>``) cho các clause đã kiểm tra."""
    lines = [f"p cnf {n_vars} {len(clauses)}"]
    lines.extend(
        " ".join(str(literal) for literal in clause) + " 0" for clause in clauses
    )
    return "\n".join(lines) + "\n"


def parse_kissat_output(
    returncode: int, stdout: str
) -> tuple[SolveStatus, list[int] | None]:
    """Đọc mã thoát + stdout của Kissat thành ``(status, model)``.

    Raises:
        BackendError: Mã thoát không phải 10/20, hoặc báo SAT mà không có model.
    """
    if returncode == UNSAT_EXIT_CODE:
        return "UNSAT", None
    if returncode != SAT_EXIT_CODE:
        raise BackendError(
            f"kissat kết thúc với mã {returncode} (10 = SAT, 20 = UNSAT): "
            f"{stdout.strip()[:200]!r}"
        )

    try:
        model = [
            int(token)
            for line in stdout.splitlines()
            if line.startswith("v")
            for token in line.split()[1:]
            if token != "0"
        ]
    except ValueError as exc:  # output hỏng -> ERR, không nuốt
        raise BackendError(f"Model của kissat không đọc được: {exc}") from exc

    if not model:
        raise BackendError("kissat báo SAT nhưng stdout không có dòng model 'v'.")
    return "SAT", model


class KissatBackend:
    """Kissat ngoài process, cùng interface với ``SatBackend``.

    Khác biệt đã biết: thời gian ghi file DIMACS nằm trong ``solve_time`` (với PySAT
    nó nằm trong ``add_clauses``), và timeout do phía Python cắt (``subprocess``
    timeout), không dựa vào option thời gian của Kissat.
    """

    def __init__(self, binary: str | None = None):
        self.binary = binary or kissat_path()
        if self.binary is None:
            raise BackendError(
                "Không tìm thấy binary Kissat: đặt biến môi trường "
                f"{BINARY_ENV_VAR} hoặc thêm 'kissat' vào PATH "
                "(xem docs/sat_tooling.md mục 7)."
            )

        self._clauses: list[list[int]] = []
        self._n_vars = 0
        self._status: SolveStatus = "UNKNOWN"
        self._solve_time = 0.0
        self._model: list[int] | None = None

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
    def n_vars(self) -> int:
        return self._n_vars

    @property
    def n_clauses(self) -> int:
        return len(self._clauses)

    # --- nạp CNF --------------------------------------------------------

    def add_clause(self, clause: Sequence[int]) -> None:
        """Thêm một clause. Từ chối clause rỗng và literal 0/không nguyên."""
        literals = validate_clause(clause)
        self._clauses.append(literals)
        self._n_vars = max(self._n_vars, max(abs(literal) for literal in literals))

    def add_clauses(self, clauses: Iterable[Sequence[int]]) -> None:
        for clause in clauses:
            self.add_clause(clause)

    # --- giải -----------------------------------------------------------

    def solve(self, time_limit: float | None = None) -> SolveStatus:
        """Giải CNF đã nạp.

        ``time_limit`` là số giây; ``None`` là không giới hạn. Quá thời gian thì
        process bị cắt và trả ``"UNKNOWN"``.
        """
        if time_limit is not None and time_limit <= 0:
            self._status, self._solve_time, self._model = "UNKNOWN", 0.0, None
            return self._status

        text = dimacs(max(1, self._n_vars), self._clauses)
        start = monotonic()
        try:
            with TemporaryDirectory() as tmp:
                cnf_path = Path(tmp) / "probe.cnf"
                cnf_path.write_text(text, encoding="ascii")

                try:
                    proc = subprocess.run(
                        [self.binary, str(cnf_path)],
                        capture_output=True,
                        text=True,
                        timeout=time_limit,
                        check=False,
                    )
                except subprocess.TimeoutExpired:
                    self._status, self._model = "UNKNOWN", None
                    return self._status

            self._status, self._model = parse_kissat_output(
                proc.returncode, proc.stdout
            )
        except OSError as exc:  # binary hỏng/không chạy được -> ERR
            raise BackendError(
                f"Không chạy được binary kissat '{self.binary}': {exc}"
            ) from exc
        finally:
            self._solve_time = monotonic() - start

        return self._status

    # --- model ----------------------------------------------------------

    def get_model(self) -> list[int] | None:
        """Model của lần giải SAT gần nhất; ``None`` nếu chưa SAT."""
        if self._status != "SAT":
            return None
        return list(self._model) if self._model else None

    # --- vòng đời -------------------------------------------------------

    def delete(self) -> None:
        """Không có tài nguyên native; xả clause và model đã giữ trong RAM."""
        self._clauses = []
        self._model = None

    def __enter__(self) -> "KissatBackend":
        return self

    def __exit__(self, *_exc) -> None:
        self.delete()
