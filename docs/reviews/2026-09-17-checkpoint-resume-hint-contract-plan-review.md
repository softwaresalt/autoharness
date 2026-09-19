---
title: "Plan review verdict manifest — Checkpoint resume_hint contract"
description: "Mutable verdict manifest for docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. The reviews live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 07, remediated and awaiting attempt 08. Plan revision: 7. Attempt-07 reviewer gate result FAIL and reviewer verdict BLOCKED against content HEAD 22bca5c8 are immutable facts and are recorded unchanged. The derived top-level verdict is REMEDIATED-PENDING-REVIEW because the operator authorized one additional remediation cycle after attempt 07 and Stage produced plan revision 7 in response. No PASS exists anywhere in this record. Seven P1 findings and one P2 follow-up are open. The remediation is unverified: it awaits independent attempt 08."
doc_type: review-manifest
source: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
date: 2026-09-18
plan_id: checkpoint-resume-hint-contract
plan_path: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
plan_revision: 7
latest_attempt: 7
review_terminal: false
awaiting_attempt: 8
reviewed_content_head: 22bca5c8
gate_result: FAIL
verdict: REMEDIATED-PENDING-REVIEW
p0_open: 0
p1_open: 7
p2_open: 1
remediation_authorization: operator-authorized
latest_remediation_revision: 7
latest_disposition: REMEDIATED-PENDING-REVIEW
latest_artifact: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-07.md
attempts:
  - attempt: 2
    form: combined-document
    legacy_coverage:
      covers_attempts: [1, 2]
      original_attempt_label: "01-02"
      note: "One document authored for two cycles; preserved verbatim, never retroactively split."
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
  - attempt: 7
    artifact: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-07.md
    reviewed_revision: 6
    reviewed_content_head: 22bca5c8
    verdict: BLOCKED
    p1_open: 7
    p2_open: 1
    remediation_revision: 7
    disposition: REMEDIATED-PENDING-REVIEW
    remediation_parent_head: 689c48a0
    remediation_content_state: uncommitted-working-tree
    terminal: false
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
| `plan_revision` | 7 |
| `latest_attempt` | **07** (remediated, awaiting attempt **08**) |
| `latest_artifact` | `docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-07.md` |
| `reviewed_content_head` | `22bca5c8` |
| `gate_result` (attempt 07, immutable) | **FAIL** |
| `verdict` | **REMEDIATED-PENDING-REVIEW** (derived) |
| `p1_open` | **7** (all addressed in revision 7; unverified until attempt 08) |
| `p2_open` | 1 |

**The top-level `verdict` is derived, not authored.** Take the
highest-numbered roster entry — attempt 07. Its `remediation_revision` is
**7**, so a Stage-produced revision supersedes the content the reviewer judged,
and the top-level `verdict` is that entry's `disposition`:
`REMEDIATED-PENDING-REVIEW`.

That derivation does **not** overwrite what the reviewer said. The attempt-07
entry still carries `verdict: BLOCKED` and the manifest still carries
`gate_result: FAIL` — those are immutable facts about content HEAD
`22bca5c8` and they are never rewritten. `REMEDIATED-PENDING-REVIEW` is a
`disposition`, never a `verdict` value, and it asserts only that Stage
produced a revision in response. It asserts **nothing** about whether that
revision is adequate. No `PASS` exists anywhere in this record, and none may
be entered except by an independent attempt 08.

## What attempt 07 records

Terminal independent review opened against plan revision 6 at content HEAD `22bca5c8`; gate result FAIL, decision BLOCKED, seven P1 findings open plus one P2 follow-up. Persona coverage was complete (Constitution, Python, Scope Boundary, Learnings, Architecture, Agent-Native Parity, Security Lens); the anchor route was absent so the cross-model rubric ran under same-model declared degradation, the Learnings persona was degraded because it could not inspect the diff, and Scope Boundary returned no P0/P1. The seven open P1s are: the activation order prohibits the raw path in the instruction before the guarded adapter and all producer wiring exist, creating an intermediate state with no lawful producer; the guarded create is CLI-only while the agent/MCP registry still advertises raw backlogit_create_checkpoint, and the inventory omits the installed and template registries and the agent declarations; the Stage/Ship startup scan cannot call a Python predicate from Markdown and needs one atomic executable historical-scan command or tool with CLI/agent parity; classification omits abandoned status and malformed or future-schema records, so it is not total; --state-dump is an ambiguous path-or-JSON surface lacking workspace containment, link/reparse/device rejection, bounds and a no-shell argv requirement, while a public --origin permits a compatibility downgrade; a text scan for raw operation names cannot distinguish prohibitive documentation from a producer bypass; and the adapter RED tests and their ordering do not pin the exact safe activation boundary. The P2 follow-up is installed-registry semantic-link parity.

## What followed attempt 07

The operator explicitly authorized **one additional bounded remediation cycle**
after attempt 07 returned terminal. Stage produced **plan revision 7** in
response, at parent HEAD `689c48a0` with the remediation carried as uncommitted
working-tree content. Every P1 the attempt-07 reviewer raised against this plan
is addressed in that revision; the plan was rewritten as a coherent
current-state contract rather than extended with a correction log.

This is a **disposition, not a verdict**. Nothing here asserts the remediation
is adequate, complete, or correct. That judgement belongs to an independent
**attempt 08**, which has not run. Until it does, the reviewer-raised findings
are recorded as open.

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
| 2 (legacy `01-02`) | `...-plan-review-attempts-01-02-combined.md` | 2 | PASS | — | — |
| 3 | `...-plan-review-attempt-03.md` | 3 | PASS | — | — |
| 4 | `...-plan-review-attempt-04.md` | 3 | BLOCKED | 4 | REMEDIATED-PENDING-REVIEW |
| 5 | `...-plan-review-attempt-05.md` | 4 | BLOCKED | 5 | REMEDIATED-PENDING-REVIEW |
| 6 | `...-plan-review-attempt-06.md` | 5 | BLOCKED | 6 | REMEDIATED-PENDING-REVIEW |
| **7** | `...-plan-review-attempt-07.md` | 6 @ `22bca5c8` | **BLOCKED** (7 P1 open, 1 P2) | **7** | REMEDIATED-PENDING-REVIEW |

**`attempt` is an integer in every row.** Deterministic latest-attempt
selection is a numeric maximum, and a string such as `"01-02"` has no numeric
maximum against `3`, `4`, `5`, `6` or `7`. The roster therefore carries
integers only, and exactly **one artifact per numeric attempt**.

The first row is the legacy combined document, normalized to `attempt: 2` with
an explicit `legacy_coverage` block recording `covers_attempts: [1, 2]`, the
original `"01-02"` label, and `form: combined-document`. **Nothing is lost and
nothing is invented**: the document was authored once, for two cycles, and is
preserved verbatim rather than retroactively split — fabricating two
independently-authored records from a document never authored that way would be
a provenance forgery. `reviewed_revision` remains 2, the revision the document
itself names; the pre-remediation cycle merged into it is not separately
recoverable from the record, and is not invented here. `legacy_coverage` is an
optional **roster-entry** key, not a ninth manifest contract key.

**Attempt 7 carries a `remediation_revision` and a `disposition`, and its
`terminal` flag is now `false`.** When attempt 07 was written, the authorized
remediation budget was exhausted and the columns were correctly empty. The
operator then authorized one further bounded cycle, Stage produced revision 7,
and the columns record that fact. The reviewer's own `verdict: BLOCKED` in that
same row is untouched — the remediation columns describe Stage's response, not
the reviewer's judgement, which is exactly why they are separate columns.

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
