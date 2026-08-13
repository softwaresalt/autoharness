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


def _best_effort_child_cleanup(
    child: Optional[ChildProcess], signal_num: int
) -> None:
    """Best-effort ``signal()`` + ``close()`` for a possibly-still-live
    child, swallowing every exception (this is only ever called from a
    ``finally`` block as a safety net -- it must never mask or replace
    whatever exception is already propagating, and a child that cannot be
    cleaned up here is no worse off than one this function was never
    called for).

    Catches ``BaseException``, not ``Exception``: ``Exception`` does not
    cover ``KeyboardInterrupt``/``SystemExit``/other ``BaseException``
    subclasses, so a ``finally``-block safety net that only caught
    ``Exception`` could let one of those escape this helper -- masking the
    exception already propagating from the caller's ``try`` block and
    skipping the caller's subsequent ``lock.release()``, recreating the
    exact stranded-lock failure this helper exists to prevent (Copilot
    review, PR #330).
    """

    if child is None:
        return
    try:
        child.signal(signal_num)
    except BaseException:
        pass
    try:
        child.close()
    except BaseException:
        pass


def cancel_session(
    machine: SessionStateMachine,
    *,
    child: Optional[ChildProcess] = None,
    journal: Optional[SessionJournal] = None,
    emit: Optional[Callable[[Any], None]] = None,
    lock: Optional[ReleasableLock] = None,
    reason: str = "",
    signal_num: int = signal.SIGTERM,
) -> Phase:
    """Drive ``machine`` from its current (post-LOCKING) phase to CANCELLED.

    Terminates ``child`` (if given) via ``signal()`` then ``close()``,
    records the cancellation request and the terminal phase transition,
    and releases ``lock`` EXACTLY ONCE (if given) --
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

    **Event recording (``emit`` vs ``journal``, P-018 Copilot review
    finding, PR #331, comment 3778121169)**: when ``emit`` is supplied
    (e.g. ``run_session``'s own synchronized ``_emit`` closure, which
    both publishes to the ``EventBus`` AND journals under a shared lock),
    every event this function would otherwise journal directly is instead
    routed through ``emit``. Without this, ``EventBus`` subscribers never
    observed cancellation events at all (only the journal did, via a
    direct, unsynchronized ``journal.append_event`` call), and that direct
    call could race with a concurrent PTY output-pump thread's own
    ``emit``-routed ``ChildOutput`` journal writes, risking duplicate/
    out-of-order journal sequence numbers. ``journal`` (when given without
    ``emit``) is kept as the ORIGINAL direct-journal-only fallback for
    backward compatibility with callers that have no bus/lock to route
    through (e.g. this module's own unit tests).

    **Lock-release-before-observable-CANCELLED (128-S review remediation)**:
    the task's own acceptance criteria require that "CANCELLED is entered
    ONLY AFTER child termination, journal flush and lock release have
    COMPLETED inside DRAINING" -- i.e. no caller/observer holding a
    reference to ``machine`` may ever see ``phase == CANCELLED`` while the
    guard lock is still held. ``lock.release()`` is therefore called BEFORE
    the final ``machine.transition(Phase.CANCELLED)`` call (which is the
    exact statement that makes CANCELLED externally observable), not after.

    **Best-effort child cleanup before an exceptional lock release (P0
    fix, 128-S closure-PR review)**: if an unexpected exception is raised
    BEFORE the child has been signalled/closed on the happy path above (for
    example, recording ``CancelRequested`` or the ``CANCELLING`` transition
    itself raises), the ``finally`` block below now ALSO attempts
    ``child.signal()``/``child.close()`` -- best-effort, every exception
    swallowed -- before releasing ``lock``. Releasing the lock without ever
    attempting to terminate a still-live child would let a second
    supervised session start concurrently against the same workspace while
    the orphaned child keeps running; a best-effort cleanup attempt closes
    that gap without risking masking the original exception (this cleanup
    is entirely exception-swallowing) or double work (skipped when the
    happy-path cleanup already ran).
    """

    def _record(event: Any) -> None:
        if emit is not None:
            emit(event)
        elif journal is not None:
            journal.append_event(event)

    lock_released = False
    child_cleanup_done = False
    try:
        _record(CancelRequested(reason=reason))

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
            child_cleanup_done = True

        draining_event = machine.transition(Phase.DRAINING)
        _record(draining_event)

        # Release the guard lock BEFORE the CANCELLED transition below makes
        # the terminal phase externally observable (see docstring).
        if lock is not None:
            lock.release()
            lock_released = True

        event: SessionPhaseChanged = machine.transition(Phase.CANCELLED)
        _record(event)
    finally:
        if not child_cleanup_done:
            _best_effort_child_cleanup(child, signal_num)
        if lock is not None and not lock_released:
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
        self,
        machine: SessionStateMachine,
        *,
        journal: Optional[SessionJournal] = None,
        emit: Optional[Callable[[Any], None]] = None,
        child: Optional[ChildProcess] = None,
        lock: Optional[ReleasableLock] = None,
        reason: str = "",
        signal_num: int = signal.SIGTERM,
    ) -> Phase:
        """One restart attempt from RUNNING.

        On success: ``RUNNING -> RESTARTING -> LAUNCHING``, budget
        decremented, recorded via ``RestartScheduled`` (with ``reason``,
        128-S review remediation -- operational journals must be able to
        explain WHY a restart occurred, not just count attempts).

        On declined confirmation or exhausted budget:
        ``RUNNING -> RESTARTING -> DRAINING -> FAILED``, recorded via
        ``RestartExhausted``. This is a terminal, absorbing outcome -- a
        further :meth:`attempt` call after reaching ``FAILED`` raises
        :class:`~autoharness.supervise.errors.IllegalTransitionError`
        rather than looping. Per F22/the every-failure-path lock contract
        (128-S review remediation), this exhaustion/decline path ALSO
        terminates ``child`` (if given) and releases ``lock`` EXACTLY ONCE
        (guaranteed via ``finally``, mirroring :func:`cancel_session`) --
        every failure path must complete DRAINING cleanup and release the
        lock, not only the explicit cancellation path. A best-effort
        child-cleanup attempt also runs in ``finally`` (P0 fix, 128-S
        closure-PR review) before the lock is released, in case an
        exception was raised before the happy-path child cleanup above ran
        -- mirroring :func:`cancel_session`'s equivalent fix.

        **Event recording (``emit`` vs ``journal``, P-018 Copilot review
        finding, PR #331, comment 3778121169)**: identical rationale to
        :func:`cancel_session`'s own docstring -- when ``emit`` is
        supplied, every event this method would otherwise journal directly
        is instead routed through it (published to the ``EventBus`` AND
        journaled under its shared lock); ``journal`` alone remains the
        original direct-journal-only fallback for callers with no
        bus/lock to route through.
        """

        def _record(event: Any) -> None:
            if emit is not None:
                emit(event)
            elif journal is not None:
                journal.append_event(event)

        machine.transition(Phase.RESTARTING)

        # Fail-closed confirmation (128-S review remediation): the plan's
        # non-interactive-approval contract requires this callback to
        # "never auto-approve" -- a callback that RAISES (e.g. an
        # unavailable approval channel) must be treated identically to an
        # explicit decline, not left to propagate and strand the session in
        # RESTARTING with the lock never released. Any exception here is
        # therefore equivalent to ``confirm_restart() -> False``.
        try:
            confirmed = self.confirm_restart()
        except Exception:
            confirmed = False

        if self.remaining_budget <= 0 or not confirmed:
            lock_released = False
            child_cleanup_done = False
            try:
                _record(RestartExhausted(attempts=self.attempts_used))
                draining_event = machine.transition(Phase.DRAINING)
                _record(draining_event)

                if child is not None:
                    try:
                        child.signal(signal_num)
                    except ProcessLookupError:
                        pass
                    try:
                        child.close()
                    except ProcessLookupError:
                        pass
                    child_cleanup_done = True

                if lock is not None:
                    lock.release()
                    lock_released = True

                event = machine.transition(Phase.FAILED)
                _record(event)
            finally:
                # Best-effort child cleanup before an exceptional lock
                # release (P0 fix, 128-S closure-PR review) -- mirrors
                # cancel_session's finally: if journal/DRAINING-transition
                # raised before the happy-path cleanup above ran, attempt
                # it here first so the lock is never released while a
                # still-live child goes untouched.
                if not child_cleanup_done:
                    _best_effort_child_cleanup(child, signal_num)
                if lock is not None and not lock_released:
                    lock.release()
            return machine.phase

        # Approved restart (128-S review remediation): the OLD child (if
        # still live) must be terminated BEFORE the machine returns to
        # LAUNCHING, mirroring the exhaustion branch's cleanup above.
        # Without this, a still-running previous child can continue
        # alongside whatever the caller launches next, in direct
        # contradiction of "budget exhaustion drains ... and NEVER loops" --
        # the approved path is not exempt from the same every-restart
        # cleanup contract, it simply proceeds to LAUNCHING afterward
        # instead of draining to FAILED.
        if child is not None:
            try:
                child.signal(signal_num)
            except ProcessLookupError:
                pass  # child already exited/reaped -- nothing left to signal
            try:
                child.close()
            except ProcessLookupError:
                pass  # child already exited/reaped -- nothing left to close

        delay = self.backoff_delay(self.attempts_used)
        self.sleep_fn(delay)
        self.attempts_used += 1

        _record(
            RestartScheduled(
                attempt=self.attempts_used, max_attempts=self.max_restarts, reason=reason
            )
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
