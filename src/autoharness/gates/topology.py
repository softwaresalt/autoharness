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
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

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
_ARTIFACT_ID_PATTERN = re.compile(r"^\d+(?:\.\d+)*-[A-Za-z]+$")
_BRANCH_KIND_PREFIXES = ("feat/", "chore/")
_POST_CLAIM_WRAP_TOKENS = frozenset({
    "SHIPMENT_STATE_INCONSISTENT",
    "LIFECYCLE_NO_ACTIVE_SHIPMENT",
    "LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS",
    "LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH",
})


class BacklogUnavailableError(RuntimeError):
    def __init__(self, path: Path, reason: str) -> None:
        self.path = str(path)
        self.reason = reason
        super().__init__(f"{reason}: {path}")


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
    def primary_token(self) -> str | None:
        for check in self.checks:
            if check.status == "blocked" and check.token:
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


def _tuple_of_str(
    value: Any,
    *,
    source_path: Path | None = None,
    field_name: str = "",
) -> tuple[str, ...]:
    """Coerce a frontmatter field to a tuple of nonblank string ids.

    A missing field (``None``) legitimately means "none declared" and
    resolves to an empty tuple. But a field that IS present with a
    non-sequence value (e.g. ``dependencies: "100-S"`` as a bare string, or
    ``custom_fields.items: 42``) must never be silently normalized to an
    empty tuple: that would drop an actual blocking predecessor or hide
    active/done manifest tasks from the detect-before-consistency scan,
    letting corrupted backlog state pass fail-closed checks. When
    ``source_path`` is provided, a present-but-wrong-shaped value raises
    BacklogUnavailableError instead of coercing.
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
    return tuple(str(item) for item in value if str(item).strip())



def _archived_status(frontmatter: dict[str, Any]) -> str | None:
    value = frontmatter.get("archived_status")
    return str(value).strip().lower() if isinstance(value, str) and value.strip() else None


class FilesystemTopologyReaders:
    """Default read-only topology readers backed by the local workspace."""

    def __init__(self, workspace: Path | str = ".") -> None:
        self.workspace = Path(workspace)
        self.backlog_dir = self.workspace / ".backlogit"

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
                record = records.setdefault(shipment_id.strip(), {"shipment_id": shipment_id.strip()})
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
            compaction = fm.get("compaction_status") or fm.get("compaction")
            if isinstance(compaction, str) and compaction.strip().lower() in {"done", "degraded"}:
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

        branch_check = _branch_ownership_check(target, shipments, bound_readers)
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
        try:
            revalidation_shipments = tuple(bound_readers.list_shipments())
        except BacklogUnavailableError as exc:
            return _backlog_unavailable_result(topology_input, "post_claim", target, exc)
        revalidation = _evaluate_core(
            topology_input,
            "pre_claim",
            target,
            bound_readers,
            revalidation_shipments,
        )
        if revalidation.exit_code != 0:
            return _claim_verify_failed(
                topology_input,
                target,
                revalidation,
                reason="pre-claim revalidation did not pass before the bounded post-claim retry",
            )
        try:
            retry_shipments = tuple(bound_readers.list_shipments())
        except BacklogUnavailableError as exc:
            return _backlog_unavailable_result(topology_input, "post_claim", target, exc)
        retry = _evaluate_core(topology_input, "post_claim", target, bound_readers, retry_shipments)
        if retry.exit_code == 0:
            return retry
        return _claim_verify_failed(
            topology_input,
            target,
            retry,
            reason="target shipment did not become the sole active shipment after the bounded retry",
        )

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


def _branch_ownership_check(
    target: str | None,
    shipments: Sequence[ShipmentState],
    readers: TopologyReaders,
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
    default_branch = _normalize_branch_name(readers.default_branch())
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
            },
        )

    if current_branch == default_branch:
        return CheckResult(
            name="branch_ownership",
            status="passed",
            token="BRANCH_CREATE_ELIGIBLE",
            message=(
                f"BRANCH_CREATE_ELIGIBLE: current branch {current_branch} is the default branch for target {target}"
            ),
            details={"current_branch": current_branch, "expected_branches": list(canonical)},
        )

    if _resolve_shipment_from_branch(current_branch, (shipment,)) == target:
        return CheckResult(
            name="branch_ownership",
            status="passed",
            token="BRANCH_OK",
            message=f"BRANCH_OK: current branch {current_branch} matches target {target}",
            details={"current_branch": current_branch, "expected_branches": list(canonical)},
        )

    return CheckResult(
        name="branch_ownership",
        status="blocked",
        token="BRANCH_MISMATCH",
        message=(
            f"BRANCH_MISMATCH: current branch {current_branch} does not match target {target}"
        ),
        details={"current_branch": current_branch, "expected_branches": list(canonical)},
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
