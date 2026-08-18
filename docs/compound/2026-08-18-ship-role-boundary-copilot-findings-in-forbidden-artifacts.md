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
4. Resolve the GraphQL thread (`resolveReviewThread` mutation) once the
   reply is posted — an unresolved-but-explained thread still counts as
   "unresolved" for P-018 purposes and will block merge.
5. **Never edit the forbidden artifact directly**, even for a trivial
   one-character fix. Doing so is a P-010 violation regardless of how minor
   or "obviously correct" the edit would be.

This is the same posture as the stop-condition language "Accept P2/P3 as
follow-up backlog items" — except here there is no backlog item to open
because the finding is about an artifact's own accuracy, not a new defect
requiring new tracked work; a reply-with-rationale is the correct sized
response.

## Applicability

Any Ship session running a docs/backlog-only staging PR (or any PR that
happens to touch Stage-authored planning artifacts as part of a larger
change) should expect Copilot to find real issues in that content and should
default to this reply-classify-resolve pattern rather than either (a)
silently editing forbidden content to "just fix it," or (b) leaving the
thread unresolved and blocking on P-018 indefinitely.
