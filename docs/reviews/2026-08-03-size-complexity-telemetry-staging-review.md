---
title: "plan-review — Size + Complexity first-class staging & backlogit telemetry evidence mapping"
type: plan-review
date: 2026-08-03
revised: 2026-08-03 (re-review after Copilot PR #291 findings 3708167171 / 3708167225 / 3708167265 / 3708167293)
route: claude-opus-4.8 / anthropic / high (P-013.5, inherited)
plan: docs/archive/plans/2026-08-03-size-complexity-telemetry-staging-plan.md
deliberation: docs/decisions/2026-08-03-size-complexity-telemetry-staging-deliberation.md
scope_reviewed: 9 published tasks — S1/112-S {107.001-T,107.002-T,107.003-T,107.004-T,107.005-T}; S2/113-S {108.001-T,108.002-T,108.003-T,108.004-T}
verdict: PASS
---

## Verdict: PASS (re-review)

This re-review covers **every task actually published** to shipments 112-S and 113-S — 9 tasks,
not the original 7 — after correcting the four blocking findings from Copilot's review of PR #291.
The plan is dependency-correct, width-isolated, non-conflating, each task is single-family and
≤ 2h, and plan hardening now reflects the true blast radius of the schema change (live runtime
model + schema-mirror parity + version registration). Proceed to harvest/hand-off.

## Copilot PR #291 findings — resolution (all four addressed)

- **F-1 (3708167171, 108.002-T):** The schema is NOT an inert forward contract — a live strict
  runtime model (`src/autoharness/telemetry/tool_event.py`, `additionalProperties:false`),
  composer, jsonl serialization, a byte-identical root mirror guarded by a parity test, and a
  `schema_contracts` version registration all depend on it. **Resolved:** 108.002-T now scopes BOTH
  schema mirrors + registration + schema-contract tests (schema family); the runtime model +
  composer + jsonl serialization + runtime tests are split into new **108.004-T** (python-runtime
  family, dep 108.002-T), added to feature 108-F and shipment 113-S. Width preserved; neither task
  exceeds 2h.
- **F-2 (3708167225, review doc):** The prior PASS reviewed 7 tasks but 112-S published
  107.005-T (native `complexity` header-def enablement) too. **Resolved:** 107.005-T is now
  documented in the plan (F1.T5) with dependency/width/risk analysis, and this re-review covers all
  9 published tasks.
- **F-3 (3708167265, 107.004-T):** A behavioral Stage change must also update the installed dogfood
  `.github/agents/_stage.agent.md` and refresh the `.autoharness/harness-manifest.yaml` checksum.
  **Resolved:** 107.004-T scope + acceptance now require the template edit, the identical installed-copy
  edit, and the manifest checksum refresh (procedure per 110-S/106.004-T). Kept as one coherent
  agent-template task (checksum refresh is a deterministic consequence, not a separate family).
- **F-4 (3708167293, 108.001-T):** Session/tool aggregates are not per-operation event fields, and
  `compaction_count` is not a ToolTelemetryEvent field at all. **Resolved:** 108.001-T now mandates an
  explicit event-vs-epoch granularity dimension; observed is restricted to genuine per-invocation
  evidence; aggregate-only values (session cumulative tokens, tool_usage roll-ups, compaction_count)
  are routed to ExecutionEpoch or marked unavailable at event granularity; observed/derived/
  unavailable/not_applicable are labelled distinctly.

## Findings

### P0 — Blocking (0)
None (the four PR #291 blockers above are resolved).

### P1 — Must-fix before harvest (0)
None.

### P2 — Advisory (3, non-blocking; folded into acceptance)
- P2-a (108.002-T/108.004-T): keep the complexity field structurally separate from
  `work_sizing_snapshot`; record the chosen shape + version decision in the PR description; keep the
  two schema mirrors byte-identical except `$id`.
- P2-b (108.001-T): every mapped target field carries BOTH `metric_sources` and `metric_quality`
  plus the new evidence-class + granularity labels; "observed" reserved for host_reported/
  backlogit-direct per-invocation fields only.
- P2-c (107.003-T): if no lightweight fixture harness exists in-repo, degrade to a reviewer
  checklist only (no new test runner).

## Scope / Policy Checks
- Non-conflation invariant (size=volume, complexity=difficulty/uncertainty) adopted verbatim from
  backlogit's released contract and enforced across 107.001-T/107.003-T/108.002-T — PASS.
- P-003 granularity: **9 tasks**, each single-family, ≤2h, with explicit deps and acceptance;
  the schema/runtime split (108.002-T vs 108.004-T) keeps schema-family and Python-runtime-family
  work in separate units — PASS.
- P-010 boundary: Stage authored only planning docs + backlog; all implementation (schema, runtime,
  templates, config) is delegated to Ship via tasks — PASS.
- Blast radius (108.002-T/108.004-T): elevated and now correctly characterised — additive-optional
  field across BOTH schema mirrors + registration + live runtime model/composer/jsonl, with matching
  parity/conformance/round-trip tests; additive rollback documented; no live emitter/store wiring
  (084-F owns emission) — PASS.
- Granularity fidelity (108.001-T): aggregate-only evidence is never mapped onto per-operation event
  fields; `compaction_count` explicitly recorded as not-an-event-field — PASS.
- Dogfood integrity (107.004-T): installed `.github/agents/_stage.agent.md` + manifest checksum
  refresh included, preventing manifest drift — PASS.
- Shipment integrity: 112-S {5 tasks} and 113-S {4 tasks} exclude their parent features (107-F/108-F);
  113-S blocked-on 112-S — PASS.
- Sensitivity: 108.003-T restricts the backlogit boundary to counts/durations/labels/hashes and
  documents redaction/secret-scan defaults; no raw-content exfiltration — PASS.

## Disposition
PASS — 9 published tasks reviewed; four PR #291 blockers resolved; three P2 advisories folded into
acceptance. Ordered shipment chain S1 (112-S) queued, S2 (113-S) blocked-on-S1. S2 is the
backlogit-only carve-out that unblocks the backlogit portion of 082-F; other packs stay
blocked-on-operator.
