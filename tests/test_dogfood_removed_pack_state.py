"""Dogfood install state after the agent-intercom pack was disabled (209-F U8)."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

from autoharness.verify_workspace import verify_workspace

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AUTOHARNESS = _REPO_ROOT / ".autoharness"
RETIRED = "agent-intercom"
PROFILE_ARTIFACT = ".autoharness/workspace-profile.yaml"
CONFIG_ARTIFACT = ".autoharness/config.yaml"


def _lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _load(name: str) -> dict:
    return yaml.safe_load((_AUTOHARNESS / name).read_text(encoding="utf-8"))


def _artifact(manifest: dict, path: str) -> dict:
    return next(item for item in manifest["artifacts"] if item["path"] == path)


class DogfoodPackStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = _load("harness-manifest.yaml")
        self.config = _load("config.yaml")
        self.profile = _load("workspace-profile.yaml")

    def test_pack_is_disabled_in_all_three_documents(self) -> None:
        self.assertNotIn(RETIRED, self.config["capability_packs"])
        self.assertNotIn(RETIRED, self.manifest["capability_packs"])
        self.assertNotIn(RETIRED, [o["pack"] for o in self.manifest["capability_pack_overlays"]])
        recommendations = self.profile["harness_recommendations"]
        self.assertNotIn(RETIRED, recommendations["capability_packs"])
        reasons = recommendations["recommendation_reasons"]["capability_packs"]
        self.assertNotIn(RETIRED, [reason["item"] for reason in reasons])
        self.assertNotIn("agent_intercom", self.profile)

    def test_remaining_packs_are_unchanged(self) -> None:
        expected = ["backlogit", "agent-engram", "graphtor-docs"]
        self.assertEqual(self.config["capability_packs"], expected)
        self.assertEqual(self.manifest["capability_packs"], expected)
        self.assertEqual(self.profile["harness_recommendations"]["capability_packs"], expected)

    def test_config_is_not_version_bumped(self) -> None:
        self.assertEqual(self.config["schema_version"], "1.2.0")

    def test_profile_and_manifest_are_minted_at_1_1_0_and_validate(self) -> None:
        self.assertEqual(self.profile["schema_version"], "1.1.0")
        self.assertEqual(self.manifest["schema_version"], "1.1.0")
        for kind, document in (("workspace-profile", self.profile), ("harness-manifest", self.manifest)):
            with self.subTest(kind=kind):
                schema = json.loads((_REPO_ROOT / "schemas" / kind / "1.1.0.schema.json").read_text(encoding="utf-8"))
                self.assertEqual([e.message for e in Draft7Validator(schema).iter_errors(document)], [])

    def test_config_integrity_records_match_the_lf_blob(self) -> None:
        digest = _lf_sha256(_AUTOHARNESS / "config.yaml")
        self.assertEqual(self.manifest["config_hash"], digest)
        self.assertEqual(_artifact(self.manifest, CONFIG_ARTIFACT)["checksum"], digest)

    def test_profile_integrity_pair_matches_the_lf_blob(self) -> None:
        digest = _lf_sha256(_AUTOHARNESS / "workspace-profile.yaml")
        self.assertEqual(self.manifest["profile_hash"], digest)
        self.assertEqual(_artifact(self.manifest, PROFILE_ARTIFACT)["checksum"], digest)

    def test_dogfood_verify_has_no_blockers_and_no_removed_pack_warning(self) -> None:
        with tempfile.TemporaryDirectory() as staging:
            report = verify_workspace(_REPO_ROOT, _REPO_ROOT, Path(staging))
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["strict_schema_blockers"], [])
        self.assertEqual([w for w in report["warnings"] if w.get("kind") == "removed-capability-pack"], [])
        self.assertEqual([p for p in report["migration_proposals"] if p.get("proposal_id") == "remove-retired-capability-pack"], [])


if __name__ == "__main__":
    unittest.main()
