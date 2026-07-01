"""Tests for the validation_gates JSON Schema (lifecycle_hooks + telemetry)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "validation-gates" / "1.0.0.schema.json"
_POINTER_PATH = _REPO_ROOT / "schemas" / "validation-gates.schema.json"


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


class ValidationGatesSchemaTests(unittest.TestCase):
    def test_schema_validates_design_doc_section5_example_verbatim(self) -> None:
        validator = _load_validator()
        instance = yaml.safe_load(DESIGN_DOC_SECTION5)
        errors = sorted(validator.iter_errors(instance), key=str)
        self.assertEqual(errors, [], msg=f"unexpected schema errors: {[e.message for e in errors]}")

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
        self.assertTrue(versioned["$id"].endswith("/schemas/validation-gates/1.0.0.schema.json"))
        # Apart from $id, the pointer mirrors the versioned schema verbatim.
        pointer.pop("$id", None)
        versioned.pop("$id", None)
        self.assertEqual(pointer, versioned)


if __name__ == "__main__":
    unittest.main()
