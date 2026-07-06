"""Tests for gate policy enforcement + correction report (feature 050.008).

Covers advisory warn-not-block, the repeated-failure circuit breaker (block +
requeue + checkpoint on the 3rd consecutive failure), the audited operator
``--force`` bypass, and the per-file correction report enumerating exit codes
and stderr.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from autoharness.gates.config import GatePolicy
from autoharness.gates.feedback import build_correction_report, enforce
from autoharness.gates.gate import GateCheckReport
from autoharness.gates.runner import GateResult


def _result(file: str, exit_code: int | None, *, enforcement: str | None = None, stderr: str = "") -> GateResult:
    return GateResult(
        file=file,
        pattern="docs/**/*.md",
        command="check {file_path}",
        exit_code=exit_code,
        stderr=stderr,
        duration=0.01,
        enforcement=enforcement,
    )


def _report(*results: GateResult) -> GateCheckReport:
    return GateCheckReport(
        results=tuple(results),
        matched_files=tuple(r.file for r in results),
        discovered_files=tuple(r.file for r in results),
    )


_FIXED = datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc)


def _clock():
    return _FIXED


class AdvisoryTests(unittest.TestCase):
    def test_advisory_policy_warns_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _report(_result("docs/a.md", 1, stderr="lint error"))
            outcome = enforce(
                report,
                GatePolicy(enforcement="advisory"),
                task_id="050.008",
                workspace=tmp,
                clock=_clock,
            )
            self.assertEqual(outcome.exit_code, 0)
            self.assertFalse(outcome.blocked)
            self.assertEqual(outcome.status, "advisory")

    def test_per_gate_advisory_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Block policy is absolute, but the failing gate itself is advisory.
            report = _report(_result("docs/a.md", 1, enforcement="advisory"))
            outcome = enforce(report, GatePolicy(enforcement="absolute"), workspace=tmp, clock=_clock)
            self.assertEqual(outcome.exit_code, 0)
            self.assertFalse(outcome.blocked)

    def test_all_pass_is_passed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _report(_result("docs/a.md", 0))
            outcome = enforce(report, GatePolicy(), workspace=tmp, clock=_clock)
            self.assertEqual(outcome.status, "passed")
            self.assertEqual(outcome.exit_code, 0)


class CircuitBreakerTests(unittest.TestCase):
    def test_third_consecutive_failure_requeues_and_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _report(_result("docs/a.md", 1, stderr="boom"))
            policy = GatePolicy(enforcement="absolute", on_repeated_failure="block", max_gate_failures=3)

            first = enforce(report, policy, task_id="050.008", workspace=tmp, clock=_clock)
            self.assertEqual(first.status, "blocked")
            self.assertEqual(first.exit_code, 1)
            self.assertFalse(first.requeue)

            second = enforce(report, policy, task_id="050.008", workspace=tmp, clock=_clock)
            self.assertEqual(second.consecutive_failures, 2)
            self.assertFalse(second.requeue)

            third = enforce(report, policy, task_id="050.008", workspace=tmp, clock=_clock)
            self.assertEqual(third.status, "blocked-requeue")
            self.assertTrue(third.requeue)
            self.assertEqual(third.exit_code, 1)
            self.assertIsNotNone(third.checkpoint_path)
            self.assertTrue(Path(third.checkpoint_path).exists())
            content = Path(third.checkpoint_path).read_text(encoding="utf-8")
            self.assertIn("circuit-breaker", content)
            self.assertIn("docs/a.md", content)

    def test_pass_resets_consecutive_counter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = GatePolicy(max_gate_failures=3)
            fail = _report(_result("docs/a.md", 1))
            enforce(fail, policy, task_id="t", workspace=tmp, clock=_clock)
            enforce(fail, policy, task_id="t", workspace=tmp, clock=_clock)
            # A pass resets the counter.
            enforce(_report(_result("docs/a.md", 0)), policy, task_id="t", workspace=tmp, clock=_clock)
            after = enforce(fail, policy, task_id="t", workspace=tmp, clock=_clock)
            self.assertEqual(after.consecutive_failures, 1)
            self.assertFalse(after.requeue)

    def test_escalate_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _report(_result("docs/a.md", 1))
            policy = GatePolicy(on_repeated_failure="escalate", max_gate_failures=1)
            outcome = enforce(report, policy, task_id="t", workspace=tmp, clock=_clock)
            self.assertEqual(outcome.status, "escalate")
            self.assertTrue(outcome.escalate)
            self.assertEqual(outcome.exit_code, 1)


class ForceBypassTests(unittest.TestCase):
    def test_force_bypasses_and_audits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _report(_result("docs/a.md", 1, stderr="boom"))
            outcome = enforce(
                report,
                GatePolicy(enforcement="absolute"),
                task_id="050.008",
                workspace=tmp,
                force=True,
                clock=_clock,
            )
            self.assertEqual(outcome.status, "forced")
            self.assertEqual(outcome.exit_code, 0)
            self.assertTrue(outcome.forced)
            self.assertFalse(outcome.blocked)
            audit = Path(tmp) / ".autoharness" / "gates" / "gate-force-audit.log"
            self.assertTrue(audit.exists())
            text = audit.read_text(encoding="utf-8")
            self.assertIn("FORCE_BYPASS", text)
            self.assertIn("050.008", text)


class CorrectionReportTests(unittest.TestCase):
    def test_report_enumerates_each_file_exit_and_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _report(
                _result("docs/a.md", 0),
                _result("docs/b.md", 2, stderr="line one\nline two"),
            )
            outcome = enforce(report, GatePolicy(), task_id="t", workspace=tmp, clock=_clock)
            text = build_correction_report(report, outcome)
            self.assertIn("docs/a.md", text)
            self.assertIn("[PASS]", text)
            self.assertIn("[FAIL]", text)
            self.assertIn("exit=2", text)
            self.assertIn("line one", text)
            self.assertIn("line two", text)

    def test_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _report(_result("docs/b.md", 2, stderr="boom"))
            outcome = enforce(report, GatePolicy(), task_id="t", workspace=tmp, clock=_clock)
            import json

            payload = json.loads(build_correction_report(report, outcome, emit_json=True))
            self.assertEqual(payload["status"], outcome.status)
            self.assertEqual(payload["results"][0]["exit_code"], 2)
            self.assertEqual(payload["results"][0]["stderr"], "boom")
            self.assertEqual(
                payload["repeated_failure"],
                {
                    "count": 1,
                    "threshold": 3,
                    "reached": False,
                    "action": "block",
                },
            )

    def test_json_report_marks_repeated_failure_reached(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _report(_result("docs/b.md", 2, stderr="boom"))
            policy = GatePolicy(max_gate_failures=2)

            enforce(report, policy, task_id="t", workspace=tmp, clock=_clock)
            outcome = enforce(report, policy, task_id="t", workspace=tmp, clock=_clock)

            import json

            payload = json.loads(build_correction_report(report, outcome, emit_json=True))
            self.assertEqual(
                payload["repeated_failure"],
                {
                    "count": 2,
                    "threshold": 2,
                    "reached": True,
                    "action": "block",
                },
            )

    def test_json_report_exposes_escalate_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _report(_result("docs/b.md", 2, stderr="boom"))
            outcome = enforce(
                report,
                GatePolicy(on_repeated_failure="escalate", max_gate_failures=1),
                task_id="t",
                workspace=tmp,
                clock=_clock,
            )

            import json

            payload = json.loads(build_correction_report(report, outcome, emit_json=True))
            self.assertEqual(
                payload["repeated_failure"],
                {
                    "count": 1,
                    "threshold": 1,
                    "reached": True,
                    "action": "escalate",
                },
            )

    def test_invalid_repeated_failure_action_defaults_to_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _report(_result("docs/b.md", 2, stderr="boom"))
            outcome = enforce(
                report,
                GatePolicy(on_repeated_failure="invalid", max_gate_failures=1),
                task_id="t",
                workspace=tmp,
                clock=_clock,
            )

            import json

            payload = json.loads(build_correction_report(report, outcome, emit_json=True))
            self.assertTrue(outcome.requeue)
            self.assertFalse(outcome.escalate)
            self.assertEqual(payload["repeated_failure"]["action"], "block")

    def test_json_report_pass_reset_exposes_zero_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = GatePolicy(max_gate_failures=3)
            enforce(_report(_result("docs/b.md", 2)), policy, task_id="t", workspace=tmp, clock=_clock)
            report = _report(_result("docs/b.md", 0))
            outcome = enforce(report, policy, task_id="t", workspace=tmp, clock=_clock)

            import json

            payload = json.loads(build_correction_report(report, outcome, emit_json=True))
            self.assertEqual(
                payload["repeated_failure"],
                {
                    "count": 0,
                    "threshold": 3,
                    "reached": False,
                    "action": "block",
                },
            )


if __name__ == "__main__":
    unittest.main()
