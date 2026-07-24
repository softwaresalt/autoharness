"""Tests for the comparative baseline summary (055.006-T).

Summarizes comparable baseline metrics across eval model configs and folds in
deterministic reviewer-matrix scores when available. Pure and reproducible.
"""

from __future__ import annotations

import unittest

from autoharness.eval.reviewer import DIMENSIONS, DimensionScore, ReviewMatrixResult
from autoharness.eval.runner import EvalRun, EvalRunReport, ResolvedFrozenState
from autoharness.eval.summary import BaselineSummary, ConfigSummary, summarize_baseline
from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
    WorkSizingSnapshot,
)
from autoharness.telemetry.record import RecordSummary


def _epoch(name, models, itok, otok, cogs, dur, gate=(0,)):
    return ExecutionEpoch(
        task_id=f"eval:{name}",
        route=RouteConfiguration(models=tuple(models)),
        economics=EconomicPayload(
            input_tokens=itok, output_tokens=otok, cogs_usd=cogs, duration_seconds=dur
        ),
        operations=OperationalReality(cli_tools=()),
        outcome=AbsoluteOutcome(gate_exit_codes=tuple(gate)),
    )


def _report(rows, frozen=ResolvedFrozenState("main", "HEAD", "abc123")):
    runs = tuple(
        EvalRun(
            config_name=row["name"],
            epoch=_epoch(**row),
            record=RecordSummary(enabled=False),
        )
        for row in rows
    )
    return EvalRunReport(frozen_state=frozen, runs=runs)


def _review(overall):
    dims = {d: DimensionScore(d, overall, 10.0, ()) for d in DIMENSIONS}
    return ReviewMatrixResult(dimensions=dims, overall=overall, files=())


_ROWS = [
    {"name": "opus", "models": ["claude-opus-4.6"], "itok": 2000, "otok": 1000, "cogs": 0.20, "dur": 120.0},
    {"name": "sonnet", "models": ["claude-sonnet-4.5"], "itok": 1000, "otok": 500, "cogs": 0.05, "dur": 60.0},
]


class SummaryStructureTests(unittest.TestCase):
    def test_returns_baseline_summary_with_one_row_per_config(self) -> None:
        summary = summarize_baseline(_report(_ROWS))
        self.assertIsInstance(summary, BaselineSummary)
        self.assertEqual([c.config_name for c in summary.configs], ["opus", "sonnet"])
        self.assertTrue(all(isinstance(c, ConfigSummary) for c in summary.configs))

    def test_config_rows_carry_economics_and_route(self) -> None:
        summary = summarize_baseline(_report(_ROWS))
        opus = summary.configs[0]
        self.assertEqual(opus.primary_model, "claude-opus-4.6")
        self.assertEqual(opus.input_tokens, 2000)
        self.assertEqual(opus.output_tokens, 1000)
        self.assertEqual(opus.total_tokens, 3000)
        self.assertEqual(opus.cogs_usd, 0.20)
        self.assertEqual(opus.duration_seconds, 120.0)

    def test_frozen_state_is_propagated(self) -> None:
        summary = summarize_baseline(_report(_ROWS))
        self.assertEqual(summary.frozen_base, "main")
        self.assertEqual(summary.frozen_head, "HEAD")
        self.assertEqual(summary.frozen_sha, "abc123")

    def test_frozen_state_none_is_tolerated(self) -> None:
        summary = summarize_baseline(_report(_ROWS, frozen=None))
        self.assertIsNone(summary.frozen_base)
        self.assertIsNone(summary.frozen_sha)


class ComparativeSelectorTests(unittest.TestCase):
    def test_cheapest_fastest_and_lowest_token_identified(self) -> None:
        summary = summarize_baseline(_report(_ROWS))
        self.assertEqual(summary.cheapest_config, "sonnet")
        self.assertEqual(summary.costliest_config, "opus")
        self.assertEqual(summary.fastest_config, "sonnet")
        self.assertEqual(summary.lowest_token_config, "sonnet")

    def test_totals_sum_across_configs(self) -> None:
        summary = summarize_baseline(_report(_ROWS))
        self.assertAlmostEqual(summary.total_cogs_usd, 0.25)
        self.assertEqual(summary.total_tokens, 4500)

    def test_blocked_configs_reflect_nonzero_gate_exit(self) -> None:
        rows = [
            {"name": "ok", "models": ["m"], "itok": 1, "otok": 1, "cogs": 0.0, "dur": 1.0, "gate": (0,)},
            {"name": "bad", "models": ["m"], "itok": 1, "otok": 1, "cogs": 0.0, "dur": 1.0, "gate": (0, 1)},
        ]
        summary = summarize_baseline(_report(rows))
        self.assertEqual(summary.blocked_configs, ("bad",))
        self.assertFalse(summary.configs[0].blocked)
        self.assertTrue(summary.configs[1].blocked)

    def test_cheapest_tie_breaks_alphabetically_for_determinism(self) -> None:
        rows = [
            {"name": "zeta", "models": ["m"], "itok": 1, "otok": 1, "cogs": 0.10, "dur": 5.0},
            {"name": "alpha", "models": ["m"], "itok": 1, "otok": 1, "cogs": 0.10, "dur": 5.0},
        ]
        summary = summarize_baseline(_report(rows))
        self.assertEqual(summary.cheapest_config, "alpha")


class ReviewFoldingTests(unittest.TestCase):
    def test_quality_absent_without_reviews(self) -> None:
        summary = summarize_baseline(_report(_ROWS))
        self.assertIsNone(summary.highest_quality_config)
        for config in summary.configs:
            self.assertIsNone(config.quality_overall)

    def test_quality_folded_in_when_reviews_provided(self) -> None:
        reviews = {"opus": _review(9.0), "sonnet": _review(6.0)}
        summary = summarize_baseline(_report(_ROWS), reviews=reviews)
        self.assertEqual(summary.configs[0].quality_overall, 9.0)
        self.assertEqual(summary.configs[1].quality_overall, 6.0)
        self.assertEqual(summary.highest_quality_config, "opus")

    def test_quality_dimensions_exposed(self) -> None:
        reviews = {"opus": _review(8.0), "sonnet": _review(8.0)}
        summary = summarize_baseline(_report(_ROWS), reviews=reviews)
        self.assertEqual(summary.configs[0].quality_dimensions["security"], 8.0)

    def test_highest_quality_tie_breaks_alphabetically(self) -> None:
        reviews = {"opus": _review(7.0), "sonnet": _review(7.0)}
        summary = summarize_baseline(_report(_ROWS), reviews=reviews)
        self.assertEqual(summary.highest_quality_config, "opus")

    def test_partial_reviews_only_score_present_configs(self) -> None:
        reviews = {"sonnet": _review(9.5)}
        summary = summarize_baseline(_report(_ROWS), reviews=reviews)
        self.assertIsNone(summary.configs[0].quality_overall)
        self.assertEqual(summary.configs[1].quality_overall, 9.5)
        self.assertEqual(summary.highest_quality_config, "sonnet")


class DeterminismTests(unittest.TestCase):
    def test_to_dict_is_reproducible(self) -> None:
        reviews = {"opus": _review(9.0), "sonnet": _review(6.0)}
        first = summarize_baseline(_report(_ROWS), reviews=reviews).to_dict()
        second = summarize_baseline(_report(_ROWS), reviews=reviews).to_dict()
        self.assertEqual(first, second)

    def test_to_dict_has_expected_shape(self) -> None:
        summary = summarize_baseline(_report(_ROWS))
        data = summary.to_dict()
        self.assertIn("configs", data)
        self.assertIn("cheapest_config", data)
        self.assertIn("frozen_state", data)
        self.assertEqual(len(data["configs"]), 2)

    def test_empty_report_summarizes_without_error(self) -> None:
        summary = summarize_baseline(_report([]))
        self.assertEqual(summary.configs, ())
        self.assertIsNone(summary.cheapest_config)
        self.assertEqual(summary.total_tokens, 0)


class TelemetryMetricFoldingTests(unittest.TestCase):
    def test_eval_summary_exposes_ratified_telemetry_metrics(self) -> None:
        epoch = ExecutionEpoch(
            task_id="eval:telemetry",
            route=RouteConfiguration(models=("m",)),
            economics=EconomicPayload(
                input_tokens=100,
                output_tokens=25,
                context_area_tokens=400,
                avoided_read_estimated_tokens=80,
                tool_output_estimated_tokens=20,
                cogs_usd=2.0,
                duration_seconds=8.0,
            ),
            operations=OperationalReality(
                expected_tool_count=2,
                observed_expected_tool_count=1,
                missing_expected_tool_count=1,
                expected_tool_counts={"engram.map_code": 2},
                observed_tool_counts={"engram.map_code": 1},
                missing_expected_tool_counts={"engram.map_code": 1},
            ),
            outcome=AbsoluteOutcome(gate_exit_codes=(0,), tool_gap_count=1),
            sizing=WorkSizingSnapshot(
                task_size_label="M",
                feature_planned_size_label=None,
                shipment_planned_size_label=None,
            ),
        )
        report = EvalRunReport(None, (EvalRun("telemetry", epoch, RecordSummary(enabled=False)),))

        summary = summarize_baseline(report)
        config = summary.configs[0]

        self.assertEqual(config.context_area_tokens, 400)
        self.assertEqual(config.net_offload_tokens, 60)
        self.assertEqual(config.consumption_generation_ratio, 4.0)
        self.assertEqual(config.expected_tool_gap_rate, 0.5)
        self.assertEqual(config.task_size_label, "M")
        self.assertEqual(summary.cost_per_successful_epoch, 2.0)

    def test_context_area_tokens_unavailable_is_not_false_precision(self) -> None:
        """Copilot review t8: when the epoch marks ``context_area_tokens``
        unavailable (as legacy/null normalization does), the summary must surface
        ``unavailable`` rather than the numeric 0 placeholder (079.006-T)."""
        epoch = ExecutionEpoch(
            task_id="eval:ctx-unavailable",
            route=RouteConfiguration(models=("m",)),
            economics=EconomicPayload(
                input_tokens=10,
                output_tokens=5,
                cogs_usd=1.0,
                context_area_tokens=0,
                metric_quality={"context_area_tokens": "unavailable"},
            ),
            operations=OperationalReality(),
            outcome=AbsoluteOutcome(gate_exit_codes=(0,)),
        )
        summary = summarize_baseline(
            EvalRunReport(None, (EvalRun("ctx", epoch, RecordSummary(enabled=False)),))
        )
        config = summary.configs[0]
        self.assertEqual(config.context_area_tokens, "unavailable")
        self.assertEqual(config.to_dict()["context_area_tokens"], "unavailable")

    def test_missing_metrics_are_unavailable_not_false_precision(self) -> None:
        epoch = ExecutionEpoch(
            task_id="eval:missing",
            route=RouteConfiguration(models=("m",)),
            economics=EconomicPayload(input_tokens=10, output_tokens=0, cogs_usd=1.0),
            operations=OperationalReality(),
            outcome=AbsoluteOutcome(gate_exit_codes=()),
        )
        summary = summarize_baseline(
            EvalRunReport(None, (EvalRun("missing", epoch, RecordSummary(enabled=False)),))
        )

        config = summary.configs[0]
        self.assertEqual(config.consumption_generation_ratio, "unavailable")
        self.assertEqual(config.expected_tool_gap_rate, "unavailable")
        self.assertEqual(summary.cost_per_successful_epoch, "unavailable")
        self.assertEqual(summary.planned_vs_composition, "unavailable")
        self.assertEqual(summary.cost_per_size_point, "unavailable")


if __name__ == "__main__":
    unittest.main()
