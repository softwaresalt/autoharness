---
title: "Foundation: Ship pre-task harness-generation lifecycle"
description: "Installs the Ship pre-task harness-generation LIFECYCLE that invokes the actor policy P-004 already names. At revision 2 the ACTOR INSTALL ITSELF is no longer performed here - it moved to the narrow one-time precursor 188-S, because this unit could not bootstrap itself through an actor that did not exist. At revision 4 the unit is re-grounded in live workspace state: the Ship agent TEMPLATE already carries a harness-generation section and the INSTALLED MIRROR carries none, so this unit RECONCILES THE EXISTING TEMPLATE SECTION IN PLACE - never duplicating it - and INSTALLS the corresponding dogfood mirror section in the SAME commit, reaching template/mirror parity rather than assuming it. At revision 5 the two remaining non-blocking P2 findings are closed at their root: the mirror's 'Step 2' reference set is replaced by an EXACT THREE-CLASS PARTITION derived line-by-line from live content (one heading, five top-level cross-references, four procedure-local lowercase sub-step references), making parity criterion P6 truthful and satisfiable while preserving the conservative Step-1.5 insertion; and the D/G/P label vocabulary is UNIFIED on the plan's numbering across the plan and all three consuming task records, extended to G1-G8 so no failure-mode check is lost. At revision 6 the single open P2 (S12) is corrected at its root: the claim that class-A and class-B lines all lie ABOVE the insertion point and do not shift is WITHDRAWN as false for class A, because the class-A heading at :336 IS the insertion successor and necessarily shifts. The exact truthful stability is now carried consistently on the plan, 181.004-T, 181.005-T, 181-F, 187-S and the verdict manifest: class B's five upstream references are line-number stable, class A is the shifted successor heading that must be re-located and re-validated by exact whole-line heading identity, and class-C lines below the insertion point shift. No gate may require the pre-insertion class-A line number after insertion. It also defines the lifecycle states including an explicit NO_HARNESS failed-precondition state. Closes the assumed-skill bootstrap gap at its root so the P-004 gate work in 176-S consumes an installed producer instead of an assumption. At revision 8 that producer is a COMPLETED FACT rather than pending precursor work: .github/skills/harness-architect/SKILL.md is part of the PUBLICATION BASELINE, installed at exact manifest checksum parity by the bounded Auto-Tune harness-maintenance commit 07b4be79263252b1820701fd123d0aed85c1db2a; the precursor 188-S and its feature 182-F are RETIRED AND ARCHIVED WITHOUT EVER HAVING BEEN CLAIMED, EXECUTED OR SHIPPED; and 187-S is an explicit dag-root with no shipment dependencies. Revision 8 restates those external facts ONLY and changes NO reviewed criterion, task contract, blast radius, rollback bound, verification floor or sizing. INSTALLATION ALONE CONFERS NO TASK CLAIM."
doc_type: plan
source: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
date: 2026-09-18
plan_id: ship-harness-lifecycle-foundation
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_role: active
revision: 8
revision_scope: graph-fact-synchronization-only
revision_8_note: "Revision 8 is a GRAPH-FACT SYNCHRONIZATION ONLY and is NOT a remediation, not a correction log and not a re-scoping. The harness-architect actor is now part of the publication baseline, installed by the bounded Auto-Tune harness-maintenance commit 07b4be79263252b1820701fd123d0aed85c1db2a at exact manifest checksum parity; 188-S and 182-F are retired and archived WITHOUT EVER HAVING BEEN CLAIMED, EXECUTED OR SHIPPED; and 187-S carries the dag-root label because its only prerequisite was 188-S. This revision restates those external facts wherever this plan asserted them as future work. NOTHING THE TERMINAL REVIEW JUDGED HAS CHANGED: D1-D3, G1-G8, P1-P6, the three-class A/B/C partition, the S12 addressing rule, the conservative Step 1.5 insertion, the no-renumbering rule, the ACTIVATE three-file contract, the D11 manifest-parity binding, the blast radius, the rollback confinement, the verification floor, the task set, the task edges and every size/complexity value are ALL UNCHANGED AND BYTE-IDENTICAL IN SUBSTANCE."
verdict: null
verdict_is_pass: false
verdict_revision: null
verdict_asserted_against_revision: null
disposition: PENDING-INDEPENDENT-REVIEW
publication_eligible: false
publication_eligible_basis: "No independent review has judged revision 8."
historical_verdict_revision_7: PASS
historical_verdict_revision_7_attempt: 6
historical_verdict_is_not_carried_forward: true
verdict_note: "NO VERDICT IS ASSERTED AGAINST REVISION 8. Revision 8 has NOT been independently reviewed. THE VERDICT CARRY-FORWARD IS WITHDRAWN: revision 8 formerly carried attempt 06's PASS forward on the basis that no reviewed criterion had changed. That carry was STAGE REASONING ABOUT A VERDICT, and a verdict is not Stage's to extend - only an independent attempt may determine that a revision passes. The carry-forward fields (verdict_carried_to_revision, verdict_carry_basis, verdict_carry_claim_is_falsifiable) are REMOVED, not restated. HISTORICAL AND STILL TRUE, SCOPED TO REVISION 7: independent attempt 06 judged REVISION 7 and returned PASS with zero P0, zero P1, zero P2 and one carried P3 (S13); acceptance-matrix criteria A1-A4 were GitHub-dependent, NOT OBSERVABLE in that session and expressly NOT asserted, while A5-A8 passed locally. That record stands as the review history of revision 7 AND OF NO LATER REVISION. CURRENT STATE: revision 8 awaits independent plan-review attempt 07 against revision 8 itself. NO attempt 07 has been opened, registered or rostered, and Stage opens none. THIS PLAN IS NOT PUBLICATION-ELIGIBLE until that current-revision independent review returns. WHAT REVISION 8 CHANGED is stated in revision_8_note and is a graph-fact synchronization only; that characterisation is STAGE'S DESCRIPTION OF ITS OWN EDIT AND IS AN INPUT TO THE PENDING REVIEW, NOT A SUBSTITUTE FOR IT, and attempt 07 is free to reject it. INDEPENDENT OF THE REVIEW AXIS: S13 (P3) remains the single finding carried against this plan, held as a non-blocking follow-up in stash 703B6FAF under the operator's standing disposition and outside this shipment's scope. Publication eligibility and task claimability remain DISTINCT GATES and neither is satisfied by the other; nothing here authorizes execution."
awaiting_attempt: 7
awaiting_attempt_against_revision: 8
latest_attempt: 6
latest_attempt_reviewed_revision: 7
review_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 6
source_stash_ids:
  - 76EBDE6D
source_stash_note: "Corrected at revision 4 (finding S9). The governing decision's portfolio table assigns 76EBDE6D to this unit by name - docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md line 993, row 'P4 | 187-S | 181-F | foundation | 76EBDE6D' - and every live carrier already cites it: the 187-S title and body, 181-F, 181.002-T and 181.005-T. 76EBDE6D is an ARCHIVED stash entry, retrievable at .backlogit/archive/stash.jsonl line 234: 'P-021 RELIABILITY FOLLOW-UP: P-004 red-phase precondition is unsatisfiable on this workspace.' That is this unit's genuine origin. The prior value 3EF5AAF2 was a MIS-CITATION, not a second genuine source: the same decision table assigns it at line 995 to 177-S / 169-F, the post-claim member-status portfolio, and it is the declared source of docs/plans/2026-09-18-post-claim-member-status-contract-plan.md. It has no relation to the Ship harness-generation lifecycle. This unit is SINGLE-SOURCE; no multi-source relation is claimed because none exists."
feature_id: 181-F
shipment_id: 187-S
unit_role: precursor-foundation
depends_on_shipments: []
removed_depends_on_shipments:
  - 184-S
  - 188-S
dag_root: true
dag_root_note: "187-S is an explicit dag-root: its ONLY prerequisite was 188-S, and that unit is retired because the harness-architect actor it was to install is now part of the publication baseline. ROOT STATUS IS A GRAPH FACT, NOT AN EXECUTION AUTHORIZATION. Execution of this unit's tasks still requires ordinary pre-claim checks, this unit's OWN P-002 / P-004 harness generation at claim time, independent review, CI and closure. INSTALLATION ALONE CONFERS NO TASK CLAIM."
actor_installed_in_baseline: true
actor_installed_by_commit: 07b4be79263252b1820701fd123d0aed85c1db2a
actor_artifact: .github/skills/harness-architect/SKILL.md
actor_artifact_sha256: 49f6bae3945bf823aecbe959fa38197c05325d19b14d5608e5b0b47eeda41716
bootstrap_precursor_plan: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
bootstrap_precursor_status: RETIRED-SUPERSEDED-COMPLETED-EXTERNALLY
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
work, executed against an actor that is **already present in the publication
baseline**, with no special authority of any kind.

**What this unit no longer owns.** Generating
`.github/skills/harness-architect/` from its template. That single file is
**already installed**, by the bounded Auto-Tune harness-maintenance commit
`07b4be79263252b1820701fd123d0aed85c1db2a`, at exact manifest checksum parity.

**No waiver anywhere on this path.** No bootstrap grant is consumed, written or
inherited here; no `--force` is used and no force-audit log is touched. Because
the actor exists in the baseline, the **full** mechanical P-004 evidence —
`py_compile` exit 0 and a failing `unittest discover` carrying the expected RED
markers — is genuinely produced by this unit's own harness generation at claim
time rather than suspended. If the lifecycle is not installed, P-004 still fails
closed.

**Dependency:** this unit declares **no** shipment predecessor. `187-S` is an
explicit `dag-root`. That is a graph fact, not an execution authorization.

## What P-004 already requires

The live policy's precondition is not vague and does not need amending:

> `python -m py_compile src/autoharness/cli.py` exits 0 **and**
> `python -m unittest discover` exits non-zero

and its postcondition records `Compilation: PASS` and `Red Phase: CONFIRMED`.

This matters for scope: attempt-08's P0 on `176-S` (the gate omits the
compilation channel) is a **regression against live policy**, not a gap in it.
`176-S` restores the observation; this unit supplies the **lifecycle step** that
produces the state the observation reads. The actor that step invokes is part of
the publication baseline, not produced here.

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
2. **`### Step 2` means two different things in the two files, and the mirror's
   own `step 2` references are of three different kinds.** In the template
   `### Step 2` is Harness Generation; in the mirror it is the Task Execution
   Loop (`:336`). **Renumbering any existing mirror step is forbidden** — but
   the reason must be stated exactly, because revisions 3 and 4 stated it
   loosely and finding `S10` was right to reject the looseness.

   A case-**insensitive** search for `step 2` in `.github/agents/_ship.agent.md`
   returns exactly ten lines: 184, 214, 275, 283, 302, 305, 326, 336, 377, 748.
   That citation set is exact and complete. It is **not**, however, ten
   cross-references to the Task Execution Loop. It partitions into three
   **disjoint and exhaustive** classes, re-derived line by line against live
   content:

   | Class | Lines | Count | What it is |
   |---|---|---|---|
   | **A — definition** | 336 | 1 | The heading `### Step 2: Task Execution Loop` itself. A definition, not a reference. |
   | **B — top-level cross-references** | 275, 283, 302, 305, 326 | **5** | Capital-`S` `Step 2`, all inside `### Step 0.5: Work Intake` (`:209`–`:328`), each resolving to the class-A heading. **These are the references renumbering would invalidate.** |
   | **C — procedure-local sub-step references** | 184, 214, 377, 748 | 4 | Lowercase `step 2`, each resolving to a numbered **item 2 of its own enclosing procedure**, never to the top-level step sequence. |

   The partition is mechanically checkable: a case-**sensitive** search for
   `Step 2` returns exactly the six class-A+B lines, a case-sensitive search for
   `step 2` returns exactly the four class-C lines, and 6 + 4 = 10.

   Each class-C line resolves locally, and to a different procedure:

   | Line | Enclosing procedure | Local item 2 it denotes |
   |---|---|---|
   | 184 | Crash-Resumption / Startup Recovery Protocol, `ZERO-CANDIDATE NORMAL STARTUP` | `:183` — "Fail closed on validation/quarantine anomalies FIRST" |
   | 214 | `### Step 0.5: Work Intake` | `:215` — "Verify all tasks have clear scope and acceptance criteria", i.e. the scope/status validation the line names |
   | 377 | `### Step 2: Task Execution Loop`'s **own** numbered list | `:358` — "Begin telemetry context", the item that produces the `context_ref` the line names |
   | 748 | `#### Closure Tasks` | `:674` — "Close the shipment via single-artifact safe-close", the item that archives |

   **No class-C line is affected by inserting a new top-level section**, at
   `Step 1.5` or anywhere else, because none of them is resolved against the
   top-level step sequence at all.
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
first runs, because it is part of the publication baseline. No task in this unit
exercises the
phase against `.github/skills/harness-architect/`; `181.004-T` exercises it
against a fixture template in a scratch root instead.

## The ACTIVATE contract, stated mechanically

`181.005-T` performs **one commit** over **exactly three files**: the two Ship
surfaces below, and the single `.autoharness/harness-manifest.yaml` entry that
records the installed one. **Two surfaces are edited; the third file is the
manifest entry that describes one of them.** Everything an executor needs to
avoid producing a duplicate section is fixed here, and the manifest member adds
no heading, no anchor and no gate to any of it.

**Manifest parity is part of that same atomic unit (decision `D11`).**
`.github/agents/_ship.agent.md` is a **manifest-tracked installed artifact**
with an `artifacts:` entry recording a `sha256` of its pre-insertion content;
`templates/agents/_ship.agent.md.tmpl` is **not** tracked, because the manifest
tracks no template, so this commit refreshes **exactly one** manifest entry. In
the **same commit** and the **same rollback unit**, rewrite that checksum to
the `sha256` of the installed mirror *as written by this commit*, then **verify
checksum parity** by re-digesting the installed file and comparing it against
the recorded value. A commit that inserts `### Step 1.5` into the mirror
without that refresh leaves the manifest asserting a digest of a file the same
commit has already rewritten — an installed-artifact parity hole in a unit
whose entire purpose is closing a template-versus-mirror parity gap — and is an
**immediate revert**, not a fixup commit. The refresh is a **commit member, not
a third surface**: `D1`–`D3`, `G1`–`G8` and `P1`–`P6` all remain scoped to the
two Ship surfaces exactly as written below, and none of them reads the
manifest. This binds a **future implementation commit**; it authorizes no
staging-time edit to the live manifest, and none has occurred.

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
| G8 (post) | Occurrences of the D2 and D3 literals in the mirror | **exactly 1 each** | FAIL the commit — an anchor heading was renumbered, retitled or consumed by the insertion. |

`G8` is new at revision 5. It is **not** a new requirement: it is the
anchor-integrity check that revision 4 carried only inside the `181.005-T`
record, under a label (`G6`) that collided with the plan's. Finding `S11`
required one canonical vocabulary; promoting the check to `G8` satisfies that
**without dropping the coverage it provided**.

**Every gate above is a COUNT of a whole-line literal, never a line-number
assertion (clarified at revision 6, finding `S12`).** `G3` and `G8` are
satisfied by *exactly one* whole-line `D2` match and *exactly one* whole-line
`D3` match **wherever those lines now sit in the file**. `G8` runs
**post-commit**, when `D2` has already shifted from `:336` to `:336 + N`; it
MUST NOT be evaluated at, or read against, the pre-insertion line number.
No gate in this family requires the pre-insertion class-A line number after
the insertion.

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
* It renumbers **nothing**, so the mirror's **five** class-B top-level `Step 2`
  cross-references (`:275`, `:283`, `:302`, `:305`, `:326`) continue to resolve
  to `### Step 2: Task Execution Loop`, and its class-A heading keeps its
  **step** number — `Step 2` — which is a statement about the heading's *text*
  and says **nothing** about its *line* number. The four class-C lowercase
  references were never at risk from a top-level insertion and remain
  unaffected as *references*.
* **Line-number stability, stated exactly (corrected at revision 6, finding
  `S12`).** This bullet previously read "every class-A and class-B line lies
  **above** the insertion point (`:336`), so **none of their line numbers
  changes**… only the class-C lines at `:377` and `:748` shift". That statement
  is **WITHDRAWN as false for class A**, and all three of its sub-claims are
  withdrawn with it. The class-A line **is** `:336`; `D2` defines the insertion
  as occurring immediately **before** it; therefore the class-A heading is the
  **insertion successor** and **necessarily shifts**. The truthful statement is:

  | Lines | Position relative to the insertion point (`:336`) | Effect of the commit |
  |---|---|---|
  | **Class B — `:275`, `:283`, `:302`, `:305`, `:326`** (all five) | strictly **above** | **LINE-NUMBER STABLE.** Unchanged by the commit. |
  | **Class C — `:184`, `:214`** | strictly **above** | **LINE-NUMBER STABLE.** Unchanged by the commit. |
  | **Class A — `:336`** (the heading itself) | **IS** the insertion point; the insertion goes immediately before it | **SHIFTS** to `:336 + N`, where `N` is the inserted block length. |
  | **Class C — `:377`, `:748`** | strictly **below** | **SHIFT** to `:377 + N` and `:748 + N`. |

  Consequences, stated so no reader or executor can re-derive the withdrawn
  claim:

  * **Class B's five upstream references are the ONLY line-number stability
    this unit asserts as load-bearing**, and they are exactly the set `P6b` is
    evaluated against. Class C's `:184`/`:214` are stable too, but no gate or
    criterion reads them.
  * **The class-A heading MUST be re-located and re-validated by exact,
    whole-line, case-sensitive heading identity** — the literal
    `### Step 2: Task Execution Loop` — **after** the insertion. Its
    pre-insertion line number `:336` is a **pre-insertion locator only** and
    is invalid as a post-insertion address.
  * **NO GATE, CRITERION OR HALT CONDITION MAY REQUIRE THE PRE-INSERTION
    CLASS-A LINE NUMBER AFTER THE INSERTION**, and none does: `P6a` is a
    property of heading **text**; `P6b` names **class-B** lines only; `D1`–`D3`
    match **whole lines**, not line numbers; `G1`–`G8` are **counts**. `G8`'s
    post-commit anchor-integrity check is satisfied by *exactly one* whole-line
    `D2` match **wherever it now sits**, not at `:336`.
  * None of the shifting is a parity violation. The conservative `Step 1.5`
    outcome, the no-renumbering rule and the three-class partition are
    **unchanged** by this correction — only the line-number stability claim is
    corrected.
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
| P6 | Two clauses, both required. **`P6a`** — **no other heading in either file is added, removed, renumbered or retitled.** **`P6b`** — the mirror's **five** class-B top-level `Step 2` cross-references (`:275`, `:283`, `:302`, `:305`, `:326`) still resolve to `### Step 2: Task Execution Loop`. **Those five line numbers remain valid post-commit because all five lie strictly above the insertion point and are line-number stable** (see *The mirror section's heading and placement*), whereas **the class-A target heading itself SHIFTS and is resolved by exact whole-line heading identity, never by its pre-insertion line number `:336`**. `P6b` is scoped to class B **deliberately**: the four class-C lowercase references (`:184`, `:214`, `:377`, `:748`) resolve to numbered item 2 of their own enclosing procedures and are not resolved against the top-level step sequence, so requiring them to resolve to the Task Execution Loop would state an invariant that **never held** and would fail a perfectly correct commit. See *Live state of the two ACTIVATE targets*, consequence 2, for the three-class partition. |

`P6` was a single clause through revision 4, and its second half asserted that
**ten** references resolve to the Task Execution Loop. Finding `S10` showed
that four of the ten never did, so the criterion could not be satisfied even by
a correct commit. Splitting it into `P6a`/`P6b` and scoping `P6b` to the five
references that genuinely resolve there makes the criterion **true** and
**mechanically satisfiable** while protecting exactly the same commit. The
conservative instruction it supports — renumber nothing, use `Step 1.5` — is
**unchanged**.

Parity is a **post-commit property of two files**, verified by reading them —
not an inference from the fact that one commit touched both.

### The canonical label vocabulary (revision 5, finding `S11`)

**This section is the single authoritative definition of the `D`, `G` and `P`
label space for this unit.** Finding `S11` found two authoritative surfaces
answering differently to the same label: `181.005-T` had defined `D2`/`D3`
swapped relative to the plan, had re-used `G5`/`G6`/`G7` for different
referents, and had shifted `P1`–`P6` by one — while `181.003-T` and
`181.004-T` cross-referenced *the plan's* numbering. A contract whose stated
purpose is to be mechanical cannot do that.

The divergence is resolved by **adopting the plan's vocabulary everywhere**, not
by adding aliases. Aliases would leave exactly the ambiguity `S11` objected to.

| Family | Canonical range | Defined in |
|---|---|---|
| `D1`–`D3` | detection literals | *Detection — exact literals, no fuzzy matching*, above |
| `G1`–`G8` | counted gates (`G1`–`G3` pre-commit, `G4`–`G8` post-commit) | *Duplicate prevention — counted, not asserted*, above |
| `P1`–`P6` | parity criteria (`P6` = `P6a` + `P6b`) | *Parity criteria — what "at parity" means, exactly*, above |

Every consuming record now uses these referents and only these:

| Record | Cites | Status at revision 5 |
|---|---|---|
| `181.003-T` | `D1`–`D3`, `G1`–`G8`, `P1`–`P6`; content contract bound to `P3`, `P4`, `P5` | `G1`-`G7` → `G1`-`G8`; referents already matched |
| `181.004-T` | pre-commit `G1`–`G3`; records the class-A/B/C partition for `P6b` | `G1`-`G7` → `G1`-`G8`; ten-line predicate replaced by the partition |
| `181.005-T` | `D1`–`D3`, `G1`–`G8`, `P1`–`P6` | **rewritten** — swapped `D2`/`D3` corrected, private `G5`/`G6`/`G7` and shifted `P1`–`P6` removed |

**Coverage is preserved, failure mode by failure mode.** Nothing detectable
under revision 4's two label sets is undetectable under revision 5's single one:

| Failure mode | Detected by (canonical) |
|---|---|
| Template section appended with an identical heading | `G1`/`G4` — count becomes 2 |
| Template section appended with the same title, different step number | `G5`; `P1` |
| Template heading retitled, moved or deleted | `G1` (pre), `G4` (post), `P1` |
| Mirror section absent or wrongly headed | `G6`, `P2` |
| Mirror section written as a renumbered `### Step N: Harness Generation` | `G7` |
| A mirror **anchor** heading renumbered, retitled or consumed | `G8` — *the check formerly carried only as the record's private `G6`* |
| Any **other** mirror heading renumbered or retitled | `P6a` |
| A class-B top-level `Step 2` cross-reference broken | `P6b` |
| Unresolved `{{...}}` left in the mirror section | `P5` |
| Semantic drift between the two sections | `P3`, `P4` |

The one gap `S11` identified — renumbering a **non-anchor** mirror heading being
caught by the plan's `P6` but by none of the record's gates — is closed, because
`P6a` is now the record's own criterion rather than a differently-numbered one.
The record's former `G7` ("the two sections satisfy parity `P1`–`P6`") is
**removed rather than renumbered**: it was a wrapper that restated parity inside
the gate family, and parity is asserted explicitly and separately. Removing it
loses no check and ends the collision on `G7`.

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
`.github/skills/harness-architect/SKILL.md` is **already installed in the
publication baseline**. The resolver therefore observes a surface that
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
installed `.github/skills/harness-architect/SKILL.md` — **present in the
publication baseline, and consumed here read-only as a satisfied
precondition** — and
returning `NO_HARNESS` against a scratch harness root in which a required
surface is absent. It additionally asserts the pre-commit gates `G1`–`G3` hold
against live file content, so a stale premise is caught **before** activation
rather than during it, and it **re-derives and records the class-A/B/C `step 2`
partition** so that `P6b` is evaluated post-commit against a recorded five-line
class-B set rather than re-derived under time pressure. The scratch-root
exercise uses a fixture template under
the test tree; it never writes under `.github/skills/`, and it never generates
the `harness-architect` deliverable.

**ACTIVATE.** `181.005-T` — **one task, one commit**, transcribing the fixture
text into both surfaces simultaneously: **update in place** the template's
existing `### Step 2: Harness Generation (P-002 / P-004)`, and **insert** the
mirror's new `### Step 1.5: Harness Generation (P-002 / P-004)` at the fixed
anchor. Those two files are the **only** surfaces this commit may change, and
`G1`–`G8` plus `P1`–`P6` bound it.

> Splitting this across commits produces a reachable state in which exactly one
> of the two Ship surfaces declares the phase. Today the workspace is already
> in the template-ahead form of that state; a split would merely replace it
> with the mirror-ahead form. Only a single commit that reconciles both at once
> ends the divergence rather than reversing its direction. Sequential task
> edges are not atomic.

**No task in this unit generates, installs, modifies or deletes
`.github/skills/harness-architect/SKILL.md`.** That file is part of the
publication baseline and this unit's precondition.

## Tasks

| ID | Phase | Task | Size | Cx |
|---|---|---|---|---|
| `181.001-T` | RED | lifecycle-state contract tests incl. `NO_HARNESS` reachability | S | medium |
| `181.002-T` | PREPARE | harness-surface requirement resolver (Python, `src/`) | S | medium |
| `181.003-T` | PREPARE | author the canonical phase **text** as test-owned fixture data — **agent-procedure design, no Python** | S | medium |
| `181.004-T` | VERIFY | lifecycle evidence + pre-commit gates `G1`–`G3`, actor already present in the publication baseline, no live reference yet | XS | low |
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
  (3) `G4`–`G8` and `P1`–`P6` make the commit's success a counted, mechanical
  property instead of a claim. It is not split further because the atomicity
  requirement is precisely that both files move together — splitting it would
  reintroduce the defect it exists to prevent.
* All five tasks remain within the 2-hour envelope. No task exceeds it, and the
  one remaining `complexity: high` task carries the de-risking above.
* **Held unchanged at revision 5.** Revision 5 unifies a label vocabulary and
  corrects a stated predicate; it removes ambiguity rather than adding work, so
  neither axis moves on any task. The unit's composition stays
  `S`/`S`/`S`/`XS`/`M` with `unsized: 0`, and `181.005-T` is **again held** at
  `M`/`high` rather than shrunk on the strength of a sharper contract.
* **Held unchanged at revision 6.** Revision 6 corrects one false stability
  claim and states the truthful one in its place across the plan, `181.004-T`
  and `181.005-T`. It adds no surface, no file, no gate and no step; it
  replaces one recorded assertion with a better-specified assertion of the same
  shape, and adds one addressing rule that constrains *how* an already-required
  check is performed. Neither axis moves on any task. The composition stays
  `S`/`S`/`S`/`XS`/`M` with `unsized: 0`; `181.004-T` stays `XS`/`low` and
  `181.005-T` is **again held** at `M`/`high`.

**No task in this unit generates `.github/skills/harness-architect/`**, at
revision 2, 3, 4, 5, 6, 7 or 8. It is part of the publication baseline, and
`181.004-T` observes it as an already-satisfied precondition rather than
producing it.

**No task in this unit produces Python at `181.003-T`.** The `src/` deliverable
of this unit is the resolver and the state contract, authored by `181.002-T`
and tested by `181.001-T`. `181.003-T` produces Markdown fixture text only.

## Out of scope

* The P-004 gate's own three-channel observation logic — `176-S` owns it and
  consumes this unit's `HARNESS_READY` state.
* Any edit to policy P-004's text. Its precondition is correct as written;
  this unit satisfies it rather than changing it.
* Generating `.github/skills/harness-architect/` itself. It is already present
  in the publication baseline; this unit consumes it.
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
| R1 | The `harness-architect` template is stale relative to current skill conventions | The installed actor is part of the publication baseline at exact manifest checksum parity; `181.004-T` re-observes frontmatter and structure before activation, so a stale template fails VERIFY here rather than landing broken. |
| R2 | The lifecycle step slows every shipment start | The resolver short-circuits when all required surfaces are already present, which is the steady state after the first execution. |
| R3 | `NO_HARNESS` becomes a routine blocker | It is only reachable when a required surface has no authoritative template. The resolver reports the missing template path, so the remedy is explicit rather than a retry loop. |
| R4 | The ACTIVATE commit appends a **second** harness-generation section to the template instead of updating the existing one | The primary risk of this unit, and the defect `S7` caught. Detection is by exact heading literal (`D1`); the outcome is **counted** both before (`G1`) and after (`G4`, `G5`). A pre-count other than exactly 1, or a post-count other than exactly 1, halts or fails the commit. Plan and record both say **update in place**; neither says "add". |
| R5 | The mirror insertion renumbers an existing step and silently breaks its internal `Step 2` cross-references | The mirror section is `Step 1.5`, chosen so nothing is renumbered. `P6a` forbids renumbering any heading, `P6b` asserts the **five** class-B top-level cross-references (`:275`, `:283`, `:302`, `:305`, `:326`) still resolve, `G7` detects a renumbered `Step N: Harness Generation` and `G8` detects a renumbered anchor. `181.004-T` records the class-A/B/C partition pre-commit so the post-commit check is mechanical rather than a re-derivation. The four class-C lowercase references are procedure-local and out of scope of this risk. |
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
| H1 | Is the lifecycle phase real, or does it just assume the actor it invokes? | Real, and the assumption is exactly what it removes. `181.004-T` observes the resolver returning `HARNESS_READY` only after it has actually located `.github/skills/harness-architect/SKILL.md` and matched it against its authoritative template, and returning `NO_HARNESS` against a scratch root where a required surface is absent. This unit does not generate the actor and does not validate it into existence: the actor is part of the publication baseline at exact manifest checksum parity, so a stale or non-conforming surface is caught by `181.004-T`'s own pre-commit observation rather than assumed away. |
| H2 | Could `NO_HARNESS` be silently treated as a pass? | It is a distinct terminal state, and the P-004 gate in `176-S` consumes it as a failed precondition. The rule is the same one this portfolio applies everywhere: an unobserved precondition is not a satisfied one. |
| H3 | Does this unit amend policy P-004? | No, and it must not. P-004's precondition already requires `py_compile` exit 0 and a non-zero test run. The defect is an implementation that stopped observing one channel. Amending the policy would delete the requirement instead of satisfying it. No task in this unit may edit `.github/policies/workflow-policies.md` or `templates/policies/`, in the ACTIVATE commit or anywhere else. |
| H4 | Why not a waiver or a force flag? | Both were evaluated and rejected. A waiver suspends the gate for exactly the case it exists to catch, and an override reachable by the agent it constrains is not a gate. |
| H5 | Does the phase run on every task? | Pre-task, per shipment, short-circuiting when all required surfaces are present — which is the steady state, because the actor is in the publication baseline. A per-task full re-resolution would be a cost with no added guarantee. |
| H6 | Could the resolver install surfaces beyond the one required? | It resolves; it does not install. Only `harness-architect` is required by this portfolio and it is already present in the publication baseline. Generating anything in the ACTIVATE commit would widen it past its stated contract and is out of scope. |
| H7 | Could reverting this unit remove the installed actor? | No, and the Rollback section states so explicitly. The ACTIVATE commit touches exactly three files — the Ship agent template, its installed mirror, and the single `.autoharness/harness-manifest.yaml` entry recording that mirror — so its revert cannot reach `.github/skills/harness-architect/` **or** that file's own manifest entry, which belongs to the publication baseline and which this unit never touches. |
| H8 | Does anything in this unit still assume it installs the actor? | It must not, and the propagation is the risk. At revision 4 the Rollout, Blast radius, Rollback, this pass, the Tasks table, the Out-of-scope list and **all five** task records state the same reduced scope. A single surface left at revision-1 framing is what blocked revision 2, because Ship executes records rather than narrative. |
| **H9** | **Does the ACTIVATE commit's target already contain the section this unit intends to add?** | **Yes — and revision 3 did not know it.** `templates/agents/_ship.agent.md.tmpl:326` already carries `### Step 2: Harness Generation (P-002 / P-004)`. This is now the governing fact of the unit: the template section is **updated in place**, never re-added, under exact-literal detection `D1` and counted gates `G1`/`G4`/`G5`. An instruction to "add the step to both files" is withdrawn from the plan and from every record, because against a file that already has the section it authorizes exactly the duplicate this unit must not produce. |
| **H10** | **Is the stated atomicity hazard the drift that actually exists?** | **It was not; it is now.** Revision 3 argued against "the installed mirror has a lifecycle step its template does not declare". The live drift is the exact inverse — template ahead, mirror empty. The argument is replaced: a split commit would not create divergence, it would merely **reverse the direction** of the divergence that already exists. Only a single commit reconciling both surfaces ends it. The conclusion (one commit) survives; the reasoning that reached it does not, and has been rewritten rather than patched. |
| **H11** | **Could the mirror insertion break the mirror's own internal cross-references?** | It could, and that is why the heading is `Step 1.5` rather than `Step 2`. The mirror's `### Step 2` is `Task Execution Loop` (`:336`), and **five** passages — `:275`, `:283`, `:302`, `:305`, `:326`, all inside `### Step 0.5: Work Intake` — are genuine top-level cross-references to it. Revisions 3 and 4 said **ten**, conflating those five with the file's four *lowercase*, procedure-local `step 2` references (`:184`, `:214`, `:377`, `:748`) and with the heading itself; finding `S10` rejected that, and the three-class partition under *Live state of the two ACTIVATE targets* replaces it. The corrected count does **not** weaken the answer: renumbering is still forbidden by `P6a`, the five surviving references are asserted by `P6b`, `G7` detects a renumbered harness heading and `G8` detects a renumbered anchor. Fractional numbering is already this file's own convention (`Step 0.1b`/`0.1c`/`0.1d`/`0.5`), so the insertion introduces no new document grammar. |
| **H12** | **Is `181.003-T` genuinely inert if the phase text lands in a live file?** | It would not be — which is why it no longer does. `181.003-T` writes the canonical text to **test-owned fixture paths**, and `181.005-T` transcribes it into the two live surfaces. Had `181.003-T` edited the template in place it would have modified the template's **executed** `Step 2` while claiming to be inert, and the activation commit would no longer have been atomic across both surfaces. This is the `169.011-T` pattern: author the canonical source as data, transcribe it at ACTIVATE. |
| **H13** | **Does any gate, criterion or evidence requirement address a line that the commit itself moves?** | **It did — at revision 5, in the evidence record, and finding `S12` caught it.** Revision 5 asserted that class-A and class-B lines all lie *above* the insertion point and do not shift. The class-A line **is** the insertion point (`:336`), so the heading it names is the insertion **successor** and shifts by the inserted block length. Revision 6 withdraws that claim and states the stability exactly: class B's five upstream references are line-number stable and are the only stability the unit relies on; class-C `:184`/`:214` are also stable but unread; class A shifts and **must be re-located and re-validated by exact whole-line heading identity**; class-C `:377`/`:748` shift. The corrected statement does **not** weaken anything: no gate ever depended on the false claim (`P6a` is heading text, `P6b` is class-B only, `D1`–`D3` are whole-line matches, `G1`–`G8` are counts), and the rule is now stated positively — **no gate may require the pre-insertion class-A line number after the insertion**. The conservative `Step 1.5` insertion, `P6a`/`P6b` and the three-class partition are unchanged. |

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
* **`.autoharness/harness-manifest.yaml`** — **exactly one** `artifacts:`
  entry, the one recording `.github/agents/_ship.agent.md`, its `checksum`
  refreshed in the same commit and the same rollback unit per decision `D11`.
  No other entry is created, refreshed or rewritten, and no
  `declared_surface_count` anywhere in the portfolio moves: the manifest is a
  commit member, not a declared surface.
* **No new installed skill.** The `harness-architect` actor is already present
  in the publication baseline; this unit neither generates, modifies nor removes
  it.
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
* restores the `.autoharness/harness-manifest.yaml` `checksum` for
  `.github/agents/_ship.agent.md` to its pre-commit value, **together with**
  the mirror itself, because the refresh and the insertion are one commit and
  one rollback unit — the manifest is never left describing a file the revert
  has changed back;
* renumbers nothing in either file, because the commit renumbered nothing.

**The post-revert state is the pre-`187-S` steady state**, which is the
template-ahead drift described under *Live state of the two ACTIVATE targets* —
a **known**, pre-existing condition this unit inherited, not a new one it
creates. Naming that plainly matters: a reviewer must be able to tell that the
revert restores a documented prior state rather than leaving fresh divergence.

**The revert must not touch `.github/skills/harness-architect/SKILL.md`.** That
file is part of the publication baseline, it is not produced by this unit, and
every
code-bearing shipment in the portfolio is gated on its existence. Deleting it
would turn a unit-scoped revert into a portfolio-wide regression. **The revert
must also not touch any policy text**, in template or installed form, because
the commit did not.

### Verification floor

`HARNESS_READY` and `NO_HARNESS` both observed reachable. A unit that has never
observed its own failure state has not tested its precondition.

Additionally, and unchanged in substance since revision 4: the ACTIVATE commit
is not complete until `P1`–`P6` are verified **by reading both files after the
commit**. At revision 5 `P6` is verified as its two clauses `P6a` and `P6b`,
and `P6b` is evaluated against the **five** class-B cross-reference lines
recorded by `181.004-T` — not against the ten-line case-insensitive occurrence
set, which finding `S10` showed could not be satisfied. Parity is a
property of the two artifacts, never an inference from the fact that one commit
touched both.

**Addressing rule, added at revision 6 (finding `S12`).** Post-commit
verification reads the mirror at its **post-commit** state. The five class-B
lines (`:275`, `:283`, `:302`, `:305`, `:326`) are still addressable by number
because they lie above the insertion point and do not move. **The class-A
target heading is NOT**: it has shifted to `:336 + N` and MUST be found by the
exact whole-line literal `### Step 2: Task Execution Loop`. Any verification
step, evidence assertion or gate that reads the class-A heading at `:336`
**after** the commit is reading a stale address and is a defect in the
verification, not evidence of a parity failure.

**Manifest-parity floor, added at revision 7 (decision `D11`).** The ACTIVATE
commit is not complete until the `.autoharness/harness-manifest.yaml`
`checksum` for `.github/agents/_ship.agent.md` has been rewritten to a fresh
`sha256` of the post-commit mirror **and** that equality has been re-derived by
digesting the file again and comparing. Parity here is the same kind of claim
as `P1`-`P6`: a property of the artifacts, read after the commit, never an
inference from the fact that the commit intended to update both. This floor is
scoped to that **one** entry; no other manifest entry is read, refreshed or
asserted by this unit, and `.github/skills/harness-architect/SKILL.md`'s entry
belongs to the publication baseline and is untouched here.
