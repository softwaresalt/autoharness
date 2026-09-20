---
title: "Foundation: Ship pre-task harness-generation lifecycle"
description: "Installs the Ship pre-task harness-generation LIFECYCLE that invokes the actor policy P-004 already names. At revision 2 the ACTOR INSTALL ITSELF is no longer performed here - it moved to the narrow one-time precursor 188-S, because this unit could not bootstrap itself through an actor that did not exist. At revision 4 the unit is re-grounded in live workspace state: the Ship agent TEMPLATE already carries a harness-generation section and the INSTALLED MIRROR carries none, so this unit RECONCILES THE EXISTING TEMPLATE SECTION IN PLACE - never duplicating it - and INSTALLS the corresponding dogfood mirror section in the SAME commit, reaching template/mirror parity rather than assuming it. It also defines the lifecycle states including an explicit NO_HARNESS failed-precondition state. Closes the assumed-skill bootstrap gap at its root so the P-004 gate work in 176-S consumes an installed producer instead of an assumption."
doc_type: plan
source: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
date: 2026-09-18
plan_id: ship-harness-lifecycle-foundation
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_role: active
revision: 4
verdict: null
disposition: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 4 remediates independent plan-review attempt 02 of revision 3 (FAIL/BLOCK, P0 0 / P1 1 / P2 2 / P3 0). S7 (P1, blocking): the plan is re-grounded in live workspace state. templates/agents/_ship.agent.md.tmpl ALREADY carries '### Step 2: Harness Generation (P-002 / P-004)' while .github/agents/_ship.agent.md carries no harness-generation step at all and uses '### Step 2' for its Task Execution Loop - the exact inverse of the drift revision 3 assumed. Problem frame, Contract, Composed-state check, Rollout, Rollback, hardening and the task records are rewritten so 181.005-T UPDATES THE EXISTING TEMPLATE SECTION IN PLACE and NEVER adds a duplicate, while INSTALLING a parity mirror section at a fixed anchor in the same commit, under exact heading-literal detection, pre/post occurrence counts, explicit parity criteria and a confined rollback. S8 (P2): 181.003-T is re-scoped as an INERT agent-template/procedure design task producing canonical phase TEXT at two named fixture paths - it is not and never was an src/ module task - and the Composed-state check, Blast radius, Tasks table and its size/complexity are reconciled to that, with scope guards and plan/manifest/source citations propagated to 181.001-T, 181.003-T and 181.004-T. S9 (P2): source_stash_ids is corrected from 3EF5AAF2 to 76EBDE6D, the single source the governing decision assigns to P4/187-S/181-F and the ID every live record already carries. The verdict field is NULL because revision 4 has NOT been reviewed; REMEDIATED-PENDING-REVIEW is a DISPOSITION and never a verdict. Stage asserts no PASS, closes no finding, and has performed no self-review."
awaiting_attempt: 3
review_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 3
source_stash_ids:
  - 76EBDE6D
source_stash_note: "Corrected at revision 4 (finding S9). The governing decision's portfolio table assigns 76EBDE6D to this unit by name - docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md line 993, row 'P4 | 187-S | 181-F | foundation | 76EBDE6D' - and every live carrier already cites it: the 187-S title and body, 181-F, 181.002-T and 181.005-T. 76EBDE6D is an ARCHIVED stash entry, retrievable at .backlogit/archive/stash.jsonl line 234: 'P-021 RELIABILITY FOLLOW-UP: P-004 red-phase precondition is unsatisfiable on this workspace.' That is this unit's genuine origin. The prior value 3EF5AAF2 was a MIS-CITATION, not a second genuine source: the same decision table assigns it at line 995 to 177-S / 169-F, the post-claim member-status portfolio, and it is the declared source of docs/plans/2026-09-18-post-claim-member-status-contract-plan.md. It has no relation to the Ship harness-generation lifecycle. This unit is SINGLE-SOURCE; no multi-source relation is claimed because none exists."
feature_id: 181-F
shipment_id: 187-S
unit_role: precursor-foundation
depends_on_shipments:
  - 188-S
removed_depends_on_shipments:
  - 184-S
bootstrap_precursor_plan: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
gates:
  - 176-S
requires_plan_hardening: true
hardening_rationale: "Modifies the Ship agent lifecycle itself: every future shipment execution passes through the step this unit touches, so a defect here is a defect in every subsequent execution. At revision 4 the pass is re-derived against LIVE FILE CONTENT rather than against the 188-S split alone - the revision-3 pass asked every question about the split and none about what the ACTIVATE commit's own target already contains, which is how a same-named pre-existing section went unnoticed. The hardening subject is now the in-place reconciliation of that existing section, duplicate prevention, mirror-parity criteria, and rollback confinement."
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

The chosen path is the remaining one: **install the actor**. Revision 2 changes
**where** that install happens.

## Provenance

This unit has **one** source, and it is `76EBDE6D`.

| Field | Value |
|---|---|
| Source stash ID | `76EBDE6D` |
| Where it lives | `.backlogit/archive/stash.jsonl` line 234 — **archived**, not active |
| What it says | *"P-021 RELIABILITY FOLLOW-UP: P-004 red-phase precondition is unsatisfiable on this workspace."* |
| Who assigns it to this unit | The governing decision's portfolio table, `docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md` line 993: `P4 \| 187-S \| 181-F \| foundation \| 76EBDE6D` |
| Live carriers already citing it | `187-S` title and body, `181-F`, `181.002-T`, `181.005-T` |

Revisions 1–3 declared `source_stash_ids: [3EF5AAF2]`. That was a
**mis-citation, corrected at revision 4** (finding `S9`) — not a second genuine
source, and **no multi-source relation is claimed, because none exists**.
`3EF5AAF2` is assigned by the *same* decision table, at line 995, to
`177-S` / `169-F` — the post-claim member-status portfolio — and is the declared
source of `docs/plans/2026-09-18-post-claim-member-status-contract-plan.md`. It
has no relation to the Ship harness-generation lifecycle. The unit now carries
a single agreed provenance ID across the plan, the feature, the shipment and
every task record.

## The bootstrap split (revision 2)

PR #457 review thread `PRRT_kwDORzpWpM6kHrw5` found that revision 1 could not
reach execution at all, and that reversing one dependency edge would not have
been enough. It was correct on both counts: the deadlock had **two independent
axes**, and each needs its own fix.

| Axis | Defect at revision 1 | Fix at revision 2 |
|---|---|---|
| Self-bootstrap | This unit's tasks write Python under `src/`, so P-002/P-004 require a harness-ready state whose only declared producer is the actor *this unit was to install*. It could not bootstrap itself through an actor that did not exist. | The **actor install alone** moves to the narrow, one-time, separately reviewed precursor shipment `188-S` (plan: `docs/plans/2026-09-20-harness-architect-bootstrap-plan.md`). |
| Graph order | This unit declared `depends_on 184-S`, a code-bearing substrate shipment that needs the *same* absent lifecycle — the ordering ran the wrong way, and through the wrong kind of predecessor. | The `184-S` edge is **removed**. It was never a technical dependency: this unit delivers the surface-resolution phase, the resolver and the state contract — **not** the installed actor — and consumes none of `184-S`'s operation registry, result model or transport. |

Axis 2 alone is the "simple edge reversal" the reviewer judged insufficient. It
is fixed here **in addition to** axis 1, not instead of it.

**What this unit still owns.** The Ship pre-task **harness-surface resolution**
phase — reconciled into the Ship agent's existing harness-generation step and
mirrored into the installed agent — the resolver that locates the installed
actor, the lifecycle state contract the P-004 gate consumes, and the
`HARNESS_READY` / `NO_HARNESS` token contract. All ordinary harness-backed
work, executed *after* `188-S` has installed the actor, with no special
authority of any kind.

**What this unit no longer owns.** Generating
`.github/skills/harness-architect/` from its template. That single file is
`188-S`'s entire deliverable.

**No waiver anywhere on this path.** `188-S` consumes no bootstrap grant,
writes no bootstrap grant, uses no `--force`, and touches no force-audit log.
It executes the complete procedure already specified in
`templates/skills/harness-architect/SKILL.md.tmpl`, so the **full** mechanical
P-004 evidence — `py_compile` exit 0 and a failing `unittest discover` carrying
the expected RED markers — is genuinely produced rather than suspended. If the
lifecycle is not installed, P-004 still fails closed.

**Dependency:** this unit now declares exactly one predecessor, `188-S`.

## What P-004 already requires

The live policy's precondition is not vague and does not need amending:

> `python -m py_compile src/autoharness/cli.py` exits 0 **and**
> `python -m unittest discover` exits non-zero

and its postcondition records `Compilation: PASS` and `Red Phase: CONFIRMED`.

This matters for scope: attempt-08's P0 on `176-S` (the gate omits the
compilation channel) is a **regression against live policy**, not a gap in it.
`176-S` restores the observation; this unit supplies the **lifecycle step** that
produces the state the observation reads. The actor that step invokes is
supplied by `188-S`, not here.

## Live state of the two ACTIVATE targets

**Read at `da8f890a`, before anything else in this plan was written.** Revision
3 reasoned about these two files without reading them, and was wrong about
which way they had drifted. The facts:

| Surface | Live content |
|---|---|
| `templates/agents/_ship.agent.md.tmpl:326` | **`### Step 2: Harness Generation (P-002 / P-004)` already exists.** It is a full pre-task procedure: list queued tasks, partition on the `harness-ready` label, invoke **harness-architect** for the unlabelled batch, then confirm every queued task carries the label and "halt and report the gap" otherwise. Its step sequence is `Step 1: Pre-Flight Checks` → `Step 2: Harness Generation` → `Step 3: Build Ready Queue` → `Step 4: Execute Task Loop` → `Step 5: PR Lifecycle` → `Step 6: Post-Merge Closure`. |
| `.github/agents/_ship.agent.md` | **No harness-generation step of any kind.** Zero occurrences of `harness-ready`, zero of `harness-architect`; every one of its `harness` matches is the product name `autoharness`. Its step sequence is `Step 1: Pre-Flight Checks` (line 329) → `Step 2: Task Execution Loop` (line 336) → `Step 3: Review Gate` → `Step 4: PR Lifecycle` → `Step 5: Post-Merge Closure`. |

Three consequences govern the whole of this unit:

1. **The drift runs template → mirror, not mirror → template.** The template
   declares a harness-generation step the installed mirror does not. Revision 3
   justified single-commit activation against the *opposite* hazard. That
   justification is withdrawn and replaced below.
2. **`### Step 2` means two different things in the two files.** In the
   template it is Harness Generation; in the mirror it is the Task Execution
   Loop, and **ten** passages inside the mirror refer to "Step 2" meaning that
   loop (lines 184, 214, 275, 283, 302, 305, 326, 336, 377, 748). **Renumbering
   any existing mirror step is therefore forbidden** — it would silently
   invalidate every one of those cross-references.
3. **This unit's phase and the existing Step 2 are genuinely distinct, and
   ordered.** The existing Step 2 generates *task test harnesses* by invoking
   `harness-architect`. This unit resolves *which installed skill surfaces
   under `.github/skills/` a shipment requires, and whether they are present*.
   The second is a **precondition of the first**: Step 2 cannot invoke
   `harness-architect` if `harness-architect` is not installed. So this unit's
   phase belongs **inside** the existing section, ahead of its task listing —
   not in a second, parallel section.

## Contract

The Ship agent's **existing** harness-generation step gains a leading
surface-resolution phase, executed before it lists any task:

1. Determine the harness surfaces the shipment's tasks require.
2. Report each required surface `PRESENT` or `ABSENT` against
   `.github/skills/`.
3. Record the outcome as a typed lifecycle state — `HARNESS_READY` or
   `NO_HARNESS`.
4. On `NO_HARNESS`, halt before the task partition runs.

This is a **real installed lifecycle phase in the Ship agent**, not a
documentation note and not an assumption recorded in a plan. `harness-architect`
— the only surface this portfolio requires — is already present when the phase
first runs, because `188-S` installed it. No task in this unit exercises the
phase against `.github/skills/harness-architect/`; `181.004-T` exercises it
against a fixture template in a scratch root instead.

## The ACTIVATE contract, stated mechanically

`181.005-T` performs **one commit** over **exactly two files**. Everything an
executor needs to avoid producing a duplicate section is fixed here.

### Detection — exact literals, no fuzzy matching

| Step | File | Operation | Exact literal |
|---|---|---|---|
| D1 | `templates/agents/_ship.agent.md.tmpl` | Locate the section to **update in place** | `### Step 2: Harness Generation (P-002 / P-004)` |
| D2 | `.github/agents/_ship.agent.md` | Locate the **insertion anchor** (insert immediately *before* it) | `### Step 2: Task Execution Loop` |
| D3 | `.github/agents/_ship.agent.md` | Locate the **preceding boundary** (insert immediately *after* its block ends) | `### Step 1: Pre-Flight Checks` |

Matching is on the **whole heading line**, exact and case-sensitive. Substring,
regex-loosened or heading-level-agnostic matching is forbidden: `Harness
Generation` appears in prose elsewhere and must not be mistaken for a heading.

### Duplicate prevention — counted, not asserted

| Gate | Check | Required | On failure |
|---|---|---|---|
| G1 (pre) | Occurrences of the D1 literal in the template | **exactly 1** | HALT — 0 means the section was removed since planning; ≥2 means a duplicate already exists. Either way the premise of this plan is void. Touch no file, commit nothing, return to Stage. |
| G2 (pre) | Occurrences of `### Step 2: Harness Generation` (any suffix) in the mirror | **exactly 0** | HALT — the mirror already has the section; re-plan rather than reconcile blind. |
| G3 (pre) | Occurrences of the D2 and D3 literals in the mirror | **exactly 1 each** | HALT — anchor ambiguous or absent. |
| G4 (post) | Occurrences of the D1 literal in the template | **exactly 1** | FAIL the commit — the update was not in place. |
| G5 (post) | Occurrences of `Harness Generation (P-002 / P-004)` as a **heading** in the template | **exactly 1** | FAIL the commit — a second section was appended. |
| G6 (post) | Occurrences of `### Step 1.5: Harness Generation (P-002 / P-004)` in the mirror | **exactly 1** | FAIL the commit. |
| G7 (post) | Occurrences of any heading line matching `### Step N: Harness Generation` in the mirror | **exactly 0** | FAIL the commit — the mirror section must be `Step 1.5`, not a renumbered `Step 2`. |

**The template section is UPDATED, never re-added.** The executor edits the
body beneath the D1 heading. It does not delete-and-reinsert the section, does
not move it, and does not change its heading text.

### The mirror section's heading and placement

The mirror receives a **new** section headed exactly:

```text
### Step 1.5: Harness Generation (P-002 / P-004)
```

inserted between the end of `### Step 1: Pre-Flight Checks` and the line
`### Step 2: Task Execution Loop`.

`Step 1.5` is chosen deliberately and is **not** cosmetic:

* It places the phase in the same ordinal position the template gives it —
  after pre-flight, before the task loop.
* It renumbers **nothing**, so all ten pre-existing "Step 2" references in the
  mirror continue to resolve to the Task Execution Loop.
* Fractional step numbers are already this file's own convention
  (`Step 0.1b`, `Step 0.1c`, `Step 0.1d`, `Step 0.5`), so it introduces no new
  document grammar.

### Parity criteria — what "at parity" means, exactly

After the commit, all six must hold. `181.004-T` states them as assertions and
`181.005-T` is not complete until they pass.

| # | Criterion |
|---|---|
| P1 | The template contains **exactly one** harness-generation section, still headed `### Step 2: Harness Generation (P-002 / P-004)`. |
| P2 | The mirror contains **exactly one** harness-generation section, headed `### Step 1.5: Harness Generation (P-002 / P-004)`. |
| P3 | The two sections carry the **same ordered procedure**: the surface-resolution phase first, then the queued-task listing, then the `harness-ready` partition, then the `harness-architect` invocation for the unlabelled batch, then the post-scaffold label confirmation and gap halt. |
| P4 | The two sections carry the **same state tokens and the same halt conditions** — `HARNESS_READY`, `NO_HARNESS`, halt-before-partition on `NO_HARNESS`, halt-and-report on a post-scaffold label gap. |
| P5 | They differ **only** in (a) resolved template variables and (b) the step number in the heading. In the mirror, `{{BUILD_CHECK_COMMAND}}` resolves to `python -m py_compile src/autoharness/cli.py`, bound from `.autoharness/harness-manifest.yaml` → `variables_used`; `{{STATUS_QUEUED}}` resolves to `queued`, bound from `.autoharness/backlog-registry.yaml` → `status_values.queued` (line 249), because `STATUS_QUEUED` is **not** present in `variables_used` and must not be invented. Any variable that resolves from neither source is a **fail-closed halt**, not a guess. No other difference is permitted. |
| P6 | **No other heading in either file is added, removed, renumbered or retitled**, and the mirror's ten pre-existing "Step 2" references still resolve to `### Step 2: Task Execution Loop`. |

Parity is a **post-commit property of two files**, verified by reading them —
not an inference from the fact that one commit touched both.

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `HARNESS_READY` — every required skill surface present in `.github/skills/` and matching its authoritative template |
| Fail state | `NO_HARNESS` — a required surface is absent and could not be resolved; **an explicit failed precondition, never silent success and never an implicit pass** |
| Producer of the state | the harness-surface requirement resolver implemented by `181.002-T` (Python, under `src/`) |
| Author of the phase text that calls it | `181.003-T` — **agent-procedure text only, no Python** |
| Activation commit | `181.005-T` |
| Consumer | the P-004 gate in `176-S`; Ship's own pre-task sequence |

`HARNESS_READY` is reachable for the only surface currently required, because
`188-S` has already installed `.github/skills/harness-architect/SKILL.md` before
this unit becomes claimable. The resolver therefore observes a surface that
exists rather than one it would have to create.

`NO_HARNESS` is distinct from a policy failure. A gate that cannot observe its
precondition has **not** observed a pass — this is the same
`NO_OBSERVATION`-is-not-`PASS` rule the P-004 gate work in `176-S` applies to
its three observation channels.

## Rollout

**PREPARE (inert).** `181.001-T` through `181.003-T`. The lifecycle-state
tests and the harness-surface requirement resolver exist under `src/` and
`tests/` but nothing invokes them; the canonical phase text exists as
**test-owned fixture data**, not yet in either live Ship surface. No policy or
gate depends on any of it. Live shipment execution is unchanged, and — this is
the point of staging the text as data — **neither live Ship file is touched
before the activation commit**, so the template's executed `Step 2` is not
altered by a task that claims to be inert.

This mirrors the pattern already used by `169.011-T`, which authored, as
test-owned data at two named paths, the single canonical source that its
ACTIVATE commit later transcribed.

**VERIFY.** `181.004-T` — RED assertions observed failing, then passing. The
resolver is observed returning `HARNESS_READY` only after actually locating the
installed `.github/skills/harness-architect/SKILL.md` — **already installed by
`188-S`, and consumed here read-only as a satisfied precondition** — and
returning `NO_HARNESS` against a scratch harness root in which a required
surface is absent. It additionally asserts the pre-commit gates `G1`–`G3` hold
against live file content, so a stale premise is caught **before** activation
rather than during it. The scratch-root exercise uses a fixture template under
the test tree; it never writes under `.github/skills/`, and it never generates
the `harness-architect` deliverable.

**ACTIVATE.** `181.005-T` — **one task, one commit**, transcribing the fixture
text into both surfaces simultaneously: **update in place** the template's
existing `### Step 2: Harness Generation (P-002 / P-004)`, and **insert** the
mirror's new `### Step 1.5: Harness Generation (P-002 / P-004)` at the fixed
anchor. Those two files are the **only** surfaces this commit may change, and
`G1`–`G7` plus `P1`–`P6` bound it.

> Splitting this across commits produces a reachable state in which exactly one
> of the two Ship surfaces declares the phase. Today the workspace is already
> in the template-ahead form of that state; a split would merely replace it
> with the mirror-ahead form. Only a single commit that reconciles both at once
> ends the divergence rather than reversing its direction. Sequential task
> edges are not atomic.

**No task in this unit generates, installs, modifies or deletes
`.github/skills/harness-architect/SKILL.md`.** That file is `188-S`'s entire
deliverable and this unit's precondition.

## Tasks

| ID | Phase | Task | Size | Cx |
|---|---|---|---|---|
| `181.001-T` | RED | lifecycle-state contract tests incl. `NO_HARNESS` reachability | S | medium |
| `181.002-T` | PREPARE | harness-surface requirement resolver (Python, `src/`) | S | medium |
| `181.003-T` | PREPARE | author the canonical phase **text** as test-owned fixture data — **agent-procedure design, no Python** | S | medium |
| `181.004-T` | VERIFY | lifecycle evidence + pre-commit gates `G1`–`G3`, actor already installed by `188-S`, no live reference yet | XS | low |
| `181.005-T` | ACTIVATE | one commit: update the template's existing `Step 2` in place, install the mirror's `Step 1.5` | M | high |

Edges: `181.001-T` → `181.002-T` → `181.003-T` → `181.004-T` → `181.005-T`.

### Sizing and complexity, re-derived at revision 4

Two axes, independently assigned, never conflated.

* **`181.003-T`: `M`/`high` → `S`/`medium`.** This is a re-derivation against a
  changed scope, not a downgrade of an unchanged one. At revision 3 the task
  was described in two sentences and the plan simultaneously implied it was a
  `src/` module (`S8`); it also had to decide, unaided, how its phase related to
  a template section nobody had read (`S7`). Both sources of uncertainty are
  now removed: the deliverable is exactly two fixture files, the target heading
  and insertion anchor are fixed literals, and the parity criteria `P1`–`P6`
  are stated for it rather than left to judgement. What remains is bounded
  prose authoring against a specified contract — one sitting, `S`, and
  `medium` rather than `high` because judgement is still required to keep the
  two variants semantically identical.
* **`181.005-T`: `M`/`high`, unchanged.** It stays `high` because it is the
  activation commit on the one file every future shipment execution passes
  through. Under the two-axis gate a `complexity: high` task requires a
  **de-risking step**, and this unit carries three, all added at revision 4:
  (1) `181.003-T` reduces the commit to a **transcription** of already-reviewed
  text rather than an authoring act; (2) `181.004-T` asserts the pre-commit
  gates `G1`–`G3` against live file content **before** activation is reached;
  (3) `G4`–`G7` and `P1`–`P6` make the commit's success a counted, mechanical
  property instead of a claim. It is not split further because the atomicity
  requirement is precisely that both files move together — splitting it would
  reintroduce the defect it exists to prevent.
* All five tasks remain within the 2-hour envelope. No task exceeds it, and the
  one remaining `complexity: high` task carries the de-risking above.

**No task in this unit generates `.github/skills/harness-architect/`**, at
revision 2, 3 or 4. `188-S` installs it, and `181.004-T` observes it as an
already-satisfied precondition rather than producing it.

**No task in this unit produces Python at `181.003-T`.** The `src/` deliverable
of this unit is the resolver and the state contract, authored by `181.002-T`
and tested by `181.001-T`. `181.003-T` produces Markdown fixture text only.

## Out of scope

* The P-004 gate's own three-channel observation logic — `176-S` owns it and
  consumes this unit's `HARNESS_READY` state.
* Any edit to policy P-004's text. Its precondition is correct as written;
  this unit satisfies it rather than changing it.
* Generating `.github/skills/harness-architect/` itself. That is the entire
  deliverable of the one-time precursor `188-S`; this unit consumes it.
* Generating any other absent skill surface. The resolver reports; only
  `harness-architect` is required by this portfolio, and installing more would
  widen the activation commit beyond its contract.
* **Any change to the template's existing `Step 2` beyond inserting the
  surface-resolution phase and bringing the mirror to parity with it.** Its
  task-partition and `harness-architect` invocation logic is pre-existing,
  works, and is not this unit's to redesign. Reconciling it is in scope;
  rewriting it is not.
* **Renumbering any step in either Ship surface.**

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | The `harness-architect` template is stale relative to current skill conventions | `188-S` generates and validates it under its own verification floor; `181.004-T` re-observes frontmatter and structure before activation, so a stale template fails VERIFY in either unit rather than landing broken. |
| R2 | The lifecycle step slows every shipment start | The resolver short-circuits when all required surfaces are already present, which is the steady state after the first execution. |
| R3 | `NO_HARNESS` becomes a routine blocker | It is only reachable when a required surface has no authoritative template. The resolver reports the missing template path, so the remedy is explicit rather than a retry loop. |
| R4 | The ACTIVATE commit appends a **second** harness-generation section to the template instead of updating the existing one | The primary risk of this unit, and the defect `S7` caught. Detection is by exact heading literal (`D1`); the outcome is **counted** both before (`G1`) and after (`G4`, `G5`). A pre-count other than exactly 1, or a post-count other than exactly 1, halts or fails the commit. Plan and record both say **update in place**; neither says "add". |
| R5 | The mirror insertion renumbers an existing step and silently breaks the ten internal "Step 2" references | The mirror section is `Step 1.5`, chosen so nothing is renumbered. `P6` states the invariant, `G7` detects a renumbered `Step N: Harness Generation`, and `181.004-T` records the pre-existing reference lines so the post-commit check is mechanical. |
| R6 | `181.003-T` edits a live Ship surface while claiming to be inert | It writes to test-owned fixture paths only; both live surfaces are untouched until `181.005-T`. `181.004-T`'s "no executed Ship step references the lifecycle yet" assertion is now a statement about **file content**, not only about wiring. |
| R7 | A template variable in the mirror transcription resolves from no named source and is improvised | `P5` names the source for each: `BUILD_CHECK_COMMAND` from `.autoharness/harness-manifest.yaml` → `variables_used`; `STATUS_QUEUED` from `.autoharness/backlog-registry.yaml` → `status_values.queued`, because it is **not** in `variables_used`. Any variable resolving from neither is a fail-closed halt. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

Re-derived at revision 4 against **live file content**. The revision-3 pass
was re-derived against the `188-S` split and every question was sound, but not
one of them was asked against what the ACTIVATE commit's own targets actually
contain — which is how a same-named, same-policy-cited pre-existing section
went unnoticed through two attempts. `H9`–`H12` close that class.

| # | Question | Answer |
|---|---|---|
| H1 | Is the lifecycle phase real, or does it just assume the actor it invokes? | Real, and the assumption is exactly what it removes. `181.004-T` observes the resolver returning `HARNESS_READY` only after it has actually located `.github/skills/harness-architect/SKILL.md` and matched it against its authoritative template, and returning `NO_HARNESS` against a scratch root where a required surface is absent. This unit does not generate the actor and does not validate it into existence: `188-S` installs it under its own verification floor, so a stale or non-conforming template fails **there**, before this unit is claimable. |
| H2 | Could `NO_HARNESS` be silently treated as a pass? | It is a distinct terminal state, and the P-004 gate in `176-S` consumes it as a failed precondition. The rule is the same one this portfolio applies everywhere: an unobserved precondition is not a satisfied one. |
| H3 | Does this unit amend policy P-004? | No, and it must not. P-004's precondition already requires `py_compile` exit 0 and a non-zero test run. The defect is an implementation that stopped observing one channel. Amending the policy would delete the requirement instead of satisfying it. No task in this unit may edit `.github/policies/workflow-policies.md` or `templates/policies/`, in the ACTIVATE commit or anywhere else. |
| H4 | Why not a waiver or a force flag? | Both were evaluated and rejected. A waiver suspends the gate for exactly the case it exists to catch, and an override reachable by the agent it constrains is not a gate. |
| H5 | Does the phase run on every task? | Pre-task, per shipment, short-circuiting when all required surfaces are present — which is the steady state after `188-S`. A per-task full re-resolution would be a cost with no added guarantee. |
| H6 | Could the resolver install surfaces beyond the one required? | It resolves; it does not install. Only `harness-architect` is required by this portfolio and it is already installed by `188-S` before this unit runs. Generating anything in the ACTIVATE commit would widen it past its stated contract and is out of scope. |
| H7 | Could reverting this unit remove `188-S`'s deliverable? | No, and the Rollback section states so explicitly. The ACTIVATE commit touches exactly two files — the Ship agent template and its installed mirror — so its revert cannot reach `.github/skills/harness-architect/`. |
| H8 | Does anything in this unit still assume it installs the actor? | It must not, and the propagation is the risk. At revision 4 the Rollout, Blast radius, Rollback, this pass, the Tasks table, the Out-of-scope list and **all five** task records state the same reduced scope. A single surface left at revision-1 framing is what blocked revision 2, because Ship executes records rather than narrative. |
| **H9** | **Does the ACTIVATE commit's target already contain the section this unit intends to add?** | **Yes — and revision 3 did not know it.** `templates/agents/_ship.agent.md.tmpl:326` already carries `### Step 2: Harness Generation (P-002 / P-004)`. This is now the governing fact of the unit: the template section is **updated in place**, never re-added, under exact-literal detection `D1` and counted gates `G1`/`G4`/`G5`. An instruction to "add the step to both files" is withdrawn from the plan and from every record, because against a file that already has the section it authorizes exactly the duplicate this unit must not produce. |
| **H10** | **Is the stated atomicity hazard the drift that actually exists?** | **It was not; it is now.** Revision 3 argued against "the installed mirror has a lifecycle step its template does not declare". The live drift is the exact inverse — template ahead, mirror empty. The argument is replaced: a split commit would not create divergence, it would merely **reverse the direction** of the divergence that already exists. Only a single commit reconciling both surfaces ends it. The conclusion (one commit) survives; the reasoning that reached it does not, and has been rewritten rather than patched. |
| **H11** | **Could the mirror insertion break the mirror's own internal cross-references?** | It could, and that is why the heading is `Step 1.5` rather than `Step 2`. The mirror's `### Step 2` is `Task Execution Loop`, and **ten** passages inside the file refer to "Step 2" meaning that loop (lines 184, 214, 275, 283, 302, 305, 326, 336, 377, 748). Renumbering is forbidden by `P6` and detected by `G7`. Fractional numbering is already this file's own convention (`Step 0.1b`/`0.1c`/`0.1d`/`0.5`), so the insertion introduces no new document grammar. |
| **H12** | **Is `181.003-T` genuinely inert if the phase text lands in a live file?** | It would not be — which is why it no longer does. `181.003-T` writes the canonical text to **test-owned fixture paths**, and `181.005-T` transcribes it into the two live surfaces. Had `181.003-T` edited the template in place it would have modified the template's **executed** `Step 2` while claiming to be inert, and the activation commit would no longer have been atomic across both surfaces. This is the `169.011-T` pattern: author the canonical source as data, transcribe it at ACTIVATE. |

### Blast radius

* **`src/`** — the modules implementing the harness-surface requirement
  resolver and the lifecycle state contract (`181.002-T`, tested by
  `181.001-T`). **`181.003-T` contributes no Python**; its output is fixture
  text under `tests/`.
* **`tests/`** — the lifecycle-state contract tests and the two canonical
  phase-text fixtures.
* **`templates/agents/_ship.agent.md.tmpl`** — one existing section updated in
  place. No heading added, removed or renumbered.
* **`.github/agents/_ship.agent.md`** — one new section inserted at a fixed
  anchor. No existing heading renumbered.
* **No new installed skill.** The `harness-architect` actor is installed by
  `188-S`; this unit neither generates, modifies nor removes it.
* **No policy text**, in template or installed form.

Every future shipment execution passes through the reconciled step, so a defect
here is a defect in all subsequent execution. That is why the commit's success
is expressed as counted gates rather than as a description.

### Rollback

`181.001-T`–`181.004-T` are inert: they add Python, tests and fixture data that
nothing invokes, and they touch **neither** live Ship surface.

`181.005-T` reverts as a unit. A `git revert` of that single commit:

* restores `templates/agents/_ship.agent.md.tmpl`'s `### Step 2: Harness
  Generation (P-002 / P-004)` to its exact pre-commit body — the section itself
  is **not** removed, because this unit did not create it;
* removes `.github/agents/_ship.agent.md`'s `### Step 1.5: Harness Generation
  (P-002 / P-004)` in its entirety;
* renumbers nothing in either file, because the commit renumbered nothing.

**The post-revert state is the pre-`187-S` steady state**, which is the
template-ahead drift described under *Live state of the two ACTIVATE targets* —
a **known**, pre-existing condition this unit inherited, not a new one it
creates. Naming that plainly matters: a reviewer must be able to tell that the
revert restores a documented prior state rather than leaving fresh divergence.

**The revert must not touch `.github/skills/harness-architect/SKILL.md`.** That
file is `188-S`'s deliverable, it is not produced by this unit, and every
code-bearing shipment in the portfolio is gated on its existence. Deleting it
would turn a unit-scoped revert into a portfolio-wide regression. **The revert
must also not touch any policy text**, in template or installed form, because
the commit did not.

### Verification floor

`HARNESS_READY` and `NO_HARNESS` both observed reachable. A unit that has never
observed its own failure state has not tested its precondition.

Additionally, and new at revision 4: the ACTIVATE commit is not complete until
`P1`–`P6` are verified **by reading both files after the commit**. Parity is a
property of the two artifacts, never an inference from the fact that one commit
touched both.
