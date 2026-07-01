"""Tests for runtime-artifact gitignore + config template activation (U6)."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft7Validator

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GITIGNORE = _REPO_ROOT / ".gitignore"
_CONFIG_TEMPLATE = _REPO_ROOT / "templates" / "harness-config.yaml.tmpl"
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "validation-gates" / "1.0.0.schema.json"


class MetricsGitignoreTests(unittest.TestCase):
    def test_metrics_dir_is_listed_in_gitignore(self) -> None:
        self.assertIn(".autoharness/metrics/", _GITIGNORE.read_text(encoding="utf-8"))

    def test_git_check_ignore_matches_metrics_artifacts(self) -> None:
        # Emission never dirties the tree — the DB, its WAL/SHM sidecars, and the
        # JSONL stream are all ignored under the metrics directory.
        for rel in (
            ".autoharness/metrics/execution_epochs.db",
            ".autoharness/metrics/execution_epochs.db-wal",
            ".autoharness/metrics/execution_epochs.db-shm",
            ".autoharness/metrics/execution_epochs.jsonl",
        ):
            result = subprocess.run(
                ["git", "check-ignore", rel],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, f"{rel} is not gitignored")


class TelemetryTemplateActivationTests(unittest.TestCase):
    def test_template_documents_activation_path(self) -> None:
        text = _CONFIG_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("telemetry:", text)
        self.assertIn('mode: "sqlite"', text)
        self.assertIn("emit_jsonl: true", text)
        self.assertIn("execution_epochs.db", text)

    def test_telemetry_block_has_no_unresolved_template_vars(self) -> None:
        text = _CONFIG_TEMPLATE.read_text(encoding="utf-8")
        telemetry_section = text[text.index("# telemetry:"):]
        self.assertNotIn("{{", telemetry_section)

    def test_activated_telemetry_block_validates_against_schema(self) -> None:
        schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = Draft7Validator(schema)
        activated = {
            "telemetry": {
                "mode": "sqlite",
                "database_path": ".autoharness/metrics/execution_epochs.db",
                "emit_jsonl": True,
            }
        }
        self.assertEqual(list(validator.iter_errors(activated)), [])


if __name__ == "__main__":
    unittest.main()
