---
type: session-memory
agent: ship
shipment: 169-S
feature: 161-F
date: 2026-10-08
mode: dark (P-017)
---

# Ship session: 169-S / 161-F (SHIP-11, shipment-reconcile Pre-Mode member-class status contract)

## Build and PR (2026-10-07 to 2026-10-08T04:48Z, summarized from PR #506)

* Claimed `169-S` (`post_claim` exit 0, intake reconcile `PROCEED`,
  `.backlogit/reconcile/169-S-pre-20261007-232926.md`). Seven tasks
  `161.001-T`..`161.007-T` delivered the Option A contract for stash bug
  `15A02E21`: the Member-Class Status Contract block (R-1 declared status over
  location, R-2 tolerate-and-report `qualifying-feature-pre-archived-anomaly`,
  R-5 explicit HALT for any other value), Pre-Mode step 2b advisory
  classification, the Step 0(c) agreement check
  (`RECONCILE_FAIL_PREMODE_CLASSIFIER_DRIFT`), the classifier contract halt
  (`RECONCILE_FAIL_PREMODE_CLASSIFIER_CONTRACT`), and contract, regression and
  single-source parity tests. No Python source changed.
* `161.007-T` (diagram 05 currency) was disposed not-applicable in-repo: the
  target diagram exists only as operator WIP in `git stash@{1}`; follow-up
  stash `675EA40E`, with a proposed diagram left in the git-ignored
  `.proof-scratch/169-S/`.
* Local review: 10 personas, three review-fix cycles plus a confirmation pass,
  `READY_WITH_FOLLOWUPS`, P0=0, P1=0 at `c2e6b48e`. Full suite 3476 OK
  (skipped=57) at `c2e6b48e` through the pre-push hook with the temp reroute.
* Copilot: six rounds. Round 1 (`84bd37aa`) one thread, fixed `fb68e399`,
  resolved. Rounds 2 to 5 each one review-body "Previously missed" finding with
  no thread, fixed in `b879a045` (stale Phase-A checkpoint resolved),
  `24d5fc13` (duplicate member-class row rejected), `0b2c0bc5` (same-directory
  duplicate fixture isolated) and `c2e6b48e` (SAFE_CLOSE guarantee qualified).
  The round-4 finding arrived after the three-cycle limit; Ship held the merge
  and the operator authorized a cycle extension. Round 6 (`c2e6b48e`) was clean.
* PR #506 merged with `--merge` as `489e7c3b` (parents `364f3aad`,
  `c2e6b48e`) at 2026-10-08T04:48:32Z under the P-017 pre-authorization.
* One timing-sensitive failure was seen once in
  `test_shipment_cascade_close_invoke` (re-probe drift row, 2 s subprocess
  probe timeout); it passed when rerun.

## Post-merge closure (2026-10-08T04:50Z onward)

* Re-read the merged `_ship.agent.md`, `shipment-reconcile`,
  `operational-closure`, `compact-context`, P-015/P-020/P-021/P-014 and the PR
  automation instructions. The merged skill (this shipment's own change)
  governed the close.
* Merge confirmation: `MERGE_CONFIRMED` (state `MERGED`, ancestor of
  `origin/main`). Checkpoints: 101, 0 active, 0 quarantined.
* Branch `post-merge/161-f-shipment-reconcile-premode-member-class-contract`;
  `backlogit sync` (`Indexed 1755 artifacts`); `pipeline-topology --phase
  lifecycle` exit 0 (`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`).
* Lock, Pre-Mode, classify-only, agreement check, mutating cascade-close,
  disposition and post-mode ran in one supervised PowerShell process so the
  lock token stayed in memory (never written to disk):
  * Lock acquired 05:01:11Z.
  * Pre-Mode (`expected_status: done`) `PROCEED` at 05:01:22Z: step 2b
    `CASCADE`, qualifying set `[161-F]`; `161-F` (queue, `active`) matched
    under the `qualifying-feature` row; the seven tasks (archive, `done`)
    matched under `strict-scalar`. The old single-scalar Pre-Mode would have
    halted on `161-F`; the new contract passes it.
  * Classify-only exit 0 at 05:01:43Z; agreement check `agreed`.
  * Mutating cascade-close: N = 9, B = 672 s, default `--timeout` 1800 s.
    The backlogit child ran 05:02:17Z to 05:21:30Z (1153 s, about 1.7 × B);
    command exit 0 at 05:21:45Z, postconditions pass, `returned_ids` `[]`.
  * Disposition `DISPOSITION_COMPLETE` (empty set); post-mode `PROCEED`; lock
    released 05:21:54Z.
* Close commit `8c751c02`. The first attempt committed only the staged
  `169-S` rename because a stale pathspec (`queue/169-S.md`, already moved)
  made `git add` fail; the commit was amended before any push.
* Follow-up captures: `4CB6A1E0` (cascade timeout sizing underestimates this
  host), `16128302` (decision record still says 169-S unrouted; Stage-owned),
  `38D29192` (copilot-review gate does not see review-body findings).
* Bug record
  `docs/bugs/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-mismatch.md`
  marked fixed in 169-S; the decision record was left to Stage (P-010).
* Compound learning:
  `docs/compound/2026-10-08-copilot-review-body-findings-without-threads.md`.

## Learnings

* Copilot's "0 open findings" headline can sit above a "Previously missed"
  finding with no thread; read every review body, not just threads.
* Run the lock-holding close sequence in one process when the runtime cannot
  keep a shell's variables between calls; the token must stay in memory.
* After a cascade moves a record, re-derive pathspecs from `git status`
  instead of reusing the pre-close paths.
