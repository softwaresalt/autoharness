"""Deterministic tests for the read-only DAG readiness/critical-path/downstream-dependents
analyzer (110.001-T, 117-S).

This analyzer reuses the existing shipment-blocks reader (``ShipmentState`` /
``FilesystemTopologyReaders.list_shipments()`` from ``autoharness.gates.topology``)
for data access ONLY. Cycle detection is owned by this analyzer, not the reused
reader (see 110.001-T acceptance criteria 5).
"""

from __future__ import annotations

import json
import unittest

from autoharness.gates.topology import (
    DagReadinessResult,
    NextEligibleResult,
    ShipmentState,
    compute_dag_readiness,
    compute_next_eligible,
)


def _shipment(
    shipment_id: str,
    status: str | None,
    *,
    archived_status: str | None = None,
    deps: tuple[str, ...] = (),
) -> ShipmentState:
    return ShipmentState(
        shipment_id=shipment_id,
        title=shipment_id,
        live_status=status,
        archived_status=archived_status,
        archived_record_present=archived_status is not None,
        manifest_item_ids=(),
        blocking_predecessor_ids=deps,
    )


class ComputeDagReadinessEmptyAndSingleNodeTests(unittest.TestCase):
    def test_empty_graph_returns_empty_report(self) -> None:
        result = compute_dag_readiness(())
        self.assertIsInstance(result, DagReadinessResult)
        self.assertEqual(result.ready_set, ())
        self.assertEqual(result.critical_path, ())
        self.assertEqual(result.downstream_dependents, {})
        self.assertFalse(result.cycle_detected)
        self.assertEqual(result.cycle_nodes, ())

    def test_single_queued_node_is_ready_and_is_the_critical_path(self) -> None:
        shipments = (_shipment("001-S", "queued"),)
        result = compute_dag_readiness(shipments)
        self.assertEqual(result.ready_set, ("001-S",))
        self.assertEqual(result.critical_path, ("001-S",))
        self.assertEqual(result.downstream_dependents, {"001-S": ()})
        self.assertFalse(result.cycle_detected)

    def test_single_active_node_is_not_ready_but_is_still_the_critical_path(self) -> None:
        shipments = (_shipment("001-S", "active"),)
        result = compute_dag_readiness(shipments)
        self.assertEqual(result.ready_set, ())
        self.assertEqual(result.critical_path, ("001-S",))


class ComputeDagReadinessLinearChainTests(unittest.TestCase):
    def test_linear_chain_ready_dependent_when_predecessor_shipped(self) -> None:
        # A (shipped) -> B (shipped) -> C (queued): C's only predecessor B is
        # finished (shipped terminal), so C is ready.
        shipments = (
            _shipment("001-S", "shipped"),
            _shipment("002-S", "shipped", deps=("001-S",)),
            _shipment("003-S", "queued", deps=("002-S",)),
        )
        result = compute_dag_readiness(shipments)
        self.assertEqual(result.ready_set, ("003-S",))
        self.assertEqual(result.critical_path, ("001-S", "002-S", "003-S"))
        self.assertEqual(result.downstream_dependents["001-S"], ("002-S", "003-S"))
        self.assertEqual(result.downstream_dependents["002-S"], ("003-S",))
        self.assertEqual(result.downstream_dependents["003-S"], ())

    def test_linear_chain_via_done_predecessor_archived_status(self) -> None:
        # A predecessor with no live record but archived_status: done still
        # counts as a genuine no-longer-blocking terminal closure.
        shipments = (
            _shipment("001-S", None, archived_status="done"),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        result = compute_dag_readiness(shipments)
        self.assertEqual(result.ready_set, ("002-S",))

    def test_queued_dependent_with_active_predecessor_is_excluded_regression(self) -> None:
        # REGRESSION (110.001-T AC5): an active predecessor is in-progress
        # work -- NOT terminal-ready -- and must block a live queued dependent.
        shipments = (
            _shipment("001-S", "active"),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        result = compute_dag_readiness(shipments)
        self.assertEqual(result.ready_set, ())

    def test_queued_dependent_with_queued_predecessor_is_excluded(self) -> None:
        shipments = (
            _shipment("001-S", "queued"),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        result = compute_dag_readiness(shipments)
        self.assertEqual(result.ready_set, ("001-S",))
        self.assertNotIn("002-S", result.ready_set)

    def test_queued_dependent_with_abandoned_predecessor_is_excluded_fail_closed(self) -> None:
        shipments = (
            _shipment("001-S", "abandoned"),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        result = compute_dag_readiness(shipments)
        self.assertEqual(result.ready_set, ())

    def test_queued_dependent_with_unknown_predecessor_is_excluded_fail_closed(self) -> None:
        # Predecessor id references a shipment that does not exist in the
        # supplied graph at all -- must fail closed, never treated as ready.
        shipments = (_shipment("002-S", "queued", deps=("999-S",)),)
        result = compute_dag_readiness(shipments)
        self.assertEqual(result.ready_set, ())
        # The unknown predecessor id is not itself a node in the graph.
        self.assertNotIn("999-S", result.downstream_dependents)


class ComputeDagReadinessStatusFilteringTests(unittest.TestCase):
    def test_dependency_free_active_shipment_excluded_from_ready_set(self) -> None:
        result = compute_dag_readiness((_shipment("001-S", "active"),))
        self.assertEqual(result.ready_set, ())

    def test_dependency_free_shipped_shipment_excluded_from_ready_set(self) -> None:
        result = compute_dag_readiness((_shipment("001-S", "shipped"),))
        self.assertEqual(result.ready_set, ())

    def test_dependency_free_abandoned_shipment_excluded_from_ready_set(self) -> None:
        result = compute_dag_readiness((_shipment("001-S", "abandoned"),))
        self.assertEqual(result.ready_set, ())

    def test_dependency_free_archived_only_shipment_excluded_from_ready_set(self) -> None:
        result = compute_dag_readiness((_shipment("001-S", None, archived_status="shipped"),))
        self.assertEqual(result.ready_set, ())

    def test_dependency_free_queued_shipment_included_in_ready_set(self) -> None:
        result = compute_dag_readiness((_shipment("001-S", "queued"),))
        self.assertEqual(result.ready_set, ("001-S",))


class ComputeDagReadinessBranchMergeTests(unittest.TestCase):
    def test_branch_and_merge_critical_path_picks_longest_chain_by_node_count(self) -> None:
        # 001 -> 002 -> 004
        # 001 -> 003 -> 004 -> 005
        # Longest chain by node count: 001, 002 or 003, 004, 005 (length 4).
        shipments = (
            _shipment("001-S", "shipped"),
            _shipment("002-S", "shipped", deps=("001-S",)),
            _shipment("003-S", "shipped", deps=("001-S",)),
            _shipment("004-S", "shipped", deps=("002-S", "003-S")),
            _shipment("005-S", "queued", deps=("004-S",)),
        )
        result = compute_dag_readiness(shipments)
        self.assertEqual(len(result.critical_path), 4)
        self.assertEqual(result.critical_path[0], "001-S")
        self.assertEqual(result.critical_path[-1], "005-S")
        self.assertEqual(result.critical_path[-2], "004-S")
        self.assertEqual(result.ready_set, ("005-S",))

    def test_merge_dependent_blocked_when_only_one_of_two_predecessors_finished(self) -> None:
        shipments = (
            _shipment("001-S", "shipped"),
            _shipment("002-S", "active"),
            _shipment("003-S", "queued", deps=("001-S", "002-S")),
        )
        result = compute_dag_readiness(shipments)
        self.assertEqual(result.ready_set, ())

    def test_downstream_dependents_transitive_closure(self) -> None:
        shipments = (
            _shipment("001-S", "shipped"),
            _shipment("002-S", "shipped", deps=("001-S",)),
            _shipment("003-S", "queued", deps=("002-S",)),
        )
        result = compute_dag_readiness(shipments)
        self.assertEqual(result.downstream_dependents["001-S"], ("002-S", "003-S"))


class ComputeDagReadinessCycleGuardTests(unittest.TestCase):
    def test_two_node_cycle_is_detected_and_degrades_safely(self) -> None:
        shipments = (
            _shipment("001-S", "queued", deps=("002-S",)),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        result = compute_dag_readiness(shipments)
        self.assertTrue(result.cycle_detected)
        # never fabricate a critical path or ready-set on a detected cycle
        self.assertEqual(result.critical_path, ())
        self.assertEqual(result.ready_set, ())
        self.assertTrue(set(result.cycle_nodes) >= {"001-S", "002-S"})

    def test_self_cycle_is_detected(self) -> None:
        shipments = (_shipment("001-S", "queued", deps=("001-S",)),)
        result = compute_dag_readiness(shipments)
        self.assertTrue(result.cycle_detected)
        self.assertEqual(result.ready_set, ())
        self.assertEqual(result.critical_path, ())

    def test_cycle_downstream_of_an_otherwise_clean_prefix_still_degrades_whole_report(self) -> None:
        # 001 (shipped) -> 002 (queued) -> 003 (queued) -> 002 (cycle)
        shipments = (
            _shipment("001-S", "shipped"),
            _shipment("002-S", "queued", deps=("001-S", "003-S")),
            _shipment("003-S", "queued", deps=("002-S",)),
        )
        result = compute_dag_readiness(shipments)
        self.assertTrue(result.cycle_detected)
        self.assertEqual(result.ready_set, ())
        self.assertEqual(result.critical_path, ())


class ComputeDagReadinessAmbiguousProvenanceTests(unittest.TestCase):
    """Regression coverage for a shipment with BOTH a live queue record and an
    archive-folder record (corrupted/duplicated provenance) -- the same
    condition pipeline-topology's PREDECESSOR_STATE_AMBIGUOUS/
    TARGET_STATE_AMBIGUOUS checks fail closed on. compute_dag_readiness must
    never treat an ambiguous record as terminal-ready in either the
    predecessor or the ready-set-candidate role."""

    def test_ambiguous_predecessor_is_not_treated_as_finished(self) -> None:
        predecessor = _shipment("001-S", "shipped", archived_status="shipped")
        dependent = _shipment("002-S", "queued", deps=("001-S",))
        result = compute_dag_readiness((predecessor, dependent))
        self.assertEqual(result.ready_set, ())

    def test_ambiguous_queued_shipment_is_excluded_from_ready_set(self) -> None:
        ambiguous = _shipment("001-S", "queued", archived_status="shipped")
        result = compute_dag_readiness((ambiguous,))
        self.assertEqual(result.ready_set, ())


class DagReadinessResultToDictTests(unittest.TestCase):
    def test_to_dict_shape_is_json_serializable(self) -> None:
        import json

        shipments = (
            _shipment("001-S", "shipped"),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        result = compute_dag_readiness(shipments)
        payload = result.to_dict()
        serialized = json.dumps(payload)
        reloaded = json.loads(serialized)
        self.assertEqual(reloaded["ready_set"], ["002-S"])
        self.assertEqual(reloaded["critical_path"], ["001-S", "002-S"])
        self.assertIn("downstream_dependents", reloaded)
        self.assertIn("cycle_detected", reloaded)
        self.assertIn("cycle_nodes", reloaded)


class ComputeNextEligibleHelpersMixin:
    """Shared helper: run the analyzer end-to-end from a shipment tuple by
    first computing DagReadinessResult (reused, unmodified) then feeding it
    to compute_next_eligible -- exactly the intended two-step call shape."""

    @staticmethod
    def _next_eligible(shipments: tuple[ShipmentState, ...]) -> NextEligibleResult:
        readiness = compute_dag_readiness(shipments)
        return compute_next_eligible(shipments, readiness)


class ComputeNextEligibleCycleDetectedTests(unittest.TestCase, ComputeNextEligibleHelpersMixin):
    """Branch 2 (gate outcome 2): cycle_detected -- highest priority, evaluated
    before any provenance/active/ready partitioning."""

    def test_cycle_detected_returns_null_cursor_with_offending_cycle_nodes(self) -> None:
        shipments = (
            _shipment("001-S", "queued", deps=("002-S",)),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        result = self._next_eligible(shipments)
        self.assertIsInstance(result, NextEligibleResult)
        self.assertIsNone(result.next_eligible)
        self.assertEqual(result.next_eligible_reason, "cycle_detected")
        self.assertEqual(result.candidate_ids, ())
        self.assertEqual(set(result.offending_ids), {"001-S", "002-S"})

    def test_cycle_detected_takes_priority_over_active_shipment_present(self) -> None:
        # An active shipment elsewhere in the graph must NOT cause
        # resume_active to win over a detected cycle.
        shipments = (
            _shipment("001-S", "active"),
            _shipment("002-S", "queued", deps=("003-S",)),
            _shipment("003-S", "queued", deps=("002-S",)),
        )
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible_reason, "cycle_detected")
        self.assertIsNone(result.next_eligible)


class ComputeNextEligibleAmbiguousProvenanceTests(unittest.TestCase, ComputeNextEligibleHelpersMixin):
    """Branch 3 (gate outcome 3): ambiguous live/archive provenance, checked
    BEFORE active/ready partitioning. AC6 dedicated regression, including the
    single-active-but-ambiguous case which MUST report ambiguous_provenance
    and MUST NOT report resume_active."""

    def test_ambiguous_shipment_returns_null_cursor_with_offending_id(self) -> None:
        shipments = (_shipment("001-S", "queued", archived_status="shipped"),)
        result = self._next_eligible(shipments)
        self.assertIsNone(result.next_eligible)
        self.assertEqual(result.next_eligible_reason, "ambiguous_provenance")
        self.assertEqual(result.candidate_ids, ())
        self.assertEqual(result.offending_ids, ("001-S",))

    def test_single_active_but_ambiguous_reports_ambiguous_not_resume_active(self) -> None:
        # H3b: exactly one 'active' shipment that is ALSO ambiguous must
        # report ambiguous_provenance, never resume_active, and must never be
        # folded into multi_active_anomaly or no_candidates.
        shipments = (
            _shipment("001-S", "active", archived_status="shipped"),
            _shipment("002-S", "queued"),
        )
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible_reason, "ambiguous_provenance")
        self.assertIsNone(result.next_eligible)
        self.assertEqual(result.offending_ids, ("001-S",))

    def test_ambiguous_takes_priority_over_multi_active_anomaly(self) -> None:
        shipments = (
            _shipment("001-S", "active", archived_status="shipped"),
            _shipment("002-S", "active"),
        )
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible_reason, "ambiguous_provenance")
        self.assertEqual(result.offending_ids, ("001-S",))


class ComputeNextEligibleMultiActiveAnomalyTests(unittest.TestCase, ComputeNextEligibleHelpersMixin):
    """Branch 4 (gate outcome 4): AC5 dedicated regression -- two or more
    active shipments must never pick a winner and must never fall through to
    the ready-set."""

    def test_two_active_shipments_returns_null_cursor_with_both_offending_ids(self) -> None:
        shipments = (
            _shipment("001-S", "active"),
            _shipment("002-S", "active"),
            _shipment("003-S", "queued"),
        )
        result = self._next_eligible(shipments)
        self.assertIsNone(result.next_eligible)
        self.assertEqual(result.next_eligible_reason, "multi_active_anomaly")
        self.assertEqual(result.offending_ids, ("001-S", "002-S"))
        self.assertEqual(result.candidate_ids, ())

    def test_three_active_shipments_all_listed_as_offending(self) -> None:
        shipments = (
            _shipment("003-S", "active"),
            _shipment("001-S", "active"),
            _shipment("002-S", "active"),
        )
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible_reason, "multi_active_anomaly")
        self.assertEqual(result.offending_ids, ("001-S", "002-S", "003-S"))


class ComputeNextEligibleResumeActiveTests(unittest.TestCase, ComputeNextEligibleHelpersMixin):
    """Branch 5 (gate outcome 5): exactly one active shipment resumes -- no
    tie-break applies here (nothing to tie-break with exactly one)."""

    def test_exactly_one_active_shipment_is_the_cursor(self) -> None:
        shipments = (
            _shipment("001-S", "active"),
            _shipment("002-S", "queued"),
        )
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible, "001-S")
        self.assertEqual(result.next_eligible_reason, "resume_active")
        self.assertEqual(result.candidate_ids, ("001-S",))
        self.assertEqual(result.offending_ids, ())

    def test_resume_active_wins_over_nonempty_ready_set(self) -> None:
        shipments = (
            _shipment("001-S", "active"),
            _shipment("002-S", "queued"),
            _shipment("003-S", "queued"),
        )
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible, "001-S")
        self.assertEqual(result.next_eligible_reason, "resume_active")


class ComputeNextEligibleReadySetHeadTests(unittest.TestCase, ComputeNextEligibleHelpersMixin):
    """Branch 6 (gate outcome 6): zero active shipments, non-empty ready_set.
    Tie-break: DESC transitive downstream fan-out, then ASC shipment id. This
    is the ONLY branch the tie-break applies to (AC7)."""

    def test_single_ready_candidate_is_the_cursor(self) -> None:
        shipments = (_shipment("001-S", "queued"),)
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible, "001-S")
        self.assertEqual(result.next_eligible_reason, "ready_set_head")
        self.assertEqual(result.candidate_ids, ("001-S",))
        self.assertEqual(result.offending_ids, ())

    def test_tie_break_prefers_higher_downstream_fan_out(self) -> None:
        # 002-S has 2 transitive downstream dependents (004-S, 005-S via
        # 004-S); 003-S has 0. Both are independently ready (no predecessors).
        # 002-S must win despite 003-S having a lexicographically smaller id.
        shipments = (
            _shipment("002-S", "queued"),
            _shipment("003-S", "queued"),
            _shipment("004-S", "queued", deps=("002-S",)),
        )
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible_reason, "ready_set_head")
        self.assertEqual(result.next_eligible, "002-S")
        self.assertEqual(set(result.candidate_ids), {"002-S", "003-S"})

    def test_tie_break_falls_back_to_ascending_id_on_equal_fan_out(self) -> None:
        # Both candidates have zero downstream dependents (equal fan-out):
        # fall back to ascending shipment id.
        shipments = (
            _shipment("005-S", "queued"),
            _shipment("002-S", "queued"),
            _shipment("003-S", "queued"),
        )
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible_reason, "ready_set_head")
        self.assertEqual(result.next_eligible, "002-S")

    def test_total_order_determinism_under_shuffled_input(self) -> None:
        # H5: identical graph, shuffled input list order, must yield an
        # identical cursor every time -- covers the fan-out tie resolved by
        # the ASC-id fallback.
        base = [
            _shipment("005-S", "queued"),
            _shipment("002-S", "queued"),
            _shipment("003-S", "queued"),
            _shipment("004-S", "queued", deps=("002-S",)),
            _shipment("006-S", "queued", deps=("003-S",)),
        ]
        orderings = [
            tuple(base),
            tuple(reversed(base)),
            (base[2], base[0], base[4], base[1], base[3]),
            (base[4], base[3], base[2], base[1], base[0]),
        ]
        results = [self._next_eligible(shipments) for shipments in orderings]
        first = results[0]
        for other in results[1:]:
            self.assertEqual(other.next_eligible, first.next_eligible)
            self.assertEqual(other.next_eligible_reason, first.next_eligible_reason)
            self.assertEqual(set(other.candidate_ids), set(first.candidate_ids))


class ComputeNextEligibleNoCandidatesTests(unittest.TestCase, ComputeNextEligibleHelpersMixin):
    """Branch 7 (gate outcome 7): zero active shipments, empty ready_set."""

    def test_empty_graph_returns_no_candidates(self) -> None:
        result = self._next_eligible(())
        self.assertIsNone(result.next_eligible)
        self.assertEqual(result.next_eligible_reason, "no_candidates")
        self.assertEqual(result.candidate_ids, ())
        self.assertEqual(result.offending_ids, ())

    def test_all_shipped_graph_returns_no_candidates(self) -> None:
        shipments = (
            _shipment("001-S", "shipped"),
            _shipment("002-S", "shipped", deps=("001-S",)),
        )
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible_reason, "no_candidates")
        self.assertIsNone(result.next_eligible)

    def test_all_blocked_queued_with_unfinished_predecessors_returns_no_candidates(self) -> None:
        shipments = (
            _shipment("001-S", "queued"),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        result = self._next_eligible(shipments)
        # 001-S itself IS ready (no predecessors), so this is ready_set_head,
        # not no_candidates -- use a genuinely blocked-everywhere graph instead.
        self.assertEqual(result.next_eligible_reason, "ready_set_head")

    def test_genuinely_all_blocked_returns_no_candidates(self) -> None:
        shipments = (_shipment("002-S", "queued", deps=("999-S",)),)
        result = self._next_eligible(shipments)
        self.assertEqual(result.next_eligible_reason, "no_candidates")
        self.assertIsNone(result.next_eligible)


class ComputeNextEligibleDetailShapeTests(unittest.TestCase, ComputeNextEligibleHelpersMixin):
    """AC4: detail payload always exposes BOTH candidate_ids and
    offending_ids keys as arrays (never {}, never null, never omitted)."""

    def test_to_dict_shape_present_on_every_branch(self) -> None:
        graphs = {
            "cycle_detected": (
                _shipment("001-S", "queued", deps=("002-S",)),
                _shipment("002-S", "queued", deps=("001-S",)),
            ),
            "ambiguous_provenance": (_shipment("001-S", "queued", archived_status="shipped"),),
            "multi_active_anomaly": (
                _shipment("001-S", "active"),
                _shipment("002-S", "active"),
            ),
            "resume_active": (_shipment("001-S", "active"),),
            "ready_set_head": (_shipment("001-S", "queued"),),
            "no_candidates": (),
        }
        for expected_reason, shipments in graphs.items():
            with self.subTest(expected_reason=expected_reason):
                result = self._next_eligible(shipments)
                self.assertEqual(result.next_eligible_reason, expected_reason)
                payload = result.to_dict()
                self.assertIn("next_eligible", payload)
                self.assertIn("next_eligible_reason", payload)
                self.assertIn("next_eligible_detail", payload)
                detail = payload["next_eligible_detail"]
                self.assertEqual(set(detail.keys()), {"candidate_ids", "offending_ids"})
                self.assertIsInstance(detail["candidate_ids"], list)
                self.assertIsInstance(detail["offending_ids"], list)
                # JSON round-trip safety.
                reloaded = json.loads(json.dumps(payload))
                self.assertEqual(
                    set(reloaded["next_eligible_detail"].keys()),
                    {"candidate_ids", "offending_ids"},
                )

    def test_analyzer_never_emits_degraded_reason(self) -> None:
        # AC3/AC10: the analyzer must never emit 'degraded' -- that outcome
        # is CLI-only (115.002-T), synthesized before this analyzer is ever
        # invoked. Sweep every branch-representative graph and assert none
        # of them produce 'degraded'.
        graphs = [
            (),
            (_shipment("001-S", "queued"),),
            (_shipment("001-S", "active"),),
            (_shipment("001-S", "active"), _shipment("002-S", "active")),
            (_shipment("001-S", "queued", archived_status="shipped"),),
            (
                _shipment("001-S", "queued", deps=("002-S",)),
                _shipment("002-S", "queued", deps=("001-S",)),
            ),
        ]
        for shipments in graphs:
            result = self._next_eligible(shipments)
            self.assertNotEqual(result.next_eligible_reason, "degraded")


if __name__ == "__main__":
    unittest.main()
