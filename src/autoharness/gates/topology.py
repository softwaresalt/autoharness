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
from dataclasses import dataclass, field
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
        return ""

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

    return _pass_result(topology_input, resolved_phase, target, checks)
