---
title: "P-004 red-phase observation gate - BLOCKED requirements contract"
description: "BLOCKED. This is a requirements and decision contract, not an implementation plan. Revision 8 deliberately STOPS specifying implementation detail, because every such detail written before the foundations exist has been fiction: the operation registry, transport envelope, exec primitive and harness-surface resolver this gate must consume are all undelivered, so their exact module paths, signatures and schemas CANNOT be known yet. Revisions 6 and 7 were reviewed against invented surfaces and failed for that reason. Revision 8 records WHAT the gate must be true of, WHAT was learned from attempts 01 and 02, and WHAT must exist before any of it can be specified. It has NO live feature, NO tasks and NO shipment. NO INDEPENDENT REVIEW ATTEMPT IS SCHEDULED OR AUTHORIZED; review resumes only after 185-S and 187-S have shipped and Stage has re-derived the exact delivered surfaces."
doc_type: plan
source: docs/plans/2026-09-18-p004-observation-gate-plan.md
date: 2026-09-18
plan_id: p004-observation-gate
plan_path: docs/plans/2026-09-18-p004-observation-gate-plan.md
plan_role: blocked-requirements-contract
status: blocked
revision: 8
revision_scope: full-rewrite-as-blocked-requirements-contract
revision_8_note: "Revision 8 CHANGES THE KIND OF DOCUMENT THIS IS. Revisions 1-7 were implementation plans for a gate whose every dependency is undelivered, and each was reviewed against surfaces that do not exist: attempt 01 blocked on live carriers encoding a superseded design (O1); attempt 02 blocked on a derivation contract whose sentinel the installed actor does not emit (O11), a result schema the specified runner cannot populate (O14), a self-referential digest (O16) and a transport envelope that was asserted rather than specified (O17). THE COMMON CAUSE IS NOT POOR DRAFTING. It is that an implementation plan for an unbuilt substrate can only be guesswork, and reviewing guesswork consumes attempts without converging. Revision 8 therefore withdraws the invented implementation detail, preserves the VALIDATED DESIGN DIRECTION as requirements, and BLOCKS. No attempt 03 is scheduled or authorized."
blocked: true
blocked_on:
  - 185-S
  - 187-S
blocked_reason: "This gate consumes four surfaces that do not exist: the operation registry and transport envelope (184-S, itself archived and withheld), the fixed-argv exec primitive (185-S / 179-F), the harness-surface resolver and its typed result (187-S / 181-F), and a harness-architect actor whose emitted marker grammar is whatever those units settle on. Their exact module paths, function signatures, result schemas and registration mechanics CANNOT be specified in advance. Writing them speculatively is what produced O5, O7, O14, O17 and O19."
unblock_condition: "BOTH 185-S and 187-S have actually SHIPPED, AND Stage has re-derived from the delivered code the exact registry API, exec-primitive signature, resolver entry point and result schema, CLI and MCP registration paths, and manifest entries. Only then may this document become an implementation plan again."
verdict: null
verdict_is_pass: false
verdict_asserted_against_revision: null
disposition: BLOCKED-PENDING-FOUNDATIONS
publication_eligible: false
publication_eligible_basis: "BLOCKED. Publication eligibility requires an independent PASS against the current revision, and NO REVIEW IS SCHEDULED. Attempt 02 returned FAIL against revision 7; that is the standing verdict and it is not carried forward as an assertion about revision 8."
last_independent_verdict: FAIL
last_independent_verdict_attempt: 2
last_independent_verdict_revision: 7
verdict_note: "NO VERDICT IS ASSERTED AGAINST REVISION 8, AND NONE WILL BE SOUGHT UNTIL THE UNBLOCK CONDITION IS MET. The verdict manifest at review_manifest is the SOLE AUTHORITY for review state; these fields are POINTERS. Revision 8 CLOSES NO FINDING: O1-O25 all remain open, and they are NOT recorded as addressed-pending-review, because revision 8 does not attempt to address them - it withdraws the premise that they could be addressed yet."
awaiting_attempt: null
awaiting_attempt_against_revision: null
review_scheduled: false
review_authorized: false
review_resumption_condition: "Independent review resumes ONLY after 185-S and 187-S have shipped AND Stage has re-derived the exact delivered surfaces. Requesting an attempt before then repeats the attempt-01 and attempt-02 failure mode and is not authorized."
latest_attempt: 2
latest_attempt_reviewed_revision: 7
review_manifest: docs/reviews/2026-09-18-p004-observation-gate-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 8
decision_state_machine: SM-1
source_stash_ids:
  - 76EBDE6D
feature_id: null
shipment_id: null
carriers_status: RETIRED-NEVER-EXECUTED-PERMANENTLY
retired_carriers:
  - 176-S
  - 168-F
  - 168.001-T
  - 168.002-T
  - 168.003-T
  - 168.004-T
  - 168.005-T
  - 168.006-T
  - 168.007-T
  - 168.008-T
  - 168.009-T
  - 168.010-T
  - 168.011-T
  - 168.012-T
retired_carriers_note: "PERMANENTLY RETIRED. These records are NEVER restored, revived or re-opened under any restoration clause. The underlying requirement - that P-004 declares a red-phase precondition with no executable producer - REMAINS OPEN and is carried by this document. When the unblock condition is met, Stage harvests a FRESH feature, task set and shipment under NEW IDs against the then-current repository state. Retiring the carrier retired the superseded DESIGN, never the requirement."
held_successor_shipment: 168-S
held_successor_note: "168-S declares dependencies ['166-S', '176-S'] and 176-S is archived, so 168-S is UNCLAIMABLE. That is a deliberate FAIL-CLOSED HOLD, not an oversight. The edge is preserved as a truthful record of what 168-S was sequenced behind. It is cleared ONLY by an operator-directed re-sequencing of 168-S onto the fresh replacement shipment once one exists. NOTHING HERE MAY BE READ AS MEANING 176-S CAN SHIP - it cannot, ever."
unit_role: gate-requirements
supersedes_plan: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
harvest_gate: "NO HARVEST. Stage creates a fresh feature, task set and shipment only after the unblock condition is met AND this document has been rewritten as an implementation plan AND that plan holds an independent PASS. No empty or perpetually blocked queued shipment is created in the interim."
depends_on_units:
  - 185-S
  - 187-S
findings_open:
  - O1
  - O2
  - O3
  - O4
  - O5
  - O6
  - O7
  - O8
  - O9
  - O10
  - O11
  - O12
  - O13
  - O14
  - O15
  - O16
  - O17
  - O18
  - O19
  - O20
  - O21
  - O22
  - O23
  - O24
  - O25
findings_closed: []
findings_addressed_pending_review: []
findings_note: "ALL TWENTY-FIVE FINDINGS REMAIN OPEN. None is closed and none is recorded as addressed-pending-review. Revision 8 does not claim to have addressed them; it withdraws the premise that a speculative implementation plan could. Several - O5, O7, O14, O17, O19, O20 - are recorded below as REQUIREMENTS the future implementation plan must satisfy, which is a different thing from a remediation."
requires_plan_hardening: true
hardening_rationale: "When it becomes an implementation plan again, this unit will implement a mandatory policy gate that every future shipment traverses, spawn subprocesses, parse source with the AST module and mutate a policy-bearing label. That hardening obligation is recorded now and discharged later."
tags:
  - p-004
  - gate
  - policy
  - blocked
  - requirements-contract
---

# P-004 red-phase observation gate - BLOCKED requirements contract

## Status

**BLOCKED.** This document is a **requirements and decision contract**, not an
implementation plan. It has no live feature, no tasks and no shipment, and
**no independent review attempt is scheduled or authorized.**

## Why this document changed kind

Revisions 1-7 were implementation plans. Two independent attempts reviewed
them, and both failed on the same underlying cause:

| Attempt | Reviewed | Verdict | What it actually found |
|---|---|---|---|
| 01 | revision 6 | FAIL, `P0` 1 / `P1` 8 / `P2` 1 | Live carriers still instructed an executor to build a superseded design (`O1`) |
| 02 | revision 7 | FAIL, `P0` 2 / `P1` 19 / `P2` 4 | The derivation contract's sentinel has no producer (`O11`); the result schema cannot be populated by the specified runner (`O14`); the evidence digest is self-referential (`O16`); the transport envelope is asserted, not specified (`O17`) |

`O5`, `O7`, `O14`, `O17`, `O19` and `O20` are all the **same defect in
different clothes**: each names a surface - an exec primitive, an operation
registry, a result envelope, an activation file set - that **does not exist
yet**, and then specifies how to use it. That specification could only ever be
a guess, and a review of a guess is not convergence. It is attempt consumption.

**The correct response is to stop guessing and to stop reviewing.** Nothing is
gained by producing revision 9 for attempt 03 against the same absent
substrate.

## What must exist before this becomes a plan again

| Needed | Delivered by | State today |
|---|---|---|
| Operation registry and transport envelope | `184-S` / `178-F` | **archived and withheld** under `D10`, pending `TRANSPORT_DECIDED` |
| Fixed-argv exec primitive, bounded reader | `185-S` / `179-F` | queued, **unclaimable** while `184-S` is withheld |
| Harness-surface resolver, typed result, CLI | `187-S` / `181-F` | queued, `dag-root`, **plan not yet passed review** |
| Actor marker grammar the gate parses | settled by the above | **not settled** - see `O11` |

Until `185-S` and `187-S` have **actually shipped**, the exact module paths,
function signatures, result schemas, registration mechanics, CLI and MCP paths
and manifest entries are unknowable. Writing them is what produced the
findings above.

## The requirements - validated direction, preserved

What follows is **what must be true**, not how to build it. Each item survived
independent review as a *direction*; none may be read as an implementation
specification, and each must be re-derived against the delivered surfaces
before it is turned into a task.

### R1 - the whole-suite policy is unsatisfiable and must be amended, not worked around

The installed P-004 precondition demands a whole-suite `unittest discover` run
exiting non-zero **with every generated harness test failing**, on a repository
whose established suite passes. Attempt 02 found (`O21`) that the non-zero-exit
requirement, the retained whole-suite discovery and the
established-tests-may-pass allowance cannot all hold as stated.

**Requirement:** the gate is **task-scoped and structured**, not whole-suite
and exit-code-derived. Amending the policy text is part of the future unit's
scope, performed **after** the foundations ship - never a local reinterpretation
by the gate.

### R2 - the actor does not apply the label; Ship does

Attempt 02 found (`O11`) that direct actor mutation of a policy-bearing label
bypasses the very gate that is supposed to authorize it.

**Requirement:** `harness-architect` **no longer applies `harness-ready`**.
Ship applies it, **exclusively**, and **only** after a `RED_CONFIRMED` gate
result. The actor produces artifacts; it does not adjudicate.

### R3 - the expected set is declared by the producer, not inferred from test bodies

Attempt 02 found (`O11`) that the plan's per-test sentinel
`raise NotImplementedError("P004:<qualified-test-id>")` **has no producer**:
the manifest variable `UNIMPLEMENTED_MARKER` is the constant literal
`raise NotImplementedError("...")`. It also found (`O12`) that an
unconditionally raising test is **vacuous** - it fails regardless of the subject
- and (`O13`) that the expected set was neither shipment-scoped nor owned.

**Requirement:**

* The actor emits a **module-level literal declaration**, conventionally
  `P004_HARNESS`, carrying the task ID, the mapping from qualified test ID to
  the expected production-stub marker, and the source files under test.
* The declaration is a **literal data structure that does not execute** -
  readable by `ast.literal_eval` after a safe parse, with no call, no
  comprehension, no name reference and no import.
* **Test bodies never contain an unconditional marker raise.** The marker is
  raised by the **production stub** the test exercises.
* The gate validates the **actual exception raised by exercising each declared
  test**, not the text of the test's source.

This makes the expected set producer-owned, shipment-scoped and falsifiable -
the three properties `O11`, `O12` and `O13` found missing.

### R4 - one structured run, gate-owned, never a parse of human output

Attempt 02 found (`O14`) that default `unittest` output cannot supply
per-test outcomes, markers and correlation.

**Requirement:** the gate owns a **single structured child run** with a
machine-readable result protocol of its own design. It does **not** parse
default human-readable output, and it does **not** run the suite twice.
Policy text, actor and gate are updated in **one atomic unit** - a gate that
expects a declaration the installed actor does not emit is exactly `O11`.

### R5 - identifiers in, trusted context injected

Attempt 02 found (`O20`) that exposing `workspace_root` and
`autoharness_home` as caller parameters **inverts the trust boundary**: the
caller supplies the roots the containment checks are performed against.

**Requirement:** the public operation accepts **identifiers only**. Trusted
context is injected by the invoking surface, never supplied by the caller.

### R6 - registration is an ACTIVATE act

Attempt 02 found (`O18`) that registering an operation makes it discoverable
and invocable, so "register it inert during PREPARE" contradicts `D2`.

**Requirement:** registration happens at **ACTIVATE** and nowhere earlier. The
exact `OperationResult` adapter, transport schema, CLI and MCP parity paths,
activation file set and manifest entries are **derived from the delivered
`184-S`/`185-S` substrate**, and enumerated exhaustively then - satisfying
`O17` and `O19` with facts rather than assertions.

### R7 - digests project, never self-reference

Attempt 02 found (`O16`) that `evidence_sha256` was defined over the document
that contains it.

**Requirement:** every digest is computed over an **explicit projection** of
the result that **excludes the digest field itself**, with domain separation
and explicit absence sentinels.

### R8 - bounds, containment, typed outcomes, approval-gated rollback

Attempt 02 found (`O15`) that AST containment, grammar and resource bounds were
undefined.

**Requirement:** the AST walk is confined to files under the canonical
workspace root, with an explicit accepted grammar, explicit per-file and
aggregate bounds, and an explicit mapping for syntax errors. Outcomes are typed
and exhaustive; the resolver's non-ready states are preserved distinctly, and
**neither executes any command**. Rollback requires **fresh, live, SHA-bound
operator approval** with a safety mode and an explicit halt when the operator is
dark or AFK. There is no unconditional revert path.

## What this document does not do

* It does **not** name a gate module path, function signature, dataclass shape,
  result schema, operation ID, CLI path or MCP tool name. Those were `O5`,
  `O7`, `O14`, `O17`, `O19` and `O20`, and they are unknowable today.
* It does **not** claim any finding is addressed. All twenty-five remain open.
* It does **not** request a review.
* It does **not** create, restore or revive a carrier.

## Carriers

`176-S`, `168-F` and `168.001-T` ... `168.012-T` are **permanently retired**:
archived, never claimed, never executed, and **never restored under any
restoration clause**. When the unblock condition is met, Stage harvests a
**fresh** feature, task set and shipment under **new IDs** against the
then-current repository state.

`168-S` - an unrelated shipment carrying the `160-F` family - declares
`dependencies: ['166-S', '176-S']`. Because `176-S` is archived, `168-S` is
**unclaimable**. That is a deliberate **fail-closed hold**, preserved as a
truthful record of what `168-S` was sequenced behind. It clears only by an
operator-directed re-sequencing onto the fresh replacement shipment once one
exists. **`176-S` can never ship.**

## Provenance

* Supersedes `docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md`
* Source stash `76EBDE6D`
* Governing decision: the 2026-09-18 shared-execution-architecture and
  portfolio-reslicing decision, revision **8**, `SM-1` and `D10`
* Verdict manifest: `docs/reviews/2026-09-18-p004-observation-gate-plan-review.md`
* Finding namespace: `O`-prefix, reserved for `p004-observation-gate`
