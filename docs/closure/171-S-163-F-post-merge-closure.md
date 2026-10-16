---
shipment: 171-S
feature: 163-F
pr: 527
merge_commit: 2a159b27f2b295228c000c34f50b529a94fe47a5
reviewed_head: 0274e8a2
date: 2026-10-16
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/171-S-163-F-close-evidence.json
---

# 171-S / 163-F Post-Merge Closure: Shipment-Reconcile Step 0(c) Evidence Gate

## Summary

Shipment 171-S (covering feature 163-F, tasks 163.001-T through 163.009-T) merged through PR #527 as merge commit `2a159b27f2b295228c000c34f50b529a94fe47a5` (merge commit strategy, P-009; two parents verified, present in `origin/main`). The change makes the Step 0(c) pre-mutation evidence record provable by the closure-evidence gate. This is the first closure under the new ordering gate.

## Gates

* Reviewed HEAD of the PR: `0274e8a2` (PR head at merge). Merge: merge commit only; admin fallback not used.
* Evidence ordering: the `--classify-only` run (`pre_close.captured_at` 2026-10-16T06:29:46Z) happened after the merge and before any member close mutation.

## Shipment close

* Pre-mode (`expected_status: done`): every manifest member `matched` or `pre-archived` (feature `163-F` `active` under the qualifying-feature row; 163.006-T and 163.008-T `pre-archived`; the other six tasks `done`), no orphans, shipment record `record-consistent`. Recommendation: PROCEED.
* Step 0(d) agreement-check outcome: `agreed`. The Pre-Mode step 2b verdict (CASCADE, qualifying feature set `163-F`) equals the `--classify-only` evidence record (`classifier_verdict` CASCADE, `engine_verdict` VERIFIED on backlogit 1.11.0, `selected_close_path` cascade).
* Close path: `cascade`, through the mutating `autoharness shipment cascade-close` (exit 0). No direct `backlogit shipment ship` call was made.
* Postcondition: `pass`. `archived_ids` equals `required_ids`; `returned_ids` empty, `parent_id` preserved, baseline invariant, disposition byte-identical. Shipment `archived_status: shipped`; feature `163-F` `archived_status: done`.
* Linked-deliberation disposition (P-015 INV-12): `DISPOSITION_COMPLETE`. The only disposition-set deliberation, `033-DL`, is `retained_description_mention` (already `done` in `archive/`); nothing was archived.
* Post-mode: archive files present for the shipment, feature, and all nine tasks. No deleted archive files. Recommendation: PROCEED.
* Reports: `.backlogit/reconcile/171-S-pre-20261016-063000.md`, `.backlogit/reconcile/171-S-post-20261016-065000.md`.

## Follow-ups (P-021 C2 captures, capture-only)

Active stash entry `CA919C4C` (deferred capture-writer subsecond precision) stays active. Triage belongs to Stage; Ship did not triage, reprioritize, or edit it.

## Residual risk and conditions

`closure_status: READY`. No open conditions.

## Close evidence

Record: `docs/closure/evidence/171-S-163-F-close-evidence.json` (phase `post_close`, `merge_commit_sha` `2a159b27`, `classifier_verdict` CASCADE, `engine_verdict` VERIFIED, `postcondition_verdict` pass, `failures` none, `operator_action` none).

## Step 0(d) chronology disclosure

The Pre-Mode report `.backlogit/reconcile/171-S-pre-20261016-063000.md` carries a nominal frontmatter `generated_at` of `2026-10-16T06:30:00Z`, which is later than the evidence capture (`06:29:46Z`). It is a rounded value written by the executor, not a measured instant. The file's own creation time on disk was `06:29:14Z`, before the capture, and the report was produced by Pre-Mode before the `--classify-only` run. That filesystem timestamp is not durable committed evidence, so the `agreed` outcome rests on the content comparison (CASCADE verdict and qualifying set `163-F` equal in report and record), not on a provable ordering. The report was left unaltered (not backdated).

## Compaction (P-020)

`compaction_status: done`. compact-context (`target: all`) ran as a Tier-1 consolidation: session memory written to `docs/memory/2026-10-16/ship-171-s-163-f-post-merge-closure.md`, three 163-F/171-S Stage review-fix memories consolidated into `docs/memory/compacted/2026-10-16-171-s-163-f-compacted.md` and the originals moved to `docs/archive/memory/2026-09-10/`. Source stash entries (856B6770, A9BABC8B, D6502107, E1E31E6A) are no longer active (already retired by harvest).
