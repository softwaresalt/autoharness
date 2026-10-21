"""Contract tests for 214.002-T: P-012 per-operation surface choice (MCP and CLI as equal peers)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"
_MIRROR = _REPO_ROOT / ".github" / "policies" / "workflow-policies.md"


def _lf_text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def _p012(text: str) -> str:
    start = text.index("## P-012:")
    end = text.index("\n## P-013", start)
    return text[start:end]


class P012SurfaceChoiceTests(unittest.TestCase):
    def _each(self):
        for path in (_TEMPLATE, _MIRROR):
            yield path, _p012(_lf_text(path))

    def test_equal_peer_rule_present(self) -> None:
        for path, section in self._each():
            with self.subTest(path=path.name):
                self.assertIn("equal supported surfaces", section)
                self.assertIn("without trying the other first", section)

    def test_three_report_tokens_present(self) -> None:
        for path, section in self._each():
            with self.subTest(path=path.name):
                self.assertIn("TOOL_OK: {operation} via {mcp|cli}", section)
                self.assertIn("TOOL_DEGRADED: {operation}", section)
                self.assertIn("TOOL_UNAVAILABLE: {operation}", section)

    def test_cli_only_on_mcp_failure_wording_removed(self) -> None:
        for path, section in self._each():
            with self.subTest(path=path.name):
                self.assertNotIn("using CLI fallback", section)
                self.assertNotIn("registry-declared CLI fallback", section)

    def test_forbidden_substitution_language_preserved(self) -> None:
        for path, section in self._each():
            with self.subTest(path=path.name):
                self.assertIn("Silently bypassing a configured backlog tool", section)
                self.assertIn("undeclared command", section)
                self.assertIn("filesystem or cache edit", section)

    def test_argument_elements_and_non_idempotent_retry_rules(self) -> None:
        for path, section in self._each():
            with self.subTest(path=path.name):
                self.assertIn("separate argument elements", section)
                self.assertIn("non-idempotent mutation", section)

    def test_hook_ack_concrete_sequence_only(self) -> None:
        for path, section in self._each():
            with self.subTest(path=path.name):
                self.assertIn("highest concrete event sequence", section)
                self.assertIn("never a derived signal", section)

    def test_log_telemetry_stays_mcp_only(self) -> None:
        for path, section in self._each():
            with self.subTest(path=path.name):
                self.assertIn("`log_telemetry`", section)

    def test_version_row_1_38_0_in_template_and_mirror(self) -> None:
        for path in (_TEMPLATE, _MIRROR):
            with self.subTest(path=path.name):
                self.assertRegex(_lf_text(path), re.compile(r"^\| 1\.38\.0 +\|", re.MULTILINE))

    def test_p012_section_identical_in_template_and_mirror(self) -> None:
        self.assertEqual(_p012(_lf_text(_TEMPLATE)), _p012(_lf_text(_MIRROR)))


if __name__ == "__main__":
    unittest.main()
