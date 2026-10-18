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
from autoharness.shipment_close.journal import write_json
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
        harness = _DetachHarness(self, hold=True)
        started = harness.detach()
        self.assertEqual(started.exit_code, EXIT_STARTED, started.message)
        running = self._poll(harness, live_supervisor=True)
        self.assertEqual(running.exit_code, EXIT_STARTED, running.message)
        self.assertIsNone(running.outcome_source)
        harness.release()
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

    def test_poll_after_a_recovery_reports_the_recovered_exit_code(self) -> None:
        from test_shipment_close_recover_reconstruct import _Recovery

        rows = [
            ("recovered pass", {}, 0),
            (
                "recovered failed invocation",
                {"ship": {"archive": [], "envelope": {"jsonrpc": "2.0", "id": 1, "error": {"code": -1}}, "exit": 1}},
                EXIT_INVOCATION_INDETERMINATE,
            ),
        ]
        for label, kwargs, expected in rows:
            with self.subTest(label):
                orphan = _Recovery(self, **kwargs)
                self.assertEqual(orphan.run_recovery().exit_code, expected)
                self.assertFalse((orphan.journal_dir / "outcome.json").exists())
                result = self._poll(orphan)
                self.assertEqual(result.exit_code, expected, result.message)
                self.assertEqual(result.outcome_source, "recovered_evidence")

    def test_poll_of_a_postconditions_only_recovery_derives_the_code_from_the_facts(self) -> None:
        from test_shipment_close_recover_reconstruct import _Recovery

        orphan = _Recovery(self)
        orphan.mark_unproven()
        orphan.write_logs(correlated=True)
        exit_record = json.loads((orphan.journal_dir / "exit.json").read_text(encoding="utf-8"))
        exit_record.update(state="timed_out", exit_code=None, timed_out=True)
        write_json(orphan.journal(), "exit.json", exit_record)
        self.assertEqual(orphan.run_recovery().exit_code, EXIT_INVOCATION_INDETERMINATE)
        result = self._poll(orphan)
        self.assertEqual(result.exit_code, EXIT_INVOCATION_INDETERMINATE, result.message)
        self.assertEqual(result.outcome_source, "recovered_evidence")

    def test_an_outcome_landing_during_the_lock_read_is_not_reported_as_an_orphan(self) -> None:
        from autoharness.shipment_close import poll as poll_module
        from autoharness.shipment_close.journal import Journal

        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        directory = harness.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.journal"
        journal = Journal(path=directory, run_id=harness.record()["run_id"])

        def late_finalizer(*args: object, **kwargs: object):
            command._write_outcome(journal, 8, "post_write_failed", "supervisor", detail="x")
            return None  # the lock vanished as the finalizer released it

        with mock.patch.object(poll_module, "observe_lock", late_finalizer):
            result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertEqual((result.exit_code, result.outcome_source), (8, "journal_outcome"), result.message)

    def test_a_journal_without_a_readable_meta_is_an_operator_review_exit_7(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        directory = harness.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.journal"
        (directory / "meta.json").write_text("{not json", encoding="utf-8")
        result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertEqual(result.exit_code, EXIT_LOCKED, result.message)
        self.assertIsNone(result.recovery_available)

    def test_an_unreadable_evidence_record_is_exit_7_not_a_guess(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        harness.evidence.write_text("[1, 2]", encoding="utf-8")
        self.assertEqual(poll_cascade_close(harness.root, _SHIPMENT, _FEATURE).exit_code, EXIT_LOCKED)
        harness.evidence.write_text("{torn", encoding="utf-8")
        self.assertEqual(poll_cascade_close(harness.root, _SHIPMENT, _FEATURE).exit_code, EXIT_LOCKED)

    def test_an_invoking_record_of_another_run_is_never_reported_as_this_runs_state(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        record = harness.record()
        harness.evidence.write_text(json.dumps({**record, "run_id": "c" * 32}), encoding="utf-8")
        result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertEqual((result.exit_code, result.recovery_available), (EXIT_LOCKED, False), result.message)

    def test_a_lock_held_by_another_run_blocks_recovery_advice(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        lock = harness.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(json.dumps({"run_id": "d" * 32, "pid": 1, "host": current_host()}), encoding="utf-8")
        result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertEqual((result.exit_code, result.recovery_available), (EXIT_LOCKED, False), result.message)

    def test_a_linked_journal_directory_is_untrusted_exit_7_with_no_recovery(self) -> None:
        import shutil
        import tempfile

        from cascade_close_test_support import make_dir_link

        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        directory = harness.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.journal"
        elsewhere = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, elsewhere, True)
        moved = elsewhere / "journal"
        shutil.copytree(directory, moved)
        shutil.rmtree(directory)
        reason = make_dir_link(directory, moved)
        if reason:
            self.skipTest(reason)
        result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertEqual((result.exit_code, result.recovery_available), (EXIT_LOCKED, False), result.message)

    def test_a_linked_lock_directory_is_untrusted_exit_7_with_no_recovery(self) -> None:
        import shutil
        import tempfile

        from cascade_close_test_support import make_dir_link

        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        gates = harness.root / ".autoharness" / "gates"
        elsewhere = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, elsewhere, True)
        moved = elsewhere / "cascade-close"
        shutil.copytree(gates / "cascade-close", moved)
        shutil.rmtree(gates / "cascade-close")
        reason = make_dir_link(gates / "cascade-close", moved)
        if reason:
            self.skipTest(reason)
        result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertEqual((result.exit_code, result.recovery_available), (EXIT_LOCKED, False), result.message)

    def test_an_exit_0_outcome_needs_a_validated_post_close_record_for_the_same_run(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self.assertEqual(harness.run().exit_code, EXIT_OK)
        record = harness.record()
        record["post_close"]["postcondition_verdict"] = "fail"
        harness.evidence.write_text(json.dumps(record), encoding="utf-8")
        result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertEqual((result.exit_code, result.outcome_source), (EXIT_POSTCONDITION_FAILED, "evidence_record"))
        harness.evidence.unlink()
        result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertEqual(result.exit_code, EXIT_INPUT, result.message)
        self.assertIsNone(result.outcome_source)

    def test_an_exit_0_outcome_with_an_unreadable_evidence_record_is_exit_7(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self.assertEqual(harness.run().exit_code, EXIT_OK)
        harness.evidence.write_text("{torn", encoding="utf-8")
        self.assertEqual(poll_cascade_close(harness.root, _SHIPMENT, _FEATURE).exit_code, EXIT_LOCKED)

    def test_a_recovery_record_wins_over_a_stale_failing_outcome(self) -> None:
        from test_shipment_close_recover_reconstruct import _Recovery

        orphan = _Recovery(self)
        self.assertEqual(orphan.run_recovery().exit_code, 0)
        command._write_outcome(orphan.journal(), 8, "post_write_failed", "supervisor", detail="stale")
        self.assertTrue((orphan.journal_dir / "outcome.json").exists())
        result = poll_cascade_close(orphan.root, _SHIPMENT, _FEATURE)
        self.assertEqual((result.exit_code, result.outcome_source), (0, "recovered_evidence"), result.message)

    def test_a_transient_sharing_violation_reading_the_lock_is_retried(self) -> None:
        from autoharness.shipment_close import poll as poll_module
        from autoharness.shipment_close.persist import PersistError

        harness = _Harness(self, probes=[_VERIFIED])
        self._orphan(harness)
        calls: list[int] = []

        def flaky(*args: object, **kwargs: object):
            calls.append(1)
            if len(calls) == 1:
                try:
                    raise PermissionError("sharing violation")
                except PermissionError as exc:
                    raise PersistError(EXIT_LOCKED, "existing lock is unreadable") from exc
            return None

        with mock.patch.object(poll_module, "observe_lock", flaky):
            result = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertEqual(len(calls), 2)
        self.assertEqual((result.exit_code, result.recovery_available), (EXIT_LOCKED, True), result.message)

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
