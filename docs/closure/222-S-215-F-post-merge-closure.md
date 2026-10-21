---
shipment: 222-S
feature: 215-F
pr: 550
merge_commit: 1b5dd29aed72af8071dbb7e037010740ddc71390
reviewed_head: c9c417d4
date: 2026-10-21
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/222-S-215-F-close-evidence.json
---

# 222-S / 215-F Post-Merge Closure: engine line 1.11 verified, 1.12 only after probe

## Summary

Shipment 222-S (feature 215-F, tasks 215.001-T and 215.002-T; release 1.6.0 chain 4/6) merged through PR #550 as merge commit `1b5dd29aed72af8071dbb7e037010740ddc71390` (merge commit strategy, P-009; two parents verified, in `origin/main`). The change adds the engine-line verification runbook `docs/engine-line-verification.md`, compatibility-matrix rows (v1.11.0 verified, HEAD unverified), and pin and drift-guard tests in `tests/test_engine_line_verification_runbook.py`. It makes no source, CI, or template changes. Closure ran on `post-merge/222-s-215-f-engine-line` under dark mode (P-017).

## Gates

* Reviewed HEADs: `8fa740f7` (local review clean, no P0/P1), then `c9c417d45ef29968a8874ab43ea7e36b57af7cbb` (merged HEAD). P-014 readiness `READY` recorded in the PR body for the merged HEAD.
* CI: all required checks passed on the first and final HEAD. Pre-push hook full unittest passed (4593 tests, skipped 69).
* P-018 copilot-review gate: `UNRESOLVED_THREADS` on the first HEAD, then `SATISFIED` on the merged HEAD and immediately before merge. One Copilot round, 4 findings, all fixed in `c9c417d4`. Threads replied and resolved, and a body-disposition comment was posted.
* Dark mode: no admin fallback, no tag created.

## Process deviations

* Telemetry begin/record and `backlogit_track_commit` were not run. No `backlogit commit` CLI exists, and the pre-merge task telemetry was skipped as observational.
* The file-lock skill was not invoked for the single-agent pre-mode report.

## Shipment close

* Lifecycle topology gate: exit 0 (`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`) before the close.
* Pre-mode (`expected_status: done`): PROCEED. Report `.backlogit/reconcile/222-S-pre-20261021-211500.md`. 215-F is the qualifying feature.
* Step 0(d) agreement-check outcome: `agreed` (CASCADE, qualifying feature set `215-F`; engine VERIFIED on backlogit 1.11.0).
* Close path: `cascade` via the mutating `autoharness shipment cascade-close` (`--detach` then `--poll`; final exit 0, postcondition `pass`). No direct `backlogit shipment ship` call.
* Linked-Deliberation Disposition (P-015 INV-12): `DISPOSITION_COMPLETE` (empty set).
* Post-mode: PROCEED. Report `.backlogit/reconcile/222-S-post-20261021-213000.md`.
* Final: 222-S `archived_status: shipped`; 215-F and its two tasks `archived_status: done`.

## Follow-ups

None.

## Source artifact cleanup

No source stash cleanup performed. The shipment carries no `source_stash_id`, and the plan-level stash `9AF294A4` still feeds later shipments in the chain.

## Residual risk and conditions

`closure_status: READY`. No open conditions. Rollback: revert the merge commit through a PR; owner: Ship / operator.

## Compaction (P-020)

`compaction_status: done`. This unit's session memory was archived to `docs/archive/memory/2026-10-21/ship-222-s-215-f-post-merge-closure.md` with a summary at `docs/memory/compacted/2026-10-21-222-s-215-f-compacted.md`.

## Close evidence

Record: `docs/closure/evidence/222-S-215-F-close-evidence.json` (phase `post_close`).
