"""Tests for the bounded ToolTelemetryEvent JSONL journal (U3, 084.003-T)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.telemetry import tool_event_jsonl
from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.tool_event import ToolTelemetryEvent


def _event(**overrides) -> ToolTelemetryEvent:
    kwargs = dict(
        tool_surface="cli",
        tool_name="pytest",
        operation="run_tests",
        status="success",
        sensitivity="internal",
        backlog_item_id="084.003-T",
    )
    kwargs.update(overrides)
    return ToolTelemetryEvent(**kwargs)


class ToolEventJsonlTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.jsonl_path = Path(self._tmp.name) / "tool_events.jsonl"


class DisabledModeTests(unittest.TestCase):
    def test_journal_path_for_config_is_none_when_disabled(self) -> None:
        config = TelemetryConfig()
        self.assertIsNone(tool_event_jsonl.journal_path_for_config(config))

    def test_record_tool_event_short_circuits_when_disabled(self) -> None:
        config = TelemetryConfig()
        summary = tool_event_jsonl.record_tool_event(_event(), config)
        self.assertFalse(summary.written)
        self.assertEqual(summary.status, "disabled")
        self.assertEqual(summary.errors, [])

    def test_read_events_reports_disabled_for_none_path(self) -> None:
        result = tool_event_jsonl.read_events(None, backlog_item_id="084.003-T")
        self.assertEqual(result.status, "disabled")
        self.assertEqual(result.events, ())


class WorkspaceContainmentTests(unittest.TestCase):
    def test_journal_path_derives_beside_database_path_no_new_config_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / ".autoharness" / "metrics" / "execution_epochs.db"
            config = TelemetryConfig(enabled=True, mode="sqlite", database_path=db_path)
            journal = tool_event_jsonl.journal_path_for_config(config)
            self.assertEqual(journal, db_path.parent / "tool_events.jsonl")
            # Stays within the same directory as the epoch database — no
            # separate containment surface is introduced.
            self.assertEqual(journal.parent, db_path.parent)


class AppendAndReplayTests(ToolEventJsonlTestCase):
    def test_first_write_is_created(self) -> None:
        result = tool_event_jsonl.append_event(_event(), self.jsonl_path)
        self.assertEqual(result.status, "created")

    def test_identical_replay_is_idempotent(self) -> None:
        event = _event()
        tool_event_jsonl.append_event(event, self.jsonl_path)
        result = tool_event_jsonl.append_event(event, self.jsonl_path)
        self.assertEqual(result.status, "idempotent_replay")
        lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)

    def test_conflicting_replay_is_rejected_with_diagnostic(self) -> None:
        event = _event()
        tool_event_jsonl.append_event(event, self.jsonl_path)
        conflicting = ToolTelemetryEvent(
            tool_surface="cli",
            tool_name="pytest",
            operation="run_tests",
            status="success",
            sensitivity="internal",
            backlog_item_id="084.003-T",
            event_id=event.event_id,
            input_tokens=5,
            metric_sources={"input_tokens": "host_reported"},
            metric_quality={"input_tokens": "observed"},
        )
        with self.assertRaises(tool_event_jsonl.TelemetryConflictError):
            tool_event_jsonl.append_event(conflicting, self.jsonl_path)

    def test_record_tool_event_reports_conflict_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "execution_epochs.db"
            config = TelemetryConfig(enabled=True, mode="sqlite", database_path=db_path)
            event = _event()
            tool_event_jsonl.record_tool_event(event, config)
            conflicting = ToolTelemetryEvent(
                tool_surface="cli",
                tool_name="pytest",
                operation="run_tests",
                status="failed",
                sensitivity="internal",
                backlog_item_id="084.003-T",
                event_id=event.event_id,
            )
            summary = tool_event_jsonl.record_tool_event(conflicting, config)
            self.assertEqual(summary.status, "conflict_rejected")
            self.assertTrue(summary.errors)


class NonAsciiDigestStabilityTests(ToolEventJsonlTestCase):
    def test_non_ascii_content_round_trips_and_replays_idempotently(self) -> None:
        event = _event(server_name="サーバー", artifact_refs=("docs/télémetrie.md",))
        first = tool_event_jsonl.append_event(event, self.jsonl_path)
        second = tool_event_jsonl.append_event(event, self.jsonl_path)
        self.assertEqual(first.status, "created")
        self.assertEqual(second.status, "idempotent_replay")
        self.assertEqual(first.payload_digest, second.payload_digest)
        result = tool_event_jsonl.read_events(self.jsonl_path, backlog_item_id="084.003-T")
        self.assertEqual(len(result.events), 1)
        self.assertEqual(result.events[0].server_name, "サーバー")
        self.assertEqual(result.events[0].artifact_refs, ("docs/télémetrie.md",))


class MalformedLineTests(ToolEventJsonlTestCase):
    def test_malformed_lines_are_skipped_not_crashed(self) -> None:
        good = _event(epoch_id="a" * 32)
        self.jsonl_path.write_text(
            "not-json\n" + tool_event_jsonl.json.dumps(good.to_dict()) + "\n{\"incomplete\":\n",
            encoding="utf-8",
        )
        result = tool_event_jsonl.read_events(self.jsonl_path, epoch_id="a" * 32)
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.events), 1)
        self.assertTrue(any("skipped malformed line" in diag for diag in result.diagnostics))


class CrossSegmentReadTests(ToolEventJsonlTestCase):
    def test_read_events_spans_sealed_and_active_segments(self) -> None:
        with mock.patch.object(tool_event_jsonl, "_MAX_SEGMENT_BYTES", 50):
            for index in range(6):
                tool_event_jsonl.append_event(
                    _event(epoch_id=f"{index:032d}"), self.jsonl_path
                )
        # With such a low threshold, several sealed segments should now exist
        # alongside the active one.
        sealed = [g for g, _p in tool_event_jsonl.sealed_segments(self.jsonl_path)]
        self.assertGreater(len(sealed), 0)

        results = [
            tool_event_jsonl.read_events(self.jsonl_path, epoch_id=f"{index:032d}")
            for index in range(6)
        ]
        for index, result in enumerate(results):
            self.assertEqual(result.status, "ok", f"expected event {index} to be found")
            self.assertEqual(len(result.events), 1)


class BoundedRotationRetentionTests(ToolEventJsonlTestCase):
    def test_rollover_and_retention_bounded(self) -> None:
        with mock.patch.object(tool_event_jsonl, "_MAX_SEGMENT_BYTES", 50), mock.patch.object(
            tool_event_jsonl, "_MAX_RETAINED_SEGMENTS", 2
        ):
            for index in range(10):
                tool_event_jsonl.append_event(
                    _event(epoch_id=f"{index:032d}"), self.jsonl_path
                )
        sealed = tool_event_jsonl.sealed_segments(self.jsonl_path)
        self.assertLessEqual(len(sealed), 2)


class SegmentIOFailureTests(ToolEventJsonlTestCase):
    """Review fix 3 (PR #273, PRRT_kwDORzpWpM6Vnq_P): a segment I/O failure must
    surface as an ``unavailable`` read status with no events returned, rather
    than silently reducing to a diagnostic while a partial/undercounted event
    set is still handed back to the caller (record.py's composition path)."""

    def test_segment_io_failure_returns_unavailable_status_with_no_events(self) -> None:
        good = _event(epoch_id="c" * 32)
        tool_event_jsonl.append_event(good, self.jsonl_path)
        with mock.patch("pathlib.Path.open", side_effect=OSError("permission denied")):
            result = tool_event_jsonl.read_events(self.jsonl_path, epoch_id="c" * 32)
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.events, ())
        self.assertTrue(any("unavailable" in diag for diag in result.diagnostics))

    def test_partial_segment_failure_still_reports_unavailable_not_partial_ok(self) -> None:
        # One sealed segment is unreadable while another segment/the active
        # segment is perfectly readable: the read must not silently return the
        # readable subset as if it were the complete correlated set.
        with mock.patch.object(tool_event_jsonl, "_MAX_SEGMENT_BYTES", 50):
            for index in range(6):
                tool_event_jsonl.append_event(_event(epoch_id=f"{index:032d}"), self.jsonl_path)
        sealed = [path for _generation, path in tool_event_jsonl.sealed_segments(self.jsonl_path)]
        self.assertGreater(len(sealed), 0)
        broken_segment = sealed[0]

        real_open = Path.open

        def _flaky_open(self, *args, **kwargs):
            if self == broken_segment:
                raise OSError("simulated unreadable segment")
            return real_open(self, *args, **kwargs)

        with mock.patch("pathlib.Path.open", new=_flaky_open):
            result = tool_event_jsonl.read_events(self.jsonl_path, epoch_id="000000000000000000000000000005")
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.events, ())


class ExactCorrelationSelectionTests(ToolEventJsonlTestCase):
    def test_epoch_id_event_never_matches_via_backlog_item_id(self) -> None:
        event = _event(epoch_id="b" * 32, backlog_item_id="084.003-T")
        tool_event_jsonl.append_event(event, self.jsonl_path)
        # Asking only by backlog_item_id must not select an epoch-correlated event.
        result = tool_event_jsonl.read_events(self.jsonl_path, backlog_item_id="084.003-T")
        self.assertEqual(result.events, ())

    def test_backlog_item_id_only_event_matches_fallback(self) -> None:
        event = _event(backlog_item_id="084.003-T")
        tool_event_jsonl.append_event(event, self.jsonl_path)
        result = tool_event_jsonl.read_events(self.jsonl_path, backlog_item_id="084.003-T")
        self.assertEqual(len(result.events), 1)


if __name__ == "__main__":
    unittest.main()
