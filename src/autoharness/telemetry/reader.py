"""Local telemetry sink readers and v1.0 -> v1.1 normalization."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal

from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.epoch import EpochError, ExecutionEpoch

TelemetrySource = Literal["sqlite", "jsonl", "combined"]


@dataclass(frozen=True)
class TelemetryReadResult:
    status: str
    records: tuple[dict[str, Any], ...] = ()
    diagnostics: tuple[str, ...] = ()
    source: str = "combined"


def _canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(record: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(record).encode("utf-8")).hexdigest()


def _normalize_record(raw: Any) -> dict[str, Any]:
    return ExecutionEpoch.from_mapping(raw).to_record()


def _loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return default


def _row_get(row: sqlite3.Row, key: str, default: Any = None) -> Any:
    if key not in row.keys():
        return default
    value = row[key]
    return default if value is None else value


def _record_from_sqlite_row(row: sqlite3.Row) -> dict[str, Any]:
    payload_json = _row_get(row, "payload_json")
    if payload_json:
        return _normalize_record(json.loads(payload_json))

    route = {
        "models": _loads(_row_get(row, "models"), []),
        "route_kinds": _loads(_row_get(row, "route_kinds"), []),
    }
    economics = {
        "input_tokens": _row_get(row, "input_tokens", 0),
        "output_tokens": _row_get(row, "output_tokens", 0),
        "cogs_usd": _row_get(row, "cogs_usd", 0.0),
        "duration_seconds": _row_get(row, "duration_seconds", 0.0),
        "cached_input_tokens": _row_get(row, "cached_input_tokens", 0),
        "cumulative_input_tokens": _row_get(row, "cumulative_input_tokens", 0),
        "cumulative_output_tokens": _row_get(row, "cumulative_output_tokens", 0),
        "context_tokens_before": _row_get(row, "context_tokens_before", 0),
        "context_tokens_after": _row_get(row, "context_tokens_after", 0),
        "context_area_tokens": _row_get(row, "context_area_tokens", 0),
        "avoided_read_estimated_tokens": _row_get(row, "avoided_read_estimated_tokens", 0),
        "tool_output_estimated_tokens": _row_get(row, "tool_output_estimated_tokens", 0),
        "metric_sources": _loads(_row_get(row, "economics_metric_sources"), {}),
        "metric_quality": _loads(_row_get(row, "economics_metric_quality"), {}),
    }
    operations = {
        "cli_tools": _loads(_row_get(row, "cli_tools"), []),
        "tool_surfaces": _loads(_row_get(row, "tool_surfaces"), []),
        "retrieval_packs": _loads(_row_get(row, "retrieval_packs"), []),
        "route_kind_counts": _loads(_row_get(row, "route_kind_counts"), {}),
        "routed_lookup_count": _row_get(row, "routed_lookup_count", 0),
        "raw_file_read_count": _row_get(row, "raw_file_read_count", 0),
        "raw_search_count": _row_get(row, "raw_search_count", 0),
        "avoided_file_read_count": _row_get(row, "avoided_file_read_count", 0),
        "tool_output_bytes": _row_get(row, "tool_output_bytes", 0),
        "expected_tool_count": _row_get(row, "expected_tool_count", 0),
        "observed_expected_tool_count": _row_get(row, "observed_expected_tool_count", 0),
        "missing_expected_tool_count": _row_get(row, "missing_expected_tool_count", 0),
        "expected_tool_counts": _loads(_row_get(row, "expected_tool_counts"), {}),
        "observed_tool_counts": _loads(_row_get(row, "observed_tool_counts"), {}),
        "missing_expected_tool_counts": _loads(_row_get(row, "missing_expected_tool_counts"), {}),
        "degraded_tool_count": _row_get(row, "degraded_tool_count", 0),
        "stale_or_unavailable_index_count": _row_get(row, "stale_or_unavailable_index_count", 0),
        "metric_sources": _loads(_row_get(row, "operations_metric_sources"), {}),
        "metric_quality": _loads(_row_get(row, "operations_metric_quality"), {}),
    }
    outcome = {
        "gate_exit_codes": _loads(_row_get(row, "gate_exit_codes"), []),
        "tool_failure_count": _row_get(row, "tool_failure_count", 0),
        "tool_degraded_count": _row_get(row, "tool_degraded_count", 0),
        "tool_gap_count": _row_get(row, "tool_gap_count", 0),
        "metric_sources": _loads(_row_get(row, "outcome_metric_sources"), {}),
        "metric_quality": _loads(_row_get(row, "outcome_metric_quality"), {}),
    }
    sizing_json = _row_get(row, "sizing_json")
    return _normalize_record(
        {
            "epoch_id": _row_get(row, "epoch_id"),
            "schema_version": _row_get(row, "schema_version"),
            "task_id": _row_get(row, "task_id"),
            "backlog_item_id": _row_get(row, "backlog_item_id"),
            "timestamp": _row_get(row, "timestamp"),
            "workspace_id": _row_get(row, "workspace_id"),
            "session_id": _row_get(row, "session_id"),
            "agent_role": _row_get(row, "agent_role"),
            "phase": _row_get(row, "phase"),
            "feature_id": _row_get(row, "feature_id"),
            "shipment_id": _row_get(row, "shipment_id"),
            "branch": _row_get(row, "branch"),
            "commit_sha": _row_get(row, "commit_sha"),
            "route": route,
            "economics": economics,
            "operations": operations,
            "outcome": outcome,
            "sizing": _loads(sizing_json, None) if sizing_json else None,
        }
    )


def _read_sqlite(path: Path | None) -> tuple[list[dict[str, Any]], list[str], bool]:
    if path is None or not path.exists():
        return [], ["sqlite unavailable: database file missing"], False
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='execution_epochs'"
        ).fetchone()
        if table is None:
            return [], ["sqlite unavailable: execution_epochs table missing"], False
        records: list[dict[str, Any]] = []
        diagnostics: list[str] = []
        for row in conn.execute("SELECT * FROM execution_epochs ORDER BY timestamp, epoch_id"):
            try:
                records.append(_record_from_sqlite_row(row))
            except (EpochError, json.JSONDecodeError, TypeError, ValueError) as exc:
                diagnostics.append(f"sqlite skipped malformed row: {exc}")
        return records, diagnostics, True
    except sqlite3.Error as exc:
        return [], [f"sqlite unavailable: {exc}"], False
    finally:
        conn.close()


def _dedupe(records: Iterable[dict[str, Any]], source: str) -> tuple[list[dict[str, Any]], list[str]]:
    by_id: dict[str, tuple[dict[str, Any], str]] = {}
    diagnostics: list[str] = []
    for record in records:
        epoch_id = str(record.get("epoch_id"))
        digest = _digest(record)
        existing = by_id.get(epoch_id)
        if existing is None:
            by_id[epoch_id] = (record, digest)
            continue
        _existing_record, existing_digest = existing
        if existing_digest != digest:
            diagnostics.append(
                f"{source} conflict for epoch_id {epoch_id}: first accepted digest "
                f"{existing_digest} != later digest {digest}"
            )
    return [item[0] for item in by_id.values()], diagnostics


def _read_jsonl(path: Path | None) -> tuple[list[dict[str, Any]], list[str], bool]:
    if path is None or not path.exists():
        return [], ["jsonl unavailable: file missing"], False
    records: list[dict[str, Any]] = []
    diagnostics: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(_normalize_record(json.loads(line)))
                except (EpochError, json.JSONDecodeError, TypeError, ValueError) as exc:
                    diagnostics.append(f"jsonl skipped malformed line {line_number}: {exc}")
    except OSError as exc:
        return [], [f"jsonl unavailable: {exc}"], False
    deduped, duplicate_diagnostics = _dedupe(records, "jsonl")
    return deduped, [*diagnostics, *duplicate_diagnostics], True


def _combine(
    sqlite_records: list[dict[str, Any]],
    jsonl_records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    combined: dict[str, tuple[dict[str, Any], str]] = {}
    diagnostics: list[str] = []
    for record in sqlite_records:
        combined[record["epoch_id"]] = (record, _digest(record))
    for record in jsonl_records:
        epoch_id = record["epoch_id"]
        digest = _digest(record)
        existing = combined.get(epoch_id)
        if existing is None:
            combined[epoch_id] = (record, digest)
        elif existing[1] != digest:
            diagnostics.append(
                f"combined sqlite precedence conflict for epoch_id {epoch_id}: "
                f"sqlite digest {existing[1]} != jsonl digest {digest}"
            )
    return [item[0] for item in combined.values()], diagnostics


def read_epoch_records(
    config: TelemetryConfig,
    *,
    source: TelemetrySource = "combined",
) -> TelemetryReadResult:
    """Read persisted epoch records from configured local sinks and normalize to v1.1."""
    if source not in {"sqlite", "jsonl", "combined"}:
        raise ValueError("source must be one of: sqlite, jsonl, combined")
    if not config.enabled:
        return TelemetryReadResult(status="disabled", source=source)

    diagnostics: list[str] = []
    sqlite_records: list[dict[str, Any]] = []
    jsonl_records: list[dict[str, Any]] = []
    sqlite_available = jsonl_available = False

    if source in {"sqlite", "combined"}:
        sqlite_records, sqlite_diag, sqlite_available = _read_sqlite(config.database_path)
        diagnostics.extend(sqlite_diag)
    if source in {"jsonl", "combined"}:
        jsonl_records, jsonl_diag, jsonl_available = _read_jsonl(config.jsonl_path)
        diagnostics.extend(jsonl_diag)

    if source == "sqlite":
        records = sqlite_records
        available = sqlite_available
    elif source == "jsonl":
        records = jsonl_records
        available = jsonl_available
    else:
        records, combine_diag = _combine(sqlite_records, jsonl_records)
        diagnostics.extend(combine_diag)
        available = sqlite_available or jsonl_available

    status = "ok" if records else ("unavailable" if not available else "empty")
    return TelemetryReadResult(
        status=status,
        records=tuple(records),
        diagnostics=tuple(diagnostics),
        source=source,
    )
