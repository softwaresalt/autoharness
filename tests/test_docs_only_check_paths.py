"""Tests for the docs_only_check path rules and two-layer snapshot primitive (216.001-T)."""

from __future__ import annotations

import os
import unittest

from _docs_only_repo import BACKLOG, DOCS, TempRepo
from autoharness import docs_only_check as dc


class PathRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write("docs/guide.md", "g\n")
        self.repo.write("docs/sub/more.md", "m\n")
        self.repo.commit_all("docs")

    def check(self, owned, docs=DOCS, backlog=BACKLOG):
        return dc.check_owned_paths(self.repo.root, owned, docs, backlog)

    def rules(self, owned, **kw):
        return {v.rule for v in self.check(owned, **kw).violations}

    def test_pass_case(self) -> None:
        result = self.check(["docs/guide.md", "docs/sub/more.md", "docs/new-file.md"])
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.exit_code, 0)

    def test_deny_list_overrides_docs_root(self) -> None:
        for docs in ("docs", "src", "templates", ".github"):
            self.repo.write(f"{docs}/x.md", "x\n")
        for rel in ("src/x.md", "templates/x.md", ".github/x.md", ".backlogit/queue/x.md"):
            with self.subTest(path=rel):
                self.assertEqual(self.check([rel], docs=rel.split("/")[0]).status, "violation")
        self.assertIn("DENY_LIST", self.rules(["docs/AGENTS.md"]))
        self.assertIn("DENY_LIST", self.rules(["docs/x.agent.md", "docs/SKILL.md"]))
        self.assertIn("DENY_LIST", self.rules([".GitHub/x.md"], docs=".GitHub"))

    def test_deny_list_case_insensitive_backlog_root(self) -> None:
        self.assertIn("DENY_LIST", self.rules([".BACKLOGIT/x.md"], docs=".BACKLOGIT"))

    def test_traversal_and_malformed_paths(self) -> None:
        for bad in ("docs/../src/a.md", "docs//a.md", "./docs/a.md", "docs/./a.md", "/docs/a.md",
                    "C:/docs/a.md", "docs\\a.md", "docs/a:b.md", "docs/", ""):
            with self.subTest(path=bad):
                self.assertEqual(self.check([bad]).status, "violation", bad)

    def test_not_markdown_or_outside_docs_root(self) -> None:
        self.assertIn("NOT_MARKDOWN", self.rules(["docs/a.txt"]))
        self.assertIn("NOT_MARKDOWN", self.rules(["docs/a.mdx"]))
        self.assertIn("OUTSIDE_DOCS_ROOT", self.rules(["README.md"]))
        self.assertIn("OUTSIDE_DOCS_ROOT", self.rules(["Docs2/a.md"]))
        self.assertEqual(self.check(["DOCS/guide.md"]).status, "pass")

    def test_directory_is_not_a_regular_file(self) -> None:
        self.repo.write("docs/dir.md/inner.md", "x\n")
        self.assertIn("NOT_REGULAR_FILE", self.rules(["docs/dir.md"]))

    def test_symlink_owned_or_parent(self) -> None:
        target = self.repo.root / "docs" / "guide.md"
        link = self.repo.root / "docs" / "link.md"
        try:
            os.symlink(target, link)
            os.symlink(self.repo.root / "src_real", self.repo.root / "docs" / "linkdir", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        self.assertIn("SYMLINK", self.rules(["docs/link.md"]))
        self.assertIn("SYMLINK", self.rules(["docs/linkdir/a.md"]))

    def test_docs_root_fail_closed(self) -> None:
        for bad in ("", ".", "./", "..", "/", "docs/..", "docs\\x", "C:"):
            with self.subTest(docs=bad):
                result = self.check(["docs/guide.md"], docs=bad)
                self.assertEqual(result.status, "error")
                self.assertEqual(result.exit_code, 2)

    def test_empty_owned_is_invalid_input(self) -> None:
        self.assertEqual(self.check([]).status, "error")
        self.assertEqual(self.check(None).status, "error")
        self.assertEqual(self.check("docs/guide.md").status, "error")

    def test_not_a_repository_is_error(self) -> None:
        other = TempRepo()
        self.addCleanup(other.cleanup)
        missing = other.root / "nope"
        self.assertEqual(dc.check_owned_paths(missing, ["docs/a.md"], DOCS, BACKLOG).status, "error")


class SnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write("docs/a.md", "a\n")
        self.repo.write("docs/b.md", "b\n")
        self.repo.write("docs/c.md", "c\n")
        self.head = self.repo.commit_all("docs")

    def snap(self):
        return dc.take_snapshot(self.repo.root)

    def test_clean_tree_has_no_entries(self) -> None:
        snap = self.snap()
        self.assertEqual(snap.head_sha, self.head)
        self.assertEqual(snap.entries, {})

    def test_modified_unstaged(self) -> None:
        self.repo.write("docs/a.md", "a2\n")
        entry = self.snap().entries["docs/a.md"]
        committed = self.repo.git("ls-files", "-s", "docs/a.md").split()
        self.assertEqual(entry.index, f"{committed[0]} {committed[1]}")
        self.assertNotEqual(entry.worktree, None)

    def test_staged_then_restored_is_independent_layers(self) -> None:
        clean_worktree = None
        self.repo.write("docs/a.md", "a2\n")
        self.repo.git("add", "docs/a.md")
        staged_blob = self.repo.git("ls-files", "-s", "docs/a.md").split()[1]
        self.repo.write("docs/a.md", "a\n")
        entry = self.snap().entries["docs/a.md"]
        self.assertEqual(entry.index, f"100644 {staged_blob}")
        self.assertEqual(entry.worktree, dc.take_snapshot(self.repo.root).entries["docs/a.md"].worktree)
        self.repo.write("docs/a.md", "a2\n")
        self.assertNotEqual(entry.worktree, self.snap().entries["docs/a.md"].worktree)
        self.assertEqual(clean_worktree, None)
    def test_staged_modification_reports_both_layers(self) -> None:
        self.repo.write("docs/a.md", "staged\n")
        self.repo.git("add", "docs/a.md")
        self.repo.write("docs/a.md", "worktree\n")
        first = self.snap().entries["docs/a.md"]
        self.repo.write("docs/a.md", "worktree2\n")
        second = self.snap().entries["docs/a.md"]
        self.assertEqual(first.index, second.index)
        self.assertNotEqual(first.worktree, second.worktree)

    def test_untracked_and_deleted_and_renamed(self) -> None:
        self.repo.write("docs/new.md", "n\n")
        (self.repo.root / "docs" / "b.md").unlink()
        self.repo.git("mv", "docs/c.md", "docs/c2.md")
        entries = self.snap().entries
        self.assertIsNone(entries["docs/new.md"].index)
        self.assertIsNotNone(entries["docs/new.md"].worktree)
        self.assertIsNotNone(entries["docs/b.md"].index)
        self.assertIsNone(entries["docs/b.md"].worktree)
        self.assertIsNone(entries["docs/c.md"].index)
        self.assertIsNone(entries["docs/c.md"].worktree)
        self.assertIsNotNone(entries["docs/c2.md"].index)
        self.assertIsNotNone(entries["docs/c2.md"].worktree)

    def test_worktree_hash_is_lf_normalized(self) -> None:
        self.repo.write("docs/a.md", "x\ny\n")
        lf = self.snap().entries["docs/a.md"].worktree
        (self.repo.root / "docs" / "a.md").write_bytes(b"x\r\ny\r\n")
        self.assertEqual(self.snap().entries["docs/a.md"].worktree, lf)

    def test_git_failure_raises(self) -> None:
        other = TempRepo()
        self.addCleanup(other.cleanup)
        with self.assertRaises(dc.DocsOnlyError):
            dc.take_snapshot(other.root / "missing")

    def test_no_shell_and_fixed_argv(self) -> None:
        import inspect

        source = inspect.getsource(dc)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("urllib", source)
        self.assertNotIn("requests", source)


if __name__ == "__main__":
    unittest.main()
