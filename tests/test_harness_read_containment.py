"""Unit C, task C2 (187.002-T): harness_read static roots and resolved-path containment.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "C2: Static roots and resolved-path containment".

Proof G cases G14 to G23 and G32 run on each host over a real temporary tree.
On Windows the directory junctions are created with ``mklink /J`` in a
subprocess and never skip; the file and directory symlink cases alone may skip,
with the reason recorded, when the host lacks symlink privilege. On Linux each
junction case (G15, G16, G21b, G23) runs under the same case ID with a
directory-symlink analogue and the same expected code, and the upper-case root
case G21a is a case-sensitivity check (``PATH_NOT_FOUND``). G30 (directory
targets) is verified by C4's module.

Roster (P-004, Marker Convention): every test in this module as of the C2 RED
commit; each reached the RED-phase stub with its own marker
``AHLC_C2_READ_CONTAINMENT:<t>``. ``AutoharnessRootEscapeTests`` and
``test_is_contained_compares_normcase_forms`` were added by the shipment's
local review, after GREEN.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from autoharness import harness_read
from autoharness.harness_read import ReadErrorCode, TrustRoot, open_reader

IS_WINDOWS = sys.platform == "win32"
IN_BYTES = b"PG-IN-01\n"
AH_BYTES = b"PG-AH-01\n"
_ERROR_PRIVILEGE_NOT_HELD = 1314


def make_directory_link(link: Path, target: Path) -> None:
    """Windows: a directory junction via ``mklink /J``. Linux: a directory symlink analogue.

    Kept in sync with the copy in ``test_harness_read_nonregular.py`` (each task's
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


def make_symlink(link: Path, target: Path, *, directory: bool) -> str | None:
    """Create a symlink; return a skip reason only for a Windows host without symlink privilege."""
    try:
        os.symlink(target, link, target_is_directory=directory)
    except OSError as error:
        if IS_WINDOWS and getattr(error, "winerror", None) == _ERROR_PRIVILEGE_NOT_HELD:
            return "host lacks symlink privilege (WinError 1314)"
        raise
    return None


class ContainmentFixture(unittest.TestCase):
    """The Proof G tree: ``ws`` (root W), ``ws/.autoharness`` (root A), ``ws-outside``."""

    tree: Path
    ws: Path
    ws_upper: Path
    sentinel_abs: str
    sentinel_token: bytes
    symlink_skip_reason: str | None

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.mkdtemp(prefix="ahlc-c2-")
        cls.addClassCleanup(shutil.rmtree, cls._tmp, True)
        cls.tree = Path(cls._tmp)
        ws = cls.tree / "ws"
        cls.ws = ws
        (ws / "docs").mkdir(parents=True)
        (ws / ".autoharness").mkdir()
        (ws / "docs" / "in.txt").write_bytes(IN_BYTES)
        (ws / ".autoharness" / "m.yaml").write_bytes(AH_BYTES)
        outside = cls.tree / "ws-outside"
        outside.mkdir()
        cls.sentinel_token = b"AHLC-C2-SENTINEL-" + os.urandom(8).hex().encode()
        (outside / "sentinel.txt").write_bytes(cls.sentinel_token)
        cls.sentinel_abs = os.path.abspath(str(outside / "sentinel.txt"))

        make_directory_link(ws / "j-out", outside)
        make_directory_link(ws / "j-in", ws / "docs")
        make_directory_link(ws / ".autoharness" / "up", ws / "docs")

        reason = None
        for link, target, directory in (
            (ws / "s-f-out", outside / "sentinel.txt", False),
            (ws / "s-d-out", outside, True),
            (ws / "s-f-in", ws / "docs" / "in.txt", False),
            (ws / "dl-in", ws / "docs" / "absent.txt", False),
            (ws / "dl-out", outside / "absent.txt", False),
        ):
            reason = make_symlink(link, target, directory=directory) or reason
            if reason:
                break
        cls.symlink_skip_reason = reason

        cls.ws_upper = cls.tree / "WS"
        # Probe the filesystem rather than the OS: on a case-insensitive volume the
        # differently cased spelling is the same directory (G21a accepts); on a
        # case-sensitive one it names a distinct directory that holds no
        # docs/in.txt but does hold an outward link, so G21a is PATH_NOT_FOUND
        # and G21b still escapes.
        cls.case_insensitive = cls.ws_upper.exists()
        if not cls.case_insensitive:
            cls.ws_upper.mkdir()
            make_directory_link(cls.ws_upper / "j-out", outside)
    def read(self, root: TrustRoot, relative_path: str, *, workspace: Path | None = None):
        reader = open_reader(workspace_root=str(workspace or self.ws))
        result = reader.read_bytes(root, relative_path)
        self.assertNotIn(self.sentinel_abs, result.path)
        self.assertNotIn(self.sentinel_token.decode(), repr(result))
        if result.data is not None:
            self.assertNotIn(self.sentinel_token, result.data)
        self.assertEqual(reader.usage.files_claimed, 1)
        return result

    def assert_ok(self, result, expected: bytes) -> None:
        self.assertIsNone(result.error)
        self.assertEqual(result.data, expected)

    def assert_error(self, result, code: ReadErrorCode) -> None:
        self.assertIs(result.error, code)
        self.assertIsNone(result.data)

    def require_symlinks(self) -> None:
        if self.symlink_skip_reason:
            self.skipTest(self.symlink_skip_reason)


class ContainmentCaseTests(ContainmentFixture):
    W = TrustRoot.WORKSPACE
    A = TrustRoot.AUTOHARNESS

    def test_G14_in_root_accept_exact_bytes(self) -> None:
        self.assert_ok(self.read(self.W, "docs/in.txt"), IN_BYTES)

    def test_G15_directory_junction_out_rejected(self) -> None:
        self.assert_error(self.read(self.W, "j-out/sentinel.txt"), ReadErrorCode.OUTSIDE_TRUST_ROOT)

    def test_G16_in_root_junction_accepted(self) -> None:
        self.assert_ok(self.read(self.W, "j-in/in.txt"), IN_BYTES)

    def test_G17_file_symlink_out_rejected(self) -> None:
        self.require_symlinks()
        self.assert_error(self.read(self.W, "s-f-out"), ReadErrorCode.OUTSIDE_TRUST_ROOT)

    def test_G18_directory_symlink_out_rejected(self) -> None:
        self.require_symlinks()
        self.assert_error(
            self.read(self.W, "s-d-out/sentinel.txt"), ReadErrorCode.OUTSIDE_TRUST_ROOT
        )

    def test_G19_in_root_file_symlink_accepted(self) -> None:
        self.require_symlinks()
        self.assert_ok(self.read(self.W, "s-f-in"), IN_BYTES)

    def test_G20a_dangling_link_inside_is_not_found(self) -> None:
        self.require_symlinks()
        self.assert_error(self.read(self.W, "dl-in"), ReadErrorCode.PATH_NOT_FOUND)

    def test_G20b_dangling_link_outside_is_outside(self) -> None:
        self.require_symlinks()
        self.assert_error(self.read(self.W, "dl-out"), ReadErrorCode.OUTSIDE_TRUST_ROOT)

    def test_G21a_upper_case_root_spelling(self) -> None:
        result = self.read(self.W, "docs/in.txt", workspace=self.ws_upper)
        if self.case_insensitive:
            self.assert_ok(result, IN_BYTES)
        else:
            self.assert_error(result, ReadErrorCode.PATH_NOT_FOUND)

    def test_G21b_upper_case_root_junction_escape(self) -> None:
        self.assert_error(
            self.read(self.W, "j-out/sentinel.txt", workspace=self.ws_upper),
            ReadErrorCode.OUTSIDE_TRUST_ROOT,
        )

    def test_G22a_autoharness_root_accept(self) -> None:
        self.assert_ok(self.read(self.A, "m.yaml"), AH_BYTES)

    def test_G22b_autoharness_file_through_workspace_root(self) -> None:
        self.assert_ok(self.read(self.W, ".autoharness/m.yaml"), AH_BYTES)

    def test_G23_autoharness_junction_into_workspace_rejected(self) -> None:
        self.assert_error(self.read(self.A, "up/in.txt"), ReadErrorCode.OUTSIDE_TRUST_ROOT)

    def test_G32a_missing_file(self) -> None:
        self.assert_error(self.read(self.W, "docs/absent.txt"), ReadErrorCode.PATH_NOT_FOUND)

    def test_G32b_missing_parent(self) -> None:
        self.assert_error(self.read(self.W, "nodir/x.txt"), ReadErrorCode.PATH_NOT_FOUND)

    def test_sentinel_never_in_any_result(self) -> None:
        requests = [
            (self.W, "j-out/sentinel.txt"),
            (self.W, "docs/in.txt"),
            (self.A, "up/in.txt"),
            (self.A, "m.yaml"),
        ]
        if not self.symlink_skip_reason:
            requests += [(self.W, "s-f-out"), (self.W, "s-d-out/sentinel.txt"), (self.W, "dl-out")]
        reader = open_reader(workspace_root=str(self.ws))
        for root, relative_path in requests:
            result = reader.read_bytes(root, relative_path)
            self.assertNotIn(self.sentinel_token.decode(), repr(result))
            self.assertNotIn(self.sentinel_abs, result.path)
            if result.data is not None:
                self.assertNotIn(self.sentinel_token, result.data)
        self.assertEqual(reader.usage.files_claimed, len(requests))


class IsContainedTests(unittest.TestCase):
    """The private ``_is_contained`` patch point: ``commonpath`` over ``normcase``."""

    def test_is_contained_cross_drive_is_false_without_raising(self) -> None:
        # Windows: different drives make commonpath raise ValueError. POSIX: both
        # spellings are relative names with nothing in common.
        self.assertFalse(harness_read._is_contained("C:\\ws", "D:\\x"))

    def test_is_contained_compares_normcase_forms(self) -> None:
        base = os.path.abspath(tempfile.gettempdir())
        root = os.path.join(base, "Ws")
        target = os.path.join(base, "wS", "x")
        case_folds = os.path.normcase("Ws") == os.path.normcase("wS")
        self.assertIs(harness_read._is_contained(root, target), case_folds)

    def test_is_contained_rejects_string_prefix_sibling(self) -> None:
        base = os.path.abspath(tempfile.gettempdir())
        root = os.path.join(base, "ws")
        self.assertFalse(harness_read._is_contained(root, os.path.join(base, "ws-outside", "x")))
        self.assertTrue(harness_read._is_contained(root, os.path.join(root, "docs", "x")))
        self.assertTrue(harness_read._is_contained(root, root))

    def test_is_contained_mixed_absolute_and_relative_is_false(self) -> None:
        root = os.path.abspath(tempfile.gettempdir())
        self.assertFalse(harness_read._is_contained(root, "relative" + os.sep + "x"))


class AutoharnessRootEscapeTests(unittest.TestCase):
    """``.autoharness`` must be the workspace's own directory, never a link elsewhere."""

    def _escape_tree(self, target_name: str) -> tuple[Path, bytes]:
        tree = Path(tempfile.mkdtemp(prefix="ahlc-c2-root-"))
        self.addCleanup(shutil.rmtree, tree, True)
        ws = tree / "ws"
        (ws / "docs").mkdir(parents=True)
        outside = tree / "ws-outside"
        outside.mkdir()
        token = b"AHLC-C2-ROOT-SENTINEL-" + os.urandom(8).hex().encode()
        target = outside if target_name == "outside" else ws / "docs"
        (target / "m.yaml").write_bytes(token)
        make_directory_link(ws / ".autoharness", target)
        return ws, token

    def test_autoharness_root_link_outside_workspace_rejected(self) -> None:
        ws, token = self._escape_tree("outside")
        reader = open_reader(workspace_root=str(ws))
        for root, relative_path in (
            (TrustRoot.AUTOHARNESS, "m.yaml"),
            (TrustRoot.WORKSPACE, ".autoharness/m.yaml"),
        ):
            with self.subTest(root=root):
                result = reader.read_bytes(root, relative_path)
                self.assertIs(result.error, ReadErrorCode.OUTSIDE_TRUST_ROOT)
                self.assertIsNone(result.data)
                self.assertNotIn(token.decode(), repr(result))
        self.assertEqual(reader.usage.files_claimed, 2)
        lexical = reader.read_bytes(TrustRoot.AUTOHARNESS, "../m.yaml")
        self.assertIs(lexical.error, ReadErrorCode.LEXICAL_INVALID)
        self.assertEqual(reader.usage.files_claimed, 2)

    def test_autoharness_root_link_onto_workspace_directory_rejected(self) -> None:
        ws, _token = self._escape_tree("docs")
        reader = open_reader(workspace_root=str(ws))
        result = reader.read_bytes(TrustRoot.AUTOHARNESS, "m.yaml")
        self.assertIs(result.error, ReadErrorCode.OUTSIDE_TRUST_ROOT)
        self.assertIsNone(result.data)


if __name__ == "__main__":
    unittest.main()
