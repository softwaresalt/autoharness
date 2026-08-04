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

The JSONL mirror is a best-effort, concurrent-writer-safe file, not the source of truth: once the active `execution_epochs.jsonl` segment reaches a size threshold it rolls over into sealed segments (`execution_epochs.jsonl.NNNNN`) via a no-replace generation claim so a concurrent rollover never clobbers a sealed segment, and a bounded retention window prunes the oldest sealed segments. Retention is intentionally lossy on the mirror only — SQLite retains authoritative history and is never pruned. Both the append-time replay preflight and the reader span the active segment plus all retained sealed segments, so `epoch_id` dedupe, SQLite-over-JSONL precedence, and malformed-line skipping hold across rotated segments (within the retention horizon); a late append into a just-sealed segment is reconciled on read.

Aggregation computes UTC-normalized date buckets, token consumption, token generation, context-area estimates, COGS, duration, routed-vs-raw usage, avoided-read counts/token estimates, expected counts, observed counts, missing counts, per-tool gap rates, size-label distributions, within-size dispersion, and derived efficiency metrics. Derived metrics include `net_offload_tokens`, `consumption_generation_ratio`, `gap_rate`, and `cost_per_successful_epoch`; denominators are aggregate totals, never averages of per-epoch ratios. If an operand is null/unavailable or the denominator is zero, the metric is `unavailable`. Each derived ratio value stays machine-readable — a bare number or the `unavailable` sentinel — and never embeds provenance text. When a usable ratio was computed from `estimated` or `derived` operands, the marker is surfaced additively in a sibling `derived_quality` map keyed by metric name (fully `observed` ratios and `unavailable` values are omitted), so downstream JSON consumers can compare the numbers while still seeing operand provenance.

Reports filter only on persisted fields such as `session_id`, `backlog_item_id`, `feature_id`, `shipment_id`, `phase`, `branch`, and `commit_sha`. No CLI report subcommand is included in shipment 092-S.

## ToolTelemetryEvent v1.0

`ToolTelemetryEvent v1.0` is a forward-only schema contract. It describes future granular event identity, correlation, optional `work_sizing_snapshot`, tool, timing, outcome, token economics, provenance maps, offload, retrieval health, evidence, and safety fields. As of 079-F, live event model/sink/emission and deterministic event-to-epoch composition were deferred to 084-F if needed, not part of 079-F core. 084-F implemented that deferred scope; see [Tool-Event Emission and Composition (084-F)](#tool-event-emission-and-composition-084-f) below. The published schema (`schemas/tool-telemetry-event.schema.json`) itself did not change — 084-F only adds a runtime model, journal, composer, and CLI surface that implement the existing contract.

### Non-conflated complexity dimension (108-F)

108-F (108.002-T/108.004-T) added two additive, optional, top-level fields — **not** a
version bump, since both are nullable and every previously-valid record stays valid:

* `task_complexity_label` — `trivial | low | medium | high | null`, backlogit's task-only
  implementation-difficulty/uncertainty label.
* `complexity_source` — provenance for the label, drawn from the same `metric_sources`
  vocabulary used elsewhere in this schema (e.g. `backlogit`, `operator`, `unavailable`).

Both fields are **structurally separate top-level properties**, deliberately NOT nested
inside `work_sizing_snapshot`: `size` (implementation volume/effort, feature/shipment/task
scoped) and `complexity` (implementation difficulty/uncertainty, task-only) answer different
questions and must never be combined into one field or scalar
([size-complexity-reference.md](size-complexity-reference.md)). Feature- and shipment-level
`task_complexity_label` is `not_applicable` — backlogit's `complexity` field is task-only. See
[docs/telemetry/backlogit-evidence-map.md](telemetry/backlogit-evidence-map.md) for the full
backlogit-evidence-to-field mapping and
[docs/telemetry/backlogit-sensitivity-guardrails.md](telemetry/backlogit-sensitivity-guardrails.md)
for sensitivity/redaction guardrails on backlogit-sourced evidence. The live runtime model
(`src/autoharness/telemetry/tool_event.py`), composer, and JSONL journal all round-trip these
fields (108.004-T); no emitter call sites changed (084-F still owns emission).

## Tool-Event Emission and Composition (084-F)

### Event Lifecycle

1. **Begin** — Ship (or any host) runs `autoharness telemetry begin ... --json` as documented above, producing `context_ref` and a stable `epoch_id`.
2. **Optional event emission** — while a task is in progress, tool use MAY emit individual `ToolTelemetryEvent` records with `autoharness telemetry event --context-ref <context_ref> --from-json <event-payload> --json`. Emission is entirely observational: it never blocks work, and a disabled telemetry config makes it a no-op before any payload is read or parsed (mirroring `telemetry record`'s disabled-mode contract). Correlation identity (`epoch_id`/`backlog_item_id`) and any other frozen context fields are merged onto the event from the begin context; the event payload's own identity fields must agree with the context or the call is rejected.
3. **compose-on-record** — at task close, `autoharness telemetry record --context-ref <context_ref> --from-json <epoch-payload> --compose-tool-events --json` opts in to composing the retained, deduplicated events correlated to that context into the closing `ExecutionEpoch` before dispatch to sinks. Omitting `--compose-tool-events` reproduces today's close-payload-only behavior exactly, with zero journal reads.

### Journal Retention and Rotation

The event journal (`src/autoharness/telemetry/tool_event_jsonl.py`) is a bounded, segmented JSONL journal built on the same shared primitives extracted from the execution-epoch JSONL sink into `src/autoharness/telemetry/_jsonl_segments.py` (segment enumeration, no-replace rollover, retention pruning, canonical-line scan, file identity). It does not duplicate or diverge from the epoch mirror's rotation/retention model described above — see that section for the shared no-replace generation-claim and bounded-retention mechanics, which apply identically to the event journal. The journal path is derived from the enabled telemetry directory beside the configured epoch database; there is no separate event-journal configuration field. Appending an event is idempotent by `event_id`: an identical replay is a no-op, and a conflicting replay (same `event_id`, different canonical content) is rejected with a diagnostic rather than silently overwritten. Reads stream matches across the active segment plus all retained sealed segments (cross-segment correlation), skip malformed lines with a diagnostic instead of crashing, and are stable under non-ASCII content.

### Composer Ownership and Hybrid Refusal

Composition treats a fixed set of `ExecutionEpoch` fields as **composer-owned** once `--compose-tool-events` is requested: `route.route_kinds`; the token/context-area/COGS-adjacent economics metrics other than `cogs_usd` and `duration_seconds` (which remain close-owned); the entire `operations` payload class (`cli_tools`, `tool_surfaces`, `retrieval_packs`, routed/raw counts, avoided-read counts, `tool_output_bytes`, expected/observed/missing tool count maps, `degraded_tool_count`, `stale_or_unavailable_index_count`); and `outcome.tool_failure_count`/`tool_degraded_count`/`tool_gap_count` (`gate_exit_codes` stays close-owned). `cogs_usd`, `duration_seconds`, and `gate_exit_codes` are always close-payload owned, composed or not.

If the close payload already supplies nonzero values for any composer-owned field **and** composition is requested, the record call fails closed with a controlled `ToolEventCompositionError` — this is a hybrid input and is refused rather than silently picking a winner, because merging on top of it would double count. Any other composition failure (a missing or unreadable event journal, or an unexpected error while reading/composing events) fails open instead: the diagnostic is recorded in the composition summary and the original, unmerged close payload is recorded exactly as it would be with `--compose-tool-events` omitted. A missing event journal therefore never blocks task completion — the existing close-payload-only path always remains fully valid.

### Expectation Semantics

An event carrying a non-null `expected_tool` records one explicit expected opportunity for that tool. Satisfaction uses explicit event links (the plan's `## Review Fixes` item 2): a direct invocation event (never expectation-only) whose own `expected_tool` equals its own `tool_name` counts one expected AND one observed opportunity in that same event. A separate, standalone expectation event (operation `expect`, status `skipped`) is identified by its `event_id`; a later invocation or retry satisfies it only when that invocation's `parent_event_id` equals the expectation event's `event_id` and its `tool_name` equals the expectation's `expected_tool`. Multiple retries linked to the same expectation event count one expected opportunity and at most one observed opportunity — never per-retry, never double counted. Unlinked events — an invocation with no `parent_event_id`, or a `parent_event_id` that does not resolve to a standalone expectation event in the correlated set — never satisfy an expectation, even when the tool name matches. A status-only expectation record never counts as an invocation by itself. The `parent_event_id` linkage above governs *how* an event may satisfy an expectation before the result folds into the persisted epoch schema's storage shape, which remains **flat per-tool maps with no per-operation dimension** (`expected_tool_counts`/`observed_tool_counts`/`missing_expected_tool_counts` are keyed by tool name only). Missing counts clamp at zero and never go negative. Failed and degraded invocations are counted separately from "missing": a failed or degraded invocation of an expected tool still satisfies that expectation and is never conflated with a tool that was never invoked at all.

### Provenance

Composition reuses the 095-S additive-provenance pattern (`docs/compound/095-S-derived-metric-provenance-additive-map.md`): every composer-populated metric stays strictly numeric, and provenance travels in the existing additive sibling `metric_sources`/`metric_quality` maps keyed by metric name — never inline or interleaved with the value. Populated composer-derived economics metrics report source `"derived"` (the value is an aggregate over per-tool events, not a single host report) and the worst (least-trusted) quality label contributed by any event for that metric name. Malformed or out-of-vocabulary labels normalize fail-closed rather than crashing or silently passing through.

### Privacy and Safety

Only schema-shaped fields may ever be persisted in the event journal: no raw tool output, prompts, stderr, or credentials are captured by `ToolTelemetryEvent`, matching the plan's Risks section (secret leakage — schema fields only, safe fingerprints and paths, no raw output). All journal and context artifacts stay workspace-contained; path-safe rules reject absolute paths, traversal, and symlink escapes exactly as they do for the existing begin-context artifacts.

### Rollback

Tool-event emission and composition are opt-in end to end. Omitting `telemetry event` calls during a task, or omitting `--compose-tool-events` at close, reverts to today's close-payload-only behavior with zero event-journal reads — there is no migration or backfill step, and the event journal is purely additive alongside the existing epoch sinks.

### CLI Examples

```bash
# Emit a sanitized tool-use event mid-task (fails open; never blocks work)
autoharness telemetry event --context-ref .autoharness/metrics/contexts/<ref>.json \
  --from-json event-payload.json --json

# Close the task, composing retained events into the epoch
autoharness telemetry record --context-ref .autoharness/metrics/contexts/<ref>.json \
  --from-json epoch-payload.json --compose-tool-events --json

# Close the task without composition (unchanged, zero journal reads)
autoharness telemetry record --context-ref .autoharness/metrics/contexts/<ref>.json \
  --from-json epoch-payload.json --json
```

## Cross-Pack Sequencing

Shipment 092-S is fail-closed on the released backlogit hierarchical-sizing contract and task 079.013-T, plus the 079.014-T begin context, 079.016-T record-close/idempotency, and 079.015-T Ship host handoff tasks. 082-F maps real pack evidence before broad adapter implementation. 084-F implements live token-efficiency event emission if required — see [Tool-Event Emission and Composition (084-F)](#tool-event-emission-and-composition-084-f) for the delivered contract. 085-F builds benchmark suites after stable telemetry inputs exist.

## Rollback and Disabled Mode

Set `telemetry.mode: none` or omit the `telemetry` block to disable telemetry. Begin returns a structured disabled/no-op result, record skips payload parsing when disabled, and no sink files are created.

