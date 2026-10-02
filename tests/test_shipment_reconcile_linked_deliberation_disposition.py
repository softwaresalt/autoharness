"""Contract tests for the shipment-reconcile Linked-Deliberation Disposition
step (P-015 INV-12) and its hand-offs, post-mode coverage and scenario matrix
(shipment 206-S, feature 200-F, slice 5 of 6 of umbrella 195-F).

The disposition step is documentation-as-contract: the Ship agent and the
``shipment-reconcile`` skill execute it from the prose, and the pure planner
``compute_linked_deliberation_disposition`` in
``src/autoharness/gates/shipment_closure.py`` is tested separately in
``tests/test_linked_deliberation_disposition_planner.py``. This module pins
the load-bearing skill text in both the product template and the installed
dogfood mirror, and proves the template renders the same edited regions as
the mirror.

Plan: ``docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md``
(units U5a and U5b). Decision:
``docs/decisions/2026-09-29-backlogit-1-11-cascade-linked-deliberation-alignment-deliberation.md``.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SKILL_TEMPLATE = _ROOT / "templates" / "skills" / "shipment-reconcile" / "SKILL.md.tmpl"
_SKILL_MIRROR = _ROOT / ".github" / "skills" / "shipment-reconcile" / "SKILL.md"

_SECTION_HEADING = "### Linked-Deliberation Disposition (P-015 INV-12)"
_NEXT_HEADING = "### Mixed-Role Detection Mode"
_HALT_DISPOSITION = "HALT — linked-deliberation disposition failed {id}"
# The Step 0(c) linked-deliberation matcher literal. The disposition step
# references it by name only, so this slice must not add an occurrence.
_MATCHER_LITERAL = r"\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b"
_OUTCOMES = (
    "archived",
    "already-archived",
    "retained_read_error",
    "retained_ambiguous",
    "retained_engine_unverified",
    "retained_live_status",
    "retained_shared_reference",
    "retained_description_mention",
)


def _flatten(text: str) -> str:
    """Collapse whitespace so a phrase wrapped across lines still matches."""
    return re.sub(r"\s+", " ", text)


def _variants() -> tuple[tuple[str, str], ...]:
    return (
        ("template", _SKILL_TEMPLATE.read_text(encoding="utf-8")),
        ("mirror", _SKILL_MIRROR.read_text(encoding="utf-8")),
    )


def _section(raw: str) -> str:
    """The raw text of the Linked-Deliberation Disposition section."""
    start = raw.index(_SECTION_HEADING)
    return raw[start : raw.index(_NEXT_HEADING, start)]


def _step(section: str, number: int) -> str:
    """One numbered step of the disposition section, flattened."""
    start = section.index(f"\n{number}. **")
    following = section.find(f"\n{number + 1}. **", start)
    end = following if following != -1 else len(section)
    return _flatten(section[start:end])


class DispositionSectionAssertionsI(unittest.TestCase):
    """200.002-T: scenarios H-a, H-h and H-k."""

    def test_h_a_section_exists_in_template_and_mirror(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                self.assertEqual(raw.count(_SECTION_HEADING), 1)
                # The section sits after the Cascade Close Sub-Procedure,
                # where both close paths hand off to it, and before the
                # Mixed-Role Detection Mode section.
                self.assertLess(
                    raw.index("### Cascade Close Sub-Procedure"),
                    raw.index(_SECTION_HEADING),
                )
                self.assertLess(raw.index(_SECTION_HEADING), raw.index(_NEXT_HEADING))

    def test_h_h_engine_unverified_means_no_mutation(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                plan = _step(_section(raw), 1)
                self.assertIn("**Engine UNVERIFIED means no mutation.**", plan)
                self.assertIn("`retained_engine_unverified`", plan)
                self.assertIn("nothing is mutated, on every close path", plan)
                self.assertIn("`ENGINE_SEMANTICS_UNVERIFIED`", plan)

    def test_h_k_planner_is_cited_as_plan_source(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                plan = _step(_section(raw), 1)
                self.assertIn("`compute_linked_deliberation_disposition(", plan)
                self.assertIn("`src/autoharness/gates/shipment_closure.py`", plan)
                self.assertIn(
                    "Other workspaces apply the same stated rules and first-match "
                    "precedence over the eight `LinkedDeliberationOutcome` values",
                    plan,
                )


class DispositionSectionAssertionsII(unittest.TestCase):
    """200.003-T: scenarios H-e, H-g and H-l."""

    def test_h_e_disposition_baseline_definition(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                baseline = _step(_section(raw), 2)
                self.assertIn("**Disposition baseline.**", baseline)
                self.assertIn("(i) the path-specific set", baseline)
                self.assertIn("safe-close observation-set fingerprints", baseline)
                self.assertIn("out-of-manifest descendant fingerprints", baseline)
                self.assertIn("(ii) the disposition snapshot", baseline)
                self.assertRegex(
                    baseline,
                    r"\(iii\) a pre-disposition `git status --porcelain -- "
                    r"\"[^\"]+/\"` capture",
                )
                self.assertIn(
                    "minus the `closure_scope(S)` IDs this run already archived",
                    baseline,
                )

    def test_h_g_allowed_side_effect_paths_exclude_stash_files(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                baseline = _step(_section(raw), 2)
                self.assertIn("`v1.11.0` `internal/core/archive.go`", baseline)
                self.assertIn("the target deliberation's own queue→archive move", baseline)
                self.assertIn(
                    "frontmatter keys `status`, `archived_status`, and `archived_from`",
                    baseline,
                )
                self.assertRegex(baseline, r"gitignored item event log \(`[^`]+/logs/`\)")
                self.assertRegex(baseline, r"index \(`[^`]+/\*\.db\*`\)")
                self.assertIn("lock and hook-queue files", baseline)
                self.assertRegex(
                    baseline,
                    r"`ArchiveItem` does \*\*not\*\* write `[^`]+/stash\.jsonl` or "
                    r"`[^`]+/archive/stash\.jsonl`",
                )
                self.assertIn(
                    "any change there, or to any other path, violates the "
                    "disposition baseline",
                    baseline,
                )

    def test_h_l_matcher_referenced_by_name_not_restated(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                section = _section(raw)
                self.assertIn("the Step 0(c) matcher", _flatten(section))
                self.assertNotIn(_MATCHER_LITERAL, section)
                # The plan text (U5a step 1) says the skill-wide count "stays
                # 2"; 199.007-T (205-S) later removed the second literal from a
                # Quality Criteria bullet, so the skill-wide count this slice
                # must leave unchanged is 1: the Step 0(c) snapshot definition.
                self.assertEqual(raw.count(_MATCHER_LITERAL), 1)


if __name__ == "__main__":
    unittest.main()
