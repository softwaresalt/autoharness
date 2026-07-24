"""Expected-vs-actual tool gap roll-up helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from autoharness.telemetry.epoch import AbsoluteOutcome, OperationalReality


@dataclass(frozen=True)
class ToolGapSummary:
    operations: OperationalReality
    outcome: AbsoluteOutcome
    diagnostics: Mapping[str, int]


def _count_sum(values: Mapping[str, int]) -> int:
    return sum(int(value) for value in values.values())


def _missing_counts(
    expected_tool_counts: Mapping[str, int],
    observed_tool_counts: Mapping[str, int],
) -> dict[str, int]:
    keys = set(expected_tool_counts) | set(observed_tool_counts)
    return {
        key: max(int(expected_tool_counts.get(key, 0)) - int(observed_tool_counts.get(key, 0)), 0)
        for key in sorted(keys)
        if int(expected_tool_counts.get(key, 0)) > 0
    }


def expected_tool_gap_rate(
    tool_name: str,
    expected_tool_counts: Mapping[str, int],
    missing_expected_tool_counts: Mapping[str, int],
) -> float | None:
    """Return missing/expected for a tool, or None when no expectation exists."""
    expected = int(expected_tool_counts.get(tool_name, 0))
    if expected == 0:
        return None
    return int(missing_expected_tool_counts.get(tool_name, 0)) / expected


def summarize_tool_gaps(
    *,
    expected_tool_counts: Mapping[str, int],
    observed_tool_counts: Mapping[str, int],
    route_kind_counts: Mapping[str, int] | None = None,
    raw_file_read_count: int = 0,
    raw_search_count: int = 0,
    routed_lookup_count: int = 0,
    avoided_file_read_count: int = 0,
    tool_output_bytes: int = 0,
    degraded_tool_count: int = 0,
    stale_or_unavailable_index_count: int = 0,
) -> ToolGapSummary:
    """Build epoch-level gap roll-ups from explicit aggregate evidence.

    This helper does not enforce routing policy. It records evidence supplied by
    the host/runtime: missing expected-tool invocations become gaps; stale or
    degraded routes where the expected tool was invoked remain diagnostics only.
    """
    route_kind_counts = dict(route_kind_counts or {})
    expected_tool_counts = dict(expected_tool_counts)
    observed_tool_counts = dict(observed_tool_counts)
    missing_expected_tool_counts = _missing_counts(expected_tool_counts, observed_tool_counts)
    expected_total = _count_sum(expected_tool_counts)
    observed_total = _count_sum(observed_tool_counts)
    missing_total = _count_sum(missing_expected_tool_counts)

    operations_sources = {
        "route_kind_counts": "host",
        "routed_lookup_count": "host",
        "raw_file_read_count": "host",
        "raw_search_count": "host",
        "avoided_file_read_count": "estimated",
        "tool_output_bytes": "host",
        "expected_tool_count": "host",
        "observed_expected_tool_count": "host",
        "missing_expected_tool_count": "derived",
        "expected_tool_counts": "host",
        "observed_tool_counts": "host",
        "missing_expected_tool_counts": "derived",
        "degraded_tool_count": "host",
        "stale_or_unavailable_index_count": "host",
    }
    operations_quality = {
        "route_kind_counts": "observed",
        "routed_lookup_count": "observed",
        "raw_file_read_count": "observed",
        "raw_search_count": "observed",
        "avoided_file_read_count": "estimated",
        "tool_output_bytes": "observed",
        "expected_tool_count": "observed",
        "observed_expected_tool_count": "observed",
        "missing_expected_tool_count": "derived",
        "expected_tool_counts": "observed",
        "observed_tool_counts": "observed",
        "missing_expected_tool_counts": "derived",
        "degraded_tool_count": "observed",
        "stale_or_unavailable_index_count": "observed",
    }
    outcome_sources = {"tool_gap_count": "derived"}
    outcome_quality = {"tool_gap_count": "derived"}

    operations = OperationalReality(
        route_kind_counts=route_kind_counts,
        routed_lookup_count=int(routed_lookup_count),
        raw_file_read_count=int(raw_file_read_count),
        raw_search_count=int(raw_search_count),
        avoided_file_read_count=int(avoided_file_read_count),
        tool_output_bytes=int(tool_output_bytes),
        expected_tool_count=expected_total,
        observed_expected_tool_count=observed_total,
        missing_expected_tool_count=missing_total,
        expected_tool_counts=expected_tool_counts,
        observed_tool_counts=observed_tool_counts,
        missing_expected_tool_counts=missing_expected_tool_counts,
        degraded_tool_count=int(degraded_tool_count),
        stale_or_unavailable_index_count=int(stale_or_unavailable_index_count),
        metric_sources=operations_sources,
        metric_quality=operations_quality,
    )
    outcome = AbsoluteOutcome(
        tool_gap_count=missing_total,
        metric_sources=outcome_sources,
        metric_quality=outcome_quality,
    )
    return ToolGapSummary(
        operations=operations,
        outcome=outcome,
        diagnostics={
            "degraded_tool_count": int(degraded_tool_count),
            "stale_or_unavailable_index_count": int(stale_or_unavailable_index_count),
            "raw_file_read_count": int(raw_file_read_count),
            "raw_search_count": int(raw_search_count),
        },
    )
