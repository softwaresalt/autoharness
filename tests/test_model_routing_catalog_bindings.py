"""B1 (215-S): tier-delta route catalog and subagent site bindings in the pure resolver.

Vectors live in `fixtures/model_routing/catalog-bindings.json` (plain JSON, the
Go-parity contract) and every resolution runs through `guarded_resolve`, so the
no-I/O property is enforced during each call.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from _resolver_purity_guard import assert_module_import_pure, guarded_resolve

from autoharness import model_routing
from autoharness.model_routing import SiteSpec

FIXTURE = Path(__file__).parent / "fixtures" / "model_routing" / "catalog-bindings.json"
FIELDS = ("model_family", "model_provider", "reasoning_effort", "context_tier")
KNOWN_KEYS = {
    "tier1",
    "tier2",
    "tier3",
    "orchestrator",
    "stage",
    "ship",
    "escalation",
    "anchor_review",
    "alt_review",
    "alt_doc_review",
    "routes",
    "bindings",
}


def _sites(vector):
    return {
        site_id: SiteSpec(site_id, spec["default_tier"], spec["managed"])
        for site_id, spec in vector["sites"].items()
    }


def _resolve(vector, config=None):
    return guarded_resolve(config if config is not None else vector["config"], vector["site"], sites=_sites(vector))


class CatalogBindingsVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.vectors = cls.doc["vectors"]

    def test_fixture_is_plain_json_with_unique_ids(self):
        ids = [v["id"] for v in self.vectors]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({v["branch"] for v in self.vectors}, {"bound", "unbound", "error"})

    def test_every_vector_matches_its_expectation(self):
        for vector in self.vectors:
            with self.subTest(vector=vector["id"]):
                resolved = _resolve(vector)
                expected = vector["expected"]
                for field in FIELDS:
                    self.assertEqual(getattr(resolved, field), expected[field], field)
                self.assertEqual(resolved.tier_class, expected["tier_class"])
                self.assertEqual(list(resolved.errors), expected["errors"])
                self.assertEqual(list(resolved.resolution_chain), expected["resolution_chain"])
                self.assertEqual(resolved.site, vector["site"])
                self.assertEqual(resolved.kind, "route")

    def test_bound_chain_never_names_the_site_default_tier(self):
        checked = 0
        for vector in self.vectors:
            if vector["branch"] != "bound":
                continue
            default_tier = vector["sites"][vector["site"].split(":", 1)[1]]["default_tier"]
            resolved = _resolve(vector)
            if default_tier is None or resolved.tier_class == default_tier:
                continue
            checked += 1
            with self.subTest(vector=vector["id"]):
                for entry in resolved.resolution_chain:
                    self.assertFalse(entry.startswith(f"{default_tier}."), entry)
        self.assertGreaterEqual(checked, 5)

    def test_unbound_chain_names_no_binding_or_catalog_layer(self):
        for vector in self.vectors:
            if vector["branch"] != "unbound":
                continue
            with self.subTest(vector=vector["id"]):
                for entry in _resolve(vector).resolution_chain:
                    self.assertFalse(entry.startswith(("bindings.", "routes.")), entry)

    def test_overrides_in_config_change_no_field(self):
        for vector in self.vectors:
            with self.subTest(vector=vector["id"]):
                config = copy.deepcopy(vector["config"])
                config["overrides"] = {
                    "TIER_1_FAMILY": "zzz",
                    "TIER_2_PROVIDER": "zzz",
                    "TIER_3_CONTEXT_TIER": "long_context",
                    "agent:x": {"model_family": "zzz"},
                }
                self.assertEqual(_resolve(vector, config), _resolve(vector))

    def test_bound_and_unbound_branch_contrast_on_one_config(self):
        by_id = {v["id"]: v for v in self.vectors}
        unbound = _resolve(by_id["unbound-inherits-every-field-from-site-default-tier"])
        self.assertEqual(
            (unbound.model_provider, unbound.reasoning_effort, unbound.context_tier),
            ("prov-t2", "high", "long_context"),
        )
        for vid in ("bound-bare-tier-keeps-unset-fields-empty", "bound-catalog-route-sets-only-effort"):
            bound = _resolve(by_id[vid])
            self.assertEqual(bound.model_provider, "", vid)
            self.assertEqual(bound.context_tier, "default", vid)
            self.assertNotEqual(bound.reasoning_effort, "high", vid)

    def test_six_baseline_profiles_are_covered(self):
        profiles = {v["site"].split(":", 1)[1] for v in self.vectors if v["id"].startswith("baseline-profile-")}
        self.assertEqual(profiles, {"fast", "ingest", "standard", "repair", "reviewer", "architect"})


class SiteRegistryInputTests(unittest.TestCase):
    CONFIG = {"model_routing": {"tier1": {"model_family": "f1"}, "bindings": {"agent:x": {"route": "tier1"}}}}

    def test_sites_is_an_input_never_discovered(self):
        resolved = guarded_resolve(self.CONFIG, "agent:x")
        self.assertEqual(resolved.errors, ("ROUTING_UNKNOWN_SITE: agent:x",))
        resolved = guarded_resolve(self.CONFIG, "agent:x", sites={})
        self.assertEqual(resolved.errors, ("ROUTING_UNKNOWN_SITE: agent:x",))

    def test_sites_mapping_is_not_mutated(self):
        sites = {"x": SiteSpec("x", "tier2", True)}
        snapshot = dict(sites)
        guarded_resolve(self.CONFIG, "agent:x", sites=sites)
        self.assertEqual(sites, snapshot)

    def test_site_spec_has_exactly_three_frozen_fields(self):
        spec = SiteSpec("x", "tier1", True)
        self.assertEqual(
            [f for f in spec.__dataclass_fields__], ["site", "default_tier", "managed"]
        )
        with self.assertRaises(AttributeError):
            spec.managed = False

    def test_role_sites_and_escalation_are_unchanged_by_sites(self):
        config = {"model_routing": {"tier3": {"model_family": "f3"}}}
        sites = {"x": SiteSpec("x", "tier2", True)}
        self.assertEqual(guarded_resolve(config, "stage", sites=sites), guarded_resolve(config, "stage"))
        self.assertEqual(
            guarded_resolve(config, "stage", kind="escalation", sites=sites),
            guarded_resolve(config, "stage", kind="escalation"),
        )

    def test_agent_site_has_no_escalation(self):
        resolved = guarded_resolve(
            self.CONFIG, "agent:x", kind="escalation", sites={"x": SiteSpec("x", "tier2", True)}
        )
        self.assertTrue(resolved.errors[0].startswith("UNSUPPORTED"))

    def test_non_agent_unknown_site_keeps_the_legacy_code(self):
        self.assertTrue(guarded_resolve(self.CONFIG, "nope").errors[0].startswith("UNKNOWN_SITE"))

    def test_malformed_bindings_and_routes_are_errors_not_exceptions(self):
        sites = {"x": SiteSpec("x", "tier2", True)}
        for bindings in ("oops", ["agent:x"], {"agent:x": "tier1"}, {"agent:x": None}):
            with self.subTest(bindings=bindings):
                config = {"model_routing": {"tier1": {"model_family": "f1"}, "bindings": bindings}}
                resolved = guarded_resolve(config, "agent:x", sites=sites)
                self.assertIsInstance(resolved.errors, tuple)
        config = {
            "model_routing": {
                "tier1": {"model_family": "f1"},
                "routes": {"r": "tier1"},
                "bindings": {"agent:x": {"route": "r"}},
            }
        }
        self.assertEqual(
            guarded_resolve(config, "agent:x", sites=sites).errors, ("ROUTING_CATALOG_INVALID: r: not a mapping",)
        )


class KnownKeysAndPurityTests(unittest.TestCase):
    def test_known_keys_is_a_frozenset_of_exactly_the_twelve_keys(self):
        self.assertIsInstance(model_routing.MODEL_ROUTING_KNOWN_KEYS, frozenset)
        self.assertEqual(model_routing.MODEL_ROUTING_KNOWN_KEYS, KNOWN_KEYS)
        self.assertEqual(len(model_routing.MODEL_ROUTING_KNOWN_KEYS), 12)

    def test_module_is_still_import_pure(self):
        assert_module_import_pure(model_routing)

    def test_no_resolver_call_bypasses_guarded_resolve(self):
        import re

        source = Path(__file__).read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"\bresolve" r"_site\(", source), [])


if __name__ == "__main__":
    unittest.main()
