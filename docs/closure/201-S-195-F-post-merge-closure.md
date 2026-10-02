---
shipment: 201-S
feature: 195-F
pr: 479
merge_commit: bf3aaf76738e934cc77718d5d137386c30165ca9
reviewed_head: 4d781f1b
date: 2026-10-02
closure_status: READY
compaction_status: done
---

# 201-S / 195-F Post-Merge Closure: Ship and Operational-Closure Disposition Consumers (195-F slice 6 of 6, terminal)

## Summary

Shipment 201-S is the terminal slice of the 195-F re-split (slice 6 of 6). It
covers the umbrella feature 195-F. Its manifest is `195-F` plus `195.006-T`,
`195.013-T`, `195.012-T`, `195.014-T` … `195.017-T`, `195.007-T`, `195.018-T`,
and `195.019-T`. It merged through PR #479 as merge commit `bf3aaf76`. The
merge used `--merge`, and the final reviewed HEAD was `4d781f1b`.

The slice makes Ship post-merge Step 7 and the operational-closure skill's
"Source artifact cleanup" consume the `linked_deliberation_disposition` report
instead of archiving deliberations themselves. It also adds the closing
negative grep and the compound learnings.

This closure is the first to run the full realigned contract on main. It is
also the live proof of the INV-12 Linked-Deliberation Disposition step for
195-F's linked deliberation `038-DL` (rule 195-F T5). The proof **passed**:
every outcome matches the plan's expectations (see
[Live Proof: Expected vs Actual](#live-proof-expected-vs-actual)).

## Review History

* Local multi-persona review used 9 personas and found no P0 or P1. Its
  P-021 C2 captures were `BCD87392`, `40DCBEBC`, `D79EA53A`, and `73800955`,
  and it reused `3B43CE5A` and `8928EC67`.
* There were 2 Copilot review rounds on PR #479. The 3 threads in cycle 1 were
  fixed in `4d781f1b`, replied to with the fixing SHA, and resolved.

## Gates

| Gate | Result |
|---|---|
| Local review | `READY_WITH_FOLLOWUPS`, P0=0, P1=0, at `4d781f1b` |
| Full local build | `PYTHONPATH=src python -m unittest discover -s tests`: `Ran 2656 tests`, `OK (skipped=54)` at `4d781f1b` |
| Required CI | Green on PR #479 (`test`, `ci gate`, `detect code changes`, `pipeline-topology (ambient)`) |
| P-018 copilot-review | PASS at `4d781f1b` before merge |
| P-009 merge strategy | Merge commit (`--merge`) |
| P-016 worktree topology | Single worktree |
| Merge authority | Dark-mode activation record (P-017), `merge_approval_pre_authorized: true`; no admin fallback (`admin_fallback_pre_authorized: false`) |
| Merge confirmation | `MERGED` at `2026-10-02T19:51:05Z`; `bf3aaf76` is an ancestor of `origin/main` |
| Closure lifecycle topology gate | `autoharness gate pipeline-topology --mode agent --shipment 201-S --phase lifecycle --json`: exit 0 on `chore/201-s-closure` (`BRANCH_OK`; sole active shipment `201-S`) |

## Validator Evidence / Runtime Verification

There is no runtime validator surface. The slice changes agent and skill text,
templates, and tests. The unit suite and the parity tests verify it. This
closure ran the realigned contract against live backlog data, as recorded
below.

## Closure Path

`shipment-reconcile` selected `CASCADE` for 201-S. P-015 agrees.

* **Classifier**: `classify_shipment_close_path` returned `CASCADE`. The
  qualifying root feature is `195-F`, and there are no out-of-manifest
  descendants (`196-F` … `200-F` link to `195-F` with `related_to`, not
  `parent_id`).
* **Engine-semantics gate (Step 0(c))**: the CLI probe
  `backlogit version --no-update-check --format json` returned `version`
  `1.11.0` and `commit` `131577c`. `probe_surface` is `cli`, the same surface
  the close path invokes. So `assess_cascade_engine_semantics` returned
  `VERIFIED` (minor line `1.11`).
* **Selection**: `select_close_path` returned `CASCADE`.
* **Linked-deliberation disposition snapshot**: the read-only
  `compute_linked_deliberation_disposition` covered every manifest member. It
  found `034-DL` and `038-DL`, both linked from `195-F` alone, with no
  unresolved references and no read failures.

The run held the `.backlogit/queue/201-S.md` file lock throughout (acquired
`2026-10-02T19:54:46Z`, released `2026-10-02T20:05:40Z`). It recorded each of
the following as it happened:

* the pre-mode check (`PROCEED`). `195-F` was `active` in the queue, and the
  10 tasks had declared status `done` in the archive (not truly archived).
* the Step 0 snapshot of every member
* a fresh pre-invocation revalidation: classifier, disposition snapshot, and
  an exact-string engine re-probe. There was no drift.
* a baseline fingerprint of 1503 queue and archive records
* the raw output of
  `backlogit shipment ship 201-S --sha bf3aaf76… --message … --author …`
  (backlogit 1.11.0, exit 0, about 9.8 minutes from invocation to
  postcondition evaluation, under the 15-minute circuit-breaker threshold)

The results were:

* `archived_ids`: `195-F`, the 10 tasks, and `201-S`
* `returned_ids`: `[]`
* `allowed_ids` (flat `closure_scope(S)`) and `required_ids` both equal those
  12 IDs.
* `archived_ids - allowed_ids` = `[]` and `required_ids - archived_ids` = `[]`.
* `parent_id` is preserved on all 10 tasks.
* Baseline invariance holds for out-of-manifest descendants (the set is
  empty).
* The disposition snapshot taken after the cascade is byte-identical to the
  Step 0(c) snapshot. The cascade did not touch `034-DL` or `038-DL`.
* The whole-tree fingerprint diff shows changes only on records in
  `allowed_ids`.
* The shipment record has `status: archived` and `archived_status: shipped`.
* The cascade gate returned `recommendation: CLOSED`.

## Linked-Deliberation Disposition (P-015 INV-12)

Ship ran the step exactly as merged at `bf3aaf76`, under the same lock, after
the cascade gate and before post-mode.

* **Plan (step 1)**: the planner ran with the Step 0(c) engine decision and
  the default active stash path. It returned no `planning_error`, and its
  result equals the Step 0(c) snapshot.
* **Disposition baseline (step 2)**: the (i) CASCADE descendant set was
  empty. The (ii) disposition snapshot held `034-DL` and `038-DL`. The (iii)
  baseline captured `git status --porcelain -- .backlogit/` (13 entries, all
  `closure_scope(S)` records the cascade moved or rewrote). It also
  fingerprinted 1724 non-exempt `.backlogit/` paths by location and SHA-256,
  without following reparse points; no path was flagged.
* **Archive and verify (steps 3 and 4)**: there was no planned `archive`, so
  there was no archive call. Ship made no deliberation mutation.
* **Report (step 5)**:

  | id | link_kinds | linking_members | outcome | reason_code | referrers |
  |---|---|---|---|---|---|
  | `034-DL` | `description` | `195-F` | `already-archived` | `already-archived` | — |
  | `038-DL` | `source_deliberation_id`, `description` | `195-F` | `retained_shared_reference` | `retained_shared_reference` | `1263B218`, `8928EC67` |

  The report has no unresolved references or read failures. There was no
  `ENGINE_SEMANTICS_UNVERIFIED` or `ENGINE_LINE_UNVERIFIED_ADVISORY` advisory.
  `stranded_linked_deliberation` is `["038-DL"]`.
* **Gate (step 6)**: the final invariance check ran after the report write.
  It found no fingerprint diff and no porcelain diff, the descendants were
  unchanged, the snapshot was identical, and each snapshot deliberation had
  exactly one outcome. The result was
  **`recommendation: DISPOSITION_COMPLETE`**.

Post-mode then returned `PROCEED`. Every manifest item and the shipment record
are archived, and there were no deletions under `.backlogit/archive/`.

Reports:

* Pre-mode: `.backlogit/reconcile/201-S-pre-20261002-195450.md` (`PROCEED`)
* Cascade close and disposition:
  `.backlogit/reconcile/201-S-cascade-close-20261002-195524.md` (`CLOSED`,
  `DISPOSITION_COMPLETE`)
* Post-mode: `.backlogit/reconcile/201-S-post-20261002-200538.md` (`PROCEED`)

No P-005 event was raised. No operator deviation was needed.

## Live Proof: Expected vs Actual

The expectations come from the plan
(`docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md`, Runtime
Verification and Closure, "Operational closure of `201-S`") and the 195-F
body.

| Expectation | Expected | Actual | Result |
|---|---|---|---|
| Engine-semantics gate | `VERIFIED (1, 11)`; `probe_surface` equals the invocation surface | `VERIFIED`, `1.11.0` / `131577c`, `probe_surface` `cli` = invocation `cli` | Pass |
| Close path | Classifier `CASCADE`; `select_close_path` `CASCADE` | `CASCADE` / `CASCADE` | Pass |
| Disposition-set records across the cascade | Byte-identical | Byte-identical (post-cascade re-collection equals Step 0(c)) | Pass |
| Disposition set source | `195-F` alone (task bodies carry no deliberation IDs) | `linking_members` = `195-F` for both entries | Pass |
| `034-DL` (description mention; already archived) | `already-archived` | `already-archived` | Pass |
| `038-DL` (`source_deliberation_id`) | `retained_shared_reference` while active stash entries cite it (`8928EC67` and the 2026-09-29 follow-up entries), found through the default `stash_path`; otherwise `archived` with `archived_status: queued` | `retained_shared_reference`, referrers `1263B218` (2026-09-29 follow-up) and `8928EC67`, from the default active stash | Pass |
| `019-DL`, `027-DL` | Outside the disposition set (or `already-archived`) | Outside the disposition set | Pass |
| Other mention-only deliberations | `retained_description_mention` | None present | Pass (none) |
| Operational-closure source cleanup | Copies the `038-DL` outcome from the report; no second archiver | Copied below; Ship did not archive `038-DL` | Pass |

Every actual outcome is in the plan's list, and there was no halt.

## Closure Index Resync

`CLOSURE_INDEX_SYNC_OK`. Ship ran `backlogit sync` (the CLI fallback for
`backlogit_sync_index`) after the cascade close and the follow-up stash
capture (`33004C12`), before any closure commit. It exited 0 with
`Indexed 1676 artifacts`. This closure created no checkpoints, so none needed
resolving. A re-run of the P-018 gate on PR #479 at closure returned
`SATISFIED: PASS`.

## Source Artifact Cleanup

Ship post-merge Step 7 ran under the merged contract. The only shipped
top-level item in scope is `195-F`.

| Item | Field | Value | Outcome | reason_code |
|---|---|---|---|---|
| `195-F` | `source_stash_id` | `8FEE91F4` | skipped: already archived (archived `2026-09-29T07:18:34Z`, `reason: harvested`, `harvested_artifact_id: 195-F`) | n/a |
| `195-F` | `source_deliberation_id` | `038-DL` | `retained_shared_reference` (copied from the disposition report; never archived by Ship) | `retained_shared_reference` (copied) |

* No `skipped_not_in_disposition_report` outcome arose. `038-DL` is in the
  report.
* Archived source artifacts: 0 stash entries and 0 deliberations.
* Ship made no change to plan, decision, review, or spike artifacts. Stage
  owns those (P-010).

## Releasability Evidence

* **Status**: READY. The change is limited to agent and skill text,
  templates, and tests.
* **Monitoring**: the CI `test` job and the canonical suite.
* **Healthy signals**: the following hold:
  * the Ship Step 7, operational-closure, and disposition-step test modules
    stay green
  * later closures copy disposition outcomes into "Source artifact cleanup"
    and never archive a retained deliberation
* **Failure signals**: any of the following:
  * a regression in those test modules
  * a closure that archives a `source_deliberation_id` outside the
    disposition step
  * a closure that re-derives an outcome instead of copying it
* **Rollback trigger**: a suite regression attributable to this slice.
* **Rollback procedure**: `git revert -m 1 bf3aaf76`.
* **Owner**: operator (softwaresalt). The Ship agent owns closure mechanics.
* **Validation window**: through the next CASCADE or SAFE_CLOSE closure with a
  linked deliberation.

## Follow-Up Items

All follow-ups are active stash entries. Stage owns triage.

* `33004C12` (new, this closure): retire the stranded `038-DL` once it is no
  longer a shared reference. `195-F` is archived, so no later closure re-runs
  the disposition step for it.
* `BCD87392`: realign the self-hosting dogfood Ship mirror with the template
  (including Step 7).
* `40DCBEBC`: reword the P-010 "Ship MAY" bullet in the workflow policies.
* `D79EA53A`: decide how retained outcomes become follow-ups, and stop
  hard-coding the `retained_*` vocabulary.
* `73800955`: verify the compound learnings against backlogit tag `v1.11.0`.
* `3B43CE5A` (reused): carry the disposition record and advisories through
  the operational-closure skill.
* `8928EC67` (reused): backlogit engine-behavior registry and the
  verify-workspace drift probe.

Carried-over entries from earlier slices stay active and untouched. With
201-S shipped, the 195-F re-split is complete. The next shipment in the
dark-mode scope is `198-S`. It is blocked on `201-S` and waits for its
re-plan (`1263B218`). Its own `blocks` edges and the `pre_claim` topology gate
decide when it can be claimed.

## Residual Risks

* `038-DL` stays live (`queued`) and stranded until `33004C12` is acted on.
  The stash text of `33004C12` itself cites `038-DL`, so while it is active it
  also counts as a referrer. Stage archives it when it acts on it.
* The cascade rewrote each released task's `commit` field to the merge SHA.
  The implementing commits remain in git history.
* The cascade took about 9.8 minutes on 12 artifacts. This is a latency
  observation, not a correctness issue.
* The live proof exercised the `already-archived` and
  `retained_shared_reference` outcomes. The disposition step's archive and
  verify-after-each paths have still not run against live data. The
  scenario-matrix tests cover them.

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this closure's session
memory was written.

* **Assessment**: `docs/memory` holds 175 files (about 1303 KB), which exceeds
  the generic thresholds in aggregate.
* **Candidates**: the run was a bounded Tier-1 pass over this release unit.
  The 201-S session memory was consolidated into
  `docs/memory/compacted/2026-10-02-ship-201-s-195-f-full-lifecycle-compacted.md`.
  The verbose original is at
  `docs/archive/memory/2026-10-02-ship-201-s-195-f-closure-session.md`.
* **Excluded**:
  * `docs/memory/2026-09-29/stage-8fee91f4-backlogit-1-11-cascade-alignment.md`.
    195-F is now complete, so this file is eligible. It is Stage-owned
    planning memory, and five earlier closure records cite its path, so this
    bounded run left it in place for a Stage-run compaction.
  * other release units' memories, which are out of scope for this bounded
    run
  * plans, because Stage owns that work (P-010)
