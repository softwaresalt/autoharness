"""harness-manifest contract 1.1.0: the retired agent-intercom pack (209-F U3).

Same pattern as the workspace-profile bump (U2): the published 0.9.0 and 1.0.0
mirrors stay byte-identical (pinned below) so a legacy manifest listing the
retired pack keeps validating against the contract it was written against; the
new 1.1.0 mirror drops the value from both pack enums.
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
_ROOT_SCHEMA = _REPO_ROOT / "schemas" / "harness-manifest.schema.json"
_MIRROR_DIR = _REPO_ROOT / "schemas" / "harness-manifest"
_MIRROR_0_9_0 = _MIRROR_DIR / "0.9.0.schema.json"
_MIRROR_1_0_0 = _MIRROR_DIR / "1.0.0.schema.json"
_MIRROR_1_1_0 = _MIRROR_DIR / "1.1.0.schema.json"

# SHA-256 of the LF-normalized bytes of the published mirrors (pre-209-F blobs
# c5e96c78e8c9d1786d12bad9a7450a4dcb2c9a46 and e0e47e745da0a90df7eaeec0520df80abe2bc507).
_MIRROR_0_9_0_SHA256 = "f4b3d30d495712b938aaf57c9bfe5ba3aaee79993d66988e89f12a712019b03b"
_MIRROR_1_0_0_SHA256 = "e936c481167425e8d9b975e526035bb87baa0ef51430c706865e01010df4614c"

_RETIRED = "agent-intercom"
_MANIFEST_PATH = Path("harness-manifest.yaml")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _manifest(version: str) -> dict:
    return {
        "schema_version": version,
        "installed_at": "2026-10-18T00:00:00Z",
        "autoharness_version": "1.0.0",
        "profile_hash": "abc",
        "primitives_installed": [1],
        "artifacts": [],
    }


def _with_pack(manifest: dict, pack: str) -> dict:
    clone = copy.deepcopy(manifest)
    clone["capability_packs"] = [pack, "backlogit"]
    clone["capability_pack_overlays"] = [
        {"pack": pack, "overlay_targets": [], "verification_checks": []},
    ]
    return clone


def _errors(schema_path: Path, document: dict) -> list[str]:
    return [error.message for error in Draft7Validator(_load_json(schema_path)).iter_errors(document)]


def _pack_enums(schema: dict) -> list[list[str]]:
    props = schema["properties"]
    return [
        props["capability_packs"]["items"]["enum"],
        props["capability_pack_overlays"]["items"]["properties"]["pack"]["enum"],
    ]


class ManifestContractVersionTests(unittest.TestCase):
    def test_contract_reports_1_1_0_current_with_all_mirrors_known(self) -> None:
        contract = SCHEMA_CONTRACTS["manifest"]
        self.assertEqual(contract["current_version"], "1.1.0")
        self.assertEqual(tuple(contract["known_versions"]), ("0.9.0", "1.0.0", "1.1.0"))
        self.assertEqual(
            summarize_schema_contract("manifest", _MANIFEST_PATH, _manifest("1.1.0"))["status"], "current"
        )
        self.assertEqual(
            summarize_schema_contract("manifest", _MANIFEST_PATH, _manifest("1.0.0"))["status"], "known-legacy"
        )

    def test_resolve_contract_schema_path_selects_the_matching_mirror(self) -> None:
        for version, mirror in (("0.9.0", _MIRROR_0_9_0), ("1.0.0", _MIRROR_1_0_0), ("1.1.0", _MIRROR_1_1_0)):
            self.assertEqual(
                resolve_contract_schema_path("manifest", _REPO_ROOT, {"schema_version": version}), mirror
            )

    def test_one_dot_zero_to_one_dot_one_migration_entry(self) -> None:
        entries = [
            r for r in CONTRACT_MIGRATIONS["manifest"] if r["proposal_id"] == "upgrade-manifest-contract-1.0.0-to-1.1.0"
        ]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["status"], "known-legacy")
        self.assertEqual(entries[0]["from_version"], "1.0.0")
        self.assertEqual(entries[0]["to_version"], "1.1.0")
        self.assertIn("1.1.0", entries[0]["action"])

        legacy = plan_schema_contract_migrations("manifest", _MANIFEST_PATH, _manifest("1.0.0"), [])
        self.assertIn("upgrade-manifest-contract-1.0.0-to-1.1.0", {p["proposal_id"] for p in legacy})
        current = plan_schema_contract_migrations("manifest", _MANIFEST_PATH, _manifest("1.1.0"), [])
        self.assertNotIn("upgrade-manifest-contract-1.0.0-to-1.1.0", {p["proposal_id"] for p in current})

    def test_historical_zero_nine_upgrade_entry_is_kept(self) -> None:
        ids = {r["proposal_id"] for r in CONTRACT_MIGRATIONS["manifest"]}
        self.assertIn("upgrade-manifest-contract-0.9.0-to-1.0.0", ids)


class ManifestCurrentVersionProposalTests(unittest.TestCase):
    def _proposal(self, proposal_id: str, document: dict, findings: list[dict] | None = None) -> dict:
        proposals = plan_schema_contract_migrations("manifest", _MANIFEST_PATH, document, findings or [])
        matches = [p for p in proposals if p["proposal_id"] == proposal_id]
        self.assertEqual(len(matches), 1, proposal_id)
        return matches[0]

    def test_missing_version_backfill_targets_1_1_0(self) -> None:
        document = _manifest("1.1.0")
        del document["schema_version"]
        proposal = self._proposal("backfill-manifest-schema-version", document)
        self.assertEqual(proposal["to_version"], "1.1.0")
        self.assertIn("schema_version: 1.1.0", proposal["action"])
        self.assertNotIn("1.0.0", proposal["action"])

    def test_unknown_version_review_targets_1_1_0(self) -> None:
        proposal = self._proposal("review-unknown-manifest-contract", _manifest("9.9.9"))
        self.assertEqual(proposal["to_version"], "1.1.0")
        self.assertTrue(proposal["manual_review"])

    def test_normalize_rule_targets_1_1_0_and_applies_to_current_and_legacy_documents(self) -> None:
        rule = next(r for r in CONTRACT_MIGRATIONS["manifest"] if r["proposal_id"] == "normalize-legacy-manifest-capability-packs")
        self.assertEqual(rule["to_version"], "1.1.0")
        finding = {"kind": "legacy-manifest-capability-pack", "legacy_value": "circuit-breaker"}
        for version in ("1.0.0", "1.1.0"):
            proposal = self._proposal("normalize-legacy-manifest-capability-packs", _manifest(version), [finding])
            self.assertEqual(proposal["to_version"], "1.1.0", version)


class ManifestMirrorTests(unittest.TestCase):
    def test_published_mirrors_are_byte_pinned(self) -> None:
        self.assertEqual(_sha256_lf(_MIRROR_0_9_0), _MIRROR_0_9_0_SHA256)
        self.assertEqual(_sha256_lf(_MIRROR_1_0_0), _MIRROR_1_0_0_SHA256)

    def test_root_schema_equals_1_1_0_mirror_and_pins_the_version(self) -> None:
        root = _load_json(_ROOT_SCHEMA)
        self.assertEqual(root, _load_json(_MIRROR_1_1_0))
        self.assertEqual(root["properties"]["schema_version"]["const"], "1.1.0")

    def test_legacy_1_0_0_manifest_listing_the_retired_pack_still_validates(self) -> None:
        self.assertEqual(_errors(_MIRROR_1_0_0, _with_pack(_manifest("1.0.0"), _RETIRED)), [])

    def test_1_1_0_rejects_the_retired_pack_in_both_enums(self) -> None:
        for schema_path in (_ROOT_SCHEMA, _MIRROR_1_1_0):
            errors = _errors(schema_path, _with_pack(_manifest("1.1.0"), _RETIRED))
            self.assertEqual(len(errors), 2, schema_path.name)
            for error in errors:
                self.assertIn(f"'{_RETIRED}' is not one of", error)

    def test_1_1_0_accepts_every_remaining_pack(self) -> None:
        enums = _pack_enums(_load_json(_MIRROR_1_1_0))
        self.assertEqual(enums[0], enums[1])
        for pack in enums[0]:
            self.assertEqual(_errors(_MIRROR_1_1_0, _with_pack(_manifest("1.1.0"), pack)), [], pack)

    def test_1_1_0_enums_are_the_legacy_enums_minus_the_retired_pack(self) -> None:
        legacy = _pack_enums(_load_json(_MIRROR_1_0_0))
        current = _pack_enums(_load_json(_MIRROR_1_1_0))
        for legacy_enum, current_enum in zip(legacy, current):
            self.assertIn(_RETIRED, legacy_enum)
            self.assertEqual([p for p in legacy_enum if p != _RETIRED], current_enum)

    def test_retired_pack_name_is_absent_from_root_and_new_mirror_text(self) -> None:
        for schema_path in (_ROOT_SCHEMA, _MIRROR_1_1_0):
            self.assertNotIn("intercom", schema_path.read_text(encoding="utf-8").lower(), schema_path.name)


if __name__ == "__main__":
    unittest.main()
