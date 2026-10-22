"""Tests for the docs_only_check completion phase and the two-task shipment flow (216.009-T)."""

from __future__ import annotations

import copy
import unittest

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


if __name__ == "__main__":
    unittest.main()
