---
title: "Stage session memory — 085-F structural-navigation-benchmark-suite"
type: session-memory
date: 2026-08-02
agent: stage
route: claude-opus-4.8 / anthropic / high
feature: 085-F
shipment: 111-S
---

## Outcome

Executed full Stage `stage next` lifecycle for feature `085-F`. Produced a **reviewed,
queued, task-only shipment `111-S`** (8 tasks). Ship NOT invoked; no claim, no
implementation, no branch/PR, no commit/push.

## Artifacts (untracked, not committed)

- Spike: `docs/spikes/2026-08-02-structural-navigation-benchmark-feasibility.md`
- Deliberation: `docs/decisions/2026-08-02-structural-navigation-benchmark-design-deliberation.md`
- Plan (+hardening): `docs/archive/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md`
- Review: `docs/reviews/2026-08-02-structural-navigation-benchmark-suite-review.md`
- This memory file.

## Decision

Direction **C — Hybrid, deterministic-core-first**. Reproducible deterministic replay core is
the shippable unit; live-run mode is an additive opt-in emitting the same ExecutionEpoch v1.1
records. Benchmark consumes the shipped telemetry reader/report/aggregation APIs read-only; zero
telemetry-contract / schema / CLI-distribution change; additive layer over `src/autoharness/eval`.

## Backlog (all queued)

`085-F` → 001 corpus/loader → {002 harness, 003 scorer} → {004 metrics-adapter, 005 env-controls}
→ 006 honest-renderer → {007 tests, 008 docs}. **11 `blocks` edges** (006 depends on 003, 004 **and
005** — see cycle-2 review-fix). Families: code (001–006),
test (007), docs (008); width-isolated; ≤2h each.

## Review

plan-review PASS after **1 fix cycle**. P1-1 (benchmark epochs could pollute the authoritative
telemetry store) fixed in-plan via mandatory isolated benchmark `TelemetryConfig` sink +
reserved `benchmark:` namespace (002 acceptance; 005 records sink path). P2-1/P2-2 folded into
001/007/008 acceptance. Hardening present (result-integrity + multi-family blast radius; H1–H7).

### Cycle 2 — external review-fix (PR #288 Copilot threads)

Bounded Stage review-fix pass over 5 Copilot threads on PR #288 (`chore/stage-111-S`). All five
valid; corrected in Stage-owned artifacts only (plan / task acceptance / DAG). Verdict remains
**PASS after 2 fix cycles** (within the 3-cycle limit). No source/template/schema/shipment-manifest
change; manifest still task-only 8 items; DAG acyclic.
- Live-run "delivery" claim deferred → out-of-scope (Summary + Out-of-scope; no new task).
- 085.002-T epoch cardinality clarified: 2×N epochs (one per arm per repeat), no overwrite.
- 085.004-T delta-provenance rule: least-certain across operands; `unavailable`/`not_applicable`
  propagates; no false-precision `observed`.
- 085.006-T now depends on 085.005-T (added blocks edge; degraded-run producer contract).
- 085.005-T family reclassified `code/config` → `code` (width-isolation consistency).

## Degraded mode

backlogit MCP unavailable → CLI fallback throughout (`INDEX_SYNC_OK` via `backlogit sync`).
engram/intercom/graphtor tool surfaces unavailable → file-based fallback; no broadcasts.
`append_comment` has no CLI fallback → feature traceability captured in artifacts instead.

## Ship handoff

Handoff token: **shipment `111-S`** (queued). Ship claims 111-S, executes tasks in
dependency order 001→008 across separate code/test/docs families, then closes per the 097-S
task-only safe-close path (covering feature `085-F` closed separately, not via manifest cascade).

## Explicitly excluded (untouched)

Pre-existing dirty `.backlogit/stash.jsonl` (unrelated mod); blocked features 077/080/081/082-F;
both stash entries; previously shipped telemetry artifacts (read-only evidence only).
