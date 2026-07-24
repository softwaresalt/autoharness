"""Library-level telemetry report slicing and rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from autoharness.telemetry.aggregation import AggregationResult, aggregate_epochs
from autoharness.telemetry.reader import TelemetryReadResult

_ALLOWED_FILTERS = {
    "session_id",
    "backlog_item_id",
    "feature_id",
    "shipment_id",
    "phase",
    "branch",
    "commit_sha",
    "workspace_id",
    "agent_role",
    "task_id",
    "epoch_id",
}


@dataclass(frozen=True)
class TelemetryReportSummary:
    status: str
    filters: Mapping[str, str] = field(default_factory=dict)
    records: tuple[dict[str, Any], ...] = ()
    totals: Mapping[str, Any] = field(default_factory=dict)
    derived: Mapping[str, Any] = field(default_factory=dict)
    tool_gap_rates: Mapping[str, float | None] = field(default_factory=dict)
    size_groups: Mapping[str, Mapping[str, Mapping[str, Any]]] = field(default_factory=dict)
    unavailable_metrics: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


def filter_records(records: Iterable[dict[str, Any]], filters: Mapping[str, str] | None = None) -> tuple[dict[str, Any], ...]:
    filters = filters or {}
    unsupported = set(filters) - _ALLOWED_FILTERS
    if unsupported:
        raise ValueError(f"Unsupported telemetry report filters: {sorted(unsupported)}")
    result = []
    for record in records:
        if all(str(record.get(key)) == str(value) for key, value in filters.items()):
            result.append(record)
    return tuple(result)


def _unavailable_metrics(records: Iterable[dict[str, Any]]) -> tuple[str, ...]:
    unavailable: set[str] = set()
    for record in records:
        economics = record.get("economics") or {}
        for key, value in economics.items():
            if key.startswith("metric_"):
                continue
            if value is None or value == "unavailable":
                unavailable.add(key)
    return tuple(sorted(unavailable))


def summarize_report(
    read_result: TelemetryReadResult,
    *,
    filters: Mapping[str, str] | None = None,
) -> TelemetryReportSummary:
    records = filter_records(read_result.records, filters)
    if not records:
        return TelemetryReportSummary(
            status=read_result.status,
            filters=dict(filters or {}),
            diagnostics=read_result.diagnostics,
        )
    aggregate: AggregationResult = aggregate_epochs(records)
    return TelemetryReportSummary(
        status=read_result.status,
        filters=dict(filters or {}),
        records=records,
        totals=aggregate.totals,
        derived=aggregate.derived,
        tool_gap_rates=aggregate.tool_gap_rates,
        size_groups=aggregate.size_groups,
        unavailable_metrics=_unavailable_metrics(records),
        diagnostics=read_result.diagnostics,
    )


_QUALITY_RANK = {
    "observed": 0,
    "derived": 1,
    "estimated": 2,
    "not_applicable": 3,
    "unavailable": 4,
}


def _quality(records: tuple[dict[str, Any], ...], field: str) -> str:
    # Copilot review c9: aggregate quality deterministically across records by
    # degrading to the least-certain (highest-rank) quality present, so multi-epoch
    # slices never imply false precision or depend on record ordering.
    worst: str | None = None
    worst_rank = -1
    for record in records:
        quality = (record.get("economics") or {}).get("metric_quality") or {}
        label = quality.get(field)
        if label is None:
            continue
        rank = _QUALITY_RANK.get(str(label), _QUALITY_RANK["unavailable"])
        if rank > worst_rank:
            worst_rank = rank
            worst = str(label)
    if worst is not None:
        return worst
    return "unavailable" if field in _unavailable_metrics(records) else "observed"


def render_report(report: TelemetryReportSummary) -> str:
    if not report.records:
        diagnostics = "; ".join(report.diagnostics) if report.diagnostics else "no telemetry records"
        return f"Telemetry report: {report.status} — no telemetry records ({diagnostics})"

    lines = [
        "Telemetry report",
        f"Status: {report.status}",
        f"Filters: {dict(report.filters) if report.filters else 'none'}",
        f"Epochs: {len(report.records)}",
        f"Token consumption: {report.totals.get('input_tokens', 0)}",
        f"Token generation: {report.totals.get('output_tokens', 0)}",
        f"context-area estimates: {report.totals.get('context_area_tokens', 0)} ({_quality(report.records, 'context_area_tokens')})",
        f"COGS: {report.totals.get('cogs_usd', 0)}",
        f"duration: {report.totals.get('duration_seconds', 0)}",
        (
            "Routed/raw usage: "
            f"routed={report.totals.get('routed_lookup_count', 0)}, "
            f"raw_reads={report.totals.get('raw_file_read_count', 0)}"
        ),
        (
            "Expected/observed/missing: "
            f"{report.totals.get('expected_tool_count', 0)}/"
            f"{report.totals.get('observed_expected_tool_count', 0)}/"
            f"{report.totals.get('missing_expected_tool_count', 0)}"
        ),
        f"Per-tool gap rates: {dict(report.tool_gap_rates)}",
        f"Size-label distributions: {dict(report.size_groups)}",
    ]
    for key, value in report.derived.items():
        lines.append(f"{key}: {value}")
    if report.unavailable_metrics:
        lines.append(f"Unavailable metrics: {', '.join(report.unavailable_metrics)}")
    if report.diagnostics:
        lines.append(f"Diagnostics: {'; '.join(report.diagnostics)}")
    return "\n".join(lines)
