"""A3 (214-S): verify_workspace route helpers delegate to the model_routing resolver."""

from __future__ import annotations

import unittest
from unittest import mock

from autoharness import model_routing
from autoharness import verify_workspace as vw

MR = {
    "tier2": {"model_family": "t2", "model_provider": "p2", "reasoning_effort": "medium"},
    "tier3": {"model_family": "t3", "model_provider": "p3", "reasoning_effort": "high"},
    "stage": {"model_family": "s", "escalation": {"model_family": "e"}},
}
CONFIG = {"model_routing": MR}


class HelperDelegationTests(unittest.TestCase):
    def assert_delegates(self, name, invoke):
        with mock.patch.object(model_routing, name, wraps=getattr(model_routing, name)) as spy:
            invoke()
        self.assertTrue(spy.called, f"{name} was not called")

    def test_primitive_helpers(self):
        cases = {
            "tier_dict": lambda: vw._model_routing_tier_dict(MR, "tier3"),
            "tier_fallback_dict": lambda: vw._tier_fallback_dict(MR, "tier3"),
            "resolve_route_field": lambda: vw._resolve_role_route_field({}, MR["tier3"], "model_family"),
            "resolve_context_tier": lambda: vw._resolve_context_tier({}, MR["tier3"]),
            "escalation_route_has_any_field": lambda: vw._escalation_route_has_any_field({"model_family": "x"}),
            "effective_escalation_route": lambda: vw._effective_escalation_route_for_role(MR, "stage"),
            "effective_escalation_context_tier": lambda: vw._effective_escalation_context_tier_for_role(MR, "stage"),
        }
        for name, invoke in cases.items():
            with self.subTest(helper=name):
                self.assert_delegates(name, invoke)

    def test_variable_derivations_use_resolve_site(self):
        for label, invoke in {
            "role": lambda: vw._derive_role_route_variables(MR),
            "orchestrator": lambda: vw._derive_orchestrator_route_variables(MR),
        }.items():
            with self.subTest(derivation=label):
                self.assert_delegates("resolve_site", invoke)

    def test_checks_use_resolve_site(self):
        def role_check():
            vw._add_role_route_resolution_check({"targeted_checks": {}}, "k", CONFIG)

        def escalation_check():
            vw._add_escalation_route_resolution_check({"targeted_checks": {}}, "k", CONFIG, stage_installed=True)

        for label, invoke in {"role": role_check, "escalation": escalation_check}.items():
            with self.subTest(check=label):
                self.assert_delegates("resolve_site", invoke)

    def test_own_family_defaults_are_shared_not_copied(self):
        self.assertIs(vw._TIER_OWN_FAMILY_DEFAULT, model_routing.TIER_OWN_FAMILY_DEFAULT)

    def test_delegated_value_is_what_the_helper_returns(self):
        sentinel = mock.Mock(
            model_family="SENT-F",
            model_provider="SENT-P",
            reasoning_effort="SENT-E",
            context_tier="long_context",
            errors=(),
        )
        with mock.patch.object(model_routing, "resolve_site", return_value=sentinel):
            variables = vw._derive_role_route_variables(MR)
        self.assertEqual(variables["STAGE_FAMILY"], "SENT-F")
        self.assertEqual(variables["SHIP_PROVIDER"], "SENT-P")
        self.assertEqual(variables["STAGE_CONTEXT_TIER"], "long_context")

    def test_no_new_targeted_check_keys(self):
        report = {"targeted_checks": {}}
        vw._add_role_route_resolution_check(report, "k", CONFIG)
        self.assertEqual(set(report["targeted_checks"]["k"]), {"ok", "errors"})
        vw._add_escalation_route_resolution_check(report, "e", CONFIG)
        self.assertEqual(
            set(report["targeted_checks"]["e"]),
            {
                "ok",
                "errors",
                "ambiguous",
                "resolved_escalation_family",
                "resolved_escalation_provider",
                "resolved_escalation_reasoning_effort",
                "same_route_roles",
                "deprecated_flat_in_use",
                "per_role",
            },
        )


if __name__ == "__main__":
    unittest.main()
