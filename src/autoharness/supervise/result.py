"""SupervisorResult — a single typed result envelope for supervisor operations.

Every supervisor operation (session lifecycle, lock acquisition, redaction
pass, gated-action resolution) reports its outcome through this one envelope
so callers never have to pattern-match ad hoc tuples or bare exceptions to
learn what happened. This module is pure: no I/O, no subprocess invocation,
no ``sys.exit``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

# The vocabulary is intentionally small and closed. Callers should not invent
# additional status strings; ``failed``/``blocked`` distinguish an
# unrecoverable error from a fail-closed refusal (e.g. a lock contention).
STATUSES = frozenset({"ok", "failed", "blocked", "cancelled"})


@dataclass(frozen=True)
class SupervisorResult:
    """Typed outcome envelope returned by every supervisor operation.

    Attributes:
        status: One of :data:`STATUSES`.
        exit_code: The machine-readable exit code associated with this
            outcome (``0`` for success; see
            :mod:`autoharness.supervise.errors` for the failure taxonomy).
        data: Arbitrary structured payload produced by the operation.
        messages: Human-readable informational messages, in emission order.
        warnings: Human-readable non-fatal warnings, in emission order.
        artifacts: Paths or identifiers of artifacts produced or touched by
            the operation (e.g. a journal checkpoint path).
    """

    status: str
    exit_code: int
    data: Mapping[str, Any] = field(default_factory=dict)
    messages: Sequence[str] = field(default_factory=tuple)
    warnings: Sequence[str] = field(default_factory=tuple)
    artifacts: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(
                f"SupervisorResult.status must be one of {sorted(STATUSES)}, got {self.status!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain, JSON-safe ``dict``."""

        return {
            "status": self.status,
            "exit_code": self.exit_code,
            "data": dict(self.data),
            "messages": list(self.messages),
            "warnings": list(self.warnings),
            "artifacts": list(self.artifacts),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SupervisorResult":
        """Reconstruct a :class:`SupervisorResult` from :meth:`to_dict` output."""

        return cls(
            status=payload["status"],
            exit_code=payload["exit_code"],
            data=dict(payload.get("data", {})),
            messages=tuple(payload.get("messages", ())),
            warnings=tuple(payload.get("warnings", ())),
            artifacts=tuple(payload.get("artifacts", ())),
        )
