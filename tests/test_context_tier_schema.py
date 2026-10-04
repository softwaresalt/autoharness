"""Schema-level tests for the optional ``context_tier`` route field (194-F, C1).

Covers ``definitions/contextTier`` in the harness-config schema and its
reference from every tier, role, and escalation route object:

  * existing configs without the field stay valid (D-C5, INV-C6);
  * ``context_tier: long_context`` validates; an unknown value is rejected;
  * ``context_tier`` does not participate in the both-present escalation
    ambiguity (``nonEmptyRouteFields`` unchanged, D-C3 / INV-C4);
  * the versioned 1.1.0 mirror carries the identical contract (lockstep).

See docs/plans/2026-09-27-context-tier-model-routing-plan.md section C1.
"""

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
_DOGFOOD_CONFIG = _REPO_ROOT / ".autoharness" / "config.yaml"
_CONFIG_TEMPLATE = _REPO_ROOT / "templates" / "harness-config.yaml.tmpl"

_SCHEMAS = (_ROOT_CONFIG_SCHEMA, _VERSIONED_CONFIG_SCHEMA)
_TIER_KEYS = ("tier1", "tier2", "tier3")
_ROUTE_KEYS = ("orchestrator", "stage", "ship", "escalation")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(schema_path: Path) -> Draft7Validator:
    schema = _load_json(schema_path)
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def _object_branch(route_schema: dict) -> dict:
    """Return the object form of a route schema (the oneOf object branch for
    tiers/orchestrator, or the schema itself for object-only routes)."""
    if route_schema.get("type") == "object":
        return route_schema
    for branch in route_schema.get("oneOf", []):
        if branch.get("type") == "object":
            return branch
    raise AssertionError(f"no object form in route schema: {route_schema}")


def _rendered_template_model_routing() -> dict:
    """Render the config template's model_routing block with tier model ids and
    every other placeholder empty (the role-less / unset install shape)."""
    text = _CONFIG_TEMPLATE.read_text(encoding="utf-8")
    match = re.search(r"(?m)^model_routing:\n(?:(?:  [^\n]*|)\n)+", text)
    if match is None:
        raise AssertionError("model_routing block missing from config template")
    block = match.group(0)
    for tier, model in (("1", "gpt-5.4-mini"), ("2", "claude-sonnet-5"), ("3", "claude-opus-5")):
        block = block.replace("{{MODEL_ROUTING_TIER" + tier + "}}", model)
    block = re.sub(r"\{\{[A-Z0-9_]+\}\}", "", block)
    return yaml.safe_load(block)["model_routing"]


class ContextTierDefinitionTests(unittest.TestCase):
    def test_context_tier_definition_enum(self) -> None:
        for schema_path in _SCHEMAS:
            with self.subTest(schema=schema_path.name):
                definition = _load_json(schema_path)["definitions"]["contextTier"]
                self.assertEqual(definition["type"], "string")
                self.assertEqual(definition["enum"], ["", "default", "long_context"])

    def test_every_route_object_references_context_tier(self) -> None:
        for schema_path in _SCHEMAS:
            props = _load_json(schema_path)["properties"]["model_routing"]["properties"]
            routes = {key: _object_branch(props[key]) for key in _TIER_KEYS + _ROUTE_KEYS}
            routes["stage.escalation"] = props["stage"]["properties"]["escalation"]
            routes["ship.escalation"] = props["ship"]["properties"]["escalation"]
            for name, route in routes.items():
                with self.subTest(schema=schema_path.name, route=name):
                    self.assertEqual(
                        route["properties"].get("context_tier"),
                        {"$ref": "#/definitions/contextTier"},
                    )

    def test_non_empty_route_fields_unchanged(self) -> None:
        """D-C3: context_tier never joins the both-present ambiguity predicate."""
        for schema_path in _SCHEMAS:
            with self.subTest(schema=schema_path.name):
                definition = _load_json(schema_path)["definitions"]["nonEmptyRouteFields"]
                required = sorted(branch["required"][0] for branch in definition["anyOf"])
                self.assertEqual(required, ["model_family", "model_provider", "reasoning_effort"])

    def test_anchor_and_alt_review_routes_unchanged(self) -> None:
        """D-C7: review routes do not gain context_tier."""
        props = _load_json(_ROOT_CONFIG_SCHEMA)["properties"]["model_routing"]["properties"]
        for key, route in props.items():
            if key in _TIER_KEYS + _ROUTE_KEYS:
                continue
            with self.subTest(route=key):
                self.assertNotIn("context_tier", _object_branch(route).get("properties", {}))


class ContextTierValidationTests(unittest.TestCase):
    def test_existing_dogfood_config_validates(self) -> None:
        config = yaml.safe_load(_DOGFOOD_CONFIG.read_text(encoding="utf-8"))
        for schema_path in _SCHEMAS:
            with self.subTest(schema=schema_path.name):
                errors = list(_validator(schema_path).iter_errors(config))
                self.assertEqual(errors, [])

    def test_rendered_config_template_validates(self) -> None:
        config = {"schema_version": "1.1.0", "model_routing": _rendered_template_model_routing()}
        for schema_path in _SCHEMAS:
            with self.subTest(schema=schema_path.name):
                errors = list(_validator(schema_path).iter_errors(config))
                self.assertEqual(errors, [])

    def test_long_context_on_ship_validates(self) -> None:
        config = {
            "schema_version": "1.1.0",
            "model_routing": {
                "ship": {"model_family": "claude-opus-5.5", "context_tier": "long_context"}
            },
        }
        for schema_path in _SCHEMAS:
            with self.subTest(schema=schema_path.name):
                self.assertTrue(_validator(schema_path).is_valid(config))

    def test_every_route_accepts_each_allowed_value(self) -> None:
        for value in ("", "default", "long_context"):
            config = {
                "schema_version": "1.1.0",
                "model_routing": {
                    "tier1": {"model": "m1", "context_tier": value},
                    "tier2": {"model": "m2", "context_tier": value},
                    "tier3": {"model": "m3", "context_tier": value},
                    "orchestrator": {"model_family": "o", "context_tier": value},
                    "stage": {"context_tier": value, "escalation": {"context_tier": value}},
                    "ship": {"context_tier": value, "escalation": {"context_tier": value}},
                    "escalation": {"context_tier": value},
                },
            }
            for schema_path in _SCHEMAS:
                with self.subTest(schema=schema_path.name, value=value):
                    errors = list(_validator(schema_path).iter_errors(config))
                    self.assertEqual(errors, [])

    def test_unknown_context_tier_value_rejected(self) -> None:
        routes = {
            "tier2": {"model": "m2", "context_tier": "huge"},
            "orchestrator": {"context_tier": "huge"},
            "ship": {"context_tier": "huge"},
            "escalation": {"context_tier": "huge"},
            "stage": {"escalation": {"context_tier": "huge"}},
        }
        for key, route in routes.items():
            config = {"schema_version": "1.1.0", "model_routing": {key: route}}
            for schema_path in _SCHEMAS:
                with self.subTest(schema=schema_path.name, route=key):
                    self.assertFalse(_validator(schema_path).is_valid(config))

    def test_flat_context_only_plus_nested_family_is_not_ambiguous(self) -> None:
        config = {
            "schema_version": "1.1.0",
            "model_routing": {
                "escalation": {"context_tier": "long_context"},
                "stage": {"escalation": {"model_family": "claude-sonnet-5"}},
            },
        }
        for schema_path in _SCHEMAS:
            with self.subTest(schema=schema_path.name):
                self.assertTrue(_validator(schema_path).is_valid(config))

    def test_nested_context_only_plus_flat_family_is_not_ambiguous(self) -> None:
        config = {
            "schema_version": "1.1.0",
            "model_routing": {
                "escalation": {"model_family": "gpt-6-sol"},
                "ship": {"escalation": {"context_tier": "long_context"}},
            },
        }
        for schema_path in _SCHEMAS:
            with self.subTest(schema=schema_path.name):
                self.assertTrue(_validator(schema_path).is_valid(config))


if __name__ == "__main__":
    unittest.main()
