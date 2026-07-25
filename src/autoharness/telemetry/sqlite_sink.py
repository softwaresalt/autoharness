"""SQLite epoch sink — repo-local aggregator (Phase 2, U3, task 051.003).

Writes one row per :class:`~autoharness.telemetry.epoch.ExecutionEpoch` to a
repo-local SQLite database (default ``.autoharness/metrics/execution_epochs.db``)
whose columns support quantitative metric queries. Uses stdlib ``sqlite3`` only,
WAL journaling, and short-lived per-write connections so concurrent emissions do
not contend on a long-held handle. Parent directories are auto-created.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autoharness.telemetry.epoch import ExecutionEpoch

_BUSY_TIMEOUT_SECONDS = 5.0
_BUSY_TIMEOUT_MS = 5000
_MAX_WRITE_RETRIES = 5


class TelemetryConflictError(RuntimeError):
    """Raised when an epoch_id already has different immutable payload content."""


@dataclass(frozen=True)
class SinkWriteResult:
    status: str
    payload_digest: str

_SCHEMA = """
CREATE TABLE IF NOT EXISTS execution_epochs (
    epoch_id          TEXT PRIMARY KEY,
    schema_version    TEXT NOT NULL,
    task_id           TEXT NOT NULL,
    backlog_item_id   TEXT,
    timestamp         TEXT NOT NULL,
    workspace_id      TEXT,
    session_id        TEXT,
    agent_role        TEXT,
    phase             TEXT,
    feature_id        TEXT,
    shipment_id       TEXT,
    branch            TEXT,
    commit_sha        TEXT,
    primary_model     TEXT,
    primary_route_kind TEXT,
    models            TEXT NOT NULL,
    route_kinds       TEXT,
    input_tokens      INTEGER NOT NULL,
    output_tokens     INTEGER NOT NULL,
    total_tokens      INTEGER NOT NULL,
    cached_input_tokens INTEGER,
    cumulative_input_tokens INTEGER,
    cumulative_output_tokens INTEGER,
    context_tokens_before INTEGER,
    context_tokens_after INTEGER,
    context_area_tokens INTEGER,
    avoided_read_estimated_tokens INTEGER,
    tool_output_estimated_tokens INTEGER,
    cogs_usd          REAL NOT NULL,
    duration_seconds  REAL NOT NULL,
    economics_metric_sources TEXT,
    economics_metric_quality TEXT,
    cli_tools         TEXT NOT NULL,
    tool_surfaces     TEXT,
    retrieval_packs   TEXT,
    route_kind_counts TEXT,
    routed_lookup_count INTEGER,
    raw_file_read_count INTEGER,
    raw_search_count INTEGER,
    avoided_file_read_count INTEGER,
    tool_output_bytes INTEGER,
    expected_tool_count INTEGER,
    observed_expected_tool_count INTEGER,
    missing_expected_tool_count INTEGER,
    expected_tool_counts TEXT,
    observed_tool_counts TEXT,
    missing_expected_tool_counts TEXT,
    degraded_tool_count INTEGER,
    stale_or_unavailable_index_count INTEGER,
    operations_metric_sources TEXT,
    operations_metric_quality TEXT,
    gate_exit_codes   TEXT NOT NULL,
    tool_failure_count INTEGER,
    tool_degraded_count INTEGER,
    tool_gap_count INTEGER,
    outcome_metric_sources TEXT,
    outcome_metric_quality TEXT,
    blocked           INTEGER NOT NULL,
    sizing_json       TEXT,
    payload_json      TEXT,
    payload_digest    TEXT
);
"""

_MIGRATION_COLUMNS: dict[str, str] = {
    "backlog_item_id": "TEXT",
    "workspace_id": "TEXT",
    "session_id": "TEXT",
    "agent_role": "TEXT",
    "phase": "TEXT",
    "feature_id": "TEXT",
    "shipment_id": "TEXT",
    "branch": "TEXT",
    "commit_sha": "TEXT",
    "primary_route_kind": "TEXT",
    "route_kinds": "TEXT",
    "cached_input_tokens": "INTEGER",
    "cumulative_input_tokens": "INTEGER",
    "cumulative_output_tokens": "INTEGER",
    "context_tokens_before": "INTEGER",
    "context_tokens_after": "INTEGER",
    "context_area_tokens": "INTEGER",
    "avoided_read_estimated_tokens": "INTEGER",
    "tool_output_estimated_tokens": "INTEGER",
    "economics_metric_sources": "TEXT",
    "economics_metric_quality": "TEXT",
    "tool_surfaces": "TEXT",
    "retrieval_packs": "TEXT",
    "route_kind_counts": "TEXT",
    "routed_lookup_count": "INTEGER",
    "raw_file_read_count": "INTEGER",
    "raw_search_count": "INTEGER",
    "avoided_file_read_count": "INTEGER",
    "tool_output_bytes": "INTEGER",
    "expected_tool_count": "INTEGER",
    "observed_expected_tool_count": "INTEGER",
    "missing_expected_tool_count": "INTEGER",
    "expected_tool_counts": "TEXT",
    "observed_tool_counts": "TEXT",
    "missing_expected_tool_counts": "TEXT",
    "degraded_tool_count": "INTEGER",
    "stale_or_unavailable_index_count": "INTEGER",
    "operations_metric_sources": "TEXT",
    "operations_metric_quality": "TEXT",
    "tool_failure_count": "INTEGER",
    "tool_degraded_count": "INTEGER",
    "tool_gap_count": "INTEGER",
    "outcome_metric_sources": "TEXT",
    "outcome_metric_quality": "TEXT",
    "sizing_json": "TEXT",
    "payload_json": "TEXT",
    "payload_digest": "TEXT",
}

_INSERT_COLUMNS = (
    "epoch_id",
    "schema_version",
    "task_id",
    "backlog_item_id",
    "timestamp",
    "workspace_id",
    "session_id",
    "agent_role",
    "phase",
    "feature_id",
    "shipment_id",
    "branch",
    "commit_sha",
    "primary_model",
    "primary_route_kind",
    "models",
    "route_kinds",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "cached_input_tokens",
    "cumulative_input_tokens",
    "cumulative_output_tokens",
    "context_tokens_before",
    "context_tokens_after",
    "context_area_tokens",
    "avoided_read_estimated_tokens",
    "tool_output_estimated_tokens",
    "cogs_usd",
    "duration_seconds",
    "economics_metric_sources",
    "economics_metric_quality",
    "cli_tools",
    "tool_surfaces",
    "retrieval_packs",
    "route_kind_counts",
    "routed_lookup_count",
    "raw_file_read_count",
    "raw_search_count",
    "avoided_file_read_count",
    "tool_output_bytes",
    "expected_tool_count",
    "observed_expected_tool_count",
    "missing_expected_tool_count",
    "expected_tool_counts",
    "observed_tool_counts",
    "missing_expected_tool_counts",
    "degraded_tool_count",
    "stale_or_unavailable_index_count",
    "operations_metric_sources",
    "operations_metric_quality",
    "gate_exit_codes",
    "tool_failure_count",
    "tool_degraded_count",
    "tool_gap_count",
    "outcome_metric_sources",
    "outcome_metric_quality",
    "blocked",
    "sizing_json",
    "payload_json",
    "payload_digest",
)


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def canonical_payload_json(epoch: ExecutionEpoch) -> str:
    return _json(epoch.to_record())


def payload_digest(epoch: ExecutionEpoch) -> str:
    import hashlib

    return hashlib.sha256(canonical_payload_json(epoch).encode("utf-8")).hexdigest()


def _column_names(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(execution_epochs)")}


def _migrate_schema(conn: sqlite3.Connection) -> None:
    existing = _column_names(conn)
    for column, definition in _MIGRATION_COLUMNS.items():
        if column not in existing:
            try:
                conn.execute(f"ALTER TABLE execution_epochs ADD COLUMN {column} {definition}")
            except sqlite3.OperationalError as exc:
                # Copilot review t6: a concurrent initializer can add the same
                # column between our snapshot and this ALTER, yielding a
                # "duplicate column name" error. Treat that as already-migrated
                # (idempotent) rather than dropping telemetry; re-raise anything
                # else.
                if "duplicate column name" not in str(exc).lower():
                    raise


def _connect(database_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(database_path), timeout=_BUSY_TIMEOUT_SECONDS)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS};")
    return conn


def ensure_schema(database_path: Path) -> None:
    """Create the parent directory and (idempotently) the epoch table."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = _connect(database_path)
    try:
        conn.executescript(_SCHEMA)
        _migrate_schema(conn)
        conn.commit()
    finally:
        conn.close()


def find_epoch_digest(database_path: Path, epoch_id: str) -> str | None:
    """Return the stored digest for ``epoch_id`` without creating a missing DB."""
    if not database_path.exists():
        return None
    conn = _connect(database_path)
    try:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='execution_epochs'"
        ).fetchone()
        if table is None or "payload_digest" not in _column_names(conn):
            return None
        row = conn.execute(
            "SELECT payload_digest FROM execution_epochs WHERE epoch_id = ?",
            (epoch_id,),
        ).fetchone()
        return None if row is None else row[0]
    finally:
        conn.close()


def _insert_values(epoch: ExecutionEpoch, digest: str, payload_json: str) -> tuple[Any, ...]:
    route = epoch.route
    economics = epoch.economics
    operations = epoch.operations
    outcome = epoch.outcome
    sizing = epoch.sizing.to_dict() if epoch.sizing is not None else None
    return (
        epoch.epoch_id,
        epoch.schema_version,
        epoch.task_id,
        epoch.backlog_item_id,
        epoch.timestamp,
        epoch.workspace_id,
        epoch.session_id,
        epoch.agent_role,
        epoch.phase,
        epoch.feature_id,
        epoch.shipment_id,
        epoch.branch,
        epoch.commit_sha,
        route.primary_model,
        route.primary_route_kind,
        _json(list(route.models)),
        _json(list(route.route_kinds)),
        economics.input_tokens,
        economics.output_tokens,
        economics.total_tokens,
        economics.cached_input_tokens,
        economics.cumulative_input_tokens,
        economics.cumulative_output_tokens,
        economics.context_tokens_before,
        economics.context_tokens_after,
        economics.context_area_tokens,
        economics.avoided_read_estimated_tokens,
        economics.tool_output_estimated_tokens,
        economics.cogs_usd,
        economics.duration_seconds,
        _json(dict(economics.metric_sources)),
        _json(dict(economics.metric_quality)),
        _json(list(operations.cli_tools)),
        _json(list(operations.tool_surfaces)),
        _json(list(operations.retrieval_packs)),
        _json(dict(operations.route_kind_counts)),
        operations.routed_lookup_count,
        operations.raw_file_read_count,
        operations.raw_search_count,
        operations.avoided_file_read_count,
        operations.tool_output_bytes,
        operations.expected_tool_count,
        operations.observed_expected_tool_count,
        operations.missing_expected_tool_count,
        _json(dict(operations.expected_tool_counts)),
        _json(dict(operations.observed_tool_counts)),
        _json(dict(operations.missing_expected_tool_counts)),
        operations.degraded_tool_count,
        operations.stale_or_unavailable_index_count,
        _json(dict(operations.metric_sources)),
        _json(dict(operations.metric_quality)),
        _json(list(outcome.gate_exit_codes)),
        outcome.tool_failure_count,
        outcome.tool_degraded_count,
        outcome.tool_gap_count,
        _json(dict(outcome.metric_sources)),
        _json(dict(outcome.metric_quality)),
        int(outcome.blocked),
        _json(sizing) if sizing is not None else None,
        payload_json,
        digest,
    )


def _check_existing_digest(
    conn: sqlite3.Connection,
    epoch_id: str,
    digest: str,
) -> SinkWriteResult | None:
    row = conn.execute(
        "SELECT payload_digest FROM execution_epochs WHERE epoch_id = ?",
        (epoch_id,),
    ).fetchone()
    if row is None:
        return None
    existing_digest = row[0]
    if existing_digest == digest:
        return SinkWriteResult(status="idempotent_replay", payload_digest=digest)
    raise TelemetryConflictError(
        f"conflicting immutable replay for epoch_id {epoch_id}: "
        f"existing digest {existing_digest or '<missing>'} != {digest}"
    )


def write_epoch(epoch: ExecutionEpoch, database_path: Path) -> SinkWriteResult:
    """Persist a single epoch. Opens and closes a short-lived connection.

    Uses a busy timeout plus a small bounded retry on ``database is locked`` so
    parallel emitters do not drop rows under contention.
    """
    ensure_schema(database_path)
    digest = payload_digest(epoch)
    payload_json = canonical_payload_json(epoch)
    insert_sql = (
        f"INSERT INTO execution_epochs ({', '.join(_INSERT_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in _INSERT_COLUMNS)})"
    )
    values = _insert_values(epoch, digest, payload_json)
    last_exc: sqlite3.OperationalError | None = None
    for attempt in range(_MAX_WRITE_RETRIES):
        conn = _connect(database_path)
        try:
            existing = _check_existing_digest(conn, epoch.epoch_id, digest)
            if existing is not None:
                return existing
            conn.execute(insert_sql, values)
            conn.commit()
            return SinkWriteResult(status="created", payload_digest=digest)
        except sqlite3.IntegrityError:
            conn.rollback()
            existing = _check_existing_digest(conn, epoch.epoch_id, digest)
            if existing is not None:
                return existing
            raise
        except sqlite3.OperationalError as exc:
            if "database is locked" not in str(exc).lower():
                raise
            last_exc = exc
            time.sleep(0.05 * (attempt + 1))
        finally:
            conn.close()
    if last_exc is not None:
        raise last_exc
