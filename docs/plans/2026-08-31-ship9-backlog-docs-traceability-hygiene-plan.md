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

### 01340569 — a checkpoint tracking-policy question (**premise corrected, cycle 1**)

**The original statement of this entry was factually wrong on both of its
claims, and is corrected here on direct measurement.** As recorded in cycle 0 it
read: *"`backlogit sync` auto-added `.backlogit/checkpoints/` to `.gitignore`, but
five checkpoint files are already tracked, leaving a state where the ignore rule
lies about the repository."* Measured at this HEAD:

| Claim | Measured reality |
|---|---|
| `.gitignore` contains `.backlogit/checkpoints/` | **FALSE.** `.gitignore` carries exactly five `.backlogit` rules — `.backlogit/*.db`, `.backlogit/hooks_queue.jsonl`, `.backlogit/*.db-shm`, `.backlogit/*.db-wal`, `.backlogit/runtime/`. There is **no** checkpoints rule. `git check-ignore -v` on a checkpoint file exits 1 (not ignored). |
| Five checkpoint files are tracked | **FALSE — there are 19.** `git ls-files .backlogit/checkpoints/` returns 19 tracked files. |

**Consequence: the defect as stated does not exist.** There is no ignore rule, so
no ignore rule is lying. The 19 tracked checkpoint files are **honestly
represented** by the current configuration. The remaining question is a genuine
but *undecided* policy question — *should* checkpoints be tracked? — not a
correctness defect awaiting repair.

Deferred under P-021 C1 because a tracking/history decision was outside PR #409's
authorized change. That deferral remains correct; only the premise was wrong.

## Direction

Ordered so that the *record* is corrected before the *files* are moved, because
compaction that runs against a wrong assessment reproduces the wrong assessment.

1. Decide `34D50F2D`'s disposition on its own evidence, and repoint its dangling
   references in the same pass (the two are the same entry).
2. Correct the closure record forward and add the guard that makes the counting
   error detectable.
3. Execute the four-candidate Phase 2 compaction.
4. Decide and implement the checkpoint tracking policy.

**Recorded direction on `01340569` — REVERSED in review-fix cycle 1.**

Cycle 0 preferred **untrack via `git rm --cached`**, on the reasoning that the
ignore rule expressed the tool's intent and the tracked files were historical
accidents. That reasoning rested entirely on the premise corrected above: **there
is no ignore rule**, so there is no tool intent to honour and no inconsistency to
resolve. With the premise gone, the conclusion does not survive.

**New direction: KEEP CHECKPOINTS TRACKED. Add no ignore rule. Change nothing in
the git index.** This is the fully non-destructive option and it is now the
better-supported one:

* **The tracked checkpoints are load-bearing audit evidence.** This very run
  depends on committed checkpoint records for P-017 audit evidence, and Stage's
  own crash-resumption protocol enumerates checkpoints across sessions. Untracking
  19 files would delete that evidence trail from the repository going forward.
* **Nothing is currently inconsistent.** No rule claims these files are ignored.
* **`git rm --cached` is a destructive index mutation and is NOT preauthorized.**
  See **H2** as rewritten below.

**Gating for any future untracking (binding).** If a later run still wants to
untrack checkpoints, that operation requires a **distinct, explicit operator
approval recorded at execution time**. It is **not** covered by this run's
dark-mode merge preauthorization: merge approval authorizes merging the reviewed
diff, not running destructive index commands. The task **must not** run
`git rm --cached` under this shipment's authority.

**Scope of task 3's Part B is therefore: record the corrected premise, record the
decision, and stop.** No `.gitignore` edit, no index mutation, no file movement.

## Hardening (P-006)

Not triggered: documentation, backlog state, and one tracking decision. No
source, schema, or distribution surface. Three constraints are binding anyway.

* **H1 (binding).** `7645AE19` is **correct-forward only**. The merged closure
  artifact must not be silently rewritten; the correction is an appended,
  dated, clearly-marked correction that preserves the original claim verbatim
  alongside it.
* **H2 (binding) — REWRITTEN in cycle 1. `git rm --cached` is NOT preauthorized
  and MUST NOT run in this shipment.** Cycle 0 treated it as an approved operation
  needing only a safety check. It is a **destructive index mutation** under
  Constitution Principle VII, and this run's dark-mode record preauthorizes
  **merge approval only** — merge approval is not, and never implies, approval to
  execute destructive commands. Requirements:
  * The **non-destructive alternative is adopted** (keep tracked, add no ignore
    rule, touch nothing), so no destructive operation is needed at all.
  * If a future run revisits untracking, it requires a **distinct, explicit
    operator approval obtained at execution time**, naming the exact paths. An
    agent may not infer it from this plan, from merge approval, or from the
    cycle-0 recommendation this cycle withdrew.
  * Under dark-factory/AFK mode the operation **never runs**, because the approval
    cannot be obtained. Fail closed.
* **H4 (binding) — SHIP-5 is a genuine prerequisite, encoded as a real edge.**
  Task 3's acceptance requires the frontmatter-decode check on every produced
  artifact, and cycle-0 finding 5 relies on SHIP-5's *strengthened truncation*
  guard being in place — a decode check alone cannot see the space-hash class.
  That is a real dependency, not shipment-chain ordering: SHIP-9 task 3
  consumes SHIP-5 task 3a's guard. It is recorded as a `blocks` edge
  (SHIP-5 → SHIP-9) and the task's acceptance names the guard it must run.
* **H5 (binding) — safety mode.** Every task enters `careful`. Task 1 additionally
  enters `investigate-first`, because its charter is to *decide* an archival
  disposition on evidence before any stash mutation, and `investigate-first` is
  exactly the posture that separates evidence from proposed change.
* **H3 (binding).** Compaction is **consolidation, not deletion**. Each of the
  four candidates is consolidated into a decided-state artifact with its source
  preserved per the compact-context Phase 2 contract; no content is destroyed.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Decide `34D50F2D`'s archival disposition on candidate (c)'s evidence and repoint its three dangling references | S | medium | `.backlogit/stash.jsonl`, `.backlogit/archive/stash.jsonl` |
| 2 | Correct the PR #411 closure record forward and add a per-directory P-020 assessment guard | M | medium | `docs/closure/`, `tests/` or the compact-context skill |
| 3 | Execute P-020 Phase 2 consolidation for the four named candidates and record the checkpoint tracking decision | M | medium | `docs/plans/`, `docs/memory/` (Part A only; Part B is record-only) |

Task 1 pairs `B90A5BBF` and `99E4CF94` because both operate on the same stash
entry and a reactivation would move the text the references live in — doing them
separately risks repointing references in a file that is about to move. Task 3's
Part B is **record-only** after the cycle-1 premise correction: it touches neither
`.gitignore` nor the git index (**H2**), so it no longer shares a "tree-state
operation" rationale with Part A — it is retained in task 3 purely because it is a
short written decision with no surface of its own, and it is explicitly bounded to
writing that decision down.

## Non-goals

* No re-litigation of candidate (d) / `111-F` / `119-S`. Task 1 examines
  candidate (c)'s disposition only.
* No compaction of any directory or file beyond the four enumerated candidates.
* No change to the P-020 thresholds themselves.
* **No `.gitignore` edit and no git-index mutation** (**H2**). No
  `git rm --cached`, under this shipment's authority or any inference from it.
* No deletion of checkpoint files from disk or history.

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `backlogit doctor`;
`backlogit_sync_index`; **`git status` and `git diff --stat` confirming this
shipment made no change to `.gitignore` and no change to the git index for
`.backlogit/checkpoints/`** (the corrected Part B postcondition — the previous
"five files no longer tracked" check is withdrawn with its premise); markdownlint
on every changed document; a re-run of the P-020 assessment confirming the
recursive counts are now reported per directory; SHIP-5 task 3a's truncation guard
run green over every artifact task 3 produces (**H4**).

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

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass.`
Every selected persona was covered inline against the Persona Rubric Adapter and normalized to
the P0–P3 scale; no persona was skipped. Declared, not silent.

**Plan hardening (P-006): required — `no`.** Not triggered (documentation and
backlog state only; after the cycle-1 correction this shipment mutates no git
index and no source, schema, or distribution surface — the blast radius is
strictly *smaller* than at cycle 0). Constraints **H1**–**H5** are recorded as
binding regardless, and each is propagated into a task acceptance criterion.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Correctness | inline persona pass | 1 P1 (cycle 0), 1 P1 (cycle 1) |
| Maintainability | inline persona pass | 1 P1 (cycle 0) |
| Constitution | inline persona pass | 1 P1 (cycle 0), 1 P1 (cycle 1) |
| Security | inline persona pass | 1 P3 (cycle 0), 1 P1 (cycle 1) |
| Scope boundary | inline persona pass | 1 P2 (cycle 0) |
| Template integrity | inline persona pass | 1 P2 (cycle 0) |
| Architecture | inline persona pass | 1 P2 (cycle 0), 1 P2 (cycle 1) |
| Schema/CLI/docs coupling | inline persona pass | 1 P2 (cycle 1) |

### Review-fix cycle 1 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 8 | Correctness | **P1** | `01340569`'s stated precondition is false on both claims: `.gitignore` contains **no** `.backlogit/checkpoints/` rule (`git check-ignore` exits 1), and **19** checkpoint files are tracked, not five. Every downstream conclusion rested on that premise. | **Resolved.** The premise is corrected in-place with the measurements, the "lying ignore rule" defect is withdrawn as non-existent, and the direction is reversed to the non-destructive **keep-tracked, change-nothing** option. |
| 9 | Security / Constitution | **P1** | `git rm --cached` was treated as approved-and-safe, needing only an on-disk survival check. It is a destructive index mutation, and this run holds **merge** preauthorization only — which never implies authority to execute destructive commands. | **Resolved by the rewritten H2.** The destructive path is removed from the shipment entirely; any future untracking requires a **distinct explicit operator approval at execution time**, and fails closed under AFK/dark mode. Nothing is run now. |
| 10 | Schema/CLI/docs coupling | P2 | The SHIP-5 → SHIP-9 relationship was carried only as a prose remark inside a plan-review finding, indistinguishable from shipment-chain ordering. | **Resolved by H4.** It is a genuine artifact dependency (SHIP-9 task 3 consumes SHIP-5 task 3a's truncation guard) and is now encoded as a real `blocks` edge with the guard named in task 3's acceptance. |
| 11 | Architecture | P2 | Task 3's Part A/Part B pairing was justified as "both tracking/tree-state operations". After the correction Part B mutates no tree state, so that rationale is void. | **Resolved.** The rationale is replaced honestly: Part B is retained only because it is a short record-only decision with no surface of its own, and it is explicitly bounded to writing the decision down. |

**Verdict: PASS.** Cycle 1: 2 P1 raised, both resolved; 2 P2 dispositioned.
Cumulative: **zero unresolved P0/P1**. Two review-fix cycles of three consumed.
