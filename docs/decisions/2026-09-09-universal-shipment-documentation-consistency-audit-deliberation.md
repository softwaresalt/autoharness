---
title: "Deliberation — universal shipment documentation consistency audit"
doc_type: deliberation
problem_type: agent-workflow
category: universal-audit-delivery
status: decided
decided_at: "2026-09-09T16:09:52-07:00"
decided_by: stage
source_intake: "operator request 2026-09-09 (stash 8F2FD1F6): the ten-point audit must be a compound learning applied by the harness on every shipment regardless of installed workspace, not a PR-body checklist"
source_stash: 8F2FD1F6
evidence:
  - docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md
  - docs/compound/2026-08-18-stage-agent-checkpoint-index-sync-ordering-self-contradiction.md
  - docs/decisions/2026-09-07-review-pattern-learning-methodology-deliberation.md
  - .backlogit/queue/162.004-T.md
source: docs/decisions/2026-09-09-universal-shipment-documentation-consistency-audit-deliberation.md
tags: [review, compound-learning, universality, template-authoring, p-021, evidence-consistency, deliberation]
---

# Deliberation: making the documentation consistency audit universal

## Problem statement

PR #440 temporarily carried a ten-point documentation consistency checklist in
its **PR body**. The checklist worked — it caught real contradictions — but the
delivery vector was wrong in three ways:

1. **Ephemeral.** It was removed before merge. Nothing durable survived.
2. **Per-PR and manual.** It applied because an agent happened to paste it into
   one PR body, not because the harness required it.
3. **Dogfood-local.** Even if retained, it would exist only in this
   repository's PR history, never in a workspace where the harness is installed.

The operator's requirement is explicit: the audit must be *"a compound learning
that gets applied by the harness on every shipment regardless of workspace in
which the harness is installed."*

## Prior art retrieved (Step 1.8, confidence: high)

Two existing compound learnings and one already-staged feature bear directly on
this. Ignoring them would produce a duplicate implementation.

| Artifact | What it already covers | Residual gap |
|---|---|---|
| `docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md` | 12 root-cause classes + a "reusable evidence-consistency checklist"; overlaps operator categories 1, 2, 3, 4, 7, 10. Already has canonical `problem_type` / `category` / `root_cause` / `tags`. | Scoped to PR #436 as a *retrospective* taxonomy. Not normative, not universal, no delivery vector. |
| `docs/compound/2026-08-18-stage-agent-checkpoint-index-sync-ordering-self-contradiction.md` | Stale ordinal/finality claims in edited ordered lists (a narrow instance of category 1 + 10). | Single-surface, single-class. |
| Feature **162-F** / shipment **170-S** (queued, plan-reviewed PASS, 13 sized tasks) | A **conditional** Evidence Consistency Reviewer persona with a 10-point branch-tree-only rubric (`162.004-T`), review-skill Step 1.5 retrieval, mechanical post-fix delta checks, pr-lifecycle inventory, dogfood parity tests. | Trigger is conditional and dogfood-path-specific; four operator categories missing; no PR-body concision contract; no anti-self-reference rule. |

**Conclusion: this is not a duplicate, but it is also not greenfield.** The
taxonomy content is largely solved. What is unsolved is *universality*.

## The central finding — the delivery paradox

The operator asked for a *compound learning* that applies *in every workspace*.
Investigation shows these two properties are, as the harness is built today,
**mutually unreachable by the compound library alone**:

* `templates/skills/compound/SKILL.md.tmpl` authors learnings into the **target
  workspace's own** `docs/compound/`, which is **empty at install time**.
* There is **no seeding, bundling, or propagation mechanism** that copies this
  repository's `docs/compound/` entries into an installed workspace. Nothing
  under `templates/foundation/`, `templates/packs/`, or the install layers
  carries learning content.

Therefore a learning written in `docs/compound/` here can never, by itself,
execute in a customer workspace. Taking the operator's words literally and only
authoring a compound entry would satisfy the letter of the request and fail its
intent completely.

**Resolution — separate memory from behaviour.** The two halves travel by
different vectors and must not be conflated:

* **Memory vector (this repo):** `docs/compound/` records *why* the audit
  exists, with the searchable frontmatter the operator asked for. Institutional
  memory, dogfood-scoped, retrieved by `learnings-researcher`.
* **Behaviour vector (every workspace):** normative, technology-agnostic
  **template surfaces** carry the audit itself. This is what actually "gets
  applied by the harness on every shipment".

This distinction is recorded explicitly so that a future session does not
attempt to ship `docs/compound/` content into target workspaces.

## Options considered

### Option A — New standalone compound learning + new instruction, ignoring 162-F

Author a fresh compound entry and a fresh audit surface from scratch.

*Rejected.* Directly duplicates the taxonomy learning and collides with
`162.004-T`'s persona on the same files. Produces two competing rubrics with
different category counts — itself an instance of audit category 2 (status
consistency) and category 9 (schema consistency with neighbours).

### Option B — Extend 162-F in place; expand 170-S's scope

Mutate the queued 170-S manifest and rewrite `162.004-T` to be universal.

*Rejected.* 170-S is **queued with a PASS plan-review verdict**. Rewriting
already-gated scope silently invalidates that verdict without re-running the
gate, and destroys the traceability between the PR #436 evidence and the work it
authorized. It also enlarges a shipment that is already 13 tasks.

### Option C — Universalization + completion layer, sequenced behind 170-S ✅ **SELECTED**

Accept 162-F as the *substrate* (persona exists, retrieval exists, parity tests
exist). Add a strictly additive layer that:

1. promotes the audit from **conditional** to **every-shipment**;
2. moves the trigger from dogfood paths to **technology-agnostic** predicates;
3. adds the **four missing categories** (5, 6, 8, 9);
4. establishes the **PR-body concision contract** and the
   **anti-self-referential-readiness rule**;
5. consolidates — not duplicates — the compound taxonomy learning.

*Selected.* Minimal new surface area, no re-litigation of a passed gate, and a
clean dependency edge that prevents file-level collision during execution.

### Option D — Defer until 170-S ships, then re-evaluate

*Rejected.* The gap is fully knowable now; deferring loses the operator's intent
while 170-S executes, and the sequencing edge already prevents collision.

## Decisions

### D1 — Single normative surface, referenced not duplicated

The ten categories are authored **once**, in a new technology-agnostic
instruction template:

`templates/instructions/shipment-documentation-audit.instructions.md.tmpl`

Ship agent, `operational-closure`, `pr-lifecycle`, and the Evidence Consistency
Reviewer persona **reference** it. They do not restate the categories. Restating
would create exactly the cross-surface drift the audit exists to catch (category
7 + RC-10 propagation incompleteness).

### D2 — Every shipment, not a conditional trigger

The audit is a **mandatory pre-readiness step for every shipment**, replacing
`162.004-T`'s path-conditional trigger. The persona's *invocation* stays
conditional for cost reasons only where a shipment demonstrably touches no
documentation surface; the *audit obligation* itself is unconditional and its
outcome must be recorded either way (including an explicit "no documentation
surface touched" result, so an unrecorded audit is distinguishable from one that
never ran).

### D3 — Technology-agnostic predicates only

Trigger and rubric language must not name `.backlogit/**`,
`src/autoharness/gates/**`, Python, Copilot, or any IDE/provider. Predicates are
expressed against harness-level concepts already available in every install:
the configured docs root and its subdirectories, the configured backlog
directory, and frontmatter keys declared by the workspace's own gates.

### D4 — Compound learning: consolidate, do not duplicate

`docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md` is
**extended in place** to become the canonical audit rationale: the four missing
categories are folded in, the ten-category universal form is stated, PR #439 and
PR #440 evidence is added, and the delivery-paradox finding is recorded. Its
existing canonical frontmatter (`problem_type`, `category`, `root_cause`,
`tags`) is preserved and extended. **No competing compound entry is created.**

### D5 — PR bodies carry outcome, not the checklist

PR bodies record only: audit verdict, evidence pointer (the committed audit
record), and any deferred follow-up IDs. The verbose checklist never appears in
a PR body. This is the direct encoding of the operator's opening sentence.

### D6 — Anti-self-referential readiness (the PR #439 lesson)

A committed artifact can never truthfully assert the SHA of the commit that
contains it — a fixed point that PR #439 chased through repeated `reviewed_head`
substitutions.

* **Mutable surfaces** (PR body, external gates) own **current-HEAD** readiness.
* **Committed evidence** records only **immutable** state: a
  `last_code_affecting_head` or an explicitly named observed HEAD.

Any audit rule that would require a committed file to name its own commit is
malformed and must be restructured, not re-substituted.

### D7 — P-021 integration

In-scope inconsistencies found by the audit are **fixed before readiness is
claimed**. Out-of-scope ones are **captured as deferred entries before
disposition**, under the existing P-021 C1/C2 capture contract. The audit adds
no new deferral mechanism.

### D8 — No new template variables

The audit surfaces are static normative prose plus predicates over
already-resolved configuration. **No new `{{...}}` variables are introduced**,
so `docs/` variable-resolution documentation is untouched. Verification asserts
this negatively (no unresolved or newly-introduced variables), which is why
D8 is testable rather than aspirational.

## Constraints preserved

* **P-001 / P-010** — Stage plans; Ship executes. This deliberation authorizes
  no source or template mutation.
* **P-006** — blast radius spans multiple template families (instructions,
  agents, skills) plus installed dogfood mirrors ⇒ plan hardening required.
* **P-021** — audit findings route through the existing capture contract.
* **170-S dependency** — mandatory sequencing edge; overlapping-surface
  collision is the primary execution risk.

## Acceptance posture (feeds planning)

Verification must be deterministic and stack-neutral, exercised against **at
least three target technology profiles** drawn from the schema's own enumeration
(for example `python`/`cli-tool`, `typescript`/`web-app`, `go`/`mcp-server`),
proving the audit surface renders and is referenced consistently in each, and
that installed dogfood output matches its templates.

## Open risk

Execution of this feature and 170-S touch overlapping files (Ship agent, review
persona, pr-lifecycle). The dependency edge orders them but does not merge them;
whichever executes second must re-verify the first's content rather than assume
it. This is recorded as an explicit plan input.
