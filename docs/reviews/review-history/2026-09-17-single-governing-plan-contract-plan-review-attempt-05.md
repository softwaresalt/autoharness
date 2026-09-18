---
title: "Plan review attempt 05 — Single governing plan contract (plan revision 5)"
description: "Immutable per-attempt plan-review artifact. Records the final independent review cycle against docs/plans/2026-09-17-single-governing-plan-contract-plan.md at revision 4 - verdict BLOCKED because the plan, its harvested tasks and the live manifests each declared a different wire format for the same records, and because task T4a required a carried-forward-context field that T3 never defined - together with the Stage remediation-cycle-3 response that raises the plan to revision 5. Disposition: REMEDIATED-PENDING-REVIEW. Stage does not review its own remediation and asserts no PASS."
doc_type: review
source: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 5
attempt_range: "05"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-single-governing-plan-contract-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-04.md
plan_path: docs/plans/2026-09-17-single-governing-plan-contract-plan.md
plan_revision: 5
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: C9CD24F3
feature_id: 171-F
shipment_id: 179-S
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
  - "governing-plan"
  - "wire-format"
  - "review-input-set"
  - "remediation-cycle-3"
---

# Plan review attempt 05 — Single governing plan contract

## Scope of this attempt

Independent review cycle 3 - the **final authorized review-fix cycle** - opened
against **plan revision 4** and returned **BLOCKED** with two findings scoped
to this plan. Both are contract-identity failures: the same record was
described three different ways across the plan, its tasks and the live
artifacts, and a required input had no defined representation.

Operative input set: plan revision 4, its verdict manifest, the live `171-F` /
`179-S` backlog records (notably `171.001-T` and `171.003-T`), and the live
verdict manifests under `docs/reviews/`. Attempts 01-02, 03 and 04 are
preserved in `review-history/` and are excluded from the operative set as
superseded history.

dispatch_mode: `declared-degradation`

`TOOL_DEGRADED: reviewer-subagent-dispatch - declared fallback: single-agent
persona pass`. No reviewer subagent was dispatched; the cycle-3 findings were
operator-supplied and are recorded here as received.

## Findings raised at revision 4, and their closure at revision 5

| ID | Finding (independent review cycle 3) | Closure evidence |
|---|---|---|
| B6 | **Three conflicting wire formats for the same records.** The plan required `plan_role` plus **path-valued** `supersedes` / `source_history` / `review_manifest`; `171.001-T` instead specified a **status-valued** `supersedes` / `superseded_by` pair keyed on revision; and `171.003-T` named the field `plan_revision_reviewed` while every live manifest under `docs/reviews/` actually uses `plan_revision`. No implementer could satisfy all three, and the conformance test would have asserted whichever one its author happened to read | The plan now carries a **single normative wire-format table** of exactly seven plan-identity fields - `plan_id`, `plan_role`, `revision`, `supersedes`, `superseded_by`, `source_history`, `review_manifest` - with type and requiredness per field, and **two explicit naming decisions recorded with their reasons**: (1) the role field is **`plan_role`, never `status`**, because plan frontmatter already uses `status: draft\|reviewed` for a different axis; (2) `supersedes` / `superseded_by` are **repo-relative paths, never `(plan_id, revision)` pairs**, because the fail-closed token `PLAN_SUPERSEDES_CYCLE` is specified as firing on "cyclic **or unresolvable**", which presupposes a resolvable reference. A second normative table pins the manifest wire format against the **live** manifests: **`plan_revision` is the field**, and **`plan_revision_reviewed` is declared to be a field name nowhere in the contract**. `171.001-T`, `171.003-T`, `171.004-T` and `171.013-T` are aligned to this one contract |
| B6b | **`T4a` required "carried-forward context" that `T3` never defined**, so a required review input had no representation - and any ad-hoc representation risked the context silently becoming operative input, which is exactly the history-leak the plan exists to prevent | `carried_forward_context[]` is added to the manifest wire format as a list of `{artifact, reason}` entries, and a new section defines a **two-band typed value** `ReviewInputSet(operative, context)`. `operative` holds **exactly one** document with `plan_role: active`; a superseded or history document appearing in `operative` raises **`REVIEW_INPUT_HISTORY_LEAK`**. Flattening the two bands into a single list is declared a contract violation. The representation therefore *cannot* become operative input by construction, rather than by convention |
## The one contract, stated once

For the avoidance of a fourth variant, the governing contract after revision 5
is exactly:

* **Plan identity** - `plan_id`, `plan_role` (`active` \| `superseded` \|
  `history`), `revision`, `supersedes` (path \| null), `superseded_by`
  (path \| null), `source_history` (list of paths), `review_manifest` (path).
* **Manifest** - `plan_revision` (integer, **not** `plan_revision_reviewed`),
  `latest_attempt`, `latest_attempt_artifact`, `verdict`, `attempts[]`,
  `carried_forward_context[]`.
* **Assembly** - `ReviewInputSet(operative, context)`, `operative` cardinality
  exactly one, violation token `REVIEW_INPUT_HISTORY_LEAK`.

Every plan sentence, task body, test description and verdict surface in scope
now states this and only this.

## Dependency graph as propagated

```text
No dependency edges changed for `171-F` / `179-S` in this attempt. The
corrections are to the *content* of T1, T3, T4a, T4b, T5a and T5b and to the
harvested bodies of `171.001-T`, `171.003-T`, `171.004-T` and `171.013-T`.
Twelve members remain the exact membership of `179-S`.
```

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
* Both cycle-3 P1 findings scoped to this plan (**B6, B6b**) are closed at the
  document and record level, with a single normative contract replacing three
  conflicting ones.
* Verdict carried forward to the manifest: **REMEDIATED-PENDING-REVIEW**. The
  next reviewer pass is attempt 06.