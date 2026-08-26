---
title: "Implementation Plan — Model-Routing Hierarchy + Dynamic Reload (F02FD596 + E8B5B3C5)"
date: "2026-08-07"
description: "Implementation plan for nested per-role escalation routing (F02FD596) and session-start dynamic config reload (E8B5B3C5), with fail-closed migration and P-013.5/P-013.6 compatibility."
doc_type: plan
source: docs/archive/plans/2026-08-07-model-routing-hierarchy-dynamic-reload-plan.md
stash_ids: ["F02FD596", "E8B5B3C5"]
model_route:
  model_family: claude-opus-4.8
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/decisions/2026-08-07-model-routing-hierarchy-dynamic-reload-deliberation.md"
  - "schemas/harness-config/1.0.0.schema.json"
  - "src/autoharness/verify_workspace.py"
tags: ["model-routing", "F02FD596", "E8B5B3C5", "plan"]
---

# Implementation Plan — Model-Routing Hierarchy + Dynamic Reload

## Objective

Correct the flat `model_routing.escalation` to a nested per-role hierarchy
(F02FD596) and add session-start dynamic config reload (E8B5B3C5), preserving
P-013.5/P-013.6 and the ESCALATION_DEGRADED guard, failing closed on ambiguous
legacy configuration.

## Affected surfaces (verified)

* `schemas/harness-config/1.0.0.schema.json` and `schemas/harness-config.schema.json`
* `src/autoharness/verify_workspace.py` (loader/resolver/verification)
* `templates/instructions/escalation-protocol.instructions.md.tmpl`,
  `templates/agents/_ship.agent.md.tmpl`, `_stage.agent.md.tmpl`,
  `_orchestrator.agent.md.tmpl`, `templates/policies/workflow-policies.md.tmpl`
* `.autoharness/config.yaml` (dogfood data — **operator-confirmed at Ship**)

## Work decomposition (F02FD596 first, then E8B5B3C5)

### F02FD596 — nested per-role escalation (bug)

* **T1 (schema)**: add `ship.escalation` + `stage.escalation` nested objects to both
  schema files (`{model_provider?, model_family?, reasoning_effort?}`,
  `additionalProperties:false`); keep flat `escalation` as **deprecated-legacy**;
  encode the both-present ambiguity as invalid via schema `not`/`oneOf` where
  expressible, otherwise enforced in loader (T2).
* **T2 (resolver + fail-closed)**: implement escalation resolution precedence
  (`<role>.escalation` → flat legacy → per-field `tier3`); both-present →
  fail-closed ERROR/halt; preserve ESCALATION_DEGRADED same-route guard vs the acting
  role's own resolved route.
* **T3 (templates + verify + migration doc)**: update escalation-protocol/agent/
  workflow-policy templates to describe nested per-role escalation + deprecation of
  flat; update `verify_workspace.py` checks; author a flat→nested migration note with
  the fail-closed both-present rule. No dogfood data values written here.

### E8B5B3C5 — session-start dynamic reload (feature; depends on F02FD596)

* **T4 (reload + cache invalidation)**: at session start, re-read + schema-validate
  `.autoharness/config.yaml`, re-resolve role + nested escalation routes, invalidate
  cached/baked route state.
* **T5 (degraded/fail-closed + propagation + tests)**: on invalid/missing config →
  halt to operator (no stale-route run); propagate resolved route as invocation-time
  directive to agents and inherited skills (P-013.5) and escalation directive
  (P-013.6); add verification/tests; confirm no P-013 tier regression.

## Dependencies

* T2 → T1; T3 → T1; T4 → T2; T5 → T4. (E8B5B3C5's T4 depends on F02FD596's resolver,
  encoding bug-before-feature.) Acyclic.

## Width isolation / 2-hour rule

Schema (T1), resolver (T2), and template/verify (T3) are separated so no task mixes
schema evolution with template families or loader logic. Reload (T4) and
degraded/propagation (T5) are separated. Each task is a single concern targeting < 2
human-hours.

## Verification / DoD

* Schema validates nested routes; both-present config rejected (fail closed).
* Resolver precedence + same-route ESCALATION_DEGRADED guard covered by tests.
* Legacy flat `escalation` still resolves with deprecation warning (no regression to
  this workspace's current escalation).
* Session-start reload re-resolves routes; invalid config halts; P-013.5/P-013.6
  propagation verified.

## Requires plan hardening

**Yes.** Elevated blast radius: JSON-schema evolution, routing semantics the harness
itself depends on (this session's escalation route resolves from `model_routing`),
multiple template families, and a fail-closed migration. See the paired hardening
doc `docs/archive/plans/2026-08-07-model-routing-hierarchy-dynamic-reload-hardening.md`.
