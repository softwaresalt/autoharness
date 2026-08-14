"""Plan 2 V1 remote authority and message contracts (121.008-T).

This module defines the ENTIRE closed vocabulary of commands that may ever
cross the Plan 2 remote boundary, the 4-tier authority model, and the
request/response envelope shapes. It is the single place that decides
whether a command string is remotely dispatchable at all -- nothing in
:mod:`autoharness.remote.steer` or :mod:`autoharness.remote.observe` may
bypass :func:`ensure_remotely_dispatchable`.

Design invariants (do not weaken):

* ``ObserveCommand`` and ``SteerCommand`` are the only two remotely
  reachable vocabularies (``REMOTE_EXPOSED_TIERS``). ``LocalOnlyCommand``
  mirrors :data:`autoharness.supervise.contracts.GATED_ACTION_CATALOG`
  exactly -- V1 never remotely exposes Approve/Privileged actions.
* ``COMMAND_TIER`` is total over the union of all three vocabularies and
  immutable (``MappingProxyType``) -- there is no permissive fallback for
  an unregistered command string.
* ``RemoteRequest.role`` is a coarse ROLE identifier (e.g.
  ``"remote_operator"``), never a workstation/hostname/IP identity --
  this is an explicit audit-privacy requirement from the shipment.
"""

from __future__ import annotations

import enum
import json
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from autoharness.remote.errors import (
    LocalOnlyCommandError,
    MalformedRequestError,
    RequestTooLargeError,
    UnknownRemoteCommandError,
)
from autoharness.supervise.contracts import GATED_ACTION_CATALOG

REMOTE_OPERATOR_ROLE = "remote_operator"


class ObserveCommand(enum.Enum):
    """The closed set of read-only Observe commands (Plan 2 V1 scope)."""

    STATUS = "status"
    PHASE = "phase"
    PROGRESS = "progress"
    OUTPUT_TAIL = "output_tail"
    JOURNAL_TAIL = "journal_tail"


class SteerCommand(enum.Enum):
    """The closed set of state-changing Steer commands (Plan 2 V1 scope)."""

    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    REQUEST_CHECKPOINT = "request_checkpoint"


class LocalOnlyCommand(enum.Enum):
    """Commands that remain LOCAL-ONLY in V1.

    This vocabulary mirrors ``GATED_ACTION_CATALOG`` from Plan 1 exactly --
    it exists here purely so :data:`COMMAND_TIER` can classify (and then
    reject) these identifiers if a remote request names one, never so they
    can be dispatched.
    """

    SESSION_RESTART = "session_restart"
    FORCE_UNLOCK = "force_unlock"


_local_only_values = {c.value for c in LocalOnlyCommand}
_gated_action_keys = set(GATED_ACTION_CATALOG.keys())
if _local_only_values != _gated_action_keys:  # pragma: no cover - defensive
    raise RuntimeError(
        "LocalOnlyCommand has drifted from supervise.contracts.GATED_ACTION_CATALOG: "
        f"local_only={sorted(_local_only_values)!r} catalog={sorted(_gated_action_keys)!r}"
    )


class AuthorityTier(enum.Enum):
    """The 4-tier Plan 2 authorization model.

    Only ``OBSERVE`` and ``STEER`` are ever remotely exposed in V1
    (:data:`REMOTE_EXPOSED_TIERS`). ``APPROVE`` and ``PRIVILEGED`` remain
    local-only for the foreseeable future -- there is no roadmap item in
    this shipment that changes that.
    """

    OBSERVE = "observe"
    STEER = "steer"
    APPROVE = "approve"
    PRIVILEGED = "privileged"


REMOTE_EXPOSED_TIERS: frozenset[AuthorityTier] = frozenset(
    {AuthorityTier.OBSERVE, AuthorityTier.STEER}
)


def _build_command_tier() -> Mapping[str, AuthorityTier]:
    registry: dict[str, AuthorityTier] = {}
    for command in ObserveCommand:
        registry[command.value] = AuthorityTier.OBSERVE
    for command in SteerCommand:
        registry[command.value] = AuthorityTier.STEER
    for command in LocalOnlyCommand:
        registry[command.value] = AuthorityTier.PRIVILEGED
    return MappingProxyType(registry)


# Frozen, exhaustive, closed registry -- total over every command string
# this package is aware of. There is no permissive default branch anywhere
# that consults this table.
COMMAND_TIER: Mapping[str, AuthorityTier] = _build_command_tier()


def resolve_command_tier(command: str) -> AuthorityTier:
    """Resolve ``command`` to its :class:`AuthorityTier`.

    Raises:
        UnknownRemoteCommandError: if ``command`` is not in the closed
            vocabulary at all (this is the ONLY way an unrecognized string
            -- including any raw-shell-shaped input -- is handled).
    """

    try:
        return COMMAND_TIER[command]
    except KeyError as exc:
        raise UnknownRemoteCommandError(
            f"{command!r} is not a recognized Plan 2 remote command"
        ) from exc


def ensure_remotely_dispatchable(command: str) -> AuthorityTier:
    """Resolve ``command`` and fail closed unless its tier is remotely exposed.

    Raises:
        UnknownRemoteCommandError: ``command`` is outside the closed
            vocabulary entirely.
        LocalOnlyCommandError: ``command`` is recognized but resolves to
            the Approve/Privileged tier, which V1 never dispatches
            remotely.
    """

    tier = resolve_command_tier(command)
    if tier not in REMOTE_EXPOSED_TIERS:
        raise LocalOnlyCommandError(
            f"{command!r} resolves to tier {tier.value!r}, which is local-only in V1"
        )
    return tier


# Security requirement: 16 KiB max request size.
MAX_REQUEST_BYTES: int = 16 * 1024

# Security requirement: 30 requests/minute with a burst of 5.
RATE_LIMIT_PER_MINUTE: int = 30
RATE_LIMIT_BURST: int = 5


def validate_request_size(payload: bytes) -> None:
    """Fail closed if ``payload`` exceeds :data:`MAX_REQUEST_BYTES`.

    Raises:
        TypeError: ``payload`` is not ``bytes``.
        RequestTooLargeError: ``payload`` exceeds the 16 KiB limit.
    """

    if not isinstance(payload, bytes):
        raise TypeError(f"payload must be bytes, got {type(payload).__name__}")
    if len(payload) > MAX_REQUEST_BYTES:
        raise RequestTooLargeError(
            f"request payload of {len(payload)} bytes exceeds the "
            f"{MAX_REQUEST_BYTES}-byte V1 limit"
        )


def decode_request(payload: bytes) -> "RemoteRequest":
    """Decode one bounded JSON request into the frozen protocol envelope.

    This is the transport boundary for the size contract. Dispatchers accept
    only the typed result, so malformed bytes cannot reach binding, rate
    limiting, or state mutation.
    """

    validate_request_size(payload)
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MalformedRequestError("request payload is not valid UTF-8 JSON") from exc

    if not isinstance(decoded, dict):
        raise MalformedRequestError("request payload must be a JSON object")

    required_fields = ("command", "request_id", "workspace_id", "session_id", "issued_at")
    missing = [name for name in required_fields if name not in decoded]
    if missing:
        raise MalformedRequestError(
            f"request payload is missing required field(s): {', '.join(missing)}"
        )

    string_fields = ("command", "request_id", "workspace_id", "session_id")
    for name in string_fields:
        value = decoded[name]
        if not isinstance(value, str) or not value:
            raise MalformedRequestError(f"request field {name!r} must be a non-empty string")

    issued_at = decoded["issued_at"]
    if (
        isinstance(issued_at, bool)
        or not isinstance(issued_at, (int, float))
        or not math.isfinite(issued_at)
    ):
        raise MalformedRequestError("request field 'issued_at' must be a number")

    role = decoded.get("role", REMOTE_OPERATOR_ROLE)
    if role != REMOTE_OPERATOR_ROLE:
        raise MalformedRequestError(
            f"request field 'role' must be {REMOTE_OPERATOR_ROLE!r}"
        )

    request_payload = decoded.get("payload", {})
    if not isinstance(request_payload, dict):
        raise MalformedRequestError("request field 'payload' must be a JSON object")

    return RemoteRequest(
        command=decoded["command"],
        request_id=decoded["request_id"],
        workspace_id=decoded["workspace_id"],
        session_id=decoded["session_id"],
        issued_at=float(issued_at),
        role=role,
        payload=MappingProxyType(dict(request_payload)),
    )


@dataclass(frozen=True)
class RemoteRequest:
    """An inbound Plan 2 remote request envelope.

    ``role`` is deliberately a coarse authorization role (never a
    workstation/hostname/IP identity) so audit records never leak
    workstation-identifying information -- an explicit audit-privacy
    requirement from the shipment.
    """

    command: str
    request_id: str
    workspace_id: str
    session_id: str
    issued_at: float
    role: str = "remote_operator"
    payload: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if self.role != REMOTE_OPERATOR_ROLE:
            raise ValueError(
                f"remote requests must use the {REMOTE_OPERATOR_ROLE!r} role"
            )


@dataclass(frozen=True)
class RemoteResponse:
    """An outbound Plan 2 remote response envelope."""

    request_id: str
    command: str
    ok: bool
    payload: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    error: str | None = None
