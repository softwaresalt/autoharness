---
title: Plan review verdict manifest — P-004 three-channel observation gate
description: Mutable verdict manifest for docs/plans/2026-09-18-p004-observation-gate-plan.md. MANIFEST REVISION 3. The plan is at REVISION 7 and HAS NOW BEEN INDEPENDENTLY REVIEWED. The most recent independent attempt is 02, which judged plan REVISION 7 at committed base 844cee9c and returned FAIL/BLOCK at P0 2 / P1 19 / P2 4 / P3 0 - 25 findings open, 21 blocking. awaiting_attempt is 3. Revision 7 correctly retires the superseded 176-S / 168-F carriers, removes expected-green characterization entirely and derives the expected set rather than accepting it from the caller, but the derivation contract depends on a unique per-test AST sentinel THE INSTALLED ACTOR DOES NOT PRODUCE, so the gate would adjudicate NO_OBSERVATION unconditionally. NO FINDING IS CLOSED; O1-O10 are CARRIED OPEN. THE PLAN REMAINS WITHHELD FROM HARVEST with no live feature, tasks or shipment. NOT PUBLICATION-ELIGIBLE; publication, execution and harvest are distinct gates and none is open.
doc_type: review-manifest
source: docs/reviews/2026-09-18-p004-observation-gate-plan-review.md
date: 2026-09-18
manifest_shape: attempt-roster
plan_id: p004-observation-gate
plan_path: docs/plans/2026-09-18-p004-observation-gate-plan.md
plan_revision: 7
plan_revision_reviewed: 7
awaiting_attempt_against_revision: 7
publication_eligible: false
publication_eligibility_note: 'NOT PUBLICATION-ELIGIBLE. Independent attempt 02 judged plan revision 7 FAIL/BLOCK at P0 2 / P1 19 / P2 4; that is the standing verdict. THE EXECUTION GATE IS SEPARATE AND ALSO NOT OPEN: this plan is WITHHELD FROM HARVEST and has no live carriers. Its re-harvest requires 185-S and 187-S to have shipped and this plan to hold an independent PASS.'
feature_id: null
shipment_id: null
latest_attempt: 2
review_terminal: false
awaiting_attempt: 3
reviewed_content_head: 844cee9c
gate_result: FAIL
verdict: FAIL
p0_open: 2
p1_open: 19
p2_open: 4
remediation_authorization: authorized-by-operator-directive-after-recording
latest_remediation_revision: null
latest_disposition: FAIL-BLOCKING-P0-AND-P1
latest_artifact: docs/reviews/review-history/2026-09-18-p004-observation-gate-plan-review-attempt-02.md
verdict_is_pass: false
verdict_note: 'FAIL/BLOCK as independently determined by attempt 02 against plan REVISION 7 at committed base 844cee9c, under the standing decision rule (P0 or P1 FAIL, P2-only ADVISORY, P3-or-none PASS). WHAT REVISION 7 GOT RIGHT: 176-S, 168-F and every live 168 task are archived as retired and never executed, which is the structural remediation of O1; expected-green characterization is REMOVED, not renamed; the expected set is DERIVED rather than caller-supplied; commands are stated as shell-free argv with a closed environment allowlist; and rollback requires fresh, live, SHA-bound approval with a dark/AFK halt. THE CENTRAL NEW DEFECT (O11, P0): the derivation contract requires each generated harness test to carry a UNIQUE sentinel raise NotImplementedError("P004:<qualified-test-id>"), but the installed actor renders that marker from manifest variable UNIMPLEMENTED_MARKER whose live value is the CONSTANT LITERAL raise NotImplementedError("...") - no P004 prefix, no qualified test ID, identical in every generated test. Against a real harness the gate derives ZERO matching sentinels, trips its own at-least-one rule and returns NO_OBSERVATION unconditionally; the plan''s central mechanism has no producer. O11 also records that direct actor label mutation bypasses the future gate. THE REMAINING NEW BLOCKERS: an unconditional raise makes the RED test vacuous and non-falsifiable (O12); the expected set is neither shipment-scoped nor producer-owned (O13); default unittest output CANNOT populate the required structured per-test result schema and no TestResult subclass or alternative runner is named (O14); AST containment, sentinel grammar and resource bounds are undefined (O15); evidence_sha256 is SELF-REFERENTIAL and cannot be computed as written (O16); the OperationResult adapter and transport schema are missing so CLI/MCP derivation is asserted not specified (O17); PREPARE registration is NOT inert because registering an operation makes it discoverable and invocable, violating D2 (O18); the ACTIVATE unit enumerates no paths, files or manifest entries, so D11 parity cannot be checked (O19); the operation claims identifier-only inputs while taking workspace_root and autoharness_home, inverting the containment trust boundary (O20); the non-zero-exit requirement contradicts the retained whole-suite discovery and the established-tests-may-pass allowance (O21); and 181.005-T names templates/agents/ship.md.tmpl and .github/agents/ship.md, NEITHER OF WHICH EXISTS, so this plan''s own harvest prerequisite 187-S cannot be satisfied as its owner specifies it (O22, the same defect as lifecycle S35). NON-BLOCKING: the PR-3 environment override is not guaranteed to replace rather than merge (O23); archived 168.009-T omits the retirement markers its siblings carry (O24); and the archived 176/168 records carry copied, contradictory NOREVIVE-versus-REHARVEST rationale reproduced thirteen times (O25). O1-O10 are CARRIED OPEN WITHOUT RE-ARGUMENT at unchanged severity: addressed is not closed, and the remediation is not independently verifiable while the derivation contract has no producer, the result schema cannot be populated by the specified runner and the transport contract is unspecified. NO finding was closed, lowered, deferred or waived at this attempt.'
open_findings:
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
blocking_findings: &id001
- O1
- O2
- O3
- O4
- O5
- O6
- O7
- O8
- O9
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
finding_id_namespace: O-prefix, reserved for p004-observation-gate; distinct from the S-prefix namespace of ship-harness-lifecycle-foundation
p3_open: 0
actor_conformance_resolved_externally: true
actor_conformance_resolving_commits:
- 1cb0dc8140a809d63c3193d58431cd14408788b7
- b8ac632a93751fb29c51a8e5bf0f5e036b65cfb3
prerequisite_note: Attempt-01 finding O2 observed that the substantive harness-architect correction landed via external Ship review-remediation commits 1cb0dc81 and b8ac632a, with canonical suite 2358 passed / 0 failed / 54 skipped and manifest parity. 191-S is now ARCHIVED AS RETIRED, NEVER CLAIMED AND NEVER EXECUTED. NO RECORD MAY BE READ AS IMPLYING 191-S SHIPPED.
attempts:
- attempt: 1
  artifact: docs/reviews/review-history/2026-09-18-p004-observation-gate-plan-review-attempt-01.md
  reviewed_revision: 6
  reviewed_content_head: b11d6555
  reviewed_content_state: committed
  gate_result: FAIL
  verdict: FAIL
  verdict_is_pass: false
  p0: 1
  p1: 8
  p2: 1
  p3: 0
  blocking:
  - O1
  - O2
  - O3
  - O4
  - O5
  - O6
  - O7
  - O8
  - O9
  closed_predecessor_findings: []
  carried_predecessor_findings: []
  findings_raised:
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
  remediation_revision: null
  disposition: FAIL-BLOCKING-P0-AND-P1
  terminal_designation: not-terminal-remediation-authorized
  dispatch_mode: multi-agent
  personas_applied:
  - constitution
  - python
  - scope-boundary
  - learnings
  - architecture
  - agent-native-parity
  security_lens_triggered: false
  learnings_scope: full
  learnings_note: The Learnings persona cited P-007 G1-G9 as the settled approval pattern the lifecycle plan adopted at its revision 9 and this plan did not (O9), and cited the 188-S self-bootstrap retirement as precedent for O2's circularity.
  remediation_note: Attempt 01 performed NO remediation and did NOT modify the plan. It is the FIRST independent review this plan has ever received. It PROPOSES a further remediation cycle, which the dispatching operator directive explicitly authorizes.
- attempt: 2
  artifact: docs/reviews/review-history/2026-09-18-p004-observation-gate-plan-review-attempt-02.md
  reviewed_revision: 7
  reviewed_content_head: 844cee9c
  reviewed_content_state: committed
  gate_result: FAIL
  verdict: FAIL
  verdict_is_pass: false
  p0: 2
  p1: 19
  p2: 4
  p3: 0
  blocking: *id001
  closed_predecessor_findings: []
  carried_predecessor_findings:
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
  findings_raised:
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
  remediation_revision: null
  disposition: FAIL-BLOCKING-P0-AND-P1
  terminal_designation: not-terminal-remediation-authorized
  dispatch_mode: multi-agent
  personas_applied:
  - constitution
  - python
  - scope-boundary
  - learnings
  - architecture
  - agent-native-parity
  security_lens_triggered: false
  learnings_scope: full
  learnings_note: The Learnings persona cited P-007 G1-G9 as the settled approval pattern revision 7 correctly adopted at O9, and cited attempt-01 O1 as the precedent for treating a queued shipment manifest as an executable instruction set rather than a document subordinate to plan prose.
  remediation_note: Attempt 02 performed NO remediation and did NOT modify the plan. It is the FIRST independent review of revision 7. It PROPOSES a further remediation cycle, which the dispatching operator directive explicitly authorizes after recording.
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 7
manifest_revision: 3
plan_revision_7_scope: full-rewrite-current-state-addressing-attempt-01-findings
latest_attempt_reviewed_revision: 7
carriers_status: RETIRED-NEVER-EXECUTED
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
- 168.010-T
- 168.011-T
- 168.012-T
retired_carriers_note: 'Archived as RETIRED, SUPERSEDED, NEVER CLAIMED AND NEVER EXECUTED at the revision-7 remediation. This is the structural remediation of O1: the superseded instruction set no longer exists in the live queue. The original defect linkage is preserved on each archived record and the records are NEVER RESTORED; re-harvest is forward-only.'
harvest_gate: Stage re-harvests a FRESH feature, task set and shipment only after BOTH 185-S and 187-S have shipped AND this plan holds an independent PASS. No empty queued shipment is created in the interim.
findings_addressed_pending_review: []
open_counts_note: Counts are AS DETERMINED BY ATTEMPT 02 against plan revision 7 and are NOT re-derived by Stage. They comprise the ten findings O1-O10 CARRIED OPEN from attempt 01 plus the fifteen findings O11-O25 RAISED AT ATTEMPT 02. No finding has ever been closed on this plan.
retired_prerequisite_shipment: 191-S
review_state_authority: THIS MANIFEST IS THE SOLE AUTHORITY for this plan's review state. The plan's own verdict fields are pointers, not a second record.
open_findings_count: 25
blocking_findings_count: 21
findings_addressed_pending_review_note: 'EMPTY BY DESIGN. Attempt 02 was a RECORDING-ONLY turn: no remediation was performed and no plan, carrier, source, template, skill or manifest file was modified. Nothing is pending review that was not already judged by attempt 02.'
plan_pointer_fields_stale: true
plan_pointer_fields_stale_note: The plan's own latest_attempt / awaiting_attempt fields still read 1 and 2 because plan edits were FORBIDDEN by the directive that dispatched attempt 02. THIS MANIFEST IS AUTHORITATIVE; the plan's fields are pointers only, per review_state_authority. Reconcile them at the next remediation cycle.
---

# Verdict manifest — P-004 red-phase observation gate

This file is a **selection surface**, not a review. It names which immutable
attempt artifact is authoritative right now, and it is the **sole authority**
for this plan's review state.

## Current state

| | |
|---|---|
| Plan revision | **7** — current-state rewrite addressing attempt-01 findings |
| Last independent attempt | **02**, which judged revision **7** at committed base `844cee9c` |
| Verdict of record | **FAIL / BLOCK** — `P0` 2 / `P1` 19 / `P2` 4 / `P3` 0 |
| Awaiting | independent attempt **03** against revision **7** |
| Publication eligible | **false** |
| Harvest state | **withheld** — no live feature, tasks or shipment |

The authoritative artifact is
`docs/reviews/review-history/2026-09-18-p004-observation-gate-plan-review-attempt-02.md`.
The attempt-01 artifact is **immutable and untouched**.

## Findings

**Open: 25.** `O1`–`O25`. Ten (`O1`–`O10`) are **carried open without
re-argument** from attempt 01 at unchanged severity; fifteen (`O11`–`O25`) were
**raised at attempt 02**. **No finding has ever been closed on this plan.**
Stage remediates; Stage never closes.

`findings_addressed_pending_review` is **empty by design**: attempt 02 was a
recording-only turn and performed no remediation.

### What attempt 02 blocked on

* **`O11`** (P0) — the derivation contract requires a **unique** per-test
  sentinel `raise NotImplementedError("P004:<qualified-test-id>")`, but the
  installed actor renders that marker from manifest variable
  `UNIMPLEMENTED_MARKER`, whose live value is the **constant literal**
  `raise NotImplementedError("...")` — no `P004:` prefix, no qualified test ID,
  identical in every generated test. The gate would derive **zero** matching
  sentinels and return `NO_OBSERVATION` unconditionally. The plan's central
  mechanism **has no producer**. Direct actor label mutation additionally
  bypasses the future gate.
* **`O12`** — an unconditional `raise` makes the RED test **vacuous**: it fails
  regardless of the subject, so the RED phase is non-falsifiable as specified.
* **`O13`** — the expected set is neither **shipment-scoped** nor
  producer-owned; tests generated for another shipment enter it.
* **`O14`** — default `unittest` output **cannot** populate the required
  structured per-test result schema, and no `TestResult` subclass or
  alternative runner is named.
* **`O15`** — AST **containment**, sentinel grammar and resource bounds are
  undefined; there is no workspace-root containment rule for the walk.
* **`O16`** — `evidence_sha256` is **self-referential** and cannot be computed
  as written.
* **`O17`** — the `OperationResult` adapter and transport schema are missing,
  so CLI/MCP derivation is **asserted, not specified**.
* **`O18`** — PREPARE registration is **not inert**: registering an operation
  makes it discoverable and invocable, violating `D2`.
* **`O19`** — the ACTIVATE unit enumerates **no** paths, files or manifest
  entries, so `D11` parity cannot be checked.
* **`O20`** — the operation claims identifier-only inputs while taking
  `workspace_root` and `autoharness_home`, **inverting** the containment trust
  boundary.
* **`O21`** — the non-zero-exit requirement contradicts the retained
  whole-suite discovery and the established-tests-may-pass allowance.
* **`O22`** — `181.005-T` names `templates/agents/ship.md.tmpl` and
  `.github/agents/ship.md`, **neither of which exists**; this plan's own
  harvest prerequisite `187-S` cannot be satisfied as its owner specifies it.
  Same defect as lifecycle `S35`.

Non-blocking: **`O23`** (the `PR-3` env override is not guaranteed to replace
rather than merge), **`O24`** (archived `168.009-T` omits the retirement
markers its siblings carry) and **`O25`** (the archived `176`/`168` records
carry copied, contradictory `NOREVIVE`-versus-`REHARVEST` rationale, reproduced
thirteen times).

### What revision 7 changed in response to attempt 01

Recorded for provenance. **Addressed is not closed** — attempt 02 carried all
ten findings open because the remediation is not independently verifiable while
the derivation contract has no producer (`O11`), the result schema cannot be
populated by the specified runner (`O14`) and the transport contract is
unspecified (`O17`).

* **`O1`** — `176-S`, `168-F` and every live `168.00x-T` / `168.01x-T` task are
  **archived as retired, superseded, never claimed and never executed**. The
  superseded instruction set no longer exists in the live queue; prose deferral
  is replaced by structural removal. The plan has **no** live carriers and is
  **withheld from harvest**.
* **`O2`** — `191-S` is **retired, never claimed and never executed**. The
  actor correction it was to deliver landed via external Ship commits.
* **`O3`** — `expected_green_characterization` is **removed entirely**, not
  deferred and not renamed.
* **`O4`** — the expected test and marker set is **derived** by the gate from
  the generated harness through a safe AST walk of the sentinel
  `raise NotImplementedError("P004:<qualified-test-id>")`, with marker/ID
  correlation validated and at least one expected test required. Callers supply
  identifiers only.
* **`O5`** — commands are **shell-free argv specifications**; the leading
  `PYTHONPATH=src` is parsed against a closed environment allowlist into an
  env override, with explicit spawn / timeout / signal / decode mappings.
* **`O6`** — per-test expected-marker correlation is **enforced**, and an
  unexpected failure, error **or skip** of an expected harness test blocks.
* **`O7`** — a typed API in `src/autoharness/gates/red_phase.py` with exact
  enums, dataclasses, result schema and digests, registered as **one**
  operation `harness/p004-gate` from which the CLI and MCP forms are derived.
  The Ship skill records the result verbatim, so no surface is unwired.
* **`O8`** — the resolver precondition is carried as a **separate** field;
  `NO_HARNESS` (exit 1) and `UNRESOLVED` (exit 2) are preserved as distinct
  error detail while both collapse to the final token `NO_OBSERVATION`, and
  neither executes any command. No readiness state is persisted.
* **`O9`** — rollback requires **fresh, live, SHA-bound operator approval**
  revalidated immediately before the command, with an explicit halt when the
  operator is dark or AFK. There is no unconditional revert path.
* **`O10`** — carrier ownership and revision pointers are reconciled; the
  governing decision is at revision 7.

## Attempt roster

| Attempt | Artifact | Reviewed rev | Reviewer verdict | Remediation rev | Disposition |
|---|---|---|---|---|---|
| 01 | `…-p004-observation-gate-plan-review-attempt-01.md` | 6 | **FAIL** (P0 1 / P1 8 / P2 1 / P3 0) | 7 | `FAIL-BLOCKING-P0-AND-P1` |
| 02 | `…-p004-observation-gate-plan-review-attempt-02.md` | 7 | **FAIL** (P0 2 / P1 19 / P2 4 / P3 0) | — | `FAIL-BLOCKING-P0-AND-P1` |

`reviewed_revision` + `verdict` are what an **independent reviewer** judged;
`remediation_revision` + `disposition` are what **Stage** produced in response.
`REMEDIATED-PENDING-REVIEW` is never a `verdict` value; it is only ever a
`disposition`. Both attempt artifacts are **immutable**; attempt 01 was not
touched when attempt 02 was recorded.

## Pointer reconciliation outstanding

The plan's own `latest_attempt` / `awaiting_attempt` fields still read **1** and
**2**. Plan edits were **forbidden** by the directive that dispatched attempt
02, so they were not reconciled. **This manifest is authoritative** and the
plan's fields are pointers only, per `review_state_authority`. Reconcile at the
next remediation cycle.

## Publication, execution and harvest are three distinct gates

* **Publication** — requires an independent `PASS` against the current
  revision. **Shut.**
* **Execution** — requires live carriers and a claimable shipment. **Shut:**
  this plan has none, by design.
* **Harvest** — requires `185-S` **and** `187-S` shipped **and** an independent
  `PASS` on this plan. **Shut.** No empty queued shipment is created in the
  interim, and the archived carriers are **never restored**.

## Provenance

* Plan: `docs/plans/2026-09-18-p004-observation-gate-plan.md`, revision **7**
* Supersedes: `docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md`
* Source stash: `76EBDE6D`
* Governing decision: the 2026-09-18 shared-execution-architecture and portfolio-reslicing decision, revision **7**, `SM-1` and `D11`
* Finding namespace: `O`-prefix, reserved for `p004-observation-gate` and distinct from the `S`-prefix namespace of `ship-harness-lifecycle-foundation`

## Authority

Only an **independent** plan-review attempt may assert a verdict or close a
finding. Stage may remediate and may record disposition, and may never do
either of the former. `SM-2` `HARVEST_ADMITTED` is **SHUT**.
