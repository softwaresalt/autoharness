"""Capability-pack assertions are conditional on the pack being enabled (S2-U2)."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import pytest
import yaml

from autoharness.verify_workspace import (
    FOUNDATION_ASSERTIONS,
    PACK_ASSERTIONS,
    SUPPORTED_CAPABILITY_PACKS,
    verify_workspace,
)

PACKS = (
    "agent-engram",
    "backlogit",
    "graphtor-docs",
    "browser-verification",
    "continuous-learning",
    "strict-safety",
)

BASE_COPILOT_INSTRUCTIONS = (
    "## Durable Knowledge Layout\n"
    "Reusable learnings and hard-won fixes\n"
    "Session memory and checkpoints\n"
    "Graduated architecture and design rationale\n"
    "## Session Memory Requirements\n"
    "65%\n"
    "phase or major task group\n"
    "## Backlog Workflow Expectations\n"
    "queue-aware and dependency-aware operations\n"
    "commit-tracking\n"
    "parallel markdown trackers\n"
)


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _build_workspace(root: Path, pack: str, *, enabled: bool, content: bool) -> tuple[Path, Path]:
    home = root / "home"
    schema = json.dumps({"$schema": "http://json-schema.org/draft-07/schema#", "type": "object"})
    for name, directory in (
        ("harness-manifest.schema.json", "harness-manifest"),
        ("harness-config.schema.json", "harness-config"),
        ("workspace-profile.schema.json", "workspace-profile"),
    ):
        (home / "schemas" / directory).mkdir(parents=True, exist_ok=True)
        (home / "schemas" / name).write_text(schema, encoding="utf-8")
        (home / "schemas" / directory / "1.0.0.schema.json").write_text(schema, encoding="utf-8")

    workspace = root / "workspace"
    _write_yaml(
        workspace / ".autoharness" / "harness-manifest.yaml",
        {
            "schema_version": "1.0.0",
            "installed_at": "2026-04-25T00:00:00Z",
            "autoharness_version": "1.3.2",
            "profile_hash": "abc",
            "primitives_installed": [9],
            "capability_packs": [pack] if enabled else [],
            "artifacts": [],
        },
    )
    _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
    _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

    github = workspace / ".github"
    github.mkdir(parents=True, exist_ok=True)
    (github / "copilot-instructions.md").write_text(BASE_COPILOT_INSTRUCTIONS, encoding="utf-8")

    if enabled and content:
        by_path: dict[str, list[str]] = {}
        for assertion in PACK_ASSERTIONS[pack]:
            by_path.setdefault(assertion["path"], []).extend(assertion["must_contain"])
        for rel, tokens in by_path.items():
            target = workspace / rel
            if rel == ".github/copilot-instructions.md":
                target.write_text(
                    BASE_COPILOT_INSTRUCTIONS + "\n".join(tokens) + "\n", encoding="utf-8"
                )
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("\n".join(tokens) + "\n", encoding="utf-8")
    return workspace, home


def _verify(pack: str, *, enabled: bool, content: bool) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace, home = _build_workspace(Path(temp_dir), pack, enabled=enabled, content=content)
        return verify_workspace(workspace, home)


def _pack_keys(pack: str) -> set[str]:
    return {assertion["key"] for assertion in PACK_ASSERTIONS[pack]}


@pytest.mark.parametrize("pack", PACKS)
def test_disabled_pack_yields_no_pack_derived_failure(pack: str) -> None:
    report = _verify(pack, enabled=False, content=False)
    checks = report["targeted_checks"]

    assert not (_pack_keys(pack) & set(checks))
    foundation = {a["key"] for a in FOUNDATION_ASSERTIONS} & set(checks)
    assert foundation, "foundation checks should still run"
    assert all(checks[key]["ok"] for key in foundation), {
        key: checks[key] for key in foundation if not checks[key]["ok"]
    }


@pytest.mark.parametrize("pack", PACKS)
def test_enabled_pack_with_content_passes(pack: str) -> None:
    checks = _verify(pack, enabled=True, content=True)["targeted_checks"]

    for key in _pack_keys(pack):
        assert checks[key]["ok"], key


@pytest.mark.parametrize("pack", PACKS)
def test_enabled_pack_with_content_removed_fails_closed(pack: str) -> None:
    checks = _verify(pack, enabled=True, content=False)["targeted_checks"]

    for key in _pack_keys(pack):
        assert key in checks
        assert not checks[key]["ok"], key


def test_remote_operator_guidance_is_agent_engram_scoped() -> None:
    assert "copilot_remote_operator_guidance" in _pack_keys("agent-engram")
    assert "copilot_remote_operator_guidance" not in {a["key"] for a in FOUNDATION_ASSERTIONS}


def test_every_pack_assertion_key_is_a_supported_pack() -> None:
    assert set(PACK_ASSERTIONS) <= SUPPORTED_CAPABILITY_PACKS


def _is_pack_owned_token(token: str) -> bool:
    return (
        token.startswith("#")
        and token.lstrip("# ").strip() in SUPPORTED_CAPABILITY_PACKS
    ) or bool(re.fullmatch(r"[a-z]+(?:_[a-z]+)+|[A-Z][a-z]+(?:[A-Z][a-z]+)+", token))


def test_foundation_assertions_name_no_pack_owned_headings_or_tools() -> None:
    pack_tokens = {
        token
        for assertions in PACK_ASSERTIONS.values()
        for assertion in assertions
        for token in assertion["must_contain"]
        if _is_pack_owned_token(token)
    }
    pack_tokens |= {f"### {pack}" for pack in PACK_ASSERTIONS}
    pack_tokens |= {"sync_workspace"}

    offenders = [
        (assertion["key"], token)
        for assertion in FOUNDATION_ASSERTIONS
        for token in assertion["must_contain"]
        if token in pack_tokens
    ]
    assert offenders == []


def test_template_scopes_agent_engram_section_with_pack_markers() -> None:
    root = Path(__file__).resolve().parents[1]
    template = (root / "templates/foundation/copilot-instructions.md.tmpl").read_text(encoding="utf-8")
    begin = template.index("<!-- pack-scope:agent-engram:begin -->")
    end = template.index("<!-- pack-scope:agent-engram:end -->")
    assert begin < template.index("### agent-engram", begin) < end
    skill = (root / ".github/skills/install-harness/SKILL.md").read_text(encoding="utf-8")
    assert "pack-scope:{pack}:begin" in skill and "prune" in skill
