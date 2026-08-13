"""Pure session lifecycle state machine (119.003-T).

This module is pure: no I/O, no subprocess invocation, no threads, and
critically NO dependency on :mod:`autoharness.supervise.events` (the
119.004-T event bus). This is the deliberate resolution of the F19
event/session import cycle: :class:`SessionStateMachine` constructs and
returns already-typed ``SessionPhaseChanged`` events (imported from
:mod:`autoharness.supervise.contracts`, never redefined here); it is the
caller's job to hand that event to an event bus if one exists. This module
never imports the event bus itself.

The 14-phase lifecycle and its legal-transition table are DATA
(:data:`LEGAL_TRANSITIONS`), not scattered conditional logic, so the graph
properties documented below can be verified by searching the table itself
rather than trusting a hand-written enumeration:

* :data:`TERMINAL_PHASES` is EXACTLY ``{EXITED, FAILED, REFUSED,
  CANCELLED}`` and every member is absorbing (no outgoing edges).
* ``DRAINING`` is the SOLE gateway into ``{EXITED, FAILED, CANCELLED}`` --
  every edge landing on one of those three originates at ``DRAINING``.
* ``REFUSED`` is the ONE documented exception: reachable ONLY directly from
  ``LOCKING`` (lock contention), never through ``DRAINING``.
* ``CANCELLING`` transitions ONLY to ``DRAINING`` -- there is no
  ``CANCELLING -> EXITED`` and no ``CANCELLING -> CANCELLED`` edge; both are
  illegal by omission from the table.
* Every post-LOCKING phase capable of a genuine (non-cancellation) failure
  -- ``BOOTSTRAPPING``, ``PREFLIGHT``, ``RESOLVING``, ``LAUNCHING``,
  ``RUNNING`` and ``RESTARTING`` -- carries a DIRECT edge to ``DRAINING``
  (P0 fix, 128-S closure-PR review), so a real failure never needs to be
  misrouted through ``CANCELLING`` (which represents an operator-initiated
  cancellation, a semantically different event) just to reach ``FAILED``.

:class:`SessionStateMachine` raises
:class:`~autoharness.supervise.errors.IllegalTransitionError` (kind
``ErrorKind.ILLEGAL_TRANSITION``) for any transition absent from the table,
with no permissive fallback: the machine's phase is left unchanged when a
transition is rejected.
"""

from __future__ import annotations

import enum
from types import MappingProxyType
from typing import Mapping

from autoharness.supervise.contracts import SessionPhaseChanged
from autoharness.supervise.errors import IllegalTransitionError


class Phase(enum.Enum):
    """The 14 supervised-session lifecycle phases."""

    INIT = "init"
    LOCKING = "locking"
    BOOTSTRAPPING = "bootstrapping"
    PREFLIGHT = "preflight"
    RESOLVING = "resolving"
    LAUNCHING = "launching"
    RUNNING = "running"
    CANCELLING = "cancelling"
    RESTARTING = "restarting"
    DRAINING = "draining"
    EXITED = "exited"
    FAILED = "failed"
    REFUSED = "refused"
    CANCELLED = "cancelled"


# The legal-transition table, as DATA. Every entry not listed here for a
# given source phase is illegal by omission -- there is no default/fallback
# edge computed from any other rule.
LEGAL_TRANSITIONS: Mapping[Phase, frozenset[Phase]] = MappingProxyType(
    {
        Phase.INIT: frozenset({Phase.LOCKING}),
        # REFUSED is the ONE documented exception to the DRAINING gateway,
        # reachable ONLY from LOCKING (lock contention).
        Phase.LOCKING: frozenset({Phase.BOOTSTRAPPING, Phase.REFUSED}),
        # Each pre-RUNNING phase also carries a DIRECT edge to DRAINING (P0
        # fix, 128-S closure-PR review): a genuine failure during
        # bootstrap/preflight/resolve/launch must be able to reach
        # FAILED via DRAINING WITHOUT being mislabeled as an
        # operator-initiated cancellation by routing through CANCELLING.
        # This mirrors the RUNNING/RESTARTING pattern below, where DRAINING
        # is already a direct destination for exactly this reason. The
        # spec's "no direct failure edge ... to FAILED" and "failure paths
        # terminate in FAILED via DRAINING" language is satisfied either
        # way (FAILED is still only reachable through DRAINING), but only
        # this direct edge lets a real failure be reported without a false
        # CANCELLING phase-change event appearing in the journal/event
        # stream.
        Phase.BOOTSTRAPPING: frozenset(
            {Phase.PREFLIGHT, Phase.CANCELLING, Phase.DRAINING}
        ),
        Phase.PREFLIGHT: frozenset(
            {Phase.RESOLVING, Phase.CANCELLING, Phase.DRAINING}
        ),
        Phase.RESOLVING: frozenset(
            {Phase.LAUNCHING, Phase.CANCELLING, Phase.DRAINING}
        ),
        Phase.LAUNCHING: frozenset(
            {Phase.RUNNING, Phase.CANCELLING, Phase.DRAINING}
        ),
        Phase.RUNNING: frozenset(
            {Phase.DRAINING, Phase.CANCELLING, Phase.RESTARTING}
        ),
        Phase.RESTARTING: frozenset(
            {Phase.LAUNCHING, Phase.CANCELLING, Phase.DRAINING}
        ),
        # CANCELLING -> DRAINING ONLY. No CANCELLING -> EXITED/CANCELLED.
        Phase.CANCELLING: frozenset({Phase.DRAINING}),
        # DRAINING is the SOLE gateway to every terminal state except REFUSED.
        Phase.DRAINING: frozenset({Phase.EXITED, Phase.FAILED, Phase.CANCELLED}),
        # Terminal phases are absorbing: no outgoing edges.
        Phase.EXITED: frozenset(),
        Phase.FAILED: frozenset(),
        Phase.REFUSED: frozenset(),
        Phase.CANCELLED: frozenset(),
    }
)

#: The exact, closed terminal-state set. No outgoing transitions exist from
#: any of these (see :data:`LEGAL_TRANSITIONS`).
TERMINAL_PHASES: frozenset[Phase] = frozenset(
    {Phase.EXITED, Phase.FAILED, Phase.REFUSED, Phase.CANCELLED}
)


class SessionStateMachine:
    """Drives a single session through :data:`LEGAL_TRANSITIONS`.

    Holds only the current :class:`Phase`; every transition is validated
    against the table with NO permissive fallback -- an illegal transition
    raises :class:`IllegalTransitionError` and leaves the current phase
    unchanged.
    """

    def __init__(self, initial_phase: Phase = Phase.INIT) -> None:
        self._phase = initial_phase

    @property
    def phase(self) -> Phase:
        return self._phase

    def transition(self, to_phase: Phase) -> SessionPhaseChanged:
        """Attempt to move to ``to_phase``.

        Returns the :class:`SessionPhaseChanged` event describing this one
        transition (exactly one event per successful call). Raises
        :class:`IllegalTransitionError` -- and leaves :attr:`phase`
        unchanged -- when ``to_phase`` is not a legal destination from the
        current phase.
        """

        legal_destinations = LEGAL_TRANSITIONS.get(self._phase, frozenset())
        if to_phase not in legal_destinations:
            raise IllegalTransitionError(
                f"illegal session transition: {self._phase.value!r} -> {to_phase.value!r}"
            )
        previous_phase = self._phase
        self._phase = to_phase
        return SessionPhaseChanged(phase=to_phase.value, previous_phase=previous_phase.value)
