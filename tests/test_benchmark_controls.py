"""Tests for benchmark reproducibility controls + run manifest (085.005-T)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.eval.benchmark.controls import (
    DEFAULT_ROUTE,
    RunManifest,
    classify_scenario_runs,
    compute_dispersion,
    run_benchmark,
)
from autoharness.eval.benchmark.harness import isolated_benchmark_telemetry_config, run_corpus
from autoharness.eval.benchmark.scenarios import load_default_corpus


class RunBenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workspace_root = Path(self._tmp.name)
        self.sink_root = self.workspace_root / "benchmark-sink"
        self.corpus = load_default_corpus()

    def test_manifest_reproduces_corpus_hash(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=1, seed=0, workspace_root=Path.cwd())
        self.assertEqual(manifest.corpus_hash, self.corpus.manifest_hash)

    def test_manifest_pins_route_and_seed(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=1, seed=42, workspace_root=Path.cwd())
        self.assertEqual(manifest.route, DEFAULT_ROUTE)
        self.assertEqual(manifest.seed, 42)

    def test_manifest_records_isolated_sink_paths(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=1, seed=0, workspace_root=Path.cwd())
        self.assertIn("execution_epochs.db", manifest.sink_database_path)
        self.assertNotIn(".autoharness", manifest.sink_database_path)

    def test_manifest_resolves_commit_sha_via_git(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=1, seed=0, workspace_root=Path.cwd())
        self.assertIsNotNone(manifest.commit_sha)
        self.assertEqual(len(manifest.commit_sha or ""), 40)

    def test_manifest_resolves_none_commit_sha_outside_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            non_repo = Path(tmp)
            _, manifest = run_benchmark(
                self.corpus, non_repo / "sink", repeats=1, seed=0, workspace_root=non_repo
            )
            self.assertIsNone(manifest.commit_sha)

    def test_cold_index_scenario_captured_and_classified_negative(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=1, seed=0, workspace_root=Path.cwd())
        cold = next(c for c in manifest.scenario_classifications if c.scenario_id == "pos-cold-index-miss")
        self.assertTrue(cold.degraded)
        self.assertTrue(cold.retained)
        self.assertEqual(cold.outcome_classification, "negative")

    def test_stale_scenario_retained_not_demoted_from_degraded_flag(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=1, seed=0, workspace_root=Path.cwd())
        stale = next(
            c for c in manifest.scenario_classifications if c.scenario_id == "neutral-stale-partial-recall"
        )
        self.assertTrue(stale.retained)
        # Stale-partial-recall does not set degraded_tool_count in the
        # executor (only cold does) — classification stays at its nominal
        # class rather than being demoted.
        self.assertFalse(stale.degraded)
        self.assertEqual(stale.outcome_classification, "neutral")

    def test_warm_scenario_not_degraded(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=1, seed=0, workspace_root=Path.cwd())
        warm = next(c for c in manifest.scenario_classifications if c.scenario_id == "pos-config-lookup-warm")
        self.assertFalse(warm.degraded)
        self.assertEqual(warm.outcome_classification, "positive")

    def test_degraded_and_stale_totals_are_nonzero(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=1, seed=0, workspace_root=Path.cwd())
        self.assertGreaterEqual(manifest.degraded_tool_count_total, 1)
        self.assertGreaterEqual(manifest.stale_or_unavailable_index_count_total, 2)

    def test_dispersion_present_when_repeats_greater_than_one(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=3, seed=1, workspace_root=Path.cwd())
        self.assertTrue(manifest.dispersion)
        for d in manifest.dispersion:
            self.assertEqual(len(d.values), 3)
            self.assertGreaterEqual(d.spread, 0.0)

    def test_no_dispersion_when_repeats_equal_one(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=1, seed=1, workspace_root=Path.cwd())
        self.assertEqual(manifest.dispersion, ())

    def test_repeated_runs_with_same_seed_reproduce_identical_dispersion(self) -> None:
        _, manifest_a = run_benchmark(
            self.corpus, self.sink_root / "a", repeats=3, seed=9, workspace_root=Path.cwd()
        )
        _, manifest_b = run_benchmark(
            self.corpus, self.sink_root / "b", repeats=3, seed=9, workspace_root=Path.cwd()
        )
        dispersion_a = {(d.scenario_id, d.arm): d.values for d in manifest_a.dispersion}
        dispersion_b = {(d.scenario_id, d.arm): d.values for d in manifest_b.dispersion}
        self.assertEqual(dispersion_a, dispersion_b)

    def test_manifest_to_dict_shape(self) -> None:
        _, manifest = run_benchmark(self.corpus, self.sink_root, repeats=1, seed=0, workspace_root=Path.cwd())
        payload = manifest.to_dict()
        self.assertIn("scenario_classifications", payload)
        self.assertIn("dispersion", payload)
        self.assertEqual(payload["corpus_hash"], self.corpus.manifest_hash)


class ClassifyAndDispersionUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workspace_root = Path(self._tmp.name)
        self.config = isolated_benchmark_telemetry_config(
            self.workspace_root / "sink", workspace_root=self.workspace_root
        )
        self.corpus = load_default_corpus()

    def test_classify_scenario_runs_never_promotes_to_positive(self) -> None:
        scenario = self.corpus.get("neutral-ambiguous-term-warm")
        repeats = run_corpus((scenario,), self.config, repeats=1, seed=0)[scenario.id]
        classification = classify_scenario_runs(scenario, repeats)
        self.assertIn(classification.outcome_classification, ("neutral",))

    def test_compute_dispersion_single_value_zero_spread(self) -> None:
        scenario = self.corpus.get("pos-config-lookup-warm")
        repeats = run_corpus((scenario,), self.config, repeats=1, seed=0)[scenario.id]
        dispersion = compute_dispersion(repeats, arm="baseline")
        self.assertEqual(dispersion.spread, 0.0)
        self.assertEqual(len(dispersion.values), 1)


if __name__ == "__main__":
    unittest.main()
