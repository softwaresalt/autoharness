"""Shipment-closure path classification for the P-015 verified fully-covered-root exception.

This module implements the MACHINE-CHECKABLE precondition check described in
the "VERIFIED FULLY-COVERED-ROOT EXCEPTION" subsection of P-015
(``templates/policies/workflow-policies.md.tmpl``). It decides, given a
shipment manifest's declared item ids, whether the manifest is eligible for
the narrow cascade-close exception or whether the default single-artifact
safe-close prohibition still governs.

This is a pure, read-only classification: it never mutates the backlog and
never calls out to ``backlogit`` itself. It reuses
``autoharness.gates.topology._frontmatter`` for the identical fail-closed
YAML-frontmatter parsing convention already established there, rather than
re-deriving backlog-artifact parsing logic in a second place.

Design summary (mirrors the policy text precisely -- see P-015 for the
authoritative wording):

* The predicate is quantified over EVERY feature member of the manifest, not
  a single covering feature.
* Each feature member MUST be a ROOT (no ``parent_id``) AND MUST be FULLY
  COVERED (every one of its children -- enumerated by scanning the live
  backlog for records whose ``parent_id`` matches the feature -- is also a
  manifest member).
* Childlessness for a root feature member with zero children is POSITIVELY
  VERIFIED against the live workspace (enumerate children, assert the count
  is exactly zero) -- NEVER inferred from "no missing children found". A
  feature whose children cannot be enumerated (unreadable backlog directory,
  a malformed record encountered during the scan, etc.) is NOT verified
  childless, and the WHOLE manifest falls back to safe-close.
* A childless-root member must additionally be TERMINAL: it parents nothing
  (already implied by zero enumerated children), and no member also declares
  it as ``parent_id`` (a redundant safety net over the backlog-wide scan).
* The manifest MUST contain NOTHING beyond qualifying root feature members
  and their children. Any other manifest member (a non-root feature, or a
  task whose parent is not one of the qualifying root features) forces the
  whole manifest back to safe-close.
* If ANY feature member fails ANY precondition, the WHOLE MANIFEST falls back
  to the default safe-close prohibition -- qualification is never per-member.
* There is NO id-specific special case for any particular feature id
  anywhere in this module.
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


class ClosePath(str, Enum):
    """The two possible shipment-closure operations P-015 governs."""

    SAFE_CLOSE = "safe_close"
    CASCADE = "cascade"


@dataclass(frozen=True)
class ClosePathDecision:
    """The result of :func:`classify_shipment_close_path`.

    ``qualifying_feature_ids`` is populated only when ``close_path`` is
    :attr:`ClosePath.CASCADE`; it lists every root feature member whose
    full-coverage precondition was verified.
    """

    close_path: ClosePath
    reason: str
    qualifying_feature_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class _ArtifactRecord:
    """The minimal backlog fields this module needs: type and parent linkage."""

    artifact_id: str
    artifact_type: str
    parent_id: str | None


def _normalize_id(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _read_artifact_record(backlog_dir: Path, artifact_id: str) -> _ArtifactRecord | None:
    """Read one backlog artifact's ``artifact_type``/``parent_id`` from queue or archive.

    Returns ``None`` when the artifact cannot be found at all. Raises
    :class:`~autoharness.gates.topology.BacklogUnavailableError` when a
    candidate file is found but its frontmatter is malformed, or when the
    lookup itself is ambiguous -- callers convert that into a fail-closed
    safe-close decision rather than letting it propagate as an unhandled
    exception.

    Two hardening checks beyond a bare glob match:

    * ``artifact_id`` MUST match the same safe backlog-artifact-id shape
      enforced elsewhere (``gates.topology._ARTIFACT_ID_PATTERN``) before it
      is ever interpolated into a filesystem glob pattern. ``glob.escape``
      alone neutralizes ``*``/``?``/``[`` metacharacters but does NOT reject
      path separators or ``..`` segments, so an id shaped like
      ``"../../outside"`` could otherwise resolve a glob outside
      ``queue``/``archive`` entirely.
    * The broad ``id.*`` glob pattern matches by FILENAME PREFIX only, which
      could silently select a differently-named file (or, if both a queue
      and an archive copy exist for the same id, an arbitrary one of the
      two) without ever confirming the file's own frontmatter ``id`` field
      actually equals ``artifact_id``. Since a false match can authorize a
      destructive cascade close, every candidate across BOTH ``queue`` and
      ``archive`` is collected, each candidate's frontmatter ``id`` is
      verified to match, and more than one verified match is treated as an
      ambiguous/torn backlog state -- fail closed rather than silently
      preferring whichever location happened to be scanned first.
    """

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
        for candidate in sorted(base.glob(f"{_glob_escape(artifact_id)}.*")):
            if not candidate.is_file():
                continue
            fm = _frontmatter(candidate)
            fm_id = _normalize_id(fm.get("id"))
            if fm_id != artifact_id:
                # The record must DECLARE a normalized frontmatter id that
                # equals artifact_id. Never fall back to the filename stem
                # when the id field is missing/blank -- doing so would let a
                # malformed record with no declared id authorize the
                # destructive cascade path purely because its filename
                # happens to match.
                continue
            artifact_type = str(fm.get("artifact_type") or "").strip().lower()
            raw_parent_id = fm.get("parent_id")
            parent_id = _normalize_id(raw_parent_id)
            if raw_parent_id is not None and parent_id is None:
                # The frontmatter DECLARES a parent_id field, but it does not
                # normalize to a valid non-empty string (e.g. a bare YAML
                # integer, or a blank string). `_normalize_id` maps that to
                # the SAME `None` sentinel used for "no parent declared at
                # all" -- silently treating a malformed declared parent_id as
                # "this is a root" would let a non-root feature with a
                # corrupted field wrongly qualify for cascade close. Fail
                # closed instead of guessing.
                raise BacklogUnavailableError(
                    backlog_dir,
                    f"artifact {artifact_id!r} has a malformed parent_id field "
                    f"({raw_parent_id!r}) that cannot be safely normalized",
                )
            matches.append(
                _ArtifactRecord(
                    artifact_id=artifact_id, artifact_type=artifact_type, parent_id=parent_id
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


def _enumerate_children(backlog_dir: Path, feature_id: str) -> tuple[str, ...] | None:
    """Return every backlog artifact id whose ``parent_id`` is ``feature_id``.

    Returns ``None`` (rather than raising or returning an empty tuple) when
    the enumeration itself could not be trusted -- an unreadable backlog
    directory, or a malformed record encountered anywhere during the full
    queue+archive scan. Childlessness must be POSITIVELY VERIFIED; it must
    never be inferred from an enumeration that merely failed to find
    anything.
    """

    children: list[str] = []
    for folder in ("queue", "archive"):
        base = backlog_dir / folder
        if not base.exists() or not base.is_dir():
            # A missing/unreadable backlog directory can never positively
            # prove childlessness for any feature.
            return None
        try:
            candidates = sorted(base.glob("*.md"))
        except OSError:
            return None
        for candidate in candidates:
            try:
                fm = _frontmatter(candidate)
            except BacklogUnavailableError:
                return None
            raw_parent_id = fm.get("parent_id")
            parent_id = _normalize_id(raw_parent_id)
            if raw_parent_id is not None and parent_id is None:
                # A record declares a parent_id field that does not
                # normalize to a valid non-empty string. Silently treating
                # this the same as "no parent declared" could hide a
                # malformed-but-real child of `feature_id` from this
                # enumeration, letting a feature with actual children be
                # wrongly verified childless. Childlessness must be
                # POSITIVELY verified, so a record whose parentage cannot be
                # trusted makes the whole enumeration untrustworthy.
                return None
            if parent_id != feature_id:
                continue
            child_id = _normalize_id(fm.get("id")) or candidate.stem
            children.append(child_id)
    return tuple(sorted(set(children)))


def classify_shipment_close_path(
    manifest_items: Sequence[str],
    workspace_backlog_dir: Path | str,
) -> ClosePathDecision:
    """Classify whether the P-015 verified fully-covered-root exception applies.

    Parameters:
        manifest_items: the shipment manifest's ``custom_fields.items`` ids,
            in whatever order the manifest declares them.
        workspace_backlog_dir: path to the workspace's backlog directory
            (containing ``queue/`` and ``archive/`` subdirectories, e.g.
            ``.backlogit``).

    Returns a :class:`ClosePathDecision` naming the permitted close operation
    and the reason. Any ambiguity, read failure, or precondition violation
    for ANY feature member falls back to :attr:`ClosePath.SAFE_CLOSE` for the
    ENTIRE manifest -- this function never grants a partial/per-member
    exception.
    """

    backlog_dir = Path(workspace_backlog_dir)
    raw_items = list(manifest_items)
    normalized = [_normalize_id(item) for item in raw_items]
    invalid = [
        raw for raw, norm in zip(raw_items, normalized) if norm is None
    ]
    if invalid:
        # A manifest item that cannot be normalized (empty/blank, or not a
        # string at all) must never be silently dropped from consideration --
        # doing so could let an otherwise-disqualifying member vanish from
        # the "extras" check below and let the manifest wrongly qualify for
        # cascade. Reject the WHOLE manifest instead.
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
        # No feature member at all means this manifest is not shaped as the
        # fully-covered-root pattern (which requires the covering feature to
        # be listed FIRST in `items`) -- it falls back to whatever the
        # Durable Rule (task-only, per-item safe-close) already governs.
        return ClosePathDecision(
            close_path=ClosePath.SAFE_CLOSE,
            reason="manifest contains no feature member; the exception requires at least one",
        )

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

        children = _enumerate_children(backlog_dir, feature.artifact_id)
        if children is None:
            return ClosePathDecision(
                close_path=ClosePath.SAFE_CLOSE,
                reason=(
                    f"childlessness of feature member {feature.artifact_id!r} could not "
                    "be verified against the live workspace; falling back to safe-close"
                ),
            )

        missing = tuple(child for child in children if child not in manifest_id_set)
        if missing:
            return ClosePathDecision(
                close_path=ClosePath.SAFE_CLOSE,
                reason=(
                    f"feature member {feature.artifact_id!r} has children outside the "
                    f"manifest: {missing}"
                ),
            )

        if not children:
            # Verified-childless root: additionally require it be TERMINAL --
            # no manifest member declares it as parent either (a redundant
            # cross-check over the backlog-wide scan above, guarding against
            # a scan/manifest inconsistency).
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
                        f"children but is declared as parent by manifest member(s) "
                        f"{declared_as_parent_by}"
                    ),
                )

        qualifying_feature_ids.append(feature.artifact_id)
        accounted_ids.update(children)

    extras = tuple(item_id for item_id in manifest_ids if item_id not in accounted_ids)
    if extras:
        return ClosePathDecision(
            close_path=ClosePath.SAFE_CLOSE,
            reason=(
                "manifest contains member(s) outside the qualifying root feature(s) "
                f"and their children: {extras}"
            ),
        )

    return ClosePathDecision(
        close_path=ClosePath.CASCADE,
        reason="every feature member is a verified fully-covered root; cascade close is permitted",
        qualifying_feature_ids=tuple(qualifying_feature_ids),
    )
