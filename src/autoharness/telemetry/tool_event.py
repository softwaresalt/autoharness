"""ToolTelemetryEvent v1.0 runtime model (U1, 084.001-T).

Implements the ratified ``schemas/tool-telemetry-event.schema.json`` contract as
an immutable runtime model. The schema is a frozen forward contract published by
079-F; this module is a faithful runtime implementation of it and MUST NOT
redesign or loosen it (docs/plans/2026-07-31-token-efficiency-telemetry-emission-decided-plan.md).

Mirrors the conventions established by :mod:`autoharness.telemetry.epoch`:
frozen dataclass, ``from __future__ import annotations``, a controlled
``ValueError`` subclass, canonical UUID/timestamp handling, per-metric
provenance completeness (``metric_sources`` / ``metric_quality``), and stable
``to_dict`` / ``from_mapping`` round-trips.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from autoharness.telemetry.epoch import WorkSizingSnapshot

SCHEMA_VERSION = "1.0.0"

TOOL_SURFACES = frozenset({"mcp", "cli", "shell", "builtin", "api", "unknown"})
STATUSES = frozenset({"success", "degraded", "blocked", "skipped", "failed", "operator_required"})
SENSITIVITIES = frozenset({"public", "internal", "ambiguous"})

# metric_sources / metric_quality value vocabularies, per the published schema.
METRIC_SOURCE_VALUES = frozenset(
    {
        "host_reported",
        "estimated",
        "derived",
        "unavailable",
        "not_applicable",
        "host",
        "backlogit",
        "operator",
    }
)
METRIC_QUALITY_VALUES = frozenset(
    {"observed", "estimated", "derived", "unavailable", "not_applicable"}
)
SECRET_SCAN_STATUSES = frozenset({"not_run", "passed", "flagged", "unavailable"})

# task_complexity_label vocabulary (108.002-T): backlogit's task-only complexity
# enum, structurally separate from size (WorkSizingSnapshot). complexity_source
# reuses the METRIC_SOURCE_VALUES vocabulary rather than defining its own, since
# it is provenance metadata of the same shape as every other *_source field.
TASK_COMPLEXITY_LABELS = frozenset({"trivial", "low", "medium", "high"})

# route_kind / freshness_state are well-known enums extensible via an "x-*" prefix.
_WELL_KNOWN_ROUTE_KINDS = frozenset(
    {
        "structural_graph",
        "doc_index",
        "backlog_index",
        "intercom",
        "raw_search",
        "raw_read",
        "none",
    }
)
_WELL_KNOWN_FRESHNESS_STATES = frozenset({"fresh", "stale", "unavailable", "unknown"})
_X_EXTENSION_PATTERN = re.compile(r"^x-[a-z0-9-]+$")
_EPOCH_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
# Schema contract for event_id: "type": "string", "minLength": 1, "pattern": "\\S"
# — any non-empty, non-whitespace-only string, NOT a UUID requirement. A UUID
# is only ever a convenience default when the field is omitted.
_EVENT_ID_NONWHITESPACE_PATTERN = re.compile(r"\S")

# Names of every nullable non-negative quantity that requires same-named
# metric_sources/metric_quality provenance once it is "populated" (a value
# strictly greater than zero per the schema's ``exclusiveMinimum: 0`` allOf
# conditionals). A null or a zero value is "not observed" and needs no entry.
_NONNEG_METRICS: tuple[str, ...] = (
    "retry_count",
    "duration_ms",
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "cumulative_input_tokens",
    "cumulative_output_tokens",
    "context_tokens_before",
    "context_tokens_after",
    "context_area_tokens",
    "routed_lookup_count",
    "raw_file_read_count",
    "raw_search_count",
    "avoided_file_read_count",
    "avoided_read_bytes",
    "avoided_read_estimated_tokens",
    "tool_output_bytes",
    "tool_output_estimated_tokens",
    "result_count",
)

# The complete set of top-level schema properties. additionalProperties: false
# at the schema root means any other key is rejected by from_mapping.
_SCHEMA_PROPERTY_NAMES = frozenset(
    {
        "schema_version",
        "event_id",
        "epoch_id",
        "parent_event_id",
        "timestamp",
        "workspace_id",
        "repo",
        "branch",
        "commit_sha",
        "session_id",
        "agent_role",
        "phase",
        "backlog_item_id",
        "feature_id",
        "shipment_id",
        "work_sizing_snapshot",
        "task_complexity_label",
        "complexity_source",
        "tool_surface",
        "server_name",
        "tool_name",
        "operation",
        "tool_version",
        "argv_fingerprint",
        "started_at",
        "ended_at",
        "duration_ms",
        "status",
        "exit_code",
        "error_kind",
        "retry_count",
        "degraded_mode",
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "cumulative_input_tokens",
        "cumulative_output_tokens",
        "context_tokens_before",
        "context_tokens_after",
        "context_area_tokens",
        "metric_sources",
        "metric_quality",
        "route_kind",
        "retrieval_pack",
        "expected_tool",
        "expected_reason",
        "fallback_reason",
        "routed_lookup_count",
        "raw_file_read_count",
        "raw_search_count",
        "avoided_file_read_count",
        "avoided_read_bytes",
        "avoided_read_estimated_tokens",
        "tool_output_bytes",
        "tool_output_estimated_tokens",
        "result_count",
        "freshness_state",
        "evidence_path",
        "artifact_refs",
        "sensitivity",
        "redaction_applied",
        "secret_scan_status",
    }
)


class ToolTelemetryEventError(ValueError):
    """Raised when a ToolTelemetryEvent payload is malformed or invalid."""


def event_correlates(
    event: "ToolTelemetryEvent", *, epoch_id: str | None, backlog_item_id: str | None
) -> bool:
    """Exact-correlation predicate shared by the journal reader (U3) and the
    event-to-epoch composer (U4): an event carrying an ``epoch_id`` is ONLY ever
    selected by an exact ``epoch_id`` match. The ``backlog_item_id`` fallback
    applies ONLY to events with NO ``epoch_id`` at all, so an event correlated to
    a different epoch is never attached here by a coincidentally-matching
    ``backlog_item_id`` (docs/plans/2026-07-31-token-efficiency-telemetry-emission-decided-plan.md,
    decision 5)."""
    if event.epoch_id is not None:
        return epoch_id is not None and event.epoch_id == epoch_id
    if backlog_item_id is not None and event.backlog_item_id is not None:
        return event.backlog_item_id == backlog_item_id
    return False


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_uuid_hex(value: Any, field_name: str) -> str | None:
    """Canonicalize a UUID-parseable value to lowercase 32-hex, or ``None``."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        raise ToolTelemetryEventError(f"'{field_name}' must be a non-empty UUID value.")
    try:
        return uuid.UUID(raw).hex
    except (AttributeError, TypeError, ValueError) as exc:
        raise ToolTelemetryEventError(
            f"'{field_name}' must be parseable by uuid.UUID(); got {raw!r}."
        ) from exc


def _normalize_event_id(value: Any, field_name: str = "event_id") -> str:
    """Validate a caller-supplied ``event_id`` against the frozen schema
    contract: any non-empty, non-whitespace-only string (pattern '\\S'). This
    is deliberately NOT a UUID requirement -- ``parent_event_id`` already
    accepts arbitrary schema-valid IDs (e.g. ``"tool-call-17"``), and
    ``event_id`` must accept the same values. A UUID is only ever generated as
    a convenience default when the field is omitted entirely."""
    if (
        not isinstance(value, str)
        or len(value) < 1
        or not _EVENT_ID_NONWHITESPACE_PATTERN.search(value)
    ):
        raise ToolTelemetryEventError(
            f"'{field_name}' must be a non-empty, non-whitespace-only string; got {value!r}."
        )
    return value


def _normalize_nonempty_str(value: Any, field_name: str) -> str:
    if value is None or not isinstance(value, str) or not value.strip():
        raise ToolTelemetryEventError(f"'{field_name}' must be a non-empty string.")
    return value


def _normalize_optional_str(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ToolTelemetryEventError(
            f"'{field_name}' must be a string or null; got {type(value).__name__}."
        )
    return value


def _normalize_timestamp(value: Any, field_name: str = "timestamp") -> str:
    """Validate/canonicalize an ISO-8601 instant with an explicit UTC offset.

    Mirrors ``cli.py``'s ``_validate_record_timestamp``: a timezone-naive value
    is an ambiguous instant and is rejected rather than silently assumed UTC.
    """
    if value is None:
        return _utc_now_iso()
    if not isinstance(value, str) or not value.strip():
        raise ToolTelemetryEventError(f"'{field_name}' must be a non-empty ISO-8601 string.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ToolTelemetryEventError(
            f"'{field_name}' {value!r} is not a valid ISO-8601 instant."
        ) from exc
    if parsed.tzinfo is None:
        raise ToolTelemetryEventError(
            f"'{field_name}' {value!r} lacks an explicit UTC offset (e.g. 'Z' or '+00:00')."
        )
    return value


def _normalize_bool(value: Any, field_name: str, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ToolTelemetryEventError(f"'{field_name}' must be a boolean; got {value!r}.")
    return value


def _normalize_nonneg_int(value: Any, field_name: str, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ToolTelemetryEventError(
            f"'{field_name}' must be a non-negative integer; got {value!r}."
        )
    if value < 0:
        raise ToolTelemetryEventError(f"'{field_name}' must be >= 0; got {value!r}.")
    return value


def _normalize_nonneg_or_none(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ToolTelemetryEventError(
            f"'{field_name}' must be a non-negative integer or null; got {value!r}."
        )
    if value < 0:
        raise ToolTelemetryEventError(f"'{field_name}' must be >= 0; got {value!r}.")
    return value


def _normalize_int_or_none(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ToolTelemetryEventError(f"'{field_name}' must be an integer or null; got {value!r}.")
    return value


def _normalize_str_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise ToolTelemetryEventError(f"'{field_name}' must be a JSON array of strings.")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ToolTelemetryEventError(f"'{field_name}' items must be strings; got {item!r}.")
        result.append(item)
    return tuple(result)


def _normalize_metric_map(value: Any, field_name: str, allowed: frozenset) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ToolTelemetryEventError(f"'{field_name}' must be a mapping.")
    result: dict[str, str] = {}
    for key, raw in value.items():
        if not isinstance(raw, str) or raw not in allowed:
            raise ToolTelemetryEventError(
                f"'{field_name}[{key!r}]' must be one of {sorted(allowed)}; got {raw!r}."
            )
        result[str(key)] = raw
    return result


def _normalize_extensible(
    value: Any, field_name: str, well_known: frozenset
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ToolTelemetryEventError(
            f"'{field_name}' must be a string or null; got {type(value).__name__}."
        )
    if value in well_known or _X_EXTENSION_PATTERN.match(value):
        return value
    raise ToolTelemetryEventError(
        f"'{field_name}' must be one of {sorted(well_known)} or match '^x-[a-z0-9-]+$'; "
        f"got {value!r}."
    )


def _metric_populated(value: Any) -> bool:
    """A metric is "populated" only when it is a strictly-positive number.

    Matches the schema's ``exclusiveMinimum: 0`` allOf conditionals: an absent
    (``null``) or observed-zero value never requires provenance.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


@dataclass(frozen=True)
class ToolTelemetryEvent:
    """Immutable runtime model of the ratified ToolTelemetryEvent v1.0 contract."""

    tool_surface: str
    tool_name: str
    operation: str
    status: str
    sensitivity: str
    schema_version: str = SCHEMA_VERSION
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    epoch_id: str | None = None
    parent_event_id: str | None = None
    timestamp: str = field(default_factory=_utc_now_iso)
    workspace_id: str | None = None
    repo: str | None = None
    branch: str | None = None
    commit_sha: str | None = None
    session_id: str | None = None
    agent_role: str | None = None
    phase: str | None = None
    backlog_item_id: str | None = None
    feature_id: str | None = None
    shipment_id: str | None = None
    work_sizing_snapshot: WorkSizingSnapshot | None = None
    task_complexity_label: str | None = None
    complexity_source: str | None = None
    server_name: str | None = None
    tool_version: str | None = None
    argv_fingerprint: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    duration_ms: int | None = None
    exit_code: int | None = None
    error_kind: str | None = None
    retry_count: int = 0
    degraded_mode: bool = False
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_input_tokens: int | None = None
    cumulative_input_tokens: int | None = None
    cumulative_output_tokens: int | None = None
    context_tokens_before: int | None = None
    context_tokens_after: int | None = None
    context_area_tokens: int | None = None
    metric_sources: Mapping[str, str] = field(default_factory=dict)
    metric_quality: Mapping[str, str] = field(default_factory=dict)
    route_kind: str | None = None
    retrieval_pack: str | None = None
    expected_tool: str | None = None
    expected_reason: str | None = None
    fallback_reason: str | None = None
    routed_lookup_count: int | None = None
    raw_file_read_count: int | None = None
    raw_search_count: int | None = None
    avoided_file_read_count: int | None = None
    avoided_read_bytes: int | None = None
    avoided_read_estimated_tokens: int | None = None
    tool_output_bytes: int | None = None
    tool_output_estimated_tokens: int | None = None
    result_count: int | None = None
    freshness_state: str | None = None
    evidence_path: str | None = None
    artifact_refs: tuple[str, ...] = ()
    redaction_applied: bool = False
    secret_scan_status: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ToolTelemetryEventError(
                f"'schema_version' must be the const {SCHEMA_VERSION!r}; got {self.schema_version!r}."
            )
        if self.tool_surface not in TOOL_SURFACES:
            raise ToolTelemetryEventError(
                f"'tool_surface' must be one of {sorted(TOOL_SURFACES)}; got {self.tool_surface!r}."
            )
        if self.status not in STATUSES:
            raise ToolTelemetryEventError(
                f"'status' must be one of {sorted(STATUSES)}; got {self.status!r}."
            )
        if self.sensitivity not in SENSITIVITIES:
            raise ToolTelemetryEventError(
                f"'sensitivity' must be one of {sorted(SENSITIVITIES)}; got {self.sensitivity!r}."
            )
        _normalize_nonempty_str(self.tool_name, "tool_name")
        _normalize_nonempty_str(self.operation, "operation")
        _normalize_nonempty_str(self.event_id, "event_id")
        _normalize_timestamp(self.timestamp)

        if isinstance(self.retry_count, bool) or not isinstance(self.retry_count, int) or self.retry_count < 0:
            raise ToolTelemetryEventError(
                f"'retry_count' must be a non-negative integer; got {self.retry_count!r}."
            )
        if not isinstance(self.degraded_mode, bool):
            raise ToolTelemetryEventError("'degraded_mode' must be a boolean.")
        if not isinstance(self.redaction_applied, bool):
            raise ToolTelemetryEventError("'redaction_applied' must be a boolean.")

        if self.epoch_id is not None and not _EPOCH_ID_PATTERN.match(str(self.epoch_id)):
            raise ToolTelemetryEventError(
                f"'epoch_id' must be 32 lowercase hex characters when present; got {self.epoch_id!r}."
            )
        has_epoch = self.epoch_id is not None
        has_backlog = self.backlog_item_id is not None and str(self.backlog_item_id).strip() != ""
        if not has_epoch and not has_backlog:
            raise ToolTelemetryEventError(
                "ToolTelemetryEvent requires at least one correlation anchor per the "
                "schema anyOf: a canonical 'epoch_id' or a non-empty 'backlog_item_id'."
            )

        for key, value in self.metric_sources.items():
            if value not in METRIC_SOURCE_VALUES:
                raise ToolTelemetryEventError(
                    f"metric_sources[{key!r}] must be one of {sorted(METRIC_SOURCE_VALUES)}; "
                    f"got {value!r}."
                )
        for key, value in self.metric_quality.items():
            if value not in METRIC_QUALITY_VALUES:
                raise ToolTelemetryEventError(
                    f"metric_quality[{key!r}] must be one of {sorted(METRIC_QUALITY_VALUES)}; "
                    f"got {value!r}."
                )

        if (
            self.route_kind is not None
            and self.route_kind not in _WELL_KNOWN_ROUTE_KINDS
            and not _X_EXTENSION_PATTERN.match(self.route_kind)
        ):
            raise ToolTelemetryEventError(
                f"'route_kind' must be one of {sorted(_WELL_KNOWN_ROUTE_KINDS)} or an "
                f"'x-*' extension; got {self.route_kind!r}."
            )
        if (
            self.freshness_state is not None
            and self.freshness_state not in _WELL_KNOWN_FRESHNESS_STATES
            and not _X_EXTENSION_PATTERN.match(self.freshness_state)
        ):
            raise ToolTelemetryEventError(
                f"'freshness_state' must be one of {sorted(_WELL_KNOWN_FRESHNESS_STATES)} or an "
                f"'x-*' extension; got {self.freshness_state!r}."
            )
        if self.secret_scan_status is not None and self.secret_scan_status not in SECRET_SCAN_STATUSES:
            raise ToolTelemetryEventError(
                f"'secret_scan_status' must be one of {sorted(SECRET_SCAN_STATUSES)} or null; "
                f"got {self.secret_scan_status!r}."
            )

        if self.work_sizing_snapshot is not None and not isinstance(
            self.work_sizing_snapshot, WorkSizingSnapshot
        ):
            raise ToolTelemetryEventError(
                "'work_sizing_snapshot' must be a WorkSizingSnapshot instance or None."
            )

        if self.task_complexity_label is not None and self.task_complexity_label not in TASK_COMPLEXITY_LABELS:
            raise ToolTelemetryEventError(
                f"'task_complexity_label' must be one of {sorted(TASK_COMPLEXITY_LABELS)} or null; "
                f"got {self.task_complexity_label!r}."
            )
        if self.complexity_source is not None and self.complexity_source not in METRIC_SOURCE_VALUES:
            raise ToolTelemetryEventError(
                f"'complexity_source' must be one of {sorted(METRIC_SOURCE_VALUES)} or null; "
                f"got {self.complexity_source!r}."
            )

        if self.exit_code is not None and (
            isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int)
        ):
            raise ToolTelemetryEventError(f"'exit_code' must be an integer or null; got {self.exit_code!r}.")

        for name in _NONNEG_METRICS:
            if name in ("retry_count",):
                continue  # already validated above (never null)
            value = getattr(self, name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ToolTelemetryEventError(
                    f"'{name}' must be a non-negative integer or null; got {value!r}."
                )

        if not isinstance(self.artifact_refs, tuple):
            object.__setattr__(self, "artifact_refs", tuple(self.artifact_refs))
        for ref in self.artifact_refs:
            if not isinstance(ref, str):
                raise ToolTelemetryEventError(f"'artifact_refs' items must be strings; got {ref!r}.")

        missing = self.missing_provenance()
        if missing:
            raise ToolTelemetryEventError(
                "populated metrics are missing same-named metric_sources/metric_quality "
                f"provenance: {missing}"
            )

    def missing_provenance(self) -> tuple[str, ...]:
        """Return populated (strictly-positive) metrics lacking provenance in
        BOTH ``metric_sources`` and ``metric_quality``."""
        return tuple(
            name
            for name in _NONNEG_METRICS
            if _metric_populated(getattr(self, name))
            and (name not in self.metric_sources or name not in self.metric_quality)
        )

    @property
    def has_complete_provenance(self) -> bool:
        return not self.missing_provenance()

    @property
    def is_expectation_only(self) -> bool:
        """True for a status-only expectation record: ``operation == "expect"``
        with ``status == "skipped"``. These never count as a tool invocation
        (docs/plans/2026-07-31-token-efficiency-telemetry-emission-decided-plan.md,
        decision 7)."""
        return self.operation == "expect" and self.status == "skipped"

    def to_dict(self) -> dict[str, Any]:
        """Return the stable, schema-shaped serialization of this event."""
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "epoch_id": self.epoch_id,
            "parent_event_id": self.parent_event_id,
            "timestamp": self.timestamp,
            "workspace_id": self.workspace_id,
            "repo": self.repo,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "session_id": self.session_id,
            "agent_role": self.agent_role,
            "phase": self.phase,
            "backlog_item_id": self.backlog_item_id,
            "feature_id": self.feature_id,
            "shipment_id": self.shipment_id,
            "work_sizing_snapshot": (
                self.work_sizing_snapshot.to_dict() if self.work_sizing_snapshot is not None else None
            ),
            "task_complexity_label": self.task_complexity_label,
            "complexity_source": self.complexity_source,
            "tool_surface": self.tool_surface,
            "server_name": self.server_name,
            "tool_name": self.tool_name,
            "operation": self.operation,
            "tool_version": self.tool_version,
            "argv_fingerprint": self.argv_fingerprint,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "exit_code": self.exit_code,
            "error_kind": self.error_kind,
            "retry_count": self.retry_count,
            "degraded_mode": self.degraded_mode,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "cumulative_input_tokens": self.cumulative_input_tokens,
            "cumulative_output_tokens": self.cumulative_output_tokens,
            "context_tokens_before": self.context_tokens_before,
            "context_tokens_after": self.context_tokens_after,
            "context_area_tokens": self.context_area_tokens,
            "metric_sources": dict(self.metric_sources),
            "metric_quality": dict(self.metric_quality),
            "route_kind": self.route_kind,
            "retrieval_pack": self.retrieval_pack,
            "expected_tool": self.expected_tool,
            "expected_reason": self.expected_reason,
            "fallback_reason": self.fallback_reason,
            "routed_lookup_count": self.routed_lookup_count,
            "raw_file_read_count": self.raw_file_read_count,
            "raw_search_count": self.raw_search_count,
            "avoided_file_read_count": self.avoided_file_read_count,
            "avoided_read_bytes": self.avoided_read_bytes,
            "avoided_read_estimated_tokens": self.avoided_read_estimated_tokens,
            "tool_output_bytes": self.tool_output_bytes,
            "tool_output_estimated_tokens": self.tool_output_estimated_tokens,
            "result_count": self.result_count,
            "freshness_state": self.freshness_state,
            "evidence_path": self.evidence_path,
            "artifact_refs": list(self.artifact_refs),
            "sensitivity": self.sensitivity,
            "redaction_applied": self.redaction_applied,
            "secret_scan_status": self.secret_scan_status,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ToolTelemetryEvent":
        if not isinstance(data, Mapping):
            raise ToolTelemetryEventError("ToolTelemetryEvent payload must be a JSON object (mapping).")
        unknown = set(data.keys()) - _SCHEMA_PROPERTY_NAMES
        if unknown:
            raise ToolTelemetryEventError(
                f"Unknown ToolTelemetryEvent field(s) (additionalProperties: false): {sorted(unknown)}."
            )

        schema_version = data.get("schema_version", SCHEMA_VERSION)
        if schema_version != SCHEMA_VERSION:
            raise ToolTelemetryEventError(
                f"'schema_version' must be {SCHEMA_VERSION!r}; got {schema_version!r}."
            )

        for required_name in ("tool_surface", "tool_name", "operation", "status", "sensitivity"):
            if required_name not in data or data.get(required_name) is None:
                raise ToolTelemetryEventError(f"'{required_name}' is required.")

        tool_surface = data["tool_surface"]
        if tool_surface not in TOOL_SURFACES:
            raise ToolTelemetryEventError(
                f"'tool_surface' must be one of {sorted(TOOL_SURFACES)}; got {tool_surface!r}."
            )
        status = data["status"]
        if status not in STATUSES:
            raise ToolTelemetryEventError(f"'status' must be one of {sorted(STATUSES)}; got {status!r}.")
        sensitivity = data["sensitivity"]
        if sensitivity not in SENSITIVITIES:
            raise ToolTelemetryEventError(
                f"'sensitivity' must be one of {sorted(SENSITIVITIES)}; got {sensitivity!r}."
            )

        event_id = data.get("event_id")
        event_id = uuid.uuid4().hex if event_id is None else _normalize_event_id(event_id, "event_id")
        epoch_id = _normalize_uuid_hex(data.get("epoch_id"), "epoch_id")
        timestamp = _normalize_timestamp(data.get("timestamp"))

        raw_sizing = data.get("work_sizing_snapshot")
        if raw_sizing is None:
            work_sizing_snapshot = None
        elif isinstance(raw_sizing, Mapping):
            work_sizing_snapshot = WorkSizingSnapshot.from_mapping(raw_sizing)
        else:
            raise ToolTelemetryEventError(
                "'work_sizing_snapshot' must be an object or null (frozen schema contract); "
                f"got {type(raw_sizing).__name__}."
            )

        metric_sources = _normalize_metric_map(
            data.get("metric_sources"), "metric_sources", METRIC_SOURCE_VALUES
        )
        metric_quality = _normalize_metric_map(
            data.get("metric_quality"), "metric_quality", METRIC_QUALITY_VALUES
        )
        artifact_refs = _normalize_str_tuple(data.get("artifact_refs"), "artifact_refs")

        return cls(
            schema_version=schema_version,
            event_id=event_id,
            epoch_id=epoch_id,
            parent_event_id=_normalize_optional_str(data.get("parent_event_id"), "parent_event_id"),
            timestamp=timestamp,
            workspace_id=_normalize_optional_str(data.get("workspace_id"), "workspace_id"),
            repo=_normalize_optional_str(data.get("repo"), "repo"),
            branch=_normalize_optional_str(data.get("branch"), "branch"),
            commit_sha=_normalize_optional_str(data.get("commit_sha"), "commit_sha"),
            session_id=_normalize_optional_str(data.get("session_id"), "session_id"),
            agent_role=_normalize_optional_str(data.get("agent_role"), "agent_role"),
            phase=_normalize_optional_str(data.get("phase"), "phase"),
            backlog_item_id=_normalize_optional_str(data.get("backlog_item_id"), "backlog_item_id"),
            feature_id=_normalize_optional_str(data.get("feature_id"), "feature_id"),
            shipment_id=_normalize_optional_str(data.get("shipment_id"), "shipment_id"),
            work_sizing_snapshot=work_sizing_snapshot,
            task_complexity_label=data.get("task_complexity_label"),
            complexity_source=data.get("complexity_source"),
            tool_surface=tool_surface,
            sensitivity=sensitivity,
            server_name=_normalize_optional_str(data.get("server_name"), "server_name"),
            tool_name=_normalize_nonempty_str(data.get("tool_name"), "tool_name"),
            operation=_normalize_nonempty_str(data.get("operation"), "operation"),
            tool_version=_normalize_optional_str(data.get("tool_version"), "tool_version"),
            argv_fingerprint=_normalize_optional_str(data.get("argv_fingerprint"), "argv_fingerprint"),
            started_at=_normalize_optional_str(data.get("started_at"), "started_at"),
            ended_at=_normalize_optional_str(data.get("ended_at"), "ended_at"),
            duration_ms=_normalize_nonneg_or_none(data.get("duration_ms"), "duration_ms"),
            status=status,
            exit_code=_normalize_int_or_none(data.get("exit_code"), "exit_code"),
            error_kind=_normalize_optional_str(data.get("error_kind"), "error_kind"),
            retry_count=_normalize_nonneg_int(data.get("retry_count"), "retry_count", 0),
            degraded_mode=_normalize_bool(data.get("degraded_mode"), "degraded_mode", False),
            input_tokens=_normalize_nonneg_or_none(data.get("input_tokens"), "input_tokens"),
            output_tokens=_normalize_nonneg_or_none(data.get("output_tokens"), "output_tokens"),
            cached_input_tokens=_normalize_nonneg_or_none(
                data.get("cached_input_tokens"), "cached_input_tokens"
            ),
            cumulative_input_tokens=_normalize_nonneg_or_none(
                data.get("cumulative_input_tokens"), "cumulative_input_tokens"
            ),
            cumulative_output_tokens=_normalize_nonneg_or_none(
                data.get("cumulative_output_tokens"), "cumulative_output_tokens"
            ),
            context_tokens_before=_normalize_nonneg_or_none(
                data.get("context_tokens_before"), "context_tokens_before"
            ),
            context_tokens_after=_normalize_nonneg_or_none(
                data.get("context_tokens_after"), "context_tokens_after"
            ),
            context_area_tokens=_normalize_nonneg_or_none(
                data.get("context_area_tokens"), "context_area_tokens"
            ),
            metric_sources=metric_sources,
            metric_quality=metric_quality,
            route_kind=_normalize_extensible(data.get("route_kind"), "route_kind", _WELL_KNOWN_ROUTE_KINDS),
            retrieval_pack=_normalize_optional_str(data.get("retrieval_pack"), "retrieval_pack"),
            expected_tool=_normalize_optional_str(data.get("expected_tool"), "expected_tool"),
            expected_reason=_normalize_optional_str(data.get("expected_reason"), "expected_reason"),
            fallback_reason=_normalize_optional_str(data.get("fallback_reason"), "fallback_reason"),
            routed_lookup_count=_normalize_nonneg_or_none(
                data.get("routed_lookup_count"), "routed_lookup_count"
            ),
            raw_file_read_count=_normalize_nonneg_or_none(
                data.get("raw_file_read_count"), "raw_file_read_count"
            ),
            raw_search_count=_normalize_nonneg_or_none(data.get("raw_search_count"), "raw_search_count"),
            avoided_file_read_count=_normalize_nonneg_or_none(
                data.get("avoided_file_read_count"), "avoided_file_read_count"
            ),
            avoided_read_bytes=_normalize_nonneg_or_none(
                data.get("avoided_read_bytes"), "avoided_read_bytes"
            ),
            avoided_read_estimated_tokens=_normalize_nonneg_or_none(
                data.get("avoided_read_estimated_tokens"), "avoided_read_estimated_tokens"
            ),
            tool_output_bytes=_normalize_nonneg_or_none(data.get("tool_output_bytes"), "tool_output_bytes"),
            tool_output_estimated_tokens=_normalize_nonneg_or_none(
                data.get("tool_output_estimated_tokens"), "tool_output_estimated_tokens"
            ),
            result_count=_normalize_nonneg_or_none(data.get("result_count"), "result_count"),
            freshness_state=_normalize_extensible(
                data.get("freshness_state"), "freshness_state", _WELL_KNOWN_FRESHNESS_STATES
            ),
            evidence_path=_normalize_optional_str(data.get("evidence_path"), "evidence_path"),
            artifact_refs=artifact_refs,
            redaction_applied=_normalize_bool(data.get("redaction_applied"), "redaction_applied", False),
            secret_scan_status=data.get("secret_scan_status"),
        )


def _reject_if_escapes_workspace(root: Path, value: str, field_name: str) -> None:
    """Reject a repo-local reference that is absolute, traverses outside
    ``root``, or resolves outside ``root`` after following symlinks.

    Mirrors the ``_is_within``/``resolve()`` containment convention already
    used by :mod:`autoharness.telemetry.context` (``resolve_context_ref``):
    ``Path.resolve()`` follows symlinks, so a symlink planted inside the
    workspace that points outside it is caught the same way plain ``..``
    traversal is.
    """
    raw = Path(value)
    if raw.is_absolute():
        raise ToolTelemetryEventError(
            f"'{field_name}' must be a repo-local path, not absolute; got {value!r}."
        )
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ToolTelemetryEventError(
            f"'{field_name}' escapes the workspace root (traversal or symlink escape): {value!r}."
        ) from None


def validate_event_workspace_references(
    event: "ToolTelemetryEvent", workspace_root: Path | str
) -> None:
    """Validate ``evidence_path``/``artifact_refs`` against the CLI workspace
    before journal append (R4 safety invariant: "workspace-contained, bounded,
    sanitized"; schema descriptions: "Repo-local path to sanitized retained
    evidence" / "Safe paths/IDs involved, not raw content").

    Rejects absolute paths, ``..`` traversal, and post-symlink-resolution
    escapes for both ``evidence_path`` and every ``artifact_refs`` entry.
    Raises :class:`ToolTelemetryEventError` — the same fail-closed error class
    used for every other malformed-input rejection in this module — so callers
    (the CLI) treat an unsafe reference exactly like any other invalid
    payload, never silently persisting it.
    """
    root = Path(workspace_root).resolve()
    if event.evidence_path is not None:
        _reject_if_escapes_workspace(root, event.evidence_path, "evidence_path")
    for index, ref in enumerate(event.artifact_refs):
        _reject_if_escapes_workspace(root, ref, f"artifact_refs[{index}]")
