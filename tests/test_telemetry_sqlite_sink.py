"""Tests for the SQLite epoch sink (U3, task 051.003)."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
    WorkSizingSnapshot,
)
from autoharness.telemetry.sqlite_sink import (
    TelemetryConflictError,
    ensure_schema,
    write_epoch,
)


def _epoch(task_id: str = "051.003-T") -> ExecutionEpoch:
    return ExecutionEpoch(
        task_id=task_id,
        route=RouteConfiguration(models=("claude-opus-4.6",)),
        economics=EconomicPayload(input_tokens=100, output_tokens=50, cogs_usd=0.01, duration_seconds=12.0),
        operations=OperationalReality(cli_tools=("git",)),
        outcome=AbsoluteOutcome(gate_exit_codes=(0,)),
    )


def _v11_epoch(epoch_id: str = "0123456789abcdef0123456789abcdef") -> ExecutionEpoch:
    return ExecutionEpoch(
        epoch_id=epoch_id,
        task_id="079.003-T",
        backlog_item_id="079.003-T",
        workspace_id="ws1",
        session_id="s1",
        agent_role="ship",
        phase="build",
        feature_id="079-F",
        shipment_id="092-S",
        branch="feat/079-telemetry-metrics-core",
        commit_sha="abc123",
        route=RouteConfiguration(
            models=("gpt-5.4-mini",),
            route_kinds=("structural_graph",),
        ),
        economics=EconomicPayload(
            input_tokens=100,
            output_tokens=50,
            cached_input_tokens=10,
            cumulative_input_tokens=1000,
            cumulative_output_tokens=500,
            context_tokens_before=900,
            context_tokens_after=950,
            context_area_tokens=1850,
            avoided_read_estimated_tokens=250,
            tool_output_estimated_tokens=40,
            cogs_usd=0.02,
            duration_seconds=12.5,
            metric_sources={
                "input_tokens": "host",
                "output_tokens": "host",
                "cached_input_tokens": "host",
                "cumulative_input_tokens": "host",
                "cumulative_output_tokens": "host",
                "context_tokens_before": "host",
                "context_tokens_after": "host",
                "context_area_tokens": "estimated",
                "avoided_read_estimated_tokens": "estimated",
                "tool_output_estimated_tokens": "estimated",
                "cogs_usd": "host",
                "duration_seconds": "host",
            },
            metric_quality={
                "input_tokens": "observed",
                "output_tokens": "observed",
                "cached_input_tokens": "observed",
                "cumulative_input_tokens": "observed",
                "cumulative_output_tokens": "observed",
                "context_tokens_before": "observed",
                "context_tokens_after": "observed",
                "context_area_tokens": "estimated",
                "avoided_read_estimated_tokens": "estimated",
                "tool_output_estimated_tokens": "estimated",
                "cogs_usd": "observed",
                "duration_seconds": "observed",
            },
        ),
        operations=OperationalReality(
            cli_tools=("git",),
            tool_surfaces=("mcp", "cli"),
            retrieval_packs=("agent-engram",),
            route_kind_counts={"structural_graph": 1},
            routed_lookup_count=1,
            raw_file_read_count=0,
            raw_search_count=0,
            avoided_file_read_count=2,
            tool_output_bytes=512,
            expected_tool_count=1,
            observed_expected_tool_count=0,
            missing_expected_tool_count=1,
            expected_tool_counts={"engram.map_code": 1},
            observed_tool_counts={"engram.map_code": 0},
            missing_expected_tool_counts={"engram.map_code": 1},
            degraded_tool_count=1,
            stale_or_unavailable_index_count=1,
            metric_sources={
                "route_kind_counts": "host",
                "routed_lookup_count": "host",
                "avoided_file_read_count": "estimated",
                "tool_output_bytes": "host",
                "expected_tool_count": "host",
                "missing_expected_tool_count": "derived",
                "expected_tool_counts": "host",
                "observed_tool_counts": "host",
                "missing_expected_tool_counts": "derived",
                "degraded_tool_count": "host",
                "stale_or_unavailable_index_count": "host",
            },
            metric_quality={
                "route_kind_counts": "observed",
                "routed_lookup_count": "observed",
                "avoided_file_read_count": "estimated",
                "tool_output_bytes": "observed",
                "expected_tool_count": "observed",
                "missing_expected_tool_count": "derived",
                "expected_tool_counts": "observed",
                "observed_tool_counts": "observed",
                "missing_expected_tool_counts": "derived",
                "degraded_tool_count": "observed",
                "stale_or_unavailable_index_count": "observed",
            },
        ),
        outcome=AbsoluteOutcome(
            gate_exit_codes=(0,),
            tool_failure_count=0,
            tool_degraded_count=1,
            tool_gap_count=1,
            metric_sources={"tool_degraded_count": "host", "tool_gap_count": "derived"},
            metric_quality={"tool_degraded_count": "observed", "tool_gap_count": "derived"},
        ),
        sizing=WorkSizingSnapshot(
            snapshot_at="2026-07-24T03:07:22Z",
            task_size_label="M",
            feature_planned_child_task_count=2,
            feature_planned_child_size_histogram={"M": 1, "unsized": 1},
            feature_child_membership_hash=WorkSizingSnapshot.membership_hash(["a", "b"]),
        ),
    )


class SqliteSinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        self.db_path = self.workspace / ".autoharness" / "metrics" / "execution_epochs.db"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_schema_created_at_repo_relative_path_with_parents(self) -> None:
        self.assertFalse(self.db_path.exists())
        ensure_schema(self.db_path)
        self.assertTrue(self.db_path.exists())
        # Path is repo-relative under the workspace metrics directory.
        self.assertEqual(self.db_path.parent.name, "metrics")

    def test_migration_is_idempotent(self) -> None:
        ensure_schema(self.db_path)
        ensure_schema(self.db_path)  # second call must be a no-op, not raise
        conn = sqlite3.connect(str(self.db_path))
        try:
            names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertIn("execution_epochs", names)

    def test_epoch_persisted_and_queryable(self) -> None:
        epoch = _epoch()
        write_epoch(epoch, self.db_path)

        conn = sqlite3.connect(str(self.db_path))
        try:
            row = conn.execute(
                "SELECT task_id, primary_model, total_tokens, cogs_usd, blocked "
                "FROM execution_epochs WHERE epoch_id = ?",
                (epoch.epoch_id,),
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "051.003-T")
        self.assertEqual(row[1], "claude-opus-4.6")
        self.assertEqual(row[2], 150)
        self.assertAlmostEqual(row[3], 0.01)
        self.assertEqual(row[4], 0)

    def test_multiple_epochs_do_not_collide(self) -> None:
        write_epoch(_epoch("a"), self.db_path)
        write_epoch(_epoch("b"), self.db_path)
        conn = sqlite3.connect(str(self.db_path))
        try:
            count = conn.execute("SELECT COUNT(*) FROM execution_epochs").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 2)

    def test_concurrent_writes_drop_no_rows(self) -> None:
        # Parallel emitters must not lose rows to "database is locked".
        import threading

        ensure_schema(self.db_path)
        n_threads = 10
        m_records = 40

        def worker(tid: int) -> None:
            for i in range(m_records):
                write_epoch(_epoch(f"t{tid}-{i}"), self.db_path)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        conn = sqlite3.connect(str(self.db_path))
        try:
            count = conn.execute("SELECT COUNT(*) FROM execution_epochs").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, n_threads * m_records)

    def test_migration_from_pre_079_schema_keeps_legacy_rows_readable(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.executescript(
                """
                CREATE TABLE execution_epochs (
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
                INSERT INTO execution_epochs (
                    epoch_id, schema_version, task_id, timestamp, primary_model,
                    models, input_tokens, output_tokens, total_tokens, cogs_usd,
                    duration_seconds, cli_tools, gate_exit_codes, blocked
                ) VALUES (
                    'legacy', '1.0.0', '051.003-T', '2026-01-01T00:00:00Z',
                    'gpt-5.4-mini', '["gpt-5.4-mini"]', 1, 2, 3, 0.01,
                    4.0, '["git"]', '[0]', 0
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

        ensure_schema(self.db_path)
        write_epoch(_v11_epoch(), self.db_path)

        conn = sqlite3.connect(str(self.db_path))
        try:
            legacy = conn.execute(
                "SELECT schema_version, task_id, total_tokens FROM execution_epochs WHERE epoch_id='legacy'"
            ).fetchone()
            columns = {row[1] for row in conn.execute("PRAGMA table_info(execution_epochs)")}
            v11 = conn.execute(
                "SELECT feature_id, cached_input_tokens, route_kind_counts, sizing_json, payload_digest "
                "FROM execution_epochs WHERE epoch_id=?",
                ("0123456789abcdef0123456789abcdef",),
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(legacy, ("1.0.0", "051.003-T", 3))
        for column in (
            "backlog_item_id",
            "feature_id",
            "shipment_id",
            "cached_input_tokens",
            "economics_metric_sources",
            "route_kind_counts",
            "expected_tool_counts",
            "tool_degraded_count",
            "sizing_json",
            "payload_json",
            "payload_digest",
        ):
            self.assertIn(column, columns)
        self.assertEqual(v11[0], "079-F")
        self.assertEqual(v11[1], 10)
        self.assertEqual(json.loads(v11[2]), {"structural_graph": 1})
        self.assertEqual(json.loads(v11[3])["task_size_label"], "M")
        self.assertEqual(len(v11[4]), 64)

    def test_legacy_v1_record_normalizes_to_v11_before_persistence(self) -> None:
        legacy = {
            "epoch_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "schema_version": "1.0.0",
            "task_id": "051.003-T",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "route": {"models": ["m"]},
            "economics": {"input_tokens": 100, "output_tokens": 50, "cogs_usd": 0.01, "duration_seconds": 12.0},
            "operations": {"cli_tools": ["git"]},
            "outcome": {"gate_exit_codes": [0]},
        }
        write_epoch(ExecutionEpoch.from_mapping(legacy), self.db_path)

        conn = sqlite3.connect(str(self.db_path))
        try:
            row = conn.execute(
                "SELECT schema_version, economics_metric_sources, payload_json "
                "FROM execution_epochs WHERE epoch_id=?",
                ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",),
            ).fetchone()
        finally:
            conn.close()

        sources = json.loads(row[1])
        payload = json.loads(row[2])
        self.assertEqual(row[0], "1.1.0")
        self.assertEqual(payload["schema_version"], "1.1.0")
        self.assertEqual(sources["input_tokens"], "unavailable")
        self.assertEqual(sources["duration_seconds"], "unavailable")

    def test_first_write_immutable_idempotent_replay_and_conflict(self) -> None:
        first = _v11_epoch("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
        same = first
        conflict = ExecutionEpoch(
            epoch_id=first.epoch_id,
            task_id="079.003-T",
            route=first.route,
            economics=EconomicPayload(input_tokens=999),
            operations=first.operations,
            outcome=first.outcome,
        )

        created = write_epoch(first, self.db_path)
        idempotent = write_epoch(same, self.db_path)
        with self.assertRaises(TelemetryConflictError):
            write_epoch(conflict, self.db_path)

        conn = sqlite3.connect(str(self.db_path))
        try:
            rows = conn.execute(
                "SELECT input_tokens, payload_digest FROM execution_epochs WHERE epoch_id=?",
                (first.epoch_id,),
            ).fetchall()
        finally:
            conn.close()

        self.assertEqual(created.status, "created")
        self.assertEqual(idempotent.status, "idempotent_replay")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], 100)
        self.assertEqual(rows[0][1], created.payload_digest)


class SqliteMigrationRaceTests(unittest.TestCase):
    """Copilot review t6: the check-then-ALTER migration must tolerate a
    concurrent initializer adding the same column between the column snapshot and
    the ALTER (``duplicate column name``) instead of dropping telemetry."""

    def test_migrate_schema_tolerates_duplicate_column_race(self) -> None:
        from unittest import mock

        from autoharness.telemetry import sqlite_sink

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "execution_epochs.db"
            ensure_schema(db_path)  # all migration columns now present
            conn = sqlite_sink._connect(db_path)
            try:
                # Simulate a stale pre-migration snapshot: every migration column
                # appears missing, so _migrate_schema will re-attempt each ALTER on
                # a column that already exists (the concurrent-writer race).
                with mock.patch.object(sqlite_sink, "_column_names", return_value=set()):
                    sqlite_sink._migrate_schema(conn)  # must not raise
                columns = {row[1] for row in conn.execute("PRAGMA table_info(execution_epochs)")}
            finally:
                conn.close()

            for column in sqlite_sink._MIGRATION_COLUMNS:
                self.assertIn(column, columns)


if __name__ == "__main__":
    unittest.main()
