---
title: "Single-governing-plan contract with immutable review history"
description: "Implementation plan separating the plan contract from the review log: durable plan identity metadata, exactly one active decided plan per identity, immutable per-attempt review artifacts written outside the plan file, manifest-driven review-input assembly that fails closed when historical prose leaks into the operative input set, a pre-dispatch verifier for the single-governing-plan invariants and budget signals, and a fail-closed non-destructive migration for existing append-only plans."
doc_type: plan
source: docs/plans/2026-09-17-single-governing-plan-contract-plan.md
date: 2026-09-17
status: reviewed
revision: 2
revision_note: "Revision 2 is the canonical statement of the intended design. Review findings were remediated in place; this document states exactly one binding requirement per topic. The bounded audit trail lives in `linked_review`. This plan deliberately models the discipline it specifies."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 1
source_bug_report: docs/bugs/2026-09-13-autoharness-append-only-plan-review-loop-bug-report.md
source_stash_id: C9CD24F3
stash_ids:
  - C9CD24F3
prior_learnings:
  - docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md
  - docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md
  - docs/compound/2026-08-12-verify-hosted-review-findings-against-frozen-task-spec.md
  - docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md
linked_review: docs/reviews/2026-09-17-single-governing-plan-contract-plan-review.md
covering_feature: 171-F
shipment: 179-S
requires_plan_hardening: "yes"
plan_hardening_status: complete
tags:
  - "plan-review"
  - "review-convergence"
  - "artifact-lifecycle"
  - "fail-closed-design"
---

# Single-governing-plan contract with immutable review history

## Problem

The plan-remediation loop appends every review attempt, rebuttal, withdrawal
note, and remediation narrative into the **same live plan file** that is also
the governing contract. Later review attempts read that whole file as one
authoritative contract, so superseded and withdrawn prose is judged alongside
current instructions.

Consequence: already-fixed findings reappear; retired wording is flagged as a
current requirement; each remediation makes the plan longer, more
contradictory, and more expensive to review. Architecturally sound designs get
trapped in a non-convergent loop and exhaust review circuit breakers on
mechanical text contradictions rather than real design defects.

Corroborated inside this repository. `docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md`
and `docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`
describe the same mechanism from the inside, and
`docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md` records the
manual remedy in its own `revision_note`: "a full canonical rewrite … rather
than an accreting record of corrections", with the audit trail segregated into
`linked_review`. The discipline already works. It is **manual and unenforced**.

## Scope ceiling (decision D5)

The report offers a seven-step decomposition. The **2-hour rule governs, not
the report's decomposition.** This release unit delivers the load-bearing
minimum plus migration. Nothing in the report's out-of-scope list is reopened:
no new service, no database, no non-Git storage, no prompt-wording-only fix, no
replacement of human design judgment, no reopening of any resolved upstream
decomposition.

## Design

### Plan identity metadata

Every plan carries durable frontmatter identity:

| Field | Meaning |
|---|---|
| `plan_id` | Stable identity across revisions and rewrites |
| `plan_role` | `active` \| `superseded` \| `history` |
| `revision` | Monotonic integer |
| `supersedes` | Path of the revision this replaces, if any |
| `source_history` | Ordered paths of the immutable review artifacts consumed |
| `review_manifest` | Path of the structured verdict record |

**Exactly one** `plan_role: active` document may exist per `plan_id`. Two
actives is a fail-closed authoring error, not a warning.

### Immutable review artifacts

Each review attempt is written as its own file under a `review-history/` path,
named by plan identity and attempt number. Once written it is **never edited**.
Remediation never patches a review artifact; it produces the next one.

Historical evidence is **never deleted** — the report requires this and so does
the anti-duplication reasoning already used for stash entries: a superseded
artifact is itself the diagnostic record of what changed and why.

### Manifest-driven review-input assembly

The reviewer input set is assembled **from the manifest**, not by reading a
directory or a file range. Archived history is excluded by default. If a
document whose `plan_role` is `superseded` or `history` appears in the
operative input set, assembly **fails closed** with
`REVIEW_INPUT_HISTORY_LEAK` rather than proceeding with a polluted input.

### Regenerate, do not patch

After remediation the plan is **regenerated** as a normalized authoritative
contract at `revision + 1`, with the prior revision marked
`plan_role: superseded`. Editing findings into the live plan body is prohibited
by the verifier, not by convention.

### Structured latest-verdict record

Latest attempt and verdict are read from a structured record, never discovered
by scanning inline markers or narrative. Tokens:
`REVIEW_VERDICT_AMBIGUOUS` when two records claim latest;
`REVIEW_VERDICT_MISSING` when the manifest names an attempt with no record.

### Pre-dispatch verifier

Runs before any reviewer dispatch and fails closed on:

| Token | Condition |
|---|---|
| `PLAN_MULTIPLE_ACTIVE` | More than one `plan_role: active` for a `plan_id` |
| `PLAN_IDENTITY_MISSING` | Required identity field absent |
| `REVIEW_INPUT_HISTORY_LEAK` | Superseded/history document in the operative input set |
| `REVIEW_VERDICT_AMBIGUOUS` | Two records claim latest |
| `REVIEW_VERDICT_MISSING` | Manifest names an attempt with no record |
| `PLAN_BUDGET_BREACH` | Plan exceeds the configured line/token budget |
| `PLAN_SUPERSEDES_CYCLE` | `supersedes` chain is cyclic or unresolvable |

`PLAN_BUDGET_BREACH` is the mechanical proxy for the report's "~3,000 lines by
attempt 3" evidence.

### Migration

Existing append-only plans are migrated by **classification, never deletion**:
the current authoritative content becomes the `active` revision; prior inline
review narrative is extracted into `review-history/` artifacts preserving
original text verbatim. Ambiguity about which prose is operative **fails
closed** and defers to the operator; it never guesses. Migration is idempotent.

## Work Breakdown

| # | Task | Scope |
|---|---|---|
| T1 | Plan identity schema: fields, enums, single-active constraint | `schemas/` |
| T2 | Review-artifact schema and `review-history/` path contract | `schemas/` + `docs/` |
| T3 | Structured latest-verdict record and its two ambiguity tokens | `schemas/` + `src/autoharness/` |
| T4 | Manifest-driven review-input assembly with `REVIEW_INPUT_HISTORY_LEAK` | `.github/skills/plan-review/` + `templates/skills/` |
| T5 | Regenerate-not-patch remediation path in the plan-review skill | `.github/skills/plan-review/` + `templates/skills/` |
| T6 | Pre-dispatch verifier implementing all seven tokens | `src/autoharness/` |
| T7 | Stage agent remediation path updated to regenerate at `revision + 1` | `templates/agents/_stage.agent.md.tmpl` + installed mirror |
| T8 | Auto-consolidation trigger after the first failed cycle or on budget breach | `.github/skills/compact-context/` + `templates/skills/` |
| T9 | Atomic backlog references to the active plan path | harvest skill + `templates/skills/` |
| T10 | Fail-closed, non-destructive, idempotent migration for existing plans | `src/autoharness/` |
| T11 | Regression suite: one passing and one failing concrete state per token | `tests/` |
| T12 | Migration suite: clean case, ambiguous case (must fail closed), idempotence case | `tests/` |

T10 and T12 are sequenced **before** T6 is enforced at blocking severity, for
the same ordering reason recorded in decision **D6**: shipping a validator
ahead of a migration converts a latent gap into a hard self-inflicted block.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* Every token in the verifier table has one passing and one failing case.
* Migration over this repository's own `docs/plans/` is a **dry run** in tests
  only; no committed plan is rewritten by this release unit.
* `autoharness gate check` passes on every modified file.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Migration destroys historical review evidence | Migration only classifies and extracts verbatim; deletion is not implemented, and T12 asserts byte-preservation |
| R2 | The verifier blocks all review work on legacy plans | T10/T12 land before T6 enforces at blocking severity (decision D6 ordering) |
| R3 | Budget breach becomes a bypassable warning | It is a fail-closed token with no waiver path; raising the budget is a version-controlled config change |
| R4 | Single-active is enforced per-file rather than per-identity, missing renames | The constraint keys on `plan_id`, not path; T11 carries a rename case |
| R5 | The feature is over-built relative to the 2-hour rule | Scope ceiling in decision D5; twelve tasks each bounded to one surface |

## Out of scope

* Any new service, database, or non-Git storage.
* Deletion of any historical review evidence.
* A prompt-wording-only fix.
* Replacing human design judgment or reopening any resolved decomposition.
* Rewriting any currently committed plan in `docs/plans/`.
* Adjacent stash entries `C327A8DE` (plan/work-item soundness linter) and
  `8CB5A9B9` (review-cycle circuit breaker), and epic `D911A3B2`. Cross-read
  during deliberation, confirmed distinct, left untouched.
