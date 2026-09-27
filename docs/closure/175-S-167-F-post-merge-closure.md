---
shipment: 175-S
feature: 167-F
pr: 458
merge_commit: 985e3990f348772a823f0b9860a18de8cebd591b
reviewed_head: 34d88829ce57947912f0d2aed758c86bd1103fa9
date: 2026-09-27
closure_status: READY_WITH_CONDITIONS
compaction_status: done
conditions:
  - id: operator-accepts-175s-cascade-evidence-deviation
    description: >-
      Operator explicitly accepts that the 175-S cascade close lacks contemporaneous
      returned_ids, pre-invocation revalidation, and baseline-fingerprint records,
      and that only the postconditions were verified afterward from git history
      (.backlogit/reconcile/175-S-cascade-close-20260927-202155.md).
    satisfied: true
    evidence: https://github.com/softwaresalt/autoharness/pull/459#issuecomment-5860003692
    follow_up: 008F3BCF
---

# 175-S / 167-F Post-Merge Closure -- Closure-Evidence Producer/Consumer Naming Contract

## Summary

Shipment 175-S (feature 167-F, tasks 167.001-T through 167.012-T) merged via
PR #458 as merge commit `985e3990` (`--merge`, two parents; reviewed HEAD
`34d88829`). It reconciles the closure-evidence producer and consumer on one
contract module (`src/autoharness/gates/closure_contract.py`):

* canonical write pattern `docs/closure/{shipment_id}-{feature_id}-post-merge-closure.md`
* closed recognized-read set: legacy date-prefixed names are readable, never written
* pipeline-topology predecessor-closure reader rewired onto the contract, with
  the validity predicate unchanged
* new `PREDECESSOR_CLOSURE_UNRECOGNIZED` diagnostic token
* write-time gate `autoharness gate closure-evidence`
* producer docs (operational-closure skill, Ship agent; template and mirror)
  aligned to the contract

## Gates and Dark-Mode Record (P-017)

| Gate | Result |
|---|---|
| Local multi-persona review | 3 review-fix cycles; final `READY_WITH_FOLLOWUPS`, P0=0, P1=0 |
| Full local build | `PYTHONPATH=src python -m unittest discover -s tests`: 2439 tests OK (54 skipped) at `34d88829` |
| Copilot review (P-018) | 2 iterations; 2 threads fixed in `34d88829`, replied, resolved; gate `SATISFIED` |
| Required CI | ci gate, test, pipeline-topology (ambient), detect code changes: all pass |
| P-009 merge strategy | merge commit only (squash/rebase disabled); two parents verified |
| P-016 worktree topology | single worktree |
| Merge authority | `DARK_MODE_ACTIVE` `merge_approval_pre_authorized`; admin fallback not used |

## Validator Evidence / Runtime Verification

This shipment adds no runtime service surface. The change is a CLI gate and
library contract, verified by the unit/integration suite, including
composed producer/consumer state-machine, semantic-parity, non-drift, and
adversarial regression batteries. No runtime validator probes apply.

## Closure Path

`shipment-reconcile` classified 175-S as `CASCADE` under P-015. Root feature
167-F had no out-of-manifest descendants. The cascade archived exactly the
13 manifest items plus the shipment record, with no unexpected IDs and every
`parent_id` preserved (measured from git history). The shipment record reads
`archived_status: shipped`. `returned_ids` is **unproven**: the original
run's summary said `returned_ids=[]`, but the raw command output was not
retained.

Reconciliation reports: `.backlogit/reconcile/175-S-pre-20260927-202155.md`,
`.backlogit/reconcile/175-S-cascade-close-20260927-202155.md`, and
`.backlogit/reconcile/175-S-post-20260927-202155.md`. They are post-hoc
reconstructions from immutable git evidence (pre-close `985e3990`,
post-close `5cc5371a`), including a classifier re-run against the exported
pre-close tree, because the original run omitted them.

**Evidence-completeness deviation (P-005 process deviation).** The original
cascade close did not record three items the skill requires at the time of
the close: the pre-invocation classifier revalidation, the pre-invocation
baseline fingerprint, and the raw `backlogit_ship_shipment` result, including
`returned_ids`. None can be reproduced after the close. The safety
postconditions those checks protect are measured from committed history:

* exactly the allowed IDs were archived
* no out-of-manifest backlog item changed between `985e3990` and `5cc5371a`
* `parent_id` values were preserved
* the classifier re-run finds no out-of-manifest descendants

The cascade-close report records the gap in its frontmatter and in an
explicit deviation section. The operator accepted this deviation for this
iteration only
([PR #459 comment](https://github.com/softwaresalt/autoharness/pull/459#issuecomment-5860003692)).
The root-cause fix is deferred to stash entry 008F3BCF.

## Source Artifact Cleanup

* Source stash entry FD0CCB42 was already archived at Stage harvest; no
  retirement action was required.
* All 12 tasks and feature 167-F are archived with `archived_status: done`.

## Releasability Evidence

* **Status**: READY_WITH_CONDITIONS. The operator accepted the cascade
  evidence deviation for this iteration only
  ([PR #459 comment](https://github.com/softwaresalt/autoharness/pull/459#issuecomment-5860003692)),
  which satisfies the frontmatter condition
  `operator-accepts-175s-cascade-evidence-deviation`. Root-cause fix
  (automatic, fail-closed capture of close-command evidence) is deferred to
  high-priority bug stash entry 008F3BCF, for Stage triage.
* **Monitoring**: CI `test` job and the pipeline-topology ambient gate on every
  push; the next shipment's `pre_claim` consumes this artifact as predecessor
  evidence.
* **Rollback**: revert merge commit `985e3990` with
  `git revert -m 1 985e3990f348772a823f0b9860a18de8cebd591b`. The reader
  still accepts legacy names, so existing closure history stays readable.
* **Owner**: operator (softwaresalt); Ship agent for closure mechanics.
* **Validation window**: through the next successor-shipment `pre_claim`.

## Follow-Up Items

These are P-021 C2 deferred-scope captures. Triage is Stage-owned.

* C1CAE343: link/UNC containment and TOCTOU hardening across the reader and the gate
* 352AF87E: frontmatter identity vs filename cross-check
* 40134A08: configurable closure directory
* 27F44BCE: public acceptance-predicate/parser API
* 04B98FC2: pre-existing template/mirror drift (heading, `DEFAULT_BRANCH` placeholder)
* DEEAE9F1: gate double-read and sibling-artifact verdict divergence
* 9DF8BC43: gate telemetry
* 30B8411A: legacy `compaction: degraded` wording in the Ship agent

## Residual Risks

* The cascade close rewrote each task's `commit` field to the merge SHA. The
  original per-task commits remain in git history.
* The write-time gate is stricter than the reader: it rejects symlinked
  entries. The reader-side hardening is tracked by C1CAE343.
* The cascade-close audit trail is incomplete: contemporaneous `returned_ids`,
  pre-invocation revalidation, and baseline-fingerprint records are missing,
  and only the postconditions were verified afterward (see Closure Path). The
  process fix is to capture these at close time; the skill already requires
  it. Ship made no skill change in this PR. The operator accepted the gap for
  this iteration; automatic fail-closed evidence capture is tracked by
  008F3BCF.

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` immediately after this
artifact was created.

* **Assessment**: `docs/memory` (77 files, about 1285 KB) exceeds the
  generic thresholds in aggregate.
* **Candidates**: selection stayed bounded to this release unit (Tier-1).
  This session's fresh memory was consolidated into
  `docs/memory/compacted/2026-09-27-ship-175-s-167-f-full-lifecycle-compacted.md`.
  The verbose original moved to `docs/archive/memory/`.
* **Excluded**:
  * The Stage memory `docs/memory/2026-09-17-stage-closure-evidence-naming-contract.md`
    and the seven-entry portfolio memories are referenced by live review and
    decision artifacts, and by shipments still in the portfolio DAG.
  * Plan consolidation into a decided-plan was not performed. Creating or
    modifying plan artifacts is outside Ship's role boundary (P-010), and the
    plan is referenced by the live multi-shipment portfolio deliberation.
  * This closure record is fresh, so it is not past `threshold_days`.
