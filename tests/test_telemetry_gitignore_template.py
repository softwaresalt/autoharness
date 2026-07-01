"""Tests for runtime-artifact gitignore + config template activation (U6)."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft7Validator

from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
)
from autoharness.telemetry.jsonl_sink import append_epoch
from autoharness.telemetry.sqlite_sink import write_epoch

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


class MetricsEmissionHardGateTests(unittest.TestCase):
    """End-to-end: real emission under a real git repo must leave the tree clean."""

    def _epoch(self, task_id: str) -> ExecutionEpoch:
        return ExecutionEpoch(
            task_id=task_id,
            route=RouteConfiguration(models=("gpt-5.4",)),
            economics=EconomicPayload(input_tokens=10, output_tokens=5),
            operations=OperationalReality(cli_tools=("git",)),
            outcome=AbsoluteOutcome(gate_exit_codes=(0,)),
        )

    def _git(self, repo: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, check=True
        )

    def test_emitted_metrics_artifacts_are_never_tracked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._git(repo, "init")
            self._git(repo, "config", "user.email", "t@example.com")
            self._git(repo, "config", "user.name", "t")

            # Copy the repo's real ignore rule for the metrics directory.
            metrics_rule = next(
                line
                for line in _GITIGNORE.read_text(encoding="utf-8").splitlines()
                if line.strip() == ".autoharness/metrics/"
            )
            (repo / ".gitignore").write_text(metrics_rule + "\n", encoding="utf-8")
            # Commit .gitignore so a fully-clean `git status` directly proves the
            # emitted metrics artifacts are ignored (nothing shows at all).
            self._git(repo, "add", ".gitignore")
            self._git(repo, "commit", "-m", "add gitignore")

            metrics = repo / ".autoharness" / "metrics"
            db_path = metrics / "execution_epochs.db"
            jsonl_path = metrics / "execution_epochs.jsonl"

            # Emit a real epoch through both sinks.
            write_epoch(self._epoch("gate-T"), db_path)
            append_epoch(self._epoch("gate-T"), jsonl_path)

            self.assertTrue(db_path.exists())
            self.assertTrue(jsonl_path.exists())

            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            offending = [
                line
                for line in status.stdout.splitlines()
                if ".autoharness/metrics/" in line.replace("\\", "/")
            ]
            self.assertEqual(
                offending,
                [],
                f"metrics artifacts leaked into git status: {offending!r}",
            )
            # With .gitignore committed, emission must leave the tree fully clean.
            self.assertEqual(
                status.stdout.strip(),
                "",
                f"emission dirtied the working tree; git status:\n{status.stdout}",
            )


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
