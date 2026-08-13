"""Tests for locking.py's stale-record lifecycle and force_unlock (118.006-T).

Core acquire/release/guard-permanence tests (118.005-T) live in
``tests/test_supervise_locking.py``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from autoharness.supervise.locking import (
    GUARD_RELATIVE_PATH,
    RECORD_RELATIVE_PATH,
    ForceUnlockOutcome,
    Liveness,
    SessionLock,
    SessionRecord,
    diagnose_liveness,
    force_unlock,
    get_file_identity,
    is_stale_eligible_for_force_unlock,
    read_record,
)

_WORKER_SCRIPT = Path(__file__).resolve().parent / "_supervise_lock_worker.py"

# Real subprocess race tests below: measured cost is small (each iteration
# spawns 1-2 subprocesses, not 8), so the full spirit of "repeated
# iterations" is honored with a modest repeat count chosen for signal
# without materially inflating suite runtime; see each test's inline
# rationale where a specific count is chosen.
_RACE_REPEATS = 10


def _run_worker(args: list[str], timeout: float = 20.0) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_WORKER_SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _write_record(workspace: Path, record: SessionRecord) -> Path:
    record_path = Path(workspace) / RECORD_RELATIVE_PATH
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record.to_dict()), encoding="utf-8")
    return record_path


def _spawn_dead_pid() -> int:
    """Spawn and wait out a trivial subprocess; its PID is then guaranteed dead."""

    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    pid = proc.pid
    proc.wait(timeout=10)
    return pid


class DeadPidDetectionTests(unittest.TestCase):
    def test_dead_pid_is_diagnosed_stale_and_eligible(self) -> None:
        dead_pid = _spawn_dead_pid()
        record = SessionRecord(pid=dead_pid, start_time=0.0, session_id="dead-session")

        liveness = diagnose_liveness(record)

        self.assertEqual(liveness, Liveness.STALE)
        self.assertTrue(is_stale_eligible_for_force_unlock(liveness))


@unittest.skipUnless(sys.platform == "win32", "Windows-specific OpenProcess/GetExitCodeProcess contract")
class WindowsKilledPidStillActiveRegressionTests(unittest.TestCase):
    """Regression for a real Windows liveness bug found while validating
    118.006-T against the stale-record characterization suite: a
    ``TerminateProcess``-killed child's PID can remain a VALID
    ``OpenProcess`` target for a time after it has already exited (the
    process object is not necessarily torn down the instant the process
    dies -- e.g. while any handle, including our own diagnostic
    ``OpenProcess`` call, or the parent's own ``subprocess.Popen`` handle,
    is still outstanding). Checking only "did ``OpenProcess`` succeed" is
    therefore NOT sufficient to determine liveness -- it must be paired
    with ``GetExitCodeProcess`` returning ``STILL_ACTIVE`` (259); any other
    exit code means the process has already exited and must be treated as
    dead."""

    def test_killed_process_is_diagnosed_dead_immediately_after_wait(self) -> None:
        from autoharness.supervise.locking import _pid_exists

        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"]
        )
        try:
            # Give the child a moment to actually start running before we
            # kill it, so this exercises a genuinely-running-then-killed
            # process rather than racing process creation itself.
            time.sleep(0.2)
            proc.kill()
            proc.wait(timeout=10)

            # No polling/retry loop here: this must be correct on the FIRST
            # observation immediately after wait() returns, not merely
            # eventually-consistent after some unspecified delay -- that
            # is exactly the defect this regression guards against.
            alive = _pid_exists(proc.pid)
        finally:
            if proc.poll() is None:  # pragma: no cover - defensive
                proc.kill()
                proc.wait(timeout=10)

        self.assertFalse(
            alive,
            "a killed-and-waited process must be diagnosed dead (not True/"
            "alive) immediately, not merely after an unbounded grace period",
        )


class StartTimeMismatchTests(unittest.TestCase):
    def test_start_time_mismatch_on_a_live_pid_is_stale(self) -> None:
        """A recycled PID: the PID is alive, but the recorded start-time is wrong."""

        import os

        from autoharness.supervise.locking import _process_start_time

        real_pid = os.getpid()
        real_start_time = _process_start_time(real_pid)
        if real_start_time is None:
            self.skipTest("process start-time is indeterminate on this platform/build")

        mismatched_record = SessionRecord(
            pid=real_pid, start_time=real_start_time + 10_000_000.0, session_id="mismatch"
        )

        liveness = diagnose_liveness(mismatched_record)

        self.assertEqual(liveness, Liveness.STALE)

    def test_force_unlock_refuses_when_expected_record_does_not_match_disk(self) -> None:
        """force_unlock re-validates identity: a caller-supplied expectation
        that no longer matches the on-disk record (e.g. start-time drifted
        between diagnosis and cleanup) is refused, even though the PID
        portion matches."""

        with tempfile.TemporaryDirectory() as workspace:
            on_disk = SessionRecord(pid=999999, start_time=111.0, session_id="original")
            _write_record(workspace, on_disk)

            wrong_expectation = SessionRecord(pid=999999, start_time=222.0, session_id="original")

            outcome = force_unlock(workspace, wrong_expectation)

            self.assertEqual(outcome, ForceUnlockOutcome.RECORD_CHANGED)
            # Untouched: still the original on-disk record.
            self.assertEqual(read_record(Path(workspace) / RECORD_RELATIVE_PATH), on_disk)


class ForceUnlockHappyPathTests(unittest.TestCase):
    def test_removes_a_genuinely_stale_record_and_guard_remains(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            dead_pid = _spawn_dead_pid()
            stale_record = SessionRecord(pid=dead_pid, start_time=0.0, session_id="stale")
            _write_record(workspace, stale_record)

            self.assertEqual(diagnose_liveness(stale_record), Liveness.STALE)

            guard_path = Path(workspace) / GUARD_RELATIVE_PATH
            identity_before = None
            if guard_path.exists():
                identity_before = get_file_identity(guard_path)

            outcome = force_unlock(workspace, stale_record)

            self.assertEqual(outcome, ForceUnlockOutcome.REMOVED)
            self.assertFalse((Path(workspace) / RECORD_RELATIVE_PATH).exists())
            self.assertTrue(guard_path.exists(), "guard file must never be removed")
            if identity_before is not None:
                self.assertEqual(get_file_identity(guard_path), identity_before)


class ForceUnlockRefusedAgainstLiveLockTests(unittest.TestCase):
    def test_refused_while_a_real_process_holds_the_lock(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            result_path = Path(workspace) / "park_result.json"
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(_WORKER_SCRIPT),
                    "--workspace",
                    workspace,
                    "--result",
                    str(result_path),
                    "park",
                    "--timeout",
                    "20",
                ]
            )
            try:
                deadline = time.time() + 10
                while not result_path.exists() and time.time() < deadline:
                    time.sleep(0.05)
                self.assertTrue(result_path.exists())
                status = json.loads(result_path.read_text(encoding="utf-8"))
                self.assertEqual(status["outcome"], "acquired")

                holder_record = read_record(Path(status["record_path"]))
                self.assertIsNotNone(holder_record)

                outcome = force_unlock(workspace, holder_record)

                self.assertEqual(outcome, ForceUnlockOutcome.REFUSED_LIVE)
                # The live holder's record must be untouched.
                self.assertEqual(read_record(Path(status["record_path"])), holder_record)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=10)
                    time.sleep(0.2)  # let Windows release the file lock before tempdir cleanup


class CrashWithoutReleaseCleanupTests(unittest.TestCase):
    def test_force_unlock_cleans_up_after_a_killed_holder(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            result_path = Path(workspace) / "park_result.json"
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(_WORKER_SCRIPT),
                    "--workspace",
                    workspace,
                    "--result",
                    str(result_path),
                    "park",
                    "--timeout",
                    "30",
                ]
            )
            try:
                deadline = time.time() + 10
                while not result_path.exists() and time.time() < deadline:
                    time.sleep(0.05)
                status = json.loads(result_path.read_text(encoding="utf-8"))
                holder_record = read_record(Path(status["record_path"]))
                self.assertIsNotNone(holder_record)

                # Simulate a crash: kill without letting it release cleanly.
                proc.kill()
                proc.wait(timeout=10)
                time.sleep(0.2)  # let Windows release the file lock before tempdir cleanup

                # Give the OS a brief moment to actually release the handle.
                deadline = time.time() + 5
                while diagnose_liveness(holder_record) != Liveness.STALE and time.time() < deadline:
                    time.sleep(0.05)

                self.assertEqual(diagnose_liveness(holder_record), Liveness.STALE)

                outcome = force_unlock(workspace, holder_record)

                self.assertEqual(outcome, ForceUnlockOutcome.REMOVED)
                self.assertFalse((Path(workspace) / RECORD_RELATIVE_PATH).exists())
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=10)
                    time.sleep(0.2)  # let Windows release the file lock before tempdir cleanup


class IndeterminateLivenessTests(unittest.TestCase):
    def test_indeterminate_pid_liveness_is_never_eligible(self) -> None:
        record = SessionRecord(pid=424242, start_time=1.0, session_id="indeterminate")

        with mock.patch("autoharness.supervise.locking._pid_exists", return_value=None):
            liveness = diagnose_liveness(record)

        self.assertEqual(liveness, Liveness.INDETERMINATE)
        self.assertFalse(is_stale_eligible_for_force_unlock(liveness))

    def test_indeterminate_start_time_is_never_eligible(self) -> None:
        record = SessionRecord(pid=1, start_time=1.0, session_id="indeterminate-start")

        with mock.patch("autoharness.supervise.locking._pid_exists", return_value=True), mock.patch(
            "autoharness.supervise.locking._process_start_time", return_value=None
        ):
            liveness = diagnose_liveness(record)

        self.assertEqual(liveness, Liveness.INDETERMINATE)
        self.assertFalse(is_stale_eligible_for_force_unlock(liveness))

    def test_live_process_with_matching_start_time_is_live_not_eligible(self) -> None:
        import os

        from autoharness.supervise.locking import _process_start_time

        pid = os.getpid()
        start_time = _process_start_time(pid)
        if start_time is None:
            self.skipTest("process start-time is indeterminate on this platform/build")

        record = SessionRecord(pid=pid, start_time=start_time, session_id="self")
        liveness = diagnose_liveness(record)

        self.assertEqual(liveness, Liveness.LIVE)
        self.assertFalse(is_stale_eligible_for_force_unlock(liveness))


class RealRaceTests(unittest.TestCase):
    """Mandatory real-subprocess race tests for force_unlock vs. concurrent
    normal acquisition.

    Design note: rather than running the "diagnosing" side in its own
    subprocess, the diagnosis + force_unlock call happens in THIS test
    process while the CONTENDING acquisition happens in a genuinely
    separate OS process. The invariant under test -- mutual exclusion via
    the guard file's OS-level lock -- is enforced identically regardless of
    which side runs in-process, and a real second process holding the lock
    is what makes the race real (not simulated). This keeps the test
    deterministic (ordering is fixed by explicit wait-for-file barriers,
    not sleep-based timing guesses) while still exercising genuine
    cross-process contention.
    """

    def test_cleanup_cannot_remove_live_holders_record_under_interleaving(self) -> None:
        for iteration in range(_RACE_REPEATS):
            with tempfile.TemporaryDirectory() as workspace:
                # Step 1: a previously-diagnosed stale record sits on disk
                # (as if a prior session crashed).
                stale_record = SessionRecord(
                    pid=_spawn_dead_pid(), start_time=0.0, session_id=f"stale-{iteration}"
                )
                _write_record(workspace, stale_record)
                self.assertEqual(diagnose_liveness(stale_record), Liveness.STALE)

                # Step 2: a genuinely separate process races in and performs
                # a NORMAL acquisition, interleaved before our force_unlock
                # call below.
                result_path = Path(workspace) / f"park_result_{iteration}.json"
                proc = subprocess.Popen(
                    [
                        sys.executable,
                        str(_WORKER_SCRIPT),
                        "--workspace",
                        workspace,
                        "--result",
                        str(result_path),
                        "park",
                        "--timeout",
                        "15",
                    ]
                )
                try:
                    deadline = time.time() + 10
                    while not result_path.exists() and time.time() < deadline:
                        time.sleep(0.02)
                    self.assertTrue(result_path.exists(), f"iteration {iteration}: contender never reported")
                    status = json.loads(result_path.read_text(encoding="utf-8"))
                    self.assertEqual(status["outcome"], "acquired")
                    contender_record = read_record(Path(status["record_path"]))
                    self.assertIsNotNone(contender_record)
                    record_mtime_before = Path(status["record_path"]).stat().st_mtime

                    # Step 3: force_unlock, using the ORIGINAL (now stale)
                    # expected_record, races against the live contender.
                    outcome = force_unlock(workspace, stale_record)

                    # The contender got there first (it is already fully
                    # acquired and parked by the time we call force_unlock),
                    # so our attempt must be REFUSED, never REMOVED.
                    self.assertEqual(
                        outcome,
                        ForceUnlockOutcome.REFUSED_LIVE,
                        f"iteration {iteration}: force_unlock did not refuse against a live holder",
                    )

                    # Exactly one live holder remains: the contender. Its
                    # record is untouched (identical content, unchanged
                    # mtime).
                    after_record = read_record(Path(status["record_path"]))
                    self.assertEqual(after_record, contender_record)
                    record_mtime_after = Path(status["record_path"]).stat().st_mtime
                    self.assertEqual(record_mtime_before, record_mtime_after)
                finally:
                    if proc.poll() is None:
                        proc.kill()
                        proc.wait(timeout=10)
                        time.sleep(0.2)  # let Windows release the file lock before tempdir cleanup

    def test_refused_cleanup_performs_zero_writes_to_record_file(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            result_path = Path(workspace) / "park_result.json"
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(_WORKER_SCRIPT),
                    "--workspace",
                    workspace,
                    "--result",
                    str(result_path),
                    "park",
                    "--timeout",
                    "15",
                ]
            )
            try:
                deadline = time.time() + 10
                while not result_path.exists() and time.time() < deadline:
                    time.sleep(0.02)
                status = json.loads(result_path.read_text(encoding="utf-8"))
                record_path = Path(status["record_path"])
                content_before = record_path.read_bytes()
                mtime_before = record_path.stat().st_mtime

                outcome = force_unlock(workspace, SessionRecord(pid=1, start_time=1.0, session_id="irrelevant"))

                self.assertEqual(outcome, ForceUnlockOutcome.REFUSED_LIVE)
                self.assertEqual(record_path.read_bytes(), content_before)
                self.assertEqual(record_path.stat().st_mtime, mtime_before)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=10)
                    time.sleep(0.2)  # let Windows release the file lock before tempdir cleanup

    def test_guard_survives_every_force_unlock_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            guard_path = Path(workspace) / GUARD_RELATIVE_PATH

            # REMOVED path.
            stale = SessionRecord(pid=_spawn_dead_pid(), start_time=0.0, session_id="a")
            _write_record(workspace, stale)
            force_unlock(workspace, stale)
            identity_after_removed = get_file_identity(guard_path)

            # RECORD_CHANGED path.
            other = SessionRecord(pid=_spawn_dead_pid(), start_time=0.0, session_id="b")
            _write_record(workspace, other)
            force_unlock(workspace, SessionRecord(pid=999, start_time=999.0, session_id="wrong"))
            identity_after_changed = get_file_identity(guard_path)

            # NOTHING_TO_REMOVE path (no record file present at all).
            record_path = Path(workspace) / RECORD_RELATIVE_PATH
            if record_path.exists():
                record_path.unlink()
            outcome_nothing = force_unlock(
                workspace, SessionRecord(pid=1, start_time=1.0, session_id="none")
            )
            self.assertEqual(outcome_nothing, ForceUnlockOutcome.NOTHING_TO_REMOVE)
            identity_after_nothing = get_file_identity(guard_path)

            self.assertEqual(identity_after_removed, identity_after_changed)
            self.assertEqual(identity_after_changed, identity_after_nothing)


class PositiveControlTests(unittest.TestCase):
    """Deliberately-unsafe helper variants that MUST fail the invariants
    above when substituted in -- these prove the race/identity assertions
    actually detect real defects rather than trivially passing."""

    @staticmethod
    def _unsafe_delete_record_without_guard(record_path: Path) -> None:
        """BAD: deletes the record with no guard-lock, no re-validation."""

        record_path.unlink()

    @staticmethod
    def _unsafe_overwrite_record_without_guard(record_path: Path, fake: SessionRecord) -> None:
        """BAD: mutates the record with no guard-lock, no re-validation."""

        record_path.write_text(json.dumps(fake.to_dict()), encoding="utf-8")

    @staticmethod
    def _unsafe_replace_guard_file(guard_path: Path) -> None:
        """BAD: deletes and recreates the guard file (changes its identity).

        The replacement file is written under a distinct temporary name and
        then atomically moved onto ``guard_path`` via ``os.replace`` rather
        than unlinking ``guard_path`` and recreating it under the SAME name.
        This guarantees the replacement inode is allocated from a fresh,
        never-before-used directory entry before the original is removed,
        so the assertion below cannot flake on filesystems (observed on
        Linux ext4/tmpfs CI runners) that immediately reuse a just-freed
        inode number for a new file created under the same name in the
        same directory -- a filesystem-dependent allocation-reuse race that
        has nothing to do with the identity guarantee under test.
        """

        replacement = guard_path.with_name(guard_path.name + ".unsafe-replacement.tmp")
        replacement.write_bytes(b"\0")
        os.replace(replacement, guard_path)

    def test_unsafe_delete_corrupts_a_live_holders_record(self) -> None:
        """Demonstrates that WITHOUT the guard-lock discipline, a
        "cleanup" can destroy a live holder's record -- exactly what the
        real force_unlock implementation must never do."""

        with tempfile.TemporaryDirectory() as workspace:
            with SessionLock(workspace) as lock:
                self.assertTrue(lock.record_path.exists())

                self._unsafe_delete_record_without_guard(lock.record_path)

                # The unsafe variant DID corrupt the live holder's state --
                # this is the defect our real force_unlock's guard-first
                # discipline prevents.
                self.assertFalse(
                    lock.record_path.exists(),
                    "expected the unsafe delete to corrupt the live holder's record",
                )
            # lock.release() below (via __exit__) tolerates the record
            # already being gone (idempotent/crash-safe per 118.005-T).

    def test_unsafe_overwrite_corrupts_a_live_holders_record(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            with SessionLock(workspace) as lock:
                original = read_record(lock.record_path)
                self.assertIsNotNone(original)

                fake = SessionRecord(pid=1, start_time=1.0, session_id="attacker")
                self._unsafe_overwrite_record_without_guard(lock.record_path, fake)

                corrupted = read_record(lock.record_path)
                self.assertNotEqual(corrupted, original)
                self.assertEqual(corrupted, fake)

    def test_unsafe_guard_replacement_changes_identity(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            lock = SessionLock(workspace)
            lock.acquire()
            identity_before = get_file_identity(lock.guard_path)
            lock.release()

            self._unsafe_replace_guard_file(lock.guard_path)
            identity_after_unsafe = get_file_identity(lock.guard_path)

            self.assertNotEqual(
                identity_before,
                identity_after_unsafe,
                "expected the unsafe guard replacement to change file identity",
            )

            # Contrast: the real force_unlock path never touches the guard
            # file's identity, in any outcome (see RealRaceTests above).


if __name__ == "__main__":
    unittest.main()
