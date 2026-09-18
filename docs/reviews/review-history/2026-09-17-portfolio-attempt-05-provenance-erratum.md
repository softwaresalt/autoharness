---
title: "Erratum — attempt-05 provenance conflation across the seven-entry contract-defect staging portfolio"
description: "Immutable erratum artifact. The six attempt-05 review-history records of the 2026-09-17 seven-entry contract-defect staging portfolio each conflate two distinct facts into a single plan_revision field: the revision an independent reviewer actually read and blocked (revision 4), and the revision Stage subsequently produced in response (revision 5). Those six records are immutable and are NOT rewritten. This erratum states the corrected reading for each of them by exact path, and is the artifact the six mutable verdict manifests carry in carried_forward_context[] so the corrected reading travels with the record."
doc_type: review
source: docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md
date: 2026-09-19
review_artifact_role: erratum
review_artifact_immutable: true
applies_to_attempt: 5
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
tags:
  - "plan-review"
  - "erratum"
  - "provenance"
  - "verdict-manifest"
  - "portfolio-2026-09-17"
---

# Erratum — attempt-05 provenance conflation

## What this artifact is, and what it is not

This is an **erratum**, not a review and not a revision of one. It publishes the
corrected reading of six immutable records **without touching them**.

The six attempt-05 artifacts named below are immutable per-attempt review
records. They are **not rewritten, not amended in place, and not superseded**.
Rewriting an immutable review record to make its metadata tidier would destroy
the very provenance the split-surface contract exists to protect, and would be
indistinguishable from backdating. The records stand exactly as authored.

What this erratum supplies is the *reading*: which field in those records means
what, and which fact each of them silently merged.

## The defect

Each of the six attempt-05 artifacts carries a single `plan_revision` key and a
title of the form *"Plan review attempt 05 — &lt;plan&gt; (plan revision 5)"*.
A reader — human or mechanical — takes both as saying *"this is a review of
revision 5."*

It is not. In every one of the six cases the independent reviewer opened the
attempt against **revision 4** and returned **BLOCKED**. Revision 5 is the
revision **Stage produced afterwards, in response**. No reviewer read revision 5
at attempt 05, and no reviewer passed it.

Each artifact does carry the reviewer-entry facts correctly, in
`verdict_at_entry: BLOCKED` and `verdict_at_entry_plan_revision: 4`, and each
carries `decision: REMEDIATED-PENDING-REVIEW`. The defect is not that the truth
is absent; it is that the **headline fields assert something else**, and a
consumer reading `plan_revision` and the title alone reaches the wrong
conclusion — that a reviewer evaluated revision 5.

That conflation is exactly the hazard the single-governing-plan contract now
closes structurally, by splitting the manifest roster entry into
`reviewed_revision` + `verdict` (what an independent reviewer judged) and
`remediation_revision` + `disposition` (what Stage subsequently produced), and
by making `REMEDIATED-PENDING-REVIEW` illegal as a `verdict` value.

## Corrected reading, per artifact

All six rows share the same shape because all six attempts shared the same
cycle. Each row states the record **as written**, then the **corrected
reading**.

### 1. `docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-05.md`

| | Value |
|---|---|
| As recorded | `plan_revision: 5`; title "(plan revision 5)"; `decision: REMEDIATED-PENDING-REVIEW` |
| Corrected reading | Reviewed revision **4**; reviewer verdict **BLOCKED**; Stage remediation produced revision **5**; disposition **REMEDIATED-PENDING-REVIEW** |
| Already correct in the record | `verdict_at_entry: BLOCKED`, `verdict_at_entry_plan_revision: 4` |
| Plan | `docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md` (`plan_id: p004-red-phase-precondition-scoping`) |

### 2. `docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-05.md`

| | Value |
|---|---|
| As recorded | `plan_revision: 5`; title "(plan revision 5)"; `decision: REMEDIATED-PENDING-REVIEW` |
| Corrected reading | Reviewed revision **4**; reviewer verdict **BLOCKED**; Stage remediation produced revision **5**; disposition **REMEDIATED-PENDING-REVIEW** |
| Already correct in the record | `verdict_at_entry: BLOCKED`, `verdict_at_entry_plan_revision: 4` |
| Plan | `docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md` (`plan_id: workspace-authoritative-branch-resolution`) |

### 3. `docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md`

| | Value |
|---|---|
| As recorded | `plan_revision: 5`; title "(plan revision 5)"; `decision: REMEDIATED-PENDING-REVIEW` |
| Corrected reading | Reviewed revision **4**; reviewer verdict **BLOCKED**; Stage remediation produced revision **5**; disposition **REMEDIATED-PENDING-REVIEW** |
| Already correct in the record | `verdict_at_entry: BLOCKED`, `verdict_at_entry_plan_revision: 4` |
| Plan | `docs/plans/2026-09-17-single-governing-plan-contract-plan.md` (`plan_id: single-governing-plan-contract`) |

### 4. `docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-05.md`

| | Value |
|---|---|
| As recorded | `plan_revision: 5`; title "(plan revision 5)"; `decision: REMEDIATED-PENDING-REVIEW` |
| Corrected reading | Reviewed revision **4**; reviewer verdict **BLOCKED**; Stage remediation produced revision **5**; disposition **REMEDIATED-PENDING-REVIEW** |
| Already correct in the record | `verdict_at_entry: BLOCKED`, `verdict_at_entry_plan_revision: 4` |
| Plan | `docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md` (`plan_id: checkpoint-resume-hint-contract`) |

### 5. `docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempt-05.md`

| | Value |
|---|---|
| As recorded | `plan_revision: 5`; title "(plan revision 5)"; `decision: REMEDIATED-PENDING-REVIEW` |
| Corrected reading | Reviewed revision **4**; reviewer verdict **BLOCKED**; Stage remediation produced revision **5**; disposition **REMEDIATED-PENDING-REVIEW** |
| Already correct in the record | `verdict_at_entry: BLOCKED`, `verdict_at_entry_plan_revision: 4` |
| Plan | `docs/plans/2026-09-17-safe-close-record-transition-disposition-plan.md` (`plan_id: safe-close-record-transition-disposition`) |

### 6. `docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-05.md`

| | Value |
|---|---|
| As recorded | `plan_revision: 5`; title "(plan revision 5)"; `decision: REMEDIATED-PENDING-REVIEW` |
| Corrected reading | Reviewed revision **4**; reviewer verdict **BLOCKED**; Stage remediation produced revision **5**; disposition **REMEDIATED-PENDING-REVIEW** |
| Already correct in the record | `verdict_at_entry: BLOCKED`, `verdict_at_entry_plan_revision: 4` |
| Plan | `docs/plans/2026-09-17-post-claim-member-status-contract-plan.md` (`plan_id: post-claim-member-status-contract`) |

## What is NOT claimed here

* **No PASS is asserted anywhere.** At attempt 05 every one of the six plans was
  blocked at revision 4 and remediated by Stage to revision 5. Stage does not
  review its own remediation. Nothing in this erratum converts a disposition
  into a verdict.
* **No attempt-05 artifact is superseded by this file.** Supersession is an
  attempt-to-attempt relation recorded in the artifacts and the manifests. This
  erratum sits alongside them as context.
* **No attempt-05 artifact is edited.** Their bytes are unchanged. If a future
  consumer finds a discrepancy between an attempt-05 record's headline
  `plan_revision` and this erratum, **this erratum states the corrected
  reading** and the record states what was written at the time. Both facts are
  retained deliberately.

## How this erratum is reached

Each of the six mutable verdict manifests carries this file in its
`carried_forward_context[]` with the reason
`"attempt-05 records conflate reviewed revision 4 with Stage-produced revision 5"`.
Because `carried_forward_context[]` surfaces only in the **`context`** band of
the two-band `ReviewInputSet`, this erratum can never enter a later review's
`operative` band — it is provenance, never a governing input. That is the same
guarantee `REVIEW_INPUT_HISTORY_LEAK` enforces for every other history document,
and it applies here regardless of this file's name or location.

## Structural correction already applied

The normalized manifests now record attempt 05 as:

```yaml
- attempt: 5
  artifact: <the immutable attempt-05 artifact>
  reviewed_revision: 4
  verdict: BLOCKED
  remediation_revision: 5
  disposition: REMEDIATED-PENDING-REVIEW
```

which carries both facts without merging them, and which no longer records
`REMEDIATED-PENDING-REVIEW` in a `verdict` field.
