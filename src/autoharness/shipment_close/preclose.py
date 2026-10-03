"""Pre-close snapshot and ``--classify-only`` for ``cascade-close`` (192-F, plan unit A2).

:func:`run_preclose` takes the fresh pre-close snapshot: the classifier
verdict, the A2a engine-semantics decision, the ``select_close_path``
selection, the fingerprints of the shipment record, every manifest member,
and every out-of-manifest descendant, the planner's linked-deliberation
disposition snapshot, and (for a selected SAFE_CLOSE) the A2b observation
set. Every later branch keys on the **selected** close path, never on the
classifier verdict alone (re-plan R2; 038-DL D4a).

:func:`run_classify_only` is ``--classify-only``: input validation, then the
A1b pair lock and existing-record check (before any classification, so an
``invoking`` record always wins with exit 7; AN-F02), then the snapshot, then
one ``phase: pre_close`` verdict record. It exits 0 when the selected path is
CASCADE and 3 when it is SAFE_CLOSE (including classifier CASCADE under an
UNVERIFIED engine). It never mutates backlog state and never archives a
deliberation.

Every fail-closed condition raises :class:`PreCloseError` carrying exit 2,
and no record is written.
"""

from __future__ import annotations

import dataclasses
import datetime
import re
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from autoharness.backlog_root import BacklogUnavailableError as BacklogRootUnavailableError
from autoharness.backlog_root import resolve_backlog_root
from autoharness.gates.cascade_evidence import (
    EVIDENCE_SCHEMA_VERSION,
    CascadeEvidenceError,
    close_path_selection_to_record,
    declared_status_to_record,
    disposition_plan_to_record,
    engine_semantics_to_record,
    observation_entry_to_record,
    redact,
    validate_evidence_record,
)
from autoharness.gates.closure_contract import ClosureContractError, validate_closure_id
from autoharness.gates.shipment_closure import (
    ClosePath,
    ClosePathDecision,
    EngineSemanticsDecision,
    EngineSemanticsVerdict,
    LinkedDeliberationDispositionPlan,
    LinkedDeliberationOutcome,
    classify_shipment_close_path,
    compute_linked_deliberation_disposition,
    select_close_path,
)
from autoharness.shipment_close import EXIT_INPUT, EXIT_OK, EXIT_SAFE_CLOSE_SELECTED
from autoharness.shipment_close.engine_probe import probe_engine_semantics
from autoharness.shipment_close.observation import LocatedRecord, compute_observation_set, locate_record
from autoharness.shipment_close.persist import (
    MODE_CLASSIFY_ONLY,
    MODE_REPLACE_PRE_CLOSE,
    PersistError,
    acquire_pair_lock,
    check_existing_record,
    write_evidence_atomic,
)
from autoharness.shipment_close.runner import ResolvedBinary

__all__ = [
    "ClassifyOnlyResult",
    "PreCloseError",
    "PreCloseSnapshot",
    "build_pre_close_record",
    "run_classify_only",
    "run_preclose",
    "validate_preclose_inputs",
]

_SHA_PATTERN: Final = re.compile(r"[0-9a-f]{40}")
_DRIVE_PREFIX: Final = re.compile(r"[A-Za-z]:")
_OPEN_SHIPMENT_STATUSES: Final = frozenset({"queued", "active"})
# The pre_close-phase gaps a cascade-selected verdict record legitimately has
# before A3 invokes anything; every other validator problem refuses the write.
_CASCADE_PRE_CLOSE_GAPS: Final = ("record.phase:", "record.invocation:", "record.post_close:")


class PreCloseError(CascadeEvidenceError):
    """A fail-closed pre-close refusal carrying its command exit code (always 2 here)."""

    def __init__(self, message: str, exit_code: int = EXIT_INPUT) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class PreCloseSnapshot:
    """The fresh pre-close snapshot; ``pre_close`` and ``tool`` are the encoded record sections."""

    shipment_id: str
    feature_id: str
    backlog_dir: Path
    manifest_ids: tuple[str, ...]
    classifier: ClosePathDecision
    engine: EngineSemanticsDecision
    invocation_surface: str
    selection: tuple[ClosePath, str]
    disposition: LinkedDeliberationDispositionPlan
    tool: dict
    pre_close: dict

    @property
    def selected_close_path(self) -> ClosePath:
        return self.selection[0]


@dataclass(frozen=True)
class ClassifyOnlyResult:
    """The ``--classify-only`` outcome (A3d renders it)."""

    exit_code: int
    message: str
    evidence_path: Path | None = None
    selected_close_path: str | None = None
    classifier_verdict: str | None = None
    engine_verdict: str | None = None


def validate_preclose_inputs(shipment_id: object, feature_id: object, merge_commit_sha: object) -> None:
    """Validate S, F (closure-contract grammar) and ``--sha`` (40 lowercase hex) before any read."""

    try:
        validate_closure_id(shipment_id, field="shipment_id")  # type: ignore[arg-type]
        validate_closure_id(feature_id, field="feature_id")  # type: ignore[arg-type]
    except ClosureContractError as exc:
        raise PreCloseError(str(exc)) from exc
    if type(merge_commit_sha) is not str or _SHA_PATTERN.fullmatch(merge_commit_sha) is None:
        raise PreCloseError(f"--sha must be a full 40-character lowercase hex SHA (got {merge_commit_sha!r})")


def _locate(backlog_dir: Path, artifact_id: str, what: str) -> LocatedRecord:
    try:
        located = locate_record(backlog_dir, artifact_id)
    except CascadeEvidenceError as exc:
        raise PreCloseError(f"{what} {artifact_id!r} cannot be fingerprinted: {exc}") from exc
    if located is None:
        raise PreCloseError(f"{what} {artifact_id!r} is missing from the backlog")
    return located


def _manifest_ids(shipment: LocatedRecord) -> tuple[str, ...]:
    custom_fields = shipment.frontmatter.get("custom_fields")
    items = custom_fields.get("items") if isinstance(custom_fields, Mapping) else None
    if type(items) is not list or not items:
        raise PreCloseError(f"shipment {shipment.id!r} declares no manifest items")
    if any(type(item) is not str or item == "" or item != item.strip() for item in items):
        raise PreCloseError(f"shipment {shipment.id!r} manifest holds a malformed item")
    if len(set(items)) != len(items):
        raise PreCloseError(f"shipment {shipment.id!r} manifest holds a duplicate member")
    return tuple(items)


def _is_record_path(value: object, backlog_root_name: str) -> bool:
    """The A1 textual record-path rule (re-plan cycle-1 R12)."""

    if type(value) is not str or value == "" or value.startswith(("/", "\\")) or "\\" in value:
        return False
    if _DRIVE_PREFIX.match(value):
        return False
    segments = value.split("/")
    return segments[0] == backlog_root_name and ".." not in segments


def _contain_plan_paths(plan: LinkedDeliberationDispositionPlan, backlog_root_name: str) -> LinkedDeliberationDispositionPlan:
    """Null every planner path outside the backlog root, keeping the reason_code (R12)."""

    dispositions = []
    for disposition in plan.dispositions:
        for snapshot in disposition.records:
            if not _is_record_path(snapshot.path, backlog_root_name):
                raise PreCloseError(
                    f"deliberation {disposition.deliberation_id!r} record path is not under the backlog root"
                )
        path = disposition.path if _is_record_path(disposition.path, backlog_root_name) else None
        dispositions.append(dataclasses.replace(disposition, path=path))
    failures = tuple(
        dataclasses.replace(failure, path=failure.path if _is_record_path(failure.path, backlog_root_name) else None)
        for failure in plan.read_failures
    )
    return dataclasses.replace(plan, dispositions=tuple(dispositions), read_failures=failures)


def _located_entry(located: LocatedRecord | None, artifact_id: str) -> dict[str, object]:
    if located is None:
        return {"id": artifact_id, "location": "missing", "sha256": None, "declared_status": None}
    return {
        "id": artifact_id,
        "location": located.location,
        "sha256": located.sha256,
        "declared_status": declared_status_to_record(located.declared_status),
    }


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_preclose(
    workspace: Path | str, shipment_id: str, feature_id: str, *, resolved: ResolvedBinary
) -> PreCloseSnapshot:
    """Take the fresh pre-close snapshot; raise :class:`PreCloseError` (exit 2) on any fail-closed condition."""

    for value, field in ((shipment_id, "shipment_id"), (feature_id, "feature_id")):
        try:
            validate_closure_id(value, field=field)
        except ClosureContractError as exc:
            raise PreCloseError(str(exc)) from exc
    root = Path(workspace).resolve()
    try:
        backlog_dir = resolve_backlog_root(root)  # both roots present fails closed
    except BacklogRootUnavailableError as exc:
        raise PreCloseError(f"backlog root cannot be resolved: {exc}") from exc

    # The shipment must still be open (AN-F01).
    shipment = _locate(backlog_dir, shipment_id, "shipment")
    if shipment.artifact_type != "shipment":
        raise PreCloseError(f"{shipment_id!r} is not a shipment record")
    if shipment.location != "queue" or not (
        type(shipment.declared_status) is str and shipment.declared_status in _OPEN_SHIPMENT_STATUSES
    ):
        raise PreCloseError(
            f"shipment {shipment_id!r} is no longer open (location {shipment.location}, "
            f"status {shipment.declared_status!r}); no verdict record after the fact"
        )
    manifest_ids = _manifest_ids(shipment)

    # Torn or missing manifest members fail closed (RECONCILE_FAIL_SNAPSHOT_*).
    members = {member_id: _locate(backlog_dir, member_id, "manifest member") for member_id in manifest_ids}

    classifier = classify_shipment_close_path(manifest_ids, backlog_dir)
    probe = probe_engine_semantics(resolved, workspace=root)
    selection = select_close_path(classifier, probe.decision)
    for label, text in (("close_path_selection.reason", selection[1]), ("classifier_reason", classifier.reason)):
        if redact(text)[0] != text:
            raise PreCloseError(f"{label} is not redaction-neutral; the validator would reject the record")

    selected = selection[0]
    if selected is ClosePath.CASCADE:
        if feature_id not in classifier.qualifying_feature_ids:
            raise PreCloseError(f"feature {feature_id!r} is not in the qualifying set {classifier.qualifying_feature_ids}")
    elif feature_id not in manifest_ids and feature_id not in {member.parent_id for member in members.values()}:
        raise PreCloseError(f"feature {feature_id!r} is neither a manifest member nor the parent of one")

    manifest_members = []
    for member_id in manifest_ids:
        member = members[member_id]
        if type(member.artifact_type) is not str or member.artifact_type.strip() == "":
            raise PreCloseError(f"manifest member {member_id!r} declares no artifact_type")
        manifest_members.append(
            {
                "id": member_id,
                "artifact_type": member.artifact_type.strip().lower(),
                "location": member.location,
                "sha256": member.sha256,
                "declared_status": declared_status_to_record(member.declared_status),
                "parent_id": member.parent_id,
            }
        )

    descendants = []
    for descendant_id in classifier.out_of_manifest_descendant_ids:
        try:
            descendants.append(_located_entry(locate_record(backlog_dir, descendant_id), descendant_id))
        except CascadeEvidenceError as exc:
            raise PreCloseError(f"out-of-manifest descendant {descendant_id!r} cannot be fingerprinted: {exc}") from exc

    # Disposition snapshot (re-plan R5): read-only, no stash_path, never archives.
    plan = compute_linked_deliberation_disposition(manifest_ids, shipment_id, backlog_dir, engine=probe.decision)
    if plan.planning_error is not None:
        raise PreCloseError(f"linked-deliberation planning_error: {plan.planning_error}")
    plan = _contain_plan_paths(plan, backlog_dir.name)
    try:
        disposition_record = disposition_plan_to_record(plan)
    except CascadeEvidenceError as exc:
        raise PreCloseError(f"disposition snapshot cannot be encoded: {exc}") from exc

    pre_close: dict[str, object] = {
        "classifier_verdict": classifier.close_path.name,
        "classifier_reason": classifier.reason,
        "qualifying_feature_ids": list(classifier.qualifying_feature_ids),
        "engine_semantics": engine_semantics_to_record(probe.decision, invocation_surface=probe.invocation_surface),
        "close_path_selection": close_path_selection_to_record(selection),
        "shipment_record": {
            "location": shipment.location,
            "sha256": shipment.sha256,
            "declared_status": declared_status_to_record(shipment.declared_status),
        },
        "manifest_members": manifest_members,
        "out_of_manifest_descendants": descendants,
        "linked_deliberation_disposition": disposition_record,
    }

    if selected is ClosePath.SAFE_CLOSE:
        verified = probe.decision.verdict is EngineSemanticsVerdict.VERIFIED
        deliberation_records = (
            []
            if verified
            else [
                (disposition.deliberation_id, snapshot)
                for disposition in plan.dispositions
                if disposition.outcome != LinkedDeliberationOutcome.ALREADY_ARCHIVED
                for snapshot in disposition.records
            ]
        )
        try:
            observation = compute_observation_set(
                manifest_ids,
                shipment_id,
                backlog_dir,
                excluded_ids={disposition.deliberation_id for disposition in plan.dispositions},
                deliberation_records=deliberation_records,
            )
        except CascadeEvidenceError as exc:
            raise PreCloseError(f"the safe-close observation set cannot be established: {exc}") from exc
        pre_close["observation_set"] = [observation_entry_to_record(entry) for entry in observation]
    pre_close["captured_at"] = _utc_now()

    return PreCloseSnapshot(
        shipment_id=shipment_id,
        feature_id=feature_id,
        backlog_dir=backlog_dir,
        manifest_ids=manifest_ids,
        classifier=classifier,
        engine=probe.decision,
        invocation_surface=probe.invocation_surface,
        selection=selection,
        disposition=plan,
        tool={
            "binary_path": resolved.binary_path,
            "binary_sha256": resolved.binary_sha256,
            "version_excerpt": probe.version_excerpt,
        },
        pre_close=pre_close,
    )


def build_pre_close_record(snapshot: PreCloseSnapshot, *, merge_commit_sha: str, run_id: str) -> dict[str, object]:
    """Assemble the ``phase: pre_close`` evidence record from a snapshot."""

    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "shipment_id": snapshot.shipment_id,
        "feature_id": snapshot.feature_id,
        "merge_commit_sha": merge_commit_sha,
        "run_id": run_id,
        "phase": "pre_close",
        "tool": dict(snapshot.tool),
        "pre_close": snapshot.pre_close,
    }


def _record_problems(record: Mapping[str, object], snapshot: PreCloseSnapshot) -> list[str]:
    selected = snapshot.selected_close_path.value
    problems = validate_evidence_record(
        record, shipment_id=snapshot.shipment_id, feature_id=snapshot.feature_id, close_path=selected
    )
    if snapshot.selected_close_path is ClosePath.CASCADE:
        problems = [problem for problem in problems if not problem.startswith(_CASCADE_PRE_CLOSE_GAPS)]
    return problems


def run_classify_only(
    workspace: Path | str,
    shipment_id: str,
    feature_id: str,
    merge_commit_sha: str,
    *,
    resolved: ResolvedBinary,
    run_id: str | None = None,
    replace_pre_close: bool = False,
) -> ClassifyOnlyResult:
    """``--classify-only``: write one ``pre_close`` verdict record; exit 0 (CASCADE) or 3 (SAFE_CLOSE).

    Plain ``--classify-only`` is no-clobber: an existing ``pre_close`` record
    exits 2. ``replace_pre_close`` (``--classify-only --replace-pre-close``,
    destructive and operator-approved) replaces an existing ``pre_close``
    record only through the A1b pre_close takeover, keyed on the ``run_id``
    the existing-record check returned under this lock hold (Copilot PR #481
    T6). An ``invoking`` or ``post_close`` record is never replaced.
    """

    try:
        validate_preclose_inputs(shipment_id, feature_id, merge_commit_sha)
    except PreCloseError as exc:
        return ClassifyOnlyResult(exc.exit_code, str(exc))
    owner = run_id if run_id is not None else uuid.uuid4().hex
    try:
        lock = acquire_pair_lock(workspace, shipment_id, feature_id, owner)
    except PersistError as exc:
        return ClassifyOnlyResult(exc.exit_code, str(exc))
    try:
        mode = MODE_REPLACE_PRE_CLOSE if replace_pre_close else MODE_CLASSIFY_ONLY
        existing = check_existing_record(lock, mode=mode)  # before any classification (AN-F02)
        snapshot = run_preclose(workspace, shipment_id, feature_id, resolved=resolved)
        record = build_pre_close_record(snapshot, merge_commit_sha=merge_commit_sha, run_id=owner)
        problems = _record_problems(record, snapshot)
        if problems:
            raise PreCloseError(f"the verdict record fails validation: {problems}")
        takeover = existing.get("run_id") if existing is not None else None
        write_evidence_atomic(lock.evidence_path, record, owner_run_id=owner, takeover_from_run_id=takeover)
    except (PreCloseError, PersistError) as exc:
        return ClassifyOnlyResult(exc.exit_code, str(exc))
    except CascadeEvidenceError as exc:
        return ClassifyOnlyResult(EXIT_INPUT, str(exc))
    finally:
        lock.release()
    selected = snapshot.selected_close_path
    exit_code = EXIT_OK if selected is ClosePath.CASCADE else EXIT_SAFE_CLOSE_SELECTED
    return ClassifyOnlyResult(
        exit_code,
        f"selected {selected.value} ({snapshot.selection[1]})",
        evidence_path=lock.evidence_path,
        selected_close_path=selected.value,
        classifier_verdict=snapshot.classifier.close_path.name,
        engine_verdict=snapshot.engine.verdict.value,
    )
