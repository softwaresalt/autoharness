"""194.006-T (C4b): route-family variables are config-authoritative in verify's
staged render.

For the route family only (every variable returned by the tier, orchestrator,
role, raw-escalation and escalation-prose derivers, including the
``*_CONTEXT_TIER`` members), the precedence is ``config.overrides[<VAR>]`` >
the config-derived value (assigned over ``variables_used``) > the
``variables_used`` value, the last used only when no authoritative config is
loaded. Non-route variables keep manifest-first precedence, and a recorded
route variable that differs from the authoritative value produces a non-fatal
``ROUTE_VARIABLE_STALE`` warning (reviews AN-F3, AS-F6, AS-F9, AS-F10).
"""

from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
import unittest.mock as _mock
from pathlib import Path
from typing import Any

import yaml

from autoharness.verify_workspace import (
    _compose_artifact_variables,
    _derive_escalation_prose_variables,
    _derive_orchestrator_route_variables,
    _derive_raw_escalation_variables,
    _derive_role_route_variables,
    _derive_template_variables,
    _derive_tier_route_variables,
    _render_template,
    _route_family_variables,
    _route_variable_stale_warnings,
    verify_workspace,
)

_ROOT = Path(__file__).resolve().parents[1]
_SHIP_TEMPLATE_REL = "templates/agents/_ship.agent.md.tmpl"
_SHIP_REL = ".github/agents/_ship.agent.md"
_STALE = "ROUTE_VARIABLE_STALE"
_BRANCH_PATCH = "autoharness.verify_workspace._resolve_default_branch"

_ROUTING = {
    "tier1": {"model_family": "gpt-5.4-mini", "model_provider": "openai", "reasoning_effort": "low"},
    "tier2": {"model_family": "claude-sonnet-5", "model_provider": "anthropic", "reasoning_effort": "high"},
    "tier3": {"model_family": "claude-opus-5", "model_provider": "anthropic", "reasoning_effort": "high"},
    "ship": {
        "model_family": "claude-opus-5.5",
        "model_provider": "anthropic",
        "reasoning_effort": "high",
        "context_tier": "long_context",
    },
}


def _config(**extra: Any) -> dict[str, Any]:
    config: dict[str, Any] = {"schema_version": "1.0.0", "model_routing": copy.deepcopy(_ROUTING)}
    config.update(extra)
    return config


def _manifest(variables_used: dict[str, str] | None = None) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": "1.0.0",
        "installed_at": "2026-10-04T00:00:00Z",
        "autoharness_version": "1.5.0",
        "profile_hash": "abc",
        "primitives_installed": [3, 8],
        "capability_packs": [],
        "artifacts": [
            {
                "path": _SHIP_REL,
                "template": _SHIP_TEMPLATE_REL,
                "primitive": 4,
                "checksum": "0" * 64,
            }
        ],
    }
    if variables_used is not None:
        manifest["variables_used"] = dict(variables_used)
    return manifest


def _derive(manifest: dict[str, Any], config: dict[str, Any], **kwargs: Any) -> dict[str, str]:
    with _mock.patch(_BRANCH_PATCH, return_value="main"):
        return _derive_template_variables(_ROOT, manifest, config, {}, {}, **kwargs)


def _model_family(rendered: str) -> str:
    match = re.search(r'^model_family:\s*"?([^"\n]+)"?\s*$', rendered, re.MULTILINE)
    if match is None:
        raise AssertionError("rendered Ship frontmatter has no model_family line")
    return match.group(1)


def _stale_messages(report: dict[str, Any]) -> list[str]:
    return [
        str(warning.get("message", ""))
        for warning in report["warnings"]
        if str(warning.get("message", "")).startswith(_STALE)
    ]


class RouteFamilyMembershipTests(unittest.TestCase):
    def test_route_family_is_union_of_the_five_derivers(self) -> None:
        expected: dict[str, str] = {}
        for derive in (
            _derive_tier_route_variables,
            _derive_orchestrator_route_variables,
            _derive_role_route_variables,
            _derive_raw_escalation_variables,
            _derive_escalation_prose_variables,
        ):
            expected.update(derive(_ROUTING))
        self.assertEqual(_route_family_variables(_ROUTING), expected)

    def test_route_family_includes_context_tier_members(self) -> None:
        family = _route_family_variables(_ROUTING)
        for name in ("SHIP_CONTEXT_TIER", "STAGE_CONTEXT_TIER", "TIER_2_CONTEXT_TIER"):
            self.assertIn(name, family)
        self.assertEqual(family["SHIP_CONTEXT_TIER"], "long_context")

    def test_route_family_excludes_non_route_variables(self) -> None:
        family = _route_family_variables(_ROUTING)
        self.assertNotIn("PRIMARY_LANGUAGE", family)
        self.assertNotIn("PROJECT_NAME", family)


class DeriveTemplateVariablesPrecedenceTests(unittest.TestCase):
    def test_config_authoritative_is_keyword_only(self) -> None:
        with self.assertRaises(TypeError):
            _derive_template_variables(_ROOT, _manifest(), _config(), {}, {}, True)  # type: ignore[misc]

    def test_authoritative_config_value_assigned_over_recorded_route_variable(self) -> None:
        manifest = _manifest({"SHIP_FAMILY": "claude-sonnet-5", "SHIP_CONTEXT_TIER": "default"})
        variables = _derive(manifest, _config(), config_authoritative=True)
        self.assertEqual(variables["SHIP_FAMILY"], "claude-opus-5.5")
        self.assertEqual(variables["SHIP_CONTEXT_TIER"], "long_context")

    def test_override_beats_config_derived_value(self) -> None:
        manifest = _manifest({"SHIP_FAMILY": "claude-sonnet-5"})
        config = _config(overrides={"SHIP_FAMILY": "custom-x"})
        variables = _derive(manifest, config, config_authoritative=True)
        self.assertEqual(variables["SHIP_FAMILY"], "custom-x")

    def test_non_route_recorded_variable_still_wins(self) -> None:
        manifest = _manifest({"PRIMARY_LANGUAGE": "Haskell", "SHIP_FAMILY": "claude-sonnet-5"})
        variables = _derive(manifest, _config(), config_authoritative=True)
        self.assertEqual(variables["PRIMARY_LANGUAGE"], "Haskell")

    def test_non_route_override_is_not_newly_honored(self) -> None:
        manifest = _manifest({"PRIMARY_LANGUAGE": "Haskell"})
        config = _config(overrides={"PRIMARY_LANGUAGE": "Ocaml"})
        variables = _derive(manifest, config, config_authoritative=True)
        self.assertEqual(variables["PRIMARY_LANGUAGE"], "Haskell")

    def test_non_authoritative_keeps_manifest_first(self) -> None:
        manifest = _manifest({"SHIP_FAMILY": "claude-sonnet-5"})
        config = _config(overrides={"SHIP_FAMILY": "custom-x"})
        variables = _derive(manifest, config, config_authoritative=False)
        self.assertEqual(variables["SHIP_FAMILY"], "claude-sonnet-5")

    def test_default_is_non_authoritative(self) -> None:
        manifest = _manifest({"SHIP_FAMILY": "claude-sonnet-5"})
        self.assertEqual(_derive(manifest, _config())["SHIP_FAMILY"], "claude-sonnet-5")

    def test_no_recorded_route_variables_render_identically(self) -> None:
        manifest = _manifest({"PRIMARY_LANGUAGE": "Haskell"})
        self.assertEqual(
            _derive(manifest, _config(), config_authoritative=True),
            _derive(manifest, _config(), config_authoritative=False),
        )


class ComposeArtifactVariablesTests(unittest.TestCase):
    """A2: role overlay honors overrides and is skipped when not authoritative."""

    _BASE = {"ESCALATION_FAMILY": "recorded-esc", "ESCALATION_CONTEXT_TIER": "recorded-tier", "X": "y"}

    def test_overrides_win_after_role_overlay(self) -> None:
        composed = _compose_artifact_variables(
            dict(self._BASE),
            _ROUTING,
            "ship",
            config_authoritative=True,
            overrides={"ESCALATION_CONTEXT_TIER": "ovr-tier", "ESCALATION_PROVIDER": "ovr-prov"},
        )
        self.assertEqual(composed["ESCALATION_CONTEXT_TIER"], "ovr-tier")
        self.assertEqual(composed["ESCALATION_PROVIDER"], "ovr-prov")
        self.assertNotEqual(composed["ESCALATION_FAMILY"], "recorded-esc")

    def test_non_authoritative_skips_role_overlay(self) -> None:
        base = dict(self._BASE)
        composed = _compose_artifact_variables(
            base, _ROUTING, "ship", config_authoritative=False, overrides={"ESCALATION_FAMILY": "ignored"}
        )
        self.assertEqual(composed, self._BASE)

    def test_authoritative_overlay_unchanged_without_overrides(self) -> None:
        composed = _compose_artifact_variables(dict(self._BASE), _ROUTING, "ship", config_authoritative=True)
        self.assertEqual(composed["ESCALATION_CONTEXT_TIER"], "default")
        self.assertEqual(composed["X"], "y")

    def test_base_mapping_not_mutated(self) -> None:
        base = dict(self._BASE)
        _compose_artifact_variables(
            base, _ROUTING, "ship", config_authoritative=True, overrides={"ESCALATION_FAMILY": "o"}
        )
        self.assertEqual(base, self._BASE)


class RouteVariableStaleWarningTests(unittest.TestCase):
    def test_exactly_one_warning_for_one_stale_variable(self) -> None:
        manifest = _manifest({"SHIP_FAMILY": "claude-sonnet-5", "SHIP_PROVIDER": "anthropic"})
        warnings = _route_variable_stale_warnings(manifest, _config(), ".autoharness/harness-manifest.yaml")
        self.assertEqual(len(warnings), 1)
        self.assertEqual(
            warnings[0]["message"],
            "ROUTE_VARIABLE_STALE: SHIP_FAMILY recorded=claude-sonnet-5 config=claude-opus-5.5",
        )
        self.assertEqual(warnings[0]["field"], "SHIP_FAMILY")

    def test_no_warning_without_recorded_route_variables(self) -> None:
        manifest = _manifest({"PRIMARY_LANGUAGE": "Haskell"})
        self.assertEqual(
            _route_variable_stale_warnings(manifest, _config(), ".autoharness/harness-manifest.yaml"), []
        )

    def test_override_is_the_compared_authoritative_value(self) -> None:
        manifest = _manifest({"SHIP_FAMILY": "custom-x"})
        config = _config(overrides={"SHIP_FAMILY": "custom-x"})
        self.assertEqual(
            _route_variable_stale_warnings(manifest, config, ".autoharness/harness-manifest.yaml"), []
        )

    def test_distinct_stale_variables_stay_distinct_after_summary(self) -> None:
        manifest = _manifest({"SHIP_FAMILY": "a", "SHIP_PROVIDER": "b"})
        warnings = _route_variable_stale_warnings(manifest, _config(), ".autoharness/harness-manifest.yaml")
        self.assertEqual(len({warning["rule"] for warning in warnings}), 2)

    def test_dogfood_records_no_route_variables(self) -> None:
        manifest = yaml.safe_load((_ROOT / ".autoharness" / "harness-manifest.yaml").read_text(encoding="utf-8"))
        config = yaml.safe_load((_ROOT / ".autoharness" / "config.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            _route_variable_stale_warnings(manifest, config, ".autoharness/harness-manifest.yaml"), []
        )
        self.assertEqual(
            _derive(manifest, config, config_authoritative=True),
            _derive(manifest, config, config_authoritative=False),
        )


class VerifyWorkspaceStagedRenderTests(unittest.TestCase):
    """End-to-end: verify's staged Ship render and its warnings[]."""

    def _run(
        self,
        variables_used: dict[str, str] | None,
        *,
        config: dict[str, Any] | None,
        raw_config: str | None = None,
    ) -> tuple[dict[str, Any], str, Path]:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        home = root / "home"
        workspace = root / "workspace"
        schema = json.dumps({"$schema": "http://json-schema.org/draft-07/schema#", "type": "object"})
        for name, versioned in (
            ("harness-manifest.schema.json", "harness-manifest"),
            ("harness-config.schema.json", "harness-config"),
            ("workspace-profile.schema.json", "workspace-profile"),
        ):
            (home / "schemas" / versioned).mkdir(parents=True, exist_ok=True)
            (home / "schemas" / name).write_text(schema, encoding="utf-8")
            (home / "schemas" / versioned / "1.0.0.schema.json").write_text(schema, encoding="utf-8")
        (home / "templates" / "agents").mkdir(parents=True, exist_ok=True)
        (home / _SHIP_TEMPLATE_REL).write_bytes((_ROOT / _SHIP_TEMPLATE_REL).read_bytes())
        meta = workspace / ".autoharness"
        meta.mkdir(parents=True, exist_ok=True)
        (meta / "harness-manifest.yaml").write_text(
            yaml.safe_dump(_manifest(variables_used), sort_keys=False), encoding="utf-8"
        )
        if raw_config is not None:
            (meta / "config.yaml").write_text(raw_config, encoding="utf-8")
        elif config is not None:
            (meta / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        staging = root / "staging"
        with _mock.patch(_BRANCH_PATCH, return_value="main"):
            report = verify_workspace(workspace, home, staging_dir=staging)
        rendered = (staging / _SHIP_REL).read_text(encoding="utf-8")
        return report, rendered, workspace

    def test_stale_record_renders_config_value_with_one_warning(self) -> None:
        report, rendered, _ = self._run({"SHIP_FAMILY": "claude-sonnet-5"}, config=_config())
        self.assertEqual(_model_family(rendered), "claude-opus-5.5")
        messages = _stale_messages(report)
        self.assertEqual(len(messages), 1, messages)
        self.assertTrue(messages[0].startswith("ROUTE_VARIABLE_STALE: SHIP_FAMILY "), messages)

    def test_override_wins_in_staged_render(self) -> None:
        report, rendered, _ = self._run(
            {"SHIP_FAMILY": "claude-sonnet-5"}, config=_config(overrides={"SHIP_FAMILY": "custom-x"})
        )
        self.assertEqual(_model_family(rendered), "custom-x")

    def test_no_recorded_route_variables_no_warning_byte_identical(self) -> None:
        report, rendered, workspace = self._run({"PRIMARY_LANGUAGE": "Haskell"}, config=_config())
        self.assertEqual(_stale_messages(report), [])
        manifest = yaml.safe_load((workspace / ".autoharness" / "harness-manifest.yaml").read_text(encoding="utf-8"))
        config = _config()
        with _mock.patch(_BRANCH_PATCH, return_value="main"):
            legacy = _derive_template_variables(workspace, manifest, config, {}, {})
        expected = _render_template(
            (_ROOT / _SHIP_TEMPLATE_REL).read_text(encoding="utf-8"),
            _compose_artifact_variables(legacy, config["model_routing"], "ship"),
        )
        self.assertEqual(rendered, expected)

    def test_manifest_only_keeps_recorded_route_without_warning(self) -> None:
        report, rendered, _ = self._run({"SHIP_FAMILY": "claude-opus-5.5"}, config=None)
        self.assertEqual(_model_family(rendered), "claude-opus-5.5")
        self.assertEqual(_stale_messages(report), [])

    def test_config_without_model_routing_is_not_authoritative(self) -> None:
        # A1: a parseable config that declares no model_routing mapping must not
        # let built-in defaults overwrite recorded route variables.
        report, rendered, _ = self._run(
            {"SHIP_FAMILY": "claude-opus-5.5"},
            config={"schema_version": "1.0.0", "capability_packs": []},
        )
        self.assertEqual(_model_family(rendered), "claude-opus-5.5")
        self.assertEqual(_stale_messages(report), [])

    def test_config_with_non_mapping_model_routing_is_not_authoritative(self) -> None:
        report, rendered, _ = self._run(
            {"SHIP_FAMILY": "claude-opus-5.5"},
            config={"schema_version": "1.0.0", "model_routing": ["not", "a", "mapping"]},
        )
        self.assertEqual(_model_family(rendered), "claude-opus-5.5")
        self.assertEqual(_stale_messages(report), [])

    def test_config_with_model_routing_mapping_is_authoritative(self) -> None:
        report, rendered, _ = self._run({"SHIP_FAMILY": "claude-sonnet-5"}, config=_config())
        self.assertEqual(_model_family(rendered), "claude-opus-5.5")
        self.assertEqual(len(_stale_messages(report)), 1)

    def test_escalation_context_tier_override_survives_ship_role_overlay(self) -> None:
        # A2: config.overrides wins for the role-composed escalation variables.
        _, rendered, _ = self._run(
            None, config=_config(overrides={"ESCALATION_CONTEXT_TIER": "long_context_override"})
        )
        self.assertIn(
            "escalation `context_tier` resolves to `long_context_override`", rendered
        )

    def test_escalation_family_override_survives_ship_role_overlay(self) -> None:
        _, rendered, _ = self._run(None, config=_config(overrides={"ESCALATION_FAMILY": "custom-esc"}))
        self.assertIn("`custom-esc`", rendered)

    def test_manifest_only_keeps_recorded_escalation_variables(self) -> None:
        # A2: with no authoritative config the role overlay is skipped, so the
        # manifest-recorded escalation prose is kept (manifest-first).
        _, rendered, _ = self._run(
            {"ESCALATION_FAMILY": "recorded-esc", "ESCALATION_CONTEXT_TIER": "recorded-tier"}, config=None
        )
        self.assertIn("`recorded-esc`", rendered)
        self.assertIn("escalation `context_tier` resolves to `recorded-tier`", rendered)

    def test_invalid_config_keeps_manifest_first_without_warning(self) -> None:
        report, rendered, _ = self._run(
            {"SHIP_FAMILY": "claude-opus-5.5"}, config=None, raw_config="model_routing: [unclosed\n"
        )
        self.assertTrue(
            any(b.get("kind") == "invalid-config-yaml" for b in report["strict_schema_blockers"])
        )
        self.assertEqual(_model_family(rendered), "claude-opus-5.5")
        self.assertEqual(_stale_messages(report), [])


if __name__ == "__main__":
    unittest.main()
