---
shipment: 198-S
feature: 192-F
pr: 485
prs: [482, 483, 484, 485]
merge_commit: 829ab5e13db9aafd25f21d12f92f4abd2d14a457
feature_merge_commit: eb8b78115c4650e898049920d7f454cb435083dd
reviewed_head: 58cea2f2
date: 2026-10-03
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/198-S-192-F-close-evidence.json
---

# 198-S / 192-F Post-Merge Closure: Cascade-Close Evidence Capture (`autoharness shipment cascade-close`)

## Summary

Shipment 198-S delivers feature 192-F: the evidence-capturing
`autoharness shipment cascade-close` command, the `close_path` and
`close_evidence` closure-artifact keys, and the closure-evidence gate checks
that consume them. Its manifest is `192-F` plus 26 tasks (`192.001-T` ..
`192.026-T`).

Delivery took two merges and one interim halt:

1. **PR #482** (`feat(shipment-close): cascade-close evidence capture
   command`) merged as `eb8b7811` at `2026-10-03T05:10:52Z`. It carried
   `192.001-T` .. `192.022-T`.
2. **First closure attempt: halted before mutation.** The `--classify-only`
   run selected `CASCADE`. Ship then stopped before the mutating run, because
   the predicted `backlogit shipment ship` runtime for 24 artifacts (about
   973–1020 s) exceeded the command's hard 900 s `--timeout` cap. A timeout
   would have killed the engine partway through archiving (exit 6). The
   backlog was not mutated. **PR #483** (merge `7313f9ba`) recorded the halt
   (`.backlogit/reconcile/198-S-cascade-close-20261003-051645.md`), the
   session checkpoint, and the follow-up stash entries, including bug
   `F50BD40F`.
3. **Operator decision: "Fix the cap first. Option 1."** Stage added the
   remediation tasks `192.023-T` .. `192.026-T` to 198-S in **PR #484**
   (merge `938c410c`). The manifest grew from 23 to 27 items.
4. **PR #485** (`fix(shipment-close): raise cascade-close --timeout to
   30-3600 s, default 1800`) merged as `829ab5e1` at `2026-10-03T08:04:23Z`,
   with reviewed HEAD `58cea2f2`. It added the skill's timeout-sizing rule
   (`B = ceil(1.5 * (F + P * N))`) and the `--timeout + 600 s` supervision
   budget with attached async supervision. `F50BD40F` was archived.
5. **This closure** (resumed) ran the full CASCADE close at `829ab5e1`. It
   is the first live end-to-end run of the mutating `cascade-close` command,
   and it exited 0.

## Gates

| Gate | Result |
|---|---|
| Feature PR merges | #482 `eb8b7811` and #485 `829ab5e1`, both `MERGED` by merge commit (P-009); `829ab5e1` has two parents and is an ancestor of `origin/main` |
| Merge authority | Dark-mode activation record (P-017), merges pre-authorized |
| Closure lifecycle topology gate | `autoharness gate pipeline-topology --mode agent --shipment 198-S --phase lifecycle --json`: exit 0 on `chore/198-s-closure-2` (`BRANCH_OK`, sole active shipment `198-S`, predecessor `201-S` explicit) |
| Pre-mode reconcile | `PROCEED` (27 items: `192-F` `active` in queue; 26 tasks `done` in archive; no orphans; `record-consistent`) |
| `--classify-only --replace-pre-close` | Exit 0: `CASCADE`, engine `VERIFIED` (`1.11.0` / `131577c`, cli) |
| Mutating `cascade-close` | Exit 0, `postcondition_verdict: pass`, 1006 s |
| INV-12 disposition | `DISPOSITION_COMPLETE` |
| Post-mode reconcile | `PROCEED` |
| Closure index resync | `CLOSURE_INDEX_SYNC_OK` (`backlogit sync`: `Indexed 1696 artifacts` after the final backlog mutation) |
| Closure-evidence gate | `autoharness gate closure-evidence --path docs/closure/198-S-192-F-post-merge-closure.md --shipment 198-S --json`: exit 0 with `compaction_status: done` (the earlier `pending` run failed only `frontmatter_predicate`, as expected) |
| Full unit suite | See [Verification](#verification) |

## Validator Evidence / Runtime Verification

There is no runtime validator surface. The change is a CLI command, its
evidence record, a gate, skill and agent text, and tests. This closure is the
runtime verification: it ran the shipped command against the live backlog,
as recorded below.

## Closure Path

`close_path: cascade`. `close_evidence`:
`docs/closure/evidence/198-S-192-F-close-evidence.json` (phase `post_close`,
run `63c8a3695be646eaaa70a4f501798144`, `merge_commit_sha` `829ab5e1…`).

* **Lock**: `.backlogit/queue/198-S.md` was held from pre-mode
  (`2026-10-03T08:07:37Z`) through post-mode (released
  `2026-10-03T08:25:52Z`).
* **Stale record replaced**: the `pre_close` record written at `eb8b7811`
  covered 23 items. Under the operator's Option 1 approval, Ship replaced it
  with `--classify-only --replace-pre-close` at `829ab5e1`. Classifier
  `CASCADE`, qualifying root `192-F`, no out-of-manifest descendants.
  Disposition snapshot: `035-DL` and `038-DL`.
* **Timeout sizing**: N = 27 + 1 = 28. B = ceil(1.5 × (133 + 35 × 28)) =
  1670 s, which is at most 1800 s, so Ship used the default `--timeout`
  (1800 s). The supervision budget was 2400 s. The run was started attached,
  in async mode, and polled until it exited.
* **Mutating run**: `autoharness shipment cascade-close --shipment 198-S
  --feature 192-F --sha 829ab5e1… --message "Merge pull request #485 …"
  --author "Derek Williams <…>" --json`. Exit 0. The command took 1006 s;
  the `backlogit shipment ship` child took about 985 s
  (`08:08:46Z` → `08:25:12Z`), with `timed_out: false` and
  `mutation_state: completed`.
* **Postconditions** (from the `post_close` record):
  * `archived_ids`: 28 IDs (`192-F`, the 26 tasks, and `198-S`)
  * `returned_ids`: `[]`
  * `allowed_ids` and `required_ids` are the same 28 IDs
  * `unexpected_archived` and `missing_required` are both `[]`
  * `parent_id_preserved`, `baseline_invariant`, and
    `disposition_byte_identical` are all `true`
  * shipment record `status: archived`, `archived_status: shipped`
* **Whole-tree guard**: Ship fingerprinted 1521 queue and archive records
  plus both stash files before the run. Only the 30 `closure_scope(S)` paths
  changed (28 archive records plus the `192-F` and `198-S` queue copies).
* Cascade gate: **`CLOSED`**. No P-005 event. Ship made no direct
  `backlogit shipment ship` call and did not substitute `SAFE_CLOSE`.

## Linked-Deliberation Disposition (P-015 INV-12)

The step ran under the same lock, after `CLOSED` and before post-mode, with
all inputs taken from the evidence record. The planner result equals the
`pre_close` snapshot. There was no planned `archive`, so Ship made no
deliberation mutation. The final invariance check found no fingerprint diff
(1746 non-exempt paths) and no porcelain diff.

| id | link_kinds | linking_members | outcome | reason_code | referrers |
|---|---|---|---|---|---|
| `035-DL` | `source_deliberation_id`, `description` | `192-F`, `192.001-T` .. `192.016-T` | `retained_shared_reference` | `retained_shared_reference` | `2A85BA55`, `4DA3BCE6`, `AE33E3E3` |
| `038-DL` | `description` | `192-F`, `192.005-T`, `192.006-T`, `192.008-T`, `192.012-T`, `192.014-T` | `retained_shared_reference` | `retained_shared_reference` | `33004C12`, `8928EC67` |

No unresolved references and no read failures. Neither
`ENGINE_SEMANTICS_UNVERIFIED` nor `ENGINE_LINE_UNVERIFIED_ADVISORY` applies.
`stranded_linked_deliberation`: `["035-DL", "038-DL"]`.
**`recommendation: DISPOSITION_COMPLETE`**.

Reports:

* Pre-mode: `.backlogit/reconcile/198-S-pre-20261003-080737.md` (`PROCEED`)
* Cascade close and disposition:
  `.backlogit/reconcile/198-S-cascade-close-20261003-080830.md` (`CLOSED`,
  `DISPOSITION_COMPLETE`)
* Post-mode: `.backlogit/reconcile/198-S-post-20261003-082550.md` (`PROCEED`)
* Earlier halt (history): `.backlogit/reconcile/198-S-pre-20261003-051636.md`
  and `.backlogit/reconcile/198-S-cascade-close-20261003-051645.md`

## Source Artifact Cleanup

The only shipped top-level item is `192-F`.

| Item | Field | Value | Outcome | reason_code |
|---|---|---|---|---|
| `192-F` | `source_stash_id` | `008F3BCF` | skipped: already archived (`2026-09-28T03:36:57Z`) | n/a |
| `192-F` | `source_deliberation_id` | `035-DL` | `retained_shared_reference` (copied from the disposition report; Ship did not archive it) | `retained_shared_reference` (copied) |

Archived source artifacts: 0 stash entries and 0 deliberations. Ship made no
change to plan, decision, review, or spike artifacts (P-010).

## Releasability Evidence

* **Status**: READY. The command is already on `main` (#482, #485). This
  closure proves it end to end on live data.
* **Invariants to preserve**: the following must keep holding:
  * a CASCADE close runs only through `autoharness shipment cascade-close`
  * a `--classify-only` run precedes every mutating run
  * exits 2 and 4 mean nothing was mutated; exits 5–8 forbid committing,
    retrying, or substituting `SAFE_CLOSE`
  * the INV-12 disposition step is the only archiver of a linked
    deliberation
* **Deployment path**: merge-only. Consumers get the command in the next
  autoharness release after 1.5.0.
* **Monitoring**: the CI `test` job and the canonical unit suite. Each later
  closure's `close_evidence` record and the closure-evidence gate run.
* **Healthy signals**: the following hold:
  * later closures write a `post_close` record with
    `postcondition_verdict: pass`
  * `invocation.timed_out` stays `false`
  * the closure-evidence gate exits 0 on closure artifacts that carry
    `close_path` and `close_evidence`
* **Failure signals**: any of the following:
  * a `cascade-close` exit 5, 6, 7, or 8
  * an evidence record left at `invoking`
  * a stale pair lock
  * a child runtime that approaches the sized `--timeout`
* **Rollback trigger**: a `cascade-close` defect that corrupts backlog state,
  or a suite regression attributable to 192-F.
* **Rollback procedure**: `git revert -m 1 829ab5e1` (timeout cap) and
  `git revert -m 1 eb8b7811` (command). The backlog state committed by this
  closure stays valid either way. Restoring individual archived records uses
  `backlogit restore`.
* **Owner**: operator (softwaresalt). The Ship agent owns closure mechanics.
* **Validation window**: through the next two CASCADE closures. Watch child
  runtime against B for each.
* **Risky action record**:
  * `--classify-only --replace-pre-close` (overwrites a `pre_close` record):
    ActionRisk medium. Approved through operator Option 1. Result: exit 0.
  * the mutating `cascade-close` (destructive, archives 28 artifacts):
    ActionRisk high. Approved through operator Option 1. Result: exit 0,
    postconditions pass.

## Verification

`$env:PYTHONPATH='src'; python -m unittest discover -s tests` (venv Python) on
the closure branch: result recorded in the closure PR's Local Review
Readiness block.

## Follow-Up Items

All follow-ups are active stash entries. Stage owns triage.

* `A5FA81C4` (new, this closure; task/low): the effective `--timeout` is not
  recorded in the evidence record (no `invocation.timeout_seconds`). This is
  a residual risk from PR #485.
* `E01BA307` (task/low): evidence-record absolute paths, the redaction
  margin, and the `cli.binary` allowlist.
* `320499CC` (task/low): directory fsync on Windows, spawn-failure
  `mutation_state`, exit-code nuances, and probe scratch-dir accumulation.
* `8C88A1DB` (feature/low): the evidence path is fixed to
  `docs/closure/evidence`.
* `9869AA32` (carried over): a stall-detection timeout class for long
  cascades. PR #485 partly addressed it with the cascade-close Stall
  Detection row.

## Residual Risks

* `035-DL` and `038-DL` remain live (`queued`) and stranded. `192-F` is now
  archived, so no later closure re-runs the disposition step for 192-F.
  Their active referrers (`2A85BA55`, `4DA3BCE6`, `AE33E3E3`, `33004C12`,
  and `8928EC67`) keep them retained until Stage acts on those entries.
* The cascade rewrote each task's `commit` field to `829ab5e1`. The
  implementing commits remain in git history (#482 and #485).
* Cascade runtime grows by about 35 s per artifact. With the reference costs,
  a closure scope of 65 or more artifacts gives B > 3600 s, which the skill routes to an operator
  HALT before the run.
* The engine probe scratch directories under
  `.autoharness/gates/cascade-close/probe/` are Git-ignored and were left in
  place (`320499CC`).

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this closure's
session memory was written.

* **Assessment**: `docs/memory` held 178 files (about 1312 KB), which
  exceeds the generic thresholds in aggregate.
* **Candidates**: the run was a bounded Tier-1 pass over this release unit.
  The two 198-S memories (the 2026-10-02 halt checkpoint and the 2026-10-03
  resumed-closure session) were consolidated into
  `docs/memory/compacted/2026-10-03-ship-198-s-192-f-full-lifecycle-compacted.md`.
  The verbose originals are under `docs/archive/memory/`.
* **Excluded**:
  * other release units' memories, which are out of scope for this bounded
    run
  * plans (`docs/plans/2026-09-27-cascade-close-evidence-capture-plan.md`
    and `docs/plans/2026-10-03-cascade-close-timeout-cap-plan.md`), because
    Stage owns that work (P-010)
  * closure records, which are fresh (under `threshold_days`)
