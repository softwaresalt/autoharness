"""Tests for autoharness.supervise.sidecar -- sidecar lifecycle/preflight (120.002-T).

Covers: ``backlogit sync`` (skipped with outcome "unavailable" when not on
PATH), Engram DIRECT-sync-first with a daemon bind+sync FALLBACK on
failure (mirroring start.ps1's ``Invoke-EngramCommandWithProgress``
sequence), non-fatal failure handling for every sidecar, and the hard
invariant that this module performs NO backlog-artifact mutation and NO
Engram authority writes beyond the two explicitly-permitted derived-index
maintenance invocations.
"""

from __future__ import annotations

import dataclasses
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.supervise.sidecar import SidecarReport, run_sidecars


def _completed(argv, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=argv, returncode=returncode, stdout=stdout, stderr=stderr)


class BacklogitSidecarTests(unittest.TestCase):
    def test_absent_is_unavailable_and_non_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            with mock.patch("shutil.which", return_value=None):
                report = run_sidecars(Path(workspace))
            self.assertEqual(report.outcomes["backlogit"], "unavailable")
            self.assertTrue(any("backlogit" in w.lower() for w in report.warnings))

    def test_present_and_succeeding_is_ok(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            def which(name, *a, **k):
                return f"/resolved/{name}" if name in ("backlogit", "engram") else None

            with mock.patch("shutil.which", side_effect=which):
                with mock.patch("subprocess.run") as run_mock:
                    run_mock.return_value = _completed(["backlogit", "sync"], 0)
                    report = run_sidecars(Path(workspace))
            self.assertEqual(report.outcomes["backlogit"], "ok")

    def test_present_and_failing_is_degraded_non_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            def which(name, *a, **k):
                return f"/resolved/{name}" if name == "backlogit" else None

            with mock.patch("shutil.which", side_effect=which):
                with mock.patch("subprocess.run") as run_mock:
                    run_mock.return_value = _completed(["backlogit", "sync"], 1, stderr="boom")
                    report = run_sidecars(Path(workspace))
            self.assertEqual(report.outcomes["backlogit"], "degraded")
            self.assertTrue(any("backlogit" in w.lower() for w in report.warnings))

    def test_never_raises_even_on_exception(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            def which(name, *a, **k):
                return f"/resolved/{name}" if name == "backlogit" else None

            with mock.patch("shutil.which", side_effect=which):
                with mock.patch("subprocess.run", side_effect=OSError("boom")):
                    report = run_sidecars(Path(workspace))  # must not raise
            self.assertEqual(report.outcomes["backlogit"], "degraded")


class EngramSidecarTests(unittest.TestCase):
    def test_absent_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            with mock.patch("shutil.which", return_value=None):
                report = run_sidecars(Path(workspace))
            self.assertEqual(report.outcomes["engram"], "unavailable")

    def test_direct_sync_success_is_ok_and_calls_direct_only(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            def which(name, *a, **k):
                return f"/resolved/{name}" if name == "engram" else None

            calls = []

            def run(argv, **kwargs):
                calls.append(list(argv))
                return _completed(argv, 0)

            with mock.patch("shutil.which", side_effect=which):
                with mock.patch("subprocess.run", side_effect=run):
                    report = run_sidecars(Path(workspace))
            self.assertEqual(report.outcomes["engram"], "ok")
            self.assertEqual(len(calls), 1)
            self.assertIn("--direct", calls[0])
            self.assertIn("sync", calls[0])

    def test_direct_failure_falls_back_to_bind_then_daemon_sync(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            def which(name, *a, **k):
                return f"/resolved/{name}" if name == "engram" else None

            calls = []

            def run(argv, **kwargs):
                calls.append(list(argv))
                if "--direct" in argv:
                    return _completed(argv, 1, stderr="direct failed")
                return _completed(argv, 0)

            with mock.patch("shutil.which", side_effect=which):
                with mock.patch("subprocess.run", side_effect=run):
                    report = run_sidecars(Path(workspace))
            self.assertEqual(report.outcomes["engram"], "ok")
            self.assertEqual(len(calls), 3)
            self.assertIn("--direct", calls[0])
            self.assertIn("bind", calls[1])
            self.assertIn("sync", calls[2])
            self.assertNotIn("--direct", calls[2])

    def test_direct_and_fallback_both_fail_is_degraded_non_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            def which(name, *a, **k):
                return f"/resolved/{name}" if name == "engram" else None

            def run(argv, **kwargs):
                return _completed(argv, 1, stderr="failed")

            with mock.patch("shutil.which", side_effect=which):
                with mock.patch("subprocess.run", side_effect=run):
                    report = run_sidecars(Path(workspace))
            self.assertEqual(report.outcomes["engram"], "degraded")
            self.assertTrue(any("engram" in w.lower() for w in report.warnings))

    def test_bind_failure_still_attempts_daemon_sync_then_degrades(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            def which(name, *a, **k):
                return f"/resolved/{name}" if name == "engram" else None

            calls = []

            def run(argv, **kwargs):
                calls.append(list(argv))
                if "--direct" in argv:
                    return _completed(argv, 1, stderr="direct failed")
                if "bind" in argv:
                    return _completed(argv, 1, stderr="bind failed")
                return _completed(argv, 0)

            with mock.patch("shutil.which", side_effect=which):
                with mock.patch("subprocess.run", side_effect=run):
                    report = run_sidecars(Path(workspace))
            # Mirrors start.ps1: bind failure still attempts the daemon sync
            # step (three calls total), and overall degrades non-fatally.
            self.assertEqual(len(calls), 3)
            self.assertEqual(report.outcomes["engram"], "degraded")


class SidecarReportShapeTests(unittest.TestCase):
    def test_report_is_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            with mock.patch("shutil.which", return_value=None):
                report = run_sidecars(Path(workspace))
            with self.assertRaises(dataclasses.FrozenInstanceError):
                report.outcomes = {}  # type: ignore[misc]

    def test_never_raises_for_completely_absent_tools(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            with mock.patch("shutil.which", return_value=None):
                report = run_sidecars(Path(workspace))  # must not raise
            self.assertIsInstance(report, SidecarReport)
            self.assertEqual(report.outcomes["backlogit"], "unavailable")
            self.assertEqual(report.outcomes["engram"], "unavailable")


class NoShellTrueTests(unittest.TestCase):
    def test_never_passes_shell_true(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            def which(name, *a, **k):
                return f"/resolved/{name}"

            with mock.patch("shutil.which", side_effect=which):
                with mock.patch("subprocess.run") as run_mock:
                    run_mock.return_value = _completed(["x"], 0)
                    run_sidecars(Path(workspace))
            for call in run_mock.call_args_list:
                self.assertIsNot(call.kwargs.get("shell"), True)


if __name__ == "__main__":
    unittest.main()
