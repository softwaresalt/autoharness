---
title: "deliberation — Structural-Navigation Benchmark Design (085-F)"
type: deliberation
date: 2026-08-02
route: claude-opus-4.8 / anthropic / high (P-013.5, inherited)
feature: 085-F
spike: docs/spikes/2026-08-02-structural-navigation-benchmark-feasibility.md
decision_status: decided
chosen_option: "C — Hybrid, deterministic-core-first"
---

## Problem frame

The accepted product direction (TokenMasterX evaluation, Direction D) commits to a
structural-navigation benchmark with A/B/C-style before/after comparisons and **honest
negative results**. 079-F/084-F shipped the telemetry data contract and token-efficiency
metrics, so 085-F no longer proceeds on ad-hoc metrics — it consumes ExecutionEpoch v1.1 /
ToolTelemetryEvent v1.0 via the telemetry reader/report APIs. The open design question is
the **benchmark methodology**: how to generate before/after evidence that is (1) reproducible,
(2) honest about metric availability, and (3) representative — including neutral and negative
cases — for tightened Engram-first structural routing.

## Options considered

### Option A — Live end-to-end agent runs only
A real agent executes each navigation task under baseline (routing off) and treatment
(Engram-first) arms; epochs are captured from live host telemetry.
- **Pros:** Highest realism; measures true agent behavior.
- **Cons:** Non-deterministic; not CI-safe; host token/cost frequently `unavailable`
  (spike F1); expensive; hard to reproduce a published result. Fails the feature's
  "reproducible before/after evidence" goal.

### Option B — Deterministic replay/fixture harness only
A versioned scenario corpus with gold answers is driven through a deterministic navigation
executor (raw-read baseline vs Engram-first treatment), each arm emitting an ExecutionEpoch
through the shipped `telemetry begin`/`record` path; metrics read back via the reader/report API.
- **Pros:** Fully reproducible and CI-gateable; operations counters
  (`routed_lookup_count`, `raw_file_read_count`, `avoided_file_read_count`) are **observed**;
  corpus hash pins the experiment.
- **Cons:** A proxy for real behavior; token/cost may be `estimated`/`unavailable`; a
  deterministic model can be accused of encoding its own conclusion if scenarios are not
  representative and negatives are not deliberately included.

### Option C — Hybrid, deterministic-core-first
Ship the **deterministic replay core (Option B)** as the reproducible, CI-safe unit AND
provide a minimal **additive opt-in live-run mode (Option A)** that emits the *same*
ExecutionEpoch shape, so both funnel through the identical reader/report/aggregation path
and are comparable. Reporting labels every metric with its `metric_quality`
(`observed`/`estimated`/`unavailable`) so live-run host gaps are honest, not hidden.
- **Pros:** Reproducibility (deterministic core) + realism escape hatch (live mode) without
  forking the metrics path; honest provenance is intrinsic; negatives and degraded-index
  runs are first-class; scope stays additive over `src/autoharness/eval`.
- **Cons:** Slightly larger surface than B alone. Mitigated by shipping the deterministic
  core fully and keeping live mode a thin opt-in flag on the same runner/report seams.

## Chosen direction

**Option C — Hybrid, deterministic-core-first.**

Rationale: the feature's goals require BOTH reproducible before/after evidence (satisfied
only by a deterministic core) AND credible input to a real integration decision (which
benefits from occasional live validation). Because the shipped telemetry contract already
normalizes any producer into the same ExecutionEpoch v1.1 record and the same
aggregation/derived-metric math, a single reader/report layer serves both arms with no
contract change. Provenance (`metric_quality`/`derived_quality`, 095-S sparse map) makes
the deterministic core's `estimated` token figures and the live mode's `unavailable` host
figures **honest by construction**. This shipment delivers the deterministic core end to end
and exposes the live-run mode as an additive opt-in.

## Design commitments (feed the plan)

1. **Scenario classes are mandatory and balanced.** The corpus MUST contain positive
   (routing clearly reduces raw reads), neutral (routing neither helps nor hurts), and
   negative (routing costs more — cold/stale index, un-indexed novel file) cases. No
   cherry-picking; the corpus manifest hash is published.
2. **Two arms, paired, pinned.** Baseline = routing OFF (raw read/grep). Treatment =
   Engram-first ON. Same scenario, same pinned route (`claude-opus-4.8/anthropic/high`),
   same seed, N repeats. Deltas computed from aggregate-total slices (never averages of
   per-epoch ratios), per the aggregation contract.
3. **Correctness is a separate, non-tradeable axis.** A dedicated scorer grades each arm's
   produced target set against gold answers (precision/recall/exact-match). An efficiency
   win is never reported when correctness regressed.
4. **Honest reporting rules.** Distinguish `unavailable` from observed-zero; surface
   `metric_quality`/`derived_quality`; mark estimated/derived aggregates; report all three
   outcome classes; retain degraded/cold-index runs as negatives.
5. **Zero telemetry-contract change.** The benchmark is a pure consumer of the shipped
   reader/report/aggregation APIs and an additive layer over `src/autoharness/eval`.

## Open questions / risks (to plan hardening)

- OQ1: Deterministic token estimates could be mistaken for observed measurements →
  mitigation: force `metric_quality=estimated` for synthesized token/cost fields.
- OQ2: A representative corpus is itself a validity claim → mitigation: publish scenario
  provenance/rationale per case and the corpus hash; require the balanced-class invariant
  to be test-enforced.
- OQ3: Blast radius touches multiple families (eval code, tests, docs, fixtures) and the
  integrity of published results → routes to **plan hardening** (P-006).
