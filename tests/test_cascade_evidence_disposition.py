"""Disposition and set-term rule tests for CASCADE close evidence (192.011-T, plan unit A1c).

Four table-driven scenarios (plan ``### A1c``):

1. outcome and engine/outcome consistency, both ways (re-plan cycle-1 R13);
2. planner state (a missing snapshot, a non-null ``planning_error``);
3. set terms (no disposition-set deliberation in ``allowed_ids`` /
   ``required_ids``; D2, H10 carve-out);
4. disposition-set deliberations in the safe-close observation set (re-plan
   cycle-1 R2, cycle-2 C2-1).

Fixtures build dispositions from ``LinkedDeliberationOutcome`` values and
``PLANNED_ARCHIVE`` and never hard-code a linked deliberation in either flat
set.
"""

from __future__ import annotations

import unittest

from autoharness.gates.cascade_evidence import validate_evidence_record
from autoharness.gates.shipment_closure import PLANNED_ARCHIVE, LinkedDeliberationOutcome

from test_cascade_evidence_contract import _engine_record, cascade_record, safe_close_record

_SHIPMENT = "198-S"
_FEATURE = "192-F"
_SHA_D = "d" * 64
_SHA_E = "e" * 64
_SHA_F = "f" * 64

_OUTCOME = LinkedDeliberationOutcome
_RETAINED = (
    _OUTCOME.RETAINED_READ_ERROR,
    _OUTCOME.RETAINED_AMBIGUOUS,
    _OUTCOME.RETAINED_ENGINE_UNVERIFIED,
    _OUTCOME.RETAINED_LIVE_STATUS,
    _OUTCOME.RETAINED_SHARED_REFERENCE,
    _OUTCOME.RETAINED_DESCRIPTION_MENTION,
)


def _value(outcome: object) -> str:
    return str(getattr(outcome, "value", outcome))


def _disposition(
    outcome: object,
    *,
    deliberation_id: str = "035-DL",
    reason_code: str | None = None,
    records: list[tuple[str, str]] | None = None,
) -> dict:
    snapshot_records = records if records is not None else [(f".backlogit/queue/{deliberation_id}.md", _SHA_D)]
    return {
        "deliberation_id": deliberation_id,
        "outcome": _value(outcome),
        "reason_code": reason_code if reason_code is not None else _value(outcome),
        "path": None,
        "link_kinds": ["source_deliberation_id"],
        "linking_member_ids": [_FEATURE],
        "referrer_ids": [],
        "declared_status": "accepted",
        "records": [
            {"path": path, "declared_status": "accepted", "sha256": sha256} for path, sha256 in snapshot_records
        ],
    }


def _with_dispositions(record: dict, dispositions: list[dict]) -> dict:
    record["pre_close"]["linked_deliberation_disposition"]["dispositions"] = dispositions
    return record


def _verified_safe_close() -> dict:
    return safe_close_record()


def _unverified_safe_close() -> dict:
    # CASCADE x UNVERIFIED -> SAFE_CLOSE (select_close_path).
    return safe_close_record(classifier="CASCADE", engine=_engine_record("1.10.1"))


def _validate(record: dict, close_path: str) -> list[str]:
    return validate_evidence_record(record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path=close_path)


class DispositionOutcomeTests(unittest.TestCase):
    """Scenario 1: pre-mutation outcomes and two-way engine/outcome consistency."""

    def test_outcome_and_engine_consistency_table(self) -> None:
        rows: list[tuple[str, object, str, dict, bool]] = []
        # Every retained_* outcome under its matching engine verdict is accepted.
        for outcome in _RETAINED:
            if outcome is _OUTCOME.RETAINED_ENGINE_UNVERIFIED:
                rows.append((f"{outcome.value} / UNVERIFIED", _unverified_safe_close, "safe_close", _disposition(outcome), True))
            elif outcome in (_OUTCOME.RETAINED_READ_ERROR, _OUTCOME.RETAINED_AMBIGUOUS):
                rows.append((f"{outcome.value} / VERIFIED", _verified_safe_close, "safe_close", _disposition(outcome), True))
                rows.append((f"{outcome.value} / UNVERIFIED", _unverified_safe_close, "safe_close", _disposition(outcome), True))
            else:
                rows.append((f"{outcome.value} / VERIFIED", _verified_safe_close, "safe_close", _disposition(outcome), True))
        rows += [
            (
                "retained_read_error with an unknown reason_code",
                _verified_safe_close,
                "safe_close",
                _disposition(_OUTCOME.RETAINED_READ_ERROR, reason_code="some_future_reason"),
                True,
            ),
            ("archive / VERIFIED", _verified_safe_close, "safe_close", _disposition(PLANNED_ARCHIVE), True),
            ("archive / VERIFIED cascade", cascade_record, "cascade", _disposition(PLANNED_ARCHIVE), True),
            ("already-archived / VERIFIED", _verified_safe_close, "safe_close", _disposition(_OUTCOME.ALREADY_ARCHIVED), True),
            ("already-archived / UNVERIFIED", _unverified_safe_close, "safe_close", _disposition(_OUTCOME.ALREADY_ARCHIVED), True),
            ("archived / VERIFIED", _verified_safe_close, "safe_close", _disposition(_OUTCOME.ARCHIVED), False),
            ("archived / UNVERIFIED", _unverified_safe_close, "safe_close", _disposition(_OUTCOME.ARCHIVED), False),
            ("unknown outcome / VERIFIED", _verified_safe_close, "safe_close", _disposition("retained_whatever"), False),
            ("unknown outcome / UNVERIFIED", _unverified_safe_close, "safe_close", _disposition("retained_whatever"), False),
            ("archive / UNVERIFIED", _unverified_safe_close, "safe_close", _disposition(PLANNED_ARCHIVE), False),
            (
                "retained_live_status / UNVERIFIED",
                _unverified_safe_close,
                "safe_close",
                _disposition(_OUTCOME.RETAINED_LIVE_STATUS),
                False,
            ),
            (
                "retained_shared_reference / UNVERIFIED",
                _unverified_safe_close,
                "safe_close",
                _disposition(_OUTCOME.RETAINED_SHARED_REFERENCE),
                False,
            ),
            (
                "retained_description_mention / UNVERIFIED",
                _unverified_safe_close,
                "safe_close",
                _disposition(_OUTCOME.RETAINED_DESCRIPTION_MENTION),
                False,
            ),
            (
                "retained_engine_unverified / VERIFIED",
                _verified_safe_close,
                "safe_close",
                _disposition(_OUTCOME.RETAINED_ENGINE_UNVERIFIED),
                False,
            ),
            (
                "retained_engine_unverified / VERIFIED cascade",
                cascade_record,
                "cascade",
                _disposition(_OUTCOME.RETAINED_ENGINE_UNVERIFIED),
                False,
            ),
            ("empty reason_code", _verified_safe_close, "safe_close", _disposition(PLANNED_ARCHIVE, reason_code=""), False),
        ]
        for label, builder, close_path, disposition, accepted in rows:
            with self.subTest(label):
                record = builder()
                if close_path == "safe_close" and record["pre_close"]["engine_semantics"]["verdict"] == "UNVERIFIED":
                    # Keep the C2-1 observation rule satisfied so only the outcome rule decides.
                    record["pre_close"]["observation_set"] += _expected_observation([disposition])
                errors = _validate(_with_dispositions(record, [disposition]), close_path)
                if accepted:
                    self.assertEqual(errors, [])
                else:
                    self.assertNotEqual(errors, [], f"{label} was accepted")


def _expected_observation(dispositions: list[dict]) -> list[dict]:
    entries = []
    for disposition in dispositions:
        if disposition["outcome"] == _OUTCOME.ALREADY_ARCHIVED.value:
            continue
        for snapshot in disposition["records"]:
            entries.append(
                {
                    "id": disposition["deliberation_id"],
                    "path": snapshot["path"],
                    "location": "queue",
                    "sha256": snapshot["sha256"],
                    "declared_status": snapshot["declared_status"],
                }
            )
    return entries


class PlannerStateTests(unittest.TestCase):
    """Scenario 2: the snapshot is required on both paths and the planner did not fail."""

    def test_planner_state_table(self) -> None:
        def drop_snapshot(record: dict) -> None:
            del record["pre_close"]["linked_deliberation_disposition"]

        def planning_error(record: dict) -> None:
            record["pre_close"]["linked_deliberation_disposition"]["planning_error"] = "stash unreadable"

        rows = [
            ("safe_close without snapshot", safe_close_record, "safe_close", drop_snapshot),
            ("cascade without snapshot", cascade_record, "cascade", drop_snapshot),
            ("safe_close with planning_error", safe_close_record, "safe_close", planning_error),
            ("cascade with planning_error", cascade_record, "cascade", planning_error),
        ]
        for label, builder, close_path, mutation in rows:
            with self.subTest(label):
                record = builder()
                self.assertEqual(_validate(record, close_path), [], "baseline must be valid")
                mutation(record)
                self.assertNotEqual(_validate(record, close_path), [], f"{label} was accepted")


class SetTermTests(unittest.TestCase):
    """Scenario 3: no disposition-set deliberation is ever an allowed/required set term (D2)."""

    def test_set_term_table(self) -> None:
        def with_terms(key: str, deliberation_id: str, *, in_snapshot: bool):
            def build() -> dict:
                record = cascade_record()
                if in_snapshot:
                    _with_dispositions(record, [_disposition(PLANNED_ARCHIVE, deliberation_id=deliberation_id)])
                record["post_close"][key] = sorted(record["post_close"][key] + [deliberation_id])
                return record

            return build

        rows = [
            ("disposition-set id in required_ids", with_terms("required_ids", "035-DL", in_snapshot=True), False),
            ("disposition-set id in allowed_ids", with_terms("allowed_ids", "035-DL", in_snapshot=True), False),
            # H10: an explicit-member deliberation is excluded from the disposition set.
            ("explicit-member deliberation in allowed_ids", with_terms("allowed_ids", "040-DL", in_snapshot=False), True),
        ]
        for label, build, accepted in rows:
            with self.subTest(label):
                errors = _validate(build(), "cascade")
                if accepted:
                    self.assertEqual(errors, [])
                else:
                    self.assertNotEqual(errors, [], f"{label} was accepted")


class ObservationSetTests(unittest.TestCase):
    """Scenario 4: disposition-set deliberations in the observation set (cycle-1 R2, cycle-2 C2-1)."""

    def test_observation_set_table(self) -> None:
        dispositions = [
            _disposition(
                _OUTCOME.RETAINED_ENGINE_UNVERIFIED,
                deliberation_id="035-DL",
                records=[(".backlogit/queue/035-DL.md", _SHA_D), (".backlogit/queue/035-DL-notes.md", _SHA_E)],
            ),
            _disposition(
                _OUTCOME.ALREADY_ARCHIVED,
                deliberation_id="036-DL",
                records=[(".backlogit/archive/036-DL.md", _SHA_F)],
            ),
        ]

        def verified_with_deliberation() -> dict:
            record = _with_dispositions(_verified_safe_close(), [_disposition(PLANNED_ARCHIVE)])
            record["pre_close"]["observation_set"] += _expected_observation([_disposition(PLANNED_ARCHIVE)])
            return record

        def unverified(mutation=None):
            def build() -> dict:
                record = _with_dispositions(_unverified_safe_close(), [dict(item) for item in dispositions])
                record["pre_close"]["observation_set"] += _expected_observation(dispositions)
                if mutation is not None:
                    mutation(record["pre_close"]["observation_set"])
                return record

            return build

        def omit_one(entries: list[dict]) -> None:
            entries.pop()

        def change_sha(entries: list[dict]) -> None:
            entries[-1]["sha256"] = "0" * 64

        def add_already_archived(entries: list[dict]) -> None:
            entries.append(
                {
                    "id": "036-DL",
                    "path": ".backlogit/archive/036-DL.md",
                    "location": "archive",
                    "sha256": _SHA_F,
                    "declared_status": "accepted",
                }
            )

        def duplicate(entries: list[dict]) -> None:
            entries.append(dict(entries[-1]))

        rows = [
            ("VERIFIED safe_close holding a disposition-set id", verified_with_deliberation, False),
            ("UNVERIFIED safe_close holding exactly the expected entries", unverified(), True),
            ("UNVERIFIED safe_close with one path omitted", unverified(omit_one), False),
            ("UNVERIFIED safe_close with a changed sha256", unverified(change_sha), False),
            ("UNVERIFIED safe_close with an already-archived path added", unverified(add_already_archived), False),
            ("UNVERIFIED safe_close with a duplicated entry", unverified(duplicate), False),
        ]
        for label, build, accepted in rows:
            with self.subTest(label):
                errors = _validate(build(), "safe_close")
                if accepted:
                    self.assertEqual(errors, [])
                else:
                    self.assertNotEqual(errors, [], f"{label} was accepted")


if __name__ == "__main__":
    unittest.main()
