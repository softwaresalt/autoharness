"""Tests for the TelemetryConfig typed loader (U2, task 051.003/051.006)."""

from __future__ import annotations

import unittest
from pathlib import Path

from autoharness.telemetry.config import (
    DEFAULT_DATABASE_PATH,
    TelemetryConfig,
    TelemetryConfigError,
    load_telemetry_config,
)


class TelemetryConfigLoaderTests(unittest.TestCase):
    def test_absent_block_yields_disabled_config(self) -> None:
        for absent in (None, {}, "not-a-mapping", []):
            config = load_telemetry_config(absent)
            self.assertIsInstance(config, TelemetryConfig)
            self.assertFalse(config.enabled)
            self.assertEqual(config.mode, "none")
            self.assertIsNone(config.database_path)
            self.assertFalse(config.emit_jsonl)

    def test_mode_none_is_disabled_noop(self) -> None:
        config = load_telemetry_config({"mode": "none", "emit_jsonl": True})
        self.assertFalse(config.enabled)
        self.assertEqual(config.mode, "none")

    def test_sqlite_mode_parses_into_typed_structure(self) -> None:
        config = load_telemetry_config(
            {
                "mode": "sqlite",
                "database_path": ".autoharness/metrics/execution_epochs.db",
                "emit_jsonl": True,
            },
            workspace_root="/tmp/does-not-need-to-exist-ws",
        )
        self.assertTrue(config.enabled)
        self.assertEqual(config.mode, "sqlite")
        self.assertTrue(config.emit_jsonl)
        self.assertIsNotNone(config.database_path)
        self.assertIsNotNone(config.jsonl_path)
        self.assertEqual(config.database_path.name, "execution_epochs.db")
        self.assertEqual(config.jsonl_path.name, "execution_epochs.jsonl")

    def test_database_path_resolves_repo_relative_under_workspace_root(self) -> None:
        root = Path.cwd()
        config = load_telemetry_config({"mode": "sqlite"}, workspace_root=root)
        # Default repo-relative path resolves under the workspace root.
        self.assertTrue(config.database_path.is_absolute())
        self.assertEqual(
            config.database_path,
            (root / DEFAULT_DATABASE_PATH).resolve(),
        )
        self.assertEqual(config.database_path.parent, config.jsonl_path.parent)

    def test_absolute_database_path_is_preserved(self) -> None:
        abs_path = Path.cwd().resolve() / "custom" / "epochs.db"
        config = load_telemetry_config(
            {"mode": "sqlite", "database_path": str(abs_path)},
            workspace_root="/some/other/root",
        )
        self.assertEqual(config.database_path, abs_path)

    def test_unsupported_mode_raises(self) -> None:
        with self.assertRaises(TelemetryConfigError):
            load_telemetry_config({"mode": "postgres"})


if __name__ == "__main__":
    unittest.main()
