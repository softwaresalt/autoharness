"""Typed telemetry configuration loader (Phase 2, U2).

Consumes the already-parsed ``telemetry`` mapping (from ``GatesConfig.telemetry``
or a raw dict) into an immutable :class:`TelemetryConfig`. This module is
deliberately free of any import from ``gates/``, ``verify_workspace``, or the
install/tune modules — telemetry evolves independently of gating (P2-2).

An absent mapping, an empty mapping, or ``mode: none`` yields a disabled config:
the fail-open-to-current default with no emission and no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

DEFAULT_DATABASE_PATH = ".autoharness/metrics/execution_epochs.db"
DEFAULT_JSONL_NAME = "execution_epochs.jsonl"
VALID_MODES = ("sqlite", "none")


class TelemetryConfigError(ValueError):
    """Raised when a present telemetry block declares an unsupported mode."""


@dataclass(frozen=True)
class TelemetryConfig:
    """Parsed telemetry configuration.

    ``enabled`` is True only for ``mode: sqlite``. An absent block or
    ``mode: none`` produces a disabled config (no-op).
    """

    enabled: bool = False
    mode: str = "none"
    database_path: Path | None = None
    emit_jsonl: bool = False
    jsonl_path: Path | None = None


def _resolve(root: Path, raw: str) -> Path:
    """Resolve a possibly repo-relative path against the workspace root."""
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    return (root / candidate).resolve()


def load_telemetry_config(
    telemetry: Any,
    *,
    workspace_root: Path | str | None = None,
) -> TelemetryConfig:
    """Load a typed telemetry configuration from a raw ``telemetry`` mapping.

    Args:
        telemetry: The parsed ``telemetry`` mapping. Anything that is not a
            non-empty mapping, or whose ``mode`` is ``none``, yields a disabled
            config (no behavior change).
        workspace_root: The workspace root that repo-relative ``database_path``
            values resolve against. Defaults to the current working directory.

    Returns:
        A :class:`TelemetryConfig`. ``enabled`` is False when telemetry is off.

    Raises:
        TelemetryConfigError: when a present block declares an unsupported mode.
    """
    root = Path(workspace_root) if workspace_root is not None else Path.cwd()

    if not isinstance(telemetry, Mapping) or not telemetry:
        return TelemetryConfig()

    mode = str(telemetry.get("mode", "none")).lower()
    if mode == "none":
        return TelemetryConfig(mode="none")
    if mode not in VALID_MODES:
        raise TelemetryConfigError(
            f"Unsupported telemetry mode {mode!r}; expected one of {VALID_MODES}."
        )

    db_raw = telemetry.get("database_path") or DEFAULT_DATABASE_PATH
    database_path = _resolve(root, str(db_raw))
    emit_jsonl = bool(telemetry.get("emit_jsonl", False))
    jsonl_path = database_path.parent / DEFAULT_JSONL_NAME

    return TelemetryConfig(
        enabled=True,
        mode="sqlite",
        database_path=database_path,
        emit_jsonl=emit_jsonl,
        jsonl_path=jsonl_path,
    )
