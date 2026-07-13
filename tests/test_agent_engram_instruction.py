"""Structural routing contract tests for the agent-engram instruction."""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = (
    _REPO_ROOT / "templates" / "instructions" / "agent-engram.instructions.md.tmpl"
)
_DOGFOOD = (
    _REPO_ROOT / ".github" / "instructions" / "agent-engram.instructions.md"
)

_STRUCTURAL_TERMS = (
    "callers/callees",
    "impact analysis",
    "symbol lookup",
    "blast-radius checks",
    "inheritance",
    "implementations",
    "implementers",
    '"where/how is this implemented?"',
)


class AgentEngramInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = _TEMPLATE.read_text(encoding="utf-8")
        cls.dogfood = _DOGFOOD.read_text(encoding="utf-8")

    def test_files_exist(self) -> None:
        self.assertTrue(_TEMPLATE.is_file(), f"missing template: {_TEMPLATE}")
        self.assertTrue(_DOGFOOD.is_file(), f"missing dogfood mirror: {_DOGFOOD}")

    def test_structural_queries_must_route_before_grep(self) -> None:
        for text in (self.template, self.dogfood):
            normalized = text.lower()
            self.assertIn(
                "structural code questions must route through the "
                "agent-engram code-graph tools",
                normalized,
            )
            self.assertIn("before grep/ripgrep or raw file reads", normalized)
            self.assertIn("unless a direct-tool exemption applies", normalized)
            for term in _STRUCTURAL_TERMS:
                self.assertIn(term, normalized)

    def test_required_graph_tools_remain_named(self) -> None:
        for text in (self.template, self.dogfood):
            self.assertIn("`list_symbols`", text)
            self.assertIn("`map_code`", text)
            self.assertIn("`impact_analysis`", text)
            self.assertIn("`query_graph`", text)
            self.assertIn("`query_graph_neighborhood`", text)

    def test_direct_tool_exemptions_are_preserved(self) -> None:
        for text in (self.template, self.dogfood):
            normalized = text.lower()
            self.assertIn("literal-text or regex", normalized)
            self.assertIn("already know the exact file path", normalized)
            self.assertIn("trivial single-file", normalized)


if __name__ == "__main__":
    unittest.main()
