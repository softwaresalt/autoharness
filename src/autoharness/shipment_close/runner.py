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
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

from autoharness.shipment_close import EXIT_INPUT
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
    "BoundedRunResult",
    "ResolvedBinary",
    "hash_binary",
    "resolve_backlogit_binary",
    "run_bounded",
    "validate_timeout",
]

REGISTRY_PATH: Final = Path(".autoharness") / "backlog-registry.yaml"
DEFAULT_TIMEOUT_SECONDS: Final = 120
MIN_TIMEOUT_SECONDS: Final = 30
MAX_TIMEOUT_SECONDS: Final = 900

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
    """Return a ``--timeout`` value in 30-900 s; anything else is exit 2."""

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
    unresolved binary; a resolved basename (minus ``.exe`` on Windows) that is
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
        candidate = Path(os.path.abspath(candidate))
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
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_group(process)
        try:
            process.wait(timeout=_KILL_WAIT_SECONDS)
        except subprocess.TimeoutExpired:
            pass
    for reader in readers:
        reader.join(_READER_JOIN_SECONDS)
    for pipe in (process.stdout, process.stderr):
        try:
            pipe.close()
        except OSError:
            pass
    for reader in readers:
        reader.join(_READER_JOIN_SECONDS)
    finished_at = _utc_now()
    return BoundedRunResult(
        argv=argv,
        exit_code=process.returncode,
        timed_out=timed_out,
        started_at=started_at,
        finished_at=finished_at,
        stdout=stdout_capture.finish(),
        stderr=stderr_capture.finish(),
    )
