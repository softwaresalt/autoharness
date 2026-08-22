---
title: "Newly inserted 'final action' step must be re-verified when a later step is added to the same numbered list"
description: "Adding a new checkpoint-creation step to _stage.agent.md's Session Continuity procedure after an existing step that already claimed to be 'the final action' created a textual self-contradiction (index sync ran first, then a step that runs after it claimed finality) — caught by hosted Copilot review, not local review, on the first pass."
problem_type: "process-pitfall"
category: "documentation-consistency"
component: "stage-agent-instructions"
root_cause: "When a template gains a new ordered step, any pre-existing step in the same list that textually asserts 'this is the final action' (or equivalent ordinal/finality language) becomes stale unless it is either moved after the new step or its finality claim is qualified/removed. The insertion in this case appended the new checkpoint-creation step textually after the step claiming finality, without checking whether the new step's actual required position (before index sync, so a crash between checkpoint-write and index-sync self-heals via re-sync rather than losing the checkpoint pointer) was consistent with where it landed in the list."
resolution_type: "fix"
severity: "low"
tags:
  - "stage"
  - "checkpoint"
  - "instruction-authoring"
  - "self-contradiction"
  - "code-review-caught"
citations:
  - "PR #357 (second Copilot review round)"
  - ".github/agents/_stage.agent.md Step 6 Session Continuity"
  - "Shipment 139-S"
source: docs/compound/2026-08-18-stage-agent-checkpoint-index-sync-ordering-self-contradiction.md
doc_type: learning
---

# A "Final Action" Claim Must Be Re-Verified Whenever a Later Step Is Inserted Into the Same List

## Context

Shipment 139-S's checkpoint-payload-contract work added a new checkpoint
creation step to `.github/agents/_stage.agent.md`'s Session Continuity
procedure (Step 6). The existing item 3 in that list already stated it was
"the final action" (referring to the index-sync call). The new checkpoint
creation step was added as item 4 — textually *after* item 3's finality
claim — even though the checkpoint must be written *before* index sync (so a
crash between the two states self-heals via a subsequent re-sync, rather
than losing the checkpoint's pointer if index sync ran first and the
process died before the checkpoint write landed).

## The mistake

The new step was inserted using ordinary "append after the relevant
existing step" instinct without cross-checking two things at once:
1. Whether any *other* step in the same list makes an ordinal/finality claim
   ("this is the last step", "this runs after everything else", etc.).
2. Whether the new step's own correctness requirement (checkpoint-before-
   sync, for crash-safety) is compatible with the position it was inserted
   at.

Both checks were skipped locally; the contradiction ("item 3 is final" while
"item 4 exists and must run before item 3, semantically") was caught only by
the hosted Copilot reviewer on PR #357, not by the two local adversarial
reviews performed before the PR was opened.

## The rule that should have been followed instead

**Whenever a new step is inserted into an existing ordered/numbered
procedure, grep the same list for ordinal/finality language ("final",
"last", "only after", "always runs after") and verify the new step's
required position doesn't invalidate that claim.** If it does, either:
- reorder so the finality claim is actually true again (what was done
  here — checkpoint creation now precedes index sync), or
- rewrite the finality claim to explicitly name what it excludes.

Local review sessions should specifically scan touched ordered lists for
this class of contradiction — it's a purely textual/structural check (no
runtime behavior to exercise) and is exactly the kind of thing a fast
static read catches, but only if the reviewer is looking for stale ordinal
claims rather than only checking new content in isolation.

## Applicability

Any agent/skill instruction file with an explicitly ordered procedure
(numbered steps, "Step N", checklists with "final"/"last" language) that
receives a new step insertion during unrelated feature work. Before
committing, re-scan the *entire* affected list — not just the diff region —
for finality/ordinal claims that the insertion may have invalidated.
