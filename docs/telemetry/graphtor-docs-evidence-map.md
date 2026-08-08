---
title: graphtor-docs Evidence → ToolTelemetryEvent Field Map
description: Maps graphtor-docs's real SyncMetrics/SyncStatus telemetry surface (src/sync/mod.rs) and search result_count to the ratified ToolTelemetryEvent v1.0 forward contract, with per-metric metric_sources/metric_quality provenance and documented adapter gaps (G-G1..G-G5).
---

# graphtor-docs Evidence → ToolTelemetryEvent Field Map

> **Navigation**: [README](../../README.md) · [Telemetry Reference](../telemetry-reference.md) ·
> [Backlogit Evidence Map](backlogit-evidence-map.md) ·
> [Engram Evidence Map](engram-evidence-map.md) ·
> [Cross-Pack Adapter-Gap Report](cross-pack-adapter-gap-report.md)

## Purpose and scope

This document is the `graphtor-docs` portion of feature 082-F (082.002-T), the third pack
mapping alongside [`docs/telemetry/backlogit-evidence-map.md`](backlogit-evidence-map.md)
(108-F/113-F) and [`docs/telemetry/engram-evidence-map.md`](engram-evidence-map.md) (082.001-T).
It contains **no emitter code and no graphtor repo, schema, CLI, or template mutation** — 084-F
owns event emission; this document owns evidence classification only, sourced from an
authoritative, read-only local `graphtor-docs` workspace (`C:\Source\GitHub\graphtor`). No raw
pack content, file snippets, or absolute paths are reproduced below — only field names, schema
shapes, and counts.

Sources reviewed (read-only): `src/sync/mod.rs` (`SyncMetrics`, `SourceSyncState`), and the
`get_status` MCP tool's `SyncStatus` enum plus document-search `result_count`.

## Real surface (observed)

* **Ingestion-cycle telemetry** — `SyncMetrics` (`src/sync/mod.rs`): `files_total`,
  `files_synced`, `files_deleted`, `chunks_created`, `chunks_deleted`, `duration_ms`, `errors`.
  This is **cycle-scoped** (one record per sync cycle across potentially many files), **not**
  per-tool-call.
* **Source freshness state** — `SourceSyncState` / per-source `*.sync_state.json` (mtime-tracked
  freshness), driving staleness determination.
* **Server/search status** — the `get_status` MCP tool returns a `SyncStatus` enum
  (`Idle` / `Syncing` / `InProgress` / `Done{files, chunks}` / `Complete{metrics}` / `Error`);
  document-search calls separately return `result_count`.

## Evidence-class vocabulary (same as backlogit-evidence-map.md / engram-evidence-map.md)

| Evidence-class | Meaning |
|---|---|
| `observed` | Reported directly by `SyncMetrics`/`SyncStatus`/search results at the granularity graphtor actually measures (per-cycle for sync, per-call for search `result_count`). |
| `derived` | Computed by the adapter from correlated evidence: `freshness_state` (mtime comparison), `route_kind` (constant classification), `error_kind` (category extracted from a `SyncStatus::Error` message). |
| `unavailable` | The evidence does not exist on any surface reviewed — most notably, **all per-call token economics** (see G-G1). |

## Mapping: `SyncMetrics` / `SyncStatus` / search (cycle- and call-scoped, as noted per row)

| `ToolTelemetryEvent` field | graphtor source | `metric_sources` | `metric_quality` | evidence-class | scope |
|---|---|---|---|---|---|
| `tool_name` / `operation` | MCP tool name (`get_status`, document search, sync trigger) | `host_reported` | `observed` | observed | call |
| `server_name` | `graphtor-docs` for `mcp`-surface events; **`null` for `cli`/`shell`/`builtin`/`api`** (contract requires `server_name: null` for non-MCP events) | `host_reported` | `observed` (surface-dependent) | observed | call |
| `tool_surface` | `mcp` / `cli`, contextual on call path | `host_reported` | `observed` | observed | call |
| `duration_ms` | `SyncMetrics.duration_ms` — **cycle-scoped**; an adapter attributing this to a single triggering call must wrap the cycle (see G-G2) | `host_reported` | `observed` | observed | cycle |
| `status` | `SyncStatus` mapped to the 6-value taxonomy (`Error` → `failed`, `Complete`/`Done` → `success`, `Syncing`/`InProgress` → in-flight, not terminal) | `host_reported` | `observed` (mapped) | observed | call/cycle |
| `result_count` | document-search `result_count` — genuinely per-call | `host_reported` | `observed` | observed | call |
| `freshness_state` | `SourceSyncState` mtime vs. source mtime comparison (`fresh`/`stale`) | `derived` | `derived` | derived | call |
| `route_kind` | `doc_index` (fixed constant for graphtor's document-retrieval tool family) | `derived` | `derived` | derived | call |
| `retrieval_pack` | `graphtor-docs` (constant identity) | `host_reported` | `observed` | observed | call |
| `routed_lookup_count` | count of **observed routed/indexed document-search invocations only** — a positive value is evidence an offload occurred; **`unavailable` for ingestion-only sync cycles** (`files_*`/`chunks_*` volume does NOT establish routed lookups; see G-G4) | `host_reported` | `observed` (routed searches only; else `unavailable`) | observed / unavailable (split) | call |
| `error_kind` | category extracted from `SyncStatus::Error(msg)` — the message itself is redacted, only a category label is retained | `derived` | `derived` | derived | cycle |
| `input_tokens` / `output_tokens` / `cached_input_tokens` | **NOT PRESENT at any granularity** — local embedding retrieval (`all-MiniLM-L6-v2`), no host token accounting exists (G-G1) | n/a | `unavailable` | unavailable | n/a |
| `event_id` | **NOT PRESENT** — no native per-call unique identifier | n/a | `unavailable` | unavailable | n/a |
| `epoch_id` / `backlog_item_id` (correlation key) | **NOT PRESENT** — no native correlation to autoharness work-unit identity | n/a | `unavailable` | unavailable | n/a |
| `phase` / `agent_role` | **NOT PRESENT** | n/a | `unavailable` | unavailable | n/a |
| ingest volume (`files_total`/`files_synced`/`files_deleted`/`chunks_created`/`chunks_deleted`) | **adapter/schema gap — see G-G4.** No core `ToolTelemetryEvent` field exists for these, and they **must not** be prescribed as new `x-graphtor-*` root properties | `host_reported` | `observed` (retained out-of-band, not emitted in-event) | observed (out-of-band only) | cycle |

## Adapter gaps (G-G1 .. G-G5)

* **G-G1 (major) — no per-tool-call token economics.** Retrieval is local embedding
  (`all-MiniLM-L6-v2`); `input_tokens`/`output_tokens`/`cached_input_tokens` are **unavailable**
  at the source, at any granularity. An adapter **MUST** emit `metric_sources: unavailable` /
  `metric_quality: unavailable` for these three fields and **MUST NEVER emit a numeric `0`** —
  a `0` would falsely imply an observed zero-token call rather than "no token accounting
  exists here at all." Any token figure an adapter might compute for a graphtor call (e.g.
  estimating from returned document byte length) would itself be `derived`, never `observed`.
* **G-G2 — cycle-scoped vs. event-scoped mismatch.** `SyncMetrics` is scoped to an entire sync
  **cycle** (potentially many files), not a single tool invocation. A per-call
  `ToolTelemetryEvent` needs adapter-side wrapping to correctly attribute a cycle's aggregate
  `duration_ms`/`errors` to the operation that triggered it, without misattributing one cycle's
  totals to multiple unrelated calls (the same aggregate-misattribution caution documented for
  backlogit's `tool_usage`/`session_summary` records applies here).
* **G-G3 — no native identity/correlation/phase.** Same class of gap as engram's G-E1: no
  `event_id`, correlation key (`epoch_id`/`backlog_item_id`), `agent_role`, or `phase` exists at
  source; all are adapter-owned, and the correlation-key invariant (`anyOf: epoch_id |
  backlog_item_id`) applies identically.
* **G-G4 — ingest volume counts have no core field and cannot be `x-graphtor-*` root
  properties.** `files_total`/`files_synced`/`files_deleted`/`chunks_created`/`chunks_deleted`
  have no corresponding `ToolTelemetryEvent` root property. The schema's root object is
  `additionalProperties: false`, and the `^x-[a-z0-9-]+$` extension pattern governs only the
  **values** permitted inside `route_kind`/`freshness_state` (e.g. an `x-graphtor-sync` route
  kind value), **not** the addition of new arbitrary root-level fields. Therefore these counts
  **must be reported out-of-band** (e.g. in an adapter-side sync-cycle log or report, outside
  the `ToolTelemetryEvent` envelope) rather than fabricating an invalid event by inventing new
  root properties. Related caution: `routed_lookup_count` must be populated only from genuine
  routed/indexed search invocations — a large `files_*`/`chunks_*` ingest count is not evidence
  of retrieval offload and must not be substituted for it.
* **G-G5 — sensitivity (error messages + source paths).** `SyncStatus::Error(msg)` may embed
  local filesystem paths or other environment-specific detail, and `SourceSyncState` entries are
  keyed by source path. Both are classified **internal** per the schema's "ambiguous defaults to
  internal" rule; an adapter must redact the raw message/path and retain only a derived
  `error_kind` category (`redaction_applied: true`) before any non-local emission.

## Sensitivity note (AC4)

No raw sync-cycle output, no absolute filesystem/source paths, and no raw error-message text
are reproduced anywhere in this document — only field **names**, their `ToolTelemetryEvent`
mapping, and provenance classification. `SyncStatus::Error` message content and
`SourceSyncState` path keys are internal-sensitivity source fields per G-G5 above.

## Cross-references

* [`docs/telemetry/backlogit-evidence-map.md`](backlogit-evidence-map.md) — the 108-F precedent
  this document mirrors in structure and evidence-class vocabulary.
* [`docs/telemetry/engram-evidence-map.md`](engram-evidence-map.md) — the companion 082.001-T
  mapping for the first pack.
* [`docs/telemetry/cross-pack-adapter-gap-report.md`](cross-pack-adapter-gap-report.md) — the
  082.003-T consolidated synthesis across all three packs.
* [`docs/telemetry-reference.md`](../telemetry-reference.md) — `ToolTelemetryEvent` v1.0 /
  `ExecutionEpoch` v1.1 schema overviews.
* `schemas/tool-telemetry-event.schema.json` — authoritative field definitions, including the
  `additionalProperties: false` root constraint and the `^x-[a-z0-9-]+$` value-only extension
  pattern referenced in G-G4.
* `docs/decisions/2026-08-07-082F-cross-pack-measurability-evidence.md` — the evidence-gathering
  session this mapping formalizes.
