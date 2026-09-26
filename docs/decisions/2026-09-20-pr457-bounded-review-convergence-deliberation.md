---
title: "Bounded review convergence for PR #457: freeze semantics at the reviewed local HEAD and cap remediation at two pushes"
description: "Stage decision governing the non-convergent review loop on PR #457. Diagnoses the loop as a structural property of a portfolio whose semantics are duplicated across plan, feature, task, shipment, decision and mutable verdict surfaces, combined with a review that restarts on every push. Freezes semantics at locally-reviewed HEAD 68e77668, adopts a two-push cap (Push A = the complete consolidated local remediation, Push B = at most one consolidated correction for genuinely new merge blockers), defines an explicit comment-classification matrix, redefines P-018 completion as thread-based rather than zero-finding-based, fixes a deterministic merge-ready acceptance matrix, and makes HALTED the defined outcome when the cap is exhausted. Distinguishes publication readiness from execution readiness: merging reviewed Stage artifacts confers no Ship claim authority."
doc_type: decision
source: docs/decisions/2026-09-20-pr457-bounded-review-convergence-deliberation.md
date: 2026-09-20
status: decided
decision_status: decided
promoted_to: none
promoted_to_note: "No backlog link. This decision governs the disposition of an already-open pull request, not future implementation work. Any follow-up work it surfaces is captured as P-021 deferred-expansion stash entries by the executing session, not by this artifact."
depth: standard
deciders: operator, Stage
pr: 457
pr_remote_head: a55bd5a69671c1d5fb882d97862d176b6941981e
reviewed_local_head: 68e7766804f57037ccc9808c1458d4132cbd9f02
branch: chore/stage-176-s-workflow-defects
scope: publication-readiness
policies: [P-018, P-021, P-009, P-016, P-014, P-005]
prior_learnings:
  - docs/compound/093-S-review-loop-convergence.md
optimizes_for: bounded-truthful-outcome
guarantees_merge: false
---

# Bounded review convergence for PR #457

## Problem frame

PR #457 publishes a Stage portfolio re-slice: plans, plan-review verdict
manifests, shipment records, backlog records and a governing decision. Its
review loop is not converging. The remote head has carried 11 unresolved
Copilot threads while the branch has advanced by a full consolidated
remediation series locally, and every prior instinct — publish, read the new
findings, fix them, publish again — reliably produces a fresh non-empty
finding set rather than an empty one.

The loop is not failing because the findings are wrong or because the fixes
are weak. It is failing because **the termination condition in use ("zero
Copilot comments") is not reachable in bounded time for this artifact class**,
while the condition that actually gates merge (P-018: current-HEAD review
complete, zero *unresolved threads*) is reachable without any further push.
This decision replaces the unreachable condition with the reachable one and
puts a hard cap on the remaining push budget.

This protocol optimizes for a **bounded truthful outcome**, not for a
guaranteed merge. Its two permitted terminal states are MERGED and HALTED,
and HALTED is a success of the protocol, not a failure of it.

## Observed root causes

**R1 — Semantics are duplicated across six surfaces.** One contract truth
(for example "188-S is the bootstrap root and 187-S is gated on it") is
restated in the plan, the feature record, the task records, the shipment
record, the governing decision and the mutable verdict manifest. Correcting
the statement on one surface makes a neighboring surface false. Finding
supply therefore scales with the number of carrier surfaces, not with the
number of real defects — the 11 original threads reduced to four defect
families, and one of those families was true of 27 records rather than the
4 flagged.

**R2 — Review restarts on every push, including docs-only pushes.** P-018 is
by-construction multi-round: a new HEAD re-arms the gate and re-triggers a
full review pass. A push made *to fix* findings is indistinguishable, to the
trigger, from a push that introduces them. The fix rate and the
finding-generation rate are not ordered, so the loop has no natural fixpoint.
This is the same mechanism recorded in `docs/compound/093-S-review-loop-convergence.md`,
where 13 auto-triggered rounds still surfaced genuine new findings after the
second capped push.

**R3 — The verdict surface is itself reviewable prose.** A mutable verdict
manifest is an artifact that selects which immutable attempt record is
authoritative. Because it is prose, it can contradict what it selects, and
that contradiction is a legitimate finding. Reviewing the review generates
findings at the same rate as reviewing the plan (open P3 items J5, B5 and B6
are exactly this shape).

**R4 — P3 prose-consistency findings are in unbounded supply.** Across a
27-record family, "this sentence is stale relative to that sentence" is a
finding template with dozens of valid instantiations. No finite fix pass
retires the template.

**R5 — Pre-push finding chasing has no terminal condition.** Five independent
local plan-review attempts and eleven commits were consumed reaching terminal
PASS. Each remediation revision legitimately invited a further attempt. The
local loop converged only because terminal attempts were declared; the remote
loop has never had an equivalent declaration.

**R6 — Publication readiness and execution readiness are conflated.** Pressure
to make the merged artifact set "correct enough to execute" pulls
execution-gate concerns (topology, pre-claim, dependency clearance) into a
review whose actual subject is whether the documents are true and safe to
publish. This inflates the blocker bar and, with it, the push count.

## Current state

| Surface | Current state |
|---|---|
| PR #457 | OPEN, `MERGEABLE`, no review decision recorded |
| Remote head | `a55bd5a6` — stale relative to the branch |
| Copilot threads on remote head | 11 unresolved |
| CI | Green, but green **on `a55bd5a6`**, not on the reviewed content |
| Local head | `68e77668`, branch `chore/stage-176-s-workflow-defects`, 11 commits ahead, unpublished |
| Local series content | One consolidated remediation addressing all 11 original threads, plus the bootstrap-root repair and the successor archival |
| Bootstrap root 188-S | Added and repaired; plan-review **terminal PASS**, P3-only residue |
| 187-S lifecycle foundation | Plan revision 6; plan-review **terminal attempt 05 PASS**, P3-only residue |
| 181-S / 184-S | Archived as premature conditional successors (fail-closed withholding) |
| Copilot review of `68e77668` | Has never run — the content has never been published |
| Open residue | P3 findings only (J5, B4, B5, B6) plus tracked P-021 deferrals |

The decisive asymmetry: **every gate that has actually been evaluated against
the reviewed content passes, and every gate currently reported against the PR
was evaluated against content that no longer represents the branch.**

## Options considered

**Option A — Unbounded zero-comment loop.** Keep pushing until Copilot
returns no comments. Rejected: R1–R4 make the target unreachable in bounded
time; R2 guarantees each attempt re-arms the trigger; and 093-S is direct
prior evidence that genuine new findings survive past the second push on a
far smaller surface. Cost is unbounded and the outcome is undefined.

**Option B — Merge now.** Merge at the current remote head, or publish and
merge without waiting for the current-HEAD review. Rejected: merging
`a55bd5a6` merges content known to be superseded and leaves 11 threads
unresolved, which is a direct P-018 violation; merging after publication
without awaiting review completion is the same violation with a newer SHA.
It is cheap and fast and it publishes a state we have positive evidence is
wrong.

**Option C — Bounded push cap with thread-based completion.** Freeze
semantics at the reviewed local HEAD, publish once, classify every resulting
comment against an explicit matrix, spend at most one further consolidated
push on genuine current-merge blockers, resolve everything else by evidence
or tracked deferral, and halt deterministically if the cap is exhausted.
**Selected.**

### Tradeoff matrix

| Criterion | A: unbounded loop | B: merge now | C: bounded cap |
|---|---|---|---|
| Terminates in bounded time | No | Yes | Yes (≤2 pushes) |
| Merges content that is actually true | Eventually, maybe | No | Yes |
| P-018 satisfied at merge | Eventually, maybe | No — violated | Yes, or HALTED |
| Real blockers still get fixed | Yes | No | Yes (Push B) |
| Non-blocking findings preserved | Fixed, unboundedly | Lost | Tracked as P-021 / residual-risk |
| Cost | Unbounded | Near zero | ≤2 review rounds |
| Failure mode | Silent non-termination | Publishing a false authoritative state | Explicit HALTED for operator disposition |

## Decision

**D1 — Freeze semantics at the reviewed local HEAD.** Pre-push finding
chasing stops at `68e77668`. No further semantic edits to plans, features,
tasks, shipments, decisions or verdict manifests are made in anticipation of
findings that have not been raised against this content. The only permitted
edits before Push A are **deterministic publication metadata** — the PR body,
the residual-risk/follow-up list, thread replies and thread resolution — none
of which changes HEAD and none of which re-triggers review.

**D2 — Two-push cap.** *Push A* publishes the complete current consolidated
local remediation exactly as it stands, as a fast-forward of the existing
branch — no new commits, no rewrite, no squash. *Push B* is at most one
consolidated correction, spent only if the current-HEAD Copilot review of
Push A surfaces a genuinely new **current-merge blocker** per D3. All such
blockers found in that review are collected and fixed in a single push; Push B
is never spent incrementally.

**D3 — Classify every comment by this matrix.** Classification is per comment,
is recorded in the reply, and determines the response:

| Class | Trigger | Response | Push |
|---|---|---|---|
| **C1 — Already fixed / duplicate / stale** | The finding is true of `a55bd5a6` (or of a superseded revision) and false of the reviewed HEAD, or restates a finding already answered | Reply with **current-HEAD evidence** (file, line, commit), then resolve | None |
| **C2 — Current-merge blocker** | P0 or P1; **or** a P2 that makes a live queued shipment unclaimable, unsafe, unreachable or prematurely executable, or that makes authoritative plan/manifest state materially false | Collect with all other C2 findings from the same review; fix once in **Push B** | Push B only |
| **C3 — Non-blocking advisory / out-of-scope** | P2 not meeting the C2 bar; P3; stylistic, subjective, or scope-expanding | Capture in backlogit **before** replying where P-021 requires deferred-expansion capture; add to the PR residual-risk/follow-up list; reply with the disposition and the tracking ID, then resolve | None |

A finding is never downgraded to avoid a push, and a severity is never lowered
to reach a verdict. The C2 bar is a *merge* bar, not a *promotion* bar: a
finding may be a permanent blocker for later execution and still be correctly
deferred here, provided it is tracked (the 093-S distinction between "hard
blocker for promotion" and "acceptable to defer at merge, tracked").

**D4 — There is no Push C.** After Push B, the push budget is spent. If the
review of Push B surfaces a further genuinely new merge blocker, PR #457 is
declared **HALTED** for operator disposition, or is split/replaced under a
separately authorized workflow. Convergence to zero comments is explicitly
not pursued.

**D5 — P-018 completion is thread-based.** The gate is satisfied when Copilot
has completed a review for the **current** `headRefOid` and every
Copilot-authored thread is resolved. It is not a zero-finding gate. Every
thread must receive a **substantive** reply — current-HEAD evidence, a fix
reference, or a tracked deferral with its ID — and then be resolved. Thread
resolution and PR-body edits do not create a new HEAD and therefore do not
re-trigger review; this is the mechanism that makes the cap workable.

**D6 — Merge-ready is a conjunction, evaluated once.** See the acceptance
matrix. If any condition is false after the push cap is spent, the outcome is
deterministic **HALTED**, not another loop iteration.

**D7 — Publication readiness is not execution readiness.** Merging these
reviewed Stage artifacts authorizes nothing downstream. Each shipment root
still faces its own topology/pre-claim gate and its dependency gates at claim
time. A merged plan with verdict PASS is publication-eligible and
claim-neutral. This separation is what allows the C2 bar to stay narrow
without importing risk.

## Acceptance matrix

Merge proceeds only when **all** of the following are true for the same HEAD:

| # | Condition | Evidence source |
|---|---|---|
| A1 | Remote head equals the reviewed local head | `gh pr view 457 --json headRefOid` vs. local `git rev-parse HEAD` |
| A2 | CI green **on that head** | Required-check status for the same SHA |
| A3 | Copilot review complete for the **current** head | `autoharness gate copilot-review 457` / review state for that SHA |
| A4 | Zero unresolved Copilot threads | Thread resolution state; every thread has a substantive reply |
| A5 | No live queued shipment carries a current merge blocker | C2 classification results across the review |
| A6 | All P2/P3 residue tracked | backlogit entries and the PR residual-risk/follow-up list |
| A7 | Local review readiness block current for that head (P-014) | Local readiness record |
| A8 | P-009 merge-commit-only and P-016 single-branch discipline hold | Merge method; no parallel branch/worktree |

Any `false` after the cap is spent ⇒ **HALTED**.

## Stop conditions

| Counter | Limit | Action on reaching it |
|---|---|---|
| Code pushes to PR #457 under this protocol | 2 (A and B) | No Push C. Declare HALTED or split/replace under separate authorization |
| Consolidated corrections per review round | 1 | Collect all C2 findings from a round; never fix incrementally |
| Pre-push speculative semantic edits | 0 | Semantics frozen at `68e77668`; metadata-only edits permitted |
| Copilot review rounds awaited | 2 (one per push) | Report the outcome of the second round; do not await a third |
| Zero-comment target | Not a stop condition | Never pursued; D5 governs completion |

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| A real defect is misclassified C3 and merges | C2 bar is written as concrete, checkable harm classes (unclaimable / unsafe / unreachable / prematurely executable / materially false authoritative state), not as a severity opinion; every C3 is tracked, never silently dropped |
| Push B is spent on a finding that was actually C1 | C1 requires **current-HEAD** evidence in the reply; if the evidence cannot be produced, the finding is not C1 |
| HALTED is read as failure and reopens the loop | HALTED is a defined terminal outcome of this protocol requiring operator disposition; re-entry requires separate authorization, not agent initiative |
| P3 residue accumulates unmerged and is lost | P-021 capture occurs **before** the reply, so the tracking ID exists at reply time and appears in both the thread and the PR follow-up list |
| Merged artifacts are read as execution authorization | D7 is stated in the decision and restated in the PR body; claim-time gates are unchanged and independent |
| Fast-forward publication is corrupted by a rewrite | Push A publishes `68e77668` exactly; no squash, no rebase, no amend (P-009, P-016) |

## Exact next action

Hand this decision to the operator/Orchestrator, who owns PR actions, and
execute **Push A**: publish branch `chore/stage-176-s-workflow-defects` at
exactly `68e77668` as a fast-forward of remote `a55bd5a6` — no new commits,
no rewrite, no semantic edits. Then wait for CI and for the Copilot review of
that head to complete, and classify every resulting comment under the D3
matrix before any further action. Stage takes no push, no PR mutation and no
thread action in this session.
