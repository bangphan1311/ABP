"""Thi hành memory_limit ở cấp hệ điều hành cho worker benchmark.

memory_limit dùng đơn vị GiB (1 GiB = 1024**3 byte).
Windows: Job Object giới hạn committed memory của cả job/process tree.
POSIX: RLIMIT_AS giới hạn virtual address space của worker và tiến trình con.
Đây là hai loại tài nguyên OS khác nhau; benchmark chính thức phải dùng cùng một OS.
"""
from __future__ import annotations

import ctypes
import math
import os
from ctypes import wintypes
from typing import Any


GIB = 1024 ** 3
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000


def memory_limit_to_bytes(limit_gib: float | int | None) -> int | None:
    """Kiểm tra và đổi memory_limit (GiB) sang byte."""
    if limit_gib is None:
        return None
    if (
        isinstance(limit_gib, bool)
        or not isinstance(limit_gib, (int, float))
        or not math.isfinite(float(limit_gib))
        or limit_gib <= 0
    ):
        raise ValueError("memory_limit phải là số hữu hạn > 0 GiB hoặc None.")
    value = int(float(limit_gib) * GIB)
    if value <= 0 or value > (1 << (8 * ctypes.sizeof(ctypes.c_size_t))) - 1:
        raise ValueError("memory_limit nằm ngoài phạm vi OS hỗ trợ.")
    return value


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", _IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class WindowsMemoryJob:
    """Job Object đã cấu hình hard limit; worker phải được sinh ở trạng thái suspended."""

    def __init__(self, limit_bytes: int):
        if os.name != "nt" or not hasattr(ctypes, "WinDLL"):
            raise OSError("WindowsMemoryJob chỉ dùng được trên Windows.")
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
        self._handle = None
        self._assigned = False

        self._kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self._kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        self._kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
        ]
        self._kernel32.SetInformationJobObject.restype = wintypes.BOOL
        self._kernel32.AssignProcessToJobObject.argtypes = [
            wintypes.HANDLE, wintypes.HANDLE
        ]
        self._kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        self._kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self._kernel32.TerminateJobObject.restype = wintypes.BOOL
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL
        self._ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        self._ntdll.NtResumeProcess.restype = ctypes.c_long

        self._handle = self._kernel32.CreateJobObjectW(None, None)
        if not self._handle:
            raise ctypes.WinError(ctypes.get_last_error())

        info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = (
            JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        info.JobMemoryLimit = limit_bytes
        ok = self._kernel32.SetInformationJobObject(
            self._handle,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not ok:
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def assign_and_resume(self, process: Any) -> None:
        """Gắn worker còn suspended vào job rồi mới cho chạy."""
        handle = wintypes.HANDLE(int(process._handle))  # subprocess.Popen trên Windows
        if not self._kernel32.AssignProcessToJobObject(self._handle, handle):
            error = ctypes.WinError(ctypes.get_last_error())
            try:
                process.kill()
                process.wait(timeout=5)
            except Exception:
                pass
            raise OSError(
                f"Không thể gắn worker vào Windows Job Object; từ chối chạy không giới hạn RAM: {error}"
            ) from error
        self._assigned = True

        # Popen đóng primary-thread handle sau CreateProcess. NtResumeProcess được dùng
        # để resume process được tạo bằng CREATE_SUSPENDED sau khi Job Object đã gắn.
        status = self._ntdll.NtResumeProcess(handle)
        if status < 0:
            self.terminate()
            try:
                process.wait(timeout=5)
            except Exception:
                pass
            raise OSError(f"NtResumeProcess thất bại, NTSTATUS=0x{status & 0xFFFFFFFF:08X}.")

    def terminate(self) -> None:
        """Kết thúc worker và mọi tiến trình con trong job."""
        if self._handle and self._assigned:
            self._kernel32.TerminateJobObject(self._handle, 1)

    def close(self) -> None:
        """Đóng handle; KILL_ON_JOB_CLOSE dọn tiến trình còn sót."""
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None


def make_posix_memory_preexec(limit_bytes: int):
    """Tạo preexec hook dùng RLIMIT_AS trên POSIX; kiểm tra hard limit trước khi fork."""
    if os.name != "posix":
        raise OSError("RLIMIT_AS chỉ hỗ trợ trên POSIX.")
    try:
        import resource
    except ImportError as exc:
        raise OSError("Môi trường này không hỗ trợ resource/RLIMIT_AS.") from exc
    if not hasattr(resource, "RLIMIT_AS"):
        raise OSError("Hệ điều hành không hỗ trợ RLIMIT_AS.")

    _soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    if hard != resource.RLIM_INFINITY and limit_bytes > hard:
        raise ValueError(
            "memory_limit yêu cầu lớn hơn hard RLIMIT_AS hiện tại; không thể bảo đảm mức giới hạn yêu cầu."
        )

    def _apply_limit() -> None:
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))

    return _apply_limit
