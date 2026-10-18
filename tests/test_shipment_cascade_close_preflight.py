"""``cascade-close`` caller-wait pre-flight (211.007-T, plan unit T8): the refusal is pre-mutation."""

from __future__ import annotations

import unittest

from test_shipment_cascade_close_detach import _DetachHarness
from test_shipment_cascade_close_invoke import _FEATURE, _SHIPMENT, _VERIFIED, _Harness, _ship_argvs

from autoharness.gates.cascade_evidence import build_evidence_path
from autoharness.shipment_close import EXIT_INPUT, EXIT_OK
from autoharness.shipment_close.journal import journal_path
from autoharness.shipment_close.runner import SUPERVISION_MARGIN_SECONDS


class CallerWaitPreflightTests(unittest.TestCase):
    def _assert_nothing_happened(self, harness: _Harness) -> None:
        self.assertEqual(harness.argv_log(), [], "not even the engine probe may run")
        self.assertFalse(harness.shipped)
        self.assertFalse(build_evidence_path(harness.root, _SHIPMENT, _FEATURE).exists())
        self.assertFalse((harness.root / ".autoharness" / "gates" / "cascade-close").exists())
        self.assertFalse(journal_path(harness.root, _SHIPMENT, _FEATURE).exists())

    def test_a_caller_wait_shorter_than_timeout_plus_margin_is_refused_before_anything_runs(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        needed = 60 + SUPERVISION_MARGIN_SECONDS  # the harness runs with --timeout 60
        for declared in (0, 1, needed - 1):
            with self.subTest(declared=declared):
                outcome = harness.run(caller_wait_seconds=declared)
                self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
                self.assertIn(str(needed), outcome.message)
                self.assertIn("--detach", outcome.message)
                self._assert_nothing_happened(harness)

    def test_a_sufficient_or_undeclared_caller_wait_runs(self) -> None:
        needed = 60 + SUPERVISION_MARGIN_SECONDS
        for declared in (needed, needed + 1, None):
            with self.subTest(declared=declared):
                harness = _Harness(self, probes=[_VERIFIED])
                outcome = harness.run(caller_wait_seconds=declared)
                self.assertEqual(outcome.exit_code, EXIT_OK, (outcome.message, outcome.failures))
                self.assertEqual(len(_ship_argvs(harness.argv_log())), 1)

    def test_detach_is_never_refused_by_the_caller_wait(self) -> None:
        harness = _DetachHarness(self)
        outcome = harness.detach(caller_wait_seconds=1)
        self.assertIn(outcome.exit_code, (9, 0), outcome.message)
        self.assertNotIn("caller wait", outcome.message)
        harness.wait_outcome()
        harness.wait_lock_gone()


if __name__ == "__main__":
    unittest.main()
