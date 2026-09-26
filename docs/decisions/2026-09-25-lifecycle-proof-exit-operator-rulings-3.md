---
title: "Lifecycle proof-exit operator rulings 3 (2026-09-25): OD-4 gaps accepted, OD-10 routed to an architecture decision, OD-12 confirmed and C4 fully decided; PE-AUTH-01 met; 30 met, 0 conditional; OD-11 still open"
source: "docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-3.md"
doc_type: decision
description: "Third Stage addendum to the PE-1.7 proof-exit refresh (a04dea18), recording the operator rulings given at 2026-09-25T17:36:52-07:00 on the decisions left open by the second rulings record (2634bac2). OD-4: the 17 gaps are explicitly accepted, so the veto window closes and PE-AUTH-02 and PE-EVIDENCE-01 stay MET without depending on an interpretation. OD-10: R-C3b is routed to an architecture decision, which is not made here; IM-16 stays open with a defined route and stays not-deferrable before the resolver result contract is frozen. OD-11 is not decided: the Orchestrator is presenting the 47-code candidate list to the operator; IM-17 and IM-03's finality stay open. OD-12: yes, recorded as the first of the two answers offered in 2634bac2 (the rulings records 928bf3ff, 2634bac2 and this record are addenda to the Stage-authored proof-exit report, and 2634bac2's stash write 9144435A is the post-exit OD-7 capture allowed under OD-8). PE-AUTH-01 (P0) becomes MET. C4: in the next review epoch, P0 and P1 findings block, only matrix-critical P2 findings block publication, and other P2 and all P3 findings are captured as follow-ups or residual risk; with the reviewer lead already decided (gpt-6-sol), C4 is fully decided. Totals: 30 MET, 0 MET-COND, 0 OPEN-EVIDENCE, 0 UNSATISFIED, 7 Windows-met with Linux PENDING, 3 deferred (40). The 2634bac2 Phase 2 hold is lifted for Phase 2 work that does not depend on the resolver contract; freezing the resolver result contract or API still needs OD-10's architecture decision and OD-11. This record authorizes no plan, harvest, review epoch, activation, claim, retirement execution, push or pull request."
date: 2026-09-25
created: 2026-09-25
status: recorded
decision_status: partially-decided
deciders: operator
recorded_by: Stage
operator_rulings_at: "2026-09-25T17:36:52-07:00"
operator_rulings_relayed_by: Orchestrator
docline:
  type: decision
  date: 2026-09-25
  conclusion: "od-4-accepted-od-10-routed-od-12-confirmed-c4-decided-30-met-0-met-cond-od-11-open"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "proof-exit"
    - "operator-rulings"
    - "acceptance-matrix"
    - "implementation-matrix-ratification"
    - "ship-lifecycle"
    - "linux-execution-gate"
artifact_class: proof-exit-report-addendum
supersedes: none
relates:
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md, commit: a04dea18, relation: "records rulings on its open decisions"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings.md, commit: 928bf3ff, relation: "first addendum; OD-4 gap list and OD-12 origin"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-2.md, commit: 2634bac2, relation: "third addendum; continues its open-decision list"}
  - {path: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md, relation: "Decision 2 items 2 and 5; target of the OD-10 architecture decision; not edited"}
  - {path: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md, commit: e65887d8, relation: "charter PE-1.7; section 7.1 P2-critical and section 9 defaults"}
  - {path: docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md, relation: "defines C4 and matrix-critical P2"}
records_rulings_on: [docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md, docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings.md, docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-2.md]
records_rulings_on_commits: [a04dea18, 928bf3ff, 2634bac2]
prior_reports_edited: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.7"
charter_commit: e65887d8
charter_edited: false
matrix_id: PE-1.7
head_at_authoring: 2634bac2000f601b46efc8a06d2e4fa04f4c8829
branch: chore/stage-176-s-workflow-defects
worktrees: 1
rulings:
  OD-4: {ruling: "gaps accepted", gaps_accepted: 17, veto_window: closed, interpretation_dependency: none}
  OD-10: {ruling: "refer to architecture decision", target: "amend or extend docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md Decision 2 items 2 and 5, or a new architecture decision record", architecture_decision_made: false, answer_assumed: none}
  OD-11: {ruling: "not decided", note: "operator asked to see the actual reason codes and their purpose; the Orchestrator presents the 47-code candidate list directly"}
  OD-12: {ruling: "yes", answer_chosen: 1, answer_text: "the rulings records 928bf3ff, 2634bac2 and this record are part of the Stage-authored proof-exit report (addenda to a04dea18), and 2634bac2's one-line .backlogit/stash.jsonl change (9144435A) is the post-exit OD-7 capture under OD-8, outside PE-AUTH-01's proof-phase commit rule", answer_not_chosen: 2}
  C4-P2: {ruling: "only matrix-critical P2 findings block", reading_confirmed: 1}
  C4-reviewer-lead: {ruling: "decided in 2634bac2", model: gpt-6-sol, satisfied_by: ".autoharness/config.yaml model_routing.anchor_review"}
  C4: {status: fully-decided}
pending_confirmation: []
stash_entry_created: false
backlog_item_created: false
proof_verdicts_changed: false
matrix_row_counts:
  total: 40
  met: 30
  met_conditional: 0
  open_evidence: 0
  unsatisfied: 0
  windows_met_linux_pending: 7
  deferred_to_implementation_matrix: 3
  not_deferrable_or_mixed: 37
  not_deferrable_met_clean: 30
rows_changed: [PE-AUTH-01]
rows_condition_changed_status_unchanged: [PE-AUTH-02, PE-EVIDENCE-01]
met_conditional_rows: []
open_evidence_rows: []
unsatisfied_rows: []
implementation_matrix_status: ratified-by-operator-with-carve-outs
im_rows_ratified: [IM-01, IM-02, IM-04, IM-05, IM-06, IM-07, IM-08, IM-09, IM-10, IM-11, IM-12, IM-13, IM-14, IM-15]
im_rows_ratified_finality_open: [IM-03]
im_rows_not_ratified: [IM-16, IM-17]
im_16_route: "architecture decision (OD-10); not yet made"
open_operator_decisions: [OD-11, OD-10-architecture-decision]
resolved_operator_decisions: {OD-1: "superseded (4c6e2701)", OD-2: "resolved, Option A (e65887d8)", OD-3: "approved (928bf3ff)", OD-4: "gaps accepted, veto window closed (this record)", OD-5: "confirmed (928bf3ff)", OD-6: "withhold cleanup until the work ships (2634bac2)", OD-7: "yes; stash 9144435A (2634bac2)", OD-8: "confirmed (2634bac2)", OD-9: "accepted (928bf3ff)", OD-10: "routed to an architecture decision (this record); the decision itself is open", OD-12: "yes, answer 1 (this record)", C2: "approved (2634bac2)", C3: "retire 187-S, execution deferred to Phase 2 (2634bac2)", C4: "reviewer lead gpt-6-sol (2634bac2); only matrix-critical P2 blocks (this record)"}
cross_platform_acceptance: unmet
linux_gate: "not-deferrable, non-waivable execution and release gate (section 6.9); Windows evidence never satisfies it"
phase_2_ready: "gating decisions answered; starts only on Orchestrator routing"
phase_2_hold_2634bac2: lifted
phase_2_blocked_by: []
resolver_contract_freeze_blocked_by: [OD-10-architecture-decision, OD-10-tests-of-both-orders, OD-11]
implementation_ready: false
feature_id: 181-F
shipment_id: 187-S
shipment_status: "queued and frozen; retirement approved (C3) but not executed; not read or touched by this record"
shipment_claim_ready: false
publication_eligible: false
publication_ready: false
claim_ready: false
plan_changed: false
ship_surface_changed: false
config_changed: false
proof_run_performed: false
authorizes: none
stage_model_route: "claude-opus-5.5/anthropic/high requested and configured; unverified by Stage (ROUTING_DEGRADED: not self-verifiable)"
---

# Lifecycle proof-exit operator rulings 3 (2026-09-25)

## Bottom Line

| Question | Answer |
|---|---|
| What did the operator decide? | OD-4: the 17 gaps are **accepted**. OD-10: R-C3b is **routed to an architecture decision**. OD-12: **yes**. C4: **only matrix-critical `P2` findings block** publication, so C4 is fully decided |
| What is still open? | **OD-11** (the operator wants to see the reason codes first) and **the architecture decision that OD-10 routes to** (routed, not yet made) |
| What changes in the rows? | `PE-AUTH-01` (`P0`) becomes **`MET`**. `PE-AUTH-02` and `PE-EVIDENCE-01` stay `MET`, and no longer depend on an interpretation |
| Counts | **30 `MET`**, 0 `MET-COND`, 0 `OPEN-EVIDENCE`, 0 `UNSATISFIED`, 7 Windows-met with Linux `PENDING`, 3 deferred (40) |
| Can Phase 2 start? | The `2634bac2` hold is **lifted** for Phase 2 work that does not depend on the resolver contract. Phase 2 starts only when the Orchestrator routes it. Freezing the resolver result contract or API still needs OD-10's architecture decision and OD-11 |
| What does this authorize? | **Nothing.** It records the rulings and their effects. See [What This Record Does Not Do](#what-this-record-does-not-do) |

## Scope and Method

* **Actor.** Stage, directed by the Orchestrator. Stage wrote this one file.
  It made **no** backlog write: no stash entry, backlog item, shipment change
  or checkpoint. It ran no proof, fixture, build, test suite or linter other
  than a Markdown lint of this file, and no index refresh. It did not read or
  touch `187-S`, and made no push, branch, worktree or pull request. It did
  not touch any `git stash` entry.
* **Nothing earlier is edited.** The charter (`e65887d8`), the refresh report
  (`a04dea18`), the first and second rulings records (`928bf3ff`,
  `2634bac2`), the read-budget architecture decision and every findings
  artifact stay as committed.
* **Fail-closed rule** (as in `928bf3ff` and `2634bac2`). A row becomes
  `MET` only if its sole remaining condition is closed by a ruling recorded
  here. A row that picks up a new condition is not counted as met.
* **Session state.** backlogit MCP `get_version` (update check skipped)
  returned `1.10.1-0.20260823032255-b07729386a31+dirty` (`TOOL_OK`). Index
  sync was not run, on purpose (`INDEX_SYNC_SKIPPED`, as in `928bf3ff` and
  `2634bac2`). Checkpoint recovery: `list_checkpoints` with
  `consumer_id: stage` and no status or agent filter returned 67 records, all
  `stage`/`resolved`, with 0 needing quarantine and 0 quarantined. That is a
  normal zero-candidate startup. The host tool wrapper again spooled that
  read-only output (74.4 KB) to OS Temp outside the working directory. Stage
  did not direct that write and read the spool read-only. Engram, intercom and
  graphtor-docs expose no tools here (`ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`,
  `GRAPHTOR_UNAVAILABLE`). The Orchestrator relays to the operator.

## Operator Rulings (verbatim)

Given at **2026-09-25T17:36:52-07:00** and relayed by the Orchestrator.

> OD-4: "Gaps accepted"
>
> OD-10: "Refer to architecture decision"
>
> OD-11: "I need to see the actual reason codes and understand what exactly
> they pertain to, what their purpose is."
>
> OD-12: "Yes"
>
> C4: "only matrix-critical P2 findings block"

The decision definitions are in the refresh report's "Open Operator
Decisions" section (`a04dea18`), widened for OD-12 in `2634bac2`. C4 is
defined in the parent deliberation, section "Operator decisions".

### How Each Ruling Is Read

| Ruling | Reading recorded here | Basis |
|---|---|---|
| OD-4 "Gaps accepted" | **The operator explicitly accepts each of the 17 gaps** listed in `928bf3ff`: OD4-C4-1 to 6, OD4-D5-1 and 2, OD4-E5-1 to 3, OD4-F2-1 to 4, and OD4-G2-1 and 2. **The veto window is closed.** `PE-AUTH-02` and `PE-EVIDENCE-01` stay `MET`. They are met by operator acceptance of the gaps, not by new evidence, and no longer by an interpretation that could be vetoed | `928bf3ff` recorded "OD-4: approved" as the Orchestrator's interpretation, open to veto. `2634bac2` kept the window open while the Orchestrator explained the gaps. The operator's own words now state the acceptance directly |
| OD-10 "Refer to architecture decision" | **Routed, not decided.** R-C3b goes to an architecture decision: either an amendment or extension of `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md` Decision 2 items 2 and 5, or a new architecture decision record. **This record does not make that decision, and Stage assumes neither answer.** See [OD-10: The Route for R-C3b](#od-10-the-route-for-r-c3b) | OD-10 offered "rule on R-C3b, or route it to an architecture decision". The operator chose the second |
| OD-11 (codes requested) | **Not decided.** The operator asked to see the actual reason codes, what each one pertains to and what it is for. The Orchestrator is presenting the 47-code candidate list, with explanations, directly to the operator. IM-17 and IM-03's finality stay open | A request for information is not a ruling |
| OD-12 "Yes" | **Answer 1 of the two offered in `2634bac2`.** The rulings records `928bf3ff`, `2634bac2` and this record are part of the Stage-authored proof-exit report, as addenda to `a04dea18`, for `PE-AUTH-01`'s literal commit criterion. `2634bac2`'s one-line `.backlogit/stash.jsonl` change (stash entry `9144435A`) is the post-exit OD-7 capture that OD-8 allows, outside `PE-AUTH-01`'s proof-phase commit rule, and is not a proof-phase violation. See [OD-12: Which Answer](#od-12-which-answer) | The Orchestrator's relay names the three records and the stash write, which is answer 1's wording |
| C4 "only matrix-critical P2 findings block" | **Reading 1 of `2634bac2` is confirmed.** Reading 2 (all `P2` block) is rejected. With the reviewer lead decided in `2634bac2` (`gpt-6-sol`, via `model_routing.anchor_review`), **C4 is fully decided.** See [C4: The Publication Policy](#c4-the-publication-policy) | The operator's words match reading 1 exactly |

## OD-10: The Route for R-C3b

**The question** (from Proof C run 4 and IM-16). A read-limit error happens
first. A later recheck then completes and finds a disagreement. Should the
resolver report the read-limit code from the `FILE_COUNT_LIMIT` family (early
return), or `INPUT_CHANGED_DURING_RESOLUTION`? Both results are
`UNRESOLVED / 2`. Only the reason code differs.

**The route.** The answer is made in an architecture decision, which either
amends or extends Decision 2 of
`docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`
(item 2, precedence, and item 5, what the resolver does after a read-limit
error), or is a new architecture decision record. Which of these two forms
is used is part of that decision. It is not chosen here.

**What stays the same.**

* **IM-16 stays open, now with a defined route.** It stays carved out of the
  matrix ratification. The route matches the row as drafted in `a04dea18`
  ("Decide in architecture (Decision 2 items 2 and 5), record the decision,
  and test both orders"). Stage does not treat the routing as ratification
  of the row.
* **IM-16 stays `not-deferrable` before the resolver result contract is
  frozen,** with proposed severity `P1` (the operator may lower it).
* **The freeze has two prerequisites from OD-10:** the recorded architecture
  decision, and tests of both orders (read-limit error first then
  disagreement, and the reverse).
* **R-C3b stays `DISPUTED_NOT_ASSUMED`** until that decision is recorded.
  Stage assumes neither code.
* **No row status changes.** OD-10 conditions IM-16 and IM-03's finality,
  not a proof-entry row (`a04dea18`, OD-10 row).

## OD-12: Which Answer

`2634bac2` offered two answers, either of which closes `PE-AUTH-01`:

| Answer | Text in `2634bac2` | Chosen? |
|---|---|---|
| 1 | Confirm that the rulings records `928bf3ff` and `2634bac2` are part of the Stage-authored proof-exit report, and that `2634bac2`'s one-line `.backlogit/stash.jsonl` change is the post-exit OD-7 capture, outside `PE-AUTH-01`'s proof-phase commit rule | **Yes.** The relay also names this record |
| 2 | Rule under OD-8 that commits after the `a04dea18` report are post-exit and outside `PE-AUTH-01` entirely | **No** |

**Why answer 1.** The relay confirms two specific classifications: the
rulings records are addenda to the proof-exit report, and the one stash write
is the post-exit capture authorized under OD-8 and OD-7. That is answer 1. It
does not state answer 2's blanket rule that every commit after `a04dea18` is
outside `PE-AUTH-01`. So Stage does not assume that rule: a later
`docs/decisions/` commit that is neither a findings file nor an addendum
would still have to be classified on its own terms.

**This record's own commit.** It adds one file under `docs/decisions/`,
classified `artifact_class: proof-exit-report-addendum`, and changes nothing
else. The operator's confirmation names this record, so its commit adds no
new condition to `PE-AUTH-01`. That is unlike `928bf3ff` and `2634bac2`, each
of which raised OD-12 for its own commit.

## C4: The Publication Policy

**The rule for the next review epoch:**

| Finding | Effect at publication | Source |
|---|---|---|
| `P0` | **Blocks** | Parent decision publication gate ("zero admitted `P0` and `P1`"); P-014 for merge readiness. Unchanged |
| `P1` | **Blocks** | Same. Unchanged |
| Matrix-critical `P2` | **Blocks** | This ruling |
| Other `P2` | Does not block. Captured as a follow-up or recorded residual risk | This ruling |
| `P3` | Does not block. Captured as a follow-up or recorded residual risk | This ruling |

**What "matrix-critical" means.** Neither `a04dea18` nor `928bf3ff` defines
the term. They name C4 and the proposal ("only matrix-critical ones"). The
definition comes from the sources behind that proposal:

* The parent deliberation: "Criticality is predesignated per matrix row, not
  argued per finding," and finding IDs are tied to matrix rows.
* Charter section 7.1: `P2-critical` means "Predesignated critical".

So a `P2` finding is **matrix-critical** when its stable finding ID maps to a
matrix row that is predesignated `P2-critical`. A reviewer cannot make a
finding critical by argument. Criticality comes only from the row. In the
ratified implementation matrix, the only `P2-critical` row is **IM-14** (no
artifact claims race, TOCTOU or hardlink-alias resistance; from
`PE-SAFETY-06`). IM-09 is a plain `P2` row. In the proof-entry matrix, the
`P2-critical` rows are `PE-SAFETY-06` and `PE-SAFETY-07`.

**One mapping detail is left to the epoch freeze, not decided here.** The
sources do not say how a `P2`-rated finding against a `P1` row is treated.
Section 9 already requires the severity mapping to be frozen before the epoch
opens, and ratification of the section 9 defaults is already a gate for the
epoch. That detail belongs there. It is not a new operator decision, and
Stage assumes no answer.

**What else is unchanged.** The lead reviewer is `gpt-6-sol`, via the
existing `model_routing.anchor_review` route (decided in `2634bac2`; no
configuration change). The route must stay fixed through the epoch, because
a route change pauses it. Section 9's other defaults (frozen rubric, persona
set and severity mapping, finding lineage, cadence and budgets) still need
ratification before the epoch opens. The P2 publication rule, which is one
of those defaults, is now decided by this ruling.

## Implementation Matrix Ratification

The operator's ratification with carve-outs (`2634bac2`) stands. The
precondition that `2634bac2` recorded as not met, "OD-12, so that no
`MET-COND` row remains", **is now met.** No `MET-COND` row remains.

| Draft ID | Status after this record |
|---|---|
| IM-01, IM-02, IM-04 to IM-15 | **Ratified**, as in `2634bac2`. IM-01 and IM-02 stay **unmet**, because Linux has not been executed |
| IM-03 | **Ratified as a proof-backed requirement. Its finality as the frozen resolver contract stays open** on IM-16 and IM-17 |
| IM-16 | **Not ratified. Open, routed** to an architecture decision (OD-10) |
| IM-17 | **Not ratified. Open** on OD-11 |

## Row-Status Consequences

| Row | Sev | Status in `2634bac2` | Status now | Reason |
|---|---|---|---|---|
| `PE-AUTH-01` | `P0` | `MET-COND` (OD-12, widened) | **`MET`** | OD-12 is answered (answer 1). The rulings records `928bf3ff`, `2634bac2` and this record are proof-exit report addenda, so every proof-phase commit changes only `docs/decisions/*-spike.md` findings or the proof-exit report. The stash write in `2634bac2` is the post-exit OD-7 capture, made through MCP, and is not a proof-phase backlog mutation. This record's commit adds no new condition (see [OD-12: Which Answer](#od-12-which-answer)). OD-12 was the row's only remaining condition. Git still has one author identity and cannot attribute actors further |
| `PE-AUTH-02` | `P1` | `MET`, by operator acceptance of gaps (OD-4 reading, vetoable) | **`MET`**, by operator acceptance of gaps | The OD-4 dependency is removed: the operator accepted the gaps in their own words. The row is still met by acceptance, not by new evidence |
| `PE-EVIDENCE-01` | `P1` | `MET`, by operator acceptance of gaps (OD-4 reading, vetoable) | **`MET`**, by operator acceptance of gaps | Same as `PE-AUTH-02` |

Other rows, checked against this commit:

* `PE-AUTH-03` (`MET`, unchanged). Every decision recorded here is an
  operator ruling, quoted with its timestamp. This record authorizes nothing
  itself. The OD-10 architecture decision is not made, and C3 execution is
  still deferred. The row's criterion ("the proof-exit report lists C2, C3
  and C4 as pending") was met by the report at exit (`a04dea18`). OD-12 now
  confirms that the addenda are part of that report, and they record C2, C3
  and C4 as operator-decided, not self-authorized. Under OD-8, operator
  decisions made after the exit do not undo it. This is the same Stage
  reading disclosed in `2634bac2`, and the operator has not disagreed. If the
  operator disagrees, `PE-AUTH-03` becomes `MET-COND` on that point.
* `PE-SCOPE-01` to `07` and `PE-TASK-03` (`MET`, unchanged). No plan,
  review, `.backlogit/` file, shipment or lock file changes. No harvest
  happens.
* `PE-ACTIVATE-01` (`MET`, unchanged). Since `08787a4b`, only
  `docs/decisions/` files and `.backlogit/stash.jsonl` have changed, and this
  commit adds one more `docs/decisions/` file. The template, mirror, manifest
  and config blobs are the blobs at `08787a4b`.
* `PE-FLOW-02` (`MET`, unchanged). No Phase 2 artifact exists. This record is
  not one.

## Updated Counts

Checked against the `2634bac2` table: its 29 `MET` rows plus `PE-AUTH-01`
give 30. The `MET-COND` row moves to `MET`. Every other row is unchanged.
This matches the expected totals.

| Status | Rows | IDs |
|---|---|---|
| `MET` | 30 | AUTH-01, AUTH-02, AUTH-03, AUTH-04, SCOPE-01 to 07, FLOW-01 to 04, INTERFACE-02, INTERFACE-03, SAFETY-06, DATA-01 to 04, TASK-01, TASK-03, EVIDENCE-01, EVIDENCE-03, EVIDENCE-04, EVIDENCE-05, ACTIVATE-01, ACTIVATE-03 |
| `MET-COND` | 0 | none |
| `OPEN-EVIDENCE` | 0 | none |
| `UNSATISFIED` | 0 | none |
| `WIN-MET / LINUX-PENDING` | 7 | SAFETY-01, 02, 03, 04, 05, 07, EVIDENCE-02 |
| `DEFERRED` | 3 | INTERFACE-01, TASK-02, ACTIVATE-02 |
| **Total** | **40** | 36 not-deferrable, 1 mixed (SAFETY-02) and 3 deferred |

All 30 `MET` rows are not-deferrable, and none depends on an open operator
decision. The one disclosed Stage reading (`PE-AUTH-03`, below) is unchanged
from `2634bac2`. The 7 Linux-`PENDING` rows stay pending until IM-01 runs on
Linux, and no one can waive that gate.

## Phase 2 Gate

`2634bac2` held Phase 2 "until OD-12 is answered and C4-P2 is confirmed".
**Both are now answered, so that hold is lifted.**

| Work | Status |
|---|---|
| Phase 2 work that does not depend on the resolver contract (IM-03), for example the C2 re-slice into units A to D, `187-S` retirement under C3 and harvest under `PE-TASK-03` | **No gating decision remains open.** Starts only when the Orchestrator routes it. The C3 retirement mechanics must still be checked against the installed backlogit version first, and the retirement must not be performed as a Ship claim (see `2634bac2`, C3) |
| Freezing the resolver result contract or API (IM-03 finality; unit B's contract) | **Still blocked** on OD-10's architecture decision plus tests of both orders (IM-16), and on OD-11 (IM-17) |

This record only records that the gating decisions are answered. It does not
start Phase 2.

## Open Decisions

| ID | Decision | Status | Plain language | Affects |
|---|---|---|---|---|
| OD-11 | Ratify, revise or reject the section 6.5 candidate proposals | **Open.** The Orchestrator is presenting the 47-code candidate list, with explanations, directly to the operator | Agree whether the proven list of reason codes is the list to build, once you have seen what each code means | IM-17, IM-03 finality |
| OD-10 architecture decision | Decide R-C3b in architecture (amend or extend Decision 2 items 2 and 5, or a new record), then test both orders | **Routed, not yet made** | In one rare double-failure case, choose which of two reason codes to report | IM-16, IM-03 finality |

Resolved: OD-1 (superseded, `4c6e2701`), OD-2 (Option A, `e65887d8`), OD-3,
OD-5 and OD-9 (`928bf3ff`), OD-6, OD-7, OD-8, C2, C3 and the C4 reviewer lead
(`2634bac2`), and OD-4 (gaps accepted), OD-10 (routing), OD-12 (answer 1) and
the C4 `P2` policy (this record).

## Remaining Gates

| Gate | What still blocks it |
|---|---|
| **Phase 2** (not resolver-contract-dependent) | Nothing among the operator decisions. The Orchestrator's routing, then the C3 retirement-mechanics check |
| **IM-03 as the final resolver contract** | OD-10's architecture decision and tests of both orders (IM-16), and OD-11 (IM-17) |
| **New review epoch** (Phase 4) | Phase 2 and 3 output, and ratification of the section 9 governance defaults. The lead reviewer route (`anchor_review`, `gpt-6-sol`) and the `P2` rule are decided |
| **Activation** (`PE-ACTIVATE-02`, IM-08, unit D) | A planned and reviewed release unit, one task and one commit measured against `08787a4b`. Nothing is activated now |
| **Any claim of a successor to `187-S`** | Phase 2 re-slice first. Then the ordinary P-002 and P-004 claim gates, CI and closure gates. No proof `PASS` confers claim authority (IM-15). Any containment-dependent unit also needs IM-01, the Linux-native run, which no one can waive |
| **Cross-platform acceptance** (IM-02) | IM-01 |
| **Scratch cleanup** | Withheld under OD-6 until the last lifecycle release unit closes |
| **IM-10 reconciliation** | Stash `9144435A`. Needs triage and its own operator-approved release unit before the byte-exact resolver runs |
| **Publication** | Not ready (`publication_eligible: false`). There are 39 local commits ahead of upstream, 40 with this one, and none is pushed. Pushing is an operator action |

## What This Record Does Not Do

This record only records the rulings of 2026-09-25T17:36:52-07:00 and their
effect on the rows, the counts and the open-decision list. It **does not
make** the OD-10 architecture decision, choose between R-C3b's two codes or
choose that decision's form. It **does not decide** OD-11 or list the 47
codes. It **does not ratify** IM-16, IM-17, IM-03's finality, the section 6.5
candidate proposals or the section 9 defaults other than the `P2` rule. It
**authorizes no** plan, plan revision, harvest, backlog item, stash entry,
shipment change, `187-S` retirement step, review epoch, activation, claim,
configuration change, proof run, scratch cleanup, push or pull request.
`187-S` stays `queued` and frozen until Phase 2 is routed.

## References

* Refresh report: `docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md` (`a04dea18`, PE-1.7), sections "Implementation Matrix Draft, Refreshed" (IM-03, IM-14, IM-16, IM-17) and "Open Operator Decisions" (OD-10, OD-11, C4)
* First rulings record: `docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings.md` (`928bf3ff`), OD-4 gap list and OD-12 origin
* Second rulings record: `docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-2.md` (`2634bac2`), sections "C4-P2: Two Readings, Neither Assumed", "Row-Status Consequences" and "Open Decisions" (widened OD-12)
* Architecture decision: `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`, Decision 2 items 2 and 5 (not edited)
* Parent decision: `docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md`, "Three distinct gates" and "C4"
* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (PE-1.7, `e65887d8`; sections 3, 7.1, 7.2, 8 and 9)
* Configuration: `.autoharness/config.yaml` (`model_routing.anchor_review`)
* Policies: `.github/policies/workflow-policies.md` (P-010, P-014)
