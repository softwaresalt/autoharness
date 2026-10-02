"""Consumers of the shipment-reconcile ``linked_deliberation_disposition`` report.

Plan unit U6b (docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md):
post-merge consumers read the P-015 INV-12 Linked-Deliberation Disposition
report and never archive a retained deliberation on their own.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SHIP_TEMPLATE = _ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"

_STEP7_START = "7. **Source artifact cleanup**"
_STEP7_END = "8. **Mandatory (P-020)**"


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _ship_template_step7() -> str:
    text = _SHIP_TEMPLATE.read_text(encoding="utf-8")
    start = text.index(_STEP7_START)
    end = text.index(_STEP7_END, start)
    return _normalize(text[start:end])


class ShipStep7ConsumesDispositionReportTests(unittest.TestCase):
    """195.012-T K-1: Ship template post-merge Step 7 reads the report."""

    def test_k1_step7_reads_linked_deliberation_disposition_report(self) -> None:
        section = _ship_template_step7()
        self.assertIn("`linked_deliberation_disposition` report", section)
        self.assertIn("Linked-Deliberation Disposition step (P-015 INV-12)", section)
        # The verify-workspace ``ship_source_artifact_cleanup`` tokens stay present.
        self.assertIn("source_deliberation_id", section)
        self.assertIn("backlogit_archive_item", section)
        self.assertIn("never call `backlogit_archive_item` on it independently", section)
        # The withdrawn independent archive call is gone.
        self.assertNotIn(
            "If it exists and is not already archived, call `backlogit_archive_item`",
            section,
        )

    def test_k1_archived_and_already_archived_are_recorded_and_skipped(self) -> None:
        section = _ship_template_step7()
        self.assertIn(
            "outcome `archived` or `already-archived`: record it and skip",
            section,
        )

    def test_k1_retained_outcomes_are_never_archived_and_recorded_verbatim(self) -> None:
        section = _ship_template_step7()
        self.assertIn(
            "any `retained_*` outcome (including `retained_read_error`): **never archive**",
            section,
        )
        self.assertIn(
            "record the outcome verbatim with its `reason_code` (and `path`, when present)",
            section,
        )
        self.assertIn(
            "An unknown `reason_code` is accepted and recorded verbatim.",
            section,
        )

    def test_k1_missing_from_report_is_skipped_not_archived(self) -> None:
        section = _ship_template_step7()
        self.assertIn(
            "the deliberation is absent from the report (the report predates this "
            "contract, or the link was outside the disposition set): record "
            "`skipped_not_in_disposition_report` and never archive",
            section,
        )


if __name__ == "__main__":
    unittest.main()
