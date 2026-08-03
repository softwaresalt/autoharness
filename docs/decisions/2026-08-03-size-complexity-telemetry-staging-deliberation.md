---
title: "Size + Complexity as first-class staging metadata, and backlogit telemetry evidence mapping"
type: deliberation
date: 2026-08-03
route: claude-opus-4.8 / anthropic / high (P-013.5)
scope: DARK_MODE (stash 34D50F2D, 936C68F3; feature 082-F backlogit carve-out)
informs: [082-F]
stash_refs: [34D50F2D, 936C68F3]
---

# Deliberation: Size + Complexity first-class in staging, and backlogit telemetry evidence mapping

## Problem Frame

<!-- BEGIN:problem-frame -->
The operator asked to (1) continue the two remaining active stash entries, (2) make
task-level `size` and `complexity` first-class in Stage task creation without conflating
effort and reasoning/risk, and (3) map backlogit telemetry evidence to the ratified
autoharness `ToolTelemetryEvent`/`ExecutionEpoch` contracts, distinguishing observed vs
derived vs unavailable fields while protecting sensitivity. backlogit 1.8.0 (commit
fd8d2c9d) now exposes task `complexity` (trivial|low|medium|high), `size` (XS..XL) with
`size_source` (human|agent|derived) and `size_ruleset_version`, session/tool telemetry
records, and `size_composition` shipment rollups — so the access prerequisite of feature
082-F is now satisfied **for backlogit only**.

Two boundary questions gate the two legacy stash entries:
- 34D50F2D candidates (a) unified CLI/MCP action-observation execution abstraction,
  (c) background Verification & Compaction layer, (d) crash-resumption + context-pruning —
  are LARGE, architectural, and per archived deliberation 011-DL each require their own
  spike → impl-plan → review before any harvest. Blind-harvesting them would violate the
  2-hour rule and P-003 (unverifiable tasks).
- 936C68F3 has an EXTERNAL "backlogit-internal active→queued transition guard" previously
  routed upstream, plus a decision-gated true self-repair (part 2) that requires the
  operator to deliberately lift the report-and-halt / no-auto-repair stance first.
<!-- END:problem-frame -->

## Evidence gathered (read-only)

<!-- BEGIN:notes -->
Upstream backlogit 1.8.0 (C:\Source\GitHub\backlogit @ fd8d2c9d, read-only):
- `internal/core/artifact_complexity.go` + `internal/config/defaults.go`: `complexity` is a
  **task-only** enum `[trivial, low, medium, high]`, validated against the type header-def.
  Backlogit help states the ratified semantics verbatim: **"size = implementation volume;
  complexity = implementation difficulty and uncertainty."** This is the non-conflation
  contract, authored upstream — autoharness must preserve, not redefine, it.
- `internal/core/artifact_size.go`: `size` provenance flows through the single seam
  `SetArtifactSizeWithProvenance`; **a non-empty `size_source` requires a non-empty
  `size_ruleset_version`** (provenance-completeness enforced before write). CLI flags
  `--size` / `--size-source` / `--size-ruleset-version` are one mutation group; `--complexity`
  is a separate, mutually-exclusive mutation.
- `docs/telemetry-fields.md`: harvested `session_summary` (total/prompt/completion/cached
  tokens, model_calls, tool_calls, tokens_by_model, tool_calls_by_server, completed_tasks,
  tokens_per_task, compaction_count, peak_utilization, remaining_capacity, depletion_rate,
  max_context_tokens) and `tool_usage` (server_name, tool_name, call_count,
  total_duration_ms); SQLite `telemetry_sessions` / `telemetry_tool_usage`.
- `internal/core/shipment.go:isValidShipmentTransition`: shipment transitions permit ONLY
  `queued→active` and `active→shipped|abandoned`. **`active→queued` is structurally invalid**
  and returns `ErrShipmentConflict`; `ClaimShipment` (061-F) is all-or-nothing with rollback
  to fully queued on mid-flight failure. This is exactly the guard 936C68F3's EXTERNAL part
  requested → **superseded upstream**.

Autoharness ratified contracts (read-only):
- `schemas/tool-telemetry-event/1.0.0.schema.json` (ToolTelemetryEvent v1.0, forward contract):
  identity/correlation (incl. `feature_id`, `shipment_id`), optional `work_sizing_snapshot`
  (WorkSizingSnapshot — carries level-qualified SIZE labels, sources, ruleset versions,
  child/manifest counts, size histograms, membership hashes; **no complexity field**),
  token economics, `metric_sources`/`metric_quality` maps
  (host_reported|estimated|derived|unavailable|not_applicable|host|backlogit|operator and
  observed|estimated|derived|unavailable|not_applicable), `retrieval_pack` (accepts
  `backlogit`), `route_kind` (accepts `backlog_index`), sensitivity/redaction fields.
- `docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md`: autoharness owns the
  local epoch time-series store + reporting; backlogit owns work-state, planned sizing,
  hierarchy/membership, traceability; other packs expose adapters. 082-F is the evidence step;
  084-F is emission. Close path must NOT re-read mutable backlogit state and call it planned.

Gap identified: WorkSizingSnapshot carries size but there is **no complexity dimension**
anywhere in the event contract. Making complexity first-class in telemetry is genuinely
net-new, and must be added as a structurally-separate field (not nested inside the sizing
snapshot) so effort (size) and reasoning/risk (complexity) are never conflated.
<!-- END:notes -->

## Options

<!-- BEGIN:options -->
A) Single coherent shipment covering both staging-workflow changes and telemetry-contract
   changes. REJECTED as the primary shape: the two concerns touch different product surfaces
   (agent/skill templates vs schema/docs) and have a real semantic dependency — complexity
   telemetry mapping is only defensible once the size/complexity semantics and validation are
   established in the staging workflow.
B) (CHOSEN) Two ordered shipments in a blocks chain: S1 makes size+complexity first-class in
   the staging workflow (semantics, enum validation, 2h-rule/granularity gating); S2 maps
   backlogit telemetry evidence to ToolTelemetryEvent and adds a non-conflated complexity
   dimension + sensitivity guard, and is the unblocked backlogit carve-out of 082-F. Only S1
   is queued/eligible; S2 is blocked on S1.
C) Blind-harvest 34D50F2D (a)/(c)/(d) and/or 936C68F3 part (2) now. REJECTED: (a)/(c)/(d) are
   large/architectural (011-DL) and out of the small-coherent-shipment envelope; 936C68F3
   part (2) is operator-decision-gated (report-and-halt stance not lifted). Harvesting either
   would produce non-granular, unverifiable, or policy-blocked tasks (P-003 / P-010 risk).
<!-- END:options -->

## Chosen Direction

<!-- BEGIN:chosen-direction -->
Option B. Non-conflation is the load-bearing invariant, adopted verbatim from backlogit's
released contract:
- **size** = implementation VOLUME/effort → enum XS|S|M|L|XL; drives the volume half of the
  2-hour rule.
- **complexity** = implementation DIFFICULTY and UNCERTAINTY (reasoning/risk) → enum
  trivial|low|medium|high; drives a reliability gate independent of size. A physically small
  task with high uncertainty (e.g. schema semantics) must be split or de-risked even when its
  size is S/XS. The two axes are recorded, validated, and reported SEPARATELY; no arithmetic
  combines them into a single scalar.

Every task Stage creates from now on MUST carry both `size` (with `size_source: agent` and a
concrete `size_ruleset_version`, honoring backlogit's provenance-completeness rule) and
`complexity`, with both enums validated before write. This session applies the semantics to
its own harvested tasks as the first exemplar.

Shipment shaping: S1 (F1) queued/eligible; S2 (F2) blocked on S1 via a shipment blocks edge.
S2 is the backlogit-only carve-out that unblocks the backlogit portion of 082-F; the Engram,
graphtor-docs, and agent-intercom portions of 082-F remain blocked-on-operator (access still
absent).

Stash dispositions:
- 34D50F2D: candidates (a)/(c)/(d) remain explicitly DEFERRED (not harvested this session);
  entry stays ACTIVE as the living tracker. This session advances only the cross-cutting
  size/complexity + backlogit-telemetry measurability outcome, which lightly touches the
  telemetry/metrics facet of (c) without harvesting (c) itself.
- 936C68F3: EXTERNAL active→queued guard → RESOLVED-UPSTREAM (superseded by
  `isValidShipmentTransition` + 061-F all-or-nothing claim rollback); part (2) decision-gated
  self-repair remains DEFERRED pending operator lift of the report-and-halt stance. Entry
  stays ACTIVE as the tracker for part (2) only; no harvest.
<!-- END:chosen-direction -->

## Open Questions

<!-- BEGIN:open-questions -->
1. backlogit complexity is task-only; features/shipments have no complexity. Feature/shipment
   complexity aggregation is intentionally OUT of scope here — telemetry carries task-level
   complexity only, and feature/shipment complexity fields map to `not_applicable`. Any future
   rollup semantics need their own decision.
2. Placement of the complexity dimension in the event contract: chosen approach is a
   structurally-separate optional field/section, NOT nested inside WorkSizingSnapshot, to
   preserve non-conflation. Final field shape is settled during S2/T2.2 review.
3. 34D50F2D lead-capability selection and spec model-pick reconciliation remain operator
   decisions (unchanged from 011-DL); staging cannot self-authorize them.
<!-- END:open-questions -->
