"""Expected-vs-actual tool usage gap signal tests (079.004-T)."""

from __future__ import annotations

import shutil
import sqlite3
import unittest
from pathlib import Path

from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
)
from autoharness.telemetry.gaps import (
    expected_tool_gap_rate,
    summarize_tool_gaps,
)
from autoharness.telemetry.sqlite_sink import write_epoch

_ROOT = Path(__file__).resolve().parents[1]
_TEST_OUTPUT = _ROOT / ".test-output" / "telemetry-tool-gaps"


class TelemetryToolGapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = _TEST_OUTPUT / self._testMethodName
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.db_path = self.workspace / ".autoharness" / "metrics" / "execution_epochs.db"

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_expected_engram_route_used_has_no_gap(self) -> None:
        summary = summarize_tool_gaps(
            expected_tool_counts={"engram.map_code": 1},
            observed_tool_counts={"engram.map_code": 1},
            route_kind_counts={"structural_graph": 1},
        )

        self.assertEqual(summary.operations.missing_expected_tool_count, 0)
        self.assertEqual(summary.outcome.tool_gap_count, 0)
        self.assertEqual(summary.diagnostics["stale_or_unavailable_index_count"], 0)

    def test_expected_route_missed_and_raw_read_used_counts_gap(self) -> None:
        summary = summarize_tool_gaps(
            expected_tool_counts={"engram.map_code": 1},
            observed_tool_counts={"engram.map_code": 0},
            route_kind_counts={"raw_read": 1},
            raw_file_read_count=1,
        )

        self.assertEqual(summary.operations.missing_expected_tool_counts, {"engram.map_code": 1})
        self.assertEqual(summary.operations.missing_expected_tool_count, 1)
        self.assertEqual(summary.outcome.tool_gap_count, 1)
        self.assertEqual(summary.operations.raw_file_read_count, 1)

    def test_observed_unexpected_tool_preserves_gap_invariants(self) -> None:
        """Regression (local review P3): a tool observed but never expected must
        not break gap-invariant validation of a legitimately built epoch. The
        stored and derived missing-expected maps must agree on zero-key handling.
        """
        summary = summarize_tool_gaps(
            expected_tool_counts={"engram.map_code": 1},
            observed_tool_counts={"engram.map_code": 1, "grep": 3},
        )

        self.assertTrue(summary.operations.gap_invariants_hold())
        self.assertEqual(
            summary.operations.derived_missing_expected_tool_counts(),
            dict(summary.operations.missing_expected_tool_counts),
        )

    def test_observed_expected_tool_count_excludes_unexpected_tools(self) -> None:
        """Regression (Copilot review c7): observed_expected_tool_count counts
        invocations of EXPECTED tools only. An unexpected observed tool (e.g. grep)
        must not inflate the scalar or the stored observed_tool_counts map, and the
        gap invariants must still hold.
        """
        summary = summarize_tool_gaps(
            expected_tool_counts={"engram.map_code": 1},
            observed_tool_counts={"engram.map_code": 1, "grep": 3},
        )

        self.assertEqual(summary.operations.observed_expected_tool_count, 1)
        self.assertNotIn("grep", summary.operations.observed_tool_counts)
        self.assertEqual(dict(summary.operations.observed_tool_counts), {"engram.map_code": 1})
        self.assertTrue(summary.operations.gap_invariants_hold())

    def test_stale_route_fallback_with_expected_tool_invoked_is_diagnostic_only(self) -> None:
        summary = summarize_tool_gaps(
            expected_tool_counts={"engram.map_code": 1},
            observed_tool_counts={"engram.map_code": 1},
            route_kind_counts={"structural_graph": 1, "raw_search": 1},
            raw_search_count=1,
            degraded_tool_count=1,
            stale_or_unavailable_index_count=1,
        )

        self.assertEqual(summary.operations.missing_expected_tool_count, 0)
        self.assertEqual(summary.outcome.tool_gap_count, 0)
        self.assertEqual(summary.operations.degraded_tool_count, 1)
        self.assertEqual(summary.operations.stale_or_unavailable_index_count, 1)
        self.assertEqual(summary.outcome.tool_degraded_count, 0)

    def test_expected_but_no_tool_invoked_counts_gap_without_event_stream(self) -> None:
        summary = summarize_tool_gaps(
            expected_tool_counts={"engram.map_code": 1},
            observed_tool_counts={},
        )

        self.assertEqual(summary.operations.observed_expected_tool_count, 0)
        self.assertEqual(summary.operations.missing_expected_tool_counts, {"engram.map_code": 1})
        self.assertEqual(summary.outcome.tool_gap_count, 1)

    def test_no_expected_route_has_no_gap_even_with_raw_read(self) -> None:
        summary = summarize_tool_gaps(
            expected_tool_counts={},
            observed_tool_counts={},
            route_kind_counts={"raw_read": 1},
            raw_file_read_count=1,
        )

        self.assertEqual(summary.operations.expected_tool_count, 0)
        self.assertEqual(summary.operations.missing_expected_tool_count, 0)
        self.assertEqual(summary.outcome.tool_gap_count, 0)

    def test_per_tool_gap_rate_is_deterministic(self) -> None:
        self.assertEqual(expected_tool_gap_rate("engram.map_code", {"engram.map_code": 4}, {"engram.map_code": 1}), 0.25)
        self.assertIsNone(expected_tool_gap_rate("engram.map_code", {}, {}))

    def test_gap_rollups_are_queryable_from_persisted_epoch_data(self) -> None:
        summary = summarize_tool_gaps(
            expected_tool_counts={"engram.map_code": 2},
            observed_tool_counts={"engram.map_code": 1},
            route_kind_counts={"structural_graph": 1, "raw_read": 1},
            raw_file_read_count=1,
        )
        epoch = ExecutionEpoch(
            epoch_id="aaaaaaaaaaaa4aaa8aaaaaaaaaaaaaaa",
            task_id="079.004-T",
            route=RouteConfiguration(route_kinds=("structural_graph", "raw_read")),
            economics=EconomicPayload(),
            operations=summary.operations,
            outcome=summary.outcome,
        )
        write_epoch(epoch, self.db_path)

        conn = sqlite3.connect(str(self.db_path))
        try:
            row = conn.execute(
                "SELECT missing_expected_tool_count, expected_tool_counts, "
                "missing_expected_tool_counts, route_kind_counts, tool_gap_count "
                "FROM execution_epochs WHERE epoch_id=?",
                (epoch.epoch_id,),
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(row[0], 1)
        self.assertIn("engram.map_code", row[1])
        self.assertIn("raw_read", row[3])
        self.assertEqual(row[4], 1)


if __name__ == "__main__":
    unittest.main()
