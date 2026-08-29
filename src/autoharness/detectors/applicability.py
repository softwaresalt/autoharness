"""Applicability context and fail-closed evaluation for pre-review detectors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

from autoharness.detectors.contract import ApplicabilitySpec, NodeResult, NodeSpec
from autoharness.gates.discovery import resolve_commit_ref
from autoharness.gates.match import path_matches
from autoharness.gates.topology import FilesystemTopologyReaders, _resolve_shipment_from_branch


class ApplicabilityContextError(ValueError):
    pass


@dataclass(frozen=True)
class ApplicabilityContext:
    base_sha: str
    head_sha: str
    modified_paths: tuple[str, ...]
    shipment_id: str
    shipment_item_types: frozenset[str]
    workspace_surfaces: frozenset[str]
    touches_reviewable_paths: bool


def _load_workspace_profile(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ApplicabilityContextError("workspace profile is missing") from exc
    except OSError as exc:  # pragma: no cover - defensive
        raise ApplicabilityContextError("workspace profile is unreadable") from exc
    if not isinstance(data, dict):
        raise ApplicabilityContextError("workspace profile is malformed")
    return data


def _resolve_item_types(readers, shipment_id: str):
    shipments = tuple(readers.list_shipments())
    current_branch = readers.current_branch()
    resolved = _resolve_shipment_from_branch(current_branch, shipments)
    if resolved != shipment_id:
        raise ApplicabilityContextError("shipment manifest could not be resolved from the current branch")
    for shipment in shipments:
        if shipment.shipment_id != shipment_id:
            continue
        item_types: set[str] = set()
        for item_id in shipment.manifest_item_ids:
            artifact = readers.read_artifact(item_id)
            if artifact is None or not artifact.artifact_type:
                continue
            item_types.add(artifact.artifact_type)
        return frozenset(item_types)
    raise ApplicabilityContextError("shipment manifest is unavailable")


def build_applicability_context(
    base: str,
    head: str = "HEAD",
    *,
    cwd: Path | None = None,
    resolve_ref: Callable[..., str | None] = resolve_commit_ref,
    discover: Callable[..., list[str]],
    profile_loader: Callable[[Path], dict] = _load_workspace_profile,
    readers_factory: Callable[[Path], object] = FilesystemTopologyReaders,
) -> ApplicabilityContext:
    workspace = cwd or Path(".")
    base_sha = resolve_ref(base, cwd=workspace)
    if base_sha is None:
        raise ApplicabilityContextError("base ref could not be resolved")
    head_sha = resolve_ref(head, cwd=workspace)
    if head_sha is None:
        raise ApplicabilityContextError("head ref could not be resolved")

    readers = readers_factory(workspace)
    shipments = tuple(readers.list_shipments())
    current_branch = readers.current_branch()
    shipment_id = _resolve_shipment_from_branch(current_branch, shipments)
    if shipment_id is None:
        raise ApplicabilityContextError("shipment manifest could not be resolved from the current branch")
    shipment_item_types = _resolve_item_types(readers, shipment_id)

    profile = profile_loader(workspace / ".autoharness" / "workspace-profile.yaml")
    runtime_surfaces = profile.get("runtime_surfaces")
    if not isinstance(runtime_surfaces, dict):
        raise ApplicabilityContextError("workspace profile is missing runtime_surfaces")
    workspace_surfaces = frozenset(
        name for name, enabled in runtime_surfaces.items() if isinstance(enabled, bool) and enabled
    )

    modified_paths = tuple(discover(base_sha, head_sha, cwd=workspace))
    touches_reviewable_paths = any(not path.lower().endswith(".md") for path in modified_paths)

    return ApplicabilityContext(
        base_sha=base_sha,
        head_sha=head_sha,
        modified_paths=modified_paths,
        shipment_id=shipment_id,
        shipment_item_types=shipment_item_types,
        workspace_surfaces=workspace_surfaces,
        touches_reviewable_paths=touches_reviewable_paths,
    )


def context_failure_results(nodes: tuple[NodeSpec, ...] | list[NodeSpec], reason: str) -> tuple[NodeResult, ...]:
    return tuple(
        NodeResult(
            name=node.node_id,
            status="insufficient_evidence",
            token="INSUFFICIENT_EVIDENCE",
            message=reason,
        )
        for node in nodes
    )


def _not_applicable(node_id: str, message: str, excluded_by: str) -> NodeResult:
    return NodeResult(
        name=node_id,
        status="not_applicable",
        token="NOT_APPLICABLE",
        message=message,
        excluded_by=excluded_by,
    )


def evaluate_node_applicability(node: NodeSpec, context: ApplicabilityContext) -> NodeResult | None:
    applies_when: ApplicabilitySpec = node.applies_when
    if applies_when.always:
        return None
    if applies_when.changed_paths_any and not any(
        path_matches(pattern, path)
        for pattern in applies_when.changed_paths_any
        for path in context.modified_paths
    ):
        return _not_applicable(node.node_id, "excluded by changed_paths_any", "changed_paths_any")
    if applies_when.shipment_has_items_of_type and not any(
        item_type in context.shipment_item_types for item_type in applies_when.shipment_has_items_of_type
    ):
        return _not_applicable(
            node.node_id,
            "excluded by shipment_has_items_of_type",
            "shipment_has_items_of_type",
        )
    if applies_when.workspace_surfaces_any and not any(
        surface in context.workspace_surfaces for surface in applies_when.workspace_surfaces_any
    ):
        return _not_applicable(
            node.node_id,
            "excluded by workspace_surfaces_any",
            "workspace_surfaces_any",
        )
    return None
