"""Safe-close observation-set tests (192.013-T, plan unit A2b).

Four table-driven scenarios (plan ``### A2b``):

1. a task-only, partial-feature manifest yields the parent feature and the
   unshipped siblings, including a sibling already archived at baseline;
2. an out-of-manifest descendant of a manifest feature member is included;
3. the exclusion table: ``excluded_ids``, the closure-scope exclusion of a
   whole-feature manifest (re-plan cycle-1 R11), and the UNVERIFIED-engine
   ``deliberation_records`` (re-plan cycle-2 C2-1);
4. the torn-versus-missing table (re-plan cycle-2 C2-2).

Fixtures live in a Git-ignored scratch directory inside the workspace
(``.autoharness/staging/tmp/``), the convention of
``tests/test_shipment_closure_classification.py`` (constitution IV).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import unittest
import uuid
from pathlib import Path

from autoharness.gates.cascade_evidence import (
    DECLARED_STATUS_MISSING,
    CascadeEvidenceError,
    ObservationEntry,
    observation_entry_to_record,
)
from autoharness.gates.shipment_closure import DeliberationRecordSnapshot
from autoharness.shipment_close import observation
from autoharness.shipment_close.observation import compute_observation_set, locate_record

_SHIPMENT = "900-S"


def write_artifact(
    backlog_dir: Path,
    folder: str,
    artifact_id: str,
    artifact_type: str,
    *,
    parent_id: str | None = None,
    status: str | None = None,
    filename: str | None = None,
    extra: str = "",
) -> Path:
    """Write one backlog record (the classification-test builder, plus a path return)."""

    lines = ["---", f"id: {artifact_id}", f"artifact_type: {artifact_type}"]
    if parent_id is not None:
        lines.append(f"parent_id: {parent_id}")
    if status is not None:
        lines.append(f"status: {status}")
    if extra:
        lines.append(extra)
    lines.append("---")
    lines.append(f"# {artifact_id}")
    target_dir = backlog_dir / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / (filename or f"{artifact_id}.md")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def make_scratch_backlog(test: unittest.TestCase) -> Path:
    """Create ``<repo>/.autoharness/staging/tmp/<nonce>/.backlogit/{queue,archive}``."""

    repo_root = Path(os.getcwd()).resolve(strict=True)
    scratch = (repo_root / ".autoharness" / "staging" / "tmp" / uuid.uuid4().hex).resolve()
    if os.path.commonpath([str(repo_root), str(scratch)]) != str(repo_root):
        raise AssertionError(f"containment violation: {scratch} escapes {repo_root}")
    backlog_dir = scratch / ".backlogit"
    (backlog_dir / "queue").mkdir(parents=True)
    (backlog_dir / "archive").mkdir(parents=True)
    test.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
    return backlog_dir


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _by_id(entries: tuple[ObservationEntry, ...]) -> dict[str, ObservationEntry]:
    return {entry.id: entry for entry in entries}


class PartialFeatureTests(unittest.TestCase):
    """Scenario 1: parent feature plus unshipped siblings (queue and archive)."""

    def test_task_only_partial_feature_manifest(self) -> None:
        backlog = make_scratch_backlog(self)
        feature = write_artifact(backlog, "queue", "500-F", "feature")
        write_artifact(backlog, "queue", "500.001-T", "task", parent_id="500-F", status="done")
        sibling = write_artifact(backlog, "queue", "500.002-T", "task", parent_id="500-F", status="queued")
        archived = write_artifact(backlog, "archive", "500.003-T", "task", parent_id="500-F", status="archived")
        write_artifact(backlog, "queue", _SHIPMENT, "shipment", status="active")
        write_artifact(backlog, "queue", "777-F", "feature")  # unrelated: never observed

        entries = compute_observation_set(["500.001-T"], _SHIPMENT, backlog, excluded_ids=())
        by_id = _by_id(entries)
        self.assertEqual(set(by_id), {"500-F", "500.002-T", "500.003-T"})
        self.assertEqual(
            by_id["500-F"],
            ObservationEntry(
                id="500-F",
                path=".backlogit/queue/500-F.md",
                location="queue",
                sha256=_sha(feature),
                declared_status=DECLARED_STATUS_MISSING,
            ),
        )
        self.assertEqual(by_id["500.002-T"].sha256, _sha(sibling))
        self.assertEqual(by_id["500.002-T"].declared_status, "queued")
        self.assertEqual(by_id["500.003-T"].location, "archive")
        self.assertEqual(by_id["500.003-T"].path, ".backlogit/archive/500.003-T.md")
        self.assertEqual(by_id["500.003-T"].sha256, _sha(archived))
        self.assertEqual(by_id["500.003-T"].declared_status, "archived")
        # Deterministic order, and every entry is encodable by the A1d codec.
        self.assertEqual([entry.id for entry in entries], sorted(by_id))
        for entry in entries:
            observation_entry_to_record(entry)
        # Private-name rule (re-plan cycle-2 C2-4): nothing private at module top level.
        for name in ("_scan_backlog", "_enumerate_descendants", "_read_artifact_record", "_check_path_containment"):
            self.assertFalse(hasattr(observation, name), name)

        located = locate_record(backlog, "500.003-T")
        self.assertIsNotNone(located)
        self.assertEqual(located.location, "archive")
        self.assertEqual(located.parent_id, "500-F")
        self.assertEqual(located.artifact_type, "task")
        self.assertIsNone(locate_record(backlog, "500.099-T"))


class DescendantTests(unittest.TestCase):
    """Scenario 2: out-of-manifest descendants of a manifest feature member."""

    def test_out_of_manifest_descendants_are_observed(self) -> None:
        backlog = make_scratch_backlog(self)
        write_artifact(backlog, "queue", "501-F", "feature")
        write_artifact(backlog, "queue", "501.001-T", "task", parent_id="501-F")
        write_artifact(backlog, "archive", "501.002-T", "task", parent_id="501-F", status="archived")
        grandchild = write_artifact(backlog, "queue", "501.001.001-T", "subtask", parent_id="501.001-T")
        write_artifact(backlog, "queue", _SHIPMENT, "shipment", status="active")

        entries = compute_observation_set(["501-F", "501.001-T"], _SHIPMENT, backlog, excluded_ids=())
        by_id = _by_id(entries)
        self.assertEqual(set(by_id), {"501.002-T", "501.001.001-T"})
        self.assertEqual(by_id["501.001.001-T"].sha256, _sha(grandchild))
        self.assertEqual(by_id["501.002-T"].location, "archive")


class ExclusionTests(unittest.TestCase):
    """Scenario 3: excluded IDs, closure scope, and UNVERIFIED deliberation records."""

    def test_exclusion_table(self) -> None:
        with self.subTest("excluded_ids removes a descendant"):
            backlog = make_scratch_backlog(self)
            write_artifact(backlog, "queue", "502-F", "feature")
            write_artifact(backlog, "queue", "502.001-T", "task", parent_id="502-F")
            write_artifact(backlog, "queue", "502-DL", "deliberation", parent_id="502-F", status="active")
            entries = compute_observation_set(["502.001-T"], _SHIPMENT, backlog, excluded_ids={"502-DL"})
            self.assertEqual(set(_by_id(entries)), {"502-F"})
            with_dl = compute_observation_set(["502.001-T"], _SHIPMENT, backlog, excluded_ids=())
            self.assertEqual(set(_by_id(with_dl)), {"502-F", "502-DL"})

        with self.subTest("whole-feature manifest: covering feature in closure scope"):
            backlog = make_scratch_backlog(self)
            write_artifact(backlog, "queue", "503-F", "feature")
            write_artifact(backlog, "queue", "503.001-T", "task", parent_id="503-F")
            archived = write_artifact(backlog, "archive", "503.002-T", "task", parent_id="503-F", status="archived")
            write_artifact(backlog, "queue", _SHIPMENT, "shipment", status="active", extra="parent_id: 503-F")
            entries = compute_observation_set(["503-F", "503.001-T"], _SHIPMENT, backlog, excluded_ids=())
            by_id = _by_id(entries)
            self.assertEqual(set(by_id), {"503.002-T"})
            self.assertEqual(by_id["503.002-T"].sha256, _sha(archived))

        with self.subTest("UNVERIFIED deliberation records are copied from the snapshot"):
            backlog = make_scratch_backlog(self)
            write_artifact(backlog, "queue", "504-F", "feature")
            write_artifact(backlog, "queue", "504.001-T", "task", parent_id="504-F")
            write_artifact(backlog, "archive", "505-DL", "deliberation", parent_id="504-F", status="archived")
            snapshot = DeliberationRecordSnapshot(
                path=".backlogit/queue/504-DL.md", declared_status="active", sha256="d" * 64
            )
            entries = compute_observation_set(
                ["504.001-T"],
                _SHIPMENT,
                backlog,
                excluded_ids={"504-DL", "505-DL"},
                deliberation_records=[("504-DL", snapshot)],
            )
            by_id = _by_id(entries)
            # 505-DL is an already-archived disposition: A2 never passes it.
            self.assertEqual(set(by_id), {"504-F", "504-DL"})
            self.assertEqual(
                by_id["504-DL"],
                ObservationEntry(
                    id="504-DL",
                    path=".backlogit/queue/504-DL.md",
                    location="queue",
                    sha256="d" * 64,
                    declared_status="active",
                ),
            )

        with self.subTest("a deliberation record path outside queue/archive raises"):
            backlog = make_scratch_backlog(self)
            write_artifact(backlog, "queue", "506-F", "feature")
            bad = DeliberationRecordSnapshot(path=".backlogit/other/506-DL.md", declared_status=None, sha256="e" * 64)
            with self.assertRaises(CascadeEvidenceError):
                compute_observation_set(
                    ["506-F"], _SHIPMENT, backlog, excluded_ids={"506-DL"}, deliberation_records=[("506-DL", bad)]
                )


class TornVersusMissingTests(unittest.TestCase):
    """Scenario 4: a torn member raises; a missing member is recorded (C2-2)."""

    def test_torn_versus_missing_table(self) -> None:
        with self.subTest("torn sibling raises and returns nothing"):
            backlog = make_scratch_backlog(self)
            write_artifact(backlog, "queue", "507-F", "feature")
            write_artifact(backlog, "queue", "507.001-T", "task", parent_id="507-F")
            write_artifact(backlog, "queue", "507.002-T", "task", parent_id="507-F", status="queued")
            write_artifact(backlog, "archive", "507.002-T", "task", parent_id="507-F", status="archived")
            with self.assertRaises(CascadeEvidenceError):
                compute_observation_set(["507.001-T"], _SHIPMENT, backlog, excluded_ids=())

        with self.subTest("missing parent feature is recorded, not raised"):
            backlog = make_scratch_backlog(self)
            write_artifact(backlog, "queue", "508.001-T", "task", parent_id="508-F")
            write_artifact(backlog, "queue", "508.002-T", "task", parent_id="508-F")
            entries = compute_observation_set(["508.001-T"], _SHIPMENT, backlog, excluded_ids=())
            by_id = _by_id(entries)
            self.assertEqual(set(by_id), {"508-F", "508.002-T"})
            self.assertEqual(
                by_id["508-F"],
                ObservationEntry(id="508-F", path=None, location="missing", sha256=None, declared_status=None),
            )
            self.assertEqual(
                observation_entry_to_record(by_id["508-F"])["location"], "missing"
            )

        with self.subTest("an unreadable traversal scan raises"):
            backlog = make_scratch_backlog(self)
            write_artifact(backlog, "queue", "509.001-T", "task", parent_id="509-F")
            (backlog / "queue" / "broken.md").write_text("no frontmatter\n", encoding="utf-8")
            with self.assertRaises(CascadeEvidenceError):
                compute_observation_set(["509.001-T"], _SHIPMENT, backlog, excluded_ids=())

        with self.subTest("a stray candidate file that cannot be fingerprinted raises"):
            backlog = make_scratch_backlog(self)
            write_artifact(backlog, "queue", "510-F", "feature")
            write_artifact(backlog, "queue", "510.001-T", "task", parent_id="510-F")
            (backlog / "queue" / "510-F.notes").write_bytes(b"\xff\xfe not utf-8")
            with self.assertRaises(CascadeEvidenceError):
                compute_observation_set(["510.001-T"], _SHIPMENT, backlog, excluded_ids=())


if __name__ == "__main__":
    unittest.main()
