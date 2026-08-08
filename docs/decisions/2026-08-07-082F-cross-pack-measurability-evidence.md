---
title: "082-F Cross-Pack Measurability Evidence Mapping (Engram + graphtor-docs)"
date: "2026-08-07"
description: "Read-only evidence-gathering session mapping real Engram and graphtor-docs telemetry surfaces to the ratified ToolTelemetryEvent v1.0 forward contract, with per-metric provenance (observed/estimated/derived/unavailable/unsafe) and adapter-gap report. Unblocks 082-F using operator-provided read-only local pack workspaces."
topic: "Which real pack telemetry surfaces map to ToolTelemetryEvent v1.0, and what adapter gaps remain before emission work?"
depth: "evidence"
decision_status: "evidence-complete"
doc_type: decision
source: docs/decisions/2026-08-07-082F-cross-pack-measurability-evidence.md
source_stash_ids:
  - "83854CD2"
backlog_items:
  - "082-F"
linked_artifacts:
  - "docs/decisions/2026-07-13-cross-pack-measurability-telemetry-deliberation.md"
  - "docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md"
  - ".backlogit/archive/108-F.md"
tags:
  - "capability-packs"
  - "telemetry"
  - "measurability"
  - "engram"
  - "graphtor-docs"
  - "082-F"
  - "evidence"
---

# 082-F Cross-Pack Measurability Evidence Mapping

## Status

**EVIDENCE-COMPLETE for Engram and graphtor-docs.** The 082-F access prerequisite
(operator-provided read access to pack workspaces or sanitized fixtures) is now
satisfied by authoritative read-only local source workspaces:

* `C:\Source\GitHub\engram` (`agent-engram`)
* `C:\Source\GitHub\graphtor` (`graphtor-docs`)
* `C:\Source\GitHub\backlogit` (`backlogit` — already mapped by **108-F**, done)

All inspection was **read-only**; no external workspace was mutated. `agent-intercom`
is **out of 082-F scope** (removed from the 082-F queue item's evidence list and
unavailable this session); its measurability is deferred to a future session that
has an intercom evidence surface.

This document is the 082-F evidence-mapping deliverable: it maps each pack's real
telemetry surface to the ratified `ToolTelemetryEvent` v1.0 forward contract
(`docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md`), classifies
each metric's provenance, and reports adapter gaps **before** any broad pack-adapter
emission work (which remains out of 082-F scope).

## Method and safety posture

* Source of truth: canonical `src/` trees (Rust) plus live local telemetry artifacts;
  `.copilot/session-state/**` mirrors were excluded as non-authoritative.
* No raw document/code snippet content, secrets, or user payloads were copied into
  this report. Only field names, schema shapes, provenance, and counts are recorded.
* Sensitivity defaults: ambiguous → internal. Workspace absolute paths and branch
  names appear in raw pack records and are classified **internal** (never emit to a
  remote sink without redaction).

## Provenance vocabulary (per ratified contract)

Each mapped metric is tagged with `metric_sources` ∈ {`host_reported`, `estimated`,
`derived`, `unavailable`, `not_applicable`} and `metric_quality` ∈ {`observed`,
`estimated`, `derived`, `unavailable`, `not_applicable`}. Every emitted metric MUST
carry a same-named entry in both maps; a numeric `0` is only emitted when the pack
actually observed zero.

---

## Pack 1 — agent-engram

### Real surface (observed)

* **Per-tool-call usage telemetry** — `UsageEvent` written to
  `.engram/metrics/{branch}/usage.jsonl` (`src/models/metrics.rs`), pinned schema
  `USAGE_SCHEMA_VERSION = 2`, additive-only, explicitly documented as the
  "autoharness contract". A live sample was confirmed for `get_daemon_status`.
* **Aggregate reports** — `get_token_savings_report` (token savings / avoided reads),
  `get_health_report` (index freshness / daemon health), `get_daemon_status`.

### Field mapping to ToolTelemetryEvent v1.0

| ToolTelemetryEvent field | Engram source field | metric_sources | metric_quality |
|---|---|---|---|
| `tool_name` | `tool_name` | host_reported | observed |
| `operation` | `tool_name` (same identity) | host_reported | observed |
| `server_name` | pack identity `agent-engram` | host_reported | observed |
| `tool_surface` | `mcp` (SSE) / `cli` | host_reported | observed |
| `timestamp` / `started_at` | `timestamp` (RFC 3339) | host_reported | observed |
| `duration_ms` | `latency_ms` | host_reported | observed |
| `status` | `outcome` (`success`/`error` → map to taxonomy) | host_reported | observed (mapped) |
| `result_count` | `result_count` / `results_returned` | host_reported | observed |
| `input_tokens` | `estimated_input_tokens` (`request_bytes/4`) | estimated | estimated |
| `output_tokens` | `estimated_output_tokens` (`response_bytes/4`) | estimated | estimated |
| `input_tokens` (attributed) | `prompt_tokens_attributed` (optional) | host_reported | observed |
| `output_tokens` (attributed) | `completion_tokens_attributed` (optional) | host_reported | observed |
| `cached_input_tokens` | `cached_tokens_attributed` (optional) | host_reported | observed |
| `tool_output_bytes` | `response_bytes` | host_reported | observed |
| `tool_output_estimated_tokens` | `estimated_tokens` (`response_bytes/4`) | estimated | estimated |
| `agent_role` | `agent_role` (optional `_meta.agent_role`) | host_reported | observed |
| `session_id` | `connection_id` (SSE UUID, optional) | host_reported | observed |
| `branch` | `branch` (sanitized) | host_reported | observed |
| `workspace_id` | `workspace` (abs path — **internal**) | host_reported | observed |
| correlation | `correlation_id` (dual-source, sanitized, 128-char cap) | host_reported | observed |
| `freshness_state` | derived from `get_health_report` | derived | derived |
| `route_kind` | `structural_graph` (fixed for engram graph tools) | derived | derived |
| `retrieval_pack` | `agent-engram` (constant) | host_reported | observed |
| `avoided_*` / savings | `get_token_savings_report` outputs | estimated | estimated |

### Engram gaps vs contract

* **G-E1**: No native `event_id`, `epoch_id`/`backlog_item_id`, `git commit_sha`, or
  `phase` — adapter must synthesize `event_id` and supply a correlation key
  (`epoch_id` **or** `backlog_item_id`) or the event is schema-invalid.
* **G-E2**: Token economics are **estimated** (bytes/4), except optional
  runtime-attributed fields; adapter must set `estimated` provenance and never
  relabel as `observed`.
* **G-E3**: No `metric_sources`/`metric_quality` maps at source — adapter-owned.
* **G-E4**: `outcome` is free-form (`success`/`error`); adapter maps to the 6-value
  status taxonomy (`degraded`/`blocked`/`skipped`/`operator_required` unobservable
  here → conservative mapping).
* **G-E5 (sensitivity)**: `workspace` abs path + `branch` are **internal**; redaction
  required before any non-local emission (`redaction_applied` accordingly).

---

## Pack 2 — graphtor-docs

### Real surface (observed)

* **Ingestion-cycle telemetry** — `SyncMetrics` (`src/sync/mod.rs`): `files_total`,
  `files_synced`, `files_deleted`, `chunks_created`, `chunks_deleted`, `duration_ms`,
  `errors`. Cycle-scoped, not per-tool-call.
* **Source freshness state** — `SourceSyncState` / `*.sync_state.json` per source
  (mtime-tracked); drives staleness.
* **Server/search status** — `get_status` MCP tool returns `SyncStatus`
  (`Idle`/`Syncing`/`InProgress`/`Done{files,chunks}`/`Complete{metrics}`/`Error`);
  document search returns `result_count`.

### Field mapping to ToolTelemetryEvent v1.0

| ToolTelemetryEvent field | graphtor source | metric_sources | metric_quality |
|---|---|---|---|
| `tool_name` / `operation` | MCP tool name (`get_status`, search, sync) | host_reported | observed |
| `server_name` | `graphtor-docs` | host_reported | observed |
| `tool_surface` | `mcp` / `cli` | host_reported | observed |
| `duration_ms` | `SyncMetrics.duration_ms` (sync ops) | host_reported | observed |
| `status` | `SyncStatus` → taxonomy (`Error`→`failed`, `Complete`→`success`) | host_reported | observed (mapped) |
| `result_count` | search `result_count` | host_reported | observed |
| `freshness_state` | `SourceSyncState` mtime vs source (`fresh`/`stale`) | derived | derived |
| `route_kind` | `doc_index` (constant for graphtor retrieval) | derived | derived |
| `retrieval_pack` | `graphtor-docs` (constant) | host_reported | observed |
| `routed_lookup_count` | ingest/search cycle counts | host_reported | observed |
| `error_kind` | `SyncStatus::Error(msg)` category (redact msg) | derived | derived |
| ingest volume | `files_*` / `chunks_*` (pack-namespaced extension) | host_reported | observed |

### graphtor gaps vs contract

* **G-G1 (major)**: **No per-tool-call token economics.** Retrieval is local
  embedding (`all-MiniLM-L6-v2`); `input_tokens`/`output_tokens`/`cached_input_tokens`
  are **unavailable** at source. Adapter MUST emit `unavailable` provenance, not `0`.
  Any token figure would be `derived` (estimated from returned bytes) at best.
* **G-G2**: Telemetry is **cycle-scoped** (`SyncMetrics`), not event-scoped; a
  per-call `ToolTelemetryEvent` needs adapter-side wrapping to attribute a cycle to
  the triggering operation.
* **G-G3**: No `event_id`/correlation/`agent_role`/`phase` at source — adapter-owned
  (same as G-E1); correlation-key invariant applies.
* **G-G4**: ingest counts (`files_*`, `chunks_*`) have no core field — carry as a
  `x-graphtor-*` namespaced extension (contract permits `^x-[a-z0-9-]+$`).
* **G-G5 (sensitivity)**: `SyncStatus::Error(msg)` and source paths may contain local
  filesystem detail → **internal**, redact `error_kind`/paths before non-local emit.

---

## Cross-pack synthesis

| Dimension | Engram | graphtor-docs | backlogit (108-F, done) |
|---|---|---|---|
| Per-call event surface | Yes (`usage.jsonl` v2) | No (cycle-scoped) | Yes (JSONL logs) |
| Token economics | Estimated (+optional attributed) | Unavailable | n/a (see 108-F) |
| Outcome taxonomy | free-form → mapped | `SyncStatus` → mapped | mapped (108-F) |
| Freshness/health | `get_health_report` (derived) | `sync_state` (derived) | index freshness |
| Correlation keys | adapter-synthesized | adapter-synthesized | backlog-native |
| `route_kind` | `structural_graph` | `doc_index` | `backlog_index` |
| Sensitivity risk | paths/branch (internal) | paths/error msg (internal) | item text (internal) |

### Observed vs estimated vs derived vs unavailable vs unsafe (summary)

* **Observed (host_reported)**: engram tool identity/timing/outcome/result/attributed
  tokens; graphtor sync counts/duration/status/result_count.
* **Estimated**: engram bytes/4 token counts and savings report.
* **Derived**: freshness_state, route_kind, error_kind category for both packs.
* **Unavailable**: graphtor per-call token economics (emit `unavailable`, never `0`).
* **Unsafe to emit raw**: absolute workspace paths, branch names, raw error messages,
  and any retrieved snippet content — all **internal**; require `redaction_applied`.

## Adapter-gap conclusion (feeds the plan)

1. Both packs can map to `ToolTelemetryEvent` v1.0 **as adapters** (autoharness-side
   wrappers), not by modifying the pack repos — consistent with the 079-F ownership
   model and the 108-F precedent.
2. Engram is the strongest evidence source (native per-call schema v2); graphtor
   needs adapter-side per-call wrapping and must declare token economics `unavailable`.
3. `agent-intercom` remains unmapped and is explicitly deferred.
4. No pack change is required for 082-F. The 082-F deliverable is **documentation**:
   the per-pack mapping tables above plus a consolidated adapter-gap + sensitivity
   report and a sanitized-fixture decision. Broad adapter emission is downstream and
   out of scope.

## Fixtures & sensitivity decision

* Do **not** commit raw pack telemetry. If fixtures are needed downstream, commit only
  **synthetic sanitized** single-line records (paths/branches replaced with tokens,
  no real error strings), clearly labeled, under a downstream feature — not 082-F.
* All cross-pack evidence classified **internal**; nothing here is emitted to a remote.
