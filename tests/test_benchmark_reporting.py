"""Tests for the honest reporting renderer (085.006-T)."""

from __future__ import annotations

import dataclasses
import tempfile
import unittest
from pathlib import Path

from autoharness.eval.benchmark.controls import run_benchmark
from autoharness.eval.benchmark.harness import BENCHMARK_NAMESPACE_PREFIX
from autoharness.eval.benchmark.metrics import NOT_APPLICABLE
from autoharness.eval.benchmark.reporting import (
    BenchmarkReport,
    ReportIdentityError,
    RepeatCorrectnessVarianceError,
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


class BuildReportIdentityValidationTests(unittest.TestCase):
    """H6 review-fix: build_report fails closed on cross-run/mismatched inputs."""

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
        # Sanity: the unmodified fixture must build cleanly before each test
        # mutates exactly one input to prove that specific check fires.
        build_report(self.corpus, self.results, self.manifest, self.read_result)

    def test_corpus_hash_mismatch_rejected(self) -> None:
        bad_manifest = dataclasses.replace(self.manifest, corpus_hash="not-the-real-hash")
        with self.assertRaises(ReportIdentityError) as ctx:
            build_report(self.corpus, self.results, bad_manifest, self.read_result)
        self.assertIn("manifest_hash", str(ctx.exception))

    def test_results_missing_scenario_rejected(self) -> None:
        some_id = next(iter(self.results))
        truncated_results = {k: v for k, v in self.results.items() if k != some_id}
        with self.assertRaises(ReportIdentityError) as ctx:
            build_report(self.corpus, truncated_results, self.manifest, self.read_result)
        self.assertIn("missing=", str(ctx.exception))

    def test_results_extra_scenario_rejected(self) -> None:
        some_id = next(iter(self.results))
        padded_results = dict(self.results)
        padded_results["not-a-real-scenario"] = self.results[some_id]
        with self.assertRaises(ReportIdentityError) as ctx:
            build_report(self.corpus, padded_results, self.manifest, self.read_result)
        self.assertIn("extra=", str(ctx.exception))

    def test_repeat_count_mismatch_rejected(self) -> None:
        some_id = next(iter(self.results))
        short_results = dict(self.results)
        short_results[some_id] = self.results[some_id][:1]
        with self.assertRaises(ReportIdentityError) as ctx:
            build_report(self.corpus, short_results, self.manifest, self.read_result)
        self.assertIn("repeat run", str(ctx.exception))

    def test_failed_read_result_rejected(self) -> None:
        bad_read_result = dataclasses.replace(self.read_result, status="unavailable", records=())
        with self.assertRaises(ReportIdentityError) as ctx:
            build_report(self.corpus, self.results, self.manifest, bad_read_result)
        self.assertIn("status", str(ctx.exception))

    def test_missing_sink_records_rejected(self) -> None:
        some_id = next(iter(self.results))
        some_id_prefix = f"benchmark:{some_id}:"
        filtered_records = tuple(
            r for r in self.read_result.records if not str(r.get("backlog_item_id", "")).startswith(some_id_prefix)
        )
        bad_read_result = dataclasses.replace(self.read_result, records=filtered_records)
        with self.assertRaises(ReportIdentityError) as ctx:
            build_report(self.corpus, self.results, self.manifest, bad_read_result)
        self.assertIn("missing", str(ctx.exception))

    def test_cross_run_workspace_id_mismatch_rejected(self) -> None:
        mutated_records = []
        mutated_one = False
        for record in self.read_result.records:
            if not mutated_one and str(record.get("backlog_item_id", "")).startswith(BENCHMARK_NAMESPACE_PREFIX):
                record = dict(record)
                record["workspace_id"] = "benchmark:a-different-run"
                mutated_one = True
            mutated_records.append(record)
        self.assertTrue(mutated_one)
        bad_read_result = dataclasses.replace(self.read_result, records=tuple(mutated_records))
        with self.assertRaises(ReportIdentityError) as ctx:
            build_report(self.corpus, self.results, self.manifest, bad_read_result)
        self.assertIn("workspace_id", str(ctx.exception))

    def test_cross_run_session_id_mismatch_rejected(self) -> None:
        # A different run_id but an unchanged (shared/default) workspace_id
        # simulates the exact gap the reviewer flagged: two runs sharing a
        # workspace_id must still be distinguishable.
        mutated_records = []
        mutated_one = False
        for record in self.read_result.records:
            if not mutated_one and str(record.get("backlog_item_id", "")).startswith(BENCHMARK_NAMESPACE_PREFIX):
                record = dict(record)
                record["session_id"] = "a-different-run-id"
                mutated_one = True
            mutated_records.append(record)
        self.assertTrue(mutated_one)
        bad_read_result = dataclasses.replace(self.read_result, records=tuple(mutated_records))
        with self.assertRaises(ReportIdentityError) as ctx:
            build_report(self.corpus, self.results, self.manifest, bad_read_result)
        self.assertIn("run_id", str(ctx.exception))

    def test_duplicate_sink_record_rejected(self) -> None:
        # Two matching records for the same expected scenario/repeat/arm
        # identity (e.g. a read_result assembled by merging two runs) must
        # be refused rather than silently summed by scenario_arm_records().
        target = None
        for record in self.read_result.records:
            if str(record.get("backlog_item_id", "")).startswith(BENCHMARK_NAMESPACE_PREFIX):
                target = record
                break
        self.assertIsNotNone(target)
        duplicated_records = self.read_result.records + (dict(target),)
        bad_read_result = dataclasses.replace(self.read_result, records=duplicated_records)
        with self.assertRaises(ReportIdentityError) as ctx:
            build_report(self.corpus, self.results, self.manifest, bad_read_result)
        self.assertIn("more than one record", str(ctx.exception))


class RepeatCorrectnessVarianceTests(unittest.TestCase):
    """Review-fix (Copilot thread PRRT_kwDORzpWpM6WFzL7): correctness must be
    scored across every repeat, not just repeat 0 — a later repeat's
    regression must not slip past the H3 no-win rule."""

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

    def test_variance_across_repeats_fails_closed(self) -> None:
        scenario_id = "pos-config-lookup-warm"
        repeat_runs = self.results[scenario_id]
        self.assertGreaterEqual(len(repeat_runs), 2)
        # Corrupt repeat 1's treatment produced_answer so its correctness
        # score disagrees with repeat 0's — the exact violation of the
        # deterministic-core assumption this check exists to catch. Only
        # produced_answer is mutated; the sink/epoch identity fields used by
        # _validate_run_identity (H6) are untouched, so this isolates the H3
        # per-repeat variance check.
        mutated_treatment = dataclasses.replace(
            repeat_runs[1].treatment, produced_answer=("not-the-gold-answer-at-all",)
        )
        mutated_repeat = dataclasses.replace(repeat_runs[1], treatment=mutated_treatment)
        mutated_results = dict(self.results)
        mutated_results[scenario_id] = (repeat_runs[0], mutated_repeat) + repeat_runs[2:]

        with self.assertRaises(RepeatCorrectnessVarianceError) as ctx:
            build_report(self.corpus, mutated_results, self.manifest, self.read_result)
        self.assertIn(scenario_id, str(ctx.exception))

    def test_no_variance_when_all_repeats_agree(self) -> None:
        # Control: the unmodified fixture (every repeat's produced_answer is
        # identical for the deterministic default_arm_executor) must build
        # cleanly — this is not a fixed-verdict change, only a fail-closed
        # guard for genuine cross-repeat disagreement.
        report = build_report(self.corpus, self.results, self.manifest, self.read_result)
        self.assertEqual(len(report.scenario_reports), len(self.corpus.scenarios))


if __name__ == "__main__":
    unittest.main()
