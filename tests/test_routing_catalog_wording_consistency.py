"""Wording consistency pins for the 208-F/215-S registry-unavailable token and migration notes."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from autoharness import schema_contracts

_ROOT = Path(__file__).resolve().parents[1]
_ROUTE_DESCRIPTION = "Name of a route declared under model_routing.routes, or a bare tier tier1-tier3"


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _read(rel: str) -> str:
    return _flat((_ROOT / rel).read_text(encoding="utf-8"))


class RegistryUnavailableTokenTests(unittest.TestCase):
    def test_tuning_guide_documents_the_token_fail_closed(self) -> None:
        text = _read("docs/tuning-guide.md")
        self.assertIn("`ROUTING_SITE_REGISTRY_UNAVAILABLE`", text)
        self.assertIn(
            "non-empty `bindings` are declared and the site registry cannot be built, "
            "`ROUTING_SITE_REGISTRY_UNAVAILABLE` (fail-closed)",
            text,
        )

    def test_catalog_row_does_not_claim_errors_are_skipped(self) -> None:
        self.assertNotIn("nothing to check while both blocks are empty", _read("docs/tuning-guide.md"))

    def test_changelog_documents_the_token(self) -> None:
        self.assertIn("`ROUTING_SITE_REGISTRY_UNAVAILABLE`", _read("CHANGELOG.md"))

    def test_tuning_guide_notes_pipeline_site_keys_are_schema_rejected_at_1_2_0(self) -> None:
        text = _read("docs/tuning-guide.md")
        self.assertRegex(
            text,
            r"At `1\.2\.0` the config schema also rejects pipeline-site binding keys[^.]*`ROUTING_BINDING_ON_PIPELINE_SITE`[^.]*secondary error",
        )


class MigrationAndSchemaWordingTests(unittest.TestCase):
    def test_upgrade_summary_is_not_purely_additive(self) -> None:
        summaries = [
            entry["summary"]
            for contract in schema_contracts.CONTRACT_MIGRATIONS.values()
            for entry in contract
            if entry.get("proposal_id") == "upgrade-config-contract-1.1.0-to-1.2.0"
        ]
        self.assertEqual(len(summaries), 1)
        self.assertNotIn("(additive:", summaries[0])
        self.assertIn("model_routing is now closed", summaries[0])
        self.assertIn("routes and bindings", summaries[0])

    def test_binding_route_description_names_catalog_or_bare_tier(self) -> None:
        for rel in ("schemas/harness-config.schema.json", "schemas/harness-config/1.2.0.schema.json"):
            with self.subTest(schema=rel):
                schema = json.loads((_ROOT / rel).read_text(encoding="utf-8"))
                route = schema["properties"]["model_routing"]["properties"]["bindings"]["patternProperties"]
                (binding,) = route.values()
                self.assertEqual(binding["properties"]["route"]["description"], _ROUTE_DESCRIPTION)


if __name__ == "__main__":
    unittest.main()
