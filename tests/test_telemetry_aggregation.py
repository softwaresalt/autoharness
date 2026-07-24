"""Telemetry aggregation and derived metrics tests (079.011-T)."""

from __future__ import annotations

import unittest

from autoharness.telemetry.aggregation import (
    aggregate_epochs,
    derived_efficiency_metrics,
    is_successful_epoch,
)


def _record(
    epoch_id: str,
    timestamp: str,
    *,
    task_size: str | None = None,
    feature_size: str | None = None,
    shipment_size: str | None = None,
    input_tokens: int | None = 10,
    output_tokens: int | None = 5,
    avoided_tokens: int | None = 8,
    tool_output_tokens: int | None = 2,
    cogs_usd: float | None = 1.0,
    gate_exit_codes=(0,),
    blocked: bool | None = False,
    expected=None,
    observed=None,
    missing=None,
) -> dict:
    expected = expected if expected is not None else {"engram.map_code": 1}
    observed = observed if observed is not None else {"engram.map_code": 1}
    missing = missing if missing is not None else {"engram.map_code": 0}
    return {
        "epoch_id": epoch_id,
        "timestamp": timestamp,
        "schema_version": "1.1.0",
        "task_id": f"{epoch_id}-task",
        "feature_id": "079-F",
        "shipment_id": "092-S",
        "economics": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "avoided_read_estimated_tokens": avoided_tokens,
            "tool_output_estimated_tokens": tool_output_tokens,
            "cogs_usd": cogs_usd,
            "duration_seconds": 3.0,
            "metric_sources": {},
            "metric_quality": {},
        },
        "operations": {
            "expected_tool_counts": expected,
            "observed_tool_counts": observed,
            "missing_expected_tool_counts": missing,
            "expected_tool_count": sum(expected.values()),
            "observed_expected_tool_count": sum(observed.values()),
            "missing_expected_tool_count": sum(missing.values()),
            "route_kind_counts": {"structural_graph": 1},
            "raw_file_read_count": 0,
            "routed_lookup_count": 1,
        },
        "outcome": {
            "gate_exit_codes": list(gate_exit_codes),
            "blocked": blocked,
            "tool_gap_count": sum(missing.values()),
        },
        "sizing": {
            "task_size_label": task_size,
            "feature_planned_size_label": feature_size,
            "shipment_planned_size_label": shipment_size,
        },
    }


class TelemetryAggregationTests(unittest.TestCase):
    def test_date_buckets_normalize_mixed_offsets_to_utc(self) -> None:
        records = [
            _record("a", "2026-07-24T00:30:00+01:00"),
            _record("b", "2026-07-23T23:30:00Z"),
            _record("c", "2026-07-24T00:30:00Z"),
        ]

        result = aggregate_epochs(records, bucket="day")

        self.assertEqual([bucket.bucket for bucket in result.buckets], ["2026-07-23", "2026-07-24"])
        self.assertEqual(result.buckets[0].epoch_count, 2)
        self.assertEqual(result.buckets[1].epoch_count, 1)
        self.assertEqual([record["epoch_id"] for record in result.ordered_records], ["a", "b", "c"])

    def test_range_filtering_uses_utc_instants(self) -> None:
        records = [
            _record("before", "2026-07-23T23:59:59Z"),
            _record("inside", "2026-07-24T01:00:00+01:00"),
            _record("after", "2026-07-24T00:00:01Z"),
        ]

        result = aggregate_epochs(records, start="2026-07-24T00:00:00Z", end="2026-07-24T00:00:00Z")

        self.assertEqual([record["epoch_id"] for record in result.ordered_records], ["inside"])

    def test_deduplicates_by_epoch_id_and_preserves_first_conflict(self) -> None:
        first = _record("dup", "2026-07-24T00:00:00Z", input_tokens=10)
        identical = dict(first)
        conflict = _record("dup", "2026-07-24T00:00:00Z", input_tokens=999)

        result = aggregate_epochs([first, identical, conflict])

        self.assertEqual(result.total_epochs, 1)
        self.assertEqual(result.totals["input_tokens"], 10)
        self.assertTrue(any("conflict" in item.lower() for item in result.diagnostics))

    def test_per_tool_gap_invariants_and_rate(self) -> None:
        result = aggregate_epochs(
            [
                _record(
                    "gap",
                    "2026-07-24T00:00:00Z",
                    expected={"engram.map_code": 3},
                    observed={"engram.map_code": 1},
                    missing={"engram.map_code": 2},
                )
            ]
        )

        self.assertEqual(result.tool_gap_rates["engram.map_code"], 2 / 3)
        self.assertEqual(result.totals["missing_expected_tool_count"], 2)
        self.assertEqual(result.totals["tool_gap_count"], 2)

    def test_derived_metrics_use_aggregate_totals_not_average_of_epoch_ratios(self) -> None:
        result = aggregate_epochs(
            [
                _record("one", "2026-07-24T00:00:00Z", input_tokens=100, output_tokens=100),
                _record("two", "2026-07-24T01:00:00Z", input_tokens=1, output_tokens=1),
            ]
        )

        self.assertEqual(result.derived["consumption_generation_ratio"], 101 / 101)
        self.assertEqual(result.derived["net_offload_tokens"], 12)

    def test_successful_epoch_denominator_for_cost_per_successful_epoch(self) -> None:
        self.assertTrue(is_successful_epoch(_record("ok", "2026-07-24T00:00:00Z", gate_exit_codes=(0,))))
        self.assertFalse(is_successful_epoch(_record("empty", "2026-07-24T00:00:00Z", gate_exit_codes=())))
        self.assertFalse(is_successful_epoch(_record("failed", "2026-07-24T00:00:00Z", gate_exit_codes=(0, 1))))

        result = aggregate_epochs(
            [
                _record("ok1", "2026-07-24T00:00:00Z", cogs_usd=2.0, gate_exit_codes=(0,)),
                _record("ok2", "2026-07-24T00:00:00Z", cogs_usd=4.0, gate_exit_codes=(0,)),
                _record("failed", "2026-07-24T00:00:00Z", cogs_usd=100.0, gate_exit_codes=(1,)),
            ]
        )

        self.assertEqual(result.derived["cost_per_successful_epoch"], 3.0)

    def test_unavailable_derived_metrics_when_operands_missing_or_denominator_zero(self) -> None:
        metrics = derived_efficiency_metrics([_record("zero", "2026-07-24T00:00:00Z", output_tokens=0)])
        self.assertEqual(metrics["consumption_generation_ratio"], "unavailable")
        self.assertEqual(metrics["cost_per_successful_epoch"], 1.0)

        no_success = derived_efficiency_metrics([_record("fail", "2026-07-24T00:00:00Z", cogs_usd=1.0, gate_exit_codes=(1,))])
        self.assertEqual(no_success["cost_per_successful_epoch"], "unavailable")

        missing = derived_efficiency_metrics([_record("missing", "2026-07-24T00:00:00Z", avoided_tokens=None)])
        self.assertEqual(missing["net_offload_tokens"], "unavailable")

    def test_metric_quality_unavailable_excludes_value_from_aggregate(self) -> None:
        """Regression (Copilot review c8): a numeric metric whose metric_quality is
        'unavailable' (e.g. a normalized legacy row retaining its raw value) must be
        treated as a missing operand. Aggregate totals and derived metrics over it
        become unavailable rather than summing it as if it were observed precision.
        """
        observed = _record("obs", "2026-07-24T00:00:00Z", input_tokens=100, output_tokens=50)
        legacy = _record("legacy", "2026-07-24T01:00:00Z", input_tokens=999, output_tokens=1)
        legacy["economics"]["metric_quality"] = {"input_tokens": "unavailable"}

        result = aggregate_epochs([observed, legacy])

        self.assertEqual(result.totals["input_tokens"], "unavailable")
        self.assertEqual(result.derived["consumption_generation_ratio"], "unavailable")
        # A field without an unavailable-quality entry still aggregates normally.
        self.assertEqual(result.totals["output_tokens"], 51)

    def test_size_label_groups_are_ordinal_with_no_cost_per_point(self) -> None:
        result = aggregate_epochs(
            [
                _record("s1", "2026-07-24T00:00:00Z", task_size="S", cogs_usd=1.0),
                _record("s2", "2026-07-24T01:00:00Z", task_size="S", cogs_usd=3.0),
                _record("m1", "2026-07-24T02:00:00Z", task_size="M", cogs_usd=5.0),
            ]
        )

        self.assertEqual(result.size_groups["task_size_label"]["S"]["count"], 2)
        self.assertEqual(result.size_groups["task_size_label"]["S"]["cogs_usd_range"], (1.0, 3.0))
        self.assertEqual(result.derived["cost_per_size_point"], "unavailable")
        self.assertEqual(result.derived["planned_vs_composition"], "unavailable")

    def test_parent_child_costs_are_not_double_counted_in_feature_slices(self) -> None:
        result = aggregate_epochs(
            [
                _record("child-a", "2026-07-24T00:00:00Z", feature_size="L", cogs_usd=2.0),
                _record("child-b", "2026-07-24T01:00:00Z", feature_size="L", cogs_usd=3.0),
            ],
            group_by="feature_planned_size_label",
        )

        self.assertEqual(result.groups["L"]["totals"]["cogs_usd"], 5.0)
        self.assertNotIn("parent_planned_cost", result.groups["L"]["totals"])


if __name__ == "__main__":
    unittest.main()
