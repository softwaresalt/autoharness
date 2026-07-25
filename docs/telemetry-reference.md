---
title: Telemetry Reference
description: ExecutionEpoch v1.1, ToolTelemetryEvent v1.0, pre-execution contexts, local sinks, readers, aggregation, and report boundaries.
---

# Telemetry Reference

> **Navigation**: [README](../README.md) · [Architecture](ARCHITECTURE.md) · [Validation Gates](gates-reference.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md)

## Ownership Model

autoharness owns the local epoch time-series telemetry contract, repo-local SQLite/JSONL persistence, reader normalization, aggregation formulas, report helpers, and eval-facing summaries. backlogit owns work-state traceability, task IDs, shipment membership, dependencies, comments, and task-level planned `size`. agent-engram is the structural/graph ingestion consumer for emitted telemetry; telemetry modules do not import agent-engram or CozoDB.

## ExecutionEpoch v1.1

`ExecutionEpoch v1.1` is the persisted task-close record. Required serialized fields are `schema_version`, `epoch_id`, `task_id`, `backlog_item_id`, `timestamp`, `route`, `economics`, `operations`, and `outcome`.

| Area | Fields |
|---|---|
| Root correlation | `workspace_id`, `session_id`, `agent_role`, `phase`, `backlog_item_id`, `feature_id`, `shipment_id`, `branch`, `commit_sha` |
| Route | `models`, `route_kinds`, derived `primary_route_kind` |
| Economics | `input_tokens`, `output_tokens`, `cached_input_tokens`, `cumulative_input_tokens`, `cumulative_output_tokens`, `context_tokens_before`, `context_tokens_after`, `context_area_tokens`, `avoided_read_estimated_tokens`, `tool_output_estimated_tokens`, `cogs_usd`, `duration_seconds`, `metric_sources`, `metric_quality` |
| Operations | `cli_tools`, `tool_surfaces`, `retrieval_packs`, `route_kind_counts`, routed/raw counts, avoided-read counts, `tool_output_bytes`, expected/observed/missing tool count maps, `degraded_tool_count`, `stale_or_unavailable_index_count`, provenance maps |
| Outcome | `gate_exit_codes`, `tool_failure_count`, `tool_degraded_count`, `tool_gap_count`, provenance maps |
| Sizing | optional nested `WorkSizingSnapshot` |

nullable metric fields mean the value is unavailable; zero counts mean an observed zero. Every populated metric must have same-named `metric_sources` and `metric_quality` entries. Quality values distinguish observed, estimated, derived, unavailable, and not-applicable data so reports never imply false precision.

## WorkSizingSnapshot

`WorkSizingSnapshot` is captured once at the `pre_execution` boundary and then carried through the close record unchanged. It includes `snapshot_at`, `snapshot_boundary`, `task_size_label`, null-by-contract feature/shipment size labels, per-level `sizing_sources`, `sizing_source_revisions`, `sizing_ruleset_versions`, feature child count/histogram/hash, and shipment manifest count/histogram/hash.

Backlogit stores task-level `custom_fields.size` only. Feature and shipment labels are null-by-contract and expose computed composition instead. Composition uses the same canonical sorted unique task-ID set for count, histogram, and membership hash. The histogram uses `XS`, `S`, `M`, `L`, `XL`, plus `unsized`; skipped unresolved IDs are excluded from both count and histogram. There is no `unavailable` histogram bucket. The membership hash is lowercase SHA-256 over a compact UTF-8 JSON array of sorted unique task IDs; unavailable membership yields `null`.

Size labels are ordinal and level-relative. Reports may group by labels and show dispersion or monotonicity observations, but cost-per-size-point stays `unavailable` unless a future named/versioned label-to-point mapping is present. `autoharness gate size` task labels are deterministic metadata complexity/scope bucket values, not elapsed time; the 2-hour rule remains a separate task-scope ceiling.

## Begin and Record Lifecycle

Ship invokes `autoharness telemetry begin --task-id <id> --backlog-item-id <id> --feature-id <feature> --shipment-id <shipment> --capture-backlogit-sizing --json` immediately after task claim. Begin creates a workspace-contained context artifact under the configured metrics `contexts/` directory and returns `context_ref`, stable `epoch_id`, and a canonical context digest. Path-safe context artifact rules reject absolute refs, traversal, separator tricks, symlink escapes, mismatched filename stems, and digest mismatches.

At task close, Ship invokes `autoharness telemetry record --context-ref <context_ref> --from-json <epoch-payload> --json`. Record merges frozen identity/correlation/sizing from begin with close-time roll-up metrics. It does not re-read backlogit size, hierarchy, shipment membership, or any other mutable planning state at close.

Replay semantics are first-write immutable. Sinks store or derive `payload_digest`; identical replays are idempotent, partial sink retries repair only missing sinks when the digest matches, and conflicting replays are diagnosed as `conflict_rejected` without replacing the first accepted content.

## Sinks, Readers, Aggregation, and Reports

SQLite persists queryable columns plus JSON payload columns for every v1.1 field. JSONL writes the exact `ExecutionEpoch.to_record()` object. Readers normalize legacy v1.0 rows to v1.1, mark unknown metric provenance as `unavailable`, deduplicate by `epoch_id`, and apply SQLite-over-JSONL precedence in combined mode.

Aggregation computes UTC-normalized date buckets, token consumption, token generation, context-area estimates, COGS, duration, routed-vs-raw usage, avoided-read counts/token estimates, expected counts, observed counts, missing counts, per-tool gap rates, size-label distributions, within-size dispersion, and derived efficiency metrics. Derived metrics include `net_offload_tokens`, `consumption_generation_ratio`, `gap_rate`, and `cost_per_successful_epoch`; denominators are aggregate totals, never averages of per-epoch ratios. If an operand is null/unavailable or the denominator is zero, the metric is `unavailable`.

Reports filter only on persisted fields such as `session_id`, `backlog_item_id`, `feature_id`, `shipment_id`, `phase`, `branch`, and `commit_sha`. No CLI report subcommand is included in shipment 092-S.

## ToolTelemetryEvent v1.0

`ToolTelemetryEvent v1.0` is a forward-only schema contract. It describes future granular event identity, correlation, optional `work_sizing_snapshot`, tool, timing, outcome, token economics, provenance maps, offload, retrieval health, evidence, and safety fields. live event model/sink/emission and deterministic event-to-epoch composition are deferred to 084-F if needed, not part of 079-F core.

## Cross-Pack Sequencing

Shipment 092-S is fail-closed on the released backlogit hierarchical-sizing contract and task 079.013-T, plus the 079.014-T begin context, 079.016-T record-close/idempotency, and 079.015-T Ship host handoff tasks. 082-F maps real pack evidence before broad adapter implementation. 084-F implements live token-efficiency event emission if required. 085-F builds benchmark suites after stable telemetry inputs exist.

## Rollback and Disabled Mode

Set `telemetry.mode: none` or omit the `telemetry` block to disable telemetry. Begin returns a structured disabled/no-op result, record skips payload parsing when disabled, and no sink files are created.

