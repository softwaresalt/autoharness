"""Optional PTY-backed child process backend, with graceful degradation (119.002-T).

Implements the SAME ``ChildProcess`` protocol as
:mod:`autoharness.supervise.process`:

* :class:`PtyChildProcess` -- POSIX PTY backend using the stdlib ``pty``
  module (``pty.fork()``), giving the child a real pseudo-terminal while
  still letting the supervisor capture its output.
* :class:`WinPtyChildProcess` -- Windows PTY backend built on the OPTIONAL
  third-party ``pywinpty`` package (``import winpty``). Genuinely optional:
  this module MUST import cleanly and degrade gracefully when ``pywinpty``
  is not installed, which is the expected state in most environments
  (including this one).

Both PTY-module imports are GUARDED at module load time (``try/except
ImportError``) so importing this module never raises merely because a
platform lacks the corresponding PTY facility.

**F29 degrade-to-inherited-stdio contract (hard requirement)**:
:func:`create_pty_or_inherited_child_process` attempts real PTY
construction and, on ANY failure or unavailability, returns an
:class:`~autoharness.supervise.process.InheritStdioChildProcess` instance
instead -- NEVER a
:class:`~autoharness.supervise.process.PipeChildProcess`. The returned
warning string is non-``None`` exactly when degraded, and ``None`` exactly
when a real PTY backend was used. The factory itself never spawns the
child; like every other backend constructor in this package, construction
and ``spawn()`` remain separate steps.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import time
from typing import Optional, Sequence, Tuple

from autoharness.supervise.process import ChildProcess, InheritStdioChildProcess

# Guarded imports: importing this module must never raise merely because a
# platform lacks the corresponding PTY facility.
try:
    import pty as _pty  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - exercised on Windows
    _pty = None  # type: ignore[assignment]

try:
    import winpty as _winpty  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - exercised whenever pywinpty is absent
    _winpty = None  # type: ignore[assignment]


def _posix_pty_available() -> bool:
    """Whether the stdlib ``pty`` module is usable on this platform."""

    return sys.platform != "win32" and _pty is not None


def _winpty_available() -> bool:
    """Whether the optional ``pywinpty`` package is importable."""

    return sys.platform == "win32" and _winpty is not None


class PtyChildProcess:
    """POSIX PTY backend built on the stdlib ``pty`` module.

    Uses ``pty.fork()`` to give the child a real pseudo-terminal while the
    parent retains a readable/writable master file descriptor. Exit status
    is returned UNMODIFIED via ``os.waitpid`` decoding (``WEXITSTATUS`` for
    normal exit; the negative signal number for signal termination, matching
    the ``subprocess`` module's own convention).
    """

    supports_output_capture: bool = True

    def __init__(self, argv: Sequence[str]) -> None:
        self._argv: tuple[str, ...] = tuple(argv)
        self._pid: Optional[int] = None
        self._master_fd: Optional[int] = None
        self._exit_code: Optional[int] = None

    @property
    def argv(self) -> tuple[str, ...]:
        return self._argv

    @property
    def pid(self) -> Optional[int]:
        return self._pid

    def spawn(self) -> None:
        if _pty is None:  # pragma: no cover - guarded by callers/factory
            raise RuntimeError("stdlib pty module is unavailable on this platform")
        pid, master_fd = _pty.fork()
        if pid == 0:
            # Child branch: exec argv verbatim, never through a shell.
            try:
                os.execvp(self._argv[0], list(self._argv))
            except OSError:
                os._exit(127)
        self._pid = pid
        self._master_fd = master_fd

    def read(self) -> Optional[str]:
        if self._master_fd is None:
            raise RuntimeError("cannot read before spawn()")
        try:
            data = os.read(self._master_fd, 4096)
        except OSError:
            # EIO is the conventional POSIX signal that the slave side of
            # the PTY has closed -- treat exactly like EOF.
            return None
        if not data:
            return None
        return data.decode("utf-8", errors="replace")

    def write(self, data: bytes) -> None:
        if self._master_fd is None:
            raise RuntimeError("cannot write before spawn()")
        os.write(self._master_fd, data)

    def signal(self, sig: int) -> None:
        if self._pid is None:
            raise RuntimeError("cannot signal before spawn()")
        os.kill(self._pid, sig)

    def wait(self, timeout: Optional[float] = None) -> int:
        if self._pid is None:
            raise RuntimeError("cannot wait before spawn()")
        if self._exit_code is not None:
            return self._exit_code
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            reaped_pid, status = os.waitpid(self._pid, os.WNOHANG)
            if reaped_pid != 0:
                if os.WIFEXITED(status):
                    self._exit_code = os.WEXITSTATUS(status)
                elif os.WIFSIGNALED(status):
                    self._exit_code = -os.WTERMSIG(status)
                else:  # pragma: no cover - defensive, unreachable in practice
                    self._exit_code = status
                return self._exit_code
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(f"child pid {self._pid} did not exit within {timeout}s")
            time.sleep(0.01)

    def close(self) -> None:
        """Release resources and reap the child, avoiding a zombie.

        128-S review remediation: the previous implementation only closed
        the master file descriptor without terminating/waiting for the
        child. When cancellation calls :meth:`signal` followed by
        :meth:`close`, a child that has not yet exited could remain
        running or become an unreaped zombie -- this now mirrors the
        pipe/inherited-stdio backends' terminate/wait/kill sequence before
        releasing the file descriptor.
        """

        if self._pid is not None and self._exit_code is None:
            with contextlib.suppress(ProcessLookupError):
                os.kill(self._pid, signal.SIGTERM)
            try:
                self.wait(timeout=5)
            except TimeoutError:
                # Genuinely still running after the bounded wait: escalate.
                with contextlib.suppress(ProcessLookupError):
                    os.kill(self._pid, signal.SIGKILL)
                with contextlib.suppress(TimeoutError, ChildProcessError):
                    self.wait(timeout=5)
            except ChildProcessError:
                # 128-S review remediation: ChildProcessError from
                # os.waitpid means THIS PID IS NO LONGER OUR WAITABLE
                # CHILD (e.g. already reaped by a SIGCHLD handler or some
                # other independent race) -- it is NOT evidence the child
                # is still running. Conflating it with TimeoutError and
                # escalating to SIGKILL sends a kill signal to a bare PID
                # number that the OS may have already reused for an
                # entirely unrelated process. There is nothing left for
                # THIS backend to reap, so no further action is taken.
                pass
        if self._master_fd is not None:
            with contextlib.suppress(OSError):
                os.close(self._master_fd)
            self._master_fd = None


class WinPtyChildProcess:
    """Windows PTY backend built on the OPTIONAL ``pywinpty`` package.

    Only ever constructed after :func:`_winpty_available` confirms
    ``pywinpty`` imported successfully; callers (the factory below) must
    never construct this class when ``_winpty`` is ``None``.
    """

    supports_output_capture: bool = True

    def __init__(self, argv: Sequence[str]) -> None:
        self._argv: tuple[str, ...] = tuple(argv)
        self._pty = None
        self._exit_code: Optional[int] = None

    @property
    def argv(self) -> tuple[str, ...]:
        return self._argv

    @property
    def pid(self) -> Optional[int]:
        return getattr(self._pty, "pid", None) if self._pty is not None else None

    def spawn(self) -> None:
        if _winpty is None:  # pragma: no cover - guarded by callers/factory
            raise RuntimeError("pywinpty is not installed")
        # pywinpty's PtyProcess.spawn takes a single command-line string; it
        # performs its own internal quoting. We build that string via
        # subprocess.list2cmdline solely to preserve argv's exact tokens as
        # separate arguments -- this is NOT shell re-interpolation, it is the
        # documented, argv-preserving way to hand a token list to a Win32
        # CreateProcess-style API that only accepts one command-line string.
        cmdline = subprocess.list2cmdline(list(self._argv))
        self._pty = _winpty.PtyProcess.spawn(cmdline)

    def read(self) -> Optional[str]:
        if self._pty is None:
            raise RuntimeError("cannot read before spawn()")
        try:
            data = self._pty.read(4096)
        except EOFError:
            return None
        if not data:
            return None
        return data

    def write(self, data: bytes) -> None:
        if self._pty is None:
            raise RuntimeError("cannot write before spawn()")
        text = data.decode("utf-8") if isinstance(data, bytes) else data
        self._pty.write(text)

    def signal(self, sig: int) -> None:
        # pywinpty has no arbitrary POSIX-signal-delivery API; terminate is
        # the closest available analog and is documented as such here.
        if self._pty is None:
            raise RuntimeError("cannot signal before spawn()")
        self._pty.terminate(force=True)

    def wait(self, timeout: Optional[float] = None) -> int:
        """Block until the child exits; return its REAL exit code, unmodified.

        H3 exit-status fidelity is a hard invariant (119.001-T): if
        ``pywinpty`` cannot report a real ``exitstatus`` after the process
        is no longer alive, that is reported as an error -- NEVER silently
        mapped to ``0``/success, which would fabricate a successful exit
        for what may be a crashed or killed child (128-S review
        remediation).
        """

        if self._pty is None:
            raise RuntimeError("cannot wait before spawn()")
        deadline = None if timeout is None else time.monotonic() + timeout
        while self._pty.isalive():
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(f"pywinpty child did not exit within {timeout}s")
            time.sleep(0.01)
        self._exit_code = self._pty.exitstatus
        if self._exit_code is None:
            raise RuntimeError(
                "pywinpty reported exitstatus=None after the child was no longer "
                "alive; the real exit code is unknown, so it cannot be reported "
                "-- fabricating a successful (0) exit code is prohibited by the "
                "exit-status fidelity invariant (H3)"
            )
        return self._exit_code

    def close(self) -> None:
        """Terminate (if still alive), bounded-wait, and release the handle.

        128-S review remediation: the previous implementation closed the
        pywinpty handle unconditionally, without first terminating/waiting
        for a still-running child (unlike every other backend's ``close()``
        in this package) and dropped the handle even when ``self._pty.close()``
        itself raised. A still-live child is now signalled via ``terminate``
        (mirroring :meth:`signal`) and given a bounded wait before the
        handle is released, and the handle reference is cleared only in a
        ``finally`` so it is never leaked even if the underlying close call
        raises.
        """

        if self._pty is None:
            return
        try:
            with contextlib.suppress(Exception):
                if self._pty.isalive():
                    with contextlib.suppress(Exception):
                        self._pty.terminate(force=True)
                    deadline = time.monotonic() + 5
                    while self._pty.isalive() and time.monotonic() < deadline:
                        time.sleep(0.01)
            with contextlib.suppress(Exception):
                self._pty.close()
        finally:
            self._pty = None


def _try_construct_pty_backend(argv: Sequence[str]) -> Optional[ChildProcess]:
    """Attempt to construct a real PTY backend; return ``None`` if unavailable.

    Never raises for mere unavailability -- both availability checks are
    consulted first. Construction itself may still raise for genuinely
    unexpected errors; :func:`create_pty_or_inherited_child_process` is the
    layer responsible for catching that and degrading anyway.
    """

    if sys.platform == "win32":
        if not _winpty_available():
            return None
        return WinPtyChildProcess(argv)
    if not _posix_pty_available():
        return None
    return PtyChildProcess(argv)


def create_pty_or_inherited_child_process(
    argv: Sequence[str],
) -> Tuple[ChildProcess, Optional[str]]:
    """Construct a PTY backend, degrading to inherited stdio on any failure.

    Returns a ``(child_process, warning)`` pair. ``warning`` is ``None``
    when a real PTY backend was constructed, and a non-``None`` explanatory
    string whenever construction was unavailable or failed for any reason
    -- this factory NEVER hard-fails merely because PTY support is absent,
    and NEVER degrades to :class:`~autoharness.supervise.process.PipeChildProcess`.
    """

    backend: Optional[ChildProcess]
    warning: Optional[str]
    try:
        backend = _try_construct_pty_backend(argv)
        warning = None
    except Exception as exc:  # fail-safe: any construction error degrades
        backend = None
        warning = f"PTY backend construction failed ({exc!r}); degraded to inherited stdio"

    if backend is not None:
        return backend, None

    if warning is None:
        warning = "PTY backend unavailable on this platform; degraded to inherited stdio"
    return InheritStdioChildProcess(argv), warning
