"""``cascade-close --detach``: authorization barrier, argv authentication, revalidation, rollback (211.008-T, plan unit T7).

Hardening H7 (two-phase barrier and its addenda) and H12 (supervisor argv integrity). Every scenario asserts the
safety property directly: the fake ``backlogit shipment ship`` is never launched unless the supervisor holds a valid,
unexpired ``authorize.json``, an exact authenticated argv, and a snapshot that still matches the durable record.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from _proc_race import retry_read
from test_shipment_cascade_close_invoke import (
    _FAKE_BACKLOGIT,
    _FEATURE,
    _SHA,
    _SHIPMENT,
    _VERIFIED,
    _default_ship,
    _Harness,
    _ship_argvs,
)

from autoharness.gates.cascade_evidence import validate_evidence_record
from autoharness.shipment_close import (
    EXIT_INPUT,
    EXIT_OK,
    EXIT_REVALIDATION_DRIFT,
    EXIT_STARTED,
    command,
    runner,
)
from autoharness.shipment_close.journal import (
    Journal,
    argv_sha256,
    journal_path,
    read_json,
    write_json,
)
from autoharness.shipment_close.liveness import is_process_alive
from autoharness.shipment_close.persist import observe_lock
from autoharness.shipment_close.runner import ResolvedBinary, hash_binary

_SRC = str(Path(__file__).resolve().parent.parent / "src")
_SLOW_SHIP = _FAKE_BACKLOGIT.replace(
    '    sys.stderr.write(ship.get("stderr", ""))',
    '    time.sleep(ship.get("sleep", 0))\n'
    '    deadline = time.monotonic() + 120\n'
    '    while (HERE / "hold").exists() and time.monotonic() < deadline:\n'
    "        time.sleep(0.05)\n"
    '    sys.stderr.write(ship.get("stderr", ""))',
)
assert _SLOW_SHIP != _FAKE_BACKLOGIT


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = _SRC + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _spawn(argv: list[str], journal_dir: Path) -> subprocess.Popen:
    return runner.spawn_detached(argv, cwd=journal_dir).process


class _DetachHarness(_Harness):
    def __init__(self, test: unittest.TestCase, *, sleep: float = 0.0, hold: bool = False) -> None:
        super().__init__(test, probes=[_VERIFIED], ship={**_default_ship(), "sleep": sleep})
        # A held engine blocks inside `shipment ship` until release(), so the run cannot finish inside the ack window.
        self.hold_file = self.fakes / "hold"
        if hold:
            self.hold_file.write_text("held", encoding="utf-8")
            test.addCleanup(self.release)
        self.script.write_text(_SLOW_SHIP, encoding="utf-8")
        self.resolved = ResolvedBinary(
            binary_path=str(self.script),
            binary_sha256=hash_binary(self.script),
            argv_prefix=(sys.executable, str(self.script)),
        )
        self.directory = journal_path(self.root, _SHIPMENT, _FEATURE)
        self.lock_path = self.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.lock"
        self.test = test

    def detach(self, **kwargs: object) -> command.CascadeCloseOutcome:
        kwargs.setdefault("ready_timeout_seconds", 30.0)
        return self.run(detach=True, **kwargs)

    def release(self) -> None:
        self.hold_file.unlink(missing_ok=True)

    def wait_outcome(self, timeout: float = 90.0) -> dict:
        deadline = time.monotonic() + timeout
        path = self.directory / "outcome.json"
        while time.monotonic() < deadline:
            if path.exists():
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except (ValueError, OSError):  # mid-write, or a transient Windows sharing violation
                    pass
            time.sleep(0.1)
        self.test.fail("the supervisor never wrote outcome.json")

    def wait_lock_gone(self, timeout: float = 30.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and self.lock_path.exists():
            time.sleep(0.1)
        self.test.assertFalse(self.lock_path.exists(), "the pair lock was not released")

    def assert_rolled_back_without_shipping(self) -> None:
        self.wait_lock_gone()
        self.test.assertFalse(self.shipped, "backlogit shipment ship ran without authorization")
        self.test.assertEqual(_ship_argvs(self.argv_log()), [])
        record = self.record()
        self.test.assertEqual(record["phase"], "pre_close")
        self.test.assertNotIn("invocation", record)
        self.test.assertEqual(record["pre_close"]["close_path_selection"]["selected_close_path"], "cascade")

    def run_id(self) -> str:
        return json.loads((self.directory / "meta.json").read_text(encoding="utf-8"))["run_id"]


class DetachHappyPathTests(unittest.TestCase):
    def test_detach_returns_started_and_the_supervisor_is_the_only_finalizer(self) -> None:
        harness = _DetachHarness(self, hold=True)
        captured: list[dict] = []
        real_write = command.write_evidence_atomic

        def write(path, record, **kwargs):
            captured.append(json.loads(json.dumps(record)))
            return real_write(path, record, **kwargs)

        with mock.patch.object(command, "write_evidence_atomic", side_effect=write):
            outcome = harness.detach()
        self.assertEqual(outcome.exit_code, EXIT_STARTED, outcome.message)
        self.assertEqual(outcome.phase_written, "invoking")
        self.assertEqual(outcome.journal_path, harness.directory)
        # The foreground wrote only pre_close and invoking: it never finalizes in detached mode.
        self.assertEqual([record["phase"] for record in captured], ["pre_close", "invoking"])
        self.assertEqual(harness.record()["phase"], "invoking")
        lock = observe_lock(harness.root, _SHIPMENT, _FEATURE)
        self.assertIsNotNone(lock)
        self.assertTrue(lock.supervisor)
        self.assertNotEqual(lock.pid, os.getpid(), "the lock pid must have been handed to the supervisor")
        self.assertTrue(is_process_alive(lock.pid))
        self.assertIsNotNone(lock.pid_start)

        harness.release()
        finished = harness.wait_outcome()
        self.assertEqual(
            (finished["exit_code"], finished["outcome"], finished["finalizer"]), (0, "completed", "supervisor")
        )
        harness.wait_lock_gone()
        record = harness.record()
        self.assertEqual(record["phase"], "post_close")
        self.assertEqual(
            validate_evidence_record(record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path="cascade"), []
        )
        journal = Journal(path=harness.directory, run_id=record["run_id"])
        self.assertEqual(read_json(journal, "meta.json")["finalizer"], "supervisor")
        self.assertEqual(read_json(journal, "authorize.json")["run_id"], record["run_id"])
        self.assertEqual(len(_ship_argvs(harness.argv_log())), 1)
        self.assertEqual(
            {entry.name for entry in harness.directory.iterdir()}
            - {"ready.json", "authorize.json", "child_started.json"},
            {"meta.json", "exit.json", "outcome.json"},
        )

    def test_the_exact_argv_reaches_the_engine_and_the_invoking_record_authenticates_it(self) -> None:
        harness = _DetachHarness(self)
        message = "close token=supersecretvalue123"
        invoking: dict = {}
        real_write = command.write_evidence_atomic

        def write(path, record, **kwargs):
            if record["phase"] == "invoking":
                invoking.update(json.loads(json.dumps(record)))
            return real_write(path, record, **kwargs)

        with mock.patch.object(command, "write_evidence_atomic", side_effect=write):
            outcome = harness.detach(message=message)
        # The run may already have finished inside the ack window; this test does not depend on it still running.
        self.assertIn(outcome.exit_code, (EXIT_STARTED, EXIT_OK), outcome.message)
        harness.wait_outcome()
        ship = _ship_argvs(harness.argv_log())[0]
        self.assertEqual(ship[ship.index("--message") + 1], message)
        self.assertNotIn("supersecretvalue123", json.dumps(harness.record()))
        self.assertEqual(invoking["invocation"]["argv_sha256"], argv_sha256([*harness.resolved.argv_prefix, *ship]))


class NeverSpawnWithoutAuthorizationTests(unittest.TestCase):
    def test_a_delayed_supervisor_never_ships_after_the_foreground_aborts(self) -> None:
        harness = _DetachHarness(self)

        def delayed(journal_dir):
            code = (
                "import runpy, sys, time\n"
                "time.sleep(4)\n"
                "sys.argv = ['supervisor', '--supervise', sys.argv[1]]\n"
                "runpy.run_module('autoharness.shipment_close.supervisor', run_name='__main__')\n"
            )
            return _spawn([sys.executable, "-c", code, str(journal_dir)], journal_dir)

        with mock.patch.object(command, "spawn_supervisor", delayed):
            outcome = harness.detach(ready_timeout_seconds=1.0)
        self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
        self.assertIn("nothing was invoked", outcome.message)
        self.assertTrue((harness.directory / "abort.json").exists())
        self.assertFalse((harness.directory / "authorize.json").exists())
        time.sleep(7)  # the delayed supervisor wakes up, sees abort.json, and must not spawn
        harness.assert_rolled_back_without_shipping()

    def test_abort_followed_by_an_attached_invocation_succeeds(self) -> None:
        harness = _DetachHarness(self)

        def never_ready(journal_dir):
            return _spawn([sys.executable, "-c", "import time; time.sleep(1)"], journal_dir)

        with mock.patch.object(command, "spawn_supervisor", never_ready):
            outcome = harness.detach(ready_timeout_seconds=0.5)
        self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
        harness.assert_rolled_back_without_shipping()
        attached = harness.run()
        self.assertEqual(attached.exit_code, EXIT_OK, (attached.message, attached.failures))
        self.assertEqual(harness.record()["phase"], "post_close")

    def test_a_supervisor_that_cannot_be_spawned_is_a_mutation_free_exit_2(self) -> None:
        harness = _DetachHarness(self)
        with mock.patch.object(command, "spawn_supervisor", side_effect=OSError("no process for you")):
            outcome = harness.detach()
        self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
        harness.assert_rolled_back_without_shipping()
        journal = Journal(path=harness.directory, run_id=harness.run_id())
        self.assertEqual(retry_read(lambda: read_json(journal, "exit.json"))["state"], "never_started")
        self.assertEqual(harness.wait_outcome()["outcome"], "never_started")

    def test_a_runtime_without_job_breakaway_fails_closed_before_authorizing(self) -> None:
        harness = _DetachHarness(self)

        def confined(journal_dir):
            process = _spawn([sys.executable, "-c", "import time; time.sleep(1)"], journal_dir)
            process.autoharness_breakaway = False
            return process

        with mock.patch.object(command, "spawn_supervisor", confined):
            outcome = harness.detach()
        self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
        self.assertIn("breakaway", outcome.message)
        self.assertFalse((harness.directory / "authorize.json").exists())
        harness.assert_rolled_back_without_shipping()

    def test_a_late_authorize_past_valid_until_is_refused(self) -> None:
        harness = _DetachHarness(self)
        outcome = harness.detach(authorize_validity_seconds=-5.0)
        self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
        finished = harness.wait_outcome()
        self.assertEqual((finished["exit_code"], finished["outcome"]), (2, "never_authorized"))
        harness.assert_rolled_back_without_shipping()

    def test_an_abort_file_beats_a_valid_authorize_file(self) -> None:
        harness = _DetachHarness(self)
        real_authorize = command._write_authorization

        def abort_then_authorize(journal, launch, validity):
            write_json(
                journal,
                "abort.json",
                {
                    "schema_version": 1,
                    "run_id": journal.run_id,
                    "written_at": "2026-10-17T00:00:00.000000Z",
                    "reason": "test",
                },
            )
            return real_authorize(journal, launch, validity)

        with mock.patch.object(command, "_write_authorization", abort_then_authorize):
            outcome = harness.detach()
        self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
        harness.assert_rolled_back_without_shipping()

    def test_killing_the_foreground_between_the_lock_handoff_and_authorize_lets_the_supervisor_self_expire(
        self,
    ) -> None:
        harness = _DetachHarness(self)
        driver = harness.fakes / "driver.py"
        driver.write_text(
            textwrap.dedent(
                f"""
                import os, sys
                sys.path.insert(0, {_SRC!r})
                from autoharness.shipment_close import command
                from autoharness.shipment_close.runner import ResolvedBinary, hash_binary
                root, script = sys.argv[1], sys.argv[2]
                resolved = ResolvedBinary(binary_path=script, binary_sha256=hash_binary(script),
                                          argv_prefix=(sys.executable, script))
                def die(*args, **kwargs):
                    os._exit(3)  # an abrupt kill: no finally blocks, no lock release
                command._await_ready = die
                command.run_cascade_close(root, {_SHIPMENT!r}, {_FEATURE!r}, {_SHA!r}, message="m", author="a",
                                          resolved=resolved, timeout=60, detach=True, authorize_window_seconds=4.0)
                os._exit(9)
                """
            ),
            encoding="utf-8",
        )
        process = subprocess.run(
            [sys.executable, str(driver), str(harness.root), str(harness.script)],
            env=_env(),
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(process.returncode, 3, process.stdout + process.stderr)
        self.assertEqual(harness.record()["phase"], "invoking")
        finished = harness.wait_outcome(timeout=60)
        self.assertEqual((finished["exit_code"], finished["outcome"]), (2, "never_authorized"))
        harness.assert_rolled_back_without_shipping()


@unittest.skipIf(sys.prefix != sys.base_prefix, "inside a venv the real launcher already stacks a second layer")
class LauncherPidMismatchTests(unittest.TestCase):
    """A Windows venv ``python.exe`` is a launcher: the spawned pid is not the interpreter that runs the supervisor."""

    _LAUNCHER = textwrap.dedent(
        """
        import subprocess, sys
        raise SystemExit(subprocess.call([sys.executable, "-m", "autoharness.shipment_close.supervisor",
                                          "--supervise", sys.argv[1]]))
        """
    )

    def _launcher_spawn(self, harness: _DetachHarness):
        launcher = harness.fakes / "launcher.py"
        launcher.write_text(self._LAUNCHER, encoding="utf-8")

        def spawn(journal_dir):
            spawned = runner.spawn_detached([sys.executable, str(launcher), str(journal_dir)], cwd=journal_dir)
            spawned.process.autoharness_breakaway = spawned.breakaway
            return spawned.process

        return spawn

    @unittest.skipUnless(os.name == "nt", "the launcher handoff is accepted on Windows only (a POSIX spawn is the interpreter itself)")
    def test_a_launcher_fronted_supervisor_still_ships_and_owns_the_lock(self) -> None:
        harness = _DetachHarness(self, sleep=1.0)
        with mock.patch.object(command, "spawn_supervisor", self._launcher_spawn(harness)):
            outcome = harness.detach()
            # The fast fake engine may finish inside the ack window, which reports the final exit code.
            self.assertIn(outcome.exit_code, (EXIT_STARTED, EXIT_OK), outcome.message)
            finished = harness.wait_outcome()
        self.assertEqual((finished["exit_code"], finished["outcome"]), (0, "completed"))
        harness.wait_lock_gone()
        self.assertEqual(len(_ship_argvs(harness.argv_log())), 1)

    def test_a_foreign_lock_pid_is_still_refused(self) -> None:
        harness = _DetachHarness(self)
        real_handoff = command.handoff_lock

        def wrong_pid(lock, *, pid, pid_start, **kwargs):
            return real_handoff(lock, pid=os.getpid(), pid_start=pid_start, **kwargs)

        with (
            mock.patch.object(command, "spawn_supervisor", self._launcher_spawn(harness)),
            mock.patch.object(command, "handoff_lock", wrong_pid),
        ):
            harness.detach()
            finished = harness.wait_outcome()
        self.assertEqual((finished["exit_code"], finished["outcome"]), (2, "never_started"))
        harness.assert_rolled_back_without_shipping()


class SupervisorAuthenticationTests(unittest.TestCase):
    def _hooked_spawn(self, mutate):
        real_spawn = command.spawn_supervisor

        def hooked(journal_dir):
            mutate(Path(journal_dir))
            return real_spawn(journal_dir)

        return hooked

    def test_a_launch_record_rewritten_with_a_consistent_hash_is_refused(self) -> None:
        harness = _DetachHarness(self)

        def mutate(directory: Path) -> None:
            launch = json.loads((directory / "launch.json").read_text(encoding="utf-8"))
            launch["argv"][launch["argv"].index("--message") + 1] = "attacker-chosen message"
            launch["argv_sha256"] = argv_sha256(launch["argv"])
            (directory / "launch.json").write_text(json.dumps(launch), encoding="utf-8")

        with mock.patch.object(command, "spawn_supervisor", self._hooked_spawn(mutate)):
            outcome = harness.detach()
        self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
        finished = harness.wait_outcome()
        self.assertEqual((finished["exit_code"], finished["outcome"]), (2, "never_started"))
        harness.assert_rolled_back_without_shipping()

    def test_a_swapped_binary_is_revalidation_drift_and_never_spawns(self) -> None:
        harness = _DetachHarness(self)

        def mutate(directory: Path) -> None:
            with open(harness.script, "a", encoding="utf-8") as handle:
                handle.write("\n# swapped after the foreground re-hash\n")

        with mock.patch.object(command, "spawn_supervisor", self._hooked_spawn(mutate)):
            outcome = harness.detach()
        self.assertEqual(outcome.exit_code, EXIT_REVALIDATION_DRIFT, outcome.message)
        finished = harness.wait_outcome()
        self.assertEqual((finished["exit_code"], finished["outcome"]), (4, "revalidation_drift"))
        harness.assert_rolled_back_without_shipping()

    def test_backlog_state_changed_during_the_handshake_is_drift_and_never_spawns(self) -> None:
        harness = _DetachHarness(self)
        real_authorize = command._write_authorization

        def drift_then_authorize(journal, launch, validity):
            with open(harness.backlog / "queue" / "600-DL.md", "a", encoding="utf-8") as handle:
                handle.write("edited during the handshake\n")
            return real_authorize(journal, launch, validity)

        with mock.patch.object(command, "_write_authorization", drift_then_authorize):
            outcome = harness.detach()
        self.assertIn(outcome.exit_code, (EXIT_REVALIDATION_DRIFT, EXIT_STARTED), outcome.message)
        finished = harness.wait_outcome()
        self.assertEqual((finished["exit_code"], finished["outcome"]), (4, "revalidation_drift"))
        harness.assert_rolled_back_without_shipping()

    def test_the_supervisor_accepts_only_a_journal_directory(self) -> None:
        for args in ([], ["--supervise"], ["--supervise", "a", "b"], ["--other", "x"], ["--supervise", "relative.journal"]):
            with self.subTest(args=args):
                process = subprocess.run(
                    [sys.executable, "-m", "autoharness.shipment_close.supervisor", *args],
                    env=_env(),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(process.returncode, 2, process.stderr)


class UnconfirmedStartTests(unittest.TestCase):
    def test_a_lost_acknowledgement_after_authorize_is_exit_9_never_a_refusal(self) -> None:
        harness = _DetachHarness(self, hold=True)
        outcome = harness.detach(ack_timeout_seconds=0.0)
        self.assertEqual(outcome.exit_code, EXIT_STARTED, outcome.message)
        self.assertIn("unconfirmed", outcome.message)
        harness.release()
        finished = harness.wait_outcome()
        self.assertEqual(finished["exit_code"], 0)
        self.assertEqual(len(_ship_argvs(harness.argv_log())), 1)


if __name__ == "__main__":
    unittest.main()
