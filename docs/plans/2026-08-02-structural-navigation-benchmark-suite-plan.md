---
title: "impl-plan — Structural-Navigation Benchmark Suite (085-F)"
type: impl-plan
date: 2026-08-02
route: claude-opus-4.8 / anthropic / high (P-013.5, inherited)
feature: 085-F
spike: docs/spikes/2026-08-02-structural-navigation-benchmark-feasibility.md
deliberation: docs/decisions/2026-08-02-structural-navigation-benchmark-design-deliberation.md
chosen_direction: "C — Hybrid, deterministic-core-first"
requires_plan_hardening: yes
hardening_present: yes
blast_radius: elevated (result-integrity + multi-family: eval code / tests / docs / fixtures)
---

## Summary

Build a reproducible structural-navigation benchmark suite as an **additive layer** over the
existing `src/autoharness/eval` A/B harness and the shipped telemetry read/report/aggregation
APIs (ExecutionEpoch v1.1 / ToolTelemetryEvent v1.0). Deliver the deterministic replay core
end to end. **Live-run mode is out of scope for this shipment** — it remains a deferred,
additive opt-in extension point that this shipment documents (008) but does not implement or
verify; no task here delivers a callable live path. **No telemetry-contract, schema, or
CLI-distribution change.** Every task is width-isolated to a single family and scoped ≤ 2h.

## Grounding (shipped seams this plan consumes read-only)

- `reader.read_epoch_records(config, source) -> TelemetryReadResult`
- `report.summarize_report(read_result, filters) / render_report(...)`
- `aggregation.aggregate_epochs / derived_efficiency_metrics` (denominators = aggregate totals)
- provenance: `metric_sources` / `metric_quality` (`observed|derived|estimated|not_applicable|unavailable`),
  sparse `derived_quality` (095-S); nullable = unavailable, zero-count = observed zero
- `src/autoharness/eval/{matrix,runner,summary,reviewer}.py` (existing paired-run seams)

## Task decomposition (width-isolated, ≤ 2h each)

### 085.001-T — Scenario corpus model + loader (family: code)
Add a scenario data model + loader under `src/autoharness/eval/` (e.g. `benchmark/scenarios.py`):
each scenario declares id, class (`positive|neutral|negative`), navigation task, gold answer
(target set), and index-state precondition (`warm|cold|stale`). Loader validates the corpus and
enforces the **balanced-class invariant** (>=1 positive, >=1 neutral, >=1 negative) and computes
a canonical corpus manifest hash. Ships an initial representative corpus fixture.
- **Acceptance:** loader rejects an unbalanced corpus; manifest hash is deterministic over sorted
  scenario ids; corpus fixture contains all three classes with documented rationale per case.

### 085.002-T — Baseline/treatment run harness (family: code)  — dep: 001
Deterministic executor that runs each scenario under two arms — baseline (routing OFF: raw
read/grep) and treatment (Engram-first ON) — and emits one ExecutionEpoch per arm through the
shipped `telemetry begin`/`telemetry record` path, correlated by synthetic `backlog_item_id`
and `phase` (`benchmark-baseline` / `benchmark-treatment`). Pins route, seed, N repeats.
**Sink isolation (review-fix R1c cycle 1):** benchmark runs MUST target an isolated
`TelemetryConfig` whose sink directory is dedicated to the benchmark (e.g. a run-scoped
`benchmark/` metrics dir), never the repository's authoritative `.autoharness/metrics` store, so
benchmark epochs cannot pollute production telemetry aggregates. Synthetic `backlog_item_id`/
`workspace_id` use a reserved `benchmark:` namespace prefix.
- **Acceptance:** running a scenario produces **exactly two correlated epochs per repeat** (one
  baseline + one treatment), i.e. **2×N epochs total for N repeats**, each with a unique per-repeat
  epoch identity — repeats never overwrite or collapse before persistence, so all repeats are
  independently readable via `read_epoch_records`; arms are distinguishable by `phase`; determinism
  verified across repeats for operations counters; **the authoritative metrics store is provably
  untouched** (benchmark reader points only at the isolated benchmark sink dir).

### 085.003-T — Correctness scorer (family: code)  — dep: 001
Separate-axis scorer grading each arm's produced target set against the scenario gold answer
(precision / recall / exact-match). No coupling to efficiency metrics.
- **Acceptance:** exact-match, partial, and miss cases score deterministically; scorer output
  carries no token/cost fields (axis separation enforced).

### 085.004-T — Telemetry metrics extraction + A/B delta adapter (family: code)  — dep: 002
Adapter that reads persisted epochs via `read_epoch_records`, slices arms with
`summarize_report(filters={phase: ...})`, and computes per-scenario + aggregate A/B deltas for
tokens/context/cost/latency and routed-vs-raw/avoided-read/`net_offload_tokens`. Combines
`metric_quality`/`derived_quality` across operands with a **deterministic delta-provenance rule**:
the delta carries the **least-certain** quality across all operands (baseline, treatment, and every
repeat), and any `unavailable` or `not_applicable` operand makes the delta `unavailable`
(respectively `not_applicable`) — never a false-precision `observed`. Deltas use aggregate-total
slices (never averages of per-epoch ratios).
- **Acceptance:** delta for a known fixture matches hand-computed aggregate-total math; the
  delta-provenance rule is applied per field (least-certain across operands); a mixed
  observed/estimated comparison is labeled `estimated` (the least-certain operand), never
  `observed`; `unavailable`/`not_applicable` operands yield `unavailable`/`not_applicable`
  deltas (not 0).

### 085.005-T — Environment + repeatability controls (family: code)  — dep: 002
Reproducibility controls on the harness: pinned route capture, seed pinning, warm/cold/stale
index-state selection, `ENGRAM_DEGRADED` capture (`degraded_tool_count`,
`stale_or_unavailable_index_count`), N-repeat dispersion, and a run manifest recording
`workspace_id`/`commit_sha`/corpus-hash/route/seed. The run manifest also records the **isolated
benchmark sink path** (review-fix R1c) so a published result is reproducible and provably
sink-isolated.
- **Acceptance:** a cold-index treatment run is captured and classified as a negative/neutral
  case (not dropped or errored); run manifest reproduces the corpus hash; repeated runs report
  dispersion.

### 085.006-T — Honest reporting renderer (family: code)  — dep: 003, 004, 005
Report renderer that composes correctness + efficiency deltas into per-scenario and aggregate
output covering all three outcome classes. Enforces honest-reporting rules: distinguish
`unavailable` from observed-zero; surface `metric_quality`/`derived_quality`; label estimated/
derived aggregates; **suppress any efficiency "win" claim when correctness regressed**; retain
and display negative/degraded runs.
- **Acceptance:** an `unavailable` field renders as `unavailable` (never `0`); a correctness
  regression forces a non-win verdict regardless of token savings; a negative-class scenario
  appears in output; estimated aggregates are flagged.

### 085.007-T — Unit tests for benchmark suite (family: test)  — dep: 005, 006
`tests/` coverage: corpus loader + balanced-class invariant, correctness scorer axis separation,
metrics/delta adapter aggregate-total math, provenance honesty (`unavailable` vs observed-zero,
malformed-label fail-closed), reporting rules (no-win-on-correctness-regression, negatives shown),
degraded-index capture. Uses the canonical unittest gate.
- **Acceptance:** tests fail if any honest-reporting rule regresses; provenance and axis-separation
  invariants are pinned; no network / no live-agent dependency.

### 085.008-T — Methodology + interpretation docs (family: docs)  — dep: 005, 006
`docs/` methodology + how-to-run + interpretation guide: scenario-class rationale, baseline/
treatment definitions, measures, provenance caveats (what `unavailable`/`estimated`/`derived`
mean here), honest-reporting rules, and reproducibility (corpus hash, pinned route/seed). Marks
the deterministic core as the reproducible unit and live mode as an additive opt-in.
- **Acceptance:** no unresolved cross-references; every measure in the report maps to a documented
  provenance rule; interpretation guide states the correctness-over-efficiency precedence.

## Dependency order

`085-F` (parent) → 001 → {002, 003}; 002 → {004, 005}; {003, 004, 005} → 006 → {007, 008}

Add order for shipment: 001, 002, 003, 004, 005, 006, 007, 008.

## Width-isolation ledger

| Task | Family | Touches |
|---|---|---|
| 001 | code | eval/benchmark scenarios + corpus fixture |
| 002 | code | eval/benchmark run harness (telemetry begin/record consumer) |
| 003 | code | eval/benchmark correctness scorer |
| 004 | code | eval/benchmark metrics/delta adapter (reader/report consumer) |
| 005 | code | eval/benchmark reproducibility controls + run manifest |
| 006 | code | eval/benchmark honest reporting renderer |
| 007 | test | tests/ only |
| 008 | docs | docs/ only |

No task crosses a family boundary; no task mixes benchmark code with schema or CLI-distribution
work. Telemetry contract is consumed read-only.

## Risks

- **R1 — Overstating unavailable data.** Mitigated by 004/006 acceptance pinning `unavailable`
  ≠ 0 and provenance surfacing; test-enforced in 007.
- **R2 — Cherry-picked corpus.** Mitigated by 001 balanced-class invariant (test-enforced) and
  published corpus hash + per-case rationale.
- **R3 — Correctness/efficiency conflation.** Mitigated by 003 axis separation and 006 no-win-on-
  regression rule.
- **R4 — Determinism mistaken for realism.** Mitigated by explicit `estimated` provenance on
  synthesized token/cost and docs (008) framing the deterministic core as a proxy + live opt-in.
- **R5 — Degraded-index runs silently dropped.** Mitigated by 005 capturing and classifying them.

## Plan hardening (P-006) — determination: REQUIRED, and APPLIED

`requires_plan_hardening: yes`. Signal: elevated blast radius is **result-integrity** (a benchmark
that overstates or hides negatives is actively harmful) plus **multi-family** surface (eval code /
tests / docs / fixtures). Below is the applied hardening.

### Failure-mode analysis + mitigations

| # | Failure mode | Blast | Mitigation (owning task) | Verified by |
|---|---|---|---|---|
| H1 | `unavailable` token/cost rendered as `0`, implying a false savings | result integrity | Preserve `metric_quality`; render `unavailable` literally (004/006) | 007 provenance test |
| H2 | Corpus omits neutral/negative → cherry-picked "wins" | credibility | Balanced-class invariant + published hash (001) | 007 invariant test |
| H3 | Efficiency win reported despite correctness regression | misleading verdict | No-win-on-regression rule (006); axis separation (003) | 007 rule test |
| H4 | Deterministic estimates presented as observed | false precision | Force `metric_quality=estimated` on synthesized fields (002/004); docs (008) | 007 + doc-review |
| H5 | Degraded/cold-index treatment run dropped as an "error" | hidden negative | Capture + classify degraded runs (005) | 007 degraded test |
| H6 | Per-epoch ratio averaging instead of aggregate-total denominators | wrong deltas | Reuse aggregation contract; deltas from slice totals (004) | 007 delta math test |
| H7 | Scope creep into telemetry-contract / CLI-distribution change | boundary breach | Read-only consumer; width-isolation ledger; no schema/CLI task | plan-review scope check |

### Rollback / blast-containment

The suite is **purely additive** (new `eval/benchmark` modules, new tests, new docs, new corpus
fixture). Removing the new modules/fixtures reverts to pre-085-F behavior with zero telemetry or
CLI change. No migration or backfill. Live-run mode is opt-in and off by default.

### Residual risks (accepted, documented in 008)

- Deterministic core is a proxy for live agent behavior (accepted; live opt-in + estimated
  provenance disclose this).
- Corpus representativeness is a validity claim (accepted; per-case rationale + hash make it
  auditable and revisable).

## Out of scope

- Any change to ExecutionEpoch v1.1 / ToolTelemetryEvent v1.0 schemas or the sink/reader/report
  math (consumed read-only).
- A new `telemetry report` CLI subcommand (not shipped by 092-S; benchmark uses the library API).
- Ship-phase execution: implementation, branch/PR, build/test runs, commit/push (owned by Ship).
- **Live-run mode implementation/verification.** Deferred: this shipment delivers only the
  deterministic replay core. Live mode remains a documented (008), off-by-default, additive
  opt-in extension point; no task here implements or verifies a callable live path. A future
  increment owns live-run implementation and its own acceptance.
