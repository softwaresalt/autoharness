"""Module-boundary and hermeticity tests for the eval package.

* The eval package depends on ``telemetry`` in one direction only and stays
  decoupled from gating/install/tune modules (mirrors the telemetry boundary).
* **Hermeticity (no live LLM / network):** the eval runner and reviewer must be
  fully deterministic. No network or model-client library may be imported —
  this is the mechanical guarantee behind the plan's "no live LLM / network
  calls in the eval runner or reviewer" constraint.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parents[1] / "src" / "autoharness" / "eval"

# eval may depend on telemetry (one direction). It must NOT couple to gating,
# workspace verification, schema contracts, or install/tune internals.
_FORBIDDEN_IMPORT_FRAGMENTS = (
    "autoharness.gates",
    "autoharness.verify_workspace",
    "autoharness.schema_contracts",
    "autoharness.install",
    "autoharness.tune",
)

# No network / live-model client may be imported: the runner and reviewer are
# deterministic and hermetic.
_FORBIDDEN_NETWORK_IMPORTS = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib.request",
    "urllib3",
    "socket",
    "http.client",
    "openai",
    "anthropic",
    "google.generativeai",
)


def _iter_module_files() -> list[Path]:
    return sorted(_EVAL_DIR.glob("*.py"))


def _imported_names(module: Path) -> list[str]:
    tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return imported


def _matches(name: str, fragment: str) -> bool:
    return name == fragment or name.startswith(fragment + ".")


class EvalImportBoundaryTests(unittest.TestCase):
    def test_no_import_of_gates_or_install_tune_modules(self) -> None:
        for module in _iter_module_files():
            for name in _imported_names(module):
                for forbidden in _FORBIDDEN_IMPORT_FRAGMENTS:
                    self.assertFalse(
                        _matches(name, forbidden),
                        f"{module.name} imports forbidden module {name!r} (eval decoupling).",
                    )

    def test_no_network_or_model_client_imports(self) -> None:
        for module in _iter_module_files():
            for name in _imported_names(module):
                for forbidden in _FORBIDDEN_NETWORK_IMPORTS:
                    self.assertFalse(
                        _matches(name, forbidden),
                        f"{module.name} imports {name!r}; eval must be hermetic "
                        f"(no live LLM / network calls).",
                    )


if __name__ == "__main__":
    unittest.main()
