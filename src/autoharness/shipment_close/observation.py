"""Safe-close observation set for ``cascade-close`` (192-F, plan unit A2b).

:func:`compute_observation_set` computes the path-keyed safe-close
observation set that A2 records for a selected SAFE_CLOSE and that the A4b
gate re-checks. It is read-only. The set is the union of:

* the shipment-reconcile ``mode: safe-close`` observation set: the covering
  (parent) feature of each manifest member plus every unshipped sibling;
* every out-of-manifest descendant of each manifest member (the classifier's
  traversal, ``_scan_backlog`` / ``_enumerate_descendants``);
* the UNVERIFIED-engine ``deliberation_records`` A2 copies from the
  disposition snapshot (re-plan cycle-2 C2-1).

Every ID in ``closure_scope(S) = items(S) ∪ {S}`` and every ID in
``excluded_ids`` is removed from the traversal entries (re-plan cycle-1 R2,
R11).

Ancestor walk (conservative gap-fill): the skill derives "the covering
feature" from the manifest hierarchy. This module walks each member's
``parent_id`` chain to its top-most ancestor, observes every ancestor, and
observes every descendant of that root. For the usual task -> feature
hierarchy that is exactly the covering feature plus its unshipped siblings;
deeper hierarchies are watched in full rather than guessed.

Per-ID resolution (re-plan cycle-2 C2-2): an expected ID with no record is
recorded as ``location: missing`` and never raises; a torn ID, an unreadable
scan, or a record that cannot be fingerprinted raises
:class:`~autoharness.gates.cascade_evidence.CascadeEvidenceError`.

Private-name rule (re-plan cycle-2 C2-4): the ``shipment_closure`` private
helpers, and the classifier's frontmatter parser ``topology._frontmatter``,
are imported lazily inside the functions that use them, never at module top
level.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from glob import escape as glob_escape
from pathlib import Path
from typing import Final

from autoharness.gates.cascade_evidence import (
    DECLARED_STATUS_MISSING,
    CascadeEvidenceError,
    ObservationEntry,
    observation_entry_to_record,
)
from autoharness.gates.shipment_closure import DeliberationRecordSnapshot

__all__ = ["LocatedRecord", "compute_observation_set", "locate_record"]

_FOLDERS: Final = ("queue", "archive")
_MAX_ANCESTOR_DEPTH: Final = 64


@dataclass(frozen=True)
class LocatedRecord:
    """One backlog record, read once: its location, hash, and declared fields."""

    id: str
    path: str  # workspace-relative POSIX path, first segment the backlog root
    location: str  # queue | archive
    sha256: str
    artifact_type: object
    parent_id: str | None
    declared_status: object  # DECLARED_STATUS_MISSING when the key is absent
    frontmatter: dict


class _PreReadText:
    """Hands already-read text to ``topology._frontmatter`` (one read per record)."""

    __slots__ = ("_path", "_text")

    def __init__(self, path: Path, text: str) -> None:
        self._path = path
        self._text = text

    def read_text(self, encoding: str | None = None, errors: str | None = None) -> str:
        return self._text

    def __fspath__(self) -> str:
        return os.fspath(self._path)

    def __str__(self) -> str:
        return str(self._path)


def _normalize(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _relative_path(candidate: Path, backlog_dir: Path) -> str:
    root = Path(os.path.abspath(backlog_dir))
    target = Path(os.path.abspath(candidate))
    return (Path(root.name) / target.relative_to(root)).as_posix()


def locate_record(backlog_dir: Path | str, artifact_id: str) -> LocatedRecord | None:
    """Locate and fingerprint one record by ID in ``queue/`` and ``archive/``.

    Identity is first resolved with ``shipment_closure._read_artifact_record``
    (frontmatter ``id`` match, torn detection). No match returns ``None``.
    The matching file is then read **once**: its SHA-256 and its frontmatter
    come from the same bytes. A torn ID, an unsafe or unreadable candidate, a
    path-containment failure, or a match that cannot be re-established
    raises :class:`CascadeEvidenceError`.
    """

    from autoharness.gates.shipment_closure import _check_path_containment, _read_artifact_record
    from autoharness.gates.topology import BacklogUnavailableError, _frontmatter

    backlog = Path(backlog_dir)
    try:
        resolved = _read_artifact_record(backlog, artifact_id)
    except BacklogUnavailableError as exc:
        raise CascadeEvidenceError(f"record {artifact_id!r} cannot be resolved: {exc}") from exc
    if resolved is None:
        return None

    matches: list[LocatedRecord] = []
    for folder in _FOLDERS:
        base = backlog / folder
        if not base.is_dir():
            continue
        try:
            candidates = sorted(base.glob(f"{glob_escape(artifact_id)}.*"))
        except OSError as exc:
            raise CascadeEvidenceError(f"cannot scan {base} for {artifact_id!r}: {exc}") from exc
        for candidate in candidates:
            containment = _check_path_containment(candidate, backlog)
            if containment is not None:
                raise CascadeEvidenceError(f"record {artifact_id!r} candidate {candidate} fails containment: {containment}")
            if not candidate.is_file():
                continue
            try:
                raw = candidate.read_bytes()
                text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
                frontmatter = _frontmatter(_PreReadText(candidate, text))  # type: ignore[arg-type]
            except (OSError, UnicodeDecodeError, BacklogUnavailableError, ValueError, TypeError, RecursionError) as exc:
                raise CascadeEvidenceError(f"record {artifact_id!r} cannot be fingerprinted ({candidate}): {exc}") from exc
            if _normalize(frontmatter.get("id")) != artifact_id:
                continue
            raw_parent = frontmatter.get("parent_id")
            parent_id = _normalize(raw_parent)
            if raw_parent is not None and parent_id is None:
                raise CascadeEvidenceError(f"record {artifact_id!r} has a malformed parent_id {raw_parent!r}")
            matches.append(
                LocatedRecord(
                    id=artifact_id,
                    path=_relative_path(candidate, backlog),
                    location=folder,
                    sha256=hashlib.sha256(raw).hexdigest(),
                    artifact_type=frontmatter.get("artifact_type"),
                    parent_id=parent_id,
                    declared_status=frontmatter["status"] if "status" in frontmatter else DECLARED_STATUS_MISSING,
                    frontmatter=frontmatter,
                )
            )
    if len(matches) != 1:
        raise CascadeEvidenceError(
            f"record {artifact_id!r} cannot be read consistently ({len(matches)} matching file(s) at fingerprint time)"
        )
    return matches[0]


def _entry_for(backlog: Path, artifact_id: str) -> ObservationEntry:
    located = locate_record(backlog, artifact_id)
    if located is None:
        return ObservationEntry(id=artifact_id, path=None, location="missing", sha256=None, declared_status=None)
    return ObservationEntry(
        id=artifact_id,
        path=located.path,
        location=located.location,
        sha256=located.sha256,
        declared_status=located.declared_status,
    )


def _deliberation_entry(deliberation_id: str, snapshot: DeliberationRecordSnapshot) -> ObservationEntry:
    if type(snapshot) is not DeliberationRecordSnapshot or type(snapshot.path) is not str:
        raise CascadeEvidenceError(f"deliberation {deliberation_id!r}: expected a DeliberationRecordSnapshot")
    segments = snapshot.path.split("/")
    if len(segments) < 3 or segments[1] not in _FOLDERS:
        raise CascadeEvidenceError(
            f"deliberation {deliberation_id!r} record path {snapshot.path!r} is not under queue/ or archive/"
        )
    return ObservationEntry(
        id=deliberation_id,
        path=snapshot.path,
        location=segments[1],
        sha256=snapshot.sha256,
        declared_status=snapshot.declared_status,
    )


def compute_observation_set(
    manifest_items: Sequence[str],
    shipment_id: str,
    backlog_dir: Path | str,
    *,
    excluded_ids: Iterable[str],
    deliberation_records: Iterable[tuple[str, DeliberationRecordSnapshot]] = (),
) -> tuple[ObservationEntry, ...]:
    """Return the safe-close observation set, one entry per record path, sorted by ``(id, path)``.

    Read-only. Raises :class:`CascadeEvidenceError` on a ``None`` traversal
    scan, a torn ID, a ``BacklogUnavailableError``, or a record that cannot
    be fingerprinted. Every entry is checked with the A1d
    ``observation_entry_to_record`` encoder before it is returned.
    """

    from autoharness.gates.shipment_closure import _enumerate_descendants, _read_artifact_record, _scan_backlog
    from autoharness.gates.topology import BacklogUnavailableError

    if isinstance(manifest_items, (str, bytes)):
        raise CascadeEvidenceError("manifest_items must be a sequence of IDs, not a single string")
    backlog = Path(backlog_dir)
    manifest_ids = tuple(dict.fromkeys(manifest_items))
    closure_scope = frozenset(manifest_ids) | {shipment_id}
    excluded = frozenset(excluded_ids)

    try:
        scan = _scan_backlog(backlog)
    except BacklogUnavailableError as exc:  # pragma: no cover - _scan_backlog returns None instead
        raise CascadeEvidenceError(f"the backlog traversal scan failed: {exc}") from exc
    if scan is None:
        raise CascadeEvidenceError("the backlog traversal scan could not be established (fail closed)")

    expected: set[str] = set()
    try:
        for member_id in manifest_ids:
            record = _read_artifact_record(backlog, member_id)
            if record is None:
                continue
            root = member_id
            parent_id = record.parent_id
            seen = {member_id}
            for _ in range(_MAX_ANCESTOR_DEPTH):
                if parent_id is None or parent_id in seen:
                    break
                seen.add(parent_id)
                expected.add(parent_id)
                parent = _read_artifact_record(backlog, parent_id)
                if parent is None:
                    root = None
                    expected.update(_enumerate_descendants(scan.children_index, parent_id))
                    break
                root = parent_id
                parent_id = parent.parent_id
            else:
                raise CascadeEvidenceError(f"the parent_id chain of {member_id!r} is too deep (fail closed)")
            if root is not None:
                expected.update(_enumerate_descendants(scan.children_index, root))
            expected.update(_enumerate_descendants(scan.children_index, member_id))
    except BacklogUnavailableError as exc:
        raise CascadeEvidenceError(f"an observation-set member cannot be resolved: {exc}") from exc

    expected -= closure_scope
    expected -= excluded
    torn = sorted(expected & set(scan.ambiguous_ids))
    if torn:
        raise CascadeEvidenceError(f"observation-set member(s) resolve to more than one record: {torn}")

    entries = [_entry_for(backlog, artifact_id) for artifact_id in sorted(expected)]
    entries.extend(_deliberation_entry(deliberation_id, snapshot) for deliberation_id, snapshot in deliberation_records)
    keys = [(entry.id, entry.path) for entry in entries]
    if len(set(keys)) != len(keys):
        raise CascadeEvidenceError("the observation set holds a duplicate (id, path) entry")
    for entry in entries:
        observation_entry_to_record(entry)
    return tuple(sorted(entries, key=lambda entry: (entry.id, entry.path or "")))
