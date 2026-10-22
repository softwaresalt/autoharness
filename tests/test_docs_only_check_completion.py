"""Tests for the docs_only_check completion phase and the two-task shipment flow (216.009-T)."""

from __future__ import annotations

import copy
import tempfile
import subprocess
import unittest
from pathlib import Path

from _docs_only_repo import BACKLOG, DOCS, ShipmentRepo, item_text
from autoharness import docs_only_check as dc


class CompletionBase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = ShipmentRepo()
        self.addCleanup(self.repo.cleanup)
        self.t1, self.t2 = self.repo.TASKS
        self.manifest = [self.repo.SHIPMENT, *self.repo.members]

    def baseline(self, owned):
        result = dc.baseline_phase(self.repo.root, owned, DOCS, BACKLOG)
        self.assertEqual(result.status, "pass", (result.violations, result.errors))
        return result.record

    def complete(self, record, owned, task=None):
        return dc.completion_phase(
            self.repo.root, owned, DOCS, BACKLOG, record,
            task_id=task or self.t1, feature_id=self.repo.FEATURE,
            shipment_id=self.repo.SHIPMENT, manifest_ids=self.manifest,
        )

    def rules(self, result):
        return {v.rule for v in result.violations}


class BaselineInputBindingTests(CompletionBase):
    def test_completion_rejects_owned_path_not_admitted_at_baseline(self) -> None:
        self.repo.claim_all()
        self.repo.write("docs/b.md", "dirty before baseline\n")
        base = self.baseline(["docs/a.md"])
        self.assertEqual(base["owned_paths"], ["docs/a.md"])
        result = self.complete(base, ["docs/b.md"])
        self.assertEqual(result.status, "error")
        self.assertEqual(result.exit_code, 2)
        self.assertTrue(any("INPUT_MISMATCH" in e for e in result.errors), result.errors)

    def test_completion_rejects_mismatched_roots(self) -> None:
        self.repo.claim_all()
        base = self.baseline(["docs/a.md"])
        result = dc.completion_phase(
            self.repo.root, ["docs/a.md"], DOCS, ".other-backlog", base,
            task_id=self.t1, feature_id=self.repo.FEATURE,
            shipment_id=self.repo.SHIPMENT, manifest_ids=self.manifest,
        )
        self.assertEqual(result.exit_code, 2)

    def test_tampered_bound_inputs_fail_digest(self) -> None:
        self.repo.claim_all()
        base = copy.deepcopy(self.baseline(["docs/a.md"]))
        base["owned_paths"] = ["docs/b.md"]
        result = self.complete(base, ["docs/b.md"])
        self.assertEqual(result.exit_code, 2)
        self.assertTrue(any("DIGEST_MISMATCH" in e for e in result.errors), result.errors)


class TwoTaskShipmentFlowTests(CompletionBase):
    def test_two_task_shipment_end_to_end(self) -> None:
        repo = self.repo
        repo.claim_all()
        repo.add_label(self.t1)
        base1 = self.baseline(["docs/a.md"])
        repo.write("docs/a.md", "a edited\n")
        repo.save(self.t1, status="active", updated="2026-02-02T00:00:00Z")
        done1 = self.complete(base1, ["docs/a.md"])
        self.assertEqual(done1.status, "pass", (done1.violations, done1.errors))
        self.assertEqual(done1.record["implementation"]["result"], "pass")
        self.assertEqual(done1.record["lifecycle"]["result"], "pass")
        repo.close_out(self.t1, "docs: task 1", ("docs/a.md",))
        repo.add_label(self.t2)
        base2 = self.baseline(["docs/b.md"])
        paths = {e["path"] for e in base2["entries"]}
        self.assertIn("docs/memory/session.md", paths)
        repo.write("docs/b.md", "b edited\n")
        done2 = self.complete(base2, ["docs/b.md"], task=self.t2)
        self.assertEqual(done2.status, "pass", (done2.violations, done2.errors))
        self.assertIn("docs/b.md", done2.record["delta_paths"])
        self.assertNotIn("docs/memory/session.md", done2.record["delta_paths"])

    def test_allowed_mutation_of_already_dirty_lifecycle_file(self) -> None:
        self.repo.claim_all()
        base = self.baseline(["docs/a.md"])
        self.repo.write("docs/a.md", "edit\n")
        self.repo.save(self.t1, status="done", updated="2026-05-05T00:00:00Z", labels=("harness-verification-gated",))
        self.repo.save(self.repo.FEATURE, updated="2026-05-05T00:00:00Z")
        self.repo.save(self.repo.SHIPMENT, updated="2026-05-05T00:00:00Z")
        self.assertEqual(self.complete(base, ["docs/a.md"]).status, "pass")

    def test_new_checkpoint_admitted_existing_checkpoint_not(self) -> None:
        base = self.baseline(["docs/a.md"])
        self.repo.write("docs/a.md", "edit\n")
        self.repo.write(f"{BACKLOG}/checkpoints/new.json", "{}\n")
        self.assertEqual(self.complete(base, ["docs/a.md"]).status, "pass")
        self.repo.write(f"{BACKLOG}/checkpoints/old.json", '{"x":1}\n')
        result = self.complete(base, ["docs/a.md"])
        self.assertIn("BACKLOG_PATH_NOT_LIFECYCLE", self.rules(result))


    def _checkpoint_link(self, target: Path) -> Path:
        link = self.repo.root / BACKLOG / "checkpoints" / "linked.json"
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"cannot create symlink: {exc}")
        return link

    def test_untracked_checkpoint_symlink_is_rejected(self) -> None:
        base = self.baseline(["docs/a.md"])
        self.repo.write("docs/a.md", "edit\n")
        self._checkpoint_link(self.repo.root / "README.md")
        result = self.complete(base, ["docs/a.md"])
        self.assertIn("NOT_REGULAR_FILE", self.rules(result))
        self.assertEqual(result.exit_code, 1)

    def test_untracked_checkpoint_symlink_outside_workspace_is_rejected(self) -> None:
        base = self.baseline(["docs/a.md"])
        self.repo.write("docs/a.md", "edit\n")
        with tempfile.TemporaryDirectory() as outside:
            self._checkpoint_link(Path(outside) / "secret.json")
            result = self.complete(base, ["docs/a.md"])
        self.assertIn("NOT_REGULAR_FILE", self.rules(result))
        self.assertEqual(result.exit_code, 1)

    def test_staged_checkpoint_symlink_with_restored_regular_file_is_rejected(self) -> None:
        base = self.baseline(["docs/a.md"])
        self.repo.write("docs/a.md", "edit\n")
        link = self.repo.root / BACKLOG / "checkpoints" / "linked.json"
        target = self.repo.root / "README.md"
        self._checkpoint_link(target)
        self.repo.git("add", "--", f"{BACKLOG}/checkpoints/linked.json")
        link.unlink()
        link.write_text("{}\n", encoding="utf-8", newline="")
        result = self.complete(base, ["docs/a.md"])
        self.assertIn("NOT_REGULAR_FILE", self.rules(result))
        self.assertEqual(result.exit_code, 1)


class CompletionViolationTests(CompletionBase):
    def setUp(self) -> None:
        super().setUp()
        self.repo.claim_all()
        self.owned = ["docs/a.md"]

    def run_case(self, mutate, *, pre=None):
        self.repo.write("docs/a.md", "a\n")
        if pre:
            pre()
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        mutate()
        return self.complete(base, self.owned)

    def test_item_outside_manifest(self) -> None:
        result = self.run_case(lambda: self.repo.write(f"{BACKLOG}/queue/888-T.md", item_text("888-T")))
        self.assertIn("BACKLOG_PATH_NOT_LIFECYCLE", self.rules(result))
        self.assertEqual(result.exit_code, 1)

    def test_modified_tracked_item_outside_manifest(self) -> None:
        result = self.run_case(lambda: self.repo.write(f"{BACKLOG}/queue/777-T.md", item_text("777-T", body="x\n")))
        self.assertIn("BACKLOG_PATH_NOT_LIFECYCLE", self.rules(result))

    def test_stash_edit(self) -> None:
        result = self.run_case(lambda: self.repo.write(f"{BACKLOG}/stash.jsonl", "{\"a\":1}\n"))
        self.assertIn("BACKLOG_PATH_NOT_LIFECYCLE", self.rules(result))

    def test_body_edit_of_own_file(self) -> None:
        result = self.run_case(lambda: self.repo.save(self.t1, body="tampered\n"))
        self.assertIn("LIFECYCLE_BODY_CHANGED", self.rules(result))

    def test_body_edit_of_already_dirty_lifecycle_file(self) -> None:
        self.repo.add_label(self.t1)
        result = self.run_case(lambda: self.repo.save(self.t1, body="tampered\n"))
        self.assertIn("LIFECYCLE_BODY_CHANGED", self.rules(result))

    def test_protected_frontmatter_and_non_route_label_in_dirty_file(self) -> None:
        self.repo.add_label(self.t1)
        for mutate in (
            lambda: self.repo.save(self.t1, extra="priority: low"),
            lambda: self.repo.save(self.t1, labels=("harness-verification-gated", "sneaky")),
        ):
            with self.subTest():
                self.repo.save(self.t1, extra="", labels=("harness-verification-gated",))
                result = self.run_case(mutate)
                self.assertIn("LIFECYCLE_PROTECTED_FRONTMATTER_CHANGED", self.rules(result))

    def test_feature_and_shipment_protected_keys(self) -> None:
        for item in (self.repo.FEATURE, self.repo.SHIPMENT):
            with self.subTest(item=item):
                self.repo.save(item, extra="")
                result = self.run_case(lambda: self.repo.save(item, extra="parent_id: 1-F"))
                self.assertIn("LIFECYCLE_PROTECTED_FRONTMATTER_CHANGED", self.rules(result))
                self.repo.save(item, extra="")

    def test_sibling_edited(self) -> None:
        result = self.run_case(lambda: self.repo.save(self.t2, updated="2026-09-09T00:00:00Z"))
        self.assertIn("SIBLING_MEMBER_CHANGED", self.rules(result))

    def test_src_and_non_owned_docs(self) -> None:
        result = self.run_case(lambda: self.repo.write("src/mod.py", "x = 2\n"))
        self.assertIn("DENY_LIST", self.rules(result))
        result = self.run_case(lambda: self.repo.write("docs/b.md", "other\n"))
        self.assertIn("NOT_OWNED_PATH", self.rules(result))
        self.assertEqual(result.record["implementation"]["result"], "violation")
        self.assertEqual(result.record["lifecycle"]["result"], "pass")

    def test_preexisting_dirty_path_modified_again(self) -> None:
        pre = lambda: self.repo.write("docs/memory/keep.md", "dirty\n")
        result = self.run_case(lambda: self.repo.write("docs/memory/keep.md", "dirty again\n"), pre=pre)
        self.assertIn("NOT_OWNED_PATH", self.rules(result))

    def test_preexisting_dirty_path_unchanged_is_not_delta(self) -> None:
        self.repo.write("docs/memory/keep.md", "dirty\n")
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        self.assertEqual(self.complete(base, self.owned).status, "pass")

    def test_dual_layer_changes(self) -> None:
        keep = "docs/memory/keep.md"
        self.repo.write(keep, "k1\n")
        self.repo.git("add", keep)
        self.repo.write(keep, "k2\n")
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        # staged content changes while the working-tree bytes are restored
        self.repo.write(keep, "k3\n")
        self.repo.git("add", keep)
        self.repo.write(keep, "k2\n")
        self.assertIn("NOT_OWNED_PATH", self.rules(self.complete(base, self.owned)))
        # reverse: staged content restored, working tree changes
        self.repo.write(keep, "k1\n")
        self.repo.git("add", keep)
        self.repo.write(keep, "k9\n")
        self.assertIn("NOT_OWNED_PATH", self.rules(self.complete(base, self.owned)))

    def test_tampered_record_and_head_moved(self) -> None:
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        tampered = copy.deepcopy(base)
        tampered["entries"].append({"path": "src/mod.py", "index": None, "worktree": None})
        result = self.complete(tampered, self.owned)
        self.assertEqual(result.exit_code, 2)
        self.assertEqual(self.complete({"phase": "baseline"}, self.owned).exit_code, 2)
        self.repo.git("add", "docs/a.md")
        self.repo.git("commit", "-q", "-m", "moved")
        self.assertEqual(self.complete(base, self.owned).exit_code, 2)

    def test_rejected_baseline_is_invalid_for_completion(self) -> None:
        self.repo.write("docs/a.md", "dirty\n")
        rejected = dc.baseline_phase(self.repo.root, ["docs/a.md"], DOCS, BACKLOG)
        self.assertEqual(rejected.exit_code, 1)
        self.assertIn("OWNED_PATH_DIRTY_AT_BASELINE", self.rules(rejected))
        result = self.complete(rejected.record, ["docs/a.md"])
        self.assertEqual(result.exit_code, 2)
        self.assertTrue(any("not a passing baseline" in e for e in result.errors))

    def test_bad_inputs_are_errors(self) -> None:
        base = self.baseline(self.owned)
        bad = dc.completion_phase(
            self.repo.root, self.owned, DOCS, BACKLOG, base, task_id="../x", feature_id=self.repo.FEATURE,
            shipment_id=self.repo.SHIPMENT, manifest_ids=self.manifest,
        )
        self.assertEqual(bad.exit_code, 2)
        absent = dc.completion_phase(
            self.repo.root, self.owned, DOCS, BACKLOG, base, task_id="404-T", feature_id=self.repo.FEATURE,
            shipment_id=self.repo.SHIPMENT, manifest_ids=self.manifest,
        )
        self.assertEqual(absent.exit_code, 2)

    def test_read_manifest_from_live_shipment_file(self) -> None:
        ids = dc.read_manifest_ids(self.repo.root, BACKLOG, self.repo.SHIPMENT)
        self.assertEqual(ids, list(self.repo.members))
        with self.assertRaises(dc.DocsOnlyError):
            dc.read_manifest_ids(self.repo.root, BACKLOG, "404-S")

    def test_owned_path_rules_apply_at_completion(self) -> None:
        base = self.baseline(self.owned)
        result = dc.completion_phase(
            self.repo.root, ["src/mod.py"], DOCS, BACKLOG, base, task_id=self.t1,
            feature_id=self.repo.FEATURE, shipment_id=self.repo.SHIPMENT, manifest_ids=self.manifest,
        )
        self.assertEqual(result.exit_code, 1)


class StashAppendOnlyTests(CompletionBase):
    STASH = f"{BACKLOG}/stash.jsonl"
    OLD = '{"id":"AAAA0001","text":"existing"}\n'
    NEW = '{"id":"BBBB0002","text":"DEFERRED SCOPE EXPANSION: follow-up","kind":"chore"}\n'

    def setUp(self) -> None:
        super().setUp()
        self.repo.write(self.STASH, self.OLD)
        self.repo.commit_all("stash seed")
        self.repo.claim_all()
        self.owned = ["docs/a.md"]

    def run_stash(self, content: str, *, stage: bool = False):
        self.repo.write("docs/a.md", "a\n")
        self.repo.write(self.STASH, self.OLD)
        self.repo.git("reset", "-q", "--", self.STASH)
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        self.repo.write(self.STASH, content)
        if stage:
            self.repo.git("add", "--", self.STASH)
        return self.complete(base, self.owned)

    def test_append_of_deferred_entry_after_baseline_passes(self) -> None:
        result = self.run_stash(self.OLD + self.NEW)
        self.assertEqual(result.status, "pass", (result.violations, result.errors))
        self.assertIn(self.STASH, result.record["delta_paths"])
        self.assertEqual(self.run_stash(self.OLD + self.NEW, stage=True).status, "pass")

    def test_non_append_changes_still_fail(self) -> None:
        cases = {
            "edit": '{"id":"AAAA0001","text":"changed"}\n' + self.NEW,
            "removal": "",
            "rewrite": self.NEW + self.OLD,
            "no trailing newline": self.OLD + self.NEW.rstrip("\n"),
            "non-deferred entry": self.OLD + '{"id":"CCCC0003","text":"plain"}\n',
            "malformed": self.OLD + "not json\n",
            "blank line": self.OLD + "\n" + self.NEW,
        }
        for name, content in cases.items():
            with self.subTest(name):
                result = self.run_stash(content)
                self.assertIn("BACKLOG_PATH_NOT_LIFECYCLE", self.rules(result))
                self.assertEqual(result.exit_code, 1)

    def test_staged_layer_must_also_be_append_only(self) -> None:
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        self.repo.write(self.STASH, "{}\n")
        self.repo.git("add", "--", self.STASH)
        self.repo.write(self.STASH, self.OLD + self.NEW)
        self.assertIn("BACKLOG_PATH_NOT_LIFECYCLE", self.rules(self.complete(base, self.owned)))

    def test_staged_deletion_with_valid_working_tree_append_fails(self) -> None:
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        self.repo.git("rm", "-q", "--cached", "--", self.STASH)
        self.repo.write(self.STASH, self.OLD + self.NEW)
        result = self.complete(base, self.owned)
        self.assertIn("BACKLOG_PATH_NOT_LIFECYCLE", self.rules(result))

    def test_stash_dirty_at_baseline_fails_closed(self) -> None:
        self.repo.write(self.STASH, self.OLD + self.NEW)
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        self.repo.write(self.STASH, self.OLD + self.NEW + self.NEW.replace("BBBB0002", "DDDD0004"))
        self.assertIn("BACKLOG_PATH_NOT_LIFECYCLE", self.rules(self.complete(base, self.owned)))

    def test_staged_symlink_mode_stash_with_valid_append_fails(self) -> None:
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        content = self.OLD + self.NEW
        blob = subprocess.run(
            ["git", "-C", str(self.repo.root), "hash-object", "-w", "--stdin"],
            input=content.encode("utf-8"), capture_output=True, check=True,
        ).stdout.decode().strip()
        self.repo.git("update-index", "--cacheinfo", f"120000,{blob},{self.STASH}")
        self.repo.write(self.STASH, content)
        self.assertIn("BACKLOG_PATH_NOT_LIFECYCLE", self.rules(self.complete(base, self.owned)))


class ReviewHardeningTests(CompletionBase):
    def setUp(self) -> None:
        super().setUp()
        self.repo.claim_all()
        self.owned = ["docs/a.md"]

    def test_lifecycle_file_replaced_by_identical_symlink_is_rejected(self) -> None:
        for item in (self.t1, self.repo.FEATURE, self.repo.SHIPMENT):
            with self.subTest(item):
                rel = self.repo.path_of(item)
                base = self.baseline(self.owned)
                self.repo.write("docs/a.md", "edit\n")
                live = self.repo.root.joinpath(*rel.split("/"))
                content = live.read_bytes()
                target = self.repo.root / "docs" / "linked-copy.md"
                target.write_bytes(content)
                live.unlink()
                try:
                    live.symlink_to(target)
                except (OSError, NotImplementedError) as exc:
                    self.skipTest(f"cannot create symlink: {exc}")
                try:
                    result = self.complete(base, self.owned)
                    self.assertIn("LIFECYCLE_FILE_MISSING", self.rules(result))
                    self.assertEqual(result.exit_code, 1)
                finally:
                    live.unlink()
                    live.write_bytes(content)
                    target.unlink()
                    self.repo.git("checkout", "--", "docs/a.md")
    def args(self, base, **over):
        kwargs = dict(task_id=self.t1, feature_id=self.repo.FEATURE, shipment_id=self.repo.SHIPMENT, manifest_ids=self.manifest)
        kwargs.update(over)
        return dc.completion_phase(self.repo.root, self.owned, DOCS, BACKLOG, base, **kwargs)

    def blob(self, path: str) -> str:
        return self.repo.git("hash-object", "-w", path).strip()

    def test_case_colliding_dirty_paths_keep_exact_identity(self) -> None:
        repo = self.repo
        repo.git("config", "core.ignorecase", "false")
        upper, lower = self.blob("README.md"), self.blob("docs/b.md")
        for name in ("src/Foo.py", "src/foo.py"):
            repo.git("update-index", "--add", "--cacheinfo", f"100644,{upper},{name}")
        base = self.baseline(self.owned)
        self.assertEqual({e["path"] for e in base["entries"]} & {"src/Foo.py", "src/foo.py"}, {"src/Foo.py", "src/foo.py"})
        repo.git("update-index", "--cacheinfo", f"100644,{lower},src/foo.py")
        result = self.args(base)
        self.assertIn("src/foo.py", result.record["delta_paths"])
        self.assertNotIn("src/Foo.py", result.record["delta_paths"])
        self.assertIn("NOT_OWNED_PATH", self.rules(result))

    def test_sibling_substituted_as_feature_is_rejected(self) -> None:
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        self.assertEqual(self.args(base).status, "pass")
        for wrong in (self.t2, "777-T", "404-F", self.repo.SHIPMENT, self.t1):
            result = self.args(base, feature_id=wrong)
            self.assertEqual(result.exit_code, 2, wrong)

    def test_task_with_other_parent_is_rejected(self) -> None:
        self.repo.save(self.t1, extra="parent_id: 901-F")
        self.repo.commit_all("reparent")
        base = self.baseline(self.owned)
        result = self.args(base)
        self.assertEqual(result.exit_code, 2)

    def test_task_only_manifest_resolves_feature_through_parent_id(self) -> None:
        manifest = [self.repo.SHIPMENT, *self.repo.TASKS]
        base = self.baseline(self.owned)
        self.repo.write("docs/a.md", "edit\n")
        self.assertEqual(self.args(base, manifest_ids=manifest).status, "pass")
        for wrong in (self.t2, "777-T", "404-F"):
            self.assertEqual(self.args(base, manifest_ids=manifest, feature_id=wrong).exit_code, 2, wrong)
        self.repo.git("rm", "-q", "--cached", "--", self.repo.path_of(self.repo.FEATURE))
        (self.repo.root / self.repo.path_of(self.repo.FEATURE)).unlink()
        self.assertEqual(self.args(base, manifest_ids=manifest).exit_code, 2)

    def test_case_variant_owned_delta_path_gets_symlink_check(self) -> None:
        owned = ["docs/new.md"]
        base = dc.baseline_phase(self.repo.root, owned, DOCS, BACKLOG).record
        target = self.repo.root / "README.md"
        link = self.repo.root / "docs" / "NEW.md"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"cannot create symlink: {exc}")
        result = dc.completion_phase(
            self.repo.root, owned, DOCS, BACKLOG, base, task_id=self.t1, feature_id=self.repo.FEATURE,
            shipment_id=self.repo.SHIPMENT, manifest_ids=self.manifest,
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn("SYMLINK", self.rules(result))

    def test_staged_symlink_with_restored_working_tree_is_rejected(self) -> None:
        base = self.baseline(self.owned)
        link = self.blob("README.md")
        self.repo.git("update-index", "--cacheinfo", f"120000,{link},docs/a.md")
        self.assertEqual(self.repo.git("diff", "--cached", "--name-only").strip(), "docs/a.md")
        result = self.args(base)
        self.assertIn("NOT_REGULAR_FILE", self.rules(result))
        self.assertEqual(result.exit_code, 1)

    def test_archive_copy_beside_queue_copy_is_rejected(self) -> None:
        for item in (self.t1, self.repo.FEATURE, self.repo.SHIPMENT):
            repo = self.repo
            base = self.baseline(self.owned)
            repo.write(f"{BACKLOG}/archive/{item}.md", item_text(item, body="arbitrary\n"))
            result = self.args(base)
            if item == self.t1:
                self.assertEqual(result.exit_code, 2, item)
            else:
                self.assertIn("LIFECYCLE_DUPLICATE_COPY", self.rules(result), item)
            (repo.root / BACKLOG / "archive" / f"{item}.md").unlink()

    def test_archive_relocation_preserves_content_rules(self) -> None:
        repo = self.repo
        base = self.baseline(self.owned)
        queue = repo.root / BACKLOG / "queue" / f"{self.t1}.md"
        moved = repo.root / BACKLOG / "archive" / f"{self.t1}.md"
        moved.parent.mkdir(parents=True, exist_ok=True)
        text = queue.read_text(encoding="utf-8")
        queue.unlink()
        moved.write_text(text.replace("status: active", "status: done"), encoding="utf-8", newline="")
        self.assertEqual(self.args(base).status, "pass")
        moved.write_text(text + "extra body\n", encoding="utf-8", newline="")
        self.assertIn("LIFECYCLE_BODY_CHANGED", self.rules(self.args(base)))
        moved.write_text(text.replace("id: 900.001-T", "id: 900.001-T\nshipment: 999-S"), encoding="utf-8", newline="")
        self.assertIn("LIFECYCLE_PROTECTED_FRONTMATTER_CHANGED", self.rules(self.args(base)))


if __name__ == "__main__":
    unittest.main()


class SubmoduleFingerprintTests(CompletionBase):
    def add_submodule(self) -> None:
        sub = ShipmentRepo.__mro__[1]()
        self.addCleanup(sub.cleanup)
        try:
            self.repo.git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(sub.root), "vendor/sub")
        except subprocess.CalledProcessError as exc:
            self.skipTest(f"git submodule add unavailable: {exc}")
        self.repo.commit_all("add submodule")

    def test_dirty_submodule_at_baseline_is_rejected(self) -> None:
        self.add_submodule()
        self.repo.claim_all()
        self.repo.write("vendor/sub/README.md", "dirty\n")
        result = dc.baseline_phase(self.repo.root, ["docs/a.md"], DOCS, BACKLOG)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("SUBMODULE_DIRTY_AT_BASELINE", self.rules(result))

    def test_ignore_submodules_setting_does_not_hide_dirty_baseline(self) -> None:
        self.add_submodule()
        self.repo.claim_all()
        self.repo.git("config", "diff.ignoreSubmodules", "all")
        self.repo.git("config", "submodule.vendor/sub.ignore", "all")
        self.repo.write("vendor/sub/README.md", "dirty\n")
        result = dc.baseline_phase(self.repo.root, ["docs/a.md"], DOCS, BACKLOG)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("SUBMODULE_DIRTY_AT_BASELINE", self.rules(result))

    def test_ignore_submodules_setting_does_not_hide_task_submodule_commit(self) -> None:
        self.add_submodule()
        self.repo.claim_all()
        self.repo.git("config", "diff.ignoreSubmodules", "all")
        self.repo.git("config", "submodule.vendor/sub.ignore", "all")
        base = self.baseline(["docs/a.md"])
        self.repo.write("docs/a.md", "edit\n")
        sub_root = self.repo.root / "vendor" / "sub"
        subprocess.run(["git", "-C", str(sub_root), "config", "user.email", "t@example.com"], check=True)
        subprocess.run(["git", "-C", str(sub_root), "config", "user.name", "t"], check=True)
        self.repo.write("vendor/sub/new.txt", "x\n")
        subprocess.run(["git", "-C", str(sub_root), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(sub_root), "commit", "-q", "-m", "sub change"], check=True)
        result = self.complete(base, ["docs/a.md"])
        self.assertIn("UNFINGERPRINTABLE_ENTRY", self.rules(result))

    def test_submodule_dirtied_during_task_is_rejected(self) -> None:
        self.add_submodule()
        self.repo.claim_all()
        base = self.baseline(["docs/a.md"])
        self.repo.write("docs/a.md", "edit\n")
        self.repo.write("vendor/sub/README.md", "dirty\n")
        result = self.complete(base, ["docs/a.md"])
        self.assertIn("UNFINGERPRINTABLE_ENTRY", self.rules(result))
