"""Journaled child runner and platform probes (211.006-T / plan unit T5; hardening H12, H13).

The first two classes are the T5 de-risking probes and run before everything
else in the file's reading order:

* the detached shim survives a killed launcher (and, on Windows, a killed Job
  Object that allows breakaway);
* the shim proves the descendant group is quiescent (Windows Job Object
  membership, POSIX process group) and an escaped open writer is caught.

The remaining classes cover the journaled runner itself.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
import uuid
from pathlib import Path
from unittest import mock

from autoharness.shipment_close import journal as journal_module
from autoharness.shipment_close import quiescence, runner, supervisor
from autoharness.shipment_close.journal import (
    Journal,
    JournalError,
    argv_sha256,
    build_launch,
    create_journal,
    open_journal,
    read_json,
    utc_now,
    write_json,
)
from autoharness.shipment_close.liveness import is_process_alive
from autoharness.shipment_close.persist import (
    PARSE_CAP_BYTES,
    STDOUT_OVERFLOW_ERROR,
    STREAM_DRAIN_INCOMPLETE_ERROR,
    PersistError,
)

_SRC = str(Path(__file__).resolve().parent.parent / "src")
_WINDOWS = os.name == "nt"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = _SRC + os.pathsep + env.get("PYTHONPATH", "")
    return env


class _Fixture:
    def __init__(self, test: unittest.TestCase) -> None:
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        base = Path(tmp.name).resolve()
        self.root = base / "ws"
        self.fakes = base / "fakes"
        self.root.mkdir()
        self.fakes.mkdir()
        self.run_id = uuid.uuid4().hex
        self.journal = create_journal(self.root, "218-S", "211-F", self.run_id)

    def script(self, name: str, body: str) -> Path:
        path = self.fakes / name
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return path

    def write_launch(self, script: Path, *args: str, timeout: int = 30, **overrides: object) -> dict:
        argv = [sys.executable, str(script), *args]
        launch = build_launch(
            run_id=self.run_id,
            workspace=str(self.root),
            shipment_id="218-S",
            feature_id="211-F",
            merge_commit_sha="a" * 40,
            mode="attached",
            argv=argv,
            binary_path=str(script),
            binary_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
            argv_prefix=[sys.executable, str(script)],
            cwd=str(self.fakes),
            timeout_seconds=timeout,
        )
        launch.update(overrides)
        write_json(self.journal, "launch.json", launch)
        return launch


def _wait_for(predicate, *, timeout: float, interval: float = 0.1) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def _kill_pid(pid: int) -> None:
    if is_process_alive(pid) is not True:
        return
    if _WINDOWS:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, check=False)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


_LAUNCHER = """
import subprocess, sys, time
from autoharness.shipment_close.runner import spawn_detached
journal, pid_file = sys.argv[1], sys.argv[2]
spawned = spawn_detached([sys.executable, "-m", "autoharness.shipment_close.supervisor", "--shim", journal],
                         cwd=journal)
open(pid_file, "w").write(f"{spawned.process.pid} {int(spawned.breakaway)}")
time.sleep(120)
"""

_JOB_LAUNCHER = """
import ctypes, subprocess, sys, time
from ctypes import wintypes
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateJobObjectW.restype = wintypes.HANDLE
k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
k32.GetCurrentProcess.restype = wintypes.HANDLE
k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
class BASIC(ctypes.Structure):
    _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("LimitFlags", wintypes.DWORD),
                ("c", ctypes.c_size_t), ("d", ctypes.c_size_t), ("e", wintypes.DWORD),
                ("f", ctypes.c_size_t), ("g", wintypes.DWORD), ("h", wintypes.DWORD)]
class IO(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in "abcdef"]
class EXT(ctypes.Structure):
    _fields_ = [("Basic", BASIC), ("Io", IO), ("p", ctypes.c_size_t), ("q", ctypes.c_size_t),
                ("r", ctypes.c_size_t), ("s", ctypes.c_size_t)]
job = k32.CreateJobObjectW(None, None)
info = EXT()
info.Basic.LimitFlags = 0x2000 | 0x800   # KILL_ON_JOB_CLOSE | BREAKAWAY_OK
assert k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
assert k32.AssignProcessToJobObject(job, k32.GetCurrentProcess())
from autoharness.shipment_close.runner import spawn_detached
journal, pid_file = sys.argv[1], sys.argv[2]
spawned = spawn_detached([sys.executable, "-m", "autoharness.shipment_close.supervisor", "--shim", journal],
                         cwd=journal)
open(pid_file, "w").write(f"{spawned.process.pid} {int(spawned.breakaway)}")
time.sleep(120)
"""

_SLOW_CHILD = """
import pathlib, sys, time
time.sleep(3)
pathlib.Path(sys.argv[1]).write_text("done", encoding="utf-8")
sys.stdout.write("slow child output\\n")
"""


class DetachedSurvivalProbeTests(unittest.TestCase):
    """T5 first probe: the shim and its child outlive a killed launcher."""

    def _run_probe(self, launcher_source: str) -> None:
        fixture = _Fixture(self)
        marker = fixture.fakes / "marker.txt"
        script = fixture.script("slow.py", _SLOW_CHILD)
        fixture.write_launch(script, str(marker))
        launcher = fixture.script("launcher.py", launcher_source)
        pid_file = fixture.fakes / "shim.pid"
        process = subprocess.Popen(
            [sys.executable, str(launcher), str(fixture.journal.path), str(pid_file)],
            env=_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.addCleanup(process.kill)
        self.assertTrue(_wait_for(pid_file.exists, timeout=20), "the launcher never spawned the shim")
        text = pid_file.read_text(encoding="utf-8")
        shim_pid, breakaway = int(text.split()[0]), text.split()[1]
        self.addCleanup(_kill_pid, shim_pid)
        if _WINDOWS and breakaway != "1":
            self.skipTest("this runtime does not permit CREATE_BREAKAWAY_FROM_JOB; the shim cannot outlive its job here")
        process.kill()  # TerminateProcess / SIGKILL of the launcher only
        process.wait(timeout=20)
        self.assertTrue(
            _wait_for(lambda: (fixture.journal.path / "exit.json").exists(), timeout=60),
            "the shim did not survive the launcher being killed",
        )
        exit_record = read_json(fixture.journal, "exit.json")
        self.assertEqual(exit_record["state"], "exited")
        self.assertEqual(exit_record["exit_code"], 0)
        self.assertEqual(marker.read_text(encoding="utf-8"), "done")
        self.assertIn(b"slow child output", (fixture.journal.path / "stdout.raw").read_bytes())

    def test_shim_outlives_a_killed_launcher(self) -> None:
        self._run_probe(_LAUNCHER)

    @unittest.skipUnless(_WINDOWS, "Job Object breakaway is Windows-specific")
    def test_shim_outlives_a_killed_job_that_permits_breakaway(self) -> None:
        self._run_probe(_JOB_LAUNCHER)


_GRANDCHILD_PARENT = """
import subprocess, sys
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], stdout=sys.stdout, stderr=sys.stderr)
open(sys.argv[1], "w").write(str(child.pid))
sys.stdout.write("parent done\\n")
sys.stdout.flush()
"""


class DescendantGroupProbeTests(unittest.TestCase):
    """T5 second probe: a surviving grandchild is found through the group, killed, and the capture is unproven."""

    def test_a_surviving_grandchild_is_killed_and_the_capture_is_incomplete(self) -> None:
        fixture = _Fixture(self)
        pid_file = fixture.fakes / "grandchild.pid"
        script = fixture.script("spawner.py", _GRANDCHILD_PARENT)
        fixture.write_launch(script, str(pid_file), quiescence_grace_seconds=1.0)
        started = time.monotonic()
        result = runner.run_journaled(fixture.journal)
        elapsed = time.monotonic() - started
        grandchild = int(pid_file.read_text(encoding="utf-8"))
        self.addCleanup(_kill_pid, grandchild)
        self.assertLess(elapsed, 30)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.stdout.drain_incomplete)
        self.assertIsNone(result.stdout.parse_bytes)
        self.assertEqual(result.stdout.parse_error, STREAM_DRAIN_INCOMPLETE_ERROR)
        exit_record = read_json(fixture.journal, "exit.json")
        for stream in ("stdout", "stderr"):
            verdict = exit_record["quiescence"][stream]
            self.assertFalse(verdict["proven"])
            self.assertGreaterEqual(verdict["survivors_killed"], 1)
        self.assertTrue(
            _wait_for(lambda: is_process_alive(grandchild) is False, timeout=10),
            "the surviving grandchild was not killed",
        )

    def test_a_quiet_child_is_proven_quiescent_with_final_byte_counts(self) -> None:
        fixture = _Fixture(self)
        script = fixture.script("quiet.py", "import sys\nsys.stdout.write('hello\\n')\nsys.stderr.write('warn\\n')\n")
        fixture.write_launch(script)
        result = runner.run_journaled(fixture.journal)
        self.assertEqual(result.exit_code, 0)
        exit_record = read_json(fixture.journal, "exit.json")
        out = fixture.journal.path.joinpath("stdout.raw").read_bytes()
        err = fixture.journal.path.joinpath("stderr.raw").read_bytes()
        self.assertTrue(exit_record["quiescence"]["stdout"]["proven"])
        self.assertTrue(exit_record["quiescence"]["stderr"]["proven"])
        self.assertEqual(exit_record["quiescence"]["stdout"]["total_bytes"], len(out))
        self.assertEqual(exit_record["quiescence"]["stderr"]["total_bytes"], len(err))
        self.assertEqual(exit_record["quiescence"]["stdout"]["survivors_killed"], 0)
        self.assertEqual(
            exit_record["quiescence"]["stdout"]["method"].split("+")[0],
            "job_object" if _WINDOWS else "process_group",
        )
        self.assertFalse(result.stdout.drain_incomplete)

    @unittest.skipUnless(_WINDOWS, "Job Object membership is Windows-specific")
    def test_job_object_membership_enumerates_a_live_grandchild(self) -> None:
        fixture = _Fixture(self)
        out_file = fixture.fakes / "probe.out"
        script = fixture.script(
            "probe.py",
            """
            import subprocess, sys, time
            from autoharness.shipment_close import quiescence
            job = quiescence.WindowsJob.enter_current_process()
            assert job is not None
            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            members = job.members()
            assert child.pid in members, members
            assert job.kill_members() >= 1
            child.wait(timeout=10)
            for _ in range(50):
                if not job.members():
                    break
                time.sleep(0.1)
            assert job.members() == frozenset(), job.members()
            open(sys.argv[1], "w").write("ok")
            """,
        )
        process = subprocess.run(
            [sys.executable, str(script), str(out_file)], env=_env(), capture_output=True, text=True, timeout=60
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(out_file.read_text(encoding="utf-8"), "ok")

    @unittest.skipIf(_WINDOWS, "process-group semantics are POSIX-specific")
    def test_posix_group_members_and_kill(self) -> None:
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
        self.addCleanup(child.kill)
        group = quiescence.PosixGroup(child.pid)
        self.assertEqual(group.members(), frozenset({child.pid}))
        self.assertEqual(group.kill_members(), 1)
        child.wait(timeout=10)
        self.assertEqual(group.members(), frozenset())

    def test_group_that_cannot_be_enumerated_is_never_quiescent(self) -> None:
        class Opaque:
            method = "opaque"

            def members(self):
                return None

            def kill_members(self) -> int:
                return 0

        verdict = quiescence.settle_group(Opaque(), grace=0.0)
        self.assertFalse(verdict.proven)
        self.assertFalse(quiescence.settle_group(None, grace=0.0).proven)

    def test_survivors_that_exit_on_their_own_within_the_grace_are_proven(self) -> None:
        class Draining:
            method = "fake"

            def __init__(self) -> None:
                self.calls = 0

            def members(self):
                self.calls += 1
                return frozenset({7}) if self.calls < 3 else frozenset()

            def kill_members(self) -> int:
                raise AssertionError("must not kill members that drain by themselves")

        verdict = quiescence.settle_group(Draining(), grace=5.0, poll=0.0)
        self.assertTrue(verdict.proven)
        self.assertEqual(verdict.survivors_killed, 0)


class EscapedWriterProbeTests(unittest.TestCase):
    """H13(b): an empty group does not prove that no writer escaped it."""

    def test_probe_sees_another_process_holding_the_file(self) -> None:
        fixture = _Fixture(self)
        path = fixture.fakes / "held.raw"
        floor = time.time()
        path.write_bytes(b"")
        holder = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import sys, time\n"
                f"h = open({str(path)!r}, 'ab')\n"
                "sys.stdout.write('ready\\n'); sys.stdout.flush()\n"
                "time.sleep(30)\n",
            ],
            stdout=subprocess.PIPE,
        )
        self.addCleanup(holder.stdout.close)
        self.addCleanup(holder.kill)
        self.assertEqual(holder.stdout.readline().strip(), b"ready")
        verdict = quiescence.probe_writers([path], started_before_epoch=floor)
        if verdict.clean is None:
            self.skipTest(f"no open-writer primitive here: {verdict.detail}")
        self.assertFalse(verdict.clean)
        holder.kill()
        holder.wait(timeout=10)
        self.assertTrue(
            _wait_for(lambda: quiescence.probe_writers([path], started_before_epoch=floor).clean is True, timeout=10)
        )

    def test_an_escaped_grandchild_holding_stdout_makes_the_capture_unproven(self) -> None:
        fixture = _Fixture(self)
        pid_file = fixture.fakes / "escaped.pid"
        script = fixture.script("escaper.py", _GRANDCHILD_PARENT)
        fixture.write_launch(script, str(pid_file))

        class EmptyGroup:
            """A group that (wrongly) reports no members, i.e. the writer escaped it."""

            method = "empty_fake"

            def members(self):
                return frozenset()

            def kill_members(self) -> int:
                return 0

        scratch = fixture.fakes / "probe.tmp"
        scratch.write_bytes(b"")
        probe = quiescence.probe_writers([scratch])
        if probe.clean is None:
            self.skipTest(f"no open-writer primitive here: {probe.detail}")
        launch = read_json(fixture.journal, "launch.json")
        with mock.patch.object(quiescence, "enter_group", lambda pid=None: EmptyGroup()):
            exit_record = supervisor.run_child(fixture.journal, launch, grace_seconds=1.0)
        self.addCleanup(_kill_pid, int(pid_file.read_text(encoding="utf-8")))
        for stream in ("stdout", "stderr"):
            self.assertFalse(exit_record["quiescence"][stream]["proven"], stream)
        self.assertIn("writer", exit_record["quiescence"]["stdout"]["method"])

    def test_proc_fd_scan_with_injected_tables(self) -> None:
        paths = [Path("/j/stdout.raw")]
        tables = {"/proc": ["1", "50", "self"], "/proc/50/fd": ["0", "3"]}
        links = {"/proc/50/fd/0": "/dev/null", "/proc/50/fd/3": "/j/stdout.raw"}

        def listdir(path: str) -> list[str]:
            return tables[path.replace("\\", "/")]

        def readlink(path: str) -> str:
            return links[path.replace("\\", "/")]

        with mock.patch.object(quiescence.os.path, "realpath", lambda p: str(p).replace("\\", "/")):
            verdict = quiescence.scan_proc_fds(
                paths, proc_root=Path("/proc"), self_pid=1, listdir=listdir, readlink=readlink
            )
            self.assertFalse(verdict.clean)
            links["/proc/50/fd/3"] = "/elsewhere"
            clean = quiescence.scan_proc_fds(
                paths, proc_root=Path("/proc"), self_pid=1, listdir=listdir, readlink=readlink
            )
            self.assertTrue(clean.clean)

            def denied(path: str) -> list[str]:
                if path.replace("\\", "/") == "/proc":
                    return ["50"]
                raise PermissionError

            self.assertIsNone(
                quiescence.scan_proc_fds(paths, listdir=denied, stat_uid=lambda p: 1000, my_uid=1000).clean
            )

    def test_unavailable_primitive_is_unproven(self) -> None:
        with (
            mock.patch.object(quiescence, "_WINDOWS", False),
            mock.patch.object(quiescence.os.path, "isdir", return_value=False),
        ):
            self.assertIsNone(quiescence.probe_writers([Path("x")]).clean)


class JournalLaunchTests(unittest.TestCase):
    def test_argv_hash_is_over_the_exact_argv(self) -> None:
        argv = ["a", "--message", "token=abc123", "é"]
        self.assertEqual(
            argv_sha256(argv), hashlib.sha256(json.dumps(argv, separators=(",", ":")).encode("utf-8")).hexdigest()
        )
        self.assertNotEqual(argv_sha256(argv), argv_sha256([*argv, "x"]))

    def test_launch_schema_rejects_a_hash_that_does_not_match_its_argv(self) -> None:
        fixture = _Fixture(self)
        script = fixture.script("noop.py", "pass\n")
        launch = fixture.write_launch(script)
        self.assertEqual(read_json(fixture.journal, "launch.json")["argv_sha256"], launch["argv_sha256"])
        tampered = dict(launch, argv=[*launch["argv"], "--extra"])
        with self.assertRaises(JournalError):
            write_json(fixture.journal, "launch.json", tampered)

    def test_open_journal_binds_the_directory_to_the_launch_record(self) -> None:
        fixture = _Fixture(self)
        fixture.write_launch(fixture.script("noop.py", "pass\n"))
        opened = open_journal(str(fixture.journal.path))
        self.assertEqual(opened.run_id, fixture.run_id)
        other = fixture.root / ".autoharness" / "gates" / "cascade-close" / "999-S-998-F.journal"
        other.mkdir()
        (other / "launch.json").write_bytes((fixture.journal.path / "launch.json").read_bytes())
        with self.assertRaises(JournalError):
            open_journal(str(other))
        with self.assertRaises(JournalError):
            open_journal("relative.journal")

    def test_barrier_files_are_schema_checked(self) -> None:
        fixture = _Fixture(self)
        good = {
            "ready.json": {"supervisor_pid": 5},
            "authorize.json": {"nonce": "n" * 16, "valid_until": "2026-10-17T00:00:00.000000Z"},
            "abort.json": {"reason": "timeout"},
            "child_started.json": {"state": "spawning", "pid": None},
        }
        for name, extra in good.items():
            with self.subTest(name=name):
                record = {"schema_version": 1, "run_id": fixture.run_id, "written_at": journal_module.utc_now(), **extra}
                write_json(fixture.journal, name, record)
                self.assertEqual(read_json(fixture.journal, name)["run_id"], fixture.run_id)
                with self.assertRaises(JournalError):
                    write_json(fixture.journal, name, {**record, "stray": 1})


class RunJournaledTests(unittest.TestCase):
    def test_completed_child_is_streamed_through_the_capture(self) -> None:
        fixture = _Fixture(self)
        script = fixture.script(
            "ok.py", "import sys\nsys.stdout.write('{\"ok\": true}\\n')\nsys.stderr.write('note\\n')\nsys.exit(3)\n"
        )
        fixture.write_launch(script)
        result = runner.run_journaled(fixture.journal)
        self.assertFalse(result.timed_out)
        self.assertEqual(result.exit_code, 3)
        self.assertEqual(result.stdout.parse_bytes.replace(b"\r\n", b"\n"), b'{"ok": true}\n')
        self.assertIn("note", result.stderr.excerpt)
        self.assertIsNone(result.stderr.parse_bytes)
        self.assertFalse(result.stdout.drain_incomplete)
        self.assertTrue(result.started_at and result.finished_at)

    def test_timeout_kills_the_child(self) -> None:
        fixture = _Fixture(self)
        script = fixture.script(
            "sleeper.py", "import sys, time\nsys.stdout.write('started\\n')\nsys.stdout.flush()\ntime.sleep(60)\n"
        )
        fixture.write_launch(script, timeout=1)
        started = time.monotonic()
        result = runner.run_journaled(fixture.journal)
        self.assertTrue(result.timed_out)
        self.assertLess(time.monotonic() - started, 30)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("started", result.stdout.excerpt)
        self.assertEqual(read_json(fixture.journal, "exit.json")["state"], "timed_out")

    def test_two_mebibyte_stdout_is_drained(self) -> None:
        fixture = _Fixture(self)
        script = fixture.script(
            "flood.py",
            "import sys\nchunk = b'0123456789abcdef' * 4096\n"
            "for _ in range(32):\n    sys.stdout.buffer.write(chunk)\nsys.stdout.buffer.flush()\n",
        )
        fixture.write_launch(script, timeout=60)
        result = runner.run_journaled(fixture.journal)
        expected = (b"0123456789abcdef" * 4096) * 32
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.total_bytes, 2 * 1024 * 1024)
        self.assertGreater(result.stdout.total_bytes, PARSE_CAP_BYTES)
        self.assertEqual(result.stdout.sha256, hashlib.sha256(expected).hexdigest())
        self.assertIsNone(result.stdout.parse_bytes)
        self.assertEqual(result.stdout.parse_error, STDOUT_OVERFLOW_ERROR)
        self.assertTrue(result.stdout.capture_truncated)

    def test_a_redaction_triggering_message_reaches_the_child_byte_for_byte(self) -> None:
        fixture = _Fixture(self)
        seen = fixture.fakes / "argv.json"
        script = fixture.script(
            "echo.py", "import json, sys\nopen(sys.argv[1], 'w', encoding='utf-8').write(json.dumps(sys.argv[2:]))\n"
        )
        message = "close with token=ghp_abcdefghijklmnopqrstuvwxyz0123456789 and password: hunter2"
        fixture.write_launch(script, str(seen), "--message", message)
        result = runner.run_journaled(fixture.journal)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(seen.read_text(encoding="utf-8")), ["--message", message])

    def test_a_launch_record_that_was_tampered_with_never_spawns(self) -> None:
        fixture = _Fixture(self)
        marker = fixture.fakes / "ran.txt"
        script = fixture.script("mark.py", "import pathlib, sys\npathlib.Path(sys.argv[1]).write_text('ran')\n")
        fixture.write_launch(script, str(marker))
        launch_file = fixture.journal.path / "launch.json"
        body = json.loads(launch_file.read_text(encoding="utf-8"))
        body["argv"][-1] = str(fixture.fakes / "other.txt")
        launch_file.write_text(json.dumps(body), encoding="utf-8")
        with self.assertRaises(PersistError):
            runner.run_journaled(fixture.journal)  # the wrapper's own schema read refuses first
        self.assertFalse(marker.exists())
        shim = subprocess.run(
            [sys.executable, "-m", "autoharness.shipment_close.supervisor", "--shim", str(fixture.journal.path)],
            env=_env(),
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(shim.returncode, 2, shim.stderr)
        self.assertFalse(marker.exists())
        self.assertFalse((fixture.fakes / "other.txt").exists())
        self.assertEqual(read_json(fixture.journal, "exit.json")["state"], "never_started")

    def test_an_argv_that_does_not_start_with_the_recorded_prefix_never_spawns(self) -> None:
        fixture = _Fixture(self)
        marker = fixture.fakes / "ran.txt"
        script = fixture.script("mark.py", "import pathlib, sys\npathlib.Path(sys.argv[1]).write_text('ran')\n")
        argv = [sys.executable, str(script), str(marker)]
        launch = build_launch(
            run_id=fixture.run_id,
            workspace=str(fixture.root),
            shipment_id="218-S",
            feature_id="211-F",
            merge_commit_sha="a" * 40,
            mode="attached",
            argv=argv,
            binary_path=str(script),
            binary_sha256="0" * 64,
            argv_prefix=["/not/the/binary", str(script)],
            cwd=str(fixture.fakes),
            timeout_seconds=30,
        )
        (fixture.journal.path / "launch.json").write_text(json.dumps(launch), encoding="utf-8")
        with self.assertRaises(PersistError):
            runner.run_journaled(fixture.journal)
        self.assertFalse(marker.exists())

    def test_spawn_failure_is_a_persist_error_and_a_spawn_failed_sentinel(self) -> None:
        fixture = _Fixture(self)
        argv = [str(fixture.fakes / "missing-binary.exe")]
        launch = build_launch(
            run_id=fixture.run_id,
            workspace=str(fixture.root),
            shipment_id="218-S",
            feature_id="211-F",
            merge_commit_sha="a" * 40,
            mode="attached",
            argv=argv,
            binary_path=argv[0],
            binary_sha256="0" * 64,
            argv_prefix=argv,
            cwd=str(fixture.fakes),
            timeout_seconds=30,
        )
        write_json(fixture.journal, "launch.json", launch)
        with self.assertRaises(PersistError) as caught:
            runner.run_journaled(fixture.journal)
        self.assertIn("cannot spawn", str(caught.exception))
        self.assertEqual(read_json(fixture.journal, "exit.json")["state"], "spawn_failed")

    def test_a_shim_that_leaves_no_sentinel_is_an_indeterminate_incomplete_result(self) -> None:
        fixture = _Fixture(self)
        script = fixture.script("noop.py", "pass\n")
        fixture.write_launch(script)
        with mock.patch.object(runner, "spawn_detached") as spawn:
            spawn.return_value = runner.DetachedSpawn(subprocess.Popen([sys.executable, "-c", "pass"]), breakaway=False)
            result = runner.run_journaled(fixture.journal)
        self.assertIsNone(result.exit_code)
        self.assertTrue(result.stdout.drain_incomplete)
        self.assertTrue(result.stderr.drain_incomplete)

    def test_keyboard_interrupt_kills_the_shim_and_its_child(self) -> None:
        fixture = _Fixture(self)
        pid_file = fixture.fakes / "child.pid"
        script = fixture.script(
            "sleeper.py", "import os, sys, time\nopen(sys.argv[1], 'w').write(str(os.getpid()))\ntime.sleep(60)\n"
        )
        fixture.write_launch(script, str(pid_file), timeout=120)
        original_wait = subprocess.Popen.wait
        calls = {"n": 0}

        def interrupted(process, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                _wait_for(pid_file.exists, timeout=20)
                raise KeyboardInterrupt
            return original_wait(process, timeout=timeout)

        with mock.patch.object(subprocess.Popen, "wait", interrupted):
            with self.assertRaises(KeyboardInterrupt):
                runner.run_journaled(fixture.journal)
        child = int(pid_file.read_text(encoding="utf-8"))
        self.addCleanup(_kill_pid, child)
        self.assertTrue(
            _wait_for(lambda: is_process_alive(child) is False, timeout=15), "the child survived the interrupt"
        )

    def test_the_stream_cap_kills_a_runaway_writer_and_marks_the_capture_unproven(self) -> None:
        fixture = _Fixture(self)
        script = fixture.script(
            "runaway.py",
            "import sys\nchunk = b'x' * 65536\nwhile True:\n    sys.stdout.buffer.write(chunk)\n    sys.stdout.buffer.flush()\n",
        )
        fixture.write_launch(script, timeout=120, stream_cap_bytes=256 * 1024)
        result = runner.run_journaled(fixture.journal)
        self.assertTrue(result.stdout.drain_incomplete)
        verdict = read_json(fixture.journal, "exit.json")["quiescence"]["stdout"]
        self.assertFalse(verdict["proven"])


class ShimBootstrapTests(unittest.TestCase):
    def test_the_working_directory_entry_is_removed_before_anything_importable_loads(self) -> None:
        bootstrap = runner._SHIM_BOOTSTRAP
        self.assertLess(bootstrap.index("sys.path.pop(0)"), bootstrap.index("import runpy"))
        self.assertEqual(bootstrap.split(";")[0].strip(), "import sys")

    def test_a_journal_local_runpy_is_never_imported(self) -> None:
        fixture = _Fixture(self)
        marker = fixture.fakes / "decoy-ran.txt"
        (fixture.root / "runpy.py").write_text(
            f"open({str(marker)!r}, 'w').write('decoy')\nraise SystemExit(99)\n", encoding="utf-8"
        )
        completed = subprocess.run(
            [sys.executable, "-c", runner._SHIM_BOOTSTRAP, "--shim", str(fixture.fakes / "not-a-journal")],
            cwd=str(fixture.root),
            env=_env(),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertFalse(marker.exists(), "the journal-local runpy.py was imported")
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("refusing to start", completed.stderr)


class SpawnEnvironmentTests(unittest.TestCase):
    def test_inherited_relative_and_empty_entries_are_resolved_against_the_foreground_directory(self) -> None:
        fixture = _Fixture(self)
        base = fixture.root
        merged = runner._spawn_environment({"PYTHONPATH": os.pathsep.join(["src", "", ".", str(fixture.fakes), ""])}, base)
        entries = merged["PYTHONPATH"].split(os.pathsep)
        package_root = str(Path(runner.__file__).resolve().parents[2])
        self.assertEqual(
            entries,
            [
                package_root,
                os.path.join(base, "src"),
                str(base),
                os.path.join(base, "."),
                str(fixture.fakes),
                str(base),
            ],
        )
        self.assertTrue(all(os.path.isabs(entry) for entry in entries))

    def test_dotdot_entries_are_not_lexically_collapsed(self) -> None:
        fixture = _Fixture(self)
        merged = runner._spawn_environment({"PYTHONPATH": os.pathsep.join([os.path.join("link", "..", "x")])}, fixture.root)
        self.assertEqual(
            merged["PYTHONPATH"].split(os.pathsep)[1], os.path.join(fixture.root, "link", "..", "x")
        )

    def test_the_working_directory_is_only_read_when_pythonpath_is_set(self) -> None:
        with (
            mock.patch.object(runner, "Path") as path,
            mock.patch.object(runner.os, "getcwd", side_effect=FileNotFoundError("deleted")) as getcwd,
        ):
            path.return_value.resolve.return_value.parents = ["unused", "unused", "ROOT"]
            for env in ({"PATH": "x"}, {"PYTHONPATH": ""}):
                self.assertEqual(runner._spawn_environment(env)["PYTHONPATH"], "ROOT")
            getcwd.assert_not_called()
            with self.assertRaises(FileNotFoundError):
                runner._spawn_environment({"PYTHONPATH": "src"})

    def test_an_unset_pythonpath_yields_only_the_package_root(self) -> None:
        merged = runner._spawn_environment({"PATH": "x"})
        self.assertEqual(merged["PYTHONPATH"], str(Path(runner.__file__).resolve().parents[2]))

    def test_the_default_base_is_the_foreground_working_directory(self) -> None:
        merged = runner._spawn_environment({"PYTHONPATH": "."})
        self.assertEqual(merged["PYTHONPATH"].split(os.pathsep)[1], os.path.join(os.getcwd(), "."))

    def test_a_spawned_child_in_the_journal_directory_never_sees_a_journal_local_import(self) -> None:
        fixture = _Fixture(self)
        journal_dir = fixture.root / "journal"
        journal_dir.mkdir()
        (journal_dir / "decoy_mod.py").write_text("DECOY = True\n", encoding="utf-8")
        probe = fixture.fakes / "probe.py"
        out = fixture.fakes / "probe.json"
        probe.write_text(
            "import json, sys\n"
            "try:\n"
            "    import decoy_mod\n"
            "    found = True\n"
            "except ImportError:\n"
            "    found = False\n"
            "json.dump({'found': found, 'path': sys.path}, open(sys.argv[1], 'w'))\n",
            encoding="utf-8",
        )
        for inherited in (".", "", "src:", os.pathsep.join(["", "."])):
            out.unlink(missing_ok=True)
            env = dict(os.environ, PYTHONPATH=inherited)
            argv = [sys.executable, str(probe), str(out)]
            spawned = runner.spawn_detached(argv, cwd=journal_dir, env=env)
            spawned.process.wait(timeout=60)
            result = json.loads(out.read_text(encoding="utf-8"))
            self.assertFalse(result["found"], f"PYTHONPATH={inherited!r} re-admitted a journal-local import")


class ReapChildGroupTests(unittest.TestCase):
    def _journal_with_child(self, pid: int | None, *, exit_written: bool = False) -> Journal:
        fixture = _Fixture(self)
        if pid is not None:
            write_json(
                fixture.journal,
                "child_started.json",
                {"schema_version": 1, "run_id": fixture.run_id, "state": "spawned", "pid": pid, "written_at": utc_now()},
            )
        if exit_written:
            write_json(
                fixture.journal,
                "exit.json",
                {
                    "schema_version": 1,
                    "run_id": fixture.run_id,
                    "state": "exited",
                    "child_pid": pid,
                    "started_at": utc_now(),
                    "finished_at": utc_now(),
                    "exit_code": 0,
                    "timed_out": False,
                    "quiescence": {
                        key: {"proven": True, "method": "x", "survivors_killed": 0, "total_bytes": 0}
                        for key in ("stdout", "stderr")
                    },
                },
            )
        return fixture.journal

    def setUp(self) -> None:
        patcher = mock.patch.object(signal, "SIGKILL", 9, create=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_no_recorded_child_means_nothing_is_signalled(self) -> None:
        calls: list = []
        runner._reap_child_group(self._journal_with_child(None), killpg=lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_a_pidless_spawning_marker_without_an_exit_sentinel_may_still_be_running(self) -> None:
        fixture = _Fixture(self)
        write_json(
            fixture.journal,
            "child_started.json",
            {"schema_version": 1, "run_id": fixture.run_id, "state": "spawning", "pid": None, "written_at": utc_now()},
        )
        calls: list = []
        with self.assertRaises(runner.ChildMayStillRunError):
            runner._reap_child_group(fixture.journal, killpg=lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_a_spawning_marker_with_an_exit_sentinel_is_settled(self) -> None:
        fixture = _Fixture(self)
        write_json(
            fixture.journal,
            "child_started.json",
            {"schema_version": 1, "run_id": fixture.run_id, "state": "spawning", "pid": None, "written_at": utc_now()},
        )
        write_json(
            fixture.journal,
            "exit.json",
            {
                "schema_version": 1,
                "run_id": fixture.run_id,
                "state": "spawn_failed",
                "child_pid": None,
                "started_at": utc_now(),
                "finished_at": utc_now(),
                "exit_code": None,
                "timed_out": False,
                "quiescence": {
                    key: {"proven": True, "method": "x", "survivors_killed": 0, "total_bytes": 0}
                    for key in ("stdout", "stderr")
                },
            },
        )
        runner._reap_child_group(fixture.journal, killpg=lambda *args: self.fail("must not signal"))

    def test_a_recorded_exit_sentinel_means_a_recycled_pid_is_never_signalled(self) -> None:
        calls: list = []
        journal = self._journal_with_child(4242, exit_written=True)
        runner._reap_child_group(journal, killpg=lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_a_surviving_group_is_killed_and_verified_gone(self) -> None:
        calls: list = []
        gone = {"after": 2}

        def killpg(pid: int, sig: int) -> None:
            calls.append((pid, sig))
            if sig == 0:
                gone["after"] -= 1
                if gone["after"] < 0:
                    raise ProcessLookupError

        runner._reap_child_group(self._journal_with_child(4242), killpg=killpg, sleep=lambda _: None)
        self.assertEqual(calls[0], (4242, 9))
        self.assertTrue(all(call == (4242, 0) for call in calls[1:]))
        self.assertGreaterEqual(len(calls), 3)

    def test_an_already_gone_group_is_fine(self) -> None:
        def killpg(pid: int, sig: int) -> None:
            raise ProcessLookupError

        runner._reap_child_group(self._journal_with_child(4242), killpg=killpg)

    def test_a_group_that_never_dies_is_an_error(self) -> None:
        clock = {"now": 0.0}

        def monotonic() -> float:
            return clock["now"]

        def sleep(seconds: float) -> None:
            clock["now"] += 5

        with self.assertRaises(runner.ChildMayStillRunError):
            runner._reap_child_group(
                self._journal_with_child(4242), killpg=lambda pid, sig: None, sleep=sleep, monotonic=monotonic
            )

    def test_a_group_that_cannot_be_signalled_is_an_error(self) -> None:
        def killpg(pid: int, sig: int) -> None:
            raise PermissionError("denied")

        with self.assertRaises(runner.ChildMayStillRunError):
            runner._reap_child_group(self._journal_with_child(4242), killpg=killpg)

    @unittest.skipIf(_WINDOWS, "POSIX process groups")
    def test_a_real_orphaned_child_group_is_killed_and_verified_gone(self) -> None:
        launcher = subprocess.run(
            [
                sys.executable,
                "-c",
                "import subprocess, sys; "
                "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True, "
                "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
                "print(p.pid)",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
        pid = int(launcher.stdout.strip())
        self.addCleanup(_kill_pid, pid)
        journal = self._journal_with_child(pid)
        try:
            runner._reap_child_group(journal)
        except runner.ChildMayStillRunError:
            stat = Path(f"/proc/{pid}/stat")
            if stat.exists() and stat.read_text(encoding="utf-8").rsplit(")", 1)[-1].split()[0] == "Z":
                self.skipTest("the orphan was not reaped by this environment's init (zombie)")
            raise
        self.assertTrue(_wait_for(lambda: is_process_alive(pid) is False, timeout=10))

    def test_terminate_shim_reaps_the_child_group_on_posix_only(self) -> None:
        journal = self._journal_with_child(4242)
        process = mock.Mock()
        process.poll.return_value = 0
        with (
            mock.patch.object(runner, "_kill_group"),
            mock.patch.object(runner, "_wait_after_kill"),
            mock.patch.object(runner, "_reap_child_group") as reap,
        ):
            with mock.patch.object(runner, "_WINDOWS", False):
                runner._terminate_shim(process, journal)
            reap.assert_called_once_with(journal)
            reap.reset_mock()
            with mock.patch.object(runner, "_WINDOWS", True):
                runner._terminate_shim(process, journal)
            reap.assert_not_called()

    def test_run_journaled_propagates_a_surviving_child_without_a_second_termination(self) -> None:
        fixture = _Fixture(self)
        script = fixture.script("sleeper.py", "import time\ntime.sleep(60)\n")
        fixture.write_launch(script, timeout=30)
        dummy = subprocess.Popen([sys.executable, "-c", "pass"])
        self.addCleanup(dummy.wait)
        with (
            mock.patch.object(runner, "spawn_detached") as spawn,
            mock.patch.object(runner, "_terminate_shim", side_effect=runner.ChildMayStillRunError("alive")) as terminate,
        ):
            spawn.return_value = runner.DetachedSpawn(dummy, breakaway=False)
            with mock.patch.object(subprocess.Popen, "wait", side_effect=subprocess.TimeoutExpired("x", 1)):
                with self.assertRaises(runner.ChildMayStillRunError):
                    runner.run_journaled(fixture.journal)
        self.assertEqual(terminate.call_count, 1)


class ModeMismatchTests(unittest.TestCase):
    """A detached launch must go through the barrier (``--supervise``); the bare shim may not exec it."""

    def _write(self, fixture: _Fixture, mode: str) -> Path:
        marker = fixture.fakes / "ran.txt"
        script = fixture.script("mark.py", "import pathlib, sys\npathlib.Path(sys.argv[1]).write_text('ran')\n")
        launch = fixture.write_launch(script, str(marker))
        if mode == "detached":
            launch = build_launch(
                run_id=fixture.run_id,
                workspace=str(fixture.root),
                shipment_id="218-S",
                feature_id="211-F",
                merge_commit_sha="a" * 40,
                mode="detached",
                argv=launch["argv"],
                binary_path=launch["binary_path"],
                binary_sha256=launch["binary_sha256"],
                argv_prefix=launch["argv_prefix"],
                cwd=launch["cwd"],
                timeout_seconds=30,
                authorize_deadline="2099-01-01T00:00:00.000000Z",
                authorize_nonce="n" * 16,
            )
            write_json(fixture.journal, "launch.json", launch)
        return marker

    def _run(self, fixture: _Fixture, flag: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "autoharness.shipment_close.supervisor", flag, str(fixture.journal.path)],
            env=_env(),
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_the_shim_refuses_a_detached_launch(self) -> None:
        fixture = _Fixture(self)
        marker = self._write(fixture, "detached")
        process = self._run(fixture, "--shim")
        self.assertEqual(process.returncode, 2, process.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(read_json(fixture.journal, "exit.json")["state"], "never_started")

    def test_the_supervisor_refuses_an_attached_launch(self) -> None:
        fixture = _Fixture(self)
        marker = self._write(fixture, "attached")
        process = self._run(fixture, "--supervise")
        self.assertEqual(process.returncode, 2, process.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(read_json(fixture.journal, "exit.json")["state"], "never_started")


if __name__ == "__main__":
    unittest.main()
