"""Schema contract metadata, compatibility helpers, and migration planning."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


LEGACY_CAPABILITY_PACK_ERROR_RE = re.compile(
    r"^((?:[A-Za-z0-9_]+\.)*(?:capability_packs\.\d+|capability_pack_overlays\.\d+\.pack)): '([^']+)' is not one of"
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

SCHEMA_CONTRACTS: dict[str, dict[str, Any]] = {
    "manifest": {
        "contract_name": "harness-manifest",
        "schema_file": "harness-manifest.schema.json",
        "versioned_schema_dir": "harness-manifest",
        "current_version": "1.0.0",
        "known_versions": ("0.9.0", "1.0.0"),
        "compatibility_model": "versioned-contract",
    },
    "config": {
        "contract_name": "harness-config",
        "schema_file": "harness-config.schema.json",
        "versioned_schema_dir": "harness-config",
        "current_version": "1.0.0",
        "known_versions": ("0.9.0", "1.0.0"),
        "compatibility_model": "versioned-contract",
    },
    "profile": {
        "contract_name": "workspace-profile",
        "schema_file": "workspace-profile.schema.json",
        "versioned_schema_dir": "workspace-profile",
        "current_version": "1.0.0",
        "known_versions": ("0.9.0", "1.0.0"),
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
            "proposal_id": "backfill-manifest-schema-version",
            "status": "missing-version",
            "from_version": None,
            "to_version": "1.0.0",
            "severity": "degrading",
            "summary": "Backfill manifest schema_version to the current contract version.",
            "changed_fields": ["schema_version"],
            "action": "Back up the installed manifest, write schema_version: 1.0.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "review-unknown-manifest-contract",
            "status": "unknown-version",
            "from_version": "*",
            "to_version": "1.0.0",
            "severity": "manual-review",
            "summary": "Review the unknown manifest contract before auto-applying tune changes.",
            "changed_fields": ["schema_version"],
            "action": "Do not auto-apply. Inspect the installed manifest contract and choose a manual migration or regeneration path.",
            "manual_review": True,
        },
        {
            "proposal_id": "normalize-legacy-manifest-capability-packs",
            "warning_kind": "legacy-manifest-capability-pack",
            "from_version": "1.0.0",
            "to_version": "1.0.0",
            "severity": "degrading",
            "summary": "Replace legacy manifest capability-pack values with current overlay or health-report signals.",
            "changed_fields": ["capability_packs", "capability_pack_overlays[*].pack"],
            "action": "Rewrite legacy capability-pack entries so the manifest uses the current overlay vocabulary and verification checks.",
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
            "proposal_id": "backfill-config-schema-version",
            "status": "missing-version",
            "from_version": None,
            "to_version": "1.0.0",
            "severity": "degrading",
            "summary": "Backfill config schema_version to the current contract version.",
            "changed_fields": ["schema_version"],
            "action": "Back up .autoharness/config.yaml, write schema_version: 1.0.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "review-unknown-config-contract",
            "status": "unknown-version",
            "from_version": "*",
            "to_version": "1.0.0",
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
            "from_version": "1.0.0",
            "to_version": "1.0.0",
            "severity": "degrading",
            "summary": "Replace legacy config capability-pack values with currently supported packs.",
            "changed_fields": ["capability_packs"],
            "action": "Remove legacy pack names from .autoharness/config.yaml and express the intended behavior through current capability packs or explicit config.",
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
            "proposal_id": "backfill-profile-schema-version",
            "status": "missing-version",
            "from_version": None,
            "to_version": "1.0.0",
            "severity": "degrading",
            "summary": "Backfill workspace-profile schema_version to the current contract version.",
            "changed_fields": ["schema_version"],
            "action": "Back up .autoharness/workspace-profile.yaml, write schema_version: 1.0.0, and rerun verify-workspace.",
        },
        {
            "proposal_id": "review-unknown-profile-contract",
            "status": "unknown-version",
            "from_version": "*",
            "to_version": "1.0.0",
            "severity": "manual-review",
            "summary": "Review the unknown workspace-profile contract before auto-applying tune changes.",
            "changed_fields": ["schema_version"],
            "action": "Do not auto-apply. Inspect the installed workspace-profile contract and choose a manual migration or regeneration path.",
            "manual_review": True,
        },
        {
            "proposal_id": "normalize-legacy-profile-drift-categories",
            "warning_kind": "legacy-profile-drift-category",
            "from_version": "1.0.0",
            "to_version": "1.0.0",
            "severity": "degrading",
            "summary": "Rewrite legacy drift_report category values into the current taxonomy.",
            "changed_fields": ["drift_report.changes[*].category"],
            "action": "Rewrite legacy drift categories to the current breaking/degrading/cosmetic/growth taxonomy or regenerate the profile from fresh discovery.",
        },
        {
            "proposal_id": "normalize-legacy-profile-capability-packs",
            "warning_kind": "legacy-profile-capability-pack",
            "from_version": "1.0.0",
            "to_version": "1.0.0",
            "severity": "degrading",
            "summary": "Replace legacy workspace-profile capability-pack recommendations with the current pack vocabulary.",
            "changed_fields": ["harness_recommendations.capability_packs"],
            "action": "Remove legacy pack names from the recommended capability-pack set and regenerate the profile if needed.",
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
    warnings: list[dict[str, Any]] = []
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

        proposals.append(proposal)

    return proposals