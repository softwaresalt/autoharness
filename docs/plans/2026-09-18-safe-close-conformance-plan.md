---
title: "SAFE_CLOSE record-transition: isolated conformance evidence and upstream escalation"
description: "Reduced current-state contract for the SAFE_CLOSE defect. Removes the unsupported administrative-close transition and its untested rollback entirely, moves external-binary conformance to an isolated Linux CI container with no credentials, egress denied after acquisition, a read-only or absent repository and disposable mounts, and reduces the local shipment scope to evidence and upstream escalation only. 002-C stays blocked and outside every shipment manifest. Out-of-scope task 173.012-T is archived."
doc_type: plan
source: docs/plans/2026-09-18-safe-close-conformance-plan.md
date: 2026-09-18
plan_id: safe-close-conformance
plan_path: docs/plans/2026-09-18-safe-close-conformance-plan.md
plan_role: conditional-future
harvest_status: withheld
harvest_withheld_reason: "Shipment 181-S, covering feature 173-F and its tasks were harvested prematurely and are archived as a conditional future unit. A blocks edge onto the predecessor spike clears on predecessor COMPLETION and cannot enforce the spike's verdict token, and no installed shipment-claim predicate reads the findings artifact. Withheld by archival - a repository-supported backlog operation - because a live shipment carrying an invented blocked status is malformed data under the pre_claim status vocabulary. PR #457 review thread PRRT_kwDORzpWpM6kHrxK."
harvest_gate_artifact: docs/spikes/2026-09-18-conformance-isolation-findings.md
reharvest_condition: "Stage re-harvests this plan's records only in a NEW staging session, after reading the gate artifact and observing an authorizing isolation verdict. Non-authorizing states harvest nothing. This plan is PRESERVED INTACT and UNREDUCED; only its live, claimable records are withdrawn."
withheld_records: .backlogit/archive/
revision: 1
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document replacing the eight-attempt append history of safe-close-record-transition-disposition at architecture level. It awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-safe-close-conformance-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 7F9CB5E9
feature_id: 173-F
shipment_id: 181-S
unit_role: reduced-defect-unit
supersedes_plan: docs/plans/2026-09-17-safe-close-record-transition-disposition-plan.md
depends_on_shipments:
  - 183-S
input_contract: docs/spikes/2026-09-18-conformance-isolation-findings.md
task_reharvest_gate: 183-S
requires_plan_hardening: true
hardening_rationale: "Executes an external third-party binary. Isolation is the entire safety argument, and the attempt-08 findings were concentrated in sandboxing, redirect handling, TOCTOU and platform mismatch."
tags:
  - defect-unit
  - safe-close
  - conformance
  - isolation
  - reduced-scope
---

# SAFE_CLOSE record-transition: isolated conformance and escalation

## Reduction: what was removed, not deferred

Attempt 08 recorded eight P1 findings against this unit. The largest were not
implementation errors — they were consequences of the unit trying to **ship a
workaround for a transition the tool does not support**.

| Previously in scope | Disposition |
|---|---|
| Administrative-close transition | **Removed.** No supported, tested transition exists, and none is invented here. |
| Rollback for that transition | **Removed** with it. A rollback for an unsupported transition is untestable by construction. |
| Windows-local conformance run | **Removed.** Replaced by isolated Linux CI; the Windows/Linux mismatch finding disappears rather than being patched. |
| Redirect allowlist, TOCTOU and hardlink handling in a local run | **Moved** into the isolation boundary, where they are container properties rather than hand-written checks. |
| Oversized T0 task | **Removed.** Its scope is re-sliced against the `183-S` findings. |
| `173.012-T` (mutates finalized non-member `002-C`) | **Archived.** Out of scope; it reached outside the shipment's membership. |

The architecture decision's position is explicit: **no administrative-close
workaround ships until a supported, tested transition and rollback exist. If
none exists, the local shipment scope is evidence and documentation only.**
None exists. So that is the scope.

This is a reduction by *deletion*, which is why this unit's task count falls
rather than growing for a ninth time.

## What remains

1. **Isolated conformance evidence.** The external binary's record-transition
   behaviour is observed in an isolated Linux CI container:
   * no credentials of any kind present in the environment;
   * network egress **denied after acquisition** — the binary is fetched, then
     the network is closed, so a conformance run cannot reach anything;
   * the repository **read-only or absent**;
   * **disposable mounts**, discarded with the container.
2. **Upstream escalation.** The observed gap is reported upstream with the
   evidence record, because the fix belongs in the tool, not in a local
   workaround.
3. **In-workspace documentation.** The blocked state, its cause, and the
   operator-only interim path are documented. The interim path is **operator
   action outside the agent surface** — it is not automated, not delegated to
   Ship, and not reachable from any agent procedure.

## 002-C stays blocked

`002-C` remains blocked and **outside every shipment manifest**. It is not a
member of `181-S`, not a member of any other shipment, and no task in this unit
mutates it. Its blocked state is the honest record of an unsupported
transition, and closing it administratively would be the exact workaround this
reduction removes.

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `CONFORMANCE_OBSERVED` — the isolated run completed and the transition behaviour was recorded, whatever that behaviour was |
| Fail state | `CONFORMANCE_UNOBSERVED` — isolation could not be established, or the run did not complete. **Not a conformance verdict**; an absent observation. |
| Third state | `ISOLATION_REFUSED` — a precondition of the sandbox was unmet (credentials present, egress open, repository writable). The run does not start. |
| Producer | the `183-S` isolation findings; the CI container definition |
| Consumer | the evidence record and the upstream escalation |
| Activation commit | one task, one commit: CI definition plus the documentation of the blocked state and operator-only interim path |

Note that `CONFORMANCE_OBSERVED` does **not** mean the binary conforms. It
means the behaviour was observed under isolation. A non-conforming observation
is a successful outcome of this unit — the evidence is the deliverable.

## Rollout

**PREPARE (inert).** The container definition and evidence-record format are
authored; nothing runs in CI and no documentation is switched over.

**VERIFY.** `ISOLATION_REFUSED` observed reachable by violating each
precondition in turn — a sandbox whose refusal path has never been observed is
a sandbox nobody has tested.

**ACTIVATE.** One task, one commit: the CI definition and the workspace
documentation of the blocked state land together.

## Task re-harvest gate

Deferred until `183-S` reports whether the isolation properties are achievable
in this workspace's CI and whether the boundary is reusable. If `183-S` finds
the properties unachievable, this unit reduces further — to documentation and
escalation only, with no conformance run at all — rather than relaxing an
isolation property to make a run possible.

## Out of scope

* Any administrative-close transition, workaround, or rollback.
* Any mutation of `002-C` or of any finalized non-member record.
* Any local, credentialed, or network-enabled execution of the external binary.
* `173.012-T`, archived as out of scope with provenance.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | CI cannot deny egress after acquisition | `183-S` answers this before tasks are harvested; if it cannot, the unit reduces to documentation and escalation rather than running without the property. |
| R2 | The reduced unit is perceived as abandoning the problem | The problem is upstream. The escalation with evidence is the actionable output; a local workaround would be a false resolution. |
| R3 | Operators treat the interim path as agent-executable | It is stated as operator-only in the documentation, and no agent procedure references it. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Is a run that could not be isolated a conformance failure? | No — it is `ISOLATION_REFUSED`, and the run does not start. Reporting an isolation failure as a conformance verdict would attribute a harness defect to the binary under test. |
| H2 | Has the sandbox's refusal path ever been observed? | It must be, before activation. VERIFY requires each precondition violated in turn — credentials present, egress open, repository writable — and the refusal observed. An untested refusal path is an untested sandbox. |
| H3 | Could the isolation properties be relaxed to make a run possible? | No. If `183-S` finds a property unachievable, the unit reduces to documentation and escalation. Relaxing a property to obtain a result would make the result meaningless. |
| H4 | Does removing the administrative-close transition leave `002-C` in a false state? | No. `002-C` stays blocked, which is the truthful record of an unsupported transition. Closing it administratively would make the record false, which is the opposite of the fix. |
| H5 | Is a non-conforming observation a failure of this unit? | No. The evidence is the deliverable. `CONFORMANCE_OBSERVED` records what happened; the upstream escalation carries it. |
| H6 | Could the operator-only interim path be automated later? | Not from any agent surface, and no agent procedure references it. It is operator action outside the agent boundary by design, not by omission. |
| H7 | Why archive `173.012-T` rather than rewrite it? | It mutates `002-C`, a finalized non-member of this shipment. Rewriting it would retain a task that reaches outside its shipment's membership; archiving it with provenance records the decision truthfully. |

### Blast radius

A CI definition executing a third-party binary, plus workspace documentation.
The binary never runs locally, never with credentials, and never against a
writable repository, so the blast radius is bounded by the container.

### Rollback

PREPARE is inert. The ACTIVATE commit reverts as a unit, removing the CI
definition and the documentation together. No workspace record transitions, so
no rollback of state is required — the deliberate consequence of removing the
administrative transition.

### Verification floor

Every isolation property from `183-S` carries a verdict with a cited mechanism
and an observation. A property asserted from documentation alone is not
verified.
