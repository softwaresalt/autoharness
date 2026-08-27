---
title: 'Closure Summary — 111-S through 113-S: Benchmark Suite, Staging Size/Complexity
  & Backlogit Telemetry Mapping (2026-08-03/04)'
source: docs/closure/2026-08-03-benchmark-staging-backlogit-telemetry-closure-summary.md
doc_type: closure-compaction-summary
compaction_phase: phase-3-closure-compaction
compacted_on: "2026-08-26"
period_start: "2026-08-03"
period_end: "2026-08-04"
shipments: [111-S, 112-S, 113-S]
features: [085-F, 107-F, 108-F]
source_artifacts:
  - docs/archive/closure/111-S-085-F-post-merge-closure.md
  - docs/archive/closure/112-S-107-F-post-merge-closure.md
  - docs/archive/closure/113-S-108-F-post-merge-closure.md
---

# Closure Summary — 111-S through 113-S: Benchmark Suite, Staging Size/Complexity & Backlogit Telemetry Mapping (2026-08-03/04)

Consolidates three post-merge closure records: the structural-navigation
benchmark suite (`085-F`), size+complexity first-class staging metadata
(`107-F`), and backlogit telemetry evidence mapping (`108-F`, a
backlogit-only carve-out of `082-F`). Source artifacts are preserved
verbatim at `docs/archive/closure/`.

## Shipments & Features Covered

| Shipment | Feature | Tasks | PR | Merge commit | Merged at | `closure_status` | `compaction_status` |
|---|---|---|---|---|---|---|---|
| 111-S | 085-F | 085.001–008-T (8) | #289 | `806f2fc23872fb073051c11c5d1c18d9836c3cca` | 2026-08-03T20:16:24Z | READY | done |
| 112-S | 107-F | 107.001–005-T (5) | #292 | `5311a3127e247e11a9ab25b1bfc0bd4095393a77` | 2026-08-04T01:06:14Z | READY | done |
| 113-S | 108-F | 108.001–004-T (4) | #294 | `c2011114edd302968145e05bd164fc0bd3ad5f3c` | 2026-08-04T07:29:34Z | READY | done |

All three merges verified as genuine two-parent merge commits (P-009).

## What Was Verified, and Verdict per Shipment

- **111-S / 085-F** — deterministic-core-first structural-navigation
  benchmark suite (`src/autoharness/eval/benchmark/`): scenario corpus +
  loader, run harness with isolated telemetry sink, correctness scorer,
  telemetry A/B delta adapter, reproducibility controls, honest reporting
  renderer. Purely additive; live-run mode explicitly deferred/out of
  scope. Local review: 0 P0, 1 P1 fixed (missing malformed-quality-label
  fail-closed test coverage) + 1 P3 fixed. **6 rounds of Copilot review, 15
  findings, all fixed** (scenario-id collision, label-trust ordering,
  reused-sink rejection, sink workspace-root containment hardened across 3
  rounds, run-identity validation/hardening, mandatory isolated-telemetry
  enforcement). Runtime: CLI probe PASS + full canonical unittest gate
  (1065 passed / 7 skipped / 0 failed). 98 new targeted tests. **Verdict:
  READY.**
- **112-S / 107-F** — task-level `size`/`complexity` made first-class,
  validated, non-conflated planning metadata (native `complexity` enum,
  reference doc, harvest-skill + `_stage` agent mandates with fail-closed
  enum validation, P-003 granularity gate on both axes, additive
  registry-schema field). Docs/templates/backlogit-config only — no `src/`
  change. Local review: READY, P0=0/P1=0. **3 rounds of Copilot review, 8
  findings, all fixed** (round 3 corrected backlogit 1.8.0's actual
  create/update call sequencing, verified against backlogit source);
  review-fix cycle limit (3) reached with no new findings in round 3.
  Runtime: CLI probe PASS; full-build not applicable (docs/config-only),
  verified instead via unittest (1065 passed/7 skipped/0 failed) +
  `verify-workspace` checksum scan (unchanged). **Verdict: READY.**
- **113-S / 108-F** — maps backlogit 1.8 telemetry evidence to the ratified
  `ToolTelemetryEvent`/`ExecutionEpoch` contract (observed vs. derived vs.
  unavailable/not_applicable), adds a structurally-separate task-level
  `complexity` dimension to the event schema (non-conflated with `size`),
  documents sensitivity/redaction guardrails. Local review: READY,
  P0=0/P1=0. Copilot review round 2: 4 findings, all fixed. Runtime: CLI
  probe PASS; full local build recorded (unittest 1093 tests OK skipped=7,
  CLI smoke, targeted telemetry suite 147 tests). **Verdict: READY.**

## Healthy Signals

- All three merges are genuine two-parent commits; P-009 preserved.
- 112-S's Copilot review round 3 caught and corrected a real
  backlogit-version-specific sequencing assumption before merge.
- 113-S explicitly left the linked (not parent/child) feature `082-F`
  untouched (`status: blocked`, queue-resident) throughout its own closure.
- Full canonical unittest gate stayed at 1065/1093 across the group with no
  regressions (111-S added 98 new tests; 113-S's telemetry suite added 147
  targeted tests).

## Failure Signals Observed — Move-vs-Archive Recurrence (Occurrences 2, 3, 4)

The "move vs. explicit archive" gap first identified at **109-S** (see the
2026-08-01 group summary) **recurred in every shipment in this group**:

- **111-S (2nd occurrence)**: this closure's first pass treated the 8
  manifest tasks, and symmetrically `085-F`, as already archived merely
  because their files physically resided under `.backlogit/archive/` (a
  `move --status done` side effect). A Copilot review thread on the closure
  PR caught the gap for the 8 tasks; the symmetric gap on `085-F` was then
  proactively found and fixed in the same pass. All 9 items plus the
  shipment were explicitly archived and re-verified.
- **112-S (3rd occurrence)**: caught **proactively** this time — before
  skipping any item as pre-archived — via the documented pre-flight `status:`
  field check, run against all 5 manifest tasks. No Copilot review thread was
  needed to catch it.
- **113-S (4th occurrence)**: caught **mid-procedure**, during the
  shipment/feature archival pre-flight, on all 4 manifest tasks.

Each occurrence was fixed with no corruption reaching `origin/main`, but the
recurrence across 3 consecutive shipments (after 109-S's original discovery
and 110-S's successful avoidance) confirms the compound-doc reminder alone
is insufficient; a stronger, scripted pre-flight enforcement step remains an
open follow-up (first recorded during 111-S's closure).

A second, unrelated process error in **111-S**: an initial archival commit
was mistakenly made directly on local `main` before the post-merge closure
branch existed. Caught before pushing; recovered via `git reset --hard` to
the merge commit and redone correctly on the closure branch. Documented in
`docs/compound/2026-08-03-post-merge-closure-branch-before-first-commit.md`.

## Monitoring, Validation Windows & Rollback Triggers

- **111-S**: rollback = revert `806f2fc...` (safe; purely additive package,
  no shipped file modified, live-run mode explicitly deferred so no
  partially-wired runtime surface exists). Validation window: immediate
  post-merge 2026-08-03.
- **112-S**: rollback = revert `5311a31...` (safe; docs/templates/config
  only, no `src/` behavior change). Validation window: immediate post-merge
  2026-08-04.
- **113-S**: rollback = revert `c201111...` (safe; additive schema mirror +
  docs, no destructive migration). Validation window: immediate post-merge
  2026-08-04.

## Unresolved Follow-Ups Carried Forward

1. **Move-vs-archive pre-flight enforcement** (open since 111-S, recurred
   through 112-S and 113-S): add an explicit/scripted pre-flight
   `backlogit get <id>` status-field check as a hard, unconditional step in
   the Step 5 Closure Tasks procedure, rather than relying solely on the
   compound-doc reminder. **Still open** at the close of this group.
2. **111-S residual risks** (both explicitly non-blocking, no exploit path
   identified): (a) `controls._outcome_classification()`'s neutral-collapse
   for an already-negative-class degraded scenario has confusing but
   harmless semantics — untested combination since the shipped corpus has no
   negative+degraded scenario; (b) a caller-supplied `ArmExecutor` that
   varies correctness by `repeat_index` remains explicitly out of scope
   (live-run mode) — `RepeatCorrectnessVarianceError` fails closed rather
   than silently under-scoring.
3. **112-S / 113-S**: no shipment-specific follow-ups beyond the shared
   move-vs-archive item above (both explicitly recorded `none` in their own
   Local Review Readiness follow-ups fields).
4. **113-S**: `082-F`'s remaining engram/graphtor-docs/agent-intercom scope
   (the portion not carved out into `108-F`) remains open and untouched,
   `status: blocked` — out of scope for this shipment, not resolved here.
