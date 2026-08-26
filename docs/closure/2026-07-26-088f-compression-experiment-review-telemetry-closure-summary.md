---
doc_type: closure-compaction-summary
compaction_phase: phase-3-closure-compaction
compacted_on: "2026-08-26"
period_start: "2026-07-26"
period_end: "2026-07-28"
shipments: [093-S, 094-S, 096-S, 097-S]
features: [088-F, 089-F, 091-F, 092-F]
source_artifacts:
  - docs/archive/closure/093-S-088-F-post-merge-closure.md
  - docs/archive/closure/094-S-089-F-post-merge-closure.md
  - docs/archive/closure/096-S-091-F-post-merge-closure.md
  - docs/archive/closure/097-S-092-F-post-merge-closure.md
---

# Closure Summary — 093-S through 097-S: 088-F Compression Experiment, Review Routing & Telemetry Hardening (2026-07-26 to 2026-07-28)

Consolidates four post-merge closure records spanning the throwaway
Copilot-CLI output-compression experiment (`088-F`), its Copilot
review-follow-up hardening (`089-F`), multi-model review-routing
enhancements (`091-F`), and telemetry subsystem follow-up hardening
(`092-F`). Source artifacts are preserved verbatim at
`docs/archive/closure/`; this file is a compaction, not a replacement
record of authority.

## Note on `compaction_status`

**None of these four source records contain a `compaction_status` field.**
The field was introduced starting with shipment `104-S` (2026-07-30
onward); it does not exist in the harness's closure-record convention
before that date. This is not an omission by this compaction — it is
accurately reflecting the absence of the field in the original records.

## Shipments & Features Covered

| Shipment | Feature | PR | Merge commit | Merged at | `closure_status` |
|---|---|---|---|---|---|
| 093-S | 088-F | #229 | `e5470befd3f52bcde6f181666a00bce5ca04e014` | 2026-07-26T06:15:16Z | **READY_WITH_CONDITIONS** |
| 094-S | 089-F | #232 | `afa25f2e27abe32b89981cf2a280cdab0349ae13` | 2026-07-26T08:56:28Z | READY |
| 096-S | 091-F | #238 | `42a5d6b9ae6649b997e60efb56f30ea3aae9f4af` | 2026-07-28T06:22:42Z | READY |
| 097-S | 092-F | #241 | `52851c2` | 2026-07-28T21:09:01Z | READY |

All four merges verified as genuine two-parent merge commits on `main`
(P-009 / Constitution XI — no squash, no rebase).

## What Was Verified, and Verdict per Shipment

- **093-S / 088-F** — Copilot CLI output-compression experiment: a
  throwaway, flag-gated (`BRAINSPACE_EXPERIMENT_ENABLED`), disabled-by-default
  prototype under `experiments/088-compression-experiment/`. Verified:
  isolation (zero imports from `src/autoharness`), disabled-by-default no-op
  passthrough, workspace-containment tests, base-harness regression (680
  passed/140 subtests, unchanged baseline), experiment suite (226 passed, 2
  skipped — tiktoken-dependent), CI green. **Verdict: READY_WITH_CONDITIONS**
  — base harness unconditionally releasable; the experiment itself carries
  2 residual escalated findings (below) plus pilot-promotion preconditions.
- **094-S / 089-F** — Hardening pass closing both 093-S findings via TDD
  (`089.001-T`, `089.002-T`). Verified: fail-safe non-string-`cwd` tests,
  benchmark early-decline evidence tests, experiment suite (231 passed, 2
  skipped), base-harness regression (680 passed/140 subtests, unchanged), CI
  green, 1 Copilot finding (test non-determinism re: tiktoken) fixed before
  merge. **Verdict: READY**, no conditions outstanding.
- **096-S / 091-F** — Multi-model adversarial review-routing enhancements
  (anchor-review route defaults, plurality confidence classification,
  persona install-path normalization to canonical `.github/agents/subagents/`).
  Verified: targeted anchor-routing tests (10 passed), full suite (711 tests
  OK), manifest checksum scan clean for edited skills, CI green. **Verdict:
  READY.**
- **097-S / 092-F** — Telemetry subsystem follow-up hardening (disabled
  idempotency summaries, metric provenance observability, JSONL scan reuse,
  Ship-lifecycle freshness coverage, derived size monotonicity). Verified:
  canonical gate `PYTHONPATH=src python -m unittest discover -s tests` → 721
  tests OK, CI green at feature PR merge gate. **Verdict: READY.**

## Healthy Signals

- All four PRs merged via genuine merge commits; no squash/rebase found.
- CI green at every merge gate across all four shipments.
- 093-S/094-S: complete isolation of the experiment from base-harness
  runtime maintained throughout (verified both pre- and post-hardening).
- 096-S: anchor-review route and persona path conventions verified
  structurally (schema parity, placeholder placement, path integrity).
- 097-S: telemetry hardening verified via the canonical unittest gate with
  no regressions.

## Failure Signals Observed

- **093-S residual findings** (both fixed in 094-S, not left open):
  `workspace.py:152` — a dict payload with a truthy non-string `cwd` reached
  `os.path.realpath()` and raised an uncaught `TypeError` (fail-safe
  passthrough gap, low severity); `benchmark.py:215` — the early-decline
  return path dropped `capture_failed`/non-live `provenance` fields, an
  evidence-honesty gap affecting SAFE WIN determinations in the benchmark
  report (moderate severity).
- **097-S**: telemetry JSONL log growth has no rotation/retention policy —
  tracked as a residual follow-up (see below), not fixed in this window.
- No other regressions or unresolved failure signals recorded across the
  four shipments.

## Process Deviations (P-015) — Documented, Not Sanctioned

- **093-S**: closed via the forbidden cascade command
  `backlogit shipment ship 093-S` rather than the required single-artifact
  safe-close procedure. Verified via `backlogit doctor` and queue enumeration
  that no corruption occurred (093-S's manifest was exactly 088-F's complete
  7-task set, so there was no protected sibling set to violate). **Recorded
  explicitly as a correction, not a sanctioned exception** — the
  single-artifact safe-close procedure is unconditionally required for every
  shipment closure, regardless of whether this particular run happened to be
  safe.
- **096-S**: also used the `backlogit shipment ship 096-S` cascade, this
  time **operator-directed explicitly**. Recorded as a bounded, explicit
  P-015 deviation. Verified safe afterward: the cascade archived exactly the
  task-only manifest (`091.001-T`–`091.008-T`) plus the derived covering
  feature `091-F`, with no corruption found.

## Monitoring, Validation Windows & Rollback Triggers

- **093-S/094-S**: not applicable for the base harness (nothing deployed by
  default). If an operator opts in locally, the experiment's own store
  TTL/purge and fail-safe-passthrough stderr logging is the only monitoring
  surface. Rollback: delete `experiments/088-compression-experiment/` (or
  never opt in) — no schema/CLI-distribution/generated-artifact dependency.
  094-S rollback: revert merge commit `afa25f2e...` (single-commit revert,
  no dependents at time of closure).
- **096-S**: rollback = revert merge commit `42a5d6b9...` if the routing
  contract must be removed. No runtime surface to monitor (templates/schemas/
  skills/docs only).
- **097-S**: validation window = immediate post-merge on 2026-07-28 after
  `main` synced to `52851c2`. Rollback trigger: revert `52851c2` if telemetry
  record writes, JSONL append/replay, or aggregation/reporting consumers
  regress.

## Unresolved Follow-Ups Carried Forward

1. **Pilot-promotion preconditions for the 088-F experiment** (from 093-S,
   still open as of these closures — not resolved by any subsequent shipment
   in this group): real `tiktoken` availability in a pilot environment, a
   stronger task-answerability proof beyond the substring proxy, a wider
   adversarial benchmark corpus, explicit product/security sign-off on
   retention semantics, and a re-run of the round-9 decline-control
   regression (`unwritable-store-passthrough`, reads 6/7 without a real
   tokenizer) once `tiktoken` is installed. These gate any future narrow
   pilot decision, not the merged base harness.
2. **097-S**: JSONL sink rotation/retention for telemetry logs — tracked as
   Stage-filed stash entry **`7D1E2F1A`**. Ship did not create the stash item
   directly (P-010 role boundary; Ship cannot create stash entries).

No other residual follow-ups were recorded across this group (094-S and
096-S both explicitly closed with zero outstanding follow-ups).
