---
title: "Plan review attempt 05 — Checkpoint resume_hint contract (plan revision 5)"
description: "Immutable per-attempt plan-review artifact. Records the final independent review cycle against docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md at revision 4 - verdict BLOCKED because a package-local Python function was named as the enforceable boundary against Markdown agent producers that call backlogit MCP/CLI directly and import no Python, and because the task graph inverted structural assertion against the wiring it asserts - together with the Stage remediation-cycle-3 response that raises the plan to revision 5. Disposition: REMEDIATED-PENDING-REVIEW. Stage does not review its own remediation and asserts no PASS."
doc_type: review
source: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-05.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 5
attempt_range: "05"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-04.md
plan_path: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
plan_revision: 5
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 71200CBB
feature_id: 172-F
shipment_id: 180-S
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
  - "checkpoint"
  - "resume-hint"
  - "validation-boundary"
  - "dependency-ordering"
  - "remediation-cycle-3"
---

# Plan review attempt 05 — Checkpoint resume_hint contract

## Scope of this attempt

Independent review cycle 3 - the **final authorized review-fix cycle** - opened
against **plan revision 4** and returned **BLOCKED** with two findings scoped
to this plan. Both concern executability: an enforcement point that could not
enforce, and an ordering that could not hold.

Operative input set: plan revision 4, its verdict manifest, the live `172-F` /
`180-S` backlog records, the installed `backlogit.instructions.md`, and the
Stage and Ship agent templates. Attempts 01-02, 03 and 04 are preserved in
`review-history/` and are excluded from the operative set as superseded
history.

dispatch_mode: `declared-degradation`

`TOOL_DEGRADED: reviewer-subagent-dispatch - declared fallback: single-agent
persona pass`. No reviewer subagent was dispatched; the cycle-3 findings were
operator-supplied and are recorded here as received.

## Findings raised at revision 4, and their closure at revision 5

| ID | Finding (independent review cycle 3) | Closure evidence |
|---|---|---|
| B4 | **The validation boundary was not enforceable.** Revision 4 named the package-local Python function `validate_checkpoint_payload()` in `src/autoharness/` as the boundary "both producer paths must route through". But the two producers are **Markdown agent templates** - Stage and Ship - which call `backlogit_create_checkpoint` (MCP) or `backlogit checkpoint create` (CLI) **directly** and import no Python at all. A library function sitting beside that call path cannot intercept it. "Both producer paths call this exact function" was therefore an instruction with no mechanism, and T6''s structural assertion had no wiring to assert | The boundary is redefined as an **executable adapter**: `autoharness checkpoint create --state-dump <path-or-json> [--origin harness]`. Producers invoke the adapter **instead of** the raw create operation. The adapter validates **strictly pre-write**, writes **nothing** on a failing outcome, and on a clean outcome performs the **official backlogit create call itself** - so `backlogit.instructions.md` rule 2 ("only through the official create operation") is preserved, because the adapter *is* how that operation is reached. `validate_checkpoint_payload(payload, *, origin)` survives as the **single predicate** with exactly two callers: the adapter and the startup scan. Crucially, "did this template invoke the adapter, or the raw tool?" is now a **decidable property of the template text**, which is what makes T6''s assertion meaningful |
| B7 | **Dependency inversion in the task graph.** Revision 4 encoded `T5c -> T3, T4, T5, T6` while specifying T6 as the step that asserts the producer wiring **that T5c creates**. A structural assertion cannot precede its own subject: T6 could only have failed permanently or been quietly weakened until it asserted nothing | The edges are swapped. The order is now `T5a` (RED) -> `T5` (implement, inert) -> `T5c` (ENABLE the wiring; blocked by `T3, T4, T5` - **no longer by T6**) -> `T6` (GREEN plus structural verifier; blocked by `T5c`) -> `T7` (live audit; blocked by `T6`). The *Ordering enforcement* section is rewritten for revision 5, naming the inversion and the swapped edges explicitly so the correction is auditable rather than silent |
| B7a | Downstream surfaces still described the withdrawn four-edge set and the library-call framing | Risks **R1** and **R5** rewritten; **R8** (adapter drifting into a second checkpoint store) and **R9** (assertion written against non-existent wiring) added; hardening **H1**, **H2** and **H3** rewritten with the revision-5 correction recorded as superseding revision 4; the T5c risky-action row now names the three-edge predecessor set and `T6 -> T5c`; Verification bullets and the monitoring window now name the adapter |
## Why the adapter is not a second checkpoint store

This was checked explicitly, because an adapter that *writes* would violate the
instruction the plan is meant to uphold.

* The adapter adds **no storage capability**. It validates, then delegates to
  the official backlogit create operation.
* It adds **no schema**, **no field**, and **no default**; a payload that
  passes validation is forwarded unchanged.
* On a failing outcome it exits non-zero and performs **no** create call, so no
  malformed record reaches disk - which is the whole reason validation must be
  pre-write rather than post-write.

Risk **R8** records the drift hazard and the constraint that closes it.

## Dependency graph as propagated

```text
T5a (172.00?-T, RED)        → no functional predecessor
T5  (implement, inert)      → blocked by T5a
T5c (enable wiring)         → blocked by T3, T4, T5     [was: T3, T4, T5, T6]
T6  (green + structural)    → blocked by T5c            [new edge; was reversed]
T7  (live corpus audit)     → blocked by T6
```

Concretely, in the harvested graph: the edge `172.009-T → 172.006-T` is
removed, the edge `172.006-T → 172.009-T` is added, and `172.007-T` is
retargeted from `172.009-T` onto `172.006-T`. Ten members remain the exact
membership of `180-S`; no member is added or removed.

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
* Both cycle-3 P1 findings scoped to this plan (**B4, B7**, with propagation
  corollary **B7a**) are closed at the document and record level, including the
  swapped dependency edges in the live graph.
* Verdict carried forward to the manifest: **REMEDIATED-PENDING-REVIEW**. The
  next reviewer pass is attempt 06.