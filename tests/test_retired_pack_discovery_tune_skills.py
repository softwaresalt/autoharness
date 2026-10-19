"""209-F U18: discovery, tune-harness and verify-harness skills handle the retired pack.

Pins that workspace-discovery neither detects, records nor recommends the retired
``agent-intercom`` pack and emits a profile skeleton on the current contract,
that tune-harness reports the retired pack as a drift category and offers
proposal-only cleanup under the checksum rule without ever re-weaving it, and
that verify-harness points at the P-017 Dark Factory Visibility Protocol.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

from autoharness.schema_contracts import REMOVED_CAPABILITY_PACKS, SCHEMA_CONTRACTS

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SKILLS = _REPO_ROOT / ".github" / "skills"
_DISCOVERY = _SKILLS / "workspace-discovery" / "SKILL.md"
_TUNE = _SKILLS / "tune-harness" / "SKILL.md"
_VERIFY = _SKILLS / "verify-harness" / "SKILL.md"
_PROFILE_SCHEMA = _REPO_ROOT / "schemas" / "workspace-profile.schema.json"

_RETIRED = "agent-intercom"
_DISCOVERY_NOTE = "#### Step 1.5c: Retired Capability Pack Handling"
_TUNE_SECTION = "#### Step 1.6b: Retired Capability Pack Cleanup"
_OVERLAY_FILE = ".github/instructions/agent-intercom.instructions.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    end = len(lines)
    for i in range(start + 1, len(lines)):
        stripped = lines[i].lstrip()
        hashes = len(stripped) - len(stripped.lstrip("#"))
        if 0 < hashes <= level and stripped[hashes : hashes + 1] == " ":
            end = i
            break
    return "\n".join(lines[start:end])


def _without(text: str, section: str) -> str:
    return text.replace(section, "")


def _profile_skeleton(text: str) -> str:
    section = text.split("#### Step 4.1: Compose the Profile", 1)[1].split("#### Step 4.2", 1)[0]
    match = re.search(r"```yaml\n(.*?)\n```", section, flags=re.DOTALL)
    assert match is not None, "Step 4.1 has no yaml profile skeleton"
    return match.group(1)


_SAMPLE_VALUES = {
    "ISO_8601_TIMESTAMP": "2026-10-19T00:00:00Z",
    "RECOMMENDED_PRESET": "full",
    "PRE_PUSH_ENABLED": "false",
    "CI_PATH_FILTER_MODE": "fail_closed_changes_job",
}


def _render_profile(text: str) -> dict:
    rendered = re.sub(
        r"\{\{([A-Za-z0-9_]+)\}\}",
        lambda match: _SAMPLE_VALUES.get(match.group(1), "sample"),
        _profile_skeleton(text),
    )
    return yaml.safe_load(rendered)


class DiscoveryRetiredPackTests(unittest.TestCase):
    def test_discovery_names_the_retired_pack_only_in_its_handling_note(self) -> None:
        text = _text(_DISCOVERY)
        note = _section(text, _DISCOVERY_NOTE)
        self.assertIn(_RETIRED, note)
        self.assertNotIn("intercom", _without(text, note).casefold())

    def test_handling_note_stops_detection_recording_and_recommendation(self) -> None:
        note = _section(_text(_DISCOVERY), _DISCOVERY_NOTE)
        for phrase in ("never detect", "never record", "never recommend"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, note)

    def test_generated_profile_skeleton_records_no_retired_pack_block(self) -> None:
        for info in REMOVED_CAPABILITY_PACKS.values():
            self.assertNotIn(info.profile_block_key, _profile_skeleton(_text(_DISCOVERY)))

    def test_generated_profile_skeleton_pins_the_current_profile_contract(self) -> None:
        profile = _render_profile(_text(_DISCOVERY))
        self.assertEqual(profile["schema_version"], SCHEMA_CONTRACTS["profile"]["current_version"])

    def test_generated_profile_skeleton_validates_against_the_current_profile_schema(self) -> None:
        schema = json.loads(_text(_PROFILE_SCHEMA))
        profile = _render_profile(_text(_DISCOVERY))
        errors = [error.message for error in Draft7Validator(schema).iter_errors(profile)]
        self.assertEqual(errors, [])


class TuneRetiredPackTests(unittest.TestCase):
    def test_tune_names_the_retired_pack_only_in_its_cleanup_section(self) -> None:
        text = _text(_TUNE)
        section = _section(text, _TUNE_SECTION)
        self.assertIn(_RETIRED, section)
        self.assertNotIn("intercom", _without(text, section).casefold())

    def test_cleanup_section_documents_the_offered_cleanup_items(self) -> None:
        section = _section(_text(_TUNE), _TUNE_SECTION)
        for item in (
            "capability_packs",
            "capability_pack_overlays",
            _OVERLAY_FILE,
            "woven sections",
            "remove-retired-capability-pack",
            "removed-capability-pack",
        ):
            with self.subTest(item=item):
                self.assertIn(item, section)

    def test_cleanup_section_applies_the_checksum_rule_and_never_auto_deletes(self) -> None:
        section = _section(_text(_TUNE), _TUNE_SECTION)
        self.assertIn("checksum matches", section)
        self.assertIn("manual_review: true", section)
        self.assertIn("never auto-delete", section)

    def test_cleanup_section_is_proposal_only_backed_up_and_never_re_weaves(self) -> None:
        section = _section(_text(_TUNE), _TUNE_SECTION)
        self.assertIn("proposal-only", section)
        self.assertIn(".autoharness/backups/", section)
        self.assertIn("never re-weave", section)

    def test_retired_pack_is_a_named_drift_category_and_maps_to_a_proposal_source(self) -> None:
        text = _text(_TUNE)
        categories = _section(text, "#### Step 1.2: Categorize Drift")
        self.assertIn("Retired capability pack", categories)
        mapping = _section(text, "#### Step 2.2: Generate Change Proposals")
        self.assertIn("source: retired-pack", mapping)

    def test_no_weaving_or_enable_rows_remain_for_the_retired_pack(self) -> None:
        text = _text(_TUNE)
        outside = _without(text, _section(text, _TUNE_SECTION)).casefold()
        self.assertNotIn("heartbeat", outside)
        self.assertNotIn("remote operator workflow", outside)


class VerifyHarnessEventContractTests(unittest.TestCase):
    def test_dark_factory_event_contract_points_at_the_policy_visibility_protocol(self) -> None:
        text = _text(_VERIFY)
        self.assertNotIn("intercom", text.casefold())
        self.assertIn("P-017 Dark Factory Visibility Protocol", text)


if __name__ == "__main__":
    unittest.main()
