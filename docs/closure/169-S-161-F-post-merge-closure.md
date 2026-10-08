---
shipment: 169-S
feature: 161-F
pr: 506
prs: [506]
merge_commit: 489e7c3ba7db238f57815fb18cc41541564caaa3
reviewed_head: c2e6b48e
date: 2026-10-08
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/169-S-161-F-close-evidence.json
---

# 169-S / 161-F Post-Merge Closure: Shipment-Reconcile Pre-Mode Member-Class Status Contract (Option A)

## Summary

Shipment 169-S (SHIP-11) completes feature 161-F, the Option A fix for stash
bug `15A02E21` decided in
`docs/decisions/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation.md`
and planned in
`docs/plans/2026-09-07-shipment-reconcile-cascade-premode-member-class-contract-plan.md`.
Before this change, `shipment-reconcile` Pre-Mode compared every manifest member
with one scalar `expected_status`, so a classifier-verified `CASCADE` manifest,
whose qualifying root feature is validly `active` until the cascade archives it,
always halted. The merged contract:

* adds the single authoritative **Member-Class Status Contract** block: a
  `qualifying-feature` row (`active`/`done` matched, `archived` tolerated and
  reported as `qualifying-feature-pre-archived-anomaly`, anything else a HALT)
  and a `strict-scalar` row (the old single-`expected_status` semantics);
* reads declared frontmatter `status` regardless of `queue/`/`archive/`
  location (R-1), and makes every unlisted value an explicit
  `status-mismatch` HALT (R-5);
* adds Pre-Mode step 2b (advisory, in-process classification on the pre-close
  invocation only), the `RECONCILE_FAIL_PREMODE_CLASSIFIER_CONTRACT` halt, and
  the Step 0(c) agreement check (`RECONCILE_FAIL_PREMODE_CLASSIFIER_DRIFT`);
* updates the Ship agent pointer (installed and template) and adds contract,
  regression and single-source parity tests. No Python source changed.

`161.007-T` (diagram currency) was disposed not-applicable in-repo: its target,
`docs/diagrams/05-shipment-reconcile-cascade-premode.mmd`, is untracked operator
WIP in `git stash@{1}`; the delta is follow-up `675EA40E`.

**PR #506** (`fix(shipment-reconcile): Pre-Mode member-class status contract for
cascade closures (169-S, 161-F)`) merged as `489e7c3b` at
`2026-10-08T04:48:32Z`, using `--merge` (two parents: `364f3aad`, `c2e6b48e`).
The reviewed HEAD was `c2e6b48e`. The PR ran under dark mode (P-017).

## Gates

| Gate | Result |
|---|---|
| Startup (closure) | **Tools:** backlogit 1.11.0 CLI (MCP not exposed); `backlogit sync` on the closure branch, `Indexed 1755 artifacts`. Intercom, engram and graphtor not exposed (degraded visibility). The global `autoharness` is a stale 1.5.0 without `shipment`, so every `autoharness` command ran the checkout's CLI through a git-ignored `src` wrapper (`C4D5B676`). **Checkpoints:** 101, 0 active, 0 quarantined; no recovery. **P-016:** one worktree |
| Context reload | The merged `main` changed the `shipment-reconcile` skill (this shipment) and `_ship.agent.md` (Step 0.5 scope note and the Step 5 pre-mode pointer). Both were re-read before the close, and the close ran under them |
| Local review (P-014) | 10 personas over three review-fix cycles plus a confirmation pass; focused re-reviews of every Copilot fix commit. `READY_WITH_FOLLOWUPS` at `c2e6b48e`, P0=0, P1=0 |
| Full local build | `PYTHONPATH=src python -m unittest discover -s tests` -> `Ran 3476 tests ... OK (skipped=57)` at `c2e6b48e` through the pre-push hook, with the temp reroute. One timing-sensitive failure in `test_shipment_cascade_close_invoke` (2 s probe timeout) was seen once at `a5e571a5` and passed on rerun |
| Copilot review (P-018) | Six rounds; see **Copilot Review Rounds** below. Round 6 on `c2e6b48e` was clean. `autoharness gate copilot-review 506 --enforcement auto` returned PASS for the reviewed HEAD |
| CI | Every check passed at `c2e6b48e`: `detect code changes`, `pipeline-topology (ambient)`, `test` and `ci gate` |
| P-009 / P-016 | The repository allows only merge commits; the merge commit has two parents. One worktree |
| Pre-close topology | `pipeline-topology --phase lifecycle` exited 0 on the closure branch before the close (`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`, `WORKTREE_TOPOLOGY_OK`, predecessor `159-S`, `explicit`) |
| Merge confirmation | `MERGE_CONFIRMED`: PR #506 merged at 2026-10-08T04:48:32Z as SHA `489e7c3b`, an ancestor of `origin/main` |
| Dark-mode merge authorization (P-017) | Source: the activation record (`merge_approval_pre_authorized`). Strategy `--merge`. No admin fallback (`admin_fallback_pre_authorized` false) |
| Closure-evidence gate | `autoharness gate closure-evidence --path docs/closure/169-S-161-F-post-merge-closure.md --shipment 169-S`: while compaction was pending, only `frontmatter_predicate` failed; after compaction it exited 0 |
| Index resync | `backlogit sync` after the close, the stash captures and compaction: `CLOSURE_INDEX_SYNC_OK` |

## Copilot Review Rounds

| Round | Reviewed HEAD | Findings | Disposition |
|---|---|---|---|
| 1 | `84bd37aa` | 1 inline comment (1 thread): defer recording the agreement-check outcome until the check runs | Fixed in `fb68e399`; reply cites the fix; thread resolved |
| 2 | `fb68e399` | 0 threads; review body "Previously missed (1)": a stale `active` Phase-A checkpoint | Fixed in `b879a045` (superseded checkpoint resolved); PR comment cites the fix |
| 3 | `b879a045` | 0 threads; "Previously missed (1)": a duplicate member-class row silently overwrote the first in the test reader | Fixed in `24d5fc13` (reject duplicates, regression test, RED captured) |
| 4 | `24d5fc13` | 0 threads; "Previously missed (1)": a fixture did not isolate the same-directory duplicate | Valid and in scope, raised after the three-cycle limit: Ship held the merge for an operator decision; the operator authorized a cycle extension (recorded in a PR comment); fixed in `0b2c0bc5` |
| 5 | `a5e571a5` | 0 threads; "Previously missed (1)": a sentence overstated the Safe-Close step 4 guarantee | Fixed in `c2e6b48e` (qualified in both skill copies; the step 4 algorithm stays deferred as `D16452D7`) |
| 6 | `c2e6b48e` | 0 threads, 0 open findings, no "Previously missed" section | Clean; merge presented |

Every round's headline read "0 open findings" from round 2 on, and the P-018
gate passed each round, because review-body findings carry no thread. The
learning is `docs/compound/2026-10-08-copilot-review-body-findings-without-threads.md`
and the gate gap is follow-up `38D29192`. Copilot's overview line ("needs a
closer look ... human validation") was recorded each round; the operator's P-017
pre-authorization is the human sign-off.

## Validator Evidence / Runtime Verification

There is no runtime surface: the change is a skill contract, the Ship agent
pointer and tests. The live validation is this closure itself, the first
pre-close Pre-Mode run under the new contract on a `CASCADE` manifest:

* Pre-Mode (`expected_status: done`) returned `PROCEED`, with step 2b verdict
  `CASCADE` and qualifying set `[161-F]`. `161-F` (`queue`, declared `active`)
  matched under the `qualifying-feature` row; the seven tasks (`archive`,
  declared `done`) matched under the `strict-scalar` row by declared status, not
  location. Under the old single-scalar Pre-Mode, `161-F` would have been a
  `status-mismatch` HALT.
* The Step 0(c) agreement check compared the classify-only record's
  `pre_close.classifier_verdict` / `qualifying_feature_ids` (`CASCADE`,
  `[161-F]`) with that Pre-Mode report: **agreement-check outcome `agreed`**.
* Verdict: `PASS`.

## Closure Path

`close_path: cascade`. The `close_evidence` record is
`docs/closure/evidence/169-S-161-F-close-evidence.json` (phase `post_close`,
run `357f5eded7184c8a9cf436a6b960da07`, `merge_commit_sha` `489e7c3b…`).

* **Lock.** `.backlogit/queue/169-S.md` was held from pre-mode
  (`2026-10-08T05:01:11Z`) through post-mode (released `05:21:54Z`). The whole
  locked sequence ran in one supervised process so the lock token was never
  written to disk.
* **Classification.** Classify-only returned `CASCADE` with qualifying root
  `161-F`, no out-of-manifest descendants and engine `VERIFIED` (backlogit
  1.11.0, commit `131577c`, CLI surface).
* **Agreement check (Step 0(c)).** `agreed`.
* **Timeout.** N = 9, so B = 672 s; the default `--timeout` (1800 s) applied.
  The `backlogit shipment ship` child ran 1153 s (05:02:17Z to 05:21:30Z),
  about 1.7 × B; see **Residual Risks**. The run was supervised attached until
  the command exited 0 at 05:21:45Z.
* **Approval.** The operator's dark-mode instruction for 169-S directed closure
  with the classifier-selected close path (P-015).
* **Postconditions:**
  * `archived_ids` = `required_ids` = `allowed_ids` = {`161-F`, `161.001-T` to
    `161.007-T`, `169-S`}
  * `returned_ids` `[]`
  * `parent_id_preserved`, `baseline_invariant` and
    `disposition_byte_identical` are all `true`
  * the shipment is `status: archived`, `archived_status: shipped`; the merge
    commit is tracked on `169-S` (`commit_tracked`, `489e7c3b`)
* **Commit.** `8c751c02`.

Reports:

* Pre-mode: `.backlogit/reconcile/169-S-pre-20261008-050122.md` (`PROCEED`)
* Cascade close and disposition:
  `.backlogit/reconcile/169-S-cascade-close-20261008-052145.md` (`CLOSED`,
  `DISPOSITION_COMPLETE`)
* Post-mode: `.backlogit/reconcile/169-S-post-20261008-052154.md` (`PROCEED`)

## Linked-Deliberation Disposition (P-015 INV-12)

The planner snapshot was empty, and `linked_deliberation_drift` is `[]`. No
deliberation was mutated. **`recommendation: DISPOSITION_COMPLETE`**.

## Source Artifact Cleanup

| Item | Field | Value | Outcome |
|---|---|---|---|
| `161-F` | `source_stash_id` | (absent) | `none` |
| `161-F` | `source_deliberation_id` | (absent) | `none` |

`161-F` declares neither field. The stash entry its plan and decision record
name, `15A02E21`, is already in `.backlogit/archive/stash.jsonl` (archived by
Stage at harvest), so no retirement was needed. Record bookkeeping that
`161.007-T`'s review narrowing assigned to closure:

* **Bug record**
  `docs/bugs/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-mismatch.md`:
  `status` set to fixed in 169-S, with `fixed_date` and `fixed_in` (shipment,
  feature, PR, merge commit, this artifact).
* **Decision record**
  `docs/decisions/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation.md`:
  not modified. It is a deliberation artifact, which Ship may not modify
  (P-010); its stale `harvested_shipment_status` is follow-up `16128302` for
  Stage.

## Releasability Evidence

* **Status.** `READY`. There is no tag, publish or release-record obligation.
* **Invariants to preserve.** Intake (`queued`/`active`) Pre-Mode stays
  strict-scalar for every member; any declared status outside a row's cells
  halts; Step 0(c) stays authoritative for the close path.
* **Healthy signals.** The next `CASCADE` closure's pre-close Pre-Mode passes an
  `active` qualifying feature, and the agreement check reports `agreed`.
* **Failure signals.** A `RECONCILE_FAIL_PREMODE_CLASSIFIER_CONTRACT` or
  `RECONCILE_FAIL_PREMODE_CLASSIFIER_DRIFT` halt on a manifest the classifier
  and the Pre-Mode report agree on, or an intake run accepting a mixed manifest.
* **Monitoring.** The next two shipment closures' Pre-Mode reports.
* **Rollback.** Revert merge `489e7c3b` (`git revert -m 1`) with operator
  approval; no data migration is involved.
* **Owner and validation window.** Ship owns rollback, with operator approval,
  through the next two shipment closures.

## Follow-Up Items

From the shipment (P-021 deferred, recorded in PR #506):

* `675EA40E`: diagram 05 delta, for when the operator publishes the diagram
  set. Needs deliberation.
* `D16452D7`: Safe-Close step 4 still keys its `pre-archived` skip on location
  (pre-existing).
* `814BB949`: hard-coded status literals in the template.
* `F0F8916F`: an explicit invocation discriminator for `mode: pre`.
* `A9BABC8B`: re-ground 171-S/163-F plan anchors before it runs.
* `B5AB7D95`: reciprocal cross-references to P-002.7.
* `D6502107`: a declared input channel for the agreement check.
* `E1E31E6A`: generic-template wording defects.

From this closure:

* `4CB6A1E0`: the cascade-close timeout sizing reference underestimates this
  host. Needs deliberation.
* `16128302`: decision-record status bookkeeping (Stage).
* `38D29192`: the copilot-review gate and loop do not see review-body findings.
  Needs deliberation.

All eleven IDs were confirmed present in `.backlogit/stash.jsonl`.

## Residual Risks

* **Cascade timeout margin.** The child took 1153 s for N = 9 against a sizing
  of B = 672 s; only the 1800 s default floor kept it inside the timeout. At
  this host's rate a closure with N ≥ ~15 could time out mid-cascade (exit 6)
  while B still says the default suffices (`4CB6A1E0`).
* **Review-body findings.** The P-018 gate passes a current-HEAD review whose
  body carries a "Previously missed" finding (`38D29192`); until that changes,
  Ship must read review bodies by hand.
* **Location-keyed step 4 skip.** An `archive/`-resident qualifying feature
  that declares `active`/`done` passes Pre-Mode but is skipped by Safe-Close
  step 4 when the engine gate selects `SAFE_CLOSE` (`D16452D7`, documented in
  the contract).
* **Flaky probe timeout.** `test_shipment_cascade_close_invoke`'s re-probe
  drift row uses a 2 s subprocess timeout and failed once under load.

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this closure's
session memory was written.

* **Assessment.** `docs/memory` held 187 files (about 1340 KB), above the
  generic thresholds in aggregate.
* **Candidates.** This was the bounded, per-merge Tier-1 pass: the P-020 floor
  for the release unit just closed. The single 169-S session memory was
  consolidated into
  `docs/memory/compacted/2026-10-08-ship-169-s-161-f-full-lifecycle-compacted.md`;
  the verbose original is
  `docs/archive/memory/2026-10-08-ship-169-s-161-f-session.md`.
* **Not processed in this run:**
  * **Other release units' memories.** They are not owned by this shipment
    (P-021 C1).
  * **Closure records.** They serve as predecessor-closure evidence at their
    canonical paths.
  * **Plans.** Stage owns plans (P-010); the 161-F plan is not consolidated by
    Ship.
* **Checkpoints.** This closure session created no checkpoint; none is active
  (101 total, 0 active).
* **Report.** 1 file compacted and 1 compacted summary written; 0 plans
  consolidated; 0 closure records compacted; nothing deleted.

The closure-evidence gate failed only `frontmatter_predicate` while compaction
was `pending`, and exited 0 after compaction was finalized to `done`.
