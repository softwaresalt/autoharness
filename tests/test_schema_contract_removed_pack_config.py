"""harness-config contract 1.3.0: the retired agent-intercom pack (209-F U4).

209-F/216-S ships after 208-F/215-S, so the new version is the then-current
1.2.0 plus one. The published 0.9.0/1.0.0/1.1.0/1.2.0 mirrors stay byte-identical
(pinned below); a config pinned to any of them that lists the retired pack keeps
validating against the contract it was written against. The dogfood
.autoharness/config.yaml is operator-owned and deliberately stays at 1.2.0
(plan D-10).
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

from _config_schema_contract import CURRENT_CONFIG_SCHEMA_VERSION, current_config_mirror_path
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
_TEMPLATE = _REPO_ROOT / "templates" / "harness-config.yaml.tmpl"
_NEW_VERSION = "1.3.0"
_PREVIOUS_VERSION = "1.2.0"
_RETIRED = "agent-intercom"
_CONFIG_PATH = Path("config.yaml")

# SHA-256 of the LF-normalized bytes of the published mirrors (pre-209-F blobs).
_FROZEN_MIRROR_SHA256 = {
    "0.9.0": "37fde2f77c09c757c698d4c07e98aa7812a05dedcfe8ae2c275cb45f8a41ef69",
    "1.0.0": "13b9af4cd5cbc624be4ab421d2b670756f97664e0e7189d6b44b97407dba8d65",
    "1.1.0": "8e969547d17e946197a0b2f1106e5e5fcc14e96e115dde5d1e41d48b25b713d0",
    "1.2.0": "834a66c11c63e1d24ce02f36d6cebb8c335613b49cfba6efd64c44a719e78d30",
}


def _mirror(version: str) -> Path:
    return _MIRROR_DIR / f"{version}.schema.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _without_id(schema: dict) -> dict:
    clone = json.loads(json.dumps(schema))
    clone.pop("$id", None)
    return clone


def _errors(schema_path: Path, document: dict) -> list[str]:
    return [error.message for error in Draft7Validator(_load_json(schema_path)).iter_errors(document)]


class ConfigContractVersionTests(unittest.TestCase):
    def test_contract_reports_the_new_version_current_with_every_mirror_known(self) -> None:
        contract = SCHEMA_CONTRACTS["config"]
        self.assertEqual(contract["current_version"], _NEW_VERSION)
        self.assertEqual(tuple(contract["known_versions"]), ("0.9.0", "1.0.0", "1.1.0", "1.2.0", _NEW_VERSION))
        self.assertEqual(CURRENT_CONFIG_SCHEMA_VERSION, _NEW_VERSION)
        self.assertEqual(current_config_mirror_path(), _mirror(_NEW_VERSION))
        self.assertEqual(
            summarize_schema_contract("config", _CONFIG_PATH, {"schema_version": _NEW_VERSION})["status"], "current"
        )
        self.assertEqual(
            summarize_schema_contract("config", _CONFIG_PATH, {"schema_version": _PREVIOUS_VERSION})["status"],
            "known-legacy",
        )

    def test_resolve_contract_schema_path_selects_the_matching_mirror(self) -> None:
        for version in (*_FROZEN_MIRROR_SHA256, _NEW_VERSION):
            self.assertEqual(
                resolve_contract_schema_path("config", _REPO_ROOT, {"schema_version": version}), _mirror(version)
            )

    def test_previous_to_new_migration_entry(self) -> None:
        proposal_id = f"upgrade-config-contract-{_PREVIOUS_VERSION}-to-{_NEW_VERSION}"
        entries = [r for r in CONTRACT_MIGRATIONS["config"] if r["proposal_id"] == proposal_id]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["status"], "known-legacy")
        self.assertEqual(entries[0]["from_version"], _PREVIOUS_VERSION)
        self.assertEqual(entries[0]["to_version"], _NEW_VERSION)
        self.assertIn(f"schema_version to {_NEW_VERSION}", entries[0]["action"])

        legacy = plan_schema_contract_migrations("config", _CONFIG_PATH, {"schema_version": _PREVIOUS_VERSION}, [])
        self.assertIn(proposal_id, {p["proposal_id"] for p in legacy})
        current = plan_schema_contract_migrations("config", _CONFIG_PATH, {"schema_version": _NEW_VERSION}, [])
        self.assertNotIn(proposal_id, {p["proposal_id"] for p in current})

    def test_earlier_upgrade_entries_are_kept(self) -> None:
        ids = {r["proposal_id"] for r in CONTRACT_MIGRATIONS["config"]}
        self.assertIn("upgrade-config-contract-0.9.0-to-1.0.0", ids)
        self.assertIn("upgrade-config-contract-1.1.0-to-1.2.0", ids)


class ConfigCurrentVersionProposalTests(unittest.TestCase):
    def _proposal(self, proposal_id: str, document: dict, findings: list[dict] | None = None) -> dict:
        proposals = plan_schema_contract_migrations("config", _CONFIG_PATH, document, findings or [])
        matches = [p for p in proposals if p["proposal_id"] == proposal_id]
        self.assertEqual(len(matches), 1, proposal_id)
        return matches[0]

    def test_missing_version_backfill_targets_the_new_version(self) -> None:
        proposal = self._proposal("backfill-config-schema-version", {"preset": "full"})
        self.assertEqual(proposal["to_version"], _NEW_VERSION)
        self.assertIn(f"schema_version: {_NEW_VERSION}", proposal["action"])
        self.assertNotIn("1.0.0", proposal["action"])

    def test_unknown_version_review_targets_the_new_version(self) -> None:
        proposal = self._proposal("review-unknown-config-contract", {"schema_version": "9.9.9"})
        self.assertEqual(proposal["to_version"], _NEW_VERSION)
        self.assertTrue(proposal["manual_review"])

    def test_normalize_rule_targets_the_new_version_for_current_and_legacy_documents(self) -> None:
        rule = next(r for r in CONTRACT_MIGRATIONS["config"] if r["proposal_id"] == "normalize-legacy-config-capability-packs")
        self.assertEqual(rule["to_version"], _NEW_VERSION)
        finding = {"kind": "legacy-config-capability-pack", "legacy_value": "circuit-breaker"}
        for version in ("1.0.0", _PREVIOUS_VERSION, _NEW_VERSION):
            proposal = self._proposal(
                "normalize-legacy-config-capability-packs", {"schema_version": version}, [finding]
            )
            self.assertEqual(proposal["to_version"], _NEW_VERSION, version)


class ConfigMirrorTests(unittest.TestCase):
    def test_published_mirrors_are_byte_pinned(self) -> None:
        for version, digest in _FROZEN_MIRROR_SHA256.items():
            raw = _mirror(version).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest, version)

    def test_root_schema_equals_the_new_mirror_except_id_and_pins_the_version(self) -> None:
        root = _load_json(_ROOT_SCHEMA)
        mirror = _load_json(_mirror(_NEW_VERSION))
        self.assertNotEqual(root["$id"], mirror["$id"])
        self.assertEqual(
            mirror["$id"], f"https://softwaresalt.github.io/autoharness/schemas/harness-config/{_NEW_VERSION}.schema.json"
        )
        self.assertEqual(_without_id(root), _without_id(mirror))
        self.assertEqual(root["properties"]["schema_version"]["const"], _NEW_VERSION)

    def test_new_mirror_differs_from_the_previous_one_only_by_the_pack_and_version(self) -> None:
        previous = _without_id(_load_json(_mirror(_PREVIOUS_VERSION)))
        new = _without_id(_load_json(_mirror(_NEW_VERSION)))
        previous["properties"]["schema_version"]["const"] = _NEW_VERSION
        previous_enum = previous["properties"]["capability_packs"]["items"]["enum"]
        previous["properties"]["capability_packs"]["items"]["enum"] = [p for p in previous_enum if p != _RETIRED]
        self.assertIn(_RETIRED, previous_enum)
        self.assertEqual(new, previous)

    def test_config_pinned_to_an_earlier_version_listing_the_retired_pack_still_validates(self) -> None:
        for version in _FROZEN_MIRROR_SHA256:
            document = {"schema_version": version, "capability_packs": [_RETIRED, "backlogit"]}
            self.assertEqual(_errors(_mirror(version), document), [], version)

    def test_new_version_rejects_the_retired_pack_in_the_root_and_the_mirror(self) -> None:
        document = {"schema_version": _NEW_VERSION, "capability_packs": [_RETIRED, "backlogit"]}
        for schema_path in (_ROOT_SCHEMA, _mirror(_NEW_VERSION)):
            errors = _errors(schema_path, document)
            self.assertEqual(len(errors), 1, schema_path.name)
            self.assertIn(f"'{_RETIRED}' is not one of", errors[0])

    def test_new_version_accepts_every_remaining_pack(self) -> None:
        packs = _load_json(_mirror(_NEW_VERSION))["properties"]["capability_packs"]["items"]["enum"]
        self.assertNotIn(_RETIRED, packs)
        document = {"schema_version": _NEW_VERSION, "capability_packs": list(packs)}
        self.assertEqual(_errors(_mirror(_NEW_VERSION), document), [])

    def test_retired_pack_name_is_absent_from_the_root_and_the_new_mirror_text(self) -> None:
        for schema_path in (_ROOT_SCHEMA, _mirror(_NEW_VERSION)):
            self.assertNotIn("intercom", schema_path.read_text(encoding="utf-8").lower(), schema_path.name)


class ConfigTemplateAndDogfoodTests(unittest.TestCase):
    def test_template_pins_the_new_version(self) -> None:
        text = _TEMPLATE.read_text(encoding="utf-8")
        self.assertRegex(text, rf'(?m)^schema_version: "{re.escape(_NEW_VERSION)}"$')

    def test_operator_owned_dogfood_config_stays_on_the_previous_contract(self) -> None:
        config = yaml.safe_load((_REPO_ROOT / ".autoharness" / "config.yaml").read_text(encoding="utf-8"))
        self.assertEqual(config["schema_version"], _PREVIOUS_VERSION)
        self.assertEqual(resolve_contract_schema_path("config", _REPO_ROOT, config), _mirror(_PREVIOUS_VERSION))
        self.assertEqual(_errors(_mirror(_PREVIOUS_VERSION), config), [])


if __name__ == "__main__":
    unittest.main()
