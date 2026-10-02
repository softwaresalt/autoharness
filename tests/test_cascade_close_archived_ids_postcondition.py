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

try:
    from _assertion_render import render_source
except ModuleNotFoundError:  # pragma: no cover - module path differs by runner
    from tests._assertion_render import render_source

try:
    from test_flat_manifest_closure_docs import POLICY_PARITY_ALLOWLIST
except ModuleNotFoundError:  # pragma: no cover - module path differs by runner
    from tests.test_flat_manifest_closure_docs import POLICY_PARITY_ALLOWLIST

_ROOT = Path(__file__).resolve().parents[1]
_SKILL_TEMPLATE = _ROOT / "templates" / "skills" / "shipment-reconcile" / "SKILL.md.tmpl"
_SKILL_MIRROR = _ROOT / ".github" / "skills" / "shipment-reconcile" / "SKILL.md"
_POLICY_TEMPLATE = _ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"
_SPIKE_DOC = _ROOT / "docs" / "spikes" / "2026-08-18-cascade-close-pre-archived-member-behavior.md"
_COMPOUND_DOC = _ROOT / "docs" / "compound" / "2026-08-18-p015-cascade-classifier-override-deviation.md"
_COMPOUND_DOC_1101 = (
    _ROOT
    / "docs"
    / "compound"
    / "2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md"
)

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


def _skill_mirror_content() -> str:
    return _SKILL_MIRROR.read_text(encoding="utf-8")


def _skill_variants() -> tuple[tuple[str, str], ...]:
    return (("template", _skill_content()), ("mirror", _skill_mirror_content()))


def _policy_content() -> str:
    return _POLICY_TEMPLATE.read_text(encoding="utf-8")


def _spike_content() -> str:
    return _SPIKE_DOC.read_text(encoding="utf-8")


def _compound_content() -> str:
    return _COMPOUND_DOC.read_text(encoding="utf-8")


def _compound_content_1101() -> str:
    return _COMPOUND_DOC_1101.read_text(encoding="utf-8")


def _flatten(text: str) -> str:
    """Collapse newlines/indentation so a phrase that wraps across lines in
    the authored markdown can still be matched as a contiguous substring."""
    return re.sub(r"\s+", " ", text)


def _flatten_blockquote(text: str) -> str:
    """Like `_flatten`, but additionally strips a leading Markdown
    blockquote marker (`> `) from every line before collapsing whitespace,
    so a phrase that wraps across blockquoted lines (e.g. a spike doc's
    `> **SUPERSEDED ...**` banner) can still be matched as a contiguous
    substring without embedded `>` characters splitting words apart."""
    unquoted = re.sub(r"(?m)^>\s?", "", text)
    return _flatten(unquoted)


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
            "every other manifest item that was **not** truly `status: archived` "
            "in the Step 0(b) all-member pre-close declared-status snapshot",
            content,
        )
        self.assertIn(
            "A disposition-set deliberation that is not an explicit manifest "
            "member is never a `required_ids` member",
            content,
        )

    def test_allowed_ids_row_is_flat_closure_scope_without_linked_deliberation_union(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn("**Compute `allowed_ids`** = `closure_scope(S)`", content)
        self.assertIn(
            "every explicit manifest item ID from `items(S)`, regardless of "
            "`artifact_type`, plus the shipment record itself",
            content,
        )
        self.assertIn("linked deliberations are handled only by INV-12", content)
        self.assertIn("H10 carve-out", content)
        self.assertNotIn("every validated linked deliberation ID", content)

    def test_required_ids_no_longer_extended_for_linked_deliberations(self) -> None:
        content = _flatten(_skill_content())
        self.assertIn(
            "Because Step 0(b) snapshots every explicit manifest member "
            "regardless of `artifact_type`, no Step 0(c) "
            "linked-deliberation extension participates in this set",
            content,
        )
        self.assertIn(
            "A disposition-set deliberation that is not an explicit manifest "
            "member is never a `required_ids` member",
            content,
        )
        self.assertNotIn(
            "extended by Step 0(c) for qualifying feature members and their "
            "validated linked deliberations",
            content,
        )

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
        # The Quality Criteria bullet must reference the flat two-set gate,
        # not the retired linked-deliberation allowance.
        quality_idx = content.index("## Quality Criteria")
        quality_section = content[quality_idx:]
        self.assertIn("flat two-set", quality_section)
        self.assertIn("allowed_ids", quality_section)
        self.assertIn("required_ids", quality_section)
        self.assertIn("linked deliberations are handled only by INV-12", quality_section)
        self.assertNotIn("validated linked deliberation IDs", quality_section)
        self.assertNotIn("never a blanket allowance for arbitrary IDs", quality_section)

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
        # Under the flat 1.11.x sets, the pre-archived tolerance is scoped
        # to explicit non-shipment, non-feature manifest members. A linked
        # deliberation participates here only if it is an explicit manifest
        # member under H10, never merely because it is in the disposition set.
        content = _flatten(_skill_content())
        self.assertIn(
            "An `allowed_ids` **non-shipment, non-feature** member",
            content,
        )
        self.assertIn("including an explicit-member deliberation under H10", content)
        self.assertNotIn(
            "qualifying feature member's validated linked deliberation — "
            "never the qualifying feature member itself",
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

    # Relax R9 (198.002-T): item-7 policy assertions moved here from
    # CascadeCloseLinkedDeliberationAllowanceTests (which U3b replaces).
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

    def test_item_7_never_restates_blanket_manifest_member_omission_claim(
        self,
    ) -> None:
        # Negative assertion: the unqualified "A member whose declared
        # `status` is already truly `archived` ... correctly absent" phrase
        # must never reappear -- it contradicted the unconditional
        # qualifying-feature required_ids rule stated later in the same
        # item.
        content = _flatten(_policy_content())
        self.assertNotIn(
            "A member whose declared `status` is already truly `archived` "
            "before the invocation",
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


    # 198.004-T (U2b-2): close-path gate vs INV-12 split assertions.
    def test_b_b_required_check_drops_expected_cascade_mutation_clause(self) -> None:
        content = _policy_content()
        section = content[content.index("## P-015") : content.index("## P-016")]
        match = re.search(r"^\*\*Required Check[^\n]+", section, re.MULTILINE)
        self.assertIsNotNone(match)
        required_check = match.group(0)
        self.assertNotIn("expected, in-scope cascade mutation", section)
        self.assertIn(
            "every disposition-set (`validated_linked_deliberations(S)`) record path",
            required_check,
        )
        self.assertIn(
            "a disposition-set member that changes during the cascade is engine drift",
            required_check,
        )

    def test_b_c_postcondition_is_two_part(self) -> None:
        content = _policy_content()
        section = content[content.index("## P-015") : content.index("## P-016")]
        match = re.search(r"^\*\*Postcondition\*\* \(two parts\)[^\n]+", section, re.MULTILINE)
        self.assertIsNotNone(match)
        postcondition = match.group(0)
        part_a = (
            "(a) **Close-path gate postcondition** (INV-10; flat sets; "
            "evaluated before INV-12 disposition)"
        )
        part_b = (
            "(b) **INV-12 postcondition** (after the gate): only "
            "disposition-set deliberations whose INV-12 outcome is `archived` "
            "may change relative to the disposition baseline"
        )
        self.assertIn(part_a, postcondition)
        self.assertIn(part_b, postcondition)
        self.assertLess(postcondition.index(part_a), postcondition.index(part_b))

    def test_b_d_inv_10_label_present(self) -> None:
        content = _policy_content()
        match = re.search(r"^\* \*\*INV-10 [^\n]+", content, re.MULTILINE)
        self.assertIsNotNone(match)
        bullet = match.group(0)
        expected_prefix = (
            "* **INV-10 (Close-path gate postconditions (evaluated before "
            "INV-12 disposition)).**"
        )
        self.assertEqual(bullet[: len(expected_prefix)], expected_prefix)
        self.assertIn(
            "INV-12's `archived` deliberations are the only artifacts outside "
            "`allowed_ids(S)` that may change after the gate, and only through INV-12",
            bullet,
        )
        self.assertNotIn("**INV-10 (Postconditions).**", content)

    # 198.006-T (U2b-4): item-7, evidence-class and P-010 assertions.
    def test_item_7_omission_sentence_scoped_to_non_feature_members(self) -> None:
        # Inverted replacement of the item-7 test retired by relax R9
        # (198.002-T): under the flat 1.11.x sets the "correctly absent"
        # sentence covers non-feature manifest members only.
        content = _flatten(_policy_content())
        self.assertIn(
            "A non-feature manifest member (any explicit manifest member that "
            "is not a qualifying feature member) whose declared `status` is "
            "already truly `archived` before the invocation has no transition "
            "to report and is **correctly absent** from `archived_ids`",
            content,
        )
        self.assertIn("the way a non-feature manifest member can be.", content)
        match = re.search(
            r"^7\. \*\*Pre-archived manifest members[^\n]+", _policy_content(), re.MULTILINE
        )
        self.assertIsNotNone(match)
        item_7 = match.group(0)
        self.assertNotIn("qualifying feature member's validated linked deliberation", item_7)
        self.assertNotIn("a qualifying feature's linked deliberation", item_7)
        self.assertIn("appends no linked deliberations", item_7)

    def test_b_e_evidence_class_note_states_two_propositions(self) -> None:
        content = _policy_content()
        match = re.search(r"^\*\*Evidence-class note\.\*\*[^\n]+", content, re.MULTILINE)
        self.assertIsNotNone(match)
        note = match.group(0)
        self.assertIn("two engine propositions", note)
        first = note.index("(1) **inert archived descendants**")
        second = note.index("(2) **backlogit 1.11.x leaves linked deliberations independent**")
        self.assertLess(first, second)
        self.assertIn("`v1.11.0` (L716-751)", note)
        self.assertIn("TestUArchiveCandidateFlat_UnlistedLinkedDeliberationIsUntouched", note)
        self.assertIn("190-S", note)
        self.assertIn(
            "`archive_item` single-artifact semantics is a verified-line **assumption**",
            note,
        )

    def test_b_f_p010_inv_12_archival_clarification(self) -> None:
        content = _policy_content()
        section = content[content.index("## P-010") : content.index("## P-011")]
        must_not = section[section.index("**Ship MUST NOT**") : section.index("**Ship MAY**")]
        may = section[section.index("**Ship MAY**") :]
        self.assertIn(
            "- Create or modify deliberation, spike, plan, or review artifacts "
            "(P-015 INV-12 archival transitions excepted)",
            must_not,
        )
        self.assertIn(
            "- Archive a validated linked deliberation only through the P-015 "
            "INV-12 Linked-Deliberation Disposition step (and the post-merge "
            "source-artifact retirement that consumes its report); this is a "
            "closure lifecycle transition, not creation or modification of "
            "deliberation content",
            may,
        )

    # 198.007-T (B-g): rendered-region parity for the U2b-edited paragraphs
    # (198.003-T, 198.005-T), modulo POLICY_PARITY_ALLOWLIST. The
    # Evidence-class note is compared from its 198.005-T region anchor only:
    # its opening sentences carry pre-existing, deliberate mirror-concrete
    # evidence commits that are outside this unit's edit.
    def test_b_g_u2b_paragraphs_rendered_region_parity(self) -> None:
        rendered = render_source(".github/policies/workflow-policies.md")
        mirror = (_ROOT / ".github" / "policies" / "workflow-policies.md").read_text(
            encoding="utf-8"
        )
        line_anchors = (
            "**Statement**: Shipment closure is a flat-manifest operation.",
            "**Required Check (verify-after-each invariant)**",
            "**Postcondition** (two parts)",
            "**Violation Action (approval-gated rollback)**",
            "**Relationship to P-007**: P-015",
            "* **INV-7 (",
            "* **INV-10 (",
            "* **INV-11 (",
            "7. **Pre-archived manifest members",
            "- Create or modify deliberation, spike, plan, or review artifacts",
            "- Archive a validated linked deliberation",
        )
        region_anchors = (
            ("**Evidence-class note.**", "Under the verified engine-semantics line"),
        )
        for anchor in line_anchors + tuple(line for line, _ in region_anchors):
            with self.subTest(anchor=anchor):
                expected = [line for line in rendered.splitlines() if line.startswith(anchor)]
                actual = [line for line in mirror.splitlines() if line.startswith(anchor)]
                self.assertEqual(len(expected), 1)
                self.assertEqual(len(actual), 1)
                region, observed = expected[0], actual[0]
                for line_anchor, region_anchor in region_anchors:
                    if anchor == line_anchor:
                        self.assertIn(region_anchor, region)
                        self.assertIn(region_anchor, observed)
                        region = region[region.index(region_anchor) :]
                        observed = observed[observed.index(region_anchor) :]
                for template_text, mirror_text in POLICY_PARITY_ALLOWLIST:
                    region = region.replace(template_text, mirror_text)
                self.assertEqual(observed, region)


class CascadeCloseLinkedDeliberationFlatSemanticsTests(unittest.TestCase):
    """199.004-T/199.005-T/199.006-T: pins the U3b flat-engine
    disposition-snapshot contract in both the template and installed mirror.
    """

    def test_f_a_disposition_snapshot_states_exact_link_sources(self) -> None:
        for label, raw in _skill_variants():
            with self.subTest(surface=label):
                content = _flatten(raw)
                section = content[
                    content.index("**Linked-deliberation disposition snapshot.**") :
                    content.index("**Engine-semantics gate", content.index("**Linked-deliberation disposition snapshot."))
                ]
                self.assertIn("every explicit manifest member regardless of `artifact_type`", section)
                self.assertIn("`custom_fields.source_deliberation_id` as a complete literal value", section)
                self.assertIn("description/references text scanned with the identical", section)
                self.assertIn(r"\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b", section)

    def test_f_b_disposition_snapshot_validates_existence_before_location(self) -> None:
        for label, raw in _skill_variants():
            with self.subTest(surface=label):
                content = _flatten(raw)
                section = content[
                    content.index("**Linked-deliberation disposition snapshot.**") :
                    content.index("**Engine-semantics gate", content.index("**Linked-deliberation disposition snapshot."))
                ]
                self.assertIn("Validate existence before location", section)
                self.assertIn("first determine whether the ID resolves to any deliberation record", section)
                self.assertIn("only then classify where each record path resides", section)

    def test_f_h_disposition_snapshot_excludes_self_and_closure_scope(self) -> None:
        for label, raw in _skill_variants():
            with self.subTest(surface=label):
                content = _flatten(raw)
                section = content[
                    content.index("**Linked-deliberation disposition snapshot.**") :
                    content.index("**Engine-semantics gate", content.index("**Linked-deliberation disposition snapshot."))
                ]
                self.assertIn("exclude the shipment record itself and every ID in `closure_scope(S)`", section)
                self.assertIn("H10", section)
                self.assertIn("an explicit-member deliberation is an ordinary manifest member", section)

    def test_f_c_torn_deliberation_is_retained_ambiguous_not_a_halt(self) -> None:
        for label, raw in _skill_variants():
            with self.subTest(surface=label):
                content = _flatten(raw)
                section = content[
                    content.index("**Linked-deliberation disposition snapshot.**") :
                    content.index("**Engine-semantics gate", content.index("**Linked-deliberation disposition snapshot."))
                ]
                self.assertIn("A torn or duplicate deliberation", section)
                self.assertIn("`retained_ambiguous` and does **not** halt", section)
                self.assertIn("every discovered record path is still fingerprinted", section)
                self.assertIn("`RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS`", section)
                self.assertIn("apply to manifest members only", section)

    def test_f_d_unresolved_references_are_recorded_without_halting(self) -> None:
        for label, raw in _skill_variants():
            with self.subTest(surface=label):
                content = _flatten(raw)
                section = content[
                    content.index("**Linked-deliberation disposition snapshot.**") :
                    content.index("**Engine-semantics gate", content.index("**Linked-deliberation disposition snapshot."))
                ]
                self.assertIn("An unresolved ID records `unresolved_references`", section)
                self.assertIn("does **not** halt", section)
                self.assertIn("`RECONCILE_FAIL_SNAPSHOT_MISSING`", section)
                self.assertIn("never to disposition-set deliberations", section)

    def test_f_e_snapshot_records_sha_256_per_record_path(self) -> None:
        for label, raw in _skill_variants():
            with self.subTest(surface=label):
                content = _flatten(raw)
                section = content[
                    content.index("**Linked-deliberation disposition snapshot.**") :
                    content.index("**Engine-semantics gate", content.index("**Linked-deliberation disposition snapshot."))
                ]
                self.assertIn("every record path", section)
                self.assertIn("SHA-256 of each record path's bytes", section)
                self.assertIn("captured SHA-256 values", section)

    def test_f_f_disposition_snapshot_is_not_a_blanket_allowance(self) -> None:
        for label, raw in _skill_variants():
            with self.subTest(surface=label):
                content = _flatten(raw)
                section = content[
                    content.index("**Linked-deliberation disposition snapshot.**") :
                    content.index("**Engine-semantics gate", content.index("**Linked-deliberation disposition snapshot."))
                ]
                self.assertIn("uses the planner's `validated_linked_deliberations(S)` set definition", section)
                self.assertIn("collect link candidates from", section)
                self.assertIn("exclude the shipment record itself and every ID in `closure_scope(S)`", section)
                self.assertNotIn("any embedded deliberation ID", section)
                self.assertNotIn("blanket allowance for arbitrary IDs", section)

    def test_f_g_linked_deliberation_ids_appears_only_as_superseded_provenance(self) -> None:
        for label, raw in _skill_variants():
            with self.subTest(surface=label):
                self.assertEqual(raw.count("`linkedDeliberationIDs`"), 1)
                idx = raw.index("`linkedDeliberationIDs`")
                context = _flatten(raw[max(0, idx - 200) : idx + 300])
                self.assertIn("Superseded provenance only", context)
                self.assertIn("removed `linkedDeliberationIDs` helper", context)
                self.assertIn("the engine does not archive these disposition-set deliberations", context)


class CascadeCloseEngineSemanticsGateTests(unittest.TestCase):
    """198.009-T (U3a-2): first assertions for the 198.008-T skill triple --
    Step 0(b) all-member snapshot, the Step 0(c) Engine-semantics gate and
    the `select_close_path` routing."""

    def test_c_a_engine_semantics_gate_tokens_present(self) -> None:
        content = _skill_content()
        for token in (
            "Engine-semantics gate",
            "ENGINE_SEMANTICS_UNVERIFIED",
            "no_update_check",
            "probe_surface",
            "select_close_path",
        ):
            with self.subTest(token=token):
                self.assertIn(token, content)
        flat = _flatten(content)
        gate = flat[flat.index("**Engine-semantics gate") : flat.index("**Close-path selection.**")]
        # Literal tool/CLI wording, never an {{OP_...}} placeholder.
        self.assertIn("`backlogit_get_version` with `no_update_check: true`", gate)
        self.assertIn("`backlogit version --no-update-check --format json`", gate)
        self.assertIn("Verified engine-semantics lines: `1.11`", gate)
        self.assertNotIn("{{OP_", gate)

    def test_c_c_pre_invocation_re_probe_compares_raw_engine_semantics(self) -> None:
        flat = _flatten(_skill_content())
        re_probe = flat[
            flat.index("**Engine-semantics re-probe (pre-invocation revalidation).**") :
            flat.index("**Baseline-fingerprint capture", flat.index("**Engine-semantics re-probe"))
        ]
        self.assertIn("re-run the Step 0(c) Engine-semantics gate probe **fresh**", re_probe)
        self.assertIn("on the SAME surface", re_probe)
        self.assertIn("compare the RAW `version`, `commit`, and `probe_surface` values", re_probe)
        self.assertIn("resulting engine-semantics verdict", re_probe)
        self.assertIn("by exact string equality", re_probe)
        self.assertIn("never a normalized or minor-line-only comparison", re_probe)

    def test_c_d_re_probe_failure_halts_drift_without_safe_close(self) -> None:
        flat = _flatten(_skill_content())
        re_probe = flat[
            flat.index("**Engine-semantics re-probe (pre-invocation revalidation).**") :
            flat.index("**Baseline-fingerprint capture", flat.index("**Engine-semantics re-probe"))
        ]
        self.assertIn("Any difference, or a re-probe failure of any kind", re_probe)
        self.assertIn("HALT — cascade pre-invocation revalidation drift detected", re_probe)
        self.assertIn("do NOT invoke either close path", re_probe)
        self.assertIn("Never fall back to `SAFE_CLOSE` here", re_probe)
        self.assertIn("prohibited `CASCADE` → `SAFE_CLOSE` substitution", re_probe)

    def test_c_e_step_0b_snapshots_every_explicit_manifest_member(self) -> None:
        flat = _flatten(_skill_content())
        self.assertIn(
            "Snapshot pre-close `parent_id` and declared `status` for every "
            "explicit manifest member regardless of `artifact_type`",
            flat,
        )
        self.assertNotIn("declared `status` for every task item", flat)

    def test_c_f_cascade_routing_names_linked_deliberation_disposition_step(self) -> None:
        flat = _flatten(_skill_content())
        self.assertIn(
            "in place of steps 1–10, then continue to the "
            "Linked-Deliberation Disposition step.",
            flat,
        )
        self.assertNotIn("then proceed to post-mode", flat)
        self.assertIn(
            "unresolved precondition, and including `ENGINE_SEMANTICS_UNVERIFIED`)",
            flat,
        )


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
        # A truly pre-archived non-feature manifest member is excluded from
        # required_ids, so its absence from archived_ids does not trigger the
        # missing-required halt. This is exactly what the withdrawn full-set-
        # equality claim got wrong, without any deliberation-ID tolerance
        # example.
        transition_idx = content.index("`archived_ids` is a transition log")
        transition = content[transition_idx : content.index("**No-substitution rule**")]
        self.assertIn("A non-feature manifest member", transition)
        self.assertIn("has no transition to report", transition)
        self.assertIn("this is expected engine behavior", transition)
        self.assertIn(
            "correctly absent\" the way a non-feature manifest member can",
            transition,
        )
        self.assertNotIn("validated linked deliberation", transition)
        self.assertNotIn("027-DL", transition)


    def test_scenario_2_preamble_never_restates_blanket_manifest_member_claim(
        self,
    ) -> None:
        # Negative assertion (PR #407 review, thread PRRT_kwDORzpWpM6b0kit):
        # the withdrawn, over-broad "A manifest member ... correctly absent"
        # phrasing must never reappear unqualified -- it would let an agent
        # accept the exact qualifying-feature omission step 3 now rejects.
        content = _flatten(_skill_content())
        self.assertNotIn(
            "A manifest member that was already truly `status: archived` "
            "before the call",
            content,
        )

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


class CascadeCloseEvidenceTrailScopeTests(unittest.TestCase):
    """PR #407 review cycle 10 (threads PRRT_kwDORzpWpM6b00dS /
    PRRT_kwDORzpWpM6b00d-): the evidence-trail docs (spike + compound
    learning) must scope their own "correctly absent" restatements the same
    way the live skill/policy contract does -- never generalized to every
    manifest member, since a qualifying feature member is forced through
    `status: done` before archive-candidate collection and is therefore
    never "correctly absent" the way a task or linked deliberation is.
    """

    def test_spike_supersession_note_scopes_correctly_absent_to_task_and_linked_deliberation(
        self,
    ) -> None:
        content = _flatten_blockquote(_spike_content())
        self.assertIn(
            "truly `status: archived` **manifest task item, or a "
            "qualifying feature member's validated linked deliberation,** "
            "has no transition to report and is correctly **absent** from "
            "`archived_ids`",
            content,
        )
        self.assertIn("PRRT_kwDORzpWpM6b00dS", content)
        self.assertIn(
            "never extends to the qualifying feature member itself", content
        )

    def test_spike_supersession_note_never_restates_blanket_member_claim(self) -> None:
        content = _flatten_blockquote(_spike_content())
        self.assertNotIn(
            "truly `status: archived` member has no transition to report "
            "and is correctly **absent** from `archived_ids`",
            content,
        )

    def test_compound_doc_correction_scopes_correctly_absent_to_task_and_linked_deliberation(
        self,
    ) -> None:
        content = _flatten(_compound_content())
        self.assertIn(
            "truly `status: archived` **manifest task item, or a "
            "qualifying feature member's validated linked deliberation,** "
            "has **no transition to report** and is **correctly absent** "
            "from `archived_ids`",
            content,
        )
        self.assertIn("PRRT_kwDORzpWpM6b00d-", content)
        self.assertIn(
            "never extends to the qualifying feature member itself", content
        )

    def test_compound_doc_never_restates_blanket_member_claim(self) -> None:
        content = _flatten(_compound_content())
        self.assertNotIn(
            "truly `status: archived` manifest member has **no transition "
            "to report** and is **correctly absent** from `archived_ids`",
            content,
        )


class CascadeCloseCorrectedBannerScopeTests(unittest.TestCase):
    """PR #407 review (thread PRRT_kwDORzpWpM6b1Dh_): the CORRECTED /
    RETRACTED banner in the 2026-08-23 `archived_ids` compound-learning
    document must scope its own "correctly treats ... absence ... as
    expected" restatement the same way the live skill/policy contract and
    the other two evidence-trail docs (cycle 9/10) do -- never generalized
    to every pre-archived manifest member, since a qualifying feature member
    (and the shipment record) are unconditional `required_ids` members and
    can never be "correctly absent" the way a task item or linked
    deliberation can.
    """

    def test_banner_scopes_correctly_treats_to_task_and_linked_deliberation(
        self,
    ) -> None:
        content = _flatten_blockquote(_compound_content_1101())
        self.assertIn(
            "which correctly treats a truly pre-archived **manifest task "
            "item's, or a qualifying feature member's validated linked "
            "deliberation's,** absence from `archived_ids` as expected, "
            "not a fail-closed halt condition.",
            content,
        )
        self.assertIn("PRRT_kwDORzpWpM6b1Dh_", content)
        self.assertIn(
            "never extends to the shipment record or to a qualifying "
            "feature member itself",
            content,
        )

    def test_banner_never_restates_blanket_member_claim(self) -> None:
        content = _flatten_blockquote(_compound_content_1101())
        self.assertNotIn(
            "which correctly treats a truly pre-archived member's absence "
            "from `archived_ids` as expected, not a fail-closed halt "
            "condition.",
            content,
        )


class CascadeCloseFrontmatterMetadataScopeTests(unittest.TestCase):
    """PR #407 review (thread PRRT_kwDORzpWpM6b1bmy): the 2026-08-23
    compound document's CORRECTED/RETRACTED body banner (pinned by
    ``CascadeCloseCorrectedBannerScopeTests`` above) retracted the
    "1.10.1-vs-1.9.0 behavior change" / "regression" diagnosis, but the
    document's own searchable YAML frontmatter still asserted the
    retracted framing verbatim in ``root_cause`` and still classified the
    entry via a ``regression`` tag. Compound retrieval indexes frontmatter
    directly, so a corrected body banner does not stop the retracted
    diagnosis from being surfaced through frontmatter-only retrieval.
    This pins that the frontmatter now names the autoharness exact-match
    expectation as the defect (not an engine behavior change) and no
    longer carries the ``regression`` tag.
    """

    @staticmethod
    def _frontmatter() -> dict:
        import yaml

        raw = _compound_content_1101()
        assert raw.startswith("---\n")
        end = raw.index("\n---", 4)
        frontmatter = raw[4:end]
        parsed = yaml.safe_load(frontmatter)
        assert isinstance(parsed, dict)
        return parsed

    def test_frontmatter_parses(self) -> None:
        parsed = self._frontmatter()
        self.assertIsInstance(parsed, dict)

    def test_root_cause_names_autoharness_expectation_as_the_defect(self) -> None:
        root_cause = self._frontmatter()["root_cause"]
        self.assertIn("autoharness", root_cause.lower())
        self.assertIn("exact-match", root_cause.lower())
        self.assertIn("expectation", root_cause.lower())
        self.assertIn("defect", root_cause.lower())

    def test_root_cause_no_longer_asserts_1_10_1_vs_1_9_0_behavior_change(
        self,
    ) -> None:
        root_cause = self._frontmatter()["root_cause"]
        self.assertNotIn("1.10.1", root_cause)
        self.assertNotIn("1.9.0", root_cause)
        self.assertNotIn("behavior change", root_cause.lower())

    def test_tags_no_longer_include_regression(self) -> None:
        tags = self._frontmatter()["tags"]
        self.assertNotIn("regression", tags)


if __name__ == "__main__":
    unittest.main()
