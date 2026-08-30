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
        consumes=(),
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
            validator=ValidatorSpec(ref="autoharness.detectors.art.section_markers:validate", handler=validate, consumes=tuple(consumes)),
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

    def test_validator_evidence_view_is_restricted_to_self_and_declared_consumes(self) -> None:
        # Three producers run: ART-01, ART-02 (both upstream, no relation to each
        # other), and ART-03 which depends_on + consumes only ART-01. ART-03's
        # validator must see its own evidence and ART-01's, but never ART-02's
        # (Copilot-2: `consumes` must actually restrict the visible evidence map,
        # not just be a schema-only hint while the full accumulated map leaks
        # through).
        seen_keys = []

        def capturing_validate(node, evidence_map, _context):
            seen_keys.append(frozenset(evidence_map.keys()))
            return NodeResult(name=node.node_id, status="passed")

        upstream_one = self._node("det:D-ART/ART-01@1")
        upstream_two = self._node("det:D-ART/ART-02@1")
        downstream = self._node(
            "det:D-ART/ART-03@1",
            depends_on=("det:D-ART/ART-01@1",),
            consumes=("det:D-ART/ART-01@1",),
            validate=capturing_validate,
        )

        result = assemble_detector_results(
            (upstream_one, upstream_two, downstream), context=object()
        )

        self.assertEqual([item.status for item in result.results], ["passed", "passed", "passed"])
        downstream_view = seen_keys[-1]
        self.assertEqual(downstream_view, {"det:D-ART/ART-03@1", "det:D-ART/ART-01@1"})
        self.assertNotIn("det:D-ART/ART-02@1", downstream_view)

    def test_exit_code_reflects_a_node_result_status_of_invalid(self) -> None:
        # `status_exit_code("invalid") == 2`, but the assembler previously
        # hard-coded `exit_code=0` regardless of individual node statuses --
        # a legitimately-returned `status="invalid"` result was silently
        # reported as an overall success. The exit code must now be derived
        # from the canonical per-result mapping.
        invalid_node = self._node(
            "det:D-ART/ART-01@1",
            validate=lambda node, _evidence_map, _context: NodeResult(
                name=node.node_id, status="invalid", token="INVALID", message="bad input"
            ),
        )
        result = assemble_detector_results((invalid_node,), context=object())
        self.assertEqual(result.results[0].status, "invalid")
        self.assertEqual(result.exit_code, 2)
        self.assertFalse(result.cycle_nodes)

    def test_validator_returning_non_node_result_is_converted_to_invalid_not_crashed(self) -> None:
        # The validator SDK contract requires a `NodeResult`. A detector
        # implementation bug that instead returns `None` (or any other type)
        # must never crash serialization/downstream dependency handling --
        # it is converted to a synthesized `status="invalid"` NodeResult, and
        # the overall exit code reflects that failure.
        malformed_node = self._node(
            "det:D-ART/ART-01@1",
            validate=lambda node, _evidence_map, _context: None,
        )
        downstream = self._node(
            "det:D-ART/ART-02@1",
            depends_on=("det:D-ART/ART-01@1",),
        )
        result = assemble_detector_results((malformed_node, downstream), context=object())
        self.assertEqual(result.results[0].status, "invalid")
        self.assertIsInstance(result.results[0], NodeResult)
        self.assertIn("NoneType", result.results[0].message)
        # The malformed result is still treated as blocking for downstream
        # dependents, exactly like any other non-clean upstream status.
        self.assertEqual(result.results[1].status, "blocked_upstream")
        self.assertEqual(result.exit_code, 2)

    def test_producer_returning_non_evidence_is_converted_to_invalid_without_calling_validator(self) -> None:
        # Copilot review finding (PR #420): the producer output was stored
        # without enforcing the declared `Evidence` contract. A producer
        # that returns `None`, another type, or `Evidence` for a different
        # node must never reach the validator (where it could even yield a
        # false `passed`) -- it must be converted to a synthesized
        # `status="invalid"` NodeResult, exactly like malformed validator
        # output is already handled.
        validator_calls = []

        def recording_validate(node, _evidence_map, _context):
            validator_calls.append(node.node_id)
            return NodeResult(name=node.node_id, status="passed")

        malformed_node = self._node(
            "det:D-ART/ART-01@1",
            produce=lambda node, _context: None,
            validate=recording_validate,
        )
        downstream = self._node(
            "det:D-ART/ART-02@1",
            depends_on=("det:D-ART/ART-01@1",),
        )
        result = assemble_detector_results((malformed_node, downstream), context=object())
        self.assertEqual(result.results[0].status, "invalid")
        self.assertIn("NoneType", result.results[0].message)
        self.assertEqual(validator_calls, [], "the validator must never be called with untrustworthy evidence")
        self.assertEqual(result.results[1].status, "blocked_upstream")
        self.assertEqual(result.exit_code, 2)

    def test_producer_returning_evidence_for_wrong_node_is_converted_to_invalid(self) -> None:
        # A producer returning `Evidence` addressed to a *different* node_id
        # (e.g. a copy-paste bug) must be rejected the same way as a
        # completely wrong type -- the node_id mismatch is itself an SDK
        # contract violation, not merely an unusual-but-valid payload.
        validator_calls = []

        def recording_validate(node, _evidence_map, _context):
            validator_calls.append(node.node_id)
            return NodeResult(name=node.node_id, status="passed")

        mismatched_node = self._node(
            "det:D-ART/ART-01@1",
            produce=lambda node, _context: Evidence("det:D-ART/ART-99@1", {"node": "wrong"}),
            validate=recording_validate,
        )
        result = assemble_detector_results((mismatched_node,), context=object())
        self.assertEqual(result.results[0].status, "invalid")
        self.assertIn("ART-99", result.results[0].message)
        self.assertEqual(validator_calls, [])
        self.assertEqual(result.exit_code, 2)

    def test_validator_returning_wrong_node_name_is_converted_to_invalid(self) -> None:
        # Copilot review finding (PR #420): the validator contract was
        # checked only by type, not by node identity. A validator returning
        # `NodeResult(name="another-node", status="passed")` would
        # otherwise be recorded under the current dependency key while
        # serializing a *different* name, yielding a misattributed report
        # and letting downstream nodes proceed on a bogus clean status.
        # Require `result.name == node.node_id`, symmetric with the
        # producer's own node_id check.
        wrong_name_node = self._node(
            "det:D-ART/ART-01@1",
            validate=lambda node, _evidence_map, _context: NodeResult(name="det:D-ART/ART-99@1", status="passed"),
        )
        downstream = self._node(
            "det:D-ART/ART-02@1",
            depends_on=("det:D-ART/ART-01@1",),
        )
        result = assemble_detector_results((wrong_name_node, downstream), context=object())
        self.assertEqual(result.results[0].status, "invalid")
        self.assertIn("ART-99", result.results[0].message)
        self.assertEqual(result.results[1].status, "blocked_upstream")
        self.assertEqual(result.exit_code, 2)

    def test_validator_returning_waived_is_converted_to_invalid(self) -> None:
        # Copilot review finding (PR #420, round 6): `status="waived"` is a
        # reserved status -- waiver authority belongs exclusively to the
        # audited waiver engine planned for S10, which does not exist yet.
        # A detector implementation directly returning
        # `NodeResult(status="waived")` must never be accepted as a
        # legitimate result in S1; it is converted to `status="invalid"`,
        # symmetric with the type/identity checks above, and downstream
        # nodes must see it as blocking exactly like any other non-clean
        # upstream status.
        waiving_node = self._node(
            "det:D-ART/ART-01@1",
            validate=lambda node, _evidence_map, _context: NodeResult(name=node.node_id, status="waived"),
        )
        downstream = self._node(
            "det:D-ART/ART-02@1",
            depends_on=("det:D-ART/ART-01@1",),
        )
        result = assemble_detector_results((waiving_node, downstream), context=object())
        self.assertEqual(result.results[0].status, "invalid")
        self.assertIn("waived", result.results[0].message.lower())
        self.assertIn("S10", result.results[0].message)
        self.assertEqual(result.results[1].status, "blocked_upstream")
        self.assertEqual(result.exit_code, 2)

    def test_validator_returning_non_json_serializable_details_is_converted_to_invalid(self) -> None:
        # Copilot review finding (PR #420, round 7): a validator may return
        # a structurally valid `NodeResult` whose `details`/`provenance`
        # contains a non-JSON value (e.g. a `Path`). This must never pass
        # the SDK boundary silently -- `emit_pre_review_report()` would
        # otherwise raise an uncaught `TypeError` from `json.dumps` later,
        # bypassing both the assembler's own `invalid`-result handling and
        # the report's `publication_failed` path.
        import pathlib

        non_serializable_node = self._node(
            "det:D-ART/ART-01@1",
            validate=lambda node, _evidence_map, _context: NodeResult(
                name=node.node_id,
                status="passed",
                details={"offending_path": pathlib.Path("some/path")},
            ),
        )
        result = assemble_detector_results((non_serializable_node,), context=object())
        self.assertEqual(result.results[0].status, "invalid")
        self.assertIn("json-serializable", result.results[0].message.lower())
        self.assertEqual(result.exit_code, 2)

    def test_validator_returning_non_json_serializable_provenance_is_converted_to_invalid(self) -> None:
        non_serializable_node = self._node(
            "det:D-ART/ART-01@1",
            validate=lambda node, _evidence_map, _context: NodeResult(
                name=node.node_id,
                status="passed",
                provenance={"tags": {"a", "b"}},
            ),
        )
        result = assemble_detector_results((non_serializable_node,), context=object())
        self.assertEqual(result.results[0].status, "invalid")
        self.assertIn("json-serializable", result.results[0].message.lower())
        self.assertEqual(result.exit_code, 2)


if __name__ == "__main__":
    unittest.main()
