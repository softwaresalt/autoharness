---
title: "082-F Implementation Plan — Cross-Pack Measurability Documentation (Engram + graphtor-docs)"
date: "2026-08-07"
description: "Implementation plan decomposing 082-F into documentation/mapping deliverables that formalize the Engram and graphtor-docs telemetry evidence mapping to ToolTelemetryEvent v1.0. Documentation-only; no pack, schema, CLI, or template mutation."
doc_type: plan
source: docs/archive/plans/2026-08-07-082F-cross-pack-measurability-plan.md
backlog_items:
  - "082-F"
model_route:
  model_family: claude-opus-4.8
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/decisions/2026-08-07-082F-cross-pack-measurability-evidence.md"
  - "docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md"
tags: ["082-F", "telemetry", "measurability", "plan"]
---

# 082-F Implementation Plan

## Objective

Formalize the completed cross-pack measurability evidence
(`docs/decisions/2026-08-07-082F-cross-pack-measurability-evidence.md`) into
durable, reviewable documentation deliverables that map real Engram and
graphtor-docs telemetry surfaces to the ratified `ToolTelemetryEvent` v1.0 forward
contract, report adapter gaps, and record sensitivity/redaction guardrails —
**before** any broad pack-adapter emission work (out of scope).

## Scope boundary (non-negotiable)

* **In scope**: documentation authoring under `docs/` mapping pack surfaces to the
  contract; per-metric provenance tables; adapter-gap report; sensitivity/fixture
  decision. Mirrors the 108-F (backlogit) precedent, which produced a mapping
  deliverable, not pack code.
* **Out of scope**: modifying engram/graphtor/backlogit repos; implementing a live
  `ToolTelemetryEvent` model/emitter/adapter; JSON-schema changes; CLI/template
  changes; `agent-intercom` mapping (deferred, no evidence surface this session).

## Context inputs

* Ratified contract: `docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md`
  (`ToolTelemetryEvent` v1.0 field set, provenance maps, correlation-key invariant).
* Evidence: `docs/decisions/2026-08-07-082F-cross-pack-measurability-evidence.md`
  (engram schema v2 `usage.jsonl`; graphtor `SyncMetrics`/`SyncStatus`/freshness).
* Precedent: 108-F `backlogit-telemetry-evidence-mapping` (done).

## Work decomposition (tasks — 2-hour rule, width-isolated)

1. **T1 — Engram measurability mapping doc** (`docs/`): finalize the engram→
   `ToolTelemetryEvent` v1.0 field table, per-metric `metric_sources`/`metric_quality`,
   gaps G-E1..G-E5, and the estimated-token caveat. Single pack, single doc.
   *size S, complexity low.*
2. **T2 — graphtor-docs measurability mapping doc** (`docs/`): finalize the graphtor→
   contract mapping, cycle-vs-event wrapping note, `token economics = unavailable`
   rule, `x-graphtor-*` extension namespacing, gaps G-G1..G-G5. Single pack, single doc.
   *size S, complexity low.*
3. **T3 — Consolidated cross-pack adapter-gap + sensitivity/fixtures report** (`docs/`):
   synthesize engram + graphtor + 108-F backlogit into one adapter-gap matrix, the
   observed/estimated/derived/unavailable/unsafe summary, the redaction/sensitivity
   guardrails, the sanitized-fixtures decision, and the explicit `agent-intercom`
   deferral. Depends on T1 and T2. *size M, complexity medium.*

All three are documentation authoring; each is comfortably < 2 human-hours and
touches no source/schema/CLI/template surface. No task combines pack surfaces with
CLI or schema work (width isolation preserved).

## Dependencies

* T3 depends on (`blocks`) T1 and T2. T1 and T2 are independent and parallelizable
  within the shipment (Ship executes single-active, so effective order T1 → T2 → T3).

## Verification / DoD mapping

* Maps real pack surfaces to the ratified contract with provenance (082-F DoD ✓).
* Identifies observed/estimated/derived/unavailable/unsafe per pack (DoD ✓).
* Reports adapter gaps before broad implementation (DoD ✓).
* Records fixture-safety and redaction guardrails; no raw pack content committed (DoD ✓).
* markdownlint heading hierarchy (P-008); frontmatter valid; cross-references resolve.

## Risks

* Low. Documentation-only; primary risk is contract drift — mitigated by citing the
  ratified ownership doc field-by-field.
* Sensitivity risk (exfiltration of internal paths) — mitigated by the redaction rule
  and synthetic-only fixture decision; enforced in T3.

## Requires plan hardening

**No.** Blast radius is documentation-only: no schema change, no CLI distribution
surface, no template family, no runtime code, no cross-repo mutation. The elevated-
blast-radius triggers (schemas, CLI distribution, multiple template families) are
absent. P-006 hardening not required. (Evidence already gathered read-only; the
sensitivity guardrail is captured as a first-class task AC in T3.)
