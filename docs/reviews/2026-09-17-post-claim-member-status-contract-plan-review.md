---
title: "Plan review verdict manifest — Canonical post-claim member-status contract"
description: "Latest-verdict manifest for docs/plans/2026-09-17-post-claim-member-status-contract-plan.md. This file is NOT a review record; it is the small mutable selection surface that names which immutable attempt artifact is authoritative. The reviews themselves live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 04. Verdict: REMEDIATED-PENDING-REVIEW at plan revision 4. Local review cycle 2 returned BLOCKED at revision 3 because the revision-3 design had not been propagated into the executable backlog records; Stage remediation cycle 2 propagated it. Stage does not review its own remediation, so no PASS is asserted at revision 4."
doc_type: review-manifest
source: docs/reviews/2026-09-17-post-claim-member-status-contract-plan-review.md
date: 2026-09-18
plan_path: docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
plan_revision: 4
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 3EF5AAF2
feature_id: 169-F
shipment_id: 177-S
latest_attempt: 4
latest_attempt_artifact: docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-04.md
verdict: REMEDIATED-PENDING-REVIEW
decision: REMEDIATED-PENDING-REVIEW
p0_open: 0
p1_open: 0
review_cycles_used: 4
review_cycles_remaining: 0
plan_hardening_status: complete
plan_hardening_evidence: "docs/plans/2026-09-17-post-claim-member-status-contract-plan.md#plan-hardening-record-p-006"
attempts:
  - attempt: "01-02"
    artifact: docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempts-01-02-combined.md
    conformance: non-conforming-combined
    plan_revision: 2
    verdict: PASS
    superseded_by: 3
    note: "Two review cycles recorded in one mutable file. Preserved verbatim as evidence; only classification keys added."
  - attempt: 3
    artifact: docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-03.md
    conformance: conforming
    plan_revision: 3
    verdict: PASS
    superseded_by: 4
    note: "Remediation-cycle-1 re-review. All consolidated blocking findings verified closed."
  - attempt: 4
    artifact: docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-04.md
    conformance: conforming
    plan_revision: 4
    verdict: REMEDIATED-PENDING-REVIEW
    superseded_by: null
    note: "Local review cycle 2: BLOCKED at plan revision 3 because the revision-3 design was never propagated into the executable backlog records. Stage remediation cycle 2 propagated it and raised the plan to revision 4. Stage does not review its own remediation; awaiting reviewer attempt 05."
tags:
  - "plan-review"
  - "verdict-manifest"
  - "remediation-cycle-1"
---

# Plan review verdict manifest — Canonical post-claim member-status contract

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
| Plan | `docs/plans/2026-09-17-post-claim-member-status-contract-plan.md` |
| Plan revision | 4 |
| Latest attempt | **04** |
| Authoritative artifact | `docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-04.md` |
| Verdict | **REMEDIATED-PENDING-REVIEW** |
| P0 open | 0 |
| P1 open | 0 |
| Plan hardening (P-006) | complete, persisted at `## Plan Hardening Record (P-006)` |
| Feature | `169-F` (6 tasks) |
| Shipment | `177-S` |

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
| 01–02 | `2026-09-17-post-claim-member-status-contract-plan-review-attempts-01-02-combined.md` | 2 | non-conforming-combined | PASS | superseded by 03 |
| 03 | `2026-09-17-post-claim-member-status-contract-plan-review-attempt-03.md` | 3 | conforming | PASS | superseded by 04 |
| 04 | `2026-09-17-post-claim-member-status-contract-plan-review-attempt-04.md` | 4 | conforming | REMEDIATED-PENDING-REVIEW | **authoritative** |

Attempts 01–02 were written as a single mutable document covering two cycles.
That file is preserved verbatim rather than retroactively split — fabricating
two independently-authored records from a document never authored that way
would be a provenance forgery. Only classification frontmatter keys were added.

## Selection rule

Consumers resolve the governing verdict by reading `latest_attempt` and
`latest_attempt_artifact` from this file's frontmatter. Superseded attempts are
history: readable for provenance, never operative input to a later review.
