"""Tests for autoharness.remote.observe -- the redacted V1 Observe surface
over Plan 1's event bus and journal seams (121.006-T).

Covers: status/phase/progress/output_tail/journal_tail responses, bounded
backpressure (drop-oldest + truncated flag) on the output tail, that
already-redacted content is all a remote Observe caller ever sees (no
second redaction pass, no raw pass-through), and binding/rate-limit
enforcement shared with Steer.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.remote.binding import WorkspaceSessionBinding
from autoharness.remote.contracts import RemoteRequest
from autoharness.remote.errors import RateLimitExceededError, UnknownRemoteCommandError
from autoharness.remote.observe import BoundedOutputTail, ObserveService
from autoharness.remote.rate_limit import TokenBucketRateLimiter
from autoharness.supervise.contracts import ChildOutput
from autoharness.supervise.events import EventBus
from autoharness.supervise.journal import SessionJournal
from autoharness.supervise.redact import PLACEHOLDER, Redactor
from autoharness.supervise.session import Phase, SessionStateMachine


def _request(command: str, request_id: str = "req-1", *, workspace_id: str = "/workspace/a") -> RemoteRequest:
    return RemoteRequest(
        command=command,
        request_id=request_id,
        workspace_id=workspace_id,
        session_id="session-a",
        issued_at=1000.0,
    )


class BoundedOutputTailTests(unittest.TestCase):
    def test_records_lines_up_to_capacity(self) -> None:
        tail = BoundedOutputTail(capacity=3)
        for i in range(3):
            tail.record(ChildOutput(stream="stdout", line=f"line-{i}"))
        result = tail.tail()
        self.assertEqual(result["lines"], ["line-0", "line-1", "line-2"])
        self.assertFalse(result["truncated"])
        self.assertEqual(result["dropped_count"], 0)

    def test_drops_oldest_and_signals_truncation_when_over_capacity(self) -> None:
        tail = BoundedOutputTail(capacity=2)
        for i in range(5):
            tail.record(ChildOutput(stream="stdout", line=f"line-{i}"))
        result = tail.tail()
        self.assertEqual(result["lines"], ["line-3", "line-4"])
        self.assertTrue(result["truncated"])
        self.assertGreater(result["dropped_count"], 0)

    def test_never_blocks_or_raises_on_overflow(self) -> None:
        tail = BoundedOutputTail(capacity=1)
        for i in range(100):
            tail.record(ChildOutput(stream="stdout", line=f"line-{i}"))  # must not raise
        self.assertEqual(len(tail.tail()["lines"]), 1)


def _make_service(workspace: str, journal: SessionJournal) -> tuple[ObserveService, WorkspaceSessionBinding]:
    binding = WorkspaceSessionBinding(
        workspace_root=workspace, session_id=journal.session_id, secret=b"s" * 32
    )
    machine = SessionStateMachine()
    for phase in (Phase.LOCKING, Phase.BOOTSTRAPPING, Phase.PREFLIGHT, Phase.RESOLVING, Phase.LAUNCHING, Phase.RUNNING):
        machine.transition(phase)
    service = ObserveService(
        state_machine=machine,
        journal=journal,
        output_tail=BoundedOutputTail(capacity=50),
        binding=binding,
        rate_limiter=TokenBucketRateLimiter(capacity=50, refill_per_minute=3000),
    )
    return service, binding


class ObserveCommandTests(unittest.TestCase):
    def test_status_and_phase_report_current_phase(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="session-a")
            service, binding = _make_service(workspace, journal)
            token = binding.issue_token()

            status = service.handle(
                _request("status", workspace_id=workspace), token, now=1001.0
            )
            phase = service.handle(
                _request("phase", request_id="req-2", workspace_id=workspace), token, now=1001.0
            )

            self.assertEqual(status.payload["phase"], "running")
            self.assertEqual(phase.payload["phase"], "running")

    def test_progress_reports_a_journal_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="session-a")
            journal.append_child_output_unavailable(reason="test")
            service, binding = _make_service(workspace, journal)
            token = binding.issue_token()

            response = service.handle(
                _request("progress", workspace_id=workspace), token, now=1001.0
            )
            self.assertIn("journal_cursor", response.payload)
            self.assertGreaterEqual(response.payload["journal_cursor"], 0)

    def test_output_tail_reflects_attached_event_bus(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="session-a")
            service, binding = _make_service(workspace, journal)
            token = binding.issue_token()

            bus = EventBus()
            service.attach(bus)
            bus.emit(ChildOutput(stream="stdout", line="hello from child"))

            response = service.handle(
                _request("output_tail", workspace_id=workspace), token, now=1001.0
            )
            self.assertIn("hello from child", response.payload["lines"])

    def test_output_tail_never_leaks_a_registered_secret(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="session-a")
            service, binding = _make_service(workspace, journal)
            token = binding.issue_token()

            redactor = Redactor()
            redactor.register_secret("super-secret-value-1234567890")
            bus = EventBus(redactor=redactor)
            service.attach(bus)
            bus.emit(ChildOutput(stream="stdout", line="token=super-secret-value-1234567890 ok"))

            response = service.handle(
                _request("output_tail", workspace_id=workspace), token, now=1001.0
            )
            joined = " ".join(response.payload["lines"])
            self.assertNotIn("super-secret-value-1234567890", joined)
            self.assertIn(PLACEHOLDER, joined)

    def test_journal_tail_reports_a_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="session-a")
            service, binding = _make_service(workspace, journal)
            token = binding.issue_token()

            response = service.handle(
                _request("journal_tail", workspace_id=workspace), token, now=1001.0
            )
            self.assertIn("cursor", response.payload)


class ObserveGuardrailTests(unittest.TestCase):
    def test_steer_command_is_not_observe_dispatchable(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="session-a")
            service, binding = _make_service(workspace, journal)
            with self.assertRaises(UnknownRemoteCommandError):
                service.handle(
                    _request("cancel", workspace_id=workspace), binding.issue_token(), now=1001.0
                )

    def test_rate_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="session-a")
            binding = WorkspaceSessionBinding(
                workspace_root=workspace, session_id="session-a", secret=b"s" * 32
            )
            service = ObserveService(
                state_machine=SessionStateMachine(),
                journal=journal,
                output_tail=BoundedOutputTail(capacity=10),
                binding=binding,
                rate_limiter=TokenBucketRateLimiter(capacity=1, refill_per_minute=1),
            )
            token = binding.issue_token()
            service.handle(_request("status", workspace_id=workspace), token, now=1001.0)
            with self.assertRaises(RateLimitExceededError):
                service.handle(
                    _request("status", request_id="req-2", workspace_id=workspace),
                    token,
                    now=1001.0,
                )


if __name__ == "__main__":
    unittest.main()
