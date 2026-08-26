---
title: "082-F Cross-Pack Measurability Documentation"
doc_type: decided-plan
status: planned
created: 2026-08-07
feature: "082-F"
supersedes:
  - docs/archive/plans/2026-08-07-082F-cross-pack-measurability-plan.md
---

# Decided Plan: 082-F Cross-Pack Measurability Documentation

**Outcome:** Planned as a documentation-only delivery for feature `082-F`. The source plan records no PR or merge evidence, so status remains `planned`. The decided scope is to turn the already-gathered Engram and graphtor-docs evidence into durable mapping docs and one consolidated adapter-gap/sensitivity report before any broader pack-adapter implementation begins.

## Decisions

- Treat `082-F` as **documentation authoring**, not implementation. The deliverables map real Engram and graphtor-docs telemetry surfaces to the ratified `ToolTelemetryEvent` v1.0 contract and record the adapter gaps that still block broad emission work.
- Follow the `108-F` backlogit precedent: document field mappings, provenance, gaps, and safety limits first, then leave pack-adapter code for a later increment.
- Preserve pack-specific truth in the docs: graphtor token economics remain `unavailable`, graphtor-only extensions stay namespaced, and Engram's estimated-token caveats remain explicit instead of being normalized away.
- Record redaction, sensitivity, and sanitized-fixture rules as first-class deliverables so no raw internal pack content needs to be committed.
- Keep `agent-intercom` mapping deferred; this plan only covers packs with evidence surfaces gathered in the source material.

## Implementation (3 tasks)

- **T1 — Engram measurability mapping doc:** finalize the Engram-to-contract table, per-metric provenance, adapter gaps `G-E1..G-E5`, and the estimated-token caveat.
- **T2 — graphtor-docs measurability mapping doc:** finalize graphtor-to-contract mapping, cycle-vs-event wrapping, `token economics = unavailable`, extension namespacing, and gaps `G-G1..G-G5`.
- **T3 — Consolidated cross-pack report:** synthesize Engram, graphtor-docs, and the shipped backlogit precedent into one adapter-gap matrix plus the redaction/sensitivity/fixture decisions.

## Key constraints preserved

- This is **documentation-only**: no pack code, no JSON schema change, no CLI change, no template mutation, and no cross-repo edits.
- Every mapping stays anchored to the ratified ownership and telemetry-contract decisions rather than inventing a new contract.
- Sensitive pack details stay behind redaction and sanitized-fixture rules; no raw pack payloads are carried into committed artifacts.
- The consolidated report depends on both pack-specific mapping docs so the shared gap matrix reflects actual surfaced evidence rather than speculation.

## Rejected alternatives

- **Building live `ToolTelemetryEvent` adapters or emitters now** — rejected because this increment exists to make the evidence and gaps durable first.
- **Modifying Engram, graphtor-docs, or backlogit repositories from this plan** — rejected as out of scope.
- **Folding in `agent-intercom` now** — rejected because the source work did not gather a comparable evidence surface for that pack.