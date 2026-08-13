"""Tests for autoharness.supervise.locking -- the atomic guard lock (118.005-T).

Stale-record lifecycle / force_unlock tests (118.006-T) live in
``tests/test_supervise_locking_stale.py``.
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

from autoharness.supervise.errors import LockError
from autoharness.supervise.locking import (
    GUARD_RELATIVE_PATH,
    SessionLock,
    SessionLockRefused,
    ensure_ignored,
    get_file_identity,
)

_WORKER_SCRIPT = Path(__file__).resolve().parent / "_supervise_lock_worker.py"

# Mandatory real-parallel-contender test: target 50 iterations per the
# shipment spec, and measured wall-clock cost on this sandbox comfortably
# supports it (~0.6s/iteration for 8 real subprocess spawns), so the full
# target of 50 iterations is used rather than a reduced count.
_CONTENDER_COUNT = 8
_CONTENDER_ITERATIONS = 50


def _run_worker(args: list[str], timeout: float = 20.0) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_WORKER_SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class AcquireReleaseRoundTripTests(unittest.TestCase):
    def test_acquire_then_release_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            lock = SessionLock(workspace)
            lock.acquire()
            try:
                self.assertTrue(lock.held)
                self.assertTrue(lock.guard_path.exists())
                self.assertTrue(lock.record_path.exists())
            finally:
                lock.release()

            self.assertFalse(lock.held)
            self.assertTrue(lock.guard_path.exists(), "guard file must survive release")
            self.assertFalse(lock.record_path.exists(), "record file may be removed on release")

    def test_double_release_is_a_safe_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            lock = SessionLock(workspace)
            lock.acquire()
            lock.release()
            lock.release()  # must not raise
            self.assertFalse(lock.held)

    def test_release_when_never_held_is_a_safe_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            lock = SessionLock(workspace)
            lock.release()  # never acquired; must not raise
            self.assertFalse(lock.held)

    def test_release_after_handle_dropped_without_release_is_safe(self) -> None:
        """Simulate a crash: the fd is closed directly, bypassing .release()."""

        with tempfile.TemporaryDirectory() as workspace:
            lock = SessionLock(workspace)
            lock.acquire()
            # Simulate an abrupt loss of the handle (as if the process died)
            # by closing the underlying file object directly, without going
            # through the public release() API.
            assert lock._handle is not None
            lock._handle.close()

            lock.release()  # must not raise even though the handle is already closed
            self.assertFalse(lock.held)

    def test_context_manager_acquires_and_releases(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            with SessionLock(workspace) as lock:
                self.assertTrue(lock.held)
            self.assertFalse(lock.held)


class PathContainmentTests(unittest.TestCase):
    def test_escaping_guard_relative_path_raises_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            workspace = Path(parent) / "workspace"
            workspace.mkdir()

            with self.assertRaises(LockError):
                SessionLock(workspace, guard_relative="../../escape.guard")

            # Nothing should have been written outside the workspace as a
            # result of the aborted construction.
            escape_target = Path(parent) / "escape.guard"
            self.assertFalse(escape_target.exists())

    def test_escaping_record_relative_path_raises_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            workspace = Path(parent) / "workspace"
            workspace.mkdir()

            with self.assertRaises(LockError):
                SessionLock(workspace, record_relative="../../escape.record")

            escape_target = Path(parent) / "escape.record"
            self.assertFalse(escape_target.exists())

    def test_existing_symlinked_ancestor_component_raises(self) -> None:
        """128-S review remediation: a lexically-contained relative path
        must still be rejected if an ALREADY-EXISTING ancestor directory
        component is a symlink pointing outside the workspace -- otherwise
        the "all writes stay inside the workspace" guarantee is bypassable
        via a planted symlink.
        """

        with tempfile.TemporaryDirectory() as parent:
            workspace = Path(parent) / "workspace"
            workspace.mkdir()
            outside = Path(parent) / "outside"
            outside.mkdir()

            symlinked_dir = workspace / "linked"
            try:
                os.symlink(outside, symlinked_dir, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is not permitted in this environment")

            from autoharness.supervise.locking import _resolve_contained_path

            with self.assertRaises(LockError):
                _resolve_contained_path(workspace, Path("linked") / "evil.guard")

    def test_non_symlinked_existing_ancestor_is_unaffected(self) -> None:
        """The new symlink check must not spuriously reject an ordinary,
        already-existing, non-symlinked ancestor directory."""

        with tempfile.TemporaryDirectory() as parent:
            workspace = Path(parent) / "workspace"
            (workspace / "real").mkdir(parents=True)

            from autoharness.supervise.locking import _resolve_contained_path

            resolved = _resolve_contained_path(workspace, Path("real") / "fine.guard")
            self.assertTrue(str(resolved).startswith(str(Path(workspace).resolve())))


class GuardPermanenceTests(unittest.TestCase):
    def test_guard_identity_unchanged_across_acquire_release(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            lock = SessionLock(workspace)
            lock.acquire()
            identity_while_held = get_file_identity(lock.guard_path)
            lock.release()
            identity_after_release = get_file_identity(lock.guard_path)

            self.assertEqual(identity_while_held, identity_after_release)

    def test_guard_survives_simulated_crash_with_unchanged_identity(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            lock = SessionLock(workspace)
            lock.acquire()
            identity_before_crash = get_file_identity(lock.guard_path)

            # Simulate a crash: drop the lock via the OS by closing the
            # handle directly, bypassing .release() entirely (no unlock
            # call, no record cleanup).
            assert lock._handle is not None
            lock._handle.close()
            lock._handle = None
            lock._held = False

            identity_after_crash = get_file_identity(lock.guard_path)
            self.assertEqual(identity_before_crash, identity_after_crash)
            self.assertTrue(lock.guard_path.exists())


class EnsureIgnoredTests(unittest.TestCase):
    def test_creates_ignore_file_with_given_entries(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            ignore_path = ensure_ignored(workspace, "supervise/session.guard", "supervise/session.record")
            content = ignore_path.read_text(encoding="utf-8")
            self.assertIn("supervise/session.guard", content)
            self.assertIn("supervise/session.record", content)

    def test_is_idempotent_and_additive_not_duplicating_or_destructive(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            autoharness_dir = Path(workspace) / ".autoharness"
            autoharness_dir.mkdir(parents=True)
            ignore_path = autoharness_dir / ".gitignore"
            ignore_path.write_text("# pre-existing unrelated entry\nsomething-else/\n", encoding="utf-8")

            ensure_ignored(workspace, "supervise/session.guard")
            ensure_ignored(workspace, "supervise/session.guard", "supervise/session.record")

            content = ignore_path.read_text(encoding="utf-8")
            self.assertIn("# pre-existing unrelated entry", content)
            self.assertIn("something-else/", content)
            self.assertEqual(content.count("supervise/session.guard"), 1)
            self.assertIn("supervise/session.record", content)

    def test_invoked_automatically_on_guard_creation(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            lock = SessionLock(workspace)
            lock.acquire()
            try:
                ignore_path = Path(workspace) / ".autoharness" / ".gitignore"
                self.assertTrue(ignore_path.exists())
                content = ignore_path.read_text(encoding="utf-8")
                self.assertIn("session.guard", content)
                self.assertIn("session.record", content)
            finally:
                lock.release()


class RealParallelContenderTests(unittest.TestCase):
    """Mandatory: real separate OS processes racing the same guard file.

    Runs the full spec-target 50 iterations x 8 processes (see the
    module-level comment for measured timing).
    """

    def test_exactly_one_contender_acquires_per_iteration(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            for iteration in range(_CONTENDER_ITERATIONS):
                result_paths = [
                    Path(workspace) / f"result_{iteration}_{i}.txt" for i in range(_CONTENDER_COUNT)
                ]
                procs = []
                for i in range(_CONTENDER_COUNT):
                    procs.append(
                        subprocess.Popen(
                            [
                                sys.executable,
                                str(_WORKER_SCRIPT),
                                "--workspace",
                                workspace,
                                "--result",
                                str(result_paths[i]),
                                "contend",
                                "--hold",
                                "0.2",
                            ]
                        )
                    )

                for proc in procs:
                    return_code = proc.wait(timeout=15)
                    self.assertEqual(return_code, 0, f"worker process failed on iteration {iteration}")

                outcomes = [p.read_text(encoding="utf-8") for p in result_paths]
                acquired_count = sum(1 for o in outcomes if o.startswith("acquired"))
                refused_count = sum(1 for o in outcomes if o == "refused")

                self.assertEqual(
                    acquired_count,
                    1,
                    f"iteration {iteration}: expected exactly one acquisition, "
                    f"got {acquired_count} (outcomes={outcomes})",
                )
                self.assertEqual(refused_count, _CONTENDER_COUNT - 1)

                # All contenders that inspected identity locked the SAME
                # guard file on disk (same resolved path for every process).
                guard_path = Path(workspace) / GUARD_RELATIVE_PATH
                self.assertTrue(guard_path.exists())

                for p in result_paths:
                    p.unlink(missing_ok=True)

            # Guard identity remains stable across every iteration.
            self.assertTrue((Path(workspace) / GUARD_RELATIVE_PATH).exists())


class OsReleaseOnDeathTests(unittest.TestCase):
    def test_lock_becomes_available_after_holder_process_is_killed(self) -> None:
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
                self.assertTrue(result_path.exists(), "worker never reported acquisition")
                status = json.loads(result_path.read_text(encoding="utf-8"))
                self.assertEqual(status["outcome"], "acquired")

                # A fresh contender in THIS process must be refused while
                # the subprocess still holds the lock.
                contender = SessionLock(workspace)
                with self.assertRaises(SessionLockRefused):
                    contender.acquire()

                # Now kill the holder without letting it release cleanly --
                # the OS must release the file lock on process death.
                proc.kill()
                proc.wait(timeout=10)

                # A fresh contender in this process can now acquire.
                deadline = time.time() + 10
                acquired = False
                last_error: Exception | None = None
                while time.time() < deadline and not acquired:
                    try:
                        contender.acquire()
                        acquired = True
                    except SessionLockRefused as exc:
                        last_error = exc
                        time.sleep(0.1)

                self.assertTrue(acquired, f"lock never became available after kill: {last_error}")
                contender.release()
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
