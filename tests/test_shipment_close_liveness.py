"""Liveness verdict tests (211.004-T, plan unit T3; hardening H3, H6)."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.shipment_close import liveness
from autoharness.shipment_close.liveness import (
    ProbeResult,
    current_host,
    is_process_alive,
    process_start_time,
    provably_dead,
)

_HOST = "host-a"


def _fixed(state: str, start: str | None = None):
    return lambda pid: ProbeResult(state, start=start, detail=state)  # type: ignore[arg-type]


class VerdictRulesTest(unittest.TestCase):
    def verdict(self, *, host=_HOST, pid=100, pid_start="5", prober=None, local=_HOST):
        return provably_dead(host, pid, pid_start, local_host=local, prober=prober)

    def test_absent_pid_is_dead(self) -> None:
        verdict = self.verdict(prober=_fixed("absent"))
        self.assertTrue(verdict.dead)
        self.assertEqual(verdict.basis, "pid_absent")

    def test_start_time_mismatch_is_pid_reuse_and_dead(self) -> None:
        verdict = self.verdict(prober=_fixed("alive", "6"))
        self.assertTrue(verdict.dead)
        self.assertEqual(verdict.basis, "pid_start_mismatch")

    def test_equal_start_time_is_alive(self) -> None:
        verdict = self.verdict(prober=_fixed("alive", "5"))
        self.assertFalse(verdict.dead)
        self.assertEqual(verdict.basis, "alive")

    def test_every_doubt_is_not_dead(self) -> None:
        cases = {
            "unrecorded start": dict(pid_start=None, prober=_fixed("alive", "5"), basis="pid_start_unrecorded"),
            "non-string start": dict(pid_start=5, prober=_fixed("alive", "5"), basis="pid_start_unrecorded"),
            "unreadable start": dict(prober=_fixed("alive", None), basis="start_unreadable"),
            "probe unknown": dict(prober=_fixed("unknown"), basis="unknown"),
            "foreign host": dict(host="host-b", prober=_fixed("absent"), basis="foreign_host"),
            "legacy no host": dict(host=None, prober=_fixed("absent"), basis="legacy_lock"),
            "empty host": dict(host="", prober=_fixed("absent"), basis="legacy_lock"),
            "pid none": dict(pid=None, prober=_fixed("absent"), basis="invalid_pid"),
            "pid zero": dict(pid=0, prober=_fixed("absent"), basis="invalid_pid"),
            "pid negative": dict(pid=-4, prober=_fixed("absent"), basis="invalid_pid"),
            "pid bool": dict(pid=True, prober=_fixed("absent"), basis="invalid_pid"),
            "pid str": dict(pid="12", prober=_fixed("absent"), basis="invalid_pid"),
            "pid too large": dict(pid=2**40, prober=_fixed("absent"), basis="invalid_pid"),
        }
        for name, spec in cases.items():
            with self.subTest(name):
                basis = spec.pop("basis")
                verdict = self.verdict(**spec)
                self.assertFalse(verdict.dead)
                self.assertEqual(verdict.basis, basis)

    def test_probe_is_not_called_for_a_foreign_host(self) -> None:
        prober = mock.Mock(return_value=ProbeResult("absent"))
        self.verdict(host="elsewhere", prober=prober)
        prober.assert_not_called()

    def test_is_process_alive_tristate(self) -> None:
        self.assertTrue(is_process_alive(7, prober=_fixed("alive")))
        self.assertFalse(is_process_alive(7, prober=_fixed("absent")))
        self.assertIsNone(is_process_alive(7, prober=_fixed("unknown")))
        self.assertIsNone(is_process_alive(0, prober=_fixed("alive")))

    def test_process_start_time_only_for_live_processes(self) -> None:
        self.assertEqual(process_start_time(7, prober=_fixed("alive", "9")), "9")
        self.assertIsNone(process_start_time(7, prober=_fixed("absent")))
        self.assertIsNone(process_start_time(-1, prober=_fixed("alive", "9")))


class _FakeKernel32:
    def __init__(self, *, handle=1, error=0, exit_code=259, created=777) -> None:
        self.handle, self.error, self._exit, self._created = handle, error, exit_code, created
        self.closed: list[int] = []

    def open_process(self, pid):
        return (self.handle, 0) if self.handle is not None else (None, self.error)

    def exit_code(self, handle):
        return self._exit

    def creation_time(self, handle):
        return self._created

    def close(self, handle) -> None:
        self.closed.append(handle)


class WindowsProbeBranchesTest(unittest.TestCase):
    def test_branches_via_the_kernel32_seam(self) -> None:
        cases = [
            ("no such pid", _FakeKernel32(handle=None, error=87), "absent", None),
            ("access denied is unknown, never dead", _FakeKernel32(handle=None, error=5), "unknown", None),
            ("other open error", _FakeKernel32(handle=None, error=1234), "unknown", None),
            ("exited", _FakeKernel32(exit_code=0), "absent", None),
            ("exit code query failed", _FakeKernel32(exit_code=None), "unknown", None),
            ("times query failed", _FakeKernel32(created=None), "unknown", None),
            ("running", _FakeKernel32(created=12345), "alive", "12345"),
        ]
        for name, api, state, start in cases:
            with self.subTest(name):
                result = liveness._windows_probe(42, api)
                self.assertEqual((result.state, result.start), (state, start))
                if api.handle is not None:
                    self.assertEqual(api.closed, [api.handle])

    def test_ctypes_load_failure_is_unknown(self) -> None:
        with mock.patch.object(liveness, "_CtypesKernel32", side_effect=OSError("no dll")):
            self.assertEqual(liveness._windows_probe(42).state, "unknown")


@unittest.skipUnless(os.name == "nt", "Windows ctypes back end")
class WindowsRealProcessTest(unittest.TestCase):
    def test_never_calls_os_kill(self) -> None:
        with mock.patch.object(os, "kill", side_effect=AssertionError("os.kill must not be used on nt")):
            self.assertTrue(is_process_alive(os.getpid()))
            self.assertIsNotNone(process_start_time(os.getpid()))
            provably_dead(current_host(), os.getpid(), "1")

    def test_own_process_is_alive_and_stable(self) -> None:
        start = process_start_time(os.getpid())
        self.assertIsNotNone(start)
        self.assertEqual(start, process_start_time(os.getpid()))
        verdict = provably_dead(current_host(), os.getpid(), start)
        self.assertFalse(verdict.dead)

    def test_exited_child_is_dead_and_a_wrong_start_is_pid_reuse(self) -> None:
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            start = process_start_time(child.pid)
            self.assertIsNotNone(start)
            self.assertFalse(provably_dead(current_host(), child.pid, start).dead)
            reused = provably_dead(current_host(), child.pid, str(int(start) + 1))
            self.assertEqual((reused.dead, reused.basis), (True, "pid_start_mismatch"))
        finally:
            child.kill()
            child.wait()
        verdict = provably_dead(current_host(), child.pid, start)
        self.assertTrue(verdict.dead, verdict)

    def test_nonexistent_pid_is_absent(self) -> None:
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child.wait()
        # The Popen handle is closed on GC; probe a pid unlikely to exist right now.
        self.assertIn(liveness._windows_probe(2**31 - 7).state, ("absent", "unknown"))


class PosixProbeTest(unittest.TestCase):
    def _proc(self, root: Path, pid: int, state: str, start: str) -> None:
        directory = root / str(pid)
        directory.mkdir()
        fields = [state, *["0"] * 18, start, "0", "0"]
        (directory / "stat").write_text(f"{pid} (we ird) ) name) {' '.join(fields)}\n", encoding="ascii")

    def test_stat_parsing_survives_parentheses_and_spaces_in_the_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._proc(root, 10, "S", "98765")
            result = liveness._posix_probe(10, kill=lambda pid, sig: None, proc_root=root)
            self.assertEqual((result.state, result.start), ("alive", "98765"))

    def test_zombie_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._proc(root, 11, "Z", "1")
            self.assertEqual(liveness._posix_probe(11, kill=lambda p, s: None, proc_root=root).state, "absent")

    def test_kill_outcomes(self) -> None:
        def raiser(exc):
            def kill(pid, sig):
                raise exc

            return kill

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(liveness._posix_probe(5, kill=raiser(ProcessLookupError()), proc_root=root).state, "absent")
            self.assertEqual(liveness._posix_probe(5, kill=raiser(OSError("x")), proc_root=root).state, "unknown")
            # Permission denied means the process exists; without /proc the start time is unreadable, so not dead.
            denied = liveness._posix_probe(5, kill=raiser(PermissionError()), proc_root=root)
            self.assertEqual((denied.state, denied.start), ("alive", None))

    def test_unparsable_stat_is_alive_without_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "12").mkdir()
            (root / "12" / "stat").write_text("12 (x) S 1 2\n", encoding="ascii")
            result = liveness._posix_probe(12, kill=lambda p, s: None, proc_root=root)
            self.assertEqual((result.state, result.start), ("alive", None))
            self.assertFalse(provably_dead(_HOST, 12, "1", local_host=_HOST, prober=lambda p: result).dead)

    def test_an_out_of_range_pid_is_unknown_never_a_crash(self) -> None:
        def kill(pid, sig):
            raise OverflowError("signed integer is greater than maximum")

        self.assertEqual(liveness._posix_probe(2**40, kill=kill, proc_root=Path("/nonexistent")).state, "unknown")
        self.assertEqual(
            liveness._posix_probe(5, kill=lambda p, s: (_ for _ in ()).throw(ValueError("bad")), proc_root=Path("/x")).state,
            "unknown",
        )

    def test_signal_zero_is_the_only_signal_sent(self) -> None:
        calls = []
        liveness._posix_probe(5, kill=lambda pid, sig: calls.append((pid, sig)), proc_root=Path("/nonexistent"))
        self.assertEqual(calls, [(5, 0)])


class DefaultSelectionTest(unittest.TestCase):
    def test_backend_follows_the_platform(self) -> None:
        with mock.patch.object(liveness.os, "name", "nt"):
            self.assertIs(liveness.default_prober(), liveness._windows_probe)
        with mock.patch.object(liveness.os, "name", "posix"):
            self.assertIs(liveness.default_prober(), liveness._posix_probe)


if __name__ == "__main__":
    unittest.main()
