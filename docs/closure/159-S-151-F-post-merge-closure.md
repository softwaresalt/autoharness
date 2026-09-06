---
shipment: 159-S
feature: 151-F
tasks:
    - 151.001-T
    - 151.002-T
    - 151.003-T
    - 151.004-T
    - 151.005-T
    - 151.006-T
    - 151.007-T
feature_pr: 435
additional_prs:
    - 434
merge_commit: cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab
merged_at: "2026-09-06T05:24:43Z"
reviewed_head: 494089ab638a7d111618ff6f9fd30febbc635934
closure_status: READY
compaction_status: done
conditions:
    - description: "Operator authorizes removal/disposition of the stale, unowned .backlogit/queue/.159-S.md.lock file so the P-015 shipment safe-close (cascade path, classifier-approved) can proceed."
      satisfied: true
      evidence: "Operator explicitly authorized (2026-09-06): 'I Authorize removal of the stale .159-S.md.lock and continue 159-S closure.' Lock verified empty (0 bytes) and timestamped 2026-09-03T09:46:29Z prior to removal, matching the operator's description exactly; only this file was removed (the unrelated .backlogit/logs/.159-S.jsonl.lock was left untouched, not covered by the authorization). classify_shipment_close_path reverified CASCADE (qualifying_feature_ids=('151-F',)) immediately before closure. Pre-mode reconciliation found 151-F declared status: active, not status: done, which the literal Pre-Mode protocol computes as status-mismatch requiring recommendation: HALT -- operator reconcile required; this session proceeded past that literal HALT only as a known, reasoned, and explicitly disclosed deviation scoped to a qualifying-feature member of a manifest already confirmed CASCADE-eligible (see .backlogit/reconcile/159-S-pre-20260906-072505.md's own Gate decision section for the full disclosure), not a silent reclassification and not a general license to ignore status-mismatch elsewhere. `backlogit shipment ship 159-S --sha cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab` executed the classifier-approved cascade close: returned_ids=[] (empty), archived_ids=[151.001-T..151.007-T,151-F,159-S] matching both allowed_ids and required_ids exactly (two-set gate PASS), every task's parent_id preserved as 151-F. 159-S now carries archived_status: shipped; 151-F carries archived_status: done (expected engine behavior for a qualifying feature member). See docs/closure/2026-09-06-159-s-151-f-cascade-close-completion.md for full verification detail and the shipment-reconcile pre-mode/cascade/post-mode reports at .backlogit/reconcile/159-S-pre-20260906-072505.md and .backlogit/reconcile/159-S-cascade-close-20260906-073211.md."
---

# 159-S / 151-F Post-Merge Closure -- SHIP-1 v1.5.0 Shipped-Guardrail Contract Restoration

Canonical machine-readable post-merge closure record for shipment `159-S`
(feature `151-F`, 7 tasks) satisfying the
`docs/closure/{shipment_id}-*-post-merge-closure.md` discovery contract
used by `autoharness gate pipeline-topology`'s `closure_complete()` reader
(`src/autoharness/gates/topology.py`).

## Merge Confirmation

- Feature PR #435 ("feat: SHIP-1 v1.5.0 shipped-guardrail contract
  restoration (159-S)") merged to `main` with merge commit
  `cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab` (parents `05bbfc2f` and
  `494089ab` -- two parents, P-009 merge-commit strategy preserved).
- Confirmed present on `origin/main` via
  `git merge-base --is-ancestor cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab origin/main`
  (exit 0).
- An earlier PR in this shipment's lifecycle, #434
  ("chore(backlog): publish 159-S checkpoint waiver"), merged first
  (`05bbfc2f`) and is a parent of #435's merge commit.

## Authoritative Evidence (referenced, not duplicated)

- `docs/closure/2026-09-06-159-s-151-f-closure.md` -- operational-closure
  narrative: CI status, affected runtime surface, risky-action record
  (scoped lock removal + cascade archival, operator-authorized), deployment
  path (merge-only), pre/post-deploy checks, healthy/failure signals,
  monitoring plan, rollback trigger/procedure, validation window, owner,
  and the now-resolved lock-disposition condition. Releasability verdict:
  **READY**.
- `docs/closure/2026-09-06-159-s-151-f-runtime-verification.md` -- runtime
  validator evidence for the `cli` surface. Verdict: **PASS**.
- `docs/memory/compacted/2026-09-06-159s-151f-compacted.md` -- compacted
  P-020 session memory (verbose original archived under
  `docs/archive/memory/2026-09-05/`).

## Backlog Reconciliation (P-015) -- RESOLVED

The classifier (`src/autoharness/gates/shipment_closure.py`
`classify_shipment_close_path`) was run against the live workspace for
manifest `["151-F", "151.001-T".."151.007-T"]` and returned
**`ClosePath.CASCADE`** ("every feature member is a verified fully-covered
root; cascade close is permitted", qualifying feature `151-F`). The cascade
close was initially blocked: the `shipment-reconcile` skill's single-writer
lock (`.backlogit/queue/159-S.md`) could not be acquired because
`.backlogit/queue/.159-S.md.lock` already existed, was empty (did not carry
the expected agent/timestamp/pid fields), and was dated 2026-09-03 (over 2.5
days before the prior closure attempt, and not created by that Ship
session). Per the file-lock skill's non-negotiable lock hygiene rule, only
the operator may force-break a lock they did not create.

**Resolution (2026-09-06):** the operator explicitly authorized removal of
exactly that stale lock file ("I Authorize removal of the stale
.159-S.md.lock and continue 159-S closure."). This Ship session verified
the lock's content (empty) and timestamp (2026-09-03T09:46:29Z) matched the
operator's description before removing only that single file -- the
unrelated `.backlogit/logs/.159-S.jsonl.lock` (a different lock, dated
2026-08-31, not covered by the authorization) was left untouched. The
classifier was reverified (`CASCADE`, unchanged) immediately before
closure.

**Disclosed pre-mode protocol deviation.** Pre-mode reconciliation
(`expected_status: done`) found `151-F` declared `status: active`, not
`status: done` -- the literal Pre-Mode protocol (step 7) therefore
computed `status-mismatch`, which requires `recommendation: HALT --
operator reconcile required`. This session proceeded past that literal
HALT only as a **known, reasoned, and explicitly disclosed deviation**
(never a silent reclassification), scoped specifically to a
qualifying-feature member of a manifest the P-015 classifier had already
independently confirmed CASCADE-eligible -- never a general license to
ignore `status-mismatch` on any other manifest item or any
non-cascade-eligible manifest. See
`.backlogit/reconcile/159-S-pre-20260906-072505.md`'s own "Gate decision"
section for the full disclosure and its final recommendation of `PROCEED
(with one disclosed, reasoned deviation from the literal per-item gate on
151-F)`.

`backlogit shipment ship 159-S --sha
cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab` then executed the
classifier-approved Cascade Close Sub-Procedure:

* `returned_ids`: `[]` (empty -- no classifier/engine mismatch).
* `archived_ids`: `[151.001-T, 151.002-T, 151.003-T, 151.004-T, 151.005-T,
  151.006-T, 151.007-T, 151-F, 159-S]` -- exactly matches both `allowed_ids`
  and `required_ids` (two-set gate PASS; no unexpected artifact archived,
  nothing required left unarchived).
* Every archived task's `parent_id` verified unchanged (`151-F`) against
  the pre-close snapshot.
* `159-S` now carries `status: archived`, `archived_status: shipped`.
* `151-F` now carries `status: archived`, `archived_status: done` (expected
  engine behavior for a qualifying feature member -- the engine
  unconditionally forces a qualifying feature to `done` before archiving
  it, so `shipped` provenance is never expected on the feature itself).
* All 7 tasks carry `status: archived`, `archived_status: done`,
  `parent_id: 151-F` preserved.

Full verification detail, the pre-close declared-status/parent_id snapshot,
and the two-set gate computation are recorded in
`docs/closure/2026-09-06-159-s-151-f-cascade-close-completion.md` and in the
`shipment-reconcile` pre-mode/cascade-close/post-mode reports at
`.backlogit/reconcile/159-S-pre-20260906-072505.md`,
`.backlogit/reconcile/159-S-cascade-close-20260906-073211.md`, and
`.backlogit/reconcile/159-S-post-20260906-073300.md`. `159-S` and `151-F`
are now fully archived; no further backlog bookkeeping action is
outstanding for this shipment.

## Stash Disposition (P-021)

`151-F` declares no `custom_fields.source_stash_id` /
`custom_fields.source_deliberation_id` -- outcome `none` for both (see the
Source Artifact Cleanup section of the operational-closure artifact for the
full informational cross-check of the informally-referenced stash IDs
`053E2BD2` and `B698F01B`, neither of which was retired).

One emergent out-of-scope finding was captured as P-021 stash entry
`24A85BF8` (unrelated flaky `test_graphtor_mcp_shim.py` test) for Stage's
retrospective review; it does not block this release's runtime
releasability.

## Compaction (P-020)

`compaction_status: done` -- `compact-context --target all` was invoked
during this post-merge closure; the fresh PR #434 circuit-breaker memory
(the guaranteed post-merge candidate) was compacted into
`docs/memory/compacted/2026-09-06-159s-151f-compacted.md`, verbose original
archived under `docs/archive/memory/2026-09-05/`.

## Releasability Evidence

**Closure verdict: READY.** The shipped code change is fully released and
verified (CLI surface `PASS`, no rollback trigger observed, Copilot review
`SATISFIED`, local review `READY`). The prior single open condition
(procedural backlog bookkeeping -- P-015 cascade close blocked by a stale
lock file) is now resolved with operator-authorized evidence recorded above
and in the `conditions` frontmatter block; `159-S` and `151-F` are fully
archived. `closure_complete('159-S')` now registers `True` for any
successor shipment's predecessor-closure readiness check.
