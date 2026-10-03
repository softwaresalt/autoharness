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
* :class:`CascadeEvidenceError`, the single error type.

Layering (AS-F07): this module never writes, never spawns a subprocess, never
imports the command package and defines no exit codes.

Selection consistency (re-plan R1/R2, D4a): the validator re-assesses the
recorded raw engine inputs with
:func:`~autoharness.gates.shipment_closure.assess_cascade_engine_semantics` and
re-selects with :func:`~autoharness.gates.shipment_closure.select_close_path`,
so a hand-edited verdict or selection is rejected.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Final, Literal

from autoharness.gates.closure_contract import (
    ClosureContractError,
    assert_path_within_workspace,
    validate_closure_id,
)
from autoharness.gates.shipment_closure import (
    ClosePath,
    ClosePathDecision,
    EngineSemanticsVerdict,
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
_RETAINED_READ_ERROR: Final = "retained_read_error"

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
    # Plain shape check; the A1d decoder owns the canonical encoding.
    return type(value) is str or isinstance(value, Mapping)


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


def _check_engine_shape(checker: _Checker, engine: Mapping[str, object], where: str) -> bool:
    before = len(checker.errors)
    checker.field(engine, "verdict", where, lambda v: v in _ENGINE_VERDICTS, f"one of {sorted(_ENGINE_VERDICTS)}")
    checker.field(engine, "reason", where, _is_str, "a string")
    for key in ("probed_version", "probed_commit", "probe_surface"):
        checker.field(engine, key, where, lambda v: v is None or _is_str(v), "a string or null")
    checker.field(
        engine,
        "minor_line",
        where,
        lambda v: v is None or (type(v) is list and len(v) == 2 and all(_is_int(i) for i in v)),
        "null or a list of two integers",
    )
    surface = checker.field(engine, "invocation_surface", where, _is_str, "a string")
    if surface is not _MISSING and surface != "cli":
        checker.fail(f"{where}.invocation_surface", f"must be 'cli' (got {surface!r})")
    return len(checker.errors) == before


def _check_selection(checker: _Checker, pre_close: Mapping[str, object], close_path: str) -> None:
    """Re-assess the engine and re-select the close path (re-plan R1/R2, D4a)."""

    where = "record.pre_close"
    verdict = checker.field(
        pre_close, "classifier_verdict", where, lambda v: v in _CLASSIFIER_VERDICTS, "CASCADE or SAFE_CLOSE"
    )
    reason = checker.field(pre_close, "classifier_reason", where, _is_str, "a string")
    qualifying = checker.field(pre_close, "qualifying_feature_ids", where, _is_str_list, "a list of strings")
    engine = checker.mapping(pre_close, "engine_semantics", where)
    selection = checker.mapping(pre_close, "close_path_selection", where)
    engine_ok = engine is not None and _check_engine_shape(checker, engine, f"{where}.engine_semantics")
    selected = reason_recorded = _MISSING
    if selection is not None:
        selected = checker.field(
            selection,
            "selected_close_path",
            f"{where}.close_path_selection",
            lambda v: v in _CLOSE_PATHS,
            f"one of {sorted(_CLOSE_PATHS)}",
        )
        reason_recorded = checker.field(selection, "reason", f"{where}.close_path_selection", _is_str, "a string")
    if selected is not _MISSING and selected != close_path:
        checker.fail(
            f"{where}.close_path_selection.selected_close_path",
            f"record selected {selected!r} but is offered for {close_path!r}",
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

    if not engine_ok or engine is None:
        return
    decision = assess_cascade_engine_semantics(
        engine["probed_version"],
        probe_surface=engine["probe_surface"],
        invocation_surface=engine["invocation_surface"],
        probed_commit=engine["probed_commit"],
    )
    expected_engine = {
        "verdict": decision.verdict.value,
        "reason": decision.reason,
        "probed_version": decision.probed_version,
        "minor_line": list(decision.minor_line) if decision.minor_line is not None else None,
        "probed_commit": decision.probed_commit,
        "probe_surface": decision.probe_surface,
    }
    for key, expected in expected_engine.items():
        if engine[key] != expected:
            checker.fail(
                f"{where}.engine_semantics.{key}",
                f"recorded {engine[key]!r} but re-assessment gives {expected!r}",
            )
    if verdict is _MISSING or reason is _MISSING or qualifying is _MISSING or selected is _MISSING or reason_recorded is _MISSING:
        return
    classifier = ClosePathDecision(
        close_path=_CLASSIFIER_VERDICTS[verdict],
        reason=reason,
        qualifying_feature_ids=tuple(qualifying),
    )
    expected_path, expected_reason = select_close_path(classifier, decision)
    if selected != expected_path.value:
        checker.fail(
            f"{where}.close_path_selection.selected_close_path",
            f"recorded {selected!r} but select_close_path gives {expected_path.value!r}",
        )
    if reason_recorded != expected_reason:
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

    if close_path == "safe_close":
        for index, entry in enumerate(checker.items(pre_close, "observation_set", where)):
            entry_where = f"{where}.observation_set[{index}]"
            location = _check_located_entry(checker, entry, entry_where, require_id=True)
            path = entry.get("path", _MISSING)
            if location == "missing" and path is not None:
                checker.fail(f"{entry_where}.path", "must be null when location is missing")
            else:
                checker.record_path(path, f"{entry_where}.path", nullable=location == "missing")
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
    if len(checker.roots) > 1:
        checker.fail("record", f"path fields span more than one backlog root {sorted(checker.roots)}")

    if close_path == "cascade":
        _check_cascade(checker, record, pre_close)
    else:
        _check_safe_close(checker, record, pre_close)
    return checker.errors
