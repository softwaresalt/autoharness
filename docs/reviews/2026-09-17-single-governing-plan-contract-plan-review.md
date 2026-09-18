---
title: "Plan review verdict manifest — Single governing plan contract"
description: "Mutable verdict manifest for docs/plans/2026-09-17-single-governing-plan-contract-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. The reviews live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 07 (terminal). Plan revision: 6. Verdict: BLOCKED, gate result FAIL, taken directly from the attempt-07 reviewer verdict against content HEAD 22bca5c8. Five P1 findings are open, including the attempts[] representation gap that the live rosters in this portfolio already exhibit. The authorized extra remediation cycle is exhausted, so no remediation followed and no further Stage fix cycle is authorized."
doc_type: review-manifest
source: docs/reviews/2026-09-17-single-governing-plan-contract-plan-review.md
date: 2026-09-18
plan_id: single-governing-plan-contract
plan_path: docs/plans/2026-09-17-single-governing-plan-contract-plan.md
plan_revision: 6
latest_attempt: 7
review_terminal: true
reviewed_content_head: 22bca5c8
gate_result: FAIL
verdict: BLOCKED
p0_open: 0
p1_open: 5
p2_open: 0
remediation_authorization: none-exhausted
latest_remediation_revision: null
latest_disposition: null
latest_artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-07.md
attempts:
  - attempt: "01-02"
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempts-01-02-combined.md
    reviewed_revision: 2
    verdict: PASS
    remediation_revision: null
    disposition: null
  - attempt: 3
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-03.md
    reviewed_revision: 3
    verdict: PASS
    remediation_revision: null
    disposition: null
  - attempt: 4
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-04.md
    reviewed_revision: 3
    verdict: BLOCKED
    remediation_revision: 4
    disposition: REMEDIATED-PENDING-REVIEW
  - attempt: 5
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md
    reviewed_revision: 4
    verdict: BLOCKED
    remediation_revision: 5
    disposition: REMEDIATED-PENDING-REVIEW
  - attempt: 6
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-06.md
    reviewed_revision: 5
    verdict: BLOCKED
    remediation_revision: 6
    disposition: REMEDIATED-PENDING-REVIEW
  - attempt: 7
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-07.md
    reviewed_revision: 6
    reviewed_content_head: 22bca5c8
    verdict: BLOCKED
    p1_open: 5
    p2_open: 0
    remediation_revision: null
    disposition: null
    terminal: true
carried_forward_context:
  - artifact: docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md
    reason: "Attempt-05 records conflate the reviewed revision 4 with the Stage-produced revision 5; this erratum states the corrected reading without editing the immutable records."
tags:
  - "plan-review"
  - "verdict-manifest"
  - "portfolio-2026-09-17"
---

# Plan review verdict manifest — Single governing plan contract

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
| `plan_id` | `single-governing-plan-contract` |
| `plan_path` | `docs/plans/2026-09-17-single-governing-plan-contract-plan.md` |
| `plan_revision` | 6 |
| `latest_attempt` | **07** (terminal) |
| `latest_artifact` | `docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-07.md` |
| `reviewed_content_head` | `22bca5c8` |
| `gate_result` | **FAIL** |
| `verdict` | **BLOCKED** (derived) |
| `p1_open` | **5** |
| `p2_open` | 0 |

**The top-level `verdict` is derived, not authored.** Take the
highest-numbered roster entry — attempt 07. Its `remediation_revision` is
`null`, so no Stage-produced revision supersedes what the reviewer judged, and
the top-level `verdict` is that entry's reviewer `verdict`: `BLOCKED`. The
authorized extra remediation cycle is exhausted; there is no further Stage fix
cycle, and no `PASS` exists anywhere in this record.

## What attempt 07 records

Terminal independent review opened against plan revision 6 at content HEAD `22bca5c8`; gate result FAIL, decision BLOCKED, five P1 findings open. Persona coverage was complete (Constitution, Python, Scope Boundary, Learnings, Architecture, Agent-Native Parity, Security Lens); the anchor route was absent so the cross-model rubric ran under same-model declared degradation, the Learnings persona was degraded because it could not inspect the diff, and Scope Boundary returned no P0/P1. The five open P1s are: the integer attempts[] contract cannot represent the legacy '01-02' entry carried by every live manifest here, nor the SAFE_CLOSE multipart attempt 06, and supplies no bounded compatibility representation or total latest-attempt selection rule; T4a and T4b are scoped as Markdown skill work while T6 imports and calls an assembler and a history predicate, so executable module ownership contradicts the task bodies; no initial impl-plan producer task emits the seven-field plan identity or initializes the verdict manifest before the pre-dispatch verifier activates; review-input and remediation paths are consumed without canonical workspace containment, traversal rejection or symlink rejection; and RED tests remain sequenced after schema and manifest implementation on several surfaces. No remediation followed.

The SAFE_CLOSE manifest's lossless `part`-keyed representation of its multipart attempt 06 is **evidence for** the first finding, not a proposed resolution of it.

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
| **07** (terminal) | `...-plan-review-attempt-07.md` | 6 @ `22bca5c8` | **BLOCKED** (5 P1 open) | — | — |

Attempt 07 has no `remediation_revision` and no `disposition` because the
operator-authorized extra remediation cycle was **exhausted** before it ran. The
empty remediation columns are a fact about what Stage did — nothing — not a
placeholder awaiting a later fill.

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
