---
title: Backlogit Evidence → ToolTelemetryEvent/ExecutionEpoch Field Map
description: Maps backlogit 1.8 telemetry evidence (tool_call_fact, tool_usage, session_summary, session_fact, shipment size_composition) to the ratified ToolTelemetryEvent v1.0 / ExecutionEpoch v1.1 contract, with explicit granularity (event vs epoch) and evidence-class (observed | derived | unavailable | not_applicable) labels for every mapped target.
---

# Backlogit Evidence → ToolTelemetryEvent/ExecutionEpoch Field Map

> **Navigation**: [README](../../README.md) · [Telemetry Reference](../telemetry-reference.md) ·
> [Size + Complexity Reference](../size-complexity-reference.md) ·
> [Engram Evidence Map](engram-evidence-map.md) ·
> [graphtor-docs Evidence Map](graphtor-docs-evidence-map.md) ·
> [Cross-Pack Adapter-Gap Report](cross-pack-adapter-gap-report.md)

## Purpose and scope

This document is the backlogit-only carve-out of feature 082-F: a factual mapping from
backlogit 1.8's harvested telemetry evidence to the ratified `ToolTelemetryEvent` v1.0 /
`ExecutionEpoch` v1.1 contract. It contains **no emitter code** — 084-F owns event emission;
this document owns evidence classification only. Engram, graphtor-docs, and agent-intercom
portions of 082-F remain blocked-on-operator (see
[docs/telemetry/backlogit-sensitivity-guardrails.md](backlogit-sensitivity-guardrails.md)
for the carve-out statement).

Sources reviewed (read-only, upstream `C:\Source\GitHub\backlogit`, backlogit 1.8.0):

* `docs/telemetry-fields.md` — `session_summary` and `tool_usage` JSONL record
  documentation and the `telemetry_sessions`/`telemetry_tool_usage` SQLite mirrors.
* `internal/telemetry/records.go` — the `ToolCallFact` and `SessionFact` Go struct
  definitions (the two additional record types backlogit 1.8 harvests alongside
  `session_summary`/`tool_usage`; not yet documented in `telemetry-fields.md`).
* `internal/telemetry/schema_ref.go` — the authoritative field enumeration backlogit's own
  `backlogit telemetry schema` command emits for all four record types.

## The granularity dimension (non-negotiable)

Every mapped target below is tagged with a **granularity** label, because backlogit's
evidence is harvested at two structurally different levels and the ratified contract has two
structurally different record types for them:

* **`event`** — genuine **per-invocation** evidence: one row per completed tool call. Only
  `tool_call_fact` is per-invocation evidence in backlogit 1.8. This is the ONLY granularity
  that may populate `ToolTelemetryEvent` per-operation fields directly with `observed` quality
  **from the telemetry harvester**. A second, structurally distinct source also carries
  `observed` quality at `event` granularity without going through the harvester at all:
  planning-time state (`size_composition`, task `custom_fields.complexity`) read directly via
  `backlogit shipment get`/`backlogit get` and captured once into a `ToolTelemetryEvent`'s
  embedded `work_sizing_snapshot`/`task_complexity_label` at the `pre_execution` boundary. This
  is a direct, unaggregated read of current planning state (not a derived/computed roll-up), so
  it satisfies `observed` quality the same way `tool_call_fact` does — it is simply captured by
  a different mechanism (a one-time snapshot read, not a harvested call record). See the
  dedicated mapping section below for this source; the "Summary" section further down describes
  only the `tool_call_fact` harvester path and is not making a claim about this snapshot path.
* **`epoch`** — **per-session or per-tool-in-session aggregate** evidence: totals, counts, and
  derived ratios computed over many calls. `session_summary`, `tool_usage`, and `session_fact`
  are all aggregate-granularity. Aggregate evidence belongs at `ExecutionEpoch` economics
  granularity (a roll-up over a unit of work), never forced onto a single `ToolTelemetryEvent`'s
  per-operation fields — doing so would misattribute a session-wide total to one call and
  double-count when multiple calls in the same session are each (wrongly) stamped with the
  full session aggregate.

**Rule:** aggregate-only backlogit values (session cumulative tokens, tool_usage call-count/
duration roll-ups, `compaction_count`) are never mapped onto per-operation `ToolTelemetryEvent`
fields. They are routed to `ExecutionEpoch` (economics) granularity where a corresponding slot
exists, or labelled `unavailable` when no corresponding slot exists in either ratified schema
today (see [`compaction_count`](#compaction_count-is-not-a-tooltelemetryevent-field) below).

## Evidence-class vocabulary

Every mapped target carries FOUR labels: `metric_sources` value, `metric_quality` value,
evidence-class, and granularity.

| Evidence-class | Meaning |
|---|---|
| `observed` | Reserved for host_reported/backlogit-direct evidence at genuine **per-invocation** granularity only: `tool_name`, `server_name`, `model`, `started_at`/`completed_at`/`duration_ms`, and `success` from `tool_call_fact`. Per-call input/output/cached tokens would also be `observed` if backlogit exposed them at that granularity — **it does not** (see below). |
| `derived` | Computed from correlated evidence rather than reported directly by any single source: `tokens_per_task`, `depletion_rate`, `peak_utilization`, `remaining_capacity`, and any autoharness-side offload/avoided-read estimate. Labelled at the granularity where the computation is actually performed. |
| `unavailable` | The evidence does not exist in the current upstream backlogit 1.8 source, or exists only at a coarser granularity than the target field requires (e.g., a per-operation field with only aggregate evidence available). |
| `not_applicable` | The target field is autoharness-internal identity/correlation metadata that backlogit has no equivalent for at any granularity (`event_id`, `epoch_id`, `argv_fingerprint`, `exit_code`, `error_kind`). |

The corresponding `metric_sources` vocabulary values used below (`schemas/tool-telemetry-event.schema.json`):
`host_reported`, `estimated`, `derived`, `unavailable`, `not_applicable`, `host`, `backlogit`, `operator`.
`backlogit` is used specifically for evidence harvested by backlogit's own telemetry harvester
(all four record types below); `host_reported` is reserved for evidence an autoharness-native
emitter observes directly from the tool-call host, independent of backlogit.

## Important correction: `tool_call_fact` has NO per-call token fields

Per `internal/telemetry/records.go` (`ToolCallFact`), the concrete per-invocation source backlogit
1.8 exposes is `.backlogit/telemetry/tool-calls.jsonl`, one record per matched
`tool.execution_start` + `tool.execution_complete` pair, with exactly these fields:

`record_type`, `harvested_at`, `session_id`, `branch` (optional), `repository` (optional),
`tool_name`, `server_name` (optional, empty for built-ins), `is_builtin`, `turn_id` (optional),
`model` (optional — the model that triggered the call), `started_at`, `completed_at`,
`duration_ms`, `success`.

**There is no per-call `input_tokens`/`output_tokens`/`cached_input_tokens` field on
`ToolCallFact`.** Token accounting in backlogit 1.8 exists ONLY at session (`session_summary`)
and session+model (`session_fact.model_metrics`) aggregate granularity. Any claim of per-call
token `observed` evidence would be fabricated — this map does not make that claim.

## Mapping: `tool_call_fact` (event granularity, per-invocation)

Source: `.backlogit/telemetry/tool-calls.jsonl`, `record_type: "tool_call_fact"`.

| backlogit field | `ToolTelemetryEvent` target | `metric_sources` | `metric_quality` | evidence-class | granularity |
|---|---|---|---|---|---|
| `tool_name` | `tool_name` | `backlogit` | `observed` | observed | event |
| `server_name` | `server_name` | `backlogit` | `observed` | observed | event |
| `is_builtin` | `tool_surface` (`builtin` vs `mcp`/`cli`, contextual) | `backlogit` | `observed` | observed | event |
| `model` | not a direct schema field; informs `agent_role`/emitter-side model attribution, not a `ToolTelemetryEvent` property | `backlogit` | `observed` | observed | event |
| `started_at` | `started_at` | `backlogit` | `observed` | observed | event |
| `completed_at` | `ended_at` | `backlogit` | `observed` | observed | event |
| `duration_ms` | `duration_ms` | `backlogit` | `observed` | observed | event |
| `success` | `status` (`success` vs `failed`, contextual mapping; backlogit's boolean does not distinguish `degraded`/`blocked`/`skipped`/`operator_required`) | `backlogit` | `observed` | observed | event |
| `session_id` | `session_id` | `backlogit` | `observed` | observed | event |
| `branch` | `branch` | `backlogit` | `observed` | observed | event |
| `repository` | `repo` | `backlogit` | `observed` | observed | event |
| `turn_id` | no direct schema field (closest concept is `parent_event_id`, but a `turn_id` is a host conversation-turn identifier, not an event correlation ID; do not conflate) | `backlogit` | `unavailable` | unavailable | event |
| `input_tokens` / `output_tokens` / `cached_input_tokens` | **NOT PRESENT on `ToolCallFact`** | n/a | n/a | unavailable | event |

## Mapping: `tool_usage` (aggregate, session × tool granularity)

Source: `.backlogit/telemetry-sessions.jsonl`, `record_type: "tool_usage"` (one record per
`(session_id, server_name, tool_name)` tuple, aggregated over the whole session — NOT one
record per call).

| backlogit field | Target | `metric_sources` | `metric_quality` | evidence-class | granularity |
|---|---|---|---|---|---|
| `call_count` | No per-operation `ToolTelemetryEvent` field (a per-call event's own `retry_count`/occurrence is a different concept). Conceptually an `ExecutionEpoch` `OperationalReality.observed_tool_counts[tool_name]` analog, but that field is populated by autoharness's own event composer from correlated events, not from backlogit's independent aggregate — mixing the two sources into one field would misattribute provenance. | `backlogit` | `unavailable` | unavailable | epoch |
| `total_duration_ms` | No existing `ExecutionEpoch` field aggregates per-tool cumulative duration today. | `backlogit` | `unavailable` | unavailable | epoch |

**This is the canonical aggregate-misattribution trap the granularity dimension exists to
prevent:** `tool_usage.call_count` and `total_duration_ms` describe an entire session's use of
one tool, not any single call. Stamping either value onto a single `ToolTelemetryEvent`
`duration_ms` or treating `call_count` as that event's `retry_count` would misattribute a
session total to one operation and, if repeated across every call in the session, would
double- (or N-times-) count the same aggregate. Neither value is mapped onto a
`ToolTelemetryEvent` per-operation field.

## Mapping: `session_summary` (aggregate, session granularity)

Source: `.backlogit/telemetry-sessions.jsonl`, `record_type: "session_summary"` — one record per
Copilot CLI session.

| backlogit field | Target | `metric_sources` | `metric_quality` | evidence-class | granularity |
|---|---|---|---|---|---|
| `session_id` | `ExecutionEpoch.session_id` | `backlogit` | `observed` | observed | epoch |
| `branch` | `ExecutionEpoch.branch` | `backlogit` | `observed` | observed | epoch |
| `repository` | no direct `ExecutionEpoch` field (epoch correlation uses `workspace_id`, not a repository string) | `backlogit` | `unavailable` | unavailable | epoch |
| `total_tokens` | `EconomicPayload` has no single combined-total field (`input_tokens` + `output_tokens` are tracked separately); `total_tokens` is a derived sum at epoch granularity if both components are separately sourced | `backlogit` | `derived` | derived | epoch |
| `prompt_tokens` | `EconomicPayload.input_tokens` (session-aggregate, not per-call; unavailable at event granularity, usable as a `derived`/`estimated` roll-up input at epoch granularity) | `backlogit` | `estimated` | derived | epoch |
| `completion_tokens` | `EconomicPayload.output_tokens` (session-aggregate; unavailable at event granularity, epoch-level roll-up input) | `backlogit` | `estimated` | derived | epoch |
| `cached_tokens` | `EconomicPayload.cached_input_tokens` (session-aggregate; epoch-level roll-up input) | `backlogit` | `estimated` | derived | epoch |
| `model_calls` | no direct `ExecutionEpoch` field; conceptually distinct from `tool_calls` | `backlogit` | `unavailable` | unavailable | epoch |
| `tool_calls` | see `tool_usage.call_count` note above — same aggregate-misattribution caution applies | `backlogit` | `unavailable` | unavailable | epoch |
| `tokens_by_model` | no direct `ExecutionEpoch` field (`RouteConfiguration.models` records which models were involved, not a token breakdown by model) | `backlogit` | `unavailable` | unavailable | epoch |
| `tool_calls_by_server` | no direct `ExecutionEpoch` field for backlogit-sourced per-server breakdown (the composer's own `route_kind_counts`/`observed_tool_counts` are autoharness-event-sourced, a different provenance) | `backlogit` | `unavailable` | unavailable | epoch |
| `completed_tasks` | correlates to `ExecutionEpoch.backlog_item_id`(s) for the session, not a single scalar field | `backlogit` | `observed` | observed | epoch |
| `tokens_per_task` | **derived** metric, already labelled as such by backlogit itself (`number or null`, `total_tokens / len(completed_tasks)`) | `backlogit` | `derived` | derived | epoch |
| `compaction_count` | **see dedicated section below — not a field in either ratified schema today** | n/a | n/a | unavailable | n/a |
| `peak_utilization` | **derived** (backlogit's own definition: highest prompt/max-context ratio) — no direct `ExecutionEpoch` field exists to hold this ratio today | `backlogit` | `derived` | derived | epoch |
| `remaining_capacity` | **derived** — no direct `ExecutionEpoch` field | `backlogit` | `derived` | derived | epoch |
| `depletion_rate` | **derived** (average total tokens per model call) — no direct `ExecutionEpoch` field | `backlogit` | `derived` | derived | epoch |
| `max_context_tokens` | model-configuration metadata, not a measured quantity — no direct `ExecutionEpoch` field; would be `not_applicable` as a "metric" | `backlogit` | `not_applicable` | not_applicable | epoch |

### `compaction_count` is NOT a `ToolTelemetryEvent` field

`compaction_count` exists in backlogit's `session_summary` record and `telemetry_sessions` SQL
mirror only. It has **no corresponding field in `schemas/tool-telemetry-event.schema.json`
(event granularity) and no corresponding field in `schemas/execution-epoch/1.1.0.schema.json`
(epoch granularity) as of this writing.** It must not be silently mapped onto any existing
field of either contract (there is no plausible epoch-level "count" field it could safely
alias to without inventing semantics the target field wasn't designed to carry). This map
records it as `unavailable` at both granularities and as an explicit schema gap, not a mapping
target — closing that gap (if ever prioritized) is future schema work, out of scope for 108-F.

## Mapping: `session_fact` (aggregate, session granularity, model-level breakdown)

Source: `.backlogit/telemetry/session-facts.jsonl`, `record_type: "session_fact"` — harvested
from a `session.shutdown` event; richer per-model detail than `session_summary` but still one
record per session (not per call).

| backlogit field | Target | `metric_sources` | `metric_quality` | evidence-class | granularity |
|---|---|---|---|---|---|
| `total_api_duration_ms` | `EconomicPayload.duration_seconds` (unit conversion required; session-aggregate, not per-call; epoch-level roll-up input) | `backlogit` | `estimated` | derived | epoch |
| `total_premium_requests` | `EconomicPayload.cogs_usd` — **no established premium-request-to-USD conversion exists in this codebase**; do not fabricate one | `backlogit` | `unavailable` | unavailable | epoch |
| `model_metrics[model].{input_tokens,output_tokens,cache_read_tokens,cache_write_tokens,reasoning_tokens,request_count,request_cost}` | per-model token/request breakdown; no direct `ExecutionEpoch` field decomposes economics by model today (`EconomicPayload` is a single aggregate, not per-model; would require a schema extension to represent per-model breakdown, out of scope for 108-F) | `backlogit` | `unavailable` | unavailable | epoch |
| `current_tokens` / `system_tokens` / `conversation_tokens` / `tool_definitions_tokens` | context-window composition snapshot at shutdown; conceptually adjacent to `EconomicPayload.context_tokens_before`/`context_tokens_after` but measured at a different boundary (session shutdown vs per-operation before/after) — not a safe direct alias; granularity/boundary mismatch | `backlogit` | `unavailable` | unavailable | epoch |
| `tool_call_count` | same aggregate-misattribution caution as `session_summary.tool_calls` / `tool_usage.call_count` | `backlogit` | `unavailable` | unavailable | epoch |

## Mapping: shipment `size_composition` and task `complexity`

Source: `backlogit shipment get <id>` / `backlogit get <task-id>` (`custom_fields`), not the
telemetry JSONL/SQLite surfaces above — a planning-time (not runtime-observed) evidence source.

| backlogit field | Target | `metric_sources` | `metric_quality` | evidence-class | granularity |
|---|---|---|---|---|---|
| shipment `size_composition.histogram` | `WorkSizingSnapshot.shipment_manifest_size_histogram` | `backlogit` | `observed` | observed | event (`work_sizing_snapshot`, `pre_execution` boundary, embedded in a `ToolTelemetryEvent`) |
| shipment `size_composition.members[].size` / task `custom_fields.size` | `WorkSizingSnapshot.task_size_label` / `feature_planned_size_label` / `shipment_planned_size_label` | `backlogit` | `observed` | observed | event |
| shipment `size_composition.unsized` / `skipped` | `WorkSizingSnapshot.*_skipped_ids` (diagnostic) | `backlogit` | `observed` | observed | event |
| task `custom_fields.complexity` (`trivial\|low\|medium\|high`, task artifact_type ONLY per `.backlogit/header-def.yaml`) | `task_complexity_label` (new, 108.002-T; structurally separate top-level field, NOT nested in `work_sizing_snapshot` — size and complexity must never conflate) | `backlogit` | `observed` | observed | event |
| — (autoharness's own record of how it learned the complexity value) | `complexity_source` (new, 108.002-T) | `backlogit` (when read directly from a backlogit task record) | `observed` | observed | event |

**Non-conflation reminder:** `size` answers "how much implementation volume" and is
feature/shipment/task-scoped via `WorkSizingSnapshot`. `complexity` answers "how hard/uncertain"
and is **task-only** in backlogit's own contract
([size-complexity-reference.md](../size-complexity-reference.md)) — feature- and
shipment-level `task_complexity_label` is always `null` (the field's enum is
`trivial|low|medium|high|null`; there is no `not_applicable` enum member), paired with
`complexity_source: not_applicable` to record why
([backlogit-sensitivity-guardrails.md](backlogit-sensitivity-guardrails.md) restates this for
the safety boundary). The two axes are never combined into one scalar or nested inside each
other's payload.

## Summary: what `observed` evidence backlogit 1.8's telemetry harvester gives autoharness at event granularity

Restated for emphasis, since this is the finding that corrected the original (pre-re-review)
plan draft: genuine per-invocation `observed` evidence from backlogit 1.8's **telemetry
harvester** is limited to `tool_call_fact`'s fields — `tool_name`, `server_name`, `model`,
`is_builtin`, `started_at`, `completed_at`, `duration_ms`, `success`, and the optional
`branch`/`repository`/`turn_id` correlation fields. **No per-call token evidence exists.**
Everything else useful (tokens, model-level breakdowns, derived utilization/depletion metrics)
is aggregate, session-granularity evidence that belongs at `ExecutionEpoch` economics
granularity or is presently unrepresentable in either ratified schema. This restatement is
scoped to the harvester path only — it does not apply to the separately-sourced, directly-read
planning-time snapshot (`size_composition`/task `complexity`) described in the granularity
dimension section above and the dedicated mapping section below, which also carries `observed`
quality at `event` granularity through a different (non-harvester) mechanism.

## Cross-references

* [`docs/telemetry-reference.md`](../telemetry-reference.md) — `ToolTelemetryEvent` v1.0 and
  `ExecutionEpoch` v1.1 schema overviews.
* [`docs/size-complexity-reference.md`](../size-complexity-reference.md) — non-conflated
  `size`/`complexity` semantics this map's `WorkSizingSnapshot`/`task_complexity_label` rows
  depend on.
* [`docs/telemetry/backlogit-sensitivity-guardrails.md`](backlogit-sensitivity-guardrails.md) —
  sensitivity/redaction defaults and the 082-F backlogit carve-out (108.003-T).
* `schemas/tool-telemetry-event.schema.json` / `schemas/tool-telemetry-event/1.0.0.schema.json` —
  the event contract this map targets.
* `schemas/execution-epoch/1.1.0.schema.json` — the epoch contract aggregate evidence routes to.
* `docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md` — autoharness owns
  reporting; backlogit owns planned sizing/work-state; 082-F=evidence, 084-F=emission.
