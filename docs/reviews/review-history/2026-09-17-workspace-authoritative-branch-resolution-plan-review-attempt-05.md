---
title: "Plan review attempt 05 — Workspace-authoritative branch resolution (plan revision 5)"
description: "Immutable per-attempt plan-review artifact. Records the final independent review cycle against docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md at revision 4 - verdict BLOCKED because divergence set D was empirically wrong: `git check-ref-format --branch` specially interprets `@{-N}` and accepts bare `@`, while the wider `@{...}` family is rejected exactly as rule V10 rejects it and is therefore shared behaviour, not divergence - together with the Stage remediation-cycle-3 response that raises the plan to revision 5. Disposition: REMEDIATED-PENDING-REVIEW. Stage does not review its own remediation and asserts no PASS."
doc_type: review
source: docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-05.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 5
attempt_range: "05"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-workspace-authoritative-branch-resolution-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-04.md
plan_path: docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md
plan_revision: 5
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 86498B64
feature_id: 170-F
shipment_id: 178-S
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
  - "branch-resolution"
  - "git-check-ref-format"
  - "divergence-set"
  - "hermetic-fixture"
  - "remediation-cycle-3"
---

# Plan review attempt 05 — Workspace-authoritative branch resolution

## Scope of this attempt

Independent review cycle 3 - the **final authorized review-fix cycle** - opened
against **plan revision 4** and returned **BLOCKED** with one finding scoped to
this plan. The finding was empirical, not stylistic: revision 4's divergence
set D described behaviour that `git` does not exhibit, so every assertion built
on D would have tested the wrong thing.

Operative input set: plan revision 4, its verdict manifest, the live `170-F` /
`178-S` backlog records, and read-only probes of the installed
`git version 2.55.0.windows.5`. Attempts 01-02, 03 and 04 are preserved in
`review-history/` and are excluded from the operative set as superseded
history.

dispatch_mode: `declared-degradation`

`TOOL_DEGRADED: reviewer-subagent-dispatch - declared fallback: single-agent
persona pass`. No reviewer subagent was dispatched for this attempt; the
cycle-3 finding was operator-supplied and was then **independently verified by
measurement** before remediation.

## Findings raised at revision 4, and their closure at revision 5

| ID | Finding (independent review cycle 3) | Closure evidence |
|---|---|---|
| B5 | **Divergence set D was wrong.** Revision 4 placed the whole `@{...}` family in D, claiming `git check-ref-format --branch` accepts it where rule V10 rejects it. Measurement disproves this. `--branch` first runs `interpret_branch_name`, which expands **only** the `@{-N}` previous-checkout form, and then runs `check_refname_format`, whose "cannot contain `@{`" rule rejects everything else. So `foo@{1}`, `main@{0}`, `a@{b}`, `@{u}`, `@{upstream}`, `foo@{upstream}` and `@{-0}` all exit **128** - a **shared** rejection agreeing with V10, not a divergence. Conversely revision 4 **missed** a real divergence: bare `@` exits 0 and prints `@` | The "Divergence set D" section is replaced with a **measured probe table** and the corrected definition: **D = { bare `@` } union { resolvable `@{-N}`, N >= 1 }**. The `@{...}` family is restated as a shared rejection and listed explicitly. The V10 row of the V1-V11 table is annotated with the correction. The mechanism (`interpret_branch_name` then `check_refname_format`) is documented so the boundary is derivable rather than memorized |
| B5a | **The `@{-N}` arm is reflog-dependent**, so an assertion written against the ambient repository would pass or fail according to the checkout history of whoever runs it | The plan now **requires a hermetic fixture repository** with a scripted checkout history for the `@{-N}` arm. The ambient reflog is explicitly forbidden as an assertion substrate. The "Superset pinning" section is rewritten around the fixture requirement, and the `T1` work-breakdown row names both the two-shape D and the fixture repo |
## Measured evidence of record

These probes were run read-only against `git version 2.55.0.windows.5` and are
the evidentiary basis for the corrected D. They are recorded here because a
future reviewer must be able to re-derive the boundary rather than trust it.

| Value | `git check-ref-format --branch` | V10 | Class |
|---|---|---|---|
| `@{-1}`, `@{-2}`, `@{-99}` | exit 0, resolves to a branch name | rejects | **divergence** (reflog-dependent) |
| `@` | exit 0, prints `@` | rejects | **divergence** |
| `@{-0}` | exit 128 | rejects | shared |
| `foo@{1}`, `main@{0}`, `a@{b}`, `@{u}`, `@{upstream}`, `foo@{upstream}` | exit 128 | rejects | shared |
| `--force`, `HEAD`, `a.lock`, `a..b` | exit 128 | rejects | shared |
| `x@`, `@x`, `feat/x` | exit 0 | accepts | agree |

Risk **R8** is updated and a new risk **R9** (reflog-dependent assertion) is
added; hardening entry **H2** is extended with the revision-5 correction.

## Dependency graph as propagated

```text
No dependency edges changed for `170-F` / `178-S` in this attempt. The
correction is to the *content* of T1 and its assertions, not to the task graph.
Eleven tasks plus the covering feature remain the exact membership of `178-S`.
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
* The cycle-3 P1 finding scoped to this plan (**B5**, with its fixture
  corollary **B5a**) is closed against measured evidence.
* Verdict carried forward to the manifest: **REMEDIATED-PENDING-REVIEW**. The
  next reviewer pass is attempt 06.