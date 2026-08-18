---
title: "Skipping only the direct violator in the topology gate's numeric-adjacency fallback leaves multi-hop reverse dependencies undetected (rule corrected 2026-08-18 — see supersession note)"
description: "_prior_shipment_id's implicit numeric-predecessor heuristic must disable itself for a target once a NUMERICALLY LOWER shipment declares that target as a dependency (a genuine reverse edge) -- not for ANY shipment regardless of direction, which is over-broad and wrongly suppresses the fallback for normal higher-numbered forward dependents too. A two-hop reverse chain (e.g. 141-S depends on 140-S depends on 139-S) still tripped a false BRANCH_MISMATCH/PRECLAIM block via the next-lower-numbered shipment; the ANY-direction fix that closed that gap introduced a new, opposite-direction false negative -- see the superseding residual-defect doc."
problem_type: "logic-bug"
category: "gate-correctness"
component: "pipeline-topology-gate"
root_cause: "The gate's _prior_shipment_id() picked the highest-numbered {N}-S strictly below the target as an implicit predecessor whenever no explicit predecessor existed. The first fix only excluded the shipment that was itself a direct explicit-dependency violator, but left the heuristic active for any other numerically-adjacent shipment — so a multi-hop reverse-dependency chain (target declared as a dependency of some other, non-adjacent shipment) could still trigger the fallback via a different, unrelated numerically-close shipment. The rule documented in this file's first version (disable for ANY declaring shipment, regardless of numeric direction) was itself later found to be over-broad -- see Supersession Note below."
resolution_type: "fix"
severity: "medium"
tags:
  - "ship"
  - "pipeline-topology"
  - "gate-correctness"
  - "shipment-dependencies"
  - "code-review-caught"
  - "superseded-partially"
citations:
  - "PR #357 (second Copilot review round)"
  - "src/autoharness/gates/topology.py::_prior_shipment_id"
  - "tests/test_gates_topology.py::ImplicitNumericPredecessorTests::test_multi_hop_reverse_dependency_disables_fallback_entirely_not_just_the_violator"
  - "Shipment 139-S"
  - "docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md (supersedes the rule below)"
---

# Multi-Hop Reverse Dependency Must Disable the Entire Fallback, Not Just Skip the Violator

## Supersession note (added during 139-S post-merge closure, 2026-08-18)

**The "rule that should have been followed" section below, as originally
written, is itself over-broad and must NOT be applied literally.** A
post-merge closure adversarial review found that disabling the fallback for
*any* shipment declaring the target as a dependency — regardless of numeric
direction — also wrongly suppresses the fallback when a numerically
**higher** shipment declares a completely normal forward dependency on the
target (e.g. `113-S depends on 112-S`, evaluating target `112-S`). That is
not a reverse-edge anomaly at all, and the correct predicate requires the
declaring shipment to be numerically **lower** than the target. See
`docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`
for the full repro, corrected diff, and current (as of 2026-08-18, still
**unfixed on `main`**) status. Read the code example and "rule" below as
historical context for the multi-hop lesson only — do not copy the
`any(...)` predicate as-is into new code.

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

**This session's own second-pass fix repeated the same class of mistake in
the opposite direction**: replacing "is this specific candidate the
violator" with "does *any* relationship at all exist" is *also* wrong — it
needed the precise directional predicate (numerically lower AND an explicit
dependency on target) the whole time. See the Supersession Note above.

## The rule that should have been followed instead (SUPERSEDED — see note above; kept for historical context only)

**~~Once any explicit reverse-dependency edge exists for a target shipment
anywhere in the full shipment set, disable the entire numeric-adjacency
fallback for that target — do not merely exclude the one shipment that
happens to violate it.~~ Corrected rule: only when a NUMERICALLY LOWER
shipment explicitly declares the target as its own dependency** (a genuine
reverse edge — the lower-numbered shipment is blocked by the
higher-numbered target, the opposite of what numeric adjacency assumes).
Concretely:

```python
# SUPERSEDED / INCORRECT — do not use as-is (over-broad, see note above):
if any(target in s.blocking_predecessor_ids for s in shipments):
    return None

# CORRECTED — restrict to numerically lower dependents:
for s in shipments:
    other = re.match(r"^(\d+)-S$", s.shipment_id)
    if not other or int(other.group(1)) >= target_num:
        continue
    if target in s.blocking_predecessor_ids:
        return None
```


This must run *before* any numeric-adjacency selection logic, and it must
scan the *entire* shipment set, not just a locally-scoped candidate list.
The mere existence of one explicit reverse (numerically-lower) edge is
proof the ordering is intentionally declared, so guessing via numeric
adjacency is never safe for that target again, regardless of which other
shipment would have been guessed. **A forward (numerically-higher) edge is
not such proof — see the Supersession Note above.**

## Applicability

Any "infer an implicit relationship when no explicit one exists" fallback
heuristic (dependency ordering, predecessor/successor inference, adjacency
guessing) must be gated on the *precise* directional predicate that makes a
declared edge anomalous relative to the heuristic's own assumption — not on
"is this specific candidate the one causing the problem in front of me,"
but *also* not on "does any relationship at all exist for this target,"
which this file's own first-pass correction wrongly settled on. Both
framings are bug magnets in opposite directions: the first treats symptoms
name-by-name instead of the underlying invariant; the second overcorrects
into disabling a heuristic for perfectly normal relationships that say
nothing about the anomaly being guarded against. Get the exact predicate
right (here: "numerically lower AND explicitly depends on target") and test
both the too-narrow and too-broad boundary cases explicitly — as
`docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`'s
regression test now does for the too-broad case this file's original
version missed.
