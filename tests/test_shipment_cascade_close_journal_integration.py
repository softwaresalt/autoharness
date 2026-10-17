"""Attached ``cascade-close`` through the durable journal (211.005-T, plan unit T6; hardening H5, H12, H13)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

from test_shipment_cascade_close_invoke import (
    _FAKE_BACKLOGIT,
    _FEATURE,
    _SHIPMENT,
    _VERIFIED,
    _Harness,
    _ship_argvs,
)

from autoharness.gates.cascade_evidence import validate_evidence_record
from autoharness.shipment_close import (
    EXIT_INVOCATION_INDETERMINATE,
    EXIT_LOCKED,
    EXIT_OK,
    EXIT_POST_WRITE_FAILED,
    command,
)
from autoharness.shipment_close.journal import Journal, argv_sha256, journal_path, read_json
from autoharness.shipment_close.liveness import current_host, is_process_alive
from autoharness.shipment_close.persist import (
    STREAM_DRAIN_INCOMPLETE_ERROR,
    PersistError,
    acquire_pair_lock,
)
from autoharness.shipment_close.runner import ResolvedBinary, hash_binary

_RUN = "c" * 32


def _journal_dir(harness: _Harness) -> Path:
    return journal_path(harness.root, _SHIPMENT, _FEATURE)


class AttachedJournalTests(unittest.TestCase):
    def test_a_clean_run_keeps_only_the_final_answer_files(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        captured: dict[str, dict] = {}
        real_write = command.write_evidence_atomic

        def write(path, record, **kwargs):
            captured[record["phase"]] = json.loads(json.dumps(record))
            return real_write(path, record, **kwargs)

        with mock.patch.object(command, "write_evidence_atomic", side_effect=write):
            outcome = harness.run(caller_wait_seconds=4000)
        self.assertEqual(outcome.exit_code, EXIT_OK, (outcome.message, outcome.failures))
        directory = _journal_dir(harness)
        self.assertEqual(outcome.journal_path, directory)
        names = {entry.name for entry in directory.iterdir()}
        self.assertEqual(names, {"meta.json", "exit.json", "outcome.json"})

        journal = Journal(path=directory, run_id=outcome_run_id(harness))
        meta = read_json(journal, "meta.json")
        exact_argv = _ship_argvs(harness.argv_log())[0]
        self.assertEqual(meta["run_id"], journal.run_id)
        self.assertEqual(meta["argv_redacted"], captured["invoking"]["invocation"]["argv_redacted"])
        self.assertEqual(meta["timeout_seconds"], 60)
        self.assertEqual(meta["caller_wait_seconds"], 4000)
        self.assertEqual(meta["host"], current_host())
        self.assertEqual(meta["wrapper_pid"], os.getpid())
        self.assertEqual(meta["finalizer"], "foreground")
        self.assertEqual(meta["argv_sha256"], captured["invoking"]["invocation"]["argv_sha256"])
        self.assertEqual(len(meta["argv_sha256"]), 64)
        self.assertNotIn("argv_sha256", captured["post_close"]["invocation"])
        self.assertEqual(argv_sha256([*harness.resolved.argv_prefix, *exact_argv]), meta["argv_sha256"])
        outcome_file = read_json(journal, "outcome.json")
        self.assertEqual((outcome_file["exit_code"], outcome_file["outcome"], outcome_file["finalizer"]), (0, "completed", "foreground"))
        self.assertEqual(read_json(journal, "exit.json")["exit_code"], 0)
        record = harness.record()
        self.assertEqual(
            validate_evidence_record(record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path="cascade"), []
        )

    def test_the_exact_argv_reaches_the_engine_while_the_record_holds_only_the_redacted_copy(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        message = "close 900-S token=supersecretvalue123"
        outcome = harness.run(message=message)
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        ship = _ship_argvs(harness.argv_log())[0]
        self.assertEqual(ship[ship.index("--message") + 1], message)
        recorded = json.dumps(harness.record()["invocation"]["argv_redacted"])
        self.assertNotIn("supersecretvalue123", recorded)
        meta = json.loads((_journal_dir(harness) / "meta.json").read_text(encoding="utf-8"))
        self.assertNotIn("supersecretvalue123", json.dumps(meta["argv_redacted"]))

    def test_a_failed_run_keeps_the_raw_journal(self) -> None:
        ship = {
            "archive": [],
            "envelope": {"jsonrpc": "2.0", "id": 1, "error": {"code": 6, "message": "gate blocked"}},
            "exit": 1,
            "stderr": "failure detail token=supersecretvalue123\n",
        }
        harness = _Harness(self, probes=[_VERIFIED], ship=ship)
        outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_INVOCATION_INDETERMINATE, outcome.message)
        directory = _journal_dir(harness)
        self.assertEqual(
            {entry.name for entry in directory.iterdir()},
            {"meta.json", "launch.json", "exit.json", "outcome.json", "stdout.raw", "stderr.raw"},
        )
        # The journal holds the raw output; only the evidence record is redacted.
        self.assertIn(b"supersecretvalue123", (directory / "stderr.raw").read_bytes())
        self.assertNotIn("supersecretvalue123", harness.evidence.read_text(encoding="utf-8"))
        outcome_file = json.loads((directory / "outcome.json").read_text(encoding="utf-8"))
        self.assertEqual((outcome_file["exit_code"], outcome_file["outcome"]), (6, "invocation_failed"))

    def test_a_post_write_failure_keeps_the_journal_and_records_exit_8(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        real_write = command.write_evidence_atomic

        def write(path, record, **kwargs):
            if record.get("phase") == "post_close":
                raise PersistError(2, "simulated post-close write failure")
            return real_write(path, record, **kwargs)

        with mock.patch.object(command, "write_evidence_atomic", side_effect=write):
            outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_POST_WRITE_FAILED, outcome.message)
        directory = _journal_dir(harness)
        self.assertTrue((directory / "stdout.raw").exists())
        self.assertTrue((directory / "launch.json").exists())
        outcome_file = json.loads((directory / "outcome.json").read_text(encoding="utf-8"))
        self.assertEqual((outcome_file["exit_code"], outcome_file["outcome"]), (8, "post_write_failed"))

    def test_a_leftover_journal_from_a_rolled_back_run_does_not_block_a_new_run(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        directory = _journal_dir(harness)
        directory.mkdir(parents=True)
        (directory / "stdout.raw").write_bytes(b"stale output from another run")
        (directory / "abort.json").write_text("{}", encoding="utf-8")
        outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        self.assertFalse((directory / "abort.json").exists())

    def test_an_unspawnable_child_is_a_recorded_exit_6(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        with mock.patch.object(command, "run_journaled", side_effect=PersistError(2, "cannot spawn 'backlogit'")):
            outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_INVOCATION_INDETERMINATE, outcome.message)
        self.assertIn("could not be spawned", harness.record()["post_close"]["parse_error"])
        self.assertEqual(harness.record()["phase"], "post_close")

    def test_a_lingering_grandchild_fails_closed_to_exit_6_never_completed(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        pid_file = harness.fakes / "grandchild.pid"
        lingering = _FAKE_BACKLOGIT.replace(
            'sys.exit(ship.get("exit", 0))',
            "import subprocess\n"
            "    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], stdout=sys.stdout, stderr=sys.stderr)\n"
            f"    open({str(pid_file)!r}, 'w').write(str(child.pid))\n"
            "    sys.stdout.flush()\n"
            '    sys.exit(ship.get("exit", 0))',
        )
        self.assertNotEqual(lingering, _FAKE_BACKLOGIT)
        harness.script.write_text(lingering, encoding="utf-8")
        harness.resolved = ResolvedBinary(
            binary_path=str(harness.script),
            binary_sha256=hash_binary(harness.script),
            argv_prefix=(sys.executable, str(harness.script)),
        )
        started = time.monotonic()
        outcome = harness.run(quiescence_grace_seconds=1.0)
        self.assertLess(time.monotonic() - started, 60)
        self.addCleanup(_stop_pid, int(pid_file.read_text(encoding="utf-8")))
        self.assertEqual(outcome.exit_code, EXIT_INVOCATION_INDETERMINATE, outcome.message)
        record = harness.record()
        self.assertEqual(record["phase"], "post_close")
        self.assertEqual(record["post_close"]["parse_error"], STREAM_DRAIN_INCOMPLETE_ERROR)
        self.assertTrue(record["invocation"]["stdout"]["capture_truncated"])
        self.assertNotEqual(
            validate_evidence_record(record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path="cascade"), []
        )
        outcome_file = json.loads((_journal_dir(harness) / "outcome.json").read_text(encoding="utf-8"))
        self.assertEqual(outcome_file["outcome"], "invocation_failed")


def outcome_run_id(harness: _Harness) -> str:
    return harness.record()["run_id"]


def _stop_pid(pid: int) -> None:
    if is_process_alive(pid) is not True:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, check=False)
    else:
        os.kill(pid, 9)


class RecoveryAvailableTests(unittest.TestCase):
    """A mutating run that meets an orphaned ``invoking`` record reports ``recovery_available``; exit 7 is unchanged."""

    def _invoking(self, harness: _Harness) -> bytes:
        harness.evidence.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "phase": "invoking",
            "run_id": "0123456789abcdef0123456789abcdef",
            "shipment_id": _SHIPMENT,
            "feature_id": _FEATURE,
        }
        harness.evidence.write_text(json.dumps(record) + "\n", encoding="utf-8")
        return harness.evidence.read_bytes()

    def _dead_pid(self) -> int:
        process = subprocess.Popen([sys.executable, "-c", "pass"])
        process.wait(timeout=30)
        return process.pid

    def _stale_lock(self, harness: _Harness, *, pid: int, host: str | None = None) -> Path:
        lock_dir = harness.root / ".autoharness" / "gates" / "cascade-close"
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock = lock_dir / f"{_SHIPMENT}-{_FEATURE}.lock"
        lock.write_text(
            json.dumps({"run_id": "0123456789abcdef0123456789abcdef", "pid": pid, "host": host or current_host()}),
            encoding="utf-8",
        )
        return lock

    def test_invoking_record_without_a_lock_is_recoverable(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        before = self._invoking(harness)
        outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_LOCKED, outcome.message)
        self.assertTrue(outcome.recovery_available)
        self.assertEqual(harness.argv_log(), [])
        self.assertEqual(harness.evidence.read_bytes(), before)

    def test_invoking_record_with_a_dead_owner_lock_is_recoverable(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        before = self._invoking(harness)
        lock = self._stale_lock(harness, pid=self._dead_pid())
        lock_before = lock.read_bytes()
        outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_LOCKED, outcome.message)
        self.assertTrue(outcome.recovery_available)
        self.assertEqual(lock.read_bytes(), lock_before, "nothing may be taken over or recovered here")
        self.assertEqual(harness.evidence.read_bytes(), before)
        self.assertFalse(harness.shipped)

    def test_a_live_owner_is_not_recoverable(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self._invoking(harness)
        self._stale_lock(harness, pid=os.getpid())
        outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_LOCKED, outcome.message)
        self.assertFalse(outcome.recovery_available)

    def test_a_stale_lock_without_an_invoking_record_is_not_recoverable(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        self._stale_lock(harness, pid=self._dead_pid())
        outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_LOCKED, outcome.message)
        self.assertFalse(outcome.recovery_available)

    def test_a_lock_held_by_a_live_run_in_this_process_is_not_recoverable(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        held = acquire_pair_lock(harness.root, _SHIPMENT, _FEATURE, _RUN)
        self.addCleanup(held.release)
        outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_LOCKED, outcome.message)
        self.assertFalse(outcome.recovery_available)
        self.assertEqual(_ship_argvs(harness.argv_log()), [])


if __name__ == "__main__":
    unittest.main()
