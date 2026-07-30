---
title: Multi-Shipment Dark-Factory Sequencing Hardening — decided plan
doc_type: decided-plan
status: shipped
created: 2026-07-30
feature: 101-F
tasks: 101.001-T, 101.002-T, 101.003-T, 101.004-T
shipment: 105-S
source_stash_id: 60C57761
grounding_decision: backlogit spike 001-SP (DEFER standalone ship_sequence.jsonl; reuse queue + item_deps)
supersedes: docs/archive/plans/2026-07-30-multi-shipment-dark-sequencing-plan.md
---

# Decided Plan: Multi-Shipment Dark-Factory Sequencing Hardening

**Outcome:** Shipped as feature `101-F` / shipment `105-S` (tasks
`101.001-T`..`101.004-T`), PR #266, merge commit
`59a4551b5bead5d86dc18cbb05af27cf9e602c25` (merged 2026-07-30T23:46:25Z; two
parents, P-009 merge commit). Plan-review verdict: **PASS**, P0 = 0, P1 = 0
(two P2 resolved in-plan). P-006 hardening required and present. This
decided-plan replaces the verbose original (problem frame, requirements trace,
full unit specs, risks, hardening, and inline seven-persona review), archived
for traceability at
`docs/archive/plans/2026-07-30-multi-shipment-dark-sequencing-plan.md`.

## Problem (settled)

During a long-running P-017 dark run the Orchestrator parcels a chosen/calculated
sequence of queued shipments one-by-one. Three template surfaces under-specified
how that sequence is authored, selected, and audited: (1) Orchestrator selection
was priority-only ("highest-priority queued shipment"); (2) `DARK_MODE_SCOPE`
recorded an unordered set with no restart cursor; (3) no shipment-sequencing
authoring playbook existed. Grounding decision (backlogit spike `001-SP`): reuse
`custom_fields.queue_position` + `item_deps` blocks-chains — **no new
`ship_sequence.jsonl` scheduler, no new sequence-manifest file.**

## Decisions (actionable, as shipped)

1. **Reuse `queue_position` + `item_deps`; no standalone scheduler.** Consistent
   with backlogit spike `001-SP` DEFER. The queue and dependency graph already
   express ordering and gating.
2. **`item_deps` suppression is a HARD eligibility gate; `queue_position` orders
   only among already-eligible shipments.** On conflict (queue_position lists A
   before B but A is blocked by B), **eligibility wins** — B is claimed first.
   (Resolves review finding P2-A.)
3. **Selection reconciles with the `blocked` shipment lifecycle**
   (`2026-05-07-backlogit-shipment-status-constraints`): a dependency-gated
   shipment sits at `status: blocked` and returns to `queued` when the gate
   clears. The selection rule operates on `--status queued` (already excluding
   blocked) AND adds an explicit `item_deps` re-check before claim as a
   belt-and-suspenders guard. Both paths are documented so authors pick the right
   one (redundant-by-design, not duplication — P3-A).
4. **`queue view` is a first-pass filter, not the eligibility authority and not a
   sequence-reconstruction source.** It returns only the currently eligible head
   (queue_position first, then priority) and withholds `status: blocked`
   shipments. Reconstructing the full ordered sequence (for the P-017 scope +
   restart cursor) requires listing across **both `queued` and `blocked`
   statuses** (or an unfiltered listing) then traversing the `item_deps`
   blocks-chain — a queued-only listing truncates the chain.
5. **Four tasks, one per template + a terminal coherence sweep.** Each edit is a
   single file / single skill domain; cross-set coherence is validated only after
   all three edits exist, so U4 is a distinct terminal milestone.
6. **No new template variables** (reuse `{{STATUS_QUEUED}}`); install-harness
   SKILL.md variable-resolution table untouched. Verified counts unchanged:
   orchestrator 11, workflow-policies 9, backlogit.instructions 0.

## Implementation units (surviving review, as shipped)

- **U1 / 101.001-T** — Queue-ordering-aware Orchestrator selection. Rewrote Step 2
  "Route to Ship" rule #1 in `templates/agents/_orchestrator.agent.md.tmpl`:
  `queue view --type shipment --status queued` first-pass candidate (queue_position
  order, withholds blocked) → constrain to the P-017 `DARK_MODE_SCOPE` ordered
  cursor (halt rather than substitute an out-of-scope global queue head:
  no-silent-scope-expansion) → explicit `item_deps` + status re-check before claim.
  Rule #2 (P-001/P-016/P-020 closure guard) preserved verbatim. Edited the
  source-controlled dogfood mirror `.github/agents/_orchestrator.agent.md` and
  regenerated its checksum in `.autoharness/harness-manifest.yaml`.
- **U2 / 101.002-T** — `templates/policies/workflow-policies.md.tmpl` P-017:
  activation-contract item 1 records the ordered shipment sequence;
  `DARK_MODE_SCOPE` carries restartable resume/audit evidence (ordered list, last
  completed, next to claim) derived from queue + item_deps, no new scheduler.
  Reconstruction caveat documented. Scope rule + P-001 relationship preserved.
- **U3 / 101.003-T** — Shipment Sequencing Protocol added to
  `templates/instructions/backlogit.instructions.md.tmpl` (adjacent to Queue and
  Dependency Protocol): select-eligible (queue view + item_deps re-check),
  reconstruct-sequence (list queued+blocked + traversal), `dep add <next> <prev>
  --type blocks`, honor queue_position, `dep_type` collapses to `blocks` on
  sync/rehydrate, and the blocked-status-lifecycle vs item_deps blocks-chain
  reconciliation note. No new variable.
- **U4 / 101.004-T** — Cross-reference coherence + multi-profile validation
  sweep (validation-only). Rendered all three templates against Rust / TypeScript
  / Python fixtures (9 renders): valid Markdown, MD001/MD025/MD041 heading
  hierarchy clean, 0 unresolved `{{...}}`, no new variable. Reciprocal
  cross-references across the set verified.

## Dependency DAG (as executed)

`U1 → {U2, U3}`; `{U2, U3} → U4` (U4 also depends on U1). U1 is the anchor; U4 is
terminal.

## Rejected alternatives

- **Standalone `ship_sequence.jsonl` scheduler / sequence-manifest file** —
  rejected per backlogit spike `001-SP` DEFER; the queue + dependency graph
  already express ordering and gating. Adding one would create a parallel
  scheduler to keep in sync.
- **Priority-only selection** — the original behavior; rejected because shipments
  rarely carry priority, making "highest-priority" effectively arbitrary and
  order-blind.
- **`queue view` as the sequence-reconstruction source** — rejected; it hides
  blocked successors and returns only the eligible head, so it truncates the
  ordered chain.
- **U4 authoring "minor coherence touch-ups"** — rejected (P2-B); U4 is
  validation-only, non-trivial fixes route back to the owning unit to keep
  authorship in one place and prevent scope drift.

## Constraints preserved

- 097-S task-only manifest (items = task IDs only; covering feature `101-F`
  derived via `parent_id`, never listed).
- Tool-agnostic contract: shared agent/policy templates describe abstract
  operations; concrete backlogit recipes live only in the backlogit overlay
  (`backlogit.instructions.md.tmpl`). (Enforced through Copilot rounds 1–2.)
- No new `{{VARIABLE}}`; dogfood mirror + manifest checksum regenerated for every
  Orchestrator edit.

## Rollback

`git revert` the merge commit `59a4551` (or the specific template + installed
mirror + manifest-checksum commits). Documentation/template text only — no data
migration, no runtime state.
