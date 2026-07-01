"""Tests for the doublestar glob matcher (T4)."""

from __future__ import annotations

import unittest

from autoharness.gates.match import filter_matching, path_matches


class GlobMatchTests(unittest.TestCase):
    def test_doublestar_matches_nested_docs(self) -> None:
        self.assertTrue(path_matches("docs/**/*.md", "docs/nested/deep/a.md", case_sensitive=True))
        # zero intermediate segments also match
        self.assertTrue(path_matches("docs/**/*.md", "docs/a.md", case_sensitive=True))

    def test_windows_backslash_path_normalized_before_match(self) -> None:
        self.assertTrue(path_matches("docs/**/*.md", "docs\\nested\\a.md", case_sensitive=True))

    def test_case_sensitivity_rule_applied_per_host(self) -> None:
        self.assertFalse(path_matches("docs/**/*.md", "Docs/A.MD", case_sensitive=True))
        self.assertTrue(path_matches("docs/**/*.md", "Docs/A.MD", case_sensitive=False))

    def test_non_matching_files_excluded(self) -> None:
        self.assertFalse(path_matches("src/**/*.py", "docs/a.md", case_sensitive=True))
        # single star does not cross a slash
        self.assertTrue(path_matches("docs/*.md", "docs/a.md", case_sensitive=True))
        self.assertFalse(path_matches("docs/*.md", "docs/x/a.md", case_sensitive=True))

    def test_filter_matching_preserves_order(self) -> None:
        paths = ["docs/a.md", "src/x.py", "docs/sub/b.md", "README.txt"]
        self.assertEqual(
            filter_matching("docs/**/*.md", paths, case_sensitive=True),
            ["docs/a.md", "docs/sub/b.md"],
        )


if __name__ == "__main__":
    unittest.main()
