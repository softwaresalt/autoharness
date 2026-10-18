"""Supervisor hardening: authorization re-checks, spawn ordering, post-spawn failures, launch binary identity."""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from test_shipment_cascade_close_detach import _DetachHarness
from test_shipment_close_journaled_runner import _Fixture, _env

from autoharness.shipment_close import EXIT_STARTED, command, runner, supervisor
from autoharness.shipment_close.journal import (
    Journal,
    JournalError,
    argv_sha256,
    build_launch,
    journal_has,
    open_journal,
    read_json,
    write_json,
)
from autoharness.shipment_close.liveness import is_process_alive

_FAR = "2099-01-01T00:00:00.000000Z"
_PAST = "2020-01-01T00:00:00.000000Z"


def _instant(seconds: float) -> str:
    moment = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _write_authorization(journal: Journal, nonce: str, valid_until: str) -> None:
    write_json(
        journal,
        "authorize.json",
        {
            "schema_version": 1,
            "run_id": journal.run_id,
            "nonce": nonce,
            "valid_until": valid_until,
            "written_at": _instant(0),
        },
    )


def _quick_script(fixture: _Fixture) -> Path:
    return fixture.script("quick.py", "import sys\nsys.stdout.write('ok')\n")


class LaunchBinaryIdentityTests(unittest.TestCase):
    def test_the_binary_must_be_the_last_prefix_element(self) -> None:
        fixture = _Fixture(self)
        script = _quick_script(fixture)
        launch = build_launch(
            run_id=fixture.run_id,
            workspace=str(fixture.root),
            shipment_id="218-S",
            feature_id="211-F",
            merge_commit_sha="a" * 40,
            mode="attached",
            argv=[str(script), sys.executable],
            binary_path=str(script),
            binary_sha256="0" * 64,
            argv_prefix=[str(script), sys.executable],
            cwd=str(fixture.fakes),
            timeout_seconds=30,
        )
        with self.assertRaises(JournalError):
            write_json(fixture.journal, "launch.json", launch)
        launch["argv_prefix"] = launch["argv"] = [sys.executable, str(script)]
        launch["argv_sha256"] = argv_sha256(launch["argv"])
        write_json(fixture.journal, "launch.json", launch)


class AuthorizationTests(unittest.TestCase):
    def _detached(self, fixture: _Fixture) -> dict:
        return fixture.write_launch(
            _quick_script(fixture), mode="detached", authorize_deadline=_FAR, authorize_nonce="nonce-1"
        )

    def test_a_transient_untrusted_read_is_retried_not_treated_as_invalid(self) -> None:
        fixture = _Fixture(self)
        launch = self._detached(fixture)
        _write_authorization(fixture.journal, "nonce-1", _FAR)
        real = supervisor.read_json
        calls: list[str] = []

        def flaky(journal, name, **kwargs):
            calls.append(name)
            if name == "authorize.json" and calls.count(name) == 1:
                raise JournalError("untrusted", "a concurrent replace")
            return real(journal, name, **kwargs)

        with mock.patch.object(supervisor, "read_json", flaky):
            self.assertEqual(supervisor._wait_for_authorization(fixture.journal, launch), "authorized")

    def test_a_persistently_untrusted_authorization_is_invalid(self) -> None:
        fixture = _Fixture(self)
        launch = self._detached(fixture)
        _write_authorization(fixture.journal, "nonce-1", _FAR)

        def always(journal, name, **kwargs):
            raise JournalError("untrusted", "bad")

        with mock.patch.object(supervisor, "read_json", always), mock.patch.object(supervisor.time, "sleep"):
            self.assertEqual(supervisor._wait_for_authorization(fixture.journal, launch), "invalid_authorization")

    def test_the_clock_is_sampled_after_the_authorization_is_read(self) -> None:
        fixture = _Fixture(self)
        launch = self._detached(fixture)
        _write_authorization(fixture.journal, "nonce-1", _instant(0.3))
        real = supervisor.read_json

        def slow_read(journal, name, **kwargs):
            value = real(journal, name, **kwargs)
            if name == "authorize.json":
                time.sleep(0.8)  # the grant lapses while it is being read
            return value

        with mock.patch.object(supervisor, "read_json", slow_read):
            self.assertEqual(supervisor._wait_for_authorization(fixture.journal, launch), "expired")

    def test_the_authorization_is_rechecked_right_before_the_spawn(self) -> None:
        fixture = _Fixture(self)
        launch = self._detached(fixture)
        _write_authorization(fixture.journal, "nonce-1", _FAR)
        self.assertTrue(supervisor._authorization_current(fixture.journal, launch))
        write_json(
            fixture.journal,
            "abort.json",
            {"schema_version": 1, "run_id": fixture.run_id, "reason": "late", "written_at": _instant(0)},
        )
        self.assertFalse(supervisor._authorization_current(fixture.journal, launch))

    def test_an_authorization_that_lapsed_before_the_spawn_is_refused(self) -> None:
        fixture = _Fixture(self)
        launch = self._detached(fixture)
        _write_authorization(fixture.journal, "nonce-1", _PAST)
        self.assertFalse(supervisor._authorization_current(fixture.journal, launch))
        _write_authorization(fixture.journal, "other-nonce", _FAR)
        self.assertFalse(supervisor._authorization_current(fixture.journal, launch))


class SpawnOrderingTests(unittest.TestCase):
    def test_streams_are_opened_before_the_spawning_marker_and_a_refusal_never_spawns(self) -> None:
        fixture = _Fixture(self)
        launch = fixture.write_launch(_quick_script(fixture))
        seen: dict[str, bool] = {}

        def refuse() -> None:
            seen["streams_open"] = all((fixture.journal.path / name).exists() for name in ("stdout.raw", "stderr.raw"))
            raise supervisor._SpawnRefused("authorization lapsed")

        with mock.patch.object(supervisor.subprocess, "Popen") as popen:
            record = supervisor.run_child(fixture.journal, launch, before_spawn=refuse)
        self.assertTrue(seen["streams_open"])
        self.assertEqual(record["state"], "never_started")
        popen.assert_not_called()
        self.assertFalse(journal_has(fixture.journal, "child_started.json"))

    def test_a_stream_open_failure_closes_the_opened_fds_and_never_writes_spawning(self) -> None:
        fixture = _Fixture(self)
        launch = fixture.write_launch(_quick_script(fixture))
        real_open = supervisor.open_stream_file
        opened: list[int] = []
        closed: list[int] = []

        def open_once_then_fail(journal, name):
            if opened:
                raise JournalError("untrusted", "refused")
            opened.append(real_open(journal, name))
            return opened[0]

        real_close = os.close

        def spy_close(fd):
            closed.append(fd)
            real_close(fd)

        before = mock.Mock()
        with (
            mock.patch.object(supervisor, "open_stream_file", open_once_then_fail),
            mock.patch.object(supervisor.os, "close", spy_close),
        ):
            record = supervisor.run_child(fixture.journal, launch, before_spawn=before)
        self.assertEqual(record["state"], "never_started")
        self.assertIn(opened[0], closed)
        before.assert_not_called()

    def test_spawning_is_written_after_the_streams_and_just_before_the_spawn(self) -> None:
        fixture = _Fixture(self)
        launch = fixture.write_launch(_quick_script(fixture))
        order: list[str] = []
        real_open = supervisor.open_stream_file

        def spy_open(journal, name):
            order.append(f"open:{name}")
            return real_open(journal, name)

        real_popen = supervisor.subprocess.Popen

        def spy_popen(*args, **kwargs):
            order.append("popen")
            return real_popen(*args, **kwargs)

        with (
            mock.patch.object(supervisor, "open_stream_file", spy_open),
            mock.patch.object(supervisor.subprocess, "Popen", spy_popen),
        ):
            supervisor.run_child(fixture.journal, launch, before_spawn=lambda: order.append("spawning"))
        self.assertEqual(order, ["open:stdout.raw", "open:stderr.raw", "spawning", "popen"])


class PostSpawnFailureTests(unittest.TestCase):
    def test_an_error_while_proving_quiescence_still_leaves_an_exit_sentinel(self) -> None:
        fixture = _Fixture(self)
        launch = fixture.write_launch(_quick_script(fixture))
        with mock.patch.object(supervisor.quiescence, "settle_group", side_effect=RuntimeError("probe broke")):
            record = supervisor.run_child(fixture.journal, launch, grace_seconds=0.2)
        self.assertEqual(record["state"], "exited")
        self.assertEqual(record["exit_code"], 0)
        for stream in ("stdout", "stderr"):
            self.assertFalse(record["quiescence"][stream]["proven"])
        self.assertEqual(read_json(fixture.journal, "exit.json")["state"], "exited")

    def test_a_transient_exit_write_failure_is_retried(self) -> None:
        fixture = _Fixture(self)
        launch = fixture.write_launch(_quick_script(fixture))
        real = supervisor.write_json
        failures = [OSError("sharing violation"), OSError("sharing violation")]

        def flaky(journal, name, payload):
            if name == "exit.json" and failures:
                raise failures.pop()
            return real(journal, name, payload)

        with (
            mock.patch.object(supervisor, "write_json", flaky),
            mock.patch.object(supervisor.time, "sleep"),
        ):
            record = supervisor.run_child(fixture.journal, launch, grace_seconds=0.2)
        self.assertEqual(record["state"], "exited")
        self.assertEqual(read_json(fixture.journal, "exit.json")["state"], "exited")


class PreSpawnFailureTests(unittest.TestCase):
    def _supervised_failure(self, harness: _DetachHarness) -> _InProcessSupervisor:
        holder: list[_InProcessSupervisor] = []

        def spawn(journal_dir):
            holder.append(_InProcessSupervisor(Path(journal_dir)))
            return holder[0]

        with (
            mock.patch.object(command, "spawn_supervisor", spawn),
            mock.patch.object(supervisor, "_wait_for_authorization", side_effect=RuntimeError("injected before spawn")),
        ):
            harness.detach(ack_timeout_seconds=3.0)
            holder[0].thread.join(60)
        self.assertIsInstance(holder[0].error, RuntimeError)
        return holder[0]

    def test_an_unexpected_failure_before_the_spawn_completes_the_never_started_proof_then_releases_the_lock(
        self,
    ) -> None:
        harness = _DetachHarness(self)
        self._supervised_failure(harness)
        harness.assert_rolled_back_without_shipping()
        self.assertEqual(read_json(open_journal(harness.directory), "exit.json")["state"], "never_started")
        self.assertEqual(harness.wait_outcome()["outcome"], "never_started")

    def test_a_failed_never_started_proof_keeps_the_lock_for_recovery(self) -> None:
        harness = _DetachHarness(self)
        with mock.patch.object(command, "finish_never_started", side_effect=command.PersistError(2, "cannot roll back")):
            self._supervised_failure(harness)
        self.assertTrue(harness.lock_path.exists(), "the lock must stay so recovery sees a dead owner")
        self.assertEqual(harness.record()["phase"], "invoking")
        self.assertFalse(harness.shipped)


class ShimPidJournalTests(unittest.TestCase):
    def test_the_attached_shim_journals_the_child_pid(self) -> None:
        fixture = _Fixture(self)
        fixture.write_launch(_quick_script(fixture))
        self.assertEqual(supervisor.main(["--shim", str(fixture.journal.path)]), 0)
        started = read_json(fixture.journal, "child_started.json")
        exited = read_json(fixture.journal, "exit.json")
        self.assertEqual(started["state"], "spawned")
        self.assertEqual(started["pid"], exited["child_pid"])
        self.assertGreater(started["pid"], 0)


class KilledAfterSpawnTests(unittest.TestCase):
    def _slow(self, fixture: _Fixture) -> dict:
        return fixture.write_launch(fixture.script("slow.py", "import time\ntime.sleep(60)\n"), timeout=120)

    def _assert_child_killed(self, pids: list[int]) -> None:
        self.assertEqual(len(pids), 1)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and is_process_alive(pids[0]) is not False:
            time.sleep(0.1)
        self.assertIs(is_process_alive(pids[0]), False, "the spawned child must not outlive the supervisor")

    def test_an_interrupt_while_resolving_the_group_still_kills_the_child(self) -> None:
        fixture = _Fixture(self)
        launch = self._slow(fixture)
        pids: list[int] = []

        def interrupted(pid: int, entered: object = None) -> None:
            pids.append(pid)
            raise supervisor._Terminated

        with (
            mock.patch.object(supervisor, "_group_for", interrupted),
            self.assertRaises(supervisor._Terminated),
        ):
            supervisor.run_child(fixture.journal, launch)
        self._assert_child_killed(pids)

    def test_an_interrupt_in_the_spawn_callback_still_kills_the_child(self) -> None:
        fixture = _Fixture(self)
        launch = self._slow(fixture)
        pids: list[int] = []

        def interrupted(pid: int) -> None:
            pids.append(pid)
            raise supervisor._Terminated

        with self.assertRaises(supervisor._Terminated):
            supervisor.run_child(fixture.journal, launch, on_spawned=interrupted)
        self._assert_child_killed(pids)


class PosixGroupKillBeforeCallbackTests(unittest.TestCase):
    """The child's process group is armed immediately after ``Popen``, before anything that can be interrupted."""

    PID = 4321

    def _run(self, fixture: _Fixture, **kwargs) -> list[tuple[int, int]]:
        launch = fixture.write_launch(fixture.script("slow.py", "import time\ntime.sleep(60)\n"), timeout=120)
        calls: list[tuple[int, int]] = []
        process = mock.Mock()
        process.pid = self.PID
        process.poll.return_value = None
        popen = mock.Mock(return_value=process)
        with (
            mock.patch.object(supervisor, "_WINDOWS", False),
            mock.patch.object(supervisor.quiescence, "_WINDOWS", False),
            mock.patch.object(supervisor.subprocess, "Popen", popen),
            mock.patch.object(supervisor.signal, "SIGKILL", 9, create=True),
            mock.patch.object(supervisor.quiescence.os, "killpg", lambda pgid, sig: calls.append((pgid, sig)), create=True),
            self.assertRaises(supervisor._Terminated),
        ):
            supervisor.run_child(fixture.journal, launch, **kwargs)
        self.assertEqual(popen.call_count, 1)
        process.kill.assert_called_once_with()
        return calls

    def test_a_termination_in_the_spawn_callback_kills_the_whole_group(self) -> None:
        def interrupted(pid: int) -> None:
            raise supervisor._Terminated

        calls = self._run(_Fixture(self), on_spawned=interrupted)
        self.assertEqual(calls, [(self.PID, 9)])

    def test_a_termination_while_closing_the_stream_descriptors_kills_the_whole_group(self) -> None:
        real_close, armed = supervisor._close_all, [True]

        def interrupted_once(fds: list[int]) -> None:
            if armed:
                armed.clear()
                raise supervisor._Terminated
            real_close(fds)

        with mock.patch.object(supervisor, "_close_all", interrupted_once):
            calls = self._run(_Fixture(self))
        self.assertEqual(calls, [(self.PID, 9)])

    def test_a_termination_while_resolving_the_group_still_kills_the_whole_group(self) -> None:
        with mock.patch.object(supervisor, "_group_for", side_effect=supervisor._Terminated):
            calls = self._run(_Fixture(self))
        self.assertEqual(calls, [(self.PID, 9)])

    def test_the_group_exists_before_the_spawn_callback_runs(self) -> None:
        seen: list[object] = []
        real_enter = supervisor.quiescence.enter_group

        def enter(pid):
            seen.append(("enter", pid))
            return real_enter(pid)

        def interrupted(pid: int) -> None:
            seen.append(("callback", pid))
            raise supervisor._Terminated

        with mock.patch.object(supervisor.quiescence, "enter_group", enter):
            self._run(_Fixture(self), on_spawned=interrupted)
        self.assertEqual(seen, [("enter", self.PID), ("callback", self.PID)])


class AttachedSpawningMarkerTests(unittest.TestCase):
    def test_the_attached_shim_journals_spawning_before_the_spawn(self) -> None:
        fixture = _Fixture(self)
        fixture.write_launch(_quick_script(fixture))
        states: list[str] = []
        real_popen = subprocess.Popen

        def spying_popen(*args, **kwargs):
            states.append(read_json(fixture.journal, "child_started.json")["state"])
            return real_popen(*args, **kwargs)

        with mock.patch.object(supervisor.subprocess, "Popen", spying_popen):
            self.assertEqual(supervisor.main(["--shim", str(fixture.journal.path)]), 0)
        self.assertEqual(states, ["spawning"])
        self.assertEqual(read_json(fixture.journal, "child_started.json")["state"], "spawned")

    def test_an_unwritable_marker_refuses_the_spawn_as_never_started(self) -> None:
        fixture = _Fixture(self)
        fixture.write_launch(_quick_script(fixture))
        with (
            mock.patch.object(supervisor, "_write_child_started", side_effect=OSError("disk full")),
            mock.patch.object(supervisor.subprocess, "Popen") as popen,
        ):
            self.assertEqual(supervisor.main(["--shim", str(fixture.journal.path)]), 0)
        popen.assert_not_called()
        self.assertEqual(read_json(fixture.journal, "exit.json")["state"], "never_started")
        self.assertFalse(journal_has(fixture.journal, "child_started.json"))


class UnexpectedQuiescenceErrorTests(unittest.TestCase):
    def test_the_error_type_and_message_are_journaled_without_changing_the_verdict(self) -> None:
        fixture = _Fixture(self)
        launch = fixture.write_launch(_quick_script(fixture))
        with mock.patch.object(supervisor.quiescence, "settle_group", side_effect=RuntimeError("probe broke")):
            record = supervisor.run_child(fixture.journal, launch, grace_seconds=0.2)
        for stream in ("stdout", "stderr"):
            self.assertFalse(record["quiescence"][stream]["proven"])
            self.assertIn("RuntimeError: probe broke", record["quiescence"][stream]["method"])
        self.assertEqual(read_json(fixture.journal, "exit.json")["quiescence"], record["quiescence"])


class BestEffortNeverStartedTests(unittest.TestCase):
    def test_it_never_writes_a_sentinel_next_to_a_spawn_record_or_an_exit(self) -> None:
        for existing in ("child_started.json", "exit.json"):
            with self.subTest(existing=existing):
                fixture = _Fixture(self)
                fixture.write_launch(_quick_script(fixture))
                if existing == "child_started.json":
                    write_json(
                        fixture.journal,
                        "child_started.json",
                        {
                            "schema_version": 1,
                            "run_id": fixture.run_id,
                            "state": "spawning",
                            "pid": None,
                            "written_at": _instant(0),
                        },
                    )
                else:
                    empty = {"proven": True, "method": "m", "survivors_killed": 0, "total_bytes": 0}
                    supervisor._write_exit(
                        fixture.journal,
                        state="exited",
                        exit_code=0,
                        child_pid=1,
                        started_at=_instant(0),
                        finished_at=_instant(0),
                        quiescence={"stdout": empty, "stderr": dict(empty)},
                    )
                before = {p.name: p.read_bytes() for p in fixture.journal.path.iterdir() if p.is_file()}
                supervisor._best_effort_never_started(str(fixture.journal.path))
                after = {p.name: p.read_bytes() for p in fixture.journal.path.iterdir() if p.is_file()}
                self.assertEqual(before, after)

    def test_it_still_writes_the_sentinel_for_an_untouched_journal(self) -> None:
        fixture = _Fixture(self)
        fixture.write_launch(_quick_script(fixture))
        supervisor._best_effort_never_started(str(fixture.journal.path))
        self.assertEqual(read_json(fixture.journal, "exit.json")["state"], "never_started")


class SpawnedInterpreterIsolationTests(unittest.TestCase):
    def test_a_shadow_package_in_the_journal_directory_is_never_imported(self) -> None:
        fixture = _Fixture(self)
        shadow = fixture.journal.path / "autoharness"
        shadow.mkdir()
        (shadow / "__init__.py").write_text("open('shadow-imported', 'w').write('x')\n", encoding="utf-8")
        argv = runner.supervisor_argv("--supervise", "relative.journal")
        process = subprocess.run(
            argv, cwd=fixture.journal.path, env=_env(), capture_output=True, text=True, timeout=60
        )
        self.assertEqual(process.returncode, 2, process.stderr)
        self.assertFalse((fixture.journal.path / "shadow-imported").exists())


class _InProcessSupervisor:
    """A fake spawned process whose supervisor runs on a thread of this very process."""

    autoharness_breakaway = True

    def __init__(self, journal_dir: Path) -> None:
        self.pid = os.getpid()
        self.returncode: int | None = None
        self.error: BaseException | None = None

        def run() -> None:
            try:
                journal = open_journal(journal_dir)
                self.returncode = supervisor.supervise(journal, read_json(journal, "launch.json"))
            except BaseException as exc:  # noqa: BLE001
                self.error = exc

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def poll(self) -> int | None:
        return self.returncode if not self.thread.is_alive() else None

    def wait(self, timeout: float | None = None) -> int | None:
        self.thread.join(timeout)
        return self.returncode


class PostSpawnLockTests(unittest.TestCase):
    def test_an_unexpected_error_after_the_spawn_point_leaves_the_lock_for_recovery(self) -> None:
        harness = _DetachHarness(self)
        real_run_child = supervisor.run_child
        holder: list[_InProcessSupervisor] = []

        def exploding(journal, launch, **kwargs):
            kwargs["before_spawn"]()  # writes the 'spawning' marker: the spawn point has been reached
            raise RuntimeError("unexpected after the spawn point")

        def spawn(journal_dir):
            holder.append(_InProcessSupervisor(Path(journal_dir)))
            return holder[0]

        with (
            mock.patch.object(command, "spawn_supervisor", spawn),
            mock.patch.object(supervisor, "run_child", exploding),
        ):
            outcome = harness.detach()
            holder[0].thread.join(60)
        self.assertEqual(outcome.exit_code, EXIT_STARTED, outcome.message)
        self.assertIsNone(holder[0].error)
        self.assertTrue(harness.lock_path.exists(), "the lock must stay for recovery")
        self.assertEqual(harness.record()["phase"], "invoking")
        self.assertFalse(harness.shipped)
        self.assertEqual(json.loads((harness.directory / "child_started.json").read_text(encoding="utf-8"))["state"], "spawning")
        del real_run_child


if __name__ == "__main__":
    unittest.main()
