"""Role-bound pipeline agent render tests (194-F, C4a, 194.005-T).

Plan unit C4a (docs/plans/2026-09-27-context-tier-model-routing-plan.md): the
Ship and Stage agent templates bind their routing frontmatter to the P-013.5
role variables (``{{SHIP_*}}`` / ``{{STAGE_*}}``, including ``*_CONTEXT_TIER``),
which is the durable Ship pin. Covers:

  * placeholder discipline: the templates carry the role variables, never a
    literal ``long_context`` (Core Rule 3);
  * rendered-candidate validation (H-C6): each template is rendered with
    ``verify_workspace._render_template`` over ``_compose_artifact_variables(
    _derive_template_variables(...), model_routing, role)`` under three
    configs -- this repository's config, a config with no role routes, and a
    config holding the fresh-install Ship seed -- and the rendered frontmatter
    passes B1 ``check_agent(..., "tier-routed", "installed")`` with zero
    non-informational findings;
  * the installed mirrors carry the matching ``context_tier`` values with
    their ``model_*`` values unchanged (D-C6 binding);
  * the dogfood config's explicit Ship route declares ``long_context`` and the
    manifest records the refreshed checksums and ``config_hash``.

``max_subagent_tier`` is deliberately NOT changed by this unit: the operator
held it at its current values (Ship template 2, Ship mirror 3, Stage 3) while
the ceiling conflict is deliberated (stash 9F6AC6B3), superseding ruling 5b.
"""

from __future__ import annotations

import copy
import hashlib
import re
import tempfile
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
_SHIP_TEMPLATE = _ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
_STAGE_TEMPLATE = _ROOT / "templates" / "agents" / "_stage.agent.md.tmpl"
_SHIP_MIRROR_REL = ".github/agents/_ship.agent.md"
_STAGE_MIRROR_REL = ".github/agents/_stage.agent.md"
_CONFIG_REL = ".autoharness/config.yaml"
_PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")
_ROUTE_KEYS = ("model_family", "model_provider", "reasoning_effort", "context_tier")

# Fresh-install Ship seed (install-harness Step 1.2, H-C3; C3b).
_FRESH_INSTALL_SHIP_SEED = {
    "model_family": "gpt-6-luna",
    "model_provider": "openai",
    "reasoning_effort": "xhigh",
    "context_tier": "long_context",
}

_CONFIG_DOGFOOD = "dogfood"
_CONFIG_ROLELESS = "no-role-routes"
_CONFIG_SEED = "fresh-install-seed"


def _load(name: str) -> dict[str, Any]:
    return yaml.safe_load((_AUTOHARNESS / name).read_text(encoding="utf-8")) or {}


def _lf_sha256(path: Path) -> str:
    """SHA-256 of the LF-normalized blob (IM-12: the working tree may be CRLF)."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _config_for(label: str) -> dict[str, Any]:
    config = copy.deepcopy(_load("config.yaml"))
    routing = config.setdefault("model_routing", {})
    if label == _CONFIG_ROLELESS:
        routing.pop("ship", None)
        routing.pop("stage", None)
    elif label == _CONFIG_SEED:
        routing["ship"] = dict(_FRESH_INSTALL_SHIP_SEED)
    elif label != _CONFIG_DOGFOOD:
        raise ValueError(label)
    return config


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
    return _render_template(template.read_text(encoding="utf-8"), variables)


def _frontmatter_block(text: str) -> str:
    return text.split("\n---", 1)[0]


class TemplateBindingTests(unittest.TestCase):
    def _assert_bound(self, template: Path, prefix: str) -> None:
        block = _frontmatter_block(template.read_text(encoding="utf-8"))
        expected = {
            "model_family": f'model_family: "{{{{{prefix}_FAMILY}}}}"',
            "model_provider": f'model_provider: "{{{{{prefix}_PROVIDER}}}}"',
            "reasoning_effort": f'reasoning_effort: "{{{{{prefix}_REASONING_EFFORT}}}}"',
            "context_tier": f'context_tier: "{{{{{prefix}_CONTEXT_TIER}}}}"',
        }
        lines = block.splitlines()
        for key, line in expected.items():
            with self.subTest(template=template.name, key=key):
                self.assertIn(line, lines)

    def test_ship_template_binds_ship_role_variables(self) -> None:
        self._assert_bound(_SHIP_TEMPLATE, "SHIP")

    def test_stage_template_binds_stage_role_variables(self) -> None:
        self._assert_bound(_STAGE_TEMPLATE, "STAGE")

    def test_templates_carry_no_literal_long_context(self) -> None:
        for template in (_SHIP_TEMPLATE, _STAGE_TEMPLATE):
            with self.subTest(template=template.name):
                self.assertNotIn("long_context", template.read_text(encoding="utf-8"))

    def test_templates_no_longer_bind_tier_variables_for_routing(self) -> None:
        for template, prefix in ((_SHIP_TEMPLATE, "TIER_2"), (_STAGE_TEMPLATE, "TIER_3")):
            block = _frontmatter_block(template.read_text(encoding="utf-8"))
            with self.subTest(template=template.name):
                self.assertNotIn("{{" + prefix + "_", block)


class RenderedCandidateTests(unittest.TestCase):
    """H-C6: render under three configs and validate as installed frontmatter."""

    _EXPECTED_SHIP = {
        _CONFIG_DOGFOOD: ("claude-opus-5.5", "anthropic", "high", "long_context"),
        _CONFIG_ROLELESS: ("claude-sonnet-5", "anthropic", "high", "default"),
        _CONFIG_SEED: ("gpt-6-luna", "openai", "xhigh", "long_context"),
    }
    _EXPECTED_STAGE = {
        _CONFIG_DOGFOOD: ("claude-opus-5.5", "anthropic", "high", "default"),
        _CONFIG_ROLELESS: ("claude-opus-5.5", "anthropic", "high", "default"),
        _CONFIG_SEED: ("claude-opus-5.5", "anthropic", "high", "default"),
    }

    @classmethod
    def setUpClass(cls) -> None:
        cls.rendered: dict[tuple[str, str], str] = {}
        for label in (_CONFIG_DOGFOOD, _CONFIG_ROLELESS, _CONFIG_SEED):
            config = _config_for(label)
            cls.rendered[("ship", label)] = _render(_SHIP_TEMPLATE, _SHIP_MIRROR_REL, config)
            cls.rendered[("stage", label)] = _render(_STAGE_TEMPLATE, _STAGE_MIRROR_REL, config)

    def _parsed(self, role: str, label: str):
        parsed = parse_frontmatter(self.rendered[(role, label)], MODE_INSTALLED)
        self.assertIsNone(parsed.error)
        return parsed

    def test_rendered_frontmatter_has_no_placeholders(self) -> None:
        for (role, label), text in self.rendered.items():
            with self.subTest(role=role, config=label):
                self.assertEqual(_PLACEHOLDER.findall(_frontmatter_block(text)), [])

    def test_ship_route_values(self) -> None:
        for label, expected in self._EXPECTED_SHIP.items():
            with self.subTest(config=label):
                data = self._parsed("ship", label).data
                self.assertEqual(tuple(data[key] for key in _ROUTE_KEYS), expected)

    def test_stage_route_values(self) -> None:
        for label, expected in self._EXPECTED_STAGE.items():
            with self.subTest(config=label):
                data = self._parsed("stage", label).data
                self.assertEqual(tuple(data[key] for key in _ROUTE_KEYS), expected)

    def test_max_subagent_tier_unchanged(self) -> None:
        """Operator hold (stash 9F6AC6B3): ruling 5b's Ship 2 -> 3 is not applied."""
        for label in self._EXPECTED_SHIP:
            with self.subTest(config=label):
                self.assertEqual(self._parsed("ship", label).data["max_subagent_tier"], 2)
                self.assertEqual(self._parsed("stage", label).data["max_subagent_tier"], 3)

    def test_rendered_frontmatter_passes_b1_installed_mode(self) -> None:
        for role, label in self.rendered:
            with self.subTest(role=role, config=label):
                findings = check_agent(self._parsed(role, label), "tier-routed", MODE_INSTALLED)
                self.assertFalse(has_blocking_findings(findings), findings)


class InstalledMirrorTests(unittest.TestCase):
    def _mirror(self, rel: str) -> dict[str, Any]:
        parsed = parse_frontmatter((_ROOT / rel).read_text(encoding="utf-8"), MODE_INSTALLED)
        self.assertIsNone(parsed.error)
        return parsed.data

    def test_ship_mirror_route(self) -> None:
        data = self._mirror(_SHIP_MIRROR_REL)
        self.assertEqual(
            tuple(data[key] for key in _ROUTE_KEYS),
            ("claude-opus-5.5", "anthropic", "high", "long_context"),
        )
        self.assertEqual(data["max_subagent_tier"], 3)

    def test_stage_mirror_route(self) -> None:
        data = self._mirror(_STAGE_MIRROR_REL)
        self.assertEqual(
            tuple(data[key] for key in _ROUTE_KEYS),
            ("claude-opus-5.5", "anthropic", "high", "default"),
        )
        self.assertEqual(data["max_subagent_tier"], 3)

    def test_mirror_routes_equal_render_under_this_config(self) -> None:
        config = _config_for(_CONFIG_DOGFOOD)
        for template, rel in ((_SHIP_TEMPLATE, _SHIP_MIRROR_REL), (_STAGE_TEMPLATE, _STAGE_MIRROR_REL)):
            rendered = parse_frontmatter(_render(template, rel, config), MODE_INSTALLED).data
            mirror = self._mirror(rel)
            with self.subTest(mirror=rel):
                self.assertEqual(
                    {key: mirror[key] for key in _ROUTE_KEYS},
                    {key: rendered[key] for key in _ROUTE_KEYS},
                )

    def test_mirrors_pass_b1_installed_mode(self) -> None:
        for rel in (_SHIP_MIRROR_REL, _STAGE_MIRROR_REL):
            with self.subTest(mirror=rel):
                findings = check_agent(self._mirror(rel), "tier-routed", MODE_INSTALLED)
                self.assertFalse(has_blocking_findings(findings), findings)


class DogfoodConfigAndManifestTests(unittest.TestCase):
    def test_dogfood_ship_route_declares_long_context(self) -> None:
        ship = _load("config.yaml")["model_routing"]["ship"]
        self.assertEqual(ship.get("context_tier"), "long_context")
        # D-C6 binding: the Ship model route is unchanged.
        self.assertEqual(
            (ship["model_family"], ship["model_provider"], ship["reasoning_effort"]),
            ("claude-opus-5.5", "anthropic", "high"),
        )

    def test_manifest_checksums_refreshed(self) -> None:
        manifest = _load("harness-manifest.yaml")
        by_path = {entry["path"]: entry for entry in manifest.get("artifacts") or []}
        for rel in (_SHIP_MIRROR_REL, _STAGE_MIRROR_REL, _CONFIG_REL):
            with self.subTest(path=rel):
                self.assertEqual(by_path[rel]["checksum"], _lf_sha256(_ROOT / rel))

    def test_config_hash_matches_raw_config_blob(self) -> None:
        manifest = _load("harness-manifest.yaml")
        self.assertEqual(manifest["config_hash"], _lf_sha256(_ROOT / _CONFIG_REL))


if __name__ == "__main__":
    unittest.main()
