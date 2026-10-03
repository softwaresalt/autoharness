"""verify_workspace frontmatter-conformity check (193-F B2a).

B2a.1 (193.004.001-ST): artifact-class derivation, plugin-global profile
selection, scan-target enumeration, and the resolve-then-contain per-file
evaluation. B2a.2 (193.004.002-ST): check integration, result shape, Markdown
parity, INV-B3 byte identity, and the dogfood pin.

Plan: docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md (### B2a).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import yaml

from autoharness import verify_workspace as vw
from autoharness.frontmatter_contract import (
    FM_BARE_MODEL,
    FM_PARSE_ERROR,
    FM_PATH_ESCAPE,
    PROFILE_PLUGIN_GLOBAL,
    PROFILE_TIER_ROUTED,
)

_ROOT = Path(__file__).resolve().parents[1]


def _symlinks_supported() -> bool:
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "target"
        target.write_text("x", encoding="utf-8")
        try:
            os.symlink(target, Path(temp_dir) / "link")
        except (OSError, NotImplementedError):
            return False
    return True


_SYMLINKS = _symlinks_supported()
_SYMLINK_SKIP = "platform cannot create symlinks (e.g. Windows without developer mode)"

CONFORMANT_AGENT = (
    "---\n"
    "name: Demo\n"
    "description: A demo agent\n"
    "max_subagent_tier: 2\n"
    "subagent_depth: 0\n"
    "model_family: fam\n"
    "model_provider: prov\n"
    "reasoning_effort: high\n"
    "---\n\n# Demo\n"
)
PLUGIN_GLOBAL_AGENT = (
    "---\n"
    "name: Demo\n"
    "description: A demo agent\n"
    "max_subagent_tier: 2\n"
    "subagent_depth: 0\n"
    "---\n\n# Demo\n"
)
BARE_MODEL_AGENT = "---\nname: Hand\ndescription: Hand-written agent\nmodel: gpt-x\n---\n\n# Hand\n"


def _skill(name: str | None, extra: str = "") -> str:
    name_line = f"name: {name}\n" if name else ""
    return f"---\n{name_line}description: A demo skill\n{extra}---\n\n# Skill\n"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class _Env:
    """A scratch autoharness_home + workspace pair under a temp directory."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.home = root / "home"
        self.ws = root / "ws"
        (self.home / "templates").mkdir(parents=True)
        (self.ws / ".autoharness").mkdir(parents=True)
        self.workspace = self.ws.resolve()
        self.autoharness_home = self.home.resolve()

    def write(self, relative: str, text: str, base: Path | None = None) -> Path:
        path = (base or self.ws) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))  # exact bytes: no newline translation
        return path

    def template(self, relative: str, text: str = "---\nname: x\n---\n") -> Path:
        return self.write(relative, text, base=self.home / "templates")


def _artifact(path: str, template: str, checksum: str = "") -> dict[str, Any]:
    return {"path": path, "template": template, "checksum": checksum, "primitive": 1}


# ---------------------------------------------------------------------------
# B2a.1 — classification
# ---------------------------------------------------------------------------


class ProvenanceClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.env = _Env(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _classify(self, manifest: dict[str, Any], rel: str) -> dict[str, Any]:
        index = vw._fc_build_provenance_index(self.env.workspace, self.env.autoharness_home, manifest)
        return vw._fc_classify(rel, index)

    def test_managed_rendered_requires_existing_contained_source(self) -> None:
        self.env.template("agents/demo.agent.md.tmpl")
        manifest = {"artifacts": [_artifact(".github/agents/demo.agent.md", "agents/demo.agent.md.tmpl")]}
        entry = self._classify(manifest, ".github/agents/demo.agent.md")
        self.assertEqual(entry["class"], vw.FC_CLASS_MANAGED_RENDERED)
        self.assertTrue(entry["tracked"])
        self.assertEqual(
            Path(entry["source_path"]).resolve(),
            (self.env.home / "templates" / "agents" / "demo.agent.md.tmpl").resolve(),
        )

    def test_templates_prefixed_label_resolves_managed_rendered(self) -> None:
        self.env.template("agents/demo.agent.md.tmpl")
        manifest = {
            "artifacts": [_artifact(".github/agents/demo.agent.md", "templates/agents/demo.agent.md.tmpl")]
        }
        self.assertEqual(
            self._classify(manifest, ".github/agents/demo.agent.md")["class"],
            vw.FC_CLASS_MANAGED_RENDERED,
        )

    def test_suffix_shaped_label_without_source_is_unknown_provenance(self) -> None:
        manifest = {"artifacts": [_artifact(".github/agents/demo.agent.md", "agents/missing.agent.md")]}
        self.assertEqual(
            self._classify(manifest, ".github/agents/demo.agent.md")["class"],
            vw.FC_CLASS_UNKNOWN_PROVENANCE,
        )

    def test_label_escaping_templates_dir_is_unknown_provenance(self) -> None:
        self.env.write("outside.md", "---\nname: x\n---\n", base=self.env.home)
        manifest = {
            "artifacts": [_artifact(".github/agents/demo.agent.md", "templates/../outside.md")]
        }
        self.assertEqual(
            self._classify(manifest, ".github/agents/demo.agent.md")["class"],
            vw.FC_CLASS_UNKNOWN_PROVENANCE,
        )

    def test_global_definition_labels_are_managed_source(self) -> None:
        manifest = {
            "artifacts": [
                _artifact(".github/agents/x.agent.md", "global agent definition"),
                _artifact(".github/skills/y/SKILL.md", "global skill definition"),
            ]
        }
        self.assertEqual(vw.AUTOHARNESS_SOURCE_LABELS, {"global agent definition", "global skill definition"})
        self.assertEqual(self._classify(manifest, ".github/agents/x.agent.md")["class"], vw.FC_CLASS_MANAGED_SOURCE)
        self.assertEqual(self._classify(manifest, ".github/skills/y/SKILL.md")["class"], vw.FC_CLASS_MANAGED_SOURCE)

    def test_workspace_source_label_is_workspace_authored(self) -> None:
        manifest = {"artifacts": [_artifact(".github/agents/x.agent.md", "workspace merge install")]}
        entry = self._classify(manifest, ".github/agents/x.agent.md")
        self.assertEqual(entry["class"], vw.FC_CLASS_WORKSPACE_AUTHORED)
        self.assertTrue(entry["tracked"])

    def test_untracked_path_is_workspace_authored(self) -> None:
        entry = self._classify({"artifacts": []}, ".github/agents/hand.agent.md")
        self.assertEqual(entry["class"], vw.FC_CLASS_WORKSPACE_AUTHORED)
        self.assertFalse(entry["tracked"])

    def test_other_tracked_labels_are_unknown_provenance(self) -> None:
        manifest = {
            "artifacts": [
                _artifact(".github/agents/a.agent.md", "workspace-discovery output"),
                _artifact(".github/agents/b.agent.md", "some label a target added"),
            ]
        }
        for rel in (".github/agents/a.agent.md", ".github/agents/b.agent.md"):
            self.assertEqual(self._classify(manifest, rel)["class"], vw.FC_CLASS_UNKNOWN_PROVENANCE, rel)

    def test_community_installed_path_is_managed_community(self) -> None:
        manifest = {
            "artifacts": [],
            "community_templates": [
                {
                    "template_id": "adr-generator",
                    "template_path": "templates/community/agents/adr-generator.agent.md.tmpl",
                    "installed_path": ".github/agents/adr-generator.agent.md",
                    "installed_checksum": "abc",
                    "source_checksum": "def",
                }
            ],
        }
        entry = self._classify(manifest, ".github/agents/adr-generator.agent.md")
        self.assertEqual(entry["class"], vw.FC_CLASS_MANAGED_COMMUNITY)
        self.assertEqual(entry["installed_checksum"], "abc")
        self.assertEqual(entry["template_path"], "templates/community/agents/adr-generator.agent.md.tmpl")

    def test_paths_compare_as_normalized_posix_strings(self) -> None:
        manifest = {"artifacts": [_artifact(".\\.github\\agents\\x.agent.md", "global agent definition")]}
        self.assertEqual(self._classify(manifest, ".github/agents/x.agent.md")["class"], vw.FC_CLASS_MANAGED_SOURCE)

    def test_malformed_manifest_entries_are_ignored(self) -> None:
        manifest = {"artifacts": ["nope", 3, None], "community_templates": "bad"}
        self.assertEqual(
            self._classify(manifest, ".github/agents/x.agent.md")["class"], vw.FC_CLASS_WORKSPACE_AUTHORED
        )


# ---------------------------------------------------------------------------
# B2a.1 — plugin-global selector
# ---------------------------------------------------------------------------


class PluginAgentSelectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.env = _Env(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _plugin(self, data: Any) -> None:
        text = data if isinstance(data, str) else json.dumps(data)
        self.env.write("plugin.json", text)

    def _load(self, install_mode: str | None = "self-install") -> tuple[frozenset[str], list[dict[str, Any]]]:
        manifest: dict[str, Any] = {"artifacts": []}
        if install_mode is not None:
            manifest["install_mode"] = install_mode
        return vw._fc_load_plugin_agents(self.env.workspace, manifest)

    def test_self_install_autoharness_plugin_lists_agents(self) -> None:
        self._plugin({"name": "autoharness", "agents": ["./.github/agents/auto-tune.agent.md"]})
        agents, warnings = self._load()
        self.assertEqual(agents, frozenset({".github/agents/auto-tune.agent.md"}))
        self.assertEqual(warnings, [])

    def test_foreign_plugin_name_is_ignored(self) -> None:
        self._plugin({"name": "other-plugin", "agents": [".github/agents/auto-tune.agent.md"]})
        agents, warnings = self._load()
        self.assertEqual(agents, frozenset())
        self.assertEqual(warnings, [])

    def test_non_self_install_manifest_never_selects_plugin_global(self) -> None:
        self._plugin({"name": "autoharness", "agents": [".github/agents/auto-tune.agent.md"]})
        for mode in (None, "workspace", "global"):
            agents, warnings = self._load(mode)
            self.assertEqual(agents, frozenset(), mode)
            self.assertEqual(warnings, [], mode)

    def test_missing_plugin_json_is_empty_without_warning(self) -> None:
        agents, warnings = self._load()
        self.assertEqual((agents, warnings), (frozenset(), []))

    def test_invalid_plugin_json_warns_once_and_is_empty(self) -> None:
        for payload in ("{not json", json.dumps(["a"]), json.dumps({"name": "autoharness", "agents": "x"})):
            self._plugin(payload)
            agents, warnings = self._load()
            self.assertEqual(agents, frozenset(), payload)
            self.assertEqual(len(warnings), 1, payload)
            self.assertEqual(warnings[0]["kind"], "frontmatter-conformity-plugin-json")

    def test_undecodable_plugin_json_warns_once(self) -> None:
        (self.env.ws / "plugin.json").write_bytes(b"\xff\xfe\x00bad")
        agents, warnings = self._load()
        self.assertEqual(agents, frozenset())
        self.assertEqual(len(warnings), 1)

    @unittest.skipUnless(_SYMLINKS, _SYMLINK_SKIP)
    def test_symlinked_plugin_json_escaping_workspace_is_never_read(self) -> None:
        outside = self.env.root / "outside-plugin.json"
        outside.write_text(
            json.dumps({"name": "autoharness", "agents": [".github/agents/auto-tune.agent.md"]}),
            encoding="utf-8",
        )
        os.symlink(outside, self.env.ws / "plugin.json")
        with mock.patch.object(vw, "_fc_read_bytes", side_effect=AssertionError("read")) as reader:
            agents, warnings = self._load()
        reader.assert_not_called()
        self.assertEqual(agents, frozenset())
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["kind"], "frontmatter-conformity-plugin-json")

    @unittest.skipUnless(_SYMLINKS, _SYMLINK_SKIP)
    def test_symlinked_plugin_json_inside_workspace_is_not_read(self) -> None:
        inner = self.env.write(
            "real-plugin.json",
            json.dumps({"name": "autoharness", "agents": [".github/agents/auto-tune.agent.md"]}),
        )
        os.symlink(inner, self.env.ws / "plugin.json")
        agents, warnings = self._load()
        self.assertEqual(agents, frozenset())
        self.assertEqual(len(warnings), 1)

    def test_plugin_json_directory_is_not_read(self) -> None:
        (self.env.ws / "plugin.json").mkdir()
        agents, warnings = self._load()
        self.assertEqual(agents, frozenset())
        self.assertEqual(len(warnings), 1)


# ---------------------------------------------------------------------------
# B2a.1 — scan-target enumeration and containment
# ---------------------------------------------------------------------------


class ScanTargetEnumerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.env = _Env(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_missing_directories_give_zero_targets(self) -> None:
        self.assertEqual(vw._fc_enumerate_targets(self.env.workspace, {}), [])

    def test_agents_recursive_and_skill_roots_only_sorted(self) -> None:
        self.env.write(".github/agents/z.agent.md", CONFORMANT_AGENT)
        self.env.write(".github/agents/subagents/a.agent.md", CONFORMANT_AGENT)
        self.env.write(".github/agents/notes.md", "not an agent")
        self.env.write(".github/skills/beta/SKILL.md", _skill("beta"))
        self.env.write(".github/skills/alpha/SKILL.md", _skill("alpha"))
        self.env.write(".github/skills/alpha/resources/nested/SKILL.md", _skill("nested"))
        self.env.write(".github/skills/README.md", "readme")
        targets = vw._fc_enumerate_targets(self.env.workspace, {})
        self.assertEqual(
            [(t["rel"], t["kind"]) for t in targets],
            [
                (".github/agents/subagents/a.agent.md", "agent"),
                (".github/agents/z.agent.md", "agent"),
                (".github/skills/alpha/SKILL.md", "skill"),
                (".github/skills/beta/SKILL.md", "skill"),
            ],
        )
        self.assertEqual(targets[2]["skill_dir"], "alpha")

    def test_configured_local_agents_dir_is_scanned_for_global_tool(self) -> None:
        self.env.write("custom-agents/local.agent.md", CONFORMANT_AGENT)
        profile = {"distribution": {"is_global_tool": True, "local_agents_dir": "custom-agents"}}
        rels = [t["rel"] for t in vw._fc_enumerate_targets(self.env.workspace, profile)]
        self.assertEqual(rels, ["custom-agents/local.agent.md"])
        # Not a global tool: the local agents dir is not scanned.
        self.assertEqual(vw._fc_enumerate_targets(self.env.workspace, {}), [])

    def test_overlapping_scan_dirs_are_deduplicated(self) -> None:
        self.env.write(".github/agents/x.agent.md", CONFORMANT_AGENT)
        profile = {"distribution": {"is_global_tool": True, "local_agents_dir": ".github/agents"}}
        rels = [t["rel"] for t in vw._fc_enumerate_targets(self.env.workspace, profile)]
        self.assertEqual(rels, [".github/agents/x.agent.md"])

    def test_contained_file_resolves_inside_workspace(self) -> None:
        path = self.env.write(".github/agents/x.agent.md", CONFORMANT_AGENT)
        resolved = vw._fc_resolve_contained(self.env.workspace, path)
        self.assertEqual(resolved, path.resolve())

    @unittest.skipUnless(_SYMLINKS, _SYMLINK_SKIP)
    def test_escaping_symlink_is_not_contained(self) -> None:
        outside = self.env.root / "outside.agent.md"
        outside.write_text(CONFORMANT_AGENT, encoding="utf-8")
        link = self.env.ws / ".github" / "agents" / "x.agent.md"
        link.parent.mkdir(parents=True)
        os.symlink(outside, link)
        self.assertIsNone(vw._fc_resolve_contained(self.env.workspace, link))


# ---------------------------------------------------------------------------
# B2a.1 — per-file evaluation (resolve-then-contain, never read escaping bytes)
# ---------------------------------------------------------------------------


class PerFileEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.env = _Env(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _evaluate(
        self,
        manifest: dict[str, Any],
        rel: str,
        plugin_agents: frozenset[str] = frozenset(),
        checksum_lookup: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        index = vw._fc_build_provenance_index(self.env.workspace, self.env.autoharness_home, manifest)
        targets = {t["rel"]: t for t in vw._fc_enumerate_targets(self.env.workspace, {})}
        return vw._fc_evaluate_target(
            self.env.workspace, targets[rel], index, plugin_agents, checksum_lookup or {}
        )

    @unittest.skipUnless(_SYMLINKS, _SYMLINK_SKIP)
    def test_escaping_managed_path_gives_fm_path_escape_without_reading(self) -> None:
        outside = self.env.root / "outside.agent.md"
        outside.write_text(BARE_MODEL_AGENT, encoding="utf-8")
        link = self.env.ws / ".github" / "agents" / "x.agent.md"
        link.parent.mkdir(parents=True)
        os.symlink(outside, link)
        manifest = {"artifacts": [_artifact(".github/agents/x.agent.md", "global agent definition")]}
        with mock.patch.object(vw, "_fc_read_bytes", side_effect=AssertionError("read")) as reader:
            record = self._evaluate(manifest, ".github/agents/x.agent.md")
        reader.assert_not_called()
        self.assertFalse(record["skipped"])
        self.assertEqual([f.code for f in record["findings"]], [FM_PATH_ESCAPE])
        self.assertEqual(record["class"], vw.FC_CLASS_MANAGED_SOURCE)

    @unittest.skipUnless(_SYMLINKS, _SYMLINK_SKIP)
    def test_escaping_untracked_path_is_skipped_with_warning_without_reading(self) -> None:
        outside = self.env.root / "outside.agent.md"
        outside.write_text(BARE_MODEL_AGENT, encoding="utf-8")
        link = self.env.ws / ".github" / "agents" / "x.agent.md"
        link.parent.mkdir(parents=True)
        os.symlink(outside, link)
        with mock.patch.object(vw, "_fc_read_bytes", side_effect=AssertionError("read")) as reader:
            record = self._evaluate({"artifacts": []}, ".github/agents/x.agent.md")
        reader.assert_not_called()
        self.assertTrue(record["skipped"])
        self.assertEqual(record["warning"]["kind"], "frontmatter-conformity")
        self.assertEqual(record["warning"]["path"], ".github/agents/x.agent.md")

    def test_undecodable_file_gives_parse_error(self) -> None:
        path = self.env.ws / ".github" / "agents" / "x.agent.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"---\nname: \xff\xfe\n---\n")
        record = self._evaluate({"artifacts": []}, ".github/agents/x.agent.md")
        self.assertEqual([f.code for f in record["findings"]], [FM_PARSE_ERROR])

    def test_unexpected_exception_becomes_parse_error_with_type_name(self) -> None:
        self.env.write(".github/agents/x.agent.md", CONFORMANT_AGENT)
        with mock.patch.object(vw.fc, "parse_frontmatter", side_effect=RuntimeError("boom")):
            record = self._evaluate({"artifacts": []}, ".github/agents/x.agent.md")
        self.assertEqual([f.code for f in record["findings"]], [FM_PARSE_ERROR])
        self.assertIn("RuntimeError", record["findings"][0].message)

    def test_base_exception_is_not_swallowed(self) -> None:
        self.env.write(".github/agents/x.agent.md", CONFORMANT_AGENT)
        with mock.patch.object(vw.fc, "parse_frontmatter", side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):
                self._evaluate({"artifacts": []}, ".github/agents/x.agent.md")

    def test_profile_selection_uses_plugin_agent_set(self) -> None:
        self.env.write(".github/agents/x.agent.md", PLUGIN_GLOBAL_AGENT)
        plugin = frozenset({".github/agents/x.agent.md"})
        record = self._evaluate({"artifacts": []}, ".github/agents/x.agent.md", plugin)
        self.assertEqual(record["profile"], PROFILE_PLUGIN_GLOBAL)
        self.assertEqual(record["findings"], [])
        record = self._evaluate({"artifacts": []}, ".github/agents/x.agent.md")
        self.assertEqual(record["profile"], PROFILE_TIER_ROUTED)

    def test_skill_profile_and_checksum_status_from_artifact_scan(self) -> None:
        self.env.write(".github/skills/demo/SKILL.md", _skill("demo"))
        manifest = {"artifacts": [_artifact(".github/skills/demo/SKILL.md", "global skill definition", "x")]}
        record = self._evaluate(
            manifest, ".github/skills/demo/SKILL.md", checksum_lookup={".github/skills/demo/SKILL.md": "user-modified"}
        )
        self.assertEqual(record["profile"], "skill")
        self.assertEqual(record["checksum_status"], "user-modified")
        self.assertEqual(record["findings"], [])

    def test_untracked_checksum_status(self) -> None:
        self.env.write(".github/agents/hand.agent.md", BARE_MODEL_AGENT)
        record = self._evaluate({"artifacts": []}, ".github/agents/hand.agent.md")
        self.assertEqual(record["checksum_status"], "untracked")
        self.assertIn(FM_BARE_MODEL, [f.code for f in record["findings"]])

    def test_community_checksum_status_from_installed_checksum(self) -> None:
        self.env.write(".github/agents/adr.agent.md", CONFORMANT_AGENT)
        base = {
            "template_id": "adr",
            "template_path": "templates/community/agents/adr.agent.md.tmpl",
            "installed_path": ".github/agents/adr.agent.md",
            "source_checksum": "",
        }
        cases = ((_sha(CONFORMANT_AGENT), "unchanged"), ("0" * 64, "user-modified"), ("", "checksum-untracked"))
        for checksum, expected in cases:
            manifest = {"artifacts": [], "community_templates": [dict(base, installed_checksum=checksum)]}
            record = self._evaluate(manifest, ".github/agents/adr.agent.md")
            self.assertEqual(record["class"], vw.FC_CLASS_MANAGED_COMMUNITY)
            self.assertEqual(record["checksum_status"], expected, checksum)


# ---------------------------------------------------------------------------
# B2a.2 — check integration, result shape, Markdown parity, INV-B3, dogfood pin
# ---------------------------------------------------------------------------


def _write_permissive_schemas(autoharness_home: Path) -> None:
    schema = json.dumps({"$schema": "http://json-schema.org/draft-07/schema#", "type": "object"})
    for name in ("harness-manifest", "harness-config", "workspace-profile"):
        (autoharness_home / "schemas" / name).mkdir(parents=True, exist_ok=True)
        (autoharness_home / "schemas" / f"{name}.schema.json").write_text(schema, encoding="utf-8")
        (autoharness_home / "schemas" / name / "1.0.0.schema.json").write_text(schema, encoding="utf-8")


class _VerifyFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.env = _Env(Path(self._tmp.name))
        _write_permissive_schemas(self.env.home)
        self.staging = self.env.root / "staging"
        self.artifacts: list[dict[str, Any]] = []
        self.community: list[dict[str, Any]] = []
        self.manifest_extra: dict[str, Any] = {}
        self.profile: dict[str, Any] = {"schema_version": "1.0.0"}

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def track(self, rel: str, label: str, *, unchanged: bool = True) -> None:
        checksum = ""
        path = self.env.ws / rel
        if path.exists():
            checksum = hashlib.sha256(path.read_bytes()).hexdigest() if unchanged else "0" * 64
        self.artifacts.append(_artifact(rel, label, checksum))

    def run_verify(self) -> dict[str, Any]:
        manifest = {
            "schema_version": "1.0.0",
            "installed_at": "2026-09-28T00:00:00Z",
            "autoharness_version": "0.0.0",
            "profile_hash": "abc",
            "primitives_installed": [1],
            "capability_packs": [],
            "artifacts": self.artifacts,
            "variables_used": {"PROJECT_NAME": "demo"},
        }
        if self.community:
            manifest["community_templates"] = self.community
        manifest.update(self.manifest_extra)
        self.env.write(".autoharness/harness-manifest.yaml", yaml.safe_dump(manifest, sort_keys=False))
        self.env.write(".autoharness/config.yaml", yaml.safe_dump({"schema_version": "1.0.0"}))
        self.env.write(".autoharness/workspace-profile.yaml", yaml.safe_dump(self.profile, sort_keys=False))
        return vw.verify_workspace(self.env.ws, self.env.home, self.staging)

    @staticmethod
    def check(report: dict[str, Any]) -> dict[str, Any]:
        return report["targeted_checks"]["frontmatter_conformity"]

    @staticmethod
    def fc_warnings(report: dict[str, Any]) -> list[dict[str, Any]]:
        return [w for w in report["warnings"] if w.get("kind") == vw.FC_WARNING_KIND]


class FrontmatterConformityCheckTests(_VerifyFixture):
    def test_result_shape(self) -> None:
        self.env.write(".github/agents/hand.agent.md", CONFORMANT_AGENT)
        check = self.check(self.run_verify())
        self.assertEqual(set(check), {"ok", "errors", "info", "files"})
        self.assertEqual(
            set(check["files"][".github/agents/hand.agent.md"]),
            {"class", "profile", "checksum_status", "findings"},
        )

    def test_managed_skill_with_routing_key_fails(self) -> None:
        self.env.template("skills/demo/SKILL.md.tmpl", _skill("demo"))
        self.env.write(".github/skills/demo/SKILL.md", _skill("demo", "model_family: fam\n"))
        self.track(".github/skills/demo/SKILL.md", "skills/demo/SKILL.md.tmpl")
        check = self.check(self.run_verify())
        self.assertFalse(check["ok"])
        self.assertIn(".github/skills/demo/SKILL.md: FM_FORBIDDEN_KEY model_family", check["errors"])
        self.assertEqual(check["files"][".github/skills/demo/SKILL.md"]["class"], vw.FC_CLASS_MANAGED_RENDERED)

    def test_managed_user_modified_agent_with_bare_model_fails(self) -> None:
        self.env.template("agents/demo.agent.md.tmpl", CONFORMANT_AGENT)
        self.env.write(".github/agents/demo.agent.md", CONFORMANT_AGENT.replace("---\n\n#", "model: gpt-x\n---\n\n#"))
        self.track(".github/agents/demo.agent.md", "agents/demo.agent.md.tmpl", unchanged=False)
        check = self.check(self.run_verify())
        self.assertFalse(check["ok"])
        record = check["files"][".github/agents/demo.agent.md"]
        self.assertEqual(record["checksum_status"], "user-modified")
        self.assertIn(".github/agents/demo.agent.md: FM_BARE_MODEL model", check["errors"])

    def test_managed_source_skill_without_name_fails(self) -> None:
        self.env.write(".github/skills/install-harness/SKILL.md", _skill(None))
        self.track(".github/skills/install-harness/SKILL.md", "global skill definition")
        check = self.check(self.run_verify())
        self.assertFalse(check["ok"])
        self.assertIn(".github/skills/install-harness/SKILL.md: FM_MISSING_REQUIRED name", check["errors"])

    def test_workspace_authored_bare_model_passes_with_exactly_one_warning(self) -> None:
        self.env.write(".github/agents/hand.agent.md", BARE_MODEL_AGENT)
        report = self.run_verify()
        check = self.check(report)
        self.assertTrue(check["ok"])
        self.assertEqual(check["errors"], [])
        warnings = self.fc_warnings(report)
        self.assertEqual(len(warnings), 1)
        warning = warnings[0]
        self.assertEqual(warning["path"], ".github/agents/hand.agent.md")
        self.assertEqual(warning["class"], vw.FC_CLASS_WORKSPACE_AUTHORED)
        self.assertIn(FM_BARE_MODEL, warning["codes"])
        self.assertEqual(warning["codes"], sorted(set(warning["codes"])))

    def test_unknown_provenance_labels_warn_and_never_fail(self) -> None:
        for name, label in (
            ("a", "workspace-discovery output"),
            ("b", "a label the target added"),
            ("c", "agents/missing-source.agent.md"),
        ):
            rel = f".github/agents/{name}.agent.md"
            self.env.write(rel, BARE_MODEL_AGENT)
            self.track(rel, label)
        report = self.run_verify()
        check = self.check(report)
        self.assertTrue(check["ok"])
        self.assertEqual(check["errors"], [])
        warnings = self.fc_warnings(report)
        self.assertEqual(len(warnings), 3)
        self.assertEqual({w["class"] for w in warnings}, {vw.FC_CLASS_UNKNOWN_PROVENANCE})

    def test_foreign_plugin_json_or_non_self_install_never_selects_plugin_global(self) -> None:
        self.env.write(".github/agents/auto-tune.agent.md", PLUGIN_GLOBAL_AGENT)
        self.track(".github/agents/auto-tune.agent.md", "global agent definition")
        self.env.write("plugin.json", json.dumps({"name": "autoharness", "agents": [".github/agents/auto-tune.agent.md"]}))
        # Manifest is not self-install: plugin.json ignored, agent is tier-routed and fails.
        check = self.check(self.run_verify())
        self.assertEqual(check["files"][".github/agents/auto-tune.agent.md"]["profile"], PROFILE_TIER_ROUTED)
        self.assertFalse(check["ok"])
        # Self-install, but a foreign plugin name.
        self.manifest_extra = {"install_mode": "self-install"}
        self.env.write("plugin.json", json.dumps({"name": "other", "agents": [".github/agents/auto-tune.agent.md"]}))
        check = self.check(self.run_verify())
        self.assertEqual(check["files"][".github/agents/auto-tune.agent.md"]["profile"], PROFILE_TIER_ROUTED)

    def test_plugin_global_passes_with_tier_and_fails_with_model_family(self) -> None:
        self.manifest_extra = {"install_mode": "self-install"}
        self.env.write("plugin.json", json.dumps({"name": "autoharness", "agents": ["./.github/agents/auto-tune.agent.md"]}))
        self.env.write(".github/agents/auto-tune.agent.md", PLUGIN_GLOBAL_AGENT)
        self.track(".github/agents/auto-tune.agent.md", "global agent definition")
        check = self.check(self.run_verify())
        self.assertTrue(check["ok"], check["errors"])
        self.assertEqual(check["files"][".github/agents/auto-tune.agent.md"]["profile"], PROFILE_PLUGIN_GLOBAL)
        self.env.write(".github/agents/auto-tune.agent.md", PLUGIN_GLOBAL_AGENT.replace("---\n\n#", "model_family: fam\n---\n\n#"))
        check = self.check(self.run_verify())
        self.assertFalse(check["ok"])
        self.assertIn(".github/agents/auto-tune.agent.md: FM_FORBIDDEN_KEY model_family", check["errors"])

    @unittest.skipUnless(_SYMLINKS, _SYMLINK_SKIP)
    def test_symlinked_plugin_json_escaping_workspace_is_never_read(self) -> None:
        self.manifest_extra = {"install_mode": "self-install"}
        outside = self.env.root / "outside-plugin.json"
        outside.write_text(
            json.dumps({"name": "autoharness", "agents": [".github/agents/auto-tune.agent.md"]}), encoding="utf-8"
        )
        os.symlink(outside, self.env.ws / "plugin.json")
        self.env.write(".github/agents/auto-tune.agent.md", PLUGIN_GLOBAL_AGENT)
        self.track(".github/agents/auto-tune.agent.md", "global agent definition")
        report = self.run_verify()
        plugin_warnings = [w for w in report["warnings"] if w.get("kind") == vw.FC_PLUGIN_WARNING_KIND]
        self.assertEqual(len(plugin_warnings), 1)
        check = self.check(report)
        self.assertEqual(check["files"][".github/agents/auto-tune.agent.md"]["profile"], PROFILE_TIER_ROUTED)

    def test_unknown_key_only_agent_passes_with_no_warning(self) -> None:
        self.env.write(".github/agents/hand.agent.md", CONFORMANT_AGENT.replace("---\n\n#", "custom_key: 1\n---\n\n#"))
        report = self.run_verify()
        check = self.check(report)
        self.assertTrue(check["ok"])
        self.assertEqual(self.fc_warnings(report), [])
        self.assertEqual(check["errors"], [])
        self.assertEqual(check["info"], [".github/agents/hand.agent.md: FM_UNKNOWN_KEY custom_key"])
        codes = [f["code"] for f in check["files"][".github/agents/hand.agent.md"]["findings"]]
        self.assertEqual(codes, ["FM_UNKNOWN_KEY"])

    @unittest.skipUnless(_SYMLINKS, _SYMLINK_SKIP)
    def test_escaping_symlink_untracked_skipped_and_managed_fails(self) -> None:
        outside = self.env.root / "outside.agent.md"
        outside.write_text(BARE_MODEL_AGENT, encoding="utf-8")
        (self.env.ws / ".github" / "agents").mkdir(parents=True)
        os.symlink(outside, self.env.ws / ".github" / "agents" / "untracked.agent.md")
        report = self.run_verify()
        check = self.check(report)
        self.assertTrue(check["ok"])
        self.assertNotIn(".github/agents/untracked.agent.md", check["files"])
        skipped = [w for w in self.fc_warnings(report) if w["path"] == ".github/agents/untracked.agent.md"]
        self.assertEqual(len(skipped), 1)

        os.symlink(outside, self.env.ws / ".github" / "agents" / "managed.agent.md")
        self.artifacts.append(_artifact(".github/agents/managed.agent.md", "global agent definition", "x"))
        check = self.check(self.run_verify())
        self.assertFalse(check["ok"])
        self.assertIn(".github/agents/managed.agent.md: FM_PATH_ESCAPE", check["errors"])

    def test_undecodable_file_gives_parse_error_without_crashing(self) -> None:
        # Full verify path with an undecodable managed skill (the pre-existing
        # agent-identity scan reads *.agent.md as UTF-8 and is out of scope).
        path = self.env.ws / ".github" / "skills" / "bad" / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"---\nname: \xff\xfe\n---\n")
        self.track(".github/skills/bad/SKILL.md", "global skill definition")
        check = self.check(self.run_verify())
        self.assertFalse(check["ok"])
        self.assertEqual(
            [f["code"] for f in check["files"][".github/skills/bad/SKILL.md"]["findings"]], [FM_PARSE_ERROR]
        )
        # Check level, undecodable agent.
        agent = self.env.ws / ".github" / "agents" / "bad.agent.md"
        agent.parent.mkdir(parents=True)
        agent.write_bytes(b"---\nname: \xff\xfe\n---\n")
        report: dict[str, Any] = {"warnings": [], "targeted_checks": {}, "checksum_scan": []}
        vw._add_frontmatter_conformity_check(
            report, self.env.workspace, self.env.autoharness_home, {"artifacts": []}, {}
        )
        check = self.check(report)
        self.assertTrue(check["ok"])
        self.assertEqual(
            [f["code"] for f in check["files"][".github/agents/bad.agent.md"]["findings"]], [FM_PARSE_ERROR]
        )
        self.assertEqual(
            [w["path"] for w in report["warnings"]],
            [".github/agents/bad.agent.md", ".github/skills/bad/SKILL.md"],
        )

    def test_no_agents_directory_is_ok_with_zero_files(self) -> None:
        report = self.run_verify()
        check = self.check(report)
        self.assertTrue(check["ok"])
        self.assertEqual(check["files"], {})
        # Overall verify may still fail on the legacy unconditional orchestrator_tier_fields (AS-F1).
        self.assertFalse(report["targeted_checks"]["orchestrator_tier_fields"]["ok"])

    def test_managed_nonconformant_agent_in_local_agents_dir_fails(self) -> None:
        self.profile = {
            "schema_version": "1.0.0",
            "distribution": {"is_global_tool": True, "local_agents_dir": "custom-agents"},
        }
        self.env.template("agents/local.agent.md.tmpl", CONFORMANT_AGENT)
        self.env.write("custom-agents/local.agent.md", BARE_MODEL_AGENT)
        self.track("custom-agents/local.agent.md", "agents/local.agent.md.tmpl")
        check = self.check(self.run_verify())
        self.assertFalse(check["ok"])
        self.assertIn("custom-agents/local.agent.md", check["files"])

    def test_markdown_report_carries_errors_info_and_warnings(self) -> None:
        self.env.write(".github/skills/install-harness/SKILL.md", _skill(None))
        self.track(".github/skills/install-harness/SKILL.md", "global skill definition")
        self.env.write(".github/agents/hand.agent.md", BARE_MODEL_AGENT.replace("---\n\n#", "custom_key: 1\n---\n\n#"))
        report = self.run_verify()
        check = self.check(report)
        self.assertTrue(check["errors"])
        self.assertTrue(check["info"])
        markdown = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
        for line in check["errors"] + check["info"]:
            self.assertIn(line, markdown)
        self.assertIn("  info: ", markdown)
        warnings = self.fc_warnings(report)
        self.assertTrue(warnings)
        for warning in warnings:
            self.assertIn(json.dumps(warning, ensure_ascii=False), markdown)

    def test_check_registered_once_after_render_loop(self) -> None:
        self.env.write(".github/agents/hand.agent.md", CONFORMANT_AGENT)
        real = vw._add_frontmatter_conformity_check
        observed: list[int] = []

        def _spy(report: dict[str, Any], *args: Any, **kwargs: Any) -> None:
            # The staging render loop has already populated `rendered`/`checksum_scan`.
            observed.append(len(report["checksum_scan"]))
            real(report, *args, **kwargs)

        self.env.template("agents/demo.agent.md.tmpl", CONFORMANT_AGENT)
        self.env.write(".github/agents/demo.agent.md", CONFORMANT_AGENT)
        self.track(".github/agents/demo.agent.md", "agents/demo.agent.md.tmpl")
        with mock.patch.object(vw, "_add_frontmatter_conformity_check", side_effect=_spy) as spy:
            self.run_verify()
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(observed, [1])

    def test_check_writes_nothing(self) -> None:
        self.env.write(".github/agents/hand.agent.md", BARE_MODEL_AGENT)
        self.env.write(".github/skills/demo/SKILL.md", _skill("demo"))

        def _snapshot() -> dict[str, tuple[int, bytes]]:
            return {
                p.relative_to(self.env.root).as_posix(): (p.stat().st_mtime_ns, p.read_bytes())
                for p in sorted(self.env.root.rglob("*"))
                if p.is_file()
            }

        before = _snapshot()
        report: dict[str, Any] = {"warnings": [], "targeted_checks": {}, "checksum_scan": [], "migration_proposals": []}
        vw._add_frontmatter_conformity_check(
            report, self.env.workspace, self.env.autoharness_home, {"artifacts": []}, {}
        )
        self.assertEqual(_snapshot(), before)

    def test_existing_model_routing_results_byte_identical_before_and_after(self) -> None:
        """INV-B3: the three *_model_routing_fields results are untouched by registration."""
        for name in ("_orchestrator", "_stage", "_ship"):
            self.env.write(f".github/agents/{name}.agent.md", BARE_MODEL_AGENT)
        self.env.write(".github/agents/_ship.agent.md", CONFORMANT_AGENT)
        keys = (
            "orchestrator_model_routing_fields",
            "stage_model_routing_fields",
            "ship_model_routing_fields",
        )
        with_check = self.run_verify()
        with mock.patch.object(vw, "_add_frontmatter_conformity_check", return_value=None):
            without_check = self.run_verify()
        self.assertIn("frontmatter_conformity", with_check["targeted_checks"])
        self.assertNotIn("frontmatter_conformity", without_check["targeted_checks"])
        for key in keys:
            self.assertEqual(
                json.dumps(with_check["targeted_checks"][key], sort_keys=True).encode("utf-8"),
                json.dumps(without_check["targeted_checks"][key], sort_keys=True).encode("utf-8"),
                key,
            )


class DogfoodFrontmatterConformityPinTests(unittest.TestCase):
    """Integration pin: this repository's own agents and skills conform (B2a, H-B10)."""

    def test_repository_frontmatter_conformity_ok(self) -> None:
        with tempfile.TemporaryDirectory() as staging:
            report = vw.verify_workspace(_ROOT, _ROOT, Path(staging))
        check = report["targeted_checks"]["frontmatter_conformity"]
        self.assertTrue(check["ok"], check["errors"])
        self.assertTrue(check["files"])
        self.assertIn(".github/agents/_ship.agent.md", check["files"])
        self.assertEqual(
            check["files"][".github/agents/auto-tune.agent.md"]["profile"], PROFILE_PLUGIN_GLOBAL
        )


if __name__ == "__main__":
    unittest.main()
