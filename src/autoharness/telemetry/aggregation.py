"""Telemetry aggregation and derived efficiency metrics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


UNAVAILABLE = "unavailable"
_SIZE_FIELDS = (
    "task_size_label",
    "feature_planned_size_label",
    "shipment_planned_size_label",
)


@dataclass(frozen=True)
class BucketSummary:
    bucket: str
    epoch_count: int
    totals: Mapping[str, Any]


@dataclass(frozen=True)
class AggregationResult:
    total_epochs: int
    ordered_records: tuple[dict[str, Any], ...]
    buckets: tuple[BucketSummary, ...]
    totals: Mapping[str, Any]
    derived: Mapping[str, Any]
    tool_gap_rates: Mapping[str, float | None]
    size_groups: Mapping[str, Mapping[str, Mapping[str, Any]]]
    groups: Mapping[str, Mapping[str, Any]]
    diagnostics: tuple[str, ...] = field(default_factory=tuple)


def _canonical(record: Mapping[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _parse_instant(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _number(value: Any) -> float | int | None:
    if value is None or value == UNAVAILABLE:
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_field(records: Iterable[dict[str, Any]], section: str, field: str) -> float | int | None:
    total: float | int = 0
    for record in records:
        sec = record.get(section) or {}
        # Copilot review c8: honor metric_quality. A metric marked unavailable or
        # not_applicable is a missing operand even when a raw numeric value is
        # retained (e.g. normalized legacy rows), so the aggregate is unavailable
        # rather than implying false precision (telemetry-reference contract).
        quality = (sec.get("metric_quality") or {}).get(field)
        if quality in ("unavailable", "not_applicable"):
            return None
        value = _number(sec.get(field))
        if value is None:
            return None
        total += value
    return total


def _economic_total(records: Iterable[dict[str, Any]], field: str) -> float | int | str:
    value = _sum_field(records, "economics", field)
    return UNAVAILABLE if value is None else value


def _operation_sum(records: Iterable[dict[str, Any]], field: str) -> int:
    return sum(int((record.get("operations") or {}).get(field) or 0) for record in records)


def _outcome_sum(records: Iterable[dict[str, Any]], field: str) -> int:
    return sum(int((record.get("outcome") or {}).get(field) or 0) for record in records)


def is_successful_epoch(record: Mapping[str, Any]) -> bool:
    outcome = record.get("outcome") if isinstance(record.get("outcome"), Mapping) else {}
    codes = outcome.get("gate_exit_codes") or ()
    if not codes:
        return False
    blocked = outcome.get("blocked")
    if blocked is None:
        blocked = any(int(code) != 0 for code in codes)
    return not bool(blocked) and all(int(code) == 0 for code in codes)


def _dedupe(records: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    by_id: dict[str, tuple[dict[str, Any], str]] = {}
    diagnostics: list[str] = []
    for record in records:
        epoch_id = str(record.get("epoch_id"))
        canonical = _canonical(record)
        existing = by_id.get(epoch_id)
        if existing is None:
            by_id[epoch_id] = (record, canonical)
        elif existing[1] != canonical:
            diagnostics.append(f"conflict for epoch_id {epoch_id}; first accepted content preserved")
    return [entry[0] for entry in by_id.values()], diagnostics


def _derived_ratio(numerator: float | int | None, denominator: float | int | None) -> float | str:
    if numerator is None or denominator is None or denominator == 0:
        return UNAVAILABLE
    return numerator / denominator


def derived_efficiency_metrics(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records = list(records)
    input_tokens = _sum_field(records, "economics", "input_tokens")
    output_tokens = _sum_field(records, "economics", "output_tokens")
    avoided = _sum_field(records, "economics", "avoided_read_estimated_tokens")
    tool_output = _sum_field(records, "economics", "tool_output_estimated_tokens")
    expected = _operation_sum(records, "expected_tool_count")
    missing = _operation_sum(records, "missing_expected_tool_count")

    successful = [record for record in records if is_successful_epoch(record)]
    successful_cost = _sum_field(successful, "economics", "cogs_usd") if successful else None

    return {
        "net_offload_tokens": (
            UNAVAILABLE if avoided is None or tool_output is None else avoided - tool_output
        ),
        "consumption_generation_ratio": _derived_ratio(input_tokens, output_tokens),
        "gap_rate": _derived_ratio(missing, expected),
        "cost_per_successful_epoch": _derived_ratio(successful_cost, len(successful)),
        "planned_vs_composition": UNAVAILABLE,
        "cost_per_size_point": UNAVAILABLE,
    }


def _per_tool_rates(records: Iterable[dict[str, Any]]) -> dict[str, float | None]:
    expected: dict[str, int] = {}
    observed: dict[str, int] = {}
    missing: dict[str, int] = {}
    for record in records:
        ops = record.get("operations") or {}
        for key, value in (ops.get("expected_tool_counts") or {}).items():
            expected[key] = expected.get(key, 0) + int(value)
        for key, value in (ops.get("observed_tool_counts") or {}).items():
            observed[key] = observed.get(key, 0) + int(value)
        for key, value in (ops.get("missing_expected_tool_counts") or {}).items():
            missing[key] = missing.get(key, 0) + int(value)
    # Derive missing from expected/observed for invariant checking; stored missing
    # remains in totals, but rates use the same max(expected-observed, 0) rule.
    rates: dict[str, float | None] = {}
    for key in sorted(set(expected) | set(observed) | set(missing)):
        expected_count = expected.get(key, 0)
        if expected_count == 0:
            rates[key] = None
        else:
            rates[key] = max(expected_count - observed.get(key, 0), 0) / expected_count
    return rates


def _totals(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "input_tokens": _economic_total(records, "input_tokens"),
        "output_tokens": _economic_total(records, "output_tokens"),
        "context_area_tokens": _economic_total(records, "context_area_tokens"),
        "avoided_read_estimated_tokens": _economic_total(records, "avoided_read_estimated_tokens"),
        "tool_output_estimated_tokens": _economic_total(records, "tool_output_estimated_tokens"),
        "cogs_usd": _economic_total(records, "cogs_usd"),
        "duration_seconds": _economic_total(records, "duration_seconds"),
        "expected_tool_count": _operation_sum(records, "expected_tool_count"),
        "observed_expected_tool_count": _operation_sum(records, "observed_expected_tool_count"),
        "missing_expected_tool_count": _operation_sum(records, "missing_expected_tool_count"),
        "tool_gap_count": _outcome_sum(records, "tool_gap_count"),
        "raw_file_read_count": _operation_sum(records, "raw_file_read_count"),
        "routed_lookup_count": _operation_sum(records, "routed_lookup_count"),
    }


def _bucket_records(records: list[dict[str, Any]], bucket: str) -> tuple[BucketSummary, ...]:
    if bucket != "day":
        raise ValueError("only day buckets are supported in 079-F core")
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        key = _parse_instant(str(record["timestamp"])).date().isoformat()
        groups.setdefault(key, []).append(record)
    return tuple(
        BucketSummary(bucket=key, epoch_count=len(group), totals=_totals(group))
        for key, group in sorted(groups.items())
    )


def _size_groups(records: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    output: dict[str, dict[str, dict[str, Any]]] = {}
    for field in _SIZE_FIELDS:
        # Copilot review t2: count every epoch in a label group, but only include
        # a cogs value in the cost range when its metric_quality is available. An
        # unavailable cost must never be coerced to a fabricated 0.0; a group with
        # no measured cost surfaces an explicit unavailable range.
        field_counts: dict[str, int] = {}
        field_costs: dict[str, list[float]] = {}
        for record in records:
            sizing = record.get("sizing") or {}
            label = sizing.get(field) if isinstance(sizing, Mapping) else None
            if label is None:
                continue
            key = str(label)
            field_counts[key] = field_counts.get(key, 0) + 1
            economics = record.get("economics") or {}
            quality = (economics.get("metric_quality") or {}).get("cogs_usd")
            if quality in ("unavailable", "not_applicable"):
                continue
            cogs = _number(economics.get("cogs_usd"))
            if cogs is None:
                continue
            field_costs.setdefault(key, []).append(float(cogs))
        output[field] = {
            label: {
                "count": field_counts[label],
                "cogs_usd_range": (
                    (min(costs), max(costs)) if (costs := field_costs.get(label)) else UNAVAILABLE
                ),
                "ordinal_only": True,
            }
            for label in sorted(field_counts)
        }
    return output


def _group_by(records: list[dict[str, Any]], group_by: str | None) -> dict[str, dict[str, Any]]:
    if not group_by:
        return {}
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        value = None
        if group_by in _SIZE_FIELDS:
            sizing = record.get("sizing") or {}
            value = sizing.get(group_by) if isinstance(sizing, Mapping) else None
        else:
            value = record.get(group_by)
        if value is not None:
            groups.setdefault(str(value), []).append(record)
    return {
        key: {
            "epoch_count": len(group),
            "totals": _totals(group),
            "derived": derived_efficiency_metrics(group),
        }
        for key, group in sorted(groups.items())
    }


def aggregate_epochs(
    records: Iterable[dict[str, Any]],
    *,
    bucket: str = "day",
    start: str | None = None,
    end: str | None = None,
    group_by: str | None = None,
) -> AggregationResult:
    unique, diagnostics = _dedupe(records)
    start_dt = _parse_instant(start) if start else None
    end_dt = _parse_instant(end) if end else None
    filtered: list[dict[str, Any]] = []
    for record in unique:
        instant = _parse_instant(str(record["timestamp"]))
        if start_dt and instant < start_dt:
            continue
        if end_dt and instant > end_dt:
            continue
        filtered.append(record)
    ordered = sorted(filtered, key=lambda item: (_parse_instant(str(item["timestamp"])), str(item["epoch_id"])))
    return AggregationResult(
        total_epochs=len(ordered),
        ordered_records=tuple(ordered),
        buckets=_bucket_records(ordered, bucket),
        totals=_totals(ordered),
        derived=derived_efficiency_metrics(ordered),
        tool_gap_rates=_per_tool_rates(ordered),
        size_groups=_size_groups(ordered),
        groups=_group_by(ordered, group_by),
        diagnostics=tuple(diagnostics),
    )
