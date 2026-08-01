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

from autoharness.telemetry import jsonl_sink, sqlite_sink, tool_event_jsonl
from autoharness.telemetry.config import TelemetryConfig, load_telemetry_config
from autoharness.telemetry.epoch import ExecutionEpoch
from autoharness.telemetry.tool_event_compose import (
    ToolEventCompositionError,
    apply_composition_patch,
    compose_tool_events as _compose_tool_events,
    detect_hybrid_fields,
)


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
    idempotency_outcome: str | None = "disabled"
    errors: list[str] = field(default_factory=list)
    missing_provenance: dict[str, list[str]] = field(default_factory=dict)
    composition_requested: bool = False
    composition_applied: bool = False
    composed_selected_event_count: int = 0
    composed_ignored_event_count: int = 0
    composition_diagnostics: list[str] = field(default_factory=list)

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
            "missing_provenance": {
                section: list(metrics)
                for section, metrics in self.missing_provenance.items()
            },
            "errors": list(self.errors),
            "composition_requested": self.composition_requested,
            "composition_applied": self.composition_applied,
            "composed_selected_event_count": self.composed_selected_event_count,
            "composed_ignored_event_count": self.composed_ignored_event_count,
            "composition_diagnostics": list(self.composition_diagnostics),
        }


def _missing_provenance(epoch: ExecutionEpoch) -> dict[str, list[str]]:
    sections = {
        "economics": epoch.economics.missing_provenance(),
        "operations": epoch.operations.missing_provenance(),
        "outcome": epoch.outcome.missing_provenance(),
    }
    return {
        section: list(metrics)
        for section, metrics in sections.items()
        if metrics
    }


def _preflight_conflict(
    epoch: ExecutionEpoch,
    config: TelemetryConfig,
    summary: RecordSummary,
) -> tuple[bool, Any | None]:
    digest = sqlite_sink.payload_digest(epoch)
    summary.payload_digest = digest
    observed: list[tuple[str, str]] = []
    jsonl_preflight = None

    if config.database_path is not None:
        try:
            existing = sqlite_sink.find_epoch_digest(config.database_path, epoch.epoch_id)
            if existing is not None:
                observed.append(("sqlite", existing))
        except Exception as exc:
            summary.errors.append(f"sqlite sink preflight failed: {exc}")

    if config.emit_jsonl and config.jsonl_path is not None:
        try:
            jsonl_preflight = jsonl_sink.scan_epoch_digest(config.jsonl_path, epoch.epoch_id)
            existing = jsonl_preflight.existing_digest
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
        return True, jsonl_preflight
    return False, jsonl_preflight


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


def record_epoch(
    epoch: ExecutionEpoch,
    config: TelemetryConfig,
    *,
    compose_tool_events: bool = False,
) -> RecordSummary:
    """Dispatch an epoch to every enabled sink, failing open on sink errors.

    ``compose_tool_events`` is an opt-in flag (084.005-T / U5): when ``True``,
    the U3 ToolTelemetryEvent journal derived from ``config`` is read, events
    correlated to ``epoch.epoch_id``/``epoch.backlog_item_id`` are selected
    (exact ``epoch_id`` match first; ``backlog_item_id`` fallback only for
    events with no ``epoch_id`` at all — decision 5), and the resulting
    composer-owned patch (route/economics/operations/outcome — see
    :mod:`autoharness.telemetry.tool_event_compose`) is merged onto the
    close-supplied epoch before it is dispatched to sinks. Every other
    close-payload field (``gate_exit_codes``, ``cogs_usd``,
    ``duration_seconds``, and all root-level identity fields) is preserved
    verbatim (decision 6).

    **Hybrid refusal (fail CLOSED):** if the close-supplied epoch already
    populates a composer-owned field with a nonzero/non-empty value while
    composition is requested, :class:`ToolEventCompositionError` is raised —
    this is the one case where this function does NOT fail open, because
    silently picking either side would double-count or silently discard data
    (decision 6).

    **Composition I/O failures fail OPEN:** a missing or unreadable journal,
    or any other unexpected error while reading/composing events, is recorded
    in ``composition_diagnostics`` and the original (unmerged) close payload
    is recorded exactly as if composition had not been requested — a missing
    event journal must never block task completion.

    When ``compose_tool_events`` is left at its default (``False``), this
    function's behavior is byte-for-byte identical to the pre-U5 code path.
    """
    summary = RecordSummary(enabled=config.enabled, epoch_id=epoch.epoch_id)
    if not config.enabled:
        summary.idempotency_outcome = "disabled"
        return summary

    summary.composition_requested = compose_tool_events
    if compose_tool_events:
        hybrid_fields = detect_hybrid_fields(epoch)
        if hybrid_fields:
            raise ToolEventCompositionError(
                "compose_tool_events requested but the close payload already "
                "supplies composer-owned field(s): "
                + ", ".join(hybrid_fields)
                + ". Refusing hybrid input to prevent double counting or silent "
                "data loss (decision 6)."
            )
        try:
            journal_path = tool_event_jsonl.journal_path_for_config(config)
            read_result = tool_event_jsonl.read_events(
                journal_path,
                epoch_id=epoch.epoch_id,
                backlog_item_id=epoch.backlog_item_id,
            )
            summary.composition_diagnostics.extend(read_result.diagnostics)
            if read_result.status == "unavailable":
                # A segment I/O failure: read_events already reports no
                # events for this status (never a partial/undercounted
                # subset). Skip composition entirely so the original
                # close-supplied payload persists unmerged, matching the
                # documented fail-open contract, rather than recording an
                # undercounted roll-up as the immutable epoch.
                summary.composition_diagnostics.append(
                    "tool-event composition skipped: journal read unavailable "
                    "(segment I/O failure)"
                )
            else:
                composition = _compose_tool_events(
                    read_result.events,
                    epoch_id=epoch.epoch_id,
                    backlog_item_id=epoch.backlog_item_id,
                )
                summary.composed_selected_event_count = composition.selected_event_count
                summary.composed_ignored_event_count = composition.ignored_event_count
                summary.composition_diagnostics.extend(composition.diagnostics)
                epoch = apply_composition_patch(epoch, composition)
                summary.composition_applied = True
        except ToolEventCompositionError:
            raise
        except Exception as exc:  # fail-open: composition I/O never blocks completion
            summary.composition_diagnostics.append(
                f"tool-event composition unavailable: {exc}"
            )

    summary.missing_provenance = _missing_provenance(epoch)

    has_conflict, jsonl_preflight = _preflight_conflict(epoch, config, summary)
    if has_conflict:
        return summary

    if config.database_path is not None:
        try:
            sqlite_result = sqlite_sink.write_epoch(epoch, config.database_path)
            summary.sqlite_status = sqlite_result.status
            summary.payload_digest = sqlite_result.payload_digest
            summary.sqlite_written = True
        except sqlite_sink.TelemetryConflictError as exc:
            summary.errors.append(f"sqlite sink conflict: {exc}")
            # Copilot review t3: a conflict raised here (another writer inserted
            # after preflight) still returns early, so finalize the documented
            # conflict_rejected outcome before returning instead of leaving it unset.
            summary.idempotency_outcome = "conflict_rejected"
            return summary
        except Exception as exc:  # fail-open: never block completion
            summary.errors.append(f"sqlite sink failed: {exc}")

    if config.emit_jsonl and config.jsonl_path is not None:
        try:
            jsonl_result = jsonl_sink.append_epoch(
                epoch,
                config.jsonl_path,
                preflight=jsonl_preflight,
            )
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
