"""Shipment-reconcile pre-mode: shipment-record-status classification contract
(105-F / 109-S).

Extends `shipment-reconcile` pre-mode to be the long-term integrity-check home
for shipment-record-status consistency: a NEW classification that compares the
shipment record's OWN status against the aggregate status of its manifest
tasks, distinct from the per-item (`matched` / `pre-archived` / `missing` /
`status-mismatch` / `orphan` / `qualifying-feature-pre-archived-anomaly`)
classifications.

Four record-scope cases, mutually exclusive, partitioned first by the record's
own status (`{{STATUS_QUEUED}}` vs `{{STATUS_BLOCKED}}`):

* `record-consistent`
* `record-queued-with-active-work` -- record `{{STATUS_QUEUED}}` AND a manifest
  task `{{STATUS_ACTIVE}}`/`{{STATUS_DONE}}` (the 103-S failure mode).
* `record-blocked-with-active-work` -- record `{{STATUS_BLOCKED}}` AND a
  manifest task `{{STATUS_ACTIVE}}`. Takes PRECEDENCE over the case below when
  a blocked record has both an active task and a done task.
* `record-blocked-with-done-work` -- record `{{STATUS_BLOCKED}}` AND no task
  `{{STATUS_ACTIVE}}` AND a manifest task `{{STATUS_DONE}}`.

The check reuses data already read in pre-mode steps 2 (shipment record via
`{{OP_GET_SHIPMENT_MCP}}`) and 3 (manifest item statuses) -- NO new scan
(plan P2-2). Any non-consistent classification HALTs the pre-mode
recommendation with `HALT — operator reconcile required`, naming the shipment
id, the record's own status, and the conflicting task ids. Detect-and-report
only; NO auto-repair.

Both copies are verified: the template
`templates/skills/shipment-reconcile/SKILL.md.tmpl` and its installed dogfood
mirror `.github/skills/shipment-reconcile/SKILL.md`. (An earlier revision of
this docstring said no installed mirror existed and verified the template
alone; that premise became false once the resolved copy was installed, which
left the copy that this workspace actually executes untested. Corrected by
161.004-T.) A needle that names a template placeholder is rendered with this
workspace's own variable table before it is searched for in the resolved copy.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import Callable

_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _ROOT / "templates" / "skills" / "shipment-reconcile" / "SKILL.md.tmpl"
_RESOLVED_RELATIVE = ".github/skills/shipment-reconcile/SKILL.md"
_RESOLVED = _ROOT / _RESOLVED_RELATIVE

_CASES = (
    "record-consistent",
    "record-queued-with-active-work",
    "record-blocked-with-active-work",
    "record-blocked-with-done-work",
)

# Anchors used to bound ordering assertions within the Pre-Mode protocol.
_CHECK_ITEM_ANCHOR = "Check each manifest item"
_ORPHAN_SCAN_ANCHOR = "Orphan scan"
_PRODUCE_REPORT_ANCHOR = "Produce report"
_GATE_DECISION_ANCHOR = "Gate decision"
_NEW_STEP_ANCHOR = "Shipment-record-status classification"

_resolved_variables: dict[str, str] | None = None


def _render_needle(needle: str) -> str:
    """Render a placeholder-bearing needle for the resolved copy."""
    global _resolved_variables
    if _resolved_variables is None:
        from _assertion_render import VARIANT_BACKLOGIT, RenderedCorpus

        _resolved_variables = RenderedCorpus(VARIANT_BACKLOGIT).variables_for(_RESOLVED_RELATIVE)
    from autoharness.verify_workspace import _render_template

    return _render_template(needle, _resolved_variables)


def _sources() -> tuple[tuple[str, str, Callable[[str], str]], ...]:
    """(label, content, needle renderer) for the template and the resolved copy."""
    return (
        ("template", _TEMPLATE.read_text(encoding="utf-8"), lambda needle: needle),
        ("resolved", _RESOLVED.read_text(encoding="utf-8"), _render_needle),
    )


class ShipmentRecordStatusClassificationTests(unittest.TestCase):
    def test_all_four_cases_present(self) -> None:
        for label, content, _ in _sources():
            for case in _CASES:
                with self.subTest(source=label, case=case):
                    self.assertIn(case, content)

    def test_cases_are_declared_mutually_exclusive(self) -> None:
        for label, content, _ in _sources():
            with self.subTest(source=label):
                self.assertIn("mutually exclusive", content)

    def test_blocked_active_precedence_over_blocked_done(self) -> None:
        """blocked+active takes precedence over blocked+done when both apply."""
        for label, content, _ in _sources():
            with self.subTest(source=label):
                self.assertIn("takes precedence over", content)
                precedence_idx = content.index("takes precedence over")
                # Precedence statement must live near/after the active-work case and
                # reference the done-work case as the one it out-ranks.
                self.assertLess(
                    content.index("record-blocked-with-active-work"),
                    content.index("record-blocked-with-done-work"),
                )
                self.assertGreater(
                    precedence_idx,
                    content.index("record-blocked-with-active-work"),
                )

    def test_new_classification_reuses_in_hand_data_no_new_scan(self) -> None:
        """P2-2: the record-vs-tasks compare reuses data already read in
        steps 2 (OP_GET_SHIPMENT_MCP) and 3 (manifest item statuses); it must
        not introduce a new scan."""
        for label, content, render in _sources():
            with self.subTest(source=label):
                self.assertIn("NO new scan", content)
                self.assertIn(render("{{OP_GET_SHIPMENT_MCP}}"), content)
                new_step_idx = content.index(_NEW_STEP_ANCHOR)
                # The new step must reference reuse of already-loaded/already-read data.
                self.assertTrue(
                    "already loaded" in content[new_step_idx : new_step_idx + 1500]
                    or "already read" in content[new_step_idx : new_step_idx + 1500]
                )

    def test_new_step_ordered_after_item_and_orphan_checks_before_report(self) -> None:
        """Pre-Mode ordering: the record-status classification step runs after
        the manifest-item check + orphan scan (it reuses their data) and
        before the report is produced."""
        for label, content, _ in _sources():
            with self.subTest(source=label):
                check_idx = content.index(_CHECK_ITEM_ANCHOR)
                orphan_idx = content.index(_ORPHAN_SCAN_ANCHOR)
                new_step_idx = content.index(_NEW_STEP_ANCHOR)
                report_idx = content.index(_PRODUCE_REPORT_ANCHOR)
                self.assertLess(check_idx, orphan_idx)
                self.assertLess(orphan_idx, new_step_idx)
                self.assertLess(new_step_idx, report_idx)

    def test_new_step_filters_to_task_artifacts_before_aggregating(self) -> None:
        """Review-fix (Copilot, PR #280): the manifest `items` list is untyped
        and may include the covering feature id (fallback-assembled manifest).
        The classification must filter to task-artifact entries -- reusing the
        artifact_type already read in step 3, no new read -- before
        aggregating active/done status, mirroring the Ship agent's existing
        task-artifact filter for its own intake early-warning scan."""
        for label, content, _ in _sources():
            with self.subTest(source=label):
                new_step_idx = content.index(_NEW_STEP_ANCHOR)
                region = content[max(0, new_step_idx - 2500) : new_step_idx + 2000]
                self.assertIn("task-artifact", region)
                self.assertIn("artifact_type", region)
                self.assertIn("covering feature", region)
                self.assertIn("templates/agents/_ship.agent.md.tmpl", region)

    def test_new_step_is_detect_and_report_no_auto_repair(self) -> None:
        for label, content, _ in _sources():
            with self.subTest(source=label):
                new_step_idx = content.index(_NEW_STEP_ANCHOR)
                region = content[new_step_idx : new_step_idx + 2500]
                self.assertIn("detect-and-report", region)
                self.assertIn("NO auto-repair", region)

    def test_gate_decision_halts_on_any_inconsistent_case_naming_ids(self) -> None:
        """Gate wiring: any non-consistent classification produces the
        existing HALT recommendation, naming the shipment id, record status,
        and conflicting task ids -- reusing the existing HALT path (no new
        terminal state)."""
        for label, content, _ in _sources():
            with self.subTest(source=label):
                gate_idx = content.index(_GATE_DECISION_ANCHOR, content.index(_NEW_STEP_ANCHOR))
                gate_region = content[gate_idx : gate_idx + 2000]
                self.assertIn("HALT — operator reconcile required", gate_region)
                self.assertIn("record-queued-with-active-work", gate_region)
                self.assertIn("record-blocked-with-active-work", gate_region)
                self.assertIn("record-blocked-with-done-work", gate_region)
                self.assertIn("shipment id", gate_region)
                self.assertIn("record", gate_region)
                self.assertIn("conflicting", gate_region)

    def test_quality_criteria_requires_record_status_classification(self) -> None:
        for label, content, _ in _sources():
            with self.subTest(source=label):
                quality_idx = content.index("## Quality Criteria")
                related_idx = content.index("## Related Artifacts")
                quality_region = content[quality_idx:related_idx]
                self.assertIn("shipment-record-status", quality_region)
                self.assertIn("record-consistent", quality_region)
                self.assertIn("precedence", quality_region)
                self.assertIn("no new scan", quality_region.lower())

    def test_active_and_done_record_status_explicitly_resolve_consistent(self) -> None:
        """Review-fix (P1): the Required Protocol step must give an explicit
        branch for record {{STATUS_ACTIVE}}/{{STATUS_DONE}} -- the normal
        record status at the skill's own mandatory Ship Step 6 invocation site
        -- rather than leaving it unmatched by the three named inconsistency
        bullets."""
        for label, content, render in _sources():
            with self.subTest(source=label):
                new_step_idx = content.index(_NEW_STEP_ANCHOR)
                region = content[new_step_idx : new_step_idx + 1200]
                self.assertIn(render("{{STATUS_ACTIVE}}"), region)
                self.assertIn("record-consistent", region)
                # The explicit ACTIVE/DONE branch must be scoped as "always" so it is
                # not confused with the queued/blocked exclusion branch below it.
                self.assertIn("always", region)

    def test_no_stray_unresolved_double_brace_tokens(self) -> None:
        """The new prose must only ever use the already-established
        {{STATUS_*}} / {{OP_*}} placeholder tokens, never a bespoke unresolved
        variable that the installer would not know how to resolve. The
        resolved copy must carry no placeholder at all."""
        for label, content, _ in _sources():
            new_step_idx = content.index(_NEW_STEP_ANCHOR)
            region = content[new_step_idx : new_step_idx + 2000]
            tokens = re.findall(r"\{\{[^}]+\}\}", region)
            if label == "resolved":
                with self.subTest(source=label):
                    self.assertEqual(tokens, [])
                continue
            for token in tokens:
                with self.subTest(source=label, token=token):
                    self.assertRegex(
                        token, r"^\{\{(STATUS|OP|BACKLOG_DIRECTORY)[A-Z_]*\}\}$"
                    )


if __name__ == "__main__":
    unittest.main()