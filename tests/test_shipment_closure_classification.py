"""Tests for the P-015 verified fully-covered-root close-path classifier (118.007-T).

See ``src/autoharness/gates/shipment_closure.py`` and the "VERIFIED
FULLY-COVERED-ROOT EXCEPTION" subsection of P-015 in
``templates/policies/workflow-policies.md.tmpl`` for the authoritative
contract this module implements.
"""

from __future__ import annotations

from pathlib import Path

import tempfile
import unittest

from autoharness.gates.shipment_closure import ClosePath, classify_shipment_close_path


def _write_artifact(
    backlog_dir: Path,
    folder: str,
    artifact_id: str,
    artifact_type: str,
    parent_id: str | None = None,
) -> None:
    lines = ["---", f"id: {artifact_id}", f"artifact_type: {artifact_type}"]
    if parent_id is not None:
        lines.append(f"parent_id: {parent_id}")
    lines.append("---")
    lines.append(f"# {artifact_id}")
    content = "\n".join(lines) + "\n"
    target_dir = backlog_dir / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / f"{artifact_id}.md").write_text(content, encoding="utf-8")




class ShipmentClosureClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.backlog_dir = Path(self._tmpdir.name) / ".backlogit"
        (self.backlog_dir / "queue").mkdir(parents=True)
        (self.backlog_dir / "archive").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_fully_covered_root_feature_selects_cascade(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "200-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "200.001-T", "task", parent_id="200-F")
        _write_artifact(self.backlog_dir, "queue", "200.002-T", "task", parent_id="200-F")

        decision = classify_shipment_close_path(
            ["200-F", "200.001-T", "200.002-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("200-F",)


    def test_verified_childless_terminal_root_feature_also_qualifies(self) -> None:
        # Regression case (must NOT be special-cased to any specific feature id):
        # a root feature member with zero children, positively verified against
        # the live backlog (not merely absent from the manifest), still
        # qualifies for cascade close.
        _write_artifact(self.backlog_dir, "queue", "201-F", "feature")

        decision = classify_shipment_close_path(["201-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("201-F",)


    def test_root_feature_missing_child_falls_back_to_safe_close(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "202-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "202.001-T", "task", parent_id="202-F")
        _write_artifact(self.backlog_dir, "queue", "202.002-T", "task", parent_id="202-F")

        # 202.002-T is a real child of 202-F but is NOT listed in the manifest.
        decision = classify_shipment_close_path(["202-F", "202.001-T"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "202.002-T" in decision.reason


    def test_non_root_feature_member_falls_back_to_safe_close(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "203-F", "feature")
        # 204-F declares a parent -- it is not a root feature.
        _write_artifact(self.backlog_dir, "queue", "204-F", "feature", parent_id="203-F")

        decision = classify_shipment_close_path(["204-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "204-F" in decision.reason
        assert "not a root" in decision.reason


    def test_extra_task_belonging_to_no_member_feature_falls_back_to_safe_close(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "205-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "205.001-T", "task", parent_id="205-F")
        # 206.001-T is an orphaned manifest member: its parent is not any
        # feature member of this manifest.
        _write_artifact(self.backlog_dir, "queue", "206.001-T", "task", parent_id="206-F")

        decision = classify_shipment_close_path(
            ["205-F", "205.001-T", "206.001-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "206.001-T" in decision.reason


    def test_childlessness_query_failure_falls_back_to_safe_close_not_treated_as_childless(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "207-F", "feature")
        # An unrelated malformed record (no frontmatter delimiters at all) sits
        # in the same queue directory. `_build_children_index` must scan every
        # queue/archive record to positively verify childlessness for 207-F, so
        # this malformed record makes that enumeration untrustworthy -- it must
        # NOT be silently skipped and treated as "no children found" (that would
        # be exactly the anti-vacuity defect P-015 explicitly forbids).
        (self.backlog_dir / "queue" / "garbage.md").write_text(
            "this is not a valid backlog artifact file\nno frontmatter delimiters here\n",
            encoding="utf-8",
        )

        decision = classify_shipment_close_path(["207-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "could not be verified" in decision.reason


    def test_adding_child_to_previously_qualifying_childless_feature_flips_to_safe_close(self) -> None:
        # Proves the classifier observes LIVE state, not a cached/hardcoded
        # allowance: the exact same manifest classifies differently before and
        # after the backlog gains a new (unlisted) child.
        _write_artifact(self.backlog_dir, "queue", "208-F", "feature")

        before = classify_shipment_close_path(["208-F"], self.backlog_dir)
        assert before.close_path is ClosePath.CASCADE

        _write_artifact(self.backlog_dir, "queue", "208.001-T", "task", parent_id="208-F")

        after = classify_shipment_close_path(["208-F"], self.backlog_dir)
        assert after.close_path is ClosePath.SAFE_CLOSE
        assert "208.001-T" in after.reason


    def test_manifest_with_no_feature_member_falls_back_to_safe_close(self) -> None:
        # A task-only manifest (the ordinary Durable Rule shape) is simply not
        # eligible for this exception at all -- it is not a violation of any
        # precondition, just outside the exception's scope.
        _write_artifact(self.backlog_dir, "queue", "209-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "209.001-T", "task", parent_id="209-F")

        decision = classify_shipment_close_path(["209.001-T"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "no feature member" in decision.reason


    def test_manifest_item_that_cannot_be_found_falls_back_to_safe_close(self) -> None:
        decision = classify_shipment_close_path(["999-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "999-F" in decision.reason


    def test_empty_manifest_falls_back_to_safe_close(self) -> None:
        decision = classify_shipment_close_path([], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE


    def test_manifest_item_with_glob_metacharacters_does_not_match_unrelated_file(self) -> None:
        # Regression: a manifest item id containing glob metacharacters must
        # never be treated as a glob pattern that resolves to an unrelated,
        # arbitrary backlog file. It must be matched LITERALLY (and therefore
        # not found, falling back to safe-close), never silently resolve to
        # whatever happens to sort first on disk.
        _write_artifact(self.backlog_dir, "queue", "210-F", "feature")

        decision = classify_shipment_close_path(["*"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "*" in decision.reason


    def test_file_with_no_declared_id_is_never_trusted_via_filename_match(self) -> None:
        # Regression: a candidate backlog file whose FILENAME happens to
        # match the manifest id but whose frontmatter declares no `id` field
        # at all must never be accepted on filename shape alone -- it must
        # be treated the same as "not found", falling back to safe-close.
        target_dir = self.backlog_dir / "queue"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "211-F.md").write_text(
            "---\nartifact_type: feature\n---\n# 211-F\n", encoding="utf-8"
        )

        decision = classify_shipment_close_path(["211-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "211-F" in decision.reason



    # --- Regression tests: pre-archived manifest members and the P-015
    # cascade classifier (132.003-T). These prove the classifier already
    # scans BOTH queue/ and archive/ for every manifest member -- a manifest
    # member's archival state at classification time never changes the
    # CASCADE/SAFE_CLOSE verdict, exactly as
    # docs/spikes/2026-08-18-cascade-close-pre-archived-member-behavior.md
    # found for the live backlogit engine. See templates/skills/
    # shipment-reconcile/SKILL.md.tmpl's Cascade Close Sub-Procedure preamble
    # and P-015's "VERIFIED FULLY-COVERED-ROOT EXCEPTION" item 7 in
    # templates/policies/workflow-policies.md.tmpl for the authoritative
    # contract these tests guard.

    def test_all_manifest_members_pre_archived_still_selects_cascade(self) -> None:
        # Every manifest member -- feature and both children -- is already
        # archived when classification runs. A pre-archived manifest member
        # must not disqualify CASCADE.
        _write_artifact(self.backlog_dir, "archive", "220-F", "feature")
        _write_artifact(self.backlog_dir, "archive", "220.001-T", "task", parent_id="220-F")
        _write_artifact(self.backlog_dir, "archive", "220.002-T", "task", parent_id="220-F")

        decision = classify_shipment_close_path(
            ["220-F", "220.001-T", "220.002-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("220-F",)


    def test_feature_pre_archived_children_queued_still_selects_cascade(self) -> None:
        # The covering feature is already archived while its children remain
        # queued -- an asymmetric pre-archival pattern that must still
        # qualify.
        _write_artifact(self.backlog_dir, "archive", "221-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "221.001-T", "task", parent_id="221-F")
        _write_artifact(self.backlog_dir, "queue", "221.002-T", "task", parent_id="221-F")

        decision = classify_shipment_close_path(
            ["221-F", "221.001-T", "221.002-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("221-F",)


    def test_feature_queued_children_pre_archived_still_selects_cascade(self) -> None:
        # The inverse asymmetric pattern: the covering feature remains
        # queued while one child is already archived.
        _write_artifact(self.backlog_dir, "queue", "222-F", "feature")
        _write_artifact(self.backlog_dir, "archive", "222.001-T", "task", parent_id="222-F")
        _write_artifact(self.backlog_dir, "queue", "222.002-T", "task", parent_id="222-F")

        decision = classify_shipment_close_path(
            ["222-F", "222.001-T", "222.002-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("222-F",)


    def test_mixed_pre_archived_and_queued_manifest_members_still_selects_cascade(self) -> None:
        # A three-child manifest with a mix of queued and pre-archived
        # children alongside a queued feature.
        _write_artifact(self.backlog_dir, "queue", "223-F", "feature")
        _write_artifact(self.backlog_dir, "archive", "223.001-T", "task", parent_id="223-F")
        _write_artifact(self.backlog_dir, "queue", "223.002-T", "task", parent_id="223-F")
        _write_artifact(self.backlog_dir, "archive", "223.003-T", "task", parent_id="223-F")

        decision = classify_shipment_close_path(
            ["223-F", "223.001-T", "223.002-T", "223.003-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("223-F",)


    def test_verified_childless_terminal_root_feature_pre_archived_still_qualifies(self) -> None:
        # A childless, terminal root feature that is ITSELF already archived
        # (not merely its children) must still positively verify childless
        # and qualify for CASCADE -- childlessness verification scans both
        # queue/ and archive/, and so does the feature-record lookup itself.
        _write_artifact(self.backlog_dir, "archive", "224-F", "feature")

        decision = classify_shipment_close_path(["224-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("224-F",)


    def test_pre_archived_out_of_manifest_child_falls_back_to_safe_close(self) -> None:
        # Negative case: a REAL child of the root feature already sits in
        # archive/ but is NOT listed in the manifest. Pre-archival must not
        # excuse an out-of-manifest child from the full-coverage precondition
        # -- this must still fall back to safe-close exactly as an
        # out-of-manifest child in queue/ would (existing coverage:
        # test_root_feature_missing_child_falls_back_to_safe_close).
        _write_artifact(self.backlog_dir, "queue", "225-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "225.001-T", "task", parent_id="225-F")
        _write_artifact(self.backlog_dir, "archive", "225.002-T", "task", parent_id="225-F")

        decision = classify_shipment_close_path(["225-F", "225.001-T"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "225.002-T" in decision.reason


    def test_pre_archived_feature_with_pre_archived_out_of_manifest_child_falls_back_to_safe_close(
        self,
    ) -> None:
        # Strengthens the prior negative case (Copilot review, PR #365): that
        # case only pre-archived the out-of-manifest CHILD while leaving the
        # feature itself queued, so it only proved the child's location is
        # irrelevant -- it did not prove that pre-archiving the FEATURE
        # record cannot itself create a false CASCADE grant. Here BOTH the
        # root feature and the out-of-manifest child are already archived;
        # the manifest still omits the real child, so this must still fall
        # back to safe-close.
        _write_artifact(self.backlog_dir, "archive", "228-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "228.001-T", "task", parent_id="228-F")
        _write_artifact(self.backlog_dir, "archive", "228.002-T", "task", parent_id="228-F")

        decision = classify_shipment_close_path(["228-F", "228.001-T"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "228.002-T" in decision.reason


    def test_out_of_manifest_grandchild_falls_back_to_safe_close(self) -> None:
        # Regression (155-S, PR #407 review, thread PRRT_kwDORzpWpM6b2MJv):
        # the "fully covered" precondition must walk the FULL descendant
        # tree, not just direct children of the feature. Backlogit's own
        # `releaseScopeItemIDs` recursively adds every descendant of each
        # manifest item before `collectArchiveCandidateIDs` archives terminal
        # descendants -- a classifier that only checks the feature's direct
        # children would wrongly select CASCADE here even though the
        # manifest task has an out-of-manifest subtask (grandchild of the
        # feature) that the live engine would archive.
        _write_artifact(self.backlog_dir, "queue", "230-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "230.001-T", "task", parent_id="230-F")
        # 230.001-002-T is a real child of the MANIFEST TASK 230.001-T (a
        # grandchild of 230-F) and is NOT listed in the manifest.
        _write_artifact(
            self.backlog_dir, "queue", "230.001.001-T", "task", parent_id="230.001-T"
        )

        decision = classify_shipment_close_path(["230-F", "230.001-T"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "230.001.001-T" in decision.reason

    def test_full_descendant_tree_present_in_manifest_still_selects_cascade(self) -> None:
        # Positive counterpart: when every descendant at every depth IS a
        # manifest member, CASCADE is still correctly selected -- the fix
        # must not regress the ordinary multi-level-but-fully-covered case.
        _write_artifact(self.backlog_dir, "queue", "231-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "231.001-T", "task", parent_id="231-F")
        _write_artifact(
            self.backlog_dir, "queue", "231.001.001-T", "task", parent_id="231.001-T"
        )

        decision = classify_shipment_close_path(
            ["231-F", "231.001-T", "231.001.001-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("231-F",)

    def test_pre_archived_non_root_feature_falls_back_to_safe_close(self) -> None:
        # Negative case: a feature member that declares a parent_id (is not a
        # root) is disqualifying regardless of whether its own record lives
        # in queue/ or archive/ -- pre-archival tolerance never relaxes the
        # root-ness precondition.
        _write_artifact(self.backlog_dir, "queue", "226-F", "feature")
        _write_artifact(
            self.backlog_dir, "archive", "227-F", "feature", parent_id="226-F"
        )

        decision = classify_shipment_close_path(["227-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "227-F" in decision.reason
        assert "not a root" in decision.reason

if __name__ == "__main__":
    unittest.main()
