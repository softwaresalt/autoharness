---
shipment: 223-S
feature: 216-F
pr: 552
merge_commit: 386757af97d0b66072c115f5739044d15d1d0be6
reviewed_head: 009177026bcbd73ba8fe68f1a0baad94650e9444
date: 2026-10-23
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/223-S-216-F-close-evidence.json
---

# 223-S / 216-F Post-Merge Closure: docs-only route checker

## Summary

Shipment 223-S (feature 216-F, tasks 216.001-T through 216.009-T) merged through PR #552 as merge commit `386757af97d0b66072c115f5739044d15d1d0be6` (merge commit strategy, P-009). Closure ran on `post-merge/223-s-216-f-docs-only-route` under dark mode (P-017). No tag was created.

## Decisions

* Close path `cascade` through the mutating `autoharness shipment cascade-close`; no direct `backlogit shipment ship` call.
* Review-fix cycles 4 and beyond were operator-authorized.
* Remaining review findings were deferred as stash follow-ups (see Follow-ups) rather than expanding scope (P-021).
* The failed first cascade-close record was handled through an operator-authorized move-aside (see Documented deviation).

## Gates

* P-014 local review readiness `READY` for reviewed HEAD `009177026bcbd73ba8fe68f1a0baad94650e9444` (the merged HEAD).
* P-018 copilot-review gate: `SATISFIED` for the merged HEAD; CI green at `009177026bcbd73ba8fe68f1a0baad94650e9444`.
* PR #552 merged as `386757af97d0b66072c115f5739044d15d1d0be6`. No admin fallback.
* Copilot review took 12 fix cycles: `20575f4e`, `a4f6dcb2`, `f247c254`, `4f73972c`, `c8e43848`, `4b29ec1b`, `f3dd58fa`, `64b3ae4e`, `d664e557`, `5d817e75`, `d9de1ad4`, `00917702`. The operator authorized cycle 4 and later.

## Documented deviation: cascade close attempt 1

* Attempt 1 failed: exit 6 `invocation_failed`, caused by a transient ~10 s internal backlogit lineage-check deadline on member `216.006-T` under host load. `mutation_state` was `none`; nothing was archived.
* `--replace-pre-close` refused with 'evidence already finalized': it cannot supersede a `post_close` record whose `mutation_state` is `none`.
* Operator-authorized dark-mode deviation: the failed record was hash-verified (SHA-256 `E7E70B91C1BC5A6E9150A4EC8CCEED4483459F880286C2873D961C849FA162AD`) against the preserved copy `docs/closure/evidence/223-S-216-F-close-evidence.attempt1-failed.json`, then moved (not edited) to `.autoharness/gates/cascade-close/223-S-216-F.attempt1-evidence.json`.
* `--classify-only` was redone and the ancestry of all 9 member heads was verified. One mutating re-run (attempt 2 of 3) succeeded. The preserved copy is committed with this closure PR.

## Shipment close

* Pre-mode report `.backlogit/reconcile/223-S-pre-20261023-024500.md` (PROCEED; qualifying feature 216-F).
* Close evidence phase `post_close`, postcondition `pass`.
* Linked-Deliberation Disposition (P-015 INV-12): `042-DL` `retained_description_mention`; the planner matched the Step 0(c) snapshot, nothing was archived (`DISPOSITION_COMPLETE`).
* Post-mode: PROCEED. Report `.backlogit/reconcile/223-S-post-20261023-072000.md`.
* Final: 223-S `archived_status: shipped`; 216-F and 216.001-T through 216.009-T archived (`done`).

## Follow-ups

Stash IDs: `C345FC7A`, `69C2D77B`, `AF61F88C`, `B942F27B`. Two further follow-ups (the transient backlogit lineage-check deadline, and `--replace-pre-close` superseding a finalized failed record with `mutation_state: none`) were captured only in the operator's uncommitted local stash intake, so they are not cited by ID here.

## Source artifact cleanup

No source stash cleanup performed.

## Residual risk and conditions

`closure_status: READY`. The follow-ups above are tracked stash entries, not closure conditions. Rollback: revert the merge commit through a PR; owner: Ship / operator.

## Compaction (P-020)

`compaction_status: done`. This unit's session memory was archived to `docs/archive/memory/2026-10-23/ship-223-s-216-f-post-merge-closure.md` with a summary at `docs/memory/compacted/2026-10-23-223-s-216-f-compacted.md`. Scan found no other candidates above thresholds that were acted on.

## Close evidence

Record: `docs/closure/evidence/223-S-216-F-close-evidence.json` (phase `post_close`).
