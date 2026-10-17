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

import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from autoharness.shipment_close import quiescence
from autoharness.shipment_close.journal import (
    _RUN_ID,
    STREAM_FILES,
    Journal,
    JournalError,
    _read_capped,
    enforce_stream_cap,
    open_journal,
    open_stream_file,
    read_json,
    utc_now,
    write_json,
)

__all__ = ["main", "run_child", "write_never_started"]

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


def write_never_started(journal: Journal) -> dict[str, object]:
    """Persist the ``never_started`` sentinel: the proof that no child was ever spawned for this run."""

    return _write_exit(journal)


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
) -> dict[str, object]:
    """Spawn the launch argv into the journal, wait, prove quiescence, and persist ``exit.json``; returns it."""

    argv = list(launch["argv"])  # type: ignore[arg-type]
    timeout = float(launch["timeout_seconds"])  # type: ignore[arg-type]
    cap = int(launch["stream_cap_bytes"])  # type: ignore[arg-type]
    grace = float(launch["quiescence_grace_seconds"]) if grace_seconds is None else grace_seconds  # type: ignore[arg-type]
    entered = quiescence.enter_group(None) if _WINDOWS else None
    if _WINDOWS and entered is None:
        # Without a Job Object the descendant set cannot be proven; refuse before anything runs.
        return write_never_started(journal)
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


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] != "--shim":
        sys.stderr.write("usage: python -m autoharness.shipment_close.supervisor --shim <journal-dir>\n")
        return 2
    path = args[1]
    try:
        journal = open_journal(path)
        launch = read_json(journal, "launch.json")
    except JournalError as exc:
        _best_effort_never_started(path)
        sys.stderr.write(f"refusing to start: {exc}\n")
        return 2
    _install_sigterm()
    try:
        run_child(journal, launch)
    except _Terminated:
        return 143
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
