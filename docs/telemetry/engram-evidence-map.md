---
title: Engram Evidence → ToolTelemetryEvent Field Map
description: Maps agent-engram's real UsageEvent v2 telemetry surface (.engram/metrics/{branch}/usage.jsonl) and aggregate reports (get_token_savings_report, get_health_report, get_daemon_status) to the ratified ToolTelemetryEvent v1.0 forward contract, with per-metric metric_sources/metric_quality provenance and documented adapter gaps (G-E1..G-E5).
---

# Engram Evidence → ToolTelemetryEvent Field Map

> **Navigation**: [README](../../README.md) · [Telemetry Reference](../telemetry-reference.md) ·
> [Backlogit Evidence Map](backlogit-evidence-map.md) ·
> [graphtor-docs Evidence Map](graphtor-docs-evidence-map.md) ·
> [Cross-Pack Adapter-Gap Report](cross-pack-adapter-gap-report.md)

## Purpose and scope

This document is the `agent-engram` portion of feature 082-F (082.001-T), the second pack
mapping after the 108-F/113-F backlogit precedent
([`docs/telemetry/backlogit-evidence-map.md`](backlogit-evidence-map.md)). It contains **no
emitter code and no engram repo, schema, CLI, or template mutation** — 084-F owns event
emission; this document owns evidence classification only, sourced from an authoritative,
read-only local `agent-engram` workspace (`C:\Source\GitHub\engram`). No raw pack content, file
snippets, or absolute paths are reproduced below — only field names, schema shapes, and counts.

Sources reviewed (read-only): `src/models/metrics.rs` (`UsageEvent`, schema
`USAGE_SCHEMA_VERSION = 2`), and the aggregate report surfaces exposed by
`get_token_savings_report`, `get_health_report`, and `get_daemon_status`.

## Real surface (observed)

* **Per-tool-call usage telemetry** — one `UsageEvent` record per completed tool call, appended
  to `.engram/metrics/{branch}/usage.jsonl`. Pinned schema `schema_version = 2`, additive-only
  (existing fields are never renamed or removed), explicitly documented in source as the
  "autoharness contract."
* **Aggregate reports** — `get_token_savings_report` (avoided-read/token-savings summary),
  `get_health_report` (index freshness / daemon health), `get_daemon_status` (workspace binding
  and daemon readiness).

## Evidence-class vocabulary (same as backlogit-evidence-map.md)

| Evidence-class | Meaning |
|---|---|
| `observed` | Reported directly by the `UsageEvent` record at genuine per-invocation granularity: tool identity, timing, outcome, result counts, and optional runtime-attributed token fields. |
| `estimated` | Computed by engram itself from a proxy (payload byte size), not counted by a tokenizer: `estimated_input_tokens`, `estimated_output_tokens`, `estimated_tokens` (all `bytes / 4`). |
| `derived` | Computed by the adapter from correlated evidence rather than reported directly by any single field: `freshness_state`, `route_kind`, token-savings aggregates. |
| `unavailable` | The evidence does not exist on `UsageEvent` at any surface reviewed. |

## Mapping: `UsageEvent` v2 (event granularity, per-invocation)

Source: `.engram/metrics/{branch}/usage.jsonl`, one JSON object per line, `schema_version: 2`.

| `ToolTelemetryEvent` field | Engram source field | `metric_sources` | `metric_quality` | evidence-class |
|---|---|---|---|---|
| `tool_name` | `tool_name` | `host_reported` | `observed` | observed |
| `operation` | `tool_name` (same identity; engram does not distinguish a separate operation axis) | `host_reported` | `observed` | observed |
| `server_name` | pack identity `agent-engram` for `mcp`-surface events; **`null` for `cli`/`shell`/`builtin`/`api`** (contract requires `server_name: null` for non-MCP events) | `host_reported` | `observed` (surface-dependent) | observed |
| `tool_surface` | `mcp` (SSE transport) or `cli`, contextual on call path | `host_reported` | `observed` | observed |
| `timestamp` | `timestamp` (RFC 3339) — **completion time, not call start** (see caution below) | `host_reported` | `observed` | observed |
| `started_at` | **NOT directly available** — `timestamp` is constructed via `chrono::Utc::now()` at the point the `UsageEvent` is built, which happens *after* the response is fully computed (elapsed/`latency_ms` and `response_bytes`-derived fields are already known by then); it is the call's *completion* time, not its start. An adapter must either leave `started_at` `unavailable`, or derive it as `timestamp` minus `latency_ms` with `derived` (not `observed`) provenance — never map `timestamp` directly onto `started_at` | n/a | `unavailable` (or `derived` if computed) | unavailable |
| `duration_ms` | `latency_ms` | `host_reported` | `observed` | observed |
| `status` | `outcome` (free-form `success`/`error`, mapped to the 6-value taxonomy — see G-E4) | `host_reported` | `observed` (mapped) | observed |
| `result_count` | `result_count` (canonical) or `results_returned`/`symbols_returned` (tool-specific) | `host_reported` | `observed` | observed |
| `input_tokens` | **`estimated_input_tokens`** (`request_bytes / 4`) — **NEVER relabeled `observed`** (AC2 / G-E2) | `estimated` | `estimated` | estimated |
| `output_tokens` | **`estimated_output_tokens`** (`response_bytes / 4`) — **NEVER relabeled `observed`** (AC2 / G-E2) | `estimated` | `estimated` | estimated |
| `tool_output_estimated_tokens` | `estimated_tokens` (`response_bytes / 4`, output-side compatibility alias) | `estimated` | `estimated` | estimated |
| `input_tokens` (attributed variant) | `prompt_tokens_attributed` (optional, runtime-supplied) — **only** this and the two attributed fields below may legitimately carry `host_reported`/`observed` for token economics | `host_reported` | `observed` | observed |
| `output_tokens` (attributed variant) | `completion_tokens_attributed` (optional, runtime-supplied) | `host_reported` | `observed` | observed |
| `cached_input_tokens` | `cached_tokens_attributed` (optional, runtime-supplied) | `host_reported` | `observed` | observed |
| `tool_output_bytes` | `response_bytes` | `host_reported` | `observed` | observed |
| `agent_role` | `agent_role` (optional, sourced from `_meta.agent_role`) | `host_reported` | `observed` | observed |
| `session_id` | `connection_id` (optional SSE connection UUID) | `host_reported` | `observed` | observed |
| `branch` | `branch` (already sanitized at source) | `host_reported` | `observed` | observed |
| `workspace_id` | `workspace` (resolved absolute path — **internal**, see sensitivity note below) | `host_reported` | `observed` | observed |
| correlation | `correlation_id` (dual-source: MCP `_meta.correlation_id` or CLI flag/env; sanitized, 128-char cap) | `host_reported` | `observed` | observed |
| `freshness_state` | derived from `get_health_report` index-freshness signal, not a `UsageEvent` field | `derived` | `derived` | derived |
| `route_kind` | `structural_graph` (fixed constant for engram's graph-retrieval tool family) | `derived` | `derived` | derived |
| `retrieval_pack` | `agent-engram` (constant identity) | `host_reported` | `observed` | observed |
| avoided-read / savings estimates | `get_token_savings_report` outputs | `estimated` | `estimated` | estimated |
| `event_id` | **NOT PRESENT** — no native per-call unique identifier | n/a | `unavailable` | unavailable |
| `epoch_id` / `backlog_item_id` (correlation key) | **NOT PRESENT** — no native correlation to autoharness work-unit identity | n/a | `unavailable` | unavailable |
| `phase` | **NOT PRESENT** | n/a | `unavailable` | unavailable |
| `response_shape_counts` | no direct `ToolTelemetryEvent` field (a deterministic response-shape bucket counter); not mapped | n/a | `unavailable` | unavailable |

## Adapter gaps (G-E1 .. G-E5)

* **G-E1 — synthesized identity + correlation key required.** `UsageEvent` has no native
  `event_id`, `epoch_id`/`backlog_item_id`, git `commit_sha`, or `phase`. Any adapter that
  composes a `ToolTelemetryEvent` from a `UsageEvent` record MUST synthesize a stable
  `event_id` and supply a correlation key (`epoch_id` **or** `backlog_item_id`) — the schema's
  own `anyOf` requires one of the two; without it the composed event is schema-invalid.
* **G-E2 — token economics are estimated, never observed (AC2, review F2).**
  `estimated_input_tokens`, `estimated_output_tokens`, and `estimated_tokens` are all computed
  as `bytes / 4` — a byte-size proxy, not a tokenizer count. An adapter MUST set
  `metric_sources: estimated` / `metric_quality: estimated` for these three fields and MUST
  NEVER relabel them `host_reported`/`observed`. Only the three optional
  runtime-attributed fields (`prompt_tokens_attributed`, `completion_tokens_attributed`,
  `cached_tokens_attributed`) may legitimately carry `host_reported`/`observed` provenance,
  and only when the runtime layer actually supplied them (they are optional and frequently
  absent).
* **G-E3 — no native provenance maps.** `UsageEvent` carries no `metric_sources`/
  `metric_quality` structure of its own; both maps are entirely adapter-owned and must be
  populated per-field as shown in the mapping table above.
* **G-E4 — outcome taxonomy mapping is adapter-owned.** `outcome` is a free-form string
  (`"success"`/`"error"` observed in source; no enum enforcement at the Rust type level).
  An adapter must map this onto the ratified 6-value `status` taxonomy
  (`success`/`failed`/`degraded`/`blocked`/`skipped`/`operator_required`); only `success` and a
  generic failure are directly observable from engram today — `degraded`, `blocked`,
  `skipped`, and `operator_required` are not distinguishable from `outcome` alone and require a
  conservative (non-`success`) fallback mapping until engram's own outcome vocabulary is
  extended, which is out of 082-F's scope to request.
* **G-E5 — sensitivity (workspace path + branch).** `workspace` is a resolved **absolute
  filesystem path** and `branch` is a git branch name; both are classified **internal** per the
  schema's "ambiguous defaults to internal" rule. Neither may be emitted to a non-local sink
  without redaction (`redaction_applied: true`), and no absolute path value appears anywhere in
  this document (see the sensitivity note below).

## Sensitivity note (AC4)

No raw `usage.jsonl` record content, no absolute filesystem paths, and no live session/
correlation-id values are reproduced anywhere in this document — only field **names**, their
`ToolTelemetryEvent` mapping, and provenance classification. `workspace` (absolute path) and
`branch` (branch name) are internal-sensitivity source fields per G-E5 above; any future
adapter emitting them to a non-local sink must set `redaction_applied: true` or omit them.

## Cross-references

* [`docs/telemetry/backlogit-evidence-map.md`](backlogit-evidence-map.md) — the 108-F precedent
  this document mirrors in structure and evidence-class vocabulary.
* [`docs/telemetry/graphtor-docs-evidence-map.md`](graphtor-docs-evidence-map.md) — the
  companion 082.002-T mapping for the second pack.
* [`docs/telemetry/cross-pack-adapter-gap-report.md`](cross-pack-adapter-gap-report.md) — the
  082.003-T consolidated synthesis across all three packs.
* [`docs/telemetry-reference.md`](../telemetry-reference.md) — `ToolTelemetryEvent` v1.0 /
  `ExecutionEpoch` v1.1 schema overviews.
* `schemas/tool-telemetry-event.schema.json` — authoritative field definitions.
* `docs/decisions/2026-08-07-082F-cross-pack-measurability-evidence.md` — the evidence-gathering
  session this mapping formalizes.
