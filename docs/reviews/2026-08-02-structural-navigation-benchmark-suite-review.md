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
p1_count: 5
p2_count: 3
review_fix_cycles: 2
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

## Cycle 2 — external review-fix (PR #288 Copilot threads; within 3-cycle limit)

Five Copilot-authored review threads on PR #288 were triaged during a bounded Stage review-fix
pass. All five are **valid** and were corrected in Stage-owned artifacts (plan / task acceptance /
DAG); no source, template, schema, or shipment-manifest change was required. Verdict remains
**PASS**; feature intent, deterministic-replay methodology, correctness non-tradeability, isolated
telemetry sink, honest unavailable-vs-zero reporting, 2h granularity, task-only manifest, and the
dependency DAG are preserved.

- **C2-P1-1 (valid, FIXED) — Live-run "delivery" claim with no implementing/verifying task.**
  Thread `PRRT_kwDORzpWpM6V39xV`. The Summary read as if live-run mode were delivered here, but no
  task implements a callable live path (direction C is deterministic-core-first). Per the
  reviewer's own alternative, the mode is **deferred, not implemented**: Summary reworded to state
  live mode is out of scope for this shipment, and an explicit "Out of scope" bullet now owns the
  deferral. 008 continues to document it as an off-by-default opt-in. No new task added (avoids
  scope creep / preserves task-only 8-item manifest).
- **C2-P1-2 (valid, FIXED) — Epoch cardinality vs N-repeats contradiction (085.002-T).**
  Thread `PRRT_kwDORzpWpM6V39xx`. "Exactly two epochs" conflicted with N-repeat dispersion.
  Acceptance now specifies **exactly two correlated epochs per repeat (2×N total)** with unique
  per-repeat epoch identity and no overwrite/pre-persistence collapse; task body aligned.
- **C2-P1-3 (valid, FIXED) — Delta-provenance "carried unchanged" enabled false precision (085.004-T).**
  Thread `PRRT_kwDORzpWpM6V39yJ`. A delta combines operands with possibly different quality labels,
  so "unchanged" is undefined. Plan + task now specify a **deterministic delta-provenance rule**:
  least-certain quality across all operands; `unavailable`/`not_applicable` propagates to the delta;
  a mixed observed/estimated comparison is labeled `estimated`, never `observed`.
- **C2-P1-4 (valid, FIXED) — Missing 085.005-T dependency on the renderer (085.006-T).**
  Thread `PRRT_kwDORzpWpM6V39ye`. The renderer must retain/display degraded runs, but degraded-run
  capture/classification is owned by 085.005-T. Added the `085.005-T → 085.006-T` blocks edge
  (task frontmatter + backlogit DAG + plan dep line/heading); no cycle introduced.
- **C2-P2-1 (valid, FIXED) — Width-isolation family inconsistency (085.005-T).**
  Thread `PRRT_kwDORzpWpM6V39yR`. Plan heading/ledger labeled 005 `code/config`, contradicting the
  single-family claim and the task's `family:code` label. Reclassified consistently to `code`
  (task is code-level controls + a run manifest, not a committed config change).

Verdict: **PASS (after 2 fix cycles)**. All five threads resolved in-plan/in-backlog; no re-plan,
no scope expansion, manifest still task-only (8 items), DAG acyclic.
