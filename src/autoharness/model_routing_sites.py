"""Read-only builder for the installed `agent:<id>` site registry (B2, 215-S).

The pure resolver (`model_routing`) never discovers sites; this module is the
I/O half. It is disk-first: installed agent files are enumerated first and then
left-joined to the manifest provenance index, so a workspace-authored agent
(which has no manifest entry by definition) is reachable. The shared
`verify_workspace` helpers are imported function-locally (never at module top
level) because `verify_workspace` imports this module.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from autoharness.model_routing import SiteSpec

AGENT_FILE_SUFFIX = ".agent.md"
PIPELINE_AGENT_IDS = frozenset({"_orchestrator", "_stage", "_ship"})

REASON_PATH_UNUSABLE = "template-path-unusable"
REASON_UNREADABLE = "template-unreadable"
REASON_NO_TIER = "no-tier-placeholder"
REASON_AMBIGUOUS_TIER = "ambiguous-tier"

_FRONTMATTER = re.compile(r"\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_TIER_FAMILY_VARIABLE = re.compile(r"\{\{\s*TIER_(\d+)_FAMILY\s*\}\}")


@dataclass(frozen=True)
class SiteRegistry:
    sites: Mapping[str, SiteSpec]
    orphans: tuple[str, ...]
    conflicts: tuple[str, ...]
    unresolved: Mapping[str, str]


def _read_template_bytes(path: Path) -> bytes:
    """Single read seam for template sources (tests assert what is, and is not, read)."""
    return path.read_bytes()


def derive_template_default_tier(text: str) -> tuple[str | None, str | None]:
    """Parse a template's frontmatter for its `{{TIER_<N>_FAMILY}}` variable.

    Returns (`tier<N>`, None) for exactly one distinct N, else (None, reason). A targeted
    regex, not a YAML parse: template frontmatter can carry unquoted `{{...}}` values.
    """
    block = _FRONTMATTER.match(text)
    numbers = sorted(set(_TIER_FAMILY_VARIABLE.findall(block.group(1)))) if block else []
    if not numbers:
        return None, REASON_NO_TIER
    if len(numbers) > 1:
        return None, REASON_AMBIGUOUS_TIER
    return f"tier{int(numbers[0])}", None


def _template_default_tier(source: Path | None) -> tuple[str | None, str | None]:
    if source is None:
        return None, REASON_PATH_UNUSABLE
    try:
        text = _read_template_bytes(source).decode("utf-8")
    except Exception:  # noqa: BLE001 - any read or decode failure is a recorded reason, never a crash
        return None, REASON_UNREADABLE
    return derive_template_default_tier(text)


def _site_id(rel: str) -> str:
    return rel.rsplit("/", 1)[-1][: -len(AGENT_FILE_SUFFIX)]


def _scan_dir_prefixes(vw: Any, workspace_path: Path, profile: Any) -> list[str]:
    prefixes: list[str] = []
    for scan_dir in vw._resolve_agent_scan_dirs(workspace_path, profile):
        prefix = vw._fc_normalize_relative(vw._relative_workspace_path(workspace_path, scan_dir))
        if prefix and prefix not in prefixes:
            prefixes.append(prefix)
    return prefixes


def _orphans(
    vw: Any,
    workspace_path: Path,
    prefixes: list[str],
    provenance: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    found: list[str] = []
    for rel, entry in provenance.items():
        if not rel.endswith(AGENT_FILE_SUFFIX) or ".." in rel.split("/"):
            continue
        if not any(rel.startswith(f"{prefix}/") for prefix in prefixes):
            continue
        if entry["class"] == vw.FC_CLASS_MANAGED_SOURCE or _site_id(rel) in PIPELINE_AGENT_IDS:
            continue
        if not os.path.lexists(workspace_path / rel):
            found.append(rel)
    return tuple(sorted(found))


def build_site_registry(
    workspace_path: Path,
    autoharness_home: Path,
    manifest: Any,
    profile: Any = None,
) -> SiteRegistry:
    """Enumerate installed agent files, then join them to the manifest. Read-only."""
    from autoharness import verify_workspace as vw

    workspace_path = Path(workspace_path)
    autoharness_home = Path(autoharness_home)
    provenance = vw._fc_build_provenance_index(workspace_path, autoharness_home, manifest)

    candidates: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for target in vw._fc_enumerate_targets(workspace_path, profile):
        if target["kind"] != "agent":
            continue
        path = target["path"]
        if vw._fc_is_link_or_reparse(path) or vw._fc_resolve_contained(workspace_path, path) is None:
            continue
        site_id = _site_id(target["rel"])
        if site_id in PIPELINE_AGENT_IDS:
            continue
        entry = vw._fc_classify(target["rel"], provenance)
        if entry["class"] == vw.FC_CLASS_MANAGED_SOURCE:
            continue
        candidates.setdefault(site_id, []).append((target["rel"], entry))

    sites: dict[str, SiteSpec] = {}
    unresolved: dict[str, str] = {}
    conflicts: list[str] = []
    for site_id in sorted(candidates):
        if len(candidates[site_id]) > 1:
            conflicts.append(site_id)
            continue
        _, entry = candidates[site_id][0]
        if entry["class"] not in vw.FC_MANAGED_CLASSES:
            sites[site_id] = SiteSpec(site_id, None, False)
            continue
        if entry["class"] == vw.FC_CLASS_MANAGED_COMMUNITY:
            source = vw._fc_contained_community_source(autoharness_home, entry.get("template_path") or "")
        else:
            source_path = entry.get("source_path")
            source = Path(source_path) if source_path else None
        default_tier, reason = _template_default_tier(source)
        sites[site_id] = SiteSpec(site_id, default_tier, True)
        if reason is not None:
            unresolved[site_id] = reason

    prefixes = _scan_dir_prefixes(vw, workspace_path, profile)
    return SiteRegistry(
        sites=MappingProxyType(sites),
        orphans=_orphans(vw, workspace_path, prefixes, provenance),
        conflicts=tuple(conflicts),
        unresolved=MappingProxyType(unresolved),
    )
