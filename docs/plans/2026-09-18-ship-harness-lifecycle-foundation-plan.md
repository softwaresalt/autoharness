---
title: "Foundation: Ship pre-task harness-generation lifecycle"
description: "Installs the actor that policy P-004 already names but the workspace does not contain. Generates .github/skills/harness-architect/ from its existing template, adds a real pre-task harness-generation step to the Ship agent template and installed mirror, and defines the lifecycle states including an explicit NO_HARNESS failed-precondition state. Closes the assumed-skill bootstrap gap at its root so the P-004 gate work in 176-S consumes an installed producer instead of an assumption."
doc_type: plan
source: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
date: 2026-09-18
plan_id: ship-harness-lifecycle-foundation
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_role: active
revision: 1
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document authored under the strategic redesign, not a remediation of a prior revision. It carries REMEDIATED-PENDING-REVIEW because it awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 3EF5AAF2
feature_id: 181-F
shipment_id: 187-S
unit_role: precursor-foundation
depends_on_shipments:
  - 184-S
gates:
  - 176-S
requires_plan_hardening: true
hardening_rationale: "Modifies the Ship agent lifecycle itself and installs a new skill into the global harness. Every future shipment execution passes through the step this unit adds, so a defect here is a defect in every subsequent execution."
tags:
  - foundation
  - ship-lifecycle
  - harness-architect
  - p004-bootstrap
  - precursor
---

# Foundation: Ship pre-task harness-generation lifecycle

## Problem frame

Installed policy `.github/policies/workflow-policies.md`, policy P-004:

> **Applies To:** `ship` (via harness-architect skill)

The workspace contains eighteen installed skills under `.github/skills/`.
**`harness-architect` is not one of them.** The template exists —
`templates/skills/harness-architect/SKILL.md.tmpl` — but it has never been
generated into the installed harness.

So the installed policy names an actor the installed workspace does not
contain. Attempt-08 recorded this against `176-S` as the bootstrap family
(`B1`, `B2`): the P-004 gate work assumes a producer that no unit builds.

There were four ways to make that assumption go away. Three were rejected by
the architecture decision:

| Rejected | Why |
|---|---|
| Waiver | Suspends the gate for the case it exists to catch. |
| Force flag | An override reachable by the agent it constrains is not a gate. |
| Edit the policy to drop the actor | Deletes the requirement rather than satisfying it, and P-004's live precondition is correct as written. |

The chosen path is the remaining one: **install the actor**.

## What P-004 already requires

The live policy's precondition is not vague and does not need amending:

> `python -m py_compile src/autoharness/cli.py` exits 0 **and**
> `python -m unittest discover` exits non-zero

and its postcondition records `Compilation: PASS` and `Red Phase: CONFIRMED`.

This matters for scope: attempt-08's P0 on `176-S` (the gate omits the
compilation channel) is a **regression against live policy**, not a gap in it.
`176-S` restores the observation; this unit supplies the actor that runs it.

## Contract

The Ship agent gains a **pre-task harness-generation step**, executed before
the first task of a shipment is started:

1. Determine the harness surfaces the shipment's tasks require.
2. If a required skill surface is absent from `.github/skills/`, generate it
   from its authoritative template.
3. Record the generation outcome as a typed lifecycle state.
4. If generation is not possible, halt with `NO_HARNESS`.

This is a **real installed lifecycle step in the Ship agent**, not a
documentation note and not an assumption recorded in a plan.

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `HARNESS_READY` — every required skill surface present in `.github/skills/` and matching its authoritative template |
| Fail state | `NO_HARNESS` — a required surface is absent and could not be generated; **an explicit failed precondition, never silent success and never an implicit pass** |
| Producer | the pre-task lifecycle step (`181.003-T`) |
| Consumer | the P-004 gate in `176-S`; Ship's own task-start sequence |
| Activation commit | `181.005-T` |

`HARNESS_READY` is reachable today for the only surface currently required:
`harness-architect` has a complete template, so generation has a real source.

`NO_HARNESS` is distinct from a policy failure. A gate that cannot observe its
precondition has **not** observed a pass — this is the same
`NO_OBSERVATION`-is-not-`PASS` rule the P-004 gate work in `176-S` applies to
its three observation channels.

## Rollout

**PREPARE (inert).** `181.001-T` through `181.003-T`. The lifecycle step and
its tests exist; the Ship agent does not yet invoke it, and no policy or gate
depends on it. Live shipment execution is unchanged.

**VERIFY.** `181.004-T` — RED assertions observed failing, then passing, and
`harness-architect` observed generating from its template into a scratch
harness root without touching `.github/skills/`.

**ACTIVATE.** `181.005-T` — **one task, one commit**: generate
`.github/skills/harness-architect/SKILL.md` from its template, and add the
pre-task lifecycle step to **both** `templates/agents/_ship.agent.md.tmpl`
and `.github/agents/_ship.agent.md`, simultaneously.

> Splitting this across commits produces a reachable state in which the
> installed Ship mirror has a lifecycle step its template does not declare, or
> the skill is installed while no lifecycle step invokes it. Sequential task
> edges are not atomic.

## Tasks

| ID | Phase | Task | Size | Cx |
|---|---|---|---|---|
| `181.001-T` | RED | lifecycle-state tests incl. `NO_HARNESS` reachability | S | medium |
| `181.002-T` | PREPARE | harness-surface requirement resolver | S | medium |
| `181.003-T` | PREPARE | pre-task harness-generation lifecycle step | M | high |
| `181.004-T` | VERIFY | generation evidence against the `harness-architect` template | XS | low |
| `181.005-T` | ACTIVATE | one commit: install skill + add step to template and mirror | M | high |

Edges: `181.001-T` → `181.002-T` → `181.003-T` → `181.004-T` → `181.005-T`.

## Out of scope

* The P-004 gate's own three-channel observation logic — `176-S` owns it and
  consumes this unit's `HARNESS_READY` state.
* Any edit to policy P-004's text. Its precondition is correct as written;
  this unit satisfies it rather than changing it.
* Generating any other absent skill surface. The resolver is general; only
  `harness-architect` is required by this portfolio, and installing more would
  widen the activation commit beyond its contract.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | The `harness-architect` template is stale relative to current skill conventions | `181.004-T` generates it and validates frontmatter and structure before activation; a stale template fails VERIFY rather than landing broken. |
| R2 | The lifecycle step slows every shipment start | The resolver short-circuits when all required surfaces are already present, which is the steady state after the first execution. |
| R3 | `NO_HARNESS` becomes a routine blocker | It is only reachable when a required surface has no authoritative template. The resolver reports the missing template path, so the remedy is explicit rather than a retry loop. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Is generating a skill from a template really the bootstrap, or just a copy? | It is the bootstrap only if the generated surface is the one policy names. `181.004-T` validates the generated skill's frontmatter and structure before activation, so a stale template fails VERIFY rather than installing a non-functional actor. |
| H2 | Could `NO_HARNESS` be silently treated as a pass? | It is a distinct terminal state, and the P-004 gate in `176-S` consumes it as a failed precondition. The rule is the same one this portfolio applies everywhere: an unobserved precondition is not a satisfied one. |
| H3 | Does this unit amend policy P-004? | No, and it must not. P-004's precondition already requires `py_compile` exit 0 and a non-zero test run. The defect is an implementation that stopped observing one channel. Amending the policy would delete the requirement instead of satisfying it. |
| H4 | Why not a waiver or a force flag? | Both were evaluated and rejected. A waiver suspends the gate for exactly the case it exists to catch, and an override reachable by the agent it constrains is not a gate. |
| H5 | Does the lifecycle step run on every task? | Pre-task, per shipment, short-circuiting when all required surfaces are present — which is the steady state after first execution. A per-task full re-resolution would be a cost with no added guarantee. |
| H6 | Could the resolver install surfaces beyond the one required? | It is general, but only `harness-architect` is required by this portfolio. Installing more would widen the ACTIVATE commit past its stated contract and is out of scope. |

### Blast radius

The Ship agent lifecycle itself, in both template and installed form, plus one
new installed skill. Every future shipment execution passes through the added
step, so a defect is a defect in all subsequent execution.

### Rollback

`181.001-T`–`181.004-T` are inert. `181.005-T` reverts as a unit: the installed
skill and the lifecycle step in template and mirror disappear together, which is
the only rollback that cannot leave a lifecycle step invoking an absent skill.

### Verification floor

`HARNESS_READY` and `NO_HARNESS` both observed reachable. A unit that has never
observed its own failure state has not tested its precondition.
