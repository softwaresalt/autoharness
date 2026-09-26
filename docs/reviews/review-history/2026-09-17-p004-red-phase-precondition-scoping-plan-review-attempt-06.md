---
title: "Plan review attempt 06 — P-004 red-phase precondition scoping"
description: "Immutable per-attempt plan-review artifact. Part 1 records the independent review opened against docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md at revision 5 — verdict BLOCKED on four coupled defects: a bootstrap task that substituted a future declared-set criterion for the installed P-004 precondition and itself had no policy-compliant claim path, residual positional-correspondence language in the unittest loader contract, an unspecified addSubTest failure path in P004Result, and an unassigned mapping from Draft-07 shape failures to the required marker tokens. Part 2 records, separately, the operator-authorized remediation that raised the plan to revision 6. Disposition REMEDIATED-PENDING-REVIEW. Stage does not review its own remediation and asserts no PASS."
doc_type: review
source: docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-06.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 6
attempt_range: "06"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-p004-red-phase-precondition-scoping-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-05.md
plan_path: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
plan_id: p004-red-phase-precondition-scoping
reviewed_revision: 5
remediation_revision: 6
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 76EBDE6D
feature_id: 168-F
shipment_id: 176-S
review_cycle: 6
dispatch_mode: declared-degradation
decision: REMEDIATED-PENDING-REVIEW
verdict_at_entry: BLOCKED
verdict_at_entry_plan_revision: 5
remediation_authorization: operator-authorized-final-extra-cycle
p0_open: 0
p1_open: 0
tags:
  - "plan-review"
  - "p004"
  - "red-phase"
  - "unittest-loader"
  - "json-schema-draft-07"
  - "bootstrap"
---

# Plan review attempt 06 — P-004 red-phase precondition scoping

Two strictly separated halves. **Part 1** records the independent reviewer's
verdict at plan revision 5, as received. **Part 2** records the remediation that
followed, which was **operator-authorized, not reviewer-approved**. Conflating
the two would manufacture a PASS no reviewer gave — the precise defect the
portfolio erratum
`docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md`
documents for the attempt-05 records.

---

## Part 1 — Review verdict at plan revision 5

Opened against **plan revision 5**; verdict **BLOCKED**. Operative input set:
plan revision 5 and the live `168-F` / `176-S` records at entry. Attempts 01–02,
03, 04 and 05 are superseded history and were excluded from the operative set.

dispatch_mode: `declared-degradation`
decision: `BLOCKED`

### P1 findings

**A1 — the bootstrap task was unauthorized and itself unclaimable.**
Revision 5 introduced `168.009-T` as a bootstrap task to escape the P-004
red-phase deadlock. As written it substituted a *future* declared-set criterion
for the *installed* P-004 precondition, before the policy, schema and runner it
depended on existed — and it supplied no policy-compliant claim path for
itself, so it reproduced the deadlock one level up. A force grant or a
self-authorized policy bypass is not an available remedy, and operator approval
does not change an installed precondition.

**A2 — positional-correspondence language survived the loader correction.**
Operative surfaces still implied that `loadTestsFromNames` yields results in
positional correspondence with the declared IDs. They must instead specify
independent `loadTestsFromName` per declared ID, recursive suite flattening,
`loader.errors` sampled before and after each association, and test-object
identity as the association key.

**A3 — `P004Result` had no defined `addSubTest` failure path.**
The result object specified no handling for `addSubTest` failures and errors,
no per-test detail formatting, and no tests over that path.

**A4 — token mapping was unassigned at any concrete boundary.**
The mapping of Draft-07 / `jsonschema` shape failures onto the required
`P004_MARKER_MISPLACED` and `P004_EMPTY_RED_SET` tokens was not assigned to a
concrete Python validation boundary and was untested. Draft-07 enforces item
shape only; duplicate-ID detection and red/green overlap are Python's.

**Portfolio-wide finding 7 (relayed from the single-governing-plan contract).**
This plan did not carry the mandated seven-field plan identity wire format
(`plan_id`, `plan_role`, `revision`, path-valued `supersedes`, path-valued
`superseded_by`, `source_history`, `review_manifest`).

---

## Part 2 — Operator-authorized remediation to plan revision 6

**Authorization:** `operator-authorized-final-extra-cycle`. This is Stage work,
not reviewer work. No finding below was verified closed by an independent
reviewer.

* **A1 closed by removal, not by a grant.** The existing Ship lifecycle already
  supplies the ordering the bootstrap task was invented to create: shipment
  claim precedes harness generation, and harness-architect authors the failing
  tests and assigns `harness-ready` before any implementation task is claimed.
  With that grounding stated, a separate bootstrap task is structurally
  unnecessary. `168.009-T` was **removed and archived**; the plan, `168-F`,
  `176-S`, the dependency edges and every task count were rewritten to the
  eight-task shape. No force grant, no policy bypass, and no claim that operator
  approval alters the installed P-004 precondition.
* **A2 closed.** Plan, `168-F`, `176-S` and every `168.00N-T` body now specify
  independent `loadTestsFromName` per declared ID, recursive suite flattening,
  `loader.errors` before/after association, and test-object identity. All
  positional-correspondence language was rewritten out rather than annotated.
* **A3 closed.** `P004Result` now specifies `addSubTest` failure and error
  handling with per-test detail formatting, and carries tests over it.
* **A4 closed.** The Draft-07 → token mapping is assigned to a named Python
  validation boundary and tested there; the schema retains per-item shape only,
  with duplicate-ID and red/green-overlap detection explicitly Python-owned.
* **Finding 7 closed.** The plan carries the seven identity fields;
  `plan_role` replaces any use of `status` as a plan-role substitute, and
  `plan_revision_reviewed` does not appear as a field anywhere.

### Disposition

`REMEDIATED-PENDING-REVIEW` at plan revision 6. **No PASS is asserted.** The
next reviewer pass is **attempt 07**, which must be independent and is the
terminal review for this plan.
