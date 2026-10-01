# Ship session — 203-S / 197-F post-merge closure (2026-10-01)

## Outcome

* 203-S (195-F slice 2 of 6; covering feature 197-F; manifest `197-F`,
  `197.001-T` … `197.010-T`) delivered by PR #470. The operator approved the
  merge, which landed as merge commit `61e2ffea` (`--merge`, P-009). Final
  reviewed HEAD `b79fe20d`, `READY_WITH_FOLLOWUPS`, P0=0/P1=0. 2563 tests OK.
  CI green. P-018 copilot-review `SATISFIED`.
* Delivered: the rest of U1b (H3 truly-archived referrer rules, stash
  referrers, input safety, read errors, precedence edge cases), the first
  P-015 U2a triple (flat sets, disposition-set admission, INV-1/INV-6,
  engine-semantics CASCADE precondition, SAFE_CLOSE reliance wording), and the
  INV-12 triple with its policy-only assertions.
* Closure ran on `chore/203-s-closure`. The `pipeline-topology` lifecycle
  gate returned exit 0.

## Interim rule A (operator decision 2026-10-01, stash 26D90B0F)

After #470, P-015 is internally inconsistent until slices 3 and 4 merge. The
new flat `allowed_ids(S) = closure_scope(S)` and INV-12 sit beside a Required
Check, Postcondition, item 7, INV-10, P-007 and a `shipment-reconcile` skill
that still add validated linked deliberations to the allowed/required sets.
The operator ruled that the skill stays authoritative for closure execution
until slice 4 (199-F) merges. Ship followed the skill and did not edit the
policy or skill files. A comment recording the decision was appended to stash
entry 26D90B0F (`backlogit comment add`, which writes to the git-ignored local
JSONL log).

The 197-F description's T3 rule predicted a SAFE_CLOSE with
`ENGINE_SEMANTICS_UNVERIFIED`, because the skill cannot record the engine
precondition until slice 3. Under interim rule A the skill classifier governed
instead. Ship also composed the engine gate as advisory evidence:
backlogit 1.11.0 on the CLI surface was `VERIFIED`, and `select_close_path`
returned `CASCADE`. The skill and P-015 therefore agreed, and no tie-break was
needed.

## Close

* Path: `CASCADE`, qualifying root `197-F`, no out-of-manifest descendants,
  no linked deliberations (T2 deliberation-clean).
* The run held the lock, captured a fresh revalidation (no drift), took a
  1503-file whole-tree fingerprint, and invoked `backlogit shipment ship`
  (exit 0, about 7.5 minutes).
* `archived_ids`: 197.001-T … 197.010-T, 197-F, 203-S. `returned_ids: []`.
  Both two-set differences were empty. `parent_id` was preserved. There were
  no out-of-scope tree changes. 203-S is `archived_status: shipped`.
* Reports: `.backlogit/reconcile/203-S-{pre-20261001-174244,cascade-close-20261001-174255,post-20261001-175025}.md`.
* Linked-deliberation disposition: the step is not yet on main (transition
  window), so all are retained. The disposition set is empty under T2.

## Learnings

* A scripted, lock-held run (pre → Step 0 → revalidation → fingerprint →
  cascade → postconditions → post) plus a renderer that builds the reconcile
  reports from `evidence.json` makes the evidence contemporaneous and cheap to
  reproduce. The 202-S script was reused with a few constant changes.
* `backlogit comment add` works on stash IDs, but the comment lands only in
  the git-ignored `.backlogit/logs/`. The closure doc is the durable record.
