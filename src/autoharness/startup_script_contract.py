"""Startup-script contract detection for tune/verify drift classification.

The generic manifest checksum scan in ``verify_workspace`` only compares each
installed artifact against the checksum recorded in that workspace's own
manifest. That catches missing or locally modified files, but it cannot detect
contract staleness when a target workspace still has an untouched, byte-for-byte
legacy ``start.ps1`` or ``start.sh`` from an older autoharness install. This
module closes that gap with deterministic, marker-based classification for the
thin-shim startup-script contract.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


STARTUP_SCRIPT_CONTRACT_VERSION = "1.0.0"

_CUSTOM_SECTION_MARKERS = (
    re.compile(r"──\s*Claude Code\s*─+"),
    re.compile(r"──\s*OpenAI Codex\s*/\s*Agents\s*─+"),
    re.compile(r"──\s*Custom\s*─+"),
)

_PS1_DEFAULT_CUSTOM_TAIL = "\n".join(
    [
        "# ── Claude Code ─────────────────────────────────────────────────────────────",
        "# Uncomment to run Claude Code with workspace-local state directories.",
        "# CLAUDE_CONFIG_DIR redirects Claude's config and history to the workspace.",
        "# Verify that your installed version of Claude Code supports this env variable.",
        "#",
        '# $env:CLAUDE_CONFIG_DIR = ".\\.claude"',
        "# claude",
        "",
        "# ── OpenAI Codex / Agents ────────────────────────────────────────────────────",
        "# Uncomment to run Codex with a workspace-local API key file.",
        "#",
        "# $env:OPENAI_API_KEY = (Get-Content .openai-token -Raw).Trim()",
        "# codex",
    ]
) + "\n"

_SH_DEFAULT_CUSTOM_TAIL = "\n".join(
    [
        "# ── Claude Code ─────────────────────────────────────────────────────────────",
        "# Uncomment to run Claude Code with workspace-local state directories.",
        "# CLAUDE_CONFIG_DIR redirects Claude's config and history to the workspace.",
        "# Verify that your installed version of Claude Code supports this env variable.",
        "#",
        '# export CLAUDE_CONFIG_DIR="./.claude"',
        "# claude",
        "",
        "# ── OpenAI Codex / Agents ────────────────────────────────────────────────────",
        "# Uncomment to run Codex with a workspace-local API key file.",
        "#",
        '# export OPENAI_API_KEY="$(cat .openai-token)"',
        "# codex",
    ]
) + "\n"

STARTUP_SCRIPT_CONTRACTS: dict[str, dict[str, Any]] = {
    "ps1": {
        "contract_name": "startup-script-ps1",
        "template": "scripts/start.ps1.tmpl",
        "current_version": STARTUP_SCRIPT_CONTRACT_VERSION,
        "known_versions": ("0.9.0", STARTUP_SCRIPT_CONTRACT_VERSION),
        "current_marker": "autoharness run --workspace $PSScriptRoot -- @args",
        "legacy_markers": (
            "COPILOT_HOME redirects the Copilot CLI database",
            "function Invoke-EngramCommandWithProgress",
        ),
        "custom_section_markers": _CUSTOM_SECTION_MARKERS,
        "default_custom_tail": _PS1_DEFAULT_CUSTOM_TAIL,
    },
    "sh": {
        "contract_name": "startup-script-sh",
        "template": "scripts/start.sh.tmpl",
        "current_version": STARTUP_SCRIPT_CONTRACT_VERSION,
        "known_versions": ("0.9.0", STARTUP_SCRIPT_CONTRACT_VERSION),
        'current_marker': 'exec autoharness run --workspace "$script_dir" -- "$@"',
        "legacy_markers": ("COPILOT_HOME redirects the Copilot CLI database",),
        "custom_section_markers": _CUSTOM_SECTION_MARKERS,
        "default_custom_tail": _SH_DEFAULT_CUSTOM_TAIL,
    },
}


def resolve_startup_script_shell(relative_path: str, template: str | None = None) -> str | None:
    """Resolve the startup-script shell from manifest template metadata or path."""
    if template:
        for shell, contract in STARTUP_SCRIPT_CONTRACTS.items():
            if template == contract["template"]:
                return shell

    basename = Path(relative_path).name.lower()
    if basename == "start.ps1":
        return "ps1"
    if basename == "start.sh":
        return "sh"
    return None


def classify_startup_script(
    shell: str,
    content: str | None,
    manifest_contract_version: str | None = None,
) -> dict[str, Any]:
    """Classify a startup script against the thin-shim contract markers."""
    contract = STARTUP_SCRIPT_CONTRACTS[shell]
    known_versions = tuple(contract["known_versions"])
    evidence: list[str] = []

    classification: dict[str, Any] = {
        "shell": shell,
        "contract_name": contract["contract_name"],
        "current_version": contract["current_version"],
        "known_versions": list(known_versions),
        "manifest_contract_version": manifest_contract_version,
    }

    if manifest_contract_version is not None and manifest_contract_version not in known_versions:
        evidence.append(
            f"Manifest records unknown contract_version '{manifest_contract_version}'; "
            f"known versions are {', '.join(known_versions)}."
        )
        classification["status"] = "ambiguous"
        classification["evidence"] = evidence
        return classification

    if content is None:
        evidence.append("Installed startup script is missing from the workspace.")
        classification["status"] = "missing"
        classification["evidence"] = evidence
        return classification

    current_marker = contract["current_marker"]
    current_marker_present = _has_active_marker(content, current_marker)
    legacy_hits = [marker for marker in contract["legacy_markers"] if marker in content]

    if current_marker_present and not legacy_hits:
        _core, tail = _find_custom_tail(content, contract["custom_section_markers"])
        evidence.append(f"Matched current delegation marker: {current_marker}")
        if tail:
            if tail.rstrip() == contract["default_custom_tail"].rstrip():
                evidence.append("Supported custom-section scaffold matches the current default tail.")
                classification["status"] = "current"
            else:
                evidence.append("Detected preserved custom-section tail after the current delegation block.")
                classification["status"] = "customized"
                classification["custom_sections"] = tail
        else:
            evidence.append("No supported custom-section tail was present after the current delegation block.")
            classification["status"] = "current"
        classification["evidence"] = evidence
        return classification

    if legacy_hits and not current_marker_present:
        evidence.append(
            "Matched legacy startup-script marker(s): " + ", ".join(legacy_hits)
        )
        evidence.append("Current thin-shim delegation marker was not found.")
        classification["status"] = "known-legacy"
        _core, tail = _find_custom_tail(content, contract["custom_section_markers"])
        if tail.strip():
            evidence.append(
                "Detected a preserved custom-section tail in the legacy script; it "
                "must be extracted and reattached (not discarded) when this script "
                "is refreshed to the current contract."
            )
            classification["custom_sections"] = tail
        classification["evidence"] = evidence
        return classification

    if current_marker_present and legacy_hits:
        evidence.append(f"Matched current delegation marker: {current_marker}")
        evidence.append(
            "Matched legacy startup-script marker(s): " + ", ".join(legacy_hits)
        )
        classification["status"] = "ambiguous"
        classification["evidence"] = evidence
        return classification

    evidence.append("No recognized current or legacy startup-script markers were found.")
    classification["status"] = "ambiguous"
    classification["evidence"] = evidence
    return classification


def plan_startup_script_migration(
    shell: str,
    relative_path: str,
    classification: dict[str, Any],
) -> dict[str, Any] | None:
    """Build a deterministic migration proposal from a startup-script classification."""
    status = classification["status"]
    if status == "current":
        return None

    contract = STARTUP_SCRIPT_CONTRACTS[shell]
    proposal_id_by_status = {
        "missing": f"generate-startup-script-{shell}",
        "known-legacy": f"refresh-startup-script-{shell}-contract",
        "customized": f"refresh-customized-startup-script-{shell}-contract",
        "ambiguous": f"review-startup-script-{shell}-contract",
    }
    summary_by_status = {
        "missing": f"Generate missing {relative_path} from the current thin-shim startup-script contract.",
        "known-legacy": f"Refresh legacy {relative_path} to the current thin-shim startup-script contract.",
        "customized": (
            f"Refresh {relative_path} to the current thin-shim startup-script contract "
            "while preserving supported custom sections."
        ),
        "ambiguous": f"Review {relative_path} manually before changing its startup-script contract.",
    }
    action_by_status = {
        "missing": (
            "Generate the script from the current template, then record the accepted "
            "contract version and checksum in the manifest."
        ),
        "known-legacy": (
            "Back up the installed script under the target workspace's dated "
            "autoharness backup area before refresh, refresh it from the current "
            "template, and update manifest contract/checksum metadata only after "
            "the accepted refresh lands."
        ),
        "customized": (
            "Back up the installed script under the target workspace's dated "
            "autoharness backup area before refresh, refresh the core delegation "
            "block from the current template, deterministically reattach the "
            "preserved supported custom section(s), and update manifest "
            "contract/checksum metadata only after the accepted refresh lands."
        ),
        "ambiguous": (
            "Do not auto-apply. Surface the script for operator review and choose "
            "a manual migration or regeneration path."
        ),
    }

    proposal: dict[str, Any] = {
        "proposal_id": proposal_id_by_status[status],
        "contract": contract["contract_name"],
        "path": relative_path,
        "to_version": contract["current_version"],
        "status": status,
        "severity": "breaking" if status == "missing" else "degrading",
        "summary": summary_by_status[status],
        "action": action_by_status[status],
        "manual_review": status == "ambiguous",
        "evidence": list(classification.get("evidence") or []),
    }
    if classification.get("custom_sections"):
        proposal["custom_sections"] = classification["custom_sections"]
        if status == "known-legacy":
            proposal["action"] = (
                "Back up the installed script under the target workspace's dated "
                "autoharness backup area before refresh, refresh the core "
                "delegation block from the current template, deterministically "
                "reattach the preserved supported custom section(s) recovered "
                "from this legacy script, and update manifest contract/checksum "
                "metadata only after the accepted refresh lands."
            )
    return proposal


def _has_active_marker(content: str, marker: str) -> bool:
    """True if `marker` appears on at least one non-commented (active) line.

    A raw substring search would also match a disabled/commented-out copy of the
    marker text (e.g. ``# exec autoharness run --workspace "$script_dir" -- "$@"``),
    misclassifying a script that no longer delegates as ``current``. Only a line
    whose stripped text does not begin with a comment marker counts as active.
    """
    for line in content.splitlines():
        if marker in line and not line.strip().startswith("#"):
            return True
    return False


def _find_custom_tail(content: str, patterns: tuple[re.Pattern[str], ...]) -> tuple[str, str]:
    """Split a script into its refreshable core block and supported custom tail."""
    offset = 0
    for line in content.splitlines(keepends=True):
        if any(pattern.search(line) for pattern in patterns):
            return content[:offset], content[offset:]
        offset += len(line)
    return content, ""
