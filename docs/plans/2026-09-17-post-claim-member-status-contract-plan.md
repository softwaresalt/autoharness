---
title: "Canonical post-claim member-status contract and downstream-conformance verification"
description: "Implementation plan naming the post-claim manifest-member status expectation as a versioned canonical policy clause with the backlogit claim-cascade attribution inline, cross-linking it to the existing Ship-agent tolerance note so the two cannot drift, adding a verify-workspace check that fails closed when an installed policy registry declares a wave-admission rule treating post-claim member active as a blocking residual, and pinning the claim-to-admission transition with a composed state-machine test."
doc_type: plan
source: docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
date: 2026-09-17
status: reviewed
revision: 2
revision_note: "Revision 2 is the canonical statement of the intended design. Review findings were remediated in place; this document states exactly one binding requirement per topic. The bounded audit trail lives in `linked_review`."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 1
source_spike: docs/spikes/2026-09-17-post-claim-member-status-contract-spike.md
source_bug_report: docs/bugs/2026-09-17-autoharness-shipment-claim-wave-admission-contract-conflict.md
source_stash_id: 3EF5AAF2
stash_ids:
  - 3EF5AAF2
prior_learnings:
  - docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
linked_review: docs/reviews/2026-09-17-post-claim-member-status-contract-plan-review.md
covering_feature: 169-F
shipment: 177-S
requires_plan_hardening: "yes"
plan_hardening_status: complete
tags:
  - "policy"
  - "shipment-claim"
  - "contract-drift"
  - "verify-workspace"
  - "fail-closed-design"
---

# Canonical post-claim member-status contract

## Problem

Stash `3EF5AAF2` reports a deterministic deadlock: backlogit `ClaimShipment`
activates every queued manifest member atomically with the shipment, while a
`P-002.6` wave-admission policy halts with `WAVE_NO_PROGRESS` on any member
found `active` at admission.

The spike (`docs/spikes/2026-09-17-post-claim-member-status-contract-spike.md`)
established by existence proof that **`P-002.6` does not exist in autoharness**
— `git log -S` over all refs returns only the commit that added the bug report
— and that the canonical Ship contract **already tolerates** post-claim
all-active members, in both `templates/agents/_ship.agent.md.tmpl` (line 274)
and `.github/agents/_ship.agent.md` (line 322).

The actionable defect is therefore not the halt. It is that the canonical
tolerance is prose-only, unnamed, unversioned, and unenforced, so a consuming
workspace can author a contradictory admission rule into that vacuum — which is
exactly what `P-002.6` is — and nothing in the harness detects it.

## Design

### Part 1 — Name the contract (`P-002.7`)

Add a numbered sub-clause to P-002 in `templates/policies/workflow-policies.md.tmpl`
and its installed mirror, stating:

* **Statement.** Immediately after a shipment claim, every queued manifest
  member legitimately reads `active`. This is the claim operation's own
  cascade, not evidence of prior partial execution.
* **Attribution (inline, versioned).** backlogit `ClaimShipment` activates the
  shipment record and every included queued member in one all-or-nothing
  operation; observed and recorded for 1.10.0 in
  `docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`
  and asserted upstream by `TestClaimShipment_ActivatesIncludedScope`. The
  clause records the **observed version range** and instructs re-verification
  against whatever version is installed, rather than asserting the behaviour
  for all versions.
* **Prohibition.** No derived or workspace-local admission rule may treat the
  post-claim all-active state as a blocking residual.
* **Preserved distinction.** A *mid-execution partial-active* manifest — some
  members `done`, some `active`, some `queued` — is a genuinely different
  state and any active-residual gate a workspace authors for it remains valid
  and is **not** weakened. The discriminator is the claim boundary, not member
  status alone.
* **Relationship to `SHIPMENT_STATE_INCONSISTENT`.** The existing early-warning
  fires on the inverse condition (record `queued`, member `active` or `done`)
  and is untouched. The new clause explicitly states that it does not
  suppress, soften, or pre-empt that halt.

### Part 2 — Prevent drift

Cross-reference the new clause from the Ship-agent intake-reconciliation scope
note in both the template and the installed mirror, so the tolerance prose and
the policy clause name each other. A structural test asserts the cross-
reference resolves in both directions and in both copies.

### Part 3 — Detect the contradiction downstream

Extend `src/autoharness/verify_workspace.py` with a fail-closed check over the
installed policy registry:

| Token | Condition |
|---|---|
| `POST_CLAIM_CONTRACT_MISSING` | The installed registry has P-002 but no post-claim member-status clause |
| `POST_CLAIM_CONTRACT_CONTRADICTED` | The installed registry declares an admission rule treating post-claim member `active` as blocking |
| `POST_CLAIM_CONTRACT_UNVERSIONED` | The clause is present but carries no observed-version attribution |

Detection is **declarative and conservative**: it matches on the policy
registry's own structured clause vocabulary, not on free prose. A workspace
that has authored a genuine mid-execution residual gate (the preserved
distinction above) must **not** trip `POST_CLAIM_CONTRACT_CONTRADICTED`; the
regression suite carries that exact negative case.

### Part 4 — Pin the transition

Composed state-machine test for the claim→admission transition, per
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`
Lesson 1/6 — for every gate, name one concrete legitimate state that passes and
one that fails:

| State | Expected |
|---|---|
| Record `active`, all members `active`, claim just issued | **admit** |
| Record `queued`, one member `active` | **halt** `SHIPMENT_STATE_INCONSISTENT` |
| Record `active`, mixed `done`/`active`/`queued` mid-execution | **admit**, not an intake-reconciliation case |
| Registry declaring post-claim-active-is-residual | **halt** `POST_CLAIM_CONTRACT_CONTRADICTED` |

## Work Breakdown

| # | Task | Scope |
|---|---|---|
| T1 | Author the `P-002.7` clause in the policy **template** | `templates/policies/workflow-policies.md.tmpl` |
| T2 | Apply the identical clause to the installed mirror, atomically with T1 | `.github/policies/workflow-policies.md` |
| T3 | Add the bidirectional cross-reference in the Ship template and installed mirror | `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md` |
| T4 | Implement the three `verify-workspace` tokens with declarative clause-vocabulary matching | `src/autoharness/verify_workspace.py` |
| T5 | Composed state-machine regression test for the four transition states | `tests/` |
| T6 | Negative-case suite: a legitimate mid-execution residual gate must not trip the contradiction token | `tests/` |
| T7 | Document the contract and the downstream-conformance check | `docs/` |

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* `autoharness verify-workspace` on this repository reports the clause present,
  versioned, and uncontradicted.
* `autoharness gate check` passes on every modified file.
* Cross-reference resolution asserted in both directions, both copies.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | The contradiction check false-positives on a legitimate mid-execution residual gate | T6 is a dedicated negative suite; matching is on structured clause vocabulary, never free prose |
| R2 | The version attribution becomes stale as backlogit moves | The clause records an *observed* range and mandates re-verification; `POST_CLAIM_CONTRACT_UNVERSIONED` makes the absence of attribution itself a failure |
| R3 | Adding a verify-workspace failure mode blocks existing consumer workspaces on upgrade | The three tokens are introduced in report-only severity for one release, then promoted; the promotion is a declared follow-up, not silent |
| R4 | The clause is read as licence to weaken a genuine stalled-wave gate | The Preserved distinction paragraph is normative text in the clause itself, and R1's negative suite enforces it |

## Out of scope

* Any change to backlogit. The upstream contract is correct and no upstream
  request is filed for this entry (spike Q3).
* Editing, weakening, or removing `P-002.6` in any consuming workspace.
  autoharness publishes a canonical clause; it does not reach into consumers.
* The report's Option A and Option B, both of which presuppose changing what
  claim does.
* `149-S`, `140-S`, and `CC0EBB59`, which live in another workspace's history
  and are cited as evidence only.
