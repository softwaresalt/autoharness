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
launch record, and the launch schema re-hashes the argv, so the shim only execs
an argv whose ``argv_sha256`` integrity checks out against ``launch.json``. That
hash check is the whole authentication on the attached (``--shim``) path; the
detached (``--supervise``) path additionally cross-checks the launch record
against the ``invoking`` evidence record, the meta, and the pair lock before it
spawns anything.
"""

from __future__ import annotations

import contextlib
import datetime
import functools
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
    MAX_JSON_BYTES,
    STREAM_FILES,
    Journal,
    JournalError,
    _read_capped,
    argv_sha256,
    enforce_stream_cap,
    journal_created_epoch,
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


class _SpawnRefused(Exception):
    """Raised by ``before_spawn`` when the spawn must not happen; nothing was spawned."""


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


_EXIT_WRITE_ATTEMPTS: Final = 4


def _write_exit_retrying(journal: Journal, **fields: object) -> dict[str, object]:
    """``exit.json`` is the only proof of what the child did: retry a transient write failure (a sharing violation)."""

    for attempt in range(_EXIT_WRITE_ATTEMPTS):
        try:
            return _write_exit(journal, **fields)
        except (JournalError, OSError):
            if attempt == _EXIT_WRITE_ATTEMPTS - 1:
                raise
            time.sleep(0.1 * (attempt + 1))
    raise AssertionError("unreachable")


def _close_all(fds: list[int]) -> None:
    for fd in fds:
        with contextlib.suppress(OSError):
            os.close(fd)
    fds.clear()  # a descriptor number is never closed twice: it may have been reused


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
    fds: list[int] = []
    try:
        for name in STREAM_FILES:
            fds.append(open_stream_file(journal, name))
    except (JournalError, OSError):
        _close_all(fds)
        return write_never_started(journal)
    flags = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | _CREATE_NO_WINDOW}
        if _WINDOWS
        else {"start_new_session": True}
    )
    if before_spawn is not None:
        try:
            before_spawn()
        except _SpawnRefused:
            _close_all(fds)
            return write_never_started(journal)
        except BaseException:
            _close_all(fds)
            raise
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
        _close_all(fds)
        empty = {"proven": True, "method": "not_spawned", "survivors_killed": 0, "total_bytes": 0}
        return _write_exit_retrying(
            journal,
            state="spawn_failed",
            started_at=started_at,
            finished_at=utc_now(),
            quiescence={"stdout": dict(empty), "stderr": dict(empty)},
        )
    group = entered if _WINDOWS else None
    timed_out = False
    capped = False
    deadline = time.monotonic() + timeout
    try:
        # Arm the group kill before anything interruptible: a SIGTERM from here on must reach the whole group.
        group = _group_for(process.pid, entered)
        _close_all(fds)  # the child holds its own copies; the open-writer probe needs ours closed
        if on_spawned is not None:
            with contextlib.suppress(JournalError, OSError):
                on_spawned(process.pid)
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
        if group is None and not _WINDOWS:
            group = quiescence.PosixGroup(process.pid)
        _kill_everything(group, process)
        _close_all(fds)
        raise

    try:
        verdicts = _prove_quiescence(journal, group, cap=cap, grace=grace, capped=capped)
    except Exception as exc:  # noqa: BLE001 - the child ran: an exit sentinel with an unproven verdict beats none
        diagnostic = f"{type(exc).__name__}: {exc}"[:200]
        verdicts = {
            key: {
                "proven": False,
                "method": f"supervisor_error ({diagnostic})",
                "survivors_killed": 0,
                "total_bytes": _stream_size(journal, name),
            }
            for key, name in zip(("stdout", "stderr"), STREAM_FILES)
        }
    return _write_exit_retrying(
        journal,
        state="timed_out" if timed_out else "exited",
        child_pid=process.pid,
        started_at=started_at,
        finished_at=utc_now(),
        exit_code=process.returncode,
        timed_out=timed_out,
        quiescence=verdicts,
    )


def _prove_quiescence(
    journal: Journal, group: quiescence.DescendantGroup | None, *, cap: int, grace: float, capped: bool
) -> dict[str, object]:
    paths = [journal.path / name for name in STREAM_FILES]
    group_verdict = quiescence.settle_group(group, grace=grace, poll=0.1)
    writer_verdict = quiescence.settle_writers(
        paths,
        grace=grace,
        poll=0.1,
        probe=functools.partial(quiescence.probe_writers, started_before_epoch=journal_created_epoch(journal)),
    )
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
    return verdicts


_AUTH_POLL_SECONDS: Final = 0.1
_AUTH_READ_ATTEMPTS: Final = 5


def _read_authorization(journal: Journal) -> dict[str, object]:
    """Read ``authorize.json``, retrying what a concurrent atomic replace transiently refuses (a sharing violation)."""

    for attempt in range(_AUTH_READ_ATTEMPTS):
        try:
            return read_json(journal, "authorize.json")
        except PermissionError:
            pass
        except JournalError as exc:
            if exc.reason != "untrusted":
                raise
        if attempt < _AUTH_READ_ATTEMPTS - 1:
            time.sleep(0.05)
    return read_json(journal, "authorize.json")


def _authorization_verdict(journal: Journal, launch: Mapping[str, object], deadline: datetime.datetime) -> str | None:
    """``None`` while no ``authorize.json`` exists, else ``authorized``/``aborted``/``expired``/``invalid_authorization``.

    The clock is sampled after the file is read, so a slow read can never make an expired grant look valid.
    """

    if not journal_has(journal, "authorize.json"):
        return None
    try:
        authorization = _read_authorization(journal)
    except (JournalError, OSError):
        return "invalid_authorization"
    now = datetime.datetime.now(datetime.timezone.utc)
    if journal_has(journal, "abort.json"):
        return "aborted"
    if authorization["nonce"] != launch["authorize_nonce"]:
        return "invalid_authorization"
    valid_until = parse_utc(authorization["valid_until"])
    if valid_until is None or now > valid_until or now > deadline:
        return "expired"
    return "authorized"


def _wait_for_authorization(journal: Journal, launch: Mapping[str, object]) -> str:
    """Block until the foreground authorizes, aborts, or the persisted ``authorize_deadline`` passes (H7).

    Returns ``authorized`` only for a valid, unexpired ``authorize.json`` carrying this launch's nonce while no
    ``abort.json`` exists; an abort always wins. Any other result means the child must never be spawned.
    """

    deadline = parse_utc(launch["authorize_deadline"])
    if deadline is None:
        return "invalid_deadline"
    while True:
        if journal_has(journal, "abort.json"):
            return "aborted"
        verdict = _authorization_verdict(journal, launch, deadline)
        if verdict is not None:
            return verdict
        if datetime.datetime.now(datetime.timezone.utc) >= deadline:
            return "expired"
        time.sleep(_AUTH_POLL_SECONDS)


def _authorization_current(journal: Journal, launch: Mapping[str, object]) -> bool:
    """The last check before the spawn: no abort, and the grant and the window are still open right now."""

    deadline = parse_utc(launch["authorize_deadline"])
    if deadline is None or journal_has(journal, "abort.json"):
        return False
    return _authorization_verdict(journal, launch, deadline) == "authorized"


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


def _write_child_started(journal: Journal, state: str, pid: int | None) -> None:
    write_json(
        journal,
        "child_started.json",
        {"schema_version": 1, "run_id": journal.run_id, "state": state, "pid": pid, "written_at": utc_now()},
    )


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
        _write_child_started(journal, state, pid)

    def before_spawn() -> None:
        if not _authorization_current(journal, launch):
            raise _SpawnRefused("the authorization lapsed or was aborted before the spawn")
        started("spawning", None)

    try:
        exit_record = run_child(
            journal,
            launch,
            before_spawn=before_spawn,
            on_spawned=lambda pid: started("spawned", pid),
        )
    except Exception as exc:  # noqa: BLE001 - past the spawn point a child may be running: never release the lock
        sys.stderr.write(f"the supervised run failed unexpectedly: {type(exc).__name__}: {exc}\n")
        if journal_has(journal, "child_started.json"):
            return 2, False
        return refuse("never_started", 2, f"the shim failed before spawning: {type(exc).__name__}")
    if exit_record["state"] == "never_started":
        return refuse("never_started", 2, "the child was not spawned (no descendant group, stream, or authorization); nothing ran")

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
    except BaseException:
        # Past the spawn point the lock stays for recovery. Before it, the never-started proof must be
        # complete before the lock is released; when it cannot be completed the lock stays held.
        release = False
        if not journal_has(journal, "child_started.json"):
            release = _finish_never_started_best_effort(lock, journal)
        raise
    finally:
        if release:
            lock.release()
    return status


def _finish_never_started_best_effort(lock, journal: Journal) -> bool:
    """Complete the never-started proof after an unexpected pre-spawn failure; False when it cannot be completed."""

    from autoharness.shipment_close import command

    try:
        if journal_has(journal, "outcome.json"):
            return True
        command.finish_never_started(
            lock,
            journal,
            outcome="never_started",
            exit_code=2,
            finalizer="supervisor",
            detail="the supervisor failed before spawning the child",
        )
    except Exception as exc:  # noqa: BLE001 - a failed rollback keeps the lock so recovery sees a dead owner
        with contextlib.suppress(OSError, ValueError):
            sys.stderr.write(f"the never-started rollback failed: {type(exc).__name__}: {exc}; leaving the lock for recovery\n")
        return False
    return True


def _best_effort_never_started(path: str) -> None:
    """A launch that failed authentication still leaves the never-started proof when its run id is readable.

    It never writes next to evidence of a spawn attempt or an existing exit sentinel.
    """

    try:
        raw, _ = _read_capped(Path(path) / "launch.json", MAX_JSON_BYTES)
        run_id = json.loads(raw.decode("utf-8")).get("run_id")
        if type(run_id) is str and _RUN_ID.fullmatch(run_id):
            journal = Journal(path=Path(path), run_id=run_id)
            if not (journal_has(journal, "exit.json") or journal_has(journal, "child_started.json")):
                write_never_started(journal)
    except (JournalError, OSError, ValueError, AttributeError, RecursionError):
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

    def mark_spawning() -> None:
        try:
            _write_child_started(journal, "spawning", None)
        except (JournalError, OSError) as exc:
            raise _SpawnRefused(f"the spawning marker cannot be journaled: {exc}") from exc

    try:
        if args[0] == "--supervise":
            return supervise(journal, launch)
        run_child(
            journal,
            launch,
            before_spawn=mark_spawning,
            on_spawned=lambda pid: _write_child_started(journal, "spawned", pid),
        )
    except _Terminated:
        return 143
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
