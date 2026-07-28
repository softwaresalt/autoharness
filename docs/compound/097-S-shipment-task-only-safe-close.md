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
