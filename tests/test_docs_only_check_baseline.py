"""Tests for the docs_only_check baseline phase (216.008-T)."""

from __future__ import annotations

import copy
import unittest

from _docs_only_repo import BACKLOG, DOCS, ShipmentRepo
from autoharness import docs_only_check as dc


class BaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = ShipmentRepo()
        self.addCleanup(self.repo.cleanup)
        self.t1, self.t2 = self.repo.TASKS

    def baseline(self, owned=("docs/a.md",)):
        return dc.baseline_phase(self.repo.root, list(owned), DOCS, BACKLOG)

    def test_pre_state_is_recorded_not_judged(self) -> None:
        self.repo.claim_all()
        self.repo.add_label(self.t1)
        self.repo.write("docs/a.md", "a edited by task 1\n")
        self.repo.close_out(self.t1, "docs: task 1", ("docs/a.md",))
        self.repo.add_label(self.t2)
        self.repo.write("docs/memory/session.md", "dirty memory\n")
        result = self.baseline(owned=("docs/b.md",))
        self.assertEqual(result.status, "pass", result.violations)
        record = result.record
        self.assertEqual(record["head_sha"], self.repo.head())
        by_path = {e["path"]: e for e in record["entries"]}
        self.assertIn("docs/memory/session.md", by_path)
        self.assertNotIn("docs/a.md", by_path)
        task2 = by_path[self.repo.path_of(self.t2)]
        self.assertIsNotNone(task2["index"])
        self.assertIsNotNone(task2["worktree"])
        self.assertEqual(len(task2["body_sha256"]), 64)
        self.assertEqual(len(task2["protected_frontmatter_sha256"]), 64)
        self.assertIn(self.repo.path_of(self.repo.SHIPMENT), by_path)
        self.assertNotIn("body_sha256", by_path["docs/memory/session.md"])
        self.assertEqual(record["self_digest"], dc.compute_self_digest(record))

    def test_allowlisted_keys_do_not_change_protected_hash(self) -> None:
        self.repo.claim_all()
        before = {e["path"]: e for e in self.baseline().record["entries"]}[self.repo.path_of(self.t1)]
        self.repo.save(self.t1, labels=("harness-verification-gated",), updated="2026-04-01T00:00:00Z", status="done")
        after = {e["path"]: e for e in self.baseline().record["entries"]}[self.repo.path_of(self.t1)]
        self.assertEqual(before["body_sha256"], after["body_sha256"])
        self.assertEqual(before["protected_frontmatter_sha256"], after["protected_frontmatter_sha256"])
        self.repo.save(self.t1, labels=("harness-verification-gated", "other"))
        changed = {e["path"]: e for e in self.baseline().record["entries"]}[self.repo.path_of(self.t1)]
        self.assertNotEqual(after["protected_frontmatter_sha256"], changed["protected_frontmatter_sha256"])
        self.repo.save(self.t1, body="different body\n")
        body = {e["path"]: e for e in self.baseline().record["entries"]}[self.repo.path_of(self.t1)]
        self.assertNotEqual(after["body_sha256"], body["body_sha256"])

    def test_owned_path_dirty_variants_fail(self) -> None:
        def run(setup) -> set[str]:
            repo = ShipmentRepo()
            self.addCleanup(repo.cleanup)
            setup(repo)
            return {v.rule for v in dc.baseline_phase(repo.root, ["docs/a.md"], DOCS, BACKLOG).violations}

        def modified(r): r.write("docs/a.md", "x\n")
        def staged(r): r.write("docs/a.md", "x\n"); r.git("add", "docs/a.md")
        def deleted(r): (r.root / "docs" / "a.md").unlink()
        def renamed(r): r.git("mv", "docs/a.md", "docs/a2.md")
        def untracked(r):
            r.git("rm", "-q", "--cached", "docs/a.md")

        for name, setup in (("modified", modified), ("staged", staged), ("deleted", deleted),
                            ("renamed", renamed), ("untracked", untracked)):
            with self.subTest(name):
                self.assertIn("OWNED_PATH_DIRTY_AT_BASELINE", run(setup))

    def test_new_untracked_owned_file_fails(self) -> None:
        self.repo.write("docs/brand-new.md", "n\n")
        result = self.baseline(owned=("docs/brand-new.md",))
        self.assertEqual(result.exit_code, 1)
        self.assertEqual({v.rule for v in result.violations}, {"OWNED_PATH_DIRTY_AT_BASELINE"})

    def test_self_digest_detects_alteration(self) -> None:
        self.repo.claim_all()
        record = self.baseline().record
        self.assertTrue(dc.verify_self_digest(record))
        for mutate in (
            lambda r: r["entries"][0].__setitem__("worktree", "100644 " + "0" * 64),
            lambda r: r["entries"][0].__setitem__("index", None),
            lambda r: r["entries"][0].__setitem__("body_sha256", "0" * 64),
            lambda r: r["entries"][0].__setitem__("protected_frontmatter_sha256", "0" * 64),
            lambda r: r.__setitem__("head_sha", "0" * 40),
            lambda r: r["entries"].pop(),
        ):
            tampered = copy.deepcopy(record)
            mutate(tampered)
            self.assertFalse(dc.verify_self_digest(tampered))

    def test_unparseable_frontmatter_fails_closed(self) -> None:
        self.repo.write(self.repo.path_of(self.t1), "---\nid: [unclosed\n---\nbody\n")
        result = self.baseline()
        self.assertEqual(result.status, "error")
        self.assertEqual(result.exit_code, 2)
        self.repo.write(self.repo.path_of(self.t1), "no frontmatter at all\n")
        self.assertEqual(self.baseline().status, "error")

    def test_invalid_owned_rule_and_git_failure(self) -> None:
        self.assertEqual(dc.baseline_phase(self.repo.root, ["src/mod.py"], DOCS, BACKLOG).status, "violation")
        self.assertEqual(dc.baseline_phase(self.repo.root, [], DOCS, BACKLOG).status, "error")
        self.assertEqual(dc.baseline_phase(self.repo.root / "missing", ["docs/a.md"], DOCS, BACKLOG).status, "error")


if __name__ == "__main__":
    unittest.main()
