"""In-memory detector DAG assembly and evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from autoharness.detectors.applicability import evaluate_node_applicability
from autoharness.detectors.contract import Evidence, NodeResult, NodeSpec, status_exit_code, topological_order_or_cycle

_BLOCKING_UPSTREAM_STATUSES = frozenset({
    "failed",
    "insufficient_evidence",
    "blocked_upstream",
    "invalid",
    "not_applicable",
    "skipped",
    "waived",
})


@dataclass(frozen=True)
class DetectorAssemblyResult:
    results: tuple[NodeResult, ...] = ()
    exit_code: int = 0
    cycle_nodes: tuple[str, ...] = ()
    evaluated_count: int = 0
    evaluation_order: tuple[str, ...] = ()

    @property
    def invalid(self) -> bool:
        return self.exit_code == 2


def _blocked_result(node: NodeSpec, blocked_by: str, status: str) -> NodeResult:
    return NodeResult(
        name=node.node_id,
        status="blocked_upstream",
        token="BLOCKED_UPSTREAM",
        message=f"blocked by upstream {blocked_by} ({status})",
        details={"blocked_by": blocked_by, "blocked_status": status},
    )


def assemble_detector_results(
    nodes: tuple[NodeSpec, ...] | list[NodeSpec],
    context: Any,
) -> DetectorAssemblyResult:
    ordered_ids, cycle_nodes = topological_order_or_cycle(nodes)
    if cycle_nodes:
        return DetectorAssemblyResult(exit_code=2, cycle_nodes=cycle_nodes)

    node_map = {node.node_id: node for node in nodes}
    results: list[NodeResult] = []
    result_map: dict[str, NodeResult] = {}
    evidence_map: dict[str, Evidence] = {}
    evaluated_count = 0

    for node_id in ordered_ids:
        node = node_map[node_id]
        for dependency in node.depends_on:
            dependency_result = result_map[dependency]
            if dependency_result.status in _BLOCKING_UPSTREAM_STATUSES:
                blocked = _blocked_result(node, dependency, dependency_result.status)
                results.append(blocked)
                result_map[node_id] = blocked
                break
        else:
            applicability_result = evaluate_node_applicability(node, context)
            if applicability_result is not None:
                results.append(applicability_result)
                result_map[node_id] = applicability_result
                continue
            try:
                if node.producer.handler is None:
                    raise RuntimeError("producer handler is unavailable")
                evidence = node.producer.handler(node, context)
                if not isinstance(evidence, Evidence) or evidence.node_id != node.node_id:
                    # The producer SDK contract requires an `Evidence` for
                    # this exact node. A producer that returns `None`,
                    # another type, or `Evidence` addressed to a different
                    # node could otherwise still reach a validator -- and
                    # even yield a `passed` result -- despite an SDK
                    # contract violation being silently misattributed.
                    # Treat this as a hard SDK contract violation (status
                    # "invalid"), the same status already synthesized below
                    # for malformed validator output, without ever calling
                    # the validator on untrustworthy evidence.
                    if isinstance(evidence, Evidence):
                        got_desc = f"Evidence for node {evidence.node_id!r}"
                    else:
                        got_desc = repr(type(evidence).__name__)
                    result = NodeResult(
                        name=node.node_id,
                        status="invalid",
                        token="INVALID",
                        message=(
                            f"producer for {node.node_id} returned {got_desc} "
                            "instead of Evidence for this node"
                        ),
                    )
                else:
                    evidence_map[node_id] = evidence
                    if node.validator.handler is None:
                        raise RuntimeError("validator handler is unavailable")
                    # The validator always sees its own node's just-produced evidence,
                    # plus exactly the sibling evidence it declared via `consumes` (the
                    # registry loader enforces `consumes ⊆ depends_on`, so every
                    # declared sibling is guaranteed to already be in evidence_map with
                    # a non-blocking status by this point). Never expose the entire
                    # accumulated evidence_map: an undeclared sibling must not be
                    # silently visible just because it happens to sort earlier.
                    visible_evidence = {node_id: evidence}
                    for consumed in node.validator.consumes:
                        if consumed in evidence_map:
                            visible_evidence[consumed] = evidence_map[consumed]
                    result = node.validator.handler(node, MappingProxyType(visible_evidence), context)
                    if not isinstance(result, NodeResult) or result.name != node.node_id:
                        # The validator SDK contract requires a `NodeResult`
                        # for this exact node. A detector implementation that
                        # returns `None`/another type, or a `NodeResult`
                        # addressed to a different node's `name` (e.g. a
                        # copy-paste bug), would otherwise crash later during
                        # serialization/downstream dependency-status handling
                        # -- or worse, be recorded under the current
                        # dependency key while serializing a different name,
                        # yielding a misattributed report and allowing
                        # downstream nodes to proceed on a bogus "clean"
                        # status. Treat this as a hard SDK contract violation
                        # (status "invalid", the same status a detector can
                        # legitimately return for its own invalid-input
                        # findings) -- symmetric with the producer's own
                        # node_id check above -- rather than letting it
                        # propagate as an uncaught exception or a silent
                        # misattribution.
                        if isinstance(result, NodeResult):
                            got_desc = f"NodeResult for node {result.name!r}"
                        else:
                            got_desc = repr(type(result).__name__)
                        result = NodeResult(
                            name=node.node_id,
                            status="invalid",
                            token="INVALID",
                            message=(
                                f"validator for {node.node_id} returned {got_desc} "
                                "instead of a NodeResult for this node"
                            ),
                        )
            except Exception as exc:
                result = NodeResult(
                    name=node.node_id,
                    status="insufficient_evidence",
                    token="INSUFFICIENT_EVIDENCE",
                    message=str(exc),
                )
            results.append(result)
            result_map[node_id] = result
            evaluated_count += 1

    return DetectorAssemblyResult(
        results=tuple(results),
        exit_code=2 if any(status_exit_code(result.status) != 0 for result in results) else 0,
        cycle_nodes=(),
        evaluated_count=evaluated_count,
        evaluation_order=ordered_ids,
    )
