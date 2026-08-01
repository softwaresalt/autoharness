---
title: "Token-Efficiency Telemetry Event Emission and Deterministic Epoch Composition — DECIDED"
type: decided-plan
date: 2026-07-31
decided_at: 2026-08-01
supersedes: docs/archive/plans/2026-07-31-token-efficiency-telemetry-emission-plan.md
source: docs/decisions/2026-07-13-tokenmasterx-integration-spike.md
shipment: 107-S
feature: 084-F
decision: PASS
tags:
  - "telemetry"
  - "token-efficiency"
  - "primitive-7"
  - "084-F"
---

# Decided Plan — 084-F Token-Efficiency Telemetry Event Emission

Consolidated from the reviewed plan (plan-review cycle 1 **FAIL** → 3 P1
clarifications applied via `## Review Fixes` → cycle 2 **PASS**,
`Requires plan hardening: yes`). This decided-plan keeps only the actionable
decisions, surviving implementation units, and rationale; the verbose original
— including both review cycles and the full persona-coverage table — is
archived at `docs/archive/plans/2026-07-31-token-efficiency-telemetry-emission-plan.md`.
Two post-harvest hardening passes on PR #273 refined the implementation
further after harvest (pass 1: `parent_event_id`-linked expected-tool
accounting via the plan's own ratified Review Fix #2, local task-level fix,
commit `1c09212`; pass 2: the sole hosted Copilot review round, 6 hardening
fixes, commit `25ab0c8` — see
`docs/compound/107-S-084-F-copilot-review-fix-patterns.md`).

## Scope

Implement the already-ratified `schemas/tool-telemetry-event.schema.json`
(ToolTelemetryEvent v1.0) as a runtime model: an immutable event model, a
bounded workspace-contained JSONL event journal, a deterministic pure
event-to-epoch composer, generic CLI surfaces (`telemetry event`,
`telemetry record --compose-tool-events`), and Ship template/dogfood lifecycle
wiring. Does **not** redesign the schema, add Engram/backlogit/graphtor-docs/
intercom adapters (082-F), or add benchmark scenarios (085-F).

## Surviving Implementation Units (all 8 shipped)

| Unit | Task | Scope |
|---|---|---|
| U1 | 084.001-T | `ToolTelemetryEvent` runtime model — immutable, strict `from_mapping`, canonical UUID/timestamp handling, provenance completeness |
| U2 | 084.002-T | Shared segmented JSONL primitives extracted from `jsonl_sink.py` (byte-for-byte behavior preserved) |
| U3 | 084.003-T | Bounded `ToolTelemetryEvent` journal — dedupe by event ID, reject conflicting replays, exact-correlation reads |
| U4 | 084.004-T | Deterministic pure event-to-epoch composer — sum deltas, max cumulative totals, provenance-preserving, explicit expected-tool-gap derivation |
| U5 | 084.005-T | Epoch record composition integration — hybrid-input refusal, selected/ignored event counts and diagnostics |
| U6 | 084.006-T | CLI surface: `telemetry event --context-ref ... --from-json ... --json`, `telemetry record --compose-tool-events` |
| U7 | 084.007-T | Ship lifecycle template + dogfood parity — optional sanitized tool-event calls, close-time composition only on observed success |
| U8 | 084.008-T | `docs/telemetry-reference.md` contract documentation + schema/doc parity tests |

## Key Decisions

1. Implement the existing schema exactly; `from_mapping` fails closed on
   invalid correlation, enums, nonnegative quantities, and timestamps. CLI
   converts model errors to exit 2.
2. Reuse the existing JSONL segment enumeration, no-replace rollover,
   retention, and canonical digest primitives — no second file-handling
   implementation.
3. Event journal writes are observational and fail-open on I/O **after**
   payload validation; disabled telemetry short-circuits before any read.
4. `telemetry event --context-ref` merges only frozen correlation/sizing from
   the begin context and never re-reads backlogit.
5. `--compose-tool-events` selects exact epoch-ID matches; backlog-item
   fallback only when events lack epoch IDs and exactly match the context
   task; mismatches are diagnostic-only, never cross-attached.
6. Composer-owned fields and precomposed nonzero values are mutually exclusive
   in one close payload — hybrid input fails closed.
7. Expected-tool accounting uses explicit links: a direct invocation with
   `expected_tool == tool_name` counts one expected+observed opportunity; a
   separate expectation event is satisfied only by a later invocation whose
   `parent_event_id` equals the expectation's `event_id` **and** whose
   `tool_name` equals the expectation's `expected_tool`. Multiple retries under
   one expectation count once. Unlinked events never satisfy an expectation.
8. Apply the 095-S additive-provenance rule: numeric values stay numeric,
   trust lives in sibling source/quality maps, malformed labels normalize
   fail-closed to `unavailable`.
9. Cumulative token totals use max-per-stream (order-independent); timestamp
   order is used only to *diagnose* a later-lower value as a non-monotonic
   emitter warning — cumulative values are never summed (formalized further by
   PR #273 review-fix #4, `_non_monotonic_diagnostics()`).

## Post-Harvest PR Hardening (2 passes: 1 local task-level fix + 1 hosted Copilot review round, both resolved)

- **Pass 1 — local task-level fix** (`1c09212`, not a hosted Copilot PR
  comment): implemented `parent_event_id`-linked expected-tool accounting per
  Review-Fix #2 above, resolving a gap against the plan's own ratified
  requirement found during task build/local review.
- **Pass 2 — hosted Copilot review round** (`25ab0c8`, 6 threads, PR #273's
  sole hosted Copilot review round): (1) preserve caller-supplied `event_id`,
  UUID-generate only when omitted; (2) workspace-containment validation for
  `evidence_path`/`artifact_refs` including symlink-escape checks; (3)
  `read_events()` returns `unavailable` (not a partial set) on any segment I/O
  failure, so `record_epoch` skips composition rather than persisting an
  undercount; (4) non-monotonic-cumulative diagnostics for both token streams;
  (5) zero-valued metrics excluded from provenance-quality aggregation
  (`exclusiveMinimum: 0` respected); (6) non-object/non-null
  `work_sizing_snapshot` now fails strict ingestion instead of silently
  becoming `None`. Full per-fix rationale in
  `docs/compound/107-S-084-F-copilot-review-fix-patterns.md`.

## Constraints / Protected Invariants (preserved through harvest + PR hardening)

1. Events and epochs are never correlated across task/epoch boundaries; a
   context disagreement is diagnostic-only.
2. Delta metrics summed once; cumulative totals never summed; event IDs
   deduplicated before composition.
3. Composer-owned roll-ups and precomposed values are mutually exclusive.
4. Every populated metric carries source+quality provenance; unknown/malformed
   provenance degrades to `unavailable`.
5. No raw tool output, prompt, stderr, credential, or secret is persisted;
   evidence references are repo-local identifiers or sanitized/validated paths.
6. Disabled telemetry performs no payload read, validation, or filesystem
   write; enabled sink failures are fail-open and visible.
7. `WorkSizingSnapshot` comes only from the frozen begin context; event
   emission and close composition never re-read backlogit.
8. Existing non-composed `ExecutionEpoch` recording remains backward-compatible.

## Rejected Alternatives

- None proposed at the plan level beyond the excluded scope items (082-F
  adapters, 085-F benchmarks, schema redesign) — these are explicit
  non-goals, not rejected-during-review alternatives.

## Rollback

Rollback is invocation-first: remove/disable Ship event calls and omit
`--compose-tool-events`; existing `ExecutionEpoch` recording is unaffected.
Code rollback can then remove the event CLI/model/journal/composer without
migrating existing epoch data (additive, no schema/data migration). Revert
merge commit `364f6b07abc2418ec9f696603d5da4b9cf879256`.

## Revision Log

- **r1 — Plan Review Cycle 1 → Review Fixes** (pre-harvest, 2026-07-31): 3 P1
  clarifications (authoritative post-retention record; expected-tool machine
  correlation key; distinct trust boundaries for strict rejection vs.
  fail-closed provenance normalization) resolved; cycle 2 = PASS.
- **r2 — PR #273 local task-level fix** (`1c09212`, 084.004-T, not a hosted
  Copilot PR comment): implemented `parent_event_id`-linked expected-tool
  accounting.
- **r3 — PR #273 hosted Copilot review round** (`25ab0c8`, post-harvest, sole
  hosted Copilot review round on this PR): 6 hardening fixes listed above; all
  replied + resolved; P-018 gate `SATISFIED`.

## Closure

Shipped as shipment `107-S` / feature `084-F`, PR #273, merge commit
`364f6b07abc2418ec9f696603d5da4b9cf879256`. Full operational closure evidence:
`docs/closure/107-S-084-F-post-merge-closure.md`.
