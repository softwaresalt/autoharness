"""ART-01 backlogit section-marker conformance detector."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from autoharness.detectors.contract import Evidence, NodeResult, NodeSpec

_MARKER_RE = re.compile(r"<!--\s*(BEGIN|END):([a-z0-9-]+)\s*-->")


def _workspace_from_context(context: Any) -> Path:
    return Path(getattr(context, "workspace", "."))


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.DOTALL)
    if match is None:
        return {}, text
    data = yaml.safe_load(match.group(1)) or {}
    return data if isinstance(data, dict) else {}, text[match.end() :]


def _load_template_sections(workspace: Path) -> dict[str, tuple[dict[str, Any], ...]]:
    templates: dict[str, tuple[dict[str, Any], ...]] = {}
    for path in sorted((workspace / ".backlogit" / "templates").glob("*.md")):
        frontmatter, _body = _split_frontmatter(path.read_text(encoding="utf-8"))
        artifact_type = frontmatter.get("type")
        raw_sections = frontmatter.get("sections")
        if not isinstance(artifact_type, str) or not isinstance(raw_sections, list):
            continue
        sections = []
        for section in raw_sections:
            if not isinstance(section, dict) or not isinstance(section.get("name"), str):
                continue
            sections.append({"name": section["name"], "required": bool(section.get("required", False))})
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
    templates = _load_template_sections(workspace)
    artifacts = []
    for path in sorted((workspace / ".backlogit" / "queue").glob("*.md")):
        frontmatter, body = _split_frontmatter(path.read_text(encoding="utf-8"))
        artifact_type = frontmatter.get("artifact_type")
        sections = templates.get(artifact_type, ()) if isinstance(artifact_type, str) else ()
        artifacts.append(
            {
                "path": str(path.relative_to(workspace)).replace('\\', '/'),
                "artifact_type": artifact_type,
                "sections": _inspect_declared_sections(body, sections),
            }
        )
    return Evidence(node.node_id, {"artifacts": artifacts}, provenance={"artifact_count": len(artifacts)})


def validate(node: NodeSpec, evidence_map, _context: Any) -> NodeResult:
    evidence = evidence_map[node.node_id]
    artifacts = evidence.payload.get("artifacts", [])
    failures = []
    for artifact in artifacts:
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
            },
            provenance={"artifact_count": len(artifacts)},
        )
    return NodeResult(
        name=node.node_id,
        status="passed",
        token="PASSED",
        message="ART-01 section-marker conformance passed",
        details={"artifact_count": len(artifacts), "failure_count": 0, "failures": []},
        provenance={"artifact_count": len(artifacts)},
    )
