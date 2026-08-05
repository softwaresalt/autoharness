"""Deterministic shipment/worktree topology gate.

Skeleton implementation for the ``autoharness gate pipeline-topology`` command.
It intentionally stays inside the ``autoharness.gates`` boundary and does not
import install/tune modules. The fully-populated topology and readiness checks
are layered onto this module in follow-up tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VALID_MODES = ("agent", "manual", "ci")
VALID_PHASES = ("pre_claim", "post_claim", "lifecycle", "ambient")
SCOPED_PHASES = ("pre_claim", "post_claim", "lifecycle")


@dataclass(frozen=True)
class TopologyInput:
    mode: str
    phase: str | None
    target_shipment_id: str | None
    emit_json: bool = False
    force: bool = False


@dataclass(frozen=True)
class TopologyResult:
    mode: str
    phase: str
    resolved_target_shipment_id: str | None
    exit_code: int = 0
    message: str = "topology gate skeleton"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "phase": self.phase,
            "target_shipment_id": self.resolved_target_shipment_id,
            "exit_code": self.exit_code,
            "message": self.message,
        }


def evaluate(topology_input: TopologyInput) -> TopologyResult:
    """Resolve the command shape and echo it back in a JSON-capable report."""
    if topology_input.mode not in VALID_MODES:
        return TopologyResult(
            mode=topology_input.mode,
            phase=topology_input.phase or "ambient",
            resolved_target_shipment_id=topology_input.target_shipment_id,
            exit_code=2,
            message=f"invalid mode: {topology_input.mode!r}",
        )

    resolved_phase = topology_input.phase or ("ambient" if topology_input.mode in ("manual", "ci") else "")
    if topology_input.mode == "agent":
        target = (topology_input.target_shipment_id or "").strip()
        if not target:
            return TopologyResult(
                mode=topology_input.mode,
                phase=resolved_phase or "ambient",
                resolved_target_shipment_id=None,
                exit_code=2,
                message="agent mode requires --shipment <shipment_id>",
            )
        if resolved_phase not in SCOPED_PHASES:
            return TopologyResult(
                mode=topology_input.mode,
                phase=resolved_phase or "ambient",
                resolved_target_shipment_id=target,
                exit_code=2,
                message="agent mode requires --phase pre_claim|post_claim|lifecycle",
            )
        return TopologyResult(topology_input.mode, resolved_phase, target)

    if resolved_phase not in VALID_PHASES:
        return TopologyResult(
            mode=topology_input.mode,
            phase=resolved_phase or "ambient",
            resolved_target_shipment_id=topology_input.target_shipment_id,
            exit_code=2,
            message=f"invalid phase: {resolved_phase!r}",
        )

    target = (topology_input.target_shipment_id or "").strip() or None
    return TopologyResult(topology_input.mode, resolved_phase, target)
