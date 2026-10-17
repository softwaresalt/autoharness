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


if __name__ == "__main__":
    unittest.main()
