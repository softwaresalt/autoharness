"""Deterministic shipment/worktree topology gate.

This module hosts the read-only, fail-closed topology checks that guard shipment
claim, lifecycle, and ambient hook/CI execution. The core invariant work is kept
inside ``autoharness.gates`` so it can evolve independently of install/tune
surfaces.

Local limitation: the active-shipment scan and detect-before consistency scan can
only observe the current checkout. They are deliberately detect-before guards, not
serialization, leases, or cross-machine locks. backlogit provides no workspace-
wide claim lock, so concurrent work in another checkout can still race this gate.
"""

from __future__ import annotations

from collections.abc import Sequence
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
_BRANCH_KIND_PREFIXES = ("feat/", "chore/")


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
    import yaml

    raw = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", raw, flags=re.DOTALL)
    if not match:
        return {}
    loaded = yaml.safe_load(match.group(1))
    return loaded if isinstance(loaded, dict) else {}


def _tuple_of_str(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
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
        live_status = queue_fm.get("status") if isinstance(queue_fm.get("status"), str) else None
        archived = _archived_status(archive_fm)
        return ArtifactState(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            live_status=str(live_status).strip().lower() if isinstance(live_status, str) and live_status.strip() else None,
            archived_status=archived,
        )

    def list_shipments(self) -> Sequence[ShipmentState]:
        records: dict[str, dict[str, Any]] = {}
        for folder, is_archive in (("queue", False), ("archive", True)):
            base = self.backlog_dir / folder
            if not base.exists():
                continue
            for candidate in sorted(base.glob("*.md")):
                fm = _frontmatter(candidate)
                if fm.get("artifact_type") != "shipment":
                    continue
                shipment_id = fm.get("id")
                if not isinstance(shipment_id, str) or not shipment_id.strip():
                    continue
                record = records.setdefault(shipment_id, {"shipment_id": shipment_id})
                title = fm.get("title")
                if isinstance(title, str) and title.strip():
                    record["title"] = title.strip()
                if is_archive:
                    record["archived_status"] = _archived_status(fm)
                else:
                    status = fm.get("status")
                    if isinstance(status, str) and status.strip():
                        record["live_status"] = status.strip().lower()
                    custom_fields = fm.get("custom_fields")
                    items = ()
                    if isinstance(custom_fields, dict):
                        items = _tuple_of_str(custom_fields.get("items"))
                    record["manifest_item_ids"] = items
                    record["blocking_predecessor_ids"] = _tuple_of_str(fm.get("dependencies"))
        return tuple(
            ShipmentState(
                shipment_id=str(record.get("shipment_id", "")),
                title=str(record.get("title", record.get("shipment_id", ""))),
                live_status=record.get("live_status"),
                archived_status=record.get("archived_status"),
                manifest_item_ids=tuple(record.get("manifest_item_ids", ()) or ()),
                blocking_predecessor_ids=tuple(record.get("blocking_predecessor_ids", ()) or ()),
            )
            for record in sorted(records.values(), key=lambda item: str(item.get("shipment_id", "")))
        )

    def read_artifact(self, artifact_id: str) -> ArtifactState | None:
        return self._artifact_from_paths(artifact_id)

    def current_branch(self) -> str:
        return _run_git(["git", "--no-pager", "branch", "--show-current"], self.workspace) or "main"

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
            if isinstance(compaction, str) and compaction.strip().lower() in {"done", "ready"}:
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

    def closure_complete(self, shipment_id: str) -> bool | None:
        return None


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


def _is_stage_spike_research_worktree(entry: WorktreeEntry) -> bool:
    branch = (entry.branch or "").lower()
    path_name = Path(entry.path).name.lower()
    branch_ok = branch.startswith("spike/") or branch.startswith("research/")
    path_ok = "stage-spike" in path_name or "stage-research" in path_name
    return branch_ok and path_ok


def _worktree_uniqueness_check(readers: TopologyReaders) -> CheckResult:
    entries = parse_worktree_porcelain(readers.worktree_porcelain())
    implementation = [entry for entry in entries if not _is_stage_spike_research_worktree(entry)]
    if len(implementation) == 1:
        return CheckResult(
            name="worktree_topology",
            status="passed",
            token="WORKTREE_TOPOLOGY_OK",
            details={
                "implementation_worktrees": [entry.path for entry in implementation],
                "spike_research_worktrees": [entry.path for entry in entries if _is_stage_spike_research_worktree(entry)],
            },
        )
    if len(implementation) == 0:
        return CheckResult(
            name="worktree_topology",
            status="blocked",
            token="NO_IMPLEMENTATION_WORKTREE",
            message="NO_IMPLEMENTATION_WORKTREE: topology gate requires exactly one implementation worktree",
            details={"spike_research_worktrees": [entry.path for entry in entries if _is_stage_spike_research_worktree(entry)]},
        )
    return CheckResult(
        name="worktree_topology",
        status="blocked",
        token="MULTIPLE_IMPLEMENTATION_WORKTREES",
        message="MULTIPLE_IMPLEMENTATION_WORKTREES: topology gate allows exactly one implementation worktree",
        details={
            "implementation_worktrees": [entry.path for entry in implementation],
            "spike_research_worktrees": [entry.path for entry in entries if _is_stage_spike_research_worktree(entry)],
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
        if explicit not in shipment_map and shipment_map:
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


def _is_shipped_terminal(shipment: ShipmentState) -> bool:
    if shipment.live_status == "shipped":
        return True
    return shipment.archived_status in {"shipped", "done"}


def _shipment_readiness_check(
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
    shipments = tuple(bound_readers.list_shipments())
    target, target_error = _resolve_target_shipment(topology_input, shipments, bound_readers)
    if target_error is not None:
        return _invalid_result(topology_input, resolved_phase, target_error)

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

    readiness_check = _shipment_readiness_check(target, shipments, bound_readers)
    checks.append(readiness_check)
    if readiness_check.status == "blocked":
        return _blocked_result(topology_input, resolved_phase, target, readiness_check)

    return _pass_result(topology_input, resolved_phase, target, checks)
