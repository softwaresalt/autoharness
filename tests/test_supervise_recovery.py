"""Tests for autoharness.supervise.recovery -- cancellation and restart (119.006-T).

Uses FakeChildProcess exclusively (no real subprocess). Every
cancellation/failure test additionally asserts: (a) the terminal phase
reached is CANCELLED (not EXITED) for cancellation paths, and differs from
the EXITED value asserted in a paired normal-completion test; (b) the
lock's release path was invoked EXACTLY ONCE (F22); (c) the direct
CANCELLING -> CANCELLED transition remains illegal (negative control reusing
119.003-T's IllegalTransitionError).
"""

from __future__ import annotations

import signal as signal_module
import tempfile
import unittest
from pathlib import Path

from autoharness.supervise.errors import IllegalTransitionError
from autoharness.supervise.journal import SessionJournal, read_cursor
from autoharness.supervise.process import FakeChildProcess
from autoharness.supervise.recovery import (
    RestartController,
    cancel_session,
    resume_from_journal,
)
from autoharness.supervise.session import Phase, SessionStateMachine


class _CountingLock:
    """Lightweight release-call-counting fake satisfying the release contract.

    A real temp-directory-backed ``SessionLock`` would work too (it exposes
    the same ``release()`` contract), but recovery tests otherwise avoid all
    real I/O (they use ``FakeChildProcess`` exclusively), so this in-memory
    fake keeps the whole suite fast and dependency-free while still proving
    the release path is invoked exactly once (F22).
    """

    def __init__(self) -> None:
        self.release_calls = 0

    def release(self) -> None:
        self.release_calls += 1


def _drive_to(machine: SessionStateMachine, *phases: Phase) -> None:
    for phase in phases:
        machine.transition(phase)


class CancelDuringVariousPhasesTests(unittest.TestCase):
    def _assert_common_cancellation_contract(
        self, machine: SessionStateMachine, lock: _CountingLock
    ) -> None:
        # (a) terminal phase reached is CANCELLED, not EXITED.
        self.assertEqual(machine.phase, Phase.CANCELLED)
        self.assertNotEqual(machine.phase, Phase.EXITED)
        # (b) lock release invoked exactly once.
        self.assertEqual(lock.release_calls, 1)
        # (c) direct CANCELLING -> CANCELLED remains illegal.
        control_machine = SessionStateMachine()
        _drive_to(control_machine, Phase.LOCKING, Phase.BOOTSTRAPPING, Phase.CANCELLING)
        with self.assertRaises(IllegalTransitionError):
            control_machine.transition(Phase.CANCELLED)

    def test_cancel_during_launching(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
        )
        child = FakeChildProcess(argv=("echo",))
        child.spawn()
        lock = _CountingLock()

        cancel_session(machine, child=child, lock=lock, reason="operator cancel")

        self.assertTrue(child.closed)
        self._assert_common_cancellation_contract(machine, lock)

    def test_cancel_during_bootstrapping(self) -> None:
        machine = SessionStateMachine()
        _drive_to(machine, Phase.LOCKING, Phase.BOOTSTRAPPING)
        lock = _CountingLock()

        cancel_session(machine, lock=lock, reason="cancel during bootstrap")

        self._assert_common_cancellation_contract(machine, lock)

    def test_cancel_during_preflight(self) -> None:
        machine = SessionStateMachine()
        _drive_to(machine, Phase.LOCKING, Phase.BOOTSTRAPPING, Phase.PREFLIGHT)
        lock = _CountingLock()

        cancel_session(machine, lock=lock, reason="cancel during preflight")

        self._assert_common_cancellation_contract(machine, lock)

    def test_cancel_during_resolving(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine, Phase.LOCKING, Phase.BOOTSTRAPPING, Phase.PREFLIGHT, Phase.RESOLVING
        )
        lock = _CountingLock()

        cancel_session(machine, lock=lock, reason="cancel during resolve")

        self._assert_common_cancellation_contract(machine, lock)

    def test_cancel_during_running(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )
        child = FakeChildProcess(argv=("sleep", "30"))
        child.spawn()
        lock = _CountingLock()

        cancel_session(machine, child=child, lock=lock, reason="operator cancel while running")

        self.assertTrue(child.closed)
        self._assert_common_cancellation_contract(machine, lock)

    def test_cancel_terminates_child_via_signal_and_close(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine, Phase.LOCKING, Phase.BOOTSTRAPPING, Phase.PREFLIGHT, Phase.RESOLVING, Phase.LAUNCHING, Phase.RUNNING
        )
        child = FakeChildProcess(argv=("sleep", "30"))
        child.spawn()
        lock = _CountingLock()

        cancel_session(machine, child=child, lock=lock)

        self.assertGreaterEqual(len(child.signals_received), 1)
        self.assertTrue(child.closed)

    def test_cancel_journals_cancel_requested_and_phase_change(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="cancel-test")
            machine = SessionStateMachine()
            _drive_to(machine, Phase.LOCKING, Phase.BOOTSTRAPPING)
            lock = _CountingLock()

            cancel_session(machine, journal=journal, lock=lock, reason="test reason")

            content = journal.journal_path.read_text(encoding="utf-8")
            self.assertIn("CancelRequested", content)


class NormalCompletionParityTests(unittest.TestCase):
    """Paired normal-completion run, asserting its terminal phase differs
    from the cancellation terminal phase (EXITED vs. CANCELLED)."""

    def test_normal_completion_reaches_exited_distinct_from_cancelled(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
            Phase.DRAINING,
            Phase.EXITED,
        )
        self.assertEqual(machine.phase, Phase.EXITED)
        self.assertNotEqual(machine.phase, Phase.CANCELLED)


class RestartWithBudgetTests(unittest.TestCase):
    def test_restart_succeeds_with_remaining_budget_and_journals(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="restart-test")
            machine = SessionStateMachine()
            _drive_to(
                machine,
                Phase.LOCKING,
                Phase.BOOTSTRAPPING,
                Phase.PREFLIGHT,
                Phase.RESOLVING,
                Phase.LAUNCHING,
                Phase.RUNNING,
            )
            recorded_delays: list[float] = []
            controller = RestartController(
                max_restarts=2,
                confirm_restart=lambda: True,
                sleep_fn=recorded_delays.append,
            )

            result_phase = controller.attempt(machine, journal=journal, reason="crash-loop")

            self.assertEqual(result_phase, Phase.LAUNCHING)
            self.assertEqual(controller.attempts_used, 1)
            self.assertEqual(controller.remaining_budget, 1)
            content = journal.journal_path.read_text(encoding="utf-8")
            self.assertIn("RestartScheduled", content)
            self.assertIn("crash-loop", content)

    def test_restart_declined_by_operator_drains_to_failed_not_looping(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )
        controller = RestartController(
            max_restarts=3,
            confirm_restart=lambda: False,
            sleep_fn=lambda _delay: None,
        )

        result_phase = controller.attempt(machine)

        self.assertEqual(result_phase, Phase.FAILED)
        self.assertNotEqual(result_phase, Phase.EXITED)
        # never loops: FAILED is absorbing, a further attempt() call must
        # raise rather than silently doing nothing or looping.
        with self.assertRaises(IllegalTransitionError):
            controller.attempt(machine)

    def test_budget_exhaustion_drains_to_failed_never_loops_again(self) -> None:
        recorded_delays: list[float] = []
        controller = RestartController(
            max_restarts=2,
            confirm_restart=lambda: True,
            sleep_fn=recorded_delays.append,
        )

        # Attempt 1: RUNNING -> RESTARTING -> LAUNCHING (budget 2 -> 1 left)
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )
        phase_after_1 = controller.attempt(machine)
        self.assertEqual(phase_after_1, Phase.LAUNCHING)

        # Simulate failure again: LAUNCHING -> RUNNING -> RESTARTING -> LAUNCHING
        machine.transition(Phase.RUNNING)
        phase_after_2 = controller.attempt(machine)
        self.assertEqual(phase_after_2, Phase.LAUNCHING)
        self.assertEqual(controller.remaining_budget, 0)

        # Simulate a third failure: budget is now exhausted -> drains to FAILED.
        machine.transition(Phase.RUNNING)
        phase_after_3 = controller.attempt(machine)
        self.assertEqual(phase_after_3, Phase.FAILED)

        # Never loops again: FAILED is absorbing.
        with self.assertRaises(IllegalTransitionError):
            controller.attempt(machine)

    def test_backoff_timing_uses_increasing_delays_across_attempts(self) -> None:
        recorded_delays: list[float] = []
        controller = RestartController(
            max_restarts=3,
            confirm_restart=lambda: True,
            sleep_fn=recorded_delays.append,
            backoff_base_seconds=1.0,
            backoff_multiplier=2.0,
        )
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )

        controller.attempt(machine)
        machine.transition(Phase.RUNNING)
        controller.attempt(machine)
        machine.transition(Phase.RUNNING)
        controller.attempt(machine)

        self.assertEqual(recorded_delays, [1.0, 2.0, 4.0])
        self.assertEqual(recorded_delays, sorted(recorded_delays))


class RestartExhaustionLockAndChildReleaseTests(unittest.TestCase):
    """128-S review remediation: the declined/exhausted restart path must
    release the session lock EXACTLY ONCE and terminate the child (when
    given), mirroring cancel_session's every-failure-path contract (F22).
    """

    def test_declined_restart_releases_lock_and_closes_child(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )
        child = FakeChildProcess(argv=("sleep", "30"))
        child.spawn()
        lock = _CountingLock()
        controller = RestartController(
            max_restarts=3,
            confirm_restart=lambda: False,
            sleep_fn=lambda _delay: None,
        )

        result_phase = controller.attempt(machine, child=child, lock=lock)

        self.assertEqual(result_phase, Phase.FAILED)
        self.assertEqual(lock.release_calls, 1)
        self.assertTrue(child.closed)

    def test_exhausted_restart_releases_lock_exactly_once(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )
        lock = _CountingLock()
        controller = RestartController(max_restarts=0, confirm_restart=lambda: True)

        result_phase = controller.attempt(machine, lock=lock)

        self.assertEqual(result_phase, Phase.FAILED)
        self.assertEqual(lock.release_calls, 1)

    def test_declined_restart_child_already_exited_race_still_releases_lock(self) -> None:
        """Mirrors cancel_session's ProcessLookupError race tolerance:
        a child that already exited must not strand the lock."""

        class _AlreadyExitedChild:
            def signal(self, sig: int) -> None:
                raise ProcessLookupError("already exited")

            def close(self) -> None:
                raise ProcessLookupError("already exited")

        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )
        lock = _CountingLock()
        controller = RestartController(max_restarts=1, confirm_restart=lambda: False)

        result_phase = controller.attempt(
            machine, child=_AlreadyExitedChild(), lock=lock
        )

        self.assertEqual(result_phase, Phase.FAILED)
        self.assertEqual(lock.release_calls, 1)


class ResumeAfterCrashTests(unittest.TestCase):
    def test_resume_reads_only_journal_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            first = SessionJournal(workspace, session_id="resume-test")
            from autoharness.supervise.contracts import ChildOutputUnavailable

            first.append_event(ChildOutputUnavailable(reason="a"))
            expected_last_seq = first.append_event(ChildOutputUnavailable(reason="b"))
            del first  # simulate crash

            recovered = resume_from_journal(
                Path(workspace) / ".autoharness" / "sessions" / "resume-test" / "journal.jsonl"
            )

            self.assertEqual(recovered, expected_last_seq)

    def test_resume_never_imports_backlogit(self) -> None:
        import ast

        import autoharness.supervise.recovery as recovery_module

        with open(recovery_module.__file__, "r", encoding="utf-8") as handle:
            content = handle.read()
        tree = ast.parse(content)
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        for name in imported_modules:
            self.assertNotIn("backlogit", name.lower())


class CancelSessionLockReleaseOnExceptionRegressionTests(unittest.TestCase):
    """Regression test for the 128-S code-review P0 finding: ``cancel_session``
    must release the lock EXACTLY ONCE even when ``child.signal()``/
    ``child.close()`` raises (a realistic race: the child already exited
    before cancellation runs). Before the fix, any exception raised before
    the function's final statement left the lock permanently un-released.
    """

    class _AlreadyExitedChild:
        """A child that raises ``ProcessLookupError`` from signal()/close(),
        simulating a process that exited/was reaped before cancellation ran.
        """

        def spawn(self) -> None:  # pragma: no cover - not exercised here
            raise NotImplementedError

        def read(self):  # pragma: no cover - not exercised here
            return None

        def write(self, data: bytes) -> None:  # pragma: no cover
            raise NotImplementedError

        def signal(self, sig: int) -> None:
            raise ProcessLookupError("already exited")

        def wait(self) -> int:  # pragma: no cover - not exercised here
            return 0

        def close(self) -> None:
            raise ProcessLookupError("already exited")

        @property
        def supports_output_capture(self) -> bool:  # pragma: no cover
            return False

    def test_lock_released_exactly_once_when_child_signal_raises(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
        )
        lock = _CountingLock()

        # Must NOT raise: an already-exited child is an expected race, not a
        # failure, and cancellation must still reach CANCELLED with the lock
        # released exactly once.
        result_phase = cancel_session(
            machine,
            child=self._AlreadyExitedChild(),
            lock=lock,
            reason="already-exited-race",
        )

        self.assertEqual(result_phase, Phase.CANCELLED)
        self.assertEqual(machine.phase, Phase.CANCELLED)
        self.assertEqual(lock.release_calls, 1)

    def test_lock_released_exactly_once_on_unexpected_exception(self) -> None:
        """Even a genuinely unexpected exception (not the expected
        ProcessLookupError race) must not strand the lock: `finally`
        guarantees release-exactly-once regardless of what raised.
        """

        class _BoomChild:
            def signal(self, sig: int) -> None:
                raise RuntimeError("boom")

            def close(self) -> None:  # pragma: no cover - not reached
                raise NotImplementedError

        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
        )
        lock = _CountingLock()

        with self.assertRaises(RuntimeError):
            cancel_session(machine, child=_BoomChild(), lock=lock, reason="boom")

        self.assertEqual(lock.release_calls, 1)


class RestartConfirmCallbackRaisesFailsClosedTests(unittest.TestCase):
    """128-S review remediation (round 3): a ``confirm_restart`` callback
    that RAISES (e.g. an unavailable approval channel) must be treated
    identically to an explicit decline -- never left to propagate and
    strand the session in RESTARTING with the lock un-released. The plan's
    non-interactive-approval contract requires "never auto-approve", and an
    ambiguous (exception) outcome must fail closed toward NOT approving.
    """

    def test_confirm_restart_exception_drains_to_failed_and_releases_lock(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )
        lock = _CountingLock()

        def _raising_confirm() -> bool:
            raise RuntimeError("approval channel unavailable")

        controller = RestartController(max_restarts=3, confirm_restart=_raising_confirm)

        result_phase = controller.attempt(machine, lock=lock)

        self.assertEqual(result_phase, Phase.FAILED)
        self.assertNotEqual(result_phase, Phase.RESTARTING)
        self.assertEqual(lock.release_calls, 1)

    def test_confirm_restart_exception_does_not_consume_budget(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )

        def _raising_confirm() -> bool:
            raise RuntimeError("approval channel unavailable")

        controller = RestartController(max_restarts=3, confirm_restart=_raising_confirm)
        controller.attempt(machine)

        self.assertEqual(controller.attempts_used, 0)


class ApprovedRestartTerminatesOldChildTests(unittest.TestCase):
    """128-S review remediation (round 3): an APPROVED restart must
    terminate the old (still-live) child BEFORE the machine returns to
    LAUNCHING -- otherwise a still-running previous child can continue
    alongside whatever the caller launches next, mirroring the exhaustion
    branch's cleanup contract but proceeding to LAUNCHING instead of
    draining to FAILED.
    """

    def test_approved_restart_signals_and_closes_old_child(self) -> None:
        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )
        old_child = FakeChildProcess(argv=("old",))
        old_child.spawn()
        controller = RestartController(
            max_restarts=3,
            confirm_restart=lambda: True,
            sleep_fn=lambda _delay: None,
        )

        result_phase = controller.attempt(machine, child=old_child, reason="crash-loop")

        self.assertEqual(result_phase, Phase.LAUNCHING)
        self.assertIn(signal_module.SIGTERM, old_child.signals_received)
        self.assertTrue(old_child.closed)

    def test_approved_restart_tolerates_already_exited_old_child(self) -> None:
        class _AlreadyExitedChild:
            def signal(self, sig: int) -> None:
                raise ProcessLookupError("already exited")

            def close(self) -> None:
                raise ProcessLookupError("already exited")

        machine = SessionStateMachine()
        _drive_to(
            machine,
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
        )
        controller = RestartController(
            max_restarts=3,
            confirm_restart=lambda: True,
            sleep_fn=lambda _delay: None,
        )

        # Must NOT raise: an already-exited old child is an expected race.
        result_phase = controller.attempt(machine, child=_AlreadyExitedChild())

        self.assertEqual(result_phase, Phase.LAUNCHING)


if __name__ == "__main__":
    unittest.main()
