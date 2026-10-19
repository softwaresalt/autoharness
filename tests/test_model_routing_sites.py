"""B2 (215-S): the read-only site registry builder and the template tier sync test."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from autoharness import model_routing_sites as sites_module
from autoharness.model_routing import SiteSpec
from autoharness.model_routing_sites import SiteRegistry, build_site_registry, derive_template_default_tier

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_AND_SOURCE = ("_orchestrator", "_stage", "_ship", "auto-tune", "auto-mergeinstall")


def _frontmatter(*variables: str, body: str = "") -> str:
    keys = "\n".join(f'model_family: "{{{{{name}}}}}"' for name in variables)
    return f"---\nname: Fixture\n{keys}\n---\n\n# Fixture\n{body}\n"


TIER_1 = _frontmatter("TIER_1_FAMILY")
TIER_2 = _frontmatter("TIER_2_FAMILY")
NO_TIER = "---\nname: Fixture\nmodel_family: fixed\n---\n\n# Fixture\n"
TWO_TIERS = _frontmatter("TIER_1_FAMILY", "TIER_3_FAMILY")
BODY_ONLY_TIER = "---\nname: Fixture\n---\n\n# Fixture {{TIER_2_FAMILY}}\n"

AGENT = "---\nname: x\n---\n"


def _snapshot(*roots: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.is_file() and not path.is_symlink():
                result[f"{root.name}/{path.relative_to(root).as_posix()}"] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
    return result


class SiteFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.workspace = base / "workspace"
        self.home = base / "home"
        self.outside = base / "outside"
        for directory in (self.workspace, self.home, self.outside):
            directory.mkdir()
        self.read_paths: list[Path] = []
        real = sites_module._read_template_bytes

        def recording(path):
            self.read_paths.append(Path(path))
            return real(path)

        patcher = mock.patch.object(sites_module, "_read_template_bytes", side_effect=recording)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, root: Path, rel: str, text: str) -> Path:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def build(self, manifest, profile=None) -> SiteRegistry:
        before = _snapshot(self.workspace, self.home, self.outside)
        registry = build_site_registry(self.workspace, self.home, manifest, profile)
        self.assertEqual(_snapshot(self.workspace, self.home, self.outside), before, "builder wrote to disk")
        return registry

    @staticmethod
    def artifact(path: str, template: str) -> dict:
        return {"path": path, "template": template}

    @staticmethod
    def community(path: str, template_path: str) -> dict:
        return {"installed_path": path, "template_path": template_path, "template_id": Path(path).name}


class DeriveTierTests(unittest.TestCase):
    def test_exactly_one_distinct_tier_in_frontmatter(self):
        self.assertEqual(derive_template_default_tier(TIER_2), ("tier2", None))
        self.assertEqual(derive_template_default_tier(_frontmatter("TIER_3_FAMILY", "TIER_3_FAMILY")), ("tier3", None))

    def test_no_or_ambiguous_tier(self):
        self.assertEqual(derive_template_default_tier(NO_TIER), (None, "no-tier-placeholder"))
        self.assertEqual(derive_template_default_tier(TWO_TIERS), (None, "ambiguous-tier"))

    def test_only_the_frontmatter_block_is_parsed(self):
        self.assertEqual(derive_template_default_tier(BODY_ONLY_TIER), (None, "no-tier-placeholder"))
        self.assertEqual(derive_template_default_tier("no frontmatter {{TIER_1_FAMILY}}"), (None, "no-tier-placeholder"))

    def test_crlf_and_bom_frontmatter(self):
        text = "\ufeff" + TIER_1.replace("\n", "\r\n")
        self.assertEqual(derive_template_default_tier(text), ("tier1", None))

    def test_unquoted_placeholder_is_not_yaml_parsed(self):
        text = "---\nname: x\nmodel_family: {{TIER_2_FAMILY}}\nmodel: {unclosed\n---\n"
        self.assertEqual(derive_template_default_tier(text), ("tier2", None))


class ManagedAndAuthoredTests(SiteFixture):
    def test_managed_rendered_agent_registers_with_template_default_tier(self):
        self.write(self.workspace, ".github/agents/subagents/alpha.agent.md", AGENT)
        self.write(self.home, "templates/agents/review/alpha.agent.md.tmpl", TIER_1)
        manifest = {
            "artifacts": [self.artifact(".github/agents/subagents/alpha.agent.md", "agents/review/alpha.agent.md.tmpl")]
        }
        registry = self.build(manifest)
        self.assertEqual(dict(registry.sites), {"alpha": SiteSpec("alpha", "tier1", True)})
        self.assertEqual((registry.orphans, registry.conflicts, dict(registry.unresolved)), ((), (), {}))

    def test_managed_community_agent_registers_with_template_default_tier(self):
        self.write(self.workspace, ".github/agents/beta.agent.md", AGENT)
        self.write(self.home, "templates/community/agents/beta.agent.md.tmpl", TIER_2)
        manifest = {
            "community_templates": [
                self.community(".github/agents/beta.agent.md", "templates/community/agents/beta.agent.md.tmpl")
            ]
        }
        registry = self.build(manifest)
        self.assertEqual(dict(registry.sites), {"beta": SiteSpec("beta", "tier2", True)})
        self.assertEqual(dict(registry.unresolved), {})

    def test_same_template_bytes_yield_the_same_tier_through_either_source(self):
        self.write(self.workspace, ".github/agents/rendered.agent.md", AGENT)
        self.write(self.workspace, ".github/agents/community.agent.md", AGENT)
        self.write(self.home, "templates/agents/shared.agent.md.tmpl", TIER_2)
        self.write(self.home, "templates/community/agents/shared.agent.md.tmpl", TIER_2)
        manifest = {
            "artifacts": [self.artifact(".github/agents/rendered.agent.md", "agents/shared.agent.md.tmpl")],
            "community_templates": [
                self.community(".github/agents/community.agent.md", "templates/community/agents/shared.agent.md.tmpl")
            ],
        }
        registry = self.build(manifest)
        self.assertEqual(registry.sites["rendered"].default_tier, "tier2")
        self.assertEqual(registry.sites["rendered"].default_tier, registry.sites["community"].default_tier)

    def test_workspace_authored_agent_without_manifest_entry_is_unmanaged(self):
        self.write(self.workspace, ".github/agents/custom.agent.md", AGENT)
        registry = self.build({"artifacts": []})
        self.assertEqual(dict(registry.sites), {"custom": SiteSpec("custom", None, False)})
        self.assertEqual(dict(registry.unresolved), {})
        self.assertEqual(self.read_paths, [])

    def test_non_dict_manifest_registers_everything_as_workspace_authored(self):
        self.write(self.workspace, ".github/agents/custom.agent.md", AGENT)
        for manifest in (None, [], "x"):
            with self.subTest(manifest=manifest):
                registry = self.build(manifest)
                self.assertEqual(dict(registry.sites), {"custom": SiteSpec("custom", None, False)})

    def test_managed_rendered_with_missing_template_source_is_workspace_authored(self):
        self.write(self.workspace, ".github/agents/ghosted.agent.md", AGENT)
        manifest = {"artifacts": [self.artifact(".github/agents/ghosted.agent.md", "agents/missing.agent.md.tmpl")]}
        registry = self.build(manifest)
        self.assertEqual(dict(registry.sites), {"ghosted": SiteSpec("ghosted", None, False)})
        self.assertEqual(dict(registry.unresolved), {})

    def test_site_id_is_the_installed_file_name(self):
        self.write(self.workspace, ".github/agents/subagents/python-reviewer.agent.md", AGENT)
        self.write(self.home, "templates/agents/review/technology-reviewer.agent.md.tmpl", TIER_1)
        manifest = {
            "artifacts": [
                self.artifact(
                    ".github/agents/subagents/python-reviewer.agent.md", "agents/review/technology-reviewer.agent.md.tmpl"
                )
            ]
        }
        self.assertEqual(list(self.build(manifest).sites), ["python-reviewer"])

    def test_scan_includes_the_local_agents_dir_for_a_global_tool_profile(self):
        self.write(self.workspace, ".github/local-agents/local.agent.md", AGENT)
        self.assertEqual(self.build({}).sites, {})
        profile = {"distribution": {"is_global_tool": True}}
        self.assertEqual(list(self.build({}, profile).sites), ["local"])


class UnresolvedDefaultTests(SiteFixture):
    def _managed(self, kind: str, template_text: str):
        self.write(self.workspace, ".github/agents/gamma.agent.md", AGENT)
        if kind == "rendered":
            self.write(self.home, "templates/agents/gamma.agent.md.tmpl", template_text)
            return {"artifacts": [self.artifact(".github/agents/gamma.agent.md", "agents/gamma.agent.md.tmpl")]}
        self.write(self.home, "templates/community/agents/gamma.agent.md.tmpl", template_text)
        return {
            "community_templates": [
                self.community(".github/agents/gamma.agent.md", "templates/community/agents/gamma.agent.md.tmpl")
            ]
        }

    def assert_unresolved(self, registry: SiteRegistry, reason: str):
        self.assertEqual(dict(registry.sites), {"gamma": SiteSpec("gamma", None, True)})
        self.assertEqual(dict(registry.unresolved), {"gamma": reason})
        self.assertEqual((registry.orphans, registry.conflicts), ((), ()))

    def test_template_without_tier_placeholder_for_both_classes(self):
        for kind in ("rendered", "community"):
            with self.subTest(kind=kind):
                self.assert_unresolved(self.build(self._managed(kind, NO_TIER)), "no-tier-placeholder")

    def test_template_with_two_distinct_tiers_for_both_classes(self):
        for kind in ("rendered", "community"):
            with self.subTest(kind=kind):
                self.assert_unresolved(self.build(self._managed(kind, TWO_TIERS)), "ambiguous-tier")

    def test_template_whose_read_raises_for_both_classes(self):
        for kind in ("rendered", "community"):
            for error in (OSError("denied"), UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad")):
                with self.subTest(kind=kind, error=type(error).__name__):
                    manifest = self._managed(kind, TIER_1)
                    with mock.patch.object(sites_module, "_read_template_bytes", side_effect=error):
                        self.assert_unresolved(self.build(manifest), "template-unreadable")

    def test_undecodable_template_bytes_are_unreadable(self):
        manifest = self._managed("rendered", TIER_1)
        with mock.patch.object(sites_module, "_read_template_bytes", return_value=b"\xff\xfe\x00bad"):
            self.assert_unresolved(self.build(manifest), "template-unreadable")

    def test_community_template_path_naming_a_missing_file(self):
        self.write(self.workspace, ".github/agents/gamma.agent.md", AGENT)
        manifest = {
            "community_templates": [
                self.community(".github/agents/gamma.agent.md", "templates/community/agents/absent.agent.md.tmpl")
            ]
        }
        self.assert_unresolved(self.build(manifest), "template-path-unusable")
        self.assertEqual(self.read_paths, [])

    def test_community_template_path_that_is_absolute_or_escapes_is_never_read(self):
        outside_template = self.write(self.outside, "evil.agent.md.tmpl", TIER_1)
        for label, template_path in (
            ("absolute", str(outside_template)),
            ("rooted", "/" + outside_template.name),
            ("traversal", "templates/../../outside/evil.agent.md.tmpl"),
            ("backslash-traversal", "templates\\..\\..\\outside\\evil.agent.md.tmpl"),
            ("outside-templates", "docs/evil.agent.md.tmpl"),
            ("not-a-file", "templates"),
        ):
            with self.subTest(label=label):
                self.write(self.home, "docs/evil.agent.md.tmpl", TIER_1)
                (self.home / "templates").mkdir(exist_ok=True)
                self.write(self.workspace, ".github/agents/gamma.agent.md", AGENT)
                manifest = {
                    "community_templates": [self.community(".github/agents/gamma.agent.md", template_path)]
                }
                self.read_paths.clear()
                self.assert_unresolved(self.build(manifest), "template-path-unusable")
                self.assertEqual(self.read_paths, [], "an unusable template path must never be read")

    def test_unresolved_site_never_raises_or_guesses(self):
        manifest = self._managed("community", NO_TIER)
        registry = self.build(manifest)
        self.assertTrue(registry.sites["gamma"].managed)
        self.assertIsNone(registry.sites["gamma"].default_tier)


class ExclusionOrphanAndConflictTests(SiteFixture):
    def test_pipeline_and_managed_source_agents_are_excluded(self):
        for name in PIPELINE_AND_SOURCE:
            self.write(self.workspace, f".github/agents/{name}.agent.md", AGENT)
        self.write(self.workspace, ".github/agents/subagents/keep.agent.md", AGENT)
        manifest = {
            "artifacts": [
                self.artifact(".github/agents/auto-tune.agent.md", "global agent definition"),
                self.artifact(".github/agents/auto-mergeinstall.agent.md", "global agent definition"),
            ]
        }
        registry = self.build(manifest)
        self.assertEqual(list(registry.sites), ["keep"])

    def test_missing_pipeline_and_managed_source_files_are_not_orphans(self):
        manifest = {
            "artifacts": [
                self.artifact(".github/agents/_stage.agent.md", "agents/_stage.agent.md.tmpl"),
                self.artifact(".github/agents/auto-tune.agent.md", "global agent definition"),
            ]
        }
        self.assertEqual(self.build(manifest).orphans, ())

    def test_manifest_orphans_from_artifacts_and_community_entries(self):
        self.write(self.home, "templates/agents/review/present.agent.md.tmpl", TIER_1)
        self.write(self.workspace, ".github/agents/subagents/present.agent.md", AGENT)
        manifest = {
            "artifacts": [
                self.artifact(".github/agents/subagents/present.agent.md", "agents/review/present.agent.md.tmpl"),
                self.artifact(".github/agents/subagents/zeta.agent.md", "agents/review/zeta.agent.md.tmpl"),
                self.artifact(".github/skills/x/SKILL.md", "skills/x/SKILL.md.tmpl"),
                self.artifact("docs/elsewhere.agent.md", "agents/elsewhere.agent.md.tmpl"),
            ],
            "community_templates": [
                self.community(".github/agents/alpha.agent.md", "templates/community/agents/alpha.agent.md.tmpl")
            ],
        }
        registry = self.build(manifest)
        self.assertEqual(registry.orphans, (".github/agents/alpha.agent.md", ".github/agents/subagents/zeta.agent.md"))
        self.assertEqual(list(registry.sites), ["present"])
        self.assertEqual(dict(registry.unresolved), {})

    def test_same_site_id_in_two_files_registers_neither(self):
        self.write(self.workspace, ".github/agents/subagents/dup.agent.md", AGENT)
        self.write(self.workspace, ".github/agents/dup.agent.md", AGENT)
        self.write(self.workspace, ".github/agents/solo.agent.md", AGENT)
        self.write(self.home, "templates/agents/dup.agent.md.tmpl", TIER_1)
        manifest = {"artifacts": [self.artifact(".github/agents/dup.agent.md", "agents/dup.agent.md.tmpl")]}
        registry = self.build(manifest)
        self.assertEqual(registry.conflicts, ("dup",))
        self.assertEqual(list(registry.sites), ["solo"])
        self.assertEqual(dict(registry.unresolved), {})
        self.assertEqual(self.read_paths, [])

    def test_registry_is_frozen_with_sorted_deterministic_output(self):
        for name in ("zz", "aa", "mm"):
            self.write(self.workspace, f".github/agents/{name}.agent.md", AGENT)
        registry = self.build({})
        self.assertEqual(list(registry.sites), ["aa", "mm", "zz"])
        with self.assertRaises(AttributeError):
            registry.orphans = ()
        with self.assertRaises(TypeError):
            registry.sites["new"] = SiteSpec("new", None, False)


class ContainmentTests(SiteFixture):
    def _symlink(self, link: Path, target: Path, directory: bool):
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(target, link, target_is_directory=directory)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlinks unavailable: {exc}")

    def test_symlinked_scan_root_is_not_traversed_or_read(self):
        self.write(self.outside, "agents/escaped.agent.md", AGENT)
        self.write(self.home, "templates/agents/escaped.agent.md.tmpl", TIER_1)
        self._symlink(self.workspace / ".github" / "agents", self.outside / "agents", True)
        manifest = {"artifacts": [self.artifact(".github/agents/escaped.agent.md", "agents/escaped.agent.md.tmpl")]}
        registry = self.build(manifest)
        self.assertEqual(dict(registry.sites), {})
        self.assertEqual(self.read_paths, [])

    def test_symlinked_agent_file_is_skipped(self):
        real = self.write(self.outside, "real.agent.md", AGENT)
        self.write(self.workspace, ".github/agents/ok.agent.md", AGENT)
        self._symlink(self.workspace / ".github" / "agents" / "linked.agent.md", real, False)
        registry = self.build({})
        self.assertEqual(list(registry.sites), ["ok"])

    def test_symlinked_agent_subdirectory_escape_is_not_registered(self):
        self.write(self.outside, "sub/escaped.agent.md", AGENT)
        self._symlink(self.workspace / ".github" / "agents" / "subagents", self.outside / "sub", True)
        self.write(self.workspace, ".github/agents/ok.agent.md", AGENT)
        self.assertEqual(list(self.build({}).sites), ["ok"])


class ImportTests(unittest.TestCase):
    def test_module_imports_standalone_without_verify_workspace(self):
        code = (
            "import sys; import autoharness.model_routing_sites as m; "
            "assert 'autoharness.verify_workspace' not in sys.modules; "
            "assert callable(m.build_site_registry)"
        )
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
        result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_verify_workspace_still_imports_after_the_module(self):
        code = "import autoharness.model_routing_sites, autoharness.verify_workspace"
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
        result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


def _shipped_agent_templates() -> list[Path]:
    agents = sorted((REPO_ROOT / "templates" / "agents").rglob("*.agent.md.tmpl"))
    community = sorted((REPO_ROOT / "templates" / "community" / "agents").glob("*.agent.md.tmpl"))
    return [path for path in agents if not path.name.startswith("_")] + community


class TemplateSyncTests(unittest.TestCase):
    def test_every_shipped_subagent_and_community_agent_template_maps_to_exactly_one_tier(self):
        templates = _shipped_agent_templates()
        self.assertTrue(any(p.name == "adr-generator.agent.md.tmpl" for p in templates))
        self.assertGreaterEqual(len(templates), 14)
        for path in templates:
            with self.subTest(template=path.relative_to(REPO_ROOT).as_posix()):
                tier, reason = derive_template_default_tier(path.read_text(encoding="utf-8"))
                self.assertIsNone(reason, "add a recognizable {{TIER_<N>_FAMILY}} frontmatter variable")
                self.assertIn(tier, ("tier1", "tier2", "tier3"))


class ThisWorkspaceTests(unittest.TestCase):
    EXPECTED_SUBAGENTS = (
        "agent-native-parity-reviewer",
        "architecture-strategist",
        "concurrency-reviewer",
        "constitution-reviewer",
        "correctness-reviewer",
        "learnings-researcher",
        "maintainability-reviewer",
        "python-reviewer",
        "schema-cli-docs-coupling-reviewer",
        "scope-boundary-auditor",
        "security-lens-reviewer",
        "security-reviewer",
        "template-integrity-reviewer",
    )

    @classmethod
    def setUpClass(cls):
        manifest = yaml.safe_load((REPO_ROOT / ".autoharness" / "harness-manifest.yaml").read_text(encoding="utf-8"))
        profile = yaml.safe_load((REPO_ROOT / ".autoharness" / "workspace-profile.yaml").read_text(encoding="utf-8"))
        cls.registry = build_site_registry(REPO_ROOT, REPO_ROOT, manifest, profile)

    def test_registry_holds_the_thirteen_managed_subagents_and_nothing_else(self):
        self.assertEqual(sorted(self.registry.sites), sorted(self.EXPECTED_SUBAGENTS))
        for site_id, spec in self.registry.sites.items():
            with self.subTest(site=site_id):
                self.assertTrue(spec.managed)
                self.assertIn(spec.default_tier, ("tier1", "tier2", "tier3"))
        self.assertEqual(self.registry.sites["python-reviewer"].default_tier, "tier1")
        self.assertEqual(self.registry.sites["security-reviewer"].default_tier, "tier2")

    def test_pipeline_and_source_agents_are_excluded_and_nothing_is_flagged(self):
        for name in PIPELINE_AND_SOURCE:
            self.assertNotIn(name, self.registry.sites)
        self.assertEqual(self.registry.orphans, ())
        self.assertEqual(self.registry.conflicts, ())
        self.assertEqual(dict(self.registry.unresolved), {})


if __name__ == "__main__":
    unittest.main()
