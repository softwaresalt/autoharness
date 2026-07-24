"""Pre-execution backlogit hierarchical sizing snapshot adapter."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from autoharness.telemetry.epoch import WorkSizingSnapshot

_SIZE_LABELS = {"XS", "S", "M", "L", "XL"}
_HISTOGRAM_LABELS = _SIZE_LABELS | {"unsized"}

Runner = Callable[[tuple[str, ...], Path], str]


def _default_runner(backlogit_bin: str) -> Runner:
    def run(argv: tuple[str, ...], cwd: Path) -> str:
        completed = subprocess.run(
            [backlogit_bin, "--cwd", str(cwd), *argv, "--no-update-check"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return completed.stdout

    return run


def _json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("backlogit output did not contain a JSON object")
    loaded = json.loads(text[start : end + 1])
    return loaded if isinstance(loaded, dict) else {}


def _safe_get(runner: Runner, cwd: Path, item_id: str | None) -> dict[str, Any] | None:
    if not item_id:
        return None
    try:
        return _json_object(runner(("get", item_id, "--format", "json"), cwd))
    except Exception:
        return None


def _valid_size(value: Any) -> str | None:
    text = str(value) if value is not None else ""
    return text if text in _SIZE_LABELS else None


def _task_size(item: Mapping[str, Any] | None) -> str | None:
    if not isinstance(item, Mapping):
        return None
    custom = item.get("custom_fields")
    if not isinstance(custom, Mapping):
        return None
    return _valid_size(custom.get("size"))


def _revision(item: Mapping[str, Any] | None) -> str:
    if not isinstance(item, Mapping):
        return "unavailable"
    custom = item.get("custom_fields")
    if isinstance(custom, Mapping):
        for key in ("size_revision", "planned_estimate_revision"):
            if custom.get(key):
                return str(custom[key])
    return str(item.get("updated_at") or "unavailable")


def _composition(
    item: Mapping[str, Any] | None,
) -> tuple[int | None, dict[str, int], str | None, str]:
    if not isinstance(item, Mapping):
        return None, {}, None, "unavailable"
    comp = item.get("size_composition")
    if not isinstance(comp, Mapping):
        return None, {}, None, "unavailable"

    members = comp.get("members")
    if not isinstance(members, list):
        return None, {}, None, str(comp.get("ruleset_version") or "unavailable")
    ids: list[str] = []
    for member in members:
        if isinstance(member, Mapping):
            if member.get("artifact_type") == "task" and member.get("id"):
                ids.append(str(member["id"]))
        elif member:
            ids.append(str(member))
    unique_ids = sorted(set(ids))
    histogram_raw = comp.get("histogram")
    histogram: dict[str, int] = {}
    if isinstance(histogram_raw, Mapping):
        for key, value in histogram_raw.items():
            if key in _SIZE_LABELS:
                histogram[str(key)] = max(int(value), 0)
    sized_count = sum(histogram.values())
    unsized = max(len(unique_ids) - sized_count, 0)
    if unsized:
        histogram["unsized"] = unsized
    unsupported = set(histogram) - _HISTOGRAM_LABELS
    for key in unsupported:
        histogram.pop(key, None)
    return (
        len(unique_ids),
        histogram,
        WorkSizingSnapshot.membership_hash(unique_ids),
        str(comp.get("ruleset_version") or "unavailable"),
    )


def capture_work_sizing_snapshot(
    *,
    workspace: Path | str,
    task_id: str,
    feature_id: str | None = None,
    shipment_id: str | None = None,
    runner: Runner | None = None,
    backlogit_bin: str = "backlogit",
    snapshot_at: str | None = None,
) -> WorkSizingSnapshot:
    """Capture a single immutable pre-execution WorkSizingSnapshot from backlogit."""
    cwd = Path(workspace)
    run = runner or _default_runner(backlogit_bin)
    sync_ok = True
    try:
        run(("sync",), cwd)
    except Exception:
        # 079.013-T freshness contract: a failed pre-capture sync means we cannot
        # guarantee the index reflects current on-disk membership, so degrade
        # feature/shipment composition to explicit unavailable instead of reading a
        # potentially stale cached composition. Telemetry still emits (non-blocking).
        sync_ok = False

    task = _safe_get(run, cwd, task_id)
    feature = _safe_get(run, cwd, feature_id) if sync_ok else None
    shipment = _safe_get(run, cwd, shipment_id) if sync_ok else None

    task_label = _task_size(task)
    feature_count, feature_histogram, feature_hash, feature_ruleset = _composition(feature)
    shipment_count, shipment_histogram, shipment_hash, shipment_ruleset = _composition(shipment)

    return WorkSizingSnapshot(
        snapshot_at=snapshot_at or datetime.now(timezone.utc).isoformat(),
        snapshot_boundary="pre_execution",
        task_size_label=task_label,
        feature_planned_size_label=None,
        shipment_planned_size_label=None,
        sizing_sources={
            "task": "backlogit" if task is not None and task_label is not None else "unavailable",
            "feature": "backlogit" if feature_count is not None else "unavailable",
            "shipment": "backlogit" if shipment_count is not None else "unavailable",
        },
        sizing_source_revisions={
            "task": _revision(task),
            "feature": _revision(feature),
            "shipment": _revision(shipment),
        },
        sizing_ruleset_versions={
            "task": "backlogit-hierarchical-sizing-v1",
            "feature": feature_ruleset,
            "shipment": shipment_ruleset,
        },
        feature_planned_child_task_count=feature_count,
        feature_planned_child_size_histogram=feature_histogram,
        feature_child_membership_hash=feature_hash,
        shipment_manifest_task_count=shipment_count,
        shipment_manifest_size_histogram=shipment_histogram,
        shipment_membership_hash=shipment_hash,
    )
