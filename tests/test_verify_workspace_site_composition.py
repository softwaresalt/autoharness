"""B6a (215-S, 208.007-T): render-time site composition for bound subagents.

`_compose_site_route_variables` is the single shared composition function: both render
seams (the staged loop and the in-memory community render) call it, and
`_expected_site_route` reads its expectation from the same composed map.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import yaml

from autoharness import frontmatter_contract as fc
from autoharness import model_routing_sites as mrs
from autoharness import verify_workspace as vw
from autoharness.model_routing import SiteSpec
from autoharness.model_routing_sites import SiteRegistry

REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTE_FIELDS = ("model_family", "model_provider", "reasoning_effort", "context_tier")
NO_TIER = "---\nname: Fixture\ndescription: A fixture\nmodel_family: fixed\n---\n\n# Fixture\n"
INSTALLED = "---\nname: Fixture\n---\n\n# Fixture\n"


def template(tier: int) -> str:
    return (
        "---\n"
        "name: Fixture\n"
        'description: "A fixture"\n'
        f"max_subagent_tier: {tier}\n"
        f'reasoning_effort: "{{{{TIER_{tier}_REASONING_EFFORT}}}}"\n'
        f'model_provider: "{{{{TIER_{tier}_PROVIDER}}}}"\n'
        f'model_family: "{{{{TIER_{tier}_FAMILY}}}}"\n'
        f'context_tier: "{{{{TIER_{tier}_CONTEXT_TIER}}}}"\n'
        "subagent_depth: 0\n"
        "---\n\n# Fixture\n"
    )


def routing(*, bindings: dict | None = None) -> dict:
    block: dict[str, Any] = {
        "tier1": {"model_family": "f1"},
        "tier2": {
            "model_family": "f2",
            "model_provider": "p2",
            "reasoning_effort": "e2",
            "context_tier": "long_context",
        },
        "tier3": {"model_family": "f3"},
        "routes": {"fast": {"tier": "tier1", "model_family": "f-fast"}},
    }
    if bindings is not None:
        block["bindings"] = bindings
    return block


def parse_route(raw: bytes) -> dict[str, str]:
    data = yaml.safe_load(raw.decode("utf-8").split("---")[1])
    return {field: data[field] for field in ROUTE_FIELDS}


class Fixture:
    def __init__(self, root: Path) -> None:
        self.home = (root / "home").resolve()
        self.ws = (root / "ws").resolve()
        (self.home / "templates").mkdir(parents=True)
        (self.ws / ".autoharness").mkdir(parents=True)
        shutil.copytree(REPO_ROOT / "schemas", self.home / "schemas")
        self.artifacts: list[dict] = []
        self.community: list[dict] = []
        self.kinds: dict[str, str] = {}
        self.staging = self.ws / ".autoharness" / "staging"

    def _write(self, base: Path, rel: str, text: str) -> None:
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def add(self, site: str, kind: str, template_text: str | None = None, tier: int = 2) -> None:
        self.kinds[site] = kind
        text = template(tier) if template_text is None else template_text
        if kind == "rendered":
            rel = f".github/agents/subagents/{site}.agent.md"
            self._write(self.ws, rel, INSTALLED)
            self._write(self.home / "templates", f"agents/review/{site}.agent.md.tmpl", text)
            self.artifacts.append(
                {"path": rel, "template": f"agents/review/{site}.agent.md.tmpl", "checksum": "", "primitive": 1}
            )
        elif kind == "community":
            rel = f".github/agents/{site}.agent.md"
            template_path = f"templates/community/agents/{site}.agent.md.tmpl"
            self._write(self.ws, rel, INSTALLED)
            self._write(self.home, template_path, text)
            self.community.append({"installed_path": rel, "template_path": template_path, "template_id": site})
        else:
            self._write(self.ws, f".github/agents/{site}.agent.md", INSTALLED)

    def rel(self, site: str) -> str:
        return {
            "rendered": f".github/agents/subagents/{site}.agent.md",
            "community": f".github/agents/{site}.agent.md",
            "authored": f".github/agents/{site}.agent.md",
        }[self.kinds[site]]

    @property
    def manifest(self) -> dict:
        return {"artifacts": self.artifacts, "community_templates": self.community}

    def write_config(self, model_routing_block: dict, overrides: dict | None = None) -> dict:
        config: dict[str, Any] = {"schema_version": "1.2.0", "model_routing": model_routing_block}
        if overrides is not None:
            config["overrides"] = overrides
        self._write(self.ws, ".autoharness/config.yaml", yaml.safe_dump(config, sort_keys=False))
        self._write(self.ws, ".autoharness/harness-manifest.yaml", yaml.safe_dump(self.manifest, sort_keys=False))
        self.config = config
        return config

    def variables(self, authoritative: bool = True) -> dict[str, str]:
        return vw._derive_template_variables(
            self.ws, self.manifest, self.config, {}, {}, config_authoritative=authoritative
        )

    def registry(self) -> SiteRegistry:
        return mrs.build_site_registry(self.ws, self.home, self.manifest, {})

    def overrides(self, authoritative: bool = True) -> Any:
        return self.config.get("overrides") if authoritative else None

    def expected(self, site: str, authoritative: bool = True) -> dict[str, str] | None:
        return vw._expected_site_route(
            self.variables(authoritative),
            self.config["model_routing"],
            site,
            self.registry(),
            config_authoritative=authoritative,
            overrides=self.overrides(authoritative),
        )

    def staged_bytes(self, site: str) -> bytes:
        vw.verify_workspace(self.ws, self.home, self.staging)
        return vw._normalize_stage_path(self.staging, self.rel(site)).read_bytes()

    def candidate_bytes(self, site: str, authoritative: bool = True) -> bytes:
        index = vw._fc_build_provenance_index(self.ws, self.home, self.manifest)
        entry = vw._fc_classify(self.rel(site), index)
        record = {
            "class": entry["class"],
            "entry": entry,
            "rel": self.rel(site),
            "kind": "agent",
            "profile": fc.PROFILE_TIER_ROUTED,
        }
        captured: list[bytes] = []

        def capture(raw: bytes, rec: dict) -> list:
            captured.append(raw)
            return []

        with mock.patch.object(vw, "_fc_check_bytes", side_effect=capture):
            result = vw._fc_rendered_candidate(
                record,
                {},
                self.home,
                self.variables(authoritative),
                self.config["model_routing"],
                config_authoritative=authoritative,
                overrides=self.overrides(authoritative),
                site_registry=self.registry(),
            )
        assert result["status"] == "pass", result
        return captured[0]

    def render(self, site: str, authoritative: bool = True) -> bytes:
        if self.kinds[site] == "rendered":
            return self.staged_bytes(site)
        return self.candidate_bytes(site, authoritative)


class SiteCompositionCase(unittest.TestCase):
    SEAMS = ("rendered", "community")

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.fx = Fixture(Path(self._tmp.name))

    def assert_round_trip(self, site: str, rendered: bytes, authoritative: bool = True) -> dict[str, str]:
        parsed = parse_route(rendered)
        self.assertEqual(self.fx.expected(site, authoritative), parsed, "expected route != parsed rendered bytes")
        return parsed

    def setup_bound(self, kind: str, *, overrides: dict | None = None, route: str = "fast", tier: int = 2) -> None:
        self.fx.add("alpha", kind, tier=tier)
        self.fx.write_config(routing(bindings={"agent:alpha": {"route": route}}), overrides)


class BoundBranchTests(SiteCompositionCase):
    BOUND = {"model_family": "f-fast", "model_provider": "", "reasoning_effort": "", "context_tier": "default"}

    def test_bound_agent_renders_with_the_binding_at_both_seams(self) -> None:
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.setup_bound(kind)
                self.assertEqual(self.assert_round_trip("alpha", self.fx.render("alpha")), self.BOUND)

    def test_bound_tier_with_empty_fields_overwrites_instead_of_inheriting(self) -> None:
        # The agent's own tier2 supplies p2/e2/long_context; the bound tier1 route leaves them empty.
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.setup_bound(kind)
                parsed = self.assert_round_trip("alpha", self.fx.render("alpha"))
                self.assertEqual(
                    (parsed["model_provider"], parsed["reasoning_effort"], parsed["context_tier"]),
                    ("", "", "default"),
                )
                self.fx.write_config(routing())
                unbound = self.assert_round_trip("alpha", self.fx.render("alpha"))
                self.assertEqual(
                    unbound,
                    {
                        "model_family": "f2",
                        "model_provider": "p2",
                        "reasoning_effort": "e2",
                        "context_tier": "long_context",
                    },
                )

    def test_override_on_the_agents_own_tier_wins_per_variable(self) -> None:
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.setup_bound(kind, overrides={"TIER_2_FAMILY": "ov-fam", "TIER_2_PROVIDER": "ov-prov"})
                parsed = self.assert_round_trip("alpha", self.fx.render("alpha"))
                self.assertEqual(parsed["model_family"], "ov-fam")
                self.assertEqual(parsed["model_provider"], "ov-prov")
                self.assertEqual((parsed["reasoning_effort"], parsed["context_tier"]), ("", "default"))

    def test_valid_context_tier_override_wins(self) -> None:
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.setup_bound(kind, overrides={"TIER_2_CONTEXT_TIER": "long_context"})
                parsed = self.assert_round_trip("alpha", self.fx.render("alpha"))
                self.assertEqual(parsed["context_tier"], "long_context")
                self.assertEqual(parsed["model_family"], "f-fast")

    def test_override_on_the_bound_routes_tier_variables_does_not_reach_the_agent(self) -> None:
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.setup_bound(kind, overrides={"TIER_1_FAMILY": "ov-fam", "TIER_1_PROVIDER": "ov-prov"})
                parsed = self.assert_round_trip("alpha", self.fx.render("alpha"))
                self.assertEqual(parsed, self.BOUND)

    def test_invalid_context_tier_override_is_skipped(self) -> None:
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.setup_bound(kind, overrides={"TIER_2_CONTEXT_TIER": "bogus"})
                parsed = self.assert_round_trip("alpha", self.fx.render("alpha"))
                self.assertEqual(parsed["context_tier"], "default")

    def test_bound_route_on_a_higher_tier_than_the_agent_default(self) -> None:
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.fx.add("alpha", kind, tier=1)
                config_block = routing(bindings={"agent:alpha": {"route": "tier3", "reasoning_effort": "max"}})
                self.fx.write_config(config_block)
                parsed = self.assert_round_trip("alpha", self.fx.render("alpha"))
                self.assertEqual(parsed["model_family"], "f3")
                self.assertEqual(parsed["reasoning_effort"], "max")


class UnboundAndNoOverlayTests(SiteCompositionCase):
    def test_unbound_agents_render_byte_identically_to_a_workspace_without_bindings(self) -> None:
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.fx.add("alpha", kind)
                self.fx.add("beta", kind, tier=1)
                self.fx.write_config(routing())
                baseline = {site: self.fx.render(site) for site in ("alpha", "beta")}
                self.fx.write_config(routing(bindings={"agent:alpha": {"route": "fast"}}))
                self.assertNotEqual(self.fx.render("alpha"), baseline["alpha"])
                self.assertEqual(self.fx.render("beta"), baseline["beta"])
                self.assert_round_trip("beta", self.fx.render("beta"))

    def test_unbound_agent_with_override_is_unchanged(self) -> None:
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.fx.add("alpha", kind)
                self.fx.add("beta", kind, tier=1)
                overrides = {"TIER_2_FAMILY": "ov-fam"}
                self.fx.write_config(routing(), overrides)
                baseline = self.fx.render("alpha")
                self.fx.write_config(routing(bindings={"agent:beta": {"route": "fast"}}), overrides)
                self.assertEqual(self.fx.render("alpha"), baseline)
                self.assertEqual(self.assert_round_trip("alpha", baseline)["model_family"], "ov-fam")

    def test_composition_returns_the_base_map_itself_when_nothing_overlays(self) -> None:
        self.fx.add("alpha", "community")
        self.fx.add("beta", "community", NO_TIER)
        self.fx.add("custom", "authored")
        block = routing(
            bindings={
                "agent:alpha": {"route": "nope"},
                "agent:custom": {"route": "fast"},
            }
        )
        self.fx.write_config(block)
        registry = self.fx.registry()
        base = self.fx.variables()
        cases = {
            "unbound managed site": ("beta", True),
            "binding does not resolve": ("alpha", True),
            "workspace-authored site": ("custom", True),
            "unregistered site": ("ghost", True),
            "pipeline artifact (no site)": (None, True),
        }
        for label, (site, authoritative) in cases.items():
            with self.subTest(label=label):
                composed = vw._compose_site_route_variables(
                    base, block, site, registry, config_authoritative=authoritative, overrides=None
                )
                self.assertIs(composed, base)

    def test_non_authoritative_config_gets_the_base_map(self) -> None:
        self.setup_bound("community")
        base = self.fx.variables(False)
        composed = vw._compose_site_route_variables(
            base,
            self.fx.config["model_routing"],
            "alpha",
            self.fx.registry(),
            config_authoritative=False,
            overrides=None,
        )
        self.assertIs(composed, base)
        parsed = self.assert_round_trip("alpha", self.fx.candidate_bytes("alpha", False), authoritative=False)
        self.assertEqual(parsed["model_family"], "f2")

    def test_bound_site_with_unresolved_default_tier_gets_no_overlay(self) -> None:
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.fx.add("alpha", kind, NO_TIER)
                self.fx.write_config(routing(bindings={"agent:alpha": {"route": "fast"}}))
                registry = self.fx.registry()
                self.assertEqual(dict(registry.unresolved), {"alpha": "no-tier-placeholder"})
                base = self.fx.variables()
                composed = vw._compose_site_route_variables(
                    base,
                    self.fx.config["model_routing"],
                    "alpha",
                    registry,
                    config_authoritative=True,
                    overrides=None,
                )
                self.assertIs(composed, base)
                self.assertIsNone(self.fx.expected("alpha"))

    def test_bound_site_whose_binding_does_not_resolve_gets_the_base_map_render(self) -> None:
        for kind in self.SEAMS:
            with self.subTest(kind=kind):
                self.setUp()
                self.setup_bound(kind, route="nope")
                parsed = self.assert_round_trip("alpha", self.fx.render("alpha"))
                self.assertEqual(parsed["model_family"], "f2")

    def test_missing_registry_means_no_overlay(self) -> None:
        self.setup_bound("rendered")
        base = self.fx.variables()
        composed = vw._compose_site_route_variables(
            base, self.fx.config["model_routing"], "alpha", None, config_authoritative=True, overrides=None
        )
        self.assertIs(composed, base)

    def test_composition_never_mutates_the_base_map(self) -> None:
        self.setup_bound("community", overrides={"TIER_2_FAMILY": "ov"})
        base = self.fx.variables()
        snapshot = dict(base)
        composed = vw._compose_site_route_variables(
            base,
            self.fx.config["model_routing"],
            "alpha",
            self.fx.registry(),
            config_authoritative=True,
            overrides=self.fx.overrides(),
        )
        self.assertIsNot(composed, base)
        self.assertEqual(base, snapshot)

    def test_config_authoritative_has_no_default(self) -> None:
        with self.assertRaises(TypeError):
            vw._compose_site_route_variables({}, {}, "alpha", None, overrides=None)  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            vw._compose_site_route_variables({}, {}, "alpha", None, config_authoritative=True)  # type: ignore[call-arg]

    def test_site_id_comes_from_agent_artifacts_only(self) -> None:
        self.assertEqual(vw._site_id_for_artifact(".github/agents/subagents/alpha.agent.md"), "alpha")
        self.assertEqual(vw._site_id_for_artifact(".github/agents/beta.agent.md"), "beta")
        for rel in (
            ".github/agents/_stage.agent.md",
            ".github/agents/_ship.agent.md",
            ".github/agents/_orchestrator.agent.md",
            ".github/instructions/x.instructions.md",
            "docs/alpha.agent.md",
            ".github/skills/x/SKILL.md",
        ):
            with self.subTest(rel=rel):
                self.assertIsNone(vw._site_id_for_artifact(rel))


class ExpectedRouteTests(SiteCompositionCase):
    def test_workspace_authored_bound_site_reads_the_resolver_output_alone(self) -> None:
        self.fx.add("custom", "authored")
        self.fx.write_config(routing(bindings={"agent:custom": {"route": "fast", "reasoning_effort": "low"}}))
        self.assertEqual(
            self.fx.expected("custom"),
            {"model_family": "f-fast", "model_provider": "", "reasoning_effort": "low", "context_tier": "default"},
        )
        self.assertIsNone(self.fx.expected("custom", authoritative=False))

    def test_unbound_authored_unregistered_and_pipeline_sites_have_no_expectation(self) -> None:
        self.fx.add("custom", "authored")
        self.fx.write_config(routing())
        self.assertIsNone(self.fx.expected("custom"))
        self.assertIsNone(self.fx.expected("ghost"))

    def test_unbound_managed_site_expects_its_default_tier(self) -> None:
        self.fx.add("alpha", "rendered", tier=1)
        self.fx.write_config(routing())
        self.assertEqual(
            self.fx.expected("alpha"),
            {"model_family": "f1", "model_provider": "", "reasoning_effort": "", "context_tier": "default"},
        )


class ReinstallRegressionTests(SiteCompositionCase):
    def _candidate_through_the_conformity_check(self, overrides: dict | None) -> bytes:
        self.setup_bound("community", overrides=overrides)
        captured: list[bytes] = []
        real = vw._fc_check_bytes

        def capture(raw: bytes, record: dict) -> list:
            captured.append(raw)
            return real(raw, record)

        with mock.patch.object(vw, "_fc_check_bytes", side_effect=capture):
            report = vw.verify_workspace(self.fx.ws, self.fx.home, self.fx.staging)
        self.assertEqual(len(captured), 1, report["targeted_checks"].get("frontmatter_conformity"))
        return captured[0]

    def test_community_candidate_behind_a_reinstall_proposal_carries_the_bound_route(self) -> None:
        for overrides, family in ((None, "f-fast"), ({"TIER_2_FAMILY": "ov-fam"}, "ov-fam")):
            with self.subTest(overrides=overrides):
                self.setUp()
                raw = self._candidate_through_the_conformity_check(overrides)
                parsed = parse_route(raw)
                self.assertEqual(parsed["model_family"], family)
                self.assertEqual((parsed["model_provider"], parsed["reasoning_effort"]), ("", ""))
                self.assertEqual(self.fx.expected("alpha"), parsed)

    def test_staged_render_reproduces_the_bound_route_with_and_without_an_override(self) -> None:
        for overrides, family in ((None, "f-fast"), ({"TIER_2_FAMILY": "ov-fam"}, "ov-fam")):
            with self.subTest(overrides=overrides):
                self.setUp()
                self.setup_bound("rendered", overrides=overrides)
                parsed = self.assert_round_trip("alpha", self.fx.staged_bytes("alpha"))
                self.assertEqual(parsed["model_family"], family)

    def test_bound_unresolved_site_candidate_carries_no_binding(self) -> None:
        self.fx.add("alpha", "community", NO_TIER)
        self.fx.write_config(routing(bindings={"agent:alpha": {"route": "fast"}}))
        self.assertEqual(self.fx.render("alpha"), NO_TIER.encode("utf-8"))


class SingleFunctionContractTests(unittest.TestCase):
    SOURCE = (REPO_ROOT / "src" / "autoharness" / "verify_workspace.py").read_text(encoding="utf-8")

    @staticmethod
    def _function_body(source: str, name: str) -> str:
        match = re.search(rf"^def {name}\(.*?(?=^def |\Z)", source, re.DOTALL | re.MULTILINE)
        assert match, name
        return match.group(0)

    def test_both_render_seams_and_the_expectation_call_the_shared_function(self) -> None:
        for name in ("_fc_rendered_candidate", "_expected_site_route"):
            with self.subTest(name=name):
                self.assertIn("_compose_site_route_variables(", self._function_body(self.SOURCE, name))
        main = self._function_body(self.SOURCE, "verify_workspace")
        self.assertIn("_compose_site_route_variables(", main)
        calls = re.findall(r"(?<!def )_compose_site_route_variables\(", self.SOURCE)
        self.assertGreaterEqual(len(calls), 3)

    def test_no_other_composition_of_a_sites_tier_variables(self) -> None:
        # The only f-string that builds a per-tier variable name from a computed tier number.
        builders = re.findall(r'f"TIER_\{', self.SOURCE)
        self.assertEqual(len(builders), 1)
        owner = self._function_body(self.SOURCE, "_site_tier_variable_names")
        self.assertIn('f"TIER_{', owner)

    def test_shared_function_signature(self) -> None:
        import inspect

        parameters = inspect.signature(vw._compose_site_route_variables).parameters
        self.assertEqual(
            list(parameters), ["base_variables", "model_routing", "site_id", "site_registry", "config_authoritative", "overrides"]
        )
        self.assertIs(parameters["config_authoritative"].default, inspect.Parameter.empty)
        self.assertEqual(parameters["config_authoritative"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertEqual(parameters["overrides"].kind, inspect.Parameter.KEYWORD_ONLY)


class RealWorkspaceByteIdentityTests(unittest.TestCase):
    def test_dogfood_workspace_composes_the_base_map_for_every_agent(self) -> None:
        import yaml as _yaml

        config = _yaml.safe_load((REPO_ROOT / ".autoharness" / "config.yaml").read_text(encoding="utf-8"))
        manifest = _yaml.safe_load((REPO_ROOT / ".autoharness" / "harness-manifest.yaml").read_text(encoding="utf-8"))
        registry = mrs.build_site_registry(REPO_ROOT, REPO_ROOT, manifest, {})
        base = {"TIER_2_FAMILY": "x"}
        self.assertTrue(registry.sites)
        for site in registry.sites:
            composed = vw._compose_site_route_variables(
                base, config["model_routing"], site, registry, config_authoritative=True, overrides=None
            )
            self.assertIs(composed, base, site)


if __name__ == "__main__":
    unittest.main()
