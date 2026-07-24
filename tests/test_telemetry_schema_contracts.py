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


if __name__ == "__main__":
    unittest.main()
