"""Tests for the SQLite epoch sink (U3, task 051.003)."""

from __future__ import annotations

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
)
from autoharness.telemetry.sqlite_sink import ensure_schema, write_epoch


def _epoch(task_id: str = "051.003-T") -> ExecutionEpoch:
    return ExecutionEpoch(
        task_id=task_id,
        route=RouteConfiguration(models=("claude-opus-4.6",)),
        economics=EconomicPayload(input_tokens=100, output_tokens=50, cogs_usd=0.01, duration_seconds=12.0),
        operations=OperationalReality(cli_tools=("git",)),
        outcome=AbsoluteOutcome(gate_exit_codes=(0,)),
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


if __name__ == "__main__":
    unittest.main()
