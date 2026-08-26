---
title: "Shipment Closure Cascade Guard — decided plan"
doc_type: decided-plan
status: planned
created: 2026-07-02
feature: "056-F"
tasks: ["056.001-T", "056.002-T", "056.003-T"]
supersedes:
  - docs/archive/plans/2026-07-02-shipment-closure-cascade-guard-plan.md
---

# Decided Plan: Shipment Closure Cascade Guard

**Outcome:** Planned, not shipped. The source plan for feature `056-F` records a harness-side response to the `056-S` closure failure: Ship must stop using cascade `backlogit shipment ship` for partial-feature closure because it can archive a covering feature and unshipped sibling tasks. The chosen fix stays inside harness templates and the installed Ship mirror; it does not attempt to patch the external backlogit binary.

## Decision

Replace Ship's post-merge cascade close with a manifest-scoped, single-artifact safe-close procedure. Ship should enumerate only manifest item IDs, snapshot pre-closure state, archive each manifest item individually, and verify after each archival that the parent feature and every unshipped sibling task remain in queue. If any non-manifest artifact cascades into archive or disappears, revert the unintended backlog mutation and halt with a P-005 violation rather than committing corrupt backlog state.

## Implementation (3 tasks)

- **056.002-T** — add the `safe-close` procedure to `shipment-reconcile` as the source of truth: archive manifest items one by one, verify the invariant after each step, reuse `pre-archived` classification, and keep report-and-halt behavior.
- **056.001-T** — rewrite Ship closure Step 1.b in the template and installed Ship mirror so Ship delegates to `shipment-reconcile` instead of calling the cascade shipment-close operation directly.
- **056.003-T** — codify the rule as a workflow policy forbidding cascade shipment shipping for partial-feature shipments and requiring single-artifact closure with verify-after-each and revert-on-cascade semantics.

The intended order is `056.002-T -> 056.001-T -> 056.003-T` so the agent references an existing safe-close procedure before policy text points at it.

## Key constraints preserved

- Enumerate only the shipment manifest's explicit item IDs; never archive the parent feature ID as part of partial-feature closure.
- Reuse `shipment-reconcile`'s `pre-archived` classification so already-shipped items are not treated as false positives.
- Keep the existing `shipment-reconcile` pre/post gates as defense in depth; only the destructive middle step changes.
- Preserve report-and-halt semantics; do not auto-prune the manifest after detecting a cascade.
- Leave CLI/schema surfaces and the external backlogit binary untouched.

## Rejected alternatives

- **Keep using cascade `backlogit shipment ship`** — rejected because `056-S` showed it can archive non-manifest artifacts and corrupt the backlog.
- **Patch backlogit here** — rejected because the bug lives in the external backlogit binary, not in autoharness.
- **Silently continue or auto-clean after a cascade** — rejected because the plan requires explicit revert + halt to prevent committing corrupted backlog state.
- **Retroactive repair of already-archived items** — rejected as out of scope for this fix.

## Verification expectations

- Walk the `056-S` scenario against the new procedure and confirm the parent feature and unshipped siblings survive closure.
- Run template quality gates: valid frontmatter, markdown structure, resolved variables, and cross-reference integrity.
- Run verify-harness for overlay coherence after the template changes land.