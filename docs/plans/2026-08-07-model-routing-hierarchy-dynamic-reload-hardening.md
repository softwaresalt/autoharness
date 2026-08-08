---
title: "Plan Hardening — Model-Routing Hierarchy + Dynamic Reload (F02FD596 + E8B5B3C5)"
date: "2026-08-07"
description: "P-006 plan hardening for the model-routing hierarchy + dynamic reload plan. Enumerates blast-radius controls, fail-closed invariants, backward-compatibility guarantees, and de-risking for high-complexity tasks."
doc_type: plan-hardening
source: docs/plans/2026-08-07-model-routing-hierarchy-dynamic-reload-hardening.md
stash_ids: ["F02FD596", "E8B5B3C5"]
model_route:
  model_family: claude-opus-4.8
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/plans/2026-08-07-model-routing-hierarchy-dynamic-reload-plan.md"
tags: ["P-006", "hardening", "model-routing", "F02FD596", "E8B5B3C5"]
---

# Plan Hardening (P-006) — Model-Routing Hierarchy + Dynamic Reload

## Blast-radius summary

Schema evolution (two schema files) + loader/resolver semantics + five template
surfaces + the routing config the harness *itself* consumes for role and escalation
routing. A defective change could mis-route or silently degrade escalation for every
agent, including the acting agent. Hence hardening is REQUIRED.

## Hardening items

* **H1 — No-regression for the current flat escalation.** The existing flat
  `model_routing.escalation` (this workspace: `gpt-5.6-sol/high`) MUST continue to
  resolve for all roles with only a deprecation warning. Add a regression test that
  loads the *current* dogfood config unchanged and asserts identical escalation
  resolution. (De-risks T2/T4 high complexity.)
* **H2 — Both-present fail-closed.** When flat `escalation` AND any nested
  `<role>.escalation` coexist, the loader MUST raise a hard error and halt (no silent
  precedence). Negative test required. Never auto-pick a winner.
* **H3 — ESCALATION_DEGRADED guard preserved and role-scoped.** The same-route no-op
  guard MUST compare the resolved escalation tuple to the **acting role's own resolved
  route** (not a global route). Test: a role whose escalation equals its own route →
  ESCALATION_DEGRADED → operator-halt fallback, never a silent same-model "escalation".
* **H4 — Per-field fallback integrity.** Missing sub-fields of a nested escalation
  fall back per-field to `tier3` (not whole-object), matching the existing flat-route
  contract. Test each sub-field independently.
* **H5 — additionalProperties:false parity.** Nested escalation objects MUST keep
  `additionalProperties:false` to prevent typo'd keys silently ignored (a routing
  safety hazard). Schema test for an unknown key → invalid.
* **H6 — Reload fail-closed (no stale routes).** On invalid/missing/schema-failing
  config at session start, the harness MUST halt to operator; it MUST NOT continue on
  baked/stale routes and MUST NOT invent a last-known-good. Test invalid-config →
  halt. (De-risks T4/T5 high complexity.)
* **H7 — P-013.5/P-013.6 propagation.** Freshly resolved routes MUST propagate to
  invoked agents and inherited skills (invocation-time directive) and to the
  escalation directive; a stale directive after reload is a defect. Test propagation
  end-to-end.
* **H8 — Dogfood data change gated.** Writing concrete escalation values
  (terra/sonnet-5) into `.autoharness/config.yaml` is a separate, operator-confirmed
  step at Ship; the structural tasks MUST NOT write dogfood escalation data values.
* **H9 — Schema version discipline.** Additive nested fields are backward-compatible;
  bump/annotate schema per the repo's schema-versioning convention; do not remove or
  rename existing `escalation`/`ship`/`stage` fields.

## High-complexity de-risking (two-axis gate)

Tasks T2, T4, T5 are `complexity: high`. This hardening doc is their required
de-risking artifact: each high-complexity task carries the specific H-items above as
acceptance criteria (H1–H5 for T2; H6/H7 for T4/T5). Sizes are held at ≤ M so each
remains within the 2-hour execution bound; the uncertainty is retired by the
enumerated invariants and mandatory negative tests rather than by further splitting.

## Residual risk

Low-to-moderate after hardening. The dominant residual risk (mis-attributing a
legacy flat route to a role) is eliminated by H2's fail-closed rule. The self-
referential risk (this session's own escalation) is covered by H1's unchanged-config
regression test.
