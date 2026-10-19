"""Contract cut-over tests for harness-config schema 1.2.0 (208-F B5).

The root schema, ``SCHEMA_CONTRACTS['config']``, the 1.2.0 mirror and the dogfood
marker flip together. The published 1.1.0 mirror is never edited in place: it is
pinned by a byte hash so the in-place-mutation bug class cannot recur
(docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md).
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

from autoharness.schema_contracts import (
    CONTRACT_MIGRATIONS,
    SCHEMA_CONTRACTS,
    plan_schema_contract_migrations,
    resolve_contract_schema_path,
    summarize_schema_contract,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ROOT_SCHEMA = _REPO_ROOT / "schemas" / "harness-config.schema.json"
_MIRROR_DIR = _REPO_ROOT / "schemas" / "harness-config"
_MIRROR_1_1_0 = _MIRROR_DIR / "1.1.0.schema.json"
_MIRROR_1_2_0 = _MIRROR_DIR / "1.2.0.schema.json"
_DOGFOOD_CONFIG = _REPO_ROOT / ".autoharness" / "config.yaml"

# SHA-256 of the LF-normalized bytes of the published 1.1.0 mirror.
_MIRROR_1_1_0_SHA256 = "8e969547d17e946197a0b2f1106e5e5fcc14e96e115dde5d1e41d48b25b713d0"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _without_id(schema: dict) -> dict:
    clone = json.loads(json.dumps(schema))
    clone.pop("$id", None)
    return clone


class ConfigContractVersionTests(unittest.TestCase):
    def test_contract_reports_1_2_0_current_and_1_1_0_known_legacy(self) -> None:
        contract = SCHEMA_CONTRACTS["config"]
        self.assertEqual(contract["current_version"], "1.2.0")
        self.assertIn("1.1.0", contract["known_versions"])
        self.assertIn("1.2.0", contract["known_versions"])

        current = summarize_schema_contract("config", Path("config.yaml"), {"schema_version": "1.2.0"})
        self.assertEqual(current["status"], "current")
        legacy = summarize_schema_contract("config", Path("config.yaml"), {"schema_version": "1.1.0"})
        self.assertEqual(legacy["status"], "known-legacy")

    def test_resolve_contract_schema_path_selects_matching_mirror(self) -> None:
        self.assertEqual(
            resolve_contract_schema_path("config", _REPO_ROOT, {"schema_version": "1.2.0"}),
            _MIRROR_1_2_0,
        )
        self.assertEqual(
            resolve_contract_schema_path("config", _REPO_ROOT, {"schema_version": "1.1.0"}),
            _MIRROR_1_1_0,
        )

    def test_known_legacy_1_1_0_config_gets_the_upgrade_proposal(self) -> None:
        entries = [r for r in CONTRACT_MIGRATIONS["config"] if r["proposal_id"] == "upgrade-config-contract-1.1.0-to-1.2.0"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["status"], "known-legacy")
        self.assertEqual(entries[0]["from_version"], "1.1.0")
        self.assertEqual(entries[0]["to_version"], "1.2.0")

        proposals = plan_schema_contract_migrations(
            "config", Path("config.yaml"), {"schema_version": "1.1.0"}, []
        )
        ids = {proposal["proposal_id"] for proposal in proposals}
        self.assertIn("upgrade-config-contract-1.1.0-to-1.2.0", ids)

        current = plan_schema_contract_migrations(
            "config", Path("config.yaml"), {"schema_version": "1.2.0"}, []
        )
        self.assertNotIn("upgrade-config-contract-1.1.0-to-1.2.0", {p["proposal_id"] for p in current})


class ConfigSchemaMirrorTests(unittest.TestCase):
    def test_legacy_1_1_0_mirror_preserved_unchanged(self) -> None:
        raw = _MIRROR_1_1_0.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _MIRROR_1_1_0_SHA256)

    def test_legacy_1_1_0_mirror_keeps_open_model_routing(self) -> None:
        # Moved from test_anchor_review_routing: model_routing stays open at 1.1.0,
        # so a custom route key keeps validating against the untouched mirror.
        schema = _load_json(_MIRROR_1_1_0)
        self.assertNotIn("additionalProperties", schema["properties"]["model_routing"])
        custom_route = {
            "schema_version": "1.1.0",
            "model_routing": {"workspace_specific_review": {"model_provider": "local", "model_family": "custom"}},
        }
        self.assertTrue(Draft7Validator(schema).is_valid(custom_route))

    def test_root_schema_equals_1_2_0_mirror_except_id(self) -> None:
        root = _load_json(_ROOT_SCHEMA)
        mirror = _load_json(_MIRROR_1_2_0)
        self.assertNotEqual(root["$id"], mirror["$id"])
        self.assertEqual(_without_id(root), _without_id(mirror))
        self.assertEqual(root["properties"]["schema_version"]["const"], "1.2.0")

    def test_root_schema_carries_catalog_bindings_and_closed_model_routing(self) -> None:
        model_routing = _load_json(_ROOT_SCHEMA)["properties"]["model_routing"]
        self.assertIn("routes", model_routing["properties"])
        self.assertIn("bindings", model_routing["properties"])
        self.assertIs(model_routing["additionalProperties"], False)

    def test_dogfood_config_validates_against_root_and_current_mirror(self) -> None:
        config = yaml.safe_load(_DOGFOOD_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(config["schema_version"], "1.2.0")
        for path in (_ROOT_SCHEMA, _MIRROR_1_2_0):
            validator = Draft7Validator(_load_json(path))
            self.assertEqual([e.message for e in validator.iter_errors(config)], [], path.name)

    def test_dogfood_config_selects_current_mirror(self) -> None:
        config = yaml.safe_load(_DOGFOOD_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(resolve_contract_schema_path("config", _REPO_ROOT, config), _MIRROR_1_2_0)
        self.assertEqual(summarize_schema_contract("config", _DOGFOOD_CONFIG, config)["status"], "current")


if __name__ == "__main__":
    unittest.main()
