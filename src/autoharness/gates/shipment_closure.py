"""Shipment-closure path classification for the P-015 flat-manifest exception.

This module implements the machine-checkable selector between the default
``safe_close`` path and the narrow ``cascade`` exception described by P-015.
The authoritative contract uses four set names:

* ``manifest_scope(S)`` — exactly ``items(S)``.
* ``closure_scope(S)`` — exactly ``items(S) ∪ {S}``.
* ``allowed_ids(S)`` — ``closure_scope(S) ∪ validated_linked_deliberations(S)``.
* ``required_ids(S)`` — the members of ``closure_scope(S)`` that were not
  already truly archived in the pre-close snapshot.

The descendant walk in this module is a BLAST-RADIUS containment check on the
cascade instrument, not a definition of closure scope. An out-of-manifest
artifact remains outside ``manifest_scope(S)``, ``closure_scope(S)``,
``allowed_ids(S)``, and ``required_ids(S)`` even when it is reachable from a
manifest feature via ``parent_id``.

INV-6 is therefore narrower than the superseded "fully covered" framing:
``cascade`` is permitted only when every out-of-manifest descendant reachable
from each manifest feature member is ENGINE-INERT. Engine inertness is granted
only when the record's own parsed frontmatter value satisfies
``isinstance(status, str) and status == "archived"``. No post-parse
normalization broadens that authorization: no ``.lower()``, no ``.strip()``, no
``.casefold()``, no alias table, and no ``str()`` coercion of non-string
values. ``"Archived"``, ``"ARCHIVED"``, the YAML-quoted literal
``status: " archived "``, missing ``status``, and non-string YAML parses such
as ``status: yes`` or a bare ``status:`` all fail closed.

Accepted YAML-equivalence limitation: the comparison happens after
``yaml.safe_load`` via ``autoharness.gates.topology._frontmatter``, so lexically
separate but YAML-equivalent values collapse to the same parsed scalar. An
unquoted ``status: archived   `` therefore parses to the canonical string
``"archived"`` and is treated as inert. That is correct, not a compromise,
because the backlog engine reads the same field through YAML parsing and agrees
on the parsed scalar even when the raw bytes differ.

Torn/duplicate identity also fails closed. The backlog-wide queue+archive scan
builds the descendant/status indexes in one pass, and any id that resolves to
more than one record anywhere in that scan invalidates cascade selection for the
whole manifest. A torn or duplicate out-of-manifest descendant is especially
important: its declared status is ambiguous, so it can never satisfy the exact
match inertness rule.

A symlinked backlog entry also fails closed, for both a manifest item
(``_read_artifact_record``) and any out-of-manifest descendant discovered by
the whole-backlog scan (``_scan_backlog``): a symlink can point outside the
backlog tree, so its declared frontmatter cannot be trusted for a
cascade/safe-close decision. Neither function follows a symlink to read its
target; both treat the symlink itself as a failure of classification.

This is a pure, read-only classification: it never mutates the backlog, never
calls out to ``backlogit``, and reuses
``autoharness.gates.topology._frontmatter`` for the repository's existing
fail-closed YAML-frontmatter parsing convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from glob import escape as _glob_escape
from pathlib import Path
from typing import Sequence

from autoharness.gates.topology import (
    _ARTIFACT_ID_PATTERN,
    BacklogUnavailableError,
    _frontmatter,
)

CANONICAL_INERT_STATUS = "archived"


class ClosePath(str, Enum):
    """The two possible shipment-closure operations P-015 governs."""

    SAFE_CLOSE = "safe_close"
    CASCADE = "cascade"


@dataclass(frozen=True)
class ClosePathDecision:
    """The result of :func:`classify_shipment_close_path`.

    ``qualifying_feature_ids`` is populated only when ``close_path`` is
    :attr:`ClosePath.CASCADE`; it lists every root feature member whose
    blast-radius containment check passed.
    """

    close_path: ClosePath
    reason: str
    qualifying_feature_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class _ArtifactRecord:
    """The minimal backlog fields this module needs for classification."""

    artifact_id: str
    artifact_type: str
    parent_id: str | None
    status: object | None


@dataclass(frozen=True)
class _BacklogScan:
    """Backlog-wide descendant/status indexes plus duplicate-id diagnostics."""

    children_index: dict[str, list[str]]
    status_index: dict[str, object | None]
    ambiguous_ids: tuple[str, ...] = field(default_factory=tuple)


def _normalize_id(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _is_engine_inert(status: object) -> bool:
    return isinstance(status, str) and status == CANONICAL_INERT_STATUS


def _format_status(status: object) -> str:
    return repr(status)


def _format_status_observations(
    artifact_ids: Sequence[str], status_index: dict[str, object | None]
) -> str:
    return ", ".join(
        f"{artifact_id} (status={_format_status(status_index.get(artifact_id))})"
        for artifact_id in artifact_ids
    )


def _read_artifact_record(backlog_dir: Path, artifact_id: str) -> _ArtifactRecord | None:
    """Read one backlog artifact's ``artifact_type``/``parent_id``/``status``."""

    if not _ARTIFACT_ID_PATTERN.match(artifact_id):
        raise BacklogUnavailableError(
            backlog_dir,
            f"manifest item id has an invalid or unsafe shape and cannot be resolved: "
            f"{artifact_id!r}",
        )

    matches: list[_ArtifactRecord] = []
    for folder in ("queue", "archive"):
        base = backlog_dir / folder
        if not base.exists():
            continue
        try:
            glob_candidates = sorted(base.glob(f"{_glob_escape(artifact_id)}.*"))
        except OSError as exc:
            raise BacklogUnavailableError(
                backlog_dir,
                f"could not scan {base} for manifest item {artifact_id!r}: {exc}",
            ) from exc
        for candidate in glob_candidates:
            if candidate.is_symlink():
                raise BacklogUnavailableError(
                    backlog_dir,
                    f"manifest item {artifact_id!r} resolved to a symlinked backlog "
                    f"entry ({candidate}); a symlink may escape the backlog tree and "
                    "cannot be trusted for classification",
                )
            if not candidate.is_file():
                continue
            fm = _frontmatter(candidate)
            fm_id = _normalize_id(fm.get("id"))
            if fm_id != artifact_id:
                continue
            artifact_type = str(fm.get("artifact_type") or "").strip().lower()
            raw_parent_id = fm.get("parent_id")
            parent_id = _normalize_id(raw_parent_id)
            if raw_parent_id is not None and parent_id is None:
                raise BacklogUnavailableError(
                    backlog_dir,
                    f"artifact {artifact_id!r} has a malformed parent_id field "
                    f"({raw_parent_id!r}) that cannot be safely normalized",
                )
            matches.append(
                _ArtifactRecord(
                    artifact_id=artifact_id,
                    artifact_type=artifact_type,
                    parent_id=parent_id,
                    status=fm.get("status"),
                )
            )

    if not matches:
        return None
    if len(matches) > 1:
        raise BacklogUnavailableError(
            backlog_dir,
            f"manifest item {artifact_id!r} resolved to {len(matches)} distinct backlog "
            "records across queue/archive; this ambiguous/torn state cannot safely be "
            "classified",
        )
    return matches[0]


def _scan_backlog(backlog_dir: Path) -> _BacklogScan | None:
    """Scan queue+archive once for descendant edges, status values, and ambiguity."""

    children_index: dict[str, list[str]] = {}
    status_index: dict[str, object | None] = {}
    ambiguous_ids: set[str] = set()

    for folder in ("queue", "archive"):
        base = backlog_dir / folder
        if not base.exists() or not base.is_dir():
            return None
        try:
            candidates = sorted(base.glob("*.md"))
        except OSError:
            return None
        for candidate in candidates:
            if candidate.is_symlink():
                return None
            try:
                fm = _frontmatter(candidate)
            except BacklogUnavailableError:
                return None
            raw_parent_id = fm.get("parent_id")
            parent_id = _normalize_id(raw_parent_id)
            if raw_parent_id is not None and parent_id is None:
                return None

            artifact_id = _normalize_id(fm.get("id"))
            if artifact_id is None:
                # A missing or non-string declared id cannot be trusted: falling
                # back to the filename stem would let a filename substitute for
                # declared identity, and a record here could then be silently
                # treated as an out-of-manifest descendant with a fabricated id
                # (e.g. one that happens to match a genuinely archived status).
                # Fail closed for the whole scan instead.
                return None
            if artifact_id in status_index:
                ambiguous_ids.add(artifact_id)
            else:
                status_index[artifact_id] = fm.get("status")

            if parent_id is None:
                continue
            children_index.setdefault(parent_id, []).append(artifact_id)

    for parent_id, child_ids in children_index.items():
        children_index[parent_id] = sorted(set(child_ids))

    return _BacklogScan(
        children_index=children_index,
        status_index=status_index,
        ambiguous_ids=tuple(sorted(ambiguous_ids)),
    )


def _enumerate_descendants(
    children_index: dict[str, list[str]], root_id: str
) -> tuple[str, ...]:
    """Return every backlog artifact id transitively descended from ``root_id``."""

    visited: set[str] = set()
    frontier = [root_id]
    while frontier:
        next_frontier: list[str] = []
        for node in frontier:
            for child_id in children_index.get(node, ()):
                if child_id not in visited:
                    visited.add(child_id)
                    next_frontier.append(child_id)
        frontier = next_frontier
    return tuple(sorted(visited))


def classify_shipment_close_path(
    manifest_items: Sequence[str],
    workspace_backlog_dir: Path | str,
) -> ClosePathDecision:
    """Classify whether the P-015 flat-manifest cascade exception applies.

    Any ambiguity, read failure, or containment-precondition violation for any
    feature member falls back to :attr:`ClosePath.SAFE_CLOSE` for the entire
    manifest. Qualification is never partial or per-member.
    """

    backlog_dir = Path(workspace_backlog_dir)
    raw_items = list(manifest_items)
    normalized = [_normalize_id(item) for item in raw_items]
    invalid = [raw for raw, norm in zip(raw_items, normalized) if norm is None]
    if invalid:
        return ClosePathDecision(
            close_path=ClosePath.SAFE_CLOSE,
            reason=f"manifest contains unnormalizable item(s): {invalid!r}",
        )
    manifest_ids = tuple(dict.fromkeys(normalized))
    if not manifest_ids:
        return ClosePathDecision(
            close_path=ClosePath.SAFE_CLOSE,
            reason="manifest declares no items; nothing to classify",
        )
    manifest_id_set = set(manifest_ids)

    records: dict[str, _ArtifactRecord] = {}
    try:
        for artifact_id in manifest_ids:
            record = _read_artifact_record(backlog_dir, artifact_id)
            if record is None:
                return ClosePathDecision(
                    close_path=ClosePath.SAFE_CLOSE,
                    reason=f"manifest item {artifact_id!r} could not be found in the backlog",
                )
            records[artifact_id] = record
    except BacklogUnavailableError as exc:
        return ClosePathDecision(
            close_path=ClosePath.SAFE_CLOSE,
            reason=f"a manifest item's backlog record is malformed: {exc}",
        )

    feature_members = [record for record in records.values() if record.artifact_type == "feature"]
    if not feature_members:
        return ClosePathDecision(
            close_path=ClosePath.SAFE_CLOSE,
            reason="manifest contains no feature member; the exception requires at least one",
        )

    scan = _scan_backlog(backlog_dir)
    if scan is None:
        return ClosePathDecision(
            close_path=ClosePath.SAFE_CLOSE,
            reason=(
                "descendant containment/childlessness could not be verified against the "
                "live workspace; falling back to safe-close"
            ),
        )

    ambiguous_id_set = set(scan.ambiguous_ids)
    qualifying_feature_ids: list[str] = []
    accounted_ids: set[str] = {feature.artifact_id for feature in feature_members}

    for feature in feature_members:
        if feature.parent_id is not None:
            return ClosePathDecision(
                close_path=ClosePath.SAFE_CLOSE,
                reason=(
                    f"feature member {feature.artifact_id!r} is not a root "
                    f"(parent_id={feature.parent_id!r})"
                ),
            )

        descendants = _enumerate_descendants(scan.children_index, feature.artifact_id)

        torn_out_of_manifest = tuple(
            descendant
            for descendant in descendants
            if descendant not in manifest_id_set and descendant in ambiguous_id_set
        )
        if torn_out_of_manifest:
            return ClosePathDecision(
                close_path=ClosePath.SAFE_CLOSE,
                reason=(
                    f"feature member {feature.artifact_id!r} has torn/ambiguous descendants "
                    f"outside the manifest that resolve to more than one record: "
                    f"{torn_out_of_manifest}"
                ),
            )

        out_of_manifest = tuple(
            descendant for descendant in descendants if descendant not in manifest_id_set
        )
        non_inert = tuple(
            descendant
            for descendant in out_of_manifest
            if not _is_engine_inert(scan.status_index.get(descendant))
        )
        if non_inert:
            return ClosePathDecision(
                close_path=ClosePath.SAFE_CLOSE,
                reason=(
                    f"feature member {feature.artifact_id!r} has out-of-manifest descendants "
                    f"that are not engine-inert: "
                    f"{_format_status_observations(non_inert, scan.status_index)}"
                ),
            )

        if not descendants:
            declared_as_parent_by = tuple(
                record.artifact_id
                for record in records.values()
                if record.parent_id == feature.artifact_id
            )
            if declared_as_parent_by:
                return ClosePathDecision(
                    close_path=ClosePath.SAFE_CLOSE,
                    reason=(
                        f"feature member {feature.artifact_id!r} has zero enumerated "
                        f"descendants but is declared as parent by manifest member(s) "
                        f"{declared_as_parent_by}"
                    ),
                )

        qualifying_feature_ids.append(feature.artifact_id)
        accounted_ids.update(descendants)

    if ambiguous_id_set:
        return ClosePathDecision(
            close_path=ClosePath.SAFE_CLOSE,
            reason=(
                "descendant containment/childlessness could not be fully verified because "
                f"these ids resolve to more than one record: {tuple(sorted(ambiguous_id_set))}"
            ),
        )

    extras = tuple(item_id for item_id in manifest_ids if item_id not in accounted_ids)
    if extras:
        return ClosePathDecision(
            close_path=ClosePath.SAFE_CLOSE,
            reason=(
                "manifest contains member(s) outside the qualifying root feature(s) "
                f"and their descendants: {extras}"
            ),
        )

    return ClosePathDecision(
        close_path=ClosePath.CASCADE,
        reason=(
            "every feature member is a root whose out-of-manifest descendants are "
            "engine-inert; cascade close is permitted"
        ),
        qualifying_feature_ids=tuple(qualifying_feature_ids),
    )
