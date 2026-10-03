"""declared_status and observation-entry codec tests (192.017-T, plan unit A1d).

Three table-driven scenarios (plan ``### A1d``):

1. the canonical ``declared_status`` tag table, including the YAML date case
   (re-plan cycle-1 R8);
2. malformed tagged objects, raised by the decoder and rejected by
   ``validate_evidence_record``;
3. observation-entry round trips (including a ``location: missing`` entry,
   re-plan cycle-2 C2-2) and byte-stable serialization.
"""

from __future__ import annotations

import datetime
import unittest

import yaml

from autoharness.gates import cascade_evidence
from autoharness.gates.cascade_evidence import (
    DECLARED_STATUS_MISSING,
    CascadeEvidenceError,
    ObservationEntry,
    OpaqueStatus,
    declared_status_from_record,
    declared_status_to_record,
    observation_entry_from_record,
    observation_entry_to_record,
    validate_evidence_record,
)
from test_cascade_evidence_contract import safe_close_record

_SHA = "d" * 64


class _Custom:
    pass


class DeclaredStatusTagTests(unittest.TestCase):
    """Scenario 1: every tag encodes and round-trips; a YAML date is not a string."""

    def test_declared_status_tag_table(self) -> None:
        yaml_date = yaml.safe_load("status: 2026-01-01")["status"]
        # (label, value, expected record)
        rows = [
            ("exact str", "done", "done"),
            ("missing key", DECLARED_STATUS_MISSING, {"type": "missing", "value": None}),
            ("null", None, {"type": "null", "value": None}),
            ("bool", True, {"type": "bool", "value": "true"}),
            ("int", 3, {"type": "int", "value": "3"}),
            ("float", 1.5, {"type": "float", "value": "1.5"}),
            ("YAML date", yaml_date, {"type": "date", "value": "2026-01-01"}),
            (
                "datetime",
                datetime.datetime(2026, 1, 1, 12, 30, tzinfo=datetime.timezone.utc),
                {"type": "datetime", "value": "2026-01-01T12:30:00+00:00"},
            ),
            (
                "list",
                ["done", 2],
                {"type": "list", "value": '["done",{"type":"int","value":"2"}]'},
            ),
            (
                "mapping",
                {"b": None, "a": "x"},
                {"type": "mapping", "value": '{"a":"x","b":{"type":"null","value":null}}'},
            ),
            ("other", _Custom(), {"type": "other", "value": "_Custom"}),
        ]
        for label, value, expected in rows:
            with self.subTest(label):
                encoded = declared_status_to_record(value)
                self.assertEqual(encoded, expected)
                decoded = declared_status_from_record(encoded)
                self.assertEqual(declared_status_to_record(decoded), encoded)
        self.assertIsInstance(yaml_date, datetime.date)
        self.assertNotEqual(declared_status_to_record(yaml_date), declared_status_to_record("2026-01-01"))
        self.assertEqual(declared_status_from_record({"type": "other", "value": "_Custom"}), OpaqueStatus("_Custom"))
        self.assertIs(declared_status_from_record({"type": "missing", "value": None}), DECLARED_STATUS_MISSING)
        # A bool is never an int, and a str subclass is never an exact str.
        self.assertEqual(declared_status_to_record(False)["type"], "bool")


class MalformedTagTests(unittest.TestCase):
    """Scenario 2: a malformed tagged object raises and rejects the record."""

    def test_malformed_tag_table(self) -> None:
        rows = [
            ("unknown tag", {"type": "enum", "value": "x"}),
            ("tagged object without value", {"type": "int"}),
            ("non-object non-string value", 7),
            ("JSON null", None),
            ("extra key", {"type": "null", "value": None, "extra": 1}),
            ("non-canonical int text", {"type": "int", "value": "007"}),
            ("unparseable date", {"type": "date", "value": "2026-13-45"}),
            ("missing tag with a value", {"type": "missing", "value": "x"}),
        ]
        for label, value in rows:
            with self.subTest(label):
                with self.assertRaises(CascadeEvidenceError):
                    declared_status_from_record(value)
                record = safe_close_record()
                record["pre_close"]["manifest_members"][0]["declared_status"] = value
                errors = validate_evidence_record(
                    record, shipment_id="198-S", feature_id="192-F", close_path="safe_close"
                )
                self.assertNotEqual(errors, [], f"{label} was accepted")
        record = safe_close_record()
        record["pre_close"]["observation_set"][0]["declared_status"] = {"type": "bogus", "value": None}
        self.assertNotEqual(
            validate_evidence_record(record, shipment_id="198-S", feature_id="192-F", close_path="safe_close"),
            [],
        )


class ObservationEntryTests(unittest.TestCase):
    """Scenario 3: observation entries round-trip and serialize byte-stably."""

    def test_observation_entry_table(self) -> None:
        queue_entry = ObservationEntry(
            id="192.001-T",
            path=".backlogit/queue/192.001-T.md",
            location="queue",
            sha256=_SHA,
            declared_status=datetime.date(2026, 1, 1),
        )
        missing_entry = ObservationEntry(
            id="192.099-T", path=None, location="missing", sha256=None, declared_status=None
        )
        rows = [
            (
                "queue entry",
                queue_entry,
                {
                    "id": "192.001-T",
                    "path": ".backlogit/queue/192.001-T.md",
                    "location": "queue",
                    "sha256": _SHA,
                    "declared_status": {"type": "date", "value": "2026-01-01"},
                },
            ),
            (
                "missing entry",
                missing_entry,
                {"id": "192.099-T", "path": None, "location": "missing", "sha256": None, "declared_status": None},
            ),
        ]
        for label, entry, expected in rows:
            with self.subTest(label):
                encoded = observation_entry_to_record(entry)
                self.assertEqual(encoded, expected)
                self.assertEqual(observation_entry_from_record(encoded), entry)
                self.assertEqual(observation_entry_to_record(observation_entry_from_record(encoded)), encoded)
        for label, bad in (
            ("missing entry with a path", dict(rows[1][2], path=".backlogit/queue/x.md")),
            ("unknown location", dict(rows[0][2], location="elsewhere")),
            ("unknown key", dict(rows[0][2], extra=True)),
            ("missing key", {k: v for k, v in rows[0][2].items() if k != "sha256"}),
        ):
            with self.subTest(label):
                with self.assertRaises(CascadeEvidenceError):
                    observation_entry_from_record(bad)

        record = safe_close_record()
        record["pre_close"]["observation_set"] = [observation_entry_to_record(e) for e in (queue_entry, missing_entry)]
        self.assertEqual(
            validate_evidence_record(record, shipment_id="198-S", feature_id="192-F", close_path="safe_close"),
            [],
        )
        first = cascade_evidence._serialize_evidence_record(record)
        second = cascade_evidence._serialize_evidence_record(
            cascade_evidence.json.loads(first)  # re-serialize the parsed form
        )
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))
        self.assertTrue(first.endswith("\n") and not first.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
