"""Tests for the deterministic event-to-epoch composer (U4, 084.004-T)."""

from __future__ import annotations

import random
import unittest

from autoharness.telemetry import tool_event_compose
from autoharness.telemetry.tool_event import _NONNEG_METRICS, ToolTelemetryEvent


def _event(**overrides) -> ToolTelemetryEvent:
    kwargs = dict(
        tool_surface="cli",
        tool_name="pytest",
        operation="run_tests",
        status="success",
        sensitivity="internal",
        epoch_id="1" * 32,
    )
    kwargs.update(overrides)
    # Auto-fill metric_sources/metric_quality for any populated nonneg metric so
    # tests can set metrics without hand-writing provenance for every field;
    # explicit metric_sources/metric_quality overrides still take precedence.
    sources = dict(kwargs.pop("metric_sources", {}) or {})
    quality = dict(kwargs.pop("metric_quality", {}) or {})
    for name in _NONNEG_METRICS:
        value = kwargs.get(name)
        if value:
            sources.setdefault(name, "host_reported")
            quality.setdefault(name, "observed")
    kwargs["metric_sources"] = sources
    kwargs["metric_quality"] = quality
    return ToolTelemetryEvent(**kwargs)


class OrderIndependenceTests(unittest.TestCase):
    def test_composition_is_independent_of_event_arrival_order(self) -> None:
        events = [
            _event(input_tokens=10, output_tokens=5, tool_name="engram.map_code", route_kind="structural_graph"),
            _event(input_tokens=20, output_tokens=7, tool_name="graphtor.search_local_docs", route_kind="doc_index"),
            _event(input_tokens=5, output_tokens=1, tool_name="grep", tool_surface="shell", route_kind="raw_search"),
        ]
        forward = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        shuffled = list(events)
        random.Random(42).shuffle(shuffled)
        reordered = tool_event_compose.compose_tool_events(shuffled, epoch_id="1" * 32)
        self.assertEqual(forward.to_dict(), reordered.to_dict())


class RetryAccumulationTests(unittest.TestCase):
    def test_delta_metrics_accumulate_across_retries(self) -> None:
        events = [
            _event(input_tokens=10, output_tokens=4, retry_count=0),
            _event(input_tokens=12, output_tokens=5, retry_count=1),
            _event(input_tokens=8, output_tokens=3, retry_count=2),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.economics.input_tokens, 30)
        self.assertEqual(result.economics.output_tokens, 12)


class CumulativeNotSummedTests(unittest.TestCase):
    def test_cumulative_totals_use_max_not_sum(self) -> None:
        events = [
            _event(cumulative_input_tokens=100, cumulative_output_tokens=40),
            _event(cumulative_input_tokens=250, cumulative_output_tokens=90),
            _event(cumulative_input_tokens=180, cumulative_output_tokens=60),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.economics.cumulative_input_tokens, 250)
        self.assertEqual(result.economics.cumulative_output_tokens, 90)

    def test_non_monotonic_cumulative_decrease_emits_diagnostic_but_keeps_max(self) -> None:
        # Ratified plan Review Fix #4: a timestamp-ordered decrease in either
        # cumulative token stream must be surfaced as a diagnostic while the
        # composed value still uses the maximum (never summed, never dropped).
        events = [
            _event(
                timestamp="2026-07-31T00:00:00+00:00",
                cumulative_input_tokens=100,
                cumulative_output_tokens=40,
            ),
            _event(
                timestamp="2026-07-31T00:00:01+00:00",
                cumulative_input_tokens=250,
                cumulative_output_tokens=90,
            ),
            _event(
                timestamp="2026-07-31T00:00:02+00:00",
                cumulative_input_tokens=180,
                cumulative_output_tokens=60,
            ),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.economics.cumulative_input_tokens, 250)
        self.assertEqual(result.economics.cumulative_output_tokens, 90)
        self.assertTrue(
            any(
                "cumulative_input_tokens" in diag and "non-monotonic" in diag
                for diag in result.diagnostics
            ),
            result.diagnostics,
        )
        self.assertTrue(
            any(
                "cumulative_output_tokens" in diag and "non-monotonic" in diag
                for diag in result.diagnostics
            ),
            result.diagnostics,
        )

    def test_monotonic_cumulative_stream_emits_no_diagnostic(self) -> None:
        events = [
            _event(
                timestamp="2026-07-31T00:00:00+00:00",
                cumulative_input_tokens=100,
                cumulative_output_tokens=40,
            ),
            _event(
                timestamp="2026-07-31T00:00:01+00:00",
                cumulative_input_tokens=250,
                cumulative_output_tokens=90,
            ),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertFalse(any("non-monotonic" in diag for diag in result.diagnostics))

    def test_context_tokens_before_uses_min_and_after_uses_max(self) -> None:
        events = [
            _event(context_tokens_before=1000, context_tokens_after=1200),
            _event(context_tokens_before=800, context_tokens_after=1500),
            _event(context_tokens_before=900, context_tokens_after=1100),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.economics.context_tokens_before, 800)
        self.assertEqual(result.economics.context_tokens_after, 1500)


class ProvenanceCorrectnessTests(unittest.TestCase):
    def test_populated_metric_carries_derived_source_and_worst_quality(self) -> None:
        events = [
            _event(
                input_tokens=10,
                metric_sources={"input_tokens": "host_reported"},
                metric_quality={"input_tokens": "observed"},
            ),
            _event(
                input_tokens=5,
                metric_sources={"input_tokens": "estimated"},
                metric_quality={"input_tokens": "estimated"},
            ),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.economics.metric_sources["input_tokens"], "derived")
        self.assertEqual(result.economics.metric_quality["input_tokens"], "estimated")

    def test_unpopulated_metric_has_no_provenance_entry(self) -> None:
        events = [_event()]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertNotIn("input_tokens", result.economics.metric_sources)
        self.assertNotIn("input_tokens", result.economics.metric_quality)

    def test_malformed_quality_label_normalizes_to_unavailable(self) -> None:
        # ToolTelemetryEvent.__post_init__ itself validates metric_quality
        # values against the schema vocabulary, so a malformed label can never
        # reach the composer through a real event; test the defensive
        # normalization helper directly instead.
        self.assertEqual(tool_event_compose._normalize_quality("not-a-real-label"), "unavailable")
        self.assertEqual(tool_event_compose._normalize_quality(None), "observed")
        self.assertEqual(tool_event_compose._worst_quality(["observed", "estimated"]), "estimated")
        self.assertEqual(tool_event_compose._worst_quality([]), "observed")

    def test_zero_valued_metric_does_not_downgrade_provenance_quality(self) -> None:
        # Review fix 5 (PR #273, PRRT_kwDORzpWpM6Vnq_h): a zero-valued metric is
        # "not observed" (schema exclusiveMinimum: 0 semantics) and must never
        # contribute to aggregated provenance quality, even when it carries an
        # "unavailable" quality label. Only strictly-positive contributors count.
        events = [
            _event(
                input_tokens=10,
                metric_sources={"input_tokens": "host_reported"},
                metric_quality={"input_tokens": "observed"},
            ),
            _event(
                input_tokens=0,
                metric_sources={"input_tokens": "unavailable"},
                metric_quality={"input_tokens": "unavailable"},
            ),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.economics.input_tokens, 10)
        self.assertEqual(result.economics.metric_quality["input_tokens"], "observed")


class ExplicitExpectationSemanticsTests(unittest.TestCase):
    def test_direct_invocation_with_self_expected_tool_counts_expected_and_observed(self) -> None:
        # Review Fixes #2, case 1: a direct invocation event (never
        # expectation-only) whose own expected_tool equals its own tool_name
        # counts one expected AND one observed opportunity in the same event —
        # no separate expectation event or parent_event_id link is needed.
        events = [
            _event(operation="code_search", tool_name="engram.map_code", expected_tool="engram.map_code", status="success"),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.operations.expected_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(result.operations.observed_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(result.operations.missing_expected_tool_counts.get("engram.map_code", 0), 0)

    def test_expectation_satisfied_by_parent_event_id_linked_invocation(self) -> None:
        # Review Fixes #2, case 2: a standalone expectation-only event is
        # identified by its event_id; a later invocation satisfies it only
        # when parent_event_id equals that expectation event's event_id and
        # tool_name matches the expectation's expected_tool.
        expectation = _event(
            event_id="e" * 32,
            operation="expect",
            status="skipped",
            expected_tool="engram.map_code",
        )
        invocation = _event(
            operation="code_search",
            tool_name="engram.map_code",
            status="success",
            parent_event_id="e" * 32,
        )
        result = tool_event_compose.compose_tool_events([expectation, invocation], epoch_id="1" * 32)
        self.assertEqual(result.operations.expected_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(result.operations.observed_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(result.operations.missing_expected_tool_counts.get("engram.map_code", 0), 0)

    def test_expectation_only_record_never_counts_as_invocation(self) -> None:
        events = [
            _event(
                operation="expect",
                status="skipped",
                tool_name="engram.map_code",
                expected_tool="engram.map_code",
            ),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.operations.expected_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(result.operations.observed_tool_counts.get("engram.map_code", 0), 0)
        self.assertEqual(result.operations.missing_expected_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(len(result.operations.cli_tools), 0)

    def test_unlinked_invocation_never_satisfies_expectation(self) -> None:
        # Review Fixes #2: unlinked events never satisfy an expectation. A
        # same-tool invocation with no parent_event_id at all (never even
        # attempting to link) leaves the expectation missing.
        events = [
            _event(event_id="e" * 32, operation="expect", status="skipped", expected_tool="engram.map_code"),
            _event(operation="doc_lookup", tool_name="engram.map_code", status="success"),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.operations.expected_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(result.operations.observed_tool_counts.get("engram.map_code", 0), 0)
        self.assertEqual(result.operations.missing_expected_tool_counts.get("engram.map_code"), 1)

    def test_invocation_with_wrong_parent_event_id_never_satisfies_expectation(self) -> None:
        # An invocation whose parent_event_id points at an event_id that is
        # not a standalone expectation event (or does not exist at all in the
        # correlated set) is unlinked and never satisfies an expectation.
        events = [
            _event(event_id="e" * 32, operation="expect", status="skipped", expected_tool="engram.map_code"),
            _event(operation="doc_lookup", tool_name="engram.map_code", status="success", parent_event_id="f" * 32),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.operations.observed_tool_counts.get("engram.map_code", 0), 0)
        self.assertEqual(result.operations.missing_expected_tool_counts.get("engram.map_code"), 1)

    def test_invocation_in_a_different_correlated_epoch_does_not_satisfy_expectation(self) -> None:
        # An invocation event under a *different* epoch is excluded from the
        # correlated set entirely and never satisfies this epoch's expectation,
        # regardless of any parent_event_id it might carry.
        events = [
            _event(event_id="e" * 32, operation="expect", status="skipped", expected_tool="engram.map_code"),
            _event(
                epoch_id="2" * 32,
                operation="doc_lookup",
                tool_name="engram.map_code",
                status="success",
                parent_event_id="e" * 32,
            ),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.operations.expected_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(result.operations.observed_tool_counts.get("engram.map_code", 0), 0)
        self.assertEqual(result.operations.missing_expected_tool_counts.get("engram.map_code"), 1)


class OverObservationTests(unittest.TestCase):
    def test_multiple_retries_under_one_expectation_count_one_expected_and_at_most_one_observed(self) -> None:
        # Review Fixes #2: multiple retries linked to the same expectation
        # event (same parent_event_id) count one expected opportunity and at
        # most one observed opportunity — never per-retry, never double
        # counted, never negative.
        events = [
            _event(event_id="e" * 32, operation="expect", status="skipped", expected_tool="engram.map_code"),
            _event(operation="code_search", tool_name="engram.map_code", status="success", parent_event_id="e" * 32),
            _event(operation="code_search", tool_name="engram.map_code", status="success", parent_event_id="e" * 32),
            _event(operation="code_search", tool_name="engram.map_code", status="success", parent_event_id="e" * 32),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.operations.expected_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(result.operations.observed_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(result.operations.missing_expected_tool_counts.get("engram.map_code", 0), 0)
        self.assertGreaterEqual(result.operations.missing_expected_tool_count, 0)

    def test_multiple_self_declared_invocations_of_same_tool_each_count_expected_and_observed(self) -> None:
        # Unlike the linked-retry case above, three *independent* self-declared
        # direct-invocation events (no shared parent expectation) each
        # legitimately declare and satisfy their own expected opportunity, so
        # expected/observed grow together and nothing is ever missing or
        # negative.
        events = [
            _event(operation="code_search", tool_name="engram.map_code", expected_tool="engram.map_code", status="success"),
            _event(operation="code_search", tool_name="engram.map_code", expected_tool="engram.map_code", status="success"),
            _event(operation="code_search", tool_name="engram.map_code", expected_tool="engram.map_code", status="success"),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.operations.expected_tool_counts.get("engram.map_code"), 3)
        self.assertEqual(result.operations.observed_tool_counts.get("engram.map_code"), 3)
        self.assertEqual(result.operations.missing_expected_tool_counts.get("engram.map_code", 0), 0)
        self.assertGreaterEqual(result.operations.missing_expected_tool_count, 0)


class FailedDegradedSeparateFromMissingTests(unittest.TestCase):
    def test_failed_and_degraded_invocations_still_satisfy_expectation(self) -> None:
        events = [
            _event(event_id="e" * 32, operation="expect", status="skipped", expected_tool="engram.map_code"),
            _event(operation="code_search", tool_name="engram.map_code", status="failed", parent_event_id="e" * 32),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.operations.observed_tool_counts.get("engram.map_code"), 1)
        self.assertEqual(result.operations.missing_expected_tool_counts.get("engram.map_code", 0), 0)
        self.assertEqual(result.outcome.tool_failure_count, 1)
        self.assertEqual(result.outcome.tool_degraded_count, 0)

    def test_degraded_invocation_counted_separately_not_as_missing(self) -> None:
        events = [
            _event(event_id="e" * 32, operation="expect", status="skipped", expected_tool="engram.map_code"),
            _event(operation="code_search", tool_name="engram.map_code", status="degraded", parent_event_id="e" * 32),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.operations.missing_expected_tool_counts.get("engram.map_code", 0), 0)
        self.assertEqual(result.outcome.tool_degraded_count, 1)
        self.assertEqual(result.outcome.tool_failure_count, 0)


class ZeroUnavailableMetricsTests(unittest.TestCase):
    def test_no_events_produces_zeroed_defaults_with_no_provenance(self) -> None:
        result = tool_event_compose.compose_tool_events([], epoch_id="1" * 32)
        self.assertEqual(result.economics.input_tokens, 0)
        self.assertEqual(result.economics.metric_sources, {})
        self.assertEqual(result.operations.expected_tool_count, 0)
        self.assertEqual(result.outcome.tool_gap_count, 0)
        self.assertEqual(result.selected_event_count, 0)

    def test_all_none_metrics_stay_zero_with_no_provenance(self) -> None:
        events = [_event(input_tokens=None, output_tokens=None)]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.economics.input_tokens, 0)
        self.assertNotIn("input_tokens", result.economics.metric_sources)


class CorrelationSelectionTests(unittest.TestCase):
    def test_epoch_id_match_is_selected_and_others_ignored(self) -> None:
        events = [
            _event(epoch_id="1" * 32, input_tokens=10),
            _event(epoch_id="2" * 32, input_tokens=999),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.selected_event_count, 1)
        self.assertEqual(result.ignored_event_count, 1)
        self.assertEqual(result.economics.input_tokens, 10)
        self.assertTrue(result.diagnostics)

    def test_backlog_item_id_fallback_only_for_events_without_epoch_id(self) -> None:
        events = [
            _event(epoch_id=None, backlog_item_id="084.004-T", input_tokens=10),
            _event(epoch_id="2" * 32, backlog_item_id="084.004-T", input_tokens=999),
        ]
        result = tool_event_compose.compose_tool_events(events, backlog_item_id="084.004-T")
        self.assertEqual(result.selected_event_count, 1)
        self.assertEqual(result.economics.input_tokens, 10)

    def test_compose_from_context_uses_context_epoch_id(self) -> None:
        context = {"epoch_id": "1" * 32, "backlog_item_id": "084.004-T"}
        events = [
            _event(epoch_id="1" * 32, input_tokens=10),
            _event(epoch_id="2" * 32, input_tokens=999),
        ]
        result = tool_event_compose.compose_from_context(events, context)
        self.assertEqual(result.selected_event_count, 1)
        self.assertEqual(result.economics.input_tokens, 10)


class RouteAndOperationsAggregationTests(unittest.TestCase):
    def test_route_kinds_and_tool_sets_are_sorted_unique(self) -> None:
        events = [
            _event(route_kind="doc_index", tool_name="graphtor.search_local_docs"),
            _event(route_kind="structural_graph", tool_name="engram.map_code"),
            _event(route_kind="doc_index", tool_name="graphtor.search_local_docs"),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.route.route_kinds, ("doc_index", "structural_graph"))
        self.assertEqual(result.operations.cli_tools, ("engram.map_code", "graphtor.search_local_docs"))

    def test_raw_and_avoided_counts_sum_across_events(self) -> None:
        events = [
            _event(raw_file_read_count=2, raw_search_count=1, avoided_file_read_count=3, tool_output_bytes=500),
            _event(raw_file_read_count=1, raw_search_count=0, avoided_file_read_count=2, tool_output_bytes=250),
        ]
        result = tool_event_compose.compose_tool_events(events, epoch_id="1" * 32)
        self.assertEqual(result.operations.raw_file_read_count, 3)
        self.assertEqual(result.operations.raw_search_count, 1)
        self.assertEqual(result.operations.avoided_file_read_count, 5)
        self.assertEqual(result.operations.tool_output_bytes, 750)


if __name__ == "__main__":
    unittest.main()
