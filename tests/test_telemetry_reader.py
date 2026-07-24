"""Tests for local telemetry sink readers and v1.0 -> v1.1 normalization."""

from __future__ import annotations

import json
import shutil
import sqlite3
import unittest
from pathlib import Path

from autoharness.telemetry.config import load_telemetry_config
from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
    WorkSizingSnapshot,
)
from autoharness.telemetry.jsonl_sink import append_epoch
from autoharness.telemetry.reader import read_epoch_records
from autoharness.telemetry.sqlite_sink import ensure_schema, write_epoch

_ROOT = Path(__file__).resolve().parents[1]
_TEST_OUTPUT = _ROOT / ".test-output" / "telemetry-reader"


def _config(workspace: Path, database_path: str = ".autoharness/metrics/execution_epochs.db"):
    return load_telemetry_config(
        {"mode": "sqlite", "database_path": database_path, "emit_jsonl": True},
        workspace_root=workspace,
    )


def _epoch(epoch_id: str, task_id: str = "079.005-T") -> ExecutionEpoch:
    return ExecutionEpoch(
        epoch_id=epoch_id,
        task_id=task_id,
        backlog_item_id=task_id,
        feature_id="079-F",
        shipment_id="092-S",
        route=RouteConfiguration(models=("gpt-5.4-mini",), route_kinds=("structural_graph",)),
        economics=EconomicPayload(
            input_tokens=10,
            output_tokens=5,
            cached_input_tokens=1,
            cumulative_input_tokens=100,
            cumulative_output_tokens=50,
            metric_sources={"input_tokens": "host", "output_tokens": "host"},
            metric_quality={"input_tokens": "observed", "output_tokens": "observed"},
        ),
        operations=OperationalReality(
            cli_tools=("git",),
            expected_tool_count=1,
            observed_expected_tool_count=1,
            expected_tool_counts={"engram.map_code": 1},
            observed_tool_counts={"engram.map_code": 1},
        ),
        outcome=AbsoluteOutcome(gate_exit_codes=(0,)),
        sizing=WorkSizingSnapshot(
            snapshot_at="2026-07-24T03:37:49Z",
            task_size_label="M",
            feature_planned_child_task_count=1,
            feature_planned_child_size_histogram={"M": 1},
            feature_child_membership_hash=WorkSizingSnapshot.membership_hash([task_id]),
        ),
    )


class TelemetryReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = _TEST_OUTPUT / self._testMethodName / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(_TEST_OUTPUT / self._testMethodName, ignore_errors=True)

    def test_reads_default_sqlite_and_jsonl_sinks_through_config(self) -> None:
        config = _config(self.workspace)
        sqlite_epoch = _epoch("11111111111141118111111111111111", "sqlite-task")
        jsonl_epoch = _epoch("22222222222242228222222222222222", "jsonl-task")
        write_epoch(sqlite_epoch, config.database_path)
        append_epoch(jsonl_epoch, config.jsonl_path)

        result = read_epoch_records(config, source="combined")
        by_id = {record["epoch_id"]: record for record in result.records}

        self.assertEqual(result.status, "ok")
        self.assertEqual(by_id[sqlite_epoch.epoch_id]["task_id"], "sqlite-task")
        self.assertEqual(by_id[jsonl_epoch.epoch_id]["task_id"], "jsonl-task")
        self.assertEqual(by_id[sqlite_epoch.epoch_id]["schema_version"], "1.1.0")
        self.assertEqual(by_id[sqlite_epoch.epoch_id]["sizing"]["task_size_label"], "M")

    def test_reads_custom_database_path_with_colocated_jsonl(self) -> None:
        config = _config(self.workspace, "custom-metrics/epochs.db")
        write_epoch(_epoch("33333333333343338333333333333333", "custom-sqlite"), config.database_path)
        append_epoch(_epoch("44444444444444448444444444444444", "custom-jsonl"), config.jsonl_path)

        result = read_epoch_records(config, source="combined")

        self.assertEqual(config.jsonl_path.parent, config.database_path.parent)
        self.assertEqual({record["task_id"] for record in result.records}, {"custom-sqlite", "custom-jsonl"})

    def test_legacy_v1_jsonl_normalizes_to_v11_with_unavailable_provenance(self) -> None:
        config = _config(self.workspace)
        config.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        legacy = {
            "epoch_id": "55555555555545558555555555555555",
            "schema_version": "1.0.0",
            "task_id": "legacy-task",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "route": {"models": ["m"]},
            "economics": {"input_tokens": 0, "output_tokens": 0, "cogs_usd": 0.0, "duration_seconds": 0.0},
            "operations": {"cli_tools": ["git"]},
            "outcome": {"gate_exit_codes": [0]},
        }
        config.jsonl_path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")

        result = read_epoch_records(config, source="jsonl")
        record = result.records[0]

        self.assertEqual(record["schema_version"], "1.1.0")
        self.assertEqual(record["backlog_item_id"], "legacy-task")
        self.assertEqual(record["economics"]["metric_sources"]["input_tokens"], "unavailable")
        self.assertEqual(record["economics"]["metric_quality"]["duration_seconds"], "unavailable")

    def test_missing_disabled_or_absent_inputs_return_empty_unavailable_result(self) -> None:
        disabled = load_telemetry_config(None, workspace_root=self.workspace)
        disabled_result = read_epoch_records(disabled, source="combined")
        missing_result = read_epoch_records(_config(self.workspace), source="combined")

        self.assertEqual(disabled_result.status, "disabled")
        self.assertEqual(disabled_result.records, ())
        self.assertEqual(missing_result.status, "unavailable")
        self.assertEqual(missing_result.records, ())
        self.assertTrue(missing_result.diagnostics)

    def test_jsonl_duplicate_and_conflicting_retries_preserve_first_record(self) -> None:
        config = _config(self.workspace)
        first = _epoch("66666666666646668666666666666666", "first")
        same = first.to_record()
        conflict = _epoch(first.epoch_id, "conflict").to_record()
        config.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        config.jsonl_path.write_text(
            "\n".join(json.dumps(item, separators=(",", ":")) for item in (same, same, conflict))
            + "\n",
            encoding="utf-8",
        )

        result = read_epoch_records(config, source="jsonl")

        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.records[0]["task_id"], "first")
        self.assertTrue(any("conflict" in item.lower() for item in result.diagnostics))

    def test_combined_mode_prefers_sqlite_and_surfaces_cross_sink_conflicts(self) -> None:
        config = _config(self.workspace)
        sqlite_epoch = _epoch("77777777777747778777777777777777", "sqlite-wins")
        jsonl_conflict = _epoch(sqlite_epoch.epoch_id, "jsonl-conflict")
        write_epoch(sqlite_epoch, config.database_path)
        config.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        config.jsonl_path.write_text(json.dumps(jsonl_conflict.to_record()) + "\n", encoding="utf-8")

        result = read_epoch_records(config, source="combined")

        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.records[0]["task_id"], "sqlite-wins")
        self.assertTrue(any("sqlite precedence" in item.lower() for item in result.diagnostics))

    def test_partial_sink_retry_mirrored_records_count_once(self) -> None:
        config = _config(self.workspace)
        epoch = _epoch("88888888888848888888888888888888", "partial-repair")
        write_epoch(epoch, config.database_path)
        append_epoch(epoch, config.jsonl_path)

        result = read_epoch_records(config, source="combined")

        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.records[0]["task_id"], "partial-repair")
        self.assertEqual(result.records[0]["sizing"]["task_size_label"], "M")

    def test_legacy_sqlite_row_without_payload_json_is_reconstructed_and_normalized(self) -> None:
        config = _config(self.workspace)
        ensure_schema(config.database_path)
        conn = sqlite3.connect(str(config.database_path))
        try:
            conn.execute(
                """
                INSERT INTO execution_epochs (
                    epoch_id, schema_version, task_id, timestamp, primary_model,
                    models, input_tokens, output_tokens, total_tokens, cogs_usd,
                    duration_seconds, cli_tools, gate_exit_codes, blocked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "99999999999949998999999999999999",
                    "1.0.0",
                    "legacy-sqlite",
                    "2026-01-01T00:00:00+00:00",
                    "m",
                    '["m"]',
                    1,
                    2,
                    3,
                    0.01,
                    4.0,
                    '["git"]',
                    "[0]",
                    0,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        result = read_epoch_records(config, source="sqlite")

        self.assertEqual(result.records[0]["schema_version"], "1.1.0")
        self.assertEqual(result.records[0]["backlog_item_id"], "legacy-sqlite")
        self.assertEqual(result.records[0]["sizing"], None)


if __name__ == "__main__":
    unittest.main()
