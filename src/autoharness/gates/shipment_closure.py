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

    surface_problem = _validate_probe_surface(probe_surface, invocation_surface)
    if surface_problem is not None:
        return _unverified(surface_problem, **recorded)

    minor_line = (parsed.major, parsed.minor)
    if parsed.unreleased:
        return _unverified(
            f"unreleased build {version!r} (pre-release or build metadata present)",
            minor_line=minor_line,
            **recorded,
        )
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
