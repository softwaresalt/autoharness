"""Tests for autoharness.remote.errors -- Plan 2 V1 remote error taxonomy (121.008-T)."""

from __future__ import annotations

import unittest

from autoharness.remote.errors import (
    EXIT_CODE_BY_KIND,
    BindingMismatchError,
    DevtunnelUnavailableError,
    DuplicateRequestError,
    IllegalRemoteStateError,
    LocalOnlyCommandError,
    RateLimitExceededError,
    RemoteError,
    RemoteErrorKind,
    RequestTooLargeError,
    StaleRequestError,
    UnknownRemoteCommandError,
)


class ErrorKindTotalityTests(unittest.TestCase):
    def test_every_kind_has_an_exit_code(self) -> None:
        self.assertEqual(set(RemoteErrorKind), set(EXIT_CODE_BY_KIND.keys()))

    def test_exit_codes_are_positive_integers(self) -> None:
        for kind, code in EXIT_CODE_BY_KIND.items():
            with self.subTest(kind=kind):
                self.assertIsInstance(code, int)
                self.assertGreater(code, 0)


class BaseErrorTests(unittest.TestCase):
    def test_default_kind_is_unknown(self) -> None:
        error = RemoteError("boom")
        self.assertEqual(error.kind, RemoteErrorKind.UNKNOWN)
        self.assertEqual(error.exit_code, EXIT_CODE_BY_KIND[RemoteErrorKind.UNKNOWN])

    def test_kind_can_be_supplied_explicitly(self) -> None:
        error = RemoteError("boom", kind=RemoteErrorKind.PROTOCOL)
        self.assertEqual(error.kind, RemoteErrorKind.PROTOCOL)


class SubclassKindTests(unittest.TestCase):
    CASES = (
        (UnknownRemoteCommandError, RemoteErrorKind.PROTOCOL),
        (LocalOnlyCommandError, RemoteErrorKind.AUTHORITY),
        (RequestTooLargeError, RemoteErrorKind.SIZE_LIMIT),
        (RateLimitExceededError, RemoteErrorKind.RATE_LIMIT),
        (BindingMismatchError, RemoteErrorKind.BINDING),
        (IllegalRemoteStateError, RemoteErrorKind.STATE),
        (DuplicateRequestError, RemoteErrorKind.IDEMPOTENCY),
        (StaleRequestError, RemoteErrorKind.IDEMPOTENCY),
        (DevtunnelUnavailableError, RemoteErrorKind.TRANSPORT),
    )

    def test_each_subclass_carries_its_documented_kind(self) -> None:
        for cls, expected_kind in self.CASES:
            with self.subTest(cls=cls):
                error = cls("message")
                self.assertEqual(error.kind, expected_kind)
                self.assertIsInstance(error, RemoteError)


if __name__ == "__main__":
    unittest.main()