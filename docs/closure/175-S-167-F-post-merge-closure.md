---
shipment: 175-S
feature: 167-F
pr: 458
merge_commit: 985e3990f348772a823f0b9860a18de8cebd591b
reviewed_head: 34d88829ce57947912f0d2aed758c86bd1103fa9
date: 2026-09-27
closure_status: READY
compaction_status: done
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
13 manifest items plus the shipment record, with `returned_ids=[]`, no
unexpected IDs, and every `parent_id` preserved. The shipment record reads
`archived_status: shipped`.

Reconciliation reports: `.backlogit/reconcile/175-S-pre-20260927-202155.md`,
`.backlogit/reconcile/175-S-cascade-close-20260927-202155.md`, and
`.backlogit/reconcile/175-S-post-20260927-202155.md`. They are post-hoc
reconstructions from immutable git evidence (pre-close `985e3990`,
post-close `5cc5371a`), including a classifier re-run against the exported
pre-close tree, because the original run omitted them.

## Source Artifact Cleanup

* Source stash entry FD0CCB42 was already archived at Stage harvest; no
  retirement action was required.
* All 12 tasks and feature 167-F are archived with `archived_status: done`.

## Releasability Evidence

* **Status**: READY
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
