"""Structural tests for anchor review routing and review-gate contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ROOT_CONFIG_SCHEMA = _REPO_ROOT / "schemas" / "harness-config.schema.json"
_VERSIONED_CONFIG_SCHEMA = _REPO_ROOT / "schemas" / "harness-config" / "1.1.0.schema.json"
_CONFIG_TEMPLATE = _REPO_ROOT / "templates" / "harness-config.yaml.tmpl"
_VERIFY_HARNESS = _REPO_ROOT / ".github" / "skills" / "verify-harness" / "SKILL.md"
_ADVERSARIAL_AGENT = _REPO_ROOT / "templates" / "agents" / "adversarial-review.agent.md.tmpl"
_ADVERSARIAL_INSTRUCTIONS = _REPO_ROOT / "templates" / "instructions" / "adversarial-review.instructions.md.tmpl"
_PLAN_REVIEW = _REPO_ROOT / "templates" / "skills" / "plan-review" / "SKILL.md.tmpl"
_REVIEW = _REPO_ROOT / "templates" / "skills" / "review" / "SKILL.md.tmpl"
_PLAN_HARDEN = _REPO_ROOT / "templates" / "skills" / "plan-harden" / "SKILL.md.tmpl"
_HARVEST = _REPO_ROOT / "templates" / "skills" / "harvest" / "SKILL.md.tmpl"
_INSTALL_HARNESS = _REPO_ROOT / ".github" / "skills" / "install-harness" / "SKILL.md"
_REVIEW_TEMPLATES = _REPO_ROOT / "templates" / "agents" / "review"
_RESEARCH_TEMPLATES = _REPO_ROOT / "templates" / "agents" / "research"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    return json.loads(_read(path))


def _without_id(schema: dict) -> dict:
    clone = json.loads(json.dumps(schema))
    clone.pop("$id", None)
    return clone


class AnchorReviewConfigContractTests(unittest.TestCase):
    def test_root_and_versioned_harness_config_schemas_match_except_id(self) -> None:
        root = _load_json(_ROOT_CONFIG_SCHEMA)
        versioned = _load_json(_VERSIONED_CONFIG_SCHEMA)
        self.assertNotEqual(root.get("$id"), versioned.get("$id"))
        self.assertEqual(_without_id(root), _without_id(versioned))

    def test_anchor_review_route_validates_and_rejects_unknown_properties(self) -> None:
        schema = _load_json(_ROOT_CONFIG_SCHEMA)
        Draft7Validator.check_schema(schema)
        validator = Draft7Validator(schema)
        model_props = schema["properties"]["model_routing"]["properties"]
        self.assertIn("anchor_review", model_props)
        self.assertNotIn("additionalProperties", schema["properties"]["model_routing"])
        anchor_schema = model_props["anchor_review"]
        self.assertFalse(anchor_schema.get("additionalProperties", True))
        self.assertEqual(set(anchor_schema["required"]), {"model_provider", "model_family"})
        self.assertEqual(anchor_schema["properties"]["model_provider"]["default"], "openai")
        self.assertEqual(anchor_schema["properties"]["model_family"]["default"], "gpt-5.6-sol")
        self.assertEqual(anchor_schema["properties"]["reasoning_effort"]["default"], "high")

        valid = {
            "schema_version": "1.1.0",
            "model_routing": {
                "anchor_review": {
                    "model_provider": "openai",
                    "model_family": "gpt-5.6-sol",
                    "reasoning_effort": "high",
                }
            },
        }
        self.assertEqual(list(validator.iter_errors(valid)), [])

        invalid = {
            "schema_version": "1.1.0",
            "model_routing": {
                "anchor_review": {
                    "model_provider": "openai",
                    "model_family": "gpt-5.6-sol",
                    "unexpected": "not allowed",
                }
            },
        }
        self.assertFalse(validator.is_valid(invalid))

        custom_route = {
            "schema_version": "1.1.0",
            "model_routing": {
                "workspace_specific_review": {"model_provider": "local", "model_family": "custom"}
            },
        }
        self.assertTrue(validator.is_valid(custom_route))

    def test_harness_config_template_has_anchor_defaults_and_valid_yaml_when_reasoning_empty(self) -> None:
        text = _read(_CONFIG_TEMPLATE)
        for token in (
            "{{ANCHOR_REVIEW_PROVIDER}}",
            "{{ANCHOR_REVIEW_FAMILY}}",
            "{{ANCHOR_REVIEW_REASONING_EFFORT}}",
        ):
            self.assertIn(token, text)
        match = re.search(r"(?m)^  anchor_review:\n(?:    [^\n]+\n)+", text)
        self.assertIsNotNone(match, "model_routing.anchor_review block missing")
        rendered = match.group(0)
        rendered = rendered.replace("{{ANCHOR_REVIEW_PROVIDER}}", "openai")
        rendered = rendered.replace("{{ANCHOR_REVIEW_FAMILY}}", "gpt-5.6-sol")
        rendered = rendered.replace("{{ANCHOR_REVIEW_REASONING_EFFORT}}", "")
        parsed = yaml.safe_load("model_routing:\n" + rendered)
        self.assertEqual(parsed["model_routing"]["anchor_review"]["model_provider"], "openai")
        self.assertEqual(parsed["model_routing"]["anchor_review"]["model_family"], "gpt-5.6-sol")
        self.assertEqual(parsed["model_routing"]["anchor_review"]["reasoning_effort"], "")


class AnchorReviewSkillRoutingTests(unittest.TestCase):
    def test_verify_harness_loads_anchor_from_workspace_config_without_template_placeholders(self) -> None:
        text = _read(_VERIFY_HARNESS)
        self.assertNotIn("{{ANCHOR_REVIEW_", text)
        self.assertIn("model_routing.anchor_review", text)
        self.assertIn("Anchor Reviewer", text)
        self.assertIn("declared fallback", text)
        self.assertIn("`overlay-coherence` domain value", text)
        self.assertIn("Resolve the effective anchor route first", text)
        self.assertIn("never treat an omitted", text)
        self.assertIn("`anchor_review` config key by itself as degradation", text)

    def test_adversarial_review_templates_have_rendered_anchor_placeholders_and_preserve_consensus(self) -> None:
        agent = _read(_ADVERSARIAL_AGENT)
        instructions = _read(_ADVERSARIAL_INSTRUCTIONS)
        for text in (agent, instructions):
            self.assertIn("{{ANCHOR_REVIEW_PROVIDER}}", text)
            self.assertIn("{{ANCHOR_REVIEW_FAMILY}}", text)
            self.assertIn("{{ANCHOR_REVIEW_REASONING_EFFORT}}", text)
            self.assertIn("Anchor Reviewer", text)
            self.assertIn("consensus", text.lower())
        self.assertIn('anchor_review_provider: "{{ANCHOR_REVIEW_PROVIDER}}"', agent)
        self.assertIn('anchor_review_family: "{{ANCHOR_REVIEW_FAMILY}}"', agent)
        for count in ("| 2 |", "| 3 |", "| 4 (default with anchor) |", "| 5 |"):
            self.assertIn(count, agent)
        self.assertIn("including `anchor_review`", agent)
        self.assertIn("anchor_reasoning_effort", agent)
        self.assertIn("pass the reasoning effort when non-empty", agent)
        for text in (agent, instructions):
            self.assertIn("Plurality", text)
            self.assertIn("more than one", text)
            self.assertIn("strict majority", text)
        self.assertIn("every agreement count from 1 to", agent)
        self.assertIn("majority, plurality, unique", agent)

    def test_plan_and_code_review_route_one_persona_to_anchor_when_available(self) -> None:
        for path in (_PLAN_REVIEW, _REVIEW):
            text = _read(path)
            self.assertIn("anchor reviewer", text.lower(), path.name)
            self.assertIn("model_routing.anchor_review", text, path.name)
            self.assertIn("declared degradation", text.lower(), path.name)
            self.assertIn("same rubric", text.lower(), path.name)


class PlanReviewGateContractTests(unittest.TestCase):
    def test_plan_review_backport_sections_are_parameterized_and_machine_readable(self) -> None:
        text = _read(_PLAN_REVIEW)
        for heading in (
            "## Dispatch Capability and Declared Degradation",
            "## Relationship to P-012",
            "## Persona Rubric Adapter",
        ):
            self.assertIn(heading, text)
        for token in ("{{DOCS_PLANS}}", "{{DOCS_COMPOUND}}", "{{PRIMARY_LANGUAGE}}", "{{PRIMARY_LANGUAGE_LOWER}}"):
            self.assertIn(token, text)
        self.assertIn("dispatch_mode:", text)
        self.assertIn("decision:", text)
        self.assertIn("same-model-declared-degradation", text)
        self.assertIn("single-agent-declared-degradation", text)
        self.assertNotIn("docs/exec-plans", text)
        self.assertNotIn("go-reviewer", text.lower())
        self.assertNotIn("backlogit", text.lower())

    def test_persona_identity_mapping_uses_installed_paths_and_existing_templates(self) -> None:
        plan_review = _read(_PLAN_REVIEW)
        install = _read(_INSTALL_HARNESS)
        expected_paths = {
            ".github/agents/subagents/constitution-reviewer.agent.md": _REVIEW_TEMPLATES / "constitution-reviewer.agent.md.tmpl",
            ".github/agents/subagents/{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md": _REVIEW_TEMPLATES / "technology-reviewer.agent.md.tmpl",
            ".github/agents/subagents/scope-boundary-auditor.agent.md": _REVIEW_TEMPLATES / "scope-boundary-auditor.agent.md.tmpl",
            ".github/agents/subagents/learnings-researcher.agent.md": _RESEARCH_TEMPLATES / "learnings-researcher.agent.md.tmpl",
        }
        combined = plan_review + "\n" + install
        for installed_path, template_path in expected_paths.items():
            self.assertIn(installed_path, combined)
            self.assertTrue(template_path.exists(), template_path)

    def test_plan_harden_and_harvest_fail_closed_on_review_gate_markers(self) -> None:
        plan_harden = _read(_PLAN_HARDEN)
        harvest = _read(_HARVEST)
        self.assertIn("review-gate capability", plan_harden.lower())
        self.assertIn("dispatch_mode:", plan_harden)
        self.assertIn("decision:", plan_harden)
        self.assertIn("dispatch_mode:", harvest)
        self.assertIn("decision:", harvest)
        self.assertIn("FAIL", harvest)
        self.assertIn("ADVISORY", harvest)
        self.assertIn("explicit authorization", harvest.lower())


class AnchorReviewVariableDocumentationTests(unittest.TestCase):
    def test_install_harness_documents_every_anchor_review_variable(self) -> None:
        text = _read(_INSTALL_HARNESS)
        for token in (
            "{{ANCHOR_REVIEW_PROVIDER}}",
            "{{ANCHOR_REVIEW_FAMILY}}",
            "{{ANCHOR_REVIEW_REASONING_EFFORT}}",
        ):
            self.assertIn(token, text)
        self.assertIn("config.model_routing.anchor_review.model_provider", text)
        self.assertIn("config.model_routing.anchor_review.model_family", text)
        self.assertIn("gpt-5.6-sol", text)
        self.assertIn("openai", text)
        self.assertIn("degradation", text.lower())


if __name__ == "__main__":
    unittest.main()