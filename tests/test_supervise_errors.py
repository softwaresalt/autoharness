"""Tests for autoharness.supervise.errors (118.003-T)."""

from __future__ import annotations

import unittest

from autoharness.supervise.errors import (
    EXIT_CODE_BY_KIND,
    ApprovalError,
    AutoharnessError,
    ConfigError,
    ErrorKind,
    LockError,
    ResolutionError,
    RestartError,
)


class ExitCodeContractTests(unittest.TestCase):
    def test_every_error_kind_has_exactly_one_exit_code_entry(self) -> None:
        """The mapping must be total: every ErrorKind member has an entry."""

        for kind in ErrorKind:
            self.assertIn(kind, EXIT_CODE_BY_KIND)

    def test_exit_codes_are_ints(self) -> None:
        for kind, code in EXIT_CODE_BY_KIND.items():
            self.assertIsInstance(code, int, f"{kind} exit code must be an int")

    def test_mapping_has_no_extra_keys_beyond_the_enum(self) -> None:
        self.assertEqual(set(EXIT_CODE_BY_KIND.keys()), set(ErrorKind))


class AutoharnessErrorTests(unittest.TestCase):
    def test_base_error_defaults_to_unknown_kind(self) -> None:
        err = AutoharnessError("boom")

        self.assertEqual(err.kind, ErrorKind.UNKNOWN)
        self.assertEqual(err.exit_code, EXIT_CODE_BY_KIND[ErrorKind.UNKNOWN])

    def test_base_error_accepts_explicit_kind_override(self) -> None:
        err = AutoharnessError("boom", kind=ErrorKind.LOCK)

        self.assertEqual(err.kind, ErrorKind.LOCK)
        self.assertEqual(err.exit_code, EXIT_CODE_BY_KIND[ErrorKind.LOCK])

    def test_subclasses_fix_their_own_kind(self) -> None:
        cases = {
            ConfigError: ErrorKind.CONFIG,
            LockError: ErrorKind.LOCK,
            ResolutionError: ErrorKind.RESOLUTION,
            ApprovalError: ErrorKind.APPROVAL,
            RestartError: ErrorKind.RESTART,
        }
        for cls, expected_kind in cases.items():
            err = cls("message")
            self.assertEqual(err.kind, expected_kind)
            self.assertEqual(err.exit_code, EXIT_CODE_BY_KIND[expected_kind])
            self.assertIsInstance(err, AutoharnessError)

    def test_error_message_preserved(self) -> None:
        err = ConfigError("bad config")
        self.assertEqual(str(err), "bad config")

    def test_all_subclasses_are_raisable_and_catchable_as_base(self) -> None:
        for cls in (ConfigError, LockError, ResolutionError, ApprovalError, RestartError):
            with self.assertRaises(AutoharnessError):
                raise cls("test")


if __name__ == "__main__":
    unittest.main()
