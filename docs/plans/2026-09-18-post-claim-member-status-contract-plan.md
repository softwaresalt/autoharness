---
title: "Canonical post-claim member-status contract (P-002.7) with RED-first cross-surface evidence"
description: "Reduced current-state contract for the post-claim member-status defect. Keeps one contract — a canonical member-status vocabulary asserted identically across every declared surface — and fixes the attempt-08 finding that its evidence was GREEN-only by requiring every assertion to be observed failing before it is observed passing. Carries no dependency on the operation substrate: this unit changes declarations and their conformance tests, not execution boundaries, and is the only defect unit that is a DAG root."
doc_type: plan
source: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
date: 2026-09-18
plan_id: post-claim-member-status-contract-v2
plan_path: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
plan_role: active
revision: 1
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document replacing the eight-attempt append history of post-claim-member-status-contract at architecture level. It awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-post-claim-member-status-contract-v2-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 3EF5AAF2
feature_id: 169-F
shipment_id: 177-S
unit_role: reduced-defect-unit
supersedes_plan: docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
depends_on_shipments: []
dag_role: root
requires_plan_hardening: false
hardening_rationale: "No new executable surface, no command execution, no schema migration of existing mutable records. The change is a declaration contract plus its conformance test; blast radius is bounded by the declared surface list."
tags:
  - defect-unit
  - p002-7
  - member-status
  - reduced-scope
  - dag-root
---

# Canonical post-claim member-status contract (P-002.7)

## Why this unit is a root

Every other unit in this portfolio waits on a foundation because it needs an
executable boundary that does not yet exist. This one does not. It changes
**declarations** — a status vocabulary and the surfaces that state it — and
asserts their agreement with a conformance test.

Attempt 08 recorded no bootstrap, no execution, no schema-compatibility and no
transport finding against it. It was blocked on a single evidence defect.

Making it a root matters: the architecture decision forbids false serial
dependencies among independent successors, and serializing this unit behind
`182-S` → `184-S` → `185-S` would be exactly that.

## The defect

Stash `3EF5AAF2`: when Ship claims a shipment, the member items' post-claim
status is stated differently on different surfaces. There is no canonical
vocabulary, so each surface asserts its own and the divergence is invisible
until a reconcile step reports an integrity error.

## The evidence defect (attempt-08 `B2`)

The previous revision's assertions were **GREEN-only**: each was written to
observe the intended end state, and none was observed failing first.

A GREEN-only assertion cannot distinguish "the contract holds" from "the
assertion does not test the contract". A test that passes before the change and
after it has measured nothing. That is not a stylistic preference about TDD —
it is the same `NO_OBSERVATION`-is-not-`PASS` rule the rest of this portfolio
enforces, applied to this unit's own evidence.

**Every assertion in this unit is observed failing against the current
divergent surfaces before it is observed passing.** The RED observation is
recorded per assertion, not as an aggregate suite result, because an aggregate
non-zero exit does not prove that *this* assertion failed.

## Contract

1. A canonical post-claim member-status vocabulary is defined **once**.
2. Every declared surface states it identically.
3. A conformance test enumerates the surfaces and asserts agreement — so a
   surface added later fails the test rather than silently diverging.
4. The surface list is derived by a rule over tracked files, with generated
   paths excluded by rule. `.autoharness/staging/` is excluded because it is
   gitignored generated output, not a mirror.

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `STATUS_CONTRACT_HELD` — every declared surface states the canonical vocabulary identically |
| Fail state | `STATUS_CONTRACT_DIVERGENT` — named surface and named divergence |
| Producer | the canonical vocabulary definition |
| Consumer | the cross-surface conformance test; Ship's claim sequence |
| Activation commit | one task, one commit across every declared surface and its mirror |

`STATUS_CONTRACT_HELD` is reachable once all declared surfaces are updated.
`STATUS_CONTRACT_DIVERGENT` is reachable **today**, which is what makes the
RED observation possible and the assertions meaningful.

## Rollout

**PREPARE (inert).** The canonical vocabulary and the conformance test are
authored; the test is observed failing per assertion against the current
surfaces. No surface has changed, so live behaviour is unchanged.

**VERIFY.** Per-assertion RED observations recorded, then the same assertions
observed passing after the activation change is staged.

**ACTIVATE.** One task, one commit updating every declared surface —
template and installed mirror together. Splitting them produces a reachable
state in which a mirror states a vocabulary its template does not.

## Out of scope

* Any change to the claim mechanism itself.
* Shipment reconcile classification logic.
* The status-transition table. This unit canonicalizes what member status *is*
  after a claim, not which transitions are legal.

## Note on an adjacent observation

During this session's research, `backlogit` was observed to reject
`queued → abandoned` and `blocked → abandoned` via its
`validate_status_transition` pre-hook, leaving `abandoned` apparently reachable
only through `active`. That is a transition-table observation about the backlog
tool, **not** a post-claim member-status defect, and it is recorded here only
so it is not lost. It is explicitly **not** in this unit's scope.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | The surface list is incomplete | It is derived by rule and asserted at a fixed count, so an unlisted surface fails the test rather than being exempted. |
| R2 | RED observation is claimed rather than recorded | Each assertion's failing observation is recorded individually; an aggregate suite exit code is explicitly insufficient evidence. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Why is this unit not gated behind the substrate foundations? | Because it needs none of them. It changes declarations and asserts their agreement. Serializing it behind `182-S` → `184-S` → `185-S` would be a false dependency, which the architecture decision forbids. |
| H2 | Is a passing conformance test evidence the contract holds? | Only if it was first observed failing. The attempt-08 defect was GREEN-only assertions, which cannot distinguish a held contract from an assertion that tests nothing. |
| H3 | Is an aggregate non-zero suite exit sufficient RED evidence? | No. It does not prove that *this* assertion failed. Each assertion's failing observation is recorded individually. |
| H4 | What if a surface is added after the contract lands? | The surface list is derived by rule and the count is asserted, so a new surface fails the conformance test rather than diverging silently. |
| H5 | Is the `abandoned`-transition observation in scope? | No. It is a backlog-tool transition-table observation recorded so it is not lost, explicitly outside this unit's contract, which concerns what member status *is* after a claim. |
| H6 | Why one commit across all surfaces? | A commit boundary mid-migration is a reachable state in which a mirror states a vocabulary its template does not — the divergence the unit exists to remove. |

### Blast radius

Declaration surfaces and their mirrors, plus one conformance test. No executable
boundary, no command execution, no migration of existing mutable records — which
is why this plan declares `requires_plan_hardening: false` and this section is a
completeness pass rather than a gate.

### Rollback

PREPARE is inert. The ACTIVATE commit reverts as a unit, returning every surface
to its current divergent state simultaneously.

### Verification floor

Every assertion recorded failing before it is recorded passing, individually.
