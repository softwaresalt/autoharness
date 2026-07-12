"""TDD-red tests locking the graphtor-docs full-suite contract (feature 076-F).

These tests fail until graphtor-docs is completed to agent-engram parity:
* the versioned ``harness-config/1.0.0`` schema must match the root config schema
  (capability_packs enum + ``graphtor_docs`` config block);
* the versioned ``workspace-profile/1.0.0`` schema must carry the ``graphtor_docs``
  structural block that the root profile schema already declares;
* a ``full`` config enabling graphtor-docs must validate against the versioned
  config schema;
* every registered capability pack (including graphtor-docs) must default into the
  ``full`` preset.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml
from jsonschema import validate

_REPO = Path(__file__).resolve().parents[1]
_ROOT_CONFIG = _REPO / "schemas" / "harness-config.schema.json"
_VER_CONFIG = _REPO / "schemas" / "harness-config" / "1.0.0.schema.json"
_ROOT_PROFILE = _REPO / "schemas" / "workspace-profile.schema.json"
_VER_PROFILE = _REPO / "schemas" / "workspace-profile" / "1.0.0.schema.json"
_REGISTRY = _REPO / "templates" / "packs" / "capability-pack-registry.yaml"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class GraphtorDocsSchemaParityTests(unittest.TestCase):
    """Root and versioned schemas must cover graphtor-docs identically."""

    def test_versioned_config_enum_equals_root_config_enum(self) -> None:
        root_enum = set(
            _load_json(_ROOT_CONFIG)["properties"]["capability_packs"]["items"]["enum"]
        )
        ver_enum = set(
            _load_json(_VER_CONFIG)["properties"]["capability_packs"]["items"]["enum"]
        )
        self.assertEqual(
            ver_enum,
            root_enum,
            "versioned harness-config capability_packs enum diverges from root",
        )
        self.assertIn("graphtor-docs", ver_enum)

    def test_versioned_config_has_graphtor_docs_block(self) -> None:
        root_block = _load_json(_ROOT_CONFIG)["properties"]["graphtor_docs"]
        ver_props = _load_json(_VER_CONFIG)["properties"]
        self.assertIn(
            "graphtor_docs",
            ver_props,
            "versioned harness-config is missing the graphtor_docs config block",
        )
        self.assertEqual(
            ver_props["graphtor_docs"],
            root_block,
            "versioned graphtor_docs config block diverges from root",
        )

    def test_versioned_profile_has_graphtor_docs_block(self) -> None:
        root_block = _load_json(_ROOT_PROFILE)["properties"]["graphtor_docs"]
        ver_props = _load_json(_VER_PROFILE)["properties"]
        self.assertIn(
            "graphtor_docs",
            ver_props,
            "versioned workspace-profile is missing the graphtor_docs block",
        )
        self.assertEqual(
            ver_props["graphtor_docs"],
            root_block,
            "versioned graphtor_docs profile block diverges from root",
        )

    def test_full_config_enabling_graphtor_docs_validates_versioned(self) -> None:
        schema = _load_json(_VER_CONFIG)
        config = {
            "schema_version": "1.0.0",
            "capability_packs": ["graphtor-docs"],
            "graphtor_docs": {
                "sources_path": ".graphtor/config/sources.yaml",
                "binary_path": None,
                "embed_model_dir": None,
            },
        }
        validate(config, schema)


class GraphtorDocsFullPresetMembershipTests(unittest.TestCase):
    """Every registered pack must be a default member of the ``full`` preset."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.packs = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))["packs"]

    def test_every_pack_defaults_into_full_preset(self) -> None:
        for pack in self.packs:
            self.assertIn(
                "full",
                pack["default_in_preset"],
                f"pack {pack['id']!r} is not a default of the full preset",
            )

    def test_graphtor_docs_defaults_into_full_preset(self) -> None:
        graphtor = next(p for p in self.packs if p["id"] == "graphtor-docs")
        self.assertIn("full", graphtor["default_in_preset"])


if __name__ == "__main__":
    unittest.main()
