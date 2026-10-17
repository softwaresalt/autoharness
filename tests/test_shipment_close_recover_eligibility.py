"""``cascade-close --recover`` eligibility, takeover, dry-run and recovery-owner rollback (211.010-T, plan unit T10).

Covers hardening H2 (engine still running), H3 (provably dead), H7 addendum (d) (recovery-owner rollback), H8 (torn
writes, idempotence) and H11 (read-only process scan). The orphaned ``invoking`` state is produced by really running
the attached command against the fake backlogit and killing the finalizer.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import subprocess
import sys
import unittest
from unittest import mock

from test_shipment_cascade_close_invoke import _FEATURE, _SHIPMENT, _VERIFIED, _Harness

from autoharness.shipment_close import EXIT_INPUT, EXIT_LOCKED, EXIT_OK, EXIT_RECOVERY_REFUSED, command, recover
from autoharness.shipment_close.journal import Journal, journal_path, write_json, write_never_started
from autoharness.shipment_close.liveness import ProbeResult, current_host
from autoharness.shipment_close.persist import (
    MODE_RECOVER,
    LockDisposition,
    PersistError,
    acquire_pair_lock,
    check_existing_record,
    observe_lock,
)
from autoharness.shipment_close.recover import (
    RecoverEnv,
    RecoverOptions,
    _ship_processes,
    list_processes,
    recover_cascade_close,
)


class _FinalizerDied(Exception):
    pass


def _quiet_env(**overrides: object) -> RecoverEnv:
    values: dict[str, object] = {"list_processes": lambda: [(1, "System")], "sleep": lambda seconds: None}
    values.update(overrides)
    return RecoverEnv(**values)  # type: ignore[arg-type]


def _options(**overrides: object) -> RecoverOptions:
    values: dict[str, object] = {"settle_seconds": 5.0}
    values.update(overrides)
    return RecoverOptions(**values)  # type: ignore[arg-type]


# The re-probe is slow enough that captured_at precedes started_at by a whole second (the validator's strict ordering).
_PROBES = [_VERIFIED, {**_VERIFIED, "sleep": 1.2}]


def _dead_pid() -> int:
    process = subprocess.Popen([sys.executable, "-c", "pass"])
    process.wait(timeout=30)
    return process.pid


class _Orphan(_Harness):
    """A real run whose finalizer died after the child finished: invoking record, journal, no lock."""

    def __init__(self, test: unittest.TestCase, *, ship: dict | None = None) -> None:
        super().__init__(test, probes=_PROBES, ship=ship)
        self.test = test
        with mock.patch.object(command, "_finalize", side_effect=_FinalizerDied("killed")):
            outcome = self.run()
        test.assertEqual(outcome.exit_code, 6, outcome.message)
        test.assertEqual(self.record()["phase"], "invoking")
        self.journal_dir = journal_path(self.root, _SHIPMENT, _FEATURE)
        self.lock_path = self.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.lock"

    def journal(self) -> Journal:
        return Journal(path=self.journal_dir, run_id=self.record()["run_id"])

    def write_lock(self, **payload: object) -> bytes:
        base = {
            "run_id": self.record()["run_id"],
            "pid": _dead_pid(),
            "started_at": "2026-10-16T00:00:00Z",
            "host": current_host(),
            "pid_start": "100",
        }
        base.update(payload)
        base = {key: value for key, value in base.items() if value is not None}
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        data = (json.dumps(base, sort_keys=True) + "\n").encode("utf-8")
        self.lock_path.write_bytes(data)
        return data

    def snapshot_state(self) -> dict[str, bytes | None]:
        state: dict[str, bytes | None] = {"evidence": self.evidence.read_bytes()}
        state["lock"] = self.lock_path.read_bytes() if self.lock_path.exists() else None
        state["siblings"] = "\n".join(sorted(os.listdir(self.lock_path.parent))).encode()
        return state

    def recover(self, options: RecoverOptions | None = None, env: RecoverEnv | None = None, **kwargs: object):
        return recover_cascade_close(
            self.root, _SHIPMENT, _FEATURE, options=options or _options(), env=env or _quiet_env(), **kwargs
        )


class DryRunAndEligibilityTests(unittest.TestCase):
    def test_dry_run_on_an_orphan_reports_eligibility_and_writes_nothing(self) -> None:
        orphan = _Orphan(self)
        before = orphan.snapshot_state()
        outcome = orphan.recover(_options(dry_run=True))
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        self.assertTrue(outcome.dry_run)
        self.assertFalse(outcome.recovered)
        self.assertEqual(outcome.action, "reconstruct")
        self.assertTrue(any("settle" in note for note in outcome.notes), outcome.notes)
        self.assertEqual(orphan.snapshot_state(), before)

    def test_a_dead_owner_lock_is_eligible_and_left_untouched_by_dry_run(self) -> None:
        orphan = _Orphan(self)
        orphan.write_lock()
        before = orphan.snapshot_state()
        outcome = orphan.recover(_options(dry_run=True))
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        self.assertEqual(orphan.snapshot_state(), before)

    def test_phase_and_input_errors(self) -> None:
        orphan = _Orphan(self)
        record = json.loads(orphan.evidence.read_text(encoding="utf-8"))
        for phase, expected in (("post_close", EXIT_INPUT), ("pre_close", EXIT_INPUT), ("mystery", EXIT_RECOVERY_REFUSED)):
            with self.subTest(phase=phase):
                orphan.evidence.write_text(json.dumps({**record, "phase": phase}), encoding="utf-8")
                outcome = orphan.recover(_options(dry_run=True))
                self.assertEqual(outcome.exit_code, expected, outcome.message)
        orphan.evidence.write_text("{not json", encoding="utf-8")
        self.assertEqual(orphan.recover(_options(dry_run=True)).exit_code, EXIT_RECOVERY_REFUSED)
        orphan.evidence.unlink()
        self.assertEqual(orphan.recover(_options(dry_run=True)).exit_code, EXIT_INPUT)

    def test_the_settle_window_can_only_be_raised(self) -> None:
        orphan = _Orphan(self)
        outcome = orphan.recover(_options(settle_seconds=1.0, dry_run=True))
        self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
        self.assertEqual(orphan.recover(_options(settle_seconds=30.0, dry_run=True)).exit_code, EXIT_OK)

    def test_a_pair_mismatch_in_the_record_is_refused(self) -> None:
        orphan = _Orphan(self)
        record = json.loads(orphan.evidence.read_text(encoding="utf-8"))
        orphan.evidence.write_text(json.dumps({**record, "feature_id": "999-F"}), encoding="utf-8")
        self.assertEqual(orphan.recover(_options(dry_run=True)).exit_code, EXIT_RECOVERY_REFUSED)

    def test_an_invalid_pre_close_section_is_refused(self) -> None:
        orphan = _Orphan(self)
        record = json.loads(orphan.evidence.read_text(encoding="utf-8"))
        record["pre_close"]["classifier_verdict"] = "SAFE_CLOSE"
        orphan.evidence.write_text(json.dumps(record), encoding="utf-8")
        outcome = orphan.recover(_options(dry_run=True))
        self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)


class RefusalMatrixTests(unittest.TestCase):
    """Exit 10 writes nothing: the record, the lock, and the lock directory stay byte-identical."""

    def _refused(self, orphan: _Orphan, options: RecoverOptions | None = None, env: RecoverEnv | None = None) -> str:
        before = orphan.snapshot_state()
        base = options or _options()
        for dry_run in (True, False):
            outcome = orphan.recover(
                RecoverOptions(dry_run, base.confirm_owner_dead, base.confirm_engine_stopped, base.settle_seconds), env
            )
            self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)
            self.assertFalse(outcome.recovered)
            self.assertEqual(orphan.snapshot_state(), before)
        return outcome.message

    def test_a_live_lock_owner_refuses(self) -> None:
        orphan = _Orphan(self)
        orphan.write_lock(pid=os.getpid(), pid_start=None)
        self.assertIn("not provably dead", self._refused(orphan))

    def test_a_lock_held_by_a_live_run_other_than_the_original_refuses(self) -> None:
        orphan = _Orphan(self)
        orphan.write_lock(run_id="f" * 32, pid=os.getpid(), pid_start=None)
        self.assertIn("not provably dead", self._refused(orphan))

    def test_a_dead_recovery_runs_lock_left_by_a_crash_after_takeover_is_stale(self) -> None:
        orphan = _Orphan(self)
        orphan.write_lock(run_id="f" * 32)
        outcome = orphan.recover(_options(dry_run=True))
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)

    def test_an_unreadable_lock_needs_the_operator_confirmation(self) -> None:
        orphan = _Orphan(self)
        orphan.lock_path.parent.mkdir(parents=True, exist_ok=True)
        orphan.lock_path.write_bytes(b"\x00 not json")
        self._refused(orphan)
        self.assertEqual(orphan.recover(_options(dry_run=True, confirm_owner_dead=True)).exit_code, EXIT_OK)

    def test_a_foreign_host_lock_needs_the_operator_confirmation(self) -> None:
        orphan = _Orphan(self)
        orphan.write_lock(host="some-other-host")
        self._refused(orphan)
        self.assertEqual(orphan.recover(_options(dry_run=True, confirm_owner_dead=True)).exit_code, EXIT_OK)

    def test_a_legacy_lock_without_host_needs_the_operator_confirmation(self) -> None:
        orphan = _Orphan(self)
        orphan.write_lock(host=None, pid_start=None)
        self._refused(orphan)

    def test_a_pid_reused_by_another_process_is_dead(self) -> None:
        orphan = _Orphan(self)
        orphan.write_lock(pid=4242, pid_start="100")
        env = _quiet_env(prober=lambda pid: ProbeResult("alive", start="999", detail="alive"), local_host=current_host())
        self.assertEqual(orphan.recover(_options(dry_run=True), env).exit_code, EXIT_OK)

    def test_a_live_journaled_child_refuses(self) -> None:
        orphan = _Orphan(self)
        journal = orphan.journal()
        os.unlink(orphan.journal_dir / "exit.json")
        write_json(
            journal,
            "child_started.json",
            {
                "schema_version": 1,
                "run_id": journal.run_id,
                "written_at": "2026-10-16T00:00:00Z",
                "state": "spawned",
                "pid": os.getpid(),
            },
        )
        self.assertIn("alive", self._refused(orphan))

    def test_an_unknown_child_state_refuses(self) -> None:
        orphan = _Orphan(self)
        journal = orphan.journal()
        os.unlink(orphan.journal_dir / "exit.json")
        write_json(
            journal,
            "child_started.json",
            {"schema_version": 1, "run_id": journal.run_id, "written_at": "2026-10-16T00:00:00Z", "state": "spawned", "pid": 4242},
        )
        unknown = _quiet_env(prober=lambda pid: ProbeResult("unknown", detail="no access"))
        self._refused(orphan, env=unknown)

    def test_a_running_ship_process_refuses(self) -> None:
        orphan = _Orphan(self)
        line = f"C:/tools/backlogit.exe --jsonrpc shipment ship {_SHIPMENT} --sha abc"
        env = _quiet_env(list_processes=lambda: [(4321, line)])
        self.assertIn("4321", self._refused(orphan, env=env))

    def test_an_unreadable_process_scan_is_unknown_and_refuses(self) -> None:
        orphan = _Orphan(self)
        self._refused(orphan, env=_quiet_env(list_processes=lambda: None))

        def boom():
            raise OSError("no ps")

        self._refused(orphan, env=_quiet_env(list_processes=boom))

    def test_a_changing_live_state_during_the_settle_window_refuses(self) -> None:
        orphan = _Orphan(self)
        member = orphan.backlog / "queue" / "600-F.md"
        archive_copy = orphan.backlog / "archive" / "600-F.md"

        def engine_still_running(seconds: float) -> None:
            target = archive_copy if archive_copy.exists() else member
            target.write_text(target.read_text(encoding="utf-8") + "\nstill moving\n", encoding="utf-8")

        self.assertIn("settle", self._refused(orphan, env=_quiet_env(sleep=engine_still_running)))

    def test_a_legacy_record_without_a_journal_needs_confirm_engine_stopped(self) -> None:
        orphan = _Orphan(self)
        shutil.rmtree(orphan.journal_dir)
        self.assertIn("--confirm-engine-stopped", self._refused(orphan))
        outcome = orphan.recover(_options(dry_run=True, confirm_engine_stopped=True))
        # Eligibility now passes; this fixture has no engine event log, so reconstruction (T11) refuses.
        self.assertNotIn("--confirm-engine-stopped", outcome.message)
        self.assertIn("event log", outcome.message)

    def test_a_journal_for_another_argv_refuses(self) -> None:
        orphan = _Orphan(self)
        record = json.loads(orphan.evidence.read_text(encoding="utf-8"))
        record["invocation"]["argv_sha256"] = "0" * 64
        orphan.evidence.write_text(json.dumps(record), encoding="utf-8")
        self.assertIn("argv_sha256", self._refused(orphan))

    def test_a_journal_directory_that_is_a_link_refuses(self) -> None:
        orphan = _Orphan(self)
        outside = orphan.root / "elsewhere"
        outside.mkdir()
        shutil.rmtree(orphan.journal_dir)
        from cascade_close_test_support import make_dir_link

        reason = make_dir_link(orphan.journal_dir, outside)
        if reason is not None:
            self.skipTest(reason)
        self.addCleanup(lambda: os.path.lexists(orphan.journal_dir) and os.rmdir(orphan.journal_dir))
        self._refused(orphan)


class ProcessScanTests(unittest.TestCase):
    def test_matching_requires_backlogit_and_the_exact_shipment(self) -> None:
        lines = [
            (1, f"backlogit shipment ship {_SHIPMENT} --sha x"),
            (2, f"BACKLOGIT.EXE --cwd C:/w shipment ship {_SHIPMENT}"),
            (3, f"backlogit shipment ship {_SHIPMENT}9 --sha x"),
            (4, f"backlogit shipment ship {_SHIPMENT}-X"),
            (5, f"python tool.py shipment ship {_SHIPMENT}"),
            (6, "backlogit shipment ship 111-S"),
            (os.getpid(), f"backlogit shipment ship {_SHIPMENT}"),
        ]
        self.assertEqual(_ship_processes(lines, _SHIPMENT), [1, 2])

    def test_the_default_lister_reads_this_process(self) -> None:
        processes = list_processes()
        self.assertIsNotNone(processes)
        self.assertIn(os.getpid(), [pid for pid, _ in processes])


class ExistingRecordModeTests(unittest.TestCase):
    def test_recover_mode_returns_an_invoking_record_and_refuses_other_phases(self) -> None:
        orphan = _Orphan(self)
        run_id = orphan.record()["run_id"]
        lock = acquire_pair_lock(orphan.root, _SHIPMENT, _FEATURE, "a" * 32)
        self.addCleanup(lock.release)
        self.assertEqual(check_existing_record(lock, mode=MODE_RECOVER)["run_id"], run_id)
        record = json.loads(orphan.evidence.read_text(encoding="utf-8"))
        for phase, expected in (("pre_close", EXIT_INPUT), ("post_close", EXIT_INPUT), ("odd", EXIT_LOCKED)):
            orphan.evidence.write_text(json.dumps({**record, "phase": phase}), encoding="utf-8")
            with self.assertRaises(PersistError) as caught:
                check_existing_record(lock, mode=MODE_RECOVER)
            self.assertEqual(caught.exception.exit_code, expected, phase)
        orphan.evidence.write_text(json.dumps({**record, "feature_id": "999-F"}), encoding="utf-8")
        with self.assertRaises(PersistError) as caught:
            check_existing_record(lock, mode=MODE_RECOVER)
        self.assertEqual(caught.exception.exit_code, EXIT_LOCKED)

    def test_the_mutating_mode_still_refuses_an_invoking_record(self) -> None:
        orphan = _Orphan(self)
        lock = acquire_pair_lock(orphan.root, _SHIPMENT, _FEATURE, "a" * 32)
        self.addCleanup(lock.release)
        with self.assertRaises(PersistError) as caught:
            check_existing_record(lock, mode="mutating")
        self.assertEqual(caught.exception.exit_code, EXIT_LOCKED)


class _NeverStarted(_Harness):
    """A run killed after the ``never_started`` sentinel and before the rollback."""

    def __init__(self, test: unittest.TestCase) -> None:
        super().__init__(test, probes=_PROBES)

        def crash_after_sentinel(lock, state, snapshot, durable, argv, owner, timeout, **kw):
            journal = command._prepare_journal(
                lock,
                resolved=kw["resolved"],
                argv=argv,
                merge_commit_sha=kw["merge_commit_sha"],
                timeout=timeout,
                caller_wait=kw["caller_wait"],
                grace=kw["grace"],
                mode="attached",
                finalizer="foreground",
            )
            command._write_invoking(lock, state, durable, argv, owner, journal)
            write_never_started(journal)
            raise _FinalizerDied("killed between the sentinel and the rollback")

        with mock.patch.object(command, "_invoke_and_finalize", side_effect=crash_after_sentinel):
            outcome = self.run()
        test.assertEqual(outcome.exit_code, 6, outcome.message)
        self.lock_path = self.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.lock"
        self.original_run = self.record()["run_id"]

    def stale_lock(self, **payload: object) -> None:
        base = {
            "run_id": self.original_run,
            "pid": _dead_pid(),
            "started_at": "2026-10-16T00:00:00Z",
            "host": current_host(),
            "pid_start": "100",
        }
        base.update(payload)
        base = {key: value for key, value in base.items() if value is not None}
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.write_text(json.dumps(base) + "\n", encoding="utf-8")


class RecoveryOwnerRollbackTests(unittest.TestCase):
    def test_rollback_then_an_attached_retry_succeeds(self) -> None:
        harness = _NeverStarted(self)
        self.assertEqual(harness.record()["phase"], "invoking")
        harness.stale_lock()
        calls_before = len(harness.argv_log())
        outcome = recover_cascade_close(
            harness.root, _SHIPMENT, _FEATURE, options=_options(), env=_quiet_env(), run_id="b" * 32
        )
        self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
        self.assertEqual(outcome.action, "rollback")
        self.assertFalse(outcome.recovered)
        self.assertEqual(outcome.lock_disposition.action, "tombstoned")
        record = harness.record()
        self.assertEqual((record["phase"], record["run_id"]), ("pre_close", "b" * 32))
        self.assertNotIn("invocation", record)
        self.assertFalse(harness.lock_path.exists(), "the recovery run releases its lock")
        tombstones = [name for name in os.listdir(harness.lock_path.parent) if ".stale-" in name]
        self.assertEqual(len(tombstones), 1)
        self.assertFalse(harness.shipped, "recovery never invokes the engine")
        self.assertEqual(len(harness.argv_log()), calls_before, "recovery never spawns backlogit")

        retry = harness.run()
        self.assertEqual(retry.exit_code, EXIT_OK, retry.message)
        self.assertTrue(harness.shipped)

    def test_a_missing_lock_is_enough_for_the_rollback(self) -> None:
        harness = _NeverStarted(self)
        outcome = recover_cascade_close(harness.root, _SHIPMENT, _FEATURE, options=_options(), env=_quiet_env())
        self.assertEqual((outcome.exit_code, outcome.action), (EXIT_INPUT, "rollback"), outcome.message)
        self.assertEqual(outcome.lock_disposition.action, "absent")
        self.assertEqual(harness.record()["phase"], "pre_close")

    def test_the_dry_run_reports_the_rollback_and_writes_nothing(self) -> None:
        harness = _NeverStarted(self)
        harness.stale_lock()
        before = (harness.evidence.read_bytes(), harness.lock_path.read_bytes())
        outcome = recover_cascade_close(
            harness.root, _SHIPMENT, _FEATURE, options=_options(dry_run=True), env=_quiet_env()
        )
        self.assertEqual((outcome.exit_code, outcome.action), (EXIT_OK, "rollback"), outcome.message)
        self.assertEqual((harness.evidence.read_bytes(), harness.lock_path.read_bytes()), before)

    def test_rollback_refuses_a_live_owner_and_an_operator_confirmation_alone(self) -> None:
        harness = _NeverStarted(self)
        harness.stale_lock(pid=os.getpid(), pid_start=None)
        outcome = recover_cascade_close(harness.root, _SHIPMENT, _FEATURE, options=_options(), env=_quiet_env())
        self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)
        harness.stale_lock(host="some-other-host")
        outcome = recover_cascade_close(
            harness.root, _SHIPMENT, _FEATURE, options=_options(confirm_owner_dead=True), env=_quiet_env()
        )
        self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)
        self.assertIn("provably", outcome.message)
        self.assertEqual(harness.record()["phase"], "invoking")

    def test_a_child_started_record_voids_the_never_started_proof(self) -> None:
        harness = _NeverStarted(self)
        journal = Journal(path=journal_path(harness.root, _SHIPMENT, _FEATURE), run_id=harness.original_run)
        write_json(
            journal,
            "child_started.json",
            {"schema_version": 1, "run_id": journal.run_id, "written_at": "2026-10-16T00:00:00Z", "state": "spawning", "pid": None},
        )
        outcome = recover_cascade_close(harness.root, _SHIPMENT, _FEATURE, options=_options(), env=_quiet_env())
        self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)
        self.assertEqual(harness.record()["phase"], "invoking")

    def test_a_second_recovery_after_a_rollback_exits_2_and_changes_nothing(self) -> None:
        harness = _NeverStarted(self)
        recover_cascade_close(harness.root, _SHIPMENT, _FEATURE, options=_options(), env=_quiet_env())
        before = harness.evidence.read_bytes()
        outcome = recover_cascade_close(harness.root, _SHIPMENT, _FEATURE, options=_options(), env=_quiet_env())
        self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
        self.assertEqual(harness.evidence.read_bytes(), before)


class RollbackProofTests(unittest.TestCase):
    def _eligibility(self, harness: _NeverStarted):
        return recover.assess_eligibility(harness.root, _SHIPMENT, _FEATURE, _options(), _quiet_env())

    def test_owner_death_comes_from_the_real_lock_disposition(self) -> None:
        harness = _NeverStarted(self)
        eligibility = self._eligibility(harness)
        dead = LockDisposition("tombstoned", 1, "h", "pid_absent")
        self.assertTrue(recover._owner_provably_dead(eligibility, dead))
        self.assertFalse(recover._owner_provably_dead(eligibility, LockDisposition("operator_confirmed", 1, "h", "operator_confirmed")))
        absent = LockDisposition("absent", None, None, "lock_absent")
        self.assertTrue(recover._owner_provably_dead(eligibility, absent))

    def test_an_absent_lock_does_not_prove_death_once_a_spawn_record_appears(self) -> None:
        harness = _NeverStarted(self)
        eligibility = self._eligibility(harness)
        journal = Journal(path=journal_path(harness.root, _SHIPMENT, _FEATURE), run_id=harness.original_run)
        write_json(
            journal,
            "child_started.json",
            {"schema_version": 1, "run_id": journal.run_id, "written_at": "2026-10-16T00:00:00Z", "state": "spawning", "pid": None},
        )
        absent = LockDisposition("absent", None, None, "lock_absent")
        self.assertFalse(recover._owner_provably_dead(eligibility, absent))

    def test_an_invalid_pre_close_record_is_refused_before_anything_is_written(self) -> None:
        harness = _NeverStarted(self)
        eligibility = self._eligibility(harness)
        broken = dataclasses.replace(eligibility, record={**eligibility.record, "pre_close": {}})
        lock = acquire_pair_lock(harness.root, _SHIPMENT, _FEATURE, "b" * 32)
        self.addCleanup(lock.release)
        before = harness.evidence.read_bytes()
        with self.assertRaises(recover._Refused):
            recover._rollback(lock, broken, "b" * 32, LockDisposition("absent", None, None, "lock_absent"))
        self.assertEqual(harness.evidence.read_bytes(), before)


class PowerShellResolutionTests(unittest.TestCase):
    def test_only_the_absolute_system_powershell_is_used(self) -> None:
        root = "C:\\Windows"
        expected = os.path.join(root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
        self.assertEqual(
            recover._powershell_path({"SystemRoot": root}, cwd="C:\\ws", is_file=lambda p: p == expected), expected
        )
        self.assertIsNone(recover._powershell_path({"SystemRoot": root}, cwd="C:\\ws", is_file=lambda p: False))
        self.assertIsNone(recover._powershell_path({}, cwd="C:\\ws", is_file=lambda p: True))
        self.assertIsNone(recover._powershell_path({"SystemRoot": "relative"}, cwd="C:\\ws", is_file=lambda p: True))

    def test_a_system_root_inside_the_working_directory_is_rejected(self) -> None:
        self.assertIsNone(
            recover._powershell_path({"SystemRoot": "C:\\ws\\fake"}, cwd="C:\\ws", is_file=lambda p: True)
        )

    def test_the_process_listing_is_decoded_as_utf_8(self) -> None:
        sep = "\t" if os.name == "nt" else " "
        stdout = f"4242{sep}backlogit shipment ship 900-S caf\u00e9\n".encode("utf-8")
        completed = subprocess.CompletedProcess([], 0, stdout=stdout, stderr=b"")
        with (
            mock.patch.object(recover.subprocess, "run", return_value=completed),
            mock.patch.object(recover, "_powershell_path", return_value="C:\\Windows\\powershell.exe"),
        ):
            processes = list_processes()
        self.assertEqual(processes, [(4242, "backlogit shipment ship 900-S caf\u00e9")])


class TakeoverInteractionTests(unittest.TestCase):
    def test_a_stale_takeover_guard_refuses_without_writing(self) -> None:
        harness = _NeverStarted(self)
        harness.stale_lock()
        guard = harness.lock_path.with_name(harness.lock_path.name + ".takeover")
        guard.write_text("{}", encoding="utf-8")
        before = (harness.evidence.read_bytes(), harness.lock_path.read_bytes())
        outcome = recover_cascade_close(harness.root, _SHIPMENT, _FEATURE, options=_options(), env=_quiet_env())
        self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)
        self.assertEqual((harness.evidence.read_bytes(), harness.lock_path.read_bytes()), before)

    def test_the_record_changing_after_the_takeover_is_refused(self) -> None:
        harness = _NeverStarted(self)
        harness.stale_lock()
        real = check_existing_record

        def racing(lock, *, mode):
            record = json.loads(harness.evidence.read_text(encoding="utf-8"))
            record["invocation"]["started_at"] = "2026-10-17T00:00:00Z"
            harness.evidence.write_text(json.dumps(record), encoding="utf-8")
            return real(lock, mode=mode)

        with mock.patch("autoharness.shipment_close.recover.check_existing_record", racing):
            outcome = recover_cascade_close(harness.root, _SHIPMENT, _FEATURE, options=_options(), env=_quiet_env())
        self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)
        self.assertFalse(harness.lock_path.exists(), "the recovery lock is always released")
        self.assertIsNone(observe_lock(harness.root, _SHIPMENT, _FEATURE))


if __name__ == "__main__":
    unittest.main()
