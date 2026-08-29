"""Assembler tests for pre-review detector DAG evaluation (149.005-T / 149.010-T)."""

from __future__ import annotations

import unittest

from autoharness.detectors.contract import (
    ApplicabilitySpec,
    Evidence,
    NodeResult,
    NodeSpec,
    ProducerSpec,
    RemediationSpec,
    ValidatorSpec,
)
from autoharness.detectors import applicability as applicability_mod
from autoharness.detectors.assembler import assemble_detector_results


class AssemblerTests(unittest.TestCase):
    def _node(
        self,
        node_id: str,
        *,
        depends_on=(),
        produce=None,
        validate=None,
    ) -> NodeSpec:
        detector_id = node_id.split('/')[1].split('@')[0]
        if produce is None:
            produce = lambda node, _context: Evidence(node.node_id, {"node": node.node_id})
        if validate is None:
            validate = lambda node, _evidence_map, _context: NodeResult(name=node.node_id, status="passed")
        return NodeSpec(
            node_id=node_id,
            domain="D-ART",
            detector_id=detector_id,
            version="1",
            applies_when=ApplicabilitySpec(always=True),
            producer=ProducerSpec(kind="pure", ref="autoharness.detectors.art.section_markers:produce", handler=produce),
            validator=ValidatorSpec(ref="autoharness.detectors.art.section_markers:validate", handler=validate),
            depends_on=tuple(depends_on),
            severity="medium",
            remediation=RemediationSpec(class_name="guided_fix", authority="stage"),
        )

    def test_cycle_is_invalid_and_evaluates_zero_nodes(self) -> None:
        produced = []

        def produce(node, _context):
            produced.append(node.node_id)
            return Evidence(node.node_id, {})

        nodes = (
            self._node("det:D-ART/ART-01@1", depends_on=("det:D-ART/ART-02@1",), produce=produce),
            self._node("det:D-ART/ART-02@1", depends_on=("det:D-ART/ART-01@1",), produce=produce),
        )

        result = assemble_detector_results(nodes, context=object())

        self.assertEqual(result.exit_code, 2)
        self.assertEqual(result.evaluated_count, 0)
        self.assertEqual(result.results, ())
        self.assertEqual(result.cycle_nodes, ("det:D-ART/ART-01@1", "det:D-ART/ART-02@1"))
        self.assertEqual(produced, [])

    def test_upstream_failed_or_insufficient_evidence_blocks_downstream(self) -> None:
        downstream_produced = []

        def downstream_producer(node, _context):
            downstream_produced.append(node.node_id)
            return Evidence(node.node_id, {})

        upstream_failed = self._node(
            "det:D-ART/ART-01@1",
            validate=lambda node, _evidence_map, _context: NodeResult(name=node.node_id, status="failed"),
        )
        downstream = self._node(
            "det:D-ART/ART-02@1",
            depends_on=("det:D-ART/ART-01@1",),
            produce=downstream_producer,
        )
        failed_result = assemble_detector_results((upstream_failed, downstream), context=object())
        self.assertEqual([item.status for item in failed_result.results], ["failed", "blocked_upstream"])
        self.assertEqual(downstream_produced, [])

        def raising_producer(node, _context):
            raise RuntimeError(f"{node.node_id} unavailable")

        upstream_insufficient = self._node("det:D-ART/ART-03@1", produce=raising_producer)
        downstream_again = self._node(
            "det:D-ART/ART-04@1",
            depends_on=("det:D-ART/ART-03@1",),
            produce=downstream_producer,
        )
        insufficient_result = assemble_detector_results((upstream_insufficient, downstream_again), context=object())
        self.assertEqual(
            [item.status for item in insufficient_result.results],
            ["insufficient_evidence", "blocked_upstream"],
        )
        self.assertIn("det:D-ART/ART-03@1 unavailable", insufficient_result.results[0].message)
        self.assertEqual(downstream_produced, [])


if __name__ == "__main__":
    unittest.main()
