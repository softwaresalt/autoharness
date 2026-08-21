"""Contract tests for the P-021 (Bounded Fix-Cycle Scope Containment and
Deferred Expansion Capture) CLAUSE-BOUNDARY semantics group (134.013-T).

This module OWNS behaviours B1 (C1-GATE), B10 (C4-NON-BYPASS), B11
(C5-BOUNDARY), B12 (STAGE-ONLY-REPRIORITIZATION), B14
(RECONCILIATION-CONSUMER), and B18 (C5-REFERENCE-ROLE). See
``OWNED_BEHAVIOURS`` below.

Per the CROSS-FILE BEHAVIOUR ALLOCATION declared in the archived
134.011-T task spec, the authoritative CLAUSE -> BEHAVIOR ->
CARRIER-SUBSET MAPPING lives in
``tests/test_scope_containment_policy_contract.py`` (134.011-T). This
module imports that mapping (``BEHAVIOR_CARRIER_SUBSETS``) rather than
restating it or hardcoding a carrier list (CARRIER-SET RESOLUTION rule).

Import direction is strictly one-way: this module imports from
134.011-T's module only. It MUST NOT import from
``tests/test_scope_containment_semantics_contract.py`` (134.012-T) --
that dependency edge would make the three-way allocation graph cyclic.
134.012-T is the one that imports from BOTH 134.011-T and this module.
"""

from __future__ import annotations

import re
import unittest

from test_scope_containment_policy_contract import (
    BEHAVIOR_CARRIER_SUBSETS,
    _MARKERS,
    _load_all_texts,
    _load_carrier_texts,
    _normalize,
    _resolve_backlog_artifact,
)

# Behaviours this file OWNS, per the CROSS-FILE BEHAVIOUR ALLOCATION.
OWNED_BEHAVIOURS = frozenset({"B1", "B10", "B11", "B12", "B14", "B18"})


def _resolve(behavior_id: str) -> frozenset[str]:
    """CARRIER-SET RESOLUTION: resolve a behaviour's carrier subset from the
    authoritative ``BEHAVIOR_CARRIER_SUBSETS`` mapping in 134.011-T's module.
    This module MUST NOT restate the matrix or hardcode a carrier list."""
    return BEHAVIOR_CARRIER_SUBSETS[behavior_id]


def _contains(haystack: str, needle: str) -> bool:
    return _normalize(needle) in _normalize(haystack)


def _extract_paragraph_starting_with(text: str, prefix: str) -> str:
    """Extracts the single line (paragraph) whose stripped content starts with
    ``prefix``. Used for the C4 negative guard so it inspects only the
    OPERATIVE clause statement on a surface, not an unrelated historical
    quotation elsewhere in the same file (134.013's "deliberation" surface,
    019-DL (backlog artifact, resolved via ``_resolve_backlog_artifact`` --
    not a hardcoded ``queue/`` path), legitimately quotes the historical
    defective C4 wording inside its own AMENDMENT note as a documented
    correction -- a blind whole-file substring scan would false-positive on
    that legitimate quotation, so this helper narrows the scan to the
    numbered clause line itself)."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped
    raise AssertionError(f"no paragraph starting with {prefix!r} found")


# Historical defective C4 wording (Staging PR #372 review-fix cycle 1,
# 019-DL (backlog artifact, location resolved not hardcoded) "C4 AMENDMENT"
# note): the clause originally
# closed its non-bypass list with a sentence naming ONE authorization as
# sufficient to expand the ACTIVE fix cycle -- an in-cycle bypass license,
# not the FORWARD-acting/separate-work-unit semantics the corrected clause
# states.
_C4_DEFECTIVE_BYPASS_PHRASE = "only an explicit operator authorization"

# Historical defective C5 wording (019-DL (backlog artifact, location
# resolved not hardcoded) "C5 AMENDMENT" note): the clause originally
# prohibited Ship from "removing" stash entries
# WITHOUT QUALIFICATION, which would forbid Ship's own correct, manifest-
# derived post-merge Step 7 `backlogit_stash_remove` retirement. The corrected
# clause qualifies the prohibition with DISCRETIONARY/DISCRETIONARILY.
_C5_UNQUALIFIED_REMOVE_PHRASE = "or remove them"

# Historical defective B14 wording (Stage reconciliation "Anti-duplication"
# obligation): a defect would have Stage *remove* (destructively) rather than
# *archive* the duplicate entries it finds during reconciliation, which
# contradicts the ARCHIVE-not-REMOVE disposition and the backlogit tool
# protocol (no `stash remove` subcommand; `backlogit_stash_remove` deprecated
# in favour of `backlogit_stash_archive`).
_B14_DEFECTIVE_REMOVE_DUPLICATES_PHRASE = "removes the duplicates under its own authority"


class ScopeContainmentBoundaryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        all_texts = _load_all_texts()
        cls.carrier_texts = _load_carrier_texts(all_texts)
        cls.workflow_policy_text = all_texts["workflow_policy"]
        cls.ship_template_text = all_texts["ship_template"]
        cls.ship_dogfood_text = all_texts["ship_dogfood"]
        cls.stage_template_text = all_texts["stage_template"]
        cls.stage_dogfood_text = all_texts["stage_dogfood"]
        cls.role_enforcement_template_text = all_texts["role_enforcement_template"]
        cls.role_enforcement_dogfood_text = all_texts["role_enforcement_dogfood"]
        cls.orchestrator_template_text = all_texts["orchestrator_template"]
        cls.orchestrator_dogfood_text = all_texts["orchestrator_dogfood"]
        cls.feature_flow_dark_template_text = all_texts["feature_flow_dark_template"]
        cls.feature_flow_dark_dogfood_text = all_texts["feature_flow_dark_dogfood"]
        cls.github_pr_automation_template_text = all_texts["github_pr_automation_template"]
        cls.github_pr_automation_dogfood_text = all_texts["github_pr_automation_dogfood"]
        cls.pr_lifecycle_template_text = all_texts["pr_lifecycle_template"]
        cls.fix_ci_template_text = all_texts["fix_ci_template"]

        # Plan clause table (one of the three surfaces the C4 universal
        # negative guard sweeps, per the task's explicit "plan clause table"
        # requirement).
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[1]
        plan_path = (
            repo_root / "docs" / "plans" / "2026-08-18-bounded-fix-cycle-scope-containment-plan.md"
        )
        cls.plan_text = plan_path.read_text(encoding="utf-8")

        # Deliberation artifact (the third surface the C4 universal negative
        # guard sweeps). Resolved via the shared lifecycle-stable resolver
        # (queue/ -> archive/ probe) rather than a hardcoded queue/ path,
        # since 019-DL's lifecycle location is not stable across archival.
        deliberation_path = _resolve_backlog_artifact("019-DL", repo_root=repo_root)
        cls.deliberation_text = deliberation_path.read_text(encoding="utf-8")

    # -- shared self-consistency check -------------------------------------

    def test_owned_behaviours_are_declared_in_the_authoritative_mapping(self) -> None:
        """Every behaviour this file claims to own must resolve against
        134.011-T's authoritative BEHAVIOR_CARRIER_SUBSETS mapping -- an
        owned ID absent from that mapping would be exactly the kind of
        invisible/unregistered assertion MATRIX CORRECTION 5 exists to
        prevent."""
        for behavior_id in OWNED_BEHAVIOURS:
            with self.subTest(behavior_id=behavior_id):
                self.assertIn(behavior_id, BEHAVIOR_CARRIER_SUBSETS)

    # -- B1: C1-GATE ---------------------------------------------------------

    def test_b1_c1_gate_present_on_full_declared_subset(self) -> None:
        """B1 (C1-GATE): every carrier in B1's resolved subset must gate its
        fix-cycle loop on a P-021 C1 same-contract-surface classification
        check. This behaviour exists because the original coverage matrix
        (before MATRIX CORRECTION 3) would not have detected a carrier
        omitted from C1's row, since the completeness guard at that point
        checked only C2 and C3."""
        subset = _resolve("B1")
        self.assertTrue(subset, "B1 subset must not be empty")
        for carrier in subset:
            with self.subTest(carrier=carrier):
                marker = _MARKERS[("C1", carrier)]
                texts = self.carrier_texts[carrier]
                self.assertTrue(
                    any(_contains(t, marker) for t in texts),
                    f"C1 gate marker missing from carrier {carrier}: {marker!r}",
                )

    # -- B10: C4-NON-BYPASS ----------------------------------------------

    def test_b10_c4_non_bypass_present_on_full_declared_subset(self) -> None:
        """B10 (C4-NON-BYPASS): every carrier in B10's resolved subset must
        state that its own pressure/exhaustion/mode does not authorize
        scope expansion (MATRIX CORRECTION 3: C4 previously listed only 004
        and 009, though 006 and 007-pr-lifecycle both carry the
        cycle-exhaustion-does-not-authorize-expansion annotation in their
        Stop Conditions rows)."""
        subset = _resolve("B10")
        self.assertTrue(subset)
        for carrier in subset:
            with self.subTest(carrier=carrier):
                marker = _MARKERS[("C4", carrier)]
                texts = self.carrier_texts[carrier]
                self.assertTrue(
                    any(_contains(t, marker) for t in texts),
                    f"C4 non-bypass marker missing from carrier {carrier}: {marker!r}",
                )

    def test_b10_authoritative_surface_states_full_active_cycle_boundary(self) -> None:
        """B10, authoritative surface (001): C4 is a BOUNDARY ON THE ACTIVE
        FIX CYCLE, not a list of insufficient authorizations ending in a
        sufficient one. No authorization -- including explicit operator
        authorization -- expands the fix cycle that discovered the
        expansion; authorization is FORWARD-acting only, opening a
        SEPARATE work unit through C2 capture + mandatory C6 deliberation,
        never retroactively expanding the in-flight cycle."""
        text = self.workflow_policy_text
        self.assertTrue(
            _contains(text, "AND NEITHER DOES ANY AUTHORIZATION, INCLUDING EXPLICIT OPERATOR AUTHORIZATION"),
        )
        self.assertTrue(
            _contains(text, "Nothing expands the fix cycle that discovered the expansion"),
        )
        self.assertTrue(
            _contains(
                text,
                "Authorization is therefore a FORWARD act that opens new work, "
                "never a RETROACTIVE one that makes an already-discovered "
                "expansion in-scope for the cycle in flight",
            ),
        )

    def test_b10_universal_negative_guard_no_carrier_reintroduces_bypass_phrasing(self) -> None:
        """Non-vacuous universal negative guard (134.013-T criterion): none
        of the C4 carriers, the plan clause table, or the deliberation
        artifact's OPERATIVE clause-4 statement may reintroduce the
        historical defective wording "Only an explicit operator
        authorization recorded as [a] new/expanded approved scope does" --
        a closing sentence that reads as naming ONE authorization
        sufficient to expand the ACTIVE fix cycle (the exact bypass C1/C4
        forbid). See 019-DL (backlog artifact, location resolved not
        hardcoded) "C4 AMENDMENT" note."""
        subset = _resolve("B10")
        for carrier in subset:
            for text in self.carrier_texts[carrier]:
                with self.subTest(carrier=carrier):
                    self.assertNotIn(
                        _C4_DEFECTIVE_BYPASS_PHRASE,
                        _normalize(text),
                        f"carrier {carrier} reintroduces the C4 bypass phrasing",
                    )

        plan_c4_row = _extract_paragraph_starting_with(self.plan_text, "| C4 Non-bypass")
        self.assertNotIn(_C4_DEFECTIVE_BYPASS_PHRASE, _normalize(plan_c4_row))

        deliberation_c4_clause = _extract_paragraph_starting_with(
            self.deliberation_text, "4. **Non-bypass.**"
        )
        self.assertNotIn(_C4_DEFECTIVE_BYPASS_PHRASE, _normalize(deliberation_c4_clause))

    def test_b10_universal_negative_guard_is_non_vacuous(self) -> None:
        """Proves the guard above actually fires: construct the historical
        defective wording in-memory and confirm the same detection logic
        flags it, rather than trusting an unvalidated 'looks right' guard."""
        defective_carrier_text = (
            "Review pressure, finding severity, dark factory mode, circuit-breaker "
            "exhaustion, and convenience never authorize expansion. Only an explicit "
            "operator authorization recorded as a new/expanded approved scope does."
        )
        self.assertIn(_C4_DEFECTIVE_BYPASS_PHRASE, _normalize(defective_carrier_text))

        defective_plan_row = (
            "| C4 Non-bypass | Review pressure, severity, dark factory mode (P-017), "
            "circuit-breaker exhaustion, and convenience never authorize expansion. "
            "Only an explicit operator authorization recorded as new/expanded "
            "approved scope does. |"
        )
        self.assertIn(_C4_DEFECTIVE_BYPASS_PHRASE, _normalize(defective_plan_row))

        defective_deliberation_clause = (
            "4. **Non-bypass.** Review pressure, finding severity, dark factory mode "
            "(P-017), circuit-breaker exhaustion, and apparent convenience never "
            "authorize expansion. Only an explicit operator authorization recorded as "
            "a new/expanded approved scope does."
        )
        self.assertIn(_C4_DEFECTIVE_BYPASS_PHRASE, _normalize(defective_deliberation_clause))

        # And confirm the CURRENT, corrected wording does NOT trip the guard
        # (otherwise the guard would be unsatisfiable rather than genuinely
        # discriminating).
        self.assertNotIn(
            _C4_DEFECTIVE_BYPASS_PHRASE,
            _normalize(
                "AND NEITHER DOES ANY AUTHORIZATION, INCLUDING EXPLICIT OPERATOR "
                "AUTHORIZATION. Nothing expands the fix cycle that discovered the "
                "expansion."
            ),
        )

    # -- B11: C5-BOUNDARY (001 + 002 ONLY) --------------------------------

    def test_b11_c5_boundary_subset_is_001_and_002_only(self) -> None:
        """B11's declared subset is 001[A] and 002[N] ONLY -- explicitly NOT
        003, which carries B18 (the reference-only role) instead. This
        assertion resolves the subset from the shared mapping rather than
        hardcoding it, and merely confirms the SIZE/membership invariant
        the rest of this test class depends on."""
        subset = _resolve("B11")
        self.assertEqual(len(subset), 2)
        self.assertIn("001", subset)
        self.assertIn("002", subset)
        self.assertNotIn("003", subset)

    def test_b11_c5_boundary_creation_grant_and_named_forbidden_verbs(self) -> None:
        """B11 (C5-BOUNDARY): 001 and 002 must both carry (a) the
        capture-only creation grant, (b) the forbidden verbs BY NAME --
        discretionary REMOVAL and discretionary ARCHIVAL, governed by one
        DISCRETIONARY qualifier (owner 134.002-T; C5 ARCHIVAL AMENDMENT in
        019-DL (backlog artifact, location resolved not hardcoded) --
        archival was originally omitted from
        the prohibition even though 134.002-T always named both verbs), and
        (c) the manifest-derived post-merge Step 7 cleanup exception."""
        # (a) creation grant
        self.assertTrue(_contains(self.workflow_policy_text, "Ship MAY create stash entries for capture only"))
        self.assertTrue(_contains(self.ship_template_text, "create a capture-only stash entry (P-021 C5)"))
        self.assertTrue(_contains(self.ship_dogfood_text, "create a capture-only stash entry (P-021 C5)"))

        # (b) forbidden verbs by name, one DISCRETIONARY qualifier governing both
        self.assertTrue(
            _contains(self.workflow_policy_text, "DISCRETIONARILY remove, or DISCRETIONARILY archive them"),
        )
        self.assertTrue(_contains(self.ship_template_text, "discretionary removal or archival of stash entries"))
        self.assertTrue(_contains(self.ship_dogfood_text, "discretionary removal or archival of stash entries"))

        # (c) manifest-derived cleanup exception (Ship's post-merge Step 7)
        self.assertTrue(
            _contains(
                self.workflow_policy_text,
                "manifest-derived retirement of the source stash entry that fed the shipped scope",
            ),
        )
        self.assertTrue(
            _contains(
                self.ship_template_text,
                "a manifest-derived closure operation, distinct from discretionary removal",
            ),
        )
        self.assertTrue(
            _contains(
                self.ship_dogfood_text,
                "a manifest-derived closure operation, distinct from discretionary removal",
            ),
        )

    def test_b11_c5_exception_negative_guard_no_unqualified_remove(self) -> None:
        """C5-EXCEPTION sub-test: negative guard against the historical
        defective wording that prohibited Ship from "removing" stash
        entries WITHOUT QUALIFICATION (019-DL (backlog artifact, location
        resolved not hardcoded) "C5 AMENDMENT" note) -- a blanket verb
        prohibition that would have made
        Ship's own correct, manifest-derived post-merge Step 7
        `backlogit_stash_remove` retirement a C5 violation."""
        for text in (self.workflow_policy_text, self.ship_template_text, self.ship_dogfood_text):
            self.assertNotIn(_C5_UNQUALIFIED_REMOVE_PHRASE, _normalize(text))

    def test_b11_c5_exception_negative_guard_is_non_vacuous(self) -> None:
        """Proves the C5-EXCEPTION guard fires against the historical
        defective wording, then confirms the current corrected wording does
        not trip it."""
        defective = (
            "Ship MAY create stash entries for capture only, and MUST NOT triage, "
            "prioritize, re-classify, edit, harvest, deliberate on, or remove them."
        )
        self.assertIn(_C5_UNQUALIFIED_REMOVE_PHRASE, _normalize(defective))

        corrected = (
            "Ship MAY create stash entries for capture only, and MUST NOT triage, "
            "prioritize, re-classify, edit, harvest, deliberate on, DISCRETIONARILY "
            "remove, or DISCRETIONARILY archive them."
        )
        self.assertNotIn(_C5_UNQUALIFIED_REMOVE_PHRASE, _normalize(corrected))

    def test_b11_c5_exception_provenance_distinction_agreement_h2(self) -> None:
        """Positive agreement check (hardening H2): both 001 and 002 must
        draw the DISCRETIONARY-vs-MANIFEST-DERIVED distinction by
        PROVENANCE, not by verb, so the exception cannot regress silently
        into a verb-only carve-out."""
        self.assertTrue(_contains(self.workflow_policy_text, "manifest-derived post-merge cleanup exception survives unchanged"))
        self.assertTrue(
            _contains(
                self.ship_template_text,
                "distinct from discretionary removal",
            ),
        )
        self.assertTrue(
            _contains(
                self.ship_dogfood_text,
                "distinct from discretionary removal",
            ),
        )

    # -- B18: C5-REFERENCE-ROLE (003 ONLY) --------------------------------

    def test_b18_c5_reference_role_subset_is_003_only(self) -> None:
        """B18's declared subset is 003[R] ONLY. This behaviour was SPLIT
        OUT of B11 in the owner-contract reconciliation cycle specifically
        because role-enforcement's obligation is recognition/citation, not
        the full C5 boundary semantics B11 demands."""
        subset = _resolve("B18")
        self.assertEqual(subset, frozenset({"003"}))

    def test_b18_c5_reference_role_recognition_and_citation_only(self) -> None:
        """B18 (C5-REFERENCE-ROLE): role-enforcement must assert ONLY (a) a
        capture-only stash write matches the Allowed column and does not
        trigger the fail-closed halt, (b) any OTHER stash op remains a
        P-010 violation that MUST halt, (c) citation of P-021 C5 by
        policy ID/clause label (not restated text), and (d) the
        pre-existing fail-closed rationale paragraph is unchanged."""
        for text in (self.role_enforcement_template_text, self.role_enforcement_dogfood_text):
            with self.subTest(source=text[:40]):
                # (a)
                self.assertTrue(
                    _contains(
                        text,
                        "matches the acting agent's Allowed column via P-021 C5",
                    ),
                )
                self.assertTrue(
                    _contains(text, "does NOT trigger the fail-closed unclassified-mutation halt"),
                )
                # (b)
                self.assertTrue(
                    _contains(
                        text,
                        "Any OTHER stash operation by Ship",
                    ),
                )
                self.assertTrue(_contains(text, "remains a P-010 violation and MUST"))
                # (c) citation by ID/clause label
                self.assertTrue(_contains(text, "P-021 C2"))
                self.assertTrue(_contains(text, "P-021 C5"))
                # (d) pre-existing fail-closed rationale paragraph unchanged
                self.assertTrue(
                    _contains(
                        text,
                        "A default-allow policy for unlisted operations undermines",
                    ),
                )

    def test_b18_c5_reference_role_negative_guard_does_not_over_demand(self) -> None:
        """Negative guard proving this test does NOT over-demand: 003 must
        NOT be required to carry the creation grant ("Ship MAY create stash
        entries for capture only") or the manifest-derived cleanup
        exception wording ("manifest-derived closure operation") -- role-
        enforcement's job is recognition/citation, not restating the full
        C5 boundary. Requiring those phrases here would recreate the exact
        defect the B11/B18 split fixed: a `[R]` reference-only carrier
        wrongly demanded to reproduce clause text."""
        for text in (self.role_enforcement_template_text, self.role_enforcement_dogfood_text):
            self.assertNotIn(
                "ship may create stash entries for capture only",
                _normalize(text),
            )
            self.assertNotIn("manifest-derived closure operation", _normalize(text))

    # -- B12: STAGE-ONLY-REPRIORITIZATION ----------------------------------

    def test_b12_stage_only_reprioritization_present_on_full_declared_subset(self) -> None:
        """B12 (STAGE-ONLY-REPRIORITIZATION): every carrier in B12's
        resolved subset must state that a captured deferred-scope-expansion
        entry's priority is PROVISIONAL ONLY, and that re-prioritization and
        triage remain Stage-only."""
        subset = _resolve("B12")
        self.assertTrue(subset)
        for carrier in subset:
            texts = self.carrier_texts[carrier]
            with self.subTest(carrier=carrier):
                self.assertTrue(
                    any(_contains(t, "provisional priority") for t in texts),
                    f"provisional-priority marker missing from carrier {carrier}",
                )

    def test_b12_stage_only_reprioritization_explicit_stage_only_wording(self) -> None:
        """The provisional-priority markers alone do not prove the
        Stage-only allocation; each procedural carrier must ALSO state that
        re-prioritization/triage remain Stage-only, and the authoritative
        surface (001) must forbid Ship from prioritizing at all (which is
        how Stage-only reprioritization is allocated on the authoritative
        surface, per the Relationship-to-P-010 cross-reference)."""
        for carrier in ("004", "006", "007-pr-lifecycle", "007-fix-ci"):
            texts = self.carrier_texts[carrier]
            with self.subTest(carrier=carrier):
                self.assertTrue(any(_contains(t, "stage-only") for t in texts))

        self.assertTrue(
            _contains(
                self.workflow_policy_text,
                "MUST NOT triage, prioritize, re-classify, edit, harvest, deliberate on",
            ),
        )

    # -- B14: RECONCILIATION-CONSUMER (008 ONLY) ---------------------------

    def test_b14_reconciliation_consumer_subset_is_008_only(self) -> None:
        subset = _resolve("B14")
        self.assertEqual(subset, frozenset({"008"}))

    def test_b14_reconciliation_trigger_is_two_part_and_independent(self) -> None:
        """B14 obligation (1): the trigger is TWO independently triggered
        obligations, not one -- (1a) unconditional duplicate detection over
        EVERY triaged entry regardless of field population, and (1b)
        late-identifier reconciliation gated on an `N/A` source-ref field.
        Neither trigger may be stated as a precondition of the other."""
        for text in (self.stage_template_text, self.stage_dogfood_text):
            with self.subTest(source=text[:40]):
                self.assertTrue(
                    _contains(text, "Duplicate detection is UNCONDITIONAL"),
                )
                self.assertTrue(
                    _contains(text, "regardless of whether any source-ref field is"),
                )
                self.assertTrue(
                    _contains(text, "Late-identifier reconciliation is MANDATORY"),
                )
                self.assertTrue(
                    _contains(
                        text,
                        "TRIGGERED whenever any source-ref field of the entry is recorded",
                    ),
                )
                self.assertTrue(
                    _contains(text, "are independent"),
                )

    def test_b14_retrieval_source_and_join_key(self) -> None:
        """B14 obligation (2): Stage recovers late identifiers from the
        SHIP-OWNED RESIDUAL-RISK RECORDS that cite the deferred entry ID
        (the join key), and MUST NOT ask Ship to supply them by editing the
        entry (which would violate the single-write invariant)."""
        for text in (self.stage_template_text, self.stage_dogfood_text):
            with self.subTest(source=text[:40]):
                self.assertTrue(_contains(text, "SHIP-OWNED RESIDUAL-RISK RECORDS"))
                self.assertTrue(_contains(text, "MUST NOT ask Ship to supply them"))

    def test_b14_stage_authority_discharges_cross_clause_c5_carriage(self) -> None:
        """B14 obligation (3): Stage reconciles under its OWN pre-existing
        stash authority, requiring NO change to Ship's C5 capture-only
        carve-out and NO Ship write -- this explicitly discharges 008's
        cross-clause C5 carriage (008 is a C5 carrier per the authoritative
        matrix precisely because of this obligation, not because Stage
        performs any capture-only stash write itself)."""
        for text in (self.stage_template_text, self.stage_dogfood_text):
            with self.subTest(source=text[:40]):
                self.assertTrue(_contains(text, "Stage reconciles the entry under its OWN pre-existing stash authority"))
                self.assertTrue(_contains(text, "NO Ship write"))
                self.assertTrue(_contains(text, "capture-only carve-out"))

    def test_b14_anti_duplication_is_five_part_compound(self) -> None:
        """B14 obligation (4), the compound anti-duplication requirement:
        (i) in-place update of the EXISTING entry, (ii) the deferred entry
        ID as the stable identity across the expansion's lifetime, (iii)
        detection governed by the unconditional trigger, (iv) reconciling
        INTO the EARLIEST-CAPTURED entry and ARCHIVING (never removing) the
        duplicates, and (v) recording the merge (surviving ID + archived
        duplicate IDs + disposition)."""
        for text in (self.stage_template_text, self.stage_dogfood_text):
            with self.subTest(source=text[:40]):
                self.assertTrue(_contains(text, "MUST update the EXISTING deferred entry in place"))
                self.assertTrue(_contains(text, "MUST NOT create"))
                self.assertTrue(_contains(text, "stable identity for the expansion across its whole lifetime"))
                self.assertTrue(_contains(text, "EARLIEST-CAPTURED entry"))
                self.assertTrue(_contains(text, "ARCHIVES"))
                self.assertTrue(_contains(text, "NEVER by destructive removal"))
                self.assertTrue(_contains(text, "SURVIVING entry ID"))
                self.assertTrue(_contains(text, "ARCHIVED"))

    def test_b14_anti_duplication_negative_guard_no_removes_duplicates(self) -> None:
        """Non-vacuous negative guard against the historical defective
        wording that would have Stage *remove* (destructively) rather than
        *archive* the duplicate entries it finds -- contradicting both the
        ARCHIVE-not-REMOVE disposition and the backlogit tool protocol (no
        `stash remove` subcommand; `backlogit_stash_remove` deprecated in
        favour of `backlogit_stash_archive`)."""
        for text in (self.stage_template_text, self.stage_dogfood_text):
            self.assertNotIn(_B14_DEFECTIVE_REMOVE_DUPLICATES_PHRASE, _normalize(text))

    def test_b14_anti_duplication_negative_guard_is_non_vacuous(self) -> None:
        defective = (
            "If Stage finds more than one entry describing the same expansion, it "
            "reconciles into the earliest-captured entry and removes the duplicates "
            "under its own authority."
        )
        self.assertIn(_B14_DEFECTIVE_REMOVE_DUPLICATES_PHRASE, _normalize(defective))

        corrected = (
            "If Stage finds more than one entry describing the same expansion, it "
            "reconciles into the EARLIEST-CAPTURED entry and ARCHIVES the duplicates "
            "under its own authority via backlogit's stash ARCHIVE operation."
        )
        self.assertNotIn(_B14_DEFECTIVE_REMOVE_DUPLICATES_PHRASE, _normalize(corrected))

    def test_b14_non_blocking(self) -> None:
        """B14 obligation (5): a missing late identifier is NEVER a gate on
        deliberation, planning, or harvest, and is NOT a C3 or C6
        shortfall; the `N/A` stands as a truthful terminal record."""
        for text in (self.stage_template_text, self.stage_dogfood_text):
            with self.subTest(source=text[:40]):
                self.assertTrue(_contains(text, "STANDS as a truthful"))
                self.assertTrue(_contains(text, "NEVER a gate on deliberation, planning, or harvest"))

    def test_b14_idempotence(self) -> None:
        """B14 obligation (6): reconciliation over an already-reconciled
        entry is a no-op; it never overwrites a concrete identifier with
        `N/A`, and never rewrites a concrete identifier already recorded."""
        for text in (self.stage_template_text, self.stage_dogfood_text):
            with self.subTest(source=text[:40]):
                self.assertTrue(_contains(text, "already-reconciled entry is a no-op"))
                self.assertTrue(_contains(text, "never overwrites"))

    def test_b14_provenance_audit_output_four_forms(self) -> None:
        """B14 obligation (7): the outcome is recorded for ALL FOUR CASES --
        (i) successful reconciliation (identifiers + residual-risk record),
        (ii) no-result reconciliation ("no late identifier found"
        explicitly), (iii) duplicate merge (surviving ID + archived
        duplicate IDs + disposition), and (iv) a clean duplicate scan
        (unconditional detection found nothing) -- because an unrecorded
        clean scan is indistinguishable from a scan that never ran."""
        for text in (self.stage_template_text, self.stage_dogfood_text):
            with self.subTest(source=text[:40]):
                self.assertTrue(_contains(text, "ALL FOUR CASES"))
                self.assertTrue(_contains(text, "no late identifier found"))
                self.assertTrue(_contains(text, "SURVIVING entry ID"))
                self.assertTrue(_contains(text, "CLEAN DUPLICATE SCAN") or _contains(text, "clean duplicate scan") or _contains(text, "clean scan"))

    def test_b14_reference_style_citation_not_restated_clause_text(self) -> None:
        """B14's final requirement: the reconciliation workflow references
        P-021 C5 and C6 BY POLICY ID AND CLAUSE LABEL; it does not restate
        the authoritative clause text (which lives solely in
        `templates/policies/workflow-policies.md.tmpl`, owned by
        134.001-T)."""
        for text in (self.stage_template_text, self.stage_dogfood_text):
            with self.subTest(source=text[:40]):
                self.assertTrue(
                    any(
                        _contains(text, phrase)
                        for phrase in (
                            "References P-021 C5 and C6 by policy ID and clause label",
                            "This reconciliation workflow references P-021 C5 and C6 by policy ID and clause label",
                        )
                    ),
                )


if __name__ == "__main__":
    unittest.main()
