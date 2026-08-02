---
title: "Implementation Plan: Telemetry-driven Auto-escalation Protocol (capability 011-DL(b))"
type: impl-plan
date: 2026-08-02
route: claude-opus-4.8 / anthropic / high (P-013.5)
source_stash: 34D50F2D
deliberation: 011-DL
spike: docs/spikes/2026-08-02-telemetry-driven-auto-escalation-protocol-spike.md
feature: 106-F
requires_plan_hardening: yes
hardened: yes
tags:
  - auto-escalation
  - model-routing
  - "P-013.6"
  - verify-workspace
  - external-guard
  - "011-DL"
---

# Implementation Plan — Telemetry-driven Auto-escalation Protocol (106-F)

## Problem

Spec §4 (`docs/product-specs/autoHarness-framework-specifications.md`) calls for
telemetry-driven **auto**-escalation: when an iteration/failure threshold is
crossed, the agent halts, compiles an escalation payload, re-routes to a stronger
escalation model, and hands off terminally to engram. Today (per spike F2) the
Stage/Ship templates only *halt and prompt the operator* — a **manual**
escalation. The automated protocol layer does not exist as autoharness product
prose, and there is no config-resolved escalation route (spike F3), so the
escalation model target cannot be declared environment-agnostically.

## Chosen design (bounded, in-boundary)

Extend the existing escalation seam (spike F2) using the proven P-013.5
named-route pattern (spike F3). The **protocol** lives in autoharness product
artifacts; the runtime trigger-evaluation engine and telemetry emitter/store are
routed OUT via the external-guard pattern (spike F1/F5). Escalation is a
**reasoning** escalation, never an **authority** escalation — it never
self-authorizes merge, shipment claim, or source mutation, and preserves
P-001/P-009/P-014/P-017/P-020.

### Model reconciliation (011-DL Q2 / spike F4)

The `model_routing.escalation` route falls back **per field** to `tier3`
(`claude-opus-4.8`) when unset — escalation must route to *deeper* reasoning than
the failing tier, so the spec's literal "Sonnet 5" is superseded by the
config-resolved route. Ship stays `claude-sonnet-5`; spec's "Ship=Terra" is
advisory and rejected. No regression to the shipped P-013.5 routing.

## Implementation units (each single-family, ≤2h, width-isolated)

| ID | Task | Family | Depends on | Acceptance |
|---|---|---|---|---|
| T1 | Add optional `model_routing.escalation` route to **both** `schemas/harness-config.schema.json` and `schemas/harness-config/1.0.0.schema.json` | schema | — | Route object `{ model_family, model_provider, reasoning_effort }`, `additionalProperties:false`, **no** required fields (mirrors `stage`/`ship`); documented per-field fallback to `tier3`; both schema files validate the existing `.autoharness/config.yaml` unchanged (no regression) |
| T2 | Add `ESCALATION_PROVIDER` / `ESCALATION_FAMILY` / `ESCALATION_REASONING_EFFORT` to the `install-harness/SKILL.md` variable-resolution table with per-field `tier3` fallback | installer/skill docs | T1 | Variable table lists all three with tier3 fallback semantics; no `{{...}}` left unresolved in the table's own examples; consistent with existing `STAGE_*`/`SHIP_*` rows |
| T3 | Author the escalation-payload **contract** (fields the halting agent compiles) as a section in `templates/instructions/role-enforcement.instructions.md.tmpl` (+ installed overlay note) | instruction template | — | Enumerates payload fields: threshold-kind + count, failure summary, last-N action/observation refs, artifact refs, telemetry-evidence pointers (schema `evidence_path`/`artifact_refs`), resumption checkpoint ref; states authority-preservation invariant |
| T4 | Extend **Stage** `_stage.agent.md.tmpl` Stop-Conditions/escalation prose: on consecutive-failure threshold → compile payload (T3) → re-route to config-resolved escalation model → terminal engram handoff → halt | agent template (Stage) | T3 | Auto-escalation directive present; dark-mode-safe; cites P-013.6; preserves existing operator-halt behavior when escalation route unavailable (`ESCALATION_DEGRADED`) |
| T5 | Extend **Ship** `_ship.agent.md.tmpl` "Escalation Protocol — Consecutive Task Failures" with the same auto-escalation directive | agent template (Ship) | T3 | Same as T4 for Ship; does not alter merge/claim authority; `ESCALATION_DEGRADED` fallback to existing operator-prompt |
| T6 | Add `P-013.6 — Telemetry-driven Auto-escalation Protocol` clause to `templates/policies/workflow-policies.md.tmpl` (+ amendment-log bump) | policy template | T3 | Resolve/Declare/Degrade-explicitly/Authority-preservation/External-guard/Violation-Action structure; amendment log version bumped |
| T7 | Add fail-closed `verify_workspace.py` checks: `escalation_route_resolution` (route resolves or falls back to tier3) and `escalation_directive_present` (Stage+Ship templates reference the auto-escalation directive + P-013.6), each gated on file existence | verify CLI | T1, T4, T5 | Both checks registered only when target files exist; unresolved route or missing directive = verification FAIL (fail-closed); no false-fail on default/legacy installs |
| T8 | Add tests for the T7 checks in `tests/test_verify_workspace.py` | tests | T7 | Positive + negative cases for each check; a missing-escalation-route install with tier3 present passes via fallback; a declared-but-unresolvable route fails |
| T9 | External-guard boundary decision doc under `docs/decisions/` recording what is routed OUT (telemetry emitter/store, MAX_ITERATIONS runtime evaluator) and why | docs | — | Names OUT scope, cross-refs spike F1/F5 and external-guard precedent (2970FA4E); states re-entry criteria if runtime substrate later ships |

**Add order (parent-first, dependency-topological):** 106-F → T1 → T2 → T3 →
T4 → T5 → T6 → T9 → T7 → T8.

## Plan Hardening (P-006) — required (elevated blast radius)

**Blast-radius signals:** two JSON schema files (config schema family), CLI
installer variable contract, three template families (agent × 2, instruction,
policy), and `verify_workspace.py` + tests. Multi-family + schema ⇒ `requires_plan_hardening: yes`.

### Failure modes & mitigations
- **Schema over-tightening regresses existing installs.** Mitigation: `escalation`
  is *optional* with `additionalProperties:false` and **no required fields**;
  T1 acceptance requires the unchanged `.autoharness/config.yaml` to still
  validate against both schema files.
- **verify check false-fail on legacy/default installs.** Mitigation (mirrors the
  104-F `model_provider` lesson): checks are **existence-gated** and route
  resolution passes via **tier3 fallback**; T8 negative test asserts a
  no-escalation-route install passes.
- **Authority-escalation drift** (agent auto-escalates privilege). Mitigation:
  T3/T4/T5/T6 all encode the *reasoning-not-authority* invariant; escalation
  terminal state is halt + engram handoff, never merge/claim/mutation.
- **Dark-mode policy bypass.** Mitigation: directive explicitly preserves
  P-001/P-009/P-014/P-017/P-020; `ESCALATION_DEGRADED` falls back to the existing
  operator-halt rather than proceeding autonomously.
- **Scope creep into the runtime engine.** Mitigation: T9 external-guard doc
  fixes the OUT boundary; no task touches telemetry emitter/store or
  backlogit/engram binaries.

### Rollback
Each task is an isolated additive change. Revert order is reverse-topological
(T8→T1); schema (T1) and verify (T7) reverts are independently safe because both
are additive and fallback-preserving. No data migration; config remains
backward-compatible.

### Residual risks (operator-visible, non-blocking)
1. The **runtime trigger evaluator** remains external — the protocol is inert
   until a telemetry emitter/store exists (candidate deferred; documented in T9).
2. `engram` terminal handoff depends on the engram tool surface being available
   at escalation time; `ESCALATION_DEGRADED` covers its absence.
3. Escalation-route default (tier3) may cost more compute per escalation; operators
   can point the route at a cheaper model — documented in T2.

## Out of scope (external-guard, spike F1/F5)
- Live telemetry event emitter / sink / queryable store.
- Runtime MAX_ITERATIONS counter / automated threshold-evaluation engine.
- Any change to `backlogit` / `agent-engram` external binaries.
- Candidates 011-DL (a)/(c)/(d) — remain deferred in stash `34D50F2D`.

## Traceability
`34D50F2D` (stash) → `011-DL` (deliberation) → this spike/plan → `106-F` (feature)
→ queued shipment. Stash stays **active** (only candidate (b) promoted).
