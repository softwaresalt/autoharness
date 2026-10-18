"""Direct unit tests for the quiescence probes' fail-closed branches."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.shipment_close import quiescence


def _scan(tables: dict[str, list[str]], uids: dict[str, int], my_uid: int = 1000, **kwargs):
    kwargs.setdefault("readlink", lambda p: "/dev/null")

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


class ScanProcFdsStartFloorTests(unittest.TestCase):
    """An unreadable same-uid process that predates the journal cannot hold it by inheritance."""

    FLOOR = 1_000_000.0
    HIDDEN = ({"/proc": ["50"], "/proc/50/fd": PermissionError()}, {"/proc/50": 1000})

    def _scan_with(self, started, **kwargs):
        tables, uids = self.HIDDEN
        return _scan(tables, uids, started_before_epoch=self.FLOOR, start_epoch=lambda pid: started, **kwargs)

    def test_an_old_unreadable_process_is_skipped(self) -> None:
        self.assertTrue(self._scan_with(self.FLOOR - 3600).clean)

    def test_a_process_just_inside_the_slack_still_counts(self) -> None:
        slack = quiescence.START_SLACK_SECONDS
        self.assertIsNone(self._scan_with(self.FLOOR - slack + 0.5).clean)
        self.assertTrue(self._scan_with(self.FLOOR - slack - 0.5).clean)

    def test_a_new_unreadable_process_is_unproven(self) -> None:
        self.assertIsNone(self._scan_with(self.FLOOR + 1).clean)
        self.assertIsNone(self._scan_with(self.FLOOR).clean)

    def test_an_unknown_start_time_is_unproven(self) -> None:
        self.assertIsNone(self._scan_with(None).clean)

    def test_without_a_floor_an_old_process_is_still_unproven(self) -> None:
        tables, uids = self.HIDDEN
        verdict = _scan(tables, uids, start_epoch=lambda pid: 1.0)
        self.assertIsNone(verdict.clean)

    def test_a_readable_writer_dominates_an_old_hidden_process(self) -> None:
        tables = {"/proc": ["50", "60"], "/proc/50/fd": PermissionError(), "/proc/60/fd": ["3"]}
        uids = {"/proc/50": 1000, "/proc/60": 1000}
        verdict = _scan(
            tables,
            uids,
            started_before_epoch=self.FLOOR,
            start_epoch=lambda pid: 1.0,
            readlink=lambda p: "/j/stdout.raw",
        )
        self.assertFalse(verdict.clean)


class StartEpochReaderTests(unittest.TestCase):
    def _reader(self, stat_line: str, btime: str | None = "btime 1000\n"):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / "7").mkdir()
        (root / "7" / "stat").write_text(stat_line, encoding="ascii")
        if btime is not None:
            (root / "stat").write_text("cpu 1 2 3\n" + btime, encoding="ascii")
        return quiescence._start_epoch_reader(root)

    @staticmethod
    def _stat(comm: str, starttime: int) -> str:
        rest = ["S"] + ["0"] * 18 + [str(starttime)] + ["0"] * 10  # fields 3..22 then filler
        return f"7 ({comm}) " + " ".join(rest) + "\n"

    def test_the_start_instant_is_btime_plus_ticks(self) -> None:
        if not hasattr(os, "sysconf"):
            self.skipTest("no sysconf on this platform")
        ticks = os.sysconf("SC_CLK_TCK")
        self.assertAlmostEqual(self._reader(self._stat("python", 5 * ticks))("7"), 1005.0)

    def test_a_comm_with_spaces_and_parentheses_is_parsed(self) -> None:
        if not hasattr(os, "sysconf"):
            self.skipTest("no sysconf on this platform")
        ticks = os.sysconf("SC_CLK_TCK")
        self.assertAlmostEqual(self._reader(self._stat("a ) b (c", 2 * ticks))("7"), 1002.0)

    def test_unparsable_or_missing_data_is_none(self) -> None:
        self.assertIsNone(self._reader("garbage without a paren\n")("7"))
        self.assertIsNone(self._reader("7 (x) S 1 2\n")("7"))
        self.assertIsNone(self._reader(self._stat("x", 1), btime=None)("7"))
        self.assertIsNone(self._reader(self._stat("x", 1), btime="btime nope\n")("7"))
        self.assertIsNone(self._reader(self._stat("x", 1))("999"))


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
