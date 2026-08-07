"""Structural contract tests for the 111-F crash-resumption + prune-on-restore
protocol (119-S / 111.001-T, 111.002-T, 111.003-T, 111.004-T, 111.006-T,
111.007-T).

These tests assert:

* the Orchestrator template + installed mirror contain the owner-exclusive
  routing protocol (zero-candidate no-op, explicit operator selection,
  ownership validation, fail-closed-on-ambiguity, degraded backlogit-
  unreachable fallback);
* the Stage and Ship templates + installed mirrors each contain their own
  owner-scoped Crash-Resumption / Startup Recovery Protocol, including the
  H3 ordering invariant that resolve-checkpoint only happens after a
  confirmed successful resume (never before);
* the backlogit-pack overlay instruction template + installed mirror
  contain the Checkpoint-Recovery / Prune-on-Restore Protocol, including its
  own degraded engram-unreachable fail-closed fallback (never a
  file-based-prune continuation);
* the harness manifest tracks a single (non-dual) checksum for each of these
  six artifacts, matching the artifact's actual on-disk bytes.
"""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]

_ORCH_TEMPLATE = _REPO_ROOT / "templates" / "agents" / "_orchestrator.agent.md.tmpl"
_ORCH_MIRROR = _REPO_ROOT / ".github" / "agents" / "_orchestrator.agent.md"

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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class OrchestratorCrashResumptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = _read(_ORCH_TEMPLATE)
        cls.mirror = _read(_ORCH_MIRROR)

    def test_files_exist(self) -> None:
        self.assertTrue(_ORCH_TEMPLATE.is_file())
        self.assertTrue(_ORCH_MIRROR.is_file())

    def test_zero_candidate_is_normal_startup_not_failure(self) -> None:
        for text in (self.template, self.mirror):
            self.assertIn("Zero-candidate case", text)
            self.assertIn("EXPLICITLY NOT a failure", text)

    def test_owner_exclusive_routing_never_performed_directly(self) -> None:
        for text in (self.template, self.mirror):
            self.assertIn("Owner-exclusive routing", text)
            self.assertIn(
                "MUST NEVER execute Stage-owned or Ship-owned "
                "restore/resume/prune/resolve work itself",
                text,
            )

    def test_fail_closed_on_ambiguity_among_existing_candidates_only(self) -> None:
        for text in (self.template, self.mirror):
            self.assertIn("Fail closed on ambiguity", text)
            self.assertIn(
                "never triggered by the zero-candidate case", text
            )

    def test_no_dead_session_auto_recovery(self) -> None:
        for text in (self.template, self.mirror):
            self.assertIn("No dead-session auto-recovery", text)
            self.assertIn("no heartbeat, session-lock, or lease", text)

    def test_degraded_backlogit_unreachable_fallback(self) -> None:
        for text in (self.template, self.mirror):
            self.assertIn("Degraded fallback", text)
            self.assertIn("backlogit", text.split("Degraded fallback", 1)[1][:400])
            self.assertIn("NO auto-resume", text)

    def test_ordering_zero_candidate_precedes_fail_closed(self) -> None:
        for text in (self.template, self.mirror):
            zero_idx = text.find("Zero-candidate case")
            fail_idx = text.find("Fail closed on ambiguity")
            self.assertNotEqual(zero_idx, -1)
            self.assertNotEqual(fail_idx, -1)
            self.assertLess(zero_idx, fail_idx)

    def test_deferred_candidates_noted(self) -> None:
        for text in (self.template, self.mirror):
            self.assertIn("34D50F2D", text)
            self.assertIn("DEFERRED", text)


class OwnerAgentCrashResumptionTests(unittest.TestCase):
    """Shared contract shape for Stage (agent: stage) and Ship (agent: ship)."""

    def _assert_owner_protocol(self, text: str, owner: str, other: str) -> None:
        self.assertIn("Crash-Resumption / Startup Recovery Protocol", text)
        self.assertIn("ZERO-CANDIDATE NORMAL STARTUP", text)
        self.assertIn("EXPLICIT OPERATOR SELECTION", text)
        self.assertIn("OWNER VALIDATION", text)
        self.assertIn("OWNER-EXCLUSIVE, OPERATOR-CONFIRMED RESTORE", text)
        self.assertIn("OWNER-SCOPED RESOLUTION", text)
        self.assertIn("FAIL CLOSED", text)
        self.assertIn("NO FRESH-START FALLBACK", text)
        self.assertIn(f"agent: {owner}", text)
        self.assertIn("cross-role handling of any kind", text)
        # H3: resolve is invoked ONLY AFTER confirmed successful resume — never before.
        self.assertIn("ONLY AFTER", text)
        self.assertIn("never before, never on ambiguous or torn state", text)
        # never cross-role resolve
        self.assertIn(f"NEVER resolve a `{other}`-owned checkpoint", text)

    def _assert_ordering_confirm_before_resolve(self, text: str) -> None:
        confirm_idx = text.find("OWNER-EXCLUSIVE, OPERATOR-CONFIRMED RESTORE")
        resolve_idx = text.find("OWNER-SCOPED RESOLUTION")
        self.assertNotEqual(confirm_idx, -1)
        self.assertNotEqual(resolve_idx, -1)
        self.assertLess(
            confirm_idx,
            resolve_idx,
            "operator-confirmed restore section must precede owner-scoped "
            "resolution section (H3 ordering)",
        )

    def test_stage_template_and_mirror(self) -> None:
        for text in (_read(_STAGE_TEMPLATE), _read(_STAGE_MIRROR)):
            self._assert_owner_protocol(text, owner="stage", other="ship")
            self._assert_ordering_confirm_before_resolve(text)

    def test_ship_template_and_mirror(self) -> None:
        for text in (_read(_SHIP_TEMPLATE), _read(_SHIP_MIRROR)):
            self._assert_owner_protocol(text, owner="ship", other="stage")
            self._assert_ordering_confirm_before_resolve(text)

    def test_stage_never_handles_ship_owned_checkpoints(self) -> None:
        for text in (_read(_STAGE_TEMPLATE), _read(_STAGE_MIRROR)):
            self.assertIn("never selectable here", text)

    def test_ship_never_handles_stage_owned_checkpoints(self) -> None:
        for text in (_read(_SHIP_TEMPLATE), _read(_SHIP_MIRROR)):
            self.assertIn("never selectable here", text)


class BacklogitOverlayCheckpointRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = _read(_BACKLOGIT_OVERLAY_TEMPLATE)
        cls.mirror = _read(_BACKLOGIT_OVERLAY_MIRROR)

    def test_files_exist(self) -> None:
        self.assertTrue(_BACKLOGIT_OVERLAY_TEMPLATE.is_file())
        self.assertTrue(_BACKLOGIT_OVERLAY_MIRROR.is_file())

    def test_checkpoint_recovery_section_present(self) -> None:
        for text in (self.template, self.mirror):
            self.assertIn(
                "Checkpoint-Recovery / Prune-on-Restore Protocol", text
            )

    def test_bounded_read_select_summarize_pruning(self) -> None:
        for text in (self.template, self.mirror):
            section = text.split(
                "Checkpoint-Recovery / Prune-on-Restore Protocol", 1
            )[1]
            self.assertIn("prune", section.lower())
            self.assertIn("cursor", section.lower())

    def test_engram_unreachable_fails_closed_no_file_prune_fallback(self) -> None:
        for text in (self.template, self.mirror):
            section = text.split(
                "Checkpoint-Recovery / Prune-on-Restore Protocol", 1
            )[1]
            self.assertIn("engram", section.lower())
            self.assertIn("fail", section.lower())
            self.assertIn("operator handoff", section.lower())
            # The section must explicitly say the file-based prune degradation
            # path is NOT used, rather than merely omitting the phrase.
            self.assertIn(
                "file-based prune", section.lower()
            )
            self.assertIn("is not used", section.lower())

    def test_no_unresolved_placeholders(self) -> None:
        import re

        placeholder_re = re.compile(r"\{\{[A-Z0-9_]+\}\}")
        # Strip fenced code blocks before scanning, matching verify_workspace's
        # own PLACEHOLDER_RE / CODE_FENCE_RE convention.
        lines = self.mirror.splitlines()
        in_fence = False
        remaining: list[str] = []
        for line in lines:
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence:
                remaining.append(line)
        self.assertFalse(
            placeholder_re.search("\n".join(remaining)),
            "installed backlogit.instructions.md must have zero unresolved "
            "{{VARIABLE}} placeholders",
        )


class ManifestChecksumCoherenceTests(unittest.TestCase):
    """Single-checksum (not dual installed_checksum/source_checksum, not a
    drift comparison) coherence for the six artifacts this shipment touched."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = yaml.safe_load(_read(_MANIFEST_PATH))

    def _artifact(self, path: str) -> dict:
        return next(
            item
            for item in self.manifest["artifacts"]
            if item.get("path") == path
        )

    def _assert_checksum_matches(self, rel_path: str) -> None:
        artifact = self._artifact(rel_path)
        self.assertIn("checksum", artifact)
        self.assertNotIn("installed_checksum", artifact)
        self.assertNotIn("source_checksum", artifact)
        digest = hashlib.sha256(
            (_REPO_ROOT / rel_path).read_bytes()
        ).hexdigest()
        self.assertEqual(
            artifact["checksum"],
            digest,
            f"manifest checksum drift for {rel_path}",
        )

    def test_orchestrator_mirror_checksum(self) -> None:
        self._assert_checksum_matches(".github/agents/_orchestrator.agent.md")

    def test_stage_mirror_checksum(self) -> None:
        self._assert_checksum_matches(".github/agents/_stage.agent.md")

    def test_ship_mirror_checksum(self) -> None:
        self._assert_checksum_matches(".github/agents/_ship.agent.md")

    def test_install_harness_skill_checksum(self) -> None:
        self._assert_checksum_matches(".github/skills/install-harness/SKILL.md")

    def test_tune_harness_skill_checksum(self) -> None:
        self._assert_checksum_matches(".github/skills/tune-harness/SKILL.md")

    def test_backlogit_instruction_checksum(self) -> None:
        self._assert_checksum_matches(
            ".github/instructions/backlogit.instructions.md"
        )

    def test_backlogit_instruction_artifact_registered(self) -> None:
        artifact = self._artifact(".github/instructions/backlogit.instructions.md")
        self.assertEqual(
            artifact.get("template"),
            "instructions/backlogit.instructions.md.tmpl",
        )

    def test_backlogit_overlay_verification_checks_present(self) -> None:
        overlay = next(
            item
            for item in self.manifest["capability_pack_overlays"]
            if item.get("pack") == "backlogit"
        )
        checks_text = "\n".join(overlay.get("verification_checks", []))
        self.assertIn("backlogit.instructions.md installed", checks_text)
        self.assertIn("Crash-Resumption Protocol", checks_text)
        self.assertIn("Checkpoint-Recovery / Prune-on-Restore Protocol", checks_text)


if __name__ == "__main__":
    unittest.main()
