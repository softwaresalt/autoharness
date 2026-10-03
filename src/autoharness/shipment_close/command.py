"""``cascade-close`` orchestration (192-F, plan unit A3).

:func:`run_cascade_close` is the mutating mode of ``autoharness shipment
cascade-close``. Every step runs under the A1b pair lock:

1. the existing-record check (exit 7 or 2), before any classification;
2. ``--message`` / ``--author`` validation (exit 2);
3. :func:`~autoharness.shipment_close.preclose.run_preclose` (the A2a engine
   probe plus ``select_close_path``). With no ``cascade``-selected record, a
   selected path other than CASCADE writes the ``pre_close`` verdict record
   and exits 3: the engine gate fails closed to SAFE_CLOSE and nothing is
   invoked. A ``cascade``-selected ``--classify-only`` record is the Step 0(c)
   record: any difference from it (including a fresh SAFE_CLOSE selection,
   or a changed re-hashed ``tool.binary_sha256``) exits 4 and leaves it
   byte-identical (re-plan cycle-1 R1; D4a; INV-P4);
4. the ``pre_close`` write. Over an existing ``pre_close`` record it is the
   A1b **pre_close takeover**, made only after step 3's exact match; a
   refused takeover exits 4, any other write failure exits 2;
5. revalidation: the whole snapshot is recomputed (which re-runs the A2a
   probe on the same binary and CLI surface) and compared with the durable
   record, ignoring only ``run_id`` and ``captured_at``. Any difference, or
   a snapshot that can no longer be taken, exits 4 and never substitutes
   SAFE_CLOSE;
6. the binary re-hash (exit 4 on a mismatch);
7. the owner-bound ``invoking`` record (exit 2 if it cannot be written);
8. the fixed ``shipment ship`` argv through the A3a runner;
9. the post-close re-read, the disposition re-collection (pre-close
   manifest IDs and the recorded engine decision), the A3c drift check, and
   the A3b INV-10 evaluation;
10. the owner-bound ``post_close`` record, written even when the invocation
    or the parse failed (exit 8 if it cannot be written).

The command spawns only the A2a probe (steps 3 and 5) and ``shipment ship``.
It never archives, moves, or edits a deliberation or any other artifact.
The CLI wiring and ``--json`` rendering are A3d.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from autoharness.gates.cascade_evidence import (
    DECLARED_STATUS_MISSING,
    CascadeEvidenceError,
    engine_semantics_from_record,
    redact,
    serialize_evidence_record,
)
from autoharness.gates.shipment_closure import (
    ClosePath,
    LinkedDeliberationDispositionPlan,
    compute_linked_deliberation_disposition,
)
from autoharness.shipment_close import (
    EXIT_INPUT,
    EXIT_INVOCATION_INDETERMINATE,
    EXIT_LOCKED,
    EXIT_OK,
    EXIT_POST_WRITE_FAILED,
    EXIT_POSTCONDITION_FAILED,
    EXIT_REVALIDATION_DRIFT,
    EXIT_SAFE_CLOSE_SELECTED,
)
from autoharness.shipment_close.observation import locate_record
from autoharness.shipment_close.persist import (
    MODE_MUTATING,
    PairLock,
    PersistError,
    StreamCapture,
    TakeoverRefusedError,
    _read_no_follow,
    acquire_pair_lock,
    check_existing_record,
    redact_record_free_text,
    write_evidence_atomic,
)
from autoharness.shipment_close.postclose import (
    MUTATION_INDETERMINATE,
    ParsedResult,
    ParseError,
    PostCloseReread,
    RereadRecord,
    derive_mutation_state,
    disposition_byte_identical,
    evaluate_linked_deliberation_drift,
    evaluate_postconditions,
    parse_ship_response,
)
from autoharness.shipment_close.preclose import (
    PreCloseError,
    PreCloseSnapshot,
    _contain_plan_paths,
    _record_problems,
    build_pre_close_record,
    run_preclose,
    validate_preclose_inputs,
)
from autoharness.shipment_close.runner import (
    DEFAULT_TIMEOUT_SECONDS,
    BoundedRunResult,
    ResolvedBinary,
    hash_binary,
    run_bounded,
    validate_timeout,
)

__all__ = [
    "MAX_SHIP_TEXT_LENGTH",
    "CascadeCloseOutcome",
    "build_ship_argv",
    "run_cascade_close",
    "validate_ship_text",
]

MAX_SHIP_TEXT_LENGTH: Final = 1024
_DRIFT_HALT: Final = "HALT — cascade pre-invocation revalidation drift detected"
_SELECTIONS: Final = frozenset({ClosePath.CASCADE.value, ClosePath.SAFE_CLOSE.value})
_ABSENT: Final = object()


@dataclass(frozen=True)
class CascadeCloseOutcome:
    """The command outcome A3d renders; ``phase_written`` is the last phase this run wrote."""

    exit_code: int
    message: str
    evidence_path: Path | None = None
    phase_written: str | None = None
    classifier_verdict: str | None = None
    engine_verdict: str | None = None
    selected_close_path: str | None = None
    mutation_state: str | None = None
    postcondition_verdict: str | None = None
    failures: tuple[str, ...] = ()


class _Halt(Exception):
    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass
class _State:
    evidence_path: Path | None = None
    phase_written: str | None = None
    classifier_verdict: str | None = None
    engine_verdict: str | None = None
    selected_close_path: str | None = None
    mutation_state: str | None = None
    postcondition_verdict: str | None = None
    failures: tuple[str, ...] = ()

    def note(self, snapshot: PreCloseSnapshot) -> None:
        self.classifier_verdict = snapshot.classifier.close_path.name
        self.engine_verdict = snapshot.engine.verdict.value
        self.selected_close_path = snapshot.selected_close_path.value

    def outcome(self, exit_code: int, message: str) -> CascadeCloseOutcome:
        fields = {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}
        return CascadeCloseOutcome(exit_code=exit_code, message=message, **fields)


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_ship_text(value: object, flag: str) -> str:
    """Step 2: non-empty, no NUL or newline (CR or LF), at most 1,024 characters (exit 2)."""

    if (
        type(value) is not str
        or value == ""
        or any(character in value for character in ("\x00", "\n", "\r"))
        or len(value) > MAX_SHIP_TEXT_LENGTH
    ):
        raise PreCloseError(
            f"{flag} must be a non-empty string of at most {MAX_SHIP_TEXT_LENGTH} characters "
            "with no NUL or newline"
        )
    return value


def build_ship_argv(
    resolved: ResolvedBinary, root: Path, shipment_id: str, merge_commit_sha: str, message: str, author: str
) -> list[str]:
    """The fixed step 8 argv (``--cwd`` is the workspace root)."""

    return [
        *resolved.argv_prefix,
        "--no-update-check",
        "--jsonrpc",
        "--cwd",
        str(root),
        "shipment",
        "ship",
        shipment_id,
        "--sha",
        merge_commit_sha,
        "--message",
        message,
        "--author",
        author,
    ]


# ---------------------------------------------------------------------------
# Comparison over the persisted encoding
# ---------------------------------------------------------------------------


def _comparable(record: Mapping[str, object]) -> dict:
    """The record as it is persisted (redacted, canonical), minus ``run_id`` and ``pre_close.captured_at``."""

    redacted, _ = redact_record_free_text(record)
    canonical = json.loads(serialize_evidence_record(redacted))
    canonical.pop("run_id", None)
    pre_close = canonical.get("pre_close")
    if isinstance(pre_close, dict):
        pre_close.pop("captured_at", None)
    return canonical


def _differences(fresh: Mapping[str, object], recorded: Mapping[str, object]) -> list[str]:
    left, right = _comparable(fresh), _comparable(recorded)
    differences = []
    for key in sorted(set(left) | set(right)):
        old, new = right.get(key, _ABSENT), left.get(key, _ABSENT)
        if isinstance(old, dict) and isinstance(new, dict) and key in ("pre_close", "tool"):
            differences.extend(
                f"{key}.{sub}" for sub in sorted(set(old) | set(new)) if old.get(sub, _ABSENT) != new.get(sub, _ABSENT)
            )
        elif old != new:
            differences.append(key)
    return differences


def _selected_path(record: Mapping[str, object]) -> object:
    pre_close = record.get("pre_close")
    selection = pre_close.get("close_path_selection") if isinstance(pre_close, Mapping) else None
    return selection.get("selected_close_path") if isinstance(selection, Mapping) else None


def _recorded_binary_hash(record: Mapping[str, object]) -> object:
    tool = record.get("tool")
    return tool.get("binary_sha256") if isinstance(tool, Mapping) else None


def _rehash(resolved: ResolvedBinary) -> str | None:
    try:
        return hash_binary(resolved.binary_path)
    except PersistError:
        return None


# ---------------------------------------------------------------------------
# Steps 3-7 (pre-invocation)
# ---------------------------------------------------------------------------


def _snapshot(workspace: Path, shipment_id: str, feature_id: str, resolved: ResolvedBinary) -> PreCloseSnapshot:
    try:
        return run_preclose(workspace, shipment_id, feature_id, resolved=resolved)
    except PreCloseError as exc:
        raise _Halt(exc.exit_code, str(exc)) from exc


def _write_pre_close(lock: PairLock, record: Mapping[str, object], owner: str, takeover: str | None) -> None:
    try:
        write_evidence_atomic(lock.evidence_path, record, owner_run_id=owner, takeover_from_run_id=takeover)
    except TakeoverRefusedError as exc:
        raise _Halt(EXIT_REVALIDATION_DRIFT, f"{exc}; nothing invoked") from exc
    except CascadeEvidenceError as exc:
        raise _Halt(EXIT_INPUT, f"the pre_close record could not be written: {exc}; nothing invoked") from exc


def _check_handed_off(fresh: Mapping[str, object], handed_off: Mapping[str, object], resolved: ResolvedBinary) -> None:
    """Step 3 against a ``cascade``-selected ``--classify-only`` record: any difference exits 4."""

    differences = _differences(fresh, handed_off)
    if _rehash(resolved) != _recorded_binary_hash(handed_off):
        differences.append("tool.binary_sha256 (re-hashed)")
    if differences:
        raise _Halt(
            EXIT_REVALIDATION_DRIFT,
            f"the fresh pre-close result differs from the cascade-selected --classify-only record in "
            f"{differences}; the record is left byte-identical and nothing is invoked (never SAFE_CLOSE)",
        )


def _read_durable(lock: PairLock) -> dict:
    try:
        durable = json.loads(_read_no_follow(lock.evidence_path).decode("utf-8"))
    except (OSError, ValueError, CascadeEvidenceError) as exc:
        raise _Halt(EXIT_REVALIDATION_DRIFT, f"{_DRIFT_HALT}: the durable pre_close record cannot be re-read: {exc}")
    if not isinstance(durable, dict):
        raise _Halt(EXIT_REVALIDATION_DRIFT, f"{_DRIFT_HALT}: the durable pre_close record is not an object")
    return durable


def _revalidate(
    workspace: Path,
    lock: PairLock,
    shipment_id: str,
    feature_id: str,
    merge_commit_sha: str,
    owner: str,
    resolved: ResolvedBinary,
) -> tuple[PreCloseSnapshot, dict]:
    """Step 5: recompute the whole snapshot (and re-probe) and compare it with the durable record."""

    durable = _read_durable(lock)
    try:
        snapshot = run_preclose(workspace, shipment_id, feature_id, resolved=resolved)
    except PreCloseError as exc:
        raise _Halt(EXIT_REVALIDATION_DRIFT, f"{_DRIFT_HALT}: the snapshot cannot be recomputed: {exc}") from exc
    recomputed = build_pre_close_record(snapshot, merge_commit_sha=merge_commit_sha, run_id=owner)
    differences = _differences(recomputed, durable)
    if durable.get("run_id") != owner or durable.get("phase") != "pre_close":
        differences.append("run_id/phase")
    if differences:
        raise _Halt(EXIT_REVALIDATION_DRIFT, f"{_DRIFT_HALT}: {differences}; nothing invoked (never SAFE_CLOSE)")
    return snapshot, durable


# ---------------------------------------------------------------------------
# Steps 8-10 (invocation and post-close)
# ---------------------------------------------------------------------------


def _spawn_failed(argv: list[str], started_at: str) -> BoundedRunResult:
    return BoundedRunResult(
        argv=tuple(argv),
        exit_code=None,
        timed_out=False,
        started_at=started_at,
        finished_at=_utc_now(),
        stdout=StreamCapture(parse_buffer=True).finish(),
        stderr=StreamCapture().finish(),
    )


def _parse(result: BoundedRunResult, spawn_error: str | None) -> ParsedResult | ParseError:
    if spawn_error is not None:
        return ParseError(f"backlogit could not be spawned: {redact(spawn_error)[0]}")
    if result.stdout.parse_error is not None:
        return ParseError(result.stdout.parse_error)
    if result.stdout.parse_bytes is None:
        return ParseError("stdout was not retained for parsing")
    return parse_ship_response(result.stdout.parse_bytes)


def _reread(snapshot: PreCloseSnapshot, disposition: LinkedDeliberationDispositionPlan | None) -> PostCloseReread:
    ids = {snapshot.shipment_id, *snapshot.manifest_ids}
    descendants = snapshot.pre_close.get("out_of_manifest_descendants")
    if isinstance(descendants, list):
        ids.update(entry["id"] for entry in descendants if isinstance(entry, Mapping) and type(entry.get("id")) is str)
    records: dict[str, RereadRecord] = {}
    unreadable: set[str] = set()
    for artifact_id in sorted(ids):
        try:
            located = locate_record(snapshot.backlog_dir, artifact_id)
        except CascadeEvidenceError:
            unreadable.add(artifact_id)
            continue
        if located is None:
            continue
        frontmatter = located.frontmatter
        records[artifact_id] = RereadRecord(
            location=located.location,
            sha256=located.sha256,
            declared_status=located.declared_status,
            parent_id=located.parent_id,
            archived_status=frontmatter.get("archived_status", DECLARED_STATUS_MISSING),
        )
    shipment = records.pop(snapshot.shipment_id, None)
    return PostCloseReread(
        shipment=shipment, records=records, disposition=disposition, unreadable_ids=frozenset(unreadable)
    )


def _recollect(snapshot: PreCloseSnapshot, durable: Mapping[str, object]) -> LinkedDeliberationDispositionPlan:
    """Re-collect the disposition with the pre-close manifest IDs and the recorded engine decision."""

    try:
        pre_close = durable["pre_close"]
        engine, _ = engine_semantics_from_record(pre_close["engine_semantics"])  # type: ignore[index]
        plan = compute_linked_deliberation_disposition(
            snapshot.manifest_ids, snapshot.shipment_id, snapshot.backlog_dir, engine=engine
        )
    except Exception as exc:  # noqa: BLE001 - an unusable re-collection is planning_error drift, never a skip
        return LinkedDeliberationDispositionPlan(
            shipment_id=snapshot.shipment_id,
            engine=None,
            dispositions=(),
            unresolved_references=(),
            planning_error=f"the post-close re-collection failed: {type(exc).__name__}: {exc}",
        )
    if plan.planning_error is None:
        try:
            plan = _contain_plan_paths(plan, snapshot.backlog_dir.name)
        except PreCloseError as exc:
            plan = dataclasses.replace(plan, planning_error=str(exc))
    return plan


def _evaluate(
    snapshot: PreCloseSnapshot, durable: Mapping[str, object], result: BoundedRunResult, parsed: object
) -> tuple[dict[str, object], str]:
    """Step 9; never raises (an evaluation error is itself a recorded failure)."""

    try:
        recollected = _recollect(snapshot, durable)
        reread = _reread(snapshot, recollected)
        archived_ids = parsed.archived_ids if isinstance(parsed, ParsedResult) else ()
        drift = evaluate_linked_deliberation_drift(snapshot, archived_ids, recollected)
        post = evaluate_postconditions(
            snapshot,
            parsed,  # type: ignore[arg-type]
            reread,
            linked_deliberation_drift=drift,
            disposition_byte_identical=disposition_byte_identical(drift),
        )
        mutation_state = derive_mutation_state(
            snapshot, parsed, reread, exit_code=result.exit_code, timed_out=result.timed_out  # type: ignore[arg-type]
        )
        return post.to_record(), mutation_state
    except Exception as exc:  # noqa: BLE001 - the failure evidence must still be written
        message = f"evaluation_error: {type(exc).__name__}: {exc}"
        parse_error = parsed.message if isinstance(parsed, ParseError) else None
        return (
            {"parse_error": parse_error, "postcondition_verdict": "fail", "failures": [message]},
            MUTATION_INDETERMINATE,
        )


def _invoke_and_finalize(
    lock: PairLock,
    state: _State,
    snapshot: PreCloseSnapshot,
    durable: dict,
    argv: list[str],
    owner: str,
    timeout: int,
) -> CascadeCloseOutcome:
    invocation_started = _utc_now()
    invoking = dict(durable)
    invoking["phase"] = "invoking"
    invoking["invocation"] = {"argv_redacted": [redact(item)[0] for item in argv], "started_at": invocation_started}
    try:
        write_evidence_atomic(lock.evidence_path, invoking, owner_run_id=owner)
    except CascadeEvidenceError as exc:
        raise _Halt(EXIT_INPUT, f"the invoking record could not be written: {exc}; nothing invoked") from exc
    state.phase_written = "invoking"

    spawn_error: str | None = None
    try:
        result = run_bounded(argv, cwd=lock.workspace, timeout=timeout)
    except PersistError as exc:
        spawn_error = str(exc)
        result = _spawn_failed(argv, invocation_started)

    parsed = _parse(result, spawn_error)
    post_close, mutation_state = _evaluate(snapshot, durable, result, parsed)
    state.mutation_state = mutation_state
    state.postcondition_verdict = str(post_close.get("postcondition_verdict"))
    failures = post_close.get("failures")
    state.failures = tuple(str(item) for item in failures) if isinstance(failures, list) else ()

    final = dict(invoking)
    final["phase"] = "post_close"
    final["invocation"] = {
        "argv_redacted": invoking["invocation"]["argv_redacted"],
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "mutation_state": mutation_state,
        "stdout": result.stdout.to_record(),
        "stderr": result.stderr.to_record(),
    }
    final["post_close"] = post_close

    invocation_failed = (
        spawn_error is not None or result.timed_out or result.exit_code != 0 or not isinstance(parsed, ParsedResult)
    )
    try:
        write_evidence_atomic(lock.evidence_path, final, owner_run_id=owner)
    except (CascadeEvidenceError, OSError) as exc:
        return state.outcome(
            EXIT_POST_WRITE_FAILED,
            f"the post_close record could not be written after the invocation: {exc}; operator review required",
        )
    state.phase_written = "post_close"

    if invocation_failed:
        if spawn_error is not None:
            reason = spawn_error
        elif result.timed_out:
            reason = "timed out"
        elif result.exit_code != 0:
            reason = f"exit code {result.exit_code}"
        else:
            reason = f"stdout did not parse: {getattr(parsed, 'message', parsed)}"
        return state.outcome(
            EXIT_INVOCATION_INDETERMINATE, f"backlogit shipment ship failed ({reason}); operator review required"
        )
    if state.postcondition_verdict != "pass":
        return state.outcome(EXIT_POSTCONDITION_FAILED, "a postcondition failed; operator review required")
    return state.outcome(EXIT_OK, "cascade close completed; every postcondition passed")


# ---------------------------------------------------------------------------
# The command
# ---------------------------------------------------------------------------


def _run_locked(
    lock: PairLock,
    state: _State,
    *,
    shipment_id: str,
    feature_id: str,
    merge_commit_sha: str,
    message: str,
    author: str,
    resolved: ResolvedBinary,
    timeout: int,
) -> CascadeCloseOutcome:
    owner = lock.run_id
    workspace = lock.workspace

    # Step 1: the existing-record check, before any classification.
    try:
        existing = check_existing_record(lock, mode=MODE_MUTATING)
    except PersistError as exc:
        raise _Halt(exc.exit_code, str(exc)) from exc
    if existing is not None and _selected_path(existing) not in _SELECTIONS:
        raise _Halt(
            EXIT_LOCKED, "the existing pre_close record carries no recognizable close-path selection (operator review)"
        )
    handed_off = existing if existing is not None and _selected_path(existing) == ClosePath.CASCADE.value else None

    # Step 2.
    try:
        validate_ship_text(message, "--message")
        validate_ship_text(author, "--author")
    except PreCloseError as exc:
        raise _Halt(exc.exit_code, str(exc)) from exc

    # Step 3.
    snapshot = _snapshot(workspace, shipment_id, feature_id, resolved)
    state.note(snapshot)
    fresh = build_pre_close_record(snapshot, merge_commit_sha=merge_commit_sha, run_id=owner)
    if handed_off is not None:
        _check_handed_off(fresh, handed_off, resolved)
    problems = _record_problems(fresh, snapshot)
    if problems:
        raise _Halt(EXIT_INPUT, f"the pre_close record fails validation: {problems}")
    takeover = existing.get("run_id") if existing is not None else None  # type: ignore[assignment]

    if snapshot.selected_close_path is not ClosePath.CASCADE:
        # Only reachable with no cascade-selected record: the engine gate fails closed.
        _write_pre_close(lock, fresh, owner, takeover)
        state.phase_written = "pre_close"
        raise _Halt(
            EXIT_SAFE_CLOSE_SELECTED,
            f"selected {snapshot.selected_close_path.value} ({snapshot.selection[1]}); verdict recorded, nothing invoked",
        )

    # Step 4: the pre_close write (a takeover over any existing pre_close record).
    _write_pre_close(lock, fresh, owner, takeover)
    state.phase_written = "pre_close"

    # Step 5: revalidation, including the engine re-probe.
    revalidated, durable = _revalidate(workspace, lock, shipment_id, feature_id, merge_commit_sha, owner, resolved)

    # Step 6: re-hash the binary immediately before the spawn.
    rehashed = _rehash(resolved)
    if rehashed is None or rehashed != _recorded_binary_hash(durable):
        raise _Halt(
            EXIT_REVALIDATION_DRIFT,
            f"{_DRIFT_HALT}: the resolved binary's SHA-256 changed or cannot be read; nothing invoked",
        )

    # Steps 7-10.
    argv = build_ship_argv(resolved, workspace, shipment_id, merge_commit_sha, message, author)
    return _invoke_and_finalize(lock, state, revalidated, durable, argv, owner, timeout)


def run_cascade_close(
    workspace: Path | str,
    shipment_id: str,
    feature_id: str,
    merge_commit_sha: str,
    *,
    message: str,
    author: str,
    resolved: ResolvedBinary,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    run_id: str | None = None,
) -> CascadeCloseOutcome:
    """Run the mutating ``cascade-close``; returns a frozen :class:`CascadeCloseOutcome` (exit codes per plan A3)."""

    state = _State()
    try:
        validate_preclose_inputs(shipment_id, feature_id, merge_commit_sha)
        validate_timeout(timeout)
    except (PreCloseError, PersistError) as exc:
        return state.outcome(exc.exit_code, str(exc))
    owner = run_id if run_id is not None else uuid.uuid4().hex
    try:
        lock = acquire_pair_lock(workspace, shipment_id, feature_id, owner)
    except PersistError as exc:
        return state.outcome(exc.exit_code, str(exc))
    state.evidence_path = lock.evidence_path
    try:
        return _run_locked(
            lock,
            state,
            shipment_id=shipment_id,
            feature_id=feature_id,
            merge_commit_sha=merge_commit_sha,
            message=message,
            author=author,
            resolved=resolved,
            timeout=timeout,
        )
    except _Halt as halt:
        return state.outcome(halt.exit_code, str(halt))
    except Exception as exc:  # noqa: BLE001 - fail closed; an invoking record means operator review
        exit_code = EXIT_INVOCATION_INDETERMINATE if state.phase_written == "invoking" else EXIT_INPUT
        return state.outcome(exit_code, f"unexpected failure: {type(exc).__name__}: {exc}")
    finally:
        lock.release()
