---
title: "Plan review verdict manifest — Conformance isolation spike (S2)"
description: "Mutable verdict manifest for docs/plans/2026-09-18-conformance-isolation-spike-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. The reviews live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 02. Plan revision: 3. Independent attempt 01 reviewed revision 1 at content HEAD db39553a and returned FAIL/BLOCKED on one P0, one P1, two P2 and one P3. A Stage remediation cycle produced revision 2, and independent attempt 02 reviewed that revision at content HEAD 5aa8643f, verified all five attempt-01 findings closed in plan, task and manifest state, and returned gate result FAIL and verdict BLOCKED on zero P0, one P1, one P2 and one P3 new finding. A second operator-authorized Stage remediation cycle has since produced revision 3, which closes F1 by making 177.004-T an enforced prerequisite of 177.002-T and 177.005-T with real blocks edges rather than by withdrawing the safety claim, closes F2 by replacing the single ISOLATION_UNDETERMINED reading with a four-state machine whose floor-only state is explicitly not a pass, and closes F3 by reordering the 183-S manifest into dependency order. That revision is UNREVIEWED: its disposition is REMEDIATED-PENDING-REVIEW and it awaits independent attempt 03. The plan is not harvest-ready and not Ship-ready. No PASS exists anywhere in this record and none is asserted."
doc_type: review-manifest
source: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
date: 2026-09-18
manifest_shape: attempt-roster
plan_id: conformance-isolation-spike
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_revision: 3
feature_id: 177-F
shipment_id: 183-S
latest_attempt: 2
review_terminal: false
awaiting_attempt: 3
reviewed_content_head: 5aa8643f
gate_result: FAIL
verdict: null
verdict_is_pass: false
p0_open: 0
p1_open: 1
p2_open: 1
p3_open: 1
remediation_authorization: operator-authorized-single-cycle
latest_remediation_revision: 3
latest_disposition: REMEDIATED-PENDING-REVIEW
latest_artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-02.md
attempts:
  - attempt: 1
    artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-01.md
    reviewed_revision: 1
    reviewed_content_head: db39553a
    verdict: BLOCKED
    p0_open: 1
    p1_open: 1
    p2_open: 2
    p3_open: 1
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: 2
    disposition: REMEDIATED-PENDING-REVIEW
    terminal: false
    findings_state: closed-at-attempt-02
  - attempt: 2
    artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-02.md
    reviewed_revision: 2
    reviewed_content_head: 5aa8643f
    reviewed_branch: chore/stage-176-s-workflow-defects
    verdict: BLOCKED
    p0_open: 0
    p1_open: 1
    p2_open: 1
    p3_open: 1
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: 3
    disposition: REMEDIATED-PENDING-REVIEW
    terminal: false
    closed_predecessor_findings: [A1, A2, B1, B2, C1]
carried_forward_context: []
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
external_tracker: 002-C
external_tracker_state: blocked-outside-shipment
tags:
  - "plan-review"
  - "verdict-manifest"
  - "portfolio-2026-09-18"
---

# Verdict manifest — Conformance isolation spike (S2)

This file is a **selection surface**, not a review. It names which immutable
attempt artifact is authoritative right now, and nothing else.

## Current verdict

| Field | Value |
|---|---|
| `plan_id` | `conformance-isolation-spike` |
| `plan_path` | `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` |
| `plan_revision` | 3 |
| `latest_attempt` | **02** |
| `latest_artifact` | `docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-02.md` |
| `reviewed_content_head` | `5aa8643f` |
| `gate_result` (attempt 02, immutable) | **FAIL** |
| `verdict` | **null** (derived — see below) |
| `verdict_is_pass` | **false** |
| `latest_remediation_revision` | **3** |
| `latest_disposition` | **REMEDIATED-PENDING-REVIEW** |
| `awaiting_attempt` | **03** |
| `p0_open` | **0** |
| `p1_open` | **1** |
| `p2_open` | **1** |
| `p3_open` | **1** |

**The top-level `verdict` is derived, not authored.** Take the highest-numbered
roster entry — attempt 02. Its `remediation_revision` is now **3**, so the
content attempt 02 judged (revision 2 at `5aa8643f`) has been superseded by
Stage and the reviewer's BLOCKED no longer describes the current plan text.
A superseded reviewer verdict may not be carried forward as the manifest's
verdict, and Stage may not author a replacement, so `verdict` is **null** and
the current state of the plan is the *disposition*
**`REMEDIATED-PENDING-REVIEW`**, which is not a verdict and is never a pass.
Attempt 02's own `gate_result` of **FAIL** against revision 2 remains immutable
in the history artifact; it is reproduced above as the last independent
judgement on record, not as a judgement of revision 3.

**`p1_open`, `p2_open` and `p3_open` above are attempt 02's counts, not
current counts.** They stay at 1/1/1 because only an independent attempt 03 can
decrement them. Stage's revision-3 remediation claims F1, F2 and F3 are
addressed; that claim is recorded under "What follows attempt 02" below and
carries no authority until attempt 03 re-derives it from plan, task and
manifest state.

**The attempt-01 counts are closed, and by the only authority that can close
them.** Attempt 01's P0, P1, two P2 and P3 were remediated by Stage and are now
recorded closed because an *independent* attempt 02 re-derived each one from
plan, task and manifest state rather than accepting the remediation narrative.
The open counts above are attempt 02's **own, new** findings.

**Remediation has not converged.** Revision 2 closed every attempt-01 finding
and introduced a new P1 doing it. Revision 3 addresses that P1 and its two
coupled findings, but is itself unreviewed. `awaiting_attempt` is **03**, and no
Ship work is authorized against `183-S` or anything downstream of it.

## What attempt 01 records

Independent first review opened against plan revision 1 at content HEAD
`db39553a`; gate result FAIL, decision BLOCKED, one P0, one P1, two P2 and one
P3 open.

Persona coverage was complete across all seven personas (Constitution, Python,
Scope Boundary, Learnings, Architecture, Agent-Native Parity, Security Lens).
Reviewer subagent dispatch was unavailable, so every persona ran as a declared
inline pass with its own finding list; `.autoharness/config.yaml` declares no
`anchor_review` route, so the cross-model rubrics ran same-model. Engram
indexed retrieval was circuit-open and was not retried, and intercom was
unavailable, so visibility was local-only. All evidence was gathered by bounded
direct exact-path reads, `git` plumbing, and read-only backlogit SQL.

**The P0 (`A1`)** is that the plan's declared pass state is unreachable under
its own decomposition. The plan states every property `I1`–`I7` "is classified
ACHIEVABLE or NOT ACHIEVABLE by this spike. None is assumed", and defines
`ISOLATION_UNDETERMINED` as any property left unclassified, adding that a
partially-classified result "is a **fail**, not a partial pass". But
`177.001-T` determines `I2`/`I3`, `177.002-T` determines `I4`/`I5`/`I6`, and
`177.003-T` is an authoring task — **no task determines `I1`**, "No credentials
of any kind in the job environment". The plan's own `R3` and `H2` forbid a
verdict resting on assertion rather than an observed mechanism, so the
authoring task cannot absorb it. Executed as decomposed, the spike terminates
in its own fail state. This is the defect class recorded in
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`
and the one decision D6 exists to catch before harvest; it is graded P0 both
because the contract is broken rather than incomplete and because `I1` is the
security-critical property deciding whether an untrusted binary shares an
environment with a readable token.

**The P1 (`A2`)** is the same structural gap on `I7`: the redirect rule must be
"derived from observed acquisition behaviour", but no task performs an
acquisition, so the rule replacing attempt-08 `B6`'s unsatisfiable rule would
itself be derived from assumption.

The two P2s are the `verdict`-key enum defect (`B1`, graded P2 only because the
manifest-reading consumer does not yet exist) and `177.002-T` carrying
`complexity: high` with neither a split nor a declared de-risking rationale
(`B2`). The P3 is that the composed-state check names producer and consumer in
prose rather than by path.

Attempt 01 also recorded, positively, that the plan's attempt-08 citations of
`B3`, `B4` and `B6` are exact; that the `002-C` boundary is stated exactly as
D5 requires and is confirmed in `item_deps` (no edge in either direction);
that the degradation floor is correctly one-directional; that hardening is
declared and present; and that the three `177.x` task records in `183-S` match
the plan's task table on both size and complexity.

## What follows attempt 01

A Stage remediation cycle, authorized by the operator as a single bounded
cycle, produced **plan revision 2**. What the revision changed, per finding:

* **A1 (P0)** — `I1` now has a determining task. New `177.004-T` inspects the
  **actual job/container environment** and records objective evidence:
  environment-variable **names only**, mount and path presence or absence, and
  the identity the job runs as. It does not read values, so the observation
  cannot itself leak the credential it is looking for. The property is
  determined by observation, not by assertion, which is what `R3` and `H2`
  require and what the authoring task could never supply.
* **A2 (P1)** — new `177.005-T` performs **one real release-asset
  acquisition** and records the redirect chain it actually follows. The `I7`
  allowlist and pinning rule is then **read off that recorded chain** by
  `177.003-T`, which may not invent one. No assumption-derived redirect policy
  can enter, which is the defect attempt-08 `B6` first recorded. `I2` was also
  redefined to be evaluated **after** the observed acquisition, so the
  acquisition and the egress denial no longer contradict each other.
* **A1 and A2, structurally** — a new `## Property coverage` table assigns
  every property `I1`–`I7` a determining task and a named evidence shape, and
  states explicitly that `177.003-T` **transcribes only**. New `177.006-T`
  runs the coverage and composed-state check: first that every property *has*
  a determining task, then that every ledger row is `DETERMINED`, emitting
  `ISOLATION_CHARACTERIZED` or `ISOLATION_UNDETERMINED`. The structural check
  runs first on purpose — it is what would have caught `A1` before harvest.
  A third `ISOLATION_NOT_OBSERVED` state prevents an unrun spike from being
  scored as a determined one.
* **B1 (P2)** — the plan's `verdict` frontmatter key is now `null`, with the
  disposition value moved to a `disposition` key where it belongs.
* **B2 (P2)** — `177.002-T` retains `complexity: high` and now carries the
  **declared de-risking rationale** attempt 01 named as an acceptable answer:
  the three properties `I4`/`I5`/`I6` share one container harness, so splitting
  them would triple setup cost without reducing uncertainty, and the
  uncertainty is concentrated in a single question the task states up front.
* **C1 (P3)** — the composed-state check now names producer and consumer **by
  path** rather than in prose.

The **security model is preserved exactly** and is now stated as a constraint
rather than a question: isolated Linux container, no credentials, restricted
and disposable mounts, post-acquisition network denial, containment over
verification. A property that proves unachievable moves `181-S` to the
evidence-and-documentation floor; it never relaxes the requirement. The
degradation floor remains one-directional.

`002-C` is unchanged: still `blocked`, still outside every manifest, still with
no dependency edge in either direction.

The plan was rewritten as a single coherent current-state document. It carries
no correction log and no review addendum: the remediation narrative lives here,
in the mutable manifest, which is the surface designed to hold it.

**The findings were not closed by that remediation.** Closing them required an
independent attempt 02 against revision 2, which is recorded below.

## What attempt 02 records

Independent second review opened against plan revision 2 at content HEAD
`5aa8643f` on branch `chore/stage-176-s-workflow-defects`; gate result
**FAIL**, decision **BLOCKED**, zero P0, one P1, one P2 and one P3 open.

Persona coverage was complete across all seven personas, with Agent-Native
Parity and Security Lens both triggered and run. Dispatch was again
`single-agent-declared-degradation` with no `anchor_review` route; engram
indexed retrieval was circuit-open and not retried; intercom was unavailable,
so visibility was local-only. Evidence came from bounded direct exact-path
reads, `git` plumbing, and read-only backlogit SQL over a freshly synced index.

**All five attempt-01 findings are verified closed**, each re-derived from the
executable surface rather than accepted from the remediation narrative:

* **A1 (P0)** — `177.004-T` exists, is a member of `183-S`, and determines
  `I1` by enumerating the job environment from a running job rather than
  asserting it; `I1` now has a determining task and the pass state
  `ISOLATION_CHARACTERIZED` is reachable.
* **A2 (P1)** — `177.005-T` exists and performs a real acquisition, so the
  `I7` redirect rule is derived from observed behaviour, not assumption.
* **B1 (P2)** — `verdict: null` with the disposition on its own key.
* **B2 (P2)** — `complexity: high` now carries explicit de-risking: the unit
  is a spike, every task is time-boxed, and `177.006-T` validates coverage and
  composed state before any verdict is emitted.
* **C1 (P3)** — producer/consumer relationships are tabulated rather than
  left in prose.

Correspondence was re-verified independently: all six `177.x` tasks match the
plan's table on both size and complexity; `183-S` has no incoming edge and
`181-S` depends on it, in the direction the plan asserts; `002-C` remains
`blocked`, outside every manifest, with no dependency edge in either direction.

**The open P1 (`F1`) is new and was introduced by the remediation.** The plan's
`### Blast radius` and hardening answer `H7` rest the probe-safety argument on
a claim of ordering — that `I1` "is determined before any probe job is trusted
to be safe". Four independent records deny it: the plan's own task sequence,
`177.004-T`'s body (which says it "may run in any order relative to them"
immediately before the contradicting sentence), `177.002-T`'s and `177.005-T`'s
bodies, and `item_deps`, which carries no edge from either probe task to
`177.004-T`. It is graded P1 rather than P0 because the pass state is still
reachable, the security model is not weakened, and no task executes an
untrusted binary — but a safety argument the executable record contradicts is
not a safety argument. The remedy is a choice of two: add `blocks` edges from
`177.004-T` to `177.002-T` and `177.005-T`, **or** withdraw the ordering claim
from the blast radius, `H7` and `177.004-T`.

**The P2 (`F2`)** is that `ISOLATION_UNDETERMINED` is asserted to block `181-S`
harvest *and* to leave the degradation floor standing, in both the plan and
`177.006-T`, with no `NOT-DETERMINED-FALLBACK` pass value to carry the second
reading; the sibling `182-S` plan solves the identical shape with
`NOT-ANSWERED-FALLBACK`. Decision `R2`/`D5` are not contradicted, because
`R2`'s trigger is a *conclusion* rather than a non-conclusion, so the floor
stays reachable — hence P2. **The P3 (`F3`)** is that the `183-S` manifest
`items` array is not in dependency order; `item_deps` is correct, so this is
presentational.

## What follows attempt 02

A second Stage remediation cycle, authorized by the operator as a single
bounded cycle, produced **plan revision 3**. What the revision changed, per
finding:

* **F1 (P1)** — resolved by **enforcing the ordering, not withdrawing the
  claim**. `177.004-T` is now a real prerequisite of both untrusted-work tasks:
  `item_deps` carries `177.002-T → 177.004-T` and `177.005-T → 177.004-T`, and
  the two task records carry the matching `dependencies` frontmatter. The
  plan's task-sequence paragraph, `177.004-T`'s body (the "may run in any order
  relative to them" sentence is gone), `177.002-T`'s and `177.005-T`'s bodies,
  hardening answer `H7`, the `### Blast radius` paragraph and the `183-S`
  manifest ordering now all state the same thing: the credential-environment
  inspection is observed **before** any acquisition or probe job runs. The
  safety claim is stronger than it was, and the executable record now carries
  it rather than contradicting it. Hardening answers `H9` and `H10` and risk
  `R8` were added to state the enforced edge and what happens if `I1` comes
  back adverse.
* **F2 (P2)** — resolved by **defining the missing transition rather than
  copying the sibling's pass value**. `182-S`'s `NOT-ANSWERED-FALLBACK` is a
  *pass* value, and importing it here would assert a proven isolation floor
  that nothing observed. The composed-state check is now a **four-state
  machine**: `ISOLATION_CHARACTERIZED` (the only pass — every property
  `DETERMINED`), `ISOLATION_FLOOR_ONLY` (every property determined, at least
  one determined **NOT ACHIEVABLE** — explicitly **not a pass**, permits only
  the evidence-and-documentation floor harvest of `181-S`),
  `ISOLATION_UNDETERMINED` (any row `ABSENT` — blocks `181-S` harvest entirely
  and names the absent rows) and `ISOLATION_NOT_OBSERVED` (evaluated first,
  covers an unrun spike and an absent verdict line, never a pass). A
  "Successor eligibility, stated per state" table makes successor eligibility
  unambiguous for each of the four; a fail-closed default states that silence
  never produces eligibility; and three explicit verdict-line forms remove the
  formatting ambiguity. The ledger gained a third value, `NOT DETERMINED —
  FLOOR INVOKED`, which requires all three of what was attempted, what blocked
  it, and a written statement that the property is unproven and the floor is
  invoked — anything less is `ABSENT`. No state presents the floor as proven
  and no PASS is fabricated. Risks `R1` and `R9` and hardening `H4` were
  reworded to match.
* **F3 (P3)** — the `183-S` manifest `items` array is now in dependency order:
  `177-F`, `177.004-T`, `177.005-T`, `177.001-T`, `177.002-T`, `177.003-T`,
  `177.006-T`. No dependency edge changed; the DAG is identical and the
  reordering only makes it readable top to bottom. `183-S` gained a description
  stating that the manifest order **is** dependency order and why `177.004-T`
  leads it.

`002-C` is unchanged under all four composed states: still `blocked`, still
outside every manifest, still with no dependency edge in either direction. The
degradation floor remains one-directional, and `183-S` remains a DAG root with
no incoming edge and `181-S` still depending on it.

The plan was rewritten as a single coherent current-state document. It carries
no correction log and no review addendum: the remediation narrative lives here,
in the mutable manifest, which is the surface designed to hold it.

**The findings are not closed by this remediation.** Closing them requires an
independent attempt 03 against revision 3.

## Attempt roster

`reviewed_revision` + `verdict` are what an **independent reviewer** judged.
`remediation_revision` + `disposition` are what **Stage** produced in response.
They are separate columns because merging them is how a fabricated PASS enters
the record. `REMEDIATED-PENDING-REVIEW` is never a `verdict` value; it is only
ever a `disposition`.

| Attempt | Artifact | Reviewed rev | Reviewer verdict | Remediation rev | Disposition |
|---|---|---|---|---|---|
| 1 | `...-plan-review-attempt-01.md` | 1 @ `db39553a` | **BLOCKED** (1 P0, 1 P1, 2 P2, 1 P3) | 2 | `REMEDIATED-PENDING-REVIEW` |
| **2** | `...-plan-review-attempt-02.md` | 2 @ `5aa8643f` | **BLOCKED** (0 P0, 1 P1, 1 P2, 1 P3) | 3 | `REMEDIATED-PENDING-REVIEW` |

## Provenance

* Plan: `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` at revision 3
* Feature: `177-F` — Shipment: `183-S` (queued, DAG root, no incoming edge)
* Shipment members after remediation, in manifest (dependency) order: `177-F`,
  `177.004-T` (determines `I1`; enforced prerequisite of the two untrusted-work
  tasks), `177.005-T` (observes the acquisition that `I7` is read off),
  `177.001-T`, `177.002-T`, `177.003-T` (transcribes only), `177.006-T`
  (coverage and four-state composed-state validation)
* External tracker: `002-C`, `blocked`, outside every manifest, no dependency
  edge in either direction — unchanged by this review
* Governing decision: the 2026-09-18 shared-execution-architecture and
  portfolio-reslicing decision, revision 1

## Authority

Latest attempt and verdict are read from this manifest, never from the plan
body. Per-attempt reviews live one per attempt under
`docs/reviews/review-history/` and are never edited afterwards. A disagreement
between `latest_attempt`/`latest_artifact` and the roster derivation above is
`REVIEW_VERDICT_AMBIGUOUS`, not a matter of narrative.
