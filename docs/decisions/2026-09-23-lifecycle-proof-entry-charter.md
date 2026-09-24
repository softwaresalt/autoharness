---
title: "Lifecycle proof-entry charter and acceptance matrix, version 1.1"
description: "Operator-approved proof-entry charter for the Ship pre-task harness-generation lifecycle, issued under the 2026-09-23 Option B governance reset with proportionate Option D containment. Freezes lifecycle plan revision 12 and review attempt 11 as diagnostic evidence; fixes the proportionate threat model (operator-controlled local workspace, ordinary static containment on actual Windows and Linux, no race or hardlink-alias claims); defines a seven-proof bounded portfolio with narrow questions, time and file bounds and pass/fail criteria; and fixes acceptance matrix PE-1.1, in which every row carries an existing normative source, a verifiable pass criterion, evidence, violation severity and deferral status. Version 1.1 is an operator-approved correction of proof actor and timing only: Stage performs read-only analysis and authors the findings; Ship runs verification-only disposable fixture commands in a named scratch directory inside the one current worktree; no additional worktree is used; Linux evidence that cannot be produced at proof entry is PENDING, never PASS, and becomes a non-waivable execution and release gate. Frozen for proof entry only: the implementation acceptance matrix is ratified after proof evidence and before any new review epoch. Subordinate to the constitution and the workflow policy registry; overrides nothing."
doc_type: decision
artifact_class: proof-entry-charter
source: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
date: 2026-09-23
status: decided
decision_status: decided
charter_version: "1.1"
matrix_id: PE-1.1
supersedes_version: "1.0"
superseded_version_commit: 2e3c98a1
freeze_scope: proof-entry-only
implementation_matrix_status: not-ratified
deciders: operator, Stage
operator_approval: "2026-09-23 - Option B governance reset combined with the proportionate Option D containment scope"
version_1_1_operator_approval: "2026-09-23 - operator 'Proceed' on the exact proposed correction: PE-1.0 to PE-1.1, proof actor and timing only (no Stage executable proof and no extra worktree; Ship verification-only fixture execution in the one current worktree; Stage read-only analysis and findings authorship; Linux PENDING, never PASS, when no Linux host exists at proof entry)"
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

# Lifecycle proof-entry charter (version 1.1)

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
3. fixes acceptance matrix **PE-1.1**, the only set of criteria a proof or a
   proof-phase artifact is judged against.

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
| What is frozen | This charter and matrix PE-1.1, for **proof entry only** |
| What is not ratified | The implementation acceptance matrix. It is drafted from proof evidence and ratified by the operator **after** proof exit and **before** any new review epoch opens |
| How it changes | Only by an operator-approved version bump (1.2, 2.0, ...), recorded as a new charter version. Proof authors and proof executors cannot edit rows mid-proof |
| Current version | 1.1, operator-approved on 2026-09-23. It supersedes version 1.0 (`2e3c98a1`), which assigned executable proofs to a Stage spike worktree that the Stage role boundary does not permit. Version 1.1 corrects proof actor and timing only. The threat model, the acceptance criteria, the seven proof questions and the evidence standards are unchanged, and every row keeps its ID. Proofs are judged against PE-1.1 only |
| Change requests | A requirement discovered during a proof that is not a PE-1.1 row is recorded as a change request in that proof's evidence. It is not a proof-phase blocker |

## 4. Scope

### 4.1 In scope

* The seven proofs in section 6: Stage read-only analysis, Ship
  verification-only fixture execution in an untracked scratch directory, and
  the Stage-authored findings artifacts.
* One Stage-authored proof-exit report that lists every proof verdict against
  PE-1.1.

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
| D | Does one budget equation over every admitted member, candidate and recheck fit the read limits at the admitted maximum? | 45m | 1 disposable | any | `PE-DATA-03`, `PE-SAFETY-04` | `S71` |
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

### 6.6 Proof D - budget equation

* **Question.** Can the admitted maximum membership intrinsically exhaust the
  read budget?
* **Actors.** Stage derives `C(N)` read-only. Ship runs the exhaustive check
  in scratch. Stage records the verdict from Ship's output.
* **Setup.** Derive a closed-form claim count `C(N)` over every claim source:
  queue candidates, archive candidates, stable absence entries, manifest
  reads, template reads, installed reads, and ledger rechecks. Revision 12's
  values (`max_files=256`, membership `1..512`) are diagnostic inputs only.
* **Pass.** `C(N)` is checked exhaustively for every admitted `N` and for the
  real `187-S` membership (seventeen manifest items). `C(N_max)` fits the
  chosen file and byte limits with a recorded margin. Budget exhaustion maps to
  an explicit reducer class that yields `UNRESOLVED`, never `NO_HARNESS`.
* **Fail.** Any admitted `N` exceeds the budget. The remedy (a lower admitted
  bound, a larger budget, or a different read plan) is an architecture change
  routed to the charter.

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
  cursor restore before checkpoint validate-and-resolve; the harness step
  before checkpoint validation; the consumer proceeding on process status
  without a validated document; and divergent placement between template and
  mirror.
* **Fail.** No single state machine satisfies both files without contradicting
  retained text. That reopens the activation design.
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

## 7. Acceptance matrix PE-1.1

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
| `PE-SAFETY-04` | Reads are bounded per file, in total and by count, with explicit exhaustion codes | Constitution section I (explicit error handling; silent failures forbidden); attempt 11 `S71` lineage | The Proof D equation passes, and the Proof G bound cases pass on Windows and on Linux when executed; a Linux `PENDING` is recorded as `PENDING` | Proofs D and G findings | `P1` | `not-deferrable` (Linux half of Proof G: `linux-execution-gate`) |
| `PE-SAFETY-05` | Every rejection is explicit and closed; there is no silent fallback or partial success | P-012; constitution sections I and V | No Proof B case, and no Proof G case on any executed host, returns success with missing or truncated content | Proofs B and G findings | `P1` | `not-deferrable` (Linux half of Proof G: `linux-execution-gate`) |
| `PE-SAFETY-06` | No artifact claims race, TOCTOU or hardlink-alias resistance | Parent decision (non-claims) | Text audit of proof artifacts and the matrix draft finds no such claim | Audit record in the proof-exit report | `P2-critical` | `not-deferrable` |
| `PE-SAFETY-07` | Non-regular targets and reserved device names are rejected | Constitution section III | The corresponding Proof G cases return closed codes on Windows, and on Linux when executed (reserved device names are Windows-only cases); a Linux `PENDING` is recorded as `PENDING` | Proof G per-host results | `P2-critical` | `not-deferrable` (Linux half: `linux-execution-gate`) |

### 7.7 DATA

| ID | Requirement | Normative source | Pass criterion | Evidence | Severity | Deferral |
|---|---|---|---|---|---|---|
| `PE-DATA-01` | Member and global manifest reason codes are closed, with fixed precedence | Parent decision (closed `SurfaceSpec` map); attempt 11 `S70` and `S76` lineage | Proof C maps every input class to exactly one outcome, and every code is reachable | Proof C truth table | `P1` | `not-deferrable` |
| `PE-DATA-02` | The result schema and runtime outputs have exact parity | Constitution section V; `S76` lineage | Proof C: every output validates, every schema branch is reachable, mutated outputs are rejected | Proof C validation log | `P1` | `not-deferrable` |
| `PE-DATA-03` | The budget equation holds for every admitted member, candidate and recheck | Attempt 11 `S71` lineage; plan revision 12 lines 78 and 144 (diagnostic inputs) | `C(N) <= max_files` for every admitted `N`; exhaustion yields `UNRESOLVED` | Proof D derivation and exhaustive check | `P1` | `not-deferrable` |
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
| `PE-ACTIVATE-01` | No activation occurs during proofs; Proof E's fixture is standalone | Governing decision revision 9 (PREPARE to VERIFY to ACTIVATE); P-010 | Both Ship surfaces and the manifest are byte-identical to `082df7b2` at proof exit | `git diff` of the three paths | `P0` | `not-deferrable` |
| `PE-ACTIVATE-02` | The future activation of template, mirror and manifest checksum is one task and one commit | Governing decision revision 9 (activation is one task and one commit) | Checked at implementation | Implementation commit | `P1` | `deferred-to-implementation-matrix` |
| `PE-ACTIVATE-03` | Publication, execution and claim/closure gates stay distinct; a proof `PASS` confers no claim authority | `docs/decisions/2026-09-20-pr457-bounded-review-convergence-deliberation.md` (merging Stage artifacts confers no claim authority); P-002; P-020 | No proof artifact asserts publication or claim readiness | Text audit | `P1` | `not-deferrable` |

## 8. Proof exit

Proof exit is reached when every proof is `PASS`, or is `FAIL` or `BLOCKED`
with a recorded route, or (Proof G only) is `PENDING-LINUX` with its Linux
gate carried forward. The Stage-authored proof-exit report:

1. lists each proof verdict against its PE-1.1 rows;
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

## Cross-references

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
