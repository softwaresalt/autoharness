"""159-S-shape replay tests for the closure-evidence temporal-ordering contract (171-S U1)."""

from __future__ import annotations

import copy
import json
import unittest
from datetime import datetime, timezone

from autoharness.gates import cascade_evidence
from test_cascade_evidence_contract import _FEATURE, _SHIPMENT, cascade_record

_MEMBER = "192.001-T"


def _record(captured: str = "2026-10-02T00:00:00Z", started: str = "2026-10-02T00:00:01Z",
            finished: str = "2026-10-02T00:00:02Z") -> dict:
    record = copy.deepcopy(cascade_record())
    record["pre_close"]["captured_at"] = captured
    record["invocation"]["started_at"] = started
    record["invocation"]["finished_at"] = finished
    return record


def _problems(record: dict) -> list[str]:
    return cascade_evidence.validate_evidence_record(
        record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path="cascade"
    )


def _utc(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _event(item_id: str, timestamp: str, event_type: str, delta: dict | None = None) -> str:
    return json.dumps({"timestamp": timestamp, "item_id": item_id, "event_type": event_type, "delta": delta or {}})


class InRecordOrderingTests(unittest.TestCase):
    def test_ordered_record_passes(self) -> None:
        self.assertEqual(_problems(_record()), [])

    def test_equal_start_and_finish_passes(self) -> None:
        self.assertEqual(_problems(_record(finished="2026-10-02T00:00:01Z")), [])

    def test_capture_after_invocation_start_fails(self) -> None:
        problems = _problems(_record(captured="2026-10-02T00:30:00Z"))
        self.assertTrue(any("record.pre_close.captured_at: must precede invocation.started_at" in p for p in problems), problems)

    def test_capture_equal_to_invocation_start_fails(self) -> None:
        problems = _problems(_record(captured="2026-10-02T00:00:01Z"))
        self.assertTrue(any("must precede invocation.started_at" in p for p in problems), problems)

    def test_finish_before_start_fails(self) -> None:
        problems = _problems(_record(finished="2026-10-02T00:00:00Z"))
        self.assertTrue(any("record.invocation.finished_at: must not precede started_at" in p for p in problems), problems)

    def test_unparseable_timestamp_fails(self) -> None:
        problems = _problems(_record(captured="yesterday"))
        self.assertTrue(any("record.pre_close.captured_at" in p and "RFC 3339" in p for p in problems), problems)

    def test_mixed_offsets_compare_as_instants(self) -> None:
        # 22:00:00-07:00 is 05:00:00Z, so by string order it would wrongly look earlier than the Z-suffixed start.
        ok = _record(captured="2026-10-01T22:00:00-07:00", started="2026-10-02T05:00:01Z", finished="2026-10-02T05:00:02Z")
        self.assertEqual(_problems(ok), [])
        bad = _record(captured="2026-10-01T22:00:02-07:00", started="2026-10-02T05:00:01Z", finished="2026-10-02T05:00:02Z")
        self.assertTrue(any("must precede invocation.started_at" in p for p in _problems(bad)))


class Rfc3339ParsingTests(unittest.TestCase):
    def test_out_of_range_offsets_and_years_are_not_instants(self) -> None:
        for value in ("2026-10-02T00:00:00+99:00", "2026-10-02T00:00:00+24:00", "2026-10-02T00:00:00+05:60",
                      "0001-01-01T00:00:00+05:00", "２０２６-10-02T00:00:00Z"):
            with self.subTest(value=value):
                self.assertIsNone(cascade_evidence.parse_rfc3339_instant(value))

    def test_out_of_range_offset_is_reported_not_raised(self) -> None:
        for value in ("2026-10-02T00:00:00+99:00", "0001-01-01T00:00:00+05:00"):
            problems = _problems(_record(captured=value))
            self.assertTrue(any("record.pre_close.captured_at" in p and "RFC 3339" in p for p in problems), problems)


class EngineWindowTests(unittest.TestCase):
    MERGE = _utc("2026-10-02T00:00:00Z")

    def _check(self, logs: dict[str, str | None], *, record: dict | None = None, merge=MERGE):
        record = record or _record(captured="2026-10-02T01:00:00Z", started="2026-10-02T01:00:05Z", finished="2026-10-02T01:10:00Z")

        def read_log(item_id: str) -> str | None:
            if item_id not in logs:
                return None
            return logs[item_id]

        return cascade_evidence.check_engine_window(record, merge_time=merge, read_log=read_log)

    def _full_logs(self, **overrides: str | None) -> dict[str, str | None]:
        logs: dict[str, str | None] = {_SHIPMENT: "", _MEMBER: "", _FEATURE: ""}
        logs.update(overrides)
        return logs

    def test_clean_logs_pass(self) -> None:
        errors, warnings = self._check(self._full_logs())
        self.assertEqual((errors, warnings), ([], []))

    def test_archived_inside_window_fails(self) -> None:
        log = _event(_MEMBER, "2026-10-01T17:30:00-07:00", "archived", {"archive_path": "x"})
        errors, _ = self._check(self._full_logs(**{_MEMBER: log}))
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(_MEMBER, errors[0])
        self.assertIn("archived", errors[0])

    def test_status_changed_to_shipped_inside_window_fails(self) -> None:
        log = _event(_MEMBER, "2026-10-02T00:30:00Z", "status_changed", {"from": "done", "to": "shipped"})
        errors, _ = self._check(self._full_logs(**{_MEMBER: log}))
        self.assertEqual(len(errors), 1, errors)

    def test_artifact_mutation_to_archived_inside_window_fails(self) -> None:
        log = _event(_MEMBER, "2026-10-02T00:30:00Z", "artifact_mutation", {"changes": {"status": "archived"}})
        errors, _ = self._check(self._full_logs(**{_MEMBER: log}))
        self.assertEqual(len(errors), 1, errors)

    def test_shipment_status_changed_inside_window_fails(self) -> None:
        log = _event(_SHIPMENT, "2026-10-02T00:30:00Z", "shipment_status_changed", {"status": "shipped"})
        errors, _ = self._check(self._full_logs(**{_SHIPMENT: log}))
        self.assertEqual(len(errors), 1, errors)

    def test_archive_before_merge_passes(self) -> None:
        log = _event(_MEMBER, "2026-10-01T23:59:59Z", "archived")
        self.assertEqual(self._check(self._full_logs(**{_MEMBER: log}))[0], [])

    def test_archive_at_capture_instant_is_ambiguous_for_whole_second_capture(self) -> None:
        # The capture writer records whole seconds: an archive inside that second is not provably later.
        log = _event(_MEMBER, "2026-10-02T01:00:00.100Z", "archived")
        errors, _ = self._check(self._full_logs(**{_MEMBER: log}))
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("ambiguous", errors[0])

    def test_beyond_microsecond_capture_with_provably_later_event_passes(self) -> None:
        record = _record(captured="2026-10-02T01:00:00.5000001Z", started="2026-10-02T01:00:05Z", finished="2026-10-02T01:10:00Z")
        for stamp in ("2026-10-02T01:00:00.6000000Z", "2026-10-02T01:00:01Z"):
            log = _event(_MEMBER, stamp, "archived")
            self.assertEqual(self._check(self._full_logs(**{_MEMBER: log}), record=record)[0], [], stamp)

    def test_sub_microsecond_finish_before_start_fails_in_record(self) -> None:
        record = _record(started="2026-10-02T01:00:01.5000009Z", finished="2026-10-02T01:00:01.5000001Z")
        self.assertTrue(any("must not precede started_at" in p for p in _problems(record)))
        ok = _record(started="2026-10-02T01:00:01.5000001Z", finished="2026-10-02T01:00:01.5000009Z")
        self.assertEqual(_problems(ok), [])

    def test_beyond_microsecond_capture_precision_is_ambiguous(self) -> None:
        record = _record(captured="2026-10-02T01:00:00.5000001Z", started="2026-10-02T01:00:05Z", finished="2026-10-02T01:10:00Z")
        log = _event(_MEMBER, "2026-10-02T01:00:00.5000000Z", "archived")
        errors, _ = self._check(self._full_logs(**{_MEMBER: log}), record=record)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("ambiguous", errors[0])

    def test_lowercase_separator_whole_second_capture_is_still_ambiguous(self) -> None:
        record = _record(captured="2026-10-02t01:00:00Z", started="2026-10-02T01:00:05Z", finished="2026-10-02T01:10:00Z")
        log = _event(_MEMBER, "2026-10-02T01:00:00.100Z", "archived")
        errors, _ = self._check(self._full_logs(**{_MEMBER: log}), record=record)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("ambiguous", errors[0])

    def test_unicode_line_separator_inside_json_string_is_not_a_line_break(self) -> None:
        line = json.dumps(
            {"timestamp": "2026-10-02T00:30:00Z", "item_id": _MEMBER, "event_type": "comment", "delta": {"text": "a\u0085b"}},
            ensure_ascii=False,
        )
        self.assertEqual(self._check(self._full_logs(**{_MEMBER: line + "\r\n"}))[0], [])

    def test_archive_in_same_second_after_subsecond_capture_passes(self) -> None:
        record = _record(captured="2026-10-02T01:00:00.500Z", started="2026-10-02T01:00:05Z", finished="2026-10-02T01:10:00Z")
        log = _event(_MEMBER, "2026-10-02T01:00:00.600Z", "archived")
        self.assertEqual(self._check(self._full_logs(**{_MEMBER: log}), record=record)[0], [])

    def test_archive_the_second_after_whole_second_capture_passes(self) -> None:
        log = _event(_MEMBER, "2026-10-02T01:00:01Z", "archived")
        self.assertEqual(self._check(self._full_logs(**{_MEMBER: log}))[0], [])

    def test_non_mutation_events_inside_window_pass(self) -> None:
        log = "\n".join(
            [
                _event(_MEMBER, "2026-10-02T00:20:00Z", "commit_tracked", {"commit_sha": "abc"}),
                _event(_MEMBER, "2026-10-02T00:21:00Z", "comment", {}),
                _event(_MEMBER, "2026-10-02T00:22:00Z", "status_changed", {"from": "active", "to": "done"}),
                _event(_MEMBER, "2026-10-02T00:23:00Z", "artifact_mutation", {"changes": {"status": "done"}}),
            ]
        )
        self.assertEqual(self._check(self._full_logs(**{_MEMBER: log}))[0], [])

    def test_unresolvable_merge_time_fails(self) -> None:
        errors, _ = self._check(self._full_logs(), merge=None)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("merge_commit_sha", errors[0])

    def test_missing_log_for_unarchived_member_fails(self) -> None:
        logs = self._full_logs()
        del logs[_MEMBER]
        errors, _ = self._check(logs)
        self.assertTrue(any(_MEMBER in e for e in errors), errors)

    def test_missing_log_for_archived_member_warns(self) -> None:
        record = _record(captured="2026-10-02T01:00:00Z", started="2026-10-02T01:00:05Z", finished="2026-10-02T01:10:00Z")
        record["pre_close"]["manifest_members"][0]["declared_status"] = "archived"
        logs = self._full_logs()
        del logs[_MEMBER]
        errors, warnings = self._check(logs, record=record)
        self.assertEqual(errors, [])
        self.assertTrue(any(_MEMBER in w for w in warnings), warnings)

    def test_missing_log_for_archive_resident_done_member_fails(self) -> None:
        record = _record(captured="2026-10-02T01:00:00Z", started="2026-10-02T01:00:05Z", finished="2026-10-02T01:10:00Z")
        record["pre_close"]["manifest_members"][0]["location"] = "archive"
        record["pre_close"]["manifest_members"][0]["declared_status"] = "done"
        logs = self._full_logs()
        del logs[_MEMBER]
        errors, _ = self._check(logs, record=record)
        self.assertTrue(any(_MEMBER in e for e in errors), errors)

    def test_malformed_recognized_mutation_payloads_fail_closed(self) -> None:
        for event_type, delta in (
            ("status_changed", None),
            ("status_changed", {"from": "active"}),
            ("artifact_mutation", None),
            ("artifact_mutation", {"changes": "nope"}),
            ("artifact_mutation", {"changes": {"status": 5}}),
            ("artifact_mutation", {"changes": {"status": None}}),
            (None, {}),
            ("", {}),
            (7, {}),
            ("shipment_status_changed", {}),
        ):
            line = json.dumps(
                {"timestamp": "2026-10-02T00:30:00Z", "item_id": _MEMBER, "event_type": event_type, "delta": delta}
            )
            errors, _ = self._check(self._full_logs(**{_MEMBER: line}))
            self.assertTrue(any("malformed mutation event" in e for e in errors), (event_type, delta, errors))

    def test_artifact_mutation_changing_only_non_status_fields_passes(self) -> None:
        line = _event(_MEMBER, "2026-10-02T00:30:00Z", "artifact_mutation", {"changes": {"title": "x"}})
        errors, _ = self._check(self._full_logs(**{_MEMBER: line}))
        self.assertEqual(errors, [])

    def test_malformed_log_line_fails(self) -> None:
        errors, _ = self._check(self._full_logs(**{_MEMBER: "{not json"}))
        self.assertTrue(any(_MEMBER in e and "malformed" in e for e in errors), errors)

    def test_unreadable_log_fails(self) -> None:
        record = _record(captured="2026-10-02T01:00:00Z", started="2026-10-02T01:00:05Z", finished="2026-10-02T01:10:00Z")

        def read_log(item_id: str) -> str | None:
            raise ValueError("fails containment")

        errors, _ = cascade_evidence.check_engine_window(record, merge_time=self.MERGE, read_log=read_log)
        self.assertTrue(errors)

    def test_replay_159s_shape_post_hoc_capture_fails(self) -> None:
        # Members were archived before the (post-hoc) capture: the window [M, C) holds the archive.
        record = _record(captured="2026-10-02T05:30:00Z", started="2026-10-02T05:30:10Z", finished="2026-10-02T05:40:00Z")
        log = _event(_MEMBER, "2026-10-02T05:14:25Z", "archived")
        errors, _ = cascade_evidence.check_engine_window(
            record,
            merge_time=_utc("2026-10-02T04:48:32Z"),
            read_log=lambda item_id: log if item_id == _MEMBER else "",
        )
        self.assertEqual(len(errors), 1, errors)
        # Rule 1 also fails when the capture follows the invocation start.
        late = _record(captured="2026-10-02T05:30:00Z", started="2026-10-02T05:25:00Z", finished="2026-10-02T05:40:00Z")
        self.assertTrue(any("must precede invocation.started_at" in p for p in _problems(late)))

    def test_replay_169s_shape_passing_counterpart(self) -> None:
        record = _record(captured="2026-10-02T05:02:03Z", started="2026-10-02T05:02:17Z", finished="2026-10-02T05:21:30Z")
        log = _event("161.003-T", "2026-10-01T22:14:25-07:00", "archived")
        errors, _ = cascade_evidence.check_engine_window(
            record,
            merge_time=_utc("2026-10-02T04:48:32Z"),
            read_log=lambda item_id: log if item_id == _MEMBER else "",
        )
        self.assertEqual(errors, [])
        self.assertEqual(_problems(record), [])

    def test_tagged_declared_status_does_not_raise(self) -> None:
        record = _record(captured="2026-10-02T01:00:00Z", started="2026-10-02T01:00:05Z", finished="2026-10-02T01:10:00Z")
        tagged = {"type": "missing", "value": None}
        record["pre_close"]["shipment_record"] = {"location": "queue", "declared_status": tagged}
        record["pre_close"]["manifest_members"][0]["declared_status"] = tagged
        errors, _ = cascade_evidence.check_engine_window(record, merge_time=self.MERGE, read_log=lambda item_id: "")
        self.assertEqual(errors, [])

    def test_missing_log_with_tagged_status_is_not_archived(self) -> None:
        record = _record(captured="2026-10-02T01:00:00Z", started="2026-10-02T01:00:05Z", finished="2026-10-02T01:10:00Z")
        record["pre_close"]["manifest_members"][0]["declared_status"] = {"type": "missing", "value": None}
        errors, _ = cascade_evidence.check_engine_window(
            record, merge_time=self.MERGE, read_log=lambda item_id: None if item_id == _MEMBER else ""
        )
        self.assertTrue(any(_MEMBER in e for e in errors), errors)

    def test_deeply_nested_log_line_is_malformed_not_a_crash(self) -> None:
        errors, _ = self._check(self._full_logs(**{_MEMBER: "[" * 100000}))
        self.assertTrue(any(_MEMBER in e and "malformed" in e for e in errors), errors)

    def test_close_mutation_with_missing_or_garbage_timestamp_fails_closed(self) -> None:
        for event in (
            json.dumps({"item_id": _MEMBER, "event_type": "archived", "delta": {}}),
            _event(_MEMBER, "garbage", "archived"),
        ):
            errors, _ = self._check(self._full_logs(**{_MEMBER: event}))
            self.assertTrue(any("malformed timestamp" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
