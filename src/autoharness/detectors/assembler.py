"""In-memory detector DAG assembly and evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from autoharness.detectors.applicability import evaluate_node_applicability
from autoharness.detectors.contract import Evidence, NodeResult, NodeSpec

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


def _ordered_nodes(nodes: tuple[NodeSpec, ...] | list[NodeSpec]) -> list[NodeSpec]:
    return sorted(nodes, key=lambda node: node.node_id)


def _topological_order(nodes: tuple[NodeSpec, ...] | list[NodeSpec]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    node_map = {node.node_id: node for node in nodes}
    colors = {node_id: "white" for node_id in node_map}
    stack: list[str] = []
    order: list[str] = []

    def visit(node_id: str) -> tuple[str, ...] | None:
        colors[node_id] = "gray"
        stack.append(node_id)
        for dependency in sorted(node_map[node_id].depends_on):
            color = colors.get(dependency)
            if color == "gray":
                start = stack.index(dependency)
                return tuple(stack[start:])
            if color == "white":
                cycle = visit(dependency)
                if cycle is not None:
                    return cycle
        stack.pop()
        colors[node_id] = "black"
        order.append(node_id)
        return None

    for node in _ordered_nodes(tuple(node_map.values())):
        if colors[node.node_id] != "white":
            continue
        cycle = visit(node.node_id)
        if cycle is not None:
            return (), cycle
    return tuple(order), ()


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
    ordered_ids, cycle_nodes = _topological_order(nodes)
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
                evidence_map[node_id] = evidence
                if node.validator.handler is None:
                    raise RuntimeError("validator handler is unavailable")
                result = node.validator.handler(node, MappingProxyType(dict(evidence_map)), context)
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
        exit_code=0,
        cycle_nodes=(),
        evaluated_count=evaluated_count,
        evaluation_order=ordered_ids,
    )
