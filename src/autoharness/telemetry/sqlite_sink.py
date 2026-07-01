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
from pathlib import Path

from autoharness.telemetry.epoch import ExecutionEpoch

_BUSY_TIMEOUT_SECONDS = 5.0
_BUSY_TIMEOUT_MS = 5000
_MAX_WRITE_RETRIES = 5

_SCHEMA = """
CREATE TABLE IF NOT EXISTS execution_epochs (
    epoch_id          TEXT PRIMARY KEY,
    schema_version    TEXT NOT NULL,
    task_id           TEXT NOT NULL,
    timestamp         TEXT NOT NULL,
    primary_model     TEXT,
    models            TEXT NOT NULL,
    input_tokens      INTEGER NOT NULL,
    output_tokens     INTEGER NOT NULL,
    total_tokens      INTEGER NOT NULL,
    cogs_usd          REAL NOT NULL,
    duration_seconds  REAL NOT NULL,
    cli_tools         TEXT NOT NULL,
    gate_exit_codes   TEXT NOT NULL,
    blocked           INTEGER NOT NULL
);
"""


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
        conn.commit()
    finally:
        conn.close()


def write_epoch(epoch: ExecutionEpoch, database_path: Path) -> None:
    """Persist a single epoch. Opens and closes a short-lived connection.

    Uses a busy timeout plus a small bounded retry on ``database is locked`` so
    parallel emitters do not drop rows under contention.
    """
    ensure_schema(database_path)
    last_exc: sqlite3.OperationalError | None = None
    for attempt in range(_MAX_WRITE_RETRIES):
        conn = _connect(database_path)
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO execution_epochs (
                    epoch_id, schema_version, task_id, timestamp,
                    primary_model, models,
                    input_tokens, output_tokens, total_tokens,
                    cogs_usd, duration_seconds,
                    cli_tools, gate_exit_codes, blocked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    epoch.epoch_id,
                    epoch.schema_version,
                    epoch.task_id,
                    epoch.timestamp,
                    epoch.route.primary_model,
                    json.dumps(list(epoch.route.models)),
                    epoch.economics.input_tokens,
                    epoch.economics.output_tokens,
                    epoch.economics.total_tokens,
                    epoch.economics.cogs_usd,
                    epoch.economics.duration_seconds,
                    json.dumps(list(epoch.operations.cli_tools)),
                    json.dumps(list(epoch.outcome.gate_exit_codes)),
                    int(epoch.outcome.blocked),
                ),
            )
            conn.commit()
            return
        except sqlite3.OperationalError as exc:
            if "database is locked" not in str(exc).lower():
                raise
            last_exc = exc
            time.sleep(0.05 * (attempt + 1))
        finally:
            conn.close()
    if last_exc is not None:
        raise last_exc
