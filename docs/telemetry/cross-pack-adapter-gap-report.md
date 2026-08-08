---
title: Cross-Pack Adapter-Gap + Sensitivity/Fixtures Report (082-F)
description: Consolidated synthesis of Engram (082.001-T), graphtor-docs (082.002-T), and backlogit (108-F, done) telemetry evidence mapping — a unified adapter-gap matrix, an observed/estimated/derived/unavailable/unsafe summary per pack, explicit sensitivity/redaction acceptance criteria, the sanitized-fixtures decision, and the traceable agent-intercom deferral note.
---

# Cross-Pack Adapter-Gap + Sensitivity/Fixtures Report

> **Navigation**: [README](../../README.md) · [Telemetry Reference](../telemetry-reference.md) ·
> [Backlogit Evidence Map](backlogit-evidence-map.md) ·
> [Engram Evidence Map](engram-evidence-map.md) ·
> [graphtor-docs Evidence Map](graphtor-docs-evidence-map.md)

## Purpose and scope

This document is the 082.003-T consolidated deliverable of feature 082-F. It synthesizes the
three per-pack evidence mappings — [`backlogit-evidence-map.md`](backlogit-evidence-map.md)
(108-F, done), [`engram-evidence-map.md`](engram-evidence-map.md) (082.001-T), and
[`graphtor-docs-evidence-map.md`](graphtor-docs-evidence-map.md) (082.002-T) — into one
cross-pack adapter-gap matrix, one observed/estimated/derived/unavailable/unsafe summary, an
explicit sensitivity/redaction guardrail set encoded as acceptance criteria, the
sanitized-fixtures decision, and a traceable `agent-intercom` deferral note. It contains **no
emitter code**. Adapters remain **autoharness-side wrappers**, never pack-repo changes — this
is consistent with the ratified 079-F ownership model
(`docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md`) and the 108-F precedent,
which produced a mapping deliverable, not pack code. Depends on 082.001-T and 082.002-T (both
done); 108-F is independently done and referenced, not re-derived.

## Unified adapter-gap matrix

| Dimension | backlogit (108-F) | Engram (082.001-T) | graphtor-docs (082.002-T) |
|---|---|---|---|
| Per-invocation event surface | `tool_call_fact` (JSONL) | `UsageEvent` v2 (`usage.jsonl`) | none — cycle-scoped only |
| Aggregate/cycle surface | `tool_usage`, `session_summary`, `session_fact` | `get_token_savings_report`, `get_health_report` | `SyncMetrics` (per sync cycle) |
| Native identity/correlation (`event_id`, `epoch_id`/`backlog_item_id`, `phase`) | none — adapter-owned | none — adapter-owned | none — adapter-owned |
| Per-call token economics | none at `tool_call_fact`; session/session+model aggregate only | `estimated` (bytes/4) + optional runtime-attributed `observed` | **unavailable at any granularity** (local embedding) |
| Native provenance maps (`metric_sources`/`metric_quality`) | none — adapter-owned | none — adapter-owned | none — adapter-owned |
| Outcome taxonomy | boolean `success` → adapter-mapped | free-form `outcome` string → adapter-mapped | `SyncStatus` enum → adapter-mapped |
| Freshness/health signal | index freshness (not part of the four record types) | `get_health_report` (derived) | `SourceSyncState` mtime (derived) |
| `route_kind` (fixed adapter constant) | `backlog_index` | `structural_graph` | `doc_index` |
| Non-schema evidence requiring out-of-band reporting | `compaction_count` (no ratified-schema field at all) | none identified | ingest volume (`files_*`/`chunks_*`) — G-G4 |
| Sensitivity risk (internal by default) | item text / task-content fields (not in the safe evidence surface) | `workspace` (abs path), `branch` | `SyncStatus::Error` message, source paths |
| Adapter classification | autoharness-side wrapper (no backlogit repo change) | autoharness-side wrapper (no engram repo change) | autoharness-side wrapper (no graphtor repo change) |

## Observed / estimated / derived / unavailable / unsafe summary (per pack)

* **backlogit (108-F, done)**: `observed` — `tool_name`, `server_name`, `is_builtin`,
  `started_at`/`completed_at`/`duration_ms`, `success`, `session_id`, `branch`, `repository`,
  `WorkSizingSnapshot` counts/hashes, `task_complexity_label`. `derived` — `total_tokens`
  (sum), `tokens_per_task`, `peak_utilization`, `remaining_capacity`, `depletion_rate`.
  `unavailable` — per-call token fields on `tool_call_fact`, `turn_id` correlation,
  `compaction_count` (no ratified-schema slot). `not_applicable` — autoharness-internal
  identity fields (`event_id`, `argv_fingerprint`, `exit_code`, `error_kind`). **Unsafe to
  emit raw**: task/feature/shipment description or DoD prose text (IDs are safe, content is
  not).
* **Engram (082.001-T)**: `observed` — `tool_name`, `server_name` (surface-dependent),
  `timestamp`, `latency_ms`→`duration_ms`, `outcome`→`status` (mapped), `result_count`,
  optional `prompt_tokens_attributed`/`completion_tokens_attributed`/`cached_tokens_attributed`,
  `agent_role`, `connection_id`→`session_id`, `branch`, `workspace`→`workspace_id`,
  `correlation_id`. `estimated` — `estimated_input_tokens`, `estimated_output_tokens`,
  `estimated_tokens` (all `bytes/4` — **never** relabeled `observed`, AC2/G-E2), token-savings
  report outputs. `derived` — `freshness_state`, `route_kind`. `unavailable` — `event_id`,
  correlation key (`epoch_id`/`backlog_item_id`), `phase`. **Unsafe to emit raw**: `workspace`
  (absolute path), `branch` — internal, redaction required (G-E5).
* **graphtor-docs (082.002-T)**: `observed` — MCP tool name/identity, `server_name`
  (surface-dependent), `SyncMetrics.duration_ms`, `SyncStatus`→`status` (mapped), search
  `result_count`, routed-search `routed_lookup_count` (search calls only). `derived` —
  `freshness_state` (mtime comparison), `route_kind`, `error_kind` (category from
  `SyncStatus::Error`). `unavailable` — **all per-call token economics** (`input_tokens`/
  `output_tokens`/`cached_input_tokens` — G-G1, **never** a numeric `0`), `event_id`,
  correlation key, `phase`, `agent_role`, ingest-only `routed_lookup_count`. **Reported
  out-of-band, not emitted in-event**: `files_total`/`files_synced`/`files_deleted`/
  `chunks_created`/`chunks_deleted` (G-G4 — no core field, cannot be `x-graphtor-*` root
  properties). **Unsafe to emit raw**: `SyncStatus::Error` message text, source file paths —
  internal, redaction required (G-G5).

## Sensitivity/redaction guardrails as explicit acceptance criteria (AC1, review F1)

Per plan review finding **F1** (P2, accepted): the sensitivity/redaction guardrail below is
encoded as an explicit acceptance criterion here — not left as advisory prose — so a downstream
emitter cannot read it as optional.

**AC1 (this document, binding on any future 084-F-scoped adapter built from this evidence):**

1. Any field classified **internal** in any of the three per-pack evidence maps (backlogit
   item-content text; Engram `workspace`/`branch`; graphtor-docs `SyncStatus::Error`
   message/source paths) **MUST** carry `redaction_applied: true` before it is emitted to any
   non-local sink, or **MUST be omitted** entirely.
2. `sensitivity` **MUST** default to `internal` whenever a field's classification is ambiguous,
   per the schema's own rule ("ambiguous defaults to internal handling") — never default to
   `public`.
3. `secret_scan_status` **MUST** be `not_run` unless a scan actually executed; `passed` must
   never be asserted without a real scan step.
4. These three rules are **binding acceptance criteria for any adapter/emitter that consumes
   this evidence mapping**, not optional guidance — an implementation that skips them fails
   review regardless of functional correctness.

## Sanitized-fixtures decision

* **No raw pack telemetry is committed** anywhere in 082-F's deliverables (this document nor
  either per-pack evidence map). All three mapping documents describe field **names**, schema
  shapes, and provenance classifications only — never live record content, live session/
  correlation IDs, or absolute filesystem paths.
* If a downstream feature (post-082-F, out of this feature's scope) needs illustrative fixture
  data, only **synthetic, sanitized, single-line records** are permitted: paths and branch
  names replaced with placeholder tokens, no real error strings, clearly labeled as synthetic.
  Such fixtures **must not** be added under 082-F — they belong to whatever future
  adapter/emission feature consumes this mapping (084-F or a successor), where a fresh
  sensitivity review of the fixture content itself would apply.

## Explicit agent-intercom deferral note (AC3, review F3)

Per plan review finding **F3** (P3, accepted): `agent-intercom` measurability is **explicitly
and traceably deferred**, not silently dropped. 082-F's originating queue item listed
`agent-intercom` among the four capability packs in scope for a cross-pack measurability
session; this shipment's evidence-gathering session (see
`docs/decisions/2026-08-07-082F-cross-pack-measurability-evidence.md`) recorded that
`agent-intercom` was **unavailable this session** (no evidence surface, no operator-provided
read access) and was removed from the session's active evidence list rather than mapped from
guesswork or public-web inference. **This report reaffirms that deferral explicitly**: no
`agent-intercom` mapping exists in this document, in `engram-evidence-map.md`, or in
`graphtor-docs-evidence-map.md`. A future session with an actual `agent-intercom` evidence
surface (operator-provided read access or sanitized fixtures) is required before any
`agent-intercom` telemetry mapping can be authored — this is a **traceable gap**, not an
oversight, and must not be assumed covered by 082-F when reviewing future work.

## Adapter ownership reaffirmation

Consistent with the ratified 079-F ownership split and the 108-F precedent: every mapping in
this report and its two companion per-pack documents describes an **autoharness-side adapter**
(a wrapper composing a `ToolTelemetryEvent`/`ExecutionEpoch` from pack-native evidence). None of
the three packs' source repositories require any change to support this mapping — no schema,
CLI, template, or runtime code in `agent-engram`, `graphtor-docs`, or `backlogit` was or needs to
be modified for 082-F. Broad adapter *emission* implementation (the actual composer/emitter
code) remains out of 082-F's scope, deferred to 084-F or a successor feature, per the plan's
scope boundary.

## Cross-references

* [`docs/telemetry/backlogit-evidence-map.md`](backlogit-evidence-map.md) — 108-F backlogit
  mapping (done), synthesized above.
* [`docs/telemetry/backlogit-sensitivity-guardrails.md`](backlogit-sensitivity-guardrails.md) —
  108-F backlogit-specific sensitivity precedent this report's AC1 guardrail generalizes across
  all three packs.
* [`docs/telemetry/engram-evidence-map.md`](engram-evidence-map.md) — 082.001-T Engram mapping,
  synthesized above.
* [`docs/telemetry/graphtor-docs-evidence-map.md`](graphtor-docs-evidence-map.md) — 082.002-T
  graphtor-docs mapping, synthesized above.
* [`docs/telemetry-reference.md`](../telemetry-reference.md) — `ToolTelemetryEvent` v1.0 /
  `ExecutionEpoch` v1.1 schema overviews.
* `schemas/tool-telemetry-event.schema.json` — authoritative field/safety definitions.
* `docs/decisions/2026-08-07-082F-cross-pack-measurability-evidence.md` — the evidence-gathering
  session this report and its two companion documents formalize.
* `docs/plans/2026-08-07-082F-cross-pack-measurability-plan.md` and
  `docs/reviews/2026-08-07-082F-cross-pack-measurability-review.md` — the harvested plan and
  its PASS review (findings F1/F2/F3 addressed above).
* `docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md` — the ratified 079-F
  ownership contract this report's adapter-classification section reaffirms.
