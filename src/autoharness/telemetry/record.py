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
    sqlite_status: str | None = None
    jsonl_status: str | None = None
    payload_digest: str | None = None
    epoch_id: str | None = None
    context_ref: str | None = None
    context_digest: str | None = None
    idempotency_outcome: str | None = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "sqlite_written": self.sqlite_written,
            "jsonl_written": self.jsonl_written,
            "sqlite_status": self.sqlite_status,
            "jsonl_status": self.jsonl_status,
            "payload_digest": self.payload_digest,
            "epoch_id": self.epoch_id,
            "context_ref": self.context_ref,
            "context_digest": self.context_digest,
            "idempotency_outcome": self.idempotency_outcome,
            "errors": list(self.errors),
        }


def _preflight_conflict(epoch: ExecutionEpoch, config: TelemetryConfig, summary: RecordSummary) -> bool:
    digest = sqlite_sink.payload_digest(epoch)
    summary.payload_digest = digest
    observed: list[tuple[str, str]] = []

    if config.database_path is not None:
        try:
            existing = sqlite_sink.find_epoch_digest(config.database_path, epoch.epoch_id)
            if existing is not None:
                observed.append(("sqlite", existing))
        except Exception as exc:
            summary.errors.append(f"sqlite sink preflight failed: {exc}")

    if config.emit_jsonl and config.jsonl_path is not None:
        try:
            existing = jsonl_sink.find_epoch_digest(config.jsonl_path, epoch.epoch_id)
            if existing is not None:
                observed.append(("jsonl", existing))
        except Exception as exc:
            summary.errors.append(f"jsonl sink preflight failed: {exc}")

    conflicts = [
        f"{name} digest {existing} != {digest}"
        for name, existing in observed
        if existing != digest
    ]
    if conflicts:
        summary.errors.append(
            f"immutable epoch conflict for {epoch.epoch_id}: " + "; ".join(conflicts)
        )
        summary.idempotency_outcome = "conflict_rejected"
        return True
    return False


def _finalize_idempotency(summary: RecordSummary) -> None:
    if summary.idempotency_outcome == "conflict_rejected":
        return
    statuses = [
        status
        for status in (summary.sqlite_status, summary.jsonl_status)
        if status is not None
    ]
    if any("conflict" in err.lower() for err in summary.errors):
        summary.idempotency_outcome = "conflict_rejected"
    elif statuses and all(status == "idempotent_replay" for status in statuses):
        summary.idempotency_outcome = "idempotent_replay"
    elif "created" in statuses and "idempotent_replay" in statuses:
        summary.idempotency_outcome = "partial_repaired"
    elif "created" in statuses:
        summary.idempotency_outcome = "created"
    else:
        summary.idempotency_outcome = "created" if summary.sqlite_written or summary.jsonl_written else "disabled"


def record_epoch(epoch: ExecutionEpoch, config: TelemetryConfig) -> RecordSummary:
    """Dispatch an epoch to every enabled sink, failing open on sink errors."""
    summary = RecordSummary(enabled=config.enabled, epoch_id=epoch.epoch_id)
    if not config.enabled:
        summary.idempotency_outcome = "disabled"
        return summary

    if _preflight_conflict(epoch, config, summary):
        return summary

    if config.database_path is not None:
        try:
            sqlite_result = sqlite_sink.write_epoch(epoch, config.database_path)
            summary.sqlite_status = sqlite_result.status
            summary.payload_digest = sqlite_result.payload_digest
            summary.sqlite_written = True
        except sqlite_sink.TelemetryConflictError as exc:
            summary.errors.append(f"sqlite sink conflict: {exc}")
            return summary
        except Exception as exc:  # fail-open: never block completion
            summary.errors.append(f"sqlite sink failed: {exc}")

    if config.emit_jsonl and config.jsonl_path is not None:
        try:
            jsonl_result = jsonl_sink.append_epoch(epoch, config.jsonl_path)
            summary.jsonl_status = jsonl_result.status
            summary.payload_digest = jsonl_result.payload_digest
            summary.jsonl_written = True
        except jsonl_sink.TelemetryConflictError as exc:
            summary.errors.append(f"jsonl sink conflict: {exc}")
        except Exception as exc:  # fail-open: never block completion
            summary.errors.append(f"jsonl sink failed: {exc}")

    _finalize_idempotency(summary)
    return summary


def load_workspace_telemetry_config(workspace: Path) -> TelemetryConfig:
    """Read ``<workspace>/.autoharness/config.yaml`` and load its telemetry block.

    Fail-open: an absent config file, an absent/``none`` telemetry block, an
    unreadable file, malformed YAML, or an invalid telemetry block all yield a
    disabled config. No parse error ever propagates — telemetry is off the
    completion critical path.
    """
    import logging

    import yaml

    from autoharness.telemetry.config import TelemetryConfigError

    logger = logging.getLogger(__name__)

    config_path = workspace / ".autoharness" / "config.yaml"
    telemetry_block: Any = None
    try:
        if config_path.exists():
            loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                telemetry_block = loaded.get("telemetry")
        return load_telemetry_config(telemetry_block, workspace_root=workspace)
    except (yaml.YAMLError, OSError, TelemetryConfigError) as exc:
        logger.warning("Telemetry disabled (fail-open): could not load config: %s", exc)
        return TelemetryConfig()
    except Exception as exc:  # fail-open: no config problem may block completion
        logger.warning("Telemetry disabled (fail-open): unexpected config error: %s", exc)
        return TelemetryConfig()
