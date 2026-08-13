"""Tests for autoharness.supervise.approvals -- console approval channel (120.005-T).

Covers both mandatory FallbackPolicy variants resolved non-interactively
(UseSafeDefault -> its declared reference/value; Refuse -> "REFUSED"),
interactive approve/deny via an injected input function, the unknown/
unregistered-identifier fail-closed contract, minimal structured local
command routing, and the mandatory no-open-socket assertion (reusing
events.py's H7 no-listen guard).
"""

from __future__ import annotations

import unittest

from autoharness.supervise.contracts import ApprovalResolved, UnknownGatedActionError
from autoharness.supervise.events import install_no_listen_guard
from autoharness.supervise.approvals import ConsoleApprovalService


class NonInteractiveFallbackTests(unittest.TestCase):
    def test_use_safe_default_action_resolves_to_declared_reference(self) -> None:
        service = ConsoleApprovalService()
        resolved = service.request_approval("session_restart", interactive=False)
        self.assertIsInstance(resolved, ApprovalResolved)
        self.assertEqual(resolved.kind, "session_restart")
        self.assertEqual(
            resolved.resolution, "decline restart (the restart budget defaults to 0)"
        )

    def test_refuse_action_resolves_to_refused(self) -> None:
        service = ConsoleApprovalService()
        resolved = service.request_approval("force_unlock", interactive=False)
        self.assertEqual(resolved.kind, "force_unlock")
        self.assertEqual(resolved.resolution, "REFUSED")

    def test_never_silently_auto_approves(self) -> None:
        service = ConsoleApprovalService()
        resolved = service.request_approval("force_unlock", interactive=False)
        self.assertNotIn(resolved.resolution, ("force_unlock", "approved", "accepted"))


class InteractiveApprovalTests(unittest.TestCase):
    def test_interactive_approve_via_injected_input(self) -> None:
        service = ConsoleApprovalService()
        outputs: list[str] = []
        resolved = service.request_approval(
            "session_restart",
            interactive=True,
            input_fn=lambda prompt="": "restart",
            output_fn=outputs.append,
        )
        self.assertEqual(resolved.resolution, "restart")
        self.assertTrue(len(outputs) > 0)

    def test_interactive_deny_via_injected_input(self) -> None:
        service = ConsoleApprovalService()
        resolved = service.request_approval(
            "session_restart",
            interactive=True,
            input_fn=lambda prompt="": "decline",
            output_fn=lambda *_a, **_k: None,
        )
        self.assertEqual(resolved.resolution, "decline")

    def test_interactive_force_unlock_approve(self) -> None:
        service = ConsoleApprovalService()
        resolved = service.request_approval(
            "force_unlock",
            interactive=True,
            input_fn=lambda prompt="": "force_unlock",
            output_fn=lambda *_a, **_k: None,
        )
        self.assertEqual(resolved.resolution, "force_unlock")

    def test_interactive_unrecognized_input_falls_back_to_safe_default(self) -> None:
        service = ConsoleApprovalService()
        resolved = service.request_approval(
            "session_restart",
            interactive=True,
            input_fn=lambda prompt="": "not-a-real-option",
            output_fn=lambda *_a, **_k: None,
        )
        # Unrecognized input fails closed to the catalog's fallback policy.
        self.assertEqual(
            resolved.resolution, "decline restart (the restart budget defaults to 0)"
        )


class UnknownIdentifierTests(unittest.TestCase):
    def test_unknown_identifier_raises_and_propagates(self) -> None:
        service = ConsoleApprovalService()
        with self.assertRaises(UnknownGatedActionError):
            service.request_approval("not-a-real-gated-action", interactive=False)

    def test_unknown_identifier_does_not_proceed_to_any_side_effect(self) -> None:
        service = ConsoleApprovalService()
        side_effects: list[str] = []
        try:
            service.request_approval("totally-unregistered", interactive=False)
            side_effects.append("reached-past-lookup")
        except UnknownGatedActionError:
            pass
        self.assertEqual(side_effects, [])


class StructuredLocalCommandTests(unittest.TestCase):
    def test_status_pause_resume_cancel_routed_over_same_channel(self) -> None:
        service = ConsoleApprovalService()
        for command in ("status", "pause", "resume", "cancel"):
            with self.subTest(command=command):
                response = service.handle_command(command)
                self.assertIsInstance(response, str)
                self.assertGreater(len(response), 0)

    def test_unknown_command_does_not_raise(self) -> None:
        service = ConsoleApprovalService()
        response = service.handle_command("not-a-real-command")
        self.assertIsInstance(response, str)


class NoOpenSocketTests(unittest.TestCase):
    def test_module_never_opens_a_listening_socket(self) -> None:
        service = ConsoleApprovalService()
        with install_no_listen_guard():
            service.request_approval("session_restart", interactive=False)
            service.request_approval("force_unlock", interactive=False)
            service.handle_command("status")


class InjectableConstructionTests(unittest.TestCase):
    def test_constructible_with_no_module_level_singleton(self) -> None:
        service_a = ConsoleApprovalService()
        service_b = ConsoleApprovalService()
        self.assertIsNot(service_a, service_b)


if __name__ == "__main__":
    unittest.main()
