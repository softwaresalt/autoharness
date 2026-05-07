---
problem_type: backlogit_shipment_status_constraints
category: backlogit
root_cause: Shipment artifacts in backlogit only accept queued/active/shipped/abandoned as valid statuses. Other artifact types (task, feature, bug, spike, chore) accept a broader set including review/blocked/done/archived. Setting status=review on a shipment is silently accepted by the CLI but is not a valid state per the schema.
tags: [backlogit, shipment, status, schema, header-def]
shipment: 011-S
date: 2026-05-07
---

# backlogit Shipment Status Constraints

## Problem

A shipment artifact was moved to `status: review` during PR review, mirroring the
pattern used for tasks and features. Copilot review flagged this as invalid.

## Root Cause

backlogit's `header-def.yaml` defines different status enums per artifact type:

| Artifact type | Valid statuses |
|---|---|
| task, feature, bug, spike, chore, subtask | queued, active, blocked, review, done, accepted, rejected, archived |
| **shipment** | **queued, active, shipped, abandoned** |

The `backlogit move` CLI does not validate against the schema — it silently accepts
invalid status values, which only surface as issues during review or downstream
processing.

## Fix

While a shipment's PR is under review, keep the shipment at `status: active`.
Only transition to `shipped` after the PR is merged and the Merge Confirmation
Gate passes.

## Valid shipment lifecycle

```
queued → active (claimed, branch created)
active → shipped (PR merged, closure complete)
active → abandoned (cancelled)
```

## Verification

Check `.backlogit/header-def.yaml` under `types.shipment.fields.status.values`
to confirm valid transitions. The schema is the source of truth.
