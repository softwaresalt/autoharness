"""Schema tests for the harness-config 1.2.0 mirror (208-F B4).

The 1.2.0 mirror adds the model_routing ``routes`` catalog and ``bindings`` map
and closes ``model_routing`` to an allowlist of exactly twelve keys. It is
published unreferenced until the atomic cut-over (B5): every assertion here
validates against the mirror file directly, never the root schema, and the
published 1.1.0 mirror keeps accepting every document it accepts today.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MIRROR_1_2_0 = _REPO_ROOT / "schemas" / "harness-config" / "1.2.0.schema.json"
_MIRROR_1_1_0 = _REPO_ROOT / "schemas" / "harness-config" / "1.1.0.schema.json"
_DOGFOOD_CONFIG = _REPO_ROOT / ".autoharness" / "config.yaml"
_CONFIG_TEMPLATE = _REPO_ROOT / "templates" / "harness-config.yaml.tmpl"

_EXPECTED_ID = "https://softwaresalt.github.io/autoharness/schemas/harness-config/1.2.0.schema.json"
_MODEL_ROUTING_KEYS = frozenset(
    {
        "tier1",
        "tier2",
        "tier3",
        "orchestrator",
        "stage",
        "ship",
        "escalation",
        "anchor_review",
        "alt_review",
        "alt_doc_review",
        "routes",
        "bindings",
    }
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(path: Path) -> Draft7Validator:
    schema = _load_json(path)
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def _errors(validator: Draft7Validator, document: dict) -> list[str]:
    """Return ``path: message`` strings so failures are asserted by named path."""
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in validator.iter_errors(document)
    ]


def _config(model_routing: dict, version: str = "1.2.0") -> dict:
    return {"schema_version": version, "model_routing": model_routing}


def _rendered_template_model_routing() -> dict:
    text = _CONFIG_TEMPLATE.read_text(encoding="utf-8")
    match = re.search(r"(?m)^model_routing:\n(?:(?:  [^\n]*|)\n)+", text)
    if match is None:
        raise AssertionError("model_routing block missing from config template")
    block = match.group(0)
    for tier, model in (("1", "gpt-5.4-mini"), ("2", "claude-sonnet-5"), ("3", "claude-opus-5")):
        block = block.replace("{{MODEL_ROUTING_TIER" + tier + "}}", model)
    block = re.sub(r"\{\{[A-Z0-9_]+\}\}", "", block)
    return yaml.safe_load(block)["model_routing"]


class MirrorIdentityTests(unittest.TestCase):
    def test_mirror_is_a_valid_schema_with_1_2_0_identity(self) -> None:
        schema = _load_json(_MIRROR_1_2_0)
        Draft7Validator.check_schema(schema)
        self.assertEqual(schema["$id"], _EXPECTED_ID)
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.2.0")

    def test_model_routing_is_a_closed_twelve_key_allowlist(self) -> None:
        model_routing = _load_json(_MIRROR_1_2_0)["properties"]["model_routing"]
        self.assertEqual(set(model_routing["properties"]), _MODEL_ROUTING_KEYS)
        self.assertIs(model_routing["additionalProperties"], False)

    def test_ambiguity_constraint_is_unchanged_from_1_1_0(self) -> None:
        new = _load_json(_MIRROR_1_2_0)["properties"]["model_routing"]
        old = _load_json(_MIRROR_1_1_0)["properties"]["model_routing"]
        self.assertEqual(new["not"], old["not"])

    def test_pre_existing_model_routing_properties_are_unchanged(self) -> None:
        new = _load_json(_MIRROR_1_2_0)["properties"]["model_routing"]["properties"]
        old = _load_json(_MIRROR_1_1_0)["properties"]["model_routing"]["properties"]
        for key, definition in old.items():
            with self.subTest(key=key):
                self.assertEqual(new[key], definition)


class CatalogAndBindingsValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = _validator(_MIRROR_1_2_0)

    def test_bare_config_and_empty_catalog_and_bindings_validate(self) -> None:
        for document in (
            {"schema_version": "1.2.0"},
            _config({}),
            _config({"routes": {}, "bindings": {}}),
        ):
            with self.subTest(document=document):
                self.assertEqual(_errors(self.validator, document), [])

    def test_valid_catalog_and_bindings_validate(self) -> None:
        document = _config(
            {
                "routes": {
                    "reviewer-xhigh": {
                        "tier": "tier3",
                        "model_family": "claude-opus-5.5",
                        "model_provider": "anthropic",
                        "reasoning_effort": "xhigh",
                        "context_tier": "long_context",
                    },
                    "plain": {"tier": "tier1"},
                },
                "bindings": {
                    "agent:security-reviewer": {"route": "reviewer-xhigh"},
                    "agent:learnings-researcher": {
                        "route": "plain",
                        "model_family": "gpt-5.6-luna",
                        "model_provider": "openai",
                        "reasoning_effort": "high",
                        "context_tier": "default",
                    },
                },
            }
        )
        self.assertEqual(_errors(self.validator, document), [])

    def test_route_named_like_a_tier_or_default_fails_with_named_path(self) -> None:
        for name in ("tier1", "tier2", "tier3", "default"):
            with self.subTest(name=name):
                errors = _errors(self.validator, _config({"routes": {name: {"tier": "tier2"}}}))
                self.assertTrue(
                    any(error.startswith("model_routing.routes:") and f"'{name}'" in error for error in errors),
                    errors,
                )

    def test_route_name_must_match_the_name_pattern(self) -> None:
        for name in ("Stage", "1stage", "has space", "x" * 49):
            with self.subTest(name=name):
                errors = _errors(self.validator, _config({"routes": {name: {"tier": "tier2"}}}))
                self.assertTrue(any(error.startswith("model_routing.routes:") for error in errors), errors)
        self.assertEqual(
            _errors(self.validator, _config({"routes": {"a" + "b" * 47: {"tier": "tier2"}}})),
            [],
        )

    def test_route_without_tier_fails_with_named_path(self) -> None:
        errors = _errors(self.validator, _config({"routes": {"reviewer": {"model_family": "m"}}}))
        self.assertIn("model_routing.routes.reviewer: 'tier' is a required property", errors)

    def test_route_tier_enum_and_unknown_keys_are_rejected(self) -> None:
        bad = {
            "bad-tier": {"tier": "tier4"},
            "bad-key": {"tier": "tier2", "model": "x"},
            "bad-context": {"tier": "tier2", "context_tier": "huge"},
        }
        for name, route in bad.items():
            with self.subTest(route=name):
                errors = _errors(self.validator, _config({"routes": {name: route}}))
                self.assertTrue(any(error.startswith(f"model_routing.routes.{name}") for error in errors), errors)

    def test_unknown_binding_key_shape_fails_with_named_path(self) -> None:
        for key in ("phases.architect", "agent:Upper", "agent:", "stage"):
            with self.subTest(key=key):
                errors = _errors(self.validator, _config({"bindings": {key: {"route": "r"}}}))
                self.assertTrue(
                    any(error.startswith("model_routing.bindings:") and f"'{key}'" in error for error in errors),
                    errors,
                )

    def test_binding_shape_is_closed(self) -> None:
        bad = {
            "missing-route": {"model_family": "m"},
            "non-string-route": {"route": 1},
            "unknown-key": {"route": "r", "tier": "tier2"},
        }
        for label, binding in bad.items():
            with self.subTest(binding=label):
                errors = _errors(self.validator, _config({"bindings": {"agent:x": binding}}))
                self.assertTrue(any(error.startswith("model_routing.bindings.agent:x") for error in errors), errors)

    def test_baseline_shaped_block_fails_with_named_paths(self) -> None:
        tier = {"model_family": "claude-sonnet-5.5", "model_provider": "anthropic", "reasoning_effort": "medium"}
        baseline = _config(
            {
                "tier1": dict(tier),
                "orchestrator": {**tier, "subagents": {"dispatcher": dict(tier)}},
                "stage": {**tier, "phases": {"discover": dict(tier)}},
                "ship": {
                    **tier,
                    "phases": {"implement": dict(tier)},
                    "escalation": {**tier, "max_cycles": 2, "fallback": dict(tier)},
                },
            }
        )
        errors = _errors(self.validator, baseline)
        for fragment in (
            "model_routing.tier1:",
            "model_routing.orchestrator:",
            "model_routing.stage: Additional properties are not allowed ('phases'",
            "model_routing.ship: Additional properties are not allowed ('phases'",
            "model_routing.ship.escalation: Additional properties are not allowed",
        ):
            with self.subTest(fragment=fragment):
                self.assertTrue(any(error.startswith(fragment) for error in errors), errors)


class ClosedModelRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = _validator(_MIRROR_1_2_0)

    def test_unknown_model_routing_key_fails_naming_the_key(self) -> None:
        errors = _errors(self.validator, _config({"routez": {}}))
        self.assertEqual(
            errors,
            ["model_routing: Additional properties are not allowed ('routez' was unexpected)"],
        )

    def test_inert_baseline_subagents_block_fails_naming_the_key(self) -> None:
        errors = _errors(self.validator, _config({"subagents": {"backlogit_ops": {"model_family": "m"}}}))
        self.assertEqual(
            errors,
            ["model_routing: Additional properties are not allowed ('subagents' was unexpected)"],
        )

    def test_every_dogfood_and_template_model_routing_key_is_allowlisted(self) -> None:
        dogfood = yaml.safe_load(_DOGFOOD_CONFIG.read_text(encoding="utf-8"))["model_routing"]
        rendered = _rendered_template_model_routing()
        for label, block in (("dogfood", dogfood), ("template", rendered)):
            with self.subTest(source=label):
                self.assertLessEqual(set(block), _MODEL_ROUTING_KEYS)


class LegacyMirrorUnchangedTests(unittest.TestCase):
    def test_1_1_0_documents_with_unknown_keys_still_validate_against_1_1_0(self) -> None:
        validator = _validator(_MIRROR_1_1_0)
        documents = (
            _config({"tier3": "claude-opus-5"}, "1.1.0"),
            _config({"routez": {}}, "1.1.0"),
            _config({"subagents": {"backlogit_ops": {"model_family": "m"}}}, "1.1.0"),
        )
        for document in documents:
            with self.subTest(document=document):
                self.assertEqual(_errors(validator, document), [])

    def test_1_1_0_mirror_still_pins_its_own_version(self) -> None:
        schema = _load_json(_MIRROR_1_1_0)
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.1.0")
        self.assertNotIn("additionalProperties", schema["properties"]["model_routing"])
        self.assertNotIn("routes", schema["properties"]["model_routing"]["properties"])


if __name__ == "__main__":
    unittest.main()
