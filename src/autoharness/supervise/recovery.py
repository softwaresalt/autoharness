"""Cancellation and restart recovery flows (119.006-T).

Two independent flows built on top of the 119.003-T session state machine:

* :func:`cancel_session` -- drives the machine through
  ``<phase> -> CANCELLING -> DRAINING -> CANCELLED`` from ANY post-LOCKING
  phase (every such phase has a legal edge into ``CANCELLING`` per
  :data:`autoharness.supervise.session.LEGAL_TRANSITIONS`), terminating a
  supervised child (via its
  :class:`~autoharness.supervise.process.ChildProcess` ``signal()``/
  ``close()`` contract) if one is running, journaling the cancellation,
  and releasing the session lock EXACTLY ONCE (F22).
* :class:`RestartController` -- restart budget tracking with exponential
  backoff. The budget DEFAULTS TO 0 (restart is opt-in via the explicit
  ``max_restarts`` constructor argument); every restart attempt requires
  BOTH remaining budget AND an explicit operator-confirmation callback.
  Budget exhaustion or a declined confirmation drains the session to
  ``FAILED`` (via ``DRAINING``) and NEVER loops -- ``FAILED`` is an
  absorbing terminal state in the session state machine, so a further
  :meth:`RestartController.attempt` call after exhaustion raises
  :class:`~autoharness.supervise.errors.IllegalTransitionError` rather than
  silently repeating.

**Resume** is intentionally minimal: :func:`resume_from_journal` reads
ONLY the 119.005-T journal cursor via
:func:`autoharness.supervise.journal.read_cursor`. This module never
imports anything backlogit-related and performs no filesystem access
outside the journal path -- asserted by construction in
``tests/test_supervise_recovery.py`` via an AST import scan, mirroring the
119.003-T no-event-bus-import contract in :mod:`autoharness.supervise.session`.

**Lock release contract**: this module calls ``lock.release()`` -- it does
not care whether ``lock`` is a real
:class:`autoharness.supervise.locking.SessionLock` or any other object
exposing a no-argument ``release()`` method; either satisfies the contract.
"""

from __future__ import annotations

import signal
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, Union

from autoharness.supervise.contracts import (
    CancelRequested,
    RestartExhausted,
    RestartScheduled,
    SessionPhaseChanged,
)
from autoharness.supervise.journal import SessionJournal, read_cursor
from autoharness.supervise.process import ChildProcess
from autoharness.supervise.session import Phase, SessionStateMachine

PathLike = Union[str, "Path"]


class ReleasableLock(Protocol):
    """Minimal structural contract this module depends on for lock release."""

    def release(self) -> None: ...


def cancel_session(
    machine: SessionStateMachine,
    *,
    child: Optional[ChildProcess] = None,
    journal: Optional[SessionJournal] = None,
    lock: Optional[ReleasableLock] = None,
    reason: str = "",
    signal_num: int = signal.SIGTERM,
) -> Phase:
    """Drive ``machine`` from its current (post-LOCKING) phase to CANCELLED.

    Terminates ``child`` (if given) via ``signal()`` then ``close()``,
    journals the cancellation request and the terminal phase transition (if
    ``journal`` is given), and releases ``lock`` EXACTLY ONCE (if given) --
    after the state machine has reached ``CANCELLED`` on the happy path,
    and on ANY OTHER exception raised anywhere in this function (P0 fix,
    128-S code review): ``lock.release()`` is guaranteed via ``finally`` so
    a lock can never be stranded by a raised exception, which would
    otherwise permanently block every future session from acquiring the
    guard lock -- worse than a double release. A child that has already
    exited by the time cancellation runs (a realistic, foreseeable race,
    e.g. it crashed or was reaped independently) is an EXPECTED outcome,
    not a failure: ``ProcessLookupError`` from ``child.signal()``/
    ``child.close()`` is swallowed so the DRAINING gateway and CANCELLED
    terminal are still reached normally rather than leaving the machine
    stuck in CANCELLING with the lock never released.
    """

    try:
        if journal is not None:
            journal.append_event(CancelRequested(reason=reason))

        if machine.phase is not Phase.CANCELLING:
            machine.transition(Phase.CANCELLING)

        if child is not None:
            try:
                child.signal(signal_num)
            except ProcessLookupError:
                pass  # child already exited/reaped -- nothing left to signal
            try:
                child.close()
            except ProcessLookupError:
                pass  # child already exited/reaped -- nothing left to close

        machine.transition(Phase.DRAINING)
        event: SessionPhaseChanged = machine.transition(Phase.CANCELLED)

        if journal is not None:
            journal.append_event(event)
    finally:
        if lock is not None:
            lock.release()

    return machine.phase


@dataclass
class RestartController:
    """Restart budget, backoff, and operator-confirmation gate.

    ``max_restarts`` DEFAULTS TO 0 -- restart is opt-in. Each
    :meth:`attempt` requires BOTH remaining budget (``attempts_used <
    max_restarts``) AND ``confirm_restart()`` returning ``True``; either
    condition failing drains the session to ``FAILED`` via ``DRAINING`` and
    never loops (``FAILED`` is absorbing in the session state machine).

    ``sleep_fn`` is injectable (default ``time.sleep``) so tests never sleep
    for real; backoff delay for the Nth attempt (0-indexed) is
    ``backoff_base_seconds * backoff_multiplier ** N``.
    """

    max_restarts: int = 0
    confirm_restart: Callable[[], bool] = field(default=lambda: False)
    sleep_fn: Callable[[float], None] = field(default=time.sleep)
    backoff_base_seconds: float = 1.0
    backoff_multiplier: float = 2.0

    attempts_used: int = field(default=0, init=False)

    @property
    def remaining_budget(self) -> int:
        return max(self.max_restarts - self.attempts_used, 0)

    def backoff_delay(self, attempt_index: int) -> float:
        """The backoff delay (seconds) for the ``attempt_index``'th attempt (0-indexed)."""

        return self.backoff_base_seconds * (self.backoff_multiplier**attempt_index)

    def attempt(
        self, machine: SessionStateMachine, *, journal: Optional[SessionJournal] = None
    ) -> Phase:
        """One restart attempt from RUNNING.

        On success: ``RUNNING -> RESTARTING -> LAUNCHING``, budget
        decremented, journaled via ``RestartScheduled``.

        On declined confirmation or exhausted budget:
        ``RUNNING -> RESTARTING -> DRAINING -> FAILED``, journaled via
        ``RestartExhausted``. This is a terminal, absorbing outcome -- a
        further :meth:`attempt` call after reaching ``FAILED`` raises
        :class:`~autoharness.supervise.errors.IllegalTransitionError`
        rather than looping.
        """

        machine.transition(Phase.RESTARTING)

        if self.remaining_budget <= 0 or not self.confirm_restart():
            if journal is not None:
                journal.append_event(RestartExhausted(attempts=self.attempts_used))
            machine.transition(Phase.DRAINING)
            machine.transition(Phase.FAILED)
            return machine.phase

        delay = self.backoff_delay(self.attempts_used)
        self.sleep_fn(delay)
        self.attempts_used += 1

        if journal is not None:
            journal.append_event(
                RestartScheduled(attempt=self.attempts_used, max_attempts=self.max_restarts)
            )

        machine.transition(Phase.LAUNCHING)
        return machine.phase


def resume_from_journal(journal_path: PathLike) -> int:
    """Resume support: read ONLY the 119.005-T journal cursor.

    Never reads or writes any backlogit checkpoint file, and performs no
    filesystem access beyond ``journal_path`` itself -- this module has no
    backlogit dependency by construction (verified in
    ``tests/test_supervise_recovery.py`` via an AST import scan).
    """

    return read_cursor(journal_path)
