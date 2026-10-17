"""Descendant-group quiescence and open-writer probes for the journaled runner (211-F, plan unit T5; hardening H13).

Regular-file capture has no end-of-file signal, so after the direct child exits
the shim must prove nothing is still writing to the journal streams:

* **descendant group**: Windows places the shim in a Job Object before it spawns
  the child (every descendant inherits the membership and, without
  ``JOB_OBJECT_LIMIT_BREAKAWAY_OK``, cannot leave it), so the job's process-id
  list *is* the descendant set; POSIX uses the child's process group (the child
  is spawned with ``start_new_session``). Membership that cannot be enumerated is
  ``None`` and never counts as quiescent.
* **escaped writers**: an empty group does not prove that no writer escaped it
  (``setsid`` on POSIX, a service/launcher on Windows). Windows therefore opens
  every journal stream with share mode 0 (which fails while any other handle is
  open), and Linux scans ``/proc/*/fd`` for links to the journal files. A
  platform with neither primitive reports ``unproven``.

Everything here is read-only apart from :meth:`DescendantGroup.kill_members`,
which only terminates processes that are members of the shim's own group/job.
"""

from __future__ import annotations

import os
import signal
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol

__all__ = [
    "QUIESCENCE_GRACE_SECONDS",
    "DescendantGroup",
    "GroupVerdict",
    "PosixGroup",
    "WindowsJob",
    "WriterVerdict",
    "enter_group",
    "probe_writers",
    "scan_proc_fds",
    "settle_group",
    "settle_writers",
]

QUIESCENCE_GRACE_SECONDS: Final = 5.0
_WINDOWS: Final = os.name == "nt"
_PROCESS_TERMINATE: Final = 0x0001
_JOB_OBJECT_BASIC_PROCESS_ID_LIST: Final = 3
_ERROR_MORE_DATA: Final = 234
_ERROR_SHARING_VIOLATION: Final = 32
_ERROR_FILE_NOT_FOUND: Final = 2
_GENERIC_READ: Final = 0x80000000
_OPEN_EXISTING: Final = 3
_FILE_ATTRIBUTE_NORMAL: Final = 0x80
_INITIAL_PID_CAPACITY: Final = 256


class DescendantGroup(Protocol):
    method: str

    def members(self) -> frozenset[int] | None:
        """The live members other than the caller, or ``None`` when they cannot be enumerated."""

    def kill_members(self) -> int:
        """Terminate the current members; returns how many terminations were issued."""


@dataclass(frozen=True)
class GroupVerdict:
    proven: bool
    method: str
    survivors_killed: int
    detail: str = ""


@dataclass(frozen=True)
class WriterVerdict:
    """``clean`` is True when no writer holds the files, False when one does, ``None`` when it cannot be told."""

    clean: bool | None
    method: str
    detail: str = ""


# ---------------------------------------------------------------------------
# Windows: Job Object membership (ctypes only)
# ---------------------------------------------------------------------------


class _Win32:
    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        self.ctypes = ctypes
        self.wintypes = wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k32.AssignProcessToJobObject.restype = wintypes.BOOL
        k32.GetCurrentProcess.argtypes = []
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.c_void_p,
        ]
        k32.QueryInformationJobObject.restype = wintypes.BOOL
        k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        k32.TerminateProcess.restype = wintypes.BOOL
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        k32.CloseHandle.restype = wintypes.BOOL
        k32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        k32.CreateFileW.restype = wintypes.HANDLE
        self.k32 = k32
        self.invalid_handle = ctypes.c_void_p(-1).value


class WindowsJob:
    """A Job Object the current process has joined; its pid list is the descendant set."""

    method = "job_object"

    def __init__(self, handle: int, api: _Win32) -> None:
        self._handle = handle
        self._api = api
        self._self_pid = os.getpid()

    @classmethod
    def enter_current_process(cls) -> WindowsJob | None:
        """Create a job and join it (before spawning any child); ``None`` when that is not possible."""

        try:
            api = _Win32()
            handle = api.k32.CreateJobObjectW(None, None)
            if not handle:
                return None
            if not api.k32.AssignProcessToJobObject(handle, api.k32.GetCurrentProcess()):
                api.k32.CloseHandle(handle)
                return None
        except (ImportError, AttributeError, OSError):
            return None
        return cls(int(handle), api)

    def _pids(self) -> frozenset[int] | None:
        api = self._api
        ctypes = api.ctypes
        capacity = _INITIAL_PID_CAPACITY
        for _ in range(4):

            class _PidList(ctypes.Structure):
                _fields_ = [
                    ("NumberOfAssignedProcesses", api.wintypes.DWORD),
                    ("NumberOfProcessIdsInList", api.wintypes.DWORD),
                    ("ProcessIdList", ctypes.c_size_t * capacity),
                ]

            buffer = _PidList()
            ctypes.set_last_error(0)
            ok = api.k32.QueryInformationJobObject(
                self._handle,
                _JOB_OBJECT_BASIC_PROCESS_ID_LIST,
                ctypes.byref(buffer),
                ctypes.sizeof(buffer),
                None,
            )
            if ok and buffer.NumberOfAssignedProcesses == buffer.NumberOfProcessIdsInList:
                return frozenset(buffer.ProcessIdList[: buffer.NumberOfProcessIdsInList])
            if not ok and ctypes.get_last_error() != _ERROR_MORE_DATA:
                return None
            capacity = max(capacity * 4, buffer.NumberOfAssignedProcesses + 16)
        return None

    def members(self) -> frozenset[int] | None:
        pids = self._pids()
        return None if pids is None else pids - {self._self_pid}

    def kill_members(self) -> int:
        pids = self.members() or frozenset()
        api = self._api
        killed = 0
        for pid in pids:
            handle = api.k32.OpenProcess(_PROCESS_TERMINATE, False, pid)
            if not handle:
                continue
            try:
                if api.k32.TerminateProcess(handle, 1):
                    killed += 1
            finally:
                api.k32.CloseHandle(handle)
        return killed


# ---------------------------------------------------------------------------
# POSIX: the child's process group
# ---------------------------------------------------------------------------


class PosixGroup:
    """The process group led by the (already reaped) child; ``killpg(pgid, 0)`` tests whether anything is left."""

    method = "process_group"

    def __init__(
        self,
        pgid: int,
        *,
        killpg: Callable[[int, int], None] | None = None,
    ) -> None:
        self._pgid = pgid
        self._killpg = killpg if killpg is not None else getattr(os, "killpg", None)

    def members(self) -> frozenset[int] | None:
        if self._killpg is None:
            return None
        try:
            self._killpg(self._pgid, 0)
        except ProcessLookupError:
            return frozenset()
        except PermissionError:
            return frozenset({self._pgid})  # exists, owned by another user
        except OSError:
            return None
        return frozenset({self._pgid})

    def kill_members(self) -> int:
        if self._killpg is None:
            return 0
        try:
            self._killpg(self._pgid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            return 0
        return 1


def enter_group(child_pid: int | None = None) -> DescendantGroup | None:
    """Windows: join a fresh job now (call before the child spawns). POSIX: the group of ``child_pid``."""

    if _WINDOWS:
        return WindowsJob.enter_current_process()
    return PosixGroup(child_pid) if child_pid is not None else None


# ---------------------------------------------------------------------------
# Open-writer probes
# ---------------------------------------------------------------------------


def _exclusive_open_held(path: Path) -> WriterVerdict:
    try:
        api = _Win32()
    except (ImportError, AttributeError, OSError):
        return WriterVerdict(None, "unavailable", "kernel32 is unavailable")
    ctypes = api.ctypes
    ctypes.set_last_error(0)
    handle = api.k32.CreateFileW(
        str(path), _GENERIC_READ, 0, None, _OPEN_EXISTING, _FILE_ATTRIBUTE_NORMAL, None
    )
    if handle is not None and int(handle) != api.invalid_handle:
        api.k32.CloseHandle(handle)
        return WriterVerdict(True, "exclusive_open")
    error = ctypes.get_last_error()
    if error == _ERROR_SHARING_VIOLATION:
        return WriterVerdict(False, "exclusive_open", f"{path.name} is held open by another process")
    if error == _ERROR_FILE_NOT_FOUND:
        return WriterVerdict(None, "exclusive_open", f"{path.name} is missing")
    return WriterVerdict(None, "exclusive_open", f"{path.name}: CreateFileW failed (error {error})")


def scan_proc_fds(
    paths: Sequence[Path],
    *,
    proc_root: Path = Path("/proc"),
    self_pid: int | None = None,
    listdir: Callable[[str], list[str]] = os.listdir,
    readlink: Callable[[str], str] = os.readlink,
    stat_uid: Callable[[str], int] = lambda path: os.stat(path).st_uid,
    my_uid: int | None = None,
) -> WriterVerdict:
    """Linux: look for any other process holding a descriptor linked to one of ``paths``.

    An fd table we cannot read only counts as unproven when the process runs under our own uid:
    a foreign-uid process cannot hold our 0600 journal files open.
    """

    me = str(self_pid if self_pid is not None else os.getpid())
    if my_uid is None:
        my_uid = os.getuid() if hasattr(os, "getuid") else -1
    wanted = {os.path.realpath(path) for path in paths}
    try:
        pids = [name for name in listdir(str(proc_root)) if name.isdigit() and name != me]
    except OSError as exc:
        return WriterVerdict(None, "proc_fd_scan", f"cannot list {proc_root}: {exc.__class__.__name__}")
    unreadable = 0
    for pid in pids:
        fd_dir = str(proc_root / pid / "fd")
        try:
            descriptors = listdir(fd_dir)
        except FileNotFoundError:
            continue  # the process exited during the scan
        except OSError as exc:
            if isinstance(exc, PermissionError):
                try:
                    if stat_uid(str(proc_root / pid)) != my_uid:
                        continue
                except OSError:
                    pass
            unreadable += 1
            continue
        for descriptor in descriptors:
            try:
                target = readlink(f"{fd_dir}/{descriptor}")
            except OSError:
                continue
            if target.endswith(" (deleted)"):
                target = target[: -len(" (deleted)")]
            if os.path.realpath(target) in wanted:
                return WriterVerdict(False, "proc_fd_scan", f"process {pid} holds a journal file open")
    if unreadable:
        return WriterVerdict(None, "proc_fd_scan", f"{unreadable} process fd tables were unreadable")
    return WriterVerdict(True, "proc_fd_scan")


def probe_writers(paths: Sequence[Path]) -> WriterVerdict:
    """One open-writer probe over ``paths`` using the strongest primitive the platform offers."""

    if _WINDOWS:
        for path in paths:
            verdict = _exclusive_open_held(path)
            if verdict.clean is not True:
                return verdict
        return WriterVerdict(True, "exclusive_open")
    if os.path.isdir("/proc/self/fd"):
        return scan_proc_fds(paths)
    return WriterVerdict(None, "unavailable", "no open-writer primitive on this platform")


# ---------------------------------------------------------------------------
# Settling (bounded polling)
# ---------------------------------------------------------------------------


def settle_group(
    group: DescendantGroup | None,
    *,
    grace: float = QUIESCENCE_GRACE_SECONDS,
    poll: float = 0.1,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> GroupVerdict:
    """Prove the descendant group is empty; kill survivors after ``grace`` and report the capture unproven."""

    if group is None:
        return GroupVerdict(False, "unavailable", 0, "no descendant-group primitive is available")
    members = group.members()
    if members is None:
        return GroupVerdict(False, group.method, 0, "group membership cannot be enumerated")
    deadline = clock() + grace
    while members and clock() < deadline:
        sleep(poll)
        members = group.members()
        if members is None:
            return GroupVerdict(False, group.method, 0, "group membership cannot be enumerated")
    if not members:
        return GroupVerdict(True, group.method, 0)
    killed = group.kill_members()
    for _ in range(20):
        remaining = group.members()
        if not remaining:
            break
        sleep(poll)
    return GroupVerdict(False, group.method, killed, "descendants outlived the direct child and were killed")


def settle_writers(
    paths: Sequence[Path],
    *,
    grace: float = QUIESCENCE_GRACE_SECONDS,
    poll: float = 0.1,
    probe: Callable[[Sequence[Path]], WriterVerdict] = probe_writers,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> WriterVerdict:
    """Retry the open-writer probe for up to ``grace`` seconds; a persistent writer or an unproven platform fails."""

    deadline = clock() + grace
    verdict = probe(paths)
    while verdict.clean is False and clock() < deadline:
        sleep(poll)
        verdict = probe(paths)
    return verdict
