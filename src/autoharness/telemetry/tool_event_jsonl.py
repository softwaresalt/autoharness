"""Bounded ToolTelemetryEvent JSONL journal (U3, 084.003-T).

A segmented, best-effort JSONL journal for :class:`ToolTelemetryEvent` records,
built on the shared primitives in ``_jsonl_segments.py`` (U2) so it shares
identical segment rotation, retention, replay-scan, and atomic-append
semantics with the execution-epoch JSONL sink (``jsonl_sink.py``) under its
own independent rotation bounds and generation sequence.

**Path derivation:** the journal path is derived from the already-enabled
telemetry directory — beside the configured epoch SQLite database — with NO
new configuration fields (per the plan's decision to avoid a schema-versioned
bump across the telemetry config surface for a workspace-wide constant).

**Fail-open / disabled contract:** callers MUST check ``TelemetryConfig.enabled``
before invoking this module's I/O — mirroring ``record.py``'s pattern, telemetry
disablement short-circuits before any read or validation of caller-supplied
input. :func:`record_tool_event` implements that check directly; direct callers
of :func:`append_event` are expected to have already gated on
``config.enabled``.

**No raw output / secrets:** this journal only ever persists the fields already
validated by :class:`~autoharness.telemetry.tool_event.ToolTelemetryEvent` — no
raw tool output, prompts, stderr, or credentials are accepted by that model, so
none can reach this journal.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from autoharness.telemetry import _jsonl_segments
from autoharness.telemetry._jsonl_segments import (
    JsonlPreflightScan,
    SinkWriteResult,
    TelemetryConflictError,
    sealed_segments,
    segment_read_paths,
)
from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.tool_event import (
    ToolTelemetryEvent,
    ToolTelemetryEventError,
    event_correlates,
)

logger = logging.getLogger(__name__)

# Beside the configured epoch database, alongside execution_epochs.jsonl. No new
# TelemetryConfig field: derived deterministically from database_path.parent so
# no schema-versioned config bump is needed for this workspace-wide constant.
TOOL_EVENTS_JSONL_NAME = "tool_events.jsonl"

# Independent rotation/retention bounds for the event journal (own generation
# sequence from the epoch JSONL sink's). Same rationale as jsonl_sink.py: module
# constants, not TelemetryConfig fields; tests patch these locally.
_MAX_SEGMENT_BYTES = 8 * 1024 * 1024
_MAX_RETAINED_SEGMENTS = 8

__all__ = [
    "JsonlPreflightScan",
    "SinkWriteResult",
    "TelemetryConflictError",
    "ToolEventReadResult",
    "ToolEventRecordSummary",
    "append_event",
    "find_event_digest",
    "journal_path_for_config",
    "read_events",
    "record_tool_event",
    "scan_event_digest",
]


def journal_path_for_config(config: TelemetryConfig) -> Path | None:
    """Return the ToolTelemetryEvent journal path for an enabled config, or
    ``None`` when telemetry is disabled or no database path is configured."""
    if not config.enabled or config.database_path is None:
        return None
    return config.database_path.parent / TOOL_EVENTS_JSONL_NAME


def _max_sealed_generation(jsonl_path: Path) -> int:
    generations = sealed_segments(jsonl_path)
    return generations[-1][0] if generations else 0


def _active_generation(jsonl_path: Path) -> int:
    return _max_sealed_generation(jsonl_path) + 1


def _seal_active_segment(jsonl_path: Path) -> int | None:
    return _jsonl_segments.seal_active_segment(
        jsonl_path, max_sealed_generation_fn=_max_sealed_generation
    )


def _rollover_if_needed(jsonl_path: Path) -> None:
    _jsonl_segments.rollover_if_needed(
        jsonl_path,
        max_segment_bytes=_MAX_SEGMENT_BYTES,
        max_retained_segments=_MAX_RETAINED_SEGMENTS,
        max_sealed_generation_fn=_max_sealed_generation,
    )


def _prune_sealed_segments(jsonl_path: Path) -> None:
    _jsonl_segments.prune_sealed_segments(
        jsonl_path, max_retained_segments=_MAX_RETAINED_SEGMENTS
    )


def scan_event_digest(
    jsonl_path: Path,
    event_id: str,
    *,
    start_offset: int = 0,
) -> JsonlPreflightScan:
    """Return digest and active-segment identity when scanning for ``event_id``
    across the active segment plus all retained sealed segments."""
    return _jsonl_segments.scan_key_digest(
        jsonl_path,
        "event_id",
        event_id,
        active_generation_fn=_active_generation,
        start_offset=start_offset,
    )


def find_event_digest(jsonl_path: Path, event_id: str) -> str | None:
    """Return the digest for the first accepted JSONL record with ``event_id``."""
    return scan_event_digest(jsonl_path, event_id).existing_digest


def _revalidate_preflight(
    jsonl_path: Path,
    event_id: str,
    scan: JsonlPreflightScan,
) -> str | None:
    return _jsonl_segments.revalidate_preflight(
        jsonl_path,
        event_id,
        scan,
        active_generation_fn=_active_generation,
        scan_fn=scan_event_digest,
    )


def append_event(
    event: ToolTelemetryEvent,
    jsonl_path: Path,
    *,
    preflight: JsonlPreflightScan | None = None,
) -> SinkWriteResult:
    """Append one ToolTelemetryEvent as a single atomic JSON line.

    Dedupes across retained segments by ``event_id``: an identical replay is
    idempotent (``status="idempotent_replay"``); a same-``event_id`` replay
    whose canonical content differs raises :class:`TelemetryConflictError`
    with a diagnostic rather than silently overwriting or duplicating.
    """
    record = event.to_dict()
    line_json = json.dumps(record, separators=(",", ":"))
    return _jsonl_segments.append_record(
        jsonl_path=jsonl_path,
        key_field="event_id",
        key_value=event.event_id,
        record=record,
        line_json=line_json,
        preflight=preflight,
        scan_fn=scan_event_digest,
        revalidate_fn=_revalidate_preflight,
        rollover_fn=_rollover_if_needed,
    )


@dataclass
class ToolEventRecordSummary:
    """Outcome of appending one event through :func:`record_tool_event`."""

    enabled: bool = False
    written: bool = False
    status: str | None = None
    payload_digest: str | None = None
    event_id: str | None = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "written": self.written,
            "status": self.status,
            "payload_digest": self.payload_digest,
            "event_id": self.event_id,
            "errors": list(self.errors),
        }


def record_tool_event(event: ToolTelemetryEvent, config: TelemetryConfig) -> ToolEventRecordSummary:
    """Append ``event`` to the journal derived from ``config``, failing open.

    Disabled telemetry returns immediately (no journal I/O). A sink failure
    (I/O error, unexpected exception) is captured in the summary's ``errors``
    rather than raised, mirroring ``record.py``'s fail-open sink dispatch — a
    broken journal write must never block task completion. A conflicting
    replay is reported via ``errors`` with ``status="conflict_rejected"``.
    """
    summary = ToolEventRecordSummary(enabled=config.enabled, event_id=event.event_id)
    if not config.enabled:
        summary.status = "disabled"
        return summary

    jsonl_path = journal_path_for_config(config)
    if jsonl_path is None:
        summary.status = "disabled"
        return summary

    try:
        result = append_event(event, jsonl_path)
        summary.status = result.status
        summary.payload_digest = result.payload_digest
        summary.written = True
    except TelemetryConflictError as exc:
        summary.errors.append(f"tool event journal conflict: {exc}")
        summary.status = "conflict_rejected"
        logger.warning("Tool event journal conflict for %s: %s", event.event_id, exc)
    except Exception as exc:  # fail-open: never block task completion
        summary.errors.append(f"tool event journal write failed: {exc}")
        summary.status = "write_failed"
        logger.warning("Tool event journal write failed for %s: %s", event.event_id, exc)
    return summary


@dataclass(frozen=True)
class ToolEventReadResult:
    status: str
    events: tuple[ToolTelemetryEvent, ...] = ()
    diagnostics: tuple[str, ...] = ()




def read_events(
    jsonl_path: Path | None,
    *,
    epoch_id: str | None = None,
    backlog_item_id: str | None = None,
) -> ToolEventReadResult:
    """Stream exact-correlation reads across all retained segments.

    Selects events whose ``epoch_id`` exactly matches ``epoch_id`` (when the
    event carries one), or — only for events with NO ``epoch_id`` — whose
    ``backlog_item_id`` exactly matches ``backlog_item_id``. Malformed lines are
    skipped with a diagnostic, never crashing the read. Duplicate ``event_id``
    entries across segments are deduplicated (first-write wins); a later
    conflicting replay is reported as a diagnostic, not raised.
    """
    if jsonl_path is None:
        return ToolEventReadResult(status="disabled")
    segment_paths = segment_read_paths(jsonl_path)
    if not segment_paths:
        return ToolEventReadResult(status="empty")

    diagnostics: list[str] = []
    by_id: dict[str, tuple[ToolTelemetryEvent, str]] = {}
    for segment in segment_paths:
        try:
            with segment.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        raw = json.loads(line)
                        event = ToolTelemetryEvent.from_mapping(raw)
                    except (json.JSONDecodeError, ToolTelemetryEventError, TypeError, ValueError) as exc:
                        diagnostics.append(
                            f"tool event journal skipped malformed line {line_number} "
                            f"in {segment.name}: {exc}"
                        )
                        continue
                    digest = _jsonl_segments.digest_record(event.to_dict())
                    existing = by_id.get(event.event_id)
                    if existing is None:
                        by_id[event.event_id] = (event, digest)
                    elif existing[1] != digest:
                        diagnostics.append(
                            f"tool event journal conflict for event_id {event.event_id}: "
                            f"first accepted digest {existing[1]} != later digest {digest}"
                        )
        except OSError as exc:
            diagnostics.append(f"tool event journal unavailable: {exc}")

    selected = [
        event
        for event, _digest in by_id.values()
        if event_correlates(event, epoch_id=epoch_id, backlog_item_id=backlog_item_id)
    ]
    status = "ok" if selected else "empty"
    return ToolEventReadResult(status=status, events=tuple(selected), diagnostics=tuple(diagnostics))
