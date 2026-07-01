"""Execution Epoch model — the four design-§4 payload classes.

An :class:`ExecutionEpoch` is the immutable, structured record the harness
runtime hands to ``autoharness telemetry record`` at task-completion time. It
composes the four payload classes named in the design doc:

* :class:`RouteConfiguration` — models used (route configuration)
* :class:`EconomicPayload` — tokens, COGS, duration
* :class:`OperationalReality` — CLI tools used
* :class:`AbsoluteOutcome` — gate exit codes

The serialized shape produced by :meth:`ExecutionEpoch.to_record` is the stable
contract shared by both sinks (SQLite + JSONL) and the external ingestion
boundary (agent-engram). ``from_mapping`` reverses it losslessly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

SCHEMA_VERSION = "1.0.0"


class EpochError(ValueError):
    """Raised when an epoch payload is malformed or a required class is missing."""


@dataclass(frozen=True)
class RouteConfiguration:
    """Route configuration — the models used during the epoch."""

    models: tuple[str, ...] = ()

    @property
    def primary_model(self) -> str | None:
        return self.models[0] if self.models else None

    def to_dict(self) -> dict[str, Any]:
        return {"models": list(self.models)}

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RouteConfiguration":
        return cls(models=tuple(data.get("models", ())))


@dataclass(frozen=True)
class EconomicPayload:
    """Economic payload — tokens, cost of goods sold, and wall-clock duration."""

    input_tokens: int = 0
    output_tokens: int = 0
    cogs_usd: float = 0.0
    duration_seconds: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cogs_usd": self.cogs_usd,
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "EconomicPayload":
        return cls(
            input_tokens=int(data.get("input_tokens", 0)),
            output_tokens=int(data.get("output_tokens", 0)),
            cogs_usd=float(data.get("cogs_usd", 0.0)),
            duration_seconds=float(data.get("duration_seconds", 0.0)),
        )


@dataclass(frozen=True)
class OperationalReality:
    """Operational reality — the CLI tools actually used during the epoch."""

    cli_tools: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"cli_tools": list(self.cli_tools)}

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "OperationalReality":
        return cls(cli_tools=tuple(data.get("cli_tools", ())))


@dataclass(frozen=True)
class AbsoluteOutcome:
    """Absolute outcome — the gate exit code(s) recorded for the epoch."""

    gate_exit_codes: tuple[int, ...] = ()

    @property
    def blocked(self) -> bool:
        """True when any recorded gate exited non-zero."""
        return any(code != 0 for code in self.gate_exit_codes)

    def to_dict(self) -> dict[str, Any]:
        return {"gate_exit_codes": list(self.gate_exit_codes)}

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "AbsoluteOutcome":
        return cls(gate_exit_codes=tuple(int(c) for c in data.get("gate_exit_codes", ())))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_PAYLOAD_TYPES = {
    "route": RouteConfiguration,
    "economics": EconomicPayload,
    "operations": OperationalReality,
    "outcome": AbsoluteOutcome,
}


@dataclass(frozen=True)
class ExecutionEpoch:
    """A single execution epoch composed of the four required payload classes."""

    task_id: str
    route: RouteConfiguration
    economics: EconomicPayload
    operations: OperationalReality
    outcome: AbsoluteOutcome
    epoch_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = field(default_factory=_utc_now_iso)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, expected in _PAYLOAD_TYPES.items():
            value = getattr(self, name)
            if not isinstance(value, expected):
                raise EpochError(
                    f"ExecutionEpoch.{name} must be a {expected.__name__} instance; "
                    f"got {type(value).__name__}."
                )

    def to_record(self) -> dict[str, Any]:
        """Return the stable serialized shape shared by every sink."""
        return {
            "epoch_id": self.epoch_id,
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "route": self.route.to_dict(),
            "economics": self.economics.to_dict(),
            "operations": self.operations.to_dict(),
            "outcome": self.outcome.to_dict(),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ExecutionEpoch":
        """Reconstruct an epoch from a mapping produced by :meth:`to_record`.

        Raises:
            EpochError: when the mapping is not a mapping, ``task_id`` is absent,
                or any of the four required payload classes is missing.
        """
        if not isinstance(data, Mapping):
            raise EpochError("Epoch payload must be a JSON object (mapping).")
        if "task_id" not in data:
            raise EpochError("Epoch payload is missing the required 'task_id' field.")
        for key in _PAYLOAD_TYPES:
            if key not in data:
                raise EpochError(f"Epoch payload is missing the required '{key}' payload class.")

        # Normalize every downstream shape/coercion failure (e.g. ``route: []``
        # raising AttributeError, or ``input_tokens: "abc"`` raising ValueError)
        # into a single controlled EpochError so the CLI never leaks a traceback.
        try:
            fields: dict[str, Any] = {
                "task_id": str(data["task_id"]),
                "route": RouteConfiguration.from_mapping(data["route"]),
                "economics": EconomicPayload.from_mapping(data["economics"]),
                "operations": OperationalReality.from_mapping(data["operations"]),
                "outcome": AbsoluteOutcome.from_mapping(data["outcome"]),
            }
            if data.get("epoch_id"):
                fields["epoch_id"] = str(data["epoch_id"])
            if data.get("timestamp"):
                fields["timestamp"] = str(data["timestamp"])
            if data.get("schema_version"):
                fields["schema_version"] = str(data["schema_version"])
            return cls(**fields)
        except EpochError:
            raise
        except (AttributeError, TypeError, ValueError, ArithmeticError) as exc:
            raise EpochError(f"Epoch payload is malformed: {exc}") from exc
