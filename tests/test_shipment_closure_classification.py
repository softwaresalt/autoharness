"""Tests for the shipment-closure close-path classifier.

See ``src/autoharness/gates/shipment_closure.py`` and the shipment-closure
policy/skill contract surfaces for the authoritative behavior this module
implements.
"""

from __future__ import annotations

import os
from pathlib import Path
import unittest
import uuid

from autoharness.gates.shipment_closure import ClosePath, classify_shipment_close_path


def _write_artifact_file(
    backlog_dir: Path,
    folder: str,
    filename: str,
    artifact_id: str,
    artifact_type: str,
    parent_id: str | None = None,
    status: str | None = None,
) -> None:
    lines = ["---", f"id: {artifact_id}", f"artifact_type: {artifact_type}"]
    if parent_id is not None:
        lines.append(f"parent_id: {parent_id}")
    if status is not None:
        lines.append(f"status: {status}")
    lines.append("---")
    lines.append(f"# {artifact_id}")
    content = "\n".join(lines) + "\n"
    target_dir = backlog_dir / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / filename).write_text(content, encoding="utf-8")


def _write_artifact(
    backlog_dir: Path,
    folder: str,
    artifact_id: str,
    artifact_type: str,
    parent_id: str | None = None,
    status: str | None = None,
) -> None:
    _write_artifact_file(
        backlog_dir,
        folder,
        f"{artifact_id}.md",
        artifact_id,
        artifact_type,
        parent_id=parent_id,
        status=status,
    )


class ShipmentClosureClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(os.getcwd()).resolve(strict=True)
        nonce = uuid.uuid4().hex
        self.scratch_dir = (
            self.repo_root / ".autoharness" / "staging" / "tmp" / nonce
        ).resolve()
        if os.path.commonpath([str(self.repo_root), str(self.scratch_dir)]) != str(
            self.repo_root
        ):
            raise AssertionError(
                f"containment violation: {self.scratch_dir} escapes {self.repo_root}"
            )
        self.backlog_dir = self.scratch_dir / ".backlogit"
        (self.backlog_dir / "queue").mkdir(parents=True, exist_ok=True)
        (self.backlog_dir / "archive").mkdir(parents=True, exist_ok=True)

    def _classify_out_of_manifest_child(
        self,
        *,
        status: str | None,
        folder: str = "queue",
        feature_id: str = "300-F",
        manifest_child_id: str = "300.001-T",
        extra_child_id: str = "300.002-T",
    ):
        _write_artifact(self.backlog_dir, "queue", feature_id, "feature")
        _write_artifact(
            self.backlog_dir, "queue", manifest_child_id, "task", parent_id=feature_id
        )
        _write_artifact(
            self.backlog_dir,
            folder,
            extra_child_id,
            "task",
            parent_id=feature_id,
            status=status,
        )
        return classify_shipment_close_path([feature_id, manifest_child_id], self.backlog_dir)

    def _classify_out_of_manifest_grandchild(
        self,
        *,
        status: str | None,
        folder: str = "queue",
        feature_id: str = "301-F",
        manifest_child_id: str = "301.001-T",
        extra_grandchild_id: str = "301.001.001-T",
    ):
        _write_artifact(self.backlog_dir, "queue", feature_id, "feature")
        _write_artifact(
            self.backlog_dir, "queue", manifest_child_id, "task", parent_id=feature_id
        )
        _write_artifact(
            self.backlog_dir,
            folder,
            extra_grandchild_id,
            "task",
            parent_id=manifest_child_id,
            status=status,
        )
        return classify_shipment_close_path([feature_id, manifest_child_id], self.backlog_dir)

    def _classify_torn_out_of_manifest_descendant(self):
        _write_artifact(self.backlog_dir, "queue", "302-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "302.001-T", "task", parent_id="302-F")
        _write_artifact(
            self.backlog_dir,
            "queue",
            "302.002-T",
            "task",
            parent_id="302-F",
            status="queued",
        )
        _write_artifact(
            self.backlog_dir,
            "archive",
            "302.002-T",
            "task",
            parent_id="302-F",
            status="archived",
        )
        return classify_shipment_close_path(["302-F", "302.001-T"], self.backlog_dir)

    def _classify_duplicate_out_of_manifest_descendant(self):
        _write_artifact(self.backlog_dir, "queue", "303-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "303.001-T", "task", parent_id="303-F")
        _write_artifact_file(
            self.backlog_dir,
            "queue",
            "303.002-T.md",
            "303.002-T",
            "task",
            parent_id="303-F",
            status="queued",
        )
        _write_artifact_file(
            self.backlog_dir,
            "queue",
            "303.002-T-copy.md",
            "303.002-T",
            "task",
            parent_id="303-F",
            status="queued",
        )
        return classify_shipment_close_path(["303-F", "303.001-T"], self.backlog_dir)

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
        _write_artifact(self.backlog_dir, "queue", "201-F", "feature")

        decision = classify_shipment_close_path(["201-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("201-F",)

    def test_root_feature_missing_child_falls_back_to_safe_close(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "202-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "202.001-T", "task", parent_id="202-F")
        _write_artifact(self.backlog_dir, "queue", "202.002-T", "task", parent_id="202-F")

        decision = classify_shipment_close_path(["202-F", "202.001-T"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "202.002-T" in decision.reason

    def test_non_root_feature_member_falls_back_to_safe_close(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "203-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "204-F", "feature", parent_id="203-F")

        decision = classify_shipment_close_path(["204-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "204-F" in decision.reason
        assert "not a root" in decision.reason

    def test_extra_task_belonging_to_no_member_feature_falls_back_to_safe_close(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "205-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "205.001-T", "task", parent_id="205-F")
        _write_artifact(self.backlog_dir, "queue", "206.001-T", "task", parent_id="206-F")

        decision = classify_shipment_close_path(
            ["205-F", "205.001-T", "206.001-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "206.001-T" in decision.reason

    def test_childlessness_query_failure_falls_back_to_safe_close_not_treated_as_childless(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "207-F", "feature")
        (self.backlog_dir / "queue" / "garbage.md").write_text(
            "this is not a valid backlog artifact file\nno frontmatter delimiters here\n",
            encoding="utf-8",
        )

        decision = classify_shipment_close_path(["207-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "could not be verified" in decision.reason

    def test_adding_child_to_previously_qualifying_childless_feature_flips_to_safe_close(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "208-F", "feature")

        before = classify_shipment_close_path(["208-F"], self.backlog_dir)
        assert before.close_path is ClosePath.CASCADE

        _write_artifact(self.backlog_dir, "queue", "208.001-T", "task", parent_id="208-F")

        after = classify_shipment_close_path(["208-F"], self.backlog_dir)
        assert after.close_path is ClosePath.SAFE_CLOSE
        assert "208.001-T" in after.reason

    def test_manifest_with_no_feature_member_falls_back_to_safe_close(self) -> None:
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
        _write_artifact(self.backlog_dir, "queue", "210-F", "feature")

        decision = classify_shipment_close_path(["*"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "*" in decision.reason

    def test_file_with_no_declared_id_is_never_trusted_via_filename_match(self) -> None:
        target_dir = self.backlog_dir / "queue"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "211-F.md").write_text(
            "---\nartifact_type: feature\n---\n# 211-F\n", encoding="utf-8"
        )

        decision = classify_shipment_close_path(["211-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "211-F" in decision.reason

    def test_all_manifest_members_pre_archived_still_selects_cascade(self) -> None:
        _write_artifact(self.backlog_dir, "archive", "220-F", "feature")
        _write_artifact(self.backlog_dir, "archive", "220.001-T", "task", parent_id="220-F")
        _write_artifact(self.backlog_dir, "archive", "220.002-T", "task", parent_id="220-F")

        decision = classify_shipment_close_path(
            ["220-F", "220.001-T", "220.002-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("220-F",)

    def test_feature_pre_archived_children_queued_still_selects_cascade(self) -> None:
        _write_artifact(self.backlog_dir, "archive", "221-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "221.001-T", "task", parent_id="221-F")
        _write_artifact(self.backlog_dir, "queue", "221.002-T", "task", parent_id="221-F")

        decision = classify_shipment_close_path(
            ["221-F", "221.001-T", "221.002-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("221-F",)

    def test_feature_queued_children_pre_archived_still_selects_cascade(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "222-F", "feature")
        _write_artifact(self.backlog_dir, "archive", "222.001-T", "task", parent_id="222-F")
        _write_artifact(self.backlog_dir, "queue", "222.002-T", "task", parent_id="222-F")

        decision = classify_shipment_close_path(
            ["222-F", "222.001-T", "222.002-T"], self.backlog_dir
        )

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("222-F",)

    def test_mixed_pre_archived_and_queued_manifest_members_still_selects_cascade(self) -> None:
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
        _write_artifact(self.backlog_dir, "archive", "224-F", "feature")

        decision = classify_shipment_close_path(["224-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("224-F",)

    def test_pre_archived_out_of_manifest_child_falls_back_to_safe_close(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "225-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "225.001-T", "task", parent_id="225-F")
        _write_artifact(self.backlog_dir, "archive", "225.002-T", "task", parent_id="225-F")

        decision = classify_shipment_close_path(["225-F", "225.001-T"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "225.002-T" in decision.reason

    def test_pre_archived_feature_with_pre_archived_out_of_manifest_child_falls_back_to_safe_close(
        self,
    ) -> None:
        _write_artifact(self.backlog_dir, "archive", "228-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "228.001-T", "task", parent_id="228-F")
        _write_artifact(self.backlog_dir, "archive", "228.002-T", "task", parent_id="228-F")

        decision = classify_shipment_close_path(["228-F", "228.001-T"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "228.002-T" in decision.reason

    def test_out_of_manifest_grandchild_falls_back_to_safe_close(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "230-F", "feature")
        _write_artifact(self.backlog_dir, "queue", "230.001-T", "task", parent_id="230-F")
        _write_artifact(
            self.backlog_dir, "queue", "230.001.001-T", "task", parent_id="230.001-T"
        )

        decision = classify_shipment_close_path(["230-F", "230.001-T"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "230.001.001-T" in decision.reason

    def test_full_descendant_tree_present_in_manifest_still_selects_cascade(self) -> None:
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
        _write_artifact(self.backlog_dir, "queue", "226-F", "feature")
        _write_artifact(
            self.backlog_dir, "archive", "227-F", "feature", parent_id="226-F"
        )

        decision = classify_shipment_close_path(["227-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE
        assert "227-F" in decision.reason
        assert "not a root" in decision.reason

    def test_archived_out_of_manifest_child_selects_cascade(self) -> None:
        decision = self._classify_out_of_manifest_child(status="archived", folder="archive")

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("300-F",)

    def test_done_but_not_archived_out_of_manifest_child_falls_back_to_safe_close(self) -> None:
        decision = self._classify_out_of_manifest_child(status="done")

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_done_but_not_archived_out_of_manifest_child_reason_names_observed_status(self) -> None:
        decision = self._classify_out_of_manifest_child(status="done")

        assert "done" in decision.reason

    def test_live_out_of_manifest_child_falls_back_to_safe_close(self) -> None:
        """Indicative/unproven rationale only: a reported returned_ids=[] never authorizes cascade."""
        decision = self._classify_out_of_manifest_child(status="queued")

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_live_out_of_manifest_child_reason_names_observed_status(self) -> None:
        """Indicative/unproven rationale only: a reported returned_ids=[] never authorizes cascade."""
        decision = self._classify_out_of_manifest_child(status="queued")

        assert "queued" in decision.reason

    def test_out_of_manifest_child_in_archive_without_status_falls_back_to_safe_close(self) -> None:
        decision = self._classify_out_of_manifest_child(status=None, folder="archive")

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_archived_out_of_manifest_grandchild_selects_cascade(self) -> None:
        decision = self._classify_out_of_manifest_grandchild(status="archived", folder="archive")

        assert decision.close_path is ClosePath.CASCADE
        assert decision.qualifying_feature_ids == ("301-F",)

    def test_live_out_of_manifest_grandchild_falls_back_to_safe_close(self) -> None:
        decision = self._classify_out_of_manifest_grandchild(status="queued")

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_titlecase_archived_out_of_manifest_child_falls_back_to_safe_close(self) -> None:
        decision = self._classify_out_of_manifest_child(status="Archived", feature_id="304-F")

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_titlecase_archived_out_of_manifest_child_reason_names_observed_status(self) -> None:
        decision = self._classify_out_of_manifest_child(status="Archived", feature_id="304-F")

        assert "Archived" in decision.reason

    def test_uppercase_archived_out_of_manifest_child_falls_back_to_safe_close(self) -> None:
        decision = self._classify_out_of_manifest_child(status="ARCHIVED", feature_id="305-F")

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_uppercase_archived_out_of_manifest_child_reason_names_observed_status(self) -> None:
        decision = self._classify_out_of_manifest_child(status="ARCHIVED", feature_id="305-F")

        assert "ARCHIVED" in decision.reason

    def test_whitespace_padded_archived_out_of_manifest_child_falls_back_to_safe_close(self) -> None:
        """The padded variant must be written as the YAML-quoted literal status: " archived "."""
        decision = self._classify_out_of_manifest_child(status='" archived "', feature_id="306-F")

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_whitespace_padded_archived_out_of_manifest_child_reason_names_observed_status(
        self,
    ) -> None:
        """The padded variant must be written as the YAML-quoted literal status: " archived "."""
        decision = self._classify_out_of_manifest_child(status='" archived "', feature_id="306-F")

        assert " archived " in decision.reason

    def test_torn_out_of_manifest_descendant_falls_back_to_safe_close(self) -> None:
        decision = self._classify_torn_out_of_manifest_descendant()

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_torn_out_of_manifest_descendant_reason_is_torn_specific(self) -> None:
        decision = self._classify_torn_out_of_manifest_descendant()

        assert "torn" in decision.reason.lower() or "ambiguous" in decision.reason.lower()

    def test_duplicate_id_within_single_root_falls_back_to_safe_close(self) -> None:
        decision = self._classify_duplicate_out_of_manifest_descendant()

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_bool_status_out_of_manifest_child_falls_back_to_safe_close(self) -> None:
        decision = self._classify_out_of_manifest_child(status="yes", feature_id="307-F")

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_null_status_out_of_manifest_child_falls_back_to_safe_close(self) -> None:
        decision = self._classify_out_of_manifest_child(status="", feature_id="308-F")

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def _symlink_manifest_item(self, feature_id: str) -> None:
        """Write a real ``feature_id`` record outside the backlog tree, then
        replace its ``queue/`` entry with a symlink pointing at that real file."""

        real_target = self.scratch_dir / f"{feature_id}-real.md"
        real_target.write_text(
            f"---\nid: {feature_id}\nartifact_type: feature\nstatus: queued\n---\n",
            encoding="utf-8",
        )
        symlink_path = self.backlog_dir / "queue" / f"{feature_id}.md"
        symlink_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(real_target, symlink_path)
        except OSError:
            self.skipTest("symlink creation is not permitted in this environment")

    def test_symlinked_manifest_item_falls_back_to_safe_close(self) -> None:
        self._symlink_manifest_item("309-F")

        decision = classify_shipment_close_path(["309-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_symlinked_manifest_item_reason_names_symlink(self) -> None:
        self._symlink_manifest_item("310-F")

        decision = classify_shipment_close_path(["310-F"], self.backlog_dir)

        assert "symlink" in decision.reason.lower()

    def _symlink_out_of_manifest_descendant(self, feature_id: str, manifest_child_id: str) -> None:
        """Feature + in-manifest child are real files; an out-of-manifest
        descendant is a symlink pointing at a real ``status: archived`` file."""

        _write_artifact(self.backlog_dir, "queue", feature_id, "feature")
        _write_artifact(
            self.backlog_dir, "queue", manifest_child_id, "task", parent_id=feature_id
        )
        descendant_id = f"{feature_id}-symlinked-child"
        real_target = self.scratch_dir / f"{descendant_id}-real.md"
        real_target.write_text(
            f"---\nid: {descendant_id}\nartifact_type: task\nparent_id: {feature_id}\n"
            "status: archived\n---\n",
            encoding="utf-8",
        )
        symlink_path = self.backlog_dir / "archive" / f"{descendant_id}.md"
        symlink_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(real_target, symlink_path)
        except OSError:
            self.skipTest("symlink creation is not permitted in this environment")

    def test_symlinked_out_of_manifest_descendant_falls_back_to_safe_close(self) -> None:
        self._symlink_out_of_manifest_descendant("311-F", "311.001-T")

        decision = classify_shipment_close_path(["311-F", "311.001-T"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_out_of_manifest_descendant_with_no_declared_id_falls_back_to_safe_close(self) -> None:
        """A scanned record with a missing/non-string ``id`` must never be trusted
        via its filename stem, even when that stem happens to declare
        ``status: archived``: falling back to the filename would let a forged or
        malformed record masquerade as an engine-inert out-of-manifest descendant."""

        feature_id = "312-F"
        manifest_child_id = "312.001-T"
        _write_artifact(self.backlog_dir, "queue", feature_id, "feature")
        _write_artifact(
            self.backlog_dir, "queue", manifest_child_id, "task", parent_id=feature_id
        )
        # No declared `id:` field at all; the filename stem happens to look like
        # a plausible archived descendant, which must NOT be trusted.
        (self.backlog_dir / "archive" / "312.002-T.md").write_text(
            f"---\nartifact_type: task\nparent_id: {feature_id}\nstatus: archived\n---\n",
            encoding="utf-8",
        )

        decision = classify_shipment_close_path(
            [feature_id, manifest_child_id], self.backlog_dir
        )

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def _symlink_directory_component(self, feature_id: str, symlinked_folder: str) -> None:
        """Replace an entire ``queue``/``archive`` directory with a symlink
        pointing at a real, out-of-tree directory containing a valid root
        feature -- the untrusted-directory-component variant of the leaf-file
        symlink tests above."""

        real_dir = self.scratch_dir / f"{symlinked_folder}-real"
        real_dir.mkdir(parents=True, exist_ok=True)
        (real_dir / f"{feature_id}.md").write_text(
            f"---\nid: {feature_id}\nartifact_type: feature\nstatus: queued\n---\n",
            encoding="utf-8",
        )
        symlink_path = self.backlog_dir / symlinked_folder
        # setUp() pre-creates queue/ and archive/ as real (empty) directories;
        # remove that placeholder before replacing it with a symlink.
        symlink_path.rmdir()
        try:
            os.symlink(real_dir, symlink_path, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation is not permitted in this environment")

    def test_symlinked_queue_directory_falls_back_to_safe_close(self) -> None:
        self._symlink_directory_component("313-F", "queue")

        decision = classify_shipment_close_path(["313-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE

    def test_symlinked_archive_directory_falls_back_to_safe_close(self) -> None:
        _write_artifact(self.backlog_dir, "queue", "314-F", "feature")
        self._symlink_directory_component("314-F-other", "archive")

        decision = classify_shipment_close_path(["314-F"], self.backlog_dir)

        assert decision.close_path is ClosePath.SAFE_CLOSE


if __name__ == "__main__":
    unittest.main()
