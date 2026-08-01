"""CLI tests for `autoharness telemetry event` and `telemetry record --compose-tool-events`
(U6, 084.006-T)."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from autoharness.cli import TELEMETRY_USAGE, main
from autoharness.telemetry.context import begin_context
from autoharness.telemetry.record import load_workspace_telemetry_config
from autoharness.telemetry.tool_event_jsonl import journal_path_for_config, read_events

_ENABLED_CONFIG = """
schema_version: "1.0.0"
telemetry:
  mode: "sqlite"
  database_path: ".autoharness/metrics/execution_epochs.db"
  emit_jsonl: true
"""

_DISABLED_CONFIG = """
schema_version: "1.0.0"
telemetry:
  mode: "none"
"""

_EVENT_PAYLOAD = {
    "tool_surface": "cli",
    "tool_name": "pytest",
    "operation": "run_tests",
    "status": "success",
    "sensitivity": "internal",
    "input_tokens": 10,
    "output_tokens": 4,
    "metric_sources": {"input_tokens": "host_reported", "output_tokens": "host_reported"},
    "metric_quality": {"input_tokens": "observed", "output_tokens": "observed"},
}

_EPOCH_PAYLOAD = {
    "task_id": "084.006-T",
    "route": {"models": ["claude-opus-4.6"]},
    "economics": {"cogs_usd": 0.01, "duration_seconds": 12.0},
    "operations": {},
    "outcome": {"gate_exit_codes": [0]},
}


class TelemetryEventCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        (self.workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
        self.event_payload_path = self.workspace / "event.json"
        self.event_payload_path.write_text(json.dumps(_EVENT_PAYLOAD), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_config(self, text: str) -> None:
        (self.workspace / ".autoharness" / "config.yaml").write_text(text, encoding="utf-8")

    def _begin(self, task_id: str = "084.006-T", epoch_id: str = "3" * 32):
        config = load_workspace_telemetry_config(self.workspace)
        return begin_context(
            config,
            self.workspace,
            task_id=task_id,
            epoch_id=epoch_id,
            captured_at="2026-07-31T00:00:00Z",
        )

    def _run_event(self, *extra: str) -> None:
        main(
            [
                "telemetry",
                "event",
                "--from-json",
                str(self.event_payload_path),
                "--workspace",
                str(self.workspace),
                *extra,
            ]
        )

    def test_help_lists_event_and_compose_flag(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["telemetry", "help"])
        self.assertIn("telemetry event", buf.getvalue())
        self.assertIn("--compose-tool-events", buf.getvalue())
        self.assertIn("telemetry event", TELEMETRY_USAGE)

    def test_event_requires_context_ref(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        with self.assertRaises(SystemExit) as ctx:
            self._run_event()
        self.assertEqual(ctx.exception.code, 2)

    def test_disabled_telemetry_is_a_noop_before_parsing_payload(self) -> None:
        self._write_config(_DISABLED_CONFIG)
        # Malformed payload should never even be read when disabled.
        self.event_payload_path.write_text("not json at all", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            self._run_event("--context-ref", "does-not-exist.json", "--json")
        summary = json.loads(buf.getvalue())
        self.assertFalse(summary["enabled"])
        self.assertFalse(summary["written"])

    def test_invalid_payload_exits_2(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        begin = self._begin()
        bad_payload = dict(_EVENT_PAYLOAD)
        del bad_payload["tool_name"]
        self.event_payload_path.write_text(json.dumps(bad_payload), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self._run_event("--context-ref", str(begin.context_ref))
        self.assertEqual(ctx.exception.code, 2)

    def test_context_bound_event_is_appended_to_journal_with_frozen_correlation(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        begin = self._begin(task_id="084.006-T", epoch_id="4" * 32)

        buf = io.StringIO()
        with redirect_stdout(buf):
            self._run_event("--context-ref", str(begin.context_ref), "--json")
        summary = json.loads(buf.getvalue())
        self.assertTrue(summary["written"])

        config = load_workspace_telemetry_config(self.workspace)
        journal_path = journal_path_for_config(config)
        result = read_events(journal_path, epoch_id="4" * 32)
        self.assertEqual(len(result.events), 1)
        self.assertEqual(result.events[0].epoch_id, "4" * 32)
        self.assertEqual(result.events[0].backlog_item_id, "084.006-T")

    def test_direct_caller_can_supply_matching_epoch_id_explicitly(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        begin = self._begin(task_id="084.006-T", epoch_id="5" * 32)
        payload = dict(_EVENT_PAYLOAD)
        payload["epoch_id"] = "5" * 32
        self.event_payload_path.write_text(json.dumps(payload), encoding="utf-8")

        self._run_event("--context-ref", str(begin.context_ref))

        config = load_workspace_telemetry_config(self.workspace)
        journal_path = journal_path_for_config(config)
        result = read_events(journal_path, epoch_id="5" * 32)
        self.assertEqual(len(result.events), 1)

    def test_mismatched_explicit_epoch_id_is_rejected(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        begin = self._begin(task_id="084.006-T", epoch_id="6" * 32)
        payload = dict(_EVENT_PAYLOAD)
        payload["epoch_id"] = "7" * 32
        self.event_payload_path.write_text(json.dumps(payload), encoding="utf-8")

        with self.assertRaises(SystemExit) as ctx:
            self._run_event("--context-ref", str(begin.context_ref))
        self.assertEqual(ctx.exception.code, 2)

    def test_sink_failure_is_a_warning_not_a_crash(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        begin = self._begin(task_id="084.006-T", epoch_id="8" * 32)

        from unittest import mock

        with mock.patch(
            "autoharness.telemetry.tool_event_jsonl.append_event",
            side_effect=RuntimeError("disk full"),
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                self._run_event("--context-ref", str(begin.context_ref), "--json")
        summary = json.loads(buf.getvalue())
        self.assertFalse(summary["written"])
        self.assertTrue(summary["errors"])


class TelemetryRecordComposeCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        (self.workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
        self.event_payload_path = self.workspace / "event.json"
        self.event_payload_path.write_text(json.dumps(_EVENT_PAYLOAD), encoding="utf-8")
        self.epoch_payload_path = self.workspace / "epoch.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_config(self, text: str) -> None:
        (self.workspace / ".autoharness" / "config.yaml").write_text(text, encoding="utf-8")

    def _begin(self, task_id: str = "084.006-T", epoch_id: str = "9" * 32):
        config = load_workspace_telemetry_config(self.workspace)
        return begin_context(
            config,
            self.workspace,
            task_id=task_id,
            epoch_id=epoch_id,
            captured_at="2026-07-31T00:00:00Z",
        )

    def test_compose_flag_merges_events_into_recorded_epoch(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        begin = self._begin(task_id="084.006-T", epoch_id="9" * 32)

        main(
            [
                "telemetry",
                "event",
                "--from-json",
                str(self.event_payload_path),
                "--workspace",
                str(self.workspace),
                "--context-ref",
                str(begin.context_ref),
            ]
        )

        close_payload = dict(_EPOCH_PAYLOAD)
        self.epoch_payload_path.write_text(json.dumps(close_payload), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            main(
                [
                    "telemetry",
                    "record",
                    "--from-json",
                    str(self.epoch_payload_path),
                    "--workspace",
                    str(self.workspace),
                    "--context-ref",
                    str(begin.context_ref),
                    "--compose-tool-events",
                    "--json",
                ]
            )
        summary = json.loads(buf.getvalue())
        self.assertTrue(summary["composition_requested"])
        self.assertTrue(summary["composition_applied"])
        self.assertEqual(summary["composed_selected_event_count"], 1)

        import sqlite3

        db_path = self.workspace / ".autoharness" / "metrics" / "execution_epochs.db"
        conn = sqlite3.connect(str(db_path))
        try:
            row = conn.execute(
                "SELECT input_tokens, output_tokens FROM execution_epochs WHERE epoch_id = ?",
                ("9" * 32,),
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(row, (10, 4))

    def test_compose_flag_off_by_default_leaves_behavior_unchanged(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        begin = self._begin(task_id="084.006-T", epoch_id="a" * 32)
        close_payload = dict(_EPOCH_PAYLOAD)
        self.epoch_payload_path.write_text(json.dumps(close_payload), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            main(
                [
                    "telemetry",
                    "record",
                    "--from-json",
                    str(self.epoch_payload_path),
                    "--workspace",
                    str(self.workspace),
                    "--context-ref",
                    str(begin.context_ref),
                    "--json",
                ]
            )
        summary = json.loads(buf.getvalue())
        self.assertFalse(summary["composition_requested"])
        self.assertFalse(summary["composition_applied"])

    def test_hybrid_payload_with_compose_flag_exits_2(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        begin = self._begin(task_id="084.006-T", epoch_id="b" * 32)
        close_payload = dict(_EPOCH_PAYLOAD)
        close_payload["economics"] = {
            "input_tokens": 5,
            "cogs_usd": 0.01,
            "duration_seconds": 12.0,
            "metric_sources": {"input_tokens": "host_reported"},
            "metric_quality": {"input_tokens": "observed"},
        }
        self.epoch_payload_path.write_text(json.dumps(close_payload), encoding="utf-8")

        with self.assertRaises(SystemExit) as ctx:
            main(
                [
                    "telemetry",
                    "record",
                    "--from-json",
                    str(self.epoch_payload_path),
                    "--workspace",
                    str(self.workspace),
                    "--context-ref",
                    str(begin.context_ref),
                    "--compose-tool-events",
                ]
            )
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
