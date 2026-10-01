---
shipment: 203-S
feature: 197-F
pr: 470
merge_commit: 61e2ffea1fcb14582312b0fb57ba97377dc15d26
reviewed_head: b79fe20d
date: 2026-10-01
closure_status: READY
compaction_status: done
---

# 203-S / 197-F Post-Merge Closure: Planner Fail-Closed Hardening, P-015 Flat Sets, Engine-Gate Precondition and INV-12 (195-F slice 2 of 6)

## Summary

Shipment 203-S (195-F slice 2 of 6; covering feature 197-F; manifest
`197-F`, `197.001-T` … `197.010-T`) merged through PR #470 as merge commit
`61e2ffea`. The operator approved the merge, and it used `--merge`. The final
reviewed HEAD was `b79fe20d`.

The slice contains:

* **U1b remainder** in `src/autoharness/gates/shipment_closure.py`: H3
  truly-archived referrer rules, stash referrers and the default stash path,
  input safety, read errors, and precedence edge cases. With these, all eight
  `LinkedDeliberationOutcome` values exist.
* **The first P-015 U2a triple**: flat sets, the disposition-set admission
  paragraph, INV-1/INV-6, the engine-semantics `CASCADE` precondition, and
  `SAFE_CLOSE` reliance wording.
* **The INV-12 triple** (197.009-T) and its policy-only assertions
  (197.010-T).

The planner still has no runtime caller. Slice 5 (206-S) wires it to
mutation.

## Interim Rule A (operator decision)

**Interim rule A per operator decision 2026-10-01, stash 26D90B0F:
shipment-reconcile skill authoritative until slice 4.**

After #470, P-015 is internally inconsistent until 195-F slices 3 and 4 merge.
The new flat `allowed_ids(S) = closure_scope(S)` and INV-12 sit beside parts
that are not yet realigned:

* the Required Check
* the Postcondition
* item 7
* INV-10
* P-007
* the `shipment-reconcile` skill

These parts still add validated linked deliberations to the allowed and
required sets. The operator ruled that
`.github/skills/shipment-reconcile/SKILL.md` remains authoritative for closure
execution until slice 4 (199-F, shipment 205-S) merges. That covers close-path
selection, evidence capture, and the safe-close and cascade procedure. Where
P-015's slice-2 text conflicts, the skill wins.

* Ship followed the skill for this closure. It did not edit the policy or
  skill files.
* A comment recording the decision was appended to stash entry `26D90B0F`
  with `backlogit comment add 26D90B0F --actor ship` (`{"ok": true}`).
  backlogit stores comment events in the git-ignored `.backlogit/logs/`
  JSONL log, so this closure record is the durable, version-controlled copy.
  The stash entry stays active, and Stage owns its triage.
* **Relationship to the 197-F T3 rule.** The T3 transition rule in 197-F
  predicted a `SAFE_CLOSE` with `ENGINE_SEMANTICS_UNVERIFIED`. That
  prediction assumed the skill could not record the engine precondition
  before slice 3. Interim rule A supersedes T3 for close-path selection, so
  the skill's Step 0(c) classifier governed. Ship also composed the slice-1
  engine gate as advisory evidence:
  * `assess_cascade_engine_semantics` on backlogit `1.11.0`, probed and
    invoked on the CLI surface, returned `VERIFIED`.
  * `select_close_path` returned `CASCADE`.

  The skill and the P-015 composition therefore agreed, and the interim rule
  did not have to break a tie.
* **Linked-deliberation disposition.** The step is not yet on main
  (transition window), so all deliberations are retained. Under T2 the
  disposition set is empty, and Ship made no deliberation mutation.

## Gates

| Gate | Result |
|---|---|
| Local review | `READY_WITH_FOLLOWUPS`, P0=0, P1=0, at `b79fe20d` |
| Full local build | 2563 tests OK. `uv run autoharness --help`: exit 0 |
| Required CI | Green at `b79fe20d` |
| P-018 copilot-review | `SATISFIED` at `b79fe20d` |
| P-009 merge strategy | Merge commit (`--merge`) |
| P-016 worktree topology | Single worktree |
| Merge authority | Explicit operator approval (normal mode, no dark mode, no admin fallback) |
| Closure lifecycle topology gate | `uv run autoharness gate pipeline-topology --mode agent --shipment 203-S --phase lifecycle --json`: exit 0 on `chore/203-s-closure` (predecessor `202-S`, explicit) |

## Validator Evidence / Runtime Verification

There is no runtime surface, because nothing calls the planner at runtime and
the policy text changes are documentation. The unit suite and the policy
assertions verify the slice. No runtime validator probes apply.

## Closure Path

`shipment-reconcile` (authoritative under interim rule A) classified 203-S as
`CASCADE` under P-015:

* The qualifying root feature is `197-F`.
* There are no out-of-manifest descendants.
* There are no validated linked deliberations. 197-F is a T2
  "deliberation-clean slice", so the pre-195 and flat
  `allowed_ids`/`required_ids` coincide.

The run held the `.backlogit/queue/203-S.md` file lock throughout (acquired
`17:42:43Z`, released `17:50:27Z`). It captured the Step 0 snapshot, a fresh
pre-invocation revalidation with no drift, and the baseline fingerprint (1503
queue and archive records). It also captured the raw
`backlogit shipment ship 203-S --sha 61e2ffea…` result (backlogit 1.11.0,
exit 0, about 7.5 minutes). All of this evidence is contemporaneous.

* `archived_ids`: `197.001-T` … `197.010-T`, `197-F`, `203-S`
* `returned_ids`: `[]`
* `archived_ids - allowed_ids` = `[]` and `required_ids - archived_ids` = `[]`
* `parent_id` is preserved on all ten tasks.
* The whole-tree fingerprint diff shows changes only on the twelve
  `allowed_ids` records, with no out-of-scope change.
* The shipment record is `status: archived` with `archived_status: shipped`.

Reports:

* Pre-mode: `.backlogit/reconcile/203-S-pre-20261001-174244.md` (`PROCEED`)
* Cascade close: `.backlogit/reconcile/203-S-cascade-close-20261001-174255.md`
  (`CLOSED`)
* Post-mode: `.backlogit/reconcile/203-S-post-20261001-175025.md` (`PROCEED`)

No P-005 event was raised. No operator deviation was needed beyond the
recorded interim rule A.

## Source Artifact Cleanup

* No manifest item declares `custom_fields.source_stash_id` or
  `custom_fields.source_deliberation_id`, so there was no source stash or
  deliberation to retire.
* The umbrella feature `195-F` is linked `related_to`, not through
  `parent_id`. It stays open until slice 6 (201-S), and Ship did not touch it.
* Ship made no change to plan, decision, review, or spike artifacts, which are
  Stage-owned (P-010).

## Releasability Evidence

* **Status**: READY. The planner code has no runtime caller, and the policy
  changes are documentation governed by interim rule A until slice 4.
* **Monitoring**: the CI `test` job and the canonical suite.
* **Healthy signals**: these test modules stay green:
  * `tests/test_linked_deliberation_disposition_planner.py`
  * `tests/test_flat_manifest_closure_docs.py`
  * `tests/test_cascade_engine_semantics_gate.py`
  * `tests/test_shipment_closure_classification.py`
* **Failure signals**:
  * a regression in those modules
  * any runtime caller of `compute_linked_deliberation_disposition` appearing
    before 206-S
  * a closure that follows P-015 slice-2 text over the skill before slice 4
    merges
* **Rollback trigger**: a suite regression attributable to the slice.
* **Rollback procedure**: `git revert -m 1 61e2ffea`.
* **Owner**: operator (softwaresalt). The Ship agent owns closure mechanics.
* **Validation window**: through 205-S (slice 4), which realigns the skill and
  the remaining P-015 sections.

## Follow-Up Items

These P-021 deferred scope expansions and follow-ups stay active. Stage owns
triage:

* `26D90B0F`: remove the interim P-015 contract contradiction between 195-F
  slices. It carries the interim rule A comment.
* `B31435CF`: bound the INV-12 planner's reads (`_read_record`,
  `_scan_stash_referrers`). Captured during 203-S.
* `56566173`: maintainability consolidation of the INV-12 planner and its
  tests. Captured during 203-S.
* `D6CCDE2C`, `3C09D9D0`, `6F2C4BFD`, `013363F5`, `492FB413`: carried over
  from 202-S.

Next shipment: `204-S` (slice 3 of 6, 198-F). It is `queued`, and its only
predecessor, 203-S, has now shipped, so 204-S is eligible to claim.

## Residual Risks

* The cascade rewrote each released task's `commit` field to the merge SHA.
  The implementing commits remain in git history.
* P-015 is internally inconsistent until slice 4 merges. The mitigation is
  interim rule A, recorded here and on `26D90B0F`.
* The cascade took about 7.5 minutes of CPU-bound engine time for 12
  artifacts. This is an operational latency observation, not a correctness
  issue.

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this artifact was
created.

* **Assessment**: `docs/memory` holds 171 files (about 1294 KB), and 103 of
  them are uncompacted (about 935 KB). That exceeds the generic `max_files`
  and `max_size_kb` thresholds in aggregate.
* **Candidates**: selection was bounded to this release unit (Tier-1). The
  203-S session memory was consolidated into
  `docs/memory/compacted/2026-10-01-ship-203-s-197-f-full-lifecycle-compacted.md`,
  and the verbose original moved to
  `docs/archive/memory/2026-10-01-ship-203-s-197-f-closure-session.md`.
* **Excluded**:
  * `docs/memory/2026-09-29/stage-8fee91f4-backlogit-1-11-cascade-alignment.md`,
    because the umbrella 195-F work is still active (slices 3 to 6)
  * other release units' and Stage-owned memories past `threshold_days`, which
    stay out of this bounded Tier-1 run
  * plans, because consolidating them into decided-plans is Stage-owned
    (P-010)
  * closure records that are not past `threshold_days`
