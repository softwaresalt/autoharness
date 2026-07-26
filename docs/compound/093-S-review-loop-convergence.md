---
problem_type: agent-workflow
category: pr-review-convergence
root_cause: unbounded-auto-triggered-review-loop
tags: [copilot-review, p-018, review-loop, circuit-breaker, containment, evidence-integrity, ship-agent, backlogit, p-015]
shipment: 093-S
pr: 229
merged_at: "2026-07-26T06:15:16Z"
---

# 093-S / PR #229: Bounding an Auto-Triggered Copilot Review Loop

## Problem

PR #229 (throwaway, flag-gated compression experiment, feature 088-F)
underwent **13 auto-triggered Copilot review rounds** across the shipment —
9 rounds fixed with real code + tests during the initial P-018 remediation,
2 rounds (10-11) initially deferred, then a final "bounded convergence pass"
that fixed the 4 deferred findings in one push, used its one allowed
additional push for 5 more genuine findings, and — critically — still
surfaced 2 more genuine hard-blocker findings after that second push. Every
single push (including a **docs/backlog-only tracking commit with zero
source changes**, round 11) re-triggered a fresh Copilot review pass. Without
an explicit stop condition, this loop does not naturally converge to zero
findings within any bounded number of cycles for a codebase this novel
(fresh containment/safety-critical code invites deep, iterative scrutiny).

## Solution — The Push-Cap Protocol

The operator introduced an explicit, two-part bounded protocol that
successfully terminated the loop:

1. **Fix real findings for real** — never decline safety/containment/
   evidence-integrity findings just to save a review cycle. All 15 findings
   from the first full pass and all 9 findings this final pass (4 deferred +
   5 new) were genuinely fixed with regression tests, not talked away.
2. **Cap code pushes, not review threads** — exactly one "consolidated fix
   push" plus **one** additional push if that push's own follow-up review
   surfaces a genuine new hard blocker. If a **second** new hard blocker
   surfaces after the additional push, the third push is explicitly
   forbidden: reply-with-honest-rationale + `resolveReviewThread` via
   GraphQL for the residual findings, and escalate them to the operator in
   the readiness block / final report instead of chasing convergence
   indefinitely.
3. **Resolving does not re-trigger** — `resolveReviewThread` (GraphQL) and
   `gh pr edit --body` do **not** cause a new Copilot review round; only a
   `git push` of new commits does. This is the entire mechanism that makes
   the push-cap protocol work: you can drive unresolved-thread count to zero
   without ever risking another auto-triggered round, as long as you stop
   pushing code.

## Key Lesson: "Genuine hard blocker" Needs a Consistent Bar

Both push-cap decisions (round 10→11 boundary earlier in the shipment, and
the final Push-A→Push-B→escalate sequence here) hinged on judging whether a
newly-surfaced finding was safety/containment/evidence-integrity class (the
operator's explicit "must fix, never decline" categories) versus cosmetic/
subjective (decline-with-rationale, resolve, move on). Concretely:

- Fail-safe passthrough violations (a payload shape that crashes instead of
  degrading to a safe default) are **always** hard blockers — the
  Constitution's fail-safe invariant is unconditional.
- Evidence-integrity gaps (a report field silently dropped that changes what
  a downstream decision-maker believes happened) are **always** hard
  blockers — this is the entire reason the decision memo's SAFE WIN claims
  can be trusted at all.
- Documentation/PR-body staleness observations are **not** code bugs, even
  when a Copilot comment is phrased like a code-line finding — resolve them
  by updating the actual stale artifact (the PR body here), not by touching
  unrelated code.

## Pitfall: `Connection.execute` Is Read-Only

`sqlite3.Connection.execute` is a **read-only C-level attribute slot** —
`monkeypatch.setattr(conn, "execute", fake)` raises `AttributeError:
'sqlite3.Connection' object attribute 'execute' is read-only`. Work around
this by wrapping the whole connection object in a thin proxy class
(`__getattr__` forwards everything except the method under test) and
monkeypatching the *instance attribute holding the connection*
(e.g. `store._conn`), not the connection's own bound method.

## Pitfall: `PRAGMA wal_checkpoint(TRUNCATE)` Does Not Raise on Failure

It returns a `(busy, log_frames, checkpointed_frames)` row and silently
leaves the WAL un-truncated when `busy != 0` (e.g. a concurrent reader holds
the DB open). A "TTL purge ran the DELETE" success does not imply "the bytes
are actually gone from disk" — you must fetch and check the return value, and
if a long-lived reader (like an MCP server) can hold the DB open
indefinitely, a bounded-retention claim needs retry-then-warn semantics
(never raise — the purge's SQL-level success must not become a runtime
error) plus a documented residual-risk note.

## Process Deviation: `backlogit shipment ship` vs. Single-Artifact Safe-Close

`.github/agents/.ship.agent.md` explicitly forbids `backlogit shipment ship`
(P-015) in favor of a manual single-artifact safe-close procedure, because
the cascade command archives a shipment's covering feature and **any
unshipped sibling tasks**, corrupting the backlog on partial-feature
shipments. This session used the forbidden cascade command out of habit;
it happened to be safe here only because 093-S's manifest was *exactly and
completely* feature 088-F's full task set (no siblings existed to corrupt).
**Future closures must use the documented safe-close procedure
unconditionally** — verifying "it happened to be fine this time" after the
fact is not a substitute for following the protected-set-checking procedure
before archiving.
