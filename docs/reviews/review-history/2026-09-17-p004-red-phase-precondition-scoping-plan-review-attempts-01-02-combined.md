---
review_artifact_role: history
review_artifact_immutable: true
attempt_range: "01-02"
attempt_conformance: non-conforming-combined
preservation_note: "PRESERVED VERBATIM. This file records review cycles 1 and 2 as a single mutable document. That form is the exact defect docs/plans/2026-09-17-single-governing-plan-contract-plan.md exists to correct, and it is retained unedited as evidence rather than retroactively split into two artifacts that were never independently authored. Body text below is unchanged from commit 1b6a312d. Only these classification keys were added, by the remediation-cycle-1 classify-never-delete action. Superseded by attempt-03; see the latest-verdict manifest named in verdict_manifest."
verdict_manifest: docs/reviews/2026-09-17-p004-red-phase-precondition-scoping-plan-review.md
title: "Plan review — P-004 red-phase precondition scoping"
description: "Multi-persona plan review of docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md, gating harvest. Inline persona coverage under declared subagent-dispatch degradation. Gate decision: PASS, 0 P0 / 0 P1 open."
doc_type: review
source: docs/reviews/2026-09-17-p004-red-phase-precondition-scoping-plan-review.md
date: 2026-09-17
plan_path: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
plan_revision: 2
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 1
source_stash_id: 76EBDE6D
review_cycle: 2
review_cycles_remaining: 1
dispatch_mode: declared-degradation
decision: PASS
p0_open: 0
p1_open: 0
tags:
  - "plan-review"
  - "policy"
  - "p-004"
---

# Plan review — P-004 red-phase precondition scoping

## Dispatch mode

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent
persona pass`. Cross-model dispatch unavailable in this CLI session; the anchor
review route could not be dispatched. Every selected persona rubric was applied
inline with a separate finding list, so coverage is complete and auditable. No
persona was skipped.

Personas applied: Constitution Reviewer, Python Reviewer, Scope Boundary
Auditor, Learnings Researcher (always-on); Architecture Strategist
(cross-model, inline). Security Lens Reviewer and Agent-Native Parity Reviewer
**not triggered** — the plan touches no auth/authz, API surface, secrets store,
external trust boundary, or MCP/agent-parity surface.

Plan hardening: the plan declares `requires_plan_hardening: "no"`. Confirmed
correct — single policy clause plus one schema field, one template family, no
schema-distribution or CLI-distribution blast radius. `plan-harden` not invoked.

## Final Reviewed Contract

The reviewed contract is: replace P-004's whole-suite every-function-red
precondition with a precondition over a **declared harness set** carrying two
disjoint classes (`expected_red`, `expected_green_characterization`), addressed
by explicit test ID, asserted by **exact set equality in both directions**, with
seven distinguishable fail-closed tokens. The default-branch whole-suite CI gate
is unmodified and must continue to exit zero. Six tasks; T3 blocks on T2 for
template/mirror atomicity.

## Findings

### Cycle 1 — findings raised and remediated in place

| ID | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| F1 | Scope Boundary Auditor | **P0** | Cycle-1 draft scoped the precondition to "newly authored test functions", which the source stash entry itself identifies as still obstructed by characterization cases. | **Resolved.** Plan now adopts the declared-set disposition and explicitly rejects the newly-authored framing **on its own terms**, naming why (a newly authored characterization test is both newly authored and green by construction). |
| F2 | Constitution Reviewer | **P0** | Cycle-1 draft allowed a subset check ("every declared red test failed"), which passes vacuously when collection silently drops tests. | **Resolved.** Predicate is now exact set equality in both directions, with `P004_MISSING_OBSERVATION` and `P004_UNDECLARED_OBSERVATION` as distinct tokens. |
| F3 | Python Reviewer | **P1** | Selector was specified by marker/naming convention, which re-introduces implicit discovery. | **Resolved.** Selector is explicit test-ID addressing; the plan states the rationale (confirmed set == declared set). |
| F4 | Architecture Strategist | **P1** | No constraint prevented an empty `expected_red` set, making the gate vacuously satisfiable. | **Resolved.** `P004_EMPTY_RED_SET` token added; non-empty red is a schema constraint (T1). |
| F5 | Learnings Researcher | **P1** | Plan did not address template/installed-mirror drift, the class recorded in `docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`. | **Resolved.** T2/T3 split with an explicit `blocks` edge plus a byte-identity check promoted into Verification as a gate. |
| F6 | Scope Boundary Auditor | P2 | Disjointness of the two declared sets was implied, not required. | **Resolved.** `P004_SET_OVERLAP` token added. |
| F7 | Constitution Reviewer | P2 | Risk table did not address a red test authored trivially to satisfy the gate. | **Resolved.** R1 added; marker review at the existing operator approval gate is the control. |

### Cycle 2 — verification pass

No new P0 or P1. Two P3 observations recorded and **accepted without change**:

* **P3-1** (Python Reviewer): the branch-name-style validation vocabulary in the
  companion branch-resolution plan and the token vocabulary here are
  independently specified. Accepted: different contract surfaces, deliberately
  not coupled.
* **P3-2** (Architecture Strategist): the harness-manifest schema change could
  in principle be shared with a future shipment-scoped test selector. Accepted
  as YAGNI; no speculative generalization.

## Persona coverage

| Persona | Findings | Open P0/P1 |
|---|---|---|
| Constitution Reviewer | F2, F7 | 0 |
| Python Reviewer | F3, P3-1 | 0 |
| Scope Boundary Auditor | F1, F6 | 0 |
| Learnings Researcher | F5 | 0 |
| Architecture Strategist | F4, P3-2 | 0 |

## Gate decision

**PASS.** 0 P0 open, 0 P1 open. Cleared for harvest.

Explicitly verified before passing: the plan adds no command to CI, removes
none, authorizes no bypass or waiver for P-004, and does not modify `168-S`'s
manifest.
