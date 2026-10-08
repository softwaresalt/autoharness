---
title: "Copilot review-body findings have no review thread: read every review body, not only the threads"
problem_type: review-process
category: workflow
root_cause: "Copilot's overview-style review (ccr-overview-v2) can report a finding only in a collapsed \"Previously missed\" section of the review body, under a \"0 open findings\" headline, with no inline comment and therefore no review thread. The thread-based handling loop (reply, then resolve) and the P-018 copilot-review gate both key on threads, so such a finding passes every thread check while still being an unaddressed valid finding."
tags: [p-018, p-021, copilot-review, shadow-review, review-fix-cycle, dark-mode, pr-automation]
shipment: 169-S
date: 2026-10-08
source: docs/compound/2026-10-08-copilot-review-body-findings-without-threads.md
doc_type: learning
---

## Problem

PR #506 (169-S / 161-F) had six Copilot review rounds. Round 1 left one inline
comment, which became one review thread. Rounds 2 to 5 each left **0 inline
comments and 0 threads**, and each review body's headline still read
**"0 open findings"**, yet each body carried a collapsed **"Previously missed (1)"**
section ("In code that hasn't changed since last review") with one valid,
in-scope finding:

* Round 2 (`fb68e399`): a stale `active` Phase-A checkpoint committed on the branch.
* Round 3 (`b879a045`): a test-reader that silently let a duplicate table row win.
* Round 4 (`24d5fc13`): a test fixture that left a duplicate in place, so the case it
  named was not isolated.
* Round 5 (`a5e571a5`): a skill sentence that overstated a Safe-Close guarantee.

Each round's `autoharness gate copilot-review` result was a PASS, because the gate
checks for a current-HEAD Copilot review and for unresolved Copilot-authored
threads. A review-body finding is neither, and the "0 open findings" headline
does not count it. A loop that only walks `reviewThreads`, or only reads the
headline, would have merged with four valid findings unaddressed.

## Solution

* **Read the review body every round.** After each Copilot review of the
  current HEAD, read the review's `body` as well as its threads. Treat any
  finding in the body (including a collapsed or "previously missed" item) as a
  review comment for the categorization in §1.3 of
  `github-pr-automation.instructions.md`.
* **Handle it without a thread.** There is nothing to reply to or resolve.
  Fix or defer it exactly like a threaded finding (P-021 C1 classification,
  C2 capture first for out-of-scope items), push the fix, and then post a PR
  comment that quotes the finding and cites the fixing commit SHA (or the
  deferred stash ID). That PR comment is the audit trail that a thread reply
  normally provides.
* **Count it as a review-fix cycle.** A review-body finding fixed by a push is
  a cycle like any other. In PR #506, rounds 1 to 3 used the three-cycle limit;
  the round-4 finding was valid and in scope, so Ship held the merge and
  asked the operator rather than fix past the limit or defer an in-scope
  finding (P-021 C3/C4). The operator authorized an extension, recorded in a
  PR comment, and rounds 4 and 5 were fixed under it.
* **Define a clean round on the body too.** The "0 open findings" headline is
  not enough. A round is clean only when the review of the current HEAD has no
  open threads **and** its body has neither an open finding nor a
  "Previously missed" section. Round 6 (`c2e6b48e`) met both, and only then was
  the PR presented for merge.
* **Remember that each push re-arms Copilot.** Every fix push starts a new
  round, and the new round may find something an earlier round missed. Budget
  the operator's round allowance (here six) up front.

## Prevention

* When recording shadow-review outcomes in a Local Review Readiness block, list
  inline comments, threads **and** review-body findings per round, so a
  body-only finding cannot be reported as "0 comments".
* Copilot's overview line ("Needs a closer look", "requires human
  sign-off") is a risk note, not a finding. Record it, and treat the
  operator's P-017 pre-authorization as the sign-off, but do not count it as an
  open finding.

## References

* PR #506 comments of 2026-10-08 (rounds 2 to 5 dispositions and the
  operator-authorized cycle extension).
* `docs/closure/169-S-161-F-post-merge-closure.md` (Copilot rounds summary).
* `.github/instructions/github-pr-automation.instructions.md` §1.3 to §1.8 and
  §1.9.4 Check 5 (P-018).
