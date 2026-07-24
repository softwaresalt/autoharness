"""End-to-end tests for `autoharness telemetry record` (U5, task 051.001)."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.cli import main
from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.context import begin_context
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
    "epoch_id": "11111111111141118111111111111111",
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

    def test_non_ascii_payload_replays_idempotently_across_sinks(self) -> None:
        """Regression (local review P2): the SQLite and JSONL payload-digest
        canonicalization must agree for non-ASCII payloads so an identical
        replay is idempotent rather than a false cross-sink immutable conflict.
        """
        self._write_config(_ENABLED_CONFIG)
        from autoharness.telemetry.record import load_workspace_telemetry_config

        config = load_workspace_telemetry_config(self.workspace)
        payload = dict(_PAYLOAD)
        payload["epoch_id"] = "22222222222242228222222222222222"
        payload["branch"] = "feat/t\u00ebst-\u03a9"  # non-ASCII correlation value
        epoch = ExecutionEpoch.from_mapping(payload)

        first = record_epoch(epoch, config)
        second = record_epoch(epoch, config)

        self.assertEqual(first.idempotency_outcome, "created")
        self.assertEqual(second.idempotency_outcome, "idempotent_replay")
        self.assertEqual(second.errors, [])

    def test_record_rejects_missing_epoch_id_without_context(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        payload = dict(_PAYLOAD)
        del payload["epoch_id"]
        self.payload_path.write_text(json.dumps(payload), encoding="utf-8")

        with self.assertRaises(SystemExit) as ctx:
            self._run()

        self.assertEqual(ctx.exception.code, 2)

    def test_record_context_ref_merges_frozen_identity_and_reports_digests(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        from autoharness.telemetry.record import load_workspace_telemetry_config

        config = load_workspace_telemetry_config(self.workspace)
        begin = begin_context(
            config,
            self.workspace,
            task_id="079.016-T",
            backlog_item_id="079.016-T",
            feature_id="079-F",
            shipment_id="092-S",
            epoch_id="22222222-2222-4222-8222-222222222222",
            captured_at="2026-07-24T03:37:49Z",
        )
        close_payload = dict(_PAYLOAD)
        close_payload.pop("epoch_id")
        close_payload["task_id"] = "will-be-overridden"
        self.payload_path.write_text(json.dumps(close_payload), encoding="utf-8")

        import contextlib
        import io

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self._run("--context-ref", begin.context_ref, "--json")
        result = json.loads(stdout.getvalue())

        self.assertEqual(result["epoch_id"], "22222222222242228222222222222222")
        self.assertEqual(result["context_ref"], begin.context_ref)
        self.assertEqual(result["context_digest"], begin.context_digest)
        self.assertRegex(result["payload_digest"], r"^[0-9a-f]{64}$")
        self.assertNotEqual(result["payload_digest"], result["context_digest"])
        self.assertEqual(result["idempotency_outcome"], "created")

        conn = sqlite3.connect(str(self.workspace / ".autoharness" / "metrics" / "execution_epochs.db"))
        try:
            row = conn.execute(
                "SELECT task_id, feature_id, shipment_id FROM execution_epochs WHERE epoch_id=?",
                ("22222222222242228222222222222222",),
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(row, ("079.016-T", "079-F", "092-S"))

    def test_record_context_ref_rejects_unsafe_refs_mismatch_and_tamper(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        from autoharness.telemetry.record import load_workspace_telemetry_config

        config = load_workspace_telemetry_config(self.workspace)
        begin = begin_context(
            config,
            self.workspace,
            task_id="079.016-T",
            epoch_id="33333333-3333-4333-8333-333333333333",
            captured_at="2026-07-24T03:37:49Z",
        )

        for bad_ref in (str(begin.context_path), "..\\escape.json"):
            with self.assertRaises(SystemExit) as ctx:
                self._run("--context-ref", bad_ref)
            self.assertEqual(ctx.exception.code, 2)

        mismatched = dict(_PAYLOAD)
        mismatched["epoch_id"] = "44444444444444448444444444444444"
        self.payload_path.write_text(json.dumps(mismatched), encoding="utf-8")
        with self.assertRaises(SystemExit) as mismatch_ctx:
            self._run("--context-ref", begin.context_ref)
        self.assertEqual(mismatch_ctx.exception.code, 2)

        payload = json.loads(begin.context_path.read_text(encoding="utf-8"))
        payload["task_id"] = "tampered"
        begin.context_path.write_text(json.dumps(payload), encoding="utf-8")
        close_payload = dict(_PAYLOAD)
        close_payload["epoch_id"] = begin.epoch_id
        self.payload_path.write_text(json.dumps(close_payload), encoding="utf-8")
        with self.assertRaises(SystemExit) as tamper_ctx:
            self._run("--context-ref", begin.context_ref)
        self.assertEqual(tamper_ctx.exception.code, 2)

    def test_record_context_idempotency_and_conflict_outcomes(self) -> None:
        self._write_config(_ENABLED_CONFIG)
        from autoharness.telemetry.record import load_workspace_telemetry_config

        config = load_workspace_telemetry_config(self.workspace)
        begin = begin_context(
            config,
            self.workspace,
            task_id="079.016-T",
            epoch_id="55555555-5555-4555-8555-555555555555",
            captured_at="2026-07-24T03:37:49Z",
        )
        close_payload = dict(_PAYLOAD)
        close_payload.pop("epoch_id")
        close_payload["economics"] = {"input_tokens": 1, "output_tokens": 1}
        self.payload_path.write_text(json.dumps(close_payload), encoding="utf-8")

        import contextlib
        import io

        first_stdout = io.StringIO()
        with contextlib.redirect_stdout(first_stdout):
            self._run("--context-ref", begin.context_ref, "--json")
        second_stdout = io.StringIO()
        with contextlib.redirect_stdout(second_stdout):
            self._run("--context-ref", begin.context_ref, "--json")

        conflict_payload = dict(close_payload)
        conflict_payload["economics"] = {"input_tokens": 999, "output_tokens": 1}
        self.payload_path.write_text(json.dumps(conflict_payload), encoding="utf-8")
        conflict_stdout = io.StringIO()
        with contextlib.redirect_stdout(conflict_stdout):
            self._run("--context-ref", begin.context_ref, "--json")

        self.assertEqual(json.loads(first_stdout.getvalue())["idempotency_outcome"], "created")
        self.assertEqual(json.loads(second_stdout.getvalue())["idempotency_outcome"], "idempotent_replay")
        conflict = json.loads(conflict_stdout.getvalue())
        self.assertEqual(conflict["idempotency_outcome"], "conflict_rejected")
        self.assertFalse(conflict["sqlite_written"])
        self.assertFalse(conflict["jsonl_written"])

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

    def test_enabled_route_models_as_string_exits_2(self) -> None:
        # route.models given as a string (not an array) must be rejected as a
        # malformed shape (exit 2), never silently split into a tuple of chars.
        self._write_config(_ENABLED_CONFIG)
        bad = json.loads(json.dumps(_PAYLOAD))
        bad["route"]["models"] = "claude-opus-4.6"
        self.payload_path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self._run()
        self.assertEqual(ctx.exception.code, 2)

    def test_enabled_cli_tools_as_string_exits_2(self) -> None:
        # operations.cli_tools given as a string must be rejected (exit 2),
        # never silently split into a tuple of chars.
        self._write_config(_ENABLED_CONFIG)
        bad = json.loads(json.dumps(_PAYLOAD))
        bad["operations"]["cli_tools"] = "git"
        self.payload_path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self._run()
        self.assertEqual(ctx.exception.code, 2)

    def test_enabled_gate_exit_codes_as_string_exits_2(self) -> None:
        # outcome.gate_exit_codes given as a string must be rejected (exit 2).
        self._write_config(_ENABLED_CONFIG)
        bad = json.loads(json.dumps(_PAYLOAD))
        bad["outcome"]["gate_exit_codes"] = "0"
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

    def test_sqlite_write_conflict_sets_conflict_rejected_outcome(self) -> None:
        """Copilot review t3: a TelemetryConflictError raised by the sqlite sink
        (another writer inserted after preflight passed) must still finalize the
        documented ``conflict_rejected`` idempotency outcome instead of leaving it
        unset by returning early."""
        from autoharness.telemetry import sqlite_sink

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / ".autoharness" / "metrics" / "execution_epochs.db"
            config = TelemetryConfig(
                enabled=True,
                mode="sqlite",
                database_path=db_path,
                emit_jsonl=False,
            )
            with mock.patch(
                "autoharness.telemetry.record.sqlite_sink.write_epoch",
                side_effect=sqlite_sink.TelemetryConflictError("post-preflight race"),
            ):
                summary = record_epoch(self._epoch(), config)

            self.assertEqual(summary.idempotency_outcome, "conflict_rejected")
            self.assertFalse(summary.sqlite_written)
            self.assertTrue(any("conflict" in err.lower() for err in summary.errors))

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

    def test_partial_sink_failure_repairs_missing_jsonl_on_identical_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            db_path = workspace / ".autoharness" / "metrics" / "execution_epochs.db"
            config = TelemetryConfig(
                enabled=True,
                mode="sqlite",
                database_path=db_path,
                emit_jsonl=True,
                jsonl_path=db_path.parent / "execution_epochs.jsonl",
            )
            epoch = self._epoch()
            with mock.patch(
                "autoharness.telemetry.record.jsonl_sink.append_epoch",
                side_effect=OSError("jsonl unavailable"),
            ):
                first = record_epoch(epoch, config)
            retry = record_epoch(epoch, config)

            self.assertTrue(first.sqlite_written)
            self.assertFalse(first.jsonl_written)
            self.assertTrue(first.errors)
            self.assertTrue(retry.sqlite_written)
            self.assertTrue(retry.jsonl_written)
            self.assertEqual(len(config.jsonl_path.read_text(encoding="utf-8").splitlines()), 1)

    def test_conflicting_retry_after_partial_sqlite_success_writes_no_missing_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            db_path = workspace / ".autoharness" / "metrics" / "execution_epochs.db"
            config = TelemetryConfig(
                enabled=True,
                mode="sqlite",
                database_path=db_path,
                emit_jsonl=True,
                jsonl_path=db_path.parent / "execution_epochs.jsonl",
            )
            epoch = self._epoch()
            with mock.patch(
                "autoharness.telemetry.record.jsonl_sink.append_epoch",
                side_effect=OSError("jsonl unavailable"),
            ):
                record_epoch(epoch, config)
            conflict = ExecutionEpoch(
                epoch_id=epoch.epoch_id,
                task_id=epoch.task_id,
                route=epoch.route,
                economics=EconomicPayload(input_tokens=999),
                operations=epoch.operations,
                outcome=epoch.outcome,
            )

            summary = record_epoch(conflict, config)

            self.assertFalse(summary.sqlite_written)
            self.assertFalse(summary.jsonl_written)
            self.assertTrue(any("conflict" in err.lower() for err in summary.errors))
            self.assertFalse(config.jsonl_path.exists())

    def test_conflicting_retry_after_partial_jsonl_success_writes_no_missing_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            db_path = workspace / ".autoharness" / "metrics" / "execution_epochs.db"
            config = TelemetryConfig(
                enabled=True,
                mode="sqlite",
                database_path=db_path,
                emit_jsonl=True,
                jsonl_path=db_path.parent / "execution_epochs.jsonl",
            )
            epoch = self._epoch()
            with mock.patch(
                "autoharness.telemetry.record.sqlite_sink.write_epoch",
                side_effect=OSError("sqlite unavailable"),
            ):
                first = record_epoch(epoch, config)
            conflict = ExecutionEpoch(
                epoch_id=epoch.epoch_id,
                task_id=epoch.task_id,
                route=epoch.route,
                economics=EconomicPayload(input_tokens=999),
                operations=epoch.operations,
                outcome=epoch.outcome,
            )

            summary = record_epoch(conflict, config)

            self.assertFalse(first.sqlite_written)
            self.assertTrue(first.jsonl_written)
            self.assertFalse(summary.sqlite_written)
            self.assertFalse(summary.jsonl_written)
            self.assertTrue(any("conflict" in err.lower() for err in summary.errors))
            self.assertFalse(db_path.exists())


if __name__ == "__main__":
    unittest.main()
