"""U5 (161.002-T): non-regression and 159-S replay for the shipment-reconcile
Pre-Mode Member-Class Status Contract (161-F / 169-S).

Pins the outcomes the corrected contract must NOT change, plus the one outcome
it must newly produce:

* Invariant I-3: a task-only manifest always classifies ``SAFE_CLOSE``, so a
  task-only closure takes the strict scalar path unchanged. Task-class outcomes
  are pinned explicitly (PA-3, the plan's "sleeper" action): ``queued`` and
  ``active`` HALT at closure; truly ``archived`` is ``pre-archived``; a
  relocated-but-``done`` task is ``matched``.
* R-1 targeted: an archive-resident record that declares ``queued`` HALTs. The
  former location-first step 3 silently passed it as ``pre-archived``.
* Intake (``expected_status: queued`` / ``active``) is unchanged even for a
  manifest whose shape would classify ``CASCADE`` at closure.
* 159-S replay: the exact historical manifest shape ``[151-F, 151.001-T ..
  151.007-T]`` (feature ``active`` in ``queue/``, every task declared ``done``
  and relocated to ``archive/``) now returns ``PROCEED`` with every member
  ``matched``, so the recorded P-005 deviation would not have been necessary.

Existing orphan-scan, record-scope and safe-close assertions are covered by
``test_shipment_reconcile_record_status.py`` and
``test_shipment_reconcile_safe_close.py``; the canonical gate runs them, and
they are not duplicated here.
"""

from __future__ import annotations

import unittest

from autoharness.gates.shipment_closure import ClosePath, classify_shipment_close_path

import _member_class_contract as mcc


def _evaluate_all(backlog: mcc.FixtureBacklog, manifest, *, expected_status: str, decision):
    return {
        label: mcc.evaluate_premode(
            mcc.load_contract(text),
            backlog.members(manifest),
            expected_status=expected_status,
            decision=decision,
        )
        for label, text in mcc.sources()
    }


class _FixtureTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.backlog = mcc.FixtureBacklog()
        self.addCleanup(self.backlog.cleanup)

    def _classify(self, manifest):
        return classify_shipment_close_path(list(manifest), self.backlog.backlog_dir)


class TaskClassNonRegressionTests(_FixtureTestCase):
    """I-3 and the PA-3 task-class pins."""

    _FEATURE = "910-F"
    _MANIFEST = ("910.001-T", "910.002-T")

    def _task_only(self, first_status: str, *, first_location: str = "archive") -> None:
        self.backlog.add(self._FEATURE, "feature", status="active")
        self.backlog.add(
            "910.001-T", "task", status=first_status, location=first_location, parent_id=self._FEATURE
        )
        self.backlog.add("910.002-T", "task", status="done", location="archive", parent_id=self._FEATURE)

    def test_task_only_manifest_always_classifies_safe_close(self) -> None:
        self._task_only("done")
        decision = self._classify(self._MANIFEST)
        self.assertIs(decision.close_path, ClosePath.SAFE_CLOSE)
        self.assertEqual(decision.qualifying_feature_ids, ())

    def test_task_class_outcomes_are_unchanged_at_closure(self) -> None:
        cases = (
            ("done", "archive", mcc.MATCHED, mcc.PROCEED),  # relocated-but-done
            ("archived", "archive", mcc.PRE_ARCHIVED, mcc.PROCEED),  # truly archived
            ("queued", "queue", mcc.STATUS_MISMATCH, mcc.HALT),
            ("active", "queue", mcc.STATUS_MISMATCH, mcc.HALT),
            ("parked", "queue", mcc.STATUS_MISMATCH, mcc.HALT),  # R-5
        )
        for status, location, expected_class, expected_recommendation in cases:
            with self.subTest(status=status, location=location):
                backlog = mcc.FixtureBacklog()
                self.addCleanup(backlog.cleanup)
                backlog.add(self._FEATURE, "feature", status="active")
                backlog.add("910.001-T", "task", status=status, location=location, parent_id=self._FEATURE)
                backlog.add("910.002-T", "task", status="done", location="archive", parent_id=self._FEATURE)
                decision = classify_shipment_close_path(list(self._MANIFEST), backlog.backlog_dir)
                self.assertIs(decision.close_path, ClosePath.SAFE_CLOSE)
                for label, outcome in _evaluate_all(
                    backlog, self._MANIFEST, expected_status="done", decision=decision
                ).items():
                    self.assertEqual(outcome.classifications["910.001-T"], expected_class, label)
                    self.assertEqual(outcome.recommendation, expected_recommendation, label)


class DeclaredStatusOverLocationTests(_FixtureTestCase):
    """R-1: location never short-circuits the declared-status read."""

    def test_archive_resident_queued_qualifying_feature_halts(self) -> None:
        self.backlog.add("920-F", "feature", status="queued", location="archive")
        self.backlog.add("920.001-T", "task", status="done", location="archive", parent_id="920-F")
        manifest = ("920-F", "920.001-T")
        decision = self._classify(manifest)
        self.assertIs(decision.close_path, ClosePath.CASCADE, decision.reason)
        for label, outcome in _evaluate_all(
            self.backlog, manifest, expected_status="done", decision=decision
        ).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.HALT)
                self.assertEqual(outcome.classifications["920-F"], mcc.STATUS_MISMATCH)

    def test_archive_resident_queued_task_halts(self) -> None:
        self.backlog.add("921-F", "feature", status="active")
        self.backlog.add("921.001-T", "task", status="queued", location="archive", parent_id="921-F")
        self.backlog.add("921.002-T", "task", status="done", location="archive", parent_id="921-F")
        manifest = ("921.001-T",)
        decision = self._classify(manifest)
        for label, outcome in _evaluate_all(
            self.backlog, manifest, expected_status="done", decision=decision
        ).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.classifications["921.001-T"], mcc.STATUS_MISMATCH)
                self.assertEqual(outcome.recommendation, mcc.HALT)

    def test_premode_step_3_no_longer_classifies_by_location(self) -> None:
        for label, text in mcc.sources():
            premode = mcc.flatten(mcc.section(text, "### Pre-Mode", "### Post-Mode"))
            with self.subTest(source=label):
                self.assertNotIn("if archive file exists, classify as `pre-archived`", premode)
                self.assertIn("Location never short-circuits", premode)
                self.assertIn("location label", premode)


class IntakeNonRegressionTests(_FixtureTestCase):
    """Intake keeps strict scalar semantics for every member, feature included."""

    _MANIFEST = ("930-F", "930.001-T", "930.002-T")

    def _uniform(self, status: str) -> None:
        self.backlog.add("930-F", "feature", status=status)
        for task in self._MANIFEST[1:]:
            self.backlog.add(task, "task", status=status, parent_id="930-F")

    def test_fresh_intake_all_queued_proceeds(self) -> None:
        self._uniform("queued")
        decision = self._classify(self._MANIFEST)
        self.assertIs(decision.close_path, ClosePath.CASCADE, decision.reason)
        for label, outcome in _evaluate_all(
            self.backlog, self._MANIFEST, expected_status="queued", decision=decision
        ).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.PROCEED, outcome)

    def test_post_claim_intake_all_active_proceeds(self) -> None:
        self._uniform("active")  # P-002.7 row T1
        decision = self._classify(self._MANIFEST)
        for label, outcome in _evaluate_all(
            self.backlog, self._MANIFEST, expected_status="active", decision=decision
        ).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.PROCEED, outcome)

    def test_intake_never_applies_the_qualifying_feature_row(self) -> None:
        # A `done` feature at `queued` intake is drift, not a qualifying-feature pass.
        self.backlog.add("930-F", "feature", status="done")
        for task in self._MANIFEST[1:]:
            self.backlog.add(task, "task", status="queued", parent_id="930-F")
        decision = self._classify(self._MANIFEST)
        for label, outcome in _evaluate_all(
            self.backlog, self._MANIFEST, expected_status="queued", decision=decision
        ).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.classifications["930-F"], mcc.STATUS_MISMATCH)
                self.assertEqual(outcome.recommendation, mcc.HALT)


class Replay159STests(_FixtureTestCase):
    """The executable evidence behind decision D-1's acceptance basis."""

    _MANIFEST = ("151-F", *(f"151.00{index}-T" for index in range(1, 8)))

    def test_159s_shape_proceeds_with_no_deviation(self) -> None:
        self.backlog.add("151-F", "feature", status="active")
        for task in self._MANIFEST[1:]:
            self.backlog.add(task, "task", status="done", location="archive", parent_id="151-F")
        decision = self._classify(self._MANIFEST)
        self.assertIs(decision.close_path, ClosePath.CASCADE, decision.reason)
        self.assertEqual(decision.qualifying_feature_ids, ("151-F",))
        for label, outcome in _evaluate_all(
            self.backlog, self._MANIFEST, expected_status="done", decision=decision
        ).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.PROCEED, outcome)
                self.assertIsNone(outcome.halt_token)
                self.assertEqual(set(outcome.classifications.values()), {mcc.MATCHED}, outcome)


if __name__ == "__main__":
    unittest.main()
