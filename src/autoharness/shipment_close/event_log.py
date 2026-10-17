"""Read-only reader for the backlogit engine event log (211-F, plan unit T1).

backlogit appends one JSON object per line to ``<backlog root>/logs/<id>.jsonl``.
This module reads those logs to find the facts the engine itself authored for a
shipment cascade (``shipment_status_changed -> shipped`` carrying
``_shipment_operation``) and reports, per item, the ``archived`` events and any
event authored by someone other than the engine.

The spike (``docs/spikes/2026-10-16-cascade-close-engine-event-log-provenance.md``)
established that item-level ``archived`` events carry only ``archive_path`` and
the actor ``backlogit`` regardless of who ran the archive, so they cannot, today,
be attributed to a cascade. :func:`attribute_archived_footprint` therefore
returns ``attributed=False`` unless every in-window archived event itself names
the cascade operation. Nothing here ever writes, and a missing, unreadable, or
malformed log is an :class:`EventLogError`, never an empty result.
"""

from __future__ import annotations

import datetime
import json
import os
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from autoharness.gates.cascade_evidence import CascadeEvidenceError, parse_rfc3339_instant

__all__ = [
    "ENGINE_ACTOR",
    "EVENT_LOG_DIR_NAME",
    "MAX_LOG_BYTES",
    "ArchiveAttribution",
    "CascadeEvents",
    "EngineEvent",
    "EventLogError",
    "attribute_archived_footprint",
    "read_cascade_events",
]

EVENT_LOG_DIR_NAME: Final = "logs"
ENGINE_ACTOR: Final = "backlogit"
MAX_LOG_BYTES: Final = 8 * 1024 * 1024
_OPERATION_KEY: Final = "_shipment_operation"

REASON_NO_CORRELATION: Final = "archived events carry no cascade operation correlation"
REASON_FOREIGN_ACTOR: Final = "a foreign-actor event touches a required item inside the window"
REASON_MISSING_ARCHIVE: Final = "a required id has no archived event inside the window"


class EventLogError(CascadeEvidenceError):
    """The event log is missing, unreadable, linked, oversized, or malformed."""


@dataclass(frozen=True)
class EngineEvent:
    item_id: str
    event_type: str
    actor: str
    timestamp: str
    instant: datetime.datetime
    delta: Mapping[str, object]

    @property
    def operation(self) -> str | None:
        value = self.delta.get(_OPERATION_KEY)
        return value if isinstance(value, str) else None


@dataclass(frozen=True)
class CascadeEvents:
    shipment_id: str
    since: datetime.datetime
    scope_item_ids: tuple[str, ...]
    shipped_events: tuple[EngineEvent, ...]
    released_events: tuple[EngineEvent, ...]
    archived_events: tuple[EngineEvent, ...]
    foreign_events: tuple[EngineEvent, ...]
    missing_item_logs: tuple[str, ...]


@dataclass(frozen=True)
class ArchiveAttribution:
    attributed: bool
    reason: str
    missing_ids: tuple[str, ...]
    uncorrelated_ids: tuple[str, ...]
    foreign_event_item_ids: tuple[str, ...]


def _is_link(path: Path) -> bool:
    from autoharness.gates.shipment_closure import _is_symlink_or_reparse_point

    return _is_symlink_or_reparse_point(path)


def _parse_event(raw: str, *, where: str, expected_item_id: str) -> EngineEvent:
    try:
        obj = json.loads(raw)
    except ValueError as exc:
        raise EventLogError(f"{where}: malformed JSON ({exc.__class__.__name__})") from exc
    if type(obj) is not dict:
        raise EventLogError(f"{where}: event is not an object")
    values: dict[str, str] = {}
    for key in ("timestamp", "actor", "item_id", "event_type"):
        value = obj.get(key)
        if type(value) is not str or not value:
            raise EventLogError(f"{where}: missing or non-string {key!r}")
        values[key] = value
    delta = obj.get("delta", {})
    if type(delta) is not dict:
        raise EventLogError(f"{where}: delta is not an object")
    if values["item_id"] != expected_item_id:
        raise EventLogError(f"{where}: item_id {values['item_id']!r} does not match its log {expected_item_id!r}")
    instant = parse_rfc3339_instant(values["timestamp"])
    if instant is None:
        raise EventLogError(f"{where}: timestamp is not an offset-bearing RFC 3339 instant")
    return EngineEvent(
        item_id=values["item_id"],
        event_type=values["event_type"],
        actor=values["actor"],
        timestamp=values["timestamp"],
        instant=instant,
        delta=delta,
    )


def _read_log(logs_dir: Path, item_id: str, *, required: bool) -> tuple[EngineEvent, ...] | None:
    path = logs_dir / f"{item_id}.jsonl"
    if not os.path.lexists(path):
        if required:
            raise EventLogError(f"event log not found: {path}")
        return None
    if _is_link(path):
        raise EventLogError(f"event log is a symlink or reparse point: {path}")
    try:
        size = path.stat().st_size
        if size > MAX_LOG_BYTES:
            raise EventLogError(f"event log exceeds {MAX_LOG_BYTES} bytes: {path}")
        text = path.read_bytes().decode("utf-8")
    except OSError as exc:
        raise EventLogError(f"event log unreadable: {path} ({exc.__class__.__name__})") from exc
    except UnicodeDecodeError as exc:
        raise EventLogError(f"event log is not UTF-8: {path}") from exc
    events = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            events.append(_parse_event(line, where=f"{path.name}:{number}", expected_item_id=item_id))
    return tuple(events)


def _replay_scope(shipment_events: tuple[EngineEvent, ...]) -> tuple[str, ...]:
    """Replay the shipment's manifest events in timestamp order (created, added, removed, corrected)."""

    scope: dict[str, None] = {}
    for event in sorted(shipment_events, key=lambda e: e.instant):
        delta = event.delta
        if event.event_type == "shipment_created":
            items = delta.get("items")
            if type(items) is not list or not all(type(i) is str for i in items):
                raise EventLogError("shipment_created carries no string item list")
            scope.update(dict.fromkeys(items))
        elif event.event_type == "shipment_item_added":
            item = delta.get("item_id")
            if type(item) is not str:
                raise EventLogError("shipment_item_added carries no item_id")
            scope[item] = None
        elif event.event_type == "shipment_item_removed":
            item = delta.get("removed_item")
            if type(item) is not str:
                raise EventLogError("shipment_item_removed carries no removed_item")
            scope.pop(item, None)
        elif event.event_type == "shipment_manifest_corrected":
            removed = delta.get("removed_items", [])
            if type(removed) is not list or not all(type(i) is str for i in removed):
                raise EventLogError("shipment_manifest_corrected carries a malformed removed_items")
            for item in removed:
                scope.pop(item, None)
    return tuple(scope)


def read_cascade_events(backlog_dir: Path | str, shipment_id: str, since: datetime.datetime) -> CascadeEvents:
    """Read the shipment's and its items' event logs; events before ``since`` are excluded.

    ``since`` must be timezone-aware (normally ``invocation.started_at``). The
    shipment log is required; an item log that does not exist is listed in
    ``missing_item_logs`` rather than treated as empty-and-fine.
    """

    if since.tzinfo is None:
        raise EventLogError("since must be a timezone-aware instant")
    logs_dir = Path(backlog_dir) / EVENT_LOG_DIR_NAME
    if _is_link(logs_dir) or not logs_dir.is_dir():
        raise EventLogError(f"event log directory is missing or untrusted: {logs_dir}")
    shipment_events = _read_log(logs_dir, shipment_id, required=True)
    assert shipment_events is not None
    scope = _replay_scope(shipment_events)
    all_events = list(shipment_events)
    missing = []
    for item_id in scope:
        item_events = _read_log(logs_dir, item_id, required=False)
        if item_events is None:
            missing.append(item_id)
        else:
            all_events.extend(item_events)
    cutoff = since.astimezone(datetime.timezone.utc)
    windowed = [e for e in all_events if e.instant >= cutoff]
    tracked = {shipment_id, *scope}
    shipped = tuple(
        e
        for e in windowed
        if e.item_id == shipment_id
        and e.event_type == "shipment_status_changed"
        and e.delta.get("status") == "shipped"
        and e.operation == shipment_id
    )
    released = tuple(
        e
        for e in windowed
        if e.event_type == "status_changed" and e.operation == shipment_id and e.item_id in tracked
    )
    archived = tuple(e for e in windowed if e.event_type == "archived" and e.item_id in tracked)
    foreign = tuple(e for e in windowed if e.actor != ENGINE_ACTOR and e.item_id in tracked)
    return CascadeEvents(
        shipment_id=shipment_id,
        since=cutoff,
        scope_item_ids=scope,
        shipped_events=shipped,
        released_events=released,
        archived_events=archived,
        foreign_events=foreign,
        missing_item_logs=tuple(missing),
    )


def attribute_archived_footprint(
    events: CascadeEvents,
    required_ids: Collection[str],
    *,
    window_end: datetime.datetime | None = None,
) -> ArchiveAttribution:
    """Decide whether every required archived id is tied to this cascade by engine provenance.

    Attribution needs, for every required id, an engine-authored ``archived``
    event inside ``[since, window_end]`` that itself names this cascade's
    operation, and no foreign-actor event on a required id in the window. The
    event log does not currently supply the operation on ``archived`` events, so
    real logs yield ``attributed=False`` (reason: no correlation).
    """

    required = tuple(dict.fromkeys(required_ids))
    end = window_end.astimezone(datetime.timezone.utc) if window_end is not None else None

    def in_window(event: EngineEvent) -> bool:
        return event.instant >= events.since and (end is None or event.instant <= end)

    archived: dict[str, list[EngineEvent]] = {}
    for event in events.archived_events:
        if event.actor == ENGINE_ACTOR and in_window(event):
            archived.setdefault(event.item_id, []).append(event)
    missing = tuple(i for i in required if i not in archived)
    foreign = tuple(
        dict.fromkeys(e.item_id for e in events.foreign_events if e.item_id in required and in_window(e))
    )
    uncorrelated = tuple(
        i for i in required if i in archived and not all(e.operation == events.shipment_id for e in archived[i])
    )
    if missing:
        return ArchiveAttribution(False, REASON_MISSING_ARCHIVE, missing, uncorrelated, foreign)
    if foreign:
        return ArchiveAttribution(False, REASON_FOREIGN_ACTOR, missing, uncorrelated, foreign)
    if uncorrelated:
        return ArchiveAttribution(False, REASON_NO_CORRELATION, missing, uncorrelated, foreign)
    return ArchiveAttribution(True, "every required archived id carries this cascade's operation", (), (), ())
