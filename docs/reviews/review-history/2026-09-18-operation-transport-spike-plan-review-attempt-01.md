---
title: "Plan review attempt 01 — Operation transport spike (S1)"
description: "Immutable per-attempt plan-review artifact recording the first independent review of docs/plans/2026-09-18-operation-transport-spike-plan.md at revision 1, against reviewed content HEAD db39553a. Gate result FAIL; decision BLOCKED on three P1, one P2 and one P3 deduplicated finding, zero P0. The blockers are: the plan declares itself a gate but carries no composed-state check, which the governing decision requires before harvest; the question set defines the .mcp.json registration shape without asking what tool authority that registration declares, on a server that would expose filesystem-writing and subprocess-executing operations; and the plan declares requires_plan_hardening false on a unit whose entire subject is distribution blast radius and a new agent trust boundary, while its sibling spike declares true on identical reasoning. Dispatch ran in single-agent declared degradation with all seven personas covered inline; engram indexed retrieval was circuit-open and intercom unavailable. No remediation was performed and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-18-operation-transport-spike-plan-review-attempt-01.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 1
attempt_range: "01"
attempt_conformance: conforming
review_terminal: false
verdict_manifest: docs/reviews/2026-09-18-operation-transport-spike-plan-review.md
supersedes: null
plan_path: docs/plans/2026-09-18-operation-transport-spike-plan.md
plan_id: operation-transport-spike
reviewed_revision: 1
reviewed_content_head: db39553a
reviewed_content_state: committed
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 71200CBB
  - 76EBDE6D
feature_id: 176-F
shipment_id: 182-S
unit_role: precursor-spike
dag_role: root
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
p0_open: 0
p1_open: 3
p2_open: 1
p3_open: 1
hardening_required: true
hardening_present: false
persona_coverage:
  - persona: constitution
    status: complete
    mode: inline
    findings: A1
  - persona: python
    status: complete
    mode: inline
    findings: none
  - persona: scope-boundary
    status: complete
    mode: inline
    findings: C1
  - persona: learnings
    status: complete
    mode: inline
    findings: A2
  - persona: architecture
    status: complete
    mode: inline-same-model
    findings: A1, A2, A3
  - persona: agent-native-parity
    status: complete
    mode: inline-same-model
    trigger: "Plan defines an MCP server registration shape and a CLI/MCP parity-test strategy."
    findings: A2
  - persona: security-lens
    status: complete
    mode: inline-same-model
    trigger: "Plan defines a new external transport surface and its registration into the agent trust boundary."
    findings: A2, A3
tags:
  - "plan-review"
  - "spike"
  - "mcp"
  - "transport"
  - "distribution"
  - "portfolio-2026-09-18"
---

# Plan review attempt 01 — Operation transport spike (S1)

This artifact records **one thing**: an independent reviewer's verdict on plan
revision 1 as it stands at content HEAD `db39553a`. It has no Part 2. No
remediation followed it, no finding below is closed, and Stage asserts no
`PASS`.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-18-operation-transport-spike-plan.md` |
| Reviewed revision | 1 |
| Reviewed content HEAD | `db39553a` (committed) |
| Verdict at entry | `REMEDIATED-PENDING-REVIEW` at plan revision 1 |
| Covering feature / shipment | `176-F` / `182-S` |
| Unit role | precursor spike, DAG root (`182-S` has no incoming dependency edge) |
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

Both conditional personas were **triggered and ran**: Agent-Native Parity,
because the plan defines an MCP registration shape and a CLI/MCP parity-test
strategy; Security Lens, because the plan defines a new transport surface that
enters the agent trust boundary.

Indexed retrieval was circuit-open and was not retried. Every claim below cites
an exact path, a backlogit record, or a `git` fact.

## What the plan gets right

Recorded so the blockers are not read as a rejection of the unit's premise.

* The factual base is **accurate and independently verified**. `.mcp.json`
  registers exactly the six servers named (`backlogit`, `engram`,
  `graphtor-docs`, `context7`, `tavily`, `github`), `autoharness` is not among
  them; `pyproject.toml` declares exactly `jsonschema>=4.23.0` and
  `PyYAML>=6.0.2` with `requires-python = ">=3.10"`.
* The attempt-08 citations are **exact**. `180-S` attempt-08 `B3` is "the
  guarded MCP create has no server, owner, or registration", and its body reads
  "no MCP server that exposes it, no owner that implements it, and no
  registration step that makes it callable" — quoted correctly. `176-S`
  attempt-08 `B6` is "no MCP parity for the gate surface" — characterized
  correctly. After this portfolio's recorded provenance failures, this matters.
* Task-to-record correspondence **holds**: `176.001-T` (XS/low),
  `176.002-T` (S/medium), `176.003-T` (XS/low) in shipment `182-S` match the
  plan's task table on both axes.
* Every cross-reference in the plan resolves, including
  `docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md`.
  The two unresolved paths are the spike's own deliverables, which is correct.
* Refusing to decide the transport inside a plan is the right call and is the
  governing decision's D7 position.

## P0 findings

**None.** No finding against this plan reaches P0. The count is recorded as
zero rather than inflated for symmetry with the sibling units.

## P1 findings (3, deduplicated)

**A1 — the plan declares itself a gate but carries no composed-state check.**

The frontmatter declares `gates: 184-S`. The Deliverable section declares the
findings artifact "the **input contract** for
`docs/plans/2026-09-18-operation-substrate-transport-plan.md`" and states that
plan "must not be harvested into executable tasks that assume a transport
before this artifact names one."

The governing decision's D6 is unambiguous: "No gate is harvested into
executable tasks until its composed state machine is written down and checked",
and it specifies the five rows every gate declares — pass state, fail state,
producer, consumer, activation commit.

This plan has no such table. The consequence is concrete, not formal:

* there is no declared pass state, so nothing states what "the spike answered
  the question" means;
* there is no fail state **distinct from "no observation"**, which D6 requires
  explicitly and which is the same `NO_OBSERVATION`-is-not-`PASS` rule the rest
  of this portfolio enforces;
* nothing tells `184-S` how to decide whether the findings artifact is usable,
  so `184-S` inherits that judgement as an assumption — the exact frame error
  the governing decision exists to end.

The sibling spike `183-S`, identical in shape and role, carries the required
`## Composed-state check` with `ISOLATION_CHARACTERIZED` /
`ISOLATION_UNDETERMINED` and an explicit "a partially-classified result is a
fail, not a partial pass" rule. The asymmetry is unexplained.

*Recommendation.* Add the D6 table. The natural shape is pass state
`TRANSPORT_DECIDED` (each of Q1–Q6 carries a recorded answer or an explicitly
recorded non-answer plus the R1 fallback), fail state `TRANSPORT_UNDECIDED`
(any question left unanswered and unfallen-back), producer the findings
artifact at its exact path, consumer
`docs/plans/2026-09-18-operation-substrate-transport-plan.md`, activation
commit none.

*Personas:* Architecture Strategist; Constitution Reviewer (Principle V,
Structured Observability).

**A2 — the question set defines the registration shape but never asks what
authority that registration grants.**

Q4 asks for "the exact `.mcp.json` registration entry for an `autoharness`
server". No question asks what **tool authority** that entry declares.

This is a live, named defect class in this very portfolio, not a hypothetical:

* the governing decision's security-boundary table lists "Tool authority" as
  enforced by "explicit per-tool allowlist in agent frontmatter and
  `.mcp.json`" and **not** by a wildcard;
* F8 records that `.mcp.json`'s `"tools": ["*"]` for the `backlogit` server is
  a current defect, and SM-4 makes narrowing it part of `180-S`'s activation
  commit rather than a follow-up — "The guard is only a gate if the unguarded
  path is closed in the **same** commit."

The server this spike designs is materially more dangerous than `backlogit`'s.
Per D1 the operations behind it write to the filesystem through the atomic
write primitive and execute subprocesses through the fixed-argv primitive. A
registration shape recommended with no authority question will be adopted by
`184-S` at whatever default the throwaway prototype happened to use — and the
default that already exists in this repository's `.mcp.json` is `["*"]`. The
portfolio would then remove the wildcard from `backlogit` in `180-S` while
introducing it on a subprocess-executing server in `184-S`.

The plan's own Out-of-scope section makes this worse rather than better: it
assigns changes to `.mcp.json` to `184-S` as "activation steps", so the
authority question has no other owner. It is out of scope here and unasked
there.

*Recommendation.* Add a question — "what per-tool allowlist does the
`autoharness` server declare, how is the operation registry projected into it,
and what is the default for an operation that is registered but not yet
allowlisted?" — and make its answer part of the deliverable alongside Q4. The
fail-closed default (registered but not allowlisted ⇒ not callable) should be
stated, not discovered.

*Personas:* Security Lens Reviewer; Agent-Native Parity Reviewer; Architecture
Strategist; Learnings Researcher.

**A3 — `requires_plan_hardening: false` on a unit whose whole subject is
distribution blast radius and a new trust boundary.**

The stated rationale is that the spike "ships no code, mutates no template,
touches no policy, and changes no installed surface", with blast radius "one
new file under `docs/spikes/`".

That measures the blast radius of the **artifact** and not of the **decision**,
and the sibling spike says so itself. `183-S` ships no code either, yet
declares `requires_plan_hardening: true` on the reasoning that "Getting the
question set wrong produces a foundation plan that under-specifies isolation,
so the question set itself warrants adversarial review even though the spike
ships no code." That argument applies here with more force, and A2 is its
demonstration: a question-set omission on a security surface is exactly what an
adversarial pass exists to catch, and no adversarial pass was run.

Stage's planning gate independently names "CLI distribution" as an
elevated-blast-radius hardening signal, and this spike's Q2/Q3/Q6 are entirely
about CLI distribution. Under the plan-review gate's own table, a plan showing
hardening signals without hardening is a **FAIL** condition in its own right.

*Recommendation.* Run `plan-harden` over the question set — specifically over
what a wrong or incomplete answer to each of Q1–Q6 costs `184-S` — or restate
the rationale to address why a transport-and-authority question set needs no
adversarial pass while an isolation question set does.

*Personas:* Security Lens Reviewer; Architecture Strategist; Constitution
Reviewer (Principle VIII, Explicit Safety Modes for Elevated Risk).

## P2 findings (1)

**B1 — the `verdict` key carries a value from the disposition enum.**

Plan frontmatter and the pre-review manifest both set
`verdict: REMEDIATED-PENDING-REVIEW`, while `verdict_note` concedes the
document "is a fresh document … not a remediation of a prior revision".

The immutable record for this portfolio already settles the vocabulary. The
attempt-08 manifest for `177-S` states: "`REMEDIATED-PENDING-REVIEW` is not
available here and is not used: it is a `disposition`, never a `verdict`, and
it asserts that Stage produced a revision in response". Here the value asserts
a remediation that the note itself denies.

This is **operative**, not prose. SM-2's `HARVEST_ADMITTED` state is defined as
"the normalized manifest for `plan_id` reports `verdict: PASS` at
`latest_attempt`"; a `verdict` key carrying an out-of-enum value is the
`REVIEW_VERDICT_AMBIGUOUS` condition that manifest's selection rule names.

Graded **P2**, not P1, on an explicit and narrow ground: the manifest-reading
consumer does not exist yet. Per F7, today's `harvest` reads an inline marker
inside the plan document and never opens the manifest, so the present blast
radius is record integrity rather than admission control. It becomes P1 the
moment `186-S` activates. The same defect is present on all three plans
reviewed this cycle and on all three of their manifests; it is counted once per
plan surface.

*Recommendation.* Use `verdict: null` (the pre-review manifests already model
this correctly for `gate_result`) or a `PENDING-REVIEW` value, and express the
remediation state, if it must be expressed at all, under a `disposition` key.

*Personas:* Constitution Reviewer; Architecture Strategist; Scope Boundary
Auditor.

## P3 findings (1)

**C1 — the time box is a task count, not a time bound.**

D7 records that both spikes are "time-boxed". The `## Time box` section bounds
the spike at "the three tasks above". It does supply a real abort criterion for
Q1 — record the unresolved question and recommend the CLI-only fallback — which
is more than most spike plans carry, and is not faulted.

What is missing is any elapsed bound on `176.002-T`, the `S`/medium prototype,
which is the only open-ended task in the unit and the one a transport spike
would actually overrun. Advisory.

*Personas:* Scope Boundary Auditor.

## Runtime verification and operational closure

Not applicable and correctly so. The unit produces a document, activates
nothing, and declares no activation commit; there is no runtime surface to
verify and no closure evidence to produce. This is noted explicitly because the
plan-review gate requires these gaps to be called out when absent rather than
passed over in silence.

## Disposition

**No remediation.** `remediation_revision` is `null`, `disposition` is `null`,
and the governing revision remains 1 — the revision reviewed and found
BLOCKED.

This plan is **not harvest-ready and not Ship-ready**. No backlog record,
source file, test, template or configuration was changed on the strength of
this review. Closing A1–A3 requires a Stage remediation cycle producing
revision 2 and an independent attempt 02.
