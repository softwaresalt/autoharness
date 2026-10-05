"""Unit C, task C4 (187.004-T): harness_read non-regular targets.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "C4: Non-regular targets".

After containment the resolved path must be a regular file; anything else is
``NOT_REGULAR_FILE`` before any open (ordinary input rejection, FI-10). G30
runs on each host (Windows: a ``mklink /J`` junction; Linux: a directory
symlink analogue). The G31 class is Linux-only (``NOT_APPLICABLE_ON_WINDOWS``):
G31a is the Proof G FIFO row, and G31b and G31c are the C4 device-node checks
(``/dev`` as the workspace root, and an in-root link to ``/dev/null``, where
containment precedes the regular-file check).

Roster (P-004, Marker Convention): G30a, G30b, G31a and G31b, each of which
reached the RED-phase stub with its own marker ``AHLC_C4_READ_NONREGULAR:<t>``
at the C4 RED commit (G31a and G31b on Linux). G31c, G32a and G32b are
characterization tests (outside the roster): they pin behavior C2 already
provides and may pass before C4. G31b and G31c are the C4 device-node checks,
filed under the Linux-only G31 class; they are not Proof G rows.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from autoharness.harness_read import ReadErrorCode, TrustRoot, open_reader

IS_WINDOWS = sys.platform == "win32"
W = TrustRoot.WORKSPACE
LINUX_ONLY = "NOT_APPLICABLE_ON_WINDOWS: Linux special files (G31 class)"


def make_directory_link(link: Path, target: Path) -> None:
    """Windows: a directory junction via ``mklink /J``. Linux: a directory symlink analogue.

    Kept in sync with the copy in ``test_harness_read_containment.py`` (each task's
    file budget names its own test module).
    """
    if IS_WINDOWS:
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            encoding="oem",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"mklink /J failed: {completed.stdout} {completed.stderr}")
    else:
        os.symlink(target, link, target_is_directory=True)


class NonRegularFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="ahlc-c4-")
        self.addCleanup(shutil.rmtree, self._tmp, True)
        self.ws = Path(self._tmp) / "ws"
        (self.ws / "docs").mkdir(parents=True)
        (self.ws / "docs" / "in.txt").write_bytes(b"PG-IN-01\n")
        make_directory_link(self.ws / "j-in", self.ws / "docs")

    def read(self, relative_path: str, *, workspace: str | None = None):
        return open_reader(workspace_root=workspace or str(self.ws)).read_bytes(W, relative_path)

    def assert_error(self, result, code: ReadErrorCode) -> None:
        self.assertIs(result.error, code)
        self.assertIsNone(result.data)


class NonRegularCaseTests(NonRegularFixture):
    def test_G30a_directory_is_not_regular(self) -> None:
        self.assert_error(self.read("docs"), ReadErrorCode.NOT_REGULAR_FILE)

    def test_G30b_junction_to_directory_is_not_regular(self) -> None:
        self.assert_error(self.read("j-in"), ReadErrorCode.NOT_REGULAR_FILE)

    @unittest.skipIf(IS_WINDOWS, LINUX_ONLY)
    def test_G31a_fifo_is_not_regular_within_bounded_time(self) -> None:
        os.mkfifo(self.ws / "fifo")

        def expire(signum: int, frame: object) -> None:
            raise AssertionError("reading a FIFO did not return within 10 seconds")

        previous = signal.signal(signal.SIGALRM, expire)
        self.addCleanup(signal.signal, signal.SIGALRM, previous)
        self.addCleanup(signal.setitimer, signal.ITIMER_REAL, 0)
        signal.setitimer(signal.ITIMER_REAL, 10)
        result = self.read("fifo")
        signal.setitimer(signal.ITIMER_REAL, 0)
        self.assert_error(result, ReadErrorCode.NOT_REGULAR_FILE)

    @unittest.skipIf(IS_WINDOWS, LINUX_ONLY)
    def test_G31b_device_node_under_dev_root_is_not_regular(self) -> None:
        self.assert_error(self.read("null", workspace="/dev"), ReadErrorCode.NOT_REGULAR_FILE)

    @unittest.skipIf(IS_WINDOWS, LINUX_ONLY)
    def test_G31c_char_in_root_link_to_device_is_outside(self) -> None:
        os.symlink("/dev/null", self.ws / "devnull")
        self.assert_error(self.read("devnull"), ReadErrorCode.OUTSIDE_TRUST_ROOT)

    def test_G32a_char_missing_file(self) -> None:
        self.assert_error(self.read("docs/absent.txt"), ReadErrorCode.PATH_NOT_FOUND)

    def test_G32b_char_missing_parent(self) -> None:
        self.assert_error(self.read("nodir/x.txt"), ReadErrorCode.PATH_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
