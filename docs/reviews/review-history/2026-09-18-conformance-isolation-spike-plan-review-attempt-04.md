---
title: "Plan review attempt 04 — Conformance isolation spike (S2)"
description: "Immutable per-attempt plan-review artifact recording the fourth and operator-designated terminal independent review of docs/plans/2026-09-18-conformance-isolation-spike-plan.md at revision 4, against reviewed content HEAD 42f2f8ec. Gate result ADVISORY; decision ADVISORY on zero P0, zero P1, one P2 and three P3 deduplicated findings. Both attempt-03 findings are independently re-derived closed: I1_GATE is now a real fail-closed verdict predicate carried inside the gated tasks rather than an ordering edge, with OPEN defined as exactly one readable ACHIEVABLE line and CLOSED as everything else including missing, unreadable, multi-line and unrecognised, and both gated tasks declining their untrusted acquisition and containment probe entirely on CLOSED; and the committed probe workflow now has one owning task, one exact path, a declared dispatch model, a declared removal owner and point, a declared rollback and branch-cleanliness evidence, with blast radius and rollback stated truthfully. The open P2 is that the gate task's mandated branch-cleanliness check has no expressible verdict: its record requires emit-no-pass on a dirty branch while the plan's composed-state vocabulary is exhaustively ledger-derived and would force the pass state, so the check is a claim rather than an executable predicate. Dispatch ran in single-agent declared degradation with all seven personas covered inline; engram was circuit-open and not retried, intercom and graphtor-docs were unavailable. No remediation was performed and no remediation cycle is proposed."
doc_type: review
source: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-04.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 4
attempt_range: "04"
attempt_conformance: conforming
review_terminal: true
terminal_designation: operator-declared
terminal_disposition: TERMINAL-ADVISORY
verdict_manifest: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-03.md
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_id: conformance-isolation-spike
reviewed_revision: 4
reviewed_content_head: 42f2f8ec
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
review_cycle: 4
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
    note: "Indexed retrieval circuit open per operator instruction; NOT retried this session. All evidence below comes from bounded direct exact-path reads, git plumbing, and read-only backlogit MCP reads over a freshly synced index (1430 artifacts)."
  - capability: agent-intercom
    state: unavailable
    note: "No operator broadcast performed; visibility is local-only. No operator choice-presentation step was skipped, because this review presents no choice."
  - capability: graphtor-docs
    state: unavailable
    note: "No graphtor-docs tool surface was exposed to this session. Documentation questions were answered by direct reads under docs/."
backlogit_index_state: "INDEX_SYNC_OK — 1430 artifacts indexed at session start"
gate_result: ADVISORY
decision: ADVISORY
verdict_at_entry: null
verdict_at_entry_disposition: REMEDIATED-PENDING-REVIEW
verdict_at_entry_plan_revision: 4
remediation_authorization: none-this-cycle
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 0
p1_open: 0
p2_open: 1
p3_open: 3
open_findings: [K3, K4, K5, K6]
hardening_required: true
hardening_present: true
hardening_sufficient: true
hardening_sufficiency_note: "The hardening pass carries H1-H14, including the verdict-predicate question H12, the gate-reachability question H13 and the committed-surface question H14 added this revision. Blast radius and rollback now name the one mutated tracked surface truthfully. K3 is not a hardening insufficiency: H14 states the branch-cleanliness expectation; the composed-state vocabulary provides no token to express its failure."
attempt_03_findings_verified:
  - finding: "K1 — the I1 precedence is enforced only by a blocks edge, which gates on predecessor completion and therefore clears while credential absence is unverified or affirmatively falsified"
    severity: P1
    state: closed
    evidence: "The plan carries a ## I1 gate section defining a verdict predicate distinct from the ordering edge. 177.004-T writes exactly one I1_GATE line to docs/spikes/2026-09-18-conformance-isolation-i1-gate.md as the last action of its run and is the sole writer. 177.005-T and 177.002-T each read that line as their FIRST action, before any acquisition, download, redirect follow, network request, handle creation, mount setup or substitution attempt. OPEN is defined as: file exists, readable, exactly one I1_GATE line, token ACHIEVABLE. CLOSED is everything else, enumerated identically in the plan and in both gated task records: missing file, unreadable file, no I1_GATE line, more than one I1_GATE line, unrecognised token, NOT_ACHIEVABLE, FLOOR_INVOKED. On CLOSED neither task runs its untrusted work at all - not deferred, not retried, not narrowed - and each records its properties NOT DETERMINED - FLOOR INVOKED naming I1 as the blocker with all three required parts. 177.006-T carries a third check that reads the observed token and forbids ISOLATION_CHARACTERIZED on a CLOSED gate, and treats a DETERMINED verdict on a gated property under a CLOSED gate as itself a fail. 177-F and the 183-S description reproduce the same predicate. The blocks edges remain in item_deps and are stated everywhere as ordering only, never as the safety argument."
  - finding: "K2 — the GitHub-hosted-runner probe workflow has no declared owner, path, lifecycle or rollback while blast radius and rollback describe the spike as mutating no tracked surface"
    severity: P2
    state: closed
    evidence: "The plan carries a ## Probe workflow lifecycle section with a four-row owner table. Created: 177.004-T, exactly one workflow at .github/workflows/spike-177-isolation-probe.yml, committed to chore/stage-176-s-workflow-defects in its own commit, no other workflow added or modified. Dispatched: all four determining tasks reuse that single workflow via workflow_dispatch by input (i1-credentials, i7-acquisition, i2-i3-egress, i4-i6-containment). Removed: 177.003-T at spike close, in the same commit that lands the findings artifact. Rolled back: 177.003-T removes it anyway on abort; rollback is git revert of the single creation commit or deletion of the single added path. Declared constraints: explicit minimal permissions block, no secrets, workflow_dispatch-only so it cannot fire on push, pull_request or schedule. Evidence: creation commit SHA and path, four dispatch run IDs and URLs, removal commit SHA, and a git status --porcelain observation showing the path absent from the branch tip. Blast radius and rollback now both name the one mutated tracked surface. The path was verified absent from the working tree at review time. All four task records and 177-F reproduce their part of the lifecycle."
persona_coverage:
  - persona: constitution
    status: complete
    mode: inline
    findings: none
  - persona: python
    status: complete
    mode: inline
    findings: none
  - persona: scope-boundary
    status: complete
    mode: inline
    findings: K3
  - persona: learnings
    status: complete
    mode: inline
    findings: none
  - persona: architecture
    status: complete
    mode: inline-same-model
    findings: K3, K4
  - persona: agent-native-parity
    status: complete
    mode: inline-same-model
    trigger: "Plan defines a machine-read gate artifact, a fail-closed token vocabulary an agent evaluates as its first action, and a four-state composed vocabulary a successor agent reads at 181-S harvest time."
    findings: K4, K5
  - persona: security-lens
    status: complete
    mode: inline-same-model
    trigger: "Plan defines credential-absence determination, untrusted external asset acquisition, adversarial containment probing, egress denial and a committed CI surface running on hosted runners."
    findings: K6
tags:
  - "plan-review"
  - "spike"
  - "ci-isolation"
  - "supply-chain"
  - "safe-close"
  - "portfolio-2026-09-18"
---

# Plan review attempt 04 — Conformance isolation spike (S2)

Attempt 03's two findings were **independently re-derived from plan, task,
feature and shipment records and from the working tree**. No closure summary
was trusted.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` |
| Reviewed revision | 4 |
| Reviewed content HEAD | `42f2f8ec` (committed) |
| Verdict at entry | `null`, disposition `REMEDIATED-PENDING-REVIEW` at plan revision 4 |
| Covering feature / shipment | `177-F` / `183-S` |
| Unit role | precursor spike, DAG root |
| External tracker | `002-C`, `blocked`, outside every manifest |
| Governing decision | 2026-09-18 shared-execution-architecture, revision 1 |
| Dispatch mode | `single-agent-declared-degradation` |
| Terminal | yes — operator-declared terminal attempt 04 |
| Gate result | **ADVISORY** |
| Decision | **ADVISORY** |

## Dispatch and coverage

All seven personas were applied inline, each with its own finding list.
Reviewer personas are leaf executors and spawned nothing. Engram remained
circuit-open and was not retried; intercom and graphtor-docs were unavailable,
so operator visibility was local-only.

## `I1_GATE` is a real fail-closed verdict predicate, not an ordering

This was attempt 03's `K1` and it is the critical question of the unit. It is
**closed**, and the closure is structural rather than rhetorical.

**The predicate is separated from the edge, explicitly and everywhere.** The
plan states that a `blocks` edge is a predicate over predecessor *completion*,
that `177.004-T` completes on three outcomes, and that two of the three leave
credential absence unverified or affirmatively falsified while still clearing
the edge. `H12`, `R8`, `R10`, the blast-radius section, both gated task
records, `177.001-T`, `177.006-T`, `177-F` and the `183-S` description all say
the edge is ordering and is **never** offered as the safety argument.

**The predicate is a verdict, carried inside the gated tasks.** The gate
artifact is a single non-secret line at
`docs/spikes/2026-09-18-conformance-isolation-i1-gate.md`, written by
`177.004-T` as the last action of its own run; `177.004-T` is the sole writer.

**OPEN and CLOSED are total and identical on every surface:**

| Result | Condition |
|---|---|
| OPEN | file exists, is readable, contains **exactly one** `I1_GATE:` line, token is `ACHIEVABLE` |
| CLOSED | **everything else** — missing file, unreadable file, no `I1_GATE:` line, more than one `I1_GATE:` line, unrecognised token, `NOT_ACHIEVABLE`, `FLOOR_INVOKED` |

**Acquisition and probe cannot touch untrusted material unless OPEN.** Both
gated tasks read the line as their *first* action, and the prohibition is
enumerated against the specific operations rather than left generic:
`177.005-T` performs no acquisition, download, redirect follow or network
request; `177.002-T` performs no handle creation, mount setup, substitution
attempt or probe of any kind. On CLOSED neither runs at all — "not deferred,
not retried, not narrowed".

**Closed paths force a floor-only, non-pass state, structurally.** On CLOSED,
`177.005-T` records `I7`, `177.002-T` records `I4`/`I5`/`I6`, and `177.001-T`
records `I2` (via the acquisition that never ran), each
`NOT DETERMINED — FLOOR INVOKED` naming `I1` as the blocker with all three
required parts. `ISOLATION_CHARACTERIZED` requires **all seven** properties
`DETERMINED`, so it is unreachable — not by a rule that must be remembered but
by the ledger's own arithmetic. `ISOLATION_FLOOR_ONLY` is declared explicitly
not a pass and authorizes only floor-only harvest. If a gated task records
fewer than the three parts, its row is `ABSENT` and the unit composes to
`ISOLATION_UNDETERMINED`, which blocks harvest outright. There is no third
path, and `177.006-T` independently treats a `DETERMINED` verdict on a gated
property under a CLOSED gate as itself a fail.

**`I3`'s exemption is correctly scoped.** Repository absence or read-only
mounting is observable without acquiring or probing anything untrusted, so
`177.001-T` determines it normally regardless of gate state. `177.001-T`
carries no gate read because it performs no untrusted acquisition and no
containment probe — which is verified against its own record and against the
plan's statement that acquisition occurs only inside `177.005-T`'s dispatch.

**Invariants and evidence remain non-secret and reachable.** The names-only
rule binds the `I1` inventory, the gate line, the findings artifact and every
job log; an inventory that would require a secret value to be meaningful is
itself the `NOT ACHIEVABLE` finding. The gate line carries a token, a verdict,
a short non-secret mechanism or reason identifier and a date — a reader learns
*whether* credential absence was established, never *what* any credential is.
The artifact is reachable: it lives under `docs/spikes/`, is written before the
`blocks` edges clear, and the edges exist precisely so it is present to be
read.

## Committed probe workflow lifecycle — complete

Attempt 03's `K2` is **closed**. Owner, exact path, own commit, dispatch model,
removal owner and point, abort-path removal, rollback and evidence are all
declared, and reproduced in the four affected task records, `177-F` and the
`183-S` description. The workflow is `workflow_dispatch`-only with an explicit
minimal `permissions:` block and no secrets, so it cannot fire on unrelated
branch activity. The path was verified **absent** from the working tree at
review time. Blast radius and rollback now name the one mutated tracked surface
truthfully rather than describing the spike as mutating nothing.

## Independent verification of plan-to-record correspondence

* Sizing and complexity match the plan's Tasks table on all six tasks
  (`177.004-T` S/medium, `177.005-T` S/medium, `177.001-T` S/medium,
  `177.002-T` S/high, `177.003-T` XS/low, `177.006-T` XS/low); each carries
  `size_source: agent` and a non-empty `size_ruleset_version`. `177.002-T`'s
  `complexity: high` carries the declared de-risking rationale the harvest
  contract requires, and the size axis is bounded independently at a
  120-minute elapsed bound.
* `item_deps` encodes the declared sequence exactly: `177.004-T` blocks both
  `177.005-T` and `177.002-T`; `177.005-T` blocks `177.001-T`; all four
  determining tasks block `177.003-T`; `177.003-T` blocks `177.006-T`.
* `183-S` manifest order is dependency order and leads with `177-F`.
* Every property `I1`–`I7` has an assigned **determining** task; `177.003-T`
  transcribes and determines none, and `177.006-T` checks that assignment
  structurally before it checks evidence.
* `183-S` is a DAG root with no incoming shipment edge; `181-S` depends on it,
  in the direction `gates: 181-S` asserts.
* `002-C` was read directly: `status: blocked`, top-level chore, no dependency
  edges in either direction, outside `183-S` and `181-S` manifests and outside
  `173-F` parentage. Unchanged by this unit under all four composed states.
* Source ID `7F9CB5E9` is carried by every executable record. Every
  cross-referenced path resolves.

## P0 findings

None.

## P1 findings

None.

## P2 findings (1)

### `K3` — the branch-cleanliness check has no expressible verdict, so it is a claim rather than an executable predicate

`177.006-T`'s record mandates a **fourth check**: confirm the findings artifact
records the creation commit SHA and path, the four dispatch run IDs and URLs,
the removal commit SHA, and a `git status --porcelain` observation showing
`.github/workflows/spike-177-isolation-probe.yml` absent from the branch tip;
and it states that a branch still carrying the workflow at spike close "is an
UNCLOSED SPIKE: record it as such and **emit no pass**".

The plan's composed-state vocabulary cannot express that instruction. The four
states are defined **exhaustively as functions of the coverage ledger**:
`ISOLATION_CHARACTERIZED` is "every property I1–I7 is `DETERMINED`",
`ISOLATION_FLOOR_ONLY` is "no property is `ABSENT`, and at least one is
`NOT DETERMINED — FLOOR INVOKED`", `ISOLATION_UNDETERMINED` is "one or more
properties is `ABSENT`", and `ISOLATION_NOT_OBSERVED` is a missing or
ledger-less artifact. Branch state appears in none of them, and the three
verdict line forms carry no field for it.

So an all-`DETERMINED` ledger on a branch that still carries the probe workflow
forces `ISOLATION_CHARACTERIZED` by the plan's own table while the task record
forbids a pass, and no token exists to express the outcome the record demands.

The plan and `R11` also say only that `177.006-T` "records it as such" — they
do not say it withholds the pass — so the plan and the record disagree on the
check's consequence as well as lacking a token for it.

This is the same defect *class* as `K1`: a stated safety expectation resting on
something that is not an executable predicate. It is graded **P2**, not P1,
because its consequence differs by an order of magnitude. `K1` governed whether
untrusted acquisition and adversarial probing could run against a job
environment whose credential absence was unverified. `K3` governs whether a
`workflow_dispatch`-only workflow, carrying a minimal `permissions:` block and
no secrets and incapable of firing on `push`, `pull_request` or `schedule`, is
left on a non-default chore branch with a declared owner and a one-commit
revert. No untrusted execution, no credential exposure and no successor
eligibility turns on it: the load-bearing safety mechanism — the `I1` verdict
predicate and the ledger-forced floor-only state — is intact and fully
expressible.

## P3 findings (3)

### `K4` — the plan enumerates two mechanical checks where the gate task performs four

The plan's *"The transition is executable and auditable"* paragraph states that
`177.006-T` performs the transition "in two checks": Coverage and Evidence. The
`177.006-T` record performs four, adding the `I1` gate check and the
branch-cleanliness check. The `I1` gate check is covered substantively elsewhere
in the plan (the *I1 gate* section's *composed state this forces*, `H13`, `R10`),
so this is an enumeration gap rather than a missing requirement — but a reader
who takes the "two checks" sentence as the gate's definition will under-specify
the task. Advisory.

### `K5` — the gate line's literal differs by a dash between the plan and its sole writer

The plan prints the third form as
`I1_GATE: FLOOR_INVOKED | verdict=NOT DETERMINED — FLOOR INVOKED | …` with an
em dash; `177.004-T`'s record prints `NOT DETERMINED - FLOOR INVOKED` with a
hyphen. The OPEN/CLOSED predicate keys on the **first field's token** only, and
both surfaces agree that the token is `FLOOR_INVOKED`, so the gate decision is
unaffected on either reading. Recorded because the line is machine-read and its
literal should not differ between the document that specifies it and the record
that writes it. Advisory.

### `K6` — `I2`'s evidence is observed in a job that performs no acquisition, and the weakening is not noted

`I2` is defined as "network egress denied **after** acquisition completes", and
its acceptance evidence is "a recorded egress attempt to a known-reachable
host, made **after** the acquisition observed in `177.005-T` completes". But
the *Probe workflow lifecycle* section states that "the workflow performs asset
acquisition only inside `177.005-T`'s dispatch", and `177.001-T`'s record
confirms it "performs NO untrusted acquisition" and dispatches its own separate
`i2-i3-egress` probe.

The "after" relation is therefore a *task-level* ordering across two separate
hosted-runner jobs, not an in-job `acquire → deny → probe` sequence. That is
the correct security posture — `177.001-T` deliberately carries no gate read
precisely because it touches nothing untrusted, and moving the acquisition into
its job would create an ungated untrusted acquisition, which would be a far more
serious finding. The plan is internally consistent about it. The finding is
only that the plan never notes that the observation supporting `I2` is
correspondingly weaker than its own definition reads, leaving `181-S` to inherit
a verdict whose evidentiary scope is narrower than stated. Advisory.

## Runtime verification and operational closure

Nothing in this unit was executed. No workflow was created, dispatched or
removed; no hosted-runner job was run; no asset was acquired. The review
performed no build, no test run and no linting, and created, claimed and closed
no shipment. `002-C` was read and not modified.

## Disposition

Gate result **ADVISORY**; decision **ADVISORY**. Zero P0, zero P1, one P2,
three P3.

Attempt 04 is the operator-designated terminal attempt. No remediation was
performed and **no further remediation cycle is proposed**. `K3` is an advisory
follow-up candidate that the operator may choose to dispose of before the unit
is executed; it does not block, because no policy in
`.github/policies/workflow-policies.md` makes a P2 plan-to-record divergence
blocking, and the unit's load-bearing safety predicate is sound.

No severity was raised to force a block or lowered to force a closure, and no
finding was closed on a closure summary.
