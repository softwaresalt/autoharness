"""Supervisor error taxonomy and machine-readable exit-code contract.

:class:`AutoharnessError` is the single base exception every supervisor
operation raises. Every error carries a machine-readable :class:`ErrorKind`
that a future CLI adapter can use to derive a stable process exit code via
:data:`EXIT_CODE_BY_KIND` without re-deriving mapping logic per call site.

This module is pure: no I/O, no subprocess invocation, no ``sys.exit``.
"""

from __future__ import annotations

import enum


class ErrorKind(enum.Enum):
    """Machine-readable supervisor error taxonomy.

    Every member MUST have exactly one entry in :data:`EXIT_CODE_BY_KIND`
    (enforced by module-load-time assertion below and by
    ``tests/test_supervise_errors.py``).
    """

    CONFIG = "config_error"
    LOCK = "lock_error"
    RESOLUTION = "resolution_error"
    APPROVAL = "approval_error"
    RESTART = "restart_error"
    ILLEGAL_TRANSITION = "illegal_transition_error"
    UNKNOWN = "unknown_error"


# Single machine-readable exit-code contract table. Every ErrorKind member
# has exactly one entry (totality, not injectivity, is the contract: distinct
# kinds MAY legitimately share an exit code).
EXIT_CODE_BY_KIND: dict[ErrorKind, int] = {
    ErrorKind.UNKNOWN: 1,
    ErrorKind.CONFIG: 2,
    ErrorKind.LOCK: 3,
    ErrorKind.RESOLUTION: 4,
    ErrorKind.APPROVAL: 5,
    ErrorKind.RESTART: 6,
    ErrorKind.ILLEGAL_TRANSITION: 7,
}

_missing_kinds = set(ErrorKind) - set(EXIT_CODE_BY_KIND)
if _missing_kinds:  # pragma: no cover - defensive, guards future edits
    raise RuntimeError(
        f"EXIT_CODE_BY_KIND is missing entries for: {sorted(k.value for k in _missing_kinds)}"
    )


class AutoharnessError(Exception):
    """Base exception for all supervisor errors.

    Subclasses fix :attr:`kind` as a class attribute; callers may also pass
    ``kind=`` explicitly to the base class directly when a bespoke subclass
    is not warranted.
    """

    kind: ErrorKind = ErrorKind.UNKNOWN

    def __init__(self, message: str, *, kind: ErrorKind | None = None) -> None:
        super().__init__(message)
        if kind is not None:
            self.kind = kind

    @property
    def exit_code(self) -> int:
        """The machine-readable exit code for this error's :attr:`kind`."""

        return EXIT_CODE_BY_KIND[self.kind]


class ConfigError(AutoharnessError):
    """Invalid or missing supervisor configuration."""

    kind = ErrorKind.CONFIG


class LockError(AutoharnessError):
    """Session guard lock acquisition, contention, or containment failure."""

    kind = ErrorKind.LOCK


class ResolutionError(AutoharnessError):
    """Failure resolving a required executable, path, or sidecar tool."""

    kind = ErrorKind.RESOLUTION


class ApprovalError(AutoharnessError):
    """A gated action could not be resolved through the approval workflow."""

    kind = ErrorKind.APPROVAL


class RestartError(AutoharnessError):
    """Session restart scheduling or budget-exhaustion failure."""

    kind = ErrorKind.RESTART


class IllegalTransitionError(AutoharnessError):
    """A session state machine transition was attempted that is not in the
    legal-transition table (see :mod:`autoharness.supervise.session`)."""

    kind = ErrorKind.ILLEGAL_TRANSITION
