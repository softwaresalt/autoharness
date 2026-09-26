---
title: "Lifecycle proof-exit operator rulings 2 (2026-09-25): OD-6, OD-7, OD-8, C2 and C3 decided; C4 reviewer lead decided and C4 P2 policy pending confirmation; implementation matrix ratified with OD-10, OD-11 and OD-12 carve-outs; row statuses and counts unchanged"
source: "docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-2.md"
doc_type: decision
description: "Second Stage addendum to the PE-1.7 proof-exit refresh (a04dea18), recording the operator rulings given at 2026-09-25T17:19:15-07:00 on the decisions left open by the first rulings record (928bf3ff). OD-8 confirmed (proof entry has exited under section 8; rows that do not hold block ratification and Phase 2 but do not undo the exit). OD-6 decided: keep all scratch evidence until the work ships. OD-7 yes: stash entry 9144435A captures the IM-10 harness-architect render mismatch. C2 approved: release units A, B, C and D, with unit C allowed to fold into unit B within budget. C3 approved: retire 187-S; execution is deferred to Phase 2 and not performed here. C4 split: the reviewer-lead half is decided (gpt-6-sol), and is already satisfied by the existing model_routing.anchor_review route in .autoharness/config.yaml, which corrects earlier statements that no such key or route existed; the P2 publication-policy half is ambiguous and PENDING OPERATOR CONFIRMATION, with both readings listed. OD-4 stands; the operator asked for an explanation, and OD-4 is not reopened. The implementation matrix IM-01 to IM-17 is RATIFIED by the operator with carve-outs: IM-16 (OD-10), IM-17 (OD-11) and IM-03's finality stay open. PE-AUTH-01 (P0) stays MET-COND on OD-12, which this record widens to cover its own commit. OD-8 changes no row status. Totals unchanged: 29 MET, 1 MET-COND, 0 OPEN-EVIDENCE, 0 UNSATISFIED, 7 Windows-met with Linux PENDING, 3 deferred. Phase 2 must not start until OD-12 is answered and C4-P2 is confirmed. This record authorizes no plan, harvest, review epoch, activation, claim, retirement execution, push or pull request."
date: 2026-09-25
created: 2026-09-25
status: recorded
decision_status: partially-decided
deciders: operator
recorded_by: Stage
operator_rulings_at: "2026-09-25T17:19:15-07:00"
operator_rulings_relayed_by: Orchestrator
docline:
  type: decision
  date: 2026-09-25
  conclusion: "od-6-od-7-od-8-c2-c3-decided-c4-reviewer-decided-c4-p2-pending-matrix-ratified-with-carve-outs-counts-unchanged"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["stash:9144435A"]
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
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings.md, commit: 928bf3ff, relation: "second addendum; continues its open-decision list"}
  - {path: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md, commit: e65887d8, relation: "charter PE-1.7; section 9 anchor_review statement corrected here, not edited"}
  - {path: docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md, relation: "defines C2, C3 and C4"}
records_rulings_on: [docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md, docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings.md]
records_rulings_on_commits: [a04dea18, 928bf3ff]
prior_reports_edited: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.7"
charter_commit: e65887d8
charter_edited: false
matrix_id: PE-1.7
head_at_authoring: 928bf3ffeb0794ac86d287708397d978fbeec9c3
branch: chore/stage-176-s-workflow-defects
worktrees: 1
rulings:
  OD-4: {ruling: "standing (928bf3ff reading not vetoed)", note: "operator asked for an explanation of the 17 gaps; the Orchestrator provides it separately; not reopened", operator_may_veto: true, veto_effect: "reopens OD-4; PE-AUTH-02 and PE-EVIDENCE-01 revert to OPEN-EVIDENCE"}
  OD-6: {ruling: "withhold cleanup", reading: "keep all scratch evidence (.proof-scratch/ directories and docs/scratch/* artifacts) until the lifecycle work ships"}
  OD-7: {ruling: "yes", stash_entry_id: 9144435A}
  OD-8: {ruling: confirmed, row_status_effect: none}
  C2: {ruling: approved, reading: "release units A, B, C and D; unit C may fold into unit B when B stays within budget"}
  C3: {ruling: "retire 187-S", execution: "deferred to Phase 2; not performed here"}
  C4-reviewer-lead: {ruling: decided, model: gpt-6-sol, satisfied_by: ".autoharness/config.yaml model_routing.anchor_review (present since 5bcb00e5)"}
  C4-P2: {ruling: "pending operator confirmation", readings: ["only matrix-critical P2 findings block publication", "all P2 findings block publication; P3 never blocks"], assumed: none}
  matrix: {ruling: "ratified with carve-outs", not_ratified: [IM-16, IM-17], open_finality: [IM-03]}
pending_confirmation: [C4-P2]
stash_entry_created: true
stash_entry_id: 9144435A
stash_entry_kind: bug
stash_entry_priority: medium
backlog_item_created: false
proof_verdicts_changed: false
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
rows_changed: []
rows_condition_changed_status_unchanged: [PE-AUTH-01]
met_conditional_rows: [PE-AUTH-01]
open_evidence_rows: []
unsatisfied_rows: []
implementation_matrix_status: ratified-by-operator-with-carve-outs
im_rows_ratified: [IM-01, IM-02, IM-04, IM-05, IM-06, IM-07, IM-08, IM-09, IM-10, IM-11, IM-12, IM-13, IM-14, IM-15]
im_rows_ratified_finality_open: [IM-03]
im_rows_not_ratified: [IM-16, IM-17]
open_operator_decisions: [OD-10, OD-11, OD-12, C4-P2]
resolved_operator_decisions: {OD-1: "superseded (4c6e2701)", OD-2: "resolved, Option A (e65887d8)", OD-3: "approved (928bf3ff)", OD-4: "approved (928bf3ff; interpretation, vetoable, explanation pending)", OD-5: "confirmed (928bf3ff)", OD-6: "withhold cleanup until the work ships (this record)", OD-7: "yes; stash 9144435A (this record)", OD-8: "confirmed (this record)", OD-9: "accepted (928bf3ff)", C2: "approved (this record)", C3: "retire 187-S, execution deferred to Phase 2 (this record)", C4-reviewer-lead: "gpt-6-sol, already configured (this record)"}
cross_platform_acceptance: unmet
linux_gate: "not-deferrable, non-waivable execution and release gate (section 6.9); Windows evidence never satisfies it"
phase_2_ready: false
phase_2_blocked_by: [OD-12, C4-P2]
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

# Lifecycle proof-exit operator rulings 2 (2026-09-25)

## Bottom Line

| Question | Answer |
|---|---|
| What did the operator decide? | OD-8 confirmed. OD-6: keep all scratch evidence until the work ships. OD-7: yes, captured as stash entry **`9144435A`**. C2 approved. C3: retire `187-S`, with execution deferred to Phase 2. C4 reviewer lead: `gpt-6-sol`. The implementation matrix is **ratified with carve-outs** |
| What is still open? | OD-10, OD-11, OD-12 and the C4 `P2` publication policy (**C4-P2, pending confirmation**). The OD-4 veto window also stands while the Orchestrator explains the 17 gaps |
| What changes in the rows? | **No row status changes.** OD-8 fixes how rows are read, not what they hold. `PE-AUTH-01` (`P0`) stays `MET-COND` on OD-12, and OD-12 is widened to cover this record's commit |
| Counts | Unchanged: 29 `MET`, 1 `MET-COND`, 0 `OPEN-EVIDENCE`, 0 `UNSATISFIED`, 7 Windows-met with Linux `PENDING`, 3 deferred |
| Correction | `.autoharness/config.yaml` **already declares** `model_routing.anchor_review` (`openai`, `gpt-6-sol`, `high`). Earlier statements that no such key or route existed were wrong |
| Can Phase 2 start? | **No.** Not until OD-12 is answered and C4-P2 is confirmed |
| What does this authorize? | **Nothing** beyond recording the rulings and the one OD-7 stash capture. See [What This Record Does Not Do](#what-this-record-does-not-do) |

## Scope and Method

* **Actor.** Stage, directed by the Orchestrator. Stage wrote this one file
  and made one backlog write, the OD-7 stash entry. It ran no proof,
  fixture, build, test suite or linter other than a Markdown lint of this
  file, and no index refresh. It did not read or touch `187-S`, and made no
  push, branch, worktree or pull request. It did not touch any `git stash`
  entry.
* **Nothing earlier is edited.** The charter (`e65887d8`), the refresh report
  (`a04dea18`), the first rulings record (`928bf3ff`), the prior report
  (`9c83517d`) and every findings artifact stay as committed. Where this
  record corrects an earlier statement, the correction lives here only.
* **Fail-closed rule** (as in `928bf3ff`). A row becomes `MET` only if its
  sole remaining condition is closed by a ruling recorded here. A row that
  picks up a new condition is not counted as met.
* **Session state.** backlogit MCP `get_version` (update check skipped)
  returned `1.10.1-0.20260823032255-b07729386a31+dirty` (`TOOL_OK`). Index
  sync was not run, on purpose (`INDEX_SYNC_SKIPPED`, consistent with
  `PE-AUTH-01` and `928bf3ff`). Checkpoint recovery: `list_checkpoints` with
  `consumer_id: stage` and no status or agent filter returned 67 records, all
  `stage`/`resolved`, with 0 needing quarantine and 0 quarantined, which is a
  normal zero-candidate startup. The host tool wrapper again spooled that
  read-only output (74.4 KB) to OS Temp outside the working directory. Stage
  did not direct that write and read the spool read-only. Engram, intercom and
  graphtor-docs expose no tools here (`ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`,
  `GRAPHTOR_UNAVAILABLE`). The Orchestrator relays to the operator.
* **The stash write.** MCP `backlogit_stash` (kind `bug`, priority `medium`,
  both set at creation) returned `9144435A`. One `backlogit_stash_edit` on
  the same ID fixed one sentence of wording, with kind and priority
  unchanged. The net working-tree change is one appended line in the tracked
  file `.backlogit/stash.jsonl`. No other `.backlogit/` tracked file changed.

## Operator Rulings (verbatim)

Given at **2026-09-25T17:19:15-07:00** and relayed by the Orchestrator. Where
the relay quoted the operator's words, they are quoted. Where the relay gave
only the substance, it is marked *(substance)*.

> OD-4 *(substance)*: the operator asked for an explanation of the 17
> evidence gaps.
>
> OD-8: "Confirmed"
>
> OD-6 *(substance)*: keep all scratch files until the work ships.
>
> OD-7: "Yes"
>
> C2: "Approved"
>
> C3: "Retire 187-S"
>
> C4: "Only P2 findings block; lead reviewer to use gpt-6-sol" and "Probably
> should incorporate a reviewer specific routing in config.yaml"
>
> Matrix: "Don't know what OD-11 & OD-12 are about, otherwise, matrix
> ratified."

The operator did not mention OD-10. The decision definitions are in the
refresh report's "Open Operator Decisions" section (`a04dea18`). C2, C3 and
C4 are defined in the parent deliberation, section "Operator decisions".

### How Each Ruling Is Read

| Ruling | Reading recorded here | Basis |
|---|---|---|
| OD-4 (explanation requested) | **Not a veto. OD-4 is not reopened.** The `928bf3ff` reading (explicit operator acceptance of each of the 17 listed gaps) **stands**, pending no veto after the explanation. The Orchestrator gives the explanation separately. If the operator vetoes afterwards, OD-4 reopens and `PE-AUTH-02` and `PE-EVIDENCE-01` go back to `OPEN-EVIDENCE` | A request for an explanation is not a veto. `928bf3ff` set the veto window as standing until the operator says otherwise |
| OD-8 "Confirmed" | Confirms the reading of charter section 8 against section 7.1: **proof entry has exited** once section 8 is met, and `not-deferrable` rows that do not hold **block ratification and Phase 2 but do not undo the exit**. Section 8 was met by the refresh report (`a04dea18`): every proof is `PASS` except G, which is `PENDING-LINUX` with its Linux gate carried as IM-01, and report items 1 to 5 are present. Consequences are under [OD-8: What It Changes](#od-8-what-it-changes) | OD-8 was a confirm-or-reject decision on a stated reading |
| OD-6 (keep until the work ships) | **Cleanup is withheld.** The 17 Git-ignored `.proof-scratch/` directories named in OD-6 stay in place as evidence, including the C run 1 to 4 directories that Proof C run 4 asked to keep hash-pinned. On the Orchestrator's relay, the ruling also covers the `docs/scratch/*` artifacts: none is deleted before shipment closure. "The work ships" is read fail-closed as closure of the **last** lifecycle release unit that succeeds `187-S` (see C2 and C3), unless the operator says otherwise. When cleanup is due, Ship alone removes `.proof-scratch/` directories, under charter section 6.1 | OD-6 was approve-or-withhold. "Keep until the work ships" is withhold, with a release condition |
| OD-7 "Yes" | Stage captures the IM-10 render-mismatch follow-up as **one** stash entry: **`9144435A`**, kind `bug`, priority `medium`. It cites the IM-10 row of `a04dea18` verbatim, plus the Proof C run 2 facts. `bug` fits better than a task, because the installed file is drifted from its template render. `medium` is kept, because IM-10's `P1` severity applies at the future byte-exact resolver gate, not to current work. The entry is a capture only. It is not a release unit, plan or harvest | OD-7 offered "a stash entry or release unit after proof exit". OD-8 confirms that proof entry has exited |
| C2 "Approved" | Approves the parent decision's bounded proposal: **the A / B / C / D release-unit split in Phase 2, with unit C allowed to fold into unit B when B stays within budget.** The units are listed under [C2: What Is Approved](#c2-what-is-approved). Each unit must still meet the remediation budget (at most 6 tasks, at most 8 hours, independently valuable; IM-11). The approval fixes the Phase 2 DAG shape. It harvests nothing | Parent deliberation, "C2 - release-unit split"; Phase 2 table; `928bf3ff` Open Decisions row C2 |
| C3 "Retire 187-S" | Chooses **retire** over re-charter for `187-S`. Patching was never an option. The migration target (the acceptance matrix and a structured review index) is as proposed. **Execution is deferred to Phase 2 and is not performed or authorized by this record.** `187-S` stays `queued` and frozen until then. See [C3: Retirement Mechanics Deferred](#c3-retirement-mechanics-deferred) | Parent deliberation, "C3 - migration and the fate of 187-S" |
| C4 reviewer lead | **Decided:** the lead reviewer model is `gpt-6-sol`. The existing `model_routing.anchor_review` route already names it, so no configuration change is needed. See [C4: Reviewer Lead and the anchor_review Correction](#c4-reviewer-lead-and-the-anchor_review-correction) | The operator named the model directly |
| C4 `P2` policy | **AMBIGUOUS. PENDING OPERATOR CONFIRMATION.** Both readings are listed under [C4-P2: Two Readings, Neither Assumed](#c4-p2-two-readings-neither-assumed) | "Only P2 findings block" does not name one reading |
| Matrix | **Ratified by the operator, with carve-outs.** See [Implementation Matrix Ratification](#implementation-matrix-ratification) | "otherwise, matrix ratified", with OD-11 and OD-12 excluded by the operator's own words |

## OD-8: What It Changes

OD-8 changes **no row status and no count.** It fixes how the rows are read:

* **Proof entry is exited.** The refresh report (`a04dea18`) is the section 8
  report. The first rulings record and this record are addenda written after
  that exit.
* **Rows that do not hold block later gates, not the exit.** `PE-AUTH-01`
  (`MET-COND`), the 7 Linux-`PENDING` rows and the 3 deferred rows keep their
  statuses. They block matrix ratification and Phase 2 where the charter says
  so. They do not undo the exit. Section 7.1's wording ("`P1` blocks proof
  exit"; "`not-deferrable` must hold at proof exit") is read on these terms.
* **The proof-entry freezes lift where the charter ties them to exit.**
  `PE-SCOPE-03` says the backlog, carriers, shipment and stash are frozen
  "until proof exit" (deferral: "lifts at proof exit"). That is why the OD-7
  stash capture, which OD-7 itself bounds to "after proof exit", is made now.
  `PE-SCOPE-03` stays `MET`: its literal criterion covers `.backlogit/queue/`
  and `.backlogit/archive/` for `181-F` and `181.*` and `187-S` read-back,
  and none of those changed. Lifting the freeze does **not** open Phase 2 or
  permit any `187-S` change. Those stay gated below.
* **Effect on `PE-AUTH-01` and OD-12.** See
  [Row-Status Consequences](#row-status-consequences).

## C2: What Is Approved

From the parent deliberation, Phase 2 table:

| Unit | Content | Independent value |
|---|---|---|
| A | Actor and P-004 conformance, plus per-task lifecycle semantics | The evidence contract becomes true and testable |
| B | Resolver, one-entry `SurfaceSpec`, result schema and CLI | A working, callable resolver |
| C | Portable ordinary-containment reader on Windows and Linux. **May fold into B if B stays within budget** | Required containment and bounds |
| D | Final Ship activation: template, mirror and manifest checksum in one task and one commit (IM-08) | The lifecycle goes live |

Not approved by C2: any plan, harvest, task, shipment or DAG edge. Whether
C folds into B is decided at Phase 2 against the budget, not here. Any unit
that depends on containment (at least C, or B if C folds into it) still needs
IM-01, the Linux-native run, before it ships.

## C3: Retirement Mechanics Deferred

* **Approved:** retire `187-S`. **Not done:** any retirement step. This
  record does not read, move, activate, claim or abandon `187-S`, `181-F` or
  any `181.*` item.
* **Mechanics must be checked at Phase 2.** The Orchestrator reports that, in
  backlogit 1.8.0, the only supported path to an abandoned shipment is
  `queued` to `active` to `abandoned`. This workspace's backend reports
  `1.10.1-0.20260823032255-b07729386a31+dirty`. Stage has not checked the
  path on either version. At Phase 2, the retirement mechanism must be
  verified against the installed version before anything is done.
* **Retirement is not a Ship execution.** If the only path to `abandoned`
  passes through `active`, that transition must **not** be recorded or
  performed as a Ship claim or Ship execution of `187-S`, and must not make
  `187-S` claim-ready (`PE-SCOPE-04`, IM-15). Stage may not claim or close a
  shipment on Ship's behalf (P-010). If no retirement path avoids a claim-like
  transition, the mechanism goes back to the operator for a ruling.
* **The fate of `181-F` and its 17 items** under retirement (archive,
  re-parent or re-slice into the C2 units) is a Phase 2 decision and is not
  made here.

## C4: Reviewer Lead and the anchor_review Correction

**The reviewer-lead half is decided and already satisfied.** The working
configuration declares:

```yaml
model_routing:
  anchor_review:
    model_provider: "openai"
    model_family: "gpt-6-sol"
    reasoning_effort: "high"
```

`schemas/harness-config.schema.json` (around line 726) defines
`anchor_review` as the "First-class anchor reviewer route used by
adversarial, plan, and code review flows". It requires `model_provider` and
`model_family` and allows no other properties besides `reasoning_effort`.
The schema default family is `gpt-5.6-sol`. This workspace overrides it with
`gpt-6-sol`.

Git history of `.autoharness/config.yaml`, read read-only:

| Commit | `anchor_review` |
|---|---|
| `5bcb00e5^` | Absent |
| `5bcb00e5` (2026-09-23 22:15:47 -07:00) | Added: `openai`, `gpt-6-sol`, `high` |
| `89b0db6d`, `08787a4b`, HEAD `928bf3ff` | Unchanged: `openai`, `gpt-6-sol`, `high` |

**Corrections.** These earlier statements were wrong, and this record
corrects them without editing the originals:

| Statement | Where | Why it is wrong |
|---|---|---|
| "No `model_routing.anchor_review` route is selected" (row C4) | Refresh report, `a04dea18`, "Open Operator Decisions" | At `a04dea18` the route had been configured, and committed, since `5bcb00e5`. No C4 lead had been ratified, but a configured route existed |
| "No `model_routing.anchor_review` route is selected here" (row C4) | Prior report, `9c83517d` | The same error. The route existed at its HEAD |
| "The working configuration, inspected read-only, declares no `model_routing.anchor_review` key" | Charter, section 9 (text dating from v1.0, `2e3c98a1`, carried unchanged to v1.7, `e65887d8`) | True when first written at `2e3c98a1` (2026-09-23 17:45:26 -07:00), because the key was added about 4.5 hours later in `5bcb00e5`. It was wrong from `5bcb00e5` onward, and is wrong as a statement in charter v1.7 |
| "declares no `model_routing.anchor_review` key" | Parent deliberation (`082df7b2`), reviewer-routing row | True when written. It is historical only, and not a current fact |

**"Probably should incorporate a reviewer specific routing in config.yaml."**
That reviewer-specific route already exists, as shown above. No change is
made in this record (`config_changed: false`). Any further change, for
example raising `reasoning_effort` to `xhigh`, would be an operator setup
commit. It would need a manifest checksum refresh from raw staged-blob bytes
(IM-12). It would also change the config blob relative to the
`PE-ACTIVATE-01` / IM-08 comparator `08787a4b`, so it would need to be
recorded against that comparator. Under the parent decision, any route change
must happen before the review epoch opens, because a mid-epoch route change
pauses the epoch. Stage has not verified that each review skill actually
dispatches this route at run time. The schema says a skill must declare
degradation when it cannot dispatch the route.

### C4-P2: Two Readings, Neither Assumed

`P0` and `P1` findings **always** block, whatever C4-P2 says. That comes from
the parent decision's publication gate ("zero admitted `P0` and `P1`") and,
for merge readiness, from P-014 (no unresolved `P0`/`P1`). C4-P2 decides only
what `P2` (and `P3`) findings do at publication.

| Reading | Meaning | Source of the reading |
|---|---|---|
| 1 | **Only matrix-critical `P2` findings block publication.** Other `P2` findings are recorded and followed up. This is the standing proposal in the parent decision and charter section 9 | The Orchestrator reads "Only P2 findings block" as most likely a confirmation of this proposal |
| 2 | **All `P2` findings block publication. `P3` never blocks** (advisory only) | The literal words "Only P2 findings block" |

**Neither reading is assumed.** The Orchestrator's relay named both. C4-P2
stays **PENDING OPERATOR CONFIRMATION**. It gates the review epoch (Phase 4)
and, on the Orchestrator's direction, Phase 2 as well.

## Implementation Matrix Ratification

**The operator ratified the implementation matrix IM-01 to IM-17, with
carve-outs.** It is recorded as operator-given. Stage does not ratify it.

| Draft ID | Status after this record |
|---|---|
| IM-01, IM-02, IM-04 to IM-09, IM-11 to IM-15 | **Ratified** as drafted in `a04dea18`, with the `928bf3ff` qualifier removals for IM-07 and IM-13. That includes each row's proposed severity and deferral, such as IM-09's `operator-deferrable` designation. Ratifying a requirement is not meeting it: IM-01 and IM-02 stay **unmet**, because Linux has not been executed |
| IM-10 | **Ratified.** Capture is done under OD-7: stash `9144435A`. The requirement is unchanged. The reconciliation still needs its own operator-approved release unit before any byte-exact render-parity resolver runs against `harness-architect` at HEAD |
| IM-03 | **Ratified as a proof-backed requirement.** Its row already allows "a ratified revision ... re-proven the same way". **Its finality as the frozen resolver contract stays open** until IM-16 and IM-17 are decided |
| IM-16 | **Not ratified. Open on OD-10.** The operator did not mention OD-10 |
| IM-17 | **Not ratified. Open on OD-11.** The operator asked what OD-11 is about |

**Preconditions, stated honestly.** `928bf3ff` listed what ratification should
wait for: OD-12 (so that no `MET-COND` row remains), OD-8 (to fix the
reading), OD-10 and OD-11 (before IM-03 is final) and the OD-4 reading
standing. Where they stand now:

| Precondition | Status |
|---|---|
| OD-8 | **Met.** Confirmed here |
| OD-4 reading stands | **Met for now.** It stands, and the veto window stays open while the explanation is given |
| OD-10 and OD-11 before IM-03 is final | **Respected by the carve-outs.** IM-16, IM-17 and IM-03's finality are excluded |
| OD-12, so that no `MET-COND` row remains | **Not met.** The operator ratified while OD-12 was still open. `PE-AUTH-01` (`P0`) stays `MET-COND` |

Only the operator ratifies the matrix (charter section 3), so the ratification
is recorded as given. It does not close OD-12 or change `PE-AUTH-01`.
**Phase 2 (re-slice, harvest, `187-S` retirement) and the review epoch must
not start until OD-12 is answered and C4-P2 is confirmed.** If a later OD-4
veto reopens `PE-AUTH-02` and `PE-EVIDENCE-01`, Stage will re-present the
matrix position before Phase 2.

## Row-Status Consequences

**No row changes status.** One row's condition is widened.

| Row | Sev | Status in `928bf3ff` | Status now | Reason |
|---|---|---|---|---|
| `PE-AUTH-01` | `P0` | `MET-COND` (OD-12) | **`MET-COND` (OD-12, widened)** | OD-12 asked the operator to confirm that `928bf3ff` is part of the Stage-authored proof-exit report under the row's literal commit criterion: every proof-phase commit changes only `docs/decisions/*-spike.md` findings or the proof-exit report, and Stage makes no backlog mutation. **This record's commit raises the same question twice over.** (a) It adds a second `docs/decisions/` file not named `*-spike.md` (`artifact_class: proof-exit-report-addendum`). (b) It changes `.backlogit/stash.jsonl` by one line, the OD-7 stash entry. Stage's reading under OD-8 is that proof entry exited at `a04dea18`, so this commit is post-exit, and the stash write is the post-exit capture OD-7 allows. But that reading bears on the very classification OD-12 asks about, so the row is **not** counted as met. OD-12 now covers both `928bf3ff` and this commit. See the OD-12 row under [Open Decisions](#open-decisions). If the operator treated this commit as a proof-phase commit **and** rejected the post-exit stash write, the row would be `UNSATISFIED`, a `P0`, which halts to the operator under section 7.1 |

Other rows, checked against this commit:

* `PE-AUTH-03` (`MET`, unchanged). The row forbids **self**-authorization of
  retirement, re-charter, reviewer selection or `P2` policy. Every decision
  recorded here is an operator ruling, quoted with its timestamp. This record
  authorizes nothing itself: C3 execution is deferred and C4-P2 is left
  pending. The row's criterion ("the proof-exit report lists C2, C3 and C4 as
  pending") was met by the report at exit (`a04dea18`, and `928bf3ff`), and
  under OD-8 later operator decisions do not undo the exit. This is a Stage
  reading and is disclosed here. If the operator disagrees, `PE-AUTH-03`
  becomes `MET-COND` on that point.
* `PE-SCOPE-03` (`MET`, unchanged). See [OD-8: What It Changes](#od-8-what-it-changes).
* `PE-SCOPE-01`, `02`, `04` to `06` and `PE-TASK-03` (`MET`, unchanged). No
  plan, review, `.backlogit/queue/`, `.backlogit/archive/`, shipment or lock
  file changes. No harvest happens: Phase 2 is held.
* `PE-ACTIVATE-01` (`MET`, unchanged). Since `08787a4b`, only
  `docs/decisions/` files have changed, and this commit adds one more plus
  `.backlogit/stash.jsonl`. The template, mirror, manifest and config blobs
  are the blobs at `08787a4b`.
* `PE-FLOW-02` (`MET`, unchanged). The matrix is now ratified with
  carve-outs, but Phase 2 stays held by OD-12 and C4-P2.

## Updated Counts

Unchanged from `928bf3ff`.

| Status | Rows | IDs |
|---|---|---|
| `MET` | 29 | AUTH-02, AUTH-03, AUTH-04, SCOPE-01 to 07, FLOW-01 to 04, INTERFACE-02, INTERFACE-03, SAFETY-06, DATA-01 to 04, TASK-01, TASK-03, EVIDENCE-01, EVIDENCE-03, EVIDENCE-04, EVIDENCE-05, ACTIVATE-01, ACTIVATE-03 |
| `MET-COND` | 1 | AUTH-01 (`P0`, OD-12, widened) |
| `OPEN-EVIDENCE` | 0 | none |
| `UNSATISFIED` | 0 | none |
| `WIN-MET / LINUX-PENDING` | 7 | SAFETY-01, 02, 03, 04, 05, 07, EVIDENCE-02 |
| `DEFERRED` | 3 | INTERFACE-01, TASK-02, ACTIVATE-02 |
| **Total** | **40** | 36 not-deferrable, 1 mixed (SAFETY-02) and 3 deferred |

Two of the 29 (`PE-AUTH-02`, `PE-EVIDENCE-01`) are met by operator acceptance
of evidence gaps and depend on the OD-4 reading standing after the
explanation.

## Open Decisions

| ID | Decision | Status | Plain language | Affects |
|---|---|---|---|---|
| OD-12 (widened) | Confirm that the rulings records `928bf3ff` **and this record** are part of the Stage-authored proof-exit report, and that this commit's one-line `.backlogit/stash.jsonl` change is the post-exit OD-7 capture, outside `PE-AUTH-01`'s proof-phase commit rule. Alternatively, rule under OD-8 that commits after the `a04dea18` report are post-exit and outside `PE-AUTH-01` entirely. Either answer closes the row | **Open.** The operator asked what it is about. Stage recommends confirmation | The strict rule for proof-phase commits allows only findings files and the report. These two follow-up records are neither by name, and this one also adds a stash line. A one-line yes clears it | `PE-AUTH-01`; Phase 2 |
| C4-P2 | Which `P2` findings block publication: reading 1 (only matrix-critical `P2`) or reading 2 (all `P2`; `P3` never) | **Pending operator confirmation** | Say which of the two you meant | Review epoch; Phase 2 (Orchestrator hold) |
| OD-10 | Rule on R-C3b (Decision 2 items 2 and 5), or route it to an architecture decision | **Open.** Not mentioned by the operator | In one rare double-failure case, choose which of two reason codes to report | IM-16, IM-03 finality |
| OD-11 | Ratify, revise or reject the section 6.5 candidate proposals | **Open.** The operator asked what it is about | Agree whether the proven reason list is the list to build | IM-17, IM-03 finality |
| OD-4 veto window | Keep or veto the reading of "OD-4: approved" as acceptance of each of the 17 gaps | **Standing.** Explanation being given by the Orchestrator | If vetoed, OD-4 reopens and two rows go back to open evidence | `PE-AUTH-02`, `PE-EVIDENCE-01` |

Resolved: OD-1 (superseded, `4c6e2701`), OD-2 (Option A, `e65887d8`), OD-3,
OD-4 (vetoable), OD-5 and OD-9 (`928bf3ff`), and OD-6, OD-7, OD-8, C2, C3,
the C4 reviewer lead and matrix ratification with carve-outs (this record).

## Remaining Gates

| Gate | What still blocks it |
|---|---|
| **Phase 2** (re-slice under C2, harvest, `187-S` retirement under C3) | OD-12 answered and C4-P2 confirmed. `PE-TASK-03` harvest rule: the matrix is now ratified with carve-outs. Retirement mechanics must be checked first (see C3) |
| **IM-03 as the final resolver contract** | OD-10 (IM-16) and OD-11 (IM-17) |
| **New review epoch** (Phase 4) | Phase 2 and 3 output, C4-P2, and ratification of the section 9 governance defaults. The lead reviewer route is already configured (`anchor_review`, `gpt-6-sol`) |
| **Activation** (`PE-ACTIVATE-02`, IM-08, unit D) | A planned and reviewed release unit, one task and one commit measured against `08787a4b`. Nothing is activated now |
| **Any claim of a successor to `187-S`** | Phase 2 re-slice first. Then the ordinary P-002 and P-004 claim gates, CI and closure gates. No proof `PASS` confers claim authority (IM-15). Any containment-dependent unit also needs IM-01, the Linux-native run, which no one can waive |
| **Cross-platform acceptance** (IM-02) | IM-01 |
| **Scratch cleanup** | Withheld under OD-6 until the last lifecycle release unit closes |
| **IM-10 reconciliation** | Captured as stash `9144435A`. Needs triage and its own operator-approved release unit before the byte-exact resolver runs |
| **Publication** | Not ready (`publication_eligible: false`). There are 38 local commits ahead of upstream, 39 with this one, and none is pushed. Pushing is an operator action |

## What This Record Does Not Do

This record only records the rulings of 2026-09-25T17:19:15-07:00, their
effect on the open-decision list, the `anchor_review` correction, and one
stash capture under OD-7 (`9144435A`). It **does not decide** OD-10, OD-11,
OD-12 or C4-P2, and it does not reopen OD-4. It **does not ratify** IM-16,
IM-17 or IM-03's finality, the section 6.5 candidate proposals, R-C3b or the
section 9 governance defaults. It **authorizes no** plan, plan revision,
harvest, backlog item, shipment change, `187-S` retirement step, review
epoch, activation, claim, configuration change, proof run, scratch cleanup,
push or pull request. `187-S` stays `queued` and frozen until Phase 2.

## References

* Refresh report: `docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md` (`a04dea18`, PE-1.7), sections "Implementation Matrix Draft, Refreshed" (IM-10) and "Open Operator Decisions" (OD-6, OD-7, OD-8, C4)
* First rulings record: `docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings.md` (`928bf3ff`), sections "Open Decisions" and "Remaining Gates"
* Parent decision: `docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md`, Phase 2 table and "Operator decisions" (C2, C3, C4)
* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (PE-1.7, `e65887d8`; sections 3, 6.1, 7.1, 7.2, 7.3, 8, 9 and 10)
* Proof C run 2: `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run2-spike.md` (render-parity facts for IM-10)
* Proof C run 4: `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run4-spike.md` (`4c6e2701`)
* Configuration: `.autoharness/config.yaml` (`model_routing.anchor_review`); schema `schemas/harness-config.schema.json` (`anchor_review`, around line 726)
* Policies: `.github/policies/workflow-policies.md` (P-010, P-014)
* Stash entry: `9144435A` (IM-10 render-parity follow-up)
