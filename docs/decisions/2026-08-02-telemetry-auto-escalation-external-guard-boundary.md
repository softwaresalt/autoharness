---
title: "External-guard boundary for the Telemetry-driven Auto-escalation Protocol"
description: "Records what is routed OUT of autoharness for capability 011-DL(b): the live telemetry event emitter/sink/store, the runtime MAX_ITERATIONS threshold-evaluation engine, and any backlogit/agent-engram binary changes. States the protocol is dormant until a runtime telemetry substrate ships and defines re-entry criteria."
topic: "What stays IN the autoharness product boundary for auto-escalation (P-013.6), and what is explicitly routed OUT to runtime/external concerns?"
depth: "standard"
decision_status: "accepted"
doc_type: decision
source: docs/decisions/2026-08-02-telemetry-auto-escalation-external-guard-boundary.md
source_stash_ids:
  - "34D50F2D"
deliberation: "011-DL"
spike: docs/spikes/2026-08-02-telemetry-driven-auto-escalation-protocol-spike.md
plan: docs/plans/2026-08-02-telemetry-driven-auto-escalation-protocol-plan.md
backlog_items:
  - "106-F"
  - "106.009-T"
  - "110-S"
linked_artifacts:
  - "schemas/harness-config.schema.json"
  - "schemas/harness-config/1.0.0.schema.json"
  - "templates/instructions/escalation-protocol.instructions.md.tmpl"
  - "templates/agents/_stage.agent.md.tmpl"
  - "templates/agents/_ship.agent.md.tmpl"
  - "templates/policies/workflow-policies.md.tmpl"
  - "schemas/tool-telemetry-event.schema.json"
tags:
  - "auto-escalation"
  - "external-guard"
  - "011-DL"
  - "P-013.6"
---

# External-guard Boundary — Telemetry-driven Auto-escalation Protocol (106-F)

## Decision

For deliberation `011-DL` capability (b) — telemetry-driven auto-escalation —
autoharness ships the **protocol contract only**: the escalation-payload
schema/prose, the config-resolved `model_routing.escalation` route (P-013.6),
the agent-template auto-escalation directive, and fail-closed verification.
The following are explicitly **routed OUT** of this repository as
external-guard concerns and are **not** built as part of 106-F/110-S:

1. **The live telemetry event emitter / sink / queryable store.**
   `schemas/tool-telemetry-event.schema.json` (`ToolTelemetryEvent v1.0`)
   states verbatim that it is *"a forward contract only … no live Python
   event model, no event emitter, no event sink, no event-to-epoch composer,
   and no queryable event store."* Building any of those would be a runtime
   subsystem, not a template/schema/policy artifact autoharness distributes.
2. **The runtime `MAX_ITERATIONS` / threshold-evaluation engine** that
   automatically *fires* the escalation trigger. Agent-observable
   failure/iteration counts already exist as prose (each pipeline agent's own
   Stop Conditions table); an automated numeric evaluator that watches those
   counts and fires without agent participation is a runtime concern outside
   the templates-are-the-product boundary.
3. **Any change to the `backlogit` or `agent-engram` external binaries.** The
   terminal engram handoff described by the protocol uses the existing engram
   tool surface (MCP tools / file-based fallback) exactly as already exposed;
   no new binary capability is requested or assumed.

## Rationale

* **Global-tool / local-output boundary.** autoharness is a globally-installed
  agent harness framework; its product is templates, schemas, skills, and
  documentation — never a standing runtime service. A live telemetry
  emitter/store or a numeric threshold-evaluation daemon would cross that
  boundary into application-runtime territory.
* **Spike evidence (F1, F5).** `docs/spikes/2026-08-02-telemetry-driven-auto-escalation-protocol-spike.md`
  F1 draws the hard scope line at the telemetry schema's own forward-contract
  disclaimer; F5 requires the protocol to remain policy-preserving under P-017
  (dark factory) — a reasoning escalation, never an authority escalation. Both
  findings depend on the trigger *evaluation* and *emission* machinery staying
  external so the in-repo protocol cannot itself mutate authority or invent a
  parallel runtime.
* **External-guard precedent (stash `2970FA4E`).** This repository has an
  established precedent of carving out backlogit/engram-internal or
  runtime-only concerns from otherwise-adjacent capability work and routing
  them upstream/external rather than building them locally — see stash
  `2970FA4E`'s deferred carve-outs (a `backlogit`-internal `active→queued`
  transition guard explicitly routed **upstream to the backlogit project**
  because backlogit is an external binary, and a decision-gated self-repair
  capability withheld pending an operator policy decision), documented at
  `docs/decisions/2026-07-30-ship-claim-integrity-preflight-spike.md` and
  carried through `docs/compound/2026-08-01-shipment-record-status-integrity.md`.
  The same discipline — draw the product boundary at "what autoharness can
  author as portable artifacts" and route the rest out — applies here to the
  telemetry emitter/store and the runtime evaluator.

## Dormant-until-runtime status (non-negotiable framing)

P-013.6 and the escalation-protocol instruction are **inert** as installed:
without a live telemetry emitter/store and threshold-evaluation engine, no
automated trigger ever fires the protocol. The **existing manual
operator-halt behavior** (each pipeline agent's Stop Conditions table) remains
the actual, effective behavior today. This is not a stub or a fake feature —
the payload contract, route resolution, and `ESCALATION_DEGRADED` semantics are
real and independently testable (verify_workspace checks, T7/T8) — but
operators must not be misled into believing automated escalation is *live*
before a runtime substrate exists. Every installed artifact that documents this
protocol (P-013.6, `escalation-protocol.instructions.md`, the Stage/Ship
directives) states this dormant status explicitly.

## Re-entry criteria (when a runtime substrate later ships)

Building the routed-out runtime evaluator and telemetry emitter/store becomes
in-scope for a future capability only when **all** of the following hold:

1. A concrete, reviewed proposal establishes *where* the live telemetry
   emitter/sink/store would run (it cannot be an autoharness-distributed
   template — it would need its own hosting story, analogous to how
   `backlogit`/`agent-engram` are separate external binaries autoharness
   integrates with rather than ships).
2. The proposal defines how the runtime evaluator observes agent-side
   failure/iteration counts without granting itself authority beyond what
   P-013.6's authority-preservation invariant already allows the halting agent
   (reasoning escalation only, never authority escalation).
3. A dedicated spike (mirroring this one) re-examines the global-tool /
   local-output boundary for the specific runtime shape proposed, and a
   deliberation records operator sign-off before any implementation plan is
   drafted.
4. The existing P-013.6 protocol contract, escalation-payload schema, and
   `ESCALATION_DEGRADED` semantics are treated as the stable interface the new
   runtime substrate must satisfy — not re-litigated from scratch.

Until then, this boundary decision stands: the protocol contract ships now: the
emitter/store/evaluator remain external-guard, out of scope.

## Cross-references

* Spike: `docs/spikes/2026-08-02-telemetry-driven-auto-escalation-protocol-spike.md`
  (F1 — telemetry forward-contract-only boundary; F5 — dark-mode/P-017
  authority-preservation compatibility).
* Plan: `docs/plans/2026-08-02-telemetry-driven-auto-escalation-protocol-plan.md`
  ("Out of scope (external-guard, spike F1/F5)").
* External-guard precedent: stash `2970FA4E`
  (`docs/decisions/2026-07-30-ship-claim-integrity-preflight-spike.md`,
  `docs/compound/2026-08-01-shipment-record-status-integrity.md`).
* Policy: P-013.6 in `templates/policies/workflow-policies.md.tmpl`.
