"""Tests for the lifecycle_hooks config block + typed loader (T2)."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from autoharness.gates.config import GatesConfig, GatesConfigError, load_gates_config
from autoharness.schema_contracts import (
    load_lifecycle_hooks_config,
    resolve_validation_gates_schema_path,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "validation-gates" / "1.0.0.schema.json"
_CONFIG_TEMPLATE = _REPO_ROOT / "templates" / "harness-config.yaml.tmpl"

PRESENT_CONFIG = """
schema_version: "1.0.0"
lifecycle_hooks:
  pre_execution:
    - name: "estimate_complexity"
      condition: "task.size == null"
      action: "internal:estimate_tshirt_size"
      write_back: "backlogit update {task_id} --size {result}"
  pre_task_completion:
    enforcement: "advisory"
    on_repeated_failure: "escalate"
    max_gate_failures: 5
    validation_gates:
      - pattern: "docs/**/*.md"
        command: "engram verify {file_path}"
        timeout_seconds: 15
      - pattern: "src/**/*.py"
        command: "pytest tests/ --lf"
        timeout_seconds: 60
telemetry:
  mode: "sqlite"
  database_path: ".autoharness/metrics/execution_epochs.db"
  emit_jsonl: true
"""

ABSENT_CONFIG = """
schema_version: "1.0.0"
preset: standard
"""


class LifecycleHooksLoaderTests(unittest.TestCase):
    def test_absent_block_yields_disabled_config_no_behavior_change(self) -> None:
        data = yaml.safe_load(ABSENT_CONFIG)
        config = load_gates_config(data, schema_path=_SCHEMA_PATH)
        self.assertIsInstance(config, GatesConfig)
        self.assertFalse(config.enabled)
        self.assertEqual(config.validation_gates, ())
        # Non-dict / None inputs also fail-open to disabled.
        self.assertFalse(load_gates_config(None, schema_path=_SCHEMA_PATH).enabled)

    def test_telemetry_only_config_is_retained(self) -> None:
        # A telemetry-only block (no lifecycle_hooks) keeps gates disabled but
        # must NOT discard the telemetry configuration.
        data = {
            "schema_version": "1.0.0",
            "telemetry": {"mode": "sqlite", "emit_jsonl": True},
        }
        config = load_gates_config(data, schema_path=_SCHEMA_PATH)
        self.assertFalse(config.enabled)
        self.assertEqual(config.validation_gates, ())
        self.assertEqual(config.telemetry.get("mode"), "sqlite")
        self.assertTrue(config.telemetry.get("emit_jsonl"))

    def test_emptied_blocks_are_killswitch_disabled(self) -> None:
        # The documented kill-switch: removing OR emptying the block disables
        # gating. In YAML an emptied key parses as null (or an empty mapping).
        for raw in ('lifecycle_hooks:\n', 'lifecycle_hooks: {}\n'):
            data = yaml.safe_load('schema_version: "1.0.0"\n' + raw)
            config = load_gates_config(data, schema_path=_SCHEMA_PATH)
            self.assertFalse(config.enabled)
            self.assertEqual(config.validation_gates, ())

    def test_null_telemetry_is_treated_as_absent(self) -> None:
        data = yaml.safe_load('schema_version: "1.0.0"\ntelemetry:\n')
        config = load_gates_config(data, schema_path=_SCHEMA_PATH)
        self.assertFalse(config.enabled)

    def test_lifecycle_hooks_without_gates_is_disabled(self) -> None:
        # A lifecycle_hooks block with a policy but no validation_gates has no
        # gates to run, so enabled must be False (matches the docstring).
        data = {
            "schema_version": "1.0.0",
            "lifecycle_hooks": {"pre_task_completion": {"enforcement": "absolute"}},
        }
        config = load_gates_config(data, schema_path=_SCHEMA_PATH)
        self.assertFalse(config.enabled)
        self.assertEqual(config.validation_gates, ())

    def test_present_block_parses_into_typed_structure(self) -> None:
        data = yaml.safe_load(PRESENT_CONFIG)
        config = load_gates_config(data, schema_path=_SCHEMA_PATH)
        self.assertTrue(config.enabled)
        self.assertEqual(len(config.validation_gates), 2)
        first = config.validation_gates[0]
        self.assertEqual(first.pattern, "docs/**/*.md")
        self.assertEqual(first.command, "engram verify {file_path}")
        self.assertEqual(first.timeout_seconds, 15)
        self.assertEqual(config.policy.enforcement, "advisory")
        self.assertEqual(config.policy.on_repeated_failure, "escalate")
        self.assertEqual(config.policy.max_gate_failures, 5)
        self.assertEqual(len(config.lifecycle_hooks.pre_execution), 1)
        self.assertEqual(config.lifecycle_hooks.pre_execution[0].name, "estimate_complexity")

    def test_present_but_invalid_block_raises(self) -> None:
        data = yaml.safe_load(PRESENT_CONFIG)
        data["lifecycle_hooks"]["pre_task_completion"]["enforcement"] = "sometimes"
        with self.assertRaises(GatesConfigError):
            load_gates_config(data, schema_path=_SCHEMA_PATH)

    def test_resolution_path_via_schema_contracts(self) -> None:
        schema_path = resolve_validation_gates_schema_path(_REPO_ROOT)
        self.assertIsNotNone(schema_path)
        self.assertTrue(schema_path.exists())
        present = load_lifecycle_hooks_config(yaml.safe_load(PRESENT_CONFIG), _REPO_ROOT)
        self.assertTrue(present.enabled)
        absent = load_lifecycle_hooks_config(yaml.safe_load(ABSENT_CONFIG), _REPO_ROOT)
        self.assertFalse(absent.enabled)

    def test_config_ships_as_template_artifact(self) -> None:
        text = _CONFIG_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("lifecycle_hooks:", text)
        self.assertIn("telemetry:", text)
        self.assertIn("validation_gates:", text)


if __name__ == "__main__":
    unittest.main()
