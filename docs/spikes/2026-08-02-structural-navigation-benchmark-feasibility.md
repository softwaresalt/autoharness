---
title: "spike — Structural-Navigation Benchmark Feasibility (085-F)"
type: spike
date: 2026-08-02
route: claude-opus-4.8 / anthropic / high (P-013.5, inherited)
feature: 085-F
time_box: 2h (Stage staging investigation, read-only)
worktree: none (single main worktree; P-016 spike exception NOT exercised — no separate worktree created)
consumes:
  - schemas/execution-epoch.schema.json (ExecutionEpoch v1.1)
  - schemas/tool-telemetry-event.schema.json (ToolTelemetryEvent v1.0)
  - src/autoharness/telemetry/reader.py (read_epoch_records)
  - src/autoharness/telemetry/report.py (summarize_report / render_report)
  - src/autoharness/telemetry/aggregation.py (aggregate_epochs / derived_efficiency_metrics)
  - src/autoharness/eval/{matrix,runner,summary,reviewer}.py (existing A/B eval seams)
status: complete
---

## Question

Can a **reproducible** structural-navigation benchmark suite be built on top of the
already-shipped telemetry data path (ExecutionEpoch v1.1 / ToolTelemetryEvent v1.0),
producing honest before/after (baseline-vs-treatment) evidence — including neutral
and negative results — for tightened Engram-first structural routing, without
modifying the telemetry contract and without overstating host-observable data?

This is a **read-only staging investigation**. No source, template, schema, or config
file was mutated; no build/test suite was run; no branch/worktree was created.

## What the shipped telemetry path already gives us (verified, read-only)

1. **A stable read API.** `reader.read_epoch_records(config, source=...) -> TelemetryReadResult`
   returns normalized v1.1 `records`, a `status` (`ok`/`empty`/`unavailable`/`disabled`),
   and `diagnostics`. It reads SQLite (authoritative) and/or the segmented JSONL mirror,
   dedupes by `epoch_id`, and applies SQLite-over-JSONL precedence. A benchmark can read
   persisted epochs after each run without re-implementing sink parsing.

2. **A correlation spine.** Each epoch carries `backlog_item_id`, `feature_id`,
   `shipment_id`, `phase`, `session_id`, `agent_role`, `branch`, `commit_sha`,
   `workspace_id`. `report.filter_records` filters only on these persisted fields.
   A benchmark can tag every run with a synthetic `backlog_item_id`/`phase`
   (e.g. `phase=benchmark-baseline` vs `phase=benchmark-treatment`) and slice the two
   arms deterministically with `summarize_report(read_result, filters=...)`.

3. **The exact efficiency measures the feature needs.** `aggregate_epochs` /
   `derived_efficiency_metrics` already compute, over an epoch slice:
   - token consumption/generation (`input_tokens`, `output_tokens`),
   - `context_area_tokens`, `cumulative_input_tokens`,
   - routed-vs-raw usage (`routed_lookup_count`, `raw_file_read_count`, `raw_search_count`),
   - avoided reads (`avoided_file_read_count`, `avoided_read_estimated_tokens`),
   - `net_offload_tokens = avoided_read_estimated_tokens - tool_output_estimated_tokens`,
   - `cost_per_successful_epoch`, `cogs_usd`, `duration_seconds`,
   - `consumption_generation_ratio`, `gap_rate`, per-tool gap rates, size-group dispersion.
   Denominators are **aggregate totals, never averages of per-epoch ratios** — so an A/B
   delta computed from two slices is contract-correct without new math.

4. **First-class provenance for honest reporting.** Every populated metric carries a
   same-named `metric_sources`/`metric_quality` entry; derived ratios carry a **sparse
   additive** `derived_quality` sibling map (095-S pattern). The vocabulary is
   `observed | derived | estimated | not_applicable | unavailable`. Crucially, the model
   distinguishes **`unavailable` (host could not measure)** from an **observed zero**
   (`nullable field = unavailable; zero count = observed zero`, per telemetry-reference).
   `report._quality` degrades to the least-certain label across a slice and fail-closes
   malformed labels to `unavailable`. This is exactly the substrate honest reporting needs
   to avoid presenting an `unavailable` as a "0 win".

## What is NOT provided and must be built (the benchmark's real scope)

- **A scenario corpus** of representative structural-navigation tasks with **gold answers**
  (the correct target set), spanning positive / neutral / negative classes.
- **A baseline-vs-treatment executor** that runs each scenario under (a) raw file-read /
  grep navigation (routing OFF) and (b) Engram-first structural routing (routing ON), and
  emits an ExecutionEpoch per arm through the shipped `telemetry begin`/`telemetry record`
  path (correlated by synthetic `backlog_item_id` + `phase`).
- **A correctness scorer** — a *separate axis* from efficiency — that scores each arm's
  produced target set against the gold answer (precision/recall/exact-match). Efficiency
  wins must never be reported when correctness regressed.
- **A benchmark report layer** that composes the two arms' `summarize_report` outputs into
  per-scenario deltas + an aggregate, surfaces `metric_quality`/`derived_quality`, and
  enforces the honest-reporting rules.
- **Environment & repeatability controls**: pinned route, seeds, warm/cold index state,
  degraded-mode capture, N repeats with dispersion, and a versioned corpus manifest hash.

## Key findings / risks

- **F1 — Host-observable token data is often `unavailable`.** In many environments the host
  cannot report per-run `input_tokens`/`cogs_usd`; the reader marks these `unavailable`.
  A deterministic replay core (fixture-driven navigation) can reliably produce the
  **operations** counters that matter most for the routing hypothesis
  (`routed_lookup_count`, `raw_file_read_count`, `avoided_file_read_count`) as **observed**,
  while token/cost may be `estimated` or `unavailable`. The report MUST label them as such.
- **F2 — Determinism vs realism tension.** A fully-deterministic replay harness is
  CI-safe and reproducible but is a proxy for real agent behavior; a live agent run is
  realistic but non-deterministic and cost/token-noisy. Both, however, emit the *same*
  ExecutionEpoch shape, so the same reader/report path aggregates them. This argues for a
  **hybrid, deterministic-core-first** design (see deliberation).
- **F3 — Degraded routing is a first-class negative case, not an error.** `ENGRAM_DEGRADED`
  (stale/cold/unavailable index) makes the treatment arm fall back to raw reads plus index
  overhead. This is precisely the honest **negative** result the feature demands and must be
  captured (`stale_or_unavailable_index_count`, `degraded_tool_count`), not silently dropped.
- **F4 — No new CLI report subcommand exists** (telemetry-reference: "No CLI report
  subcommand is included in shipment 092-S"). The benchmark consumes the **library** report
  API directly; it does not depend on an unshipped CLI surface.
- **F5 — Provenance parity has parallel sites.** `aggregation._field_quality` (optimistic
  `observed` default) and `report._quality` (pessimistic `unavailable` default) intentionally
  differ (095-S). The benchmark report must consume these as-is and not "unify" them.

## Feasibility conclusion

**Feasible.** The reproducible benchmark can be built as an additive layer over the existing
`src/autoharness/eval` A/B harness and the shipped telemetry read/report/aggregation APIs,
with **zero telemetry-contract changes**. The dominant risk is *reporting integrity*
(overstating `unavailable` data, hiding negatives, conflating correctness with efficiency),
which is a design/hardening concern rather than a technical blocker — it routes this plan to
plan-hardening. Recommend Direction C (hybrid, deterministic-core-first) in the deliberation.

## Follow-ups handed to plan

- Reproducible deterministic core is the shippable unit; live-run mode is an additive opt-in
  reusing the same runner/report seams.
- Reporting must distinguish `unavailable` from observed-zero and mark estimated/derived
  aggregates; correctness is a separate, non-tradeable axis.
- Degraded/cold-index runs are retained and reported as negative/neutral, never discarded.
