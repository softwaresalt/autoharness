"""B6 (215-S, 208.008-T): verify-workspace catalog, binding, site, inert-key, unknown-key and alias checks.

Every check is existence-gated and registered only when the config declares a
`model_routing` mapping. The alias check is a thin wrapper over the shared
`model_routing_yaml.check_model_routing_yaml`; it carries no scanner of its own.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from _config_schema_contract import CURRENT_CONFIG_SCHEMA_VERSION, current_config_mirror_path

from autoharness import model_routing, model_routing_yaml
from autoharness import model_routing_sites as sites_module
from autoharness import verify_workspace as vw
from autoharness.cli import _report_has_failures
from autoharness.model_routing import MODEL_ROUTING_KNOWN_KEYS, SiteSpec
from autoharness.model_routing_sites import SiteRegistry

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKS = ("routing_catalog_integrity", "routing_inert_keys", "routing_unknown_keys", "routing_anchor_alias_free")

AGENT = "---\nname: Fixture\ndescription: A fixture\nmodel_family: fam\n---\n\n# Fixture\n"


def _template(*variables: str) -> str:
    keys = "\n".join(f'model_family: "{{{{{name}}}}}"' for name in variables)
    return f"---\nname: Fixture\ndescription: A fixture\n{keys}\n---\n\n# Fixture\n"


TIER_1 = _template("TIER_1_FAMILY")
TIER_2 = _template("TIER_2_FAMILY")
NO_TIER = "---\nname: Fixture\nmodel_family: fixed\n---\n\n# Fixture\n"
TWO_TIERS = _template("TIER_1_FAMILY", "TIER_3_FAMILY")

TIERS = {
    "tier1": {"model": "fam-1", "model_family": "fam-1"},
    "tier2": {"model": "fam-2", "model_family": "fam-2", "model_provider": "prov-2"},
    "tier3": {"model": "fam-3", "model_family": "fam-3"},
}
FAST = {"tier": "tier1", "model_family": "fam-fast"}


def _routing(**extra) -> dict:
    return {**{key: dict(value) for key, value in TIERS.items()}, **extra}


class Env:
    def __init__(self, root: Path) -> None:
        self.home = (root / "home").resolve()
        self.ws = (root / "ws").resolve()
        (self.home / "templates").mkdir(parents=True)
        (self.ws / ".autoharness").mkdir(parents=True)
        shutil.copytree(REPO_ROOT / "schemas", self.home / "schemas")
        self.artifacts: list[dict] = []
        self.community: list[dict] = []

    def write(self, base: Path, rel: str, text: str) -> Path:
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def rendered_agent(self, site: str, template_text: str) -> None:
        installed = f".github/agents/subagents/{site}.agent.md"
        template = f"agents/review/{site}.agent.md.tmpl"
        self.write(self.ws, installed, AGENT)
        self.write(self.home / "templates", template, template_text)
        self.artifacts.append({"path": installed, "template": template, "checksum": "", "primitive": 1})

    def community_agent(self, site: str, template_text: str) -> None:
        installed = f".github/agents/{site}.agent.md"
        template = f"templates/community/agents/{site}.agent.md.tmpl"
        self.write(self.ws, installed, AGENT)
        self.write(self.home, template, template_text)
        self.community.append({"installed_path": installed, "template_path": template, "template_id": site})

    def authored_agent(self, site: str) -> None:
        self.write(self.ws, f".github/agents/{site}.agent.md", AGENT)

    def config(self, version: str | None, model_routing_block: dict | None, raw: str | None = None) -> None:
        if raw is None:
            data: dict = {"schema_version": version}
            if model_routing_block is not None:
                data["model_routing"] = model_routing_block
            raw = yaml.safe_dump(data, sort_keys=False)
        self.write(self.ws, ".autoharness/config.yaml", raw)

    def verify(self) -> dict:
        manifest = {"artifacts": self.artifacts, "community_templates": self.community}
        self.write(self.ws, ".autoharness/harness-manifest.yaml", yaml.safe_dump(manifest, sort_keys=False))
        return vw.verify_workspace(self.ws, self.home, self.ws / ".autoharness" / "staging")


class RoutingCatalogCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.env = Env(Path(self._tmp.name))

    def run_checks(self, version: str | None, model_routing_block: dict | None, raw: str | None = None) -> dict:
        self.env.config(version, model_routing_block, raw)
        return self.env.verify()

    def check(self, report: dict, key: str) -> dict:
        self.assertIn(key, report["targeted_checks"])
        return report["targeted_checks"][key]

    def assert_passes(self, report: dict, *keys: str) -> None:
        for key in keys or CHECKS:
            check = self.check(report, key)
            self.assertTrue(check["ok"], (key, check))
            self.assertEqual(check["errors"], [], key)

    def errors(self, report: dict, key: str = "routing_catalog_integrity") -> list[str]:
        check = self.check(report, key)
        self.assertFalse(check["ok"], (key, check))
        return check["errors"]

    def assert_error(self, report: dict, fragment: str, key: str = "routing_catalog_integrity") -> None:
        errors = self.errors(report, key)
        self.assertTrue(any(fragment in error for error in errors), (fragment, errors))


class ValidAndAbsentTests(RoutingCatalogCase):
    def test_valid_catalog_and_binding_pass(self) -> None:
        self.env.rendered_agent("alpha", TIER_2)
        report = self.run_checks(
            CURRENT_CONFIG_SCHEMA_VERSION,
            _routing(routes={"fast": FAST}, bindings={"agent:alpha": {"route": "fast"}}),
        )
        self.assert_passes(report)

    def test_config_without_routes_bindings_or_unknown_keys_adds_only_passing_checks(self) -> None:
        report = self.run_checks(CURRENT_CONFIG_SCHEMA_VERSION, _routing())
        self.assert_passes(report)
        for key in CHECKS:
            self.assertEqual(report["targeted_checks"][key]["errors"], [])
        self.assertFalse([w for w in report["warnings"] if str(w.get("kind", "")).startswith("routing-")])

    def test_config_without_model_routing_registers_no_routing_check(self) -> None:
        report = self.run_checks(CURRENT_CONFIG_SCHEMA_VERSION, None)
        for key in CHECKS:
            self.assertNotIn(key, report["targeted_checks"])

    def test_registry_is_built_without_bindings_for_the_route_drift_check(self) -> None:
        self.env.authored_agent("custom")
        real = sites_module.build_site_registry
        with mock.patch.object(sites_module, "build_site_registry", side_effect=real) as build:
            self.run_checks(CURRENT_CONFIG_SCHEMA_VERSION, _routing(routes={"fast": FAST}))
        self.assertEqual(build.call_count, 1)

    def test_registry_is_built_exactly_once_per_run(self) -> None:
        self.env.rendered_agent("alpha", TIER_1)
        real = sites_module.build_site_registry
        with mock.patch.object(sites_module, "build_site_registry", side_effect=real) as build:
            self.run_checks(
                CURRENT_CONFIG_SCHEMA_VERSION,
                _routing(routes={"fast": FAST}, bindings={"agent:alpha": {"route": "fast"}}),
            )
        self.assertEqual(build.call_count, 1)


class CatalogAndBindingFailureTests(RoutingCatalogCase):
    def bound(self, **bindings) -> dict:
        return self.run_checks(
            CURRENT_CONFIG_SCHEMA_VERSION, _routing(routes={"fast": FAST}, bindings=bindings)
        )

    def test_unresolved_reference_fails(self) -> None:
        self.env.rendered_agent("alpha", TIER_1)
        self.assert_error(self.bound(**{"agent:alpha": {"route": "nope"}}), "ROUTING_REF_UNRESOLVED: nope")

    def test_unknown_site_fails(self) -> None:
        self.assert_error(self.bound(**{"agent:ghost": {"route": "fast"}}), "ROUTING_UNKNOWN_SITE: agent:ghost")

    def test_non_agent_binding_key_is_an_unknown_site(self) -> None:
        self.assert_error(self.bound(**{"bogus": {"route": "fast"}}), "ROUTING_UNKNOWN_SITE: bogus")

    def test_pipeline_site_binding_fails(self) -> None:
        for key in ("agent:_stage", "agent:_ship", "agent:_orchestrator", "stage", "orchestrator"):
            with self.subTest(key=key):
                self.assert_error(self.bound(**{key: {"route": "fast"}}), f"ROUTING_BINDING_ON_PIPELINE_SITE: {key}")

    def test_tier_named_route_fails_even_when_unreferenced(self) -> None:
        for name in ("tier1", "tier3", "default"):
            with self.subTest(name=name):
                report = self.run_checks(
                    CURRENT_CONFIG_SCHEMA_VERSION, _routing(routes={name: {"tier": "tier1"}})
                )
                self.assert_error(report, f"ROUTING_CATALOG_INVALID: {name}: reserved route name")

    def test_malformed_catalog_entries_fail(self) -> None:
        for entry, reason in (("oops", "not a mapping"), ({}, "missing tier"), ({"tier": "tier9"}, "invalid tier")):
            with self.subTest(entry=entry):
                report = self.run_checks(CURRENT_CONFIG_SCHEMA_VERSION, _routing(routes={"odd": entry}))
                self.assert_error(report, f"ROUTING_CATALOG_INVALID: odd: {reason}")

    def test_non_mapping_routes_and_bindings_fail_without_raising(self) -> None:
        report = self.run_checks(CURRENT_CONFIG_SCHEMA_VERSION, _routing(routes=["x"], bindings="y"))
        self.assert_error(report, "ROUTING_CATALOG_INVALID: routes: not a mapping")
        self.assert_error(report, "ROUTING_CATALOG_INVALID: bindings: not a mapping")

    def test_binding_to_workspace_authored_agent_is_a_known_site(self) -> None:
        self.env.authored_agent("custom")
        self.assert_passes(self.bound(**{"agent:custom": {"route": "fast"}}), "routing_catalog_integrity")

    def test_binding_to_managed_community_agent_with_resolvable_tier_passes(self) -> None:
        self.env.community_agent("beta", TIER_2)
        self.assert_passes(self.bound(**{"agent:beta": {"route": "fast"}}), "routing_catalog_integrity")

    def test_binding_to_manifest_orphan_names_the_missing_file(self) -> None:
        self.env.rendered_agent("alpha", TIER_1)
        (self.env.ws / ".github/agents/subagents/alpha.agent.md").unlink()
        report = self.bound(**{"agent:alpha": {"route": "fast"}})
        self.assert_error(report, "ROUTING_UNKNOWN_SITE: agent:alpha")
        self.assert_error(report, ".github/agents/subagents/alpha.agent.md")

    def test_binding_to_duplicate_site_id_names_the_cause(self) -> None:
        self.env.authored_agent("dup")
        self.env.write(self.env.ws, ".github/agents/subagents/dup.agent.md", AGENT)
        report = self.bound(**{"agent:dup": {"route": "fast"}})
        self.assert_error(report, "ROUTING_UNKNOWN_SITE: agent:dup")
        self.assert_error(report, "duplicate")

    def test_registry_build_failure_fails_closed(self) -> None:
        self.env.authored_agent("custom")
        with mock.patch.object(sites_module, "build_site_registry", side_effect=OSError("boom")):
            report = self.bound(**{"agent:custom": {"route": "fast"}})
        self.assert_error(report, "ROUTING_SITE_REGISTRY_UNAVAILABLE")


class UnresolvedDefaultBindingTests(RoutingCatalogCase):
    REASONS = {
        "no-tier-placeholder": NO_TIER,
        "ambiguous-tier": TWO_TIERS,
        "template-unreadable": TIER_1,
    }

    def _setup(self, kind: str, template_text: str) -> None:
        (self.env.rendered_agent if kind == "rendered" else self.env.community_agent)("gamma", template_text)

    def _bind(self, extra_routing: dict | None = None) -> dict:
        return self.run_checks(
            CURRENT_CONFIG_SCHEMA_VERSION,
            _routing(routes={"fast": FAST}, bindings={"agent:gamma": {"route": "fast"}}, **(extra_routing or {})),
        )

    def test_binding_on_unresolved_default_fails_for_both_classes_and_each_reason(self) -> None:
        for kind in ("rendered", "community"):
            for reason, template_text in self.REASONS.items():
                with self.subTest(kind=kind, reason=reason):
                    self.setUp()
                    self._setup(kind, template_text)
                    if reason == "template-unreadable":
                        with mock.patch.object(sites_module, "_read_template_bytes", side_effect=OSError("denied")):
                            report = self._bind()
                    else:
                        report = self._bind()
                    self.assert_error(report, f"ROUTING_BINDING_UNRESOLVED_SITE: gamma: {reason}")

    def test_template_path_unusable_for_community_class(self) -> None:
        self.env.community_agent("gamma", TIER_1)
        (self.env.home / "templates/community/agents/gamma.agent.md.tmpl").unlink()
        self.assert_error(self._bind(), "ROUTING_BINDING_UNRESOLVED_SITE: gamma: template-path-unusable")

    def test_template_path_unusable_for_rendered_class(self) -> None:
        self.env.rendered_agent("gamma", TIER_1)
        registry = SiteRegistry(
            sites={"gamma": SiteSpec("gamma", None, True)},
            orphans=(),
            conflicts=(),
            unresolved={"gamma": "template-path-unusable"},
        )
        with mock.patch.object(sites_module, "build_site_registry", return_value=registry):
            report = self._bind()
        self.assert_error(report, "ROUTING_BINDING_UNRESOLVED_SITE: gamma: template-path-unusable")

    def test_bound_site_whose_installed_frontmatter_equals_the_route_still_fails(self) -> None:
        self.env.rendered_agent("gamma", NO_TIER)
        self.env.write(
            self.env.ws,
            ".github/agents/subagents/gamma.agent.md",
            "---\nname: Fixture\ndescription: x\nmodel_family: fam-fast\n---\n\n# Fixture\n",
        )
        self.assert_error(self._bind(), "ROUTING_BINDING_UNRESOLVED_SITE: gamma: no-tier-placeholder")

    def test_unbound_unresolved_site_is_known_and_adds_no_failure(self) -> None:
        self.env.rendered_agent("gamma", NO_TIER)
        self.env.authored_agent("custom")
        report = self.run_checks(
            CURRENT_CONFIG_SCHEMA_VERSION,
            _routing(routes={"fast": FAST}, bindings={"agent:custom": {"route": "fast"}}),
        )
        self.assert_passes(report, "routing_catalog_integrity")
        # The unresolved site is a known id: binding it is rejected for the reason, not as unknown.
        report = self._bind()
        self.assertFalse(any("ROUTING_UNKNOWN_SITE" in e for e in self.errors(report)))


class InertAndUnknownKeyTests(RoutingCatalogCase):
    def test_routes_in_a_1_1_0_config_fail_once(self) -> None:
        report = self.run_checks("1.1.0", _routing(routes={"fast": FAST}))
        self.assert_error(report, "ROUTING_KEYS_REQUIRE_1_2_0: routes", "routing_inert_keys")
        self.assertTrue(report["targeted_checks"]["routing_unknown_keys"]["ok"])
        self.assertEqual(report["targeted_checks"]["routing_unknown_keys"]["warnings"], [])
        self.assertFalse([w for w in report["warnings"] if w.get("kind") == "routing-unknown-key"])

    def test_bindings_in_a_1_1_0_config_fail(self) -> None:
        self.env.authored_agent("custom")
        report = self.run_checks("1.1.0", _routing(bindings={"agent:custom": {"route": "tier1"}}))
        self.assert_error(report, "ROUTING_KEYS_REQUIRE_1_2_0: bindings", "routing_inert_keys")

    def test_routes_in_a_1_2_0_config_pass_the_inert_check(self) -> None:
        report = self.run_checks(CURRENT_CONFIG_SCHEMA_VERSION, _routing(routes={"fast": FAST}))
        self.assert_passes(report, "routing_inert_keys")

    def test_unknown_key_in_a_1_2_0_config_fails_with_the_key_and_allowed_set(self) -> None:
        with mock.patch.object(vw, "_schema_errors", return_value=[]):
            report = self.run_checks("1.2.0", _routing(routez={"x": 1}))
        errors = self.errors(report, "routing_unknown_keys")
        self.assertEqual(len(errors), 1)
        self.assertIn("ROUTING_UNKNOWN_KEY: routez", errors[0])
        for allowed in sorted(MODEL_ROUTING_KNOWN_KEYS):
            self.assertIn(allowed, errors[0])
        self.assertEqual(report["strict_schema_blockers"], [])
        self.assertTrue(_report_has_failures(report))
        self.assert_passes(report, "routing_catalog_integrity", "routing_inert_keys", "routing_anchor_alias_free")

    def test_inert_subagents_block_in_a_1_2_0_config_fails(self) -> None:
        with mock.patch.object(vw, "_schema_errors", return_value=[]):
            report = self.run_checks("1.2.0", _routing(subagents={"alpha": {"model_family": "x"}}))
        self.assert_error(report, "ROUTING_UNKNOWN_KEY: subagents", "routing_unknown_keys")

    def test_unknown_keys_in_a_1_1_0_config_are_one_advisory_each(self) -> None:
        report = self.run_checks("1.1.0", _routing(subagents={"alpha": {}}, routez={"x": 1}))
        check = self.check(report, "routing_unknown_keys")
        self.assertTrue(check["ok"])
        self.assertEqual(check["errors"], [])
        self.assertEqual(len(check["warnings"]), 2)
        advisories = [w for w in report["warnings"] if w.get("kind") == "routing-unknown-key"]
        self.assertEqual(len(advisories), 2)
        self.assertEqual({w["severity"] for w in advisories}, {"warning"})
        self.assertEqual({w["rule"] for w in advisories}, {"ROUTING_UNKNOWN_KEY:routez", "ROUTING_UNKNOWN_KEY:subagents"})
        for warning in advisories:
            self.assertIn("ROUTING_UNKNOWN_KEY", warning["message"])
        self.assertEqual([b for b in report["strict_schema_blockers"] if b["path"].endswith("config.yaml")], [])

    def test_unknown_key_check_never_mutates_the_config(self) -> None:
        block = _routing(routez={"x": 1})
        snapshot = json.dumps(block, sort_keys=True)
        vw_config = {"schema_version": "1.1.0", "model_routing": block}
        report: dict = {"targeted_checks": {}, "warnings": []}
        vw._add_model_routing_catalog_checks(report, vw_config, self.env.ws / ".autoharness/config.yaml", None, None)
        self.assertEqual(json.dumps(block, sort_keys=True), snapshot)

    def test_known_key_set_matches_the_current_schema_mirror(self) -> None:
        schema = json.loads(current_config_mirror_path().read_text(encoding="utf-8"))
        properties = schema["properties"]["model_routing"]["properties"]
        self.assertEqual(set(properties), set(model_routing.MODEL_ROUTING_KNOWN_KEYS))


BASELINE_CONFIG = """\
schema_version: "{version}"
model_routing:
  tier1: &t1
    model_family: fam-1
  tier2:
    model_family: fam-2
  tier3: *t1
"""

ALIAS_ONLY_CONFIG = """\
schema_version: "{version}"
shared: &shared
  model_family: fam-1
model_routing:
  tier1: *shared
  tier2:
    model_family: fam-2
"""


class AnchorAliasTests(RoutingCatalogCase):
    def test_baseline_block_with_anchors_fails_at_1_2_0(self) -> None:
        with mock.patch.object(vw, "_schema_errors", return_value=[]):
            report = self.run_checks(None, None, BASELINE_CONFIG.format(version="1.2.0"))
        self.assert_error(report, "ROUTING_ANCHOR_UNSUPPORTED", "routing_anchor_alias_free")

    def test_baseline_block_warns_at_1_1_0(self) -> None:
        report = self.run_checks(None, None, BASELINE_CONFIG.format(version="1.1.0"))
        check = self.check(report, "routing_anchor_alias_free")
        self.assertTrue(check["ok"])
        self.assertEqual(check["errors"], [])
        self.assertTrue(check["warnings"])
        advisories = [w for w in report["warnings"] if w.get("kind") == "routing-anchor-unsupported"]
        self.assertEqual(len(advisories), len(check["warnings"]))
        self.assertTrue(all("ROUTING_ANCHOR_UNSUPPORTED" in w["message"] for w in advisories))

    def test_alias_under_model_routing_fails_at_1_2_0_and_warns_at_1_1_0(self) -> None:
        with mock.patch.object(vw, "_schema_errors", return_value=[]):
            report = self.run_checks(None, None, ALIAS_ONLY_CONFIG.format(version="1.2.0"))
        self.assert_error(report, "ROUTING_ANCHOR_UNSUPPORTED: alias", "routing_anchor_alias_free")
        report = self.run_checks(None, None, ALIAS_ONLY_CONFIG.format(version="1.1.0"))
        self.assertTrue(self.check(report, "routing_anchor_alias_free")["ok"])
        self.assertTrue(self.check(report, "routing_anchor_alias_free")["warnings"])

    def test_alias_check_delegates_to_the_shared_function(self) -> None:
        sentinel = model_routing_yaml.YamlGuardResult(("ROUTING_ANCHOR_UNSUPPORTED: sentinel",), (), None)
        with mock.patch.object(model_routing_yaml, "check_model_routing_yaml", return_value=sentinel) as guard:
            report = self.run_checks(CURRENT_CONFIG_SCHEMA_VERSION, _routing())
        guard.assert_called_once()
        raw_text, version = guard.call_args.args
        self.assertIn("model_routing", raw_text)
        self.assertEqual(version, CURRENT_CONFIG_SCHEMA_VERSION)
        self.assert_error(report, "ROUTING_ANCHOR_UNSUPPORTED: sentinel", "routing_anchor_alias_free")

    def test_parse_error_is_reported_not_raised(self) -> None:
        guard = model_routing_yaml.YamlGuardResult((), (), "mapping values are not allowed here")
        with mock.patch.object(model_routing_yaml, "check_model_routing_yaml", return_value=guard):
            report = self.run_checks(CURRENT_CONFIG_SCHEMA_VERSION, _routing())
        self.assert_error(report, "mapping values are not allowed here", "routing_anchor_alias_free")

    def test_clean_config_passes_the_alias_check(self) -> None:
        self.assert_passes(self.run_checks(CURRENT_CONFIG_SCHEMA_VERSION, _routing()), "routing_anchor_alias_free")

    def test_verify_workspace_carries_no_yaml_scanner_of_its_own(self) -> None:
        source = (REPO_ROOT / "src" / "autoharness" / "verify_workspace.py").read_text(encoding="utf-8")
        for needle in ("yaml.parse", "yaml.scan", "AliasEvent", "ScalarEvent", "yaml.compose"):
            self.assertNotIn(needle, source)
        self.assertIsNotNone(re.search(r"model_routing_yaml\.check_model_routing_yaml\(", source))


class RealWorkspaceTests(unittest.TestCase):
    def test_dogfood_workspace_gains_only_passing_routing_checks(self) -> None:
        with tempfile.TemporaryDirectory() as staging:
            report = vw.verify_workspace(REPO_ROOT, REPO_ROOT, Path(staging))
        for key in CHECKS:
            self.assertIn(key, report["targeted_checks"])
            self.assertTrue(report["targeted_checks"][key]["ok"], key)
        self.assertFalse([w for w in report["warnings"] if str(w.get("kind", "")).startswith("routing-")])


if __name__ == "__main__":
    unittest.main()
