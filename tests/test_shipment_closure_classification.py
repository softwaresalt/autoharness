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
        # in the same queue directory. `_enumerate_children` must scan every
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


if __name__ == "__main__":
    unittest.main()
