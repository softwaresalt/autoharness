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

    def test_quality_label_is_order_independent_least_certain(self) -> None:
        """Regression (Copilot review c9): multi-record quality labeling must be
        deterministic. It degrades to the least-certain quality across records
        rather than returning whichever record happens to be first in the slice.
        """
        from autoharness.telemetry.report import _quality

        observed = _record("obs", metric_quality="observed")
        unavailable = _record("unavail", metric_quality="unavailable")
        estimated = _record("est", metric_quality="estimated")

        self.assertEqual(_quality((observed, unavailable), "context_area_tokens"), "unavailable")
        self.assertEqual(_quality((unavailable, observed), "context_area_tokens"), "unavailable")
        self.assertEqual(_quality((observed, estimated), "context_area_tokens"), "estimated")
        self.assertEqual(_quality((estimated, observed), "context_area_tokens"), "estimated")

    def test_quality_flags_populated_metric_missing_label_as_unavailable(self) -> None:
        """090.006-T: a record whose economics carry a real (populated) value for
        a metric but whose metric_quality map has no entry for that field is a
        genuine provenance gap. Previously such records were skipped entirely
        (quality.get(field) is None -> continue), which let the aggregate fall
        through to the "observed" default purely for lack of information. Any
        populated record missing its label must degrade the aggregate to
        "unavailable" instead."""
        from autoharness.telemetry.report import _quality

        # _record()'s economics populate input_tokens=100 but metric_quality
        # only documents context_area_tokens — input_tokens has no label.
        record = _record("a")

        self.assertEqual(_quality((record,), "input_tokens"), "unavailable")

    def test_quality_preserves_observed_when_all_populated_records_labeled(self) -> None:
        """090.006-T: the missing-label degradation must not regress the common
        case — when every populated record carries a real "observed" label for
        the field, the aggregate quality remains "observed"."""
        from autoharness.telemetry.report import _quality

        record = _record("a")
        record["economics"]["metric_quality"]["input_tokens"] = "observed"

        self.assertEqual(_quality((record,), "input_tokens"), "observed")

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

    def test_report_surfaces_avoided_read_and_raw_search_totals(self) -> None:
        """Regression (Copilot review r3c C4 / NEW-2): the 079.012-T report
        contract requires avoided-read counts, raw-search counts, and token
        estimates to be aggregated into totals and rendered — they were summed
        elsewhere but omitted from ``_totals`` and the rendered surface.
        """
        record = _record("a")
        record["operations"]["raw_search_count"] = 3
        report = summarize_report(TelemetryReadResult("ok", (record,)))

        self.assertEqual(report.totals["avoided_file_read_count"], 2)
        self.assertEqual(report.totals["raw_search_count"], 3)

        text = render_report(report)
        self.assertIn("raw_searches=3", text)
        self.assertIn("Avoided reads: count=2", text)
        self.assertIn("est_tokens=80", text)
        self.assertIn("Tool-output estimate: est_tokens=20", text)

    def test_primary_economic_metrics_carry_quality_labels(self) -> None:
        """Regression (Copilot review r3c batch-D D3): the 079.012-T report
        contract requires every primary economic metric to expose provenance,
        not just ``context_area_tokens``. Token consumption/generation, COGS,
        and duration must each render their quality label so observed values are
        not confused with estimated or unavailable ones.
        """
        record = _record("a")
        record["economics"]["metric_quality"] = {
            "input_tokens": "observed",
            "output_tokens": "observed",
            "cogs_usd": "estimated",
            "duration_seconds": "estimated",
            "context_area_tokens": "estimated",
        }
        text = render_report(summarize_report(TelemetryReadResult("ok", (record,))))

        self.assertIn("Token consumption: 100 (observed)", text)
        self.assertIn("Token generation: 25 (observed)", text)
        self.assertIn("COGS: 2.0 (estimated)", text)
        self.assertIn("duration: 8.0 (estimated)", text)


if __name__ == "__main__":
    unittest.main()
