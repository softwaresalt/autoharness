"""Resolution tests for the optional ``context_tier`` route field (194-F, C2a).

Covers the resolver and the derivation half of plan unit C2
(docs/plans/2026-09-27-context-tier-model-routing-plan.md):

  * ``_resolve_context_tier``: route -> fallback tier -> ``"default"``, and a
    legacy string tier gives ``"default"``;
  * resolved variables (never empty): ``TIER_1/2/3_CONTEXT_TIER``,
    ``ORCHESTRATOR_CONTEXT_TIER`` (route -> tier2 -> default, including the
    scalar orchestrator form), ``STAGE_CONTEXT_TIER``, ``SHIP_CONTEXT_TIER``;
  * raw pass-through (constraint C3, H-C1): ``LEGACY/STAGE/SHIP_ESCALATION_CONTEXT_TIER``
    are ``""`` when unset and never take a resolved value;
  * schema parity (H-C5): the schema ``contextTier`` enum equals
    ``["", *CONTEXT_TIER_VALUES]``.

The escalation-resolution half (collapsed ``ESCALATION_CONTEXT_TIER``, the
role-scoped overlay, per_role ``resolved_context_tier``, frontmatter
validation) is C2b (194.014-T), which extends this module.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from autoharness.frontmatter_contract import CONTEXT_TIER_VALUES, ROUTE_VALUE_KEYS
from autoharness.verify_workspace import (
    _derive_orchestrator_route_variables,
    _derive_raw_escalation_variables,
    _derive_role_route_variables,
    _derive_tier_route_variables,
    _resolve_context_tier,
    _resolve_role_route_field,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMAS = (
    _REPO_ROOT / "schemas" / "harness-config.schema.json",
    _REPO_ROOT / "schemas" / "harness-config" / "1.1.0.schema.json",
)

_RAW_CONTEXT_TIER_VARIABLES = (
    "LEGACY_ESCALATION_CONTEXT_TIER",
    "STAGE_ESCALATION_CONTEXT_TIER",
    "SHIP_ESCALATION_CONTEXT_TIER",
)


class ContextTierValuesTests(unittest.TestCase):
    def test_context_tier_values_constant(self) -> None:
        self.assertEqual(CONTEXT_TIER_VALUES, ("default", "long_context"))

    def test_schema_enum_parity(self) -> None:
        for schema_path in _SCHEMAS:
            with self.subTest(schema=schema_path.name):
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                self.assertEqual(
                    schema["definitions"]["contextTier"]["enum"],
                    ["", *CONTEXT_TIER_VALUES],
                )

    def test_context_tier_not_yet_a_route_value_key(self) -> None:
        """C2a must not extend the frontmatter contract; that is C5a (194.007-T)."""
        self.assertNotIn("context_tier", ROUTE_VALUE_KEYS)


class ResolveContextTierTests(unittest.TestCase):
    def test_explicit_route_value_wins(self) -> None:
        self.assertEqual(
            _resolve_context_tier({"context_tier": "long_context"}, {"context_tier": "default"}),
            "long_context",
        )

    def test_falls_back_to_tier(self) -> None:
        self.assertEqual(_resolve_context_tier({}, {"context_tier": "long_context"}), "long_context")

    def test_empty_route_value_inherits(self) -> None:
        self.assertEqual(
            _resolve_context_tier({"context_tier": ""}, {"context_tier": "long_context"}),
            "long_context",
        )

    def test_defaults_when_neither_declares(self) -> None:
        self.assertEqual(_resolve_context_tier({}, {}), "default")
        self.assertEqual(_resolve_context_tier({}, None), "default")
        self.assertEqual(_resolve_context_tier({"context_tier": ""}, {"context_tier": ""}), "default")

    def test_legacy_string_tier_gives_default(self) -> None:
        self.assertEqual(_resolve_context_tier({}, "claude-sonnet-5"), "default")

    def test_resolve_role_route_field_is_field_generic(self) -> None:
        self.assertEqual(
            _resolve_role_route_field({}, {"context_tier": "long_context"}, "context_tier"),
            "long_context",
        )
        # Existing fields are unchanged.
        self.assertEqual(_resolve_role_route_field({}, "m2", "model_family"), "m2")


class TierAndOrchestratorContextTierTests(unittest.TestCase):
    def test_tier_variables_resolve_or_default(self) -> None:
        variables = _derive_tier_route_variables(
            {
                "tier1": {"model": "m1", "context_tier": "long_context"},
                "tier2": "legacy-m2",
                "tier3": {"model": "m3", "context_tier": ""},
            }
        )
        self.assertEqual(variables["TIER_1_CONTEXT_TIER"], "long_context")
        self.assertEqual(variables["TIER_2_CONTEXT_TIER"], "default")
        self.assertEqual(variables["TIER_3_CONTEXT_TIER"], "default")

    def test_tier_variables_default_when_tiers_absent(self) -> None:
        variables = _derive_tier_route_variables({})
        for name in ("TIER_1_CONTEXT_TIER", "TIER_2_CONTEXT_TIER", "TIER_3_CONTEXT_TIER"):
            with self.subTest(variable=name):
                self.assertEqual(variables[name], "default")

    def test_orchestrator_explicit_then_tier2_then_default(self) -> None:
        tier2 = {"model": "m2", "context_tier": "long_context"}
        explicit = _derive_orchestrator_route_variables(
            {"tier2": {"model": "m2"}, "orchestrator": {"context_tier": "long_context"}}
        )
        self.assertEqual(explicit["ORCHESTRATOR_CONTEXT_TIER"], "long_context")
        inherited = _derive_orchestrator_route_variables(
            {"tier2": tier2, "orchestrator": {"model_family": "o"}}
        )
        self.assertEqual(inherited["ORCHESTRATOR_CONTEXT_TIER"], "long_context")
        defaulted = _derive_orchestrator_route_variables({"orchestrator": {"model_family": "o"}})
        self.assertEqual(defaulted["ORCHESTRATOR_CONTEXT_TIER"], "default")

    def test_scalar_orchestrator_form_gives_tier2_context_tier(self) -> None:
        variables = _derive_orchestrator_route_variables(
            {"tier2": {"model": "m2", "context_tier": "long_context"}, "orchestrator": "gpt-5.4"}
        )
        self.assertEqual(variables["ORCHESTRATOR_FAMILY"], "gpt-5.4")
        self.assertEqual(variables["ORCHESTRATOR_CONTEXT_TIER"], "long_context")


class RoleContextTierTests(unittest.TestCase):
    def test_ship_fallback_chain_explicit_tier2_default(self) -> None:
        explicit = _derive_role_route_variables(
            {
                "tier2": {"model": "m2", "context_tier": "default"},
                "ship": {"model_family": "s", "context_tier": "long_context"},
            }
        )
        self.assertEqual(explicit["SHIP_CONTEXT_TIER"], "long_context")
        via_tier2 = _derive_role_route_variables(
            {"tier2": {"model": "m2", "context_tier": "long_context"}, "ship": {"model_family": "s"}}
        )
        self.assertEqual(via_tier2["SHIP_CONTEXT_TIER"], "long_context")
        defaulted = _derive_role_route_variables({"tier2": "legacy-m2", "ship": {"model_family": "s"}})
        self.assertEqual(defaulted["SHIP_CONTEXT_TIER"], "default")

    def test_stage_falls_back_to_tier3_not_tier2(self) -> None:
        variables = _derive_role_route_variables(
            {
                "tier2": {"model": "m2", "context_tier": "long_context"},
                "tier3": {"model": "m3"},
            }
        )
        self.assertEqual(variables["STAGE_CONTEXT_TIER"], "default")
        self.assertEqual(variables["SHIP_CONTEXT_TIER"], "long_context")

    def test_role_variables_never_empty(self) -> None:
        variables = _derive_role_route_variables({})
        self.assertEqual(variables["STAGE_CONTEXT_TIER"], "default")
        self.assertEqual(variables["SHIP_CONTEXT_TIER"], "default")


class RawEscalationContextTierTests(unittest.TestCase):
    def test_raw_variables_empty_when_unset(self) -> None:
        raw = _derive_raw_escalation_variables(
            {
                "tier3": {"model": "m3", "context_tier": "long_context"},
                "escalation": {"model_family": "e"},
                "stage": {"context_tier": "long_context", "escalation": {"model_family": "se"}},
                "ship": {"context_tier": "long_context"},
            }
        )
        for name in _RAW_CONTEXT_TIER_VARIABLES:
            with self.subTest(variable=name):
                self.assertEqual(raw[name], "")

    def test_raw_variables_mirror_declared_values_verbatim(self) -> None:
        raw = _derive_raw_escalation_variables(
            {
                "escalation": {"context_tier": "long_context"},
                "stage": {"escalation": {"context_tier": "default"}},
                "ship": {"escalation": {"context_tier": "long_context"}},
            }
        )
        self.assertEqual(raw["LEGACY_ESCALATION_CONTEXT_TIER"], "long_context")
        self.assertEqual(raw["STAGE_ESCALATION_CONTEXT_TIER"], "default")
        self.assertEqual(raw["SHIP_ESCALATION_CONTEXT_TIER"], "long_context")

    def test_raw_variables_never_take_resolved_value(self) -> None:
        """A flat escalation context_tier never leaks into the nested raw slots."""
        raw = _derive_raw_escalation_variables(
            {
                "tier3": {"model": "m3", "context_tier": "long_context"},
                "escalation": {"context_tier": "long_context"},
                "stage": {"escalation": {"model_family": "se"}},
                "ship": {"escalation": {"model_family": "she"}},
            }
        )
        self.assertEqual(raw["STAGE_ESCALATION_CONTEXT_TIER"], "")
        self.assertEqual(raw["SHIP_ESCALATION_CONTEXT_TIER"], "")


if __name__ == "__main__":
    unittest.main()
