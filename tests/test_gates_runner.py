"""Tests for the injection-safe subprocess gate runner (T5).

Security controls are acceptance-blocking (Plan Hardening A1 / P2-1).
"""

from __future__ import annotations

import subprocess
import unittest

from autoharness.gates.config import ValidationGate
from autoharness.gates.runner import GateResult, build_argv, run_gate


def _gate(command: str, timeout: int = 10) -> ValidationGate:
    return ValidationGate(pattern="*", command=command, timeout_seconds=timeout)


class GateRunnerTests(unittest.TestCase):
    def test_nonzero_exit_captured_with_stderr(self) -> None:
        gate = _gate("python -c \"import sys; sys.stderr.write('boom'); sys.exit(3)\"")
        result = run_gate(gate, "docs/a.md")
        self.assertIsInstance(result, GateResult)
        self.assertEqual(result.exit_code, 3)
        self.assertIn("boom", result.stderr)
        self.assertFalse(result.passed)
        self.assertEqual(result.failure_reason, "nonzero-exit")

    def test_pass_captured(self) -> None:
        result = run_gate(_gate("python -c \"import sys; sys.exit(0)\""), "docs/a.md")
        self.assertTrue(result.passed)

    def test_timeout_enforced_with_hard_kill(self) -> None:
        gate = _gate("python -c \"import time; time.sleep(30)\"", timeout=1)
        result = run_gate(gate, "docs/a.md")
        self.assertTrue(result.timed_out)
        self.assertIsNone(result.exit_code)
        self.assertFalse(result.passed)
        self.assertEqual(result.failure_reason, "timeout")
        self.assertLess(result.duration, 15)

    def test_missing_binary_reported_distinctly(self) -> None:
        gate = _gate("definitely_not_a_real_binary_xyzzy verify {file_path}")
        result = run_gate(gate, "docs/a.md")
        self.assertTrue(result.missing_binary)
        self.assertEqual(result.failure_reason, "missing-binary")
        self.assertIn("configuration error", result.stderr)
        self.assertIn("definitely_not_a_real_binary_xyzzy", result.stderr)

    def test_file_path_cannot_inject_second_command(self) -> None:
        # A crafted file path with shell metacharacters must remain a single argv
        # element; argv arity is fixed by the template, not the path content.
        malicious = "a.md; rm -rf / && echo $(whoami) `id`"
        argv = build_argv("engram verify {file_path}", {"file_path": malicious})
        self.assertEqual(argv, ["engram", "verify", malicious])
        self.assertEqual(len(argv), 3)

    def test_execution_never_uses_shell_true(self) -> None:
        calls: list[dict] = []

        def spy(argv, **kwargs):
            calls.append({"argv": argv, "kwargs": kwargs})

            class _P:
                returncode = 0
                stdout = ""
                stderr = ""

            return _P()

        run_gate(_gate("engram verify {file_path}"), "a.md; rm -rf /", run_fn=spy)
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0]["kwargs"].get("shell"), False)
        self.assertIsInstance(calls[0]["argv"], list)
        # The dangerous path is a single, inert argv element.
        self.assertIn("a.md; rm -rf /", calls[0]["argv"])

    def test_source_contains_no_shell_true(self) -> None:
        from pathlib import Path

        src = (Path(__file__).resolve().parents[1] / "src" / "autoharness" / "gates" / "runner.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("shell=True", src)


if __name__ == "__main__":
    unittest.main()
