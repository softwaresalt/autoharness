"""Tests for the ExecutionEpoch model + four payload classes (U1, task 051.001)."""

from __future__ import annotations

import dataclasses
import unittest

from autoharness.telemetry.epoch import (
    SCHEMA_VERSION,
    AbsoluteOutcome,
    EconomicPayload,
    EpochError,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
    WorkSizingSnapshot,
)


def _full_epoch() -> ExecutionEpoch:
    return ExecutionEpoch(
        task_id="051.001-T",
        route=RouteConfiguration(models=("claude-opus-4.6", "gpt-5.4-mini")),
        economics=EconomicPayload(
            input_tokens=1200,
            output_tokens=800,
            cogs_usd=0.042,
            duration_seconds=93.5,
            metric_sources={
                "input_tokens": "host",
                "output_tokens": "host",
                "cogs_usd": "host",
                "duration_seconds": "host",
            },
            metric_quality={
                "input_tokens": "observed",
                "output_tokens": "observed",
                "cogs_usd": "observed",
                "duration_seconds": "observed",
            },
        ),
        operations=OperationalReality(cli_tools=("git", "pytest", "backlogit")),
        outcome=AbsoluteOutcome(gate_exit_codes=(0, 0, 1)),
    )


class ExecutionEpochTests(unittest.TestCase):
    def test_full_epoch_serializes_all_four_payload_classes(self) -> None:
        epoch = _full_epoch()
        record = epoch.to_record()

        self.assertEqual(record["task_id"], "051.001-T")
        self.assertEqual(record["route"]["models"], ["claude-opus-4.6", "gpt-5.4-mini"])
        self.assertEqual(record["economics"]["input_tokens"], 1200)
        self.assertEqual(record["economics"]["output_tokens"], 800)
        self.assertAlmostEqual(record["economics"]["cogs_usd"], 0.042)
        self.assertAlmostEqual(record["economics"]["duration_seconds"], 93.5)
        self.assertEqual(record["operations"]["cli_tools"], ["git", "pytest", "backlogit"])
        self.assertEqual(record["outcome"]["gate_exit_codes"], [0, 0, 1])
        self.assertEqual(record["schema_version"], "1.1.0")
        self.assertTrue(record["epoch_id"])
        self.assertTrue(record["timestamp"])

    def test_derived_payload_properties(self) -> None:
        epoch = _full_epoch()
        self.assertEqual(epoch.route.primary_model, "claude-opus-4.6")
        self.assertEqual(epoch.economics.total_tokens, 2000)
        self.assertTrue(epoch.outcome.blocked)
        self.assertFalse(AbsoluteOutcome(gate_exit_codes=(0, 0)).blocked)

    def test_round_trip_to_record_and_from_mapping(self) -> None:
        epoch = _full_epoch()
        rebuilt = ExecutionEpoch.from_mapping(epoch.to_record())
        self.assertEqual(rebuilt.to_record(), epoch.to_record())
        self.assertEqual(rebuilt.epoch_id, epoch.epoch_id)
        self.assertEqual(rebuilt.timestamp, epoch.timestamp)

    def test_missing_required_payload_class_raises(self) -> None:
        record = _full_epoch().to_record()
        del record["outcome"]
        with self.assertRaises(EpochError):
            ExecutionEpoch.from_mapping(record)

    def test_missing_task_id_raises(self) -> None:
        record = _full_epoch().to_record()
        del record["task_id"]
        with self.assertRaises(EpochError):
            ExecutionEpoch.from_mapping(record)

    def test_wrong_payload_type_raises_on_construction(self) -> None:
        with self.assertRaises(EpochError):
            ExecutionEpoch(
                task_id="x",
                route={"models": []},  # type: ignore[arg-type]
                economics=EconomicPayload(),
                operations=OperationalReality(),
                outcome=AbsoluteOutcome(),
            )


class ExecutionEpochV11Tests(unittest.TestCase):
    def test_schema_version_is_1_1_0(self) -> None:
        self.assertEqual(SCHEMA_VERSION, "1.1.0")
        self.assertEqual(_full_epoch().schema_version, "1.1.0")
        # The version is a module-level constant / dataclass default, not a class attr.
        self.assertFalse(hasattr(ExecutionEpoch, "SCHEMA_VERSION"))

    def test_economics_additive_v11_fields_round_trip(self) -> None:
        names = (
            "input_tokens", "output_tokens", "cached_input_tokens",
            "cumulative_input_tokens", "cumulative_output_tokens",
            "context_tokens_before", "context_tokens_after", "context_area_tokens",
            "avoided_read_estimated_tokens", "tool_output_estimated_tokens",
        )
        econ = EconomicPayload(
            input_tokens=100, output_tokens=40, cached_input_tokens=25,
            cumulative_input_tokens=9000, cumulative_output_tokens=3000,
            context_tokens_before=12000, context_tokens_after=12800,
            context_area_tokens=24000, avoided_read_estimated_tokens=1500,
            tool_output_estimated_tokens=600,
            metric_sources={n: "host" for n in names},
            metric_quality={n: "observed" for n in names},
        )
        d = econ.to_dict()
        self.assertEqual(d["cached_input_tokens"], 25)
        self.assertEqual(d["context_area_tokens"], 24000)
        self.assertEqual(d["avoided_read_estimated_tokens"], 1500)
        self.assertEqual(EconomicPayload.from_mapping(d), econ)

    def test_generation_stays_separate_from_consumption(self) -> None:
        d = _full_epoch().economics.to_dict()
        # generation and consumption are distinct keys, never collapsed into a lone total.
        self.assertIn("input_tokens", d)
        self.assertIn("output_tokens", d)
        self.assertIn("cumulative_input_tokens", d)
        self.assertIn("cumulative_output_tokens", d)
        self.assertNotIn("total_tokens", d)

    def test_missing_provenance_flags_populated_metrics(self) -> None:
        econ = EconomicPayload(input_tokens=10, output_tokens=5)  # no provenance supplied
        self.assertEqual(set(econ.missing_provenance()), {"input_tokens", "output_tokens"})
        self.assertFalse(econ.has_complete_provenance)

    def test_complete_provenance_passes(self) -> None:
        econ = _full_epoch().economics
        self.assertEqual(econ.missing_provenance(), ())
        self.assertTrue(econ.has_complete_provenance)

    def test_zero_metrics_need_no_provenance(self) -> None:
        self.assertEqual(EconomicPayload().missing_provenance(), ())

    def test_cumulative_totals_preserved_not_rederived(self) -> None:
        names = ("input_tokens", "output_tokens", "cumulative_input_tokens", "cumulative_output_tokens")
        econ = EconomicPayload(
            input_tokens=100, output_tokens=40,
            cumulative_input_tokens=999999, cumulative_output_tokens=888888,
            metric_sources={n: "host" for n in names},
            metric_quality={n: "observed" for n in names},
        )
        rebuilt = EconomicPayload.from_mapping(econ.to_dict())
        self.assertEqual(rebuilt.cumulative_input_tokens, 999999)
        self.assertEqual(rebuilt.cumulative_output_tokens, 888888)
        # host-supplied cumulative totals are preserved, never summed from per-turn tokens.
        self.assertNotEqual(rebuilt.cumulative_input_tokens, rebuilt.input_tokens)

    def test_correlation_fields_round_trip(self) -> None:
        epoch = ExecutionEpoch(
            task_id="079.001-T",
            route=RouteConfiguration(),
            economics=EconomicPayload(),
            operations=OperationalReality(),
            outcome=AbsoluteOutcome(gate_exit_codes=(0,)),
            workspace_id="ws1", session_id="s1", agent_role="ship", phase="build",
            feature_id="079-F", shipment_id="092-S",
            branch="feat/079-telemetry-metrics-core", commit_sha="abc123",
        )
        rec = epoch.to_record()
        expected = {
            "workspace_id": "ws1", "session_id": "s1", "agent_role": "ship",
            "phase": "build", "feature_id": "079-F", "shipment_id": "092-S",
            "branch": "feat/079-telemetry-metrics-core", "commit_sha": "abc123",
            "backlog_item_id": "079.001-T",
        }
        for key, value in expected.items():
            self.assertEqual(rec[key], value)
        self.assertEqual(ExecutionEpoch.from_mapping(rec).to_record(), rec)

    def test_backlog_item_id_defaults_to_task_id(self) -> None:
        epoch = ExecutionEpoch(
            task_id="079.002-T", route=RouteConfiguration(), economics=EconomicPayload(),
            operations=OperationalReality(), outcome=AbsoluteOutcome(),
        )
        self.assertEqual(epoch.backlog_item_id, "079.002-T")

    def test_legacy_v1_0_record_normalizes_to_v1_1(self) -> None:
        legacy = {
            "epoch_id": "abc", "schema_version": "1.0.0", "task_id": "051.001-T",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "route": {"models": ["m"]},
            "economics": {"input_tokens": 100, "output_tokens": 50, "cogs_usd": 0.01, "duration_seconds": 12.0},
            "operations": {"cli_tools": ["git"]},
            "outcome": {"gate_exit_codes": [0]},
        }
        epoch = ExecutionEpoch.from_mapping(legacy)
        self.assertEqual(epoch.schema_version, "1.1.0")  # normalized, never a hybrid 1.0.0 record
        self.assertEqual(epoch.backlog_item_id, "051.001-T")  # copied from task_id
        for name in ("input_tokens", "output_tokens", "cogs_usd", "duration_seconds",
                     "cached_input_tokens", "context_area_tokens"):
            self.assertEqual(epoch.economics.metric_quality[name], "unavailable")
            self.assertEqual(epoch.economics.metric_sources[name], "unavailable")
        # observed values are retained even though provenance cannot be established.
        self.assertEqual(epoch.economics.input_tokens, 100)
        self.assertEqual(epoch.to_record()["schema_version"], "1.1.0")

    def test_empty_epoch_id_rejected_not_silently_replaced(self) -> None:
        rec = _full_epoch().to_record()
        rec["epoch_id"] = "   "
        with self.assertRaises(EpochError):
            ExecutionEpoch.from_mapping(rec)

    def test_sizing_snapshot_attaches_and_round_trips(self) -> None:
        snap = WorkSizingSnapshot(
            snapshot_at="2026-07-15T00:00:00+00:00",
            task_size_label="M", feature_planned_size_label="L",
            shipment_planned_size_label="XL",
            sizing_sources={"task": "backlogit", "feature": "backlogit", "shipment": "backlogit"},
            feature_planned_child_task_count=3,
            feature_planned_child_size_histogram={"M": 2, "unsized": 1},
            feature_child_membership_hash=WorkSizingSnapshot.membership_hash(
                ["079.001-T", "079.002-T", "079.003-T"]
            ),
        )
        epoch = ExecutionEpoch(
            task_id="079.001-T", route=RouteConfiguration(), economics=EconomicPayload(),
            operations=OperationalReality(), outcome=AbsoluteOutcome(), sizing=snap,
        )
        rec = epoch.to_record()
        self.assertEqual(rec["sizing"]["task_size_label"], "M")
        self.assertEqual(rec["sizing"]["snapshot_boundary"], "pre_execution")
        self.assertEqual(ExecutionEpoch.from_mapping(rec).to_record(), rec)

    def test_sizing_absent_serializes_null(self) -> None:
        self.assertIsNone(_full_epoch().to_record()["sizing"])

    def test_bad_sizing_type_rejected(self) -> None:
        with self.assertRaises(EpochError):
            ExecutionEpoch(
                task_id="x", route=RouteConfiguration(), economics=EconomicPayload(),
                operations=OperationalReality(), outcome=AbsoluteOutcome(),
                sizing={"task_size_label": "M"},  # type: ignore[arg-type]
            )


class WorkSizingSnapshotTests(unittest.TestCase):
    def test_defaults_are_pre_execution_and_nullable(self) -> None:
        snap = WorkSizingSnapshot()
        self.assertEqual(snap.snapshot_boundary, "pre_execution")
        self.assertIsNone(snap.snapshot_at)
        self.assertIsNone(snap.task_size_label)
        self.assertIsNone(snap.feature_planned_child_task_count)

    def test_invalid_size_label_rejected(self) -> None:
        with self.assertRaises(EpochError):
            WorkSizingSnapshot(task_size_label="HUGE")
        with self.assertRaises(EpochError):
            WorkSizingSnapshot(shipment_planned_size_label="0")

    def test_valid_ordinal_labels_accepted(self) -> None:
        for label in ("XS", "S", "M", "L", "XL"):
            self.assertEqual(WorkSizingSnapshot(task_size_label=label).task_size_label, label)

    def test_no_numeric_point_fields_exist(self) -> None:
        names = {f.name for f in dataclasses.fields(WorkSizingSnapshot)}
        self.assertFalse(any("point" in n or "weight" in n for n in names))

    def test_no_implicit_label_to_point_mapping(self) -> None:
        self.assertFalse(hasattr(WorkSizingSnapshot, "LABEL_POINTS"))
        self.assertFalse(hasattr(WorkSizingSnapshot, "label_to_points"))

    def test_histogram_rejects_unavailable_bucket(self) -> None:
        # Acceptance criterion: there is NO 'unavailable' histogram bucket.
        with self.assertRaises(EpochError):
            WorkSizingSnapshot(feature_planned_child_size_histogram={"unavailable": 2})
        with self.assertRaises(EpochError):
            WorkSizingSnapshot(shipment_manifest_size_histogram={"unavailable": 1})

    def test_histogram_allows_unsized_bucket(self) -> None:
        snap = WorkSizingSnapshot(
            feature_planned_child_task_count=3,
            feature_planned_child_size_histogram={"M": 2, "unsized": 1},
        )
        self.assertTrue(snap.feature_composition_consistent())

    def test_feature_count_equals_histogram_sum_including_unsized(self) -> None:
        good = WorkSizingSnapshot(
            feature_planned_child_task_count=4,
            feature_planned_child_size_histogram={"S": 1, "M": 2, "unsized": 1},
        )
        self.assertTrue(good.feature_composition_consistent())
        bad = WorkSizingSnapshot(
            feature_planned_child_task_count=5,
            feature_planned_child_size_histogram={"S": 1, "M": 2, "unsized": 1},
        )
        self.assertFalse(bad.feature_composition_consistent())

    def test_shipment_count_equals_histogram_sum(self) -> None:
        good = WorkSizingSnapshot(
            shipment_manifest_task_count=2,
            shipment_manifest_size_histogram={"M": 1, "L": 1},
        )
        self.assertTrue(good.shipment_composition_consistent())
        bad = WorkSizingSnapshot(
            shipment_manifest_task_count=3,
            shipment_manifest_size_histogram={"M": 1, "L": 1},
        )
        self.assertFalse(bad.shipment_composition_consistent())

    def test_unknown_membership_is_vacuously_consistent(self) -> None:
        snap = WorkSizingSnapshot()  # counts are None
        self.assertTrue(snap.feature_composition_consistent())
        self.assertTrue(snap.shipment_composition_consistent())

    def test_membership_hash_deterministic_and_collapses_duplicates(self) -> None:
        h1 = WorkSizingSnapshot.membership_hash(["b", "a", "a"])
        h2 = WorkSizingSnapshot.membership_hash(["a", "b"])
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)
        self.assertEqual(h1, h1.lower())

    def test_membership_hash_empty_is_none(self) -> None:
        self.assertIsNone(WorkSizingSnapshot.membership_hash([]))

    def test_snapshot_round_trips_through_mapping(self) -> None:
        snap = WorkSizingSnapshot(
            task_size_label="S",
            shipment_manifest_task_count=2,
            shipment_manifest_size_histogram={"S": 1, "unsized": 1},
            shipment_membership_hash=WorkSizingSnapshot.membership_hash(["a", "b"]),
        )
        self.assertEqual(WorkSizingSnapshot.from_mapping(snap.to_dict()), snap)


if __name__ == "__main__":
    unittest.main()
