"""Repository-wide frontmatter conformity test (193-F B3 agents half, B4 skills half).

Runs the B1 contract (``autoharness.frontmatter_contract``) in template mode
over every agent template and in installed mode over every installed agent,
selecting the agent profile from the root ``plugin.json`` ``agents[]`` via
``agent_profile_for`` (plan docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md).
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

import yaml

from autoharness.frontmatter_contract import (
    MODE_INSTALLED,
    MODE_TEMPLATE,
    PROFILE_PLUGIN_GLOBAL,
    ROUTE_VALUE_KEYS,
    agent_profile_for,
    check_agent,
    check_skill,
    has_blocking_findings,
    parse_frontmatter,
    read_frontmatter,
)
from autoharness.verify_workspace import _derive_template_variables, _render_template

_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST = _ROOT / ".autoharness" / "harness-manifest.yaml"
_ADR_GENERATOR = _ROOT / "templates" / "community" / "agents" / "adr-generator.agent.md.tmpl"
_ADVERSARIAL_REVIEW = _ROOT / "templates" / "agents" / "adversarial-review.agent.md.tmpl"
_PLUGIN_GLOBAL_AGENTS = (
    ".github/agents/auto-tune.agent.md",
    ".github/agents/auto-mergeinstall.agent.md",
)
_TIER_STATEMENT = re.compile(r"operates at \*\*Tier (\d+)")
_PLACEHOLDER = re.compile(r"\{\{[^{}]*\}\}")


def _rel(path: Path) -> str:
    return path.relative_to(_ROOT).as_posix()


def _plugin_agents() -> list[str]:
    data = json.loads((_ROOT / "plugin.json").read_text(encoding="utf-8"))
    return [str(item) for item in data.get("agents") or []]


def _staged_blob_sha256(path: Path) -> str:
    """SHA-256 of the LF-normalized blob (IM-12 / CR-F1: working tree may be CRLF)."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _format(failures: dict[str, list[tuple[str, str]]]) -> str:
    return "\n".join(f"{path}: {codes}" for path, codes in sorted(failures.items()))


class AgentFrontmatterConformityTests(unittest.TestCase):
    def test_agent_templates_conform_in_template_mode(self) -> None:
        plugin_agents = _plugin_agents()
        templates = sorted((_ROOT / "templates").rglob("*.agent.md.tmpl"))
        self.assertTrue(templates)
        self.assertIn(_ADR_GENERATOR, templates)
        failures: dict[str, list[tuple[str, str]]] = {}
        for path in templates:
            findings = check_agent(
                read_frontmatter(path, MODE_TEMPLATE),
                agent_profile_for(_rel(path), plugin_agents),
                MODE_TEMPLATE,
            )
            if has_blocking_findings(findings):
                failures[_rel(path)] = [(f.code, f.key) for f in findings if not f.informational]
        self.assertEqual(failures, {}, _format(failures))

    def test_installed_agents_conform_in_installed_mode(self) -> None:
        plugin_agents = _plugin_agents()
        agents = sorted((_ROOT / ".github" / "agents").rglob("*.agent.md"))
        self.assertTrue(agents)
        failures: dict[str, list[tuple[str, str]]] = {}
        for path in agents:
            findings = check_agent(
                read_frontmatter(path, MODE_INSTALLED),
                agent_profile_for(_rel(path), plugin_agents),
                MODE_INSTALLED,
            )
            if has_blocking_findings(findings):
                failures[_rel(path)] = [(f.code, f.key) for f in findings if not f.informational]
        self.assertEqual(failures, {}, _format(failures))

    def test_plugin_global_agents_are_selected_and_carry_no_route_values(self) -> None:
        plugin_agents = _plugin_agents()
        self.assertEqual(sorted(plugin_agents), sorted(_PLUGIN_GLOBAL_AGENTS))
        for rel in _PLUGIN_GLOBAL_AGENTS:
            with self.subTest(agent=rel):
                self.assertEqual(agent_profile_for(rel, plugin_agents), PROFILE_PLUGIN_GLOBAL)
                parsed = read_frontmatter(_ROOT / rel, MODE_INSTALLED)
                self.assertIsNone(parsed.error)
                # Tier 3: verify-harness dispatches its Tier 3 Reviewer A.
                self.assertEqual(parsed.data.get("max_subagent_tier"), 3)
                self.assertEqual(parsed.data.get("subagent_depth"), 2)
                self.assertFalse(set(parsed.data) & ROUTE_VALUE_KEYS)

    def test_plugin_global_agent_body_declares_exactly_one_tier(self) -> None:
        """AS-F4: the body Tier statement is the base tier; unrelated to max_subagent_tier."""
        for rel in _PLUGIN_GLOBAL_AGENTS:
            with self.subTest(agent=rel):
                text = (_ROOT / rel).read_text(encoding="utf-8")
                tiers = _TIER_STATEMENT.findall(text)
                self.assertEqual(len(tiers), 1, tiers)
                self.assertIn(int(tiers[0]), (1, 2, 3))

    def test_plugin_global_manifest_checksums_match_staged_blobs(self) -> None:
        manifest = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
        by_path = {item.get("path"): item for item in manifest.get("artifacts") or []}
        for rel in _PLUGIN_GLOBAL_AGENTS:
            with self.subTest(agent=rel):
                self.assertIn(rel, by_path)
                self.assertEqual(by_path[rel].get("checksum"), _staged_blob_sha256(_ROOT / rel))

    def test_adversarial_review_renders_conformant_with_empty_config(self) -> None:
        """Empty config renders empty alt/anchor review routes; installed mode must accept them."""
        content = _ADVERSARIAL_REVIEW.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            variables = _derive_template_variables(Path(tmp), {}, {}, {}, {})
        # install-harness documents an empty-string default for the ALT_REVIEW_*
        # variables when config.model_routing.alt_review is unset.
        variables.setdefault("ALT_REVIEW_PROVIDER", "")
        variables.setdefault("ALT_REVIEW_FAMILY", "")
        rendered = _render_template(content, variables)
        self.assertEqual(_PLACEHOLDER.findall(rendered.split("\n---", 1)[0]), [])
        parsed = parse_frontmatter(rendered, MODE_INSTALLED)
        self.assertIsNone(parsed.error)
        empty_review_keys = [
            key for key in ("alt_review_family", "anchor_review_family") if parsed.data.get(key) == ""
        ]
        self.assertTrue(empty_review_keys, "expected at least one review family to render empty")
        findings = check_agent(parsed, "tier-routed", MODE_INSTALLED)
        self.assertFalse(has_blocking_findings(findings), findings)

    def test_adr_generator_renders_conformant(self) -> None:
        """H-B9: TIER_2_* resolve for a community agent and the render passes installed mode."""
        content = _ADR_GENERATOR.read_text(encoding="utf-8")
        for variable in ("TIER_2_FAMILY", "TIER_2_PROVIDER", "TIER_2_REASONING_EFFORT"):
            self.assertTrue("{{" + variable + "}}" in content, f"adr-generator lacks {{{{{variable}}}}}")
        configs = {
            "default": {},
            "explicit": {
                "model_routing": {
                    "tier2": {
                        "model_family": "claude-sonnet-5",
                        "model_provider": "anthropic",
                        "reasoning_effort": "high",
                    }
                }
            },
        }
        # Community template variables are recorded in variables_used by install-harness
        # when the operator selects the community template (install-harness Step 1.3a).
        manifest = {"variables_used": {"ADR_DIRECTORY": "docs/adrs"}}
        checked: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            for label, config in configs.items():
                with self.subTest(config=label):
                    variables = _derive_template_variables(Path(tmp), manifest, config, {}, {})
                    rendered = _render_template(content, variables)
                    self.assertEqual(_PLACEHOLDER.findall(rendered), [])
                    parsed = parse_frontmatter(rendered, MODE_INSTALLED)
                    findings = check_agent(parsed, "tier-routed", MODE_INSTALLED)
                    self.assertFalse(has_blocking_findings(findings), findings)
                    self.assertEqual(parsed.data["max_subagent_tier"], 2)
                    self.assertEqual(parsed.data["subagent_depth"], 0)
                    self.assertEqual(parsed.data["model_family"], "claude-sonnet-5")
                    if label == "explicit":
                        self.assertEqual(parsed.data["model_provider"], "anthropic")
                    checked.append(label)
        # Guard against a vacuous pass: every config must have been rendered and checked.
        self.assertEqual(checked, list(configs))

    def test_adr_generator_keeps_attribution_comments_inside_frontmatter(self) -> None:
        lines = _ADR_GENERATOR.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
        self.assertEqual(lines[0], "---")
        self.assertTrue(lines[1].startswith("# Source: "))
        self.assertTrue(lines[2].startswith("# License: "))


class SkillFrontmatterConformityTests(unittest.TestCase):
    """B4 (193.003-T): skills carry name == directory and no routing key (P-013.5)."""

    # 18 skill templates that lacked ``name:`` before 193.003-T (all 13 community
    # skill templates already carried it).
    REMEDIATED_TEMPLATES = (
        "brainstorm",
        "build-feature",
        "compact-context",
        "compound",
        "compound-refresh",
        "deliberate",
        "evolve",
        "file-lock",
        "fix-ci",
        "impl-plan",
        "learn",
        "observe",
        "operational-closure",
        "plan-harden",
        "runtime-verification",
        "safety-modes",
        "skill-search",
        "spike",
    )
    # Nine template-rendered installed skills (render parity with the template edit, H-B8).
    TEMPLATE_RENDERED_INSTALLED = (
        "compact-context",
        "deliberate",
        "file-lock",
        "fix-ci",
        "impl-plan",
        "operational-closure",
        "plan-harden",
        "runtime-verification",
        "spike",
    )
    # Four ``global skill definition`` sources.
    SOURCE_INSTALLED = ("install-harness", "tune-harness", "verify-harness", "workspace-discovery")

    def _check_all(self, paths: list[Path], mode: str) -> dict[str, list[tuple[str, str]]]:
        failures: dict[str, list[tuple[str, str]]] = {}
        for path in paths:
            findings = check_skill(read_frontmatter(path, mode), path.parent.name, mode)
            if has_blocking_findings(findings):
                failures[_rel(path)] = [(f.code, f.key) for f in findings if not f.informational]
        return failures

    def test_skill_templates_conform_in_template_mode(self) -> None:
        templates = sorted((_ROOT / "templates").rglob("SKILL.md.tmpl"))
        self.assertTrue(templates)
        failures = self._check_all(templates, MODE_TEMPLATE)
        self.assertEqual(failures, {}, _format(failures))

    def test_installed_skills_conform_in_installed_mode(self) -> None:
        skills = sorted((_ROOT / ".github" / "skills").glob("*/SKILL.md"))
        self.assertTrue(skills)
        failures = self._check_all(skills, MODE_INSTALLED)
        self.assertEqual(failures, {}, _format(failures))

    def _first_key_line(self, path: Path) -> str:
        lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
        self.assertEqual(lines[0], "---", _rel(path))
        return next(line for line in lines[1:] if not line.startswith("#"))

    def test_remediated_name_is_first_frontmatter_key(self) -> None:
        for name in self.REMEDIATED_TEMPLATES:
            with self.subTest(template=name):
                path = _ROOT / "templates" / "skills" / name / "SKILL.md.tmpl"
                self.assertEqual(self._first_key_line(path), f"name: {name}")
        for name in self.TEMPLATE_RENDERED_INSTALLED + self.SOURCE_INSTALLED:
            with self.subTest(installed=name):
                path = _ROOT / ".github" / "skills" / name / "SKILL.md"
                self.assertEqual(self._first_key_line(path), f"name: {name}")

    def test_template_rendered_skills_keep_name_render_parity(self) -> None:
        for name in self.TEMPLATE_RENDERED_INSTALLED:
            with self.subTest(skill=name):
                self.assertIn(name, self.REMEDIATED_TEMPLATES)
                template = _ROOT / "templates" / "skills" / name / "SKILL.md.tmpl"
                installed = _ROOT / ".github" / "skills" / name / "SKILL.md"
                self.assertEqual(self._first_key_line(template), self._first_key_line(installed))

    def test_remediated_skill_manifest_checksums_match_staged_blobs(self) -> None:
        manifest = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
        by_path = {item.get("path"): item for item in manifest.get("artifacts") or []}
        for name in self.TEMPLATE_RENDERED_INSTALLED + self.SOURCE_INSTALLED:
            rel = f".github/skills/{name}/SKILL.md"
            with self.subTest(skill=rel):
                self.assertIn(rel, by_path)
                self.assertEqual(by_path[rel].get("checksum"), _staged_blob_sha256(_ROOT / rel))
        for name in self.SOURCE_INSTALLED:
            self.assertEqual(
                by_path[f".github/skills/{name}/SKILL.md"].get("template"), "global skill definition"
            )
        for name in self.TEMPLATE_RENDERED_INSTALLED:
            self.assertEqual(
                by_path[f".github/skills/{name}/SKILL.md"].get("template"), f"skills/{name}/SKILL.md.tmpl"
            )


if __name__ == "__main__":
    unittest.main()
