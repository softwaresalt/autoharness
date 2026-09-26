---
title: "Plan review attempt 08 (terminal) — Single governing plan contract"
description: "Immutable per-attempt plan-review artifact recording the independent attempt-08 review of docs/plans/2026-09-17-single-governing-plan-contract-plan.md at revision 7, against reviewed content HEAD f142173c. Gate result FAIL; decision BLOCKED on one P0, seven P1 and one P2 deduplicated finding: Harvest is omitted from the manifest-backed consumer migration so a stale inline PASS still reaches a consumer, the closed eight-key manifest format rejects the live manifests it claims to match, pre-review manifests with null fields are incompatible with the same closed format, the writer can produce two plan_role active documents without an atomic commit, the T6a consumer graph is stale, there is no atomic review-result recorder, the token contract is stated as six in one place and eight in another, and template/mirror pairs declared atomic are harvested as separately-committable tasks. The authorized remediation cycle is exhausted: no remediation was performed, no finding is closed, and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-08.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 8
attempt_range: "08"
attempt_conformance: conforming
review_terminal: true
verdict_manifest: docs/reviews/2026-09-17-single-governing-plan-contract-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-07.md
plan_path: docs/plans/2026-09-17-single-governing-plan-contract-plan.md
plan_id: single-governing-plan-contract
reviewed_revision: 7
reviewed_content_head: f142173c
reviewed_content_state: committed
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: C9CD24F3
source_stash_id_recorded_in_backlog: C9CD24F3
source_stash_id_conflict: false
feature_id: 171-F
shipment_id: 179-S
review_cycle: 8
dispatch_mode: declared-degradation
anchor_route: absent
anchor_route_note: "No cross-model anchor was available. The cross-model rubrics ran under same-model declared degradation; this is recorded, not compensated for."
gate_result: FAIL
decision: BLOCKED
verdict_at_entry: REMEDIATED-PENDING-REVIEW
verdict_at_entry_plan_revision: 7
remediation_authorization: none-exhausted
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 1
p1_open: 7
p2_open: 1
severity_basis: "Severities are the dispatch-recorded severities. The Harvest consumer-migration omission was dispatched with an explicit P0 label; the remaining substantive findings dispatched for this plan are recorded P1. Findings dispatched on the portfolio P2 list are recorded P2 against the plan surface they land on."
persona_coverage:
  - persona: constitution
    status: complete
  - persona: python
    status: complete
  - persona: scope-boundary
    status: complete
    findings: none
  - persona: learnings
    status: degraded
    note: "Not-ready/degraded: could not inspect the diff. Relevant prior lessons were retrieved and applied."
  - persona: architecture
    status: complete
  - persona: agent-native-parity
    status: complete
  - persona: security-lens
    status: complete
tags:
  - "plan-review"
  - "terminal-review"
  - "review-convergence"
  - "artifact-lifecycle"
  - "manifest-contract"
---

# Plan review attempt 08 (terminal) — Single governing plan contract

This artifact records **one thing**: the independent reviewer's verdict on plan
revision 7 as it stands at content HEAD `f142173c`. It has no Part 2. The
authorized remediation budget is **exhausted**, so no remediation followed this
review, no finding below is closed, and Stage asserts no `PASS`.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-17-single-governing-plan-contract-plan.md` |
| Reviewed revision | 7 |
| Reviewed content HEAD | `f142173c` (committed) |
| Verdict at entry | `REMEDIATED-PENDING-REVIEW` at plan revision 7 |
| Covering feature / shipment | `171-F` / `179-S` |
| Source stash | `C9CD24F3` (plan and backlog agree) |
| Dispatch mode | `declared-degradation` |
| Gate result | **FAIL** |
| Decision | **BLOCKED** |

## Dispatch and coverage

All **seven** required personas ran: Constitution, Python, Scope Boundary,
Learnings, Architecture, Agent-Native Parity, Security Lens.

* **Anchor route absent.** No cross-model anchor was reachable; the cross-model
  rubrics executed under *same-model declared degradation*.
* **Learnings degraded / not-ready.** Could not inspect the diff; prior lessons
  were retrieved and applied, diff-grounded checks did not run.
* **Scope Boundary returned no finding for this plan.** Its `source_stash_id`
  and the executable records both name `C9CD24F3`, which exists.

## P0 findings (1)

**A1 — Harvest is omitted from the manifest-backed consumer migration.**
The plan migrates review-verdict consumers onto the structured manifest but
**does not migrate Harvest**. Harvest is the step that turns a reviewed plan into
executable backlog records, so it is precisely the consumer whose misreading has
executable consequence. Left unmigrated, Harvest continues to read an **inline
`PASS` marker** in plan or review narrative, which means a stale or superseded
inline `PASS` still admits a plan to decomposition and the manifest gate is
**bypassed at the only point where bypassing it creates work**. The contract's
central claim — that the manifest is the single authority for latest attempt and
verdict — is false as long as this consumer is exempt.

## P1 findings (7, deduplicated)

**B1 — the closed eight-key format rejects the live manifests.**
The manifest wire format is specified as a **closed** set of eight contract
keys. The live verdict manifests in `docs/reviews/` carry additional keys that
the plan itself relies on — `gate_result`, `p0_open`/`p1_open`/`p2_open`,
`latest_remediation_revision`, `latest_disposition`, `review_terminal`,
`awaiting_attempt`, and the roster-entry extras `legacy_coverage`, `parts`,
`terminal`. A closed format validating the records it was derived from would
reject **every one of them**. The plan claims the format `deliberately matches
the key names the verdict manifests already carry`; closed-ness contradicts that
claim.

**B2 — pre-review initial manifests carry null fields the closed format cannot
accept.**
A manifest created **before** the first attempt has no `latest_attempt`, no
`latest_artifact`, and an empty `attempts[]`. Under a closed, fully-required
eight-key format those are schema violations, so the contract makes it
impossible to create a conformant manifest for a plan that has not yet been
reviewed — and the plan provides no initial/`null`-tolerant state.

**B3 — the writer can create two `plan_role: active` documents.**
`link_supersession()` performs several writes — set the prior revision's
`plan_role`/`superseded_by`, set the new revision's `supersedes`, append to
`source_history`, update the manifest — with **no atomic commit**. An
interruption between the new document becoming `active` and the prior document
becoming `superseded` leaves **two actives for one `plan_id`**, which the plan
declares a fail-closed authoring error. The invariant is asserted but its writer
can violate it.

**B4 — the `T6a` consumer graph is stale.**
The consumer inventory in `T6a` does not match the consumers that exist at this
revision; at minimum it omits Harvest (see A1). A migration driven by a stale
graph silently exempts whatever the graph forgot.

**B5 — there is no atomic review-result recorder.**
Recording a review result touches the immutable artifact, the manifest roster,
the manifest's top-level selection fields, and the plan's `source_history`. No
single operation makes that set atomic, so a partial write yields a manifest that
points at an artifact that does not exist, or an artifact with no roster entry —
both of which are `REVIEW_VERDICT_AMBIGUOUS` states the plan does not define a
recovery for.

**B6 — the token contract is six in one place and eight in another.**
The error/outcome token set is stated with **two different cardinalities** in the
same document. Only one can be the contract; a consumer implementing the other
is conformant with the text and wrong in practice.

**B7 — template/mirror pairs declared atomic are split across commits.**
Pairs the plan declares `one atomic change set` — a template and its installed
mirror — are harvested as **separate tasks**, and separate tasks are separately
committable. The atomicity is asserted in prose and defeated by the
decomposition, so a drifted mirror is reachable between two green commits. This
is recorded here because this plan owns the atomicity contract; the same shape
recurs on `177-S` (`T1`/`T2`) and is **not** double-counted there.

## P2 findings (1)

**C1 — the verdict manifest's `description` asserts a falsehood.**
The mutable verdict manifest's `description` claims `No PASS exists anywhere in
this record` while its own roster carries `verdict: PASS` at attempts 2 and 3.
The truthful statement is narrower: no `PASS` exists at or after attempt 4, and
none exists against the governing revision. Recorded against the manifest
wording **as observed at `f142173c`**; one defect class, six instances across the
portfolio, counted once per manifest surface. It is a live instance of the exact
misreading this plan exists to prevent.

## Disposition

**No remediation.** The authorized remediation budget is exhausted.
`remediation_revision` is `null`, `disposition` is `null`, and the governing
revision remains 7 — the revision that was reviewed and found BLOCKED.

This plan is **not harvest-ready and not Ship-ready**. No backlog executable
record, source file, test or configuration was changed on the strength of this
review.
