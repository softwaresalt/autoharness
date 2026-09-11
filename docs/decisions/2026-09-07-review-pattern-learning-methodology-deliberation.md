---
title: "Deliberation — baking hosted-review pattern learning into the harness workflow"
doc_type: deliberation
problem_type: agent-workflow
category: review-pattern-learning
status: decided
decided_at: "2026-09-07T23:42:58-07:00"
decided_by: stage
source_intake: "operator request 2026-09-07 (compound-learn from Copilot review patterns; proactively detect before PR)"
evidence:
  - docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md
  - docs/reviews/2026-09-07-pr-436-adversarial-review.md
  - docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md
source: docs/decisions/2026-09-07-review-pattern-learning-methodology-deliberation.md
tags: [review, compound-learning, p-018, p-021, reliability, workflow, deliberation]
---

# Deliberation: making hosted-review pattern learning systematic

## Problem statement

The harness currently learns from hosted (Copilot) review **anecdotally**. Six
prior compound entries already record Copilot-review lessons
(`107-S`, `114-S`, `115-S`, `093-S`, `2026-08-12-hosted-review-catches…`,
`2026-09-03-copilot-review-surfaces-latent-parent-id…`). Each was written
after the fact, by whoever happened to notice; none is retrieved *before* the
next PR; and the same classes keep recurring.

PR #436 quantifies the cost: **13 rounds, 56 raw finding utterances, 24
distinct findings, 12 root-cause classes, 100% escape rate past local review
and CI.** Four findings from its final round remain unfixed. Three separate
classes had already been recorded in the compound library **and were not
retrieved before the PR was opened**.

The gap is not knowledge. It is **retrieval, classification, and
promotion discipline**.

## Constraints (must not be broken)

* **P-001 role separation** — Stage plans, Ship executes. No step may let one
  role act for the other.
* **P-018 review gate semantics** unchanged — this adds analysis, not a new
  blocking authority.
* **P-021 capture-only for Ship** — Ship may capture findings; it may not
  edit stash entries or publish backlog records.
* **Bounded review cycles** (`093-S` circuit breaker) — nothing here may
  license additional review rounds.
* **No runtime telemetry engine.** Metrics must be derivable from artifacts
  the workflow already writes.
* **No "one compound file per comment."** Explicitly rejected by the operator.
* Template ↔ dogfood mirror parity and harness manifest checksums must hold.

## Question 1 — Where does *proactive* retrieval belong?

| Option | Placement | Assessment |
|---|---|---|
| **1A** | New always-on `review` persona | Rejected — always-on cost on every diff, most of which is code, not evidence |
| **1B** | Ship agent only, before local readiness | Rejected — misses standalone/interactive `review` invocations and Stage-run analysis |
| **1C** | `review` skill Step 1.5 (after scope, before persona routing), + a **conditional** persona; Ship invokes the same skill | **CHOSEN** |
| **1D** | Learnings Researcher persona expansion only | Rejected — Learnings Researcher searches for *related past issues in the changed code*; pattern retrieval is a different query (class-based, not component-based) |

**Decision 1: 1C.** Pattern retrieval becomes an explicit `review` step that
runs before persona routing, so its output can *influence* routing. Ship gets
it for free because Ship already calls `review`.

**Rationale.** The single most valuable output of retrieval is not a checklist
for the human — it is the decision to **spawn the Evidence Consistency
Reviewer** (Question 2). Retrieval must therefore precede routing.

## Question 2 — Why did every persona miss all 24 findings?

Because **no persona owned evidence coherence**. Constitution, Correctness,
Maintainability, Python, Template Integrity, Schema-CLI-Docs Coupling and
Scope Boundary all review *content*. Every one of PR #436's top classes
(RC-2, RC-5, RC-9, RC-10, RC-11, RC-12) is a property of the *relationship
between artifacts*, invisible in any single hunk.

**Decision 2: add one conditional persona — `Evidence Consistency Reviewer`.**

* **Trigger:** the diff touches `docs/closure/**`, `docs/memory/**`,
  `.backlogit/**`, `docs/reviews/**`, or **any file whose frontmatter carries a
  key read by `src/autoharness/gates/**`**.
* **Rubric:** the 10-point evidence-consistency checklist in the compound
  learning, verbatim.
* **Hard rule:** it reads the **branch tree** (`git show HEAD:<path>`), never
  the working tree.

**Rejected alternative:** folding the rubric into Template Integrity Reviewer.
Rejected because Template Integrity is already the anchor-reviewer default and
carries a large, unrelated rubric; merging would dilute both and make the
degradation story ambiguous.

## Question 3 — RC-9 and RC-11 are *created by remediating*. How?

This is the hardest part and the one a checklist alone cannot solve.
Current-HEAD readiness drift (8 manifestations) and chronology falsification
(8) do not exist when the pre-PR review runs. They come into existence when a
fix commit is written.

| Option | Assessment |
|---|---|
| **3A** Re-run the full local review after every fix commit | Rejected — cost is prohibitive and it re-reviews unchanged code |
| **3B** Nothing; accept the drift | Rejected — this is the status quo that produced 8 recurrences |
| **3C** **Post-fix delta check**: after each review-fix commit, run a bounded, mechanical check of *only* the drift-prone classes (RC-9 SHA equality, RC-10 propagation grep, RC-11 chronology verbs, RC-12 date ordering) | **CHOSEN** |

**Decision 3: 3C.** Four of the twelve classes are cheaply mechanisable
(SHA compare, `git grep` identifier reconciliation, pre-mutation verb scan,
date-ordering assertion). Run exactly those, on the touched files only,
immediately before push. This is seconds of work and covers **19 of PR #436's
56 utterances**.

**Explicitly:** the delta check is **not** a review round and never triggers
one. It is a pre-push self-check, and it is bounded by the same circuit
breaker.

## Question 4 — Where does *synthesis* belong, and what triggers promotion?

**Decision 4a: synthesis at PR closure, once, never per round.**
`pr-lifecycle` gains a "hosted-review finding inventory" step that runs when
the PR reaches a terminal review state. It classifies **threaded *and*
suppressed** findings — reading the review `body` field, per the `114-S`
lesson — and counts recurrences.

**Decision 4b: the bounded promotion threshold.** Promote to a compound
learning only when at least one holds:

1. the root-cause class recurs ≥2× in this PR, or ≥2× across PRs;
2. the finding reveals a cross-contract invariant neither surface states;
3. it escaped local review **and** CI;
4. it is P0/P1 or touches a fail-closed safety gate;
5. **the reviewer itself declares it a recurrence.**

Otherwise: **one-off correction, recorded in the PR Review History and
nowhere else.**

**Decision 4c: consolidate, don't accrete.** If the `root_cause` class already
exists in `docs/compound/`, **append a dated example to that file**. A new
file requires a *new class*. When an entry outgrows itself, split
taxonomy (`docs/compound/`) from evidence (`docs/reviews/`) with bidirectional
frontmatter links — the pattern used by this session's own artifacts.

## Question 5 — Metrics without a telemetry engine

**Decision 5:** five metrics, all derived from artifacts the workflow already
produces (finding inventory, PR Review History, `git log`, stash timestamps),
emitted **once per PR at closure** into the closure record's review section:
recurrence rate, first-detected phase, escaped-to-hosted-review count,
time-to-disposition (**which must be ≥ 0 — this is the RC-12 guard**), and
class coverage.

No runtime instrumentation. No new schema. No new CLI surface.

## Question 6 — Which surfaces change?

| Surface | Change | Why |
|---|---|---|
| `.github/skills/review/SKILL.md` + `templates/skills/review/SKILL.md.tmpl` | Step 1.5 pattern retrieval; Evidence Consistency Reviewer persona + routing rule; post-fix delta check; Stage-run analysis posture (fixes **AF-11**) | Proactive half |
| `.github/skills/pr-lifecycle/SKILL.md` + template | Hosted-review finding inventory step; recurrence classification; compound-learning checkpoint with the bounded threshold | Reactive half |
| `.github/instructions/github-pr-automation.instructions.md` + template | Enumerate **suppressed** findings from review bodies, not only `reviewThreads`; the exact GraphQL/REST retrieval recipe | 64% of PR #436's findings were invisible to thread-only reads |
| `.github/agents/_ship.agent.md` + template | Invoke retrieval before local readiness; invoke synthesis after hosted review/closure; **route Stage-owned data-currency gaps back to Stage before claiming readiness** (fixes **AF-07**'s structural cause) | Ship is the agent that actually runs both ends |
| `.github/instructions/copilot-code-review.instructions.md` | Concise durable pointer to the taxonomy | Smallest possible footprint |
| `tests/` | Template↔dogfood parity assertions; manifest checksum coverage for changed installed files | Prove the methodology is actually carried |

**Explicitly NOT changed:** `AGENTS.md`, `.github/copilot-instructions.md`,
the constitution. A pointer in one instruction file is sufficient; adding
policy text to foundation files for a process improvement is scope creep.

**Learnings Researcher:** unchanged. Its component-based query is
complementary to, not a substitute for, class-based pattern retrieval.

## Decision summary

1. Pattern retrieval → `review` Step 1.5, before persona routing.
2. New conditional `Evidence Consistency Reviewer` persona, 10-point rubric,
   branch-tree reads only.
3. Bounded mechanical **post-fix delta check** for the four drift-prone
   classes; not a review round.
4. Synthesis once at closure; bounded 5-signal promotion threshold;
   consolidate-don't-accrete; taxonomy/evidence split.
5. Five workflow-evidence metrics at closure; no telemetry engine.
6. Six surfaces + tests; foundation files get a pointer only.

## Residual risks

* **Checklist fatigue** — mitigated by making only 4 of 12 classes mandatory
  mechanical checks and the rest rubric-driven.
* **Retrieval returns nothing useful on a code-only PR** — acceptable; the
  conditional persona simply does not trigger.
* **The promotion threshold is judgment-bearing** (signals 2 and 4) —
  accepted; the alternative (pure recurrence counting) misses first-occurrence
  cross-contract invariants like AF-05.
* **This deliberation cannot fix PR #436.** All findings are captured
  (`846D0282`, `0BE73C89`, `9E22BFC6`, `27F9EC8A`, `AFEFC6AB`) and await
  operator disposition.
