---
title: "Plan review verdict manifest — Single-governing-plan contract"
description: "Latest-verdict manifest for docs/plans/2026-09-17-single-governing-plan-contract-plan.md. This file is NOT a review record; it is the small mutable selection surface that names which immutable attempt artifact is authoritative. The reviews themselves live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 05. Verdict: REMEDIATED-PENDING-REVIEW at plan revision 5. Independent review cycle 3 - the final authorized review-fix cycle - returned BLOCKED at revision 4; Stage remediation cycle 3 closed every finding and raised the plan to revision 5. No PASS is asserted at revision 5; the next independent reviewer pass is attempt 06. Local review cycle 2 returned BLOCKED at revision 3 because the revision-3 design had not been propagated into the executable backlog records; Stage remediation cycle 2 propagated it. Stage does not review its own remediation, so no PASS is asserted at revision 4."
doc_type: review-manifest
source: docs/reviews/2026-09-17-single-governing-plan-contract-plan-review.md
date: 2026-09-19
plan_path: docs/plans/2026-09-17-single-governing-plan-contract-plan.md
plan_revision: 5
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: C9CD24F3
feature_id: 171-F
shipment_id: 179-S
latest_attempt: 5
latest_attempt_artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md
verdict: REMEDIATED-PENDING-REVIEW
decision: REMEDIATED-PENDING-REVIEW
p0_open: 0
p1_open: 0
review_cycles_used: 5
review_cycles_remaining: 0
plan_hardening_status: complete
plan_hardening_evidence: "docs/plans/2026-09-17-single-governing-plan-contract-plan.md#plan-hardening-record-p-006"
attempts:
  - attempt: "01-02"
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempts-01-02-combined.md
    conformance: non-conforming-combined
    plan_revision: 2
    verdict: PASS
    superseded_by: 3
    note: "Two review cycles recorded in one mutable file. Preserved verbatim as evidence; only classification keys added."
  - attempt: 3
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-03.md
    conformance: conforming
    plan_revision: 3
    verdict: PASS
    superseded_by: 4
    note: "Remediation-cycle-1 re-review. All consolidated blocking findings verified closed."
  - attempt: 4
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-04.md
    conformance: conforming
    plan_revision: 4
    verdict: REMEDIATED-PENDING-REVIEW
    superseded_by: 5
    note: "Local review cycle 2: BLOCKED at plan revision 3 because the revision-3 design was never propagated into the executable backlog records. Stage remediation cycle 2 propagated it and raised the plan to revision 4. Stage does not review its own remediation; awaiting reviewer attempt 05."
  - attempt: 5
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md
    conformance: conforming
    plan_revision: 5
    verdict: REMEDIATED-PENDING-REVIEW
    superseded_by: null
    note: "Independent review cycle 3 (final authorized cycle): BLOCKED at plan revision 4 because the plan, 171.001-T and 171.003-T each declared a different wire format for the same records (plan_role with path-valued supersedes vs status/revision-valued supersedes; plan_revision_reviewed vs the plan_revision the live manifests actually use), and because T4a required a carried-forward-context field T3 never defined. Stage remediation cycle 3 pinned one normative contract across every plan, task, test and verdict surface, added carried_forward_context[] and the two-band ReviewInputSet(operative, context) with REVIEW_INPUT_HISTORY_LEAK, and raised the plan to revision 5. Stage does not review its own remediation; awaiting independent reviewer attempt 06."
tags:
  - "plan-review"
  - "verdict-manifest"
  - "remediation-cycle-1"
---

# Plan review verdict manifest — Single-governing-plan contract

## What this file is

A **selection surface**, not a review. It answers one question — *which review
attempt is authoritative right now* — and nothing else.

The review records themselves are immutable, one file per attempt, under
`docs/reviews/review-history/`. They are never edited after they are written.
This manifest is the only mutable part of the review surface, and the only
thing it ever changes is which attempt it points at.

This split is the contract that
`docs/plans/2026-09-17-single-governing-plan-contract-plan.md` specifies. It is
applied here to the whole portfolio, including to that plan's own review
history.

## Current verdict

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-17-single-governing-plan-contract-plan.md` |
| Plan revision | 5 |
| Latest attempt | **05** |
| Authoritative artifact | `docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md` |
| Verdict | **REMEDIATED-PENDING-REVIEW** |
| P0 open | 0 |
| P1 open | 0 |
| Plan hardening (P-006) | complete, persisted at `## Plan Hardening Record (P-006)` |
| Feature | `171-F` (11 tasks) |
| Shipment | `179-S` |

**What attempt 05 changed:** Independent review cycle 3 - the **final**
authorized review-fix cycle - returned **BLOCKED** at plan revision 4 on
three conflicting wire formats for the same records across the plan, `171.001-T` and `171.003-T`, and a `T4a` requirement for carried-forward context that `T3` never defined. Stage remediation cycle 3 pinned one normative contract - `plan_role` with path-valued `supersedes`/`superseded_by`, and `plan_revision` rather than `plan_revision_reviewed` - across every plan, task, test and verdict surface, and defined `carried_forward_context[]` plus the two-band `ReviewInputSet(operative, context)` so carried context cannot become operative input. Stage does not review its own
remediation, so the verdict is `REMEDIATED-PENDING-REVIEW` rather than PASS;
the next reviewer pass is **attempt 06**, which must be independent.
`review_cycles_remaining: 0` records that no further *Stage fix cycle* is
authorized - it does not authorize skipping attempt 06.

**What attempt 04 changed:** Local review cycle 2 returned **BLOCKED** at plan
revision 3 — not because the design was wrong, but because it had never been
propagated into the executable backlog records. Stage remediation cycle 2
propagated it: task bodies, titles, dependency edges, shipment manifests and
stash provenance were rewritten to match plan revision 4 and decision revision
3, descoped or blocked children were re-homed out of the covering features so
every shipment can genuinely close, and the TDD orderings were machine-encoded
as `blocks` edges instead of prose. Stage does not review its own remediation,
so the verdict is `REMEDIATED-PENDING-REVIEW` rather than PASS; the next
reviewer pass is attempt 05.

## Attempt history

| Attempt | Artifact | Plan rev | Conformance | Verdict | Status |
|---|---|---|---|---|---|
| 01–02 | `2026-09-17-single-governing-plan-contract-plan-review-attempts-01-02-combined.md` | 2 | non-conforming-combined | PASS | superseded by 03 |
| 03 | `2026-09-17-single-governing-plan-contract-plan-review-attempt-03.md` | 3 | conforming | PASS | superseded by 04 |
| 04 | `2026-09-17-single-governing-plan-contract-plan-review-attempt-04.md` | 4 | conforming | REMEDIATED-PENDING-REVIEW | superseded by 05 |
| 05 | `2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md` | 5 | conforming | REMEDIATED-PENDING-REVIEW | **authoritative** |

Attempts 01–02 were written as a single mutable document covering two cycles.
That file is preserved verbatim rather than retroactively split — fabricating
two independently-authored records from a document never authored that way
would be a provenance forgery. Only classification frontmatter keys were added.

## Selection rule

Consumers resolve the governing verdict by reading `latest_attempt` and
`latest_attempt_artifact` from this file's frontmatter. Superseded attempts are
history: readable for provenance, never operative input to a later review.
