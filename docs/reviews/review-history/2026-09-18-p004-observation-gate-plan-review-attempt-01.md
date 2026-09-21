---
title: "Plan review attempt 01 - P004-OBSERVATION-GATE (176-S)"
description: "Immutable per-attempt plan-review artifact recording the FIRST independent review of docs/plans/2026-09-18-p004-observation-gate-plan.md at revision 6. This plan had never been independently reviewed: its manifest stood in the legitimate pre-review state with verdict REMEDIATED-PENDING-REVIEW, a Stage-authored readiness marker and not a verdict. GATE RESULT FAIL/BLOCK at P0 1 / P1 8 / P2 1. The central defect is that the plan reduces its own scope in prose while the live carriers it governs - feature 168-F, twelve 168.* tasks and the 176-S shipment manifest - still instruct an executor to build the superseded architecture. Finding IDs use the O-prefix namespace reserved for this plan and do not collide with the S-prefix namespace of the ship-harness-lifecycle-foundation plan."
doc_type: review
source: docs/reviews/review-history/2026-09-18-p004-observation-gate-plan-review-attempt-01.md
date: 2026-09-20
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 1
attempt_range: "01"
attempt_conformance: conforming
review_terminal: false
terminal_designation: not-terminal-remediation-authorized
terminal_disposition: FAIL-BLOCKING-P0-AND-P1
terminal_note: "Attempt 01 CONSUMES attempt number 1 and is NOT terminal. The operator directive that dispatched it explicitly authorizes continued remediation after recording."
verdict_manifest: docs/reviews/2026-09-18-p004-observation-gate-plan-review.md
supersedes: null
predecessor_artifact: null
predecessor_note: "No predecessor. This is the first independent attempt against this plan. The superseded plan docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md carried its own eight-attempt history under a different plan_id; those attempts judged a different document and confer nothing here."
plan_path: docs/plans/2026-09-18-p004-observation-gate-plan.md
plan_id: p004-observation-gate
reviewed_revision: 6
reviewed_content_head: b11d6555
reviewed_content_state: committed
reviewed_branch: chore/stage-176-s-workflow-defects
plan_mutated_by_this_attempt: false
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 6
feature_id: 168-F
shipment_id: 176-S
finding_id_namespace: "O-prefix, reserved for p004-observation-gate; distinct from the S-prefix namespace of ship-harness-lifecycle-foundation"
review_cycle: 1
dispatch_mode: multi-agent
degraded_capabilities: []
security_lens_triggered: false
security_lens_note: "No Security Lens trigger fired. O5 (shell-free handling of the PYTHONPATH=src prefix) touches command construction and would become a security finding the moment a shell is introduced; at revision 6 no executor exists, so it is recorded on the PYTHON and ARCHITECTURE axes as a correctness and specification gap."
gate_result: FAIL
decision: BLOCK
verdict_is_pass: false
verdict_at_entry: REMEDIATED-PENDING-REVIEW
verdict_at_entry_disposition: PENDING-FIRST-INDEPENDENT-REVIEW
verdict_at_entry_is_pass: false
verdict_at_entry_note: "REMEDIATED-PENDING-REVIEW is a Stage-authored READINESS marker, never a verdict. The manifest stood in the legitimate pre-review state with latest_attempt null and an empty attempt roster."
verdict_at_entry_plan_revision: 6
verdict_at_entry_publication_eligible: false
remediation_authorization: authorized-by-fresh-operator-directive-after-recording
remediation_performed: false
remediation_cycle_proposed: true
disposition: FAIL-BLOCKING-P0-AND-P1
p0_open: 1
p1_open: 8
p2_open: 1
p3_open: 0
open_findings: [O1, O2, O3, O4, O5, O6, O7, O8, O9, O10]
blocking_findings: [O1, O2, O3, O4, O5, O6, O7, O8, O9]
closed_predecessor_findings: []
carried_predecessor_findings: []
findings_raised_at_this_attempt: [O1, O2, O3, O4, O5, O6, O7, O8, O9, O10]
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_note: "requires_plan_hardening is declared true and a hardening section is present, but it does not reach the defects recorded here: it hardens the activation commit arithmetic and the checksum verification contract while leaving the gate's own API, result model, evidence model, marker enforcement and safety mode unspecified."
personas_applied:
  - constitution
  - python
  - scope-boundary
  - learnings
  - architecture
  - agent-native-parity
personas_not_applied:
  - security-lens
tags:
  - "plan-review"
  - "attempt"
  - "fail"
  - "revision-6"
  - "p004"
  - "portfolio-2026-09-18"
---

# Plan review attempt 01 - P004-OBSERVATION-GATE (176-S)

## Reviewed subject

`docs/plans/2026-09-18-p004-observation-gate-plan.md` at **revision 6**, at
committed base `b11d6555` on branch `chore/stage-176-s-workflow-defects`.

This is the **first independent review this plan has ever received**. Its
manifest stood at `latest_attempt: null` with an empty roster and
`verdict: REMEDIATED-PENDING-REVIEW` - a Stage-authored readiness marker, not a
verdict, and correctly documented as such in the manifest body.

The plan was **not mutated by this attempt**.

## Findings

Findings are merged and de-duplicated conservatively. The `O` prefix is reserved
for this plan and does not collide with the `S` prefix used by the
ship-harness-lifecycle-foundation plan.

### O1 - the live carriers still execute the superseded architecture (P0, BLOCKING)

Revision 1 reduced this unit's scope: bootstrap, schema, storage lifecycle,
identity and MCP parity were declared to have moved to the foundations that own
them. The plan states this reduction in **prose**.

The backlog did not move with it. Feature `168-F`, the twelve `168.*` tasks, and
the `176-S` shipment manifest that carries all thirteen are **live, queued and
unchanged**. They still instruct an executor to build the architecture the plan
says it no longer owns.

A shipment manifest is an **executable instruction set**, not commentary. At
claim time Ship reads `176-S` and its members, not this plan's Reduction
section. A prose deferral in a governing document cannot deauthorize work that
a live task record still specifies. Until the carriers are reconciled, the
reduction is an intention rather than a fact, and the unit will build the
superseded design if it is claimed.

This is a `P0` because it is not a documentation inconsistency - it is a live
divergence between what the plan authorizes and what the backlog will execute.

### O2 - `191-S` is circular, has no governing plan, and has been overtaken by events (P1, BLOCKING)

Revision 6 adds `191-S` to `depends_on_shipments` and attributes actor
conformance to it. Three problems compound.

1. **`191-S` has no governing plan of its own.** Every other shipment in this
   portfolio is governed by a plan that has been or will be independently
   reviewed. `191-S` was created directly from a review finding, and its
   contract lives only in backlog prose. Nothing gates its design.
2. **It is circular.** `191-S` writes Python under `src/` and `tests/`, so it is
   subject to `P-002` and `P-004` - the very gate this plan builds and the
   lifecycle `187-S` builds. It must pass gates that do not yet work.
3. **It has been overtaken by events.** The substantive actor correction was
   performed directly on this branch by Ship review-remediation commits
   `1cb0dc81` and `b8ac632a`: the installed actor now runs the canonical
   `PYTHONPATH=src python -m unittest discover -s tests`, the manifest carries
   `variables_used.UNIMPLEMENTED_MARKER`, and manifest parity holds with the
   canonical suite at **2358 passed / 0 failed / 54 skipped**.

**This finding records that fact and does not act on it.** The carriers are not
remediated in this turn. But a dependency declared on a shipment whose work has
already landed elsewhere is a stale gate, and any future remediation must
establish what, if anything, `191-S` still owns before leaving it in the chain.

### O3 - expected-green characterization conflicts with live all-generated-tests-red policy (P1, BLOCKING)

The plan characterizes part of the observed outcome set as expected-green. Live
policy requires that **all generated tests be red** in the red phase, and the
harness-architect guardrail prose strengthened by `1cb0dc81` explicitly rejects
passes as red-phase evidence.

A gate that admits an expected-green outcome over the declared harness set is
adjudicating against a different contract from the one the actor now enforces.
One of the two must move, and the plan does not acknowledge the conflict.

### O4 - no authoritative producer for test IDs, markers or outcome declarations (P1, BLOCKING)

The gate asserts **exact set equality** between declared and observed outcomes
over the declared harness set. That requires a declared set with stable
identity. The plan never names what produces it.

Unspecified: what constitutes a test identifier; who emits the declaration;
where it is stored; how a declared identifier is correlated with an observed
one; and what happens when the runner reports an identifier that no declaration
mentions. Set equality is meaningless until both sets have a defined producer
and a shared identity scheme.

### O5 - the canonical commands conflict with the classifier, and `PYTHONPATH=src` has no shell-free handling (P1, BLOCKING)

Two symptoms of one defect - the plan treats a command string as if it were
directly executable.

The canonical test command is `PYTHONPATH=src python -m unittest discover -s
tests`. That string is **not an argv vector**. `PYTHONPATH=src` is an
environment assignment that only a shell interprets; passed to a fixed-argv exec
primitive it becomes a nonexistent program name.

This unit consumes the **fixed-argv exec primitive** from `185-S`, precisely to
avoid a shell. The plan therefore requires a specified split between environment
overlay and argv - which variables are lifted into the child environment, how,
and with what precedence - and provides none.

Relatedly, the declared-set classifier's treatment of this command is
inconsistent with the exact-command requirement: the command is quoted as a
literal to be run verbatim, while the classifier needs it decomposed. Both
cannot hold.

### O6 - the per-test expected marker is not enforced (P1, BLOCKING)

`P-004` requires expected failure markers **for every test function**. The plan
records the requirement but specifies no enforcement: no per-test marker
extraction, no correlation between marker and test identifier, and no failure
mode for a test that fails without its marker or carries a marker while passing.

Without enforcement the gate cannot distinguish a properly red suite from a
suite that failed for unrelated reasons - which is the exact class of false
evidence the actor's guardrail prose was strengthened to reject.

### O7 - no typed API, result, evidence or digest, and no registered operation (P1, BLOCKING)

The gate has no specified Python surface: no `red_phase` entry point signature,
no typed result model, no evidence model, no digest over its inputs, and no
registered CLI or MCP operation.

The consequence is an agent-native parity failure. Ship's prose would instruct
an agent to consult a gate that exposes no callable boundary and no machine
-readable result. The instruction would be **unwired** - it would read as a
requirement while enforcing nothing, which is the same defect class recorded as
`S15` against the lifecycle plan.

### O8 - resolver non-ready and invalid states are not exhaustively preserved (P1, BLOCKING)

The lifecycle resolver distinguishes `HARNESS_READY`, `NO_HARNESS` and
`UNRESOLVED`, with `NO_HARNESS` terminal and `UNRESOLVED` a halt. Revision 6
binds this gate to direct resolver consumption but preserves only the ready and
`NO_HARNESS` paths in its own adjudication.

`UNRESOLVED`, invalid input and race-detected states have no defined mapping
here. A state that the producer treats as a halt must not be silently collapsed
into `NO_OBSERVATION` by the consumer, because those carry different
authorizations downstream.

The freshness and no-bypass rules have the same gap: revision 6 correctly states
that recomputation happens at adjudication and that no caller token authorizes,
but specifies no tests that would fail if a future implementation cached a
result or honoured a supplied token.

### O9 - rollback lacks fresh live approval, and no safety mode is defined (P1, BLOCKING)

The lifecycle plan was corrected at revision 9 to require a fresh, SHA-bound,
revalidated operator approval before `git revert`, under this workspace's own
`P-007` `G1`-`G9` precedent. **This plan was not correspondingly corrected.** Its
rollback still prescribes a revert without that gate.

Separately, no safety mode is defined for the gate itself: there is no stated
behaviour for dark, AFK or unattended operation, where an approval channel is
unreachable. Absence of a channel must be a fail-closed halt, and the plan does
not say so.

### O10 - decision and carrier ownership and revision pointers are stale (P2)

`decision_revision` and several ownership references do not match the current
decision revision or the current owners. The row corrected at revision 6 fixed
the actor attribution; adjacent pointers were not swept, so the plan cites a
mixture of current and superseded ownership.

## Persona coverage

| Persona | Applied | Principal contributions |
|---|---|---|
| Constitution | yes | `O1` (live carriers versus prose deferral), `O9` (approval-gate precedent not applied) |
| Python | yes | `O5` (`PYTHONPATH=src` is not argv), `O7` (typed API, result and digest) |
| Scope boundary | yes | `O1`, `O2` (`191-S` ownership and governing plan), `O10` |
| Learnings | yes | Cited `P-007` `G1`-`G9` as the settled approval pattern the lifecycle plan adopted and this one did not; cited the `188-S` self-bootstrap retirement as precedent for `O2`'s circularity |
| Architecture | yes | `O2`, `O4` (declared-set producer), `O8` (state preservation across the producer/consumer boundary) |
| Agent-Native Parity | yes | `O7` - Ship prose consulting a gate with no callable boundary or machine-readable result is unwired instruction |
| Security Lens | no | Not triggered; see `security_lens_note` |

`dispatch_mode: multi-agent`. No capability ran degraded at this attempt.

## Gate result

**FAIL / BLOCK**, under the standing decision rule (`P0` or `P1` present is
`FAIL`; `P2`-only is `ADVISORY`; `P3`-or-none is `PASS`).

Counts: `P0` 1, `P1` 8, `P2` 1, `P3` 0 - **10 findings open**, 9 blocking.

No finding was closed, lowered, deferred or waived. There were no predecessor
findings to carry.

`verdict: REMEDIATED-PENDING-REVIEW` is **replaced** by `FAIL`. `SM-2`
`HARVEST_ADMITTED` is **SHUT** and the plan is **not publication-eligible**. The
execution axis is separately shut: `176-S` depends on `185-S` and `187-S`, and
`187-S` is itself blocked.

## Authorization boundary

This attempt **consumed attempt number 1** and is **not terminal**. The operator
directive that dispatched it explicitly authorizes continued remediation after
recording.

This review **performed no remediation**: no plan, source, template, skill,
manifest, test, backlog carrier, stash entry, checkpoint or GitHub surface was
mutated. It wrote only this immutable artifact and the mutable verdict manifest.

## Scope statement

Verdicts are asserted by independent attempts and never by Stage. Stage authored
revision 6; Stage did not judge it. `O2`'s record of the external Ship
remediation commits is an observation of committed repository state, not a
closure of any finding in this plan and not an implication that `191-S` shipped -
it has not; it remains queued.
