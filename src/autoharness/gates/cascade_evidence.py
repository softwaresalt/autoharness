"""Read-only CASCADE close-evidence record contract (192-F, plan unit A1).

This module is the single, read-only evidence contract shared by the
closure-evidence gate (A4/A4b) and the ``shipment_close`` command. It owns:

* :data:`EVIDENCE_SCHEMA_VERSION` and :func:`build_evidence_path`, which builds
  ``docs/closure/evidence/{S}-{F}-close-evidence.json`` for one
  ``(shipment_id, feature_id)`` pair;
* :func:`validate_evidence_record`, the single validator. ``close_path`` is the
  *selected* close path, never the classifier verdict;
* :func:`redact`, the one redaction function every persisted free-text field
  goes through;
* :class:`CascadeEvidenceError`, the single error type;
* the pure record codec (``*_to_record`` / ``*_from_record``) that every
  writer and every comparison uses, so one encoder and one decoder exist per
  record field (A1d: ``declared_status`` and observation entries; A1e:
  ``engine_semantics`` and ``close_path_selection``; A1f: the
  linked-deliberation disposition snapshot).

Layering (AS-F07): this module never writes, never spawns a subprocess, never
imports the command package and defines no exit codes.

Selection consistency (re-plan R1/R2, D4a): the validator re-assesses the
recorded raw engine inputs with
:func:`~autoharness.gates.shipment_closure.assess_cascade_engine_semantics` and
re-selects with :func:`~autoharness.gates.shipment_closure.select_close_path`,
so a hand-edited verdict or selection is rejected.
"""

from __future__ import annotations

import datetime
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from autoharness.gates.closure_contract import (
    ClosureContractError,
    assert_path_within_workspace,
    validate_closure_id,
)
from autoharness.gates.shipment_closure import (
    PLANNED_ARCHIVE,
    ClosePath,
    ClosePathDecision,
    DeliberationRecordSnapshot,
    DispositionReadFailure,
    EngineSemanticsDecision,
    EngineSemanticsVerdict,
    LinkedDeliberationDisposition,
    LinkedDeliberationDispositionPlan,
    LinkedDeliberationOutcome,
    UnresolvedDeliberationReference,
    assess_cascade_engine_semantics,
    select_close_path,
)

EVIDENCE_SCHEMA_VERSION: Final = 1
EVIDENCE_DIR: Final = Path("docs") / "closure" / "evidence"
EVIDENCE_FILENAME_TEMPLATE: Final = "{shipment_id}-{feature_id}-close-evidence.json"

REDACTION_MARKER: Final = "[REDACTED]"

_CLOSE_PATHS: Final = frozenset({"cascade", "safe_close"})
_PHASES: Final = frozenset({"pre_close", "invoking", "post_close"})
_CLASSIFIER_VERDICTS: Final = {"CASCADE": ClosePath.CASCADE, "SAFE_CLOSE": ClosePath.SAFE_CLOSE}
_ENGINE_VERDICTS: Final = frozenset(verdict.value for verdict in EngineSemanticsVerdict)
_MUTATION_STATES: Final = frozenset({"none", "completed", "indeterminate"})
_LOCATIONS: Final = frozenset({"queue", "archive", "missing"})
_BACKLOG_ROOTS: Final = frozenset({".backlog", ".backlogit"})

_SHA256_PATTERN: Final = re.compile(r"[0-9a-f]{64}")
_RUN_ID_PATTERN: Final = re.compile(r"[0-9a-f]{32}")
_DRIVE_PREFIX_PATTERN: Final = re.compile(r"[A-Za-z]:")

# Keys whose list values are ID lists, sorted on serialization (Principle IX).
_ID_LIST_KEYS: Final = frozenset(
    {
        "qualifying_feature_ids",
        "linking_member_ids",
        "referrer_ids",
        "archived_ids",
        "returned_ids",
        "allowed_ids",
        "required_ids",
        "unexpected_archived",
        "missing_required",
    }
)

# ---------------------------------------------------------------------------
# Redaction (re-plan cycle-1 R6, R17)
# ---------------------------------------------------------------------------

_CREDENTIAL_KEYS: Final = (
    "client_secret",
    "refresh_token",
    "access_token",
    "api_key",
    "apikey",
    "password",
    "secret",
    "token",
)
_CREDENTIAL_KEY_ALTERNATION: Final = "|".join(_CREDENTIAL_KEYS)

_REDACTION_RULES: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    # Authorization header values (bearer or basic scheme; the scheme is kept).
    (
        re.compile(
            r"(\bauthorization\b[\"']?\s*[:=]\s*[\"']?(?:bearer|basic)\s+)[^\s\"',;]+",
            re.IGNORECASE,
        ),
        rf"\g<1>{REDACTION_MARKER}",
    ),
    (re.compile(r"(\bbearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), rf"\g<1>{REDACTION_MARKER}"),
    # Quoted JSON credential keys: the quoted value is redacted through its
    # closing quote and the key is kept.
    (
        re.compile(
            rf"(\"(?:{_CREDENTIAL_KEY_ALTERNATION})\"\s*:\s*)\"(?:[^\"\\]|\\.)*\"",
            re.IGNORECASE,
        ),
        rf'\g<1>"{REDACTION_MARKER}"',
    ),
    # key=value credential pairs over the same shared key set.
    (
        re.compile(
            rf"(\b(?:{_CREDENTIAL_KEY_ALTERNATION})\s*=\s*)[^\s&\"',;]+",
            re.IGNORECASE,
        ),
        rf"\g<1>{REDACTION_MARKER}",
    ),
    # GitHub tokens.
    (re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"), REDACTION_MARKER),
    # sk- style API keys.
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"), REDACTION_MARKER),
)


class CascadeEvidenceError(Exception):
    """The single error type of the close-evidence contract."""


# ---------------------------------------------------------------------------
# Record codec: declared_status and observation entries (plan unit A1d)
# ---------------------------------------------------------------------------


class _DeclaredStatusMissing:
    """Sentinel for a frontmatter with no ``status`` key at all."""

    _instance: _DeclaredStatusMissing | None = None

    def __new__(cls) -> _DeclaredStatusMissing:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "DECLARED_STATUS_MISSING"


DECLARED_STATUS_MISSING: Final = _DeclaredStatusMissing()


@dataclass(frozen=True)
class OpaqueStatus:
    """The decoded form of an ``other`` tag: only the original type name is kept."""

    type_name: str


@dataclass(frozen=True)
class ObservationEntry:
    """One safe-close observation-set entry (``location: missing`` has null fields)."""

    id: str
    path: str | None
    location: str
    sha256: str | None
    declared_status: object


_STATUS_TAGS: Final = frozenset(
    {"missing", "null", "bool", "int", "float", "date", "datetime", "list", "mapping", "other"}
)
_OBSERVATION_KEYS: Final = frozenset({"id", "path", "location", "sha256", "declared_status"})


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def declared_status_to_record(value: object) -> str | dict[str, object]:
    """Encode a parsed frontmatter scalar canonically (re-plan cycle-1 R8).

    An exact ``str`` is stored as the JSON string. Every other value is a
    tagged object ``{"type": tag, "value": canonical text or null}``, so a YAML
    date never compares equal to a quoted date string.
    """

    if type(value) is str:
        return value
    if value is DECLARED_STATUS_MISSING:
        return {"type": "missing", "value": None}
    if value is None:
        return {"type": "null", "value": None}
    if type(value) is bool:
        return {"type": "bool", "value": "true" if value else "false"}
    if type(value) is int:
        return {"type": "int", "value": str(value)}
    if type(value) is float:
        return {"type": "float", "value": repr(value)}
    if type(value) is datetime.datetime:
        return {"type": "datetime", "value": value.isoformat()}
    if type(value) is datetime.date:
        return {"type": "date", "value": value.isoformat()}
    if type(value) is list:
        return {"type": "list", "value": _canonical_json([declared_status_to_record(item) for item in value])}
    if type(value) is dict:
        encoded = {str(key): declared_status_to_record(item) for key, item in value.items()}
        return {"type": "mapping", "value": _canonical_json(encoded)}
    if type(value) is OpaqueStatus:
        return {"type": "other", "value": value.type_name}
    return {"type": "other", "value": type(value).__name__}


def _decode_tagged(tag: str, text: object) -> object:
    if tag == "missing":
        return DECLARED_STATUS_MISSING
    if tag == "null":
        return None
    if type(text) is not str:
        raise CascadeEvidenceError(f"declared_status tag {tag!r} requires a string value")
    if tag == "bool":
        if text not in ("true", "false"):
            raise CascadeEvidenceError(f"declared_status bool value {text!r} is not 'true' or 'false'")
        return text == "true"
    if tag == "int":
        return int(text)
    if tag == "float":
        return float(text)
    if tag == "date":
        return datetime.date.fromisoformat(text)
    if tag == "datetime":
        return datetime.datetime.fromisoformat(text)
    if tag == "list":
        items = json.loads(text)
        if type(items) is not list:
            raise CascadeEvidenceError("declared_status list value is not a JSON list")
        return [declared_status_from_record(item) for item in items]
    if tag == "mapping":
        items = json.loads(text)
        if type(items) is not dict:
            raise CascadeEvidenceError("declared_status mapping value is not a JSON object")
        return {key: declared_status_from_record(item) for key, item in items.items()}
    if text == "":
        raise CascadeEvidenceError("declared_status other value must name a type")
    return OpaqueStatus(text)


def declared_status_from_record(record_value: object) -> object:
    """Decode a canonical ``declared_status`` record value.

    Raises :class:`CascadeEvidenceError` on an unknown tag, a malformed tagged
    object, a non-object non-string value, or any non-canonical encoding, so
    ``declared_status_to_record(declared_status_from_record(r)) == r`` holds
    for every accepted ``r``.
    """

    if type(record_value) is str:
        return record_value
    if not isinstance(record_value, Mapping):
        raise CascadeEvidenceError(
            f"declared_status must be a string or a tagged object (got {type(record_value).__name__})"
        )
    if set(record_value) != {"type", "value"}:
        raise CascadeEvidenceError(
            f"declared_status tagged object must have exactly 'type' and 'value' (got {sorted(map(str, record_value))})"
        )
    tag = record_value["type"]
    if tag not in _STATUS_TAGS:
        raise CascadeEvidenceError(f"declared_status has unknown tag {tag!r}")
    text = record_value["value"]
    if tag in ("missing", "null") and text is not None:
        raise CascadeEvidenceError(f"declared_status tag {tag!r} requires a null value")
    try:
        decoded = _decode_tagged(tag, text)
    except CascadeEvidenceError:
        raise
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise CascadeEvidenceError(f"declared_status {tag!r} value {text!r} is malformed: {exc}") from exc
    if declared_status_to_record(decoded) != dict(record_value):
        raise CascadeEvidenceError(f"declared_status {tag!r} value {text!r} is not canonical")
    return decoded


def observation_entry_to_record(entry: ObservationEntry) -> dict[str, object]:
    """Encode one observation-set entry; ``location: missing`` keeps every other field null."""

    if type(entry) is not ObservationEntry:
        raise CascadeEvidenceError(f"expected an ObservationEntry (got {type(entry).__name__})")
    if entry.location == "missing":
        if entry.path is not None or entry.sha256 is not None or entry.declared_status is not None:
            raise CascadeEvidenceError(
                f"observation entry {entry.id!r}: a missing entry has null path, sha256 and declared_status"
            )
        status: object = None
    else:
        status = declared_status_to_record(entry.declared_status)
    record = {
        "id": entry.id,
        "path": entry.path,
        "location": entry.location,
        "sha256": entry.sha256,
        "declared_status": status,
    }
    observation_entry_from_record(record)  # one decoder: reject what it would reject
    return record


def observation_entry_from_record(record: object) -> ObservationEntry:
    """Decode one observation-set entry record; raises :class:`CascadeEvidenceError`."""

    if not isinstance(record, Mapping):
        raise CascadeEvidenceError("observation entry must be an object")
    keys = set(record)
    if keys != _OBSERVATION_KEYS:
        raise CascadeEvidenceError(
            f"observation entry keys must be {sorted(_OBSERVATION_KEYS)} (got {sorted(map(str, keys))})"
        )
    entry_id = record["id"]
    if type(entry_id) is not str or entry_id == "":
        raise CascadeEvidenceError("observation entry id must be a non-empty string")
    location = record["location"]
    if location not in _LOCATIONS:
        raise CascadeEvidenceError(f"observation entry {entry_id!r}: unknown location {location!r}")
    if location == "missing":
        if record["path"] is not None or record["sha256"] is not None or record["declared_status"] is not None:
            raise CascadeEvidenceError(
                f"observation entry {entry_id!r}: a missing entry has null path, sha256 and declared_status"
            )
        return ObservationEntry(id=entry_id, path=None, location=location, sha256=None, declared_status=None)
    path = record["path"]
    if type(path) is not str or path == "":
        raise CascadeEvidenceError(f"observation entry {entry_id!r}: path must be a non-empty string")
    sha256 = record["sha256"]
    if not _is_sha256(sha256):
        raise CascadeEvidenceError(f"observation entry {entry_id!r}: sha256 must be a lowercase hex digest")
    return ObservationEntry(
        id=entry_id,
        path=path,
        location=location,
        sha256=sha256,
        declared_status=declared_status_from_record(record["declared_status"]),
    )


# ---------------------------------------------------------------------------
# Record codec: engine_semantics and close_path_selection (plan unit A1e)
# ---------------------------------------------------------------------------

_ENGINE_KEYS: Final = frozenset(
    {"verdict", "reason", "probed_version", "minor_line", "probed_commit", "probe_surface", "invocation_surface"}
)
_SELECTION_KEYS: Final = frozenset({"selected_close_path", "reason"})


def engine_semantics_to_record(
    decision: EngineSemanticsDecision, *, invocation_surface: str
) -> dict[str, object]:
    """Encode an ``EngineSemanticsDecision`` plus its ``invocation_surface`` input.

    Every value is stored verbatim (re-plan cycle-1 R6), so re-assessment of
    the recorded inputs reproduces the recorded outputs. ``minor_line`` is
    ``[major, minor]`` or ``None``. There is no probe excerpt (cycle-1 R7).
    """

    if type(decision) is not EngineSemanticsDecision:
        raise CascadeEvidenceError(f"expected an EngineSemanticsDecision (got {type(decision).__name__})")
    record = {
        "verdict": decision.verdict.value if isinstance(decision.verdict, EngineSemanticsVerdict) else decision.verdict,
        "reason": decision.reason,
        "probed_version": decision.probed_version,
        "minor_line": list(decision.minor_line) if decision.minor_line is not None else None,
        "probed_commit": decision.probed_commit,
        "probe_surface": decision.probe_surface,
        "invocation_surface": invocation_surface,
    }
    engine_semantics_from_record(record)  # one decoder: reject what it would reject
    return record


def engine_semantics_from_record(record: object) -> tuple[EngineSemanticsDecision, str]:
    """Decode an ``engine_semantics`` record into ``(decision, invocation_surface)``.

    Raises :class:`CascadeEvidenceError` on a missing or unknown key, an
    unknown ``verdict``, a ``minor_line`` that is neither ``None`` nor a list
    of two integers, or a wrong-typed value.
    """

    if not isinstance(record, Mapping):
        raise CascadeEvidenceError("engine_semantics must be an object")
    keys = set(record)
    if keys != _ENGINE_KEYS:
        raise CascadeEvidenceError(
            f"engine_semantics keys must be {sorted(_ENGINE_KEYS)} (got {sorted(map(str, keys))})"
        )
    verdict = record["verdict"]
    if verdict not in _ENGINE_VERDICTS or type(verdict) is not str:
        raise CascadeEvidenceError(f"engine_semantics has unknown verdict {verdict!r}")
    if type(record["reason"]) is not str:
        raise CascadeEvidenceError("engine_semantics.reason must be a string")
    for key in ("probed_version", "probed_commit", "probe_surface"):
        if record[key] is not None and type(record[key]) is not str:
            raise CascadeEvidenceError(f"engine_semantics.{key} must be a string or null")
    if type(record["invocation_surface"]) is not str:
        raise CascadeEvidenceError("engine_semantics.invocation_surface must be a string")
    minor_line = record["minor_line"]
    if minor_line is not None and not (
        type(minor_line) is list and len(minor_line) == 2 and all(type(part) is int for part in minor_line)
    ):
        raise CascadeEvidenceError(f"engine_semantics.minor_line must be null or two integers (got {minor_line!r})")
    decision = EngineSemanticsDecision(
        verdict=EngineSemanticsVerdict(verdict),
        reason=record["reason"],
        probed_version=record["probed_version"],
        minor_line=(minor_line[0], minor_line[1]) if minor_line is not None else None,
        probe_surface=record["probe_surface"],
        probed_commit=record["probed_commit"],
    )
    return decision, record["invocation_surface"]


def close_path_selection_to_record(selection: tuple[ClosePath, str]) -> dict[str, object]:
    """Encode the ``(ClosePath, reason)`` result of ``select_close_path``."""

    if type(selection) is not tuple or len(selection) != 2 or type(selection[0]) is not ClosePath:
        raise CascadeEvidenceError("expected a (ClosePath, reason) selection")
    record = {"selected_close_path": selection[0].value, "reason": selection[1]}
    close_path_selection_from_record(record)
    return record


def close_path_selection_from_record(record: object) -> tuple[ClosePath, str]:
    """Decode a ``close_path_selection`` record; raises :class:`CascadeEvidenceError`."""

    if not isinstance(record, Mapping):
        raise CascadeEvidenceError("close_path_selection must be an object")
    keys = set(record)
    if keys != _SELECTION_KEYS:
        raise CascadeEvidenceError(
            f"close_path_selection keys must be {sorted(_SELECTION_KEYS)} (got {sorted(map(str, keys))})"
        )
    selected = record["selected_close_path"]
    if type(selected) is not str or selected not in _CLOSE_PATHS:
        raise CascadeEvidenceError(f"close_path_selection has unknown selected_close_path {selected!r}")
    if type(record["reason"]) is not str:
        raise CascadeEvidenceError("close_path_selection.reason must be a string")
    return ClosePath(selected), record["reason"]


# ---------------------------------------------------------------------------
# Record codec: linked-deliberation disposition snapshot (plan unit A1f)
# ---------------------------------------------------------------------------

_PLAN_KEYS: Final = frozenset({"dispositions", "unresolved_references", "read_failures", "planning_error"})
_DISPOSITION_KEYS: Final = frozenset(
    {
        "deliberation_id",
        "outcome",
        "reason_code",
        "path",
        "link_kinds",
        "linking_member_ids",
        "referrer_ids",
        "declared_status",
        "records",
    }
)
_SNAPSHOT_RECORD_KEYS: Final = frozenset({"path", "declared_status", "sha256"})
_UNRESOLVED_KEYS: Final = frozenset({"id", "reason_code"})
_READ_FAILURE_KEYS: Final = frozenset({"path", "reason_code"})


def _require_keys(record: object, expected: frozenset[str], where: str) -> Mapping[str, object]:
    if not isinstance(record, Mapping):
        raise CascadeEvidenceError(f"{where} must be an object")
    keys = set(record)
    if keys != expected:
        raise CascadeEvidenceError(f"{where} keys must be {sorted(expected)} (got {sorted(map(str, keys))})")
    return record


def _require_list(value: object, where: str) -> list[object]:
    if type(value) is not list:
        raise CascadeEvidenceError(f"{where} must be a list")
    return value


def _require_str_list(value: object, where: str) -> tuple[str, ...]:
    items = _require_list(value, where)
    if not all(type(item) is str for item in items):
        raise CascadeEvidenceError(f"{where} must be a list of strings")
    return tuple(items)


def _require_str(value: object, where: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if type(value) is not str:
        raise CascadeEvidenceError(f"{where} must be a string{' or null' if nullable else ''}")
    return value


def _outcome_from_record(value: object, where: str) -> object:
    outcome = _require_str(value, where)
    if outcome == "":
        raise CascadeEvidenceError(f"{where} must be a non-empty string")
    try:
        return LinkedDeliberationOutcome(outcome)
    except ValueError:
        # The planned "archive" and any other string round-trip verbatim; the
        # outcome vocabulary is the A1c validator's concern, not the codec's.
        return outcome


def disposition_plan_to_record(plan: LinkedDeliberationDispositionPlan) -> dict[str, object]:
    """Encode four of the six plan fields (re-plan cycle-1 R14).

    ``shipment_id`` and ``engine`` are dropped: they equal the record's
    top-level ``shipment_id`` and ``pre_close.engine_semantics``. Every
    ``declared_status`` goes through :func:`declared_status_to_record`, and ID
    lists are sorted.
    """

    if type(plan) is not LinkedDeliberationDispositionPlan:
        raise CascadeEvidenceError(f"expected a LinkedDeliberationDispositionPlan (got {type(plan).__name__})")
    record = {
        "dispositions": [
            {
                "deliberation_id": disposition.deliberation_id,
                "outcome": str(getattr(disposition.outcome, "value", disposition.outcome)),
                "reason_code": disposition.reason_code,
                "path": disposition.path,
                "link_kinds": list(disposition.link_kinds),
                "linking_member_ids": sorted(disposition.linking_member_ids),
                "referrer_ids": sorted(disposition.referrer_ids),
                "declared_status": declared_status_to_record(disposition.declared_status),
                "records": [
                    {
                        "path": snapshot.path,
                        "declared_status": declared_status_to_record(snapshot.declared_status),
                        "sha256": snapshot.sha256,
                    }
                    for snapshot in disposition.records
                ],
            }
            for disposition in plan.dispositions
        ],
        "unresolved_references": [
            {"id": reference.id, "reason_code": reference.reason_code} for reference in plan.unresolved_references
        ],
        "read_failures": [
            {"path": failure.path, "reason_code": failure.reason_code} for failure in plan.read_failures
        ],
        "planning_error": plan.planning_error,
    }
    disposition_plan_from_record(record, shipment_id=plan.shipment_id, engine=plan.engine)
    return record


def disposition_plan_from_record(
    record: object, *, shipment_id: str | None, engine: object
) -> LinkedDeliberationDispositionPlan:
    """Decode a disposition snapshot, restoring ``shipment_id`` and ``engine``.

    Raises :class:`CascadeEvidenceError` on a missing or unknown key, a
    wrong-typed value, or a malformed tagged ``declared_status``.
    """

    plan = _require_keys(record, _PLAN_KEYS, "linked_deliberation_disposition")
    dispositions = []
    for index, raw in enumerate(_require_list(plan["dispositions"], "dispositions")):
        where = f"dispositions[{index}]"
        entry = _require_keys(raw, _DISPOSITION_KEYS, where)
        snapshots = []
        for record_index, raw_snapshot in enumerate(_require_list(entry["records"], f"{where}.records")):
            snapshot_where = f"{where}.records[{record_index}]"
            snapshot = _require_keys(raw_snapshot, _SNAPSHOT_RECORD_KEYS, snapshot_where)
            if not _is_sha256(snapshot["sha256"]):
                raise CascadeEvidenceError(f"{snapshot_where}.sha256 must be a lowercase hex digest")
            snapshots.append(
                DeliberationRecordSnapshot(
                    path=_require_str(snapshot["path"], f"{snapshot_where}.path"),
                    declared_status=declared_status_from_record(snapshot["declared_status"]),
                    sha256=snapshot["sha256"],
                )
            )
        deliberation_id = _require_str(entry["deliberation_id"], f"{where}.deliberation_id")
        if deliberation_id == "":
            raise CascadeEvidenceError(f"{where}.deliberation_id must be a non-empty string")
        dispositions.append(
            LinkedDeliberationDisposition(
                deliberation_id=deliberation_id,
                outcome=_outcome_from_record(entry["outcome"], f"{where}.outcome"),
                reason_code=_require_str(entry["reason_code"], f"{where}.reason_code"),
                link_kinds=_require_str_list(entry["link_kinds"], f"{where}.link_kinds"),
                linking_member_ids=_require_str_list(entry["linking_member_ids"], f"{where}.linking_member_ids"),
                records=tuple(snapshots),
                declared_status=declared_status_from_record(entry["declared_status"]),
                referrer_ids=_require_str_list(entry["referrer_ids"], f"{where}.referrer_ids"),
                path=_require_str(entry["path"], f"{where}.path", nullable=True),
            )
        )
    unresolved = []
    for index, raw in enumerate(_require_list(plan["unresolved_references"], "unresolved_references")):
        where = f"unresolved_references[{index}]"
        entry = _require_keys(raw, _UNRESOLVED_KEYS, where)
        unresolved.append(
            UnresolvedDeliberationReference(
                id=_require_str(entry["id"], f"{where}.id"),
                reason_code=_require_str(entry["reason_code"], f"{where}.reason_code"),
            )
        )
    failures = []
    for index, raw in enumerate(_require_list(plan["read_failures"], "read_failures")):
        where = f"read_failures[{index}]"
        entry = _require_keys(raw, _READ_FAILURE_KEYS, where)
        failures.append(
            DispositionReadFailure(
                path=_require_str(entry["path"], f"{where}.path", nullable=True),
                reason_code=_require_str(entry["reason_code"], f"{where}.reason_code"),
            )
        )
    return LinkedDeliberationDispositionPlan(
        shipment_id=shipment_id,
        engine=engine,
        dispositions=tuple(dispositions),
        unresolved_references=tuple(unresolved),
        read_failures=tuple(failures),
        planning_error=_require_str(plan["planning_error"], "planning_error", nullable=True),
    )

def redact(text: str) -> tuple[str, bool]:
    """Return ``(redacted_text, redaction_applied)`` for one free-text value.

    Covers bearer/basic ``Authorization`` values; ``key=value`` pairs and
    quoted JSON keys over one shared, case-insensitive credential key set;
    GitHub ``gh[pousr]_`` and ``github_pat_`` tokens; and ``sk-`` style keys.
    ``redaction_applied`` is ``True`` only when the text changed. Because the
    result is a tuple, a redaction-neutrality check is written
    ``redact(x)[0] == x``.
    """

    if type(text) is not str:
        raise CascadeEvidenceError(f"redact expects a str, got {type(text).__name__}")
    result = text
    for pattern, replacement in _REDACTION_RULES:
        result = pattern.sub(replacement, result)
    return result, result != text


# ---------------------------------------------------------------------------
# Path
# ---------------------------------------------------------------------------


def build_evidence_path(
    workspace_root: Path | str, shipment_id: str, feature_id: str
) -> Path:
    """Build ``docs/closure/evidence/{S}-{F}-close-evidence.json`` under ``workspace_root``.

    Both identifiers are validated with the closure-contract grammar before any
    join, and the directory and output are asserted inside the resolved
    workspace. Never creates a directory or writes a file. Raises
    :class:`CascadeEvidenceError`.
    """

    try:
        validated_shipment = validate_closure_id(shipment_id, field="shipment_id")
        validated_feature = validate_closure_id(feature_id, field="feature_id")
        root = Path(workspace_root).resolve()
        directory = assert_path_within_workspace(EVIDENCE_DIR, workspace_root=root)
        filename = EVIDENCE_FILENAME_TEMPLATE.format(
            shipment_id=validated_shipment, feature_id=validated_feature
        )
        output = assert_path_within_workspace(directory / filename, workspace_root=root)
    except ClosureContractError as exc:
        raise CascadeEvidenceError(str(exc)) from exc
    if output.parent != directory:
        raise CascadeEvidenceError(
            f"evidence path '{output}' does not lie directly in '{directory}'"
        )
    return output


# ---------------------------------------------------------------------------
# Serialization (Principle IX)
# ---------------------------------------------------------------------------


def _canonicalize(value: object, key: str | None = None) -> object:
    if isinstance(value, Mapping):
        return {item_key: _canonicalize(item, item_key) for item_key, item in value.items()}
    if isinstance(value, list):
        items = [_canonicalize(item) for item in value]
        if key in _ID_LIST_KEYS and all(type(item) is str for item in items):
            return sorted(items)
        return items
    return value


def _serialize_evidence_record(record: Mapping[str, object]) -> str:
    """Serialize ``record`` under the A1 rule: sorted keys and ID lists, LF, one trailing newline."""

    text = json.dumps(_canonicalize(record), sort_keys=True, indent=2, ensure_ascii=False)
    return text + "\n"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class _Missing:
    pass


_MISSING: Final = _Missing()


def _is_str(value: object) -> bool:
    return type(value) is str


def _is_nonempty_str(value: object) -> bool:
    return type(value) is str and value != ""


def _is_int(value: object) -> bool:
    return type(value) is int


def _is_bool(value: object) -> bool:
    return type(value) is bool


def _is_str_list(value: object) -> bool:
    return type(value) is list and all(type(item) is str for item in value)


def _is_sha256(value: object) -> bool:
    return type(value) is str and _SHA256_PATTERN.fullmatch(value) is not None


def _is_declared_status(value: object) -> bool:
    # One decoder (A1d): a value is well-typed only if the codec accepts it.
    try:
        declared_status_from_record(value)
    except CascadeEvidenceError:
        return False
    return True


class _Checker:
    """Collects validation errors with a dotted location prefix."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.roots: set[str] = set()

    def fail(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def mapping(self, parent: Mapping[str, object], key: str, where: str) -> Mapping[str, object] | None:
        value = parent.get(key, _MISSING)
        if value is _MISSING:
            self.fail(f"{where}.{key}", "required key is missing")
            return None
        if not isinstance(value, Mapping):
            self.fail(f"{where}.{key}", "must be an object")
            return None
        return value

    def field(self, parent: Mapping[str, object], key: str, where: str, predicate, expected: str) -> object:
        value = parent.get(key, _MISSING)
        if value is _MISSING:
            self.fail(f"{where}.{key}", "required key is missing")
            return _MISSING
        if not predicate(value):
            self.fail(f"{where}.{key}", f"must be {expected}")
            return _MISSING
        return value

    def items(self, parent: Mapping[str, object], key: str, where: str) -> list[Mapping[str, object]]:
        value = parent.get(key, _MISSING)
        if value is _MISSING:
            self.fail(f"{where}.{key}", "required key is missing")
            return []
        if type(value) is not list:
            self.fail(f"{where}.{key}", "must be a list")
            return []
        entries = []
        for index, entry in enumerate(value):
            if not isinstance(entry, Mapping):
                self.fail(f"{where}.{key}[{index}]", "must be an object")
                continue
            entries.append(entry)
        return entries

    def record_path(self, value: object, where: str, *, nullable: bool) -> None:
        """Textual record-path rule (re-plan cycle-1 R12); runs before any read."""

        if value is None:
            if not nullable:
                self.fail(where, "path must not be null here")
            return
        if type(value) is not str or value == "":
            self.fail(where, "path must be a non-empty string or null")
            return
        if value.startswith(("/", "\\")):
            self.fail(where, f"path {value!r} is absolute or a UNC path")
            return
        if _DRIVE_PREFIX_PATTERN.match(value):
            self.fail(where, f"path {value!r} carries a drive prefix")
            return
        if "\\" in value:
            self.fail(where, f"path {value!r} is not a POSIX path")
            return
        segments = value.split("/")
        if ".." in segments:
            self.fail(where, f"path {value!r} contains a '..' segment")
            return
        if segments[0] not in _BACKLOG_ROOTS:
            self.fail(where, f"path {value!r} is not under the backlog root")
            return
        self.roots.add(segments[0])


def _check_located_entry(
    checker: _Checker, entry: Mapping[str, object], where: str, *, require_id: bool
) -> object:
    """Check ``{location, sha256, declared_status}`` (and ``id``); return ``location``."""

    if require_id:
        checker.field(entry, "id", where, _is_nonempty_str, "a non-empty string")
    location = checker.field(entry, "location", where, lambda v: v in _LOCATIONS, f"one of {sorted(_LOCATIONS)}")
    missing = location == "missing"
    if missing:
        for key in ("sha256", "declared_status"):
            if entry.get(key, _MISSING) is not None:
                checker.fail(f"{where}.{key}", "must be null when location is missing")
    else:
        checker.field(entry, "sha256", where, _is_sha256, "a lowercase SHA-256 hex digest")
        checker.field(entry, "declared_status", where, _is_declared_status, "a declared status")
    return location


def _check_tool(checker: _Checker, record: Mapping[str, object]) -> None:
    tool = checker.mapping(record, "tool", "record")
    if tool is None:
        return
    checker.field(tool, "binary_path", "record.tool", _is_nonempty_str, "a non-empty string")
    checker.field(tool, "binary_sha256", "record.tool", _is_sha256, "a lowercase SHA-256 hex digest")
    checker.field(tool, "version_excerpt", "record.tool", _is_str, "a string")


def _check_selection(checker: _Checker, pre_close: Mapping[str, object], close_path: str) -> None:
    """Re-assess the engine and re-select the close path (re-plan R1/R2, D4a).

    The recorded ``engine_semantics`` and ``close_path_selection`` are decoded
    through the A1e codec (one decoder), re-assessed with
    ``assess_cascade_engine_semantics`` and ``select_close_path``, and compared
    as ``*_to_record`` encodings.
    """

    where = "record.pre_close"
    verdict = checker.field(
        pre_close, "classifier_verdict", where, lambda v: v in _CLASSIFIER_VERDICTS, "CASCADE or SAFE_CLOSE"
    )
    reason = checker.field(pre_close, "classifier_reason", where, _is_str, "a string")
    qualifying = checker.field(pre_close, "qualifying_feature_ids", where, _is_str_list, "a list of strings")
    engine = checker.mapping(pre_close, "engine_semantics", where)
    selection = checker.mapping(pre_close, "close_path_selection", where)

    decoded_engine: EngineSemanticsDecision | None = None
    surface = ""
    if engine is not None:
        try:
            decoded_engine, surface = engine_semantics_from_record(engine)
        except CascadeEvidenceError as exc:
            checker.fail(f"{where}.engine_semantics", str(exc))
        else:
            if surface != "cli":
                checker.fail(f"{where}.engine_semantics.invocation_surface", f"must be 'cli' (got {surface!r})")
    decoded_selection: tuple[ClosePath, str] | None = None
    if selection is not None:
        try:
            decoded_selection = close_path_selection_from_record(selection)
        except CascadeEvidenceError as exc:
            checker.fail(f"{where}.close_path_selection", str(exc))
    if decoded_selection is not None and decoded_selection[0].value != close_path:
        checker.fail(
            f"{where}.close_path_selection.selected_close_path",
            f"record selected {decoded_selection[0].value!r} but is offered for {close_path!r}",
        )

    # Sanitized inputs, unredacted outputs (re-plan cycle-1 R6): compare the
    # text element of redact(), never the tuple.
    neutral_fields = []
    if engine is not None:
        neutral_fields += [
            (f"{where}.engine_semantics.{key}", engine.get(key)) for key in ("probed_version", "probed_commit", "reason")
        ]
    if selection is not None:
        neutral_fields.append((f"{where}.close_path_selection.reason", selection.get("reason")))
    for location, value in neutral_fields:
        if type(value) is str and redact(value)[0] != value:
            checker.fail(location, "value is not redaction-neutral (sanitized input expected)")

    if decoded_engine is None or engine is None:
        return
    fresh = assess_cascade_engine_semantics(
        decoded_engine.probed_version,
        probe_surface=decoded_engine.probe_surface,
        invocation_surface=surface,
        probed_commit=decoded_engine.probed_commit,
    )
    expected_engine = engine_semantics_to_record(fresh, invocation_surface=surface)
    for key, expected in expected_engine.items():
        if engine[key] != expected:
            checker.fail(
                f"{where}.engine_semantics.{key}",
                f"recorded {engine[key]!r} but re-assessment gives {expected!r}",
            )
    if decoded_selection is None or selection is None or _MISSING in (verdict, reason, qualifying):
        return
    classifier = ClosePathDecision(
        close_path=_CLASSIFIER_VERDICTS[verdict],
        reason=reason,
        qualifying_feature_ids=tuple(qualifying),
    )
    expected_selection = close_path_selection_to_record(select_close_path(classifier, fresh))
    if selection["selected_close_path"] != expected_selection["selected_close_path"]:
        checker.fail(
            f"{where}.close_path_selection.selected_close_path",
            f"recorded {selection['selected_close_path']!r} but select_close_path gives "
            f"{expected_selection['selected_close_path']!r}",
        )
    if selection["reason"] != expected_selection["reason"]:
        checker.fail(
            f"{where}.close_path_selection.reason",
            "recorded reason disagrees with select_close_path",
        )

def _check_disposition_paths(checker: _Checker, pre_close: Mapping[str, object]) -> None:
    """Walk the disposition snapshot's path fields (shape rules belong to A1c)."""

    snapshot = pre_close.get("linked_deliberation_disposition")
    if not isinstance(snapshot, Mapping):
        return
    where = "record.pre_close.linked_deliberation_disposition"
    dispositions = snapshot.get("dispositions")
    for index, disposition in enumerate(dispositions if type(dispositions) is list else []):
        if not isinstance(disposition, Mapping):
            checker.fail(f"{where}.dispositions[{index}]", "must be an object")
            continue
        # The planner sets ``path`` only on retained_read_error; it is null on
        # every other outcome and may be null on a read error reported outside
        # the backlog root (A2 then keeps only the reason_code).
        checker.record_path(disposition.get("path"), f"{where}.dispositions[{index}].path", nullable=True)
        records = disposition.get("records")
        for record_index, snapshot_record in enumerate(records if type(records) is list else []):
            if not isinstance(snapshot_record, Mapping):
                checker.fail(f"{where}.dispositions[{index}].records[{record_index}]", "must be an object")
                continue
            checker.record_path(
                snapshot_record.get("path"),
                f"{where}.dispositions[{index}].records[{record_index}].path",
                nullable=False,
            )
    failures = snapshot.get("read_failures")
    for index, failure in enumerate(failures if type(failures) is list else []):
        if not isinstance(failure, Mapping):
            checker.fail(f"{where}.read_failures[{index}]", "must be an object")
            continue
        checker.record_path(failure.get("path"), f"{where}.read_failures[{index}].path", nullable=True)


def _check_pre_close(checker: _Checker, pre_close: Mapping[str, object], close_path: str) -> None:
    where = "record.pre_close"
    _check_selection(checker, pre_close, close_path)
    shipment_record = checker.mapping(pre_close, "shipment_record", where)
    if shipment_record is not None:
        _check_located_entry(checker, shipment_record, f"{where}.shipment_record", require_id=False)
    for index, member in enumerate(checker.items(pre_close, "manifest_members", where)):
        member_where = f"{where}.manifest_members[{index}]"
        _check_located_entry(checker, member, member_where, require_id=True)
        checker.field(member, "artifact_type", member_where, _is_nonempty_str, "a non-empty string")
        checker.field(member, "parent_id", member_where, lambda v: v is None or _is_str(v), "a string or null")
    for index, descendant in enumerate(checker.items(pre_close, "out_of_manifest_descendants", where)):
        _check_located_entry(checker, descendant, f"{where}.out_of_manifest_descendants[{index}]", require_id=True)
    checker.field(pre_close, "captured_at", where, _is_nonempty_str, "a non-empty string")
    _check_disposition_paths(checker, pre_close)
    snapshot = pre_close.get("linked_deliberation_disposition", _MISSING)
    if snapshot is not _MISSING:
        # One decoder (A1f); presence and outcome rules belong to A1c.
        try:
            disposition_plan_from_record(snapshot, shipment_id=None, engine=None)
        except CascadeEvidenceError as exc:
            checker.fail(f"{where}.linked_deliberation_disposition", str(exc))

    if close_path == "safe_close":
        for index, entry in enumerate(checker.items(pre_close, "observation_set", where)):
            entry_where = f"{where}.observation_set[{index}]"
            location = _check_located_entry(checker, entry, entry_where, require_id=True)
            path = entry.get("path", _MISSING)
            if location == "missing" and path is not None:
                checker.fail(f"{entry_where}.path", "must be null when location is missing")
            else:
                checker.record_path(path, f"{entry_where}.path", nullable=location == "missing")
            try:
                observation_entry_from_record(entry)
            except CascadeEvidenceError as exc:
                checker.fail(entry_where, str(exc))
    elif "observation_set" in pre_close:
        checker.fail(f"{where}.observation_set", "is recorded only on a selected SAFE_CLOSE")


def _check_capture(checker: _Checker, capture: Mapping[str, object], where: str) -> None:
    for key in ("total_bytes", "total_lines"):
        checker.field(capture, key, where, lambda v: _is_int(v) and v >= 0, "a non-negative integer")
    checker.field(capture, "sha256", where, _is_sha256, "a lowercase SHA-256 hex digest")
    for key in ("capture_truncated", "redaction_applied"):
        checker.field(capture, key, where, _is_bool, "a boolean")
    checker.field(capture, "excerpt", where, _is_str, "a string")


def _check_cascade(checker: _Checker, record: Mapping[str, object], pre_close: Mapping[str, object] | None) -> None:
    """``cascade`` requirements plus internal consistency (AS-F11)."""

    if record.get("phase") != "post_close":
        checker.fail("record.phase", "a cascade record must be in phase post_close")
    if pre_close is not None:
        if pre_close.get("classifier_verdict") != "CASCADE":
            checker.fail("record.pre_close.classifier_verdict", "a cascade record requires CASCADE")
        engine = pre_close.get("engine_semantics")
        if not isinstance(engine, Mapping) or engine.get("verdict") != EngineSemanticsVerdict.VERIFIED.value:
            checker.fail("record.pre_close.engine_semantics.verdict", "a cascade record requires VERIFIED")

    invocation = checker.mapping(record, "invocation", "record")
    if invocation is not None:
        where = "record.invocation"
        checker.field(invocation, "argv_redacted", where, _is_str_list, "a list of strings")
        for key in ("started_at", "finished_at"):
            checker.field(invocation, key, where, _is_nonempty_str, "a non-empty string")
        exit_code = checker.field(invocation, "exit_code", where, lambda v: v is None or _is_int(v), "an integer or null")
        if exit_code is not _MISSING and exit_code != 0:
            checker.fail(f"{where}.exit_code", f"a passing cascade requires exit code 0 (got {exit_code!r})")
        timed_out = checker.field(invocation, "timed_out", where, _is_bool, "a boolean")
        if timed_out is True:
            checker.fail(f"{where}.timed_out", "a passing cascade cannot have timed out")
        state = checker.field(
            invocation, "mutation_state", where, lambda v: v in _MUTATION_STATES, f"one of {sorted(_MUTATION_STATES)}"
        )
        if state is not _MISSING and state != "completed":
            checker.fail(f"{where}.mutation_state", f"a passing cascade requires completed (got {state!r})")
        for stream in ("stdout", "stderr"):
            capture = checker.mapping(invocation, stream, where)
            if capture is not None:
                _check_capture(checker, capture, f"{where}.{stream}")

    post_close = checker.mapping(record, "post_close", "record")
    if post_close is None:
        return
    where = "record.post_close"
    if post_close.get("parse_error") is not None:
        checker.fail(f"{where}.parse_error", "a passing cascade must have a parsed result")
    parsed = checker.mapping(post_close, "parsed_result", where)
    if parsed is not None:
        parsed_where = f"{where}.parsed_result"
        checker.field(parsed, "shipment_status", parsed_where, _is_str, "a string")
        checker.field(parsed, "archived_ids", parsed_where, _is_str_list, "a list of strings")
        returned = checker.field(parsed, "returned_ids", parsed_where, _is_str_list, "a list of strings")
        if returned is not _MISSING and returned:
            checker.fail(f"{parsed_where}.returned_ids", "must be empty")
        checker.field(parsed, "commit_sha", parsed_where, lambda v: v is None or _is_str(v), "a string or null")
    for key in ("shipment_record_status", "shipment_record_archived_status"):
        checker.field(post_close, key, where, _is_declared_status, "a declared status")
    for key in ("allowed_ids", "required_ids"):
        checker.field(post_close, key, where, _is_str_list, "a list of strings")
    for key in ("unexpected_archived", "missing_required", "failures"):
        value = checker.field(post_close, key, where, _is_str_list, "a list of strings")
        if value is not _MISSING and value:
            checker.fail(f"{where}.{key}", "must be empty under a pass verdict")
    drift = checker.field(post_close, "linked_deliberation_drift", where, lambda v: type(v) is list, "a list")
    if drift is not _MISSING and drift:
        checker.fail(f"{where}.linked_deliberation_drift", "must be empty under a pass verdict")
    for key in ("disposition_byte_identical", "parent_id_preserved", "baseline_invariant", "shipment_archived_shipped"):
        value = checker.field(post_close, key, where, _is_bool, "a boolean")
        if value is False:
            checker.fail(f"{where}.{key}", "must be true under a pass verdict")
    verdict = checker.field(post_close, "postcondition_verdict", where, lambda v: v in ("pass", "fail"), "pass or fail")
    if verdict is not _MISSING and verdict != "pass":
        checker.fail(f"{where}.postcondition_verdict", "a cascade record requires pass")


def _check_safe_close(checker: _Checker, record: Mapping[str, object], pre_close: Mapping[str, object] | None) -> None:
    if record.get("phase") != "pre_close":
        checker.fail("record.phase", "a safe_close record must be in phase pre_close")
    for key in ("invocation", "post_close"):
        if record.get(key) is not None:
            checker.fail(f"record.{key}", "a safe_close record invokes nothing")
    if pre_close is None:
        return
    engine = pre_close.get("engine_semantics")
    engine_verdict = engine.get("verdict") if isinstance(engine, Mapping) else None
    classifier = pre_close.get("classifier_verdict")
    if classifier == "CASCADE" and engine_verdict != EngineSemanticsVerdict.UNVERIFIED.value:
        checker.fail(
            "record.pre_close.classifier_verdict",
            "a safe_close record with classifier CASCADE requires an UNVERIFIED engine",
        )


# ---------------------------------------------------------------------------
# Disposition and set-term rules (plan unit A1c)
# ---------------------------------------------------------------------------

# Pre-mutation outcomes only (re-plan cycle-1 R13): the command never archives,
# so the post-mutation "archived" is never a recorded outcome.
_UNVERIFIED_OUTCOMES: Final = frozenset(
    {
        LinkedDeliberationOutcome.RETAINED_READ_ERROR.value,
        LinkedDeliberationOutcome.RETAINED_AMBIGUOUS.value,
        LinkedDeliberationOutcome.ALREADY_ARCHIVED.value,
        LinkedDeliberationOutcome.RETAINED_ENGINE_UNVERIFIED.value,
    }
)
_PRE_MUTATION_OUTCOMES: Final = _UNVERIFIED_OUTCOMES | frozenset(
    {
        PLANNED_ARCHIVE,
        LinkedDeliberationOutcome.RETAINED_LIVE_STATUS.value,
        LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE.value,
        LinkedDeliberationOutcome.RETAINED_DESCRIPTION_MENTION.value,
    }
)


def _check_disposition_rules(
    checker: _Checker, record: Mapping[str, object], pre_close: Mapping[str, object], close_path: str
) -> None:
    """Disposition, set-term, and observation-set rules (re-plan R5, D2, D3a; cycle-1 R2/R13; cycle-2 C2-1)."""

    where = "record.pre_close.linked_deliberation_disposition"
    snapshot = checker.mapping(pre_close, "linked_deliberation_disposition", "record.pre_close")
    if snapshot is None:
        return
    if snapshot.get("planning_error", _MISSING) is not None:
        checker.fail(f"{where}.planning_error", "must be null (the command never records a failed plan)")

    engine = pre_close.get("engine_semantics")
    engine_verdict = engine.get("verdict") if isinstance(engine, Mapping) else None
    raw_dispositions = snapshot.get("dispositions")
    dispositions = [
        entry for entry in (raw_dispositions if type(raw_dispositions) is list else []) if isinstance(entry, Mapping)
    ]

    disposition_ids: set[str] = set()
    expected_observations: dict[tuple[str, str], object] = {}
    for index, disposition in enumerate(dispositions):
        entry_where = f"{where}.dispositions[{index}]"
        deliberation_id = disposition.get("deliberation_id")
        if type(deliberation_id) is str:
            disposition_ids.add(deliberation_id)
        outcome = disposition.get("outcome")
        if outcome not in _PRE_MUTATION_OUTCOMES or type(outcome) is not str:
            checker.fail(f"{entry_where}.outcome", f"must be a pre-mutation outcome (got {outcome!r})")
            outcome = None
        if not _is_nonempty_str(disposition.get("reason_code")):
            checker.fail(f"{entry_where}.reason_code", "must be a non-empty string")
        # Engine/outcome consistency, both ways (D3a; cycle-1 R13).
        if outcome is not None:
            if engine_verdict == EngineSemanticsVerdict.UNVERIFIED.value and outcome not in _UNVERIFIED_OUTCOMES:
                checker.fail(f"{entry_where}.outcome", f"{outcome!r} is impossible under an UNVERIFIED engine")
            if (
                engine_verdict == EngineSemanticsVerdict.VERIFIED.value
                and outcome == LinkedDeliberationOutcome.RETAINED_ENGINE_UNVERIFIED.value
            ):
                checker.fail(f"{entry_where}.outcome", "retained_engine_unverified requires an UNVERIFIED engine")
        if outcome == LinkedDeliberationOutcome.ALREADY_ARCHIVED.value or type(deliberation_id) is not str:
            continue
        records = disposition.get("records")
        for snapshot_record in records if type(records) is list else []:
            if isinstance(snapshot_record, Mapping) and type(snapshot_record.get("path")) is str:
                expected_observations[(deliberation_id, snapshot_record["path"])] = snapshot_record.get("sha256")

    # No linked-deliberation set terms (D2).
    post_close = record.get("post_close")
    if isinstance(post_close, Mapping):
        for key in ("allowed_ids", "required_ids"):
            terms = post_close.get(key)
            leaked = sorted(disposition_ids & set(terms)) if _is_str_list(terms) else []
            if leaked:
                checker.fail(f"record.post_close.{key}", f"contains disposition-set deliberation(s) {leaked}")

    # Disposition-set deliberations in the observation set (cycle-1 R2; cycle-2 C2-1).
    observation = pre_close.get("observation_set")
    if type(observation) is not list:
        return
    observed = [
        entry for entry in observation if isinstance(entry, Mapping) and entry.get("id") in disposition_ids
    ]
    unverified_safe_close = (
        close_path == "safe_close" and engine_verdict == EngineSemanticsVerdict.UNVERIFIED.value
    )
    if not unverified_safe_close:
        for entry in observed:
            checker.fail("record.pre_close.observation_set", f"holds disposition-set deliberation {entry.get('id')!r}")
        return
    seen: dict[tuple[str, str], int] = {}
    for entry in observed:
        key = (entry.get("id"), entry.get("path"))
        if key not in expected_observations:
            checker.fail("record.pre_close.observation_set", f"unexpected disposition-set entry {key!r}")
            continue
        seen[key] = seen.get(key, 0) + 1
        if entry.get("sha256") != expected_observations[key]:
            checker.fail("record.pre_close.observation_set", f"entry {key!r} sha256 disagrees with the snapshot")
    for key in expected_observations:
        count = seen.get(key, 0)
        if count != 1:
            checker.fail("record.pre_close.observation_set", f"expected exactly one entry for {key!r} (got {count})")


def validate_evidence_record(
    record: Mapping[str, object],
    *,
    shipment_id: str,
    feature_id: str,
    close_path: Literal["cascade", "safe_close"],
) -> list[str]:
    """Validate one close-evidence record; return the list of problems (empty when valid).

    ``close_path`` is the **selected** close path. The record must match the
    ``(shipment_id, feature_id)`` pair, carry every required key well-typed,
    keep every path field a relative POSIX path under one backlog root, and
    agree with a fresh engine re-assessment and close-path re-selection.
    """

    checker = _Checker()
    if not isinstance(record, Mapping):
        return ["record: must be a JSON object"]
    if close_path not in _CLOSE_PATHS:
        return [f"close_path: must be one of {sorted(_CLOSE_PATHS)} (got {close_path!r})"]

    schema_version = record.get("schema_version", _MISSING)
    if not _is_int(schema_version) or schema_version != EVIDENCE_SCHEMA_VERSION:
        checker.fail("record.schema_version", f"must be {EVIDENCE_SCHEMA_VERSION} (got {schema_version!r})")
    for key, expected in (("shipment_id", shipment_id), ("feature_id", feature_id)):
        value = record.get(key, _MISSING)
        if value != expected or not _is_str(value):
            checker.fail(f"record.{key}", f"must be {expected!r} (got {value!r})")
    checker.field(record, "merge_commit_sha", "record", _is_nonempty_str, "a non-empty string")
    checker.field(
        record, "run_id", "record", lambda v: _is_str(v) and _RUN_ID_PATTERN.fullmatch(v) is not None, "a uuid4 hex"
    )
    checker.field(record, "phase", "record", lambda v: v in _PHASES, f"one of {sorted(_PHASES)}")
    _check_tool(checker, record)

    pre_close = checker.mapping(record, "pre_close", "record")
    if pre_close is not None:
        _check_pre_close(checker, pre_close, close_path)
        _check_disposition_rules(checker, record, pre_close, close_path)
    if len(checker.roots) > 1:
        checker.fail("record", f"path fields span more than one backlog root {sorted(checker.roots)}")

    if close_path == "cascade":
        _check_cascade(checker, record, pre_close)
    else:
        _check_safe_close(checker, record, pre_close)
    return checker.errors
