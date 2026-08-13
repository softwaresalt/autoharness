"""Tests for autoharness.supervise.process -- the ChildProcess protocol (119.001-T).

Covers argv fidelity, the no-shell invariant, real-subprocess exit-code
round-tripping, stream capture on the Pipe backend, signal/terminate
handling, reaping without zombies, and the TTY-attachment-fidelity contract
for the inherit-stdio backend.
"""

from __future__ import annotations

import os
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


class EnvPropagationTests(unittest.TestCase):
    """120-F post-closure correction (2026-08-13): neither backend may pass
    its own explicit ``env=`` override to ``subprocess.Popen`` -- doing so
    would silently stop the resolved ENGRAM_WORKSPACE/GRAPHTOR_DB_PATH/
    GRAPHTOR_SOURCES bootstrap.py additions (applied to this process's own
    ``os.environ`` by ``app.run_session``) from ever reaching the spawned
    child. ``subprocess.Popen``'s own default (``env=None``) means "inherit
    the calling process's current environment verbatim" -- the invariant
    this test asserts holds for both real-process backends.
    """

    def test_pipe_backend_never_passes_an_explicit_env_override(self) -> None:
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

        self.assertNotIn("env", captured["kwargs"])

    def test_inherit_backend_never_passes_an_explicit_env_override(self) -> None:
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

        self.assertNotIn("env", captured["kwargs"])

    def test_pipe_backend_child_actually_observes_a_parent_env_addition(self) -> None:
        # End-to-end (real subprocess, no mock): a variable added to this
        # test process's own os.environ right before spawn() must be
        # observable inside the real child -- proving inheritance is not
        # merely "no override kwarg" but an actual, working propagation
        # path, exactly mirroring how bootstrap.py's binding additions
        # reach the real Copilot child.
        sentinel_name = "AUTOHARNESS_TEST_ENV_PROPAGATION_SENTINEL"
        sentinel_value = "propagated-ok"
        with unittest.mock.patch.dict(os.environ, {sentinel_name: sentinel_value}):
            proc = PipeChildProcess(
                [_PY, "-c", f"import os, sys; sys.stdout.write(os.environ.get({sentinel_name!r}, ''))"]
            )
            proc.spawn()
            output_lines = []
            while True:
                line = proc.read()
                if line is None:
                    break
                output_lines.append(line)
            exit_code = proc.wait()
            proc.close()

        self.assertEqual(exit_code, 0)
        self.assertEqual("".join(output_lines), sentinel_value)



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


class CwdForwardingTests(unittest.TestCase):
    """120-F runtime-defect remediation: Copilot (and, by inheritance, any
    local stdio MCP server IT spawns, e.g. Engram/graphtor-docs) must run
    with cwd anchored to the resolved workspace root, independent of
    whatever directory the operator's shell happened to be in when
    `start.ps1`/`start.sh`/`autoharness run` was invoked. Both real-process
    backends must accept an optional ``cwd`` constructor argument and
    forward it verbatim to ``subprocess.Popen`` (``None`` means "inherit
    the parent's own cwd", exactly today's default behavior, so this is
    purely additive).
    """

    def test_inherit_backend_forwards_cwd_to_popen(self) -> None:
        import tempfile

        captured: dict[str, object] = {}
        original_popen = subprocess.Popen

        def spy(*args, **kwargs):  # noqa: ANN002, ANN003
            captured["kwargs"] = kwargs
            return original_popen(*args, **kwargs)

        with tempfile.TemporaryDirectory() as workspace:
            proc = InheritStdioChildProcess([_PY, "-c", "pass"], cwd=workspace)
            with unittest.mock.patch("subprocess.Popen", side_effect=spy):
                proc.spawn()
            proc.wait()
            proc.close()

        self.assertEqual(captured["kwargs"].get("cwd"), workspace)

    def test_inherit_backend_defaults_cwd_to_none_when_omitted(self) -> None:
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

        self.assertIsNone(captured["kwargs"].get("cwd"))

    def test_pipe_backend_forwards_cwd_to_popen(self) -> None:
        import tempfile

        captured: dict[str, object] = {}
        original_popen = subprocess.Popen

        def spy(*args, **kwargs):  # noqa: ANN002, ANN003
            captured["kwargs"] = kwargs
            return original_popen(*args, **kwargs)

        with tempfile.TemporaryDirectory() as workspace:
            proc = PipeChildProcess([_PY, "-c", "pass"], cwd=workspace)
            with unittest.mock.patch("subprocess.Popen", side_effect=spy):
                proc.spawn()
            proc.wait()
            proc.close()

        self.assertEqual(captured["kwargs"].get("cwd"), workspace)


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
