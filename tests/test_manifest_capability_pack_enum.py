"""Guards that the harness-manifest schema pack enums cover every enabled pack.

`graphtor-docs` was originally absent from the manifest schema pack enums even
though the dogfood manifest (and any install that selects graphtor-docs) lists
it in ``capability_packs`` and ``capability_pack_overlays``. That made such
manifests schema-invalid. These tests lock the enum coverage and prove the
dogfood manifest validates on the capability-pack surface.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST_SCHEMAS = (
    _REPO_ROOT / "schemas" / "harness-manifest.schema.json",
    _REPO_ROOT / "schemas" / "harness-manifest" / "1.0.0.schema.json",
)
_DOGFOOD_MANIFEST = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"


def _pack_enums(schema: dict) -> list[list[str]]:
    props = schema["properties"]
    return [
        props["capability_packs"]["items"]["enum"],
        props["capability_pack_overlays"]["items"]["properties"]["pack"]["enum"],
    ]


class ManifestPackEnumTests(unittest.TestCase):
    def test_graphtor_docs_in_both_enums_of_both_schema_files(self) -> None:
        for schema_path in _MANIFEST_SCHEMAS:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            for enum in _pack_enums(schema):
                self.assertIn(
                    "graphtor-docs",
                    enum,
                    f"graphtor-docs missing from a pack enum in {schema_path.name}",
                )

    def test_both_schema_files_share_identical_pack_enums(self) -> None:
        enum_sets = []
        for schema_path in _MANIFEST_SCHEMAS:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            enum_sets.append([set(e) for e in _pack_enums(schema)])
        self.assertEqual(
            enum_sets[0],
            enum_sets[1],
            "root and versioned manifest schemas must share the same pack enums",
        )

    def test_dogfood_manifest_valid_on_capability_pack_surface(self) -> None:
        if not _DOGFOOD_MANIFEST.exists():
            self.skipTest("dogfood manifest not present")
        schema = json.loads(_MANIFEST_SCHEMAS[0].read_text(encoding="utf-8"))
        manifest = yaml.safe_load(_DOGFOOD_MANIFEST.read_text(encoding="utf-8"))
        validator = Draft7Validator(schema)
        pack_errors = [
            e
            for e in validator.iter_errors(manifest)
            if any(
                str(p).startswith("capability_pack")
                for p in ([e.absolute_path[0]] if e.absolute_path else [])
            )
        ]
        self.assertEqual(
            pack_errors,
            [],
            f"dogfood manifest has capability-pack schema violations: "
            f"{[e.message for e in pack_errors]}",
        )


if __name__ == "__main__":
    unittest.main()
