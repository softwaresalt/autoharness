"""Append-only session journal (119.005-T).

:class:`SessionJournal` persists one JSON object per line under
``<workspace_root>/.autoharness/sessions/<session_id>/journal.jsonl``:

* Line 0 is a schema-versioned header record (``{"schema_version": 1,
  "session_id": ..., "kind": "header", "seq": 0}``), written once before any
  event line.
* Every subsequent line carries a monotonically increasing integer ``seq``
  (continuing on from the header's ``seq=0``) and a UTC ISO-8601
  ``timestamp``.

**Redaction choke point**: every write -- including the header line --
routes through :func:`autoharness.supervise.redact.redact_record`. There is
no raw-write API. When a record cannot be safely redacted (fails closed),
this module writes a small ``redaction_failed`` marker record instead of
ever writing the original unredacted content, while still preserving the
append-only, monotonically increasing ``seq`` sequence.

**Path containment**: this module REUSES
:func:`autoharness.supervise.locking._resolve_contained_path` rather than
re-implementing the same escape-detection logic a second time (the two
concerns -- "does this path stay inside the workspace root" -- are
identical, and duplicating it would risk the two copies drifting out of
sync). An escaping ``session_id`` (e.g. containing ``..``) therefore raises
:class:`~autoharness.supervise.errors.LockError`, reusing locking.py's own
containment-failure exception type, rather than being silently clamped.

**H6 containment (git-ignore)**: on journal-root creation this module calls
:func:`autoharness.supervise.locking.ensure_ignored` with the ``"sessions"``
entry -- the SAME reused helper 118.005-T/127-S already introduced for the
guard/record lock files -- so there is exactly one ``.gitignore``
maintenance code path, not a second competing one.

**Resume cursor**: :func:`read_cursor` reads back the last successfully
written ``seq`` from an existing journal file, tolerating a crash-mid-write
(a final, truncated/corrupt line) by skipping it rather than raising.
"""

from __future__ import annotations

import dataclasses
import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from autoharness.supervise.contracts import ChildOutputUnavailable
from autoharness.supervise.locking import _resolve_contained_path, ensure_ignored
from autoharness.supervise.redact import Redactor, redact_record

PathLike = Union[str, "Path"]

JOURNAL_FILENAME = "journal.jsonl"
SCHEMA_VERSION = 1

# Journal roots live under .autoharness/sessions/<session_id>/, reusing the
# SAME .autoharness/.gitignore file locking.py already maintains for the
# guard/record lock files -- see the module docstring's H6 note.
_SESSIONS_RELATIVE = Path("sessions")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_cursor(path: PathLike) -> int:
    """Return the last successfully written ``seq`` in the journal at ``path``.

    Returns ``-1`` when the file does not exist or contains no valid
    ``seq``-bearing line, so a caller can uniformly compute the next seq as
    ``read_cursor(path) + 1`` whether resuming an existing journal or
    starting a brand new one.

    Tolerates a truncated/corrupt trailing line (the signature of a crash
    mid-write): such a line is skipped rather than raising.
    """

    journal_path = Path(path)
    if not journal_path.exists():
        return -1

    last_valid_seq = -1
    with journal_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                # Truncated/corrupt trailing line from a crash mid-write:
                # ignore it rather than crashing the resume.
                continue
            seq = record.get("seq") if isinstance(record, Mapping) else None
            if isinstance(seq, int):
                last_valid_seq = seq
    return last_valid_seq


class SessionJournal:
    """Append-only JSONL journal for a single supervised session."""

    def __init__(
        self,
        workspace_root: PathLike,
        session_id: str,
        *,
        redactor: Optional[Redactor] = None,
    ) -> None:
        self.workspace_root = Path(workspace_root)
        self.session_id = session_id
        self._redactor = redactor

        # Containment check runs before any write. An escaping session_id
        # (e.g. "../../evil") raises LockError immediately rather than being
        # clamped into some other, unintended location.
        self.session_dir = _resolve_contained_path(
            self.workspace_root, Path(".autoharness") / _SESSIONS_RELATIVE / session_id
        )
        self.journal_path = self.session_dir / JOURNAL_FILENAME

        self._next_seq = 0
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        self.session_dir.mkdir(parents=True, exist_ok=True)
        # Reuse the SAME ignore-file helper locking.py already introduced;
        # the entry is relative to .autoharness/, matching how SessionLock
        # registers its own guard/record relative paths.
        ensure_ignored(self.workspace_root, _SESSIONS_RELATIVE.as_posix())

        if self.journal_path.exists() and self.journal_path.stat().st_size > 0:
            self._terminate_truncated_trailing_line()
            last_seq = read_cursor(self.journal_path)
            if last_seq >= 0:
                self._next_seq = last_seq + 1
                self._initialized = True
                return
            # 128-S review remediation: the file is non-empty but contains
            # NO valid seq-bearing record at all -- e.g. a crash during the
            # very first header write left only a corrupt fragment (already
            # isolated onto its own line above). Treat this identically to
            # a brand-new journal and fall through to write a proper
            # schema-versioned header at seq 0, rather than silently
            # skipping the header and letting the first real event claim
            # seq 0 without one ever having been written.

        header = {
            "schema_version": SCHEMA_VERSION,
            "session_id": self.session_id,
            "kind": "header",
            "seq": 0,
            "timestamp": _utc_now_iso(),
        }
        self._write_line(self._redact_or_fallback(header))
        self._next_seq = 1
        self._initialized = True

    def _terminate_truncated_trailing_line(self) -> None:
        """Isolate a crash-truncated trailing line onto its own line.

        ``read_cursor`` correctly SKIPS a truncated/corrupt trailing line
        left by a crash mid-write, but the file on disk may not end in a
        newline in that case. Without this fix, the next ``_write_line``
        call (opened in append mode) would write its JSON object directly
        after the corrupt bytes with no separating newline, merging the new
        (well-formed) record onto the same physical line as the corrupt one
        -- making the newly-appended, otherwise-valid event ALSO unreadable
        by any future ``read_cursor``/line-based reader (128-S review
        remediation). Called once, at resume time, before any new line is
        appended.
        """

        with self.journal_path.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            if size == 0:
                return
            handle.seek(-1, 2)
            last_byte = handle.read(1)
        if last_byte != b"\n":
            with self.journal_path.open("a", encoding="utf-8") as handle:
                handle.write("\n")

    def _redact_or_fallback(self, record: Mapping[str, Any]) -> Mapping[str, Any]:
        redacted, warning = redact_record(dict(record), self._redactor)
        if redacted is not None:
            return redacted
        # Fail closed: never write the raw record. Preserve seq/timestamp
        # (both already-trusted, non-secret scalars) so the append-only,
        # monotonically increasing sequence stays intact.
        return {
            "seq": record.get("seq"),
            "timestamp": record.get("timestamp", _utc_now_iso()),
            "kind": "redaction_failed",
            "warning": warning or "redaction failed, record dropped",
        }

    def _write_line(self, record: Mapping[str, Any]) -> None:
        line = json.dumps(record, sort_keys=True)
        with self.journal_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def _append_record(self, payload: Mapping[str, Any]) -> int:
        self._ensure_initialized()
        seq = self._next_seq
        record = dict(payload)
        record["seq"] = seq
        record["timestamp"] = _utc_now_iso()
        self._write_line(self._redact_or_fallback(record))
        self._next_seq += 1
        return seq

    def append_event(self, event: Any) -> int:
        """Journal an already-constructed contracts.py event dataclass instance.

        Returns the assigned ``seq``. The event's ``kind`` (its class name)
        is recorded alongside its fields.
        """

        if not dataclasses.is_dataclass(event) or isinstance(event, type):
            raise TypeError(
                f"append_event() requires an already-constructed event dataclass instance, got {type(event)!r}"
            )
        payload = dataclasses.asdict(event)
        payload["kind"] = type(event).__name__
        return self._append_record(payload)

    def append_child_output_unavailable(self, reason: str) -> int:
        """F29 convenience: journal a ``ChildOutputUnavailable`` marker.

        Intended to be called at session start when the active
        :class:`~autoharness.supervise.process.ChildProcess` backend does
        not support output capture (``supports_output_capture`` is
        ``False``).
        """

        return self.append_event(ChildOutputUnavailable(reason=reason))

    def read_own_cursor(self) -> int:
        """Convenience: :func:`read_cursor` applied to this journal's own path."""

        return read_cursor(self.journal_path)

    def read_own_tail(self, limit: int = 50) -> list[dict[str, Any]]:
        """Read a strict, bounded tail for remote Observe consumers.

        ``read_cursor`` intentionally tolerates a crash-truncated final line
        for resume logic. Remote observation has a different contract: it
        must signal malformed or unavailable data explicitly rather than
        presenting a partial journal as authoritative.
        """

        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        if not self.journal_path.exists():
            raise FileNotFoundError(self.journal_path)

        records: deque[dict[str, Any]] = deque(maxlen=limit)
        with self.journal_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"journal line {line_number} is malformed JSON"
                    ) from exc
                if not isinstance(record, dict) or not isinstance(record.get("seq"), int):
                    raise ValueError(
                        f"journal line {line_number} is missing an integer seq"
                    )
                records.append(record)
        return list(records)
