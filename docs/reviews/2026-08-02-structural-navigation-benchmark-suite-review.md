---
title: "plan-review — Structural-Navigation Benchmark Suite (085-F)"
type: plan-review
date: 2026-08-02
route: claude-opus-4.8 / anthropic / high (P-013.5, inherited)
plan: docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md
spike: docs/spikes/2026-08-02-structural-navigation-benchmark-feasibility.md
deliberation: docs/decisions/2026-08-02-structural-navigation-benchmark-design-deliberation.md
feature: 085-F
verdict: PASS
p0_count: 0
p1_count: 1
p2_count: 2
review_fix_cycles: 1
requires_plan_hardening: yes
hardening_present: yes
---

## Verdict: PASS (after 1 fix cycle)

The plan is bounded, grounded in the shipped telemetry read/report/aggregation seams and the
existing `src/autoharness/eval` A/B harness, and consumes the ExecutionEpoch v1.1 /
ToolTelemetryEvent v1.0 contract **read-only**. Plan hardening is present and commensurate with
the elevated (result-integrity + multi-family) blast radius. One P1 was found and corrected in
scope; two P2 advisories are folded into acceptance. Ready for harvest.

## Findings

### P0 — Blocking (0)
None.

### P1 — Must-fix before harvest (1, RESOLVED in cycle 1)
- **P1-1 (valid, FIXED) — Benchmark epochs could pollute the authoritative telemetry store.**
  As originally written, 085.002-T emitted ExecutionEpochs through `telemetry begin`/`record`
  without specifying an isolated sink, so benchmark runs would write into the repository's
  authoritative `.autoharness/metrics` SQLite store and JSONL mirror — contaminating real
  aggregates and, via first-write-immutable replay, permanently. **Fix applied:** 085.002-T now
  requires an isolated benchmark `TelemetryConfig`/sink directory and a reserved `benchmark:`
  namespace for synthetic `backlog_item_id`/`workspace_id`; its acceptance now asserts the
  authoritative store is provably untouched. 085.006-T records the isolated sink path in the run
  manifest. Verified against `reader.read_epoch_records` (config-driven sink paths) and the
  first-write-immutable replay semantics in `docs/telemetry-reference.md`.

### P2 — Advisory (2, non-blocking; folded into acceptance)
- **P2-1 Corpus-class rationale must be machine-checkable, not just prose.** Fold into 085.001-T:
  the balanced-class invariant (>=1 positive/neutral/negative) is test-enforced in 085.007-T, and
  each scenario stores a short `rationale` field so the "not cherry-picked" claim is auditable.
- **P2-2 Live-run mode must be off-by-default and clearly labeled.** Fold into 085.008-T doc
  acceptance: state plainly that the deterministic core is the reproducible unit and live mode is
  an additive opt-in whose host token/cost is frequently `unavailable`, so operators are not
  misled into treating live numbers as observed ground truth.

## Scope / Policy checks
- **Width isolation** — code (001–006) / test (007) / docs (008); no task crosses a family; no
  benchmark-code task mixes in schema or CLI-distribution work. ✔
- **2h rule** — each task is a single concern (loader / harness / scorer / adapter / renderer /
  controls / tests / docs); none exceeds the ceiling. ✔
- **P-003 speculative-task risk — CLEARED.** Every task has a concrete, independently verifiable
  acceptance criterion (invariant rejects, deterministic hash, provenance `unavailable`≠0,
  no-win-on-regression, degraded capture). No speculative scaffolding.
- **Telemetry-contract boundary — CLEARED.** Consumed read-only; no schema/sink/reader/report math
  change; net-additive `eval/benchmark` layer with a clean rollback. ✔
- **P-006 hardening — present and required** (result-integrity + multi-family). H1–H7 failure
  modes each map to an owning task and a verifying test. ✔
- **Honest-reporting invariants** — `unavailable` vs observed-zero, `metric_quality`/
  `derived_quality` surfacing, aggregate-total denominators, correctness-over-efficiency
  precedence — all pinned in 004/005 and test-enforced in 007. ✔
- **Stage role boundary respected** — planning/backlog only; no source/template/config mutation,
  no build/test run, no branch/PR, no commit/push performed by staging. ✔

## Disposition
PASS — proceed to harvest. 1 review-fix cycle (within the 3-cycle limit); P1-1 corrected in the
plan; P2-1/P2-2 folded into 001/007/008 acceptance. No re-plan required.
