"""Unit B, task B2 (188.002-T): backlog root, records, membership and declarations.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "B2: Backlog root, records, membership and
declarations".

The private helper under test is ``harness_surfaces._read_records(reader, *,
workspace_root, shipment_id)`` (IM-16-F02.1). It accepts the reader the test
passes in so the test can observe ``usage.files_claimed``; it is not a patch
point (the only B patch point stays ``_resolve``'s limits, B4b, IM-06).

Every fixture is a real temporary workspace named after the test method. In
the RED phase the stub derives its marker suffix from that request
(``AHLC_B2_RECORDS_MEMBERSHIP:<workspace directory name>``), so each roster
test reaches its own marker. ``RecordsRosterTests`` is the expected-RED
roster; ``test_structural_*`` tests reach no stub and are outside it.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml
from _env_patch import patched_environ

from autoharness import harness_surfaces as hs
from autoharness.harness_read import ReadErrorCode, ReadLimits, open_reader

MARKER = "AHLC_B2_RECORDS_MEMBERSHIP"
ARCH = "harness-surface:harness-architect"
NONE = "harness-surface:none"


class RecordsFixture(unittest.TestCase):
    """Builds a workspace named after the running test method."""

    root_name = ".backlogit"

    def setUp(self) -> None:
        self.scratch = Path(tempfile.mkdtemp(prefix="ahlc-b2-"))
        self.addCleanup(shutil.rmtree, self.scratch, True)
        self.ws = self.scratch / self._testMethodName
        self.ws.mkdir()
        self.backlog = self.ws / self.root_name
        for folder in ("queue", "archive"):
            (self.backlog / folder).mkdir(parents=True)

    def write_raw(self, folder: str, item_id: str, data: bytes) -> Path:
        path = self.backlog / folder / f"{item_id}.md"
        path.write_bytes(data)
        return path

    def write(self, item_id: str, folder: str = "queue", **frontmatter: Any) -> Path:
        body = {"id": item_id, **frontmatter}
        text = "---\n" + yaml.safe_dump(body, sort_keys=False) + "---\n\nbody\n"
        return self.write_raw(folder, item_id, text.encode("utf-8"))

    def shipment(self, items: Any, item_id: str = "7-S", **extra: Any) -> None:
        custom = {"custom_fields": {"items": items}} if items is not _ABSENT else {}
        self.write(item_id, artifact_type="shipment", **custom, **extra)

    def task(self, item_id: str, labels: Any = (ARCH,), folder: str = "queue", **extra: Any) -> None:
        self.write(item_id, folder, artifact_type="task", labels=list(labels), **extra)

    def feature(self, item_id: str, labels: Any = (), **extra: Any) -> None:
        self.write(item_id, artifact_type="feature", labels=list(labels), **extra)

    def read(self, shipment_id: Any = "7-S", limits: ReadLimits | None = None) -> tuple[Any, Any]:
        reader = open_reader(workspace_root=self.ws, limits=limits)
        outcome = hs._read_records(reader, workspace_root=self.ws, shipment_id=shipment_id)
        return outcome, reader

    def assert_code(self, code: str, shipment_id: Any = "7-S") -> Any:
        outcome, _reader = self.read(shipment_id)
        self.assertIn(code, outcome.facts)
        self.assertEqual(outcome.reason_code, code)
        return outcome


_ABSENT = object()


class RecordsRosterTests(RecordsFixture):
    """Expected-RED roster: one fixture per class 2 and class 3 code, plus the B2 bounds."""

    # Class 2: backlog root and shipment record.

    def test_backlog_root_not_found(self) -> None:
        shutil.rmtree(self.backlog)
        outcome = self.assert_code("BACKLOG_ROOT_NOT_FOUND")
        self.assertIsNone(outcome.backlog_root)
        outcome, reader = self.read("7-S")
        self.assertEqual(reader.usage.files_claimed, 0)
        missing = self.scratch / "missing-workspace"
        reader = open_reader(workspace_root=missing)
        outcome = hs._read_records(reader, workspace_root=missing, shipment_id="7-S")
        self.assertEqual(outcome.reason_code, "BACKLOG_ROOT_NOT_FOUND")
        self.assertEqual(reader.usage.files_claimed, 0)

    def test_backlog_root_ambiguous(self) -> None:
        (self.ws / ".backlog").mkdir()
        outcome = self.assert_code("BACKLOG_ROOT_AMBIGUOUS")
        self.assertIsNone(outcome.backlog_root)

    def test_backlog_root_is_a_directory_probe(self) -> None:
        shutil.rmtree(self.backlog)
        (self.ws / ".backlogit").write_text("not a directory", encoding="utf-8")
        self.assert_code("BACKLOG_ROOT_NOT_FOUND")
        (self.ws / ".backlog" / "queue").mkdir(parents=True)
        path = self.ws / ".backlog" / "queue" / "7-S.md"
        path.write_text("---\nid: 7-S\nartifact_type: shipment\ncustom_fields:\n  items: ['1-T']\n---\n", encoding="utf-8")
        (self.ws / ".backlog" / "queue" / "1-T.md").write_text(
            f"---\nid: 1-T\nartifact_type: task\nlabels: ['{ARCH}']\n---\n", encoding="utf-8"
        )
        outcome, _reader = self.read()
        self.assertEqual(outcome.backlog_root, ".backlog")
        self.assertEqual(outcome.facts, ())

    def test_shipment_id_invalid(self) -> None:
        for invalid in ("", "7", "7-T", "x-S", "../7-S", "7-S\n", " 7-S", "7-s", "7.1-S", None, 7):
            with self.subTest(invalid=invalid):
                outcome, reader = self.read(invalid)
                self.assertEqual(outcome.reason_code, "SHIPMENT_ID_INVALID")
                self.assertIsNone(outcome.shipment_id)
                self.assertEqual(reader.usage.files_claimed, 0)

    def test_shipment_not_found(self) -> None:
        outcome = self.assert_code("SHIPMENT_NOT_FOUND")
        self.assertEqual(outcome.shipment_id, "7-S")
        self.assertEqual(outcome.backlog_root, ".backlogit")

    def test_shipment_ambiguous(self) -> None:
        self.shipment(["1-T"])
        self.write("7-S", "archive", artifact_type="shipment", custom_fields={"items": ["1-T"]})
        self.task("1-T")
        self.assert_code("SHIPMENT_AMBIGUOUS")

    def test_shipment_record_invalid(self) -> None:
        variants: dict[str, bytes | None] = {
            "no frontmatter": b"id: 7-S\n",
            "unterminated": b"---\nid: 7-S\nartifact_type: shipment\n",
            "bad yaml": b"---\nid: [7-S\n---\n",
            "not a mapping": b"---\n- 7-S\n---\n",
            "invalid utf-8": b"---\nid: 7-S\nartifact_type: shipment\ntitle: \xff\n---\n",
            "duplicate key": b"---\nid: 7-S\nid: 7-S\nartifact_type: shipment\n---\n",
            "alias": b"---\nid: &a 7-S\nartifact_type: shipment\ntitle: *a\n---\n",
            "missing id": b"---\nartifact_type: shipment\ncustom_fields:\n  items: ['1-T']\n---\n",
            "non-string type": b"---\nid: 7-S\nartifact_type: 3\n---\n",
            "directory": None,
        }
        self.task("1-T")
        for label, data in variants.items():
            with self.subTest(variant=label):
                target = self.backlog / "queue" / "7-S.md"
                if target.is_dir():
                    target.rmdir()
                elif target.exists():
                    target.unlink()
                if data is None:
                    target.mkdir()
                else:
                    target.write_bytes(data)
                self.assert_code("SHIPMENT_RECORD_INVALID")
        (self.backlog / "queue" / "7-S.md").rmdir()
        self.shipment(["1-T"])
        (self.backlog / "archive" / "7-S.md").mkdir()
        self.assert_code("SHIPMENT_RECORD_INVALID")

    def test_shipment_id_mismatch(self) -> None:
        self.task("1-T")
        self.write_raw("queue", "7-S", b"---\nid: 8-S\nartifact_type: shipment\ncustom_fields:\n  items: ['1-T']\n---\n")
        self.assert_code("SHIPMENT_ID_MISMATCH")
        self.write_raw("queue", "7-S", b"---\nid: 7-S\nartifact_type: feature\ncustom_fields:\n  items: ['1-T']\n---\n")
        self.assert_code("SHIPMENT_ID_MISMATCH")

    # Class 2: membership.

    def test_members_invalid(self) -> None:
        for items in (_ABSENT, None, "1-T", {"a": "1-T"}, ["1-T", 2], [["1-T"]]):
            with self.subTest(items=items):
                self.shipment(items)
                outcome, reader = self.read()
                self.assertEqual(outcome.reason_code, "MEMBERS_INVALID")
                self.assertEqual(reader.usage.files_claimed, 2)
        self.write_raw("queue", "7-S", b"---\nid: 7-S\nartifact_type: shipment\ncustom_fields: 3\n---\n")
        self.assert_code("MEMBERS_INVALID")

    def test_members_empty(self) -> None:
        self.shipment([])
        outcome, reader = self.read()
        self.assertEqual(outcome.reason_code, "MEMBERS_EMPTY")
        self.assertEqual(reader.usage.files_claimed, 2)

    def test_members_too_many(self) -> None:
        for count in (49, 512, 513):
            with self.subTest(count=count):
                items = [f"{index}-T" for index in range(1, count + 1)]
                self.shipment(items)
                self.task("1-T")
                outcome, reader = self.read()
                self.assertEqual(outcome.reason_code, "MEMBERS_TOO_MANY")
                self.assertLessEqual(reader.usage.files_claimed, 4)
                # Only the two shipment candidates were claimed: no member candidate read.
                self.assertEqual(reader.usage.files_claimed, 2)

    def test_members_admitted_bounds(self) -> None:
        for count in (1, 48):
            with self.subTest(count=count):
                items = [f"{index}-T" for index in range(1, count + 1)]
                self.shipment(items)
                for item in items:
                    self.task(item)
                outcome, reader = self.read()
                self.assertEqual(outcome.facts, ())
                self.assertIsNone(outcome.reason_code)
                self.assertEqual(reader.usage.files_claimed, 2 + 2 * count)
                self.assertEqual(len(outcome.declarations), count)

    def test_member_id_invalid(self) -> None:
        self.shipment(["1-T", "not-an-id", "2..1-T", ""])
        self.task("1-T")
        self.assert_code("MEMBER_ID_INVALID")

    def test_member_kind_unsupported(self) -> None:
        self.shipment(["1-T", "4-S", "5-B"])
        self.task("1-T")
        self.assert_code("MEMBER_KIND_UNSUPPORTED")

    def test_member_duplicate(self) -> None:
        self.shipment(["1-T", "1-T"])
        self.task("1-T")
        outcome, reader = self.read()
        self.assertEqual(outcome.reason_code, "MEMBER_DUPLICATE")
        self.assertEqual(reader.usage.files_claimed, 4)

    def test_member_not_found(self) -> None:
        self.shipment(["1-T", "2-T"])
        self.task("1-T")
        self.assert_code("MEMBER_NOT_FOUND")

    def test_member_ambiguous(self) -> None:
        self.shipment(["1-T"])
        self.task("1-T")
        self.task("1-T", folder="archive")
        self.assert_code("MEMBER_AMBIGUOUS")

    def test_member_record_invalid(self) -> None:
        self.shipment(["1-T"])
        variants: dict[str, bytes | None] = {
            "no frontmatter": b"plain\n",
            "bad yaml": b"---\nid: [1-T\n---\n",
            "labels not a list": b"---\nid: 1-T\nartifact_type: task\nlabels: harness-surface:none\n---\n",
            "non-string label": b"---\nid: 1-T\nartifact_type: task\nlabels: [3]\n---\n",
            "directory": None,
        }
        for label, data in variants.items():
            with self.subTest(variant=label):
                target = self.backlog / "queue" / "1-T.md"
                if target.is_dir():
                    target.rmdir()
                elif target.exists():
                    target.unlink()
                if data is None:
                    target.mkdir()
                else:
                    target.write_bytes(data)
                self.assert_code("MEMBER_RECORD_INVALID")

    def test_member_id_mismatch(self) -> None:
        self.shipment(["1-T", "2-F"])
        self.write_raw("queue", "1-T", f"---\nid: 9-T\nartifact_type: task\nlabels: ['{ARCH}']\n---\n".encode())
        self.write_raw("queue", "2-F", b"---\nid: 2-F\nartifact_type: task\nlabels: []\n---\n")
        outcome = self.assert_code("MEMBER_ID_MISMATCH")
        self.assertEqual(outcome.facts.count("MEMBER_ID_MISMATCH"), 2)

    def test_no_task_members(self) -> None:
        self.shipment(["1-F", "2-F"])
        self.feature("1-F")
        self.feature("2-F")
        outcome = self.assert_code("NO_TASK_MEMBERS")
        self.assertEqual(outcome.declarations, ())

    def test_features_never_expand(self) -> None:
        self.shipment(["1-F", "1.001-T"])
        self.feature("1-F")
        self.task("1.001-T")
        self.task("1.002-T", labels=["harness-surface:unknown-surface"], parent_id="1-F")
        outcome, reader = self.read()
        self.assertEqual(outcome.facts, ())
        self.assertEqual(reader.usage.files_claimed, 6)
        self.assertEqual(outcome.declarations, (hs.Declaration("1.001-T", "harness-architect"),))

    # Class 3: declarations.

    def test_feature_declares_surface(self) -> None:
        for labels in ([NONE], [ARCH], ["harness-surface:Bad"]):
            with self.subTest(labels=labels):
                self.shipment(["1-F", "2-T"])
                self.feature("1-F", labels=labels)
                self.task("2-T")
                self.assert_code("FEATURE_DECLARES_SURFACE")

    def test_declaration_missing(self) -> None:
        for labels in ([], ["ship-lifecycle", "Harness-Surface:none"]):
            with self.subTest(labels=labels):
                self.shipment(["1-T"])
                self.task("1-T", labels=labels)
                self.assert_code("DECLARATION_MISSING")
        self.shipment(["1-T"])
        self.write_raw("queue", "1-T", b"---\nid: 1-T\nartifact_type: task\n---\n")
        self.assert_code("DECLARATION_MISSING")

    def test_declaration_malformed(self) -> None:
        for label in ("harness-surface:", "harness-surface", "harness-surface:Bad_Name", "harness-surface:a--b",
                      "harness-surface:-a", "harness-surface: a"):
            with self.subTest(label=label):
                self.shipment(["1-T"])
                self.task("1-T", labels=[label])
                self.assert_code("DECLARATION_MALFORMED")

    def test_declaration_duplicate(self) -> None:
        self.shipment(["1-T"])
        self.task("1-T", labels=[ARCH, ARCH])
        self.assert_code("DECLARATION_DUPLICATE")

    def test_declaration_mixed(self) -> None:
        for labels in ([ARCH, NONE], [NONE, "harness-surface:other"], [ARCH, "harness-surface:other"]):
            with self.subTest(labels=labels):
                self.shipment(["1-T"])
                self.task("1-T", labels=labels)
                self.assert_code("DECLARATION_MIXED")

    def test_surface_unsupported(self) -> None:
        for label in ("harness-surface:harvest", "harness-surface:impl-plan"):
            with self.subTest(label=label):
                self.shipment(["1-T", "2-T"])
                self.task("1-T", labels=[label])
                self.task("2-T", labels=[NONE])
                outcome = self.assert_code("SURFACE_UNSUPPORTED")
                self.assertEqual(outcome.surface_ids, ())

    def test_class_3_tiebreak_listed_order(self) -> None:
        # Encounter order picks MIXED (5-T first), task-ID order picks UNSUPPORTED (1-T),
        # listed order picks MISSING (9-T): listed order governs.
        self.shipment(["5-T", "1-T", "9-T"])
        self.task("5-T", labels=[ARCH, NONE])
        self.task("1-T", labels=["harness-surface:other"])
        self.task("9-T", labels=[])
        outcome = self.assert_code("DECLARATION_MISSING")
        self.assertEqual(
            set(outcome.facts), {"DECLARATION_MIXED", "SURFACE_UNSUPPORTED", "DECLARATION_MISSING"}
        )
        self.assertEqual(outcome.facts, ("DECLARATION_MIXED", "SURFACE_UNSUPPORTED", "DECLARATION_MISSING"))
        # The same task can raise two class 3 facts; listed order picks MALFORMED over DUPLICATE.
        self.shipment(["1-T"])
        self.task("1-T", labels=["harness-surface:Bad", "harness-surface:Bad"])
        self.assert_code("DECLARATION_MALFORMED")

    # Bounds and isolation.

    def test_declarations_and_surface_union(self) -> None:
        self.shipment(["10-T", "1-F", "2-T", "2.1-T"])
        self.feature("1-F")
        self.task("10-T", labels=[NONE, "ship-lifecycle"])
        self.task("2-T")
        self.task("2.1-T", labels=[ARCH])
        outcome, _reader = self.read()
        self.assertEqual(outcome.facts, ())
        self.assertEqual(outcome.surface_ids, ("harness-architect",))
        self.assertEqual(
            outcome.declarations,
            (
                hs.Declaration("2-T", "harness-architect"),
                hs.Declaration("2.1-T", "harness-architect"),
                hs.Declaration("10-T", "none"),
            ),
        )
        self.assertEqual((outcome.backlog_root, outcome.shipment_id), (".backlogit", "7-S"))
        self.assertIsNone(outcome.read_limit)

    def test_backlogit_workspace_dir_ignored(self) -> None:
        self.shipment(["1-T"])
        self.task("1-T")
        baseline, _reader = self.read()
        decoy = self.scratch / "decoy"
        (decoy / ".backlogit" / "queue").mkdir(parents=True)
        with patched_environ(BACKLOGIT_WORKSPACE_DIR=str(decoy)):
            outcome, _reader = self.read()
        self.assertEqual(outcome, baseline)
        self.assertEqual(outcome.facts, ())

    def test_read_limit_stops_reads(self) -> None:
        self.shipment(["1-T", "2-T"])
        self.task("1-T")
        self.task("2-T")
        outcome, reader = self.read(limits=ReadLimits(max_files=3))
        self.assertEqual(outcome.read_limit, hs.ReadLimitHit(ReadErrorCode.FILE_COUNT_LIMIT, hs.ReadStage.MEMBER_CANDIDATE))
        self.assertEqual(reader.usage.files_claimed, 3)
        outcome, reader = self.read(limits=ReadLimits(max_file_bytes=8))
        self.assertEqual(outcome.read_limit, hs.ReadLimitHit(ReadErrorCode.FILE_SIZE_LIMIT, hs.ReadStage.SHIPMENT_CANDIDATE))
        self.assertEqual(reader.usage.files_claimed, 1)


class FirstApplicableRosterTests(unittest.TestCase):
    def test_first_applicable_orders_by_registry(self) -> None:
        self.assertEqual(
            hs._first_applicable(["DECLARATION_MISSING", "MEMBER_NOT_FOUND", "MEMBER_ID_INVALID"]), "MEMBER_ID_INVALID"
        )
        self.assertEqual(hs._first_applicable(["SURFACE_UNSUPPORTED", "DECLARATION_MIXED"]), "DECLARATION_MIXED")
        self.assertIsNone(hs._first_applicable([]))
        with self.assertRaises(KeyError):
            hs._first_applicable(["READ_BUDGET_EXHAUSTED"])


class RosterStructuralTests(unittest.TestCase):
    def test_structural_roster_markers_pairwise_distinct(self) -> None:
        names = [
            name
            for cls in (RecordsRosterTests, FirstApplicableRosterTests)
            for name in dir(cls)
            if name.startswith("test_")
        ]
        markers = [f"{MARKER}:{name}" for name in names]
        self.assertEqual(len(set(markers)), len(markers))
        self.assertFalse(any(name.startswith("test_structural_") for name in names))


if __name__ == "__main__":
    unittest.main()
