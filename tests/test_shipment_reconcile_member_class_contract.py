"""U4 (161.001-T): gate-behaviour tests for the shipment-reconcile Pre-Mode
Member-Class Status Contract (161-F / 169-S; bug 15A02E21; decision D-2/D-3).

Defect under test: Pre-Mode step 3 compared every manifest member's declared
``status`` against one scalar ``expected_status``. A P-015 ``CASCADE``-eligible
manifest must contain its qualifying root feature, which is validly ``active``
until the cascade archives it, so every cascade-eligible closure halted with
``status-mismatch`` before Safe-Close Step 0(c) ever ran.

Behavioural scenarios run the real, unmodified ``classify_shipment_close_path``
against an in-repo fixture backlog and apply the status sets *parsed from the
skill's own member-class table* (``tests/_member_class_contract.py``):

* (a) fully-covered root under ``CASCADE``, qualifying feature ``active`` or
  ``done`` -> ``PROCEED``;
* archived qualifying feature -> tolerated, reported under
  ``qualifying-feature-pre-archived-anomaly`` (R-2), never silently absorbed;
* (b) the same manifest with the feature ``queued`` -> ``HALT``;
* unrecognised feature status -> explicit ``HALT`` (R-5);
* (c) ``SAFE_CLOSE`` manifest -> strict scalar semantics, unchanged;
* (d) classifier error -> strict scalar semantics, fail-closed;
* classifier contract violations (I-1/I-2) -> ``HALT``.

Doc-contract assertions pin step 2b (portable, references Step 0(c), advisory
for gating only, R-3 reason rules) and the report contract. Every assertion runs
against BOTH the resolved skill and the rendered template.
"""

from __future__ import annotations

import re
import unittest

from autoharness.gates.shipment_closure import (
    ClosePath,
    ClosePathDecision,
    classify_shipment_close_path,
)

import _member_class_contract as mcc

_FEATURE = "900-F"
_TASKS = tuple(f"900.00{index}-T" for index in range(1, 4))
_MANIFEST = (_FEATURE, *_TASKS)


def _premode_section(text: str) -> str:
    return mcc.section(text, "### Pre-Mode", "### Post-Mode")


class _FixtureTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.backlog = mcc.FixtureBacklog()
        self.addCleanup(self.backlog.cleanup)

    def _fully_covered_root(self, *, feature_status: str, feature_location: str = "queue") -> None:
        self.backlog.add(_FEATURE, "feature", status=feature_status, location=feature_location)
        for task in _TASKS:
            # Ship's task loop relocates completed tasks: archive-resident, declared `done`.
            self.backlog.add(task, "task", status="done", location="archive", parent_id=_FEATURE)

    def _classify(self, manifest=_MANIFEST) -> ClosePathDecision:
        return classify_shipment_close_path(list(manifest), self.backlog.backlog_dir)

    def _evaluate(self, *, expected_status: str = "done", decision, manifest=_MANIFEST):
        outcomes = {}
        for label, text in mcc.sources():
            contract = mcc.load_contract(text)
            outcomes[label] = mcc.evaluate_premode(
                contract,
                self.backlog.members(manifest),
                expected_status=expected_status,
                decision=decision,
            )
        return outcomes


class QualifyingFeatureGateBehaviourTests(_FixtureTestCase):
    """Scenarios (a), (b), R-2 and R-5 under a real CASCADE verdict."""

    def test_a_cascade_active_qualifying_feature_proceeds(self) -> None:
        self._fully_covered_root(feature_status="active")
        decision = self._classify()
        self.assertIs(decision.close_path, ClosePath.CASCADE, decision.reason)
        self.assertEqual(decision.qualifying_feature_ids, (_FEATURE,))
        for label, outcome in self._evaluate(decision=decision).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.PROCEED, outcome)
                self.assertEqual(outcome.classifications[_FEATURE], mcc.MATCHED)

    def test_a_cascade_done_qualifying_feature_proceeds(self) -> None:
        self._fully_covered_root(feature_status="done")
        decision = self._classify()
        self.assertIs(decision.close_path, ClosePath.CASCADE, decision.reason)
        for label, outcome in self._evaluate(decision=decision).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.PROCEED, outcome)
                self.assertEqual(outcome.classifications[_FEATURE], mcc.MATCHED)

    def test_archived_qualifying_feature_is_tolerated_and_reported_under_its_own_label(self) -> None:
        self._fully_covered_root(feature_status="archived", feature_location="archive")
        decision = self._classify()
        self.assertIs(decision.close_path, ClosePath.CASCADE, decision.reason)
        for label, outcome in self._evaluate(decision=decision).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.PROCEED, outcome)
                # R-2: never the generic benign `pre-archived` label.
                self.assertEqual(outcome.classifications[_FEATURE], mcc.ANOMALY)

    def test_b_cascade_queued_qualifying_feature_halts(self) -> None:
        self._fully_covered_root(feature_status="queued")
        decision = self._classify()
        self.assertIs(decision.close_path, ClosePath.CASCADE, decision.reason)
        for label, outcome in self._evaluate(decision=decision).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.HALT, outcome)
                self.assertEqual(outcome.classifications[_FEATURE], mcc.STATUS_MISMATCH)

    def test_unrecognised_qualifying_feature_status_halts_explicitly(self) -> None:
        for status in ("parked", "blocked", "review"):
            with self.subTest(status=status):
                backlog = mcc.FixtureBacklog()
                self.addCleanup(backlog.cleanup)
                backlog.add(_FEATURE, "feature", status=status)
                for task in _TASKS:
                    backlog.add(task, "task", status="done", location="archive", parent_id=_FEATURE)
                decision = classify_shipment_close_path(list(_MANIFEST), backlog.backlog_dir)
                self.assertIs(decision.close_path, ClosePath.CASCADE, decision.reason)
                for label, text in mcc.sources():
                    outcome = mcc.evaluate_premode(
                        mcc.load_contract(text),
                        backlog.members(_MANIFEST),
                        expected_status="done",
                        decision=decision,
                    )
                    self.assertEqual(outcome.recommendation, mcc.HALT, (label, outcome))
                    self.assertEqual(outcome.classifications[_FEATURE], mcc.STATUS_MISMATCH)


class StrictScalarFallbackTests(_FixtureTestCase):
    """Scenarios (c) and (d): no relaxation without a CASCADE verdict."""

    def test_c_safe_close_partial_feature_keeps_strict_semantics(self) -> None:
        self._fully_covered_root(feature_status="active")
        # A live out-of-manifest sibling makes this a partial-feature shipment.
        self.backlog.add("900.004-T", "task", status="queued", parent_id=_FEATURE)
        decision = self._classify()
        self.assertIs(decision.close_path, ClosePath.SAFE_CLOSE)
        for label, outcome in self._evaluate(decision=decision).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.HALT, outcome)
                self.assertEqual(outcome.classifications[_FEATURE], mcc.STATUS_MISMATCH)
                for task in _TASKS:
                    self.assertEqual(outcome.classifications[task], mcc.MATCHED)

    def test_d_classifier_error_keeps_strict_fail_closed_semantics(self) -> None:
        self._fully_covered_root(feature_status="active")
        for label, outcome in self._evaluate(decision=None).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.HALT, outcome)
                self.assertEqual(outcome.classifications[_FEATURE], mcc.STATUS_MISMATCH)

    def test_d_safe_close_with_read_failure_reason_keeps_strict_semantics(self) -> None:
        self._fully_covered_root(feature_status="active")
        decision = ClosePathDecision(
            close_path=ClosePath.SAFE_CLOSE,
            reason="a manifest item's backlog record is malformed: simulated",
        )
        for label, outcome in self._evaluate(decision=decision).items():
            with self.subTest(source=label):
                self.assertEqual(outcome.recommendation, mcc.HALT, outcome)

    def test_classifier_contract_violations_halt(self) -> None:
        self._fully_covered_root(feature_status="active")
        empty_cascade = ClosePathDecision(close_path=ClosePath.CASCADE, reason="synthetic I-2")
        foreign_cascade = ClosePathDecision(
            close_path=ClosePath.CASCADE, reason="synthetic I-1", qualifying_feature_ids=("901-F",)
        )
        for decision in (empty_cascade, foreign_cascade):
            for label, outcome in self._evaluate(decision=decision).items():
                with self.subTest(source=label, reason=decision.reason):
                    self.assertEqual(outcome.recommendation, mcc.HALT)
                    self.assertEqual(outcome.halt_token, mcc.CLASSIFIER_CONTRACT_HALT)


class MemberClassContractTextTests(unittest.TestCase):
    """Doc-contract assertions over both copies."""

    def test_contract_block_declares_both_member_classes(self) -> None:
        for label, text in mcc.sources():
            with self.subTest(source=label):
                contract = mcc.load_contract(text)
                self.assertEqual(
                    set(contract), {mcc.CLASS_QUALIFYING_FEATURE, mcc.CLASS_STRICT_SCALAR}
                )
                feature_row = contract[mcc.CLASS_QUALIFYING_FEATURE]
                self.assertEqual(set(feature_row.matched), {"active", "done"})
                self.assertEqual(dict(feature_row.tolerated), {"archived": mcc.ANOMALY})
                self.assertIn("queued", feature_row.halting)
                self.assertTrue(feature_row.halts_on_any_other_value)
                strict_row = contract[mcc.CLASS_STRICT_SCALAR]
                self.assertTrue(strict_row.matched_is_expected_status)
                self.assertEqual(dict(strict_row.tolerated), {"archived": mcc.PRE_ARCHIVED})
                self.assertTrue(strict_row.halts_on_any_other_value)

    def test_membership_comes_only_from_the_classifier_set(self) -> None:
        for label, text in mcc.sources():
            block = mcc.flatten(mcc.extract_contract_block(text))
            with self.subTest(source=label):
                self.assertIn("qualifying feature set recorded by Pre-Mode step 2b", block)
                self.assertIn("never from an ID pattern", block)
                self.assertIn("only to the pre-close invocation (`expected_status: done`)", block)
                self.assertIn(mcc.CLASSIFIER_CONTRACT_HALT, block)

    def test_unrecognised_status_halt_is_explicit(self) -> None:
        for label, text in mcc.sources():
            block = mcc.flatten(mcc.extract_contract_block(text))
            with self.subTest(source=label):
                self.assertIn("R-5", block)
                self.assertIn("never silently absorbed", block)

    def test_shipment_record_row_reuses_109s_vocabulary_and_treats_blocked_as_anomaly(self) -> None:
        for label, text in mcc.sources():
            block = mcc.flatten(mcc.extract_contract_block(text))
            with self.subTest(source=label):
                for token in (
                    "record-consistent",
                    "record-queued-with-active-work",
                    "record-blocked-with-active-work",
                    "record-blocked-with-done-work",
                ):
                    self.assertIn(token, block)
                # No parallel record-scope vocabulary inside the block.
                self.assertEqual(
                    set(re.findall(r"`(record-[a-z-]+)`", block)),
                    {
                        "record-consistent",
                        "record-queued-with-active-work",
                        "record-blocked-with-active-work",
                        "record-blocked-with-done-work",
                    },
                )
                self.assertIn("reportable anomaly, never a waitable state", block)
                self.assertIn("no legal outbound transition", block)

    def test_step_2b_is_portable_and_references_step_0c(self) -> None:
        for label, text in mcc.sources():
            premode = mcc.flatten(_premode_section(text))
            with self.subTest(source=label):
                self.assertIn("2b. **Classify the close path for gating**", premode)
                self.assertIn(
                    "`classify_shipment_close_path(manifest_items, workspace_backlog_dir)`-shaped function",
                    premode,
                )
                self.assertIn("the equivalent structural check", premode)
                self.assertIn("Safe-Close Step 0(c)", premode)
                self.assertIn("advisory for gating only", premode)
                self.assertIn("Step 0(c) remains authoritative", premode)

    def test_step_2b_runs_after_lock_and_manifest_load_and_before_item_check(self) -> None:
        for label, text in mcc.sources():
            premode = _premode_section(text)
            with self.subTest(source=label):
                lock = premode.index("Acquire single-writer lock")
                load = premode.index("Load manifest")
                step_2b = premode.index("2b. **Classify the close path for gating**")
                check = premode.index("Check each manifest item")
                self.assertLess(lock, load)
                self.assertLess(load, step_2b)
                self.assertLess(step_2b, check)

    def test_step_2b_reason_is_never_blank(self) -> None:
        for label, text in mcc.sources():
            premode = mcc.flatten(_premode_section(text))
            with self.subTest(source=label):
                self.assertIn("verbatim", premode)
                self.assertIn("classifier-reason-unavailable", premode)
                self.assertIn("never a blank field", premode)

    def test_disagreement_between_2b_and_step_0c_is_a_halt(self) -> None:
        for label, text in mcc.sources():
            flat = mcc.flatten(text)
            with self.subTest(source=label):
                self.assertGreaterEqual(flat.count("RECONCILE_FAIL_PREMODE_CLASSIFIER_DRIFT"), 2)
                step_0c = mcc.flatten(mcc.section(text, "c. **Classify the close path**", "1. **Load manifest**"))
                self.assertIn("RECONCILE_FAIL_PREMODE_CLASSIFIER_DRIFT", step_0c)
                self.assertIn("pre_close.classifier_verdict", step_0c)
                self.assertIn("pre_close.qualifying_feature_ids", step_0c)

    def test_report_contract_records_verdict_reason_set_and_per_item_class(self) -> None:
        for label, text in mcc.sources():
            premode = mcc.flatten(_premode_section(text))
            report = premode[premode.index("**Produce report**") :]
            with self.subTest(source=label):
                for needle in (
                    "verdict",
                    "reason",
                    "qualifying feature set",
                    "location label",
                    "declared status",
                    "member class",
                    "classification",
                ):
                    self.assertIn(needle, report)

    def test_gate_decision_proceeds_on_reported_anomaly_and_halts_on_contract_violation(self) -> None:
        for label, text in mcc.sources():
            premode = mcc.flatten(_premode_section(text))
            gate = premode[premode.index("**Gate decision**") :]
            with self.subTest(source=label):
                self.assertIn(mcc.ANOMALY, gate)
                self.assertIn(mcc.CLASSIFIER_CONTRACT_HALT, gate)


if __name__ == "__main__":
    unittest.main()
