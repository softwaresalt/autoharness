"""Tests for the pre-execution telemetry begin context artifact (079.014-T)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import unittest
import uuid
from pathlib import Path
from unittest import mock

from autoharness.cli import main
from autoharness.telemetry.config import load_telemetry_config
from autoharness.telemetry.context import (
    TelemetryContextError,
    begin_context,
    resolve_context_ref,
)
from autoharness.telemetry.epoch import WorkSizingSnapshot

_ROOT = Path(__file__).resolve().parents[1]
_TEST_OUTPUT = _ROOT / ".test-output" / "telemetry-begin-context"


class TelemetryBeginContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = _TEST_OUTPUT / self._testMethodName / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)
        (self.workspace / ".autoharness").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(_TEST_OUTPUT / self._testMethodName, ignore_errors=True)

    def _write_config(self, text: str) -> None:
        (self.workspace / ".autoharness" / "config.yaml").write_text(text, encoding="utf-8")

    def _config(self, telemetry: dict | None = None):
        return load_telemetry_config(
            telemetry
            or {
                "mode": "sqlite",
                "database_path": ".autoharness/metrics/execution_epochs.db",
                "emit_jsonl": True,
            },
            workspace_root=self.workspace,
        )

    def test_begin_accepts_and_normalizes_caller_uuid(self) -> None:
        raw_epoch_id = str(uuid.UUID("01234567-89AB-CDEF-0123-456789ABCDEF"))
        result = begin_context(
            self._config(),
            self.workspace,
            task_id="079.014-T",
            backlog_item_id="079.014-T",
            feature_id="079-F",
            shipment_id="092-S",
            epoch_id=raw_epoch_id,
            workspace_id="workspace-1",
            session_id="session-1",
            agent_role="ship",
            phase="build",
            branch="feat/079-telemetry-metrics-core",
            commit_sha="abc123",
            captured_at="2026-07-24T03:07:22Z",
        )

        self.assertEqual(result.status, "created")
        self.assertEqual(result.epoch_id, "0123456789abcdef0123456789abcdef")
        self.assertIsNotNone(result.context_ref)
        self.assertIsNotNone(result.context_path)
        self.assertTrue(result.context_path.exists())
        self.assertTrue(result.context_path.resolve().is_relative_to(self.workspace.resolve()))
        self.assertEqual(
            result.context_path.name,
            "0123456789abcdef0123456789abcdef.json",
        )

        payload = json.loads(result.context_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["context_schema_version"], "1.0.0")
        self.assertEqual(payload["epoch_id"], result.epoch_id)
        self.assertEqual(payload["task_id"], "079.014-T")
        self.assertEqual(payload["feature_id"], "079-F")
        self.assertEqual(payload["shipment_id"], "092-S")
        self.assertEqual(payload["snapshot_boundary"], "pre_execution")
        self.assertEqual(payload["context_digest"], result.context_digest)

    def test_begin_rejects_non_uuid_and_path_like_ids(self) -> None:
        for bad_id in (
            "",
            "   ",
            "not-a-uuid",
            "..",
            "..\\evil",
            "../evil",
            "C:\\evil\\id",
            "/evil/id",
            "0123456789abcdef0123456789abcdef\\x",
        ):
            with self.assertRaises(TelemetryContextError, msg=bad_id):
                begin_context(self._config(), self.workspace, task_id="079.014-T", epoch_id=bad_id)

    def test_default_and_custom_context_directories_stay_inside_workspace(self) -> None:
        default_result = begin_context(
            self._config(),
            self.workspace,
            task_id="079.014-T",
            epoch_id="11111111-1111-4111-8111-111111111111",
            captured_at="2026-07-24T03:07:22Z",
        )
        self.assertEqual(
            default_result.context_path.parent,
            (self.workspace / ".autoharness" / "metrics" / "contexts").resolve(),
        )

        custom = self._config({"mode": "sqlite", "database_path": "telemetry/custom.db"})
        custom_result = begin_context(
            custom,
            self.workspace,
            task_id="079.014-T",
            epoch_id="22222222-2222-4222-8222-222222222222",
            captured_at="2026-07-24T03:07:22Z",
        )
        self.assertEqual(custom_result.context_path.parent, (self.workspace / "telemetry" / "contexts").resolve())

        disabled_workspace = _TEST_OUTPUT / self._testMethodName / "disabled-workspace"
        disabled_workspace.mkdir(parents=True, exist_ok=True)
        outside = _TEST_OUTPUT / self._testMethodName / "outside" / "epochs.db"
        disabled = load_telemetry_config(
            {"mode": "sqlite", "database_path": str(outside)},
            workspace_root=disabled_workspace,
        )
        disabled_result = begin_context(disabled, disabled_workspace, task_id="079.014-T")
        self.assertEqual(disabled_result.status, "disabled")
        self.assertFalse((disabled_workspace / ".autoharness" / "metrics").exists())

    def test_resolve_context_ref_rejects_absolute_traversal_and_separator_ids(self) -> None:
        config = self._config()
        result = begin_context(
            config,
            self.workspace,
            task_id="079.014-T",
            epoch_id="33333333-3333-4333-8333-333333333333",
            captured_at="2026-07-24T03:07:22Z",
        )
        self.assertEqual(resolve_context_ref(config, self.workspace, result.context_ref), result.context_path)

        for bad_ref in (
            str(result.context_path),
            "..\\contexts\\33333333333343338333333333333333.json",
            ".autoharness\\metrics\\contexts\\..\\escape.json",
            ".autoharness\\metrics\\contexts\\not-a-uuid.json",
            ".autoharness\\metrics\\contexts\\33333333333343338333333333333333\\x.json",
        ):
            with self.assertRaises(TelemetryContextError, msg=bad_ref):
                resolve_context_ref(config, self.workspace, bad_ref)

    def test_begin_rejects_symlink_context_directory_escape(self) -> None:
        config = self._config()
        context_dir = self.workspace / ".autoharness" / "metrics" / "contexts"
        outside = _TEST_OUTPUT / self._testMethodName / "outside-contexts"
        outside.mkdir(parents=True, exist_ok=True)
        context_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(outside, context_dir, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink unavailable: {exc}")

        with self.assertRaises(TelemetryContextError):
            begin_context(
                config,
                self.workspace,
                task_id="079.014-T",
                epoch_id="44444444-4444-4444-8444-444444444444",
                captured_at="2026-07-24T03:07:22Z",
            )

    def test_begin_is_atomic_idempotent_and_conflict_preserving(self) -> None:
        config = self._config()
        fixed_id = "55555555-5555-4555-8555-555555555555"
        first = begin_context(
            config,
            self.workspace,
            task_id="079.014-T",
            epoch_id=fixed_id,
            captured_at="2026-07-24T03:07:22Z",
        )
        original = first.context_path.read_text(encoding="utf-8")

        second = begin_context(
            config,
            self.workspace,
            task_id="079.014-T",
            epoch_id=fixed_id,
            captured_at="2026-07-24T03:07:22Z",
        )
        self.assertEqual(second.status, "idempotent_begin")
        self.assertEqual(first.context_digest, second.context_digest)

        conflict = begin_context(
            config,
            self.workspace,
            task_id="DIFFERENT-T",
            epoch_id=fixed_id,
            captured_at="2026-07-24T03:07:22Z",
        )
        self.assertEqual(conflict.status, "conflict")
        self.assertEqual(first.context_digest, conflict.context_digest)
        self.assertEqual(first.context_path.read_text(encoding="utf-8"), original)

    def test_disabled_telemetry_begin_is_noop(self) -> None:
        result = begin_context(load_telemetry_config(None, workspace_root=self.workspace), self.workspace, task_id="079.014-T")

        self.assertEqual(result.status, "disabled")
        self.assertFalse(result.enabled)
        self.assertIsNone(result.context_ref)
        self.assertFalse((self.workspace / ".autoharness" / "metrics").exists())

    def test_context_contains_safe_metadata_and_optional_sizing_snapshot(self) -> None:
        sizing = WorkSizingSnapshot(
            snapshot_at="2026-07-24T03:07:22Z",
            task_size_label="M",
            sizing_sources={"task": "backlogit"},
            sizing_source_revisions={"task": "rev-1"},
            sizing_ruleset_versions={"task": "backlogit-1.2.3"},
        )
        result = begin_context(
            self._config(),
            self.workspace,
            task_id="079.014-T",
            epoch_id="66666666-6666-4666-8666-666666666666",
            sizing=sizing,
            source_metadata={"task": "backlogit"},
            ruleset_metadata={"task": "backlogit-1.2.3"},
            version_metadata={"autoharness": "1.4.11"},
            captured_at="2026-07-24T03:07:22Z",
        )
        payload = json.loads(result.context_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["sizing"]["task_size_label"], "M")
        self.assertEqual(payload["source_metadata"], {"task": "backlogit"})
        self.assertEqual(payload["ruleset_metadata"], {"task": "backlogit-1.2.3"})
        self.assertEqual(payload["version_metadata"], {"autoharness": "1.4.11"})
        forbidden = {
            "raw_tool_output",
            "prompt",
            "prompt_body",
            "stderr",
            "stderr_body",
            "credentials",
            "secret",
            "argv",
            "unredacted_argv",
        }
        self.assertTrue(forbidden.isdisjoint(payload))

    def test_cli_begin_emits_json_result_and_writes_context(self) -> None:
        self._write_config(
            'schema_version: "1.0.0"\n'
            "telemetry:\n"
            '  mode: "sqlite"\n'
            '  database_path: ".autoharness/metrics/execution_epochs.db"\n'
        )
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            main(
                [
                    "telemetry",
                    "begin",
                    "--workspace",
                    str(self.workspace),
                    "--task-id",
                    "079.014-T",
                    "--epoch-id",
                    "77777777-7777-4777-8777-777777777777",
                    "--feature-id",
                    "079-F",
                    "--json",
                ]
            )

        result = json.loads(stdout.getvalue())
        self.assertEqual(result["status"], "created")
        self.assertEqual(result["epoch_id"], "77777777777747778777777777777777")
        self.assertTrue((self.workspace / result["context_ref"]).exists())

    def test_begin_does_not_recurse_on_malformed_existing_context(self) -> None:
        """Copilot review r3 (context.py:251): when the target context file exists
        but is malformed/partial, _read_context returns None and the exclusive
        open raises FileExistsError. The old code recursed indefinitely to
        RecursionError. It must instead return a controlled conflict."""
        config = self._config()
        epoch_id = "88888888-8888-4888-8888-888888888888"
        first = begin_context(
            config, self.workspace, task_id="079.014-T", epoch_id=epoch_id,
            captured_at="2026-07-24T03:07:22Z",
        )
        first.context_path.write_text("{ not valid json", encoding="utf-8")

        result = begin_context(
            config, self.workspace, task_id="079.014-T", epoch_id=epoch_id,
            captured_at="2026-07-24T03:07:22Z",
        )

        self.assertEqual(result.status, "conflict")
        self.assertTrue(result.enabled)

    def test_begin_is_fail_open_on_filesystem_write_error(self) -> None:
        """Copilot review r3 (context.py:249): a filesystem failure (read-only
        workspace, permission denial, disk full) raises a raw OSError. The CLI
        catches only TelemetryContextError, so an unhandled OSError would halt the
        Ship task, violating the fail-open contract. begin_context must degrade to
        an unavailable begin instead."""
        config = self._config()
        with mock.patch(
            "autoharness.telemetry.context.Path.open",
            side_effect=PermissionError("read-only workspace"),
        ):
            result = begin_context(
                config, self.workspace, task_id="079.014-T",
                epoch_id="99999999-9999-4999-8999-999999999999",
                captured_at="2026-07-24T03:07:22Z",
            )

        self.assertFalse(result.enabled)
        self.assertEqual(result.status, "unavailable")
        self.assertTrue(result.errors)


if __name__ == "__main__":
    unittest.main()
