"""Tests for shared backlog storage-root resolution."""

from __future__ import annotations

import subprocess
import sys
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
        # A valid literal override (one of the two supported candidate
        # names) takes precedence over the default .backlog-first auto-detect
        # order, even when both candidate roots are also present.
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._make_root(workspace, ".backlog")
            legacy = self._make_root(workspace, ".backlogit")

            resolved = resolve_backlog_root(
                workspace,
                env={"BACKLOGIT_WORKSPACE_DIR": ".backlogit"},
            )

        self.assertEqual(resolved, legacy)

    def test_missing_override_fails_closed_without_fallthrough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._make_root(workspace, ".backlog")

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(
                    workspace,
                    env={"BACKLOGIT_WORKSPACE_DIR": ".backlogit"},
                )

        self.assertEqual(exc.exception.path, str(workspace / ".backlogit"))
        self.assertEqual(exc.exception.reason, "configured backlog directory is unavailable")

    def test_backlog_only_workspace_uses_new_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            backlog_root = self._make_root(workspace, ".backlog")

            resolved = resolve_backlog_root(workspace, env={})

        self.assertEqual(resolved, backlog_root)

    def test_backlogit_only_workspace_uses_legacy_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            legacy_root = self._make_root(workspace, ".backlogit")

            resolved = resolve_backlog_root(workspace, env={})

        self.assertEqual(resolved, legacy_root)

    def test_both_roots_present_is_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._make_root(workspace, ".backlog")
            self._make_root(workspace, ".backlogit")

            with self.assertRaises(AmbiguousBacklogRootError) as exc:
                resolve_backlog_root(workspace, env={})

        self.assertEqual(exc.exception.candidates, (str(workspace / ".backlog"), str(workspace / ".backlogit")))

    def test_neither_root_present_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(workspace, env={})

        self.assertEqual(exc.exception.path, str(workspace))
        self.assertEqual(exc.exception.reason, "backlog directory is unavailable")


class OverrideValidationRejectionTests(unittest.TestCase):
    """PR #344 Copilot review, thread PRRT_kwDORzpWpM6ZihN2: the override is
    not an arbitrary filesystem path -- it must be one of the two literal
    candidate names, mirroring backlogit 1.9.0's
    ``validateWorkspaceDirOverride``. These cases previously succeeded
    against an unrelated directory (for example ``override-root`` or
    ``custom-root``); they must now fail closed."""

    def _make_root(self, workspace: Path, name: str) -> Path:
        root = workspace / name
        root.mkdir(parents=True)
        return root

    def test_arbitrary_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._make_root(workspace, "custom-root")

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(workspace, env={"BACKLOGIT_WORKSPACE_DIR": "custom-root"})

        self.assertIn("must be one of", exc.exception.reason)

    def test_path_separator_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._make_root(workspace, ".backlog")

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(workspace, env={"BACKLOGIT_WORKSPACE_DIR": "sub/.backlog"})

        self.assertIn("must be one of", exc.exception.reason)

    def test_absolute_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            backlog_root = self._make_root(workspace, ".backlog")

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(
                    workspace, env={"BACKLOGIT_WORKSPACE_DIR": str(backlog_root)}
                )

        self.assertIn("must be one of", exc.exception.reason)

    def test_dot_and_dotdot_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._make_root(workspace, ".backlog")

            for value in (".", ".."):
                with self.assertRaises(BacklogUnavailableError) as exc:
                    resolve_backlog_root(workspace, env={"BACKLOGIT_WORKSPACE_DIR": value})
                self.assertIn("must be one of", exc.exception.reason)

    def test_case_alias_is_rejected_with_distinct_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._make_root(workspace, ".backlog")

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(workspace, env={"BACKLOGIT_WORKSPACE_DIR": ".BACKLOG"})

        self.assertIn("exact supported case", exc.exception.reason)

    @unittest.skipUnless(sys.platform == "win32", "drive-letter override paths are meaningful on Windows only")
    def test_drive_prefix_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._make_root(workspace, ".backlog")

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(workspace, env={"BACKLOGIT_WORKSPACE_DIR": "C:.backlog"})

        self.assertIn("must be one of", exc.exception.reason)


class CandidateSymlinkRejectionTests(unittest.TestCase):
    """PR #344 Copilot review, thread PRRT_kwDORzpWpM6ZihN5: ``Path.is_dir()``
    follows symlinks, so an unrelated or escaping directory reached through a
    symlinked/reparse-point ``.backlog``/``.backlogit`` must not be silently
    accepted as the resolved root."""

    def _skip_if_symlink_unsupported(self, workspace: Path, target: Path, link: Path) -> None:
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink creation unsupported in this environment: {exc}")

    def test_symlinked_candidate_is_rejected_on_auto_detect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            real_target = workspace / "elsewhere"
            real_target.mkdir()
            link = workspace / ".backlog"
            self._skip_if_symlink_unsupported(workspace, real_target, link)

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(workspace, env={})

        self.assertIn("symlink", exc.exception.reason)

    def test_symlinked_override_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            real_target = workspace / "elsewhere"
            real_target.mkdir()
            link = workspace / ".backlogit"
            self._skip_if_symlink_unsupported(workspace, real_target, link)

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(workspace, env={"BACKLOGIT_WORKSPACE_DIR": ".backlogit"})

        self.assertIn("symlink", exc.exception.reason)


class CandidateJunctionRejectionTests(unittest.TestCase):
    """PR #344 Copilot review round 3, thread PRRT_kwDORzpWpM6ZipoH: on
    Windows, directory junctions are reparse points but are NOT symbolic
    links, so ``Path.is_symlink()`` alone does not catch them and
    ``Path.is_dir()`` still follows them -- a junction could otherwise
    silently redirect the resolved backlog root outside the workspace."""

    def _make_junction(self, link: Path, target: Path) -> None:
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            self.skipTest(
                f"directory junction creation unsupported in this environment: {result.stderr.strip()}"
            )

    @unittest.skipUnless(sys.platform == "win32", "directory junctions are a Windows-only filesystem feature")
    def test_junction_candidate_is_rejected_on_auto_detect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            real_target = workspace / "elsewhere"
            real_target.mkdir()
            link = workspace / ".backlog"
            self._make_junction(link, real_target)

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(workspace, env={})

        self.assertIn("symlink", exc.exception.reason)

    @unittest.skipUnless(sys.platform == "win32", "directory junctions are a Windows-only filesystem feature")
    def test_junction_override_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            real_target = workspace / "elsewhere"
            real_target.mkdir()
            link = workspace / ".backlogit"
            self._make_junction(link, real_target)

            with self.assertRaises(BacklogUnavailableError) as exc:
                resolve_backlog_root(workspace, env={"BACKLOGIT_WORKSPACE_DIR": ".backlogit"})

        self.assertIn("symlink", exc.exception.reason)
