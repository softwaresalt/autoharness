"""Tests for autoharness.supervise.session -- the session state machine (119.003-T).

Covers the full legal-transition table (positive and negative controls),
cancellation vs. normal-completion terminal divergence, a mandatory
graph-property test that verifies the DRAINING-gateway invariant and
absorbing terminal states via graph search (not hand enumeration), and the
one-event-per-transition contract.
"""

from __future__ import annotations

import unittest
from collections import deque

from autoharness.supervise.contracts import SessionPhaseChanged
from autoharness.supervise.errors import ErrorKind, IllegalTransitionError
from autoharness.supervise.session import (
    LEGAL_TRANSITIONS,
    TERMINAL_PHASES,
    Phase,
    SessionStateMachine,
)

ALL_PHASES = tuple(Phase)


class PhaseEnumTests(unittest.TestCase):
    def test_exact_phase_set(self) -> None:
        expected = {
            "INIT",
            "LOCKING",
            "BOOTSTRAPPING",
            "PREFLIGHT",
            "RESOLVING",
            "LAUNCHING",
            "RUNNING",
            "CANCELLING",
            "RESTARTING",
            "DRAINING",
            "EXITED",
            "FAILED",
            "REFUSED",
            "CANCELLED",
        }
        self.assertEqual({phase.name for phase in Phase}, expected)


class TerminalSetTests(unittest.TestCase):
    def test_terminal_set_is_exact(self) -> None:
        self.assertEqual(
            TERMINAL_PHASES,
            frozenset({Phase.EXITED, Phase.FAILED, Phase.REFUSED, Phase.CANCELLED}),
        )

    def test_terminal_phases_are_absorbing(self) -> None:
        for phase in TERMINAL_PHASES:
            self.assertEqual(
                LEGAL_TRANSITIONS.get(phase, frozenset()),
                frozenset(),
                f"{phase} must have no outgoing transitions",
            )


class LegalEdgeTests(unittest.TestCase):
    """Enumerate the full transition table from the spec and assert each
    legal edge succeeds via a fresh state machine driven to that source
    phase."""

    LEGAL_EDGES = (
        (Phase.INIT, Phase.LOCKING),
        (Phase.LOCKING, Phase.BOOTSTRAPPING),
        (Phase.LOCKING, Phase.REFUSED),
        (Phase.BOOTSTRAPPING, Phase.PREFLIGHT),
        (Phase.BOOTSTRAPPING, Phase.CANCELLING),
        (Phase.PREFLIGHT, Phase.RESOLVING),
        (Phase.PREFLIGHT, Phase.CANCELLING),
        (Phase.RESOLVING, Phase.LAUNCHING),
        (Phase.RESOLVING, Phase.CANCELLING),
        (Phase.LAUNCHING, Phase.RUNNING),
        (Phase.LAUNCHING, Phase.CANCELLING),
        (Phase.RUNNING, Phase.DRAINING),
        (Phase.RUNNING, Phase.CANCELLING),
        (Phase.RUNNING, Phase.RESTARTING),
        (Phase.RESTARTING, Phase.LAUNCHING),
        (Phase.RESTARTING, Phase.CANCELLING),
        (Phase.RESTARTING, Phase.DRAINING),
        (Phase.CANCELLING, Phase.DRAINING),
        (Phase.DRAINING, Phase.EXITED),
        (Phase.DRAINING, Phase.FAILED),
        (Phase.DRAINING, Phase.CANCELLED),
    )

    def _path_to(self, target_source: Phase) -> list[Phase]:
        """BFS a shortest path of legal edges from INIT to ``target_source``."""

        queue = deque([(Phase.INIT, [Phase.INIT])])
        seen = {Phase.INIT}
        while queue:
            current, path = queue.popleft()
            if current == target_source:
                return path
            for nxt in LEGAL_TRANSITIONS.get(current, frozenset()):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, path + [nxt]))
        raise AssertionError(f"no path from INIT to {target_source}")

    def test_every_documented_legal_edge_succeeds(self) -> None:
        for source, dest in self.LEGAL_EDGES:
            with self.subTest(source=source, dest=dest):
                path = self._path_to(source)
                machine = SessionStateMachine()
                for step in path[1:]:
                    machine.transition(step)
                event = machine.transition(dest)
                self.assertEqual(machine.phase, dest)
                self.assertIsInstance(event, SessionPhaseChanged)
                self.assertEqual(event.phase, dest.value)

    def test_exact_edge_set_matches_table(self) -> None:
        actual_edges = {
            (source, dest)
            for source, dests in LEGAL_TRANSITIONS.items()
            for dest in dests
        }
        self.assertEqual(actual_edges, set(self.LEGAL_EDGES))


class IllegalEdgeTests(unittest.TestCase):
    def test_cancelling_to_exited_is_illegal(self) -> None:
        machine = SessionStateMachine()
        for step in (Phase.LOCKING, Phase.BOOTSTRAPPING, Phase.CANCELLING):
            machine.transition(step)
        with self.assertRaises(IllegalTransitionError) as ctx:
            machine.transition(Phase.EXITED)
        self.assertEqual(ctx.exception.kind, ErrorKind.ILLEGAL_TRANSITION)

    def test_cancelling_to_cancelled_is_illegal(self) -> None:
        machine = SessionStateMachine()
        for step in (Phase.LOCKING, Phase.BOOTSTRAPPING, Phase.CANCELLING):
            machine.transition(step)
        with self.assertRaises(IllegalTransitionError) as ctx:
            machine.transition(Phase.CANCELLED)
        self.assertEqual(ctx.exception.kind, ErrorKind.ILLEGAL_TRANSITION)

    def test_sample_of_illegal_edges_all_raise(self) -> None:
        legal = set(LegalEdgeTests.LEGAL_EDGES)
        sample_sources = (Phase.INIT, Phase.LOCKING, Phase.RUNNING, Phase.DRAINING, Phase.RESTARTING)
        for source in sample_sources:
            for dest in ALL_PHASES:
                if (source, dest) in legal:
                    continue
                with self.subTest(source=source, dest=dest):
                    machine = SessionStateMachine(initial_phase=source)
                    with self.assertRaises(IllegalTransitionError):
                        machine.transition(dest)

    def test_no_permissive_fallback_stays_in_place_after_failed_transition(self) -> None:
        machine = SessionStateMachine()
        with self.assertRaises(IllegalTransitionError):
            machine.transition(Phase.RUNNING)
        self.assertEqual(machine.phase, Phase.INIT)


class TerminalDivergenceTests(unittest.TestCase):
    def test_cancellation_run_reaches_cancelled(self) -> None:
        machine = SessionStateMachine()
        for step in (
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
            Phase.CANCELLING,
            Phase.DRAINING,
            Phase.CANCELLED,
        ):
            machine.transition(step)
        self.assertEqual(machine.phase, Phase.CANCELLED)

    def test_normal_completion_run_reaches_exited(self) -> None:
        machine = SessionStateMachine()
        for step in (
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
            Phase.DRAINING,
            Phase.EXITED,
        ):
            machine.transition(step)
        self.assertEqual(machine.phase, Phase.EXITED)

    def test_cancellation_and_completion_terminals_differ(self) -> None:
        cancel_machine = SessionStateMachine()
        for step in (
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.CANCELLING,
            Phase.DRAINING,
            Phase.CANCELLED,
        ):
            cancel_machine.transition(step)

        complete_machine = SessionStateMachine()
        for step in (
            Phase.LOCKING,
            Phase.BOOTSTRAPPING,
            Phase.PREFLIGHT,
            Phase.RESOLVING,
            Phase.LAUNCHING,
            Phase.RUNNING,
            Phase.DRAINING,
            Phase.EXITED,
        ):
            complete_machine.transition(step)

        self.assertNotEqual(cancel_machine.phase, complete_machine.phase)


class GraphPropertyTests(unittest.TestCase):
    """Mandatory graph-property test: search the table itself (BFS/DFS), not
    a hand-enumerated list."""

    def _reachable(self, start: Phase) -> set[Phase]:
        seen = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for nxt in LEGAL_TRANSITIONS.get(current, frozenset()):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return seen

    def test_absorbing_terminal_states_via_graph_search(self) -> None:
        for phase in TERMINAL_PHASES:
            self.assertEqual(LEGAL_TRANSITIONS.get(phase, frozenset()), frozenset())

    def test_every_reachable_terminal_from_every_post_locking_phase_is_in_terminal_set(
        self,
    ) -> None:
        post_locking_phases = [p for p in Phase if p not in (Phase.INIT,)]
        for phase in post_locking_phases:
            reachable = self._reachable(phase)
            reachable_terminals = {
                p for p in reachable if not LEGAL_TRANSITIONS.get(p, frozenset())
            }
            with self.subTest(phase=phase):
                self.assertTrue(reachable_terminals.issubset(TERMINAL_PHASES))

    def test_every_path_to_exited_failed_or_cancelled_passes_through_draining(self) -> None:
        # For every phase strictly after LOCKING (i.e. excluding the direct
        # LOCKING->REFUSED exception), any path reaching EXITED/FAILED/CANCELLED
        # must pass through DRAINING. We verify this structurally: the only
        # incoming edges into {EXITED, FAILED, CANCELLED} in the whole table
        # originate at DRAINING.
        gateway_targets = {Phase.EXITED, Phase.FAILED, Phase.CANCELLED}
        for source, dests in LEGAL_TRANSITIONS.items():
            for dest in dests:
                if dest in gateway_targets:
                    with self.subTest(source=source, dest=dest):
                        self.assertEqual(
                            source,
                            Phase.DRAINING,
                            f"only DRAINING may transition directly into {dest}",
                        )

    def test_refused_is_reachable_only_directly_from_locking(self) -> None:
        for source, dests in LEGAL_TRANSITIONS.items():
            if Phase.REFUSED in dests:
                self.assertEqual(source, Phase.LOCKING)

    def test_no_outgoing_edges_from_any_terminal_phase_via_graph_search(self) -> None:
        for phase in TERMINAL_PHASES:
            reachable = self._reachable(phase)
            self.assertEqual(reachable, {phase}, f"{phase} must be absorbing")


class OneEventPerTransitionTests(unittest.TestCase):
    def test_transition_emits_exactly_one_event(self) -> None:
        machine = SessionStateMachine()
        event = machine.transition(Phase.LOCKING)
        self.assertIsInstance(event, SessionPhaseChanged)
        self.assertEqual(event.phase, Phase.LOCKING.value)
        self.assertEqual(event.previous_phase, Phase.INIT.value)

    def test_events_track_previous_phase_across_multiple_transitions(self) -> None:
        machine = SessionStateMachine()
        first = machine.transition(Phase.LOCKING)
        second = machine.transition(Phase.BOOTSTRAPPING)
        self.assertEqual(first.previous_phase, Phase.INIT.value)
        self.assertEqual(second.previous_phase, Phase.LOCKING.value)
        self.assertEqual(second.phase, Phase.BOOTSTRAPPING.value)


class NoEventBusDependencyTests(unittest.TestCase):
    def test_session_module_does_not_import_events_module(self) -> None:
        import ast

        import autoharness.supervise.session as session_module

        source = session_module.__file__
        with open(source, "r", encoding="utf-8") as handle:
            content = handle.read()
        tree = ast.parse(content)
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        self.assertNotIn("autoharness.supervise.events", imported_modules)
        self.assertNotIn("events", {name.rsplit(".", 1)[-1] for name in imported_modules})


if __name__ == "__main__":
    unittest.main()
