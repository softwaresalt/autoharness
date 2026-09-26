---
title: "Plan review verdict manifest — Single governing plan contract"
description: "Mutable verdict manifest for docs/plans/2026-09-17-single-governing-plan-contract-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. The reviews live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 08, terminal. Plan revision: 7. Independent attempt 08 reviewed revision 7 at content HEAD f142173c and returned gate result FAIL and verdict BLOCKED on one P0, seven P1 and one P2 deduplicated finding. The authorized remediation budget is exhausted: no remediation followed attempt 08, no finding is closed, latest_remediation_revision and latest_disposition are null, and the plan is neither harvest-ready nor Ship-ready. PASS appears in this record only at attempts 2 and 3, against superseded revisions 2 and 3; no PASS exists at or after attempt 4, and none exists against the governing revision 7."
doc_type: review-manifest
source: docs/reviews/2026-09-17-single-governing-plan-contract-plan-review.md
date: 2026-09-18
plan_id: single-governing-plan-contract
plan_path: docs/plans/2026-09-17-single-governing-plan-contract-plan.md
plan_revision: 7
latest_attempt: 8
review_terminal: true
governed_plan_role: superseded
successor_manifest: docs/reviews/2026-09-18-review-authority-foundation-plan-review.md
supersession_note: "The plan this manifest governs was superseded at architecture level on 2026-09-18. This manifest remains the authoritative record of attempts 1-8 against that plan and is not re-opened; the successor plan is governed by the manifest named in successor_manifest, which is in the pre-review state."
awaiting_attempt: null
reviewed_content_head: f142173c
gate_result: FAIL
verdict: BLOCKED
p0_open: 1
p1_open: 7
p2_open: 1
remediation_authorization: none-exhausted
latest_remediation_revision: null
latest_disposition: null
latest_artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-08.md
attempts:
  - attempt: 2
    form: combined-document
    legacy_coverage:
      covers_attempts: [1, 2]
      original_attempt_label: "01-02"
      note: "One document authored for two cycles; preserved verbatim, never retroactively split."
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
    remediation_revision: 7
    disposition: REMEDIATED-PENDING-REVIEW
    remediation_parent_head: 689c48a0
    remediation_content_state: committed
    remediation_content_head: f142173c
    terminal: false
  - attempt: 8
    artifact: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-08.md
    reviewed_revision: 7
    reviewed_content_head: f142173c
    verdict: BLOCKED
    p0_open: 1
    p1_open: 7
    p2_open: 1
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
| `plan_revision` | 7 |
| `latest_attempt` | **08** (terminal; no further attempt authorized) |
| `latest_artifact` | `docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-08.md` |
| `reviewed_content_head` | `f142173c` |
| `gate_result` (attempt 08, immutable) | **FAIL** |
| `verdict` | **BLOCKED** (derived) |
| `p0_open` | **1** |
| `p1_open` | **7** |
| `p2_open` | **1** |

**The top-level `verdict` is derived, not authored.** Take the
highest-numbered roster entry — attempt 08. Its `remediation_revision` is
`null`, so no Stage-produced revision supersedes the content the reviewer
judged, and the top-level `verdict` is that entry's reviewer `verdict`:
**BLOCKED**.

`REMEDIATED-PENDING-REVIEW` is not available here and is not used: it is a
`disposition`, never a `verdict`, and it asserts that Stage produced a revision
in response — which did not happen, because the authorized remediation budget is
exhausted.

**On `PASS` in this record.** `PASS` appears at attempts 2 and 3, against
superseded plan revisions 2 and 3. No `PASS` exists at or after attempt 4, and
**no `PASS` exists against the governing revision 7**. Attempt 08 recorded the
earlier, broader claim — that no `PASS` existed *anywhere* in this record — as a
P2 finding against this manifest's wording as it stood at `f142173c`. The
statement above is the precise one; the wording it replaces was false.

## What attempt 08 records

Independent terminal review opened against plan revision 7 at content HEAD `f142173c`; gate result FAIL, decision BLOCKED, one P0, seven P1 and one P2 open. Persona coverage was complete (Constitution, Python, Scope Boundary, Learnings, Architecture, Agent-Native Parity, Security Lens); the anchor route was absent so the cross-model rubrics ran under same-model declared degradation, the Learnings persona was degraded because it could not inspect the diff, and Scope Boundary returned no finding for this plan because its `source_stash_id` `C9CD24F3` matches its executable records and exists. The P0 is that Harvest is omitted from the manifest-backed consumer migration, so the one consumer whose misreading has executable consequence still reads an inline `PASS` marker and a stale or superseded inline `PASS` still admits a plan to decomposition. The seven P1s are: the closed eight-key manifest format would reject every live verdict manifest, because the live records carry `gate_result`, the open-count keys, `latest_remediation_revision`, `latest_disposition`, `review_terminal`, `awaiting_attempt` and the roster extras `legacy_coverage`, `parts` and `terminal`; a pre-review manifest with no `latest_attempt`, no `latest_artifact` and an empty `attempts[]` cannot be conformant under that same closed format; `link_supersession()` performs several writes with no atomic commit, so an interruption leaves two `plan_role: active` documents for one `plan_id`; the `T6a` consumer graph is stale and at minimum omits Harvest; there is no atomic review-result recorder across artifact, roster, selection fields and `source_history`; the token contract is stated with two different cardinalities, six in one place and eight in another; and template/mirror pairs declared one atomic change set are harvested as separately-committable tasks, which is recorded here because this plan owns the atomicity contract and is not double-counted on `177-S`. The single P2 is that this manifest's own `description` asserted that no `PASS` existed anywhere in the record while the roster carries `PASS` at attempts 2 and 3 - a live instance of the exact misreading this plan exists to prevent.

## What follows attempt 08

**Nothing.** The authorized remediation budget is exhausted. No remediation
followed attempt 08, `latest_remediation_revision` is `null`,
`latest_disposition` is `null`, and the governing revision remains **7** — the
revision that was reviewed and found BLOCKED.

The findings are open. Closing them requires a new operator authorization, a new
Stage remediation cycle producing revision 8, and an independent attempt 09.
None of those has happened, and this manifest asserts none of them.

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
| 7 | `...-plan-review-attempt-07.md` | 6 @ `22bca5c8` | **BLOCKED** (5 P1 open) | 7 | REMEDIATED-PENDING-REVIEW |
| **8** | `...-plan-review-attempt-08.md` | 7 @ `f142173c` | **BLOCKED** (1 P0, 7 P1, 1 P2 open) | — | — |

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
`terminal` flag is `false`.** When attempt 07 was written, the authorized
remediation budget was exhausted and the columns were correctly empty. The
operator then authorized one further bounded cycle, Stage produced revision 7,
and the columns record that fact. The reviewer's own `verdict: BLOCKED` in that
same row is untouched — the remediation columns describe Stage's response, not
the reviewer's judgement, which is exactly why they are separate columns. That
remediation was uncommitted working-tree content at parent `689c48a0` when the
row was first written; it is now **committed at `f142173c`**, and the row's
`remediation_content_state` / `remediation_content_head` record the current
truth. The reviewer columns are unchanged.

**Attempt 8 carries empty remediation columns, and its `terminal` flag is
`true`.** The budget is exhausted again and was not re-authorized, so no Stage
revision followed. Empty columns here are the accurate record, not a gap waiting
to be filled.

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
