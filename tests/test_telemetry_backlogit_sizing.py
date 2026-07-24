"""Backlogit hierarchical sizing snapshot adapter tests (079.013-T)."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from autoharness.cli import main
from autoharness.telemetry.config import load_telemetry_config
from autoharness.telemetry.context import begin_context
from autoharness.telemetry.epoch import WorkSizingSnapshot
from autoharness.telemetry.sizing import _default_runner, capture_work_sizing_snapshot

_ROOT = Path(__file__).resolve().parents[1]
_TEST_OUTPUT = _ROOT / ".test-output" / "telemetry-backlogit-sizing"


class FakeBacklogitRunner:
    def __init__(
        self,
        responses: dict[str, dict],
        *,
        sync_updates: dict[str, dict] | None = None,
        sync_raises: bool = False,
    ):
        self.responses = responses
        self.sync_updates = sync_updates or {}
        self.sync_raises = sync_raises
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv: tuple[str, ...], cwd: Path) -> str:
        self.calls.append(tuple(argv))
        if argv[0] == "sync":
            if self.sync_raises:
                raise RuntimeError("sync failed")
            self.responses.update(self.sync_updates)
            return "synced"
        if argv[:2] == ("get", argv[1]) and "--format" in argv:
            item_id = argv[1]
            if item_id not in self.responses:
                raise RuntimeError(f"missing {item_id}")
            return json.dumps(self.responses[item_id])
        raise RuntimeError(f"unexpected command: {argv}")


def _task(item_id: str, size: str | None = None) -> dict:
    custom_fields = {}
    if size is not None:
        custom_fields["size"] = size
    return {
        "id": item_id,
        "artifact_type": "task",
        "custom_fields": custom_fields,
        "updated_at": "task-rev",
    }


def _rollup(item_id: str, members, histogram=None, unsized=0, skipped=None) -> dict:
    return {
        "id": item_id,
        "artifact_type": "feature" if item_id.endswith("-F") else "shipment",
        "updated_at": f"{item_id}-rev",
        "size_composition": {
            "histogram": histogram or {},
            "unsized": unsized,
            "members": members,
            "skipped": skipped or [],
            "ruleset_version": None,
        },
    }


class BacklogitSizingSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = _TEST_OUTPUT / self._testMethodName / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(_TEST_OUTPUT / self._testMethodName, ignore_errors=True)

    def test_snapshot_task_size_and_null_by_contract_parent_labels(self) -> None:
        runner = FakeBacklogitRunner(
            {
                "079.013-T": _task("079.013-T", "M"),
                "079-F": _rollup(
                    "079-F",
                    [{"id": "079.001-T", "artifact_type": "task"}, {"id": "079.002-T", "artifact_type": "task"}],
                    histogram={"M": 1},
                    unsized=1,
                ),
                "092-S": _rollup(
                    "092-S",
                    [{"id": "079.001-T", "artifact_type": "task"}, {"id": "079.001-T", "artifact_type": "task"}, {"id": "079.003-T", "artifact_type": "task"}],
                    histogram={"S": 1},
                    unsized=1,
                    skipped=[{"id": "missing", "reason": "unresolved"}],
                ),
            }
        )

        snapshot = capture_work_sizing_snapshot(
            workspace=self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            shipment_id="092-S",
            runner=runner,
            snapshot_at="2026-07-24T03:37:49Z",
        )

        self.assertEqual(snapshot.task_size_label, "M")
        self.assertIsNone(snapshot.feature_planned_size_label)
        self.assertIsNone(snapshot.shipment_planned_size_label)
        self.assertEqual(snapshot.snapshot_boundary, "pre_execution")
        self.assertEqual(snapshot.sizing_sources["task"], "backlogit")
        self.assertEqual(snapshot.sizing_source_revisions["task"], "task-rev")
        self.assertEqual(snapshot.feature_planned_child_task_count, 2)
        self.assertEqual(snapshot.feature_planned_child_size_histogram, {"M": 1, "unsized": 1})
        self.assertEqual(
            snapshot.feature_child_membership_hash,
            WorkSizingSnapshot.membership_hash(["079.001-T", "079.002-T"]),
        )
        self.assertEqual(snapshot.shipment_manifest_task_count, 2)
        self.assertEqual(snapshot.shipment_manifest_size_histogram, {"S": 1, "unsized": 1})
        self.assertEqual(
            snapshot.shipment_membership_hash,
            WorkSizingSnapshot.membership_hash(["079.001-T", "079.003-T"]),
        )
        self.assertNotIn("unavailable", snapshot.shipment_manifest_size_histogram)
        self.assertFalse(any("point" in key for key in snapshot.to_dict()))

    def test_sync_runs_immediately_before_composition_read_and_refreshes_stale_membership(self) -> None:
        runner = FakeBacklogitRunner(
            {
                "079.013-T": _task("079.013-T", "S"),
                "079-F": _rollup("079-F", [{"id": "stale", "artifact_type": "task"}], unsized=1),
            },
            sync_updates={
                "079-F": _rollup(
                    "079-F",
                    [{"id": "fresh-a", "artifact_type": "task"}, {"id": "fresh-b", "artifact_type": "task"}],
                    histogram={"S": 1},
                    unsized=1,
                )
            },
        )

        snapshot = capture_work_sizing_snapshot(
            workspace=self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            runner=runner,
            snapshot_at="2026-07-24T03:37:49Z",
        )

        self.assertEqual(runner.calls[0], ("sync",))
        self.assertEqual(runner.calls[1][:2], ("get", "079.013-T"))
        self.assertEqual(snapshot.feature_child_membership_hash, WorkSizingSnapshot.membership_hash(["fresh-a", "fresh-b"]))
        self.assertEqual(snapshot.feature_planned_child_task_count, 2)

    def test_unavailable_reads_degrade_to_null_unavailable_without_blocking(self) -> None:
        runner = FakeBacklogitRunner({})

        snapshot = capture_work_sizing_snapshot(
            workspace=self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            shipment_id="092-S",
            runner=runner,
            snapshot_at="2026-07-24T03:37:49Z",
        )

        self.assertIsNone(snapshot.task_size_label)
        self.assertIsNone(snapshot.feature_planned_child_task_count)
        self.assertEqual(snapshot.sizing_sources["task"], "unavailable")
        self.assertEqual(snapshot.sizing_sources["feature"], "unavailable")
        self.assertEqual(snapshot.sizing_sources["shipment"], "unavailable")
        self.assertIsNone(snapshot.feature_child_membership_hash)
        self.assertIsNone(snapshot.shipment_membership_hash)

    def test_malformed_histogram_value_degrades_to_unavailable_without_raising(self) -> None:
        """Regression (Copilot review r3 B4): a malformed external histogram value
        (null, non-numeric string, infinity) must not let `telemetry begin` escape
        with an unhandled exception from `int(value)`. The affected composition
        degrades to unavailable while the non-blocking sizing contract holds and
        other reads (the task label) remain intact."""
        runner = FakeBacklogitRunner(
            {
                "079.013-T": _task("079.013-T", "M"),
                "079-F": _rollup(
                    "079-F",
                    [{"id": "079.001-T", "artifact_type": "task"}],
                    histogram={"M": "not-a-number"},
                ),
            }
        )

        snapshot = capture_work_sizing_snapshot(
            workspace=self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            runner=runner,
            snapshot_at="2026-07-24T03:37:49Z",
        )

        self.assertEqual(snapshot.task_size_label, "M")
        self.assertIsNone(snapshot.feature_planned_child_task_count)
        self.assertEqual(snapshot.feature_planned_child_size_histogram, {})
        self.assertIsNone(snapshot.feature_child_membership_hash)

    def test_reported_unsized_below_derived_keeps_composition_consistent(self) -> None:
        """Regression (Copilot review c6): the ``unsized`` bucket must derive
        purely from the canonical unique task-ID set so that count equals the sum
        of the histogram buckets. A smaller ``unsized`` reported by the rollup must
        not override the derived value and break ``feature_composition_consistent``.
        """
        runner = FakeBacklogitRunner(
            {
                "079.013-T": _task("079.013-T", "M"),
                "079-F": _rollup(
                    "079-F",
                    [
                        {"id": "a-T", "artifact_type": "task"},
                        {"id": "b-T", "artifact_type": "task"},
                        {"id": "c-T", "artifact_type": "task"},
                    ],
                    histogram={"M": 1},
                    unsized=1,  # rollup under-reports; derived unsized is 2
                ),
            }
        )

        snapshot = capture_work_sizing_snapshot(
            workspace=self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            runner=runner,
            snapshot_at="2026-07-24T03:37:49Z",
        )

        self.assertEqual(snapshot.feature_planned_child_task_count, 3)
        self.assertEqual(snapshot.feature_planned_child_size_histogram, {"M": 1, "unsized": 2})
        self.assertTrue(snapshot.feature_composition_consistent())

    def test_sync_failure_degrades_composition_without_consuming_stale_index(self) -> None:
        """Regression (Copilot review c10 / C50F24DD, 079.013-T freshness AC): a
        failed pre-capture freshness sync must degrade feature/shipment composition
        to explicit unavailable rather than silently reading a potentially stale
        cached index. Telemetry must still emit (non-blocking).
        """
        runner = FakeBacklogitRunner(
            {
                "079.013-T": _task("079.013-T", "M"),
                "079-F": _rollup("079-F", [{"id": "stale-T", "artifact_type": "task"}], histogram={"M": 1}),
                "092-S": _rollup("092-S", [{"id": "stale-T", "artifact_type": "task"}], histogram={"M": 1}),
            },
            sync_raises=True,
        )

        snapshot = capture_work_sizing_snapshot(
            workspace=self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            shipment_id="092-S",
            runner=runner,
            snapshot_at="2026-07-24T03:37:49Z",
        )

        # Snapshot still emitted — a failed sync does not block telemetry.
        self.assertEqual(snapshot.snapshot_boundary, "pre_execution")
        self.assertEqual(snapshot.task_size_label, "M")
        # Composition degraded to unavailable rather than read from a stale index.
        self.assertIsNone(snapshot.feature_planned_child_task_count)
        self.assertIsNone(snapshot.feature_child_membership_hash)
        self.assertEqual(snapshot.feature_planned_child_size_histogram, {})
        self.assertIsNone(snapshot.shipment_manifest_task_count)
        self.assertIsNone(snapshot.shipment_membership_hash)
        self.assertEqual(snapshot.sizing_sources["feature"], "unavailable")
        self.assertEqual(snapshot.sizing_sources["shipment"], "unavailable")

    def test_capture_once_context_remains_immutable_after_backlogit_mutation(self) -> None:
        runner = FakeBacklogitRunner(
            {
                "079.013-T": _task("079.013-T", "S"),
                "079-F": _rollup("079-F", [{"id": "original", "artifact_type": "task"}], histogram={"S": 1}),
            }
        )
        snapshot = capture_work_sizing_snapshot(
            workspace=self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            runner=runner,
            snapshot_at="2026-07-24T03:37:49Z",
        )
        config = load_telemetry_config({"mode": "sqlite"}, workspace_root=self.workspace)
        context = begin_context(
            config,
            self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            epoch_id="99999999-9999-4999-8999-999999999999",
            sizing=snapshot,
            captured_at="2026-07-24T03:37:49Z",
        )

        runner.responses["079.013-T"] = _task("079.013-T", "XL")
        runner.responses["079-F"] = _rollup("079-F", [{"id": "mutated", "artifact_type": "task"}], histogram={"XL": 1})
        payload = json.loads(context.context_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["sizing"]["task_size_label"], "S")
        self.assertEqual(payload["sizing"]["feature_child_membership_hash"], WorkSizingSnapshot.membership_hash(["original"]))
        self.assertEqual(len([call for call in runner.calls if call[0] == "sync"]), 1)
        self.assertNotIn("raw_tool_output", payload)
        self.assertNotIn("secret", payload)

    def test_cli_begin_can_capture_backlogit_sizing_snapshot(self) -> None:
        snapshot = WorkSizingSnapshot(
            snapshot_at="2026-07-24T03:37:49Z",
            task_size_label="M",
            feature_planned_child_task_count=1,
            feature_planned_child_size_histogram={"M": 1},
            feature_child_membership_hash=WorkSizingSnapshot.membership_hash(["079.013-T"]),
        )
        config_path = self.workspace / ".autoharness" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text('telemetry:\n  mode: "sqlite"\n', encoding="utf-8")
        stdout = io.StringIO()
        with mock.patch(
            "autoharness.telemetry.sizing.capture_work_sizing_snapshot",
            return_value=snapshot,
        ):
            with contextlib.redirect_stdout(stdout):
                main(
                    [
                        "telemetry",
                        "begin",
                        "--workspace",
                        str(self.workspace),
                        "--task-id",
                        "079.013-T",
                        "--feature-id",
                        "079-F",
                        "--capture-backlogit-sizing",
                        "--epoch-id",
                        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                        "--json",
                    ]
                )
        result = json.loads(stdout.getvalue())
        payload = json.loads((self.workspace / result["context_ref"]).read_text(encoding="utf-8"))

        self.assertEqual(payload["sizing"]["task_size_label"], "M")
        self.assertEqual(payload["sizing"]["feature_planned_child_task_count"], 1)

    def test_composition_skipped_ids_surfaced_diagnostically(self) -> None:
        """Copilot review t10 / 079.013-T AC: size_composition.skipped IDs must be
        surfaced on the snapshot (feature/shipment skipped-ID fields) rather than
        silently dropped from both the count and the histogram."""
        runner = FakeBacklogitRunner(
            {
                "079.013-T": _task("079.013-T", "M"),
                "079-F": _rollup(
                    "079-F",
                    [{"id": "079.001-T", "artifact_type": "task"}],
                    histogram={"M": 1},
                    skipped=[{"id": "079.404-T", "reason": "unresolved"}],
                ),
                "092-S": _rollup(
                    "092-S",
                    [{"id": "079.001-T", "artifact_type": "task"}],
                    histogram={"M": 1},
                    skipped=[{"id": "missing", "reason": "unresolved"}, "orphan"],
                ),
            }
        )

        snapshot = capture_work_sizing_snapshot(
            workspace=self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            shipment_id="092-S",
            runner=runner,
            snapshot_at="2026-07-24T03:37:49Z",
        )

        self.assertEqual(snapshot.feature_skipped_ids, ("079.404-T",))
        self.assertEqual(snapshot.shipment_skipped_ids, ("missing", "orphan"))
        # Skipped IDs stay out of the count/histogram but are visible in to_dict.
        self.assertEqual(snapshot.feature_planned_child_task_count, 1)
        self.assertEqual(snapshot.to_dict()["shipment_skipped_ids"], ["missing", "orphan"])

    def test_no_skipped_ids_defaults_to_empty(self) -> None:
        runner = FakeBacklogitRunner(
            {
                "079.013-T": _task("079.013-T", "M"),
                "079-F": _rollup("079-F", [{"id": "079.001-T", "artifact_type": "task"}], histogram={"M": 1}),
            }
        )
        snapshot = capture_work_sizing_snapshot(
            workspace=self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            runner=runner,
            snapshot_at="2026-07-24T03:37:49Z",
        )
        self.assertEqual(snapshot.feature_skipped_ids, ())
        self.assertEqual(snapshot.shipment_skipped_ids, ())

    def test_runner_timeout_degrades_to_unavailable_without_blocking(self) -> None:
        """Copilot review t7: a hung backlogit invocation (TimeoutExpired) must
        degrade sizing composition to unavailable rather than stalling Ship;
        telemetry still emits non-blocking."""

        def timing_out_runner(argv: tuple[str, ...], cwd: Path) -> str:
            raise subprocess.TimeoutExpired(cmd="backlogit", timeout=30.0)

        snapshot = capture_work_sizing_snapshot(
            workspace=self.workspace,
            task_id="079.013-T",
            feature_id="079-F",
            shipment_id="092-S",
            runner=timing_out_runner,
            snapshot_at="2026-07-24T03:37:49Z",
        )

        self.assertEqual(snapshot.snapshot_boundary, "pre_execution")
        self.assertIsNone(snapshot.task_size_label)
        self.assertIsNone(snapshot.feature_planned_child_task_count)
        self.assertEqual(snapshot.sizing_sources["task"], "unavailable")
        self.assertEqual(snapshot.sizing_sources["feature"], "unavailable")
        self.assertEqual(snapshot.sizing_sources["shipment"], "unavailable")

    def test_default_runner_passes_timeout_to_subprocess(self) -> None:
        """Copilot review t7: the default runner must bound every backlogit
        subprocess with a timeout so a hung process cannot stall indefinitely."""
        run = _default_runner("backlogit", timeout=12.0)
        with mock.patch("autoharness.telemetry.sizing.subprocess.run") as mocked:
            mocked.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="{}")
            run(("sync",), self.workspace)

        self.assertEqual(mocked.call_args.kwargs["timeout"], 12.0)


if __name__ == "__main__":
    unittest.main()
