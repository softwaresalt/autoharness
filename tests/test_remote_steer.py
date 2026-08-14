"""Tests for autoharness.remote.steer -- bounded V1 Steer dispatch over the
supervisor state machine (121.002-T).

Covers: only the four approved Steer commands dispatch; invalid, stale,
duplicate, and out-of-state requests fail closed with structured errors;
every accepted command maps to an existing local supervisor transition or
checkpoint operation (no new reasoning loop); Approve/Privileged actions
are unreachable through Steer dispatch.
"""

from __future__ import annotations

import unittest

from autoharness.remote.binding import WorkspaceSessionBinding
from autoharness.remote.contracts import RemoteRequest
from autoharness.remote.errors import (
    DuplicateRequestError,
    IllegalRemoteStateError,
    LocalOnlyCommandError,
    RateLimitExceededError,
    UnknownRemoteCommandError,
)
from autoharness.remote.rate_limit import TokenBucketRateLimiter
from autoharness.remote.steer import SteerDispatcher
from autoharness.supervise.approvals import ConsoleApprovalService
from autoharness.supervise.contracts import CancelRequested, JournalCheckpoint
from autoharness.supervise.session import Phase, SessionStateMachine


class _FakeJournal:
    def __init__(self) -> None:
        self.appended: list[object] = []
        self._next_seq = 0

    def append_event(self, event: object) -> int:
        self.appended.append(event)
        seq = self._next_seq
        self._next_seq += 1
        return seq


def _running_machine() -> SessionStateMachine:
    machine = SessionStateMachine()
    for phase in (
        Phase.LOCKING,
        Phase.BOOTSTRAPPING,
        Phase.PREFLIGHT,
        Phase.RESOLVING,
        Phase.LAUNCHING,
        Phase.RUNNING,
    ):
        machine.transition(phase)
    return machine


def _make_dispatcher(machine: SessionStateMachine | None = None) -> tuple[
    SteerDispatcher, WorkspaceSessionBinding, _FakeJournal
]:
    binding = WorkspaceSessionBinding(
        workspace_root="/workspace/a", session_id="session-a", secret=b"s" * 32
    )
    journal = _FakeJournal()
    dispatcher = SteerDispatcher(
        state_machine=machine or _running_machine(),
        local_channel=ConsoleApprovalService(),
        journal=journal,
        binding=binding,
        rate_limiter=TokenBucketRateLimiter(capacity=50, refill_per_minute=3000),
    )
    return dispatcher, binding, journal


def _request(command: str, request_id: str = "req-1", issued_at: float = 1000.0) -> RemoteRequest:
    return RemoteRequest(
        command=command,
        request_id=request_id,
        workspace_id="/workspace/a",
        session_id="session-a",
        issued_at=issued_at,
    )


class ClosedVocabularyDispatchTests(unittest.TestCase):
    def test_unknown_command_raises(self) -> None:
        dispatcher, binding, _ = _make_dispatcher()
        request = _request("shell_exec")
        with self.assertRaises(UnknownRemoteCommandError):
            dispatcher.dispatch(request, binding.issue_token(), now=1001.0)

    def test_observe_command_is_not_steer_dispatchable(self) -> None:
        dispatcher, binding, _ = _make_dispatcher()
        request = _request("status")
        with self.assertRaises(UnknownRemoteCommandError):
            dispatcher.dispatch(request, binding.issue_token(), now=1001.0)

    def test_local_only_action_is_never_reachable(self) -> None:
        dispatcher, binding, _ = _make_dispatcher()
        request = _request("force_unlock")
        with self.assertRaises(LocalOnlyCommandError):
            dispatcher.dispatch(request, binding.issue_token(), now=1001.0)
        request2 = _request("session_restart", request_id="req-2")
        with self.assertRaises(LocalOnlyCommandError):
            dispatcher.dispatch(request2, binding.issue_token(), now=1001.0)


class PauseResumeTests(unittest.TestCase):
    def test_pause_while_running_succeeds(self) -> None:
        dispatcher, binding, _ = _make_dispatcher()
        response = dispatcher.dispatch(_request("pause"), binding.issue_token(), now=1001.0)
        self.assertTrue(response.ok)

    def test_pause_when_not_running_fails_closed(self) -> None:
        dispatcher, binding, _ = _make_dispatcher(machine=SessionStateMachine())
        with self.assertRaises(IllegalRemoteStateError):
            dispatcher.dispatch(_request("pause"), binding.issue_token(), now=1001.0)

    def test_resume_without_prior_pause_fails_closed(self) -> None:
        dispatcher, binding, _ = _make_dispatcher()
        with self.assertRaises(IllegalRemoteStateError):
            dispatcher.dispatch(_request("resume"), binding.issue_token(), now=1001.0)

    def test_pause_then_resume_round_trips(self) -> None:
        dispatcher, binding, _ = _make_dispatcher()
        dispatcher.dispatch(_request("pause", request_id="p1"), binding.issue_token(), now=1001.0)
        response = dispatcher.dispatch(
            _request("resume", request_id="r1"), binding.issue_token(), now=1002.0
        )
        self.assertTrue(response.ok)

    def test_double_pause_fails_closed(self) -> None:
        dispatcher, binding, _ = _make_dispatcher()
        dispatcher.dispatch(_request("pause", request_id="p1"), binding.issue_token(), now=1001.0)
        with self.assertRaises(IllegalRemoteStateError):
            dispatcher.dispatch(_request("pause", request_id="p2"), binding.issue_token(), now=1002.0)


class CancelTests(unittest.TestCase):
    def test_cancel_while_running_transitions_state_machine(self) -> None:
        dispatcher, binding, journal = _make_dispatcher()
        dispatcher.dispatch(_request("cancel"), binding.issue_token(), now=1001.0)
        self.assertEqual(dispatcher.state_machine.phase, Phase.CANCELLING)
        self.assertTrue(any(isinstance(event, CancelRequested) for event in journal.appended))

    def test_cancel_when_already_terminal_fails_closed(self) -> None:
        machine = _running_machine()
        machine.transition(Phase.DRAINING)
        machine.transition(Phase.EXITED)
        dispatcher, binding, _ = _make_dispatcher(machine=machine)
        with self.assertRaises(IllegalRemoteStateError):
            dispatcher.dispatch(_request("cancel"), binding.issue_token(), now=1001.0)


class RequestCheckpointTests(unittest.TestCase):
    def test_request_checkpoint_appends_journal_checkpoint_event(self) -> None:
        dispatcher, binding, journal = _make_dispatcher()
        response = dispatcher.dispatch(
            _request("request_checkpoint"), binding.issue_token(), now=1001.0
        )
        self.assertTrue(response.ok)
        self.assertTrue(any(isinstance(event, JournalCheckpoint) for event in journal.appended))

    def test_request_checkpoint_on_terminated_session_fails_closed(self) -> None:
        machine = _running_machine()
        machine.transition(Phase.DRAINING)
        machine.transition(Phase.FAILED)
        dispatcher, binding, _ = _make_dispatcher(machine=machine)
        with self.assertRaises(IllegalRemoteStateError):
            dispatcher.dispatch(_request("request_checkpoint"), binding.issue_token(), now=1001.0)


class IdempotencyAndBindingTests(unittest.TestCase):
    def test_duplicate_request_id_is_rejected(self) -> None:
        dispatcher, binding, _ = _make_dispatcher()
        dispatcher.dispatch(_request("cancel", request_id="dup-1"), binding.issue_token(), now=1001.0)
        machine2 = _running_machine()
        # Re-use the SAME dispatcher/request_id against a fresh command to
        # prove idempotency tracking is per-request_id, not per-outcome.
        with self.assertRaises(DuplicateRequestError):
            dispatcher.dispatch(
                _request("request_checkpoint", request_id="dup-1"), binding.issue_token(), now=1002.0
            )

    def test_mismatched_binding_token_is_rejected_before_any_state_change(self) -> None:
        dispatcher, binding, journal = _make_dispatcher()
        with self.assertRaises(Exception):
            dispatcher.dispatch(_request("cancel"), "wrong-token", now=1001.0)
        self.assertEqual(dispatcher.state_machine.phase, Phase.RUNNING)
        self.assertEqual(journal.appended, [])


class RateLimitIntegrationTests(unittest.TestCase):
    def test_rate_limit_exceeded_is_surfaced(self) -> None:
        binding = WorkspaceSessionBinding(
            workspace_root="/workspace/a", session_id="session-a", secret=b"s" * 32
        )
        journal = _FakeJournal()
        dispatcher = SteerDispatcher(
            state_machine=_running_machine(),
            local_channel=ConsoleApprovalService(),
            journal=journal,
            binding=binding,
            rate_limiter=TokenBucketRateLimiter(capacity=1, refill_per_minute=1),
        )
        dispatcher.dispatch(_request("pause", request_id="p1"), binding.issue_token(), now=1001.0)
        with self.assertRaises(RateLimitExceededError):
            dispatcher.dispatch(_request("resume", request_id="r1"), binding.issue_token(), now=1001.0)


if __name__ == "__main__":
    unittest.main()
