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
On backlogit **v1.8.0-dirty, commit `fd8d2c9d`** (the exact engine this evidence
was produced against — see the version-binding caveat at the end of this
document), `returnUnreleasedFeatureItems` is **not** gated by
`explicitScope`: it also runs for a non-member *ancestor* feature discovered via
`featureScopeRoots`' upward `parent_id` walk. So a **task-only** manifest whose
tasks share a covering feature with tasks in a *later* shipment causes the first
close to clear `parent_id` on every one of those later tasks. This was reproduced
against the real engine: closing S1 orphaned **14/14** downstream tasks (ARM A of
`docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1`).
Task-only membership is therefore **not** sufficient for safety on its own, and
the proposed repair (Ship calling `adopt_item` afterwards) is outside Ship's Role
Boundary (fail-closed **P-010**).

**The exception, and its preconditions.** The predicate is quantified over
**every feature member** of `custom_fields.items` — not over a single "covering
feature" — and each such member MUST satisfy **both**:

1. **FULL COVERAGE** — every child of that feature is also in the same manifest,
   so `returnUnreleasedFeatureItems` iterates an empty remainder and returns the
   empty set; and
2. **ROOT PLACEMENT** — the feature has no parent, so `featureScopeRoots` cannot
   escape upward into another shipment's scope.

The manifest MUST contain **nothing beyond** those root feature members and their
children, and qualification is **whole-manifest**: if any feature member fails,
the entire manifest falls back to safe-close.

> **CORRECTED 2026-08-11 (F30).** This previously read "the covering feature …
> and **nothing else**", scoped to *one* feature. That wording would have
> **rejected `129-S`**, which deliberately also carries the childless terminal
> umbrella `117-F` — so the drafted check would have selected safe-close and the
> claim that the 64/64 cascade evidence covers the permitted operation for *all
> three* manifests did not hold. The quantified form admits `117-F` because a
> childless root is trivially fully covered.
>
> **Anti-vacuity requirement.** "Fully covered" is **vacuously true** for a
> childless feature — precisely the shape of check that passes because it found
> nothing to test. Childlessness MUST therefore be **positively verified against
> the live workspace** (enumerate children, assert the count is exactly zero) and
> MUST NOT be inferred from "no missing children were found". A feature whose
> children cannot be enumerated is **not** verified childless and the prohibition
> applies unchanged. No id-specific allowance for `117-F` may appear anywhere.
>
> **Partial-feature safety is not weakened**: any feature member with a child
> absent, any non-root feature member, and any member that is neither a
> qualifying root feature nor a child of one still force safe-close.

Under those conditions the cascade the Durable Rule guards against is
**structurally impossible** rather than merely avoided, and a single
`backlogit shipment ship` closes the release unit with `returned_ids: []` and no
post-close repair. Verified end to end on the real engine, including negative
controls proving the predicate actually rejects partial coverage, foreign
members, and non-root feature members
(`verify-plan1-shipment-topology.ps1`, V13).

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
As of 2026-08-11 those three shipments are **GATED, not gate-clear**: the
confirmatory current-HEAD review raised **F34** (P1, unresolved) against the
force-unlock protocol in `118.005-T`/`118.006-T`, which are members of `127-S`.
An earlier revision of this document claimed gate-clear status; that claim was
made before F34 and is **withdrawn**. `127-S` remains the only *structurally*
eligible cursor, but it is not releasable while F34 is open. The close command to use is therefore:
**safe-close** until `118.007-T` lands, and the verified fully-covered-root
cascade thereafter. Because `118.007-T` is itself a member of `127-S`, the
amendment lands *within* the first shipment and before that shipment's own
close.

## Version binding of this evidence (recorded 2026-08-11)

Every close claim in this document is bound to the engine it was executed
against, **not** to the string "1.8.0":

| Field | Value |
|---|---|
| CLI version | `v1.8.0-dirty` |
| Commit | `fd8d2c9d` |
| CLI build date | `2026-08-11T01:25:43Z` |
| MCP daemon build date | `2026-08-02T07:27:31Z` (same commit `fd8d2c9d`) |
| Binary | `C:\Tools\backlogit.exe` |

Three caveats a future reader must not skip:

1. **The build is `-dirty`.** It was produced from a working tree with
   uncommitted changes, so its exact behaviour is **not reproducible from any
   commit**. "Verified on 1.8.0" is therefore a weaker claim than it appears.
   The only currently uncommitted file in the backlogit checkout is
   `.backlogit/stash.jsonl` (a data file, not source), which is consistent with
   the dirty marker being benign — but that is *inference about the present*,
   not proof about the state at build time.
2. **Two different builds of the same commit are in use.** Backlog *mutations*
   this session went through the MCP daemon (built 08-02); the *evidence*
   (verifier, simulation) went through the CLI (built 08-11). They agree on the
   facts that matter here — the CLI independently read back and validated every
   dependency edge the MCP surface wrote — so this is recorded as a known split,
   not an unresolved risk.
3. **The installed engine is behind its source, and an update is advertised.**
   `C:\Source\GitHub\backlogit` is **128 commits ahead** of `fd8d2c9d`, with
   substantial changes to precisely the close surface this document describes:
   `shipment_lifecycle.go` (+188), `dependencies.go` (+178), a **new**
   `shipment_gate_manifest.go` (+177), plus `shipment_covering.go`,
   `shipment_verify.go`, and `archive.go`.

### Does the unreleased work invalidate the F30 premise?

**No — on inspection, but this was checked rather than assumed.** The F30 ruling
depends on covering-feature derivation tolerating a manifest that carries an
additional verified-childless terminal umbrella (`117-F` in `129-S`). On
backlogit's current default branch, `DeriveCoveringFeature` still selects **the
first manifest item, in parent-first order, that is a root feature**, and does
not reject additional root features. The new `deriveCoveringFeatureStrict` is
fail-closed only about *lookup errors*, and is reachable **only** from the
opt-in formal-gate proof digest (`formalGateEnforced()`), which is not enabled
here. So the F30 structural exception holds on both the installed engine and
current source.

**This is not a licence to upgrade mid-flight.** The close-path refactor is
large and was not executed here, so the 66/66 result certifies `fd8d2c9d` only.

> **Ship-facing guard.** Ship closes against whatever is installed *at close
> time*. Before closing `127-S`/`128-S`/`129-S`, re-run
> `sim-shipment-closure.ps1` and confirm the `ENGINE UNDER TEST` block still
> reports commit `fd8d2c9d`. If it reports anything else, the backlogit engine
> was upgraded after this evidence was produced and the close proof must be
> re-established before proceeding — do not rely on this document's result.
