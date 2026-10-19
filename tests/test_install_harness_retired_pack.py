"""209-F U17: install-harness skill, install prompt and auto-mergeinstall agent drop the retired pack.

Pins that the retired ``agent-intercom`` pack is named only inside the single
"Retired capability packs" note of the installer skill, that the pack lists on the
install surfaces match the registry's live packs, and that the Step 3.3 manifest
skeleton a fresh install renders pins the current manifest contract.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

from autoharness.schema_contracts import REMOVED_CAPABILITY_PACKS, SCHEMA_CONTRACTS

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SKILL = _REPO_ROOT / ".github" / "skills" / "install-harness" / "SKILL.md"
_PROMPT = _REPO_ROOT / ".github" / "prompts" / "install-harness.prompt.md"
_AGENT = _REPO_ROOT / ".github" / "agents" / "auto-mergeinstall.agent.md"
_REGISTRY = _REPO_ROOT / "templates" / "packs" / "capability-pack-registry.yaml"
_MANIFEST_SCHEMA = _REPO_ROOT / "schemas" / "harness-manifest.schema.json"

_RETIRED = "agent-intercom"
_NOTE_HEADING = "#### Retired capability packs"
_PACK_ID = re.compile(r"`([a-z]+(?:-[a-z]+)*)`")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _live_pack_ids() -> list[str]:
    registry = yaml.safe_load(_text(_REGISTRY))
    return [pack["id"] for pack in registry["packs"] if pack["id"] not in REMOVED_CAPABILITY_PACKS]


def _without_note(text: str) -> str:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == _NOTE_HEADING)
    end = next(
        (i for i in range(start + 1, len(lines)) if re.match(r"#{1,4} ", lines[i])),
        len(lines),
    )
    return "\n".join(lines[:start] + lines[end:])


def _step_33_skeleton(text: str) -> str:
    section = text.split("#### Step 3.3: Write Installation Manifest", 1)[1]
    section = section.split("#### Step 3.4", 1)[0]
    match = re.search(r"```yaml\n(.*?)\n```", section, flags=re.DOTALL)
    assert match is not None, "Step 3.3 has no yaml manifest skeleton"
    return match.group(1)


_SAMPLE_VALUES = {
    "ISO_8601_TIMESTAMP": "2026-10-19T00:00:00Z",
    "AUTOHARNESS_VERSION": "1.0.0",
    "AUTOHARNESS_HOME": "/opt/autoharness",
    "SHA256_OF_PROFILE": "a" * 64,
    "SHA256_OF_CONFIG_OR_NULL": "b" * 64,
    "PRESET": "full",
    "PRIMARY_STACK_PACK": "python",
    "STACK_PACKS": "library",
    "INSTALL_LAYERS": "foundation, overlays",
    "CAPABILITY_PACKS": "backlogit",
    "PACK_NAME": "backlogit",
    "OVERLAY_TARGETS": "foundation-docs",
    "OVERLAY_VERIFICATION_CHECKS": "overlay installed",
    "SHA256": "c" * 64,
}


def _render_skeleton(text: str) -> dict:
    rendered = re.sub(
        r"\{\{([A-Za-z0-9_]+)\}\}",
        lambda match: _SAMPLE_VALUES.get(match.group(1), "sample"),
        _step_33_skeleton(text),
    ).replace("true|false", "true")
    return yaml.safe_load(rendered)


class RetiredPackNoteTests(unittest.TestCase):
    def test_install_surfaces_name_the_retired_pack_only_in_the_note(self) -> None:
        self.assertIn(_NOTE_HEADING, _text(_SKILL))
        self.assertIn(f"RETIRED_PACK: {_RETIRED} ignored", _text(_SKILL))
        for path in (_SKILL, _PROMPT, _AGENT):
            with self.subTest(path=path.name):
                stripped = _without_note(_text(_SKILL)) if path == _SKILL else _text(path)
                self.assertNotIn("intercom", stripped.casefold())

    def test_retired_note_says_the_pack_is_ignored_and_install_continues(self) -> None:
        text = _text(_SKILL)
        note = text.split(_NOTE_HEADING, 1)[1].split("\n#", 1)[0]
        self.assertIn("ignored", note)
        self.assertIn("continue", note)
        self.assertIn("never", note)

    def test_install_surface_pack_lists_match_the_registry(self) -> None:
        live = sorted(_live_pack_ids())
        skill_input = next(line for line in _text(_SKILL).splitlines() if line.startswith("* `capability_packs`:"))
        prompt_input = next(
            line for line in _text(_PROMPT).splitlines() if line.startswith("* ${input:capability_packs}:")
        )
        agent_line = next(line for line in _text(_AGENT).splitlines() if "Add capability packs" in line)
        for label, line in (("skill", skill_input), ("prompt", prompt_input), ("agent", agent_line)):
            with self.subTest(surface=label):
                self.assertEqual(sorted(_PACK_ID.findall(line)), live)

    def test_overlay_table_rows_match_the_registry(self) -> None:
        text = _text(_SKILL)
        table = text.split("Capability-pack overlays:", 1)[1].split("#### Step 1.3a", 1)[0]
        rows = re.findall(r"^\| `([a-z-]+)` \|", table, flags=re.MULTILINE)
        self.assertEqual(sorted(rows), sorted(_live_pack_ids()))

    def test_capability_pack_variable_table_has_no_retired_rows(self) -> None:
        text = _text(_SKILL)
        self.assertNotIn("AGENT_INTERCOM", text)


class FreshInstallManifestSkeletonTests(unittest.TestCase):
    def test_step_33_skeleton_pins_the_current_manifest_contract(self) -> None:
        manifest = _render_skeleton(_text(_SKILL))
        self.assertEqual(manifest["schema_version"], SCHEMA_CONTRACTS["manifest"]["current_version"])

    def test_rendered_step_33_skeleton_validates_against_the_current_manifest_schema(self) -> None:
        import json

        schema = json.loads(_text(_MANIFEST_SCHEMA))
        manifest = _render_skeleton(_text(_SKILL))
        errors = [error.message for error in Draft7Validator(schema).iter_errors(manifest)]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
