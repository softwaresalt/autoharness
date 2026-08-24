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

    def test_shipment_record_and_qualifying_feature_are_unconditional_required_ids_members(
        self,
    ) -> None:
        # PR #407 review (threads PRRT_kwDORzpWpM6bzlFl /
        # PRRT_kwDORzpWpM6bzlGL): a pre-archived qualifying feature member
        # cannot use the same tolerance as a pre-archived task or linked
        # deliberation, because Backlogit's ShipShipment forces every
        # explicit qualifying feature member to status: done first
        # (unconditionally, regardless of its own pre-close status) before
        # collectArchiveCandidateIDs ever runs -- so the shipment record and
        # every qualifying feature member are BOTH unconditional
        # required_ids members.
        content = _flatten(_skill_content())
        self.assertIn(
            "**Compute `required_ids`** = the shipment record and every "
            "qualifying feature member (**both unconditionally** — never "
            "omitted, and never conditioned on either artifact's own "
            "pre-close declared status)",
            content,
        )
        self.assertIn(
            "every other `allowed_ids` member (a manifest task item, or a "
            "qualifying feature member's validated linked deliberation) "
            "that was **not** truly `status: archived`",
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
        # Step 3's required_ids computation also states all three snapshot
        # parts (manifest tasks from (b), qualifying features and their
        # linked deliberations extended in (c) -- 155-S/PR #407) are
        # captured before the step 1 invocation.
        self.assertIn("extended by Step 0(c) for qualifying feature members", content)
        self.assertIn("all captured", content)
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

    def test_tolerance_list_excludes_bare_qualifying_feature_member(self) -> None:
        # PR #407 review (thread PRRT_kwDORzpWpM6bzlFl): a bare qualifying
        # feature member must no longer be offered as an eligible-for-
        # tolerance option in the parenthetical list -- only a manifest
        # task item or a qualifying feature member's *validated linked
        # deliberation* may be already truly archived pre-close.
        content = _flatten(_skill_content())
        self.assertIn(
            "(a manifest task item, or a qualifying feature member's "
            "validated linked deliberation — never the qualifying feature "
            "member itself",
            content,
        )
        self.assertNotIn(
            "(a manifest task item, a qualifying feature member, or a "
            "qualifying feature member's validated linked deliberation)",
            content,
        )

    def test_tolerance_never_extends_to_qualifying_feature_member(self) -> None:
        # PR #407 review (thread PRRT_kwDORzpWpM6bzlFl): Backlogit's own
        # ShipShipment (internal/core/shipment_lifecycle.go) unconditionally
        # forces every explicit qualifying feature member through
        # setArtifactStatus(..., StatusDone, ...) BEFORE
        # collectArchiveCandidateIDs runs, regardless of that feature's own
        # pre-close declared status -- including an already truly
        # status: archived one. By the time collectArchiveCandidateIDs
        # loads the feature its status is always done, never still
        # archived, so it is always appended to the archive candidate list.
        # A qualifying feature member can therefore never be "correctly
        # absent" from archived_ids the way a truly pre-archived task or
        # linked deliberation can.
        content = _flatten(_skill_content())
        self.assertIn(
            "Nor does it extend to a qualifying feature member itself",
            content,
        )
        self.assertIn("PRRT_kwDORzpWpM6bzlFl", content)
        self.assertIn("setArtifactStatus", content)
        self.assertIn("models.StatusDone", content)
        self.assertIn("collectArchiveCandidateIDs", content)
        self.assertIn(
            "can therefore never be \"correctly absent\" from `archived_ids`",
            content,
        )
        self.assertIn(
            "unconditional `required_ids` member exactly like the shipment "
            "record",
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


class CascadeCloseLinkedDeliberationAllowanceTests(unittest.TestCase):
    """PR #407 review (threads PRRT_kwDORzpWpM6bo8m2 /
    PRRT_kwDORzpWpM6bpEZc): a qualifying feature member's live linked
    deliberation is archived by Backlogit's own
    `collectArchiveCandidateIDs`/`linkedDeliberationIDs` before
    `archiveItems` builds `archived_ids`, so the two-set gate must
    allow-list it (via Step 0(c)'s engine-defined,
    existence-and-`artifact_type`-validated collection) rather than
    deterministically tripping the unexpected-artifact check after the
    cascade has already mutated the backlog. Companion fix: the P-015
    policy's `required_ids` summary must state the shipment's unconditional
    requirement identically to the skill.
    """

    def test_step_0c_extends_snapshot_with_linked_deliberations(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("Linked-deliberation snapshot extension", content)
        self.assertIn("collectArchiveCandidateIDs", content)
        self.assertIn("linkedDeliberationIDs", content)

    def test_linked_deliberation_torn_state_halts_fail_closed(self) -> None:
        # PR #407 follow-up review round: the linked-deliberation snapshot
        # must carry forward Step 0(b)'s torn-state (both queue/ and
        # archive/) / missing-record halt discipline, never guessing which
        # copy is authoritative before the destructive cascade invocation.
        content = _flatten(_skill_content())
        self.assertIn(
            "resolve its record location the identical way Step 0(b) "
            "resolves a manifest task item",
            content,
        )
        self.assertIn("RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS", content)
        self.assertIn("RECONCILE_FAIL_SNAPSHOT_MISSING", content)
        self.assertIn(
            "never compute `required_ids` from an arbitrary copy before "
            "the destructive cascade invocation",
            content,
        )

    def test_linked_deliberation_sources_match_engine_exactly(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("custom_fields.source_deliberation_id", content)
        self.assertIn(
            "any deliberation ID embedded in the feature's description",
            content,
        )
        self.assertIn("any deliberation the feature references", content)

    def test_linked_deliberation_requires_existence_and_artifact_type(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "restricted to IDs that resolve to an **existing** artifact "
            "whose own `artifact_type` is `deliberation`",
            content,
        )

    def test_no_blanket_allowance_for_arbitrary_ids(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "never any other ID, and never an ID that fails either check",
            content,
        )
        self.assertIn(
            "without a blanket allowance for arbitrary IDs",
            content,
        )
        # Quality Criteria echo must carry the same never-blanket-allowance
        # framing, not just the sub-procedure prose.
        quality_idx = content.index("## Quality Criteria")
        quality_section = content[quality_idx:]
        self.assertIn("never a blanket allowance for arbitrary IDs", quality_section)

    def test_allowed_ids_bullet_includes_linked_deliberations(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "every validated linked deliberation ID of each qualifying "
            "feature member captured by Step 0(c)'s linked-deliberation "
            "snapshot extension above",
            content,
        )

    def test_required_ids_bullet_extended_for_linked_deliberations(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "extended by Step 0(c) for qualifying feature members and "
            "their validated linked deliberations",
            content,
        )

    def test_non_shipment_tolerance_covers_linked_deliberation_and_illustrates_147f(
        self,
    ) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "a qualifying feature member's validated linked deliberation",
            content,
        )
        self.assertIn("147-F", content)
        self.assertIn("027-DL", content)

    def test_report_step_records_linked_deliberation_ids(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "qualifying feature IDs, and their validated linked "
            "deliberation IDs",
            content,
        )

    def test_linked_deliberation_matcher_specified_exactly(self) -> None:
        # PR #407 review (thread PRRT_kwDORzpWpM6byLno): the description/
        # references sources must cite Backlogit's own exact regex matcher
        # (`internal/core.deliberationIDPattern`, verified against the
        # installed backlogit.exe binary) rather than a broader "any
        # embedded deliberation ID" reading. An agent applying the broader
        # wording could add an ID the engine will never archive, poisoning
        # `required_ids` and causing a false halt after the destructive
        # cascade has already run. `custom_fields.source_deliberation_id`
        # must likewise be specified as a complete literal string, never
        # regex-scanned, to keep both candidate-set derivations identical.
        content = _flatten(_skill_content())
        matcher = r"\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b"
        self.assertEqual(
            content.count(matcher),
            2,
            "the exact engine matcher must be specified at both cited "
            "locations (the narrative Step 0(c) extension and the Quality "
            "Criteria allowed_ids bullet), not merely described in prose",
        )
        self.assertIn("deliberationIDPattern", content)
        self.assertIn(
            "taken as a complete literal ID string, never regex-scanned",
            content,
        )

    def test_quality_criteria_bullet_mentions_linked_deliberations(self) -> None:
        content = _flatten(_skill_content())
        quality_idx = content.index("## Quality Criteria")
        quality_section = content[quality_idx:]
        self.assertIn("linked deliberation", quality_section)

    def test_policy_required_ids_summary_states_shipment_unconditional(self) -> None:
        content = _flatten(_policy_content())
        self.assertIn(
            "The shipment record is a `required_ids` member unconditionally, "
            "regardless of its own pre-close declared status",
            content,
        )
        self.assertIn(
            "this policy summary and the skill's binding rule are the same "
            "contract and MUST NOT diverge",
            content,
        )

    def test_policy_required_ids_summary_states_qualifying_feature_unconditional(
        self,
    ) -> None:
        # PR #407 review (threads PRRT_kwDORzpWpM6bzlFl / PRRT_kwDORzpWpM6bzlGL):
        # the policy-level summary must state the same unconditional rule for
        # a qualifying feature member that it already states for the shipment
        # record, and must stay in lockstep with the skill.
        content = _flatten(_policy_content())
        self.assertIn(
            "The same unconditional-required_ids rule applies to every "
            "qualifying feature member",
            content,
        )
        self.assertIn("ShipShipment", content)
        self.assertIn(
            "no pre-close status ever exempts a qualifying feature member "
            "from this requirement either",
            content,
        )

    def test_changelog_1_23_0_row_present_and_additive(self) -> None:
        content = _policy_content()
        idx_1_22 = content.index("| 1.22.0")
        idx_1_23 = content.index("| 1.23.0")
        self.assertLess(idx_1_22, idx_1_23)
        row_match = re.search(r"^\| 1\.23\.0 .*\|$", content, re.MULTILINE)
        self.assertIsNotNone(row_match)
        row = row_match.group(0)
        self.assertIn("required_ids", row)
        self.assertIn("qualifying feature", row)
        # 1.22.0 row preserved, not rewritten.
        row_1_22_match = re.search(r"^\| 1\.22\.0 .*\|$", content, re.MULTILINE)
        self.assertIsNotNone(row_1_22_match)
        self.assertIn(
            "the shipment record is a `required_ids` member unconditionally",
            row_1_22_match.group(0),
        )

    def test_changelog_1_22_0_row_present_and_does_not_rewrite_1_21_0(self) -> None:
        content = _policy_content()
        idx_1_21 = content.index("| 1.21.0")
        idx_1_22 = content.index("| 1.22.0")
        self.assertLess(idx_1_21, idx_1_22)
        row_match = re.search(r"^\| 1\.22\.0 .*\|$", content, re.MULTILINE)
        self.assertIsNotNone(row_match)
        row = row_match.group(0)
        self.assertIn("linked deliberation", row)
        self.assertIn("required_ids", row)

    def test_1_21_0_row_still_preserved_byte_identical(self) -> None:
        # The 1.22.0 row must be additive: it must not rewrite the 1.21.0
        # correction row it follows.
        content = _policy_content()
        row_match = re.search(r"^\| 1\.21\.0 .*\|$", content, re.MULTILINE)
        self.assertIsNotNone(row_match)
        row = row_match.group(0)
        self.assertIn("Corrects, and does not delete or edit, the 1.19.0 row above", row)


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
