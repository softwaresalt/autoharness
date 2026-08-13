"""Tests for autoharness.supervise.process -- the ChildProcess protocol (119.001-T).

Covers argv fidelity, the no-shell invariant, real-subprocess exit-code
round-tripping, stream capture on the Pipe backend, signal/terminate
handling, reaping without zombies, and the TTY-attachment-fidelity contract
for the inherit-stdio backend.
"""

from __future__ import annotations

import signal
import subprocess
import sys
import unittest
import unittest.mock

from autoharness.supervise.process import (
    FakeChildProcess,
    InheritStdioChildProcess,
    OutputCaptureUnavailable,
    PipeChildProcess,
)

_PY = sys.executable


class ArgvFidelityTests(unittest.TestCase):
    def test_pipe_backend_stores_argv_as_tuple_verbatim(self) -> None:
        argv = [_PY, "-c", "pass"]
        proc = PipeChildProcess(argv)
        self.assertEqual(proc.argv, tuple(argv))
        self.assertIsInstance(proc.argv, tuple)

    def test_inherit_backend_stores_argv_as_tuple_verbatim(self) -> None:
        argv = [_PY, "-c", "pass"]
        proc = InheritStdioChildProcess(argv)
        self.assertEqual(proc.argv, tuple(argv))
        self.assertIsInstance(proc.argv, tuple)

    def test_no_reinterpolation_argv_forwarded_verbatim(self) -> None:
        # An argument containing shell metacharacters must be forwarded
        # exactly as one argv element -- never re-joined/re-quoted/re-parsed.
        argv = [_PY, "-c", "import sys; sys.exit(0)", "arg with spaces; && $(evil)"]
        proc = PipeChildProcess(argv)
        self.assertEqual(proc.argv[-1], "arg with spaces; && $(evil)")


class NoShellAssertionTests(unittest.TestCase):
    def test_pipe_backend_never_passes_shell_true(self) -> None:
        captured: dict[str, object] = {}
        original_popen = subprocess.Popen

        def spy(*args, **kwargs):  # noqa: ANN002, ANN003
            captured["kwargs"] = kwargs
            return original_popen(*args, **kwargs)

        proc = PipeChildProcess([_PY, "-c", "pass"])
        with unittest.mock.patch("subprocess.Popen", side_effect=spy):
            proc.spawn()
        proc.wait()
        proc.close()

        self.assertIsNot(captured["kwargs"].get("shell"), True)
        self.assertFalse(captured["kwargs"].get("shell", False))

    def test_inherit_backend_never_passes_shell_true(self) -> None:
        captured: dict[str, object] = {}
        original_popen = subprocess.Popen

        def spy(*args, **kwargs):  # noqa: ANN002, ANN003
            captured["kwargs"] = kwargs
            return original_popen(*args, **kwargs)

        proc = InheritStdioChildProcess([_PY, "-c", "pass"])
        with unittest.mock.patch("subprocess.Popen", side_effect=spy):
            proc.spawn()
        proc.wait()
        proc.close()

        self.assertIsNot(captured["kwargs"].get("shell"), True)
        self.assertFalse(captured["kwargs"].get("shell", False))


class ExitCodeRoundTripTests(unittest.TestCase):
    def test_pipe_backend_exit_code_round_trip(self) -> None:
        for code in (0, 1, 2, 42, 130):
            with self.subTest(code=code):
                proc = PipeChildProcess([_PY, "-c", f"import sys; sys.exit({code})"])
                proc.spawn()
                result = proc.wait()
                proc.close()
                self.assertEqual(result, code, "wait() must return the real exit code unmodified")


class StreamCaptureTests(unittest.TestCase):
    def test_pipe_backend_captures_stdout_lines(self) -> None:
        script = "print('line-one'); print('line-two')"
        proc = PipeChildProcess([_PY, "-c", script])
        proc.spawn()
        proc.wait()
        lines = []
        while True:
            line = proc.read()
            if line is None:
                break
            lines.append(line.rstrip("\n"))
        proc.close()
        self.assertEqual(lines, ["line-one", "line-two"])

    def test_pipe_backend_supports_output_capture_true(self) -> None:
        proc = PipeChildProcess([_PY, "-c", "pass"])
        self.assertTrue(proc.supports_output_capture)


class InheritStdioCaptureUnavailableTests(unittest.TestCase):
    def test_read_raises_output_capture_unavailable(self) -> None:
        proc = InheritStdioChildProcess([_PY, "-c", "pass"])
        proc.spawn()
        try:
            with self.assertRaises(OutputCaptureUnavailable):
                proc.read()
        finally:
            proc.wait()
            proc.close()

    def test_supports_output_capture_false(self) -> None:
        proc = InheritStdioChildProcess([_PY, "-c", "pass"])
        self.assertFalse(proc.supports_output_capture)


class TtyAttachmentFidelityTests(unittest.TestCase):
    """Assert InheritStdioChildProcess passes NO redirected pipe.

    We deliberately do NOT assert ``isatty() == True`` on the child, because
    CI/test environments frequently have no real controlling terminal, which
    would make that assertion environment-dependent and flaky. Instead we
    assert the structural property that actually matters: the child's
    stdin/stdout/stderr are the parent's own file descriptors/handles,
    passed through unchanged, rather than new ``subprocess.PIPE`` objects.
    This is the portable, deterministic proxy for "inherits the controlling
    terminal when one exists".
    """

    def test_inherit_backend_spawns_with_no_pipe_redirection(self) -> None:
        captured: dict[str, object] = {}
        original_popen = subprocess.Popen

        def spy(*args, **kwargs):  # noqa: ANN002, ANN003
            captured["kwargs"] = kwargs
            return original_popen(*args, **kwargs)

        proc = InheritStdioChildProcess([_PY, "-c", "pass"])
        with unittest.mock.patch("subprocess.Popen", side_effect=spy):
            proc.spawn()
        proc.wait()
        proc.close()

        kwargs = captured["kwargs"]
        for stream_name in ("stdin", "stdout", "stderr"):
            self.assertNotEqual(
                kwargs.get(stream_name),
                subprocess.PIPE,
                f"{stream_name} must not be redirected to a pipe for inherit-stdio",
            )


class SignalTerminateTests(unittest.TestCase):
    def test_fake_child_process_records_signals(self) -> None:
        fake = FakeChildProcess(argv=(_PY, "-c", "pass"), exit_code=0)
        fake.spawn()
        fake.signal(signal.SIGTERM)
        fake.signal(signal.SIGINT)
        self.assertEqual(fake.signals_received, [signal.SIGTERM, signal.SIGINT])
        result = fake.wait()
        fake.close()
        self.assertEqual(result, 0)
        self.assertTrue(fake.closed)

    def test_pipe_backend_signal_terminates_real_subprocess(self) -> None:
        proc = PipeChildProcess([_PY, "-c", "import time; time.sleep(30)"])
        proc.spawn()
        proc.signal(signal.SIGTERM)
        result = proc.wait(timeout=10)
        proc.close()
        self.assertNotEqual(result, None)


class ReapWithoutZombiesTests(unittest.TestCase):
    def test_pipe_backend_wait_reaps_process(self) -> None:
        proc = PipeChildProcess([_PY, "-c", "import sys; sys.exit(0)"])
        proc.spawn()
        proc.wait()
        # After wait() the underlying Popen has already been reaped by the
        # stdlib; poll() must reflect a completed, non-None returncode
        # rather than hanging or indicating a still-running/zombied child.
        self.assertIsNotNone(proc.raw_popen.poll())
        proc.close()

    def test_inherit_backend_close_reaps_without_prior_wait(self) -> None:
        """128-S review remediation: close() called WITHOUT a prior wait()
        on a still-running child must actually reap it (not merely signal
        termination and abandon the handle), avoiding an unreaped zombie.
        """

        proc = InheritStdioChildProcess([_PY, "-c", "import time; time.sleep(30)"])
        proc.spawn()
        raw = proc._process  # noqa: SLF001 - test introspection only
        proc.close()
        # After close(), the underlying Popen must have been waited on: its
        # returncode is set (reaped), not left None (zombie/still-running).
        self.assertIsNotNone(raw.poll())

    def test_pipe_backend_close_drains_and_reaps_chatty_child(self) -> None:
        """128-S review remediation: close() must not deadlock (and must
        reap) a child that keeps writing substantial output right up until
        termination -- a bare wait() without draining stdout risks the
        child blocking on a full OS pipe buffer.
        """

        script = (
            "import sys, time\n"
            "for _ in range(5000):\n"
            "    sys.stdout.write('x' * 200 + '\\n')\n"
            "time.sleep(30)\n"
        )
        proc = PipeChildProcess([_PY, "-c", script])
        proc.spawn()
        raw = proc.raw_popen
        proc.close()
        self.assertIsNotNone(raw.poll())


class FakeChildProcessScriptedOutputTests(unittest.TestCase):
    def test_scripted_stdout_lines_are_read_in_order_then_none(self) -> None:
        fake = FakeChildProcess(
            argv=(_PY, "-c", "pass"), scripted_stdout=["alpha", "beta"], exit_code=3
        )
        fake.spawn()
        self.assertEqual(fake.read(), "alpha")
        self.assertEqual(fake.read(), "beta")
        self.assertIsNone(fake.read())
        self.assertEqual(fake.wait(), 3)
        fake.close()

    def test_fake_write_is_recorded(self) -> None:
        fake = FakeChildProcess(argv=(_PY, "-c", "pass"))
        fake.spawn()
        fake.write(b"hello")
        self.assertEqual(fake.written, [b"hello"])
        fake.wait()
        fake.close()


if __name__ == "__main__":
    unittest.main()
