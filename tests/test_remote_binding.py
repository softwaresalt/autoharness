"""Tests for autoharness.remote.binding -- cryptographic workspace/session
binding for Plan 2 V1 remote requests (121.004-T).

Covers: correct binding round-trips, and fail-closed rejection of every
mismatched/missing/expired/ambiguous binding shape. Threat-modeled per the
task's own implementation notes: workspace confusion and cross-session
command delivery.
"""

from __future__ import annotations

import unittest

from autoharness.remote.binding import (
    WorkspaceSessionBinding,
    generate_binding_secret,
)
from autoharness.remote.contracts import RemoteRequest
from autoharness.remote.errors import BindingMismatchError


def _make_request(**overrides: object) -> RemoteRequest:
    fields = {
        "command": "status",
        "request_id": "req-1",
        "workspace_id": "/workspace/a",
        "session_id": "session-a",
        "issued_at": 1000.0,
    }
    fields.update(overrides)
    return RemoteRequest(**fields)  # type: ignore[arg-type]


class BindingSecretTests(unittest.TestCase):
    def test_generated_secrets_are_32_bytes_and_unique(self) -> None:
        first = generate_binding_secret()
        second = generate_binding_secret()
        self.assertEqual(len(first), 32)
        self.assertEqual(len(second), 32)
        self.assertNotEqual(first, second)


class HappyPathTests(unittest.TestCase):
    def test_matching_binding_and_fresh_request_verifies(self) -> None:
        binding = WorkspaceSessionBinding(
            workspace_root="/workspace/a", session_id="session-a", secret=b"s" * 32
        )
        token = binding.issue_token()
        request = _make_request(issued_at=1000.0)
        binding.verify(request, token, now=1001.0)  # must not raise

    def test_token_is_deterministic_for_same_inputs(self) -> None:
        binding = WorkspaceSessionBinding(
            workspace_root="/workspace/a", session_id="session-a", secret=b"s" * 32
        )
        self.assertEqual(binding.issue_token(), binding.issue_token())

    def test_different_secret_yields_different_token(self) -> None:
        binding_a = WorkspaceSessionBinding(
            workspace_root="/workspace/a", session_id="session-a", secret=b"a" * 32
        )
        binding_b = WorkspaceSessionBinding(
            workspace_root="/workspace/a", session_id="session-a", secret=b"b" * 32
        )
        self.assertNotEqual(binding_a.issue_token(), binding_b.issue_token())


class FailClosedMismatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.binding = WorkspaceSessionBinding(
            workspace_root="/workspace/a", session_id="session-a", secret=b"s" * 32
        )
        self.token = self.binding.issue_token()

    def test_wrong_workspace_id_rejected(self) -> None:
        request = _make_request(workspace_id="/workspace/OTHER")
        with self.assertRaises(BindingMismatchError):
            self.binding.verify(request, self.token, now=1001.0)

    def test_wrong_session_id_rejected(self) -> None:
        request = _make_request(session_id="OTHER-SESSION")
        with self.assertRaises(BindingMismatchError):
            self.binding.verify(request, self.token, now=1001.0)

    def test_empty_workspace_id_rejected(self) -> None:
        request = _make_request(workspace_id="")
        with self.assertRaises(BindingMismatchError):
            self.binding.verify(request, self.token, now=1001.0)

    def test_wrong_token_rejected(self) -> None:
        request = _make_request()
        with self.assertRaises(BindingMismatchError):
            self.binding.verify(request, "not-the-real-token", now=1001.0)

    def test_missing_token_rejected(self) -> None:
        request = _make_request()
        with self.assertRaises(BindingMismatchError):
            self.binding.verify(request, "", now=1001.0)

    def test_cross_workspace_token_replay_is_rejected(self) -> None:
        """A token issued for workspace B must never validate a request
        bound to workspace A, even if the request otherwise looks fresh."""

        other_binding = WorkspaceSessionBinding(
            workspace_root="/workspace/b", session_id="session-b", secret=b"s" * 32
        )
        other_token = other_binding.issue_token()
        request = _make_request()  # bound to workspace/a, session-a
        with self.assertRaises(BindingMismatchError):
            self.binding.verify(request, other_token, now=1001.0)

    def test_expired_binding_rejected(self) -> None:
        request = _make_request(issued_at=1000.0)
        with self.assertRaises(BindingMismatchError):
            self.binding.verify(request, self.token, now=1000.0 + 3600.0, max_age_seconds=300.0)

    def test_future_dated_request_rejected(self) -> None:
        """An ``issued_at`` timestamp after ``now`` is ambiguous/invalid and
        must fail closed rather than being treated as extra-fresh."""

        request = _make_request(issued_at=5000.0)
        with self.assertRaises(BindingMismatchError):
            self.binding.verify(request, self.token, now=1001.0)


if __name__ == "__main__":
    unittest.main()
