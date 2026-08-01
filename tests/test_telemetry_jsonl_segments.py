"""Direct tests for the shared segmented JSONL primitives module (U2, 084.002-T).

``tests/test_telemetry_jsonl_sink.py`` already pins the execution-epoch sink's
end-to-end behavior after the extraction (unmodified, still green). This file
adds focused, module-level coverage of ``_jsonl_segments`` itself so the
primitives shared with the U3 ToolTelemetryEvent journal are directly tested
independent of any one sink's orchestration layer.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.telemetry import _jsonl_segments as segs


class CanonicalJsonAndDigestTests(unittest.TestCase):
    def test_canonical_json_is_key_order_independent(self) -> None:
        first = segs.canonical_json({"b": 1, "a": 2})
        second = segs.canonical_json({"a": 2, "b": 1})
        self.assertEqual(first, second)

    def test_digest_record_is_stable_for_equivalent_mappings(self) -> None:
        self.assertEqual(
            segs.digest_record({"a": 1, "b": 2}),
            segs.digest_record({"b": 2, "a": 1}),
        )

    def test_digest_record_differs_on_value_change(self) -> None:
        self.assertNotEqual(
            segs.digest_record({"a": 1}),
            segs.digest_record({"a": 2}),
        )


class SegmentEnumerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.jsonl_path = Path(self._tmp.name) / "events.jsonl"

    def test_sealed_segments_empty_when_parent_missing(self) -> None:
        missing = Path(self._tmp.name) / "missing_dir" / "events.jsonl"
        self.assertEqual(segs.sealed_segments(missing), [])

    def test_segment_read_paths_orders_sealed_then_active(self) -> None:
        self.jsonl_path.write_text("", encoding="utf-8")
        gen1 = segs.sealed_segment_path(self.jsonl_path, 1)
        gen2 = segs.sealed_segment_path(self.jsonl_path, 2)
        gen1.write_text("", encoding="utf-8")
        gen2.write_text("", encoding="utf-8")
        paths = segs.segment_read_paths(self.jsonl_path)
        self.assertEqual(paths, [gen1, gen2, self.jsonl_path])


class ScanKeyDigestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.jsonl_path = Path(self._tmp.name) / "events.jsonl"

    def _append(self, record: dict) -> None:
        line = segs.canonical_json(record) + "\n"
        segs.atomic_append_bytes(self.jsonl_path, line.encode("utf-8"))

    def test_scan_key_digest_finds_active_segment_match(self) -> None:
        self._append({"event_id": "abc", "value": 1})
        scan = segs.scan_key_digest(
            self.jsonl_path,
            "event_id",
            "abc",
            active_generation_fn=lambda _p: 1,
        )
        self.assertIsNotNone(scan.existing_digest)
        self.assertEqual(scan.existing_digest, segs.digest_record({"event_id": "abc", "value": 1}))

    def test_scan_key_digest_returns_none_when_absent(self) -> None:
        self._append({"event_id": "abc", "value": 1})
        scan = segs.scan_key_digest(
            self.jsonl_path,
            "event_id",
            "does-not-exist",
            active_generation_fn=lambda _p: 1,
        )
        self.assertIsNone(scan.existing_digest)

    def test_scan_single_file_skips_malformed_lines(self) -> None:
        self.jsonl_path.write_text(
            '{"event_id": "ok", "v": 1}\nnot-json\n{"event_id": "ok2", "v": 2}\n',
            encoding="utf-8",
        )
        digest, _offset = segs.scan_single_file(self.jsonl_path, "event_id", "ok2", 0)
        self.assertIsNotNone(digest)


class AppendRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.jsonl_path = Path(self._tmp.name) / "events.jsonl"

    def _scan(self, jsonl_path: Path, key_value: str, *, start_offset: int = 0) -> segs.JsonlPreflightScan:
        return segs.scan_key_digest(
            jsonl_path, "event_id", key_value,
            active_generation_fn=lambda _p: 1,
            start_offset=start_offset,
        )

    def _revalidate(self, jsonl_path: Path, key_value: str, scan: segs.JsonlPreflightScan) -> str | None:
        return segs.revalidate_preflight(
            jsonl_path, key_value, scan,
            active_generation_fn=lambda _p: 1,
            scan_fn=self._scan,
        )

    def _append(self, record: dict) -> segs.SinkWriteResult:
        return segs.append_record(
            jsonl_path=self.jsonl_path,
            key_field="event_id",
            key_value=record["event_id"],
            record=record,
            line_json=segs.canonical_json(record),
            preflight=None,
            scan_fn=self._scan,
            revalidate_fn=self._revalidate,
            rollover_fn=lambda _p: None,
        )

    def test_first_write_reports_created(self) -> None:
        result = self._append({"event_id": "e1", "v": 1})
        self.assertEqual(result.status, "created")

    def test_identical_replay_is_idempotent(self) -> None:
        self._append({"event_id": "e1", "v": 1})
        result = self._append({"event_id": "e1", "v": 1})
        self.assertEqual(result.status, "idempotent_replay")

    def test_conflicting_replay_raises_telemetry_conflict_error(self) -> None:
        self._append({"event_id": "e1", "v": 1})
        with self.assertRaises(segs.TelemetryConflictError):
            self._append({"event_id": "e1", "v": 2})


if __name__ == "__main__":
    unittest.main()
