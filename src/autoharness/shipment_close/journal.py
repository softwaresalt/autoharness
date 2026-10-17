"""Durable output journal for the ``cascade-close`` command (211-F, plan unit T2; hardening H5).

The journal is the OS-level record a killed wrapper leaves behind: the raw child
streams, the exit sentinel, and the final outcome. It lives under the
Git-ignored ``.autoharness/gates/cascade-close/{S}-{F}.journal/`` and holds
**unredacted** engine output, so:

* the directory is created through :func:`ensure_trusted_directory` (every
  component a real directory, none a symlink/junction/reparse point, all inside
  the workspace);
* files are created ``0600`` on POSIX. On Windows the mode bits do not restrict
  access; the directory inherits the ACL of the workspace and is Git-ignored,
  and the operator is told so in the gates reference (best effort);
* nothing is ever read through a link (:func:`_read_capped`), every JSON read is
  size-capped and schema-checked, and a missing, torn, oversized, or malformed
  file is a :class:`JournalError`, never an empty or default value;
* raw streams are size-capped with an explicit, in-band truncation marker, and
  evidence only ever receives redacted excerpts (the existing ``redact``).

This module only manages its own named files; it never deletes a directory
tree and never touches anything outside the journal directory.
"""

from __future__ import annotations

import contextlib
import datetime
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from autoharness.gates.cascade_evidence import CascadeEvidenceError, build_evidence_path, parse_rfc3339_instant
from autoharness.shipment_close import EXIT_INPUT
from autoharness.shipment_close.persist import (
    LOCK_DIR,
    PersistError,
    _check_trusted_chain,
    _fsync_directory,
    _is_link,
    _replace_with_retry,
    ensure_trusted_directory,
)

__all__ = [
    "EXIT_STATES",
    "JOURNAL_SUFFIX",
    "MAX_JSON_BYTES",
    "OUTCOMES",
    "STREAM_CAP_BYTES",
    "STREAM_FILES",
    "TRUNCATION_MARKER",
    "Journal",
    "JournalError",
    "argv_sha256",
    "build_launch",
    "cleanup_raw_files",
    "clear_journal",
    "create_journal",
    "discard_journal",
    "enforce_stream_cap",
    "journal_has",
    "journal_path",
    "open_journal",
    "open_stream_file",
    "parse_utc",
    "read_json",
    "read_stream",
    "utc_now",
    "write_json",
    "write_never_started",
]

JOURNAL_SUFFIX: Final = ".journal"
MAX_JSON_BYTES: Final = 64 * 1024
STREAM_CAP_BYTES: Final = 8 * 1024 * 1024
TRUNCATION_MARKER: Final = b"\n[autoharness: journal stream truncated at the capture cap]\n"
STREAM_FILES: Final = ("stdout.raw", "stderr.raw")
# Files removed on a clean exit-0 run; meta/exit/outcome are retained so --poll still answers.
_RAW_FILES: Final = (*STREAM_FILES, "launch.json")
_SCHEMA_VERSION: Final = 1
_RUN_ID: Final = re.compile(r"[0-9a-f]{32}")
_SHA256: Final = re.compile(r"[0-9a-f]{64}")

OUTCOMES: Final = frozenset(
    {
        "completed",
        "postcondition_failed",
        "invocation_failed",
        "post_write_failed",
        "never_started",
        "never_authorized",
        "revalidation_drift",
    }
)
EXIT_STATES: Final = frozenset({"exited", "timed_out", "spawn_failed", "never_started"})

_META_KEYS: Final = frozenset(
    {
        "schema_version",
        "run_id",
        "shipment_id",
        "feature_id",
        "argv_redacted",
        "argv_sha256",
        "timeout_seconds",
        "caller_wait_seconds",
        "host",
        "wrapper_pid",
        "created_at",
        "finalizer",
    }
)
_EXIT_KEYS: Final = frozenset(
    {
        "schema_version",
        "run_id",
        "state",
        "child_pid",
        "started_at",
        "finished_at",
        "exit_code",
        "timed_out",
        "quiescence",
    }
)
_OUTCOME_KEYS: Final = frozenset({"schema_version", "run_id", "exit_code", "outcome", "finalizer", "written_at"})
_OUTCOME_OPTIONAL: Final = frozenset({"detail"})
_LAUNCH_KEYS: Final = frozenset(
    {
        "schema_version",
        "run_id",
        "shipment_id",
        "feature_id",
        "workspace",
        "merge_commit_sha",
        "mode",
        "argv",
        "argv_sha256",
        "binary_path",
        "binary_sha256",
        "argv_prefix",
        "cwd",
        "timeout_seconds",
        "stream_cap_bytes",
        "quiescence_grace_seconds",
        "authorize_deadline",
        "authorize_nonce",
        "created_at",
    }
)
_LAUNCH_MODES: Final = frozenset({"attached", "detached"})
_STARTED_STATES: Final = frozenset({"spawning", "spawned"})
_COMMIT_SHA: Final = re.compile(r"[0-9a-f]{40}")
_QUIESCENCE_KEYS: Final = frozenset({"proven", "method", "survivors_killed", "total_bytes"})


class JournalError(PersistError):
    """A journal refusal. ``reason`` is one of missing, torn, invalid, oversize, untrusted, exists."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(EXIT_INPUT, message)
        self.reason = reason


@dataclass(frozen=True)
class Journal:
    path: Path
    run_id: str


def _is_str(value: object) -> bool:
    return type(value) is str and bool(value)


def _is_int(value: object, *, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def _check_meta(obj: Mapping[str, object]) -> str | None:
    if set(obj) != _META_KEYS:
        return "keys differ from the schema"
    argv = obj["argv_redacted"]
    if type(argv) is not list or not argv or not all(type(a) is str for a in argv):
        return "argv_redacted must be a non-empty list of strings"
    if not (_is_str(obj["shipment_id"]) and _is_str(obj["feature_id"]) and _is_str(obj["host"])):
        return "shipment_id, feature_id, and host must be non-empty strings"
    sha = obj["argv_sha256"]
    if not (type(sha) is str and _SHA256.fullmatch(sha)):
        return "argv_sha256 must be 64 lowercase hex characters"
    if not _is_int(obj["timeout_seconds"], minimum=1):
        return "timeout_seconds must be a positive integer"
    if obj["caller_wait_seconds"] is not None and not _is_int(obj["caller_wait_seconds"]):
        return "caller_wait_seconds must be null or a non-negative integer"
    if not _is_int(obj["wrapper_pid"], minimum=1):
        return "wrapper_pid must be a positive integer"
    if not _is_str(obj["created_at"]):
        return "created_at must be a non-empty string"
    if obj["finalizer"] is not None and not _is_str(obj["finalizer"]):
        return "finalizer must be null or a non-empty string"
    return None


def _check_quiescence(value: object) -> str | None:
    if type(value) is not dict or set(value) != {"stdout", "stderr"}:
        return "quiescence must name exactly stdout and stderr"
    for stream, verdict in value.items():
        if type(verdict) is not dict or set(verdict) != _QUIESCENCE_KEYS:
            return f"quiescence.{stream} keys differ from the schema"
        if type(verdict["proven"]) is not bool or not _is_str(verdict["method"]):
            return f"quiescence.{stream} proven/method are malformed"
        if not (_is_int(verdict["survivors_killed"]) and _is_int(verdict["total_bytes"])):
            return f"quiescence.{stream} counts must be non-negative integers"
    return None


def _check_exit(obj: Mapping[str, object]) -> str | None:
    if set(obj) != _EXIT_KEYS:
        return "keys differ from the schema"
    if obj["state"] not in EXIT_STATES:
        return "state is not a known exit state"
    if obj["child_pid"] is not None and not _is_int(obj["child_pid"], minimum=1):
        return "child_pid must be null or a positive integer"
    for key in ("started_at", "finished_at"):
        if obj[key] is not None and not _is_str(obj[key]):
            return f"{key} must be null or a non-empty string"
    if obj["exit_code"] is not None and type(obj["exit_code"]) is not int:
        return "exit_code must be null or an integer"
    if type(obj["timed_out"]) is not bool:
        return "timed_out must be a boolean"
    if obj["state"] == "never_started":
        if obj["child_pid"] is not None or obj["exit_code"] is not None or obj["quiescence"] is not None:
            return "a never_started sentinel must carry no child, exit code, or quiescence"
        return None
    if obj["state"] == "exited" and obj["exit_code"] is None:
        return "an exited sentinel must carry an exit_code"
    return _check_quiescence(obj["quiescence"])


def _check_outcome(obj: Mapping[str, object]) -> str | None:
    keys = set(obj)
    if not _OUTCOME_KEYS <= keys <= _OUTCOME_KEYS | _OUTCOME_OPTIONAL:
        return "keys differ from the schema"
    if not (_is_int(obj["exit_code"]) and obj["exit_code"] <= 255):
        return "exit_code must be an integer in 0..255"
    if obj["outcome"] not in OUTCOMES:
        return "outcome is not a known outcome"
    if not (_is_str(obj["finalizer"]) and _is_str(obj["written_at"])):
        return "finalizer and written_at must be non-empty strings"
    if "detail" in obj and not _is_str(obj["detail"]):
        return "detail must be a non-empty string"
    return None


def _is_number(value: object) -> bool:
    return type(value) in (int, float) and value >= 0


def argv_sha256(argv: Sequence[str]) -> str:
    """SHA-256 over the exact argv (the canonical JSON array); H12 hashes this, never the redacted audit copy."""

    return hashlib.sha256(json.dumps(list(argv), separators=(",", ":")).encode("utf-8")).hexdigest()


def _check_launch(obj: Mapping[str, object]) -> str | None:
    if set(obj) != _LAUNCH_KEYS:
        return "keys differ from the schema"
    for key in ("argv", "argv_prefix"):
        value = obj[key]
        if type(value) is not list or not value or not all(type(item) is str for item in value):
            return f"{key} must be a non-empty list of strings"
    if obj["argv_sha256"] != argv_sha256(obj["argv"]):  # type: ignore[arg-type]
        return "argv_sha256 does not match the exact argv"
    if obj["argv"][: len(obj["argv_prefix"])] != obj["argv_prefix"]:  # type: ignore[index]
        return "argv does not start with the recorded argv_prefix"
    if obj["binary_path"] not in obj["argv_prefix"]:  # type: ignore[operator]
        return "binary_path must be part of the recorded argv_prefix"
    for key in ("shipment_id", "feature_id", "workspace", "cwd", "binary_path", "created_at"):
        if not _is_str(obj[key]):
            return f"{key} must be a non-empty string"
    if not (type(obj["binary_sha256"]) is str and _SHA256.fullmatch(obj["binary_sha256"])):
        return "binary_sha256 must be 64 lowercase hex characters"
    if not (type(obj["merge_commit_sha"]) is str and _COMMIT_SHA.fullmatch(obj["merge_commit_sha"])):
        return "merge_commit_sha must be 40 lowercase hex characters"
    if obj["mode"] not in _LAUNCH_MODES:
        return "mode must be attached or detached"
    if not _is_int(obj["timeout_seconds"], minimum=1):
        return "timeout_seconds must be a positive integer"
    if not _is_int(obj["stream_cap_bytes"], minimum=1):
        return "stream_cap_bytes must be a positive integer"
    if not _is_number(obj["quiescence_grace_seconds"]):
        return "quiescence_grace_seconds must be a non-negative number"
    for key in ("authorize_deadline", "authorize_nonce"):
        if obj[key] is not None and not _is_str(obj[key]):
            return f"{key} must be null or a non-empty string"
    if obj["mode"] == "detached" and (obj["authorize_deadline"] is None or obj["authorize_nonce"] is None):
        return "a detached launch requires authorize_deadline and authorize_nonce"
    if obj["authorize_deadline"] is not None and parse_rfc3339_instant(obj["authorize_deadline"]) is None:
        return "authorize_deadline must be an RFC 3339 timestamp"
    return None


def _check_barrier(extra: Mapping[str, Callable[[object], bool]]) -> Callable[[Mapping[str, object]], str | None]:
    base = {"schema_version", "run_id", "written_at"}

    def check(obj: Mapping[str, object]) -> str | None:
        if set(obj) != base | set(extra):
            return "keys differ from the schema"
        if not _is_str(obj["written_at"]):
            return "written_at must be a non-empty string"
        for key, valid in extra.items():
            if not valid(obj[key]):
                return f"{key} is malformed"
        return None

    return check


_SCHEMAS: Final[dict[str, Callable[[Mapping[str, object]], str | None]]] = {
    "meta.json": _check_meta,
    "exit.json": _check_exit,
    "outcome.json": _check_outcome,
    "launch.json": _check_launch,
    "ready.json": _check_barrier({"supervisor_pid": lambda v: _is_int(v, minimum=1)}),
    "authorize.json": _check_barrier(
        {"nonce": _is_str, "valid_until": lambda v: parse_rfc3339_instant(v) is not None}
    ),
    "abort.json": _check_barrier({"reason": _is_str}),
    "child_started.json": _check_barrier(
        {"state": lambda v: v in _STARTED_STATES, "pid": lambda v: v is None or _is_int(v, minimum=1)}
    ),
}


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_utc(value: object) -> datetime.datetime | None:
    """The UTC instant of a timestamp this package wrote, or ``None`` when it is not RFC 3339."""

    return parse_rfc3339_instant(value)


def build_launch(
    *,
    run_id: str,
    workspace: str,
    shipment_id: str,
    feature_id: str,
    merge_commit_sha: str,
    mode: str,
    argv: Sequence[str],
    binary_path: str,
    binary_sha256: str,
    argv_prefix: Sequence[str],
    cwd: str,
    timeout_seconds: int,
    stream_cap_bytes: int | None = None,
    quiescence_grace_seconds: float = 5.0,
    authorize_deadline: str | None = None,
    authorize_nonce: str | None = None,
) -> dict[str, object]:
    """The ``launch.json`` payload: the EXACT argv plus its hash and the trusted binary identity (H12)."""

    return {
        "schema_version": _SCHEMA_VERSION,
        "run_id": run_id,
        "shipment_id": shipment_id,
        "feature_id": feature_id,
        "workspace": workspace,
        "merge_commit_sha": merge_commit_sha,
        "mode": mode,
        "argv": list(argv),
        "argv_sha256": argv_sha256(argv),
        "binary_path": binary_path,
        "binary_sha256": binary_sha256,
        "argv_prefix": list(argv_prefix),
        "cwd": cwd,
        "timeout_seconds": timeout_seconds,
        "stream_cap_bytes": stream_cap_bytes if stream_cap_bytes is not None else STREAM_CAP_BYTES,
        "quiescence_grace_seconds": quiescence_grace_seconds,
        "authorize_deadline": authorize_deadline,
        "authorize_nonce": authorize_nonce,
        "created_at": utc_now(),
    }


def journal_path(workspace: Path | str, shipment_id: str, feature_id: str) -> Path:
    """The journal directory path for a pair (validates the ids; creates nothing)."""

    try:
        build_evidence_path(workspace, shipment_id, feature_id)
        root = Path(workspace).resolve(strict=True)
    except (CascadeEvidenceError, OSError) as exc:
        raise JournalError("invalid", str(exc)) from exc
    return root / LOCK_DIR / f"{shipment_id}-{feature_id}{JOURNAL_SUFFIX}"


def create_journal(workspace: Path | str, shipment_id: str, feature_id: str, run_id: str) -> Journal:
    """Create (or reopen) the pair's journal directory through the trust walk."""

    if not _RUN_ID.fullmatch(run_id):
        raise JournalError("invalid", f"run_id must be 32 lowercase hex characters (got {run_id!r})")
    expected = journal_path(workspace, shipment_id, feature_id)
    root = Path(workspace).resolve(strict=True)
    created = ensure_trusted_directory(root, expected.relative_to(root))
    return Journal(path=created, run_id=run_id)


def _require_trusted(journal: Journal) -> None:
    if _is_link(journal.path) or not journal.path.is_dir():
        raise JournalError("untrusted", f"journal directory is missing or is a link: {journal.path}")


def _file(journal: Journal, name: str) -> Path:
    _require_trusted(journal)
    return journal.path / name


def _open_flags() -> int:
    return getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _read_capped(path: Path, cap: int) -> tuple[bytes, bool]:
    """Read at most ``cap`` bytes through no link; the flag is True when the file was longer."""

    if not os.path.lexists(path):
        raise JournalError("missing", f"journal file not found: {path.name}")
    if _is_link(path):
        raise JournalError("untrusted", f"refusing to read through a symlink or reparse point: {path.name}")
    try:
        fd = os.open(path, os.O_RDONLY | _open_flags())
    except OSError as exc:
        raise JournalError("untrusted", f"cannot open {path.name}: {exc.__class__.__name__}") from exc
    try:
        data = bytearray()
        while len(data) <= cap:
            chunk = os.read(fd, min(65536, cap + 1 - len(data)))
            if not chunk:
                break
            data += chunk
    finally:
        os.close(fd)
    return bytes(data[:cap]), len(data) > cap


def write_json(journal: Journal, name: str, obj: Mapping[str, object]) -> None:
    """Atomically write a schema-checked journal JSON file bound to this journal's run."""

    check = _SCHEMAS.get(name)
    if check is None:
        raise JournalError("invalid", f"{name} is not a known journal JSON file")
    if obj.get("schema_version") != _SCHEMA_VERSION or obj.get("run_id") != journal.run_id:
        raise JournalError("invalid", f"{name}: schema_version or run_id does not match the journal")
    problem = check(obj)
    if problem is not None:
        raise JournalError("invalid", f"{name}: {problem}")
    data = (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(data) > MAX_JSON_BYTES:
        raise JournalError("oversize", f"{name} exceeds {MAX_JSON_BYTES} bytes")
    target = _file(journal, name)
    if os.path.lexists(target) and _is_link(target):
        raise JournalError("untrusted", f"refusing a link target: {name}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=journal.path)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if os.name != "nt":
            os.chmod(temp_name, 0o600)
        _replace_with_retry(temp_name, target)
        _fsync_directory(journal.path)
    except OSError as exc:
        raise JournalError("invalid", f"cannot write {name}: {exc}") from exc
    finally:
        if os.path.lexists(temp_name):
            with contextlib.suppress(OSError):
                os.unlink(temp_name)


def read_json(journal: Journal, name: str, *, expected_run_id: str | None = None) -> dict[str, object]:
    """Read and schema-check a journal JSON file; every defect is a :class:`JournalError`."""

    check = _SCHEMAS.get(name)
    if check is None:
        raise JournalError("invalid", f"{name} is not a known journal JSON file")
    raw, truncated = _read_capped(_file(journal, name), MAX_JSON_BYTES)
    if truncated:
        raise JournalError("oversize", f"{name} exceeds {MAX_JSON_BYTES} bytes")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise JournalError("torn", f"{name} is not valid JSON (torn or corrupt)") from exc
    if type(obj) is not dict:
        raise JournalError("invalid", f"{name} is not a JSON object")
    if obj.get("schema_version") != _SCHEMA_VERSION:
        raise JournalError("invalid", f"{name}: unsupported schema_version")
    run_id = obj.get("run_id")
    if not (type(run_id) is str and _RUN_ID.fullmatch(run_id)):
        raise JournalError("invalid", f"{name}: run_id is not 32 lowercase hex characters")
    if run_id != (expected_run_id if expected_run_id is not None else journal.run_id):
        raise JournalError("invalid", f"{name}: belongs to another run")
    problem = check(obj)
    if problem is not None:
        raise JournalError("invalid", f"{name}: {problem}")
    return obj


def open_stream_file(journal: Journal, name: str) -> int:
    """Create a raw stream file exclusively (0600, append) and return its descriptor for the child redirect."""

    if name not in STREAM_FILES:
        raise JournalError("invalid", f"{name} is not a journal stream file")
    path = _file(journal, name)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND | _open_flags()
    try:
        return os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise JournalError("exists", f"journal stream already exists: {name}") from exc
    except OSError as exc:
        raise JournalError("invalid", f"cannot create {name}: {exc.__class__.__name__}") from exc


def read_stream(journal: Journal, name: str, *, cap: int = STREAM_CAP_BYTES) -> tuple[bytes, bool]:
    """Read a raw stream through no link; returns ``(data, truncated)`` with data at most ``cap`` bytes."""

    if name not in STREAM_FILES:
        raise JournalError("invalid", f"{name} is not a journal stream file")
    return _read_capped(_file(journal, name), cap)


def enforce_stream_cap(journal: Journal, name: str, *, cap: int = STREAM_CAP_BYTES) -> bool:
    """Truncate an over-cap stream to ``cap`` bytes and append :data:`TRUNCATION_MARKER`; True if it was truncated."""

    if name not in STREAM_FILES:
        raise JournalError("invalid", f"{name} is not a journal stream file")
    path = _file(journal, name)
    if not os.path.lexists(path):
        raise JournalError("missing", f"journal file not found: {name}")
    if _is_link(path):
        raise JournalError("untrusted", f"refusing a link target: {name}")
    try:
        if path.stat().st_size <= cap:
            return False
        with open(path, "r+b") as handle:
            handle.truncate(cap)
            handle.seek(0, os.SEEK_END)
            handle.write(TRUNCATION_MARKER)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise JournalError("invalid", f"cannot cap {name}: {exc.__class__.__name__}") from exc
    return True


def _remove_files(journal: Journal, names: tuple[str, ...]) -> None:
    for name in names:
        path = journal.path / name
        if not os.path.lexists(path):
            continue
        if _is_link(path):
            raise JournalError("untrusted", f"refusing to remove a link: {name}")
        try:
            os.unlink(path)
        except OSError as exc:
            raise JournalError("invalid", f"cannot remove {name}: {exc.__class__.__name__}") from exc


def cleanup_raw_files(journal: Journal) -> None:
    """Remove only the raw streams and ``launch.json``; ``meta``/``exit``/``outcome`` stay for ``--poll``."""

    _require_trusted(journal)
    _remove_files(journal, _RAW_FILES)


def clear_journal(journal: Journal) -> None:
    """Remove every file this module owns but keep the directory (a new run reusing the pair's journal path)."""

    _require_trusted(journal)
    _remove_files(journal, (*STREAM_FILES, *_SCHEMAS))


def discard_journal(journal: Journal) -> None:
    """Remove every file this module owns, then the directory if it is then empty (never a tree delete)."""

    _require_trusted(journal)
    _remove_files(journal, (*STREAM_FILES, *_SCHEMAS))
    with contextlib.suppress(OSError):
        journal.path.rmdir()


def write_never_started(journal: Journal) -> dict[str, object]:
    """Persist the ``never_started`` sentinel: the proof that no child was ever spawned for this run."""

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
    write_json(journal, "exit.json", record)
    return record


def journal_has(journal: Journal, name: str) -> bool:
    """True when the named journal file exists (a link counts as existing and is refused when read)."""

    return os.path.lexists(_file(journal, name))


def open_journal(path: str | Path) -> Journal:
    """Open an existing journal from its directory path alone (the supervisor's only argument; H12).

    The directory must be absolute, a real directory, and exactly the location
    its own ``launch.json`` names for the pair (so a copied or relocated
    ``launch.json`` is refused); the trust walk then re-checks the chain.
    """

    candidate = Path(path)
    if not candidate.is_absolute() or not candidate.name.endswith(JOURNAL_SUFFIX):
        raise JournalError("invalid", "the journal path must be an absolute path to a .journal directory")
    if _is_link(candidate) or not candidate.is_dir():
        raise JournalError("untrusted", f"journal directory is missing or is a link: {candidate}")
    raw, truncated = _read_capped(candidate / "launch.json", MAX_JSON_BYTES)
    try:
        run_id = json.loads(raw.decode("utf-8")).get("run_id") if not truncated else None
    except (ValueError, UnicodeDecodeError, AttributeError) as exc:
        raise JournalError("torn", "launch.json is not valid JSON (torn or corrupt)") from exc
    if not (type(run_id) is str and _RUN_ID.fullmatch(run_id)):
        raise JournalError("invalid", "launch.json carries no valid run_id")
    journal = Journal(path=candidate, run_id=run_id)
    launch = read_json(journal, "launch.json")
    expected = journal_path(str(launch["workspace"]), str(launch["shipment_id"]), str(launch["feature_id"]))
    if os.path.normcase(os.path.realpath(candidate)) != os.path.normcase(os.path.realpath(expected)):
        raise JournalError("untrusted", "the journal directory is not the one its launch record names")
    try:
        _check_trusted_chain(Path(str(launch["workspace"])).resolve(strict=True), LOCK_DIR)
    except (PersistError, OSError) as exc:
        raise JournalError("untrusted", f"the journal location failed the trust walk: {exc}") from exc
    return journal
