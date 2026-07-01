"""Tests for the JSONL epoch sink — emit-only (U4, task 051.006)."""

from __future__ import annotations

import json
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
from autoharness.telemetry.jsonl_sink import append_epoch


def _epoch(task_id: str) -> ExecutionEpoch:
    return ExecutionEpoch(
        task_id=task_id,
        route=RouteConfiguration(models=("gpt-5.4",)),
        economics=EconomicPayload(input_tokens=10, output_tokens=5),
        operations=OperationalReality(cli_tools=("git",)),
        outcome=AbsoluteOutcome(gate_exit_codes=(0,)),
    )


class JsonlSinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.jsonl_path = Path(self._tmp.name) / ".autoharness" / "metrics" / "execution_epochs.jsonl"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_each_line_is_well_formed_json_with_contract_fields(self) -> None:
        epoch = _epoch("051.006-T")
        append_epoch(epoch, self.jsonl_path)

        lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        parsed = json.loads(lines[0])
        for key in ("epoch_id", "schema_version", "task_id", "timestamp", "route", "economics", "operations", "outcome"):
            self.assertIn(key, parsed)
        self.assertEqual(parsed["task_id"], "051.006-T")

    def test_append_semantics_preserve_existing_lines(self) -> None:
        append_epoch(_epoch("a"), self.jsonl_path)
        append_epoch(_epoch("b"), self.jsonl_path)

        lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["task_id"], "a")
        self.assertEqual(json.loads(lines[1])["task_id"], "b")

    def test_parent_directory_is_created(self) -> None:
        self.assertFalse(self.jsonl_path.parent.exists())
        append_epoch(_epoch("x"), self.jsonl_path)
        self.assertTrue(self.jsonl_path.exists())

    def test_concurrent_appends_produce_intact_lines(self) -> None:
        # Each append must land as exactly one atomic, complete line even under
        # many concurrent writers — no interleaving or split lines.
        import threading

        n_threads = 12
        m_records = 120

        def worker(tid: int) -> None:
            for i in range(m_records):
                append_epoch(_epoch(f"t{tid}-{i}"), self.jsonl_path)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), n_threads * m_records)
        for line in lines:
            json.loads(line)  # every line must be valid, complete JSON


if __name__ == "__main__":
    unittest.main()
