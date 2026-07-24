"""Schema mirror tests for the telemetry contract artifacts."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from autoharness.schema_contracts import SCHEMA_CONTRACTS
from autoharness.telemetry.epoch import WorkSizingSnapshot

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXECUTION_EPOCH_ROOT = _REPO_ROOT / "schemas" / "execution-epoch.schema.json"
_EXECUTION_EPOCH_VERSIONED = (
    _REPO_ROOT / "schemas" / "execution-epoch" / "1.1.0.schema.json"
)
_TOOL_EVENT_ROOT = _REPO_ROOT / "schemas" / "tool-telemetry-event.schema.json"
_TOOL_EVENT_VERSIONED = (
    _REPO_ROOT / "schemas" / "tool-telemetry-event" / "1.0.0.schema.json"
)


def _load_schema(path: Path) -> dict[str, Any]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    return schema


def _validator(path: Path) -> Draft7Validator:
    return Draft7Validator(_load_schema(path))


def _minimal_epoch_record() -> dict[str, Any]:
    return {
        "schema_version": "1.1.0",
        "epoch_id": "0123456789abcdef0123456789abcdef",
        "task_id": "079.002-T",
        "backlog_item_id": "079.002-T",
        "timestamp": "2026-07-23T19:41:39Z",
        "route": {"models": ["gpt-5.4-mini"]},
        "economics": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_input_tokens": 0,
            "cumulative_input_tokens": 0,
            "cumulative_output_tokens": 0,
            "context_tokens_before": 0,
            "context_tokens_after": 0,
            "context_area_tokens": 0,
            "avoided_read_estimated_tokens": 0,
            "tool_output_estimated_tokens": 0,
            "cogs_usd": 0.0,
            "duration_seconds": 0.0,
            "metric_sources": {},
            "metric_quality": {},
        },
        "operations": {"cli_tools": ["git"]},
        "outcome": {"gate_exit_codes": [0]},
        "sizing": None,
    }


def _minimal_tool_event() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "event_id": "event-1",
        "epoch_id": "0123456789abcdef0123456789abcdef",
        "timestamp": "2026-07-23T19:41:39Z",
        "tool_surface": "cli",
        "server_name": None,
        "tool_name": "git",
        "operation": "status",
        "status": "success",
        "retry_count": 0,
        "degraded_mode": False,
        "sensitivity": "internal",
        "redaction_applied": False,
        "metric_sources": {},
        "metric_quality": {},
        "artifact_refs": [],
    }


def _set_path(data: dict[str, Any], dotted_path: str, value: Any) -> None:
    current: dict[str, Any] = data
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = value


class ExecutionEpochSchemaContractTests(unittest.TestCase):
    def test_execution_epoch_root_and_versioned_mirrors_match_except_id(self) -> None:
        root = _load_schema(_EXECUTION_EPOCH_ROOT)
        versioned = _load_schema(_EXECUTION_EPOCH_VERSIONED)

        self.assertTrue(root["$id"].endswith("/schemas/execution-epoch.schema.json"))
        self.assertTrue(
            versioned["$id"].endswith("/schemas/execution-epoch/1.1.0.schema.json")
        )
        root.pop("$id", None)
        versioned.pop("$id", None)
        self.assertEqual(root, versioned)

    def test_execution_epoch_registration_points_at_v1_1_schema(self) -> None:
        contract = SCHEMA_CONTRACTS["execution-epoch"]

        self.assertEqual(contract["contract_name"], "execution-epoch")
        self.assertEqual(contract["schema_file"], "execution-epoch.schema.json")
        self.assertEqual(contract["versioned_schema_dir"], "execution-epoch")
        self.assertEqual(contract["current_version"], "1.1.0")
        self.assertIn("1.1.0", contract["known_versions"])

    def test_execution_epoch_schema_const_and_required_contract(self) -> None:
        schema = _load_schema(_EXECUTION_EPOCH_ROOT)

        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.1.0")
        self.assertEqual(
            set(schema["required"]),
            {
                "schema_version",
                "epoch_id",
                "task_id",
                "backlog_item_id",
                "timestamp",
                "route",
                "economics",
                "operations",
                "outcome",
            },
        )

        validator = _validator(_EXECUTION_EPOCH_ROOT)
        valid = _minimal_epoch_record()
        self.assertEqual(list(validator.iter_errors(valid)), [])
        wrong_version = copy.deepcopy(valid)
        wrong_version["schema_version"] = "1.0.0"
        self.assertFalse(validator.is_valid(wrong_version))

    def test_execution_epoch_rejects_bad_serialized_epoch_id(self) -> None:
        validator = _validator(_EXECUTION_EPOCH_ROOT)

        for bad_id in ("", "   ", "not-a-uuid", "01234567-89ab-cdef-0123-456789abcdef"):
            record = _minimal_epoch_record()
            record["epoch_id"] = bad_id
            self.assertFalse(validator.is_valid(record), bad_id)

        missing = _minimal_epoch_record()
        del missing["epoch_id"]
        self.assertFalse(validator.is_valid(missing))

    def test_execution_epoch_numeric_quantities_are_nonnegative(self) -> None:
        validator = _validator(_EXECUTION_EPOCH_ROOT)
        nonnegative_fields = (
            "economics.input_tokens",
            "economics.output_tokens",
            "economics.cached_input_tokens",
            "economics.cumulative_input_tokens",
            "economics.cumulative_output_tokens",
            "economics.context_tokens_before",
            "economics.context_tokens_after",
            "economics.context_area_tokens",
            "economics.avoided_read_estimated_tokens",
            "economics.tool_output_estimated_tokens",
            "economics.cogs_usd",
            "economics.duration_seconds",
            "operations.routed_lookup_count",
            "operations.raw_file_read_count",
            "operations.raw_search_count",
            "operations.avoided_file_read_count",
            "operations.tool_output_bytes",
            "operations.expected_tool_count",
            "operations.observed_expected_tool_count",
            "operations.missing_expected_tool_count",
            "operations.degraded_tool_count",
            "operations.stale_or_unavailable_index_count",
            "outcome.tool_failure_count",
            "outcome.tool_degraded_count",
            "outcome.tool_gap_count",
        )

        for field in nonnegative_fields:
            record = _minimal_epoch_record()
            if field.startswith("operations."):
                record["operations"].setdefault("metric_sources", {})
                record["operations"].setdefault("metric_quality", {})
            if field.startswith("outcome."):
                record["outcome"].setdefault("metric_sources", {})
                record["outcome"].setdefault("metric_quality", {})
            _set_path(record, field, -1)
            self.assertFalse(validator.is_valid(record), field)

        signed_exit_codes = _minimal_epoch_record()
        signed_exit_codes["outcome"]["gate_exit_codes"] = [-1, 0, 2]
        self.assertTrue(validator.is_valid(signed_exit_codes))

    def test_execution_epoch_sizing_snapshot_schema_forbids_points(self) -> None:
        validator = _validator(_EXECUTION_EPOCH_ROOT)

        record = _minimal_epoch_record()
        record["sizing"] = {
            "snapshot_at": "2026-07-23T19:41:39Z",
            "snapshot_boundary": "pre_execution",
            "task_size_label": "M",
            "feature_planned_size_label": "L",
            "shipment_planned_size_label": None,
            "sizing_sources": {"task": "backlogit", "feature": "backlogit"},
            "sizing_source_revisions": {"task": "rev-1"},
            "sizing_ruleset_versions": {"task": "backlogit-1.2.3"},
            "feature_planned_child_task_count": 3,
            "feature_planned_child_size_histogram": {"M": 2, "unsized": 1},
            "feature_child_membership_hash": "a" * 64,
            "shipment_manifest_task_count": None,
            "shipment_manifest_size_histogram": {},
            "shipment_membership_hash": None,
        }
        self.assertTrue(validator.is_valid(record))

        with_points = copy.deepcopy(record)
        with_points["sizing"]["task_size_points"] = 3
        self.assertFalse(validator.is_valid(with_points))

        unavailable_bucket = copy.deepcopy(record)
        unavailable_bucket["sizing"]["feature_planned_child_size_histogram"] = {
            "M": 2,
            "unavailable": 1,
        }
        self.assertFalse(validator.is_valid(unavailable_bucket))

    def test_execution_epoch_schema_documents_null_and_provenance_semantics(self) -> None:
        schema = _load_schema(_EXECUTION_EPOCH_ROOT)
        economics = schema["properties"]["economics"]
        sizing = schema["properties"]["sizing"]["anyOf"][0]

        self.assertIn("unavailable", economics["properties"]["metric_sources"]["description"])
        self.assertIn("precision", economics["properties"]["metric_quality"]["description"])
        self.assertIn("nullable", sizing["description"].lower())
        self.assertIn("no numeric point", sizing["description"].lower())

    def test_work_sizing_snapshot_model_composition_invariants(self) -> None:
        known_ids = ["079.001-T", "079.002-T", "079.002-T", "079.003-T"]
        skipped_unresolved_ids = ["079.MISSING-T"]
        unique_known = set(known_ids)
        snapshot = WorkSizingSnapshot(
            feature_planned_child_task_count=len(unique_known),
            feature_planned_child_size_histogram={"M": 2, "unsized": 1},
            feature_child_membership_hash=WorkSizingSnapshot.membership_hash(known_ids),
        )

        self.assertEqual(snapshot.feature_planned_child_task_count, len(unique_known))
        self.assertEqual(
            snapshot.feature_planned_child_task_count,
            sum(snapshot.feature_planned_child_size_histogram.values()),
        )
        self.assertEqual(
            snapshot.feature_child_membership_hash,
            WorkSizingSnapshot.membership_hash(unique_known),
        )
        self.assertNotEqual(
            snapshot.feature_child_membership_hash,
            WorkSizingSnapshot.membership_hash([*known_ids, *skipped_unresolved_ids]),
        )
        self.assertTrue(snapshot.feature_composition_consistent())
        self.assertIsNone(WorkSizingSnapshot.membership_hash([]))


class ToolTelemetryEventSchemaContractTests(unittest.TestCase):
    def test_tool_event_root_and_versioned_mirrors_match_except_id(self) -> None:
        root = _load_schema(_TOOL_EVENT_ROOT)
        versioned = _load_schema(_TOOL_EVENT_VERSIONED)

        self.assertTrue(root["$id"].endswith("/schemas/tool-telemetry-event.schema.json"))
        self.assertTrue(
            versioned["$id"].endswith("/schemas/tool-telemetry-event/1.0.0.schema.json")
        )
        root.pop("$id", None)
        versioned.pop("$id", None)
        self.assertEqual(root, versioned)

    def test_tool_event_registration_points_at_v1_schema(self) -> None:
        contract = SCHEMA_CONTRACTS["tool-telemetry-event"]

        self.assertEqual(contract["contract_name"], "tool-telemetry-event")
        self.assertEqual(contract["schema_file"], "tool-telemetry-event.schema.json")
        self.assertEqual(contract["versioned_schema_dir"], "tool-telemetry-event")
        self.assertEqual(contract["current_version"], "1.0.0")
        self.assertIn("1.0.0", contract["known_versions"])

    def test_tool_event_const_required_and_server_name_nullable(self) -> None:
        schema = _load_schema(_TOOL_EVENT_ROOT)
        validator = _validator(_TOOL_EVENT_ROOT)

        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0.0")
        self.assertEqual(
            set(schema["required"]),
            {
                "schema_version",
                "event_id",
                "timestamp",
                "tool_surface",
                "server_name",
                "tool_name",
                "operation",
                "status",
                "retry_count",
                "degraded_mode",
                "sensitivity",
                "redaction_applied",
                "metric_sources",
                "metric_quality",
                "artifact_refs",
            },
        )
        self.assertTrue(validator.is_valid(_minimal_tool_event()))

        missing_required_nullable = _minimal_tool_event()
        del missing_required_nullable["server_name"]
        self.assertFalse(validator.is_valid(missing_required_nullable))

        wrong_version = _minimal_tool_event()
        wrong_version["schema_version"] = "1.1.0"
        self.assertFalse(validator.is_valid(wrong_version))

    def test_tool_event_identity_and_correlation_invariants(self) -> None:
        validator = _validator(_TOOL_EVENT_ROOT)

        for bad_event_id in ("", "   "):
            event = _minimal_tool_event()
            event["event_id"] = bad_event_id
            self.assertFalse(validator.is_valid(event), bad_event_id)

        epoch_only = _minimal_tool_event()
        epoch_only["backlog_item_id"] = None
        self.assertTrue(validator.is_valid(epoch_only))

        backlog_only = _minimal_tool_event()
        backlog_only["epoch_id"] = None
        backlog_only["backlog_item_id"] = "079.008-T"
        self.assertTrue(validator.is_valid(backlog_only))

        both_present = _minimal_tool_event()
        both_present["backlog_item_id"] = "079.008-T"
        self.assertTrue(validator.is_valid(both_present))

        neither = _minimal_tool_event()
        neither["epoch_id"] = None
        neither["backlog_item_id"] = None
        self.assertFalse(validator.is_valid(neither))

        for bad_value in ("", "   "):
            empty_epoch = _minimal_tool_event()
            empty_epoch["epoch_id"] = bad_value
            empty_epoch["backlog_item_id"] = None
            self.assertFalse(validator.is_valid(empty_epoch), bad_value)

            empty_backlog = _minimal_tool_event()
            empty_backlog["epoch_id"] = None
            empty_backlog["backlog_item_id"] = bad_value
            self.assertFalse(validator.is_valid(empty_backlog), bad_value)

    def test_tool_event_epoch_id_filename_safety_is_separate_from_work_ids(self) -> None:
        schema = _load_schema(_TOOL_EVENT_ROOT)
        validator = _validator(_TOOL_EVENT_ROOT)

        bad_epoch_id = _minimal_tool_event()
        bad_epoch_id["epoch_id"] = "079.008-T"
        self.assertFalse(validator.is_valid(bad_epoch_id))

        backlog_work_id = _minimal_tool_event()
        backlog_work_id["epoch_id"] = None
        backlog_work_id["backlog_item_id"] = "079.008-T"
        self.assertTrue(validator.is_valid(backlog_work_id))
        self.assertIn("task or subtask", schema["properties"]["backlog_item_id"]["description"])
        self.assertIn("never", schema["properties"]["backlog_item_id"]["description"])
        self.assertIn("filename", schema["properties"]["backlog_item_id"]["description"])

    def test_tool_event_numeric_quantities_are_nonnegative_except_exit_code(self) -> None:
        validator = _validator(_TOOL_EVENT_ROOT)
        nonnegative_fields = (
            "retry_count",
            "duration_ms",
            "input_tokens",
            "output_tokens",
            "cached_input_tokens",
            "cumulative_input_tokens",
            "cumulative_output_tokens",
            "context_tokens_before",
            "context_tokens_after",
            "context_area_tokens",
            "routed_lookup_count",
            "raw_file_read_count",
            "raw_search_count",
            "avoided_file_read_count",
            "avoided_read_bytes",
            "avoided_read_estimated_tokens",
            "tool_output_bytes",
            "tool_output_estimated_tokens",
            "result_count",
        )

        for field in nonnegative_fields:
            event = _minimal_tool_event()
            event[field] = -1
            self.assertFalse(validator.is_valid(event), field)

        signed_exit_code = _minimal_tool_event()
        signed_exit_code["exit_code"] = -1
        self.assertTrue(validator.is_valid(signed_exit_code))

    def test_tool_event_metric_fields_require_source_and_quality(self) -> None:
        validator = _validator(_TOOL_EVENT_ROOT)

        missing_quality = _minimal_tool_event()
        missing_quality["input_tokens"] = 12
        missing_quality["metric_sources"] = {"input_tokens": "host_reported"}
        self.assertFalse(validator.is_valid(missing_quality))

        complete = _minimal_tool_event()
        complete["input_tokens"] = 12
        complete["metric_sources"] = {"input_tokens": "host_reported"}
        complete["metric_quality"] = {"input_tokens": "observed"}
        self.assertTrue(validator.is_valid(complete))

    def test_tool_event_work_sizing_snapshot_uses_epoch_vocabulary(self) -> None:
        validator = _validator(_TOOL_EVENT_ROOT)

        event = _minimal_tool_event()
        event["work_sizing_snapshot"] = {
            "snapshot_at": "2026-07-23T19:41:39Z",
            "snapshot_boundary": "pre_execution",
            "task_size_label": "S",
            "feature_planned_size_label": None,
            "shipment_planned_size_label": None,
            "sizing_sources": {"task": "backlogit"},
            "sizing_source_revisions": {"task": "rev-1"},
            "sizing_ruleset_versions": {"task": "backlogit-1.2.3"},
            "feature_planned_child_task_count": 2,
            "feature_planned_child_size_histogram": {"S": 1, "unsized": 1},
            "feature_child_membership_hash": "b" * 64,
            "shipment_manifest_task_count": None,
            "shipment_manifest_size_histogram": {},
            "shipment_membership_hash": None,
        }
        self.assertTrue(validator.is_valid(event))

        with_points = copy.deepcopy(event)
        with_points["work_sizing_snapshot"]["task_size_points"] = 1
        self.assertFalse(validator.is_valid(with_points))

    def test_tool_event_route_and_freshness_extension_vocabulary(self) -> None:
        validator = _validator(_TOOL_EVENT_ROOT)

        event = _minimal_tool_event()
        event["route_kind"] = "x-custom-pack"
        event["freshness_state"] = "x-custom-freshness"
        self.assertTrue(validator.is_valid(event))

        event["route_kind"] = "custom-pack"
        self.assertFalse(validator.is_valid(event))

        event = _minimal_tool_event()
        event["freshness_state"] = "custom-freshness"
        self.assertFalse(validator.is_valid(event))

    def test_tool_event_schema_documents_forward_contract_only(self) -> None:
        schema = _load_schema(_TOOL_EVENT_ROOT)
        description = schema["description"]

        self.assertIn("forward contract only", description)
        self.assertIn("no live Python event model", description)
        self.assertIn("event emitter", description)
        self.assertIn("queryable event store", description)


if __name__ == "__main__":
    unittest.main()
