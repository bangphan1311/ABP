"""Pipeline SAT cho ABP: ``Instance + K → CNF → CaDiCaL → decode → verify() → Result``.

Chiến lược ngưỡng (WORK BREAKDOWN §5): tìm K lớn nhất mà bài toán quyết định là SAT.
Bắt đầu từ cận dưới ``K = lo + 1`` (``lo`` = nghiệm tốt nhất đã verify, khởi đầu 0); mỗi
lần SAT thì decode, verify, lấy antibandwidth thực tế ``B`` rồi đặt ``K ← B + 1``; gặp
UNSAT thì ``K - 1 = B`` là tối ưu. Mọi nghiệm đều qua ``verify()`` trước khi vào ``Result``.
"""

from __future__ import annotations

import ctypes
import os
import warnings
from ctypes import wintypes
from time import perf_counter

from src.common.models import Config, Instance, Result
from src.common.checkpoint import write_incumbent_checkpoint
from src.common.verify import verify
from src.sat import order
from src.sat.backend import (
    DEFAULT_SOLVER,
    KISSAT_LIMITATION,
    BackendError,
    SatBackend,
    solver_family,
)
from src.sat.pairwise import (
    DEFAULT_ABP_ENCODING,
    DEFAULT_AMO_ENCODING,
    CNF,
    build_cnf,
    decode_model,
    trivial_unsat,
)

METHOD = "sat"
ABP_ENCODINGS = (DEFAULT_ABP_ENCODING, "order")

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


class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    """PROCESS_MEMORY_COUNTERS của psapi (chỉ cần field working set)."""

    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


# Windows dùng psapi; Linux dùng /proc/self/statm để tránh phụ thuộc API Windows
# ngay lúc import (đặc biệt khi chạy unit test/CI trên Linux).
if hasattr(ctypes, "WinDLL"):
    _psapi = ctypes.WinDLL("psapi")
    _kernel32 = ctypes.WinDLL("kernel32")
    # Thiếu prototype thì HANDLE pseudo -1 của GetCurrentProcess bị cắt 32 bit
    # và GetProcessMemoryInfo luôn thất bại.
    _kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    _psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_PROCESS_MEMORY_COUNTERS),
        wintypes.DWORD,
    ]
    _psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
else:
    _psapi = None
    _kernel32 = None


def working_set_mb() -> float:
    """Working set hiện tại của process này, đơn vị MB, qua GetProcessMemoryInfo.

    Trên Windows dùng GetProcessMemoryInfo; Linux đọc RSS từ /proc/self/statm.
    Thất bại hệ thống trả ``0.0``: số liệu bộ nhớ không được làm gãy pipeline.
    """
    if _psapi is not None and _kernel32 is not None:
        counters = _PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS)
        measured = _psapi.GetProcessMemoryInfo(
            _kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
        )
        if measured:
            return counters.WorkingSetSize / (1024.0 * 1024.0)

    # Linux: trường resident pages ở cột 2 của /proc/self/statm; chỉ đọc số liệu,
    # không tạo cơ chế enforce giới hạn bộ nhớ.
    try:
        with open("/proc/self/statm", "r", encoding="ascii") as stream:
            fields = stream.read().split()
        resident_pages = int(fields[1])
        page_size = os.sysconf("SC_PAGE_SIZE")
        if resident_pages >= 0 and page_size > 0:
            return resident_pages * page_size / (1024.0 * 1024.0)
    except (OSError, ValueError, IndexError, AttributeError):
        pass
    return 0.0


def solve_sat(
    instance: Instance, config: Config | None = None, ub: int | None = None
) -> Result:
    """Giải ABP bằng SAT; trả ``Result`` theo CONTRACT.md.

    Tìm K theo WORK BREAKDOWN §5 / Quang.md §3.3: ``K ← B + 1`` từ cận dưới, dừng ở
    lần UNSAT đầu tiên (ngưỡng đó chứng minh ``B`` tối ưu).

    ``ub`` (tùy chọn) là cận trên ngoài do bên gọi tính. Chỉ kiểm tra, không dùng để
    chứng minh: OPT vẫn cần UNSAT của solver. Nếu B đã verify lớn hơn ``ub`` → ``ValueError``
    (``ub`` sai, không phải lỗi encoding). Vắng ``ub``: hành vi mặc định.

    ``Config.time_limit`` là ngân sách cho **cả chuỗi K**: bao gồm ``build_cnf`` (encode),
    ``add_clauses`` (nạp clause) và ``solve`` của mọi lần dò. Deadline được kiểm tra trước
    mỗi pha và phần còn lại được truyền vào solver; pha đang chạy khi hết giờ vẫn hoàn
    thành nên ``t_total`` vượt ``time_limit`` một khoảng nhỏ (xem ``docs/sat_tooling.md``
    mục 4).

    ``Result.peak_memory`` là working set lớn nhất của process, đơn vị MB (float),
    chụp bằng ``GetProcessMemoryInfo`` tại các mốc — trước khi giải, sau mỗi probe,
    và trong mỗi probe: trước solve (sau khi nạp clause), sau solve, sau decode —
    rồi lấy max. Đây là max của các điểm chụp, không phải peak liên tục
    (``docs/sat_tooling.md``). ``None`` khi ERR.
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
    _validate_solver(solver_name)
    _validate_instance(instance)
    _validate_ub(ub)

    start = perf_counter()
    deadline = None if cfg.time_limit is None else start + cfg.time_limit

    lo = 0  # ngưỡng lớn nhất đã có nghiệm verify được (0 = chưa có)
    hi = instance.n  # ngưỡng đã biết UNSAT: chặn trên bằng đếm nhãn
    unsat_source = "counting:lệch nhãn tối đa n-1"
    best_solution: dict[int, int] | None = None
    best_cnf: CNF | None = None
    last_cnf: CNF | None = None  # CNF của lần dò cuối cùng (số liệu RQ1)
    probes: list[dict[str, object]] = []
    t_encode = 0.0
    t_solve = 0.0
    peak_ws = working_set_mb()  # mốc chụp đầu tiên: trước khi giải
    error: str | None = None
    timed_out = False

    while lo + 1 < hi:
        k = lo + 1  # cận dưới: ngưỡng nhỏ nhất chưa bị bác
        remaining = None if deadline is None else deadline - perf_counter()

        try:
            status, solution, cnf, probe_encode, probe_solve, probe_ws = _probe(
                instance, k, abp_encoding, amo_encoding, solver_name, remaining
            )
        except BackendError as exc:  # lỗi backend/giấy phép -> ERR
            error = str(exc)
            break

        t_encode += probe_encode
        t_solve += probe_solve
        peak_ws = max(peak_ws, probe_ws, working_set_mb())  # mốc: sau mỗi probe
        if cnf is not None:
            last_cnf = cnf

        value: int | None = None
        if status == "SAT":
            value = verify(instance, solution)  # B thực tế, có thể > K
            if value < k:  # model SAT không thỏa ngưỡng -> lỗi encoding
                error = (
                    f"Nghiệm tại K={k} chỉ đạt {value} < K: mâu thuẫn encoding."
                )
                break
            if ub is not None and value > ub:  # ub bên ngoài sai -> ValueError
                raise ValueError(
                    f"ub={ub} nhỏ hơn B={value} đã verify: ub không hợp lệ."
                )
            lo, best_solution, best_cnf = value, solution, cnf
            write_incumbent_checkpoint(
                instance,
                cfg,
                objective=value,
                solution=solution,
                metrics={
                    "t_encode": t_encode,
                    "t_solve": t_solve,
                    "t_total": perf_counter() - start,
                    "variables": cnf.n_vars if cnf is not None else None,
                    "clauses": len(cnf.clauses) if cnf is not None else None,
                    "peak_memory": peak_ws,
                },
            )
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
                "t_encode": round(probe_encode, 6),
                "t_solve": round(probe_solve, 6),
                "variables": cnf.n_vars if cnf is not None else None,
                "clauses": len(cnf.clauses) if cnf is not None else None,
            }
        )

        if timed_out:
            break

    t_total = perf_counter() - start

    status, lb, ub_out, gap, verified = summarise_result(
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
        status, lb, ub_out, gap = "ERR", None, None, None

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
        ub=ub_out,
        gap=gap,
        t_encode=t_encode,
        t_solve=t_solve,
        t_total=t_total,
        variables=last_cnf.n_vars if last_cnf else None,
        clauses=len(last_cnf.clauses) if last_cnf else None,
        peak_memory=None if error is not None else peak_ws,  # max các mốc chụp, MB
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
    abp_encoding = cfg.abp_encoding or DEFAULT_ABP_ENCODING
    amo_encoding = cfg.amo_encoding or DEFAULT_AMO_ENCODING
    solver_name = cfg.sat_solver or DEFAULT_SOLVER

    if abp_encoding not in ABP_ENCODINGS:
        raise ValueError(
            f"abp_encoding '{abp_encoding}' chưa hỗ trợ; chọn {ABP_ENCODINGS}."
        )
    _validate_solver(solver_name)
    _validate_instance(instance)

    status, solution, _cnf, _t_encode, _t_solve, _ws = _probe(
        instance, k, abp_encoding, amo_encoding, solver_name, cfg.time_limit
    )
    return status, solution


def _probe(
    instance: Instance,
    k: int,
    abp_encoding: str,
    amo_encoding: str,
    solver_name: str,
    time_limit: float | None,
) -> tuple[str, dict[int, int] | None, CNF | None, float, float, float]:
    """Dựng CNF, giải, decode; trả ``(status, labeling, cnf, t_encode, t_solve, ws_mb)``.

    ``abp_encoding`` chọn build/decode (``pairwise`` hoặc ``order``); hai encoding
    dùng chung contract ``CNF`` nên phần còn lại của pipeline không đổi.

    ``time_limit`` là ngân sách còn lại cho **cả** ``build_cnf``, ``add_clauses`` và
    ``solve`` (WORK BREAKDOWN §5: runtime gồm tạo model/encoding và mọi lần gọi
    solver). Hết ngân sách trước khi encode → ``UNKNOWN``, không dựng CNF; hết ngân
    sách sau khi nạp clause → ``solve`` nhận phần thời gian còn lại.

    ``ws_mb`` là working set lớn nhất (MB) chụp trong lần dò này: trước solve
    (sau khi nạp clause, solver còn sống), sau solve và sau decode. Là max của
    các điểm chụp, không phải peak liên tục (``docs/sat_tooling.md``).
    """
    if trivial_unsat(instance.n, k):
        return "UNSAT", None, None, 0.0, 0.0, working_set_mb()

    if time_limit is not None and time_limit <= 0:
        return "UNKNOWN", None, None, 0.0, 0.0, working_set_mb()

    t0 = perf_counter()
    if abp_encoding == "order":
        cnf = order.build_cnf(instance, k, amo_encoding=amo_encoding)
    else:
        cnf = build_cnf(instance, k, amo_encoding=amo_encoding)
    t_encode = perf_counter() - t0

    backend = SatBackend(solver_name)
    try:
        backend.add_clauses(cnf.clauses)
        ws_peak = working_set_mb()  # mốc: trước solve (đã nạp clause, solver còn sống)
        remaining = None if time_limit is None else time_limit - (perf_counter() - t0)
        t1 = perf_counter()
        status = backend.solve(time_limit=remaining)
        t_solve = perf_counter() - t1
        ws_peak = max(ws_peak, working_set_mb())  # mốc: sau solve, trước delete()

        decoder = order.decode_model if abp_encoding == "order" else decode_model
        solution = decoder(cnf, backend.get_model()) if status == "SAT" else None
        ws_peak = max(ws_peak, working_set_mb())  # mốc: sau decode
        return status, solution, cnf, t_encode, t_solve, ws_peak
    finally:
        backend.delete()


def summarise_result(
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


def _validate_solver(solver_name: str) -> None:
    """Từ chối kissat: hạn chế vĩnh viễn W2 (ticket 09).

    Family ``kissat404`` của PySAT cho model sai và abort process khi nạp clause
    sau solve; không có binary kissat ngoài (``docs/sat_tooling.md`` mục Kissat).
    Chặn trước khi dựng backend.
    """
    if solver_family(solver_name) == "kissat404":
        raise ValueError(KISSAT_LIMITATION)


def _validate_ub(ub: int | None) -> None:
    """``ub`` tùy chọn phải là số nguyên >= 1 (đồ thị có cạnh thì B >= 1, K = 1 luôn SAT)."""
    if ub is None:
        return
    if isinstance(ub, bool) or not isinstance(ub, int) or ub < 1:
        raise ValueError(f"ub phải là số nguyên >= 1: {ub!r}.")


def _validate_instance(instance: Instance) -> None:
    """Kiểm tra biên của ``Instance`` dựng tay (loader đã kiểm tra cùng điều kiện).

    Raises:
        ValueError: Nếu đồ thị rỗng, hoặc một đỉnh trong cạnh không phải số
            nguyên / nằm ngoài ``0..n-1`` (không để ``KeyError`` từ ``build_cnf``).
    """
    if isinstance(instance.n, bool) or not isinstance(instance.n, int):
        raise ValueError(f"n phải là số nguyên: {instance.n!r}.")
    if instance.n < 1:
        raise ValueError("Đồ thị phải có ít nhất một đỉnh.")
    if not instance.edges:
        raise ValueError("ABP không xác định khi đồ thị không có cạnh.")
    if any(u == v for u, v in instance.edges):
        raise ValueError("self-loop (u, u) is not allowed.")

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
