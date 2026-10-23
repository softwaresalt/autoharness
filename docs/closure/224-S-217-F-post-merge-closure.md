---
shipment: 224-S
feature: 217-F
pr: 554
merge_commit: eec5aafb78b63169a9b5bbe93aa31ce2731ee37f
reviewed_head: a597de89
date: 2026-10-23
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/224-S-217-F-close-evidence.json
---

# 224-S / 217-F Post-Merge Closure: Release 1.6.0 cut (ready to tag, operator-only tag)

## Summary

Shipment 224-S (feature 217-F, tasks 217.001-T through 217.004-T; release 1.6.0 chain 6/6) merged through PR #554 as merge commit `eec5aafb78b63169a9b5bbe93aa31ce2731ee37f` (merge commit strategy, P-009). The change cuts the 1.6.0 version sites, changelog, release notes, upgrade guide and readiness evidence. No agent created, pushed or triggered a tag; tagging is an operator-only action (see `docs/releases/1.6.0-readiness-evidence.md`, E10).

## Gates

* Reviewed HEADs: `a597de89` (local review), then `03006334c5d70995d1ec25ea53efdddf9db12f8a` (final merged HEAD). P-014 readiness recorded in the PR body for the merged HEAD.
* CI: all required checks green.
* P-018 copilot-review gate: `SATISFIED`.
* Merge strategy: merge commit only (P-009); no squash or rebase, no admin fallback, no tag.

## Shipment close

* Pre-mode (`expected_status: done`): PROCEED. Report `.backlogit/reconcile/224-S-pre-20261023-213000.md`. 217-F is the qualifying feature.
* Step 0(d) agreement-check outcome: `agreed`, per the evidence record's `pre_close` snapshot (CASCADE, qualifying feature set `217-F`; engine VERIFIED on backlogit 1.11.0).
* Close path: `cascade` via the mutating `autoharness shipment cascade-close` (attached, `--caller-wait 2400`; final exit 0, phase `post_close`, postcondition `pass`). No direct `backlogit shipment ship` call by an agent.
* Linked-Deliberation Disposition (P-015 INV-12): `DISPOSITION_COMPLETE` (empty set; no mutation). The lock was held on `.backlogit/archive/224-S.md` because the queue file no longer exists after the close, and released afterwards.
* Post-mode: PROCEED. Report `.backlogit/reconcile/224-S-post-20261023-222400.md`.
* Final: 224-S `archived_status: shipped`; 217-F and its four tasks `archived_status: done`.

## Incident note: cascade-close attempts

* Attempt 1 (mutating): ended `never_started`. The supervisor authorize window (`valid_until = written_at + 30s`) expired before the child spawned, because of host latency.
* Attempt 2 (mutating, via `--detach`): also ended `never_started` for the same reason.
* Attempt 3 (mutating, attached, `--caller-wait 2400`): succeeded. The `backlogit shipment ship` child ran about 28 minutes and exited 0.
* No evidence record was moved aside. One `--replace-pre-close` reclassification was used, through the documented `never_started` supersede path.
* The circuit-breaker threshold was not reached for the same failure, and the final run succeeded, so no circuit-break note was written.

## Follow-ups

Captured as capture-only stash entries (provisional priorities, deferred scope; triage is Stage-only):

* Ten failing `autoharness verify-workspace --workspace .` targeted checks on the dogfood workspace (stale dogfood self-install; needs a tune or reinstall). This is an operator decision to accept or remediate before tagging 1.6.0; it gates the tag, not this closure, so it is recorded as a residual condition below rather than as a closure condition.
* `uv build` and `uvx` fail the TLS handshake to `files.pythonhosted.org` on this host; the build was done offline with `--no-build-isolation`.
* The editable-install metadata reports autoharness 1.5.0 until the package is reinstalled.
* The cascade-close supervisor authorize validity is fixed at 30 seconds (`AUTHORIZE_VALIDITY_SECONDS` in `command.py`) and should be configurable or scale with host latency; the supervisor ended `never_started` twice on 224-S.

## Source artifact cleanup

No source stash cleanup performed.

## Residual risk and conditions

`closure_status: READY`. Pre-tag operator condition (not a closure condition): the operator accepts or remediates the ten dogfood `verify-workspace` failures before tagging. Rollback: revert the merge commit through a PR; owner: Ship / operator.

## Compaction (P-020)

`compaction_status: done`.

## Close evidence

Record: `docs/closure/evidence/224-S-217-F-close-evidence.json` (phase `post_close`).
