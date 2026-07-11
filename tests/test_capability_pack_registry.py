"""Tests for the capability-pack registry schema and data file.

Verifies the additive capability-pack catalog (schemas/capability-pack-registry.schema.json
+ templates/packs/capability-pack-registry.yaml) stays valid and enum-aligned with
the closed pack enum in harness-config.schema.json (the validation authority).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, validate

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "capability-pack-registry.schema.json"
_DATA_PATH = _REPO_ROOT / "templates" / "packs" / "capability-pack-registry.yaml"
_HARNESS_CONFIG_SCHEMA = _REPO_ROOT / "schemas" / "harness-config.schema.json"
_INSTRUCTIONS_DIR = _REPO_ROOT / "templates" / "instructions"

_EXPECTED_PACK_IDS = {
    "agent-intercom",
    "agent-engram",
    "backlogit",
    "browser-verification",
    "continuous-learning",
    "strict-safety",
    "release-observability",
    "adversarial-review",
    "graphtor-docs",
}


class CapabilityPackRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.data = yaml.safe_load(_DATA_PATH.read_text(encoding="utf-8"))

    def test_schema_is_valid_draft07(self) -> None:
        Draft7Validator.check_schema(self.schema)

    def test_registry_validates_against_schema(self) -> None:
        validate(self.data, self.schema)

    def test_schema_version_is_pinned(self) -> None:
        self.assertEqual(self.data["schema_version"], "1.0.0")

    def test_pack_id_set_equals_nine_names(self) -> None:
        ids = [p["id"] for p in self.data["packs"]]
        self.assertEqual(len(ids), 9)
        self.assertEqual(len(ids), len(set(ids)), "duplicate pack ids")
        self.assertEqual(set(ids), _EXPECTED_PACK_IDS)

    def test_id_enum_aligned_with_harness_config(self) -> None:
        config = json.loads(_HARNESS_CONFIG_SCHEMA.read_text(encoding="utf-8"))
        config_enum = set(config["properties"]["capability_packs"]["items"]["enum"])
        registry_enum = set(
            self.schema["definitions"]["pack"]["properties"]["id"]["enum"]
        )
        self.assertEqual(registry_enum, config_enum)
        self.assertEqual(registry_enum, _EXPECTED_PACK_IDS)

    def test_overlay_instruction_paths_exist_or_empty(self) -> None:
        for pack in self.data["packs"]:
            overlay = pack["overlay_instruction"]
            if overlay == "":
                self.assertEqual(
                    pack["id"],
                    "adversarial-review",
                    "only adversarial-review may omit an overlay instruction",
                )
                continue
            self.assertTrue(
                (_REPO_ROOT / overlay).is_file(),
                f"missing overlay instruction for {pack['id']}: {overlay}",
            )

    def test_primitive_impact_within_range(self) -> None:
        for pack in self.data["packs"]:
            impacts = pack["primitive_impact"]
            self.assertTrue(impacts, f"{pack['id']} has empty primitive_impact")
            for n in impacts:
                self.assertGreaterEqual(n, 1)
                self.assertLessEqual(n, 10)

    def test_default_in_preset_values_are_valid(self) -> None:
        allowed = {"starter", "standard", "full"}
        for pack in self.data["packs"]:
            self.assertTrue(set(pack["default_in_preset"]).issubset(allowed))

    def test_retrieval_enforced_is_optional_boolean(self) -> None:
        pack_props = self.schema["definitions"]["pack"]["properties"]
        self.assertIn(
            "retrieval_enforced",
            pack_props,
            "retrieval_enforced must be declared (schema is additionalProperties:false)",
        )
        self.assertEqual(pack_props["retrieval_enforced"]["type"], "boolean")
        required = set(self.schema["definitions"]["pack"]["required"])
        self.assertNotIn(
            "retrieval_enforced", required, "retrieval_enforced must remain optional"
        )

    def test_exactly_engram_and_graphtor_are_retrieval_enforced(self) -> None:
        marked = {
            p["id"] for p in self.data["packs"] if p.get("retrieval_enforced") is True
        }
        self.assertEqual(marked, {"agent-engram", "graphtor-docs"})


if __name__ == "__main__":
    unittest.main()
