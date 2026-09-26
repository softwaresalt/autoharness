---
title: "Plan review attempt 02 — Conformance isolation spike (S2)"
description: "Immutable per-attempt plan-review artifact recording the second independent review of docs/plans/2026-09-18-conformance-isolation-spike-plan.md at revision 2, against reviewed content HEAD 5aa8643f. Gate result FAIL; decision BLOCKED on zero P0, one P1, one P2 and one P3 deduplicated finding. All five attempt-01 findings are independently verified closed: I1 and I7 now have determining tasks 177.004-T and 177.005-T, the property coverage table assigns every property a determining task and an evidence shape, 177.006-T checks that assignment structurally before it checks evidence, the complexity-high de-risking rationale is declared, producer and consumer are path-exact, and the verdict key is null. The new P1 is that the remediation introduced a security-ordering claim that its own records deny: the plan's blast radius and H7 both rest the probe-safety argument on I1 being determined before any probe job, while the task table, 177.004-T, 177.002-T and item_deps all state the opposite independence. Dispatch ran in single-agent declared degradation with all seven personas covered inline; engram indexed retrieval was circuit-open and intercom unavailable. No remediation was performed and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-02.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 2
attempt_range: "02"
attempt_conformance: conforming
review_terminal: false
verdict_manifest: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-01.md
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_id: conformance-isolation-spike
reviewed_revision: 2
reviewed_content_head: 5aa8643f
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
review_cycle: 2
dispatch_mode: single-agent-declared-degradation
anchor_route: absent
anchor_route_note: "No anchor_review key exists in .autoharness/config.yaml model_routing, so no cross-model anchor was dispatchable. The cross-model rubrics ran under same-model declared degradation. This is recorded, not compensated for."
model_route_note: "Stage role route resolved from .autoharness/config.yaml model_routing.stage (claude-opus-5/anthropic/high), re-read fresh at session start. The escalation route model_routing.escalation (gpt-5.6-sol/openai/high) is distinct from both the role route and tier3, so the same-route ESCALATION_DEGRADED guard does not fire. No escalation was triggered: no failure threshold was reached."
degraded_capabilities:
  - capability: reviewer-subagent-dispatch
    state: degraded
    note: "TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass. Every selected persona was applied inline with its own finding list, per the Persona Rubric Adapter. Reviewer personas are leaf executors and spawned nothing."
  - capability: agent-engram
    state: circuit-open
    note: "Indexed retrieval circuit open per operator instruction; not retried this session. All evidence below comes from bounded direct exact-path reads, git plumbing, and read-only backlogit SQL over a freshly synced index (1430 artifacts)."
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
verdict_at_entry_plan_revision: 2
remediation_authorization: none-this-cycle
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 0
p1_open: 1
p2_open: 1
p3_open: 1
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_sufficiency_note: "The hardening pass gained the structural coverage question H5 that attempt 01 required, and that question is genuinely answered. H7 nonetheless rests the probe-safety answer on an ordering property the decomposition denies, which is finding F1 below."
attempt_01_findings_verified:
  - finding: "A1 — declared pass state unreachable; I1 has no determining task"
    severity: P0
    state: closed
    evidence: "177.004-T created in 183-S (S/medium, 90 min) as I1's determining task, inspecting the actual job environment for variable names, credential-bearing paths, checkout credential persistence and the mechanism producing each absence. The Property coverage table assigns all of I1-I7 a determining task and an evidence shape; 177.006-T check (1) validates that assignment structurally before it checks evidence; hardening question H5 asks the structural coverage question by name."
  - finding: "A2 — I7 requires an observation that no task performs"
    severity: P1
    state: closed
    evidence: "177.005-T created (S/medium, 90 min) to perform one real release-asset acquisition and record the redirect chain verbatim; 177.003-T transcribes and determines nothing; item_deps carries 177.001-T depending on 177.005-T, so I2's egress denial follows a real acquisition. R5 makes an I7 row with no recorded chain ABSENT."
  - finding: "B1 — verdict key carries a value from the disposition enum"
    severity: P2
    state: closed
    evidence: "Plan frontmatter now sets verdict: null and disposition: REMEDIATED-PENDING-REVIEW; the verdict manifest does the same."
  - finding: "B2 — 177.002-T carries complexity high with neither split nor declared de-risking rationale"
    severity: P2
    state: closed
    evidence: "Plan section 'On 177.002-T carrying complexity: high' declares the de-risking rationale and argues both against splitting I4 away and against splitting I5 from I6; the same rationale is reproduced in the 177.002-T record, with the size axis bounded independently at S / 120 min."
  - finding: "C1 — composed-state check names producer and consumer in prose"
    severity: P3
    state: closed
    evidence: "Producer is docs/spikes/2026-09-18-conformance-isolation-findings.md and consumer is docs/plans/2026-09-18-safe-close-conformance-plan.md, both path-exact; the consumer path was verified to exist."
persona_coverage:
  - persona: constitution
    status: complete
    mode: inline
    findings: F1
  - persona: python
    status: complete
    mode: inline
    findings: none
  - persona: scope-boundary
    status: complete
    mode: inline
    findings: F3
  - persona: learnings
    status: complete
    mode: inline
    findings: F1, F2
  - persona: architecture
    status: complete
    mode: inline-same-model
    findings: F1, F2
  - persona: agent-native-parity
    status: complete
    mode: inline-same-model
    trigger: "Plan governs a CI surface whose verdict token an agent must read at 181-S harvest time."
    findings: none
  - persona: security-lens
    status: complete
    mode: inline-same-model
    trigger: "Plan governs credential exposure, network egress control, a verify-to-execute trust boundary, and acquisition of an untrusted external release binary."
    findings: F1
tags:
  - "plan-review"
  - "spike"
  - "ci-isolation"
  - "supply-chain"
  - "safe-close"
  - "portfolio-2026-09-18"
---

# Plan review attempt 02 — Conformance isolation spike (S2)

This artifact records **one thing**: an independent reviewer's verdict on plan
revision 2 as it stands at content HEAD `5aa8643f` on branch
`chore/stage-176-s-workflow-defects`. It has no Part 2. No remediation followed
it, and Stage asserts no `PASS`.

Attempt 01's claimed closures were **independently re-derived from plan, task
and manifest state**, not accepted from the remediation commit message or the
manifest narrative. All five are genuinely closed. The blocker below is new,
and it was introduced by the remediation.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` |
| Reviewed revision | 2 |
| Reviewed content HEAD | `5aa8643f` (committed) |
| Verdict at entry | `null`, disposition `REMEDIATED-PENDING-REVIEW` at plan revision 2 |
| Covering feature / shipment | `177-F` / `183-S` |
| Unit role | precursor spike, DAG root |
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
was skipped, and no persona spawned a subagent. Cross-model personas ran under
same-model declared degradation because `.autoharness/config.yaml` declares no
`anchor_review` route.

Security Lens was triggered with the strongest warrant in this portfolio and is
the persona that raises the blocker. Agent-Native Parity was triggered on the
ground that `181-S` must read the verdict token at harvest, and returned no
finding: the token vocabulary is consistent across plan and records
(`ISOLATION_CHARACTERIZED`, `ISOLATION_UNDETERMINED`,
`ISOLATION_NOT_OBSERVED` all appear in `177-F`, `177.001-T`, `177.002-T`,
`177.004-T` and `177.006-T`).

Engram indexed retrieval was circuit-open and was **not retried** per operator
instruction. Intercom was unavailable, so visibility is local-only.

## Independent verification of attempt-01 closures

**A1 (P0) — I1 had no determining task. Closed, and closed structurally.**
`177.004-T` exists in `183-S` at `S`/`medium` with a 90-minute bound. Its
record specifies inspection of the actual job environment from inside the job:
environment-variable names, credential-bearing filesystem paths, the checkout
action's credential-persistence setting, and the mechanism producing each
absence. Names-only evidence handling is binding in both plan and record, and
an inventory that would require a secret value to be meaningful is itself the
`NOT ACHIEVABLE` verdict — which is the right shape.

The fix is structural rather than incidental, which is what attempt 01 asked
for. The `## Property coverage` table assigns every one of I1–I7 a determining
task and a named evidence shape; `177.006-T`'s check (1) validates that
assignment — and that the assigned task is a determining task, "NEVER the
authoring task `177.003-T` alone" — **before** it checks evidence; and
hardening question H5 now asks the coverage question by name, correctly
observing that the previous pass "interrogated scope, evidence quality and
partial results without ever asking whether the decomposition could reach its
own pass state."

Reachability is restored. `ISOLATION_CHARACTERIZED` is satisfiable by seven
`DETERMINED` rows, and a `DETERMINED` row admits a `NOT ACHIEVABLE` verdict, so
the pass state does not require the isolation to succeed — only to be
characterized.

**A2 (P1) — I7 required an unperformed observation. Closed.** `177.005-T`
exists at `S`/`medium` with a 90-minute bound, performs one real release-asset
download, and records each hop's host and status, the terminal host, terminal
stability across attempts, and the capture tooling. `177.003-T` "reads off" the
rule and may not invent one; R5 resolves an I7 row with no recorded chain to
`ABSENT`. The second-order point attempt 01 raised is also closed:
`item_deps` carries `177.001-T` depending on `177.005-T`, so I2's
post-acquisition egress denial is established relative to an acquisition that
actually happened.

**B1 (P2) — verdict key. Closed.**

**B2 (P2) — `complexity: high` without a declared de-risking rationale.
Closed.** The plan carries a dedicated section, and the same rationale appears
in the `177.002-T` record. The argument is made properly rather than asserted:
I4 is the low-uncertainty member and costs nothing to carry, and splitting I5
from I6 would duplicate one handle setup rather than divide the risk.

**C1 (P3) — producer and consumer in prose. Closed.** Both rows are now
path-exact, and `docs/plans/2026-09-18-safe-close-conformance-plan.md` was
verified to exist.

## Independent verification of plan-to-record correspondence

`183-S` members are `177-F` plus `177.001-T` through `177.006-T`. Size and
complexity match the plan's task table on both axes for all six tasks:
`S`/`medium`, `S`/`high`, `XS`/`low`, `S`/`medium`, `S`/`medium`, `XS`/`low`.
Every task carries `size_source: agent` and a non-empty
`size_ruleset_version`.

The two-hour rule holds on the size axis for every task, and the elapsed bounds
(90/90/120/120/45/20) are declared individual. `177.002-T` is the single
`complexity: high` task and carries the declared de-risking step B2 required.

Root eligibility and gate direction hold: `183-S` has no incoming dependency
edge, and `181-S` depends on `183-S`, matching `gates: 181-S`.

The `002-C` boundary is intact and was re-verified: `item_deps` carries no edge
in either direction between `183-S` (or any `177.x` task) and `002-C`, the plan
refuses any administrative-close transition, and `.backlogit/queue/002-C.md` is
untouched by this review.

The security model is stated as a constraint the spike may not reopen, and the
one-directional floor — "the spike determines whether the unit rises above it,
never whether it drops below it" — is preserved.

## P0 findings

**None.** Attempt 01's P0 is genuinely closed, and no new finding reaches P0.

## P1 findings (1)

**F1 — the remediation introduced a security-ordering claim that its own
records deny. The probe-safety argument rests on I1 being determined before any
probe job; nothing enforces that, and three records state the opposite.**

The plan's `### Blast radius` section justifies the operational risk of the
determining tasks like this:

> The job that does so carries no credentials (**I1 is determined before any
> probe job is trusted to be safe**), executes nothing it acquires, and leaves
> no surviving state.

Hardening answer H7 makes the same ordering the answer to whether probing is
safe at all:

> **I1's determination is what keeps the probe honest**: a probe job that
> carried credentials would be a privileged process handling an untrusted
> artifact even without executing it.

That ordering is not encoded anywhere, and the plan and the records contradict
it in five places:

| Where | What it says |
|---|---|
| Plan, `## Tasks` sequence | "`177.004-T` and `177.002-T` are independent of both and of each other." |
| `177.004-T` record | "It is independent of `177.005-T`, `177.001-T` and `177.002-T` and **may run in any order relative to them**" — followed immediately, in the same record, by "Determining I1 before any containment probe is trusted to be safe is deliberate." |
| `177.002-T` record | "Independent of `177.004-T`, `177.005-T` and `177.001-T`." |
| `177.005-T` record | "Independent of `177.004-T` and `177.002-T`." |
| `item_deps` | No edge from `177.002-T` or `177.005-T` to `177.004-T`. The only edges in `183-S` are `177.001-T` ← `177.005-T`, all four determining tasks → `177.003-T`, and `177.003-T` → `177.006-T`. |

So `177.002-T` — the adversarial containment probe — and `177.005-T` — the task
that pulls a real external release asset onto a runner — are both free to
execute before I1 has been determined at all, in a job environment whose
credential absence is, by the plan's own standard, unverified. The safety
argument the hardening pass offers has a premise the manifest denies, and
`177.004-T` denies it in the sentence immediately preceding the one that
asserts it.

This is new. `177.004-T` did not exist at revision 1, so the claim could not
previously be made; the remediation that closed attempt-01's P0 introduced the
contradiction alongside the fix. It is also precisely the boundary attempt 01
flagged forward without grading, recording that the `I5`/`I6` probes are
"hands-on containment probes against a real handle … the boundary that A1's
missing `I1` determination would otherwise have helped police," and referring it
"for the remediation cycle's attention". The cycle added the task and then
declined to wire it.

It is the composition-defect class recorded in
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`:
every clause is defensible alone — independence is a reasonable scheduling
property, and I1-before-probe is a reasonable safety property — and the defect
exists only at their seam.

**Graded P1, not P0.** The declared pass state remains reachable, every
property has a determining task, the security model is not weakened, and no
task in the unit executes the untrusted binary, so the hazard the ordering
guards against is not realized by any specified action. **Graded P1, not P2**,
because the plan's adversarial pass uses this ordering as its answer to the
question of whether the probe is safe: a hardening answer whose premise the
executable record contradicts is not an advisory wording issue, and the
property at stake is the security-critical one the unit exists around.

*Recommendation — either, not both.*

1. **Enforce it.** Add `blocks` edges making `177.004-T` a predecessor of
   `177.002-T` and `177.005-T`, and rewrite the sequence paragraph and the
   three "independent of" sentences to match. This keeps H7's answer true.
2. **Withdraw it.** Remove the ordering claim from `### Blast radius`, H7 and
   the `177.004-T` record, and replace it with the property that actually
   holds — that every probe job is configured with the same minimized
   permissions and no-secrets shape `177.004-T` inspects, independent of when
   I1 is determined. This makes the hardening answer rest on a configuration
   invariant rather than on a schedule.

Option 1 is the smaller change and the stronger guarantee.

*Personas:* Security Lens Reviewer; Architecture Strategist; Learnings
Researcher; Constitution Reviewer (Principle III, Workspace Isolation and
Security Boundaries).

## P2 findings (1)

**F2 — "blocks `181-S` harvest" and "the floor stands either way" are asserted
as simultaneous consequences of the same state, and no fallback pass value
reconciles them.**

The composed-state section says `ISOLATION_UNDETERMINED` "blocks `181-S`
harvest", and then, four lines later:

> **`ISOLATION_UNDETERMINED` is not a blocker on the unit's usefulness.** The
> floor stands either way: `181-S` degrades to evidence-and-documentation only
> and `002-C` stays blocked.

`177.006-T` reproduces both sentences verbatim. They cannot both be operative:
a blocked harvest produces no `181-S` tasks at all, including the floor's, so
"degrades to evidence-and-documentation only" describes an outcome the block
prevents from being reached.

The sibling spike solves the identical problem and shows what is missing here.
`182-S` defines `NOT-ANSWERED-FALLBACK` as a **pass** value, available when a
finding is unreachable inside its elapsed bound, explicitly because it "carries
the R1 fallback in writing" and is therefore "a materially different input to
`184-S` than a silent gap". `183-S` has no equivalent: a determining task that
merely reaches its 120-minute bound records `NOT DETERMINED`, which is a fail,
which blocks the consuming unit outright.

The governing decision is **not** contradicted, which is why this is P2. R2's
trigger is "`S2` concludes hosted runners cannot deny egress post-acquisition"
— a *conclusion*, which resolves to `DETERMINED` with a `NOT ACHIEVABLE`
verdict, passes the gate, and reaches D5's floor normally. The decision's floor
is reachable. What is unreconciled is the plan's own pair of sentences about the
timeout case, which R2 does not cover.

*Recommendation.* Either add a `NOT-DETERMINED-FALLBACK` pass value mirroring
the sibling's treatment — recording what was attempted, what blocked it, and
invoking the evidence-and-documentation floor in writing for the affected
scope — or scope the second sentence so "the floor stands" describes `181-S`'s
ceiling once the property is determined or explicitly waived, rather than a
consequence available while harvest is blocked.

*Personas:* Architecture Strategist; Learnings Researcher.

## P3 findings (1)

**F3 — the `183-S` manifest `items` order is not dependency order.**

`custom_fields.items` reads `177-F`, `177.001-T`, `177.002-T`, `177.003-T`,
`177.004-T`, `177.005-T`, `177.006-T`, which lists `177.001-T` **before**
`177.005-T` that blocks it, and lists both independent determining tasks after
it.

Execution order is not wrong — `item_deps` is correct and a
dependency-ordered consumer runs the acquisition first — so this is advisory.
It is recorded because it is the same defect class attempt 01 raised as `D1`
against `177-S`, where the remediation fixed the ordering and declared
"MANIFEST ORDER IS PHASE ORDER" in the shipment description, without
propagating that treatment to either spike manifest.

*Recommendation.* Reorder `items` to dependency order, or state in the `183-S`
description that `item_deps` is authoritative for sequence.

*Personas:* Scope Boundary Auditor.

## Runtime verification and operational closure

Called out explicitly, as the gate requires.

The unit produces a document and declares `Activation commit | None`, so there
is no runtime surface to verify and no closure evidence to produce in this
unit. That is correct for a spike.

The operational qualifier attempt 01 recorded still applies and is now the
subject of `F1` rather than a forward note: the determining tasks do run real
CI jobs that acquire a real external asset and probe containment. The plan
acknowledges this in its blast-radius section. What it does not do is make the
acknowledgement's stated precondition true.

## Disposition

**No remediation.** `remediation_revision` is `null`, `disposition` is `null`,
and the governing revision remains 2 — the revision reviewed and found
BLOCKED.

This plan is **not harvest-ready and not Ship-ready**. No backlog record,
source file, test, template, CI definition or configuration was changed on the
strength of this review; in particular no dependency edge was added, because
adding one is remediation and no remediation is authorized in this cycle.

Closing `F1` requires a Stage remediation cycle producing revision 3, followed
by an independent attempt 03. `F2` and `F3` are advisory and may be carried or
closed in the same cycle.
