"""Consumers of the shipment-reconcile ``linked_deliberation_disposition`` report.

Plan unit U6b (docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md):
post-merge consumers read the P-015 INV-12 Linked-Deliberation Disposition
report and never archive a retained deliberation on their own.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from autoharness.verify_workspace import PACK_ASSERTIONS

try:
    from _assertion_render import render_source
except ModuleNotFoundError:  # pragma: no cover - module path differs by runner
    from tests._assertion_render import render_source

try:
    from test_flat_manifest_closure_docs import POLICY_PARITY_ALLOWLIST
except ModuleNotFoundError:  # pragma: no cover - module path differs by runner
    from tests.test_flat_manifest_closure_docs import POLICY_PARITY_ALLOWLIST

_ROOT = Path(__file__).resolve().parents[1]
_SHIP_TEMPLATE = _ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
_OP_CLOSURE_INSTALLED = ".github/skills/operational-closure/SKILL.md"
_OP_CLOSURE_TEMPLATE = _ROOT / "templates" / "skills" / "operational-closure" / "SKILL.md.tmpl"
_OP_CLOSURE_MIRROR = _ROOT / _OP_CLOSURE_INSTALLED

_CLEANUP_ANCHOR = "* **Source artifact cleanup**"
_RETAINED_OUTCOMES = (
    "retained_read_error",
    "retained_engine_unverified",
    "retained_ambiguous",
    "retained_live_status",
    "retained_shared_reference",
    "retained_description_mention",
)

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
        # The withdrawn independent archive call is gone: the only remaining
        # mention of the item-archive tool is the prohibition itself.
        self.assertNotIn(
            "If it exists and is not already archived, call `backlogit_archive_item`",
            section,
        )
        self.assertEqual(section.count("backlogit_archive_item"), 1)

    def test_k1_report_locator_names_the_disposition_complete_close_report(self) -> None:
        section = _ship_template_step7()
        self.assertIn(
            "The report is the `linked_deliberation_disposition` field of this closure's "
            "`shipment-reconcile` close report under `{{BACKLOG_DIRECTORY}}/reconcile/`, "
            "taken from the run that returned `DISPOSITION_COMPLETE`",
            section,
        )

    def test_k1_unknown_outcome_and_unresolved_references_are_recorded_not_archived(
        self,
    ) -> None:
        section = _ship_template_step7()
        self.assertIn("any other outcome value: record it verbatim and never archive", section)
        self.assertIn(
            "When the ID is listed in the close report's `unresolved_references`, also "
            "copy that entry's `reason_code` verbatim",
            section,
        )
        self.assertIn("explicit manifest member is outside the disposition set (H10)", section)

    def test_k1_outcome_sub_bullets_are_siblings(self) -> None:
        raw = _SHIP_TEMPLATE.read_text(encoding="utf-8")
        start = raw.index(_STEP7_START)
        lines = raw[start : raw.index(_STEP7_END, start)].splitlines()
        heads = (
            "* outcome `archived`",
            "* any `retained_*` outcome",
            "* any other outcome value",
            "* the deliberation is absent from the report",
        )
        indents = set()
        for head in heads:
            matches = [line for line in lines if line.lstrip().startswith(head)]
            with self.subTest(head=head):
                self.assertEqual(len(matches), 1)
                indents.add(len(matches[0]) - len(matches[0].lstrip()))
        self.assertEqual(len(indents), 1, "outcome sub-bullets must share one indent")

    def test_k1_delib_count_counts_disposition_archives_not_ship_archives(self) -> None:
        section = _ship_template_step7()
        self.assertIn(
            "`{delib_count}` counts the report's `archived` outcomes (archived by the "
            "INV-12 disposition step, never by Ship)",
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

    def test_k1_missing_from_report_reason_code_is_absent_never_fabricated(self) -> None:
        section = _ship_template_step7()
        self.assertIn(
            "This outcome has no disposition-report entry, so its `reason_code` is "
            "recorded as absent — never invent a synthetic code — unless the ID is "
            "listed in the close report's `unresolved_references`.",
            section,
        )
        self.assertIn(
            "so it is never listed in `unresolved_references`, its `reason_code` is "
            "always recorded as absent",
            section,
        )
        self.assertIn(
            "a `skipped_not_in_disposition_report` outcome has no report entry, so its "
            "`reason_code` is recorded as absent unless the close report's "
            "`unresolved_references` lists the ID",
            section,
        )


def _cleanup_bullet(text: str, label: str) -> str:
    """The single Step 2 ``Source artifact cleanup`` bullet line of ``text``."""
    hits = [line for line in text.splitlines() if line.startswith(_CLEANUP_ANCHOR)]
    if len(hits) != 1:
        raise AssertionError(f"{label}: anchor {_CLEANUP_ANCHOR!r} matched {len(hits)} lines")
    return hits[0]


def _op_closure_variants() -> tuple[tuple[str, str], ...]:
    return (
        ("template", _OP_CLOSURE_TEMPLATE.read_text(encoding="utf-8")),
        ("mirror", _OP_CLOSURE_MIRROR.read_text(encoding="utf-8")),
    )


def _pack_assertion(key: str) -> dict:
    matches = [
        entry for entries in PACK_ASSERTIONS.values() for entry in entries if entry["key"] == key
    ]
    if len(matches) != 1:
        raise AssertionError(f"verify-workspace assertion {key!r} matched {len(matches)} entries")
    return matches[0]


class OperationalClosureRetainedOutcomesTests(unittest.TestCase):
    """195.016-T K-2: the Source artifact cleanup bullet lists every disposition outcome."""

    def test_k2_lists_retained_shared_reference_and_retained_read_error(self) -> None:
        for label, raw in _op_closure_variants():
            with self.subTest(surface=label):
                bullet = _cleanup_bullet(raw, label)
                self.assertIn("`retained_shared_reference`", bullet)
                self.assertIn("`retained_read_error`", bullet)

    def test_k2_lists_every_retained_outcome_and_missing_from_report(self) -> None:
        for label, raw in _op_closure_variants():
            bullet = _cleanup_bullet(raw, label)
            for outcome in (*_RETAINED_OUTCOMES, "skipped_not_in_disposition_report"):
                with self.subTest(surface=label, outcome=outcome):
                    self.assertIn(f"`{outcome}`", bullet)

    def test_k2_outcomes_are_copied_from_the_report_never_rederived(self) -> None:
        for label, raw in _op_closure_variants():
            with self.subTest(surface=label):
                bullet = _cleanup_bullet(raw, label)
                self.assertIn(
                    "are copied from the shipment's `linked_deliberation_disposition` report",
                    bullet,
                )
                self.assertIn("never re-derived", bullet)
                self.assertIn("an unknown `reason_code` is recorded verbatim", bullet)
                self.assertIn(
                    "a `skipped_not_in_disposition_report` outcome has no report entry, "
                    "so its `reason_code` is recorded as absent — never invented — unless "
                    "the close report's `unresolved_references` lists the ID, in which "
                    "case that entry's `reason_code` is copied verbatim (an explicit "
                    "manifest member is never listed there, H10)",
                    bullet,
                )
                self.assertIn(
                    "neither Ship nor the disposition step archives a `retained_*` or "
                    "`skipped_not_in_disposition_report` deliberation",
                    bullet,
                )

    def test_k2_deliberation_outcomes_use_the_report_literals(self) -> None:
        for label, raw in _op_closure_variants():
            with self.subTest(surface=label):
                bullet = _cleanup_bullet(raw, label)
                self.assertIn(
                    "otherwise it is the report's literal outcome — `archived`, "
                    "`already-archived`,",
                    bullet,
                )
                self.assertIn(
                    "A `source_stash_id` outcome is one of: archived, skipped because it "
                    "was already archived, skipped because it was not found, or `none`",
                    bullet,
                )
                self.assertIn(
                    "only the INV-12 disposition step archives a deliberation", bullet
                )


class VerifyWorkspaceTokensPresentTests(unittest.TestCase):
    """195.016-T K-3: the verify-workspace ``must_contain`` tokens stay present."""

    def test_k3_ship_source_artifact_cleanup_tokens_in_ship_template(self) -> None:
        assertion = _pack_assertion("ship_source_artifact_cleanup")
        self.assertEqual(assertion["path"], ".github/agents/_ship.agent.md")
        self.assertTrue(assertion["must_contain"])
        raw = _SHIP_TEMPLATE.read_text(encoding="utf-8")
        for token in assertion["must_contain"]:
            with self.subTest(token=token):
                self.assertIn(token, raw)

    def test_k3_closure_source_artifact_cleanup_tokens_in_op_closure_pair(self) -> None:
        assertion = _pack_assertion("closure_source_artifact_cleanup")
        self.assertEqual(assertion["path"], _OP_CLOSURE_INSTALLED)
        self.assertTrue(assertion["must_contain"])
        for label, raw in _op_closure_variants():
            for token in assertion["must_contain"]:
                with self.subTest(surface=label, token=token):
                    self.assertIn(token, raw)


class OperationalClosureRenderedRegionParityTests(unittest.TestCase):
    """195.016-T K-4: the rendered template matches the mirror over the edited bullet."""

    def test_k4_source_artifact_cleanup_rendered_region_parity(self) -> None:
        rendered = render_source(_OP_CLOSURE_INSTALLED)
        for template_text, mirror_text in POLICY_PARITY_ALLOWLIST:
            rendered = rendered.replace(template_text, mirror_text)
        mirror = _OP_CLOSURE_MIRROR.read_text(encoding="utf-8")
        self.assertEqual(
            _cleanup_bullet(mirror, "mirror"),
            _cleanup_bullet(rendered, "rendered template"),
        )

    def test_k4_cleanup_bullet_helper_detects_drift(self) -> None:
        with self.assertRaisesRegex(AssertionError, "matched 0 lines"):
            _cleanup_bullet("* **Other** — text\n", "demo")
        with self.assertRaisesRegex(AssertionError, "matched 2 lines"):
            _cleanup_bullet(f"{_CLEANUP_ANCHOR} — a\n{_CLEANUP_ANCHOR} — b\n", "demo")


if __name__ == "__main__":
    unittest.main()
