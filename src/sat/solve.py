"""Pipeline SAT cho ABP: ``Instance + K → CNF → CaDiCaL → decode → verify() → Result``.

Chiến lược ngưỡng (WORK BREAKDOWN §5): tìm K lớn nhất mà bài toán quyết định là SAT.
Bắt đầu từ cận dưới ``K = lo + 1`` (``lo`` = nghiệm tốt nhất đã verify, khởi đầu 0); mỗi
lần SAT thì decode, verify, lấy antibandwidth thực tế ``B`` rồi đặt ``K ← B + 1``; gặp
UNSAT thì ``K - 1 = B`` là tối ưu. Mọi nghiệm đều qua ``verify()`` trước khi vào ``Result``.
"""

from __future__ import annotations

import warnings
from time import perf_counter

from src.common.models import Config, Instance, Result
from src.common.verify import verify
from src.sat.backend import DEFAULT_SOLVER, BackendError, SatBackend
from src.sat.pairwise import (
    DEFAULT_ABP_ENCODING,
    DEFAULT_AMO_ENCODING,
    CNF,
    build_cnf,
    decode_model,
    trivial_unsat,
)

METHOD = "sat"
ABP_ENCODINGS = (DEFAULT_ABP_ENCODING,)

# Field Config mà W1 chưa cài đặt: đặt khác mặc định thì cảnh báo, không bỏ qua im lặng.
IGNORED_CONFIG_FIELDS = (
    "memory_limit",
    "search_mode",
    "symmetry",
    "warm_start",
    "seed",
)
_CONFIG_DEFAULTS = {
    name: getattr(Config(method=METHOD), name) for name in IGNORED_CONFIG_FIELDS
}


def _warn_ignored_config(cfg: Config) -> None:
    """Cảnh báo một lần nếu caller đặt field Config mà W1 bỏ qua (không im lặng)."""
    ignored = [
        name
        for name in IGNORED_CONFIG_FIELDS
        if getattr(cfg, name) != _CONFIG_DEFAULTS[name]
    ]
    if not ignored:
        return

    warnings.warn(
        "W1 bỏ qua các field Config: "
        + ", ".join(ignored)
        + " (memory_limit chưa cài đặt nên status MO không bao giờ xuất hiện; "
        "search_mode/symmetry/warm_start/seed thuộc P3).",
        stacklevel=2,
    )


def solve_sat(instance: Instance, config: Config | None = None) -> Result:
    """Giải ABP bằng SAT; trả ``Result`` theo CONTRACT.md.

    Tìm K theo WORK BREAKDOWN §5 / Quang.md §3.3: ``K ← B + 1`` từ cận dưới, dừng ở
    lần UNSAT đầu tiên (ngưỡng đó chứng minh ``B`` tối ưu).

    ``Config.time_limit`` là ngân sách cho **cả chuỗi K**: bao gồm ``build_cnf`` (encode),
    ``add_clauses`` (nạp clause) và ``solve`` của mọi lần dò. Deadline được kiểm tra trước
    mỗi pha và phần còn lại được truyền vào solver; pha đang chạy khi hết giờ vẫn hoàn
    thành nên ``t_total`` vượt ``time_limit`` một khoảng nhỏ (xem ``docs/sat_tooling.md``
    mục 4).
    """
    cfg = config or Config(method=METHOD)
    _warn_ignored_config(cfg)

    abp_encoding = cfg.abp_encoding or DEFAULT_ABP_ENCODING
    amo_encoding = cfg.amo_encoding or DEFAULT_AMO_ENCODING
    solver_name = cfg.sat_solver or DEFAULT_SOLVER

    if abp_encoding not in ABP_ENCODINGS:
        raise ValueError(
            f"abp_encoding '{abp_encoding}' chưa hỗ trợ; chọn {ABP_ENCODINGS}."
        )
    _validate_instance(instance)

    start = perf_counter()
    deadline = None if cfg.time_limit is None else start + cfg.time_limit

    lo = 0  # ngưỡng lớn nhất đã có nghiệm verify được (0 = chưa có)
    hi = instance.n  # ngưỡng đã biết UNSAT: chặn trên bằng đếm nhãn
    unsat_source = "counting:lệch nhãn tối đa n-1"
    best_solution: dict[int, int] | None = None
    best_cnf: CNF | None = None
    probes: list[dict[str, object]] = []
    t_encode = 0.0
    t_solve = 0.0
    error: str | None = None
    timed_out = False

    while lo + 1 < hi:
        k = lo + 1  # cận dưới: ngưỡng nhỏ nhất chưa bị bác
        remaining = None if deadline is None else deadline - perf_counter()

        try:
            status, solution, cnf, probe_encode, probe_solve = _probe(
                instance, k, amo_encoding, solver_name, remaining
            )
        except BackendError as exc:  # lỗi backend/giấy phép -> ERR
            error = str(exc)
            break

        t_encode += probe_encode
        t_solve += probe_solve

        value: int | None = None
        if status == "SAT":
            value = verify(instance, solution)  # B thực tế, có thể > K
            if value < k:  # model SAT không thỏa ngưỡng -> lỗi encoding
                error = (
                    f"Nghiệm tại K={k} chỉ đạt {value} < K: mâu thuẫn encoding."
                )
                break
            lo, best_solution, best_cnf = value, solution, cnf
        elif status == "UNSAT":
            # Ngưỡng K = lo + 1 đã bị bác -> B = lo là tối ưu.
            hi, unsat_source = k, "solver"
        else:
            timed_out = True

        probes.append(
            {
                "k": k,
                "status": status,
                "b": value,
                "t_solve": round(probe_solve, 6),
            }
        )

        if timed_out:
            break

    t_total = perf_counter() - start

    status, lb, ub, gap, verified = _summarise(
        instance, lo, hi, best_solution, timed_out, error is not None
    )

    # Nghiệm phải khớp bằng chứng của vòng dò K, nếu không là lỗi encoding.
    if status == "OPT" and verified != lo:
        error = (
            f"Nghiệm có giá trị {verified} khác ngưỡng {lo} đã chứng minh tối ưu: "
            "mâu thuẫn bằng chứng."
        )
    elif status == "FEAS" and verified is not None and verified >= hi:
        error = (
            f"Nghiệm có giá trị {verified} >= ngưỡng {hi} đã chứng minh UNSAT: "
            "mâu thuẫn bằng chứng."
        )

    if status == "ERR" and error is None:
        error = (
            "Không có nghiệm verify được dù chưa hết thời gian: "
            "trạng thái bất khả (K=1 luôn SAT khi đồ thị có cạnh)."
        )

    if error is not None:
        status, lb, ub, gap = "ERR", None, None, None

    metadata: dict[str, object] = {
        "method": METHOD,
        "abp_encoding": abp_encoding,
        "amo_encoding": amo_encoding,
        "sat_solver": solver_name,
        "probes": probes,
        "k_best": lo or None,  # B tốt nhất đã verify (= ngưỡng chứng minh được)
        "k_unsat": hi,
        "unsat_source": unsat_source,
        "abp_encoding_stats": dict(best_cnf.stats) if best_cnf else None,
    }
    if error is not None:
        metadata["error"] = error

    return Result(
        status=status,
        lb=lb,
        ub=ub,
        gap=gap,
        t_encode=t_encode,
        t_solve=t_solve,
        t_total=t_total,
        variables=best_cnf.n_vars if best_cnf else None,
        clauses=len(best_cnf.clauses) if best_cnf else None,
        peak_memory=None,  # chưa đo ở W1, xem docs/sat_tooling.md
        solution=best_solution if status in ("OPT", "FEAS") else None,
        metadata=metadata,
    )


def solve_decision(
    instance: Instance, k: int, config: Config | None = None
) -> tuple[str, dict[int, int] | None]:
    """Bài toán quyết định tại một ngưỡng ``k``: ``(status, labeling)``.

    ``Config.time_limit`` là ngân sách cho cả ``build_cnf``, ``add_clauses`` và ``solve``.
    """
    cfg = config or Config(method=METHOD)
    _warn_ignored_config(cfg)
    amo_encoding = cfg.amo_encoding or DEFAULT_AMO_ENCODING
    solver_name = cfg.sat_solver or DEFAULT_SOLVER
    _validate_instance(instance)

    status, solution, _cnf, _t_encode, _t_solve = _probe(
        instance, k, amo_encoding, solver_name, cfg.time_limit
    )
    return status, solution


def _probe(
    instance: Instance,
    k: int,
    amo_encoding: str,
    solver_name: str,
    time_limit: float | None,
) -> tuple[str, dict[int, int] | None, CNF | None, float, float]:
    """Dựng CNF, giải, decode; trả ``(status, labeling, cnf, t_encode, t_solve)``.

    ``time_limit`` là ngân sách còn lại cho **cả** ``build_cnf``, ``add_clauses`` và
    ``solve`` (WORK BREAKDOWN §5: runtime gồm tạo model/encoding và mọi lần gọi
    solver). Hết ngân sách trước khi encode → ``UNKNOWN``, không dựng CNF; hết ngân
    sách sau khi nạp clause → ``solve`` nhận phần thời gian còn lại.
    """
    if trivial_unsat(instance.n, k):
        return "UNSAT", None, None, 0.0, 0.0

    if time_limit is not None and time_limit <= 0:
        return "UNKNOWN", None, None, 0.0, 0.0

    t0 = perf_counter()
    cnf = build_cnf(instance, k, amo_encoding=amo_encoding)
    t_encode = perf_counter() - t0

    backend = SatBackend(solver_name)
    try:
        backend.add_clauses(cnf.clauses)
        remaining = None if time_limit is None else time_limit - (perf_counter() - t0)
        t1 = perf_counter()
        status = backend.solve(time_limit=remaining)
        t_solve = perf_counter() - t1

        solution = decode_model(cnf, backend.get_model()) if status == "SAT" else None
        return status, solution, cnf, t_encode, t_solve
    finally:
        backend.delete()


def _summarise(
    instance: Instance,
    lo: int,
    hi: int,
    best_solution: dict[int, int] | None,
    timed_out: bool,
    has_error: bool,
) -> tuple[str, int | None, int | None, float | None, int | None]:
    """Chuyển trạng thái tìm kiếm thành ``(status, lb, ub, gap, giá trị verify)``."""
    if has_error:
        return "ERR", None, None, None, None

    if best_solution is None:
        # Hết giờ mà chưa có nghiệm verify được -> TO. Không giới hạn thời gian
        # mà vẫn không có nghiệm là bất khả (K=1 luôn SAT khi đồ thị có cạnh).
        return ("TO" if timed_out else "ERR"), None, None, None, None

    value = verify(instance, best_solution)  # verify() là cổng bắt buộc

    if lo + 1 == hi:  # đã chứng minh K = lo tối ưu
        return "OPT", value, value, 0.0, value

    # ``hi`` là ngưỡng đã chứng minh UNSAT, nên ab_opt <= hi - 1.
    ub = hi - 1
    return "FEAS", value, ub, float(ub - value), value


def _validate_instance(instance: Instance) -> None:
    """Kiểm tra biên của ``Instance`` dựng tay (loader đã kiểm tra cùng điều kiện).

    Raises:
        ValueError: Nếu đồ thị rỗng, hoặc một đỉnh trong cạnh không phải số
            nguyên / nằm ngoài ``0..n-1`` (không để ``KeyError`` từ ``build_cnf``).
    """
    if instance.n < 1:
        raise ValueError("Đồ thị phải có ít nhất một đỉnh.")
    if not instance.edges:
        raise ValueError("ABP không xác định khi đồ thị không có cạnh.")

    for u, v in instance.edges:
        for endpoint in (u, v):
            if isinstance(endpoint, bool) or not isinstance(endpoint, int):
                raise ValueError(
                    f"Đỉnh trong cạnh ({u}, {v}) phải là số nguyên: {endpoint!r}."
                )
            if not 0 <= endpoint < instance.n:
                raise ValueError(
                    f"Cạnh ({u}, {v}) chứa đỉnh ngoài khoảng 0..{instance.n - 1}."
                )