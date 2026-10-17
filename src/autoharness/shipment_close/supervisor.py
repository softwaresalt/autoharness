"""Journaled child shim and detached supervisor for ``cascade-close`` (211-F, plan units T5 and T7).

``python -m autoharness.shipment_close.supervisor --shim <journal-dir>`` is the
OS-level half of the durable journal: it spawns the fixed ``backlogit shipment
ship`` argv with stdout/stderr redirected **by the operating system** into the
journal's raw files, waits (killing the whole descendant group on timeout or when
a stream passes its cap), proves the descendant group is quiescent and no writer
escaped it (hardening H13), and only then writes ``exit.json`` atomically. A
wrapper that is killed mid-run therefore loses neither the output nor the exit
code.

The shim accepts exactly one argument besides its mode flag, a journal
directory. The exact argv comes from the protected ``launch.json`` and nothing
else (hardening H12): :func:`open_journal` re-derives the directory from the
launch record, and the launch schema re-hashes the argv, so a shim never execs an
argv it cannot authenticate.
"""

from __future__ import annotations

import contextlib
import datetime
import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Final

from autoharness.shipment_close import quiescence
from autoharness.shipment_close.journal import (
    _RUN_ID,
    STREAM_FILES,
    Journal,
    JournalError,
    _read_capped,
    argv_sha256,
    enforce_stream_cap,
    journal_has,
    open_journal,
    open_stream_file,
    parse_utc,
    read_json,
    utc_now,
    write_json,
    write_never_started,
)

__all__ = ["main", "run_child", "supervise"]

_WINDOWS: Final = os.name == "nt"
_CREATE_NO_WINDOW: Final = 0x08000000
_KILL_WAIT_SECONDS: Final = 10
_POLL_SECONDS: Final = 0.25


class _Terminated(BaseException):
    """Raised by the POSIX SIGTERM handler so a wrapper interrupt kills the child group cleanly."""


def _group_for(pid: int, entered: quiescence.DescendantGroup | None = None) -> quiescence.DescendantGroup | None:
    """The descendant group for a just-spawned child: the job entered before the spawn, or the child's own group."""

    return entered if _WINDOWS else quiescence.enter_group(pid)


def _stream_size(journal: Journal, name: str) -> int:
    try:
        return (journal.path / name).stat().st_size
    except OSError:
        return 0


def _write_exit(journal: Journal, **fields: object) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": 1,
        "run_id": journal.run_id,
        "state": "never_started",
        "child_pid": None,
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
        "timed_out": False,
        "quiescence": None,
    }
    record.update(fields)
    write_json(journal, "exit.json", record)
    return record


def _kill_everything(group: quiescence.DescendantGroup | None, process: subprocess.Popen) -> None:
    if group is not None:
        group.kill_members()
    if process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=_KILL_WAIT_SECONDS)
    except (subprocess.TimeoutExpired, OSError):
        pass


def run_child(
    journal: Journal,
    launch: Mapping[str, object],
    *,
    grace_seconds: float | None = None,
    poll_seconds: float = _POLL_SECONDS,
    before_spawn: Callable[[], None] | None = None,
    on_spawned: Callable[[int], None] | None = None,
) -> dict[str, object]:
    """Spawn the launch argv into the journal, wait, prove quiescence, and persist ``exit.json``; returns it.

    ``before_spawn`` runs immediately before the ``Popen`` (the supervisor records ``child_started`` there, so a
    ``never_started`` proof can never coexist with a spawn attempt); ``on_spawned`` receives the child pid.
    """

    argv = list(launch["argv"])  # type: ignore[arg-type]
    timeout = float(launch["timeout_seconds"])  # type: ignore[arg-type]
    cap = int(launch["stream_cap_bytes"])  # type: ignore[arg-type]
    grace = float(launch["quiescence_grace_seconds"]) if grace_seconds is None else grace_seconds  # type: ignore[arg-type]
    entered = quiescence.enter_group(None) if _WINDOWS else None
    if _WINDOWS and entered is None:
        # Without a Job Object the descendant set cannot be proven; refuse before anything runs.
        return write_never_started(journal)
    if before_spawn is not None:
        before_spawn()
    fds = [open_stream_file(journal, name) for name in STREAM_FILES]
    flags = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | _CREATE_NO_WINDOW}
        if _WINDOWS
        else {"start_new_session": True}
    )
    started_at = utc_now()
    try:
        process = subprocess.Popen(
            argv,
            cwd=str(launch["cwd"]),
            stdin=subprocess.DEVNULL,
            stdout=fds[0],
            stderr=fds[1],
            shell=False,
            **flags,
        )
    except (OSError, ValueError):
        for fd in fds:
            os.close(fd)
        empty = {"proven": True, "method": "not_spawned", "survivors_killed": 0, "total_bytes": 0}
        return _write_exit(
            journal,
            state="spawn_failed",
            started_at=started_at,
            finished_at=utc_now(),
            quiescence={"stdout": dict(empty), "stderr": dict(empty)},
        )
    for fd in fds:
        os.close(fd)  # the child holds its own copies; the open-writer probe needs ours closed
    if on_spawned is not None:
        with contextlib.suppress(JournalError, OSError):
            on_spawned(process.pid)
    group = _group_for(process.pid, entered)
    timed_out = False
    capped = False
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                process.wait(timeout=poll_seconds)
                break
            except subprocess.TimeoutExpired:
                pass
            if time.monotonic() >= deadline:
                timed_out = True
            elif any(_stream_size(journal, name) > cap for name in STREAM_FILES):
                capped = True
            if timed_out or capped:
                _kill_everything(group, process)
                break
    except BaseException:
        _kill_everything(group, process)
        raise

    paths = [journal.path / name for name in STREAM_FILES]
    group_verdict = quiescence.settle_group(group, grace=grace, poll=0.1)
    writer_verdict = quiescence.settle_writers(paths, grace=grace, poll=0.1)
    truncated = {name: enforce_stream_cap(journal, name, cap=cap) for name in STREAM_FILES}
    verdicts: dict[str, object] = {}
    for key, name in zip(("stdout", "stderr"), STREAM_FILES):
        proven = group_verdict.proven and writer_verdict.clean is True and not truncated[name] and not capped
        method = f"{group_verdict.method}+writer_probe:{writer_verdict.method}"
        if capped or truncated[name]:
            method += "+stream_cap"
        verdicts[key] = {
            "proven": proven,
            "method": method,
            "survivors_killed": group_verdict.survivors_killed,
            "total_bytes": _stream_size(journal, name),
        }
    return _write_exit(
        journal,
        state="timed_out" if timed_out else "exited",
        child_pid=process.pid,
        started_at=started_at,
        finished_at=utc_now(),
        exit_code=process.returncode,
        timed_out=timed_out,
        quiescence=verdicts,
    )


_AUTH_POLL_SECONDS: Final = 0.1


def _wait_for_authorization(journal: Journal, launch: Mapping[str, object]) -> str:
    """Block until the foreground authorizes, aborts, or the persisted ``authorize_deadline`` passes (H7).

    Returns ``authorized`` only for a valid, unexpired ``authorize.json`` carrying this launch's nonce while no
    ``abort.json`` exists; an abort always wins. Any other result means the child must never be spawned.
    """

    deadline = parse_utc(launch["authorize_deadline"])
    nonce = launch["authorize_nonce"]
    if deadline is None:
        return "invalid_deadline"
    while True:
        now = datetime.datetime.now(datetime.timezone.utc)
        if journal_has(journal, "abort.json"):
            return "aborted"
        if journal_has(journal, "authorize.json"):
            try:
                authorization = read_json(journal, "authorize.json")
            except JournalError:
                return "invalid_authorization"
            if journal_has(journal, "abort.json"):
                return "aborted"
            if authorization["nonce"] != nonce:
                return "invalid_authorization"
            valid_until = parse_utc(authorization["valid_until"])
            if valid_until is None or now > valid_until or now > deadline:
                return "expired"
            return "authorized"
        if now >= deadline:
            return "expired"
        time.sleep(_AUTH_POLL_SECONDS)


def _read_record(path: Path) -> dict:
    from autoharness.shipment_close.persist import _read_no_follow

    record = json.loads(_read_no_follow(path).decode("utf-8"))
    if not isinstance(record, dict):
        raise ValueError("the evidence record is not a JSON object")
    return record


def _claim_lock_owner(lock, observed) -> bool:
    """Authenticate the lock handoff, tolerating a Windows venv launcher between the foreground and this process.

    The foreground records the pid it spawned. When that is a launcher (``python.exe`` in a venv) our own pid
    differs, so the handoff is accepted only if the lock is already marked as handed to a supervisor, names our
    live parent, and carries that parent's exact start time; the lock is then re-handed to our own pid and start.
    """

    from autoharness.shipment_close.liveness import process_start_time
    from autoharness.shipment_close.persist import PersistError, handoff_lock

    me = os.getpid()
    if observed.pid == me:
        return True
    parent = os.getppid()
    if not (_WINDOWS and observed.supervisor and observed.pid == parent and observed.pid_start):
        return False
    if process_start_time(parent) != observed.pid_start:
        return False
    try:
        handoff_lock(lock, pid=me, pid_start=process_start_time(me))
    except PersistError:
        return False
    return True


def _supervise_locked(lock, journal: Journal, launch: Mapping[str, object]) -> tuple[int, bool]:
    """Run the barrier, authentication, revalidation, spawn, and finalization; returns ``(status, release_lock)``."""

    from autoharness.shipment_close import command
    from autoharness.shipment_close.persist import PersistError, observe_lock
    from autoharness.shipment_close.runner import ResolvedBinary, hash_binary, result_from_journal

    def refuse(outcome: str, exit_code: int, detail: str) -> tuple[int, bool]:
        sys.stderr.write(f"not spawning: {detail}\n")
        try:
            command.finish_never_started(
                lock, journal, outcome=outcome, exit_code=exit_code, finalizer="supervisor", detail=detail
            )
        except (PersistError, JournalError, OSError) as exc:
            sys.stderr.write(f"the never-started rollback failed: {exc}; leaving the lock for recovery\n")
            return 2, False
        return 2, True

    write_json(
        journal,
        "ready.json",
        {"schema_version": 1, "run_id": journal.run_id, "supervisor_pid": os.getpid(), "written_at": utc_now()},
    )
    verdict = _wait_for_authorization(journal, launch)
    if verdict != "authorized":
        return refuse("never_authorized", 2, f"authorization not granted ({verdict})")

    shipment_id, feature_id = str(launch["shipment_id"]), str(launch["feature_id"])
    try:
        meta = read_json(journal, "meta.json")
        if meta["finalizer"] != "supervisor":
            return refuse("never_started", 2, "the finalizer token was not handed to the supervisor")
        observed = observe_lock(lock.workspace, shipment_id, feature_id)
        if observed is None or observed.run_id != journal.run_id or not _claim_lock_owner(lock, observed):
            return refuse("never_started", 2, "the pair lock was not handed to this supervisor")
        invoking = _read_record(lock.evidence_path)
    except (JournalError, PersistError, OSError, ValueError) as exc:
        return refuse("never_started", 2, f"the durable state cannot be authenticated: {exc}")
    invocation = invoking.get("invocation")
    recorded = invocation.get("argv_sha256") if isinstance(invocation, dict) else None
    tool = invoking.get("tool")
    tool_hash = tool.get("binary_sha256") if isinstance(tool, dict) else None
    if (
        invoking.get("phase") != "invoking"
        or invoking.get("run_id") != journal.run_id
        or not (launch["argv_sha256"] == recorded == meta["argv_sha256"] == argv_sha256(list(launch["argv"])))  # type: ignore[arg-type]
        or tool_hash != launch["binary_sha256"]
    ):
        return refuse("never_started", 2, "the launch argv does not match the invoking record (argv authentication)")

    resolved = ResolvedBinary(
        binary_path=str(launch["binary_path"]),
        binary_sha256=str(launch["binary_sha256"]),
        argv_prefix=tuple(launch["argv_prefix"]),  # type: ignore[arg-type]
    )

    def binary_unchanged() -> bool:
        try:
            return hash_binary(resolved.binary_path) == resolved.binary_sha256
        except PersistError:
            return False

    if not binary_unchanged():
        return refuse("revalidation_drift", 4, "the binary's SHA-256 changed before the revalidation")
    try:
        snapshot = command.revalidate_invoking(
            lock.workspace,
            invoking,
            shipment_id,
            feature_id,
            str(launch["merge_commit_sha"]),
            journal.run_id,
            resolved,
        )
    except command._Halt as halt:
        return refuse("revalidation_drift", 4, str(halt))
    if not binary_unchanged():
        return refuse("revalidation_drift", 4, "the binary's SHA-256 changed immediately before the spawn")

    def started(state: str, pid: int | None) -> None:
        write_json(
            journal,
            "child_started.json",
            {"schema_version": 1, "run_id": journal.run_id, "state": state, "pid": pid, "written_at": utc_now()},
        )

    exit_record = run_child(
        journal,
        launch,
        before_spawn=lambda: started("spawning", None),
        on_spawned=lambda pid: started("spawned", pid),
    )
    if exit_record["state"] == "never_started":
        return refuse("never_started", 2, "the shim could not establish a descendant group; nothing ran")

    state = command._State(evidence_path=lock.evidence_path)
    state.note(snapshot)
    spawn_error: str | None = None
    try:
        result = result_from_journal(journal, launch)
    except PersistError as exc:
        spawn_error = str(exc)
        result = command._spawn_failed(list(launch["argv"]), str(invocation["started_at"]))  # type: ignore[index, arg-type]
    try:
        command._finalize(
            lock, state, snapshot, invoking, invoking, journal, result, spawn_error, finalizer="supervisor"
        )
    except Exception as exc:  # noqa: BLE001 - the child ran; leave the evidence for recovery
        sys.stderr.write(f"finalization failed: {type(exc).__name__}: {exc}\n")
        command._write_outcome(journal, 8, "post_write_failed", "supervisor", detail=f"{type(exc).__name__}")
    return 0, True


def supervise(journal: Journal, launch: Mapping[str, object]) -> int:
    """The detached supervisor (``--supervise``): barrier, authentication, revalidation, spawn, finalize, release."""

    from autoharness.shipment_close.persist import PersistError, attach_pair_lock

    try:
        lock = attach_pair_lock(
            str(launch["workspace"]), str(launch["shipment_id"]), str(launch["feature_id"]), journal.run_id
        )
    except PersistError as exc:
        sys.stderr.write(f"refusing to supervise: {exc}\n")
        return 7
    release = True
    try:
        status, release = _supervise_locked(lock, journal, launch)
    finally:
        if release:
            lock.release()
    return status


def _best_effort_never_started(path: str) -> None:
    """A launch that failed authentication still leaves the never-started proof when its run id is readable."""

    try:
        raw, _ = _read_capped(Path(path) / "launch.json", 64 * 1024)
        run_id = json.loads(raw.decode("utf-8")).get("run_id")
        if type(run_id) is str and _RUN_ID.fullmatch(run_id):
            write_never_started(Journal(path=Path(path), run_id=run_id))
    except (JournalError, OSError, ValueError, AttributeError):
        pass


def _install_sigterm() -> None:
    if _WINDOWS:
        return

    def handler(signum: int, frame: object) -> None:
        raise _Terminated

    signal.signal(signal.SIGTERM, handler)


_MODES: Final = {"--shim": "attached", "--supervise": "detached"}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] not in _MODES:
        sys.stderr.write("usage: python -m autoharness.shipment_close.supervisor (--shim | --supervise) <journal-dir>\n")
        return 2
    path = args[1]
    try:
        journal = open_journal(path)
        launch = read_json(journal, "launch.json")
        if launch["mode"] != _MODES[args[0]]:
            # A detached launch must go through the barrier; an attached one has none to honour.
            raise JournalError("invalid", f"launch mode {launch['mode']!r} does not match {args[0]}")
    except JournalError as exc:
        _best_effort_never_started(path)
        sys.stderr.write(f"refusing to start: {exc}\n")
        return 2
    _install_sigterm()
    try:
        if args[0] == "--supervise":
            return supervise(journal, launch)
        run_child(journal, launch)
    except _Terminated:
        return 143
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
