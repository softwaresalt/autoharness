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
                self.assertIn("a `retained_*` deliberation is never archived", bullet)


class VerifyWorkspaceTokensPresentTests(unittest.TestCase):
    """195.016-T K-3: the verify-workspace ``must_contain`` tokens stay present."""

    def test_k3_ship_source_artifact_cleanup_tokens_in_ship_template(self) -> None:
        assertion = _pack_assertion("ship_source_artifact_cleanup")
        self.assertEqual(assertion["path"], ".github/agents/_ship.agent.md")
        raw = _SHIP_TEMPLATE.read_text(encoding="utf-8")
        for token in assertion["must_contain"]:
            with self.subTest(token=token):
                self.assertIn(token, raw)

    def test_k3_closure_source_artifact_cleanup_tokens_in_op_closure_pair(self) -> None:
        assertion = _pack_assertion("closure_source_artifact_cleanup")
        self.assertEqual(assertion["path"], _OP_CLOSURE_INSTALLED)
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
        self.assertNotEqual(
            _cleanup_bullet(f"{_CLEANUP_ANCHOR} — template\n", "a"),
            _cleanup_bullet(f"{_CLEANUP_ANCHOR} — mirror\n", "b"),
        )


if __name__ == "__main__":
    unittest.main()
