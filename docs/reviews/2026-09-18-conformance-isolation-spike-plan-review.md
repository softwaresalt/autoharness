---
title: "Plan review verdict manifest — Conformance isolation spike (S2)"
description: "Mutable verdict manifest for docs/plans/2026-09-18-conformance-isolation-spike-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. The reviews live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 01. Plan revision: 2. Independent attempt 01 reviewed revision 1 at content HEAD db39553a and returned gate result FAIL and verdict BLOCKED on one P0, one P1, two P2 and one P3 deduplicated finding. The P0 is that the declared pass state ISOLATION_CHARACTERIZED is unreachable under the plan's own task decomposition because property I1, no credentials in the job environment, is assigned to no determining task, so the spike terminates in its own fail state by construction. A Stage remediation cycle then produced plan revision 2, assigning I1 a determining task, adding an acquisition-observation task for I7, and adding a coverage and composed-state check, so latest_remediation_revision is 2 and latest_disposition is REMEDIATED-PENDING-REVIEW. The top-level verdict is null: a remediation revision supersedes the content attempt 01 judged, and no independent reviewer has judged revision 2. The findings remain counted open because only an independent attempt 02 can close them. The plan is not harvest-ready and not Ship-ready. No PASS exists anywhere in this record and none is asserted."
doc_type: review-manifest
source: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
date: 2026-09-18
manifest_shape: attempt-roster
plan_id: conformance-isolation-spike
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_revision: 2
feature_id: 177-F
shipment_id: 183-S
latest_attempt: 1
review_terminal: false
awaiting_attempt: 2
reviewed_content_head: db39553a
gate_result: FAIL
verdict: null
p0_open: 1
p1_open: 1
p2_open: 2
p3_open: 1
remediation_authorization: operator-authorized-single-cycle
latest_remediation_revision: 2
latest_disposition: REMEDIATED-PENDING-REVIEW
latest_artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-01.md
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
| `plan_revision` | 2 |
| `latest_attempt` | **01** |
| `latest_artifact` | `docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-01.md` |
| `reviewed_content_head` | `db39553a` |
| `gate_result` (attempt 01, immutable) | **FAIL** |
| `verdict` | **null** (derived — see below) |
| `latest_remediation_revision` | **2** |
| `latest_disposition` | **REMEDIATED-PENDING-REVIEW** |
| `awaiting_attempt` | **02** |
| `p0_open` | **1** |
| `p1_open` | **1** |
| `p2_open` | **2** |
| `p3_open` | **1** |

**The top-level `verdict` is derived, not authored.** Take the highest-numbered
roster entry — attempt 01. Its `remediation_revision` is now `2`, so a
Stage-produced revision **supersedes** the content the reviewer judged. The
reviewer's `BLOCKED` was returned against revision 1 and cannot be carried
forward as a judgement of revision 2, and no reviewer has judged revision 2.
The derived `verdict` is therefore **null**, and `latest_disposition` carries
what Stage actually produced: `REMEDIATED-PENDING-REVIEW`.

`REMEDIATED-PENDING-REVIEW` is a `disposition`, never a `verdict`. Writing it
into the `verdict` key would assert that a review concluded, which is precisely
the fabrication this two-column shape exists to prevent.

**The finding counts remain open.** One P0, one P1, two P2 and one P3 are still
counted open even though each was remediated. Stage remediating a finding is
not the same event as a reviewer confirming it closed, and only the latter
retires a finding. The counts drop when attempt 02 says they drop.

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

**The findings are not closed.** Closing them requires an independent attempt
02 against revision 2. This manifest asserts remediation and nothing more.

## Attempt roster

`reviewed_revision` + `verdict` are what an **independent reviewer** judged.
`remediation_revision` + `disposition` are what **Stage** produced in response.
They are separate columns because merging them is how a fabricated PASS enters
the record. `REMEDIATED-PENDING-REVIEW` is never a `verdict` value; it is only
ever a `disposition`.

| Attempt | Artifact | Reviewed rev | Reviewer verdict | Remediation rev | Disposition |
|---|---|---|---|---|---|
| **1** | `...-plan-review-attempt-01.md` | 1 @ `db39553a` | **BLOCKED** (1 P0, 1 P1, 2 P2, 1 P3) | 2 | `REMEDIATED-PENDING-REVIEW` |

## Provenance

* Plan: `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` at revision 2
* Feature: `177-F` — Shipment: `183-S` (queued, DAG root, no incoming edge)
* Shipment members after remediation: `177-F`, `177.001-T`, `177.002-T`,
  `177.003-T`, `177.004-T` (new, determines `I1`), `177.005-T` (new, observes
  the acquisition that `I7` is read off), `177.006-T` (new, coverage and
  composed-state validation)
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
