"""Tests for the honest reporting renderer (085.006-T)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.eval.benchmark.controls import run_benchmark
from autoharness.eval.benchmark.metrics import NOT_APPLICABLE
from autoharness.eval.benchmark.reporting import (
    BenchmarkReport,
    build_report,
    render_honest_report,
)
from autoharness.eval.benchmark.scenarios import load_default_corpus
from autoharness.telemetry.aggregation import UNAVAILABLE
from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.reader import read_epoch_records


class BuildReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workspace_root = Path(self._tmp.name)
        self.sink_root = self.workspace_root / "sink"
        self.corpus = load_default_corpus()
        self.results, self.manifest = run_benchmark(
            self.corpus, self.sink_root, repeats=2, seed=1, workspace_root=self.workspace_root
        )
        config = TelemetryConfig(
            enabled=True,
            mode="sqlite",
            database_path=Path(self.manifest.sink_database_path),
            emit_jsonl=True,
            jsonl_path=Path(self.manifest.sink_jsonl_path) if self.manifest.sink_jsonl_path else None,
        )
        self.read_result = read_epoch_records(config)
        self.report: BenchmarkReport = build_report(self.corpus, self.results, self.manifest, self.read_result)

    def test_every_scenario_included_including_negative_and_degraded(self) -> None:
        ids = {r.scenario_id for r in self.report.scenario_reports}
        self.assertEqual(ids, {s.id for s in self.corpus.scenarios})
        neg = next(r for r in self.report.scenario_reports if r.scenario_class == "negative")
        self.assertIsNotNone(neg)
        cold = next(r for r in self.report.scenario_reports if r.scenario_id == "pos-cold-index-miss")
        self.assertTrue(cold.degraded)

    def test_cold_index_forces_no_win_verdict_despite_cheaper_treatment(self) -> None:
        cold = next(r for r in self.report.scenario_reports if r.scenario_id == "pos-cold-index-miss")
        self.assertTrue(cold.correctness_regressed)
        self.assertEqual(cold.verdict, "no-win-correctness-regression")
        self.assertIsNotNone(cold.verdict_reason)
        # Treatment token cost is in fact lower here — verdict must still not
        # be "win" (H3: no efficiency win when correctness regressed).
        input_delta = cold.delta.fields["input_tokens"].delta
        self.assertIsInstance(input_delta, (int, float))
        self.assertLess(input_delta, 0)

    def test_stale_partial_recall_also_forces_no_win(self) -> None:
        stale = next(
            r for r in self.report.scenario_reports if r.scenario_id == "neutral-stale-partial-recall"
        )
        self.assertTrue(stale.correctness_regressed)
        self.assertEqual(stale.verdict, "no-win-correctness-regression")

    def test_warm_scenario_reports_legitimate_win(self) -> None:
        warm = next(r for r in self.report.scenario_reports if r.scenario_id == "pos-config-lookup-warm")
        self.assertFalse(warm.correctness_regressed)
        self.assertEqual(warm.verdict, "win")
        self.assertIsNone(warm.verdict_reason)

    def test_negative_scenario_reports_legitimate_win_when_both_correctly_empty(self) -> None:
        neg = next(r for r in self.report.scenario_reports if r.scenario_id == "neg-nonexistent-symbol-warm")
        self.assertFalse(neg.correctness_regressed)
        self.assertEqual(neg.baseline_score.classification, "exact")
        self.assertEqual(neg.treatment_score.classification, "exact")

    def test_aggregate_delta_present(self) -> None:
        self.assertIn("input_tokens", self.report.aggregate_delta.fields)

    def test_to_dict_roundtrip_shape(self) -> None:
        payload = self.report.to_dict()
        self.assertIn("manifest", payload)
        self.assertIn("scenario_reports", payload)
        self.assertIn("aggregate_delta", payload)
        self.assertEqual(len(payload["scenario_reports"]), len(self.corpus.scenarios))


class RenderHonestReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workspace_root = Path(self._tmp.name)
        self.sink_root = self.workspace_root / "sink"
        self.corpus = load_default_corpus()
        self.results, self.manifest = run_benchmark(
            self.corpus, self.sink_root, repeats=1, seed=3, workspace_root=self.workspace_root
        )
        config = TelemetryConfig(
            enabled=True,
            mode="sqlite",
            database_path=Path(self.manifest.sink_database_path),
            emit_jsonl=True,
            jsonl_path=Path(self.manifest.sink_jsonl_path) if self.manifest.sink_jsonl_path else None,
        )
        self.read_result = read_epoch_records(config)
        self.report = build_report(self.corpus, self.results, self.manifest, self.read_result)
        self.text = render_honest_report(self.report)

    def test_every_scenario_id_appears_in_text(self) -> None:
        for scenario in self.corpus.scenarios:
            self.assertIn(scenario.id, self.text)

    def test_regressed_scenarios_listed_explicitly(self) -> None:
        self.assertIn("Correctness-regressed scenarios", self.text)
        self.assertIn("pos-cold-index-miss", self.text)

    def test_no_win_verdict_rendered_for_regressed_scenario(self) -> None:
        self.assertIn("no-win-correctness-regression", self.text)

    def test_quality_labels_rendered(self) -> None:
        self.assertIn("quality=estimated", self.text)

    def test_manifest_identity_fields_rendered(self) -> None:
        self.assertIn(self.report.manifest.corpus_hash, self.text)
        self.assertIn(str(self.report.manifest.seed), self.text)


class EfficiencyVerdictSentinelTests(unittest.TestCase):
    """Unit-level check that a sentinel token delta never yields a false win/loss."""

    def test_inconclusive_when_field_delta_is_unavailable(self) -> None:
        from autoharness.eval.benchmark.metrics import FieldDelta, ScopeDelta
        from autoharness.eval.benchmark.reporting import _efficiency_verdict

        delta = ScopeDelta(
            scope="s1",
            baseline_repeat_count=0,
            treatment_repeat_count=0,
            fields={
                "input_tokens": FieldDelta("input_tokens", UNAVAILABLE, UNAVAILABLE, UNAVAILABLE, UNAVAILABLE),
                "output_tokens": FieldDelta("output_tokens", UNAVAILABLE, UNAVAILABLE, UNAVAILABLE, UNAVAILABLE),
            },
        )
        verdict, reason = _efficiency_verdict(delta)
        self.assertEqual(verdict, "inconclusive")
        self.assertIsNotNone(reason)

    def test_inconclusive_when_field_delta_is_not_applicable(self) -> None:
        from autoharness.eval.benchmark.metrics import FieldDelta, ScopeDelta
        from autoharness.eval.benchmark.reporting import _efficiency_verdict

        delta = ScopeDelta(
            scope="s1",
            baseline_repeat_count=1,
            treatment_repeat_count=1,
            fields={
                "input_tokens": FieldDelta(
                    "input_tokens", NOT_APPLICABLE, NOT_APPLICABLE, NOT_APPLICABLE, NOT_APPLICABLE
                ),
                "output_tokens": FieldDelta("output_tokens", 10, 5, -5, "observed"),
            },
        )
        verdict, reason = _efficiency_verdict(delta)
        self.assertEqual(verdict, "inconclusive")
        self.assertIsNotNone(reason)


if __name__ == "__main__":
    unittest.main()
