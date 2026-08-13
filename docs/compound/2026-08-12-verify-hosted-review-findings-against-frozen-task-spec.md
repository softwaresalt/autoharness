---
shipment: 128-S
feature: 119-F
category: review-process
tags: [copilot-review, false-positive, frozen-spec, task-acceptance-criteria, ship-agent, p-018, review-loop]
---

# Verify hosted-review findings against the frozen task spec before fixing or dismissing

## Problem

Hosted Copilot review on PR #328 (shipment `128-S`, supervision core
library — session state machine, PTY/process adapters, recovery/restart,
redacted journal) surfaced two findings that, read in isolation against
the diff, looked like genuine bugs:

1. `session.py:75` — Copilot suggested adding a direct transition edge
   from `DRAINING` (or an adjacent pre-terminal state) straight to
   `FAILED`, arguing the existing transition table forced an unnecessary
   detour through `CANCELLING`.
2. `recovery.py:136` — Copilot flagged the unconditional lock release in
   `cancel_session`'s `finally` block as a potential double-release /
   release-without-ownership bug.

Both are exactly the shape of finding a reviewer (human or hosted) will
raise with high confidence from the diff alone, and both would have been
easy to "fix" reflexively to close out a review thread quickly.

## Resolution

Before accepting or dismissing either finding, the frozen backlogit task
spec was fetched directly (`backlogit get 119.003-T` and
`backlogit get 119.006-T`) and checked against literal acceptance-criteria
wording rather than trusting Copilot's framing of the diff:

- `119.003-T` explicitly requires "no direct failure edge from
  BOOTSTRAPPING/PREFLIGHT/RESOLVING/LAUNCHING to FAILED" — all failures
  must route through `CANCELLING -> DRAINING -> FAILED`. The existing
  transition table already satisfies this; Copilot's suggested direct edge
  would have **violated** the frozen spec, not fixed a bug.
- `119.006-T` requires (F22) that "no path can strand" the session lock —
  i.e. the lock release in `cancel_session`'s `finally` must be
  unconditional precisely so that no early-return or exception path can
  leave the lock held. The unconditional release Copilot flagged was the
  **spec-required** behavior, not a defect.

Both findings were confirmed false positives, replied to on their review
threads with the specific spec citation, and the threads were resolved
without code changes. Five other findings from the same review rounds
*were* genuine and were fixed (see PR #328 body and
`docs/closure/128-S-119-F-post-merge-closure.md` for the full list).

## Generalizable Lesson

When a task's acceptance criteria were authored to deliberately forbid a
"natural-looking" code shape (e.g. a shortcut edge in a state machine, an
early conditional release in a cleanup path), a hosted reviewer with only
diff-level context will very likely recommend exactly that shape as a fix.
**Before fixing or dismissing any hosted-review finding on a task with a
frozen, acceptance-criteria-bearing spec, fetch the actual spec text
(`backlogit get <task-id>`) and check the finding's suggested change
against the literal acceptance-criteria wording — not against general
code-quality intuition.** This is cheap (one CLI call) and prevents two
failure modes: (a) reflexively "fixing" spec-conformant code into a spec
violation to satisfy a reviewer, and (b) reflexively dismissing a finding
as "intentional" without actually checking whether it is.

This is the second and third confirmed instance of this pattern in this
repository's Copilot-supervisor shipment sequence (a fourth-instance
review of a state-machine/lock-invariant finding); teams building strict
state machines or resource-lifecycle invariants under active hosted review
should expect this finding shape recurrently and should keep the frozen
spec one command away during review triage.
