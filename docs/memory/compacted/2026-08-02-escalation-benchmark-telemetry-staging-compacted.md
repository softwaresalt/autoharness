---
title: Compacted memory — Auto-escalation (011DL-b/106-F/110-S), benchmark suite (085-F/111-S), size/complexity telemetry staging (112-S/113-S)
doc_type: memory
memory_class: compacted
created: 2026-08-02
scope: stage-session-batch
shipment: [110-S, 111-S, 112-S, 113-S]
feature: [106-F, 085-F, "107-F", "108-F"]
consolidates:
  - docs/archive/memory/2026-08-02-stage-011DL-b-auto-escalation.md
  - docs/archive/memory/2026-08-02-stage-085-F-benchmark-suite.md
  - docs/archive/memory/2026-08-03-stage-size-complexity-telemetry-staging.md
---

# Compacted: Stage sessions 2026-08-02 → 2026-08-03

## Session 1 — Telemetry-driven auto-escalation (deliberation 011-DL part b, 106-F / 110-S)

Resolved the operator's follow-on question from `104-F` (routing enforcement): should
consecutive-failure escalation also be config/telemetry driven? Deliberation `011-DL`
(addendum "part b") evaluated 3 options; chose **hybrid** — extend the existing
`model_routing.escalation` route with a nested per-role override
(`model_routing.<role>.escalation`) resolved with clear precedence: nested role override →
legacy flat `escalation` (deprecated) → `tier3` fallback per-field.

**Decision — `ESCALATION_DEGRADED` invariant**: an escalation is degraded (must NOT proceed
as a "real" escalation) when the resolved escalation route equals the acting agent's own
already-resolved role route tuple `(model_family, model_provider, reasoning_effort)`. This
generalizes the same-route guard from `104-F`'s role-routing work to the escalation path
specifically, and became the canonical definition later referenced by both `_stage` and
`_ship` templates via `escalation-protocol.instructions.md` (single source of truth, no
per-agent redefinition).

**Fail-closed ambiguity rule**: if both the legacy flat `escalation` route and a new nested
`<role>.escalation` route are non-empty simultaneously, resolution must fail closed
(ambiguous) rather than silently pick a winner — enforced at schema level where expressible,
backstopped by loader/verification logic.

**Harvest**: feature `106-F` + 6 dependency-ordered S-sized tasks `106.001-T`…`106.006-T`
(schema nested-override field + validation → resolution precedence logic → fail-closed
ambiguity check → escalation-payload contract doc → wiring into `_stage`/`_ship` stop-condition
tables → cross-reference update in `workflow-policies.md` P-013.5/P-013.6). Shipment `110-S`
created queued, task-only, **not** dependency-gated behind `108-S` (different subsystem,
independently shippable) but logically sequenced after it in the backlog narrative since both
touch model-routing config.

## Session 2 — Evaluation/benchmark suite (085-F / 111-S)

Unblocked now that `084-F` (token-efficiency telemetry emission, session 2026-07-31) is
staged/shipped-in-progress. Deliberation-free (straightforward extension of existing
`get_evaluation_report`/`get_token_savings_report` observability surface per Primitive 7).

**Key decision — isolated telemetry sink**: benchmark/eval runs MUST write to a namespaced,
isolated telemetry sink (a distinct file/table keyed by `benchmark_run_id`), never commingle
with the authoritative production telemetry store — synthetic benchmark traffic must not
pollute real observability metrics or trigger real alerting/escalation thresholds. This is a
**hard architectural constraint**, not a style preference, and was the single most load-bearing
decision in this session.

**Harvest**: feature `085-F` + 5 S-sized tasks `085.001-T`…`085.005-T` (benchmark harness
scaffold → isolated sink writer → synthetic workload generator → comparison/report tool →
docs). Shipment `111-S` created queued, task-only.

**Failed approach (considered and rejected)**: reusing the production telemetry writer with a
`is_benchmark: true` flag column was considered and rejected — flag-based commingling was
judged too easy to accidentally leak into real aggregate reports (a downstream query
forgetting the `WHERE is_benchmark = false` filter would silently corrupt production metrics).
Physical sink isolation (separate file/table) was chosen instead specifically to make that
class of mistake structurally impossible rather than merely convention-guarded.

## Session 3 — Size vs. complexity telemetry staging (107-F/108-F, 112-S/113-S)

Follow-on operator request: telemetry should track task **size** and **complexity** as
independent signals (previously conflated as a single "difficulty" concept in ad hoc
discussion, though never actually implemented that way in code).

**Decision — non-conflation invariant**: size (volume/effort — file count, LOC, test-scenario
count; roughly the existing 2-Hour-Rule inputs) and complexity (difficulty/uncertainty —
architectural novelty, cross-cutting blast radius, ambiguity of requirements) are **two
independent axes**, not one scale. Telemetry schema must capture both as separate fields; no
derived "difficulty score" collapsing them into one number, because doing so would destroy the
ability to distinguish "big but simple" from "small but hard" tasks — a distinction the
operator explicitly wanted preserved for future model-routing tuning.

**Harvest split across two features** (large size, split for width-isolation): `107-F` (size
telemetry: instrumentation of file/LOC/test-scenario counters at task-completion time) and
`108-F` (complexity telemetry: structured complexity-signal capture, initially a small
enumerated set of qualitative tags rather than a numeric score, deferring scoring-model design
as a future follow-up). Shipments `112-S` (107-F tasks) and `113-S` (108-F tasks) both created
queued, task-only, `113-S depends_on 112-S` (shared schema migration must land first).

**Deferred / explicitly out of scope this session**: a numeric complexity-scoring model
(operator wants qualitative tags first, to gather real-world distribution data before
committing to a scoring function) — flagged as a natural follow-on feature once `108-F` data
exists.

## Cross-cutting learnings (this batch)

1. `ESCALATION_DEGRADED` and the role-routing same-route guard are the **same shape of
   invariant** applied at two different points (agent invocation vs. failure escalation) —
   both exist to prevent a "fake" routing change that resolves to the agent's own current
   model, which would otherwise silently defeat the purpose of routing/escalation.
2. Isolated-sink design for auxiliary telemetry (benchmarks, synthetic workloads) is a
   recurring pattern worth generalizing: any non-production telemetry producer should write to
   a namespaced sink, never a flag-gated column in the production store.
3. Size and complexity must remain **structurally separate telemetry fields**, never merged
   into a single scalar — this directly informed later work (`docs/compound` notes on the
   "non-conflation invariant") and should be treated as an architectural constraint for any
   future model-routing or task-triage tooling that consumes this telemetry.

## Outcome

All three sessions completed staging only (deliberation/plan/harvest); no implementation, no
git operations, no shipment claims. `110-S`, `111-S`, `112-S`, `113-S` all left `queued`
(`113-S` gated behind `112-S`) for Ship to pick up in a future session.
