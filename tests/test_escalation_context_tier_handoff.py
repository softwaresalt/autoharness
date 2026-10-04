"""P-013.6 escalation handoff carries the resolved ``context_tier`` (194-F, C6b, 194.011-T).

Plan unit C6b (docs/plans/2026-09-27-context-tier-model-routing-plan.md, review
AN-F1/AN-F9): the escalation payload gains a SEPARATE
``resolved_escalation_context_tier`` field while the ``resolved_escalation_route``
``(model_family, model_provider, reasoning_effort)`` tuple stays unchanged, so the
same-route guard and every tuple consumer are untouched (D-C3, INV-C5). Covers:

  * the payload-contract row in the escalation-protocol template and mirror, with the
    ``resolved_escalation_route`` row still naming exactly three fields;
  * the P-013.6 text (template and mirror): ``context_tier`` is excluded from the
    same-route guard, and an unhonorable escalation ``context_tier`` records
    ``ROUTING_DEGRADED: context_tier`` without blocking the handoff;
  * the Stage and Ship "Resolve the escalation route" step carries the role-scoped
    ``{{ESCALATION_CONTEXT_TIER}}`` (templates) and the field (templates and mirrors);
  * rendering Stage and Ship under the dogfood config gives ``default``;
  * a per-role fixture renders Stage ``long_context`` and Ship ``default`` (AN-F9);
  * rendered Stage and Ship frontmatter still passes B1 in installed mode.
"""

from __future__ import annotations

import copy
import re
import unittest
import unittest.mock as _mock
from pathlib import Path
from typing import Any

import yaml

from autoharness.frontmatter_contract import (
    MODE_INSTALLED,
    check_agent,
    has_blocking_findings,
    parse_frontmatter,
)
from autoharness.verify_workspace import (
    _compose_artifact_variables,
    _derive_template_variables,
    _render_template,
    _resolve_artifact_role,
)

_ROOT = Path(__file__).resolve().parents[1]
_AUTOHARNESS = _ROOT / ".autoharness"

_ESCALATION_TEMPLATE = _ROOT / "templates/instructions/escalation-protocol.instructions.md.tmpl"
_ESCALATION_MIRROR = _ROOT / ".github/instructions/escalation-protocol.instructions.md"
_POLICY_TEMPLATE = _ROOT / "templates/policies/workflow-policies.md.tmpl"
_POLICY_MIRROR = _ROOT / ".github/policies/workflow-policies.md"
_STAGE_TEMPLATE = _ROOT / "templates/agents/_stage.agent.md.tmpl"
_SHIP_TEMPLATE = _ROOT / "templates/agents/_ship.agent.md.tmpl"
_STAGE_MIRROR_REL = ".github/agents/_stage.agent.md"
_SHIP_MIRROR_REL = ".github/agents/_ship.agent.md"

_FIELD = "resolved_escalation_context_tier"
_DEGRADED = "ROUTING_DEGRADED: context_tier"
_RESOLVED_PHRASE = "the escalation `context_tier` resolves to `{tier}`"
_PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(markdown: str, heading_fragment: str) -> str:
    """Return the Markdown section whose heading contains ``heading_fragment``,
    bounded by the next heading of the same or a higher level."""
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        heading = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if not heading or heading_fragment not in heading.group(2):
            continue
        level = len(heading.group(1))
        end = len(lines)
        for candidate_index in range(index + 1, len(lines)):
            candidate = re.match(r"^(#{1,6})\s+", lines[candidate_index].strip())
            if candidate and len(candidate.group(1)) <= level:
                end = candidate_index
                break
        return "\n".join(lines[index:end])
    raise AssertionError(f"section {heading_fragment!r} not found")


def _escalation_step_section(text: str) -> str:
    return _section(text, "Escalation Protocol —")


def _load(name: str) -> dict[str, Any]:
    return yaml.safe_load((_AUTOHARNESS / name).read_text(encoding="utf-8")) or {}


def _render(template: Path, installed_rel: str, config: dict[str, Any]) -> str:
    manifest = _load("harness-manifest.yaml")
    profile = _load("workspace-profile.yaml")
    registry = _load("backlog-registry.yaml")
    model_routing = config.get("model_routing") or {}
    with _mock.patch(
        "autoharness.verify_workspace._resolve_default_branch", return_value="main"
    ):
        base = _derive_template_variables(_ROOT, manifest, config, profile, registry)
    variables = _compose_artifact_variables(
        base, model_routing, _resolve_artifact_role(installed_rel)
    )
    return _render_template(_read(template), variables)


def _per_role_fixture(flat_context_tier: str | None = None) -> dict[str, Any]:
    """Dogfood config with ``stage.escalation.context_tier: long_context`` and
    ``ship.escalation.context_tier: default`` over the flat escalation family."""
    config = copy.deepcopy(_load("config.yaml"))
    routing = config.setdefault("model_routing", {})
    flat = routing.setdefault("escalation", {})
    flat.setdefault("model_family", "gpt-6-sol")
    if flat_context_tier is not None:
        flat["context_tier"] = flat_context_tier
    routing.setdefault("stage", {})["escalation"] = {"context_tier": "long_context"}
    routing.setdefault("ship", {})["escalation"] = {"context_tier": "default"}
    return config


class EscalationPayloadContractTests(unittest.TestCase):
    def _payload_rows(self, text: str) -> dict[str, str]:
        rows: dict[str, str] = {}
        for line in text.splitlines():
            match = re.match(r"^\| `([a-z_]+)` \|", line)
            if match:
                rows[match.group(1)] = line
        return rows

    def test_payload_contract_names_separate_context_tier_field(self) -> None:
        for path in (_ESCALATION_TEMPLATE, _ESCALATION_MIRROR):
            with self.subTest(path=path.name):
                rows = self._payload_rows(_read(path))
                self.assertIn(_FIELD, rows)
                row = rows[_FIELD]
                self.assertIn("`default`", row)
                self.assertIn("same-route", row)
                self.assertIn(_DEGRADED, row)

    def test_resolved_escalation_route_row_still_names_exactly_three_fields(self) -> None:
        for path in (_ESCALATION_TEMPLATE, _ESCALATION_MIRROR):
            with self.subTest(path=path.name):
                row = self._payload_rows(_read(path))["resolved_escalation_route"]
                tuple_match = re.search(r"`\(([^)]*)\)`", row)
                self.assertIsNotNone(tuple_match, row)
                fields = [field.strip() for field in tuple_match.group(1).split(",")]
                self.assertEqual(
                    fields, ["model_family", "model_provider", "reasoning_effort"]
                )
                self.assertNotIn("context_tier", row)

    def test_same_route_definition_excludes_context_tier(self) -> None:
        for path in (_ESCALATION_TEMPLATE, _ESCALATION_MIRROR):
            with self.subTest(path=path.name):
                section = _normalize(_section(_read(path), "`ESCALATION_DEGRADED`"))
                self.assertIn(
                    _normalize("`context_tier` is excluded from the same-route comparison"),
                    section,
                )
                self.assertIn(_DEGRADED, section)

    def test_terminal_handoff_records_both_fields(self) -> None:
        for path in (_ESCALATION_TEMPLATE, _ESCALATION_MIRROR):
            with self.subTest(path=path.name):
                section = _normalize(_section(_read(path), "Terminal Engram Handoff"))
                self.assertIn(
                    _normalize("records the route in the payload's `resolved_escalation_route` field"),
                    section,
                )
                self.assertIn(f"`{_FIELD}`", section)


class P0136PolicyTests(unittest.TestCase):
    def _p0136(self, path: Path) -> str:
        return _section(_read(path), "P-013.6")

    def test_policy_states_context_tier_exclusion_and_degraded_fallback(self) -> None:
        for path in (_POLICY_TEMPLATE, _POLICY_MIRROR):
            with self.subTest(path=path.name):
                section = _normalize(self._p0136(path))
                self.assertIn(f"`{_FIELD}`", section)
                self.assertIn(
                    _normalize("`context_tier` is excluded from the same-route guard"),
                    section,
                )
                self.assertIn(_DEGRADED, section)
                self.assertIn("without blocking the handoff", section)

    def test_p0136_section_identical_between_template_and_mirror(self) -> None:
        self.assertEqual(self._p0136(_POLICY_TEMPLATE), self._p0136(_POLICY_MIRROR))

    def test_version_history_row(self) -> None:
        for path in (_POLICY_TEMPLATE, _POLICY_MIRROR):
            with self.subTest(path=path.name):
                rows = [
                    line for line in _read(path).splitlines() if line.startswith("| 1.31.0 ")
                ]
                self.assertEqual(len(rows), 1, rows)
                self.assertIn("P-013.6", rows[0])
                self.assertIn("194.011-T", rows[0])


class AgentEscalationStepTests(unittest.TestCase):
    def test_templates_bind_role_scoped_variable(self) -> None:
        for template in (_STAGE_TEMPLATE, _SHIP_TEMPLATE):
            with self.subTest(template=template.name):
                section = _normalize(_escalation_step_section(_read(template)))
                self.assertIn(
                    _normalize(_RESOLVED_PHRASE.format(tier="{{ESCALATION_CONTEXT_TIER}}")),
                    section,
                )
                self.assertIn(f"`{_FIELD}`", section)
                self.assertIn(_DEGRADED, section)
                self.assertIn(
                    _normalize("record it in the compiled payload's `resolved_escalation_route` field"),
                    section,
                )

    def test_mirrors_carry_field_and_dogfood_value(self) -> None:
        for rel in (_STAGE_MIRROR_REL, _SHIP_MIRROR_REL):
            with self.subTest(mirror=rel):
                section = _normalize(_escalation_step_section(_read(_ROOT / rel)))
                self.assertIn(_normalize(_RESOLVED_PHRASE.format(tier="default")), section)
                self.assertIn(f"`{_FIELD}`", section)
                self.assertIn(_DEGRADED, section)


class RenderedEscalationContextTierTests(unittest.TestCase):
    def _assert_rendered(self, config: dict[str, Any], expected: dict[str, str]) -> None:
        targets = {"stage": (_STAGE_TEMPLATE, _STAGE_MIRROR_REL), "ship": (_SHIP_TEMPLATE, _SHIP_MIRROR_REL)}
        for role, tier in expected.items():
            template, rel = targets[role]
            with self.subTest(role=role, tier=tier):
                rendered = _render(template, rel, config)
                section = _escalation_step_section(rendered)
                self.assertEqual(_PLACEHOLDER.findall(section), [])
                self.assertIn(
                    _normalize(_RESOLVED_PHRASE.format(tier=tier)), _normalize(section)
                )
                parsed = parse_frontmatter(rendered, MODE_INSTALLED)
                findings = check_agent(parsed, "tier-routed", MODE_INSTALLED)
                self.assertFalse(has_blocking_findings(findings), findings)

    def test_dogfood_config_renders_default(self) -> None:
        self._assert_rendered(
            copy.deepcopy(_load("config.yaml")), {"stage": "default", "ship": "default"}
        )

    def test_per_role_fixture_renders_role_scoped_values(self) -> None:
        self._assert_rendered(
            _per_role_fixture(), {"stage": "long_context", "ship": "default"}
        )

    def test_per_role_fixture_ship_default_comes_from_nested_override(self) -> None:
        # The flat route declares long_context, so Ship's `default` can only
        # come from its own nested `ship.escalation.context_tier` (AN-F9).
        self._assert_rendered(
            _per_role_fixture(flat_context_tier="long_context"),
            {"stage": "long_context", "ship": "default"},
        )


if __name__ == "__main__":
    unittest.main()
