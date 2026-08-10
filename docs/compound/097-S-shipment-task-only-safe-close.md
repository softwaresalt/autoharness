---
problem_type: backlog-safe-close
category: backlogit
root_cause: covering-feature-listed-in-shipment-manifest-items-causes-cascade-safe-close-corruption
tags: [backlogit, shipment, safe-close, manifest, task-only-items, p-010, p-015, telemetry]
shipment: 097-S
feature: 092-F
pr: 241
---

# 097-S: Shipment Manifests Must Keep `custom_fields.items` Task-ID-Only

Shipment `097-S` reinforced a safe-close contract for partial-feature shipment
manifests: `custom_fields.items` lists only task IDs. The covering feature is
derived through each task's `parent_id`; it is not listed as another manifest
item.

## Problem

When a covering feature is added directly to a shipment manifest's `items` list,
safe-close logic can treat the feature as a sibling artifact to cascade through.
That is dangerous because the feature is the parent of the tasks, not one of the
shipment's leaf task units.

## Durable Rule

For shipment manifests:

- `custom_fields.items` contains task IDs only.
- The covering feature is derived from task `parent_id` values.
- During post-merge closure, skip pre-archived manifest tasks. For partial-feature
  shipments, keep non-manifest parent or sibling artifacts protected unless the
  operator/Orchestrator explicitly declares that the covering feature itself is
  complete and in closure scope.
- When the covering feature is explicitly in closure scope, close it separately
  from the shipment manifest. Do not add it to `custom_fields.items`.
- Use per-item operations for this close path:
  `backlogit move <id> --status done` followed by `backlogit archive <id>`.
- Do not use `backlogit shipment ship <shipment>` for this partial-feature
  close path; it is too broad for the task-only manifest contract.

## Why It Matters

The manifest is the release unit's explicit membership boundary. Keeping it
task-only prevents accidental parent/sibling archival and makes the close path
auditable: the shipped task set is fixed, while any covering-feature closure is
an explicit operation outside the manifest, not an implicit cascade.

## Verification Pattern

After safe-close:

1. Confirm the shipment archive still lists only task IDs under
   `custom_fields.items`.
2. Confirm the covering feature is archived separately.
3. Confirm every task in the manifest is archived.
4. Confirm no active or queued artifact remains for the lineage.

## Reconciliation — the FULLY-COVERED ROOT exception (2026-08-10, PR #325)

**Scope of the Durable Rule above: PARTIAL-feature shipments.** Its hazard model
is a covering feature that still has children *outside* the manifest, where a
broad `shipment ship` would cascade into unshipped siblings. That reasoning is
correct and unchanged for that case.

**A second, opposite hazard exists, and task-only manifests do not avoid it.**
On backlogit 1.8.0, `returnUnreleasedFeatureItems` is **not** gated by
`explicitScope`: it also runs for a non-member *ancestor* feature discovered via
`featureScopeRoots`' upward `parent_id` walk. So a **task-only** manifest whose
tasks share a covering feature with tasks in a *later* shipment causes the first
close to clear `parent_id` on every one of those later tasks. This was reproduced
against the real engine: closing S1 orphaned **14/14** downstream tasks (ARM A of
`docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1`).
Task-only membership is therefore **not** sufficient for safety on its own, and
the proposed repair (Ship calling `adopt_item` afterwards) is outside Ship's Role
Boundary (fail-closed **P-010**).

**The exception, and its preconditions.** A covering feature MAY be an explicit
member of `custom_fields.items` when **both** hold:

1. **FULL COVERAGE** — every child of that feature is also in the same manifest,
   so `returnUnreleasedFeatureItems` iterates an empty remainder and returns the
   empty set; and
2. **ROOT PLACEMENT** — the feature has no parent, so `featureScopeRoots` cannot
   escape upward into another shipment's scope.

Under those two conditions the cascade the Durable Rule guards against is
**structurally impossible** rather than merely avoided, and a single
`backlogit shipment ship` closes the release unit with `returned_ids: []` and no
post-close repair. Verified end to end on the real engine: **64/64** and
**196/196** assertions, including a fixture replay of the exact live topology
(`verify-plan1-shipment-topology.ps1`).

**Which rule applies when.**

| Manifest shape | Contract |
|---|---|
| Covering feature has children **outside** the manifest (partial) | Durable Rule above: task-only `items`; close the feature separately with `move` + `archive`; do **not** use `shipment ship`. |
| Covering feature is **fully covered** and **root** | This exception: list the feature FIRST in `items`, then all its children; close with a single `shipment ship`. |

`127-S` / `128-S` / `129-S` (Plan-1 supervisor program) are the fully-covered-root
case and intentionally list their covering features. Ship should read this
reconciliation, not the partial-feature rule, for those three shipments.
