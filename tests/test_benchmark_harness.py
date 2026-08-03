"""Tests for the benchmark run harness (085.002-T)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.eval.benchmark.harness import (
    ARMS,
    BenchmarkHarnessError,
    default_arm_executor,
    isolated_benchmark_telemetry_config,
    run_corpus,
    run_scenario,
)
from autoharness.eval.benchmark.scenarios import load_default_corpus
from autoharness.telemetry.config import DEFAULT_DATABASE_PATH
from autoharness.telemetry.reader import read_epoch_records


class SinkIsolationTests(unittest.TestCase):
    def test_refuses_production_metrics_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp)
            production_root = (workspace_root / DEFAULT_DATABASE_PATH).parent
            with self.assertRaises(BenchmarkHarnessError):
                isolated_benchmark_telemetry_config(production_root, workspace_root=workspace_root)

    def test_refuses_subdirectory_of_production_metrics_path(self) -> None:
        # Review-fix: the isolation check is containment-based, not just an
        # exact-equality comparison — a subdirectory under the production
        # metrics root must be rejected too, not only the root itself.
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp)
            production_subdir = (workspace_root / DEFAULT_DATABASE_PATH).parent / "nested"
            with self.assertRaises(BenchmarkHarnessError):
                isolated_benchmark_telemetry_config(production_subdir, workspace_root=workspace_root)

    def test_relative_sink_root_resolves_against_workspace_root_not_cwd(self) -> None:
        # Review-fix (Copilot thread PRRT_kwDORzpWpM6V5nyp): a relative
        # sink_root must resolve against the documented workspace_root
        # parameter, not the process CWD, regardless of what CWD happens to
        # be when this is called.
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp)
            config = isolated_benchmark_telemetry_config("benchmark-sink", workspace_root=workspace_root)
            self.assertEqual(
                config.database_path,
                (workspace_root / "benchmark-sink").resolve() / "execution_epochs.db",
            )

    def test_accepts_dedicated_benchmark_sink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp)
            sink_root = workspace_root / "benchmark-runs" / "run-1"
            config = isolated_benchmark_telemetry_config(sink_root, workspace_root=workspace_root)
            self.assertTrue(config.enabled)
            # Compare resolved paths — isolated_benchmark_telemetry_config()
            # resolves sink_root, which can normalize Windows short (8.3) path
            # segments and otherwise fail a naive string/Path equality check.
            self.assertEqual(config.database_path, sink_root.resolve() / "execution_epochs.db")

    def test_refuses_dedicated_benchmark_sink_outside_workspace(self) -> None:
        # Review-fix (Copilot thread PRRT_kwDORzpWpM6V55em, reiterating
        # PRRT_kwDORzpWpM6V5nyp): a sink outside workspace_root entirely
        # bypasses the workspace-containment boundary enforced for ordinary
        # telemetry (autoharness.telemetry.config) — reject it, matching
        # that precedent, rather than treating "elsewhere on disk" as
        # "isolated".
        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as sink_tmp:
            workspace_root = Path(workspace_tmp)
            sink_root = Path(sink_tmp) / "outside-benchmark-sink"
            with self.assertRaises(BenchmarkHarnessError):
                isolated_benchmark_telemetry_config(sink_root, workspace_root=workspace_root)


class RunScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workspace_root = Path(self._tmp.name)
        self.sink_root = self.workspace_root / "benchmark-sink"
        self.config = isolated_benchmark_telemetry_config(self.sink_root, workspace_root=self.workspace_root)
        self.corpus = load_default_corpus()

    def test_run_scenario_emits_exactly_two_epochs_per_repeat(self) -> None:
        scenario = self.corpus.get("pos-config-lookup-warm")
        repeats = run_scenario(scenario, self.config, repeats=3, seed=1)
        self.assertEqual(len(repeats), 3)
        for repeat in repeats:
            self.assertEqual(repeat.baseline.arm, "baseline")
            self.assertEqual(repeat.treatment.arm, "treatment")

        read_result = read_epoch_records(self.config)
        self.assertEqual(read_result.status, "ok")
        self.assertEqual(len(read_result.records), 3 * 2)

    def test_epoch_backlog_item_ids_are_unique_per_repeat(self) -> None:
        scenario = self.corpus.get("pos-config-lookup-warm")
        repeats = run_scenario(scenario, self.config, repeats=4, seed=2)
        ids = [run.backlog_item_id for repeat in repeats for run in repeat.arm_runs]
        self.assertEqual(len(ids), len(set(ids)))

    def test_total_sink_failure_fails_closed_not_silently(self) -> None:
        # Review-fix (Copilot thread PRRT_kwDORzpWpM6V5nzS): record_epoch is
        # deliberately fail-open at the sink layer and reports failure via
        # RecordSummary rather than raising. If run_scenario ignored that
        # result, a total sink outage would let a run "succeed" with fewer
        # than the promised 2xN epochs actually persisted. Simulate a total
        # sink failure by patching record_epoch to report neither sink
        # accepted the write.
        from unittest.mock import patch

        from autoharness.telemetry.record import RecordSummary

        scenario = self.corpus.get("pos-config-lookup-warm")
        failing_summary = RecordSummary(enabled=True, sqlite_written=False, jsonl_written=False)
        with patch("autoharness.eval.benchmark.harness.record_epoch", return_value=failing_summary):
            with self.assertRaises(BenchmarkHarnessError):
                run_scenario(scenario, self.config, repeats=1, seed=0)

    def test_backlog_item_id_equals_task_id(self) -> None:
        scenario = self.corpus.get("pos-config-lookup-warm")
        repeats = run_scenario(scenario, self.config, repeats=1, seed=0)
        for run in repeats[0].arm_runs:
            self.assertEqual(run.epoch.backlog_item_id, run.epoch.task_id)

    def test_baseline_always_recalls_gold_exactly(self) -> None:
        for scenario in self.corpus.scenarios:
            outcome = default_arm_executor(scenario, "baseline", 0, 0)
            self.assertEqual(set(outcome.produced_answer), set(scenario.gold_answer))

    def test_treatment_misses_entirely_under_cold_index(self) -> None:
        scenario = self.corpus.get("pos-cold-index-miss")
        outcome = default_arm_executor(scenario, "treatment", 0, 0)
        self.assertEqual(outcome.produced_answer, ())
        self.assertEqual(outcome.operations.degraded_tool_count, 1)
        self.assertEqual(outcome.operations.stale_or_unavailable_index_count, 1)

    def test_cold_index_run_is_captured_not_dropped(self) -> None:
        scenario = self.corpus.get("pos-cold-index-miss")
        repeats = run_scenario(scenario, self.config, repeats=1, seed=0)
        read_result = read_epoch_records(self.config)
        cold_records = [
            r for r in read_result.records if str(r.get("backlog_item_id", "")).startswith(
                f"benchmark:{scenario.id}:"
            )
        ]
        self.assertEqual(len(cold_records), 2)  # baseline + treatment, neither dropped

    def test_treatment_partial_recall_under_stale_index(self) -> None:
        scenario = self.corpus.get("neutral-stale-partial-recall")
        outcome = default_arm_executor(scenario, "treatment", 0, 0)
        self.assertTrue(set(outcome.produced_answer) < set(scenario.gold_answer))
        self.assertEqual(outcome.operations.stale_or_unavailable_index_count, 1)
        self.assertEqual(outcome.operations.degraded_tool_count, 0)

    def test_operational_counters_are_labeled_estimated(self) -> None:
        scenario = self.corpus.get("pos-config-lookup-warm")
        for arm in ARMS:
            outcome = default_arm_executor(scenario, arm, 0, 0)
            for name, quality in outcome.operations.metric_quality.items():
                self.assertEqual(quality, "estimated", f"{arm}.{name} should be labeled estimated")
            for name, quality in outcome.economics.metric_quality.items():
                self.assertEqual(quality, "estimated", f"{arm} economics.{name} should be labeled estimated")
            # Review-fix (Copilot thread PRRT_kwDORzpWpM6V5UuI): context_area_tokens
            # is never actually measured by this executor (left at the
            # dataclass default of 0), so it must be explicitly present in
            # the estimated-quality label set — otherwise its unset zero
            # would read as a legitimate "observed" zero-count instead of
            # the unmeasured proxy it actually is (H4).
            self.assertIn("context_area_tokens", outcome.economics.metric_quality)

    def test_production_metrics_db_untouched(self) -> None:
        production_db = self.workspace_root / DEFAULT_DATABASE_PATH
        scenario = self.corpus.get("pos-config-lookup-warm")
        run_scenario(scenario, self.config, repeats=2, seed=0)
        self.assertFalse(production_db.exists())

    def test_run_corpus_covers_every_scenario(self) -> None:
        results = run_corpus(self.corpus.scenarios, self.config, repeats=1, seed=0)
        self.assertEqual(set(results.keys()), {s.id for s in self.corpus.scenarios})

    def test_repeats_must_be_positive(self) -> None:
        scenario = self.corpus.get("pos-config-lookup-warm")
        with self.assertRaises(BenchmarkHarnessError):
            run_scenario(scenario, self.config, repeats=0, seed=0)


if __name__ == "__main__":
    unittest.main()
