---
title: "model_routing Construct 1 Removal — decided plan"
doc_type: decided-plan
status: planned
created: 2026-07-02
feature: "053-F"
shipment: "058-S"
tasks:
  - "053.001-T"
  - "053.002-T"
  - "053.003-T"
supersedes: docs/archive/plans/2026-07-02-model-routing-construct1-removal-plan.md
---

# Decided Plan: model_routing Construct 1 Removal

**Outcome:** Feature `053-F` was narrowed to the safe, P-013-preserving removal of
legacy per-agent frontmatter `model_routing` strings for planned shipment `058-S`.
The source artifact records the operator's Construct 1 clarification and the
Construct 2 deferral, but no plan-review verdict, PR, merge commit, or shipment
evidence, so this decided-plan remains **planned**. This replaces the verbose
original, archived for traceability at `docs/archive/plans/2026-07-02-model-routing-construct1-removal-plan.md`.

## Decisions

1. **Treat `model_routing` as two different constructs.** Construct 1 is the
   legacy per-agent frontmatter string; Construct 2 is the active config object
   that still drives P-013 tier-to-model binding.
2. **Execute the safe half only.** The adopted path is the deliberation's hybrid:
   remove Construct 1 now, but defer Construct 2 until the active config binding
   has an explicit replacement decision.
3. **Carry forward stash `0CF1D6CF` instead of discarding it as drift.** The
   `.stage`, `.ship`, and `_orchestrator` mirrors keep the intentional metadata
   backfills (`model_tier`, `max_subagent_tier`, `reasoning_effort`,
   `model_provider`, `model_family`) before the deprecated field is removed.
4. **Keep the scope tightly bounded.** `.mcp.json` is excluded as local
   environment drift, and historical docs/spec/compound updates stay out of scope
   until the Construct 2 decision is made.
5. **Keep shipment `058-S` task-only.** Tasks `053.001-T`..`053.003-T` form the
   planned shipment; deferred `053.004-T` keeps feature `053-F` active afterward.

## Implementation (3 tasks + 1 deferred)

| Task | Scope |
|---|---|
| 053.001-T | Apply the intentional installed-agent frontmatter backfills and remove the deprecated `model_routing` line from `.stage`, `.ship`, and `_orchestrator` mirrors |
| 053.002-T | Remove the deprecated `model_routing:` frontmatter line from the affected `templates/agents/**/*.agent.md.tmpl` files while preserving `model_tier` and other live fields |
| 053.003-T | Reconcile Construct 1 prose in policy / doc-review templates so they no longer imply the legacy frontmatter string still exists |
| 053.004-T (deferred) | Decide what replaces the active Construct 2 config binding, reconcile schema-version skew, and only then touch config/schema/template surfaces |

## Key constraints preserved

- Every affected agent/template already declares `model_tier`; removing Construct 1
  never strips an agent's only tier marker.
- The template `model_routing:` line is a literal string, not a `{{VARIABLE}}`, so
  removal does not orphan installer variables.
- Construct 2 bindings (`{{MODEL_ROUTING_TIER*}}`, `{{TIER_*_*}}`,
  `{{ORCHESTRATOR_*}}`) remain untouched because they resolve from the active
  config object, not the deprecated frontmatter string.
- `.mcp.json` stays out of scope as local drift.
- Shipment `058-S` stays task-only, and the parent feature remains active because
  Construct 2 is intentionally deferred.

## Rejected alternatives

- **Blanket removal of every `model_routing` use, including the active config
  object** — rejected because it would regress shipped P-013 behavior without a
  named replacement binding.
- **Touch `_orchestrator.agent.md.tmpl` Construct 2 example lines or config
  schema/template now** — rejected until the active binding replacement is chosen.
- **Sweep historical docs, specs, compound entries, or memory records now** —
  rejected because those updates are tied to the still-deferred Construct 2
  decision.

## Post-deliberation refinements folded in

- The operator clarified that "the field" means **Construct 1**, not the active
  config object.
- Carry-along stash `0CF1D6CF` made the workflow-agent metadata backfills an
  intentional part of the shipment rather than accidental drift.
- `053.004-T` remains explicitly deferred until the config-binding replacement and
  schema-version-skew decision are supplied.