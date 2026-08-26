---
title: "Structural-Navigation Benchmark Suite"
doc_type: decided-plan
status: planned
created: 2026-08-02
feature: "085-F"
tasks: ["085.001-T", "085.002-T", "085.003-T", "085.004-T", "085.005-T", "085.006-T", "085.007-T", "085.008-T"]
supersedes:
  - docs/archive/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md
---

# Decided Plan: Structural-Navigation Benchmark Suite

**Outcome:** Planned as feature `085-F` with chosen direction **C — Hybrid, deterministic-core-first**. P-006 hardening is present in the source plan, but no PR or merge evidence is recorded there, so status remains `planned`. The decided shipment delivers the reproducible deterministic replay core end to end, while keeping live-run mode as a documented, additive opt-in extension rather than part of this increment.

## Decisions

- Build the benchmark as an **additive layer** over the existing `src/autoharness/eval` A/B harness and the shipped telemetry read/report/aggregation APIs. No telemetry schema, telemetry contract, or CLI-distribution change is part of this plan.
- Benchmark two arms per scenario: a baseline path with direct/raw navigation and a treatment path with Engram-first routing. Use the existing `telemetry begin` / `telemetry record` seams rather than inventing a parallel metrics format.
- Keep **correctness** and **efficiency** as separate axes. Correctness scoring is independent of token/cost metrics, and the reporting layer must never declare an efficiency "win" when correctness regresses.
- Make honest reporting a first-class rule: `unavailable` is never rendered as observed zero, delta provenance takes the **least-certain** quality across operands, and negative/degraded runs stay visible instead of being dropped.
- Make the deterministic replay core the shipped unit. Live-run mode is explicitly deferred because reproducible replay is the bounded, verifiable core and does not require new live-execution or network-dependent machinery.

## Implementation (8 tasks)

- **085.001-T — Scenario corpus model + loader:** create the scenario model, loader, class labels, precondition metadata, balanced-class invariant, and deterministic corpus hash.
- **085.002-T — Baseline/treatment run harness:** execute correlated baseline/treatment arms for each scenario and repeat, writing exactly `2×N` persisted epochs for `N` repeats.
- **085.003-T — Correctness scorer:** grade target sets against gold answers with deterministic precision/recall/exact-match logic.
- **085.004-T — Telemetry metrics extraction + A/B delta adapter:** read persisted epochs, compute per-scenario and aggregate deltas, and apply the least-certain provenance rule.
- **085.005-T — Environment + repeatability controls:** pin route/seed, capture warm/cold/stale index state, retain degraded runs, and record a run manifest.
- **085.006-T — Honest reporting renderer:** combine correctness and efficiency output without hiding regressions, unavailable data, or negative cases.
- **085.007-T — Unit tests:** pin corpus invariants, axis separation, aggregate-total delta math, provenance honesty, degraded capture, and reporting rules.
- **085.008-T — Methodology + interpretation docs:** document scenario rationale, provenance meanings, deterministic-core scope, and how to interpret results.

## Key constraints preserved

- The corpus must be balanced across positive, neutral, and negative scenarios, with a deterministic manifest hash and per-case rationale.
- Benchmark runs write to an **isolated benchmark telemetry sink**, never the repository's authoritative metrics store; synthetic ids stay in a reserved `benchmark:` namespace.
- Aggregate deltas are computed from slice totals, not from averages of per-epoch ratios.
- The telemetry contract is consumed **read-only**; the suite does not revise `ExecutionEpoch`, `ToolTelemetryEvent`, or a CLI subcommand surface.
- The suite stays offline-testable: no live agent, no network dependency, and no hidden reliance on live-run mode.

## Rejected alternatives

- **Shipping live-run mode in the same increment** — rejected to keep the benchmark reproducible, bounded, and verifiable. Live execution remains an additive follow-up.
- **Changing telemetry schemas or adding a benchmark-specific report CLI surface** — rejected because the existing read/report APIs already provide the needed contract.
- **Conflating correctness and efficiency** — rejected because a token-saving result that hurts accuracy is not a true benchmark win.
- **Treating unavailable metrics as zero** — rejected because it would overstate savings and conceal data quality limits.

## Post-review refinements folded in

- Review tightening added **sink isolation** and the reserved synthetic-id namespace so benchmark epochs cannot pollute production telemetry.
- The persisted-epoch acceptance was pinned to **exactly two correlated epochs per repeat** with unique per-repeat identity; repeats may not collapse or overwrite.
- Honest-reporting acceptance was sharpened so mixed observed/estimated inputs label deltas as the least-certain quality, and unavailable inputs stay unavailable.

## Rollback

The suite is purely additive: new benchmark modules, fixtures, tests, and docs. Reverting those additions restores the pre-085-F state with no telemetry-contract or CLI migration.