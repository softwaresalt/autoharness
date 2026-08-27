---
source: docs/plans/2026-08-03-size-complexity-telemetry-staging-decided-plan.md
title: "Size + Complexity first-class staging & backlogit telemetry evidence mapping"
doc_type: decided-plan
status: shipped
created: 2026-08-03
tasks: ["107.001-T", "107.002-T", "107.003-T", "107.004-T", "107.005-T", "108.001-T", "108.002-T", "108.003-T", "108.004-T"]
supersedes:
  - docs/archive/plans/2026-08-03-size-complexity-telemetry-staging-plan.md
---

# Decided Plan: Size + Complexity first-class staging & backlogit telemetry evidence mapping

**Outcome:** Planned with chosen direction **B — Two ordered shipments (S1 staging → S2 telemetry), non-conflated size/complexity**. The source plan maps the work to parent features `107-F` and `108-F`, with `112-S` carrying staging first and `113-S` carrying telemetry second. P-006 hardening is present because the telemetry half touches the ratified schema surface and its live runtime model, but the source plan records no PR or merge evidence, so status remains `planned`.

**Delivery status (verified against the backlog at compaction time):** shipped — `082-F`, `084-F`, `107-F`, `107.001-T`, `107.002-T`, `107.003-T`, `107.004-T`, `107.005-T`, `108-F`, `108.001-T`, `108.002-T`, `108.003-T`, `108.004-T`, `112-S`, `113-S` confirmed complete in `.backlogit/`.

## Decisions

- Split the work into two ordered increments instead of one conflated change set: **S1** makes size and complexity first-class in Stage/harvest, then **S2** maps backlogit telemetry evidence onto the ratified telemetry contract.
- Preserve backlogit's released semantics verbatim: **size** is implementation volume/effort and **complexity** is implementation difficulty/uncertainty. The two axes stay separate everywhere, and the 2-hour gate uses both independently.
- Require every created task to carry validated size metadata (`size`, `size_source: agent`, non-empty `size_ruleset_version`) and a validated `complexity` enum.
- Treat telemetry mapping as an evidence-mapping problem, not an emission problem. Every mapped target carries provenance and granularity labels, and aggregate-only backlogit values stay at epoch granularity or remain unavailable at event granularity.
- Add complexity to the telemetry contract as a **separate top-level optional field**, not nested inside `work_sizing_snapshot`, so size and complexity can never collapse into one scalar.
- Keep event emission out of scope. `084-F` remains the owner of live emitter wiring.

## Implementation (9 tasks across two ordered features)

### Feature `107-F` / shipment `112-S` — staging first

- **107.001-T — Size↔complexity reference doc:** publish the shared semantics, enums, two-axis gate rules, and provenance-completeness rule.
- **107.004-T — Stage template update:** require size + complexity at task creation, validate enums, enforce the two-axis granularity gate, and propagate the identical change to the dogfood Stage mirror plus manifest checksum.
- **107.002-T — Harvest skill update:** emit size + complexity on every work item and reject invalid values at the existing granularity gate.
- **107.003-T — Validation checklist/fixture:** pin enum validation, provenance completeness, and non-conflation.
- **107.005-T — backlogit header-def update:** enable the native task-level `complexity` field so Ship no longer has to rely on comment-only recording.

### Feature `108-F` / shipment `113-S` — telemetry second

- **108.001-T — Evidence map doc:** map backlogit telemetry surfaces onto `ToolTelemetryEvent` / `ExecutionEpoch` with explicit evidence class and event-vs-epoch granularity.
- **108.002-T — Schema mirrors + registration:** add the optional complexity field to the root and versioned schema mirrors, preserve parity, and update `known_versions` plus schema-contract tests.
- **108.004-T — Runtime model/composer/jsonl wiring:** thread the new field through the strict runtime model, serialization, and round-trip/schema-conformance tests.
- **108.003-T — Safety and correlation guardrails:** document sensitivity, redaction, and defensible-correlation limits, including the backlogit carve-out that unblocks `082-F`.

## Key constraints preserved

- The published work stays task-only at the shipment level: the two parent features 107-F and 108-F are derived from task hierarchy and are not shipment members.
- Size and complexity are never conflated: size stays volume/effort, complexity stays difficulty/uncertainty, and feature/shipment-level complexity remains `not_applicable`.
- `size_source` implies a non-empty `size_ruleset_version`; provenance completeness is a required invariant, not an optional annotation.
- Aggregate-only backlogit metrics such as session/tool roll-ups are **not** mapped onto per-operation `ToolTelemetryEvent` fields; they belong at epoch granularity or remain unavailable.
- Any telemetry-schema change must land in **both** schema mirrors, be registered in `schema_contracts`, and be threaded through the live strict runtime model/composer/jsonl path so parity and round-trip tests stay green. If versioning policy requires a new versioned file, it is added alongside `1.0.0` rather than replacing it.
- The Stage template change keeps the template edit, dogfood mirror update, and checksum refresh together as one coherent agent-template change, while the header-def and telemetry runtime work stay width-isolated.
- No emitter wiring, cross-repo mutation, or supply of raw sensitive content crosses this plan boundary.

## Rejected alternatives

- **One combined shipment for staging and telemetry** — rejected so the smaller staging semantics land first and the schema/runtime work follows in a separate ordered increment.
- **A single scalar or nested field that mixes size and complexity** — rejected because it would erase the non-conflation rule and make the two-axis gate unverifiable.
- **Mapping session/tool aggregates or `compaction_count` onto per-event telemetry fields** — rejected as misattribution and double-counting; those values are epoch-only or unavailable at event granularity.
- **Treating the telemetry schema as an inert forward contract** — rejected because the root/versioned mirror parity test, `known_versions` registration, and strict runtime model make the schema a live surface.

## Post-review refinements folded in

- Hardening corrected the initial assumption that the telemetry schema was inert. That change split the work into **schema/registration** (`108.002-T`) and **runtime-model/composer/jsonl** (`108.004-T`) so drift can be controlled explicitly.
- The native backlogit `complexity` header-def gap was pulled into the first shipment as `107.005-T` so Stage's new requirement has a real workspace field to target.
- The telemetry complexity field was fixed as a **top-level optional field** rather than a nested sizing attribute, making non-conflation enforceable in schema, runtime, and review.

## Rollback

The work is additive. Rollback removes the optional telemetry complexity field from both schema mirrors plus its registration/runtime wiring, deletes the staging reference/checklist additions, and reverts the header-def block; no data migration or emitter rollback is required.