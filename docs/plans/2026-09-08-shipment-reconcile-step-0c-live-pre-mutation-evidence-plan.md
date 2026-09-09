---
title: "shipment-reconcile Step 0(c): durable pre-mutation evidence record and fail-closed live-execution check"
description: "Implementation plan for the operator's accepted-with-remediation disposition of stash 856B6770 — make live execution of the Step 0(c) linked-deliberation collection PROVABLE by requiring a durable, timestamped pre-mutation evidence record emitted before the P-015 cascade invocation, failing closed when that record is absent or not provably pre-mutation, and locking the behaviour with a 159-S-pattern replay regression test that rejects post-hoc reconstruction"
source: "docs/decisions/2026-09-07-step-0c-pre-mutation-guard-reconstruction-disposition.md"
date: 2026-09-08
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
stash_entry: "856B6770"
related_stash_entries:
  - "9E22BFC6 — AF-06: the 856B6770 remediation had no trackable identity. THIS PLAN and its harvested feature/shipment are that identity."
  - "27F9EC8A — AF-07: committed stash currency gap for 856B6770. Part (a) discharged by the Stage stash disposition written alongside this plan; part (b) tracked by 162.011-T in 170-S."
compound_learnings:
  - "2026-09-06-composed-workflow-protocol-state-machine-validation (cited by title only — the compound-learning artifact is not yet committed to any branch; pending publication, tracked by stash 15A02E21 / follow-up 1CD92B69)"
  - "docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md"
  - "docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md"
  - "docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md"
  - "docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md"
decision_status_at_planning: "decided (operator, 2026-09-08) — Option A accepted-with-remediation P-005 deviation; mechanical outcome final; systemic remedy tracked as a SEPARATE sibling shipment, not folded into 169-S; no merge authorization"
related_but_distinct:
  - "2026-09-07-shipment-reconcile-cascade-premode-member-class-contract-plan (stash 15A02E21, feature 161-F, shipment 169-S; cited by title only — not yet committed to any branch, pending publication tracked by follow-up 1CD92B69) — RELATED, DISTINCT. 161-F fixes WHAT Pre-Mode compares (member-class status contract). This plan fixes WHETHER Step 0(c) ran live and is evidenced as pre-mutation. Different contract surface, different failure mode, different tests. MUST NOT be merged. Sequencing dependency only, to avoid conflicting edits to the same SKILL.md Step 0 / Cascade Sub-Procedure region."
  - "2026-09-07-review-pattern-learning-methodology-plan (feature 162-F, shipment 170-S; cited by title only — not yet committed to any branch, pending publication) — RELATED, DISTINCT. Hosted-review learning methodology. MUST NOT absorb this fix."
tags:
  - "plan"
  - "shipment-reconcile"
  - "pre-mutation-gate"
  - "p-005"
  - "p-015"
  - "fail-closed-design"
  - "dogfood-parity"
---

## Problem Frame

For the 159-S close of qualifying feature `151-F`, the Safe-Close **Step 0(c)
linked-deliberation collection** — which the skill requires **three separate times**
to run *before* the destructive cascade invocation — was **reconstructed after** the
cascade from preserved pre-close evidence (commit `1b758a16`), not executed live as a
pre-mutation gate.

The operator has dispositioned this (2026-09-08) as an **accepted-with-remediation
P-005 process deviation**: the mechanical archival outcome stands as verified and
final, Step 0(c) is permanently recorded as not executed as a live pre-mutation gate,
and the systemic fix is tracked here as a **separate** follow-up shipment.

### The specific defect this plan fixes

Step 0(c) is **required** but not **evidenced**. Nothing in the current contract
distinguishes these two histories:

| History | Step 0(c) inputs | Post-close artifact produced |
|---|---|---|
| **A — compliant**: scan ran at `T0`, cascade invoked at `T1 > T0` | read at `T0` | a report asserting the scan happened |
| **B — the 159-S history**: cascade invoked at `T1`, scan reconstructed at `T2 > T1` | read at `T2` from preserved copies | a report asserting the scan happened |

Both produce a byte-identical-looking assertion. **The current contract cannot tell
them apart, and therefore cannot enforce the ordering it states three times.**

This is worse for the *empty* result, which is exactly what 159-S produced: an
unrecorded empty linked-deliberation set is indistinguishable from a scan that never
ran at all.

### Why "the inputs were provably unchanged" does not close it

Step 0(c) serves **two separable purposes** (established in the decision artifact and
**not re-opened here**):

1. **Data supply** — produce the validated linked-deliberation ID set feeding
   `allowed_ids` / `required_ids`. Satisfiable post-hoc *iff* the inputs are provably
   unchanged. For 159-S it **was** satisfied; the archive differed from
   `git show 1b758a16:.backlogit/queue/151-F.md` only in archival bookkeeping fields.
2. **Pre-mutation halt** — detect ambiguous/torn (`RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS`)
   or missing (`RECONCILE_FAIL_SNAPSHOT_MISSING`) records **while not mutating is still
   possible**. **Never** satisfiable post-hoc, because the value of the gate is the
   preserved option to decline an irreversible cascade.

Step 0(c) exists precisely for the case where inputs are **not** recoverable.
Ratifying reconstruction in the easy case (inputs preserved) creates the precedent
that will be cited in the hard case (inputs destroyed). The fix must therefore make
live execution **provable**, not merely **required**.

### Grounded text locations (verified 2026-09-08)

| Surface | Location | Note |
|---|---|---|
| Step 0(c) linked-deliberation extension | `.github/skills/shipment-reconcile/SKILL.md` L456–L500 (`**Linked-deliberation snapshot extension (155-S, PR #407 review).**`) | resolved dogfood copy, 1082 lines |
| Paired template | `templates/skills/shipment-reconcile/SKILL.md.tmpl` L456–L500 | 1082 lines; **same line numbers**, verified |
| The three "before" statements | same files, L473–475, L487–492, L747–749 | explicit and load-bearing |
| Cascade Close Sub-Procedure | same files, L618 (`### Cascade Close Sub-Procedure …`) | step 1 is the destructive invocation |
| Two-set gate consuming the snapshot | same files, L730–L760 (step 3) | reads the Step 0(b)/(c) snapshot |
| Report output surface | same files, L63 — `.backlogit/reconcile/{shipment_id}-{mode}-{timestamp}.md` | the existing durable evidence location |
| Scenario matrix / quality criteria | same files, L1002 / L1011 | where negative scenarios are enumerated |
| Diagram | `docs/diagrams/05-shipment-reconcile-cascade-premode.mmd` (this file, and `docs/diagrams/` itself, do not yet exist on this branch or `main`) | U4 **creates** this diagram, drawing the new pre-mutation node; it is a new artifact, not an update to an existing one |
| Checksum manifest | `.autoharness/harness-manifest.yaml` (shipment-reconcile entries at L126, L201, L272, L274, L396) | skill/template edits invalidate checksums |

## Requirements Trace

Sourced verbatim from the decision artifact's Option A remediation clause. Three
requirements, no more:

| ID | Requirement | Unit |
|---|---|---|
| **RQ-1** | The Step 0(c) linked-deliberation collection MUST emit a **durable, timestamped pre-mutation evidence record** *before* the cascade invocation. | U2 |
| **RQ-2** | Close MUST **fail closed** when that record is absent or not provably pre-mutation — i.e. live execution becomes *provable*, not merely *required*. | U2 |
| **RQ-3** | A **replay/regression test over the 159-S shape** MUST fail if the collection is reconstructible after mutation. | U1a / U1b / U1c |

### Explicitly requiring no Python source change

`src/autoharness/gates/shipment_closure.py` is **not** modified. The classifier already
supplies the qualifying-feature determination Step 0(c) references; the evidence record
is an additive artifact written by the skill's own protocol, at the surface the skill
already owns (`.backlogit/reconcile/`). Same posture as 161-F.

## Implementation Units

### U1a — RED: replay fixture for the 159-S shape

Build a synthetic 159-S-shaped fixture workspace in
`tests/test_shipment_reconcile_precascade_evidence.py`:

* one shipment record, one covering **root** feature declaring `status: active`
  (the only valid pre-close state — the cascade is what archives it), its full
  descendant task set at every depth declaring `status: done`;
* one variant where the covering feature has **no** linked deliberation (the exact
  159-S/`151-F` shape, whose correct validated set is **empty**);
* one variant where it has **one** validated linked deliberation reachable via each
  of the three engine-defined sources in turn.

The fixture must model the **ordering** dimension explicitly: a recorded sequence of
(step, timestamp) events, so an assertion can ask *"did the evidence emission precede
the cascade invocation?"* rather than *"is an evidence file present?"*.

RED: this task lands the fixture plus failing assertions; it does not edit the skill.

### U1b — RED: replay assertions (ordering + reconstruction rejection)

Two assertion families over the U1a fixture:

1. **Ordering** — the documented sequence must not be able to reach the cascade
   invocation with no pre-existing evidence record. A trace in which the evidence
   record's `collection_completed_at` is absent, or is **not strictly before** the
   cascade invocation timestamp, must be rejected.
2. **Reconstruction rejection** — a trace that produces a byte-identical evidence
   record *after* the mutation (the literal 159-S history) must be rejected, and must
   be rejected **for the ordering reason**, not for a content-mismatch reason. This is
   the assertion that encodes the Purpose-1/Purpose-2 distinction: content equality is
   explicitly **not** sufficient.

Also assert the **explicit-empty** rule: an evidence record whose validated set is
empty must record `scan_performed: true` with an explicit empty list — an omitted
field must be rejected, because an unrecorded empty scan is indistinguishable from a
scan that never ran. This is the 159-S failure mode in one assertion.

### U1c — RED: section-scoped contract guard and dogfood-parity guard

A separate guard module asserting, over **both** `.github/skills/shipment-reconcile/SKILL.md`
and `templates/skills/shipment-reconcile/SKILL.md.tmpl`:

1. **Section-scoped contract presence** — the emission obligation, the two halt tokens,
   the explicit-empty rule and the anti-reconstruction clause appear **within the
   resolved Step 0(c) extension block / Cascade Close Sub-Procedure block**, located by
   heading/anchor and then asserted within that slice.
2. **Single-statement rule (D-5)** — the obligation is stated **once**; the Cascade
   Sub-Procedure references it rather than restating it. A second independent
   restatement fails the guard.
3. **Dogfood parity** — the two copies agree on the asserted region.

**Guard construction (per `2026-08-21-ast-based-structural-regression-guards-beat-line-regex`):**
these assertions MUST be **section-scoped** — never a bare file-wide regex, which
passes as soon as the required phrase appears anywhere in an 1082-line document, and
which cannot express the single-statement rule at all.

### U2 — ATOMIC CORE: pre-mutation evidence record + fail-closed live-execution check (INDIVISIBLE)

**Paired edit, SAME COMMIT:** `.github/skills/shipment-reconcile/SKILL.md` **AND**
`templates/skills/shipment-reconcile/SKILL.md.tmpl`, hand-edited in parallel. The
resolved dogfood copy is **NOT** regenerated (096-S).

**Do not split.** The two halves are one contract:

* the record without the check is an artifact nobody consults — the 159-S state, restated;
* the check without the record is an **unsatisfiable gate** — precisely the defect class
  `2026-09-06-composed-workflow-protocol-state-machine-validation` was written about,
  and the one 161-F exists to repair. Shipping half of this reproduces it.

**(a) Emission (RQ-1).** Extend the Step 0(c) linked-deliberation extension so that, on
the `CASCADE` path, before the Cascade Close Sub-Procedure's step 1 invocation, the
collection writes a durable record at
`.backlogit/reconcile/{shipment_id}-precascade-snapshot-{timestamp}.md` containing:

1. `shipment_id`, the manifest item list, and the git `HEAD` SHA at collection time;
2. the qualifying feature member set, **by reference to Step 0(c)'s own
   classification** — never a separate re-derivation (this is the existing
   reference-only rule at L733/L737; do not weaken it);
3. per qualifying feature, the three engine-defined sources read **verbatim**: the
   literal `custom_fields.source_deliberation_id` string, the description-scan matches,
   and the references-scan matches, each recorded with the resolved record location
   (`queue/` or `archive/`) that Step 0(b)'s resolution rule produced;
4. the dedup + existence + `artifact_type: deliberation` validation outcome per
   candidate ID;
5. the resulting validated ID set, recorded **explicitly even when empty**
   (`scan_performed: true`, `linked_deliberation_ids: []`) — never an omitted field;
6. `collection_completed_at`, a UTC timestamp, written and flushed **before** the
   cascade invocation.

**(b) Fail-closed check (RQ-2).** Before the Cascade Close Sub-Procedure step 1
invocation, re-read the record and halt on either of two new, **separately labelled,
independently failing** tokens (never merged into one test — same rule the two-set gate
already states at L753, whose merge is the documented root cause of `B57F9E24`):

* `RECONCILE_FAIL_PRECASCADE_EVIDENCE_MISSING` — no record for this `shipment_id`;
* `RECONCILE_FAIL_PRECASCADE_EVIDENCE_STALE` — a record exists but does not validate:
  `collection_completed_at` is absent, or is not strictly before the cascade invocation
  timestamp, or its recorded `HEAD` SHA / manifest item list does not match the state
  being closed.

Both emit a **P-005** violation and halt. Neither authorizes a fallback to safe-close.

**(c) The anti-reconstruction clause.** State explicitly, in-skill:

> A post-hoc reconstruction of this collection — **even one provably byte-identical to
> what a live scan would have read** — does NOT satisfy this check. The check is on the
> record's **pre-existence**, never on its **reproducibility**. Step 0(c) supplies data
> *and* preserves the option to decline an irreversible mutation; the second purpose is
> not recoverable after the mutation.

**(d) Single authoritative statement.** State the requirement **once**, in the Step 0(c)
extension, and have the Cascade Close Sub-Procedure **reference** it rather than restate
it. Two independent restatements drift — that is literally how `15A02E21` was born.

### U3 — Scenario matrix and quality criteria currency

Add the negative scenarios to the Deterministic Safe-Close Scenario Matrix (L1002) and
Quality Criteria (L1011), in both copies:

* **Negative — missing pre-cascade evidence**: cascade path selected, no evidence
  record ⇒ `RECONCILE_FAIL_PRECASCADE_EVIDENCE_MISSING`.
* **Negative — post-hoc reconstruction**: evidence record present but
  `collection_completed_at` is after the cascade invocation ⇒
  `RECONCILE_FAIL_PRECASCADE_EVIDENCE_STALE`.
* **Positive — empty validated set (the 159-S shape)**: evidence record present,
  `scan_performed: true`, `linked_deliberation_ids: []`, timestamp strictly before the
  invocation ⇒ **PASS**. This names the legitimate passing state required by lesson 6.

### U4 — Diagram currency (creates a new artifact)

`docs/diagrams/05-shipment-reconcile-cascade-premode.mmd` does not yet exist on this
branch or `main`. Create it, drawing the evidence emission as an explicit node on the
pre-mutation side of the cascade invocation, with both halt tokens as labelled exits.
Per lesson 2 of the composed-state-machine learning, the diagram is where the seam
becomes reviewable.

### U5 — Checksum recompute and GREEN

Recompute `.autoharness/harness-manifest.yaml` checksums for the edited skill and
template, and run the full suite green.

## Dependency Graph

```text
U1a (fixture)  ──┐
U1b (assertions) ┼──> U2 (ATOMIC CORE) ──> U3 ──┐
U1c (guards)   ──┘                     ──> U4 ──┴──> U5
```

RED units land first and must fail for the stated reason before U2; U5 is last because
it consumes every prior edit's bytes.

**Shipment-level:** this shipment carries a `blocks` dependency on **169-S**. Both edit
the same `SKILL.md` Step 0 region; 169-S is a sealed, plan-reviewed decomposition whose
`161.003-T` is marked *R-4 INDIVISIBLE ATOMIC CORE* and cannot be re-opened (PR #436 is
at its hard 3-cycle limit, P-018 blocked). Sequencing, not merging.

## Decisions and Rationale

| # | Decision | Rationale |
|---|---|---|
| D-1 | Evidence record lives at `.backlogit/reconcile/`, the skill's existing report surface | Additive write to a location the skill already owns; no new storage contract, no backlog-state mutation |
| D-2 | The check tests **pre-existence**, not reproducibility | Reproducibility is Purpose 1, already satisfied in 159-S. Purpose 2 is the one that failed |
| D-3 | Empty result must be recorded explicitly | An unrecorded empty scan is indistinguishable from no scan — the precise 159-S failure |
| D-4 | Two separate halt tokens, independently evaluated | Merging two questions into one condition is the documented root cause of `B57F9E24` |
| D-5 | Requirement stated **once**, referenced elsewhere | Independent restatements drift; that is how `15A02E21` arose |
| D-6 | Separate shipment, sequenced after 169-S | Different contract surface; 169-S's plan is sealed and cannot be re-reviewed |
| D-7 | No Python source change | The classifier already exposes everything Step 0(c) references |

## Risks and Caveats

| Risk | Mitigation |
|---|---|
| **Unsatisfiable gate** — the check can never pass | U3 names a concrete legitimate passing state (the empty-set 159-S shape). Lesson 6 check applied below |
| **Merge conflict with 169-S** in the same Step 0 region | `blocks` dependency on 169-S; U2 is authored against post-169-S text |
| **Guard passes on a phrase appearing elsewhere** in an 1082-line file | Section-scoped assertions (U1c), never file-wide regex |
| **Dogfood-parity drift** between resolved copy and template | Paired edit in the same commit; parity assertion in U1c; checksums in U5 |
| **Scope creep into 169-S or 170-S** | Explicit `related_but_distinct` frontmatter; separate feature, separate shipment |
| **Retroactive-compliance claim** | The plan and every harvested task state that 159-S remains a recorded, permanently disclosed deviation. This fix is forward-only |

## Non-Goals

* Re-opening the operator's disposition, or any part of the four-axis finding.
* Altering the 159-S mechanical archival outcome (final and verified).
* Any claim that 159-S becomes retroactively compliant. It does not.
* Touching PR #436, its body, its review threads, CI, or Ship-owned closure evidence.
* Any change to 169-S/161-F or 170-S/162-F scope.
* Any Python source change.

## Plan Hardening Signals (REQUIRED)

**Requires plan hardening: yes.** Signals present:

* modifies a **skill contract on an irreversible, destructive execution path**;
* introduces **new fail-closed halt tokens** (a gate-shaped change);
* **paired edit** across a resolved dogfood copy and its template (two template families);
* invalidates **harness manifest checksums**;
* edits a file region **another queued shipment (169-S) also edits**.

## Plan Hardening

### Learnings and instructions consulted

| Source | Bearing |
|---|---|
| `2026-09-06-composed-workflow-protocol-state-machine-validation` | Lessons 1, 2, 6, 8 applied directly. Lesson 6 ("can this gate ever be satisfied?") is discharged in H-2 |
| `2026-08-18-lifecycle-gate-must-precede-safe-close-mutation` | Same root class: a gate whose whole value is its position **before** the mutation, and which can never pass afterwards. Confirms the ordering requirement is not merely stylistic |
| `2026-08-21-ast-based-structural-regression-guards-beat-line-regex` | Guard construction — section-scoped structural assertion, never widen-the-regex whack-a-mole |
| `2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation` | Origin of the Step 0(c) linked-deliberation extension; confirms the three engine-defined sources are the complete input set |
| `2026-09-07-copilot-review-finding-pattern-taxonomy` | RC-5 cross-surface state currency — why U3/U4/U5 (matrix, diagram, checksums) are in scope, not optional polish |
| `2026-08-12-close-path-decisions-must-use-the-classifier-not-summarized-prose` | U2(a)(2) records the qualifying set **by reference to the classifier's determination**, never a prose re-derivation |

### H-1 — The requirement is already stated three times; do not add a fourth statement

L473–475, L487–492 and L747–749 all state the ordering. The defect is **not** that the
requirement is missing — it is that nothing **evidences** it. U2 must therefore add an
**evidence obligation and a check**, and must resist the temptation to add a fourth
prose restatement of "do this before". D-5 makes this binding: state the new obligation
once, reference it from the Cascade Sub-Procedure.

### H-2 — Lesson 6 discharge: name a passing state and a failing state

* **Legitimate passing state:** 159-S's own shape, executed correctly — shipment record
  + covering feature `active` + tasks `done`; Step 0(c) runs at `T0`, writes
  `scan_performed: true, linked_deliberation_ids: []`, `collection_completed_at: T0`;
  cascade invoked at `T1 > T0`; HEAD SHA and manifest match. **PASSES.**
* **Legitimate failing state:** the actual 159-S history — cascade at `T1`, collection
  reconstructed at `T2 > T1`. **FAILS** with
  `RECONCILE_FAIL_PRECASCADE_EVIDENCE_STALE`, for the ordering reason.

The gate is reachable. It is not the 161-F unsatisfiable-gate shape.

### H-3 — Protected invariants (must not regress)

1. The three engine-defined sources and the exact matcher
   `\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b` are unchanged; the evidence record **records**
   them, it does not redefine them.
2. `RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS` / `RECONCILE_FAIL_SNAPSHOT_MISSING` semantics are
   unchanged; the two new tokens are additive.
3. The reference-only rule (`allowed_ids` / `required_ids` are defined by reference to
   Step 0(c)'s determination, never re-derived) is preserved.
4. Declared status is read from frontmatter, never inferred from `queue/` vs `archive/`
   location (lesson 8; also 161-F's R-1).
5. The two-set gate's two independently-failing conditions stay unmerged.
6. `mode: detect-mixed-role` remains strictly read-only; the evidence record is written
   only on the safe-close/cascade path.

### H-4 — Ordering and lock invariants

The evidence emission happens **inside** the existing single-writer lock on
`.backlogit/queue/{shipment_id}.md`, between Step 0(c) and the cascade invocation. It
introduces no new lock, no second writer, and no new failure window. It must **not** be
hoisted before lock acquisition, or the record could describe a state another writer
then changed.

### H-5 — Risky actions

| Action | Risk | Control |
|---|---|---|
| Editing the destructive close path's contract | A wrong edit corrupts an irreversible operation | RED-first (U1a/U1b); U2 atomic; no behavioural change to the cascade call itself |
| New halt tokens on a close path | Could block legitimate closures | H-2 names the passing state; U3 encodes it as a positive matrix row |
| Hand-edited resolved copy + template | Divergence | Same-commit paired edit + parity assertion (U1c) + checksum recompute |

### H-6 — Unresolved operator decisions

**None blocking.** The disposition is decided (2026-09-08). This plan carries **no**
merge authorization for PR #436 and requests none; it neither requires nor implies any
further PR #436 review round.

## Plan Review

### Capability probe (P-012)

`backlogit` MCP transport closed; CLI fallback (`backlogit` v1.10.1) exercised and
functional — `TOOL_DEGRADED: backlogit MCP — CLI fallback: backlogit`. Engram, intercom
and graphtor-docs MCP tools not exposed in this session — `ENGRAM_DEGRADED`,
`INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`; file-based exploration used throughout, and
all cited line numbers were read directly rather than recalled.

### Persona coverage

| Persona | Finding |
|---|---|
| **Contract/protocol reviewer** | Requirement stated once, referenced elsewhere (D-5). No fourth restatement. **PASS** |
| **Fail-closed design reviewer** | Two tokens, independently evaluated, both P-005, neither authorizes safe-close fallback. Lesson 6 discharged in H-2. **PASS** |
| **Composed-state-machine reviewer** | New gate sits between Step 0(c) and the cascade call, inside the existing lock; no interaction with Pre-Mode's member-class contract (169-S) beyond textual adjacency. **PASS** |
| **Test-quality reviewer** | Section-scoped structural assertions, not file-wide regex. Reconstruction rejection asserted **for the ordering reason**, so a content-equality implementation cannot satisfy it. **PASS** |
| **Scope/width reviewer** | Skill + template + tests + diagram + checksums. No CLI, no schema, no Python source. 7 tasks, each ≤2h. **PASS** |
| **Evidence-consistency reviewer** | Plan asserts no retroactive compliance; 159-S disclosure remains permanent. Traceability to 856B6770, 9E22BFC6, 27F9EC8A carried in frontmatter. **PASS** |

### Findings

* **P1 — none.**
* **P2-1** (in-body, resolved): first draft placed the evidence emission before lock
  acquisition. Corrected in H-4 — emission is inside the lock.
* **P2-2** (in-body, resolved): first draft asserted reconstruction rejection via
  content comparison, which the 159-S history would have **passed** (its content was
  byte-identical). Corrected in U1b — rejection must be on the ordering axis.
* **P3-1** (accepted): U5's checksum task overlaps 169-S's own (absent) checksum step.
  Scoped to this feature's edits only; the `blocks` dependency makes the ordering
  deterministic.

### Gate decision

**PASS** — zero P0, zero P1. Cycle 1. Proceed to harvest.
