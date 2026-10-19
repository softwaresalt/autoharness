"""workspace-profile contract 1.1.0: the retired agent-intercom pack (209-F U2).

Removing a pack from the profile enums is a restrictive contract change, so it
ships as a NEW 1.1.0 mirror; the published 0.9.0 and 1.0.0 mirrors stay
byte-identical (pinned below) so legacy profiles keep validating against the
contract they were written against
(docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md).
"""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft7Validator

from autoharness.schema_contracts import (
    CONTRACT_MIGRATIONS,
    SCHEMA_CONTRACTS,
    plan_schema_contract_migrations,
    resolve_contract_schema_path,
    summarize_schema_contract,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ROOT_SCHEMA = _REPO_ROOT / "schemas" / "workspace-profile.schema.json"
_MIRROR_DIR = _REPO_ROOT / "schemas" / "workspace-profile"
_MIRROR_0_9_0 = _MIRROR_DIR / "0.9.0.schema.json"
_MIRROR_1_0_0 = _MIRROR_DIR / "1.0.0.schema.json"
_MIRROR_1_1_0 = _MIRROR_DIR / "1.1.0.schema.json"

# SHA-256 of the LF-normalized bytes of the published mirrors (pre-209-F blobs
# 0dbe68f7a05bc5bc67aa12619db8fe35ef8dd82e and 9dc2f5e21ea467406f378c7ecdd8fc999dab4ba9).
_MIRROR_0_9_0_SHA256 = "d91b2dfabd55979160fa89e2b2d2a8968b995bda1d0fd66013548769d57bf59f"
_MIRROR_1_0_0_SHA256 = "8325e03a2f5466fdb803f1a7a5961d283f0b1f2068d3671ac090946c209eea01"

_RETIRED = "agent-intercom"
_PROFILE_PATH = Path("workspace-profile.yaml")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _profile(version: str) -> dict:
    return {
        "schema_version": version,
        "generated_at": "2026-10-18T00:00:00Z",
        "workspace_path": ".",
        "languages": {"primary": "python"},
        "build": {"tool": "pip", "command": "pip install -e ."},
        "test": {"runner": "unittest", "command": "python -m unittest"},
    }


def _with_retired_recommendation(profile: dict) -> dict:
    clone = copy.deepcopy(profile)
    clone["harness_recommendations"] = {
        "capability_packs": [_RETIRED, "backlogit"],
        "recommendation_reasons": {
            "capability_packs": [{"item": _RETIRED, "because": "legacy marker", "signals": []}]
        },
    }
    return clone


def _errors(schema_path: Path, document: dict) -> list[str]:
    return [error.message for error in Draft7Validator(_load_json(schema_path)).iter_errors(document)]


class ProfileContractVersionTests(unittest.TestCase):
    def test_contract_reports_1_1_0_current_with_all_mirrors_known(self) -> None:
        contract = SCHEMA_CONTRACTS["profile"]
        self.assertEqual(contract["current_version"], "1.1.0")
        self.assertEqual(tuple(contract["known_versions"]), ("0.9.0", "1.0.0", "1.1.0"))
        self.assertEqual(
            summarize_schema_contract("profile", _PROFILE_PATH, _profile("1.1.0"))["status"], "current"
        )
        self.assertEqual(
            summarize_schema_contract("profile", _PROFILE_PATH, _profile("1.0.0"))["status"], "known-legacy"
        )

    def test_resolve_contract_schema_path_selects_the_matching_mirror(self) -> None:
        for version, mirror in (("0.9.0", _MIRROR_0_9_0), ("1.0.0", _MIRROR_1_0_0), ("1.1.0", _MIRROR_1_1_0)):
            self.assertEqual(
                resolve_contract_schema_path("profile", _REPO_ROOT, {"schema_version": version}), mirror
            )

    def test_one_dot_zero_to_one_dot_one_migration_entry(self) -> None:
        entries = [r for r in CONTRACT_MIGRATIONS["profile"] if r["proposal_id"] == "upgrade-profile-contract-1.0.0-to-1.1.0"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["status"], "known-legacy")
        self.assertEqual(entries[0]["from_version"], "1.0.0")
        self.assertEqual(entries[0]["to_version"], "1.1.0")
        self.assertIn("1.1.0", entries[0]["action"])

        legacy = plan_schema_contract_migrations("profile", _PROFILE_PATH, _profile("1.0.0"), [])
        self.assertIn("upgrade-profile-contract-1.0.0-to-1.1.0", {p["proposal_id"] for p in legacy})
        current = plan_schema_contract_migrations("profile", _PROFILE_PATH, _profile("1.1.0"), [])
        self.assertNotIn("upgrade-profile-contract-1.0.0-to-1.1.0", {p["proposal_id"] for p in current})

    def test_historical_zero_nine_upgrade_entry_is_kept(self) -> None:
        ids = {r["proposal_id"] for r in CONTRACT_MIGRATIONS["profile"]}
        self.assertIn("upgrade-profile-contract-0.9.0-to-1.0.0", ids)


class ProfileCurrentVersionProposalTests(unittest.TestCase):
    def _proposal(self, proposal_id: str, document: dict) -> dict:
        proposals = plan_schema_contract_migrations("profile", _PROFILE_PATH, document, [])
        matches = [p for p in proposals if p["proposal_id"] == proposal_id]
        self.assertEqual(len(matches), 1, proposal_id)
        return matches[0]

    def test_missing_version_backfill_targets_1_1_0(self) -> None:
        document = _profile("1.1.0")
        del document["schema_version"]
        proposal = self._proposal("backfill-profile-schema-version", document)
        self.assertEqual(proposal["to_version"], "1.1.0")
        self.assertIn("schema_version: 1.1.0", proposal["action"])
        self.assertNotIn("1.0.0", proposal["action"])

    def test_unknown_version_review_targets_1_1_0(self) -> None:
        proposal = self._proposal("review-unknown-profile-contract", _profile("9.9.9"))
        self.assertEqual(proposal["to_version"], "1.1.0")
        self.assertTrue(proposal["manual_review"])

    def test_normalize_rules_target_1_1_0_and_apply_to_current_and_legacy_documents(self) -> None:
        rules = {
            r["proposal_id"]: r
            for r in CONTRACT_MIGRATIONS["profile"]
            if r["proposal_id"].startswith("normalize-legacy-profile-")
        }
        self.assertEqual(
            set(rules),
            {"normalize-legacy-profile-drift-categories", "normalize-legacy-profile-capability-packs"},
        )
        for rule in rules.values():
            self.assertEqual(rule["to_version"], "1.1.0")

        finding = {"kind": "legacy-profile-drift-category", "legacy_value": "deleted_artifact"}
        for version in ("1.0.0", "1.1.0"):
            proposals = plan_schema_contract_migrations("profile", _PROFILE_PATH, _profile(version), [finding])
            self.assertIn("normalize-legacy-profile-drift-categories", {p["proposal_id"] for p in proposals}, version)


class ProfileMirrorTests(unittest.TestCase):
    def test_published_mirrors_are_byte_pinned(self) -> None:
        self.assertEqual(_sha256_lf(_MIRROR_0_9_0), _MIRROR_0_9_0_SHA256)
        self.assertEqual(_sha256_lf(_MIRROR_1_0_0), _MIRROR_1_0_0_SHA256)

    def test_root_schema_equals_1_1_0_mirror_and_pins_the_version(self) -> None:
        root = _load_json(_ROOT_SCHEMA)
        mirror = _load_json(_MIRROR_1_1_0)
        self.assertEqual(root, mirror)
        self.assertEqual(root["properties"]["schema_version"]["const"], "1.1.0")

    def test_legacy_1_0_0_profile_listing_the_retired_pack_still_validates(self) -> None:
        profile = _with_retired_recommendation(_profile("1.0.0"))
        profile["agent_intercom"] = {"detected": True, "config_paths": [], "instruction_markers": [], "recommended": True}
        self.assertEqual(_errors(_MIRROR_1_0_0, profile), [])

    def test_1_1_0_rejects_the_retired_pack_in_both_enums(self) -> None:
        for schema_path in (_ROOT_SCHEMA, _MIRROR_1_1_0):
            errors = _errors(schema_path, _with_retired_recommendation(_profile("1.1.0")))
            self.assertEqual(len(errors), 2, schema_path.name)
            for error in errors:
                self.assertIn(f"'{_RETIRED}' is not one of", error)

    def test_1_1_0_still_accepts_the_remaining_packs(self) -> None:
        profile = _profile("1.1.0")
        profile["harness_recommendations"] = {
            "capability_packs": ["backlogit", "agent-engram", "graphtor-docs"],
            "recommendation_reasons": {
                "capability_packs": [{"item": "backlogit", "because": "backlog markers", "signals": []}]
            },
        }
        self.assertEqual(_errors(_MIRROR_1_1_0, profile), [])

    def test_1_1_0_drops_the_agent_intercom_property_but_keeps_the_root_open(self) -> None:
        for schema_path in (_ROOT_SCHEMA, _MIRROR_1_1_0):
            schema = _load_json(schema_path)
            self.assertNotIn("agent_intercom", schema["properties"], schema_path.name)
            self.assertNotIn("additionalProperties", schema, schema_path.name)
        # The root is deliberately NOT closed: a profile that only carries the legacy
        # block still validates, and the block is detected by the U6 collector instead.
        legacy_block = _profile("1.1.0")
        legacy_block["agent_intercom"] = {"detected": True}
        self.assertEqual(_errors(_MIRROR_1_1_0, legacy_block), [])

    def test_retired_pack_name_is_absent_from_root_and_new_mirror_text(self) -> None:
        for schema_path in (_ROOT_SCHEMA, _MIRROR_1_1_0):
            self.assertNotIn("intercom", schema_path.read_text(encoding="utf-8").lower(), schema_path.name)


if __name__ == "__main__":
    unittest.main()
