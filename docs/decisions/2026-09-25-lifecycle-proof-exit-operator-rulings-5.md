---
title: "Lifecycle proof-exit operator rulings 5 (2026-09-25): section 9 governance defaults 1 to 5 ratified, epoch parameters frozen, and Go for Phase 2"
source: "docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-5.md"
doc_type: decision
description: "Fifth Stage addendum to the PE-1.7 proof-exit refresh (a04dea18). It records two operator rulings given at 2026-09-25T18:21:25-07:00, relayed verbatim by the Orchestrator: '1-5: ratified' and 'Go'. '1-5: ratified' ratifies charter section 9 governance defaults items 1 to 5 as the Orchestrator presented them: (1) freeze before the epoch, (2) stable finding lineage, (3) check cadence, (4) separate gates and (5) budgets. Item 6 (the P2 rule) was already decided under C4 (347771bd) and item 7 (the lead reviewer) under C4 (2634bac2). 'Go' starts Phase 2: the C2 re-slice into release units A, B, C and D, the C3 retirement of 187-S, the rebaselined plan, the review epoch and harvest (PE-TASK-03). This record freezes the exact epoch parameters Stage will use: the rubric version (plan-review SKILL.md blob c77f3685 at 8fa08913), the seven-persona set, the severity mapping including the P2-critical rule (IM-14, PE-SAFETY-06, PE-SAFETY-07), the reviewer route (lead gpt-6-sol / openai / high through model_routing.anchor_review, dispatched explicitly), the cadence and the budgets. No row status changes (30 MET, 0 MET-COND, 7 Windows-met with Linux PENDING, 3 deferred, 40). This record itself performs no backlog mutation, plan, review or harvest; those follow as separate Phase 2 commits."
date: 2026-09-25
created: 2026-09-25
status: recorded
decision_status: decided
deciders: operator
recorded_by: Stage
operator_rulings_at: "2026-09-25T18:21:25-07:00"
operator_rulings_relayed_by: Orchestrator
docline:
  type: decision
  date: 2026-09-25
  conclusion: "section-9-items-1-to-5-ratified-epoch-parameters-frozen-go-for-phase-2"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "proof-exit"
    - "operator-rulings"
    - "review-governance"
    - "phase-2"
    - "ship-lifecycle"
    - "linux-execution-gate"
artifact_class: proof-exit-report-addendum
supersedes: none
relates:
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md, commit: a04dea18, relation: "refresh report; implementation matrix IM-01 to IM-17"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-2.md, commit: 2634bac2, relation: "C2 approved, C3 retire 187-S, C4 lead reviewer gpt-6-sol"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-3.md, commit: 347771bd, relation: "C4 P2 rule: only matrix-critical P2 blocks"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-4.md, commit: b8a7b100, relation: "OD-11 list ratified; IM-17 closed"}
  - {path: docs/decisions/2026-09-25-read-limit-early-return-r-c3b-decision.md, commit: 8fa08913, relation: "OD-10 decided early return; IM-16 tests are an implementation obligation"}
  - {path: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md, commit: e65887d8, relation: "section 9 governance defaults (ratified here, items 1 to 5); section 7.1 P2-critical"}
  - {path: docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md, relation: "issue taxonomy, finding identity, reviewer stability, three gates, remediation budget, stop conditions and epoch identity"}
records_rulings_on: [docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md]
prior_reports_edited: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.7"
charter_commit: e65887d8
charter_edited: false
matrix_id: PE-1.7
head_at_authoring: 8fa0891383ce5750b01960cb023d420fa1f8efef
branch: chore/stage-176-s-workflow-defects
worktrees: 1
rulings:
  section_9_items_1_to_5: {ruling: ratified, operator_text: "1-5: ratified"}
  phase_2: {ruling: go, operator_text: "Go", scope: "C2 re-slice into units A, B, C and D (C may fold into B within budget); C3 retirement of 187-S; rebaselined plan; review epoch; harvest (PE-TASK-03)"}
section_9_status:
  item_1_freeze_before_epoch: ratified
  item_2_stable_finding_lineage: ratified
  item_3_check_cadence: ratified
  item_4_separate_gates: ratified
  item_5_budgets: ratified
  item_6_p2_rule: "decided under C4 (347771bd): only P2 findings on P2-critical rows block"
  item_7_lead_reviewer: "decided under C4 (2634bac2): gpt-6-sol via model_routing.anchor_review"
frozen_epoch_parameters:
  epoch_family: LIFECYCLE-E2
  epoch_token_rule: "LIFECYCLE-E2-R1-<first 8 hex of the reviewed plan blob SHA-1>, fixed when the epoch opens; never an attempt number"
  subject: "the rebaselined lifecycle release-unit plan produced in Phase 2 (path and blob fixed at epoch open)"
  matrix_version: "implementation matrix IM-01 to IM-17 as ratified: a04dea18 rows, ratified 2634bac2, IM-17 closed b8a7b100, IM-16 decided 8fa08913; proof-entry matrix PE-1.7 (e65887d8)"
  rubric:
    version: R1
    skill_path: .github/skills/plan-review/SKILL.md
    skill_blob_sha1_at_head: c77f3685e81046195a55bcf4fc1e7d8973e40f97
    head: 8fa0891383ce5750b01960cb023d420fa1f8efef
    issue_taxonomy_source: "docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md, 'Issue taxonomy and what may block'"
  persona_set:
    - {persona: "Architecture Strategist", role: lead, route: anchor_review}
    - {persona: "Security Lens Reviewer", role: supporting, route: anchor_review}
    - {persona: "Agent-Native Parity Reviewer", role: supporting, route: anchor_review}
    - {persona: "Constitution Reviewer", role: supporting, route: caller}
    - {persona: "Python Reviewer", role: supporting, route: caller}
    - {persona: "Scope Boundary Auditor", role: supporting, route: caller}
    - {persona: "Learnings Researcher", role: supporting, route: caller}
  reviewer_route:
    lead: {model_family: gpt-6-sol, model_provider: openai, reasoning_effort: high, source: ".autoharness/config.yaml model_routing.anchor_review"}
    caller: {model_family: claude-opus-5.5, model_provider: anthropic, reasoning_effort: high, source: ".autoharness/config.yaml model_routing.stage"}
    dispatch_requirement: "the lead reviewer is invoked as a subagent with model gpt-6-sol named explicitly; if the runtime cannot honor it, Stage records ROUTING_DEGRADED and the epoch pauses (no same-model substitution for the lead)"
  severity_mapping:
    P0: blocks
    P1: blocks
    P2: "blocks only when its finding ID maps to a P2-critical row: IM-14, PE-SAFETY-06, PE-SAFETY-07; otherwise recorded, non-blocking"
    P3: "recorded observation, non-blocking"
    blocking_classes: [CRITERION, EVIDENCE]
    non_blocking_classes: [CONSISTENCY, RISK, CHANGE, PROCESS, DUPLICATE, CHILD]
  finding_identity: "<matrix row>-F<NN> (for example IM-04-F01); residue after a partial close gets a linked child <parent>.<n>; nothing carried forward, open or closed, without revalidation"
  cadence: [initial-full-review, delta-reviews-against-changes-only, final-full-consistency-pass]
  budgets:
    consolidated_revisions_per_epoch: 2
    local_remediation_cycles_after_a_review: 1
    tasks_per_shipment: 6
    engineering_hours_per_shipment: 8
    contract_growth_limit: "over 20% ends the epoch"
    overrun: "escalates per P-013.6; ends in split, spike, re-charter, risk acceptance, deferral or cancellation; another attempt is not a permitted outcome"
  gates:
    publication: "zero admitted P0 and P1, and zero P2 on P2-critical rows"
    implementation: "all required proofs pass and the implementation matrix is ratified; the Linux-native gate (IM-01) is a release gate for every containment-dependent unit and cannot be waived"
    claim_closure: "ordinary runtime, CI, P-002/P-004 and P-020 gates"
matrix_row_counts:
  total: 40
  met: 30
  met_conditional: 0
  open_evidence: 0
  unsatisfied: 0
  windows_met_linux_pending: 7
  deferred_to_implementation_matrix: 3
rows_changed: []
proof_verdicts_changed: false
open_operator_decisions: []
feature_id: 181-F
shipment_id: 187-S
shipment_status: "queued and frozen at authoring; C3 retirement is the next Phase 2 step and is recorded separately"
cross_platform_acceptance: unmet
linux_gate: "not-deferrable, non-waivable execution and release gate (section 6.9); Windows evidence never satisfies it"
phase_2_ready: true
phase_2_started_by: "operator 'Go' at 2026-09-25T18:21:25-07:00"
implementation_ready: false
publication_eligible: false
claim_ready: false
backlog_item_created: false
plan_changed: false
ship_surface_changed: false
config_changed: false
proof_run_performed: false
authorizes: "Phase 2 as scoped by the operator's 'Go': C2 re-slice, C3 retirement of 187-S without any Ship claim, rebaselined plan, one review epoch under the frozen parameters, and harvest only on a review PASS"
stage_model_route: "claude-opus-5.5/anthropic/high requested and configured; unverified by Stage (ROUTING_DEGRADED: not self-verifiable)"
---

# Lifecycle proof-exit operator rulings 5 (2026-09-25)

## Bottom Line

| Question | Answer |
|---|---|
| What did the operator decide? | **"1-5: ratified"** and **"Go"** |
| What does "1-5: ratified" cover? | Charter section 9 governance defaults items 1 to 5, as the Orchestrator presented them: freeze before the epoch, stable finding lineage, check cadence, separate gates and budgets |
| What about items 6 and 7? | Already decided under C4. Item 6 (the `P2` rule) in `347771bd`. Item 7 (the lead reviewer, `gpt-6-sol`) in `2634bac2` |
| What does "Go" start? | **Phase 2**: the C2 re-slice into release units A, B, C and D, the C3 retirement of `187-S`, the rebaselined plan, the review epoch and harvest under `PE-TASK-03` |
| What is frozen here? | The exact epoch parameters in [Frozen Epoch Parameters](#frozen-epoch-parameters) |
| Row counts | Unchanged: 30 `MET`, 0 `MET-COND`, 7 Windows-met with Linux `PENDING`, 3 deferred (40) |
| Open operator decisions | None on the proof-exit list |

## Scope and Method

* **Actor.** Stage, directed by the Orchestrator. Stage wrote this one file
  and ran only a Markdown lint on it.
* **Nothing earlier is edited.** The charter, the refresh report and the four
  earlier rulings records stay as committed.
* **Session state.** backlogit MCP `get_version` (update check skipped)
  returned `1.10.1-0.20260823032255-b07729386a31+dirty` (`TOOL_OK`).
  Phase 2 has started, so the proof-phase rule against index refresh no
  longer applies: `backlogit_sync_index` ran and indexed 1474 artifacts
  (`INDEX_SYNC_OK`). Checkpoint recovery: `list_checkpoints` with
  `consumer_id: stage` and no status or agent filter returned 67 records, all
  `stage`/`resolved`, none quarantined or anomalous, so this is a normal
  zero-candidate startup. The host tool wrapper spooled that read-only output
  (74.4 KB) to OS Temp, and Stage read the spool read-only. Engram, intercom
  and graphtor-docs expose no tools in this runtime (`ENGRAM_DEGRADED`,
  `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`). The Orchestrator relays to
  the operator.

## Operator Rulings (verbatim)

Given at **2026-09-25T18:21:25-07:00** and relayed by the Orchestrator.

> 1-5: ratified
>
> Go

### What "1-5: ratified" Ratifies

Charter section 9 (`e65887d8`) lists seven proposed defaults that "take
effect only on operator ratification". Items 1 to 5 are ratified here, as
presented:

| Item | Default | Now |
|---|---|---|
| 1 | **Frozen before the epoch**: rubric version, persona set, severity mapping, reviewer route and lead reviewer. A route change pauses the epoch | **Ratified** |
| 2 | **Stable finding lineage**: finding IDs tied to matrix rows; residue gets a linked child; nothing carried forward without revalidation | **Ratified** |
| 3 | **Check cadence**: one initial full review, then delta reviews, then one final full consistency pass | **Ratified** |
| 4 | **Separate gates**: publication, implementation (execution) and claim/closure are distinct | **Ratified** |
| 5 | **Budgets**: at most two consolidated revisions per epoch; at most six tasks and eight hours per shipment; an overrun escalates per P-013.6 and ends in a split, spike, re-charter, risk acceptance, deferral or cancellation | **Ratified** |
| 6 | **`P2` publication rule** | Already decided under C4 (`347771bd`): only `P2` findings on rows marked `P2-critical` block. `P0` and `P1` always block |
| 7 | **Reviewer lead and routing** | Already decided under C4 (`2634bac2`): `gpt-6-sol` through the existing `model_routing.anchor_review` route `{openai, gpt-6-sol, high}` |

Section 9 item 7's note that "the working configuration ... declares no
`model_routing.anchor_review` key" is out of date. The key exists at
`8fa08913`, as `2634bac2` recorded.

### What "Go" Starts

Phase 2 of the parent deliberation, in this order:

1. **C3**: retire `187-S` by a mechanism that is not a Ship claim or
   execution, and give `181-F` and its live items a disposition, so nothing is
   orphaned.
2. **C2**: re-slice into release units A, B, C and D. C may fold into B only
   if B stays within budget, as `2634bac2` recorded.
3. **Rebaselined plan**, then plan hardening.
4. **Review epoch** under the parameters frozen below.
5. **Harvest** (`PE-TASK-03`), only on a review `PASS`.

Each step is committed separately. None of them is a push, pull request,
claim or Ship invocation.

## Frozen Epoch Parameters

These are fixed now, before the plan exists and before the epoch opens. A
change to any of them pauses the epoch.

### Identity

| Parameter | Frozen value |
|---|---|
| Epoch family | `LIFECYCLE-E2` (the attempt 07 to 11 record belongs to a closed epoch) |
| Epoch token | `LIFECYCLE-E2-R1-<first 8 hex of the reviewed plan blob SHA-1>`, fixed when the epoch opens. Never an attempt number |
| Matrix version | The implementation matrix IM-01 to IM-17: rows as drafted in `a04dea18`, ratified in `2634bac2`, IM-17 closed in `b8a7b100`, IM-16 decided in `8fa08913`. Proof-entry matrix PE-1.7 (`e65887d8`) |

### Rubric (version R1)

| Parameter | Frozen value |
|---|---|
| Skill | `.github/skills/plan-review/SKILL.md`, Git blob `c77f3685e81046195a55bcf4fc1e7d8973e40f97` at `8fa08913` |
| Issue taxonomy | The parent deliberation's "Issue taxonomy and what may block": `CRITERION` and `EVIDENCE` can block; `CONSISTENCY`, `RISK`, `CHANGE`, `PROCESS`, `DUPLICATE` and `CHILD` do not |

### Persona Set

| Persona | Role | Route |
|---|---|---|
| Architecture Strategist | **Lead** | `anchor_review` |
| Security Lens Reviewer | Supporting (triggered: containment and trust roots) | `anchor_review` |
| Agent-Native Parity Reviewer | Supporting (triggered: agent-facing CLI and Ship surfaces) | `anchor_review` |
| Constitution Reviewer | Supporting | Caller |
| Python Reviewer | Supporting | Caller |
| Scope Boundary Auditor | Supporting | Caller |
| Learnings Researcher | Supporting | Caller |

### Reviewer Route

| Route | Model | Provider | Effort | Source |
|---|---|---|---|---|
| Lead (`anchor_review`) | `gpt-6-sol` | `openai` | `high` | `.autoharness/config.yaml` `model_routing.anchor_review` |
| Caller (Stage) | `claude-opus-5.5` | `anthropic` | `high` | `.autoharness/config.yaml` `model_routing.stage` |

**Dispatch rule.** The lead reviewer is invoked as a subagent with the model
`gpt-6-sol` named explicitly. If the runtime cannot honor that, Stage
records `ROUTING_DEGRADED` and the epoch pauses. The lead is never replaced by
a same-model pass, because "a rubric executed by a different route is a
different rubric" (parent deliberation, "Reviewer stability").

### Severity Mapping

| Severity | Effect on publication |
|---|---|
| `P0` | Blocks |
| `P1` | Blocks |
| `P2` | Blocks **only** when its finding ID maps to a `P2-critical` row: **IM-14**, **`PE-SAFETY-06`** or **`PE-SAFETY-07`**. Otherwise recorded and non-blocking |
| `P3` | Recorded observation. Non-blocking |

A reviewer cannot make a finding `P2-critical`. Criticality is predesignated
per row.

### Finding Lineage

* A finding ID is `<matrix row>-F<NN>`, for example `IM-04-F01`. A finding
  with no matrix row is `CHANGE` (change control) or `PROCESS`, and cannot
  block.
* Each finding closes on its own named evidence.
* Residue after a partial close gets a linked child, `<parent>.<n>`.
* Nothing is carried forward, open or closed, without revalidation.

### Cadence

1. One initial full review.
2. Delta reviews against changes only.
3. One final full consistency pass.

### Budgets

| Limit | Value |
|---|---|
| Consolidated revisions per epoch | At most **2** |
| Local remediation cycles after a review | At most **1** (parent deliberation) |
| Tasks per shipment | At most **6** |
| Engineering hours per shipment | At most **8** |
| Contract growth | Over **20%** ends the epoch |
| Overrun or repeated failure | Escalates per P-013.6. Ends in split, spike, re-charter, risk acceptance, deferral or cancellation. Another attempt is not a permitted outcome |

### Gates (kept distinct)

| Gate | Criterion |
|---|---|
| Publication | Zero admitted `P0` and `P1`, and zero `P2` on a `P2-critical` row |
| Implementation (execution) | All required proofs pass and the implementation matrix is ratified. IM-01, the Linux-native run, is a release gate for every containment-dependent unit and no one can waive it |
| Claim / closure | Ordinary runtime, CI, P-002/P-004 and P-020 gates. No review or proof `PASS` confers claim authority (IM-15) |

## Row-Status Consequences

**No row status changes.** Section 9 governs the next review epoch, not a
proof-entry row. The counts stay 30 `MET`, 0 `MET-COND`, 0 `OPEN-EVIDENCE`,
0 `UNSATISFIED`, 7 Windows-met with Linux `PENDING` and 3 deferred (40).
The 7 Linux-`PENDING` rows stay pending until IM-01 runs on Linux.

## What This Record Does Not Do

It records the two rulings and freezes the epoch parameters. It **does not
itself** retire `187-S`, change any backlog item, write the plan, open the
epoch, harvest, claim, push or open a pull request. Those are the next Phase
2 steps and each is committed separately. It does not change
`.autoharness/config.yaml` or any Ship surface.

## References

* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (PE-1.7, `e65887d8`), sections 7.1, 9 and 10
* Parent deliberation: `docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md` (issue taxonomy, finding identity, reviewer stability, three gates, remediation budget, stop conditions, epoch identity, Phase 2 table)
* Refresh report: `docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md` (`a04dea18`)
* Earlier rulings: `2026-09-25-lifecycle-proof-exit-operator-rulings.md` (`928bf3ff`), `-2.md` (`2634bac2`), `-3.md` (`347771bd`), `-4.md` (`b8a7b100`)
* OD-10 decision: `docs/decisions/2026-09-25-read-limit-early-return-r-c3b-decision.md` (`8fa08913`)
* Rubric: `.github/skills/plan-review/SKILL.md`
* Escalation: `.github/instructions/escalation-protocol.instructions.md` (P-013.6)
