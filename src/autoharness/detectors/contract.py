"""Detector node, evidence, and result contracts for pre-review gates."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

NODE_ID_PATTERN = re.compile(r"^det:(?P<domain>[A-Z0-9-]+)/(?P<detector_id>[A-Z0-9-]+)@(?P<version>[0-9]+)$")
DETECTOR_STATUS_VALUES = (
    "passed",
    "failed",
    "insufficient_evidence",
    "blocked_upstream",
    "not_applicable",
    "skipped",
    "waived",
    "invalid",
)
_DETECTOR_STATUS_SET = frozenset(DETECTOR_STATUS_VALUES)
_SEVERITIES = frozenset({"critical", "high", "medium", "low"})
_REMEDIATION_AUTHORITIES = frozenset({"none", "ship", "stage", "operator"})
_REMEDIATION_CLASSES = frozenset(
    {
        "auto_fix_safe",
        "guided_fix",
        "regenerate",
        "require_plan_revision",
        "require_human_review",
        "policy_halt",
    }
)
REPORT_ONLY_MODE = "report_only"


ProducerFn = Callable[["NodeSpec", Any], "Evidence"]
ValidatorFn = Callable[["NodeSpec", Mapping[str, "Evidence"], Any], "NodeResult"]


@dataclass(frozen=True)
class ApplicabilitySpec:
    changed_paths_any: tuple[str, ...] = ()
    shipment_has_items_of_type: tuple[str, ...] = ()
    workspace_surfaces_any: tuple[str, ...] = ()
    always: bool = False


@dataclass(frozen=True)
class ProducerSpec:
    kind: str
    ref: str
    tool_version_dims: tuple[str, ...] = ()
    handler: ProducerFn | None = None


@dataclass(frozen=True)
class ValidatorSpec:
    ref: str
    consumes: tuple[str, ...] = ()
    handler: ValidatorFn | None = None


@dataclass(frozen=True)
class RemediationSpec:
    class_name: str
    hint: str = ""
    target_refs: tuple[str, ...] = ()
    authority: str = "none"

    def __post_init__(self) -> None:
        if self.class_name not in _REMEDIATION_CLASSES:
            raise ValueError(f"unsupported remediation class: {self.class_name!r}")
        if self.authority not in _REMEDIATION_AUTHORITIES:
            raise ValueError(f"unsupported remediation authority: {self.authority!r}")


@dataclass(frozen=True)
class NodeSpec:
    node_id: str
    domain: str
    detector_id: str
    version: str
    applies_when: ApplicabilitySpec
    producer: ProducerSpec
    validator: ValidatorSpec
    depends_on: tuple[str, ...] = ()
    severity: str = "medium"
    mode: str = REPORT_ONLY_MODE
    remediation: RemediationSpec = field(
        default_factory=lambda: RemediationSpec(class_name="guided_fix", authority="none")
    )

    def __post_init__(self) -> None:
        match = NODE_ID_PATTERN.fullmatch(self.node_id)
        if match is None:
            raise ValueError(f"invalid node_id: {self.node_id!r}")
        if match.group("domain") != self.domain:
            raise ValueError("node_id domain does not match NodeSpec.domain")
        if match.group("detector_id") != self.detector_id:
            raise ValueError("node_id detector_id does not match NodeSpec.detector_id")
        if match.group("version") != self.version:
            raise ValueError("node_id version does not match NodeSpec.version")
        if self.severity not in _SEVERITIES:
            raise ValueError(f"unsupported detector severity: {self.severity!r}")
        if self.mode != REPORT_ONLY_MODE:
            raise ValueError(f"unsupported detector mode: {self.mode!r}")


@dataclass(frozen=True)
class Evidence:
    node_id: str
    payload: Any
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NodeResult:
    name: str
    status: str
    token: str | None = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    excluded_by: str | None = None

    def __post_init__(self) -> None:
        if self.status not in _DETECTOR_STATUS_SET:
            raise ValueError(f"unsupported detector status: {self.status!r}")

    @property
    def verdict(self) -> str:
        return self.status

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "token": self.token,
            "message": self.message,
            "details": self.details,
            "provenance": self.provenance,
            "excluded_by": self.excluded_by,
        }


def status_exit_code(status: str) -> int:
    if status not in _DETECTOR_STATUS_SET:
        raise ValueError(f"unsupported detector status: {status!r}")
    return 2 if status == "invalid" else 0
