---
title: "Plan review attempt 07 (terminal) — P-004 red-phase precondition scoping"
description: "Immutable per-attempt plan-review artifact recording the terminal independent review of docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md at revision 6, against reviewed content HEAD 22bca5c8. Gate result FAIL; decision BLOCKED on seven deduplicated P1 findings covering lawful root bootstrap, RED-phase semantics and ordering, harness-set storage ownership, loader identity verification, expectedFailure/unexpectedSuccess token totality, the harness-architect invocation parity boundary, and the untruthful per-token subject model. The authorized extra remediation cycle is exhausted: no remediation was performed, no finding is closed, and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-07.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 7
attempt_range: "07"
attempt_conformance: conforming
review_terminal: true
verdict_manifest: docs/reviews/2026-09-17-p004-red-phase-precondition-scoping-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-06.md
plan_path: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
plan_id: p004-red-phase-precondition-scoping
reviewed_revision: 6
reviewed_content_head: 22bca5c8
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 76EBDE6D
feature_id: 168-F
shipment_id: 176-S
review_cycle: 7
dispatch_mode: declared-degradation
anchor_route: absent
anchor_route_note: "No cross-model anchor was available. The cross-model rubric ran under same-model declared degradation; this is recorded, not compensated for."
gate_result: FAIL
decision: BLOCKED
verdict_at_entry: BLOCKED
verdict_at_entry_plan_revision: 6
remediation_authorization: none-exhausted
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 0
p1_open: 7
p2_open: 0
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
  - "p004"
  - "red-phase"
  - "unittest-loader"
  - "bootstrap"
---

# Plan review attempt 07 (terminal) — P-004 red-phase precondition scoping

This artifact records **one thing**: the independent reviewer's verdict on plan
revision 6 as it stands at content HEAD `22bca5c8`. It has no Part 2. The
operator-authorized extra remediation cycle is **exhausted**, so no remediation
followed this review, no finding below is closed, and Stage asserts no `PASS`.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md` |
| Reviewed revision | 6 |
| Reviewed content HEAD | `22bca5c8` |
| Covering feature / shipment | `168-F` / `176-S` |
| Dispatch mode | `declared-degradation` |
| Gate result | **FAIL** |
| Decision | **BLOCKED** |

## Dispatch and coverage

Multi-agent persona coverage is **complete**: Constitution, Python, Scope
Boundary, Learnings, Architecture, Agent-Native Parity, and Security Lens all
ran. Two coverage facts are recorded rather than smoothed over:

* **Anchor route absent.** No cross-model anchor was reachable, so the
  cross-model rubric executed under *same-model declared degradation*. The
  verdict is not weakened by this, but the record must not imply a cross-model
  anchor existed.
* **Learnings degraded / not-ready.** The Learnings persona could not inspect
  the diff. It did retrieve relevant prior lessons, which are reflected in the
  findings, but its diff-grounded checks did not run.
* **Scope Boundary returned no P0/P1.** The plan does not exceed its declared
  boundary. The BLOCKED verdict comes entirely from the other required personas.

## P1 findings (7, deduplicated)

**A1 — the root shipment still cannot bootstrap lawfully.**
The package's reachability argument depends on an **out-of-DAG operator policy
edit**. As installed, P-004 halts before `harness-ready` is assignable, and the
repair tasks that would lift the halt cannot themselves be claimed. Removing the
bootstrap task did not remove the deadlock; it moved the unlawful step outside
the plan's own dependency graph, where no task owns it and no gate observes it.

**A2 — RED-phase semantics and sequencing are both wrong.**
Two coupled defects. First, the RED tests **describe import/load failure as a
valid red outcome**, while the P-004 contract this plan defines would classify
those same runs as *missing observations*. The two readings cannot both hold.
Second, RED tasks are, in several places, **sequenced after** the schema and
policy implementation they are supposed to fail against, which is not a RED
phase.

**A3 — the declared harness set has no owner.**
The declared harness set is assigned to the **singleton installation
harness-manifest** with no shipment-scoped storage, no lifecycle (creation,
supersession, retirement), and no named reader. Two concurrent shipments cannot
both declare a harness set under that shape, and nothing specifies who reads it
or when it is invalidated.

**A4 — loader identity must be verified, not inferred.**
The contract must **enforce that the loaded `TestCase.id()` equals the requested
`test_id`**, independently of object-identity attribution. Object identity
answers "which object came back"; it does not answer "is this the test that was
declared". A rename, a relocation, or a loader alias silently satisfies the
identity-based association while violating the declaration.

**A5 — `expectedFailure` / `unexpectedSuccess` combinations lack fail-closed tokens.**
The outcome model does not assign deterministic tokens to the
`expectedFailure` / `unexpectedSuccess` combinations. Any outcome combination
without an assigned token is an unspecified path, and an unspecified path in a
gate defaults open.

**A6 — the harness-architect invocation bypasses the gate.**
`harness-architect` (and any vanilla `unittest` invocation) **bypasses
`P004Result` and manifest validation** entirely. The plan needs **one atomic
public P004 gate/runner parity boundary** that both invocation paths must cross,
rather than a contract that binds only the path that already intended to comply.

**A7 — "every token names a `test_id`" is not a truthful invariant.**
The invariant is **impossible to satisfy** for an empty collection and for a
malformed declaration entry: in neither case does a per-test subject exist. The
plan needs a truthful subject model that distinguishes **collection-level** and
**error-level** subjects from per-test subjects, instead of asserting a
universal that its own error cases refute.

## P2 findings

None recorded for this plan.

## Disposition

**No remediation.** The extra cycle authorized after attempt 06 is exhausted, so
this artifact terminates at the verdict. `remediation_revision` is `null`,
`disposition` is `null`, and the governing revision remains 6 — the revision
that was reviewed and found BLOCKED.

This plan is **not harvest-ready and not Ship-ready**. No backlog executable
record was changed on the strength of this review.

## Date note

This artifact carries the true session date `2026-09-18`, matching the commit
clock. Earlier attempt artifacts in this series carry `date: 2026-09-19`, which
runs ahead of that clock. Those artifacts are immutable and are **not** edited
to correct it. Attempt ordering is given by `attempt`, never by `date`.
