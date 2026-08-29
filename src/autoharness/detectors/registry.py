"""Detector registry loader and schema validation."""

from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml
from jsonschema import Draft7Validator

from autoharness.detectors.contract import (
    NODE_ID_PATTERN,
    ApplicabilitySpec,
    NodeSpec,
    ProducerSpec,
    RemediationSpec,
    ValidatorSpec,
)
from autoharness.schema_contracts import VALIDATION_GATES_SCHEMA_VERSION, resolve_validation_gates_schema_path

_ALLOWED_REF_PREFIX = "autoharness.detectors"


class DetectorRegistryError(ValueError):
    exit_code = 2


@dataclass(frozen=True)
class DetectorRegistry:
    nodes: tuple[NodeSpec, ...] = ()
    version: str = ""
    schema_version: str = VALIDATION_GATES_SCHEMA_VERSION
    exit_code: int = 0


def _validate_config(config_data: dict[str, Any], autoharness_home: Path) -> None:
    schema_path = resolve_validation_gates_schema_path(autoharness_home)
    if schema_path is None:
        raise DetectorRegistryError("validation-gates schema is unavailable")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(config_data), key=lambda error: list(error.path))
    if errors:
        joined = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise DetectorRegistryError(f"Invalid detector registry: {joined}")


def _canonical_registry_version(raw_nodes: Any) -> str:
    payload = json.dumps(raw_nodes, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_callable(ref: str):
    module_name, _, attr_name = ref.partition(":")
    if not module_name or not attr_name:
        raise DetectorRegistryError(f"Invalid detector callable ref: {ref!r}")
    if module_name != _ALLOWED_REF_PREFIX and not module_name.startswith(_ALLOWED_REF_PREFIX + "."):
        raise DetectorRegistryError(f"Detector refs must resolve inside {_ALLOWED_REF_PREFIX}: {ref!r}")
    try:
        module: ModuleType = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - exercised by loader tests via failure path
        raise DetectorRegistryError(f"Could not import detector module {module_name!r}") from exc
    target = getattr(module, attr_name, None)
    if not callable(target):
        raise DetectorRegistryError(f"Detector ref {ref!r} did not resolve to a callable")
    return target


def _load_node(raw: dict[str, Any]) -> NodeSpec:
    node_id = str(raw["node_id"])
    match = NODE_ID_PATTERN.fullmatch(node_id)
    if match is None:
        raise DetectorRegistryError(f"Invalid detector node_id: {node_id!r}")

    producer_raw = dict(raw["producer"])
    if producer_raw.get("kind") == "command":
        raise DetectorRegistryError("producer.kind 'command' is not implemented in S1")
    mode = str(raw.get("mode", "report_only"))
    if mode != "report_only":
        raise DetectorRegistryError("detector mode must be report_only in S1")

    remediation_raw = dict(raw["remediation"])
    validator_raw = dict(raw["validator"])
    applies_raw = dict(raw["applies_when"])

    return NodeSpec(
        node_id=node_id,
        domain=match.group("domain"),
        detector_id=match.group("detector_id"),
        version=match.group("version"),
        applies_when=ApplicabilitySpec(
            changed_paths_any=tuple(applies_raw.get("changed_paths_any", ()) or ()),
            shipment_has_items_of_type=tuple(applies_raw.get("shipment_has_items_of_type", ()) or ()),
            workspace_surfaces_any=tuple(applies_raw.get("workspace_surfaces_any", ()) or ()),
            always=bool(applies_raw.get("always", False)),
        ),
        producer=ProducerSpec(
            kind=str(producer_raw["kind"]),
            ref=str(producer_raw["ref"]),
            tool_version_dims=tuple(producer_raw.get("tool_version_dims", ()) or ()),
            handler=_resolve_callable(str(producer_raw["ref"])),
        ),
        validator=ValidatorSpec(
            ref=str(validator_raw["ref"]),
            consumes=tuple(validator_raw.get("consumes", ()) or ()),
            handler=_resolve_callable(str(validator_raw["ref"])),
        ),
        depends_on=tuple(raw.get("depends_on", ()) or ()),
        severity=str(raw["severity"]),
        mode=mode,
        remediation=RemediationSpec(
            class_name=str(remediation_raw["class"]),
            hint=str(remediation_raw.get("hint", "")),
            target_refs=tuple(remediation_raw.get("target_refs", ()) or ()),
            authority=str(remediation_raw["authority"]),
        ),
    )


def load_detector_registry(config_data: Any, autoharness_home: Path) -> DetectorRegistry:
    if not isinstance(config_data, dict):
        return DetectorRegistry()

    _validate_config(config_data, autoharness_home)
    raw_nodes = config_data.get("detectors")
    if raw_nodes is None:
        return DetectorRegistry()
    if not isinstance(raw_nodes, list):
        raise DetectorRegistryError("detectors must be an array when present")

    nodes = tuple(_load_node(raw) for raw in raw_nodes)
    seen: set[str] = set()
    for node in nodes:
        if node.node_id in seen:
            raise DetectorRegistryError(f"Duplicate detector node_id: {node.node_id}")
        seen.add(node.node_id)
    for node in nodes:
        for depends_on in node.depends_on:
            if depends_on not in seen:
                raise DetectorRegistryError(
                    f"Detector {node.node_id} depends on unknown node {depends_on}"
                )
    return DetectorRegistry(
        nodes=nodes,
        version=_canonical_registry_version(raw_nodes),
    )


def load_detector_registry_from_workspace(
    workspace: Path,
    autoharness_home: Path,
) -> DetectorRegistry:
    config_path = workspace / ".autoharness" / "config.yaml"
    if not config_path.exists():
        return DetectorRegistry()
    config_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return load_detector_registry(config_data, autoharness_home)
