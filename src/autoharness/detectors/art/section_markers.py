"""ART-01 backlogit section-marker conformance detector."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from autoharness.backlog_root import resolve_backlog_root
from autoharness.detectors.contract import Evidence, NodeResult, NodeSpec

_MARKER_RE = re.compile(r"<!--\s*(BEGIN|END):([a-z0-9-]+)\s*-->")


def _workspace_from_context(context: Any) -> Path:
    return Path(getattr(context, "workspace", "."))


def _relevant_worktree_clean(workspace: Path, backlog_root: Path, head_sha: str | None) -> bool:
    """Return ``False`` only when git *positively confirms* uncommitted
    (staged, unstaged, or untracked) changes under the ``templates/`` and
    ``queue/`` directories beneath ``backlog_root``; return ``True``
    otherwise, including when this check does not apply at all.

    ART-01's evidence is published under a report keyed only by the
    immutable base/HEAD SHAs (``detectors/report.py``'s epoch key,
    ``detectors/applicability.py``'s diff), but this detector reads
    ``path.read_text()`` straight from the live working tree. If the
    relevant paths have uncommitted changes, a run today cannot be reliably
    reconstructed from that HEAD later, and because report publication is
    append-only/no-clobber (see ``emit_pre_review_report``), a later clean
    run at the *same* epoch key could never replace it -- so a positively
    confirmed dirty status must reject the evidence as unverifiable.

    ``head_sha`` is the same value the real `gate pre-review` CLI path
    threads through ``ApplicabilityContext`` (``detectors/applicability.py``)
    into every producer/validator call, and is exactly the SHA the report's
    epoch key is derived from. This check's entire premise is "does the
    working tree match what `head_sha` implies"; when no `head_sha` is
    supplied at all (e.g. a bare test fixture context with no epoch-key
    concept in play), there is nothing to verify reproducibility against, so
    the check is a no-op. When git itself is unavailable or the workspace is
    not a git repository, there is likewise no signal of dirtiness to act
    on, so this returns ``True`` rather than manufacturing a false positive.
    """
    if not head_sha:
        return True
    templates_dir = backlog_root / "templates"
    queue_dir = backlog_root / "queue"
    paths = [str(path) for path in (templates_dir, queue_dir) if path.exists()]
    if not paths:
        return True
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", *paths],
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )
    except OSError:
        return True
    if proc.returncode != 0:
        return True
    return not proc.stdout.strip()


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.DOTALL)
    if match is None:
        return {}, text
    data = yaml.safe_load(match.group(1)) or {}
    return data if isinstance(data, dict) else {}, text[match.end() :]


class MalformedTemplateSectionsError(ValueError):
    """Raised when a template's frontmatter declares a ``sections`` entry
    that does not conform to the ``{name: str, required: bool}`` contract.

    Previously, a malformed entry (e.g. a ``names:`` typo instead of
    ``name:``, or a missing ``name``) was silently dropped from the loaded
    template, and a non-boolean ``required`` value (e.g. the string
    ``"false"``) was coerced via ``bool(...)`` -- which is Python-truthy for
    any non-empty string. Both failure modes let a broken template contract
    silently produce a *partial* one instead: a typo could remove a required
    check entirely and every artifact of that type would then report
    ``passed``. Fail evidence production outright instead, so the assembler
    converts this into ``insufficient_evidence`` rather than trusting a
    partial, misleading section contract.
    """


def _load_template_sections(backlog_root: Path) -> dict[str, tuple[dict[str, Any], ...]]:
    templates: dict[str, tuple[dict[str, Any], ...]] = {}
    for path in sorted((backlog_root / "templates").glob("*.md")):
        frontmatter, _body = _split_frontmatter(path.read_text(encoding="utf-8"))
        artifact_type = frontmatter.get("type")
        raw_sections = frontmatter.get("sections")
        if not isinstance(artifact_type, str) or not isinstance(raw_sections, list):
            continue
        sections = []
        for section in raw_sections:
            if not isinstance(section, dict) or not isinstance(section.get("name"), str):
                raise MalformedTemplateSectionsError(
                    f"{path}: template 'sections' entry is malformed (expected a "
                    f"mapping with a string 'name'); got {section!r}"
                )
            required_raw = section.get("required", False)
            if not isinstance(required_raw, bool):
                raise MalformedTemplateSectionsError(
                    f"{path}: template section {section['name']!r} has a "
                    f"non-boolean 'required' value {required_raw!r}"
                )
            sections.append({"name": section["name"], "required": required_raw})
        templates[artifact_type] = tuple(sections)
    return templates



def _inspect_declared_sections(body: str, sections: tuple[dict[str, Any], ...]) -> dict[str, dict[str, Any]]:
    declared = {section["name"]: dict(section) for section in sections}
    observations = {
        name: {
            "required": bool(section.get("required", False)),
            "issues": [],
            "non_empty": False,
            "begin_positions": [],
            "end_positions": [],
        }
        for name, section in declared.items()
    }
    stack: list[str] = []
    markers = list(_MARKER_RE.finditer(body))
    for match in markers:
        kind, name = match.group(1), match.group(2)
        if name not in observations:
            continue
        observation = observations[name]
        positions_key = "begin_positions" if kind == "BEGIN" else "end_positions"
        observation[positions_key].append(match.start())
        if kind == "BEGIN":
            if len(observation["begin_positions"]) > 1:
                observation["issues"].append("duplicate_begin")
            if stack:
                observation["issues"].append("nested")
            stack.append(name)
        else:
            if len(observation["end_positions"]) > 1:
                observation["issues"].append("duplicate_end")
            if not stack or stack[-1] != name:
                observation["issues"].append("misordered_end")
            else:
                stack.pop()

    for name, observation in observations.items():
        if not observation["begin_positions"]:
            observation["issues"].append("missing_begin")
        if not observation["end_positions"]:
            observation["issues"].append("missing_end")
        if len(observation["begin_positions"]) == 1 and len(observation["end_positions"]) == 1:
            begin_match = next(match for match in markers if match.start() == observation["begin_positions"][0])
            end_match = next(match for match in markers if match.start() == observation["end_positions"][0])
            if begin_match.start() >= end_match.start():
                observation["issues"].append("misordered_pair")
            else:
                segment = body[begin_match.end() : end_match.start()]
                observation["non_empty"] = bool(segment.strip())
                if observation["required"] and not observation["non_empty"]:
                    observation["issues"].append("required_empty")
    return observations


def produce(node: NodeSpec, context: Any) -> Evidence:
    workspace = _workspace_from_context(context)
    backlog_root = resolve_backlog_root(workspace)
    head_sha = getattr(context, "head_sha", None)
    worktree_clean = _relevant_worktree_clean(workspace, backlog_root, head_sha)
    templates = _load_template_sections(backlog_root)
    artifacts = []
    for path in sorted((backlog_root / "queue").glob("*.md")):
        frontmatter, body = _split_frontmatter(path.read_text(encoding="utf-8"))
        artifact_type = frontmatter.get("artifact_type")
        type_resolved = isinstance(artifact_type, str) and artifact_type in templates
        sections = templates.get(artifact_type, ()) if isinstance(artifact_type, str) else ()
        artifacts.append(
            {
                "path": str(path.relative_to(workspace)).replace('\\', '/'),
                "artifact_type": artifact_type,
                "type_resolved": type_resolved,
                "sections": _inspect_declared_sections(body, sections),
            }
        )
    return Evidence(
        node.node_id,
        {"artifacts": artifacts, "worktree_clean": worktree_clean},
        provenance={"artifact_count": len(artifacts), "worktree_clean": worktree_clean},
    )


def validate(node: NodeSpec, evidence_map, _context: Any) -> NodeResult:
    evidence = evidence_map[node.node_id]
    artifacts = evidence.payload.get("artifacts", [])
    worktree_clean = evidence.payload.get("worktree_clean", True)
    if not worktree_clean:
        # Git has positively confirmed uncommitted changes under the backlog
        # templates/ or queue/ directories; reject before trusting any
        # failures/unresolved computed below since evidence read from a
        # dirty working tree cannot be reproduced from the immutable
        # base/HEAD SHAs the report is keyed by.
        return NodeResult(
            name=node.node_id,
            status="insufficient_evidence",
            token="INSUFFICIENT_EVIDENCE",
            message=(
                "ART-01 detected uncommitted changes under the backlog templates/ "
                "or queue/ directories; section-marker evidence is not "
                "reproducible from the immutable HEAD SHA and cannot be verified"
            ),
            details={
                "artifact_count": len(artifacts),
                "failure_count": 0,
                "failures": [],
                "unresolved_count": 0,
                "unresolved": [],
                "worktree_clean": False,
            },
            provenance={"artifact_count": len(artifacts)},
        )
    failures = []
    unresolved = []
    for artifact in artifacts:
        if not artifact.get("type_resolved", False):
            # A missing/malformed `artifact_type`, or one with no matching
            # template, means we never know which sections *should* be
            # present. `_load_template_sections`/`sections=()` silently makes
            # such an artifact look conformant (zero declared sections, zero
            # issues) — that would be a false "passed", not a genuine
            # verification. Report it separately so it can never be
            # confused with an artifact that was actually checked and found
            # clean.
            unresolved.append({"path": artifact.get("path"), "artifact_type": artifact.get("artifact_type")})
            continue
        section_failures = {
            name: info["issues"]
            for name, info in artifact.get("sections", {}).items()
            if info["issues"]
        }
        if not section_failures:
            continue
        failures.append(
            {
                "path": artifact.get("path"),
                "sections": section_failures,
            }
        )
    if failures:
        failing_paths = ", ".join(str(item["path"]) for item in failures)
        return NodeResult(
            name=node.node_id,
            status="failed",
            token="FAILED",
            message=f"ART-01 detected section-marker defects in {failing_paths}",
            details={
                "artifact_count": len(artifacts),
                "failure_count": len(failures),
                "failures": failures,
                "unresolved_count": len(unresolved),
                "unresolved": unresolved,
            },
            provenance={"artifact_count": len(artifacts)},
        )
    if unresolved:
        unresolved_paths = ", ".join(str(item["path"]) for item in unresolved)
        return NodeResult(
            name=node.node_id,
            status="insufficient_evidence",
            token="INSUFFICIENT_EVIDENCE",
            message=(
                "ART-01 could not resolve a template for artifact_type on "
                f"{unresolved_paths}; section conformance cannot be verified"
            ),
            details={
                "artifact_count": len(artifacts),
                "failure_count": 0,
                "failures": [],
                "unresolved_count": len(unresolved),
                "unresolved": unresolved,
            },
            provenance={"artifact_count": len(artifacts)},
        )
    return NodeResult(
        name=node.node_id,
        status="passed",
        token="PASSED",
        message="ART-01 section-marker conformance passed",
        details={
            "artifact_count": len(artifacts),
            "failure_count": 0,
            "failures": [],
            "unresolved_count": 0,
            "unresolved": [],
        },
        provenance={"artifact_count": len(artifacts)},
    )
