"""Regression coverage for the P-015 / shipment-reconcile cascade-close
`archived_ids` two-set `allowed_ids` / `required_ids` gate (155-S / 147-F).

This is a repo-side CONTRACT TEST over the template text, matching the
established `tests/test_shipment_reconcile_*.py` pattern: the cascade-close
gate is documentation-as-contract (there is no standalone Python
implementation of the Cascade Close Sub-Procedure itself -- the Ship agent
and the `shipment-reconcile` skill execute it directly from the prose), so
correctness is pinned by asserting the load-bearing textual invariants are
present, worded as independent conditions, and not silently mergeable or
removable.

See:
* `templates/policies/workflow-policies.md.tmpl` -- P-015 fully-covered-root
  exception item 7 (corrected) and the new 1.21.0 changelog row.
* `templates/skills/shipment-reconcile/SKILL.md.tmpl` -- Safe-Close Mode
  Step 0(b)/(c) (declared-status snapshot) and the Cascade Close
  Sub-Procedure (pre-archived preamble + steps 1-6).
* `docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-plan.md`
  and its hardening (A1-A4) / review docs for the normative contract this
  module pins.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SKILL_TEMPLATE = _ROOT / "templates" / "skills" / "shipment-reconcile" / "SKILL.md.tmpl"
_POLICY_TEMPLATE = _ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"

_HALT_UNEXPECTED = "cascade archived unexpected artifact"
_HALT_MISSING = "cascade did not archive required artifact"

# Byte-identical baseline of the pre-existing 1.19.0 changelog row -- MUST
# NOT be edited or deleted by the 1.21.0 correction row (147.001-T).
_CHANGELOG_1_19_0 = (
    "| 1.19.0  | {{DATE}}     | Updated P-015    | Verified fully-covered-root "
    "exception item 7: a pre-archived manifest member does not disqualify the "
    "cascade close path — it satisfies coverage/root checks the same as a "
    "queued member, does not authorize safe-close fallback, and remains "
    "included in the idempotent cascade operation's `archived_ids` result "
    "under the unchanged exact-match post-condition |"
)


def _skill_content() -> str:
    return _SKILL_TEMPLATE.read_text(encoding="utf-8")


def _policy_content() -> str:
    return _POLICY_TEMPLATE.read_text(encoding="utf-8")


def _flatten(text: str) -> str:
    """Collapse newlines/indentation so a phrase that wraps across lines in
    the authored markdown can still be matched as a contiguous substring."""
    return re.sub(r"\s+", " ", text)


class CascadeCloseTwoSetGateStructuralTests(unittest.TestCase):
    """Structural assertions (A2/A3/A4-derived) over the skill template."""

    def test_both_distinct_halt_strings_present(self) -> None:
        # A2 (BINDING): deleting either halt string must break a test rather
        # than silently widening the gate.
        content = _skill_content()
        self.assertIn(_HALT_UNEXPECTED, content)
        self.assertIn(_HALT_MISSING, content)
        self.assertNotEqual(_HALT_UNEXPECTED, _HALT_MISSING)

    def test_two_conditions_are_independently_labelled_and_not_merged(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("Unexpected-artifact check", content)
        self.assertIn("Missing-required-artifact check", content)
        self.assertIn("Two separately-labelled, independently-failing conditions", content)
        self.assertIn(
            "Neither may be evaluated as a precondition of the other, and the two "
            "MUST NOT be merged into a single combined test",
            content,
        )
        # A2 cites the concrete same-session precedent that justifies the rule.
        self.assertIn("B57F9E24", content)

    def test_shipment_record_is_unconditional_member_of_required_ids(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "**Compute `required_ids`** = the shipment record (**unconditionally** "
            "— never omitted, and never derived only by iterating Step 0(b)'s "
            "manifest-task entries)",
            content,
        )

    def test_allowed_ids_defined_via_step_0c_qualifying_feature_determination(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "every qualifying feature member identified by Step 0(c)'s own "
            "classification",
            content,
        )
        self.assertIn("independent of *how* the engine happens to transition", content)

    def test_qualifying_feature_statuses_captured_after_0c_before_invocation(self) -> None:
        content = _flatten(_skill_content())
        # Step 0(c) extension: captured immediately after qualifying features
        # are identified, and explicitly before the cascade invocation.
        self.assertIn(
            "When this classification identifies qualifying feature members",
            content,
        )
        self.assertIn(
            "extend the same pre-close declared-status snapshot from (b) — "
            "still **before** the cascade invocation, never after",
            content,
        )
        # Step 3's required_ids computation also states both snapshot parts
        # (manifest tasks from (b), qualifying features extended in (c)) are
        # captured before the step 1 invocation.
        self.assertIn("extended by Step 0(c) for qualifying feature members", content)
        self.assertIn("both captured", content)
        self.assertIn("**before** this step 1 invocation", content)

    def test_location_alone_is_not_declared_status(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "Declared `status` is read from the record's own frontmatter "
            "`status` field — never inferred from, nor substituted by, "
            "which of `queue/`/`archive/` currently holds the record",
            content,
        )
        self.assertIn(
            "A record residing in `{{BACKLOG_DIRECTORY}}/archive/` while "
            "declaring `status: done` is **not** truly archived; only a "
            "declared `status: archived` counts as truly archived",
            content,
        )
        # Restated in the Cascade Close Sub-Procedure preamble too (this is
        # the "control arm" confusion that invalidated the 2026-08-18 spike).
        self.assertIn("This location label is **descriptive only**", content)

    def test_step_0b_snapshot_timing_warning_mirrors_parent_id_precedent(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "for the identical reason already stated for `parent_id`: "
            "`status` is the very field the cascade mutates",
            content,
        )
        self.assertIn("Never a freshly-read or assumed value", content)

    def test_preserved_checks_textually_intact(self) -> None:
        content = _flatten(_skill_content())
        # returned_ids empty check (step 2) -- unchanged.
        self.assertIn(
            "cascade returned non-empty returned_ids, classifier/engine",
            content,
        )
        # parent_id preservation (step 4) -- unchanged.
        self.assertIn("cascade cleared parent_id on {id}, revert required", content)
        # no-substitution rule -- unchanged.
        self.assertIn("No-substitution rule", content)
        # protected-set / pre-archived-manifest-members-only scoping -- unchanged.
        self.assertIn("This tolerance applies to **manifest members only**", content)

    def test_gate_decision_references_both_set_relations(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("empty (no unexpected artifact archived)", content)
        self.assertIn("empty (no required artifact left unarchived)", content)
        self.assertNotIn("archived_ids` matches exactly", content)

    def test_no_live_guidance_anywhere_still_asserts_exact_match(self) -> None:
        """Copilot review (PR #407): a live '## Quality Criteria' bullet
        previously survived the step-3/preamble rewrite and kept asserting
        the withdrawn exact-match claim as current execution guidance, even
        though the Cascade Close Sub-Procedure text itself had already been
        corrected. Guard the whole document (not just the sub-procedure
        section) against any surviving "matches ... exactly" /
        "idempotent ... returns it in `archived_ids`" phrasing tied to
        archived_ids, wherever it appears."""
        content = _flatten(_skill_content())
        self.assertNotIn("archived_ids` matches the manifest exactly", content)
        self.assertNotIn(
            "the cascade operation is idempotent and still returns it in "
            "`archived_ids`",
            content,
        )
        # The Quality Criteria bullet must reference the two-set gate.
        quality_idx = content.index("## Quality Criteria")
        quality_section = content[quality_idx:]
        self.assertIn("allowed_ids", quality_section)
        self.assertIn("required_ids", quality_section)

    def test_report_records_allowed_required_and_both_differences(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("`allowed_ids`, `required_ids`, and both set differences", content)
        self.assertIn(
            "(`archived_ids - allowed_ids` and `required_ids - archived_ids`)",
            content,
        )
        # F1 (review): a vacuous required_ids must be visible, not silent.
        self.assertIn("visible in the report rather than silent", content)

    def test_already_archived_allowed_member_inclusion_or_omission_both_pass(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("MAY be included in or omitted from", content)
        self.assertIn("neither outcome fails either check", content)
        # Copilot review (PR #407): the tolerance must be explicitly scoped
        # to non-shipment allowed_ids members and must not silently cover
        # the shipment record, which is unconditionally required regardless
        # of its own pre-close declared status.
        self.assertIn("non-shipment", content)
        self.assertIn("never extends to the shipment record itself", content)
        self.assertIn(
            "remains unconditionally required regardless of its own "
            "pre-close declared status",
            content,
        )

    def test_supersession_note_present_at_point_of_change(self) -> None:
        content = _skill_content()
        self.assertIn("SUPERSESSION NOTE (155-S, 2026-08-24)", content)
        self.assertIn("WITHDRAWN", content)
        # No stray {{DATE}} placeholder introduced in the mixed-role-detection
        # scanned region (established placeholder-family invariant, see
        # tests/test_shipment_reconcile_mixed_role_detection.py).
        self.assertNotIn("{{DATE}}", content)

    def test_archived_ids_is_transition_log_not_manifest_echo(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("`archived_ids` is a transition log, not a manifest echo.", content)
        self.assertIn("archiveItems()", content)


class CascadeCloseTwoSetGatePolicyTests(unittest.TestCase):
    """Structural assertions over the P-015 policy template correction."""

    def test_no_surviving_full_set_equality_claim(self) -> None:
        content = _policy_content()
        # The literal phrase must not appear anywhere in the policy template.
        self.assertNotIn("nothing more, nothing less", content)
        # "must never be relaxed" may appear exactly once: quoted, inside the
        # withdrawal note, immediately followed by an explicit WITHDRAWN
        # marker -- never as a currently-asserted operative rule.
        occurrences = [
            m.start() for m in re.finditer(re.escape("must never be relaxed"), content)
        ]
        self.assertEqual(len(occurrences), 1)
        idx = occurrences[0]
        trailing = content[idx : idx + 400]
        self.assertIn("WITHDRAWN", trailing)

    def test_item_7_points_to_two_set_gate_as_live_guard(self) -> None:
        content = _flatten(_policy_content())
        self.assertIn(
            "The live fail-closed guard over this result is the two-set "
            "`allowed_ids` / `required_ids` gate",
            content,
        )
        self.assertIn("archived_ids` is a **transition log**", content)

    def test_preserved_pre_archived_tolerance_clauses(self) -> None:
        content = _flatten(_policy_content())
        self.assertIn(
            "does not disqualify the cascade close path, does not "
            "constitute an unresolved precondition, and does not authorize "
            "falling back to the default single-artifact safe-close "
            "procedure",
            content,
        )
        self.assertIn("no-substitution rule applies identically", content)

    def test_supersession_note_present(self) -> None:
        content = _policy_content()
        self.assertIn("SUPERSESSION NOTE (155-S", content)
        self.assertIn("That claim was false and is WITHDRAWN.", content)

    def test_changelog_1_19_0_row_preserved_byte_identical(self) -> None:
        content = _policy_content()
        self.assertIn(_CHANGELOG_1_19_0, content)

    def test_new_correction_changelog_row_present(self) -> None:
        content = _policy_content()
        self.assertIn("Corrected P-015", content)
        row_match = re.search(r"^\| 1\.21\.0 .*\|$", content, re.MULTILINE)
        self.assertIsNotNone(row_match)
        row = row_match.group(0)
        self.assertIn("allowed_ids", row)
        self.assertIn("required_ids", row)
        self.assertIn("1.19.0 row above", row)

    def test_changelog_correction_row_is_new_not_a_rewrite(self) -> None:
        content = _policy_content()
        idx_1_19 = content.index("| 1.19.0")
        idx_1_20 = content.index("| 1.20.0")
        idx_1_21 = content.index("| 1.21.0")
        # Ordering preserved: 1.19.0 precedes 1.20.0 precedes the new 1.21.0
        # correction row -- nothing was inserted between/rewritten in place.
        self.assertLess(idx_1_19, idx_1_20)
        self.assertLess(idx_1_20, idx_1_21)


class CascadeCloseTwoSetGateScenarioTests(unittest.TestCase):
    """Encodes the eight mandatory scenarios (147.003-T) as assertions that
    the corresponding textual branch of the two-set gate contract exists and
    is worded to produce that outcome. Since the Cascade Close Sub-Procedure
    is executed directly from this prose (no standalone Python gate function
    exists for it), each scenario is pinned by asserting the specific clause
    that determines its outcome is present and correctly scoped.
    """

    def test_scenario_1_all_new_members_gate_passes(self) -> None:
        # When no allowed member was truly archived pre-close, required_ids
        # equals allowed_ids minus nothing (every member is "not truly
        # archived"), so a cascade that archives everything satisfies both
        # set relations trivially. Pinned by the required_ids definition
        # itself operating over "every other allowed_ids member NOT truly
        # `status: archived`".
        content = _flatten(_skill_content())
        self.assertIn("every other", content)
        self.assertIn("that was **not** truly `status: archived`", content)

    def test_scenario_2_omitted_truly_pre_archived_tasks_gate_passes(self) -> None:
        content = _flatten(_skill_content())
        # A truly pre-archived member is excluded from required_ids, so its
        # absence from archived_ids does not trigger the missing-required
        # halt. This is exactly what the withdrawn full-set-equality claim
        # got wrong.
        self.assertIn(
            "A manifest member that was already truly `status: archived` "
            "before the call therefore has no transition to report and is "
            "**correctly absent** from `archived_ids`",
            content,
        )
        self.assertIn("this is expected engine behavior", content)

    def test_scenario_3_included_pre_archived_member_still_passes(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("MAY be included in or omitted from", content)
        self.assertIn("neither outcome fails either check", content)

    def test_scenario_4_missing_required_id_halts(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("if `required_ids - archived_ids`", content)
        self.assertIn(_HALT_MISSING, content)

    def test_scenario_5_unexpected_id_halts(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("if `archived_ids - allowed_ids`", content)
        self.assertIn(_HALT_UNEXPECTED, content)

    def test_scenario_6_incorrect_persisted_final_state_halts(self) -> None:
        # The preserved parent_id-preservation check (step 4) is the
        # persisted-final-state guard this scenario exercises; it must
        # remain textually intact and independent of the two-set gate.
        content = _flatten(_skill_content())
        self.assertIn("confirm `parent_id` is unchanged from the pre-close", content)
        self.assertIn("cascade cleared parent_id on {id}, revert required", content)

    def test_scenario_7_archive_dir_status_done_is_not_truly_archived(self) -> None:
        # MANDATORY scenario: pins the exact confusion that invalidated the
        # 2026-08-18 spike (location vs. declared status).
        content = _flatten(_skill_content())
        self.assertIn(
            "A record residing in `{{BACKLOG_DIRECTORY}}/archive/` while "
            "declaring `status: done` is **not** truly archived",
            content,
        )
        # Restated identically in both Step 0(b) and the Cascade Close
        # Sub-Procedure preamble.
        occurrences = content.count("declaring `status: done` is **not** truly archived")
        self.assertGreaterEqual(occurrences, 2)

    def test_scenario_8_post_close_read_would_pass_but_step_0b_snapshot_halts(self) -> None:
        # AMENDMENT A4 (BINDING): pins the snapshot-timing failure mode --
        # a post-close status read would report "archived" for everything
        # the cascade just archived (collapsing required_ids to empty), so
        # the snapshot MUST be Step 0(b)/(c), never a fresh post-close read.
        content = _flatten(_skill_content())
        self.assertIn(
            "would report `archived` for everything the cascade just archived",
            content,
        )
        self.assertIn("collapsing `required_ids`", content)
        self.assertIn("silently disabling the completeness check entirely", content)


class CascadeCloseFrontmatterAndVariableTests(unittest.TestCase):
    """147.002-T acceptance: frontmatter valid; no unresolved {{...}} beyond
    legitimate template variables introduced by this correction."""

    def test_skill_template_frontmatter_parses(self) -> None:
        import yaml

        raw = _skill_content()
        self.assertTrue(raw.startswith("---\n"))
        end = raw.index("\n---", 4)
        frontmatter = raw[4:end]
        parsed = yaml.safe_load(frontmatter)
        self.assertIsInstance(parsed, dict)

    def test_policy_template_frontmatter_parses(self) -> None:
        import yaml

        raw = _policy_content()
        self.assertTrue(raw.startswith("---\n"))
        end = raw.index("\n---", 4)
        frontmatter = raw[4:end]
        parsed = yaml.safe_load(frontmatter)
        self.assertIsInstance(parsed, dict)

    def test_no_new_placeholder_families_introduced_in_skill_template(self) -> None:
        # Mirrors tests/test_shipment_reconcile_mixed_role_detection.py's
        # established-placeholder-family invariant for the region this
        # correction touches (Safe-Close Mode Step 0 through the end of the
        # Cascade Close Sub-Procedure).
        content = _skill_content()
        start = content.index("### Safe-Close Mode")
        end = content.index("### Mixed-Role Detection Mode")
        region = content[start:end]
        for token in re.findall(r"\{\{[^}]+\}\}", region):
            with self.subTest(token=token):
                self.assertRegex(
                    token,
                    r"^\{\{(STATUS|OP|BACKLOG_DIRECTORY|SUFFIX)[A-Z_]*\}\}$",
                )


if __name__ == "__main__":
    unittest.main()
