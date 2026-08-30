"""Tests for the git-diff discovery utility (T3)."""

from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from autoharness.gates.discovery import InvalidGitRefError, discover_modified_files, parse_diff_output

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMP_ROOT = _REPO_ROOT / ".test-output"
_BASE_SHA = "a" * 40
_HEAD_SHA = "b" * 40


class DiscoveryTests(unittest.TestCase):
    def test_parses_diff_output_into_path_list(self) -> None:
        out = "docs/a.md\nsrc/autoharness/gates/runner.py\n"
        self.assertEqual(
            parse_diff_output(out),
            ["docs/a.md", "src/autoharness/gates/runner.py"],
        )

    def test_empty_diff_returns_empty_list(self) -> None:
        self.assertEqual(parse_diff_output(""), [])
        self.assertEqual(parse_diff_output("\n\n  \n"), [])

    def test_normalizes_backslash_separators_and_dedupes(self) -> None:
        out = "docs\\nested\\a.md\ndocs/nested/a.md\nsrc\\x.py\n"
        self.assertEqual(parse_diff_output(out), ["docs/nested/a.md", "src/x.py"])

    def test_degrades_gracefully_when_not_a_repo(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            with self.assertLogs("autoharness.gates.discovery", level=logging.WARNING):
                result = discover_modified_files(_BASE_SHA, _HEAD_SHA, cwd=Path(tmp))
            self.assertEqual(result, [])

    def test_degrades_gracefully_when_git_missing(self) -> None:
        def missing_git(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            raise FileNotFoundError("git")

        with self.assertLogs("autoharness.gates.discovery", level=logging.WARNING):
            result = discover_modified_files(_BASE_SHA, _HEAD_SHA, runner=missing_git)
        self.assertEqual(result, [])

    def test_uses_injected_runner_and_normalizes(self) -> None:
        def fake(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            self.assertEqual(
                argv,
                ["git", "diff", "--name-only", "--end-of-options", f"{_BASE_SHA}...{_HEAD_SHA}", "--"],
            )
            return 0, "src\\a.py\ndocs/b.md\n", ""

        self.assertEqual(
            discover_modified_files(_BASE_SHA, _HEAD_SHA, runner=fake),
            ["src/a.py", "docs/b.md"],
        )

    def test_rejects_symbolic_ref_directly(self) -> None:
        called = False

        def fake(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            nonlocal called
            called = True
            return 0, "", ""

        with self.assertRaises(InvalidGitRefError):
            discover_modified_files("main", _HEAD_SHA, runner=fake)
        self.assertFalse(called)


if __name__ == "__main__":
    unittest.main()
