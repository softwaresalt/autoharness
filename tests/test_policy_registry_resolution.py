"""Characterization tests for ``_resolve_policy_registry`` (156-S/148.002-T, U2).

Written BEFORE the docstring/comment correction in ``verify_workspace.py`` so the
installed-first / template-fallback precedence is demonstrably preserved across
the edit (INV-2). This module intentionally asserts behavior only -- it makes no
claim about the docstring text, which is corrected by this same unit.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.verify_workspace import _resolve_policy_registry


class PolicyRegistryResolutionPrecedenceTests(unittest.TestCase):
    """INV-2: the template-fallback branch is preserved; both precedence
    scenarios (installed-first, template-fallback) remain green."""

    def test_installed_registry_present_wins_over_template(self) -> None:
        """Scenario (a): installed present -> installed wins."""
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as home_dir:
            workspace_path = Path(workspace_dir)
            autoharness_home = Path(home_dir)

            installed = workspace_path / ".github" / "policies" / "workflow-policies.md"
            installed.parent.mkdir(parents=True, exist_ok=True)
            installed.write_text("# installed registry\n", encoding="utf-8", newline="\n")

            template = autoharness_home / "templates" / "policies" / "workflow-policies.md.tmpl"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("# template registry\n", encoding="utf-8", newline="\n")

            resolved = _resolve_policy_registry(workspace_path, autoharness_home)

            self.assertEqual(resolved, installed)

    def test_installed_absent_autoharness_home_present_falls_back_to_template(
        self,
    ) -> None:
        """Scenario (b): installed absent + autoharness_home present -> template wins."""
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as home_dir:
            workspace_path = Path(workspace_dir)
            autoharness_home = Path(home_dir)

            # No installed registry is created under workspace_path.
            template = autoharness_home / "templates" / "policies" / "workflow-policies.md.tmpl"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("# template registry\n", encoding="utf-8", newline="\n")

            resolved = _resolve_policy_registry(workspace_path, autoharness_home)

            self.assertEqual(resolved, template)

    def test_neither_installed_nor_template_resolves_to_none(self) -> None:
        """Existence-gated resolution: neither present -> None, not a raised error."""
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as home_dir:
            workspace_path = Path(workspace_dir)
            autoharness_home = Path(home_dir)

            resolved = _resolve_policy_registry(workspace_path, autoharness_home)

            self.assertIsNone(resolved)


if __name__ == "__main__":
    unittest.main()
