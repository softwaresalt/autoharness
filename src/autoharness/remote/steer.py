"""Plan 2 V1 Steer dispatch (121.002-T).

:class:`SteerDispatcher` is the ONLY place a Plan 2 remote request may
touch local supervisor state. Every accepted command maps to an EXISTING
Plan 1 seam -- there is no new reasoning loop and no new supervisor
behavior invented here:

* ``pause``/``resume`` route through the existing
  ``ConsoleApprovalService.handle_command()`` structured-command channel.
  Pause/resume are NOT modeled as OS signals (SIGSTOP/SIGCONT is
  non-portable -- Windows has no equivalent -- and a SIGTERM fallback would
  kill rather than pause); an auxiliary ``_paused`` flag tracks pause
  state at the dispatcher level. Plan 1's ``Phase`` enum and
  ``LEGAL_TRANSITIONS`` table are NOT modified for this.
* ``cancel`` transitions the injected :class:`SessionStateMachine` to
  ``Phase.CANCELLING`` (legal only from the pre-terminal phases per Plan
  1's own table) and journals a ``CancelRequested`` event, in addition to
  notifying the local channel.
* ``request_checkpoint`` appends a ``JournalCheckpoint`` event -- a
  previously-unused Plan 1 event type reserved for exactly this kind of
  caller-constructed durable-write marker.

Every dispatch passes through, in order: closed-vocabulary resolution
(:func:`~autoharness.remote.contracts.ensure_remotely_dispatchable`),
binding verification, idempotency (duplicate ``request_id`` rejection),
rate limiting, then state-legality checks specific to the command. A
rejection at any earlier stage means NO state change and NO journal write
has occurred -- this is asserted directly in the test suite.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from autoharness.remote.binding import WorkspaceSessionBinding
from autoharness.remote.contracts import (
    AuthorityTier,
    RemoteRequest,
    RemoteResponse,
    SteerCommand,
    ensure_remotely_dispatchable,
)
from autoharness.remote.errors import (
    DuplicateRequestError,
    IllegalRemoteStateError,
    UnknownRemoteCommandError,
)
from autoharness.remote.rate_limit import TokenBucketRateLimiter
from autoharness.supervise.contracts import CancelRequested, JournalCheckpoint
from autoharness.supervise.session import Phase, SessionStateMachine, TERMINAL_PHASES


@runtime_checkable
class _LocalCommandChannel(Protocol):
    def handle_command(self, command: str) -> str: ...


@runtime_checkable
class _AppendOnlyJournal(Protocol):
    def append_event(self, event: object) -> int: ...


# Phases from which SessionStateMachine.transition(Phase.CANCELLING) is a
# legal edge, per supervise.session.LEGAL_TRANSITIONS. Kept as a frozenset
# here purely for a clear precondition error message; the state machine
# itself is still the sole authority -- an illegal transition would raise
# from supervise.session regardless of this check.
_CANCELLABLE_PHASES = frozenset(
    {
        Phase.BOOTSTRAPPING,
        Phase.PREFLIGHT,
        Phase.RESOLVING,
        Phase.LAUNCHING,
        Phase.RUNNING,
        Phase.RESTARTING,
    }
)


class SteerDispatcher:
    """Dispatches closed-vocabulary Steer commands onto existing local seams."""

    def __init__(
        self,
        *,
        state_machine: SessionStateMachine,
        local_channel: _LocalCommandChannel,
        journal: _AppendOnlyJournal,
        binding: WorkspaceSessionBinding,
        rate_limiter: TokenBucketRateLimiter,
    ) -> None:
        self.state_machine = state_machine
        self._local_channel = local_channel
        self._journal = journal
        self._binding = binding
        self._rate_limiter = rate_limiter
        self._paused = False
        self._seen_request_ids: set[str] = set()
        self._checkpoint_sequence = 0

    def dispatch(self, request: RemoteRequest, token: str, *, now: float) -> RemoteResponse:
        """Dispatch ``request`` after verifying vocabulary, binding, idempotency, and rate limit.

        Raises the appropriate :class:`~autoharness.remote.errors.RemoteError`
        subclass and performs NO state change or journal write when any
        precondition fails.
        """

        # 1. Closed vocabulary: only Steer commands are ever dispatchable
        #    through this method (Observe commands and local-only actions
        #    are rejected before anything else happens).
        tier = ensure_remotely_dispatchable(request.command)
        if tier is not AuthorityTier.STEER:
            raise UnknownRemoteCommandError(
                f"{request.command!r} is not a Steer command; SteerDispatcher only "
                "handles the Steer authority tier"
            )

        # 2. Binding verification -- fail closed before any state change.
        self._binding.verify(request, token, now=now)

        # 3. Idempotency -- a duplicate request_id is rejected before any
        #    state change, regardless of which command it names this time.
        if request.request_id in self._seen_request_ids:
            raise DuplicateRequestError(
                f"request_id {request.request_id!r} has already been processed"
            )

        # 4. Rate limit -- never blocks, fails closed immediately.
        self._rate_limiter.acquire()

        command = SteerCommand(request.command)
        if command is SteerCommand.PAUSE:
            payload = self._handle_pause()
        elif command is SteerCommand.RESUME:
            payload = self._handle_resume()
        elif command is SteerCommand.CANCEL:
            payload = self._handle_cancel()
        else:
            payload = self._handle_request_checkpoint()

        # A request that failed a state-legality check was not processed and
        # remains replayable after the local session changes phase.
        self._seen_request_ids.add(request.request_id)
        return RemoteResponse(request_id=request.request_id, command=request.command, ok=True, payload=payload)

    def _handle_pause(self) -> dict[str, object]:
        if self.state_machine.phase is not Phase.RUNNING or self._paused:
            raise IllegalRemoteStateError(
                "pause is only legal while the session is RUNNING and not already paused "
                f"(phase={self.state_machine.phase.value!r}, paused={self._paused!r})"
            )
        acknowledgement = self._local_channel.handle_command("pause")
        self._paused = True
        return {"acknowledgement": acknowledgement}

    def _handle_resume(self) -> dict[str, object]:
        if not self._paused:
            raise IllegalRemoteStateError(
                "resume is only legal after a prior pause; no pause is currently in effect"
            )
        acknowledgement = self._local_channel.handle_command("resume")
        self._paused = False
        return {"acknowledgement": acknowledgement}

    def _handle_cancel(self) -> dict[str, object]:
        if self.state_machine.phase in TERMINAL_PHASES or self.state_machine.phase not in _CANCELLABLE_PHASES:
            raise IllegalRemoteStateError(
                f"cancel is not legal from phase {self.state_machine.phase.value!r}"
            )
        self.state_machine.transition(Phase.CANCELLING)
        self._journal.append_event(CancelRequested(reason="remote steer request"))
        acknowledgement = self._local_channel.handle_command("cancel")
        return {"acknowledgement": acknowledgement, "phase": self.state_machine.phase.value}

    def _handle_request_checkpoint(self) -> dict[str, object]:
        if self.state_machine.phase in TERMINAL_PHASES:
            raise IllegalRemoteStateError(
                f"request_checkpoint is not legal once the session has reached a terminal "
                f"phase ({self.state_machine.phase.value!r})"
            )
        self._checkpoint_sequence += 1
        seq = self._journal.append_event(
            JournalCheckpoint(sequence=self._checkpoint_sequence, detail="remote steer request")
        )
        return {"sequence": self._checkpoint_sequence, "journal_seq": seq}
