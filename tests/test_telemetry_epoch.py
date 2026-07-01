"""Tests for the ExecutionEpoch model + four payload classes (U1, task 051.001)."""

from __future__ import annotations

import unittest

from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    EpochError,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
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
        self.assertEqual(record["schema_version"], "1.0.0")
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


if __name__ == "__main__":
    unittest.main()
