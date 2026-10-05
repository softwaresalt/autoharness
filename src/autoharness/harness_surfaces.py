"""One-entry harness surface resolver: result contract, records and classification.

Unit B of the ship lifecycle release units plan
(``docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md``). This module
publishes the ``harness-resolution`` result contract (schema
``schemas/harness-resolution/1.0.0.schema.json``): the three resolution
states and their exit codes, the diagnostics-only ``ReadStage``, and the
47-code reason registry in listed order, where the listed order is the
precedence (FI-6). Class 1b is the exception: among the three read-limit
codes the first occurrence selects.

All reads go through one ``harness_read`` reader per resolution and inherit
its ordinary-hazard scope (FI-10); this module adds no claim beyond it.
"""

from __future__ import annotations

import enum
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import yaml

from autoharness.harness_read import Reader, ReadErrorCode, TrustRoot

__all__ = [
    "BACKLOG_ROOT_NAMES",
    "Declaration",
    "MAX_MEMBERS",
    "NONE_SURFACE",
    "REASON_REGISTRY",
    "ReadLimitHit",
    "ReadStage",
    "ReasonSpec",
    "ResolutionResult",
    "ResolutionState",
    "SCHEMA_VERSION",
    "STATE_EXIT",
    "SUPPORTED_SURFACES",
    "SurfaceRow",
    "SurfaceSpec",
    "SurfaceState",
    "make_result",
    "read_limit_diagnostics",
    "reason_spec",
    "task_id_sort_key",
]

SCHEMA_VERSION = "1.0.0"


class ResolutionState(enum.Enum):
    """The three resolution states."""

    HARNESS_READY = "HARNESS_READY"
    NO_HARNESS = "NO_HARNESS"
    UNRESOLVED = "UNRESOLVED"


STATE_EXIT: Mapping[ResolutionState, int] = MappingProxyType(
    {
        ResolutionState.HARNESS_READY: 0,
        ResolutionState.NO_HARNESS: 1,
        ResolutionState.UNRESOLVED: 2,
    }
)


class SurfaceState(enum.Enum):
    """Per-surface classification carried by a surface row."""

    PRESENT = "PRESENT"
    MISSING = "MISSING"
    STALE = "STALE"
    INVALID = "INVALID"


class ReadStage(enum.Enum):
    """Where a read happened (diagnostics only). Values are the diagnostic tokens."""

    SHIPMENT_CANDIDATE = "shipment_queue_or_archive_candidate"
    MEMBER_CANDIDATE = "member_queue_or_archive_candidate"
    MANIFEST = "manifest_read"
    TEMPLATE = "template_read"
    INSTALLED = "installed_file_read"
    CANDIDATE_RECHECK = "candidate_ledger_recheck"
    SURFACE_RECHECK = "surface_recheck"


@dataclass(frozen=True)
class ReasonSpec:
    """One registry entry: code, precedence class, state, exit and surface-row state."""

    code: str
    reason_class: str
    state: ResolutionState
    exit_code: int
    surface_state: SurfaceState | None


def _registry() -> tuple[ReasonSpec, ...]:
    unresolved, no_harness, ready = (
        ResolutionState.UNRESOLVED,
        ResolutionState.NO_HARNESS,
        ResolutionState.HARNESS_READY,
    )
    invalid, missing, stale, present = (
        SurfaceState.INVALID,
        SurfaceState.MISSING,
        SurfaceState.STALE,
        SurfaceState.PRESENT,
    )
    groups: tuple[tuple[str, ResolutionState, tuple[tuple[str, SurfaceState | None], ...]], ...] = (
        ("1", unresolved, (("INPUT_CHANGED_DURING_RESOLUTION", None),)),
        ("1b", unresolved, (
            ("FILE_COUNT_LIMIT", None),
            ("TOTAL_SIZE_LIMIT", None),
            ("FILE_SIZE_LIMIT", None),
        )),
        ("2", unresolved, tuple((code, None) for code in (
            "BACKLOG_ROOT_NOT_FOUND",
            "BACKLOG_ROOT_AMBIGUOUS",
            "SHIPMENT_ID_INVALID",
            "SHIPMENT_NOT_FOUND",
            "SHIPMENT_AMBIGUOUS",
            "SHIPMENT_RECORD_INVALID",
            "SHIPMENT_ID_MISMATCH",
            "MEMBERS_INVALID",
            "MEMBERS_EMPTY",
            "MEMBERS_TOO_MANY",
            "MEMBER_ID_INVALID",
            "MEMBER_KIND_UNSUPPORTED",
            "MEMBER_DUPLICATE",
            "MEMBER_NOT_FOUND",
            "MEMBER_AMBIGUOUS",
            "MEMBER_RECORD_INVALID",
            "MEMBER_ID_MISMATCH",
            "NO_TASK_MEMBERS",
        ))),
        ("3", unresolved, tuple((code, None) for code in (
            "FEATURE_DECLARES_SURFACE",
            "DECLARATION_MISSING",
            "DECLARATION_MALFORMED",
            "DECLARATION_DUPLICATE",
            "DECLARATION_MIXED",
            "SURFACE_UNSUPPORTED",
        ))),
        ("4", ready, (("NO_SURFACES_REQUIRED", None),)),
        ("5", unresolved, tuple((code, None) for code in (
            "MANIFEST_NOT_FOUND",
            "MANIFEST_UNREADABLE",
            "MANIFEST_DECODE_INVALID",
            "MANIFEST_YAML_INVALID",
            "MANIFEST_DUPLICATE_KEY",
            "MANIFEST_SHAPE_INVALID",
        ))),
        ("6", unresolved, tuple((code, invalid) for code in (
            "MANIFEST_ENTRY_AMBIGUOUS",
            "MANIFEST_TEMPLATE_MISMATCH",
            "MANIFEST_ENTRY_INVALID",
            "TEMPLATE_NOT_FOUND",
            "TEMPLATE_UNREADABLE",
            "TEMPLATE_VARIABLE_UNRESOLVED",
            "INSTALLED_UNREADABLE",
        ))),
        ("7", no_harness, (
            ("MANIFEST_ENTRY_NOT_FOUND", missing),
            ("INSTALLED_NOT_FOUND", missing),
            ("CHECKSUM_MISMATCH", stale),
            ("RENDER_MISMATCH", stale),
        )),
        ("8", ready, (("ALL_SURFACES_PRESENT", present),)),
    )
    return tuple(
        ReasonSpec(code, reason_class, state, STATE_EXIT[state], surface_state)
        for reason_class, state, codes in groups
        for code, surface_state in codes
    )


REASON_REGISTRY: tuple[ReasonSpec, ...] = _registry()
_BY_CODE: Mapping[str, ReasonSpec] = MappingProxyType({spec.code: spec for spec in REASON_REGISTRY})
_READ_LIMIT_CODES = frozenset(
    {ReadErrorCode.FILE_COUNT_LIMIT, ReadErrorCode.TOTAL_SIZE_LIMIT, ReadErrorCode.FILE_SIZE_LIMIT}
)
_READ_LIMIT_CODE_NAMES = frozenset(code.value for code in _READ_LIMIT_CODES)
_ROOT_CODES = frozenset({"BACKLOG_ROOT_NOT_FOUND", "BACKLOG_ROOT_AMBIGUOUS"})

BACKLOG_ROOT_NAMES = (".backlog", ".backlogit")


@dataclass(frozen=True)
class SurfaceSpec:
    """A supported surface: its ID, installed path and template (manifest form)."""

    surface_id: str
    installed_path: str
    template: str


# FI-8: exactly one supported mapping.
SUPPORTED_SURFACES: Mapping[str, SurfaceSpec] = MappingProxyType(
    {
        "harness-architect": SurfaceSpec(
            surface_id="harness-architect",
            installed_path=".github/skills/harness-architect/SKILL.md",
            template="skills/harness-architect/SKILL.md.tmpl",
        )
    }
)


@dataclass(frozen=True)
class SurfaceRow:
    """One per-surface result row."""

    surface_id: str
    installed_path: str
    template: str
    state: SurfaceState
    reason_code: str


@dataclass(frozen=True)
class Declaration:
    """One task member's surface declaration (``harness-surface:<surface_id>``)."""

    member_id: str
    surface_id: str


@dataclass(frozen=True)
class ResolutionResult:
    """A resolution result. Build it with :func:`make_result`, which checks the contract."""

    schema_version: str
    state: ResolutionState
    reason_code: str
    exit_code: int
    shipment_id: str | None
    backlog_root: str | None
    surfaces: tuple[SurfaceRow, ...]
    declarations: tuple[Declaration, ...]
    inputs_sha256: str
    diagnostics: tuple[str, ...]

    def to_document(self) -> dict[str, object]:
        """The JSON document, with fields in contract order."""
        return {
            "schema_version": self.schema_version,
            "state": self.state.value,
            "reason_code": self.reason_code,
            "exit_code": self.exit_code,
            "shipment_id": self.shipment_id,
            "backlog_root": self.backlog_root,
            "surfaces": [
                {
                    "surface_id": row.surface_id,
                    "installed_path": row.installed_path,
                    "template": row.template,
                    "state": row.state.value,
                    "reason_code": row.reason_code,
                }
                for row in self.surfaces
            ],
            "declarations": [
                {"member_id": item.member_id, "surface_id": item.surface_id} for item in self.declarations
            ],
            "inputs_sha256": self.inputs_sha256,
            "diagnostics": list(self.diagnostics),
        }


def reason_spec(code: str) -> ReasonSpec:
    """The registry entry for ``code``; ``KeyError`` for a code outside the registry."""
    return _BY_CODE[code]


def read_limit_diagnostics(code: ReadErrorCode, stage: ReadStage) -> tuple[str, str]:
    """The two class 1b diagnostics: the native read-limit code and the stage."""
    if code not in _READ_LIMIT_CODES:
        raise ValueError(f"{code!r} is not a read-limit code")
    if not isinstance(stage, ReadStage):
        raise ValueError(f"{stage!r} is not a ReadStage")
    return (f"read_error_code={code.value}", f"read_stage={stage.value}")


SHIPMENT_ID_RE = re.compile(r"^[0-9]+-S$")
MEMBER_ID_RE = re.compile(r"^([0-9]+(?:\.[0-9]+)*)-([A-Z])$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_READ_DIAGNOSTIC_PREFIXES = ("read_error_code=", "read_stage=")


def task_id_sort_key(member_id: str) -> tuple[object, ...]:
    """Sort key for task IDs (``<n>[.<n>...]-T``) by numeric parts, then the raw ID."""
    match = MEMBER_ID_RE.fullmatch(member_id) if isinstance(member_id, str) else None
    if match is None or match.group(2) != "T":
        raise ValueError(f"not a task ID: {member_id!r}")
    return (tuple(int(part) for part in match.group(1).split(".")), member_id)


def make_result(
    reason_code: str,
    *,
    shipment_id: str | None,
    backlog_root: str | None,
    inputs_sha256: str,
    surfaces: Sequence[SurfaceRow] = (),
    declarations: Sequence[Declaration] = (),
    diagnostics: Sequence[str] = (),
) -> ResolutionResult:
    """Build a result, deriving state and exit from the registry; ``ValueError`` on a contract breach."""
    try:
        spec = reason_spec(reason_code)
    except KeyError:
        raise ValueError(f"unknown reason code: {reason_code!r}") from None
    surfaces, declarations, diagnostics = tuple(surfaces), tuple(declarations), tuple(diagnostics)

    if reason_code == "SHIPMENT_ID_INVALID":
        if shipment_id is not None:
            raise ValueError("SHIPMENT_ID_INVALID carries no shipment ID")
    elif shipment_id is None:
        if reason_code not in _ROOT_CODES:
            raise ValueError(f"{reason_code} requires a shipment ID")
    elif not (isinstance(shipment_id, str) and SHIPMENT_ID_RE.fullmatch(shipment_id)):
        raise ValueError(f"invalid shipment ID: {shipment_id!r}")

    if reason_code in _ROOT_CODES:
        if backlog_root is not None:
            raise ValueError(f"{reason_code} carries no backlog root")
    elif backlog_root not in BACKLOG_ROOT_NAMES:
        raise ValueError(f"invalid backlog root: {backlog_root!r}")

    if spec.surface_state is None:
        if surfaces:
            raise ValueError(f"{reason_code} carries no surface row")
    else:
        if len(surfaces) != 1:
            raise ValueError(f"{reason_code} requires exactly one surface row")
        row = surfaces[0]
        supported = SUPPORTED_SURFACES.get(row.surface_id)
        if supported is None or (row.installed_path, row.template) != (supported.installed_path, supported.template):
            raise ValueError(f"unsupported surface row: {row!r}")
        if row.state is not spec.surface_state or row.reason_code != reason_code:
            raise ValueError(f"surface row disagrees with {reason_code}: {row!r}")

    member_ids = [item.member_id for item in declarations]
    keys = [task_id_sort_key(member_id) for member_id in member_ids]
    if keys != sorted(keys) or len(set(member_ids)) != len(member_ids):
        raise ValueError("declarations must be unique and sorted by task ID")
    if any(not isinstance(item.surface_id, str) or not item.surface_id for item in declarations):
        raise ValueError("declaration surface IDs must be non-empty strings")

    if not (isinstance(inputs_sha256, str) and _DIGEST_RE.fullmatch(inputs_sha256)):
        raise ValueError("inputs_sha256 must be 64 lowercase hex digits")

    if any(not isinstance(item, str) for item in diagnostics):
        raise ValueError("diagnostics must be strings")
    if reason_code in _READ_LIMIT_CODE_NAMES:
        valid = {read_limit_diagnostics(ReadErrorCode(reason_code), stage) for stage in ReadStage}
        if diagnostics not in valid:
            raise ValueError(f"{reason_code} requires exactly its read-limit code and stage diagnostics")
    elif any(item.startswith(_READ_DIAGNOSTIC_PREFIXES) for item in diagnostics):
        raise ValueError(f"{reason_code} carries no read-limit diagnostics")

    return ResolutionResult(
        schema_version=SCHEMA_VERSION,
        state=spec.state,
        reason_code=reason_code,
        exit_code=spec.exit_code,
        shipment_id=shipment_id,
        backlog_root=backlog_root,
        surfaces=surfaces,
        declarations=declarations,
        inputs_sha256=inputs_sha256,
        diagnostics=diagnostics,
    )


# --- B2 (188.002-T): backlog root, records, membership and declarations ------

MAX_MEMBERS = 48
NONE_SURFACE = "none"
_SURFACE_LABEL = "harness-surface"
_SURFACE_LABEL_RE = re.compile(r"^harness-surface:([a-z0-9]+(?:-[a-z0-9]+)*)$")
_ARTIFACT_TYPE_BY_SUFFIX = MappingProxyType({"S": "shipment", "F": "feature", "T": "task"})
_PRECEDENCE: Mapping[str, int] = MappingProxyType({spec.code: index for index, spec in enumerate(REASON_REGISTRY)})


class _DuplicateKeyError(yaml.YAMLError):
    """A mapping repeats a key."""


class _AliasForbiddenError(yaml.YAMLError):
    """An anchor or alias appears; record and manifest YAML have no use for either."""


class _StrictLoader(yaml.SafeLoader):
    """A ``yaml.SafeLoader`` that rejects duplicate mapping keys, anchors and aliases."""

    def compose_node(self, parent: Any, index: Any) -> Any:
        event = self.peek_event()
        if isinstance(event, yaml.AliasEvent) or getattr(event, "anchor", None) is not None:
            raise _AliasForbiddenError("anchors and aliases are not accepted")
        return super().compose_node(parent, index)

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _value_node in node.value:
            key = self.construct_object(key_node, deep=True)
            try:
                duplicate = key in seen
            except TypeError:
                continue  # unhashable keys are rejected by the base constructor
            if duplicate:
                raise _DuplicateKeyError(f"duplicate key {key!r}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def _load_yaml(text: str) -> Any:
    """Parse one YAML document with :class:`_StrictLoader` (raises ``yaml.YAMLError``)."""
    return yaml.load(text, Loader=_StrictLoader)  # noqa: S506 - _StrictLoader is a SafeLoader


@dataclass(frozen=True)
class ReadLimitHit:
    """The first read-limit error (class 1b): its native code and the stage."""

    code: ReadErrorCode
    stage: ReadStage


@dataclass(frozen=True)
class _Records:
    """Backlog-root, shipment, membership and declaration facts (classes 2 and 3)."""

    backlog_root: str | None
    shipment_id: str | None
    facts: tuple[str, ...]
    declarations: tuple[Declaration, ...]
    surface_ids: tuple[str, ...]
    read_limit: ReadLimitHit | None

    @property
    def reason_code(self) -> str | None:
        """The first applicable class 2 or class 3 fact, by listed order."""
        return _first_applicable(self.facts)


def _first_applicable(codes: Sequence[str]) -> str | None:
    """The code listed first in the registry (``KeyError`` for an unknown code).

    Class 1b selects by first occurrence, not by listed order, so read-limit
    codes are refused here.
    """
    best: tuple[int, str] | None = None
    for code in codes:
        rank = _PRECEDENCE[code]
        if code in _READ_LIMIT_CODE_NAMES:
            raise ValueError(f"{code} selects by first occurrence")
        if best is None or rank < best[0]:
            best = (rank, code)
    return None if best is None else best[1]


def _frontmatter(data: bytes) -> dict[Any, Any] | None:
    """The YAML frontmatter mapping of a record, or ``None`` when it is not well formed."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0] != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    try:
        loaded = _load_yaml("\n".join(lines[1:end]))
    except yaml.YAMLError:
        return None
    return loaded if isinstance(loaded, dict) else None


def _read_record(
    reader: Reader, backlog_root: str, item_id: str, stage: ReadStage
) -> tuple[str, dict[Any, Any] | ReadLimitHit | None]:
    """Read both exact candidates of one record.

    Returns ``("limit", hit)``, ``("absent" | "ambiguous" | "invalid" | "mismatch", None)``
    or ``("present", frontmatter)``. The first read-limit error stops all reads.
    """
    present: list[bytes] = []
    invalid = False
    for folder in ("queue", "archive"):
        result = reader.read_bytes(TrustRoot.WORKSPACE, f"{backlog_root}/{folder}/{item_id}.md")
        if result.error is None:
            present.append(result.data if result.data is not None else b"")
        elif result.error in _READ_LIMIT_CODES:
            return "limit", ReadLimitHit(result.error, stage)
        elif result.error is not ReadErrorCode.PATH_NOT_FOUND:
            invalid = True
    if invalid:
        return "invalid", None
    if not present:
        return "absent", None
    if len(present) > 1:
        return "ambiguous", None
    record = _frontmatter(present[0])
    if record is None:
        return "invalid", None
    record_id, artifact_type = record.get("id"), record.get("artifact_type")
    if not isinstance(record_id, str) or not isinstance(artifact_type, str):
        return "invalid", None
    if record_id != item_id or artifact_type != _ARTIFACT_TYPE_BY_SUFFIX[item_id[-1]]:
        return "mismatch", None
    return "present", record


_SHIPMENT_CODES = MappingProxyType(
    {
        "absent": "SHIPMENT_NOT_FOUND",
        "ambiguous": "SHIPMENT_AMBIGUOUS",
        "invalid": "SHIPMENT_RECORD_INVALID",
        "mismatch": "SHIPMENT_ID_MISMATCH",
    }
)
_MEMBER_CODES = MappingProxyType(
    {
        "absent": "MEMBER_NOT_FOUND",
        "ambiguous": "MEMBER_AMBIGUOUS",
        "invalid": "MEMBER_RECORD_INVALID",
        "mismatch": "MEMBER_ID_MISMATCH",
    }
)


def _declaration(labels: Sequence[str]) -> tuple[list[str], str | None]:
    """Class 3 facts of one task's declaration labels, and its surface when there are none."""
    declared = [label for label in labels if label == _SURFACE_LABEL or label.startswith(_SURFACE_LABEL + ":")]
    if not declared:
        return ["DECLARATION_MISSING"], None
    facts: list[str] = []
    matches = [_SURFACE_LABEL_RE.fullmatch(label) for label in declared]
    if any(match is None for match in matches):
        facts.append("DECLARATION_MALFORMED")
    if len(set(declared)) != len(declared):
        facts.append("DECLARATION_DUPLICATE")
    surfaces = {match.group(1) for match in matches if match is not None}
    if len(surfaces) > 1:
        facts.append("DECLARATION_MIXED")
    if any(surface != NONE_SURFACE and surface not in SUPPORTED_SURFACES for surface in surfaces):
        facts.append("SURFACE_UNSUPPORTED")
    if facts:
        return facts, None
    return [], surfaces.pop()


def _read_records(reader: Reader, *, workspace_root: str | os.PathLike[str], shipment_id: object) -> _Records:
    """Classes 2 and 3 for one shipment, read through ``reader``.

    The backlog root is one of two fixed names under ``workspace_root``,
    probed with ``os.path.isdir`` (a probe is not a file claim); no
    environment variable or other module selects it. Facts are collected in
    encounter order without short-circuiting across members; the first
    read-limit error stops every further read (FI-5).
    """
    base = os.fspath(workspace_root)
    roots = [name for name in BACKLOG_ROOT_NAMES if os.path.isdir(os.path.join(base, name))]
    facts: list[str] = []
    backlog_root: str | None = None
    if not roots:
        facts.append("BACKLOG_ROOT_NOT_FOUND")
    elif len(roots) > 1:
        facts.append("BACKLOG_ROOT_AMBIGUOUS")
    else:
        backlog_root = roots[0]
    valid_id = shipment_id if isinstance(shipment_id, str) and SHIPMENT_ID_RE.fullmatch(shipment_id) else None
    if valid_id is None:
        facts.append("SHIPMENT_ID_INVALID")

    def done(read_limit: ReadLimitHit | None = None, declarations: Sequence[Declaration] = ()) -> _Records:
        ordered = tuple(sorted(declarations, key=lambda item: task_id_sort_key(item.member_id)))
        surface_ids = tuple(sorted({item.surface_id for item in ordered if item.surface_id in SUPPORTED_SURFACES}))
        return _Records(backlog_root, valid_id, tuple(facts), ordered, surface_ids, read_limit)

    if facts or backlog_root is None or valid_id is None:
        return done()

    status, record = _read_record(reader, backlog_root, valid_id, ReadStage.SHIPMENT_CANDIDATE)
    if isinstance(record, ReadLimitHit):
        return done(record)
    if not isinstance(record, dict):
        facts.append(_SHIPMENT_CODES[status])
        return done()

    custom_fields = record.get("custom_fields")
    items = custom_fields.get("items") if isinstance(custom_fields, dict) else None
    if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
        facts.append("MEMBERS_INVALID")
    elif not items:
        facts.append("MEMBERS_EMPTY")
    elif len(items) > MAX_MEMBERS:
        facts.append("MEMBERS_TOO_MANY")
    if facts:
        return done()

    lookups: list[str] = []
    for item in items:
        match = MEMBER_ID_RE.fullmatch(item)
        if match is None:
            facts.append("MEMBER_ID_INVALID")
        elif match.group(2) not in ("F", "T"):
            facts.append("MEMBER_KIND_UNSUPPORTED")
        elif item in lookups:
            facts.append("MEMBER_DUPLICATE")
        else:
            lookups.append(item)
    if not any(item.endswith("-T") for item in lookups):
        facts.append("NO_TASK_MEMBERS")

    declarations: list[Declaration] = []
    for item in lookups:
        status, member = _read_record(reader, backlog_root, item, ReadStage.MEMBER_CANDIDATE)
        if isinstance(member, ReadLimitHit):
            return done(member, declarations)
        if not isinstance(member, dict):
            facts.append(_MEMBER_CODES[status])
            continue
        labels = member.get("labels")
        if labels is None:
            labels = []
        if not isinstance(labels, list) or any(not isinstance(label, str) for label in labels):
            facts.append("MEMBER_RECORD_INVALID")
            continue
        if item.endswith("-F"):
            if any(label == _SURFACE_LABEL or label.startswith(_SURFACE_LABEL + ":") for label in labels):
                facts.append("FEATURE_DECLARES_SURFACE")
            continue
        issues, surface = _declaration(labels)
        facts.extend(issues)
        if surface is not None:
            declarations.append(Declaration(item, surface))
    return done(None, declarations)

# --- B3 (188.003-T) RED-phase stubs -----------------------------------------

_B3 = "AHLC_B3_MANIFEST_CLASSIFY"


@dataclass(frozen=True)
class _Classification:
    global_code: str | None
    rows: tuple[SurfaceRow, ...]
    read_limit: ReadLimitHit | None

    @property
    def reason_code(self) -> str | None:
        raise NotImplementedError(f"{_B3}:reason_code")


def _classify_surfaces(reader: Reader, *, surface_ids: Sequence[str]) -> _Classification:
    workspace = reader._roots[TrustRoot.WORKSPACE]  # RED stub only: the request's workspace name
    raise NotImplementedError(f"{_B3}:{os.path.basename(workspace or '')}")
