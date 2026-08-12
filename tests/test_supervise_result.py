"""Tests for autoharness.supervise.result (118.003-T)."""

from __future__ import annotations

import unittest

from autoharness.supervise.result import STATUSES, SupervisorResult


class SupervisorResultTests(unittest.TestCase):
    def test_round_trip_via_to_dict_and_from_dict(self) -> None:
        original = SupervisorResult(
            status="ok",
            exit_code=0,
            data={"key": "value", "n": 3},
            messages=("started", "finished"),
            warnings=("careful",),
            artifacts=("journal.jsonl",),
        )
        payload = original.to_dict()
        reconstructed = SupervisorResult.from_dict(payload)

        self.assertEqual(reconstructed.status, original.status)
        self.assertEqual(reconstructed.exit_code, original.exit_code)
        self.assertEqual(dict(reconstructed.data), dict(original.data))
        self.assertEqual(tuple(reconstructed.messages), tuple(original.messages))
        self.assertEqual(tuple(reconstructed.warnings), tuple(original.warnings))
        self.assertEqual(tuple(reconstructed.artifacts), tuple(original.artifacts))

    def test_to_dict_is_json_safe_plain_types(self) -> None:
        result = SupervisorResult(status="blocked", exit_code=3)
        payload = result.to_dict()

        self.assertIsInstance(payload["data"], dict)
        self.assertIsInstance(payload["messages"], list)
        self.assertIsInstance(payload["warnings"], list)
        self.assertIsInstance(payload["artifacts"], list)

    def test_defaults_are_empty_containers(self) -> None:
        result = SupervisorResult(status="ok", exit_code=0)

        self.assertEqual(dict(result.data), {})
        self.assertEqual(tuple(result.messages), ())
        self.assertEqual(tuple(result.warnings), ())
        self.assertEqual(tuple(result.artifacts), ())

    def test_invalid_status_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SupervisorResult(status="not_a_real_status", exit_code=1)

    def test_every_declared_status_is_constructible(self) -> None:
        for status in STATUSES:
            result = SupervisorResult(status=status, exit_code=0)
            self.assertEqual(result.status, status)

    def test_from_dict_tolerates_missing_optional_fields(self) -> None:
        reconstructed = SupervisorResult.from_dict({"status": "cancelled", "exit_code": 5})

        self.assertEqual(reconstructed.status, "cancelled")
        self.assertEqual(reconstructed.exit_code, 5)
        self.assertEqual(dict(reconstructed.data), {})


if __name__ == "__main__":
    unittest.main()
