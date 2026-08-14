"""Plan 2 V1 loopback binding + devtunnel lifecycle boundary (121.005-T).

This module owns exactly two V1 non-negotiables:

1. **Loopback-only binding** (T7): :func:`validate_loopback_bind` is the
   single choke point that decides whether a bind host is acceptable. No
   other module in this package may bind a socket without going through
   this check first (:class:`TunnelLifecycle` enforces it at construction
   time).
2. **devtunnel is V1's sole transport and auth mechanism.**
   :func:`resolve_devtunnel_executable` fails closed with a clear,
   actionable error when the devtunnel CLI is not present on PATH -- this
   is meant to read as "you have not installed/configured a prerequisite",
   never a stack trace.

``TunnelLifecycle`` deliberately does NOT import
:class:`autoharness.supervise.process.ChildProcess` -- the devtunnel CLI is
an unsupervised auxiliary transport process, not a supervised Copilot
session child, and conflating the two would blur an intentional boundary.
Instead it depends on a small structural :class:`TunnelProcess` protocol so
production code can supply a real ``subprocess``-backed implementation
while tests use :class:`FakeTunnelProcess`.
"""

from __future__ import annotations

import shutil
import subprocess
import threading
import time
from typing import Callable, Optional, Protocol, runtime_checkable

from autoharness.remote.errors import DevtunnelUnavailableError, RemoteError, RemoteErrorKind

# Case-insensitive; covers the IPv4/IPv6 loopback literals and the
# "localhost" hostname. Deliberately does NOT attempt DNS resolution or
# accept any LAN/all-interfaces address -- T7 is a hard non-negotiable.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


class NonLoopbackBindError(RemoteError):
    """A bind host outside :data:`LOOPBACK_HOSTS` was rejected (T7)."""

    kind = RemoteErrorKind.BINDING


def validate_loopback_bind(host: str) -> None:
    """Fail closed unless ``host`` is a recognized loopback address/name.

    Raises:
        NonLoopbackBindError: ``host`` is empty or is not one of
            :data:`LOOPBACK_HOSTS` (case-insensitive).
    """

    if not host or host.lower() not in LOOPBACK_HOSTS:
        raise NonLoopbackBindError(
            f"{host!r} is not a loopback bind host; Plan 2 V1 only ever binds to "
            f"{sorted(LOOPBACK_HOSTS)!r}"
        )


def resolve_devtunnel_executable(
    which_fn: Callable[[str], Optional[str]] | None = None,
) -> str:
    """Resolve the devtunnel client executable via an injectable ``which_fn``.

    Raises:
        DevtunnelUnavailableError: ``which_fn("devtunnel")`` returned
            ``None`` -- devtunnel is V1's sole transport/auth mechanism, so
            this is reported as a clear prerequisite/configuration failure,
            never a generic error.
    """

    path = (shutil.which if which_fn is None else which_fn)("devtunnel")
    if not path:
        raise DevtunnelUnavailableError(
            "the 'devtunnel' CLI was not found on PATH; install/configure devtunnel "
            "before starting the Plan 2 remote control-plane tunnel"
        )
    return path


def build_devtunnel_argv(executable: str, port: int) -> tuple[str, ...]:
    """Build an authenticated devtunnel host command for the local UI."""

    if not executable:
        raise ValueError("devtunnel executable must not be empty")
    if port < 1 or port > 65535:
        raise ValueError("devtunnel port must be between 1 and 65535")
    return (executable, "host", "--port", str(port))


@runtime_checkable
class TunnelProcess(Protocol):
    """Structural protocol for the auxiliary devtunnel client process."""

    def spawn(self) -> None: ...

    def terminate(self) -> None: ...

    def is_alive(self) -> bool: ...


class SubprocessTunnelProcess:
    """Production devtunnel process boundary with no anonymous fallback."""

    def __init__(self, argv: tuple[str, ...]) -> None:
        if not argv:
            raise ValueError("devtunnel argv must not be empty")
        if "--allow-anonymous" in argv:
            raise ValueError("Plan 2 V1 devtunnel access must remain authenticated")
        self.argv = argv
        self._process: subprocess.Popen[bytes] | None = None

    def spawn(self) -> None:
        self._process = subprocess.Popen(
            list(self.argv),
            stdout=None,
            stderr=None,
        )

    def terminate(self) -> None:
        if self._process is None:
            return
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        self._process = None

    def is_alive(self) -> bool:
        return self._process is not None and self._process.poll() is None

class FakeTunnelProcess:
    """Injectable test double for :class:`TunnelProcess`."""

    def __init__(self, argv: tuple[str, ...]) -> None:
        self.argv = argv
        self.spawned = False
        self.terminated = False

    def spawn(self) -> None:
        self.spawned = True

    def terminate(self) -> None:
        self.terminated = True

    def is_alive(self) -> bool:
        return self.spawned and not self.terminated


class TunnelLifecycle:
    """Owns start/teardown of the loopback-bound devtunnel client process.

    Loopback validation happens at CONSTRUCTION time -- a lifecycle can
    never be built pointed at a non-loopback bind host in the first place.
    ``start()``/``teardown()`` are both idempotent, and ``teardown()`` is
    always safe to call before ``start()`` or from a ``finally`` block on a
    crash path (both are explicit acceptance criteria).
    """

    def __init__(
        self,
        *,
        bind_host: str,
        process_factory: Callable[[], TunnelProcess],
        on_loss: Callable[[], None] | None = None,
        watch_interval: float = 0.1,
    ) -> None:
        validate_loopback_bind(bind_host)
        if watch_interval <= 0:
            raise ValueError("watch_interval must be positive")
        self.bind_host = bind_host
        self._process_factory = process_factory
        self._on_loss = on_loss
        self._watch_interval = watch_interval
        self._process: Optional[TunnelProcess] = None
        self.active = False
        self._lock = threading.Lock()
        self._watch_thread: threading.Thread | None = None

    def start(self) -> None:
        """Spawn the devtunnel process. Idempotent: a second call is a no-op."""

        with self._lock:
            if self.active:
                return
            process = self._process_factory()
            process.spawn()
            self._process = process
            self.active = True
            self._watch_thread = threading.Thread(
                target=self._watch_process,
                args=(process,),
                name="autoharness-devtunnel-watch",
                daemon=True,
            )
            self._watch_thread.start()

    def teardown(self) -> None:
        """Terminate the devtunnel process. Idempotent and safe pre-start/on-crash."""

        with self._lock:
            process = self._process
            self._process = None
            self.active = False
        if process is not None:
            process.terminate()

    def _watch_process(self, process: TunnelProcess) -> None:
        while True:
            with self._lock:
                if not self.active or self._process is not process:
                    return
            if not process.is_alive():
                with self._lock:
                    if self._process is process:
                        self._process = None
                        self.active = False
                if self._on_loss is not None:
                    self._on_loss()
                return
            time.sleep(self._watch_interval)
