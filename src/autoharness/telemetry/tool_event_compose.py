"""Deterministic event-to-epoch composer (U4, 084.004-T).

Pure functions that take a set of deduplicated :class:`ToolTelemetryEvent`
records plus a correlation context (an ``epoch_id``/``backlog_item_id`` pair, or
the frozen begin-context payload produced by
:mod:`autoharness.telemetry.context`) and derive composer-owned patches for the
four :mod:`autoharness.telemetry.epoch` payload sections: :class:`RouteConfiguration`,
:class:`EconomicPayload`, :class:`OperationalReality`, and :class:`AbsoluteOutcome`.

This module performs no I/O — it is a pure roll-up over an in-memory event list.
The record-path integration (loading the journal, selecting events, merging the
patch into a closing epoch) is U5's job (``record.py``).

Composition rules (docs/plans/2026-07-31-token-efficiency-telemetry-emission-plan.md):

* Correlation selection mirrors ``tool_event_jsonl.read_events``: an event
  carrying an ``epoch_id`` is only ever selected by an exact ``epoch_id`` match;
  the ``backlog_item_id`` fallback applies only to events with no ``epoch_id`` at
  all (decision 5). Non-correlated candidates are ignored, never attached to the
  wrong epoch.
* Token/byte/count deltas are summed across selected events; cumulative running
  totals (``cumulative_input_tokens``/``cumulative_output_tokens``) use the
  maximum observed value (the final running total), never a sum.
  ``context_tokens_before`` uses the minimum observed snapshot (the earliest);
  ``context_tokens_after`` uses the maximum (the latest) (decision 2, §R2).
* Route kinds and tool/tool-surface/retrieval-pack sets are aggregated as sorted
  unique values, which is inherently independent of event arrival order.
* An event's ``expected_tool`` records one explicit expected opportunity
  (decision 7). Satisfaction uses explicit event links (``## Review Fixes``
  item 2, a ratified P1 fix): a direct invocation event whose own
  ``expected_tool`` equals its own ``tool_name`` counts one expected and one
  observed opportunity in the same event. A separate, standalone expectation
  event is identified by its ``event_id``; a later invocation or retry
  satisfies it only when that invocation's ``parent_event_id`` equals the
  expectation event's ``event_id`` and its ``tool_name`` equals the
  expectation's ``expected_tool``. Multiple retries under one expectation count
  one expected opportunity and at most one observed opportunity — unlinked
  events never satisfy an expectation. Missing counts are clamped at zero and
  never go negative. Failed and degraded invocations are counted separately
  from "missing" — a failed or degraded invocation of an expected tool still
  satisfies the expectation.
* Populated (nonzero) composer-derived economics metrics carry
  ``metric_sources``/``metric_quality`` entries; the source is always
  ``"derived"`` (the epoch-level value is an aggregate over per-tool events, not
  a single host report) and the quality is the worst (least-trusted) quality
  label reported by any contributing event for that same metric name, applying
  the 095-S additive-provenance convention (docs/compound/095-S-derived-metric-provenance-additive-map.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Sequence

from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
)
from autoharness.telemetry.gaps import summarize_tool_gaps
from autoharness.telemetry.tool_event import ToolTelemetryEvent, event_correlates

# The composer-owned attribute names within each epoch payload section. U5 uses
# these lists to merge only these attributes from the pure patch onto the
# close-supplied payload objects (every other attribute stays close-payload
# owned) and to detect "hybrid" input: a close payload that already supplies a
# nonzero/non-empty value for one of these fields while composition is
# requested must fail closed rather than silently pick one side (decision 6).
ROUTE_COMPOSER_FIELDS: tuple[str, ...] = ("route_kinds",)

ECONOMICS_COMPOSER_FIELDS: tuple[str, ...] = (
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "cumulative_input_tokens",
    "cumulative_output_tokens",
    "context_tokens_before",
    "context_tokens_after",
    "context_area_tokens",
    "avoided_read_estimated_tokens",
    "tool_output_estimated_tokens",
)

OPERATIONS_COMPOSER_FIELDS: tuple[str, ...] = (
    "cli_tools",
    "tool_surfaces",
    "retrieval_packs",
    "route_kind_counts",
    "routed_lookup_count",
    "raw_file_read_count",
    "raw_search_count",
    "avoided_file_read_count",
    "tool_output_bytes",
    "expected_tool_count",
    "observed_expected_tool_count",
    "missing_expected_tool_count",
    "expected_tool_counts",
    "observed_tool_counts",
    "missing_expected_tool_counts",
    "degraded_tool_count",
    "stale_or_unavailable_index_count",
)

OUTCOME_COMPOSER_FIELDS: tuple[str, ...] = (
    "tool_failure_count",
    "tool_degraded_count",
    "tool_gap_count",
)


class ToolEventCompositionError(ValueError):
    """Raised when tool-event composition would be unsafe: today, only the
    decision-6 hybrid refusal (a close payload already supplies a nonzero/
    non-empty value for a composer-owned field while composition is requested).
    This is a fail-CLOSED validation error — unlike composition I/O failures
    (missing/unreadable journal), which fail OPEN and leave the close payload
    unmerged, a hybrid payload must never be silently resolved by picking one
    side, so the caller (record.py, then the CLI) must reject it outright.
    """

# gate_exit_codes, cogs_usd, and duration_seconds are explicitly close-payload
# owned (decision 6) and never appear in the lists above.

# Worst-quality ranking, mirroring aggregation.py's _QUALITY_RANK so a single
# metric's provenance degrades to the least-trusted label contributed by any
# selected event, rather than silently picking an arbitrary one.
_QUALITY_RANK: Mapping[str, int] = {
    "observed": 0,
    "derived": 1,
    "estimated": 2,
    "not_applicable": 3,
    "unavailable": 4,
}


def _normalize_quality(value: Any) -> str:
    """Coerce a raw per-event ``metric_quality`` label to the known vocabulary.

    A missing label defaults to the optimistic ``"observed"`` (mirrors
    ``aggregation._normalize_quality``); any present-but-invalid label degrades
    fail-closed to ``"unavailable"`` rather than crashing the ranking lookup.
    """
    if value is None:
        return "observed"
    if isinstance(value, str) and value in _QUALITY_RANK:
        return value
    return "unavailable"


def _worst_quality(qualities: Sequence[Any]) -> str:
    ranked = [_normalize_quality(quality) for quality in qualities]
    if not ranked:
        return "observed"
    return max(ranked, key=lambda quality: _QUALITY_RANK[quality])


@dataclass(frozen=True)
class ToolEventComposition:
    """Pure composer output: composer-owned patches for the four epoch payload
    sections, plus diagnostics describing the correlated event selection."""

    route: RouteConfiguration
    economics: EconomicPayload
    operations: OperationalReality
    outcome: AbsoluteOutcome
    selected_event_count: int = 0
    ignored_event_count: int = 0
    diagnostics: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route.to_dict(),
            "economics": self.economics.to_dict(),
            "operations": self.operations.to_dict(),
            "outcome": self.outcome.to_dict(),
            "selected_event_count": self.selected_event_count,
            "ignored_event_count": self.ignored_event_count,
            "diagnostics": list(self.diagnostics),
        }


def _select_correlated(
    events: Sequence[ToolTelemetryEvent],
    *,
    epoch_id: str | None,
    backlog_item_id: str | None,
) -> tuple[list[ToolTelemetryEvent], int]:
    selected = [
        event
        for event in events
        if event_correlates(event, epoch_id=epoch_id, backlog_item_id=backlog_item_id)
    ]
    return selected, len(events) - len(selected)


def _sum_metric(events: Sequence[ToolTelemetryEvent], name: str) -> int:
    return sum(int(getattr(event, name)) for event in events if getattr(event, name) is not None)


def _min_metric(events: Sequence[ToolTelemetryEvent], name: str) -> int:
    values = [int(getattr(event, name)) for event in events if getattr(event, name) is not None]
    return min(values) if values else 0


def _max_metric(events: Sequence[ToolTelemetryEvent], name: str) -> int:
    values = [int(getattr(event, name)) for event in events if getattr(event, name) is not None]
    return max(values) if values else 0


def _metric_quality_for(events: Sequence[ToolTelemetryEvent], name: str) -> str:
    contributing = [event for event in events if getattr(event, name) is not None]
    return _worst_quality([event.metric_quality.get(name) for event in contributing])


def _compose_route(events: Sequence[ToolTelemetryEvent]) -> RouteConfiguration:
    route_kinds = tuple(sorted({event.route_kind for event in events if event.route_kind is not None}))
    return RouteConfiguration(models=(), route_kinds=route_kinds)


def _compose_economics(events: Sequence[ToolTelemetryEvent]) -> EconomicPayload:
    values: dict[str, int] = {
        name: _sum_metric(events, name)
        for name in (
            "input_tokens",
            "output_tokens",
            "cached_input_tokens",
            "context_area_tokens",
            "avoided_read_estimated_tokens",
            "tool_output_estimated_tokens",
        )
    }
    values["cumulative_input_tokens"] = _max_metric(events, "cumulative_input_tokens")
    values["cumulative_output_tokens"] = _max_metric(events, "cumulative_output_tokens")
    values["context_tokens_before"] = _min_metric(events, "context_tokens_before")
    values["context_tokens_after"] = _max_metric(events, "context_tokens_after")

    sources: dict[str, str] = {}
    quality: dict[str, str] = {}
    for name in ECONOMICS_COMPOSER_FIELDS:
        if values.get(name, 0):
            sources[name] = "derived"
            quality[name] = _metric_quality_for(events, name)

    return EconomicPayload(
        input_tokens=values["input_tokens"],
        output_tokens=values["output_tokens"],
        cached_input_tokens=values["cached_input_tokens"],
        cumulative_input_tokens=values["cumulative_input_tokens"],
        cumulative_output_tokens=values["cumulative_output_tokens"],
        context_tokens_before=values["context_tokens_before"],
        context_tokens_after=values["context_tokens_after"],
        context_area_tokens=values["context_area_tokens"],
        avoided_read_estimated_tokens=values["avoided_read_estimated_tokens"],
        tool_output_estimated_tokens=values["tool_output_estimated_tokens"],
        metric_sources=sources,
        metric_quality=quality,
    )


def _expected_observed_tool_counts(
    events: Sequence[ToolTelemetryEvent],
) -> tuple[dict[str, int], dict[str, int]]:
    """Per-tool expected/observed counts using explicit ``parent_event_id`` linkage.

    Ratified accounting (plan ``## Review Fixes`` item 2 — a P1 fix that gated
    the plan's PASS verdict; a flat, unlinked tool-name match was explicitly
    rejected):

    * A direct invocation event (not :attr:`ToolTelemetryEvent.is_expectation_only`)
      whose own ``expected_tool`` equals its own ``tool_name`` counts one
      expected AND one observed opportunity for that tool, in the same event.
    * A standalone expectation-only event (``operation == "expect"``,
      ``status == "skipped"``) with ``expected_tool`` set counts one expected
      opportunity. It is satisfied — at most one observed opportunity — only by
      a later invocation event whose ``parent_event_id`` equals that
      expectation event's ``event_id`` and whose ``tool_name`` equals the
      expectation's ``expected_tool``. Multiple retries linked to the same
      expectation event (same ``parent_event_id``) count one expected
      opportunity and at most one observed opportunity — never per-retry.
    * Unlinked events — an invocation with no ``parent_event_id``, or a
      ``parent_event_id`` that does not resolve to an expectation-only event in
      this correlated set — never satisfy an expectation. They may still
      contribute to ``expected_tool_counts`` if they independently declare an
      unrelated ``expected_tool``, but never inflate ``observed_tool_counts``
      for an expectation they are not linked to.
    """
    expected_tool_counts: dict[str, int] = {}
    observed_tool_counts: dict[str, int] = {}

    expectations_by_id: dict[str, ToolTelemetryEvent] = {
        event.event_id: event
        for event in events
        if event.is_expectation_only and event.expected_tool is not None
    }
    satisfied_expectation_ids: set[str] = set()

    for event in events:
        if event.is_expectation_only:
            if event.expected_tool is not None:
                expected_tool_counts[event.expected_tool] = (
                    expected_tool_counts.get(event.expected_tool, 0) + 1
                )
            continue

        # A real invocation event (never expectation-only).
        if event.expected_tool is not None and event.expected_tool == event.tool_name:
            # Self-declared: the same event is both the expectation and its
            # own satisfying invocation.
            expected_tool_counts[event.expected_tool] = (
                expected_tool_counts.get(event.expected_tool, 0) + 1
            )
            observed_tool_counts[event.tool_name] = observed_tool_counts.get(event.tool_name, 0) + 1
            continue

        if event.expected_tool is not None:
            # Declares an expectation unrelated to its own tool_name; counts
            # as an expected opportunity but never self-satisfies.
            expected_tool_counts[event.expected_tool] = (
                expected_tool_counts.get(event.expected_tool, 0) + 1
            )

        if event.parent_event_id is not None:
            expectation = expectations_by_id.get(event.parent_event_id)
            if (
                expectation is not None
                and expectation.expected_tool == event.tool_name
                and expectation.event_id not in satisfied_expectation_ids
            ):
                observed_tool_counts[event.tool_name] = (
                    observed_tool_counts.get(event.tool_name, 0) + 1
                )
                satisfied_expectation_ids.add(expectation.event_id)
        # else: unlinked invocation — never satisfies any expectation here.

    return expected_tool_counts, observed_tool_counts


def _compose_operations_and_outcome(
    events: Sequence[ToolTelemetryEvent],
) -> tuple[OperationalReality, AbsoluteOutcome]:
    invocation_events = [event for event in events if not event.is_expectation_only]
    expected_tool_counts, observed_tool_counts = _expected_observed_tool_counts(events)

    route_kind_counts: dict[str, int] = {}
    for event in events:
        if event.route_kind is not None:
            route_kind_counts[event.route_kind] = route_kind_counts.get(event.route_kind, 0) + 1

    # Failed and degraded invocations are counted separately from "missing" —
    # a failed or degraded invocation of an expected tool still satisfies that
    # expectation (it is present in invocation_pairs above), never conflated
    # with a tool that was never invoked at all.
    failed_count = sum(1 for event in invocation_events if event.status == "failed")
    degraded_count = sum(1 for event in invocation_events if event.status == "degraded")
    stale_count = sum(
        1 for event in invocation_events if event.freshness_state in ("stale", "unavailable")
    )

    gap_summary = summarize_tool_gaps(
        expected_tool_counts=expected_tool_counts,
        observed_tool_counts=observed_tool_counts,
        route_kind_counts=route_kind_counts,
        raw_file_read_count=_sum_metric(events, "raw_file_read_count"),
        raw_search_count=_sum_metric(events, "raw_search_count"),
        routed_lookup_count=_sum_metric(events, "routed_lookup_count"),
        avoided_file_read_count=_sum_metric(events, "avoided_file_read_count"),
        tool_output_bytes=_sum_metric(events, "tool_output_bytes"),
        degraded_tool_count=degraded_count,
        stale_or_unavailable_index_count=stale_count,
    )

    cli_tools = tuple(sorted({event.tool_name for event in invocation_events}))
    tool_surfaces = tuple(sorted({event.tool_surface for event in invocation_events}))
    retrieval_packs = tuple(
        sorted({event.retrieval_pack for event in events if event.retrieval_pack is not None})
    )
    # cli_tools/tool_surfaces/retrieval_packs are plain aggregated tuples, not
    # part of epoch.py's _OPERATIONAL_METRICS provenance-required set, so no
    # metric_sources/metric_quality entries are needed for them.
    operations = replace(
        gap_summary.operations,
        cli_tools=cli_tools,
        tool_surfaces=tool_surfaces,
        retrieval_packs=retrieval_packs,
    )

    outcome_sources = dict(gap_summary.outcome.metric_sources)
    outcome_quality = dict(gap_summary.outcome.metric_quality)
    outcome_sources["tool_failure_count"] = "derived"
    outcome_quality["tool_failure_count"] = "derived"
    outcome_sources["tool_degraded_count"] = "derived"
    outcome_quality["tool_degraded_count"] = "derived"
    outcome = replace(
        gap_summary.outcome,
        tool_failure_count=failed_count,
        tool_degraded_count=degraded_count,
        metric_sources=outcome_sources,
        metric_quality=outcome_quality,
    )

    return operations, outcome


def compose_tool_events(
    events: Sequence[ToolTelemetryEvent],
    *,
    epoch_id: str | None = None,
    backlog_item_id: str | None = None,
) -> ToolEventComposition:
    """Pure roll-up: select correlated events, then derive composer-owned
    route/economics/operations/outcome patches from them.

    ``events`` may include events that do not correlate to the requested
    ``epoch_id``/``backlog_item_id`` (e.g. a raw journal scan); those are
    counted in ``ignored_event_count`` and excluded from every computed patch,
    never attached to the wrong epoch (decision 5).
    """
    selected, ignored = _select_correlated(events, epoch_id=epoch_id, backlog_item_id=backlog_item_id)
    diagnostics: list[str] = []
    if ignored:
        diagnostics.append(
            f"{ignored} candidate event(s) ignored: no exact epoch_id/backlog_item_id correlation"
        )

    route = _compose_route(selected)
    economics = _compose_economics(selected)
    operations, outcome = _compose_operations_and_outcome(selected)

    return ToolEventComposition(
        route=route,
        economics=economics,
        operations=operations,
        outcome=outcome,
        selected_event_count=len(selected),
        ignored_event_count=ignored,
        diagnostics=tuple(diagnostics),
    )


def compose_from_context(
    events: Sequence[ToolTelemetryEvent], context: Mapping[str, Any]
) -> ToolEventComposition:
    """Convenience wrapper over :func:`compose_tool_events` accepting a frozen
    begin-context payload (as produced by
    :mod:`autoharness.telemetry.context.begin_context` / loaded via
    ``load_context_ref``) instead of bare correlation ids."""
    epoch_id = context.get("epoch_id")
    backlog_item_id = context.get("backlog_item_id")
    return compose_tool_events(
        events,
        epoch_id=str(epoch_id) if epoch_id is not None else None,
        backlog_item_id=str(backlog_item_id) if backlog_item_id is not None else None,
    )


def _is_populated(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set, frozenset)):
        return bool(value)
    if isinstance(value, (int, float)):
        return bool(value)
    return value is not None


def detect_hybrid_fields(epoch: ExecutionEpoch) -> tuple[str, ...]:
    """Return every composer-owned field the close-supplied ``epoch`` already
    populates with a nonzero/non-empty value.

    U5 (``record.py``) calls this before composing: a non-empty result while
    composition is requested is the decision-6 hybrid case and must fail
    closed rather than silently pick either the close payload's value or the
    composer's derived value.
    """
    hybrid: list[str] = []
    for name in ROUTE_COMPOSER_FIELDS:
        if _is_populated(getattr(epoch.route, name)):
            hybrid.append(f"route.{name}")
    for name in ECONOMICS_COMPOSER_FIELDS:
        if _is_populated(getattr(epoch.economics, name)):
            hybrid.append(f"economics.{name}")
    for name in OPERATIONS_COMPOSER_FIELDS:
        if _is_populated(getattr(epoch.operations, name)):
            hybrid.append(f"operations.{name}")
    for name in OUTCOME_COMPOSER_FIELDS:
        if _is_populated(getattr(epoch.outcome, name)):
            hybrid.append(f"outcome.{name}")
    return tuple(hybrid)


def apply_composition_patch(epoch: ExecutionEpoch, composition: ToolEventComposition) -> ExecutionEpoch:
    """Merge a :class:`ToolEventComposition` patch onto ``epoch``.

    Only the composer-owned attributes (the ``*_COMPOSER_FIELDS`` name lists)
    are replaced; every other field — including the close-payload-owned
    ``gate_exit_codes``, ``cogs_usd``, and ``duration_seconds`` (decision 6),
    plus every root-level identity/correlation field — is preserved verbatim.
    Provenance maps are merged by overlay: the patch only ever populates
    composer-owned metric names, so overlaying it onto the (expected-empty)
    existing map cannot clobber a close-owned metric's provenance entry.
    """
    route = replace(epoch.route, route_kinds=composition.route.route_kinds)
    economics = replace(
        epoch.economics,
        **{name: getattr(composition.economics, name) for name in ECONOMICS_COMPOSER_FIELDS},
        metric_sources={**epoch.economics.metric_sources, **composition.economics.metric_sources},
        metric_quality={**epoch.economics.metric_quality, **composition.economics.metric_quality},
    )
    operations = replace(
        epoch.operations,
        **{name: getattr(composition.operations, name) for name in OPERATIONS_COMPOSER_FIELDS},
        metric_sources={**epoch.operations.metric_sources, **composition.operations.metric_sources},
        metric_quality={**epoch.operations.metric_quality, **composition.operations.metric_quality},
    )
    outcome = replace(
        epoch.outcome,
        **{name: getattr(composition.outcome, name) for name in OUTCOME_COMPOSER_FIELDS},
        metric_sources={**epoch.outcome.metric_sources, **composition.outcome.metric_sources},
        metric_quality={**epoch.outcome.metric_quality, **composition.outcome.metric_quality},
    )
    return replace(epoch, route=route, economics=economics, operations=operations, outcome=outcome)
