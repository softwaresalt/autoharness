---
title: Plan review verdict manifest — P-004 three-channel observation gate
description: 'Mutable verdict manifest for docs/plans/2026-09-18-p004-observation-gate-plan.md. MANIFEST REVISION 2. The plan is at REVISION 7, a current-state rewrite performed by Stage under continuing operator authorization to address attempt-01 findings O1-O10. REVISION 7 HAS NOT BEEN REVIEWED. The most recent independent attempt is 01, which judged plan REVISION 6 at committed base b11d6555 and returned FAIL/BLOCK at P0 1 / P1 8 / P2 1. awaiting_attempt is 2. ALL TEN FINDINGS REMAIN OPEN and are recorded as findings_addressed_pending_review: Stage remediates, Stage never closes. THE PLAN IS WITHHELD FROM HARVEST and now has NO live feature, tasks or shipment - 176-S, 168-F and every live 168 task are ARCHIVED AS RETIRED, NEVER CLAIMED AND NEVER EXECUTED, which is the structural remediation of O1. NOT PUBLICATION-ELIGIBLE; publication and execution are distinct gates and neither is open.'
doc_type: review-manifest
source: docs/reviews/2026-09-18-p004-observation-gate-plan-review.md
date: 2026-09-18
manifest_shape: attempt-roster
plan_id: p004-observation-gate
plan_path: docs/plans/2026-09-18-p004-observation-gate-plan.md
plan_revision: 7
plan_revision_reviewed: 6
awaiting_attempt_against_revision: 7
publication_eligible: false
publication_eligibility_note: 'NOT PUBLICATION-ELIGIBLE. No independent attempt has judged plan revision 7; the attempt-01 FAIL against revision 6 is the standing verdict. THE EXECUTION GATE IS SEPARATE AND ALSO NOT OPEN: this plan is WITHHELD FROM HARVEST and has no live carriers. Its re-harvest requires 185-S and 187-S to have shipped and this plan to hold an independent PASS.'
feature_id: null
shipment_id: null
latest_attempt: 1
review_terminal: false
awaiting_attempt: 2
reviewed_content_head: b11d6555
gate_result: FAIL
verdict: FAIL
p0_open: 1
p1_open: 8
p2_open: 1
remediation_authorization: authorized-by-fresh-operator-directive-after-recording
latest_remediation_revision: 7
latest_disposition: FAIL-BLOCKING-P0-AND-P1
latest_artifact: docs/reviews/review-history/2026-09-18-p004-observation-gate-plan-review-attempt-01.md
verdict_is_pass: false
verdict_note: 'FAIL/BLOCK as independently determined by attempt 01 against plan REVISION 6 at committed base b11d6555, under the standing decision rule (P0 or P1 FAIL, P2-only ADVISORY, P3-or-none PASS). THE CENTRAL DEFECT (O1, P0): the plan reduced its scope in prose at revision 1, but feature 168-F, the twelve 168.* tasks and the 176-S shipment manifest are LIVE, QUEUED AND UNCHANGED and still specify the superseded architecture - at claim time Ship reads the manifest, not the plan''s Reduction section. The remaining blockers: 191-S is circular, has NO governing plan of its own, and has been OVERTAKEN BY EVENTS because the substantive actor correction already landed via external Ship commits 1cb0dc81 and b8ac632a (O2); the expected-green characterization conflicts with live all-generated-tests-red policy (O3); no authoritative producer exists for test IDs, markers or outcome declarations, so the exact-set-equality assertion has no defined identity scheme (O4); the canonical command PYTHONPATH=src python -m unittest discover -s tests is NOT an argv vector and has no specified shell-free environment/argv split against the 185-S fixed-argv exec primitive (O5); the per-test expected marker P-004 requires is recorded but not enforced (O6); there is no typed red_phase API, result, evidence or digest and no registered CLI/MCP operation, so Ship prose would be UNWIRED (O7); resolver UNRESOLVED/invalid/race states are not exhaustively preserved and freshness/no-bypass tests are incomplete (O8); and rollback lacks fresh live operator approval with no safety mode for dark/AFK operation (O9). O10 is a non-blocking stale-pointer item. NO finding was closed, lowered, deferred or waived; there were no predecessor findings to carry.'
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
blocking_findings:
- O1
- O2
- O3
- O4
- O5
- O6
- O7
- O8
- O9
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
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 7
manifest_revision: 2
plan_revision_7_scope: full-rewrite-current-state-addressing-attempt-01-findings
latest_attempt_reviewed_revision: 6
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
findings_addressed_pending_review:
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
open_counts_note: Counts are AS DETERMINED BY ATTEMPT 01 against plan revision 6 and are NOT re-derived by Stage. Revision 7 REMEDIATES every open finding and CLOSES NONE.
retired_prerequisite_shipment: 191-S
review_state_authority: THIS MANIFEST IS THE SOLE AUTHORITY for this plan's review state. The plan's own verdict fields are pointers, not a second record.
---

# Verdict manifest — P-004 red-phase observation gate

This file is a **selection surface**, not a review. It names which immutable
attempt artifact is authoritative right now, and it is the **sole authority**
for this plan's review state.

## Current state

| | |
|---|---|
| Plan revision | **7** — current-state rewrite addressing attempt-01 findings |
| Last independent attempt | **01**, which judged revision **6** at committed base `b11d6555` |
| Verdict of record | **FAIL / BLOCK** — `P0` 1 / `P1` 8 / `P2` 1 / `P3` 0 |
| Awaiting | independent attempt **02** against revision **7** |
| Publication eligible | **false** |
| Harvest state | **withheld** — no live feature, tasks or shipment |

**No verdict is asserted against revision 7.** The authoritative artifact
remains
`docs/reviews/review-history/2026-09-18-p004-observation-gate-plan-review-attempt-01.md`,
which is **immutable and untouched**.

## Findings

**Open: 10.** `O1`–`O10`, all recorded as
`findings_addressed_pending_review`. Revision 7 **remediates** every one and
**closes none**. Stage remediates; Stage never closes.

### What revision 7 changed in response

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

`reviewed_revision` + `verdict` are what an **independent reviewer** judged;
`remediation_revision` + `disposition` are what **Stage** produced in response.
`REMEDIATED-PENDING-REVIEW` is never a `verdict` value; it is only ever a
`disposition`. The attempt-01 artifact is **immutable and untouched**.

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
