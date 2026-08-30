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
    topological_order_or_cycle,
)
from autoharness.schema_contracts import VALIDATION_GATES_SCHEMA_VERSION, resolve_validation_gates_schema_path

_ALLOWED_REF_PREFIX = "autoharness.detectors"

# D3 evidence-reference syntax (design doc §D3): `validator.consumes` entries
# may be written as `<node_id>#evidence` to explicitly document that the
# validator consumes the named node's produced `Evidence` record (self or
# sibling). The suffix is optional sugar: a bare `<node_id>` remains valid
# and is the pre-existing convention already exercised by the loader tests.
# Normalize it away here so every downstream comparison (membership in
# `seen`, `depends_on`) -- and the assembler's `evidence_map` lookup, which
# is keyed by bare `node_id` -- consults exactly one canonical form.
_EVIDENCE_REF_SUFFIX = "#evidence"


def _normalize_evidence_ref(ref: str) -> str:
    if ref.endswith(_EVIDENCE_REF_SUFFIX):
        return ref[: -len(_EVIDENCE_REF_SUFFIX)]
    return ref


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
            consumes=tuple(
                _normalize_evidence_ref(str(entry)) for entry in (validator_raw.get("consumes", ()) or ())
            ),
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
    if config_data is None:
        return DetectorRegistry()
    if not isinstance(config_data, dict):
        raise DetectorRegistryError(
            f"Invalid detector registry: top-level config must be a mapping, got {type(config_data).__name__}"
        )

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
        for consumed in node.validator.consumes:
            if consumed not in seen:
                raise DetectorRegistryError(
                    f"Detector {node.node_id} validator.consumes references unknown node {consumed}"
                )
            # A node consuming its own just-produced evidence (the D3
            # self-evidence case, e.g. `consumes: ["<self-node_id>#evidence"]`)
            # is always available regardless of `depends_on`: the assembler
            # guarantees every node's validator sees its own node's evidence
            # unconditionally, before `consumes` is even considered. Only a
            # *sibling* reference needs the depends_on declaration, since only
            # that guarantees evaluation-order safety for someone else's
            # evidence.
            if consumed != node.node_id and consumed not in node.depends_on:
                raise DetectorRegistryError(
                    f"Detector {node.node_id} validator.consumes references {consumed}, "
                    "which must also be declared in depends_on so upstream evidence is guaranteed "
                    "to have been produced before this node's validator runs"
                )
    _order, cycle_nodes = topological_order_or_cycle(nodes)
    if cycle_nodes:
        raise DetectorRegistryError(f"Detector registry contains a dependency cycle: {' -> '.join(cycle_nodes)}")
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
    try:
        config_text = config_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise DetectorRegistryError(f"Invalid detector registry: config.yaml is unreadable: {exc}") from exc
    try:
        # Do NOT coerce with `or {}`: that would silently convert *any*
        # falsey non-mapping YAML document (`[]`, `false`, `0`, `""`) into an
        # empty registry before `load_detector_registry` ever gets a chance
        # to reject it as malformed. Only a genuine YAML `null` document is
        # an intentionally-empty config; `load_detector_registry` already
        # handles `None` (zero nodes) and fails closed on every other
        # non-mapping type -- pass the parsed value through unmodified so
        # that single, already-tested fail-closed path is authoritative.
        config_data = yaml.safe_load(config_text)
    except yaml.YAMLError as exc:
        raise DetectorRegistryError(f"Invalid detector registry: config.yaml is malformed YAML: {exc}") from exc
    return load_detector_registry(config_data, autoharness_home)
