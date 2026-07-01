"""Tests for the git-diff discovery utility (T3)."""

from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from autoharness.gates.discovery import discover_modified_files, parse_diff_output


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
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertLogs("autoharness.gates.discovery", level=logging.WARNING):
                result = discover_modified_files("main", "HEAD", cwd=Path(tmp))
            self.assertEqual(result, [])

    def test_degrades_gracefully_when_git_missing(self) -> None:
        def missing_git(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            raise FileNotFoundError("git")

        with self.assertLogs("autoharness.gates.discovery", level=logging.WARNING):
            result = discover_modified_files("main", "HEAD", runner=missing_git)
        self.assertEqual(result, [])

    def test_uses_injected_runner_and_normalizes(self) -> None:
        def fake(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            self.assertEqual(argv, ["git", "diff", "--name-only", "main...HEAD"])
            return 0, "src\\a.py\ndocs/b.md\n", ""

        self.assertEqual(
            discover_modified_files("main", "HEAD", runner=fake),
            ["src/a.py", "docs/b.md"],
        )


if __name__ == "__main__":
    unittest.main()
