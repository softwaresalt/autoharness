---
title: "Token-Efficiency Telemetry Event Emission and Deterministic Epoch Composition"
date: "2026-07-31"
description: "Implement the published ToolTelemetryEvent v1.0 runtime contract, bounded local event journal, and deterministic event-to-epoch roll-ups for 084-F."
doc_type: plan
source: docs/plans/2026-07-31-token-efficiency-telemetry-emission-plan.md
feature: "084-F"
decision_source:
  - "docs/decisions/2026-07-13-tokenmasterx-integration-spike.md"
  - "docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md"
relevant_solutions:
  - "docs/compound/095-S-derived-metric-provenance-additive-map.md"
requires_plan_hardening: "yes"
plan_review_verdict: "pass"
tags: [telemetry, token-efficiency, primitive-7, 084-F]
superseded_by: docs/plans/2026-07-31-token-efficiency-telemetry-emission-decided-plan.md
archived_at: 2026-08-01
archived_reason: "P-020 post-merge context compaction (107-S/084-F closure) — consolidated into decided-plan"
---

> **Archived**: this verbose original (full deliberation + both plan-review
> cycles) has been consolidated into
> `docs/plans/2026-07-31-token-efficiency-telemetry-emission-decided-plan.md`.
> Retained here for traceability.

# Token-Efficiency Telemetry Event Emission and Deterministic Epoch Composition

## Problem Frame

084-F is dependency-eligible because 079-F and shipment 092-S are terminal. The repository already publishes `schemas/tool-telemetry-event.schema.json` as the ratified ToolTelemetryEvent v1.0 forward contract and already persists ExecutionEpoch v1.1 summaries. The remaining gap is runtime emission: there is no typed event model, bounded event journal, or deterministic composer that turns granular tool events into the ratified epoch token, context-area, routed/raw, avoided-read, outcome, and expected-tool-gap fields.

The implementation must preserve the 079-F ownership boundary. Autoharness owns repo-local telemetry. Agent-engram remains the single graph authority. Broad capability-pack adapters remain gated by 082-F, and structural-navigation benchmarks remain 085-F. No raw tool output, prompts, stderr, credentials, or secrets may be persisted.

## Scope and Non-Goals

* Implement the existing ToolTelemetryEvent v1.0 schema as a runtime model; do not redesign the schema.
* Add a workspace-contained `tool_events.jsonl` journal with bounded segmented retention and first-write immutability by `event_id`.
* Add deterministic event-to-epoch composition for token deltas, final cumulative totals, context area, offload counts, route/tool counts, outcome counts, and explicit expected-tool gaps.
* Add generic CLI surfaces used equally by agents and direct callers: `autoharness telemetry event` and `telemetry record --compose-tool-events`.
* Wire Ship template and dogfood instructions to use the same context-bound event/record lifecycle when telemetry is enabled.
* Update contract documentation and parity tests.
* Do not add Engram, backlogit, graphtor-docs, or intercom adapters; 082-F owns evidence-gated adapters.
* Do not add benchmark scenarios or savings claims; 085-F owns benchmark proof.
* Do not change the graph stack, import agent-engram or CozoDB, persist raw content, or change telemetry disabled-mode behavior.
* Treat any contradiction in the published schema as a halt-and-replan event rather than silent schema expansion.

## Requirements Trace

* R1 — Runtime contract: parse, validate, canonicalize, and round-trip every published ToolTelemetryEvent field.
* R2 — Deterministic roll-up: sum delta metrics, use final or maximum cumulative totals, preserve consumption/generation separation, and derive expected-tool gaps from explicit expectations.
* R3 — Provenance: every populated metric has same-named source and quality; numeric fields remain numeric and quality stays in additive sibling maps.
* R4 — Safety: event persistence is workspace-contained, bounded, sanitized, secret-safe, and fail-open after validation.
* R5 — Replay: identical event replays are idempotent; conflicting same-ID content is rejected and reported; composition deduplicates by event ID.
* R6 — Parity: Ship and direct CLI users use the same event and composition commands.

## Decisions and Rationale

1. Implement the existing schema exactly. `ToolTelemetryEvent.from_mapping` fails closed on invalid correlation, enums, nonnegative quantities, timestamps, and missing provenance. The CLI converts model errors to exit 2.
2. Derive `tool_events.jsonl` from the enabled telemetry directory; do not add configuration fields. Reuse the existing JSONL segment enumeration, no-replace rollover, retention, canonical digest, and replay-scan primitives so event persistence does not fork concurrency behavior.
3. Event journal writes are observational and fail-open on I/O after payload validation. Disabled telemetry returns before reading or validating input, matching `telemetry record`.
4. `telemetry event --context-ref ...` merges only frozen correlation and sizing from the begin context, then validates. It never re-reads backlogit.
5. `telemetry record --compose-tool-events` selects exact epoch-ID matches. Backlog-item fallback is allowed only when events lack epoch IDs and exactly match the context task. Mismatches are ignored with diagnostics, never attached to another epoch.
6. Composer-owned fields cannot be supplied as precomposed nonzero values in the same close payload. Hybrid input fails closed to prevent double counting; gate exits, cost, and total task duration remain close-payload owned.
7. An event with `expected_tool` records one explicit expected opportunity. It is observed only by a correlated invocation of that tool for the same logical operation. Missing is clamped at zero. Status-only expectation records use operation `expect` and status `skipped` and do not masquerade as tool invocations.
8. Apply the 095-S additive provenance rule: values remain numeric; sparse source/quality maps carry trust; malformed labels normalize fail-closed to `unavailable`; optional exported dataclass fields are appended with defaults.

## Implementation Units

### U1 — ToolTelemetryEvent runtime model and schema parity

* Add `src/autoharness/telemetry/tool_event.py` with an immutable event model, controlled error type, strict from-mapping validation, canonical UUID/timestamp handling, provenance completeness checks, and stable serialization.
* Add focused model tests in `tests/test_telemetry_tool_event.py`, including all required fields, correlation any-of, nullable server name, extension enums, negative quantities, malformed provenance, and round-trip parity against the existing schema.
* Execution posture: test-first. Effort: at most 2h. Files: 2. Depends on: none.

### U2 — Shared segmented JSONL primitives

* Extract only the generic segment enumeration, no-replace rollover, retention, canonical-line scan, and file-identity logic from `jsonl_sink.py` into one internal helper while preserving execution-epoch behavior byte-for-byte.
* Extend existing JSONL sink tests to pin no regression in rotation, late append reconciliation, retention, and first-write precedence.
* Execution posture: characterization-first. Effort: at most 2h. Files: 3 or fewer. Depends on: none.

### U3 — Bounded ToolTelemetryEvent journal

* Add an event journal module using U1 and U2. Derive the journal beside the configured epoch DB, append canonical event records, deduplicate across retained segments by event ID, reject conflicting replays, and stream exact-correlation reads.
* Add tests for disabled mode, workspace containment, bounded rotation/retention, non-ASCII digest stability, identical replay, conflict, malformed lines, and cross-segment reads.
* Execution posture: test-first. Effort: at most 2h. Files: 2. Depends on: U1, U2.

### U4 — Deterministic event-to-epoch composer

* Add a pure composer that accepts deduplicated events plus a frozen context and returns composer-owned route, economics, operations, and outcome patches.
* Sum deltas; use final/max cumulative totals; preserve metric provenance; aggregate first-seen stable route/tool sets; derive scalar/map expected-tool invariants; count failed and degraded invocations separately; never treat degraded/stale as a missing invocation.
* Add order-independence, retry, cumulative-not-summed, provenance, explicit-expectation, over-observation, zero/unavailable, and correlation tests.
* Execution posture: test-first. Effort: at most 2h. Files: 2. Depends on: U1.

### U5 — Epoch record composition integration

* Extend the record path to load the default journal only when composition is explicitly requested, select context-correlated events, reject hybrid precomposed composer-owned fields, merge the pure patch, and preserve frozen sizing and unrelated close-owned values.
* Return selected/deduplicated/ignored event counts and composition diagnostics in the record summary. Preserve first-write immutable epoch replay semantics.
* Extend record API tests for no-events, cross-epoch events, context mismatch, hybrid refusal, deterministic retry, sink failure, and existing non-composed compatibility.
* Execution posture: test-first. Effort: at most 2h. Files: 3 or fewer. Depends on: U3, U4.

### U6 — CLI event emission and composition surface

* Extend `autoharness telemetry` with `event --context-ref ... --from-json ... --json` and `record --compose-tool-events`.
* Preserve help, stdin/file parity, disabled no-op-before-parse behavior, controlled invalid-payload exit 2, fail-open sink warnings, and structured JSON summaries.
* Add CLI tests for direct callers and context-bound agent usage.
* Execution posture: test-first. Effort: at most 2h. Files: 2. Depends on: U3, U5.

### U7 — Ship lifecycle template and dogfood parity

* Update `templates/agents/_ship.agent.md.tmpl` and `.github/agents/_ship.agent.md` to carry the begin context into optional sanitized tool-event calls and use close-time composition only when event emission succeeded.
* Keep telemetry observational: event or composition failures are reported but never block task completion; no event means the existing close payload path remains valid.
* Refresh only required manifest checksum metadata and validate three profile resolutions during Ship execution.
* Execution posture: template-first. Effort: at most 2h. Depends on: U6.

### U8 — Telemetry reference and contract verification

* Update `docs/telemetry-reference.md` with event lifecycle, journal retention, composer ownership, expectation semantics, provenance, privacy, rollback, and CLI examples.
* Update telemetry documentation/schema contract tests without changing the published event schema.
* Execution posture: docs-first. Effort: at most 2h. Files: 2. Depends on: U4, U6.

## Dependency Graph

```text
U1 ─┬─> U3 ─> U5 ─> U6 ─┬─> U7
    └─> U4 ────────> U6 └─> U8
U2 ───> U3
```

U1 and U2 may be implemented sequentially in the same shipment but not in parallel worktrees. U3 follows both. U4 follows U1. U5 follows U3/U4, then U6, then U7/U8 in dependency order.

## Risks and Caveats

* Double counting: fail closed on hybrid event-composed and precomposed roll-up fields.
* Mis-correlation: exact context epoch ID first; backlog item fallback is narrow and diagnostic; never attach disagreement.
* False precision: absent metrics stay unavailable and populated metrics require provenance.
* Secret leakage: schema fields only, safe fingerprints and paths, no raw output; ambiguous sensitivity receives internal handling.
* Journal growth/concurrency: share bounded segmented primitives and first-write precedence; do not invent a second implementation.
* Host parity: generic CLI is authoritative; pack-specific adapters remain deferred.
* Existing telemetry compatibility: composition is opt-in and disabled mode remains a no-op.

## Plan Hardening Signals

* Public API, schema, or contract change: present. New public CLI runtime behavior implements an existing published schema.
* Security, auth, permission, or compliance-sensitive behavior: present. Local telemetry evidence can expose sensitive metadata if not constrained.
* Migration, backfill, destructive action, or irreversible step: absent. No backfill; event journal is additive and bounded.
* External integration, operator checkpoint, or dependency: present. Ship agent lifecycle consumes the CLI; broad pack adapters remain excluded.
* High runtime, rollout, or rollback risk: present. Correlation or double-counting errors would corrupt evaluation evidence.

Requires plan hardening: yes

## Runtime Verification and Closure

* U1-U4: focused model, journal, and composer tests prove contract and deterministic behavior.
* U5-U6: CLI smoke scenarios prove disabled no-op, valid context-bound emission, composed close, replay, conflict, and malformed input handling.
* U7: resolve Ship template for Rust, Go, and Python profiles; assert no unresolved variables and mirror parity.
* U8: schema/doc parity and cross-reference checks.
* Full Ship verification: targeted telemetry tests, full repository unit suite, CLI help smoke, template verification, and no unresolved placeholders. Stage does not run these gates.
* Rollback trigger: any cross-epoch attachment, double counting, secret-bearing persistence, unbounded growth, or disabled-mode regression. Rollback removes event/composition invocation while retaining existing ExecutionEpoch recording.
* Closure owner: Ship. Validation window: one shipment execution plus replay of the same event and close payload before merge readiness.


## Plan Hardening

Hardening required: yes. The plan introduces a public CLI surface, writes local telemetry evidence, and composes records that drive evaluation claims. Incorrect correlation, false precision, secret persistence, or double counting is a high-impact evidence-integrity failure even though telemetry remains observational.

### Reinforcing Context

* `docs/compound/095-S-derived-metric-provenance-additive-map.md`: keep numeric values numeric, carry trust in additive sibling maps, normalize malformed labels fail-closed, and append optional exported dataclass fields with defaults.
* `docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md`: preserve exact ToolTelemetryEvent correlation, provenance, nonnegative quantity, expectation-gap, cumulative-total, and ownership rules.
* `docs/telemetry-reference.md`: preserve disabled mode, frozen pre-execution sizing, first-write immutable epoch replay, and the autoharness/agent-engram boundary.
* Existing `jsonl_sink.py`: reuse its no-replace segmented rotation and retention semantics rather than creating weaker parallel file handling.

### Protected Invariants

1. Events and epochs are never correlated across task or epoch boundaries. A context disagreement is diagnostic-only and cannot be overridden.
2. Delta metrics are summed once; cumulative totals are never summed; event IDs are deduplicated before composition.
3. Composer-owned roll-ups and precomposed values are mutually exclusive in one close request.
4. Every populated metric has source and quality provenance. Unknown or malformed provenance degrades to unavailable rather than observed.
5. No raw tool output, prompt, stderr, credential, token, or secret is persisted. Evidence references are repo-local identifiers or sanitized paths only.
6. Disabled telemetry performs no payload read, no validation, and no filesystem write. Enabled sink failures remain fail-open and visible.
7. WorkSizingSnapshot comes only from the frozen begin context. Event emission and close composition never re-read backlogit.
8. Existing non-composed ExecutionEpoch recording and sink bytes remain backward-compatible.

### Risk-Classified Actions

ProposedAction: Extract shared segmented JSONL helpers and migrate the existing epoch mirror to them without semantic change.
ActionRisk: medium — a refactor could regress concurrent rollover or replay scans. Characterization tests must pass before the event journal consumes the helper; no config/schema change is allowed.
ActionResult: pending Ship execution.

ProposedAction: Persist validated ToolTelemetryEvent records in the bounded workspace-local journal.
ActionRisk: high — local evidence can leak sensitive metadata or grow without bound. Accept schema fields only, reject unknown keys, enforce workspace containment, retain bounded segments, and default ambiguous sensitivity to internal handling.
ActionResult: pending Ship execution.

ProposedAction: Compose journal events into the task-close ExecutionEpoch.
ActionRisk: high — mis-correlation or duplicate arithmetic can corrupt evaluation evidence. Require exact context correlation, event-ID dedupe, deterministic order-independent output, hybrid-input refusal, explicit expectation accounting, and replay equality tests.
ActionResult: pending Ship execution.

ProposedAction: Add Ship lifecycle calls to the template and dogfood agent.
ActionRisk: medium — instrumentation could become a completion gate or diverge across generated and installed copies. Keep calls optional and fail-open, preserve the old close path when no events exist, update both mirrors together, and validate three resolved profiles.
ActionResult: pending Ship execution.

### Verification Matrix

* Contract: runtime serialized fields equal the published schema; unknown properties and invalid enums/correlation fail closed.
* Arithmetic: shuffled event order and repeated identical event IDs produce identical roll-ups; cumulative totals use final/max semantics.
* Correlation: wrong epoch/task/feature/shipment events are ignored with diagnostics; no fallback can cross the loaded context.
* Provenance: null/unavailable/estimated/derived values retain correct numeric and sibling-map behavior; malformed labels never crash.
* Privacy: secret-like unknown fields are rejected; evidence paths cannot escape the workspace; raw content fields do not exist.
* Concurrency/retention: event journal rotation, no-replace claims, late appends, retained-segment scans, and oldest-first pruning match epoch JSONL behavior.
* Compatibility: telemetry disabled, event-free close, legacy epoch read, and existing record replay remain unchanged.
* Agent parity: template and dogfood Ship use the same public commands documented for direct callers.

### Rollback and Monitoring

* Rollback is invocation-first: remove or disable Ship event calls and omit `--compose-tool-events`; existing epoch recording continues unchanged.
* Code rollback can then remove the event CLI/model/journal/composer without migrating existing epoch data. Retained event JSONL is observational and may age out under bounded retention.
* Monitor structured summaries for ignored-correlation events, replay conflicts, missing provenance, hybrid-input refusals, journal I/O warnings, and selected-event count zero when emission was expected.
* Any cross-epoch attachment, raw-content persistence, unbounded journal growth, or disabled-mode write blocks release readiness.
* Closure owner is Ship; one real shipment task plus identical replay is the minimum validation window.

### Review-Gate Capability Risk

Reviewer subagent and model-specific dispatch are unavailable in this session. Plan review must declare `dispatch_mode: single-agent-declared-degradation`, apply every required persona inline, and emit a literal `decision:` marker. Missing persona coverage or markers fails harvest closed.

Unresolved operator decisions: none. The Option B product direction and telemetry ownership are already ratified. Any request to add broad pack adapters, benchmark claims, new schema fields, or a second graph authority requires a separate Stage decision and is out of scope.


## Plan Review Cycle 1

dispatch_mode: single-agent-declared-degradation
decision: FAIL

The inline persona pass found no P0 findings and three P1 ambiguities that required correction before harvest:

* P1 — Architecture/Security: bounded event retention and unlimited first-write immutability were stated together without naming the authoritative post-retention record.
* P1 — Python/Architecture: expected-tool matching referred to a logical operation but did not define the machine correlation key between an expectation and a later invocation/retry.
* P1 — Learnings/Python: strict event-schema rejection and fail-closed normalization of malformed provenance were both required without assigning them to distinct trust boundaries.

Gate result: FAIL pending the clarifications below. No backlog harvest is allowed from this cycle.

## Review Fixes

1. Event replay/conflict detection is first-write immutable within the retained journal horizon. Composition must occur before task close, while task events are retained. After close, the first-write immutable ExecutionEpoch in SQLite is authoritative; a later close replay cannot replace it even if old events have aged out. The journal makes no unlimited-retention claim.
2. Expected-tool accounting uses explicit event links. A direct invocation event with `expected_tool == tool_name` counts one expected and one observed opportunity. A separate expectation event is identified by its `event_id`; a later invocation or retry satisfies it only when `parent_event_id` equals that expectation event ID and `tool_name` equals the expectation `expected_tool`. Multiple retries under one expectation count one expected opportunity and at most one observed opportunity. Unlinked events never satisfy an expectation.
3. Strict ToolTelemetryEvent ingestion rejects out-of-vocabulary or structurally malformed provenance. The defensive journal reader skips any malformed legacy/untrusted line with a diagnostic; it does not coerce it into a valid event. The 095-S unavailable normalization rule applies when aggregating a valid event whose metric is explicitly unavailable, not as a bypass of the published schema enum.
4. Cumulative token totals use the maximum populated value per correlated stream to keep composition order-independent. Timestamp order is used only to diagnose a later lower value as a non-monotonic emitter warning; cumulative values are never summed.
5. R5 replay wording is bounded accordingly: identical replays are idempotent and conflicting same-ID content is rejected within retained event segments; the composed epoch remains immutable without a retention qualifier.


## Plan Review

dispatch_mode: single-agent-declared-degradation
decision: PASS

Gate decision: PASS. Review cycle 2 confirms that the three cycle-1 P1 findings are resolved. The plan is hardened, width-isolated, dependency-ordered, and ready for harvest. Reviewer subagent and anchor-model dispatch were unavailable, but every selected persona rubric ran inline; no persona was skipped.

Plan hardening required: yes. Requirement satisfied by the risk-classified actions, protected invariants, verification matrix, rollback triggers, monitoring signals, and declared degraded-review protocol in `## Plan Hardening`.

### Persona Coverage

| Persona | Mode | Result |
| --- | --- | --- |
| Constitution Reviewer | inline rubric | PASS — test-first posture, workspace containment, fail-open observability, no new dependency, and P-016 sequential execution are explicit. |
| Python Reviewer | inline rubric | PASS — immutable typed models, controlled errors, numeric/provenance semantics, deterministic composition, and focused tests are specified. |
| Scope Boundary Auditor | inline rubric | PASS — 082-F adapters, 085-F benchmarks, schema redesign, raw output, and second graph authority are explicitly excluded. |
| Learnings Researcher | inline rubric | PASS — 095-S additive provenance and dataclass compatibility are directly applied; no known solution is contradicted. |
| Architecture Strategist | inline same-model fallback | PASS — journal authority horizon, exact correlation, pure composer boundary, and dependency chain are coherent. |
| Agent-Native Parity Reviewer | inline same-model fallback | PASS — Ship and direct callers use the same CLI surface and structured summaries. |
| Security Lens Reviewer | inline same-model fallback | PASS — schema-only data, no raw output, workspace containment, bounded retention, internal handling, and fail-closed correlation are explicit. |

### Findings by Severity

* P0: none.
* P1: none remaining. Three cycle-1 P1 findings are resolved in `## Review Fixes`.
* P2: none.
* P3: none.

### Runtime Verification and Operational Closure

Runtime verification is complete at plan level: model/schema parity, event journal replay/rotation, deterministic composition, disabled/invalid/sink-failure CLI paths, context correlation, template resolution across three profiles, and full telemetry regression gates are assigned to specific units. Operational closure names Ship as owner, defines one real task plus identical replay as the validation window, and provides invocation-first rollback and hard release blockers.

Harvest authorization: PASS. The latest review carries the required literal markers and covers every selected persona under declared degradation.

