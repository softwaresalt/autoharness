"""``cascade-close --poll`` (211.007-T, plan unit T8; hardening H14).

``--poll`` is read-only and idempotent: it maps the journal and (when needed) the evidence record to an exit code
and never writes, takes over, or recovers anything.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

from test_shipment_cascade_close_detach import _DetachHarness
from test_shipment_cascade_close_invoke import (
    _ARCHIVED,
    _FEATURE,
    _SHIPMENT,
    _VERIFIED,
    _envelope,
    _Harness,
)

from autoharness.shipment_close import (
    EXIT_INPUT,
    EXIT_INVOCATION_INDETERMINATE,
    EXIT_LOCKED,
    EXIT_OK,
    EXIT_POSTCONDITION_FAILED,
    EXIT_STARTED,
    command,
)
from autoharness.shipment_close.liveness import current_host
from autoharness.shipment_close.poll import poll_cascade_close


def _tree(root: Path, *, skip_journal: bool = False) -> dict[str, tuple[int, int]]:
    return {
        str(path.relative_to(root)): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not (skip_journal and any(part.endswith(".journal") for part in path.relative_to(root).parts[:-1]))
    }


class PollTests(unittest.TestCase):
    def _poll(self, harness: _Harness, *, live_supervisor: bool = False, **kwargs: object):
        # A live detached supervisor keeps writing its own journal (including atomic temp files) while
        # the poll runs, so only the files outside the journal can prove the poll itself wrote nothing.
        before = _tree(harness.root, skip_journal=live_supervisor)
        result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE, **kwargs)
        self.assertEqual(_tree(harness.root, skip_journal=live_supervisor), before, "--poll must not write anything")
        again = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE, **kwargs)
        self.assertEqual((again.exit_code, again.outcome_source), (result.exit_code, result.outcome_source))
        return result

    def test_poll_after_a_clean_run_and_raw_file_cleanup_returns_the_final_code(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self.assertEqual(harness.run().exit_code, EXIT_OK)
        directory = harness.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.journal"
        self.assertFalse((directory / "stdout.raw").exists())
        result = self._poll(harness)
        self.assertEqual(result.exit_code, EXIT_OK, result.message)
        self.assertEqual(result.outcome_source, "journal_outcome")
        self.assertEqual(result.journal_path, directory)

    def test_poll_reports_each_terminal_exit_code(self) -> None:
        rows = [
            (
                "postcondition failure",
                {"archive": list(_ARCHIVED), "envelope": _envelope(list(_ARCHIVED), returned=["600.009-T"])},
                EXIT_POSTCONDITION_FAILED,
            ),
            (
                "backlogit failure",
                {"archive": [], "envelope": {"jsonrpc": "2.0", "id": 1, "error": {"code": 6}}, "exit": 1},
                EXIT_INVOCATION_INDETERMINATE,
            ),
        ]
        for label, ship, expected in rows:
            with self.subTest(label):
                harness = _Harness(self, probes=[_VERIFIED], ship=ship)
                self.assertEqual(harness.run().exit_code, expected)
                self.assertEqual(self._poll(harness).exit_code, expected)

    def test_a_crash_between_the_evidence_and_the_outcome_writes_is_derived_from_the_evidence_record(self) -> None:
        rows = [
            ("pass", None, EXIT_OK),
            (
                "postcondition failure",
                {"archive": list(_ARCHIVED), "envelope": _envelope(list(_ARCHIVED), returned=["600.009-T"])},
                EXIT_POSTCONDITION_FAILED,
            ),
            (
                "failed invocation",
                {"archive": [], "envelope": {"jsonrpc": "2.0", "id": 1, "error": {"code": 6}}, "exit": 1},
                EXIT_INVOCATION_INDETERMINATE,
            ),
        ]
        for label, ship, expected in rows:
            with self.subTest(label):
                harness = _Harness(self, probes=[_VERIFIED], ship=ship) if ship else _Harness(self, probes=[_VERIFIED])
                with mock.patch.object(command, "_write_outcome"):  # the finalizer died before outcome.json
                    self.assertEqual(harness.run().exit_code, expected)
                directory = harness.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.journal"
                self.assertFalse((directory / "outcome.json").exists())
                result = self._poll(harness)
                self.assertEqual(result.exit_code, expected, result.message)
                self.assertEqual(result.outcome_source, "evidence_record")

    def test_a_running_supervisor_is_exit_9_and_wait_resolves_it(self) -> None:
        harness = _DetachHarness(self, sleep=3.0)
        started = harness.detach()
        self.assertEqual(started.exit_code, EXIT_STARTED, started.message)
        running = self._poll(harness, live_supervisor=True)
        self.assertEqual(running.exit_code, EXIT_STARTED, running.message)
        self.assertIsNone(running.outcome_source)
        finished = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE, wait_seconds=60)
        self.assertEqual(finished.exit_code, EXIT_OK, finished.message)
        # The supervisor writes the terminal evidence record before outcome.json; a poll landing in that
        # window correctly derives the same exit code from the record.
        self.assertIn(finished.outcome_source, ("journal_outcome", "evidence_record"))

    def _orphan(self, harness: _Harness) -> None:
        with mock.patch.object(command, "run_journaled", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                harness.run()
        self.assertEqual(harness.record()["phase"], "invoking")

    def test_an_orphaned_invoking_record_with_no_lock_is_exit_7_with_recovery_available(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        result = self._poll(harness)
        self.assertEqual(result.exit_code, EXIT_LOCKED, result.message)
        self.assertTrue(result.recovery_available)

    def test_a_dead_lock_owner_is_exit_7_and_a_live_one_is_still_running(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        run_id = harness.record()["run_id"]
        process = subprocess.Popen([sys.executable, "-c", "pass"])
        process.wait(timeout=30)
        lock = harness.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)

        def write(pid: int) -> None:
            lock.write_text(json.dumps({"run_id": run_id, "pid": pid, "host": current_host()}), encoding="utf-8")

        write(process.pid)
        dead = self._poll(harness)
        self.assertEqual(dead.exit_code, EXIT_LOCKED, dead.message)
        self.assertTrue(dead.recovery_available)
        write(os.getpid())
        live = self._poll(harness)
        self.assertEqual(live.exit_code, EXIT_STARTED, live.message)
        self.assertFalse(live.recovery_available)

    def test_the_cli_poll_reads_a_real_journal_without_a_binary(self) -> None:
        import io
        from contextlib import redirect_stderr, redirect_stdout

        from autoharness.cli import main

        harness = _Harness(self, probes=[_VERIFIED])
        self.assertEqual(harness.run().exit_code, EXIT_OK)
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            main(
                ["shipment", "cascade-close", "--poll", "--shipment", _SHIPMENT, "--feature", _FEATURE,
                 "--workspace", str(harness.root), "--json"]
            )
        payload = json.loads(out.getvalue())
        self.assertEqual((payload["mode"], payload["exit_code"], payload["outcome_source"]), ("poll", 0, "journal_outcome"))
        self.assertEqual(payload["mutation_possible"], "yes")

    def test_nothing_to_poll_is_exit_2(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        result = self._poll(harness)
        self.assertEqual(result.exit_code, EXIT_INPUT, result.message)

    def test_a_journal_of_another_run_is_not_reported_as_this_runs_outcome(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self.assertEqual(harness.run().exit_code, EXIT_OK)
        record = harness.record()
        record["run_id"] = "e" * 32  # a later run finalized this pair; the journal is stale
        harness.evidence.write_text(json.dumps(record), encoding="utf-8")
        directory = harness.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.journal"
        outcome = directory / "outcome.json"
        stale = json.loads(outcome.read_text(encoding="utf-8"))
        stale["run_id"] = "d" * 32
        outcome.write_text(json.dumps(stale), encoding="utf-8")
        result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertNotEqual(result.exit_code, EXIT_OK, result.message)

    def test_poll_never_waits_longer_than_requested(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        lock = harness.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(
            json.dumps({"run_id": harness.record()["run_id"], "pid": os.getpid(), "host": current_host()}),
            encoding="utf-8",
        )
        started = time.monotonic()
        result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE, wait_seconds=2, poll_interval=0.2)
        self.assertEqual(result.exit_code, EXIT_STARTED)
        self.assertGreaterEqual(time.monotonic() - started, 1.5)
        self.assertLess(time.monotonic() - started, 15)


if __name__ == "__main__":
    unittest.main()
