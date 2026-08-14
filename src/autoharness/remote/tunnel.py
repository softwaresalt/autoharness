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


@runtime_checkable
class TunnelProcess(Protocol):
    """Structural protocol for the auxiliary devtunnel client process."""

    def spawn(self) -> None: ...

    def terminate(self) -> None: ...


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


class TunnelLifecycle:
    """Owns start/teardown of the loopback-bound devtunnel client process.

    Loopback validation happens at CONSTRUCTION time -- a lifecycle can
    never be built pointed at a non-loopback bind host in the first place.
    ``start()``/``teardown()`` are both idempotent, and ``teardown()`` is
    always safe to call before ``start()`` or from a ``finally`` block on a
    crash path (both are explicit acceptance criteria).
    """

    def __init__(self, *, bind_host: str, process_factory: Callable[[], TunnelProcess]) -> None:
        validate_loopback_bind(bind_host)
        self.bind_host = bind_host
        self._process_factory = process_factory
        self._process: Optional[TunnelProcess] = None
        self.active = False

    def start(self) -> None:
        """Spawn the devtunnel process. Idempotent: a second call is a no-op."""

        if self.active:
            return
        self._process = self._process_factory()
        self._process.spawn()
        self.active = True

    def teardown(self) -> None:
        """Terminate the devtunnel process. Idempotent and safe pre-start/on-crash."""

        if self._process is not None:
            self._process.terminate()
        self._process = None
        self.active = False
