"""Tests for startup-script contract classification and migration planning."""

from __future__ import annotations

import unittest
from pathlib import Path

from autoharness.startup_script_contract import (
    STARTUP_SCRIPT_CONTRACTS,
    classify_startup_script,
    plan_startup_script_migration,
    resolve_startup_script_shell,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class StartupScriptContractTests(unittest.TestCase):
    def test_missing_classification_for_both_shells(self) -> None:
        for shell in ("ps1", "sh"):
            with self.subTest(shell=shell):
                classification = classify_startup_script(shell, None)

                self.assertEqual(classification["status"], "missing")
                self.assertEqual(classification["shell"], shell)
                self.assertTrue(classification["evidence"])

    def test_current_templates_classify_as_current_without_proposal(self) -> None:
        for shell in ("ps1", "sh"):
            with self.subTest(shell=shell):
                classification = classify_startup_script(shell, self._read_template(shell))

                self.assertEqual(classification["status"], "current")
                self.assertNotIn("custom_sections", classification)
                self.assertIsNone(
                    plan_startup_script_migration(shell, self._relative_path(shell), classification)
                )

    def test_known_legacy_classification_emits_degrading_proposal(self) -> None:
        for shell in ("ps1", "sh"):
            with self.subTest(shell=shell):
                content = "\n".join(STARTUP_SCRIPT_CONTRACTS[shell]["legacy_markers"])
                classification = classify_startup_script(shell, content)
                proposal = plan_startup_script_migration(
                    shell,
                    self._relative_path(shell),
                    classification,
                )
                proposal_data = proposal or {}

                self.assertEqual(classification["status"], "known-legacy")
                self.assertIsNotNone(proposal)
                self.assertEqual(proposal_data["severity"], "degrading")
                self.assertFalse(proposal_data["manual_review"])

    def test_customized_classification_preserves_custom_tail(self) -> None:
        for shell in ("ps1", "sh"):
            with self.subTest(shell=shell):
                content = (
                    self._read_template(shell)
                    + "\n# ── Custom ──────────────────────────────────────────────────────────\n"
                    + "# operator-specific custom command\n"
                )
                classification = classify_startup_script(shell, content)
                proposal = plan_startup_script_migration(
                    shell,
                    self._relative_path(shell),
                    classification,
                )
                proposal_data = proposal or {}

                self.assertEqual(classification["status"], "customized")
                self.assertTrue(classification["custom_sections"].strip())
                self.assertIn("operator-specific custom command", classification["custom_sections"])
                self.assertIsNotNone(proposal)
                self.assertEqual(
                    proposal_data["custom_sections"],
                    classification["custom_sections"],
                )

    def test_ambiguous_classification_covers_unrecognized_and_unknown_version(self) -> None:
        for shell in ("ps1", "sh"):
            with self.subTest(shell=shell, case="unrecognized-content"):
                classification = classify_startup_script(shell, "Write-Host 'hello'\n")
                proposal = plan_startup_script_migration(
                    shell,
                    self._relative_path(shell),
                    classification,
                )
                proposal_data = proposal or {}
                self.assertEqual(classification["status"], "ambiguous")
                self.assertIsNotNone(proposal)
                self.assertTrue(proposal_data["manual_review"])

            with self.subTest(shell=shell, case="unknown-manifest-version"):
                classification = classify_startup_script(
                    shell,
                    self._read_template(shell),
                    manifest_contract_version="2.0.0",
                )
                proposal = plan_startup_script_migration(
                    shell,
                    self._relative_path(shell),
                    classification,
                )
                proposal_data = proposal or {}
                self.assertEqual(classification["status"], "ambiguous")
                self.assertIsNotNone(proposal)
                self.assertTrue(proposal_data["manual_review"])

    def test_current_classification_is_idempotent(self) -> None:
        for shell in ("ps1", "sh"):
            with self.subTest(shell=shell):
                content = self._read_template(shell)
                first = classify_startup_script(shell, content)
                second = classify_startup_script(shell, content)

                self.assertEqual(first["status"], "current")
                self.assertEqual(second["status"], "current")
                self.assertIsNone(
                    plan_startup_script_migration(shell, self._relative_path(shell), first)
                )
                self.assertIsNone(
                    plan_startup_script_migration(shell, self._relative_path(shell), second)
                )

    def test_resolve_startup_script_shell_prefers_template_then_path(self) -> None:
        self.assertEqual(
            resolve_startup_script_shell("scripts/ignored.txt", "scripts/start.ps1.tmpl"),
            "ps1",
        )
        self.assertEqual(
            resolve_startup_script_shell("scripts/ignored.txt", "scripts/start.sh.tmpl"),
            "sh",
        )
        self.assertEqual(resolve_startup_script_shell("start.ps1"), "ps1")
        self.assertEqual(resolve_startup_script_shell("nested/start.sh"), "sh")
        self.assertIsNone(resolve_startup_script_shell("README.md", "some/other.tmpl"))

    @staticmethod
    def _read_template(shell: str) -> str:
        template_name = Path(STARTUP_SCRIPT_CONTRACTS[shell]["template"]).name
        return (REPO_ROOT / "templates" / "scripts" / template_name).read_text(encoding="utf-8")

    @staticmethod
    def _relative_path(shell: str) -> str:
        return "start.ps1" if shell == "ps1" else "start.sh"
