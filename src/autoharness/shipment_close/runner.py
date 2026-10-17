"""Bounded backlogit subprocess runner for ``cascade-close`` (192-F, plan unit A3a).

* :func:`resolve_backlogit_binary` resolves the registry's bare-name
  ``cli.binary`` through ``shutil.which`` and refuses anything that is not a
  basename-matching, out-of-workspace, non-link executable (on Windows: a
  real ``.exe``, never a ``.cmd``/``.bat`` shim; SL-F02). It records the
  absolute path and the file's SHA-256 and never spawns anything itself
  (re-plan cycle-1 R7: ``tool.version_excerpt`` comes from the single A2a
  probe spawn).
* :func:`run_bounded` spawns a fixed argv with ``shell=False`` and
  ``stdin=DEVNULL`` in a new process group, drains both streams through A1b
  :class:`~autoharness.shipment_close.persist.StreamCapture`, and on timeout
  kills the whole group (``os.killpg`` on POSIX; the absolute
  ``%SystemRoot%\\System32\\taskkill.exe /T /F /PID <pid>`` on Windows).
  If a grandchild inherited a pipe and outlives the child, the group is
  killed, a pipe whose reader is still alive is never closed (a buffered
  ``close()`` would block on the reader's lock), and that stream is marked
  ``drain_incomplete``; any ``BaseException`` while waiting kills the group
  before re-raising (198-S local review).

The trust model equals the current skill's (the first ``backlogit`` on
PATH); pinning a trusted absolute path in the registry is a P-021 follow-up.
"""

from __future__ import annotations

import datetime
import hashlib
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

from autoharness.shipment_close import EXIT_INPUT
from autoharness.shipment_close.journal import (
    STREAM_FILES,
    TRUNCATION_MARKER,
    Journal,
    JournalError,
    read_json,
    read_stream,
    utc_now,
)
from autoharness.shipment_close.persist import (
    CapturedStream,
    PersistError,
    StreamCapture,
    _is_link,
    _read_no_follow,
)

__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "MAX_TIMEOUT_SECONDS",
    "MIN_TIMEOUT_SECONDS",
    "REGISTRY_PATH",
    "SUPERVISION_MARGIN_SECONDS",
    "BoundedRunResult",
    "DetachedSpawn",
    "ResolvedBinary",
    "hash_binary",
    "resolve_backlogit_binary",
    "result_from_journal",
    "run_bounded",
    "run_journaled",
    "spawn_detached",
    "validate_timeout",
]

REGISTRY_PATH: Final = Path(".autoharness") / "backlog-registry.yaml"
DEFAULT_TIMEOUT_SECONDS: Final = 1800
MIN_TIMEOUT_SECONDS: Final = 30
MAX_TIMEOUT_SECONDS: Final = 3600
# The wrapper-supervision margin (PR #485 review). ``--timeout`` bounds only
# the ``backlogit shipment ship`` child, and this runner alone owns that
# expiry. The mutating command as a whole is supervised for ``--timeout`` +
# this margin, which covers what runs outside the child wait: two engine
# probes (``PROBE_TIMEOUT_SECONDS`` = 30 each, plus their kill path), the
# child's own kill/reader-join cleanup, and the untimed workspace reads,
# revalidation, postcondition checks, evidence writes, and lock release. Each
# bounded run's worst-case kill path is 3 * _KILL_WAIT_SECONDS + 4 *
# _READER_JOIN_SECONDS = 70 s, so the timed overhead is 2 * (30 + 70) + 70 =
# 270 s; the remaining 330 s is headroom for the untimed filesystem work.
# Documentation only: nothing in the command enforces it.
SUPERVISION_MARGIN_SECONDS: Final = 600

_BARE_NAME: Final = re.compile(r"[A-Za-z0-9_-]+")
_READ_CHUNK: Final = 65536
_KILL_WAIT_SECONDS: Final = 10
_READER_JOIN_SECONDS: Final = 10
_WINDOWS: Final = os.name == "nt"


@dataclass(frozen=True)
class ResolvedBinary:
    """A trusted backlogit binary.

    ``argv_prefix`` is ``(binary_path,)`` in production. Tests inject
    ``(sys.executable, fake_script)`` through this seam; the trust checks of
    :func:`resolve_backlogit_binary` apply to ``argv_prefix[0]``.
    """

    binary_path: str
    binary_sha256: str
    argv_prefix: tuple[str, ...]


@dataclass(frozen=True)
class BoundedRunResult:
    argv: tuple[str, ...]
    exit_code: int | None
    timed_out: bool
    started_at: str
    finished_at: str
    stdout: CapturedStream
    stderr: CapturedStream


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def validate_timeout(value: object) -> int:
    """Return a ``--timeout`` value in [MIN_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS]; anything else is exit 2."""

    if type(value) is not int or not MIN_TIMEOUT_SECONDS <= value <= MAX_TIMEOUT_SECONDS:
        raise PersistError(
            EXIT_INPUT,
            f"--timeout must be an integer from {MIN_TIMEOUT_SECONDS} to {MAX_TIMEOUT_SECONDS} seconds (got {value!r})",
        )
    return value


def hash_binary(path: Path | str) -> str:
    """SHA-256 of a binary file (A3 re-hashes immediately before spawning, SL-F03)."""

    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PersistError(EXIT_INPUT, f"cannot hash binary {path}: {exc}") from exc
    return digest.hexdigest()


def _read_cli_binary(root: Path) -> str:
    registry = root / REGISTRY_PATH
    try:
        payload = yaml.safe_load(_read_no_follow(registry).decode("utf-8"))
    except PersistError:
        raise
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise PersistError(EXIT_INPUT, f"cannot read {REGISTRY_PATH.as_posix()}: {exc}") from exc
    cli = payload.get("cli") if isinstance(payload, dict) else None
    binary = cli.get("binary") if isinstance(cli, dict) else None
    if type(binary) is not str:
        raise PersistError(EXIT_INPUT, f"{REGISTRY_PATH.as_posix()} has no string cli.binary")
    return binary


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def resolve_backlogit_binary(
    workspace: Path | str, *, which: Callable[[str], str | None] = shutil.which
) -> ResolvedBinary:
    """Resolve the registry's bare-name ``cli.binary`` to a trusted absolute path.

    Refuses (exit 2): a non-bare name (checked before any lookup); an
    unresolved binary; a resolution that is not already absolute (a
    cwd-relative ``which()`` result is never ``abspath``-ed); a resolved
    basename (minus ``.exe`` on Windows) that is
    not ``cli.binary``; a resolution inside the workspace root; a symlink or
    reparse point; and on Windows any suffix other than ``.exe``.
    """

    try:
        root = Path(workspace).resolve(strict=True)
    except OSError as exc:
        raise PersistError(EXIT_INPUT, f"workspace {workspace} cannot be resolved: {exc}") from exc
    name = _read_cli_binary(root)
    if _BARE_NAME.fullmatch(name) is None:
        raise PersistError(EXIT_INPUT, f"cli.binary must be a bare name matching ^[A-Za-z0-9_-]+$ (got {name!r})")
    found = which(name)
    if not found:
        raise PersistError(EXIT_INPUT, f"cli.binary {name!r} is not resolvable on PATH")
    candidate = Path(found)
    if not candidate.is_absolute():
        # Never abspath a cwd-relative lookup: it would trust a binary planted
        # in an attacker-controlled cwd (198-S local review).
        raise PersistError(
            EXIT_INPUT,
            f"refusing a non-absolute PATH resolution for cli.binary {name!r} ({found!r}); "
            "remove '.'/empty entries from PATH",
        )
    stem = candidate.name
    if _WINDOWS:
        if candidate.suffix.lower() != ".exe":
            raise PersistError(EXIT_INPUT, f"refusing a non-.exe binary on Windows (script shims are unsafe): {candidate}")
        stem = stem[: -len(".exe")]
        matches = stem.casefold() == name.casefold()
    else:
        matches = stem == name
    if not matches:
        raise PersistError(EXIT_INPUT, f"resolved binary {candidate} does not match cli.binary {name!r}")
    if _is_link(candidate):
        raise PersistError(EXIT_INPUT, f"refusing a symlink or reparse-point binary: {candidate}")
    if _is_within(candidate, root) or _is_within(candidate.resolve(), root):
        raise PersistError(EXIT_INPUT, f"refusing a binary inside the workspace root: {candidate}")
    if not candidate.is_file():
        raise PersistError(EXIT_INPUT, f"resolved binary is not a regular file: {candidate}")
    path_text = str(candidate)
    return ResolvedBinary(binary_path=path_text, binary_sha256=hash_binary(candidate), argv_prefix=(path_text,))


def _drain(stream, capture: StreamCapture) -> None:
    try:
        for chunk in iter(lambda: stream.read(_READ_CHUNK), b""):
            capture.feed(chunk)
    except (OSError, ValueError):
        pass  # the pipe was closed under us after a bounded join


def _kill_group(process: subprocess.Popen) -> None:
    if _WINDOWS:
        system_root = os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT")
        taskkill = Path(system_root) / "System32" / "taskkill.exe" if system_root else None
        if taskkill is not None and taskkill.is_file():
            try:
                subprocess.run(
                    [str(taskkill), "/T", "/F", "/PID", str(process.pid)],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=False,
                    timeout=_KILL_WAIT_SECONDS,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError):
                pass
        if process.poll() is None:
            process.kill()
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        if process.poll() is None:
            process.kill()


def run_bounded(argv: Sequence[str], *, cwd: Path | str, timeout: float) -> BoundedRunResult:
    """Run a fixed argv with bounded time and bounded retained output.

    Raises :class:`PersistError` (exit 2) on a malformed argv or a spawn
    failure; never raises for a non-zero exit or a timeout.
    """

    if isinstance(argv, (str, bytes)) or not argv or not all(type(item) is str for item in argv):
        raise PersistError(EXIT_INPUT, "argv must be a non-empty sequence of strings")
    if not (isinstance(timeout, (int, float)) and not isinstance(timeout, bool) and timeout > 0):
        raise PersistError(EXIT_INPUT, f"timeout must be a positive number (got {timeout!r})")
    argv = tuple(argv)
    group = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if _WINDOWS else {"start_new_session": True}
    )
    stdout_capture = StreamCapture(parse_buffer=True)
    stderr_capture = StreamCapture(parse_buffer=False)
    started_at = _utc_now()
    try:
        process = subprocess.Popen(
            list(argv),
            cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            **group,
        )
    except (OSError, ValueError) as exc:
        raise PersistError(EXIT_INPUT, f"cannot spawn {argv[0]!r}: {exc}") from exc
    readers = [
        threading.Thread(target=_drain, args=(process.stdout, stdout_capture), daemon=True),
        threading.Thread(target=_drain, args=(process.stderr, stderr_capture), daemon=True),
    ]
    for reader in readers:
        reader.start()
    timed_out = False
    incomplete = [False, False]
    try:
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_group(process)
            _wait_after_kill(process)
        for reader in readers:
            reader.join(_READER_JOIN_SECONDS)
        if any(reader.is_alive() for reader in readers):
            # A grandchild inherited a pipe and outlived the child (198-S local
            # review): kill the group, and mark every stream we had to cut short.
            incomplete = [reader.is_alive() for reader in readers]
            _kill_group(process)
            for reader in readers:
                reader.join(_READER_JOIN_SECONDS)
        for index, (reader, pipe) in enumerate(zip(readers, (process.stdout, process.stderr))):
            if reader.is_alive():
                # Never close a buffered pipe under a live reader: close() would
                # block on the lock its read() holds, defeating the bound. The
                # daemon reader is abandoned and its capture is frozen below.
                incomplete[index] = True
                continue
            try:
                pipe.close()
            except OSError:
                pass
    except BaseException:
        # KeyboardInterrupt/SystemExit must never leave the child running.
        _kill_group(process)
        _wait_after_kill(process)
        raise
    finished_at = _utc_now()
    return BoundedRunResult(
        argv=argv,
        exit_code=process.returncode,
        timed_out=timed_out,
        started_at=started_at,
        finished_at=finished_at,
        stdout=stdout_capture.finish(drain_incomplete=incomplete[0]),
        stderr=stderr_capture.finish(drain_incomplete=incomplete[1]),
    )


def _wait_after_kill(process: subprocess.Popen) -> None:
    try:
        process.wait(timeout=_KILL_WAIT_SECONDS)
    except (subprocess.TimeoutExpired, OSError):
        pass


# ---------------------------------------------------------------------------
# Journaled runner (211-F, plan unit T5)
# ---------------------------------------------------------------------------

# Slack on top of the child's own timeout for the shim's kill path, the quiescence grace
# (twice: group, then open writers), and the exit-sentinel write.
SHIM_WAIT_MARGIN_SECONDS: Final = 120
_DETACHED_PROCESS: Final = 0x00000008
_CREATE_BREAKAWAY_FROM_JOB: Final = 0x01000000
_ERROR_ACCESS_DENIED: Final = 5
_SHIM_MODULE: Final = "autoharness.shipment_close.supervisor"


@dataclass(frozen=True)
class DetachedSpawn:
    """A detached Python process. ``breakaway`` is False only when a Windows job refused breakaway."""

    process: subprocess.Popen
    breakaway: bool


def _spawn_environment(env: dict[str, str] | None) -> dict[str, str]:
    merged = dict(os.environ if env is None else env)
    package_root = str(Path(__file__).resolve().parents[2])
    existing = merged.get("PYTHONPATH")
    merged["PYTHONPATH"] = package_root + (os.pathsep + existing if existing else "")
    return merged


def spawn_detached(argv: Sequence[str], *, cwd: Path | str, env: dict[str, str] | None = None) -> DetachedSpawn:
    """Spawn ``argv`` so it outlives the caller: no console, its own group/session, and (Windows) job breakaway.

    Breakaway is attempted first; a job that forbids it (access denied) is retried without it and reported
    through ``breakaway=False``, because then the process can still be killed with its job.
    """

    options = {
        "cwd": str(cwd),
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "shell": False,
        "close_fds": True,
        "env": _spawn_environment(env),
    }
    if not _WINDOWS:
        return DetachedSpawn(subprocess.Popen(list(argv), start_new_session=True, **options), True)
    base = _DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        return DetachedSpawn(subprocess.Popen(list(argv), creationflags=base | _CREATE_BREAKAWAY_FROM_JOB, **options), True)
    except OSError as exc:
        if getattr(exc, "winerror", None) != _ERROR_ACCESS_DENIED:
            raise
    return DetachedSpawn(subprocess.Popen(list(argv), creationflags=base, **options), False)


def _terminate_shim(process: subprocess.Popen) -> None:
    """Interrupt path: ask the shim to kill its child group (POSIX SIGTERM), then kill the tree."""

    if not _WINDOWS and process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=_KILL_WAIT_SECONDS)
        except (ProcessLookupError, PermissionError, subprocess.TimeoutExpired, OSError):
            pass
    _kill_group(process)
    _wait_after_kill(process)


def _indeterminate(launch: Mapping[str, object]) -> BoundedRunResult:
    return BoundedRunResult(
        argv=tuple(launch["argv"]),  # type: ignore[arg-type]
        exit_code=None,
        timed_out=False,
        started_at=str(launch["created_at"]),
        finished_at=utc_now(),
        stdout=StreamCapture(parse_buffer=True).finish(drain_incomplete=True),
        stderr=StreamCapture().finish(drain_incomplete=True),
    )


def _capture_from_journal(journal: Journal, name: str, *, parse: bool, cap: int, proven: bool) -> CapturedStream:
    data, truncated = read_stream(journal, name, cap=cap + len(TRUNCATION_MARKER))
    capture = StreamCapture(parse_buffer=parse)
    for offset in range(0, len(data), _READ_CHUNK):
        capture.feed(data[offset : offset + _READ_CHUNK])
    return capture.finish(drain_incomplete=truncated or not proven)


def result_from_journal(journal: Journal, launch: Mapping[str, object]) -> BoundedRunResult:
    """Rebuild the :class:`BoundedRunResult` from ``exit.json`` and the raw streams (never from wrapper memory).

    A missing or unreadable sentinel or stream is an indeterminate, incomplete result (the child may have run);
    a ``never_started`` or ``spawn_failed`` sentinel raises :class:`PersistError` (nothing ran).
    """

    try:
        exit_record = read_json(journal, "exit.json")
    except JournalError:
        return _indeterminate(launch)
    argv = tuple(launch["argv"])  # type: ignore[arg-type]
    if exit_record["state"] == "never_started":
        raise PersistError(EXIT_INPUT, f"the journal shim refused to start {argv[0]!r}; nothing ran")
    if exit_record["state"] == "spawn_failed":
        raise PersistError(EXIT_INPUT, f"cannot spawn {argv[0]!r}")
    verdicts = exit_record["quiescence"]
    cap = int(launch["stream_cap_bytes"])  # type: ignore[arg-type]
    try:
        stdout = _capture_from_journal(
            journal, "stdout.raw", parse=True, cap=cap, proven=verdicts["stdout"]["proven"]  # type: ignore[index]
        )
        stderr = _capture_from_journal(
            journal, "stderr.raw", parse=False, cap=cap, proven=verdicts["stderr"]["proven"]  # type: ignore[index]
        )
    except JournalError:
        return _indeterminate(launch)
    return BoundedRunResult(
        argv=argv,
        exit_code=exit_record["exit_code"],  # type: ignore[arg-type]
        timed_out=bool(exit_record["timed_out"]),
        started_at=str(exit_record["started_at"]),
        finished_at=str(exit_record["finished_at"]),
        stdout=stdout,
        stderr=stderr,
    )


def run_journaled(journal: Journal, *, wait_margin_seconds: float = SHIM_WAIT_MARGIN_SECONDS) -> BoundedRunResult:
    """Run the journal's authenticated launch argv through the detached shim and return its journaled result.

    The wrapper only waits: the child, its exit code, and its output live in the journal, so a killed wrapper
    loses none of them. An interrupt kills the shim and its child before re-raising.
    """

    launch = read_json(journal, "launch.json")
    try:
        spawned = spawn_detached(
            [sys.executable, "-m", _SHIM_MODULE, "--shim", str(journal.path)], cwd=journal.path
        )
    except (OSError, ValueError) as exc:
        raise PersistError(EXIT_INPUT, f"cannot spawn the journal shim: {exc}") from exc
    process = spawned.process
    try:
        try:
            process.wait(timeout=float(launch["timeout_seconds"]) + wait_margin_seconds)  # type: ignore[arg-type]
        except subprocess.TimeoutExpired:
            _terminate_shim(process)
    except BaseException:
        _terminate_shim(process)
        raise
    return result_from_journal(journal, launch)
