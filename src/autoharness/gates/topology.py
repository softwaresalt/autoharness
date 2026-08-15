"""Deterministic shipment/worktree topology gate.

This module hosts the read-only, fail-closed topology checks that guard shipment
claim, lifecycle, and ambient hook/CI execution. The core invariant work is kept
inside ``autoharness.gates`` so it can evolve independently of install/tune
surfaces.

Local limitation: the active-shipment scan and detect-before consistency scan can
only observe the current checkout. They are deliberately detect-before guards, not
serialization, leases, or cross-machine locks. backlogit provides no workspace-
wide claim lock, so concurrent work in another checkout can still race this gate.
Likewise, a local hook skipped with ``git --no-verify`` executes no gate code and
emits no topology telemetry by design; CI is the independent backstop.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from autoharness.backlog_root import BacklogUnavailableError, resolve_backlog_root

VALID_MODES = ("agent", "manual", "ci")
VALID_PHASES = ("pre_claim", "post_claim", "lifecycle", "ambient")
SCOPED_PHASES = ("pre_claim", "post_claim", "lifecycle")
_NOT_YET_CLAIMED_STATUSES = frozenset({"queued", "blocked"})
_TASK_ACTIVE_OR_DONE = frozenset({"active", "done"})
_VALID_LIVE_SHIPMENT_STATUSES = frozenset({"queued", "active", "shipped", "abandoned"})
# backlogit's documented task/feature lifecycle enum (broader than the
# shipment enum above -- tasks/features also support blocked/review/
# accepted/rejected/archived as live states).
_VALID_LIVE_ARTIFACT_STATUSES = frozenset(
    {"queued", "active", "blocked", "review", "done", "accepted", "rejected", "archived"}
)
# backlogit shipment artifact filenames/ids are always digits followed by
# "-S" (e.g. "114-S.md"). A file whose id/filename matches this shape but
# whose artifact_type is missing/misspelled/wrong is a shipment-shaped
# record with a corrupted type declaration, not a legitimately-different
# artifact -- it must fail closed rather than being silently skipped from
# the shipment scan.
_SHIPMENT_ID_PATTERN = re.compile(r"^\d+-S$")
# backlogit artifact ids are always digits (optionally dot-separated for
# sub-numbered tasks, e.g. "109.001") followed by a hyphen and an uppercase
# type suffix (e.g. "114-S", "109-F", "109.001-T"). This is the full set of
# characters an id may legitimately contain -- no path separators, "..", or
# glob metacharacters. Any artifact id (e.g. a manifest item id read from
# shipment frontmatter) must match this shape before it is safely
# interpolated into a filesystem glob pattern; a malformed id containing
# "..", an absolute path, or glob metacharacters must fail closed rather
# than traverse outside the backlog directory or raise an unhandled
# path-pattern exception.
_ARTIFACT_ID_PATTERN = re.compile(r"^\d+(?:\.\d+)*-[A-Z]+$")
_BRANCH_KIND_PREFIXES = ("feat/", "chore/")
# Post-merge closure branches (`post-merge/{feature_slug}`, created per the
# Ship agent's Post-Merge Branch Protocol) are named after the covering
# FEATURE, not the shipment being closed -- shipment branch-alias matching
# (`_branch_aliases`/`_resolve_shipment_from_branch`) has no feature-level
# data to match against. Because this branch is only ever created by Ship,
# exclusively for the bounded post-merge closure window of a shipment that
# just merged, treat it as ownership-eligible unconditionally (like the
# default branch) rather than requiring an exact shipment-branch match the
# gate cannot currently compute. The still-fully-enforced active-shipment
# invariant check (a separate check) continues to guard that at most one
# shipment is active and, for post_claim/lifecycle, that it matches target.
_POST_MERGE_BRANCH_PREFIX = "post-merge/"
_POST_CLAIM_WRAP_TOKENS = frozenset({
    "SHIPMENT_STATE_INCONSISTENT",
    "LIFECYCLE_NO_ACTIVE_SHIPMENT",
    "LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS",
    "LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH",
})


@dataclass(frozen=True)
class TopologyInput:
    mode: str
    phase: str | None
    target_shipment_id: str | None
    emit_json: bool = False
    force: bool = False


@dataclass(frozen=True)
class ShipmentState:
    shipment_id: str
    title: str = ""
    live_status: str | None = None
    archived_status: str | None = None
    archived_record_present: bool = False
    manifest_item_ids: tuple[str, ...] = ()
    blocking_predecessor_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArtifactState:
    artifact_id: str
    artifact_type: str = ""
    live_status: str | None = None
    archived_status: str | None = None

    @property
    def effective_status(self) -> str | None:
        return self.live_status or self.archived_status


class TopologyReaders(Protocol):
    def list_shipments(self) -> Sequence[ShipmentState]: ...

    def read_artifact(self, artifact_id: str) -> ArtifactState | None: ...

    def current_branch(self) -> str: ...

    def default_branch(self) -> str: ...

    def worktree_porcelain(self) -> str: ...

    def read_worktree_marker(self, worktree_path: str) -> str | None: ...

    def closure_complete(self, shipment_id: str) -> bool | None: ...


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    token: str | None = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "token": self.token,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True)
class TopologyResult:
    mode: str
    phase: str
    resolved_target_shipment_id: str | None
    checks: tuple[CheckResult, ...] = ()
    exit_code: int = 0
    message: str = "topology gate pass"
    forced: bool = False

    @property
    def blocked(self) -> bool:
        return self.exit_code == 1

    @property
    def invalid(self) -> bool:
        return self.exit_code == 2

    @property
    def retry_required(self) -> bool:
        return self.exit_code == 3

    @property
    def primary_token(self) -> str | None:
        # "blocked" and "retry_required" are the only non-terminal-pass
        # check statuses that carry a caller-facing token today
        # ("passed"/"skipped" never do). CLAIM_NOT_OBSERVED
        # (109.021-T) is a read-only retry-required outcome, not a
        # `blocked` one -- it must still surface as the primary token so
        # callers (Ship's bounded reclaim-and-reverify loop, telemetry
        # mapping) can key off it the same way they key off
        # CLAIM_VERIFY_FAILED.
        for check in self.checks:
            if check.status in ("blocked", "retry_required") and check.token:
                return check.token
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "phase": self.phase,
            "target_shipment_id": self.resolved_target_shipment_id,
            "exit_code": self.exit_code,
            "blocked": self.blocked,
            "invalid": self.invalid,
            "message": self.message,
            "checks": [check.to_dict() for check in self.checks],
            "token": self.primary_token,
            "forced": self.forced,
        }


def _run_git(argv: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        shell=False,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _frontmatter(path: Path) -> dict[str, Any]:
    """Parse a backlog artifact's YAML frontmatter, failing closed on any defect.

    A malformed artifact (unreadable file, missing/invalid frontmatter block,
    invalid YAML, or a frontmatter body that is not a mapping) must never be
    silently treated as an empty record: doing so can make an active shipment
    or task quietly disappear from a scan instead of tripping the gate's
    fail-closed BACKLOG_UNAVAILABLE result. Every failure mode below raises
    BacklogUnavailableError so all callers converge on the same fail-closed
    handling already used for an unreadable backlog directory.
    """
    import yaml

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BacklogUnavailableError(path, "artifact is unreadable") from exc
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", raw, flags=re.DOTALL)
    if not match:
        raise BacklogUnavailableError(path, "artifact frontmatter is missing or malformed")
    try:
        loaded = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise BacklogUnavailableError(path, "artifact frontmatter is invalid YAML") from exc
    if not isinstance(loaded, dict):
        raise BacklogUnavailableError(path, "artifact frontmatter is not a mapping")
    return loaded


def _closure_conditions_satisfied(conditions: Any) -> bool:
    """Validate a post-merge closure artifact's machine-readable ``conditions:`` block.

    ``READY_WITH_CONDITIONS`` counts as complete only when this block is a
    well-formed, non-empty sequence of mappings and EVERY entry has
    ``satisfied: true`` (the literal boolean, not a truthy string) plus a
    non-empty ``evidence`` reference. Absent, empty, malformed, unverified,
    or evidence-less entries all fail closed (never treated as satisfied).
    """
    if not isinstance(conditions, list) or not conditions:
        return False
    for condition in conditions:
        if not isinstance(condition, dict):
            return False
        if condition.get("satisfied") is not True:
            return False
        evidence = condition.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            return False
    return True


def _closure_artifact_complete(fm: dict[str, Any]) -> bool:
    """Decide whether one parsed closure-artifact frontmatter registers complete.

    109.023-T (114-S closure pre-activation fix, Defect 3): the prior
    implementation returned ``True`` on ``compaction_status`` alone,
    ignoring ``closure_status``/releasability entirely -- a
    ``READY_WITH_CONDITIONS``, ``BLOCKED``, or closure-status-less artifact
    all registered as complete. This now requires BOTH:

    1. ``compaction_status`` in ``{done, degraded}`` (P-020 evidence), AND
    2. ``closure_status == READY`` OR a fully-satisfied machine-readable
       ``conditions:`` block when ``closure_status == READY_WITH_CONDITIONS``.

    ``BLOCKED``, a missing ``closure_status``, and any other value fail
    closed. Malformed frontmatter never reaches this function -- ``_frontmatter``
    already raises ``BacklogUnavailableError`` for that case, which callers
    convert to a fail-closed ``BACKLOG_UNAVAILABLE`` result the same way an
    unreadable backlog directory does; this function never itself
    "{}-swallows" a bad parse.
    """
    compaction = fm.get("compaction_status") or fm.get("compaction")
    if not (isinstance(compaction, str) and compaction.strip().lower() in {"done", "degraded"}):
        return False

    closure_status = fm.get("closure_status")
    if not isinstance(closure_status, str) or not closure_status.strip():
        return False

    normalized = closure_status.strip().upper()
    if normalized == "READY":
        return True
    if normalized == "READY_WITH_CONDITIONS":
        return _closure_conditions_satisfied(fm.get("conditions"))
    # BLOCKED and any other/unrecognized value fail closed.
    return False


def _tuple_of_str(
    value: Any,
    *,
    source_path: Path | None = None,
    field_name: str = "",
) -> tuple[str, ...]:
    """Coerce a frontmatter field to a tuple of validated, nonblank artifact ids.

    A missing field (``None``) legitimately means "none declared" and
    resolves to an empty tuple. But a field that IS present with a
    non-sequence value (e.g. ``dependencies: "100-S"`` as a bare string, or
    ``custom_fields.items: 42``) must never be silently normalized to an
    empty tuple: that would drop an actual blocking predecessor or hide
    active/done manifest tasks from the detect-before-consistency scan,
    letting corrupted backlog state pass fail-closed checks.

    Likewise, once the container shape is valid, every MEMBER must be
    validated too: a non-string member, a blank member, or a member that
    does not match the backlog artifact id shape (``_ARTIFACT_ID_PATTERN``)
    must never be silently stringified/coerced or dropped. Storing a
    malformed member (e.g. ``../../outside``) can later be interpolated
    into a filesystem glob (e.g. ``closure_complete``'s predecessor lookup)
    and traverse outside the intended backlog directory, or a blank/wrong-
    shaped member can silently disappear from detect-before-consistency.

    When ``source_path`` is provided, any of these defects raises
    BacklogUnavailableError instead of coercing or dropping.
    """
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        if source_path is not None:
            raise BacklogUnavailableError(
                source_path,
                f"{field_name or 'field'} must be a sequence of ids but got {value!r}",
            )
        return ()
    result: list[str] = []
    for item in value:
        text = item.strip() if isinstance(item, str) else None
        if text and _ARTIFACT_ID_PATTERN.match(text):
            result.append(text)
            continue
        if source_path is not None:
            raise BacklogUnavailableError(
                source_path,
                f"{field_name or 'field'} contains an invalid or unsafe member id: {item!r}",
            )
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return tuple(result)



def _archived_status(frontmatter: dict[str, Any]) -> str | None:
    value = frontmatter.get("archived_status")
    return str(value).strip().lower() if isinstance(value, str) and value.strip() else None


class FilesystemTopologyReaders:
    """Default read-only topology readers backed by the local workspace."""

    def __init__(self, workspace: Path | str = ".") -> None:
        self.workspace = Path(workspace)
        self._backlog_dir: Path | None = None

    @property
    def backlog_dir(self) -> Path:
        if self._backlog_dir is None:
            self._backlog_dir = resolve_backlog_root(self.workspace)
        return self._backlog_dir

    def _glob_id(self, folder: str, artifact_id: str) -> Path | None:
        base = self.backlog_dir / folder
        if not base.exists():
            return None
        for candidate in sorted(base.glob(f"{artifact_id}.*")):
            if candidate.is_file():
                return candidate
        return None

    def _artifact_from_paths(self, artifact_id: str) -> ArtifactState | None:
        if not _ARTIFACT_ID_PATTERN.match(artifact_id):
            # A malformed artifact id (containing "..", an absolute path, or
            # glob metacharacters) must never be interpolated into a
            # filesystem glob: that can traverse outside the queue/archive
            # directories or raise an unhandled path-pattern exception
            # instead of the gate's normal fail-closed result. Validate the
            # shape up front and contain resolution to exact, safe
            # candidates only.
            raise BacklogUnavailableError(
                self.backlog_dir,
                f"artifact id has an invalid or unsafe shape and cannot be resolved: {artifact_id!r}",
            )
        queue_path = self._glob_id("queue", artifact_id)
        archive_path = self._glob_id("archive", artifact_id)
        if queue_path is None and archive_path is None:
            return None
        queue_fm = _frontmatter(queue_path) if queue_path else {}
        archive_fm = _frontmatter(archive_path) if archive_path else {}
        artifact_type = ""
        for fm in (queue_fm, archive_fm):
            value = fm.get("artifact_type")
            if isinstance(value, str) and value.strip():
                artifact_type = value.strip()
                break
        live_status: str | None = None
        if queue_path is not None:
            status = queue_fm.get("status")
            normalized_status = status.strip().lower() if isinstance(status, str) and status.strip() else None
            if normalized_status not in _VALID_LIVE_ARTIFACT_STATUSES:
                # A syntactically valid queue task/feature record with a
                # missing, blank, or unsupported status must not be silently
                # normalized away: detect-before-consistency would otherwise
                # skip it, letting malformed state hide an active/done
                # manifest task and pass the fail-closed gate.
                raise BacklogUnavailableError(
                    queue_path,
                    f"artifact record has a missing or unsupported status: {status!r}",
                )
            live_status = normalized_status
        archived = _archived_status(archive_fm)
        return ArtifactState(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            live_status=live_status,
            archived_status=archived,
        )

    def list_shipments(self) -> Sequence[ShipmentState]:
        if not self.backlog_dir.exists() or not self.backlog_dir.is_dir():
            raise BacklogUnavailableError(self.backlog_dir, "backlog directory is unavailable")

        records: dict[str, dict[str, Any]] = {}
        for folder, is_archive in (("queue", False), ("archive", True)):
            base = self.backlog_dir / folder
            if not base.exists() or not base.is_dir():
                raise BacklogUnavailableError(base, "required backlog directory is unavailable")
            try:
                candidates = sorted(base.glob("*.md"))
            except OSError as exc:
                raise BacklogUnavailableError(base, "required backlog directory is unreadable") from exc
            for candidate in candidates:
                fm = _frontmatter(candidate)
                if fm.get("artifact_type") != "shipment":
                    fm_id = fm.get("id")
                    shape_id = fm_id.strip() if isinstance(fm_id, str) and fm_id.strip() else candidate.stem
                    if _SHIPMENT_ID_PATTERN.match(shape_id):
                        # A shipment-shaped id/filename (digits + "-S") with a
                        # missing or misspelled artifact_type is a corrupted
                        # type declaration, not a legitimately different
                        # artifact. Silently skipping it could remove an
                        # active shipment from the global scan and let
                        # ambient/CI pass on an incomplete backlog view.
                        raise BacklogUnavailableError(
                            candidate,
                            f"shipment-shaped record has a missing or invalid artifact_type: {fm.get('artifact_type')!r}",
                        )
                    continue
                shipment_id = fm.get("id")
                if not isinstance(shipment_id, str) or not shipment_id.strip():
                    # A syntactically valid shipment artifact with a missing or
                    # blank id cannot be safely attributed to any shipment and
                    # must not be silently dropped from the scan: that could
                    # remove an active shipment from the global count and let
                    # ambient/CI pass on an incomplete view of the backlog.
                    raise BacklogUnavailableError(candidate, "shipment record has a missing or blank id")
                normalized_shipment_id = shipment_id.strip()
                if not _SHIPMENT_ID_PATTERN.match(normalized_shipment_id):
                    # A correctly-typed shipment record (``artifact_type:
                    # shipment``) whose declared id does NOT match the
                    # module's own shipment id shape (digits + "-S") must
                    # not be silently admitted into the scan: it could
                    # become the sole active ambient target (or a
                    # predecessor/dependency match) and let corrupted
                    # backlog state pass fail-closed checks. Only the
                    # missing/misspelled artifact_type path was previously
                    # validated against this shape; a correctly-typed but
                    # wrongly-shaped id must fail closed the same way.
                    raise BacklogUnavailableError(
                        candidate,
                        f"shipment record has an id that does not match the shipment id shape: {shipment_id!r}",
                    )
                record = records.setdefault(normalized_shipment_id, {"shipment_id": normalized_shipment_id})
                folder_source_key = "archive_source_path" if is_archive else "queue_source_path"
                existing_source = record.get(folder_source_key)
                if existing_source is not None:
                    # A second record in the SAME folder for an already-seen
                    # shipment id must never be silently merged: sort-order-
                    # dependent field overwrites (active status, manifest,
                    # dependencies) can hide an active shipment from the
                    # global invariant. Fail closed instead of merging.
                    raise BacklogUnavailableError(
                        candidate,
                        (
                            f"duplicate {'archive' if is_archive else 'queue'} shipment record for id "
                            f"{shipment_id.strip()!r} (also found at {existing_source})"
                        ),
                    )
                record[folder_source_key] = candidate
                title = fm.get("title")
                if isinstance(title, str) and title.strip():
                    record["title"] = title.strip()
                if is_archive:
                    # Track archive-record presence independently of whether
                    # `archived_status` itself parsed to a usable value: a
                    # malformed/generic archive copy (missing or blank
                    # archived_status) is still a live+archive duplicate and
                    # must not be indistinguishable from "no archive record"
                    # when checking for an ambiguous predecessor state.
                    record["archived_record_present"] = True
                    record["archived_status"] = _archived_status(fm)
                else:
                    status = fm.get("status")
                    normalized_status = status.strip().lower() if isinstance(status, str) and status.strip() else None
                    if normalized_status not in _VALID_LIVE_SHIPMENT_STATUSES:
                        # A queue-folder shipment record with a missing or
                        # unrecognized status cannot be safely classified as
                        # active/inactive; treating it as "no live status" (or
                        # any other lenient default) can hide a malformed
                        # active record from the active-shipment invariant and
                        # pass fail-open in ambient/CI mode.
                        raise BacklogUnavailableError(
                            candidate,
                            f"shipment record has a missing or unsupported status: {status!r}",
                        )
                    record["live_status"] = normalized_status
                    custom_fields = fm.get("custom_fields")
                    items: tuple[str, ...] = ()
                    if custom_fields is not None:
                        if not isinstance(custom_fields, dict):
                            # A present-but-wrong-shaped custom_fields block
                            # (e.g. a bare string) must not silently degrade
                            # to "no manifest items": that hides the
                            # shipment's real manifest from the
                            # detect-before-consistency scan.
                            raise BacklogUnavailableError(
                                candidate,
                                f"custom_fields must be a mapping but got {custom_fields!r}",
                            )
                        items = _tuple_of_str(
                            custom_fields.get("items"),
                            source_path=candidate,
                            field_name="custom_fields.items",
                        )
                    record["manifest_item_ids"] = items
                    record["blocking_predecessor_ids"] = _tuple_of_str(
                        fm.get("dependencies"),
                        source_path=candidate,
                        field_name="dependencies",
                    )
        return tuple(
            ShipmentState(
                shipment_id=str(record.get("shipment_id", "")),
                title=str(record.get("title", record.get("shipment_id", ""))),
                live_status=record.get("live_status"),
                archived_status=record.get("archived_status"),
                archived_record_present=bool(record.get("archived_record_present", False)),
                manifest_item_ids=tuple(record.get("manifest_item_ids", ()) or ()),
                blocking_predecessor_ids=tuple(record.get("blocking_predecessor_ids", ()) or ()),
            )
            for record in sorted(records.values(), key=lambda item: str(item.get("shipment_id", "")))
        )

    def read_artifact(self, artifact_id: str) -> ArtifactState | None:
        return self._artifact_from_paths(artifact_id)

    def current_branch(self) -> str:
        return _run_git(["git", "--no-pager", "branch", "--show-current"], self.workspace)

    def default_branch(self) -> str:
        remote_head = _run_git(
            ["git", "--no-pager", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
            self.workspace,
        )
        if remote_head and "/" in remote_head:
            return remote_head.rsplit("/", 1)[-1]
        return "main"

    def worktree_porcelain(self) -> str:
        return _run_git(["git", "--no-pager", "worktree", "list", "--porcelain"], self.workspace)

    def read_worktree_marker(self, worktree_path: str) -> str | None:
        marker_path = Path(worktree_path) / '.autoharness' / 'stage-worktree-marker.yaml'
        try:
            return marker_path.read_text(encoding='utf-8')
        except (FileNotFoundError, OSError):
            return None

    def closure_complete(self, shipment_id: str) -> bool | None:
        closure_dir = self.workspace / "docs" / "closure"
        if not closure_dir.exists():
            return None
        matches = sorted(closure_dir.glob(f"{shipment_id}-*-post-merge-closure.md"))
        if not matches:
            return None
        for candidate in matches:
            fm = _frontmatter(candidate)
            if _closure_artifact_complete(fm):
                return True
        return False


class _NullReaders:
    def list_shipments(self) -> Sequence[ShipmentState]:
        return ()

    def read_artifact(self, artifact_id: str) -> ArtifactState | None:
        return None

    def current_branch(self) -> str:
        return "main"

    def default_branch(self) -> str:
        return "main"

    def worktree_porcelain(self) -> str:
        return (
            'worktree .\n'
            'HEAD 0000000000000000000000000000000000000000\n'
            'branch refs/heads/main\n\n'
        )

    def read_worktree_marker(self, worktree_path: str) -> str | None:
        return None

    def closure_complete(self, shipment_id: str) -> bool | None:
        return None


def _claim_not_observed(
    topology_input: TopologyInput,
    target: str | None,
) -> TopologyResult:
    # Read-only retry-required outcome contract (109.021-T). A stateless,
    # read-only post-claim detector CANNOT distinguish a merely-delayed
    # claim from a genuinely-failed one on a single snapshot -- both
    # present identically as target `queued` + zero active shipments. This
    # helper therefore never re-reads backlog state and never attempts to
    # classify delayed vs failed; it always returns the same
    # `CLAIM_NOT_OBSERVED` token for that indistinguishable case. The
    # result is non-zero (exit_code 3) and explicitly NOT `blocked`
    # (exit_code 1) so it is never confused with a genuine terminal
    # ambiguity. Terminal `CLAIM_VERIFY_FAILED` classification for
    # retry-exhaustion (a second `CLAIM_NOT_OBSERVED` after one bounded
    # Ship-owned reclaim cycle) is owned by 109.017-T's Ship-side
    # reclaim-and-reverify sequence, not by this gate.
    message = (
        "CLAIM_NOT_OBSERVED: target shipment claim not yet observed "
        "(still queued, zero active shipments) -- this is indistinguishable "
        "from a genuinely failed claim on a single read-only snapshot; "
        "(re)claim and re-invoke --phase post_claim (bounded, at most once)"
    )
    check = CheckResult(
        name="post_claim_reverify",
        status="retry_required",
        token="CLAIM_NOT_OBSERVED",
        message=message,
        details={
            "target_shipment_id": target,
        },
    )
    return TopologyResult(
        mode=topology_input.mode,
        phase="post_claim",
        resolved_target_shipment_id=target,
        checks=(check,),
        exit_code=3,
        message=message,
    )


def _claim_verify_failed(
    topology_input: TopologyInput,
    target: str | None,
    detail: TopologyResult | CheckResult,
    *,
    reason: str,
) -> TopologyResult:
    token = detail.primary_token if isinstance(detail, TopologyResult) else detail.token
    message = f"CLAIM_VERIFY_FAILED: {reason}"
    if token:
        message = f"{message} ({token})"
    check = CheckResult(
        name="post_claim_reverify",
        status="blocked",
        token="CLAIM_VERIFY_FAILED",
        message=message,
        details={
            "target_shipment_id": target,
            "cause_token": token,
        },
    )
    return TopologyResult(
        mode=topology_input.mode,
        phase="post_claim",
        resolved_target_shipment_id=target,
        checks=(check,),
        exit_code=1,
        message=message,
    )


def _evaluate_core(
    topology_input: TopologyInput,
    resolved_phase: str,
    target: str | None,
    bound_readers: TopologyReaders,
    shipments: Sequence[ShipmentState],
) -> TopologyResult:
    # Individual checks below may perform additional reads beyond the
    # already-validated `shipments` snapshot (e.g. read_artifact for the
    # detect-before-consistency scan, closure_complete for shipment
    # readiness). A malformed or unreadable artifact encountered during those
    # reads raises BacklogUnavailableError from `_frontmatter`; it must fail
    # closed the same way an unavailable backlog directory does, never escape
    # as an unhandled exception.
    try:
        checks: list[CheckResult] = []

        consistency = _detect_before_consistency(shipments, bound_readers)
        checks.append(consistency)
        if consistency.status == "blocked":
            return _blocked_result(topology_input, resolved_phase, target, consistency)

        active_check = _active_invariant_check(resolved_phase, target, shipments)
        checks.append(active_check)
        if active_check.status == "blocked":
            return _blocked_result(topology_input, resolved_phase, target, active_check)

        branch_check = _branch_ownership_check(target, shipments, bound_readers, mode=topology_input.mode)
        checks.append(branch_check)
        if branch_check.status == "blocked":
            return _blocked_result(topology_input, resolved_phase, target, branch_check)

        worktree_check = _worktree_uniqueness_check(bound_readers)
        checks.append(worktree_check)
        if worktree_check.status == "blocked":
            return _blocked_result(topology_input, resolved_phase, target, worktree_check)

        readiness_check = _shipment_readiness_check(resolved_phase, target, shipments, bound_readers)
        checks.append(readiness_check)
        if readiness_check.status == "blocked":
            return _blocked_result(topology_input, resolved_phase, target, readiness_check)

        return _pass_result(topology_input, resolved_phase, target, checks)
    except BacklogUnavailableError as exc:
        return _backlog_unavailable_result(topology_input, resolved_phase, target, exc)


def _target_live_status(target: str | None, shipments: Sequence[ShipmentState]) -> str | None:
    if target is None:
        return None
    shipment = _shipment_map(shipments).get(target)
    return shipment.live_status if shipment is not None else None


def _evaluate_post_claim(
    topology_input: TopologyInput,
    target: str | None,
    bound_readers: TopologyReaders,
) -> TopologyResult:
    try:
        initial_shipments = tuple(bound_readers.list_shipments())
    except BacklogUnavailableError as exc:
        return _backlog_unavailable_result(topology_input, "post_claim", target, exc)
    initial = _evaluate_core(topology_input, "post_claim", target, bound_readers, initial_shipments)
    if initial.exit_code == 0:
        return initial
    if initial.primary_token not in _POST_CLAIM_WRAP_TOKENS:
        return initial

    target_status = _target_live_status(target, initial_shipments)
    active_count = len(_active_shipments(initial_shipments))
    if initial.primary_token == "SHIPMENT_STATE_INCONSISTENT":
        return _claim_verify_failed(
            topology_input,
            target,
            initial,
            reason="detect-before consistency scan found a queued shipment with active/done work",
        )
    if target_status == "queued" and active_count == 0:
        # Read-only retry-required outcome (109.021-T): a single
        # post-claim snapshot showing the target still `queued` with zero
        # active shipments is INDISTINGUISHABLE between "the claim is
        # merely delayed" and "the claim genuinely failed" -- both look
        # identical to a stateless read-only detector. This gate performs
        # NO second read here and NO internal retry (there is no
        # intervening claim/mutation between two internal reads, so a
        # second internal read could never observe a different state
        # anyway -- that was the illusory self-retry this replaces).
        # Convergence, if any, must come from an external actor
        # (Ship's bounded, double-claim-guarded reclaim-and-reverify
        # sequence, 109.017-T) performing an actual claim between
        # invocations of this gate.
        return _claim_not_observed(topology_input, target)

    return _claim_verify_failed(
        topology_input,
        target,
        initial,
        reason="post-claim topology did not converge to target-active-and-sole",
    )


def _invalid_result(topology_input: TopologyInput, phase: str, message: str) -> TopologyResult:
    return TopologyResult(
        mode=topology_input.mode,
        phase=phase,
        resolved_target_shipment_id=(topology_input.target_shipment_id or "").strip() or None,
        exit_code=2,
        message=message,
    )


def _blocked_result(topology_input: TopologyInput, phase: str, target: str | None, check: CheckResult) -> TopologyResult:
    return TopologyResult(
        mode=topology_input.mode,
        phase=phase,
        resolved_target_shipment_id=target,
        checks=(check,),
        exit_code=1,
        message=check.message or "topology gate blocked",
    )


def _backlog_unavailable_result(
    topology_input: TopologyInput,
    phase: str,
    target: str | None,
    exc: BacklogUnavailableError,
) -> TopologyResult:
    check = CheckResult(
        name="backlog_state",
        status="blocked",
        token="BACKLOG_UNAVAILABLE",
        message=f"BACKLOG_UNAVAILABLE: {exc}",
        details={
            "target_shipment_id": target,
            "backlog_path": exc.path,
            "reason": exc.reason,
        },
    )
    return _blocked_result(topology_input, phase, target, check)


def _pass_result(topology_input: TopologyInput, phase: str, target: str | None, checks: Sequence[CheckResult]) -> TopologyResult:
    return TopologyResult(
        mode=topology_input.mode,
        phase=phase,
        resolved_target_shipment_id=target,
        checks=tuple(checks),
    )


def _normalize_target(value: str | None) -> str | None:
    stripped = (value or "").strip()
    return stripped or None


def _resolve_phase(topology_input: TopologyInput) -> str:
    return topology_input.phase or ("ambient" if topology_input.mode in ("manual", "ci") else "")


def _validate_input(topology_input: TopologyInput) -> TopologyResult | None:
    if topology_input.mode not in VALID_MODES:
        return _invalid_result(
            topology_input,
            topology_input.phase or "ambient",
            f"invalid mode: {topology_input.mode!r}",
        )

    resolved_phase = _resolve_phase(topology_input)
    if topology_input.mode == "agent":
        if _normalize_target(topology_input.target_shipment_id) is None:
            return _invalid_result(
                topology_input,
                resolved_phase or "ambient",
                "agent mode requires --shipment <shipment_id>",
            )
        if resolved_phase not in SCOPED_PHASES:
            return _invalid_result(
                topology_input,
                resolved_phase or "ambient",
                "agent mode requires --phase pre_claim|post_claim|lifecycle",
            )
        return None

    if resolved_phase not in VALID_PHASES:
        return _invalid_result(
            topology_input,
            resolved_phase or "ambient",
            f"invalid phase: {resolved_phase!r}",
        )
    # An explicit scoped phase (pre_claim/post_claim/lifecycle) always evaluates
    # branch ownership and shipment readiness against a specific target; that
    # target must be provided regardless of mode. Only `ambient` is meaningful
    # without one. Without this check, `--mode ci --phase pre_claim` (or manual
    # mode) with no `--shipment` could pass with zero active shipments while
    # silently skipping ownership/readiness checks the scoped-input contract
    # requires.
    if resolved_phase in SCOPED_PHASES and _normalize_target(topology_input.target_shipment_id) is None:
        return _invalid_result(
            topology_input,
            resolved_phase,
            f"--phase {resolved_phase} requires --shipment <shipment_id> in any mode",
        )
    return None



@dataclass(frozen=True)
class WorktreeEntry:
    path: str
    branch: str | None = None


def parse_worktree_porcelain(porcelain: str) -> tuple[WorktreeEntry, ...]:
    entries: list[WorktreeEntry] = []
    block: dict[str, str] = {}
    for raw_line in porcelain.splitlines():
        line = raw_line.strip()
        if not line:
            if block.get("worktree"):
                entries.append(
                    WorktreeEntry(
                        path=block["worktree"],
                        branch=block.get("branch"),
                    )
                )
            block = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            block["worktree"] = value.strip()
        elif key == "branch":
            branch = value.strip()
            if branch.startswith("refs/heads/"):
                branch = branch[len("refs/heads/") :]
            block["branch"] = branch
    if block.get("worktree"):
        entries.append(
            WorktreeEntry(
                path=block["worktree"],
                branch=block.get("branch"),
            )
        )
    return tuple(entries)


def _parse_stage_worktree_expiry(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed.astimezone(timezone.utc)


def _is_stage_spike_research_worktree(entry: WorktreeEntry, readers: TopologyReaders) -> bool:
    import yaml

    branch = (entry.branch or "").lower()
    if not (branch.startswith("spike/") or branch.startswith("research/")):
        return False

    marker_text = readers.read_worktree_marker(entry.path)
    if not isinstance(marker_text, str) or not marker_text.strip():
        return False

    try:
        marker = yaml.safe_load(marker_text)
    except yaml.YAMLError:
        return False
    if not isinstance(marker, dict):
        return False
    if marker.get("role") != "spike-research":
        return False

    expires_at = _parse_stage_worktree_expiry(marker.get("expires_at"))
    return expires_at is not None and expires_at > datetime.now(timezone.utc)


def _worktree_uniqueness_check(readers: TopologyReaders) -> CheckResult:
    entries = parse_worktree_porcelain(readers.worktree_porcelain())
    spike_research = [entry for entry in entries if _is_stage_spike_research_worktree(entry, readers)]
    implementation = [entry for entry in entries if entry not in spike_research]
    if len(implementation) == 1:
        return CheckResult(
            name="worktree_topology",
            status="passed",
            token="WORKTREE_TOPOLOGY_OK",
            details={
                "implementation_worktrees": [entry.path for entry in implementation],
                "spike_research_worktrees": [entry.path for entry in spike_research],
            },
        )
    if len(implementation) == 0:
        return CheckResult(
            name="worktree_topology",
            status="blocked",
            token="NO_IMPLEMENTATION_WORKTREE",
            message="NO_IMPLEMENTATION_WORKTREE: topology gate requires exactly one implementation worktree",
            details={"spike_research_worktrees": [entry.path for entry in spike_research]},
        )
    return CheckResult(
        name="worktree_topology",
        status="blocked",
        token="MULTIPLE_IMPLEMENTATION_WORKTREES",
        message="MULTIPLE_IMPLEMENTATION_WORKTREES: topology gate allows exactly one implementation worktree",
        details={
            "implementation_worktrees": [entry.path for entry in implementation],
            "spike_research_worktrees": [entry.path for entry in spike_research],
        },
    )


def _shipment_map(shipments: Sequence[ShipmentState]) -> dict[str, ShipmentState]:
    return {shipment.shipment_id: shipment for shipment in shipments}


def _strip_parenthetical(title: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", title).strip()


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def _branch_aliases(shipment: ShipmentState) -> tuple[str, ...]:
    base = _strip_parenthetical(shipment.title) or shipment.title
    aliases = {
        _slugify(shipment.title),
        _slugify(base),
        _slugify(f"{shipment.shipment_id} {shipment.title}"),
        _slugify(f"{shipment.shipment_id} {base}"),
    }
    return tuple(sorted(alias for alias in aliases if alias))


def _normalize_branch_name(branch: str) -> str:
    value = branch.strip()
    if value.startswith("refs/heads/"):
        value = value[len("refs/heads/") :]
    return value


def _resolve_shipment_from_branch(branch: str, shipments: Sequence[ShipmentState]) -> str | None:
    normalized = _normalize_branch_name(branch)
    if not normalized.startswith(_BRANCH_KIND_PREFIXES):
        return None
    _, slug = normalized.split("/", 1)
    exact = [shipment.shipment_id for shipment in shipments if slug in _branch_aliases(shipment)]
    if len(exact) == 1:
        return exact[0]
    prefixed = [
        shipment.shipment_id
        for shipment in shipments
        if slug.startswith(f"{shipment.shipment_id.lower()}-")
    ]
    if len(prefixed) == 1:
        return prefixed[0]
    return None


def _resolve_target_shipment(
    topology_input: TopologyInput,
    shipments: Sequence[ShipmentState],
    readers: TopologyReaders,
) -> tuple[str | None, str | None]:
    explicit = _normalize_target(topology_input.target_shipment_id)
    shipment_map = _shipment_map(shipments)
    if explicit is not None:
        if explicit not in shipment_map:
            return None, f"unknown shipment target: {explicit}"
        return explicit, None
    if topology_input.mode == "agent":
        return None, "agent mode requires --shipment <shipment_id>"
    active = _active_shipments(shipments)
    if len(active) == 1:
        return active[0].shipment_id, None
    resolved = _resolve_shipment_from_branch(readers.current_branch(), shipments)
    return resolved, None


def _ci_detached_head_branch_fallback() -> str:
    """CI-only fallback branch resolution for a detached-HEAD checkout.

    ``actions/checkout`` (and equivalent CI checkout actions) always leaves the
    working tree on a detached HEAD -- for a ``pull_request``-triggered run it
    checks out the PR merge ref, and for a ``push``-triggered run it checks out
    the pushed commit directly -- so ``git branch --show-current`` reports an
    empty string in BOTH cases even though the real branch is well known to the
    CI platform via environment variables. Without this fallback, ``--mode ci``
    would report ``BRANCH_MISMATCH: detached HEAD`` on every single CI run,
    defeating Gate C's entire purpose.

    Resolution order (GitHub Actions environment variables):

    1. ``GITHUB_HEAD_REF`` -- set only for ``pull_request`` events; this is
       ALWAYS the PR's real source branch short name (never a merge-ref, never
       ``refs/heads/``-prefixed), so it is trusted unconditionally.
    2. ``GITHUB_REF_NAME`` -- set for every event, but only trustworthy as a
       BRANCH name when ``GITHUB_REF_TYPE == "branch"``. GitHub Actions sets
       ``GITHUB_REF_TYPE`` to ``branch`` or ``tag`` to disambiguate exactly
       this case; relying on it (rather than a naive "does the name contain a
       slash" heuristic) correctly accepts a slash-containing push-triggered
       branch name (e.g. ``feat/foo``, this repo's own naming convention) and
       correctly rejects a tag push (``GITHUB_REF_TYPE == "tag"``, where
       ``GITHUB_REF_NAME`` would be a version string, not a branch) -- neither
       of which a plain ``"/" in ref_name`` substring check can distinguish.

    Returns an empty string (never raises) when neither variable resolves a
    usable branch name, preserving the existing fail-closed
    ``BRANCH_MISMATCH: detached HEAD`` behavior for a CI platform this
    fallback does not recognize, or for a non-branch ref (e.g. a tag push).
    """
    head_ref = os.environ.get("GITHUB_HEAD_REF", "").strip()
    if head_ref:
        return head_ref
    ref_type = os.environ.get("GITHUB_REF_TYPE", "").strip()
    ref_name = os.environ.get("GITHUB_REF_NAME", "").strip()
    if ref_type == "branch" and ref_name:
        return ref_name
    return ""


def _ci_default_branch_fallback() -> str:
    """CI-only fallback default-branch resolution via the GitHub Actions event payload.

    ``FilesystemTopologyReaders.default_branch()`` resolves the default branch
    from the ``refs/remotes/origin/HEAD`` symbolic ref, falling back to a
    hard-coded ``"main"`` when that ref is unset. ``actions/checkout`` does
    NOT set this symref by default (it performs a shallow, single-ref fetch
    and never runs ``git remote set-head``), so in CI this always falls back
    to the hard-coded value. For a repository whose real default branch is
    not ``main`` (e.g. ``master``, ``trunk``), a push to that actual default
    branch can be misclassified as ``BRANCH_MISMATCH`` instead of
    ``BRANCH_CREATE_ELIGIBLE`` whenever a shipment happens to be active,
    incorrectly blocking valid CI once the job is required.

    GitHub Actions writes the full webhook event payload for the triggering
    event to the file at ``GITHUB_EVENT_PATH`` for every event type, and that
    payload's ``repository.default_branch`` field is the platform's own
    authoritative answer -- present on the ``repository`` object of every
    GitHub webhook event, not just ``push``/``pull_request``.

    Returns an empty string (never raises) when ``GITHUB_EVENT_PATH`` is
    unset, unreadable, not valid JSON, or lacks a usable
    ``repository.default_branch`` string -- preserving the existing
    git-based (``main``-fallback) resolution in that case.
    """
    event_path = os.environ.get("GITHUB_EVENT_PATH", "").strip()
    if not event_path:
        return ""
    try:
        with open(event_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError):
        return ""
    if not isinstance(payload, dict):
        return ""
    repository = payload.get("repository")
    if not isinstance(repository, dict):
        return ""
    default_branch = repository.get("default_branch")
    if isinstance(default_branch, str) and default_branch.strip():
        return default_branch.strip()
    return ""


def _ci_pull_request_event_active() -> bool:
    """Return True when the current CI run is a ``pull_request`` event.

    Copilot review finding (PR #302 thread PRRT_kwDORzpWpM6WzvNo): a fork PR
    whose source branch happens to be named the same as the target
    repository's default branch (``main`` is the common default for a fork,
    so this collision is not exotic) would otherwise satisfy
    ``current_branch == default_branch`` in ``_branch_ownership_check`` and
    be granted ``BRANCH_CREATE_ELIGIBLE`` -- even though the run is testing a
    PR's proposed head, not an actual push to the target repository's
    default branch. ``GITHUB_HEAD_REF`` is set by GitHub Actions ONLY for
    ``pull_request``/``pull_request_target`` events (see
    ``_ci_detached_head_branch_fallback`` above), so its presence is a
    reliable, already-established signal that this run is a PR, not a push,
    regardless of what branch name the fork happens to use.
    """
    return bool(os.environ.get("GITHUB_HEAD_REF", "").strip())


def _branch_ownership_check(
    target: str | None,
    shipments: Sequence[ShipmentState],
    readers: TopologyReaders,
    mode: str = "agent",
) -> CheckResult:
    if target is None:
        return CheckResult(
            name="branch_ownership",
            status="skipped",
            message="ambient target did not resolve; ownership check skipped",
        )

    shipment = _shipment_map(shipments).get(target)
    if shipment is None:
        return CheckResult(
            name="branch_ownership",
            status="skipped",
            message="shipment metadata unavailable; ownership check skipped",
        )
    current_branch = _normalize_branch_name(readers.current_branch())
    ci_fallback_used = False
    if not current_branch and mode == "ci":
        fallback_branch = _ci_detached_head_branch_fallback()
        if fallback_branch:
            current_branch = _normalize_branch_name(fallback_branch)
            ci_fallback_used = True
    default_branch = _normalize_branch_name(readers.default_branch())
    default_branch_ci_fallback_used = False
    if mode == "ci":
        ci_default_branch = _ci_default_branch_fallback()
        if ci_default_branch:
            default_branch = _normalize_branch_name(ci_default_branch)
            default_branch_ci_fallback_used = True
    canonical = tuple(f"feat/{alias}" for alias in _branch_aliases(shipment)) + tuple(
        f"chore/{alias}" for alias in _branch_aliases(shipment)
    )

    if not current_branch:
        return CheckResult(
            name="branch_ownership",
            status="blocked",
            token="BRANCH_MISMATCH",
            message=(
                f"BRANCH_MISMATCH: detached HEAD does not match target {target}"
            ),
            details={
                "current_branch": current_branch,
                "expected_branches": list(canonical),
                "detached_head": True,
                "resolved_via_ci_env_fallback": ci_fallback_used,
                "default_branch": default_branch,
                "default_branch_resolved_via_ci_env_fallback": default_branch_ci_fallback_used,
            },
        )

    ci_pull_request_active = mode == "ci" and _ci_pull_request_event_active()
    if current_branch == default_branch and not ci_pull_request_active:
        return CheckResult(
            name="branch_ownership",
            status="passed",
            token="BRANCH_CREATE_ELIGIBLE",
            message=(
                f"BRANCH_CREATE_ELIGIBLE: current branch {current_branch} is the default branch for target {target}"
            ),
            details={
                "current_branch": current_branch,
                "expected_branches": list(canonical),
                "resolved_via_ci_env_fallback": ci_fallback_used,
                "default_branch": default_branch,
                "default_branch_resolved_via_ci_env_fallback": default_branch_ci_fallback_used,
            },
        )

    if current_branch.startswith(_POST_MERGE_BRANCH_PREFIX):
        return CheckResult(
            name="branch_ownership",
            status="passed",
            token="BRANCH_POST_MERGE_CLOSURE_ELIGIBLE",
            message=(
                f"BRANCH_POST_MERGE_CLOSURE_ELIGIBLE: current branch {current_branch} is a "
                f"post-merge closure branch; ownership is not matched by shipment-branch alias "
                f"(post-merge branches are feature-scoped, not shipment-scoped) for target {target}"
            ),
            details={
                "current_branch": current_branch,
                "expected_branches": list(canonical),
                "resolved_via_ci_env_fallback": ci_fallback_used,
                "default_branch": default_branch,
                "default_branch_resolved_via_ci_env_fallback": default_branch_ci_fallback_used,
            },
        )

    if _resolve_shipment_from_branch(current_branch, (shipment,)) == target:
        return CheckResult(
            name="branch_ownership",
            status="passed",
            token="BRANCH_OK",
            message=f"BRANCH_OK: current branch {current_branch} matches target {target}",
            details={
                "current_branch": current_branch,
                "expected_branches": list(canonical),
                "resolved_via_ci_env_fallback": ci_fallback_used,
                "default_branch": default_branch,
                "default_branch_resolved_via_ci_env_fallback": default_branch_ci_fallback_used,
            },
        )

    return CheckResult(
        name="branch_ownership",
        status="blocked",
        token="BRANCH_MISMATCH",
        message=(
            f"BRANCH_MISMATCH: current branch {current_branch} does not match target {target}"
        ),
        details={
            "current_branch": current_branch,
            "expected_branches": list(canonical),
            "resolved_via_ci_env_fallback": ci_fallback_used,
            "default_branch": default_branch,
            "default_branch_resolved_via_ci_env_fallback": default_branch_ci_fallback_used,
        },
    )

def _prior_shipment_id(target: str, shipments: Sequence[ShipmentState]) -> str | None:
    match = re.match(r"^(\d+)-S$", target)
    if not match:
        return None
    target_num = int(match.group(1))
    prior: tuple[int, str] | None = None
    for shipment in shipments:
        other = re.match(r"^(\d+)-S$", shipment.shipment_id)
        if not other:
            continue
        number = int(other.group(1))
        if number >= target_num:
            continue
        if prior is None or number > prior[0]:
            prior = (number, shipment.shipment_id)
    return prior[1] if prior else None


def _normalized_live_status(shipment: ShipmentState) -> str | None:
    value = (shipment.live_status or "").strip().lower()
    return value or None


def _has_ambiguous_shipment_records(shipment: ShipmentState) -> bool:
    live_status = _normalized_live_status(shipment)
    # Use archive-file presence, not archived_status content, so a
    # malformed/generic archive duplicate (missing or blank archived_status)
    # still counts as an ambiguous live+archive co-occurrence rather than
    # being indistinguishable from "no archive record at all".
    return live_status is not None and shipment.archived_record_present


def _is_shipped_terminal(shipment: ShipmentState) -> bool:
    live_status = _normalized_live_status(shipment)
    if live_status == "shipped":
        return True
    if live_status is not None:
        return False
    return shipment.archived_status in {"shipped", "done"}


def _target_phase_requirement(phase: str) -> tuple[str, str, str] | None:
    requirements = {
        "pre_claim": ("queued", "TARGET_NOT_CLAIMABLE", "before claim"),
        "post_claim": ("active", "TARGET_NOT_ACTIVE", "during post-claim verification"),
        "lifecycle": ("active", "TARGET_NOT_ACTIVE", "during lifecycle execution"),
    }
    return requirements.get(phase)


def _shipment_readiness_check(
    phase: str,
    target: str | None,
    shipments: Sequence[ShipmentState],
    readers: TopologyReaders,
) -> CheckResult:
    if target is None:
        return CheckResult(
            name="shipment_readiness",
            status="skipped",
            message="ambient target did not resolve; readiness check skipped",
        )

    shipment_map = _shipment_map(shipments)
    shipment = shipment_map.get(target)
    if shipment is not None and _has_ambiguous_shipment_records(shipment):
        # A duplicated target (live status present AND an archive-folder
        # record also present) is the same provenance corruption already
        # rejected for a predecessor via PREDECESSOR_STATE_AMBIGUOUS. The
        # target's own phase status check below only inspects
        # `normalized_live_status`, which can still equal the phase's
        # expected value (e.g. "queued" for pre_claim) even while an
        # archive-folder duplicate exists -- so this must be rejected
        # BEFORE the phase requirement is evaluated, not after.
        return CheckResult(
            name="shipment_readiness",
            status="blocked",
            token="TARGET_STATE_AMBIGUOUS",
            message=(
                f"TARGET_STATE_AMBIGUOUS: target {target} has conflicting live and archived shipment records"
            ),
            details={
                "phase": phase,
                "target_shipment_id": target,
                "live_status": shipment.live_status,
                "archived_status": shipment.archived_status,
            },
        )
    requirement = _target_phase_requirement(phase)
    normalized_live_status = _normalized_live_status(shipment) if shipment is not None else None
    if requirement is not None:
        expected_live_status, token, phase_note = requirement
        if normalized_live_status != expected_live_status:
            observed = normalized_live_status or "missing live shipment record"
            return CheckResult(
                name="shipment_readiness",
                status="blocked",
                token=token,
                message=(
                    f"{token}: target {target} must have live status {expected_live_status} {phase_note}; "
                    f"found {observed}"
                ),
                details={
                    "phase": phase,
                    "target_shipment_id": target,
                    "expected_live_status": expected_live_status,
                    "live_status": shipment.live_status if shipment else None,
                    "normalized_live_status": normalized_live_status,
                    "archived_status": shipment.archived_status if shipment else None,
                },
            )

    if shipment is None:
        return CheckResult(
            name="shipment_readiness",
            status="skipped",
            message="shipment metadata unavailable; readiness check skipped",
        )

    predecessor_ids = list(shipment.blocking_predecessor_ids)
    prior_id = _prior_shipment_id(target, shipments)
    if prior_id and prior_id not in predecessor_ids:
        predecessor_ids.append(prior_id)

    for predecessor_id in predecessor_ids:
        predecessor = shipment_map.get(predecessor_id)
        if predecessor is not None and _has_ambiguous_shipment_records(predecessor):
            return CheckResult(
                name="shipment_readiness",
                status="blocked",
                token="PREDECESSOR_STATE_AMBIGUOUS",
                message=(
                    f"PREDECESSOR_STATE_AMBIGUOUS: predecessor {predecessor_id} has conflicting live and archived shipment records"
                ),
                details={
                    "target_shipment_id": target,
                    "predecessor_id": predecessor_id,
                    "live_status": predecessor.live_status,
                    "archived_status": predecessor.archived_status,
                },
            )
        if predecessor is None or not _is_shipped_terminal(predecessor):
            return CheckResult(
                name="shipment_readiness",
                status="blocked",
                token="PREDECESSOR_NOT_SHIPPED",
                message=(
                    f"PREDECESSOR_NOT_SHIPPED: predecessor {predecessor_id} is not in a shipped terminal state"
                ),
                details={
                    "target_shipment_id": target,
                    "predecessor_id": predecessor_id,
                    "live_status": predecessor.live_status if predecessor else None,
                    "archived_status": predecessor.archived_status if predecessor else None,
                },
            )
        closure_complete = readers.closure_complete(predecessor_id)
        if closure_complete is not True:
            return CheckResult(
                name="shipment_readiness",
                status="blocked",
                token="PREDECESSOR_CLOSURE_INCOMPLETE",
                message=(
                    f"PREDECESSOR_CLOSURE_INCOMPLETE: predecessor {predecessor_id} is terminal but missing required closure evidence"
                ),
                details={
                    "target_shipment_id": target,
                    "predecessor_id": predecessor_id,
                    "closure_complete": closure_complete,
                },
            )

    return CheckResult(
        name="shipment_readiness",
        status="passed",
        details={"target_shipment_id": target, "predecessor_ids": predecessor_ids},
    )


def _active_shipments(shipments: Sequence[ShipmentState]) -> tuple[ShipmentState, ...]:
    return tuple(shipment for shipment in shipments if shipment.live_status == "active")


def _detect_before_consistency(
    shipments: Sequence[ShipmentState],
    readers: TopologyReaders,
) -> CheckResult:
    for shipment in shipments:
        if shipment.live_status not in _NOT_YET_CLAIMED_STATUSES:
            continue
        for item_id in shipment.manifest_item_ids:
            if not item_id.endswith("-T"):
                continue
            artifact = readers.read_artifact(item_id)
            if artifact is None:
                continue
            if artifact.effective_status in _TASK_ACTIVE_OR_DONE:
                status = artifact.effective_status
                return CheckResult(
                    name="detect_before_consistency",
                    status="blocked",
                    token="SHIPMENT_STATE_INCONSISTENT",
                    message=(
                        f"SHIPMENT_STATE_INCONSISTENT: shipment {shipment.shipment_id} is "
                        f"{shipment.live_status} but task {item_id} is {status}"
                    ),
                    details={
                        "shipment_id": shipment.shipment_id,
                        "shipment_status": shipment.live_status,
                        "task_id": item_id,
                        "task_status": status,
                    },
                )
    return CheckResult(name="detect_before_consistency", status="passed")


def _active_invariant_check(phase: str, target: str | None, shipments: Sequence[ShipmentState]) -> CheckResult:
    active = _active_shipments(shipments)
    active_ids = tuple(shipment.shipment_id for shipment in active)
    count = len(active_ids)

    if phase == "pre_claim":
        if count == 0:
            return CheckResult(
                name="active_shipment_invariant",
                status="passed",
                details={"active_shipment_ids": list(active_ids)},
            )
        return CheckResult(
            name="active_shipment_invariant",
            status="blocked",
            token="PRECLAIM_ACTIVE_SHIPMENT_PRESENT",
            message=(
                "PRECLAIM_ACTIVE_SHIPMENT_PRESENT: pre-claim requires zero active shipments"
            ),
            details={"active_shipment_ids": list(active_ids)},
        )

    if phase in ("post_claim", "lifecycle"):
        if count == 0:
            return CheckResult(
                name="active_shipment_invariant",
                status="blocked",
                token="LIFECYCLE_NO_ACTIVE_SHIPMENT",
                message="LIFECYCLE_NO_ACTIVE_SHIPMENT: expected exactly one active shipment",
                details={"active_shipment_ids": list(active_ids), "target_shipment_id": target},
            )
        if count > 1:
            return CheckResult(
                name="active_shipment_invariant",
                status="blocked",
                token="LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS",
                message="LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS: expected exactly one active shipment",
                details={"active_shipment_ids": list(active_ids), "target_shipment_id": target},
            )
        if active_ids[0] != target:
            return CheckResult(
                name="active_shipment_invariant",
                status="blocked",
                token="LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH",
                message=(
                    f"LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH: active shipment {active_ids[0]} "
                    f"does not match target {target}"
                ),
                details={"active_shipment_ids": list(active_ids), "target_shipment_id": target},
            )
        return CheckResult(
            name="active_shipment_invariant",
            status="passed",
            details={"active_shipment_ids": list(active_ids), "target_shipment_id": target},
        )

    if count == 0:
        return CheckResult(
            name="active_shipment_invariant",
            status="passed",
            details={"active_shipment_ids": list(active_ids), "target_shipment_id": target},
        )
    if count > 1:
        return CheckResult(
            name="active_shipment_invariant",
            status="blocked",
            token="AMBIENT_MULTIPLE_ACTIVE_SHIPMENTS",
            message="AMBIENT_MULTIPLE_ACTIVE_SHIPMENTS: ambient mode allows at most one active shipment",
            details={"active_shipment_ids": list(active_ids), "target_shipment_id": target},
        )
    active_id = active_ids[0]
    if target is None:
        return CheckResult(
            name="active_shipment_invariant",
            status="blocked",
            token="AMBIENT_TARGET_REQUIRED_FOR_ACTIVE_SHIPMENT",
            message=(
                f"AMBIENT_TARGET_REQUIRED_FOR_ACTIVE_SHIPMENT: active shipment {active_id} "
                "requires a resolvable ambient target"
            ),
            details={"active_shipment_ids": list(active_ids), "target_shipment_id": target},
        )
    if active_id != target:
        return CheckResult(
            name="active_shipment_invariant",
            status="blocked",
            token="AMBIENT_ACTIVE_SHIPMENT_MISMATCH",
            message=(
                f"AMBIENT_ACTIVE_SHIPMENT_MISMATCH: active shipment {active_id} "
                f"does not match target {target}"
            ),
            details={"active_shipment_ids": list(active_ids), "target_shipment_id": target},
        )
    return CheckResult(
        name="active_shipment_invariant",
        status="passed",
        details={"active_shipment_ids": list(active_ids), "target_shipment_id": target},
    )


@dataclass(frozen=True)
class DagReadinessResult:
    """Read-only ready-set + critical-path + downstream-dependents report.

    Computed over the SAME shipment-blocks graph
    ``FilesystemTopologyReaders.list_shipments()`` already reads
    (``ShipmentState.blocking_predecessor_ids``). ``compute_dag_readiness``
    reuses that reader for data access ONLY -- it performs no additional
    backlogit/git mutation and no new graph plumbing.

    ``critical_path`` is the LONGEST CHAIN in the blocks DAG by NODE COUNT
    (shipments are not time-weighted).

    ``ready_set`` contains ONLY LIVE ``queued`` shipments whose EVERY
    predecessor block has reached a genuine no-longer-blocking terminal
    closure (valid ``shipped``/``done`` per ``_is_shipped_terminal``). A
    ``queued`` OR ``active`` predecessor is UNFINISHED and BLOCKS its
    dependent (an ``active`` shipment is in-progress work -- NOT terminal
    and NOT non-blocking). A predecessor that is ``abandoned``, has
    ambiguous/duplicated live+archive provenance (the same corruption
    ``pipeline-topology``'s ``PREDECESSOR_STATE_AMBIGUOUS``/
    ``TARGET_STATE_AMBIGUOUS`` checks block on), or is simply
    unknown/absent from the supplied graph is treated as unfinished and
    fails closed (never terminal-ready) -- this applies both to a
    predecessor role and to the candidate shipment's own record. A
    shipment that is itself ``active``, ``shipped``, ``abandoned``, or
    archived-only (no live ``queued`` record) is NEVER a ready candidate,
    even when it has no blocking predecessors at all.

    Cycle detection is OWNED by this analyzer, not the reused reader: the
    reused ``ShipmentState``/reader performs no cycle detection of its own.
    On a detected cycle this function degrades safely -- it reports the
    cycle and NEVER fabricates a ``critical_path`` or ``ready_set`` (both
    are returned empty).
    """

    ready_set: tuple[str, ...] = ()
    critical_path: tuple[str, ...] = ()
    downstream_dependents: dict[str, tuple[str, ...]] = field(default_factory=dict)
    cycle_detected: bool = False
    cycle_nodes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready_set": list(self.ready_set),
            "critical_path": list(self.critical_path),
            "downstream_dependents": {
                node: list(dependents) for node, dependents in self.downstream_dependents.items()
            },
            "cycle_detected": self.cycle_detected,
            "cycle_nodes": list(self.cycle_nodes),
        }


def _dag_successors(shipment_map: dict[str, "ShipmentState"]) -> dict[str, list[str]]:
    """Build predecessor->dependent edges, restricted to known nodes only.

    A ``blocking_predecessor_ids`` entry that does not resolve to a known
    ``ShipmentState`` (unknown/absent from the supplied graph) never becomes
    a graph node here -- it is handled solely as a fail-closed "unfinished"
    signal by ``_all_predecessors_finished``, never as a phantom node in the
    critical-path/downstream-dependents graph.
    """
    successors: dict[str, list[str]] = {shipment_id: [] for shipment_id in shipment_map}
    for shipment in shipment_map.values():
        for predecessor_id in shipment.blocking_predecessor_ids:
            if predecessor_id in shipment_map:
                successors[predecessor_id].append(shipment.shipment_id)
    return {node: sorted(set(edges)) for node, edges in successors.items()}


def _dag_detect_cycle(
    shipment_map: dict[str, "ShipmentState"], successors: dict[str, list[str]]
) -> tuple[str, ...]:
    """Detect a cycle via DFS 3-color marking. Returns the cycle's node ids, or () if acyclic."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {node: WHITE for node in shipment_map}
    path: list[str] = []

    def visit(node: str) -> tuple[str, ...] | None:
        color[node] = GRAY
        path.append(node)
        for nxt in successors.get(node, ()):
            if color[nxt] == GRAY:
                start_index = path.index(nxt)
                return tuple(path[start_index:])
            if color[nxt] == WHITE:
                found = visit(nxt)
                if found is not None:
                    return found
        path.pop()
        color[node] = BLACK
        return None

    for node in sorted(shipment_map):
        if color[node] == WHITE:
            cycle = visit(node)
            if cycle is not None:
                return cycle
    return ()


def _dag_all_predecessors_finished(
    shipment: "ShipmentState", shipment_map: dict[str, "ShipmentState"]
) -> bool:
    for predecessor_id in shipment.blocking_predecessor_ids:
        predecessor = shipment_map.get(predecessor_id)
        if predecessor is None:
            # Unknown predecessor (not present in the supplied graph at
            # all): fail closed, never terminal-ready.
            return False
        if _has_ambiguous_shipment_records(predecessor):
            # A predecessor with BOTH a live queue record and an archive-
            # folder record is corrupted/duplicated provenance (the same
            # condition pipeline-topology's PREDECESSOR_STATE_AMBIGUOUS
            # blocks on). _is_shipped_terminal alone would short-circuit
            # to True on live_status == "shipped" and ignore this
            # ambiguity -- fail closed here, before the terminal check.
            return False
        if not _is_shipped_terminal(predecessor):
            return False
    return True


def _dag_longest_chain(
    shipment_map: dict[str, "ShipmentState"], successors: dict[str, list[str]]
) -> tuple[str, ...]:
    """Longest chain by NODE COUNT over an already-verified-acyclic graph."""
    if not shipment_map:
        return ()

    predecessors: dict[str, list[str]] = {node: [] for node in shipment_map}
    for node, edges in successors.items():
        for dependent in edges:
            predecessors[dependent].append(node)

    in_degree = {node: len(predecessors[node]) for node in shipment_map}
    ready = sorted(node for node, degree in in_degree.items() if degree == 0)
    order: list[str] = []
    remaining = dict(in_degree)
    while ready:
        ready.sort()
        node = ready.pop(0)
        order.append(node)
        for nxt in successors.get(node, ()):
            remaining[nxt] -= 1
            if remaining[nxt] == 0:
                ready.append(nxt)

    longest_len: dict[str, int] = {node: 1 for node in shipment_map}
    longest_prev: dict[str, str | None] = {node: None for node in shipment_map}
    for node in order:
        # NOTE on determinism: ties in longest_len are resolved implicitly,
        # not by an explicit id comparison here. `order` is a Kahn's-
        # algorithm topological order that always pops the lowest-id
        # zero-indegree node first, so when two predecessors reach the same
        # `candidate` length for `nxt`, the strict `>` below keeps whichever
        # one was visited (and therefore updated `nxt`) FIRST in that
        # deterministic order -- i.e. the lowest id among the tied
        # predecessors. If this DP loop is ever restructured, preserve
        # either the strict `>` + this traversal order, or add an explicit
        # id tie-break, to keep the result stable across runs.
        for nxt in successors.get(node, ()):
            candidate = longest_len[node] + 1
            if candidate > longest_len[nxt]:
                longest_len[nxt] = candidate
                longest_prev[nxt] = node

    best_node = min(shipment_map, key=lambda node: (-longest_len[node], node))
    chain: list[str] = []
    node: str | None = best_node
    while node is not None:
        chain.append(node)
        node = longest_prev[node]
    chain.reverse()
    return tuple(chain)


def _dag_downstream_dependents(
    shipment_map: dict[str, "ShipmentState"], successors: dict[str, list[str]]
) -> dict[str, tuple[str, ...]]:
    """Transitive closure of dependents per node (every node that directly or
    indirectly has this node as a blocking predecessor)."""
    result: dict[str, tuple[str, ...]] = {}
    for start in shipment_map:
        seen: set[str] = set()
        stack = list(successors.get(start, ()))
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(successors.get(node, ()))
        result[start] = tuple(sorted(seen))
    return result


def compute_dag_readiness(shipments: Sequence[ShipmentState]) -> DagReadinessResult:
    """Pure, read-only ready-set + critical-path + downstream-dependents report.

    See ``DagReadinessResult`` for the full contract. Reuses the existing
    shipment-blocks reader (``ShipmentState``) for data access only; this
    function performs no backlogit/git mutation and owns its own cycle
    detection (110.001-T AC5).
    """
    shipment_map = _shipment_map(shipments)
    successors = _dag_successors(shipment_map)

    cycle_nodes = _dag_detect_cycle(shipment_map, successors)
    if cycle_nodes:
        return DagReadinessResult(cycle_detected=True, cycle_nodes=cycle_nodes)

    ready_set = tuple(
        sorted(
            shipment_id
            for shipment_id, shipment in shipment_map.items()
            if _normalized_live_status(shipment) == "queued"
            and not _has_ambiguous_shipment_records(shipment)
            and _dag_all_predecessors_finished(shipment, shipment_map)
        )
    )
    critical_path = _dag_longest_chain(shipment_map, successors)
    downstream_dependents = _dag_downstream_dependents(shipment_map, successors)

    return DagReadinessResult(
        ready_set=ready_set,
        critical_path=critical_path,
        downstream_dependents=downstream_dependents,
        cycle_detected=False,
        cycle_nodes=(),
    )


@dataclass(frozen=True)
class NextEligibleResult:
    """Pure, read-only resumption-cursor advisory over an already-computed
    ``DagReadinessResult`` and the same ``ShipmentState`` enumeration
    (115.001-T, 115-F).

    This analyzer implements SIX of the gate's SEVEN observable outcomes --
    outcomes 2-7 in the canonical gate-level numbering: ``cycle_detected``,
    ``ambiguous_provenance``, ``multi_active_anomaly``, ``resume_active``,
    ``ready_set_head``, ``no_candidates``. Outcome 1, ``degraded``, is
    CLI-ONLY (115.002-T): it is synthesized deterministically in the
    ``BacklogUnavailableError`` handler BEFORE this analyzer is ever
    invoked, because on that path neither a ``shipments`` tuple nor a
    ``DagReadinessResult`` exists. This analyzer performs NO I/O and NO
    backlogit/git mutation on ANY branch, including every anomaly branch.

    RESOLUTION ORDER (anomaly-first, over the FULL UNFILTERED shipment
    enumeration -- never an early-narrowed subset):
      2. ``readiness.cycle_detected`` -> null cursor / ``cycle_detected``.
      3. ANY shipment with ambiguous live+archive provenance (reused
         ``_has_ambiguous_shipment_records``) -> null cursor /
         ``ambiguous_provenance`` + offending ids. Checked BEFORE
         active/ready partitioning, so a single ambiguous-but-``active``
         shipment reports ``ambiguous_provenance``, never
         ``resume_active``, and is never folded into
         ``multi_active_anomaly`` or ``no_candidates``.
      4. More than one ``active`` shipment -> null cursor /
         ``multi_active_anomaly`` + offending ids. Never picks a winner and
         never falls through to the ready-set.
      5. Exactly one ``active`` shipment -> that id is the cursor, reason
         ``resume_active``. No tie-break applies (nothing to tie-break with
         exactly one).
      6. Zero ``active`` -> tie-broken head of ``readiness.ready_set``,
         reason ``ready_set_head``. Tie-break: DESC
         ``len(readiness.downstream_dependents[id])``, then ASC shipment
         id. Shipment ids are unique so the ordering is TOTAL -- never
         ambiguous, never dependent on dict/filesystem iteration order.
         This tie-break applies to THIS branch ONLY.
      7. Zero ``active`` and an empty ``ready_set`` -> null cursor /
         ``no_candidates``.

    ``next_eligible_detail`` (via ``to_dict()``) always exposes BOTH
    ``candidate_ids`` and ``offending_ids`` as arrays -- empty arrays when
    not applicable, never ``{}`` and never ``null``. Per the normative
    detail-shape contract: ``candidate_ids`` is populated ONLY for
    ``ready_set_head`` (the tie-broken ordered ``ready_set``); it is empty
    for every other branch, including ``resume_active`` (the single
    resolved cursor is reported via ``next_eligible`` alone, with nothing
    to tie-break). ``offending_ids`` is populated ONLY for
    ``multi_active_anomaly`` and ``ambiguous_provenance``; it is empty for
    every other branch, including ``cycle_detected`` (whose participating
    nodes are already reported via the Phase 1 ``cycle_nodes`` field, not
    duplicated here).
    """

    next_eligible: str | None
    next_eligible_reason: str
    candidate_ids: tuple[str, ...] = ()
    offending_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "next_eligible": self.next_eligible,
            "next_eligible_reason": self.next_eligible_reason,
            "next_eligible_detail": {
                "candidate_ids": list(self.candidate_ids),
                "offending_ids": list(self.offending_ids),
            },
        }


def compute_next_eligible(
    shipments: Sequence[ShipmentState],
    readiness: DagReadinessResult,
) -> NextEligibleResult:
    """Pure, read-only resumption-cursor analyzer. See ``NextEligibleResult``
    for the full branch/ordering/tie-break contract.

    Consumes already-read ``ShipmentState`` values and the existing
    ``DagReadinessResult`` -- performs NO I/O and NO mutation whatsoever.
    Accepts ONLY successfully-read data: there is no ``is_degraded``/
    ``degraded`` sentinel input, by design (115.001-T AC10). A caller
    cannot express "backlog unreachable" to this function.
    """
    # Branch 2 (gate outcome 2): cycle_detected -- highest priority, checked
    # before any provenance/active/ready partitioning. offending_ids is
    # empty here per the normative detail-shape contract (014-DL plan):
    # offending_ids is populated ONLY for multi_active_anomaly or
    # ambiguous_provenance. The cycle's participating nodes are already
    # reported via readiness.cycle_nodes on the Phase 1 payload -- this
    # analyzer does not duplicate them into next_eligible_detail.
    if readiness.cycle_detected:
        return NextEligibleResult(
            next_eligible=None,
            next_eligible_reason="cycle_detected",
            candidate_ids=(),
            offending_ids=(),
        )

    # Branch 3 (gate outcome 3): ambiguous live/archive provenance, over the
    # FULL UNFILTERED enumeration -- checked BEFORE active/ready
    # partitioning so an active-but-ambiguous record is never silently
    # excluded or misreported as resume_active/multi_active_anomaly.
    ambiguous_ids = tuple(
        sorted(shipment.shipment_id for shipment in shipments if _has_ambiguous_shipment_records(shipment))
    )
    if ambiguous_ids:
        return NextEligibleResult(
            next_eligible=None,
            next_eligible_reason="ambiguous_provenance",
            candidate_ids=(),
            offending_ids=ambiguous_ids,
        )

    # Branches 4-5 (gate outcomes 4-5): partition by active count. Reuse
    # _normalized_live_status rather than re-deriving "active" semantics.
    active_ids = tuple(
        sorted(shipment.shipment_id for shipment in shipments if _normalized_live_status(shipment) == "active")
    )
    if len(active_ids) > 1:
        return NextEligibleResult(
            next_eligible=None,
            next_eligible_reason="multi_active_anomaly",
            candidate_ids=(),
            offending_ids=active_ids,
        )
    if len(active_ids) == 1:
        # candidate_ids is populated ONLY for ready_set_head (the
        # tie-broken ordered candidate list); it is empty here per the
        # normative detail-shape contract (014-DL plan) -- resume_active
        # has nothing to tie-break among, so there is no candidate list to
        # report, only the single resolved cursor in next_eligible itself.
        return NextEligibleResult(
            next_eligible=active_ids[0],
            next_eligible_reason="resume_active",
            candidate_ids=(),
            offending_ids=(),
        )

    # Branch 6 (gate outcome 6): zero active, non-empty ready_set. Tie-break
    # applies to THIS branch only: DESC downstream fan-out, then ASC id.
    # readiness.downstream_dependents/ready_set are already computed by the
    # reused compute_dag_readiness -- no new graph traversal is added here.
    if readiness.ready_set:
        def _tie_break_key(shipment_id: str) -> tuple[int, str]:
            fan_out = len(readiness.downstream_dependents.get(shipment_id, ()))
            return (-fan_out, shipment_id)

        head = min(readiness.ready_set, key=_tie_break_key)
        return NextEligibleResult(
            next_eligible=head,
            next_eligible_reason="ready_set_head",
            candidate_ids=tuple(readiness.ready_set),
            offending_ids=(),
        )

    # Branch 7 (gate outcome 7): zero active, empty ready_set.
    return NextEligibleResult(
        next_eligible=None,
        next_eligible_reason="no_candidates",
        candidate_ids=(),
        offending_ids=(),
    )


def evaluate(
    topology_input: TopologyInput,
    readers: TopologyReaders | None = None,
) -> TopologyResult:
    """Evaluate the topology gate with injected read-only readers."""
    invalid = _validate_input(topology_input)
    if invalid is not None:
        return invalid

    resolved_phase = _resolve_phase(topology_input)
    bound_readers = readers or _NullReaders()
    try:
        target_resolution_shipments = tuple(bound_readers.list_shipments())
    except BacklogUnavailableError as exc:
        return _backlog_unavailable_result(
            topology_input,
            resolved_phase,
            _normalize_target(topology_input.target_shipment_id),
            exc,
        )
    target, target_error = _resolve_target_shipment(
        topology_input,
        target_resolution_shipments,
        bound_readers,
    )
    if target_error is not None:
        return _invalid_result(topology_input, resolved_phase, target_error)

    if resolved_phase == "post_claim":
        return _evaluate_post_claim(topology_input, target, bound_readers)

    return _evaluate_core(
        topology_input,
        resolved_phase,
        target,
        bound_readers,
        target_resolution_shipments,
    )
