"""Conservative process-liveness verdicts for lock takeover and recovery (211-F, plan unit T3; hardening H3, H6).

The only question this module answers is "is the owner of this lock provably
dead?". "Cannot tell" is never "dead":

* a different host, a legacy lock with no recorded host, an invalid pid, an
  unreadable process, or any probe error is **not dead**;
* a pid that no longer exists, or whose process has exited, is dead
  (``pid_absent``);
* a pid that exists with a *different* start time than the one recorded in the
  lock is dead (``pid_start_mismatch``, pid reuse);
* a pid that exists with an equal or an unrecorded start time is **not dead**.

Windows never uses ``os.kill``: signal value 0 is ``CTRL_C_EVENT`` there and
would signal a process group. Liveness and start time come from ``ctypes``
``OpenProcess`` / ``GetExitCodeProcess`` / ``GetProcessTimes`` only. POSIX uses
``os.kill(pid, 0)`` plus the ``/proc/<pid>/stat`` start time where available.
Both back ends sit behind an injectable seam so every branch is testable on any
host. Nothing here ever signals, terminates, or modifies a process.
"""

from __future__ import annotations

import os
import socket
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, Protocol

__all__ = [
    "LivenessVerdict",
    "ProbeResult",
    "Prober",
    "current_host",
    "default_prober",
    "is_process_alive",
    "process_start_time",
    "provably_dead",
]

State = Literal["alive", "absent", "unknown"]

_MAX_PID: Final = 2**32 - 1
_PROCESS_QUERY_LIMITED_INFORMATION: Final = 0x1000
_STILL_ACTIVE: Final = 259
_ERROR_ACCESS_DENIED: Final = 5
_ERROR_INVALID_PARAMETER: Final = 87


@dataclass(frozen=True)
class ProbeResult:
    """One observation. ``start`` is only meaningful when ``state`` is ``alive``."""

    state: State
    start: str | None = None
    detail: str = ""


class Prober(Protocol):
    def __call__(self, pid: int) -> ProbeResult: ...


@dataclass(frozen=True)
class LivenessVerdict:
    dead: bool
    basis: str
    detail: str = ""


def current_host() -> str:
    return socket.gethostname()


# ---------------------------------------------------------------------------
# Windows back end (ctypes only; never os.kill)
# ---------------------------------------------------------------------------


class _Kernel32(Protocol):
    def open_process(self, pid: int) -> tuple[int | None, int]:
        """Return ``(handle, last_error)``; handle is None on failure."""

    def exit_code(self, handle: int) -> int | None: ...

    def creation_time(self, handle: int) -> int | None: ...

    def close(self, handle: int) -> None: ...


class _CtypesKernel32:
    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        self._ctypes = ctypes
        self._wintypes = wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k32.GetExitCodeProcess.restype = wintypes.BOOL
        k32.GetProcessTimes.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)]
        k32.GetProcessTimes.restype = wintypes.BOOL
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        k32.CloseHandle.restype = wintypes.BOOL
        self._k32 = k32

    def open_process(self, pid: int) -> tuple[int | None, int]:
        self._ctypes.set_last_error(0)
        handle = self._k32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return None, self._ctypes.get_last_error()
        return int(handle), 0

    def exit_code(self, handle: int) -> int | None:
        code = self._wintypes.DWORD()
        if not self._k32.GetExitCodeProcess(handle, self._ctypes.byref(code)):
            return None
        return int(code.value)

    def creation_time(self, handle: int) -> int | None:
        creation, exited, kernel, user = (self._wintypes.FILETIME() for _ in range(4))
        ref = self._ctypes.byref
        if not self._k32.GetProcessTimes(handle, ref(creation), ref(exited), ref(kernel), ref(user)):
            return None
        return (creation.dwHighDateTime << 32) | creation.dwLowDateTime

    def close(self, handle: int) -> None:
        self._k32.CloseHandle(handle)


def _windows_probe(pid: int, api: _Kernel32 | None = None) -> ProbeResult:
    try:
        kernel32 = api if api is not None else _CtypesKernel32()
    except (ImportError, AttributeError, OSError) as exc:
        return ProbeResult("unknown", detail=f"kernel32 unavailable: {exc.__class__.__name__}")
    handle, error = kernel32.open_process(pid)
    if handle is None:
        if error == _ERROR_INVALID_PARAMETER:
            return ProbeResult("absent", detail="no such process")
        return ProbeResult("unknown", detail=f"OpenProcess failed (error {error})")
    try:
        code = kernel32.exit_code(handle)
        if code is None:
            return ProbeResult("unknown", detail="GetExitCodeProcess failed")
        if code != _STILL_ACTIVE:
            return ProbeResult("absent", detail=f"process exited (code {code})")
        created = kernel32.creation_time(handle)
        if created is None:
            return ProbeResult("unknown", detail="GetProcessTimes failed")
        return ProbeResult("alive", start=str(created))
    finally:
        kernel32.close(handle)


# ---------------------------------------------------------------------------
# POSIX back end
# ---------------------------------------------------------------------------


def _proc_stat(pid: int, proc_root: Path) -> tuple[str, str] | None:
    """Return ``(state, starttime)`` from ``/proc/<pid>/stat``, or None when unavailable or unparsable."""

    try:
        text = (proc_root / str(pid) / "stat").read_text(encoding="ascii", errors="replace")
    except OSError:
        return None
    # The command name is parenthesised and may contain spaces and parentheses.
    tail = text.rpartition(")")[2].split()
    # tail[0] is the state (field 3); starttime is field 22, i.e. tail[19].
    if len(tail) < 20 or not tail[19].isdigit():
        return None
    return tail[0], tail[19]


def _posix_probe(
    pid: int,
    *,
    kill: Callable[[int, int], None] = os.kill,
    proc_root: Path = Path("/proc"),
) -> ProbeResult:
    try:
        kill(pid, 0)
    except ProcessLookupError:
        return ProbeResult("absent", detail="no such process")
    except PermissionError:
        pass  # exists, owned by another user
    except (OSError, OverflowError, ValueError) as exc:
        return ProbeResult("unknown", detail=f"kill probe failed: {exc.__class__.__name__}")
    stat = _proc_stat(pid, proc_root)
    if stat is None:
        return ProbeResult("alive", start=None, detail="start time unavailable")
    state, start = stat
    if state in ("Z", "X"):
        return ProbeResult("absent", detail=f"process is {'a zombie' if state == 'Z' else 'dead'}")
    return ProbeResult("alive", start=start)


def default_prober() -> Prober:
    return _windows_probe if os.name == "nt" else _posix_probe


def process_start_time(pid: int, *, prober: Prober | None = None) -> str | None:
    """The opaque start-time token of a live process, or None when it is absent or unreadable."""

    if type(pid) is not int or not 0 < pid <= _MAX_PID:
        return None
    result = (prober or default_prober())(pid)
    return result.start if result.state == "alive" else None


def is_process_alive(pid: int, *, prober: Prober | None = None) -> bool | None:
    """True when the process is running, False when it is provably gone, None when that cannot be told."""

    if type(pid) is not int or not 0 < pid <= _MAX_PID:
        return None
    state = (prober or default_prober())(pid).state
    return None if state == "unknown" else state == "alive"


def provably_dead(
    host: object,
    pid: object,
    pid_start: object,
    *,
    local_host: str | None = None,
    prober: Prober | None = None,
) -> LivenessVerdict:
    """Return a dead verdict only when the lock owner is provably gone; every doubt is not-dead."""

    if not isinstance(host, str) or not host:
        return LivenessVerdict(False, "legacy_lock", "no recorded host; operator confirmation required")
    if host != (local_host if local_host is not None else current_host()):
        return LivenessVerdict(False, "foreign_host", f"lock owner is on host {host!r}")
    if type(pid) is not int or not 0 < pid <= _MAX_PID:
        return LivenessVerdict(False, "invalid_pid", "the recorded pid is not a valid process id")
    result = (prober or default_prober())(pid)
    if result.state == "absent":
        return LivenessVerdict(True, "pid_absent", result.detail)
    if result.state != "alive":
        return LivenessVerdict(False, "unknown", result.detail)
    if pid_start is None or not isinstance(pid_start, str):
        return LivenessVerdict(False, "pid_start_unrecorded", "the process exists and no start time was recorded")
    if result.start is None:
        return LivenessVerdict(False, "start_unreadable", "the process exists and its start time cannot be read")
    if result.start != pid_start:
        return LivenessVerdict(True, "pid_start_mismatch", "the pid now belongs to a different process")
    return LivenessVerdict(False, "alive", "the recorded process is still running")
