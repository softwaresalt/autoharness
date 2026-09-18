---
title: "Single-governing-plan contract with immutable review history"
description: "Implementation plan for the minimum demonstrated single-governing-plan contract: a canonical current-plan input selected by durable identity metadata, exactly one immutable review artifact per attempt written outside the plan file, and explicit latest-attempt/verdict selection from a structured manifest rather than by scanning prose. A pre-dispatch verifier fails closed on identity, history-leak, and verdict-ambiguity violations. Plan-line budgets, compact-context auto-triggering, harvest rewiring, and repository-wide migration of existing append-only plans are explicitly deferred to separate Stage work."
doc_type: plan
source: docs/plans/2026-09-17-single-governing-plan-contract-plan.md
date: 2026-09-17
status: reviewed
revision: 5
revision_note: "Revision 5 is maintained as one coherent current-state contract rather than as an accreting record of corrections. Prior-revision deltas, superseded requirement variants, and reviewer chronology are not carried in the body: the immutable per-attempt review artifacts listed in `review_history` and the mutable verdict manifest named by `linked_review` are the authoritative record of that chronology."
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
latest_review_attempt: 5
latest_review_artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md
latest_review_verdict: REMEDIATED-PENDING-REVIEW
latest_review_verdict_note: "REMEDIATED-PENDING-REVIEW at revision 5. Stage does not review its own remediation, so no PASS is asserted; the next independent reviewer pass is attempt 06. Attempt classification and roster live in the verdict manifest named by `linked_review`."
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

## Scope ceiling (decision D5)

The report offers a seven-step decomposition. The **2-hour rule governs, not
the report's decomposition**, and the ceiling applies to the covering feature
as well as to individual tasks. A feature spanning `schemas/`, review storage,
plan-line budgets, a `compact-context` auto-trigger, harvest rewiring, and a
repository-wide migration over every committed plan is six surfaces with six
independent failure modes — not one release unit — and the migration alone
carries more blast radius than the contract it would be migrating toward.

**This release unit is the minimum contract the Problem section actually
demonstrates**, which is exactly three things:

1. a **canonical current-plan input** — the reviewer reads one document, and
   which document that is, is determined by durable identity metadata rather
   than by file position or recency;
2. **one immutable artifact per review attempt**, written outside the plan file
   and never edited after it is written;
3. **explicit latest-attempt and verdict selection** from a structured record,
   never inferred by scanning inline markers or narrative.

Everything the defect report says about non-convergence follows from those
three being absent. Nothing else is load-bearing for it.

### Deferred, not dropped

Each deferral below is recorded as its own Stage stash entry, carries the same
`C9CD24F3` provenance, and is named here so it is traceable rather than lost.
None of them is in `179-S`.

| Deferred surface | Why it is separable | Recorded as |
|---|---|---|
| Plan line/token budget and `PLAN_BUDGET_BREACH` | A budget is a *symptom* threshold, not the contract. With regenerate-not-patch in force, plans stop accreting, so the budget's own evidence ("~3,000 lines by attempt 3") no longer accumulates. Shipping a hard-fail threshold before observing post-contract plan sizes would pin a number chosen against pre-contract data | Stage stash entry, deferred |
| `compact-context` auto-consolidation trigger | Touches a different skill family, fires on runtime heuristics, and depends on the budget signal above | Stage stash entry, deferred |
| Harvest rewiring to atomic active-plan references | Harvest correctness is a distinct contract with its own consumers; the plan-identity metadata this unit ships is its prerequisite, not its co-requisite | Stage stash entry, deferred |
| Repository-wide migration of existing append-only plans | The highest-blast-radius item available by a wide margin: it rewrites committed history-bearing artifacts. It is separable because the contract applies to *new* review attempts from the moment it lands; legacy plans are handled by exclusion, not conversion | Stage stash entry, deferred |

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
normative wire format**, and it governs every plan, task, test, and manifest
surface in the release unit. A second vocabulary for the same surface — a
`status`-valued role, a `(plan_id, revision)`-valued supersession edge, or a
manifest key the live records do not carry — is the exact duplicate-definition
defect this plan exists to remove.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `plan_id` | string | yes | Stable identity across renames and revisions |
| `plan_role` | enum `active` \| `superseded` \| `history` | yes | Governance role of **this document** |
| `revision` | integer, monotonic | yes | Revision number within the `plan_id` |
| `supersedes` | **repo-relative path**, or `null` | yes (may be `null`) | The document this revision replaces |
| `superseded_by` | **repo-relative path**, or `null` | yes (`null` iff `plan_role: active`) | Inverse pointer; the document that replaced this one |
| `source_history` | ordered list of **repo-relative paths** | yes (may be empty) | The immutable review artifacts consumed, in attempt order |
| `review_manifest` | **repo-relative path** | yes | The structured latest-verdict record for this `plan_id` |

**Two naming decisions, stated so they cannot drift:**

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
below and is never operative input.

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

`carried_forward_context[]` entries are
`{artifact: <repo-relative path>, reason: <non-empty string>}`. The field is
defined here because an undefined input is either silently empty — making any
requirement stated over it vacuous — or improvised per caller, which is the
drift the contract forbids.

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

The verifier implements **exactly six blocking tokens and one reported
signal**. `PLAN_BUDGET_BREACH` is not among them: the budget surface is
deferred (see Scope ceiling). All six blocking tokens are structural — each is
decidable from identity metadata and the manifest alone, with no threshold to
tune and no heuristic to calibrate.

### Migration is not in this release unit

No migration over existing append-only plans ships here. Legacy plans are
handled by the non-blocking `PLAN_LEGACY_UNIDENTIFIED` classification: they are
reported and skipped, never rewritten and never deleted. The never-delete
constraint is preserved by the strongest available means — no migration code
exists in this unit to delete anything.

## Work Breakdown

Eleven tasks.

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

**No in-manifest task may depend on deferred scope.** No task in this release
unit may depend on, gate upon, or emit a token belonging to a deferred surface.
The four descoped surfaces are re-homed out of the covering feature entirely,
with P-021 linkage preserved, so `179-S` can close without executing them. In
particular the pre-dispatch verifier carries no edge onto the deferred
repository-wide migration or its regression suite.

### TDD ordering (machine-encoded)

* **T6a (RED) blocks on T1, T2, T3 only** — the schemas its assertions are
  written against. It does **not** depend on T6; that asymmetry is what makes
  it a red phase rather than a test-after task.
* **T6 (IMPLEMENTATION) blocks on T6a.**
* **T6b (GREEN) blocks on T6.**

### Sizing and complexity rationale

Under the two-axis gate, `complexity: high` forces a split or an explicit
de-risking step regardless of size. The decomposition above satisfies that
gate, and the four split/deferral decisions are recorded here so they are not
re-litigated:

* **Assembly and judgement are separate tasks.** Assembling an input set and
  judging that set for contamination are two distinct jobs; combined they rate
  `high`. Split into **T4a** (assembly) and **T4b** (leak detection), each a
  single predicate over a defined input, each `medium`. The boundary is stated
  on both task rows so the two halves cannot both claim the classification
  predicate.
* **Document production and cross-artifact linkage are separate tasks.**
  Generating a document and performing cross-artifact state transitions are
  different failure modes. Split into **T5a** (generate the next revision) and
  **T5b** (supersession bookkeeping), with T5b blocking on T5a so ordering is
  machine-encoded. The boundary is stated on both rows so the two halves cannot
  both claim the manifest write.
* **The verifier implements six structural tokens, not seven.** With
  `PLAN_BUDGET_BREACH` deferred there is no tunable threshold in it; the
  remaining six are structural checks over metadata defined by T1–T3, so T6 is
  `medium` without a further split, and T6a/T6b prove each token independently.
* **The repository-wide migration is deferred, and the deferral is the split.**
  It was the highest-risk surface and the one least reducible to a 2-hour unit.

No task in this release unit carries `complexity: high`. No task exceeds `M`.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* Every blocking token in the verifier table has one passing and one failing
  concrete case.
* The verifier implements exactly six blocking tokens; no budget token is
  reachable in this release unit.
* `PLAN_LEGACY_UNIDENTIFIED` is asserted to be **reported and non-blocking** —
  a legacy plan must not stop a review dispatch.
* A `plan_id` rename produces exactly one active plan, not two.
* The assembler emits a two-band `ReviewInputSet`; a `superseded`/`history`
  document placed in the `operative` band raises `REVIEW_INPUT_HISTORY_LEAK`,
  and no token is evaluated against the `context` band.
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
| R6 | A reviewer reads a plan-size budget as in force | `PLAN_BUDGET_BREACH` appears in no token table in this unit; Verification asserts the verifier implements six blocking tokens |
| R7 | Carried-forward context is read as operative contract text | The assembler emits two disjoint, differently typed bands; the `operative` band holds exactly one `plan_role: active` document, and flattening the bands is a visible code change rather than an accident |

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

**Hardening trigger.** Elevated blast radius on several axes: the change spans
`schemas/`, skill workflows and their templates, and an agent template with its
installed mirror. It also changes the contract that reviewer agents themselves
consume, so a defect in it degrades the mechanism that would otherwise catch
the defect.

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

| # | Hazard | Resolution in this contract |
|---|---|---|
| H1 | A covering feature spanning six independent surfaces with six independent failure modes is not one release unit | Scope reduced to the three properties the Problem section's evidence turns on; four surfaces deferred as named, traceable Stage entries |
| H2 | A repository-wide migration is the highest-blast-radius surface available and the least reducible to a 2-hour unit, yet reads as a co-requisite of the contract | Deferred entirely. Legacy plans handled by the non-blocking `PLAN_LEGACY_UNIDENTIFIED` classification, which requires no code that can rewrite or delete anything |
| H3 | A migration-before-enforcement ordering rule is a mitigation for a hazard created by bundling the two | Hazard dissolved rather than sequenced around: with no migration in the unit, there is no race for the validator to lose |
| H4 | A hard-fail plan-size threshold calibrated on pre-contract evidence would be obsolete the moment the contract lands | Deferred with the budget surface; the six remaining tokens are structural, with nothing to tune |
| H5 | Shipping `complexity: high` tasks violates the two-axis gate | T4 and T5 split into T4a/T4b and T5a/T5b; the verifier reduced to `medium` by token removal; the migration deferred. No remaining task is `high` |
| H6 | Prose-only task ordering is unenforceable | `Blocked by` column encoded per task; T5b→T5a, T4b→T4a, T6→T6a and T6b→T6 are machine edges |
| H7 | A review record that combines two cycles in one mutable file is the exact defect this plan exists to fix | Review history split into immutable per-attempt artifacts under `docs/reviews/review-history/`, with `linked_review` naming the latest-verdict manifest; both recorded in frontmatter |
| H8 | Reflexivity: a defect in this contract degrades the reviewer mechanism that would catch it | T6a/T6b assert each token independently against concrete fixture states rather than against the live repository, so the suite does not depend on the contract being already correct |
| H9 | "Carried-forward context" with no defined manifest field is either vacuous or improvised per caller | `carried_forward_context[]` defined as `{artifact, reason}` on the manifest, surfaced only in the `context` band of a two-band typed `ReviewInputSet` |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Add plan identity fields to `schemas/` (T1, T2, T3) | Low — additive; legacy plans classified, not rejected | Standard PR review | Revert schema files |
| Change the plan-review skill's input assembly and remediation path (T4a/T4b/T5a/T5b) | Medium — alters the contract reviewer agents consume | Standard PR review | Revert skill + template pair together |
| Change the Stage agent template and installed mirror (T7) | Medium — agent contract, mirrored pair | Standard PR review | Revert both copies together |
| Enable the pre-dispatch verifier at blocking severity (T6) | Medium — can halt review dispatch | Standard PR review; `PLAN_LEGACY_UNIDENTIFIED` non-blocking by construction | Disable the verifier call site; no persisted state |

**Rollback coupling.** T1–T3 revert as a schema set. T4a/T4b/T5a/T5b revert as
the plan-review skill pair (installed + template). T7 reverts as the Stage
agent pair. T6 is a single call site. T6a/T6b are test-only. Nothing in the unit
mutates persisted artifacts, so rollback is code-only.

**Monitoring and validation window.** The first remediation cycle executed
after merge is the live signal: it must produce a new revision document plus a
new immutable attempt artifact, and must leave the prior revision marked
`superseded`. A cycle that instead appends to the live plan is a contract
failure visible in the diff.

**Operator checkpoints.** None. Every action in the unit is additive schema,
skill, or agent-template text plus tests; no persisted artifact is rewritten
and no migration is performed.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers, MUST apply the Agent-Native Parity
persona inline because this plan changes agent-facing skill and agent-template
contracts, and MUST be written as a separate immutable attempt artifact — this
plan's own subject matter makes any other form self-contradicting.

**Unresolved operator decisions blocking safe execution.** None.
