"""Tests for the eval frozen-state execution loop (055.005-T, U8 sub-unit).

Scope: execute matrix-loaded runs against a frozen git state through an
injectable runner (no live model), and persist one comparable ExecutionEpoch
per model config via the shipped SQLite sink.
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from autoharness.eval.matrix import FrozenState, ModelConfig, load_matrix
from autoharness.eval.runner import (
    EvalRunOutcome,
    ResolvedFrozenState,
    replay_runner,
    resolve_frozen_state,
    run_matrix,
)
from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    OperationalReality,
)

_MATRIX = {
    "frozen_state": {"base": "main", "head": "HEAD"},
    "configs": [
        {
            "name": "opus",
            "models": ["claude-opus-4.6"],
            "baseline": {
                "economics": {"input_tokens": 1200, "output_tokens": 800, "cogs_usd": 0.05, "duration_seconds": 90.0},
                "operations": {"cli_tools": ["git", "pytest"]},
                "outcome": {"gate_exit_codes": [0]},
            },
        },
        {"name": "sonnet", "models": ["claude-sonnet-4.5"]},  # no baseline -> zeros
    ],
}


def _disabled_config() -> TelemetryConfig:
    return TelemetryConfig()


def _sqlite_config(db_path: Path) -> TelemetryConfig:
    return TelemetryConfig(enabled=True, mode="sqlite", database_path=db_path, emit_jsonl=False)


class ReplayRunnerTests(unittest.TestCase):
    def test_replays_recorded_baseline_without_models(self) -> None:
        config = ModelConfig(
            name="c",
            models=("m",),
            baseline={"economics": {"input_tokens": 10, "output_tokens": 5}},
        )
        outcome = replay_runner(config, None)
        self.assertIsInstance(outcome, EvalRunOutcome)
        self.assertEqual(outcome.economics.input_tokens, 10)
        self.assertEqual(outcome.economics.output_tokens, 5)

    def test_absent_baseline_yields_zero_economics(self) -> None:
        config = ModelConfig(name="c", models=("m",), baseline=None)
        outcome = replay_runner(config, None)
        self.assertEqual(outcome.economics.total_tokens, 0)
        self.assertEqual(outcome.operations.cli_tools, ())
        self.assertEqual(outcome.outcome.gate_exit_codes, ())


class ResolveFrozenStateTests(unittest.TestCase):
    def test_pins_sha_via_injected_git_runner(self) -> None:
        def fake_git(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            self.assertEqual(argv[:2], ["git", "rev-parse"])
            return 0, "abc123def456\n", ""

        resolved = resolve_frozen_state(FrozenState(base="main", head="HEAD"), git_runner=fake_git)
        assert resolved is not None
        self.assertEqual(resolved.base, "main")
        self.assertEqual(resolved.head, "HEAD")
        self.assertEqual(resolved.resolved_sha, "abc123def456")

    def test_degrades_to_none_sha_when_git_missing(self) -> None:
        def missing_git(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            raise FileNotFoundError("git")

        resolved = resolve_frozen_state(FrozenState(base="main"), git_runner=missing_git)
        assert resolved is not None
        self.assertIsNone(resolved.resolved_sha)

    def test_no_base_available_yields_none(self) -> None:
        self.assertIsNone(resolve_frozen_state(None))

    def test_base_override_takes_precedence(self) -> None:
        def fake_git(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            return 0, "sha\n", ""

        resolved = resolve_frozen_state(
            FrozenState(base="main"), base_override="release", git_runner=fake_git
        )
        assert resolved is not None
        self.assertEqual(resolved.base, "release")


class RunMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = Path(self._tmp.name) / "metrics" / "execution_epochs.db"

    def _no_git(self):
        def missing(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            raise FileNotFoundError("git")

        return missing

    def test_one_epoch_per_config_with_route_and_task_id(self) -> None:
        matrix = load_matrix(_MATRIX)
        report = run_matrix(matrix, _disabled_config(), git_runner=self._no_git())
        self.assertEqual(len(report.runs), 2)
        self.assertEqual([r.config_name for r in report.runs], ["opus", "sonnet"])
        opus = report.runs[0].epoch
        self.assertEqual(opus.task_id, "eval:opus")
        self.assertEqual(opus.route.models, ("claude-opus-4.6",))
        self.assertEqual(opus.economics.input_tokens, 1200)
        self.assertEqual(report.runs[1].epoch.economics.total_tokens, 0)

    def test_persists_one_row_per_config_to_sqlite(self) -> None:
        matrix = load_matrix(_MATRIX)
        report = run_matrix(matrix, _sqlite_config(self.db_path), git_runner=self._no_git())
        self.assertTrue(self.db_path.exists())
        conn = sqlite3.connect(str(self.db_path))
        try:
            count = conn.execute("SELECT COUNT(*) FROM execution_epochs").fetchone()[0]
            models = {
                row[0]
                for row in conn.execute("SELECT primary_model FROM execution_epochs").fetchall()
            }
        finally:
            conn.close()
        self.assertEqual(count, 2)
        self.assertEqual(models, {"claude-opus-4.6", "claude-sonnet-4.5"})
        self.assertTrue(all(r.record.sqlite_written for r in report.runs))

    def test_disabled_telemetry_runs_but_persists_nothing(self) -> None:
        matrix = load_matrix(_MATRIX)
        report = run_matrix(matrix, _disabled_config(), git_runner=self._no_git())
        self.assertEqual(len(report.runs), 2)
        self.assertFalse(self.db_path.exists())
        self.assertFalse(any(r.record.enabled for r in report.runs))

    def test_injected_runner_is_used(self) -> None:
        def custom_runner(config: ModelConfig, frozen: ResolvedFrozenState | None) -> EvalRunOutcome:
            return EvalRunOutcome(
                economics=EconomicPayload(input_tokens=7),
                operations=OperationalReality(cli_tools=("custom",)),
                outcome=AbsoluteOutcome(gate_exit_codes=(0,)),
            )

        matrix = load_matrix(_MATRIX)
        report = run_matrix(
            matrix, _disabled_config(), runner=custom_runner, git_runner=self._no_git()
        )
        self.assertTrue(all(r.epoch.economics.input_tokens == 7 for r in report.runs))

    def test_report_exposes_epochs_helper(self) -> None:
        matrix = load_matrix(_MATRIX)
        report = run_matrix(matrix, _disabled_config(), git_runner=self._no_git())
        self.assertEqual(len(report.epochs), 2)


if __name__ == "__main__":
    unittest.main()
