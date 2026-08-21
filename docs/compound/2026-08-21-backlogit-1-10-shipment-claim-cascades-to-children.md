---
title: "backlogit 1.10.0 shipment claim cascades activation to the covering feature and queued tasks"
description: "Claiming a shipment (queued -> active) in backlogit 1.10.0 also flips the shipment's covering feature and every queued manifest task straight to active in the same operation, not just the shipment record itself."
problem_type: "tool_version_behavior_drift"
category: "workflow-issues"
component: "backlogit-cli"
root_cause: "The Ship agent contract (templates/agents/_ship.agent.md.tmpl) was authored assuming backlogit 1.8.0 semantics, where claiming a shipment changes only the shipment record's own status and task-level claims happen individually in Step 2. backlogit 1.10.0 (the version actually installed in this workspace) cascades the claim to the covering feature and every queued task in the manifest, so by the time Step 0.5's intake-reconciliation check runs, tasks that have not yet been individually claimed already read as active."
resolution_type: "process_adjustment"
severity: "medium"
file_path: "templates/agents/_ship.agent.md.tmpl"
citations:
  - "PR #382"
  - ".backlogit/queue/144-S.md"
date: 2026-08-21
shipment: 144-S
feature: 136-F
tasks: ["136.002-T", "136.003-T"]
pr: 382
tags: [backlogit, shipment-claim, version-drift, intake-reconciliation, ship-agent]
---

# Compound Learning: backlogit 1.10.0 shipment claim cascades to children

## What happened

While executing shipment `144-S`, `backlogit shipment claim 144-S` was run
as the documented first mutation. Immediately afterward, `backlogit get
136-F` (the covering feature) and `backlogit get 136.002-T` /
`136.003-T` (the two executable tasks) all reported `status: active`, with
`updated_at` timestamps matching the claim -- not `queued`, as the Ship
agent's Step 2 ("Claim: Move the task to active via `backlogit_move_item`")
implies for a not-yet-claimed task.

This workspace runs `backlogit` **1.10.0**. The Ship agent contract's
intake-reconciliation guidance (Step 0.5 item 6) already anticipates this
exact ambiguity in its own wording -- "expected_status: `queued` (or
`active` if already claimed)" and the scope note about "true session-start
intake, where every manifest task still shares one uniform status (all
`queued` pre-claim, or all `active` immediately after this session's own
claim)" -- but does not name *why* a freshly claimed shipment's tasks would
already be uniformly `active` before Step 2 has individually claimed any of
them. This compound entry supplies that missing "why": it is cascade
behavior in the currently-installed backlogit version, not an artifact of
manual intervention or a stale index.

**Not a first observation.** The immediately prior Ship session (`147-S`)
already noted this same behavior informally in its own session memory
(`docs/archive/memory/2026-08-21-ship-147-s-execution-and-closure-session.md`):
"`backlogit shipment claim` in this backlogit version (1.10.0) atomically
activates ALL manifest task items at claim time." That note was scoped to
one session's pipeline trace and had not yet been promoted to a standalone,
generalizable `docs/compound/` entry; this entry does that promotion so the
behavior is discoverable independent of any one session's memory file.

## Why it matters

A Ship session that assumes 1.8.0-era "claim only touches the shipment
record" semantics could misdiagnose the already-active tasks as evidence of
a prior partial session (triggering the Step 0.5 item 1a
`SHIPMENT_STATE_INCONSISTENT` early-warning unnecessarily) or could treat
Step 2's per-task claim as a required state transition when it is actually
a no-op confirmation. Recognizing the cascade means:

1. The Step 0.5 item 6 intake-reconciliation check should be run with
   `expected_status: active` (not `queued`) immediately after a fresh claim
   in this backlogit version, since every manifest task -- not just the
   shipment record -- already reads `active` by the time that check runs.
2. Step 2's "Claim: move to active" for each task is safe to run as an
   idempotent confirmation (verify current status, do not error if already
   `active`) rather than an unconditional first mutation.
3. This is a **tool-version behavior**, not a contract change requested by
   any shipment -- it should not be "fixed" by editing the Ship agent
   template to assume one cascade behavior over the other. A future
   installation pinned to backlogit 1.8.0 may still see the original
   record-only claim semantics; the intake-reconciliation check's own
   dual-branch wording (`queued` or `active`) already tolerates both, and
   this entry exists so a future session recognizes *why* it observes one
   branch or the other rather than treating it as an anomaly.

## Generalizable takeaway

When an externally-versioned CLI dependency's mutation semantics are load-
bearing for an agent contract's state-machine assumptions (here: "does
claiming a shipment claim its children too?"), record the observed version
and behavior explicitly the first time a session notices a mismatch between
the contract's assumed default and the installed tool's actual behavior,
rather than silently working around it in-session. The contract's own
dual-branch wording already anticipated the ambiguity; what was missing was
the causal explanation, which this entry now provides for the next session
that hits the same fork.

## Evidence

* `backlogit version` reports `1.10.0` in this workspace.
* `backlogit shipment claim 144-S` -> immediate `backlogit get 136-F`,
  `backlogit get 136.002-T`, `backlogit get 136.003-T` all returned
  `status: active` with `updated_at` matching the claim's timestamp,
  before any task-level claim was issued.
* `136.001-T` (archived, pre-archived manifest member) was correctly left
  untouched by the same claim operation -- the cascade activates queued
  children only, never an archived one.
