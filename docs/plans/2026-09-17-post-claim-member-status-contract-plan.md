---
title: "Canonical post-claim member-status contract (downstream-conformance detection withdrawn)"
description: "Implementation plan naming the post-claim manifest-member status expectation as a versioned canonical policy clause with the backlogit claim-cascade attribution inline, cross-linking it bidirectionally to the existing Ship-agent tolerance note so the two cannot drift, and pinning the claim-to-admission transition with a composed state-machine test. Downstream detection of a contradictory workspace-authored admission rule is explicitly NOT delivered here: it presupposes a typed, machine-readable policy-clause representation that does not exist, and speculative free-text parsing of policy prose is rejected."
doc_type: plan
source: docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
date: 2026-09-17
status: reviewed
plan_id: post-claim-member-status-contract
plan_role: active
revision: 6
supersedes: null
superseded_by: null
source_history:
  - docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-04.md
  - docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-05.md
  - docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-06.md
  - docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md
review_manifest: docs/reviews/2026-09-17-post-claim-member-status-contract-plan-review.md
revision_note: "Revision 6 is maintained as one coherent current-state contract rather than as an accreting record of corrections. Prior-revision deltas, superseded requirement variants, and reviewer chronology are not carried in the body: the immutable per-attempt review artifacts listed in source_history and the mutable verdict manifest named by review_manifest are the authoritative record of that chronology. Latest attempt and verdict are read from the manifest, never from this file."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_spike: docs/spikes/2026-09-17-post-claim-member-status-contract-spike.md
source_spike_note: "The spike explored a downstream contradiction detector for workspace-authored admission rules. Decision revision 3 (D3) WITHDREW that detector from this release unit and DEFERRED it to stash entry E770139B (typed, machine-readable policy-clause representation). Spike text describing the detector as in-scope does not govern this plan, which delivers contract naming plus cross-surface structural evidence only."
source_bug_report: docs/bugs/2026-09-17-autoharness-shipment-claim-wave-admission-contract-conflict.md
source_stash_id: 3EF5AAF2
stash_ids:
  - 3EF5AAF2
prior_learnings:
  - docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
covering_feature: 169-F
shipment: 177-S
requires_plan_hardening: "yes"
plan_hardening_status: complete
plan_hardening_section: "## Plan Hardening Record (P-006)"
deferred_followup_stash_ids:
  - "E770139B"
deferred_followup_stash_note: "E770139B is the live stash entry carrying the WITHDRAWN downstream contradiction detector and its prerequisite, a typed machine-readable policy-clause representation. It is not a member of 177-S."
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

## Decision being implemented

Decision **D3**: name and cross-link the contract, and pin the claim→admission
transition with a composed state-machine test. Downstream detection of a
contradictory workspace-authored admission rule is **withdrawn from this
release unit** and deferred to stash entry `E770139B`, because it presupposes a
typed, machine-readable policy-clause representation that does not exist in
this repository.

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

### Part 3 — Downstream contradiction detection is not delivered here

A `verify-workspace` check emitting `POST_CLAIM_CONTRACT_MISSING`,
`POST_CLAIM_CONTRACT_CONTRADICTED`, and `POST_CLAIM_CONTRACT_UNVERSIONED` is
**not** part of this release unit. The reason is the state of the surface it
would have to match against:

* `.github/policies/workflow-policies.md` and its template are Markdown prose.
  There is no typed clause record, no clause schema, no clause ID index, and
  no structured clause vocabulary for a matcher to consume.
* Parts 1 and 2 add **more Markdown prose**. They do not create the
  representation such a detector would be specified against.
* A detector implemented against this surface could only be a heuristic over
  free text. `POST_CLAIM_CONTRACT_CONTRADICTED` in particular would have to
  distinguish a prohibited post-claim residual rule from a legitimate
  mid-execution residual gate by reading English — precisely the speculative
  free-text parsing this plan rejects.

Shipping a prose change under a machine-readable-detector description is a
scope-honesty defect regardless of whether the prose itself is correct. The
honest release unit is naming and cross-linking, which is what this plan
delivers.

**Deferred prerequisite, recorded not discarded.** A typed policy-clause
representation — clause identity, versioned attribution, machine-readable
prohibition/permission predicates, and a schema the installed registry must
satisfy — is real work with its own blast radius across `schemas/`,
`templates/policies/`, and `src/autoharness/verify_workspace.py`. It is
captured as Stage stash entry **`E770139B`** and is **not** a member of
`177-S`. Downstream conformance detection becomes plannable only after that
representation exists. Until then, a consuming workspace authoring a
contradictory admission rule is caught by human review of the canonical clause,
not by a gate — which is the current state, stated truthfully rather than
overclaimed.

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

The matrix has exactly these three rows. There is no
`POST_CLAIM_CONTRACT_CONTRADICTED` row, because this release unit introduces no
such token to assert.

## Work Breakdown

| # | Task | Scope |
|---|---|---|
| T1 | Author the `P-002.7` clause in the policy **template** | `templates/policies/workflow-policies.md.tmpl` |
| T2 | Apply the identical clause to the installed mirror, atomically with T1 | `.github/policies/workflow-policies.md` |
| T3 | Add the bidirectional cross-reference in the Ship template and installed mirror | `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md` |
| T4 | Structural test asserting the cross-reference resolves in both directions and in both copies, and that the clause carries its observed-version attribution | `tests/` |
| T5 | Composed state-machine regression test for the three transition states | `tests/` |
| T6 | Document the contract, its preserved distinction, and the explicitly-undelivered downstream detection | `docs/` |

T1 and T2 are one atomic change set: T2 declares a `blocks` dependency on T1 so
the template and its installed mirror cannot land apart.

**Not in this release unit:** the `verify-workspace` token implementation and
its negative-case suite. That scope belongs to the deferred typed-policy-
representation entry `E770139B`.

T4 is the assertion this surface actually supports: a structural check that the
two prose sites name each other and that the attribution paragraph is present.
It makes no judgement about a consuming workspace's rules, because it cannot.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* `autoharness gate check` passes on every modified file.
* Cross-reference resolution asserted in both directions, both copies.
* The clause's observed-version attribution paragraph is present in both copies.
* The composed state-machine test carries exactly the three transition rows.
* No new `verify-workspace` token is introduced by this release unit, and no
  document in it claims one is.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | The clause is read as licence to weaken a genuine stalled-wave gate | The Preserved distinction paragraph is normative text in the clause itself; T6 restates it in the documentation surface |
| R2 | The version attribution becomes stale as backlogit moves | The clause records an *observed* range and mandates re-verification; T4 asserts the attribution paragraph exists, so its silent deletion is caught even though its staleness is not |
| R3 | The deferred detector is quietly forgotten | It is recorded as Stage stash entry `E770139B`, restated in this plan's Out of scope, and named in the covering feature body; it is not merely absent |
| R4 | A future reader assumes downstream conformance is enforced | Part 3 states the non-delivery explicitly and gives the reason; T6 carries the same statement into `docs/` |
| R5 | Template/mirror drift between T1 and T2, or T3's two copies | T2 blocks on T1; T4 asserts both copies |

## Out of scope

* Any change to backlogit. The upstream contract is correct and no upstream
  request is filed for this entry (spike Q3).
* **Downstream conformance detection in `verify-workspace`**, and the typed
  policy-clause representation it requires. Deferred to stash entry
  `E770139B` (see Part 3). No token, no matcher, and no
  `src/autoharness/verify_workspace.py` change is delivered by `177-S`.
* Editing, weakening, or removing `P-002.6` in any consuming workspace.
  autoharness publishes a canonical clause; it does not reach into consumers.
* The report's Option A and Option B, both of which presuppose changing what
  claim does.
* `149-S`, `140-S`, and `CC0EBB59`, which live in another workspace's history
  and are cited as evidence only.

## Plan Hardening Record (P-006)

**Hardening trigger.** Elevated blast radius on two axes: the change edits a
policy registry that every downstream consumer workspace installs, and it edits
an agent template *and* its installed mirror, a pair with a recorded drift
class.

**Protected invariants.**

* `SHIPMENT_STATE_INCONSISTENT` must keep firing on the inverse condition
  (record `queued`, member `active`/`done`). Nothing here may suppress it.
* A genuine mid-execution partial-active residual gate must remain valid. The
  discriminator is the claim boundary, never member status alone.
* Template and installed mirror must not diverge.
* autoharness publishes a canonical clause; it never mutates a consumer
  workspace's policy file.
* No new fail-closed `verify-workspace` failure mode is introduced by this
  release unit, so no consumer workspace gains a new blocking condition at
  upgrade time.

**Instructions and learnings consulted.**
`.github/policies/workflow-policies.md` (P-002 numbering and clause style),
`.github/instructions/backlogit.instructions.md`,
`docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`,
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`,
`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`,
and `docs/spikes/2026-09-17-post-claim-member-status-contract-spike.md`.

| # | Hazard | Resolution in this contract |
|---|---|---|
| H1 | A `verify-workspace` detector has no typed representation to match against on this surface and could only be a free-text heuristic | Detection is not in the release unit (Part 3); the typed-representation prerequisite is deferred as named Stage work `E770139B` rather than assumed |
| H2 | `POST_CLAIM_CONTRACT_CONTRADICTED` would have to distinguish a prohibited rule from a legitimate mid-execution gate by reading English — a false positive that blocks a *correct* consumer gate | Eliminated with H1. The preserved distinction is carried by normative clause prose and T6 documentation, with no automated judgement claimed |
| H3 | A staged-severity rollout ("report-only for one release, then promoted") would describe a sequence no task implements and no artifact records | No detector and no staged-severity rollout is claimed anywhere in this unit |
| H4 | Without a detector, nothing asserts that the two prose sites stay coupled | T4 structural test asserts bidirectional cross-reference resolution in both copies and the presence of the version-attribution paragraph |
| H5 | Clause version attribution can rot silently as backlogit moves | Attribution records an **observed** range with a re-verification instruction, not a universal claim; T4 pins its presence. Staleness detection is explicitly not claimed |
| H6 | Scope creep back into backlogit or into consumer policy files | Out of scope restated with the detector deferral named; spike Q3 already established no upstream request is warranted |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Edit `templates/policies/workflow-policies.md.tmpl` (add `P-002.7`) | Medium — consumer-installed surface | Standard PR review | Revert the clause block; additive, no existing clause renumbered |
| Edit `.github/policies/workflow-policies.md` (mirror) | Medium — must land with T1 | Standard PR review | Revert together with T1; T2 blocks on T1 |
| Edit `templates/agents/_ship.agent.md.tmpl` + installed mirror (cross-reference) | Low — additive reference text | Standard PR review | Revert the reference lines |

**Rollback coupling.** T1+T2 revert together (mirror pair). T3's two copies
revert together. T4/T5 are test-only and revert independently. No data
migration, no state mutation, no destructive action anywhere in the unit.

**Operator checkpoints.** None required. Every action in the unit is additive
prose or a test; the unit introduces no new blocking failure mode.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit a literal
`dispatch_mode:` marker declaring the fallback and a literal `decision:`
marker, and MUST apply the Agent-Native Parity persona inline because this plan
edits agent-template contract text.

**Unresolved operator decisions blocking safe execution.** None.
