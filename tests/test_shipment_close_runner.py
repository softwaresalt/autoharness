"""Bounded backlogit subprocess runner tests (192.004-T, plan unit A3a).

Three table-driven scenarios (plan ``### A3a``):

1. binary trust (bare-name ``cli.binary``, basename match, workspace
   containment, Windows script shims);
2. timeout (the process group is killed, ``timed_out: true``);
3. drain (2 MiB of stdout is drained and hashed, never retained whole).

No real backlogit binary is spawned. Fakes are created by the test itself,
outside the fixture workspace root, and reach ``run_bounded`` through the
``ResolvedBinary.argv_prefix`` seam as ``(sys.executable, fake_script)``.
"""

from __future__ import annotations

import hashlib
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from autoharness.shipment_close import EXIT_INPUT
from autoharness.shipment_close import runner as runner_module
from autoharness.shipment_close.persist import (
    PARSE_CAP_BYTES,
    STDOUT_OVERFLOW_ERROR,
    STREAM_DRAIN_INCOMPLETE_ERROR,
    PersistError,
)
from autoharness.shipment_close.runner import (
    DEFAULT_TIMEOUT_SECONDS,
    ResolvedBinary,
    hash_binary,
    resolve_backlogit_binary,
    run_bounded,
    validate_timeout,
)

_EXE = ".exe" if os.name == "nt" else ""


class _Fixture:
    def __init__(self, test: unittest.TestCase, binary: str = "backlogit") -> None:
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        base = Path(tmp.name).resolve()
        self.root = base / "ws"
        self.fakes = base / "fakes"
        self.root.mkdir()
        self.fakes.mkdir()
        (self.root / ".autoharness").mkdir()
        self.set_binary(binary)

    def set_binary(self, binary: str) -> None:
        (self.root / ".autoharness" / "backlog-registry.yaml").write_text(
            f'schema_version: "1.0.0"\ncli:\n  binary: "{binary}"\n', encoding="utf-8"
        )

    def fake(self, directory: Path, name: str, content: bytes = b"fake binary\n") -> Path:
        path = directory / name
        path.write_bytes(content)
        return path

    def script(self, name: str, body: str) -> ResolvedBinary:
        path = self.fakes / name
        path.write_text(body, encoding="utf-8")
        return ResolvedBinary(
            binary_path=sys.executable,
            binary_sha256=hash_binary(Path(sys.executable)),
            argv_prefix=(sys.executable, str(path)),
        )


class BinaryTrustTests(unittest.TestCase):
    """Scenario 1: only a bare, basename-matching, out-of-workspace executable is trusted."""

    def test_binary_trust_table(self) -> None:
        with self.subTest("a trusted resolution outside the workspace"):
            fixture = _Fixture(self)
            good = fixture.fake(fixture.fakes, f"backlogit{_EXE}")
            which = mock.Mock(return_value=str(good))
            resolved = resolve_backlogit_binary(fixture.root, which=which)
            which.assert_called_once_with("backlogit")
            self.assertEqual(resolved.binary_path, str(good))
            self.assertEqual(resolved.argv_prefix, (str(good),))
            self.assertEqual(resolved.binary_sha256, hashlib.sha256(b"fake binary\n").hexdigest())

        # cli.binary values refused before any lookup (re-plan cycle-1 R3).
        for binary in (
            "/bin/sh",
            "C:\\Tools\\backlogit.exe",
            "/usr/local/bin/backlogit",
            "tools/backlogit",
            "tools\\backlogit",
            "backlogit.exe",
            ".",
            "",
            "\\\\server\\share\\backlogit",
        ):
            with self.subTest(binary=binary):
                fixture = _Fixture(self, binary)
                which = mock.Mock(return_value=None)
                with self.assertRaises(PersistError) as caught:
                    resolve_backlogit_binary(fixture.root, which=which)
                self.assertEqual(caught.exception.exit_code, EXIT_INPUT)
                which.assert_not_called()

        def refused(label: str, resolve_to) -> None:
            with self.subTest(label):
                fixture = _Fixture(self)
                target = resolve_to(fixture)
                which = mock.Mock(return_value=None if target is None else str(target))
                with self.assertRaises(PersistError) as caught:
                    resolve_backlogit_binary(fixture.root, which=which)
                self.assertEqual(caught.exception.exit_code, EXIT_INPUT)

        refused("unresolved binary", lambda f: None)
        refused("a fake binary inside the workspace root", lambda f: f.fake(f.root, f"backlogit{_EXE}"))
        refused("a resolved basename that differs", lambda f: f.fake(f.fakes, f"python{_EXE}"))
        refused("a resolved basename with a different prefix", lambda f: f.fake(f.fakes, f"backlogit2{_EXE}"))
        if os.name == "nt":
            refused("a .cmd shim", lambda f: f.fake(f.fakes, "backlogit.cmd", b"@echo off\r\n"))
            refused("a .bat shim", lambda f: f.fake(f.fakes, "backlogit.bat", b"@echo off\r\n"))
            refused("an extensionless resolution", lambda f: f.fake(f.fakes, "backlogit"))

        with self.subTest("a missing registry"):
            fixture = _Fixture(self)
            (fixture.root / ".autoharness" / "backlog-registry.yaml").unlink()
            with self.assertRaises(PersistError):
                resolve_backlogit_binary(fixture.root, which=mock.Mock(return_value=None))

        with self.subTest("timeout bounds"):
            self.assertEqual(DEFAULT_TIMEOUT_SECONDS, 120)
            for value in (30, 120, 900):
                self.assertEqual(validate_timeout(value), value)
            for value in (29, 901, 0, -1, True, 1.5, "60"):
                with self.subTest(timeout=value):
                    with self.assertRaises(PersistError) as caught:
                        validate_timeout(value)
                    self.assertEqual(caught.exception.exit_code, EXIT_INPUT)


class TimeoutTests(unittest.TestCase):
    """Scenario 2: a child that outlives its timeout is killed with its process group."""

    def test_timeout_kills_the_child(self) -> None:
        fixture = _Fixture(self)
        resolved = fixture.script(
            "sleeper.py", "import sys, time\nsys.stdout.write('started\\n')\nsys.stdout.flush()\ntime.sleep(60)\n"
        )
        started = time.monotonic()
        result = run_bounded([*resolved.argv_prefix], cwd=fixture.fakes, timeout=1)
        elapsed = time.monotonic() - started
        self.assertTrue(result.timed_out)
        self.assertLess(elapsed, 30)
        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(result.argv, tuple(resolved.argv_prefix))
        self.assertTrue(result.started_at)
        self.assertTrue(result.finished_at)

    def test_completed_child(self) -> None:
        fixture = _Fixture(self)
        resolved = fixture.script(
            "ok.py", "import sys\nsys.stdout.write('{\"ok\": true}\\n')\nsys.stderr.write('note\\n')\nsys.exit(3)\n"
        )
        result = run_bounded([*resolved.argv_prefix], cwd=fixture.fakes, timeout=30)
        self.assertFalse(result.timed_out)
        self.assertEqual(result.exit_code, 3)
        self.assertEqual(result.stdout.parse_bytes.replace(b"\r\n", b"\n"), b'{"ok": true}\n')
        self.assertIn("note", result.stderr.excerpt)
        self.assertIsNone(result.stderr.parse_bytes)

    def test_argv_validation(self) -> None:
        fixture = _Fixture(self)
        for argv in ([], "backlogit version", [sys.executable, 3]):
            with self.subTest(argv=argv):
                with self.assertRaises(PersistError):
                    run_bounded(argv, cwd=fixture.fakes, timeout=5)
        with self.subTest("an unspawnable program"):
            with self.assertRaises(PersistError):
                run_bounded([str(fixture.fakes / f"missing{_EXE}")], cwd=fixture.fakes, timeout=5)


class LingeringGrandchildTests(unittest.TestCase):
    """198-S local review: a grandchild holding stdout must not defeat the bound."""

    _GRANDCHILD_SLEEP = 20

    def test_lingering_grandchild_does_not_hang_and_marks_drain_incomplete(self) -> None:
        fixture = _Fixture(self)
        pid_file = fixture.fakes / "grandchild.pid"

        def kill_grandchild() -> None:
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                return
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                return
            time.sleep(0.5)  # let Windows release the grandchild's cwd handle

        self.addCleanup(kill_grandchild)
        resolved = fixture.script(
            "spawner.py",
            "import subprocess, sys\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep("
            f"{self._GRANDCHILD_SLEEP})'], stdout=sys.stdout, stderr=sys.stderr)\n"
            f"open({str(pid_file)!r}, 'w').write(str(child.pid))\n"
            "sys.stdout.write('parent done\\n')\nsys.stdout.flush()\n",
        )
        with mock.patch.object(runner_module, "_READER_JOIN_SECONDS", 1):
            started = time.monotonic()
            result = run_bounded([*resolved.argv_prefix], cwd=fixture.fakes, timeout=30)
            elapsed = time.monotonic() - started
        self.assertLess(elapsed, self._GRANDCHILD_SLEEP - 5)
        self.assertFalse(result.timed_out)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.stdout.drain_incomplete)
        self.assertTrue(result.stdout.capture_truncated)
        self.assertIsNone(result.stdout.parse_bytes)
        self.assertEqual(result.stdout.parse_error, STREAM_DRAIN_INCOMPLETE_ERROR)
        self.assertNotIn("drain_incomplete", result.stdout.to_record())

    def test_keyboard_interrupt_kills_the_child_group(self) -> None:
        fixture = _Fixture(self)
        resolved = fixture.script("sleeper.py", "import time\ntime.sleep(60)\n")
        original_wait = subprocess.Popen.wait
        calls = {"count": 0}

        def interrupted_wait(process, timeout=None):
            calls["count"] += 1
            if calls["count"] == 1:
                raise KeyboardInterrupt
            return original_wait(process, timeout=timeout)

        spawned: list[subprocess.Popen] = []
        original_init = subprocess.Popen.__init__

        def recording_init(process, *args, **kwargs):
            original_init(process, *args, **kwargs)
            spawned.append(process)

        with (
            mock.patch.object(subprocess.Popen, "__init__", recording_init),
            mock.patch.object(subprocess.Popen, "wait", interrupted_wait),
            mock.patch.object(runner_module, "_kill_group", wraps=runner_module._kill_group) as kill,
        ):
            with self.assertRaises(KeyboardInterrupt):
                run_bounded([*resolved.argv_prefix], cwd=fixture.fakes, timeout=30)
        kill.assert_called()
        self.assertTrue(spawned)
        self.assertIsNotNone(spawned[0].poll())


class DrainTests(unittest.TestCase):
    """Scenario 3: a 2 MiB stdout is drained and hashed but not retained whole."""

    def test_two_mebibyte_stdout_is_drained(self) -> None:
        fixture = _Fixture(self)
        resolved = fixture.script(
            "flood.py",
            "import sys\nchunk = b'0123456789abcdef' * 4096\n"
            "for _ in range(32):\n    sys.stdout.buffer.write(chunk)\nsys.stdout.buffer.flush()\n",
        )
        result = run_bounded([*resolved.argv_prefix], cwd=fixture.fakes, timeout=60)
        expected = (b"0123456789abcdef" * 4096) * 32
        self.assertFalse(result.timed_out)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.total_bytes, 2 * 1024 * 1024)
        self.assertGreater(result.stdout.total_bytes, PARSE_CAP_BYTES)
        self.assertEqual(result.stdout.sha256, hashlib.sha256(expected).hexdigest())
        self.assertIsNone(result.stdout.parse_bytes)
        self.assertEqual(result.stdout.parse_error, STDOUT_OVERFLOW_ERROR)
        self.assertTrue(result.stdout.capture_truncated)


if __name__ == "__main__":
    unittest.main()
