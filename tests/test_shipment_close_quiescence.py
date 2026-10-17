"""Direct unit tests for the quiescence probes' fail-closed branches."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from autoharness.shipment_close import quiescence


def _scan(tables: dict[str, list[str]], uids: dict[str, int], my_uid: int = 1000, **kwargs):
    def listdir(path: str) -> list[str]:
        value = tables[path.replace("\\", "/")]
        if isinstance(value, Exception):
            raise value
        return value

    def stat_uid(path: str) -> int:
        value = uids[path.replace("\\", "/")]
        if isinstance(value, Exception):
            raise value
        return value

    with mock.patch.object(quiescence.os.path, "realpath", lambda p: str(p).replace("\\", "/")):
        return quiescence.scan_proc_fds(
            [Path("/j/stdout.raw")],
            proc_root=Path("/proc"),
            self_pid=1,
            listdir=listdir,
            readlink=lambda p: "/dev/null",
            stat_uid=stat_uid,
            my_uid=my_uid,
            **kwargs,
        )


class ScanProcFdsOwnershipTests(unittest.TestCase):
    def test_foreign_uid_permission_denied_is_clean(self) -> None:
        verdict = _scan(
            {"/proc": ["50"], "/proc/50/fd": PermissionError()},
            {"/proc/50": 0},
        )
        self.assertTrue(verdict.clean)

    def test_own_uid_permission_denied_is_unproven(self) -> None:
        verdict = _scan(
            {"/proc": ["50"], "/proc/50/fd": PermissionError()},
            {"/proc/50": 1000},
        )
        self.assertIsNone(verdict.clean)

    def test_unstatable_process_denied_is_unproven(self) -> None:
        verdict = _scan(
            {"/proc": ["50"], "/proc/50/fd": PermissionError()},
            {"/proc/50": OSError("gone")},
        )
        self.assertIsNone(verdict.clean)

    def test_vanished_process_is_skipped(self) -> None:
        verdict = _scan(
            {"/proc": ["50"], "/proc/50/fd": FileNotFoundError()},
            {"/proc/50": 1000},
        )
        self.assertTrue(verdict.clean)

    def test_unlistable_proc_root_is_unproven(self) -> None:
        verdict = _scan({"/proc": OSError("no")}, {})
        self.assertIsNone(verdict.clean)


class _FakeGroup:
    method = "fake_group"

    def __init__(self, snapshots: list[frozenset[int] | None]) -> None:
        self._snapshots = list(snapshots)
        self.killed = 0

    def members(self) -> frozenset[int] | None:
        return self._snapshots.pop(0) if len(self._snapshots) > 1 else self._snapshots[0]

    def kill_members(self) -> int:
        self.killed += 1
        return 1


class SettleGroupTests(unittest.TestCase):
    def _settle(self, group, **kwargs):
        ticks = iter(range(0, 1000))
        return quiescence.settle_group(
            group, grace=3, poll=1, clock=lambda: float(next(ticks)), sleep=lambda seconds: None, **kwargs
        )

    def test_no_group_is_unproven(self) -> None:
        verdict = self._settle(None)
        self.assertFalse(verdict.proven)
        self.assertEqual(verdict.method, "unavailable")

    def test_unenumerable_membership_is_unproven(self) -> None:
        self.assertFalse(self._settle(_FakeGroup([None])).proven)
        self.assertFalse(self._settle(_FakeGroup([frozenset({1}), None])).proven)

    def test_an_empty_group_is_proven_and_a_draining_one_too(self) -> None:
        self.assertTrue(self._settle(_FakeGroup([frozenset()])).proven)
        self.assertTrue(self._settle(_FakeGroup([frozenset({1}), frozenset()])).proven)

    def test_survivors_are_killed_and_the_capture_is_unproven(self) -> None:
        group = _FakeGroup([frozenset({9})])
        verdict = self._settle(group)
        self.assertFalse(verdict.proven)
        self.assertEqual((verdict.survivors_killed, group.killed), (1, 1))


class SettleWritersTests(unittest.TestCase):
    def test_a_persistent_writer_fails_after_the_grace(self) -> None:
        ticks = iter(range(0, 1000))
        calls: list[int] = []

        def probe(paths):
            calls.append(1)
            return quiescence.WriterVerdict(False, "p", "held")

        verdict = quiescence.settle_writers(
            [Path("x")], grace=3, probe=probe, clock=lambda: float(next(ticks)), sleep=lambda seconds: None
        )
        self.assertFalse(verdict.clean)
        self.assertGreater(len(calls), 1)

    def test_an_unproven_probe_is_not_retried(self) -> None:
        calls: list[int] = []

        def probe(paths):
            calls.append(1)
            return quiescence.WriterVerdict(None, "p", "unknown")

        verdict = quiescence.settle_writers([Path("x")], grace=5, probe=probe, sleep=lambda seconds: None)
        self.assertIsNone(verdict.clean)
        self.assertEqual(len(calls), 1)

    def test_a_writer_that_goes_away_is_clean(self) -> None:
        verdicts = iter([quiescence.WriterVerdict(False, "p"), quiescence.WriterVerdict(True, "p")])
        verdict = quiescence.settle_writers(
            [Path("x")], grace=5, probe=lambda paths: next(verdicts), sleep=lambda seconds: None
        )
        self.assertTrue(verdict.clean)


class ProbeWritersTests(unittest.TestCase):
    def test_a_posix_host_without_proc_has_no_primitive(self) -> None:
        with mock.patch.object(quiescence, "_WINDOWS", False), mock.patch.object(quiescence.os.path, "isdir", return_value=False):
            self.assertIsNone(quiescence.probe_writers([Path("x")]).clean)


if __name__ == "__main__":
    unittest.main()
