---
title: "Skipping only the direct violator in the topology gate's numeric-adjacency fallback leaves multi-hop reverse dependencies undetected"
description: "_prior_shipment_id's implicit numeric-predecessor heuristic must disable itself entirely for a target once ANY shipment declares that target as a dependency, not merely skip the shipment that is the direct violator; a two-hop reverse chain (e.g. 141-S depends on 140-S depends on 139-S) still tripped a false BRANCH_MISMATCH/PRECLAIM block via the next-lower-numbered shipment."
problem_type: "logic-bug"
category: "gate-correctness"
component: "pipeline-topology-gate"
root_cause: "The gate's _prior_shipment_id() picked the highest-numbered {N}-S strictly below the target as an implicit predecessor whenever no explicit predecessor existed. The first fix only excluded the shipment that was itself a direct explicit-dependency violator, but left the heuristic active for any other numerically-adjacent shipment — so a multi-hop reverse-dependency chain (target declared as a dependency of some other, non-adjacent shipment) could still trigger the fallback via a different, unrelated numerically-close shipment."
resolution_type: "fix"
severity: "medium"
tags:
  - "ship"
  - "pipeline-topology"
  - "gate-correctness"
  - "shipment-dependencies"
  - "code-review-caught"
citations:
  - "PR #357 (second Copilot review round)"
  - "src/autoharness/gates/topology.py::_prior_shipment_id"
  - "tests/test_gates_topology.py::ImplicitNumericPredecessorTests::test_multi_hop_reverse_dependency_disables_fallback_entirely_not_just_the_violator"
  - "Shipment 139-S"
---

# Multi-Hop Reverse Dependency Must Disable the Entire Fallback, Not Just Skip the Violator

## Context

`_prior_shipment_id()` in the pipeline-topology gate infers an implicit
predecessor shipment by numeric adjacency (`{N}-S` just below the target)
when no explicit `dependencies`/`blocking_predecessor_ids` edge exists. This
heuristic exists so gate checks still work for shipments that never declared
explicit predecessors. During 139-S's PR review, Copilot flagged that an
earlier same-session fix — which only special-cased skipping the shipment
that was *itself* the direct violator of an explicit reverse-dependency edge
— left a multi-hop gap: if shipment C declares A as a dependency, but B (a
different, numerically-adjacent-to-A shipment) is not part of that
declaration at all, the numeric-adjacency fallback would still fire using B
as A's implicit predecessor, even though A's true ordering is already fully
governed by the explicit C→A edge.

## The mistake

The first-pass fix effectively asked "is *this specific candidate* the
violator?" instead of "does *any* shipment in the whole set already declare
an explicit edge involving the target?" That framing is fragile: it patches
the one reproduction case a reviewer or test happens to name, but the
underlying heuristic keeps firing for every other numerically-adjacent
shipment that isn't the one being checked.

## The rule that should have been followed instead

**Once any explicit reverse-dependency edge exists for a target shipment
anywhere in the full shipment set, disable the entire numeric-adjacency
fallback for that target — do not merely exclude the one shipment that
happens to violate it.** Concretely:

```python
if any(target in s.blocking_predecessor_ids for s in shipments):
    return None  # explicit dependencies govern; do not guess numerically
```

This must run *before* any numeric-adjacency selection logic, and it must
scan the *entire* shipment set, not just a locally-scoped candidate list.
The mere existence of one explicit edge is proof the ordering is
intentionally declared, so guessing via numeric adjacency is never safe for
that target again, regardless of which other shipment would have been
guessed.

## Applicability

Any "infer an implicit relationship when no explicit one exists" fallback
heuristic (dependency ordering, predecessor/successor inference, adjacency
guessing) must be gated on "does an explicit relationship exist for this
target *anywhere* in the full data set" — not "is this specific candidate
the one causing the problem in front of me." The first framing is a bug
magnet: it invites future regressions each time a new adjacency case
surfaces, because it treats symptoms name-by-name instead of the underlying
invariant (explicit data always outranks inference for that entity, full
stop).
