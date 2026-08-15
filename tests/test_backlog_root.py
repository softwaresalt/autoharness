"""Tests for shared backlog storage-root resolution."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.backlog_root import (
    AmbiguousBacklogRootError,
    BacklogUnavailableError,
    resolve_backlog_root,
)


class ResolveBacklogRootTests(unittest.TestCase):
    def _make_root(self, workspace: Path, name: str) -> Path:
        root = workspace / name
        root.mkdir(parents=True)
        return root

    def test_override_happy_path_takes_precedence(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            override = self._make_root(workspace, "override-root")
            self._make_root(workspace, ".backlog")
            self._make_root(workspace, ".backlogit")

            resolved = resolve_backlog_root(
                workspace,
                env={"BACKLOGIT_WORKSPACE_DIR": "override-root"},
            )

        self.assertEqual(resolved, override)

    def test_missing_override_fails_closed_without_fallthrough(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            self._make_root(workspace, ".backlog")

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(
                    workspace,
                    env={"BACKLOGIT_WORKSPACE_DIR": "missing-root"},
                )

        self.assertEqual(exc.exception.path, str(workspace / "missing-root"))
        self.assertEqual(exc.exception.reason, "configured backlog directory is unavailable")

    def test_backlog_only_workspace_uses_new_default(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            backlog_root = self._make_root(workspace, ".backlog")

            resolved = resolve_backlog_root(workspace, env={})

        self.assertEqual(resolved, backlog_root)

    def test_backlogit_only_workspace_uses_legacy_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            legacy_root = self._make_root(workspace, ".backlogit")

            resolved = resolve_backlog_root(workspace, env={})

        self.assertEqual(resolved, legacy_root)

    def test_both_roots_present_is_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            self._make_root(workspace, ".backlog")
            self._make_root(workspace, ".backlogit")

            with self.assertRaises(AmbiguousBacklogRootError) as exc:
                resolve_backlog_root(workspace, env={})

        self.assertEqual(exc.exception.candidates, (str(workspace / ".backlog"), str(workspace / ".backlogit")))

    def test_neither_root_present_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(workspace, env={})

        self.assertEqual(exc.exception.path, str(workspace))
        self.assertEqual(exc.exception.reason, "backlog directory is unavailable")
