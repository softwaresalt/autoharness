"""Evidence persistence for the ``cascade-close`` command (192-F, plan unit A1b).

This module is the only writer of close-evidence records. It owns:

* :class:`StreamCapture`, bounded streaming capture of one child stream: every
  byte is counted and hashed, a tail window (final 64 KiB / 500 lines plus a
  4 KiB leading margin) is kept for the excerpt, and stdout alone keeps a
  never-persisted parse buffer of at most 1 MiB / 10,000 lines (AS-F03).
  Redaction runs over the retained window **before** the excerpt is sliced
  (H-B4);
* :func:`redact_record_free_text`, which runs the A1 :func:`redact` over every
  persisted free-text field (SL-F04) and never over the four
  validator-re-assessed fields (re-plan cycle-1 R6);
* :func:`acquire_pair_lock`, the per-pair ``O_CREAT | O_EXCL`` lock under the
  Git-ignored ``.autoharness/gates/cascade-close/`` (SL-F01), after a
  directory-trust walk of every component (SL-F06). A held lock is never
  broken automatically (exit 7); removing a stale lock is an operator action;
* :func:`check_existing_record`, the first action under the lock;
* :func:`write_evidence_atomic`, the owner-bound atomic write (AS-F01) with the
  narrowly authorized ``pre_close`` takeover compare-and-swap (Copilot PR #481
  T6).

Every path this module touches is inside the workspace it is given
(constitution IV). It never deletes anything but its own temp file and its own
lock.
"""

from __future__ import annotations

import copy
import datetime
import hashlib
import json
import os
import re
import tempfile
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from autoharness.gates.cascade_evidence import (
    EVIDENCE_DIR,
    CascadeEvidenceError,
    build_evidence_path,
    redact,
    serialize_evidence_record,
)
from autoharness.gates.closure_contract import ClosureContractError, assert_path_within_workspace
from autoharness.shipment_close import EXIT_INPUT, EXIT_LOCKED

__all__ = [
    "LEADING_MARGIN_BYTES",
    "LOCK_DIR",
    "MODE_CLASSIFY_ONLY",
    "MODE_MUTATING",
    "MODE_REPLACE_PRE_CLOSE",
    "PARSE_CAP_BYTES",
    "PARSE_CAP_LINES",
    "STDOUT_OVERFLOW_ERROR",
    "TAIL_BYTES",
    "TAIL_LINES",
    "CapturedStream",
    "PairLock",
    "PersistError",
    "StreamCapture",
    "acquire_pair_lock",
    "check_existing_record",
    "ensure_trusted_directory",
    "redact_record_free_text",
    "serialize_evidence_record",
    "write_evidence_atomic",
]

TAIL_BYTES: Final = 64 * 1024
TAIL_LINES: Final = 500
LEADING_MARGIN_BYTES: Final = 4 * 1024
PARSE_CAP_BYTES: Final = 1024 * 1024
PARSE_CAP_LINES: Final = 10_000
STDOUT_OVERFLOW_ERROR: Final = "stdout exceeded capture cap"

LOCK_DIR: Final = Path(".autoharness") / "gates" / "cascade-close"

MODE_CLASSIFY_ONLY: Final = "classify_only"
MODE_REPLACE_PRE_CLOSE: Final = "replace_pre_close"
MODE_MUTATING: Final = "mutating"
_MODES: Final = frozenset({MODE_CLASSIFY_ONLY, MODE_REPLACE_PRE_CLOSE, MODE_MUTATING})

_RUN_ID_PATTERN: Final = re.compile(r"[0-9a-f]{32}")
_PHASES: Final = frozenset({"pre_close", "invoking", "post_close"})
_OWNER_TRANSITIONS: Final = frozenset({("pre_close", "invoking"), ("invoking", "post_close")})
_REPLACE_RETRIES: Final = 3
_REPLACE_BACKOFF_SECONDS: Final = 0.05


class PersistError(CascadeEvidenceError):
    """A persistence refusal carrying the command exit code it maps to."""

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code


# ---------------------------------------------------------------------------
# Streaming capture
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapturedStream:
    """The bounded result of one :class:`StreamCapture`.

    ``parse_bytes`` and ``parse_error`` are in-memory only and never persisted
    by :meth:`to_record`. ``capture_truncated`` is ``True`` whenever the
    excerpt is not the whole (redacted) stream.
    """

    total_bytes: int
    total_lines: int
    sha256: str
    capture_truncated: bool
    excerpt: str
    redaction_applied: bool
    parse_bytes: bytes | None
    parse_error: str | None

    def to_record(self) -> dict[str, object]:
        return {
            "total_bytes": self.total_bytes,
            "total_lines": self.total_lines,
            "sha256": self.sha256,
            "capture_truncated": self.capture_truncated,
            "excerpt": self.excerpt,
            "redaction_applied": self.redaction_applied,
        }


class StreamCapture:
    """Count, hash, and boundedly retain one child stream (AS-F03, H-B4)."""

    def __init__(self, *, parse_buffer: bool = False) -> None:
        self._hash = hashlib.sha256()
        self._total = 0
        self._newlines = 0
        self._ends_with_newline = True
        self._window = bytearray()
        self._parse_enabled = parse_buffer
        self._parse: bytearray | None = bytearray() if parse_buffer else None
        self._overflow = False

    @property
    def retained_bytes(self) -> int:
        return len(self._window) + (len(self._parse) if self._parse is not None else 0)

    def _lines(self) -> int:
        return self._newlines + (0 if self._ends_with_newline else 1)

    def feed(self, chunk: bytes) -> None:
        if not chunk:
            return
        self._hash.update(chunk)
        self._total += len(chunk)
        self._newlines += chunk.count(b"\n")
        self._ends_with_newline = chunk.endswith(b"\n")
        self._window += chunk
        excess = len(self._window) - (TAIL_BYTES + LEADING_MARGIN_BYTES)
        if excess > 0:
            del self._window[:excess]
        if self._parse is not None:
            if self._total > PARSE_CAP_BYTES or self._lines() > PARSE_CAP_LINES:
                self._parse = None
                self._overflow = True
            else:
                self._parse += chunk

    def finish(self) -> CapturedStream:
        raw = bytes(self._window)
        text = raw.decode("utf-8", errors="replace")
        redacted, applied = redact(text)  # before the slice (H-B4)
        encoded = redacted.encode("utf-8")
        excerpt = encoded[-TAIL_BYTES:].decode("utf-8", errors="ignore") if len(encoded) > TAIL_BYTES else redacted
        lines = excerpt.splitlines(keepends=True)
        if len(lines) > TAIL_LINES:
            excerpt = "".join(lines[-TAIL_LINES:])
        truncated = self._total != len(raw) or excerpt != redacted or self._overflow
        parse_bytes = bytes(self._parse) if self._parse is not None else None
        return CapturedStream(
            total_bytes=self._total,
            total_lines=self._lines(),
            sha256=self._hash.hexdigest(),
            capture_truncated=truncated,
            excerpt=excerpt,
            redaction_applied=applied,
            parse_bytes=parse_bytes,
            parse_error=STDOUT_OVERFLOW_ERROR if self._parse_enabled and self._overflow else None,
        )


# ---------------------------------------------------------------------------
# Free-text redaction (SL-F04; re-plan cycle-1 R6)
# ---------------------------------------------------------------------------


def _redact_str(value: object) -> tuple[object, bool]:
    if type(value) is not str:
        return value, False
    return redact(value)


def redact_record_free_text(record: Mapping[str, object]) -> tuple[dict, bool]:
    """Return a redacted deep copy of ``record`` and whether anything changed.

    Redacts ``tool.version_excerpt``, ``invocation.argv_redacted``, both
    ``invocation`` excerpts, ``post_close.parse_error``, and
    ``post_close.failures[]``. ``engine_semantics.reason``,
    ``close_path_selection.reason``, ``probed_version``, and ``probed_commit``
    are never redacted: they are sanitized inputs the validator re-assesses.
    """

    result = copy.deepcopy(dict(record))
    applied = False

    tool = result.get("tool")
    if isinstance(tool, dict):
        tool["version_excerpt"], changed = _redact_str(tool.get("version_excerpt"))
        applied |= changed
    invocation = result.get("invocation")
    if isinstance(invocation, dict):
        argv = invocation.get("argv_redacted")
        if type(argv) is list:
            redacted_argv = []
            for item in argv:
                value, changed = _redact_str(item)
                redacted_argv.append(value)
                applied |= changed
            invocation["argv_redacted"] = redacted_argv
        for stream in ("stdout", "stderr"):
            capture = invocation.get(stream)
            if isinstance(capture, dict) and "excerpt" in capture:
                capture["excerpt"], changed = _redact_str(capture["excerpt"])
                if changed:
                    capture["redaction_applied"] = True
                applied |= changed
    post_close = result.get("post_close")
    if isinstance(post_close, dict):
        if "parse_error" in post_close:
            post_close["parse_error"], changed = _redact_str(post_close["parse_error"])
            applied |= changed
        failures = post_close.get("failures")
        if type(failures) is list:
            redacted_failures = []
            for item in failures:
                value, changed = _redact_str(item)
                redacted_failures.append(value)
                applied |= changed
            post_close["failures"] = redacted_failures
    return result, applied


# ---------------------------------------------------------------------------
# Directory trust (SL-F06)
# ---------------------------------------------------------------------------


def _is_link(path: Path) -> bool:
    # Reused, lazily imported (private-name rule): symlink or Windows junction.
    from autoharness.gates.shipment_closure import _is_symlink_or_reparse_point

    return _is_symlink_or_reparse_point(path)


def _trusted_component(component: Path) -> None:
    if _is_link(component):
        raise PersistError(EXIT_INPUT, f"untrusted directory component (symlink or reparse point): {component}")
    if not component.is_dir():
        raise PersistError(EXIT_INPUT, f"directory component is not a real directory: {component}")


def _check_trusted_chain(root: Path, relative: Path) -> None:
    """Check every existing component of ``root / relative`` without creating anything."""

    current = root
    for part in relative.parts:
        current = current / part
        if not os.path.lexists(current):
            return
        _trusted_component(current)


def ensure_trusted_directory(workspace: Path | str, relative: Path | str) -> Path:
    """Create ``workspace / relative`` one component at a time, trust-checking each.

    Every component must be contained in the workspace and be a real directory
    (no symlink, junction, or reparse point). Missing components are created
    with ``mkdir`` and re-checked after each creation. Raises
    :class:`PersistError` (exit 2).
    """

    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise PersistError(EXIT_INPUT, f"directory {relative} is not a workspace-relative path")
    try:
        root = Path(workspace).resolve(strict=True)
    except OSError as exc:
        raise PersistError(EXIT_INPUT, f"workspace {workspace} cannot be resolved: {exc}") from exc
    _check_trusted_chain(root, relative)
    current = root
    for part in relative.parts:
        current = current / part
        if not os.path.lexists(current):
            try:
                os.mkdir(current)
            except FileExistsError:
                pass
            except OSError as exc:
                raise PersistError(EXIT_INPUT, f"cannot create {current}: {exc}") from exc
        _trusted_component(current)
        try:
            assert_path_within_workspace(current, workspace_root=root)
        except ClosureContractError as exc:
            raise PersistError(EXIT_INPUT, str(exc)) from exc
    return current


# ---------------------------------------------------------------------------
# Per-pair lock (SL-F01)
# ---------------------------------------------------------------------------


def _is_run_id(value: object) -> bool:
    return type(value) is str and _RUN_ID_PATTERN.fullmatch(value) is not None


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_no_follow(path: Path) -> bytes:
    if _is_link(path):
        raise PersistError(EXIT_INPUT, f"refusing to read through a symlink or reparse point: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        chunks = []
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _lock_run_id(lock_path: Path) -> str | None:
    try:
        payload = json.loads(_read_no_follow(lock_path).decode("utf-8"))
    except (OSError, ValueError, PersistError):
        return None
    return payload.get("run_id") if isinstance(payload, dict) else None


@dataclass
class PairLock:
    """A held per-pair lock. Release it in ``finally`` (or use it as a context manager)."""

    workspace: Path
    shipment_id: str
    feature_id: str
    run_id: str
    lock_path: Path
    evidence_path: Path
    held: bool = True

    def release(self) -> None:
        if not self.held:
            return
        self.held = False
        # Only ever remove our own lock.
        if _lock_run_id(self.lock_path) == self.run_id:
            try:
                os.unlink(self.lock_path)
            except FileNotFoundError:
                pass

    def __enter__(self) -> PairLock:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.release()


def _lock_path_for(root: Path, shipment_id: str, feature_id: str) -> Path:
    return root / LOCK_DIR / f"{shipment_id}-{feature_id}.lock"


def acquire_pair_lock(workspace: Path | str, shipment_id: str, feature_id: str, run_id: str) -> PairLock:
    """Create the per-pair lock with ``O_CREAT | O_EXCL`` after a directory-trust walk.

    Both the lock directory and ``docs/closure/evidence/`` are trust-checked
    before anything is created. An existing lock raises :class:`PersistError`
    with exit 7 and is never broken automatically.
    """

    if not _is_run_id(run_id):
        raise PersistError(EXIT_INPUT, f"run_id must be 32 lowercase hex characters (got {run_id!r})")
    try:
        evidence_path = build_evidence_path(workspace, shipment_id, feature_id)
        root = Path(workspace).resolve(strict=True)
    except (CascadeEvidenceError, OSError) as exc:
        raise PersistError(EXIT_INPUT, str(exc)) from exc
    for relative in (LOCK_DIR, EVIDENCE_DIR):
        _check_trusted_chain(root, relative)
    lock_dir = ensure_trusted_directory(root, LOCK_DIR)
    ensure_trusted_directory(root, EVIDENCE_DIR)
    lock_path = lock_dir / f"{shipment_id}-{feature_id}.lock"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(lock_path, flags, 0o600)
    except FileExistsError as exc:
        raise PersistError(
            EXIT_LOCKED,
            f"cascade-close lock already held: {lock_path} (removing a stale lock is an operator action)",
        ) from exc
    except OSError as exc:
        raise PersistError(EXIT_INPUT, f"cannot create lock {lock_path}: {exc}") from exc
    payload = json.dumps({"run_id": run_id, "pid": os.getpid(), "started_at": _utc_now()}, sort_keys=True)
    try:
        os.write(fd, (payload + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    return PairLock(
        workspace=root,
        shipment_id=shipment_id,
        feature_id=feature_id,
        run_id=run_id,
        lock_path=lock_path,
        evidence_path=evidence_path,
    )


def _require_held(lock: PairLock) -> None:
    if not isinstance(lock, PairLock) or not lock.held or _lock_run_id(lock.lock_path) != lock.run_id:
        raise PersistError(EXIT_INPUT, "the cascade-close pair lock is not held by this run")


# ---------------------------------------------------------------------------
# Existing-record check (PR #460 review; re-plan cycle-1 R1)
# ---------------------------------------------------------------------------


def check_existing_record(lock: PairLock, *, mode: str) -> Mapping[str, object] | None:
    """Return the existing ``pre_close`` record (or ``None``) for the locked pair.

    * an ``invoking`` record, an unreadable record, or an unknown phase: exit 7;
    * a ``post_close`` record: exit 2 (``evidence already finalized``);
    * a ``pre_close`` record under plain ``--classify-only``: exit 2
      (``evidence already exists``, no-clobber);
    * otherwise the ``pre_close`` record is returned unchanged, so the caller
      never re-reads it outside the lock. A ``cascade``-selected record in the
      mutating mode is the Step 0(c) record handed to A3, never overwritten
      here.
    """

    if mode not in _MODES:
        raise PersistError(EXIT_INPUT, f"unknown existing-record check mode {mode!r}")
    _require_held(lock)
    path = lock.evidence_path
    if not os.path.lexists(path):
        return None
    try:
        record = json.loads(_read_no_follow(path).decode("utf-8"))
    except PersistError:
        raise
    except (OSError, ValueError) as exc:
        raise PersistError(EXIT_LOCKED, f"existing evidence record is unreadable (operator review): {exc}") from exc
    if not isinstance(record, dict):
        raise PersistError(EXIT_LOCKED, "existing evidence record is not a JSON object (operator review)")
    phase = record.get("phase")
    if phase == "invoking":
        raise PersistError(EXIT_LOCKED, "an invoking evidence record exists (a prior run may have mutated)")
    if phase == "post_close":
        raise PersistError(EXIT_INPUT, "evidence already finalized")
    if phase != "pre_close" or not _is_run_id(record.get("run_id")):
        raise PersistError(EXIT_LOCKED, f"existing evidence record is ambiguous (phase {phase!r}; operator review)")
    if record.get("shipment_id") != lock.shipment_id or record.get("feature_id") != lock.feature_id:
        raise PersistError(EXIT_LOCKED, "existing evidence record names a different pair (operator review)")
    if mode == MODE_CLASSIFY_ONLY:
        raise PersistError(EXIT_INPUT, "evidence already exists")
    return record


# ---------------------------------------------------------------------------
# Owner-bound atomic write (AS-F01; Copilot PR #481 T6)
# ---------------------------------------------------------------------------


def _check_transition(
    existing: Mapping[str, object] | None,
    phase: str,
    owner_run_id: str,
    takeover_from_run_id: str | None,
) -> None:
    if existing is None:
        if takeover_from_run_id is not None:
            raise PersistError(EXIT_INPUT, "a pre_close takeover requires an existing pre_close record")
        if phase != "pre_close":
            raise PersistError(EXIT_INPUT, f"a new evidence record must start at pre_close (got {phase!r})")
        return
    old_phase = existing.get("phase")
    old_run_id = existing.get("run_id")
    if old_phase == "post_close":
        raise PersistError(EXIT_INPUT, "evidence already finalized; no transition out of post_close")
    if takeover_from_run_id is not None:
        if old_phase != "pre_close" or old_run_id != takeover_from_run_id or phase != "pre_close":
            raise PersistError(
                EXIT_INPUT,
                "pre_close takeover refused: the on-disk record is not the expected pre_close record "
                "or the new record is not pre_close",
            )
        return
    if old_run_id != owner_run_id:
        raise PersistError(EXIT_INPUT, "refusing a foreign writer: the on-disk record belongs to another run")
    if (old_phase, phase) not in _OWNER_TRANSITIONS:
        raise PersistError(EXIT_INPUT, f"refusing owner transition {old_phase!r} -> {phase!r}")


def _replace_with_retry(source: str, target: Path) -> None:
    for attempt in range(_REPLACE_RETRIES + 1):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            # A Windows sharing violation; bounded retries only.
            if attempt == _REPLACE_RETRIES:
                raise
            time.sleep(_REPLACE_BACKOFF_SECONDS * (2**attempt))


def _fsync_directory(directory: Path) -> None:
    if os.name == "nt":
        return  # unsupported on Windows
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_evidence_atomic(
    path: Path | str,
    record: Mapping[str, object],
    *,
    owner_run_id: str,
    takeover_from_run_id: str | None = None,
) -> None:
    """Atomically write ``record`` to its evidence path, bound to the owning run.

    The owning run (same ``run_id``, holding the pair lock) may move its own
    record ``pre_close -> invoking -> post_close``; any other writer and any
    transition out of ``post_close`` are refused. ``takeover_from_run_id``
    requests the ``pre_close`` takeover: the on-disk record must be
    ``pre_close`` with exactly that ``run_id``, and the new record must be
    ``pre_close`` with ``run_id == owner_run_id``. On any refusal the on-disk
    record is left byte-identical and :class:`PersistError` is raised.
    """

    target = Path(path)
    if not target.is_absolute():
        raise PersistError(EXIT_INPUT, f"evidence path must be absolute: {target}")
    if not isinstance(record, Mapping):
        raise PersistError(EXIT_INPUT, "evidence record must be a JSON object")
    if not _is_run_id(owner_run_id):
        raise PersistError(EXIT_INPUT, "owner_run_id must be 32 lowercase hex characters")
    if takeover_from_run_id is not None and not _is_run_id(takeover_from_run_id):
        raise PersistError(EXIT_INPUT, "takeover_from_run_id must be 32 lowercase hex characters")
    if record.get("run_id") != owner_run_id:
        raise PersistError(EXIT_INPUT, "the record's run_id is not the owning run's")
    phase = record.get("phase")
    if phase not in _PHASES:
        raise PersistError(EXIT_INPUT, f"unknown evidence phase {phase!r}")

    shipment_id, feature_id = record.get("shipment_id"), record.get("feature_id")
    if type(shipment_id) is not str or type(feature_id) is not str:
        raise PersistError(EXIT_INPUT, "the record must name its shipment_id and feature_id")
    workspace = target.parent.parent.parent.parent
    try:
        expected = build_evidence_path(workspace, shipment_id, feature_id)
    except CascadeEvidenceError as exc:
        raise PersistError(EXIT_INPUT, str(exc)) from exc
    root = workspace.resolve()
    _check_trusted_chain(root, EVIDENCE_DIR)
    if target.parent.resolve() / target.name != expected or not target.parent.is_dir():
        raise PersistError(EXIT_INPUT, f"{target} is not the evidence path of {shipment_id}/{feature_id}")
    if _lock_run_id(_lock_path_for(root, shipment_id, feature_id)) != owner_run_id:
        raise PersistError(EXIT_INPUT, "the owning run does not hold the cascade-close pair lock")
    if _is_link(target):
        raise PersistError(EXIT_INPUT, f"refusing a symlink or reparse-point evidence target: {target}")

    existing = None
    if os.path.lexists(target):
        try:
            existing = json.loads(_read_no_follow(target).decode("utf-8"))
        except PersistError:
            raise
        except (OSError, ValueError) as exc:
            raise PersistError(EXIT_INPUT, f"existing evidence record is unreadable: {exc}") from exc
        if not isinstance(existing, dict):
            raise PersistError(EXIT_INPUT, "existing evidence record is not a JSON object")
    _check_transition(existing, phase, owner_run_id, takeover_from_run_id)

    redacted, _ = redact_record_free_text(record)
    data = serialize_evidence_record(redacted).encode("utf-8")
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        _replace_with_retry(temp_name, target)
        _fsync_directory(target.parent)
    except OSError as exc:
        raise PersistError(EXIT_INPUT, f"evidence write failed: {exc}") from exc
    finally:
        if os.path.lexists(temp_name):
            os.unlink(temp_name)
