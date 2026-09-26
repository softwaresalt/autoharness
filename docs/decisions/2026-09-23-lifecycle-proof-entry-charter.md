---
title: "Lifecycle proof-entry charter and acceptance matrix, version 1.7"
description: "Operator-approved proof-entry charter for the Ship pre-task harness-generation lifecycle, issued under the 2026-09-23 Option B governance reset with proportionate Option D containment. Freezes lifecycle plan revision 12 and review attempt 11 as diagnostic evidence; fixes the proportionate threat model (operator-controlled local workspace, ordinary static containment on actual Windows and Linux, no race or hardlink-alias claims); defines a seven-proof bounded portfolio with narrow questions, time and file bounds and pass/fail criteria; and fixes acceptance matrix PE-1.1, in which every row carries an existing normative source, a verifiable pass criterion, evidence, violation severity and deferral status. Version 1.1 is an operator-approved correction of proof actor and timing only: Stage performs read-only analysis and authors the findings; Ship runs verification-only disposable fixture commands in a named scratch directory inside the one current worktree; no additional worktree is used; Linux evidence that cannot be produced at proof entry is PENDING, never PASS, and becomes a non-waivable execution and release gate. Frozen for proof entry only: the implementation acceptance matrix is ratified after proof evidence and before any new review epoch. Version 1.2 (matrix PE-1.2) changes Proof D only, after Proof D failed under PE-1.1: it re-charters section 6.6 and rows PE-DATA-03 and PE-SAFETY-04 against the decided admitted maximum of 48 members, the unchanged max_files=256, an explicit byte non-guarantee (byte exhaustion is a bounded UNRESOLVED failure, never success) and the read-limit exhaustion mapping to UNRESOLVED / 2 at every read and recheck stage; every other row, proof and verdict is unchanged. Version 1.3 (matrix PE-1.3) changes only two terms of Proof E (section 6.7) and the PE-ACTIVATE-01 comparator, after Proof E was recorded BLOCKED under PE-1.2: 'checkpoint validate-and-resolve' means unique selection plus owner and schema validation before restore, never a status resolution before resume; 'retained text' means the text kept after the planned activation edits; and PE-ACTIVATE-01 compares raw Git blobs at the operator-approved snapshot 5bcb00e5 instead of 082df7b2. No proof is re-run or re-labelled and Proof E stays BLOCKED. Version 1.4 (matrix PE-1.4) is a bounded, operator-approved correction with three parts. First, Ship alone runs its existing Step 0.1 backlog index refresh (backlogit_sync_index, or the registered backlogit sync CLI fallback) before any semantic backlog read in every proof invocation. The refresh may rewrite only Git-ignored, tool-managed cache under the current working directory. It is not a backlog edit and not a new release unit. A refresh that fails, or cannot be verified, on both transports makes the invocation BLOCKED. Second, PE-ACTIVATE-01 now compares against the operator-authorized setup snapshot 4acba14a, because the setup commits d20820ec and 4acba14a changed only the Ship role-permission rows and the mirror checksum. The 5bcb00e5 record is kept under version 1.3. Third, Proof C (section 6.5) is re-chartered for run 2. It is tested against a governing reason set that includes FILE_COUNT_LIMIT, TOTAL_SIZE_LIMIT and FILE_SIZE_LIMIT as class 1b UNRESOLVED / 2 reasons. It also carries an explicit Stage candidate (a proposal, not ratified API), per-execution raw or hashed output, and a real-surface render control that uses the top-level variables_used mapping. Every earlier verdict stays as recorded. Proof B, Proof D run 2 and Proof F are historical PASS verdicts without recorded Ship index refresh, so each needs a new admissible PE-1.4 run before proof exit. Version 1.5 (matrix PE-1.5) is a bounded delegated correction of Proof E's section 6.7 retained-text scope only, after Proof E run 4 was recorded BLOCKED under PE-1.4 on a retained-text reading fork. It adds two template passages to the section 6.7 planned replacements: the Session start sentences that restore memory context before the recovery state machine, and the context-overflow Resumption Protocol. It also states the post-activation contract they must meet: no memory-context, cursor, phase or next-action restore before the unfiltered anomaly scan and explicit unique owner and schema validation, with operator confirmation where a candidate exists; no bypass through any memory checkpoint; zero candidates are normal continuation; resolution only after a confirmed successful resume. The installed mirror has no matching passage, so its planned insertion and retained recovery protocol are unchanged. No Ship surface is edited now. Every matrix row, pass criterion, the PE-1.3 validate-and-resolve term, the PE-1.4 index refresh, the Proof C candidate and the activation baseline 4acba14a are unchanged. Every recorded verdict stands, Proof E run 4 stays BLOCKED, and Proof E needs a fresh run 5 under PE-1.5. Version 1.6 (PE-1.6, a bounded delegated decision) changes only the Proof C clock rule and time bound for run 4 onward (section 3.5); it changes no row or pass criterion, relabels no verdict (Proof C run 1 FAIL, run 2 BLOCKED, run 3 FAIL stand), leaves the PE-FLOW-04 status of Proof D run 4 to an operator ruling, and authorizes no run. Version 1.7 (matrix PE-1.7) is an explicit operator-approved change of two items only (section 3.6). First, the PE-ACTIVATE-01 comparator moves from the setup snapshot 4acba14a to the operator-approved snapshot 08787a4b, whose change to the three rows' paths is frontmatter-only model routing in the installed Ship mirror (lines 8-10) and three manifest checksum values with their notes; the template blob is unchanged, no body text changed and every section 6.7 anchor line is unchanged, so the rebaseline is not an activation and hides none. Second, the operator's PE-FLOW-04 ruling (Option A) is recorded: Proof D run 4 (36f65975, PE-1.4) is a recorded historical exception, Proof D run 5 (5976ff62, PE-1.5) is Proof D's admissible evidence, and the row is read prospectively from version 1.7 onward; the row text is unchanged, no verdict is relabelled and the run 4 breach stays on the record. Every other row, every proof's question, bounds and criteria, and the Proof C clock rule are unchanged, and version 1.7 authorizes no proof run. Subordinate to the constitution and the workflow policy registry; overrides nothing."
doc_type: decision
artifact_class: proof-entry-charter
source: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
date: 2026-09-23
status: decided
decision_status: decided
charter_version: "1.7"
matrix_id: PE-1.7
supersedes_version: "1.6"
superseded_version_commit: cd2ef261
version_history:
  - {version: "1.0", matrix_id: PE-1.0, commit: 2e3c98a1}
  - {version: "1.1", matrix_id: PE-1.1, commit: 1ad7c03a, scope: "proof actor and timing only"}
  - {version: "1.2", matrix_id: PE-1.2, commit: 286aa4af, scope: "Proof D only (section 6.6, PE-DATA-03, PE-SAFETY-04)", decision: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md}
  - {version: "1.3", matrix_id: PE-1.3, commit: 7f833cb8, scope: "Proof E terms (section 6.7) and PE-ACTIVATE-01 comparator only", record: "section 3.2", findings: docs/decisions/2026-09-24-ship-activation-proof-e-spike.md}
  - {version: "1.4", matrix_id: PE-1.4, commit: 52c985cb, scope: "Ship Step 0.1 index refresh in proofs (sections 4.3, 6.1; PE-AUTH-01, PE-AUTH-02, PE-EVIDENCE-01), PE-ACTIVATE-01 setup-snapshot comparator, and Proof C run 2 (section 6.5; PE-DATA-01, PE-DATA-02) only", record: "section 3.3", findings: docs/decisions/2026-09-24-surface-taxonomy-proof-c-spike.md}
  - {version: "1.5", matrix_id: PE-1.5, commit: d31d7b42, scope: "Proof E section 6.7 retained-text planned replacement set only (template Session start memory-context restore and context-overflow Resumption Protocol, with their post-activation contract); no row or pass-criterion text changed", record: "section 3.4", findings: docs/decisions/2026-09-24-ship-activation-proof-e-run4-spike.md}
  - {version: "1.6", matrix_id: PE-1.6, commit: cd2ef261, scope: "Proof C clock start, clock end and time bound for run 4 onward only (sections 6.1, 6.2, 6.5); no row or pass-criterion text changed; no verdict relabelled; PE-FLOW-04 row text unchanged", record: "section 3.5", findings: docs/decisions/2026-09-24-surface-taxonomy-proof-c-run3-spike.md}
  - {version: "1.7", matrix_id: PE-1.7, scope: "PE-ACTIVATE-01 comparator rebaselined from 4acba14a to the operator-approved snapshot 08787a4b (frontmatter-only mirror routing and manifest checksum values; no activation), and the operator's PE-FLOW-04 ruling (Option A: Proof D run 4 a recorded historical exception, Proof D run 5 the admissible Proof D evidence, row read prospectively) only; PE-FLOW-04 row text unchanged; no verdict relabelled; no proof run authorized", record: "section 3.6", findings: docs/decisions/2026-09-24-lifecycle-proof-exit-spike.md}
freeze_scope: proof-entry-only
implementation_matrix_status: not-ratified
deciders: operator, Stage
operator_approval: "2026-09-23 - Option B governance reset combined with the proportionate Option D containment scope"
version_1_1_operator_approval: "2026-09-23 - operator 'Proceed' on the exact proposed correction: PE-1.0 to PE-1.1, proof actor and timing only (no Stage executable proof and no extra worktree; Ship verification-only fixture execution in the one current worktree; Stage read-only analysis and findings authorship; Linux PENDING, never PASS, when no Linux host exists at proof entry)"
version_1_2_operator_approval: "2026-09-24 - operator instruction to act on Proof D's reopened decisions, authorizing a clearly identified versioned PE-1.2 change limited to Proof D (preserve Proof A and F verdicts; keep B, C, E and G separate); the concrete bound was selected by Stage under that bounded delegation and may be vetoed by the operator before the Proof D run 2 handoff"
head_at_version_1_2: b6366cef
version_1_3_operator_approval: "2026-09-24 - operator order 'Don't just tell me what is required, act on it' on Proof E's BLOCKED findings, with the Orchestrator's relayed selection of the readings dictated by the higher Ship recovery protocol (validate-and-resolve = selection plus owner/schema validation before restore; status resolution only after a confirmed successful resume) and of post-activation retained text, and of the operator-approved snapshot 5bcb00e5 as the PE-ACTIVATE-01 baseline; limited to section 6.7 terms and the PE-ACTIVATE-01 comparator; the operator may veto before the fresh Proof E handoff"
head_at_version_1_3: a04e1e5a
version_1_4_operator_approval: "2026-09-24 - operator order, relayed verbatim as 'You have not yet marked the task as complete ... stop planning and start implementing ... make good decisions and keep working autonomously until ... finished', with the Orchestrator's relayed bounding: approval of the necessary proof-entry contract correction PE-1.4 only (Ship Step 0.1 index refresh inside proofs, the PE-ACTIVATE-01 setup-snapshot comparator 4acba14a, and Proof C run 2 under Decision 2), and explicitly not approval to claim or merge any shipment or to relax P-001, P-002, P-009, P-011, P-014 or P-016"
head_at_version_1_4: 4acba14a
version_1_5_operator_approval: "2026-09-24 - bounded delegated decision; the operator did not literally select 'Option A'. Operator general instruction of 2026-09-24T14:58:27-07:00, given after the previous session's failed proofs and relayed to Stage by the Orchestrator as 'If ... open questions or ambiguities—make good decisions and keep working; if error resolve or alternative; complete remaining steps' (a relayed wording with elisions; Stage did not see the original and quotes nothing beyond the relay), with the Orchestrator's publicly recorded selection of Proof E run 4 Option A (add template Session start lines 1004-1006 and the context-overflow Resumption Protocol lines 1103-1107, at 4acba14a, to the section 6.7 planned replacements), bounded to that section 6.7 retained-text scope only; explicitly not approval to claim or merge any shipment, to edit any Ship surface or manifest now, or to relax P-001, P-002, P-004, P-011, P-016 or any other safety gate; the operator may veto before the Proof E run 5 handoff"
head_at_version_1_5: 945a224e
version_1_6_operator_approval: "2026-09-24 - bounded delegated decision; the operator did not literally approve 'charter version 1.6' and did not authorize Proof C run 4. Operator general instruction of 2026-09-24T19:23:57-07:00, relayed to Stage by the Orchestrator as 'You have not yet marked ... if open questions or ambiguities - make good decisions and keep working ... stop planning and start implementing ... continue autonomously until truly finished' (relayed wording with elisions; Stage quotes nothing beyond the relay). It is the same directive recorded verbatim for version 1.4 and the same class of delegation recorded for version 1.5. The Orchestrator bounded it to one prospective correction of the Proof C clock rule reopened by Proof C run 3 (f23b9549). It is explicitly not approval of Proof C run 4 (which needs its own named operator authorization, section 3.5), not a waiver or re-label of any verdict, not a PE-FLOW-04 ruling, and not approval to claim or merge any shipment, edit any Ship surface or manifest, or relax P-001, P-002, P-009, P-011, P-014 or P-016. The operator may veto it; a veto is recorded as a further version and relabels nothing"
head_at_version_1_6: f23b9549
version_1_7_operator_approval: "2026-09-25T13:27:40-07:00 - explicit operator rulings, relayed verbatim by the Orchestrator: (1) 'approved to modify Ships model routing and updating the manifest checksum.' and (2) '3. Option A', answering proof-exit report OD-2 (9c83517d) as presented to the operator: record Proof D run 4 (36f65975, PE-1.4) as a known historical exception to PE-FLOW-04, treat Proof D run 5 (5976ff62, PE-1.5, PASS on the synthetic decided contract) as Proof D's admissible evidence, and read the row prospectively so that it counts as met from here on, with no verdict changed; ruling (3) 'Refresh the implementation matrix and re-present.' is a Stage work order recorded here and executed outside this charter. Limited to the PE-ACTIVATE-01 comparator rebaseline to 08787a4b and the recording of the PE-FLOW-04 ruling (section 3.6); explicitly not approval of any proof run, activation, harvest, plan, review epoch, ratification of the implementation matrix, or claim, retirement or re-charter of 187-S, and not a relaxation of P-001, P-002, P-004, P-009, P-011, P-014 or P-016"
head_at_version_1_7: 08787a4b
activation_baseline_commit: 08787a4b
activation_baseline_commit_version_1_4: 4acba14a
activation_baseline_commit_version_1_3: 5bcb00e5
parent_decision: docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md
governing_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
governing_decision_revision: 9
promoted_to: none
promoted_to_note: "No plan, queue item, shipment or review attempt is linked. The charter authorizes nothing by itself. Phase 1 proof entry follows section 6.1: Ship performs verification-only fixture execution in the one current worktree and Stage authors the findings. The first handoff is Proof A to Ship."
branch: chore/stage-176-s-workflow-defects
head_at_charter: 082df7b2
head_at_version_1_1: 2e3c98a1
frozen_diagnostic_record:
  plan: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
  plan_revision: 12
  plan_revision_commit: 0806b601
  verdict_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
  verdict_manifest_revision: 21
  terminal_attempt: 11
  terminal_attempt_artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-11.md
  terminal_attempt_commit: 246d8b73
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_charter: queued
shipment_claim_ready: false
overrides: none
policies: [P-001, P-002, P-003, P-004, P-005, P-010, P-011, P-012, P-013, P-016, P-017, P-020, P-021]
labels:
  - charter
  - acceptance-matrix
  - proof-entry
  - ship-lifecycle
  - governance-reset
---

# Lifecycle proof-entry charter (version 1.7)

## 1. Purpose

This charter is the contract that Phase 1 of the lifecycle recovery is
evaluated against. It exists because the plan-revise-review loop over the
Ship pre-task harness-generation lifecycle failed eleven consecutive times
without converging (see the parent decision,
`docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md`).
The parent decision records the operator's 2026-09-23 approval of **Option B**
(governance reset, proof-first rebaseline, release-unit split) combined with
the **proportionate Option D** containment scope.

The charter does three things and nothing else:

1. fixes the threat model and platform mandate the proofs must satisfy;
2. defines a bounded portfolio of seven executable proofs, and assigns each
   proof step to the role allowed to perform it;
3. fixes acceptance matrix **PE-1.7**, the only set of criteria a proof or a
   proof-phase artifact is judged against from version 1.7 onward (section 3
   explains how verdicts recorded under PE-1.1, PE-1.2, PE-1.3, PE-1.4,
   PE-1.5 and PE-1.6 carry forward, and which proofs still need a new run).

## 2. Authority and precedence

This charter is **subordinate** to every higher source it cites. It does not
amend, waive, reinterpret or override any of them:

1. `.github/instructions/constitution.instructions.md` (which states that it
   supersedes other development practices in this workspace);
2. `.github/policies/workflow-policies.md` (P-001 through P-021), including the
   P-010 role boundary;
3. the governing decision,
   `docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md`
   (revision 9), for portfolio architecture and sequence;
4. the parent decision, for the B+D scope choice.

If any matrix row conflicts with a higher source, the higher source governs,
the row is defective, and the defect is routed to the operator as a charter
change. It is never resolved by a proof author choosing the more convenient
reading.

## 3. Freeze and versioning

| Aspect | Rule |
|---|---|
| What is frozen | This charter and matrix PE-1.7, for **proof entry only** |
| What is not ratified | The implementation acceptance matrix. It is drafted from proof evidence and ratified by the operator **after** proof exit and **before** any new review epoch opens |
| How it changes | Only by an operator-approved version bump (1.7, 2.0, ...), recorded as a new charter version. Proof authors and proof executors cannot edit rows mid-proof |
| Current version | 1.7 (matrix PE-1.7), an explicit operator approval of 2026-09-25T13:27:40-07:00 (frontmatter `version_1_7_operator_approval`; authority and exact change recorded in section 3.6). It supersedes version 1.6 (`cd2ef261`), which changed the Proof C clock rule and time bound for run 4 onward only. Version 1.6 was a bounded delegated decision (frontmatter `version_1_6_operator_approval`; section 3.5). It superseded version 1.5 (`d31d7b42`), which changed the Proof E section 6.7 retained-text replacement set only. Version 1.5 was itself a bounded delegated decision (frontmatter `version_1_5_operator_approval`; section 3.4). It superseded version 1.4 (`52c985cb`), which changed the Ship index refresh in proofs, the `PE-ACTIVATE-01` setup-snapshot comparator and Proof C run 2 only. Version 1.4 superseded version 1.3 (`7f833cb8`), which changed Proof E terms and the `PE-ACTIVATE-01` comparator only. Version 1.3 superseded version 1.2 (`286aa4af`), which changed Proof D only. Version 1.2 superseded version 1.1 (`1ad7c03a`), and version 1.1 superseded version 1.0 (`2e3c98a1`) and corrected proof actor and timing only. See section 3.1 for the version 1.2 change, section 3.2 for the version 1.3 change, section 3.3 for the version 1.4 change, section 3.4 for the exact version 1.5 change, section 3.5 for the exact version 1.6 change and section 3.6 for the exact version 1.7 change |
| Change requests | A requirement discovered during a proof that is not a PE-1.7 row is recorded as a change request in that proof's evidence. It is not a proof-phase blocker |

### 3.1 Version 1.2 change record (Proof D only)

**Why.** Proof D ended `FAIL` under PE-1.1
(`docs/decisions/2026-09-23-read-budget-proof-d-spike.md`). Section 6.1 sends
a `FAIL` back to architecture or charter, and `PE-FLOW-04` allows a failed proof
to run again only under a new charter version. The reopened decisions are
settled in
`docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`.

**What changed. Only these three items are changed, and each is marked
"(PE-1.2)" where it appears:**

| Item | PE-1.1 | PE-1.2 |
|---|---|---|
| Section 6.6, Proof D | The question asks whether the admitted maximum fits "the read limits". The pass criterion requires `C(N_max)` to fit "the chosen file and byte limits", with frozen plan revision 12's `1..512` as a diagnostic input | Proof D run 2. The admitted membership is `1..48`, with `max_files=256` and the revision 12 read plan unchanged. The file-slot fit and its margin are **guaranteed** and exhaustively checked. The byte fit is **explicitly not guaranteed**, and the proof must show that byte exhaustion is a bounded `UNRESOLVED / 2` failure, never success. Every read-limit error at every read or recheck stage reduces to `UNRESOLVED / 2` |
| Row `PE-DATA-03` | `C(N) <= max_files` for every admitted `N`; exhaustion yields `UNRESOLVED` | Adds the admitted range `1..48`, the margin rule, the byte non-guarantee and per-stage exhaustion |
| Row `PE-SAFETY-04` | "The Proof D equation passes" | "Proof D run 2 passes under section 6.6 (PE-1.2)". The Proof G half is unchanged |

Sections 1 (item 3), 4.1, 6.2 (row D), 7 (heading note), 8 (item 1) and 10
(addendum) are updated only to refer to these items.

**What did not change.** The following are all unchanged: the threat model and
platform mandate (section 5), the execution rules (section 6.1), and Proofs A,
B, C, E, F and G, including their questions, bounds and pass/fail criteria. All
other matrix rows also keep their ID and text, as do the proof-exit rules
(section 8). The frozen diagnostic record (section 4.2) stays frozen, so plan
revision 12 is not edited. The public-contract change from 512 to 48 is recorded
in the decision above. It is not a correction of the plan.

**Carried-forward verdicts.** Proof A (`BLOCKED`) and Proof F (`PASS`) were
judged under PE-1.1 against rows that PE-1.2 leaves unchanged. Their verdicts
stand as recorded and are not re-run. Proof D run 1 stays **`FAIL`** under
PE-1.1. It is never re-labelled. Proof D run 2 is judged against PE-1.2. This
version bump does not mark any proof `PASS`.

**Change request, not a change (Proof C).** The read-limit reason values that
the decision reuses (`FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT`
as `UNRESOLVED` reasons) are recorded as a change request for Proof C's truth
table and schema parity. Proof C's question, bounds and rows are unchanged.

### 3.2 Version 1.3 change record (Proof E terms and PE-ACTIVATE-01 comparator only)

**Why.** Proof E was recorded `BLOCKED` under PE-1.2
(`docs/decisions/2026-09-24-ship-activation-proof-e-spike.md`, committed at
`a04e1e5a`) because two section 6.7 terms had more than one reading, and
because `PE-ACTIVATE-01` could no longer pass as written. Section 2 routes a
row that cannot be read consistently with a higher source to the operator as a
charter change. The operator ordered Stage to act. The readings below are the
ones the higher Ship recovery protocol dictates. Neither is a convenience
choice.

**What changed. Only these items are changed, and each is marked "(PE-1.3)"
where it appears:**

| Item | PE-1.2 | PE-1.3 |
|---|---|---|
| Section 6.7, term "checkpoint validate-and-resolve" | Undefined. Proof E recorded Reading V (selection and owner validation) and Reading S (status resolution before restore) | Reading V only. Before any cursor restore: one explicit, unique operator selection of a `ship`-owned checkpoint, then the owner and CheckpointV1 schema validation, then operator confirmation. It never means calling `backlogit_resolve_checkpoint` (template `{{OP_RESOLVE_CHECKPOINT_MCP}}`) before restore. Status resolution happens only after a confirmed successful resume, as template line 1038 and mirror line 202 both require |
| Section 6.7, term "retained text" | Undefined. Proof E recorded Reading R1 (text kept after the activation edits) and Reading R2 (all current text) | Reading R1 only. Retained text is the text of each Ship surface that remains after the planned activation edits (`PE-ACTIVATE-02`). Current text that those edits replace is not retained text. A mismatch between the current text and the planned post-activation text is an expected input, not by itself a `FAIL` |
| Row `PE-ACTIVATE-01`, pass criterion | Byte-identical to `082df7b2` | Raw LF Git tracked blobs at the proof-exit commit are identical to the raw Git tracked blobs at the operator-approved snapshot `5bcb00e5` for the same three paths, with no uncommitted change to those paths |

Sections 1 (item 3), 3 (table), 4.1, 7 (heading note), 8 (item 1) and 10
(addendum and cross-references) are updated only to refer to these items. The
frontmatter records the version, the approval and the baseline commit.

**Why `082df7b2` is no longer the comparator.** Commit `5bcb00e5` ("chore:
preserve approved workspace configuration and memory"), a descendant of
`082df7b2` and an ancestor of `a04e1e5a`, was relayed to Stage as
operator-approved. Stage validated its scope for the three paths read-only with
`git diff 082df7b2 5bcb00e5 --` and raw-blob SHA-256 values from
`git cat-file blob` (every blob below contains zero CRLF sequences):

| Path | Blob at `082df7b2` | Blob at `5bcb00e5` (= `a04e1e5a`) | Raw-blob SHA-256 at `5bcb00e5` | Diff `082df7b2..5bcb00e5` |
|---|---|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | `a3407080665c874e6db742a467bcd79ce97d2666` | `a3407080665c874e6db742a467bcd79ce97d2666` | `7f2ddef1ada977fbb0d06a3f83587b1151acde297148a0847e1b0145d5595db2` | None |
| `.github/agents/_ship.agent.md` | `bd2225eb4ba4d4a89fcf1aa2b9a5e6be9a7e2247` | `5f397d0f1f2c8ce8dcded360a73a2a0d120ffc3a` | `83f9e73520f5d88708738f6bdbfc849377e9d1705366120cb49c1dc6b72ff81c` | Frontmatter lines 8-10 only: `reasoning_effort` high to xhigh, `model_provider` anthropic to openai, `model_family` claude-sonnet-5 to gpt-6-luna. Three lines replace three lines, so no body line moves |
| `.autoharness/harness-manifest.yaml` | `5ceea6c521b9517f81defcb493150d51c27f9ad1` | `17ae787d492fe06788ce21ae6fab29a26b3c4139` | `10c0fa89e08c325c099d0332e35b01008e85a26d3ffc76cc765e8cff052addb8` | Four `checksum:` values only, at lines 110, 120, 125 and 130 (entries for `.autoharness/config.yaml`, `.github/agents/_stage.agent.md`, `.github/agents/_ship.agent.md` and `.github/agents/_orchestrator.agent.md`). The mirror entry's new value equals the mirror's raw-blob SHA-256 above |

No body text of any of the three surfaces changed, so the baseline change is
not an activation and hides none. Every section 6.7 anchor line is unchanged
at `5bcb00e5`.

**Excluded from the row.** `5bcb00e5` also changes `.autoharness/config.yaml`
(25 insertions, 8 deletions), `.github/agents/_stage.agent.md`,
`.github/agents/_orchestrator.agent.md`, `.github/copilot/settings.local.json`,
two backlog checkpoint files and nine memory files. None of these is one of
the three `PE-ACTIVATE-01` paths. They are recorded here, not rebaselined, and
no row is added for them. The config change is covered by this row only
through its checksum value inside the manifest blob.

**What did not change.** The threat model and platform mandate (section 5),
the execution rules (section 6.1), Proofs A, B, C, D, F and G (sections 6.3 to
6.6, 6.8 and 6.9), including their questions, actors, bounds and pass/fail
criteria, are all unchanged. Proof E's question, actors, anchors, time and file
bound, list of mis-orderings and boundary are also unchanged. Every other
matrix row keeps its ID and text, including `PE-FLOW-03`, `PE-SCOPE-01` (its
diagnostic-record baseline stays `082df7b2`) and `PE-ACTIVATE-02`. So do the
proof-exit rules (section 8), the frozen diagnostic record (section 4.2) and
section 3.1. Plan revision 12 and the review record are not edited. No Ship
surface, manifest, config, source, backlog item or shipment is changed by this
version.

**Carried-forward verdicts.** Proof A (`BLOCKED`, PE-1.1), Proof D run 1
(`FAIL`, PE-1.1), Proof D run 2 (`PASS`, synthetic contract only, PE-1.2) and
Proof F (`PASS`, PE-1.1) were judged against rows and sections that PE-1.3
leaves unchanged. Their verdicts stand as recorded and are not re-run. Proofs
B, C and G have not been run. Proof E stays **`BLOCKED`** under PE-1.2. It is
never re-labelled, and its illustrative execution stays inadmissible. The
readings now fixed would not have made that execution admissible, because it
failed section 6.1 scratch and `PE-EVIDENCE-01` evidence rules that PE-1.3
does not change. Proof E leaves `BLOCKED` only through a fresh, admissible
execution judged against PE-1.3 (section 10 addendum). This version bump does
not mark any proof `PASS`.

**Still open (not decided here).** Whether the session-state fixture write is a
`PE-AUTH-01` violation, and whether an inadmissible run consumes a proof's time
bound (also open for Proof A), stay open for the operator.

### 3.3 Version 1.4 change record (Ship index refresh, PE-ACTIVATE-01 setup snapshot and Proof C run 2 only)

**Why.** Under PE-1.3, three things could no longer be done as written:

1. **Index refresh.** Ship Step 0.1 in `.github/agents/_ship.agent.md` (line
   126 at `4acba14a`) requires `backlogit_sync_index`, or the registered
   `backlogit sync` CLI fallback, before any semantic shipment read, task
   lookup or queue operation. P-001 is evaluated from those reads. But PE-1.3
   section 6.1 and row `PE-AUTH-01` let Ship write only its scratch
   directory, and section 4.3 forbids any backlog edit. So no Ship invocation
   could follow both Step 0.1 and the charter. Proof A invocation 3 halted on
   exactly this conflict (`docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md`).
   The operator-directed setup commit `4acba14a` resolved it on the Ship side
   by adding the cache refresh, and nothing else, to the Ship Backlog Allowed
   row.
2. **Comparator.** The operator-directed setup commits `d20820ec` and
   `4acba14a` changed all three `PE-ACTIVATE-01` paths. No proof-exit commit
   can now match `5bcb00e5`.
3. **Proof C.** Proof C run 1 is `FAIL` under PE-1.3
   (`docs/decisions/2026-09-24-surface-taxonomy-proof-c-spike.md`, `9d0ed834`).
   Its recorded route is a PE-1.4 change to section 6.5 under `PE-FLOW-04`.

The operator approval is recorded in frontmatter
`version_1_4_operator_approval`. It covers this bounded correction only. It
does not approve claiming, merging or changing any shipment. It does not relax
P-001, P-002, P-009, P-011, P-014 or P-016, and it does not change any other
actor's authority.

**What changed. Only these items are changed, and each is marked "(PE-1.4)"
where it appears:**

| Item | PE-1.3 | PE-1.4 |
|---|---|---|
| Section 4.3, backlog bullet | Any backlog, carrier, shipment or stash edit is prohibited | The prohibition is unchanged. It states that the section 6.1 index refresh is a tool-managed cache refresh: it is not such an edit and not a new release unit |
| Section 6.1, scratch bullet | Ship writes only inside the scratch directory | Ship's fixture writes go only inside the scratch directory. Its only other write is the separate index refresh. Every Ship write stays inside the current working directory |
| Section 6.1, new bullet "Backlog index refresh" | None | Ship alone runs its Step 0.1 refresh before any semantic backlog read in every proof invocation. The refresh fails closed to `BLOCKED` when both transports fail or cannot be verified. Reads use bounded projections |
| Section 6.1, per-invocation gates and evidence handoff | P-001 is evaluated with no refresh rule. The safety statement covers scratch only | P-001 is evaluated only from reads made after a successful refresh. Ship checks the three `PE-ACTIVATE-01` paths before the first write. The handoff records the refresh and the projections |
| Section 6.5, Proof C | Run 1 contract | Run 2 contract: a governing reason set held apart from the fixture's enum; the Stage candidate as a proposal; raw or hashed output for every execution; a real-surface render control that uses the top-level `variables_used` |
| Rows `PE-AUTH-01`, `PE-AUTH-02`, `PE-EVIDENCE-01` | Ship writes scratch only. The gate record has no refresh | Fixture writes go to scratch, plus the separate cache refresh. The gate record includes the refresh |
| Rows `PE-DATA-01`, `PE-DATA-02` | "Every code" is not tied to any reason set | Measured against the section 6.5 governing reason set and the Stage candidate |
| Row `PE-ACTIVATE-01`, comparator | Operator-approved snapshot `5bcb00e5` | Operator-authorized setup snapshot `4acba14a` |

The title, the frontmatter, sections 1 (item 3), 3 (table), 4.1, 6.2 (row C),
7 (heading note), 8 (item 1) and 10 (addendum and cross-references) change
only to refer to these items. The frontmatter now also records commit `7f833cb8` for version
1.3, which the version 1.3 record left open. That fills in the record. It is
not a re-label.

**Setup snapshot `4acba14a`.** Stage checked the three paths read-only. It used
`git rev-parse <commit>:<path>` to get each blob ID. It hashed the raw blob
bytes from `git cat-file blob`, captured in binary by a Python subprocess
(never PowerShell text). Every blob below contains zero CRLF sequences:

| Path | Blob at `5bcb00e5` | Blob at `d20820ec` | Blob at `4acba14a` | Raw-blob SHA-256 at `4acba14a` | Change `5bcb00e5..4acba14a` |
|---|---|---|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | `a3407080665c874e6db742a467bcd79ce97d2666` | `e06b2b4ba1b94b6f9a2910594c419ff9d0e024d9` | `4ccd7fdc2d134de485487acd75bfbc105d6f40ee` | `a2451b355d27203db51515c9f72289a59a2e11af06d2910fd934fef489f4cbeb` | Role Boundary table only: the Backlog, Source code and Build Allowed cells (lines 38, 39 and 41 at `4acba14a`) and a new "Temporary verification fixtures" paragraph (lines 45-46). Net gain of two lines |
| `.github/agents/_ship.agent.md` | `5f397d0f1f2c8ce8dcded360a73a2a0d120ffc3a` | `ad8b97a3cd78fb9315cf784fbd069f2013f4e2a4` | `e22916b62f36f1c25c421882a05f4049f1862c02` | `250fc87a4275a5b7c1a5a143b6c2d7d9b97c50db1b465a84157c3c891c4c8a38` | The same Role Boundary change (lines 47, 48, 50 and 55-56 at `4acba14a`). Net gain of two lines |
| `.autoharness/harness-manifest.yaml` | `17ae787d492fe06788ce21ae6fab29a26b3c4139` | `0654257abaa672191ec805e7ab223090bce6286e` | `251f46e8c95703ed65e421210d3b08682d79d8bc` | `e3ddbac3e4648c06442de42e2f0ecc05c5dbee645cdb9e58760b5bdd010425d0` | One `checksum:` value, at line 125, in the `.github/agents/_ship.agent.md` entry. The new value equals the mirror's raw-blob SHA-256 above |

**Why this setup is not the lifecycle activation.** The two setup commits are
P-010 role-permission setup, made so that proofs can run under the Ship Role
Boundary. `d20820ec` permits disposable Git-ignored verification scripts, and
`4acba14a` permits the Step 0.1 cache refresh. Both also refresh the mirror
checksum. They change no Pre-Flight, Harness Generation, Build Ready Queue,
task-loop or Crash-Resumption text. The count of `harness-architect`
references is unchanged: six in the template and none in the mirror, at both
`082df7b2` and `4acba14a`. They do not move, prepare or partly perform the
per-task harness placement, which remains the one future task and commit of
`PE-ACTIVATE-02`. Every section 6.7 anchor keeps its text. At `4acba14a`,
each anchor sits two lines lower in both files. For example, template Step 2
is at line 328 and template resolution at line 1040; mirror Crash-Resumption
is at line 172, resolution at line 204 and Claim at line 359. Section 6.7
still cites `082df7b2` and is unchanged. The version 1.3 baseline record for
`5bcb00e5` (section 3.2) stays as written.

**Excluded from the row.** `d20820ec` also adds `.proof-scratch/` to
`.gitignore` (line 10). That path is not one of the three `PE-ACTIVATE-01`
paths. It is recorded here, not rebaselined, and no row is added for it.

**Proof-exit rule.** At proof exit, all three paths must have the `4acba14a`
blobs above, with no uncommitted change to any of them. No activation, full or
partial, happens during proofs. Before its first write, every Ship proof
invocation checks the three blob IDs at `HEAD` and runs
`git status --porcelain` for the three paths. If a blob differs, or any of the
three paths has an uncommitted change, Ship stops before writing and returns to
the operator (`BLOCKED`).

**What did not change.** The following are unchanged: the threat model and
platform mandate (section 5), and Proofs A, B, D, E, F and G (sections 6.3,
6.4 and 6.6 to 6.9) with their questions, actors, bounds and pass and fail
criteria. That includes the section 6.9 rule that a Linux fixture root outside
the current working directory needs operator approval. This version grants no
such approval. Also unchanged are every other matrix row, the proof-exit rules
(section 8, apart from the item 1 reference), the frozen diagnostic record
(section 4.2) and sections 3.1 and 3.2. This version adds no threat-model claim
and no standalone scheduler or tool. It changes no Ship surface, manifest,
config, source, backlog item, shipment or stash entry.

**Carried-forward verdicts and required runs.** Every recorded verdict stands
as recorded, under the version it was recorded against, and none is
re-labelled. Stage audited the findings artifacts read-only for Step 0.1
refresh evidence in each Ship invocation. Under PE-1.4, a P-001 result is
admissible only when it comes from reads made after a successful refresh in
the same invocation (section 6.1). A missing refresh cannot be supplied
afterwards. So a historical `PASS` without recorded refresh evidence stays
`PASS` in the record, but it does not satisfy PE-1.4 proof exit (`PE-AUTH-02`).
This is not a finding against its results, and no proof `PASS` confers claim
authority (`PE-ACTIVATE-03`).

| Proof | Recorded verdicts (unchanged) | Ship Step 0.1 refresh evidence (read-only audit) | Status under PE-1.4 | Required before proof exit |
|---|---|---|---|---|
| A | `BLOCKED` (PE-1.1, `231a2e5a`) | None. Invocation 3 halted before any scratch write because Ship took the refresh to be a forbidden mutation | `BLOCKED`, unchanged | A fresh, admissible PE-1.4 execution to leave `BLOCKED` |
| B | `PASS` (PE-1.3, `83525c62`; disposable fixture only) | None. Ship reported "no index sync" | Historical `PASS`. Does not satisfy PE-1.4 proof exit | A new admissible PE-1.4 run under section 6.4 (unchanged) |
| C | Run 1 `FAIL` (PE-1.3, `9d0ed834`) | None. Ship reported no index sync | `FAIL`, unchanged | Run 2 under section 6.5 (PE-1.4) |
| D | Run 1 `FAIL` (PE-1.1, `b3fca43a`); run 2 `PASS` (PE-1.2, `a0079ac0`; synthetic contract only) | None recorded. P-001 came from read-only active lists, and raw stdout and stderr were not included | Historical run 2 `PASS`. Does not satisfy PE-1.4 proof exit | A new admissible PE-1.4 run under section 6.6 (unchanged), with raw or hashed output (`PE-EVIDENCE-01`) |
| E | Run 1 `BLOCKED` (PE-1.2, `a04e1e5a`); run 2 `BLOCKED` (PE-1.3, `6ee65c4a`, time bound corrected at `43f870eb`); run 3 `BLOCKED` (PE-1.3, `383ae6be`) | None recorded | `BLOCKED`, unchanged | A fresh, admissible PE-1.4 execution under section 6.7 (unchanged), checked against `PE-ACTIVATE-01` (PE-1.4) |
| F | `PASS` (PE-1.1, `3df0509f`) | None recorded. Stage's own MCP version probe is not a Ship refresh, and P-001 came from read-only CLI lists | Historical `PASS`. Does not satisfy PE-1.4 proof exit | A new admissible PE-1.4 run under section 6.8 (unchanged) |
| G | No run. Two Ship halts happened before any write, with no verdict and no findings artifact | Not applicable | Not run | A Windows run under PE-1.4. Linux stays `PENDING` unless an actual Linux-native host is available with its fixture root inside the current working directory (section 6.9) |

Each new run gets its own section 6.2 time and file bound and a new scratch
directory. Budgets do not pool with earlier runs. The 420-minute total in
section 6.2 counts one admissible run per proof.

### 3.4 Version 1.5 change record (Proof E section 6.7 retained-text replacement set only)

**Why.** Proof E run 4 was recorded `BLOCKED` under PE-1.4
(`docs/decisions/2026-09-24-ship-activation-proof-e-run4-spike.md`, committed
at `945a224e`). The execution was admissible, and the fixture met the section
6.7 pass criterion over the text it modeled. But Stage's retained-text audit
found two template passages that the section 6.7 planned replacements did
not remove and the fixture did not model:

* **Session start**: template lines 1002-1004 at `082df7b2`, which are lines
  1004-1006 at `4acba14a` and at `945a224e`. It scans `{{DOCS_MEMORY}}/`
  for the most recent memory or checkpoint file, restores context ("completed
  items, branch context, PR status, and prior build decisions"), and only
  then runs the recovery state machine.
* **`### Resumption Protocol`**: template lines 1101-1105 at `082df7b2`,
  which are lines 1103-1107 at `4acba14a` and at `945a224e`. On session
  start, it restores context from a `{{DOCS_MEMORY}}/` checkpoint with status
  `context-overflow` and resumes from the recorded next step. There is no
  selection, validation or confirmation.

Stage checked that each span is byte-identical at both commits. Neither span
has a counterpart in the installed mirror. The verdict depended on a reading
the charter did not settle. Under the reading scoped to the CheckpointV1
cursor, the run passes (`PASS`). Under the unscoped reading, it fails
(`FAIL`). Section 2 routes such a fork to the operator as a charter change.
Run 4 recorded two options. Option A adds both passages to the planned
replacements. Option B scopes "cursor restore" to the CheckpointV1 cursor.

**Authority (bounded delegation, recorded as it happened).** The operator did
not literally select Option A. The authority is the operator's general
instruction of 2026-09-24T14:58:27-07:00, given after the previous session's
failed proofs. The Orchestrator relayed it to Stage as "If ... open questions
or ambiguities—make good decisions and keep working; if error resolve or
alternative; complete remaining steps". Stage did not see the original and
quotes nothing beyond the relay. Under that instruction, the Orchestrator
publicly selected Option A and bounded it to this section 6.7 scope. The
frontmatter records this as `version_1_5_operator_approval`. It follows the
version 1.4 precedent: a broad operator directive, bounded by the
Orchestrator and recorded without inventing a quote.

Stage judged this delegation sufficient under section 3, for four reasons:

1. Option A is the reading the higher Ship recovery protocol dictates. It is
   not a convenience choice (section 2). In both Ship surfaces, the retained
   recovery protocol states "There is no automatic resume under any
   condition". That is template line 1034 and mirror line 198 at `4acba14a`.
   The protocol also requires, before any restore:
   * an unfiltered enumeration and anomaly scan;
   * an explicit, unique operator selection;
   * an owner and CheckpointV1 schema check;
   * operator confirmation.

   The `context-overflow` Resumption Protocol resumes with none of these.
   The Session start sentences restore context before the enumeration.
   Option B would keep a template path that the same template's recovery
   protocol forbids.
2. Option A is the stricter, fail-closed reading. It makes no verdict `PASS`.
   Run 4 stays `BLOCKED`, and only a fresh run can change Proof E's status.
3. It matches frozen plan revision 12 line 229: "Checkpoint handling is
   replacement, not additive correction. Remove the template's current early
   sentence that restores memory context before checkpoint validation ...
   Tests prove the prior cursor-first text/path is absent and no later bypass
   exists." The plan is a frozen diagnostic input (section 4.2). The plan
   agrees with this scope, but it does not set it and is not edited.
4. The change is bounded. It adds two spans to one list, and it states the
   contract those spans must meet after activation. It changes no row, no
   pass criterion and no actor's authority.

This version does not approve claiming, merging or changing any shipment. It
does not approve editing any Ship surface or the manifest. It does not relax
P-001, P-002, P-004, P-011, P-016 or any other safety gate. The operator may
veto it before the Proof E run 5 handoff. A veto leaves Proof E `BLOCKED`,
and the fork goes back to the operator for a new version.

**What changed. Only these items are changed, and each is marked "(PE-1.5)"
where it appears:**

| Item | PE-1.4 | PE-1.5 |
|---|---|---|
| Section 6.7, term "retained text", planned replacements | Template Step 2 and Step 3, replaced by the per-task T1-T3 step inside Step 4. Mirror: T1-T3 inserted inside Step 2 | The same, plus two template replacements: the Session start span and the `### Resumption Protocol` span (line numbers above). Neither span is retained text. The mirror's planned insertion and its retained recovery protocol are unchanged, because the mirror has no matching passage |
| Section 6.7, new bullet "Post-activation restore contract" | None | The contract that the replacement text for both spans, and every retained Ship text, must meet after activation (section 6.7) |
| Section 6.7, new bullet "Scope of the restore mis-ordering" | None stated | The mis-ordering "cursor restore before checkpoint validate-and-resolve" covers memory-context, phase and next-action restore from any source, including a docs-memory or `context-overflow` checkpoint. The pass criterion's text is unchanged |

Sections 1 (item 3), 3 (table), 4.1, 7 (heading note), 8 (item 1) and 10
(addendum and cross-references) are updated only to refer to these items. The
frontmatter records the version, the approval and the head commit. It also
records commit `52c985cb` for version 1.4, which the version 1.4 record left
open. That fills in the record. It is not a re-label.

**What did not change.** All of the following are unchanged:

* Every matrix row's ID, requirement, normative source, pass criterion,
  evidence, severity and deferral. That includes `PE-FLOW-03` and
  `PE-ACTIVATE-02`, and `PE-ACTIVATE-02` needs no pointer change, because
  section 6.7 already names it as the task that applies the planned
  replacements.
* The PE-1.3 term "checkpoint validate-and-resolve". Status resolution still
  never happens before a confirmed successful resume.
* The retained Crash-Resumption recovery order in both surfaces.
* The PE-1.4 section 6.1 rules, including Ship's Step 0.1 index refresh.
* The section 6.5 Stage candidate for Proof C.
* The `PE-ACTIVATE-01` comparator `4acba14a` and its blob IDs.
* The threat model (section 5).
* Proofs A, B, C, D, F and G, and every other part of Proof E: its question,
  actors, anchors, bounds, pass list, fail clause and boundary.
* The frozen diagnostic record (section 4.2) and sections 3.1 to 3.3.

No Ship surface, manifest, config, source, backlog item, shipment or stash
entry is changed.

**Carried-forward verdicts and required runs.** Every recorded verdict stands
as recorded, under the version it was recorded against, and none is
re-labelled:

* Proof E runs 1 to 3 (`a04e1e5a`, `6ee65c4a`, `383ae6be`) stay `BLOCKED`.
* Proof E run 4 (`945a224e`) stays `BLOCKED` under PE-1.4. PE-1.5 does not
  turn run 4's modeled result into a `PASS`.
* The runs recorded under PE-1.4 for the other proofs keep the verdicts their
  findings record:
  * Proof A run 5: `PASS`, synthetic fixture (`99e9ff5f`; addendum
    `4d132bf9`).
  * Proof B run 2: `BLOCKED` (`669ee9f6`). Proof B run 3: `PASS`, disposable
    stub and predicate (`6920cb7c`).
  * Proof C run 2: `BLOCKED` (`309ab0e2`).
  * Proof D run 3: `FAIL` (`8179feb1`). Proof D run 4: `PASS`, synthetic
    contract (`36f65975`).
  * Proof F run 2: `PASS` (`8b39a08b`).
  * Proof G: `PENDING-LINUX` (`6daf80bb`; addendum `06f8930b`).

  The rows and sections those proofs are judged against are the same in
  PE-1.4 and PE-1.5. So each of these runs keeps, under PE-1.5, the standing
  for proof exit it had under PE-1.4. Where the section 3.3 table requires a
  new PE-1.4 run of a proof other than E, a run recorded under PE-1.4, or one
  recorded later under PE-1.5, meets that requirement. This version requires
  no re-run of any proof other than E.
* Proof E leaves `BLOCKED` only through a fresh, admissible run 5 under
  section 6.7 (PE-1.5) and section 6.1 (section 10 addendum). Run 5 gets its
  own section 6.2 budget.

### 3.5 Version 1.6 change record (Proof C clock rule and time bound, run 4 onward only)

**Why.** Proof C run 3 was recorded `FAIL` under PE-1.5
(`docs/decisions/2026-09-24-surface-taxonomy-proof-c-run3-spike.md`,
`f23b9549`). The reason was the time bound. Stage charged its 18:07:19 design
work, done before the 18:21:44 operator authorization, to the 75-minute bound,
because section 6.1 says the bound covers "its Stage analysis and its Ship
execution together". The bound ran out at 19:22:19, during Stage
adjudication. Run 3 reopened one decision: when the Proof C clock starts,
whether design done before authorization counts, and whether 75 minutes is
enough. Section 6.1 routes a `FAIL` back to the charter, and `PE-FLOW-04`
allows another attempt only under a new charter version.

**Authority.** This is a bounded delegated decision, not a literal operator
approval. The operator did not say "approve charter version 1.6" and did not
authorize Proof C run 4. The operator's standing instruction of
2026-09-24T19:23:57-07:00, relayed by the Orchestrator, to make good
decisions and keep working is the same directive recorded verbatim for
version 1.4, and the same class of delegation recorded for version 1.5. The
Orchestrator bounded it to this one prospective correction (frontmatter
`version_1_6_operator_approval`). The operator may veto it. A veto is
recorded as a further version and relabels nothing.

**What changes (Proof C, run 4 onward only).**

1. **Clock start (T0).** T0 is the earliest of: the first Stage work on that
   run's design (truth table, schema branch derivation, freeze inspection,
   or reading earlier runs' artifacts in order to design this run), the
   first Ship work on that run, and the operator authorization of that run.
   Design done before authorization **counts**. Stage records T0 with a
   `Get-Date` read when that work starts. If no clock read exists, T0 is the
   earliest timestamp in any record (commit, relay or artifact) of work on
   that run.
2. **Clock end (T1).** T1 is Stage's `Get-Date` read taken when it writes the
   verdict line of the run's findings artifact, before that artifact is
   committed.
3. **No pausing and no reset.** The clock is continuous wall-clock time from
   T0 to T1. Operator waits, handoff delays, tool outages and session changes
   stay on the clock. Nothing restarts the clock within a run.
4. **Bound.** T1 minus T0 must be at most **120 minutes**. Over 120 minutes
   is `FAIL` (section 6.1). The number comes from run 3's measured stages,
   not from a reset. From 18:07:19 to the start of adjudication at 19:21:11
   took 73 m 52 s: design and authorization took about 14 m, the handoff up
   to Ship authoring about 28 m, Ship authoring about 29 m, and execution
   about 1 m. Run 3's adjudication was not finished, and a full one must
   re-hash the frozen pair and re-derive the section 6.5 conditions (about
   15 to 25 m). So the measured need is about 90 to 100 minutes. 120 minutes
   leaves a small margin and matches the two-hour task ceiling. It is not
   more generous than that.
5. **Stage marks.** The findings record T0, the authorization, FREEZE-OK,
   the start and end of Ship execution, the start of adjudication and T1.
   These are evidence only. They are not separate budgets.
6. **No carry-over.** Run 4's budget does not pool with runs 1 to 3 or with
   any Proof D run. Run 4 uses a new scratch directory and a fresh two-file
   bound. It may use run 3's frozen pair as an input only if it is re-read
   and re-hashed within run 4's clock. No output from runs 1 to 3 is run 4
   evidence.

**What does not change.** Every matrix row and pass criterion. The section
6.5 question, candidate, pass list, fail clause and boundary. The section 6.1
execution rules for every proof other than C, and Proof C's rules other than
the clock and bound. The time bounds of Proofs A, B, D, E, F and G. Sections
3.1 to 3.4 and the frozen diagnostic record. No P0 or P1 row is weakened, and
no Ship surface, manifest, config, source, backlog item, shipment or stash
entry is changed.

**Carried-forward verdicts.** Every verdict stands as recorded, under the
version it was recorded against, and none is re-labelled or waived:

* Proof C run 1: `FAIL` (PE-1.3, `9d0ed834`). Run 2: `BLOCKED` (PE-1.4,
  `309ab0e2`). Run 3: `FAIL` (PE-1.5, `f23b9549`). Run 3's single execution
  (exit 0, no fixture failure) stays unassessed evidence, not a `PASS`. Its
  render-parity `false` result stays an operator follow-up, not a Proof C
  condition.
* Proof D run 5: `PASS`, synthetic contract (PE-1.5, `5976ff62`). It is Proof
  D's effective evidence, and it met `PE-FLOW-04`: it re-ran run 3's failed
  question under a newer version.
* Every other verdict listed in section 3.4 stands.

**`PE-FLOW-04` and Proof D run 4.** This version does not change the row. Run
4 (`36f65975`, PE-1.4) re-asked a failed question without a version bump.
That breach is on the record and stays there. The row's pass criterion
depends on what exists in the record, so Stage does not declare
`PE-FLOW-04` met. Reading the row prospectively (run 4 listed as a recorded
historical exception, run 5 as the admissible evidence) would need an
explicit operator ruling. This version does not make that ruling and does not
reword the row.

**Proof C run 4 needs its own authorization.** Version 1.6 authorizes no run.
Run 3's findings say any later run needs a new operator authorization, so
Proof C run 4 may start only after an operator authorization that names
"Proof C run 4 under PE-1.6". Stage design for run 4 done before that
authorization is on run 4's clock (item 1 above). Run 4 under PE-1.6 would
meet `PE-FLOW-04`, since run 3's `FAIL` is followed by this version bump.

### 3.6 Version 1.7 change record (PE-ACTIVATE-01 comparator rebaseline and PE-FLOW-04 ruling only)

**Why.** Two things could no longer stay as written under PE-1.6:

1. **Comparator.** The operator commit `08787a4b` ("chore: preserve
   operator-approved model routing and refresh manifest checksums",
   2026-09-25T13:41:18-07:00) changed two of the three `PE-ACTIVATE-01`
   paths. No proof-exit commit can now match `4acba14a`. This is the same
   situation that version 1.3 settled for `5bcb00e5` (section 3.2) and
   version 1.4 settled for `4acba14a` (section 3.3).
2. **`PE-FLOW-04`.** The proof-exit report
   (`docs/decisions/2026-09-24-lifecycle-proof-exit-spike.md`, `9c83517d`)
   recorded `PE-FLOW-04` as `UNSATISFIED`, because Proof D run 4
   (`36f65975`) re-asked run 3's failed question under the same version,
   PE-1.4. It routed the row to the operator as OD-2. Proof D run 5
   (`5976ff62`) and section 3.5 both kept the row unmet as written, pending
   an explicit operator ruling. The operator has now ruled.

**Authority (explicit operator rulings, quoted verbatim).** At
2026-09-25T13:27:40-07:00 the operator gave three rulings, relayed verbatim
to Stage by the Orchestrator:

1. "approved to modify Ships model routing and updating the manifest checksum."
2. "3. Option A"
3. "Refresh the implementation matrix and re-present."

Ruling 2 answers OD-2 of the proof-exit report. Option A, as it was
presented to the operator, is: record Proof D run 4 (`36f65975`, PE-1.4) as
a known historical exception to `PE-FLOW-04`, treat Proof D run 5
(`5976ff62`, PE-1.5, `PASS` on the synthetic decided contract) as Proof D's
admissible evidence, and read the row prospectively, so that it counts as
met from here on. Option A changes no verdict. Ruling 3 is a Stage work
order. It changes nothing in this charter and is carried out in a separate
Stage artifact.

Unlike versions 1.4 to 1.6, this version is not a bounded delegation.
Rulings 1 and 2 are the operator's own words on the exact subject of each
item. Ruling 1 approves the Ship routing change and the manifest checksum
refresh that `08787a4b` carries. The same commit also carries the
`.autoharness/config.yaml` and `.github/agents/_orchestrator.agent.md`
routing edits. Those are the operator's own working-tree edits, disclosed
in the Proof C run 4 findings (`4c6e2701`) together with the operator's
statement of 2026-09-24T22:24:25-07:00: "I manually made the edits, which
conveys implicit operator approval". Stage records this and does not widen
either approval. The frontmatter records the rulings as
`version_1_7_operator_approval`.

This version does not approve any proof run, activation, harvest, plan,
review epoch or ratification of the implementation matrix. It does not
approve claiming, retiring, re-chartering or changing `187-S` or any other
shipment. It does not relax P-001, P-002, P-004, P-009, P-011, P-014 or
P-016. The operator may revise it by a further version, and a revision
relabels nothing.

**What changed. Only these items are changed, and each is marked "(PE-1.7)"
where it appears:**

| Item | PE-1.6 | PE-1.7 |
|---|---|---|
| Row `PE-ACTIVATE-01`, comparator | Operator-authorized setup snapshot `4acba14a` (section 3.3) | Operator-approved snapshot `08787a4b` and its blob IDs (below) |
| Section 6.1, per-invocation gates, blob check before the first write | The section 3.3 blob IDs (`4acba14a`) | The section 3.6 blob IDs (`08787a4b`). Only the reference follows the comparator. The check itself is unchanged |
| Row `PE-FLOW-04`, how it is evaluated | Over the whole record. The Proof D run 4 breach makes it unmet as written (section 3.5) | The row text is unchanged. A "(PE-1.7) Operator ruling on `PE-FLOW-04`" note under the section 7.4 table records the prospective reading, with Proof D run 4 as the single recorded historical exception |
| Section 8 item 1, how Proof D is reported | By its PE-1.4 run verdict | By run 5 (PE-1.5, `5976ff62`), its admissible evidence. Run 4 is listed as history and as the recorded exception |

The title, the frontmatter, sections 1 (item 3), 3 (table), 4.1, 7 (heading
and heading note), 8 (item 1) and 10 (addendum and cross-references) change
only to refer to these items. The frontmatter now also records commit
`cd2ef261` for version 1.6, which the version 1.6 record left open. That
fills in the record. It is not a re-label.

**Operator-approved snapshot `08787a4b`.** Stage checked the three paths
read-only:

* **Ancestry.** `08787a4b` is a descendant of `4acba14a` (`git merge-base
  --is-ancestor` exit 0) and is `HEAD` when version 1.7 is written.
* **Other commits.** `git log --oneline 4acba14a..08787a4b --` over the
  three paths returns `08787a4b` only. The range holds 20 commits. The
  other 19 each change exactly one file under `docs/decisions/`. Among
  them, `cd2ef261` changes only this charter, and `4c6e2701` changes only
  `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run4-spike.md`.
* **Diff.** `git diff 4acba14a 08787a4b --` over the three paths changes two
  files, with 9 insertions and 9 deletions. The template has no change.
* **Blobs.** Stage used `git rev-parse <commit>:<path>` for each blob ID. It
  hashed the raw blob bytes from `git cat-file blob`, captured in binary by
  a Python subprocess (never PowerShell text). Every blob below contains
  zero CRLF sequences at both commits:

| Path | Blob at `4acba14a` | Blob at `08787a4b` (= `HEAD`) | Raw-blob SHA-256 at `08787a4b` | Change `4acba14a..08787a4b` |
|---|---|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | `4ccd7fdc2d134de485487acd75bfbc105d6f40ee` | `4ccd7fdc2d134de485487acd75bfbc105d6f40ee` | `a2451b355d27203db51515c9f72289a59a2e11af06d2910fd934fef489f4cbeb` | None (106,843 bytes, 1,136 lines, at both commits) |
| `.github/agents/_ship.agent.md` | `e22916b62f36f1c25c421882a05f4049f1862c02` | `66933efaf085e7acff0db47f0bdc452a4fe58830` | `fd5a45a6c93e592eaf894228151416fdf35b527f79ee7bec6e11fa03f258b261` | Frontmatter lines 8-10 only: `reasoning_effort` xhigh to high, `model_provider` openai to anthropic, `model_family` gpt-6-luna to claude-opus-5.5. Three lines replace three lines, so no line moves (842 lines at both commits; 78,902 to 78,909 bytes). The body, from line 13 after the closing frontmatter line 12, is byte-identical |
| `.autoharness/harness-manifest.yaml` | `251f46e8c95703ed65e421210d3b08682d79d8bc` | `e4274043e66a104ca8cf9f43e0d4e939847ac30e` | `1bef348082817e9dd2706484ffa3052bdef83059490e613d590d1e94d974255e` | Three `checksum:` values and their three `note:` values only, at lines 110-111 (`.autoharness/config.yaml`), 125-126 (`.github/agents/_ship.agent.md`) and 130-131 (`.github/agents/_orchestrator.agent.md`). No line moves (534 lines at both commits; 158,091 to 159,066 bytes) |

* **Manifest values.** Each changed checksum equals the raw-blob SHA-256 of
  its path at `08787a4b`:

| Manifest line | Entry | New value | Raw-blob SHA-256 at `08787a4b` | Equal | Old value |
|---|---|---|---|---|---|
| 110 | `.autoharness/config.yaml` | `73afa025c1c9e1b0f219bb52ac1dc17a6cabe466666279844ca9091074185f00` | `73afa025c1c9e1b0f219bb52ac1dc17a6cabe466666279844ca9091074185f00` | Yes | `d38f67834a052da8ca777d0ce553d97ad3a3fe026c2c90bea49485f13d0bd6c2`, the config value at `5bcb00e5`, before `89b0db6d` |
| 125 | `.github/agents/_ship.agent.md` | `fd5a45a6c93e592eaf894228151416fdf35b527f79ee7bec6e11fa03f258b261` | `fd5a45a6c93e592eaf894228151416fdf35b527f79ee7bec6e11fa03f258b261` | Yes | `250fc87a4275a5b7c1a5a143b6c2d7d9b97c50db1b465a84157c3c891c4c8a38`, the mirror value at `4acba14a` |
| 130 | `.github/agents/_orchestrator.agent.md` | `656bac9d2d5a31b508956d81d32a95590b3e89b6b0559dff56e60171eca403ba` | `656bac9d2d5a31b508956d81d32a95590b3e89b6b0559dff56e60171eca403ba` | Yes | `832989d95da75626e864ed27b5b43743ee8d60aad9f8b67f3315d9126a6b2421`, the orchestrator value at `4acba14a` |

**Why this rebaseline is not the lifecycle activation, and hides none.** The
template blob is unchanged. The mirror's body is byte-identical, and only
three frontmatter routing values changed. In the manifest, only the
checksum and note values of three entries changed. No other entry changed,
including the `harness-architect` entry at lines 237-239. No Pre-Flight,
Harness Generation, Build Ready Queue, task-loop, Crash-Resumption, Session
start or Resumption Protocol text changed. The count of `harness-architect`
references is unchanged: six in the template and none in the mirror, at
both `4acba14a` and `08787a4b`. Nothing moves, prepares or partly performs
the per-task harness placement, which remains the one future task and
commit of `PE-ACTIVATE-02`.

Every section 6.7 anchor line is unchanged, and no line moved. Stage
compared each anchor line's text at `4acba14a` and `08787a4b`, at the same
line number:

* in the template, Step 2 (line 328), Step 3 (line 347, filter at line
  374), Step 4 (line 385), the Session start span (lines 1004-1006), the
  Crash-Resumption heading (line 1008), line 1034, the resolution rule
  (line 1040) and the `### Resumption Protocol` span (lines 1103-1107);
* in the mirror, the Crash-Resumption heading (line 172), line 198, the
  resolution rule (line 204), Step 1 (line 331), Step 2 (line 338) and
  Claim (line 359).

Section 6.7 still cites `082df7b2`, and it is unchanged.

**Excluded from the row.** `08787a4b` also changes two paths that are not
`PE-ACTIVATE-01` paths:

* `.autoharness/config.yaml` (7 insertions, 7 deletions; blob `d8cb0915` to
  `357689f9`). The Orchestrator and Ship route blocks change to
  claude-opus-5.5/anthropic/high, and the copied route comments are
  corrected.
* `.github/agents/_orchestrator.agent.md` (frontmatter lines 8-10 only; blob
  `9fb5a96b` to `6cf3c8fa`).

They are recorded here, not rebaselined, and no row is added for them. They
are covered by this row only through their checksum values inside the
manifest blob. The new config checksum also absorbs `89b0db6d` ("updated
routing", 2026-09-23T22:31:18-07:00, `.autoharness/config.yaml` only, an
ancestor of `4acba14a`). From `89b0db6d` to `4acba14a`, the manifest kept the
older config value `d38f6783...`, so the change was unrecorded. Whether
`89b0db6d` is an operator setup commit outside the proof actors
(proof-exit OD-5) is not decided by this version.

**Proof-exit rule (PE-1.7).** At proof exit, all three paths must have the
`08787a4b` blobs above, with no uncommitted change to any of them. No
activation, full or partial, happens during proofs. Before its first write,
every Ship proof invocation checks the three blob IDs at `HEAD` and runs
`git status --porcelain` for the three paths. If a blob differs, or any of
the three paths has an uncommitted change, Ship stops before writing and
returns to the operator (`BLOCKED`). When version 1.7 was written,
`git status --porcelain` for the three paths was empty, and `HEAD` was
`08787a4b`.

**Earlier checks against `4acba14a`.** Every `PE-ACTIVATE-01` check recorded
against `4acba14a` stands as recorded, under the version it was made under.
That includes Proof C run 4's check. During run 4's Ship invocations the
Orchestrator used `git stash` to set aside the operator's uncommitted mirror
routing edit, and restored it afterwards (disclosed in `4c6e2701`). This
version records that disclosure and does not re-evaluate it. The version 1.3
record for `5bcb00e5` (section 3.2) and the version 1.4 record for
`4acba14a` (section 3.3) stay as written.

**`PE-FLOW-04` ruling (Option A).** Recorded as the operator ruled it:

* **Recorded historical exception.** Proof D run 4 (`36f65975`, PE-1.4,
  `PASS` on the synthetic contract) is a recorded historical exception to
  `PE-FLOW-04`. Its breach stays on the record: it was a second attempt at
  run 3's (`8179feb1`, PE-1.4) failed question under the same version.
  Run 4 is not withdrawn, edited or relabelled, and its `PASS` stands as
  recorded. It is not relied on as evidence for any row.
* **Admissible evidence.** Proof D run 5 (`5976ff62`, PE-1.5, `PASS` on the
  synthetic decided contract only) is Proof D's admissible evidence, for
  `PE-DATA-03` and the Proof D half of `PE-SAFETY-04`.
* **Prospective reading.** From version 1.7 onward, the unchanged pass
  criterion, "No second attempt of a failed proof question exists without a
  charter version bump", is evaluated over the record minus that one listed
  exception. The exception list is closed and holds only Proof D run 4. Any
  other second attempt at a failed proof question without a version bump,
  whether already recorded or made later, still breaches the row. Only a
  further operator-approved version can add an exception.
* **Row text unchanged.** The ruling does not strictly require rewording.
  It rules on which record the unchanged criterion is evaluated over, not
  on what the criterion demands. The charter records that reading in a note
  beside the row. Version 1.5 did the same when it recorded the scope of
  the "cursor restore" mis-ordering and left the Proof E pass criterion's
  text unchanged. Rewording the criterion would change it for every proof
  and every future attempt, which the ruling does not ask for.
* **No verdict relabelled.** Proof D run 1 `FAIL` (PE-1.1), run 2 historical
  `PASS` (PE-1.2), run 3 `FAIL` (PE-1.4), run 4 `PASS` (PE-1.4) and run 5
  `PASS` (PE-1.5) all stand as recorded. The prior breach stays on the
  record.
* **Residual, disclosed and not decided.** Run 3's route, charter change
  control to make "caught" concrete, is still not enacted. Runs 4 and 5 were
  both adjudicated under run 3's stricter reading (`5976ff62`). Option A
  accepts run 5 without that clarification. This version does not enact it,
  and no row depends on it.
* **Row status.** Whether `PE-FLOW-04` is met at proof exit is for the
  proof-exit audit to decide, applying this reading.

**What did not change.** All of the following are unchanged:

* Every other matrix row's ID, requirement, normative source, pass
  criterion, evidence, severity and deferral. That includes the text of
  `PE-FLOW-04` itself, the `082df7b2` diagnostic-record baseline of
  `PE-SCOPE-01`, and `PE-ACTIVATE-02`.
* Every proof's question, actors, anchors, time and file bound, pass list,
  fail clause and boundary (sections 6.3 to 6.9). That includes the section
  6.5 candidate and governing reason set, and the section 6.7 terms and
  post-activation restore contract.
* The Proof C clock rule and its 120-minute bound (sections 3.5 and 6.5).
* The section 6.1 execution rules, including Ship's Step 0.1 index refresh,
  apart from the blob-ID reference above.
* The threat model (section 5), the section 4.3 prohibitions, the
  proof-exit rules of section 8 apart from item 1's reporting reference, the
  frozen diagnostic record (section 4.2) and sections 3.1 to 3.5.

This version changes no Ship surface, manifest, config, source, backlog
item, shipment or stash entry.

**Carried-forward verdicts.** Every verdict stands as recorded, under the
version it was recorded against, and none is relabelled or waived:

* Proof A run 5: `PASS`, synthetic fixture (PE-1.4, `99e9ff5f`; addendum
  `4d132bf9`).
* Proof B run 3: `PASS`, disposable stub and predicate (PE-1.4, `6920cb7c`).
* Proof C run 1 `FAIL` (PE-1.3, `9d0ed834`), run 2 `BLOCKED` (PE-1.4,
  `309ab0e2`), run 3 `FAIL` (PE-1.5, `f23b9549`), and run 4 `PASS` (PE-1.6,
  `4c6e2701`).
* Proof D runs 1 to 5, as listed above.
* Proof E runs 1 to 4 `BLOCKED`, and run 5 `PASS`, synthetic state-machine
  model (PE-1.5, `c7d5f97e`).
* Proof F run 2: `PASS` (PE-1.4, `8b39a08b`).
* Proof G: `PENDING-LINUX` (PE-1.4, `6daf80bb`; addendum `06f8930b`).

Apart from the two items above, every row and section these runs are judged
against is the same in PE-1.6 and PE-1.7. So each run keeps the standing it
had under PE-1.6. This version marks no proof `PASS` and re-evaluates none.

**No proof run is authorized.** Version 1.7 authorizes no proof run or
re-run. That includes Proof G's Linux half, which remains a non-waivable
execution and release gate under section 6.9, and needs its own
authorization. It also authorizes no activation, harvest, plan, review
attempt, ratification of the implementation matrix, claim, push or pull
request.

## 4. Scope

### 4.1 In scope

* The seven proofs in section 6: Stage read-only analysis, Ship
  verification-only fixture execution in an untracked scratch directory (with
  Ship's separate section 6.1 index refresh, PE-1.4), and the Stage-authored
  findings artifacts.
* One Stage-authored proof-exit report that lists every proof verdict against
  PE-1.7 (with the section 3.1 to 3.6 carry-forward of verdicts recorded
  under PE-1.1, PE-1.2, PE-1.3, PE-1.4, PE-1.5 and PE-1.6).

### 4.2 Frozen diagnostic record (read-only)

The following are preserved unchanged as evidence of how the loop failed. They
are inputs to proofs, never outputs:

* lifecycle plan revision 12 (`0806b601`);
* verdict manifest revision 21 and review attempts 07 through 11 (attempt 11 is
  terminal at `246d8b73`);
* governing decision revision 9;
* feature `181-F`, its sixteen live carriers, archived `181.001-T`, and
  shipment `187-S`.

### 4.3 Prohibited until proof exit

* Review attempt 12, plan revision 13, or any other review or plan revision.
* **Duplicate review-status mutation.** The verdict manifest remains the single
  authority for review state. Recording the loop as halted is performed once,
  by review-skill authority on the operator's instruction, and is not restated
  in any carrier, shipment or charter.
* Any backlog, carrier, shipment or stash edit, including claim, retirement or
  re-charter of `187-S`. (PE-1.4) Ship's section 6.1 index refresh is not
  such an edit. It rewrites only Git-ignored, tool-managed cache under the
  current working directory. It changes no backlog item, shipment or stash
  markdown or status, and it is not a new release unit. This exception
  covers exactly that refresh and nothing broader.
* In connection with the proofs: any task claim or state move, new release
  unit, branch creation or switch, commit by Ship, pull request, push,
  shipment mutation, or `harness-ready` label read-modify-write.
* Production source, template, test, schema, configuration or
  `.autoharness/harness-manifest.yaml` changes; GitHub push or pull request.
  Disposable proof fixtures inside Ship's section 6.1 scratch directory are
  not repository test changes. They are never staged or committed.
* P-004 observation-gate follow-up work. The two pre-existing locks under
  `docs/plans/` and `docs/reviews/` stay untouched.

### 4.4 Separate workstreams

The six other defect entries of the portfolio governed by the governing
decision remain separate. This charter neither advances, blocks, nor reorders
them, and no proof may treat them as a dependency or a deliverable.

### 4.5 Status of 187-S

`187-S` remains `queued`. It is **not claim-ready** as a consequence of this
charter, of Phase 0, or of any proof verdict. Its retirement or re-charter is a
Phase 2 operator decision (parent decision, open decision C3).

## 5. Threat model and platform mandate

Recorded from the operator's B+D approval:

| Aspect | Decision |
|---|---|
| Trust boundary | The operator controls the local development workspace. There is no hostile concurrent filesystem actor in the model |
| Containment roots | The configured workspace root and the autoharness root (`.autoharness/`), each resolved once per run |
| Required | Lexical rejection of invalid paths; rejection of any path whose resolved final target lies outside its root, including ordinary symlink and junction escapes present at read time; bounded reads; explicit, closed failure codes |
| Explicitly not claimed | Time-of-check/time-of-use (TOCTOU) or race resistance; hardlink alias resistance; resistance to hostile concurrent mutation of the tree |
| Platforms | Windows **and** Linux, both first-release functional support, verified by execution on each actual operating system. Version 1.1 changes only *when* the Linux execution happens (section 6.9), not this support promise |
| Removed obligations | Handle-relative traversal (`NtCreateFile` `RootDirectory` descent, `openat`-style descent), a public traversal adapter, and native-platform security spikes |

Reintroducing any removed obligation, or adding any not-claimed property as a
requirement, is a **threat-model change**. It requires a re-charter. It is not
a proof-phase or review-phase finding.

## 6. Proof portfolio

### 6.1 Execution rules

* **Actor split.** Every proof has two actors with separate duties. Neither
  actor performs the other's duty, and neither uses a worktree other than the
  one current worktree:
  * **Stage: read-only analysis and findings.** Under the `spike` skill
    (`.github/skills/spike/SKILL.md`), Stage scopes each proof, performs its
    read-only analysis (truth-table and budget derivation, verbatim anchor
    reading, compound and policy research, static actor and policy
    comparison), and authors every findings artifact and the proof-exit
    report. Stage never executes a fixture test or fixture command, never runs
    a build, a test suite or a linter, never writes a test, source or
    configuration file, and never creates or uses an additional worktree for
    executable proofs (P-010; the Stage Role Boundary in
    `.github/agents/_stage.agent.md`). The P-016 Stage spike/research worktree
    exception is **not** used. It permits a separate worktree for
    investigation. It does not permit Stage to run tests, and no proof needs
    it.
  * **Ship: verification-only execution.** Every executable step the matrix
    requires (writing a disposable fixture and running a bounded fixture
    command) is performed by Ship in the one current worktree on its current
    branch. No branch is created or switched. This is verification only. It
    claims no task, starts no new release unit, opens no pull request,
    mutates no shipment or label, pushes nothing, and grants no P-004 red or
    claim authority. It is test-only verification supporting the in-flight
    staged lifecycle scope (feature `181-F`, shipment `187-S`, both frozen
    under section 4.2). It is not implementation, and no new backlog item or
    shipment is created or claimed for it.
* **Scratch directory (PE-1.4).** Ship's fixture writes go only inside one
  named per-session scratch directory inside the current working directory,
  `.proof-scratch/{proof}-{YYYYMMDD-HHMMSS}/`, whose resolved path Ship records
  before the first write. Ship's only other write is the separate
  tool-managed index refresh in the next bullet. Every Ship write stays inside
  the current working directory. Ship never writes production source,
  templates, tests, schemas, configuration, the harness manifest, backlog
  item, shipment or stash files, or any deliberation, spike, plan or review
  artifact (the Ship Role Boundary in `.github/agents/_ship.agent.md` forbids
  planning artifacts). Scratch content is never staged or committed. Ship
  removes only its own scratch directory, and only after verifying that the
  resolved path equals the recorded scratch path inside the current working
  directory and that cleanup is approved in the handoff or by the operator.
* **Backlog index refresh (PE-1.4).** In every Ship proof invocation,
  including a verification-only one, Ship alone runs its existing Step 0.1
  refresh before any semantic backlog read. The refresh is
  `backlogit_sync_index`, or, if that fails, the registered CLI fallback
  `backlogit sync` run from the current working directory. Stage never runs
  the refresh or any backlog CLI mutation for a proof.
  * **Scope.** The refresh may update only Git-ignored, tool-managed index
    cache under `.backlogit/` in the current working directory: the index
    `.backlogit/*.db` and its `-shm` and `-wal` companions (`.gitignore` lines
    11, 13 and 14). Any other Git-ignored path under `.backlogit/` that the
    refresh itself writes is recorded by name. The refresh changes no backlog
    item, shipment or stash markdown or status, makes no commit, and touches
    no proof fixture source outside scratch. A write to a tracked or
    non-ignored path, or to any path outside the current working directory,
    makes the invocation `BLOCKED`. A cache refresh is not a backlog, carrier,
    shipment or stash edit, not a task claim or state move, and not a new
    release unit. This bullet asserts exactly that and nothing broader.
  * **Fail closed.** If the MCP refresh fails, Ship runs the CLI fallback. If
    the CLI exits non-zero, or neither transport's success can be verified,
    the invocation is `BLOCKED` before the first scratch write and goes back
    to the operator. For proofs this is stricter than Step 0.1's general
    `INDEX_SYNC_WARN` continuation, which does not apply. Ship records the
    transport used and the native result: the MCP success or error, or the
    CLI's own exit code, not a wrapper's. It also records bounded output: an
    excerpt of at most 2 KiB, plus the byte length and SHA-256 of the full
    stdout and stderr.
  * **Order.** Ship runs the refresh first, then the checkpoint scan and the
    P-001 reads. No invocation may record P-001 as satisfied unless the
    result comes from reads made after a successful refresh in the same
    invocation.
  * **Bounded projections.** The P-001 reads use the registered list
    operations for tasks, features, chores and shipments, each filtered to
    the active status. For each list Ship reports the count and, at most, the
    IDs and statuses. The checkpoint anomaly scan enumerates every checkpoint
    summary with no `status` or `agent` filter, as the Ship recovery protocol
    requires, so that a quarantined record with an empty field is not hidden.
    It reports the total count, the anomaly count and, for each anomaly or
    active `ship`-owned record, the filename, `agent`, `status` and validation
    flag. An anomaly, or an active `ship`-owned checkpoint, follows Ship's own
    recovery protocol (operator handoff), and the proof invocation is
    `BLOCKED`. Large raw output is never dumped to the console or the
    transcript. It is captured in process and reported by byte length and
    SHA-256, and it is never written outside the recorded scratch directory.
  * **No new mechanism.** This bullet adds no standalone scheduler or tool,
    and it changes no other actor's authority.
* **Per-invocation gates (PE-1.4).** Before every Ship invocation, Ship performs its
  fail-closed P-010 self-check (`.github/instructions/role-enforcement.instructions.md`)
  and evaluates P-001 (single release unit), P-002 (no claim and no
  `harness-ready` consumption), P-011 (branch-before-mutation, as written) and
  P-016 (`git worktree list --porcelain` shows exactly the current worktree).
  P-001 is evaluated only after the index refresh above. Before the first
  write, Ship also confirms that the three `PE-ACTIVATE-01` paths at `HEAD`
  have the section 3.6 blob IDs (PE-1.7; the section 3.3 blob IDs before
  version 1.7), with no uncommitted change to them.
  No exemption from any policy is assumed. If the active release unit
  conflicts under P-001, if any gate or check rejects verification-only
  execution, or if `HEAD` holds an unexpected change to those paths, Ship
  stops, reports the rejecting gate and its evidence, and returns to the
  operator. There is no role workaround: no Stage execution, no additional
  worktree, no substitute actor.
* **Evidence handoff (PE-1.4).** For each invocation Ship reports: the recorded scratch
  path; each bounded command verbatim; stdout, stderr and exit status (raw,
  or by SHA-256 when large); host facts; the fixture listing with a SHA-256
  per file; elapsed time; the per-invocation gate results, including the
  index refresh record and the bounded projections above; and a safety
  statement. The safety statement shows that `git status --porcelain` is
  identical before and after, apart from the scratch directory, and that
  `git status --porcelain --ignored -- .backlogit` differs, if at all, only in
  the tool-managed cache paths of the refresh bullet. Stage writes the
  immutable findings artifact from that evidence and records the verdict.
  Ship writes no findings artifact.
* **No repository suite, build or lint.** No actor runs this repository's
  build, test suite or linters as proof evidence, and Stage runs none at all
  (P-010). Every fixture command runs against its own disposable fixture
  tree in the scratch directory. Proof A runs the exact canonical command
  inside a synthetic source-layout workspace in scratch, never against this
  repository's `tests/`.
* **Disposable code.** Proof fixtures are not a prototype of the feature and
  are never committed or merged. The durable output is one Stage-authored
  findings artifact per proof (or per combined session), following the spike
  skill's `docs/decisions/{YYYY-MM-DD}-{slug}-spike.md` naming.
* **Verdicts.** Each proof ends `PASS`, `FAIL` or `BLOCKED`. Proof G alone may
  also end `PENDING-LINUX` (section 6.9). There is no partial pass. Exceeding
  the time or file bound is `FAIL`. A proof's time bound covers its Stage
  analysis and its Ship execution together. (PE-1.6) For Proof C from run 4
  onward, the clock start, clock end and bound are fixed in section 6.5 and
  section 3.5.
* **FAIL routing.** A `FAIL` returns to architecture or charter (Phase 0) with
  the reopened decision named. It never triggers a prose rewrite of a plan.
* **BLOCKED routing.** `BLOCKED` means the proof could not be executed under
  this section: a required environment was not available, or a
  per-invocation gate rejected Ship's verification-only execution. It goes to
  the operator and is never converted into `PASS`.
* **PENDING-LINUX routing.** Defined in section 6.9. It is never converted
  into `PASS`, and it is never satisfied by Windows evidence.
* **Combination.** Independent proofs may share one Stage analysis session or
  one Ship invocation only when each keeps its own question, verdict,
  evidence and time bound. Budgets do not pool. The permitted pairings are C
  with D, and B reusing C's candidate schema as an input (the schema counts
  against C's file bound only).

### 6.2 Portfolio summary

| Proof | Question (narrow) | Time | File bound | Host | Matrix rows | Lineage |
|---|---|---|---|---|---|---|
| A | Does the canonical whole-suite command plus a unique per-test `NotImplementedError` marker yield evidence that P-004 accepts, and are all P-004 rejected outcomes refused? | 60m | 3 disposable | Windows | `PE-EVIDENCE-03`, `PE-FLOW-02` | `S69`, `S78` |
| B | Can a consumer tell a genuine resolver verdict from any impostor by process status plus exactly one schema-valid document? | 60m | 2 disposable | Windows | `PE-INTERFACE-02`, `PE-SAFETY-05` | `S72` |
| C | (PE-1.4, run 2) Is a one-entry `SurfaceSpec` with total member and manifest reason codes a closed, schema-parity-complete truth table? | 75m (runs 1 to 3); 120m from run 4, clock per section 6.5 (PE-1.6) | 2 disposable | Windows | `PE-INTERFACE-03`, `PE-DATA-01`, `PE-DATA-02` | `S70`, `S76` |
| D | (PE-1.2, run 2) With the admitted maximum at 48 members, does the one budget equation over every admitted member, candidate and recheck fit `max_files` with the recorded margin, and does every read-limit error, including byte exhaustion that is not guaranteed to fit, reduce to `UNRESOLVED / 2`? | 45m | 1 disposable | any | `PE-DATA-03`, `PE-SAFETY-04` | `S71` |
| E | Can one state machine, anchored on the exact Ship template and installed mirror, express per-task harness placement and checkpoint-first restore? | 60m | 2 disposable | any | `PE-FLOW-03`, `PE-ACTIVATE-01` | `S73`, `S72` |
| F | Does the established raw staged-blob checksum procedure replay exactly? | 30m | 1 script, disposable repo | Windows | `PE-DATA-04` | `S74` |
| G | Does ordinary resolved-path containment with bounded reads satisfy every SAFETY row on actual Windows and actual Linux? | 90m | 2 disposable | Windows at proof entry; Linux at proof entry if a host exists, otherwise `PENDING` (section 6.9) | `PE-SAFETY-01` to `PE-SAFETY-07`, `PE-EVIDENCE-02`, `PE-INTERFACE-01` | Settles `S54`, the outside-root half of `S77` and the functional half of `S79`; confirms the scope retirement of `S53`, `S75`, `S80` and the `S55` non-claim |

Total: **seven proofs, 420 minutes (7.0 hours), at most 13 disposable files**.
No production code is written. No tracked file in this repository changes
other than the Stage-authored findings artifacts and the proof-exit report.
Disposable fixtures exist only in Ship's untracked scratch directory. Proof
G's 90 minutes cover proof-entry execution. A Linux half carried forward
under section 6.9 is executed later in implementation CI, outside this
budget.

Actor split per proof (section 6.1). Stage never executes. Ship never
authors findings.

| Proof | Stage (read-only analysis; findings author) | Ship (verification-only execution in scratch) |
|---|---|---|
| A | Static actor and policy evidence: compares recorded runner output with the written P-004, harness-architect and manifest text | Runner behavior: builds the synthetic source-layout workspace and runs the exact canonical command and each rejection variant |
| B | Schema and predicate reasoning; channel-rule record | Runs the stub CLI and the acceptance predicate over every genuine and impostor case |
| C | Derives the input classes, reason codes, precedence and candidate schema | Runs the exhaustive enumeration, schema validation and mutation checks |
| D | Derives `C(N)` over every claim source | Runs the exhaustive check for every admitted `N` and the real `187-S` membership |
| E | Reads the anchors verbatim and records the template/mirror asymmetry and insertion anchors | Runs the state-machine fixture over the canonical and mis-ordered traces |
| F | Researches the established compound procedure | Runs the staged-blob and HEAD checksum replay and the negative control |
| G | Defines the case set and the closed codes; audits the non-claims | Runs every case on Windows now, and on Linux now when a qualifying host exists |

### 6.3 Proof A - live P-004 RED conformance

* **Question.** What evidence shape does the live P-004 contract accept when
  the canonical whole-suite command runs over generated tests whose production
  stubs raise a unique `NotImplementedError` marker?
* **Evidence split (one question, one verdict).**
  * **A-runner (Ship, executed).** Runner behavior only: what unittest
    actually discovers, emits and returns for the synthetic workspace and each
    rejection variant.
  * **A-static (Stage, read-only).** Actor and policy evidence: Stage compares
    the recorded runner output with the written P-004 text, harness-architect
    Step 4 item 3 and Step 5.2, the manifest variables and compound entry 097-S,
    and states whether each outcome qualifies or is refused *under the written
    contract*.
  * **Boundary.** The harness-architect actor is not invoked. The findings
    never state that the actor itself accepted or refused a fixture. They
    state what the runner emitted and what the written contract requires. No
    actor runs against the live backlog, no `harness-ready` label is read,
    added or removed, and scratch results are never presented as P-004 gate
    evidence for any task.
* **Normative inputs.** P-004 in `.github/policies/workflow-policies.md`;
  `.github/skills/harness-architect/SKILL.md` Step 4 item 3 and Step 5.2;
  `.autoharness/harness-manifest.yaml` `variables_used.TEST_COMMAND` and
  `variables_used.UNIMPLEMENTED_MARKER`; `docs/compound/097-S-canonical-unittest-gate.md`.
* **Setup (Ship, in scratch).** An actual synthetic source-layout workspace
  with `src/` stubs and `tests/`: three roster tests, each reaching a stub that
  raises `NotImplementedError` with a distinct marker unique to that test; one
  unrelated established test that passes; one characterization test outside
  the roster.
* **Run (Ship).** Exactly `PYTHONPATH=src python -m unittest discover -s tests`
  from the synthetic workspace root, with no runner substitution, no
  verbosity flag and no subset. The environment assignment method on Windows
  is recorded.
* **Pass.** A-runner: the run exits non-zero; each roster test is
  individually identifiable in the output with its own marker; the unrelated
  passing test does not affect the verdict; the characterization test does
  not contaminate roster attribution; and the output shows how unittest
  classifies an uncaught `NotImplementedError` (error versus failure).
  A-static: Stage shows that this classification is consistent with P-004's
  "fails with its own expected marker" wording.
* **Required rejections.** Each of these must be shown, from actual runner
  output compared with the written contract, to be refused as RED evidence: a
  marker-bearing `AssertionError`; a pass; a skip; `expectedFailure`;
  `unexpectedSuccess`; a wrong marker; a cross-test marker; zero discovery of a
  roster test; and a collection or import error in a roster module.
* **Fail.** Any required rejection qualifies under the written contract, any
  roster test cannot be individually attributed from canonical output alone,
  or runner classification contradicts the P-004 wording. A contradiction
  routes to the P-004 scope decision (whether policy or actor text enters
  scope). It does not route to a prose rewording.

### 6.4 Proof B - CLI authenticity

* **Question.** Can Ship distinguish a real resolver verdict from a crash or
  impostor output?
* **Actors.** Ship writes and runs the stub CLI and the predicate in scratch.
  Stage records the schema reasoning, the channel rule and the verdict.
* **Setup.** A disposable stub CLI module, invoked in module form with the
  source environment set, emitting controlled outputs. A disposable acceptance
  predicate reads process status, stdout and the candidate result schema.
* **Pass.** The predicate accepts only a single schema-valid JSON document on
  stdout whose requested shipment, state, reason code and exit code all match
  the request and the process status. It returns `resolver-not-observed` for
  every impostor: startup failure, unknown command, argparse usage error, help
  text, empty stdout, malformed JSON, two documents, leading or trailing
  output, a status-to-document exit mismatch, a shipment mismatch, and a
  schema-invalid document. The channel rule for stderr is fixed by the proof
  and recorded.
* **Fail.** Any impostor is accepted, any genuine verdict is rejected, or the
  schema cannot discriminate without relying on status alone.

### 6.5 Proof C - one-entry SurfaceSpec and total reason truth table (PE-1.4, run 2; PE-1.6 clock from run 4)

* **Clock and bound from run 4 (PE-1.6).** Runs 1 to 3 keep the verdicts
  and the 75-minute bound they were judged under. From run 4 onward, the
  clock starts at T0, the earliest of the first Stage design work on the
  run, the first Ship work on it and its operator authorization. Stage
  design done before authorization counts. The clock ends at T1, Stage's
  clock read when it writes the verdict line. It runs continuously, with no
  pause or reset, and T1 minus T0 must be at most 120 minutes. Section 3.5
  gives the full rule and its basis. Run 4 needs an operator authorization
  that names "Proof C run 4 under PE-1.6".
* **Status of run 1.** Run 1 under PE-1.3 is `FAIL`
  (`docs/decisions/2026-09-24-surface-taxonomy-proof-c-spike.md`, `9d0ed834`).
  That verdict stands and is never re-labelled. This section charters run 2
  under `PE-FLOW-04`. It folds in the section 3.1 change request and Decision
  2 of `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`
  (status decided), consistent with section 6.6.
* **Question.** Is the taxonomy closed, and does the schema match the runtime
  exactly?
* **Actors.** Stage derives the truth table, the input classes, the reason
  codes and their precedence, and the candidate schema, read-only. Ship runs
  the enumeration, schema-validation and mutation fixture in scratch. Stage
  records the verdict from Ship's output.
* **Setup.** Exactly one supported mapping: surface `harness-architect` to
  installed `.github/skills/harness-architect/SKILL.md` and template
  `skills/harness-architect/SKILL.md.tmpl`, as tracked by the manifest entry at
  `.autoharness/harness-manifest.yaml:237-239` (at `082df7b2`; the same lines
  at `4acba14a`).
* **Governing reason set (PE-1.4).** This set is fixed by this charter and by
  ratified text. It does not depend on any fixture's own enum. The fixture
  holds it as a separate constant copied from this table, and never derives
  it from the candidate:

  | Code | State / exit | Source |
  |---|---|---|
  | `FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT` | `UNRESOLVED / 2`, class 1b (after class 1, before class 2) | Decision 2 items 1, 2 and 4; section 6.6 |
  | `INPUT_CHANGED_DURING_RESOLUTION` | `UNRESOLVED / 2`, class 1 | Plan revision 12 reducer precedence (frozen diagnostic input); Decision 2 item 2 |
  | `SURFACE_UNSUPPORTED` | `UNRESOLVED / 2` | This section; `PE-INTERFACE-03` |
  | `MEMBERS_TOO_MANY` | `UNRESOLVED / 2` | Section 6.6 |
  | `NO_SURFACES_REQUIRED` | `HARNESS_READY / 0`, class 4 | Plan revision 12 reducer precedence |
  | `ALL_SURFACES_PRESENT` | `HARNESS_READY / 0`, class 8 | Plan revision 12 reducer precedence |

  A class 1b result's `reason_code` is the triggering read-limit
  `ReadErrorCode`, unchanged. It is the one that occurred first in
  deterministic generation order, not the one ranked first by a fixed code
  order. The diagnostics keep the native `ReadErrorCode` and the `ReadStage`
  (Decision 2 item 4). No other code stands for a read-limit error.
  `READ_BUDGET_EXHAUSTED`, or any other code outside the governing set and
  the candidate below, is a defect.
* **Stage candidate (PE-1.4; a proposal, not ratified API).** The run 2
  candidate is the run 1 candidate enum (`c_schema.json`, SHA-256
  `c80cab23bfae45ff34e799abb7d0be1787c1d89ceab0fce0f3cc2c70f89345ae`) with
  `READ_BUDGET_EXHAUSTED` removed and the three class 1b codes added. The
  listed order is the candidate precedence:

  | Class | State / exit | Candidate codes, in order |
  |---|---|---|
  | 1 | `UNRESOLVED / 2` | `INPUT_CHANGED_DURING_RESOLUTION` |
  | 1b | `UNRESOLVED / 2` | `FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT` (first occurrence selects; no fixed order among them) |
  | 2 | `UNRESOLVED / 2` | `BACKLOG_ROOT_NOT_FOUND`, `BACKLOG_ROOT_AMBIGUOUS`, `SHIPMENT_ID_INVALID`, `SHIPMENT_NOT_FOUND`, `SHIPMENT_AMBIGUOUS`, `SHIPMENT_RECORD_INVALID`, `SHIPMENT_ID_MISMATCH`, `MEMBERS_INVALID`, `MEMBERS_EMPTY`, `MEMBERS_TOO_MANY`, `MEMBER_ID_INVALID`, `MEMBER_KIND_UNSUPPORTED`, `MEMBER_DUPLICATE`, `MEMBER_NOT_FOUND`, `MEMBER_AMBIGUOUS`, `MEMBER_RECORD_INVALID`, `MEMBER_ID_MISMATCH`, `NO_TASK_MEMBERS` |
  | 3 | `UNRESOLVED / 2` | `FEATURE_DECLARES_SURFACE`, `DECLARATION_MISSING`, `DECLARATION_MALFORMED`, `DECLARATION_DUPLICATE`, `DECLARATION_MIXED`, `SURFACE_UNSUPPORTED` |
  | 4 | `HARNESS_READY / 0` | `NO_SURFACES_REQUIRED` |
  | 5 | `UNRESOLVED / 2` | `MANIFEST_NOT_FOUND`, `MANIFEST_UNREADABLE`, `MANIFEST_DECODE_INVALID`, `MANIFEST_YAML_INVALID`, `MANIFEST_DUPLICATE_KEY`, `MANIFEST_SHAPE_INVALID` |
  | 6 | `UNRESOLVED / 2` (`INVALID` surface) | `MANIFEST_ENTRY_AMBIGUOUS`, `MANIFEST_TEMPLATE_MISMATCH`, `MANIFEST_ENTRY_INVALID`, `TEMPLATE_NOT_FOUND`, `TEMPLATE_UNREADABLE`, `TEMPLATE_VARIABLE_UNRESOLVED`, `INSTALLED_UNREADABLE` |
  | 7 | `NO_HARNESS / 1` (`MISSING` or `STALE` surface) | `MANIFEST_ENTRY_NOT_FOUND`, `INSTALLED_NOT_FOUND`, `CHECKSUM_MISMATCH`, `RENDER_MISMATCH` |
  | 8 | `HARNESS_READY / 0` | `ALL_SURFACES_PRESENT` |

  Counts are not criteria. The fixture derives every count from these lists
  and records it, and asserts no count written by hand. For reference only:
  the run 1 enum had 45 codes, so this list has 45 - 1 + 3 = 47 (2
  `HARNESS_READY`, 4 `NO_HARNESS` and 41 `UNRESOLVED`). If a derived count
  differs from this reference, the list governs and the difference is
  recorded. Not ratified by any source, and so proposals only: the codes
  outside the governing set; the order within classes 2, 3 and 5 to 7; the
  tie-break between declaration issues; and the shape of `declarations`
  items. Plan revision 12 fixes only that `declarations` is a result field
  sorted by task ID (lines 134 and 138). Run 1's
  `{member_id, surface_id}` with `additionalProperties: false` was Ship's
  assumption. The fixture may use it only when it is labelled as a candidate.
  A run 2 `PASS` ratifies none of these proposals. The commit of this charter
  version is the durable, hash-pinned candidate that the Proof C findings
  asked for. Ship copies both constants from it and records the commit.
* **Pass (PE-1.4). Every part is required.**
  1. **Enumeration.** An exhaustive enumeration over bounded input classes
     maps each class to exactly one `(state, exit, reason_code)`. The member
     classes cover one supported label, `harness-surface:none`, missing,
     duplicate, malformed, mixed (for example a supported label with
     `harness-surface:none`) and unknown-but-well-formed labels.
     Unknown-but-well-formed always yields `SURFACE_UNSUPPORTED`, which
     reduces to `UNRESOLVED`, never `NO_HARNESS`. Global manifest failure
     codes are enumerated with a fixed precedence.
  2. **Governing-set check.** This check runs against the governing constant,
     not the candidate enum. Every governing code is in the candidate, is
     reachable from at least one input, yields its governing state and exit,
     and validates against the candidate schema. Each of the three read-limit
     codes, injected at any stage, yields `UNRESOLVED / 2` with that code,
     never another code. Two read-limit errors, injected in both orders,
     yield the first-occurring code.
  3. **Closure.** Every candidate code is reachable, and precedence is a
     strict total order apart from the first-occurrence rule of class 1b.
  4. **Schema parity.** Every runtime output validates against the candidate
     schema. Every schema branch is produced by at least one input. Mutated
     outputs are rejected, including an output that uses
     `READ_BUDGET_EXHAUSTED` and a class 1b output whose code is replaced by
     a code that is not a read-limit code.
  5. **Real-surface controls (read-only, from Git blobs at the invocation
     `HEAD`).** (a) *Manifest closure:* the installed path matches exactly
     one entry, and its template matches. (b) *Checksum match:* the entry's
     `checksum` equals the SHA-256 of the raw installed blob. (c) *Render
     parity:* the template is rendered with values from the manifest's one
     top-level `variables_used` mapping (line 467 at `4acba14a`), never from
     the artifact entry, which has none. The render uses UTF-8 and LF, and the
     result is compared byte for byte with the raw installed blob. Checksum
     match and render parity are reported as separate results. Render parity
     is `true` or `false` only when every template placeholder resolved from
     the top-level mapping and the bytes were compared. Otherwise it is
     `not-evaluated`, with the unresolved names and the reason, and it is
     never `false`. Render parity `false` or `not-evaluated` is a recorded
     observation of the real installed surface. It goes to the operator, and
     by itself it is not a Proof C `FAIL`.
  6. **Evidence.** For every fixture command execution, including every
     re-execution, Ship reports raw stdout and stderr, or the byte length and
     SHA-256 of each, together with the native exit status. A final exit
     other than 0 is never reported as 0. A run without these fields cannot
     be `PASS` (`PE-EVIDENCE-01`).
* **Fail.** Any of the following is `FAIL`: an input maps to zero or more
  than one outcome; a governing or candidate code is unreachable; a
  governing code is missing, renamed or mapped to a different state or exit;
  a read-limit error yields a code other than the triggering one; schema and
  runtime disagree; or a render-parity result is computed from an artifact
  entry instead of the top-level mapping, or reported `false` without full
  resolution. A `FAIL` returns to architecture or charter (section 6.1).
* **Bounds.** Run 2 gets a new scratch directory, a fresh 75-minute bound and
  a fresh two-file bound (section 6.2). It does not pool with run 1. Run 1's
  scratch directory `C-20260924-120736` stays in place as hash-pinned
  evidence until the operator approves its cleanup.
* **Boundary.** The fixture models the candidate. It tests no production
  code and creates no reason code beyond the governing set and the candidate
  above.

### 6.6 Proof D - budget equation (PE-1.2, run 2)

* **Status of run 1.** Run 1 under PE-1.1 is `FAIL`
  (`docs/decisions/2026-09-23-read-budget-proof-d-spike.md`). That verdict
  stands. This section charters run 2 against the decision
  `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`.
  Its inputs are **decided parameters**, not diagnostic values.
* **Question.** With the admitted membership at `1..48`, does the claim count
  fit `max_files=256` with the recorded margin for every admitted input? Does
  every read-limit error at every read or recheck stage, including byte
  exhaustion that is explicitly not guaranteed to fit, reduce to
  `UNRESOLVED / 2`, never `NO_HARNESS / 1` or `HARNESS_READY / 0`?
* **Actors.** Stage derives the model read-only. Ship runs the exhaustive
  check in scratch. Stage records the verdict from Ship's output.
* **Inputs.** `C(N,U,rho) = 4(N+1) + 3U(1+rho)` over every claim source (queue
  and archive candidates, stable absence, manifest, template and installed
  reads, ledger rechecks). `N` in `1..48`, `U` in `{0,1}`, `rho` in `{0,1}`.
  `max_files=256`, `max_file_bytes=4 MiB`, `max_total_bytes=32 MiB` (unchanged).
  Read-limit errors are `FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT` and
  `FILE_SIZE_LIMIT`. They map to reducer class 1b (after mutation, before class
  2), with the triggering code as `reason_code`.
* **Pass. All four parts are required.**
  1. **File-slot guarantee.** All 192 admitted `(N,U,rho)` cases are simulated
     claim by claim and each equals the closed form. `C_max = C(48,1,1) = 202`
     is recorded with its margin of 54. The margin rule
     `C(N,U,1) + (N+1) <= 256` holds for every admitted `N`. The real `187-S`
     case gives `C(17,1,1) = 78`. Over-limit memberships `N` in `{49, 512, 513}`
     yield `MEMBERS_TOO_MANY -> UNRESOLVED / 2` with at most 4 claims and no
     member lookup.
  2. **Byte distinction.** The run computes the worst-case byte demand
     `[2(N+1) + 3U(1+rho)] * max_file_bytes` at `N=48, U=1, rho=1` (416 MiB).
     It records that this exceeds `max_total_bytes`, so **no byte fit is
     claimed**. At least one admitted case whose reservations exceed 32 MiB,
     including one at `N=17`, yields `UNRESOLVED / 2 / TOTAL_SIZE_LIMIT`, and a file over
     `max_file_bytes` yields `UNRESOLVED / 2 / FILE_SIZE_LIMIT`. Neither case
     yields success.
  3. **Exhaustion at every stage.** A read-limit error is injected at each
     stage: shipment queue or archive candidate, member queue or archive
     candidate, manifest, template, installed, candidate recheck, and surface
     recheck. Byte codes apply only where a present file is read. Each injection
     is combined with each would-be outcome (`NO_SURFACES_REQUIRED`,
     `ALL_SURFACES_PRESENT`, `MISSING`, `STALE`). Every case yields
     `UNRESOLVED / 2` with the injected code. A disagreement observed on a
     completed recheck before the error still yields
     `INPUT_CHANGED_DURING_RESOLUTION`.
  4. **Negative controls, each caught.** The run includes the four run 1
     controls, plus these: admitted maximum 512 (must produce an over-budget
     case); an installed-read exhaustion mapped to `MISSING` (exit 1); an
     exhausted candidate recorded as stable absence; an incomplete recheck
     treated as agreement; and a model that reports success when reservations
     exceed 32 MiB.
* **Fail.** Any of the following is `FAIL`: an admitted case exceeds 256 or
  breaks the margin rule; a closed form and a simulation disagree; any
  exhaustion case yields exit 0 or exit 1, or the wrong reason; a negative
  control is not caught; the findings claim a byte fit for every admitted
  member; or the time or file bound is exceeded. A `FAIL` returns to
  architecture or charter (section 6.1).
* **Boundary.** The fixture models the decided contract. It tests no
  production code and creates no reason code beyond those named above.

### 6.7 Proof E - Ship per-task actor and checkpoint-first state machine

* **Question.** Where exactly does the per-task harness call sit, and can a
  single state machine be consistent with both the exact template and the
  exact installed mirror?
* **Actors.** Stage reads the anchors below verbatim, read-only, and records
  the asymmetry and insertion anchors. Ship runs the state-machine fixture
  over the listed traces in scratch. Stage records the verdict from Ship's
  output.
* **Anchors (read-only, verbatim, at `082df7b2`).**
  `templates/agents/_ship.agent.md.tmpl` Step 2 "Harness Generation (P-002 /
  P-004)" (line 326, which says it "runs once, up front - not in a loop"),
  Step 4 "Execute Task Loop" (line 383) and the Crash-Resumption protocol (line
  1006); `.github/agents/_ship.agent.md` Step 1 (line 329), Step 2 "Task
  Execution Loop" (line 336) and the Crash-Resumption protocol (line 170). The
  installed mirror contains no `harness-architect` reference while the template
  contains six. The proof records that structural asymmetry and the insertion
  anchor it implies for each file.
* **Pass.** The fixture accepts exactly the canonical trace and rejects each
  mis-ordered trace: harness invoked once before the loop instead of per task;
  cursor restore before checkpoint validate-and-resolve (PE-1.3 term below);
  the harness step before checkpoint validation; the consumer proceeding on
  process status without a validated document; and divergent placement between
  template and mirror.
* **Term: checkpoint validate-and-resolve (PE-1.3).** Before any cursor
  restore, Ship selects exactly one checkpoint by explicit, unique operator
  selection among its `ship`-owned candidates, validates it (the anomaly and
  CheckpointV1 schema check and the `agent == ship` owner check), and obtains
  operator confirmation. This term never means calling
  `backlogit_resolve_checkpoint` (template `{{OP_RESOLVE_CHECKPOINT_MCP}}`)
  before restore. That status resolution happens only after a confirmed
  successful resume, as both Ship recovery protocols require (template line
  1038, mirror line 202). The canonical recovery order is therefore:
  enumerate, anomaly check, unique selection, owner validation, confirmation,
  restore, prune, resume, then resolution. A trace that resolves before a
  confirmed successful resume, or on ambiguous or torn state, is a mis-ordering
  the fixture must reject.
* **Term: retained text (PE-1.3).** Retained text is the text of each Ship
  surface that remains after the planned activation edits (`PE-ACTIVATE-02`)
  are applied. Current text that those edits replace is not retained text. The
  planned replacements are:
  * in the template, the up-front, run-once Step 2 "Harness Generation (P-002 /
    P-004)" (lines 326-343) and the `harness-ready`-prefiltered Step 3 "Build
    Ready Queue" (line 345, filter at line 372) are replaced by a per-task
    pre-claim harness step, T1-T3, inside Step 4 "Execute Task Loop" (line 383)
    before Step 4.1 Claim;
  * in the installed mirror, the same per-task pre-claim step T1-T3 is inserted
    inside Step 2 "Task Execution Loop" (line 336), immediately before its
    per-task step 1 Claim (line 357);
  * (PE-1.5) in the template, two more passages are replaced, and neither is
    retained text:
    * the Session start memory-context restore (lines 1002-1004; lines
      1004-1006 at `4acba14a`). It scans `{{DOCS_MEMORY}}/`, restores context,
      and then runs the recovery state machine "before shipment validation";
    * the `### Resumption Protocol` (lines 1101-1105; lines 1103-1107 at
      `4acba14a`). It resumes from a `context-overflow` checkpoint in
      `{{DOCS_MEMORY}}/`.

    The replacement text for both must meet the post-activation restore
    contract below. The mirror has no matching passage, so this adds nothing
    to the mirror's planned insertion and changes none of its retained
    recovery text.

  T1-T3 are the per-task sub-steps of the canonical body in frozen plan
  revision 12 (line 227): T1 resolves the actor surface and keeps exits 0, 1
  and 2 distinct; T2 invokes harness-architect for the current task on exit 0;
  T3 requires the current task's valid marker-bearing RED evidence before the
  task proceeds to Claim. Plan revision 12 line 225, which places a mirror
  section before the Step 2 heading, is a frozen diagnostic input and does not
  set this placement. The Crash-Resumption protocols' recovery order (template
  line 1006, mirror line 170) is retained text. (PE-1.5) Template line 1006 at
  `082df7b2` is the Crash-Resumption heading, which is line 1008 at
  `4acba14a`. It is not the Session start item that is line 1006 at
  `4acba14a`, which is replaced. Neither file is edited during
  proofs. A mismatch between current text and the planned post-activation text
  is an expected input to this proof, not by itself a `FAIL`.
* **Post-activation restore contract (PE-1.5).** After the activation
  (`PE-ACTIVATE-02`), the replacement text for the two template passages
  above, and all retained text of both Ship surfaces, must meet these rules:
  1. Ship restores no memory context, task cursor, phase or next-action
     intent, from any source, before the retained recovery state machine has
     done the following:
     * run its unfiltered enumeration and its anomaly scan;
     * when a `ship`-owned active candidate exists, obtained an explicit,
       unique operator selection, validated the owner (`agent == ship`) and
       the CheckpointV1 schema, and obtained operator confirmation.
  2. No memory checkpoint provides a path around these steps. That includes
     a `{{DOCS_MEMORY}}/` file and a `context-overflow` checkpoint. None of
     them restores the task cursor, phase or next-action intent at any point.
     A resume after a `context-overflow` halt goes only through the recovery
     state machine. The retained halt text, which records the checkpoint
     path as the resumption point, stays unchanged.
  3. Zero valid `ship`-owned active candidates is the normal continuation.
     It is not a failure and not an operator handoff. The recovery state
     machine still runs before shipment validation.
  4. Status resolution happens only after a confirmed successful resume,
     under the PE-1.3 term above, which is unchanged.

  The activation task writes the replacement wording. This charter fixes
  only the contract.
* **Scope of the restore mis-ordering (PE-1.5).** The pass list's
  mis-ordering "cursor restore before checkpoint validate-and-resolve"
  covers memory-context, phase and next-action restore from any source. It
  includes a restore from a docs-memory file or from a `context-overflow`
  checkpoint. The fixture must reject such a restore whenever it comes before
  the steps in contract rule 1. It must also reject any memory-checkpoint
  resume that bypasses those steps. The pass criterion's text is unchanged.
* **Fail.** No single state machine satisfies both files without contradicting
  retained text (PE-1.3 term above). That reopens the activation design.
* **Boundary.** No edit to either file. The fixture models them and does not
  modify them.

### 6.8 Proof F - raw staged and HEAD checksum replay

* **Question.** None. This is established procedure
  (`docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`
  section 1), replayed so that the terminal activation task cannot improvise.
* **Actors.** Stage researches the compound procedure read-only. Ship runs
  the replay and the negative control in scratch. Stage records the verdict
  from Ship's output.
* **Setup.** A disposable, independent repository initialized inside Ship's
  scratch directory. It is not a worktree of this repository and is never
  registered with it, so the P-016 worktree check is unaffected. In it:
  commit an LF file, stage a change, then read `git cat-file -p :<path>` by
  Python subprocess with binary capture and hash it with SHA-256. Commit,
  then hash `git cat-file -p HEAD:<path>` the same way.
* **Pass.** The staged digest equals the post-commit HEAD digest. A PowerShell
  text-capture negative control is run and its result recorded, whether or not
  it reproduces the CRLF hazard. The negative control alone cannot fail the
  proof.
* **Fail.** The raw staged digest differs from the HEAD digest after commit.

### 6.9 Proof G - portable ordinary-path containment on Windows and Linux

* **Question.** Does ordinary resolved-path containment with bounded reads
  satisfy every SAFETY row on actual Windows and actual Linux?
* **Actors.** Stage defines the case set and the closed codes and audits the
  non-claims, read-only. Ship runs every case on each available host in
  scratch. Stage records per-host results and the verdict.
* **Hosts.** Native Windows on NTFS, and a Linux kernel on a Linux-native
  filesystem (a native host, a VM, or WSL2 on its ext4 volume; a Windows
  volume mounted into Linux does not count). Neither Stage nor Ship pushes to
  CI to obtain a host during proofs.
* **Timing.**
  * **Windows: required now.** Ship executes the full case set on actual
    Windows at proof entry.
  * **Linux: now if a host exists.** If a qualifying Linux host is available
    at proof entry, Ship executes the identical case set there now, so both
    hosts are verified at proof entry. The Linux fixture root must sit on a
    Linux-native filesystem. When that puts the scratch directory outside the
    current working directory (for example, WSL2's ext4 volume), Ship records
    that location and needs operator approval before the first write. Without
    approval, Linux is treated as unavailable.
  * **Linux: otherwise PENDING.** If no qualifying Linux host is available at
    proof entry, the Linux half is recorded `PENDING`. It is never `PASS`,
    never inferred from Windows, and never simulated. Actual Linux execution
    of the full case set, in CI on a Linux runner with a Linux-native
    filesystem, becomes a **non-waivable execution and release gate** for the
    later implementation. It is carried into the implementation matrix draft
    as `not-deferrable`, no one may waive it, and no lifecycle release unit
    that depends on this containment is released without it. Windows evidence
    alone never satisfies the cross-platform acceptance of any row that
    requires both hosts.
* **Setup.** A disposable root containing nested directories and an outside
  sibling that holds a sentinel secret file.
* **Lexical rejection cases (each host).** Empty path; NUL byte; absolute
  path; a `..` escape and an interior `a/../../x` escape. On Windows also:
  drive-relative `C:x`; UNC `\\server\share`; `\\?\` and `\\.\` device
  prefixes; alternate data stream `name:stream`; reserved device names (`CON`,
  `NUL`, `COM1`); trailing dot or space.
* **Resolved-path cases.** Linux: a file symlink and a directory symlink to
  outside (reject); an in-root symlink resolving inside (accept); a dangling
  symlink (explicit reject). Windows: a directory junction to outside (reject,
  mandatory); an in-root junction resolving inside (accept); file and directory
  symlinks to outside (reject) when the host grants symlink creation. Also a
  case-variant root spelling on Windows.
* **Bound cases.** A file of cap+1 bytes is rejected with an explicit code
  after reading at most cap+1 bytes; the total-bytes and file-count caps each
  produce their own explicit code; a directory or other non-regular target is
  rejected; a missing target returns not-found. There is no silent truncation.
* **Informational only.** An in-root hardlink to the outside sentinel may be
  observed and recorded as *not defended*, which documents the non-claim. It is
  never a pass or fail condition.
* **Pass.** On each executed host, every accept case returns the correct
  bytes, every reject case returns its specified closed code, and the
  sentinel's bytes never appear in any result.
* **Fail.** Any escape, silent truncation or unexplained platform divergence
  on any executed host. That reopens the containment architecture.
* **Verdict rule.** `FAIL` if any executed host fails. `PASS` only when both
  Windows and Linux have executed and passed. `PENDING-LINUX` when Windows
  has passed and Linux is `PENDING`: this records the Windows result, carries
  the Linux gate forward, and is never reported as `PASS`. `BLOCKED` when
  Windows could not be executed.

## 7. Acceptance matrix PE-1.7

PE-1.7 equals PE-1.6 in every row ID, requirement, normative source, pass
criterion, evidence, severity and deferral, except the comparator in row
`PE-ACTIVATE-01`, marked "(PE-1.7)" (section 3.6). It also records, beside
the unchanged `PE-FLOW-04` row, the operator's ruling on how that row is
evaluated (the "(PE-1.7)" note under the section 7.4 table). PE-1.6 equals
PE-1.5 in every row ID, requirement, normative source, pass
criterion, evidence, severity and deferral. It changes only the Proof C clock
and bound from run 4 onward (sections 3.5 and 6.5). `PE-FLOW-04` is
unchanged. PE-1.5 equals PE-1.4 in every row ID, requirement, normative source, pass
criterion, evidence, severity and deferral. The only change is the section
6.7 scope (PE-1.5; section 3.4) against which these are read: `PE-FLOW-03`,
through its anchors "listed in section 6.7", and the future activation
(`PE-ACTIVATE-02`). PE-1.4 equals PE-1.3 except rows `PE-AUTH-01`, `PE-AUTH-02`, `PE-DATA-01`,
`PE-DATA-02`, `PE-EVIDENCE-01` and `PE-ACTIVATE-01`, each marked "(PE-1.4)"
(section 3.3). PE-1.3 equals PE-1.2 except row `PE-ACTIVATE-01`, as it read
under PE-1.3 (section 3.2). PE-1.2 equals PE-1.1 except rows `PE-DATA-03` and
`PE-SAFETY-04`, each marked "(PE-1.2)" (section 3.1).

### 7.1 Severity and deferral legend

| Severity | Meaning during proof entry |
|---|---|
| `P0` | Invalidates the proof phase; halt and route to the operator |
| `P1` | Blocks proof exit |
| `P2-critical` | Predesignated critical; blocks proof exit |
| `P2` | Recorded; does not block proof exit |
| `P3` | Recorded observation |

| Deferral status | Meaning |
|---|---|
| `not-deferrable` | Must hold at proof exit |
| `operator-deferrable` | Only the operator may defer it at proof exit, and the deferral is recorded with rationale |
| `deferred-to-implementation-matrix` | Constrains proofs where stated, and becomes a candidate row of the implementation matrix ratified after proof exit |
| `linux-execution-gate` | Applies to the Linux half of a row only. The Linux evidence is produced at proof entry when a qualifying host exists. Otherwise it is recorded `PENDING`, never `PASS`, at proof exit, and it is carried into the implementation matrix as a `not-deferrable` execution and release gate (section 6.9). It is not a deferral, no one may waive it, and Windows evidence never satisfies it |

### 7.2 AUTH

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-AUTH-01` | Proof-phase work stays inside the Stage and Ship role boundaries (PE-1.4) | P-010; `.github/agents/_stage.agent.md` Role Boundary; `.github/agents/_ship.agent.md` Role Boundary and P-010 self-check | Every proof-phase commit is a Stage commit that changes only `docs/decisions/*-spike.md` findings or the proof-exit report. Stage runs no fixture command, build, test suite or lint, performs no index refresh or backlog CLI mutation, and writes no test, source or configuration file. Ship's verification-only execution writes fixtures only in its recorded scratch directory. Its only other write is the section 6.1 index refresh, which touches only Git-ignored, tool-managed cache under the current working directory. Ship commits nothing, and performs no claim, task move, branch, PR, push, shipment or label mutation | `git show --name-only` for each proof-phase commit; Stage session log; Ship's per-invocation command log, before/after `git status --porcelain`, and before/after `git status --porcelain --ignored -- .backlogit` | `P0` | `not-deferrable` |
| `PE-AUTH-02` | No additional worktree is used; executable verification runs only in the one current worktree, under per-invocation policy gates (PE-1.4) | P-016; P-011; P-001; P-002; `.github/agents/_ship.agent.md` Role Boundary and Step 0.1; section 6.1 | `git worktree list --porcelain` shows exactly the current worktree before, during and after every Ship invocation. Each invocation records its P-010 self-check, its section 6.1 index refresh (transport, native result, bounded output), and its P-001, P-002, P-011 and P-016 results, with P-001 taken only from bounded, active-filtered reads made after a successful refresh in the same invocation. A failed or unverifiable refresh, or any rejection, halted execution as `BLOCKED` and was returned to the operator with no workaround | Worktree listings, refresh records and per-invocation gate records in Ship's reported evidence | `P1` | `not-deferrable` |
| `PE-AUTH-03` | No artifact self-authorizes attempt 12, revision 13, claim, retirement or re-charter of `187-S`, reviewer selection or `P2` policy | P-010; P-017 (autonomy is not a waiver); parent decision | The proof-exit report lists C2, C3 and C4 as pending, and neither a proof artifact nor a Ship evidence report contains an authorization or asserts P-004 red or claim authority | Text audit of proof-phase artifacts and Ship evidence reports | `P0` | `not-deferrable` |
| `PE-AUTH-04` | The charter never overrides a higher source | Constitution Governance section; workflow policy registry preamble | Every row cites an existing source; no row states an exception to it; any conflict is routed as a charter change | Row-by-row source audit in the proof-exit report | `P1` | `not-deferrable` |

### 7.3 SCOPE

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-SCOPE-01` | The diagnostic record stays frozen | Parent decision (freeze); attempt 11 frontmatter (`review_terminal: true`) | `git diff 082df7b2..<proof-exit HEAD>` is empty for the plan, the verdict manifest, attempts 07-11 and governing decision revision 9 | Diff output at proof exit | `P0` | `not-deferrable` |
| `PE-SCOPE-02` | No attempt 12, no revision 13, no duplicate review-status mutation | Verdict manifest (`attempt_12_authorized: false`); `.github/skills/plan-review/SKILL.md` | No new or changed file under `docs/reviews/` or `docs/plans/` during proofs | `git diff --name-only` at proof exit | `P0` | `not-deferrable` |
| `PE-SCOPE-03` | Backlog, carriers, shipment and stash frozen until proof exit | P-010 (edits are permitted but chartered out); parent decision | No change under `.backlogit/queue/` or `.backlogit/archive/` for `181-F` or `181.*`; `187-S` read back as `queued` with the same seventeen items | `git diff` scoped to those paths; `backlogit_get_shipment 187-S` output | `P1` | `not-deferrable` (lifts at proof exit) |
| `PE-SCOPE-04` | `187-S` is not claim-ready from Phase 0 or from proofs | P-002; P-004; verdict manifest (`publication_eligible: false`) | No claim event; status `queued`; no `harness-ready` label added | Shipment read-back; carrier labels unchanged | `P0` | `not-deferrable` |
| `PE-SCOPE-05` | The six other portfolio defect entries stay separate | Governing decision revision 9 (portfolio scope) | No proof artifact names another entry as a dependency or deliverable | Text audit | `P2` | `not-deferrable` |
| `PE-SCOPE-06` | P-004 follow-up work and its locks are untouched | P-004; `.github/skills/file-lock/SKILL.md` (only the owner or operator releases a lock) | Both lock files still exist with zero-byte content | `Get-Item -Force` length at proof exit | `P1` | `not-deferrable` |
| `PE-SCOPE-07` | Each proof stays within its time and file bound | `.github/skills/spike/SKILL.md` (time-box enforcement); section 6.2 | Recorded elapsed time and file count are at or below the bound; an overrun is recorded as `FAIL` | Per-proof header fields | `P1` | `not-deferrable` |

### 7.4 FLOW

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-FLOW-01` | A `FAIL` reopens architecture or charter, never a prose rewrite | Parent decision (architectural rule); `docs/compound/093-S-review-loop-convergence.md` | Every `FAIL` record names the reopened decision; no plan revision follows | Findings artifacts; `git log` | `P0` | `not-deferrable` |
| `PE-FLOW-02` | Proof exit precedes any implementation matrix, re-slice, harvest or plan | P-003; parent decision (phase gates) | The proof-exit report lists seven verdicts before any Phase 2 artifact exists. Each verdict is `PASS` or operator-deferred, except Proof G, which may instead be `PENDING-LINUX` with its Linux gate carried into the implementation matrix draft as `not-deferrable` | Proof-exit report; artifact dates and commits | `P0` | `not-deferrable` |
| `PE-FLOW-03` | Per-task harness placement and checkpoint-first restore are expressible for both Ship surfaces | P-002; P-004; `templates/agents/_ship.agent.md.tmpl` and `.github/agents/_ship.agent.md` anchors listed in section 6.7 | Proof E accepts only the canonical trace and rejects every listed mis-ordering | Proof E findings with verbatim anchors | `P1` | `not-deferrable` |
| `PE-FLOW-04` | A `FAIL`ed proof is re-run only under a new charter version | Parent decision (stop rules) | No second attempt of a failed proof question exists without a charter version bump | Findings artifacts; charter version history | `P1` | `not-deferrable` |

**(PE-1.7) Operator ruling on `PE-FLOW-04`.** The row text above is
unchanged. By the operator's ruling of 2026-09-25T13:27:40-07:00 ("3. Option
A"; section 3.6), from version 1.7 onward the row is read prospectively. Its
pass criterion is evaluated over the record minus one recorded historical
exception: Proof D run 4 (`36f65975`, PE-1.4). Proof D run 5 (`5976ff62`,
PE-1.5) is Proof D's admissible evidence. The exception list is closed. Any
other second attempt at a failed proof question without a version bump,
already recorded or made later, still breaches the row, and only a further
operator-approved version can add an exception. No verdict is relabelled,
and run 4's breach stays on the record.

### 7.5 INTERFACE

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-INTERFACE-01` | No public or caller-supplied traversal adapter; any test seam is private | Parent decision (B+D scope; removed obligations) | The Proof G helper has no adapter parameter; the implementation-matrix draft carries this row | Proof G source listing; matrix draft | `P1` | `deferred-to-implementation-matrix` (binding on proofs now) |
| `PE-INTERFACE-02` | Ship consumes a validated document, not a process status | P-012 (no silent fallback); constitution section V | Proof B truth table: every impostor yields `resolver-not-observed` and every genuine verdict is accepted | Proof B findings | `P1` | `not-deferrable` |
| `PE-INTERFACE-03` | Exactly one supported surface mapping, closed against the manifest | `.autoharness/harness-manifest.yaml:237-239`; parent decision section on stable boundaries | Proof C: unknown-but-well-formed surfaces yield `SURFACE_UNSUPPORTED`, which reduces to `UNRESOLVED` | Proof C findings | `P1` | `not-deferrable` |

### 7.6 SAFETY

Every Proof G case below is evaluated on each host. The Windows half must hold
at proof exit. The Linux half follows `linux-execution-gate` (section 6.9): a
Linux `PENDING` never counts as a pass, and Windows evidence never stands in
for it.

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-SAFETY-01` | Lexically invalid paths are rejected | Constitution section III (traversal attempts rejected) and section IV | Every Proof G lexical case returns its closed code on Windows, and on Linux when executed; a Linux `PENDING` is recorded as `PENDING` | Proof G per-host results | `P1` | `not-deferrable` (Linux half: `linux-execution-gate`) |
| `PE-SAFETY-02` | A resolved target outside its root is rejected, including static symlink and junction escapes; in-root links resolving inside are accepted | Constitution sections III and IV | Every Proof G resolved-path case behaves as specified on Windows, and on Linux when executed; a Linux `PENDING` is recorded as `PENDING` | Proof G per-host results | `P1` | `operator-deferrable` for the Windows symlink sub-case only, when the host lacks symlink privilege; the junction case is `not-deferrable`; Linux half: `linux-execution-gate` |
| `PE-SAFETY-03` | Static containment within the workspace root and the autoharness root | Constitution section III; parent decision threat model | Reads under `.autoharness/` succeed; escapes from either root fail; the Windows root comparison is case-insensitive; the Linux half holds when executed or is recorded `PENDING` | Proof G per-host results | `P1` | `not-deferrable` (Linux half: `linux-execution-gate`) |
| `PE-SAFETY-04` | Reads are bounded per file, in total and by count, with explicit exhaustion codes (PE-1.2) | Constitution section I (explicit error handling; silent failures forbidden); attempt 11 `S71` lineage; `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md` | Proof D run 2 passes under section 6.6 (PE-1.2), and the Proof G bound cases pass on Windows and on Linux when executed; a Linux `PENDING` is recorded as `PENDING` | Proof D run 2 and Proof G findings | `P1` | `not-deferrable` (Linux half of Proof G: `linux-execution-gate`) |
| `PE-SAFETY-05` | Every rejection is explicit and closed; there is no silent fallback or partial success | P-012; constitution sections I and V | No Proof B case, and no Proof G case on any executed host, returns success with missing or truncated content | Proofs B and G findings | `P1` | `not-deferrable` (Linux half of Proof G: `linux-execution-gate`) |
| `PE-SAFETY-06` | No artifact claims race, TOCTOU or hardlink-alias resistance | Parent decision (non-claims) | Text audit of proof artifacts and the matrix draft finds no such claim | Audit record in the proof-exit report | `P2-critical` | `not-deferrable` |
| `PE-SAFETY-07` | Non-regular targets and reserved device names are rejected | Constitution section III | The corresponding Proof G cases return closed codes on Windows, and on Linux when executed (reserved device names are Windows-only cases); a Linux `PENDING` is recorded as `PENDING` | Proof G per-host results | `P2-critical` | `not-deferrable` (Linux half: `linux-execution-gate`) |

### 7.7 DATA

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-DATA-01` | Member and global manifest reason codes are closed, with fixed precedence (PE-1.4) | Parent decision (closed `SurfaceSpec` map); attempt 11 `S70` and `S76` lineage; `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md` Decision 2 | Proof C run 2 maps every input class to exactly one outcome. Every code of the section 6.5 governing reason set and of the Stage candidate is reachable. Every governing code yields its governing state and exit, and each class 1b read-limit error yields `UNRESOLVED / 2` with the first-occurring `ReadErrorCode` | Proof C run 2 truth table and governing-set check | `P1` | `not-deferrable` |
| `PE-DATA-02` | The result schema and runtime outputs have exact parity (PE-1.4) | Constitution section V; `S76` lineage; section 6.5 | Proof C run 2: every output validates, every schema branch is reachable, mutated outputs are rejected, and an output for every governing code validates against the candidate schema | Proof C run 2 validation log | `P1` | `not-deferrable` |
| `PE-DATA-03` | The budget equation holds for every admitted member, candidate and recheck (PE-1.2) | Attempt 11 `S71` lineage; `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`; plan revision 12 lines 78 and 144 (frozen diagnostic record, superseded for the admitted range by the decision) | With the admitted range `1..48`, `C(N,U,rho) <= 256` and `C(N,U,1) + (N+1) <= 256` for every admitted input (`C_max = 202`, margin 54). No byte fit is claimed, and byte exhaustion is shown to be a bounded `UNRESOLVED / 2` failure. Every read-limit error at every read and recheck stage yields `UNRESOLVED / 2`, never `NO_HARNESS / 1` or `HARNESS_READY / 0` | Proof D run 2 derivation and exhaustive check (section 6.6) | `P1` | `not-deferrable` |
| `PE-DATA-04` | Manifest checksums are computed from raw staged blob bytes | `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md` section 1; the SHA-256-over-raw-LF-bytes convention recorded in `.autoharness/harness-manifest.yaml` entry notes | Proof F staged digest equals HEAD digest | Proof F transcript with both digests | `P1` | `not-deferrable` |

### 7.8 TASK

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-TASK-01` | Every proof respects the 2-hour rule | `.github/agents/_stage.agent.md` (2-hour rule); section 6.2 bounds | Every proof bound is at most 120 minutes, and recorded elapsed time is within its bound | Section 6.2; per-proof records | `P1` | `not-deferrable` |
| `PE-TASK-02` | Future shipments hold at most 6 tasks and 8 hours, are independently valuable, and carry derived two-axis sizing | `.github/agents/_stage.agent.md` Step 4; `docs/size-complexity-reference.md`; parent decision remediation budget | Applied at Phase 2 harvest; an overrun forces a split or re-charter, with escalation per P-013.6 | Phase 2 harvest report | `P1` | `deferred-to-implementation-matrix` |
| `PE-TASK-03` | No harvest before the implementation matrix is ratified | P-003; parent decision | No backlog item is created from lifecycle proofs before ratification | `git log` under `.backlogit/` | `P0` | `not-deferrable` |

### 7.9 EVIDENCE

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-EVIDENCE-01` | Each proof records its question, host OS and version, filesystem, interpreter, exact commands, raw outputs or their SHA-256, fixture listing, per-criterion verdict, elapsed time and file count (PE-1.4) | `.github/skills/spike/SKILL.md` Output and Phase 3; constitution section V; section 6.1 evidence handoff | Every Stage-authored findings artifact contains every listed field, taken from Ship's reported evidence. It also contains the recorded scratch path, the per-file fixture SHA-256 values, Ship's per-invocation gate results including the index refresh record, and its safety statement: fixture writes in scratch only, plus the separate tool-managed cache refresh (section 6.1) | Findings artifacts; Ship evidence reports | `P1` | `not-deferrable` |
| `PE-EVIDENCE-02` | Proof G platform evidence comes only from actual operating systems: Windows at proof entry; Linux at proof entry when a qualifying host exists, otherwise from Linux CI during implementation. Mocks, simulated platforms, a Windows volume mounted into Linux, and Windows evidence never stand in for Linux | Parent decision (platform mandate); P-010; section 6.9 | The evidence shows `platform.system()` as `Windows` with filesystem type at proof entry. For Linux it shows `Linux` with filesystem type, or it records Linux as `PENDING` (never `PASS`) with the gate carried into the implementation matrix draft as `not-deferrable` | Proof G host records; proof-exit report | `P1` | `not-deferrable` for Windows (an unavailable Windows host is `BLOCKED`); Linux half: `linux-execution-gate` |
| `PE-EVIDENCE-03` | P-004 evidence uses the exact canonical command and per-test marker attribution, and separates runner behavior from actor and policy evidence | P-004; `.github/skills/harness-architect/SKILL.md` Step 5.2; `.autoharness/harness-manifest.yaml` lines 472-473 | Proof A pass and required-rejection criteria are met. The runner half comes from an actual Ship execution of the exact command in a synthetic source-layout workspace. The policy half is Stage's static comparison with the written contract. No artifact claims that the actor accepted or refused a fixture, or presents scratch results as P-004 gate evidence for any task | Ship's Proof A transcript; Stage's Proof A static analysis | `P1` | `not-deferrable` |
| `PE-EVIDENCE-04` | Combined proofs keep separate verdicts and evidence | Section 6.1 combination rule | Each proof in a combined session has its own verdict block and time record | Findings artifacts | `P2` | `not-deferrable` |
| `PE-EVIDENCE-05` | Tool degradation is declared | P-012 | Each artifact records the engram, intercom, graphtor-docs and backlogit states | Findings headers | `P2` | `not-deferrable` |

### 7.10 ACTIVATE

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-ACTIVATE-01` | No activation occurs during proofs; Proof E's fixture is standalone (PE-1.7) | Governing decision revision 9 (PREPARE to VERIFY to ACTIVATE); P-010; sections 3.2, 3.3 and 3.6 | For each of `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md` and `.autoharness/harness-manifest.yaml`, the raw LF Git tracked blob at the proof-exit commit is identical to the raw Git tracked blob at the operator-approved snapshot `08787a4b` (blob IDs `4ccd7fdc2d134de485487acd75bfbc105d6f40ee`, `66933efaf085e7acff0db47f0bdc452a4fe58830` and `e4274043e66a104ca8cf9f43e0d4e939847ac30e`; raw-blob SHA-256 values in section 3.6), and `git status --porcelain` is empty for the three paths. The changes from `4acba14a` to `08787a4b` are an operator-approved frontmatter-only routing change to the mirror and a manifest checksum refresh, not the activation (section 3.6). The changes from `5bcb00e5` to `4acba14a` are P-010 role-permission setup and a checksum refresh, not the activation (section 3.3). The version 1.3 comparator `5bcb00e5` and the version 1.4 comparator `4acba14a` are kept as history in sections 3.2 and 3.3. Working-tree checkout bytes and a floating `HEAD` are never the comparator | `git rev-parse <proof-exit>:<path>` for the three paths; empty `git diff 08787a4b <proof-exit> --` for the three paths; raw-blob SHA-256 from `git cat-file blob`; `git status --porcelain` for the three paths | `P0` | `not-deferrable` |
| `PE-ACTIVATE-02` | The future activation of template, mirror and manifest checksum is one task and one commit | Governing decision revision 9 (activation is one task and one commit) | Checked at implementation | Implementation commit | `P1` | `deferred-to-implementation-matrix` |
| `PE-ACTIVATE-03` | Publication, execution and claim/closure gates stay distinct; a proof `PASS` confers no claim authority | `docs/decisions/2026-09-20-pr457-bounded-review-convergence-deliberation.md` (merging Stage artifacts confers no claim authority); P-002; P-020 | No proof artifact asserts publication or claim readiness | Text audit | `P1` | `not-deferrable` |

## 8. Proof exit

Proof exit is reached when every proof is `PASS`, or is `FAIL` or `BLOCKED`
with a recorded route, or (Proof G only) is `PENDING-LINUX` with its Linux
gate carried forward. The Stage-authored proof-exit report:

1. lists each proof verdict against its PE-1.7 rows. Verdicts recorded under
   PE-1.1, PE-1.2, PE-1.3, PE-1.4, PE-1.5 and PE-1.6 are listed as recorded,
   per sections 3.1 to 3.6. Proofs B and F are reported by their PE-1.4 run
   verdicts, with their historical `PASS` also listed. (PE-1.7) Proof D is
   reported by its run 5 verdict (PE-1.5, `5976ff62`), its admissible
   evidence, with run 4 (PE-1.4) listed as history and as the recorded
   `PE-FLOW-04` historical exception (section 3.6), and with run 2's
   historical `PASS` and runs 1 and 3 `FAIL` also listed. Proof C is
   reported by its latest
   recorded run (run 3 `FAIL` under PE-1.5 until a PE-1.6 run 4 is recorded),
   with run 1 `FAIL` and run 2 `BLOCKED` also listed. Proof E is reported by its PE-1.5 run 5 verdict, with
   its four earlier `BLOCKED` runs also listed. A historical verdict whose
   Ship invocations lack the section 6.1 refresh evidence never satisfies a
   proof-exit row by itself;
2. audits every `not-deferrable` row;
3. drafts, but does not ratify, the implementation acceptance matrix;
4. carries every Linux `PENDING` result into that draft as a `not-deferrable`
   execution and release gate, and states that cross-platform acceptance is
   not yet satisfied;
5. lists the operator decisions that remain open.

Any `FAIL` returns to architecture or charter. It never returns to a plan
rewrite.

## 9. Governance defaults for the next review epoch

These are **proposed defaults**. They are fixed before an epoch opens, and they
take effect only on operator ratification:

* **Frozen before the epoch.** Rubric version, persona set, severity mapping,
  reviewer route and lead reviewer. A route change pauses the epoch.
* **Stable finding lineage.** Finding IDs are tied to matrix rows. Residue gets
  a linked child. Nothing is carried forward without revalidation.
* **Check cadence.** One initial full review, then delta reviews, then one final
  full consistency pass.
* **Separate gates.** Publication, implementation (execution) and claim/closure
  are distinct gates.
* **Budgets.** At most two consolidated revisions per epoch. At most six tasks
  and eight hours per shipment. An overrun escalates per P-013.6 and ends in a
  split, a spike, a re-charter, risk acceptance, deferral or cancellation.
* **P2 publication rule.** The **proposed default** is that only
  matrix-critical `P2` blocks publication (open decision C4).
* **Reviewer lead and routing.** **Pending ratification (C4). Not selected
  here.** The working configuration, inspected read-only, declares no
  `model_routing.anchor_review` key. Any anchor route must be configured before
  the epoch opens.

## 10. Open decisions and next step

| Decision | Status | Gate |
|---|---|---|
| C1 - threat model and platforms | **Resolved** on 2026-09-23 (B+D; section 5) | - |
| C2 - release-unit split | Bounded proposal pending operator approval | Phase 2 |
| C3 - migration and the fate of `187-S` (retire or re-charter, never patch) | Bounded proposal pending operator approval | Phase 2 |
| C4 - `P2` publication policy, reviewer lead and routing | Bounded proposal pending operator approval | Phase 4 |

**Next step:** once charter version 1.1 is committed, the next handoff is
**Proof A to Ship** for verification-only execution under section 6.1, in the
one current worktree and in a named scratch directory. Ship mutates no source
file and no planning artifact. Stage then authors Proof A's findings from
Ship's evidence. No branch or worktree beyond the current one is used, no
backlog item or shipment is created or claimed, and no second release-unit PR
is opened. If a P-001 conflict with an active release unit, or any other
per-invocation gate, rejects the execution, Ship halts and returns to the
operator. `187-S` remains queued and is not claim-ready.

**Version 1.2 addendum (Proof D run 2).** Proof D run 2 may be handed to Ship
for verification-only execution under section 6.1 once version 1.2 is
committed, unless the operator vetoes the decided bound first. It uses the
section 6.6 (PE-1.2) inputs, with its own 45-minute and one-file bound, in a new
scratch directory. Run 2 does not pool run 1's budget. A read-only check at
`b6366cef` found that run 1's scratch path `.proof-scratch/` no longer exists.
Its hygiene closure is left for the proof-exit report, and it does not change
any verdict. Until run 2 is recorded, Proof D's verdict is run 1 `FAIL`.

**Version 1.3 addendum (Proof E).** A fresh Proof E execution may be handed to
Ship for verification-only execution under section 6.1 once version 1.3 is
committed, unless the operator vetoes the version 1.3 terms or baseline first.
It is judged against section 6.7 (PE-1.3) and must meet next steps 2 to 6 of
the Proof E findings (scratch path recorded before the first write, anchors
read from Git blobs, verbatim canonical and negative traces including both N2
forms, and the complete `PE-EVIDENCE-01` handoff). Next step 1 is settled by
section 3.2. Its time and file bound is section 6.2's 60 minutes and two
disposable files. Until that execution is recorded, Proof E's verdict is
PE-1.2 `BLOCKED`.

**Version 1.4 addendum (index refresh, setup snapshot and Proof C run 2).**
Once version 1.4 is committed, and unless the operator vetoes it first, every
Ship proof invocation follows section 6.1 (PE-1.4). Ship runs its own
Step 0.1 refresh with fail-closed handling before any semantic backlog read.
It uses bounded, active-filtered P-001 projections and an unfiltered,
bounded checkpoint anomaly scan. It checks the `4acba14a` blobs of the three
`PE-ACTIVATE-01` paths before the first write. The runs still required
before proof exit are listed in the section 3.3 table: Proof C run 2 under
section 6.5 (PE-1.4); new PE-1.4 runs of Proofs B, D and F; fresh PE-1.4
executions of Proofs A and E; and Proof G's first run (Windows, with Linux
`PENDING` unless section 6.9 is met inside the current working directory).
Section 6.1 allows Proof C run 2 and the Proof D run to share one Ship
invocation, each keeping its own verdict, evidence and bound. Until each run
is recorded, each proof's verdict stays as the section 3.3 table lists it.
`187-S` stays queued and is not claim-ready.

**Version 1.5 addendum (Proof E run 5).** Once version 1.5 is committed, and
unless the operator vetoes it first, a fresh Proof E run 5 may be handed to
Ship for verification-only execution. Run 5 follows these rules:

* It follows section 6.1 (PE-1.4, unchanged): Ship's own Step 0.1 refresh,
  with fail-closed handling; bounded, active-filtered P-001 projections; the
  unfiltered, bounded checkpoint anomaly scan; and the `4acba14a` blob and
  porcelain check of the three `PE-ACTIVATE-01` paths before the first write.
  Run 5 uses a new scratch directory recorded before the first write and
  its own 60-minute, two-file bound.
* It is judged against section 6.7 (PE-1.5). The fixture reads both surfaces
  from `HEAD` raw Git blobs. It treats the two added template spans as
  planned replacements: it checks that each span exists as an anchor, and it
  does not treat either span as retained text.
* The fixture keeps every run 4 case. It must also reject at least these
  two traces:
  * a memory-context or next-action restore before the enumeration, the
    anomaly scan, and the selection, owner and schema validation and
    confirmation;
  * a `context-overflow` memory-checkpoint resume without selection,
    validation and confirmation.
* It must still accept the canonical traces, including the zero-candidate
  normal continuation. The run 4 fixture may be reused as a base, but by
  itself it does not exercise these rejections.
* Every negative must be graded by its intended reason, with no expected
  value passed to the checker, and the full `PE-EVIDENCE-01` handoff is
  required.

Until run 5 is recorded, Proof E's verdict is run 4 `BLOCKED` (PE-1.4).
Nothing here authorizes an activation, a claim, a harvest or any Ship-surface
or manifest edit. `187-S` stays queued and is not claim-ready.

**Version 1.6 addendum (Proof C clock rule).** Version 1.6 authorizes no run.
Proof C's verdict is run 3 `FAIL` (PE-1.5) until a run 4 is recorded. Run 4
may be handed to Ship only after an operator authorization that names "Proof
C run 4 under PE-1.6". It is judged against section 6.5 with the PE-1.6
clock (T0 to T1, at most 120 minutes, section 3.5) and section 6.1 unchanged.
Two operator decisions stay open: the ruling on `PE-FLOW-04` for Proof D run 4
(section 3.5), and any veto of this version. Nothing here authorizes an
activation, a claim, a harvest or any Ship-surface or manifest edit.

**Version 1.7 addendum (comparator rebaseline and `PE-FLOW-04` ruling).**
Version 1.7 authorizes no run. From version 1.7 onward, `PE-ACTIVATE-01` and
the section 6.1 blob check before a Ship invocation's first write use the
`08787a4b` blobs (section 3.6). The `4acba14a` blobs named in the version 1.4
and 1.5 addenda above apply only to runs under those versions. The
`PE-FLOW-04` ruling that the version 1.6 addendum left open is now made
(Option A; section 3.6 and the note under the section 7.4 table). Proof D is
reported by run 5 (section 8 item 1). The operator's order to refresh the
implementation matrix and re-present it is a Stage work order outside this
charter. It ratifies nothing: the implementation matrix stays a draft until
the operator ratifies it after proof exit (section 3). C2, C3 and C4 stay
open. Nothing here authorizes an activation, a claim, a harvest, a plan, a
review epoch or any Ship-surface or manifest edit. `187-S` stays queued and
is not claim-ready.

## Cross-references

* Proof D run 1 findings: `docs/decisions/2026-09-23-read-budget-proof-d-spike.md`
* Version 1.2 decision: `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`
* Proof E findings (version 1.3 input): `docs/decisions/2026-09-24-ship-activation-proof-e-spike.md`
* Proof E runs 2 and 3 findings: `docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md`, `docs/decisions/2026-09-24-ship-activation-proof-e-run3-spike.md`
* Proof E run 4 findings (version 1.5 input): `docs/decisions/2026-09-24-ship-activation-proof-e-run4-spike.md`
* Proof C run 1 findings (version 1.4 input): `docs/decisions/2026-09-24-surface-taxonomy-proof-c-spike.md`
* Proof C run 3 findings (version 1.6 input): `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run3-spike.md`
* Proof D run 5 findings (`PE-FLOW-04` record): `docs/decisions/2026-09-24-read-budget-proof-d-run5-spike.md`
* Proof C run 4 findings (PE-1.6; `4c6e2701`, including the working-tree disclosure): `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run4-spike.md`
* Proof-exit report (version 1.7 input, OD-2; `9c83517d`): `docs/decisions/2026-09-24-lifecycle-proof-exit-spike.md`
* Operator-approved snapshot (version 1.7 comparator): commit `08787a4b`
* Proof A, B, D run 2 and F findings (version 1.4 refresh audit): `docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md`, `docs/decisions/2026-09-24-cli-authenticity-proof-b-spike.md`, `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md`, `docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md`
* Parent decision: `docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md`
* Governing decision: `docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md` (revision 9)
* Frozen plan: `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` (revision 12)
* Verdict manifest: `docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md`
* Terminal attempt: `docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-11.md`
* Constitution: `.github/instructions/constitution.instructions.md`
* Policies: `.github/policies/workflow-policies.md`
* Escalation: `.github/instructions/escalation-protocol.instructions.md`
* Skills: `.github/skills/spike/SKILL.md`, `.github/skills/plan-review/SKILL.md`, `.github/skills/harness-architect/SKILL.md`, `.github/skills/file-lock/SKILL.md`
* Ship surfaces: `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md` (also the Ship Role Boundary)
* Stage agent: `.github/agents/_stage.agent.md`
* Role enforcement: `.github/instructions/role-enforcement.instructions.md`
* Sizing reference: `docs/size-complexity-reference.md`
* Manifest: `.autoharness/harness-manifest.yaml`
* Learnings: `docs/compound/093-S-review-loop-convergence.md`, `docs/compound/097-S-canonical-unittest-gate.md`, `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`
* Related decision: `docs/decisions/2026-09-20-pr457-bounded-review-convergence-deliberation.md`
