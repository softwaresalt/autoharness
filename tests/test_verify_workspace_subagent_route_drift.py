"""B7 (215-S, 208.009-T): verify-workspace installed subagent route drift.

The expectation is read through B6a's `_expected_site_route` (the renderer's own composed
variables), never from raw resolver output. The opt-in is a non-empty `bindings` block.
"""

from __future__ import annotations

import itertools
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml

from autoharness import model_routing_sites as mrs
from autoharness import verify_workspace as vw
from test_verify_workspace_site_composition import NO_TIER, ROUTE_FIELDS, Fixture, parse_route, routing

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK = "subagent_route_drift"

DEFAULT_TIER2 = {
    "model_family": "f2",
    "model_provider": "p2",
    "reasoning_effort": "e2",
    "context_tier": "long_context",
}
BOUND_FAST = {"model_family": "f-fast", "model_provider": "", "reasoning_effort": "", "context_tier": "default"}
STALE = {"model_family": "stale", "model_provider": "", "reasoning_effort": "", "context_tier": "default"}


def installed_text(route: dict[str, str]) -> str:
    lines = ["---", "name: Fixture", 'description: "A fixture"', "max_subagent_tier: 2"]
    lines += [f'{field}: "{route[field]}"' for field in ROUTE_FIELDS]
    lines += ["subagent_depth: 0", "---", "", "# Fixture", ""]
    return "\n".join(lines)


class DriftFixture(Fixture):
    variables_used: dict[str, str] | None = None

    @property
    def manifest(self) -> dict:
        manifest = super().manifest
        if self.variables_used is not None:
            manifest["variables_used"] = self.variables_used
        return manifest

    def install(self, site: str, route: dict[str, str]) -> None:
        self._write(self.ws, self.rel(site), installed_text(route))

    def write_bare_config(self) -> None:
        self.config = {"schema_version": "1.2.0"}
        self._write(self.ws, ".autoharness/config.yaml", yaml.safe_dump(self.config, sort_keys=False))
        self._write(self.ws, ".autoharness/harness-manifest.yaml", yaml.safe_dump(self.manifest, sort_keys=False))


class DriftCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.fx = DriftFixture(Path(self._tmp.name))

    def verify(self) -> dict:
        return vw.verify_workspace(self.fx.ws, self.fx.home, self.fx.staging)

    def check(self, report: dict | None = None) -> dict:
        report = report or self.verify()
        self.assertIn(CHECK, report["targeted_checks"])
        return report["targeted_checks"][CHECK]

    def proposals(self, report: dict, site: str | None = None) -> list[dict]:
        found = [p for p in report["migration_proposals"] if p.get("action") == "refresh-route-frontmatter"]
        return [p for p in found if site is None or p["path"].endswith(f"/{site}.agent.md")]

    def declare_bindings_elsewhere(self) -> dict:
        """A bound, matching workspace-authored agent: declares bindings without touching `alpha`."""
        self.fx.add("other", "authored")
        self.fx.install("other", BOUND_FAST)
        return {"agent:other": {"route": "fast"}}


class MatrixTests(DriftCase):
    def test_class_by_binding_by_match_by_opt_in(self) -> None:
        for kind, bound, matches, declares in itertools.product(
            ("rendered", "community"), (False, True), (True, False), (True, False)
        ):
            if bound and not declares:
                continue  # a bound site implies the workspace declares bindings
            with self.subTest(kind=kind, bound=bound, matches=matches, declares=declares):
                self.setUp()
                self.fx.add("alpha", kind)
                bindings: dict[str, Any] = {}
                if bound:
                    bindings["agent:alpha"] = {"route": "fast"}
                elif declares:
                    bindings.update(self.declare_bindings_elsewhere())
                self.fx.write_config(routing(bindings=bindings or None))
                expected = BOUND_FAST if bound else DEFAULT_TIER2
                self.fx.install("alpha", expected if matches else STALE)
                report = self.verify()
                check = self.check(report)
                self.assertIn("alpha", check["compared"])
                self.assertNotIn("alpha", check["skipped"])
                if matches:
                    self.assertTrue(check["ok"], check)
                    self.assertEqual(check["errors"], [])
                    self.assertNotIn("alpha", check["drifted"])
                    self.assertEqual(self.proposals(report, "alpha"), [])
                    continue
                self.assertIn("alpha", check["drifted"])
                self.assertEqual(len(self.proposals(report, "alpha")), 1)
                if declares:
                    self.assertFalse(check["ok"])
                    self.assertTrue(any("SUBAGENT_ROUTE_DRIFT" in e and "alpha" in e for e in check["errors"]))
                else:
                    self.assertTrue(check["ok"], check)
                    self.assertEqual(check["errors"], [])
                    self.assertEqual(len(check["info"]), 1)
                    self.assertIn("alpha", check["info"][0])


class WorkspaceAuthoredTests(DriftCase):
    def test_bound_authored_drift_warns_and_does_not_change_ok(self) -> None:
        self.fx.add("custom", "authored")
        self.fx.write_config(routing(bindings={"agent:custom": {"route": "fast"}}))
        self.fx.install("custom", STALE)
        report = self.verify()
        check = self.check(report)
        self.assertTrue(check["ok"], check)
        self.assertEqual(check["errors"], [])
        warnings = [w for w in report["warnings"] if w.get("kind") == "subagent-route-drift"]
        self.assertEqual(len(warnings), 1)
        self.assertTrue(warnings[0]["path"].endswith("custom.agent.md"))
        self.assertEqual(len(self.proposals(report, "custom")), 1)
        self.fx.install("custom", BOUND_FAST)
        report = self.verify()
        self.assertEqual([w for w in report["warnings"] if w.get("kind") == "subagent-route-drift"], [])
        self.assertIn("custom", self.check(report)["compared"])

    def test_unbound_authored_agent_is_skipped(self) -> None:
        self.fx.add("custom", "authored")
        self.fx.add("alpha", "community")
        self.fx.install("custom", STALE)
        self.fx.install("alpha", DEFAULT_TIER2)
        self.fx.write_config(routing())
        report = self.verify()
        check = self.check(report)
        self.assertIn("custom", check["skipped"])
        self.assertNotIn("custom", check["compared"])
        self.assertEqual([w for w in report["warnings"] if w.get("kind") == "subagent-route-drift"], [])
        self.assertEqual(self.proposals(report, "custom"), [])


class ExplicitOverrideTests(DriftCase):
    OVERRIDDEN_BOUND = {**BOUND_FAST, "model_family": "ov-fam"}
    OVERRIDDEN_UNBOUND = {**DEFAULT_TIER2, "model_family": "ov-fam"}

    def test_bound_agent_with_an_override(self) -> None:
        for kind in ("rendered", "community"):
            with self.subTest(kind=kind):
                self.setUp()
                self.fx.add("alpha", kind)
                self.fx.write_config(
                    routing(bindings={"agent:alpha": {"route": "fast"}}), {"TIER_2_FAMILY": "ov-fam"}
                )
                self.fx.install("alpha", self.OVERRIDDEN_BOUND)
                self.assertTrue(self.check()["ok"])
                self.fx.install("alpha", BOUND_FAST)  # the raw binding value, override ignored
                check = self.check()
                self.assertFalse(check["ok"])
                self.assertIn("alpha", check["drifted"])
                self.fx.install("alpha", {**self.OVERRIDDEN_BOUND, "reasoning_effort": "high"})
                self.assertFalse(self.check()["ok"])

    def test_unbound_agent_rendered_with_an_override_is_not_false_drift(self) -> None:
        for kind in ("rendered", "community"):
            with self.subTest(kind=kind):
                self.setUp()
                self.fx.add("alpha", kind)
                self.fx.write_config(
                    routing(bindings=self.declare_bindings_elsewhere()), {"TIER_2_FAMILY": "ov-fam"}
                )
                self.fx.install("alpha", self.OVERRIDDEN_UNBOUND)
                check = self.check()
                self.assertTrue(check["ok"], check)
                self.assertIn("alpha", check["compared"])
                self.fx.install("alpha", DEFAULT_TIER2)  # ignores the override: real drift
                self.assertFalse(self.check()["ok"])
                self.fx.install("alpha", {**self.OVERRIDDEN_UNBOUND, "model_provider": "wrong"})
                self.assertFalse(self.check()["ok"])


class BoundBranchTests(DriftCase):
    def test_bound_tier_with_empty_fields_does_not_inherit_the_default_tier(self) -> None:
        for kind in ("rendered", "community"):
            with self.subTest(kind=kind):
                self.setUp()
                self.fx.add("alpha", kind)  # default tier2 supplies p2 / e2 / long_context
                self.fx.write_config(routing(bindings={"agent:alpha": {"route": "fast"}}))
                self.fx.install("alpha", BOUND_FAST)
                self.assertTrue(self.check()["ok"])
                self.fx.install("alpha", {**BOUND_FAST, **{k: v for k, v in DEFAULT_TIER2.items() if k != "model_family"}})
                check = self.check()
                self.assertFalse(check["ok"])
                self.assertIn("alpha", check["drifted"])


class UnresolvedDefaultTests(DriftCase):
    def add_unresolved(self, kind: str, reason: str) -> None:
        if reason == "no-tier-placeholder":
            self.fx.add("alpha", kind, NO_TIER)
        else:  # community template_path names a missing file
            self.fx.add("alpha", "community")
            (self.fx.home / "templates" / "community" / "agents" / "alpha.agent.md.tmpl").unlink()

    CASES = (("community", "no-tier-placeholder"), ("rendered", "no-tier-placeholder"), ("community", "template-path-unusable"))

    def test_unbound_with_bindings_declared_fails_naming_the_reason(self) -> None:
        for kind, reason in self.CASES:
            with self.subTest(kind=kind, reason=reason):
                self.setUp()
                self.add_unresolved(kind, reason)
                self.fx.write_config(routing(bindings=self.declare_bindings_elsewhere()))
                self.fx.install("alpha", STALE)
                report = self.verify()
                check = self.check(report)
                self.assertFalse(check["ok"])
                self.assertIn(f"ROUTING_SITE_DEFAULT_UNRESOLVED: alpha: {reason}", check["errors"])
                self.assertNotIn("alpha", check["compared"])
                self.assertEqual(self.proposals(report, "alpha"), [])

    def test_unbound_without_bindings_is_one_info_line(self) -> None:
        for kind, reason in self.CASES:
            with self.subTest(kind=kind, reason=reason):
                self.setUp()
                self.add_unresolved(kind, reason)
                self.fx.write_config(routing())
                self.fx.install("alpha", STALE)
                report = self.verify()
                check = self.check(report)
                self.assertTrue(check["ok"], check)
                self.assertEqual(check["errors"], [])
                self.assertEqual(len(check["info"]), 1)
                self.assertIn("ROUTING_SITE_DEFAULT_UNRESOLVED", check["info"][0])
                self.assertIn("alpha", check["info"][0])
                self.assertEqual(self.proposals(report, "alpha"), [])

    def test_bound_fails_even_when_the_frontmatter_equals_the_binding(self) -> None:
        for kind, reason in self.CASES:
            with self.subTest(kind=kind, reason=reason):
                self.setUp()
                self.add_unresolved(kind, reason)
                self.fx.write_config(routing(bindings={"agent:alpha": {"route": "fast"}}))
                self.fx.install("alpha", BOUND_FAST)
                report = self.verify()
                check = self.check(report)
                self.assertFalse(check["ok"])
                self.assertIn(f"ROUTING_BINDING_UNRESOLVED_SITE: alpha: {reason}", check["errors"])
                self.assertNotIn("alpha", check["compared"])
                self.assertNotIn("alpha", check["drifted"])
                self.assertEqual(self.proposals(report, "alpha"), [])

    def test_bound_site_whose_binding_does_not_resolve_reports_the_resolver_code(self) -> None:
        for kind in ("rendered", "community"):
            with self.subTest(kind=kind):
                self.setUp()
                self.fx.add("alpha", kind)
                self.fx.write_config(routing(bindings={"agent:alpha": {"route": "nope"}}))
                self.fx.install("alpha", DEFAULT_TIER2)  # matches the unbound tier: still never compared
                report = self.verify()
                check = self.check(report)
                self.assertFalse(check["ok"])
                self.assertTrue(any("ROUTING_REF_UNRESOLVED" in error for error in check["errors"]), check)
                self.assertNotIn("alpha", check["compared"])
                self.assertEqual(self.proposals(report, "alpha"), [])


class ReinstallRoundTripTests(DriftCase):
    def test_the_render_output_passes_and_one_changed_field_fails(self) -> None:
        for kind, overrides in itertools.product(("rendered", "community"), (None, {"TIER_2_FAMILY": "ov-fam"})):
            with self.subTest(kind=kind, overrides=overrides):
                self.setUp()
                self.fx.add("alpha", kind)
                self.fx.write_config(routing(bindings={"agent:alpha": {"route": "fast"}}), overrides)
                rendered = self.fx.render("alpha")
                self.fx._write(self.fx.ws, self.fx.rel("alpha"), rendered.decode("utf-8"))
                check = self.check()
                self.assertTrue(check["ok"], check)
                self.assertIn("alpha", check["compared"])
                for field in ROUTE_FIELDS:
                    with self.subTest(changed=field):
                        changed = dict(parse_route(rendered))
                        changed[field] = changed[field] + "-x"
                        self.fx.install("alpha", changed)
                        self.assertFalse(self.check()["ok"])


class ProposalAndOptInTests(DriftCase):
    def test_a_proposal_is_emitted_for_each_drift(self) -> None:
        for site in ("a1", "a2", "a3"):
            self.fx.add(site, "community")
            self.fx.install(site, STALE)
        self.fx.add("fine", "rendered")
        self.fx.install("fine", DEFAULT_TIER2)
        self.fx.write_config(routing(bindings=self.declare_bindings_elsewhere()))
        report = self.verify()
        proposals = self.proposals(report)
        self.assertEqual(sorted(Path(p["path"]).name for p in proposals), ["a1.agent.md", "a2.agent.md", "a3.agent.md"])
        for proposal in proposals:
            self.assertEqual(proposal["contract"], "model-routing")
            self.assertIn("model_family", proposal["changed_fields"])
            self.assertEqual(proposal["evidence"]["expected"], DEFAULT_TIER2)

    def test_opt_in_is_bindings_non_empty_in_both_directions(self) -> None:
        self.fx.add("alpha", "community")
        self.fx.install("alpha", STALE)
        for block, ok in ((routing(), True), (routing(bindings={}), True)):
            self.fx.write_config(block)
            self.assertEqual(self.check()["ok"], ok, block)
        self.fx.write_config(routing(bindings=self.declare_bindings_elsewhere()))
        self.assertFalse(self.check()["ok"])

    def test_schema_version_is_not_the_opt_in(self) -> None:
        self.fx.add("alpha", "community")
        self.fx.install("alpha", STALE)
        self.fx.write_config(routing())
        self.assertEqual(self.fx.config["schema_version"], "1.2.0")
        self.assertTrue(self.check()["ok"])

    def test_info_output_is_bounded_to_a_count_and_twenty_ids(self) -> None:
        for number in range(25):
            site = f"agent{number:02d}"
            self.fx.add(site, "community")
            self.fx.install(site, STALE)
        self.fx.write_config(routing())
        check = self.check()
        self.assertTrue(check["ok"])
        self.assertEqual(len(check["info"]), 1)
        line = check["info"][0]
        self.assertIn("25", line)
        self.assertEqual(len(re.findall(r"agent\d\d", line)), 20)
        self.assertEqual(len(check["drifted"]), 25)


class NonAuthoritativeConfigTests(DriftCase):
    def test_the_expectation_is_the_manifest_first_base_map_the_render_uses(self) -> None:
        self.fx.variables_used = {"TIER_2_FAMILY": "man-fam"}
        self.fx.add("alpha", "rendered")
        self.fx.write_bare_config()
        rendered = self.fx.staged_bytes("alpha")
        self.assertEqual(parse_route(rendered)["model_family"], "man-fam")
        self.fx._write(self.fx.ws, self.fx.rel("alpha"), rendered.decode("utf-8"))
        check = self.check()
        self.assertIn("alpha", check["compared"])
        self.assertEqual(check["drifted"], [])
        self.assertEqual(
            vw._expected_site_route(
                self.fx.variables(False), {}, "alpha", self.fx.registry(), config_authoritative=False, overrides=None
            ),
            parse_route(rendered),
        )
        self.fx.install("alpha", {**parse_route(rendered), "model_family": "f2"})
        self.assertIn("alpha", self.check()["drifted"])


class SourceContractTests(unittest.TestCase):
    SOURCE = (REPO_ROOT / "src" / "autoharness" / "verify_workspace.py").read_text(encoding="utf-8")

    def body(self, name: str) -> str:
        match = re.search(rf"^def {name}\(.*?(?=^(?:def |class |[A-Za-z_#])|\Z)", self.SOURCE[self.SOURCE.index(f"def {name}("):], re.DOTALL | re.MULTILINE)
        self.assertTrue(match, name)
        return match.group(0)

    def test_expectation_comes_from_the_shared_function_only(self) -> None:
        body = self.body("_add_subagent_route_drift_check")
        self.assertIn("_expected_site_route(", body)
        for forbidden in ("TIER_", "_site_tier_variable_names", "_compose_site_route_variables", "resolve_site("):
            self.assertNotIn(forbidden, re.sub(r'""".*?"""', "", body, flags=re.DOTALL), forbidden)

    def test_registry_is_built_once_per_run_whatever_the_bindings(self) -> None:
        main = self.body("verify_workspace")
        self.assertEqual(len(re.findall(r"_build_verify_site_registry\(", main)), 1)
        self.assertIn("_add_subagent_route_drift_check(", main)


class RegistryBuildTests(DriftCase):
    def test_registry_is_built_once_without_bindings(self) -> None:
        from unittest import mock

        self.fx.add("alpha", "community")
        self.fx.install("alpha", DEFAULT_TIER2)
        self.fx.write_config(routing())
        with mock.patch.object(mrs, "build_site_registry", side_effect=mrs.build_site_registry) as build:
            self.verify()
        self.assertEqual(build.call_count, 1)

    def test_registry_build_failure_fails_closed_only_with_bindings(self) -> None:
        from unittest import mock

        self.fx.add("alpha", "community")
        self.fx.install("alpha", DEFAULT_TIER2)
        with mock.patch.object(mrs, "build_site_registry", side_effect=OSError("boom")):
            self.fx.write_config(routing())
            check = self.check()
            self.assertTrue(check["ok"])
            self.assertEqual(len(check["info"]), 1)
            self.fx.write_config(routing(bindings={"agent:alpha": {"route": "fast"}}))
            check = self.check()
            self.assertFalse(check["ok"])
            self.assertTrue(any("ROUTING_SITE_REGISTRY_UNAVAILABLE" in error for error in check["errors"]))


class DriftTargetFilterTests(DriftCase):
    def test_symlinked_duplicate_sorting_first_is_not_the_drift_target(self) -> None:
        self.fx.add("alpha", "rendered")
        self.fx.install("alpha", STALE)
        link = self.fx.ws / ".github" / "agents" / "alpha.agent.md"
        try:
            os.symlink(self.fx.ws / self.fx.rel("alpha"), link)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        self.fx.write_config(routing(bindings=self.declare_bindings_elsewhere()))
        report = self.verify()
        check = self.check(report)
        self.assertEqual(check["drift"]["alpha"]["path"], self.fx.rel("alpha"))
        self.assertEqual([p["path"] for p in self.proposals(report, "alpha")], [self.fx.rel("alpha")])


class DriftReportJsonSafetyTests(DriftCase):
    def test_non_string_installed_value_is_drift_and_report_serializes(self) -> None:
        self.fx.add("alpha", "community")
        self.fx.write_config(routing(bindings=self.declare_bindings_elsewhere()))
        text = installed_text(DEFAULT_TIER2).replace('model_family: "f2"', "model_family: 2026-01-01")
        self.fx._write(self.fx.ws, self.fx.rel("alpha"), text)
        report = self.verify()
        check = self.check(report)
        self.assertIn("alpha", check["drifted"])
        self.assertFalse(check["ok"])
        json.dumps(report)


class DogfoodWorkspaceTests(unittest.TestCase):
    def test_this_workspace_stays_ok_and_reports_drift_as_info(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = vw.verify_workspace(REPO_ROOT, REPO_ROOT, Path(tmp) / "staging")
        check = report["targeted_checks"][CHECK]
        self.assertTrue(check["ok"], check)
        self.assertEqual(check["errors"], [])
        self.assertEqual(len(check["info"]), 1, check["info"])
        self.assertEqual(len(check["drifted"]), 13, check["drifted"])


if __name__ == "__main__":
    unittest.main()
