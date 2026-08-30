"""In-memory detector DAG assembly and evaluation."""

from __future__ import annotations

import json
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


def _is_json_serializable(value: Any) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    return True


def _has_malformed_result_payload(result: NodeResult) -> bool:
    """Return ``True`` when ``result``'s SDK-contract fields cannot be
    safely consumed by every downstream consumer of a ``NodeResult``.

    A prior check here only ran ``result.details``/``result.provenance``
    through ``json.dumps`` in isolation. That is necessary but not
    sufficient: ``detectors/report.py``'s ``_merged_provenance`` calls
    ``dict(result.provenance)`` on every result, and a JSON-serializable but
    non-mapping value (e.g. a plain ``list`` such as ``["x"]``) passes
    ``json.dumps`` yet still raises there (``dict()`` requires either a
    mapping or an iterable of key/value pairs). ``details``/``provenance``
    are also typed as ``dict[str, Any]`` on ``NodeResult`` itself, but that
    type hint is not runtime-enforced -- a detector can still construct one
    with any object. Likewise, ``message``/``token`` are typed ``str``/``str
    | None`` but are not runtime-checked either, so a non-JSON-serializable
    object assigned to either would still reach ``json.dumps(payload)`` in
    ``emit_pre_review_report`` uncaught. Check both facets: the two fields
    consumed as mappings must actually be ``dict`` instances, and the
    complete ``to_dict()`` payload -- covering every field, not only
    ``details``/``provenance`` -- must round-trip through ``json.dumps``.
    """
    if not isinstance(result.details, dict) or not isinstance(result.provenance, dict):
        return True
    return not _is_json_serializable(result.to_dict())


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
                    if isinstance(result, NodeResult) and result.name == node.node_id and result.status == "waived":
                        # `waived` is a reserved status in the S1 contract: waiver
                        # authority belongs exclusively to the audited waiver
                        # engine planned for S10, which does not exist yet. A
                        # detector implementation returning `status="waived"`
                        # directly would let it mint an unaudited waiver -- treat
                        # this as a hard SDK contract violation (status
                        # "invalid"), symmetric with the type/identity checks
                        # below, rather than letting an unreachable-in-S1 status
                        # silently pass through as a legitimate result.
                        result = NodeResult(
                            name=node.node_id,
                            status="invalid",
                            token="INVALID",
                            message=(
                                f"validator for {node.node_id} returned status 'waived', but waiver "
                                "authority is reserved for the S10 audited waiver engine and 'waived' "
                                "must remain unreachable until that engine exists"
                            ),
                        )
                    elif not isinstance(result, NodeResult) or result.name != node.node_id:
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
                    elif _has_malformed_result_payload(result):
                        # The report emitter (`emit_pre_review_report`)
                        # serializes every result's complete payload via
                        # `json.dumps`, and `report.py`'s `_merged_provenance`
                        # additionally calls `dict(result.provenance)` on
                        # every result. A validator returning a structurally
                        # valid `NodeResult` whose `details`/`provenance` is
                        # not an actual mapping (e.g. a `list`), or whose
                        # `details`/`provenance`/`message`/`token` contains a
                        # non-JSON value (e.g. a `Path` or `set`), would
                        # otherwise pass this SDK boundary silently, only to
                        # raise an uncaught exception later during report
                        # emission -- bypassing both this boundary's own
                        # `invalid`-result handling and the report's
                        # `publication_failed` path. Validate the full
                        # payload shape here, at the same SDK boundary as the
                        # other contract checks, and convert to `invalid`
                        # before the malformed payload can reach emission.
                        result = NodeResult(
                            name=node.node_id,
                            status="invalid",
                            token="INVALID",
                            message=(
                                f"validator for {node.node_id} returned a NodeResult with a "
                                "malformed or non-JSON-serializable details/provenance/message/token payload"
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
