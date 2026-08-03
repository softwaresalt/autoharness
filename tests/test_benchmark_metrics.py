"""Tests for the benchmark telemetry metrics extraction + A/B delta adapter (085.004-T)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.eval.benchmark.harness import isolated_benchmark_telemetry_config, run_corpus
from autoharness.eval.benchmark.metrics import (
    AGGREGATE_SCOPE,
    NOT_APPLICABLE,
    _record_field_quality,
    _worst_quality,
    compute_aggregate_delta,
    compute_corpus_deltas,
    compute_scenario_delta,
    compute_scope_delta,
    scenario_arm_records,
)
from autoharness.eval.benchmark.scenarios import load_default_corpus
from autoharness.telemetry.aggregation import UNAVAILABLE
from autoharness.telemetry.reader import read_epoch_records


class MetricsIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workspace_root = Path(self._tmp.name)
        self.sink_root = self.workspace_root / "benchmark-sink"
        self.config = isolated_benchmark_telemetry_config(self.sink_root, workspace_root=self.workspace_root)
        self.corpus = load_default_corpus()
        self.results = run_corpus(self.corpus.scenarios, self.config, repeats=3, seed=7)
        self.read_result = read_epoch_records(self.config)
        self.assertEqual(self.read_result.status, "ok")

    def test_scenario_arm_records_correlates_exact_repeat_count(self) -> None:
        records = self.read_result.records
        baseline = scenario_arm_records(records, "pos-config-lookup-warm", "baseline")
        treatment = scenario_arm_records(records, "pos-config-lookup-warm", "treatment")
        self.assertEqual(len(baseline), 3)
        self.assertEqual(len(treatment), 3)
        # No cross-scenario contamination.
        other_baseline = scenario_arm_records(records, "neg-nonexistent-symbol-warm", "baseline")
        self.assertEqual(len(other_baseline), 3)
        self.assertTrue(set(r["backlog_item_id"] for r in baseline).isdisjoint(
            set(r["backlog_item_id"] for r in other_baseline)
        ))

    def test_aggregate_total_math_matches_manual_sum(self) -> None:
        records = self.read_result.records
        baseline = scenario_arm_records(records, "pos-config-lookup-warm", "baseline")
        manual_total = sum(r["economics"]["input_tokens"] for r in baseline)

        delta = compute_scenario_delta(records, "pos-config-lookup-warm")
        self.assertEqual(delta.fields["input_tokens"].baseline_total, manual_total)

    def test_delta_is_treatment_minus_baseline(self) -> None:
        delta = compute_scenario_delta(self.read_result.records, "pos-config-lookup-warm")
        field_delta = delta.fields["input_tokens"]
        self.assertEqual(
            field_delta.delta,
            field_delta.treatment_total - field_delta.baseline_total,
        )

    def test_delta_never_averages_per_epoch_ratios(self) -> None:
        # Delta must equal (sum treatment) - (sum baseline), not an average of
        # per-repeat deltas — assert both computations agree, which is only
        # guaranteed for aggregate-total math (not ratio-averaging).
        records = self.read_result.records
        baseline = scenario_arm_records(records, "pos-config-lookup-warm", "baseline")
        treatment = scenario_arm_records(records, "pos-config-lookup-warm", "treatment")
        manual_delta = sum(r["economics"]["input_tokens"] for r in treatment) - sum(
            r["economics"]["input_tokens"] for r in baseline
        )
        delta = compute_scenario_delta(records, "pos-config-lookup-warm")
        self.assertEqual(delta.fields["input_tokens"].delta, manual_delta)

    def test_estimated_operand_yields_estimated_quality(self) -> None:
        delta = compute_scenario_delta(self.read_result.records, "pos-config-lookup-warm")
        for field_delta in delta.fields.values():
            # Every economics field the synthetic executor populates —
            # including context_area_tokens, which is never actually
            # measured (left at the dataclass default of 0) — is labeled
            # "estimated" (H4: an unmeasured proxy must never look
            # "observed" just because its default happens to be zero).
            self.assertIn(field_delta.quality, ("estimated", NOT_APPLICABLE, UNAVAILABLE))

    def test_compute_corpus_deltas_covers_every_scenario(self) -> None:
        scenario_ids = tuple(s.id for s in self.corpus.scenarios)
        deltas = compute_corpus_deltas(self.read_result, scenario_ids)
        self.assertEqual(set(deltas.keys()), set(scenario_ids))

    def test_aggregate_delta_uses_combined_totals_not_averaged_scenario_deltas(self) -> None:
        scenario_ids = tuple(s.id for s in self.corpus.scenarios)
        aggregate = compute_aggregate_delta(self.read_result, scenario_ids)
        self.assertEqual(aggregate.scope, AGGREGATE_SCOPE)

        records = self.read_result.records
        manual_baseline_total = 0
        manual_treatment_total = 0
        for scenario_id in scenario_ids:
            manual_baseline_total += sum(
                r["economics"]["input_tokens"] for r in scenario_arm_records(records, scenario_id, "baseline")
            )
            manual_treatment_total += sum(
                r["economics"]["input_tokens"] for r in scenario_arm_records(records, scenario_id, "treatment")
            )
        self.assertEqual(aggregate.fields["input_tokens"].baseline_total, manual_baseline_total)
        self.assertEqual(aggregate.fields["input_tokens"].treatment_total, manual_treatment_total)

    def test_empty_records_yield_unavailable_not_zero(self) -> None:
        delta = compute_scenario_delta((), "nonexistent-scenario")
        for field_delta in delta.fields.values():
            self.assertEqual(field_delta.delta, UNAVAILABLE)
            self.assertEqual(field_delta.quality, UNAVAILABLE)

    def test_operational_counters_honor_quality(self) -> None:
        # routed_lookup_count is populated + labeled "estimated" in this
        # harness's synthetic executor for every scenario/arm — the delta
        # must reflect that (never silently degrade to a bare int with no
        # quality-awareness, unlike the shipped aggregation._operation_sum).
        delta = compute_scenario_delta(self.read_result.records, "pos-config-lookup-warm")
        routed = delta.fields["routed_lookup_count"]
        self.assertEqual(routed.quality, "estimated")
        self.assertIsInstance(routed.delta, int)

    def test_net_offload_tokens_present(self) -> None:
        delta = compute_scenario_delta(self.read_result.records, "pos-config-lookup-warm")
        self.assertIn("net_offload_tokens", delta.fields)


class MalformedQualityLabelFailClosedTests(unittest.TestCase):
    """085.007-T acceptance: an unrecognized quality label degrades fail-closed.

    A ``metric_quality`` label that is present but not one of the recognized
    vocabulary values (``observed``/``derived``/``estimated``/
    ``not_applicable``/``unavailable``) must never be trusted verbatim — it is
    a genuine provenance gap, and the field must fail closed to
    ``unavailable`` for a populated (non-zero) value. A malformed label
    alongside a legitimate, unlabeled *zero* value still resolves to
    ``observed`` (a zero-count is a real observation on its own terms,
    independent of the malformed label) — this is intentional, asserted
    behavior, not an oversight.
    """

    def test_malformed_label_with_nonzero_value_fails_closed_to_unavailable(self) -> None:
        record = {"economics": {"input_tokens": 42, "metric_quality": {"input_tokens": "super-duper-certain"}}}
        self.assertEqual(_record_field_quality(record, "economics", "input_tokens"), UNAVAILABLE)

    def test_malformed_label_with_zero_value_resolves_observed(self) -> None:
        record = {"economics": {"input_tokens": 0, "metric_quality": {"input_tokens": "super-duper-certain"}}}
        self.assertEqual(_record_field_quality(record, "economics", "input_tokens"), "observed")

    def test_worst_quality_across_records_fails_closed_on_any_malformed_label(self) -> None:
        records = (
            {"economics": {"input_tokens": 10, "metric_quality": {"input_tokens": "observed"}}},
            {"economics": {"input_tokens": 20, "metric_quality": {"input_tokens": "bogus-label"}}},
        )
        self.assertEqual(_worst_quality(records, "economics", "input_tokens"), UNAVAILABLE)

    def test_field_delta_with_malformed_label_operand_yields_unavailable_delta(self) -> None:
        def _record(epoch_id: str, input_tokens: int, quality_label: str) -> dict:
            return {
                "epoch_id": epoch_id,
                "timestamp": "2026-08-03T00:00:00+00:00",
                "economics": {
                    "input_tokens": input_tokens,
                    "metric_quality": {"input_tokens": quality_label},
                },
            }

        baseline = (_record("baseline-1", 100, "estimated"),)
        treatment = (_record("treatment-1", 10, "not-a-real-label"),)
        scope_delta = compute_scope_delta(baseline, treatment, scope="malformed-label-probe")
        field_delta = scope_delta.fields["input_tokens"]
        self.assertEqual(field_delta.delta, UNAVAILABLE)
        self.assertEqual(field_delta.quality, UNAVAILABLE)

    def test_recognized_label_with_absent_value_still_fails_closed_to_unavailable(self) -> None:
        # Review-fix (Copilot thread PRRT_kwDORzpWpM6V5Usj): a recognized
        # quality label must not be trusted before the field's value is
        # confirmed present. An operational record such as
        # {"operations": {"metric_quality": {"raw_search_count": "estimated"}}}
        # has no raw_search_count key at all — trusting the label verbatim
        # would report an "estimated" quality for a value that was never
        # recorded, producing an estimated total of zero and violating the
        # unavailable-not-zero invariant (H1).
        record = {"operations": {"metric_quality": {"raw_search_count": "estimated"}}}
        self.assertEqual(_record_field_quality(record, "operations", "raw_search_count"), UNAVAILABLE)


class ScenarioArmRecordsColonCollisionTests(unittest.TestCase):
    """Review-fix (Copilot thread PRRT_kwDORzpWpM6V5UsG): exact scenario-id segment parsing.

    A naive prefix/suffix match on ``backlog_item_id`` conflates a scenario
    id that is itself a colon-delimited prefix of another scenario id — e.g.
    ``a`` and ``a:b`` — because ``benchmark:a:b:0:baseline`` both starts with
    ``benchmark:a:`` and ends with ``:baseline``. ``scenario_arm_records``
    must parse the repeat-index segment off first and match the remaining
    scenario-id segment for exact equality, not just prefix/suffix
    containment.
    """

    def test_short_scenario_id_does_not_absorb_colon_extended_scenario_id(self) -> None:
        records = (
            {"backlog_item_id": "benchmark:a:0:baseline", "economics": {"input_tokens": 10}},
            {"backlog_item_id": "benchmark:a:b:0:baseline", "economics": {"input_tokens": 999}},
        )
        matched = scenario_arm_records(records, "a", "baseline")
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["backlog_item_id"], "benchmark:a:0:baseline")

    def test_colon_extended_scenario_id_matches_only_its_own_records(self) -> None:
        records = (
            {"backlog_item_id": "benchmark:a:0:baseline", "economics": {"input_tokens": 10}},
            {"backlog_item_id": "benchmark:a:b:0:baseline", "economics": {"input_tokens": 999}},
        )
        matched = scenario_arm_records(records, "a:b", "baseline")
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["backlog_item_id"], "benchmark:a:b:0:baseline")


if __name__ == "__main__":
    unittest.main()
