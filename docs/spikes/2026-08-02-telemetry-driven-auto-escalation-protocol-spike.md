---
title: "Spike: Telemetry-driven auto-escalation protocol — boundary + feasibility"
type: spike
date: 2026-08-02
route: claude-opus-4.8 / anthropic / high (P-013.5)
source_stash: 34D50F2D
deliberation: 011-DL
capability: "011-DL(b) — telemetry-driven auto-escalation"
status: complete
tags:
  - auto-escalation
  - model-routing
  - telemetry
  - external-guard
  - "011-DL"
---

# Spike — Telemetry-driven Auto-escalation Protocol (capability 011-DL(b))

## Purpose

Deliberation `011-DL` isolated four net-new candidates and required a dedicated
spike per capability before planning. Under the active P-017 dark contract the
operator ordered the pipeline to progress the strongest next capability. This
spike **bounds** capability (b) — telemetry-driven auto-escalation — into a
safe, single-capability, `<2h`-per-task shipment by drawing the autoharness
product boundary (global-tool / local-output, templates-are-the-product) around
it and routing runtime concerns out.

## Capability selection rationale (vs a/c/d)

| Cand. | Capability | Repository fit | Boundary risk | Decision |
|---|---|---|---|---|
| (a) | Unified CLI/MCP action-observation execution abstraction (action/observation loop, sequential pipelining, stderr routing) | Low — fundamentally a **runtime execution engine**; little in-boundary product surface | High — mostly external runtime | Defer |
| **(b)** | **Telemetry-driven auto-escalation (threshold → halt → escalation-payload → escalation-model re-route → terminal engram handoff)** | **High — extends the already-shipped P-013.5 named-route pattern (104-F/108-S) and the existing Ship "Escalation Protocol" seam; expressible as policy + agent-template + config-route + verify prose** | **Low — protocol stays in-product; runtime engine routes out** | **SELECTED** |
| (c) | Background Verification & Compaction layer (log parsing, history summarization, state pruning) | Partial — P-020 already owns post-merge compaction as a closure gate; the background layer is an engram/runtime concern (011-DL open-Q3) | High | Defer |
| (d) | Crash-resumption + context-pruning-on-restore | Partial — checkpoint substrate shipped; core resumption belongs in external backlogit/engram binaries (011-DL open-Q4, external-guard 2970FA4E) | High | Defer |

Selection basis: **repository fit + dependency order + boundedness + value.**
(b) is the only candidate whose net-new surface is predominantly
autoharness **product** artifacts (policy/instruction/agent-template/config-schema/verify),
with its runtime dependency already isolatable behind the external-guard pattern.

## Findings (evidence-grounded)

### F1 — Telemetry is a *forward contract only* (hard scope boundary)

`schemas/tool-telemetry-event.schema.json` (`ToolTelemetryEvent v1.0`) states
verbatim it is *"a forward contract only … no live Python event model, no event
emitter, no event sink, no event-to-epoch composer, and no queryable event
store."* Consequence: an actual runtime loop that **reads** telemetry
thresholds cannot be built as an autoharness template deliverable, and building
the emitter/sink/store would be a large runtime/external concern. **The
escalation *trigger evaluation engine* is therefore OUT of scope** (external-guard).
What stays IN is the **protocol**: the policy/contract that says *when a
threshold is reached, halt → compile an escalation payload → re-route to the
escalation model → hand off terminally to engram*, expressed in product prose +
a config-resolved route + verification.

### F2 — A real escalation seam already exists (extend, don't invent)

`templates/agents/_ship.agent.md.tmpl` already has an **"Escalation Protocol —
Consecutive Task Failures"** section (≈L708) and states (≈L859) *"If the
environment supports model selection, suggest retrying the failing task with a
frontier-tier model."* Stage's Stop-Conditions table likewise halts on 3
consecutive failures and prompts the operator. Today these are **manual,
operator-gated** escalations. Capability (b) is precisely the delta from
*manual halt→prompt* to *automated halt→payload→model-reroute→engram handoff*.
This is a bounded extension of an existing seam, not a greenfield subsystem.

### F3 — The P-013.5 named-route pattern is a ready-made, proven template

`104-F/108-S` shipped optional first-class `model_routing.stage` / `.ship`
routes in both `schemas/harness-config.schema.json` and
`schemas/harness-config/1.0.0.schema.json` (`{ model_family, model_provider,
reasoning_effort }`, `additionalProperties:false`, no required fields), with
**per-field tier fallback** and **fail-closed verify checks**
(`role_route_resolution`, `orchestrator_invocation_routing_directive`). An
`model_routing.escalation` route can reuse this exact pattern verbatim, with
fallback to **tier3** (`claude-opus-4.8`, the strongest shipped reasoning tier).
This keeps templates `{{VARIABLE}}`-parameterized and environment-agnostic
(Core Rule 3) and guarantees no regression for workspaces that never declare an
escalation route.

### F4 — Model-pick reconciliation (011-DL open-Q2)

Spec assigns escalation → "Sonnet 5" and Ship → "Terra/GPT-5.6". Shipped
`.autoharness/config.yaml`: `tier2: claude-sonnet-5`, `tier3: claude-opus-4.8`,
explicit `stage`/`ship` routes (Ship = `claude-sonnet-5`). Reconciliation, per
operator directive (*spec advisory where it conflicts with policy; reconcile
without regressing*):

- **Escalation target is NOT hardcoded to "Sonnet 5."** Escalation implies
  *deeper* reasoning than the failing tier, so the config-resolved
  `model_routing.escalation` route **falls back to `tier3`** (`claude-opus-4.8`)
  when unset. Operators may still point it at any route. The spec's literal
  "Sonnet 5" is superseded by the config-resolved route (repository evidence:
  escalation must not route *down* from Stage's own tier3).
- **Ship = Terra is advisory and rejected.** Shipped `ship: claude-sonnet-5`
  is unchanged. No regression to P-013.5.

### F5 — Dark-mode / P-017 compatibility

Auto-escalation must remain policy-preserving under P-017: it may re-route the
model and hand off to engram, but it MUST NOT self-authorize merge, claim a
shipment, mutate source/templates, or bypass P-001/P-009/P-014/P-020. The
protocol's terminal state is a **halt + engram handoff for operator/next-agent
pickup**, never an autonomous privilege escalation. Escalation is a *reasoning*
escalation, not an *authority* escalation.

## Scope boundary (IN vs OUT)

**IN (autoharness product, this shipment):**
1. Optional `model_routing.escalation` route in both config schemas (tier3 fallback).
2. Installer variable-table entries (`ESCALATION_PROVIDER` / `ESCALATION_FAMILY`
   / `ESCALATION_REASONING_EFFORT`) with tier3 fallback.
3. Escalation-payload **contract** (fields a halting agent compiles: threshold
   kind + count, failure summary, last-N action/observation refs, artifact refs,
   telemetry-evidence pointers, resumption checkpoint ref).
4. Agent-template escalation **directive** extending the existing Stage + Ship
   Escalation Protocol from *halt→prompt* to *halt→compile-payload→re-route to
   config-resolved escalation model→terminal engram handoff* (environment-agnostic;
   dark-mode-safe; authority-preserving).
5. New policy sub-clause (P-013.6 — Telemetry-driven Auto-escalation Protocol)
   in `workflow-policies.md.tmpl` + amendment-log bump.
6. Fail-closed `verify_workspace.py` checks (escalation-route resolution;
   escalation-directive presence) + tests, mirroring 104-F.
7. External-guard note documenting what is routed OUT.

**OUT (routed to runtime/external — external-guard, NOT this shipment):**
- The live telemetry **event emitter / sink / queryable store** (F1).
- The runtime **MAX_ITERATIONS counter / threshold-evaluation engine** that
  *fires* the trigger (agent-observable failure/iteration counts already exist
  as prose; the automated numeric evaluator is a runtime concern).
- Any change to `backlogit`/`agent-engram` external binaries (engram handoff
  uses the existing tool surface only).

## Open questions resolved for planning

- **011-DL Q1 (lead capability):** (b), per selection table above.
- **011-DL Q2 (model picks):** F4 — config-resolved escalation route, tier3
  fallback; Ship stays `claude-sonnet-5`; spec picks advisory.
- **011-DL Q3/Q4 (Verification&Compaction / crash-resumption boundary):**
  out of scope for this capability; remain deferred candidates (c)/(d).

## Recommendation

Proceed to `impl-plan` for capability (b) with the IN scope above. Blast radius
is **elevated** (two config schemas + installer + multiple template families +
verify/tests) → **P-006 plan hardening is required** before plan-review.
Candidates (a)/(c)/(d) and their model/boundary questions remain unresolved in
stash `34D50F2D`, which stays **active** (partially consumed).
