# Session Memory: 157-S Ship Execution (final shipment, P-017 dark-factory sequence)

**Date**: 2026-08-30
**Agent**: Ship
**Shipment**: 157-S ("S1 -- Detector SDK, evidence-node contract, and gate pre-review reader"), feature 149-F, 15 tasks

## Context

Second and final shipment in a bounded operator-authorized P-017 dark-factory
sequence (`156-S -> 157-S`). 156-S was already merged, closed, and closure-
repaired (PR #419, merge commit `7674ca48362a358bd917d8c973a5325b5ff7ecd0`,
`docs/closure/156-S-148-F-post-merge-closure.md` with `closure_status: READY`)
before this shipment began. Successor topology gate confirmed 156-S was
terminal and closure-complete before 157-S was claimed.

## Outcome

- All 15 tasks implemented, tested, committed (149.001-T through 149.015-T).
- Local (pre-PR) adversarial review: 8 findings fixed directly (P-021 C3
  completions), 0 unresolved P0/P1.
- PR #420 created; 8 sequential Copilot hosted-review rounds
  (`70500e87`..`f5e19bea`), ~25 total findings, every one a P-021 C1
  same-contract-surface completion. **Zero deferred stash entries for the
  entire shipment.**
- Round 8 (final round) fixed: schema-mutation-in-place (third occurrence
  of this bug class -- see compound learning), missing
  `tool_version_dims` requirement for `ast`/`coverage`/`api` producer
  kinds, insufficient `NodeResult` payload serializability check, and an
  ART-01 `path.exists()` pathspec filter that missed working-tree
  directory deletions.
- P-018 `SATISFIED` at HEAD `f5e19bea` (0 unresolved threads).
- P-014 §1.9 local readiness gate: PASS (block updated to reflect current
  HEAD `f5e19bea` before merge -- the block had gone stale across the 8
  review rounds and needed an explicit refresh; this is a process note for
  future long-review-cycle shipments).
- P-009: repo confirmed merge-commit-only (`allow_squash_merge: false`,
  `allow_rebase_merge: false`).
- Merged via `gh pr merge 420 --merge` under `DARK_MODE_ACTIVE`
  pre-authorization. Merge commit `f93afa0eee8d228ff4a7ac54cf3b2b3b4ec5eeb9`,
  2 parents confirmed (`7674ca48...`, `f5e19bea...`).
- Backlog cascade-close (P-015 verified fully-covered-root exception):
  `backlogit shipment ship 157-S --sha f93afa0e...` archived exactly
  `149-F` + 15 tasks + `157-S` itself (17 items), zero returned/orphaned
  ids, two-set gate clean.
- Closure doc: `docs/closure/157-S-149-F-post-merge-closure.md`
  (`closure_status: READY`).
- Compound learning (split into 3 single-root-cause entries per Copilot
  review feedback on the closure PR):
  `docs/compound/2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md`,
  `docs/compound/2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md`,
  `docs/compound/2026-08-30-157-s-149-f-sdk-boundary-payload-completeness.md`.
- Post-merge closure branch:
  `post-merge/149-f-s1-detector-sdk-evidence-node-contract-and-gate-pre-review-reader`.

## Operational notes for future sessions

1. **`REVIEW_TIMEOUT` with an empty thread list is not a clean signal** --
   retry with a longer wait until a genuine `SATISFIED`/`UNRESOLVED_THREADS`
   verdict is observed. See compound learning doc for detail.
2. **Schema mirror files under `schemas/{contract}/{version}.schema.json`
   are immutable once they have commits predating the current shipment** --
   check `git log main -- <path>` before editing any schema file. Third
   occurrence of this bug class in this repository.
3. **The Local Review Readiness PR-body block can go stale across many
   review-fix-cycle iterations** -- refresh it to the actual final reviewed
   HEAD before relying on it for the P-014 gate, don't assume the
   originally-written block still applies.
4. `backlogit shipment ship` cascade close took ~8 minutes wall time for 17
   items in this run (faster than 156-S's ~11 minutes for 11 items,
   consistent with host-process contention being the dominant variable, not
   item count).
5. This was the **final shipment** in the bounded `[156-S, 157-S]` P-017
   dark-factory scope. No further shipment should be claimed under this
   activation without a new operator authorization.
