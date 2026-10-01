"""Shipment-closure path classification for the P-015 flat-manifest exception.

This module implements the machine-checkable selector between the default
``safe_close`` path and the narrow ``cascade`` exception described by P-015.
The authoritative contract uses four set names:

* ``manifest_scope(S)`` — exactly ``items(S)``.
* ``closure_scope(S)`` — exactly ``items(S) ∪ {S}``.
* ``allowed_ids(S)`` — ``closure_scope(S)`` (flat: backlogit 1.11.x
  ``shipment ship`` archive-candidate selection is the flat manifest plus the
  shipment record).
* ``required_ids(S)`` — ``{S} ∪ {qualifying feature members of S} ∪
  {x ∈ items(S) : x not truly archived pre-close}``. ``S`` and the qualifying
  feature members are required unconditionally, regardless of their own
  pre-close declared status; every other manifest item, over every
  ``artifact_type``, is required only when it was not already truly archived
  in the pre-close snapshot.

Linked deliberations are outside both sets under the verified 1.11.x engine
line: the engine leaves a linked deliberation independent unless its own ID is
an explicit manifest member (then it is an ordinary member of both sets). Their
fate is decided by the INV-12 linked-deliberation disposition step, planned
read-only by :func:`compute_linked_deliberation_disposition`.

Engine-semantics composition: :func:`assess_cascade_engine_semantics` decides
whether the probed backlogit build is on a verified minor line
(``VERIFIED_CASCADE_ENGINE_MINOR_LINES``), and :func:`select_close_path` is the
single executable composition point that combines that verdict with
:func:`classify_shipment_close_path` (``CASCADE`` only when both agree). The
runtime callers are the self-hosting shipment-reconcile Step 0(c) close-path
selection (plan unit U3a), the Linked-Deliberation Disposition step (plan unit
U5a), and the caller surface the 198-S evaluator re-plan adopts (Stage
follow-up). Until those land, these names have no runtime caller.

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
target; both treat the symlink itself as a failure of classification. This
check also covers a symlinked or (on Windows) junctioned *directory*
component -- ``backlog_dir`` itself, or its ``queue``/``archive``
subdirectory -- not only a symlinked leaf file: without it, a ``queue/``
symlink to an external directory containing crafted frontmatter could be
followed by the glob and used to authorize ``CASCADE`` from untrusted,
out-of-tree data.

This is a pure, read-only classification: it never mutates the backlog, never
calls out to ``backlogit``, and reuses
``autoharness.gates.topology._frontmatter`` for the repository's existing
fail-closed YAML-frontmatter parsing convention.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass, field
from enum import Enum
from glob import escape as _glob_escape
from pathlib import Path
from typing import Final, Literal, Sequence

from autoharness.gates.topology import (
    _ARTIFACT_ID_PATTERN,
    BacklogUnavailableError,
    _frontmatter,
)

_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)


def _is_symlink_or_reparse_point(path: Path) -> bool:
    """Return True when ``path`` itself (not a target it may point to) is a
    symlink or, on Windows, a directory-junction reparse point.

    ``Path.is_symlink()`` covers the POSIX symlink bit but does not
    reliably detect a Windows junction, which carries the reparse-point
    file attribute without necessarily setting ``S_ISLNK`` in ``lstat``.
    This mirrors the reparse-point detection already used by
    ``autoharness.gates.bootstrap_grant._is_reparse_point``: probe
    ``st_file_attributes`` (Windows-only) in addition to the POSIX
    symlink bit, and fail closed (treat an unreadable path as untrusted)
    rather than raising past the caller.
    """
    try:
        stat_result = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(stat_result.st_mode):
        return True
    if not _REPARSE_POINT_ATTRIBUTE:
        return False
    attributes = getattr(stat_result, "st_file_attributes", None)
    if attributes is None:
        return False
    return bool(attributes & _REPARSE_POINT_ATTRIBUTE)


def _directory_component_is_untrusted(*components: Path) -> bool:
    """Return True if any of ``components`` is itself a symlink/reparse point.

    Callers pass every directory component leading to a glob root (for
    example ``backlog_dir`` and ``backlog_dir / "queue"``) so a symlinked
    or junctioned intermediate directory -- not just a symlinked leaf file
    -- cannot redirect a scan to out-of-tree, untrusted frontmatter.
    """
    return any(_is_symlink_or_reparse_point(component) for component in components)

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

    ``out_of_manifest_descendant_ids`` is likewise populated only on
    :attr:`ClosePath.CASCADE`. It is the union, across every qualifying
    feature member, of the exact out-of-manifest ``parent_id`` descendant
    IDs this classification independently verified engine-inert (the
    INV-6 containment set). A ``CASCADE`` caller MUST baseline/fingerprint
    exactly this set before invocation and MUST NOT re-derive it by
    walking the backlog a second time -- the classifier's own read, at
    this snapshot, is the sole authoritative source for that set.
    """

    close_path: ClosePath
    reason: str
    qualifying_feature_ids: tuple[str, ...] = field(default_factory=tuple)
    out_of_manifest_descendant_ids: tuple[str, ...] = field(default_factory=tuple)


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
        if _directory_component_is_untrusted(backlog_dir, base):
            raise BacklogUnavailableError(
                backlog_dir,
                f"{base} (or {backlog_dir}) is a symlink/reparse-point directory "
                "component; a symlinked or junctioned backlog directory may escape "
                "the backlog tree and cannot be trusted for classification",
            )
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
            if _is_symlink_or_reparse_point(candidate):
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
        if _directory_component_is_untrusted(backlog_dir, base):
            return None
        if not base.exists() or not base.is_dir():
            return None
        try:
            candidates = sorted(base.glob("*.md"))
        except OSError:
            return None
        for candidate in candidates:
            if _is_symlink_or_reparse_point(candidate):
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
            if not _ARTIFACT_ID_PATTERN.match(artifact_id):
                # A malformed or unsafe-shaped declared id (e.g. containing path
                # separators or traversal segments such as "../invalid") must be
                # rejected exactly as manifest-item resolution already rejects it
                # in _read_artifact_record above. Without this check, a record
                # with such an id and an exact status: archived match could be
                # counted as an engine-inert out-of-manifest descendant and help
                # authorize the destructive CASCADE path from a malformed record
                # the P-015 contract requires to fail closed. Fail closed for the
                # whole scan rather than silently excluding just this record,
                # consistent with every other backlog-wide integrity violation
                # this function already treats as a whole-scan failure.
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
    out_of_manifest_descendant_ids: set[str] = set()
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
        out_of_manifest_descendant_ids.update(out_of_manifest)

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
        out_of_manifest_descendant_ids=tuple(sorted(out_of_manifest_descendant_ids)),
    )


# ---------------------------------------------------------------------------
# Engine-semantics gate (plan unit U1a)
# ---------------------------------------------------------------------------

# The single source of truth for the backlogit minor lines whose P-015 closure
# engine semantics this contract has verified. It covers BOTH engine
# propositions:
#
# 1. flat ``shipment ship`` archive-candidate selection leaves linked
#    deliberations and unlisted (out-of-manifest) descendants independent;
# 2. non-cascading ``archive_item`` changes exactly the named artifact. At
#    backlogit v1.11.0, ``internal/core/archive.go`` ``ArchiveItem`` (L103)
#    rewrites only the ``status``, ``archived_status`` and ``archived_from``
#    frontmatter keys (L234-255), plus the gitignored item event log and index.
#
# Adding a line is a contract change: re-verify both propositions against that
# engine line first. Module-local; intentionally not exported from
# ``autoharness.gates``.
VERIFIED_CASCADE_ENGINE_MINOR_LINES: Final[frozenset[tuple[int, int]]] = frozenset({(1, 11)})

_ENGINE_SEMANTICS_UNVERIFIED_PREFIX: Final = "ENGINE_SEMANTICS_UNVERIFIED:"
_PROBE_SURFACES: Final[frozenset[str]] = frozenset({"mcp", "cli"})
_RELEASE_VERSION_PATTERN: Final = (
    r"v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?"
)


class EngineSemanticsVerdict(str, Enum):
    """Whether the probed backlogit build is on a verified engine minor line."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class EngineSemanticsDecision:
    """The result of :func:`assess_cascade_engine_semantics`.

    ``probed_version``, ``probe_surface`` and ``probed_commit`` are recorded
    verbatim when the supplied value is an exact ``str`` and are ``None``
    otherwise. ``probed_commit`` is never interpreted here; the skill's
    pre-invocation re-probe compares it raw.
    """

    verdict: EngineSemanticsVerdict
    reason: str
    probed_version: str | None
    minor_line: tuple[int, int] | None
    probe_surface: str | None
    probed_commit: str | None


@dataclass(frozen=True)
class _ParsedReleaseVersion:
    major: int
    minor: int
    patch: int
    unreleased: bool


def _parse_release_version(value: str) -> _ParsedReleaseVersion | None:
    """Parse an exact-``str`` backlogit version, or return ``None``.

    Uses ``re.fullmatch`` (never ``match`` with ``$``, which accepts a trailing
    newline) with an ASCII-only digit class. There is no ``.strip()`` and no
    coercion. Any pre-release or build-metadata component (a Go
    pseudo-version, ``+dirty``, ``-rc1``) marks the build ``unreleased``.
    """

    match = re.fullmatch(_RELEASE_VERSION_PATTERN, value, flags=re.ASCII)
    if match is None:
        return None
    try:
        major, minor, patch = (int(match.group(index)) for index in (1, 2, 3))
    except ValueError:
        # int() refuses digit strings beyond the interpreter's conversion
        # limit; such a value is not a plausible release version.
        return None
    unreleased = match.group(4) is not None or match.group(5) is not None
    return _ParsedReleaseVersion(major=major, minor=minor, patch=patch, unreleased=unreleased)


def _exact_str_or_none(value: object) -> str | None:
    return value if type(value) is str else None


def _validate_probe_surface(probe_surface: object, invocation_surface: object) -> str | None:
    """Return an ``UNVERIFIED`` reason suffix, or ``None`` when the surfaces agree.

    Each surface must be exactly ``"mcp"`` or ``"cli"`` and the two must be
    equal: the MCP server and the CLI binary can be different builds, so a
    version probed on one surface says nothing about the other.
    """

    surfaces = (probe_surface, invocation_surface)
    if not all(type(surface) is str and surface in _PROBE_SURFACES for surface in surfaces):
        return (
            "unknown probe surface (probe_surface and invocation_surface must each be "
            "exactly 'mcp' or 'cli')"
        )
    if probe_surface != invocation_surface:
        return (
            f"probe surface mismatch (probed on {probe_surface!r}, invoked on "
            f"{invocation_surface!r})"
        )
    return None


def _unverified(
    detail: str,
    *,
    probed_version: str | None,
    probe_surface: str | None,
    probed_commit: str | None,
    minor_line: tuple[int, int] | None = None,
) -> EngineSemanticsDecision:
    return EngineSemanticsDecision(
        verdict=EngineSemanticsVerdict.UNVERIFIED,
        reason=f"{_ENGINE_SEMANTICS_UNVERIFIED_PREFIX} {detail}",
        probed_version=probed_version,
        minor_line=minor_line,
        probe_surface=probe_surface,
        probed_commit=probed_commit,
    )


def assess_cascade_engine_semantics(
    probed_version: object,
    *,
    probe_surface: object,
    invocation_surface: object,
    probed_commit: object = None,
) -> EngineSemanticsDecision:
    """Decide whether the probed backlogit build has verified P-015 engine semantics.

    ``VERIFIED`` only for a released build (no pre-release or build metadata)
    whose ``(major, minor)`` is in ``VERIFIED_CASCADE_ENGINE_MINOR_LINES``,
    probed and invoked on the same surface. Every ``UNVERIFIED`` reason starts
    with ``ENGINE_SEMANTICS_UNVERIFIED:``. Never raises.
    """

    try:
        return _assess_cascade_engine_semantics(
            probed_version, probe_surface, invocation_surface, probed_commit
        )
    except Exception:  # noqa: BLE001 - the gate must fail closed, never raise
        return _unverified(
            "engine-semantics assessment failed on unexpected input",
            probed_version=None,
            probe_surface=None,
            probed_commit=None,
        )


def _assess_cascade_engine_semantics(
    probed_version: object,
    probe_surface: object,
    invocation_surface: object,
    probed_commit: object,
) -> EngineSemanticsDecision:
    version = _exact_str_or_none(probed_version)
    recorded = {
        "probed_version": version,
        "probe_surface": _exact_str_or_none(probe_surface),
        "probed_commit": _exact_str_or_none(probed_commit),
    }
    if version is None:
        return _unverified(
            f"non-string probed version (got {type(probed_version).__name__})", **recorded
        )
    parsed = _parse_release_version(version)
    if parsed is None:
        return _unverified(f"unparseable probed version {version[:64]!r}", **recorded)

    minor_line = (parsed.major, parsed.minor)
    if parsed.unreleased:
        return _unverified(
            f"unreleased build {version!r} (pre-release or build metadata present)",
            minor_line=minor_line,
            **recorded,
        )
    surface_problem = _validate_probe_surface(probe_surface, invocation_surface)
    if surface_problem is not None:
        return _unverified(surface_problem, minor_line=minor_line, **recorded)
    if minor_line not in VERIFIED_CASCADE_ENGINE_MINOR_LINES:
        return _unverified(
            f"minor line {parsed.major}.{parsed.minor} not verified",
            minor_line=minor_line,
            **recorded,
        )
    return EngineSemanticsDecision(
        verdict=EngineSemanticsVerdict.VERIFIED,
        reason=(
            f"backlogit {version} ({recorded['probe_surface']}) is on verified engine "
            f"minor line {parsed.major}.{parsed.minor}"
        ),
        minor_line=minor_line,
        **recorded,
    )


_CLOSE_PATH_SELECTION_INVALID_INPUT: Final = "CLOSE_PATH_SELECTION_INVALID_INPUT"


def select_close_path(
    classifier: ClosePathDecision, engine: EngineSemanticsDecision
) -> tuple[ClosePath, str]:
    """Compose the classifier and engine verdicts into the close path to run.

    This is the single executable composition point for P-015 close-path
    selection. Truth table:

    ===================  ============  ==========================================
    classifier           engine        result
    ===================  ============  ==========================================
    ``CASCADE``          VERIFIED      ``CASCADE``
    ``CASCADE``          UNVERIFIED    ``SAFE_CLOSE`` with the engine's reason
    ``SAFE_CLOSE``       VERIFIED      ``SAFE_CLOSE`` with the classifier's reason
    ``SAFE_CLOSE``       UNVERIFIED    ``SAFE_CLOSE`` with the classifier's reason
    ===================  ============  ==========================================

    Any wrong-typed input returns ``SAFE_CLOSE`` with a reason starting
    ``CLOSE_PATH_SELECTION_INVALID_INPUT``. Never raises.
    """

    try:
        if (
            type(classifier) is not ClosePathDecision
            or type(engine) is not EngineSemanticsDecision
            or type(classifier.close_path) is not ClosePath
            or type(classifier.reason) is not str
            or type(engine.verdict) is not EngineSemanticsVerdict
            or type(engine.reason) is not str
        ):
            return (
                ClosePath.SAFE_CLOSE,
                f"{_CLOSE_PATH_SELECTION_INVALID_INPUT}: expected a ClosePathDecision "
                "and an EngineSemanticsDecision",
            )
        if classifier.close_path is not ClosePath.CASCADE:
            return ClosePath.SAFE_CLOSE, classifier.reason
        if engine.verdict is not EngineSemanticsVerdict.VERIFIED:
            return ClosePath.SAFE_CLOSE, engine.reason
        return ClosePath.CASCADE, f"{classifier.reason}; {engine.reason}"
    except Exception:  # noqa: BLE001 - selection must fail closed, never raise
        return (
            ClosePath.SAFE_CLOSE,
            f"{_CLOSE_PATH_SELECTION_INVALID_INPUT}: close-path selection failed",
        )


# ---------------------------------------------------------------------------
# Linked-deliberation disposition planner (plan unit U1b, INV-12)
# ---------------------------------------------------------------------------


class LinkedDeliberationOutcome(str, Enum):
    """The CLOSED set of outcomes INV-12 assigns to a disposition-set deliberation.

    Exactly eight values; adding one is a contract change. The planner's
    planned ``"archive"`` (:data:`PLANNED_ARCHIVE`) is the pre-mutation form of
    :attr:`ARCHIVED`, which only the disposition step assigns, after
    verify-after-each.
    """

    ARCHIVED = "archived"
    ALREADY_ARCHIVED = "already-archived"
    RETAINED_READ_ERROR = "retained_read_error"
    RETAINED_AMBIGUOUS = "retained_ambiguous"
    RETAINED_ENGINE_UNVERIFIED = "retained_engine_unverified"
    RETAINED_LIVE_STATUS = "retained_live_status"
    RETAINED_SHARED_REFERENCE = "retained_shared_reference"
    RETAINED_DESCRIPTION_MENTION = "retained_description_mention"


PLANNED_ARCHIVE: Final = "archive"

# Link kinds recorded per deliberation, in reporting order.
_LINK_KIND_SOURCE: Final = "source_deliberation_id"
_LINK_KIND_DESCRIPTION: Final = "description"
_LINK_KIND_REFERENCES: Final = "references"
_LINK_KIND_ORDER: Final = (_LINK_KIND_SOURCE, _LINK_KIND_DESCRIPTION, _LINK_KIND_REFERENCES)

# Read-error reason codes (extensible vocabulary: report consumers accept any
# reason_code, including unknown ones, and copy it verbatim).
READ_ERROR_PATH_ESCAPE: Final = "path_escape"
READ_ERROR_SYMLINK_OR_REPARSE_POINT: Final = "symlink_or_reparse_point"
READ_ERROR_UNREADABLE_FILE: Final = "unreadable_file"
READ_ERROR_MALFORMED_FRONTMATTER: Final = "malformed_frontmatter"
READ_ERROR_BODY_UNSEPARABLE: Final = "body_unseparable"
READ_ERROR_MALFORMED_STASH_ENTRY: Final = "malformed_stash_entry"

# unresolved_references reason codes (neither is a read error).
UNRESOLVED_INVALID_ID: Final = "invalid_id"
UNRESOLVED_NOT_FOUND: Final = "not_found"

_DELIBERATION_LINK_PATTERN: Final = re.compile(r"\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b")
# Mirrors the frontmatter delimiter pattern of topology._frontmatter so the body
# starts exactly where that parser's frontmatter block ends.
_FRONTMATTER_BLOCK_PATTERN: Final = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
_FRONTMATTER_OPENING_PATTERN: Final = re.compile(r"^---\s*\n")
# Deliberation statuses that are live under INV-12 (the deliberation vocabulary
# in .backlogit/header-def.yaml is queued|active|blocked|review|done|accepted|
# rejected|archived; deliberations have no in-progress status).
_LIVE_DELIBERATION_STATUSES: Final = frozenset({"active", "blocked", "review"})
_WORK_ITEM_TYPES: Final = frozenset({"feature", "task", "subtask", "bug", "chore"})


@dataclass(frozen=True)
class DeliberationRecordSnapshot:
    """One on-disk record of a disposition-set deliberation."""

    path: str
    declared_status: object | None
    sha256: str


@dataclass(frozen=True)
class LinkedDeliberationDisposition:
    """The planned outcome for one disposition-set deliberation.

    ``outcome`` is a :class:`LinkedDeliberationOutcome` or the planned
    ``"archive"``. ``reason_code`` is never empty and equals the outcome value
    for every outcome except ``retained_read_error``, which carries a read-error
    reason code plus ``path`` (workspace-relative with ``/`` separators, or as
    supplied when it resolves outside the workspace).
    """

    deliberation_id: str
    outcome: LinkedDeliberationOutcome | Literal["archive"]
    reason_code: str
    link_kinds: tuple[str, ...]
    linking_member_ids: tuple[str, ...]
    records: tuple[DeliberationRecordSnapshot, ...]
    declared_status: object | None
    referrer_ids: tuple[str, ...] = ()
    path: str | None = None


@dataclass(frozen=True)
class UnresolvedDeliberationReference:
    """A linked id that is not a disposition-set member (never a halt)."""

    id: str
    reason_code: str


@dataclass(frozen=True)
class DispositionReadFailure:
    """A record or folder the planner could not read (``reason_code`` + ``path``)."""

    path: str
    reason_code: str


@dataclass(frozen=True)
class LinkedDeliberationDispositionPlan:
    """The read-only result of :func:`compute_linked_deliberation_disposition`.

    ``read_failures`` lists every read failure of the scan, so a failure stays
    visible even when it prevents a deliberation from being discovered at all.
    ``planning_error`` is set only when the planner hit an unexpected internal
    failure or unusable input; the plan then carries no archive outcome, so
    every linked deliberation is retained.
    """

    shipment_id: str | None
    engine: object
    dispositions: tuple[LinkedDeliberationDisposition, ...]
    unresolved_references: tuple[UnresolvedDeliberationReference, ...]
    read_failures: tuple[DispositionReadFailure, ...] = ()
    planning_error: str | None = None


@dataclass(frozen=True)
class _RecordRead:
    """One backlog record, read exactly once (frontmatter, body and hash)."""

    rel_path: str
    artifact_id: str
    artifact_type: str
    status: object | None
    frontmatter: dict
    body: str
    sha256: str


@dataclass(frozen=True)
class _ReadFailure:
    rel_path: str
    reason_code: str


@dataclass(frozen=True)
class _RecordIndex:
    by_id: dict[str, list[_RecordRead]]
    failures: tuple[_ReadFailure, ...]


@dataclass(frozen=True)
class _StashEntry:
    """One active stash entry, reduced to the fields the referrer scan reads."""

    referrer_id: str
    deliberation_id: str | None
    text: object


@dataclass(frozen=True)
class _StashScan:
    entries: tuple[_StashEntry, ...] = ()
    failure: _ReadFailure | None = None


_STASH_FILENAME: Final = "stash.jsonl"


class _PreReadRecordText:
    """Path stand-in that hands ``topology._frontmatter`` already-read text.

    ``_frontmatter`` (the classifier's parser, H5) takes a path and calls
    ``path.read_text(encoding="utf-8")``. Passing this stand-in lets the
    frontmatter mapping, the Markdown body and the SHA-256 derive from ONE read
    of the record, with no window between reads. ``__fspath__`` keeps it usable
    as the real path should the parser ever open the file itself.
    """

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


def _workspace_relative(path: Path, workspace_root: Path) -> str:
    try:
        return path.relative_to(workspace_root).as_posix()
    except ValueError:
        return str(path)


def _is_within(child: Path, parent: Path) -> bool:
    """True when ``child`` is ``parent`` or lies under it (same-drive, case-normalized)."""

    child_text, parent_text = os.path.normcase(str(child)), os.path.normcase(str(parent))
    try:
        return os.path.commonpath([child_text, parent_text]) == parent_text
    except ValueError:  # different drives, or mixed absolute/relative
        return False


def _display_path(path: Path, workspace_root: Path) -> str:
    """Workspace-relative ``/`` path when ``path`` lies in the workspace, else as supplied."""

    absolute = Path(os.path.abspath(path))
    root = Path(os.path.abspath(workspace_root))
    if _is_within(absolute, root):
        return absolute.relative_to(root).as_posix()
    return str(path)


def _check_path_containment(path: Path, backlog_dir: Path) -> str | None:
    """Return the read-error reason code when ``path`` is unsafe to read, else ``None``.

    Constitution III input safety, shared by the stash path and every record
    path: ``path`` must lie inside the workspace backlog tree lexically (after
    ``..`` normalization, before anything is read) and canonically (after
    symlink resolution), and neither the backlog root nor any component from
    it down to ``path`` may be a symlink, junction or reparse point (checked
    with the classifier's :func:`_is_symlink_or_reparse_point`). The lexical
    check runs first, so a traversal is ``path_escape`` without touching the
    filesystem; a link inside the tree is ``symlink_or_reparse_point`` even
    when its target escapes. Never raises.
    """

    try:
        root = Path(os.path.abspath(backlog_dir))
        target = Path(os.path.abspath(path))
        if not _is_within(target, root):
            return READ_ERROR_PATH_ESCAPE
        components = [root]
        for part in target.relative_to(root).parts:
            components.append(components[-1] / part)
        if _directory_component_is_untrusted(*components):
            return READ_ERROR_SYMLINK_OR_REPARSE_POINT
        if not _is_within(Path(os.path.realpath(target)), Path(os.path.realpath(root))):
            return READ_ERROR_PATH_ESCAPE
    except (OSError, ValueError, RuntimeError):
        return READ_ERROR_UNREADABLE_FILE
    return None


def _read_record_body(text: str) -> str | None:
    """Return the Markdown description body after the closing frontmatter delimiter.

    ``text`` is the same (newline-normalized) text the frontmatter was parsed
    from. Returns ``None`` when the body cannot be separated.
    """

    match = _FRONTMATTER_BLOCK_PATTERN.match(text)
    return None if match is None else text[match.end():]


def _read_record(path: Path, workspace_root: Path) -> _RecordRead | _ReadFailure:
    """Read one ``*.md`` backlog entry once (frontmatter, body and hash)."""

    rel_path = _workspace_relative(path, workspace_root)
    if _is_symlink_or_reparse_point(path):
        return _ReadFailure(rel_path, READ_ERROR_SYMLINK_OR_REPARSE_POINT)
    # Stat once, directly: an entry that cannot be stat'ed (vanished mid-scan,
    # access denied) or is not a regular file must stay visible as a read
    # failure, never drop silently out of the live-referrer scan (fail closed).
    try:
        entry_mode = os.lstat(path).st_mode
    except OSError:
        return _ReadFailure(rel_path, READ_ERROR_UNREADABLE_FILE)
    if not stat.S_ISREG(entry_mode):
        return _ReadFailure(rel_path, READ_ERROR_UNREADABLE_FILE)
    try:
        raw = path.read_bytes()
        # Universal-newline translation, exactly as Path.read_text would do.
        text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except (OSError, UnicodeDecodeError):
        return _ReadFailure(rel_path, READ_ERROR_UNREADABLE_FILE)
    body = _read_record_body(text)
    if body is None:
        # An opening delimiter with no closing one: the Markdown description
        # body cannot be separated. No opening delimiter at all is missing
        # frontmatter (reported by the parser below).
        if _FRONTMATTER_OPENING_PATTERN.match(text):
            return _ReadFailure(rel_path, READ_ERROR_BODY_UNSEPARABLE)
    try:
        frontmatter = _frontmatter(_PreReadRecordText(path, text))  # type: ignore[arg-type]
    except (BacklogUnavailableError, ValueError, TypeError, RecursionError):
        # yaml.YAMLError arrives as BacklogUnavailableError; syntactically valid
        # YAML whose values cannot be constructed (e.g. an impossible date
        # raises ValueError) or that nests too deeply is equally malformed.
        return _ReadFailure(rel_path, READ_ERROR_MALFORMED_FRONTMATTER)
    if body is None:
        # Only reachable if topology._frontmatter's delimiter rule ever diverges
        # from _FRONTMATTER_BLOCK_PATTERN: fail closed rather than guess a body.
        return _ReadFailure(rel_path, READ_ERROR_MALFORMED_FRONTMATTER)
    artifact_id = _normalize_id(frontmatter.get("id"))
    if artifact_id is None or not _ARTIFACT_ID_PATTERN.match(artifact_id):
        # A record whose declared identity cannot be trusted could be a live
        # referrer we cannot name: fail closed (never plan an archive past it).
        return _ReadFailure(rel_path, READ_ERROR_MALFORMED_FRONTMATTER)
    return _RecordRead(
        rel_path=rel_path,
        artifact_id=artifact_id,
        artifact_type=str(frontmatter.get("artifact_type") or "").strip().lower(),
        status=frontmatter.get("status"),
        frontmatter=frontmatter,
        body=body,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def _read_record_safely(path: Path, backlog_dir: Path) -> _RecordRead | _ReadFailure:
    """Containment-check one record path, then read it once (never raises).

    Every record path passes the same :func:`_check_path_containment` checks
    as the stash path before any byte is read; a failure is a
    ``path_escape`` or ``symlink_or_reparse_point`` read failure for that path.
    """

    workspace_root = backlog_dir.parent
    containment = _check_path_containment(path, backlog_dir)
    if containment is not None:
        return _ReadFailure(_workspace_relative(path, workspace_root), containment)
    return _read_record(path, workspace_root)


def _index_backlog_records(backlog_dir: Path) -> _RecordIndex:
    """Read every queue-root and archive-root record once (read-only, H5).

    A folder that is missing, unlistable, or reached through a symlinked or
    junctioned directory component is itself a read failure (fail closed, like
    the classifier's ``_scan_backlog``); each folder is judged on its own, so a
    failure in one never hides the other.
    """

    workspace_root = backlog_dir.parent
    by_id: dict[str, list[_RecordRead]] = {}
    failures: list[_ReadFailure] = []
    for folder in ("queue", "archive"):
        base = backlog_dir / folder
        base_rel = _workspace_relative(base, workspace_root)
        if _directory_component_is_untrusted(backlog_dir, base):
            failures.append(_ReadFailure(base_rel, READ_ERROR_SYMLINK_OR_REPARSE_POINT))
            continue
        try:
            # Case-insensitive, so the planner never scans fewer records than
            # the classifier's glob("*.md") sees on a case-insensitive filesystem.
            candidates = sorted(
                entry for entry in base.iterdir() if entry.suffix.lower() == ".md"
            )
        except OSError:
            # Missing, not a directory, or not listable: never an empty scan.
            failures.append(_ReadFailure(base_rel, READ_ERROR_UNREADABLE_FILE))
            continue
        for candidate in candidates:
            result = _read_record_safely(candidate, backlog_dir)
            if isinstance(result, _ReadFailure):
                failures.append(result)
            else:
                by_id.setdefault(result.artifact_id, []).append(result)
    for records in by_id.values():
        records.sort(key=lambda record: record.rel_path)
    return _RecordIndex(
        by_id=by_id,
        failures=tuple(sorted(set(failures), key=lambda failure: failure.rel_path)),
    )


def _resolve_stash_path(backlog_dir: Path, stash_path: Path | str | None) -> Path:
    """Resolve the active stash file the live-referrer scan reads.

    ``None`` is the production default, ``<workspace_backlog_dir>/stash.jsonl``
    (the active stash at the resolved backlog root); it never means "do not
    scan stashes". An explicit ``stash_path`` overrides the default. The
    archived stash (``archive/stash.jsonl``) is never read.
    """

    return backlog_dir / _STASH_FILENAME if stash_path is None else Path(stash_path)


def _scan_stash_referrers(stash_file: Path, backlog_dir: Path) -> _StashScan:
    """Read the active stash entries once (read-only).

    The stash path (default or explicit) first passes
    :func:`_check_path_containment`; a failure is a read failure for the whole
    scan, reported with the stash path. A missing stash file means no active
    stash entries. Blank lines are skipped. Each entry is reduced to its
    referrer id (the entry ``id``, or ``<stash path>:<line>`` when it has
    none), its ``deliberation_id`` field and its ``text``.

    Fail closed, never raises: a stash path that is not a regular file, cannot
    be stat'ed or read, or is not valid UTF-8 is a read failure with reason
    code ``unreadable_file`` at the stash path. A non-blank line that fails
    JSON parsing or does not decode to a JSON object is a read failure with
    reason code ``malformed_stash_entry`` at the workspace-relative stash path.
    """

    workspace_root = backlog_dir.parent
    rel_path = _display_path(stash_file, workspace_root)
    containment = _check_path_containment(stash_file, backlog_dir)
    if containment is not None:
        return _StashScan(failure=_ReadFailure(rel_path, containment))
    try:
        stash_mode = os.lstat(stash_file).st_mode
    except FileNotFoundError:
        return _StashScan()
    except OSError:
        return _StashScan(failure=_ReadFailure(rel_path, READ_ERROR_UNREADABLE_FILE))
    if not stat.S_ISREG(stash_mode):
        return _StashScan(failure=_ReadFailure(rel_path, READ_ERROR_UNREADABLE_FILE))
    try:
        text = stash_file.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return _StashScan(failure=_ReadFailure(rel_path, READ_ERROR_UNREADABLE_FILE))
    entries: list[_StashEntry] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except (ValueError, RecursionError):
            entry = None
        if not isinstance(entry, dict):
            return _StashScan(
                failure=_ReadFailure(rel_path, READ_ERROR_MALFORMED_STASH_ENTRY)
            )
        entries.append(
            _StashEntry(
                referrer_id=_normalize_id(entry.get("id")) or f"{rel_path}:{line_number}",
                deliberation_id=_normalize_id(entry.get("deliberation_id")),
                text=entry.get("text"),
            )
        )
    return _StashScan(entries=tuple(entries))


def _stash_entry_links(entry: _StashEntry, deliberation_id: str) -> bool:
    """True when an active stash entry names ``deliberation_id`` (field or text)."""

    return entry.deliberation_id == deliberation_id or deliberation_id in _scan_link_ids(
        entry.text
    )


def _scan_link_ids(text: object) -> set[str]:
    """Return every deliberation-id-shaped token in ``text`` (non-str -> none)."""

    if type(text) is not str:
        return set()
    return set(_DELIBERATION_LINK_PATTERN.findall(text))


def _custom_fields(record: _RecordRead) -> dict:
    custom_fields = record.frontmatter.get("custom_fields")
    return custom_fields if isinstance(custom_fields, dict) else {}


def _record_links(record: _RecordRead) -> dict[str, set[str]]:
    """Map each linked id to the link kinds through which ``record`` links it."""

    links: dict[str, set[str]] = {}
    source_id = _normalize_id(_custom_fields(record).get("source_deliberation_id"))
    if source_id is not None:
        links.setdefault(source_id, set()).add(_LINK_KIND_SOURCE)
    for linked_id in _scan_link_ids(record.body):
        links.setdefault(linked_id, set()).add(_LINK_KIND_DESCRIPTION)
    references = record.frontmatter.get("references")
    if isinstance(references, list):
        for entry in references:
            for linked_id in _scan_link_ids(entry):
                links.setdefault(linked_id, set()).add(_LINK_KIND_REFERENCES)
    return links


def _closure_scope_ids(manifest_ids: Sequence[str], shipment_id: str | None) -> frozenset[str]:
    """``closure_scope(S) = items(S) ∪ {S}``."""

    scope = set(manifest_ids)
    if shipment_id is not None:
        scope.add(shipment_id)
    return frozenset(scope)


@dataclass
class _DispositionCandidate:
    deliberation_id: str
    records: list[_RecordRead]
    link_kinds: set[str] = field(default_factory=set)
    linking_member_ids: set[str] = field(default_factory=set)
    own_failures: tuple[_ReadFailure, ...] = ()


def _resolve_deliberation_records(
    index: _RecordIndex, deliberation_id: str
) -> list[_RecordRead] | None:
    """Return every record carrying ``deliberation_id`` when it is a deliberation.

    Existence is validated before location: the id must resolve to at least one
    record whose ``artifact_type`` is ``deliberation``; otherwise ``None``. All
    records carrying the id are returned so a torn id stays visible.
    """

    records = index.by_id.get(deliberation_id, [])
    if not any(record.artifact_type == "deliberation" for record in records):
        return None
    return list(records)


def _own_record_failures(
    index: _RecordIndex, deliberation_id: str, backlog_dir: Path
) -> tuple[_ReadFailure, ...]:
    """Read failures at the id's own record paths (``queue/`` or ``archive/<id>.md``).

    Called only after ``deliberation_id`` matched ``_ARTIFACT_ID_PATTERN``, so
    the expected paths are built from a validated id. The comparison is
    case-insensitive, like the index's ``.md`` suffix match.
    """

    workspace_root = backlog_dir.parent
    own_paths = {
        _workspace_relative(backlog_dir / folder / f"{deliberation_id}.md", workspace_root).casefold()
        for folder in ("queue", "archive")
    }
    return tuple(
        failure for failure in index.failures if failure.rel_path.casefold() in own_paths
    )


def _collect_disposition_set(
    index: _RecordIndex,
    manifest_ids: Sequence[str],
    closure_scope: frozenset[str],
    backlog_dir: Path,
) -> tuple[dict[str, _DispositionCandidate], dict[str, str]]:
    """Collect the disposition set and the unresolved references.

    The union, over EVERY explicit manifest member regardless of
    ``artifact_type``, of the literal ``custom_fields.source_deliberation_id``
    and the description-body and ``references`` matches, excluding the
    member's own id (self-reference) and every id in ``closure_scope(S)`` (H10:
    an explicit-member deliberation is governed by the flat allowed/required
    sets, never by the disposition step). Every candidate id must match
    ``_ARTIFACT_ID_PATTERN`` before any path is built from it (otherwise
    ``invalid_id``). Ids that do not resolve to a deliberation record are
    reported as unresolved (never a halt), unless a record at the id's own
    path could not be read: that id is a member, retained with its own read
    error (it may be a deliberation we cannot see). A member that cannot be
    found contributes no links; the fail-safe direction is retention, because
    an undiscovered deliberation is never archived.
    """

    candidates: dict[str, _DispositionCandidate] = {}
    unresolved: dict[str, str] = {}
    for member_id in manifest_ids:
        for member_record in index.by_id.get(member_id, []):
            for linked_id, kinds in _record_links(member_record).items():
                if linked_id == member_id or linked_id in closure_scope:
                    continue
                if not _ARTIFACT_ID_PATTERN.match(linked_id):
                    unresolved.setdefault(linked_id, UNRESOLVED_INVALID_ID)
                    continue
                candidate = candidates.get(linked_id)
                if candidate is None:
                    own_failures = _own_record_failures(index, linked_id, backlog_dir)
                    records = _resolve_deliberation_records(index, linked_id)
                    if records is None and not own_failures:
                        unresolved.setdefault(linked_id, UNRESOLVED_NOT_FOUND)
                        continue
                    candidate = _DispositionCandidate(
                        linked_id,
                        records if records is not None else list(index.by_id.get(linked_id, [])),
                        own_failures=own_failures,
                    )
                    candidates[linked_id] = candidate
                candidate.link_kinds.update(kinds)
                candidate.linking_member_ids.add(member_id)
    return candidates, unresolved


def _is_truly_archived(records: Sequence[_RecordRead]) -> bool:
    """H3: decided from the declared status (exact parsed scalar), never location.

    ``records`` are every record carrying one id. An id with more than one
    record has no trustworthy declared status, so it is never truly archived:
    a torn or duplicated referrer counts as live (fail closed to retain).
    """

    return len(records) == 1 and _is_engine_inert(records[0].status)


def _shipment_referrers(
    index: _RecordIndex, deliberation_id: str, shipment_id: str | None
) -> set[str]:
    """Shipments other than ``S``, not truly archived, that name the deliberation."""

    referrers: set[str] = set()
    for artifact_id, records in index.by_id.items():
        if artifact_id == shipment_id or _is_truly_archived(records):
            continue
        for record in records:
            if record.artifact_type != "shipment":
                continue
            custom_fields = _custom_fields(record)
            items = custom_fields.get("items")
            listed = isinstance(items, list) and any(
                _normalize_id(item) == deliberation_id for item in items
            )
            named = (
                deliberation_id in _scan_link_ids(record.body)
                or _normalize_id(custom_fields.get("source_deliberation_id")) == deliberation_id
            )
            if listed or named:
                referrers.add(artifact_id)
    return referrers


def _scan_live_referrers(
    index: _RecordIndex,
    stash: _StashScan,
    deliberation_id: str,
    closure_scope: frozenset[str],
    shipment_id: str | None,
) -> tuple[str, ...]:
    """Return the sorted live referrers of ``deliberation_id`` (bounded, read-only).

    Counted: work items outside ``closure_scope(S)`` that are not truly
    archived and link the deliberation through any link source, other
    shipments (see :func:`_shipment_referrers`), and active stash entries
    whose ``deliberation_id`` equals it or whose ``text`` matches it. Never
    counted: the deliberation itself, any other deliberation (so A<->B cycles
    never count), docs and plan files (never scanned), archived stash entries
    (never read), and truly archived records (H3: an
    ``archive/`` record declaring ``done`` is live, a ``queue/`` record
    declaring ``archived`` is not, and an id with more than one record is
    never truly archived, so any of its copies that links counts).
    """

    referrers = _shipment_referrers(index, deliberation_id, shipment_id)
    referrers.update(
        entry.referrer_id for entry in stash.entries if _stash_entry_links(entry, deliberation_id)
    )
    for artifact_id, records in index.by_id.items():
        if (
            artifact_id == deliberation_id
            or artifact_id in closure_scope
            or _is_truly_archived(records)
        ):
            continue
        for record in records:
            if record.artifact_type not in _WORK_ITEM_TYPES:
                continue
            if deliberation_id in _record_links(record):
                referrers.add(artifact_id)
    return tuple(sorted(referrers))


def _make_outcome_record(
    candidate: _DispositionCandidate,
    outcome: LinkedDeliberationOutcome | Literal["archive"],
    *,
    reason_code: str | None = None,
    path: str | None = None,
    referrer_ids: tuple[str, ...] = (),
) -> LinkedDeliberationDisposition:
    """Build a disposition record; ``reason_code`` defaults to the outcome value."""

    records = tuple(
        DeliberationRecordSnapshot(
            path=record.rel_path, declared_status=record.status, sha256=record.sha256
        )
        for record in candidate.records
    )
    return LinkedDeliberationDisposition(
        deliberation_id=candidate.deliberation_id,
        outcome=outcome,
        reason_code=reason_code or str(getattr(outcome, "value", outcome)),
        link_kinds=tuple(kind for kind in _LINK_KIND_ORDER if kind in candidate.link_kinds),
        linking_member_ids=tuple(sorted(candidate.linking_member_ids)),
        records=records,
        declared_status=candidate.records[0].status if len(candidate.records) == 1 else None,
        referrer_ids=referrer_ids,
        path=path,
    )


def _classify_outcome(
    candidate: _DispositionCandidate,
    *,
    index: _RecordIndex,
    stash: _StashScan,
    engine_verified: bool,
    closure_scope: frozenset[str],
    shipment_id: str | None,
) -> LinkedDeliberationDisposition:
    """Apply the INV-12 outcome precedence (first match wins).

    retained_read_error -> retained_ambiguous -> already-archived ->
    retained_engine_unverified -> retained_live_status ->
    retained_shared_reference -> retained_description_mention -> archive.
    """

    failure = (
        candidate.own_failures[0]
        if candidate.own_failures
        else stash.failure or (index.failures[0] if index.failures else None)
    )
    if failure is not None:
        # Rule 1, evaluated first: a read or containment failure on the
        # deliberation's own record(s) (attributed to that record's path), then
        # on any live-referrer input (the resolved stash file, or any record
        # the scan reads) fails closed to retain.
        return _make_outcome_record(
            candidate,
            LinkedDeliberationOutcome.RETAINED_READ_ERROR,
            reason_code=failure.reason_code,
            path=failure.rel_path,
        )
    if len(candidate.records) > 1:
        return _make_outcome_record(candidate, LinkedDeliberationOutcome.RETAINED_AMBIGUOUS)
    status = candidate.records[0].status
    if _is_engine_inert(status):
        return _make_outcome_record(candidate, LinkedDeliberationOutcome.ALREADY_ARCHIVED)
    if not engine_verified:
        return _make_outcome_record(
            candidate, LinkedDeliberationOutcome.RETAINED_ENGINE_UNVERIFIED
        )
    if isinstance(status, str) and status in _LIVE_DELIBERATION_STATUSES:
        return _make_outcome_record(candidate, LinkedDeliberationOutcome.RETAINED_LIVE_STATUS)
    referrers = _scan_live_referrers(
        index, stash, candidate.deliberation_id, closure_scope, shipment_id
    )
    if referrers:
        return _make_outcome_record(
            candidate,
            LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE,
            referrer_ids=referrers,
        )
    if _LINK_KIND_SOURCE not in candidate.link_kinds:
        return _make_outcome_record(
            candidate, LinkedDeliberationOutcome.RETAINED_DESCRIPTION_MENTION
        )
    return _make_outcome_record(candidate, PLANNED_ARCHIVE)


def compute_linked_deliberation_disposition(
    manifest_items: Sequence[str],
    shipment_id: str,
    workspace_backlog_dir: Path | str,
    *,
    engine: EngineSemanticsDecision,
    stash_path: Path | str | None = None,
) -> LinkedDeliberationDispositionPlan:
    """Plan the INV-12 disposition of the shipment's linked deliberations.

    Pure and read-only: it reads queue-root and archive-root records once with
    the classifier's parser (``autoharness.gates.topology._frontmatter``, H5),
    never mutates the backlog, never calls ``backlogit``, and never raises.
    Each disposition-set deliberation gets exactly one planned outcome; an
    engine that is not VERIFIED (or not an :class:`EngineSemanticsDecision`)
    retains every non-archived deliberation.

    Scope note (195-F slice 2, 197-F): slice 2 closes plan unit U1b. The
    fail-closed read path, stash referrers and the ``stash_path`` default
    (``<workspace_backlog_dir>/stash.jsonl``), path containment
    (``path_escape``), per-deliberation read-error attribution, the H3
    multi-record referrer rule and the final INV-12 outcome precedence are in
    place. This planner still has no runtime caller and must not drive any
    mutation until a later slice wires it into the close path.
    """

    normalized_shipment_id: str | None = None
    try:
        if isinstance(manifest_items, (str, bytes)):
            raise TypeError("manifest_items must be a sequence of ids, not a single string")
        normalized_shipment_id = _normalize_id(shipment_id)
        backlog_dir = Path(workspace_backlog_dir)
        normalized_items = [_normalize_id(item) for item in manifest_items]
        if any(
            item_id is None or not _ARTIFACT_ID_PATTERN.match(item_id)
            for item_id in normalized_items
        ):
            # Like topology's manifest validation: never plan a partial scope.
            raise ValueError("manifest_items contains an invalid or unsafe member id")
        manifest_ids = tuple(dict.fromkeys(normalized_items))
        closure_scope = _closure_scope_ids(manifest_ids, normalized_shipment_id)
        engine_verified = (
            type(engine) is EngineSemanticsDecision
            and engine.verdict is EngineSemanticsVerdict.VERIFIED
        )
        index = _index_backlog_records(backlog_dir)
        stash = _scan_stash_referrers(_resolve_stash_path(backlog_dir, stash_path), backlog_dir)
        read_failures = tuple(
            DispositionReadFailure(path=failure.rel_path, reason_code=failure.reason_code)
            for failure in (*index.failures, *((stash.failure,) if stash.failure else ()))
        )
        # A torn/duplicate manifest member cannot be traversed safely (a stale
        # copy could contribute links the live copy dropped): fail closed.
        torn_members = sorted(
            member_id for member_id in manifest_ids if len(index.by_id.get(member_id, ())) > 1
        )
        if torn_members:
            return LinkedDeliberationDispositionPlan(
                shipment_id=normalized_shipment_id,
                engine=engine,
                dispositions=(),
                unresolved_references=(),
                read_failures=read_failures,
                planning_error=(
                    "linked-deliberation planning failed: manifest members resolve to "
                    f"multiple records (torn/duplicate identity): {', '.join(torn_members)}"
                ),
            )
        candidates, unresolved = _collect_disposition_set(
            index, manifest_ids, closure_scope, backlog_dir
        )
        dispositions = tuple(
            _classify_outcome(
                candidates[deliberation_id],
                index=index,
                stash=stash,
                engine_verified=engine_verified,
                closure_scope=closure_scope,
                shipment_id=normalized_shipment_id,
            )
            for deliberation_id in sorted(candidates)
        )
        return LinkedDeliberationDispositionPlan(
            shipment_id=normalized_shipment_id,
            engine=engine,
            dispositions=dispositions,
            unresolved_references=tuple(
                UnresolvedDeliberationReference(id=ref_id, reason_code=reason_code)
                for ref_id, reason_code in sorted(unresolved.items())
            ),
            read_failures=read_failures,
        )
    except Exception as exc:  # noqa: BLE001 - the planner must fail closed, never raise
        return LinkedDeliberationDispositionPlan(
            shipment_id=normalized_shipment_id,
            engine=engine,
            dispositions=(),
            unresolved_references=(),
            planning_error=f"linked-deliberation planning failed: {type(exc).__name__}",
        )
