"""How t_encode, t_solve and memory are measured, and what each one sees. PySAT + Windows API only.

Run: .venv\\Scripts\\python.exe -u docs\\handoff\\sat-tooling\\probe_measure.py
"""
import ctypes
import time
import tracemalloc
from ctypes import wintypes

from pysat.card import CardEnc, EncType
from pysat.solvers import Solver


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
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


_psapi = ctypes.WinDLL("psapi")
_kernel32 = ctypes.WinDLL("kernel32")
_psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]


def rss_mb():
    pmc = PROCESS_MEMORY_COUNTERS()
    pmc.cb = ctypes.sizeof(pmc)
    ok = _psapi.GetProcessMemoryInfo(_kernel32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
    assert ok, "GetProcessMemoryInfo failed"
    return pmc.WorkingSetSize / 1e6, pmc.PeakWorkingSetSize / 1e6


N, K = 2000, 50
print("baseline rss/peak MB:", rss_mb())

tracemalloc.start()
t0 = time.perf_counter()
cnf = CardEnc.atmost(lits=list(range(1, N + 1)), bound=K, top_id=N, encoding=EncType.seqcounter)
t_encode = time.perf_counter() - t0
_, py_peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"t_encode={t_encode:.3f}s clauses={len(cnf.clauses)} tracemalloc_peak_MB={py_peak / 1e6:.2f}")
print("rss after encode MB (ws, peak):", rss_mb())

t0 = time.perf_counter()
s = Solver(name="cadical195", bootstrap_with=cnf.clauses)
t_load = time.perf_counter() - t0
print(f"t_load (solver build/add clauses)={t_load:.3f}s rss with solver alive MB (ws, peak):", rss_mb())

t0 = time.perf_counter()
r = s.solve()
t_solve = time.perf_counter() - t0
print(f"t_solve={t_solve:.3f}s result={r} stats={s.accum_stats()}")
print("rss after solve MB (ws, peak):", rss_mb())
s.delete()
print("rss after delete MB (ws, peak):", rss_mb())
