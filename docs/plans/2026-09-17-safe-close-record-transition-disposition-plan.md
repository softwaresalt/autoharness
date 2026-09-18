---
title: "SAFE_CLOSE record-transition gap: in-workspace evidence, upstream escalation, and an operator-only interim close"
description: "Implementation plan for the autoharness-owned half of the SAFE_CLOSE terminal-transition gap: re-derive the four externally-measured backlogit refusal behaviours as hermetic in-workspace fixtures to replace P-005-tainted indicative evidence, generate a portable upstream report and record the decided escalation route, document an operator-only approval-gated interim close procedure that no agent may execute, and correct every in-repository claim that split multi-shipment delivery is operationally complete while INV-11 remains blocked."
doc_type: plan
source: docs/plans/2026-09-17-safe-close-record-transition-disposition-plan.md
date: 2026-09-17
status: reviewed
revision: 2
revision_note: "Revision 2 is the canonical statement of the intended design. Review findings were remediated in place; this document states exactly one binding requirement per topic. The bounded audit trail lives in `linked_review`."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 1
source_stash_id: 7F9CB5E9
stash_ids:
  - 7F9CB5E9
deferred_scope_expansions:
  - 7F9CB5E9
predecessor_stash_id: 2B42392E
prior_learnings:
  - docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md
  - docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md
  - docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md
  - docs/compound/2026-08-01-shipment-record-status-integrity.md
linked_review: docs/reviews/2026-09-17-safe-close-record-transition-disposition-plan-review.md
covering_feature: 173-F
shipment: 181-S
requires_plan_hardening: "yes"
plan_hardening_status: complete
source_refs:
  originating_prs: [450, 451]
  originating_review_thread: "N/A (threadless — discovered during Ship post-merge closure)"
  originating_feature_id: 166-F
  originating_shipment_id: 174-S
  originating_task_id: 166.005-T
tags:
  - "shipment-closure"
  - "upstream-dependency"
  - "evidence-provenance"
  - "p-005"
  - "documentation-truth"
---

# SAFE_CLOSE record-transition gap — autoharness disposition

## Why this entry is retained

The operator imported this entry specifically to make operational
multi-shipment delivery resolvable, and explicitly directed that it not be
discarded merely because part of the fix is upstream. Decision **D7** upholds
that: the remedy is external, but three autoharness-owned obligations are real
and are delivered here.

This plan does **not** claim to fix the gap. It makes the gap honestly
evidenced, properly escalated, safely worked around by an operator, and
truthfully documented.

## Ownership boundary

**External (backlogit, Go binary, third-party dependency).** The capability to
transition a shipment record to `status: archived` + `archived_status: shipped`
**without** invoking the cascading `ShipShipment` operation. This cannot be
implemented in this repository (P-021 C1).

**Already delivered, not re-delivered here.** The fail-closed halt
`RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` with its explicit no-substitution
prohibition, shipped by `166.005-T`.

**Autoharness-owned and delivered by this plan.** Evidence re-derivation,
escalation route and portable report, operator-only interim procedure, and
documentation truth.

## Problem

backlogit `1.10.1-0.20260823032255-b07729386a31+dirty` offers no safe mechanism
to reach `archived_status: shipped` without the cascade. Four behaviours were
measured:

1. `backlogit move <S> --status shipped` → refused, exit 9, "shipment must be
   shipped via ShipShipment, not a direct status update".
2. `backlogit update <S> --status shipped` → refused identically, exit 9.
3. `backlogit archive <S>` on an active shipment → stamps
   `archived_status: active`, failing the shipment-reconcile Step 8 provenance
   gate (`RECONCILE_FAIL_SHIPMENT_RECORD_PROVENANCE`).
4. `backlogit shipment ship <S>` → the only mechanism producing
   `archived_status: shipped`, and it has no `--no-cascade` flag.

Substituting the cascade on a non-cascade-eligible manifest is **prohibited**:
the engine returns live out-of-manifest siblings and silently clears their
`parent_id` (tracked separately as `63363CF5`, untouched and outside scope).

**Blocking relationship.** This blocks `INV-11` of
`docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md` —
operational multi-shipment feature delivery. `INV-4`/`INV-5` make split
delivery *contract-complete* (an ordered sequence `S1..Sn`, feature item last in
`Sn`), but every intermediate shipment `S1..Sn-1` carries no feature member,
therefore can never qualify for CASCADE, therefore is a genuine SAFE_CLOSE
shipment, therefore hits this exact refusal.

## Evidence provenance defect (P-005) — the first deliverable

The four measurements originate from Stage spike arms run in **external
`%TEMP%` workspaces**, which is a P-005 containment and destructive-approval
violation. That evidence is therefore **indicative, not authoritative**, and no
remedy may be accepted on it.

Re-derivation is hermetic and in-workspace: checked-in fixtures under `tests/`
that exercise each refusal against the pinned backlogit binary, with the
observed version recorded in the fixture so a version change is a test signal
rather than a silent drift. No external workspace is created. No shipment
record in this repository is mutated by any fixture.

This plan's own spike discipline is the corrected pattern: the companion spike
for `3EF5AAF2` was run read-only and in-workspace for exactly this reason.

## Design

### Part A — hermetic evidence (blocks everything else)

Four fixtures, one per measured behaviour, each asserting the exact exit code
and the exact refusal message, each recording the observed backlogit version.
The fixtures operate on disposable in-`tests/` records, never on live workspace
shipments.

### Part B — escalation route and portable report

Decided route (**D7**): **file an upstream issue/PR against
`softwaresalt/backlogit`** requesting a genuine non-cascading transition to
`archived_status: shipped` — for example `shipment ship --no-cascade`, or a
permitted direct terminal status update guarded by manifest-scope verification.

Rejected and recorded: vendoring a wrapper (would reimplement archive semantics
the engine owns) and pin-and-patch (forks a binary dependency this workspace
already consumes at a moving version).

The portable report is generated **from the Part A fixtures**, so what is filed
upstream is hermetic evidence rather than the tainted measurements. The same
escalation channel is reused where it overlaps `63363CF5`; `63363CF5` itself
remains untouched.

**Filing the upstream issue is an operator action.** This plan produces the
report; it does not authorize an agent to open it.

### Part C — operator-only interim procedure

Document an approval-gated administrative-close procedure, modelled on the
explicitly authorized, Ship-verified operator close of `173-S` on 2026-09-16.

Binding constraints:

* It is **operator-only**. No agent may execute it, propose executing it, or
  treat its existence as authorization.
* It does **not** weaken `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`. The halt
  still fires; the procedure is what an operator may do *after* the halt, with
  explicit approval.
* It requires manifest-scope verification before any record mutation, and it
  records the verification as closure evidence.
* Every invocation is logged as a P-005 telemetry event, because an
  administrative close is a deviation from the normal path even when authorized.

### Part D — documentation truth

Audit every in-repository statement about split multi-shipment delivery and
correct any that describes it as operationally complete or end-to-end supported
while `INV-11` is blocked. Add a durable pointer from the `INV-11` text to this
entry so the blocked status is discoverable from the invariant itself.

## Work Breakdown

| # | Task | Scope |
|---|---|---|
| T1 | Hermetic fixture: `move --status shipped` refusal, exit 9, exact message, version recorded | `tests/` |
| T2 | Hermetic fixture: `update --status shipped` refusal, exit 9, exact message | `tests/` |
| T3 | Hermetic fixture: `archive` on active stamps `archived_status: active` and fails the Step 8 provenance gate | `tests/` |
| T4 | Hermetic fixture: `shipment ship` is the sole `archived_status: shipped` producer and exposes no `--no-cascade` | `tests/` |
| T5 | Generate the portable upstream report from T1–T4 and record the decided escalation route | `docs/` |
| T6 | Document the operator-only approval-gated interim close procedure with its four binding constraints | `docs/` |
| T7 | Documentation-truth audit and `INV-11` back-pointer | `docs/` |

T5, T6, and T7 each declare `blocks` dependencies on T1–T4: nothing may be
filed, documented, or corrected on indicative evidence.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* All four fixtures pass against the pinned backlogit binary and record its
  version.
* No live shipment record in `.backlogit/` is mutated by any fixture.
* No external `%TEMP%` workspace is created at any point.
* `autoharness gate check` passes on every modified file.
* A repository-wide search finds no remaining claim that split delivery is
  operationally complete.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | The interim procedure is read as an agent-executable path | Operator-only is stated in the procedure title, its first paragraph, and its telemetry requirement; T6's acceptance criteria include a negative assertion that no agent template references it as executable |
| R2 | Fixtures mutate live workspace records | Fixtures operate on disposable in-`tests/` records only; the Verification section asserts `.backlogit/` is unmodified |
| R3 | Upstream never lands and the entry stays open indefinitely | This plan's deliverables are complete without the upstream fix; the entry remains open against the external prerequisite, which is the honest state |
| R4 | Re-derivation is attempted in `%TEMP%` again for speed | Explicitly prohibited in Verification and Out of scope; this is the exact P-005 violation being corrected |
| R5 | The cascade is substituted on a non-eligible manifest to "just close it" | Already prohibited by `166.005-T`'s no-substitution clause, which this plan does not weaken |

## Out of scope

* Implementing the record transition. It is external.
* Any change to `166.005-T`'s halt or its no-substitution prohibition.
* Stash `63363CF5` (sibling `parent_id` clearing) — shares the escalation
  channel only; the entry itself is untouched.
* Archived predecessor `2B42392E`, whose append-only record is **not**
  rewritten; traceability runs forward from `7F9CB5E9` to it.
* `3CA122AC` (classifier/protected-set class) — confirmed distinct, active,
  unmerged, untouched.
* Any agent-executable administrative close.
