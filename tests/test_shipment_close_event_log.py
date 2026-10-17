"""Event-log provenance reader tests (211.002-T, plan unit T1; hardening H1/H9)."""

from __future__ import annotations

import datetime
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autoharness.shipment_close.event_log import (
    MAX_LOG_BYTES,
    EventLogError,
    attribute_archived_footprint,
    read_cascade_events,
)
from cascade_close_test_support import make_dir_link

_FIXTURES = Path(__file__).parent / "fixtures" / "cascade_close_event_logs"
_UTC = datetime.timezone.utc


def _instant(text: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(text)


class _TempBacklog(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.backlog = Path(self._tmp.name)

    def copy_fixture(self, name: str) -> Path:
        shutil.copytree(_FIXTURES / name / "logs", self.backlog / "logs")
        return self.backlog

    def event(self, **overrides: object) -> str:
        base = {
            "timestamp": "2026-10-16T08:05:17.3838236-07:00",
            "actor": "backlogit",
            "item_id": "X-S",
            "event_type": "comment",
            "delta": {},
        }
        base.update(overrides)
        return json.dumps(base)

    def write_log(self, item_id: str, *lines: str) -> None:
        logs = self.backlog / "logs"
        logs.mkdir(exist_ok=True)
        (logs / f"{item_id}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


class CleanCascadeFixtureTest(_TempBacklog):
    def test_shipped_event_is_operation_correlated_and_scope_replayed(self) -> None:
        self.copy_fixture("shipment_213_s_clean")
        events = read_cascade_events(self.backlog, "213-S", _instant("2026-10-16T08:03:00-07:00"))
        self.assertEqual(events.scope_item_ids, ("206-F", "206.001-T", "206.002-T", "206.003-T", "206.004-T", "206.005-T"))
        self.assertEqual(len(events.shipped_events), 1)
        shipped = events.shipped_events[0]
        self.assertEqual(shipped.operation, "213-S")
        self.assertEqual(shipped.instant, _instant("2026-10-16T15:05:17.383823+00:00"))
        self.assertEqual(events.missing_item_logs, ())

    def test_since_excludes_earlier_events(self) -> None:
        self.copy_fixture("shipment_213_s_clean")
        events = read_cascade_events(self.backlog, "213-S", _instant("2026-10-16T08:05:18-07:00"))
        self.assertEqual(events.shipped_events, ())

    def test_offset_bearing_since_is_compared_as_utc_instants(self) -> None:
        self.copy_fixture("shipment_213_s_clean")
        same = read_cascade_events(self.backlog, "213-S", _instant("2026-10-16T15:05:17.4+00:00"))
        self.assertEqual(same.shipped_events, ())
        before = read_cascade_events(self.backlog, "213-S", _instant("2026-10-16T15:05:17.3+00:00"))
        self.assertEqual(len(before.shipped_events), 1)

    def test_feature_release_event_carries_the_cascade_operation(self) -> None:
        self.copy_fixture("shipment_213_s_clean")
        events = read_cascade_events(self.backlog, "213-S", _instant("2026-10-16T08:03:00-07:00"))
        self.assertEqual([e.item_id for e in events.released_events], ["206-F"])

    def test_archived_events_in_clean_run_are_uncorrelated(self) -> None:
        self.copy_fixture("shipment_213_s_clean")
        events = read_cascade_events(self.backlog, "213-S", _instant("2026-10-16T08:03:00-07:00"))
        self.assertEqual({e.item_id for e in events.archived_events}, set(events.scope_item_ids) | {"213-S"})
        self.assertTrue(all(e.operation is None for e in events.archived_events))
        self.assertTrue(all(set(e.delta) == {"archive_path"} for e in events.archived_events))
        result = attribute_archived_footprint(events, events.scope_item_ids)
        self.assertFalse(result.attributed)
        self.assertIn("no cascade operation correlation", result.reason)
        self.assertEqual(set(result.uncorrelated_ids), set(events.scope_item_ids))


class IncidentFixtureTest(_TempBacklog):
    def test_214_s_shipped_event_exists_but_archival_is_not_attributable(self) -> None:
        self.copy_fixture("shipment_214_s_incident")
        events = read_cascade_events(self.backlog, "214-S", _instant("2026-10-16T10:43:00-07:00"))
        self.assertEqual(len(events.shipped_events), 1)
        self.assertEqual(events.shipped_events[0].operation, "214-S")
        # 207.001-T was archived twice, about an hour after the shipped event.
        counts = {}
        for event in events.archived_events:
            counts[event.item_id] = counts.get(event.item_id, 0) + 1
        self.assertEqual(counts["207.001-T"], 2)
        result = attribute_archived_footprint(events, [*events.scope_item_ids, "214-S"])
        self.assertFalse(result.attributed)

    def test_214_s_archives_outside_a_window_ending_shortly_after_shipped_are_missing(self) -> None:
        self.copy_fixture("shipment_214_s_incident")
        events = read_cascade_events(self.backlog, "214-S", _instant("2026-10-16T10:43:00-07:00"))
        result = attribute_archived_footprint(
            events, events.scope_item_ids, window_end=_instant("2026-10-16T10:50:00-07:00")
        )
        self.assertFalse(result.attributed)
        self.assertEqual(set(result.missing_ids), set(events.scope_item_ids))


class AttributionPredicateTest(_TempBacklog):
    def _scenario(self, *, archived_delta: dict, extra_item_event: str | None = None) -> None:
        self.write_log(
            "9-S",
            self.event(item_id="9-S", event_type="shipment_created", delta={"items": ["9.001-T"]}),
            self.event(
                item_id="9-S",
                event_type="shipment_status_changed",
                timestamp="2026-10-16T01:00:00+00:00",
                delta={"_shipment_operation": "9-S", "status": "shipped"},
            ),
        )
        lines = [
            self.event(
                item_id="9.001-T", event_type="archived", timestamp="2026-10-16T01:01:00+00:00", delta=archived_delta
            )
        ]
        if extra_item_event:
            lines.append(extra_item_event)
        self.write_log("9.001-T", *lines)

    def test_attributed_only_when_the_archived_event_itself_names_the_cascade(self) -> None:
        self._scenario(archived_delta={"archive_path": "a.md", "_shipment_operation": "9-S"})
        events = read_cascade_events(self.backlog, "9-S", _instant("2026-10-16T00:00:00+00:00"))
        self.assertTrue(attribute_archived_footprint(events, ["9.001-T"]).attributed)

    def test_a_wrong_operation_is_not_attribution(self) -> None:
        self._scenario(archived_delta={"archive_path": "a.md", "_shipment_operation": "8-S"})
        events = read_cascade_events(self.backlog, "9-S", _instant("2026-10-16T00:00:00+00:00"))
        self.assertFalse(attribute_archived_footprint(events, ["9.001-T"]).attributed)

    def test_foreign_actor_event_in_window_blocks_attribution(self) -> None:
        foreign = self.event(
            item_id="9.001-T", actor="human", event_type="comment", timestamp="2026-10-16T01:00:30+00:00"
        )
        self._scenario(
            archived_delta={"archive_path": "a.md", "_shipment_operation": "9-S"}, extra_item_event=foreign
        )
        events = read_cascade_events(self.backlog, "9-S", _instant("2026-10-16T00:00:00+00:00"))
        result = attribute_archived_footprint(events, ["9.001-T"])
        self.assertFalse(result.attributed)
        self.assertEqual(result.foreign_event_item_ids, ("9.001-T",))

    def test_foreign_actor_event_before_the_window_is_ignored(self) -> None:
        foreign = self.event(
            item_id="9.001-T", actor="human", event_type="comment", timestamp="2026-10-15T01:00:30+00:00"
        )
        self._scenario(
            archived_delta={"archive_path": "a.md", "_shipment_operation": "9-S"}, extra_item_event=foreign
        )
        events = read_cascade_events(self.backlog, "9-S", _instant("2026-10-16T00:00:00+00:00"))
        self.assertTrue(attribute_archived_footprint(events, ["9.001-T"]).attributed)

    def test_missing_archived_event_blocks_attribution(self) -> None:
        self._scenario(archived_delta={"archive_path": "a.md", "_shipment_operation": "9-S"})
        events = read_cascade_events(self.backlog, "9-S", _instant("2026-10-16T00:00:00+00:00"))
        result = attribute_archived_footprint(events, ["9.001-T", "9.002-T"])
        self.assertFalse(result.attributed)
        self.assertEqual(result.missing_ids, ("9.002-T",))

    def test_missing_item_log_is_reported_not_empty(self) -> None:
        self.write_log(
            "9-S", self.event(item_id="9-S", event_type="shipment_created", delta={"items": ["9.001-T"]})
        )
        events = read_cascade_events(self.backlog, "9-S", _instant("2026-10-16T00:00:00+00:00"))
        self.assertEqual(events.missing_item_logs, ("9.001-T",))


class FailClosedReaderTest(_TempBacklog):
    SINCE = _instant("2026-10-16T00:00:00+00:00")

    def _shipment(self, *extra: str) -> None:
        self.write_log(
            "9-S",
            self.event(item_id="9-S", event_type="shipment_created", delta={"items": []}),
            *extra,
        )

    def test_missing_logs_directory_or_shipment_log(self) -> None:
        with self.assertRaises(EventLogError):
            read_cascade_events(self.backlog, "9-S", self.SINCE)
        (self.backlog / "logs").mkdir()
        with self.assertRaises(EventLogError):
            read_cascade_events(self.backlog, "9-S", self.SINCE)

    def test_malformed_lines_and_shapes_are_errors(self) -> None:
        cases = {
            "invalid json": "{not json",
            "not an object": "[1]",
            "missing actor": json.dumps({"timestamp": "2026-10-16T00:00:00Z", "item_id": "9-S", "event_type": "x"}),
            "non-string type": self.event(item_id="9-S", event_type=5),
            "delta not object": self.event(item_id="9-S", delta=[]),
            "naive timestamp": self.event(item_id="9-S", timestamp="2026-10-16T00:00:00"),
            "wrong item id": self.event(item_id="8-S"),
        }
        for name, line in cases.items():
            with self.subTest(name):
                self._shipment(line)
                with self.assertRaises(EventLogError):
                    read_cascade_events(self.backlog, "9-S", self.SINCE)

    def test_malformed_manifest_event_is_an_error(self) -> None:
        self.write_log("9-S", self.event(item_id="9-S", event_type="shipment_created", delta={"items": "x"}))
        with self.assertRaises(EventLogError):
            read_cascade_events(self.backlog, "9-S", self.SINCE)

    def test_naive_since_is_refused(self) -> None:
        self._shipment()
        with self.assertRaises(EventLogError):
            read_cascade_events(self.backlog, "9-S", datetime.datetime(2026, 10, 16))

    def test_oversize_and_non_utf8_logs_are_refused(self) -> None:
        self._shipment()
        path = self.backlog / "logs" / "9-S.jsonl"
        path.write_bytes(b"x" * (MAX_LOG_BYTES + 1))
        with self.assertRaises(EventLogError):
            read_cascade_events(self.backlog, "9-S", self.SINCE)
        path.write_bytes(b"\xff\xfe\n")
        with self.assertRaises(EventLogError):
            read_cascade_events(self.backlog, "9-S", self.SINCE)

    def test_linked_logs_directory_is_refused(self) -> None:
        real = self.backlog / "real"
        real.mkdir()
        (real / "9-S.jsonl").write_text(
            self.event(item_id="9-S", event_type="shipment_created", delta={"items": []}) + "\n", encoding="utf-8"
        )
        reason = make_dir_link(self.backlog / "logs", real)
        if reason:
            self.skipTest(reason)
        with self.assertRaises(EventLogError):
            read_cascade_events(self.backlog, "9-S", self.SINCE)

    def test_blank_lines_are_tolerated(self) -> None:
        self.write_log("9-S", "", self.event(item_id="9-S", event_type="shipment_created", delta={"items": []}), "")
        events = read_cascade_events(self.backlog, "9-S", self.SINCE)
        self.assertEqual(events.scope_item_ids, ())

    def test_item_removal_shrinks_scope(self) -> None:
        self.write_log(
            "9-S",
            self.event(
                item_id="9-S",
                event_type="shipment_created",
                timestamp="2026-10-15T00:00:00+00:00",
                delta={"items": ["a", "b"]},
            ),
            self.event(
                item_id="9-S",
                event_type="shipment_item_removed",
                timestamp="2026-10-15T01:00:00+00:00",
                delta={"removed_item": "a"},
            ),
        )
        self.assertEqual(read_cascade_events(self.backlog, "9-S", self.SINCE).scope_item_ids, ("b",))


if __name__ == "__main__":
    unittest.main()
