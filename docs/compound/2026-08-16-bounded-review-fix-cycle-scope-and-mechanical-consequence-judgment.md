---
title: "Bounded review-fix cycle scope: distinguishing 'same contract surface' from 'same file'"
description: "How to judge whether a new Copilot finding during an operator-authorized bounded review-fix exception is in scope, and how to close out-of-scope findings without leaving a P-018 gate blocked"
problem_type: "process-judgment"
category: "workflow-issues"
component: "ship-agent-review-fix-cycle"
root_cause: "A scope-bounded operator exception to a review-fix circuit breaker (Stop Conditions) has no built-in test for whether a subsequent Copilot finding is 'in scope'; a loose relatedness test ('same file/PR/function') would let every follow-on comment relitigate the breaker, while a zero-tolerance test would leave legitimate mechanical consequences of the authorized fix unaddressed."
resolution_type: "workaround"
severity: "medium"
tags:
  - "ship"
  - "review-fix-cycle"
  - "p-018"
  - "circuit-breaker"
  - "scope-boundary"
citations:
  - "PR #348"
  - "docs/closure/pr348-circuit-breaker-diagnostic-escalation-policy-closure.md"
---

# Bounded Review-Fix Cycle Scope: Distinguishing "Same Contract Surface" from "Same File"

## Context

PR #348 went through 7 Copilot review-fix cycles across two Ship sessions.
The circuit-breaker review-fix stop condition (3 cycles per PR) was
deliberately exceeded twice, each time under explicit, narrowly-scoped
operator authorization rather than by the agent unilaterally deciding to keep
going. The pattern that emerged is reusable for any future bounded-cycle
authorization.

## The problem

A Stop Conditions circuit breaker (e.g., "3 review-fix cycles per task/PR")
exists specifically to prevent an agent from treating every new Copilot
comment as automatic license for another commit. But Copilot review is
iterative: fixing one finding often surfaces a new, real finding on the very
next pass (either a mirror bug in the same fix, or a consequence of the fix
itself). Treating *every* subsequent finding as "in scope because it's a
review comment" defeats the circuit breaker's purpose. Treating *no*
subsequent finding as fixable defeats the point of having a review gate at
all. The judgment call is genuinely hard to make consistently without a
sharper rule.

## The rule that worked

When an operator grants a bounded exception ("one more cycle for finding X",
or "further findings limited to the same surface as X"), evaluate each new
finding against a **narrow, literal** test: *does this finding concern the
exact thing X changed, or a different aspect of the same file/PR/subsystem?*

Concretely, in this session:

- Finding: "the shared-instruction verifier doesn't require the field we just
  added" -> **same surface** (the field itself) -> fix it.
- Finding: "the retry-directive regex doesn't handle an object-separated
  form" -> **different surface** (matcher robustness, not the new field) ->
  out of scope, even though it's in the exact same function, same file, same
  PR, and was itself in-scope for an *earlier* authorized cycle.
- Finding: "a policy interaction is unresolved between strict_safety and the
  handoff" -> **different surface and different kind of work** (a design
  decision, not a mechanical fix) -> out of scope.

The distinguishing question is never "is this related to what I just
touched?" (almost everything a reviewer flags on a small PR is *related* in
some loose sense) — it is "does fixing this require only completing the
exact change I was just authorized to make, or does it require original
design/decision work or an unrelated code path?"

## Handling out-of-scope findings without leaving the gate blocked

P-018-style Copilot-review completion gates typically require **zero
unresolved threads**, not **zero threads addressed by a code change**. When a
finding is judged out of scope:

1. Reply to the specific thread with a substantive, honest explanation: what
   the finding is, why it's judged out of scope (cite the operator's exact
   scope boundary), and that no code change was made for it.
2. Resolve the thread via the review-thread resolution mechanism (e.g.
   GraphQL `resolveReviewThread`).
3. Record the finding as disclosed residual risk in the PR body's readiness
   section and in the post-merge closure artifact, so it is not lost — it
   becomes a candidate follow-up rather than a silently dropped comment.

This satisfies the review-completion gate honestly (every thread has a
substantive disposition, not a bare acknowledgement) without either
fabricating unauthorized scope expansion or perpetually blocking merge on
advisory-level (P2/P3) findings that were explicitly bounded out of the
authorized cycle.

## Applicability

Use this pattern whenever an operator grants a scope-bounded exception to a
review-fix or build-fix circuit breaker (Stop Conditions table) rather than
lifting the breaker entirely. The bounding language itself ("same contract
surface", "same finding", "mechanical/directly-consequential only") should be
read literally and narrowly; when genuinely ambiguous, the safer default is
to treat the finding as out of scope and disclose rather than to fix and risk
an unbounded escalation of "just one more cycle."
