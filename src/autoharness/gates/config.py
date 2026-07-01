"""Typed configuration model + loader for deterministic validation gates.

An absent ``lifecycle_hooks`` block is a no-op: :func:`load_gates_config`
returns a disabled :class:`GatesConfig` and the caller behaves exactly as an
install without gates (fail-open-to-current). A present block is validated
against the versioned validation-gates JSON Schema and parsed into a typed,
immutable structure.

This module is deliberately free of any dependency on install/tune modules.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator


class GatesConfigError(ValueError):
    """Raised when a present lifecycle_hooks/telemetry block is invalid."""


@dataclass(frozen=True)
class ValidationGate:
    """A single pattern → command validation gate."""

    pattern: str
    command: str
    timeout_seconds: int
    enforcement: str | None = None


@dataclass(frozen=True)
class PreExecutionAction:
    """A pre-execution lifecycle action (e.g. complexity sizing)."""

    name: str
    action: str
    condition: str | None = None
    write_back: str | None = None


@dataclass(frozen=True)
class GatePolicy:
    """pre_task_completion gate policy + the validation gates it governs."""

    enforcement: str = "absolute"
    on_repeated_failure: str = "block"
    max_gate_failures: int = 3
    validation_gates: tuple[ValidationGate, ...] = ()


@dataclass(frozen=True)
class LifecycleHooks:
    """Parsed lifecycle_hooks block."""

    pre_execution: tuple[PreExecutionAction, ...] = ()
    pre_task_completion: GatePolicy | None = None


@dataclass(frozen=True)
class GatesConfig:
    """Top-level parsed gate configuration.

    ``enabled`` is True only when validation gates are actually configured. An
    absent, null, or emptied ``lifecycle_hooks`` block (the kill-switch) yields
    a disabled config — the fail-open-to-current default.
    """

    enabled: bool = False
    lifecycle_hooks: LifecycleHooks | None = None
    telemetry: dict[str, Any] = field(default_factory=dict)

    @property
    def validation_gates(self) -> tuple[ValidationGate, ...]:
        if self.lifecycle_hooks and self.lifecycle_hooks.pre_task_completion:
            return self.lifecycle_hooks.pre_task_completion.validation_gates
        return ()

    @property
    def policy(self) -> GatePolicy:
        if self.lifecycle_hooks and self.lifecycle_hooks.pre_task_completion:
            return self.lifecycle_hooks.pre_task_completion
        return GatePolicy()


def _validate(config_data: dict[str, Any], schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(config_data), key=lambda e: list(e.path))
    if errors:
        joined = "; ".join(
            f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}" for err in errors
        )
        raise GatesConfigError(f"Invalid lifecycle_hooks/telemetry configuration: {joined}")


def _parse_gate(raw: dict[str, Any]) -> ValidationGate:
    return ValidationGate(
        pattern=raw["pattern"],
        command=raw["command"],
        timeout_seconds=int(raw["timeout_seconds"]),
        enforcement=raw.get("enforcement"),
    )


def _parse_policy(raw: dict[str, Any]) -> GatePolicy:
    gates = tuple(_parse_gate(g) for g in raw.get("validation_gates", []))
    return GatePolicy(
        enforcement=raw.get("enforcement", "absolute"),
        on_repeated_failure=raw.get("on_repeated_failure", "block"),
        max_gate_failures=int(raw.get("max_gate_failures", 3)),
        validation_gates=gates,
    )


def _parse_action(raw: dict[str, Any]) -> PreExecutionAction:
    return PreExecutionAction(
        name=raw["name"],
        action=raw["action"],
        condition=raw.get("condition"),
        write_back=raw.get("write_back"),
    )


def _is_empty_block(value: Any) -> bool:
    """A block emptied via the kill-switch parses as YAML null or an empty map."""
    return value is None or (isinstance(value, dict) and not value)


def load_gates_config(
    config_data: Any,
    *,
    schema_path: Path | None = None,
) -> GatesConfig:
    """Load and (optionally) validate the gate configuration.

    Args:
        config_data: The parsed ``.autoharness/config.yaml`` mapping (or any
            mapping containing ``lifecycle_hooks``/``telemetry``). Anything that
            is not a mapping, or whose ``lifecycle_hooks``/``telemetry`` content
            is absent, null, or emptied (the kill-switch), yields a disabled
            config (no behavior change). A
            ``telemetry``-only mapping yields a disabled config whose telemetry
            block is retained for forward compatibility.
        schema_path: Path to the versioned validation-gates JSON Schema. When
            provided and a ``lifecycle_hooks`` block is present, the block is
            validated before parsing. When ``None``, validation is skipped.

    Returns:
        A :class:`GatesConfig`. ``enabled`` is False when no gates are present.

    Raises:
        GatesConfigError: When a present block fails schema validation.
    """
    if not isinstance(config_data, dict):
        return GatesConfig(enabled=False)

    lifecycle_raw = config_data.get("lifecycle_hooks")
    telemetry_raw = config_data.get("telemetry")

    # The documented kill-switch is "remove OR empty the block". In YAML an
    # emptied key parses as null (or an empty mapping), so a null/empty block is
    # normalized to "absent": gating is disabled without failing validation.
    lifecycle_absent = "lifecycle_hooks" not in config_data or _is_empty_block(lifecycle_raw)
    telemetry_absent = "telemetry" not in config_data or _is_empty_block(telemetry_raw)

    if lifecycle_absent and telemetry_absent:
        return GatesConfig(enabled=False)

    if schema_path is not None:
        _validate(config_data, schema_path)

    telemetry = telemetry_raw if (not telemetry_absent and isinstance(telemetry_raw, dict)) else {}

    if lifecycle_absent:
        # Telemetry-only configuration: gates stay disabled (fail-open-to-current
        # for gating), but the telemetry block is retained for forward compatibility.
        return GatesConfig(enabled=False, telemetry=telemetry)

    if not isinstance(lifecycle_raw, dict):
        raise GatesConfigError("lifecycle_hooks must be a mapping when present.")

    pre_execution = tuple(_parse_action(a) for a in lifecycle_raw.get("pre_execution", []))
    ptc_raw = lifecycle_raw.get("pre_task_completion")
    pre_task_completion = _parse_policy(ptc_raw) if isinstance(ptc_raw, dict) else None

    # "enabled" reflects whether any validation gates are actually configured;
    # Phase 1 executes only pre_task_completion validation_gates.
    enabled = bool(pre_task_completion and pre_task_completion.validation_gates)

    return GatesConfig(
        enabled=enabled,
        lifecycle_hooks=LifecycleHooks(
            pre_execution=pre_execution,
            pre_task_completion=pre_task_completion,
        ),
        telemetry=telemetry,
    )
