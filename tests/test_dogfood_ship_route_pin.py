"""194.012-T (C7) -- durable Ship-pin regression test for this repository.

Plan unit C7 (docs/plans/2026-09-27-context-tier-model-routing-plan.md). The Ship
route was originally pinned to ``claude-opus-5.5`` / ``anthropic`` / ``high``
(D-C6, 2026-09-27T13:18:02-07:00). The operator's model_routing edit of
2026-10-09, carried forward in shipment 208-S, supersedes that pin: the Ship route
is now ``claude-haiku-5.5`` / ``anthropic`` / ``xhigh``, with its nested
``ship.escalation`` set to ``claude-sonnet-5.5`` / ``anthropic`` / ``medium``. Its
``context_tier`` remains ``long_context`` (ruling 5a, 2026-09-27T22:50-07:00); the
Ship ``max_subagent_tier`` is 3 in both template and mirror (ruling 5b). The pin
reads live values and never relies on the config comment that cites these rulings.

Asserts, on the live dogfood workspace:

1. the config Ship route is ``claude-haiku-5.5`` / ``anthropic`` / ``xhigh`` /
   ``long_context``;
2. the installed ``_ship.agent.md`` frontmatter matches it on all four routing
   keys and declares ``max_subagent_tier: 3``;
3. the Ship template rendered under this config (through
   ``_compose_artifact_variables``) matches the installed frontmatter's four
   routing keys and its ``max_subagent_tier``;
4. ``verify_workspace`` reports ``role_route_resolution`` ``ok: true`` (that check
   emits only ``ok`` and ``errors``), ``_derive_template_variables`` gives the
   Ship family/provider/context tier, no ``migration_proposals[]`` entry targets
   the Ship mirror, and no ``ROUTE_VARIABLE_STALE`` warning is raised (C4b);
5. the Ship escalation route is not ``escalation_degraded`` and its context tier
   resolves to ``default`` (Ship's own ``long_context`` does not flow into
   escalation, D-C2);
6. the fresh-install Ship seed trigger (C3b) does not fire here.

It also pins the config shape after the 2026-10-09 operator edit: tier1-3,
orchestrator and stage declare ``context_tier: "default"``; the flat ``escalation``
block is absent; ``ship.escalation`` is pinned exactly; and no ``stage.escalation``
exists.
"""

from __future__ import annotations

import tempfile
import unittest
import unittest.mock as _mock
from pathlib import Path
from typing import Any

import yaml

from autoharness.frontmatter_contract import MODE_INSTALLED, parse_frontmatter
from autoharness.verify_workspace import (
    _compose_artifact_variables,
    _derive_template_variables,
    _render_template,
    _resolve_artifact_role,
    verify_workspace,
)

_ROOT = Path(__file__).resolve().parents[1]
_AUTOHARNESS = _ROOT / ".autoharness"
_SHIP_TEMPLATE = _ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
_SHIP_MIRROR_REL = ".github/agents/_ship.agent.md"
_ROUTE_KEYS = ("model_family", "model_provider", "reasoning_effort", "context_tier")
_PINNED_SHIP_ROUTE = {
    "model_family": "claude-haiku-5.5",
    "model_provider": "anthropic",
    "reasoning_effort": "xhigh",
    "context_tier": "long_context",
}
# Operator model_routing edit (2026-10-09, carried forward in 208-S): nested Ship
# escalation route. Pinned exactly; a change must update this value deliberately.
_PINNED_SHIP_ESCALATION = {
    "model_family": "claude-sonnet-5.5",
    "model_provider": "anthropic",
    "reasoning_effort": "medium",
    "context_tier": "default",
}
_PINNED_MAX_SUBAGENT_TIER = 3
_SHIP_OVERRIDE_KEYS = ("SHIP_FAMILY", "SHIP_PROVIDER", "SHIP_REASONING_EFFORT", "SHIP_CONTEXT_TIER")


def _load(name: str) -> dict[str, Any]:
    return yaml.safe_load((_AUTOHARNESS / name).read_text(encoding="utf-8")) or {}


def _fixtures() -> tuple[dict, dict, dict, dict]:
    return (
        _load("harness-manifest.yaml"),
        _load("config.yaml"),
        _load("workspace-profile.yaml"),
        _load("backlog-registry.yaml"),
    )


def _model_routing() -> dict[str, Any]:
    return _load("config.yaml").get("model_routing") or {}


def _mirror_frontmatter() -> dict[str, Any]:
    parsed = parse_frontmatter((_ROOT / _SHIP_MIRROR_REL).read_text(encoding="utf-8"), MODE_INSTALLED)
    if parsed.error is not None:
        raise AssertionError(f"{_SHIP_MIRROR_REL} frontmatter does not parse: {parsed.error}")
    return parsed.data


def _base_variables() -> dict[str, str]:
    manifest, config, profile, registry = _fixtures()
    with _mock.patch("autoharness.verify_workspace._resolve_default_branch", return_value="main"):
        return _derive_template_variables(
            _ROOT, manifest, config, profile, registry, config_authoritative=True
        )


class ConfigShipRouteTests(unittest.TestCase):
    """AC 1 and the C7 additive config edit."""

    def test_config_ship_route_is_pinned(self) -> None:
        ship = _model_routing()["ship"]
        self.assertEqual({key: ship.get(key) for key in _ROUTE_KEYS}, _PINNED_SHIP_ROUTE)

    def test_non_ship_routes_declare_default_context_tier(self) -> None:
        routing = _model_routing()
        for route in ("tier1", "tier2", "tier3", "orchestrator", "stage"):
            with self.subTest(route=route):
                self.assertEqual(routing[route].get("context_tier"), "default")

    def test_flat_escalation_block_is_absent(self) -> None:
        # Operator model_routing edit (2026-10-09, carried forward in 208-S) removed
        # the legacy flat escalation block. The escalation route now resolves via the
        # nested ship override or the tier3 fallback.
        self.assertNotIn("escalation", _model_routing())

    def test_nested_role_escalation_pins(self) -> None:
        routing = _model_routing()
        with self.subTest(role="stage"):
            self.assertNotIn("escalation", routing["stage"])
        with self.subTest(role="ship"):
            self.assertEqual(routing["ship"]["escalation"], _PINNED_SHIP_ESCALATION)


class InstalledShipMirrorTests(unittest.TestCase):
    """AC 2 and AC 3."""

    def test_mirror_matches_config_route(self) -> None:
        mirror = _mirror_frontmatter()
        ship = _model_routing()["ship"]
        self.assertEqual(
            {key: mirror.get(key) for key in _ROUTE_KEYS},
            {key: ship.get(key) for key in _ROUTE_KEYS},
        )
        self.assertEqual(mirror.get("context_tier"), "long_context")
        self.assertEqual(mirror.get("max_subagent_tier"), _PINNED_MAX_SUBAGENT_TIER)

    def test_template_render_matches_mirror(self) -> None:
        variables = _compose_artifact_variables(
            _base_variables(), _model_routing(), _resolve_artifact_role(_SHIP_MIRROR_REL)
        )
        rendered_text = _render_template(_SHIP_TEMPLATE.read_text(encoding="utf-8"), variables)
        rendered = parse_frontmatter(rendered_text, MODE_INSTALLED)
        self.assertIsNone(rendered.error)
        mirror = _mirror_frontmatter()
        self.assertEqual(
            {key: rendered.data.get(key) for key in _ROUTE_KEYS},
            {key: mirror.get(key) for key in _ROUTE_KEYS},
        )
        self.assertEqual(rendered.data.get("max_subagent_tier"), mirror.get("max_subagent_tier"))
        self.assertEqual(rendered.data.get("max_subagent_tier"), _PINNED_MAX_SUBAGENT_TIER)


class VerifyWorkspaceShipPinTests(unittest.TestCase):
    """AC 4 and AC 5, against a real staged verify of this repository."""

    @classmethod
    def setUpClass(cls) -> None:
        with tempfile.TemporaryDirectory() as staging_dir, _mock.patch(
            "autoharness.verify_workspace._resolve_default_branch", return_value="main"
        ):
            cls.report = verify_workspace(_ROOT, _ROOT, staging_dir=Path(staging_dir))

    def test_role_route_resolution_ok(self) -> None:
        check = self.report["targeted_checks"]["role_route_resolution"]
        self.assertTrue(check["ok"], check.get("errors"))
        self.assertEqual(check.get("errors"), [])

    def test_derived_ship_variables(self) -> None:
        variables = _base_variables()
        self.assertEqual(variables["SHIP_FAMILY"], "claude-haiku-5.5")
        self.assertEqual(variables["SHIP_PROVIDER"], "anthropic")
        self.assertEqual(variables["SHIP_CONTEXT_TIER"], "long_context")

    def test_no_migration_proposal_targets_ship_mirror(self) -> None:
        paths = [proposal.get("path") for proposal in self.report.get("migration_proposals") or []]
        self.assertNotIn(_SHIP_MIRROR_REL, paths)

    def test_no_route_variable_stale_warning(self) -> None:
        stale = [w for w in self.report["warnings"] if "ROUTE_VARIABLE_STALE" in str(w)]
        self.assertEqual(stale, [])

    def test_ship_escalation_not_degraded(self) -> None:
        check = self.report["targeted_checks"]["escalation_route_resolution"]
        ship = check["per_role"]["ship"]
        self.assertFalse(ship["escalation_degraded"])
        self.assertNotIn("ship", check["same_route_roles"])
        # D-C2: Ship's own long_context never flows into its escalation route.
        self.assertEqual(ship["resolved_context_tier"], "default")


class FreshInstallSeedTriggerTests(unittest.TestCase):
    """AC 6: the C3b seed trigger (install-harness Step 1.2) does not fire here."""

    def test_seed_trigger_does_not_fire(self) -> None:
        config = _load("config.yaml")
        first_install = not (_AUTOHARNESS / "harness-manifest.yaml").exists()
        ship_key_absent = "ship" not in (config.get("model_routing") or {})
        overrides = config.get("overrides") or {}
        no_ship_override = not any(key in overrides for key in _SHIP_OVERRIDE_KEYS)
        self.assertFalse(first_install)
        self.assertFalse(ship_key_absent)
        self.assertTrue(any(str(value).strip() for value in config["model_routing"]["ship"].values()))
        self.assertFalse(first_install and ship_key_absent and no_ship_override)


if __name__ == "__main__":
    unittest.main()
