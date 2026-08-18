"""Structural contract tests for the 130-F checkpoint payload contract
(139-S / 130.001-T, 130.002-T, 130.003-T, 130.004-T, 130.005-T, 130.006-T).

These tests assert:

* the backlogit overlay instruction template + installed mirror carry a
  canonical ``Checkpoint Payload Contract`` subsection stating rules 1-5
  (schema_version, official create path, required fields, context nesting,
  auto-populated timestamps) plus a fenced, parseable, placeholder-free JSON
  example, scoped explicitly to backlogit structured checkpoints only (not
  the markdown ``docs/memory/`` continuity artifact);
* each of the four agent-template write sites (Stage x2, Ship x2) and their
  two installed mirror insertions carry the non-negotiable minimum
  (``schema_version: 1``, the official create operation, and ``context``
  nesting) plus a pointer to the canonical contract section, without
  restating rules 1-5 in full;
* no surface instructs top-level (i.e. NOT nested under ``context``)
  placement of ``feature_id``, ``shipment_id``, ``stash_source``, ``mode``,
  ``route``, or ``artifacts`` — the exact malformed shape this shipment
  exists to prevent;
* the registry declares a ``cli_command`` fallback for ``create_checkpoint``
  in both the installed registry and its template;
* the harness manifest tracks a single (non-dual) checksum for each touched
  artifact, matching its actual on-disk bytes, and the backlogit overlay's
  verification_checks name the Checkpoint Payload Contract.
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]

_STAGE_TEMPLATE = _REPO_ROOT / "templates" / "agents" / "_stage.agent.md.tmpl"
_STAGE_MIRROR = _REPO_ROOT / ".github" / "agents" / "_stage.agent.md"

_SHIP_TEMPLATE = _REPO_ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
_SHIP_MIRROR = _REPO_ROOT / ".github" / "agents" / "_ship.agent.md"

_BACKLOGIT_OVERLAY_TEMPLATE = (
    _REPO_ROOT / "templates" / "instructions" / "backlogit.instructions.md.tmpl"
)
_BACKLOGIT_OVERLAY_MIRROR = (
    _REPO_ROOT / ".github" / "instructions" / "backlogit.instructions.md"
)

_MANIFEST_PATH = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"

_INSTALLED_REGISTRY = _REPO_ROOT / ".autoharness" / "backlog-registry.yaml"
_TEMPLATE_REGISTRY = (
    _REPO_ROOT / "templates" / "backlog" / "registries" / "backlogit.registry.yaml"
)

_CONTRACT_HEADING = "### Checkpoint Payload Contract"
_FENCE_RE = re.compile(r"```(?:json)?\n(.*?)```", re.DOTALL)
_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")

_DOMAIN_KEYS = ("feature_id", "shipment_id", "stash_source", "mode", "route", "artifacts")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_fences(text: str) -> str:
    lines = text.splitlines()
    in_fence = False
    remaining: list[str] = []
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            remaining.append(line)
    return "\n".join(remaining)


class BacklogitOverlayCheckpointPayloadContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = _read(_BACKLOGIT_OVERLAY_TEMPLATE)
        cls.mirror = _read(_BACKLOGIT_OVERLAY_MIRROR)

    def test_files_exist(self) -> None:
        self.assertTrue(_BACKLOGIT_OVERLAY_TEMPLATE.is_file())
        self.assertTrue(_BACKLOGIT_OVERLAY_MIRROR.is_file())

    def test_contract_section_present(self) -> None:
        for text in (self.template, self.mirror):
            self.assertIn(_CONTRACT_HEADING, text)

    def test_contract_requires_schema_version_1(self) -> None:
        for text in (self.template, self.mirror):
            section = text.split(_CONTRACT_HEADING, 1)[1]
            self.assertIn('"schema_version": 1', section)
            self.assertIn("schema_version", section)

    def test_contract_requires_official_create_path(self) -> None:
        for text in (self.template, self.mirror):
            section = text.split(_CONTRACT_HEADING, 1)[1]
            self.assertIn("backlogit_create_checkpoint", section)
            self.assertIn("backlogit checkpoint create", section)
            self.assertIn("never", section.lower())

    def test_contract_requires_context_nesting(self) -> None:
        for text in (self.template, self.mirror):
            section = text.split(_CONTRACT_HEADING, 1)[1]
            self.assertIn("`context`", section)
            self.assertIn("MUST NOT be hoisted to the top level", section)

    def test_contract_requires_core_fields(self) -> None:
        for text in (self.template, self.mirror):
            section = text.split(_CONTRACT_HEADING, 1)[1]
            for field in ("agent", "session_id", "phase", "resume_hint"):
                self.assertIn(f"`{field}`", section)

    def test_contract_notes_autopopulated_timestamps(self) -> None:
        for text in (self.template, self.mirror):
            section = text.split(_CONTRACT_HEADING, 1)[1]
            self.assertIn("created_at", section)
            self.assertIn("updated_at", section)

    def test_contract_scope_excludes_markdown_memory(self) -> None:
        for text in (self.template, self.mirror):
            section = text.split(_CONTRACT_HEADING, 1)[1]
            self.assertIn("backlogit structured checkpoints only", section)
            self.assertIn("docs/memory/", section)
            self.assertIn("takes no `schema_version`", section)

    def test_fenced_example_present_and_parses(self) -> None:
        for text in (self.template, self.mirror):
            section = text.split(_CONTRACT_HEADING, 1)[1]
            match = _FENCE_RE.search(section)
            self.assertIsNotNone(match, "expected a fenced JSON example in the contract section")
            payload = json.loads(match.group(1))
            self.assertEqual(payload["schema_version"], 1)
            self.assertIsInstance(payload["context"], dict)
            for key in _DOMAIN_KEYS:
                self.assertNotIn(key, payload)

    def test_no_unresolved_placeholders_in_mirror(self) -> None:
        stripped = _strip_fences(self.mirror)
        self.assertFalse(
            _PLACEHOLDER_RE.search(stripped),
            "installed backlogit.instructions.md must have zero unresolved "
            "{{VARIABLE}} placeholders",
        )


class WriteSiteMinimumTests(unittest.TestCase):
    """Shared assertions for the non-negotiable per-write-site minimum:
    schema_version: 1, official create path, context nesting, and a pointer
    to the canonical contract section — without restating rules 1-5 in full.
    """

    def _assert_write_site_minimum(self, section: str) -> None:
        self.assertIn("schema_version", section)
        self.assertIn("1", section)
        self.assertIn("context", section)
        self.assertIn("Checkpoint Payload Contract", section)
        # Item 3 of the T7 assertion list: each write site references the
        # official create operation and prohibits direct file writes (the
        # prohibition itself lives in the canonical contract section, but
        # each site must at minimum name the official path as the required
        # route).
        self.assertIn("official create operation", section)

    def test_stage_template_write_sites(self) -> None:
        text = _read(_STAGE_TEMPLATE)
        # Mid-session checkpoint write site
        mid_section = text.split("### Mid-session checkpoints", 1)[1].split(
            "### Session end", 1
        )[0]
        self._assert_write_site_minimum(mid_section)
        # Session-end checkpoint write site
        end_section = text.split("### Session end", 1)[1].split(
            "### Context Overflow Protocol", 1
        )[0]
        self._assert_write_site_minimum(end_section)

    def test_ship_template_write_sites(self) -> None:
        text = _read(_SHIP_TEMPLATE)
        mid_section = text.split("### Mid-session checkpoints", 1)[1].split(
            "### Learnings capture", 1
        )[0]
        self._assert_write_site_minimum(mid_section)
        end_section = text.split("### Session end", 1)[1].split(
            "## Stop Conditions", 1
        )[0]
        self._assert_write_site_minimum(end_section)

    def test_stage_mirror_write_site(self) -> None:
        text = _read(_STAGE_MIRROR)
        section = text.split("### Step 6: Session Continuity", 1)[1].split(
            "## Stop Conditions", 1
        )[0]
        self._assert_write_site_minimum(section)

    def test_ship_mirror_write_site(self) -> None:
        text = _read(_SHIP_MIRROR)
        section = text.split("5. Write session memory to `docs/memory/`.", 1)[1][:1200]
        self._assert_write_site_minimum(section)


class NegativeAntiRegressionTests(unittest.TestCase):
    """The exact malformed shape (top-level domain fields) must not be
    instructable at any write site. Anchored to the contract block and the
    fenced examples rather than bare substrings (H8) — legitimate prose in
    these files uses words like ``mode``, ``route``, and ``artifacts``
    elsewhere, so this scans only the checkpoint-write-site sections plus
    the canonical contract sections for an *instructional pattern* placing
    those fields outside `context`.
    """

    _TOP_LEVEL_HOIST_RE = re.compile(
        r"top[- ]level\s+`?(feature_id|shipment_id|stash_source|mode|route|artifacts)`?"
    )

    def _assert_no_top_level_hoist_instruction(self, section: str) -> None:
        # The only permitted mention of "top level" + a domain key is the
        # prohibition itself (contract rule 4), not an instruction to place
        # domain keys there. We assert the fenced examples never contain the
        # domain keys outside of `context`, and that any explicit top-level
        # domain key mention is a negation (never / MUST NOT / not).
        for match in self._TOP_LEVEL_HOIST_RE.finditer(section):
            window_start = max(0, match.start() - 40)
            window = section[window_start : match.end()]
            self.assertTrue(
                any(neg in window for neg in ("never", "NEVER", "MUST NOT", "not be")),
                f"unexpected non-negated top-level domain-field mention: {window!r}",
            )

    def test_overlay_contract_sections(self) -> None:
        for path in (_BACKLOGIT_OVERLAY_TEMPLATE, _BACKLOGIT_OVERLAY_MIRROR):
            text = _read(path)
            section = text.split(_CONTRACT_HEADING, 1)[1]
            self._assert_no_top_level_hoist_instruction(section)

    def test_agent_write_sites(self) -> None:
        for path in (_STAGE_TEMPLATE, _SHIP_TEMPLATE, _STAGE_MIRROR, _SHIP_MIRROR):
            text = _read(path)
            self._assert_no_top_level_hoist_instruction(text)


class RegistryCliFallbackTests(unittest.TestCase):
    def _assert_create_checkpoint_cli_fallback(self, path: Path) -> None:
        registry = yaml.safe_load(_read(path))
        operations = registry.get("operations", registry)
        create_checkpoint = None
        if isinstance(operations, dict) and "create_checkpoint" in operations:
            create_checkpoint = operations["create_checkpoint"]
        else:
            # search nested structure defensively
            def _find(obj):
                if isinstance(obj, dict):
                    if "create_checkpoint" in obj:
                        return obj["create_checkpoint"]
                    for value in obj.values():
                        found = _find(value)
                        if found is not None:
                            return found
                return None

            create_checkpoint = _find(registry)
        self.assertIsNotNone(create_checkpoint, f"create_checkpoint operation not found in {path}")
        self.assertIn("cli_command", create_checkpoint)
        self.assertIn("backlogit checkpoint create", create_checkpoint["cli_command"])

    def test_installed_registry(self) -> None:
        self._assert_create_checkpoint_cli_fallback(_INSTALLED_REGISTRY)

    def test_template_registry(self) -> None:
        self._assert_create_checkpoint_cli_fallback(_TEMPLATE_REGISTRY)


class ManifestChecksumCoherenceTests(unittest.TestCase):
    """Single-checksum (not dual installed_checksum/source_checksum) coherence
    for the artifacts this shipment touches."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = yaml.safe_load(_read(_MANIFEST_PATH))

    def _artifact(self, path: str) -> dict:
        return next(
            item for item in self.manifest["artifacts"] if item.get("path") == path
        )

    def _assert_checksum_matches(self, rel_path: str) -> None:
        artifact = self._artifact(rel_path)
        self.assertIn("checksum", artifact)
        self.assertNotIn("installed_checksum", artifact)
        self.assertNotIn("source_checksum", artifact)
        digest = hashlib.sha256((_REPO_ROOT / rel_path).read_bytes()).hexdigest()
        self.assertEqual(
            artifact["checksum"], digest, f"manifest checksum drift for {rel_path}"
        )

    def test_stage_mirror_checksum(self) -> None:
        self._assert_checksum_matches(".github/agents/_stage.agent.md")

    def test_ship_mirror_checksum(self) -> None:
        self._assert_checksum_matches(".github/agents/_ship.agent.md")

    def test_backlogit_instruction_checksum(self) -> None:
        self._assert_checksum_matches(".github/instructions/backlogit.instructions.md")

    def test_backlogit_overlay_verification_checks_present(self) -> None:
        overlay = next(
            item
            for item in self.manifest["capability_pack_overlays"]
            if item.get("pack") == "backlogit"
        )
        checks_text = "\n".join(overlay.get("verification_checks", []))
        self.assertIn("Checkpoint Payload Contract", checks_text)


class VolumeConstraintTests(unittest.TestCase):
    """H13: the newly-inserted mirror write-site guidance must carry the
    existing volume constraints so structured checkpoint writes do not flood
    the mandatory unfiltered startup scan with active candidates."""

    def _assert_volume_constraints(self, section: str) -> None:
        self.assertIn("at most one", section.lower())
        self.assertIn("resolve", section.lower())

    def test_stage_mirror_session_end(self) -> None:
        text = _read(_STAGE_MIRROR)
        section = text.split("### Step 6: Session Continuity", 1)[1].split(
            "## Stop Conditions", 1
        )[0]
        self._assert_volume_constraints(section)

    def test_ship_mirror_session_end(self) -> None:
        text = _read(_SHIP_MIRROR)
        section = text.split("5. Write session memory to `docs/memory/`.", 1)[1][:1200]
        self._assert_volume_constraints(section)


if __name__ == "__main__":
    unittest.main()
