"""Ship-response parser, flat sets, and the INV-10 evaluator for ``cascade-close`` (192-F, plan unit A3b).

* :func:`parse_ship_response` parses the JSON-RPC 2.0 envelope that
  ``backlogit --jsonrpc shipment ship`` writes to **stdout only** (backlogit
  logs to stderr). The envelope shape is characterized by the fixtures in
  ``tests/fixtures/backlogit_ship/`` (backlogit 1.11.0). Every defect is a
  :class:`ParseError`, never an exception.
* :func:`compute_flat_sets` derives the flat 1.11.x ``allowed_ids`` /
  ``required_ids`` from the pre-close snapshot only (INV-P2; re-plan R4,
  038-DL D2). Neither set holds a linked-deliberation term: a deliberation
  that is an explicit manifest member is an ordinary member (H10), and a
  disposition-set deliberation is in neither set.
* :func:`evaluate_postconditions` evaluates INV-10 in full. It is pure: the
  caller (A3) supplies the post-close re-read as a :class:`PostCloseReread`,
  and the A3c linked-deliberation drift results as keyword arguments. Every
  check is separately labelled and fails the verdict on its own (INV-P3).
* :func:`derive_mutation_state` derives ``invocation.mutation_state``. A
  timeout is never read as "no mutation", and ``none`` needs positive proof
  that nothing fingerprinted changed.

No function here reads the filesystem or spawns a process. No private
``shipment_closure`` name is imported by this module (re-plan cycle-2 C2-4):
the flat sets are re-derived locally and pinned by the A3b parity test.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final

from autoharness.gates.cascade_evidence import (
    DECLARED_STATUS_MISSING,
    CascadeEvidenceError,
    declared_status_from_record,
    declared_status_to_record,
    redact,
)
from autoharness.gates.shipment_closure import LinkedDeliberationDispositionPlan
from autoharness.shipment_close.preclose import PreCloseSnapshot

__all__ = [
    "MUTATION_COMPLETED",
    "MUTATION_INDETERMINATE",
    "MUTATION_NONE",
    "ParseError",
    "ParsedResult",
    "PostCloseReread",
    "PostCloseResult",
    "RereadRecord",
    "compute_flat_sets",
    "derive_mutation_state",
    "evaluate_postconditions",
    "parse_ship_response",
]

MUTATION_NONE: Final = "none"
MUTATION_COMPLETED: Final = "completed"
MUTATION_INDETERMINATE: Final = "indeterminate"

_ARCHIVED: Final = "archived"
_SHIPPED: Final = "shipped"
_MAX_ERROR_TEXT: Final = 512
_RESULT_KEYS: Final = ("archived_ids", "returned_ids", "shipment_id", "shipment_status", "commit_sha")


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedResult:
    """A parsed ``shipment ship`` success envelope's ``result``."""

    shipment_id: str
    shipment_status: str
    archived_ids: tuple[str, ...]
    returned_ids: tuple[str, ...]
    commit_sha: str | None

    def to_record(self) -> dict[str, object]:
        """The A1 ``post_close.parsed_result`` shape."""

        return {
            "shipment_status": self.shipment_status,
            "archived_ids": list(self.archived_ids),
            "returned_ids": list(self.returned_ids),
            "commit_sha": self.commit_sha,
        }


@dataclass(frozen=True)
class ParseError:
    """Why stdout is not a usable success envelope (a JSON-RPC ``error`` is one too)."""

    message: str


def _error_text(text: str) -> str:
    redacted = redact(text)[0]
    if len(redacted) > _MAX_ERROR_TEXT:
        redacted = redacted[:_MAX_ERROR_TEXT] + "…"
    return redacted


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate object key")
    return dict(pairs)


def _str_tuple(value: object) -> tuple[str, ...] | None:
    if type(value) is not list or any(type(item) is not str or item == "" for item in value):
        return None
    return tuple(value)


def _parse_result(result: object) -> ParsedResult | ParseError:
    if not isinstance(result, dict):
        return ParseError(f"the JSON-RPC result is a {type(result).__name__}, not an object")
    missing = [key for key in _RESULT_KEYS if key not in result]
    if missing:
        return ParseError(f"the JSON-RPC result lacks {missing}")
    archived = _str_tuple(result["archived_ids"])
    returned = _str_tuple(result["returned_ids"])
    if archived is None or returned is None:
        return ParseError("archived_ids and returned_ids must be lists of non-empty strings")
    shipment_id = result["shipment_id"]
    status = result["shipment_status"]
    if type(shipment_id) is not str or shipment_id == "" or type(status) is not str:
        return ParseError("shipment_id and shipment_status must be strings")
    commit_sha = result["commit_sha"]
    if commit_sha is not None and type(commit_sha) is not str:
        return ParseError("commit_sha must be a string or null")
    return ParsedResult(
        shipment_id=shipment_id,
        shipment_status=status,
        archived_ids=archived,
        returned_ids=returned,
        commit_sha=commit_sha,
    )


def parse_ship_response(stdout_bytes: bytes) -> ParsedResult | ParseError:
    """Parse one JSON-RPC 2.0 envelope from stdout bytes; never raises."""

    if not isinstance(stdout_bytes, (bytes, bytearray)):
        return ParseError(f"stdout must be bytes (got {type(stdout_bytes).__name__})")
    try:
        text = bytes(stdout_bytes).decode("utf-8")
    except UnicodeDecodeError as exc:
        return ParseError(f"stdout is not UTF-8: {exc.reason}")
    if text.strip() == "":
        return ParseError("stdout is empty")
    try:
        envelope = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except (ValueError, RecursionError) as exc:
        return ParseError(f"stdout is not exactly one JSON value: {_error_text(str(exc))}")
    if not isinstance(envelope, dict):
        return ParseError(f"the envelope is a {type(envelope).__name__}, not an object")
    if envelope.get("jsonrpc") != "2.0":
        return ParseError(f"the envelope is not JSON-RPC 2.0 (jsonrpc={envelope.get('jsonrpc')!r})")
    has_result, has_error = "result" in envelope, "error" in envelope
    if has_result == has_error:
        return ParseError("the envelope must carry exactly one of result and error")
    if has_error:
        error = envelope["error"]
        if not isinstance(error, dict) or type(error.get("message")) is not str:
            return ParseError("the JSON-RPC error is malformed")
        code = error.get("code")
        return ParseError(f"backlogit JSON-RPC error {code!r}: {_error_text(error['message'])}")
    return _parse_result(envelope["result"])


# ---------------------------------------------------------------------------
# Post-close re-read (supplied by A3) and the flat sets
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RereadRecord:
    """One post-close re-read: ``declared_status`` is the decoded frontmatter value."""

    location: str  # queue | archive | missing
    sha256: str | None
    declared_status: object
    parent_id: str | None
    archived_status: object = DECLARED_STATUS_MISSING


@dataclass(frozen=True)
class PostCloseReread:
    """A3's post-close read: the shipment record, every fingerprinted ID, and the re-collected disposition.

    ``records`` is keyed by artifact ID; an ID absent from it was not found.
    ``unreadable_ids`` holds every ID whose re-read failed (for example a
    queue copy and an archive copy at once). ``disposition`` is the
    post-cascade re-collection, or ``None`` when it was not obtained.
    """

    shipment: RereadRecord | None
    records: Mapping[str, RereadRecord]
    disposition: LinkedDeliberationDispositionPlan | None
    unreadable_ids: frozenset[str] = frozenset()


def _is_declared_archived(record_value: object) -> bool:
    """The local "truly archived" check over an A1-encoded declared status.

    Only an exact ``str`` equal to ``"archived"`` counts (re-plan cycle-1 R9);
    a value that does not decode is not archived.
    """

    try:
        decoded = declared_status_from_record(record_value)
    except CascadeEvidenceError:
        return False
    return type(decoded) is str and decoded == _ARCHIVED


def _members(pre_close: Mapping[str, object]) -> list[Mapping[str, object]]:
    members = pre_close.get("manifest_members")
    return [member for member in members if isinstance(member, Mapping)] if isinstance(members, list) else []


def compute_flat_sets(pre_close: Mapping[str, object], shipment_id: str) -> tuple[frozenset[str], frozenset[str]]:
    """Return ``(allowed_ids, required_ids)`` from the pre-close record section only (INV-P2).

    ``allowed_ids = items(S) ∪ {S}``; ``required_ids = {S} ∪
    qualifying_feature_ids ∪ {x ∈ items(S): x was not truly archived
    pre-close}``, over every manifest item regardless of ``artifact_type``.
    """

    members = _members(pre_close)
    member_ids = {member["id"] for member in members if type(member.get("id")) is str}
    allowed = frozenset(member_ids | {shipment_id})
    qualifying = pre_close.get("qualifying_feature_ids")
    qualifying_ids = {item for item in qualifying if type(item) is str} if isinstance(qualifying, list) else set()
    unarchived = {
        member["id"]
        for member in members
        if type(member.get("id")) is str and not _is_declared_archived(member.get("declared_status"))
    }
    return allowed, frozenset({shipment_id} | qualifying_ids | unarchived)


# ---------------------------------------------------------------------------
# mutation_state
# ---------------------------------------------------------------------------


def _fingerprinted_entries(pre_close: Mapping[str, object]) -> list[Mapping[str, object]]:
    entries = list(_members(pre_close))
    descendants = pre_close.get("out_of_manifest_descendants")
    if isinstance(descendants, list):
        entries.extend(entry for entry in descendants if isinstance(entry, Mapping))
    return entries


def _deliberation_records(plan: LinkedDeliberationDispositionPlan) -> frozenset[tuple[str, str, str]]:
    return frozenset(
        (disposition.deliberation_id, snapshot.path, snapshot.sha256)
        for disposition in plan.dispositions
        for snapshot in disposition.records
    )


def _entry_unchanged(entry: Mapping[str, object], reread: PostCloseReread) -> bool:
    artifact_id = entry.get("id")
    if type(artifact_id) is not str or artifact_id in reread.unreadable_ids:
        return False
    current = reread.records.get(artifact_id)
    if entry.get("location") == "missing":
        return current is None or current.location == "missing"
    # The same location also proves no archive-location file was gained.
    return current is not None and current.location == entry.get("location") and current.sha256 == entry.get("sha256")


def _nothing_changed(snapshot: PreCloseSnapshot, reread: PostCloseReread) -> bool:
    pre_close = snapshot.pre_close
    shipment = pre_close.get("shipment_record")
    if not isinstance(shipment, Mapping) or reread.shipment is None or snapshot.shipment_id in reread.unreadable_ids:
        return False
    if reread.shipment.location != shipment.get("location") or reread.shipment.sha256 != shipment.get("sha256"):
        return False
    if not all(_entry_unchanged(entry, reread) for entry in _fingerprinted_entries(pre_close)):
        return False
    if reread.disposition is None:
        return False
    return _deliberation_records(reread.disposition) == _deliberation_records(snapshot.disposition)


def derive_mutation_state(
    snapshot: PreCloseSnapshot,
    parsed: ParsedResult | ParseError | None,
    reread: PostCloseReread | None,
    *,
    exit_code: int | None,
    timed_out: bool,
) -> str:
    """``completed`` for a parsed success (exit 0); ``none`` only on proof of no change; else ``indeterminate``.

    A timeout is never "no mutation". ``none`` needs a non-zero exit, an
    unparsed response, and a re-read showing every fingerprinted file (the
    shipment record, every manifest member, every out-of-manifest
    descendant, and every disposition-set deliberation record) unchanged in
    SHA-256 and location, so that no fingerprinted ID gained an archive file.
    """

    if timed_out or exit_code is None:
        return MUTATION_INDETERMINATE
    if isinstance(parsed, ParsedResult):
        return MUTATION_COMPLETED if exit_code == 0 else MUTATION_INDETERMINATE
    if exit_code == 0 or reread is None:
        return MUTATION_INDETERMINATE
    return MUTATION_NONE if _nothing_changed(snapshot, reread) else MUTATION_INDETERMINATE


# ---------------------------------------------------------------------------
# INV-10
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PostCloseResult:
    """The evaluated ``post_close`` section (A1 shape via :meth:`to_record`)."""

    parsed_result: ParsedResult | None
    parse_error: str | None
    shipment_record_status: object
    shipment_record_archived_status: object
    allowed_ids: frozenset[str]
    required_ids: frozenset[str]
    unexpected_archived: tuple[str, ...]
    missing_required: tuple[str, ...]
    linked_deliberation_drift: tuple[object, ...]
    disposition_byte_identical: bool | None
    parent_id_preserved: bool
    baseline_invariant: bool
    shipment_archived_shipped: bool
    postcondition_verdict: str
    failures: tuple[str, ...] = field(default=())

    def to_record(self) -> dict[str, object]:
        return {
            "parsed_result": None if self.parsed_result is None else self.parsed_result.to_record(),
            "parse_error": self.parse_error,
            "shipment_record_status": declared_status_to_record(self.shipment_record_status),
            "shipment_record_archived_status": declared_status_to_record(self.shipment_record_archived_status),
            "allowed_ids": sorted(self.allowed_ids),
            "required_ids": sorted(self.required_ids),
            "unexpected_archived": list(self.unexpected_archived),
            "missing_required": list(self.missing_required),
            "linked_deliberation_drift": [_drift_record(entry) for entry in self.linked_deliberation_drift],
            "disposition_byte_identical": self.disposition_byte_identical,
            "parent_id_preserved": self.parent_id_preserved,
            "baseline_invariant": self.baseline_invariant,
            "shipment_archived_shipped": self.shipment_archived_shipped,
            "postcondition_verdict": self.postcondition_verdict,
            "failures": list(self.failures),
        }


def _drift_record(entry: object) -> object:
    to_record = getattr(entry, "to_record", None)
    if callable(to_record):
        return to_record()
    if dataclasses.is_dataclass(entry) and not isinstance(entry, type):
        return dataclasses.asdict(entry)
    return dict(entry) if isinstance(entry, Mapping) else entry


def _check_parent_ids(pre_close: Mapping[str, object], reread: PostCloseReread, failures: list[str]) -> bool:
    """``parent_id`` preservation for every manifest member, archived ones included (AS-F10)."""

    preserved = True
    for member in _members(pre_close):
        member_id = member.get("id")
        current = reread.records.get(member_id) if type(member_id) is str else None
        if current is None or member_id in reread.unreadable_ids or current.location == "missing":
            failures.append(f"parent_id_preserved: manifest member {member_id!r} could not be re-read")
            preserved = False
        elif current.parent_id != member.get("parent_id"):
            failures.append(
                f"parent_id_preserved: {member_id} parent_id {current.parent_id!r} "
                f"!= pre-close {member.get('parent_id')!r}"
            )
            preserved = False
    return preserved


def _check_baseline(
    pre_close: Mapping[str, object], allowed: frozenset[str], reread: PostCloseReread, failures: list[str]
) -> bool:
    """Byte-identical invariance for every fingerprinted artifact outside ``allowed_ids``."""

    invariant = True
    for entry in _fingerprinted_entries(pre_close):
        artifact_id = entry.get("id")
        if artifact_id in allowed:
            continue
        if not _entry_unchanged(entry, reread):
            current = reread.records.get(artifact_id) if type(artifact_id) is str else None
            observed = "unreadable or missing" if current is None else f"{current.location}/{current.sha256}"
            failures.append(
                f"baseline_invariant: {artifact_id!r} changed (pre-close "
                f"{entry.get('location')}/{entry.get('sha256')}, post-close {observed})"
            )
            invariant = False
    return invariant


def evaluate_postconditions(
    snapshot: PreCloseSnapshot,
    parsed: ParsedResult | ParseError | None,
    reread: PostCloseReread,
    *,
    linked_deliberation_drift: Sequence[object] | None = None,
    disposition_byte_identical: bool | None = None,
) -> PostCloseResult:
    """Evaluate INV-10 over the flat sets; pure, no I/O.

    ``linked_deliberation_drift`` and ``disposition_byte_identical`` come from
    the A3c evaluator. When either is not supplied the verdict fails, so an
    unevaluated disposition can never pass.
    """

    pre_close = snapshot.pre_close
    allowed, required = compute_flat_sets(pre_close, snapshot.shipment_id)
    failures: list[str] = []
    unexpected: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    parsed_result = parsed if isinstance(parsed, ParsedResult) else None
    parse_error: str | None = None

    if parsed_result is None:
        parse_error = parsed.message if isinstance(parsed, ParseError) else "no response was parsed"
        failures.append(f"parse_error: {parse_error}")
    else:
        if parsed_result.shipment_id != snapshot.shipment_id:
            failures.append(
                f"shipment_id: the response names {parsed_result.shipment_id!r}, not {snapshot.shipment_id!r}"
            )
        if parsed_result.shipment_status != _SHIPPED:
            failures.append(f"shipment_status: the response reports {parsed_result.shipment_status!r}, not 'shipped'")
        if parsed_result.returned_ids:
            failures.append(f"returned_ids: must be empty (got {sorted(parsed_result.returned_ids)})")
        archived = frozenset(parsed_result.archived_ids)
        unexpected = tuple(sorted(archived - allowed))
        missing = tuple(sorted(required - archived))
        if unexpected:
            failures.append(f"unexpected_archived: {list(unexpected)} archived outside allowed_ids")
        if missing:
            failures.append(f"missing_required: {list(missing)} not archived")

    parent_ids_ok = _check_parent_ids(pre_close, reread, failures)
    baseline_ok = _check_baseline(pre_close, allowed, reread, failures)

    shipment = reread.shipment
    status = DECLARED_STATUS_MISSING if shipment is None else shipment.declared_status
    archived_status = DECLARED_STATUS_MISSING if shipment is None else shipment.archived_status
    shipment_ok = (
        shipment is not None
        and snapshot.shipment_id not in reread.unreadable_ids
        and type(status) is str
        and status == _ARCHIVED
        and type(archived_status) is str
        and archived_status == _SHIPPED
    )
    if not shipment_ok:
        failures.append(
            f"shipment_archived_shipped: the re-read shipment declares status {status!r} "
            f"and archived_status {archived_status!r}"
        )

    drift = () if linked_deliberation_drift is None else tuple(linked_deliberation_drift)
    if linked_deliberation_drift is None:
        failures.append("linked_deliberation_drift: not evaluated")
    elif drift:
        failures.append(f"linked_deliberation_drift: {len(drift)} drift entr{'y' if len(drift) == 1 else 'ies'}")
    if disposition_byte_identical is not True:
        failures.append(
            "disposition_byte_identical: not evaluated"
            if disposition_byte_identical is None
            else "disposition_byte_identical: a disposition-set deliberation record changed"
        )

    return PostCloseResult(
        parsed_result=parsed_result,
        parse_error=parse_error,
        shipment_record_status=status,
        shipment_record_archived_status=archived_status,
        allowed_ids=allowed,
        required_ids=required,
        unexpected_archived=unexpected,
        missing_required=missing,
        linked_deliberation_drift=drift,
        disposition_byte_identical=disposition_byte_identical,
        parent_id_preserved=parent_ids_ok,
        baseline_invariant=baseline_ok,
        shipment_archived_shipped=shipment_ok,
        postcondition_verdict="fail" if failures else "pass",
        failures=tuple(failures),
    )
