---
title: "RESIDUAL DEFECT (unfixed on main): topology gate's reverse-edge suppression also wrongly disables the fallback for normal forward dependents"
description: "src/autoharness/gates/topology.py's _prior_shipment_id (merged in PR #357 / 139-S) disables the numeric-adjacency implicit-predecessor fallback whenever ANY shipment declares the target as a dependency, including a numerically HIGHER shipment in the normal forward-order case -- not just a genuine numerically-lower reverse-edge anomaly. A verified fix + regression test is included below but was deliberately NOT committed to main by this session (out of the 139-S bounded-stop scope and the post-merge-closure-branch scope); hand off to Stage for a proper fix task."
problem_type: "logic-bug"
category: "gate-correctness"
component: "pipeline-topology-gate"
root_cause: "The multi-hop fix landed in PR #357 (commit 0568f044) checked `any(target in shipment.blocking_predecessor_ids for shipment in shipments)` without restricting to shipments numerically LOWER than the target. A numerically HIGHER shipment declaring the target as its dependency (e.g. 113-S depends on 112-S) is the NORMAL forward-order case the numeric-adjacency heuristic is designed to support, not a reverse-edge anomaly -- it says nothing about whether the target itself has an undeclared implicit predecessor. The overly-broad check silently disables the fallback (and therefore silently ALLOWS claiming a shipment that should have been blocked by PREDECESSOR_NOT_SHIPPED) whenever any later shipment happens to have a normal forward dependency on it."
resolution_type: "fix-ready-not-applied"
severity: "high"
tags:
  - "ship"
  - "pipeline-topology"
  - "gate-correctness"
  - "shipment-dependencies"
  - "residual-defect"
  - "hand-off-to-stage"
citations:
  - "PR #357 (suppressed review comments, never resolved as threads)"
  - "src/autoharness/gates/topology.py::_prior_shipment_id"
  - "Shipment 139-S post-merge closure session, 2026-08-18"
---

# RESIDUAL DEFECT: Forward Dependents Wrongly Suppress the Topology Gate's Implicit-Predecessor Fallback

## STATUS: unfixed on `main` as of this writing. Fix verified below, NOT committed.

## Why this was not committed during this session

This defect was discovered while validating post-merge closure for shipment
139-S / PR #357, whose merged commit (`0568f044`) introduced the bug while
fixing a *different*, narrower multi-hop gap flagged by the same PR's
Copilot review. The operator's task for this session was explicitly bounded
to "139-S only" with a hard stop before touching `138-S` or any other scope
expansion, and the Post-Merge Branch Protocol restricts the post-merge
closure branch to backlog archival / knowledge graduation / documentation
work — not new source-code fixes for a shipment that has already merged and
closed. Committing this fix silently into the closure branch would both
violate that branch's scope discipline and exceed the session's
bounded-stop authorization. The fix is fully verified (all tests pass) and
is recorded here in full so no rediscovery work is needed; it should be
picked up as a properly triaged Stage-created hotfix task.

## Discovery

While independently re-verifying PR #357's Copilot review coverage during
post-merge closure (a code-review-agent adversarial pass flagged a
finding-count inconsistency in the closure/memory docs), the underlying
GraphQL review-thread data was cross-checked against the *raw* review
bodies (`gh pr view 357 --json reviews`). Several Copilot findings were
present only as "Suppressed comments" blocks embedded in review bodies —
never posted as actual `reviewThreads` — and therefore were never replied
to or resolved via the standard thread-based Copilot review workflow this
session otherwise followed faithfully. Two of these suppressed findings
(on `src/autoharness/gates/topology.py:1346`, across two separate review
rounds) described the exact forward-dependent false-negative reproduced
below, and were never actually addressed before merge.

## Reproduction

```python
# With src/ on path, tests/ on path:
from autoharness.gates.topology import evaluate, TopologyInput
import test_gates_topology as t

readers = t._FakeReaders(shipments=(
    t._shipment('111-S', 'queued'),
    t._shipment('112-S', 'queued'),
    t._shipment('113-S', 'queued', deps=('112-S',)),  # NORMAL forward dep
))
result = evaluate(
    TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='112-S'),
    readers=readers,
)
# BUG: exit_code == 0, primary_token is None.
# EXPECTED: primary_token == 'PREDECESSOR_NOT_SHIPPED' (111-S is queued and
# numerically-prior to 112-S; nothing about 113-S depending on 112-S makes
# that untrue).
```

`113-S` declaring `dependencies: [112-S]` is a completely ordinary
forward-order relationship (113 comes after 112, and needs 112 first,
exactly as numeric-adjacency would already predict) — not a reverse-edge
anomaly. Yet the current code's `any(...)` check has no directionality
filter, so it disables the entire numeric-adjacency fallback for the
*target* (112-S) merely because some other shipment (113-S, numerically
higher) happens to name it as a dependency. This means 112-S can now be
incorrectly claimed even though its true implicit predecessor (111-S) is
still unshipped.

## Verified fix

```diff
--- a/src/autoharness/gates/topology.py
+++ b/src/autoharness/gates/topology.py
@@ -1327,23 +1327,37 @@ def _prior_shipment_id(target: str, shipments: Sequence[ShipmentState]) -> str |
     if not match:
         return None
     target_num = int(match.group(1))
-    # If ANY shipment in the full set explicitly declares the target as one
-    # of its own `dependencies` (i.e. that shipment depends on / is blocked
-    # by the target), the ordering here is governed by explicit
-    # dependencies, not implicit numeric guessing -- for the WHOLE target,
-    # not just the specific numerically-adjacent shipment that made the
-    # declaration. Skipping only that one violator and falling through to
-    # the next-lower numeric candidate is still wrong: it would fabricate an
-    # implicit predecessor relationship the backlog never declared for a
-    # DIFFERENT, unrelated shipment. For example, with 137-S queued and
-    # unrelated, 138-S declaring `dependencies: [139-S]`, and target =
-    # 139-S: 138-S is skipped as the direct violator, but 137-S has no real
-    # relationship to 139-S at all and must not be injected either. The
-    # mere existence of any explicit reverse edge proves this target's
-    # ordering is explicit, so the entire numeric-adjacency fallback is
-    # disabled for it.
-    if any(target in shipment.blocking_predecessor_ids for shipment in shipments):
-        return None
+    # If any NUMERICALLY LOWER shipment in the full set explicitly declares
+    # the target as one of its own `dependencies` (i.e. that lower-numbered
+    # shipment depends on / is blocked by the higher-numbered target -- the
+    # reverse of what the numeric-adjacency heuristic assumes), the
+    # ordering here is governed by explicit dependencies, not implicit
+    # numeric guessing -- for the WHOLE target, not just the specific
+    # shipment that made the declaration.
+    #
+    # This check MUST be restricted to lower-numbered dependents. A
+    # numerically HIGHER shipment declaring the target as its dependency
+    # (e.g. 113-S depends on 112-S) is the NORMAL forward-order case the
+    # heuristic is designed to support, not an anomaly -- it says nothing
+    # about whether the target itself has an undeclared implicit
+    # predecessor, and must not suppress the fallback for the target.
+    for shipment in shipments:
+        other = re.match(r"^(\d+)-S$", shipment.shipment_id)
+        if not other:
+            continue
+        if int(other.group(1)) >= target_num:
+            continue
+        if target in shipment.blocking_predecessor_ids:
+            return None
     prior: tuple[int, str] | None = None
```

Plus a new regression test,
`test_higher_numbered_forward_dependent_does_not_suppress_targets_own_predecessor_check`,
reproducing the exact scenario above and asserting the corrected
`PREDECESSOR_NOT_SHIPPED` / `predecessor_id: 111-S` outcome.

**Verification performed this session** (fix applied locally, not
committed): full `tests/test_gates_topology.py` — 94/94 tests, 113/113
subtests pass. Full repo test suite — 1550 passed (0 new failures; the one
unrelated failure observed,
`tests/test_deploy_harness_scripts.py::DeployHarnessPs1ChecklistExecutionTests::test_checklist_report_prints_non_interactively`,
reproduces identically with or without this fix and is a local
environment-version-string mismatch unrelated to `topology.py`).

## Practical impact assessment

- Does **not** affect the `138-S -> 139-S` predecessor relationship
  itself: `138-S` (numerically lower) declaring `139-S` as its dependency
  is already correctly handled by the lower-numbered branch of the check,
  which was correct both before and after this fix.
- Only manifests when some numerically-HIGHER shipment in the live/queued
  set declares a normal forward dependency on a lower-numbered target that
  itself has an unshipped, undeclared numeric predecessor. No such
  configuration is currently known to exist in this repo's live shipment
  set as of 2026-08-18, so there is no known active false-negative right
  now — but the defect is real and will silently mis-permit a claim the
  moment such a configuration arises.

## Recommended next step

Route to Stage for a properly triaged hotfix task (new feature/task ID,
plan, and review) applying the verified diff above plus its regression
test. This is not something Ship can create on its own initiative (backlog
item creation is outside the Ship role boundary, P-010), and the
Post-Merge Branch Protocol correctly kept it out of 139-S's closure
branch.

## Applicability

Any "disable a heuristic when an explicit edge is found" fix must filter
by the specific *direction* the edge needs to have to be anomalous — not
merely "an edge involving this entity exists at all." This is the same
class of lesson as
`docs/compound/2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md`,
one level deeper: fixing "only the specific violator" was too narrow;
"any relationship at all" turned out to be too broad; the correct fix
needed the precise directional predicate (numerically lower + explicit
dependency on target) the whole time.
