---
title: "Model-Routing Hierarchy + Dynamic Reload — decided plan"
doc_type: decided-plan
status: planned
created: 2026-08-07
supersedes:
  - docs/archive/plans/2026-08-07-model-routing-hierarchy-dynamic-reload-plan.md
  - docs/archive/plans/2026-08-07-model-routing-hierarchy-dynamic-reload-hardening.md
---

# Decided Plan: Model-Routing Hierarchy + Dynamic Reload

**Outcome:** Stash IDs `F02FD596` and `E8B5B3C5` were consolidated into a single
planned change set covering nested per-role escalation routing plus session-start
dynamic reload. The source artifacts include a paired P-006 hardening pass, but
they do not record a plan-review verdict, shipment, PR, or merge commit, so this
decided-plan remains **planned**. This replaces the separate plan and hardening
artifacts, archived at `docs/archive/plans/2026-08-07-model-routing-hierarchy-dynamic-reload-plan.md` and
`docs/archive/plans/2026-08-07-model-routing-hierarchy-dynamic-reload-hardening.md`.

## Decisions

1. **Fix the hierarchy bug before adding reload behavior.** F02FD596 lands first:
   add nested `stage.escalation` and `ship.escalation` objects while keeping flat
   `model_routing.escalation` as a deprecated legacy fallback.
2. **Resolve escalation by role with explicit precedence.** Resolution order is
   `<role>.escalation` → legacy flat `escalation` → per-field fallback to `tier3`;
   the `ESCALATION_DEGRADED` same-route guard compares against the acting role's
   own resolved route, not a global route.
3. **Fail closed on ambiguous mixed configs.** If flat `escalation` and any nested
   `<role>.escalation` are both present, the loader/schema must reject the config
   and halt rather than silently picking a winner.
4. **Make dynamic reload a session-start re-resolution, not a stale-route reuse.**
   E8B5B3C5 re-reads and schema-validates `.autoharness/config.yaml`, invalidates
   cached/baked route state, and propagates the freshly resolved route to invoked
   agents, inherited skills, and the escalation directive.
5. **Keep structural and data changes separate.** Schema / loader / template tasks
   must not write concrete dogfood escalation values; updating
   `.autoharness/config.yaml` data is a separate, operator-confirmed Ship step.
6. **Keep schema evolution additive.** Nested escalation is added without removing
   or renaming existing `escalation`, `ship`, or `stage` fields.

## Implementation (5 tasks)

| Task | Scope |
|---|---|
| T1 | Add nested per-role escalation objects to both harness-config schema files with `additionalProperties: false` |
| T2 | Implement resolver precedence, fail-closed ambiguity handling, and role-scoped `ESCALATION_DEGRADED` behavior |
| T3 | Update escalation-protocol / agent / workflow-policy templates, verify checks, and migration guidance |
| T4 | Reload `.autoharness/config.yaml` at session start and invalidate cached route state |
| T5 | Fail-closed degraded handling, propagation to agents + inherited skills + escalation directive, and verification/tests |

Execution order is intentional and acyclic: T2/T3 depend on T1; T4 depends on T2;
T5 depends on T4. The feature half (reload) never lands before the routing bug
fix.

## Key constraints preserved

- **H1 — No regression for the current flat escalation:** the existing flat
  `model_routing.escalation` continues to resolve for all roles, with only a
  deprecation warning.
- **H2 — Both-present fail-closed:** flat and nested escalation may not coexist
  silently.
- **H3 — Role-scoped no-op guard:** same-route degradation compares escalation to
  the acting role's own resolved route.
- **H4 — Per-field fallback integrity:** missing nested sub-fields fall back
  per-field to `tier3`, not as a whole-object substitution.
- **H5 — Typo resistance:** nested escalation objects keep
  `additionalProperties: false`.
- **H6 — Reload fail-closed:** invalid or missing config halts to operator; no
  stale-route run and no invented last-known-good.
- **H7 — Fresh propagation:** reloaded routes must propagate through invocation-
  time directives to agents, inherited skills, and escalation.
- **H8 — Dogfood data gating:** structural tasks do not write concrete dogfood
  escalation values.
- **H9 — Schema version discipline:** additive nested fields are backward
  compatible and do not remove existing routing fields.

## Rejected alternatives

- **Silent precedence when flat and nested routes coexist** — rejected because it
  hides ambiguous authority and can mis-route every agent.
- **Compare escalation against a global route** — rejected; the no-op guard must
  be role-scoped to catch same-model "escalations" accurately.
- **Reuse stale or last-known-good routes on invalid reload** — rejected; reload
  is explicitly fail-closed.
- **Write concrete dogfood route values as part of the structural change** —
  rejected because data changes require separate operator-confirmed Ship work.

## P-006 hardening refinements folded in

- Add a regression test that the current dogfood config continues to resolve the
  legacy flat escalation exactly as before.
- Add negative tests for both-present ambiguity and for unknown nested keys.
- Test each missing nested sub-field so fallback stays per-field, not whole-object.
- Test that invalid or missing config at session start halts rather than using
  stale/baked routes.
- Test end-to-end propagation so dynamic reload updates agent, inherited-skill,
  and escalation directives together.
- Keep the high-complexity tasks bounded by attaching these invariants as
  acceptance criteria rather than widening the scope.