"""Module-boundary and scope tests for the telemetry package.

* P2-2: the telemetry package must NOT import ``gates/``, ``verify_workspace``,
  ``schema_contracts``, or install/tune modules, so telemetry evolves
  independently of gating.
* P2-5: the JSONL sink (051.006) is emit-only — no CozoDB / agent-engram
  ingestion code may be added on the autoharness side.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

_TELEMETRY_DIR = Path(__file__).resolve().parents[1] / "src" / "autoharness" / "telemetry"

_FORBIDDEN_IMPORT_FRAGMENTS = (
    "engram",
    "agent_engram",
    "autoharness.gates",
    "autoharness.verify_workspace",
    "autoharness.schema_contracts",
    "autoharness.install",
    "autoharness.tune",
    # eval depends on telemetry, never the reverse (one-directional coupling).
    "autoharness.eval",
)

# Emit-only boundary: no external ingestion vocabulary belongs in this package.
_FORBIDDEN_SCOPE_TOKENS = ("cozo", "cozodb")
_FORBIDDEN_RUNTIME_TOKENS = ("agent-engram", "agent_engram", "engram")


def _iter_module_files() -> list[Path]:
    return sorted(_TELEMETRY_DIR.glob("*.py"))


def _docstring_constant_ids(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            ids.add(id(first.value))
    return ids


def _runtime_boundary_tokens(tree: ast.AST) -> set[str]:
    docstring_ids = _docstring_constant_ids(tree)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in docstring_ids:
                continue
            value = node.value.lower()
        elif isinstance(node, ast.Name):
            value = node.id.lower()
        elif isinstance(node, ast.Attribute):
            value = node.attr.lower()
        else:
            continue
        for token in _FORBIDDEN_RUNTIME_TOKENS:
            if token in value:
                found.add(token)
    return found


class TelemetryImportBoundaryTests(unittest.TestCase):
    def test_no_import_of_gates_or_install_tune_modules(self) -> None:
        for module in _iter_module_files():
            tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
            imported: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.append(node.module)
            for name in imported:
                for forbidden in _FORBIDDEN_IMPORT_FRAGMENTS:
                    self.assertFalse(
                        name == forbidden or name.startswith(forbidden + "."),
                        f"{module.name} imports forbidden module {name!r} (boundary P2-2).",
                    )

    def test_no_cozodb_ingestion_code_present(self) -> None:
        for module in _iter_module_files():
            text = module.read_text(encoding="utf-8").lower()
            for token in _FORBIDDEN_SCOPE_TOKENS:
                self.assertNotIn(
                    token,
                    text,
                    f"{module.name} references {token!r}; JSONL sink is emit-only (P2-5).",
                )

    def test_no_engram_runtime_calls_or_ingestion_code_present(self) -> None:
        for module in _iter_module_files():
            tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
            tokens = _runtime_boundary_tokens(tree)
            self.assertEqual(
                tokens,
                set(),
                f"{module.name} has runtime agent-engram/engram tokens {sorted(tokens)}; "
                "telemetry may document downstream ingestion but must not call/import it.",
            )


class TelemetryBoundaryRuleSelfTests(unittest.TestCase):
    def test_forbidden_import_fragments_cover_engram_boundaries(self) -> None:
        for forbidden in (
            "autoharness.eval",
            "autoharness.gates",
            "autoharness.install",
            "autoharness.tune",
            "autoharness.verify_workspace",
            "autoharness.schema_contracts",
            "engram",
            "agent_engram",
        ):
            self.assertIn(forbidden, _FORBIDDEN_IMPORT_FRAGMENTS)

    def test_runtime_token_detector_allows_docstrings_but_rejects_engram_code(self) -> None:
        source = '''
"""agent-engram is a downstream ingestion boundary, not a runtime dependency."""
import importlib
client = importlib.import_module("agent-engram")
result = engram.map_code("ExecutionEpoch")
'''
        tokens = _runtime_boundary_tokens(ast.parse(source))

        self.assertIn("agent-engram", tokens)
        self.assertIn("engram", tokens)


if __name__ == "__main__":
    unittest.main()
