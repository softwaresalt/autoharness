"""Pre-execution telemetry context artifact support."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.epoch import WorkSizingSnapshot

CONTEXT_SCHEMA_VERSION = "1.0.0"
SNAPSHOT_BOUNDARY = "pre_execution"


class TelemetryContextError(ValueError):
    """Raised when a telemetry begin context would be unsafe or conflicting."""


@dataclass(frozen=True)
class TelemetryBeginResult:
    enabled: bool
    status: str
    epoch_id: str | None = None
    context_ref: str | None = None
    context_path: Path | None = None
    context_digest: str | None = None
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "status": self.status,
            "epoch_id": self.epoch_id,
            "context_ref": self.context_ref,
            "context_digest": self.context_digest,
            "errors": list(self.errors),
        }


def _is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _normalize_epoch_id(value: str | None) -> str:
    if value is None:
        return uuid.uuid4().hex
    raw = str(value)
    if not raw.strip():
        raise TelemetryContextError("epoch_id must be a UUID, not empty/whitespace.")
    if ".." in raw or "/" in raw or "\\" in raw or Path(raw).is_absolute():
        raise TelemetryContextError("epoch_id must be a UUID value, not a path fragment.")
    try:
        return uuid.UUID(raw.strip()).hex
    except (AttributeError, TypeError, ValueError) as exc:
        raise TelemetryContextError("epoch_id must be parseable by uuid.UUID().") from exc


def _context_dir(config: TelemetryConfig, workspace_root: Path | str) -> Path:
    if not config.enabled or config.database_path is None:
        raise TelemetryContextError("telemetry is disabled; no context directory is available.")
    root = Path(workspace_root).resolve()
    context_dir = (config.database_path.parent / "contexts").resolve()
    if not _is_within(root, context_dir):
        raise TelemetryContextError("telemetry context directory escapes the workspace root.")
    return context_dir


def _context_path(config: TelemetryConfig, workspace_root: Path | str, epoch_id: str) -> Path:
    context_dir = _context_dir(config, workspace_root)
    candidate = (context_dir / f"{epoch_id}.json").resolve()
    root = Path(workspace_root).resolve()
    if candidate.parent != context_dir or not _is_within(context_dir, candidate):
        raise TelemetryContextError("telemetry context path escapes the context directory.")
    if not _is_within(root, candidate):
        raise TelemetryContextError("telemetry context path escapes the workspace root.")
    return candidate


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _with_digest(payload: dict[str, Any]) -> dict[str, Any]:
    body = dict(payload)
    body.pop("context_digest", None)
    digest = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    body["context_digest"] = digest
    return body


def canonical_context_digest(payload: Mapping[str, Any]) -> str:
    body = dict(payload)
    body.pop("context_digest", None)
    return hashlib.sha256(_canonical_bytes(body)).hexdigest()


def _read_context(path: Path) -> dict[str, Any] | None:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _repo_local_ref(workspace_root: Path | str, path: Path) -> str:
    return str(path.relative_to(Path(workspace_root).resolve()))


def _build_context_payload(
    *,
    epoch_id: str,
    task_id: str,
    backlog_item_id: str | None,
    feature_id: str | None,
    shipment_id: str | None,
    workspace_id: str | None,
    session_id: str | None,
    agent_role: str | None,
    phase: str | None,
    branch: str | None,
    commit_sha: str | None,
    captured_at: str | None,
    sizing: WorkSizingSnapshot | None,
    source_metadata: Mapping[str, str] | None,
    ruleset_metadata: Mapping[str, str] | None,
    version_metadata: Mapping[str, str] | None,
) -> dict[str, Any]:
    if not task_id or not str(task_id).strip():
        raise TelemetryContextError("task_id is required for telemetry begin.")
    if sizing is not None and not isinstance(sizing, WorkSizingSnapshot):
        raise TelemetryContextError("sizing must be a WorkSizingSnapshot or None.")
    return {
        "context_schema_version": CONTEXT_SCHEMA_VERSION,
        "epoch_id": epoch_id,
        "task_id": str(task_id),
        "backlog_item_id": str(backlog_item_id) if backlog_item_id is not None else str(task_id),
        "feature_id": str(feature_id) if feature_id is not None else None,
        "shipment_id": str(shipment_id) if shipment_id is not None else None,
        "workspace_id": str(workspace_id) if workspace_id is not None else None,
        "session_id": str(session_id) if session_id is not None else None,
        "agent_role": str(agent_role) if agent_role is not None else None,
        "phase": str(phase) if phase is not None else None,
        "branch": str(branch) if branch is not None else None,
        "commit_sha": str(commit_sha) if commit_sha is not None else None,
        "captured_at": captured_at or datetime.now(timezone.utc).isoformat(),
        "snapshot_boundary": SNAPSHOT_BOUNDARY,
        "sizing": sizing.to_dict() if sizing is not None else None,
        "source_metadata": dict(source_metadata or {}),
        "ruleset_metadata": dict(ruleset_metadata or {}),
        "version_metadata": dict(version_metadata or {}),
    }


def begin_context(
    config: TelemetryConfig,
    workspace_root: Path | str,
    *,
    task_id: str,
    epoch_id: str | None = None,
    backlog_item_id: str | None = None,
    feature_id: str | None = None,
    shipment_id: str | None = None,
    workspace_id: str | None = None,
    session_id: str | None = None,
    agent_role: str | None = None,
    phase: str | None = None,
    branch: str | None = None,
    commit_sha: str | None = None,
    captured_at: str | None = None,
    sizing: WorkSizingSnapshot | None = None,
    source_metadata: Mapping[str, str] | None = None,
    ruleset_metadata: Mapping[str, str] | None = None,
    version_metadata: Mapping[str, str] | None = None,
) -> TelemetryBeginResult:
    """Create the stable pre-execution context artifact, or no-op when disabled."""
    if not config.enabled:
        return TelemetryBeginResult(enabled=False, status="disabled")

    canonical_id = _normalize_epoch_id(epoch_id)
    path = _context_path(config, workspace_root, canonical_id)
    existing = _read_context(path) if path.exists() else None
    effective_captured_at = captured_at
    if existing is not None and captured_at is None:
        existing_captured_at = existing.get("captured_at")
        if isinstance(existing_captured_at, str):
            effective_captured_at = existing_captured_at
    payload = _with_digest(
        _build_context_payload(
            epoch_id=canonical_id,
            task_id=task_id,
            backlog_item_id=backlog_item_id,
            feature_id=feature_id,
            shipment_id=shipment_id,
            workspace_id=workspace_id,
            session_id=session_id,
            agent_role=agent_role,
            phase=phase,
            branch=branch,
            commit_sha=commit_sha,
            captured_at=effective_captured_at,
            sizing=sizing,
            source_metadata=source_metadata,
            ruleset_metadata=ruleset_metadata,
            version_metadata=version_metadata,
        )
    )
    context_ref = _repo_local_ref(workspace_root, path)

    if existing is not None:
        existing_digest = existing.get("context_digest")
        if existing == payload:
            return TelemetryBeginResult(
                enabled=True,
                status="idempotent_begin",
                epoch_id=canonical_id,
                context_ref=context_ref,
                context_path=path,
                context_digest=str(existing_digest),
            )
        return TelemetryBeginResult(
            enabled=True,
            status="conflict",
            epoch_id=canonical_id,
            context_ref=context_ref,
            context_path=path,
            context_digest=str(existing_digest) if existing_digest else None,
            errors=("context already exists with different canonical content",),
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.resolve() != _context_dir(config, workspace_root):
        raise TelemetryContextError("telemetry context directory changed during creation.")
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    except FileExistsError:
        return begin_context(
            config,
            workspace_root,
            task_id=task_id,
            epoch_id=canonical_id,
            backlog_item_id=backlog_item_id,
            feature_id=feature_id,
            shipment_id=shipment_id,
            workspace_id=workspace_id,
            session_id=session_id,
            agent_role=agent_role,
            phase=phase,
            branch=branch,
            commit_sha=commit_sha,
            captured_at=effective_captured_at,
            sizing=sizing,
            source_metadata=source_metadata,
            ruleset_metadata=ruleset_metadata,
            version_metadata=version_metadata,
        )

    return TelemetryBeginResult(
        enabled=True,
        status="created",
        epoch_id=canonical_id,
        context_ref=context_ref,
        context_path=path,
        context_digest=payload["context_digest"],
    )


def resolve_context_ref(
    config: TelemetryConfig,
    workspace_root: Path | str,
    context_ref: str | Path | None,
) -> Path:
    """Resolve and validate a repo-local context reference for future close paths."""
    if context_ref is None or not str(context_ref).strip():
        raise TelemetryContextError("context_ref is required.")
    raw = Path(str(context_ref))
    if raw.is_absolute():
        raise TelemetryContextError("context_ref must be repo-local, not absolute.")
    root = Path(workspace_root).resolve()
    context_dir = _context_dir(config, root)
    candidate = (root / raw).resolve()
    if candidate.parent != context_dir:
        raise TelemetryContextError("context_ref must point directly inside the context directory.")
    if candidate.suffix != ".json":
        raise TelemetryContextError("context_ref must point to a JSON context artifact.")
    try:
        if uuid.UUID(candidate.stem).hex != candidate.stem:
            raise TelemetryContextError("context_ref filename must use the canonical epoch ID.")
    except ValueError as exc:
        raise TelemetryContextError("context_ref filename must use the canonical epoch ID.") from exc
    if not _is_within(context_dir, candidate) or not _is_within(root, candidate):
        raise TelemetryContextError("context_ref escapes the workspace or context directory.")
    return candidate


def load_context_ref(
    config: TelemetryConfig,
    workspace_root: Path | str,
    context_ref: str | Path | None,
) -> dict[str, Any]:
    """Load and validate a repo-local context artifact for task-close recording."""
    path = resolve_context_ref(config, workspace_root, context_ref)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TelemetryContextError(f"could not read context_ref: {exc}") from exc
    if not isinstance(payload, dict):
        raise TelemetryContextError("context artifact must be a JSON object.")
    epoch_id = payload.get("epoch_id")
    if not isinstance(epoch_id, str) or epoch_id != path.stem:
        raise TelemetryContextError("context filename and stored epoch_id must match.")
    if _normalize_epoch_id(epoch_id) != epoch_id:
        raise TelemetryContextError("context epoch_id must be canonical UUID hex.")
    stored_digest = payload.get("context_digest")
    actual_digest = canonical_context_digest(payload)
    if stored_digest != actual_digest:
        raise TelemetryContextError("context digest mismatch; refusing tampered context.")
    return payload
