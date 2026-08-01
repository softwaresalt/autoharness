"""Tests for record-path tool-event composition integration (U5, 084.005-T).

These tests exercise :func:`autoharness.telemetry.record.record_epoch`'s new
``compose_tool_events`` opt-in parameter directly at the API level (the CLI
``--compose-tool-events`` flag is U6's job — see
``tests/test_telemetry_event_cli.py``).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
)
from autoharness.telemetry.record import record_epoch
from autoharness.telemetry.tool_event import ToolTelemetryEvent
from autoharness.telemetry.tool_event_compose import ToolEventCompositionError
from autoharness.telemetry.tool_event_jsonl import record_tool_event

_EPOCH_ID = "1" * 32
_OTHER_EPOCH_ID = "2" * 32
_TASK_ID = "084.005-T"


def _config(workspace: Path) -> TelemetryConfig:
    db_path = workspace / ".autoharness" / "metrics" / "execution_epochs.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return TelemetryConfig(
        enabled=True,
        mode="sqlite",
        database_path=db_path,
        emit_jsonl=True,
        jsonl_path=workspace / ".autoharness" / "metrics" / "execution_epochs.jsonl",
    )


def _bare_epoch(epoch_id: str = _EPOCH_ID, task_id: str = _TASK_ID) -> ExecutionEpoch:
    return ExecutionEpoch(
        task_id=task_id,
        epoch_id=epoch_id,
        timestamp="2026-07-31T00:00:00Z",
        route=RouteConfiguration(),
        economics=EconomicPayload(cogs_usd=0.02, duration_seconds=5.0),
        operations=OperationalReality(),
        outcome=AbsoluteOutcome(gate_exit_codes=[0]),
    )


def _event(**overrides) -> ToolTelemetryEvent:
    kwargs = dict(
        tool_surface="cli",
        tool_name="pytest",
        operation="run_tests",
        status="success",
        sensitivity="internal",
        epoch_id=_EPOCH_ID,
        input_tokens=10,
        output_tokens=4,
        metric_sources={"input_tokens": "host_reported", "output_tokens": "host_reported"},
        metric_quality={"input_tokens": "observed", "output_tokens": "observed"},
    )
    kwargs.update(overrides)
    return ToolTelemetryEvent(**kwargs)


class RecordComposeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        self.config = _config(self.workspace)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_no_events_composes_to_a_no_op_patch(self) -> None:
        epoch = _bare_epoch()
        summary = record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertTrue(summary.composition_requested)
        self.assertTrue(summary.composition_applied)
        self.assertEqual(summary.composed_selected_event_count, 0)
        self.assertEqual(summary.composed_ignored_event_count, 0)
        self.assertEqual(summary.errors, [])
        self.assertEqual(summary.idempotency_outcome, "created")

    def test_composed_metrics_are_merged_from_correlated_events(self) -> None:
        record_tool_event(_event(input_tokens=10, output_tokens=4), self.config)
        record_tool_event(_event(input_tokens=6, output_tokens=2), self.config)

        epoch = _bare_epoch()
        summary = record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertTrue(summary.composition_applied)
        self.assertEqual(summary.composed_selected_event_count, 2)

        import sqlite3

        conn = sqlite3.connect(str(self.config.database_path))
        try:
            row = conn.execute(
                "SELECT input_tokens, output_tokens, cogs_usd, duration_seconds "
                "FROM execution_epochs WHERE epoch_id = ?",
                (_EPOCH_ID,),
            ).fetchone()
        finally:
            conn.close()

        input_tokens, output_tokens, cogs_usd, duration_seconds = row
        self.assertEqual(input_tokens, 16)
        self.assertEqual(output_tokens, 6)
        # close-payload-owned fields must survive composition untouched.
        self.assertEqual(cogs_usd, 0.02)
        self.assertEqual(duration_seconds, 5.0)

    def test_cross_epoch_events_are_ignored(self) -> None:
        record_tool_event(_event(epoch_id=_OTHER_EPOCH_ID, input_tokens=99, output_tokens=99), self.config)

        epoch = _bare_epoch()
        summary = record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertEqual(summary.composed_selected_event_count, 0)

    def test_backlog_item_id_fallback_only_applies_to_events_without_epoch_id(self) -> None:
        # No epoch_id on the event: falls back to backlog_item_id correlation.
        record_tool_event(
            _event(epoch_id=None, backlog_item_id=_TASK_ID, input_tokens=7, output_tokens=3),
            self.config,
        )
        epoch = _bare_epoch()
        summary = record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertEqual(summary.composed_selected_event_count, 1)

    def test_hybrid_close_payload_is_refused(self) -> None:
        epoch = ExecutionEpoch(
            task_id=_TASK_ID,
            epoch_id=_EPOCH_ID,
            timestamp="2026-07-31T00:00:00Z",
            route=RouteConfiguration(),
            economics=EconomicPayload(
                input_tokens=5,
                cogs_usd=0.02,
                duration_seconds=5.0,
                metric_sources={"input_tokens": "host_reported"},
                metric_quality={"input_tokens": "observed"},
            ),
            operations=OperationalReality(),
            outcome=AbsoluteOutcome(gate_exit_codes=[0]),
        )
        with self.assertRaises(ToolEventCompositionError):
            record_epoch(epoch, self.config, compose_tool_events=True)

    def test_hybrid_refusal_does_not_write_to_sinks(self) -> None:
        epoch = ExecutionEpoch(
            task_id=_TASK_ID,
            epoch_id=_EPOCH_ID,
            timestamp="2026-07-31T00:00:00Z",
            route=RouteConfiguration(),
            economics=EconomicPayload(
                input_tokens=5,
                cogs_usd=0.02,
                duration_seconds=5.0,
                metric_sources={"input_tokens": "host_reported"},
                metric_quality={"input_tokens": "observed"},
            ),
            operations=OperationalReality(),
            outcome=AbsoluteOutcome(gate_exit_codes=[0]),
        )
        with self.assertRaises(ToolEventCompositionError):
            record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertFalse(self.config.database_path.exists())

    def test_missing_journal_fails_open_and_still_records_close_payload(self) -> None:
        # No journal file has been created at all (no events recorded).
        epoch = _bare_epoch()
        summary = record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertTrue(summary.composition_requested)
        self.assertEqual(summary.errors, [])
        self.assertEqual(summary.idempotency_outcome, "created")

    def test_composition_read_failure_fails_open(self) -> None:
        journal_path = self.config.database_path.parent / "tool_events.jsonl"
        journal_path.parent.mkdir(parents=True, exist_ok=True)
        journal_path.write_text("not-json\n", encoding="utf-8")

        from unittest import mock

        epoch = _bare_epoch()
        with mock.patch(
            "autoharness.telemetry.record.tool_event_jsonl.read_events",
            side_effect=RuntimeError("boom"),
        ):
            summary = record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertTrue(summary.composition_requested)
        self.assertFalse(summary.composition_applied)
        self.assertTrue(
            any("tool-event composition unavailable" in diag for diag in summary.composition_diagnostics)
        )
        self.assertEqual(summary.idempotency_outcome, "created")

    def test_segment_io_failure_skips_composition_and_persists_original_close_payload(self) -> None:
        # Review fix 3 (PR #273, PRRT_kwDORzpWpM6Vnq_P): read_events returning an
        # "unavailable" status (a segment I/O failure, not an exception) must
        # skip composition entirely so the original close-supplied economics
        # persist unmerged rather than an undercounted partial roll-up.
        record_tool_event(_event(input_tokens=10, output_tokens=4), self.config)

        from unittest import mock

        from autoharness.telemetry.tool_event_jsonl import ToolEventReadResult

        epoch = _bare_epoch()
        with mock.patch(
            "autoharness.telemetry.record.tool_event_jsonl.read_events",
            return_value=ToolEventReadResult(
                status="unavailable", events=(), diagnostics=("tool event journal unavailable: boom",)
            ),
        ):
            summary = record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertTrue(summary.composition_requested)
        self.assertFalse(summary.composition_applied)
        self.assertEqual(summary.composed_selected_event_count, 0)
        self.assertTrue(
            any("unavailable" in diag for diag in summary.composition_diagnostics)
        )

        import sqlite3

        conn = sqlite3.connect(str(self.config.database_path))
        try:
            row = conn.execute(
                "SELECT input_tokens, output_tokens, cogs_usd, duration_seconds "
                "FROM execution_epochs WHERE epoch_id = ?",
                (_EPOCH_ID,),
            ).fetchone()
        finally:
            conn.close()
        # Original close payload (bare epoch, no tokens) persists unmerged —
        # never the undercounted/partial composition that a silent partial
        # read would have produced.
        input_tokens, output_tokens, cogs_usd, duration_seconds = row
        self.assertEqual(input_tokens, 0)
        self.assertEqual(output_tokens, 0)
        self.assertEqual(cogs_usd, 0.02)
        self.assertEqual(duration_seconds, 5.0)

    def test_malformed_journal_lines_are_skipped_not_fatal(self) -> None:
        record_tool_event(_event(input_tokens=10, output_tokens=4), self.config)
        journal_path = self.config.database_path.parent / "tool_events.jsonl"
        with journal_path.open("a", encoding="utf-8") as handle:
            handle.write("{not valid json\n")

        epoch = _bare_epoch()
        summary = record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertEqual(summary.composed_selected_event_count, 1)
        self.assertTrue(
            any("malformed line" in diag for diag in summary.composition_diagnostics)
        )

    def test_deterministic_retry_is_idempotent(self) -> None:
        record_tool_event(_event(input_tokens=10, output_tokens=4), self.config)
        epoch = _bare_epoch()
        first = record_epoch(epoch, self.config, compose_tool_events=True)
        second = record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertEqual(first.idempotency_outcome, "created")
        self.assertEqual(second.idempotency_outcome, "idempotent_replay")
        self.assertEqual(second.errors, [])

    def test_sink_failure_is_resilient_and_does_not_block_composition(self) -> None:
        from unittest import mock

        record_tool_event(_event(input_tokens=10, output_tokens=4), self.config)
        epoch = _bare_epoch()
        with mock.patch(
            "autoharness.telemetry.record.sqlite_sink.write_epoch",
            side_effect=RuntimeError("sink down"),
        ):
            summary = record_epoch(epoch, self.config, compose_tool_events=True)
        self.assertTrue(summary.composition_applied)
        self.assertEqual(summary.composed_selected_event_count, 1)
        self.assertTrue(any("sqlite sink failed" in err for err in summary.errors))

    def test_non_composed_record_calls_are_unaffected(self) -> None:
        epoch = _bare_epoch()
        summary = record_epoch(epoch, self.config)
        self.assertFalse(summary.composition_requested)
        self.assertFalse(summary.composition_applied)
        self.assertEqual(summary.composed_selected_event_count, 0)
        self.assertEqual(summary.composed_ignored_event_count, 0)
        self.assertEqual(summary.composition_diagnostics, [])
        # to_dict must still be well-formed with the new fields present but inert.
        as_dict = summary.to_dict()
        self.assertIn("composition_requested", as_dict)
        self.assertFalse(as_dict["composition_requested"])


if __name__ == "__main__":
    unittest.main()
