"""JSONL epoch sink — emit-only (Phase 2, U4, task 051.006).

Appends each :class:`~autoharness.telemetry.epoch.ExecutionEpoch` as exactly one
well-formed JSON object per line to the configured JSONL path (default alongside
the SQLite DB under ``.autoharness/metrics/``).

**Emit-only boundary:** this sink stops at the file. The external relational
schema and the ingestion path that consumes this stream are an agent-engram
concern (design §4) and are intentionally NOT implemented here.

**U2 (084.002-T) note:** the generic segment enumeration, no-replace seal,
retention pruning, canonical-line scan, and atomic-append primitives now live
in the internal ``_jsonl_segments`` module, shared with the ToolTelemetryEvent
journal (``tool_event_jsonl.py``). This module's own orchestration functions
(``scan_epoch_digest``, ``_revalidate_preflight``, ``append_epoch``,
``_seal_active_segment``, ``_rollover_if_needed``, ``_prune_sealed_segments``)
are kept byte-for-byte behaviorally identical to their pre-extraction form —
only their low-level pure-helper calls now delegate to ``_jsonl_segments`` —
so ``tests/test_telemetry_jsonl_sink.py`` continues to pass unmodified,
including its direct patches of ``_MAX_SEGMENT_BYTES``,
``_MAX_RETAINED_SEGMENTS``, ``_max_sealed_generation``, and ``os``.
"""

from __future__ import annotations

import json
# NOTE: ``os`` is imported here (rather than only inside ``_jsonl_segments``)
# because the pinned test suite patches ``jsonl_sink.os.unlink`` directly
# (``mock.patch.object(jsonl_sink.os, "unlink", ...)``). Since ``jsonl_sink.os``
# and ``_jsonl_segments.os`` are the SAME singleton module object, this import
# is required only so the attribute ``jsonl_sink.os`` resolves; the actual
# seal/unlink calls live in ``_jsonl_segments.claim_seal``.
import os  # noqa: F401
from pathlib import Path

from autoharness.telemetry import _jsonl_segments
from autoharness.telemetry._jsonl_segments import (
    JsonlPreflightScan,
    SinkWriteResult,
    TelemetryConflictError,
    active_inode as _active_inode,
    atomic_append_bytes as _atomic_append_bytes,
    canonical_json as _canonical_json,
    digest_record as _digest_record,
    scan_single_file as _scan_single_file,
    sealed_segment_path,
    sealed_segments,
    segment_read_paths,
)
from autoharness.telemetry.epoch import ExecutionEpoch

__all__ = [
    "JsonlPreflightScan",
    "SinkWriteResult",
    "TelemetryConflictError",
    "append_epoch",
    "canonical_payload_json",
    "find_epoch_digest",
    "payload_digest",
    "scan_epoch_digest",
    "sealed_segment_path",
    "sealed_segments",
    "segment_read_paths",
]

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


def _seal_active_segment(jsonl_path: Path) -> int | None:
    """Seal the active segment under the next free generation, no-replace.

    Returns the generation claimed, or ``None`` if the active segment was
    already sealed by a concurrent writer, or if a partial-seal rollback
    deferred the seal (the active still exceeds the threshold and the
    rollover is retried on the next append). On a generation collision the
    true max is re-read and the next generation attempted, so no global lock
    is needed and no sealed segment is ever overwritten.
    """
    while True:
        generation = _max_sealed_generation(jsonl_path) + 1
        target = sealed_segment_path(jsonl_path, generation)
        try:
            _jsonl_segments.claim_seal(jsonl_path, target)
            return generation
        except FileExistsError:
            continue
        except FileNotFoundError:
            return None
        except OSError:
            # Partial-seal rollback (e.g. a residual sharing violation): defer.
            return None


def _rollover_if_needed(jsonl_path: Path) -> None:
    """Seal and prune when the active segment has reached ``_MAX_SEGMENT_BYTES``.

    The size check runs BEFORE the pending append. Under a single serialized
    progression the resulting sealed segment is at most
    ``_MAX_SEGMENT_BYTES + one max record``, and an oversized single record (whose
    encoded line already exceeds the threshold) is written intact and sealed into
    its own segment on the following append — lines are never split.

    This is a NOMINAL, not hard, bound: the sink supports concurrent writers with
    no global lock, so N writers can each observe a below-threshold size and then
    append, and a writer holding an already-open descriptor can append after
    sealing. A sealed segment can therefore exceed the threshold by up to the sum
    of all concurrently in-flight records. That overshoot is bounded by writer
    concurrency, is acceptable under the best-effort mirror contract, and never
    causes data loss — SQLite stays authoritative and reads reconcile by
    ``epoch_id``.
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


def canonical_payload_json(epoch: ExecutionEpoch) -> str:
    return _canonical_json(epoch.to_record())


def payload_digest(epoch: ExecutionEpoch) -> str:
    return _digest_record(epoch.to_record())


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
    active_inode = _active_inode(jsonl_path)

    if start_offset <= 0:
        for _generation, sealed_path in sealed_segments(jsonl_path):
            digest, _offset = _scan_single_file(sealed_path, "epoch_id", epoch_id, 0)
            if digest is not None:
                return JsonlPreflightScan(
                    existing_digest=digest,
                    scanned_offset=active_size,
                    active_generation=active_generation,
                    active_size=active_size,
                    active_inode=active_inode,
                )

    active_digest, active_offset = _scan_single_file(jsonl_path, "epoch_id", epoch_id, start_offset)
    return JsonlPreflightScan(
        existing_digest=active_digest,
        scanned_offset=active_offset,
        active_generation=active_generation,
        active_size=active_size,
        active_inode=active_inode,
    )


def find_epoch_digest(jsonl_path: Path, epoch_id: str) -> str | None:
    """Return the digest for the first accepted JSONL record with ``epoch_id``."""
    return scan_epoch_digest(jsonl_path, epoch_id).existing_digest


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
    replacement — so a full cross-segment rescan is performed.

    The generation number can briefly ABA back to the same value during the
    non-atomic two-step hard-link seal, so the active inode is also compared: if it
    changed, the active file was swapped underneath a matching generation and the
    recorded offset is stale, forcing a full rescan. This is a best-effort
    optimization on the mirror — even if a swap slipped through, the missed
    detection only yields a duplicate mirror line reconciled on read (epoch_id
    dedupe + SQLite-over-JSONL precedence); SQLite remains authoritative.

    Otherwise the offset optimization resumes the active-tail scan from the
    recorded offset.
    """
    current_generation = _active_generation(jsonl_path)
    if scan.active_generation != current_generation:
        return scan_epoch_digest(jsonl_path, epoch_id).existing_digest
    current_inode = _active_inode(jsonl_path)
    if scan.active_inode and current_inode and scan.active_inode != current_inode:
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
