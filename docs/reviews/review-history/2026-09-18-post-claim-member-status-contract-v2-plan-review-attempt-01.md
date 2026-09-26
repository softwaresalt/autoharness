---
title: "Plan review attempt 01 — Canonical post-claim member-status contract (P-002.7), v2"
description: "Immutable per-attempt plan-review artifact recording the first independent review of docs/plans/2026-09-18-post-claim-member-status-contract-plan.md at revision 1, against reviewed content HEAD db39553a. Gate result FAIL; decision BLOCKED on two P0, three P1, two P2 and one P3 deduplicated finding. The two P0s are both plan-versus-manifest contradictions in the shipment this plan governs: 177-S encodes the policy-template and installed-mirror updates as two tasks joined by a blocks edge, which the plan's own ACTIVATE invariant and decision D2 forbid; and the GREEN-phase assertion defect the plan exists to close, attempt-08 B2, is still encoded in 169.005-T and 169.008-T with no RED task covering mirror-divergence or version-attribution assertions. Dispatch ran in single-agent declared degradation with all seven personas covered inline; engram indexed retrieval was circuit-open and intercom unavailable. No remediation was performed and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-01.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 1
attempt_range: "01"
attempt_conformance: conforming
review_terminal: false
verdict_manifest: docs/reviews/2026-09-18-post-claim-member-status-contract-v2-plan-review.md
supersedes: null
plan_path: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
plan_id: post-claim-member-status-contract-v2
reviewed_revision: 1
reviewed_content_head: db39553a
reviewed_content_state: committed
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 3EF5AAF2
feature_id: 169-F
shipment_id: 177-S
unit_role: reduced-defect-unit
dag_role: root
supersedes_plan: docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
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
p0_open: 2
p1_open: 3
p2_open: 2
p3_open: 1
hardening_required: false
hardening_present: true
carried_forward_attempt_08_findings:
  - finding: "B1 — executable records cite non-existent stash 3EF5AAF9"
    state: closed-out-of-band
    evidence: "Verified at db39553a: 169-F, 177-S and the eight 169.x task records now cite 3EF5AAF2, per the governing decision's F10 correction."
  - finding: "B2 — new assertions enter in the GREEN phase and are never observed failing"
    state: open
    evidence: "169.005-T and 169.008-T remain GREEN-phase assertion-adding tasks in shipment 177-S; see A2 below."
persona_coverage:
  - persona: constitution
    status: complete
    mode: inline
    findings: A1, C2
  - persona: python
    status: complete
    mode: inline
    findings: A2, B1
  - persona: scope-boundary
    status: complete
    mode: inline
    findings: B1, B2, C1, D1
  - persona: learnings
    status: complete
    mode: inline
    findings: A1, A2
  - persona: architecture
    status: complete
    mode: inline-same-model
    findings: A1, A2, B2, B3
  - persona: agent-native-parity
    status: complete
    mode: inline-same-model
    trigger: "The contract governs a status vocabulary that Ship's claim sequence and the backlog surfaces both consume."
    findings: B3
  - persona: security-lens
    status: complete
    mode: inline-same-model
    trigger: "Assessed for trust-boundary and privilege surfaces; the unit changes declarations only and exposes none."
    findings: none
tags:
  - "plan-review"
  - "defect-unit"
  - "p002-7"
  - "member-status"
  - "dag-root"
  - "portfolio-2026-09-18"
---

# Plan review attempt 01 — Canonical post-claim member-status contract (P-002.7), v2

This artifact records **one thing**: an independent reviewer's verdict on plan
revision 1 as it stands at content HEAD `db39553a`. It has no Part 2. No
remediation followed it, no finding below is closed, and Stage asserts no
`PASS`.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-18-post-claim-member-status-contract-plan.md` |
| Reviewed revision | 1 |
| Reviewed content HEAD | `db39553a` (committed) |
| Verdict at entry | `REMEDIATED-PENDING-REVIEW` at plan revision 1 |
| Covering feature / shipment | `169-F` / `177-S` |
| Unit role | reduced defect unit, DAG root (`177-S` has no incoming dependency edge) |
| Supersedes | `docs/plans/2026-09-17-post-claim-member-status-contract-plan.md` (revision 7, terminal at attempt 08) |
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

Security Lens was applied and returned **no finding**: the unit changes
declarations and a conformance test, exposes no execution boundary, no
credential surface and no external trust boundary. That is recorded as a
covered persona with a nil result, not as a skipped persona.

Indexed retrieval was circuit-open and was not retried. Every claim below cites
an exact path, a backlogit record, or a `git` fact.

## What the plan gets right

Recorded so the P0s are not read as a rejection of the unit's premise.

* **The root claim is correct and empirically confirmed.** The plan argues this
  unit needs no foundation and must not be serialized behind
  `182-S` → `184-S` → `185-S`. `item_deps` at `db39553a` carries **no edge in
  either direction** for `177-S`, while every other queued defect unit has one
  (`176-S` ← `185-S`,`187-S`; `178-S` ← `185-S`; `180-S` ← `185-S`;
  `181-S` ← `183-S`). The old false-star edge `177-S → 176-S` recorded in F9 is
  gone. The DAG root status this plan asserts is real.
* **The diagnosis of the attempt-08 evidence defect is exactly right.** "A
  GREEN-only assertion cannot distinguish 'the contract holds' from 'the
  assertion does not test the contract'" is the correct reading of `B2`, and
  the refusal to accept an aggregate suite exit as per-assertion RED evidence
  is the right standard.
* **The out-of-scope boundary is disciplined.** The claim mechanism, reconcile
  classification and the transition table are all excluded, and the adjacent
  `abandoned`-transition observation is recorded as explicitly out of scope
  rather than quietly absorbed.
* **Attempt-08 `B1` is genuinely closed.** Verified at `db39553a`: `169-F`,
  `177-S` and the eight `169.x` task records now cite `3EF5AAF2`; the phantom
  `3EF5AAF9` is gone. The F10 correction was applied.

The findings below are not about the plan's reasoning. They are about the
distance between that reasoning and the executable records the plan governs.

## P0 findings (2, deduplicated)

**A1 — the shipment this plan governs encodes the template/mirror split the
plan's own ACTIVATE invariant forbids.**

The plan's Rollout section states:

> **ACTIVATE.** One task, one commit updating every declared surface —
> template and installed mirror together. Splitting them produces a reachable
> state in which a mirror states a vocabulary its template does not.

Its composed-state check repeats it: "Activation commit | one task, one commit
across every declared surface and its mirror."

The governing decision states the general rule in D2, in a block quote:

> **Sequential task edges are not atomic.** A dependency edge from task *A* to
> task *B* permits a commit — and therefore a reachable repository state —
> between them. Any pair of surfaces that must never disagree belongs in **one
> task**, not in two tasks joined by an edge.

and claims the specific outcome: D2 "retires attempt-08 `B7` on `179-S` and the
`T1`/`T2` shape on `177-S` **by construction**."

It is not retired. Shipment `177-S` at `db39553a` carries:

| ID | Title | Size |
|---|---|---|
| `169.001-T` | "P-002.7 T1: author the canonical post-claim member-status clause in the **policy template**" | S |
| `169.002-T` | "P-002.7 T2: apply the identical clause to the **installed policy mirror**" | XS |

and `item_deps` carries `169.002-T` → `blocks` → `169.001-T`.

That is exactly two tasks, joined by exactly one edge, across exactly the
template/mirror pair the plan names as the pair that must never disagree. The
`T1`/`T2` shape the decision declared retired is present, unchanged, in a
`queued` shipment that is eligible for Ship claim today.

The reachable bad state is not theoretical. On completion of `169.001-T` and
before `169.002-T`, the repository sits with `templates/` stating the canonical
vocabulary and `.github/` stating the old divergent one — which is the precise
condition the unit exists to eliminate, manufactured by the unit's own rollout.

This is the composition defect recorded in
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`:
the plan clause is correct, the manifest is a reasonable decomposition, and the
contradiction lives only at their seam. It is also the parity-in-one-commit
lesson from
`docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md`,
whose Lesson 1 fix kept `.github/skills/...` and `templates/skills/...`
"at parity in the same commit".

Graded **P0**: a plan whose governing invariant is contradicted by its own
queued manifest is not shippable, and the contradiction is invisible to anyone
reading either artifact alone.

*Recommendation.* Merge `169.001-T` and `169.002-T` into one ACTIVATE task
covering template and mirror together, remove the edge, and re-check the merged
task against the 2-hour rule. If the merged task exceeds it, decision R5
applies — "A contract touching too many surfaces to activate in one task is too
large a contract and must be re-scoped" — and the contract narrows rather than
the commit splitting.

*Personas:* Architecture Strategist; Constitution Reviewer; Learnings
Researcher.

**A2 — the evidence defect this plan exists to close is still encoded in the
manifest it governs.**

The plan's central claim, set in bold, is:

> **Every assertion in this unit is observed failing against the current
> divergent surfaces before it is observed passing.** The RED observation is
> recorded per assertion, not as an aggregate suite result.

Attempt-08 `B2` — the defect being closed — named the specific assertions:

> `T4` and `T5` are GREEN tasks, but each is specified to *add* assertions —
> mirror-divergence detection, attribution-paragraph presence, and the negative
> rows for the state machine. Those assertions are authored **after** the
> production text exists, so they are never observed red.

Shipment `177-S` at `db39553a` still carries those tasks, verbatim in role:

| ID | Title | Phase |
|---|---|---|
| `169.009-T` | "T0a (**RED**): composed state-machine contract test for the three transition states, observed failing" | RED |
| `169.010-T` | "T0b (**RED**): wiring and cross-reference contract test observed failing in both copies" | RED |
| `169.008-T` | "T4 (**GREEN**): wiring, **mirror-divergence** and **version-attribution** suite verified against shipped text" | GREEN |
| `169.005-T` | "T5 (**GREEN**): composed state-machine suite verified against the shipped clause" | GREEN |

The two RED tasks cover "the three transition states" and "wiring and
cross-reference". **Mirror-divergence and version-attribution appear in no RED
task.** They appear only in `169.008-T`, a GREEN task. The negative state-machine
rows `B2` also named have no RED task either; `169.009-T` covers the three
transition states, not the negative rows.

No task in the manifest records a **per-assertion** RED observation at all. The
plan's `R2` mitigation — "Each assertion's failing observation is recorded
individually; an aggregate suite exit code is explicitly insufficient evidence"
— has no task that implements it.

So the plan asserts a closure that its own decomposition does not encode.
Executing `177-S` as manifested reproduces attempt-08 `B2` exactly: new
assertions authored after the production text exists, never observed red.

Graded **P0**: this is the sole defect the unit was re-authored to fix, the fix
is absent from the executable surface, and the shipment is queued and
claimable. A reviewer approving the plan text alone would admit to execution the
identical condition that terminated the previous eight attempts.

*Recommendation.* Re-derive the task set from this plan rather than inheriting
the superseded plan's `T0a`/`T0b`/`T1`–`T6` shape. Every assertion — including
mirror-divergence, version-attribution and the negative state-machine rows —
needs a RED task that records its individual failing observation, and the GREEN
tasks must add no assertion that no RED task introduced.

*Personas:* Architecture Strategist; Python Reviewer; Learnings Researcher.

## P1 findings (3)

**B1 — the plan enumerates no implementation units.**

Both sibling roots reviewed this cycle carry a `## Tasks` table mapping task ID
to size and complexity, and both match their shipments exactly. This plan has
no task table, names no task ID, and states no task count, while the shipment it
governs is already assembled with eight tasks including one `M`-sized member.

The effect is structural rather than cosmetic. There is no surface on which a
reviewer can check plan-to-backlog correspondence, the 2-hour rule, the
size/complexity assignment, or the plan's own "ACTIVATE is one task" invariant.
That is why A1 and A2 were invisible to the plan's own hardening pass: `H6`
asks "Why one commit across all surfaces?" and answers it correctly in
principle, without ever checking whether the manifest does it.

A governing plan that cannot be checked against the work it governs is the
precondition for both P0s above, not a separate stylistic concern.

*Recommendation.* Add the task table in the sibling plans' shape — ID, task,
size, complexity, phase (RED/PREPARE/ACTIVATE/VERIFY) — populated from the
re-derived task set A2 requires, and state the sequence explicitly.

*Personas:* Scope Boundary Auditor; Python Reviewer.

**B2 — the contract's subject is unenumerated, so its central mitigation is
unverifiable.**

Contract clause 4 reads: "The surface list is derived by a rule over tracked
files, with generated paths excluded by rule." Risk `R1`'s mitigation reads:
"It is derived by rule and asserted at a **fixed count**, so an unlisted
surface fails the test rather than being exempted."

The plan states **neither the rule, nor the count, nor the resulting list**. It
names exactly one exclusion (`.autoharness/staging/`, correctly justified as
gitignored generated output).

The governing decision demonstrates the intended shape two sections earlier.
F7 derives a closed inventory by exactly this method — "tracked files matching
a marker set, minus generated paths" — states the marker set
(`decision: PASS|FAIL|ADVISORY`, `verdict_manifest`, `latest_attempt`,
`gate_result`), states the search scope (`.github/`, `templates/`, `src/`,
`scripts/`), and **lists the four resulting files**. That inventory is
checkable. This one is not.

Three things follow. `R1`'s "fixed count" cannot be asserted against an unknown
number. The ACTIVATE task's width is unknown, so decision `R5` — the rule that
keeps a one-commit activation inside two hours — cannot be evaluated, which is
the same gap A1's remediation must close. And the conformance test's own
enumeration rule, which clause 3 makes load-bearing for future surfaces, is
specified only as "by rule".

*Recommendation.* State the marker set, the search scope, the exclusion rule,
the enumerated surface list and its count, in the F7 shape.

*Personas:* Scope Boundary Auditor; Architecture Strategist.

**B3 — the composed-state check names producer and consumer in prose rather
than as identified artifacts.**

D6 requires "Producer | A named, **existing** artifact that emits the
observation" and "Consumer | A named, **existing** artifact that reads it". The
plan supplies "the canonical vocabulary definition" and "the cross-surface
conformance test; Ship's claim sequence" — no path, no policy clause ID, no
test module name.

Every SM table in the governing decision names them precisely, including for
artifacts that do not yet exist ("Producer: `autoharness op harness p004-gate`
(created in `176-S`, on `P2`)"), which shows non-existence is not the
obstacle — the decision names the identifier and its creating unit.

This is graded P1 rather than advisory because of what the unnamed referents
are. "Ship's claim sequence" is the consumer that makes this contract matter;
without a named clause in `.github/agents/_ship.agent.md` or
`.github/policies/workflow-policies.md`, the conformance test's assertion
target is undetermined, and B2's missing surface list is the reason it cannot
be inferred. B2 and B3 share a root — nothing in this plan is named — and are
counted separately because each is independently actionable.

*Personas:* Architecture Strategist; Agent-Native Parity Reviewer.

## P2 findings (2)

**C1 — the plan misstates the immutable attempt-08 record.**

The plan states: "Attempt 08 recorded no bootstrap, no execution, no
schema-compatibility and no transport finding against it. It was blocked on **a
single** evidence defect."

The attempt-08 artifact records **two P1 findings and one P2**: `B1`, that every
executable record in the unit cited `3EF5AAF9`, a stash ID present in no stash
file live or archived; `B2`, the GREEN-only assertions; and `C1` against the
manifest's own description. The first is a provenance defect, not an evidence
defect, and it was a blocker in its own right.

The *material* position today is defensible: `B1` was corrected out of band
under F10, and this reviewer verified the correction — `169-F`, `177-S` and all
eight `169.x` records now cite `3EF5AAF2`. So one defect is genuinely open.

But the sentence as written is false about the record, and it is replicated
verbatim in `169-F`'s description ("Attempt 08 blocked this unit on a single
evidence defect"). Graded **P2** because the substantive effect is nil and the
correction it glosses over did happen. Graded no lower because this portfolio's
recurring defect class is narrative that has drifted from the record it cites,
and because the truthful sentence is both shorter and stronger: attempt 08
recorded two P1s, one of which is closed by the governing decision's
provenance correction, leaving one open.

*Recommendation.* Restate as: attempt 08 recorded two P1 findings; `B1`
(phantom source stash `3EF5AAF9`) is closed by F10 and verified in the records;
`B2` (GREEN-only assertions) is the open defect this revision addresses.

*Personas:* Constitution Reviewer; Scope Boundary Auditor.

**C2 — the `verdict` key carries a value from the disposition enum.**

Identical in kind and grading to `B1` on `182-S` and `183-S`, recorded once per
plan surface. It is slightly sharper here: this plan's own predecessor manifest
is the document that establishes the rule, stating that
`REMEDIATED-PENDING-REVIEW` "is not available here and is not used: it is a
`disposition`, never a `verdict`, and it asserts that Stage produced a revision
in response" — and revision 1's `verdict_note` concedes no revision was
produced in response to anything.

Graded P2 on the same narrow ground: per F7, today's `harvest` reads an inline
marker in the plan and never opens the manifest, so present blast radius is
record integrity rather than admission control. It becomes P1 when `186-S`
activates SM-2.

*Personas:* Constitution Reviewer; Architecture Strategist.

## P3 findings (1)

**D1 — the manifest's item order and task numbering both mislead on sequence.**

`177-S`'s `items` array is ordered `169-F`, `169.001-T`, `169.002-T`,
`169.003-T`, `169.005-T`, `169.007-T`, `169.008-T`, `169.009-T`, `169.010-T` —
which places the two RED tasks (`169.009-T` = T0a, `169.010-T` = T0b) **last**,
after the GREEN tasks. The T-labels are also non-monotonic against the IDs
(`169.007-T` is "T6" while `169.008-T` is "T4"), and `169.004-T` and
`169.006-T` are absent from the sequence.

Execution order is **not** actually wrong: `item_deps` carries
`169.001-T` → `169.009-T` and `169.001-T` → `169.010-T`, so the RED tasks block
everything downstream and a dependency-ordered consumer runs them first. This
is therefore advisory, not a blocker.

It is recorded because a reader checking RED-before-GREEN from the manifest
array — the reading that A2 is about — sees the opposite of the truth, and
because the remediation A2 requires will rewrite this task set anyway.

*Personas:* Scope Boundary Auditor.

## Runtime verification and operational closure

Called out explicitly, as the gate requires.

The plan's `## Rollout` and `### Rollback` sections are adequate in principle:
PREPARE is inert, VERIFY records per-assertion RED then GREEN, and the ACTIVATE
commit "reverts as a unit, returning every surface to its current divergent
state simultaneously."

The rollback guarantee is, however, **conditional on A1 being fixed**. It holds
only if activation is one commit. With `169.001-T` and `169.002-T` as two
tasks joined by an edge, a revert of the second commit leaves the first in
place, and the rollback returns the workspace to the split state rather than to
the "current divergent state" the plan promises. This is not counted as a
separate finding — it is a consequence of A1 — but it is recorded so the
remediation cycle re-checks the rollback claim after merging the tasks.

Closure evidence is not specified for the unit, which is acceptable at plan
stage for a declaration contract.

## Disposition

**No remediation.** `remediation_revision` is `null`, `disposition` is `null`,
and the governing revision remains 1 — the revision reviewed and found
BLOCKED.

This plan is **not harvest-ready and not Ship-ready**. No backlog record,
source file, test, template, policy or configuration was changed on the
strength of this review; in particular the eight `169.x` task records and the
`177-S` manifest were read but **not** mutated, because correcting them is
remediation and no remediation is authorized in this cycle.

Closing A1 and A2 requires a Stage remediation cycle producing revision 2 — one
that re-derives the executable task set from the plan instead of inheriting the
superseded plan's shape — followed by an independent attempt 02.
