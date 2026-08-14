"""Plan 2 V1 Observe surface (121.006-T).

:class:`ObserveService` answers the closed set of read-only Observe
commands (status/phase/progress/output_tail/journal_tail) by reading Plan
1's own seams -- the injected :class:`SessionStateMachine` and
:class:`SessionJournal` -- and never invents a second, parallel retention
store: remote Observe clients are stateless readers over data that is
already durable and already redacted.

**Single redaction choke point preserved**: :class:`BoundedOutputTail`
subscribes to ``ChildOutput`` events delivered by
:class:`~autoharness.supervise.events.EventBus`. ``EventBus.emit`` has
ALREADY applied :func:`~autoharness.supervise.redact.redact_record` before
any subscriber -- including this one -- ever sees the event. This module
therefore performs NO second redaction pass; doing so would either be
redundant or, worse, risk a second implementation drifting out of sync
with the first.

**Backpressure**: :class:`BoundedOutputTail` is a fixed-capacity ring
buffer that drops the oldest line on overflow and signals
``truncated``/``dropped_count`` rather than growing unbounded or blocking
the supervised child -- a slow or absent remote Observe client must never
stall local execution.
"""

from __future__ import annotations

from collections import deque
import threading
from typing import Mapping, Protocol, runtime_checkable

from autoharness.remote.binding import WorkspaceSessionBinding
from autoharness.remote.contracts import (
    AuthorityTier,
    ObserveCommand,
    RemoteRequest,
    RemoteResponse,
    ensure_remotely_dispatchable,
)
from autoharness.remote.errors import ObservationUnavailableError, UnknownRemoteCommandError
from autoharness.remote.rate_limit import TokenBucketRateLimiter
from autoharness.supervise.contracts import ChildOutput
from autoharness.supervise.events import EventBus
from autoharness.supervise.session import SessionStateMachine


@runtime_checkable
class _CursorReadableJournal(Protocol):
    def read_own_cursor(self) -> int: ...

    def read_own_tail(self, limit: int = 50) -> list[Mapping[str, object]]: ...


class BoundedOutputTail:
    """A fixed-capacity, drop-oldest ring buffer of observed child output lines."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._capacity = capacity
        self._lines: deque[str] = deque(maxlen=capacity)
        self._dropped_count = 0
        self._total_recorded = 0
        self._lock = threading.Lock()

    def record(self, event: ChildOutput) -> None:
        """Record a single already-redacted output line.

        Never raises and never blocks, even under sustained overflow: once
        the ring buffer is at capacity, recording a new line silently drops
        the oldest one (``collections.deque(maxlen=...)`` semantics) and
        :attr:`dropped_count` is incremented for observability.
        """

        with self._lock:
            if self._total_recorded >= self._capacity:
                self._dropped_count += 1
            self._lines.append(event.line)
            self._total_recorded += 1

    def tail(self) -> dict[str, object]:
        """Return the current buffered lines plus backpressure signaling."""

        with self._lock:
            return {
                "lines": list(self._lines),
                "truncated": self._dropped_count > 0,
                "dropped_count": self._dropped_count,
            }


class ObserveService:
    """Answers closed-vocabulary Observe commands over Plan 1's own seams."""

    def __init__(
        self,
        *,
        state_machine: SessionStateMachine,
        journal: _CursorReadableJournal,
        output_tail: BoundedOutputTail,
        binding: WorkspaceSessionBinding,
        rate_limiter: TokenBucketRateLimiter,
    ) -> None:
        self.state_machine = state_machine
        self._journal = journal
        self._output_tail = output_tail
        self._binding = binding
        self._rate_limiter = rate_limiter
        self._bus_subscription_token: str | None = None

    def attach(self, bus: EventBus) -> None:
        """Subscribe to ``ChildOutput`` events on ``bus``.

        ``EventBus.emit`` has already redacted the event before this
        service's handler ever runs -- see the module docstring.
        """

        self._bus_subscription_token = bus.subscribe(ChildOutput, self._output_tail.record)

    def _read_journal_tail(self, *, limit: int = 50) -> list[Mapping[str, object]]:
        try:
            return self._journal.read_own_tail(limit=limit)
        except (OSError, ValueError) as exc:
            raise ObservationUnavailableError(
                "local journal data is missing, malformed, or unavailable"
            ) from exc

    def handle(self, request: RemoteRequest, token: str, *, now: float) -> RemoteResponse:
        """Handle ``request`` after verifying vocabulary, binding, and rate limit.

        Raises the appropriate :class:`~autoharness.remote.errors.RemoteError`
        subclass; performs no state mutation in any case (Observe is
        strictly read-only).
        """

        tier = ensure_remotely_dispatchable(request.command)
        if tier is not AuthorityTier.OBSERVE:
            raise UnknownRemoteCommandError(
                f"{request.command!r} is not an Observe command; ObserveService only "
                "handles the Observe authority tier"
            )

        self._binding.verify(request, token, now=now)
        self._rate_limiter.acquire()

        command = ObserveCommand(request.command)
        if command in (ObserveCommand.STATUS, ObserveCommand.PHASE):
            payload: dict[str, object] = {"phase": self.state_machine.phase.value}
        elif command is ObserveCommand.PROGRESS:
            records = self._read_journal_tail()
            payload = {
                "journal_cursor": self._journal.read_own_cursor(),
                "record_count": len(records),
            }
        elif command is ObserveCommand.OUTPUT_TAIL:
            if self._bus_subscription_token is None:
                raise ObservationUnavailableError(
                    "the Observe service is not attached to the local event bus"
                )
            payload = self._output_tail.tail()
        else:
            records = self._read_journal_tail()
            payload = {
                "cursor": self._journal.read_own_cursor(),
                "records": records,
            }

        return RemoteResponse(request_id=request.request_id, command=request.command, ok=True, payload=payload)
