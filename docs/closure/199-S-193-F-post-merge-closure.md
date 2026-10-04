---
shipment: 199-S
feature: 193-F
pr: 487
prs: [487]
merge_commit: 30095385a58b7d8db0ee4f1295b08262410fe560
reviewed_head: 1c5c379e
date: 2026-10-03
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/199-S-193-F-close-evidence.json
---

# 199-S / 193-F Post-Merge Closure: Agent and Skill Frontmatter Conformity Contract

## Summary

Shipment 199-S delivers feature 193-F, the agent and skill frontmatter
conformity contract. It has these parts:

* the `frontmatter_contract` module (agent and skill key sets, a
  deterministic parser, placeholder modes, and finding codes)
* the `verify_workspace` `frontmatter_conformity` check (managed artifacts
  fail closed; workspace-authored artifacts are advisory) and its migration
  proposals
* agent and skill remediation across templates, installed copies, and
  manifest checksums
* tune-harness Step 1.5c migration guidance, the tuning-guide contract
  section, and the P-013.1 / P-013.4 plugin-global clarification

Its manifest is `193-F` plus 8 tasks (`193.001-T` .. `193.008-T`) and 2
subtasks (`193.004.001-ST`, `193.004.002-ST`). Source stash: `EF96B695`.
Source deliberation: `037-DL`.

**PR #487** (`feat(193-F): agent and skill frontmatter conformity contract
(199-S)`) merged as `30095385` at `2026-10-04T06:07:24Z`, with reviewed HEAD
`1c5c379e`.

## Gates

| Gate | Result |
|---|---|
| Feature PR merge | #487 `30095385`, `MERGED` by merge commit (P-009). `30095385` has two parents (`4651728f`, `1c5c379e`) and is an ancestor of `origin/main` |
| Merge authority | Dark-mode activation record (P-017), merges pre-authorized |
| Closure lifecycle topology gate | `autoharness gate pipeline-topology --mode agent --shipment 199-S --phase lifecycle --json`: exit 0 on `chore/199-s-closure` (`BRANCH_OK`, `WORKTREE_TOPOLOGY_OK`, sole active shipment `199-S`, predecessor `198-S` explicit) |
| Pre-mode reconcile | `PROCEED` (11 items: `193-F` `active` in queue; 8 tasks and 2 subtasks `done` in archive; no orphans; `record-consistent`) |
| `--classify-only` | Exit 0: `CASCADE`, engine `VERIFIED` (`1.11.0` / `131577c`, cli) |
| Mutating `cascade-close` | Exit 0, `postcondition_verdict: pass`, 563 s |
| INV-12 disposition | `DISPOSITION_COMPLETE` |
| Post-mode reconcile | `PROCEED` |
| Closure index resync | `CLOSURE_INDEX_SYNC_OK` (`backlogit sync`: `Indexed 1698 artifacts` after the cascade; re-run after the follow-up stash entries, the final backlog mutation: `Indexed 1704 artifacts`) |
| Closure-evidence gate | `autoharness gate closure-evidence --path docs/closure/199-S-193-F-post-merge-closure.md --shipment 199-S --json`: exit 0 with `compaction_status: done` (the earlier `pending` run failed only `frontmatter_predicate`, as expected) |
| Full unit suite | `Ran 2945 tests`, `OK (skipped=54)` on `chore/199-s-closure` |

## Validator Evidence / Runtime Verification

There is no runtime validator surface. The change is a verification module,
a `verify` check, template and installed-artifact frontmatter, skill and
policy text, and tests. The `frontmatter_conformity` check runs as part of
`autoharness verify` and the unit suite.

## Closure Path

`close_path: cascade`. `close_evidence`:
`docs/closure/evidence/199-S-193-F-close-evidence.json` (phase `post_close`,
run `d3c88114c31d43bdbe2dcadde2f3c960`, `merge_commit_sha` `30095385…`).

* **Lock**: `.backlogit/queue/199-S.md` was held from pre-mode
  (`2026-10-04T06:10:56Z`) through post-mode (released
  `2026-10-04T06:21:47Z`).
* **Classification**: classifier `CASCADE`, qualifying root `193-F`, no
  out-of-manifest descendants. Disposition snapshot: `037-DL`.
* **Timeout sizing**: N = 11 + 1 = 12. B = ceil(1.5 × (133 + 35 × 12)) =
  830 s, which is at most 1800 s, so Ship used the default `--timeout`
  (1800 s). The supervision budget was 2400 s. The run was started attached,
  in async mode, and polled until it exited.
* **Mutating run**: `autoharness shipment cascade-close --shipment 199-S
  --feature 193-F --sha 30095385… --message "Merge pull request #487 …"
  --author "Derek Williams <…>" --json`. Exit 0. The command took 563 s; the
  `backlogit shipment ship` child took about 540 s
  (`06:12:03Z` → `06:21:03Z`), with `timed_out: false` and
  `mutation_state: completed`.
* **Postconditions** (from the `post_close` record):
  * `archived_ids`: 12 IDs (`193-F`, the 8 tasks, the 2 subtasks, and
    `199-S`)
  * `returned_ids`: `[]`
  * `allowed_ids` and `required_ids` are the same 12 IDs
  * `unexpected_archived` and `missing_required` are both `[]`
  * `parent_id_preserved`, `baseline_invariant`, and
    `disposition_byte_identical` are all `true`
  * shipment record `status: archived`, `archived_status: shipped`
* **Whole-tree guard**: Ship fingerprinted 1521 queue and archive records
  plus both stash files before the run. Only the 14 `closure_scope(S)` paths
  changed (12 archive records plus the `193-F` and `199-S` queue copies).
* Cascade gate: **`CLOSED`**. No P-005 event. Ship made no direct
  `backlogit shipment ship` call and did not substitute `SAFE_CLOSE`.

## Linked-Deliberation Disposition (P-015 INV-12)

The step ran under the same lock, after `CLOSED` and before post-mode, with
all inputs taken from the evidence record. The planner result equals the
`pre_close` snapshot. There was no planned `archive`, so Ship made no
deliberation mutation. The final invariance check found no fingerprint diff
(1749 non-exempt paths) and no porcelain diff.

| id | link_kinds | linking_members | outcome | reason_code | referrers |
|---|---|---|---|---|---|
| `037-DL` | `source_deliberation_id`, `description` | `193-F`, `193.001-T` .. `193.008-T` | `retained_shared_reference` | `retained_shared_reference` | `4F7B8BA7`, `692727D7` |

No unresolved references and no read failures. Neither
`ENGINE_SEMANTICS_UNVERIFIED` nor `ENGINE_LINE_UNVERIFIED_ADVISORY` applies.
`stranded_linked_deliberation`: `["037-DL"]`.
**`recommendation: DISPOSITION_COMPLETE`**.

Reports:

* Pre-mode: `.backlogit/reconcile/199-S-pre-20261004-061057.md` (`PROCEED`)
* Cascade close and disposition:
  `.backlogit/reconcile/199-S-cascade-close-20261004-061145.md` (`CLOSED`,
  `DISPOSITION_COMPLETE`)
* Post-mode: `.backlogit/reconcile/199-S-post-20261004-062145.md` (`PROCEED`)

## Source Artifact Cleanup

The only shipped top-level item is `193-F`.

| Item | Field | Value | Outcome | reason_code |
|---|---|---|---|---|
| `193-F` | `source_stash_id` | `EF96B695` | skipped: already archived (in `.backlogit/archive/stash.jsonl`) | n/a |
| `193-F` | `source_deliberation_id` | `037-DL` | `retained_shared_reference` (copied from the disposition report; Ship did not archive it) | `retained_shared_reference` (copied) |

Archived source artifacts: 0 stash entries and 0 deliberations. Ship made no
change to plan, decision, review, or spike artifacts (P-010).

## Releasability Evidence

* **Status**: READY. The contract is already on `main` (#487).
* **Invariants to preserve**: the following must keep holding:
  * managed agent and skill artifacts that violate the frontmatter contract
    fail `autoharness verify` closed
  * workspace-authored artifacts produce advisory findings only
  * migration proposals stay deterministic and ordered
* **Deployment path**: merge-only. Consumers get the check in the next
  autoharness release.
* **Monitoring**: the CI `test` job, the canonical unit suite, and
  `autoharness verify` runs on installed workspaces (tune runs surface the
  migration proposals).
* **Healthy signals**: `autoharness verify` reports no
  `frontmatter_conformity` failures on managed artifacts in this repository
  and in freshly installed workspaces.
* **Failure signals**: any of the following:
  * a false-positive `frontmatter_conformity` failure on a managed artifact
    that the contract allows
  * a tune run proposing migrations for already-conforming artifacts
  * a suite regression in the frontmatter tests
* **Rollback trigger**: a `frontmatter_conformity` defect that blocks
  `verify` on valid workspaces, or a suite regression attributable to 193-F.
* **Rollback procedure**: `git revert -m 1 30095385`. The backlog state
  committed by this closure stays valid either way. Restoring individual
  archived records uses `backlogit restore`.
* **Owner**: operator (softwaresalt). The Ship agent owns closure mechanics.
* **Validation window**: through the next two tune or verify runs against an
  installed consumer workspace.
* **Risky action record**: the mutating `cascade-close` (destructive,
  archives 12 artifacts): ActionRisk high. Approved through the dark-mode
  activation record (P-017) and the classify-only `CASCADE` / `VERIFIED`
  routing. Result: exit 0, postconditions pass.

## Verification

`$env:PYTHONPATH='src'; python -m unittest discover -s tests` (venv Python) on
the closure branch: `Ran 2945 tests in 423.231s`, `OK (skipped=54)`, exit 0.

## Follow-Up Items

All follow-ups are active stash entries. Stage owns triage.

* `4C6CBA75` (new, task/low): `_derive_template_variables` in
  `verify_workspace.py` does not derive `ALT_REVIEW_PROVIDER` or
  `ALT_REVIEW_FAMILY`.
* `A6CF06E6` (new, task/low): legacy frontmatter helpers in
  `verify_workspace.py` (`_extract_markdown_frontmatter` and the tier and
  model-routing checks) handle delimiters more loosely than
  `frontmatter_contract` (for example, they accept `----`).
* `2568A99A` (new, task/low): code reads `install_mode`, but no install path
  emits it.
* `24BA1B8F` (new, task/low): a pre-existing MD001 heading error at
  `.github/policies/workflow-policies.md:496`.
* `BE6C7DF8` (new, task/low): frontmatter conformity hardening P3s: path
  case-folding, junction walks within contained roots, the mutable
  `VALIDATORS` registry, and OneDrive placeholder files.
* `3E60149D` (new, task/low): other tests still use
  `assertRaises(Exception)` (`test_benchmark_scenarios.py`,
  `test_gates_topology.py`).
* `9F6AC6B3` (existing, deliberation/medium): reconcile plugin-global
  `max_subagent_tier: 2` with verify-harness dispatching a Tier 3 Reviewer A.
* `09EA8F24` (existing, bug/medium): the deferred scope expansion for the
  `verify_workspace` agent-identity migration scan.

## Residual Risks

* `037-DL` remains live (`queued`) and stranded. `193-F` is now archived, so
  no later closure re-runs the disposition step for 193-F. Its active
  referrers (`4F7B8BA7` and `692727D7`) keep it retained until Stage acts on
  those entries.
* The cascade rewrote each task's and subtask's `commit` field to
  `30095385`. The implementing commits remain in git history (#487).
* The plugin-global `max_subagent_tier: 2` versus the Tier 3 verify-harness
  Reviewer A remains an open decision (`9F6AC6B3`).

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this closure's
session memory was written.

* **Assessment**: `docs/memory` held 178 files (about 1311 KB), which
  exceeds the generic thresholds in aggregate.
* **Candidates**: the run was a bounded Tier-1 pass over this release unit.
  The single 199-S memory (the 2026-10-03 closure session) was consolidated
  into
  `docs/memory/compacted/2026-10-03-ship-199-s-193-f-full-lifecycle-compacted.md`.
  The verbose original is under `docs/archive/memory/`.
* **Excluded**:
  * other release units' memories, which are out of scope for this bounded
    run
  * plans, because Stage owns that work (P-010)
  * closure records, which are fresh (under `threshold_days`)
