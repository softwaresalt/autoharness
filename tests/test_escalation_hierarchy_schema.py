"""Schema-level tests for F02FD596 nested per-role escalation hierarchy.

Covers the harness-config schema's encoding of:
  * H2 -- both-present (legacy flat + nested per-role) ambiguity is rejected
    via the model_routing-level `not` constraint.
  * H5 -- additionalProperties:false parity: an unknown key under a nested
    `<role>.escalation` is invalid, same as the legacy flat `escalation`.
  * H9 -- backward compatibility: the legacy flat `escalation` key is not
    removed or renamed, and the current dogfood config remains schema-valid.

See docs/decisions/2026-08-07-model-routing-hierarchy-dynamic-reload-deliberation.md
and docs/plans/2026-08-07-model-routing-hierarchy-dynamic-reload-hardening.md.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ROOT_CONFIG_SCHEMA = _REPO_ROOT / "schemas" / "harness-config.schema.json"
_VERSIONED_CONFIG_SCHEMA = _REPO_ROOT / "schemas" / "harness-config" / "1.0.0.schema.json"
_DOGFOOD_CONFIG = _REPO_ROOT / ".autoharness" / "config.yaml"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(schema_path: Path) -> Draft7Validator:
    schema = _load_json(schema_path)
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


class NestedEscalationSchemaTests(unittest.TestCase):
    def test_stage_and_ship_declare_nested_escalation_property(self) -> None:
        schema = _load_json(_ROOT_CONFIG_SCHEMA)
        model_routing_props = schema["properties"]["model_routing"]["properties"]
        for role in ("stage", "ship"):
            self.assertIn("escalation", model_routing_props[role]["properties"])
            escalation_schema = model_routing_props[role]["properties"]["escalation"]
            self.assertFalse(escalation_schema.get("additionalProperties", True))
            self.assertEqual(
                set(escalation_schema["properties"]),
                {"model_provider", "model_family", "reasoning_effort"},
            )

    def test_legacy_flat_escalation_key_still_present_h9(self) -> None:
        """H9: the legacy flat model_routing.escalation key must not be
        removed or renamed."""
        schema = _load_json(_ROOT_CONFIG_SCHEMA)
        model_routing_props = schema["properties"]["model_routing"]["properties"]
        self.assertIn("escalation", model_routing_props)
        self.assertIn("DEPRECATED", model_routing_props["escalation"]["description"])

    def test_both_present_flat_and_nested_stage_is_invalid_h2(self) -> None:
        validator = _validator(_ROOT_CONFIG_SCHEMA)
        config = {
            "schema_version": "1.0.0",
            "model_routing": {
                "escalation": {"model_family": "gpt-5.6-sol"},
                "stage": {"escalation": {"model_family": "claude-sonnet-5"}},
            },
        }
        self.assertFalse(validator.is_valid(config))

    def test_both_present_flat_and_nested_ship_is_invalid_h2(self) -> None:
        validator = _validator(_ROOT_CONFIG_SCHEMA)
        config = {
            "schema_version": "1.0.0",
            "model_routing": {
                "escalation": {"model_provider": "openai"},
                "ship": {"escalation": {"model_provider": "anthropic"}},
            },
        }
        self.assertFalse(validator.is_valid(config))

    def test_only_flat_escalation_is_valid(self) -> None:
        validator = _validator(_ROOT_CONFIG_SCHEMA)
        config = {
            "schema_version": "1.0.0",
            "model_routing": {"escalation": {"model_family": "gpt-5.6-sol"}},
        }
        self.assertTrue(validator.is_valid(config))

    def test_only_nested_escalation_is_valid(self) -> None:
        validator = _validator(_ROOT_CONFIG_SCHEMA)
        config = {
            "schema_version": "1.0.0",
            "model_routing": {
                "stage": {"escalation": {"model_family": "claude-sonnet-5"}},
                "ship": {"escalation": {"model_family": "gpt-5.6-sol"}},
            },
        }
        self.assertTrue(validator.is_valid(config))

    def test_neither_present_is_valid(self) -> None:
        validator = _validator(_ROOT_CONFIG_SCHEMA)
        config = {"schema_version": "1.0.0", "model_routing": {"tier3": "claude-opus-5"}}
        self.assertTrue(validator.is_valid(config))

    def test_unknown_key_under_nested_stage_escalation_is_invalid_h5(self) -> None:
        validator = _validator(_ROOT_CONFIG_SCHEMA)
        config = {
            "schema_version": "1.0.0",
            "model_routing": {"stage": {"escalation": {"unexpected": "nope"}}},
        }
        self.assertFalse(validator.is_valid(config))

    def test_unknown_key_under_nested_ship_escalation_is_invalid_h5(self) -> None:
        validator = _validator(_ROOT_CONFIG_SCHEMA)
        config = {
            "schema_version": "1.0.0",
            "model_routing": {"ship": {"escalation": {"unexpected": "nope"}}},
        }
        self.assertFalse(validator.is_valid(config))

    def test_versioned_schema_matches_root_schema_behavior(self) -> None:
        """The pinned 1.0.0 schema mirror must encode the identical
        constraint (differs only by $id, per the repo's existing schema
        pairing convention)."""
        validator = _validator(_VERSIONED_CONFIG_SCHEMA)
        ambiguous = {
            "schema_version": "1.0.0",
            "model_routing": {
                "escalation": {"model_family": "gpt-5.6-sol"},
                "stage": {"escalation": {"model_family": "claude-sonnet-5"}},
            },
        }
        self.assertFalse(validator.is_valid(ambiguous))

    def test_current_dogfood_config_is_schema_valid(self) -> None:
        """H1 regression guarantee: the current, unmodified dogfood
        .autoharness/config.yaml (flat legacy escalation only, no nested
        override) remains schema-valid after the F02FD596 nested hierarchy
        addition."""
        validator = _validator(_ROOT_CONFIG_SCHEMA)
        config = yaml.safe_load(_DOGFOOD_CONFIG.read_text(encoding="utf-8"))
        errors = list(validator.iter_errors(config))
        self.assertEqual(errors, [], f"expected dogfood config to validate cleanly: {errors}")


if __name__ == "__main__":
    unittest.main()
