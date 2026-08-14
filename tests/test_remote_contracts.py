"""Tests for autoharness.remote.contracts -- Plan 2 V1 authority + message
contracts (121.008-T).

Covers the closed Observe/Steer command vocabularies, the exhaustive
command->tier catalog, fail-closed rejection of unknown/local-only
commands, and the 16 KiB max request size contract test explicitly called
out by the shipment's harness requirements.
"""

from __future__ import annotations

import unittest

from autoharness.remote.contracts import (
    COMMAND_TIER,
    MAX_REQUEST_BYTES,
    RATE_LIMIT_BURST,
    RATE_LIMIT_PER_MINUTE,
    REMOTE_EXPOSED_TIERS,
    AuthorityTier,
    LocalOnlyCommand,
    ObserveCommand,
    RemoteRequest,
    RemoteResponse,
    SteerCommand,
    ensure_remotely_dispatchable,
    resolve_command_tier,
    validate_request_size,
)
from autoharness.remote.errors import (
    LocalOnlyCommandError,
    RequestTooLargeError,
    UnknownRemoteCommandError,
)


class ClosedVocabularyTests(unittest.TestCase):
    def test_observe_vocabulary_is_exact(self) -> None:
        expected = {"status", "phase", "progress", "output_tail", "journal_tail"}
        self.assertEqual({c.value for c in ObserveCommand}, expected)

    def test_steer_vocabulary_is_exact(self) -> None:
        expected = {"pause", "resume", "cancel", "request_checkpoint"}
        self.assertEqual({c.value for c in SteerCommand}, expected)

    def test_local_only_vocabulary_matches_gated_action_catalog(self) -> None:
        from autoharness.supervise.contracts import GATED_ACTION_CATALOG

        self.assertEqual(
            {c.value for c in LocalOnlyCommand}, set(GATED_ACTION_CATALOG.keys())
        )


class AuthorityTierTests(unittest.TestCase):
    def test_exactly_four_tiers_exist(self) -> None:
        self.assertEqual(
            {t.name for t in AuthorityTier},
            {"OBSERVE", "STEER", "APPROVE", "PRIVILEGED"},
        )

    def test_only_observe_and_steer_are_remotely_exposed(self) -> None:
        self.assertEqual(
            REMOTE_EXPOSED_TIERS, frozenset({AuthorityTier.OBSERVE, AuthorityTier.STEER})
        )


class CommandTierCatalogTests(unittest.TestCase):
    def test_catalog_is_exhaustive_and_closed(self) -> None:
        expected_keys = (
            {c.value for c in ObserveCommand}
            | {c.value for c in SteerCommand}
            | {c.value for c in LocalOnlyCommand}
        )
        self.assertEqual(set(COMMAND_TIER.keys()), expected_keys)

    def test_observe_commands_resolve_to_observe_tier(self) -> None:
        for command in ObserveCommand:
            with self.subTest(command=command):
                self.assertEqual(resolve_command_tier(command.value), AuthorityTier.OBSERVE)

    def test_steer_commands_resolve_to_steer_tier(self) -> None:
        for command in SteerCommand:
            with self.subTest(command=command):
                self.assertEqual(resolve_command_tier(command.value), AuthorityTier.STEER)

    def test_local_only_commands_resolve_to_privileged_tier(self) -> None:
        for command in LocalOnlyCommand:
            with self.subTest(command=command):
                self.assertEqual(resolve_command_tier(command.value), AuthorityTier.PRIVILEGED)

    def test_unknown_command_raises(self) -> None:
        with self.assertRaises(UnknownRemoteCommandError):
            resolve_command_tier("arbitrary_shell_command")

    def test_catalog_is_immutable_mapping(self) -> None:
        with self.assertRaises(TypeError):
            COMMAND_TIER["status"] = AuthorityTier.PRIVILEGED  # type: ignore[index]


class EnsureRemotelyDispatchableTests(unittest.TestCase):
    def test_observe_and_steer_commands_pass(self) -> None:
        for command in list(ObserveCommand) + list(SteerCommand):
            with self.subTest(command=command):
                tier = ensure_remotely_dispatchable(command.value)
                self.assertIn(tier, REMOTE_EXPOSED_TIERS)

    def test_local_only_commands_are_rejected(self) -> None:
        for command in LocalOnlyCommand:
            with self.subTest(command=command):
                with self.assertRaises(LocalOnlyCommandError):
                    ensure_remotely_dispatchable(command.value)

    def test_unknown_command_raises_unknown_not_local_only(self) -> None:
        with self.assertRaises(UnknownRemoteCommandError):
            ensure_remotely_dispatchable("rm -rf /")

    def test_no_raw_shell_or_arbitrary_command_is_ever_dispatchable(self) -> None:
        """Fuzz a handful of raw-shell-shaped strings against the closed
        catalog -- none may resolve to a remotely-dispatchable tier."""

        raw_candidates = (
            "sh",
            "bash -c 'echo hi'",
            "; rm -rf /",
            "__import__('os').system('id')",
            "",
        )
        for candidate in raw_candidates:
            with self.subTest(candidate=candidate):
                with self.assertRaises(UnknownRemoteCommandError):
                    ensure_remotely_dispatchable(candidate)


class RequestSizeLimitTests(unittest.TestCase):
    """Contract test explicitly required by the shipment harness: 16 KiB max
    request size (security requirement)."""

    def test_max_request_bytes_is_16_kib(self) -> None:
        self.assertEqual(MAX_REQUEST_BYTES, 16 * 1024)

    def test_request_at_exact_limit_is_accepted(self) -> None:
        validate_request_size(b"a" * MAX_REQUEST_BYTES)  # must not raise

    def test_request_one_byte_over_limit_is_rejected(self) -> None:
        with self.assertRaises(RequestTooLargeError):
            validate_request_size(b"a" * (MAX_REQUEST_BYTES + 1))

    def test_empty_request_is_accepted(self) -> None:
        validate_request_size(b"")  # must not raise

    def test_non_bytes_input_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            validate_request_size("not-bytes")  # type: ignore[arg-type]


class RateLimitConstantsTests(unittest.TestCase):
    """Contract test explicitly required by the shipment harness: 30
    req/min, burst 5 rate limit (security requirement)."""

    def test_rate_limit_constants_match_the_security_requirement(self) -> None:
        self.assertEqual(RATE_LIMIT_PER_MINUTE, 30)
        self.assertEqual(RATE_LIMIT_BURST, 5)


class RemoteRequestResponseShapeTests(unittest.TestCase):
    def test_remote_request_is_constructible_and_frozen(self) -> None:
        request = RemoteRequest(
            command="status",
            request_id="req-1",
            workspace_id="/workspace",
            session_id="sess-1",
            issued_at=1234.5,
        )
        self.assertEqual(request.command, "status")
        self.assertEqual(request.role, "remote_operator")
        with self.assertRaises(Exception):
            request.command = "cancel"  # type: ignore[misc]

    def test_remote_response_default_payload_is_empty_mapping(self) -> None:
        response = RemoteResponse(request_id="req-1", command="status", ok=True)
        self.assertEqual(dict(response.payload), {})

    def test_remote_request_role_is_never_a_workstation_identity(self) -> None:
        """Audit privacy requirement: the request's identity field is a
        ROLE, not a machine/workstation identifier (hostname/IP)."""

        import socket as socket_module

        request = RemoteRequest(
            command="status",
            request_id="req-1",
            workspace_id="/workspace",
            session_id="sess-1",
            issued_at=1234.5,
        )
        self.assertNotEqual(request.role, socket_module.gethostname())
        self.assertNotIn(".", request.role)  # not an IP-shaped value either


if __name__ == "__main__":
    unittest.main()
