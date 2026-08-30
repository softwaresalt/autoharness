---
type: compound-learning
shipment: 157-S
feature: 149-F
date: 2026-08-30
problem_type: premature_review_completion_assumption
category: workflow-issues
root_cause: A stateless single-read `REVIEW_TIMEOUT` verdict with an empty `unresolved_thread_ids` list was treated as equivalent to a completed, clean review, when in fact the hosted Copilot review had simply not finished analyzing at the time of the read -- the absence of listed threads reflects "nothing observed yet," not "nothing found."
resolution_type: workaround
severity: medium
source: docs/compound/2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md
doc_type: learning
title: "REVIEW_TIMEOUT with an empty thread list is not a clean signal"
citations:
  - .github/instructions/github-pr-automation.instructions.md
  - .github/instructions/circuit-breaker.instructions.md
tags:
  - copilot-review
  - p-018
  - workflow-issues
---

# REVIEW_TIMEOUT with an empty thread list is not a clean signal

## Problem

Shipment 157-S (feature 149-F) went through 8 sequential Copilot hosted-review
rounds on PR #420 before reaching `SATISFIED`. Across those rounds,
`autoharness gate copilot-review --max-wait 180-240` frequently returned
`REVIEW_TIMEOUT` on the first attempt after a push, and a second attempt with
a longer wait (`240-300`) then caught the completed review -- which usually
surfaced additional findings beyond what had just been fixed, not merely
confirmation of the prior round. Once (between rounds 6 and 7), a
`REVIEW_TIMEOUT` was observed with an *empty* `unresolved_thread_ids` list,
and the very next retry (still within the same round) surfaced 2 new threads.

## Root Cause

A `REVIEW_TIMEOUT` verdict is produced by a single stateless read of the
hosted review's current state at the moment the wait budget expires. An empty
`unresolved_thread_ids` list at that moment reflects "no threads have been
posted as of this read," which is indistinguishable from "the review will
post zero threads once it finishes" using only that one read. Treating the
empty list as a completed clean result conflates "not yet observed" with
"observed and absent."

## Resolution

Do not treat a `REVIEW_TIMEOUT` with zero listed threads as a clean signal.
Retry with a longer wait to obtain a genuine `SATISFIED` or
`UNRESOLVED_THREADS` verdict (never `REVIEW_TIMEOUT` itself) before
concluding a round is complete. This retry is bounded, not unbounded: retry
only within the remaining budget of the same-operation circuit breaker
(`.github/instructions/circuit-breaker.instructions.md`, three failures of
the identical `copilot-review` gate invocation for the same HEAD). Once that
budget is exhausted, halt and escalate (or, per the Ship pipeline's Fix-CI
stop condition, present the PR with the outstanding pending state for
operator intervention) rather than issuing a further attempt.

## Prevention

When building or operating any gate that polls an asynchronous hosted review
service, distinguish "timed out with no observations yet" from "completed
with zero findings" in both the tool's own verdict semantics and in any
downstream guidance describing how to interpret a timeout. Bound all retry
guidance explicitly against the applicable circuit breaker from the outset,
rather than describing a retry loop in prose that omits the bound.
