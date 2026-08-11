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
**197/197** assertions, including a fixture replay of the exact live topology
(`verify-plan1-shipment-topology.ps1`).

> ### ⏳ RESOLVED IN PRINCIPLE, NOT YET OPERATIVE — F26 (P1, resolved 2026-08-11); gated on `118.007-T`
>
> **Ship MUST NOT act on the exception below until `118.007-T` has landed.** The
> operator ruled (ruling 8, accepted 2026-08-11) that **P-015 is to be amended**
> so the permitted close operation and the executable evidence agree, and that
> Ship must **not** be required to perform a P-010-forbidden operation. The
> ruling settles *what the contract will say*; it does not by itself change the
> files that bind Ship.
>
> **Why this document still cannot authorise the close.** The original defect was
> never the *shape* of the rule — it was that a Stage planning artifact declared
> an exception without amending the operative surfaces. `.github/agents/_ship.agent.md`
> still prohibits the cascade **unconditionally** ("NEVER the cascade
> `backlogit_ship_shipment`, P-015" / "Do NOT call `backlogit shipment ship`"),
> and **P-015** in `templates/policies/workflow-policies.md.tmpl` still states its
> prohibition and postcondition absolutely even though its *Applies when* is scoped
> to partial-feature shipments. Restating the exception more confidently here would
> reproduce exactly the error F26 identified. **A planning artifact cannot grant Ship
> an exemption from Ship's own operative prohibition** — that remains true after the
> ruling.
>
> **How it becomes operative.** `118.007-T` (a member of **`127-S`**, the first
> shipment, deliberately placed so it lands before *any* close in the chain)
> amends all four surfaces coherently: the P-015 policy template, the Ship agent
> template, the `shipment-reconcile` skill, and this compound document. The
> exception it introduces is **machine-checkable** — a *verified* fully-covered-root
> carve-out, where "verified" means the covering feature is root, is itself a
> manifest item, and has no children outside the manifest — rather than a prose
> permission. Until that task is complete, the Durable Rule (safe-close) governs.
>
> **Role-boundary note.** Stage did **not** edit the policy or agent templates to
> implement this ruling. Templates are the product surface, so amending them is
> implementation work owned by Ship; Stage's compliant action was to create
> `118.007-T` and place it in the first shipment.
>
> **The topology was never affected.** Under either close path the
> fully-covered-root manifests are correct: the covering feature is itself a
> manifest item and no unshipped siblings exist, so the protected set is empty and
> safe-close archives exactly the release unit. The **evidence question** is
> likewise resolved — once `118.007-T` lands, the 64/64 cascade-close simulation
> once again proves a property of the operation that will actually be called.
> Detail: `docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md`.

**Which rule applies when.**

| Manifest shape | Contract |
|---|---|
| Covering feature has children **outside** the manifest (partial) | Durable Rule above: task-only `items`; close the feature separately with `move` + `archive`; do **not** use `shipment ship`. |
| Covering feature is **fully covered** and **root** | This exception: list the feature FIRST in `items`, then all its children; close with a single `shipment ship`. **⏳ NOT YET OPERATIVE — gated on `118.007-T` — see the F26 banner above; the close command is not operative pending an operator ruling.** |

`127-S` / `128-S` / `129-S` (Plan-1 supervisor program) are the fully-covered-root
case and intentionally list their covering features — a manifest shape that is
valid under **either** close path. **However, Ship must NOT treat this
reconciliation as overriding the unconditional cascade prohibition in its own
agent file** until `118.007-T` amends that file and P-015 (F26, ruling 8).
As of 2026-08-11 those three shipments are **gate-clear** — all fourteen
post-budget P1s were dispositioned by accepted operator rulings — and `127-S` is
the only structurally eligible cursor. The close command to use is therefore:
**safe-close** until `118.007-T` lands, and the verified fully-covered-root
cascade thereafter. Because `118.007-T` is itself a member of `127-S`, the
amendment lands *within* the first shipment and before that shipment's own
close.
