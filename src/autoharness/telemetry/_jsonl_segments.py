"""Shared segmented JSONL primitives (U2, 084.002-T).

Internal helper module. Reused by the execution-epoch JSONL sink
(``jsonl_sink.py``) and the ToolTelemetryEvent journal
(``tool_event_jsonl.py``) so both sinks share one implementation of segment
enumeration, no-replace rollover/seal, retention pruning, canonical-line
scanning, and file identity instead of maintaining two copies.

Not part of the public telemetry API. Import from the owning sink module
(``jsonl_sink.py`` / ``tool_event_jsonl.py``), which pin their own
module-level rotation/retention constants and dedupe key field and pass them
into these generic, parameter-driven functions.

**Zero behavior change contract (U2):** every primitive here is a verbatim
(or trivially key-field-generalized) extraction of logic that previously lived
directly in ``jsonl_sink.py``. ``jsonl_sink.py`` keeps its own orchestration
functions (``scan_epoch_digest``, ``_revalidate_preflight``, ``append_epoch``,
``_seal_active_segment``, ``_rollover_if_needed``, ``_prune_sealed_segments``)
literally in place, calling these shared primitives, so the pinned behavior in
``tests/test_telemetry_jsonl_sink.py`` — including direct patching of
``jsonl_sink._MAX_SEGMENT_BYTES``, ``jsonl_sink._MAX_RETAINED_SEGMENTS``,
``jsonl_sink._max_sealed_generation``, and ``jsonl_sink.os`` — is unaffected.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# Zero-padded minimum width of the sealed-segment generation suffix.
GENERATION_WIDTH = 5


class TelemetryConflictError(RuntimeError):
    """Raised when a JSONL replay conflicts with first-write content."""


@dataclass(frozen=True)
class SinkWriteResult:
    status: str
    payload_digest: str


@dataclass(frozen=True)
class JsonlPreflightScan:
    existing_digest: str | None
    scanned_offset: int
    # Active-segment identity captured at scan time (finding 6). Callers only
    # trust ``scanned_offset`` when the recorded generation still matches the
    # current active segment; a rollover between preflight and append changes
    # the generation and forces a full cross-segment rescan.
    active_generation: int = 0
    active_size: int = 0
    # Inode/file-index identity of the active segment at scan time. The
    # generation number can briefly ABA back to the same value during the
    # non-atomic two-step hard-link seal (link created, active not yet
    # unlinked, then a fresh active recreated at the same generation). The
    # inode of a freshly recreated active differs from the scanned one, so
    # comparing it closes the ABA window. ``0`` means identity was unavailable
    # and only generation+size apply.
    active_inode: int = 0


def active_inode(jsonl_path: Path) -> int:
    """Best-effort inode / Win32 file-index identity of the active segment."""
    try:
        return jsonl_path.stat().st_ino
    except OSError:
        return 0


def sealed_segment_path(
    jsonl_path: Path,
    generation: int,
    *,
    generation_width: int = GENERATION_WIDTH,
) -> Path:
    """Return the path of the sealed segment for ``generation`` beside the active."""
    return jsonl_path.parent / f"{jsonl_path.name}.{generation:0{generation_width}d}"


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
    """Shared segment enumeration: retained sealed segments (oldest->newest)
    then the active segment. Single source of truth for segment ordering,
    reused by replay scans and readers so both span rotated history and
    preserve first-write precedence (oldest record wins on dedupe)."""
    paths = [path for _generation, path in sealed_segments(jsonl_path)]
    if jsonl_path.exists():
        paths.append(jsonl_path)
    return paths


def max_sealed_generation(jsonl_path: Path) -> int:
    generations = sealed_segments(jsonl_path)
    return generations[-1][0] if generations else 0


def claim_seal(active_path: Path, target_path: Path) -> None:
    """No-replace seal of the active segment to ``target_path``.

    ``os.link`` creates the sealed name as a second hard link to the active
    inode, then the active name is unlinked. ``os.link`` raises
    ``FileExistsError`` if the target already exists, so a concurrent rollover
    that picked the same generation can NEVER clobber an already-sealed
    segment. It raises ``FileNotFoundError`` if the active segment was already
    sealed away by another writer.

    If unlinking the active name fails *after* the link was created, the
    partial seal is rolled back by removing the just-created link so no
    duplicate half-sealed segment is left behind, and the error propagates so
    the caller can retry the rollover on a later append.
    """
    os.link(str(active_path), str(target_path))
    try:
        os.unlink(str(active_path))
    except FileNotFoundError:
        pass
    except OSError:
        try:
            os.unlink(str(target_path))
        except FileNotFoundError:
            pass
        raise


def seal_active_segment(
    jsonl_path: Path,
    *,
    max_sealed_generation_fn: Callable[[Path], int] = max_sealed_generation,
) -> int | None:
    """Seal the active segment under the next free generation, no-replace.

    Returns the generation claimed, or ``None`` if the active segment was
    already sealed by a concurrent writer, or a partial-seal rollback deferred
    the seal. On a generation collision the true max is re-read via
    ``max_sealed_generation_fn`` and the next generation attempted, so no
    global lock is needed and no sealed segment is ever overwritten.
    """
    while True:
        generation = max_sealed_generation_fn(jsonl_path) + 1
        target = sealed_segment_path(jsonl_path, generation)
        try:
            claim_seal(jsonl_path, target)
            return generation
        except FileExistsError:
            continue
        except FileNotFoundError:
            return None
        except OSError:
            return None


def rollover_if_needed(
    jsonl_path: Path,
    *,
    max_segment_bytes: int,
    max_retained_segments: int,
    max_sealed_generation_fn: Callable[[Path], int] = max_sealed_generation,
) -> None:
    """Seal and prune when the active segment has reached ``max_segment_bytes``.

    The size check runs BEFORE the pending append; this is a NOMINAL, not
    hard, bound under concurrent writers (see ``jsonl_sink.py`` for the full
    concurrency-safety rationale, which this generalized primitive preserves).
    """
    try:
        current_size = jsonl_path.stat().st_size
    except FileNotFoundError:
        return
    if current_size < max_segment_bytes:
        return
    if seal_active_segment(jsonl_path, max_sealed_generation_fn=max_sealed_generation_fn) is not None:
        prune_sealed_segments(jsonl_path, max_retained_segments=max_retained_segments)


def prune_sealed_segments(jsonl_path: Path, *, max_retained_segments: int) -> None:
    """Prune the oldest sealed generations beyond the retention window.

    Never targets the active segment. Retention is intentionally lossy on the
    best-effort mirror only; the authoritative store deduplicates on read.
    """
    sealed = sealed_segments(jsonl_path)  # oldest generation first
    excess = len(sealed) - max_retained_segments
    for index in range(max(0, excess)):
        _generation, path = sealed[index]
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_record(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()


def scan_single_file(
    path: Path,
    key_field: str,
    key_value: str,
    start_offset: int,
) -> tuple[str | None, int]:
    """Scan one segment file for ``key_field == key_value``; return
    ``(digest, offset_reached)``."""
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
                # A single corrupt historical line must not raise and
                # permanently disable future JSONL emission. Skip and
                # continue scanning, mirroring reader resilience.
                continue
            if isinstance(record, dict) and record.get(key_field) == key_value:
                return digest_record(record), handle.tell()
        return None, handle.tell()


def scan_key_digest(
    jsonl_path: Path,
    key_field: str,
    key_value: str,
    *,
    active_generation_fn: Callable[[Path], int],
    start_offset: int = 0,
) -> JsonlPreflightScan:
    """Return digest and active-segment identity when scanning for
    ``key_field == key_value`` across sealed segments plus the active one.

    ``start_offset`` is a resume optimization for the ACTIVE segment only; see
    ``jsonl_sink.scan_epoch_digest`` for the full rationale, preserved here
    verbatim under a generalized dedupe key.
    """
    active_generation = active_generation_fn(jsonl_path)
    active_size = jsonl_path.stat().st_size if jsonl_path.exists() else 0
    active_ino = active_inode(jsonl_path)

    if start_offset <= 0:
        for _generation, sealed_path in sealed_segments(jsonl_path):
            digest, _offset = scan_single_file(sealed_path, key_field, key_value, 0)
            if digest is not None:
                return JsonlPreflightScan(
                    existing_digest=digest,
                    scanned_offset=active_size,
                    active_generation=active_generation,
                    active_size=active_size,
                    active_inode=active_ino,
                )

    active_digest, active_offset = scan_single_file(jsonl_path, key_field, key_value, start_offset)
    return JsonlPreflightScan(
        existing_digest=active_digest,
        scanned_offset=active_offset,
        active_generation=active_generation,
        active_size=active_size,
        active_inode=active_ino,
    )


def revalidate_preflight(
    jsonl_path: Path,
    key_value: str,
    scan: JsonlPreflightScan,
    *,
    active_generation_fn: Callable[[Path], int],
    scan_fn: Callable[..., JsonlPreflightScan],
) -> str | None:
    """Re-derive the existing digest for a supplied preflight whose active
    segment may have advanced or rolled over since the scan. See
    ``jsonl_sink._revalidate_preflight`` for the full rationale, preserved
    here verbatim under a generalized dedupe key and pluggable scan callable.
    """
    current_generation = active_generation_fn(jsonl_path)
    if scan.active_generation != current_generation:
        return scan_fn(jsonl_path, key_value, start_offset=0).existing_digest
    current_inode = active_inode(jsonl_path)
    if scan.active_inode and current_inode and scan.active_inode != current_inode:
        return scan_fn(jsonl_path, key_value, start_offset=0).existing_digest
    current_size = jsonl_path.stat().st_size if jsonl_path.exists() else 0
    if current_size == scan.scanned_offset:
        return None
    start_offset = scan.scanned_offset if current_size >= scan.scanned_offset else 0
    return scan_fn(jsonl_path, key_value, start_offset=start_offset).existing_digest


def atomic_append_bytes(path: Path, data: bytes) -> None:
    """Append ``data`` as a single atomic write, safe for concurrent writers.

    On POSIX, a single ``os.write`` to an ``O_APPEND`` descriptor is atomic. On
    Windows, ``O_APPEND`` via the C runtime performs a non-atomic seek+write,
    so we open the file through Win32 ``CreateFileW`` with
    ``FILE_APPEND_DATA`` access, which the kernel guarantees appends
    atomically at end-of-file.
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
    # FILE_SHARE_DELETE lets a concurrent rollover unlink/rename the active
    # name while this append handle is open.
    FILE_SHARE_DELETE = 0x00000004
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
        str(path), FILE_APPEND_DATA,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
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


def append_record(
    *,
    jsonl_path: Path,
    key_field: str,
    key_value: str,
    record: dict[str, Any],
    line_json: str,
    preflight: JsonlPreflightScan | None,
    scan_fn: Callable[..., JsonlPreflightScan],
    revalidate_fn: Callable[[Path, str, JsonlPreflightScan], str | None],
    rollover_fn: Callable[[Path], None],
) -> SinkWriteResult:
    """Append one record as a single atomic JSON line, with idempotent-replay
    and conflict detection. Generic counterpart of ``jsonl_sink.append_epoch``
    parameterized by dedupe ``key_field``/``key_value`` and caller-supplied
    scan/revalidate/rollover callables so a second sink (e.g. the
    ToolTelemetryEvent journal) can reuse the exact same replay/rotation
    semantics under its own module-level rotation constants.
    """
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    digest = digest_record(record)
    preflight_supplied = preflight is not None
    scan = preflight or scan_fn(jsonl_path, key_value, start_offset=0)
    existing_digest = scan.existing_digest
    if preflight_supplied and existing_digest is None:
        existing_digest = revalidate_fn(jsonl_path, key_value, scan)
    if existing_digest == digest:
        return SinkWriteResult(status="idempotent_replay", payload_digest=digest)
    if existing_digest is not None:
        raise TelemetryConflictError(
            f"conflicting immutable replay for {key_field} {key_value}: "
            f"existing digest {existing_digest} != {digest}"
        )
    rollover_fn(jsonl_path)
    atomic_append_bytes(jsonl_path, (line_json + "\n").encode("utf-8"))
    return SinkWriteResult(status="created", payload_digest=digest)
