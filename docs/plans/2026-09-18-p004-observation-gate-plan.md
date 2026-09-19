---
title: "P-004 red-phase gate: three-channel observation over the declared harness set"
description: "Reduced current-state contract for the P-004 gate. Restores the compilation channel the gate had dropped, adds an explicit NO_OBSERVATION failed-precondition state distinct from PASS and from FAIL, and asserts exact set equality between declared and observed outcomes over the shipment's declared harness set. Consumes the installed harness-architect lifecycle from 187-S and the fixed-argv exec primitive from 185-S rather than assuming either. Bootstrap, schema, storage lifecycle, identity and MCP parity are no longer this unit's scope: they moved to the foundations that own them."
doc_type: plan
source: docs/plans/2026-09-18-p004-observation-gate-plan.md
date: 2026-09-18
plan_id: p004-observation-gate
plan_path: docs/plans/2026-09-18-p004-observation-gate-plan.md
plan_role: active
revision: 1
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document replacing the eight-attempt append history of p004-red-phase-precondition-scoping at architecture level. It awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-p004-observation-gate-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 76EBDE6D
feature_id: 168-F
shipment_id: 176-S
unit_role: reduced-defect-unit
supersedes_plan: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
depends_on_shipments:
  - 185-S
  - 187-S
task_reharvest_gate: 187-S
requires_plan_hardening: true
hardening_rationale: "Changes a policy gate that governs every shipment execution, and depends on two foundations whose surfaces are not yet built."
tags:
  - defect-unit
  - p004
  - gate
  - reduced-scope
---

# P-004 red-phase gate: three-channel observation

## Reduction

The previous revision of this unit carried its own bootstrap, its own schema,
its own storage lifecycle, its own identity model and its own MCP parity
surface. Attempt 08 recorded one P0 and eleven P1 findings across those
families, most of which were the same missing producers four units were each
inventing separately.

This revision keeps **one contract** and moves the rest to the foundations that
own them:

| Previously in scope | Now owned by |
|---|---|
| harness-architect bootstrap / assumed skill | `187-S` — installs the actual actor |
| fixed-argv command execution | `185-S` — PR-3 exec primitive |
| MCP parity for the gate | `184-S` — one registry, two transports |
| atomic record write | `185-S` — PR-1 |
| result identity and correlation | folded into the operation result model in `184-S` |

What remains is the defect that opened stash `76EBDE6D`.

## The defect

Live policy P-004's precondition already requires both:

```text
python -m py_compile src/autoharness/cli.py   → exit 0
python -m unittest discover                    → exit non-zero
```

and its postcondition records `Compilation: PASS` and `Red Phase: CONFIRMED`.

The implemented gate observes only the test-run channel. A file that fails to
compile produces a non-zero test run, which the gate reads as a satisfied red
phase. **A compilation failure is indistinguishable from a red test.** That is
a regression against live policy text, not a gap in the policy — so the remedy
restores an observation, and P-004's text is not amended.

## Contract

The gate observes **three channels** and classifies **totally**:

| Channel | Observation |
|---|---|
| Compilation | `py_compile` over the declared harness set exits 0 |
| Collection | every declared test module imports with zero loader errors and zero `_FailedTest` placeholders |
| Outcomes | observed outcome set equals declared outcome set, by exact set equality |

Declared outcomes admit two disjoint classes: **expected-red** and
**expected-green-characterization**. A test may be in exactly one.

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `RED_CONFIRMED` — compilation clean, collection clean, observed set equals declared set |
| Fail state | `RED_NOT_CONFIRMED` — all three channels observed, sets unequal |
| Third state | `NO_OBSERVATION` — a channel could not be observed (compilation failed, a module failed to import, or `HARNESS_READY` was not reached). **A failed precondition, never a pass and never a red.** |
| Producer | `187-S`'s `HARNESS_READY` state; `185-S`'s PR-3 exec primitive |
| Consumer | Ship's task-start sequence |
| Activation commit | one task, updating the gate, policy reference, template and installed mirror together |

`RED_CONFIRMED` is reachable: a shipment declaring a harness set of expected-red
tests that compile and import satisfies all three channels.

The load-bearing distinction is that `NO_OBSERVATION` is **not** `RED_CONFIRMED`.
The current defect is exactly the collapse of these two states.

## Rollout

**PREPARE (inert).** Three-channel observer and total classifier built and
tested while the live gate continues its single-channel behaviour.

**VERIFY.** Each of the three states observed reachable, including a compilation
failure yielding `NO_OBSERVATION` rather than `RED_CONFIRMED`.

**ACTIVATE.** One task, one commit: the gate, its policy cross-reference, the
Ship agent template and the installed mirror move together.

## Task re-harvest gate

Task-level decomposition of this unit is **deliberately deferred** until
`187-S` has installed the harness lifecycle and `185-S` has fixed the exec
primitive's signature. Naming a producer before it exists is the precise defect
this redesign eliminates; harvesting tasks against an assumed exec signature
would reintroduce it. The existing tasks under `168-F` remain queued and are
re-sliced against the delivered foundation surfaces, not against this document.

## Out of scope

* Amending policy P-004's text.
* Any waiver, force flag or operator policy edit as a bootstrap path — all
  three were evaluated and rejected in the architecture decision.
* Building the harness-architect skill. `187-S` installs it.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Restoring the compilation channel blocks shipments that pass today | Intended: those shipments are passing on an unobserved precondition. The transition surfaces as `NO_OBSERVATION` with a named channel rather than a silent failure. |
| R2 | Collection cleanliness is stricter than current practice | It is the same rule the foundation plans apply to their own RED modules, so the portfolio is internally consistent. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Can a compilation failure still read as a red phase? | Not after this change. Compilation is observed as its own channel, and a failure yields `NO_OBSERVATION`. The current defect is precisely the collapse of that state into `RED_CONFIRMED`. |
| H2 | Is a non-zero test-run exit sufficient evidence of a red phase? | No. It is satisfied by an import error, a collection error, a compilation failure, or a genuine red test. Only exact set equality between declared and observed outcomes distinguishes them. |
| H3 | Can a test be in both declared outcome classes? | No. Expected-red and expected-green-characterization are disjoint, and a test in both would make set equality unfalsifiable. |
| H4 | What if `HARNESS_READY` is never reached? | `NO_OBSERVATION`. The gate has not observed a pass, so it does not report one. This is why `187-S` is a hard predecessor rather than an assumption. |
| H5 | Does this unit need to change P-004's text? | No. The live precondition already requires both channels; the implementation regressed against it. Editing the policy to match the implementation would ratify the defect. |
| H6 | Why is task harvest deferred? | Because the exec primitive's signature is the gate's calling convention, and the harness lifecycle's state is its precondition. Harvesting against assumed shapes is the exact defect this redesign removes. |

### Blast radius

A policy gate on every shipment execution, plus the Ship agent template and its
installed mirror. Restoring the compilation channel will block shipments that
currently pass, which is intended — they are passing on an unobserved
precondition.

### Rollback

PREPARE is inert; the live single-channel gate continues until activation. The
ACTIVATE commit reverts as a unit across gate, policy cross-reference, template
and mirror.

### Verification floor

All three states observed reachable, including a compilation failure yielding
`NO_OBSERVATION` rather than `RED_CONFIRMED`. A suite that never observes
`NO_OBSERVATION` has not verified the fix.
