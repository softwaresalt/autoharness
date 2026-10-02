---
shipment: 204-S
feature: 198-F
pr: 472
merge_commit: 2770128a3beec82266f6aa138e1999d8e4b346ab
reviewed_head: 1b605e8a
date: 2026-10-01
closure_status: READY
compaction_status: done
---

# 204-S / 198-F Post-Merge Closure: P-015 Close-Path Gate vs INV-12 Split, Skill Engine-Semantics Gate (195-F slice 3 of 6)

## Summary

Shipment 204-S (195-F slice 3 of 6; covering feature 198-F; manifest
`198-F`, `198.002-T` … `198.009-T`) merged through PR #472 as merge commit
`2770128a`. The operator approved the merge, and it used `--merge`. The final
reviewed HEAD was `1b605e8a`.

The slice contains:

* **The P-015 close-path gate vs INV-12 split** (U2b, 198.002-T …
  198.007-T): relax step R9 and the item-7 test move; the gate-split policy
  triple (Statement, Required Check, two-part Postcondition, Violation Action,
  P-007, INV-7, INV-10); item 7 scoped to non-feature members, with the
  evidence-class and P-010 clarifications; their policy assertions; and
  rendered-region parity for the edited paragraphs.
* **The skill engine-semantics gate** (U3a, 198.008-T and 198.009-T) in
  `.github/skills/shipment-reconcile/SKILL.md` and its template:
  * Step 0(b) now snapshots every explicit manifest member, whatever its
    `artifact_type`.
  * Step 0(c) probes the backlogit engine on the invocation surface and
    selects the close path with `select_close_path` (2x2 table).
  * The Cascade Close Sub-Procedure re-probes the engine fresh during
    pre-invocation revalidation and halts on any drift.
* A docstring update in `src/autoharness/gates/shipment_closure.py` that names
  the Step 0(c) close-path selection as a landed caller of the engine gate and
  `select_close_path`.

The Linked-Deliberation Disposition step that `CASCADE` now routes to lands in
slice 5 (206-S).

## Interim Rule A (operator decision)

**Interim rule A per operator decision 2026-10-01, stash 26D90B0F:
shipment-reconcile skill authoritative until slice 4.**

P-015 stays internally inconsistent until slice 4 (199-F, shipment 205-S)
merges. The operator ruled that `.github/skills/shipment-reconcile/SKILL.md`
remains authoritative for closure execution until then. Since #472, the skill
includes the slice-3 Step 0(c) engine-semantics gate. Where P-015 and the
skill conflict, the skill wins.

* Ship followed the skill for this closure, including its new engine-semantics
  gate. It did not edit the policy or skill files.
* A comment recording the decision for this closure was appended to stash
  entry `26D90B0F` with
  `backlogit comment add 26D90B0F --actor ship --commit-sha 2770128a…`
  (`{"ok": true}`). backlogit stores comment events in the git-ignored
  `.backlogit/logs/` JSONL log, so this closure record is the durable,
  version-controlled copy. The stash entry stays active, and Stage owns its
  triage.
* The skill's gate and the P-015 composition agreed on `CASCADE`. The
  interim rule did not have to break a tie.

## Gates

| Gate | Result |
|---|---|
| Local review | `READY_WITH_FOLLOWUPS`, P0=0, P1=0, at `1b605e8a` |
| Full local build | 2573 tests OK |
| Required CI | Green at `1b605e8a` |
| P-018 copilot-review | `SATISFIED` at `1b605e8a` |
| P-009 merge strategy | Merge commit (`--merge`) |
| P-016 worktree topology | Single worktree |
| Merge authority | Explicit operator approval (normal mode, no dark mode, no admin fallback) |
| 198-S sequencing guard | Re-verified pre-merge: 198-S `queued`, `198-S → 201-S` `blocks` edge present |
| Closure lifecycle topology gate | `uv run autoharness gate pipeline-topology --mode agent --shipment 204-S --phase lifecycle --json`: exit 0 on `chore/204-s-closure` (predecessor `203-S`, explicit) |

## Validator Evidence / Runtime Verification

There is no runtime validator surface. The slice changes policy and skill
text, tests, and a docstring. The unit suite and the policy and skill
assertions verify it. This closure also exercised the new Step 0(c)
engine-semantics gate live, as recorded below.

## Closure Path

`shipment-reconcile` (authoritative under interim rule A) selected `CASCADE`
for 204-S:

* **Classifier**: `classify_shipment_close_path` returned `CASCADE`. The
  qualifying root feature is `198-F`, and there are no out-of-manifest
  descendants.
* **Engine-semantics gate (Step 0(c))**: the probe
  `backlogit version --no-update-check --format json` on the CLI (the
  invocation surface) returned `version` `1.11.0` and `commit` `131577c`.
  `assess_cascade_engine_semantics` returned `VERIFIED`.
* **Selection**: `select_close_path` returned `CASCADE`.
* **Linked deliberations**: none. 198-F is a T2 "deliberation-clean slice",
  so the pre-195 and flat `allowed_ids`/`required_ids` coincide.

The run held the `.backlogit/queue/204-S.md` file lock throughout (acquired
`2026-10-02T00:34:21Z`, released `2026-10-02T00:41:04Z`). It captured:

* the pre-mode check and the Step 0 snapshot of every member
* a fresh pre-invocation revalidation: classifier, linked deliberations, and
  an exact-string engine re-probe (`1.11.0` / `131577c` / `cli` /
  `VERIFIED`), with no drift
* the baseline fingerprint (1503 queue and archive records)
* the raw `backlogit shipment ship 204-S --sha 2770128a…` result
  (backlogit 1.11.0, exit 0, about 6.5 minutes)

All of this evidence is contemporaneous.

* `archived_ids`: `198-F`, `198.002-T` … `198.009-T`, `204-S`
* `returned_ids`: `[]`
* `archived_ids - allowed_ids` = `[]` and `required_ids - archived_ids` = `[]`
* `parent_id` is preserved on all eight tasks.
* The whole-tree fingerprint diff shows changes only on the ten
  `allowed_ids` records, with no out-of-scope change.
* The shipment record is `status: archived` with `archived_status: shipped`.

**Linked-deliberation disposition (198-F T4)**:
`linked_deliberation_disposition: step-not-yet-on-main (transition window); all retained`.
Ship made no deliberation mutation.

Reports:

* Pre-mode: `.backlogit/reconcile/204-S-pre-20261002-003422.md` (`PROCEED`)
* Cascade close: `.backlogit/reconcile/204-S-cascade-close-20261002-003433.md`
  (`CLOSED`)
* Post-mode: `.backlogit/reconcile/204-S-post-20261002-004102.md` (`PROCEED`)

No P-005 event was raised. No operator deviation was needed beyond the
recorded interim rule A.

## Closure Index Resync

`CLOSURE_INDEX_SYNC_OK`. `backlogit sync` (the CLI fallback for
`backlogit_sync_index`) ran after every backlog mutation in this closure. That
covers the cascade close and the `26D90B0F` comment append. The sync exited 0
with `Indexed 1659 artifacts`, before the closure commits were made.

## Source Artifact Cleanup

* No manifest item declares `custom_fields.source_stash_id` or
  `custom_fields.source_deliberation_id`, so there was no source stash or
  deliberation to retire.
* The umbrella feature `195-F` is linked `related_to`, not through
  `parent_id`. It stays open until slice 6 (201-S), and Ship did not touch it.
* Ship made no change to plan, decision, review, or spike artifacts, which are
  Stage-owned (P-010).

## Releasability Evidence

* **Status**: READY. The change is policy, skill, and test text plus a
  docstring. The skill is governed by interim rule A until slice 4.
* **Monitoring**: the CI `test` job and the canonical suite.
* **Healthy signals**:
  * the policy, skill-parity, and close-path test modules stay green
  * later closures record the Step 0(c) probe (`version`, `commit`,
    `probe_surface`) and the `select_close_path` verdict
* **Failure signals**:
  * a regression in those modules
  * a `CASCADE` closure without a recorded engine probe or with re-probe
    drift
  * a closure that follows P-015 text over the skill before slice 4 merges
* **Rollback trigger**: a suite regression attributable to the slice.
* **Rollback procedure**: `git revert -m 1 2770128a`.
* **Owner**: operator (softwaresalt). The Ship agent owns closure mechanics.
* **Validation window**: through 205-S (slice 4), which realigns the skill and
  the remaining P-015 sections.

## Follow-Up Items

These P-021 deferred scope expansions and follow-ups stay active. Stage owns
triage:

* `26D90B0F`: remove the interim P-015 contract contradiction between 195-F
  slices. It carries the interim rule A comments for 203-S and 204-S.
* `0C3EDC57`: define or remove the undefined "stale probe" term in the P-015
  engine-semantics precondition paragraph. Captured during 204-S.
* `218DF163`: replace the hard-coded `.backlogit/queue/` and
  `.backlogit/archive/` path literals in the `shipment-reconcile` skill.
  Captured during 204-S.
* `4661F6AA`: update the skill's Quality Criteria and Related Artifacts
  lists. Captured during 204-S.
* `049094FC`: the 204-S local-review P2/P3 follow-ups on the P-015 and
  `shipment-reconcile` surface. Captured during 204-S.
* `B31435CF`, `56566173`: carried over from 203-S.
* `D6CCDE2C`, `3C09D9D0`, `6F2C4BFD`, `013363F5`, `492FB413`: carried over
  from 202-S.

Next shipment: `205-S` (slice 4 of 6, 199-F). Its claim eligibility is
decided by its own `blocks` edges and the `pre_claim` topology gate. 198-S
stays `queued`, sequenced behind the `198-S → 201-S` `blocks` edge.

## Residual Risks

* The cascade rewrote each released task's `commit` field to the merge SHA.
  The implementing commits remain in git history.
* P-015 is internally inconsistent until slice 4 merges. The mitigation is
  interim rule A, recorded here and on `26D90B0F`.
* The cascade took about 6.5 minutes of CPU-bound engine time for 10
  artifacts. This is an operational latency observation, not a correctness
  issue.

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this artifact was
created.

* **Assessment**: `docs/memory` holds 173 files (about 1300 KB), and 104 of
  them are uncompacted (about 938 KB). That exceeds the generic `max_files`
  and `max_size_kb` thresholds in aggregate.
* **Candidates**: selection was bounded to this release unit (Tier-1). The
  204-S session memory was consolidated into
  `docs/memory/compacted/2026-10-01-ship-204-s-198-f-full-lifecycle-compacted.md`,
  and the verbose original moved to
  `docs/archive/memory/2026-10-01-ship-204-s-198-f-closure-session.md`.
* **Excluded**:
  * `docs/memory/2026-09-29/stage-8fee91f4-backlogit-1-11-cascade-alignment.md`,
    because the umbrella 195-F work is still active (slices 4 to 6)
  * other release units' and Stage-owned memories past `threshold_days`, which
    stay out of this bounded Tier-1 run
  * plans, because consolidating them into decided-plans is Stage-owned
    (P-010)
  * closure records that are not past `threshold_days`
