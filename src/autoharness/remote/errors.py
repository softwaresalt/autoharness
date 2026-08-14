"""Plan 2 V1 remote control-plane error taxonomy (121.008-T).

Mirrors the machine-readable exit-code contract pattern established by
:mod:`autoharness.supervise.errors`: every :class:`RemoteError` carries a
:class:`RemoteErrorKind`, and :data:`EXIT_CODE_BY_KIND` maps every member to
a stable exit code with no gaps (enforced by the module-load-time
assertion below). This is a SEPARATE taxonomy from
:mod:`autoharness.supervise.errors` -- Plan 2 is independent of Plan 1 and
must not graft new kinds onto the Plan 1 ``ErrorKind`` enum.

This module is pure: no I/O, no subprocess invocation, no ``sys.exit``.
"""

from __future__ import annotations

import enum


class RemoteErrorKind(enum.Enum):
    """Machine-readable Plan 2 remote-protocol error taxonomy."""

    UNKNOWN = "unknown_error"
    PROTOCOL = "protocol_error"
    SIZE_LIMIT = "size_limit_error"
    RATE_LIMIT = "rate_limit_error"
    BINDING = "binding_error"
    AUTHORITY = "authority_error"
    STATE = "state_error"
    IDEMPOTENCY = "idempotency_error"
    TRANSPORT = "transport_error"


# Single machine-readable exit-code contract table. Every RemoteErrorKind
# member has exactly one entry; distinct kinds MAY legitimately share a
# code, but every kind MUST be present (totality, not injectivity).
EXIT_CODE_BY_KIND: dict[RemoteErrorKind, int] = {
    RemoteErrorKind.UNKNOWN: 1,
    RemoteErrorKind.PROTOCOL: 20,
    RemoteErrorKind.SIZE_LIMIT: 21,
    RemoteErrorKind.RATE_LIMIT: 22,
    RemoteErrorKind.BINDING: 23,
    RemoteErrorKind.AUTHORITY: 24,
    RemoteErrorKind.STATE: 25,
    RemoteErrorKind.IDEMPOTENCY: 26,
    RemoteErrorKind.TRANSPORT: 27,
}

_missing_kinds = set(RemoteErrorKind) - set(EXIT_CODE_BY_KIND)
if _missing_kinds:  # pragma: no cover - defensive, guards future edits
    raise RuntimeError(
        f"EXIT_CODE_BY_KIND is missing entries for: {sorted(k.value for k in _missing_kinds)}"
    )


class RemoteError(Exception):
    """Base exception for all Plan 2 remote control-plane errors.

    Subclasses fix :attr:`kind` as a class attribute; callers may also pass
    ``kind=`` explicitly to the base class directly when a bespoke subclass
    is not warranted.
    """

    kind: RemoteErrorKind = RemoteErrorKind.UNKNOWN

    def __init__(self, message: str, *, kind: RemoteErrorKind | None = None) -> None:
        super().__init__(message)
        if kind is not None:
            self.kind = kind

    @property
    def exit_code(self) -> int:
        """The machine-readable exit code for this error's :attr:`kind`."""

        return EXIT_CODE_BY_KIND[self.kind]


class UnknownRemoteCommandError(RemoteError):
    """A command outside the closed Observe/Steer/local-only vocabulary."""

    kind = RemoteErrorKind.PROTOCOL


class LocalOnlyCommandError(RemoteError):
    """A command resolved to the Approve/Privileged tier and was rejected
    for remote dispatch (V1 never exposes these tiers remotely)."""

    kind = RemoteErrorKind.AUTHORITY


class RequestTooLargeError(RemoteError):
    """A request payload exceeded the 16 KiB V1 size limit."""

    kind = RemoteErrorKind.SIZE_LIMIT


class MalformedRequestError(RemoteError):
    """A request payload is not a valid V1 structured request."""

    kind = RemoteErrorKind.PROTOCOL


class RateLimitExceededError(RemoteError):
    """The 30 req/min, burst-5 token bucket had no tokens available."""

    kind = RemoteErrorKind.RATE_LIMIT


class BindingMismatchError(RemoteError):
    """A request failed cryptographic workspace/session binding verification."""

    kind = RemoteErrorKind.BINDING


class IllegalRemoteStateError(RemoteError):
    """A Steer/Observe command was attempted while the local session was in
    a phase (or auxiliary pause state) that does not permit it."""

    kind = RemoteErrorKind.STATE


class DuplicateRequestError(RemoteError):
    """A request's idempotency key (``request_id``) was already processed."""

    kind = RemoteErrorKind.IDEMPOTENCY


class StaleRequestError(RemoteError):
    """A request's ``issued_at`` timestamp is outside the allowed freshness
    window (too old, or implausibly in the future)."""

    kind = RemoteErrorKind.IDEMPOTENCY


class DevtunnelUnavailableError(RemoteError):
    """The devtunnel client executable -- V1's sole remote transport and
    authentication mechanism -- could not be resolved on PATH."""

    kind = RemoteErrorKind.TRANSPORT


class ObservationUnavailableError(RemoteError):
    """Required local journal or event observation data is unavailable."""

    kind = RemoteErrorKind.TRANSPORT
