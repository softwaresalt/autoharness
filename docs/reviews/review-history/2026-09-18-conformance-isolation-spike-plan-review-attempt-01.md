---
title: "Plan review attempt 01 — Conformance isolation spike (S2)"
description: "Immutable per-attempt plan-review artifact recording the first independent review of docs/plans/2026-09-18-conformance-isolation-spike-plan.md at revision 1, against reviewed content HEAD db39553a. Gate result FAIL; decision BLOCKED on one P0, one P1, two P2 and one P3 deduplicated finding. The P0 is that the plan's declared pass state ISOLATION_CHARACTERIZED is unreachable under its own task decomposition: property I1, no credentials of any kind in the job environment, is assigned to no determining task, so the spike terminates in its own fail state by construction. The P1 is the same structural gap on I7, whose redirect rule must be derived from observed acquisition behaviour that no task observes. Dispatch ran in single-agent declared degradation with all seven personas covered inline; engram indexed retrieval was circuit-open and intercom unavailable. No remediation was performed and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-01.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 1
attempt_range: "01"
attempt_conformance: conforming
review_terminal: false
verdict_manifest: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
supersedes: null
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_id: conformance-isolation-spike
reviewed_revision: 1
reviewed_content_head: db39553a
reviewed_content_state: committed
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 7F9CB5E9
feature_id: 177-F
shipment_id: 183-S
unit_role: precursor-spike
dag_role: root
external_tracker: 002-C
external_tracker_state: blocked-outside-shipment
review_cycle: 1
dispatch_mode: single-agent-declared-degradation
anchor_route: absent
anchor_route_note: "No anchor_review key exists in .autoharness/config.yaml model_routing, so no cross-model anchor was dispatchable. The cross-model rubrics ran under same-model declared degradation. This is recorded, not compensated for."
degraded_capabilities:
  - capability: reviewer-subagent-dispatch
    state: degraded
    note: "TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass. Every selected persona was applied inline with its own finding list, per the Persona Rubric Adapter."
  - capability: agent-engram
    state: circuit-open
    note: "Indexed retrieval circuit open on a known content_record/chunk_id fault; not retried per operator instruction. All evidence below comes from bounded direct exact-path reads, git plumbing, and read-only backlogit SQL."
  - capability: agent-intercom
    state: unavailable
    note: "No operator broadcast performed; visibility is local-only. No operator choice-presentation step was skipped, because this review presents no choice."
gate_result: FAIL
decision: BLOCKED
verdict_at_entry: REMEDIATED-PENDING-REVIEW
verdict_at_entry_plan_revision: 1
remediation_authorization: none-this-cycle
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 1
p1_open: 1
p2_open: 2
p3_open: 1
hardening_required: true
hardening_present: true
hardening_sufficient: false
persona_coverage:
  - persona: constitution
    status: complete
    mode: inline
    findings: A1
  - persona: python
    status: complete
    mode: inline
    findings: B2
  - persona: scope-boundary
    status: complete
    mode: inline
    findings: B2, C1
  - persona: learnings
    status: complete
    mode: inline
    findings: A1
  - persona: architecture
    status: complete
    mode: inline-same-model
    findings: A1, A2, C1
  - persona: agent-native-parity
    status: complete
    mode: inline-same-model
    trigger: "Plan governs a CI surface an agent must interpret; assessed for agent-readable verdict shape."
    findings: none
  - persona: security-lens
    status: complete
    mode: inline-same-model
    trigger: "Plan governs execution of an untrusted external binary, credential exposure, network egress, and a verify-to-execute trust boundary."
    findings: A1, A2
tags:
  - "plan-review"
  - "spike"
  - "ci-isolation"
  - "supply-chain"
  - "safe-close"
  - "portfolio-2026-09-18"
---

# Plan review attempt 01 — Conformance isolation spike (S2)

This artifact records **one thing**: an independent reviewer's verdict on plan
revision 1 as it stands at content HEAD `db39553a`. It has no Part 2. No
remediation followed it, no finding below is closed, and Stage asserts no
`PASS`.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` |
| Reviewed revision | 1 |
| Reviewed content HEAD | `db39553a` (committed) |
| Verdict at entry | `REMEDIATED-PENDING-REVIEW` at plan revision 1 |
| Covering feature / shipment | `177-F` / `183-S` |
| Unit role | precursor spike, DAG root (`183-S` has no incoming dependency edge) |
| Governing decision | 2026-09-18 shared-execution-architecture, revision 1 |
| Dispatch mode | `single-agent-declared-degradation` |
| Gate result | **FAIL** |
| Decision | **BLOCKED** |

```text
dispatch_mode: single-agent-declared-degradation
decision: FAIL
```

## Dispatch and coverage

Reviewer subagent dispatch was unavailable, so all seven personas were applied
**inline**, each with its own finding list so coverage is auditable. No persona
was skipped. Cross-model personas ran under same-model declared degradation
because `.autoharness/config.yaml` declares no `anchor_review` route.

Security Lens was triggered with the strongest warrant in this portfolio: the
unit governs execution of an untrusted third-party binary, credential exposure,
network egress control, and a verify-to-execute trust boundary. Agent-Native
Parity was triggered on the weaker ground that a CI verdict must be readable by
the consuming agent, and returned no finding.

Indexed retrieval was circuit-open and was not retried. Every claim below cites
an exact path, a backlogit record, or a `git` fact.

## What the plan gets right

Recorded so the P0 is not read as a rejection of the unit's premise.

* The attempt-08 citations are **exact**. Against the safe-close attempt-08
  artifact, `B3` is "the provisioned external binary has no OS sandbox and no
  race-resistant handle containment", `B4` is "the authoring platform cannot
  execute the authoritative baseline", and `B6` is "the no-redirect rule is
  unsatisfiable as stated". All three are characterized correctly.
* The plan **has** the composed-state check its sibling `182-S` lacks, and it
  states the hard rule that "A partially-classified result is a **fail**, not a
  partial pass." That rule is correct, and it is also what convicts the plan —
  see A1.
* The `002-C` boundary is stated exactly as D5 requires: it "stays `blocked`,
  outside every manifest, with no dependency edge in either direction", and
  administrative-close transitions are refused outright. The executable records
  agree: `item_deps` carries no edge in either direction between `183-S` and
  `002-C`.
* The floor is declared and is one-directional — "the spike determines whether
  the unit rises above it, never whether it drops below it." That is the right
  shape for a research gate.
* `requires_plan_hardening: true` is correctly declared, and a hardening
  section is present. Its rationale is the one this reviewer applied against
  the sibling spike in A3 of the `182-S` attempt-01 artifact.
* Task-to-record correspondence **holds**: `177.001-T` (S/medium),
  `177.002-T` (S/high), `177.003-T` (XS/low) in shipment `183-S` match the
  plan's task table on both axes.

## P0 findings (1)

**A1 — the declared pass state is unreachable under the plan's own task
decomposition: `I1` has no determining task.**

The plan states that each of `I1`–`I7` "is classified **ACHIEVABLE** or **NOT
ACHIEVABLE** by this spike. None is assumed." Its composed-state check defines
the fail state `ISOLATION_UNDETERMINED` as "any property left unclassified",
and adds: "A partially-classified result is a **fail**, not a partial pass."

Now read the task table against the property table:

| Task | Properties it determines |
|---|---|
| `177.001-T` | `I2` egress denial, `I3` repository absence/read-only |
| `177.002-T` | `I4` disposable mounts, `I5` TOCTOU-resistant handle, `I6` hardlink/symlink resistance |
| `177.003-T` | authors the findings artifact; derives the `I7` redirect rule |

**`I1` — "No credentials of any kind in the job environment" — appears in no
task.** Verified against the executable records as well as the plan text: the
three tasks in shipment `183-S` are titled "determine runner egress-denial and
repository-absence capabilities", "determine disposable-mount and
TOCTOU-resistant handle containment options", and "author the isolation
findings artifact stating achievable and unachievable properties". No task
determines credential absence.

`177.003-T` cannot absorb it. It is an `XS`/low authoring task, and the plan
forecloses the escape route itself: risk `R3` requires that "Each verdict must
cite the mechanism and the observation that demonstrated it, not a
documentation reference alone", and hardening answer `H2` repeats it —
"Documentation alone yields `ISOLATION_UNDETERMINED`." An `I1` verdict produced
during authoring would rest on assertion, which the plan has already ruled
insufficient.

The consequence is not a gap but a contradiction: **executed exactly as
decomposed, this spike terminates in `ISOLATION_UNDETERMINED`.** Its pass state
is unreachable by any legitimate execution.

This is the defect class recorded in
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`
— "A gate no legitimate state could satisfy, assembled from clauses that were
each correct." Every clause here is individually right: the property table is
right, the fail-state rule is right, the task table is a reasonable
decomposition. The defect exists only at their seam, which is precisely why the
plan's own hardening pass missed it: `H1`–`H4` interrogate scope creep,
evidence quality and partial results, and none asks *does every declared
property have a task that determines it*.

It is also the defect D6 exists to catch before harvest — "Pass state | Exactly
one, and demonstrably **reachable** by a legitimate execution."

Graded **P0** rather than P1 on two independent grounds. First, the contract is
broken rather than incomplete: the unit cannot succeed as specified, which is
impossible scope. Second, the property left undetermined is the
security-critical one. `I1` is what decides whether an untrusted binary shares
an environment with a readable token; the plan's own justification for it is "a
token in the environment is a token it can read". Shipping `181-S` on an
isolation characterization that silently omitted credential absence is the
unsafe outcome this entire unit was created to prevent.

*Recommendation.* Assign `I1` to a determining task — most naturally
`177.001-T`, which already inspects the job environment for `I2`/`I3` — and add
a hardening question of the form "does every declared property have a task that
determines it, and does every task's output name the property it closes?" so
the coverage check is structural rather than incidental.

*Personas:* Architecture Strategist; Security Lens Reviewer; Learnings
Researcher; Constitution Reviewer (Principle III, Workspace Isolation and
Security Boundaries).

## P1 findings (1)

**A2 — `I7` requires an observation that no task performs.**

`I7` is "A correct redirect rule derived from **observed acquisition
behaviour**", and the plan is explicit about why it exists: attempt-08 `B6`
found the rule "a redirect off `github.com` halts" unsatisfiable, "because
GitHub release-asset downloads normally redirect to an object-storage host. The
transport rule must be re-derived from what acquisition actually does."

No task performs an acquisition. `177.001-T` determines egress denial and
repository state; `177.002-T` determines mounts and handle containment; neither
downloads a release asset and neither records a redirect chain. `I7` is
assigned to `177.003-T`, the authoring task.

So the replacement rule would be derived the same way the rule it replaces was
derived — from assumption about what the acquisition does, rather than from
observation of what it did. That reproduces attempt-08 `B6` under a new
sentence.

There is a second-order consequence worth stating. `I2` is "egress denied
**after** acquisition completes", so acquisition and egress denial are two
phases of one job. A task that establishes `I2` without ever performing the
acquisition it is defined relative to has not fully characterized `I2` either.

Same root cause as A1 — a property assigned to the authoring task rather than
to a determining one — and counted separately because it is independently
actionable and carries its own attempt-08 lineage.

*Recommendation.* Add an acquisition observation to `177.001-T`: perform one
release-asset download in the target runner, record the observed redirect
chain and terminal host, and derive `I7` from that record. Then `177.003-T`
transcribes a rule rather than inventing one.

*Personas:* Architecture Strategist; Security Lens Reviewer.

## P2 findings (2)

**B1 — the `verdict` key carries a value from the disposition enum.**

Identical in kind and grading to `B1` on `182-S`, recorded once per plan
surface. Plan frontmatter and the pre-review manifest set
`verdict: REMEDIATED-PENDING-REVIEW` while `verdict_note` concedes no
remediation occurred; the attempt-08 manifest for `177-S` already records that
`REMEDIATED-PENDING-REVIEW` "is a `disposition`, never a `verdict`".

Graded P2 on the narrow ground that the manifest-reading consumer does not yet
exist — per F7, today's `harvest` reads an inline marker in the plan and never
opens the manifest — so present blast radius is record integrity, not admission
control. It becomes P1 when `186-S` activates SM-2.

*Personas:* Constitution Reviewer; Architecture Strategist; Scope Boundary
Auditor.

**B2 — `177.002-T` carries `complexity: high` with neither a split nor a
declared de-risking rationale.**

Confirmed in the records: `177.002-T` is `size: S`, `complexity: high`.

Stage's harvest contract is explicit that the two axes are independent and that
"`complexity: high` forces a split or de-risking step (spike, further
decomposition, or additional deliberation) **regardless of `size`**." The plan
records neither.

The bundling is also substantively questionable. `I4` (disposable mounts) is an
infrastructure-capability question answered by reading runner behaviour.
`I5`/`I6` (TOCTOU-resistant handle, hardlink/symlink substitution resistance)
are adversarial containment questions answered by attempting substitution
against a handle. Those are different investigations with different evidence
shapes, sharing a task only because they are all "containment".

The obvious counter — that a spike *is* the de-risking step — is partly fair,
and is why this is P2 rather than P1. It does not fully answer the rule: the
sibling task `177.001-T` carries two determinations at `medium`, this one
carries three at `high`, and the plan explains neither the difference nor why
the gate is satisfied.

*Recommendation.* Either split `I4` from `I5`/`I6`, or record in the plan why
`complexity: high` is accepted without a split — the de-risking argument,
stated, is an acceptable answer; the gate objects to it being unstated.

*Personas:* Scope Boundary Auditor; Python Reviewer.

## P3 findings (1)

**C1 — the composed-state check names producer and consumer in prose rather
than by path.**

Producer is "This spike's findings artifact" and Consumer is "The reduced
`181-S` plan". Both referents are real and both resolve — the Deliverable
section gives the producer's exact path, and
`docs/plans/2026-09-18-safe-close-conformance-plan.md` exists — so this is not
a broken reference and is not graded higher.

D6 nonetheless asks for "A named, **existing** artifact" in each row, and every
SM table in the governing decision does name them exactly (for instance
"Producer: `autoharness op harness p004-gate` (created in `176-S`, on `P2`)").
Writing the paths into the table makes the rows mechanically checkable instead
of requiring a reader to resolve prose. Advisory.

*Personas:* Architecture Strategist; Scope Boundary Auditor.

## Runtime verification and operational closure

Called out explicitly, as the gate requires.

The unit produces a document and declares "Activation commit | None — the spike
activates nothing", so there is no runtime surface to verify and no closure
evidence to produce **in this unit**. That is correct for a spike.

One asymmetry is worth recording without grading it: the plan's own hardening
answer `H1` concedes "Can a spike that executes an external binary be unsafe in
itself? Yes", and resolves it by asserting the spike "runs no conformance
workload itself". The `I5`/`I6` determinations in `177.002-T` are nonetheless
hands-on containment probes against a real handle. The plan's position is
defensible — probing a handle is not executing the untrusted binary — but it is
the boundary that A1's missing `I1` determination would otherwise have helped
police, and it is recorded here for the remediation cycle's attention rather
than as a separate finding.

## Disposition

**No remediation.** `remediation_revision` is `null`, `disposition` is `null`,
and the governing revision remains 1 — the revision reviewed and found
BLOCKED.

This plan is **not harvest-ready and not Ship-ready**. No backlog record,
source file, test, template, CI definition or configuration was changed on the
strength of this review. Closing A1 and A2 requires a Stage remediation cycle
producing revision 2 and an independent attempt 02.
