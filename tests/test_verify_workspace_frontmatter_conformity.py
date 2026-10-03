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


if __name__ == "__main__":
    unittest.main()
