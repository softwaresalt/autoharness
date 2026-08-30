"""Security tests for option-safe git-ref resolution (149.013-T)."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from autoharness.gates.discovery import resolve_commit_ref

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMP_ROOT = _REPO_ROOT / ".test-output"


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _make_repo() -> tuple[Path, str, str, tempfile.TemporaryDirectory[str]]:
    _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    tempdir = tempfile.TemporaryDirectory(dir=_TEMP_ROOT)
    repo = Path(tempdir.name)
    _git(repo, "init", "--initial-branch", "main")
    _git(repo, "config", "user.name", "Autoharness Tests")
    _git(repo, "config", "user.email", "autoharness-tests@example.com")
    (repo / "tracked.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "first")
    first_sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "tag", "v1")
    (repo / "tracked.txt").write_text("two\n", encoding="utf-8")
    _git(repo, "commit", "-am", "second")
    second_sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "branch", "saved", first_sha)
    return repo, first_sha, second_sha, tempdir


class ResolveCommitRefTests(unittest.TestCase):
    def test_option_like_refs_are_rejected_without_creating_files(self) -> None:
        repo, _, _, tempdir = _make_repo()
        self.addCleanup(tempdir.cleanup)
        target = repo / "would-not-exist.txt"
        for ref in (f"--output={target}", "--upload-pack=malicious", "-not-a-ref"):
            with self.subTest(ref=ref):
                self.assertIsNone(resolve_commit_ref(ref, cwd=repo))
        self.assertFalse(target.exists())

    def test_invalid_refs_are_rejected(self) -> None:
        repo, _, _, tempdir = _make_repo()
        self.addCleanup(tempdir.cleanup)
        self.assertIsNone(resolve_commit_ref("missing-branch", cwd=repo))
        self.assertIsNone(resolve_commit_ref("f" * 40, cwd=repo))

    def test_valid_symbolic_refs_resolve_to_full_hex_sha(self) -> None:
        repo, first_sha, second_sha, tempdir = _make_repo()
        self.addCleanup(tempdir.cleanup)
        self.assertEqual(resolve_commit_ref("HEAD", cwd=repo), second_sha)
        self.assertEqual(resolve_commit_ref("HEAD~1", cwd=repo), first_sha)
        self.assertEqual(resolve_commit_ref("saved", cwd=repo), first_sha)
        self.assertEqual(resolve_commit_ref("v1", cwd=repo), first_sha)

    def test_full_sha_passes_through_unchanged(self) -> None:
        repo, _, second_sha, tempdir = _make_repo()
        self.addCleanup(tempdir.cleanup)
        self.assertEqual(resolve_commit_ref(second_sha, cwd=repo), second_sha)


if __name__ == "__main__":
    unittest.main()
