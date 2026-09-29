---
shipment: 190-S
feature: 184-F
pr: 464
merge_commit: ef661e90edc1d32ceadd5ba120b337ee01f7131d
reviewed_head: 934cbfe5aa7fd85eefb3daf7919ade0cbcae0789
date: 2026-09-29
closure_status: READY_WITH_CONDITIONS
conditions:
  - id: operator-approved-deviation-034-DL
    description: "034-DL archived standalone under explicit operator approval (option 1) after the backlogit 1.11.0 cascade left it live"
    satisfied: true
    evidence: ".backlogit/reconcile/190-S-cascade-close-20260929-061541.md#operator-approved-deviation--standalone-archival-of-034-dl-resolution"
  - id: contract-alignment-followup-captured
    description: "shipment-reconcile / P-015 vs backlogit 1.11.0 cascade mismatch captured for Stage deliberation"
    satisfied: true
    evidence: "stash 8FEE91F4"
compaction_status: done
---

# 190-S / 184-F Post-Merge Closure: Windows Temp-Directory Teardown Repair (test-only)

## Summary

Shipment 190-S (SHIP-24, `dag-root`; feature 184-F; manifest task
184.001-T) merged through PR #464 as merge commit `ef661e90`, using `--merge`
with two parents (`7d75dd1c`, `934cbfe5`). The reviewed HEAD was `934cbfe5`.

The authorized change is a bounded retry at the `_run()` temp-workspace
teardown in `tests/test_capability_pack_enforcement_verifier.py`. It catches
`PermissionError` with `winerror` 32 or 5, retries 3 times with a 0.25 s
backoff, and re-raises on the final attempt. That change landed earlier on
`main` as `6ce8bfc3` via PR #457, as prerequisite unblocking work for the
PR #457 Push B canonical-suite gate. PR #464 therefore carried only lifecycle
commits: `abd9104e` (claim) and `934cbfe5` (complete 184.001-T and track
`6ce8bfc3`).

## Gates and Dark-Mode Record (P-017)

| Gate | Result |
|---|---|
| Local review | `READY`, P0=0, P1=0, at `934cbfe5` |
| Full local build | Not applicable (backlog-only PR). The canonical suite `PYTHONPATH=src python -m unittest discover -s tests` still ran at HEAD: 2469 tests OK (54 skipped) |
| Task verification order | Exact test OK. Cross-module runs with `tests/test_graphtor_mcp_shim.py` passed 27/27 in both orderings. No lingering processes or temp dirs, so the 8CB606F8 stop condition did not trigger |
| Required CI | ci gate, detect code changes, and pipeline-topology (ambient) passed. `test` was skipped because no code changed |
| P-009 merge strategy | Merge commit, two parents verified |
| P-016 worktree topology | Single worktree |
| Merge authority | `DARK_MODE_ACTIVE`. Admin fallback was not used (`admin_fallback_pre_authorized=false`) |

## Validator Evidence / Runtime Verification

This shipment adds no runtime service surface. It changes one test module's
teardown path only. No `src/` change was made, which the task prohibited. The
unit suite and the task's four-step verification order verify it. No runtime
validator probes apply.

## Closure Path

`shipment-reconcile` classified 190-S as `CASCADE` under P-015. Root feature
184-F has no out-of-manifest descendants. Step 0(c) found one validated linked
deliberation, `034-DL`. It is linked from the 184-F description, and it was
`queue`/`queued` before the close. The skill therefore put 034-DL in both
`allowed_ids` and `required_ids`.

The evidence was captured contemporaneously: the Step 0 snapshot, a fresh
pre-invocation revalidation with no drift, the baseline fingerprint (an empty
set), and the raw `backlogit shipment ship` stdout (backlogit 1.11.0, exit 0).

The cascade archived `[184.001-T, 184-F, 190-S]` with `returned_ids: []`. It
did **not** archive `034-DL`, so `required_ids - archived_ids = [034-DL]`. The
gate halted fail-closed with a **P-005** event, and nothing was committed.

### Operator-approved deviation

* **Decision**: the operator chose option 1 on 2026-09-28 at 23:29 local:
  "I would go with option 1". This is an explicit, operator-approved deviation
  from the cascade no-substitution rule. Rollback was declined.
* **Action**: `backlogit archive 034-DL` on the closure branch. The result is
  `status: archived` with `archived_status: queued`, so the provenance is
  preserved. The body and `custom_fields` are unchanged.
* **Recomputed postcondition**: the archived set is
  `{034-DL, 184-F, 184.001-T, 190-S}`. `archived - allowed_ids = []` and
  `required_ids - archived = []`. `parent_id` is preserved. The shipment
  record is `status: archived` with `archived_status: shipped`.
* **Cause**: an engine/contract mismatch. backlogit commit `5a4b70dd`
  (174.058-T, first released in v1.11.0) removed linked-deliberation archival
  from the cascade. In v1.11.0, `collectArchiveCandidateIDs`
  (`internal/core/shipment_lifecycle.go:716`) leaves linked deliberations
  independent (see the comment at lines 734–735). The shipment-reconcile
  contract still describes the older engine. Stash `8FEE91F4` tracks the
  alignment work.

Report: `.backlogit/reconcile/190-S-cascade-close-20260929-061541.md`
(resolution `CLOSED — operator-approved deviation`). Post-mode:
`.backlogit/reconcile/190-S-post-20260929-070500.md` (`PROCEED`). All
archive files are present, there are no deletions, and a retroactive orphan
scan at `ef661e90` found no orphans. No separate pre-mode report was produced.
Its per-item checks are evidenced by the contemporaneous Step 0 snapshot, and
the disposition is recorded in the post-mode report.

## Source Artifact Cleanup

* 184-F `custom_fields.source_stash_id`: `none`, because 184-F declares no
  such field. Its traceability names source stash `78548873`, which Stage
  archived at harvest on 2026-09-20, so it was skipped as already archived.
* 184-F `custom_fields.source_deliberation_id`: `none`, because 184-F
  declares no such field.
* Deliberation `034-DL` is linked from the 184-F description, not through
  `source_deliberation_id`. The shipment-reconcile Step 0(c) validated it as a
  linked deliberation, and it was archived standalone under the
  operator-approved deviation above.
* 184-F and 184.001-T are archived with `archived_status: done`. 190-S is
  archived with `archived_status: shipped`.
* The related stash entries `8CB606F8` and `AD0F128D` stay active and were
  not touched, as the task scope required.
* Ship made no change to plan, review, spike, or decision artifacts, which
  are Stage-owned (P-010). That includes
  `docs/decisions/2026-09-20-windows-temp-cleanup-teardown-defect-deliberation.md`.

## Releasability Evidence

* **Status**: READY_WITH_CONDITIONS.
  * The shipped change is releasable.
  * One condition: the closure path needed an operator-approved deviation.
    Until `8FEE91F4` is resolved, any future `CASCADE` close whose feature
    links a live deliberation will halt the same way under backlogit 1.11.0 or
    later.
* **Monitoring**: the CI `test` job and local canonical-suite runs on
  Windows. The teardown retry should absorb transient WinError 32/5.
* **Healthy signals**: the canonical suite passes on Windows, with no
  `PermissionError` from `TemporaryDirectory` teardown in this module.
* **Failure signals**:
  * a persistent `PermissionError` re-raised after 3 attempts, which means a
    real handle leak (possibly `8CB606F8`)
  * leftover temp dirs after suite runs
* **Rollback trigger**: the retry masks a real regression, or it causes
  suite instability.
* **Rollback procedure**: revert `6ce8bfc3`, the test-only change. The merge
  commit `ef661e90` carried backlog lifecycle state only.
* **Owner**: operator (softwaresalt). The Ship agent owns closure mechanics.
* **Validation window**: through the 189-S / PR #457 Push B canonical-suite
  gate.

## Follow-Up Items

These are Ship follow-up captures. Stage owns triage.

* `8FEE91F4` (bug/high, requires deliberation): align the shipment-reconcile
  and P-015 `CASCADE` contract with backlogit 1.11.0 cascade archival
  behavior. The engine no longer archives description-linked deliberations.
* `8CB606F8` (existing, medium): the Graphtor shim `tearDown` resource leak.
  It stays deferred and untouched.

## Residual Risks

* The cascade close rewrote the released task's `commit` field to the merge
  SHA. The original implementing commit `6ce8bfc3` remains in git history and
  in the task log.
* `034-DL` records `archived_status: queued`, not `done`. That is its true
  pre-archive status. Archiving it standalone is a one-off deviation, not
  sanctioned contract behavior, until `8FEE91F4` is deliberated.

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this artifact was
created.

* **Assessment**: `docs/memory` exceeds the generic thresholds in aggregate.
* **Candidates**: selection was bounded to this release unit (Tier-1). The
  session memory and the completed Stage memory
  `2026-09-20/stage-windows-temp-cleanup-defect.md` were consolidated into
  `docs/memory/compacted/2026-09-29-ship-190-s-184-f-full-lifecycle-compacted.md`.
  The only remaining reference to the Stage memory is a resolved Stage
  checkpoint. The verbose originals moved to `docs/archive/memory/`.
* **Excluded**:
  * the other `2026-09-20` memories, which belong to 183-F, 187-S, 188-S,
    189-S, and PR #457 (other release units, and 189-S is out of scope)
  * plans, because consolidating them into decided-plans is Stage-owned
    (P-010)
  * closure records that are not past `threshold_days`
