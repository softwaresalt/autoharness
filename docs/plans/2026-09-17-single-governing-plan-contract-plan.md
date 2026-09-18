---
title: "Single-governing-plan contract with immutable review history"
description: "Implementation plan for the minimum demonstrated single-governing-plan contract: a canonical current-plan input selected by durable identity metadata, exactly one immutable review artifact per attempt written outside the plan file, and explicit latest-attempt/verdict selection from a structured manifest rather than by scanning prose. A pre-dispatch verifier fails closed on identity, history-leak, and verdict-ambiguity violations. Plan-line budgets, compact-context auto-triggering, harvest rewiring, and repository-wide migration of existing append-only plans are explicitly deferred to separate Stage work."
doc_type: plan
source: docs/plans/2026-09-17-single-governing-plan-contract-plan.md
date: 2026-09-17
status: reviewed
revision: 5
revision_note: "Revision 5 (remediation cycle 3) answers review attempt 05, which returned BLOCKED at revision 4 on wire-format conflicts. TWO CONTRACTS EXISTED FOR ONE SURFACE: the plan required `plan_role` with path-valued `supersedes`, `source_history` and `review_manifest`, while task 171.001-T required `status`-valued role with `(plan_id, revision)`-valued `supersedes`/`superseded_by` and named neither `source_history` nor `review_manifest`; and task 171.003-T required `plan_revision_reviewed` while every live verdict manifest in docs/reviews/ carries `plan_revision`. That is precisely the duplicate-definition defect this plan exists to eliminate, reproduced inside the plan itself. Revision 5 declares ONE EXACT CONTRACT and propagates it to every plan, task, test and verdict surface: the role field is `plan_role` (NEVER `status`, which is already used on a different axis); `supersedes` and `superseded_by` are REPO-RELATIVE PATHS (never (plan_id, revision) pairs) because PLAN_SUPERSEDES_CYCLE is specified as cyclic OR UNRESOLVABLE and only a path resolves; `plan_id` remains what the single-active constraint keys on; the manifest field is `plan_revision` and `plan_revision_reviewed` is declared NOT a field name anywhere. Revision 5 also closes the second attempt-05 finding: T4a required 'carried-forward context' that T3 defined no field for. `carried_forward_context[]` is now a defined manifest field, and the assembler emits a TWO-BAND typed value ReviewInputSet(operative, context) whose `operative` band holds exactly the one plan_role: active document — so carried-forward context is STRUCTURALLY incapable of becoming operative input, and REVIEW_INPUT_HISTORY_LEAK has a band to be a leak INTO. Revision 5 is STAGE-REMEDIATED AND PENDING INDEPENDENT REVIEW ATTEMPT 06; Stage does not review its own remediation and asserts no PASS. Revision 4 (remediation cycle 2) adopted decision revision 3 and closed the propagation findings from local review cycle 2. Revision 3 reduced scope correctly but the reduction was never enforced in the executable backlog records: the four descoped surfaces (repository-wide migration, its regression suite, compact-context auto-consolidation, harvest rewiring) were left as blocked children INSIDE the covering feature while being excluded from the shipment manifest, and the pre-dispatch verifier still carried `blocks` edges onto the deferred migration and its suite. That combination made the shipment unclosable without executing deferred scope. Revision 4 removes those two edges, re-homes all four descoped tasks out of the covering feature into a deferred feature via the supported backlog lifecycle with P-021 linkage preserved, and states that NO in-manifest task may depend on, gate upon, or emit a token belonging to a deferred surface. `PLAN_BUDGET_BREACH` is removed from the verifier entirely: the budget contract is deferred. Revision 4 also adds a red-phase task so the six-blocking-token contract tests are authored and observed failing before the verifier exists, resolves the duplicate `T8` task label, and fixes the T4a/T4b and T5a/T5b ownership boundaries so the assembly/judgement and authoring/linkage halves do not overlap. The bounded audit trail lives in `review_history`; `linked_review` names the current verdict manifest."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
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
review_history:
  - docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-04.md
  - docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md
review_history_note: "Attempts 01-02 were authored as one mutable file covering two cycles; it is preserved verbatim and classified rather than retroactively split into records that were never independently authored. Attempt 03 is a conforming single-attempt immutable artifact. Attempt 04 records local review cycle 2 (BLOCKED at revision 3, on non-propagation of the design into the executable backlog records) and the Stage remediation response. Attempt 05 records the final independent review cycle (BLOCKED at revision 4, on the plan/task/manifest wire-format conflicts and the undefined carried-forward-context field) and the Stage remediation cycle 3 response that produced revision 5."
latest_review_attempt: 5
latest_review_artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md
latest_review_verdict: REMEDIATED-PENDING-REVIEW
latest_review_verdict_note: "Attempt 05 returned BLOCKED at plan revision 4. Stage remediation cycle 3 closed every attempt-05 finding and raised this plan to revision 5. Stage does not review its own remediation, so NO PASS is asserted at revision 5; the next independent reviewer pass is attempt 06."
covering_feature: 171-F
shipment: 179-S
requires_plan_hardening: "yes"
plan_hardening_status: complete
plan_hardening_section: "## Plan Hardening Record (P-006)"
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

## Scope ceiling (decision D5, tightened in revision 3)

The report offers a seven-step decomposition. The **2-hour rule governs, not
the report's decomposition.** Revision 2 applied that ceiling to individual
tasks but not to the covering feature, and the feature grew to span `schemas/`,
review storage, plan-line budgets, a `compact-context` auto-trigger, harvest
rewiring, and a repository-wide migration over every committed plan. Six
surfaces with six independent failure modes is not one release unit, and the
migration alone carries more blast radius than the contract it was migrating
toward.

**Revision 3 reduces the feature to the minimum contract the Problem section
actually demonstrates**, which is exactly three things:

1. a **canonical current-plan input** — the reviewer reads one document, and
   which document that is, is determined by durable identity metadata rather
   than by file position or recency;
2. **one immutable artifact per review attempt**, written outside the plan file
   and never edited after it is written;
3. **explicit latest-attempt and verdict selection** from a structured record,
   never inferred by scanning inline markers or narrative.

Everything the defect report says about non-convergence follows from those
three being absent. Nothing else in revision 2's scope is load-bearing for it.

### Deferred, not dropped

Each deferral below is recorded as its own Stage stash entry, carries the same
`C9CD24F3` provenance, and is named here so it is traceable rather than lost.
None of them is in `179-S`.

| Deferred surface | Why it is separable | Recorded as |
|---|---|---|
| Plan line/token budget and `PLAN_BUDGET_BREACH` | A budget is a *symptom* threshold, not the contract. With regenerate-not-patch in force, plans stop accreting, so the budget's own evidence ("~3,000 lines by attempt 3") no longer accumulates. Shipping a hard-fail threshold before observing post-contract plan sizes would pin a number chosen against pre-contract data | Stage stash entry, deferred |
| `compact-context` auto-consolidation trigger | Touches a different skill family, fires on runtime heuristics, and depends on the budget signal above | Stage stash entry, deferred |
| Harvest rewiring to atomic active-plan references | Harvest correctness is a distinct contract with its own consumers; the plan-identity metadata this unit ships is its prerequisite, not its co-requisite | Stage stash entry, deferred |
| Repository-wide migration of existing append-only plans | The highest-blast-radius item in revision 2 by a wide margin: it rewrites committed history-bearing artifacts. It is separable because the contract applies to *new* review attempts from the moment it lands; legacy plans are handled by exclusion, not conversion | Stage stash entry, deferred |

**Legacy handling without migration.** A plan with no identity metadata is
classified `PLAN_LEGACY_UNIDENTIFIED`: it is reported, and the pre-dispatch
verifier does **not** block on it. This is the ordering hazard from decision
**D6** resolved by scope reduction rather than by sequencing — a validator that
never had a migration to race cannot deadlock on one. No legacy plan is
rewritten, reclassified, or deleted by this release unit.

Nothing in the report's out-of-scope list is reopened: no new service, no
database, no non-Git storage, no prompt-wording-only fix, no replacement of
human design judgment, no reopening of any resolved upstream decomposition.

## Design

### Plan identity metadata

Every plan carries durable frontmatter identity. **This table is the single
normative wire format.** Revision 4 stated one set of field names here while the
harvested task records stated a different, incompatible set
(`status`-valued instead of `plan_role`, `(plan_id, revision)`-valued
`supersedes` instead of a path, no `source_history`, no `review_manifest`) —
two contracts for one surface, which is the exact defect class this plan
exists to remove. Revision 5 resolves it by **adopting the plan's field names
as canonical** and propagating them into every task, test, and manifest surface.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `plan_id` | string | yes | Stable identity across renames and revisions |
| `plan_role` | enum `active` \| `superseded` \| `history` | yes | Governance role of **this document** |
| `revision` | integer, monotonic | yes | Revision number within the `plan_id` |
| `supersedes` | **repo-relative path**, or `null` | yes (may be `null`) | The document this revision replaces |
| `superseded_by` | **repo-relative path**, or `null` | yes (`null` iff `plan_role: active`) | Inverse pointer; the document that replaced this one |
| `source_history` | ordered list of **repo-relative paths** | yes (may be empty) | The immutable review artifacts consumed, in attempt order |
| `review_manifest` | **repo-relative path** | yes | The structured latest-verdict record for this `plan_id` |

**Two naming decisions, stated so they cannot drift again:**

* The role field is **`plan_role`, never `status`.** Plan frontmatter already
  carries a `status` key on a different axis (`draft` / `reviewed`), and
  overloading it would make the single-active constraint undecidable on
  exactly the documents it governs.
* `supersedes` / `superseded_by` are **path-valued, never
  `(plan_id, revision)`-valued.** `PLAN_SUPERSEDES_CYCLE` is specified as
  "cyclic **or unresolvable**", which requires a pointer that resolves to a
  document. `plan_id` is still what the single-active constraint keys on, so
  renaming or copying a file cannot manufacture a second governing plan; the
  path is the edge, `plan_id` is the identity.

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
directory or a file range. Archived history is excluded from the `operative`
band by construction. If a document whose `plan_role` is `superseded` or
`history` appears in the **operative** band, assembly **fails closed** with
`REVIEW_INPUT_HISTORY_LEAK` rather than proceeding with a polluted input.
Carried-forward context is carried in the separate `context` band defined
above and is never operative input.

### Regenerate, do not patch

After remediation the plan is **regenerated** as a normalized authoritative
contract at `revision + 1`, with the prior revision marked
`plan_role: superseded`. Editing findings into the live plan body is prohibited
by the verifier, not by convention.

### Structured latest-verdict record

Latest attempt and verdict are read from a structured record, never discovered
by scanning inline markers or narrative. **This table is the single normative
manifest wire format**, and it deliberately matches the key names the verdict
manifests in `docs/reviews/` already carry, so the contract can be verified
against live records rather than against a parallel vocabulary:

| Field | Type | Meaning |
|---|---|---|
| `plan_id` | string | The identity this manifest selects for |
| `plan_path` | repo-relative path | The `plan_role: active` document |
| `plan_revision` | integer | The revision of that document. **The field is `plan_revision`. `plan_revision_reviewed` is NOT a field name in this contract** and must not appear on any surface |
| `latest_attempt` | integer | Attempt number of the authoritative artifact |
| `latest_attempt_artifact` | repo-relative path | The immutable artifact for `latest_attempt` |
| `verdict` | enum | The verdict carried by that artifact |
| `attempts[]` | list | Roster; each entry `{attempt, artifact, plan_revision, verdict, superseded_by}` |
| `carried_forward_context[]` | list | See below. May be empty; never absent |

Tokens: `REVIEW_VERDICT_AMBIGUOUS` when two records claim latest;
`REVIEW_VERDICT_MISSING` when the manifest names an attempt with no record.

#### Carried-forward context — a representation that cannot become operative input

Revision 4's T4a required assembly to emit "the current plan revision plus
exactly the artifacts the manifest explicitly names as carried-forward
context", while T3 defined **no field** for that set. An undefined input is
either silently empty — in which case T4a's requirement is vacuous — or
improvised per caller, which is the drift the contract forbids. Revision 5
defines it, and defines it so that it is **structurally incapable** of being
read as operative contract text:

`carried_forward_context[]` entries are
`{artifact: <repo-relative path>, reason: <non-empty string>}`.

The assembler's output is a **two-band typed value**, not a flat list:

```text
ReviewInputSet(
    operative = [ <the single plan_role: active document> ],
    context   = [ <every carried_forward_context artifact, in manifest order> ],
)
```

The bands are **disjoint and differently typed at the boundary**, which is what
makes the guarantee structural rather than conventional:

* The `operative` band holds **exactly one** document: the `plan_role: active`
  plan named by `plan_path`. Never zero, never two, and never a review artifact.
* The `context` band may hold documents whose `plan_role` is `superseded` or
  `history`, and review artifacts from `source_history`. That is the **only**
  band in which such a document may legally appear.
* A `superseded` / `history` document appearing in the **`operative`** band is
  `REVIEW_INPUT_HISTORY_LEAK` — which is precisely the judgement T4b makes.
  Without the two-band shape the token has nothing to be a leak *into*.
* The context band is passed to the reviewer under an explicit
  non-authoritative label, and no verifier token is ever evaluated against its
  contents.

A consumer that flattens the two bands into one list has violated the contract;
the typed boundary exists so that flattening is a visible code change rather
than an accident.

### Pre-dispatch verifier

Runs before any reviewer dispatch and fails closed on:

| Token | Condition |
|---|---|
| `PLAN_MULTIPLE_ACTIVE` | More than one `plan_role: active` for a `plan_id` |
| `PLAN_IDENTITY_MISSING` | A required identity field is absent from a plan that declares a `plan_id` |
| `PLAN_SUPERSEDES_CYCLE` | `supersedes` chain is cyclic or unresolvable |
| `REVIEW_INPUT_HISTORY_LEAK` | Superseded/history document in the operative input set |
| `REVIEW_VERDICT_AMBIGUOUS` | Two records claim latest |
| `REVIEW_VERDICT_MISSING` | Manifest names an attempt with no record |

Reported, never blocking:

| Signal | Condition |
|---|---|
| `PLAN_LEGACY_UNIDENTIFIED` | A plan carrying no `plan_id` at all — pre-contract, handled by exclusion |

`PLAN_BUDGET_BREACH` is **removed** from this release unit and deferred with
the budget surface (see Scope ceiling). The six blocking tokens above are all
structural: each is decidable from identity metadata and the manifest alone,
with no threshold to tune and no heuristic to calibrate.

### Migration: not in this release unit

Revision 2 specified a fail-closed, non-destructive, idempotent migration over
existing append-only plans. That surface is deferred. Legacy plans are handled
by the non-blocking `PLAN_LEGACY_UNIDENTIFIED` classification instead: they are
reported and skipped, never rewritten and never deleted. The never-delete
constraint from cycle-1 finding F1 is preserved by the strongest available
means — no migration code exists in this unit to delete anything.

## Work Breakdown

Eleven tasks. Revision 2's twelve covered six surfaces; revision 3 covered
three and split the two tasks whose `complexity: high` was not credibly
reducible to a single 2-hour unit. Revision 4 adds the red-phase task that the
revision-3 ordering described only in prose, and resolves the duplicate `T8`
label.

| # | Task | Scope | Size / Complexity | Blocked by |
|---|---|---|---|---|
| T1 | Plan identity schema: the **seven** normative fields `plan_id`, `plan_role`, `revision`, `supersedes`, `superseded_by`, `source_history`, `review_manifest`; enums, field requiredness, and the path-valued supersession edges | `schemas/` | S / low | — |
| T2 | Review-artifact schema and the `review-history/` path and naming contract | `schemas/` + `docs/` | S / low | — |
| T3 | Structured latest-verdict manifest record — `plan_id`, `plan_path`, `plan_revision`, `latest_attempt`, `latest_attempt_artifact`, `verdict`, `attempts[]`, **and `carried_forward_context[]`** — plus its two ambiguity tokens | `schemas/` + `src/autoharness/` | S / medium | T2 |
| T4a | **ASSEMBLY only** — resolve the operative review-input set from identity metadata and the manifest, emitting the **two-band `ReviewInputSet(operative, context)`** typed value, with `operative` holding exactly the one `plan_role: active` document and `context` holding the manifest's `carried_forward_context[]` artifacts. T4a **produces a set and makes no verdict**; it emits no token | `.github/skills/plan-review/` + `templates/skills/` | S / medium | T1, T3 |
| T4b | **JUDGEMENT only** — apply the superseded/history classification predicate to the **`operative` band** of the set T4a produced and emit `REVIEW_INPUT_HISTORY_LEAK`. T4b **does not assemble, re-resolve, or widen the set**, and never evaluates a token against the `context` band; it consumes T4a's output as given | `.github/skills/plan-review/` + `templates/skills/` | S / medium | T4a |
| T5a | **DOCUMENT PRODUCTION only** — regenerate-not-patch: emit the next revision as a normalized standalone document. T5a **writes exactly one file and mutates no other artifact** | `.github/skills/plan-review/` + `templates/skills/` | M / medium | T1 |
| T5b | **CROSS-SURFACE LINKAGE only** — set the prior revision's `plan_role: superseded` and its `superseded_by` path, set the new revision's `supersedes` path, append to `source_history`, and update the verdict manifest. T5b **generates no document content**; it only records relationships between documents T5a already produced | `.github/skills/plan-review/` + `templates/skills/` | S / medium | T5a, T3 |
| T6a | **RED** — author the pre-dispatch verifier contract tests (one passing and one failing concrete state per blocking token, plus a `plan_id`-rename case and a `PLAN_LEGACY_UNIDENTIFIED` non-blocking case) against the not-yet-existing verifier, and observe them failing | `tests/` | M / medium | T1, T2, T3 |
| T6 | **IMPLEMENTATION** — pre-dispatch verifier implementing the **six** blocking tokens and the one reported signal | `src/autoharness/` | M / medium | T6a |
| T6b | **GREEN** — observe the full token contract passing against the shipped verifier and add the regression cases that only make sense against a real implementation | `tests/` | M / medium | T6 |
| T7 | Stage agent remediation path updated to regenerate at `revision + 1` | `templates/agents/_stage.agent.md.tmpl` + installed mirror | S / medium | T5a, T5b |

**Label hygiene (revision 4).** Revision 3 used `T8` for the regression suite
while another surface in the same portfolio also carried a `T8` label,
producing an unresolvable cross-reference. The regression surface is now
`T6b`, named for the implementation it verifies.

**No in-manifest task may depend on deferred scope (revision 4).** Revision 3
left the pre-dispatch verifier carrying `blocks` edges onto the deferred
repository-wide migration and its regression suite. Those edges are removed.
No task in this release unit may depend on, gate upon, or emit a token
belonging to a deferred surface; the four descoped surfaces are re-homed out
of the covering feature entirely, with P-021 linkage preserved, so the
shipment can close without executing them.

### TDD ordering (revision 4 — machine-encoded)

* **T6a (RED) blocks on T1, T2, T3 only** — the schemas its assertions are
  written against. It does **not** depend on T6; that asymmetry is what makes
  it a red phase rather than a test-after task.
* **T6 (IMPLEMENTATION) blocks on T6a.**
* **T6b (GREEN) blocks on T6.**

### Re-estimation rationale (remediation-cycle-1 correction)

Revision 2 carried four `complexity: high` tasks (T4, T5, T6, T10). Under the
two-axis gate, `complexity: high` forces a split or an explicit de-risking step
regardless of size; revision 2 recorded the rating and proceeded anyway.
Revision 3 resolves all four:

* **T4 (high)** was one task doing two distinct jobs — assembling an input set,
  and judging that set for contamination. Split into **T4a** (assembly) and
  **T4b** (leak detection). Each is a single predicate over a defined input,
  and each drops to `medium`. Revision 4 states the boundary explicitly so the
  two halves cannot both claim the classification predicate.
* **T5 (high)** conflated document generation with cross-artifact state
  transitions. Split into **T5a** (generate the next revision) and **T5b**
  (supersession bookkeeping). T5b blocks on T5a, so the ordering is machine
  encoded rather than implied. Revision 4 states the boundary explicitly so the
  two halves cannot both claim the manifest write.
* **T6 (high)** was high because it implemented seven tokens including a
  tunable budget threshold. With `PLAN_BUDGET_BREACH` deferred, the remaining
  six are all structural checks over metadata already defined by T1–T3. It
  drops to `medium` without a split, and T6a/T6b prove each token
  independently.
* **T10 (high)** — the migration — is removed from the release unit entirely.
  It was the highest-risk task in the plan and the one least separable into a
  2-hour unit; deferring it is the split.

No task in the reduced set carries `complexity: high`. No task exceeds `M`.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* Every blocking token in the verifier table has one passing and one failing
  concrete case.
* `PLAN_LEGACY_UNIDENTIFIED` is asserted to be **reported and non-blocking** —
  a legacy plan must not stop a review dispatch.
* A `plan_id` rename produces exactly one active plan, not two.
* No plan under `docs/plans/` is modified, reclassified, or deleted by this
  release unit, and no migration code exists in it to do so.
* `autoharness gate check` passes on every modified file.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Historical review evidence is destroyed | No deletion path and no migration code exists in this release unit; legacy plans are excluded by classification, never converted |
| R2 | The verifier blocks all review work on legacy plans | `PLAN_LEGACY_UNIDENTIFIED` is a reported, non-blocking signal with its own asserted non-blocking test case. The D6 ordering hazard is dissolved by scope reduction rather than sequenced around |
| R3 | Deferred surfaces are silently abandoned | Each is recorded as a named Stage stash entry carrying `C9CD24F3` provenance, tabulated in Scope ceiling, and restated in Out of scope |
| R4 | Single-active is enforced per-file rather than per-identity, missing renames | The constraint keys on `plan_id`, not path; T6a/T6b carry a rename case |
| R5 | The reduced contract does not actually fix the non-convergence loop | The three retained properties are exactly the ones the Problem section's evidence turns on: one canonical input, immutable per-attempt artifacts, explicit latest selection. The deferred surfaces are efficiency and cleanup, not correctness |
| R6 | A reviewer reads the deferred budget as still in force | `PLAN_BUDGET_BREACH` is removed from the token table, not marked optional; Verification asserts the verifier implements six blocking tokens, not seven |

## Out of scope

* Any new service, database, or non-Git storage.
* Deletion of any historical review evidence.
* A prompt-wording-only fix.
* Replacing human design judgment or reopening any resolved decomposition.
* Rewriting, reclassifying, or migrating any currently committed plan in
  `docs/plans/`.
* **Plan line/token budgets and `PLAN_BUDGET_BREACH`** — deferred (Scope
  ceiling).
* **`compact-context` auto-consolidation triggering** — deferred.
* **Harvest rewiring to atomic active-plan references** — deferred.
* **Repository-wide migration of existing append-only plans** — deferred.
* Adjacent stash entries `C327A8DE` (plan/work-item soundness linter) and
  `8CB5A9B9` (review-cycle circuit breaker), and epic `D911A3B2`. Cross-read
  during deliberation, confirmed distinct, left untouched.

## Plan Hardening Record (P-006)

Hardening applied 2026-09-17, re-run 2026-09-18 during remediation cycle 1.
Revision 2 declared `plan_hardening_status: complete` without persisting this
record; that gap is H0 below.

**Hardening trigger.** Elevated blast radius on every axis available: the
change spans `schemas/`, skill workflows and their templates, an agent template
and its installed mirror, and — in revision 2 — a migration that rewrites
committed history-bearing artifacts. It also changes the contract that reviewer
agents themselves consume, so a defect in it degrades the mechanism that would
otherwise catch the defect.

**Protected invariants.**

* Historical review evidence is never deleted, by any path, at any severity.
* No committed plan in `docs/plans/` is modified by this release unit.
* A validator must never be able to deadlock the review pipeline it gates.
* The plan-review and Stage remediation contracts must stay consistent with
  each other; a regenerate instruction in one and a patch instruction in the
  other is a live contradiction.
* Template and installed mirror must not diverge.

**Instructions and learnings consulted.**
`docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md`,
`docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`,
`docs/compound/2026-08-12-verify-hosted-review-findings-against-frozen-task-spec.md`,
`docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md`,
`.github/skills/plan-review/SKILL.md`, `.github/skills/impl-plan/SKILL.md`,
`docs/size-complexity-reference.md`, and
`docs/bugs/2026-09-13-autoharness-append-only-plan-review-loop-bug-report.md`.

| # | Hardening finding | Resolution |
|---|---|---|
| H0 | Revision 2 asserted `plan_hardening_status: complete` with no persisted hardening record | This section is the record; `plan_hardening_section` in frontmatter names it |
| H1 | The covering feature spanned six independent surfaces with six independent failure modes — not one release unit | Scope reduced to the three properties the Problem section's evidence actually turns on; four surfaces deferred as named, traceable Stage entries |
| H2 | The migration was the highest-blast-radius item in the plan and the least reducible to a 2-hour unit, yet was treated as a co-requisite of the contract | Deferred entirely. Legacy plans handled by non-blocking `PLAN_LEGACY_UNIDENTIFIED` classification, which requires no code that can rewrite or delete anything |
| H3 | The D6 migration-before-enforcement ordering was a mitigation for a hazard the plan created by bundling the two | Hazard dissolved rather than sequenced around: with no migration in the unit, there is no race for the validator to lose |
| H4 | `PLAN_BUDGET_BREACH` fixed a hard-fail threshold using pre-contract evidence, and would have been calibrated against plan sizes the contract itself makes obsolete | Deferred with the budget surface; the verifier's six remaining tokens are all structural, with nothing to tune |
| H5 | Four tasks carried `complexity: high` and shipped anyway, contrary to the two-axis gate | T4 and T5 split into T4a/T4b and T5a/T5b; T6 reduced to `medium` by token removal; T10 deferred. No remaining task is `high` |
| H6 | Task ordering was prose-only | `Blocked by` column encoded per task; T5b→T5a, T4b→T4a, T6→T6a and T6b→T6 are machine edges |
| H7 | This plan's own review record combined two cycles in one mutable file — the exact defect the plan exists to fix | Review history split into immutable per-attempt artifacts under `docs/reviews/review-history/`, with `linked_review` retained as the latest-verdict manifest. Recorded in `review_history` frontmatter |
| H8 | Reflexivity risk: a defect in this contract degrades the reviewer mechanism that would catch it | T6a/T6b assert each token independently against concrete fixture states rather than against the live repository, so the suite does not depend on the contract being already correct |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Add plan identity fields to `schemas/` (T1, T2, T3) | Low — additive; legacy plans classified, not rejected | Standard PR review | Revert schema files |
| Change the plan-review skill's input assembly and remediation path (T4a/T4b/T5a/T5b) | Medium — alters the contract reviewer agents consume | Standard PR review | Revert skill + template pair together |
| Change the Stage agent template and installed mirror (T7) | Medium — agent contract, mirrored pair | Standard PR review | Revert both copies together |
| Enable the pre-dispatch verifier at blocking severity (T6) | Medium — can halt review dispatch | Standard PR review; `PLAN_LEGACY_UNIDENTIFIED` non-blocking by construction | Disable the verifier call site; no persisted state |
| *(withdrawn)* Migrate every committed append-only plan | **High** — rewrites history-bearing committed artifacts | Would have required operator sign-off | Not applicable: deferred out of this release unit |

**Rollback coupling.** T1–T3 revert as a schema set. T4a/T4b/T5a/T5b revert as
the plan-review skill pair (installed + template). T7 reverts as the Stage
agent pair. T6 is a single call site. T6a/T6b are test-only. Nothing in the unit
mutates persisted artifacts, so rollback is code-only.

**Monitoring and validation window.** The first remediation cycle executed
after merge is the live signal: it must produce a new revision document plus a
new immutable attempt artifact, and must leave the prior revision marked
`superseded`. A cycle that instead appends to the live plan is a contract
failure visible in the diff.

**Operator checkpoints.** None in the reduced unit. The one checkpoint
revision 2 required — operator adjudication of ambiguous migration cases — is
removed with the migration.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers, MUST apply the Agent-Native Parity
persona inline because this plan changes agent-facing skill and agent-template
contracts, and MUST be written as a separate immutable attempt artifact — this
plan's own subject matter makes any other form self-contradicting.

**Unresolved operator decisions blocking safe execution.** None.
