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
    WorkSizingSnapshot,
)
from autoharness.telemetry.jsonl_sink import TelemetryConflictError, append_epoch


def _epoch(task_id: str) -> ExecutionEpoch:
    return ExecutionEpoch(
        task_id=task_id,
        route=RouteConfiguration(models=("gpt-5.4",)),
        economics=EconomicPayload(input_tokens=10, output_tokens=5),
        operations=OperationalReality(cli_tools=("git",)),
        outcome=AbsoluteOutcome(gate_exit_codes=(0,)),
    )


def _sized_epoch(epoch_id: str = "cccccccccccccccccccccccccccccccc") -> ExecutionEpoch:
    return ExecutionEpoch(
        epoch_id=epoch_id,
        task_id="079.003-T",
        route=RouteConfiguration(models=("gpt-5.4",), route_kinds=("structural_graph",)),
        economics=EconomicPayload(
            input_tokens=10,
            output_tokens=5,
            cached_input_tokens=2,
            cumulative_input_tokens=100,
            cumulative_output_tokens=50,
            context_area_tokens=200,
            avoided_read_estimated_tokens=80,
            tool_output_estimated_tokens=12,
        ),
        operations=OperationalReality(
            cli_tools=("git",),
            tool_surfaces=("mcp",),
            retrieval_packs=("agent-engram",),
            route_kind_counts={"structural_graph": 1},
            routed_lookup_count=1,
            expected_tool_count=1,
            observed_expected_tool_count=0,
            missing_expected_tool_count=1,
            expected_tool_counts={"engram.map_code": 1},
            observed_tool_counts={"engram.map_code": 0},
            missing_expected_tool_counts={"engram.map_code": 1},
        ),
        outcome=AbsoluteOutcome(gate_exit_codes=(0,), tool_gap_count=1),
        sizing=WorkSizingSnapshot(
            snapshot_at="2026-07-24T03:07:22Z",
            task_size_label="M",
            feature_planned_child_task_count=1,
            feature_planned_child_size_histogram={"M": 1},
            feature_child_membership_hash=WorkSizingSnapshot.membership_hash(["079.003-T"]),
        ),
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

    def test_v11_record_is_written_exactly_with_sizing_and_no_event_body(self) -> None:
        epoch = _sized_epoch()
        append_epoch(epoch, self.jsonl_path)

        payload = json.loads(self.jsonl_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(payload, epoch.to_record())
        self.assertEqual(payload["sizing"]["task_size_label"], "M")
        self.assertEqual(payload["operations"]["expected_tool_counts"], {"engram.map_code": 1})
        self.assertNotIn("raw_tool_output", payload)
        self.assertNotIn("tool_events", payload)

    def test_identical_replay_is_not_appended_and_conflict_is_diagnosed(self) -> None:
        first = _sized_epoch("dddddddddddddddddddddddddddddddd")
        append_epoch(first, self.jsonl_path)
        idempotent = append_epoch(first, self.jsonl_path)
        conflict = ExecutionEpoch(
            epoch_id=first.epoch_id,
            task_id="079.003-T",
            route=first.route,
            economics=EconomicPayload(input_tokens=999),
            operations=first.operations,
            outcome=first.outcome,
        )

        with self.assertRaises(TelemetryConflictError):
            append_epoch(conflict, self.jsonl_path)

        lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(idempotent.status, "idempotent_replay")
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["economics"]["input_tokens"], 10)


if __name__ == "__main__":
    unittest.main()
