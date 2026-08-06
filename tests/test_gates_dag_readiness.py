"""Deterministic tests for the read-only DAG readiness/critical-path/downstream-dependents
analyzer (110.001-T, 117-S).

This analyzer reuses the existing shipment-blocks reader (``ShipmentState`` /
``FilesystemTopologyReaders.list_shipments()`` from ``autoharness.gates.topology``)
for data access ONLY. Cycle detection is owned by this analyzer, not the reused
reader (see 110.001-T acceptance criteria 5).
"""

from __future__ import annotations

import unittest

from autoharness.gates.topology import (
    DagReadinessResult,
    ShipmentState,
    compute_dag_readiness,
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


if __name__ == "__main__":
    unittest.main()
