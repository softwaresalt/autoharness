---
title: "Plan review attempt 05 — P-004 red-phase precondition scoping (plan revision 5)"
description: "Immutable per-attempt plan-review artifact. Records the final independent review cycle against docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md at revision 4 — verdict BLOCKED on an incorrect CPython unittest loader contract, an over-assignment of value-uniqueness and cross-list disjointness to a Draft-07 JSON Schema that cannot express either, and an unaddressed bootstrap deadlock that made shipment 176-S unexecutable under the very policy it repairs — together with the Stage remediation-cycle-3 response that raises the plan to revision 5. Disposition: REMEDIATED-PENDING-REVIEW. Stage does not review its own remediation and asserts no PASS."
doc_type: review
source: docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-05.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 5
attempt_range: "05"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-p004-red-phase-precondition-scoping-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-04.md
plan_path: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
plan_revision: 5
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 76EBDE6D
feature_id: 168-F
shipment_id: 176-S
review_cycle: 5
review_cycles_remaining: 0
dispatch_mode: declared-degradation
decision: REMEDIATED-PENDING-REVIEW
verdict_at_entry: BLOCKED
verdict_at_entry_plan_revision: 4
p0_open: 0
p1_open: 0
tags:
  - "plan-review"
  - "p004"
  - "red-phase"
  - "unittest-loader"
  - "json-schema-draft-07"
  - "bootstrap"
  - "remediation-cycle-3"
---

# Plan review attempt 05 — P-004 red-phase precondition scoping

## Scope of this attempt

Independent review cycle 3 — the **final authorized review-fix cycle** — opened
against **plan revision 4** and returned **BLOCKED**. Three findings were scoped
to this plan, plus one label defect. Every one of them concerned a contract that
was stated but not *executable as stated*: an algorithm that the standard
library does not behave the way the plan claims, a constraint assigned to a
validator that provably cannot express it, and an entry point that no agent
could legally reach.

Operative input set: plan revision 4, its verdict manifest, the live `168-F` /
`176-S` backlog records, and the installed policy text in
`.github/policies/workflow-policies.md`. Attempts 01–02, 03 and 04 are
preserved in `review-history/` and are excluded from the operative set as
superseded history.

dispatch_mode: `declared-degradation`

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent
persona pass`. No reviewer subagent was dispatched for this attempt; the
cycle-3 findings were operator-supplied and are recorded here as received,
unaltered.

## Findings raised at revision 4, and their closure at revision 5

| ID | Finding (independent review cycle 3) | Closure evidence |
|---|---|---|
| B2 | **The unittest loader contract is wrong.** Revision 4's Load step called `loader.loadTestsFromNames(declared)` and then treated the result as one test per name and `TestLoader.errors` as a mapping keyed by name. Neither holds in CPython: `loadTestsFromNames` returns `suiteClass([loadTestsFromName(n) for n in names])`, i.e. one *suite* per name, and on a failed load that suite contains a synthetic `_FailedTest` whose `id()` is **not** guaranteed to equal the requested name; `TestLoader.errors` is a flat **list of formatted strings** appended in load order, with no key at all. The algorithm as written could not attribute an error to the name that caused it | The Load step is replaced with a stdlib-only algorithm that is correct against the actual API: each declared name is loaded **independently** via `loadTestsFromName`, `len(loader.errors)` is **snapshotted before and after each call** so the slice `loader.errors[before:]` attributes messages to exactly one requested name, the returned suite is **recursively flattened** to leaf tests, and results are correlated back through an `id(test_object) -> requested_name` identity map rather than by comparing `test.id()` strings. The plan carries the executable ~25-line block. Run and Compare are rewritten to key on the requested name |
| B3 | **Draft-07 cannot express what was assigned to it.** `168.001-T` assigned duplicate-`test_id` detection and red/green set disjointness to the JSON Schema. All nine files under `schemas/` declare `http://json-schema.org/draft-07/schema#`. `uniqueItems` compares **whole instances**, so `{test_id: X, marker: "a"}` and `{test_id: X, marker: "b"}` both validate; and Draft-07 has no cross-property or cross-list value comparison at all, so disjointness is inexpressible. Both fail-closed tokens would have silently never fired | A new section, *Where each constraint is enforced (revision 5)*, proves the limitation and **moves both constraints to the Python validation boundary**. A two-row ownership table now governs: the **schema** owns per-item shape only (`required`, `additionalProperties: false`, `minLength: 1`, `minItems: 1` → `P004_MARKER_MISPLACED`, `P004_EMPTY_RED_SET`); **`validate_declared_harness_set()`** owns `P004_DUPLICATE_DECLARATION` and `P004_SET_OVERLAP`. The keyed-map alternative is considered and **rejected** on the record: mainstream YAML loaders make a duplicate key silently last-wins, converting a fail-closed error into silent data loss. `168.001-T` is narrowed to per-item shape; `168.007-T` gains the validator. A verification case asserts the schema **accepts** a duplicate, as positive proof the constraint moved rather than being asserted in two places |
| B11 | **`176-S` had no executable bootstrap.** P-002's installed enforcement filters the ready queue to tasks carrying `harness-ready`, with no unlabelled path; `harness-ready` requires a P-004 red-phase confirmation; and P-004's installed precondition demands a whole-suite `discover` exiting non-zero "for every test function", which is unsatisfiable by construction. The shipment whose purpose is to repair P-004 was therefore gated behind the broken P-004 — no legal path existed from shipment claim to first task claim | A new section, *Bootstrap: how `176-S` becomes executable at all (revision 5)*, reproduces the installed P-002/P-004 text, demonstrates the deadlock, and defines a **bounded, fail-closed bootstrap acceptance contract** delivered as new task **T0**. T0 applies decision D4's *already-authorized* declared-harness-set contract to `176-S` alone; it is scoped to that one shipment, expires at T3 when the general contract lands, relaxes no exit code, grants no waiver or force flag, and runs through P-004's **existing Operator Approval Gate** — an authority already present in the installed policy, not an invented one. T0 becomes the DAG entry point and blocks T1 |
| P2-R7 | Risk **R7** and hardening entry **H7** named task "T5", which is not a task in this plan's breakdown | Both corrected to **T5b**. No other plan-relative label in the document resolves to a non-existent task |

## What was added beyond the literal findings

Closing B2, B3 and B11 required new assertions, without which the corrections
would be unverifiable:

* Three new risks — **R8** (schema silently non-enforcing after the constraint
  move), **R9** (the bootstrap being cited as precedent for future bypasses),
  **R10** (a `test_id` addressed at module or class granularity).
* Three new hardening entries — **H9** (loader contract), **H10** (schema
  over-assignment), **H11** (bootstrap impossibility).
* Six new verification cases, including the module/class-addressed case, the
  `_FailedTest.id()` mismatch case, second-name-only error attribution,
  duplicate/overlap detection from the Python boundary, the schema-accepts-a-
  duplicate positive case, and T0's fail-closed confirmation.
* The fail-closed token table is **broadened, not grown**:
  `P004_MISSING_OBSERVATION` now covers zero tests, more than one test, and a
  load error; `P004_UNDECLARED_OBSERVATION` covers surplus tests arriving from
  module- or class-addressed names. The token count remains exactly **nine**.

## Dependency graph as propagated

```text
T0 (168.009-T, bootstrap) → entry point, no predecessor
T1 (168.001-T, schema/per-item shape) → blocked by T0
... remaining edges unchanged from revision 4 ...
T0 expires at T3; it is not a general P-004 relaxation.
```

`176-S` membership grows by exactly one member (`168.009-T`). The covering
feature `168-F` grows from eight to nine tasks. No other feature or shipment
manifest changes.

## Portfolio-wide findings closed in this attempt

These findings were raised against the portfolio as a whole and are recorded
identically in all six attempt-05 artifacts.

| ID | Finding (independent review cycle 3) | Closure evidence |
|---|---|---|
| B1 | **Denormalized review surfaces contradicted the authoritative ones.** All six plans carried `latest_review_attempt: 3` and `latest_review_verdict: PASS` while their newest review artifact was attempt **04** and their verdict manifests read `REMEDIATED-PENDING-REVIEW` at `plan_revision: 4`. A consumer reading the plan frontmatter would have concluded the portfolio had passed review | Every plan's `latest_review_attempt` is now **5**, `latest_review_artifact` points at its attempt-05 artifact, and `latest_review_verdict` is **`REMEDIATED-PENDING-REVIEW`** with an explanatory `latest_review_verdict_note`. Each `review_history` list gains the attempt-05 path. Each manifest reads `latest_attempt: 5`, `plan_revision: 5`, `verdict: REMEDIATED-PENDING-REVIEW`, with the attempt-4 entry marked `superseded_by: 5`. **No PASS is asserted anywhere at revision 5.** The next independent reviewer pass is attempt 06 |
| B9 | **Current-state memory and handoff were stale**, describing 48 tasks, a serial shipment DAG, decision revision 1, and no `168-S` mutation | A refreshed current-state record supersedes them: **55 covering-feature tasks** at entry (**56** after `168.009-T`), fan-out root **`176-S`**, the `168-S → 176-S` edge, **decision revision 3**, the deferred features `174-F` / `175-F`, and the P-021 deferred stash IDs. The stale records are marked **explicitly superseded** and preserved, not deleted |
| B10 | **The terminal checkpoint `checkpoint-20260918-153229` was stale** relative to the work performed after it | A new checkpoint is created through the **official backlogit create operation** at `schema_version: 1`, with all domain and progress data nested under `context` and a truthful `resume_hint`, then **resolved** in the same session. Because a checkpoint cannot know the SHA of a commit that does not yet exist, it is bound to the exact **parent HEAD `93ffe7da`** plus an explicit enumeration of the **pending uncommitted remediation diff scope** — it does not claim a future commit SHA. `checkpoint-20260916-064310.json` is preserved byte-unchanged |
| P2-174 | `174-F`'s children were expected to be `174.001-T` / `174.002-T`, with the pre-adoption IDs surviving only as history | Verified **already satisfied**: `174-F`'s live children are exactly `174.001-T` and `174.002-T`; the pre-adoption IDs no longer resolve to live records and appear only in historical narrative |
| P2-2D70D556 | Backlog record bodies lack the `# {title}` / `## Description` headings the installed templates declare | Re-confirmed as a **tool-owned writer defect**, already captured as compliant P-021 entry `2D70D556`. **No manual body rewrite was performed merely to add headings**; doing so would fabricate authorship of tool-owned output |

## What this attempt is, and is not

This artifact records the **final independent review cycle** and the Stage
remediation response to it. The cycle-3 verdict against plan revision 4 was
**BLOCKED**.

The remediation raises the plan to **revision 5**. It does **not** assert a
reviewer PASS at revision 5. Stage does not review its own remediation; the
manifest verdict is therefore `REMEDIATED-PENDING-REVIEW`, and the next
reviewer pass is **attempt 06**, which must be independent. `review_cycles_
remaining: 0` records that no further *Stage fix cycle* is authorized — it does
not authorize skipping attempt 06.

No test suite, linter, or build was executed during this remediation. Stage's
role boundary forbids it. No source, test, or configuration file was modified;
no commit, branch, push, or pull request was created.

## Disposition

* Plan raised to **revision 5**; `source_decision` resolves at
  **decision revision 3**.
* All cycle-3 P1 findings scoped to this plan (**B2, B3, B11**) and the P2
  label defect are closed at the document and record level.
* Verdict carried forward to the manifest: **REMEDIATED-PENDING-REVIEW**. The
  next reviewer pass is attempt 06.
