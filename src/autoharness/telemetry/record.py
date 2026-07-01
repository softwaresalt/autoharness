"""Epoch record dispatch — routes an epoch to every enabled sink (U5).

This is the CLI-facing realization of the design's "Execution Epoch Emitter".
Because autoharness is an install/tune tool with **no in-process execution loop**
to wrap, the harness runtime supplies a fully-formed epoch payload at task close
and this module fans it out to the configured sinks.

**Fail-open:** telemetry is observational and off the completion critical path.
A failing or misconfigured sink is captured in the returned summary — it never
raises out of :func:`record_epoch`, so a broken sink can never block task
completion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from autoharness.telemetry import jsonl_sink, sqlite_sink
from autoharness.telemetry.config import TelemetryConfig, load_telemetry_config
from autoharness.telemetry.epoch import ExecutionEpoch


@dataclass
class RecordSummary:
    """Outcome of a record dispatch — surfaced as monitoring signal."""

    enabled: bool = False
    sqlite_written: bool = False
    jsonl_written: bool = False
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "sqlite_written": self.sqlite_written,
            "jsonl_written": self.jsonl_written,
            "errors": list(self.errors),
        }


def record_epoch(epoch: ExecutionEpoch, config: TelemetryConfig) -> RecordSummary:
    """Dispatch an epoch to every enabled sink, failing open on sink errors."""
    summary = RecordSummary(enabled=config.enabled)
    if not config.enabled:
        return summary

    if config.database_path is not None:
        try:
            sqlite_sink.write_epoch(epoch, config.database_path)
            summary.sqlite_written = True
        except Exception as exc:  # fail-open: never block completion
            summary.errors.append(f"sqlite sink failed: {exc}")

    if config.emit_jsonl and config.jsonl_path is not None:
        try:
            jsonl_sink.append_epoch(epoch, config.jsonl_path)
            summary.jsonl_written = True
        except Exception as exc:  # fail-open: never block completion
            summary.errors.append(f"jsonl sink failed: {exc}")

    return summary


def load_workspace_telemetry_config(workspace: Path) -> TelemetryConfig:
    """Read ``<workspace>/.autoharness/config.yaml`` and load its telemetry block.

    An absent config file or absent/``none`` telemetry block yields a disabled
    config (fail-open). This reads the raw ``telemetry`` mapping directly so the
    telemetry package stays decoupled from ``gates/``.
    """
    import yaml

    config_path = workspace / ".autoharness" / "config.yaml"
    telemetry_block: Any = None
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            telemetry_block = loaded.get("telemetry")
    return load_telemetry_config(telemetry_block, workspace_root=workspace)
