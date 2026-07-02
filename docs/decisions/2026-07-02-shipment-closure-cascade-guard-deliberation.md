---
title: "Shipment Closure Cascade Guard: Deliberation and Direction"
description: "Reframes stash 86F19EF7 from 'patch backlogit' to a harness-side guard: shipment closure must never use the cascade `backlogit shipment ship`, which archives the parent feature and orphans unshipped siblings on partial-feature shipments. Recommends single-artifact closure with verify-after-each invariant + git-revert-on-cascade."
topic: "How should the harness close shipments safely given the external backlogit shipment-ship parent-cascade bug that autoharness cannot patch?"
depth: "deep"
decision_status: "accepted"
promoted_to: "docs/plans/2026-07-02-shipment-closure-cascade-guard-plan.md"
linked_artifacts:
  - "templates/agents/.ship.agent.md.tmpl"
  - "templates/skills/shipment-reconcile/SKILL.md.tmpl"
  - "templates/policies/workflow-policies.md.tmpl"
  - ".github/agents/.ship.agent.md"
source_stash_ids:
  - "86F19EF7"
backlog_items:
  - "056-F"
  - "056.001-T"
  - "056.002-T"
  - "056.003-T"
tags:
  - "reliability"
  - "closure"
  - "ship-agent"
  - "backlogit"
  - "harness-guard"
---

## Problem Frame

Stash `86F19EF7` was originally worded as *"Upgrade/patch backlogit past the
shipment-ship parent-cascade bug."* That framing is **out of scope for this
repository**: the defect lives in the external `backlogit` Go binary (v1.3.0),
not in autoharness. autoharness cannot patch backlogit source and must not
pin its own reliability to an upstream fix it does not control.

The **in-scope** problem is a harness-side one: the Ship agent's post-merge
closure calls the cascade operation `{{OP_SHIP_SHIPMENT_MCP}}`
(`backlogit shipment ship`), which archives **all** queue items tied to the
shipment's feature — including the **parent feature** and any **unshipped
sibling tasks** — even when the shipment is a **partial-feature** shipment that
intentionally excludes the parent.

## What Actually Happened (056-S, this cycle)

Shipment `056-S` carried only a subset of feature `055-F`'s tasks
(`055.002-T`, `055.004-T`, `055.005-T`, `055.006-T`). On closure,
`backlogit shipment ship`:

1. Archived the **parent feature `055-F`** (which was still `blocked`, not done), and
2. Orphaned the unshipped siblings **`055.001-T`** and **`055.003-T`**.

Recovery required a manual `git revert` of the unintended archival followed by
closing the shipment via **single-artifact status moves**. This is the exact
mitigation this deliberation proposes to make the default, codified path.

## Root Cause

`backlogit shipment ship` treats a shipment as a proxy for its covering feature
and cascade-archives the whole feature subtree. For **full-feature** shipments
(feature + all its tasks) this is benign. For **partial-feature** shipments
(the 056-S lesson, and the P-001-mandated pattern when Stage deliberately ships
a subset), it is destructive: it archives artifacts that are **not in the
shipment manifest**.

Existing mitigations are **detect-after-the-fact only**:

* The `shipment-reconcile` skill runs pre/post reconciliation but is explicitly
  *report-and-halt* — it never prevents the cascade; it detects orphans/missing
  items afterward.
* Policy **P-007** covers the separate "archive files silently deleted from the
  working tree" quirk via `git restore`, not the parent-cascade.

Neither prevents the parent feature from being archived and siblings orphaned.

## Options

### Option A — Wait for / require an upstream backlogit fix

Pin a backlogit version that fixes the cascade, or file the bug upstream and
block closure until fixed.

* **Pros:** Fixes the true root cause; no harness complexity.
* **Cons:** Out of this repo's control; unbounded timeline; blocks all
  partial-feature shipments meanwhile; couples autoharness reliability to an
  external release cadence.
* **Risk:** High (schedule/availability). **Effort:** N/A here.

### Option B — Detection-only hardening (strengthen shipment-reconcile)

Keep calling `backlogit shipment ship` but make post-mode reconciliation always
detect the parent-cascade and prompt an operator revert.

* **Pros:** Small change; reuses existing skill.
* **Cons:** Still performs the destructive op every time; relies on a manual
  revert on the hot path; leaves a window where the backlog is corrupt; is
  reactive, not preventive.
* **Risk:** Medium. **Effort:** Low.

### Option C — Single-artifact closure with verify-after-each invariant + git-revert-on-cascade (RECOMMENDED)

Stop using the cascade op for closure. Close a shipment by moving/archiving
**only the shipment's explicit item IDs**, one artifact at a time, and after
each move verify the invariant that the parent feature and any unshipped
siblings remain un-archived and un-orphaned. If a cascade is nonetheless
detected (e.g., a future op regresses), `git revert`/`git restore` the
unintended archival immediately and halt.

* **Pros:** Prevents the corruption instead of cleaning it up; makes
  partial-feature shipments first-class; scoped strictly to the manifest;
  invariant + revert provides defense-in-depth; independent of upstream fixes.
* **Cons:** Larger blast radius across four artifact families (ship agent
  template, closure/reconcile skill, workflow policy, installed mirror); the
  ship agent gains a slightly more involved closure procedure.
* **Risk:** Low functional; the invariant check + revert bound the downside.
  **Effort:** Medium (multi-artifact, but each unit is small and isolated).

### Option D — Hybrid: gate the cascade behind a full-feature check

Only call `backlogit shipment ship` when the shipment manifest contains the
parent feature AND all its tasks; otherwise fall back to single-artifact
closure.

* **Pros:** Keeps the fast path for full-feature shipments.
* **Cons:** Two closure code paths to maintain and test; the "full-feature"
  detection is itself a place to get wrong; most autoharness shipments are
  partial by the P-001 pattern, so the fast path is rarely taken.
* **Risk:** Medium (path-divergence bugs). **Effort:** Medium.

## Recommendation — Option C

Adopt **single-artifact closure as the default for all shipments**, with a
verify-after-each invariant and git-revert-on-cascade. Uniform single-path
closure is simpler to reason about and test than Option D's dual path, and it
removes the destructive cascade entirely rather than merely detecting it
(Option B) or waiting on an upstream fix (Option A). The partial-feature case is
the *common* case in this harness, so the safe path should be the *only* path.

## Blast Radius (why this is non-trivial)

Four artifact families change; each is decomposed into an isolated task:

| Artifact family | File | Task |
|---|---|---|
| Ship agent (template + installed mirror) | `templates/agents/.ship.agent.md.tmpl` (Step 1.b, ~L457-479), `.github/agents/.ship.agent.md` (~L260) | `056.001-T` |
| Closure/reconcile skill | `templates/skills/shipment-reconcile/SKILL.md.tmpl` | `056.002-T` |
| Workflow policy | `templates/policies/workflow-policies.md.tmpl` (new policy + version history) | `056.003-T` |

The installed `.github/agents/.ship.agent.md` mirror must change alongside the
template because this repo dogfoods its own harness; its closure step currently
calls `backlogit_ship_shipment` directly with no reconcile gate.

## Risks and Mitigations

* **Two closure descriptions could drift** (template vs installed mirror) →
  keep both in a single task (`056.001-T`) so they change together.
* **Skill and agent could disagree on the procedure** → the agent delegates the
  archival mechanics to the `shipment-reconcile` safe-close procedure
  (`056.002-T`) so there is one source of truth.
* **Invariant false-positives** (legitimately pre-archived items) → reuse
  `shipment-reconcile`'s existing `pre-archived` classification so already-shipped
  items are not flagged.

## Guardrails Honored

This is a **deliberation only**. No agent, skill, policy, template, or installed
artifact was modified. No branch was created and no PR was opened. Execution is
owned by the Ship agent per the harvested plan and tasks (`056.001-T`,
`056.002-T`, `056.003-T`).
