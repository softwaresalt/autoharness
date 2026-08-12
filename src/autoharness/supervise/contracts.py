"""Supervisor core contract catalog: events, approvals, and gated actions.

This module is the shared contract surface for the future supervisor
runtime. It is pure and I/O-free: no subprocess invocation, no filesystem
access, no policy *logic* beyond the exhaustiveness/fallback-completeness
checks documented below.

Three catalogs live here:

1. **Stable event name/payload catalog** — the typed dataclasses a
   supervisor emits at each lifecycle milestone (session phase transitions,
   sidecar probes, child process lifecycle, approvals, restarts, journal
   checkpoints). Names and field shapes are a stable contract: adding a
   field is additive, removing/renaming one is a breaking change.
2. **Approval request/response types** — reused directly as the
   ``ApprovalRequested``/``ApprovalResolved`` event payloads below (the
   request-side fields ``kind``/``summary``/``options``/``default``/
   ``timeout`` live on ``ApprovalRequested``; the response-side fields
   ``kind``/``resolution``/``resolved_by`` live on ``ApprovalResolved``) so
   there is exactly one definition of each shape rather than a parallel pair
   of near-duplicate request/response classes.
3. **The gated-action registry** — a frozen, exhaustive, closed mapping of
   the *only* two actions in this shipment that require explicit gating
   (``session_restart``, ``force_unlock``), each carrying a single
   unambiguous :class:`FallbackPolicy` variant so a caller can never wonder
   what happens when the operator is unavailable to approve.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


# ---------------------------------------------------------------------------
# 1. Stable event name and payload catalog
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SessionPhaseChanged:
    """The supervised session moved from one lifecycle phase to another."""

    phase: str
    previous_phase: str | None = None


@dataclass(frozen=True)
class SidecarProbed:
    """A sidecar tool (backlogit, engram, gh, ...) was probed for availability."""

    name: str
    available: bool
    detail: str = ""


@dataclass(frozen=True)
class CopilotResolved:
    """The Copilot CLI executable was resolved to a concrete path."""

    exe_path: str
    source: str  # e.g. "env_path", "env_exe", "path_lookup"


@dataclass(frozen=True)
class ChildSpawned:
    """The supervised child process was spawned."""

    argv: tuple[str, ...]
    pid: int | None = None


@dataclass(frozen=True)
class ChildOutput:
    """A line of output was observed from the supervised child."""

    stream: str  # "stdout" | "stderr"
    line: str


@dataclass(frozen=True)
class ChildOutputUnavailable:
    """Child output could not be captured/observed (e.g. inherited stdio)."""

    reason: str


@dataclass(frozen=True)
class ChildExited:
    """The supervised child process exited."""

    exit_code: int


@dataclass(frozen=True)
class ApprovalRequested:
    """A gated action requires operator approval before proceeding.

    Doubles as the "approval request type" referenced by module docs: the
    request-side fields (``kind``, ``summary``, ``options``, ``default``,
    ``timeout``) live here.
    """

    kind: str
    summary: str
    options: tuple[str, ...] = ()
    default: str | None = None
    timeout: float | None = None


@dataclass(frozen=True)
class ApprovalResolved:
    """An approval request reached a resolution.

    Doubles as the "approval response type" referenced by module docs: the
    response-side fields (``kind``, ``resolution``, ``resolved_by``) live
    here.
    """

    kind: str
    resolution: str
    resolved_by: str


@dataclass(frozen=True)
class CancelRequested:
    """The operator (or an internal guard) requested cancellation."""

    reason: str = ""


@dataclass(frozen=True)
class RestartScheduled:
    """A session restart was scheduled."""

    attempt: int
    max_attempts: int


@dataclass(frozen=True)
class RestartExhausted:
    """The restart budget was exhausted; no further restarts will occur."""

    attempts: int


@dataclass(frozen=True)
class JournalCheckpoint:
    """A durable journal checkpoint was written."""

    sequence: int
    detail: str = ""


# ---------------------------------------------------------------------------
# 2. Fallback policy tagged union
# ---------------------------------------------------------------------------


class FallbackPolicy(abc.ABC):
    """Tagged union of what happens when a gated action cannot be approved.

    Exactly two variants exist: :class:`UseSafeDefault` (there is a safe,
    non-destructive value to fall back to) and :class:`Refuse` (no safe
    automatic value exists; the action must be refused).
    """

    @abc.abstractmethod
    def describe(self) -> str:
        """A short, human-readable description of this fallback behavior."""


@dataclass(frozen=True)
class UseSafeDefault(FallbackPolicy):
    """Fall back to a known-safe default value or referenced behavior."""

    reference_or_value: str

    def describe(self) -> str:
        return f"use safe default: {self.reference_or_value}"


@dataclass(frozen=True)
class Refuse(FallbackPolicy):
    """Refuse the action outright; no safe automatic value exists."""

    def describe(self) -> str:
        return "refuse: no safe automatic value exists"


# ---------------------------------------------------------------------------
# 3. Gated-action registry
# ---------------------------------------------------------------------------


class UnknownGatedActionError(KeyError):
    """Raised when looking up a gated-action identifier not in the registry."""


@dataclass(frozen=True)
class GatedActionSpec:
    """A single entry in the exhaustive gated-action catalog.

    ``fallback_policy`` has a ``None`` default purely so a caller can
    construct a policy-less spec and observe the required rejection in
    ``__post_init__`` (see ``tests/test_supervise_contracts.py``); every
    entry actually registered in :data:`GATED_ACTION_CATALOG` supplies a
    real :class:`FallbackPolicy` instance.
    """

    identifier: str
    summary: str
    options: tuple[str, ...]
    timeout: float
    fallback_policy: FallbackPolicy | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.fallback_policy, FallbackPolicy):
            raise ValueError(
                f"gated action {self.identifier!r} must declare exactly one "
                "FallbackPolicy variant (UseSafeDefault or Refuse); none was given"
            )


def _build_gated_action_catalog() -> Mapping[str, GatedActionSpec]:
    entries = (
        GatedActionSpec(
            identifier="session_restart",
            summary="Restart the supervised Copilot session after a crash, "
            "stall, or unexpected exit.",
            options=("restart", "decline"),
            timeout=30.0,
            fallback_policy=UseSafeDefault(
                "decline restart (the restart budget defaults to 0)"
            ),
        ),
        GatedActionSpec(
            identifier="force_unlock",
            summary="Forcibly remove another holder's session guard lock record.",
            options=("force_unlock", "cancel"),
            timeout=30.0,
            fallback_policy=Refuse(),
        ),
    )
    registry: dict[str, GatedActionSpec] = {}
    for entry in entries:
        registry[entry.identifier] = entry
    return MappingProxyType(registry)


# Frozen, exhaustive, closed registry. Looking up an unregistered identifier
# via get_gated_action() raises rather than returning a permissive default.
GATED_ACTION_CATALOG: Mapping[str, GatedActionSpec] = _build_gated_action_catalog()


def get_gated_action(identifier: str) -> GatedActionSpec:
    """Look up a gated action by identifier.

    Raises:
        UnknownGatedActionError: if ``identifier`` is not registered. This
            catalog is closed by design: there is no permissive default.
    """

    try:
        return GATED_ACTION_CATALOG[identifier]
    except KeyError as exc:
        raise UnknownGatedActionError(identifier) from exc
