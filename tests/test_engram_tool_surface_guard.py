"""Pinned registered-engram-tool guard.

Every backticked snake_case token in the agent-engram guidance surfaces must be
a registered engram MCP tool, a declared feature-gated tool, or a documented
``query_graph`` operation/parameter. Internal helpers such as
``query_graph_neighborhood`` are not registered tools and must not be advised.

Refresh procedure: the registered set below is transcribed from the engram
repository fixture ``tests/fixtures/mcp_tool_catalog.expected.json`` at engram
commit ``006af541`` (21 tools). When engram registers or removes a tool, update
``REGISTERED_TOOLS`` here from the new fixture in the same change that updates
the guidance, and bump the pinned commit in this docstring.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

REGISTERED_TOOLS = frozenset(
    {
        "set_workspace",
        "get_daemon_status",
        "get_workspace_status",
        "flush_state",
        "query_memory",
        "get_workspace_statistics",
        "index_workspace",
        "sync_workspace",
        "map_code",
        "list_symbols",
        "unified_search",
        "impact_analysis",
        "lint_dax",
        "get_health_report",
        "get_branch_metrics",
        "get_token_savings_report",
        "get_evaluation_report",
        "run_retrieval_eval",
        "get_retrieval_eval_report",
        "query_graph",
        "get_mutable_script_retry_metrics",
    }
)

# Tools registered only when the engram build enables the named cargo feature.
FEATURE_GATED_TOOLS = frozenset({"index_git_history"})  # feature: git-graph

# query_graph operation names and parameter names that are not tools.
QUERY_GRAPH_VOCABULARY = frozenset(
    {
        "find_path",
        "transitive_closure",
        "max_depth",
        "max_nodes",
        "edge_types",
    }
)

_GUIDANCE_FILES = (
    _REPO_ROOT / "templates" / "instructions" / "agent-engram.instructions.md.tmpl",
    _REPO_ROOT / ".github" / "instructions" / "agent-engram.instructions.md",
    _REPO_ROOT / ".claude" / "instructions.md",
)

_FORBIDDEN_TOKENS = ("query_graph_neighborhood", "Cypher-style")
_SNAKE_TOKEN = re.compile(r"`([a-z0-9]+(?:_[a-z0-9]+)+)`")


def _scan_files() -> list[Path]:
    """Return the tracked guidance/source files scanned for forbidden tokens."""
    files: list[Path] = []
    for root, patterns in (
        (_REPO_ROOT / "templates", ("*",)),
        (_REPO_ROOT / ".github", ("*",)),
        (_REPO_ROOT / ".claude", ("*",)),
        (_REPO_ROOT / "src", ("*",)),
    ):
        for pattern in patterns:
            for path in root.rglob(pattern):
                if not path.is_file() or "__pycache__" in path.parts:
                    continue
                if "archive" in path.parts or path.suffix in {".pyc", ".png"}:
                    continue
                files.append(path)
    files.extend(sorted((_REPO_ROOT / "docs").glob("*.md")))
    return files


class EngramToolSurfaceGuardTests(unittest.TestCase):
    def test_registered_set_is_pinned(self) -> None:
        self.assertEqual(len(REGISTERED_TOOLS), 21)
        self.assertTrue(REGISTERED_TOOLS.isdisjoint(FEATURE_GATED_TOOLS))

    def test_backticked_engram_tools_are_registered(self) -> None:
        allowed = REGISTERED_TOOLS | FEATURE_GATED_TOOLS | QUERY_GRAPH_VOCABULARY
        for path in _GUIDANCE_FILES:
            with self.subTest(path=str(path.relative_to(_REPO_ROOT))):
                text = path.read_text(encoding="utf-8")
                unknown = sorted(set(_SNAKE_TOKEN.findall(text)) - allowed)
                self.assertEqual(unknown, [], f"unregistered engram tool names: {unknown}")

    def test_guidance_names_query_graph_operations(self) -> None:
        for path in _GUIDANCE_FILES:
            with self.subTest(path=str(path.relative_to(_REPO_ROOT))):
                text = path.read_text(encoding="utf-8")
                self.assertIn("`query_graph`", text)
                for operation in ("neighborhood", "find_path", "transitive_closure"):
                    self.assertIn(operation, text)

    def test_forbidden_tokens_absent(self) -> None:
        for path in _scan_files():
            if path.resolve() == Path(__file__).resolve():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for token in _FORBIDDEN_TOKENS:
                with self.subTest(path=str(path.relative_to(_REPO_ROOT)), token=token):
                    self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
