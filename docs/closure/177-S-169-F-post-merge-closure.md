---
shipment: 177-S
feature: 169-F
pr: 462
merge_commit: bd70630594aa97307395bf92ee08228e2add67b4
reviewed_head: 6a5ec1dfd96c5350a79f9aa9ee9ca38f223218dd
date: 2026-09-29
closure_status: READY
compaction_status: done
---

# 177-S / 169-F Post-Merge Closure: Canonical Post-Claim Member-Status Contract (P-002.7)

## Summary

Shipment 177-S (feature 169-F, tasks 169.007, 169.009 to 169.017-T) merged
through PR #462 as merge commit `bd706305`, using `--merge` with two parents
(`435f46ae`, `6a5ec1df`). The reviewed HEAD was `6a5ec1df`. The shipment makes
backlogit's post-claim member-status admission rule explicit and testable as
policy **P-002.7**:

* P-002.7 clause in the workflow policy registry
  (`.github/policies/workflow-policies.md` and its template)
* Ship intake-reconciliation cross-reference (`_ship.agent.md` mirror and
  template), bounded by `P-002.7:BEGIN/END` markers
* design doc `docs/design-docs/2026-09-29-post-claim-member-status-contract.md`
* structural cross-surface evidence: test-owned candidate definition,
  near-miss fixtures, and `tests/test_p002_7_member_status_contract.py`
* verdict-gated rollout: `.autoharness/gates/p002-7-preactivation-readiness.txt`
  = `PREACTIVATION_READY`, then ACTIVATE (`05ee60c7`), then
  `.autoharness/gates/p002-7-status-contract-verdict.txt` =
  `STATUS_CONTRACT_HELD`, then DOCS (`a249c186`)

## Gates and Dark-Mode Record (P-017)

| Gate | Result |
|---|---|
| Local multi-persona review | `READY_WITH_FOLLOWUPS`, P0=0, P1=0, at `6a5ec1df` |
| Full local build | `PYTHONPATH=src python -m unittest discover -s tests`: 2469 tests OK (54 skipped) |
| Copilot review (P-018) | 1 thread (`PRRT_kwDORzpWpM6m8gl-`), out of scope under P-021 C1, captured as `62C1E11E`, replied, resolved |
| Required CI | ci gate, test, pipeline-topology (ambient), detect code changes: all SUCCESS |
| P-009 merge strategy | merge commit; two parents verified |
| P-016 worktree topology | single worktree |
| Merge authority | `DARK_MODE_ACTIVE` `merge_approval_pre_authorized`; admin fallback not used |

## Validator Evidence / Runtime Verification

This shipment adds no runtime service surface. It changes only policy, agent
text, docs, and tests. The unit and structural suites verify it. The verdict
artifacts record the rollout-gate outcomes. No runtime validator probes apply.

## Closure Path

`shipment-reconcile` classified 177-S as `CASCADE` under P-015. Root feature
169-F has five out-of-manifest descendants (169.001, .002, .003, .005, and
.008-T). Each declares exact `status: archived`, so each is engine-inert. The
feature has no validated linked deliberations.

The evidence was **captured contemporaneously** at close time. That closes
the 175-S gap tracked by `008F3BCF`. The captured evidence:

* the Step 0 snapshot
* a fresh pre-invocation classifier and linked-deliberation revalidation, with
  no drift
* an SHA-256 baseline fingerprint of every descendant
* the raw `backlogit shipment ship` stdout (exit 0, stderr empty)

Postconditions:

* `returned_ids` = `[]`
* `archived_ids` = 169-F, the 10 manifest tasks, and 177-S
* `archived_ids - allowed_ids` = `[]`
* `required_ids - archived_ids` = `[]`
* every `parent_id` is preserved
* all 5 descendants are byte-identical to baseline
* the shipment record is `status: archived`, `archived_status: shipped`
* recommendation: `CLOSED`

Report: `.backlogit/reconcile/177-S-cascade-close-20260929-032534.md`.

## Source Artifact Cleanup

* Source stash entry `3EF5AAF2` was archived at Stage harvest on 2026-09-18,
  so no retirement action was required.
* 169-F and all 10 manifest tasks are archived with `archived_status: done`.
* Ship made no change to plan, review, spike, or decision artifacts, which are
  Stage-owned (P-010).

## Releasability Evidence

* **Status**: READY. No closure conditions are open. The follow-ups below are
  deferred-scope captures and do not block this unit.
* **Monitoring**: the CI `test` job, including the P-002.7 structural tests,
  and the pipeline-topology ambient gate run on every push. The next Ship claim
  exercises P-002.7's post-claim all-`active` expectation at intake
  reconciliation.
* **Rollback**: revert the merge commit with
  `git revert -m 1 bd70630594aa97307395bf92ee08228e2add67b4`. The change is
  documentation, policy, and tests only.
* **Owner**: operator (softwaresalt). The Ship agent owns closure mechanics.
* **Validation window**: through the next successor-shipment `pre_claim` and
  claim.

## Follow-Up Items

These are P-021 C2 deferred-scope captures. Stage owns triage.

* `065B0331`: prose in Ship item 5 / Step 2 still implies members are not
  `active` until Step 2. Behaviorally this is a no-op.
* `62C1E11E`: scope P-002.7 T1 to the verified backlogit ClaimShipment cascade
  behavior, and add a fail-closed fallback or version gate for backlogit
  versions where a claim leaves members `queued`.

## Residual Risks

* The cascade close rewrote each released task's `commit` field to the merge
  SHA. The original per-task commits remain in git history.
* P-002.7 describes observed backlogit claim behavior. Version drift is
  tracked by `62C1E11E`.
* This shipment does not deliver detection of P-002.7 divergence in consuming
  workspaces by verify-workspace. That work is deferred to `E770139B`.

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this artifact was
created.

* **Assessment**: `docs/memory` exceeds the generic thresholds in aggregate.
* **Candidates**: selection was bounded to this release unit (Tier-1). The
  session memory and the completed Stage memory
  `2026-09-19/177-s-rollout-d2-conformance-remediation.md` were consolidated
  into
  `docs/memory/compacted/2026-09-29-ship-177-s-169-f-full-lifecycle-compacted.md`.
  The verbose originals moved to `docs/archive/memory/`.
* **Excluded**:
  * `docs/memory/2026-09-19/stage-177-s-n1-n2-mechanization.md` is
    summarized but kept in place because a live Stage memory references it.
  * Plans were not consolidated into a decided-plan, because creating or
    modifying plan artifacts is outside Ship's role boundary (P-010).
  * Other closure records are not past `threshold_days` or belong to other
    release units.
