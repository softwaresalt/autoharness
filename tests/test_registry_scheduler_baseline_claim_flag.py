"""Contract tests for the `features.scheduler_baseline_claim` registry flag (P-002.8 opt-in)."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import jsonschema
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "backlog-tool-registry.schema.json"
_REGISTRY_FILES = (
    _REPO_ROOT / "templates" / "backlog" / "registries" / "backlogit.registry.yaml",
    _REPO_ROOT / ".autoharness" / "backlog-registry.yaml",
)


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _minimal_registry(features: dict) -> dict:
    data = yaml.safe_load(_REGISTRY_FILES[0].read_text(encoding="utf-8"))
    data["features"] = features
    return data

class SchedulerBaselineClaimFlagSchemaTests(unittest.TestCase):
    def test_flag_true_validates(self) -> None:
        registry = _minimal_registry({"scheduler_baseline_claim": True})
        jsonschema.Draft7Validator(_schema()).validate(registry)

    def test_flag_non_boolean_fails(self) -> None:
        registry = _minimal_registry({"scheduler_baseline_claim": "yes"})
        errors = list(jsonschema.Draft7Validator(_schema()).iter_errors(registry))
        self.assertTrue(
            any(list(e.absolute_path)[-1:] == ["scheduler_baseline_claim"] for e in errors),
            errors,
        )

    def test_flag_is_not_required(self) -> None:
        schema = copy.deepcopy(_schema())
        features = schema["properties"]["features"]
        self.assertIn("scheduler_baseline_claim", features["properties"])
        self.assertIs(features["properties"]["scheduler_baseline_claim"]["default"], False)
        self.assertNotIn("scheduler_baseline_claim", features.get("required", []))
        self.assertNotIn("scheduler_baseline_claim", schema.get("required", []))
        registry = _minimal_registry({})
        jsonschema.Draft7Validator(schema).validate(registry)


if __name__ == "__main__":
    unittest.main()
