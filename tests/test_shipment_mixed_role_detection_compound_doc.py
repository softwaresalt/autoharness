"""Compound learning coverage for shipment-record-status mixed-role
DETECTION + REPORT-ONLY diagnostics (936C68F3 part 2 / 112-F / 118-S).

Verifies `docs/compound/2026-08-06-shipment-mixed-role-detection-report-only.md`:

* exists, with expected frontmatter
* captures the withdrawn repair premise and the Copilot PR #304 finding 1
  evidence that invalidated it
* documents the per-task ROLE classification (`live-queued` / `live-active` /
  `archived-completed(done)` in either archive representation) and the
  per-item anomaly set
* documents the `DETECTED` / `REPORTED` / `DEGRADED` outcome model with no
  repair/succeeded/refused/two-active outcome
* documents the operator-remediation runbook and the permanent
  deferral-with-evidence of auto-repair
* records the 936C68F3 living-tracker disposition and provenance-cleanup
  contract correction (source_stash_tracker_id, not source_stash_id)
* cross-references 013-DL, 112.001-R, the 109-S/105-F compound doc, and the
  shipment-reconcile SKILL template
"""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_DOC = (
    _ROOT
    / "docs"
    / "compound"
    / "2026-08-06-shipment-mixed-role-detection-report-only.md"
)

_RECORD_STATUS_DOC_REF = "docs/compound/2026-08-01-shipment-record-status-integrity.md"
_STATUS_CONSTRAINTS_DOC_REF = "docs/compound/2026-05-07-backlogit-shipment-status-constraints.md"
_SKILL_REF = "templates/skills/shipment-reconcile/SKILL.md.tmpl"


def _text() -> str:
    return _DOC.read_text(encoding="utf-8")


class ShipmentMixedRoleDetectionCompoundDocTests(unittest.TestCase):
    def test_doc_exists(self) -> None:
        self.assertTrue(_DOC.exists(), f"missing compound learning doc: {_DOC}")

    def test_has_frontmatter_with_expected_provenance(self) -> None:
        text = _text()
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("shipment: 118-S", text)
        self.assertIn("feature: 112-F", text)
        self.assertIn("source_deliberation_id: 013-DL", text)
        self.assertIn("source_stash_tracker_id: 936C68F3", text)

    def test_documents_withdrawn_repair_premise_and_evidence(self) -> None:
        text = _text()
        self.assertIn("013-DL", text)
        self.assertIn("Copilot PR #304", text)
        self.assertIn("finding 1", text)
        self.assertIn("manifest-wide", text.lower())
        self.assertIn("STRICTLY SINGLE-SHOT", text)
        self.assertIn("ErrShipmentConflict", text)
        self.assertIn("shipment_lifecycle.go", text)
        self.assertIn("NOT mutated", text)

    def test_documents_per_task_role_classification(self) -> None:
        text = _text()
        for role in ("live-queued", "live-active", "archived-completed(done)"):
            with self.subTest(role=role):
                self.assertIn(role, text)
        self.assertIn("terminal relocation", text.lower())
        self.assertIn("explicit archival", text.lower())

    def test_documents_anomaly_set(self) -> None:
        text = _text()
        for anomaly in (
            "duplicate",
            "conflicting",
            "missing",
            "malformed-provenance",
            "any-other-archived-status",
            "orphan",
            "out-of-role",
            "torn-partial",
        ):
            with self.subTest(anomaly=anomaly):
                self.assertIn(anomaly, text)

    def test_documents_outcome_model(self) -> None:
        text = _text()
        for outcome in ("DETECTED", "REPORTED", "DEGRADED"):
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, text)
        self.assertIn("succeeded", text)
        self.assertIn("repaired", text)
        self.assertIn("refused", text)
        self.assertIn("two-active", text)

    def test_documents_malformed_legacy_no_fabricated_transition(self) -> None:
        text = _text()
        self.assertIn("malformed-legacy", text)
        self.assertIn("blocked", text)
        self.assertIn("fabricated", text.lower())

    def test_documents_operator_remediation_runbook(self) -> None:
        text = _text()
        self.assertIn("Operator-Remediation Runbook", text)
        self.assertIn("NO auto-repair", text)
        self.assertIn("mode: safe-close", text)

    def test_documents_936c68f3_living_tracker_disposition(self) -> None:
        text = _text()
        self.assertIn("936C68F3", text)
        self.assertIn("ACTIVE living tracker", text)
        self.assertIn("NOT", text)
        self.assertIn("partial-report-only-slice", text)
        self.assertIn("source_stash_id", text)
        self.assertIn("source_stash_tracker_id", text)

    def test_cross_references_expected_docs_and_skill(self) -> None:
        text = _text()
        self.assertIn(_RECORD_STATUS_DOC_REF, text)
        self.assertIn(_STATUS_CONSTRAINTS_DOC_REF, text)
        self.assertIn(_SKILL_REF, text)
        self.assertIn("112.001-R", text)


if __name__ == "__main__":
    unittest.main()
