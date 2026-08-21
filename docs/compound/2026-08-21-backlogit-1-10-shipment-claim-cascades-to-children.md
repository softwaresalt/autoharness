---
title: "backlogit 1.10.0 shipment claim cascades activation to the covering feature and queued tasks"
description: "Claiming a shipment (queued -> active) in backlogit 1.10.0 also flips the shipment's covering feature and every queued manifest task straight to active in the same operation, not just the shipment record itself."
problem_type: "tool_version_behavior_drift"
category: "workflow-issues"
component: "backlogit-cli"
root_cause: "The Ship agent contract (templates/agents/_ship.agent.md.tmpl) already tolerates and documents that every manifest task may read active immediately after a shipment claim (its 4a/intake-reconciliation wording explicitly allows this), but does not attribute *why* -- it does not say this is backlogit's own shipment-claim cascade behavior in the currently-installed CLI version (1.10.0), as distinct from, e.g., a stale index or a prior partial session. This entry supplies that missing causal attribution; it does not describe a gap in the contract's tolerance, which was already correct."
resolution_type: "process_adjustment"
severity: "medium"
file_path: "templates/agents/_ship.agent.md.tmpl"
citations:
  - "PR #382"
  - ".backlogit/archive/144-S.md"
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
`updated_at` timestamps matching the claim -- before any task-level claim
(the template's Step 4.1 Claim Task) had been individually issued.

This workspace runs `backlogit` **1.10.0**. The Ship agent template
(`templates/agents/_ship.agent.md.tmpl`, current `main`) already
**tolerates** this exact state -- its 4a post-claim verification step
explicitly says "before the Step 4.1 Claim Task step moves any task to
`{{STATUS_ACTIVE}}`" (acknowledging a task can already be active before
that step runs), and its intake-reconciliation item 6 explicitly allows
"all `{{STATUS_ACTIVE}}` immediately after this session's own claim." The
contract's tolerance is correct and was **not** missing. What it does not
state is the **causal attribution**: *why* every manifest task is already
active at that point -- namely, that the currently-installed backlogit
CLI's `shipment claim` operation itself cascades the activation to the
covering feature and every queued manifest task, rather than this being an
artifact of a stale index, a prior partial session, or coincidental manual
intervention. This entry supplies that missing causal attribution only.

**Not a first observation.** The immediately prior Ship session (`147-S`)
already noted this same behavior informally in its own session memory
(`docs/archive/memory/2026-08-21-ship-147-s-execution-and-closure-session.md`):
"`backlogit shipment claim` in this backlogit version (1.10.0) atomically
activates ALL manifest task items at claim time." That note was scoped to
one session's pipeline trace and had not yet been promoted to a standalone,
generalizable `docs/compound/` entry; this entry does that promotion so the
causal attribution is discoverable independent of any one session's memory
file.

## Why it matters

A Ship session that does not know the cascade is backlogit's own claim
behavior could misdiagnose the already-active tasks as evidence of a prior
partial session (triggering the intake-reconciliation early-warning
`SHIPMENT_STATE_INCONSISTENT` early-warning unnecessarily) or could treat
the per-task claim step as a required state transition when it is actually
a no-op confirmation. Recognizing the cascade means:

1. The intake-reconciliation check should be run with
   `expected_status: active` (not `queued`) immediately after a fresh claim
   in this backlogit version, since every manifest task -- not just the
   shipment record -- already reads `active` by the time that check runs.
2. The per-task "Claim: move to active" step is safe to run as an
   idempotent confirmation (verify current status, do not error if already
   `active`) rather than an unconditional first mutation.
3. This is a **tool-version behavior**, not a contract change requested by
   any shipment -- it should not be "fixed" by editing the Ship agent
   template to assume one cascade behavior over the other. Whether an older
   or differently configured backlogit installation behaves the same way
   is **unverified by this entry** -- no 1.8.0 run, release note, or test
   was checked, and no claim about record-only semantics in any other
   version should be inferred from this observation. The
   intake-reconciliation check's own dual-branch wording (`queued` or
   `active`) already tolerates both outcomes without needing to know which
   one a given installation exhibits; treat the specific cascade behavior
   as **version-specific and to be reverified against whatever backlogit
   version is actually installed**, not assumed either way.

## Generalizable takeaway

When an externally-versioned CLI dependency's mutation semantics are load-
bearing for an agent contract's state-machine assumptions (here: "does
claiming a shipment claim its children too?"), record the observed version
and behavior explicitly the first time a session notices a mismatch between
the observed behavior and any assumption a reader might otherwise make,
rather than silently working around it in-session. The contract's own
dual-branch wording already tolerated the ambiguity correctly; what was
missing was the causal explanation for *why* the tolerated state arises,
which this entry now provides -- without extending that explanation into
an unverified claim about any other backlogit version's behavior.

## Evidence

* `backlogit version` reports `1.10.0` in this workspace.
* `backlogit shipment claim 144-S` -> immediate `backlogit get 136-F`,
  `backlogit get 136.002-T`, `backlogit get 136.003-T` all returned
  `status: active` with `updated_at` matching the claim's timestamp,
  before any task-level claim was issued.
* `136.001-T` (archived, pre-archived manifest member) was correctly left
  untouched by the same claim operation -- the cascade activates queued
  children only, never an archived one.
