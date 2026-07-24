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


class TelemetryConflictError(RuntimeError):
    """Raised when a JSONL epoch replay conflicts with first-write content."""


@dataclass(frozen=True)
class SinkWriteResult:
    status: str
    payload_digest: str


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


def find_epoch_digest(jsonl_path: Path, epoch_id: str) -> str | None:
    """Return the digest for the first accepted JSONL record with ``epoch_id``."""
    if not jsonl_path.exists():
        return None
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if isinstance(record, dict) and record.get("epoch_id") == epoch_id:
                return _digest_record(record)
    return None


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


def append_epoch(epoch: ExecutionEpoch, jsonl_path: Path) -> SinkWriteResult:
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
    """
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    digest = payload_digest(epoch)
    existing_digest = find_epoch_digest(jsonl_path, epoch.epoch_id)
    if existing_digest == digest:
        return SinkWriteResult(status="idempotent_replay", payload_digest=digest)
    if existing_digest is not None:
        raise TelemetryConflictError(
            f"conflicting immutable replay for epoch_id {epoch.epoch_id}: "
            f"existing digest {existing_digest} != {digest}"
        )
    line = json.dumps(epoch.to_record(), separators=(",", ":")) + "\n"
    _atomic_append_bytes(jsonl_path, line.encode("utf-8"))
    return SinkWriteResult(status="created", payload_digest=digest)
