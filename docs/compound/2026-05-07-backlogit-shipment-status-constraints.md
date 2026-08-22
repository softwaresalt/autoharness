---
problem_type: backlogit_shipment_status_constraints
category: backlogit
root_cause: Shipment artifacts in backlogit accept queued/blocked/active/shipped/abandoned as valid statuses. Other artifact types (task, feature, bug, spike, chore) accept a broader set including review/done/archived. Setting unsupported statuses such as review on a shipment is invalid per the schema.
tags: [backlogit, shipment, status, schema, header-def]
shipment: 011-S
date: 2026-05-07
source: docs/compound/2026-05-07-backlogit-shipment-status-constraints.md
doc_type: learning
title: "backlogit Shipment Status Constraints"
---

# backlogit Shipment Status Constraints

> **CORRECTION (2026-08-04, 109-F cycle-2 review-fix).** The "Valid shipment
> lifecycle" diagram below is STALE for backlogit 1.8.0. Verified against
> `C:/Source/GitHub/backlogit/internal/core/shipment.go` `isValidShipmentTransition`
> (L336-345) and `MoveShipmentStatus` (L107-108): the ONLY supported shipment
> transitions are `queued -> active`, `active -> shipped`, and `active -> abandoned`.
> There is **no** `queued -> blocked` and **no** `blocked -> queued` transition, and
> `blocked` is not even a defined `ShipmentStatus` constant — a shipment written to
> `blocked` becomes a dead end that can never legally transition. The `backlogit move`
> CLI silently accepts invalid status writes, which is how `blocked` shipment records
> got created. **Correct serial-sequencing pattern:** keep dependency-gated successor
> shipments at `status: queued` from creation and gate them purely with shipment
> `blocks` edges (the queue hard-eligibility gate suppresses a queued successor whose
> blocking predecessor has not yet shipped; the edge clears automatically on
> predecessor ship). Do NOT model dependency gating with a `blocked` shipment status.

## Problem

A shipment artifact was moved to `status: review` during PR review, mirroring the
pattern used for tasks and features. Copilot review flagged this as invalid.

## Root Cause

backlogit's `header-def.yaml` defines different status enums per artifact type:

| Artifact type | Valid statuses |
|---|---|
| task, feature, bug, spike, chore, subtask | queued, active, blocked, review, done, accepted, rejected, archived |
| **shipment** | **queued, blocked, active, shipped, abandoned** |

The `backlogit move` CLI does not validate against the schema — it silently accepts
invalid status values, which only surface as issues during review or downstream
processing.

## Fix

While a shipment is waiting on an external prerequisite or dependency gate that
must prevent claim/intake, keep it at `status: blocked`. Transition it back to
`queued` only after the gate clears. Once claimed, keep the shipment at
`status: active`; transition to `shipped` only after the PR is merged and the
Merge Confirmation Gate passes.

## Valid shipment lifecycle

```
queued → blocked (external/dependency gate prevents claim)
blocked → queued (gate cleared; ready for claim)
queued → active (claimed, branch created)
active → shipped (PR merged, closure complete)
active → abandoned (cancelled)
```

## Verification

Check `.backlogit/header-def.yaml` under `types.shipment.fields.status.values`
to confirm valid transitions. The schema is the source of truth.
