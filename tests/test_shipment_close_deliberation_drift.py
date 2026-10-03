"""Linked-deliberation drift evaluator tests (192.014-T, plan unit A3c).

Four scenarios (plan ``### A3c``):

1. flat-contract pass: a live linked deliberation left in ``queue/`` and
   unchanged yields no drift (the 190-S halt shape is a non-failure);
2. ``archived`` drift: a disposition-set deliberation in ``archived_ids``;
3. ``modified`` drift: a changed record yields ``modified`` and
   ``disposition_byte_identical: false``;
4. the ``snapshot_drift`` / ``planning_error`` table, including the
   settled-outcome-only comparison (re-plan cycle-2 C2-3).

Every comparison is between A1f ``disposition_plan_to_record`` encodings
(re-plan cycle-1 R8).
"""

from __future__ import annotations

import dataclasses
import unittest

from autoharness.gates.cascade_evidence import (
    declared_status_to_record,
    disposition_plan_to_record,
)
from autoharness.gates.shipment_closure import (
    PLANNED_ARCHIVE,
    ClosePath,
    ClosePathDecision,
    DeliberationRecordSnapshot,
    DispositionReadFailure,
    LinkedDeliberationDisposition,
    LinkedDeliberationDispositionPlan,
    LinkedDeliberationOutcome,
    UnresolvedDeliberationReference,
)
from autoharness.shipment_close.postclose import (
    DRIFT_ARCHIVED,
    DRIFT_MODIFIED,
    DRIFT_PLANNING_ERROR,
    DRIFT_SNAPSHOT,
    DriftEntry,
    ParsedResult,
    PostCloseReread,
    RereadRecord,
    disposition_byte_identical,
    evaluate_linked_deliberation_drift,
    evaluate_postconditions,
)
from autoharness.shipment_close.preclose import PreCloseSnapshot

_SHIPMENT = "910-S"
_FEATURE = "910-F"
_TASK = "910.001-T"
_DL = "911-DL"
_SHA_FEATURE = "a" * 64
_SHA_TASK = "b" * 64
_SHA_SHIPMENT = "c" * 64
_SHA_DL = "d" * 64


def _disposition(
    outcome: object = LinkedDeliberationOutcome.RETAINED_LIVE_STATUS,
    *,
    deliberation_id: str = _DL,
    sha: str = _SHA_DL,
    path: str | None = None,
    reason_code: str | None = None,
    link_kinds: tuple[str, ...] = ("source_deliberation_id",),
    record_path: str | None = None,
    referrer_ids: tuple[str, ...] = (),
) -> LinkedDeliberationDisposition:
    return LinkedDeliberationDisposition(
        deliberation_id=deliberation_id,
        outcome=outcome,
        reason_code=reason_code if reason_code is not None else str(getattr(outcome, "value", outcome)),
        link_kinds=link_kinds,
        linking_member_ids=(_TASK,),
        records=(
            DeliberationRecordSnapshot(
                path=record_path or f".backlogit/queue/{deliberation_id}.md", declared_status="active", sha256=sha
            ),
        ),
        declared_status="active",
        referrer_ids=referrer_ids,
        path=path,
    )


def _plan(*dispositions: LinkedDeliberationDisposition, **kwargs: object) -> LinkedDeliberationDispositionPlan:
    return LinkedDeliberationDispositionPlan(
        shipment_id=_SHIPMENT, engine=None, dispositions=tuple(dispositions), unresolved_references=(), **kwargs
    )


def _snapshot(plan: LinkedDeliberationDispositionPlan) -> PreCloseSnapshot:
    pre_close = {
        "classifier_verdict": "CASCADE",
        "qualifying_feature_ids": [_FEATURE],
        "shipment_record": {"location": "queue", "sha256": _SHA_SHIPMENT, "declared_status": "active"},
        "manifest_members": [
            {
                "id": _FEATURE,
                "artifact_type": "feature",
                "location": "queue",
                "sha256": _SHA_FEATURE,
                "declared_status": declared_status_to_record("done"),
                "parent_id": None,
            },
            {
                "id": _TASK,
                "artifact_type": "task",
                "location": "queue",
                "sha256": _SHA_TASK,
                "declared_status": declared_status_to_record("done"),
                "parent_id": _FEATURE,
            },
        ],
        "out_of_manifest_descendants": [],
        "linked_deliberation_disposition": disposition_plan_to_record(plan),
    }
    classifier = ClosePathDecision(
        close_path=ClosePath.CASCADE,
        reason="fixture",
        qualifying_feature_ids=(_FEATURE,),
        out_of_manifest_descendant_ids=(),
    )
    return PreCloseSnapshot(
        shipment_id=_SHIPMENT,
        feature_id=_FEATURE,
        backlog_dir=None,  # type: ignore[arg-type]
        manifest_ids=(_FEATURE, _TASK),
        classifier=classifier,
        engine=None,  # type: ignore[arg-type]
        invocation_surface="cli",
        selection=(ClosePath.CASCADE, "fixture"),
        disposition=plan,
        tool={},
        pre_close=pre_close,
    )


def _kinds(entries: tuple[DriftEntry, ...]) -> list[str]:
    return [entry.kind for entry in entries]


def _passing_postconditions(snapshot: PreCloseSnapshot, recollected: LinkedDeliberationDispositionPlan, drift):
    archived = (_FEATURE, _TASK, _SHIPMENT)
    parsed = ParsedResult(
        shipment_id=_SHIPMENT,
        shipment_status="shipped",
        archived_ids=archived,
        returned_ids=(),
        commit_sha=None,
    )
    reread = PostCloseReread(
        shipment=RereadRecord("archive", "e" * 64, "archived", None, archived_status="shipped"),
        records={
            _FEATURE: RereadRecord("archive", "f" * 64, "archived", None),
            _TASK: RereadRecord("archive", "1" * 64, "archived", _FEATURE),
        },
        disposition=recollected,
    )
    return evaluate_postconditions(
        snapshot,
        parsed,
        reread,
        linked_deliberation_drift=drift,
        disposition_byte_identical=disposition_byte_identical(drift),
    )


class FlatContractPassTests(unittest.TestCase):
    """Scenario 1: a live linked deliberation left unchanged is no drift (190-S shape)."""

    def test_unchanged_live_deliberation_is_not_drift(self) -> None:
        plan = _plan(_disposition())
        snapshot = _snapshot(plan)
        drift = evaluate_linked_deliberation_drift(snapshot, (_FEATURE, _TASK, _SHIPMENT), plan)
        self.assertEqual(drift, ())
        self.assertTrue(disposition_byte_identical(drift))
        result = _passing_postconditions(snapshot, plan, drift)
        self.assertEqual(result.postcondition_verdict, "pass", result.failures)
        self.assertEqual(result.to_record()["linked_deliberation_drift"], [])

    def test_retained_outcomes_alone_are_not_drift(self) -> None:
        for outcome in (
            LinkedDeliberationOutcome.RETAINED_ENGINE_UNVERIFIED,
            LinkedDeliberationOutcome.RETAINED_DESCRIPTION_MENTION,
            LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE,
        ):
            with self.subTest(outcome=outcome):
                plan = _plan(_disposition(outcome))
                self.assertEqual(evaluate_linked_deliberation_drift(_snapshot(plan), (), plan), ())

    def test_no_dispositions_is_byte_identical(self) -> None:
        plan = _plan()
        drift = evaluate_linked_deliberation_drift(_snapshot(plan), (_SHIPMENT,), plan)
        self.assertEqual(drift, ())
        self.assertTrue(disposition_byte_identical(drift))


class ArchivedDriftTests(unittest.TestCase):
    """Scenario 2: a disposition-set deliberation in archived_ids is ``archived`` drift."""

    def test_archived_disposition_member_is_drift(self) -> None:
        plan = _plan(_disposition())
        snapshot = _snapshot(plan)
        drift = evaluate_linked_deliberation_drift(snapshot, (_FEATURE, _TASK, _SHIPMENT, _DL), plan)
        self.assertIn(DRIFT_ARCHIVED, _kinds(drift))
        entry = next(entry for entry in drift if entry.kind == DRIFT_ARCHIVED)
        self.assertEqual(entry.deliberation_id, _DL)
        self.assertEqual(set(entry.to_record()), {"deliberation_id", "kind", "detail"})
        result = _passing_postconditions(snapshot, plan, drift)
        self.assertEqual(result.postcondition_verdict, "fail")
        self.assertTrue(any(f.startswith("linked_deliberation_drift") for f in result.failures))


class ModifiedDriftTests(unittest.TestCase):
    """Scenario 3: a modified or moved record is ``modified`` drift; byte identity fails."""

    def test_modified_and_moved_records(self) -> None:
        plan = _plan(_disposition())
        snapshot = _snapshot(plan)
        cases = {
            "sha changed": _plan(_disposition(sha="9" * 64)),
            "path moved": _plan(_disposition(record_path=f".backlogit/archive/{_DL}.md")),
            "record vanished": _plan(),
        }
        for label, recollected in cases.items():
            with self.subTest(label):
                drift = evaluate_linked_deliberation_drift(snapshot, (), recollected)
                self.assertIn(DRIFT_MODIFIED, _kinds(drift))
                self.assertFalse(disposition_byte_identical(drift))
                result = _passing_postconditions(snapshot, recollected, drift)
                self.assertEqual(result.postcondition_verdict, "fail")
                self.assertFalse(result.to_record()["disposition_byte_identical"])


class SnapshotDriftTableTests(unittest.TestCase):
    """Scenario 4: snapshot_drift and planning_error rows fail; a non-settled outcome swap does not."""

    def test_drift_rows(self) -> None:
        read_error = _disposition(
            LinkedDeliberationOutcome.RETAINED_READ_ERROR,
            reason_code="unreadable_file",
            path=f".backlogit/queue/{_DL}.md",
        )
        failure = DispositionReadFailure(path=".backlogit/queue/x.md", reason_code="unreadable_file")
        rows = [
            ("new link kind", _plan(_disposition()), _plan(_disposition(link_kinds=("source_deliberation_id", "references"))), DRIFT_SNAPSHOT),
            ("settled outcome changed", _plan(_disposition()), _plan(_disposition(LinkedDeliberationOutcome.RETAINED_AMBIGUOUS)), DRIFT_SNAPSHOT),
            ("settled outcome left", _plan(_disposition(LinkedDeliberationOutcome.ALREADY_ARCHIVED)), _plan(_disposition()), DRIFT_SNAPSHOT),
            ("read_error path changed", _plan(read_error), _plan(dataclasses.replace(read_error, path=".backlogit/queue/y.md")), DRIFT_SNAPSHOT),
            ("read_error reason changed", _plan(read_error), _plan(dataclasses.replace(read_error, reason_code="malformed_frontmatter")), DRIFT_SNAPSHOT),
            ("read_failures changed", _plan(_disposition()), _plan(_disposition(), read_failures=(failure,)), DRIFT_SNAPSHOT),
            (
                "unresolved references changed",
                _plan(_disposition()),
                dataclasses.replace(
                    _plan(_disposition()),
                    unresolved_references=(UnresolvedDeliberationReference(id="999-DL", reason_code="not_found"),),
                ),
                DRIFT_SNAPSHOT,
            ),
            ("new deliberation", _plan(_disposition()), _plan(_disposition(), _disposition(deliberation_id="912-DL")), DRIFT_SNAPSHOT),
            ("planning_error", _plan(_disposition()), _plan(_disposition(), planning_error="boom"), DRIFT_PLANNING_ERROR),
            ("not re-collected", _plan(_disposition()), None, DRIFT_PLANNING_ERROR),
        ]
        for label, pre, post, kind in rows:
            with self.subTest(label):
                snapshot = _snapshot(pre)
                drift = evaluate_linked_deliberation_drift(snapshot, (), post)
                self.assertIn(kind, _kinds(drift), drift)
                result = _passing_postconditions(snapshot, post, drift)
                self.assertEqual(result.postcondition_verdict, "fail")

    def test_planned_archive_to_shared_reference_is_not_drift(self) -> None:
        pre = _plan(_disposition(PLANNED_ARCHIVE, reason_code="archive"))
        post = _plan(_disposition(LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE, referrer_ids=("950-F",)))
        snapshot = _snapshot(pre)
        drift = evaluate_linked_deliberation_drift(snapshot, (_FEATURE, _TASK, _SHIPMENT), post)
        self.assertEqual(drift, ())
        self.assertEqual(_passing_postconditions(snapshot, post, drift).postcondition_verdict, "pass")

    def test_never_raises_on_unencodable_recollection(self) -> None:
        plan = _plan(_disposition())
        bad = _plan(_disposition(sha="not-a-sha"))
        drift = evaluate_linked_deliberation_drift(_snapshot(plan), (), bad)
        self.assertIn(DRIFT_PLANNING_ERROR, _kinds(drift))
        self.assertFalse(disposition_byte_identical(drift))


if __name__ == "__main__":
    unittest.main()
