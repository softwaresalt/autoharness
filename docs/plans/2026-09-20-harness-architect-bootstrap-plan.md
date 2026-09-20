---
title: "BOOTSTRAP-0: one-time installation of the harness-architect actor"
description: "Installs the actor that P-002 and P-004 name, without assuming that actor already exists and without depending on any code-bearing shipment. Resolves the 187-S bootstrap deadlock at its root: 187-S delivered both the actor and the lifecycle automation that invokes it, while itself depending on code-bearing 184-S, so no policy-compliant route existed to execute either. This unit separates the two: it installs ONLY the actor, under an explicit, one-time, token-bounded bootstrap authority whose red phase is produced by the same mechanical commands P-004 already names. 187-S keeps the lifecycle automation and becomes ordinary harness-backed work. Every code-bearing implementation shipment in the portfolio gains a dependency on this unit's completion."
doc_type: plan
source: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
date: 2026-09-20
plan_id: harness-architect-bootstrap
plan_path: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
plan_role: active
revision: 1
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document authored in the PR-457 portfolio remediation cycle. It carries REMEDIATED-PENDING-REVIEW because it awaits its FIRST independent plan-review attempt. Stage asserts no PASS, has performed no self-review, and this unit is NOT publication-eligible and NOT claimable until attempt 01 returns a verdict."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-20-harness-architect-bootstrap-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 2
source_stash_ids:
  - 76EBDE6D
feature_id: 182-F
shipment_id: 188-S
unit_role: bootstrap-precursor
depends_on_shipments: []
gates:
  - 184-S
  - 185-S
  - 186-S
  - 187-S
  - 176-S
  - 178-S
  - 180-S
requires_plan_hardening: true
hardening_rationale: "This unit defines a one-time execution authority that stands temporarily in place of an installed policy actor. An authority that is too wide, or that fails to expire, is indistinguishable from the waiver this portfolio has refused four times. Its boundary, its expiry token and its non-inheritance are the hardening subject."
tags:
  - bootstrap
  - harness-architect
  - p-002
  - p-004
  - precursor
  - dag-root
---

# BOOTSTRAP-0: one-time installation of the harness-architect actor

## Problem frame

Installed policy `.github/policies/workflow-policies.md` names an actor twice:

> **P-002** — Applies To: `ship` (consumer; harness-architect skill is the producer)
> **P-004** — Applies To: `ship` (via harness-architect skill)

`templates/skills/harness-architect/SKILL.md.tmpl` exists. The workspace
contains eighteen installed skills under `.github/skills/`, and
**`harness-architect` is not one of them.**

`187-S` (feature `181-F`) was written to close this. It cannot, as sequenced:

| # | Fact | Consequence |
|---|---|---|
| 1 | `187-S` delivers both the installed actor *and* the Ship pre-task lifecycle that invokes it | The actor's existence is an output of `187-S` |
| 2 | `187-S`'s own tasks write Python modules under `src/` | They are implementation tasks, so P-004 requires a confirmed red phase and P-002 requires a `harness-ready` label before Ship may claim them |
| 3 | The only declared producer of that label is the actor from fact 1 | `187-S` must consume its own output before producing it |
| 4 | `187-S` additionally declares `depends_on: 184-S`, which is code-bearing | `184-S` needs the same absent actor, so the deadlock is also a graph cycle in the policy sense |

Fact 4 alone would be repaired by reversing an edge. **Facts 1–3 would not.**
Reversing `187-S → 184-S` leaves `187-S` still required to bootstrap itself
through an actor that does not exist. This is why edge reversal was rejected.

## Options evaluated

| Option | Verdict |
|---|---|
| Waiver for `187-S` | **Rejected.** Suspends P-004 for exactly the case it exists to catch. Already rejected at decision D4. |
| `--force` flag on the P-004 gate | **Rejected.** An override reachable by the agent it constrains is not a gate. Already rejected at D4. |
| Edit P-002/P-004 to drop the actor | **Rejected.** Deletes the requirement instead of satisfying it. Already rejected at D4. |
| Reverse the `187-S → 184-S` edge | **Rejected.** Repairs fact 4 and leaves facts 1–3 untouched. The self-bootstrap remains. |
| Declare `187-S` exempt by operator note | **Rejected.** An undocumented waiver wearing a different word. |
| **Split the actor from the automation, and install the actor under a narrow, expiring, evidence-complete authority** | **CHOSEN** |

## The chosen route

**The actor and the automation are two different deliverables, and only the
first is a bootstrap problem.**

* **This unit (`188-S`) installs the ACTOR only** — it generates
  `.github/skills/harness-architect/SKILL.md` from its authoritative template.
  No Python module, no agent-lifecycle edit, no policy edit.
* **`187-S` keeps the AUTOMATION** — the harness-surface resolver, the Ship
  pre-task lifecycle phase, and the `HARNESS_READY`/`NO_HARNESS` state
  contract. After this unit, those are ordinary implementation tasks that a
  real installed actor can harness. `187-S` stops being self-referential.

### Why this is not a waiver

P-004's precondition is **mechanical and actor-independent**:

> `python -m py_compile src/autoharness/cli.py` exits 0 AND
> `PYTHONPATH=src python -m unittest discover -s tests` exits non-zero with
> expected failure markers

Nothing in that sentence requires the *installed copy* of the skill to be the
thing that runs it. The skill file is the **procedure specification**; the
commands are the **evidence**. During bootstrap the procedure is executed
directly from its authoritative template,
`templates/skills/harness-architect/SKILL.md.tmpl`, which is complete and
self-contained — it specifies the posture selection, the harness generation,
the compilation check (Step 5.1), the red-phase check (Step 5.2) and the
`harness-ready` labelling (Step 6).

So:

* **No gate is suspended.** Both channels are observed.
* **No severity is lowered.** A failing observation halts the unit.
* **No evidence is assumed.** The postcondition
  (`Compilation: PASS`, `Red Phase: CONFIRMED`) is recorded from the run.
* **Nothing is skipped.** The only difference from steady state is *which copy
  of the procedure text the executor read* — and erasing that difference
  permanently is this unit's entire purpose.

A waiver produces **less** evidence than the policy demands. This produces
**exactly** the evidence the policy demands, from a template-resident
procedure, once.

### How RED and GREEN are produced during bootstrap

| Phase | Task | What is observed |
|---|---|---|
| RED authored | `182.001-T` | A conformance assertion that `.github/skills/harness-architect/SKILL.md` exists, carries valid YAML frontmatter with `name: harness-architect`, and contains no unresolved `{{...}}` placeholder. Authored to FAIL, because the skill is absent. |
| RED confirmed | `182.002-T` | The two P-004 commands are run verbatim. `py_compile` exits 0 (compilation channel). `unittest discover` exits non-zero and `182.001-T`'s assertion is present in the failure set with its expected marker (red-phase channel). Recorded to `.autoharness/harness-manifest.yaml`. `harness-ready` applied to this unit's tasks. **This is the one and only exercise of the bootstrap authority.** |
| GREEN | `182.003-T` | One commit generates the skill from its template. The assertion flips to passing. |
| VERIFY + EXPIRE | `182.004-T` | Installed/template parity re-derived; the authority's expiry token emitted. |

**Scope honesty on the red-phase channel.** P-004's precondition as written
reads the *whole* discovered suite. This unit records **both** readings: the
scoped observation over its own declared harness set, and the unscoped suite
result exactly as returned. It does **not** redefine the precondition, and it
does **not** pre-empt `176-S`, which owns the scoping of the red-phase
precondition to the declared harness set and its three-channel observation.
If the two readings disagree, that disagreement is recorded as evidence and
the unit halts for operator disposition rather than choosing the convenient
one.

## The one-time boundary

The bootstrap authority is bounded on four independent axes. All four hold
simultaneously; none is sufficient alone.

| Axis | Bound |
|---|---|
| **Scope** | Exactly the tasks of `188-S` / feature `182-F`. No other shipment, feature or task may invoke it, directly or by inheritance. |
| **Count** | Exercised exactly once, by `182.002-T`. Re-running `182.002-T` after expiry is prohibited. |
| **Deliverable** | Only `.github/skills/harness-architect/SKILL.md`, generated from its existing authoritative template. Generating any other absent surface is out of scope. |
| **Expiry** | Terminated by the emission of `HARNESS_ARCHITECT_INSTALLED` by `182.004-T`. |

**After expiry, every unit routes through the installed actor — including a
re-run of this one.** If `188-S` must ever be re-executed, the installed skill
at `.github/skills/harness-architect/` already exists and is used; the
template-resident route is not re-entered. The authority is therefore not
merely time-boxed, it is **not re-enterable**, because the condition that
justified it (the actor's absence) is exactly the condition this unit destroys.

**Stage cannot extend this authority and does not hold it.** It is declared in
a reviewed plan, exercised by Ship, and expires on a token. It is **not** the
`pre_claim` bootstrap grant described in `.github/agents/_ship.agent.md`; it
consumes no grant, writes no grant, and touches no force-audit log. No agent
may author, widen or re-date it.

## Composed-state check (decision D6)

| Field | Value |
|---|---|
| Pass state | `HARNESS_ARCHITECT_INSTALLED` — the skill exists at `.github/skills/harness-architect/SKILL.md`, its frontmatter parses, `name` is `harness-architect`, it carries no unresolved `{{...}}` placeholder, and it derives from `templates/skills/harness-architect/SKILL.md.tmpl`. The only authorizing token. |
| Fail state | `HARNESS_ARCHITECT_ABSENT` — generation was attempted and the result is missing or non-conforming. An explicit failed precondition. |
| No-observation state | `HARNESS_ARCHITECT_NOT_OBSERVED` — artifact missing, unreadable, empty, carrying no `BOOTSTRAP_STATE:` line, carrying more than one, or carrying an unrecognised token. **Never a pass.** |
| Artifact | `.autoharness/gates/harness-architect-bootstrap.txt` (inside the existing gitignored `.autoharness/gates/` boundary, `.gitignore:7`; adds no new ignored path) |
| Line form | Exactly one line, `BOOTSTRAP_STATE: <token> | skill_sha256=<hex> | template_sha256=<hex> | head_commit=<sha> | checked=<RFC3339-UTC>` |
| Producer | `182.004-T`, sole writer, whole-file atomic replace via same-directory temp plus rename |
| Consumer | Stage, when re-sequencing the code-bearing shipments; and `187-S`, whose lifecycle step must find the actor already present |
| Activation commit | `182.003-T` |

Resolution is a **total function**, evaluated in this order, first match wins:
`HARNESS_ARCHITECT_NOT_OBSERVED`, `HARNESS_ARCHITECT_ABSENT`,
`HARNESS_ARCHITECT_INSTALLED`. Fail-closed: anything not affirmatively
conforming is not `INSTALLED`.

## Tasks

| ID | Phase | Task | Size | Cx |
|---|---|---|---|---|
| `182.001-T` | RED | author the harness-surface conformance assertion, observed failing | S | low |
| `182.002-T` | RED CONFIRM | exercise the one-time bootstrap authority: run both P-004 channels verbatim, record the manifest postcondition, apply `harness-ready` | S | medium |
| `182.003-T` | ACTIVATE | one commit: generate `.github/skills/harness-architect/SKILL.md` from its template | S | medium |
| `182.004-T` | VERIFY | re-derive installed/template parity, emit the expiry token | XS | low |

Edges: `182.001-T` → `182.002-T` → `182.003-T` → `182.004-T`. Four edges' worth
of ordering, one chain, no cycle, no successor task inside the unit.

## DAG position

`188-S` is a **DAG root**. It has no precursor shipment: it needs no operation
substrate, no transport decision, no isolation characterization and no schema
migration. It reads one template and writes one generated file.

It becomes the precursor of **every code-bearing implementation shipment** in
the portfolio:

```text
188-S ─┬─▶ 184-S (withheld — also gated on TRANSPORT_DECIDED)
       ├─▶ 185-S ─┬─▶ 186-S
       │          ├─▶ 178-S
       │          └─▶ 180-S
       ├─▶ 187-S
       └─▶ 176-S
```

It is **not** a precursor of `177-S`, `182-S` or `183-S`. Those three are DAG
roots and remain so:

* `182-S` and `183-S` are bounded spikes that land no production code — their
  deliverable is a findings artifact, and `176.001-T` states "NO production
  code" explicitly.
* `177-S` carries its own PREPARE/RED/VERIFY/ACTIVATE machinery: its five RED
  tasks author their own failing assertions and its `169.017-T` gate adjudicates
  them before activation. It consumes no `HARNESS_READY` from the Ship pre-task
  lifecycle.

Adding a bootstrap edge to any of those three would re-introduce the false
serial dependency that decision D8 withdrew.

## Out of scope

* The Ship pre-task harness-generation lifecycle, the harness-surface resolver
  and the `HARNESS_READY`/`NO_HARNESS` contract — `187-S` owns all three and
  keeps them.
* The P-004 gate's three-channel observation logic and the scoping of the
  red-phase precondition to the declared harness set — `176-S` owns both.
* Any edit to P-002 or P-004 text. Both are correct as written; this unit
  satisfies them.
* Generating any absent skill surface other than `harness-architect`.
* Any change to the `pre_claim` topology gate or its bootstrap-grant mechanism.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | The authority is read as a general precedent for skipping P-004 | The four boundary axes are stated in the plan, in `182-F`, in `188-S` and in `182.002-T`'s own record, and expiry is mechanical rather than narrative. |
| R2 | The `harness-architect` template is stale relative to current skill conventions | `182.001-T`'s assertion validates frontmatter, `name`, and placeholder resolution. A stale template fails the assertion at `182.003-T` and never reaches `INSTALLED`. |
| R3 | The authority is exercised, then the unit stalls before expiry | `HARNESS_ARCHITECT_NOT_OBSERVED` is the fail-closed default; no successor may treat a missing token as satisfied. |
| R4 | The unscoped suite reading is non-zero for unrelated reasons, masking the red-phase signal | Both readings are recorded; disagreement halts for operator disposition rather than resolving in the passing direction. |
| R5 | A reader concludes the actor's installation also installed the lifecycle | `182-F`, `188-S` and this plan state the split explicitly, and `187-S` retains the automation in its own manifest. |

## Hardening review

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Is this a waiver with extra words? | No. A waiver produces less evidence than the policy demands. This produces exactly the evidence P-004 names — both channels, recorded to the manifest — from a template-resident procedure. The gate is satisfied, not suspended. |
| H2 | What stops the authority being reused? | Four independent bounds: scope (this shipment's tasks), count (one task, once), deliverable (one named file), and an expiry token. It is also not re-enterable, because installing the actor destroys the condition that justified it. |
| H3 | Could an agent widen or re-date the authority? | No. It lives in a review-gated plan and expires on a token emitted by a task, not on a date. Stage does not hold it and cannot extend it. It is not the `pre_claim` bootstrap grant and consumes none. |
| H4 | Why is `188-S` a root when `187-S` was not? | Because installing the actor requires reading one template and writing one file. It needs no substrate, no transport decision and no isolation result. `187-S` was not a root because its automation genuinely needs the substrate — that dependency was never the defect. |
| H5 | Does this let `187-S` become claimable early? | No. `187-S` keeps its `184-S` dependency, and `184-S` is withheld pending `TRANSPORT_DECIDED`. `188-S` removes the *self-bootstrap*, not the *substrate prerequisite*. |
| H6 | Is the red phase real, or a formality? | Real. `182.001-T`'s assertion fails against the current workspace for the intended reason — the skill is absent — and passes only after `182.003-T` generates it. The transition is observed on both sides. |
| H7 | Does this unit need the actor to harness itself? | Its single harness artifact is one conformance assertion over a generated file. `182.002-T` produces the P-004 observation for it by executing the template-resident procedure. That is the bootstrap, exercised once, and it is why the unit exists. |
| H8 | What if generation succeeds but produces a non-conforming skill? | `HARNESS_ARCHITECT_ABSENT`. No token is emitted, the unit halts, and no successor becomes claimable. |

### Blast radius

One new generated file under `.github/skills/`, one gitignored gate artifact,
and one recorded manifest postcondition. No Python module, no agent template,
no installed agent mirror, no policy text, no CI workflow. This is the
narrowest surface any unit in this portfolio touches — deliberately, because a
bootstrap authority should not be attached to a wide change.

### Rollback

`182.001-T`–`182.002-T` are inert (a failing test and a recorded observation).
`182.003-T` reverts as a unit: deleting the generated skill returns the
workspace to the pre-bootstrap state, and the conformance assertion returns to
failing, which is its authored state. The expiry token in
`.autoharness/gates/` is never committed and is re-derived rather than
restored. Rollback restores the deadlock rather than leaving a partial state —
which is correct, because a partially-bootstrapped actor is the one state no
consumer can interpret.

### Verification floor

`HARNESS_ARCHITECT_INSTALLED` and `HARNESS_ARCHITECT_ABSENT` both observed
reachable, and the failing side of `182.001-T` observed before the passing
side. A unit that has never observed its own failure state has not tested its
precondition.
