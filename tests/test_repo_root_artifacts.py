"""Regression test: exactly the allowlisted depth-0 tracked JSON files exist at the
repository root.

Prevents recurrence of stale/accidental scratch JSON dumps at the repository root
(see 133-F / 133.001-T / 142-S). This test intentionally does NOT rely on a
.gitignore rule -- an ignore rule cannot untrack already-tracked files and fails
silently, whereas this test fails loudly and names the offending path(s).
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

from _git_env import consistent_git_env

ALLOWED_ROOT_JSON = frozenset({".mcp.json", "plugin.json"})


class RepoRootTrackedJsonAllowlistTest(unittest.TestCase):
    """Depth-0 tracked *.json files must equal exactly the allowlist."""

    def test_root_tracked_json_matches_allowlist(self) -> None:
        git = shutil.which("git")
        if git is None:
            self.skipTest("git executable not available")

        repo_root = Path(__file__).resolve().parent.parent

        if not (repo_root / ".git").exists():
            self.skipTest("not a git checkout")

        try:
            result = subprocess.run(
                [git, "ls-files", "-z", "--", "*.json"],
                cwd=repo_root,
                capture_output=True,
                check=True,
                env=consistent_git_env(),
            )
        except subprocess.CalledProcessError as exc:
            stderr_text = (exc.stderr or b"").decode("utf-8", errors="replace")
            self.fail(
                f"git ls-files failed (exit {exc.returncode}) while checking the "
                f"root-level tracked JSON allowlist; captured stderr: {stderr_text}"
            )
        raw_paths = result.stdout.decode("utf-8", errors="replace").split("\0")
        depth0_json = {p for p in raw_paths if p and "/" not in p}

        unexpected = depth0_json - ALLOWED_ROOT_JSON
        missing = ALLOWED_ROOT_JSON - depth0_json

        self.assertEqual(
            depth0_json,
            ALLOWED_ROOT_JSON,
            (
                "Root-level tracked JSON allowlist violated. "
                f"Unexpected: {sorted(unexpected)!r}. Missing: {sorted(missing)!r}. "
                f"Full observed set: {sorted(depth0_json)!r}."
            ),
        )


if __name__ == "__main__":
    unittest.main()
