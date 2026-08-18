---
title: "Ship replies-not-edits when Copilot flags valid defects in P-010-forbidden artifacts"
description: "When a Copilot review comment on a Ship-owned PR correctly identifies a defect that lives in content Ship's role boundary forbids editing (backlog acceptance-criteria fields, plan/hardening/review docs), the correct resolution is verify + reply + classify + GraphQL-resolve — never a direct edit, even a trivial one-line correction."
problem_type: "process-gap"
category: "role-boundary-enforcement"
component: "ship-agent-pr-lifecycle"
root_cause: "Copilot review operates on the full diff of a docs/backlog-only PR without knowledge of Ship's P-010 role boundary; it will flag genuine, low-severity inaccuracies (e.g. an off-by-one test count) inside plan/review/acceptance-criteria content that only Stage is authorized to author or correct."
resolution_type: "pattern"
severity: "low"
tags:
  - "ship"
  - "role-boundary"
  - "P-010"
  - "copilot-review"
  - "pr-lifecycle"
citations:
  - "PR #359 (140-S staging), review threads on comment IDs 3801315727 and two others"
  - "Shipment 140-S"
---

# Ship Replies-Not-Edits When Copilot Flags Valid Defects in Forbidden Artifacts

## Context

During the staging PR (#359) for shipment 140-S, Copilot review posted three
threads against a docs/backlog-only PR:

1. Two threads flagging the same off-by-one test-count claim ("95" instead of
   the correct "94") — one in a plan doc, one in the task's acceptance
   criteria (`131.001-T`, at the time still `.backlogit/queue/131.001-T.md`,
   since archived to `.backlogit/archive/131.001-T.md` on task completion).
2. One thread flagging that the hardening doc's H3 claim conflates two
   different guard mechanisms (a real, if minor, analytical imprecision).

All three findings were **factually correct** on independent verification
(direct `grep -c "def test_"` count confirmed 93 existing + 1 new = 94, not
95; the H3 conflation was confirmed by re-reading the actual code path). But
all three findings live in artifact categories Ship's Role Boundary table
explicitly forbids editing: backlog acceptance-criteria fields and
plan/hardening/review documents belong to Stage, not Ship, even when Ship is
the one holding the PR open for merge.

## The rule

When a Copilot (or any hosted reviewer) finding is:

* **valid** (verified independently, not just plausible), **and**
* **located in an artifact Ship's Role Boundary forbids editing**,

the resolution is:

1. Verify the finding against source of truth (re-count, re-read the
   referenced code) — do not take the review comment's claim at face value,
   but do not dismiss it either.
2. Reply on the thread (file-based `-F body=@path`, never an inline
   double-quoted string with backticks — see the separate PowerShell
   backtick-mangling compound doc) explaining: the finding is accurate, the
   correct fact (e.g. "94, not 95"), and that the artifact lives outside
   Ship's edit authority (cite the Role Boundary table category).
3. Classify severity per the standard review taxonomy — a documentation/
   acceptance-criteria inaccuracy that doesn't affect actual code
   correctness is P2/P3, non-blocking.
4. **Record a visible, owner-tracked correction/residual-risk note before
   resolving** (revised in PR #361 remediation — see Retroactive Note
   below): a verified-valid finding must never be resolved while the
   underlying defect is left both uncorrected AND untracked, since a
   silently-resolved thread lets P-018 pass while a known inaccuracy
   remains permanently in `main` with no visible follow-up. Either:
   * hand off an explicit, concrete correction/follow-up request to the
     owning agent (Stage, for plan/review/acceptance-criteria content) —
     Ship never invents a backlog ID for this handoff, only names the
     artifact and the exact correction needed; or
   * if no owning-agent handoff is practical in the moment (e.g. the
     artifact is already archived/historical and a live Stage session
     isn't available), record the residual explicitly in a Ship-authored
     compound-learning or closure-artifact residual-risk note (both squarely
     within Ship's Role Boundary for documentation/knowledge) naming the
     artifact, the specific inaccuracy, and that a Stage-owned correction
     remains outstanding.
   P-010 still requires redirecting the actual *correction* work to Stage;
   this step only requires that the redirection/residual be **visible and
   tracked** somewhere durable, never silently dropped once the thread is
   resolved.
5. Resolve the GraphQL thread (`resolveReviewThread` mutation) once the
   reply **and** the tracked correction/residual-risk record above are both
   in place — an unresolved-but-explained thread still counts as
   "unresolved" for P-018 purposes and will block merge, but resolving
   without step 4's tracked record recreates the exact gap this revision
   closes.
6. **Never edit the forbidden artifact directly**, even for a trivial
   one-character fix. Doing so is a P-010 violation regardless of how minor
   or "obviously correct" the edit would be.

This is the same posture as the stop-condition language "Accept P2/P3 as
follow-up backlog items," refined further: even when there is no new
backlog item to open (the finding is about an artifact's own accuracy, not
a new code defect), a reply-with-rationale alone is no longer sufficient —
the correction/residual must also be visibly tracked (step 4) before the
thread is resolved, so a known inaccuracy never disappears from view simply
because its hosting thread closed.

## Applicability

Any Ship session running a docs/backlog-only staging PR (or any PR that
happens to touch Stage-authored planning artifacts as part of a larger
change) should expect Copilot to find real issues in that content and should
default to this reply-classify-track-resolve pattern rather than either (a)
silently editing forbidden content to "just fix it," (b) leaving the thread
unresolved and blocking on P-018 indefinitely, or (c) resolving with a reply
but no tracked residual record.

## Retroactive Note (added in PR #361 remediation, 2026-08-18)

This compound doc's rule was revised (see "The rule" above, step 4) after a
Copilot review finding on PR #361 observed that the original version of this
pattern permitted resolving a verified-valid finding while leaving the
underlying defect both uncorrected and untracked.

The three PR #359 threads that originally motivated this pattern were
replied to and GraphQL-resolved under the **prior, weaker** version of this
rule, which did not require a tracked correction/residual-risk record. As of
this note, the two underlying documentation inaccuracies they identified
remain **uncorrected** in their respective Stage-owned artifacts:

* An off-by-one test-count claim ("95" instead of the verified-correct "94")
  in a Stage-authored plan/hardening doc and in `131.001-T`'s
  acceptance-criteria field (`131.001-T` is now archived at
  `.backlogit/archive/131.001-T.md`, having completed as a task).
* An H3 analytical claim in the hardening doc conflating two distinct guard
  mechanisms.

Per Ship's Role Boundary, Ship does not edit plan/hardening/review documents
or backlog acceptance-criteria fields, and does not open backlog items
(P-010) — so Ship cannot correct these itself and does not invent a backlog
ID here. **A Stage session should open a small correction follow-up
covering these two specific inaccuracies** the next time it triages or plans
against the artifacts in question. This note is the visible, tracked residual
required by the revised rule; it does not block PR #361 (which is a
distinct shipment, 140-S/131-F, already merged via PR #360 with its own
clean zero-thread Copilot review) and is reported to the operator as an open
item rather than silently left implicit.

