---
title: "Resolving the shipment-reconcile Pre-Mode vs P-015 CASCADE contract conflict"
description: "Deep deliberation on how to make Pre-Mode's per-item status gate satisfiable for a classifier-verified fully-covered-root manifest without weakening fail-closed posture, and how to disposition the already-executed 159-S close whose authorization basis remains open"
topic: "shipment-reconcile Pre-Mode expected_status contract vs the P-015 cascade close path"
depth: "deep"
decision_status: "decided"
decided_date: 2026-09-07
decided_by: "operator"
decision_summary: "Option A (classifier-aware, member-class-scoped Pre-Mode); qualifying-feature valid set active|done, archived tolerated-and-reported, queued hard HALT; declared frontmatter status read regardless of queue/archive location; 159-S recorded as an accepted-with-remediation P-005 deviation"
promoted_to: "impl-plan"
plan_path: "docs/plans/2026-09-07-shipment-reconcile-cascade-premode-member-class-contract-plan.md"
plan_review_verdict: "PASS (cycle 2 of 3; cycle 1 FAIL on four P1 findings, all remediated in-plan)"
plan_hardened: true
harvested_feature: "161-F"
harvested_tasks: "161.001-T, 161.002-T, 161.003-T, 161.004-T, 161.005-T, 161.006-T, 161.007-T"
shipment: "169-S"
shipment_status: "queued — NOT routed to Ship; blocked by open PR #436 / 159-S post-merge closure"
date: 2026-09-06
stash_entry: "15A02E21"
shipment: "159-S"
covering_feature: "151-F"
pull_request: 436
review_thread: "PRRT_kwDORzpWpM6ft_fB"
gate: "G-DIAG-REVIEW — operator review of docs/diagrams/ is a REQUIRED gate before impl-plan and harvest"
gate_status: "CLEARED — operator approved the diagram set with corrections on 2026-09-07, and recorded the OQ-1/OQ-2/OQ-3 decision package on 2026-09-07. No gate remains; impl-plan is authorized."
gate_cleared_date: 2026-09-07
revalidated: 2026-09-07
linked_artifacts:
  - "docs/bugs/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-mismatch.md"
  - "docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md"
  - "docs/diagrams/00-conventions-legend.mmd"
  - "docs/diagrams/01-orchestrator-stage-ship-lifecycle.mmd"
  - "docs/diagrams/02-orchestrator-control-flow.mmd"
  - "docs/diagrams/03-stage-workflow.mmd"
  - "docs/diagrams/04-ship-workflow.mmd"
  - "docs/diagrams/05-shipment-reconcile-cascade-premode.mmd"
  - "docs/diagrams/06-evidence-contract.mmd"
  - "docs/diagrams/eraser/01-lifecycle-overview.eraserdiagram"
  - "docs/diagrams/eraser/02-stage-at-a-glance.eraserdiagram (carries the approved Stage sizing / shipment right-sizing loop)"
  - "docs/diagrams/eraser/03-ship-and-closure-at-a-glance.eraserdiagram"
  - "docs/diagrams/eraser/04-cross-tool-contract-and-defect.eraserdiagram"
related_but_distinct:
  - "docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md (stash 7F93FA0C)"
  - "docs/bugs/2026-09-07-backlog-lifecycle-missing-temporary-out-of-queue-status.md (stash 4D3826FE — parked/hold lifecycle-vocabulary gap) — RELATED, DISTINCT: shares the member-class status matrix as a downstream consumer but is a different defect (missing status in the tool's lifecycle vocabulary, requiring an upstream backlogit change) and MUST NOT be merged into this fix's shipment"
tags:
  - "deliberation"
  - "workflow-protocol"
  - "cross-tool-integration"
  - "shipment-closure"
  - "p-015"
  - "p-021"
  - "fail-closed-design"
---

## Problem Frame

### The immediate problem

`shipment-reconcile` `mode: pre` compares **every** manifest member's declared `status` against a
**single scalar** `expected_status` (`done` at closure). A manifest that qualifies for the P-015
CASCADE close path is **required** to contain its qualifying root feature, and that feature is
validly `active` until the cascade operation itself archives it. Pre-Mode therefore classifies it
`status-mismatch` and returns `HALT — operator reconcile required` on **every** cascade-eligible
closure — before Safe-Close Step 0, the step that runs the classifier and could have known the
member was a qualifying feature, has executed.

Full technical detail, evidence, reproduction, and acceptance criteria are in the bug record:
`docs/bugs/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-mismatch.md`.

### The problem behind the problem

The operator's standing goal is a **consistent set of workflow protocols that compose cleanly, so
that autoharness and the external tools it orchestrates work together seamlessly.** This defect is
a direct counterexample: five independently authored, individually correct artifacts (Pre-Mode,
Safe-Close Step 0, the Cascade Close Sub-Procedure, the P-015 policy, and
`classify_shipment_close_path`) compose into a machine with an unsatisfiable state. Fixing only the
symptom leaves the generative cause untouched.

### Who cares and why

* **Ship** cannot close a full-feature shipment without either mutating state it is forbidden to
  mutate or overriding a fail-closed gate.
* **The operator** is asked to improvise an authorization decision at the single most consequential
  and least reversible moment in the pipeline.
* **Every future audit** inherits a merged precedent that proceeding past a literal HALT is
  acceptable when disclosed — which is corrosive to every other HALT in the system.

### Constraints

| Constraint | Source |
|---|---|
| Safe-close remains the default; CASCADE stays a narrow, machine-verified exception | P-015 |
| Qualification is never per-member and no feature ID is ever special-cased | P-015 / Safe-Close Step 0(c) |
| Pre-Mode is detect-and-report only — no auto-repair, no mutation | shipment-reconcile Behavioral Constraints |
| Classifier error, ambiguity, or unresolved precondition must default fail-closed | Safe-Close Step 0(c) |
| Declared frontmatter `status` is authoritative; queue/archive location is descriptive only | CT-1, restated throughout the skill |
| The two-set `allowed_ids`/`required_ids` gate and the pre-close snapshot must not be weakened | Cascade Close Sub-Procedure step 3; supersession note |
| autoharness may constrain backlogit transitions but may never assume one backlogit does not perform | CT-3 |
| No implementation, harvest, branch, PR, or PR #436 modification in this session | Operator instruction |

### Success criteria

1. A classifier-verified fully-covered-root manifest with an `active` qualifying feature returns
   `PROCEED` with no deviation, override, or pre-close mutation.
2. Genuine drift — a `queued` feature, a `queued`/`active` task at closure, a `missing` member, an
   `orphan` — still HALTs.
3. The skill no longer contradicts itself between Pre-Mode and the Cascade Close Sub-Procedure.
4. The fix generalises: the same reasoning is applied at every site that shares the rule, not only
   where the bug surfaced.
5. The authorization basis for the already-executed 159-S close is explicitly recorded.

### Explicitly out of scope

Fixing `7F93FA0C`; the Engram content-record schema incident; changing the P-015 default; altering
the two-set gate, the snapshot rules, or the CT-1 declared-status rule; re-opening `159-S`;
modifying PR #436; any implementation work in this session.

## Research Findings

**F1 — The manifest shape that triggers this is the normal one.** Stage's shipment assembly creates
the manifest with the covering feature **first**, then tasks in dependency order. `159-S` is
`[151-F, 151.001-T … 151.007-T]`. Full-feature shipments are therefore exactly the shape that
satisfies the classifier's full-coverage precondition — the defect targets the common case, not an
edge case.

**F2 — The same skill contradicts itself.** Cascade Close Sub-Procedure step 3 computes
`required_ids` as the shipment record plus every qualifying feature member "**both
unconditionally** — never omitted, and never conditioned on either artifact's own pre-close declared
status." Pre-Mode step 3 makes that same status decisive. Both clauses are in
`.github/skills/shipment-reconcile/SKILL.md`.

**F3 — The corrective filter already exists three times.** Ship Step 0.5 intake early-warning; Ship
Step 2 executable-task-set derivation ("artifact-type filtering always precedes any status read");
and Pre-Mode step 5's own record-scope classification — the last of which is explicitly justified
in-skill to stop a covering feature "falsely halt[ing] an otherwise-consistent shipment". Only
Pre-Mode step 3 omits it.

**F4 — The limitation is already documented for the wrong invocation.** Ship Step 0.5's scope note
states that `mode: pre` "accepts only one `expected_status` value … so it cannot represent a
legitimately mixed manifest" and warns against using it on a mixed-status resumed session. The same
reasoning was never carried to the closure invocation, where the manifest is *intrinsically* mixed
(record `active`, tasks `done`, feature `active`).

**F5 — Ordering is load-bearing.** Only `classify_shipment_close_path` (Safe-Close Step 0(c)) can
identify a member as a *qualifying feature*. It runs strictly after the Pre-Mode gate. Any fix that
requires Pre-Mode to reason about member class must move, duplicate, or pass in that determination.

**F6 — The classifier is already hardened and re-runnable.** It was previously strengthened from a
direct-children-only check to a full-depth `parent_id` walk (155-S / PR #407), it is a pure
read-only function over `queue/` + `archive/`, and the 159-S session re-ran it independently and
got an unchanged verdict. Running it earlier is cheap and side-effect-free.

**F7 — Prior-art precedent exists for narrowing a check by member class.** Pre-Mode's own
record-scope classification narrows its aggregation to task artifacts, and explicitly declares the
resulting cases mutually exclusive and exhaustive. A member-class-scoped per-item check is the same
move applied one level down.

**F8 — The instance is fully evidenced.** `docs/closure/2026-09-06-159-s-151-f-cascade-close-completion.md`
records the verbatim disclosure; `.backlogit/reconcile/159-S-pre-20260906-072505.md` holds the
Pre-Mode report; the cascade report records `returned_ids: []` and `allowed_ids == required_ids`,
with an empty protected set by construction. The outcome was correct; only the *route to it* was
contradictory.

### Findings added by the 2026-09-07 post-G-DIAG-REVIEW revalidation

**F9 — The classifier is status-blind, and that is what decides A vs B.**
`classify_shipment_close_path` reads exactly two fields per artifact: `artifact_type` and
`parent_id` (`src/autoharness/gates/shipment_closure.py` — `_ArtifactRecord` at lines 90–96,
`_read_artifact_record` at 102ff, `classify_shipment_close_path` at 284–438). It **never reads
`status`**. Two consequences, both material:

* Under **Option A**, the classifier supplies *member class only*; the status decision stays wholly
  inside Pre-Mode. A therefore does not delegate any safety property to the classifier — it borrows
  a structural classification and keeps the gate.
* Under **Option B**, no component anywhere in the pipeline validates the qualifying feature's
  declared status: Pre-Mode would skip it by artifact type, the classifier ignores `status` by
  construction, and the Cascade Close Sub-Procedure step 3 makes the feature a `required_ids` member
  "**both unconditionally** … never conditioned on either artifact's own pre-close declared status".
  B's cost is therefore not "a weakened signal" but "the signal ceases to exist", which is a direct
  failure of bug acceptance criterion 3.

**F10 — Pre-Mode's `pre-archived` is a *location* classification that short-circuits the status
read.** Pre-Mode step 3 (`.github/skills/shipment-reconcile/SKILL.md` lines 267–275; identical text
at `templates/skills/shipment-reconcile/SKILL.md.tmpl` lines 267–275) looks in `queue/` first and,
if the record is not there but is in `archive/`, classifies it `pre-archived` — *without ever
reading `status`*. That is why `.backlogit/reconcile/159-S-pre-20260906-072505.md` classifies all
seven archive-resident, declared-`done` tasks `pre-archived`. The consequence for this fix: an
archive-resident qualifying feature declaring `status: queued` would be labelled `pre-archived` and
never status-checked, under **both** A and B as currently drafted. The promise "a `queued` feature
still HALTs" holds today only for a *queue-resident* record. The member-class matrix must therefore
be specified to read declared `status` from wherever the record resides (CT-1), exactly as
Safe-Close Step 0(b)/(c) and the Cascade Sub-Procedure's pre-archived preamble already do, and
`pre-archived` must be demoted to a descriptive location label. This is the same location/status
conflation that PR #436's review already corrected once in the 159-S pre report.

**F11 — Tolerating a declared-`archived` qualifying feature is safe downstream, but must be
reported.** The Cascade Sub-Procedure states that the "already `archived` ⇒ correctly absent from
`archived_ids`" allowance "**never extends to the shipment record or to a qualifying feature member
itself**", because step 3 makes both unconditionally required; the engine's
`setArtifactStatus(featureID, StatusDone, …)` forces the feature to `done` before `archiveItems`
runs (recorded in `.backlogit/reconcile/159-S-cascade-close-20260906-073211.md` §"Shipment record
and qualifying feature — archived provenance"). So a truly-`archived` feature still transitions and
still satisfies the two-set gate. But a feature declaring `archived` while its shipment record is
still `active` is anomalous provenance (out-of-band mutation or a partial prior close). It should be
**tolerated-with-mandatory-report**, never tolerated silently.

**F12 — A degraded classifier and a genuine `SAFE_CLOSE` are indistinguishable by verdict alone.**
Every failure path in `classify_shipment_close_path` returns `ClosePath.SAFE_CLOSE` with a
distinguishing `reason` string — unreadable record, malformed frontmatter
(`BacklogUnavailableError`), unbuildable children index, unnormalizable item. The fail-closed
fallback is correct, but Pre-Mode's report MUST record the verdict **and the verbatim `reason`**,
otherwise the resulting HALT cannot be triaged as "genuine partial manifest" versus "transient
workspace read failure" and decision 3's fail-closed default becomes unactionable.

**F13 — The 159-S record is internally split between machine and narrative.**
`docs/closure/159-S-151-F-post-merge-closure.md` frontmatter declares `closure_status: READY` and
`conditions[0].satisfied: true`, which is what `closure_complete('159-S')` reads; the narrative in
`docs/closure/2026-09-06-159-s-151-f-closure.md` §"Risky Action Record" simultaneously says "Treat
this closure's `closure_status: READY` as provisional pending that disposition." Whichever OQ-1
disposition the operator selects must also retire the word *provisional*, or the provisional marker
outlives the decision that was supposed to resolve it.

## Options Evaluated

### Option A — Classifier-aware, member-class-scoped Pre-Mode (recommended)

Run the P-015 close-path classification as a new Pre-Mode step **2b**, before the gate decision, and
make its verdict plus its qualifying-feature **set** inputs to the per-item check. Then evaluate
each member against its **class**:

| Member class | Valid | Tolerated | Halts |
|---|---|---|---|
| Shipment record | `active` (via the existing record-scope classification) | — | `queued`, legacy `blocked` |
| Qualifying feature (CASCADE verdict only; membership taken **only** from the classifier set) | `active`, `done` | `archived` ⇒ `pre-archived` | `queued`, anything else |
| Task member | `done` (i.e. `expected_status`) | truly `archived` ⇒ `pre-archived`; relocated-but-`done` | `queued`, `active` |
| Any member under a `SAFE_CLOSE` verdict or classifier failure | today's strict scalar semantics, unchanged | | |

* **Pros.** Fixes the contradiction at its source; Pre-Mode's model finally matches backlogit's
  lifecycle (CT-3/CT-4); classifier-derived membership honours P-015's no-ID-special-casing rule;
  fail-closed posture preserved for every other class; consistent with F3 and F7 precedent; the
  report can record the verdict, the qualifying set, and the class applied per item, so the gate
  becomes *more* auditable, not less; the classifier-failure fallback is genuinely fail-closed.
* **Cons.** Pre-Mode gains a dependency on the classifier and an ordering change (the classifier
  now runs twice per close — once in Pre-Mode, once in Safe-Close Step 0(c)). Larger contract
  change than Option B. Two invocations must be documented as consistent (F6 makes re-running safe,
  but the skill must say so explicitly, and must state which invocation is authoritative for the
  snapshot — Step 0(c) remains authoritative).
* **Effort.** Medium.
* **Fit.** Highest. It is the only option that satisfies all five success criteria.

### Option B — Task-artifact-scoped per-item check (minimal)

Apply to Pre-Mode step 3 the **same** mandatory task-artifact filter Pre-Mode step 5 already
applies: compare only task artifacts to `expected_status`; non-task members get a presence check
only (`matched` / `pre-archived` / `missing`), never a status comparison.

* **Pros.** Smallest possible change; mirrors an existing, already-justified filter in the same
  file; no classifier dependency and no ordering change; immediately removes the inevitable HALT;
  lowest regression risk.
* **Cons.** It stops checking the feature's status **at all**. A genuinely wrong feature state — a
  `queued` feature whose tasks are all `done`, a real drift signal — would no longer be caught by
  Pre-Mode. It also fails to *express* why `active` is legitimate; it merely averts its eyes. And
  it applies the relaxation to non-task members on the `SAFE_CLOSE` path too, where a feature member
  in the manifest is a genuine anomaly worth halting on.
* **Effort.** Low.
* **Fit.** Good on symptom, weak on cause and on criterion 2.

### Option C — Formalised operator-disposition carve-out (documentation only)

Keep the check as-is and codify the "disclosed, reasoned deviation" procedure: a named override
token, a required operator authorization explicitly scoped to the status-mismatch override, and a
mandatory disclosure block in the reconcile report and closure record.

* **Pros.** No logic change, so zero regression risk; preserves and standardises the audit trail;
  could be delivered immediately as an interim measure.
* **Cons.** Makes an unsatisfiable gate a **permanent** manual step on every cascade closure; it
  guarantees the 15A02E21 authorization question recurs indefinitely; it institutionalises
  overriding a fail-closed HALT, which erodes the meaning of every other HALT (the compounding cost
  identified in the compound learning); and it leaves the intra-skill contradiction (F2) standing.
* **Effort.** Low.
* **Fit.** Poor as a durable fix. Acceptable only as a short-lived bridge.

### Option D — Pre-transition the qualifying feature to `done` before Pre-Mode

Move the covering feature to `done` so the scalar check passes.

* **Pros.** No protocol change at all.
* **Cons.** Pre-Mode is detect-and-report only; the mutation is outside Safe-Close's
  manifest-scoped mutation authority; it fabricates a lifecycle transition that backlogit's cascade
  engine performs itself (CT-3 violation); and because `required_ids` includes the feature
  *unconditionally*, the transition changes nothing downstream — it is mutation risk in exchange
  for ceremony.
* **Effort.** Low.
* **Fit.** Rejected outright.

## Trade-off Comparison

| Criterion | A — classifier-aware | B — task-filter | C — disposition carve-out | D — pre-transition |
|---|---|---|---|---|
| Removes the inevitable HALT | Yes | Yes | No (formalises the override) | Yes |
| Preserves fail-closed for other classes | Yes | Partially (loses feature-status signal) | Yes | Yes |
| Resolves the intra-skill contradiction (F2) | Yes | No | No | No |
| Honours no-ID-special-casing (P-015) | Yes (classifier-derived) | Yes (type-derived) | n/a | n/a |
| Respects "no mutation in Pre-Mode" | Yes | Yes | Yes | **No** |
| Respects CT-3 (no invented transitions) | Yes | Yes | Yes | **No** |
| Closes the 15A02E21 authorization question durably | Yes | Mostly | **No** | No |
| Auditability of the resulting report | Improved | Reduced | Improved | Unchanged |
| Regression risk | Medium | Low | None | Medium (state mutation) |
| Implementation effort | Medium | Low | Low | Low |
| Addresses the generative cause | Yes | No | No | No |

## Decision

**Recommended: Option A, with Option B's filter retained as the structural mechanism and today's
strict scalar semantics retained as the fail-closed default.**

Concretely, the recommended durable contract is:

1. **Pre-Mode step 2b (new).** Run `classify_shipment_close_path` over the loaded manifest before
   the gate decision. Record the verdict and the qualifying-feature set in the report. This
   invocation is **advisory for gating only**; Safe-Close Step 0(c) remains the **authoritative**
   invocation for the pre-close declared-status snapshot and for the two-set gate.
2. **Pre-Mode step 3 (amended).** Evaluate each member against its member class per the matrix in
   Option A. Membership in the qualifying-feature class comes **only** from step 2b's classifier
   set — never from an ID pattern, a `-F` suffix, or a named exception.
3. **Fail-closed default (unchanged in spirit).** `SAFE_CLOSE`, classifier error, ambiguity, or any
   unresolved precondition ⇒ today's strict scalar semantics for every member. This mirrors
   Step 0(c)'s existing default and means a *degraded* classifier can never widen what Pre-Mode
   accepts.
4. **Contradiction removed.** State the member-class status rules **once**, and have both Pre-Mode
   and the Cascade Close Sub-Procedure reference that single statement rather than restating status
   expectations independently. This is the specific change that prevents recurrence.
5. **Report contract.** The Pre-Mode report records: the close-path verdict, the qualifying-feature
   set, and the member class applied to each item, so an auditor can reconstruct *why* an `active`
   feature was accepted without reading the skill.

**Why A over B.** B removes the symptom but deletes a real signal (a `queued` feature with `done`
tasks is genuine drift) and leaves the skill self-contradictory. A keeps every signal, narrows the
relaxation to the one class the classifier has *positively verified*, and — crucially — makes
Pre-Mode's model of the world match backlogit's actual lifecycle instead of papering over the
mismatch. B's mechanism (class-scoped evaluation) is retained inside A; A adds the classifier so the
scoping is *justified* rather than merely convenient.

**Why not C.** C is the status quo with better paperwork. It guarantees that the authorization
question recurs on every cascade closure and it permanently normalises overriding fail-closed
gates.

**Interim posture until the fix lands.** If a cascade-eligible closure must happen before the fix
ships, use C's discipline as an explicit bridge: a *separate*, explicitly scoped operator
authorization naming the status-mismatch override, recorded in both the reconcile report and the
closure record. Do **not** rely on an authorization granted for an unrelated action.

**Decision status: `decided` (operator, 2026-09-07).** The recommendation above is now the
operator-selected contract. See "Operator Decision (2026-09-07)" below for the authoritative
decision package, and the Revalidation section for the four refinements that are binding parts of
it. Gate `G-DIAG-REVIEW` cleared 2026-09-07; `impl-plan` is authorized.

## Operator Decision (2026-09-07)

The operator recorded the following three-part decision package. It resolves **OQ-1**, **OQ-2** and
**OQ-3**, which are marked `RESOLVED` in the Unresolved Questions section below.

### D-1 — 159-S disposition (resolves OQ-1)

**Decision: record the prior 159-S close as an `accepted-with-remediation` P-005 deviation.**
Reading (ii) of OQ-1 is selected; retroactive ratification is **rejected**.

* The already-executed close is **not** reopened, reversed, or re-executed. `159-S` and `151-F`
  remain archived; the two-set gate matched exactly; every `parent_id` was preserved; the mechanical
  archival was and remains correct.
* What is recorded is that Ship **proceeded past a literal fail-closed `HALT`** on an authorization
  (`"I Authorize removal of the stale .159-S.md.lock and continue 159-S closure."`) that named only
  lock removal. That is a **P-005 process deviation**. It is **accepted** because its outcome was
  provably correct — the corrected contract adopted in D-2/D-3 would have returned `PROCEED` for
  exactly this manifest, with no override and no mutation.
* **The remediation is this fix.** The P-005 record names the shipment harvested from this
  deliberation as its remediation, so the deviation and its closure are retrievable from the same
  key.
* **Not a precedent.** The acceptance is scoped to this manifest, this classifier verdict, and this
  disclosure. It is explicitly **not** general licence to proceed past `status-mismatch`, and not
  prior art for overriding any other `HALT`.
* **Consequence (F13): the word `provisional` is retired.** `closure_status: READY` for `159-S` is
  now **unconditional**; the disposition that `READY` was provisional *pending* has been made.

### D-2 — Fix option (resolves OQ-2)

**Decision: Option A — classifier-aware, member-class-scoped Pre-Mode.** Options B, C and D are
rejected; see "Rejected Alternatives (operator-confirmed)" below.

### D-3 — Qualifying-feature status contract (resolves OQ-3)

**Decision: the qualifying-feature member class evaluates as follows.**

| Declared status of the qualifying feature | Verdict |
|---|---|
| `active` | **PASS** — valid pre-close state |
| `done` | **PASS** — valid pre-close state |
| `archived` | **TOLERATED AND REPORTED** — accepted, but recorded in the Pre-Mode report as anomalous provenance with its own label; never silently accepted |
| `queued` | **HARD HALT** — non-negotiable, non-overridable by this contract |
| anything else | **HALT** (fail-closed default) |

**And the binding read rule: the declared frontmatter `status` is read regardless of whether the
record resides in `queue/` or `archive/`.** Storage location never substitutes for, infers, or
short-circuits the declared-status read.

### The four binding refinements from revalidation

These are **part of the decision**, not commentary. They carry into `impl-plan`, `plan-harden`,
`plan-review` and harvest as acceptance criteria.

| # | Refinement | Origin | Why it is binding |
|---|---|---|---|
| R-1 | **Declared-status-over-location.** Member-class evaluation reads frontmatter `status` from `queue/` **or** `archive/`. `pre-archived` is demoted to a *descriptive location label* recorded alongside the declared status — never a substitute for it and never a short-circuit that skips the status comparison. | F10 | Without it, D-3's `queued` ⇒ HALT promise is **false** for an archive-resident feature, because today's step 3 classifies on location before ever reading `status`. The decision would be self-defeating. |
| R-2 | **`archived` is tolerate-*and-report*.** A qualifying feature declaring `archived` pre-close is accepted (the two-set gate still holds it unconditionally required) but MUST be emitted in the Pre-Mode report under its own anomalous-provenance label. | F11 | A feature declaring `archived` while its shipment record is still `active` indicates out-of-band mutation or a partial prior close. Silent tolerance would convert a real anomaly signal into nothing. |
| R-3 | **The classifier `reason` is recorded verbatim.** The Pre-Mode report records the close-path verdict **and** the classifier's `reason` string exactly as returned — not paraphrased, not summarised. | F12 | Every failure path in `classify_shipment_close_path` returns `SAFE_CLOSE` with a distinguishing `reason`. Without the verbatim string, a `SAFE_CLOSE` caused by a transient workspace read failure is indistinguishable from a genuine partial manifest, and the fail-closed default becomes untriageable. |
| R-4 | **Atomicity.** Pre-Mode step 2b (the classifier invocation) and the member-class matrix MUST land in the **same shipment**, in the same atomic task contract. No decomposition, sizing split, or sequencing may produce an interim state in which the matrix ships without the classifier. | Revalidation sequencing constraint | The natural split — "type filter now, classifier later" — reproduces **Option B exactly**, with F9's hole (no component anywhere validates the qualifying feature's status) open in production. The right-sizing loop must not be allowed to manufacture the rejected option as an intermediate state. |

Only regression tests, documentation, diagram currency, template-parity edits and the OQ-5 policy
lift may be sequenced into separate tasks.

### Rejected Alternatives (operator-confirmed)

| Rejected | Why rejected |
|---|---|
| **Option B — task-artifact-scoped filter only** | **Disqualifying, not merely weaker.** Under B *no component anywhere in the pipeline* validates the qualifying feature's declared status: Pre-Mode would skip it by type, the classifier never reads `status` (F9), and the Cascade Sub-Procedure holds the feature unconditionally required regardless of status. The signal does not weaken — it ceases to exist. Fails bug acceptance criterion 3. |
| **Option C — formalised operator-disposition carve-out** | Makes an unsatisfiable gate a permanent manual step on every cascade closure; guarantees the `15A02E21` authorization question recurs indefinitely; institutionalises overriding a fail-closed HALT and thereby erodes every other HALT; leaves the intra-skill contradiction (F2) standing. Retained **only** as a short-lived interim bridge, never as the end state. |
| **Option D — pre-transition the feature to `done`** | Violates Pre-Mode's detect-and-report-only no-mutation constraint; fabricates a lifecycle transition backlogit's cascade engine performs itself (CT-3); and is downstream-irrelevant because `required_ids` includes the feature unconditionally. Mutation risk in exchange for ceremony. |
| **Retroactive ratification of the 159-S close (OQ-1 reading (i))** | Removes the P-005 retrieval key entirely, severing the deviation from its remediation, and leaves the merged closure artifact's "proceeded past a literal HALT" narrative as *unlabelled* prior art — precisely the corrosion the compound learning warns about. |
| **Special-casing feature IDs (a `-F` suffix rule) instead of the classifier** | Explicitly forbidden by P-015: qualification is never per-member and no feature ID is ever special-cased. |
| **Excluding the covering feature from the manifest** | Contradicts the classifier's full-coverage precondition and would flip the verdict to `SAFE_CLOSE` — the wrong close path for a full-feature shipment. |
| **Merging this fix with `7F93FA0C`, or with the `parked`/`hold` lifecycle gap** | Same defect *class*, different surfaces, different fixes, and in the `parked`/`hold` case a different *tool*. Merging couples independent remediations and obscures both. |


## Revalidation after G-DIAG-REVIEW (2026-09-07)

**Gate outcome: `G-DIAG-REVIEW` PASSED** — the operator approved the diagram set with corrections,
including a new explicit Stage work-sizing and shipment-right-sizing loop now drawn in
`docs/diagrams/eraser/02-stage-at-a-glance.eraserdiagram` and in
`docs/diagrams/03-stage-workflow.mmd` (`V_CREATE`/`V_SIZE`/`V_CPLX` → `V_AXES` → granularity gate
`V_GATE` → rollup `B_SIZE` → right-sizing gate `B_RIGHT`). `decision_status` remains `exploring`:
the gate that blocked planning has cleared, but the operator decision on OQ-1/OQ-2/OQ-3 has not
been made and Stage will not make it (P-009).

**Validity of the three pending decisions.** All three *questions* remain valid and unanswered.
Two *recommended answers* survive unchanged; one is materially refined:

| # | Question | Question still valid? | Recommended answer after revalidation |
|---|---|---|---|
| 1 | 159-S disposition: accepted-with-remediation vs retroactive ratification | Yes — `15A02E21` is still open and `docs/closure/2026-09-06-159-s-151-f-closure.md` still calls `READY` *provisional* | **Strengthened.** Accepted-with-remediation, now also because the P-005 label is the retrieval key that ties the deviation to its remediation shipment; ratification would sever it (F13) |
| 2 | Option A (classifier-aware, member-class-scoped) vs Option B (type-filter only) | Yes | **Strengthened, and B is now disqualifying rather than merely weaker** — under B *no component at all* validates the qualifying feature's status (F9) |
| 3 | Qualifying-feature status set `active \| done`, `archived` tolerated, `queued` HALT | Yes | **Refined, not overturned.** The set is right; how membership in it is *read* was wrong (F10), and `archived` must be tolerate-and-report, not tolerate-silently (F11) |

**Effect of the new Stage sizing loop on each decision: none on substance, one new constraint on
sequencing.** The loop governs how the eventual fix is decomposed and how large a shipment may be —
it is downstream of every one of these three decisions and changes no contract, no status
semantics, and no authorization question. The one real interaction is a hazard it introduces:
Option A's scope (skill + paired template + Ship agent + agent template + tests) is large enough
that the right-sizing gate will want to split it, and the most natural split — "ship the type filter
now, add the classifier later" — produces, in the interim, a system that behaves *exactly* like
Option B, i.e. with F9's hole open in production. **Constraint to carry into harvest: Pre-Mode step
2b (classifier invocation) and the member-class matrix MUST land in the same shipment.** Only
regression tests, documentation, template-parity edits and the P-015 policy lift (OQ-5) may be
sequenced separately.

**Corrections to the recommended Option A contract** (supersede the corresponding rows/clauses
above; the Decision section's five numbered items are otherwise unchanged):

1. **Declared status is read from wherever the record resides.** The member-class evaluation reads
   the frontmatter `status` field of every member from `queue/` **or** `archive/`, and never infers
   status from location. `pre-archived` becomes a descriptive location label recorded alongside the
   declared status, never a substitute for it, and never a short-circuit that skips the status
   comparison (F10). Without this correction, Option A's own fail-closed promise ("a `queued`
   feature still HALTs") is false for an archive-resident feature.
2. **`archived` is tolerated *and reported*.** A qualifying feature whose declared status is
   `archived` before close is accepted (the two-set gate still holds it as unconditionally required
   — F11) but MUST be recorded in the Pre-Mode report as anomalous provenance with its own label,
   so a silent bypass is impossible and an auditor sees the anomaly.
3. **The report records the classifier `reason` verbatim**, not only the verdict, so a `SAFE_CLOSE`
   caused by a workspace read failure is distinguishable from a genuine partial-manifest
   `SAFE_CLOSE` (F12).
4. **Scope note.** Because Pre-Mode step 3's text is byte-identical in
   `.github/skills/shipment-reconcile/SKILL.md` and
   `templates/skills/shipment-reconcile/SKILL.md.tmpl`, the defect and all four corrections above
   are paired edits by construction.

**New contradictions introduced by the sizing correction: none.** `docs/diagrams/03-stage-workflow.mmd`
and `docs/diagrams/eraser/02-stage-at-a-glance.eraserdiagram` agree on the loop's existence,
placement (post-plan-approval, spanning harvest, gating shipment assembly) and its two-axis
`size`/`complexity` rule. The single difference is loop-back granularity — the eraser diagram
returns to "Estimate the scope of the work", the Mermaid diagram returns to `V_DECOMP` — which are
the same action at two levels of detail, not conflicting instructions. Nothing in the sizing loop
touches Pre-Mode, P-015, the cascade path, or the 159-S authorization question.


* **Option D (pre-transition the feature).** Violates Pre-Mode's no-mutation constraint and CT-3,
  and is downstream-irrelevant because `required_ids` includes the feature unconditionally.
* **Option C as the durable fix.** Retained only as an interim bridge; rejected as the end state
  because it makes an unsatisfiable gate permanent.
* **Excluding the covering feature from the manifest.** Contradicts the classifier's full-coverage
  precondition and would flip the verdict to `SAFE_CLOSE` — a different and, for a full-feature
  shipment, incorrect close path.
* **Special-casing feature IDs (e.g. a `-F` suffix rule) instead of using the classifier.**
  Explicitly forbidden by P-015: "qualification is never per-member, and no feature ID is ever
  special-cased."
* **Merging this fix with `7F93FA0C`.** Same defect *class*, different surfaces, different fixes.
  Merging them would couple two independent remediations and obscure both.

## Scope and Non-Goals

**In scope for the eventual implementation.**

* `.github/skills/shipment-reconcile/SKILL.md` — Pre-Mode steps 2b/3/7, the Output classification
  table, and the single authoritative member-class status statement.
* `templates/skills/shipment-reconcile/SKILL.md.tmpl` — the paired template edit (dogfood
  paired-edit maintenance contract).
* `.github/agents/_ship.agent.md` and `templates/agents/_ship.agent.md.tmpl` — the Step 5 closure
  pointer and the Step 0.5 scope note, updated to reference the member-class contract.
* `src/autoharness/gates/shipment_closure.py` — only if the classifier needs a callable surface
  suitable for the earlier invocation; no change to its classification logic.
* Regression tests per bug acceptance criterion 8.

**Non-goals.** Everything listed under "Explicitly out of scope" in the Problem Frame, plus: any
change to the two-set gate or snapshot rules; any change to `mode: post`, `mode: safe-close`
steps 1–10, or `mode: detect-mixed-role`; any relaxation for task members.

## Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Widening Pre-Mode accidentally admits a genuinely drifted feature | High | The relaxation applies **only** to the classifier-identified qualifying-feature set, **only** under a `CASCADE` verdict, and **only** for `active`/`done`; `queued` still HALTs. Regression test (b) in the bug record covers this. |
| Classifier failure silently widens acceptance | High | Fail-closed by construction: any classifier error/ambiguity falls back to today's strict scalar semantics. Regression test (d). |
| Two classifier invocations disagree (TOCTOU between Pre-Mode and Step 0(c)) | Medium | Step 0(c) remains authoritative; a disagreement is itself a halt condition, consistent with the existing `returned_ids`/engine-mismatch handling. Document explicitly. |
| Contract restated in two places drifts again | Medium | The single-statement requirement (decision item 4) is the direct anti-recurrence control; it is also acceptance criterion 5. |
| Template/skill pair drift (installed copy vs `templates/`) | Medium | Paired-edit maintenance contract; the resolved `.github/skills/` copy is manifest-tracked and checksum-verified. |
| Operators cite the 159-S deviation as precedent before the fix lands | Medium | The interim posture requires a *separately scoped* authorization; the bug record and this artifact both state that the deviation is not general licence. |
| Scope creep into `7F93FA0C` or Engram | Low | Explicit non-goals in all three artifacts. |

## Migration and Compatibility

* **Backward compatibility.** For a `SAFE_CLOSE` verdict, behaviour is **byte-identical** to today.
  Only the `CASCADE` path changes, and only for the qualifying-feature member class.
* **backlogit compatibility.** No new status values, no new transitions, no schema change. The fix
  *removes* an assumption about a transition backlogit does not perform (CT-3); it adds none.
* **Already-closed shipments.** Unaffected. The change is a gate-evaluation change only; no
  historical artifact is rewritten and no archived record is touched.
* **In-flight shipments.** A shipment mid-execution is unaffected until its closure invocation.
  There is no migration step and no data change.
* **Report schema.** The Pre-Mode report gains fields (verdict, qualifying set, per-item member
  class). Consumers read reports narratively today, so this is additive; existing reports remain
  readable.
* **Self-hosting order.** The installed `.github/skills/` copy and the `templates/` source must
  change together in one shipment to avoid a checksum/manifest divergence.

## Verification Plan

1. **Unit / classifier.** `classify_shipment_close_path` behaviour is unchanged — assert identical
   verdicts on the existing fixtures.
2. **Gate behaviour (the four cases in bug acceptance criterion 8).**
   (a) fully-covered root, feature `active` ⇒ `PROCEED`;
   (b) same manifest, feature `queued` ⇒ `HALT`;
   (c) partial-feature manifest (`SAFE_CLOSE`) ⇒ today's strict behaviour, unchanged;
   (d) classifier raises/errors ⇒ strict behaviour, fail-closed.
3. **Task-class regression.** A `queued` or `active` task at closure still ⇒ `HALT`; a truly
   archived task still ⇒ `pre-archived`; a relocated-but-`done` task still ⇒ tolerated.
4. **Orphan and record-scope regression.** Orphan scan and the four record-status cases unchanged.
5. **Downstream invariance.** The two-set gate, snapshot, and `returned_ids` checks are untouched —
   assert via the existing cascade-close tests.
6. **Replay of the 159-S shape.** Reconstruct the 159-S manifest shape as a fixture and assert the
   corrected Pre-Mode returns `PROCEED` **without** any deviation, override, or mutation — i.e. the
   documented deviation would not have been necessary under the corrected contract.
7. **Contract-consistency check.** Assert that the member-class status rules appear in exactly one
   authoritative location and that Pre-Mode and the Cascade Close Sub-Procedure reference it rather
   than restating it.
8. **Diagram currency.** `docs/diagrams/05-*.mmd` is updated to mark the proposed path as shipped
   and remains structurally valid.

## Unresolved Questions

* **OQ-1 — RESOLVED 2026-09-07 by operator decision D-1: accepted-with-remediation.** *(Original
  question and analysis retained below for the audit trail.)* How is the **already-executed** 159-S
  close dispositioned? Two viable readings: **(i) retroactive ratification** — the operator records that
  the lock-removal authorization plus the disclosed deviation was sufficient, on the evidence that
  the corrected contract would have returned `PROCEED`, `returned_ids` was `[]`, `allowed_ids ==
  required_ids`, and the protected set was empty by construction; or **(ii) accepted-with-remediation**
  — the deviation is recorded as a P-005 process deviation that is accepted because its outcome was
  provably correct, with the protocol fix as the remediation. *Stage's assessment: (i) and (ii)
  differ only in labelling, and (ii) is the more conservative and more honest record. Either way the
  disposition must be written down.* **This is an operator decision, not an agent decision (P-009).**
  *Revalidation addendum (2026-09-07):* Stage's assessment is now **stronger than "differ only in
  labelling"**. The two dispositions diverge on retrieval and on precedent: `accepted-with-remediation`
  keeps a P-005 record that names this fix as its remediation, so a future auditor who searches
  P-005 deviations finds both the event and its closure; `retroactive ratification` records that
  the authorization *was* sufficient, which removes the P-005 key entirely and leaves the merged
  closure artifact's "proceeded past a literal HALT" narrative as unlabelled prior art — precisely
  the corrosion the compound learning warns about. Neither disposition reverses, reopens, or
  re-executes anything: `159-S` and `151-F` are archived, the two-set gate matched exactly, every
  `parent_id` was preserved, and that mechanical archival is correct and stays as-is. Whichever is
  chosen must also retire the word *provisional* in
  `docs/closure/2026-09-06-159-s-151-f-closure.md` (F13).
* **OQ-2 — RESOLVED 2026-09-07 by operator decision D-2: Option A.** Should Pre-Mode depend on the
  classifier (A) or stay classifier-free and merely scope
  its per-item check by artifact type (B)? A trades a small ordering dependency for a real signal
  and for internal consistency.
* **OQ-3 — RESOLVED 2026-09-07 by operator decision D-3: `active | done` valid, `archived`
  tolerated-and-reported, `queued` hard HALT, declared status read regardless of location.** Should
  `done` be a *valid* pre-close state for a qualifying feature, or only `active`?
  Accepting both is more permissive but avoids a second unsatisfiable-gate risk if any future path
  does transition the feature first. *Revalidation addendum (2026-09-07):* keep `active | done` as
  the exact valid set. Narrowing to `active`-only re-creates the unsatisfiable-gate failure mode
  the moment any path (a resumed session, a manual operator transition, a future engine change)
  leaves the feature `done`, and `done` is provably harmless downstream because the engine forces
  the feature to `done` anyway before archiving it. `queued` remains a hard HALT — it is the one
  state that means "this feature's work was never claimed", which contradicts a manifest whose
  tasks are `done`. `archived` is tolerated **and reported** (F11), and every one of these
  judgements must be made against the declared `status` field read from whichever directory holds
  the record (F10). Task members are unchanged: `done` valid, truly-`archived` and
  relocated-but-`done` tolerated, `queued`/`active` HALT.
* **OQ-4.** On classifier failure, is reverting to strict semantics correct given that it
  re-creates the HALT for a cascade manifest? (Stage's view: yes — a HALT you can escalate is
  strictly better than a widened gate you cannot audit.)
* **OQ-5.** Should the member-class contract be lifted into `.github/policies/workflow-policies.md`
  (as a P-015 sub-clause) rather than living only in the skill, so future skills inherit it?
* **OQ-6.** Should `plan-review`/`plan-harden` gain a standing "name a legitimate state that passes
  this gate, and one that fails it" check, per the compound learning's recommendation 6? This would
  generalise the fix to the whole protocol surface.

## Gate: Operator Diagram Review (G-DIAG-REVIEW) — CLEARED 2026-09-07

**This deliberation does not promote to `impl-plan` or `harvest`.** The next step is explicitly an
operator review gate.

Before any implementation planning or backlog decomposition may begin, the operator must review
`docs/diagrams/` (files `00`–`06`) and confirm that the workflows as drawn match the intended
protocol design, answering in particular the review questions embedded in
`docs/diagrams/05-shipment-reconcile-cascade-premode.mmd` and **OQ-1 through OQ-3** above.

Rationale: the recommendation changes a **fail-closed gate** on the irreversible path of the
pipeline. The diagrams exist so that the composed state machine can be inspected as a whole —
which is precisely the validation step whose absence caused this defect (see the compound learning).
Proceeding to `impl-plan` without that review would repeat the generative error.

**Gate outcome required:** `APPROVED` (with or without diagram corrections) before `impl-plan`.
Stage will not self-approve this gate (P-009).

**Gate outcome recorded (2026-09-07): `APPROVED WITH CORRECTIONS`.** The operator reviewed the
diagram set and approved it with corrections, including the new explicit Stage work-sizing and
shipment-right-sizing loop (`docs/diagrams/eraser/02-stage-at-a-glance.eraserdiagram`;
`docs/diagrams/03-stage-workflow.mmd`). The diagram gate no longer blocks `impl-plan`.

**Remaining blocker — CLEARED 2026-09-07.** The operator's decisions on **OQ-1**, **OQ-2** and
**OQ-3** are recorded in "Operator Decision (2026-09-07)" above. `decision_status` is now `decided`
and `impl-plan` is authorized. See the Revalidation section for the four binding refinements
(R-1..R-4), of which **R-4 (atomicity)** is the one sequencing constraint the sizing loop must
respect: step 2b and the member-class matrix must ship together.

**Still open, and deliberately NOT blocking (carried forward, not resolved here):** OQ-4 (Stage's
recommended answer — revert to strict semantics on classifier failure — is adopted as the fix's
fail-closed default), **OQ-5** (lifting the member-class contract into
`.github/policies/workflow-policies.md` as a P-015 sub-clause; sequenceable as a separate task per
R-4) and **OQ-6** (a standing `plan-review`/`plan-harden` "name a legitimate passing state and a
legitimate failing state" check; out of scope for this shipment).

**Separately raised by the operator on 2026-09-07 and routed to its own contract surface:** the
absence of an explicit *temporary out-of-queue* lifecycle status (`parked`/`hold`). Recorded in
`docs/bugs/2026-09-07-backlog-lifecycle-missing-temporary-out-of-queue-status.md` as
**related-but-distinct** (stash entry `4D3826FE`, kind `bug`, priority `high`,
`requires deliberation: yes`, **name not decided** — the operator offered `parked` *or* `hold` and
chose neither; Stage recommends `parked` with rationale in that record). It shares this fix's
member-class status matrix as a downstream consumer,
but it is a different defect (a missing value in backlogit's lifecycle *vocabulary*, requiring an
upstream tool change) and it MUST NOT expand this shipment. The one forward-compatibility
obligation it places on this fix is recorded as **R-5** below.

**R-5 — forward-compatibility (added 2026-09-07; obligation only, no scope expansion).** The
member-class matrix authored by this fix MUST treat an **unrecognised declared status as an explicit
HALT row**, not a silent fall-through or an implicit "not one of the listed values, therefore
tolerate". This costs nothing now — `anything else ⇒ HALT` is already D-3's fail-closed default —
and it guarantees that if a future `parked`/`hold` status is ever introduced upstream, it surfaces
as a loud, triageable HALT that forces a deliberate contract decision, rather than being silently
absorbed by whichever branch happens to catch it. This is the *same* generative failure this whole
deliberation exists to fix, applied prospectively.


---

## Downstream Outcome (2026-09-07) — planned, hardened, reviewed, harvested

This decision is CLOSED and has been carried through the full Stage pipeline in the same session.

| Stage gate | Result |
|---|---|
| impl-plan | `docs/plans/2026-09-07-shipment-reconcile-cascade-premode-member-class-contract-plan.md` (units U1-U7) |
| plan-harden | **Completed and required** — fail-closed gate on an irreversible close path; invariants I-1..I-4 verified against classifier source |
| plan-review | **PASS** at cycle 2 of 3 (cycle 1 **FAIL**, four P1 findings, all remediated in-plan) |
| harvest | feature **161-F** + 7 tasks, test-first ordering, two-axis sizing applied |
| shipment | **169-S**, `queued`, high — **not routed to Ship** |

### Two corrections this decision record must carry

1. **The "byte-identical" claim in this document is wrong.** The skill and its template are identical
   *modulo* `{{BACKLOG_DIRECTORY}}`; exactly three lines differ in the step-3 block (268, 272, 277).
   The parity guard must therefore be **two-sided** (resolved copy has zero unresolved `{{...}}`;
   template has zero literal `.backlogit`), which is what U6 implements.

2. **R-1 consolidates an existing rule rather than introducing a new one.** Safe-Close Step 0(b)
   *already* states that location alone is never sufficient. Pre-Mode did not lack the rule — it
   failed to apply a rule the same file already states. This strengthens the anti-recurrence
   argument and is why U2 must also bring Step 0(b) under the single authoritative block; otherwise
   the fix would leave the rule stated in three places instead of one.

### Material scope reduction

`classify_shipment_close_path` already exposes `close_path`, `reason`, and `qualifying_feature_ids`.
**No Python source change is required.** The change is Markdown + tests only, with no runtime
surface — materially smaller than this document's original in-scope estimate.

### Execution blocker

**169-S must not be routed to Ship** while PR #436 / the 159-S post-merge closure release unit is
open. 169-S is additionally the named **P-005 remediation** for the D-1 deviation, so its closure
record must reference the 159-S deviation record recorded in
`docs/closure/2026-09-06-159-s-151-f-closure.md`.
