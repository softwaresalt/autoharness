"""Compound learning coverage for shipment-record-status claim-integrity
(2970FA4E part 3 / 105.001-T / 105-F / 109-S).

Verifies `docs/compound/2026-08-01-shipment-record-status-integrity.md`:

* exists
* captures all three signals: the `CLAIM_VERIFY_FAILED` signal, the
  `SHIPMENT_STATE_INCONSISTENT` signal, and the queued-with-active-work
  failure pattern (record stays queued while manifest tasks go active/done,
  e.g. `103-S`)
* explains the detect-and-report mitigation now homed in shipment-reconcile
  pre-mode (per T1 / 105.002-T)
* notes true self-repair remains decision-gated and the backlogit-internal
  active->queued guard is EXTERNAL
* cross-references the claim-integrity spike and the 106-S claim-integrity
  guards compound learning
"""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_DOC = _ROOT / "docs" / "compound" / "2026-08-01-shipment-record-status-integrity.md"

_SPIKE_REF = "docs/decisions/2026-07-30-ship-claim-integrity-preflight-spike.md"
_GUARDS_REF = "docs/compound/106-S-claim-integrity-guards.md"


class ShipmentRecordStatusCompoundDocTests(unittest.TestCase):
    def test_doc_exists(self) -> None:
        self.assertTrue(_DOC.exists(), f"missing compound learning doc: {_DOC}")

    def test_captures_all_three_signals(self) -> None:
        text = _DOC.read_text(encoding="utf-8")
        self.assertIn("CLAIM_VERIFY_FAILED", text)
        self.assertIn("SHIPMENT_STATE_INCONSISTENT", text)
        self.assertIn("queued-with-active-work", text)
        self.assertIn("103-S", text)

    def test_explains_detect_and_report_mitigation_homed_in_pre_mode(self) -> None:
        text = _DOC.read_text(encoding="utf-8")
        self.assertIn("shipment-reconcile", text)
        self.assertIn("pre-mode", text)
        self.assertIn("detect-and-report", text)
        self.assertIn("record-consistent", text)

    def test_notes_self_repair_decision_gated_and_external_guard(self) -> None:
        text = _DOC.read_text(encoding="utf-8")
        self.assertIn("decision-gated", text)
        self.assertIn("self-repair", text)
        self.assertIn("EXTERNAL", text)
        self.assertIn("blocked → queued", text)

    def test_cross_references_spike_and_guards_doc(self) -> None:
        text = _DOC.read_text(encoding="utf-8")
        self.assertIn(_SPIKE_REF, text)
        self.assertIn(_GUARDS_REF, text)

    def test_has_frontmatter_with_expected_tags(self) -> None:
        text = _DOC.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("shipment: 109-S", text)
        self.assertIn("feature: 105-F", text)


if __name__ == "__main__":
    unittest.main()
