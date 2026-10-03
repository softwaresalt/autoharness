"""Linked-deliberation disposition snapshot codec tests (192.019-T, plan unit A1f).

Two table-driven scenarios (plan ``### A1f``):

1. round trips over plans built from ``LinkedDeliberationOutcome`` values and
   ``PLANNED_ARCHIVE``: ``to_record`` drops ``shipment_id`` and ``engine``
   (re-plan cycle-1 R14), ``from_record`` restores them, and
   ``x_to_record(x_from_record(r)) == r``;
2. malformed plan records raise ``CascadeEvidenceError``.

No fixture hard-codes a validated linked-deliberation set.
"""

from __future__ import annotations

import copy
import datetime
import unittest

from autoharness.gates.cascade_evidence import (
    CascadeEvidenceError,
    disposition_plan_from_record,
    disposition_plan_to_record,
    validate_evidence_record,
)
from autoharness.gates.shipment_closure import (
    PLANNED_ARCHIVE,
    DeliberationRecordSnapshot,
    DispositionReadFailure,
    LinkedDeliberationDisposition,
    LinkedDeliberationDispositionPlan,
    LinkedDeliberationOutcome,
    UnresolvedDeliberationReference,
    assess_cascade_engine_semantics,
)
from test_cascade_evidence_contract import safe_close_record

_SHIPMENT = "198-S"
_SHA = "e" * 64


def _engine(version: str):
    return assess_cascade_engine_semantics(version, probe_surface="cli", invocation_surface="cli")


def _snapshot(path: str = ".backlogit/queue/035-DL.md", status: object = "accepted") -> DeliberationRecordSnapshot:
    return DeliberationRecordSnapshot(path=path, declared_status=status, sha256=_SHA)


def _disposition(outcome, **overrides) -> LinkedDeliberationDisposition:
    fields = {
        "deliberation_id": "035-DL",
        "outcome": outcome,
        "reason_code": str(getattr(outcome, "value", outcome)),
        "link_kinds": ("source_deliberation_id", "references"),
        "linking_member_ids": ("192-F", "192.001-T"),
        "records": (_snapshot(),),
        "declared_status": "accepted",
    }
    fields.update(overrides)
    return LinkedDeliberationDisposition(**fields)


def _plan(dispositions, engine, **overrides) -> LinkedDeliberationDispositionPlan:
    fields = {
        "shipment_id": _SHIPMENT,
        "engine": engine,
        "dispositions": tuple(dispositions),
        "unresolved_references": (UnresolvedDeliberationReference(id="999-DL", reason_code="not_found"),),
        "read_failures": (),
        "planning_error": None,
    }
    fields.update(overrides)
    return LinkedDeliberationDispositionPlan(**fields)


class DispositionPlanRoundTripTests(unittest.TestCase):
    """Scenario 1: every outcome round-trips; shipment_id and engine are restored."""

    def test_round_trip_table(self) -> None:
        verified = _engine("1.11.0")
        unverified = _engine("1.10.1")
        outcome = LinkedDeliberationOutcome
        rows = [
            ("planned archive", [_disposition(PLANNED_ARCHIVE)], verified, {}),
            (
                "already-archived",
                [_disposition(outcome.ALREADY_ARCHIVED, declared_status="archived",
                              records=(_snapshot(".backlogit/archive/035-DL.md", "archived"),))],
                verified,
                {},
            ),
            (
                "retained_read_error with a path",
                [_disposition(outcome.RETAINED_READ_ERROR, reason_code="unreadable_file",
                              path=".backlogit/queue/035-DL.md", records=(), declared_status=None)],
                verified,
                {"read_failures": (DispositionReadFailure(path=".backlogit/queue/035-DL.md",
                                                          reason_code="unreadable_file"),)},
            ),
            (
                "retained_ambiguous with two records",
                [_disposition(outcome.RETAINED_AMBIGUOUS, declared_status=None,
                              records=(_snapshot(), _snapshot(".backlogit/archive/035-DL.md", "archived")))],
                verified,
                {},
            ),
            ("retained_engine_unverified", [_disposition(outcome.RETAINED_ENGINE_UNVERIFIED)], unverified, {}),
            (
                "retained_live_status",
                [_disposition(outcome.RETAINED_LIVE_STATUS, declared_status="active",
                              records=(_snapshot(status="active"),))],
                verified,
                {},
            ),
            (
                "retained_shared_reference",
                [_disposition(outcome.RETAINED_SHARED_REFERENCE, referrer_ids=("193-F", "STASH-1"))],
                verified,
                {},
            ),
            (
                "retained_description_mention with a date status",
                [_disposition(outcome.RETAINED_DESCRIPTION_MENTION, link_kinds=("description",),
                              declared_status=datetime.date(2026, 1, 1),
                              records=(_snapshot(status=datetime.date(2026, 1, 1)),))],
                verified,
                {},
            ),
            ("empty plan", [], verified, {"unresolved_references": ()}),
        ]
        for label, dispositions, engine, overrides in rows:
            with self.subTest(label):
                plan = _plan(dispositions, engine, **overrides)
                record = disposition_plan_to_record(plan)
                self.assertEqual(
                    set(record), {"dispositions", "unresolved_references", "read_failures", "planning_error"}
                )
                self.assertNotIn("shipment_id", record)
                self.assertNotIn("engine", record)
                decoded = disposition_plan_from_record(record, shipment_id=_SHIPMENT, engine=engine)
                self.assertEqual(decoded, plan)
                self.assertEqual(decoded.shipment_id, _SHIPMENT)
                self.assertIs(decoded.engine, engine)
                self.assertEqual(disposition_plan_to_record(decoded), record)
        # ID lists are sorted on encode; link_kinds keep the planner's reporting order.
        unsorted = _plan(
            [_disposition(PLANNED_ARCHIVE, linking_member_ids=("192.001-T", "192-F"), referrer_ids=("Z", "A"))],
            verified,
        )
        encoded = disposition_plan_to_record(unsorted)["dispositions"][0]
        self.assertEqual(encoded["linking_member_ids"], ["192-F", "192.001-T"])
        self.assertEqual(encoded["referrer_ids"], ["A", "Z"])
        self.assertEqual(encoded["link_kinds"], ["source_deliberation_id", "references"])
        self.assertEqual(encoded["records"][0]["declared_status"], "accepted")


class MalformedDispositionPlanTests(unittest.TestCase):
    """Scenario 2: a malformed plan record raises ``CascadeEvidenceError``."""

    def test_malformed_plan_table(self) -> None:
        engine = _engine("1.11.0")
        valid = disposition_plan_to_record(_plan([_disposition(PLANNED_ARCHIVE)], engine))

        def drop_dispositions(record: dict) -> None:
            del record["dispositions"]

        def unknown_field(record: dict) -> None:
            record["dispositions"][0]["verdict"] = "archive"

        def malformed_status(record: dict) -> None:
            record["dispositions"][0]["records"][0]["declared_status"] = {"type": "date", "value": "not-a-date"}

        rows = [
            ("missing dispositions key", drop_dispositions),
            ("unknown disposition field", unknown_field),
            ("malformed tagged declared_status in records[]", malformed_status),
        ]
        for label, mutation in rows:
            with self.subTest(label):
                record = copy.deepcopy(valid)
                mutation(record)
                with self.assertRaises(CascadeEvidenceError):
                    disposition_plan_from_record(record, shipment_id=_SHIPMENT, engine=engine)
                evidence = safe_close_record()
                evidence["pre_close"]["linked_deliberation_disposition"] = record
                self.assertNotEqual(
                    validate_evidence_record(
                        evidence, shipment_id=_SHIPMENT, feature_id="192-F", close_path="safe_close"
                    ),
                    [],
                    f"{label} was accepted",
                )


if __name__ == "__main__":
    unittest.main()
