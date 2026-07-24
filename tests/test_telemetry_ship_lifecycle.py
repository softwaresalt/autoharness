"""Ship lifecycle telemetry handoff contract tests (079.015-T)."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import sqlite3
import unittest
from pathlib import Path
from unittest import mock

import yaml

from autoharness.cli import main
from autoharness.telemetry.epoch import WorkSizingSnapshot

_ROOT = Path(__file__).resolve().parents[1]
_TEST_OUTPUT = _ROOT / ".test-output" / "telemetry-ship-lifecycle"


class ShipTelemetryLifecycleTests(unittest.TestCase):
    def test_ship_template_and_dogfood_mirror_wire_begin_before_build_and_record_at_close(self) -> None:
        template = (_ROOT / "templates" / "agents" / ".ship.agent.md.tmpl").read_text(encoding="utf-8")
        mirror = (_ROOT / ".github" / "agents" / ".ship.agent.md").read_text(encoding="utf-8")

        for content in (template, mirror):
            begin_pos = content.index("autoharness telemetry begin")
            build_marker = "#### Step 4.2" if "#### Step 4.2" in content else "Pre-build knowledge retrieval"
            build_pos = content.index(build_marker)
            record_pos = content.index("autoharness telemetry record --context-ref")
            done_pos = content.index("Move the task to done") if "Move the task to done" in content else content.index("Update task status to")
            self.assertLess(begin_pos, build_pos)
            self.assertLess(record_pos, done_pos)
            self.assertIn("--capture-backlogit-sizing", content)
            self.assertIn("context_ref", content)
            self.assertIn("stable epoch_id", content)
            self.assertIn("skip context carry/record close", content)

    def test_manifest_tracks_dogfood_ship_agent_checksum(self) -> None:
        manifest = yaml.safe_load((_ROOT / ".autoharness" / "harness-manifest.yaml").read_text(encoding="utf-8"))
        artifact = next(
            item for item in manifest["artifacts"] if item.get("path") == ".github/agents/.ship.agent.md"
        )
        digest = hashlib.sha256((_ROOT / ".github" / "agents" / ".ship.agent.md").read_bytes()).hexdigest()

        self.assertEqual(artifact["checksum"], digest)

    def test_ship_lifecycle_begin_carry_record_persists_frozen_sizing_to_both_sinks(self) -> None:
        workspace = _TEST_OUTPUT / self._testMethodName / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
        (workspace / ".autoharness" / "config.yaml").write_text(
            'telemetry:\n  mode: "sqlite"\n  emit_jsonl: true\n',
            encoding="utf-8",
        )
        snapshot = WorkSizingSnapshot(
            snapshot_at="2026-07-24T04:06:55Z",
            task_size_label="S",
            feature_planned_child_task_count=2,
            feature_planned_child_size_histogram={"S": 1, "unsized": 1},
            feature_child_membership_hash=WorkSizingSnapshot.membership_hash(["fresh-a", "fresh-b"]),
        )
        mutated_snapshot = WorkSizingSnapshot(
            snapshot_at="2026-07-24T04:07:55Z",
            task_size_label="XL",
            feature_planned_child_task_count=1,
            feature_planned_child_size_histogram={"XL": 1},
            feature_child_membership_hash=WorkSizingSnapshot.membership_hash(["mutated"]),
        )
        payload_path = workspace / "close.json"
        payload_path.write_text(
            json.dumps(
                {
                    "task_id": "079.015-T",
                    "route": {"models": ["gpt-5.4-mini"]},
                    "economics": {"input_tokens": 10, "output_tokens": 5},
                    "operations": {"cli_tools": ["unittest"]},
                    "outcome": {"gate_exit_codes": [0]},
                }
            ),
            encoding="utf-8",
        )

        try:
            with mock.patch(
                "autoharness.telemetry.sizing.capture_work_sizing_snapshot",
                return_value=snapshot,
            ) as capture:
                begin_out = io.StringIO()
                with contextlib.redirect_stdout(begin_out):
                    main(
                        [
                            "telemetry",
                            "begin",
                            "--workspace",
                            str(workspace),
                            "--task-id",
                            "079.015-T",
                            "--feature-id",
                            "079-F",
                            "--shipment-id",
                            "092-S",
                            "--capture-backlogit-sizing",
                            "--epoch-id",
                            "12121212-1212-4212-8212-121212121212",
                            "--json",
                        ]
                    )
                capture.return_value = mutated_snapshot

            begin = json.loads(begin_out.getvalue())
            record_out = io.StringIO()
            with contextlib.redirect_stdout(record_out):
                main(
                    [
                        "telemetry",
                        "record",
                        "--workspace",
                        str(workspace),
                        "--from-json",
                        str(payload_path),
                        "--context-ref",
                        begin["context_ref"],
                        "--json",
                    ]
                )
            record = json.loads(record_out.getvalue())

            self.assertEqual(record["epoch_id"], begin["epoch_id"])
            self.assertEqual(record["idempotency_outcome"], "created")
            db_path = workspace / ".autoharness" / "metrics" / "execution_epochs.db"
            jsonl_path = workspace / ".autoharness" / "metrics" / "execution_epochs.jsonl"
            conn = sqlite3.connect(str(db_path))
            try:
                sqlite_payload = json.loads(
                    conn.execute("SELECT payload_json FROM execution_epochs WHERE epoch_id=?", (begin["epoch_id"],)).fetchone()[0]
                )
            finally:
                conn.close()
            jsonl_payload = json.loads(jsonl_path.read_text(encoding="utf-8").splitlines()[0])

            for persisted in (sqlite_payload, jsonl_payload):
                self.assertEqual(persisted["epoch_id"], begin["epoch_id"])
                self.assertEqual(persisted["sizing"]["task_size_label"], "S")
                self.assertEqual(persisted["sizing"]["feature_child_membership_hash"], snapshot.feature_child_membership_hash)
                self.assertNotEqual(persisted["sizing"]["feature_child_membership_hash"], mutated_snapshot.feature_child_membership_hash)
        finally:
            shutil.rmtree(_TEST_OUTPUT / self._testMethodName, ignore_errors=True)

    def test_092s_execution_ready_guardrails_are_documented_in_ship_agents(self) -> None:
        template = (_ROOT / "templates" / "agents" / ".ship.agent.md.tmpl").read_text(encoding="utf-8")
        mirror = (_ROOT / ".github" / "agents" / ".ship.agent.md").read_text(encoding="utf-8")

        for content in (template, mirror):
            self.assertIn("task-only manifests", content)
            self.assertIn("parent_id", content)
            self.assertIn("079.013-T", content)
            self.assertIn("079.015-T", content)
            self.assertIn("execution-ready", content)


if __name__ == "__main__":
    unittest.main()
