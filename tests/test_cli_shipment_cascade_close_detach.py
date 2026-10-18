"""CLI wiring of ``cascade-close --detach`` and exit code 9 (211.008-T, plan unit T7)."""

from __future__ import annotations

import unittest
from pathlib import Path

from test_cli_shipment_cascade_close import _BASE, _EVIDENCE, _MUTATING, _json, _run

from autoharness.cli import SHIPMENT_USAGE
from autoharness.shipment_close.command import CascadeCloseOutcome

_JOURNAL = Path("ws/.autoharness/gates/cascade-close/900-S-600-F.journal")


class DetachCliTests(unittest.TestCase):
    def test_detach_routes_to_the_mutating_entry_point_with_detach_set(self) -> None:
        outcome = CascadeCloseOutcome(
            exit_code=9, message="started", evidence_path=_EVIDENCE, phase_written="invoking", journal_path=_JOURNAL
        )
        payload, code, stubs = _json(*_MUTATING, "--detach", mutating=outcome)
        self.assertEqual(code, 9)
        self.assertEqual(payload["mode"], "detach")
        self.assertEqual(payload["exit_code"], 9)
        self.assertEqual(payload["mutation_possible"], "yes")
        self.assertEqual(payload["operator_action"], "none")
        self.assertEqual(payload["journal_path"], str(_JOURNAL))
        self.assertEqual(payload["phase_written"], "invoking")
        stubs.mutating.assert_called_once()
        self.assertIs(stubs.mutating.call_args.kwargs["detach"], True)
        stubs.classify.assert_not_called()

    def test_attached_calls_carry_no_detach_argument(self) -> None:
        outcome = CascadeCloseOutcome(exit_code=0, message="closed", evidence_path=_EVIDENCE)
        payload, _code, stubs = _json(*_MUTATING, mutating=outcome)
        self.assertEqual(payload["mode"], "mutating")
        self.assertNotIn("journal_path", payload)
        self.assertNotIn("detach", stubs.mutating.call_args.kwargs)

    def test_detach_mutation_free_refusals_stay_mutation_free(self) -> None:
        for exit_code in (2, 4):
            with self.subTest(exit_code=exit_code):
                outcome = CascadeCloseOutcome(exit_code=exit_code, message="refused", evidence_path=_EVIDENCE)
                payload, code, _stubs = _json(*_MUTATING, "--detach", mutating=outcome)
                self.assertEqual(code, exit_code)
                self.assertEqual(payload["mutation_possible"], "no")

    def test_detach_cannot_be_combined_with_classify_only(self) -> None:
        payload, code, stubs = _json(*_BASE, "--classify-only", "--detach")
        self.assertEqual(code, 2)
        self.assertEqual(payload["mutation_possible"], "no")
        stubs.mutating.assert_not_called()
        stubs.classify.assert_not_called()

    def test_detach_needs_the_mutating_arguments(self) -> None:
        _out, _err, code = _run(*_BASE, "--detach")
        self.assertEqual(code, 2)

    def test_usage_documents_detach_and_exit_9(self) -> None:
        self.assertIn("--detach", SHIPMENT_USAGE)
        self.assertIn("  9  --detach", SHIPMENT_USAGE)


if __name__ == "__main__":
    unittest.main()
