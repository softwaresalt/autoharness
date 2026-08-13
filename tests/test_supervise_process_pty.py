"""Tests for autoharness.supervise.process_pty -- the PTY backend (119.002-T).

Covers guarded-import behavior (degrade to InheritStdio, never to Pipe),
exit-code fidelity where a real PTY can be constructed, and the
factory-warning contract (populated exactly when degraded).
"""

from __future__ import annotations

import sys
import unittest
import unittest.mock

from autoharness.supervise.process import InheritStdioChildProcess, PipeChildProcess
from autoharness.supervise.process_pty import (
    PtyChildProcess,
    create_pty_or_inherited_child_process,
)

_PY = sys.executable
_IS_POSIX = sys.platform != "win32"


class DegradeToInheritedStdioTests(unittest.TestCase):
    def test_degrades_to_inherit_stdio_when_pty_construction_fails(self) -> None:
        with unittest.mock.patch(
            "autoharness.supervise.process_pty._try_construct_pty_backend",
            return_value=None,
        ):
            child, warning = create_pty_or_inherited_child_process([_PY, "-c", "pass"])

        self.assertIsInstance(child, InheritStdioChildProcess)
        self.assertNotIsInstance(child, PipeChildProcess)
        self.assertIsNotNone(warning)
        self.assertIsInstance(warning, str)

    def test_never_degrades_to_pipe_backend(self) -> None:
        # Simulate total unavailability (no pty module, no pywinpty) and
        # assert the degrade target is specifically InheritStdio, not Pipe.
        with unittest.mock.patch(
            "autoharness.supervise.process_pty._try_construct_pty_backend",
            side_effect=OSError("pty unavailable"),
        ):
            child, warning = create_pty_or_inherited_child_process([_PY, "-c", "pass"])

        self.assertIsInstance(child, InheritStdioChildProcess)
        self.assertIsNotNone(warning)

    def test_supports_output_capture_false_when_degraded(self) -> None:
        with unittest.mock.patch(
            "autoharness.supervise.process_pty._try_construct_pty_backend",
            return_value=None,
        ):
            child, _warning = create_pty_or_inherited_child_process([_PY, "-c", "pass"])

        self.assertFalse(child.supports_output_capture)


class WarningPopulationContractTests(unittest.TestCase):
    def test_warning_is_none_when_real_backend_constructed(self) -> None:
        fake_backend = unittest.mock.MagicMock(spec=PtyChildProcess)
        fake_backend.supports_output_capture = True
        with unittest.mock.patch(
            "autoharness.supervise.process_pty._try_construct_pty_backend",
            return_value=fake_backend,
        ):
            child, warning = create_pty_or_inherited_child_process([_PY, "-c", "pass"])

        self.assertIs(child, fake_backend)
        self.assertIsNone(warning)

    def test_warning_is_a_non_empty_string_when_degraded(self) -> None:
        with unittest.mock.patch(
            "autoharness.supervise.process_pty._try_construct_pty_backend",
            return_value=None,
        ):
            _child, warning = create_pty_or_inherited_child_process([_PY, "-c", "pass"])

        self.assertTrue(warning)


@unittest.skipUnless(_IS_POSIX, "real PTY construction exercised via stdlib pty on POSIX only")
class RealPtyExitCodeFidelityTests(unittest.TestCase):
    def test_exit_code_round_trip_over_table(self) -> None:
        for code in (0, 1, 2, 42, 130):
            with self.subTest(code=code):
                proc = PtyChildProcess([_PY, "-c", f"import sys; sys.exit({code})"])
                proc.spawn()
                result = proc.wait()
                proc.close()
                self.assertEqual(result, code)

    def test_supports_output_capture_true_on_real_pty(self) -> None:
        proc = PtyChildProcess([_PY, "-c", "pass"])
        self.assertTrue(proc.supports_output_capture)

    def test_close_reaps_still_running_child_without_zombie(self) -> None:
        """128-S review remediation: close() called on a still-running child
        (no prior wait()) must terminate AND reap it, avoiding a zombie --
        previously close() only closed the master fd.
        """

        import os as _os

        proc = PtyChildProcess([_PY, "-c", "import time; time.sleep(30)"])
        proc.spawn()
        pid = proc.pid
        proc.close()
        # Poll (non-blocking) for the child: if it were an unreaped zombie
        # or still running, waitpid(WNOHANG) would return (0, 0) (still
        # there) rather than raising ChildProcessError (already reaped).
        with self.assertRaises(ChildProcessError):
            _os.waitpid(pid, _os.WNOHANG)

    def test_close_does_not_sigkill_after_childprocesserror_from_wait(self) -> None:
        """128-S review remediation (round 3): ChildProcessError from
        ``wait()`` means this PID is no longer OUR waitable child (already
        reaped by something else) -- NOT that it is still running. close()
        must not conflate this with TimeoutError and send SIGKILL to a bare
        PID number that the OS may have already reused for an unrelated
        process.
        """

        proc = PtyChildProcess([_PY, "-c", "pass"])
        proc.spawn()
        proc._pid = 999999  # noqa: SLF001 - simulate an already-reaped PID
        proc._exit_code = None

        kill_calls: list[tuple[int, int]] = []
        real_kill = __import__("os").kill

        def _fake_kill(pid: int, sig: int) -> None:
            kill_calls.append((pid, sig))
            if pid == 999999:
                raise ProcessLookupError("no such process")
            real_kill(pid, sig)

        def _fake_wait(timeout=None):  # noqa: ANN001
            raise ChildProcessError("no such waitable child")

        with unittest.mock.patch("os.kill", side_effect=_fake_kill):
            with unittest.mock.patch.object(proc, "wait", side_effect=_fake_wait):
                proc.close()

        # SIGTERM was attempted once; SIGKILL must NEVER have been sent,
        # since ChildProcessError is not evidence the child is still alive.
        import signal as _signal

        sigkill_calls = [c for c in kill_calls if c[1] == _signal.SIGKILL]
        self.assertEqual(sigkill_calls, [])


class GuardedImportAvailabilityTests(unittest.TestCase):
    def test_pty_module_unavailable_signals_unavailable_not_raise(self) -> None:
        with unittest.mock.patch("autoharness.supervise.process_pty._posix_pty_available", return_value=False):
            with unittest.mock.patch("autoharness.supervise.process_pty._winpty_available", return_value=False):
                # Must not raise merely because PTY is unavailable.
                child, warning = create_pty_or_inherited_child_process([_PY, "-c", "pass"])
        self.assertIsInstance(child, InheritStdioChildProcess)
        self.assertIsNotNone(warning)


class WinPtyExitStatusFidelityTests(unittest.TestCase):
    """128-S review remediation: pywinpty reporting ``exitstatus=None`` after
    the child is no longer alive must NEVER be silently mapped to ``0``
    (fabricating a successful exit) -- H3 exit-status fidelity is a hard
    invariant. Uses a mocked ``pywinpty`` module so this is testable without
    the optional dependency installed.
    """

    def test_wait_raises_rather_than_fabricating_zero_when_exitstatus_unavailable(
        self,
    ) -> None:
        from autoharness.supervise.process_pty import WinPtyChildProcess

        fake_pty = unittest.mock.MagicMock()
        fake_pty.isalive.return_value = False
        fake_pty.exitstatus = None

        proc = WinPtyChildProcess([_PY, "-c", "pass"])
        proc._pty = fake_pty  # noqa: SLF001 - test introspection only

        with self.assertRaises(RuntimeError):
            proc.wait()

    def test_wait_returns_real_exit_code_when_available(self) -> None:
        from autoharness.supervise.process_pty import WinPtyChildProcess

        fake_pty = unittest.mock.MagicMock()
        fake_pty.isalive.return_value = False
        fake_pty.exitstatus = 42

        proc = WinPtyChildProcess([_PY, "-c", "pass"])
        proc._pty = fake_pty  # noqa: SLF001 - test introspection only

        self.assertEqual(proc.wait(), 42)


class WinPtyCloseTerminatesLiveChildTests(unittest.TestCase):
    """128-S review remediation (round 3): close() must terminate/wait for
    a still-alive child before releasing the handle, mirroring every other
    backend's close() in this package, and must never leak the handle
    reference even if the underlying close() call raises.
    """

    def test_close_terminates_and_waits_for_live_child_before_closing(self) -> None:
        from autoharness.supervise.process_pty import WinPtyChildProcess

        alive_sequence = [True, True, False]
        fake_pty = unittest.mock.MagicMock()
        fake_pty.isalive.side_effect = lambda: alive_sequence.pop(0) if alive_sequence else False

        proc = WinPtyChildProcess([_PY, "-c", "pass"])
        proc._pty = fake_pty  # noqa: SLF001 - test introspection only

        proc.close()

        fake_pty.terminate.assert_called_once_with(force=True)
        fake_pty.close.assert_called_once()
        self.assertIsNone(proc._pty)  # noqa: SLF001 - test introspection only

    def test_close_clears_handle_even_when_underlying_close_raises(self) -> None:
        from autoharness.supervise.process_pty import WinPtyChildProcess

        fake_pty = unittest.mock.MagicMock()
        fake_pty.isalive.return_value = False
        fake_pty.close.side_effect = RuntimeError("boom")

        proc = WinPtyChildProcess([_PY, "-c", "pass"])
        proc._pty = fake_pty  # noqa: SLF001 - test introspection only

        proc.close()  # must not raise

        self.assertIsNone(proc._pty)  # noqa: SLF001 - test introspection only

    def test_close_on_already_dead_child_never_calls_terminate(self) -> None:
        from autoharness.supervise.process_pty import WinPtyChildProcess

        fake_pty = unittest.mock.MagicMock()
        fake_pty.isalive.return_value = False

        proc = WinPtyChildProcess([_PY, "-c", "pass"])
        proc._pty = fake_pty  # noqa: SLF001 - test introspection only

        proc.close()

        fake_pty.terminate.assert_not_called()
        fake_pty.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
