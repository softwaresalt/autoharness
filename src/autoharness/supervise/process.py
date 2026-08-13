"""ChildProcess protocol and backend implementations (119.001-T).

This module defines the ``ChildProcess`` protocol shared by every child
process backend the supervisor may launch, plus three concrete
implementations:

* :class:`InheritStdioChildProcess` -- THE DEFAULT backend for interactive
  launches. Passes the parent's stdin/stdout/stderr through UNCHANGED (no
  ``subprocess.PIPE`` for any stream, on POSIX or Windows). Output is not
  observable through this backend by construction: :meth:`read` raises
  :class:`OutputCaptureUnavailable` rather than silently returning
  fabricated content. Higher layers (119.005-T's journal) detect this via
  :attr:`supports_output_capture` and emit a ``ChildOutputUnavailable``
  marker -- this module does not itself emit journal/event-bus records.
* :class:`PipeChildProcess` -- stdlib ``subprocess.Popen`` with
  ``stdout=PIPE`` and ``stderr=STDOUT`` (combined into one readable stream;
  see the class docstring for the rationale) for tests and explicit
  non-interactive use.
* :class:`FakeChildProcess` -- a scripted, dependency-free double
  implementing the same protocol for deterministic tests: no real
  subprocess is ever spawned, exit code/stdout lines/signal calls are all
  fully caller-controlled and observable.

Hard invariants enforced across every backend in this module:

* ``argv`` is ALWAYS a ``Sequence[str]``, stored and forwarded as a
  ``tuple[str, ...]`` -- never re-joined, re-quoted, or re-parsed.
* Spawning NEVER passes ``shell=True`` to ``subprocess.Popen`` (asserted by
  ``tests/test_supervise_process.py`` via a ``subprocess.Popen`` spy).
* :meth:`wait` returns the child's real exit code UNMODIFIED: no masking,
  no remapping, no inferring success/failure from captured output.
* Every real-process backend accepts an OPTIONAL ``cwd`` keyword argument,
  forwarded verbatim to ``subprocess.Popen`` (``None`` -- the default --
  means "inherit the parent's own cwd", identical to omitting it). Callers
  that anchor a workspace root (e.g. :mod:`autoharness.supervise.app`) pass
  it explicitly so the spawned child -- and, by inheritance, any local
  stdio MCP server IT in turn spawns -- resolves CWD-relative behavior
  against the real workspace rather than whatever directory the invoking
  shell happened to have as its own cwd (120-F runtime-defect
  remediation).

This module performs real subprocess I/O (unlike most of this package) but
remains otherwise pure: no filesystem writes, no journal/event-bus
integration, no policy logic beyond the invariants above.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Optional, Protocol, Sequence, runtime_checkable


class OutputCaptureUnavailable(Exception):
    """Raised by a backend whose output cannot be observed/captured.

    :class:`InheritStdioChildProcess` raises this from :meth:`read` (and
    :meth:`write`, since stdin is likewise passed through unchanged with no
    pipe to write into) rather than returning a sentinel value a caller
    might mistake for "no output yet". Callers detect this condition via
    :attr:`ChildProcess.supports_output_capture` *before* calling
    :meth:`read`/:meth:`write` when they want to avoid the exception path
    entirely; the exception exists as a hard backstop for callers that
    don't check first.
    """


@runtime_checkable
class ChildProcess(Protocol):
    """Protocol shared by every supervised child-process backend.

    Every backend exposes: ``spawn`` (start the child), ``read`` (observe
    the next unit of output, or ``None``/raise depending on the backend's
    capture support), ``write`` (send input to the child), ``signal``
    (deliver a signal), ``wait`` (block for and return the real exit code),
    and ``close`` (release any OS resources -- pipes, handles -- held by
    this backend; idempotent).
    """

    supports_output_capture: bool

    @property
    def argv(self) -> tuple[str, ...]:
        """The exact argv this backend was constructed with, unmodified."""

    @property
    def pid(self) -> Optional[int]:
        """The child's OS process id, or ``None`` before ``spawn()``."""

    def spawn(self) -> None:
        """Start the child process. Never uses ``shell=True``."""

    def read(self) -> Optional[str]:
        """Return the next captured output line, or ``None`` at EOF.

        Raises :class:`OutputCaptureUnavailable` when
        ``supports_output_capture`` is ``False``.
        """

    def write(self, data: bytes) -> None:
        """Send ``data`` to the child's stdin, when supported."""

    def signal(self, sig: int) -> None:
        """Deliver signal ``sig`` to the child."""

    def wait(self, timeout: Optional[float] = None) -> int:
        """Block until the child exits; return its REAL exit code, unmodified."""

    def close(self) -> None:
        """Release any OS resources held by this backend. Idempotent."""


class InheritStdioChildProcess:
    """Default interactive backend: parent's stdin/stdout/stderr pass through.

    No stream is redirected to ``subprocess.PIPE`` -- the child inherits the
    parent's actual file descriptors/handles (and, when one exists, its
    controlling terminal) unchanged. Because nothing is captured, ``read``
    and ``write`` both raise :class:`OutputCaptureUnavailable`;
    ``supports_output_capture`` is ``False`` so callers can detect this
    without triggering the exception path.
    """

    supports_output_capture: bool = False

    def __init__(self, argv: Sequence[str], *, cwd: Optional[str] = None) -> None:
        self._argv: tuple[str, ...] = tuple(argv)
        self._cwd: Optional[str] = cwd
        self._process: Optional[subprocess.Popen] = None

    @property
    def argv(self) -> tuple[str, ...]:
        return self._argv

    @property
    def pid(self) -> Optional[int]:
        return self._process.pid if self._process is not None else None

    def spawn(self) -> None:
        # stdin/stdout/stderr are left at their default (None), which means
        # "inherit the parent's own file descriptor/handle" -- NOT redirected
        # to a pipe. shell is never passed (defaults to False). ``cwd``
        # defaults to ``None`` (subprocess.Popen's own "inherit the parent's
        # cwd" semantics) unless a workspace root was explicitly supplied by
        # the caller (120-F runtime-defect remediation: anchors the spawned
        # child -- and, by inheritance, any local stdio MCP server it in
        # turn spawns -- to the resolved workspace regardless of the
        # invoking shell's own cwd).
        self._process = subprocess.Popen(list(self._argv), cwd=self._cwd)

    def read(self) -> Optional[str]:
        raise OutputCaptureUnavailable(
            "InheritStdioChildProcess does not capture output; check "
            "supports_output_capture before calling read()"
        )

    def write(self, data: bytes) -> None:
        raise OutputCaptureUnavailable(
            "InheritStdioChildProcess does not expose a writable stdin pipe; "
            "stdin is inherited from the parent unchanged"
        )

    def signal(self, sig: int) -> None:
        if self._process is None:
            raise RuntimeError("cannot signal before spawn()")
        self._process.send_signal(sig)

    def wait(self, timeout: Optional[float] = None) -> int:
        if self._process is None:
            raise RuntimeError("cannot wait before spawn()")
        return self._process.wait(timeout=timeout)

    def close(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        self._process = None


class PipeChildProcess:
    """Non-interactive backend: stdout/stderr captured via ``subprocess.PIPE``.

    stdout and stderr are combined into a single readable stream
    (``stderr=subprocess.STDOUT``) so :meth:`read` has one deterministic
    ordering to hand back to callers rather than requiring them to
    interleave two independently-buffered pipes themselves. stdin is also a
    pipe, so :meth:`write` is meaningful for this backend.
    """

    supports_output_capture: bool = True

    def __init__(self, argv: Sequence[str], *, cwd: Optional[str] = None) -> None:
        self._argv: tuple[str, ...] = tuple(argv)
        self._cwd: Optional[str] = cwd
        self._process: Optional[subprocess.Popen] = None

    @property
    def argv(self) -> tuple[str, ...]:
        return self._argv

    @property
    def pid(self) -> Optional[int]:
        return self._process.pid if self._process is not None else None

    @property
    def raw_popen(self) -> Optional[subprocess.Popen]:
        """The underlying ``Popen`` handle, exposed for test introspection."""

        return self._process

    def spawn(self) -> None:
        self._process = subprocess.Popen(
            list(self._argv),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=self._cwd,
        )

    def read(self) -> Optional[str]:
        if self._process is None or self._process.stdout is None:
            raise RuntimeError("cannot read before spawn()")
        line = self._process.stdout.readline()
        if line == "":
            return None
        return line

    def write(self, data: bytes) -> None:
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("cannot write before spawn()")
        self._process.stdin.write(data.decode("utf-8") if isinstance(data, bytes) else data)
        self._process.stdin.flush()

    def signal(self, sig: int) -> None:
        if self._process is None:
            raise RuntimeError("cannot signal before spawn()")
        self._process.send_signal(sig)

    def wait(self, timeout: Optional[float] = None) -> int:
        """Block until the child exits; return its REAL exit code, unmodified.

        Caller-drains-stdout contract: this backend's stdout is a plain OS
        pipe with a bounded kernel buffer. If the child writes enough output
        without this pipe being drained (via :meth:`read`) concurrently, the
        child can block on its own write() call once the buffer fills,
        meaning it never exits and this method blocks indefinitely (a
        classic ``subprocess`` pitfall). Callers that expect a chatty child
        MUST drain :meth:`read` in a loop rather than calling ``wait()``
        cold; :meth:`close` (used by cancellation/termination paths) does
        not depend on the caller having drained anything -- it uses
        ``communicate()`` internally, which drains concurrently while
        waiting, specifically to avoid this deadlock during termination.
        """

        if self._process is None:
            raise RuntimeError("cannot wait before spawn()")
        return self._process.wait(timeout=timeout)

    def close(self) -> None:
        if self._process is None:
            return
        if self._process.poll() is None:
            self._process.terminate()
            try:
                # communicate() drains stdout/stderr concurrently while
                # waiting for exit, unlike a bare wait() -- avoiding a
                # deadlock if the child emits enough final output to fill
                # the OS pipe buffer before actually exiting (128-S review
                # remediation).
                self._process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.communicate(timeout=5)
        for stream in (self._process.stdin, self._process.stdout, self._process.stderr):
            if stream is not None and not stream.closed:
                stream.close()
        self._process = None


@dataclass
class FakeChildProcess:
    """Scripted, dependency-free ``ChildProcess`` double for deterministic tests.

    No real subprocess is ever spawned. Exit code, scripted stdout lines,
    and every ``signal``/``write`` call are recorded so recovery/session
    tests can simulate cancellation and restart flows without real
    processes. This is a mutable (non-frozen) dataclass, unlike most of this
    package's value objects, because it exists purely to accumulate
    observable call history for assertions.
    """

    argv: tuple[str, ...]
    exit_code: int = 0
    scripted_stdout: list[str] = field(default_factory=list)
    supports_output_capture: bool = True
    pid: Optional[int] = 4242

    signals_received: list[int] = field(default_factory=list, init=False)
    written: list[bytes] = field(default_factory=list, init=False)
    spawned: bool = field(default=False, init=False)
    waited: bool = field(default=False, init=False)
    closed: bool = field(default=False, init=False)
    _output_index: int = field(default=0, init=False)

    def spawn(self) -> None:
        self.spawned = True

    def read(self) -> Optional[str]:
        if not self.supports_output_capture:
            raise OutputCaptureUnavailable(
                "FakeChildProcess configured with supports_output_capture=False"
            )
        if self._output_index >= len(self.scripted_stdout):
            return None
        line = self.scripted_stdout[self._output_index]
        self._output_index += 1
        return line

    def write(self, data: bytes) -> None:
        self.written.append(data)

    def signal(self, sig: int) -> None:
        self.signals_received.append(sig)

    def wait(self, timeout: Optional[float] = None) -> int:
        self.waited = True
        return self.exit_code

    def close(self) -> None:
        self.closed = True
