"""Tests for the validation_gates JSON Schema (lifecycle_hooks + telemetry)."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "validation-gates" / "1.1.0.schema.json"
_POINTER_PATH = _REPO_ROOT / "schemas" / "validation-gates.schema.json"
_LEGACY_SCHEMA_PATH = _REPO_ROOT / "schemas" / "validation-gates" / "1.0.0.schema.json"


def _load_validator() -> Draft7Validator:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


# The design-doc §5 configuration contract, verbatim (markdown escaping removed).
DESIGN_DOC_SECTION5 = """
lifecycle_hooks:
  pre_execution:
    - name: "estimate_complexity"
      condition: "task.size == null"
      action: "internal:estimate_tshirt_size"
      write_back: "backlogit update {task_id} --size {result}"

  pre_task_completion:
    validation_gates:
      - pattern: "docs/**/*.md"
        command: "engram verify {file_path}"
        timeout_seconds: 15

      - pattern: ".backlogit/queue/*.md"
        command: "backlogit doctor --target {file_path}"
        timeout_seconds: 5

      - pattern: "src/**/*.py"
        command: "pytest tests/ --lf"
        timeout_seconds: 60

telemetry:
  mode: "sqlite"
  database_path: ".autoharness/metrics/execution_epochs.db"
  emit_jsonl: true
"""

DETECTOR_CONFIG = {
    "detectors": [
        {
            "node_id": "det:D-ART/ART-01@1",
            "applies_when": {"changed_paths_any": [".backlogit/**"]},
            "producer": {
                "kind": "pure",
                "ref": "autoharness.detectors.art.section_markers:produce",
                "tool_version_dims": ["python"],
            },
            "validator": {
                "ref": "autoharness.detectors.art.section_markers:validate",
                "consumes": ["det:D-ART/ART-01@1#evidence"],
            },
            "depends_on": [],
            "severity": "medium",
            "mode": "report_only",
            "remediation": {
                "class": "guided_fix",
                "hint": "Restore required section markers.",
                "target_refs": ["path:.backlogit/templates/task.md"],
                "authority": "stage",
            },
        }
    ]
}


class ValidationGatesSchemaTests(unittest.TestCase):
    def test_schema_validates_design_doc_section5_example_verbatim(self) -> None:
        validator = _load_validator()
        instance = yaml.safe_load(DESIGN_DOC_SECTION5)
        errors = sorted(validator.iter_errors(instance), key=str)
        self.assertEqual(errors, [], msg=f"unexpected schema errors: {[e.message for e in errors]}")

    def test_schema_validates_detector_block_against_versioned_schema(self) -> None:
        validator = _load_validator()
        self.assertTrue(validator.is_valid(DETECTOR_CONFIG))

    def test_schema_rejects_detector_mode_blocking(self) -> None:
        validator = _load_validator()
        instance = copy.deepcopy(DETECTOR_CONFIG)
        instance["detectors"][0]["mode"] = "blocking"
        self.assertFalse(validator.is_valid(instance))

    def test_schema_rejects_unknown_detector_key(self) -> None:
        validator = _load_validator()
        instance = copy.deepcopy(DETECTOR_CONFIG)
        instance["detectors"][0]["unexpected"] = True
        self.assertFalse(validator.is_valid(instance))

    def test_schema_rejects_malformed_detector_node_id(self) -> None:
        validator = _load_validator()
        instance = copy.deepcopy(DETECTOR_CONFIG)
        instance["detectors"][0]["node_id"] = "detector-art-01"
        self.assertFalse(validator.is_valid(instance))

    def test_schema_requires_tool_version_dims_for_ast_coverage_api_producer_kinds(self) -> None:
        # Copilot review finding (PR #420, round 8): the D3 contract requires
        # `tool_version_dims` for producer kinds `ast`/`coverage`/`api` (the
        # epoch fingerprint depends on tool versioning to detect stale
        # evidence reuse for these kinds), but the schema previously left it
        # optional for every kind and the loader accepted omission.
        validator = _load_validator()
        for kind in ("ast", "coverage", "api"):
            instance = copy.deepcopy(DETECTOR_CONFIG)
            instance["detectors"][0]["producer"]["kind"] = kind
            del instance["detectors"][0]["producer"]["tool_version_dims"]
            with self.subTest(kind=kind):
                self.assertFalse(validator.is_valid(instance))
            instance["detectors"][0]["producer"]["tool_version_dims"] = ["python"]
            with self.subTest(kind=kind, with_dims=True):
                self.assertTrue(validator.is_valid(instance))

    def test_schema_allows_missing_tool_version_dims_for_pure_and_command_producer_kinds(self) -> None:
        validator = _load_validator()
        for kind in ("pure", "command"):
            instance = copy.deepcopy(DETECTOR_CONFIG)
            instance["detectors"][0]["producer"]["kind"] = kind
            del instance["detectors"][0]["producer"]["tool_version_dims"]
            with self.subTest(kind=kind):
                self.assertTrue(validator.is_valid(instance))

    def test_schema_rejects_unknown_placeholder(self) -> None:
        validator = _load_validator()
        instance = {
            "lifecycle_hooks": {
                "pre_task_completion": {
                    "validation_gates": [
                        {
                            "pattern": "docs/**/*.md",
                            "command": "engram verify {unknown_var}",
                            "timeout_seconds": 15,
                        }
                    ]
                }
            }
        }
        self.assertFalse(validator.is_valid(instance))

    def test_schema_rejects_bad_enforcement_enum(self) -> None:
        validator = _load_validator()
        instance = {
            "lifecycle_hooks": {
                "pre_task_completion": {
                    "enforcement": "sometimes",
                    "validation_gates": [],
                }
            }
        }
        self.assertFalse(validator.is_valid(instance))

    def test_entire_lifecycle_hooks_block_is_optional(self) -> None:
        validator = _load_validator()
        # An empty document and a telemetry-only document must both validate.
        self.assertTrue(validator.is_valid({}))
        self.assertTrue(validator.is_valid({"telemetry": {"mode": "none"}}))
        self.assertTrue(validator.is_valid({"detectors": []}))
        # Emptied (null) blocks are the kill-switch and must validate too.
        self.assertTrue(validator.is_valid({"lifecycle_hooks": None}))
        self.assertTrue(validator.is_valid({"telemetry": None}))

    def test_pointer_schema_mirrors_versioned_schema_except_id(self) -> None:
        pointer = json.loads(_POINTER_PATH.read_text(encoding="utf-8"))
        versioned = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        # Each file must carry its own $id (matching its own path) so tooling
        # that keys on $id treats them as distinct documents.
        self.assertNotEqual(pointer["$id"], versioned["$id"])
        self.assertTrue(pointer["$id"].endswith("/schemas/validation-gates.schema.json"))
        self.assertTrue(versioned["$id"].endswith("/schemas/validation-gates/1.1.0.schema.json"))
        # Apart from $id, the pointer mirrors the versioned schema verbatim.
        pointer.pop("$id", None)
        versioned.pop("$id", None)
        self.assertEqual(pointer, versioned)

    def test_legacy_1_0_0_mirror_preserved_unchanged(self) -> None:
        # Copilot review finding (PR #420, round 8): the previously published
        # `1.0.0` mirror (from 052-S) was mutated in place by this shipment's
        # own 149.002-T commit instead of being version-bumped, violating the
        # immutable-versioned-snapshot convention documented in
        # `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`.
        # The fix restores `1.0.0.schema.json` byte-identical to its
        # pre-157-S content and publishes the new `detectors` block only
        # under a new `1.1.0.schema.json` mirror. Assert the legacy mirror
        # has no knowledge of `detectors` at all -- it must remain exactly
        # what it was before this shipment touched it.
        legacy = json.loads(_LEGACY_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertTrue(legacy["$id"].endswith("/schemas/validation-gates/1.0.0.schema.json"))
        self.assertNotIn("detectors", legacy.get("properties", {}))
        self.assertNotIn("detector_node", legacy.get("definitions", {}))
        self.assertNotIn("detector_producer", legacy.get("definitions", {}))
        Draft7Validator.check_schema(legacy)
        # The legacy mirror must still validate an instance with no
        # `detectors` key (it never knew about that key) ...
        legacy_validator = Draft7Validator(legacy)
        self.assertTrue(legacy_validator.is_valid({}))
        # ... but must reject a `detectors` block since it predates that
        # extension entirely (additionalProperties: true means an unknown
        # top-level key like `detectors` is actually accepted structurally,
        # so assert instead that it has no notion of the nested detector
        # definitions used to validate its *contents*).
        self.assertNotIn("detector_producer", json.dumps(legacy))


if __name__ == "__main__":
    unittest.main()
