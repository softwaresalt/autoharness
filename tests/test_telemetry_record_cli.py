"""End-to-end tests for `autoharness telemetry record` (U5, task 051.001)."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from autoharness.cli import main
from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
)
from autoharness.telemetry.record import record_epoch

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

_PAYLOAD = {
    "task_id": "051.001-T",
    "route": {"models": ["claude-opus-4.6"]},
    "economics": {"input_tokens": 100, "output_tokens": 50, "cogs_usd": 0.01, "duration_seconds": 12.0},
    "operations": {"cli_tools": ["git", "pytest"]},
    "outcome": {"gate_exit_codes": [0]},
}


class TelemetryRecordCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        (self.workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
        self.payload_path = self.workspace / "epoch.json"
        self.payload_path.write_text(json.dumps(_PAYLOAD), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_config(self, text: str) -> None:
        (self.workspace / ".autoharness" / "config.yaml").write_text(text, encoding="utf-8")

    def _run(self, *extra: str) -> None:
        main(["telemetry", "record", "--from-json", str(self.payload_path),
              "--workspace", str(self.workspace), *extra])

    def test_enabled_telemetry_reaches_both_sinks(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        self._run()

        db_path = self.workspace / ".autoharness" / "metrics" / "execution_epochs.db"
        jsonl_path = self.workspace / ".autoharness" / "metrics" / "execution_epochs.jsonl"
        self.assertTrue(db_path.exists())
        self.assertTrue(jsonl_path.exists())

        conn = sqlite3.connect(str(db_path))
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM execution_epochs WHERE task_id = ?", ("051.001-T",)
            ).fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 1)

        line = jsonl_path.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(json.loads(line)["task_id"], "051.001-T")

    def test_disabled_telemetry_is_noop_success(self) -> None:
        self._write_config(_DISABLED_CONFIG)
        # No SystemExit ⇒ exit 0 no-op.
        self._run()
        db_path = self.workspace / ".autoharness" / "metrics" / "execution_epochs.db"
        self.assertFalse(db_path.exists())

    def test_absent_config_is_noop_success(self) -> None:
        # No config file at all ⇒ fail-open disabled, no-op success.
        self._run()
        db_path = self.workspace / ".autoharness" / "metrics" / "execution_epochs.db"
        self.assertFalse(db_path.exists())

    def test_enabled_non_utf8_payload_file_exits_2(self) -> None:
        # A non-UTF-8 payload file on the ENABLED path must be a controlled
        # exit 2, never a raw UnicodeDecodeError traceback.
        self._write_config(_ENABLED_CONFIG)
        self.payload_path.write_bytes(b"\xff\xfe\x00 not utf-8 \xff")
        with self.assertRaises(SystemExit) as ctx:
            self._run()
        self.assertEqual(ctx.exception.code, 2)

    def test_enabled_numeric_overflow_payload_exits_2(self) -> None:
        # A numeric field that overflows int() (1e309 -> inf) must be a
        # controlled exit 2, not a raw OverflowError traceback.
        self._write_config(_ENABLED_CONFIG)
        bad = json.loads(json.dumps(_PAYLOAD))
        bad["economics"]["input_tokens"] = 1e309
        self.payload_path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self._run()
        self.assertEqual(ctx.exception.code, 2)

    def test_invalid_json_payload_exits_2(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        self.payload_path.write_text("{ not valid json", encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self._run()
        self.assertEqual(ctx.exception.code, 2)

    def test_missing_payload_class_exits_2(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        bad = dict(_PAYLOAD)
        del bad["outcome"]
        self.payload_path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self._run()
        self.assertEqual(ctx.exception.code, 2)

    def test_mode_none_with_garbage_payload_is_noop_success(self) -> None:
        # Telemetry disabled ⇒ the payload is never parsed; garbage is a no-op
        # success (exit 0), NOT an exit-2 validation failure.
        self._write_config(_DISABLED_CONFIG)
        self.payload_path.write_text("{ not json", encoding="utf-8")
        self._run()  # no SystemExit ⇒ exit 0
        db_path = self.workspace / ".autoharness" / "metrics" / "execution_epochs.db"
        self.assertFalse(db_path.exists())

    def test_malformed_config_yaml_is_failopen_disabled(self) -> None:
        # A config.yaml that cannot be parsed must fail open to disabled (exit 0),
        # never propagate a YAMLError traceback.
        self._write_config("telemetry: : : not valid yaml: [\n")
        self.payload_path.write_text("{ not json", encoding="utf-8")
        self._run()  # no SystemExit ⇒ exit 0 disabled
        db_path = self.workspace / ".autoharness" / "metrics" / "execution_epochs.db"
        self.assertFalse(db_path.exists())

    def test_enabled_malformed_payload_route_shape_exits_2(self) -> None:
        # route: [] would raise AttributeError deep in from_mapping; it must be
        # normalized to a controlled exit 2 (no raw traceback).
        self._write_config(_ENABLED_CONFIG)
        bad = dict(_PAYLOAD)
        bad["route"] = []
        self.payload_path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self._run()
        self.assertEqual(ctx.exception.code, 2)

    def test_enabled_bad_token_coercion_exits_2(self) -> None:
        # input_tokens: "abc" would raise ValueError via int("abc"); normalized to
        # a controlled exit 2.
        self._write_config(_ENABLED_CONFIG)
        bad = dict(_PAYLOAD)
        bad["economics"] = {"input_tokens": "abc"}
        self.payload_path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self._run()
        self.assertEqual(ctx.exception.code, 2)


class RecordEpochFailOpenTests(unittest.TestCase):
    """A failing sink must never propagate a completion-blocking signal (P2-1)."""

    def _epoch(self) -> ExecutionEpoch:
        return ExecutionEpoch(
            task_id="x",
            route=RouteConfiguration(),
            economics=EconomicPayload(),
            operations=OperationalReality(),
            outcome=AbsoluteOutcome(),
        )

    def test_sink_error_is_captured_not_raised(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Point the DB path *under an existing file* so directory creation
            # fails — simulating a broken sink.
            blocker = Path(tmp) / "blocker"
            blocker.write_text("i am a file", encoding="utf-8")
            bad_db = blocker / "metrics" / "execution_epochs.db"
            config = TelemetryConfig(
                enabled=True,
                mode="sqlite",
                database_path=bad_db,
                emit_jsonl=False,
            )
            # Must not raise despite the sink failure.
            summary = record_epoch(self._epoch(), config)
            self.assertTrue(summary.enabled)
            self.assertFalse(summary.sqlite_written)
            self.assertTrue(summary.errors)


if __name__ == "__main__":
    unittest.main()
