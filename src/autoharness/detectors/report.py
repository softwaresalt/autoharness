"""Epoch-keyed pre-review detector report emission."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from autoharness.detectors.contract import NodeResult


def _rfc3339_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_autoharness_version() -> str:
    try:
        from autoharness import __version__

        return __version__
    except Exception:  # pragma: no cover - defensive fallback
        return ""


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_freshness_fingerprint(
    *,
    base_sha: str,
    registry_version: str,
    schema_version: str,
    tool_versions: dict[str, str],
    autoharness_version: str | None = None,
) -> str:
    payload = {
        "base_sha": base_sha,
        "registry_version": registry_version,
        "schema_version": schema_version,
        "autoharness_version": autoharness_version if autoharness_version is not None else _default_autoharness_version(),
        "tool_versions": {key: tool_versions[key] for key in sorted(tool_versions)},
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()[:16]


def compute_epoch_key(
    head_sha: str,
    *,
    base_sha: str,
    registry_version: str,
    schema_version: str,
    tool_versions: dict[str, str],
    autoharness_version: str | None = None,
) -> tuple[str, str]:
    fingerprint = build_freshness_fingerprint(
        base_sha=base_sha,
        registry_version=registry_version,
        schema_version=schema_version,
        tool_versions=tool_versions,
        autoharness_version=autoharness_version,
    )
    return f"{head_sha}-{fingerprint}", fingerprint


def report_path_for(
    workspace: Path,
    *,
    base_sha: str,
    head_sha: str,
    registry_version: str,
    schema_version: str,
    tool_versions: dict[str, str],
    autoharness_version: str | None = None,
) -> Path:
    epoch_key, _fingerprint = compute_epoch_key(
        head_sha,
        base_sha=base_sha,
        registry_version=registry_version,
        schema_version=schema_version,
        tool_versions=tool_versions,
        autoharness_version=autoharness_version,
    )
    return workspace / ".autoharness" / "gates" / "pre-review" / f"{epoch_key}.json"


def resolve_tool_versions(tool_version_dims: Iterable[str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for dimension in sorted(set(tool_version_dims)):
        if dimension == "python":
            resolved[dimension] = platform.python_version()
        else:
            resolved[dimension] = os.environ.get(f"AUTOHARNESS_TOOL_VERSION_{dimension.upper().replace('-', '_')}", "")
    return resolved


def _merged_provenance(
    result: NodeResult,
    *,
    base_sha: str,
    head_sha: str,
    epoch_key: str,
    fingerprint: str,
    tool_versions: dict[str, str],
    touches_reviewable_paths: bool,
    produced_at: str,
    reviewed_sha: str | None,
) -> dict[str, object]:
    provenance = dict(result.provenance)
    provenance.update(
        {
            "base_sha": base_sha,
            "head_sha": head_sha,
            "epoch_key": epoch_key,
            "fingerprint": fingerprint,
            "reviewed_sha": reviewed_sha,
            "platform": platform.system().lower(),
            "tool_versions": {key: tool_versions[key] for key in sorted(tool_versions)},
            "produced_at": produced_at,
            "touches_reviewable_paths": touches_reviewable_paths,
        }
    )
    return provenance


def build_report_payload(
    results: Iterable[NodeResult],
    *,
    base_sha: str,
    head_sha: str,
    registry_version: str,
    schema_version: str,
    tool_versions: dict[str, str],
    touches_reviewable_paths: bool,
    produced_at: str | None = None,
    reviewed_sha: str | None = None,
    autoharness_version: str | None = None,
) -> tuple[dict[str, object], ...]:
    timestamp = produced_at or _rfc3339_now()
    epoch_key, fingerprint = compute_epoch_key(
        head_sha,
        base_sha=base_sha,
        registry_version=registry_version,
        schema_version=schema_version,
        tool_versions=tool_versions,
        autoharness_version=autoharness_version,
    )
    payload = []
    for result in results:
        entry = result.to_dict()
        entry["provenance"] = _merged_provenance(
            result,
            base_sha=base_sha,
            head_sha=head_sha,
            epoch_key=epoch_key,
            fingerprint=fingerprint,
            tool_versions=tool_versions,
            touches_reviewable_paths=touches_reviewable_paths,
            produced_at=timestamp,
            reviewed_sha=reviewed_sha,
        )
        payload.append(entry)
    return tuple(payload)


@dataclass(frozen=True)
class ReportEmissionResult:
    path: Path
    epoch_key: str
    fingerprint: str
    payload: tuple[dict[str, object], ...]
    payload_bytes: bytes
    tool_versions: dict[str, str]
    wrote_new: bool
    publication_failed: bool = False
    message: str = ""


def emit_pre_review_report(
    results: Iterable[NodeResult],
    *,
    workspace: Path,
    base_sha: str,
    head_sha: str,
    registry_version: str,
    schema_version: str,
    tool_versions: dict[str, str],
    touches_reviewable_paths: bool,
    produced_at: str | None = None,
    reviewed_sha: str | None = None,
    autoharness_version: str | None = None,
) -> ReportEmissionResult:
    epoch_key, fingerprint = compute_epoch_key(
        head_sha,
        base_sha=base_sha,
        registry_version=registry_version,
        schema_version=schema_version,
        tool_versions=tool_versions,
        autoharness_version=autoharness_version,
    )
    path = workspace / ".autoharness" / "gates" / "pre-review" / f"{epoch_key}.json"
    payload = build_report_payload(
        tuple(results),
        base_sha=base_sha,
        head_sha=head_sha,
        registry_version=registry_version,
        schema_version=schema_version,
        tool_versions=tool_versions,
        touches_reviewable_paths=touches_reviewable_paths,
        produced_at=produced_at,
        reviewed_sha=reviewed_sha,
        autoharness_version=autoharness_version,
    )
    payload_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    temp_path = path.parent / f".{epoch_key}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
    wrote_new = False
    publication_failed = False
    message = ""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with temp_path.open("xb") as handle:
            handle.write(payload_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp_path, path)
            wrote_new = True
        except FileExistsError:
            wrote_new = False
    except OSError as exc:
        publication_failed = True
        message = f"pre-review report publish unavailable: {exc}"
    finally:
        try:
            temp_path.unlink()
        except OSError:
            # Best-effort cleanup only; never mask the primary publication
            # outcome (success, no-clobber, or publication_failed) computed above.
            pass
    return ReportEmissionResult(
        path=path,
        epoch_key=epoch_key,
        fingerprint=fingerprint,
        payload=payload,
        payload_bytes=payload_bytes,
        tool_versions={key: tool_versions[key] for key in sorted(tool_versions)},
        wrote_new=wrote_new,
        publication_failed=publication_failed,
        message=message,
    )
