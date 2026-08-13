"""Atomic single-session guard lock (118.005-T; extended by 118.006-T).

Enforces exactly ONE active supervised session per workspace via a
GUARD/RECORD split:

* **GUARD FILE** (``<workspace>/.autoharness/supervise/session.guard``) --
  stable, NEVER deleted. Created once, idempotently, if absent. The
  exclusion mechanism is an OS-backed advisory/mandatory lock held on an
  open handle to this file for the session lifetime: ``msvcrt.locking``
  over a fixed byte range on Windows, ``fcntl.flock(..., LOCK_EX|LOCK_NB)``
  on POSIX. ``O_CREAT|O_EXCL`` is never used as the locking backend --
  provisioning (creating the file if absent) is a separate, idempotent step
  from acquiring exclusivity.
* **RECORD FILE** (``<workspace>/.autoharness/supervise/session.record``) --
  separate, removable. Holds PID, process start-time, and session id ONLY.
  It carries no exclusion semantics itself.

Platform notes and limitations (documented per shipment constraints):

* Windows file-identity checks use ``os.stat().st_ino``/``st_dev``, which
  requires Python 3.12+ on NTFS to return a real file-id-based inode value
  (older Python/NTFS combinations may return ``0`` and cannot distinguish
  a replaced file from the original by inode alone; this module requires
  Python 3.12+ per ``pyproject.toml`` ``requires-python`` and documents this
  as a best-effort identity check, not a cryptographic guarantee).
* Windows process start-time (118.006-T) uses ``ctypes``/``kernel32``
  ``OpenProcess``/``GetProcessTimes`` (FILETIME creation time) as a
  best-effort, stdlib-only proxy. POSIX uses ``/proc/<pid>/stat`` field 22
  (``starttime``, ticks since boot) when ``/proc`` is available. When
  neither can be read, liveness is INDETERMINATE and callers fail closed
  (treat as live).
"""

from __future__ import annotations

import contextlib
import enum
import json
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from autoharness.supervise.errors import LockError

try:
    import msvcrt  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - exercised only off-Windows
    msvcrt = None  # type: ignore[assignment]

fcntl = None  # type: ignore[assignment]
if sys.platform != "win32":
    try:
        import fcntl  # type: ignore[import-not-found,no-redef]
    except ImportError:  # pragma: no cover - exotic POSIX without fcntl
        fcntl = None  # type: ignore[assignment]

PathLike = Union[str, "os.PathLike[str]"]

# Guard/record locations, relative to the workspace root.
GUARD_RELATIVE_PATH = Path(".autoharness") / "supervise" / "session.guard"
RECORD_RELATIVE_PATH = Path(".autoharness") / "supervise" / "session.record"

# Fixed 1-byte lock range. The guard file's sole purpose is to host this
# lock; its content is never read as data (record data lives in RECORD_FILE).
_LOCK_BYTE_RANGE = 1


class SessionLockRefused(LockError):
    """Raised when guard-lock acquisition is refused due to live contention.

    This is a DISTINCT, fail-closed outcome from a generic :class:`LockError`
    -- callers must be able to tell "another session legitimately holds this
    lock" apart from "the locking subsystem itself is broken" (e.g. a path
    containment violation, or an unavailable locking primitive).
    """


def _resolve_contained_path(workspace_root: PathLike, relative: PathLike) -> Path:
    """Resolve ``relative`` under ``workspace_root``, aborting on any escape.

    Raises :class:`LockError` (rather than silently clamping the path) if
    the resolved path is not contained within ``workspace_root``. This check
    runs before any write to guard/record paths.

    The candidate is normalized with a purely lexical ``os.path.normpath``
    rather than a second filesystem-touching ``Path.resolve()`` call. A
    second ``resolve()`` on the joined (root / relative) path re-invokes
    ``GetFinalPathNameByHandleW`` on Windows, whose returned form (with or
    without the extended-length ``\\\\?\\`` prefix) can depend on how much of
    the path currently exists on disk -- under the real parallel-contender
    lock test, one contender creating ``.autoharness/supervise`` mid-race can
    flip that prefix for a second contender's candidate resolution while
    ``root`` (resolved once, independent of any child directory's existence)
    stays unprefixed, making an otherwise-identical, non-escaping path spuriously
    fail the containment check. Lexical normalization avoids re-touching the
    filesystem for the candidate while still collapsing ``..``/``.`` segments,
    so a genuine escape is still caught.

    ``relative``'s separators are normalized to ``/`` BEFORE joining,
    regardless of the platform this code is currently running on. Without
    this, a traversal sequence expressed with the OTHER platform's separator
    convention (e.g. a Windows-style ``"..\\..\\evil"`` string evaluated on a
    POSIX host, where backslash is an ordinary filename character rather than
    a separator) would silently stay "contained" -- not because it is safe,
    but only because the current platform happens not to interpret that
    character as a path separator. The exact same input string must be
    rejected identically on every platform for a security-relevant
    containment check to mean anything (surfaced by CI running this
    module's callers' tests on Linux; 128-S).
    """

    root = Path(workspace_root).resolve()
    normalized_relative = str(relative).replace("\\", "/")
    candidate = Path(os.path.normpath(str(root / Path(normalized_relative))))
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise LockError(
            f"path {relative!s} resolves outside workspace root {root}: {candidate}"
        ) from exc
    return candidate


def ensure_ignored(workspace_root: PathLike, *relative_paths: PathLike) -> Path:
    """Idempotently ensure ``.autoharness/.gitignore`` covers ``relative_paths``.

    Creates the ignore file if absent. Appends any missing entries
    additively. NEVER rewrites or removes unrelated existing content in the
    file.

    Returns the path to the ignore file.
    """

    autoharness_dir = _resolve_contained_path(workspace_root, Path(".autoharness"))
    autoharness_dir.mkdir(parents=True, exist_ok=True)
    ignore_path = autoharness_dir / ".gitignore"

    existing_lines: list[str] = []
    if ignore_path.exists():
        existing_lines = ignore_path.read_text(encoding="utf-8").splitlines()
    existing_set = set(existing_lines)

    entries_to_add = []
    for relative_path in relative_paths:
        entry = str(relative_path).replace("\\", "/")
        if entry not in existing_set:
            entries_to_add.append(entry)
            existing_set.add(entry)

    if entries_to_add:
        needs_leading_newline = bool(existing_lines) and existing_lines[-1] != ""
        with ignore_path.open("a", encoding="utf-8") as handle:
            if needs_leading_newline:
                handle.write("\n")
            for entry in entries_to_add:
                handle.write(entry + "\n")
    elif not ignore_path.exists():
        ignore_path.touch()

    return ignore_path


def get_file_identity(path: PathLike) -> tuple[int, int]:
    """Return a ``(st_dev, st_ino)`` pair identifying the file on disk.

    Used to assert the GUARD FILE is never deleted/replaced/recreated.
    See the module docstring for the Windows/Python-version caveat.
    """

    stat_result = os.stat(path)
    return (stat_result.st_dev, stat_result.st_ino)


def _ensure_guard_file(guard_path: Path) -> None:
    """Idempotently create the guard file if absent. Never deletes it."""

    guard_path.parent.mkdir(parents=True, exist_ok=True)
    if not guard_path.exists():
        # A single placeholder byte so the fixed 1-byte lock range has
        # backing content on platforms that require it. This file is never
        # read as data.
        guard_path.write_bytes(b"\0")


def _lock_file_handle(handle) -> None:  # noqa: ANN001 - stdlib file object
    """Attempt a non-blocking exclusive lock over the fixed byte range.

    Raises :class:`SessionLockRefused` when another process already holds
    the lock.
    """

    if sys.platform == "win32":
        if msvcrt is None:  # pragma: no cover - defensive
            raise LockError("msvcrt unavailable; cannot acquire Windows guard lock")
        try:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, _LOCK_BYTE_RANGE)
        except OSError as exc:
            raise SessionLockRefused(
                "session guard lock is held by another session"
            ) from exc
    else:
        if fcntl is None:
            raise LockError("fcntl unavailable; cannot acquire POSIX guard lock")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise SessionLockRefused(
                "session guard lock is held by another session"
            ) from exc


def _unlock_file_handle(handle) -> None:  # noqa: ANN001 - stdlib file object
    """Release the guard lock on ``handle``. Idempotent: never raises."""

    if sys.platform == "win32":
        if msvcrt is None:  # pragma: no cover - defensive
            return
        try:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, _LOCK_BYTE_RANGE)
        except (OSError, ValueError):
            pass  # already unlocked / handle already invalid: idempotent no-op
    else:
        if fcntl is None:
            return
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except (OSError, ValueError):
            pass


def _posix_process_start_time(pid: int) -> Optional[float]:
    """Best-effort POSIX process start time (``/proc/<pid>/stat`` field 22).

    Returns ``None`` when indeterminate (no ``/proc``, permission denied,
    unparseable content).
    """

    stat_path = Path(f"/proc/{pid}/stat")
    try:
        content = stat_path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, OSError):
        return None
    try:
        # comm (field 2) may itself contain spaces/parens; split after the
        # last ")" to reliably reach the space-delimited fields from state
        # (field 3) onward. starttime is field 22, i.e. index 19 from state.
        after_comm = content.rsplit(")", 1)[1]
        fields = after_comm.split()
        starttime_ticks = int(fields[19])
        return float(starttime_ticks)
    except (IndexError, ValueError):
        return None


def _windows_process_start_time(pid: int) -> Optional[float]:
    """Best-effort Windows process start time via kernel32 GetProcessTimes.

    Returns ``None`` when indeterminate (process not found, access denied,
    API failure).
    """

    try:
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return None
        try:
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel_time = wintypes.FILETIME()
            user_time = wintypes.FILETIME()
            ok = kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel_time),
                ctypes.byref(user_time),
            )
            if not ok:
                return None
            value = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
            return float(value)
        finally:
            kernel32.CloseHandle(handle)
    except Exception:  # pragma: no cover - defensive: any ctypes failure is indeterminate
        return None


def _process_start_time(pid: int) -> Optional[float]:
    """Best-effort process start time. ``None`` means indeterminate.

    Used both to populate ``SessionRecord.start_time`` on acquisition
    (118.005-T) and, later, to detect a start-time mismatch indicating a
    recycled PID (118.006-T's :func:`diagnose_liveness`).
    """

    if sys.platform == "win32":
        return _windows_process_start_time(pid)
    return _posix_process_start_time(pid)


@dataclass(frozen=True)
class SessionRecord:
    """RECORD FILE payload: PID, process start-time, and session id ONLY."""

    pid: int
    start_time: float
    session_id: str

    def to_dict(self) -> dict[str, object]:
        return {"pid": self.pid, "start_time": self.start_time, "session_id": self.session_id}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "SessionRecord":
        return cls(
            pid=int(data["pid"]),  # type: ignore[arg-type]
            start_time=float(data["start_time"]),  # type: ignore[arg-type]
            session_id=str(data["session_id"]),
        )


class SessionLock:
    """Context manager guarding at most one active supervised session.

    Usage::

        with SessionLock(workspace_root) as lock:
            ...  # exactly one process reaches here per workspace at a time

    Or explicitly::

        lock = SessionLock(workspace_root)
        lock.acquire()
        try:
            ...
        finally:
            lock.release()

    Acquisition is FAIL CLOSED: contention raises :class:`SessionLockRefused`
    rather than blocking or silently succeeding. Release is idempotent and
    crash-safe -- calling it twice, or calling it when the lock was never
    held, never raises. Release drops the guard LOCK and MAY remove the
    RECORD file, but NEVER deletes/renames/truncates the GUARD FILE itself.
    """

    def __init__(
        self,
        workspace_root: PathLike,
        *,
        session_id: Optional[str] = None,
        guard_relative: PathLike = GUARD_RELATIVE_PATH,
        record_relative: PathLike = RECORD_RELATIVE_PATH,
    ) -> None:
        self.workspace_root = Path(workspace_root)
        # Containment is checked here, before any write -- an escaping
        # relative path raises immediately rather than being clamped.
        self.guard_path = _resolve_contained_path(self.workspace_root, guard_relative)
        self.record_path = _resolve_contained_path(self.workspace_root, record_relative)
        self.session_id = session_id or uuid.uuid4().hex
        self._handle = None
        self._held = False

    @property
    def held(self) -> bool:
        return self._held

    def acquire(self) -> "SessionLock":
        if self._held:
            return self  # idempotent: acquiring an already-held lock is a no-op

        _ensure_guard_file(self.guard_path)
        ensure_ignored(
            self.workspace_root,
            GUARD_RELATIVE_PATH.relative_to(".autoharness").as_posix(),
            RECORD_RELATIVE_PATH.relative_to(".autoharness").as_posix(),
        )

        handle = open(self.guard_path, "r+b")
        try:
            _lock_file_handle(handle)
        except SessionLockRefused:
            handle.close()
            raise

        self._handle = handle
        self._held = True

        record = SessionRecord(
            pid=os.getpid(), start_time=_process_start_time(os.getpid()) or 0.0,
            session_id=self.session_id,
        )
        try:
            self.record_path.write_text(json.dumps(record.to_dict()), encoding="utf-8")
        except Exception:
            # Record construction/write failed (permission error, full disk,
            # interrupted write, ...) while the OS guard is already held.
            # Never strand the guard locked with no matching record: release
            # it and reset state before re-raising so the caller sees a clean
            # failure, not a leaked lock.
            with contextlib.suppress(OSError):
                _unlock_file_handle(self._handle)
            with contextlib.suppress(OSError):
                self._handle.close()
            self._handle = None
            self._held = False
            raise
        return self

    def release(self) -> None:
        if not self._held or self._handle is None:
            return  # idempotent: release when not held is a safe no-op

        try:
            # Delete the RECORD while this process still exclusively holds
            # the guard. Unlocking the guard FIRST would open a window where
            # a waiting contender acquires the guard and writes its own new
            # record before this method deletes "the" record -- deleting
            # after that point would destroy the new live holder's metadata,
            # not this session's own (now-stale) one.
            with contextlib.suppress(FileNotFoundError, OSError):
                if self.record_path.exists():
                    self.record_path.unlink()
        finally:
            with contextlib.suppress(OSError):
                _unlock_file_handle(self._handle)
            with contextlib.suppress(OSError):
                self._handle.close()
            self._handle = None
            self._held = False

    def __enter__(self) -> "SessionLock":
        return self.acquire()

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.release()


def acquire(workspace_root: PathLike, *, session_id: Optional[str] = None) -> SessionLock:
    """Functional convenience wrapper: construct and acquire a SessionLock."""

    lock = SessionLock(workspace_root, session_id=session_id)
    lock.acquire()
    return lock


# ---------------------------------------------------------------------------
# 118.006-T: liveness, stale-record lifecycle, and force_unlock
# ---------------------------------------------------------------------------


def _pid_exists(pid: int) -> Optional[bool]:
    """Best-effort liveness check. Returns ``None`` when indeterminate."""

    if sys.platform == "win32":
        return _windows_pid_exists(pid)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # process exists; we simply cannot signal it
    except OSError:
        return None


def _windows_pid_exists(pid: int) -> Optional[bool]:
    try:
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        ERROR_INVALID_PARAMETER = 87
        STILL_ACTIVE = 259
        # ``use_last_error=True`` is required for ``ctypes.get_last_error()``
        # to reflect this call's actual ``GetLastError()`` value -- the
        # shared ``ctypes.windll.kernel32`` handle does not track it.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            last_error = ctypes.get_last_error()
            if last_error == ERROR_INVALID_PARAMETER:
                return False
            return None  # indeterminate (e.g. access denied on a live process)
        try:
            # A successful `OpenProcess` alone does NOT mean the process is
            # still running: on Windows, a process object (and therefore its
            # PID) can remain a valid `OpenProcess` target for a time after
            # the process has already exited, as long as any handle to it
            # is still outstanding anywhere in the system (this is routinely
            # observed immediately after a parent's own `TerminateProcess`/
            # `Popen.kill()` + `wait()`, before the OS fully tears down the
            # process object). `GetExitCodeProcess` is the authoritative
            # check: `STILL_ACTIVE` (259) means genuinely running; any other
            # value means the process has already exited and this PID must
            # be treated as dead, never LIVE.
            exit_code = ctypes.c_ulong(0)
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return None  # indeterminate -- could not query exit status
            return exit_code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    except Exception:  # pragma: no cover - defensive
        return None


class Liveness(enum.Enum):
    """Tri-state liveness verdict for a diagnosed session record."""

    LIVE = "live"
    STALE = "stale"
    INDETERMINATE = "indeterminate"


def diagnose_liveness(record: SessionRecord) -> Liveness:
    """Diagnose whether ``record`` refers to a still-live session.

    FAIL CLOSED: any indeterminate signal (liveness or start-time cannot be
    read) resolves to :attr:`Liveness.INDETERMINATE`, which callers must
    treat as LIVE (never eligible for force-unlock).
    """

    alive = _pid_exists(record.pid)
    if alive is None:
        return Liveness.INDETERMINATE
    if not alive:
        return Liveness.STALE  # dead PID

    current_start = _process_start_time(record.pid)
    if current_start is None:
        return Liveness.INDETERMINATE

    # A start-time mismatch means the PID was recycled by an unrelated
    # process after the recorded session ended -- treat as stale.
    if abs(current_start - record.start_time) > 1e-6:
        return Liveness.STALE

    return Liveness.LIVE


def is_stale_eligible_for_force_unlock(liveness: Liveness) -> bool:
    """Whether a diagnosed :class:`Liveness` verdict is eligible for cleanup.

    Only :attr:`Liveness.STALE` is eligible. Both :attr:`Liveness.LIVE` and
    :attr:`Liveness.INDETERMINATE` are NOT eligible -- this is the
    fail-closed rule "when liveness cannot be determined, treat as LIVE and
    REFUSE" made directly testable as a single decision point, rather than
    left implicit in caller prose.
    """

    return liveness is Liveness.STALE


class ForceUnlockOutcome(enum.Enum):
    """Outcome of a :func:`force_unlock` attempt."""

    REMOVED = "removed"
    REFUSED_LIVE = "refused_live"
    RECORD_CHANGED = "record_changed"
    NOTHING_TO_REMOVE = "nothing_to_remove"


def read_record(record_path: Path) -> Optional[SessionRecord]:
    """Read and parse the RECORD FILE, or ``None`` if absent/unparsable."""

    if not record_path.exists():
        return None
    try:
        payload = json.loads(record_path.read_text(encoding="utf-8"))
        return SessionRecord.from_dict(payload)
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return None


def force_unlock(
    workspace_root: PathLike,
    expected_record: SessionRecord,
    *,
    guard_relative: PathLike = GUARD_RELATIVE_PATH,
    record_relative: PathLike = RECORD_RELATIVE_PATH,
) -> ForceUnlockOutcome:
    """Remove a diagnosed-stale RECORD file. NEVER touches the GUARD file.

    Both normal session acquisition and ``force_unlock`` take the SAME
    underlying guard-lock primitive before touching record metadata:

    1. Attempt a non-blocking guard-lock acquisition. If it FAILS (a live
       session holds it), REFUSE immediately -- the record is never read or
       touched.
    2. If it SUCCEEDS, re-read the record INSIDE this critical section and
       re-validate it still matches ``expected_record`` (the record
       previously diagnosed as stale by the caller via
       :func:`diagnose_liveness`), AND independently re-diagnose that same
       on-disk record's liveness fresh, inside this same critical section.
       Only when the record matches AND the fresh diagnosis is
       :attr:`Liveness.STALE` is the RECORD FILE removed. The guard lock --
       taken here as a short-lived cleanup acquisition, distinct from a
       long-lived session acquisition -- is always released before
       returning.

    The caller is expected to have called :func:`diagnose_liveness` on
    ``expected_record`` and confirmed it is not :attr:`Liveness.LIVE` (or
    :attr:`Liveness.INDETERMINATE`) before calling this function, but this
    function does NOT merely trust that earlier diagnosis: it re-validates
    identity AND re-diagnoses liveness itself, inside the critical section,
    as the single authoritative enforcement point. This is defense in depth
    against a caller bug, a stale/skipped precondition check, or any
    TOCTOU window between the caller's diagnosis and this call -- both
    :attr:`Liveness.LIVE` and :attr:`Liveness.INDETERMINATE` are always
    refused here regardless of what the caller already believed.
    """

    root = Path(workspace_root)
    guard_path = _resolve_contained_path(root, guard_relative)
    record_path = _resolve_contained_path(root, record_relative)

    _ensure_guard_file(guard_path)

    handle = open(guard_path, "r+b")
    try:
        try:
            _lock_file_handle(handle)
        except SessionLockRefused:
            return ForceUnlockOutcome.REFUSED_LIVE

        # --- critical section: this process exclusively holds the guard ---
        current = read_record(record_path)
        if current is None:
            return ForceUnlockOutcome.NOTHING_TO_REMOVE
        if current != expected_record:
            return ForceUnlockOutcome.RECORD_CHANGED

        # Defense in depth: do not rely SOLELY on the caller having called
        # diagnose_liveness() before invoking this function. Re-diagnose the
        # matching on-disk record fresh, inside this same critical section,
        # and refuse to remove a record that is LIVE or INDETERMINATE
        # regardless of what the caller already believed. 118.006-T requires
        # BOTH states to always be refused; this function is the single
        # authoritative enforcement point for that, not merely a trusting
        # executor of an earlier diagnosis.
        verdict = diagnose_liveness(current)
        if verdict is not Liveness.STALE:
            return ForceUnlockOutcome.REFUSED_LIVE

        record_path.unlink()
        return ForceUnlockOutcome.REMOVED
        # --- end critical section ---
    finally:
        _unlock_file_handle(handle)
        with contextlib.suppress(OSError):
            handle.close()

