"""Execution Epoch model — the four design-§4 payload classes.

An :class:`ExecutionEpoch` is the immutable, structured record the harness
runtime hands to ``autoharness telemetry record`` at task-completion time. It
composes the four payload classes named in the design doc:

* :class:`RouteConfiguration` — models used (route configuration)
* :class:`EconomicPayload` — tokens, COGS, duration
* :class:`OperationalReality` — CLI tools used
* :class:`AbsoluteOutcome` — gate exit codes

The serialized shape produced by :meth:`ExecutionEpoch.to_record` is the stable
contract shared by both sinks (SQLite + JSONL) and the external ingestion
boundary (agent-engram). ``from_mapping`` reverses it losslessly.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "1.1.0"

# Names of every EconomicPayload numeric metric that requires provenance when
# populated (non-zero). A ``0`` default is treated as "not observed" and needs
# no provenance entry.
_ECONOMIC_METRICS: tuple[str, ...] = (
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
    "cogs_usd",
    "duration_seconds",
)

_OPERATIONAL_METRICS: tuple[str, ...] = (
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

_OUTCOME_METRICS: tuple[str, ...] = (
    "tool_failure_count",
    "tool_degraded_count",
    "tool_gap_count",
)

# Ordinal planned-size labels. There are no numeric points and no implicit
# label-to-weight mapping.
_SIZE_LABELS = frozenset({"XS", "S", "M", "L", "XL"})

# Allowed size-histogram buckets. Known members with no resolvable size label
# fall in ``unsized``; there is intentionally no ``unavailable`` bucket, and
# skipped/unresolved IDs are excluded from the count and histogram entirely.
_HISTOGRAM_KEYS = frozenset({"XS", "S", "M", "L", "XL", "unsized"})


class EpochError(ValueError):
    """Raised when an epoch payload is malformed or a required class is missing."""


def _as_tuple(value: Any, field: str) -> tuple:
    """Coerce a JSON array into a tuple, rejecting strings/bytes and non-arrays.

    A bare string is iterable, so ``tuple("abc")`` would silently yield
    ``('a', 'b', 'c')``. Reject that so a malformed shape (e.g. ``models`` given
    as a string) becomes a controlled :class:`EpochError` rather than nonsense
    telemetry that still exits 0.
    """
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise TypeError(f"'{field}' must be a JSON array, got {type(value).__name__}")
    return tuple(value)


def _metric_is_populated(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set, frozenset)):
        return bool(value)
    if isinstance(value, (int, float)):
        return bool(value)
    return value is not None


def _missing_metric_provenance(owner: Any, metric_names: tuple[str, ...]) -> tuple[str, ...]:
    sources = getattr(owner, "metric_sources", {})
    quality = getattr(owner, "metric_quality", {})
    return tuple(
        name
        for name in metric_names
        if _metric_is_populated(getattr(owner, name))
        and (name not in sources or name not in quality)
    )


@dataclass(frozen=True)
class RouteConfiguration:
    """Route configuration — the models used during the epoch."""

    models: tuple[str, ...] = ()
    route_kinds: tuple[str, ...] = ()

    @property
    def primary_model(self) -> str | None:
        return self.models[0] if self.models else None

    @property
    def primary_route_kind(self) -> str | None:
        return self.route_kinds[0] if self.route_kinds else None

    def to_dict(self) -> dict[str, Any]:
        return {"models": list(self.models), "route_kinds": list(self.route_kinds)}

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RouteConfiguration":
        return cls(
            models=_as_tuple(data.get("models"), "route.models"),
            route_kinds=_as_tuple(data.get("route_kinds"), "route.route_kinds"),
        )


@dataclass(frozen=True)
class EconomicPayload:
    """Economic payload — tokens, cost of goods sold, and wall-clock duration.

    v1.1 adds consumption/generation token separation, cumulative running
    totals, context-area estimates, tool-offload token estimates, and per-metric
    provenance maps (``metric_sources`` / ``metric_quality``). Cumulative totals
    are final epoch-close values preserved verbatim on round-trip; they are never
    re-derived from per-turn tokens.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cogs_usd: float = 0.0
    duration_seconds: float = 0.0
    cached_input_tokens: int = 0
    cumulative_input_tokens: int = 0
    cumulative_output_tokens: int = 0
    context_tokens_before: int = 0
    context_tokens_after: int = 0
    context_area_tokens: int = 0
    avoided_read_estimated_tokens: int = 0
    tool_output_estimated_tokens: int = 0
    metric_sources: Mapping[str, str] = field(default_factory=dict)
    metric_quality: Mapping[str, str] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def missing_provenance(self) -> tuple[str, ...]:
        """Return populated metrics lacking a same-named entry in BOTH maps.

        A metric is "populated" when its value is non-zero. Zero-valued metrics
        are treated as unobserved and require no provenance entry.
        """
        return _missing_metric_provenance(self, _ECONOMIC_METRICS)

    @property
    def has_complete_provenance(self) -> bool:
        return not self.missing_provenance()

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cogs_usd": self.cogs_usd,
            "duration_seconds": self.duration_seconds,
            "cached_input_tokens": self.cached_input_tokens,
            "cumulative_input_tokens": self.cumulative_input_tokens,
            "cumulative_output_tokens": self.cumulative_output_tokens,
            "context_tokens_before": self.context_tokens_before,
            "context_tokens_after": self.context_tokens_after,
            "context_area_tokens": self.context_area_tokens,
            "avoided_read_estimated_tokens": self.avoided_read_estimated_tokens,
            "tool_output_estimated_tokens": self.tool_output_estimated_tokens,
            "metric_sources": dict(self.metric_sources),
            "metric_quality": dict(self.metric_quality),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any], *, legacy: bool = False) -> "EconomicPayload":
        sources = dict(data.get("metric_sources") or {})
        quality = dict(data.get("metric_quality") or {})
        if legacy:
            # v1.0 records carried no provenance, so no metric can be established
            # as observed; mark every economic metric ``unavailable`` while
            # retaining the numeric values.
            for name in _ECONOMIC_METRICS:
                sources.setdefault(name, "unavailable")
                quality.setdefault(name, "unavailable")

        def _metric(name: str, caster: Any, default: Any) -> Any:
            # Copilot review c4: the schema declares every economics metric
            # ``anyOf integer|null``. An explicit null means the value is
            # unavailable (distinct from an observed zero per the telemetry-reference
            # contract), so coerce it to a zero placeholder and mark it unavailable
            # via provenance instead of crashing on ``int(None)`` / ``float(None)``,
            # mirroring the legacy normalization above.
            raw = data.get(name, default)
            if raw is None:
                sources.setdefault(name, "unavailable")
                quality.setdefault(name, "unavailable")
                return default
            return caster(raw)

        return cls(
            input_tokens=_metric("input_tokens", int, 0),
            output_tokens=_metric("output_tokens", int, 0),
            cogs_usd=_metric("cogs_usd", float, 0.0),
            duration_seconds=_metric("duration_seconds", float, 0.0),
            cached_input_tokens=_metric("cached_input_tokens", int, 0),
            cumulative_input_tokens=_metric("cumulative_input_tokens", int, 0),
            cumulative_output_tokens=_metric("cumulative_output_tokens", int, 0),
            context_tokens_before=_metric("context_tokens_before", int, 0),
            context_tokens_after=_metric("context_tokens_after", int, 0),
            context_area_tokens=_metric("context_area_tokens", int, 0),
            avoided_read_estimated_tokens=_metric("avoided_read_estimated_tokens", int, 0),
            tool_output_estimated_tokens=_metric("tool_output_estimated_tokens", int, 0),
            metric_sources=sources,
            metric_quality=quality,
        )


@dataclass(frozen=True)
class OperationalReality:
    """Operational reality — the CLI tools actually used during the epoch."""

    cli_tools: tuple[str, ...] = ()
    tool_surfaces: tuple[str, ...] = ()
    retrieval_packs: tuple[str, ...] = ()
    route_kind_counts: Mapping[str, int] = field(default_factory=dict)
    routed_lookup_count: int = 0
    raw_file_read_count: int = 0
    raw_search_count: int = 0
    avoided_file_read_count: int = 0
    tool_output_bytes: int = 0
    expected_tool_count: int = 0
    observed_expected_tool_count: int = 0
    missing_expected_tool_count: int = 0
    expected_tool_counts: Mapping[str, int] = field(default_factory=dict)
    observed_tool_counts: Mapping[str, int] = field(default_factory=dict)
    missing_expected_tool_counts: Mapping[str, int] = field(default_factory=dict)
    degraded_tool_count: int = 0
    stale_or_unavailable_index_count: int = 0
    metric_sources: Mapping[str, str] = field(default_factory=dict)
    metric_quality: Mapping[str, str] = field(default_factory=dict)

    def derived_missing_expected_tool_counts(self) -> dict[str, int]:
        keys = set(self.expected_tool_counts) | set(self.observed_tool_counts)
        return {
            key: max(
                int(self.expected_tool_counts.get(key, 0))
                - int(self.observed_tool_counts.get(key, 0)),
                0,
            )
            for key in sorted(keys)
            if int(self.expected_tool_counts.get(key, 0)) > 0
        }

    def gap_invariants_hold(self) -> bool:
        return (
            self.expected_tool_count == sum(int(v) for v in self.expected_tool_counts.values())
            and self.observed_expected_tool_count
            == sum(int(v) for v in self.observed_tool_counts.values())
            and self.missing_expected_tool_count
            == sum(int(v) for v in self.missing_expected_tool_counts.values())
            and dict(self.missing_expected_tool_counts)
            == self.derived_missing_expected_tool_counts()
        )

    def missing_provenance(self) -> tuple[str, ...]:
        return _missing_metric_provenance(self, _OPERATIONAL_METRICS)

    @property
    def has_complete_provenance(self) -> bool:
        return not self.missing_provenance()

    def to_dict(self) -> dict[str, Any]:
        return {
            "cli_tools": list(self.cli_tools),
            "tool_surfaces": list(self.tool_surfaces),
            "retrieval_packs": list(self.retrieval_packs),
            "route_kind_counts": dict(self.route_kind_counts),
            "routed_lookup_count": self.routed_lookup_count,
            "raw_file_read_count": self.raw_file_read_count,
            "raw_search_count": self.raw_search_count,
            "avoided_file_read_count": self.avoided_file_read_count,
            "tool_output_bytes": self.tool_output_bytes,
            "expected_tool_count": self.expected_tool_count,
            "observed_expected_tool_count": self.observed_expected_tool_count,
            "missing_expected_tool_count": self.missing_expected_tool_count,
            "expected_tool_counts": dict(self.expected_tool_counts),
            "observed_tool_counts": dict(self.observed_tool_counts),
            "missing_expected_tool_counts": dict(self.missing_expected_tool_counts),
            "degraded_tool_count": self.degraded_tool_count,
            "stale_or_unavailable_index_count": self.stale_or_unavailable_index_count,
            "metric_sources": dict(self.metric_sources),
            "metric_quality": dict(self.metric_quality),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "OperationalReality":
        return cls(
            cli_tools=_as_tuple(data.get("cli_tools"), "operations.cli_tools"),
            tool_surfaces=_as_tuple(data.get("tool_surfaces"), "operations.tool_surfaces"),
            retrieval_packs=_as_tuple(data.get("retrieval_packs"), "operations.retrieval_packs"),
            route_kind_counts=dict(data.get("route_kind_counts") or {}),
            routed_lookup_count=int(data.get("routed_lookup_count", 0)),
            raw_file_read_count=int(data.get("raw_file_read_count", 0)),
            raw_search_count=int(data.get("raw_search_count", 0)),
            avoided_file_read_count=int(data.get("avoided_file_read_count", 0)),
            tool_output_bytes=int(data.get("tool_output_bytes", 0)),
            expected_tool_count=int(data.get("expected_tool_count", 0)),
            observed_expected_tool_count=int(data.get("observed_expected_tool_count", 0)),
            missing_expected_tool_count=int(data.get("missing_expected_tool_count", 0)),
            expected_tool_counts=dict(data.get("expected_tool_counts") or {}),
            observed_tool_counts=dict(data.get("observed_tool_counts") or {}),
            missing_expected_tool_counts=dict(data.get("missing_expected_tool_counts") or {}),
            degraded_tool_count=int(data.get("degraded_tool_count", 0)),
            stale_or_unavailable_index_count=int(
                data.get("stale_or_unavailable_index_count", 0)
            ),
            metric_sources=dict(data.get("metric_sources") or {}),
            metric_quality=dict(data.get("metric_quality") or {}),
        )


@dataclass(frozen=True)
class AbsoluteOutcome:
    """Absolute outcome — the gate exit code(s) recorded for the epoch."""

    gate_exit_codes: tuple[int, ...] = ()
    tool_failure_count: int = 0
    tool_degraded_count: int = 0
    tool_gap_count: int = 0
    metric_sources: Mapping[str, str] = field(default_factory=dict)
    metric_quality: Mapping[str, str] = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        """True when any recorded gate exited non-zero."""
        return any(code != 0 for code in self.gate_exit_codes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_exit_codes": list(self.gate_exit_codes),
            "tool_failure_count": self.tool_failure_count,
            "tool_degraded_count": self.tool_degraded_count,
            "tool_gap_count": self.tool_gap_count,
            "metric_sources": dict(self.metric_sources),
            "metric_quality": dict(self.metric_quality),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "AbsoluteOutcome":
        codes = _as_tuple(data.get("gate_exit_codes"), "outcome.gate_exit_codes")
        return cls(
            gate_exit_codes=tuple(int(c) for c in codes),
            tool_failure_count=int(data.get("tool_failure_count", 0)),
            tool_degraded_count=int(data.get("tool_degraded_count", 0)),
            tool_gap_count=int(data.get("tool_gap_count", 0)),
            metric_sources=dict(data.get("metric_sources") or {}),
            metric_quality=dict(data.get("metric_quality") or {}),
        )

    def missing_provenance(self) -> tuple[str, ...]:
        return _missing_metric_provenance(self, _OUTCOME_METRICS)

    @property
    def has_complete_provenance(self) -> bool:
        return not self.missing_provenance()


@dataclass(frozen=True)
class WorkSizingSnapshot:
    """Immutable pre-execution work-sizing snapshot captured before implementation.

    Planned sizes are ordinal labels (``XS``/``S``/``M``/``L``/``XL``) only. There
    are no numeric point fields and no implicit label-to-weight mapping. Feature
    and shipment composition histograms use the size labels plus an ``unsized``
    bucket for known members without a resolvable size label; there is no
    ``unavailable`` bucket, and skipped/unresolved IDs are excluded from both the
    count and the histogram. When membership is known, the count equals the sum
    of the histogram bucket values.
    """

    snapshot_at: str | None = None
    snapshot_boundary: str = "pre_execution"
    task_size_label: str | None = None
    feature_planned_size_label: str | None = None
    shipment_planned_size_label: str | None = None
    sizing_sources: Mapping[str, str] = field(default_factory=dict)
    sizing_source_revisions: Mapping[str, str] = field(default_factory=dict)
    sizing_ruleset_versions: Mapping[str, str] = field(default_factory=dict)
    feature_planned_child_task_count: int | None = None
    feature_planned_child_size_histogram: Mapping[str, int] = field(default_factory=dict)
    feature_child_membership_hash: str | None = None
    shipment_manifest_task_count: int | None = None
    shipment_manifest_size_histogram: Mapping[str, int] = field(default_factory=dict)
    shipment_membership_hash: str | None = None

    def __post_init__(self) -> None:
        for label_field in (
            "task_size_label",
            "feature_planned_size_label",
            "shipment_planned_size_label",
        ):
            label = getattr(self, label_field)
            if label is not None and label not in _SIZE_LABELS:
                raise EpochError(
                    f"WorkSizingSnapshot.{label_field} must be one of "
                    f"{sorted(_SIZE_LABELS)} or null; got {label!r}."
                )
        for hist_field in (
            "feature_planned_child_size_histogram",
            "shipment_manifest_size_histogram",
        ):
            unsupported = set(getattr(self, hist_field)) - _HISTOGRAM_KEYS
            if unsupported:
                raise EpochError(
                    f"WorkSizingSnapshot.{hist_field} has unsupported buckets "
                    f"{sorted(unsupported)}; allowed {sorted(_HISTOGRAM_KEYS)} "
                    f"(there is no 'unavailable' bucket)."
                )

    @staticmethod
    def membership_hash(ids: Iterable[str]) -> str | None:
        """Canonical lowercase SHA-256 hex digest over the unique sorted ID set.

        Duplicate IDs are collapsed before hashing. Empty/missing membership
        yields ``None`` rather than a digest of an empty unknown set.
        """
        unique = sorted({str(item) for item in ids})
        if not unique:
            return None
        payload = json.dumps(unique, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def feature_composition_consistent(self) -> bool:
        """True when known feature composition is internally consistent.

        Unknown membership (count is ``None``) is vacuously consistent; otherwise
        the count must equal the sum of the histogram buckets.
        """
        if self.feature_planned_child_task_count is None:
            return True
        return self.feature_planned_child_task_count == sum(
            self.feature_planned_child_size_histogram.values()
        )

    def shipment_composition_consistent(self) -> bool:
        if self.shipment_manifest_task_count is None:
            return True
        return self.shipment_manifest_task_count == sum(
            self.shipment_manifest_size_histogram.values()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_at": self.snapshot_at,
            "snapshot_boundary": self.snapshot_boundary,
            "task_size_label": self.task_size_label,
            "feature_planned_size_label": self.feature_planned_size_label,
            "shipment_planned_size_label": self.shipment_planned_size_label,
            "sizing_sources": dict(self.sizing_sources),
            "sizing_source_revisions": dict(self.sizing_source_revisions),
            "sizing_ruleset_versions": dict(self.sizing_ruleset_versions),
            "feature_planned_child_task_count": self.feature_planned_child_task_count,
            "feature_planned_child_size_histogram": dict(self.feature_planned_child_size_histogram),
            "feature_child_membership_hash": self.feature_child_membership_hash,
            "shipment_manifest_task_count": self.shipment_manifest_task_count,
            "shipment_manifest_size_histogram": dict(self.shipment_manifest_size_histogram),
            "shipment_membership_hash": self.shipment_membership_hash,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "WorkSizingSnapshot":
        return cls(
            snapshot_at=data.get("snapshot_at"),
            snapshot_boundary=str(data.get("snapshot_boundary", "pre_execution")),
            task_size_label=data.get("task_size_label"),
            feature_planned_size_label=data.get("feature_planned_size_label"),
            shipment_planned_size_label=data.get("shipment_planned_size_label"),
            sizing_sources=dict(data.get("sizing_sources") or {}),
            sizing_source_revisions=dict(data.get("sizing_source_revisions") or {}),
            sizing_ruleset_versions=dict(data.get("sizing_ruleset_versions") or {}),
            feature_planned_child_task_count=data.get("feature_planned_child_task_count"),
            feature_planned_child_size_histogram=dict(
                data.get("feature_planned_child_size_histogram") or {}
            ),
            feature_child_membership_hash=data.get("feature_child_membership_hash"),
            shipment_manifest_task_count=data.get("shipment_manifest_task_count"),
            shipment_manifest_size_histogram=dict(
                data.get("shipment_manifest_size_histogram") or {}
            ),
            shipment_membership_hash=data.get("shipment_membership_hash"),
        )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_PAYLOAD_TYPES = {
    "route": RouteConfiguration,
    "economics": EconomicPayload,
    "operations": OperationalReality,
    "outcome": AbsoluteOutcome,
}


@dataclass(frozen=True)
class ExecutionEpoch:
    """A single execution epoch composed of the four required payload classes."""

    task_id: str
    route: RouteConfiguration
    economics: EconomicPayload
    operations: OperationalReality
    outcome: AbsoluteOutcome
    epoch_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = field(default_factory=_utc_now_iso)
    schema_version: str = SCHEMA_VERSION
    backlog_item_id: str | None = None
    workspace_id: str | None = None
    session_id: str | None = None
    agent_role: str | None = None
    phase: str | None = None
    feature_id: str | None = None
    shipment_id: str | None = None
    branch: str | None = None
    commit_sha: str | None = None
    sizing: WorkSizingSnapshot | None = None

    def __post_init__(self) -> None:
        for name, expected in _PAYLOAD_TYPES.items():
            value = getattr(self, name)
            if not isinstance(value, expected):
                raise EpochError(
                    f"ExecutionEpoch.{name} must be a {expected.__name__} instance; "
                    f"got {type(value).__name__}."
                )
        if self.sizing is not None and not isinstance(self.sizing, WorkSizingSnapshot):
            raise EpochError(
                "ExecutionEpoch.sizing must be a WorkSizingSnapshot instance or None; "
                f"got {type(self.sizing).__name__}."
            )
        # For task epochs the backlog item IS the task; default the correlation
        # field to task_id so every reporting slice is backed by a persisted field.
        if self.backlog_item_id is None:
            object.__setattr__(self, "backlog_item_id", self.task_id)

    def to_record(self) -> dict[str, Any]:
        """Return the stable serialized shape shared by every sink."""
        return {
            "epoch_id": self.epoch_id,
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "backlog_item_id": self.backlog_item_id,
            "timestamp": self.timestamp,
            "workspace_id": self.workspace_id,
            "session_id": self.session_id,
            "agent_role": self.agent_role,
            "phase": self.phase,
            "feature_id": self.feature_id,
            "shipment_id": self.shipment_id,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "route": self.route.to_dict(),
            "economics": self.economics.to_dict(),
            "operations": self.operations.to_dict(),
            "outcome": self.outcome.to_dict(),
            "sizing": self.sizing.to_dict() if self.sizing is not None else None,
        }

    def gap_rollups_consistent(self) -> bool:
        return (
            self.operations.gap_invariants_hold()
            and self.outcome.tool_gap_count == self.operations.missing_expected_tool_count
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ExecutionEpoch":
        """Reconstruct an epoch from a mapping produced by :meth:`to_record`.

        Legacy v1.0 payloads are normalized to v1.1: ``schema_version`` is set to
        the current version (never a hybrid ``1.0.0`` record carrying v1.1
        fields), every economic metric provenance defaults to ``unavailable``
        because observation cannot be established, and ``backlog_item_id`` is
        copied from ``task_id`` when absent.

        Raises:
            EpochError: when the mapping is not a mapping, ``task_id`` is absent,
                any required payload class is missing, or ``epoch_id`` is present
                but empty/whitespace (it is not silently replaced).
        """
        if not isinstance(data, Mapping):
            raise EpochError("Epoch payload must be a JSON object (mapping).")
        if "task_id" not in data:
            raise EpochError("Epoch payload is missing the required 'task_id' field.")
        for key in _PAYLOAD_TYPES:
            if key not in data:
                raise EpochError(f"Epoch payload is missing the required '{key}' payload class.")

        raw_version = data.get("schema_version")
        legacy = (not raw_version) or str(raw_version) == "1.0.0"

        # Normalize every downstream shape/coercion failure (e.g. ``route: []``
        # raising AttributeError, or ``input_tokens: "abc"`` raising ValueError)
        # into a single controlled EpochError so the CLI never leaks a traceback.
        try:
            fields: dict[str, Any] = {
                "task_id": str(data["task_id"]),
                "route": RouteConfiguration.from_mapping(data["route"]),
                "economics": EconomicPayload.from_mapping(data["economics"], legacy=legacy),
                "operations": OperationalReality.from_mapping(data["operations"]),
                "outcome": AbsoluteOutcome.from_mapping(data["outcome"]),
                "schema_version": SCHEMA_VERSION if legacy else str(raw_version),
            }
            if "epoch_id" in data:
                raw_id = data["epoch_id"]
                if raw_id is None or (isinstance(raw_id, str) and not raw_id.strip()):
                    raise EpochError(
                        "Epoch payload 'epoch_id' is present but empty/whitespace; "
                        "refusing to silently replace it with a fresh UUID."
                    )
                fields["epoch_id"] = str(raw_id)
            if data.get("timestamp"):
                fields["timestamp"] = str(data["timestamp"])
            for name in (
                "backlog_item_id",
                "workspace_id",
                "session_id",
                "agent_role",
                "phase",
                "feature_id",
                "shipment_id",
                "branch",
                "commit_sha",
            ):
                if data.get(name) is not None:
                    fields[name] = str(data[name])
            if fields.get("backlog_item_id") is None:
                fields["backlog_item_id"] = fields["task_id"]
            sizing_data = data.get("sizing")
            if sizing_data is not None:
                fields["sizing"] = WorkSizingSnapshot.from_mapping(sizing_data)
            return cls(**fields)
        except EpochError:
            raise
        except (AttributeError, TypeError, ValueError, ArithmeticError) as exc:
            raise EpochError(f"Epoch payload is malformed: {exc}") from exc
