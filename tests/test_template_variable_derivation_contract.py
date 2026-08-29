"""Contract tests for 142-F: verify-workspace template-variable derivation
conformance with the install-harness resolution contract
(`.github/skills/install-harness/SKILL.md`, constraint C1 sole source of
truth).

Task mapping (150-S manifest):
    142.001-T -- ClassificationTableTests, CleanPairIntersectionTests,
                 RatchetContractTests (T0a/T0b)
    142.002-T -- TierRouteShapeTests (tier1/2/3 + orchestrator polymorphism)
    142.003-T -- RoleRouteAndEscalationTests (stage/ship + raw/prose split)
    142.004-T -- InstallShapeTests (structural rendering hazard, B3/B7)
    142.005-T -- ProfileDerivedMiscConfigTests (GRAPHTOR_BINARY_PATH chain,
                 DEFAULT_BRANCH, provenance table)
    142.006-T -- ParityReconciliationTests (re-asserts the clean-pair
                 byte-identity contract stays green post-derivation)
    142.007-T -- ArtifactRoleCompositionTests (role-aware collapse)

Test-isolation note (149-F/E8158860): every temporary directory used below is
created with the ambient default location (never `dir=Path.cwd()`), per the
full-suite ambient-cwd decoupling fix.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml

from autoharness.verify_workspace import (
    _compose_artifact_variables,
    _derive_anchor_review_variables,
    _derive_escalation_prose_variables,
    _derive_orchestrator_route_variables,
    _derive_raw_escalation_variables,
    _derive_role_route_variables,
    _derive_template_variables,
    _derive_tier_route_variables,
    _effective_escalation_route_for_role,
    _escalation_route_has_any_field,
    _render_template,
    _resolve_artifact_role,
    _resolve_default_branch,
    _resolve_graphtor_binary_path,
    _resolve_graphtor_sources_path,
    verify_workspace,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_live_fixtures() -> tuple[dict, dict, dict, dict]:
    autoharness_dir = _REPO_ROOT / ".autoharness"
    load_yaml = lambda name: yaml.safe_load((autoharness_dir / name).read_text(encoding="utf-8"))
    return (
        load_yaml("harness-manifest.yaml"),
        load_yaml("config.yaml"),
        load_yaml("workspace-profile.yaml"),
        load_yaml("backlog-registry.yaml"),
    )


def _live_variables() -> dict[str, str]:
    manifest, config, profile, registry = _load_live_fixtures()
    return _derive_template_variables(_REPO_ROOT, manifest, config, profile, registry)


# ---------------------------------------------------------------------------
# 142.001-T -- Step 1: per-variable classification table (AC0a).
#
# Two classifications only, per the task's own scheme:
#   RESOLVED-FROM-SOURCE   -- the value is read from a real config/profile
#                             field (or its documented fallback chain), even
#                             when the field's own SKILL.md-documented
#                             default happens to be empty.
#   DERIVE-TO-EMPTY-STRING -- reserved for the RAW escalation pass-through
#                             family, whose SKILL.md rows are explicitly
#                             annotated "(raw, NOT resolved/fallback)" and
#                             which the derivation never subjects to any
#                             fallback chain (constraint C3).
#
# AC0a guard: a variable classified DERIVE-TO-EMPTY-STRING must cite a row
# that documents an empty default; a row documenting a fallback (tier,
# PATH-chain, or literal default) FORBIDS that classification. Enforced by
# `ClassificationTableTests.test_derive_to_empty_string_rows_document_no_fallback`.
# ---------------------------------------------------------------------------

RESOLVED_FROM_SOURCE = "RESOLVED-FROM-SOURCE"
DERIVE_TO_EMPTY_STRING = "DERIVE-TO-EMPTY-STRING"

# variable_name -> (classification, "SKILL.md citation", "fallback documented? (bool)")
# The third element records whether the cited SKILL.md row documents ANY
# fallback/default chain (tier fallback, PATH-chain, or literal default)
# other than a bare empty default -- used by the AC0a guard test below.
VARIABLE_CLASSIFICATION: dict[str, tuple[str, str, bool]] = {
    # --- model_routing tier family (SKILL.md rows 414-425, amendment B6) ---
    "MODEL_ROUTING_TIER1": (RESOLVED_FROM_SOURCE, "SKILL.md row 414 (config.model_routing.tier1.model, object or legacy-string form)", True),
    "MODEL_ROUTING_TIER2": (RESOLVED_FROM_SOURCE, "SKILL.md row 415 (config.model_routing.tier2.model, object or legacy-string form)", True),
    "MODEL_ROUTING_TIER3": (RESOLVED_FROM_SOURCE, "SKILL.md row 416 (config.model_routing.tier3.model, object or legacy-string form)", True),
    "TIER_1_REASONING_EFFORT": (RESOLVED_FROM_SOURCE, "SKILL.md row 417 (config.model_routing.tier1.reasoning_effort)", False),
    "TIER_1_PROVIDER": (RESOLVED_FROM_SOURCE, "SKILL.md row 418 (config.model_routing.tier1.model_provider)", False),
    "TIER_1_FAMILY": (RESOLVED_FROM_SOURCE, "SKILL.md row 419 (config.model_routing.tier1.model_family, default gpt-5.4-mini)", True),
    "TIER_2_REASONING_EFFORT": (RESOLVED_FROM_SOURCE, "SKILL.md row 420 (config.model_routing.tier2.reasoning_effort)", False),
    "TIER_2_PROVIDER": (RESOLVED_FROM_SOURCE, "SKILL.md row 421 (config.model_routing.tier2.model_provider)", False),
    "TIER_2_FAMILY": (RESOLVED_FROM_SOURCE, "SKILL.md row 422 (config.model_routing.tier2.model_family, default claude-sonnet-5)", True),
    "TIER_3_REASONING_EFFORT": (RESOLVED_FROM_SOURCE, "SKILL.md row 423 (config.model_routing.tier3.reasoning_effort)", False),
    "TIER_3_PROVIDER": (RESOLVED_FROM_SOURCE, "SKILL.md row 424 (config.model_routing.tier3.model_provider)", False),
    "TIER_3_FAMILY": (RESOLVED_FROM_SOURCE, "SKILL.md row 425 (config.model_routing.tier3.model_family, default claude-opus-5)", True),
    # --- orchestrator route (SKILL.md rows 426-428, amendment B6) ---
    "ORCHESTRATOR_REASONING_EFFORT": (RESOLVED_FROM_SOURCE, "SKILL.md row 426 (fallback {{TIER_2_REASONING_EFFORT}})", True),
    "ORCHESTRATOR_PROVIDER": (RESOLVED_FROM_SOURCE, "SKILL.md row 427 (fallback {{TIER_2_PROVIDER}})", True),
    "ORCHESTRATOR_FAMILY": (RESOLVED_FROM_SOURCE, "SKILL.md row 428 (own default gpt-5.4, does NOT fall back to tier2)", True),
    # --- role routes (SKILL.md rows 429-434, P-013.5, corrected review-fix cycle 1) ---
    "STAGE_REASONING_EFFORT": (RESOLVED_FROM_SOURCE, "SKILL.md row 429 (fallback {{TIER_3_REASONING_EFFORT}})", True),
    "STAGE_PROVIDER": (RESOLVED_FROM_SOURCE, "SKILL.md row 430 (fallback {{TIER_3_PROVIDER}})", True),
    "STAGE_FAMILY": (RESOLVED_FROM_SOURCE, "SKILL.md row 431 (fallback {{TIER_3_FAMILY}})", True),
    "SHIP_REASONING_EFFORT": (RESOLVED_FROM_SOURCE, "SKILL.md row 432 (fallback {{TIER_2_REASONING_EFFORT}})", True),
    "SHIP_PROVIDER": (RESOLVED_FROM_SOURCE, "SKILL.md row 433 (fallback {{TIER_2_PROVIDER}})", True),
    "SHIP_FAMILY": (RESOLVED_FROM_SOURCE, "SKILL.md row 434 (fallback {{TIER_2_FAMILY}})", True),
    # --- collapsed escalation prose triple (SKILL.md rows 435-437, F02FD596, prose-only) ---
    "ESCALATION_REASONING_EFFORT": (RESOLVED_FROM_SOURCE, "SKILL.md row 435 (nested -> legacy flat -> tier3 per-field, prose-only)", True),
    "ESCALATION_PROVIDER": (RESOLVED_FROM_SOURCE, "SKILL.md row 436 (nested -> legacy flat -> tier3 per-field, prose-only)", True),
    "ESCALATION_FAMILY": (RESOLVED_FROM_SOURCE, "SKILL.md row 437 (nested -> legacy flat -> tier3 per-field, prose-only)", True),
    # --- RAW escalation pass-through (SKILL.md rows 438-446, constraint C3) ---
    "LEGACY_ESCALATION_REASONING_EFFORT": (DERIVE_TO_EMPTY_STRING, "SKILL.md row 438 (raw, NOT resolved/fallback)", False),
    "LEGACY_ESCALATION_PROVIDER": (DERIVE_TO_EMPTY_STRING, "SKILL.md row 439 (raw, NOT resolved/fallback)", False),
    "LEGACY_ESCALATION_FAMILY": (DERIVE_TO_EMPTY_STRING, "SKILL.md row 440 (raw, NOT resolved/fallback)", False),
    "STAGE_ESCALATION_REASONING_EFFORT": (DERIVE_TO_EMPTY_STRING, "SKILL.md row 441 (raw, NOT resolved/fallback)", False),
    "STAGE_ESCALATION_PROVIDER": (DERIVE_TO_EMPTY_STRING, "SKILL.md row 442 (raw, NOT resolved/fallback)", False),
    "STAGE_ESCALATION_FAMILY": (DERIVE_TO_EMPTY_STRING, "SKILL.md row 443 (raw, NOT resolved/fallback)", False),
    "SHIP_ESCALATION_REASONING_EFFORT": (DERIVE_TO_EMPTY_STRING, "SKILL.md row 444 (raw, NOT resolved/fallback)", False),
    "SHIP_ESCALATION_PROVIDER": (DERIVE_TO_EMPTY_STRING, "SKILL.md row 445 (raw, NOT resolved/fallback)", False),
    "SHIP_ESCALATION_FAMILY": (DERIVE_TO_EMPTY_STRING, "SKILL.md row 446 (raw, NOT resolved/fallback)", False),
    # --- anchor review (SKILL.md rows 447-449) ---
    "ANCHOR_REVIEW_PROVIDER": (RESOLVED_FROM_SOURCE, "SKILL.md row 447 (default openai)", True),
    "ANCHOR_REVIEW_FAMILY": (RESOLVED_FROM_SOURCE, "SKILL.md row 448 (default gpt-5.6-sol)", True),
    "ANCHOR_REVIEW_REASONING_EFFORT": (RESOLVED_FROM_SOURCE, "SKILL.md row 449 (default high)", True),
    # --- install-shape / config write-back family (SKILL.md rows 398-402, 460, 467-470) ---
    "INSTALL_PRESET": (RESOLVED_FROM_SOURCE, "SKILL.md row 398 (config.preset, default standard)", True),
    "PRIMARY_STACK_PACK": (RESOLVED_FROM_SOURCE, "SKILL.md row 399 (config.primary_stack_pack, default web-app)", True),
    "STACK_PACKS_YAML": (RESOLVED_FROM_SOURCE, "SKILL.md row 400 (config.stack_packs, YAML list)", True),
    "INSTALL_LAYERS_YAML": (RESOLVED_FROM_SOURCE, "SKILL.md row 401 (config.install_layers, YAML list)", True),
    "CAPABILITY_PACKS_YAML": (RESOLVED_FROM_SOURCE, "SKILL.md row 402 (config.capability_packs, YAML list)", True),
    "HARNESS_OVERRIDES_YAML": (RESOLVED_FROM_SOURCE, "SKILL.md row 460 (config.overrides map, default {})", True),
    "COPILOT_CLI_ARGS_PS1": (RESOLVED_FROM_SOURCE, "SKILL.md row 467 (config.ai_tools.copilot_cli.args, PowerShell-quoted)", True),
    "COPILOT_CLI_ARGS_SH": (RESOLVED_FROM_SOURCE, "SKILL.md row 468 (config.ai_tools.copilot_cli.args, POSIX-quoted)", True),
    "COPILOT_CLI_ARGS_YAML": (RESOLVED_FROM_SOURCE, "SKILL.md rows 467-468 sibling (same config.ai_tools.copilot_cli.args source, YAML-list-rendered; SKILL.md documents no dedicated YAML row)", True),
    "ENABLED_SIDECARS_PS1": (RESOLVED_FROM_SOURCE, "SKILL.md row 469 (derived from enabled capability packs, PowerShell-quoted)", True),
    "ENABLED_SIDECARS_SH": (RESOLVED_FROM_SOURCE, "SKILL.md row 470 (derived from enabled capability packs, POSIX-quoted)", True),
    "ENABLED_SIDECARS_YAML": (RESOLVED_FROM_SOURCE, "SKILL.md rows 469-470 sibling (same enabled-capability-packs source, YAML-list-rendered; SKILL.md documents no dedicated YAML row)", True),
    # --- graphtor-docs (SKILL.md rows 505-506 / 874-875 / 1088) ---
    "GRAPHTOR_SOURCES_PATH": (RESOLVED_FROM_SOURCE, "SKILL.md rows 505/874 (ordered on-disk candidate chain, default .graphtor/config/sources.yaml)", True),
    "GRAPHTOR_BINARY_PATH": (RESOLVED_FROM_SOURCE, "SKILL.md rows 506/875/1088 (PATH -> local candidate -> literal default graphtor chain, NOT the empty-string branch)", True),
    # --- profile-derived language/lint/format (SKILL.md rows 107-108, 115, 123-124, 127-128) ---
    "LANGUAGE_VERSION": (RESOLVED_FROM_SOURCE, "SKILL.md row 107 (languages.version)", False),
    "LANGUAGE_NOTES": (RESOLVED_FROM_SOURCE, "SKILL.md row 108 (synthesized from language profile)", False),
    "FORMAT_CHECK_COMMAND": (RESOLVED_FROM_SOURCE, "SKILL.md row 115 (format.check_command)", False),
    "FORMATTER": (RESOLVED_FROM_SOURCE, "SKILL.md row 123 (format.tool)", False),
    "LINTER": (RESOLVED_FROM_SOURCE, "SKILL.md row 124 (lint.tool)", False),
    "ERROR_PATTERN": (RESOLVED_FROM_SOURCE, "SKILL.md row 127 (language-specific error handling idiom)", False),
    "DOC_COMMENT_STYLE": (RESOLVED_FROM_SOURCE, "SKILL.md row 128 (language-specific doc-comment convention)", False),
    # --- misc config (no dedicated SKILL.md row; schema-documented defaults) ---
    "STRICT_SAFETY_ENABLED": (RESOLVED_FROM_SOURCE, "schemas/harness-config.schema.json strict_safety.enabled (default false); SKILL.md carries no dedicated row", True),
    "CONTINUOUS_LEARNING_CAPTURE_HOOKS": (RESOLVED_FROM_SOURCE, "SKILL.md row 411 (config.continuous_learning.capture_hooks, default false)", True),
    "CONTINUOUS_LEARNING_ENVIRONMENT_ADAPTER": (RESOLVED_FROM_SOURCE, "SKILL.md row 412 (config.continuous_learning.environment_adapter, default none)", True),
    "CONTINUOUS_LEARNING_PROMOTION_THRESHOLD": (RESOLVED_FROM_SOURCE, "SKILL.md row 413 (config.continuous_learning.promotion_threshold, default 3)", True),
    # --- DEFAULT_BRANCH: same resolved concept as {{CI_DEFAULT_BRANCH}} (SKILL.md row 156); no dedicated {{DEFAULT_BRANCH}} row exists ---
    "DEFAULT_BRANCH": (RESOLVED_FROM_SOURCE, "SKILL.md row 156 ({{CI_DEFAULT_BRANCH}} resolution methodology: git symbolic-ref -> gh CLI -> never guess main; {{DEFAULT_BRANCH}} denotes the identical resolved concept for agent/policy/skill templates)", True),
}


class ClassificationTableTests(unittest.TestCase):
    """142.001-T Step 1 / AC0a."""

    def test_classification_table_covers_all_62_variables(self) -> None:
        self.assertEqual(len(VARIABLE_CLASSIFICATION), 62)

    def test_every_entry_has_a_cited_source_row(self) -> None:
        """AC0a: every variable cites a resolution-table row -- either a
        SKILL.md row (the sole source of truth, C1) or, for the two
        variables SKILL.md does not carry a dedicated row for
        (`STRICT_SAFETY_ENABLED`'s schema default and `DEFAULT_BRANCH`'s
        shared-concept citation to the `{{CI_DEFAULT_BRANCH}}` row), an
        explicitly documented and justified alternative."""
        for variable_name, (_classification, citation, _has_fallback) in VARIABLE_CLASSIFICATION.items():
            with self.subTest(variable=variable_name):
                self.assertTrue(citation.strip())
                self.assertTrue(
                    "SKILL.md" in citation or "schema" in citation.lower(),
                    f"{variable_name}'s citation ({citation!r}) names neither a SKILL.md "
                    "row nor a schema-default source.",
                )

    def test_derive_to_empty_string_rows_document_no_fallback(self) -> None:
        """AC0a guard: DERIVE-TO-EMPTY-STRING is forbidden for any row that
        documents a fallback (tier, PATH-chain, or literal default)."""
        for variable_name, (classification, citation, has_fallback) in VARIABLE_CLASSIFICATION.items():
            with self.subTest(variable=variable_name):
                if classification == DERIVE_TO_EMPTY_STRING:
                    self.assertFalse(
                        has_fallback,
                        f"{variable_name} is classified DERIVE-TO-EMPTY-STRING but its "
                        f"cited row ({citation}) documents a fallback -- forbidden.",
                    )

    def test_raw_escalation_family_is_the_only_derive_to_empty_string_class(self) -> None:
        derive_empty = {
            name for name, (classification, _c, _f) in VARIABLE_CLASSIFICATION.items()
            if classification == DERIVE_TO_EMPTY_STRING
        }
        expected = {
            "LEGACY_ESCALATION_FAMILY", "LEGACY_ESCALATION_PROVIDER", "LEGACY_ESCALATION_REASONING_EFFORT",
            "STAGE_ESCALATION_FAMILY", "STAGE_ESCALATION_PROVIDER", "STAGE_ESCALATION_REASONING_EFFORT",
            "SHIP_ESCALATION_FAMILY", "SHIP_ESCALATION_PROVIDER", "SHIP_ESCALATION_REASONING_EFFORT",
        }
        self.assertEqual(derive_empty, expected)

    def test_role_routes_are_not_derive_to_empty_string(self) -> None:
        """Corrected review-fix cycle 1: STAGE_*/SHIP_* were initially
        misclassified DERIVE-TO-EMPTY-STRING; this guards the correction."""
        for name in ("STAGE_FAMILY", "STAGE_PROVIDER", "STAGE_REASONING_EFFORT",
                     "SHIP_FAMILY", "SHIP_PROVIDER", "SHIP_REASONING_EFFORT"):
            with self.subTest(variable=name):
                self.assertEqual(VARIABLE_CLASSIFICATION[name][0], RESOLVED_FROM_SOURCE)


# ---------------------------------------------------------------------------
# 142.001-T Step 2 -- BLOCKING MEASUREMENT (023-DL R1 / amendment B1): clean
# pair intersection. Recorded EXPLICITLY as empty (verified below by scanning
# the four templates for any of the 62 variable placeholders).
# ---------------------------------------------------------------------------

CLEAN_PAIR_TEMPLATES = (
    "templates/instructions/role-enforcement.instructions.md.tmpl",
    "templates/instructions/circuit-breaker.instructions.md.tmpl",
    "templates/instructions/copilot-code-review.instructions.md.tmpl",
    "templates/prompts/feature-flow-dark.prompt.md.tmpl",
)

# Recorded result of the amendment-B1 blocking measurement: EMPTY. No further
# STOP-rule handling is required (B1 only fires on a non-empty intersection).
CLEAN_PAIR_INTERSECTION: frozenset[str] = frozenset()


class CleanPairIntersectionTests(unittest.TestCase):
    """142.001-T Step 2 / AC0b."""

    def test_clean_pair_intersection_is_recorded_explicitly(self) -> None:
        # AC0b requires an explicit record even when empty -- this constant
        # IS that record; assert it is the frozenset type, not merely absent.
        self.assertIsInstance(CLEAN_PAIR_INTERSECTION, frozenset)
        self.assertEqual(CLEAN_PAIR_INTERSECTION, frozenset())

    def test_no_derived_variable_appears_in_any_clean_pair_template(self) -> None:
        variable_names = set(VARIABLE_CLASSIFICATION)
        for relative_path in CLEAN_PAIR_TEMPLATES:
            template_path = _REPO_ROOT / relative_path
            with self.subTest(template=relative_path):
                self.assertTrue(template_path.exists())
                text = template_path.read_text(encoding="utf-8")
                found = {name for name in variable_names if f"{{{{{name}}}}}" in text}
                self.assertEqual(
                    found,
                    set(),
                    f"{relative_path} unexpectedly references derived variable(s) {found} "
                    "-- the recorded CLEAN_PAIR_INTERSECTION must be updated (amendment B1).",
                )


# ---------------------------------------------------------------------------
# 142.001-T (T0a/T0b) + 142.005-T AC3a/AC3b -- the monotone unresolved-set
# ratchet. T0a asserts the set of unresolved placeholders across the staged
# tree EQUALS this checked-in expected set exactly (a NEW unresolved variable
# fails immediately). T0b is the same set expressed as a ratchet: by the end
# of 150-S's derivation work the set was EMPTY (amendment B5).
#
# Reopened by 156-S/148-F (148.007-T, U7). Registering the 13 review-persona
# artifacts in `.autoharness/harness-manifest.yaml` makes `verify_workspace`'s
# staging pass render `templates/agents/review/technology-reviewer.agent.md.tmpl`
# and `concurrency-reviewer.agent.md.tmpl` for the first time (they were not
# manifest-registered, and therefore not staged, before U7). Once staged,
# `PRIMARY_LANGUAGE`/`PRIMARY_LANGUAGE_LOWER`/`TIER_1_*`/`TIER_2_*`/
# `CONCURRENCY_PATTERNS` all resolve cleanly, but the 4 names below do not:
# per plan decisions D8/D8-B and risk RK-J
# (docs/plans/2026-08-27-policy-registry-and-review-persona-layer-plan.md),
# these are Stage-reviewed prose pinned verbatim at Ship render time (already
# bound correctly into `.github/agents/subagents/python-reviewer.agent.md` by
# 148.005-T), not resolver-derived -- `_language_defaults()` in
# `src/autoharness/verify_workspace.py` has no synthesis logic for them, and
# RK-J explicitly scopes adding that resolver support as "out of S0 scope
# (would change the resolver, blast radius beyond the persona layer)". This is
# the same accepted status-change pattern already recorded in the same plan as
# RK-B (a previously-masked check becoming evaluated is a status-change, not a
# regression, and is reported as a finding rather than silently patched). This
# ratchet's own checked-in baseline is the correct place to record that
# finding -- not the resolver, and not the (unmodified, per D8-C) `.tmpl`
# files.
EXPECTED_UNRESOLVED_VARIABLES: frozenset[str] = frozenset(
    {
        "LANGUAGE_SAFETY_CHECKS",
        "LANGUAGE_IDIOM_CHECKS",
        "LANGUAGE_ERROR_HANDLING_CHECKS",
        "LANGUAGE_PERFORMANCE_CHECKS",
    }
)


def _scan_unresolved_variable_names() -> set[str]:
    """Render the full staged tree exactly as `autoharness verify-workspace`
    does and return the set of DISTINCT unresolved `{{VARIABLE}}` names
    (stripped of braces)."""
    with tempfile.TemporaryDirectory() as staging_dir:
        report = verify_workspace(_REPO_ROOT, _REPO_ROOT, staging_dir=Path(staging_dir))
        return {
            entry["placeholder"].strip("{}")
            for entry in report["unresolved"]
        }


class RatchetContractTests(unittest.TestCase):
    """142.001-T T0a/T0b, 142.002-T AC-a, 142.003-T AC-a, 142.004-T AC2a,
    142.005-T AC3a/AC3b (headline "zero unresolved" criterion)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.unresolved_names = _scan_unresolved_variable_names()

    def test_t0a_ratchet_set_equals_expected_exactly(self) -> None:
        self.assertEqual(self.unresolved_names, set(EXPECTED_UNRESOLVED_VARIABLES))

    def test_t0b_ratchet_is_the_zero_assertion(self) -> None:
        """Amendment B5 (150-S) emptied the expected set. 156-S/RK-J reopens
        it with exactly the 4 D8-B pinned, Ship-time-bound persona variables
        (see the module-level comment above `EXPECTED_UNRESOLVED_VARIABLES`);
        extending `_language_defaults` to derive them is explicitly out of S0
        scope. T0b now asserts the expected set matches this documented,
        closed residual exactly -- it is still a ratchet, just no longer the
        degenerate zero case."""
        self.assertEqual(
            EXPECTED_UNRESOLVED_VARIABLES,
            frozenset(
                {
                    "LANGUAGE_SAFETY_CHECKS",
                    "LANGUAGE_IDIOM_CHECKS",
                    "LANGUAGE_ERROR_HANDLING_CHECKS",
                    "LANGUAGE_PERFORMANCE_CHECKS",
                }
            ),
        )
        self.assertEqual(self.unresolved_names, set(EXPECTED_UNRESOLVED_VARIABLES))

    def test_a_new_unresolved_variable_would_fail_immediately(self) -> None:
        """The ratchet is an EXACT set, not a count bound: any variable name
        not in the (now non-empty, but still closed) expected set fails the
        equality assertion above -- this test documents that guarantee by
        construction rather than re-asserting it, by confirming a clearly
        fabricated name is excluded from the allow-list."""
        self.assertNotIn(
            "NOT_A_REAL_TEMPLATE_VARIABLE_XYZ", EXPECTED_UNRESOLVED_VARIABLES
        )


# ---------------------------------------------------------------------------
# 142.002-T -- tier / orchestrator polymorphic shape (amendment B6, corrected
# review-fix cycle 1).
# ---------------------------------------------------------------------------


class TierRouteShapeTests(unittest.TestCase):
    def test_scalar_shorthand_tier_route(self) -> None:
        variables = _derive_tier_route_variables({"tier3": "claude-opus-5"})
        self.assertEqual(variables["TIER_3_FAMILY"], "claude-opus-5")
        self.assertEqual(variables["TIER_3_PROVIDER"], "")
        self.assertEqual(variables["TIER_3_REASONING_EFFORT"], "")

    def test_mapping_form_tier_route_resolves_each_subfield_independently(self) -> None:
        variables = _derive_tier_route_variables(
            {
                "tier1": {
                    "model": "gpt-5.4-mini",
                    "model_family": "gpt-5.4-mini",
                    "model_provider": "openai",
                    "reasoning_effort": "low",
                }
            }
        )
        self.assertEqual(variables["TIER_1_FAMILY"], "gpt-5.4-mini")
        self.assertEqual(variables["TIER_1_PROVIDER"], "openai")
        self.assertEqual(variables["TIER_1_REASONING_EFFORT"], "low")

    def test_scalar_shorthand_orchestrator_route_does_not_derive_to_empty(self) -> None:
        """Amendment B6 orchestrator clause: provider/effort fall back to
        tier2 -- NOT to the empty string, which would encode the defect this
        amendment corrects."""
        model_routing = {
            "orchestrator": "gpt-5.6-sol",
            "tier2": {"model_provider": "openai", "reasoning_effort": "high"},
        }
        variables = _derive_orchestrator_route_variables(model_routing)
        self.assertEqual(variables["ORCHESTRATOR_FAMILY"], "gpt-5.6-sol")
        self.assertEqual(variables["ORCHESTRATOR_PROVIDER"], "openai")
        self.assertNotEqual(variables["ORCHESTRATOR_PROVIDER"], "")
        self.assertEqual(variables["ORCHESTRATOR_REASONING_EFFORT"], "high")
        self.assertNotEqual(variables["ORCHESTRATOR_REASONING_EFFORT"], "")

    def test_absent_orchestrator_uses_its_own_default_not_tier2_family(self) -> None:
        model_routing = {"tier2": {"model_family": "claude-sonnet-5"}}
        variables = _derive_orchestrator_route_variables(model_routing)
        self.assertEqual(variables["ORCHESTRATOR_FAMILY"], "gpt-5.4")
        self.assertNotEqual(variables["ORCHESTRATOR_FAMILY"], "claude-sonnet-5")

    def test_orchestrator_mapping_form_resolves_independently(self) -> None:
        model_routing = {
            "orchestrator": {"model_family": "gpt-5.6-terra", "model_provider": "openai", "reasoning_effort": "high"}
        }
        variables = _derive_orchestrator_route_variables(model_routing)
        self.assertEqual(variables["ORCHESTRATOR_FAMILY"], "gpt-5.6-terra")
        self.assertEqual(variables["ORCHESTRATOR_PROVIDER"], "openai")
        self.assertEqual(variables["ORCHESTRATOR_REASONING_EFFORT"], "high")

    def test_render_template_is_unchanged_by_this_task(self) -> None:
        """AC-c / constraint C5: `_render_template` remains pure {{VAR}}
        substitution; no tier/orchestrator-specific behavior lives in it."""
        rendered = _render_template("{{TIER_3_FAMILY}}", {"TIER_3_FAMILY": "claude-opus-5"})
        self.assertEqual(rendered, "claude-opus-5")


# ---------------------------------------------------------------------------
# 142.003-T -- role routes + escalation prose/raw split (amendments B2, B6
# corrected review-fix cycle 1, constraint C3).
# ---------------------------------------------------------------------------


class RoleRouteAndEscalationTests(unittest.TestCase):
    def test_stage_absent_falls_back_entirely_to_tier3(self) -> None:
        model_routing = {"tier3": {"model_family": "claude-opus-5", "model_provider": "anthropic", "reasoning_effort": "high"}}
        variables = _derive_role_route_variables(model_routing)
        self.assertEqual(variables["STAGE_FAMILY"], "claude-opus-5")
        self.assertEqual(variables["STAGE_PROVIDER"], "anthropic")
        self.assertEqual(variables["STAGE_REASONING_EFFORT"], "high")

    def test_ship_absent_falls_back_entirely_to_tier2(self) -> None:
        model_routing = {"tier2": {"model_family": "claude-sonnet-5", "model_provider": "anthropic", "reasoning_effort": "high"}}
        variables = _derive_role_route_variables(model_routing)
        self.assertEqual(variables["SHIP_FAMILY"], "claude-sonnet-5")
        self.assertEqual(variables["SHIP_PROVIDER"], "anthropic")
        self.assertEqual(variables["SHIP_REASONING_EFFORT"], "high")

    def test_per_subfield_fallback_not_all_or_nothing(self) -> None:
        """A declared model_family with an empty provider falls back to tier3
        for the provider ONLY -- per-sub-field, not all-or-nothing."""
        model_routing = {
            "stage": {"model_family": "claude-opus-5"},
            "tier3": {"model_family": "claude-opus-5", "model_provider": "anthropic", "reasoning_effort": "high"},
        }
        variables = _derive_role_route_variables(model_routing)
        self.assertEqual(variables["STAGE_FAMILY"], "claude-opus-5")
        self.assertEqual(variables["STAGE_PROVIDER"], "anthropic")
        self.assertEqual(variables["STAGE_REASONING_EFFORT"], "high")

    def test_role_route_values_are_never_blank_when_tier_is_declared(self) -> None:
        model_routing = {"tier3": "claude-opus-5", "tier2": "claude-sonnet-5"}
        variables = _derive_role_route_variables(model_routing)
        self.assertNotEqual(variables["STAGE_FAMILY"], "")
        self.assertNotEqual(variables["SHIP_FAMILY"], "")

    def test_role_route_falls_back_to_tiers_own_literal_default_when_tier_entirely_absent(self) -> None:
        """Review finding (this feature's own PR): STAGE_FAMILY/SHIP_FAMILY
        previously resolved to "" instead of the SKILL.md-documented tier
        own-default (claude-opus-5/claude-sonnet-5) when model_routing.tier3/
        tier2 was absent entirely -- inconsistent with TIER_3_FAMILY/
        TIER_2_FAMILY themselves, which always resolve to their own default."""
        variables = _derive_role_route_variables({})
        self.assertEqual(variables["STAGE_FAMILY"], "claude-opus-5")
        self.assertEqual(variables["SHIP_FAMILY"], "claude-sonnet-5")

    def test_escalation_prose_falls_back_to_tier3_own_default_when_tier3_absent(self) -> None:
        variables = _derive_escalation_prose_variables({})
        self.assertEqual(variables["ESCALATION_FAMILY"], "claude-opus-5")

    def test_effective_escalation_route_for_role_falls_back_to_tier3_own_default(self) -> None:
        family, _provider, _effort = _effective_escalation_route_for_role({}, "stage")
        self.assertEqual(family, "claude-opus-5")

    def test_raw_escalation_negative_test_flat_empty_nested_present(self) -> None:
        """Amendment B2 (must be NEGATIVE as well as positive): given a
        nested stage.escalation override and an UNSET flat escalation, the
        rendered flat block's three sub-fields are empty AND specifically
        NOT EQUAL to the nested override's values."""
        model_routing = {
            "stage": {
                "escalation": {
                    "model_family": "gpt-5.6-sol",
                    "model_provider": "openai",
                    "reasoning_effort": "high",
                }
            }
        }
        variables = _derive_raw_escalation_variables(model_routing)
        self.assertEqual(variables["LEGACY_ESCALATION_FAMILY"], "")
        self.assertEqual(variables["LEGACY_ESCALATION_PROVIDER"], "")
        self.assertEqual(variables["LEGACY_ESCALATION_REASONING_EFFORT"], "")
        self.assertNotEqual(variables["LEGACY_ESCALATION_FAMILY"], variables["STAGE_ESCALATION_FAMILY"])
        self.assertEqual(variables["STAGE_ESCALATION_FAMILY"], "gpt-5.6-sol")

    def test_raw_families_never_receive_the_collapsed_resolved_value(self) -> None:
        """Constraint C3: populating a raw slot from the collapsed value
        would reproduce the H2 flat+nested ambiguity (PR #316 round 3)."""
        model_routing = {"escalation": {}, "stage": {}, "ship": {}, "tier3": {"model_family": "claude-opus-5"}}
        raw = _derive_raw_escalation_variables(model_routing)
        for key in (
            "LEGACY_ESCALATION_FAMILY", "LEGACY_ESCALATION_PROVIDER", "LEGACY_ESCALATION_REASONING_EFFORT",
            "STAGE_ESCALATION_FAMILY", "STAGE_ESCALATION_PROVIDER", "STAGE_ESCALATION_REASONING_EFFORT",
            "SHIP_ESCALATION_FAMILY", "SHIP_ESCALATION_PROVIDER", "SHIP_ESCALATION_REASONING_EFFORT",
        ):
            with self.subTest(variable=key):
                self.assertEqual(raw[key], "")

    def test_nested_stage_escalation_and_empty_flat_renders_flat_block_inert(self) -> None:
        model_routing = {"stage": {"escalation": {"model_family": "gpt-5.6-sol"}}, "escalation": {}}
        raw = _derive_raw_escalation_variables(model_routing)
        flat_block = {
            "model_family": raw["LEGACY_ESCALATION_FAMILY"],
            "model_provider": raw["LEGACY_ESCALATION_PROVIDER"],
            "reasoning_effort": raw["LEGACY_ESCALATION_REASONING_EFFORT"],
        }
        self.assertFalse(_escalation_route_has_any_field(flat_block))
        self.assertEqual(raw["LEGACY_ESCALATION_FAMILY"], "")
        self.assertEqual(raw["LEGACY_ESCALATION_PROVIDER"], "")
        self.assertEqual(raw["LEGACY_ESCALATION_REASONING_EFFORT"], "")

    def test_orchestrator_agent_frontmatter_has_no_unresolved_role_route_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as staging_dir:
            verify_workspace(_REPO_ROOT, _REPO_ROOT, staging_dir=Path(staging_dir))
            text = (Path(staging_dir) / ".github/agents/_orchestrator.agent.md").read_text(encoding="utf-8")
        for placeholder in ("{{STAGE_FAMILY}}", "{{STAGE_PROVIDER}}", "{{STAGE_REASONING_EFFORT}}",
                             "{{SHIP_FAMILY}}", "{{SHIP_PROVIDER}}", "{{SHIP_REASONING_EFFORT}}"):
            with self.subTest(placeholder=placeholder):
                self.assertNotIn(placeholder, text)


# ---------------------------------------------------------------------------
# 142.004-T -- install-shape structural rendering hazard (023-DL R4,
# hardening H4; amendments B3 idempotent round-trip, B7 semantic equivalence
# + no live-config write).
# ---------------------------------------------------------------------------


class InstallShapeTests(unittest.TestCase):
    def test_staged_config_yaml_parses_as_yaml(self) -> None:
        manifest, config, profile, registry = _load_live_fixtures()
        variables = _derive_template_variables(_REPO_ROOT, manifest, config, profile, registry)
        template_path = _REPO_ROOT / "templates/harness-config.yaml.tmpl"
        rendered = _render_template(template_path.read_text(encoding="utf-8"), variables)
        parsed = yaml.safe_load(rendered)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["preset"], config["preset"])
        self.assertEqual(parsed["stack_packs"], config["stack_packs"])

    def test_start_scripts_render_syntactically_valid_array_literals(self) -> None:
        manifest, config, profile, registry = _load_live_fixtures()
        variables = _derive_template_variables(_REPO_ROOT, manifest, config, profile, registry)
        ps1_text = _render_template(
            (_REPO_ROOT / "templates/scripts/start.ps1.tmpl").read_text(encoding="utf-8"), variables
        )
        sh_text = _render_template(
            (_REPO_ROOT / "templates/scripts/start.sh.tmpl").read_text(encoding="utf-8"), variables
        )
        self.assertIn("$enabledSidecars = @(", ps1_text)
        self.assertNotIn("{{", ps1_text.split("$enabledSidecars")[1].split("\n")[0])
        self.assertIn("enabled_sidecars=(", sh_text)
        self.assertNotIn("{{", sh_text.split("enabled_sidecars=")[1].split("\n")[0])

    def test_copilot_cli_args_are_single_quoted_not_json_double_quoted(self) -> None:
        """Copilot review finding (PR #395): json.dumps-based double-quoting
        is NOT shell quoting -- a configured ai_tools.copilot_cli.args value
        containing `$(...)` would still be evaluated as a command
        substitution inside a JSON/double-quoted string when the generated
        start.sh/start.ps1 runs, turning config DATA into executable script
        content. Both POSIX and PowerShell renders must use single-quoted
        literals (which suppress ALL expansion), never double quotes."""
        from autoharness.verify_workspace import _posix_quoted_list, _powershell_quoted_list

        dangerous_args = ["$(rm -rf /)", "`whoami`", "$HOME"]
        posix_rendered = _posix_quoted_list(dangerous_args)
        ps1_rendered = _powershell_quoted_list(dangerous_args)
        self.assertNotIn('"', posix_rendered)
        self.assertNotIn('"', ps1_rendered)
        self.assertIn("'$(rm -rf /)'", posix_rendered)
        self.assertIn("'$(rm -rf /)'", ps1_rendered)

    def test_posix_quote_escapes_embedded_single_quote(self) -> None:
        from autoharness.verify_workspace import _posix_quoted_list

        rendered = _posix_quoted_list(["it's"])
        self.assertEqual(rendered, "'it'\\''s'")

    def test_powershell_quote_escapes_embedded_single_quote(self) -> None:
        from autoharness.verify_workspace import _powershell_quoted_list

        rendered = _powershell_quoted_list(["it's"])
        self.assertEqual(rendered, "'it''s'")

    def test_idempotent_round_trip_amendment_b3(self) -> None:
        """derive -> render -> parse -> RE-DERIVE from the re-parsed config
        -> the second derivation equals the first."""
        manifest, config, profile, registry = _load_live_fixtures()
        first = _derive_template_variables(_REPO_ROOT, manifest, config, profile, registry)
        template_path = _REPO_ROOT / "templates/harness-config.yaml.tmpl"
        rendered = _render_template(template_path.read_text(encoding="utf-8"), first)
        reparsed_config = yaml.safe_load(rendered)
        second = _derive_template_variables(_REPO_ROOT, manifest, reparsed_config, profile, registry)
        # Compare only the model-routing derived keys (the shape-normalising
        # surface B3 targets) rather than the full map, since re-parsing can
        # legitimately introduce keys (e.g. AUTOHARNESS_VERSION) unrelated to
        # this round-trip contract.
        model_routing_keys = [
            key for key in first
            if key.startswith(("TIER_", "MODEL_ROUTING_TIER", "ORCHESTRATOR_", "STAGE_", "SHIP_", "ESCALATION_", "ANCHOR_REVIEW_"))
        ]
        for key in model_routing_keys:
            with self.subTest(key=key):
                self.assertEqual(first[key], second[key])

    def test_semantic_route_equivalence_amendment_b7(self) -> None:
        """Rendering normalises scalar-shorthand routes into mappings; a raw
        derivation-map comparison alone is invariant under normalisation and
        would mask the reshape. Assert SEMANTIC route equivalence instead."""
        manifest, config, profile, registry = _load_live_fixtures()
        pre_variables = _derive_template_variables(_REPO_ROOT, manifest, config, profile, registry)
        template_path = _REPO_ROOT / "templates/harness-config.yaml.tmpl"
        rendered = _render_template(template_path.read_text(encoding="utf-8"), pre_variables)
        reparsed_config = yaml.safe_load(rendered)
        post_variables = _derive_template_variables(_REPO_ROOT, manifest, reparsed_config, profile, registry)
        for tier in ("TIER_1", "TIER_2", "TIER_3"):
            for field in ("FAMILY", "PROVIDER", "REASONING_EFFORT"):
                key = f"{tier}_{field}"
                with self.subTest(key=key):
                    self.assertEqual(pre_variables[key], post_variables[key])

    def test_this_feature_does_not_write_the_live_config(self) -> None:
        """Hard constraint (amendment B7): shape normalisation in the staged
        tree is acceptable; writing the staged config back over the live
        workspace config is NOT."""
        live_config_path = _REPO_ROOT / ".autoharness/config.yaml"
        before = live_config_path.read_bytes()
        with tempfile.TemporaryDirectory() as staging_dir:
            verify_workspace(_REPO_ROOT, _REPO_ROOT, staging_dir=Path(staging_dir))
        after = live_config_path.read_bytes()
        self.assertEqual(before, after)


# ---------------------------------------------------------------------------
# 142.005-T -- profile-derived / misc-config family (amendment B4 provenance
# rule, AC3c GRAPHTOR_BINARY_PATH three-rung fallback chain).
# ---------------------------------------------------------------------------


class ProfileDerivedMiscConfigTests(unittest.TestCase):
    def test_graphtor_binary_path_declared_wins_over_the_whole_chain(self) -> None:
        profile = {"graphtor_docs": {"binary_path": ".custom/graphtor"}}
        self.assertEqual(_resolve_graphtor_binary_path(profile, _REPO_ROOT), ".custom/graphtor")

    def test_graphtor_binary_path_null_falls_through_to_path_or_default(self) -> None:
        """null/absent does NOT mean empty -- the chain always yields a
        non-empty value, never "" and never the literal string "None"."""
        profile = {"graphtor_docs": {"binary_path": None}}
        with tempfile.TemporaryDirectory() as workspace_dir:
            resolved = _resolve_graphtor_binary_path(profile, Path(workspace_dir))
        self.assertNotEqual(resolved, "")
        self.assertNotEqual(resolved, "None")

    def test_graphtor_binary_path_local_candidate_rung(self) -> None:
        import shutil as _shutil
        import unittest.mock as _mock

        profile: dict[str, Any] = {"graphtor_docs": {"binary_path": None}}
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace_path = Path(workspace_dir)
            candidate = workspace_path / ".graphtor" / "bin" / "graphtor-docs"
            candidate.parent.mkdir(parents=True)
            candidate.write_text("#!/bin/sh\n", encoding="utf-8")
            with _mock.patch.object(_shutil, "which", return_value=None):
                resolved = _resolve_graphtor_binary_path(profile, workspace_path)
        self.assertEqual(resolved, ".graphtor/bin/graphtor-docs")

    def test_graphtor_binary_path_final_default_when_both_absent(self) -> None:
        import shutil as _shutil
        import unittest.mock as _mock

        profile: dict[str, Any] = {"graphtor_docs": {"binary_path": None}}
        with tempfile.TemporaryDirectory() as workspace_dir:
            with _mock.patch.object(_shutil, "which", return_value=None):
                resolved = _resolve_graphtor_binary_path(profile, Path(workspace_dir))
        self.assertEqual(resolved, "graphtor")

    def test_graphtor_sources_path_declared_wins(self) -> None:
        profile = {"graphtor_docs": {"sources_path": ".graphtor/custom-sources.yaml"}}
        self.assertEqual(
            _resolve_graphtor_sources_path(profile, _REPO_ROOT), ".graphtor/custom-sources.yaml"
        )

    def test_graphtor_sources_path_default_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            resolved = _resolve_graphtor_sources_path({}, Path(workspace_dir))
        self.assertEqual(resolved, ".graphtor/config/sources.yaml")

    def test_default_branch_resolves_to_a_non_empty_value_in_this_repo(self) -> None:
        # This repo is a real git checkout with an origin/HEAD symbolic ref
        # (confirmed main), so resolution must succeed without guessing.
        resolved = _resolve_default_branch(_REPO_ROOT)
        self.assertNotEqual(resolved, "")

    def test_default_branch_resolution_is_immune_to_ambient_git_config_pollution(self) -> None:
        """Hardening: an inherited GIT_CONFIG_COUNT with a missing/malformed
        corresponding GIT_CONFIG_KEY_N/GIT_CONFIG_VALUE_N (from an unrelated
        process-level source, e.g. test-order pollution documented in
        docs/compound/2026-08-20-*-git-subprocess-*.md and P-021 deferred
        entry 9DD9E323) must not make this workspace's own, otherwise
        healthy, git resolution fail."""
        import os as _os
        import unittest.mock as _mock

        polluted_environ = dict(_os.environ)
        polluted_environ["GIT_CONFIG_COUNT"] = "3"
        polluted_environ["GIT_CONFIG_KEY_0"] = "user.name"
        polluted_environ["GIT_CONFIG_VALUE_0"] = "Test"
        # Deliberately omit GIT_CONFIG_KEY_1/VALUE_1 and KEY_2/VALUE_2 --
        # this reproduces "missing config value GIT_CONFIG_VALUE_2" for any
        # subprocess that inherits this environment unsanitized.
        with _mock.patch.object(_os, "environ", polluted_environ):
            resolved = _resolve_default_branch(_REPO_ROOT)
        self.assertNotEqual(resolved, "")
        self.assertEqual(resolved, "main")

    def test_default_branch_left_unresolved_rather_than_empty_string_when_resolution_fails(self) -> None:
        """Copilot review finding (PR #395): silently storing "" for
        DEFAULT_BRANCH would remove the placeholder from every consuming
        template (e.g. rendering the literal broken command "git checkout "
        with a trailing space) while the zero-unresolved sweep reports
        success over detectably-broken output. SKILL.md row 156's "never
        guess main... halt installation" contract requires this variable be
        left as a DETECTABLE unresolved placeholder when it cannot
        legitimately resolve, not silently defaulted to empty."""
        import unittest.mock as _mock

        with _mock.patch(
            "autoharness.verify_workspace._resolve_default_branch", return_value=""
        ):
            manifest, config, profile, registry = _load_live_fixtures()
            variables = _derive_template_variables(_REPO_ROOT, manifest, config, profile, registry)
        self.assertNotIn("DEFAULT_BRANCH", variables)

    def test_provenance_categories_never_include_observed_in_dogfood(self) -> None:
        """Amendment B4: forbidden provenance category (iv) 'observed in the
        current dogfood copy' must never appear as a classification source."""
        for _name, (_classification, citation, _has_fallback) in VARIABLE_CLASSIFICATION.items():
            with self.subTest(citation=citation):
                self.assertNotIn("observed in the current dogfood", citation.lower())
                self.assertNotIn("dogfood copy", citation.lower())

    def test_continuous_learning_promotion_threshold_null_uses_the_documented_default(self) -> None:
        """Review finding: an explicit YAML `null` (a PRESENT key) must not
        render the Python literal string "None" -- `dict.get(key, default)`
        only applies `default` when the key is ABSENT, not when it is
        present with a `None` value."""
        manifest, config, profile, registry = _load_live_fixtures()
        config = dict(config)
        config["continuous_learning"] = {"promotion_threshold": None}
        variables = _derive_template_variables(_REPO_ROOT, manifest, config, profile, registry)
        self.assertEqual(variables["CONTINUOUS_LEARNING_PROMOTION_THRESHOLD"], "3")

    def test_harness_overrides_yaml_null_value_renders_yaml_null_not_python_none(self) -> None:
        from autoharness.verify_workspace import _yaml_flow_map

        rendered = _yaml_flow_map({"SOME_KEY": None})
        self.assertNotIn("None", rendered)
        self.assertIn("null", rendered)


# ---------------------------------------------------------------------------
# 142.006-T -- template/dogfood parity reconciliation: the clean-pair
# byte-identity contract must remain fully green after all derivation work.
# ---------------------------------------------------------------------------


class ParityReconciliationTests(unittest.TestCase):
    def test_clean_pairs_still_byte_identical_after_derivation(self) -> None:
        """Re-affirms AC4a/AC4d: no clean pair diverged (B1 STOP rule never
        triggered), so no manifest checksum needed refreshing."""
        variables = _live_variables()
        for relative_path in CLEAN_PAIR_TEMPLATES:
            template_path = _REPO_ROOT / relative_path
            with self.subTest(template=relative_path):
                rendered = _render_template(template_path.read_text(encoding="utf-8"), variables)
                for name in VARIABLE_CLASSIFICATION:
                    self.assertNotIn(f"{{{{{name}}}}}", rendered)


# ---------------------------------------------------------------------------
# 142.007-T -- artifact/role-aware composition at the render call site
# (amendment B8). `_render_template` MUST stay pure; only the composed
# mapping passed to it varies by resolved role.
# ---------------------------------------------------------------------------


class ArtifactRoleCompositionTests(unittest.TestCase):
    def test_resolve_artifact_role_from_identity_only(self) -> None:
        self.assertEqual(_resolve_artifact_role(".github/agents/_stage.agent.md"), "stage")
        self.assertEqual(_resolve_artifact_role(".github/agents/_ship.agent.md"), "ship")
        self.assertIsNone(_resolve_artifact_role(".github/instructions/escalation-protocol.instructions.md"))
        self.assertIsNone(_resolve_artifact_role(".github/agents/_orchestrator.agent.md"))

    def test_ac7a_distinct_stage_vs_ship_override_renders_not_equal(self) -> None:
        model_routing = {
            "tier3": {"model_family": "claude-opus-5"},
            "tier2": {"model_family": "claude-sonnet-5"},
            "stage": {"escalation": {"model_family": "gpt-5.6-sol", "model_provider": "openai", "reasoning_effort": "high"}},
            "ship": {"escalation": {"model_family": "gpt-5.5", "model_provider": "openai", "reasoning_effort": "medium"}},
        }
        base = {"ESCALATION_FAMILY": "base", "ESCALATION_PROVIDER": "base", "ESCALATION_REASONING_EFFORT": "base"}
        stage_vars = _compose_artifact_variables(base, model_routing, "stage")
        ship_vars = _compose_artifact_variables(base, model_routing, "ship")
        stage_triple = (stage_vars["ESCALATION_FAMILY"], stage_vars["ESCALATION_PROVIDER"], stage_vars["ESCALATION_REASONING_EFFORT"])
        ship_triple = (ship_vars["ESCALATION_FAMILY"], ship_vars["ESCALATION_PROVIDER"], ship_vars["ESCALATION_REASONING_EFFORT"])
        self.assertNotEqual(stage_triple, ship_triple)
        self.assertEqual(stage_triple, ("gpt-5.6-sol", "openai", "high"))
        self.assertEqual(ship_triple, ("gpt-5.5", "openai", "medium"))

    def test_ac7b_flat_only_both_roles_render_the_same_value(self) -> None:
        """With only the flat escalation declared (today's live shape), both
        agents render the same value -- a strict generalisation, a no-op for
        today's config."""
        model_routing = {
            "tier3": {"model_family": "claude-opus-5"},
            "escalation": {"model_family": "gpt-5.6-sol", "model_provider": "openai", "reasoning_effort": "high"},
        }
        base = {"ESCALATION_FAMILY": "x", "ESCALATION_PROVIDER": "x", "ESCALATION_REASONING_EFFORT": "x"}
        stage_vars = _compose_artifact_variables(base, model_routing, "stage")
        ship_vars = _compose_artifact_variables(base, model_routing, "ship")
        self.assertEqual(
            (stage_vars["ESCALATION_FAMILY"], stage_vars["ESCALATION_PROVIDER"], stage_vars["ESCALATION_REASONING_EFFORT"]),
            (ship_vars["ESCALATION_FAMILY"], ship_vars["ESCALATION_PROVIDER"], ship_vars["ESCALATION_REASONING_EFFORT"]),
        )
        self.assertEqual(stage_vars["ESCALATION_FAMILY"], "gpt-5.6-sol")

    def test_ac7c_neither_declared_each_role_falls_back_to_tier3(self) -> None:
        model_routing = {"tier3": {"model_family": "claude-opus-5", "model_provider": "anthropic", "reasoning_effort": "high"}}
        base = {"ESCALATION_FAMILY": "x", "ESCALATION_PROVIDER": "x", "ESCALATION_REASONING_EFFORT": "x"}
        stage_vars = _compose_artifact_variables(base, model_routing, "stage")
        ship_vars = _compose_artifact_variables(base, model_routing, "ship")
        self.assertEqual(stage_vars["ESCALATION_FAMILY"], "claude-opus-5")
        self.assertEqual(ship_vars["ESCALATION_FAMILY"], "claude-opus-5")

    def test_ac7d_render_template_byte_identical_no_behavioral_change(self) -> None:
        # `_render_template` is called with a composed mapping but its own
        # implementation is untouched pure {{VAR}} substitution.
        self.assertEqual(_render_template("{{X}}-{{Y}}", {"X": "1", "Y": "2"}), "1-2")
        self.assertEqual(_render_template("no placeholders", {"X": "1"}), "no placeholders")

    def test_ac7e_raw_families_unaffected_by_role_composition(self) -> None:
        model_routing = {
            "escalation": {"model_family": "legacy-family"},
            "stage": {"escalation": {"model_family": "stage-only"}},
        }
        base = {
            "ESCALATION_FAMILY": "base",
            "LEGACY_ESCALATION_FAMILY": "legacy-family",
            "STAGE_ESCALATION_FAMILY": "stage-only",
        }
        stage_vars = _compose_artifact_variables(base, model_routing, "stage")
        self.assertEqual(stage_vars["LEGACY_ESCALATION_FAMILY"], "legacy-family")
        self.assertEqual(stage_vars["STAGE_ESCALATION_FAMILY"], "stage-only")

    def test_ac7f_roleless_artifact_gets_base_map_unchanged(self) -> None:
        model_routing = {"stage": {"escalation": {"model_family": "gpt-5.6-sol"}}}
        base = {"ESCALATION_FAMILY": "base-value"}
        result = _compose_artifact_variables(base, model_routing, None)
        self.assertIs(result, base)
        self.assertEqual(result["ESCALATION_FAMILY"], "base-value")

    def test_compose_does_not_mutate_base_variables(self) -> None:
        model_routing = {"stage": {"escalation": {"model_family": "gpt-5.6-sol"}}}
        base = {"ESCALATION_FAMILY": "base-value"}
        _compose_artifact_variables(base, model_routing, "stage")
        self.assertEqual(base["ESCALATION_FAMILY"], "base-value")

    def test_ac7g_clean_pairs_remain_green_with_composition_in_place(self) -> None:
        variables = _live_variables()
        model_routing = {}
        for relative_path in CLEAN_PAIR_TEMPLATES:
            template_path = _REPO_ROOT / relative_path
            composed = _compose_artifact_variables(variables, model_routing, None)
            rendered = _render_template(template_path.read_text(encoding="utf-8"), composed)
            with self.subTest(template=relative_path):
                self.assertNotIn("{{ESCALATION_FAMILY}}", rendered)


if __name__ == "__main__":
    unittest.main()
