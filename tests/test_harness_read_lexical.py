"""Unit C, task C1 (187.001-T): harness_read contracts and lexical rejection.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "C1: Contracts and lexical rejection".

Every Proof G lexical case (G01 to G13, G24) has its own test, named with its
case ID, and must return ``LEXICAL_INVALID`` with zero resolve calls (a spy on
``os.path.realpath`` only) and no file claim. The fixtures are real temporary
directories; no module function is patched.

Roster (P-004, Marker Convention): every ``test_G..`` method and every
``test_lexical_..`` method; each reached the RED-phase stub with its own marker
``AHLC_C1_READ_LEXICAL:<t>`` at the C1 RED commit. The ``test_structural_..``
methods (API and docstring) reach no stub and are recorded outside the roster.
"""

from __future__ import annotations

import dataclasses
import inspect
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness import harness_read
from autoharness.harness_read import (
    ReadErrorCode,
    ReadLimits,
    ReadResult,
    ReadUsage,
    Reader,
    TrustRoot,
    open_reader,
)

REQUIRED_SENTENCE = (
    "This reader makes no race, TOCTOU or hardlink-alias resistance claim."
)

_FORBIDDEN_PARAMETER_FRAGMENTS = (
    "adapter",
    "opener",
    "callback",
    "hook",
    "resolver",
    "factory",
    "open_fn",
    "filesystem",
)


class _LexicalFixture(unittest.TestCase):
    """Real temporary tree: ``ws`` (root W), ``ws/.autoharness`` (root A), ``ws-outside``."""

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="ahlc-c1-")
        self.addCleanup(shutil.rmtree, self._tmp, True)
        tree = Path(self._tmp)
        self.ws = tree / "ws"
        (self.ws / "docs").mkdir(parents=True)
        (self.ws / ".autoharness").mkdir()
        (self.ws / "docs" / "in.txt").write_bytes(b"PG-IN-01\n")
        (self.ws / ".autoharness" / "m.yaml").write_bytes(b"PG-AH-01\n")
        outside = tree / "ws-outside"
        outside.mkdir()
        self.sentinel = outside / "sentinel.txt"
        self.sentinel.write_bytes(b"AHLC-C1-SENTINEL-" + os.urandom(8).hex().encode())
        self.sentinel_abs = os.path.abspath(str(self.sentinel))

    def _assert_lexical_invalid(self, root: TrustRoot, relative_path: str) -> None:
        reader = open_reader(workspace_root=str(self.ws))
        with mock.patch("os.path.realpath", wraps=os.path.realpath) as resolve_spy:
            result = reader.read_bytes(root, relative_path)
        self.assertIsInstance(result, ReadResult)
        self.assertIs(result.error, ReadErrorCode.LEXICAL_INVALID)
        self.assertIsNone(result.data)
        self.assertEqual(resolve_spy.call_count, 0, "lexical rejection must not resolve")
        self.assertEqual(reader.usage.files_claimed, 0, "lexical rejection must not claim")
        self.assertEqual(reader.usage.bytes_reserved, 0)
        self.assertNotIn(self.sentinel_abs, result.path)
        self.assertNotIn(self.sentinel.read_bytes().decode(), repr(result))


class LexicalCaseTests(_LexicalFixture):
    """Proof G lexical cases G01 to G13 and G24 (22 Windows variants plus slash-style twins)."""

    W = TrustRoot.WORKSPACE
    A = TrustRoot.AUTOHARNESS

    def test_G01_empty(self) -> None:
        self._assert_lexical_invalid(self.W, "")

    def test_G02_nul(self) -> None:
        self._assert_lexical_invalid(self.W, "\x00")

    def test_G03_absolute_host_path(self) -> None:
        self._assert_lexical_invalid(self.W, self.sentinel_abs)

    def test_G04a_rooted_forward_slash(self) -> None:
        self._assert_lexical_invalid(self.W, "/docs/in.txt")

    def test_G04b_rooted_backslash(self) -> None:
        self._assert_lexical_invalid(self.W, "\\docs\\in.txt")

    def test_G05a_parent_backslash(self) -> None:
        self._assert_lexical_invalid(self.W, "..\\ws-outside\\sentinel.txt")

    def test_G05b_parent_forward_slash(self) -> None:
        self._assert_lexical_invalid(self.W, "../ws-outside/sentinel.txt")

    def test_G06a_interior_parent_backslash(self) -> None:
        self._assert_lexical_invalid(self.W, "docs\\..\\..\\ws-outside\\sentinel.txt")

    def test_G06b_interior_parent_forward_slash(self) -> None:
        self._assert_lexical_invalid(self.W, "docs/../../ws-outside/sentinel.txt")

    def test_G07_drive_relative(self) -> None:
        self._assert_lexical_invalid(self.W, "C:ws-outside\\sentinel.txt")

    def test_G08_unc(self) -> None:
        self._assert_lexical_invalid(self.W, "\\\\server\\share\\x")

    def test_G09a_verbatim_prefix_backslash(self) -> None:
        self._assert_lexical_invalid(self.W, "\\\\?\\" + self.sentinel_abs)

    def test_G09b_verbatim_prefix_forward_slash(self) -> None:
        self._assert_lexical_invalid(self.W, "//?/" + self.sentinel_abs.replace("\\", "/"))

    def test_G10a_device_prefix(self) -> None:
        self._assert_lexical_invalid(self.W, "\\\\.\\" + self.sentinel_abs)

    def test_G10b_device_prefix_nul(self) -> None:
        self._assert_lexical_invalid(self.W, "\\\\.\\NUL")

    def test_G11a_alternate_stream(self) -> None:
        self._assert_lexical_invalid(self.W, "docs/in.txt:s")

    def test_G11b_alternate_stream_data(self) -> None:
        self._assert_lexical_invalid(self.W, "docs/in.txt::$DATA")

    def test_G12a_reserved_con(self) -> None:
        self._assert_lexical_invalid(self.W, "CON")

    def test_G12b_reserved_con_lowercase(self) -> None:
        self._assert_lexical_invalid(self.W, "con")

    def test_G12c_reserved_nul_component(self) -> None:
        self._assert_lexical_invalid(self.W, "docs/NUL")

    def test_G12d_reserved_com1(self) -> None:
        self._assert_lexical_invalid(self.W, "COM1")

    def test_G13a_trailing_dot(self) -> None:
        self._assert_lexical_invalid(self.W, "docs/in.txt.")

    def test_G13b_trailing_space(self) -> None:
        self._assert_lexical_invalid(self.W, "docs/in.txt ")

    def test_G24_parent_from_autoharness_root(self) -> None:
        self._assert_lexical_invalid(self.A, "../docs/in.txt")

    # Additional lexical forms named in the C1 rule list (not Proof G rows).

    def test_lexical_control_character(self) -> None:
        self._assert_lexical_invalid(self.W, "docs/in\x1f.txt")

    def test_lexical_reserved_stem_with_extension(self) -> None:
        self._assert_lexical_invalid(self.W, "docs/nul.txt")

    def test_lexical_interior_trailing_dot_component(self) -> None:
        self._assert_lexical_invalid(self.W, "docs./in.txt")


class StructuralApiTests(unittest.TestCase):
    """IM-06 / PE-INTERFACE-01: closed public surface, no adapter parameter (structural)."""

    def test_structural_public_names_are_closed(self) -> None:
        self.assertEqual(
            sorted(harness_read.__all__),
            sorted(
                [
                    "ReadErrorCode",
                    "ReadLimits",
                    "ReadResult",
                    "ReadUsage",
                    "Reader",
                    "TrustRoot",
                    "open_reader",
                ]
            ),
        )
        public = sorted(
            name
            for name, value in vars(harness_read).items()
            if not name.startswith("_")
            and getattr(value, "__module__", None) == harness_read.__name__
        )
        self.assertEqual(public, sorted(harness_read.__all__))

    def test_structural_enumerations_are_closed(self) -> None:
        self.assertEqual([m.name for m in TrustRoot], ["WORKSPACE", "AUTOHARNESS"])
        self.assertEqual(
            [m.name for m in ReadErrorCode],
            [
                "LEXICAL_INVALID",
                "OUTSIDE_TRUST_ROOT",
                "PATH_NOT_FOUND",
                "NOT_REGULAR_FILE",
                "FILE_SIZE_LIMIT",
                "TOTAL_SIZE_LIMIT",
                "FILE_COUNT_LIMIT",
                "IO",
            ],
        )
        for dropped in (
            "RACE",
            "IDENTITY_MISMATCH",
            "REPARSE_POINT",
            "ROOT_OPEN_FAILED",
            "COMPONENT_LIMIT",
            "SESSION_CLOSED",
            "PLATFORM_INVARIANT_UNAVAILABLE",
        ):
            self.assertNotIn(dropped, ReadErrorCode.__members__)

    def test_structural_frozen_value_types(self) -> None:
        limits = ReadLimits()
        self.assertEqual(
            (limits.max_files, limits.max_file_bytes, limits.max_total_bytes),
            (256, 4 * 1024 * 1024, 32 * 1024 * 1024),
        )
        self.assertEqual(
            [f.name for f in dataclasses.fields(ReadLimits)],
            ["max_files", "max_file_bytes", "max_total_bytes"],
        )
        self.assertEqual(
            [f.name for f in dataclasses.fields(ReadUsage)],
            ["files_claimed", "bytes_reserved"],
        )
        self.assertEqual(
            [f.name for f in dataclasses.fields(ReadResult)], ["data", "error", "path"]
        )
        for value in (limits, ReadUsage(), ReadResult(data=b"", error=None, path="x")):
            with self.assertRaises(dataclasses.FrozenInstanceError):
                setattr(value, dataclasses.fields(value)[0].name, None)

    def test_structural_result_requires_exactly_one_outcome(self) -> None:
        ReadResult(data=b"", error=None, path="x")
        ReadResult(data=None, error=ReadErrorCode.IO, path="x")
        for data, error in ((None, None), (b"x", ReadErrorCode.IO)):
            with self.subTest(data=data, error=error), self.assertRaises(ValueError):
                ReadResult(data=data, error=error, path="x")

    def test_structural_limits_reject_invalid_values(self) -> None:
        for kwargs in (
            {"max_files": -1},
            {"max_file_bytes": -1},
            {"max_total_bytes": -1},
            {"max_files": True},
            {"max_file_bytes": 1.5},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises((TypeError, ValueError)):
                ReadLimits(**kwargs)

    def test_structural_no_adapter_parameter_on_any_public_callable(self) -> None:
        signatures = {
            "open_reader": inspect.signature(open_reader),
            "Reader": inspect.signature(Reader),
            "Reader.read_bytes": inspect.signature(Reader.read_bytes),
        }
        self.assertEqual(list(signatures["open_reader"].parameters), ["workspace_root", "limits"])
        for parameter in signatures["open_reader"].parameters.values():
            self.assertIs(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIsNone(signatures["open_reader"].parameters["limits"].default)
        self.assertEqual(list(signatures["Reader"].parameters), ["workspace_root", "limits"])
        self.assertEqual(
            list(signatures["Reader.read_bytes"].parameters), ["self", "root", "relative_path"]
        )
        for type_name in ("ReadLimits", "ReadUsage", "ReadResult"):
            signatures[type_name] = inspect.signature(getattr(harness_read, type_name))
        for name, signature in signatures.items():
            for parameter in signature.parameters:
                for fragment in _FORBIDDEN_PARAMETER_FRAGMENTS:
                    self.assertNotIn(fragment, parameter.lower(), f"{name}({parameter})")
        public_reader_members = sorted(
            name for name in vars(Reader) if not name.startswith("_")
        )
        self.assertEqual(public_reader_members, ["read_bytes", "usage"])

    def test_structural_usage_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ahlc-c1-api-") as tmp:
            reader = open_reader(workspace_root=tmp)
            self.assertEqual(reader.usage, ReadUsage(files_claimed=0, bytes_reserved=0))
            with self.assertRaises(AttributeError):
                reader.usage = ReadUsage()  # type: ignore[misc]


class StructuralDocstringTests(unittest.TestCase):
    """IM-14 floor anchor: the required non-claim sentence on one physical line (structural)."""

    def test_structural_required_sentence_in_module_docstring(self) -> None:
        doc = harness_read.__doc__ or ""
        self.assertTrue(
            any(REQUIRED_SENTENCE in line for line in doc.splitlines()),
            "module docstring must carry the required non-claim sentence on one line",
        )
        source_lines = Path(harness_read.__file__).read_text(encoding="utf-8").splitlines()
        self.assertTrue(any(REQUIRED_SENTENCE in line for line in source_lines))


if __name__ == "__main__":
    unittest.main()
