"""One-entry harness surface resolver: result contract, records and classification.

Unit B of the ship lifecycle release units plan
(``docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md``). RED-phase
stubs for task B1 (188.001-T).
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from autoharness.harness_read import ReadErrorCode

SCHEMA_VERSION = "1.0.0"

_B1 = "AHLC_B1_RESOLUTION_CONTRACT"


class ResolutionState(enum.Enum):
    HARNESS_READY = "HARNESS_READY"
    NO_HARNESS = "NO_HARNESS"
    UNRESOLVED = "UNRESOLVED"


STATE_EXIT: Mapping[ResolutionState, int] = MappingProxyType({})


class SurfaceState(enum.Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    STALE = "STALE"
    INVALID = "INVALID"


class ReadStage(enum.Enum):
    SHIPMENT_CANDIDATE = "shipment_queue_or_archive_candidate"
    MEMBER_CANDIDATE = "member_queue_or_archive_candidate"
    MANIFEST = "manifest_read"
    TEMPLATE = "template_read"
    INSTALLED = "installed_file_read"
    CANDIDATE_RECHECK = "candidate_ledger_recheck"
    SURFACE_RECHECK = "surface_recheck"


@dataclass(frozen=True)
class ReasonSpec:
    code: str
    reason_class: str
    state: ResolutionState
    exit_code: int
    surface_state: SurfaceState | None


REASON_REGISTRY: tuple[ReasonSpec, ...] = ()


@dataclass(frozen=True)
class SurfaceRow:
    surface_id: str
    installed_path: str
    template: str
    state: SurfaceState
    reason_code: str


@dataclass(frozen=True)
class Declaration:
    member_id: str
    surface_id: str


@dataclass(frozen=True)
class ResolutionResult:
    schema_version: str
    state: ResolutionState
    reason_code: str
    exit_code: int
    shipment_id: str | None
    backlog_root: str | None
    surfaces: tuple[SurfaceRow, ...]
    declarations: tuple[Declaration, ...]
    inputs_sha256: str
    diagnostics: tuple[str, ...]

    def to_document(self) -> dict[str, object]:
        raise NotImplementedError(f"{_B1}:test_to_document_emits_schema_valid_document")


def reason_spec(code: str) -> ReasonSpec:
    raise NotImplementedError(f"{_B1}:test_reason_spec_binds_class_state_exit")


def read_limit_diagnostics(code: ReadErrorCode, stage: ReadStage) -> tuple[str, str]:
    raise NotImplementedError(f"{_B1}:test_read_limit_diagnostics_pairs_code_and_stage")


def task_id_sort_key(member_id: str) -> tuple[object, ...]:
    raise NotImplementedError(f"{_B1}:test_task_id_sort_key_orders_by_numeric_parts")


def make_result(
    reason_code: str,
    *,
    shipment_id: str | None,
    backlog_root: str | None,
    inputs_sha256: str,
    surfaces: Sequence[SurfaceRow] = (),
    declarations: Sequence[Declaration] = (),
    diagnostics: Sequence[str] = (),
) -> ResolutionResult:
    raise NotImplementedError(f"{_B1}:test_make_result_derives_outcome_and_enforces_contract")
