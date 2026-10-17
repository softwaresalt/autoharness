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
    parse_rfc3339_instant,
    validate_evidence_record,
)
from autoharness.shipment_close import EXIT_INPUT, EXIT_OK, EXIT_RECOVERY_REFUSED
from autoharness.shipment_close.journal import (
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
) -> tuple[LockObservation | None, str]:
    try:
        observed = observe_lock(workspace, shipment_id, feature_id)
    except PersistError as exc:
        raise _Refused(f"the pair lock cannot be read (operator review): {exc}") from exc
    if observed is None:
        return None, "no lock exists"
    if observed.parsed and observed.run_id != record["run_id"]:
        raise _Refused("the pair lock is held by a run other than the one that wrote the invoking record")
    try:
        action, basis = _takeover_verdict(
            observed, confirm_owner_dead=options.confirm_owner_dead, prober=env.prober, local_host=env.local_host
        )
    except PersistError as exc:
        raise _Refused(f"the lock owner is not provably dead: {exc}") from exc
    if rollback and action == "operator_confirmed":
        raise _Refused("a never-started rollback requires a provably dead lock owner, not an operator confirmation")
    return observed, f"lock owner dead ({basis})"


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
        observed, lock_note = _check_lock(workspace, shipment_id, feature_id, record, options, env, rollback=True)
        notes.append("the original run persisted never_started and never spawned a child: rollback to pre_close")
        notes.append(lock_note)
        return Eligibility(record, journal, exit_record, child_started, observed, True, tuple(notes))

    if journal is None and not options.confirm_engine_stopped:
        raise _Refused(
            "this record has no journal, so nothing proves the engine stopped; "
            "re-run with --confirm-engine-stopped once the operator has verified it"
        )
    observed, lock_note = _check_lock(workspace, shipment_id, feature_id, record, options, env, rollback=False)
    notes.append(lock_note)
    notes.append(_check_child(exit_record, child_started, env))
    _scan_for_ship(shipment_id, env)
    notes.append("no 'backlogit shipment ship' process is running")
    _settle(_snapshot(workspace, record), options.settle_seconds, env)
    notes.append(f"the live state was unchanged across the {options.settle_seconds:g} s settle window")
    return Eligibility(record, journal, exit_record, child_started, observed, False, tuple(notes))


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


def _reconstruct_and_write(
    lock: PairLock, eligibility: Eligibility, disposition: LockDisposition, recovery_run_id: str, env: RecoverEnv
) -> RecoverOutcome:
    raise _Refused("recovery reconstruction is not available in this build")


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
        return outcome(
            EXIT_OK,
            f"dry run: recovery is eligible and would {action}; nothing was written",
            action=action,
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
                lock_disposition=disposition,
                notes=eligibility.notes,
            )
        return _reconstruct_and_write(lock, eligibility, disposition, recovery_run_id, env)
    except _Refused as refused:
        return outcome(refused.exit_code, str(refused), lock_disposition=disposition, notes=eligibility.notes)
    except PersistError as exc:
        code = EXIT_INPUT if exc.exit_code == EXIT_INPUT else EXIT_RECOVERY_REFUSED
        return outcome(code, str(exc), lock_disposition=disposition, notes=eligibility.notes)
    finally:
        with contextlib.suppress(Exception):
            lock.release()
