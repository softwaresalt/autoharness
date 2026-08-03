"""Telemetry metrics extraction + A/B delta adapter (085.004-T).

Reads benchmark epochs persisted by :mod:`autoharness.eval.benchmark.harness`
via the shipped, read-only :func:`~autoharness.telemetry.reader.
read_epoch_records`, correlates baseline/treatment arms per scenario via the
``benchmark:<scenario_id>:<repeat_index>:<arm>`` ``backlog_item_id`` convention,
slices each arm with :func:`~autoharness.telemetry.report.summarize_report`
(which computes economics totals through the shipped, quality-aware
:func:`~autoharness.telemetry.aggregation.aggregate_epochs`), and computes
per-scenario + aggregate A/B deltas for tokens / context / cost / latency and
routed-vs-raw / avoided-read / ``net_offload_tokens``.

**Deterministic delta-provenance rule** (mandatory invariant): a delta carries
the **least-certain** ``metric_quality`` across *all* operands — baseline,
treatment, and every repeat epoch in both arms. Any ``unavailable`` or
``not_applicable`` operand makes the whole delta ``unavailable`` (respectively
``not_applicable``) — **never** a false-precision ``observed``, and never a
numeric ``0``.

Deltas are always computed from **aggregate-total slices** (the sum of a field
across every repeat in an arm), never from averaging per-epoch ratios —
denominators are aggregate totals, matching the shipped aggregation contract.

Note on operations counters: :func:`autoharness.telemetry.aggregation._totals`
(via :func:`aggregate_epochs`) sums operations counters (``raw_file_read_count``,
``routed_lookup_count``, ...) **without** honoring ``metric_quality`` — that
helper is economics-focused. This module therefore computes its own
quality-aware totals for the routed-vs-raw operations fields directly from the
public per-record ``operations.metric_quality`` maps, so a degraded/unlabeled
operations counter cannot silently masquerade as an observed number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from autoharness.eval.benchmark.harness import BENCHMARK_NAMESPACE_PREFIX, Arm
from autoharness.telemetry.aggregation import UNAVAILABLE, derived_efficiency_metrics
from autoharness.telemetry.reader import TelemetryReadResult
from autoharness.telemetry.report import summarize_report

NOT_APPLICABLE = "not_applicable"

#: Least-certain-wins rank — mirrors autoharness.telemetry.report._QUALITY_RANK.
_QUALITY_RANK: Mapping[str, int] = {
    "observed": 0,
    "derived": 1,
    "estimated": 2,
    NOT_APPLICABLE: 3,
    UNAVAILABLE: 4,
}
_SENTINELS = (UNAVAILABLE, NOT_APPLICABLE)

ECONOMIC_DELTA_FIELDS: tuple[str, ...] = (
    "input_tokens",
    "output_tokens",
    "cogs_usd",
    "duration_seconds",
    "context_area_tokens",
    "avoided_read_estimated_tokens",
    "tool_output_estimated_tokens",
)
OPERATIONAL_DELTA_FIELDS: tuple[str, ...] = (
    "routed_lookup_count",
    "raw_file_read_count",
    "raw_search_count",
)
DERIVED_DELTA_FIELDS: tuple[str, ...] = ("net_offload_tokens",)

AGGREGATE_SCOPE = "__aggregate__"


class MetricsAdapterError(ValueError):
    """Raised when benchmark metrics extraction is given malformed input."""


def _record_field_quality(record: Mapping[str, Any], section: str, field_name: str) -> str:
    """Worst-case quality label for one field on one record.

    Value presence is checked *before* trusting any ``metric_quality`` label
    (review-fix): a field that is absent or the ``unavailable`` sentinel is
    ``unavailable`` regardless of what the quality map claims — an
    operational record such as
    ``{"operations": {"metric_quality": {"raw_search_count": "estimated"}}}``
    with no ``raw_search_count`` key at all must not be reported as an
    "estimated" zero (that would produce an estimated total of zero for a
    value that was never recorded, violating the unavailable-not-zero
    invariant). Only once the value is confirmed present does an explicit,
    recognized ``metric_quality`` label get trusted verbatim. A field whose
    numeric value is exactly zero and has no label is treated as ``observed``
    (a zero-count is a legitimate observation, not a provenance gap — mirrors
    the shipped ``_metric_is_populated`` contract). Any other
    populated-but-unlabeled value is a genuine provenance gap and degrades to
    ``unavailable`` rather than defaulting to false precision.
    """
    section_data = record.get(section) or {}
    value = section_data.get(field_name)
    if value is None or value == UNAVAILABLE:
        return UNAVAILABLE
    quality_map = section_data.get("metric_quality")
    label = quality_map.get(field_name) if isinstance(quality_map, Mapping) else None
    if isinstance(label, str) and label in _QUALITY_RANK:
        return label
    if isinstance(value, (int, float)) and value == 0:
        return "observed"
    return UNAVAILABLE


def _worst_quality(records: Iterable[Mapping[str, Any]], section: str, field_name: str) -> str:
    """Least-certain-wins quality across ``records``.

    An **empty** record set carries no data at all — the field is
    ``unavailable``, not the false-precision ``observed`` a naive "start
    optimistic, degrade on evidence" fold would otherwise return (H1: missing
    data is never rendered as an observed zero).
    """
    records_tuple = tuple(records)
    if not records_tuple:
        return UNAVAILABLE
    worst = "observed"
    for record in records_tuple:
        label = _record_field_quality(record, section, field_name)
        if _QUALITY_RANK[label] > _QUALITY_RANK[worst]:
            worst = label
    return worst


def _combine_quality(*labels: str) -> str:
    """Least-certain-wins across every supplied quality label."""
    combined = "observed"
    for label in labels:
        normalized = label if label in _QUALITY_RANK else UNAVAILABLE
        if _QUALITY_RANK[normalized] > _QUALITY_RANK[combined]:
            combined = normalized
    return combined


def scenario_arm_records(
    records: Iterable[Mapping[str, Any]],
    scenario_id: str,
    arm: Arm,
) -> tuple[dict[str, Any], ...]:
    """Filter benchmark epoch records to one scenario's one arm.

    Correlates via the ``benchmark:<scenario_id>:<repeat_index>:<arm>``
    ``backlog_item_id`` convention (:mod:`autoharness.eval.benchmark.harness`).

    Matching parses the exact ``<scenario_id>`` segment rather than using a
    naive prefix/suffix ``str.startswith``/``str.endswith`` check
    (review-fix): a colon-delimited scenario id that is itself a prefix of
    another scenario id — e.g. ``a`` and ``a:b`` — would otherwise conflate
    the two, since ``benchmark:a:b:0:baseline`` both starts with
    ``benchmark:a:`` and ends with ``:baseline``, double-counting the ``a:b``
    epochs into the ``a`` slice's aggregate. The repeat-index segment (the
    last colon-delimited token before the arm) is parsed off first and must
    be all-digits; everything remaining must equal ``scenario_id`` exactly.
    """
    prefix = BENCHMARK_NAMESPACE_PREFIX
    suffix = f":{arm}"
    matched: list[dict[str, Any]] = []
    for record in records:
        backlog_item_id = str(record.get("backlog_item_id", ""))
        if not backlog_item_id.startswith(prefix) or not backlog_item_id.endswith(suffix):
            continue
        middle = backlog_item_id[len(prefix) : -len(suffix)]
        candidate_scenario_id, sep, repeat_part = middle.rpartition(":")
        if not sep or not repeat_part.isdigit() or candidate_scenario_id != scenario_id:
            continue
        matched.append(dict(record))
    return tuple(matched)


@dataclass(frozen=True)
class FieldDelta:
    """The A/B delta for a single field within one scope (scenario or aggregate)."""

    field: str
    baseline_total: float | int | str
    treatment_total: float | int | str
    delta: float | int | str
    quality: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "baseline_total": self.baseline_total,
            "treatment_total": self.treatment_total,
            "delta": self.delta,
            "quality": self.quality,
        }


@dataclass(frozen=True)
class ScopeDelta:
    """A/B deltas for every tracked field within one scope."""

    scope: str
    baseline_repeat_count: int
    treatment_repeat_count: int
    fields: Mapping[str, FieldDelta] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "baseline_repeat_count": self.baseline_repeat_count,
            "treatment_repeat_count": self.treatment_repeat_count,
            "fields": {name: delta.to_dict() for name, delta in self.fields.items()},
        }


def _economic_total(records: tuple[dict[str, Any], ...], field_name: str) -> float | int | str:
    if not records:
        return UNAVAILABLE
    summary = summarize_report(TelemetryReadResult(status="ok", records=records), filters=None)
    return summary.totals.get(field_name, UNAVAILABLE)


def _operational_total(records: tuple[dict[str, Any], ...], field_name: str) -> int | str:
    quality = _worst_quality(records, "operations", field_name)
    if quality in _SENTINELS:
        return quality
    return sum(int((record.get("operations") or {}).get(field_name) or 0) for record in records)


def _field_delta(
    baseline_records: tuple[dict[str, Any], ...],
    treatment_records: tuple[dict[str, Any], ...],
    field_name: str,
    *,
    section: str,
) -> FieldDelta:
    quality = _combine_quality(
        _worst_quality(baseline_records, section, field_name),
        _worst_quality(treatment_records, section, field_name),
    )
    if section == "economics":
        baseline_total = _economic_total(baseline_records, field_name)
        treatment_total = _economic_total(treatment_records, field_name)
    else:
        baseline_total = _operational_total(baseline_records, field_name)
        treatment_total = _operational_total(treatment_records, field_name)

    resolved = _resolve_sentinel(quality, baseline_total, treatment_total)
    if resolved is not None:
        return FieldDelta(
            field=field_name,
            baseline_total=baseline_total,
            treatment_total=treatment_total,
            delta=resolved,
            quality=resolved,
        )

    delta_value = treatment_total - baseline_total
    return FieldDelta(
        field=field_name,
        baseline_total=baseline_total,
        treatment_total=treatment_total,
        delta=delta_value,
        quality=quality,
    )


def _resolve_sentinel(
    quality: str,
    baseline_total: float | int | str,
    treatment_total: float | int | str,
) -> str | None:
    """Decide the sentinel label to emit, or ``None`` when a numeric delta is safe.

    ``quality`` — computed directly from the per-record ``metric_quality``
    labels via :func:`_combine_quality` — is the **authoritative** signal for
    *which* sentinel (``unavailable`` vs ``not_applicable``) to emit, because
    the shipped :func:`~autoharness.telemetry.aggregation.aggregate_epochs`
    totals collapse both cases to the single generic ``UNAVAILABLE`` string
    (it does not preserve the ``not_applicable`` distinction). A totals value
    that is unexpectedly a sentinel string while ``quality`` itself claims a
    non-sentinel label is a genuine inconsistency — fail closed to
    ``unavailable`` rather than trust a possibly-mismatched numeric.
    """
    if quality in _SENTINELS:
        return quality
    if isinstance(baseline_total, str) or isinstance(treatment_total, str):
        return UNAVAILABLE
    return None


def _net_offload_delta(
    baseline_records: tuple[dict[str, Any], ...],
    treatment_records: tuple[dict[str, Any], ...],
) -> FieldDelta:
    operand_fields = ("avoided_read_estimated_tokens", "tool_output_estimated_tokens")
    quality = _combine_quality(
        *(_worst_quality(baseline_records, "economics", f) for f in operand_fields),
        *(_worst_quality(treatment_records, "economics", f) for f in operand_fields),
    )
    baseline_net = derived_efficiency_metrics(baseline_records)["net_offload_tokens"] if baseline_records else UNAVAILABLE
    treatment_net = derived_efficiency_metrics(treatment_records)["net_offload_tokens"] if treatment_records else UNAVAILABLE

    resolved = _resolve_sentinel(quality, baseline_net, treatment_net)
    if resolved is not None:
        return FieldDelta(
            field="net_offload_tokens",
            baseline_total=baseline_net,
            treatment_total=treatment_net,
            delta=resolved,
            quality=resolved,
        )

    return FieldDelta(
        field="net_offload_tokens",
        baseline_total=baseline_net,
        treatment_total=treatment_net,
        delta=treatment_net - baseline_net,
        quality=quality,
    )


def compute_scope_delta(
    baseline_records: tuple[dict[str, Any], ...],
    treatment_records: tuple[dict[str, Any], ...],
    *,
    scope: str,
) -> ScopeDelta:
    """Compute every tracked field's A/B delta for one scope's record slices."""
    fields: dict[str, FieldDelta] = {}
    for name in ECONOMIC_DELTA_FIELDS:
        fields[name] = _field_delta(baseline_records, treatment_records, name, section="economics")
    for name in OPERATIONAL_DELTA_FIELDS:
        fields[name] = _field_delta(baseline_records, treatment_records, name, section="operations")
    fields["net_offload_tokens"] = _net_offload_delta(baseline_records, treatment_records)
    return ScopeDelta(
        scope=scope,
        baseline_repeat_count=len(baseline_records),
        treatment_repeat_count=len(treatment_records),
        fields=fields,
    )


def compute_scenario_delta(
    records: Iterable[Mapping[str, Any]],
    scenario_id: str,
) -> ScopeDelta:
    """Compute one scenario's baseline-vs-treatment A/B delta from a record pool."""
    records_tuple = tuple(records)
    baseline = scenario_arm_records(records_tuple, scenario_id, "baseline")
    treatment = scenario_arm_records(records_tuple, scenario_id, "treatment")
    return compute_scope_delta(baseline, treatment, scope=scenario_id)


def compute_corpus_deltas(
    read_result: TelemetryReadResult,
    scenario_ids: Iterable[str],
) -> dict[str, ScopeDelta]:
    """Per-scenario A/B deltas, keyed by scenario id."""
    records = read_result.records
    return {scenario_id: compute_scenario_delta(records, scenario_id) for scenario_id in scenario_ids}


def compute_aggregate_delta(
    read_result: TelemetryReadResult,
    scenario_ids: Iterable[str],
) -> ScopeDelta:
    """The whole-corpus aggregate A/B delta.

    Computed from the **combined aggregate-total** record pool across every
    scenario (never by averaging the per-scenario deltas above) — denominators
    stay aggregate totals per the shipped aggregation contract.
    """
    records = read_result.records
    all_baseline: list[dict[str, Any]] = []
    all_treatment: list[dict[str, Any]] = []
    for scenario_id in scenario_ids:
        all_baseline.extend(scenario_arm_records(records, scenario_id, "baseline"))
        all_treatment.extend(scenario_arm_records(records, scenario_id, "treatment"))
    return compute_scope_delta(tuple(all_baseline), tuple(all_treatment), scope=AGGREGATE_SCOPE)
