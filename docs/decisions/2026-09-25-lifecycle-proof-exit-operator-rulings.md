---
title: "Lifecycle proof-exit operator rulings (2026-09-25): OD-3, OD-4, OD-5 and OD-9 closed; 29 rows met, one P0 row conditional on classifying this record; matrix still a draft and not ratified"
source: "docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings.md"
doc_type: decision
description: "Stage record of the operator rulings given at 2026-09-25T14:17:13-07:00 on the open decisions of the PE-1.7 proof-exit refresh (a04dea18). OD-9 accepted, OD-3 approved (ratifies all six Stage readings (a) to (d), (i) and (ii)), OD-4 approved (recorded as the Orchestrator's interpretation: explicit operator acceptance of each of the 17 listed evidence gaps, not a Ship transcription; the operator may veto this reading, and a veto reopens OD-4), OD-5 confirmed. OD-6, OD-7, OD-8, C2, C3 and C4 are not decided: the operator asked for explanations. Row consequences, fail-closed: 11 rows become MET (PE-FLOW-02, PE-SCOPE-07, PE-INTERFACE-02, PE-INTERFACE-03, PE-DATA-01, PE-DATA-02, PE-TASK-01, PE-EVIDENCE-03, PE-EVIDENCE-05, PE-AUTH-02, PE-EVIDENCE-01). PE-AUTH-01 (P0) loses its OD-5, OD-9 and OD-4 conditions, but stays MET-COND on one new condition, OD-12: this record's own commit is not a docs/decisions/*-spike.md file, so the row's literal criterion needs the operator to classify it as part of the proof-exit report. Totals: 29 MET, 1 MET-COND, 0 OPEN-EVIDENCE, 0 UNSATISFIED, 7 Windows-met with Linux PENDING, 3 deferred. Proof verdicts A, B and C run 4 lose their conditions; no verdict is relabelled. IM-03, IM-07 and IM-13 lose their conditional qualifiers. The implementation matrix IM-01 to IM-17 stays a DRAFT and is NOT RATIFIED. This record ratifies nothing else and authorizes no plan, harvest, review epoch, activation, claim, push or pull request."
date: 2026-09-25
status: recorded
decision_status: partially-decided
deciders: operator
recorded_by: Stage
operator_rulings_at: "2026-09-25T14:17:13-07:00"
operator_rulings_relayed_by: Orchestrator
docline:
  type: decision
  date: 2026-09-25
  conclusion: "od-3-od-4-od-5-od-9-closed-29-met-1-met-cond-matrix-draft-not-ratified"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "proof-exit"
    - "operator-rulings"
    - "acceptance-matrix"
    - "ship-lifecycle"
    - "linux-execution-gate"
artifact_class: proof-exit-report-addendum
records_rulings_on: docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md
records_rulings_on_commit: a04dea18
prior_reports_edited: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.7"
charter_commit: e65887d8
charter_edited: false
matrix_id: PE-1.7
head_at_authoring: a04dea18e05aeb8aa2f568d85664be6813d62309
branch: chore/stage-176-s-workflow-defects
worktrees: 1
rulings:
  OD-3: {ruling: approved, reading: "ratifies all six Stage readings (a), (b), (c), (d), (i), (ii)", interpretation_by: Orchestrator}
  OD-4: {ruling: approved, reading: "explicit operator acceptance of each listed gap (option 2), not Ship transcription (option 1)", interpretation_by: Orchestrator, operator_may_veto: true, veto_effect: "reopens OD-4"}
  OD-5: {ruling: confirmed}
  OD-9: {ruling: accepted}
not_decided: [OD-6, OD-7, OD-8, C2, C3, C4]
od4_gaps_accepted: 17
proof_verdicts_changed: false
proof_verdict_conditions_cleared: [A, B, C]
matrix_row_counts:
  total: 40
  met: 29
  met_conditional: 1
  open_evidence: 0
  unsatisfied: 0
  windows_met_linux_pending: 7
  deferred_to_implementation_matrix: 3
  not_deferrable_or_mixed: 37
  not_deferrable_met_clean: 29
rows_changed: [PE-FLOW-02, PE-SCOPE-07, PE-INTERFACE-02, PE-INTERFACE-03, PE-DATA-01, PE-DATA-02, PE-TASK-01, PE-EVIDENCE-03, PE-EVIDENCE-05, PE-AUTH-02, PE-EVIDENCE-01]
rows_condition_changed_status_unchanged: [PE-AUTH-01]
met_conditional_rows: [PE-AUTH-01]
open_evidence_rows: []
unsatisfied_rows: []
im_rows_qualifier_removed: [IM-03, IM-07, IM-13]
implementation_matrix_status: drafted-not-ratified
open_operator_decisions: [C2, C3, C4, OD-6, OD-7, OD-8, OD-10, OD-11, OD-12, matrix-ratification]
resolved_operator_decisions: {OD-1: "superseded (4c6e2701)", OD-2: "resolved, Option A (e65887d8)", OD-3: "approved 2026-09-25T14:17:13-07:00", OD-4: "approved 2026-09-25T14:17:13-07:00 (interpretation, vetoable)", OD-5: "confirmed 2026-09-25T14:17:13-07:00", OD-9: "accepted 2026-09-25T14:17:13-07:00"}
cross_platform_acceptance: unmet
linux_gate: "not-deferrable, non-waivable execution and release gate (section 6.9); Windows evidence never satisfies it"
implementation_ready: false
feature_id: 181-F
shipment_id: 187-S
shipment_status: "queued and frozen; not read or touched by this record"
shipment_claim_ready: false
publication_eligible: false
publication_ready: false
claim_ready: false
backlog_item_created: false
stash_entry_created: false
plan_changed: false
ship_surface_changed: false
proof_run_performed: false
authorizes: none
stage_model_route: "claude-opus-5.5/anthropic/high requested and configured; unverified by Stage (ROUTING_DEGRADED: not self-verifiable)"
---

# Lifecycle proof-exit operator rulings (2026-09-25)

## Bottom Line

| Question | Answer |
|---|---|
| What did the operator decide? | OD-9 accepted, OD-3 approved, OD-4 approved, OD-5 confirmed. OD-6, OD-7, OD-8, C2, C3 and C4 are **not** decided |
| What changes? | 11 rows become `MET`. `PE-AUTH-01` (`P0`) loses all its old conditions but stays `MET-COND` on one new condition (OD-12, about this record's own commit). No row is `OPEN-EVIDENCE` or `UNSATISFIED` |
| Counts | 29 `MET`, 1 `MET-COND`, 0 `OPEN-EVIDENCE`, 0 `UNSATISFIED`, 7 Windows-met with Linux `PENDING`, 3 deferred |
| Implementation matrix | IM-03, IM-07 and IM-13 lose their "conditional on OD-x" qualifier. The matrix stays a **DRAFT** and is **NOT RATIFIED** |
| What does this authorize? | **Nothing** beyond recording the four rulings. See [What This Record Does Not Do](#what-this-record-does-not-do) |

## Scope and Method

* **Actor.** Stage, directed by the Orchestrator. Stage worked read-only apart
  from writing this one file. It ran no proof, fixture, build, test suite or
  linter, and no index refresh. It made no backlog, shipment or stash change,
  and did not read `187-S`. It made no push, branch or pull request.
* **Nothing earlier is edited.** The charter (`e65887d8`), the refresh report
  (`a04dea18`), the prior report (`9c83517d`) and every findings artifact stay
  as committed. Historical verdicts stay as recorded. This record adds the
  consequences of the rulings on top of the refresh report.
* **Fail-closed rule.** A row becomes `MET` only if its sole remaining
  condition in the refresh report was one or more of the four rulings made
  here (OD-3, OD-4, OD-5, OD-9). A row that picks up any new condition is not
  counted as met. Linux-`PENDING` and deferred rows are unchanged.
* **Session state.** backlogit MCP `get_version` (update check skipped)
  returned `1.10.1-0.20260823032255-b07729386a31+dirty` (`TOOL_OK`). Index
  sync was not run, on purpose (`INDEX_SYNC_SKIPPED`, per `PE-AUTH-01`).
  Checkpoint recovery: `list_checkpoints` with `consumer_id: stage` and no
  status or agent filter returned 67 records, all `stage`/`resolved`, with 0
  needing quarantine and 0 quarantined. That is a normal zero-candidate
  startup. The host tool wrapper spooled that read-only output (74.4 KB) to OS
  Temp outside the working directory. Stage did not direct the write and read
  the spool read-only. This is disclosed on the same terms as the refresh
  report's spool. Engram, intercom and graphtor-docs expose no tools here
  (`ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`). The
  Orchestrator relays to the operator. Stash triage, harvest, shipment and
  archive steps do not apply, because the operator forbade backlog changes.

## Operator Rulings (verbatim)

Given at **2026-09-25T14:17:13-07:00** and relayed by the Orchestrator:

> "OD-9: accepted"
>
> "OD-3: approved"
>
> "OD-4: approved"
>
> "OD-5: confirmed"
>
> "OD-8: Explain this one in plain text so i can make an educated decision"
>
> "OD-6,7: Need better explanation of these to make a ruling."
>
> "C2,C3,C4: Need full explanation of these items to make educated rulings."

The decision definitions are in the refresh report's "Open Operator
Decisions" section (`a04dea18`).

### How Each Ruling Is Read

| Ruling | Reading recorded here | Basis |
|---|---|---|
| OD-9 "accepted" | The operator accepts the Orchestrator's `git stash` set-aside of the operator's uncommitted `.github/agents/_ship.agent.md` routing edit during Proof C run 4's Ship invocations (22:29:05 to 22:34:22, disclosed in `4c6e2701`). Proof C run 4 stays `PASS` | OD-9 was an accept-or-reject decision |
| OD-3 "approved" | Ratifies **all six** Stage readings: (a) Proof A's R2 reading; (b) the A and G file-bound counts; (c) the A, B and C spool classification; (d) the direct CLI refresh transport; (i) `PE-TASK-01`'s elapsed-time clause is read over reported runs, and an overrun run is recorded `FAIL` under `PE-SCOPE-07` without failing the row; (ii) `PE-EVIDENCE-05` is read over reported-run artifacts | OD-3 was presented as "approve or veto" the six readings. This reading was supplied by the Orchestrator |
| OD-4 "approved" | **An interpretation, by the Orchestrator.** It is read as option 2, explicit operator acceptance of each listed gap, and not as option 1, Ship's read-only transcription. The Ship subagent sessions that captured the prior runs' handoffs no longer exist, so a transcription could not be verified. The accepted gaps are listed one by one below. **The operator may veto this reading. A veto reopens OD-4**, and `PE-AUTH-02` and `PE-EVIDENCE-01` go back to `OPEN-EVIDENCE` | OD-4 offered two options, and "approved" does not name one |
| OD-5 "confirmed" | `89b0db6d` ("updated routing", `.autoharness/config.yaml` only) is an operator setup commit outside the proof actors | OD-5 asked for a one-line confirmation of attribution |

### OD-4: Evidence Gaps Accepted One by One

Accepting a gap means the operator accepts the record as it stands, without
the missing field. It does **not** create, transcribe or infer the missing
evidence. Each gap stays on the record as a gap, and no verdict changes.

| Gap ID | Proof run (commit) | Gap accepted | Row |
|---|---|---|---|
| OD4-C4-1 | C run 4 (`4c6e2701`) | The byte length and SHA-256 of the index-refresh stdout are not recorded | `PE-AUTH-02`, `PE-EVIDENCE-01` |
| OD4-C4-2 | C run 4 (`4c6e2701`) | The byte length and SHA-256 of the index-refresh stderr are not recorded | `PE-AUTH-02`, `PE-EVIDENCE-01` |
| OD4-C4-3 | C run 4 (`4c6e2701`) | Whether MCP was tried before the CLI fallback is not recorded | `PE-AUTH-02` |
| OD4-C4-4 | C run 4 (`4c6e2701`) | The active-filtered task, feature and chore projections are not itemized (only shipments are) | `PE-AUTH-02` |
| OD4-C4-5 | C run 4 (`4c6e2701`) | The P-010 self-check is not itemized | `PE-AUTH-02` |
| OD4-C4-6 | C run 4 (`4c6e2701`) | The `.backlogit` ignored status before and after is not recorded | `PE-EVIDENCE-01` |
| OD4-D5-1 | D run 5 (`5976ff62`) | The P-010 self-check is not itemized | `PE-AUTH-02` |
| OD4-D5-2 | D run 5 (`5976ff62`) | The interpreter version is not captured. It is recorded as "probable" and corroborated only by Stage | `PE-EVIDENCE-01` |
| OD4-E5-1 | E run 5 (`c7d5f97e`) | The index-refresh stdout hash is relayed as a prefix only | `PE-AUTH-02`, `PE-EVIDENCE-01` |
| OD4-E5-2 | E run 5 (`c7d5f97e`) | No index-refresh stderr is recorded | `PE-AUTH-02`, `PE-EVIDENCE-01` |
| OD4-E5-3 | E run 5 (`c7d5f97e`) | No Ship elapsed time is recorded | `PE-EVIDENCE-01` |
| OD4-F2-1 | F run 2 (`8b39a08b`) | Whether MCP was tried first is not stated | `PE-AUTH-02` |
| OD4-F2-2 | F run 2 (`8b39a08b`) | The P-010 self-check is not itemized | `PE-AUTH-02` |
| OD4-F2-3 | F run 2 (`8b39a08b`) | The P-002 result is not itemized | `PE-AUTH-02` |
| OD4-F2-4 | F run 2 (`8b39a08b`) | The safety statement has no `.backlogit` ignored status before and after | `PE-EVIDENCE-01`, `PE-AUTH-01` |
| OD4-G2-1 | G run 2 (`6daf80bb`, `06f8930b`) | The bounded index-refresh output is not recorded | `PE-AUTH-02`, `PE-EVIDENCE-01` |
| OD4-G2-2 | G run 2 (`6daf80bb`, `06f8930b`) | The separate "during" worktree listing is not recorded | `PE-AUTH-02` |

The C run 4 and D run 5 gaps come from the refresh report (`a04dea18`). The
E run 5, F run 2 and G run 2 gaps are "as before", from the prior report
(`9c83517d`, rows `PE-AUTH-02` and `PE-EVIDENCE-01`). Gaps in runs that are
no longer relied on (D run 4, C run 2) were already superseded and are not
part of this acceptance. The direct CLI transport in B, D, E, F and G is a
Stage reading, ratified under OD-3 (d). OD4-C4-3 and OD4-F2-1 are accepted
as gaps on top of that.

## Proof Verdicts After the Rulings

No verdict is relabelled. Only the pending conditions are cleared.

| Proof | Verdict (unchanged) | Condition in the refresh report | After the rulings |
|---|---|---|---|
| A | Run 5 `PASS` (`99e9ff5f`, `4d132bf9`) | OD-3 (R2, file bound, spool) | No remaining condition. Scope limits unchanged |
| B | Run 3 `PASS` (`6920cb7c`) | OD-3 (spool, CLI transport) | No remaining condition. CR-B1 to CR-B5 carry forward (IM-07) |
| C | Run 4 `PASS` (`4c6e2701`) | OD-9 | No remaining condition. It still ratifies **none** of the section 6.5 candidate proposals (IM-17, OD-11). R-C3b stays `DISPUTED_NOT_ASSUMED` (IM-16, OD-10) |
| D | Run 5 `PASS` (`5976ff62`) | None | Unchanged. Gaps OD4-D5-1 and 2 accepted |
| E | Run 5 `PASS` (`c7d5f97e`) | None | Unchanged. Gaps OD4-E5-1 to 3 accepted |
| F | Run 2 `PASS` (`8b39a08b`) | None | Unchanged. Gaps OD4-F2-1 to 4 accepted |
| G | `PENDING-LINUX` (`6daf80bb`, `06f8930b`) | OD-3 (file bound) | The file-bound condition is cleared. Linux stays `PENDING`, never `PASS`. The Linux gate is non-waivable (IM-01) |

No proof `PASS` confers claim, closure, P-004 red or `harness-ready`
authority (`PE-ACTIVATE-03`).

## Row-Status Consequences

Every row that the refresh report marked `MET-COND` or `OPEN-EVIDENCE` is
listed. The 18 rows that were already `MET` keep that status. The 7
Linux-`PENDING` rows and the 3 deferred rows are unchanged.

| Row | Sev | Refresh status and condition | New status | Reason |
|---|---|---|---|---|
| `PE-AUTH-01` | `P0` | `MET-COND` (OD-5, OD-9; Proof F `.backlogit` gap under OD-4) | **`MET-COND` (OD-12)** | OD-5 confirms `89b0db6d`, OD-9 accepts the set-aside, and OD4-F2-4 accepts the Proof F gap. So every old condition is cleared. **But this record adds a new condition.** The row's criterion says every proof-phase commit is a Stage commit that changes only `docs/decisions/*-spike.md` findings or the proof-exit report. This record's commit changes one file under `docs/decisions/`, and that file is not named `*-spike.md`. Stage classifies it as an addendum to the proof-exit report (`artifact_class: proof-exit-report-addendum`), because it records rulings on the report's decisions and restates its row statuses and counts. That classification is a Stage reading, so the row is not counted as met until the operator confirms it (OD-12). Stage recommends confirmation. Git still has one author identity and cannot attribute actors further |
| `PE-FLOW-02` | `P0` | `MET-COND` (OD-3 for A and B; OD-9 for C run 4) | **`MET`** | Both conditions are ruled. Seven verdicts are listed: A, B, C (run 4), D (run 5), E and F `PASS`, and G `PENDING-LINUX` with its Linux gate carried as IM-01, `not-deferrable`. No Phase 2 artifact exists. This record is not a Phase 2 artifact. `MET` does **not** open Phase 2: the matrix is not ratified (`PE-TASK-03`) |
| `PE-SCOPE-07` | `P1` | `MET-COND` (OD-3 (b)) | **`MET`** | The A and G file-bound counts are ratified |
| `PE-INTERFACE-02` | `P1` | `MET-COND` (OD-3 (c), (d)) | **`MET`** | The spool classification and the direct CLI refresh transport are ratified. CR-B1 to CR-B5 carry into IM-07 and are not row conditions |
| `PE-INTERFACE-03` | `P1` | `MET-COND` (OD-9) | **`MET`** | OD-9 accepted. C run 4 criterion 1 stands |
| `PE-DATA-01` | `P1` | `MET-COND` (OD-9) | **`MET`** | OD-9 accepted. Non-ratification of the candidate (IM-17) and R-C3b (IM-16) condition the final contract, not this row, as the refresh report records |
| `PE-DATA-02` | `P1` | `MET-COND` (OD-9) | **`MET`** | OD-9 accepted. Parity is proven for the candidate schema as proposed. Its ratification is IM-17 |
| `PE-TASK-01` | `P1` | `MET-COND` (OD-3 (i)) | **`MET`** | The reported-runs reading is ratified. C run 3's overrun stays recorded `FAIL` |
| `PE-EVIDENCE-03` | `P1` | `MET-COND` (OD-3 (a), (b), (c)) | **`MET`** | The R2, file-bound and spool readings are ratified |
| `PE-EVIDENCE-05` | `P2` | `MET-COND` (OD-3 (ii)) | **`MET`** | The reported-run-artifacts reading is ratified |
| `PE-AUTH-02` | `P1` | `OPEN-EVIDENCE` (OD-4; transport reading under OD-3 (d)) | **`MET`**, by operator acceptance of gaps | OD-3 (d) is ratified. Every listed gap is accepted under the OD-4 reading. The row is met by the operator's acceptance, **not** by new evidence. It reverts to `OPEN-EVIDENCE` if the operator vetoes the OD-4 reading |
| `PE-EVIDENCE-01` | `P1` | `OPEN-EVIDENCE` (OD-4) | **`MET`**, by operator acceptance of gaps | Every listed gap is accepted under the OD-4 reading. Same limit and same reversion as `PE-AUTH-02` |

Other rows are affected only as follows:

* `PE-AUTH-03` (`MET`, unchanged): this record lists C2, C3 and C4 as
  pending, and it authorizes nothing.
* `PE-ACTIVATE-01` (`MET`, unchanged): this commit changes only one file
  under `docs/decisions/`. The three `PE-ACTIVATE-01` blobs are the blobs at
  `a04dea18`, equal to `08787a4b`.
* `PE-SCOPE-01` to `06` and `PE-TASK-03` (`MET`, unchanged): no plan, review,
  `.backlogit/` or shipment file changes.

## Updated Counts

| Status | Rows | IDs |
|---|---|---|
| `MET` | 29 | AUTH-02, AUTH-03, AUTH-04, SCOPE-01 to 07, FLOW-01 to 04, INTERFACE-02, INTERFACE-03, SAFETY-06, DATA-01 to 04, TASK-01, TASK-03, EVIDENCE-01, EVIDENCE-03, EVIDENCE-04, EVIDENCE-05, ACTIVATE-01, ACTIVATE-03 |
| `MET-COND` | 1 | AUTH-01 (`P0`, OD-12) |
| `OPEN-EVIDENCE` | 0 | none |
| `UNSATISFIED` | 0 | none |
| `WIN-MET / LINUX-PENDING` | 7 | SAFETY-01, 02, 03, 04, 05, 07, EVIDENCE-02 |
| `DEFERRED` | 3 | INTERFACE-01, TASK-02, ACTIVATE-02 |
| **Total** | **40** | 36 not-deferrable, 1 mixed (SAFETY-02) and 3 deferred |

Of the 37 not-deferrable or mixed rows, 29 are `MET`, 1 is `MET-COND` and 7
have their Linux half `PENDING`. Two of the 29 (`PE-AUTH-02`,
`PE-EVIDENCE-01`) are met by operator acceptance of evidence gaps, and
depend on the OD-4 reading standing.

**Rows still not `MET`:**

| Row | Why |
|---|---|
| `PE-AUTH-01` (`P0`) | OD-12: the operator must confirm that this record is part of the proof-exit report under the row's literal commit criterion |
| `PE-SAFETY-01`, `02`, `03`, `04`, `05`, `07`, `PE-EVIDENCE-02` | Linux half `PENDING`. No Linux-native run exists. This is a non-waivable execution and release gate (IM-01), not a deferral |
| `PE-INTERFACE-01`, `PE-TASK-02`, `PE-ACTIVATE-02` | `deferred-to-implementation-matrix` (IM-06, IM-11, IM-08) |

## Effect on the Implementation Matrix Draft

> **DRAFT, NOT RATIFIED.** Nothing here ratifies the matrix or any row of it.

Only these rows change, and only by losing a conditional qualifier. The
requirement text, severity and deferral of every row stay as drafted in
`a04dea18`.

| Draft ID | Status in `a04dea18` | Status now | Still open |
|---|---|---|---|
| IM-03 | Proof-backed, **conditional**, subject to OD-9. Not final until IM-16 and IM-17 are decided | **Proof-backed** (OD-9 accepted) | Not final until IM-16 (OD-10) and IM-17 (OD-11) are decided |
| IM-07 | Proof-backed, **conditional on OD-3**. CR-B1 to CR-B5 open | **Proof-backed** (OD-3 ratified) | CR-B1 to CR-B5 are open for implementation |
| IM-13 | Proof-backed, **conditional on OD-3**. The requirement reads "under R2 if the operator ratifies it (OD-3)" | **Proof-backed.** R2 is ratified, so the "if the operator ratifies it" clause is satisfied | Nothing new |

No other IM row carried an OD-3, OD-4, OD-5 or OD-9 qualifier. IM-10 stays
pending OD-7. IM-16 and IM-17 stay open on OD-10 and OD-11. IM-01 and IM-02
stay open, because Linux has not been executed.

## Open Decisions

| ID | Decision | Status | Plain language | Affects |
|---|---|---|---|---|
| C2 | Release-unit split | **Open.** The operator asked for a full explanation | How to cut the lifecycle work into separately shippable pieces | Phase 2 |
| C3 | Migration and the fate of `187-S`: retire or re-charter, never patch | **Open.** The operator asked for a full explanation. `187-S` stays `queued` and frozen | Whether the old frozen shipment is retired or re-chartered. It is never patched in place | Phase 2, claim |
| C4 | `P2` publication policy, reviewer lead and routing | **Open.** The operator asked for a full explanation | Which `P2` findings block publication (proposed: only matrix-critical ones), and which reviewer and model lead the next review epoch | Review epoch |
| OD-6 | Approve or withhold cleanup of the 17 scratch directories under `.proof-scratch/` | **Open.** The operator asked for a better explanation | Delete the leftover proof working folders, or keep them as hash-pinned evidence. Only Ship may remove them | Hygiene only |
| OD-7 | Authorize capture of the render-mismatch follow-up as a stash entry or release unit after proof exit | **Open.** The operator asked for a better explanation | Allow one installed skill file's line-wrap mismatch with its template to be logged as its own small future fix | IM-10 |
| OD-8 | Confirm the reading of section 8 against section 7.1 | **Open.** The operator asked for a plain-text explanation | Confirm that proof entry counts as exited once section 8 is met, and that rows that do not yet hold block ratification and Phase 2 but do not undo that exit | Every row not `MET` |
| OD-10 | Rule on R-C3b (Decision 2 items 2 and 5), or route it to an architecture decision | **Open** | In one rare double-failure case, choose which of two reason codes to report | IM-16 |
| OD-11 | Ratify, revise or reject the section 6.5 candidate proposals | **Open** | Agree whether the proven reason list is the list to build | IM-17, IM-03 |
| OD-12 (new) | Confirm that this rulings record is part of the Stage-authored proof-exit report (an addendum to `a04dea18`) for `PE-AUTH-01` | **Open.** Stage recommends confirmation | This file is not named like a findings file, so the strict commit rule needs a one-line yes | `PE-AUTH-01` |
| Veto window on the OD-4 reading | Keep or veto the Orchestrator's reading of "OD-4: approved" as acceptance of each gap | **Standing** until the operator says otherwise | If vetoed, OD-4 reopens and two rows go back to open evidence | `PE-AUTH-02`, `PE-EVIDENCE-01` |
| Matrix ratification | Ratify the implementation matrix draft IM-01 to IM-17 | **Open. Not ratified** | The operator's approval of the list of requirements that implementation must meet | Phase 2 and everything after it |

Resolved: OD-1 (superseded by `4c6e2701`), OD-2 (Option A, `e65887d8`),
OD-3, OD-4, OD-5 and OD-9 (this record).

## Remaining Gates

| Gate | What still blocks it |
|---|---|
| **Ratification of the implementation matrix** | OD-12 (so that no `MET-COND` row remains) and OD-8 (to fix the reading). OD-10 and OD-11 before IM-03 can be ratified as a final contract. The OD-4 reading must stand. Then the operator ratifies the draft itself. Stage does not ratify it |
| **Phase 2** (re-slice, harvest, plan) | Ratification above (`PE-TASK-03` forbids harvest before it), then C2 and C3. No plan revision, harvest or backlog item is created before that |
| **New review epoch** | Phase 2 output, C4, and ratification of the section 9 governance defaults |
| **Activation** (`PE-ACTIVATE-02`, IM-08) | A ratified matrix, a planned and reviewed release unit, and one task and one commit measured against `08787a4b`. Nothing is activated now |
| **Any claim of `187-S` or its successor** | C3 first. Then the ordinary P-002 and P-004 claim gates, CI and closure gates. No proof `PASS` confers claim authority (IM-15). Any release unit that depends on containment also needs IM-01, Linux-native execution, to pass. No one can waive it |
| **Cross-platform acceptance** (IM-02) | IM-01 |
| **Scratch cleanup** | OD-6 |
| **Render-mismatch follow-up capture** (IM-10) | OD-7 |
| **Publication** | Not ready (`publication_eligible: false`). There are 37 local commits ahead of upstream, 38 with this one, and none is pushed. Pushing is an operator action |

## What This Record Does Not Do

This record only records the four rulings (OD-3, OD-4, OD-5, OD-9) and their
effect on row statuses, counts and draft qualifiers. It **ratifies nothing
else**: not the implementation matrix or any IM row, not the section 6.5
candidate proposals, not R-C3b, not C2, C3 or C4, not the section 9
governance defaults, and not OD-6, OD-7, OD-8, OD-10, OD-11 or OD-12. It
**authorizes no** plan, plan revision, harvest, backlog item, shipment or
stash change, review epoch, activation, claim, proof run, push or pull
request. `187-S` stays `queued` and frozen.

## References

* Refresh report: `docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md` (`a04dea18`, PE-1.7), sections "Row Audit", "Implementation Matrix Draft, Refreshed", "Open Operator Decisions" and "Remaining Gates"
* Prior report: `docs/decisions/2026-09-24-lifecycle-proof-exit-spike.md` (`9c83517d`), rows `PE-AUTH-01`, `PE-AUTH-02` and `PE-EVIDENCE-01`
* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (PE-1.7, `e65887d8`; sections 3, 6.1, 6.9, 7.1, 7.2, 8, 9 and 10)
* Proof C run 4: `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run4-spike.md` (`4c6e2701`)
* Proof D run 5: `docs/decisions/2026-09-24-read-budget-proof-d-run5-spike.md` (`5976ff62`)
* Parent decision: `docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md`
