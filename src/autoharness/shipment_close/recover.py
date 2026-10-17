"""``cascade-close --recover``: evidence-only recovery of an orphaned ``invoking`` record (211-F, plan units T10-T11).

Recovery exists for the run a killed wrapper left behind: an ``invoking`` evidence record, a lock held by a dead
owner (or no lock), and possibly a journal. It never invokes backlogit and never moves, archives, or edits a backlog
artifact. It writes the evidence record (and moves a stale lock to a tombstone) and nothing else; everything it cannot
observe is recorded as unknown, and every doubt is a refusal (exit 10, nothing written).

This module holds the eligibility half (T10): the record and journal checks, owner liveness (hardening H3), child
liveness, a read-only process scan (H11), the settle-window stability proof (H2), the operator confirmations, the
serialized lock takeover (H8), and the recovery-owner rollback of a never-started run (H7 addendum d).
"""

from __future__ import annotations

import contextlib
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from autoharness.backlog_root import BacklogUnavailableError, resolve_backlog_root
from autoharness.gates.cascade_evidence import (
    CascadeEvidenceError,
    build_evidence_path,
    build_recovery_block,
    compute_flat_sets,
    parse_rfc3339_instant,
    unavailable_capture,
    validate_evidence_record,
    validate_evidence_structure,
)
from autoharness.shipment_close import (
    EXIT_INPUT,
    EXIT_INVOCATION_INDETERMINATE,
    EXIT_OK,
    EXIT_POSTCONDITION_FAILED,
    EXIT_RECOVERY_REFUSED,
)
from autoharness.shipment_close.event_log import (
    ENGINE_ACTOR,
    EventLogError,
    attribute_archived_footprint,
    read_cascade_events,
)
from autoharness.shipment_close.journal import (
    STREAM_CAP_BYTES,
    STREAM_FILES,
    Journal,
    JournalError,
    _is_link,
    journal_has,
    journal_path,
    read_json,
)
from autoharness.shipment_close.liveness import Prober, is_process_alive
from autoharness.shipment_close.persist import (
    MODE_RECOVER,
    LockDisposition,
    LockObservation,
    PairLock,
    PersistError,
    RollbackProof,
    _read_no_follow,
    _takeover_verdict,
    check_existing_record,
    observe_lock,
    takeover_stale_lock,
    write_evidence_atomic,
)
from autoharness.shipment_close.postclose import (
    ParsedResult,
    ParseError,
    PostCloseResult,
    disposition_byte_identical as byte_identical_flag,
    evaluate_linked_deliberation_drift,
    evaluate_postconditions,
)
from autoharness.shipment_close.quiescence import probe_writers
from autoharness.shipment_close.runner import BoundedRunResult, result_from_journal

__all__ = [
    "DEFAULT_SETTLE_SECONDS",
    "MIN_SETTLE_SECONDS",
    "Eligibility",
    "RecoverEnv",
    "RecoverOptions",
    "RecoverOutcome",
    "assess_eligibility",
    "list_processes",
    "recover_cascade_close",
]

MIN_SETTLE_SECONDS: Final = 5.0
DEFAULT_SETTLE_SECONDS: Final = 15.0
_PROCESS_LIST_TIMEOUT_SECONDS: Final = 60
_EXITED_STATES: Final = frozenset({"exited", "timed_out"})
_NON_RECORD_PREFIXES: Final = ("record.phase:", "record.invocation", "record.post_close")
_ID_END: Final = r"(?![A-Za-z0-9._-])"


class _Refused(Exception):
    def __init__(self, message: str, exit_code: int = EXIT_RECOVERY_REFUSED) -> None:
        super().__init__(message)
        self.exit_code = exit_code


# ---------------------------------------------------------------------------
# Read-only process scan (hardening H11)
# ---------------------------------------------------------------------------


def list_processes() -> list[tuple[int, str]] | None:
    """``(pid, command line)`` of every process, read-only; ``None`` when the listing cannot be trusted."""

    try:
        if os.name == "nt":
            shell = shutil.which("powershell") or shutil.which("pwsh")
            if shell is None:
                return None
            script = (
                "Get-CimInstance Win32_Process | ForEach-Object "
                '{ "$($_.ProcessId)`t$($_.CommandLine)" }'
            )
            argv = [shell, "-NoProfile", "-NonInteractive", "-Command", script]
        else:
            argv = ["ps", "-eo", "pid=,args="]
        completed = subprocess.run(
            argv, capture_output=True, text=True, timeout=_PROCESS_LIST_TIMEOUT_SECONDS, check=False
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if completed.returncode != 0:
        return None
    processes: list[tuple[int, str]] = []
    for line in completed.stdout.splitlines():
        head, _, rest = line.strip().partition("\t" if os.name == "nt" else " ")
        if head.isdigit():
            processes.append((int(head), rest.strip()))
    return processes or None


def _ship_processes(processes: Sequence[tuple[int, str]], shipment_id: str) -> list[int]:
    pattern = re.compile(r"shipment\s+ship\s+" + re.escape(shipment_id) + _ID_END)
    own = os.getpid()
    return [
        pid for pid, line in processes if pid != own and "backlogit" in line.lower() and pattern.search(line)
    ]


# ---------------------------------------------------------------------------
# Options, environment seams, results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecoverOptions:
    dry_run: bool = False
    confirm_owner_dead: bool = False
    confirm_engine_stopped: bool = False
    settle_seconds: float = DEFAULT_SETTLE_SECONDS


@dataclass(frozen=True)
class RecoverEnv:
    """Injection seams: liveness prober, local host name, process listing, and the settle sleep."""

    prober: Prober | None = None
    local_host: str | None = None
    list_processes: Callable[[], Sequence[tuple[int, str]] | None] = list_processes
    sleep: Callable[[float], None] = time.sleep


@dataclass(frozen=True)
class RecoverOutcome:
    exit_code: int
    message: str
    evidence_path: Path | None = None
    journal_path: Path | None = None
    dry_run: bool = False
    recovered: bool = False
    recovery_mode: str | None = None
    action: str | None = None  # reconstruct | rollback
    phase_written: str | None = None
    lock_disposition: LockDisposition | None = None
    postcondition_verdict: str | None = None
    failures: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Eligibility:
    """What the read-only assessment established; nothing here has touched a lock or an evidence record."""

    record: dict
    journal: Journal | None
    exit_record: dict | None
    child_started: dict | None
    observed_lock: LockObservation | None
    rollback: bool
    planned_lock: LockDisposition
    notes: tuple[str, ...] = field(default=())


@dataclass(frozen=True)
class _RecoverySnapshot:
    """The subset of the pre-close snapshot that the post-close re-read and INV-10 evaluation consume."""

    shipment_id: str
    feature_id: str
    backlog_dir: Path
    manifest_ids: tuple[str, ...]
    pre_close: dict


# ---------------------------------------------------------------------------
# Eligibility
# ---------------------------------------------------------------------------


def _read_record(evidence: Path, shipment_id: str, feature_id: str) -> dict:
    if not os.path.lexists(evidence):
        raise _Refused("there is no evidence record to recover", EXIT_INPUT)
    try:
        record = json.loads(_read_no_follow(evidence).decode("utf-8"))
    except (OSError, ValueError, PersistError) as exc:
        raise _Refused(f"the evidence record cannot be read (operator review): {exc}") from exc
    if not isinstance(record, dict):
        raise _Refused("the evidence record is not a JSON object (operator review)")
    phase = record.get("phase")
    if phase == "post_close":
        raise _Refused("evidence already finalized", EXIT_INPUT)
    if phase == "pre_close":
        raise _Refused("no invoking evidence record to recover (the record is pre_close)", EXIT_INPUT)
    if phase != "invoking":
        raise _Refused(f"the evidence record is in an unknown phase {phase!r} (operator review)")
    if record.get("shipment_id") != shipment_id or record.get("feature_id") != feature_id:
        raise _Refused("the evidence record names a different pair (operator review)")
    if not (type(record.get("run_id")) is str and re.fullmatch(r"[0-9a-f]{32}", record["run_id"])):
        raise _Refused("the invoking record carries no valid run_id (operator review)")
    return record


def _check_invoking_record(record: Mapping[str, object], shipment_id: str, feature_id: str) -> None:
    problems = [
        problem
        for problem in validate_evidence_record(
            record, shipment_id=shipment_id, feature_id=feature_id, close_path="cascade"
        )
        if not problem.startswith(_NON_RECORD_PREFIXES)
    ]
    invocation = record.get("invocation")
    if not isinstance(invocation, Mapping):
        problems.append("record.invocation: the invoking record carries no invocation section")
    else:
        if parse_rfc3339_instant(invocation.get("started_at")) is None:
            problems.append("record.invocation.started_at: must be an RFC 3339 timestamp")
        argv = invocation.get("argv_redacted")
        if not (type(argv) is list and argv and all(type(item) is str for item in argv)):
            problems.append("record.invocation.argv_redacted: must be a non-empty list of strings")
    if problems:
        raise _Refused(f"the pre_close part of the invoking record is not valid (operator review): {problems[:3]}")


def _load_journal(
    workspace: Path | str, shipment_id: str, feature_id: str, record: Mapping[str, object]
) -> tuple[Journal | None, dict | None, dict | None, list[str]]:
    """``(journal, exit.json, child_started.json, notes)``; a missing or foreign journal is ``None`` (legacy)."""

    notes: list[str] = []
    try:
        directory = journal_path(workspace, shipment_id, feature_id)
    except JournalError as exc:
        raise _Refused(str(exc), EXIT_INPUT) from exc
    if not os.path.lexists(directory):
        return None, None, None, ["no journal exists for this pair (a legacy record)"]
    if _is_link(directory) or not directory.is_dir():
        raise _Refused("the journal location is a link or not a directory (operator review)")
    journal = Journal(path=directory, run_id=str(record["run_id"]))
    if not journal_has(journal, "meta.json"):
        return None, None, None, ["the journal directory holds no meta.json (treated as a legacy record)"]
    try:
        meta = read_json(journal, "meta.json")
    except JournalError as exc:
        if "belongs to another run" in str(exc):
            return None, None, None, ["the journal belongs to a different run (treated as a legacy record)"]
        raise _Refused(f"the journal cannot be read (operator review): {exc}") from exc
    recorded = record["invocation"].get("argv_sha256") if isinstance(record.get("invocation"), Mapping) else None
    if meta["shipment_id"] != shipment_id or meta["feature_id"] != feature_id:
        raise _Refused("the journal names a different pair (operator review)")
    if recorded is not None and meta["argv_sha256"] != recorded:
        raise _Refused("the journal's argv_sha256 differs from the invoking record's (operator review)")
    exit_record = child_started = None
    for name in ("exit.json", "child_started.json"):
        if not journal_has(journal, name):
            continue
        try:
            value = read_json(journal, name)
        except JournalError as exc:
            raise _Refused(f"the journal's {name} cannot be read (operator review): {exc}") from exc
        if name == "exit.json":
            exit_record = value
        else:
            child_started = value
    return journal, exit_record, child_started, notes


def _check_lock(
    workspace: Path | str,
    shipment_id: str,
    feature_id: str,
    record: Mapping[str, object],
    options: RecoverOptions,
    env: RecoverEnv,
    *,
    rollback: bool,
) -> tuple[LockObservation | None, str, LockDisposition]:
    try:
        observed = observe_lock(workspace, shipment_id, feature_id)
    except PersistError as exc:
        raise _Refused(f"the pair lock cannot be read (operator review): {exc}") from exc
    if observed is None:
        return None, "no lock exists", LockDisposition("absent", None, None, "lock_absent")
    # A lock naming another run (for example a recovery run that crashed after its takeover, H8) is judged by owner
    # liveness alone: provably dead means stale, anything else refuses.
    try:
        action, basis = _takeover_verdict(
            observed, confirm_owner_dead=options.confirm_owner_dead, prober=env.prober, local_host=env.local_host
        )
    except PersistError as exc:
        raise _Refused(f"the lock owner is not provably dead: {exc}") from exc
    if rollback and action == "operator_confirmed":
        raise _Refused("a never-started rollback requires a provably dead lock owner, not an operator confirmation")
    return observed, f"lock owner dead ({basis})", LockDisposition(action, observed.pid, observed.host, basis)


def _check_child(exit_record: Mapping[str, object] | None, child_started: Mapping[str, object] | None, env: RecoverEnv) -> str:
    """The journaled child must be gone: a shim exit sentinel, else a dead journaled pid (alive or unknown refuses)."""

    if exit_record is not None and exit_record["state"] in _EXITED_STATES:
        return "the shim recorded the child's exit"
    pid = child_started.get("pid") if child_started is not None else None
    if type(pid) is int:
        alive = is_process_alive(pid, prober=env.prober)
        if alive is not False:
            raise _Refused(f"the journaled child (pid {pid}) is alive or its state is unknown; it may still be mutating")
        return f"the journaled child (pid {pid}) is gone"
    return "no journaled child pid (the process scan and the settle window decide)"


def _scan_for_ship(shipment_id: str, env: RecoverEnv) -> None:
    try:
        processes = env.list_processes()
    except Exception as exc:  # noqa: BLE001 - an unreadable scan is "unknown", never a pass
        raise _Refused(f"the process scan failed ({type(exc).__name__}); recovery is refused (operator review)") from exc
    if processes is None:
        raise _Refused("the process list cannot be read; whether the engine is running is unknown (operator review)")
    running = _ship_processes(processes, shipment_id)
    if running:
        raise _Refused(f"a backlogit 'shipment ship {shipment_id}' process is running (pid {running[0]}); wait for it")


def _snapshot(workspace: Path | str, record: Mapping[str, object]) -> _RecoverySnapshot:
    try:
        backlog_dir = resolve_backlog_root(Path(workspace).resolve())
    except (BacklogUnavailableError, OSError) as exc:
        raise _Refused(f"the backlog root cannot be resolved: {exc}") from exc
    pre_close = record["pre_close"]
    members = pre_close.get("manifest_members") if isinstance(pre_close, Mapping) else None
    if type(members) is not list:
        raise _Refused("the invoking record carries no manifest members (operator review)")
    ids = tuple(member["id"] for member in members if isinstance(member, Mapping) and type(member.get("id")) is str)
    return _RecoverySnapshot(
        shipment_id=str(record["shipment_id"]),
        feature_id=str(record["feature_id"]),
        backlog_dir=backlog_dir,
        manifest_ids=ids,
        pre_close=pre_close,  # type: ignore[arg-type]
    )


def _live_fingerprint(snapshot: _RecoverySnapshot) -> str:
    """Digest of the live backlog state plus the engine logs' size and mtime (progress shows in the logs)."""

    from autoharness.shipment_close import command

    reread = command._reread(snapshot, None)  # type: ignore[arg-type]
    parts: list[object] = [
        None if reread.shipment is None else (reread.shipment.location, reread.shipment.sha256),
        sorted((key, value.location, value.sha256) for key, value in reread.records.items()),
        sorted(reread.unreadable_ids),
    ]
    logs = []
    for artifact_id in sorted({snapshot.shipment_id, *snapshot.manifest_ids}):
        path = snapshot.backlog_dir / "logs" / f"{artifact_id}.jsonl"
        try:
            stat = path.stat()
            logs.append((artifact_id, stat.st_size, stat.st_mtime_ns))
        except OSError:
            logs.append((artifact_id, None, None))
    parts.append(logs)
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _settle(snapshot: _RecoverySnapshot, seconds: float, env: RecoverEnv) -> None:
    before = _live_fingerprint(snapshot)
    env.sleep(seconds)
    if _live_fingerprint(snapshot) != before:
        raise _Refused(
            f"the live backlog state changed during the {seconds:g} s settle window; the engine may still be running"
        )


def validate_settle_seconds(value: object) -> float:
    if type(value) not in (int, float) or value < MIN_SETTLE_SECONDS:
        raise _Refused(f"the settle window may only be raised above {MIN_SETTLE_SECONDS:g} s", EXIT_INPUT)
    return float(value)


def assess_eligibility(
    workspace: Path | str,
    shipment_id: str,
    feature_id: str,
    options: RecoverOptions = RecoverOptions(),
    env: RecoverEnv = RecoverEnv(),
) -> Eligibility:
    """Read-only eligibility; raises :class:`_Refused` (exit 10, or 2 for input errors). Takes no lock, writes nothing."""

    validate_settle_seconds(options.settle_seconds)
    try:
        evidence = build_evidence_path(workspace, shipment_id, feature_id)
    except CascadeEvidenceError as exc:
        raise _Refused(str(exc), EXIT_INPUT) from exc
    record = _read_record(evidence, shipment_id, feature_id)
    _check_invoking_record(record, shipment_id, feature_id)
    journal, exit_record, child_started, notes = _load_journal(workspace, shipment_id, feature_id, record)
    never_started = exit_record is not None and exit_record["state"] == "never_started"
    if never_started and child_started is not None:
        raise _Refused("the journal holds both a never_started sentinel and a child_started record (operator review)")

    if never_started:
        observed, lock_note, planned = _check_lock(
            workspace, shipment_id, feature_id, record, options, env, rollback=True
        )
        notes.append("the original run persisted never_started and never spawned a child: rollback to pre_close")
        notes.append(lock_note)
        return Eligibility(record, journal, exit_record, child_started, observed, True, planned, tuple(notes))

    if journal is None and not options.confirm_engine_stopped:
        raise _Refused(
            "this record has no journal, so nothing proves the engine stopped; "
            "re-run with --confirm-engine-stopped once the operator has verified it"
        )
    observed, lock_note, planned = _check_lock(workspace, shipment_id, feature_id, record, options, env, rollback=False)
    notes.append(lock_note)
    notes.append(_check_child(exit_record, child_started, env))
    _scan_for_ship(shipment_id, env)
    notes.append("no 'backlogit shipment ship' process is running")
    _settle(_snapshot(workspace, record), options.settle_seconds, env)
    notes.append(f"the live state was unchanged across the {options.settle_seconds:g} s settle window")
    return Eligibility(record, journal, exit_record, child_started, observed, False, planned, tuple(notes))


# ---------------------------------------------------------------------------
# The command
# ---------------------------------------------------------------------------


def _rollback(lock: PairLock, eligibility: Eligibility, recovery_run_id: str) -> None:
    record = {key: value for key, value in eligibility.record.items() if key not in ("invocation", "post_close")}
    record["phase"] = "pre_close"
    record["run_id"] = recovery_run_id
    proof = RollbackProof(
        never_started=True,
        child_started=False,
        original_run_id=str(eligibility.record["run_id"]),
        owner_provably_dead=True,
    )
    write_evidence_atomic(lock.evidence_path, record, owner_run_id=recovery_run_id, rollback_proof=proof)


@dataclass(frozen=True)
class _Reconstruction:
    record: dict
    mode: str
    exit_code: int
    verdict: str
    failures: tuple[str, ...]


def _journal_result(eligibility: Eligibility) -> BoundedRunResult | None:
    """The journaled run result when the journal is a complete, proven capture; ``None`` when it is not.

    Complete means: an exit sentinel, a ``proven`` quiescence verdict for both streams, stream files still exactly the
    size the verdict recorded, no drained-incomplete capture, and no writer holding the files now. Anything less is a
    partial journal (never a passing journal capture).
    """

    journal, exit_record = eligibility.journal, eligibility.exit_record
    if journal is None or exit_record is None:
        return None
    if exit_record["state"] == "spawn_failed":
        raise _Refused("the child could not be spawned and nothing proves what ran next (operator review)")
    verdicts = exit_record["quiescence"]
    if not all(verdicts[key]["proven"] for key in ("stdout", "stderr")):  # type: ignore[index]
        return None
    invocation = eligibility.record["invocation"]
    try:
        launch = read_json(journal, "launch.json")
    except JournalError:
        launch = {
            "argv": invocation["argv_redacted"],
            "stream_cap_bytes": STREAM_CAP_BYTES,
            "created_at": invocation["started_at"],
        }
    try:
        result = result_from_journal(journal, launch)
        for key, name in zip(("stdout", "stderr"), STREAM_FILES):
            if (journal.path / name).stat().st_size != verdicts[key]["total_bytes"]:  # type: ignore[index]
                return None
    except (PersistError, OSError):
        return None
    if result.stdout.drain_incomplete or result.stderr.drain_incomplete:
        return None
    if probe_writers([journal.path / name for name in STREAM_FILES]).clean is not True:
        return None
    return result


def _evaluate_live(snapshot: _RecoverySnapshot, durable: Mapping[str, object], parsed: ParsedResult | ParseError) -> PostCloseResult:
    from autoharness.shipment_close import command

    try:
        recollected = command._recollect(snapshot, durable)  # type: ignore[arg-type]
        reread = command._reread(snapshot, recollected)  # type: ignore[arg-type]
        archived = parsed.archived_ids if isinstance(parsed, ParsedResult) else ()
        drift = evaluate_linked_deliberation_drift(snapshot, archived, recollected)  # type: ignore[arg-type]
        return evaluate_postconditions(
            snapshot,  # type: ignore[arg-type]
            parsed,
            reread,
            linked_deliberation_drift=drift,
            disposition_byte_identical=byte_identical_flag(drift),
        )
    except Exception as exc:  # noqa: BLE001 - an unevaluable live state is a refusal, never a guess
        raise _Refused(f"the live postconditions could not be evaluated: {type(exc).__name__}: {exc}") from exc


def _engine_footprint(snapshot: _RecoverySnapshot, record: Mapping[str, object]) -> tuple[ParsedResult, str, str]:
    """Rebuild the engine result from the engine's own event log, or refuse (hardening H1).

    Needs exactly one engine-authored ``shipped`` event after ``invocation.started_at`` and, for every required id,
    operation-correlated archival with no foreign-actor event on the items in the window. Real backlogit logs do not
    carry the correlation on ``archived`` events (spike 2026-10-16), so this refuses there.
    """

    started = parse_rfc3339_instant(record["invocation"]["started_at"])  # type: ignore[index]
    if started is None:
        raise _Refused("the invoking record's started_at is not a valid instant (operator review)")
    try:
        events = read_cascade_events(snapshot.backlog_dir, snapshot.shipment_id, started)
    except EventLogError as exc:
        raise _Refused(f"the engine event log cannot be used (it is never treated as empty): {exc}") from exc
    if len(events.shipped_events) != 1:
        raise _Refused(
            f"{len(events.shipped_events)} engine-authored 'shipped' events for {snapshot.shipment_id} after the "
            "invocation started; exactly one is required to attribute the footprint"
        )
    shipped = events.shipped_events[0]
    _, required = compute_flat_sets(snapshot.pre_close, snapshot.shipment_id)
    attribution = attribute_archived_footprint(events, required)
    if not attribution.attributed:
        raise _Refused(
            "the archived footprint cannot be tied to this cascade by operation-correlated engine events "
            f"({attribution.reason}; missing {list(attribution.missing_ids)}, uncorrelated "
            f"{list(attribution.uncorrelated_ids)}, foreign {list(attribution.foreign_event_item_ids)}); "
            "only a complete journal can recover this record (operator review)"
        )
    archived = sorted(
        {e.item_id for e in events.archived_events if e.actor == ENGINE_ACTOR and e.instant >= events.since}
    )
    parsed = ParsedResult(
        shipment_id=snapshot.shipment_id,
        shipment_status="shipped",
        archived_ids=tuple(archived),
        returned_ids=(),
        commit_sha=None,
    )
    return parsed, shipped.timestamp, str(shipped.operation)


def _base_record(eligibility: Eligibility, recovery_run_id: str) -> dict:
    record = {key: value for key, value in eligibility.record.items() if key not in ("invocation", "post_close")}
    record["phase"] = "post_close"
    record["run_id"] = recovery_run_id
    return record


def _lock_block(disposition: LockDisposition) -> dict[str, object]:
    return {
        "action": disposition.action,
        "owner_pid": disposition.owner_pid,
        "owner_host": disposition.owner_host,
        "basis": disposition.basis,
    }


def _exit_code_for(strict_valid: bool, invocation_failed: bool, verdict: str) -> int:
    if invocation_failed:
        return EXIT_INVOCATION_INDETERMINATE
    if verdict != "pass" or not strict_valid:
        return EXIT_POSTCONDITION_FAILED
    return EXIT_OK


def reconstruct(
    workspace: Path | str, eligibility: Eligibility, disposition: LockDisposition, recovery_run_id: str
) -> _Reconstruction:
    """Build and validate the recovered ``post_close`` record without writing it; raises :class:`_Refused`.

    Facts are taken only from what was observed: the proven journal, else the engine's own event log. Every fact that
    neither supplies is ``null`` (a lost stream is the explicit unavailable marker) and says so in ``recovery.facts``.
    """

    original = eligibility.record
    snapshot = _snapshot(workspace, original)
    shipment_id, feature_id = snapshot.shipment_id, snapshot.feature_id
    result = _journal_result(eligibility)
    record = _base_record(eligibility, recovery_run_id)
    invocation_failed = False
    attribution: dict[str, object] | None = None
    argv = original["invocation"]["argv_redacted"]

    if result is not None:
        mode = "journal_complete"
        parsed = _parse_stdout(result)
        post = _evaluate_live(snapshot, original, parsed)
        parsed_ok = isinstance(parsed, ParsedResult)
        completed = parsed_ok and result.exit_code == 0 and not result.timed_out
        invocation_failed = not completed
        engine_fact = "observed_journal" if parsed_ok else "unknown"
        facts = {
            "exit_code": "observed_journal",
            "timed_out": "observed_journal",
            "finished_at": "observed_journal",
            "stdout": "observed_journal",
            "stderr": "observed_journal",
            "archived_ids": engine_fact,
            "returned_ids": engine_fact,
            "commit_sha": engine_fact,
            "mutation_state": "observed_journal",
        }
        record["invocation"] = {
            "argv_redacted": argv,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "mutation_state": "completed" if completed else "indeterminate",
            "stdout": result.stdout.to_record(),
            "stderr": result.stderr.to_record(),
        }
    else:
        mode = "journal_partial" if eligibility.journal is not None else "postconditions_only"
        parsed, shipped_at, operation = _engine_footprint(snapshot, original)
        post = _evaluate_live(snapshot, original, parsed)
        attribution = {"basis": "engine_event_log", "shipped_event_at": shipped_at, "operation": operation}
        exit_record = eligibility.exit_record if mode == "journal_partial" else None
        sentinel = exit_record is not None and exit_record["state"] in _EXITED_STATES
        invocation_failed = bool(sentinel and (exit_record["exit_code"] != 0 or exit_record["timed_out"]))  # type: ignore[index]

        def observed(key: str) -> object | None:
            return exit_record[key] if sentinel else None  # type: ignore[index]

        exit_code_fact = "observed_journal" if observed("exit_code") is not None else "unknown"
        timed_out_fact = "observed_journal" if type(observed("timed_out")) is bool else "unknown"
        journal_finished = observed("finished_at") if type(observed("finished_at")) is str else None
        facts = {
            "exit_code": exit_code_fact,
            "timed_out": timed_out_fact,
            "finished_at": "observed_journal" if journal_finished else "engine_event_log",
            "stdout": "unknown",
            "stderr": "unknown",
            "archived_ids": "engine_event_log",
            "returned_ids": "derived_live_state",
            "commit_sha": "unknown",
            "mutation_state": "derived_live_state",
        }
        record["invocation"] = {
            "argv_redacted": argv,
            "started_at": original["invocation"]["started_at"],
            "finished_at": journal_finished or shipped_at,
            "exit_code": observed("exit_code") if exit_code_fact == "observed_journal" else None,
            "timed_out": observed("timed_out") if timed_out_fact == "observed_journal" else None,
            "mutation_state": "completed" if post.postcondition_verdict == "pass" else "indeterminate",
            "stdout": unavailable_capture("the journal does not hold a complete, proven stdout capture"),
            "stderr": unavailable_capture("the journal does not hold a complete, proven stderr capture"),
        }

    record["post_close"] = post.to_record()
    record["recovery"] = build_recovery_block(
        mode=mode,
        recovered_at=_utc_now(),
        recovery_run_id=recovery_run_id,
        supersedes_run_id=str(original["run_id"]),
        lock_disposition=_lock_block(disposition),
        engine_attribution=attribution,
        facts=facts,
    )
    problems = validate_evidence_structure(record, shipment_id=shipment_id, feature_id=feature_id, close_path="cascade")
    if problems:
        raise _Refused(f"the reconstructed record does not validate; nothing was written: {problems[:3]}")
    strict_valid = not validate_evidence_record(
        record, shipment_id=shipment_id, feature_id=feature_id, close_path="cascade"
    )
    return _Reconstruction(
        record=record,
        mode=mode,
        exit_code=_exit_code_for(strict_valid, invocation_failed, post.postcondition_verdict),
        verdict=post.postcondition_verdict,
        failures=tuple(post.failures),
    )


def _parse_stdout(result: BoundedRunResult) -> ParsedResult | ParseError:
    from autoharness.shipment_close import command

    return command._parse(result, None)


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _reconstruct_and_write(
    lock: PairLock, eligibility: Eligibility, disposition: LockDisposition, recovery_run_id: str
) -> _Reconstruction:
    reconstruction = reconstruct(lock.workspace, eligibility, disposition, recovery_run_id)
    write_evidence_atomic(
        lock.evidence_path,
        reconstruction.record,
        owner_run_id=recovery_run_id,
        recover_from_run_id=str(eligibility.record["run_id"]),
    )
    return reconstruction


def recover_cascade_close(
    workspace: Path | str,
    shipment_id: str,
    feature_id: str,
    *,
    options: RecoverOptions = RecoverOptions(),
    env: RecoverEnv = RecoverEnv(),
    run_id: str | None = None,
) -> RecoverOutcome:
    """Run ``--recover`` (or ``--dry-run``): evidence-only, idempotent, fail closed.

    Exit 10 means refused with nothing written; 2 is an input error or an already-finalized record (also nothing
    written); a never-started run is rolled back to ``pre_close`` and exits 2 (mutation-free: retry attached).
    """

    try:
        evidence = build_evidence_path(workspace, shipment_id, feature_id)
        journal_dir = journal_path(workspace, shipment_id, feature_id)
    except (CascadeEvidenceError, JournalError) as exc:
        return RecoverOutcome(EXIT_INPUT, str(exc), dry_run=options.dry_run)

    def outcome(exit_code: int, message: str, **extra: object) -> RecoverOutcome:
        return RecoverOutcome(
            exit_code, message, evidence_path=evidence, journal_path=journal_dir, dry_run=options.dry_run, **extra
        )  # type: ignore[arg-type]

    try:
        eligibility = assess_eligibility(workspace, shipment_id, feature_id, options, env)
    except _Refused as refused:
        return outcome(refused.exit_code, str(refused))
    action = "rollback" if eligibility.rollback else "reconstruct"
    if options.dry_run:
        if eligibility.rollback:
            return outcome(
                EXIT_OK,
                "dry run: recovery is eligible and would roll the never-started run back to pre_close; "
                "nothing was written",
                action=action,
                notes=eligibility.notes,
            )
        try:
            planned = reconstruct(workspace, eligibility, eligibility.planned_lock, uuid.uuid4().hex)
        except _Refused as refused:
            return outcome(refused.exit_code, f"dry run: {refused}", notes=eligibility.notes)
        return outcome(
            EXIT_OK,
            f"dry run: recovery is eligible and would write a {planned.mode} record "
            f"(postcondition verdict {planned.verdict}); nothing was written",
            action=action,
            recovery_mode=planned.mode,
            lock_disposition=eligibility.planned_lock,
            postcondition_verdict=planned.verdict,
            failures=planned.failures,
            notes=eligibility.notes,
        )
    recovery_run_id = run_id if run_id is not None else uuid.uuid4().hex
    try:
        lock, disposition = takeover_stale_lock(
            workspace,
            shipment_id,
            feature_id,
            recovery_run_id,
            eligibility.observed_lock,
            confirm_owner_dead=options.confirm_owner_dead,
            prober=env.prober,
            local_host=env.local_host,
        )
    except PersistError as exc:
        return outcome(EXIT_RECOVERY_REFUSED, f"the stale lock could not be taken over: {exc}", notes=eligibility.notes)
    try:
        existing = check_existing_record(lock, mode=MODE_RECOVER)
        if (
            existing is None
            or existing.get("run_id") != eligibility.record["run_id"]
            or existing.get("invocation") != eligibility.record["invocation"]
        ):
            raise _Refused("the evidence record changed while recovery was taking the lock (operator review)")
        if eligibility.rollback:
            _rollback(lock, eligibility, recovery_run_id)
            return outcome(
                EXIT_INPUT,
                "the run never started a child: the record was rolled back to pre_close; nothing was invoked "
                "or recovered. Retry the close with an attached cascade-close",
                action="rollback",
                phase_written="pre_close",
                lock_disposition=disposition,
                notes=eligibility.notes,
            )
        reconstruction = _reconstruct_and_write(lock, eligibility, disposition, recovery_run_id)
        return outcome(
            reconstruction.exit_code,
            f"recovered a {reconstruction.mode} post_close record (postcondition verdict {reconstruction.verdict})"
            + ("" if reconstruction.exit_code == EXIT_OK else "; it does not satisfy the closure-evidence gate"),
            recovered=True,
            recovery_mode=reconstruction.mode,
            action=action,
            phase_written="post_close",
            lock_disposition=disposition,
            postcondition_verdict=reconstruction.verdict,
            failures=reconstruction.failures,
            notes=eligibility.notes,
        )
    except _Refused as refused:
        return outcome(refused.exit_code, str(refused), lock_disposition=disposition, notes=eligibility.notes)
    except PersistError as exc:
        code = EXIT_INPUT if exc.exit_code == EXIT_INPUT else EXIT_RECOVERY_REFUSED
        return outcome(code, str(exc), lock_disposition=disposition, notes=eligibility.notes)
    finally:
        with contextlib.suppress(Exception):
            lock.release()
