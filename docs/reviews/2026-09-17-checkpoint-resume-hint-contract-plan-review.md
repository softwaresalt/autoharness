---
title: "Plan review verdict manifest — Checkpoint resume_hint contract"
description: "Mutable verdict manifest for docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. The reviews live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 06. Plan revision: 6. Verdict: REMEDIATED-PENDING-REVIEW, derived from the roster - the attempt-06 reviewer verdict was BLOCKED and the revision now governing was produced by operator-authorized Stage remediation, which no reviewer has evaluated. The next independent pass is attempt 07."
doc_type: review-manifest
source: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
date: 2026-09-19
plan_id: checkpoint-resume-hint-contract
plan_path: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
plan_revision: 6
latest_attempt: 6
verdict: REMEDIATED-PENDING-REVIEW
latest_artifact: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-06.md
attempts:
  - attempt: "01-02"
    artifact: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempts-01-02-combined.md
    reviewed_revision: 2
    verdict: PASS
    remediation_revision: null
    disposition: null
  - attempt: 3
    artifact: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-03.md
    reviewed_revision: 3
    verdict: PASS
    remediation_revision: null
    disposition: null
  - attempt: 4
    artifact: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-04.md
    reviewed_revision: 3
    verdict: BLOCKED
    remediation_revision: 4
    disposition: REMEDIATED-PENDING-REVIEW
  - attempt: 5
    artifact: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-05.md
    reviewed_revision: 4
    verdict: BLOCKED
    remediation_revision: 5
    disposition: REMEDIATED-PENDING-REVIEW
  - attempt: 6
    artifact: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-06.md
    reviewed_revision: 5
    verdict: BLOCKED
    remediation_revision: 6
    disposition: REMEDIATED-PENDING-REVIEW
carried_forward_context:
  - artifact: docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md
    reason: "Attempt-05 records conflate the reviewed revision 4 with the Stage-produced revision 5; this erratum states the corrected reading without editing the immutable records."
tags:
  - "plan-review"
  - "verdict-manifest"
  - "portfolio-2026-09-17"
---

# Plan review verdict manifest — Checkpoint resume_hint contract

## What this file is

A **selection surface**, not a review. It answers one question — *which
review attempt is authoritative right now* — and nothing else.

The review records themselves are immutable, one file per attempt, under
`docs/reviews/review-history/`. They are never edited after they are written.
This manifest is the only mutable part of the review surface, and the only
thing it ever changes is which attempt it points at.

The wire format is the one specified by
`docs/plans/2026-09-17-single-governing-plan-contract-plan.md`: the eight
contract keys `plan_id`, `plan_path`, `plan_revision`, `latest_attempt`,
`verdict`, `latest_artifact`, `attempts[]` and `carried_forward_context[]`,
carried alongside the workspace docline keys. `plan_revision_reviewed` is not
a field name in this contract, and `latest_attempt_artifact` is not its key
name.

## Current verdict

| Field | Value |
|---|---|
| `plan_id` | `checkpoint-resume-hint-contract` |
| `plan_path` | `docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md` |
| `plan_revision` | 6 |
| `latest_attempt` | **06** |
| `latest_artifact` | `docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-06.md` |
| `verdict` | **REMEDIATED-PENDING-REVIEW** (derived) |

**The top-level `verdict` is derived, not authored.** Take the
highest-numbered roster entry — attempt 06. Its `remediation_revision` is
6, which equals `plan_revision`, so the top-level `verdict` is that
entry's `disposition`: `REMEDIATED-PENDING-REVIEW`. A reviewer's `PASS` is
therefore not something this manifest can assert while the governing revision
is one Stage produced.

## What attempt 06 records

Independent attempt-06 review opened against plan revision 5 and returned BLOCKED on three defects: an undefined ValidationOutcome for an active historical checkpoint with a missing or empty resume_hint; a TDD spine whose RED, implementation, wiring and verification tasks were mis-ordered and mis-owned; and an unplanned atomic update to the authoritative Checkpoint Payload Contract, which still advertised direct backlogit_create_checkpoint and backlogit checkpoint create calls as permitted harness producer paths with structural coverage limited to two agent templates. The portfolio-wide plan-identity wire-format finding also applied. Operator-authorized remediation made classification total and deterministic with the new blocking CHECKPOINT_ACTIVE_HINTLESS token, encoded the single five-node TDD spine in every body and machine edge, assigned the atomic contract-and-mirror update with checksum regeneration to 172.001-T, added inventory-backed structural verifier 172.010-T, and applied the seven identity fields, raising the plan to revision 6. Stage does not review its own remediation; awaiting independent attempt 07.

## Attempt roster

`reviewed_revision` + `verdict` are what an **independent reviewer** judged.
`remediation_revision` + `disposition` are what **Stage** produced in response.
They are separate columns because merging them is how a fabricated PASS enters
the record — the exact defect the attempt-05 artifacts carry, documented in
`docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md`.
`REMEDIATED-PENDING-REVIEW` is never a `verdict` value; it is only ever a
`disposition`.

| Attempt | Artifact | Reviewed rev | Reviewer verdict | Remediation rev | Disposition |
|---|---|---|---|---|---|
| 01–02 | `...-plan-review-attempts-01-02-combined.md` | 2 | PASS | — | — |
| 03 | `...-plan-review-attempt-03.md` | 3 | PASS | — | — |
| 04 | `...-plan-review-attempt-04.md` | 3 | BLOCKED | 4 | REMEDIATED-PENDING-REVIEW |
| 05 | `...-plan-review-attempt-05.md` | 4 | BLOCKED | 5 | REMEDIATED-PENDING-REVIEW |
| 06 | `...-plan-review-attempt-06.md` | 5 | BLOCKED | 6 | REMEDIATED-PENDING-REVIEW |

Attempts 01–02 were written as a single document covering two cycles. That
file is preserved verbatim rather than retroactively split — fabricating two
independently-authored records from a document never authored that way would be
a provenance forgery. Its `reviewed_revision` is recorded as 2, the revision the
document itself names; the pre-remediation cycle merged into it is not
separately recoverable from the record, and is not invented here.

## Carried-forward context

Every entry below is **context, never operative input**. These paths surface
only in the `context` band of the two-band `ReviewInputSet`; any of them
appearing in the `operative` band blocks with `REVIEW_INPUT_HISTORY_LEAK`,
regardless of filename or location.

* `docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md` — Attempt-05 records conflate the reviewed revision 4 with the Stage-produced revision 5; this erratum states the corrected reading without editing the immutable records.

## Selection rule

Consumers resolve the governing verdict by reading `latest_attempt` and
`latest_artifact` from this file's frontmatter, and cross-check the top-level
`verdict` against the roster derivation above. A disagreement between the two
is `REVIEW_VERDICT_AMBIGUOUS`, not a matter of narrative. Superseded attempts
are history: readable for provenance, never operative input to a later review.
