"""Contract tests for the P-021 (Bounded Fix-Cycle Scope Containment and
Deferred Expansion Capture) CAPTURE-AND-DISCHARGE semantics group (134.012-T),
plus the cross-file allocation guards (RANGE-COMPLETENESS, SUBSET-FIDELITY,
DERIVED-SUBSET) that keep the three-file B1-B18 coverage matrix from drifting
apart the way its predecessor copies did.

This module OWNS behaviours B3, B4, B5, B6, B7, B8, B9, and the two DERIVED
behaviours B16 (``B7 INTERSECT B8``) and B17 (``B6 UNION {007-fix-ci}``). See
``OWNED_BEHAVIOURS`` below.

Where 134.011-T proves each clause is PRESENT on each carrier, and 134.013-T
proves the clause-BOUNDARY behaviours are semantically correct, this module
proves the C2/C3 CAPTURE-AND-DISCHARGE clauses SAY THE RIGHT THING on each
carrier -- the class of defect where a clause is present and byte-identical
to its dogfood on every carrier, yet the carriers are semantically
contradictory with one another (three distinct real fix cycles: a threadless
path marking a KNOWN PR number N/A; authoritative C3 demanding a
review-thread reply even where no thread can exist; and fix-ci's threadless
discharge naming only two of the three required residual-risk records).

Authored LAST of the three P-021 contract-test files because its
RANGE-COMPLETENESS guard imports the ``OWNED_BEHAVIOURS`` constant from BOTH
sibling modules -- ``test_scope_containment_policy_contract`` (134.011-T) and
``test_scope_containment_boundary_contract`` (134.013-T) -- and therefore
requires both to already exist. Neither sibling imports from this module:
the allocation-check dependency edge flows one way only (011 -> 013 -> 012),
which is what keeps the three-way guard acyclic.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from test_scope_containment_policy_contract import (
    ALL_BEHAVIOURS,
    BEHAVIOR_CARRIER_SUBSETS,
    MATRIX,
    OWNED_BEHAVIOURS as _POLICY_OWNED,
    _load_all_texts,
    _load_carrier_texts,
    _normalize,
)
from test_scope_containment_boundary_contract import OWNED_BEHAVIOURS as _BOUNDARY_OWNED

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Behaviours this file OWNS, per the CROSS-FILE BEHAVIOUR ALLOCATION: the
# CAPTURE-AND-DISCHARGE group plus its two derived behaviours.
OWNED_BEHAVIOURS = frozenset({
    "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B16", "B17",
})


def _resolve(behavior_id: str) -> frozenset[str]:
    """CARRIER-SET RESOLUTION: resolve a behaviour's carrier subset from the
    authoritative ``BEHAVIOR_CARRIER_SUBSETS`` mapping in 134.011-T's module.
    This module MUST NOT restate the matrix or hardcode a carrier list."""
    return BEHAVIOR_CARRIER_SUBSETS[behavior_id]


def _contains(haystack: str, needle: str) -> bool:
    return _normalize(needle) in _normalize(haystack)


def _matrix_carriers(clause: str) -> frozenset[str]:
    return frozenset(carrier for carrier, _role in MATRIX[clause])


# ---------------------------------------------------------------------------
# SUBSET-FIDELITY: maps each behaviour to the clause row(s) its carrier subset
# must be a SUBSET of, and separately maps each clause to the behaviour(s)
# whose UNION must COVER that clause's full carrier row. B14 appears under
# both C5 and C6 in the coverage map because it also discharges 008's C5
# carriage (134.011-T's B14 justification: "this behaviour ALSO discharges
# 008's C5 carriage"). B6 and B17 are the two declared EXEMPTIONS from the
# subset check: both descend from the SINGLE-WRITE CAPTURE INVARIANT, a Ship
# ROLE property derived from C5 rather than a registry clause row, so 008
# legitimately appears in their subsets while being absent from the literal
# C2 row.
# ---------------------------------------------------------------------------

BEHAVIOR_CLAUSE: dict[str, tuple[str, ...]] = {
    "B1": ("C1",), "B2": ("C1",),
    "B3": ("C2",), "B4": ("C2",), "B5": ("C2",),
    "B7": ("C3",), "B8": ("C3",), "B9": ("C3",), "B16": ("C3",),
    "B10": ("C4",),
    "B11": ("C5",), "B12": ("C5",), "B18": ("C5",), "B14": ("C5", "C6"),
    "B13": ("C6",),
    "B15": ("C7",),
}

_SUBSET_FIDELITY_EXEMPT = frozenset({"B6", "B17"})

CLAUSE_BEHAVIOR_MAP: dict[str, tuple[str, ...]] = {
    "C1": ("B1", "B2"),
    "C2": ("B3", "B4", "B5", "B6", "B7", "B8", "B9", "B16", "B17"),
    "C3": ("B7", "B8", "B9", "B16"),
    "C4": ("B10",),
    "C5": ("B11", "B12", "B18", "B14"),
    "C6": ("B13", "B14"),
    "C7": ("B15",),
}


class ScopeContainmentSemanticsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        all_texts = _load_all_texts()
        cls.carrier_texts = _load_carrier_texts(all_texts)
        cls.workflow_policy_text = all_texts["workflow_policy"]
        cls.ship_template_text = all_texts["ship_template"]
        cls.ship_dogfood_text = all_texts["ship_dogfood"]
        cls.stage_template_text = all_texts["stage_template"]
        cls.stage_dogfood_text = all_texts["stage_dogfood"]
        cls.circuit_breaker_template_text = all_texts["circuit_breaker_template"]
        cls.circuit_breaker_dogfood_text = all_texts["circuit_breaker_dogfood"]
        cls.github_pr_automation_template_text = all_texts["github_pr_automation_template"]
        cls.github_pr_automation_dogfood_text = all_texts["github_pr_automation_dogfood"]
        cls.pr_lifecycle_template_text = all_texts["pr_lifecycle_template"]
        cls.fix_ci_template_text = all_texts["fix_ci_template"]

        # Plan clause table and deliberation artifact: both are universal
        # negative-guard sweep surfaces for the FUSED-REF and
        # ASYMMETRIC-QUALIFIER guards below.
        plan_path = (
            _REPO_ROOT / "docs" / "plans" / "2026-08-18-bounded-fix-cycle-scope-containment-plan.md"
        )
        cls.plan_text = plan_path.read_text(encoding="utf-8")

        hardening_path = (
            _REPO_ROOT / "docs" / "plans"
            / "2026-08-18-bounded-fix-cycle-scope-containment-hardening.md"
        )
        cls.hardening_text = hardening_path.read_text(encoding="utf-8")

        deliberation_path = _REPO_ROOT / ".backlogit" / "queue" / "019-DL.md"
        cls.deliberation_text = deliberation_path.read_text(encoding="utf-8")

    # -- shared self-consistency check ---------------------------------------

    def test_owned_behaviours_are_declared_in_the_authoritative_mapping(self) -> None:
        """Every behaviour this file claims to own must resolve against
        134.011-T's authoritative BEHAVIOR_CARRIER_SUBSETS mapping."""
        for behavior_id in OWNED_BEHAVIOURS:
            with self.subTest(behavior_id=behavior_id):
                self.assertIn(behavior_id, BEHAVIOR_CARRIER_SUBSETS)

    # =========================================================================
    # RANGE-COMPLETENESS guard
    # =========================================================================

    def test_range_completeness_union_of_three_owned_sets_equals_b1_to_b18(self) -> None:
        """RANGE-COMPLETENESS: the union of the three contract-test files'
        OWNED_BEHAVIOURS constants (imported, never restated) must equal the
        authoritative B1-B18 range exactly. This is the guard that would have
        caught the present defect: the dual-path and entry-reuse tests were
        correct in substance but unnumbered, so they sat outside the mapping
        and were governed by neither the subset check nor this one."""
        union = _POLICY_OWNED | _BOUNDARY_OWNED | OWNED_BEHAVIOURS
        self.assertEqual(union, ALL_BEHAVIOURS)

    def test_range_completeness_three_owned_sets_are_pairwise_disjoint(self) -> None:
        """No behaviour ID may be claimed by more than one of the three
        contract-test files -- double-counting is exactly as unsafe as an
        uncovered gap, since it hides which file is actually responsible."""
        self.assertTrue(_POLICY_OWNED.isdisjoint(_BOUNDARY_OWNED))
        self.assertTrue(_POLICY_OWNED.isdisjoint(OWNED_BEHAVIOURS))
        self.assertTrue(_BOUNDARY_OWNED.isdisjoint(OWNED_BEHAVIOURS))

    def test_range_completeness_owned_sets_match_expected_allocation(self) -> None:
        """Pins the expected allocation so a behaviour silently moved between
        files (rather than through a declared split, as B1/B10/B11/B12/B14/B18
        moved to 134.013-T during the PR #372 review-fix cycle) is caught."""
        self.assertEqual(_POLICY_OWNED, frozenset({"B2", "B13", "B15"}))
        self.assertEqual(_BOUNDARY_OWNED, frozenset({"B1", "B10", "B11", "B12", "B14", "B18"}))
        self.assertEqual(
            OWNED_BEHAVIOURS,
            frozenset({"B3", "B4", "B5", "B6", "B7", "B8", "B9", "B16", "B17"}),
        )

    # =========================================================================
    # SUBSET-FIDELITY guard
    # =========================================================================

    def test_subset_fidelity_every_non_exempt_behaviour_is_subset_of_its_clause_row(self) -> None:
        """Every behaviour subset (except the declared {B6, B17} exemption)
        must be a SUBSET of its own clause's MATRIX row. This is what keeps
        a behaviour from being asserted against a carrier the mapping
        excludes -- e.g. demanding threadless discharge (B8) from
        github-pr-automation, or thread-reply ordering (B7) from
        circuit-breaker, neither of which those surfaces can faithfully
        carry."""
        for behavior_id, clauses in BEHAVIOR_CLAUSE.items():
            subset = _resolve(behavior_id)
            for clause in clauses:
                with self.subTest(behavior_id=behavior_id, clause=clause):
                    self.assertTrue(
                        subset <= _matrix_carriers(clause),
                        f"{behavior_id} subset {sorted(subset)} is not a subset "
                        f"of {clause} row {sorted(_matrix_carriers(clause))}",
                    )

    def test_subset_fidelity_exemption_set_is_exactly_b6_and_b17(self) -> None:
        """The subset-fidelity exemption is EXACTLY {B6, B17} -- both derive
        from the single-write invariant (a Ship ROLE property, not a
        registry clause row member) -- so a future behaviour cannot quietly
        opt out of the subset check by being added to this set."""
        covered = frozenset(BEHAVIOR_CLAUSE) | _SUBSET_FIDELITY_EXEMPT
        self.assertEqual(covered, ALL_BEHAVIOURS)
        self.assertEqual(_SUBSET_FIDELITY_EXEMPT, frozenset({"B6", "B17"}))

    def test_subset_fidelity_every_clause_row_member_is_covered_by_a_behaviour(self) -> None:
        """Every member of every clause row must be covered by at least one
        mapped behaviour's subset, including the declared cross-clause
        discharge of 008's C5 carriage under B14."""
        for clause, behavior_ids in CLAUSE_BEHAVIOR_MAP.items():
            covered: set[str] = set()
            for behavior_id in behavior_ids:
                covered |= _resolve(behavior_id)
            with self.subTest(clause=clause):
                self.assertTrue(
                    _matrix_carriers(clause) <= covered,
                    f"{clause} row {sorted(_matrix_carriers(clause))} not fully "
                    f"covered by {behavior_ids}: covered={sorted(covered)}",
                )

    # =========================================================================
    # DERIVED-SUBSET guard
    # =========================================================================

    def test_derived_subset_b16_equals_b7_intersect_b8(self) -> None:
        """B16 must be recomputed as `B7 INTERSECT B8` from its parents at
        assertion time, not read from a materialized copy -- otherwise a
        parent subset could change without the derived subset following."""
        recomputed = _resolve("B7") & _resolve("B8")
        self.assertEqual(recomputed, _resolve("B16"))
        self.assertEqual(recomputed, frozenset({"001", "004", "007-fix-ci"}))

    def test_derived_subset_b17_equals_b6_union_fix_ci(self) -> None:
        """B17 must be recomputed as `B6 UNION {007-fix-ci}` from its parent
        at assertion time, not read from a materialized copy."""
        recomputed = _resolve("B6") | frozenset({"007-fix-ci"})
        self.assertEqual(recomputed, _resolve("B17"))
        self.assertEqual(recomputed, frozenset({"004", "008", "007-fix-ci"}))

    # =========================================================================
    # B9 -- C3-SYMMETRIC-GUARD (hardening H12)
    # =========================================================================

    def test_b9_c3_symmetric_guard_present_in_complete_two_part_form(self) -> None:
        """B9 (c3-symmetric-guard, H12): asserted in its COMPLETE TWO-PART
        form on every surface in the B9 subset -- (i) a same-contract-surface
        completion IS in scope and must be fixed, not deferred; AND (ii)
        deferring one without a captured entry AND a residual-risk record is
        itself a P-021 violation. Part (i) alone forbids only under-fixing
        and leaves silent deferral unpenalized, so a carrier stating half the
        guard does not carry B9. The Ship (004) and fix-ci (007-fix-ci)
        surfaces are required members: both actually run fix cycles, so a
        two-surface (001/005-only) assertion would leave them unguarded."""
        subset = _resolve("B9")
        self.assertEqual(subset, frozenset({"001", "004", "005", "007-fix-ci"}))
        for carrier in subset:
            texts = self.carrier_texts[carrier]
            with self.subTest(carrier=carrier):
                part_i = any(
                    _contains(t, "a same-contract-surface completion of the authorized change IS in scope")
                    for t in texts
                )
                part_ii = any(
                    _contains(t, "deferring such a completion WITHOUT a captured")
                    or _contains(t, "deferring one without a captured entry")
                    or _contains(t, "deferral without a captured entry and a residual-risk record is itself a violation")
                    for t in texts
                )
                self.assertTrue(part_i, f"carrier {carrier} missing B9 part (i)")
                self.assertTrue(part_ii, f"carrier {carrier} missing B9 part (ii)")

    def test_b9_negative_guard_no_carrier_states_only_the_underfixing_half(self) -> None:
        """Non-vacuous negative guard: confirms a carrier that authored ONLY
        part (i) (same-contract-surface completion is in scope) WITHOUT part
        (ii) (deferral without capture is itself a violation) would be
        detected as an incomplete B9 discharge -- this is what regresses a
        carrier stating half the guard as if it fully carried B9."""
        half_guard_text = (
            "A same-contract-surface completion of the authorized change IS "
            "in scope and MUST be fixed, not deferred."
        )
        part_i = _contains(half_guard_text, "a same-contract-surface completion of the authorized change IS in scope")
        part_ii = _contains(half_guard_text, "deferring such a completion WITHOUT a captured") or _contains(
            half_guard_text, "deferring one without a captured entry"
        )
        self.assertTrue(part_i)
        self.assertFalse(part_ii, "half-guard text unexpectedly satisfied part (ii); guard would be vacuous")

    # =========================================================================
    # B16 (partial) -- CONDITIONAL-C3 (SUBSET-SCOPED to 001[A] only)
    # =========================================================================

    def test_b16_conditional_c3_authoritative_carrier_states_conditional_reply(self) -> None:
        """B16, CONDITIONAL-C3 component (SUBSET-SCOPED to 001[A] ONLY,
        regresses fix cycle 2). NOT the load-bearing B16 criterion -- the
        complete B16 subset is asserted by
        test_b16_fix_ci_dual_path_present_on_full_declared_subset below,
        which is where the structural per-behaviour audit resolves B16. This
        criterion asserts only that the authoritative C3 text makes the
        thread-reply obligation CONDITIONAL on a thread existing, and that it
        explicitly disclaims being an unconditional requirement."""
        text = self.workflow_policy_text
        self.assertTrue(_contains(text, "WHERE A REVIEW THREAD EXISTS for the finding"))
        self.assertTrue(_contains(text, "WHERE NO REVIEW THREAD EXISTS"))
        self.assertTrue(
            _contains(text, "C3 MUST NOT be stated as an unconditional thread-reply requirement")
        )

    def test_b16_conditional_c3_negative_guard_no_carrier_states_unconditional_reply(self) -> None:
        """Negative guard (fix cycle 2): none of the B16-subset carriers may
        state that a review-thread reply is required for EVERY finding
        without a thread-availability qualifier -- the historical defect
        where authoritative C3 demanded a review-thread reply even on
        surfaces where no thread can exist (pre-PR local-review findings,
        CI findings), making the clause unsatisfiable there."""
        defective_phrase = _normalize(
            "reference the deferred entry id in the review-thread reply for every finding"
        )
        for carrier in _resolve("B16"):
            for text in self.carrier_texts[carrier]:
                with self.subTest(carrier=carrier):
                    self.assertNotIn(defective_phrase, _normalize(text))

    def test_b16_conditional_c3_negative_guard_is_non_vacuous(self) -> None:
        """Proves the guard above actually fires against the constructed
        historical defective (unconditional) wording."""
        defective_text = (
            "C3 -- bounded resolution: resolve the in-scope defect/comment as "
            "far as possible without the expansion. Reference the deferred "
            "entry ID in the review-thread reply for every finding, posted "
            "before the thread is resolved, and in the PR/closure "
            "residual-risk record."
        )
        self.assertIn(
            _normalize("reference the deferred entry id in the review-thread reply for every finding"),
            _normalize(defective_text),
        )

    # =========================================================================
    # B8 -- THREADLESS-DISCHARGE + THREE-RECORD-CITATION (regresses fix
    # cycles 2 and 3)
    # =========================================================================

    def test_b8_threadless_discharge_present_on_full_declared_subset(self) -> None:
        """B8 (c3-threadless-discharge, regresses fix cycle 2): every surface
        in the B8 subset (authoritative registry, Ship, fix-ci's CI-finding
        path) states an explicit threadless disposition, and that the
        absence of a reply is stated to be NOT a C3 shortfall.
        github-pr-automation and pr-lifecycle are deliberately EXCLUDED:
        every finding on those surfaces is a PR review comment and therefore
        always has a thread, so demanding threadless text there would force
        a contract their subject matter cannot support."""
        subset = _resolve("B8")
        self.assertEqual(subset, frozenset({"001", "004", "007-fix-ci"}))
        expectations = {
            "001": "the absence of a reply is NOT a C3 shortfall",
            "004": "their absence is NOT a C3 shortfall",
            "007-fix-ci": "the C3 thread-reply step does not apply",
        }
        for carrier in subset:
            texts = self.carrier_texts[carrier]
            marker = expectations[carrier]
            with self.subTest(carrier=carrier):
                self.assertTrue(
                    any(_contains(t, marker) for t in texts),
                    f"carrier {carrier} missing threadless-discharge marker: {marker!r}",
                )
        # github-pr-automation and pr-lifecycle must NOT be in the B8 subset.
        self.assertNotIn("006", subset)
        self.assertNotIn("007-pr-lifecycle", subset)

    def test_b8_three_record_citation_present_on_every_threadless_carrier(self) -> None:
        """THREE-RECORD-CITATION (behaviour B8, regresses fix cycle 3):
        every threadless discharge names ALL THREE residual-risk records --
        task-level, run-level AND closure -- on the authoritative surface
        and on every threadless carrier. A discharge naming only two of the
        three (the exact defect fix cycle 3 repaired in fix-ci) fails."""
        subset = _resolve("B8")
        expectations = {
            "001": "the task-level, run-level, and closure residual-risk record",
            "004": "the task-level, run-level, and closure residual-risk records",
            "007-fix-ci": "the TASK-LEVEL, run-level, and closure residual-risk records",
        }
        for carrier in subset:
            texts = self.carrier_texts[carrier]
            marker = expectations[carrier]
            with self.subTest(carrier=carrier):
                self.assertTrue(
                    any(_contains(t, marker) for t in texts),
                    f"carrier {carrier} does not cite all three residual-risk "
                    f"records: {marker!r}",
                )

    def test_b8_three_record_citation_negative_guard_rejects_two_of_three(self) -> None:
        """Non-vacuous negative guard: a discharge naming only two of the
        three required records (task-level + closure, omitting run-level --
        the exact fix cycle 3 defect in fix-ci) must be distinguishable from
        the corrected three-record form."""
        two_record_defect = (
            "cite the generated deferred entry ID in the task-level and "
            "closure residual-risk records"
        )
        three_record_marker = _normalize("the TASK-LEVEL, run-level, and closure residual-risk records")
        self.assertNotIn(three_record_marker, _normalize(two_record_defect))
        # And confirm the real fix-ci text (a three-record citation) matches.
        self.assertTrue(
            any(
                _contains(t, "the TASK-LEVEL, run-level, and closure residual-risk records")
                for t in self.carrier_texts["007-fix-ci"]
            )
        )

    # =========================================================================
    # B5 -- PER-FIELD-ID, FUSED-REF, ASYMMETRIC-QUALIFIER, LIVE-CARRIER
    # AGREEMENT (regresses the ASYMMETRIC-QUALIFIER fix cycle, hardening H7)
    # =========================================================================

    def test_b5_per_field_id_availability_judged_independently(self) -> None:
        """PER-FIELD-ID (B5): every carrier in the B5 subset states that
        source-ref availability is judged INDEPENDENTLY PER FIELD -- the
        precondition for treating the PR number and the review-thread ID as
        two distinct, separately-resolved fields rather than a single
        path-level default."""
        subset = _resolve("B5")
        self.assertEqual(subset, frozenset({"001", "004", "007-fix-ci"}))
        for carrier in subset:
            texts = self.carrier_texts[carrier]
            with self.subTest(carrier=carrier):
                self.assertTrue(
                    any(_contains(t, "judged INDEPENDENTLY PER FIELD") for t in texts),
                    f"carrier {carrier} does not judge source-ref availability independently per field",
                )

    def test_b5_per_field_id_negative_guard_rejects_paired_na_default(self) -> None:
        """Non-vacuous UNIVERSAL negative guard, swept across every C2
        carrier (not just the B5 subset, since a fused pairing is wrong
        wherever it appears): no carrier may state that the
        PR number and the review-thread ID are marked `N/A` TOGETHER as a
        blanket, path-level default (as opposed to each field's `N/A`
        following independently from its OWN availability) -- distinguishes
        the corrected per-field form from a defective paired-default one."""
        defective_phrase = _normalize(
            "the PR number and the review-thread ID are recorded as N/A together on the threadless path"
        )
        for carrier in _matrix_carriers("C2"):
            for text in self.carrier_texts[carrier]:
                with self.subTest(carrier=carrier):
                    self.assertNotIn(defective_phrase, _normalize(text))
        # Non-vacuity: the constructed defective phrase does not collapse to
        # the corrected per-field wording actually used on any B5 carrier.
        corrected_004 = _normalize(
            "The PR number and the review-thread ID are `N/A` together only for a genuinely pre-PR finding."
        )
        self.assertNotEqual(defective_phrase, corrected_004)

    def test_b5_fused_ref_negative_guard_no_field_name_fuses_the_two_refs(self) -> None:
        """FUSED-REF (B5) universal negative guard, swept across every C2
        carrier plus the plan clause table and the authoritative registry:
        no surface may enumerate a fused `PR/thread ID` FIELD NAME (treating
        the two refs as one). The corrected text on 001 and 007-fix-ci DOES
        contain the substring `PR/thread` -- but only inside the PROHIBITION
        sentence ("MUST NOT be fused into a single `PR/thread` ref/token"),
        never as a listed field name, so the guard checks for the more
        specific defective form `PR/thread ID` rather than blindly rejecting
        `PR/thread` outright, which would misfire on the correct text."""
        sweep_texts = [
            *(t for carrier in _matrix_carriers("C2") for t in self.carrier_texts[carrier]),
            self.plan_text,
        ]
        for text in sweep_texts:
            self.assertNotIn(_normalize("pr/thread id"), _normalize(text))
        # Confirm the legitimate prohibition-sentence usage of the shared
        # substring "PR/thread" is NOT itself flagged (proves the guard is
        # scoped to "PR/thread ID" specifically, not "PR/thread" generally).
        self.assertTrue(
            any(_contains(t, "PR/thread") for t in self.carrier_texts["001"]),
            "sanity check: 001 should legitimately contain 'PR/thread' inside its prohibition sentence",
        )

    def test_b5_fused_ref_negative_guard_is_non_vacuous(self) -> None:
        """Proves the FUSED-REF negative guard actually fires against a
        constructed defective enumeration that lists a fused `PR/thread ID`
        as though it were a single field, distinguishing it from the
        legitimate prohibition-sentence usage of the same substring."""
        defective_text = (
            "Source refs -- PR/thread ID, task ID, feature ID, shipment ID."
        )
        self.assertIn(_normalize("pr/thread id"), _normalize(defective_text))
        legitimate_text = (
            "The PR number and the review-thread ID are SEPARATE refs and "
            "MUST NOT be fused into a single `PR/thread` ref."
        )
        self.assertNotIn(_normalize("pr/thread id"), _normalize(legitimate_text))

    def test_b5_fused_ref_positive_each_ref_carries_its_own_per_field_na(self) -> None:
        """FUSED-REF (B5) positive assertion, subset-scoped to {001, 004,
        007-fix-ci}: the PR number and the review-thread ID each carry their
        OWN independent applicability qualifier and their OWN explicit
        per-field `N/A` case, rather than a single joint qualifier."""
        expectations = {
            "001": (
                "SEPARATE refs and MUST NOT be fused into a single",
                "recorded as an explicit `N/A`",
            ),
            "004": (
                "is recorded as `N/A` only for a genuinely pre-PR finding",
                "is recorded as `N/A` whenever no thread exists",
            ),
            "007-fix-ci": (
                "SEPARATE source refs",
                "recorded as `N/A` for a CI check failure",
            ),
        }
        for carrier, markers in expectations.items():
            texts = self.carrier_texts[carrier]
            for marker in markers:
                with self.subTest(carrier=carrier, marker=marker):
                    self.assertTrue(
                        any(_contains(t, marker) for t in texts),
                        f"carrier {carrier} missing per-field marker: {marker!r}",
                    )

    def test_b5_asymmetric_qualifier_negative_guard_rejects_one_sided_when_applicable(self) -> None:
        """ASYMMETRIC-QUALIFIER (B5) universal negative guard, swept across
        every C2 carrier, the plan clause table, the hardening doc's H7
        section, and the authoritative registry: regresses the historical
        defect (confirmed via git archaeology through commit d52ab147,
        corrected in be2ed019) where a single trailing "(when applicable)"
        was attached only to the review-thread ID, leaving the PR number
        looking unconditionally required. The corrected text either
        qualifies BOTH refs symmetrically (001, plan) or qualifies NEITHER
        (004, 007-fix-ci, where per-field N/A carries the conditionality
        instead) -- it never qualifies exactly one."""
        defective_phrase = _normalize(
            "source refs \u2014 PR number, review-thread ID (when applicable), task ID, feature ID, shipment ID"
        )
        sweep_texts = [
            *(t for carrier in _matrix_carriers("C2") for t in self.carrier_texts[carrier]),
            self.plan_text,
            self.hardening_text,
        ]
        for text in sweep_texts:
            self.assertNotIn(defective_phrase, _normalize(text))

    def test_b5_asymmetric_qualifier_negative_guard_is_non_vacuous(self) -> None:
        """Proves the ASYMMETRIC-QUALIFIER guard fires against the exact
        historical defective wording recovered from git history (present
        through commit d52ab147, corrected in be2ed019)."""
        historical_defective_text = (
            "source refs \u2014 PR number, review-thread ID (when applicable), "
            "task ID, feature ID, shipment ID"
        )
        defective_phrase = _normalize(
            "source refs \u2014 PR number, review-thread ID (when applicable), task ID, feature ID, shipment ID"
        )
        self.assertIn(defective_phrase, _normalize(historical_defective_text))

    def test_b5_asymmetric_qualifier_hardening_doc_documents_the_corrected_form(self) -> None:
        """Confirms the hardening doc's H7 addendum, in its CURRENT
        committed state, documents the corrected (non-asymmetric) form
        rather than merely narrating the defect without a fix -- i.e. the
        historical defective phrase is discussed as a REGRESSED defect, not
        left as the doc's live prescription."""
        self.assertTrue(
            _contains(self.hardening_text, "asymmetric")
            or _contains(self.hardening_text, "when applicable")
        )
        # The corrected registry text (001) itself must NOT carry the
        # asymmetric one-sided qualifier.
        self.assertNotIn(
            _normalize(
                "source refs \u2014 pr number, review-thread id (when applicable), task id, feature id, shipment id"
            ),
            _normalize(self.workflow_policy_text),
        )

    def test_b5_live_carrier_agreement_with_authoritative_c2(self) -> None:
        """LIVE-CARRIER AGREEMENT (B5): every live source-ref enumeration in
        the B5 subset agrees with the authoritative C2 clause on three
        properties -- resolved by first confirming each property's anchor
        phrase is ACTUALLY PRESENT in the authoritative registry text (001)
        at assertion time, rather than a hardcoded copy divorced from it,
        and then confirming each carrier expresses the SAME property (in its
        own wording). Historical-defect-record files (task descriptions,
        memory sections, circuit-breaker records) are excluded from this
        comparison, per the task's explicit exclusion note -- they narrate
        prior defects and are not live prescriptive carriers."""
        # Anchor: confirm the three properties are actually present in 001
        # (the authoritative source) before trusting them as "the current
        # authoritative form" to compare other carriers against.
        self.assertTrue(_contains(self.workflow_policy_text, "SEPARATE refs"))
        self.assertTrue(_contains(self.workflow_policy_text, "INDEPENDENTLY PER FIELD"))
        self.assertTrue(_contains(self.workflow_policy_text, "recorded as an explicit `N/A`"))

        # Agreement: 004 and 007-fix-ci each express the same three
        # properties in their own carrier-specific wording.
        per_carrier_properties = {
            "004": (
                "judged INDEPENDENTLY PER FIELD",
                "is recorded as `N/A` only for a genuinely pre-PR finding",
                "is recorded as `N/A` whenever no thread exists",
            ),
            "007-fix-ci": (
                "SEPARATE source refs",
                "judged INDEPENDENTLY PER FIELD",
                "recorded as `N/A` for a CI check failure",
            ),
        }
        for carrier, properties in per_carrier_properties.items():
            texts = self.carrier_texts[carrier]
            for prop in properties:
                with self.subTest(carrier=carrier, prop=prop):
                    self.assertTrue(
                        any(_contains(t, prop) for t in texts),
                        f"carrier {carrier} does not agree with authoritative C2 on: {prop!r}",
                    )

    # =========================================================================
    # B6 -- SINGLE-WRITE (Ship half + Stage-consumer half)
    # =========================================================================

    def test_b6_single_write_ship_half_states_the_capture_invariant(self) -> None:
        """SINGLE-WRITE (B6), Ship half (004): the capture is the ONLY write
        Ship ever makes to the entry -- Ship MUST NOT edit, amend, back-fill,
        re-classify, or re-prioritize it afterwards, and MUST NOT create a
        second entry for the same expansion."""
        subset = _resolve("B6")
        self.assertEqual(subset, frozenset({"004", "008"}))
        texts = self.carrier_texts["004"]
        self.assertTrue(any(_contains(t, "SINGLE-WRITE CAPTURE INVARIANT") for t in texts))
        self.assertTrue(
            any(
                _contains(
                    t,
                    "Ship MUST NOT edit, amend, back-fill, re-classify, or re-prioritize a captured entry afterwards",
                )
                for t in texts
            )
        )

    def test_b6_single_write_negative_guard_rejects_deferred_write_back(self) -> None:
        """Non-vacuous negative guard: no B6-subset carrier may instruct that
        the PR number and review-thread ID are recorded LATER, back into the
        entry, rather than at capture time -- the historical defect quoted
        verbatim in the task text (`"only afterward record the PR and
        review-thread IDs in the captured stash entry"`)."""
        defective_phrase = _normalize(
            "only afterward record the PR and review-thread IDs in the captured stash entry"
        )
        for carrier in _resolve("B6"):
            for text in self.carrier_texts[carrier]:
                with self.subTest(carrier=carrier):
                    self.assertNotIn(defective_phrase, _normalize(text))

    def test_b6_single_write_negative_guard_is_non_vacuous(self) -> None:
        """Proves the SINGLE-WRITE negative guard fires against the exact
        historical defective wording quoted in the task text."""
        historical_defective_text = (
            "Capture the six-field payload at classification time, then only "
            "afterward record the PR and review-thread IDs in the captured "
            "stash entry once they become available."
        )
        self.assertIn(
            _normalize("only afterward record the PR and review-thread IDs in the captured stash entry"),
            _normalize(historical_defective_text),
        )

    def test_b6_single_write_stage_consumer_half_requires_no_ship_write(self) -> None:
        """SINGLE-WRITE (B6), Stage-consumer half (008): Stage reconciles the
        entry under its OWN pre-existing stash authority, so late-identifier
        reconciliation requires NO change to Ship's C5 capture-only carve-out
        and NO Ship write -- the consumer-side half of the same invariant."""
        texts = self.carrier_texts["008"]
        self.assertTrue(
            any(
                _contains(
                    t,
                    "reconciliation requires NO change to Ship's C5 capture-only carve-out and NO Ship write",
                )
                for t in texts
            )
        )
        self.assertTrue(
            any(_contains(t, "Stage reconciles the entry under its OWN pre-existing stash authority") for t in texts)
        )

    # =========================================================================
    # B3 -- CAPTURE-FIRST, NO-PR/NO-THREAD-ASSUMPTION
    # =========================================================================

    def test_b3_capture_first_precondition_for_closing_present_on_full_subset(self) -> None:
        """CAPTURE-FIRST (B3): every carrier in the full B3/C2 subset states
        that capture is a PRECONDITION for closing the out-of-scope finding
        -- fixing, replying, or resolving before capture is prohibited."""
        subset = _resolve("B3")
        self.assertEqual(
            subset,
            frozenset({"001", "004", "005", "006", "007-pr-lifecycle", "007-fix-ci"}),
        )
        expectations = {
            "001": "Capture is a PRECONDITION for closing an out-of-scope finding",
            "004": "capture is a precondition for closing the finding under P-021 C2",
            "005": "before the finding is closed in any form",
            "006": "makes capture a precondition for closing the finding",
            "007-pr-lifecycle": "makes capture a precondition for closing the finding",
            "007-fix-ci": "BEFORE the finding is closed in any form",
        }
        for carrier in subset:
            texts = self.carrier_texts[carrier]
            marker = expectations[carrier]
            with self.subTest(carrier=carrier):
                self.assertTrue(
                    any(_contains(t, marker) for t in texts),
                    f"carrier {carrier} missing capture-first marker: {marker!r}",
                )

    def test_b3_no_pr_no_thread_assumption_negative_guard_universal(self) -> None:
        """NO-PR/NO-THREAD-ASSUMPTION (B3), UNIVERSAL negative guard across
        the full C2 row: no carrier may make PR or thread EXISTENCE a
        precondition for capture -- the historical defect quoted verbatim in
        the task text (`"source refs (PR number, review-thread ID when
        applicable, ...)"`), which reads as though capture itself depends on
        those refs already existing."""
        defective_phrase = _normalize(
            "source refs (PR number, review-thread ID when applicable, ...)"
        )
        for carrier in _matrix_carriers("C2"):
            for text in self.carrier_texts[carrier]:
                with self.subTest(carrier=carrier):
                    self.assertNotIn(defective_phrase, _normalize(text))

    def test_b3_no_pr_no_thread_assumption_negative_guard_is_non_vacuous(self) -> None:
        """Proves the NO-PR/NO-THREAD-ASSUMPTION guard fires against the
        exact historical defective wording quoted verbatim in the task
        text."""
        historical_defective_text = (
            "Capture requires source refs (PR number, review-thread ID when "
            "applicable, ...) to already be available."
        )
        self.assertIn(
            _normalize("source refs (PR number, review-thread ID when applicable, ...)"),
            _normalize(historical_defective_text),
        )

    def test_b3_no_pr_no_thread_assumption_positive_never_conditional(self) -> None:
        """Positive companion: the B3 subset's carriers explicitly state
        capture is NEVER conditional on a PR or thread existing."""
        expectations = {
            "001": "capture is NEVER conditional on a PR or a review thread existing",
            "004": "it is NEVER conditional on a PR or thread existing",
            "007-fix-ci": "Existence of a PR or a thread is never a precondition for capture",
        }
        for carrier, marker in expectations.items():
            texts = self.carrier_texts[carrier]
            with self.subTest(carrier=carrier):
                self.assertTrue(
                    any(_contains(t, marker) for t in texts),
                    f"carrier {carrier} missing never-conditional marker: {marker!r}",
                )

    # =========================================================================
    # B7 -- THREAD-PRESENT-ORDERING
    # =========================================================================

    def test_b7_thread_present_ordering_full_sequence_present_on_subset(self) -> None:
        """THREAD-PRESENT-ORDERING (B7): every carrier in the B7 subset
        states the full ordered sequence -- capture -> reply citing the
        deferred entry ID -> resolve (only after that reply) -> PR/closure
        residual-risk record naming the same ID."""
        subset = _resolve("B7")
        self.assertEqual(
            subset,
            frozenset({"001", "004", "006", "007-pr-lifecycle", "007-fix-ci"}),
        )
        expectations = {
            "001": (
                "reference the deferred entry ID in the review-thread reply "
                "(posted BEFORE the thread is resolved) and in the PR/closure "
                "residual-risk record"
            ),
            "004": "Resolve the thread \u2014 permitted only after that reply is posted",
            "006": "permitted only after the reply citing that ID is posted",
            "007-pr-lifecycle": "permitted only after the reply citing",
            "007-fix-ci": "permitted only after the reply citing that ID is posted",
        }
        for carrier in subset:
            texts = self.carrier_texts[carrier]
            marker = expectations[carrier]
            with self.subTest(carrier=carrier):
                self.assertTrue(
                    any(_contains(t, marker) for t in texts),
                    f"carrier {carrier} missing thread-present ordering marker: {marker!r}",
                )

    def test_b7_thread_present_ordering_reply_omitting_id_does_not_satisfy_c3(self) -> None:
        """THREAD-PRESENT-ORDERING (B7) negative-guard companion: the
        procedural carriers ({004, 006, 007-pr-lifecycle, 007-fix-ci})
        explicitly state that a reply OMITTING the deferred entry ID does
        NOT satisfy C3 -- this is what forbids replying/resolving before
        capture, closing the gap a bare "post a reply" instruction would
        leave open."""
        procedural_subset = frozenset({"004", "006", "007-pr-lifecycle", "007-fix-ci"})
        self.assertTrue(procedural_subset <= _resolve("B7"))
        for carrier in procedural_subset:
            texts = self.carrier_texts[carrier]
            with self.subTest(carrier=carrier):
                self.assertTrue(
                    any(_contains(t, "a reply omitting the deferred entry ID does not satisfy C3") for t in texts),
                    f"carrier {carrier} missing reply-omitting-id-does-not-satisfy-c3 statement",
                )

    # =========================================================================
    # B4 -- SIX-FIELD-PAYLOAD
    # =========================================================================

    def test_b4_six_field_payload_all_fields_enumerated_explicitly_on_subset(self) -> None:
        """SIX-FIELD-PAYLOAD (B4, hardening H7): every carrier in the B4
        subset (005/circuit-breaker is deliberately EXCLUDED -- H7 names
        004/006/007 as the payload carriers and 134.005-T contracts only for
        the capture-before-close requirement, not the payload) enumerates
        ALL SIX capture-payload fields EXPLICITLY, each checked with a
        carrier-specific marker -- not merely by reference to "per C2"."""
        subset = _resolve("B4")
        self.assertEqual(subset, frozenset({"001", "004", "006", "007-pr-lifecycle", "007-fix-ci"}))
        self.assertNotIn("005", subset)
        per_carrier_six_fields = {
            "001": (
                "DEFERRED SCOPE EXPANSION",
                "A one-sentence statement of the expansion",
                "Why it is out of scope, citing C1",
                "Source refs",
                "requires deliberation",
                "Kind and provisional priority",
            ),
            "004": (
                "DEFERRED SCOPE EXPANSION",
                "A one-sentence statement of the expansion",
                "Why it is out of scope, citing P-021 C1",
                "Source refs, with availability judged INDEPENDENTLY PER FIELD",
                "requires deliberation",
                "Kind and a PROVISIONAL priority only",
            ),
            "006": (
                "DEFERRED SCOPE EXPANSION",
                "a one-sentence expansion statement",
                "C1-cited out-of-scope rationale",
                "source refs (PR number, review-thread ID, task ID, feature ID, shipment ID)",
                "requires deliberation",
                "kind plus a PROVISIONAL priority",
            ),
            "007-pr-lifecycle": (
                "DEFERRED SCOPE EXPANSION",
                "A one-sentence statement of the expansion",
                "Why it is out of scope, citing the P-021 C1 test",
                "Source refs \u2014 PR number, review-thread ID, task ID, feature ID",
                "requires deliberation",
                "Kind and a PROVISIONAL priority only",
            ),
            "007-fix-ci": (
                "DEFERRED SCOPE EXPANSION",
                "A one-sentence statement of the expansion",
                "Why it is out of scope, citing the P-021 C1 test",
                "Source refs: task ID, feature ID, and shipment ID are populated whenever",
                "requires deliberation",
                "Kind and a PROVISIONAL priority only",
            ),
        }
        for carrier, field_markers in per_carrier_six_fields.items():
            self.assertEqual(len(field_markers), 6, f"carrier {carrier} field-marker list must name all 6 fields")
            texts = self.carrier_texts[carrier]
            for marker in field_markers:
                with self.subTest(carrier=carrier, marker=marker):
                    self.assertTrue(
                        any(_contains(t, marker) for t in texts),
                        f"carrier {carrier} missing six-field payload marker: {marker!r}",
                    )

    # =========================================================================
    # B16 (full) -- FIX-CI-DUAL-PATH (the CANONICAL, load-bearing B16
    # criterion; regresses fix cycle 1)
    # =========================================================================

    def test_b16_fix_ci_dual_path_present_on_full_declared_subset(self) -> None:
        """FIX-CI-DUAL-PATH (B16, canonical criterion): every carrier in the
        full B16 subset (`B7 INTERSECT B8` = {001, 004, 007-fix-ci}) states
        BOTH C3 dispositions (thread-present AND threadless) and selects
        between them by ACTUAL THREAD AVAILABILITY at classification time,
        never by finding kind or loop name -- the exact fix cycle 1
        defect."""
        subset = _resolve("B16")
        self.assertEqual(subset, frozenset({"001", "004", "007-fix-ci"}))
        selector_markers = {
            "001": ("WHERE A REVIEW THREAD EXISTS", "WHERE NO REVIEW THREAD EXISTS"),
            "004": (
                "a PR exists and the finding already has a review thread at classification time",
                "no review thread exists for the finding at classification time",
            ),
            "007-fix-ci": (
                "the path the finding actually arrives on at classification time",
                "no review thread exists for this",
            ),
        }
        for carrier, markers in selector_markers.items():
            texts = self.carrier_texts[carrier]
            for marker in markers:
                with self.subTest(carrier=carrier, marker=marker):
                    self.assertTrue(
                        any(_contains(t, marker) for t in texts),
                        f"carrier {carrier} missing dual-path selector marker: {marker!r}",
                    )

    def test_b16_fix_ci_dual_path_negative_guard_rejects_finding_kind_selector(self) -> None:
        """Non-vacuous negative guard (fix cycle 1): no B16-subset carrier
        may select the disposition by FINDING KIND rather than actual thread
        availability -- the historical defect quoted verbatim in the task
        text (`"selects between them by FINDING KIND"`)."""
        defective_phrase = _normalize("selects between them by FINDING KIND")
        for carrier in _resolve("B16"):
            for text in self.carrier_texts[carrier]:
                with self.subTest(carrier=carrier):
                    self.assertNotIn(defective_phrase, _normalize(text))
        # Non-vacuity.
        self.assertIn(
            defective_phrase,
            _normalize("Disposition selects between them by FINDING KIND, never by thread availability."),
        )

    def test_b16_fix_ci_dual_path_negative_guard_rejects_thread_never_surfaces_claim(self) -> None:
        """Non-vacuous negative guard (fix cycle 1): fix-ci's own carrier
        text must NOT claim a review thread never surfaces inside a fix-ci
        run -- the historical defect quoted verbatim in the task text
        (`"a review thread never surfaces inside a fix-ci run"`), which
        would make the thread-present path on this carrier unreachable
        prose."""
        defective_phrase = _normalize("a review thread never surfaces inside a fix-ci run")
        for text in self.carrier_texts["007-fix-ci"]:
            self.assertNotIn(defective_phrase, _normalize(text))
        # Non-vacuity.
        self.assertIn(
            defective_phrase,
            _normalize(
                "Because a review thread never surfaces inside a fix-ci run, "
                "only the threadless path applies here."
            ),
        )

    # =========================================================================
    # B17 -- FIX-CI-ENTRY-REUSE (carrier-role-scoped: {004, 008, 007-fix-ci})
    # =========================================================================

    def test_b17_fix_ci_entry_reuse_ship_full_truth_table(self) -> None:
        """FIX-CI-ENTRY-REUSE (B17), Ship half (004): the full four-case
        disposition truth table (zero matches / exactly-one-confirmed /
        exactly-one-unconfirmed / more-than-one) is present verbatim, and
        the DISCOVERY-STATUS tokens live inside the six-field payload's
        field (2) -- never a seventh field."""
        subset = _resolve("B17")
        self.assertEqual(subset, frozenset({"004", "008", "007-fix-ci"}))
        texts = self.carrier_texts["004"]
        four_case_markers = (
            "Zero matches \u2014 proceed to the C2 capture below",
            "POSITIVELY CONFIRMED to describe the SAME expansion",
            "CANNOT be so confirmed \u2014 not a match for reuse purposes",
            "More than one match \u2014 follow the discovery fail-safe below",
        )
        for marker in four_case_markers:
            with self.subTest(marker=marker):
                self.assertTrue(any(_contains(t, marker) for t in texts))
        self.assertTrue(any(_contains(t, "DISCOVERY-STATUS: AMBIGUOUS") for t in texts))
        self.assertTrue(any(_contains(t, "DISCOVERY-STATUS: LOOKUP-UNAVAILABLE") for t in texts))
        self.assertTrue(
            any(
                _contains(
                    t,
                    "the token lives inside the existing six-field payload's field (2) "
                    "\u2014 it is not a seventh field",
                )
                for t in texts
            )
        )

    def test_b17_fix_ci_entry_reuse_fix_ci_references_ship_procedure_by_name_only(self) -> None:
        """FIX-CI-ENTRY-REUSE (B17), fix-ci half (007-fix-ci): the
        REFERENCE-INTEGRITY-NOT-RESTATEMENT sub-test -- fix-ci cites
        134.004-T's discovery procedure BY NAME ONLY and deliberately does
        NOT reproduce the four-case truth table, so the two surfaces never
        carry two divergent copies of it."""
        texts = self.carrier_texts["007-fix-ci"]
        self.assertTrue(
            any(
                _contains(
                    t,
                    "that procedure is referenced here by name only and is deliberately NOT reproduced",
                )
                for t in texts
            )
        )
        self.assertTrue(any(_contains(t, "134.004-T") for t in texts))
        # And confirm the full four-case truth table wording is genuinely
        # NOT restated on this carrier (proving the reference is by name
        # only, not a disguised copy).
        for text in texts:
            self.assertNotIn(
                _normalize("Zero matches \u2014 proceed to the C2 capture below"),
                _normalize(text),
            )

    def test_b17_fix_ci_entry_reuse_stage_reconciliation_form(self) -> None:
        """FIX-CI-ENTRY-REUSE (B17), Stage half (008): late identifiers
        attach to the EXISTING deferred entry via reconciliation, under
        Stage's own pre-existing authority -- never a new entry and never a
        Ship write."""
        texts = self.carrier_texts["008"]
        self.assertTrue(
            any(
                _contains(t, "reconciliation MUST update the EXISTING deferred entry in place")
                for t in texts
            )
        )

    def test_b17_negative_guard_rejects_no_entry_because_provably_captured(self) -> None:
        """Non-vacuous UNIVERSAL negative guard: no B17-subset carrier may
        state that reuse creates NO entry "because the finding is provably
        already captured" -- the historical defect quoted verbatim in the
        task text. The corrected wording distinguishes reuse (cite the
        existing ID, create no SECOND entry) from a claim that no entry
        exists to reference at all."""
        defective_phrase = _normalize("creates NO entry, because the finding is provably already captured")
        for carrier in _resolve("B17"):
            for text in self.carrier_texts[carrier]:
                with self.subTest(carrier=carrier):
                    self.assertNotIn(defective_phrase, _normalize(text))
        # Non-vacuity.
        self.assertIn(
            defective_phrase,
            _normalize(
                "Reuse creates NO entry, because the finding is provably "
                "already captured, so nothing further is recorded."
            ),
        )


if __name__ == "__main__":
    unittest.main()
