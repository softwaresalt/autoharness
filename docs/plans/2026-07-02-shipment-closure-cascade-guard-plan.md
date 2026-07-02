---
title: "Shipment Closure Cascade Guard — Implementation Plan"
description: "Harness-side guard so Ship post-merge closure never uses cascade `backlogit shipment ship`; closes shipments via single-artifact status moves with a verify-after-each invariant + git-revert-on-cascade. Decomposed into three width-isolated tasks."
source_documents:
  - "docs/decisions/2026-07-02-shipment-closure-cascade-guard-deliberation.md"
feature: "056-F"
tasks:
  - "056.001-T"
  - "056.002-T"
  - "056.003-T"
source_stash_ids:
  - "86F19EF7"
scope: "harness templates + installed ship mirror (no CLI/schema changes)"
tags:
  - "reliability"
  - "closure"
  - "ship-agent"
  - "backlogit"
  - "harness-guard"
---

## Problem Frame

The Ship agent's post-merge closure (Step 1.b) calls `{{OP_SHIP_SHIPMENT_MCP}}`
(`backlogit shipment ship`), which cascade-archives the covering feature and any
unshipped siblings even for partial-feature shipments. This corrupted the
backlog during `056-S` closure (archived parent `055-F`; orphaned `055.001-T`,
`055.003-T`). The external backlogit binary owns the bug and cannot be patched
here. See the deliberation for the full analysis and the decision to adopt
**single-artifact closure with a verify-after-each invariant + git-revert-on-cascade**
(Option C).

## Design

Closure becomes a manifest-scoped, single-artifact procedure:

1. **Enumerate** only the shipment manifest's explicit item IDs (never the
   parent feature ID, which partial-feature shipments already exclude).
2. **Snapshot** the pre-closure archive/queue state (git-clean baseline).
3. **For each manifest item ID**, move it to `{{STATUS_DONE}}` and archive that
   single artifact.
4. **Verify-after-each invariant**: confirm the parent feature file and every
   unshipped sibling task file are still present in
   `{{BACKLOG_DIRECTORY}}/queue/` (not moved to archive, not deleted). Reuse the
   `shipment-reconcile` `pre-archived` classification so legitimately
   already-shipped items are not false-positives.
5. **git-revert-on-cascade**: if any non-manifest artifact was archived/deleted,
   `git restore`/`git revert` the unintended change and halt with a P-005
   violation event; do not commit a corrupt backlog.
6. **Commit** the archival of only the manifest items.

The existing `shipment-reconcile` pre/post gates remain as defense-in-depth; the
new procedure replaces the destructive cascade call between them.

## Task Breakdown

### 056.001-T — Guard ship-agent closure (template + installed mirror)

* Rewrite Ship closure **Step 1.b** in `templates/agents/.ship.agent.md.tmpl`
  (currently `Call {{OP_SHIP_SHIPMENT_MCP}} ... This archives all queue items
  (feature + tasks)`) to invoke the single-artifact safe-close procedure
  (delegated to `shipment-reconcile`, per 056.002-T) with the verify-after-each
  invariant and git-revert-on-cascade.
* Mirror the guidance into the installed `.github/agents/.ship.agent.md`
  closure step (currently `Close the shipment via backlogit_ship_shipment` at
  ~L260) so the dogfooded harness matches the template.
* **Acceptance**: no cascade ship op for partial-feature shipments; archives
  only shipment item IDs individually with invariant verify + revert; template
  and installed mirror agree; the 056-S scenario is prevented.
* **Width**: ship-agent concern (markdown template + its installed mirror).

### 056.002-T — Single-artifact safe-close procedure in shipment-reconcile

* Add a `safe-close` procedure/mode to
  `templates/skills/shipment-reconcile/SKILL.md.tmpl`: archive each manifest
  item individually, verify-after-each that no non-manifest artifact was
  archived/deleted, and recommend `git restore`/`git revert` on cascade
  detection. Preserve report-and-halt semantics; no auto-prune of the manifest.
* **Acceptance**: the skill documents the safe-close procedure with per-item
  invariant verification and a cascade-revert recommendation, invoked from Ship
  Step 1 in place of the cascade op.
* **Width**: skill template concern.

### 056.003-T — Workflow policy prohibiting cascade shipment-ship

* Add a new policy (next available ID, e.g. **P-015**) to
  `templates/policies/workflow-policies.md.tmpl` prohibiting cascade
  `{{OP_SHIP_SHIPMENT_MCP}}` for partial-feature shipments and requiring
  single-artifact closure with a verify-after-each invariant +
  git-revert-on-cascade. Update the version-history table; cross-reference
  P-007.
* **Acceptance**: policy with precondition/gate-point/postcondition/
  violation-action; version-history updated; ship template references it at the
  closure gate.
* **Width**: policy template concern.

## Sequencing

`056.002-T` (skill procedure = source of truth) → `056.001-T` (ship agent
delegates to it) → `056.003-T` (policy codifies it). All three are independent
enough to build in one shipment; the recommended order avoids referencing a
skill procedure that does not yet exist.

## Verification

* Template quality gates: valid YAML frontmatter, markdown heading hierarchy
  (P-008), no unresolved `{{...}}` after resolution, cross-references resolve.
* Behavioral check: walk the `056-S` scenario against the new procedure and
  confirm the parent feature and unshipped siblings survive closure.
* Multi-model adversarial verification (verify-harness) on the changed
  templates for overlay coherence and cross-reference integrity.

## Out of Scope

* No changes to the external backlogit binary.
* No CLI or schema changes (`src/autoharness/`, `schemas/` untouched).
* Retroactive repair of already-archived items is not part of this plan.
