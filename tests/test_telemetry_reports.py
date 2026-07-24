"""Telemetry report slicing and rendering tests (079.012-T)."""

from __future__ import annotations

import unittest

from autoharness.telemetry.reader import TelemetryReadResult
from autoharness.telemetry.report import filter_records, render_report, summarize_report


def _record(epoch_id: str, *, feature_id="079-F", task_size="M", metric_quality="observed") -> dict:
    return {
        "epoch_id": epoch_id,
        "timestamp": "2026-07-24T04:06:55Z",
        "session_id": "s1",
        "backlog_item_id": "079.012-T",
        "feature_id": feature_id,
        "shipment_id": "092-S",
        "phase": "build",
        "branch": "feat/079",
        "commit_sha": "abc123",
        "economics": {
            "input_tokens": 100,
            "output_tokens": 25,
            "context_area_tokens": 400,
            "avoided_read_estimated_tokens": 80,
            "tool_output_estimated_tokens": 20,
            "cogs_usd": 2.0,
            "duration_seconds": 8.0,
            "metric_sources": {"context_area_tokens": "estimated"},
            "metric_quality": {"context_area_tokens": metric_quality},
        },
        "operations": {
            "route_kind_counts": {"structural_graph": 1, "raw_read": 1},
            "routed_lookup_count": 1,
            "raw_file_read_count": 1,
            "avoided_file_read_count": 2,
            "expected_tool_count": 2,
            "observed_expected_tool_count": 1,
            "missing_expected_tool_count": 1,
            "expected_tool_counts": {"engram.map_code": 2},
            "observed_tool_counts": {"engram.map_code": 1},
            "missing_expected_tool_counts": {"engram.map_code": 1},
        },
        "outcome": {"gate_exit_codes": [0], "tool_gap_count": 1},
        "sizing": {
            "task_size_label": task_size,
            "feature_planned_size_label": None,
            "shipment_planned_size_label": None,
        },
    }


class TelemetryReportTests(unittest.TestCase):
    def test_filters_by_persisted_correlation_fields_only(self) -> None:
        records = [_record("a", feature_id="079-F"), _record("b", feature_id="080-F")]

        filtered = filter_records(records, {"feature_id": "079-F", "branch": "feat/079"})

        self.assertEqual([record["epoch_id"] for record in filtered], ["a"])
        with self.assertRaises(ValueError):
            filter_records(records, {"computed_gap_rate": "0.5"})

    def test_report_summary_includes_required_metric_surfaces(self) -> None:
        report = summarize_report(TelemetryReadResult("ok", (_record("a"),)), filters={"feature_id": "079-F"})

        self.assertEqual(report.status, "ok")
        self.assertEqual(report.filters, {"feature_id": "079-F"})
        self.assertEqual(report.totals["input_tokens"], 100)
        self.assertEqual(report.totals["output_tokens"], 25)
        self.assertEqual(report.totals["context_area_tokens"], 400)
        self.assertEqual(report.totals["routed_lookup_count"], 1)
        self.assertEqual(report.totals["raw_file_read_count"], 1)
        self.assertEqual(report.totals["missing_expected_tool_count"], 1)
        self.assertEqual(report.tool_gap_rates["engram.map_code"], 0.5)
        self.assertEqual(report.derived["net_offload_tokens"], 60)
        self.assertEqual(report.size_groups["task_size_label"]["M"]["count"], 1)

    def test_rendered_output_distinguishes_quality_and_unavailable_values(self) -> None:
        text = render_report(summarize_report(TelemetryReadResult("ok", (_record("a", metric_quality="estimated"),))))

        self.assertIn("Token consumption: 100", text)
        self.assertIn("Token generation: 25", text)
        self.assertIn("context-area estimates: 400 (estimated)", text)
        self.assertIn("COGS: 2.0", text)
        self.assertIn("duration: 8.0", text)
        self.assertIn("net_offload_tokens: 60", text)
        self.assertIn("planned_vs_composition: unavailable", text)
        self.assertIn("cost_per_size_point: unavailable", text)

    def test_degraded_inputs_render_gracefully(self) -> None:
        for status in ("disabled", "unavailable", "empty"):
            text = render_report(TelemetryReadResult(status, (), ("missing input",)))
            self.assertIn(status, text)
            self.assertIn("no telemetry records", text)

    def test_partial_v1_records_do_not_get_false_precision(self) -> None:
        partial = _record("legacy")
        partial["economics"]["context_area_tokens"] = None
        report = summarize_report(TelemetryReadResult("ok", (partial,)))

        self.assertEqual(report.derived["net_offload_tokens"], 60)
        self.assertIn("context_area_tokens", report.unavailable_metrics)


if __name__ == "__main__":
    unittest.main()
