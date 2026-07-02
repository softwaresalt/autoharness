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


def _iter_module_files() -> list[Path]:
    return sorted(_TELEMETRY_DIR.glob("*.py"))


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


if __name__ == "__main__":
    unittest.main()
