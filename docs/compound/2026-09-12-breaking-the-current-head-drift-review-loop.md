---
title: "Breaking the current-HEAD-drift Copilot review loop: separate the code-affecting fix commit from the evidence-anchor-refresh commit"
problem_type: review-coverage-gap
category: hosted-review-pattern-learning
root_cause: "A closure/runtime-verification artifact that commits a specific 'current HEAD' SHA and test count is stale the instant a later commit lands, because the anchor-refresh commit itself is one more commit past what it names. Trying to fix this by rewriting the anchor to the newest SHA in the SAME commit that also changes code is self-referential and can never converge: the commit's own SHA is unknown until after it is created. PR #446 (162-S) hit this three separate times (rounds 3->5 currency-model adoption, rounds 6->9 anchor re-staleness) before applying the fix documented here."
resolution_type: process
severity: medium
component: "Ship agent / operational-closure skill / runtime-verification skill / closure artifact convention"
related_pr: 446
related_shipment: 162-S
related_feature: 154-F
doc_type: learning
source: docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md
tags:
  - copilot-review
  - review-pattern
  - evidence-consistency
  - p-018
  - p-021
  - compound-learning
  - closure-evidence
  - current-head-drift
  - self-referential-fixed-point-identity
citations:
  - "PR #446 (SHIP-4: review-persona, policy, and agent-architecture contract integrity), 9 rounds of Copilot review, 24 threads (24 resolved)"
  - "docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md (the general taxonomy this instance confirms; class: current-HEAD readiness drift)"
  - "docs/closure/160-S-152-F-post-merge-closure.md (prior art: the Evidence Currency Model this session adopted, then had to extend)"
  - "docs/closure/2026-09-11-162-s-154-f-closure.md, docs/closure/2026-09-11-162-s-154-f-runtime-verification.md"
---

# Breaking the current-HEAD-drift Copilot review loop with a code-affecting/evidence-only commit split

## Problem

Closure and runtime-verification artifacts record a `last_code_affecting_head`
anchor plus dependent evidence (test counts, verdicts). Every time a review-fix
round lands a new commit, Copilot's next review correctly observes that the
anchor is now one commit stale relative to the PR's actual current HEAD, and
flags it. The naive fix — rewrite the anchor to name the very commit that
carries the fix — cannot work: a commit cannot know its own SHA while it is
being authored, so the anchor written into that commit is, by construction,
naming a hash the file cannot yet reference for itself, and reviewers (or a
future reader) can trivially observe the file is "about" a commit that hasn't
happened yet from the file's own perspective. Attempting this repeatedly (as
happened across rounds 3-9 of PR #446, and previously across rounds 15-17 of
PR #436, see the cited taxonomy) produces an unbounded loop: content fix ->
anchor rewrite -> new commit -> anchor now stale again -> repeat.

## Root Cause

The confusion is conflating two different things that both get called
"the current commit":

1. The commit that most recently changed **evaluable content** (template,
   policy, instruction, skill, or test source) — call this the
   **code-affecting commit**. Its test/build/CI evidence is real and
   verifiable.
2. The commit that most recently changed **the anchor pointing at (1)** —
   call this the **evidence-only commit**. It is, by definition, a *later*
   commit than (1), and it never needs its own test/build evidence beyond
   "no code changed here."

A single artifact trying to be both self-describing and always-current
conflates these two roles and chases its own tail.

## Fix

Split every anchor-refresh into its own, separate, evidence-only commit that
lands **after** the code-affecting commit it points to:

1. Land the actual content fix (template/policy/skill/test change) as its own
   commit. Run the full build/test suite against it. Do **not** touch any
   closure/runtime-verification artifact in this commit.
2. Note that commit's own SHA (now knowable, since it already exists).
3. In a **separate**, immediately-following commit, update
   `last_code_affecting_head` (and any dependent test-count/evidence prose) in
   the closure/runtime-verification artifacts to point at the SHA from step 2.
   This second commit touches **only** doc/evidence text — never any
   evaluable content — so per the artifact's own Evidence Currency Model rule
   ("the anchor is refreshed only when a code-affecting commit lands"), this
   commit correctly does **not** need to reference its own SHA. It is
   evidence-only, and its own existence doesn't retroactively make itself
   "code-affecting."
4. If a subsequent round finds the **PR body's** readiness block (which is
   *not* a git commit — it's a live, editable PR field) has fallen behind the
   already-correct committed artifacts, that is a **separate, cheaper**
   reconciliation: update the PR body to match the committed anchors. No new
   commit is needed for this, since the PR body isn't part of git history.

This converges in exactly two steps (content commit, then anchor commit) per
round, instead of an unbounded chase, because the anchor commit's job is
never to describe itself.

## Applicability

Any Ship-produced closure/runtime-verification/operational-closure artifact
that names a specific commit SHA and dependent evidence as "current" for an
open PR is subject to this same drift under repeated hosted review. Apply the
code-affecting/evidence-only split from the first anchor write, not after
the first complaint — PR #446 needed three iterations of "fix, then get told
it's stale again" before landing on this pattern; a future shipment should
adopt it immediately whenever a closure artifact is created **while the PR
is still receiving remediation commits** (i.e., before the review-fix loop
has fully converged), rather than waiting for hosted review to point out the
staleness.
