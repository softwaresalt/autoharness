"""A2 (214-S): the pure model_routing resolver against the A1 vectors, under the purity guard."""

from __future__ import annotations

import json
import os
import re
import subprocess
import unittest
from pathlib import Path

from _resolver_purity_guard import (
    ImpureAccessError,
    assert_module_import_pure,
    assert_source_import_pure,
    forbid_io,
    guarded_resolve,
)

from autoharness import model_routing

FIXTURE = Path(__file__).parent / "fixtures" / "model_routing" / "existing-semantics.json"
FIELDS = ("model_family", "model_provider", "reasoning_effort", "context_tier")


class ResolverVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = json.loads(FIXTURE.read_text(encoding="utf-8"))["vectors"]

    def test_role_routes_match_vectors(self):
        for vector in self.vectors:
            expected = vector["expected"]
            for role in ("stage", "ship"):
                with self.subTest(vector=vector["id"], role=role):
                    resolved = guarded_resolve(vector["config"], role)
                    want = expected["role_routes"][role]
                    unresolved = any(
                        e.startswith(f"{role} role route") for e in expected["role_route_resolution"]["errors"]
                    )
                    self.assertEqual(resolved.site, role)
                    self.assertEqual(resolved.kind, "route")
                    self.assertEqual(bool(resolved.errors), unresolved)
                    for field in ("model_provider", "reasoning_effort", "context_tier"):
                        self.assertEqual(getattr(resolved, field), want[field])
                    if unresolved:
                        self.assertEqual(resolved.errors, ("ROUTING_UNRESOLVED: model_family",))
                    else:
                        self.assertEqual(resolved.model_family, want["model_family"])

    def test_orchestrator_matches_vectors(self):
        for vector in self.vectors:
            with self.subTest(vector=vector["id"]):
                want = vector["expected"]["orchestrator_route_variables"]
                resolved = guarded_resolve(vector["config"], "orchestrator")
                self.assertEqual(resolved.model_family, want["ORCHESTRATOR_FAMILY"])
                self.assertEqual(resolved.model_provider, want["ORCHESTRATOR_PROVIDER"])
                self.assertEqual(resolved.reasoning_effort, want["ORCHESTRATOR_REASONING_EFFORT"])
                self.assertEqual(resolved.context_tier, want["ORCHESTRATOR_CONTEXT_TIER"])

    def test_escalation_matches_vectors(self):
        for vector in self.vectors:
            expected = vector["expected"]
            esc = expected["escalation_route_resolution"]
            installed = frozenset(vector["installed_roles"])
            for role in ("stage", "ship"):
                with self.subTest(vector=vector["id"], role=role):
                    resolved = guarded_resolve(vector["config"], role, kind="escalation", installed_roles=installed)
                    self.assertEqual(resolved.kind, "escalation")
                    if esc["ambiguous"]:
                        self.assertTrue(resolved.errors[0].startswith("AMBIGUOUS_ESCALATION_CONFIG"))
                        self.assertEqual(resolved.degraded, ())
                        continue
                    want = expected["effective_escalation"][role]
                    for field in FIELDS:
                        self.assertEqual(getattr(resolved, field), want[field])
                    self.assertEqual(bool(resolved.degraded), role in esc["same_route_roles"])
                    if resolved.degraded:
                        self.assertEqual(resolved.degraded, ("ESCALATION_DEGRADED: same-route",))
                    if role in esc["per_role"]:
                        self.assertEqual(resolved.source, esc["per_role"][role]["source"])

    def test_to_document_shape(self):
        document = guarded_resolve(self.vectors[0]["config"], "stage").to_document()
        self.assertEqual(
            set(document),
            {"site", "kind", "resolved", "resolution_chain", "degraded", "errors"},
        )
        self.assertEqual(set(document["resolved"]), {*FIELDS, "tier_class"})
        self.assertEqual(document["resolved"]["tier_class"], "tier3")
        self.assertEqual(json.loads(json.dumps(document)), document)

    def test_resolution_chain_provenance(self):
        config = {
            "model_routing": {
                "tier3": {"model_family": "f", "model_provider": "p"},
                "stage": {"reasoning_effort": "x"},
            }
        }
        self.assertEqual(
            guarded_resolve(config, "stage").resolution_chain,
            ("tier3.model_family", "tier3.model_provider", "stage.reasoning_effort", "default.context_tier"),
        )

    def test_ambiguity_has_no_per_role_resolution(self):
        config = {
            "model_routing": {
                "tier3": {"model_family": "f"},
                "escalation": {"model_family": "a"},
                "ship": {"escalation": {"model_family": "b"}},
            }
        }
        resolved = guarded_resolve(config, "stage", kind="escalation")
        self.assertEqual(resolved.model_family, "")
        self.assertEqual(resolved.resolution_chain, ())
        self.assertTrue(resolved.errors[0].startswith("AMBIGUOUS_ESCALATION_CONFIG"))

    def test_unresolved_family_and_empty_provider_effort(self):
        unresolved = guarded_resolve({"model_routing": {}}, "stage")
        self.assertEqual(unresolved.errors, ("ROUTING_UNRESOLVED: model_family",))
        valid = guarded_resolve({"model_routing": {"tier3": {"model_family": "f"}}}, "stage")
        self.assertEqual((valid.model_provider, valid.reasoning_effort, valid.errors), ("", "", ()))

    def test_explicit_empty_tier_fields_are_preserved_not_nulled(self):
        tier = {"model": "opus", "model_provider": "", "reasoning_effort": ""}
        for field in ("model_provider", "reasoning_effort"):
            self.assertEqual(model_routing.resolve_route_field({}, tier, field), "")
            self.assertIsNone(model_routing.resolve_route_field({}, {}, field))
            self.assertIsNone(
                model_routing.resolve_route_field({}, {field: "   "}, field)
            )

    def test_overrides_are_not_an_input(self):
        base = {"model_routing": {"tier3": {"model_family": "f", "model_provider": "p"}}}
        with_overrides = {**base, "overrides": {"stage": {"model_family": "zzz"}, "context_tier": "long_context"}}
        self.assertEqual(guarded_resolve(with_overrides, "stage"), guarded_resolve(base, "stage"))

    def test_invalid_site_kind_and_orchestrator_escalation(self):
        self.assertTrue(guarded_resolve({}, "nope").errors[0].startswith("UNKNOWN_SITE"))
        self.assertTrue(guarded_resolve({}, "stage", kind="x").errors[0].startswith("UNKNOWN_KIND"))
        self.assertTrue(guarded_resolve({}, "orchestrator", kind="escalation").errors[0].startswith("UNSUPPORTED"))

    def test_non_mapping_model_routing_is_unresolved_not_an_exception(self):
        self.assertEqual(
            guarded_resolve({"model_routing": "oops"}, "ship").errors, ("ROUTING_UNRESOLVED: model_family",)
        )

    def test_invalid_context_tier_is_an_error(self):
        config = {"model_routing": {"tier3": {"model_family": "f", "context_tier": "huge"}}}
        self.assertIn("ROUTING_INVALID: context_tier", guarded_resolve(config, "stage").errors)

    def test_no_resolver_call_bypasses_guarded_resolve(self):
        source = Path(__file__).read_text(encoding="utf-8")
        direct = re.findall(r"\bresolve" r"_site\(", source)
        self.assertEqual(direct, [])


class PurityGuardSelfTests(unittest.TestCase):
    def test_each_channel_trips(self):
        here = Path(__file__)
        channels = {
            "open": lambda: open(__file__),
            "Path.read_text": lambda: here.read_text(),
            "os.stat": lambda: os.stat(__file__),
            "Path.exists": lambda: here.exists(),
            "os.listdir": lambda: os.listdir("."),
            "os.environ": lambda: os.environ["PATH"],
            "os.getenv": lambda: os.getenv("PATH"),
            "subprocess.run": lambda: subprocess.run(["python", "-c", "pass"]),
            "socket": lambda: __import__("socket").create_connection(("127.0.0.1", 9)),
        }
        for name, impure in channels.items():
            with self.subTest(channel=name):
                with self.assertRaises(ImpureAccessError):
                    with forbid_io():
                        impure()

    def test_swallowed_error_still_fails_at_exit(self):
        def swallow():
            with forbid_io():
                try:
                    open(__file__)
                except Exception:
                    pass

        with self.assertRaises(ImpureAccessError):
            swallow()

    def test_pure_stub_passes_and_state_is_restored(self):
        with forbid_io():
            self.assertEqual(sorted({"b": 1, "a": 2}), ["a", "b"])
        with open(__file__, encoding="utf-8") as handle:
            self.assertTrue(handle.read())
        self.assertIn("PATH", os.environ)
        self.assertTrue(Path(__file__).exists())

    def test_state_is_restored_after_exception(self):
        with self.assertRaises(ValueError):
            with forbid_io():
                raise ValueError("boom")
        self.assertTrue(Path(__file__).exists())
        self.assertIn("PATH", os.environ)


class ImportPurityTests(unittest.TestCase):
    def test_model_routing_is_import_pure(self):
        assert_module_import_pure(model_routing)

    def test_negative_import_forms_fail(self):
        for source in (
            "from os import environ\n",
            "def f():\n    import pathlib\n    return pathlib\n",
            "import yaml\n",
            "def f():\n    return open('x')\n",
            "from autoharness.frontmatter_contract import CONTEXT_TIER_VALUES, other\n",
        ):
            with self.subTest(source=source):
                with self.assertRaises(AssertionError):
                    assert_source_import_pure(source)

    def test_allowed_forms_pass(self):
        assert_source_import_pure(
            "from __future__ import annotations\nfrom dataclasses import dataclass\n"
            "from collections.abc import Mapping\nfrom autoharness.frontmatter_contract import CONTEXT_TIER_VALUES\n"
        )


if __name__ == "__main__":
    unittest.main()
