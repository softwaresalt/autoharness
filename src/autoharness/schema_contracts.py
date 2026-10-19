"""Schema contract metadata, compatibility helpers, and migration planning."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml


LEGACY_CAPABILITY_PACK_ERROR_RE = re.compile(
    r"^((?:[A-Za-z0-9_]+\.)*(?:capability_packs\.\d+|capability_pack_overlays\.\d+\.pack"
    r"|recommendation_reasons\.capability_packs\.\d+\.item)): '([^']+)' is not one of"
)
LEGACY_DRIFT_CATEGORY_ERROR_RE = re.compile(
    r"^drift_report\.changes\.\d+\.category: '([^']+)' is not one of"
)
MISSING_SCHEMA_VERSION_ERROR_RE = re.compile(
    r"^(?:<root>|schema_version): 'schema_version' is a required property$"
)

LEGACY_UNSUPPORTED_PACKS = {"circuit-breaker", "concurrency"}
LEGACY_DRIFT_CATEGORIES = {
    "interrupted_tuning",
    "deleted_artifact",
    "deprecated_agents_removed",
    "existing_modified",
    "gitignore_updated",
}


@dataclass(frozen=True)
class RemovedPackInfo:
    """Removal metadata for a capability pack that is no longer supported."""

    pack: str
    removed_in: str
    overlay_instruction_path: str
    overlay_template_path: str
    profile_block_key: str


REMOVED_PACK_WARNING_KIND = "removed-capability-pack"
REMOVED_PACK_PROPOSAL_ID = "remove-retired-capability-pack"

# Retired packs stay recognizable so documents that still list them degrade to a
# warning and a migration proposal instead of a schema blocker (209-F/216-S).
REMOVED_CAPABILITY_PACKS: Mapping[str, RemovedPackInfo] = MappingProxyType(
    {
        "agent-intercom": RemovedPackInfo(
            pack="agent-intercom",
            removed_in="209-F",
            overlay_instruction_path=".github/instructions/agent-intercom.instructions.md",
            overlay_template_path="templates/instructions/agent-intercom.instructions.md.tmpl",
            profile_block_key="agent_intercom",
        ),
    }
)


SCHEMA_CONTRACTS: dict[str, dict[str, Any]] = {
    "execution-epoch": {
        "contract_name": "execution-epoch",
        "schema_file": "execution-epoch.schema.json",
        "versioned_schema_dir": "execution-epoch",
        "current_version": "1.1.0",
        "known_versions": ("1.1.0",),
        "compatibility_model": "versioned-contract",
    },
    "tool-telemetry-event": {
        "contract_name": "tool-telemetry-event",
        "schema_file": "tool-telemetry-event.schema.json",
        "versioned_schema_dir": "tool-telemetry-event",
        # Schema-version decision (108.002-T/108.004-T, revised in PR #294
        # review-fix cycle 2): `task_complexity_label` + `complexity_source`
        # are new top-level properties on a schema with `additionalProperties:
        # false`. Even though both are nullable, adding them in place would
        # make the SAME "1.0.0" version identifier mean two different byte-
        # level contracts (an old 1.0.0 validator rejects any record
        # containing the new properties; a patched-in-place 1.0.0 validator
        # accepts them) -- an ambiguous version identifier. Bumped to 1.1.0
        # instead: the published `1.0.0.schema.json` is restored to its
        # original pre-108-F bytes (never mutated in place) and a new
        # `1.1.0.schema.json` mirror carries the additive fields. The root
        # schema and the runtime `SCHEMA_VERSION` constant both track current
        # (1.1.0); `ToolTelemetryEvent.from_mapping` normalizes legacy 1.0.0
        # payloads forward on read (mirroring the execution-epoch v1.0->v1.1
        # legacy-normalization pattern) so old journal entries remain
        # readable.
        "current_version": "1.1.0",
        "known_versions": ("1.0.0", "1.1.0"),
        "compatibility_model": "versioned-contract",
    },
    "manifest": {
        "contract_name": "harness-manifest",
        "schema_file": "harness-manifest.schema.json",
        "versioned_schema_dir": "harness-manifest",
        # Schema-version decision (209-F/216-S U3): removing the retired
        # `agent-intercom` pack from both pack enums is a restrictive change, so it
        # is minted as 1.1.0; the 0.9.0 and 1.0.0 mirrors stay byte-identical
        # (pinned by tests/test_schema_contract_removed_pack_manifest.py).
        "current_version": "1.1.0",
        "known_versions": ("0.9.0", "1.0.0", "1.1.0"),
        "compatibility_model": "versioned-contract",
    },
    "config": {
        "contract_name": "harness-config",
        "schema_file": "harness-config.schema.json",
        "versioned_schema_dir": "harness-config",
        # Schema-version decision (F02FD596/113.001-T, revised in PR #316
        # review-fix cycle, mirroring the tool-telemetry-event v1.0->v1.1
        # precedent): adding nested `stage.escalation`/`ship.escalation`
        # properties (each `additionalProperties: false`) plus a
        # model_routing-level `not` ambiguity constraint changes what a
        # document validating under "1.0.0" means -- an old 1.0.0 validator
        # rejects a document using the new nested escalation override while
        # a patched-in-place 1.0.0 validator accepts it, making the same
        # version identifier mean two different byte-level contracts.
        # Bumped to 1.1.0 instead: the published `1.0.0.schema.json` is
        # restored to its exact original pre-PR-#316 bytes (never mutated in
        # place) and a new `1.1.0.schema.json` mirror carries the nested
        # per-role escalation additions. The root schema tracks current
        # (1.1.0). An installed config with schema_version: 1.0.0 continues
        # to validate against the untouched 1.0.0 contract (no nested
        # escalation override available); adopting nested per-role
        # escalation requires bumping schema_version to 1.1.0.
        # D-C5 exception (194-F/200-S): the optional, additive `context_tier`
        # route/frontmatter field was added to the already-published 1.1.0
        # schema IN PLACE (no 1.2.0 bump; configs without the field stay
        # valid). A config that uses context_tier therefore requires an
        # autoharness release that ships this 1.1.0 revision.
        # Schema-version decision (208-F/215-S B5, 040-DL D1/D11): closing
        # `model_routing` with `additionalProperties: false` over an explicit
        # allowlist and adding the `routes` catalog and `bindings` map makes a
        # document that validates under "1.1.0" (an unknown or inert
        # `model_routing` key included) invalid under the new contract, so
        # editing the published `1.1.0.schema.json` in place would give one
        # version identifier two byte-level meanings (the bug class in
        # docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md).
        # Bumped to 1.2.0 instead: `1.1.0.schema.json` stays byte-identical
        # (pinned by tests/test_harness_config_schema_versioning.py) and the
        # root schema now tracks the `1.2.0.schema.json` mirror. An installed
        # config with schema_version: 1.1.0 continues to validate against the
        # untouched 1.1.0 mirror; adopting routes/bindings requires bumping
        # schema_version to 1.2.0.
        # Schema-version decision (209-F/216-S U4, shipped after 208-F/215-S so the
        # slot is 1.2.0 + 1): removing the retired `agent-intercom` pack from the
        # `capability_packs` enum is a restrictive change, so it is minted as 1.3.0.
        # The 0.9.0/1.0.0/1.1.0/1.2.0 mirrors stay byte-identical (pinned by
        # tests/test_schema_contract_removed_pack_config.py); a config pinned to
        # any of them that lists the retired pack keeps validating.
        "current_version": "1.3.0",
        "known_versions": ("0.9.0", "1.0.0", "1.1.0", "1.2.0", "1.3.0"),
        "compatibility_model": "versioned-contract",
    },
    "profile": {
        "contract_name": "workspace-profile",
        "schema_file": "workspace-profile.schema.json",
        "versioned_schema_dir": "workspace-profile",
        # Schema-version decision (209-F/216-S U2): removing the retired
        # `agent-intercom` pack from both pack enums (and its `agent_intercom`
        # property) is a restrictive change, so it is minted as 1.1.0 instead of
        # mutating the published mirrors. 0.9.0 and 1.0.0 stay byte-identical
        # (pinned by tests/test_schema_contract_removed_pack_profile.py); a legacy
        # profile still validates against the contract it was written against.
        # The 1.1.0 mirror also publishes the optional `copilot_review` block that
        # the root schema already carried.
        "current_version": "1.1.0",
        "known_versions": ("0.9.0", "1.0.0", "1.1.0"),
        "compatibility_model": "versioned-contract",
    },
    "harness-resolution": {
        "contract_name": "harness-resolution",
        "schema_file": "harness-resolution.schema.json",
        "versioned_schema_dir": "harness-resolution",
        # Published by 188.001-T (ship lifecycle Unit B, B1). The 1.0.0 mirror is
        # never edited in place: a contract change is a new version
        # (docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md).
        "current_version": "1.0.0",
        "known_versions": ("1.0.0",),
        "compatibility_model": "versioned-contract",
    },
}

CONTRACT_MIGRATIONS: dict[str, list[dict[str, Any]]] = {
    "manifest": [
        {
            "proposal_id": "upgrade-manifest-contract-0.9.0-to-1.0.0",
            "status": "known-legacy",
            "from_version": "0.9.0",
            "to_version": "1.0.0",
            "severity": "degrading",
            "summary": "Upgrade the harness-manifest contract from 0.9.0 to 1.0.0.",
            "changed_fields": [
                "schema_version",
                "capability_packs",
                "capability_pack_overlays",
            ],
            "action": "Back up the installed manifest, normalize legacy capability-pack records and overlay metadata to the 1.0.0 contract, then rerun verify-workspace.",
        },
        {
            "proposal_id": "upgrade-manifest-contract-1.0.0-to-1.1.0",
            "status": "known-legacy",
            "from_version": "1.0.0",
            "to_version": "1.1.0",
            "severity": "degrading",
            "summary": "Upgrade the harness-manifest contract from 1.0.0 to 1.1.0 (the retired agent-intercom capability pack is no longer a valid pack record).",
            "changed_fields": [
                "schema_version",
                "capability_packs",
                "capability_pack_overlays[*].pack",
            ],
            "action": "Back up the installed manifest, remove the retired agent-intercom pack and its overlay record, write schema_version: 1.1.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "backfill-manifest-schema-version",
            "status": "missing-version",
            "from_version": None,
            "to_version": "1.1.0",
            "severity": "degrading",
            "summary": "Backfill manifest schema_version to the current contract version.",
            "changed_fields": ["schema_version"],
            "action": "Back up the installed manifest, write schema_version: 1.1.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "review-unknown-manifest-contract",
            "status": "unknown-version",
            "from_version": "*",
            "to_version": "1.1.0",
            "severity": "manual-review",
            "summary": "Review the unknown manifest contract before auto-applying tune changes.",
            "changed_fields": ["schema_version"],
            "action": "Do not auto-apply. Inspect the installed manifest contract and choose a manual migration or regeneration path.",
            "manual_review": True,
        },
        {
            "proposal_id": "normalize-legacy-manifest-capability-packs",
            "warning_kind": "legacy-manifest-capability-pack",
            "from_version": "*",
            "to_version": "1.1.0",
            "severity": "degrading",
            "summary": "Replace legacy manifest capability-pack values with current overlay or health-report signals.",
            "changed_fields": ["capability_packs", "capability_pack_overlays[*].pack"],
            "action": "Rewrite legacy capability-pack entries so the manifest uses the current overlay vocabulary and verification checks.",
        },
        {
            "proposal_id": REMOVED_PACK_PROPOSAL_ID,
            "warning_kind": REMOVED_PACK_WARNING_KIND,
            "from_version": "*",
            "to_version": "1.1.0",
            "severity": "degrading",
            "summary": "Remove the retired capability pack from the manifest pack list and overlay records.",
            "changed_fields": ["capability_packs", "capability_pack_overlays[*].pack"],
            "action": "Remove the retired pack from capability_packs and its capability_pack_overlays record; delete its orphan overlay instruction file only when its checksum still matches the manifest record (a modified file needs manual review).",
        },
    ],
    "config": [
        {
            "proposal_id": "upgrade-config-contract-0.9.0-to-1.0.0",
            "status": "known-legacy",
            "from_version": "0.9.0",
            "to_version": "1.0.0",
            "severity": "degrading",
            "summary": "Upgrade the harness-config contract from 0.9.0 to 1.0.0.",
            "changed_fields": [
                "schema_version",
                "backlog.prefix_map",
                "backlog.suffix_map",
                "capability_packs",
            ],
            "action": "Back up .autoharness/config.yaml, rename legacy config keys such as backlog.prefix_map, normalize any legacy capability-pack values, write schema_version: 1.0.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "upgrade-config-contract-1.1.0-to-1.2.0",
            "status": "known-legacy",
            "from_version": "1.1.0",
            "to_version": "1.2.0",
            "severity": "degrading",
            "summary": "Upgrade the harness-config contract from 1.1.0 to 1.2.0 (model_routing is now closed: unknown keys are rejected at 1.2.0; routes and bindings are the additive part).",
            "changed_fields": ["schema_version"],
            "action": "Back up .autoharness/config.yaml, bump schema_version to 1.2.0 (optionally adopt model_routing.routes and model_routing.bindings; model_routing now rejects unknown keys), and rerun verify-workspace.",
        },
        {
            "proposal_id": "upgrade-config-contract-1.2.0-to-1.3.0",
            "status": "known-legacy",
            "from_version": "1.2.0",
            "to_version": "1.3.0",
            "severity": "degrading",
            "summary": "Upgrade the harness-config contract from 1.2.0 to 1.3.0 (the retired agent-intercom capability pack is no longer a valid capability_packs entry).",
            "changed_fields": ["schema_version", "capability_packs"],
            "action": "Back up .autoharness/config.yaml, remove the retired agent-intercom pack from capability_packs, bump schema_version to 1.3.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "backfill-config-schema-version",
            "status": "missing-version",
            "from_version": None,
            "to_version": "1.3.0",
            "severity": "degrading",
            "summary": "Backfill config schema_version to the current contract version.",
            "changed_fields": ["schema_version"],
            "action": "Back up .autoharness/config.yaml, write schema_version: 1.3.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "review-unknown-config-contract",
            "status": "unknown-version",
            "from_version": "*",
            "to_version": "1.3.0",
            "severity": "manual-review",
            "summary": "Review the unknown config contract before auto-applying tune changes.",
            "changed_fields": ["schema_version"],
            "action": "Do not auto-apply. Inspect the installed config contract and choose a manual migration or regeneration path.",
            "manual_review": True,
        },
        {
            "proposal_id": "rename-config-prefix-map",
            "from_version": "*",
            "to_version": "1.0.0",
            "severity": "degrading",
            "field_path": "backlog.prefix_map",
            "summary": "Rename backlog.prefix_map to backlog.suffix_map.",
            "changed_fields": ["backlog.prefix_map", "backlog.suffix_map"],
            "action": "Rename backlog.prefix_map to backlog.suffix_map while preserving all child values, then rerun verify-workspace.",
        },
        {
            "proposal_id": "normalize-legacy-config-capability-packs",
            "warning_kind": "legacy-config-capability-pack",
            "from_version": "*",
            "to_version": "1.3.0",
            "severity": "degrading",
            "summary": "Replace legacy config capability-pack values with currently supported packs.",
            "changed_fields": ["capability_packs"],
            "action": "Remove legacy pack names from .autoharness/config.yaml and express the intended behavior through current capability packs or explicit config.",
        },
        {
            "proposal_id": REMOVED_PACK_PROPOSAL_ID,
            "warning_kind": REMOVED_PACK_WARNING_KIND,
            "from_version": "*",
            "to_version": "1.3.0",
            "severity": "degrading",
            "summary": "Remove the retired capability pack from the config capability_packs list.",
            "changed_fields": ["capability_packs"],
            "action": "Remove the retired pack from capability_packs in .autoharness/config.yaml; delete its orphan overlay instruction file only when its checksum still matches the manifest record (a modified file needs manual review).",
        },
    ],
    "profile": [
        {
            "proposal_id": "upgrade-profile-contract-0.9.0-to-1.0.0",
            "status": "known-legacy",
            "from_version": "0.9.0",
            "to_version": "1.0.0",
            "severity": "degrading",
            "summary": "Upgrade the workspace-profile contract from 0.9.0 to 1.0.0.",
            "changed_fields": [
                "schema_version",
                "drift_report.changes[*].category",
                "harness_recommendations.capability_packs",
            ],
            "action": "Back up .autoharness/workspace-profile.yaml, rewrite legacy drift categories and capability-pack recommendations to the 1.0.0 vocabulary, write schema_version: 1.0.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "upgrade-profile-contract-1.0.0-to-1.1.0",
            "status": "known-legacy",
            "from_version": "1.0.0",
            "to_version": "1.1.0",
            "severity": "degrading",
            "summary": "Upgrade the workspace-profile contract from 1.0.0 to 1.1.0 (the retired agent-intercom capability pack is no longer a valid recommendation).",
            "changed_fields": [
                "schema_version",
                "harness_recommendations.capability_packs",
                "harness_recommendations.recommendation_reasons.capability_packs[*].item",
                "agent_intercom",
            ],
            "action": "Back up .autoharness/workspace-profile.yaml, remove the retired agent-intercom pack from the recommendations and drop any agent_intercom block, write schema_version: 1.1.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "backfill-profile-schema-version",
            "status": "missing-version",
            "from_version": None,
            "to_version": "1.1.0",
            "severity": "degrading",
            "summary": "Backfill workspace-profile schema_version to the current contract version.",
            "changed_fields": ["schema_version"],
            "action": "Back up .autoharness/workspace-profile.yaml, write schema_version: 1.1.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "review-unknown-profile-contract",
            "status": "unknown-version",
            "from_version": "*",
            "to_version": "1.1.0",
            "severity": "manual-review",
            "summary": "Review the unknown workspace-profile contract before auto-applying tune changes.",
            "changed_fields": ["schema_version"],
            "action": "Do not auto-apply. Inspect the installed workspace-profile contract and choose a manual migration or regeneration path.",
            "manual_review": True,
        },
        {
            "proposal_id": "normalize-legacy-profile-drift-categories",
            "warning_kind": "legacy-profile-drift-category",
            "from_version": "*",
            "to_version": "1.1.0",
            "severity": "degrading",
            "summary": "Rewrite legacy drift_report category values into the current taxonomy.",
            "changed_fields": ["drift_report.changes[*].category"],
            "action": "Rewrite legacy drift categories to the current breaking/degrading/cosmetic/growth taxonomy or regenerate the profile from fresh discovery.",
        },
        {
            "proposal_id": "normalize-legacy-profile-capability-packs",
            "warning_kind": "legacy-profile-capability-pack",
            "from_version": "*",
            "to_version": "1.1.0",
            "severity": "degrading",
            "summary": "Replace legacy workspace-profile capability-pack recommendations with the current pack vocabulary.",
            "changed_fields": ["harness_recommendations.capability_packs"],
            "action": "Remove legacy pack names from the recommended capability-pack set and regenerate the profile if needed.",
        },
        {
            "proposal_id": REMOVED_PACK_PROPOSAL_ID,
            "warning_kind": REMOVED_PACK_WARNING_KIND,
            "from_version": "*",
            "to_version": "1.1.0",
            "severity": "degrading",
            "summary": "Remove the retired capability pack from the workspace-profile recommendations and drop its leftover profile block.",
            "changed_fields": [
                "harness_recommendations.capability_packs",
                "harness_recommendations.recommendation_reasons.capability_packs[*].item",
                "agent_intercom",
            ],
            "action": "Remove the retired pack from the recommendations and reasons and drop its leftover profile block; delete its orphan overlay instruction file only when its checksum still matches the manifest record (a modified file needs manual review).",
        },
    ],
}


def _observed_schema_version(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    raw_version = data.get("schema_version")
    if raw_version is None:
        return None
    return str(raw_version)


def _lookup_nested(data: Any, dotted_path: str) -> tuple[bool, Any]:
    current = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _versioned_schema_path(contract: dict[str, Any], autoharness_home: Path, version: str) -> Path:
    return autoharness_home / "schemas" / contract["versioned_schema_dir"] / f"{version}.schema.json"


def resolve_contract_schema_path(kind: str, autoharness_home: Path, data: Any) -> Path:
    """Resolve the best schema path for an observed contract instance."""
    contract = SCHEMA_CONTRACTS[kind]
    observed_version = _observed_schema_version(data)
    known_versions = {str(version) for version in contract["known_versions"]}

    if observed_version and observed_version in known_versions:
        candidate = _versioned_schema_path(contract, autoharness_home, observed_version)
        if candidate.exists():
            return candidate

    current_candidate = _versioned_schema_path(contract, autoharness_home, str(contract["current_version"]))
    if current_candidate.exists():
        return current_candidate

    return autoharness_home / "schemas" / contract["schema_file"]


def summarize_schema_contract(kind: str, path: Path, data: Any) -> dict[str, Any]:
    """Describe the observed schema contract for an installed artifact."""
    contract = SCHEMA_CONTRACTS[kind]
    observed_version = _observed_schema_version(data)

    known_versions = tuple(str(version) for version in contract["known_versions"])
    current_version = str(contract["current_version"])
    if observed_version == current_version:
        status = "current"
    elif observed_version in known_versions:
        status = "known-legacy"
    elif observed_version is None:
        status = "missing-version"
    else:
        status = "unknown-version"

    return {
        "kind": kind,
        "contract_name": contract["contract_name"],
        "path": str(path),
        "schema_file": contract["schema_file"],
        "compatibility_model": contract["compatibility_model"],
        "current_version": current_version,
        "known_versions": list(known_versions),
        "observed_version": observed_version,
        "status": status,
    }


def _removed_pack_warning(kind: str, path: Path, field: str, pack: str) -> dict[str, Any]:
    contract = SCHEMA_CONTRACTS[kind]
    return {
        "kind": REMOVED_PACK_WARNING_KIND,
        "path": str(path),
        "field": field,
        "legacy_value": pack,
        "contract": contract["contract_name"],
        "current_version": contract["current_version"],
        "message": (
            f"Installed {contract['contract_name']} still records the removed capability pack '{pack}'. "
            "verify-workspace treats this as compatibility drift and ignores the pack instead of failing."
        ),
        "suggested_action": f"Remove the retired '{pack}' capability pack from the installed artifact (see the {REMOVED_PACK_PROPOSAL_ID} proposal).",
    }


def removed_overlay_record_warning(path: Path, index: int, artifact: Any) -> dict[str, Any] | None:
    """Warning for a legacy manifest artifact record of a retired pack's overlay, else None.

    The record is matched by installed path or by template source (the template was
    deleted with the pack), so it never reaches the missing-template-source blocker.
    """
    if not isinstance(artifact, dict):
        return None
    record_path = str(artifact.get("path") or "").replace("\\", "/")
    template = str(artifact.get("template") or "").replace("\\", "/")
    for info in REMOVED_CAPABILITY_PACKS.values():
        template_names = {info.overlay_template_path, info.overlay_template_path.removeprefix("templates/")}
        if record_path == info.overlay_instruction_path or template in template_names:
            return _removed_pack_warning("manifest", path, f"artifacts.{index}.path", info.pack)
    return None


def removed_pack_site_key(warning: dict[str, Any]) -> tuple[Any, Any, Any] | None:
    """Dedupe key (path, field, value) for a removed-capability-pack warning."""
    if warning.get("kind") != REMOVED_PACK_WARNING_KIND:
        return None
    return (warning.get("path"), warning.get("field"), warning.get("legacy_value"))


def _removed_pack_sites(kind: str, data: Any) -> list[tuple[str, str]]:
    """List (field, pack) recording sites, with fields named as schema errors name them."""
    if not isinstance(data, dict):
        return []
    sites: list[tuple[str, str]] = []

    def add_pack_list(prefix: str, values: Any, item_key: str | None = None) -> None:
        if not isinstance(values, list):
            return
        for index, value in enumerate(values):
            if item_key is not None:
                value = value.get(item_key) if isinstance(value, dict) else None
            if isinstance(value, str) and value in REMOVED_CAPABILITY_PACKS:
                suffix = f".{item_key}" if item_key else ""
                sites.append((f"{prefix}.{index}{suffix}", value))

    if kind == "manifest":
        add_pack_list("capability_packs", data.get("capability_packs"))
        add_pack_list("capability_pack_overlays", data.get("capability_pack_overlays"), "pack")
    elif kind == "config":
        add_pack_list("capability_packs", data.get("capability_packs"))
    elif kind == "profile":
        recommendations = data.get("harness_recommendations")
        if isinstance(recommendations, dict):
            add_pack_list("harness_recommendations.capability_packs", recommendations.get("capability_packs"))
            reasons = recommendations.get("recommendation_reasons")
            if isinstance(reasons, dict):
                add_pack_list(
                    "harness_recommendations.recommendation_reasons.capability_packs",
                    reasons.get("capability_packs"),
                    "item",
                )
        # The profile root is open, so a leftover block yields no schema error.
        for info in REMOVED_CAPABILITY_PACKS.values():
            if info.profile_block_key in data:
                sites.append((info.profile_block_key, info.pack))
    return sites


def _recorded_overlay_checksum(kind: str, path: Path, data: Any, overlay_path: str) -> str | None:
    manifest: Any = data
    if kind != "manifest":
        try:
            manifest = yaml.safe_load((path.parent / "harness-manifest.yaml").read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return None
    if not isinstance(manifest, dict):
        return None
    for artifact in manifest.get("artifacts") or []:
        if isinstance(artifact, dict) and str(artifact.get("path") or "").replace("\\", "/") == overlay_path:
            checksum = artifact.get("checksum")
            return str(checksum) if checksum else None
    return None


def _retired_overlay_needs_review(kind: str, path: Path, data: Any, packs: list[str]) -> bool:
    """True when a retired pack's overlay file exists but cannot be proven unmodified."""
    workspace_root = path.parent.parent
    for pack in packs:
        info = REMOVED_CAPABILITY_PACKS.get(pack)
        if info is None:
            continue
        overlay = workspace_root / info.overlay_instruction_path
        if not overlay.is_file():
            continue
        try:
            raw = overlay.read_bytes()
        except OSError:
            return True
        recorded = _recorded_overlay_checksum(kind, path, data, info.overlay_instruction_path)
        digests = {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()}
        if recorded is None or recorded not in digests:
            return True
    return False


def classify_schema_error(kind: str, path: Path, data: Any, error: str) -> tuple[str, dict[str, Any]]:
    """Classify a schema validation error as a hard blocker or compatibility finding."""
    contract = SCHEMA_CONTRACTS[kind]
    summary = summarize_schema_contract(kind, path, data)

    if MISSING_SCHEMA_VERSION_ERROR_RE.match(error):
        return (
            "warning",
            {
                "kind": f"missing-{kind}-schema-version",
                "path": str(path),
                "contract": contract["contract_name"],
                "current_version": contract["current_version"],
                "message": (
                    f"Installed {contract['contract_name']} omits schema_version. "
                    "verify-workspace treats this as compatibility drift instead of a hard schema failure."
                ),
                "suggested_action": f"Backfill schema_version: {contract['current_version']} or regenerate the artifact from the current contract.",
            },
        )

    capability_pack_match = LEGACY_CAPABILITY_PACK_ERROR_RE.match(error)
    if kind in {"manifest", "config", "profile"} and capability_pack_match:
        field_path, pack = capability_pack_match.groups()
        if pack in REMOVED_CAPABILITY_PACKS:
            return "warning", _removed_pack_warning(kind, path, field_path, pack)
        if pack in LEGACY_UNSUPPORTED_PACKS:
            return (
                "warning",
                {
                    "kind": f"legacy-{kind}-capability-pack",
                    "path": str(path),
                    "field": field_path,
                    "legacy_value": pack,
                    "contract": contract["contract_name"],
                    "current_version": contract["current_version"],
                    "message": (
                        f"Installed {contract['contract_name']} still records legacy capability pack '{pack}'. "
                        "verify-workspace treats this as compatibility drift instead of a hard schema failure."
                    ),
                    "suggested_action": "Tune the installed artifact to replace legacy capability-pack records with current pack names or overlay signals.",
                },
            )

    drift_category_match = LEGACY_DRIFT_CATEGORY_ERROR_RE.match(error)
    if kind == "profile" and drift_category_match:
        category = drift_category_match.group(1)
        if category in LEGACY_DRIFT_CATEGORIES:
            return (
                "warning",
                {
                    "kind": "legacy-profile-drift-category",
                    "path": str(path),
                    "legacy_value": category,
                    "contract": contract["contract_name"],
                    "current_version": contract["current_version"],
                    "message": (
                        f"Workspace profile drift report still uses legacy category '{category}'. "
                        "verify-workspace treats this as compatibility drift instead of a hard schema failure."
                    ),
                    "suggested_action": "Tune the workspace profile drift report into the current category taxonomy or regenerate it from fresh discovery.",
                },
            )

    return (
        "strict_schema_blocker",
        {
            "kind": f"invalid-{kind}-schema",
            "path": str(path),
            "contract": summary["contract_name"],
            "observed_version": summary["observed_version"],
            "current_version": summary["current_version"],
            "message": error,
        },
    )


def collect_contract_state_warnings(kind: str, path: Path, data: Any) -> list[dict[str, Any]]:
    """Collect compatibility findings that do not naturally arise from schema validation."""
    warnings: list[dict[str, Any]] = [
        _removed_pack_warning(kind, path, field, pack) for field, pack in _removed_pack_sites(kind, data)
    ]
    if kind == "config":
        found, _value = _lookup_nested(data, "backlog.prefix_map")
        if found:
            warnings.append(
                {
                    "kind": "legacy-config-key",
                    "path": str(path),
                    "field": "backlog.prefix_map",
                    "legacy_value": "backlog.prefix_map",
                    "contract": SCHEMA_CONTRACTS[kind]["contract_name"],
                    "current_version": SCHEMA_CONTRACTS[kind]["current_version"],
                    "message": (
                        "Installed config still uses backlog.prefix_map. "
                        "verify-workspace treats this as compatibility drift instead of a hard schema failure."
                    ),
                    "suggested_action": "Rename backlog.prefix_map to backlog.suffix_map while preserving the existing child values.",
                }
            )
    return warnings


def plan_schema_contract_migrations(
    kind: str,
    path: Path,
    data: Any,
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Plan version-aware migration proposals for a schema-bearing artifact."""
    contract = SCHEMA_CONTRACTS[kind]
    summary = summarize_schema_contract(kind, path, data)
    proposals: list[dict[str, Any]] = []

    for rule in CONTRACT_MIGRATIONS.get(kind, []):
        status = rule.get("status")
        if status and summary["status"] != status:
            continue

        from_version = rule.get("from_version")
        if from_version not in {None, "*"} and summary["observed_version"] != from_version:
            continue
        if from_version is None and summary["observed_version"] is not None:
            continue

        evidence: list[dict[str, Any]] = []
        warning_kind = rule.get("warning_kind")
        if warning_kind:
            evidence = [finding for finding in findings if finding.get("kind") == warning_kind]
            if not evidence:
                continue

        field_path = rule.get("field_path")
        if field_path:
            found, value = _lookup_nested(data, field_path)
            if not found:
                continue
            evidence.append(
                {
                    "kind": "field-presence",
                    "path": str(path),
                    "field": field_path,
                    "value": value,
                }
            )

        proposal = {
            "proposal_id": rule["proposal_id"],
            "contract": contract["contract_name"],
            "path": str(path),
            "from_version": summary["observed_version"],
            "to_version": rule.get("to_version", contract["current_version"]),
            "status": summary["status"],
            "severity": rule["severity"],
            "summary": rule["summary"],
            "changed_fields": list(rule.get("changed_fields") or []),
            "action": rule["action"],
            "manual_review": bool(rule.get("manual_review", False)),
        }
        if evidence:
            proposal["evidence"] = evidence
            legacy_values = sorted(
                {
                    str(item["legacy_value"])
                    for item in evidence
                    if isinstance(item, dict) and item.get("legacy_value") is not None
                }
            )
            if legacy_values:
                proposal["legacy_values"] = legacy_values
            if warning_kind == REMOVED_PACK_WARNING_KIND and _retired_overlay_needs_review(
                kind, path, data, legacy_values
            ):
                proposal["manual_review"] = True

        proposals.append(proposal)

    return proposals


VALIDATION_GATES_SCHEMA_DIR = "validation-gates"
VALIDATION_GATES_SCHEMA_VERSION = "1.1.0"


def resolve_validation_gates_schema_path(autoharness_home: Path) -> Path | None:
    """Resolve the versioned validation-gates schema, falling back to the pointer.

    Returns ``None`` when neither the versioned schema nor the pointer schema is
    present, so the caller can decide to skip deep validation rather than crash.
    """
    versioned = (
        autoharness_home
        / "schemas"
        / VALIDATION_GATES_SCHEMA_DIR
        / f"{VALIDATION_GATES_SCHEMA_VERSION}.schema.json"
    )
    if versioned.exists():
        return versioned
    pointer = autoharness_home / "schemas" / "validation-gates.schema.json"
    if pointer.exists():
        return pointer
    return None


def load_lifecycle_hooks_config(
    config_data: Any,
    autoharness_home: Path,
    *,
    validate: bool = True,
):
    """Resolution path for the optional lifecycle_hooks/telemetry config block.

    An absent ``lifecycle_hooks`` block yields a disabled gate configuration
    (fail-open-to-current). A present block is validated against the versioned
    validation-gates schema (when ``validate`` is True and the schema resolves)
    and parsed into a typed :class:`autoharness.gates.config.GatesConfig`.
    """
    from autoharness.gates.config import load_gates_config

    schema_path = resolve_validation_gates_schema_path(autoharness_home) if validate else None
    return load_gates_config(config_data, schema_path=schema_path)