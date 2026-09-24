---
title: "Lifecycle proof-entry charter and acceptance matrix, version 1.3"
description: "Operator-approved proof-entry charter for the Ship pre-task harness-generation lifecycle, issued under the 2026-09-23 Option B governance reset with proportionate Option D containment. Freezes lifecycle plan revision 12 and review attempt 11 as diagnostic evidence; fixes the proportionate threat model (operator-controlled local workspace, ordinary static containment on actual Windows and Linux, no race or hardlink-alias claims); defines a seven-proof bounded portfolio with narrow questions, time and file bounds and pass/fail criteria; and fixes acceptance matrix PE-1.1, in which every row carries an existing normative source, a verifiable pass criterion, evidence, violation severity and deferral status. Version 1.1 is an operator-approved correction of proof actor and timing only: Stage performs read-only analysis and authors the findings; Ship runs verification-only disposable fixture commands in a named scratch directory inside the one current worktree; no additional worktree is used; Linux evidence that cannot be produced at proof entry is PENDING, never PASS, and becomes a non-waivable execution and release gate. Frozen for proof entry only: the implementation acceptance matrix is ratified after proof evidence and before any new review epoch. Version 1.2 (matrix PE-1.2) changes Proof D only, after Proof D failed under PE-1.1: it re-charters section 6.6 and rows PE-DATA-03 and PE-SAFETY-04 against the decided admitted maximum of 48 members, the unchanged max_files=256, an explicit byte non-guarantee (byte exhaustion is a bounded UNRESOLVED failure, never success) and the read-limit exhaustion mapping to UNRESOLVED / 2 at every read and recheck stage; every other row, proof and verdict is unchanged. Version 1.3 (matrix PE-1.3) changes only two terms of Proof E (section 6.7) and the PE-ACTIVATE-01 comparator, after Proof E was recorded BLOCKED under PE-1.2: 'checkpoint validate-and-resolve' means unique selection plus owner and schema validation before restore, never a status resolution before resume; 'retained text' means the text kept after the planned activation edits; and PE-ACTIVATE-01 compares raw Git blobs at the operator-approved snapshot 5bcb00e5 instead of 082df7b2. No proof is re-run or re-labelled and Proof E stays BLOCKED. Subordinate to the constitution and the workflow policy registry; overrides nothing."
doc_type: decision
artifact_class: proof-entry-charter
source: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
date: 2026-09-23
status: decided
decision_status: decided
charter_version: "1.3"
matrix_id: PE-1.3
supersedes_version: "1.2"
superseded_version_commit: 286aa4af
version_history:
  - {version: "1.0", matrix_id: PE-1.0, commit: 2e3c98a1}
  - {version: "1.1", matrix_id: PE-1.1, commit: 1ad7c03a, scope: "proof actor and timing only"}
  - {version: "1.2", matrix_id: PE-1.2, commit: 286aa4af, scope: "Proof D only (section 6.6, PE-DATA-03, PE-SAFETY-04)", decision: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md}
  - {version: "1.3", matrix_id: PE-1.3, scope: "Proof E terms (section 6.7) and PE-ACTIVATE-01 comparator only", record: "section 3.2", findings: docs/decisions/2026-09-24-ship-activation-proof-e-spike.md}
freeze_scope: proof-entry-only
implementation_matrix_status: not-ratified
deciders: operator, Stage
operator_approval: "2026-09-23 - Option B governance reset combined with the proportionate Option D containment scope"
version_1_1_operator_approval: "2026-09-23 - operator 'Proceed' on the exact proposed correction: PE-1.0 to PE-1.1, proof actor and timing only (no Stage executable proof and no extra worktree; Ship verification-only fixture execution in the one current worktree; Stage read-only analysis and findings authorship; Linux PENDING, never PASS, when no Linux host exists at proof entry)"
version_1_2_operator_approval: "2026-09-24 - operator instruction to act on Proof D's reopened decisions, authorizing a clearly identified versioned PE-1.2 change limited to Proof D (preserve Proof A and F verdicts; keep B, C, E and G separate); the concrete bound was selected by Stage under that bounded delegation and may be vetoed by the operator before the Proof D run 2 handoff"
head_at_version_1_2: b6366cef
version_1_3_operator_approval: "2026-09-24 - operator order 'Don't just tell me what is required, act on it' on Proof E's BLOCKED findings, with the Orchestrator's relayed selection of the readings dictated by the higher Ship recovery protocol (validate-and-resolve = selection plus owner/schema validation before restore; status resolution only after a confirmed successful resume) and of post-activation retained text, and of the operator-approved snapshot 5bcb00e5 as the PE-ACTIVATE-01 baseline; limited to section 6.7 terms and the PE-ACTIVATE-01 comparator; the operator may veto before the fresh Proof E handoff"
head_at_version_1_3: a04e1e5a
activation_baseline_commit: 5bcb00e5
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

# Lifecycle proof-entry charter (version 1.3)

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
3. fixes acceptance matrix **PE-1.3**, the only set of criteria a proof or a
   proof-phase artifact is judged against from version 1.3 onward (section 3
   explains how verdicts recorded under PE-1.1 and PE-1.2 carry forward).

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
| What is frozen | This charter and matrix PE-1.3, for **proof entry only** |
| What is not ratified | The implementation acceptance matrix. It is drafted from proof evidence and ratified by the operator **after** proof exit and **before** any new review epoch opens |
| How it changes | Only by an operator-approved version bump (1.4, 2.0, ...), recorded as a new charter version. Proof authors and proof executors cannot edit rows mid-proof |
| Current version | 1.3 (matrix PE-1.3), approved on 2026-09-24 under the operator's bounded delegation (frontmatter `version_1_3_operator_approval`). It supersedes version 1.2 (`286aa4af`), which changed Proof D only. Version 1.2 superseded version 1.1 (`1ad7c03a`), and version 1.1 superseded version 1.0 (`2e3c98a1`) and corrected proof actor and timing only. See section 3.1 for the version 1.2 change and section 3.2 for the exact version 1.3 change |
| Change requests | A requirement discovered during a proof that is not a PE-1.3 row is recorded as a change request in that proof's evidence. It is not a proof-phase blocker |

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

## 4. Scope

### 4.1 In scope

* The seven proofs in section 6: Stage read-only analysis, Ship
  verification-only fixture execution in an untracked scratch directory, and
  the Stage-authored findings artifacts.
* One Stage-authored proof-exit report that lists every proof verdict against
  PE-1.3 (with the section 3.1 and 3.2 carry-forward of verdicts recorded under
  PE-1.1 and PE-1.2).

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
  re-charter of `187-S`.
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
* **Scratch directory.** Ship writes only inside one named per-session
  scratch directory inside the current working directory,
  `.proof-scratch/{proof}-{YYYYMMDD-HHMMSS}/`, whose resolved path Ship records
  before the first write. Ship never writes production source, templates,
  tests, schemas, configuration, the harness manifest, backlog files, or any
  deliberation, spike, plan or review artifact (the Ship Role Boundary in
  `.github/agents/_ship.agent.md` forbids planning artifacts). Scratch content
  is never staged or committed. Ship removes only its own scratch directory,
  and only after verifying that the resolved path equals the recorded scratch
  path inside the current working directory and that cleanup is approved in
  the handoff or by the operator.
* **Per-invocation gates.** Before every Ship invocation, Ship performs its
  fail-closed P-010 self-check (`.github/instructions/role-enforcement.instructions.md`)
  and evaluates P-001 (single release unit), P-002 (no claim and no
  `harness-ready` consumption), P-011 (branch-before-mutation, as written) and
  P-016 (`git worktree list --porcelain` shows exactly the current worktree).
  No exemption from any policy is assumed. If the active release unit
  conflicts under P-001, or any gate rejects verification-only execution,
  Ship stops, reports the rejecting gate and its evidence, and returns to the
  operator. There is no role workaround: no Stage execution, no additional
  worktree, no substitute actor.
* **Evidence handoff.** For each invocation Ship reports: the recorded scratch
  path; each bounded command verbatim; stdout, stderr and exit status (raw,
  or by SHA-256 when large); host facts; the fixture listing with a SHA-256
  per file; elapsed time; the per-invocation gate results; and a safety
  statement showing `git status --porcelain` identical before and after
  apart from the scratch directory. Stage writes the immutable findings
  artifact from that evidence and records the verdict. Ship writes no
  findings artifact.
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
  analysis and its Ship execution together.
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
| C | Is a one-entry `SurfaceSpec` with total member and manifest reason codes a closed, schema-parity-complete truth table? | 75m | 2 disposable | Windows | `PE-INTERFACE-03`, `PE-DATA-01`, `PE-DATA-02` | `S70`, `S76` |
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

### 6.5 Proof C - one-entry SurfaceSpec and total reason truth table

* **Question.** Is the taxonomy closed, and does the schema match the runtime
  exactly?
* **Actors.** Stage derives the truth table, the input classes, the reason
  codes and their precedence, and the candidate schema, read-only. Ship runs
  the enumeration, schema-validation and mutation fixture in scratch. Stage
  records the verdict from Ship's output.
* **Setup.** Exactly one supported mapping: surface `harness-architect` to
  installed `.github/skills/harness-architect/SKILL.md` and template
  `skills/harness-architect/SKILL.md.tmpl`, as tracked by the manifest entry at
  `.autoharness/harness-manifest.yaml:237-239` (at `082df7b2`).
* **Pass.** An exhaustive enumeration over bounded input classes maps each
  class to exactly one `(state, exit, reason_code)`. The member classes cover
  one supported label, `harness-surface:none`, missing, duplicate, malformed
  and unknown-but-well-formed labels. Unknown-but-well-formed always yields
  `SURFACE_UNSUPPORTED`, which reduces to `UNRESOLVED`, never `NO_HARNESS`.
  Global manifest failure codes are enumerated with a fixed precedence. Every
  code is reachable. Every runtime output validates against the candidate
  schema, every schema branch is produced by at least one input, and mutated
  outputs are rejected.
* **Fail.** Any input maps to zero or more than one outcome, any code is
  unreachable, or schema and runtime disagree.

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
    per-task step 1 Claim (line 357).

  T1-T3 are the per-task sub-steps of the canonical body in frozen plan
  revision 12 (line 227): T1 resolves the actor surface and keeps exits 0, 1
  and 2 distinct; T2 invokes harness-architect for the current task on exit 0;
  T3 requires the current task's valid marker-bearing RED evidence before the
  task proceeds to Claim. Plan revision 12 line 225, which places a mirror
  section before the Step 2 heading, is a frozen diagnostic input and does not
  set this placement. The Crash-Resumption protocols' recovery order (template
  line 1006, mirror line 170) is retained text. Neither file is edited during
  proofs. A mismatch between current text and the planned post-activation text
  is an expected input to this proof, not by itself a `FAIL`.
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

## 7. Acceptance matrix PE-1.3

PE-1.3 equals PE-1.2 except row `PE-ACTIVATE-01`, marked "(PE-1.3)"
(section 3.2). PE-1.2 equals PE-1.1 except rows `PE-DATA-03` and
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
| `PE-AUTH-01` | Proof-phase work stays inside the Stage and Ship role boundaries | P-010; `.github/agents/_stage.agent.md` Role Boundary; `.github/agents/_ship.agent.md` Role Boundary and P-010 self-check | Every proof-phase commit is a Stage commit that changes only `docs/decisions/*-spike.md` findings or the proof-exit report. Stage runs no fixture command, build, test suite or lint and writes no test, source or configuration file. Ship's verification-only execution writes only its recorded scratch directory, commits nothing, and performs no claim, task move, branch, PR, push, shipment or label mutation | `git show --name-only` for each proof-phase commit; Stage session log; Ship's per-invocation command log and before/after `git status --porcelain` | `P0` | `not-deferrable` |
| `PE-AUTH-02` | No additional worktree is used; executable verification runs only in the one current worktree, under per-invocation policy gates | P-016; P-011; P-001; P-002; `.github/agents/_ship.agent.md` Role Boundary; section 6.1 | `git worktree list --porcelain` shows exactly the current worktree before, during and after every Ship invocation. Each invocation records its P-010 self-check and its P-001, P-002, P-011 and P-016 results. Any rejection halted execution and was returned to the operator with no workaround | Worktree listings and per-invocation gate records in Ship's reported evidence | `P1` | `not-deferrable` |
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
| `PE-DATA-01` | Member and global manifest reason codes are closed, with fixed precedence | Parent decision (closed `SurfaceSpec` map); attempt 11 `S70` and `S76` lineage | Proof C maps every input class to exactly one outcome, and every code is reachable | Proof C truth table | `P1` | `not-deferrable` |
| `PE-DATA-02` | The result schema and runtime outputs have exact parity | Constitution section V; `S76` lineage | Proof C: every output validates, every schema branch is reachable, mutated outputs are rejected | Proof C validation log | `P1` | `not-deferrable` |
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
| `PE-EVIDENCE-01` | Each proof records its question, host OS and version, filesystem, interpreter, exact commands, raw outputs or their SHA-256, fixture listing, per-criterion verdict, elapsed time and file count | `.github/skills/spike/SKILL.md` Output and Phase 3; constitution section V; section 6.1 evidence handoff | Every Stage-authored findings artifact contains every listed field, taken from Ship's reported evidence, plus the recorded scratch path, the per-file fixture SHA-256 values, Ship's per-invocation gate results and its scratch-only safety statement | Findings artifacts; Ship evidence reports | `P1` | `not-deferrable` |
| `PE-EVIDENCE-02` | Proof G platform evidence comes only from actual operating systems: Windows at proof entry; Linux at proof entry when a qualifying host exists, otherwise from Linux CI during implementation. Mocks, simulated platforms, a Windows volume mounted into Linux, and Windows evidence never stand in for Linux | Parent decision (platform mandate); P-010; section 6.9 | The evidence shows `platform.system()` as `Windows` with filesystem type at proof entry. For Linux it shows `Linux` with filesystem type, or it records Linux as `PENDING` (never `PASS`) with the gate carried into the implementation matrix draft as `not-deferrable` | Proof G host records; proof-exit report | `P1` | `not-deferrable` for Windows (an unavailable Windows host is `BLOCKED`); Linux half: `linux-execution-gate` |
| `PE-EVIDENCE-03` | P-004 evidence uses the exact canonical command and per-test marker attribution, and separates runner behavior from actor and policy evidence | P-004; `.github/skills/harness-architect/SKILL.md` Step 5.2; `.autoharness/harness-manifest.yaml` lines 472-473 | Proof A pass and required-rejection criteria are met. The runner half comes from an actual Ship execution of the exact command in a synthetic source-layout workspace. The policy half is Stage's static comparison with the written contract. No artifact claims that the actor accepted or refused a fixture, or presents scratch results as P-004 gate evidence for any task | Ship's Proof A transcript; Stage's Proof A static analysis | `P1` | `not-deferrable` |
| `PE-EVIDENCE-04` | Combined proofs keep separate verdicts and evidence | Section 6.1 combination rule | Each proof in a combined session has its own verdict block and time record | Findings artifacts | `P2` | `not-deferrable` |
| `PE-EVIDENCE-05` | Tool degradation is declared | P-012 | Each artifact records the engram, intercom, graphtor-docs and backlogit states | Findings headers | `P2` | `not-deferrable` |

### 7.10 ACTIVATE

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-ACTIVATE-01` | No activation occurs during proofs; Proof E's fixture is standalone (PE-1.3) | Governing decision revision 9 (PREPARE to VERIFY to ACTIVATE); P-010; section 3.2 | For each of `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md` and `.autoharness/harness-manifest.yaml`, the raw LF Git tracked blob at the proof-exit commit is identical to the raw Git tracked blob at the operator-approved snapshot `5bcb00e5` (blob IDs `a3407080665c874e6db742a467bcd79ce97d2666`, `5f397d0f1f2c8ce8dcded360a73a2a0d120ffc3a` and `17ae787d492fe06788ce21ae6fab29a26b3c4139`; raw-blob SHA-256 values in section 3.2), and `git status --porcelain` is empty for the three paths. Working-tree checkout bytes and a floating `HEAD` are never the comparator | `git rev-parse <proof-exit>:<path>` for the three paths; empty `git diff 5bcb00e5 <proof-exit> --` for the three paths; raw-blob SHA-256 from `git cat-file blob`; `git status --porcelain` for the three paths | `P0` | `not-deferrable` |
| `PE-ACTIVATE-02` | The future activation of template, mirror and manifest checksum is one task and one commit | Governing decision revision 9 (activation is one task and one commit) | Checked at implementation | Implementation commit | `P1` | `deferred-to-implementation-matrix` |
| `PE-ACTIVATE-03` | Publication, execution and claim/closure gates stay distinct; a proof `PASS` confers no claim authority | `docs/decisions/2026-09-20-pr457-bounded-review-convergence-deliberation.md` (merging Stage artifacts confers no claim authority); P-002; P-020 | No proof artifact asserts publication or claim readiness | Text audit | `P1` | `not-deferrable` |

## 8. Proof exit

Proof exit is reached when every proof is `PASS`, or is `FAIL` or `BLOCKED`
with a recorded route, or (Proof G only) is `PENDING-LINUX` with its Linux
gate carried forward. The Stage-authored proof-exit report:

1. lists each proof verdict against its PE-1.3 rows (verdicts recorded under
   PE-1.1 and PE-1.2 on unchanged rows carry forward per sections 3.1 and 3.2;
   Proof D is reported by its run 2 verdict, with run 1 `FAIL` also listed;
   Proof E is reported by its PE-1.3 execution verdict, with the PE-1.2
   `BLOCKED` also listed);
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

## Cross-references

* Proof D run 1 findings: `docs/decisions/2026-09-23-read-budget-proof-d-spike.md`
* Version 1.2 decision: `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`
* Proof E findings (version 1.3 input): `docs/decisions/2026-09-24-ship-activation-proof-e-spike.md`
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
