"""Tests for the read-only linked-deliberation disposition planner.

Covers the first half of plan unit U1b
(``docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md``), tasks
196.004-T..196.008-T: ``compute_linked_deliberation_disposition`` in
``src/autoharness/gates/shipment_closure.py``. Every non-read-error outcome
fixture checks ``reason_code`` through :func:`assert_reason_code_defaults`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import yaml

from autoharness.gates import shipment_closure
from autoharness.gates.shipment_closure import (
    EngineSemanticsDecision,
    LinkedDeliberationDispositionPlan,
    LinkedDeliberationOutcome,
    assess_cascade_engine_semantics,
    compute_linked_deliberation_disposition,
)

SHIPMENT_ID = "900-S"
VERIFIED = assess_cascade_engine_semantics("1.11.0", probe_surface="cli", invocation_surface="cli")
UNVERIFIED = assess_cascade_engine_semantics("1.12.0", probe_surface="cli", invocation_surface="cli")


def assert_reason_code_defaults(test: unittest.TestCase, record) -> None:
    """Every outcome except ``retained_read_error`` defaults reason_code to its value."""

    test.assertNotEqual(record.outcome, LinkedDeliberationOutcome.RETAINED_READ_ERROR)
    test.assertTrue(record.reason_code)
    test.assertEqual(record.reason_code, str(getattr(record.outcome, "value", record.outcome)))
    test.assertIsNone(record.path)


class _Backlog:
    def __init__(self, root: Path) -> None:
        self.workspace = root
        self.backlog_dir = root / ".backlogit"
        (self.backlog_dir / "queue").mkdir(parents=True)
        (self.backlog_dir / "archive").mkdir(parents=True)

    def write(
        self,
        artifact_id: str,
        artifact_type: str,
        *,
        status: str = "queued",
        folder: str = "queue",
        filename: str | None = None,
        body: str = "",
        **fields: object,
    ) -> Path:
        frontmatter: dict[str, object] = {
            "id": artifact_id,
            "artifact_type": artifact_type,
            "status": status,
        }
        frontmatter.update(fields)
        text = (
            "---\n"
            + yaml.safe_dump(frontmatter, sort_keys=True)
            + "---\n\n<!-- BEGIN:description -->\n"
            + body
            + "\n<!-- END:description -->\n"
        )
        path = self.backlog_dir / folder / (filename or f"{artifact_id}.md")
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def shipment(
        self, items: list[str], shipment_id: str = SHIPMENT_ID, status: str = "active", **kwargs
    ) -> None:
        self.write(shipment_id, "shipment", status=status, custom_fields={"items": items}, **kwargs)

    def plan(self, items: list[str], engine: EngineSemanticsDecision = VERIFIED, **kwargs):
        return compute_linked_deliberation_disposition(
            items, SHIPMENT_ID, self.backlog_dir, engine=engine, **kwargs
        )

    def stash(self, *entries: dict | str, path: Path | None = None) -> Path:
        """Write ``stash.jsonl`` lines (a dict is JSON-encoded, a str is written raw)."""

        target = path or (self.backlog_dir / "stash.jsonl")
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = [entry if isinstance(entry, str) else json.dumps(entry) for entry in entries]
        target.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="\n")
        return target


class _PlannerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.backlog = self._fresh_backlog()

    def _fresh_backlog(self) -> _Backlog:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.backlog = _Backlog(Path(tmp.name))
        return self.backlog

    def _feature_with_task(self, feature_id: str, task_id: str, **task_fields) -> list[str]:
        self.backlog.write(feature_id, "feature", status="active")
        self.backlog.write(task_id, "task", status="active", parent_id=feature_id, **task_fields)
        return [feature_id, task_id]

    def _only(self, plan: LinkedDeliberationDispositionPlan, deliberation_id: str):
        matches = [d for d in plan.dispositions if d.deliberation_id == deliberation_id]
        self.assertEqual(len(matches), 1, plan)
        return matches[0]


class DispositionPlannerSkeletonTests(_PlannerTestCase):
    """196.004-T scenarios P1-P3."""

    def test_p1_outcome_enum_is_closed_eight_values(self) -> None:
        self.assertEqual(
            [member.value for member in LinkedDeliberationOutcome],
            [
                "archived",
                "already-archived",
                "retained_read_error",
                "retained_ambiguous",
                "retained_engine_unverified",
                "retained_live_status",
                "retained_shared_reference",
                "retained_description_mention",
            ],
        )
        self.assertTrue(issubclass(LinkedDeliberationOutcome, str))

    def test_p2_queued_source_linked_deliberation_without_referrer_plans_archive(self) -> None:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": "050-DL"}
        )
        path = self.backlog.write("050-DL", "deliberation", status="queued")
        self.backlog.shipment(items)

        plan = self.backlog.plan(items)

        self.assertIsNone(plan.planning_error)
        self.assertEqual(plan.shipment_id, SHIPMENT_ID)
        self.assertIs(plan.engine, VERIFIED)
        self.assertEqual(plan.unresolved_references, ())
        record = self._only(plan, "050-DL")
        self.assertEqual(record.outcome, "archive")
        assert_reason_code_defaults(self, record)
        self.assertEqual(record.link_kinds, ("source_deliberation_id",))
        self.assertEqual(record.linking_member_ids, ("900.001-T",))
        self.assertEqual(record.declared_status, "queued")
        self.assertEqual(record.referrer_ids, ())
        self.assertEqual(len(record.records), 1)
        snapshot = record.records[0]
        self.assertEqual(snapshot.path, ".backlogit/queue/050-DL.md")
        self.assertEqual(snapshot.declared_status, "queued")
        self.assertEqual(snapshot.sha256, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_p3_unknown_id_is_unresolved_not_found(self) -> None:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": "051-DL"}
        )
        self.backlog.shipment(items)

        plan = self.backlog.plan(items)

        self.assertEqual(plan.dispositions, ())
        self.assertEqual(
            [(ref.id, ref.reason_code) for ref in plan.unresolved_references],
            [("051-DL", "not_found")],
        )

    def test_invalid_id_shape_is_unresolved_and_never_resolved(self) -> None:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": "../x-DL"}
        )
        self.backlog.shipment(items)

        plan = self.backlog.plan(items)

        self.assertEqual(plan.dispositions, ())
        self.assertEqual(
            [(ref.id, ref.reason_code) for ref in plan.unresolved_references],
            [("../x-DL", "invalid_id")],
        )

    def test_planner_is_read_only(self) -> None:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": "050-DL"}
        )
        self.backlog.write("050-DL", "deliberation")
        self.backlog.shipment(items)
        before = {
            p: p.read_bytes() for p in sorted(self.backlog.backlog_dir.rglob("*")) if p.is_file()
        }

        self.backlog.plan(items)

        after = {
            p: p.read_bytes() for p in sorted(self.backlog.backlog_dir.rglob("*")) if p.is_file()
        }
        self.assertEqual(before, after)

    def test_planner_never_raises_on_garbage_input(self) -> None:
        # A linked deliberation that a well-formed call would plan to archive,
        # so the assertions below can actually fail.
        self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": "050-DL"}
        )
        self.backlog.write("050-DL", "deliberation")
        for manifest in (None, 42):
            with self.subTest(manifest=manifest):
                plan = compute_linked_deliberation_disposition(
                    manifest, SHIPMENT_ID, self.backlog.backlog_dir, engine=VERIFIED  # type: ignore[arg-type]
                )
                self.assertIsInstance(plan, LinkedDeliberationDispositionPlan)
                self.assertIsNotNone(plan.planning_error)
                self.assertEqual(plan.dispositions, ())
        for engine in (None, "VERIFIED"):
            with self.subTest(engine=engine):
                plan = compute_linked_deliberation_disposition(
                    ["900-F", "900.001-T"], SHIPMENT_ID, self.backlog.backlog_dir, engine=engine  # type: ignore[arg-type]
                )
                self.assertIsInstance(plan, LinkedDeliberationDispositionPlan)
                self.assertFalse(any(d.outcome == "archive" for d in plan.dispositions), plan)
        plan = compute_linked_deliberation_disposition(
            [None, 7, "900-F", "900.001-T"], SHIPMENT_ID, self.backlog.backlog_dir, engine=VERIFIED  # type: ignore[list-item]
        )
        self.assertIn("ValueError", plan.planning_error or "")
        self.assertEqual(plan.dispositions, ())

    def test_any_malformed_manifest_member_rejects_the_whole_manifest(self) -> None:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": "050-DL"}
        )
        self.backlog.write("050-DL", "deliberation")
        for bad in (None, 7, "", "   ", "../../outside", "not an id"):
            with self.subTest(bad=bad):
                plan = self.backlog.plan([*items, bad])  # type: ignore[list-item]
                self.assertIsNotNone(plan.planning_error)
                self.assertEqual(plan.dispositions, ())


class DispositionLinkSourceTests(_PlannerTestCase):
    """196.005-T scenarios P4-P6."""

    def test_p4_description_only_mention_is_report_only(self) -> None:
        items = self._feature_with_task("900-F", "900.001-T", body="See 052-DL for context.")
        self.backlog.write("052-DL", "deliberation")
        self.backlog.shipment(items)

        record = self._only(self.backlog.plan(items), "052-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_DESCRIPTION_MENTION)
        assert_reason_code_defaults(self, record)
        self.assertEqual(record.link_kinds, ("description",))

    def test_references_entry_is_a_link_source(self) -> None:
        items = self._feature_with_task(
            "900-F", "900.001-T", references=["docs/decisions/x.md", "053-DL"]
        )
        self.backlog.write("053-DL", "deliberation")
        self.backlog.shipment(items)

        record = self._only(self.backlog.plan(items), "053-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_DESCRIPTION_MENTION)
        self.assertEqual(record.link_kinds, ("references",))

    def test_p5_non_deliberation_artifact_type_is_excluded(self) -> None:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": "054-DL"}
        )
        self.backlog.write("054-DL", "task", status="queued")
        self.backlog.shipment(items)

        plan = self.backlog.plan(items)

        self.assertEqual(plan.dispositions, ())
        self.assertEqual(
            [(ref.id, ref.reason_code) for ref in plan.unresolved_references],
            [("054-DL", "not_found")],
        )

    def test_p6_links_from_task_bug_and_chore_members_are_collected(self) -> None:
        self.backlog.write("055.001-T", "task", custom_fields={"source_deliberation_id": "055-DL"})
        self.backlog.write("056-B", "bug", body="Tracked in 056-DL.")
        self.backlog.write("057-C", "chore", references=["057-DL"])
        for deliberation_id in ("055-DL", "056-DL", "057-DL"):
            self.backlog.write(deliberation_id, "deliberation")
        items = ["055.001-T", "056-B", "057-C"]
        self.backlog.shipment(items)

        plan = self.backlog.plan(items)

        self.assertEqual(
            {d.deliberation_id: d.linking_member_ids for d in plan.dispositions},
            {"055-DL": ("055.001-T",), "056-DL": ("056-B",), "057-DL": ("057-C",)},
        )
        self.assertEqual(self._only(plan, "055-DL").outcome, "archive")
        for record in plan.dispositions:
            assert_reason_code_defaults(self, record)


class DispositionSetExclusionTests(_PlannerTestCase):
    """196.006-T scenarios P7-P9."""

    def test_p7_multi_feature_manifest_collects_from_every_feature(self) -> None:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": "058-DL"}
        ) + self._feature_with_task(
            "901-F", "901.001-T", custom_fields={"source_deliberation_id": "059-DL"}
        )
        self.backlog.write("058-DL", "deliberation")
        self.backlog.write("059-DL", "deliberation")
        self.backlog.shipment(items)

        plan = self.backlog.plan(items)

        self.assertEqual([d.deliberation_id for d in plan.dispositions], ["058-DL", "059-DL"])
        for record in plan.dispositions:
            self.assertEqual(record.outcome, "archive")
            assert_reason_code_defaults(self, record)

    def test_p8_self_reference_is_excluded(self) -> None:
        self.backlog.write(
            "060-DL",
            "deliberation",
            body="060-DL supersedes nothing.",
            custom_fields={"source_deliberation_id": "060-DL"},
        )
        items = ["060-DL"]
        self.backlog.shipment(items)

        plan = self.backlog.plan(items)

        self.assertEqual(plan.dispositions, ())
        self.assertEqual(plan.unresolved_references, ())

    def test_p9_explicit_member_deliberation_is_excluded(self) -> None:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": "061-DL"}
        )
        self.backlog.write("061-DL", "deliberation")
        items.append("061-DL")
        self.backlog.shipment(items)

        plan = self.backlog.plan(items)

        self.assertEqual(plan.dispositions, ())
        self.assertEqual(plan.unresolved_references, ())


class OutcomePrecedenceCoreTests(_PlannerTestCase):
    """196.007-T scenarios P10-P12 plus the H3 already-archived rule."""

    def _linked_items(self, deliberation_id: str) -> list[str]:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": deliberation_id}
        )
        self.backlog.shipment(items)
        return items

    def test_p10_torn_deliberation_is_retained_ambiguous(self) -> None:
        items = self._linked_items("062-DL")
        self.backlog.write("062-DL", "deliberation", status="queued")
        self.backlog.write("062-DL", "deliberation", status="archived", folder="archive")

        record = self._only(self.backlog.plan(items), "062-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_AMBIGUOUS)
        assert_reason_code_defaults(self, record)
        self.assertEqual(
            [snapshot.path for snapshot in record.records],
            [".backlogit/archive/062-DL.md", ".backlogit/queue/062-DL.md"],
        )
        self.assertIsNone(record.declared_status)

    def test_torn_manifest_member_is_a_planning_error_not_an_archive(self) -> None:
        # Archived copy keeps the stale link; queue copy no longer carries it.
        self.backlog.write("900-F", "feature", status="active")
        self.backlog.write("900.001-T", "task", status="active", parent_id="900-F")
        self.backlog.write(
            "900.001-T",
            "task",
            status="done",
            folder="archive",
            parent_id="900-F",
            custom_fields={"source_deliberation_id": "050-DL"},
        )
        self.backlog.write("050-DL", "deliberation", status="queued")
        items = ["900-F", "900.001-T"]
        self.backlog.shipment(items)

        plan = self.backlog.plan(items)

        self.assertEqual(plan.dispositions, ())
        self.assertIn("900.001-T", plan.planning_error or "")

    def test_p11_live_statuses_are_retained_even_without_referrer(self) -> None:
        for status in ("active", "blocked", "review"):
            with self.subTest(status=status):
                self._fresh_backlog()
                items = self._linked_items("063-DL")
                self.backlog.write("063-DL", "deliberation", status=status)

                record = self._only(self.backlog.plan(items), "063-DL")

                self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_LIVE_STATUS)
                assert_reason_code_defaults(self, record)
                self.assertEqual(record.referrer_ids, ())

    def test_non_live_statuses_plan_archive(self) -> None:
        for status in ("queued", "done", "accepted", "rejected"):
            with self.subTest(status=status):
                self._fresh_backlog()
                items = self._linked_items("064-DL")
                self.backlog.write("064-DL", "deliberation", status=status)

                record = self._only(self.backlog.plan(items), "064-DL")

                self.assertEqual(record.outcome, "archive")

    def test_h3_declared_archived_is_already_archived_regardless_of_location(self) -> None:
        for folder in ("queue", "archive"):
            with self.subTest(folder=folder):
                self._fresh_backlog()
                items = self._linked_items("065-DL")
                self.backlog.write("065-DL", "deliberation", status="archived", folder=folder)

                record = self._only(self.backlog.plan(items), "065-DL")

                self.assertIs(record.outcome, LinkedDeliberationOutcome.ALREADY_ARCHIVED)
                assert_reason_code_defaults(self, record)

    def test_h3_archive_folder_record_declaring_done_is_not_already_archived(self) -> None:
        items = self._linked_items("066-DL")
        self.backlog.write("066-DL", "deliberation", status="done", folder="archive")

        record = self._only(self.backlog.plan(items), "066-DL")

        self.assertEqual(record.outcome, "archive")

    def test_p12_engine_unverified_retains_every_non_archived_deliberation(self) -> None:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": "067-DL"}, body="067-DL? no: 068-DL"
        )
        self.backlog.write("067-DL", "deliberation", status="queued")
        self.backlog.write("068-DL", "deliberation", status="active")
        self.backlog.write("069-DL", "deliberation", status="archived")
        self.backlog.write("900.002-T", "task", parent_id="900-F", custom_fields={"source_deliberation_id": "069-DL"})
        items.append("900.002-T")
        self.backlog.shipment(items)

        for engine in (UNVERIFIED, None):
            with self.subTest(engine=engine):
                plan = self.backlog.plan(items, engine=engine)  # type: ignore[arg-type]
                for deliberation_id in ("067-DL", "068-DL"):
                    record = self._only(plan, deliberation_id)
                    self.assertIs(
                        record.outcome, LinkedDeliberationOutcome.RETAINED_ENGINE_UNVERIFIED
                    )
                    assert_reason_code_defaults(self, record)
                self.assertIs(
                    self._only(plan, "069-DL").outcome, LinkedDeliberationOutcome.ALREADY_ARCHIVED
                )


class LiveReferrerScanTests(_PlannerTestCase):
    """196.008-T scenarios P13-P15 plus counted/never-counted referrer kinds."""

    def _linked_items(self, deliberation_id: str) -> list[str]:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": deliberation_id}
        )
        self.backlog.shipment(items)
        return items

    def test_p13_deliberation_cycle_is_not_counted(self) -> None:
        items = self._linked_items("070-DL")
        self.backlog.write("070-DL", "deliberation", body="Follows up 071-DL.")
        self.backlog.write(
            "071-DL",
            "deliberation",
            body="Superseded by 070-DL.",
            custom_fields={"source_deliberation_id": "070-DL"},
        )

        record = self._only(self.backlog.plan(items), "070-DL")

        self.assertEqual(record.outcome, "archive")
        self.assertEqual(record.referrer_ids, ())

    def test_p14_other_shipment_items_referrer_is_counted(self) -> None:
        items = self._linked_items("072-DL")
        self.backlog.write("072-DL", "deliberation")
        self.backlog.shipment(["072-DL"], shipment_id="950-S", status="queued")

        record = self._only(self.backlog.plan(items), "072-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE)
        assert_reason_code_defaults(self, record)
        self.assertEqual(record.referrer_ids, ("950-S",))

    def test_p15_other_shipment_description_referrer_is_counted(self) -> None:
        items = self._linked_items("073-DL")
        self.backlog.write("073-DL", "deliberation")
        self.backlog.shipment([], shipment_id="951-S", status="queued", body="Carries 073-DL work.")

        record = self._only(self.backlog.plan(items), "073-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE)
        self.assertEqual(record.referrer_ids, ("951-S",))

    def test_other_shipment_source_deliberation_id_referrer_is_counted(self) -> None:
        items = self._linked_items("074-DL")
        self.backlog.write("074-DL", "deliberation")
        self.backlog.write(
            "952-S",
            "shipment",
            custom_fields={"items": [], "source_deliberation_id": "074-DL"},
        )

        record = self._only(self.backlog.plan(items), "074-DL")

        self.assertEqual(record.referrer_ids, ("952-S",))

    def test_out_of_scope_work_item_referrers_are_counted(self) -> None:
        items = self._linked_items("075-DL")
        self.backlog.write("075-DL", "deliberation")
        self.backlog.write("980.001-T", "task", custom_fields={"source_deliberation_id": "075-DL"})
        self.backlog.write("981-B", "bug", body="Relates to 075-DL.")
        self.backlog.write("982-C", "chore", references=["075-DL"])

        record = self._only(self.backlog.plan(items), "075-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE)
        self.assertEqual(record.referrer_ids, ("980.001-T", "981-B", "982-C"))

    def test_shared_reference_precedes_description_mention(self) -> None:
        items = self._feature_with_task("900-F", "900.001-T", body="Background: 076-DL.")
        self.backlog.shipment(items)
        self.backlog.write("076-DL", "deliberation")
        self.backlog.write("983.001-T", "task", body="Also 076-DL.")

        record = self._only(self.backlog.plan(items), "076-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE)

    def test_never_counted_referrers(self) -> None:
        items = self._linked_items("077-DL")
        self.backlog.write("077-DL", "deliberation", body="Self mention 077-DL.")
        # A manifest member is inside closure_scope(S), never a referrer.
        self.backlog.write("900.002-T", "task", body="077-DL")
        items.append("900.002-T")
        self.backlog.shipment(items)
        # Truly archived work item and shipment referrers are not counted.
        self.backlog.write(
            "984.001-T",
            "task",
            status="archived",
            folder="archive",
            custom_fields={"source_deliberation_id": "077-DL"},
        )
        self.backlog.shipment(["077-DL"], shipment_id="953-S", status="archived", folder="archive")

        record = self._only(self.backlog.plan(items), "077-DL")

        self.assertEqual(record.outcome, "archive")
        assert_reason_code_defaults(self, record)
        self.assertEqual(record.referrer_ids, ())


class TrulyArchivedReferrerTests(_PlannerTestCase):
    """197.001-T scenarios P16-P18 plus the multi-record referrer rule (H3)."""

    def _linked_items(self, deliberation_id: str) -> list[str]:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": deliberation_id}
        )
        self.backlog.shipment(items)
        return items

    def test_p16_truly_archived_referrer_is_not_counted(self) -> None:
        items = self._linked_items("100-DL")
        self.backlog.write("100-DL", "deliberation")
        self.backlog.write(
            "985.001-T",
            "task",
            status="archived",
            folder="archive",
            custom_fields={"source_deliberation_id": "100-DL"},
        )
        self.backlog.shipment(["100-DL"], shipment_id="954-S", status="archived", folder="archive")

        record = self._only(self.backlog.plan(items), "100-DL")

        self.assertEqual(record.outcome, "archive")
        assert_reason_code_defaults(self, record)
        self.assertEqual(record.referrer_ids, ())

    def test_p17_archive_folder_record_declaring_done_is_counted(self) -> None:
        items = self._linked_items("101-DL")
        self.backlog.write("101-DL", "deliberation")
        self.backlog.write(
            "986.001-T",
            "task",
            status="done",
            folder="archive",
            custom_fields={"source_deliberation_id": "101-DL"},
        )
        self.backlog.shipment(["101-DL"], shipment_id="955-S", status="shipped", folder="archive")

        record = self._only(self.backlog.plan(items), "101-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE)
        assert_reason_code_defaults(self, record)
        self.assertEqual(record.referrer_ids, ("955-S", "986.001-T"))

    def test_p18_queue_folder_record_declaring_archived_is_not_counted(self) -> None:
        items = self._linked_items("102-DL")
        self.backlog.write("102-DL", "deliberation")
        self.backlog.write(
            "987.001-T",
            "task",
            status="archived",
            folder="queue",
            custom_fields={"source_deliberation_id": "102-DL"},
        )
        self.backlog.shipment(["102-DL"], shipment_id="956-S", status="archived", folder="queue")

        record = self._only(self.backlog.plan(items), "102-DL")

        self.assertEqual(record.outcome, "archive")
        assert_reason_code_defaults(self, record)
        self.assertEqual(record.referrer_ids, ())

    def test_multi_record_referrer_counts_as_live_even_when_every_copy_declares_archived(
        self,
    ) -> None:
        # A torn referrer has no trustworthy declared status: fail closed.
        items = self._linked_items("103-DL")
        self.backlog.write("103-DL", "deliberation")
        for folder in ("queue", "archive"):
            self.backlog.write(
                "988.001-T",
                "task",
                status="archived",
                folder=folder,
                custom_fields={"source_deliberation_id": "103-DL"},
            )
            self.backlog.shipment(
                ["103-DL"], shipment_id="957-S", status="archived", folder=folder
            )

        record = self._only(self.backlog.plan(items), "103-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE)
        assert_reason_code_defaults(self, record)
        self.assertEqual(record.referrer_ids, ("957-S", "988.001-T"))

    def test_multi_record_referrer_with_one_archived_copy_still_counts(self) -> None:
        items = self._linked_items("104-DL")
        self.backlog.write("104-DL", "deliberation")
        self.backlog.write("989.001-T", "task", status="archived", folder="archive", body="104-DL")
        self.backlog.write("989.001-T", "task", status="queued", folder="queue")

        record = self._only(self.backlog.plan(items), "104-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE)
        self.assertEqual(record.referrer_ids, ("989.001-T",))


class StashReferrerTests(_PlannerTestCase):
    """197.002-T scenarios P19-P21: active stash entries are live referrers."""

    def _linked_items(self, deliberation_id: str) -> list[str]:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": deliberation_id}
        )
        self.backlog.shipment(items)
        return items

    def test_p19_stash_only_referrer_by_field_and_by_text(self) -> None:
        for form, entry in (
            ("field", {"id": "AAAA0001", "deliberation_id": "110-DL", "text": "unrelated"}),
            ("text", {"id": "AAAA0001", "text": "Follow-up from 110-DL, still open."}),
        ):
            with self.subTest(form=form):
                self._fresh_backlog()
                items = self._linked_items("110-DL")
                self.backlog.write("110-DL", "deliberation")
                self.backlog.stash({"id": "AAAA0000", "text": "no link"}, entry)

                record = self._only(self.backlog.plan(items), "110-DL")

                self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE)
                assert_reason_code_defaults(self, record)
                self.assertEqual(record.referrer_ids, ("AAAA0001",))

    def test_p20_default_call_counts_the_active_stash_entry(self) -> None:
        # The umbrella feature's own live-proof shape: a deliberation linked by
        # source_deliberation_id and cited only by one active stash entry.
        for with_entry in (True, False):
            with self.subTest(with_entry=with_entry):
                self._fresh_backlog()
                items = self._linked_items("038-DL")
                self.backlog.write("038-DL", "deliberation", status="accepted")
                if with_entry:
                    self.backlog.stash(
                        {
                            "id": "8FEE91F4",
                            "kind": "chore",
                            "deliberation_id": "038-DL",
                            "text": "Align P-015 with backlogit 1.11 (038-DL).",
                        }
                    )

                # Default call: no stash_path argument.
                plan = compute_linked_deliberation_disposition(
                    items, SHIPMENT_ID, self.backlog.backlog_dir, engine=VERIFIED
                )

                record = self._only(plan, "038-DL")
                assert_reason_code_defaults(self, record)
                if with_entry:
                    self.assertIs(
                        record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE
                    )
                    self.assertEqual(record.referrer_ids, ("8FEE91F4",))
                else:
                    self.assertEqual(record.outcome, "archive")
                    self.assertEqual(record.referrer_ids, ())

    def test_p21_absent_default_stash_file_counts_nothing_and_never_raises(self) -> None:
        items = self._linked_items("111-DL")
        self.backlog.write("111-DL", "deliberation")
        self.assertFalse((self.backlog.backlog_dir / "stash.jsonl").exists())

        plan = self.backlog.plan(items)

        self.assertIsNone(plan.planning_error)
        self.assertEqual(plan.read_failures, ())
        record = self._only(plan, "111-DL")
        self.assertEqual(record.outcome, "archive")
        assert_reason_code_defaults(self, record)

    def test_archived_stash_entries_are_never_counted(self) -> None:
        items = self._linked_items("112-DL")
        self.backlog.write("112-DL", "deliberation")
        self.backlog.stash(
            {"id": "AAAA0002", "deliberation_id": "112-DL", "text": "112-DL"},
            path=self.backlog.backlog_dir / "archive" / "stash.jsonl",
        )

        record = self._only(self.backlog.plan(items), "112-DL")

        self.assertEqual(record.outcome, "archive")
        self.assertEqual(record.referrer_ids, ())

    def test_explicit_stash_path_overrides_the_default(self) -> None:
        items = self._linked_items("113-DL")
        self.backlog.write("113-DL", "deliberation")
        self.backlog.stash({"id": "AAAA0003", "text": "default stash cites 113-DL"})
        explicit = self.backlog.stash(
            {"id": "AAAA0004", "deliberation_id": "113-DL"},
            path=self.backlog.backlog_dir / "alt" / "stash.jsonl",
        )

        record = self._only(self.backlog.plan(items, stash_path=explicit), "113-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE)
        self.assertEqual(record.referrer_ids, ("AAAA0004",))

    def test_stash_referrer_combines_with_backlog_referrers(self) -> None:
        items = self._linked_items("114-DL")
        self.backlog.write("114-DL", "deliberation")
        self.backlog.write("990.001-T", "task", body="Needs 114-DL.")
        self.backlog.stash("", {"id": "AAAA0005", "text": "Re 114-DL"}, "   ")

        record = self._only(self.backlog.plan(items), "114-DL")

        self.assertEqual(record.referrer_ids, ("990.001-T", "AAAA0005"))


class FailClosedReadPathTests(_PlannerTestCase):
    """The fail-closed read path that backs the never-raises contract.

    Any read failure retains every disposition-set deliberation as
    ``retained_read_error`` (never ``archive``) and is listed in
    ``read_failures``. Per-deliberation attribution, containment and the stash
    read errors are refined in slice 2 (197-F).
    """

    def _linked_items(self, deliberation_id: str) -> list[str]:
        items = self._feature_with_task(
            "900-F", "900.001-T", custom_fields={"source_deliberation_id": deliberation_id}
        )
        self.backlog.shipment(items)
        return items

    def _write_raw(self, folder: str, name: str, data: bytes) -> None:
        (self.backlog.backlog_dir / folder / name).write_bytes(data)

    def _assert_read_error(self, plan, deliberation_id: str, reason_code: str, path: str) -> None:
        record = self._only(plan, deliberation_id)
        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_READ_ERROR)
        self.assertEqual(record.reason_code, reason_code)
        self.assertEqual(record.path, path)
        self.assertIn((path, reason_code), [(f.path, f.reason_code) for f in plan.read_failures])

    def test_invalid_yaml_record_retains_with_malformed_frontmatter(self) -> None:
        items = self._linked_items("085-DL")
        self.backlog.write("085-DL", "deliberation")
        self._write_raw("queue", "990-T.md", b"---\nid: [unclosed\n---\nbody\n")

        self._assert_read_error(
            self.backlog.plan(items), "085-DL", "malformed_frontmatter", ".backlogit/queue/990-T.md"
        )

    def test_non_utf8_record_retains_with_unreadable_file(self) -> None:
        items = self._linked_items("086-DL")
        self.backlog.write("086-DL", "deliberation")
        self._write_raw("queue", "991-T.md", b"---\nid: 991-T\ntitle: \xff\xfe\n---\n")

        self._assert_read_error(
            self.backlog.plan(items), "086-DL", "unreadable_file", ".backlogit/queue/991-T.md"
        )

    def test_missing_closing_delimiter_retains_with_body_unseparable(self) -> None:
        items = self._linked_items("087-DL")
        self.backlog.write("087-DL", "deliberation")
        self._write_raw("queue", "992-T.md", b"---\nid: 992-T\nartifact_type: task\n")

        self._assert_read_error(
            self.backlog.plan(items), "087-DL", "body_unseparable", ".backlogit/queue/992-T.md"
        )

    def test_missing_archive_folder_is_a_read_failure_not_an_empty_scan(self) -> None:
        items = self._linked_items("088-DL")
        self.backlog.write("088-DL", "deliberation")
        (self.backlog.backlog_dir / "archive").rmdir()

        self._assert_read_error(
            self.backlog.plan(items), "088-DL", "unreadable_file", ".backlogit/archive"
        )

    def test_queue_failure_does_not_hide_archive_records(self) -> None:
        items = self._linked_items("089-DL")
        self.backlog.write("089-DL", "deliberation", status="done", folder="archive")
        self._write_raw("queue", "993-T.md", b"---\nid: [unclosed\n---\n")

        plan = self.backlog.plan(items)

        self.assertEqual(plan.unresolved_references, ())
        self._assert_read_error(plan, "089-DL", "malformed_frontmatter", ".backlogit/queue/993-T.md")

    def test_unreadable_deliberation_record_stays_visible(self) -> None:
        items = self._linked_items("094-DL")
        self._write_raw("queue", "094-DL.md", b"---\nid: [unclosed\n---\n")

        plan = self.backlog.plan(items)

        self.assertEqual(plan.dispositions, ())
        self.assertEqual(
            [(f.path, f.reason_code) for f in plan.read_failures],
            [(".backlogit/queue/094-DL.md", "malformed_frontmatter")],
        )

    def test_unconstructable_yaml_value_retains_with_malformed_frontmatter(self) -> None:
        # Valid YAML syntax whose value cannot be constructed (PyYAML raises
        # ValueError for an impossible date) must be a listed read failure,
        # not a whole-plan planning_error that loses the path.
        items = self._linked_items("090-DL")
        self.backlog.write("090-DL", "deliberation")
        self._write_raw(
            "queue", "994-T.md", b"---\nid: 994-T\nartifact_type: task\ncreated: 2026-13-45\n---\n"
        )

        plan = self.backlog.plan(items)

        self.assertIsNone(plan.planning_error)
        self._assert_read_error(plan, "090-DL", "malformed_frontmatter", ".backlogit/queue/994-T.md")

    def test_non_regular_md_entry_retains_with_unreadable_file(self) -> None:
        items = self._linked_items("091-DL")
        self.backlog.write("091-DL", "deliberation")
        (self.backlog.backlog_dir / "queue" / "995-T.md").mkdir()

        self._assert_read_error(
            self.backlog.plan(items), "091-DL", "unreadable_file", ".backlogit/queue/995-T.md"
        )

    def test_unstatable_record_retains_with_unreadable_file(self) -> None:
        # A record that cannot be stat'ed (vanished mid-scan, access denied)
        # must never silently drop out of the live-referrer scan.
        items = self._linked_items("092-DL")
        self.backlog.write("092-DL", "deliberation")
        self.backlog.write("996.001-T", "task", body="Needs 092-DL.")
        real_lstat = shipment_closure.os.lstat

        def failing_lstat(path, *args, **kwargs):
            if Path(path).name == "996.001-T.md":
                raise PermissionError("denied")
            return real_lstat(path, *args, **kwargs)

        with mock.patch.object(shipment_closure.os, "lstat", failing_lstat):
            plan = self.backlog.plan(items)

        self._assert_read_error(plan, "092-DL", "unreadable_file", ".backlogit/queue/996.001-T.md")

    def test_md_suffix_match_is_case_insensitive(self) -> None:
        # A live referrer stored with an upper-case suffix is still scanned.
        items = self._linked_items("093-DL")
        self.backlog.write("093-DL", "deliberation")
        self.backlog.write("997.001-T", "task", filename="997.001-T.MD", body="Needs 093-DL.")

        record = self._only(self.backlog.plan(items), "093-DL")

        self.assertIs(record.outcome, LinkedDeliberationOutcome.RETAINED_SHARED_REFERENCE)
        self.assertEqual(record.referrer_ids, ("997.001-T",))

    def test_crlf_record_parses_and_hashes_raw_bytes(self) -> None:
        items = self._linked_items("095-DL")
        raw = b"---\r\nid: 095-DL\r\nartifact_type: deliberation\r\nstatus: queued\r\n---\r\nbody\r\n"
        self._write_raw("queue", "095-DL.md", raw)

        record = self._only(self.backlog.plan(items), "095-DL")

        self.assertEqual(record.outcome, "archive")
        self.assertEqual(record.records[0].sha256, hashlib.sha256(raw).hexdigest())

    def test_each_record_is_read_exactly_once(self) -> None:
        items = self._linked_items("096-DL")
        self.backlog.write("096-DL", "deliberation")
        original = Path.read_bytes
        reads: list[str] = []

        def counting_read_bytes(path: Path) -> bytes:
            reads.append(path.name)
            return original(path)

        def forbidden_read_text(path: Path, *args, **kwargs) -> str:
            raise AssertionError(f"record re-read from disk: {path}")

        with mock.patch.object(Path, "read_bytes", counting_read_bytes), mock.patch.object(
            Path, "read_text", forbidden_read_text
        ):
            record = self._only(self.backlog.plan(items), "096-DL")

        self.assertEqual(record.outcome, "archive")
        self.assertEqual(sorted(reads), sorted(set(reads)))
        self.assertIn("096-DL.md", reads)

    def test_single_string_manifest_is_a_planning_error(self) -> None:
        plan = compute_linked_deliberation_disposition(
            "900-F", SHIPMENT_ID, self.backlog.backlog_dir, engine=VERIFIED
        )
        self.assertEqual(plan.dispositions, ())
        self.assertIn("TypeError", plan.planning_error or "")


if __name__ == "__main__":
    unittest.main()
