"""A1 (214-S): pin today's model_routing resolution as language-neutral vectors.

The fixture is plain JSON (the Go-parity contract for F194A1D8). Each vector is
run through the current `verify_workspace` helpers and compared to the frozen
expectation, so a later refactor that changes behavior fails here.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from autoharness import verify_workspace as vw

FIXTURE = Path(__file__).parent / "fixtures" / "model_routing" / "existing-semantics.json"


def _role_routes(model_routing):
    out = {}
    for role, tier in vw.ROLE_ROUTE_TIER_FALLBACK.items():
        route = model_routing.get(role) or {}
        if not isinstance(route, dict):
            route = {}
        fallback = vw._tier_fallback_dict(model_routing, tier)
        out[role] = {
            "model_family": vw._resolve_role_route_field(route, fallback, "model_family") or "",
            "model_provider": vw._resolve_role_route_field(route, fallback, "model_provider") or "",
            "reasoning_effort": vw._resolve_role_route_field(route, fallback, "reasoning_effort") or "",
            "context_tier": vw._resolve_context_tier(route, fallback),
        }
    return out


def _effective_escalation(model_routing):
    out = {}
    for role in vw.ROLE_ROUTE_TIER_FALLBACK:
        family, provider, effort = vw._effective_escalation_route_for_role(model_routing, role)
        out[role] = {
            "model_family": family,
            "model_provider": provider,
            "reasoning_effort": effort,
            "context_tier": vw._effective_escalation_context_tier_for_role(model_routing, role),
        }
    return out


def _check(adder, config, **kwargs):
    report = {"targeted_checks": {}}
    adder(report, "k", config, **kwargs)
    return report["targeted_checks"]["k"]


class ExistingSemanticsVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = FIXTURE.read_text(encoding="utf-8")
        cls.doc = json.loads(cls.raw)

    def test_fixture_is_plain_json_with_unique_ids(self):
        ids = [v["id"] for v in self.doc["vectors"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 14)
        for banned in ("!!python", "&id0", "NaN", "Infinity"):
            self.assertNotIn(banned, self.raw)
        # A round trip proves nothing but JSON-native types are present.
        self.assertEqual(json.loads(json.dumps(self.doc)), self.doc)

    def test_every_vector_records_the_full_check_dicts(self):
        for vector in self.doc["vectors"]:
            with self.subTest(vector=vector["id"]):
                expected = vector["expected"]
                self.assertIn("ok", expected["role_route_resolution"])
                esc = expected["escalation_route_resolution"]
                for key in ("ok", "errors", "ambiguous", "same_route_roles"):
                    self.assertIn(key, esc)
                if not esc["ambiguous"]:
                    self.assertIn("per_role", esc)

    def test_vectors_match_current_helpers(self):
        for vector in self.doc["vectors"]:
            with self.subTest(vector=vector["id"]):
                config = vector["config"]
                mr = config["model_routing"]
                installed = set(vector["installed_roles"])
                expected = vector["expected"]
                self.assertEqual(_role_routes(mr), expected["role_routes"])
                self.assertEqual(
                    vw._derive_orchestrator_route_variables(mr),
                    expected["orchestrator_route_variables"],
                )
                self.assertEqual(
                    _check(vw._add_role_route_resolution_check, config),
                    expected["role_route_resolution"],
                )
                escalation = _check(
                    vw._add_escalation_route_resolution_check,
                    config,
                    stage_installed="stage" in installed,
                    ship_installed="ship" in installed,
                )
                self.assertEqual(escalation, expected["escalation_route_resolution"])
                if not escalation["ambiguous"]:
                    self.assertEqual(_effective_escalation(mr), expected["effective_escalation"])
                else:
                    self.assertEqual(expected["effective_escalation"], {})

    def test_named_semantics_are_pinned(self):
        by_id = {v["id"]: v["expected"] for v in self.doc["vectors"]}
        self.assertTrue(by_id["both-present-ambiguous"]["escalation_route_resolution"]["ambiguous"])
        self.assertEqual(
            by_id["same-route-guard-true"]["escalation_route_resolution"]["same_route_roles"], ["stage"]
        )
        self.assertEqual(
            by_id["same-family-different-provider"]["escalation_route_resolution"]["same_route_roles"], []
        )
        self.assertEqual(
            by_id["context-tier-only-difference-still-same-route"]["escalation_route_resolution"][
                "same_route_roles"
            ],
            ["stage"],
        )
        self.assertEqual(
            by_id["installed-role-widening-no-key"]["escalation_route_resolution"]["same_route_roles"], ["ship"]
        )
        self.assertEqual(
            by_id["installed-role-not-installed-no-key"]["escalation_route_resolution"]["same_route_roles"], []
        )
        self.assertTrue(by_id["empty-provider-and-effort-valid"]["role_route_resolution"]["ok"])
        self.assertFalse(by_id["unset-model-family"]["role_route_resolution"]["ok"])


if __name__ == "__main__":
    unittest.main()
