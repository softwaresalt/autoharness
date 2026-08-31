---
title: "SHIP-9 — Backlog and docs traceability hygiene"
date: 2026-08-31
slug: backlog-docs-traceability-hygiene
doc_type: plan
source_stash: "B90A5BBF, 99E4CF94, 7645AE19, 91CE2B66, 01340569"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-9"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "no"
plan_review_verdict: "PASS"
---

# SHIP-9 — Backlog and docs traceability hygiene

## Problem

Five traceability defects. Individually small; collectively they are the record
of what this workspace believes about its own history, and three of them are
currently **wrong**.

### B90A5BBF — possible premature archival of stash `34D50F2D`

Copilot's PR #415 review (thread `PRRT_kwDORzpWpM6dYbyj`, HEAD `d0a2d5e8`) flags
that archiving `34D50F2D` may be incorrect. The entry's own most-recent
2026-08-16 Stage re-triage append states it stays **ACTIVE** solely because
candidate (c) — the background Verification & Compaction layer — "REMAINS
DEFERRED AND UNSELECTED". That rationale is unrelated to candidate (d) / feature
`111-F` / shipment `119-S`, which is what the archival commit `d0a2d5e8` cited as
justification. The archival therefore satisfied a different candidate than the
one keeping the entry alive. Precedent for reactivation exists: `936C68F3` was
reactivated from `.backlogit/archive/stash.jsonl` on 2026-08-06.

### 99E4CF94 — three dangling doc references inside `34D50F2D`

Three references point at `docs/plans/` and `docs/design-docs/` paths that were
relocated to `docs/archive/deprecated-supervisor-design/` by an earlier
quarantine — **not** by PR #411's compaction. The fairness test confirms it: the
refs exist identically on `origin/main` (main=1, head=1) and PR #411 never
touched those lines. Correctly deferred under P-021 C1 as prior-quarantine
fallout.

### 7645AE19 — a merged closure record asserts something false

`docs/closure/pr411-p020-context-compaction-closure.md` asserts
"`docs/plans` | 65 | 642 KB | 0" further candidates and states "no further file
qualifies". That is wrong: re-assessment after the PR #412 merge found **three**
genuine plan-consolidation candidates carrying an appended `## Plan Review`
section, and `docs/plans` exceeds **both** the `max_files` and `max_size_kb`
triggers. The same counting error then recurred in the #412 floor artifact's own
first draft — three instances of one root cause. **Correct the record forward;
do not silently rewrite the merged artifact.**

Root causes, all three instances: assessing one target directory's criterion and
generalising the no-op to the others, when each directory has its own Phase 2
criterion; and counting `docs/memory` root-only rather than recursively.

### 91CE2B66 — the P-020 compaction backlog is real and unactioned

`docs/plans` exceeds both thresholds (65 files > 40; 642 KB > 500 KB). Three
plans carry an appended `## Plan Review` section and are genuine compact-context
Phase 2 candidates:

* `2026-08-20-docline-lint-restoration-plan.md` (13.8 KB)
* `2026-08-20-ship-stash-archive-operation-migration-plan.md` (20.3 KB)
* `2026-08-20-template-dogfood-paired-edit-contract-plan.md` (7.4 KB)

`docs/memory` also exceeds both thresholds when counted **recursively** (92 files
/ 730 KB, not the root-only 36 / 430 KB), and `docs/memory/098-S-closure.md` is a
fourth eligible candidate: the 2026-07-30 compaction preserved it only because it
was then inside the 14-day window "despite its undated filename", and at
`closed_at` 2026-07-29 it is now 29 days old.

### 01340569 — a half-ignored checkpoint directory

`backlogit sync` auto-added `.backlogit/checkpoints/` to `.gitignore`, but **five
checkpoint files are already tracked**, leaving a state where the ignore rule
lies about the repository. Deferred under P-021 C1 because the `.gitignore` edit
was a side effect emitted by `backlogit sync` rather than part of PR #409's
authorized change, and resolving it requires `git rm --cached` on tracked
tool-managed state — a history/tracking decision.

## Direction

Ordered so that the *record* is corrected before the *files* are moved, because
compaction that runs against a wrong assessment reproduces the wrong assessment.

1. Decide `34D50F2D`'s disposition on its own evidence, and repoint its dangling
   references in the same pass (the two are the same entry).
2. Correct the closure record forward and add the guard that makes the counting
   error detectable.
3. Execute the four-candidate Phase 2 compaction.
4. Decide and implement the checkpoint tracking policy.

**Recorded direction on `01340569`.** Of the two options the entry names —
untrack the five committed files so the ignore rule becomes truthful, or remove
the auto-added ignore rule so the tracked files are honestly represented —
**untrack** is preferred. Checkpoints are tool-managed, machine-generated,
session-scoped recovery state; `backlogit sync` adding the ignore rule expresses
the tool's own intent, and the five tracked files are historical accidents.
Untracking with `git rm --cached` preserves the files on disk and in history.
This is a *recommendation carried into the task*, not a fait accompli: the task's
first step is to confirm no live process reads those five files from the index.

## Hardening (P-006)

Not triggered: documentation, backlog state, and one tracking decision. No
source, schema, or distribution surface. Three constraints are binding anyway.

* **H1 (binding).** `7645AE19` is **correct-forward only**. The merged closure
  artifact must not be silently rewritten; the correction is an appended,
  dated, clearly-marked correction that preserves the original claim verbatim
  alongside it.
* **H2 (binding).** `git rm --cached` must not delete working-tree files. Confirm
  the five paths remain on disk after the operation, and confirm the operation is
  the cached-only variant before running it.
* **H3 (binding).** Compaction is **consolidation, not deletion**. Each of the
  four candidates is consolidated into a decided-state artifact with its source
  preserved per the compact-context Phase 2 contract; no content is destroyed.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Decide `34D50F2D`'s archival disposition on candidate (c)'s evidence and repoint its three dangling references | S | medium | `.backlogit/stash.jsonl`, `.backlogit/archive/stash.jsonl` |
| 2 | Correct the PR #411 closure record forward and add a per-directory P-020 assessment guard | M | medium | `docs/closure/`, `tests/` or the compact-context skill |
| 3 | Execute P-020 Phase 2 consolidation for the four named candidates and settle the checkpoint tracking policy | M | medium | `docs/plans/`, `docs/memory/`, `.gitignore`, git index |

Task 1 pairs `B90A5BBF` and `99E4CF94` because both operate on the same stash
entry and a reactivation would move the text the references live in — doing them
separately risks repointing references in a file that is about to move. Task 3
pairs the compaction with the checkpoint decision because both are
tracking/tree-state operations reviewed by the same eye.

## Non-goals

* No re-litigation of candidate (d) / `111-F` / `119-S`. Task 1 examines
  candidate (c)'s disposition only.
* No compaction of any directory or file beyond the four enumerated candidates.
* No change to the P-020 thresholds themselves.
* No deletion of checkpoint files from disk or history (**H2**).

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `backlogit doctor`;
`backlogit_sync_index`; `git status` confirming the five checkpoint files remain
on disk and are no longer tracked; markdownlint on every changed document; a
re-run of the P-020 assessment confirming the recursive counts are now reported
per directory.

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Correctness | **P1** | Reactivating `34D50F2D` from the archive is a **destructive-adjacent backlog mutation** and this run's dark-mode record says to halt approval-dependent destructive operations not explicitly authorized. | **Resolved.** Task 1 is scoped to **decide and record**, and to reactivate **only if** candidate (c) is confirmed still deferred and unselected on current evidence. Reactivation is additive (it restores an entry to the active stash; nothing is deleted) and follows the established `936C68F3` precedent, so it is not destructive. If the evidence is ambiguous, the task records the ambiguity and leaves the archival standing — the fail-safe direction. |
| 2 | Maintainability | **P1** | A guard that re-implements the P-020 assessment will drift from the compact-context skill that performs it, and then the guard and the skill will disagree. | **Resolved.** Task 2's acceptance requires the guard to assert the **per-directory, recursive** counting property against the *same* code path the skill uses, rather than reimplementing the count. If no shared code path exists, the guard is written as an assertion on the skill's own reported output. |
| 3 | Constitution | **P1** | `git rm --cached` mutates the git index — a destructive-command class under Principle VII. | **Resolved.** **H2** makes the cached-only variant and the on-disk survival check mandatory pre- and post-conditions. The operation removes nothing from the working tree and nothing from history. Task 3's acceptance requires the pre-check (no live consumer reads those five paths from the index) to be recorded before the operation runs. |
| 4 | Scope | P2 | Compaction could sweep beyond the four candidates. | Bounded by enumeration. A fifth candidate the re-assessment reveals is a P-021 capture, not this shipment. |
| 5 | Template integrity | P2 | Consolidated artifacts must keep valid frontmatter — the exact class SHIP-5 task 3 is repairing. | Task 3's acceptance includes the frontmatter-decode check on every produced artifact. Sequencing SHIP-5 before SHIP-9 means the strengthened truncation guard is already in place when these artifacts are written. |
| 6 | Architecture | P2 | Correcting a merged closure record forward, rather than rewriting it, leaves two conflicting claims for a future reader. | **H1** requires the correction to be adjacent, dated, and explicitly superseding, so the pair reads as a record with a correction rather than as a contradiction. This is the established convention and the entry itself demands it. |
| 7 | Security | P3 | No security surface. | Confirmed: no credentials, no network egress, no path handling from untrusted input. |

**Verdict: PASS.** 3 P1 raised, all 3 resolved. Zero unresolved P0/P1. Two
review-fix cycles of three.
