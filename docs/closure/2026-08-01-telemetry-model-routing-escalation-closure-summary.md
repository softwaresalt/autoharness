---
doc_type: closure-compaction-summary
compaction_phase: phase-3-closure-compaction
compacted_on: "2026-08-26"
period_start: "2026-08-01"
period_end: "2026-08-02"
shipments: [107-S, 108-S, 109-S, 110-S]
features: [084-F, 104-F, 105-F, 106-F]
source_artifacts:
  - docs/archive/closure/107-S-084-F-post-merge-closure.md
  - docs/archive/closure/108-S-104-F-post-merge-closure.md
  - docs/archive/closure/109-S-105-F-post-merge-closure.md
  - docs/archive/closure/110-S-106-F-post-merge-closure.md
---

# Closure Summary — 107-S through 110-S: Telemetry Events, Model-Routing Enforcement & Escalation Protocol (2026-08-01/02)

Consolidates four post-merge closure records: token-efficiency telemetry
event emission and deterministic epoch composition (`084-F`), role-based
model-routing enforcement at invocation time (`104-F`) — the **final
shipment of the bounded dark-mode scope `[107-S, 108-S]`** — shipment-record-
status classification (`105-F`), and the telemetry-driven auto-escalation
protocol / P-013.6 (`106-F`). Source artifacts are preserved verbatim at
`docs/archive/closure/`.

## Shipments & Features Covered

| Shipment | Feature | Tasks | PR | Merge commit | Merged at | `closure_status` | `compaction_status` |
|---|---|---|---|---|---|---|---|
| 107-S | 084-F | 084.001–008-T (8) | #273 | `364f6b07abc2418ec9f696603d5da4b9cf879256` | 2026-08-01T19:25:34Z | READY | done |
| 108-S | 104-F | 104.001–009-T (9) | #276 | `f37e251e6bda94dd1233c11907054f71bc8f529e` | 2026-08-02T01:41:59Z | READY | done |
| 109-S | 105-F | 105.001–002-T (2) | #280 | `b9829d1135396939f978f0c048627365e85091e0` | 2026-08-02T07:00:34Z | READY | done |
| 110-S | 106-F | 106.001–009-T (9) | #284 | `ce294d3f19206dfbfeccbfbadd3ef1e109e59352` | 2026-08-02T20:57:02Z | READY | done |

All four merges verified as genuine two-parent merge commits (P-009).

## What Was Verified, and Verdict per Shipment

- **107-S / 084-F** — bounded `ToolTelemetryEvent` JSONL journal + deterministic
  epoch composer. Sole hosted Copilot review round: 6 threads, all fixed with
  25 new TDD tests (compound doc: `docs/compound/107-S-084-F-copilot-review-fix-patterns.md`).
  Process note: an initial backlog-archival commit was mistakenly made
  directly on `main` before the post-merge branch was cut — caught
  immediately, `main` hard-reset before push, redone correctly on the
  branch; no bad state reached `origin/main`. **Verdict: READY**, no
  blocking follow-ups.
- **108-S / 104-F** — P-013.5 invocation-time role-based model-routing
  enforcement. **3 hosted Copilot rounds, 10 total findings** (round 1: 8
  threads including a YAML frontmatter crash fix, an optional
  `model_provider` fix, a `ROUTING_DEGRADED` wording fix, and a hardcoded
  vendor-placeholder fix; round 2: 2 threads on verifier check scoping and
  type safety). Compound doc:
  `docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md`.
  **This is the final shipment of the bounded dark-mode scope `[107-S,
  108-S]`** — explicitly noted as scope-complete. **Verdict: READY**, no
  blocking follow-ups.
- **109-S / 105-F** — shipment-record-status classification, closing
  stash `2970FA4E` parts (1) READY-FOR-PLANNING and (3) LEARNING-FOLLOW-UP.
  Local review cycle 1/3: 1 P1 fixed (undefined branch for record status
  `ACTIVE`/`DONE`) + 1 P3 fixed (dead ternary). Copilot review pass 1: 1
  comment fixed; pass 2: 1 comment classified **Partial** — narrower risk
  resolved, broader remedy declined as out-of-scope with an explicit
  residual-risk note. Runtime: CLI probe PASS + full canonical unittest gate
  (937 tests, OK, skipped=7). **Verdict: READY.**
- **110-S / 106-F** — telemetry-driven auto-escalation protocol (P-013.6):
  a new either-agent `escalation-protocol.instructions.md`, Stage/Ship
  directives making the agent-directed escalation steps active now, a
  `model_routing.escalation` schema field with per-field fallback, and a
  decision doc recording the external-guard boundary (live telemetry
  emitter/store and an automated non-agent threshold-evaluator remain out of
  scope). Local review cycle 1/3: 1 MD025 fixed + 1 doc-accuracy fixed.
  Copilot review cycle 2/3: **5 findings, all fixed** (framing inaccuracy
  across 4 files re: "dormant until runtime"; stale Ship Model-Routing
  prose; missing schema stanza; non-fail-closed directive-presence check;
  same-route check gap for installed-but-unset-override roles). Runtime: CLI
  probe PASS + full canonical unittest gate (953 tests, OK, skipped=7) + full
  local build (`uv build`, `autoharness-1.4.11` sdist/wheel). **Verdict:
  READY.**

## Healthy Signals

- All four merges are genuine two-parent commits; P-009 preserved.
- 107-S/108-S together close out the `[107-S, 108-S]` dark-mode scope
  cleanly, with all Copilot findings fixed (no deferrals in either
  shipment).
- 109-S and 110-S both re-verify CI/§1.9/P-018 gates unconditionally
  immediately before merge, not carried over from a prior pass.
- 110-S proactively applied the `109-S` move-vs-archive closure lesson (see
  below) and needed no correction cycle.
- Full canonical unittest gate test counts climbed monotonically across the
  group with zero regressions: 937 (109-S) → 953 (110-S).

## Failure Signals Observed

- **109-S** (first occurrence): the closure-PR's own Copilot review found
  that (a) the initial closure evidence cited a repository-root `pytest` run
  instead of the canonical `PYTHONPATH=src python -m unittest discover -s
  tests` gate, and (b) `109-S`, `105.002-T`, and `105.001-T` had only been
  `backlogit move --status done`'d (which relocates the file into
  `.backlogit/archive/` as a side effect) but never had the explicit
  `backlogit archive <id>` command run, so none carried
  `archived_status`/`archived_from` metadata. **This is the first recorded
  occurrence of the recurring "move vs. explicit archive" gap** — fixed in
  this closure by running `backlogit archive` explicitly on all three
  artifacts; documented in
  `docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md`.
- **110-S**: applied the 109-S lesson proactively — every manifest artifact
  received the explicit `backlogit archive <id>` call from the start. **No
  occurrence this time** (the gap was successfully avoided, not merely
  fixed after the fact).
- 109-S's declined Copilot finding (safe-close step 4 archives any manifest
  item regardless of `artifact_type`) is a legitimate residual risk, not a
  live defect — recorded as a follow-up below.

## Monitoring, Validation Windows & Rollback Triggers

- **107-S**: rollback = revert merge commit `364f6b07...`. No destructive
  migration; additive journal/composer only.
- **108-S**: rollback = revert merge commit `f37e251e...`. Routing is
  additive with tier3 fallback; existing installs unaffected until opt-in.
- **109-S**: rollback = revert merge commit `b9829d1...` (no schema/data
  migration in either direction). Validation window: immediate post-merge on
  2026-08-02.
- **110-S**: rollback = revert merge commit `ce294d3...`. The escalation
  route is optional with tier3 fallback, so existing installs are unaffected
  until they opt in. Validation window: immediate post-merge on 2026-08-02.

## Unresolved Follow-Ups Carried Forward

1. **109-S**: one non-blocking residual-risk item — harden
   `shipment-reconcile` per-item classification / safe-close against
   malformed (non-task-only) manifests. Recommended for Stage triage; not
   created by Ship (P-010 role boundary).
2. **Move-vs-archive enforcement gap**: first surfaced at **109-S**
   (occurrence 1 of what becomes a recurring pattern across later
   shipments in this compaction set — see the 2026-08-03 and subsequent
   group summaries). **110-S avoided recurrence** by applying the lesson
   proactively. No stronger enforcement (e.g., a scripted pre-flight check)
   had yet been added as of 110-S's closure.
3. Carried-forward external items from the prior group remain open as of
   this window's shipments and are not resolved here: stash `5F14396E`
   (broad `docs/memory` compaction sweep), stash `6D6CACC1` (backlogit
   internals, routed upstream). Stash `2970FA4E` is **partially closed**
   by 109-S (parts 1 and 3); its narrower part (2) status is not
   independently confirmed in these four records.
