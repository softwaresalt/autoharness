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
    has_blocking_findings,
    parse_frontmatter,
    read_frontmatter,
)
from autoharness.verify_workspace import _derive_template_variables, _render_template

_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST = _ROOT / ".autoharness" / "harness-manifest.yaml"
_ADR_GENERATOR = _ROOT / "templates" / "community" / "agents" / "adr-generator.agent.md.tmpl"
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
                self.assertEqual(parsed.data.get("max_subagent_tier"), 2)
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
            self.assertEqual(parsed.data["model_provider"], "anthropic")

    def test_adr_generator_keeps_attribution_comments_inside_frontmatter(self) -> None:
        lines = _ADR_GENERATOR.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
        self.assertEqual(lines[0], "---")
        self.assertTrue(lines[1].startswith("# Source: "))
        self.assertTrue(lines[2].startswith("# License: "))


if __name__ == "__main__":
    unittest.main()
