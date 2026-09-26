---
title: "Plan review attempt 03 — Conformance isolation spike (S2)"
description: "Immutable per-attempt plan-review artifact recording the third and operator-designated terminal independent review of docs/plans/2026-09-18-conformance-isolation-spike-plan.md at revision 3, against reviewed content HEAD 4b4330b9. Gate result FAIL; decision BLOCKED on zero P0, one P1, one P2 and zero P3 deduplicated findings. All three attempt-02 findings are independently re-derived closed: the I1-before-probe ordering is now a real blocks edge from 177.004-T to both 177.005-T and 177.002-T in item_deps with every affected record stating it, the unreconciled ISOLATION_UNDETERMINED pair is replaced by a four-state model with per-state successor eligibility, and the 183-S manifest is in dependency order. The new P1 is that the ordering edge gates on task completion rather than on an achievable I1 verdict, so both explicitly reachable non-achievable outcomes satisfy the edge while the plan's blast radius, H7, H9, R8 and the 177.004-T record all assert that no acquisition or probe may run in a job whose credential absence is unverified. The P2 is that the determining tasks require hosted-runner jobs whose probe-workflow lifecycle is undeclared while the blast-radius and rollback sections state no tracked surface outside docs/spikes is touched. Dispatch ran in single-agent declared degradation with all seven personas covered inline; engram was circuit-open and not retried, intercom and graphtor-docs were unavailable. No remediation was performed and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-03.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 3
attempt_range: "03"
attempt_conformance: conforming
review_terminal: true
terminal_designation: operator-declared
terminal_disposition: TERMINAL-BLOCKED
verdict_manifest: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-02.md
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_id: conformance-isolation-spike
reviewed_revision: 3
reviewed_content_head: 4b4330b9
reviewed_content_state: committed
reviewed_branch: chore/stage-176-s-workflow-defects
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
review_cycle: 3
dispatch_mode: single-agent-declared-degradation
anchor_route: absent
anchor_route_note: "No anchor_review key exists in .autoharness/config.yaml model_routing, so no cross-model anchor was dispatchable. The cross-model rubrics ran under same-model declared degradation. This is recorded, not compensated for."
model_route_note: "Stage role route resolved from .autoharness/config.yaml model_routing.stage (claude-opus-5/anthropic/high), re-read fresh at session start per the Session-Start Dynamic Reload contract. The escalation route model_routing.escalation (gpt-5.6-sol/openai/high) is distinct from both the role route and tier3, so the same-route ESCALATION_DEGRADED guard does not fire. No escalation was triggered: no failure threshold was reached during this review."
degraded_capabilities:
  - capability: reviewer-subagent-dispatch
    state: degraded
    note: "TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent inline persona pass. Every selected persona was applied inline with its own finding list, per the Persona Rubric Adapter. Reviewer personas are leaf executors and spawned nothing."
  - capability: agent-engram
    state: circuit-open
    note: "Indexed retrieval circuit open per operator instruction; NOT retried this session. All evidence below comes from bounded direct exact-path reads, git plumbing, and read-only backlogit MCP reads and SQL over a freshly synced index (1430 artifacts)."
  - capability: agent-intercom
    state: unavailable
    note: "No operator broadcast performed; visibility is local-only. No operator choice-presentation step was skipped, because this review presents no choice."
  - capability: graphtor-docs
    state: unavailable
    note: "No graphtor-docs tool surface was exposed to this session. Documentation questions were answered by direct reads under docs/."
backlogit_index_state: "INDEX_SYNC_OK — 1430 artifacts indexed at session start"
gate_result: FAIL
decision: BLOCKED
verdict_at_entry: null
verdict_at_entry_disposition: REMEDIATED-PENDING-REVIEW
verdict_at_entry_plan_revision: 3
remediation_authorization: none-this-cycle
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 0
p1_open: 1
p2_open: 1
p3_open: 0
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_sufficiency_note: "The hardening pass gained H9, which asks whether the I1-before-probe ordering is enforced or only asserted, and answers 'Enforced' by citing the new blocks edges. The edges exist. The answer is nonetheless insufficient: a blocks edge enforces order, not outcome, and H9 does not ask what the edge guarantees when I1 resolves to anything other than ACHIEVABLE. That is finding K1 below. H3 and the rollback section are also silent on the probe-workflow lifecycle, which is finding K2."
attempt_02_findings_verified:
  - finding: "F1 — the remediation introduced a security-ordering claim that its own records deny"
    severity: P1
    state: closed
    evidence: "item_deps now carries 177.005-T depends-on 177.004-T and 177.002-T depends-on 177.004-T, both blocks. 177.002-T's and 177.005-T's records each open their ordering paragraph with 'BLOCKED BY 177.004-T, AND THAT ORDERING IS A SAFETY EDGE RATHER THAN A SCHEDULING PREFERENCE' and no longer claim independence from it; 177.001-T's record states it inherits the precedence transitively through 177.005-T, which item_deps confirms. The plan's Tasks section, R8 and H9 all state the edge rather than a preference. No record in 183-S now calls these tasks independent of 177.004-T."
  - finding: "F2 — blocks 181-S harvest and the floor stands either way are asserted as simultaneous consequences of the same state"
    severity: P2
    state: closed
    evidence: "The contradicting sentence pair is gone. The plan now defines four states with a Successor eligibility table stating per state what 181-S may harvest: everything under ISOLATION_CHARACTERIZED, floor-only under ISOLATION_FLOOR_ONLY, nothing under ISOLATION_UNDETERMINED or ISOLATION_NOT_OBSERVED. NOT DETERMINED - FLOOR INVOKED is the three-part fallback value the sibling spike's treatment implied, is explicitly not a pass, and is reproduced verbatim in 177.006-T."
  - finding: "F3 — the 183-S manifest items order is not dependency order"
    severity: P3
    state: closed
    evidence: "custom_fields.items now reads 177-F, 177.004-T, 177.005-T, 177.001-T, 177.002-T, 177.003-T, 177.006-T, matching item_deps, and the description opens with 'MANIFEST ORDER IS DEPENDENCY ORDER' and explains why 177.004-T leads."
persona_coverage:
  - persona: constitution
    status: complete
    mode: inline
    findings: K1
  - persona: python
    status: complete
    mode: inline
    findings: none
  - persona: scope-boundary
    status: complete
    mode: inline
    findings: K2
  - persona: learnings
    status: complete
    mode: inline
    findings: K1, K2
  - persona: architecture
    status: complete
    mode: inline-same-model
    findings: K1
  - persona: agent-native-parity
    status: complete
    mode: inline-same-model
    trigger: "Plan governs a CI surface whose four-state verdict token an agent must read and act on at 181-S harvest time."
    findings: none
  - persona: security-lens
    status: complete
    mode: inline-same-model
    trigger: "Plan governs credential exposure, network egress control, a verify-to-execute trust boundary, and acquisition of an untrusted external release binary onto a CI runner."
    findings: K1, K2
tags:
  - "plan-review"
  - "spike"
  - "ci-isolation"
  - "supply-chain"
  - "safe-close"
  - "portfolio-2026-09-18"
---

# Plan review attempt 03 — Conformance isolation spike (S2)

This artifact records **one thing**: an independent reviewer's verdict on plan
revision 3 as it stands at content HEAD `4b4330b9` on branch
`chore/stage-176-s-workflow-defects`. It has no Part 2. No remediation
followed it, and none was authorized.

Attempt 02's claimed closures were **independently re-derived from plan, task
and `item_deps` state**, not accepted from the remediation commit message or
the manifest narrative.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` |
| Reviewed revision | 3 |
| Reviewed content HEAD | `4b4330b9` (committed) |
| Verdict at entry | `null`, disposition `REMEDIATED-PENDING-REVIEW` at plan revision 3 |
| Covering feature / shipment | `177-F` / `183-S` |
| Unit role | precursor spike, DAG root |
| External tracker | `002-C`, `blocked`, outside every manifest |
| Governing decision | 2026-09-18 shared-execution-architecture, revision 1 |
| Dispatch mode | `single-agent-declared-degradation` |
| Terminal | yes — operator-declared terminal attempt |
| Gate result | **FAIL** |
| Decision | **BLOCKED** |

```text
dispatch_mode: single-agent-declared-degradation
decision: BLOCKED
```

## Dispatch and coverage

Reviewer subagent dispatch was unavailable, so all seven personas were applied
**inline**, each with its own finding list so coverage is auditable. No persona
was skipped, and no persona spawned a subagent — reviewer personas are leaf
executors in this workflow. Cross-model personas ran under same-model declared
degradation because `.autoharness/config.yaml` declares no `anchor_review`
route.

Both conditional personas were **triggered and ran**. Agent-Native Parity,
because an agent must read this unit's four-state verdict token and derive
`181-S`'s harvest authority from it. Security Lens, because the unit governs
credential exposure, egress control, a verify-to-execute trust boundary and
the acquisition of an untrusted external release binary onto a CI runner.

Engram indexed retrieval was circuit-open and was **not retried** per operator
instruction. Intercom and graphtor-docs were unavailable, so visibility is
local-only and documentation questions were answered by direct reads. Every
claim below cites an exact path, a backlogit record, or a `git` fact, taken
against a freshly synced index.

## Independent verification of attempt-02 closures

**F1 (P1) — the unenforced I1-before-probe ordering. Closed, at the layer it
was raised on.**

`item_deps` now carries, verified by direct read:

```text
177.005-T → depends on → 177.004-T  (blocks)
177.002-T → depends on → 177.004-T  (blocks)
177.001-T → depends on → 177.005-T  (blocks)
177.003-T → depends on → 177.001-T, 177.002-T, 177.004-T, 177.005-T
177.006-T → depends on → 177.003-T
```

Every one of the five denial sites attempt 02 tabulated is repaired. The
plan's Tasks section now says the ordering "is enforced rather than preferred"
and that "a version of this plan in which the records call these tasks
'independent' is a defect, not a variant". `177.002-T` and `177.005-T` each
open with "BLOCKED BY `177.004-T`, AND THAT ORDERING IS A SAFETY EDGE RATHER
THAN A SCHEDULING PREFERENCE", and neither claims independence from
`177.004-T` any more. `177.001-T` states, correctly, that it inherits the
precedence transitively. R8 and H9 were added and both cite the edge.

This is a genuine closure of the finding as written. What it does not close is
what the edge *guarantees*, which is finding `K1` below — a question attempt 02
could not reach because the edge did not exist to interrogate.

**F2 (P2) — the unreconciled `ISOLATION_UNDETERMINED` pair. Closed.** The
sentence "`ISOLATION_UNDETERMINED` is not a blocker on the unit's usefulness"
is gone; a direct search of the plan confirms no surviving instance. In its
place the plan defines four states and a **Successor eligibility** table
stating, per state, whether `181-S` may harvest and what: everything under
`ISOLATION_CHARACTERIZED`, floor-only under `ISOLATION_FLOOR_ONLY`, nothing
under `ISOLATION_UNDETERMINED` or `ISOLATION_NOT_OBSERVED`. The fallback value
`NOT DETERMINED — FLOOR INVOKED` mirrors the sibling spike's treatment, carries
all three required parts, is explicitly "not a pass value and asserts nothing
about the isolation", and is reproduced verbatim in `177.006-T`. The plan also
states that no state presents the floor as proven and that `002-C` stays
blocked under all four — which is the one-directional property attempt 01
asked for and this revision preserves.

**F3 (P3) — manifest order. Closed.** `custom_fields.items` reads `177-F`,
`177.004-T`, `177.005-T`, `177.001-T`, `177.002-T`, `177.003-T`, `177.006-T`,
which is dependency order, and the description opens with "MANIFEST ORDER IS
DEPENDENCY ORDER" and explains why the credential inspection leads.

## Independent verification of plan-to-record correspondence

`183-S` members are `177-F` plus `177.001-T` through `177.006-T`. Size and
complexity match the plan's task table on both axes for all six tasks:
`S`/`medium`, `S`/`high`, `XS`/`low`, `S`/`medium`, `S`/`medium`, `XS`/`low`.
Every task carries `size_source: agent` and a non-empty
`size_ruleset_version` (`v1`). The two-hour rule holds on the size axis for
every task; elapsed bounds are 90/90/120/120/45/20 minutes and are declared
individual. `177.002-T` is the single `complexity: high` task and carries the
declared de-risking rationale in both plan and record.

Property coverage is complete and no property is assigned to the authoring
task alone: I1 → `177.004-T`; I2, I3 → `177.001-T`; I4, I5, I6 →
`177.002-T`; I7 → `177.005-T` observes and `177.003-T` transcribes.
`177.006-T`'s structural check rejects any property whose only assignment is
`177.003-T`, and the I7 row satisfies it because it names a determining task
alongside the transcriber.

The I7 path is real rather than re-derived: `177.005-T` performs one actual
release-asset acquisition and records each hop's host, the terminal host, and
whether the terminal host is stable across repeated attempts; `177.003-T` reads
the rule off that record and R5 makes an I7 row with no recorded chain
`ABSENT`. This is the direct repair of attempt-08 `B6` and it holds.

Credential inspection precedes untrusted acquisition and probe work **in
sequence**, verified against `item_deps` and not against prose. Whether it
precedes them in *effect* is `K1`.

Fail-closed semantics hold across all four states: any row not affirmatively
`DETERMINED` or `NOT DETERMINED — FLOOR INVOKED` is `ABSENT`; any missing,
unparseable or verdict-less artifact is `ISOLATION_NOT_OBSERVED`; counts must
sum to 7 and a verdict line disagreeing with the ledger is itself a fail. No
fabricated PASS is available anywhere in the vocabulary, and
`ISOLATION_FLOOR_ONLY` is explicitly not one.

Root eligibility and gate direction hold: `183-S` has no incoming edge and
`181-S` depends on `183-S`, matching `gates: 181-S`.

The `002-C` boundary is intact and was re-verified independently:
`.backlogit/queue/002-C.md` is `status: blocked`, states that it carries no
dependency edges in either direction, carries none in `item_deps`, is in no
manifest, and is untouched by this review. The plan refuses any
administrative-close transition.

Evidence-handling discipline holds: the I1 inventory is names-only and
presence/absence-only in both plan and `177.004-T`, and an inventory requiring
a secret value to be meaningful is itself the NOT ACHIEVABLE verdict.

## P0 findings

**None.** No finding makes the declared pass state unreachable, and no task in
this unit executes the untrusted binary.

## P1 findings (1)

**K1 — the I1 edge gates on task *completion*, not on an *achievable* I1
verdict, so the probe-safety guarantee fails on two outcomes the plan itself
declares reachable.**

The plan states the guarantee four times, in the strongest available terms.
Blast radius:

> `177.004-T` determines I1 and is a `blocks` predecessor of both `177.005-T`
> (the acquisition) and `177.002-T` (the containment probe), **so no probe or
> acquisition job can run in a job environment whose credential absence is
> still unverified.**

H7 rests the answer to "is the probe itself safe" on the same property; H9
answers "is the ordering enforced" with "Enforced"; R8's mitigation is the
edge; and `177.004-T`'s own record says "**Neither acquisition nor probe work
may execute in a job environment whose credential absence is still
unverified.**"

A `blocks` edge is satisfied when its predecessor **completes**. It carries no
predicate over the predecessor's *result*. The plan declares two completion
outcomes for `177.004-T` in which credential absence is not established:

1. **`NOT DETERMINED — FLOOR INVOKED`.** `177.004-T` carries a 90-minute
   elapsed bound and an explicit recorded-and-stop rule: "on reaching it,
   record I1 as NOT DETERMINED - FLOOR INVOKED". R9 confirms this is a
   legitimate, non-extending outcome. The task completes; the edge clears;
   `177.005-T` pulls an untrusted external release asset onto a runner and
   `177.002-T` probes containment, with credential absence **unverified** —
   the literal condition the guarantee forbids.
2. **`DETERMINED` with a `NOT ACHIEVABLE` verdict.** The plan contemplates
   this explicitly ("If any of I1–I6 is NOT ACHIEVABLE, the findings artifact
   must state …") and R6 names a concrete path to it. Here the outcome is
   worse than unverified: credential absence has been **affirmatively
   falsified**, and the edge still clears. The untrusted asset is then
   acquired into a job environment observed to carry credentials, which is the
   exact hazard H7 describes — "a privileged process handling an untrusted
   artifact even without executing it."

A direct search of the plan for `halt`, `stop`, `abort` and `NOT ACHIEVABLE`
returns no stop condition on either outcome, and none of the six `177.x`
records carries one. The nearest text — `177.004-T`'s "SECURITY MODEL IS A
CONSTRAINT, NOT A QUESTION: if I1 is NOT ACHIEVABLE, `181-S` degrades to
evidence-and-documentation only" — governs the *successor unit's* scope. It
says nothing about whether *this* unit's remaining tasks proceed, and they are
the ones that touch the untrusted artifact.

So the guarantee is still a claim its records cannot deliver. The remediation
converted an ordering *assertion* into an ordering *edge*; the safety argument
needs an outcome *predicate*, and an edge is not one. This is the same
composition-defect class as attempt 02's `F1` — the clauses are individually
defensible and the defect lives at their seam — one level further in, which is
the pattern
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`
records and which `docs/compound/093-S-review-loop-convergence.md` warns does
not converge by itself on novel safety-critical work.

**Graded P1, not P0.** The declared pass state is reachable, every property
has a determining task, the security model is not weakened on paper, and no
task in the unit executes the untrusted binary — so the worst realizable
outcome is acquisition and probing in a credential-bearing environment, not
execution. **Graded P1, not P2**, because the plan's adversarial pass uses this
property as its answer to whether the probe is safe at all, because the
hazard is in the unit's own subject matter rather than adjacent to it, and
because Principle III (Workspace Isolation and Security Boundaries) is engaged
directly: a job that acquires an untrusted third-party binary while holding
credentials is the boundary violation the whole unit exists to characterize.

*Minimum remediation — one stop condition, stated in five places.* Make the
precedence a **verdict** predicate: `177.005-T` and `177.002-T` execute only if
I1 resolved `DETERMINED` with an `ACHIEVABLE` verdict. On any other I1 outcome
they do not run; their properties (I2, I3 via the transitive edge, and I4, I5,
I6) are recorded `NOT DETERMINED — FLOOR INVOKED` naming I1 as the blocker,
which resolves the unit to `ISOLATION_FLOOR_ONLY` — an outcome the four-state
model already handles correctly and which needs no new machinery. Reproduce the
condition in `177.004-T`, `177.005-T` and `177.002-T`, and amend the
blast-radius sentence, H7, H9 and R8 so each states the predicate rather than
the edge. No new task, no size change, and no change to the state vocabulary is
required.

*Personas:* Security Lens Reviewer; Constitution Reviewer (Principle III,
Workspace Isolation and Security Boundaries); Architecture Strategist;
Learnings Researcher.

## P2 findings (1)

**K2 — four determining tasks require hosted-runner jobs, and the
probe-workflow's lifecycle is undeclared while the blast-radius and rollback
sections state that no tracked surface is touched.**

The plan's blast radius says:

> **None in the workspace:** the spike produces a document and activates
> nothing. It installs nothing, registers nothing, and **mutates no tracked
> surface outside `docs/spikes/`**.

and its rollback says:

> Any CI definition written to run a determining task is a **throwaway probe,
> not a committed workflow**, and `181-S` owns every committed CI surface.

Four of the six tasks require a job on a GitHub-hosted Linux runner:
`177.004-T` ("run a probe job on a GitHub-hosted Linux runner configured
exactly as the conformance job would be"), `177.005-T` ("on a GitHub-hosted
Linux runner, perform ONE real … download"), `177.001-T` ("a recorded job run
with the repository omitted"), and `177.002-T`'s containment probes.

A hosted runner executes only workflow definitions present on a ref in the
repository. Running these tasks therefore requires committing and pushing a
workflow file to the working branch — a tracked surface outside `docs/spikes/`
— so "not a committed workflow" is true only in the narrower sense of "not
merged as a permanent CI surface", and the blast-radius sentence as written is
inaccurate. No task in the unit states how the probe workflow is created,
where it lives, who owns it across the four tasks that need it, or when it is
removed.

This is the same gap class the sibling spike was blocked on and then closed:
attempt 02's `E1` on `182-S` produced a full `## Prototype lifecycle` section
for exactly this kind of throwaway execution artifact — owner, survival across
task boundaries, observation point, discard point. `183-S` has four tasks
sharing one throwaway execution artifact and no equivalent section. The
cross-unit inconsistency is what makes it worth recording: the treatment
existed in the same remediation cycle and was not propagated.

The security dimension is small but real. The artifact in question is a
workflow that deliberately attempts egress denial and pulls an untrusted
external asset into CI. Pushing it to a branch is ordinary practice here and is
not itself the concern; leaving its removal unowned, on a unit whose entire
argument is containment, is.

**Graded P2, not P1.** Nothing in the hazard is realized by the plan's
specified actions, the workflow is a probe on a feature branch rather than a
default-branch surface, `181-S` correctly owns every committed CI surface, and
the fix is additive. **Graded P2, not P3**, because two hardening statements —
the blast radius and the rollback — are inaccurate as written rather than
merely incomplete, and the hardening section is a gate in this unit.

*Minimum remediation.* Add a short probe-workflow lifecycle paragraph on the
sibling's model: the probe workflow is created by `177.004-T` on the working
branch, is shared by `177.005-T`, `177.001-T` and `177.002-T`, is never merged
to the default branch, and is removed by `177.003-T` at spike close, which
records its removal in the findings artifact. Amend the blast-radius sentence
to say the unit touches one throwaway workflow file on the working branch and
no other tracked surface, and amend the rollback line accordingly.

*Personas:* Scope Boundary Auditor; Security Lens Reviewer; Learnings
Researcher.

## P3 findings

**None.**

## Runtime verification and operational closure

Called out explicitly, as the gate requires.

The unit produces one document and declares `Activation commit | None`, so
there is no runtime surface to verify and no closure evidence to produce in
this unit. That is correct for a spike.

The operational qualifier recorded at attempts 01 and 02 still applies and is
now split across two graded findings rather than carried as a note: the
determining tasks run real CI jobs that acquire a real external asset and probe
containment. `K1` is about what gates those jobs; `K2` is about what artifact
runs them and who removes it.

## Disposition

**No remediation.** `remediation_revision` is `null`, `disposition` is `null`,
and the governing revision remains 3 — the revision reviewed and found
BLOCKED.

This plan is **not harvest-ready and not Ship-ready**. No backlog record,
source file, test, template, CI definition or configuration was changed on the
strength of this review; in particular no dependency edge was added or removed
and `.backlogit/queue/002-C.md` was read but not touched, because mutating
either is remediation and no remediation is authorized in this cycle.

**On terminality.** The operator designated attempt 03 the terminal review
cycle. Terminality is a designation of the *review* cycle, not a closure of the
*findings*: a P1 remains a P1 and this artifact records FAIL/BLOCKED on its
merits. Severity was not lowered to reach a closable state. Closing `K1`
requires either an operator-authorized bounded remediation cycle followed by an
independent attempt 04 — which requires the operator to lift the terminal
designation — or an explicit, recorded operator waiver accepting `K1` as a
known defect. `K2` is a moderate follow-up that belongs in the same cycle.
Neither disposition is a decision this reviewer may take.
