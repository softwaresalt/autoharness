---
title: "Canonical post-claim member-status contract (downstream-conformance detection withdrawn)"
description: "Implementation plan naming the post-claim manifest-member status expectation as a versioned canonical policy clause with the backlogit claim-cascade attribution inline, cross-linking it bidirectionally to the existing Ship-agent tolerance note so the two cannot drift, and pinning the claim-to-admission transition with a composed state-machine test. Downstream detection of a contradictory workspace-authored admission rule is explicitly NOT delivered here: it presupposes a typed, machine-readable policy-clause representation that does not exist, and speculative free-text parsing of policy prose is rejected."
doc_type: plan
source: docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
date: 2026-09-17
status: reviewed
revision: 5
revision_note: "Revision 5 (remediation cycle 3) answers review attempt 05, which returned BLOCKED at revision 4 on three coupled defects, all of which left the WITHDRAWN downstream-conformance detector still advertised as deliverable. (1) `deferred_followup_stash_ids` held the unresolvable prose placeholder `pending: typed policy-clause representation for downstream conformance detection` instead of a backlog-resolvable identifier, so the deferral had no traceable destination; it is now the exact stash ID **E770139B**. (2) The plan title still read `... and downstream-conformance verification`, advertising as a deliverable the very capability decision revision 3 (D3) withdrew; the title now reads `(downstream-conformance detection withdrawn)` and the description already stated the withdrawal. (3) The `source_spike` reference pointed at a spike whose body still treats the detector as an open in-scope question, with nothing marking it superseded; a `source_spike_note` now states that D3 withdrew the detector and deferred it to E770139B. Revision 5 also propagates the revision label and the withdrawn/deferred wording into the executable records (169-F, 177-S and every live 169.* task body). Revision 5 is STAGE-REMEDIATED AND PENDING INDEPENDENT REVIEW ATTEMPT 06; Stage does not review its own remediation and asserts no PASS. Revision 4 (remediation cycle 2) adopted decision revision 3, which formally withdraws the downstream-conformance detector in D3 rather than leaving it as an open spike question. The design is otherwise unchanged from revision 3 — this release unit still delivers contract-naming plus cross-surface structural evidence only. Revision 4 exists because the withdrawn claims had NOT been propagated out of the executable backlog records: feature, task and shipment bodies still described a detector, a fourth `POST_CLAIM_CONTRACT_CONTRADICTED` transition state, and a verify-workspace surface that this plan explicitly does not deliver. Those claims are removed at the record level and the task titles, references and dependencies are reconciled. The two withdrawn tasks are re-homed to a deferred feature under P-021 capture rather than left inside the covering feature, so the shipment can close without implementing deferred scope. The bounded audit trail lives in `linked_review`."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_spike: docs/spikes/2026-09-17-post-claim-member-status-contract-spike.md
source_spike_note: "The spike explored a downstream contradiction detector for workspace-authored admission rules. Decision revision 3 (D3) WITHDREW that detector from this release unit and DEFERRED it to stash entry E770139B (typed, machine-readable policy-clause representation). Any spike text describing the detector as in-scope is superseded history; this plan delivers contract naming plus cross-surface structural evidence only."
source_bug_report: docs/bugs/2026-09-17-autoharness-shipment-claim-wave-admission-contract-conflict.md
source_stash_id: 3EF5AAF2
stash_ids:
  - 3EF5AAF2
prior_learnings:
  - docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
linked_review: docs/reviews/2026-09-17-post-claim-member-status-contract-plan-review.md
review_history:
  - docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-04.md
  - docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-05.md
review_history_note: "Attempts 01-02 were authored as one mutable file covering two cycles; it is preserved verbatim and classified rather than retroactively split into records that were never independently authored. Attempt 03 is a conforming single-attempt immutable artifact. Attempt 04 records local review cycle 2 (BLOCKED at revision 3, on non-propagation of the design into the executable backlog records) and the Stage remediation response. Attempt 05 records the final independent review cycle (BLOCKED at revision 4) and the Stage remediation cycle 3 response that produced revision 5."
latest_review_attempt: 5
latest_review_artifact: docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-05.md
latest_review_verdict: REMEDIATED-PENDING-REVIEW
latest_review_verdict_note: "Attempt 05 returned BLOCKED at plan revision 4 on the unpopulated deferred_followup_stash_ids placeholder and the residual downstream-conformance advertising in the title and spike reference. Stage remediation cycle 3 closed every attempt-05 finding and raised this plan to revision 5. Stage does not review its own remediation, so NO PASS is asserted at revision 5; the next independent reviewer pass is attempt 06."
covering_feature: 169-F
shipment: 177-S
requires_plan_hardening: "yes"
plan_hardening_status: complete
plan_hardening_section: "## Plan Hardening Record (P-006)"
deferred_followup_stash_ids:
  - "E770139B"
deferred_followup_stash_note: "E770139B is the live stash entry carrying the WITHDRAWN downstream contradiction detector and its prerequisite, a typed machine-readable policy-clause representation. Revision 4 left this field holding an unresolvable prose placeholder rather than a real stash ID; revision 5 replaces it with the exact captured entry."
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

### Part 3 — downstream contradiction detection: NOT delivered here

Revision 2 specified a `verify-workspace` check emitting
`POST_CLAIM_CONTRACT_MISSING`, `POST_CLAIM_CONTRACT_CONTRADICTED`, and
`POST_CLAIM_CONTRACT_UNVERSIONED`, and asserted that detection would be
"declarative and conservative … matches on the policy registry's own
structured clause vocabulary, not on free prose."

**That premise is false in this repository, and the check is removed from this
release unit.** The observable facts:

* `.github/policies/workflow-policies.md` and its template are Markdown prose.
  There is no typed clause record, no clause schema, no clause ID index, and
  no "structured clause vocabulary" for a matcher to consume.
* Parts 1 and 2 of this plan add **more Markdown prose**. They do not create
  the representation the detector was specified against.
* A detector implemented against this surface could only be a heuristic over
  free text. `POST_CLAIM_CONTRACT_CONTRADICTED` in particular would have to
  distinguish a prohibited post-claim residual rule from a legitimate
  mid-execution residual gate by reading English. That is precisely the
  speculative free-text parsing the revision-2 text disclaimed while
  simultaneously requiring.

Shipping a prose change under a machine-readable-detector description is a
scope-honesty defect regardless of whether the prose itself is correct. The
honest release unit is naming and cross-linking, which is what this plan now
delivers.

**Deferred prerequisite, recorded not discarded.** A typed policy-clause
representation — clause identity, versioned attribution, machine-readable
prohibition/permission predicates, and a schema the installed registry must
satisfy — is real work with its own blast radius across `schemas/`,
`templates/policies/`, and `src/autoharness/verify_workspace.py`. It is
captured as a separate Stage stash entry and is **not** a member of `177-S`.
Downstream conformance detection becomes plannable only after that
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

The fourth revision-2 row — "registry declaring post-claim-active-is-residual →
halt `POST_CLAIM_CONTRACT_CONTRADICTED`" — is removed with Part 3. There is no
token to assert.

## Work Breakdown

| # | Task | Scope |
|---|---|---|
| T1 | Author the `P-002.7` clause in the policy **template** | `templates/policies/workflow-policies.md.tmpl` |
| T2 | Apply the identical clause to the installed mirror, atomically with T1 | `.github/policies/workflow-policies.md` |
| T3 | Add the bidirectional cross-reference in the Ship template and installed mirror | `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md` |
| T4 | Structural test asserting the cross-reference resolves in both directions and in both copies, and that the clause carries its observed-version attribution | `tests/` |
| T5 | Composed state-machine regression test for the three transition states | `tests/` |
| T6 | Document the contract, its preserved distinction, and the explicitly-undelivered downstream detection | `docs/` |

Removed from this release unit with Part 3: the `verify-workspace` token
implementation and its negative-case suite. Their scope moves to the deferred
typed-policy-representation entry.

T4 replaces the assertion the removed detector would have made, at the only
level this surface actually supports: a structural check that the two prose
sites name each other and that the attribution paragraph is present. It makes
no judgement about a consuming workspace's rules, because it cannot.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* `autoharness gate check` passes on every modified file.
* Cross-reference resolution asserted in both directions, both copies.
* The clause's observed-version attribution paragraph is present in both copies.
* No new `verify-workspace` token is introduced by this release unit, and no
  document in it claims one is.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | The clause is read as licence to weaken a genuine stalled-wave gate | The Preserved distinction paragraph is normative text in the clause itself; T6 restates it in the documentation surface |
| R2 | The version attribution becomes stale as backlogit moves | The clause records an *observed* range and mandates re-verification; T4 asserts the attribution paragraph exists, so its silent deletion is caught even though its staleness is not |
| R3 | The deferred detector is quietly forgotten | It is recorded as a named Stage stash entry, restated in this plan's Out of scope, and named in the covering feature body; it is not merely absent |
| R4 | A future reader assumes downstream conformance is enforced | Part 3 states the non-delivery explicitly and gives the reason; the documentation task T6 carries the same statement into `docs/` |
| R5 | Template/mirror drift between T1 and T2, or T3's two copies | T2 blocks on T1; T4 asserts both copies |

## Out of scope

* Any change to backlogit. The upstream contract is correct and no upstream
  request is filed for this entry (spike Q3).
* **Downstream conformance detection in `verify-workspace`**, and the typed
  policy-clause representation it requires. Deferred to a separate Stage entry
  (see Part 3). No token, no matcher, and no `src/autoharness/verify_workspace.py`
  change is delivered by `177-S`.
* Editing, weakening, or removing `P-002.6` in any consuming workspace.
  autoharness publishes a canonical clause; it does not reach into consumers.
* The report's Option A and Option B, both of which presuppose changing what
  claim does.
* `149-S`, `140-S`, and `CC0EBB59`, which live in another workspace's history
  and are cited as evidence only.

## Plan Hardening Record (P-006)

Hardening applied 2026-09-17, re-run 2026-09-18 during remediation cycle 1.
Revision 2 declared `plan_hardening_status: complete` without persisting this
record, so the declaration was unverifiable — that gap is itself H0 below.

**Hardening trigger.** Elevated blast radius on three axes: the change edits a
policy registry that every downstream consumer workspace installs; it edits an
agent template *and* its installed mirror, a pair with a recorded drift class;
and revision 2 proposed a new fail-closed `verify-workspace` failure mode that
would have fired on existing consumer workspaces at upgrade time.

**Protected invariants.**

* `SHIPMENT_STATE_INCONSISTENT` must keep firing on the inverse condition
  (record `queued`, member `active`/`done`). Nothing here may suppress it.
* A genuine mid-execution partial-active residual gate must remain valid. The
  discriminator is the claim boundary, never member status alone.
* Template and installed mirror must not diverge.
* autoharness publishes a canonical clause; it never mutates a consumer
  workspace's policy file.

**Instructions and learnings consulted.**
`.github/policies/workflow-policies.md` (P-002 numbering and clause style),
`.github/instructions/backlogit.instructions.md`,
`docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`,
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`,
`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`,
and `docs/spikes/2026-09-17-post-claim-member-status-contract-spike.md`.

| # | Hardening finding | Resolution |
|---|---|---|
| H0 | Revision 2 asserted `plan_hardening_status: complete` with no persisted hardening record, so P-006 compliance rested on a frontmatter claim alone | This section is the record; `plan_hardening_section` in frontmatter now names it so the claim is checkable |
| H1 | The revision-2 `verify-workspace` detector had no typed representation to match against and would necessarily have been a free-text heuristic | Detector removed from the release unit (Part 3); the typed-representation prerequisite is deferred as named Stage work rather than assumed |
| H2 | `POST_CLAIM_CONTRACT_CONTRADICTED` would have had to distinguish a prohibited rule from a legitimate mid-execution gate by reading English — a false-positive that blocks a *correct* consumer gate | Eliminated with H1. The preserved distinction is now carried by normative clause prose and T6 documentation, with no automated judgement claimed |
| H3 | Revision 2's R3 mitigation ("report-only for one release, then promoted") described a rollout no task implemented and no artifact recorded | Removed with the detector. No staged-severity rollout is claimed |
| H4 | Removing the detector removes the only assertion that the two prose sites stay coupled | New T4 structural test asserts bidirectional cross-reference resolution in both copies and the presence of the version-attribution paragraph |
| H5 | Clause version attribution could rot silently as backlogit moves | Attribution records an **observed** range with a re-verification instruction, not a universal claim; T4 pins its presence. Staleness detection is explicitly not claimed |
| H6 | Scope creep risk back into backlogit or consumer policy files | Out of scope restated with the detector deferral named; spike Q3 already established no upstream request is warranted |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Edit `templates/policies/workflow-policies.md.tmpl` (add `P-002.7`) | Medium — consumer-installed surface | Standard PR review | Revert the clause block; additive, no existing clause renumbered |
| Edit `.github/policies/workflow-policies.md` (mirror) | Medium — must land with T1 | Standard PR review | Revert together with T1; T2 blocks on T1 |
| Edit `templates/agents/_ship.agent.md.tmpl` + installed mirror (cross-reference) | Low — additive reference text | Standard PR review | Revert the reference lines |
| *(withdrawn)* Add fail-closed `verify-workspace` tokens | **High** — new blocking failure mode on every consumer workspace at upgrade | Would have required operator sign-off | Not applicable: action withdrawn from this release unit |

**Rollback coupling.** T1+T2 revert together (mirror pair). T3's two copies
revert together. T4/T5 are test-only and revert independently. No data
migration, no state mutation, no destructive action anywhere in the unit.

**Operator checkpoints.** None required. The withdrawal of the high-risk
action is what removes the one checkpoint revision 2 would have needed.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit a literal
`dispatch_mode:` marker declaring the fallback and a literal `decision:`
marker, and MUST apply the Agent-Native Parity persona inline because this plan
edits agent-template contract text.

**Unresolved operator decisions blocking safe execution.** None.
