"""JSONL epoch sink — emit-only (Phase 2, U4, task 051.006).

Appends each :class:`~autoharness.telemetry.epoch.ExecutionEpoch` as exactly one
well-formed JSON object per line to the configured JSONL path (default alongside
the SQLite DB under ``.autoharness/metrics/``).

**Emit-only boundary:** this sink stops at the file. The external relational
schema and the ingestion path that consumes this stream are an agent-engram
concern (design §4) and are intentionally NOT implemented here.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autoharness.telemetry.epoch import ExecutionEpoch

# --- Segment rollover / retention (module constants, NOT runtime config) ------
#
# Rotation thresholds are deliberately module-level constants rather than
# ``TelemetryConfig`` fields: exposing them as configuration would require a
# schema-versioned bump across the four telemetry schemas (all
# ``additionalProperties: false``), ``config.py`` parsing, and the ``record.py``
# caller for no demonstrated per-workspace tuning need. Tests override them
# locally (e.g. ``mock.patch.object``) to exercise rollover at a low threshold.
#
# The JSONL sink is a BEST-EFFORT, concurrent-writer-safe human-readable mirror;
# SQLite is the authoritative first-write-immutable store. Rotation preserves
# that contract: sealing uses a no-replace generation claim so a concurrent
# rollover never clobbers a sealed segment, sealed segments are NOT claimed
# byte-immutable (a late ``O_APPEND`` into a just-sealed segment is acceptable and
# reconciled on read), and pruning is by-design lossy on the mirror only (SQLite
# retains authoritative history). No global write lock is introduced.

# Active segment rolls over once it reaches or exceeds this size. Default large
# enough that the existing test suite never triggers rollover.
_MAX_SEGMENT_BYTES = 8 * 1024 * 1024
# Number of sealed segments retained; oldest sealed generation pruned first.
_MAX_RETAINED_SEGMENTS = 8
# Zero-padded minimum width of the sealed-segment generation suffix.
_GENERATION_WIDTH = 5


class TelemetryConflictError(RuntimeError):
    """Raised when a JSONL epoch replay conflicts with first-write content."""


@dataclass(frozen=True)
class SinkWriteResult:
    status: str
    payload_digest: str


@dataclass(frozen=True)
class JsonlPreflightScan:
    existing_digest: str | None
    scanned_offset: int
    # Active-segment identity captured at scan time (finding 6). ``append_epoch``
    # only trusts ``scanned_offset`` when the recorded generation still matches the
    # current active segment; a rollover between preflight and append changes the
    # generation and forces a full cross-segment rescan.
    active_generation: int = 0
    active_size: int = 0


def sealed_segment_path(jsonl_path: Path, generation: int) -> Path:
    """Return the path of the sealed segment for ``generation`` beside the active."""
    return jsonl_path.parent / f"{jsonl_path.name}.{generation:0{_GENERATION_WIDTH}d}"


def sealed_segments(jsonl_path: Path) -> list[tuple[int, Path]]:
    """Return ``(generation, path)`` for sealed segments, oldest generation first."""
    parent = jsonl_path.parent
    if not parent.exists():
        return []
    prefix = jsonl_path.name + "."
    found: list[tuple[int, Path]] = []
    for child in parent.iterdir():
        name = child.name
        if not name.startswith(prefix):
            continue
        suffix = name[len(prefix):]
        if suffix.isdigit():
            found.append((int(suffix), child))
    found.sort(key=lambda item: item[0])
    return found


def segment_read_paths(jsonl_path: Path) -> list[Path]:
    """Shared segment enumeration: retained sealed segments (oldest→newest) then
    the active segment. This is the single source of truth for segment ordering,
    reused by the replay scan and the reader so both span rotated history and
    preserve first-write precedence (oldest record wins on dedupe)."""
    paths = [path for _generation, path in sealed_segments(jsonl_path)]
    if jsonl_path.exists():
        paths.append(jsonl_path)
    return paths


def _max_sealed_generation(jsonl_path: Path) -> int:
    generations = sealed_segments(jsonl_path)
    return generations[-1][0] if generations else 0


def _active_generation(jsonl_path: Path) -> int:
    """Identity of the current active segment: the generation it would seal to.

    A rollover seals the active file to ``max(sealed) + 1`` and creates a fresh
    active, so this value strictly increases across any rollover and is the signal
    that a preflight offset captured before the rollover is stale.
    """
    return _max_sealed_generation(jsonl_path) + 1


def _claim_seal(active_path: Path, target_path: Path) -> None:
    """No-replace seal of the active segment to ``target_path``.

    ``os.link`` creates the sealed name as a second hard link to the active
    inode, then the active name is unlinked. ``os.link`` raises ``FileExistsError``
    if the target already exists, so a concurrent rollover that picked the same
    generation can NEVER clobber an already-sealed segment — the loser retries the
    next generation. It raises ``FileNotFoundError`` if the active segment was
    already sealed away by another writer.

    A writer that opened the active fd before the rollover may still land a late
    append in the just-sealed inode; that is acceptable under the sink's
    best-effort contract and is reconciled on read, not prevented by a lock.
    """
    os.link(str(active_path), str(target_path))
    os.unlink(str(active_path))


def _seal_active_segment(jsonl_path: Path) -> int | None:
    """Seal the active segment under the next free generation, no-replace.

    Returns the generation claimed, or ``None`` if the active segment was already
    sealed by a concurrent writer. On a generation collision the true max is
    re-read and the next generation attempted, so no global lock is needed and no
    sealed segment is ever overwritten.
    """
    while True:
        generation = _max_sealed_generation(jsonl_path) + 1
        target = sealed_segment_path(jsonl_path, generation)
        try:
            _claim_seal(jsonl_path, target)
            return generation
        except FileExistsError:
            continue
        except FileNotFoundError:
            return None


def _rollover_if_needed(jsonl_path: Path) -> None:
    """Seal and prune when the active segment has reached ``_MAX_SEGMENT_BYTES``.

    The size check runs BEFORE the pending append, so a sealed segment is at most
    ``_MAX_SEGMENT_BYTES + one max record`` and an oversized single record (whose
    encoded line already exceeds the threshold) is written intact and sealed into
    its own segment on the following append — lines are never split.
    """
    try:
        current_size = jsonl_path.stat().st_size
    except FileNotFoundError:
        return
    if current_size < _MAX_SEGMENT_BYTES:
        return
    if _seal_active_segment(jsonl_path) is not None:
        _prune_sealed_segments(jsonl_path)


def _prune_sealed_segments(jsonl_path: Path) -> None:
    """Prune the oldest sealed generations beyond the retention window.

    Keeps at most ``_MAX_RETAINED_SEGMENTS`` sealed segments, removing the oldest
    generations first. It NEVER targets the active segment (the base name is not a
    sealed segment) and never deletes authoritative SQLite data — retention is
    intentionally lossy on the best-effort mirror only. A sealed segment carrying
    an ``epoch_id`` that is pruned pushes that epoch past the replay horizon, so a
    later replay of it is re-appended; SQLite remains authoritative and
    deduplicates on read.
    """
    sealed = sealed_segments(jsonl_path)  # oldest generation first
    excess = len(sealed) - _MAX_RETAINED_SEGMENTS
    for index in range(max(0, excess)):
        _generation, path = sealed[index]
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_payload_json(epoch: ExecutionEpoch) -> str:
    return _canonical_json(epoch.to_record())


def payload_digest(epoch: ExecutionEpoch) -> str:
    import hashlib

    return hashlib.sha256(canonical_payload_json(epoch).encode("utf-8")).hexdigest()


def _digest_record(record: dict[str, Any]) -> str:
    import hashlib

    return hashlib.sha256(_canonical_json(record).encode("utf-8")).hexdigest()


def _scan_single_file(
    path: Path,
    epoch_id: str,
    start_offset: int,
) -> tuple[str | None, int]:
    """Scan one segment file for ``epoch_id``; return ``(digest, offset_reached)``."""
    if not path.exists():
        return None, 0
    file_size = path.stat().st_size
    offset = max(0, min(start_offset, file_size))
    with path.open("rb") as handle:
        handle.seek(offset)
        for raw_line in handle:
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                # A single corrupt historical line must not raise and permanently
                # disable future JSONL emission (every append runs this preflight
                # scan). The reader already skips malformed lines; mirror that
                # resilience here and keep scanning.
                continue
            if isinstance(record, dict) and record.get("epoch_id") == epoch_id:
                return _digest_record(record), handle.tell()
        return None, handle.tell()


def scan_epoch_digest(
    jsonl_path: Path,
    epoch_id: str,
    *,
    start_offset: int = 0,
) -> JsonlPreflightScan:
    """Return digest and active-segment identity when scanning for ``epoch_id``.

    The scan spans the active segment plus all retained sealed segments so that
    idempotent-replay and conflict detection hold across rotated segments (within
    the retention horizon). A match in ANY retained segment counts.

    ``start_offset`` is a resume optimization for the ACTIVE segment only: a
    positive value means the caller already scanned the sealed segments and the
    active head during preflight under a matching generation identity, so only the
    active tail needs rescanning. The offset is never applied to sealed segments,
    which are always scanned in full.
    """
    active_generation = _active_generation(jsonl_path)
    active_size = jsonl_path.stat().st_size if jsonl_path.exists() else 0

    if start_offset <= 0:
        for _generation, sealed_path in sealed_segments(jsonl_path):
            digest, _offset = _scan_single_file(sealed_path, epoch_id, 0)
            if digest is not None:
                return JsonlPreflightScan(
                    existing_digest=digest,
                    scanned_offset=active_size,
                    active_generation=active_generation,
                    active_size=active_size,
                )

    active_digest, active_offset = _scan_single_file(jsonl_path, epoch_id, start_offset)
    return JsonlPreflightScan(
        existing_digest=active_digest,
        scanned_offset=active_offset,
        active_generation=active_generation,
        active_size=active_size,
    )


def find_epoch_digest(jsonl_path: Path, epoch_id: str) -> str | None:
    """Return the digest for the first accepted JSONL record with ``epoch_id``."""
    return scan_epoch_digest(jsonl_path, epoch_id).existing_digest


def _atomic_append_bytes(path: Path, data: bytes) -> None:
    """Append ``data`` as a single atomic write, safe for concurrent writers.

    On POSIX, a single ``os.write`` to an ``O_APPEND`` descriptor is atomic. On
    Windows, ``O_APPEND`` via the C runtime performs a non-atomic seek+write, so
    we open the file through Win32 ``CreateFileW`` with ``FILE_APPEND_DATA``
    access, which the kernel guarantees appends atomically at end-of-file.
    """
    if sys.platform == "win32":
        _win_atomic_append(path, data)
        return
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        written = os.write(fd, data)
        if written != len(data):
            raise OSError(
                f"short JSONL append: wrote {written} of {len(data)} bytes to {path}"
            )
    finally:
        os.close(fd)


def _win_atomic_append(path: Path, data: bytes) -> None:
    import ctypes
    from ctypes import wintypes

    FILE_APPEND_DATA = 0x0004
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    OPEN_ALWAYS = 4
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    handle = kernel32.CreateFileW(
        str(path), FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
        None, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, None,
    )
    if handle == INVALID_HANDLE_VALUE:
        raise OSError(ctypes.get_last_error(), f"CreateFileW failed for {path}")
    try:
        written = wintypes.DWORD(0)
        ok = kernel32.WriteFile(handle, data, len(data), ctypes.byref(written), None)
        if not ok:
            raise OSError(ctypes.get_last_error(), f"WriteFile failed for {path}")
        if written.value != len(data):
            raise OSError(
                f"short JSONL append: wrote {written.value} of {len(data)} bytes to {path}"
            )
    finally:
        kernel32.CloseHandle(handle)


def _revalidate_preflight(
    jsonl_path: Path,
    epoch_id: str,
    scan: JsonlPreflightScan,
) -> str | None:
    """Re-derive the existing digest for a supplied preflight whose active segment
    may have advanced or rolled over since the scan.

    If the active-segment generation changed (a rollover sealed the scanned active
    and created a fresh one), the recorded ``scanned_offset`` belongs to a
    different file and MUST NOT be trusted — including an equal-sized or larger
    replacement — so a full cross-segment rescan is performed. Otherwise the offset
    optimization resumes the active-tail scan from the recorded offset.
    """
    current_generation = _active_generation(jsonl_path)
    if scan.active_generation != current_generation:
        return scan_epoch_digest(jsonl_path, epoch_id).existing_digest
    current_size = jsonl_path.stat().st_size if jsonl_path.exists() else 0
    if current_size == scan.scanned_offset:
        return None
    start_offset = scan.scanned_offset if current_size >= scan.scanned_offset else 0
    return scan_epoch_digest(
        jsonl_path, epoch_id, start_offset=start_offset
    ).existing_digest


def append_epoch(
    epoch: ExecutionEpoch,
    jsonl_path: Path,
    *,
    preflight: JsonlPreflightScan | None = None,
) -> SinkWriteResult:
    """Append one epoch as a single atomic JSON line to the JSONL mirror.

    Each record is written with a single atomic append of the complete line, so a
    line is never interleaved, split, or partially written even under concurrent
    writers. The idempotent-replay digest check and the append are NOT a single
    atomic transaction, however: two processes writing the same ``epoch_id``
    concurrently can each pass the check and produce a duplicate line. That is
    benign by design — JSONL is a best-effort human-readable mirror, while SQLite
    is the authoritative first-write-immutable store. Readers deduplicate by
    ``epoch_id`` and apply SQLite-over-JSONL precedence, so duplicate mirror lines
    are reconciled on read rather than by locking this secondary sink.

    Replay checks span the active segment plus all retained sealed segments, so
    idempotent-replay and conflict detection hold across rotated segments — but
    only within the retention horizon. Once the segment carrying an ``epoch_id`` is
    pruned, a later replay of that ``epoch_id`` can no longer be detected on the
    mirror and is appended as new; SQLite remains authoritative and deduplicates on
    read.
    """
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    digest = payload_digest(epoch)
    preflight_supplied = preflight is not None
    scan = preflight or scan_epoch_digest(jsonl_path, epoch.epoch_id)
    existing_digest = scan.existing_digest
    if preflight_supplied and existing_digest is None:
        existing_digest = _revalidate_preflight(jsonl_path, epoch.epoch_id, scan)
    if existing_digest == digest:
        return SinkWriteResult(status="idempotent_replay", payload_digest=digest)
    if existing_digest is not None:
        raise TelemetryConflictError(
            f"conflicting immutable replay for epoch_id {epoch.epoch_id}: "
            f"existing digest {existing_digest} != {digest}"
        )
    _rollover_if_needed(jsonl_path)
    line = json.dumps(epoch.to_record(), separators=(",", ":")) + "\n"
    _atomic_append_bytes(jsonl_path, line.encode("utf-8"))
    return SinkWriteResult(status="created", payload_digest=digest)
