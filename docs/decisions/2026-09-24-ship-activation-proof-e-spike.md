---
title: "Proof E - Ship per-task actor and checkpoint-first state machine: findings (BLOCKED)"
source: "docs/decisions/2026-09-24-ship-activation-proof-e-spike.md"
doc_type: decision
description: "Stage-authored Proof E findings under charter PE-1.2 section 6.7, which PE-1.2 leaves unchanged. Stage re-read the section 6.7 anchors read-only at a0079ac0: they sit at the charter's line numbers. Template Step 2 runs harness generation once, up front, and Step 3 filters every harness-ready task. The installed mirror has no harness-architect reference, and its per-task loop starts at Claim. Both checkpoint protocols call resolve_checkpoint only after a confirmed successful resume. Ship ran one disposable state-machine fixture. The first execution exited 2 because the fixture compared CRLF working-tree bytes with LF Git blobs. The corrected second execution exited 0. Ship reported that it accepted the canonical trace, read with owner validation of a uniquely selected checkpoint before restore, and rejected the N1-N5 mis-orderings and the reading that puts resolve_checkpoint before restore. Ship suggested FAIL. Ship wrote the fixture under .copilot/session-state/.../files/proof-e/ instead of the .proof-scratch/{proof}-{timestamp}/ directory that section 6.1 requires. Ship's 12-state event list, commands, raw outputs, gate records and before/after status were never put into durable evidence, and the parent removed the fixture after verifying its hash. The execution is therefore inadmissible, following the Proof A precedent. The anchors alone do not meet the section 6.7 FAIL clause. That clause asks whether a machine can satisfy both files 'without contradicting retained text', and the charter expects an insertion anchor for each file. Also, one reading of 'cursor restore before checkpoint validate-and-resolve' fits the retained text of both files. Verdict: BLOCKED, not PASS and not FAIL. PE-ACTIVATE-01 is recorded separately as an open P0 activation risk. Because of the approved commit 5bcb00e5, the mirror and the manifest can no longer be byte-identical to 082df7b2 at proof exit. The charter is not adjusted here. Time: a conservative upper bound of under 48 minutes against a 60-minute bound. Files: 1 of 2 disposable."
docline:
  type: spike
  date: 2026-09-24
  time_box: "1h"
  conclusion: "defer"
  confidence: "medium"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "ship-lifecycle"
    - "harness-placement"
    - "checkpoint-recovery"
    - "state-machine"
    - "proof-entry"
proof: E
proof_run: 1
proof_verdict: BLOCKED
proof_verdict_basis: inadmissible-execution-and-static-fail-clause-not-met
ship_suggested_verdict: FAIL
ship_suggested_verdict_adopted: false
fixture_admissible: false
scratch_location_status: charter-section-6.1-breach
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.2"
matrix_id: PE-1.2
charter_section: "6.7 (unchanged by PE-1.2)"
matrix_rows: [PE-FLOW-03, PE-ACTIVATE-01]
activation_baseline_risk: {row: PE-ACTIVATE-01, severity: P0, status: open, cause_commit: 5bcb00e5, charter_adjusted: false}
branch: chore/stage-176-s-workflow-defects
head_at_ship_dispatch: a0079ac0
head_at_authoring: a0079ac0
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_authoring: queued
shipment_claim_ready: false
publication_eligible: false
actor_invoked: false
review_scheduled: false
backlog_item_created: false
plan_changed: false
fail_route: none
time_bound_status: met-by-conservative-upper-bound
file_bound_status: met
scratch_cleanup_status: removed-by-parent-after-verification
carried_forward_verdicts:
  proof_a: {verdict: BLOCKED, matrix: PE-1.1, artifact: docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md}
  proof_d_run_1: {verdict: FAIL, matrix: PE-1.1, artifact: docs/decisions/2026-09-23-read-budget-proof-d-spike.md}
  proof_d_run_2: {verdict: PASS, matrix: PE-1.2, artifact: docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md}
  proof_f: {verdict: PASS, matrix: PE-1.1, artifact: docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md}
---

# Proof E findings - Ship per-task actor and checkpoint-first state machine

## Verdict

| Field | Value |
|---|---|
| Proof | E - Ship per-task actor and checkpoint-first state machine ([charter](2026-09-23-lifecycle-proof-entry-charter.md) section 6.7, unchanged by PE-1.2) |
| Matrix rows | `PE-FLOW-03` (Proof E verdict), `PE-ACTIVATE-01` (separate activation risk, below) |
| Verdict | **`BLOCKED`** |
| Why | The only fixture execution is inadmissible. It did not run in the scratch directory that section 6.1 requires, and its section 6.1 evidence handoff was never recorded durably. The anchors alone do not meet the section 6.7 `FAIL` clause |
| Not `PASS` | No admissible fixture run shows the machine accepting the canonical trace and rejecting every listed mis-ordering. A `BLOCKED` result is never converted into `PASS` (section 6.1) |
| Not `FAIL` | Ship suggested `FAIL`. Stage does not adopt it (see "Why not FAIL"). An inadmissible run cannot establish `FAIL` either. It is illustrative only, as invocation 2 was for Proof A |
| Route | Operator. The next attempt is gated as described under Next Steps. There is no automatic retry in this session |
| Re-execution | Allowed without a charter version bump, because `PE-FLOW-04` covers `FAIL` only (the Proof A precedent). The charter text is not changed here |

This artifact asserts no activation, no claim readiness, no publication
readiness, no `harness-ready` state and no P-004 red confirmation. The
harness-architect actor was not invoked. `187-S` remains `queued` and is not
claim-ready.

## Goal

Charter section 6.7 asks: where exactly does the per-task harness call sit,
and can a single state machine be consistent with both the exact template and
the exact installed mirror?

## Success Criteria (charter section 6.7, not amended)

* **Pass.** The fixture accepts exactly the canonical trace. It rejects each
  mis-ordered trace:
  1. the harness is invoked once before the loop instead of per task;
  2. the cursor is restored before checkpoint validate-and-resolve;
  3. the harness step runs before checkpoint validation;
  4. the consumer proceeds on process status without a validated document;
  5. placement diverges between the template and the mirror.
* **Fail.** No single state machine satisfies both files without
  contradicting retained text. That reopens the activation design.
* **Boundary.** Neither file is edited. The fixture models the files and does
  not modify them.

## Stage static analysis (read-only, verbatim anchors at `a0079ac0`)

For this artifact Stage re-read the anchors read-only with `git` and file
views. Every section 6.7 anchor sits at the charter's line number. The template
has no diff from `082df7b2`. The mirror's only diff is the frontmatter lines
5-13 (see PE-ACTIVATE-01), which moves no body line.

| Surface | Anchor | Verbatim text (excerpt) |
|---|---|---|
| Template | line 326 `### Step 2: Harness Generation (P-002 / P-004)`, line 328 | "Ensure every task in the target feature or chore has a passing test harness before any implementation begins. This step runs once, up front — not in a loop." |
| Template | lines 336, 339 | "If any tasks need harnesses, invoke the **harness-architect** skill for the batch." / "confirm every queued task now carries the `harness-ready` label" |
| Template | line 345 `### Step 3: Build Ready Queue`, line 372 | "List all tasks with `harness-ready` label and `{{STATUS_QUEUED}}` status for the target feature or chore." |
| Template | line 383 `### Step 4: Execute Task Loop` | "For each task in the ready queue:" then `#### Step 4.1: Claim Task` |
| Template | line 1006 Crash-Resumption, line 1038 | "`{{OP_RESOLVE_CHECKPOINT_MCP}}` is invoked ONLY AFTER Ship confirms a successful resume of the selected checkpoint — never before, never on ambiguous or torn state." |
| Mirror | line 170 Crash-Resumption, line 202 | "`backlogit_resolve_checkpoint` is invoked ONLY AFTER Ship confirms a successful resume of the selected checkpoint — never before, never on ambiguous or torn state." |
| Mirror | line 329 `### Step 1: Pre-Flight Checks` | P-001 gate, compile check, constitution read, clean branch. No harness step |
| Mirror | line 336 `### Step 2: Task Execution Loop`, line 357 | "For each task in the derived executable task set:" then "1. **Claim**: Move the task to active via `backlogit_move_item`." |

**Structural asymmetry (confirmed).** The template contains six
`harness-architect` references. The mirror contains none. The template runs
the harness once, up front, over the batch, then builds the queue from
`harness-ready` tasks. The mirror has no harness step, and its per-task loop
begins at Claim.

**Insertion anchors implied.** For the template, the per-task harness
invocation belongs inside `Step 4: Execute Task Loop` (line 383), and it
replaces the batch Step 2 (lines 326-343). The line 372 `harness-ready`
queue filter must stop presupposing an up-front batch. For the mirror, the
harness invocation belongs inside `Step 2: Task Execution Loop` (line 336),
next to its per-task step 1 Claim (line 357). The exact position relative to
Claim comes from the frozen plan revision 12, not from this artifact. Both
recovery protocols (template line 1006, mirror line 170) already come before
intake. They order enumeration, then anomaly check, then explicit unique
operator selection, then owner validation, then operator confirmation, then
restore, then prune, then resume, then `resolve_checkpoint`.

**Ambiguous charter phrase.** "Cursor restore before checkpoint
validate-and-resolve" has two readings:

* **Reading V (selection and owner validation).** The mis-ordering is a cursor
  restore before the unique explicit selection and the owner validation
  (`agent == ship`). Both files forbid this: restore happens "only on explicit
  operator confirmation" after "a valid unique selection and ownership
  match". A machine that rejects this trace fits the retained text of both
  files.
* **Reading S (status resolution).** The canonical order would require
  `resolve_checkpoint` (the status mutation) to run before the cursor restore.
  That contradicts template line 1038 and mirror line 202, which both call
  resolution "ONLY AFTER … a successful resume". Under this reading, no
  machine that fits the retained text can accept the canonical trace.

Stage's reading is V. It is the only reading that fits the retained text and
the backlogit prune-on-restore order (restore, then prune or gate, then
resume). The charter does not settle the phrase, so this artifact records the
ambiguity instead of resolving it by fiat.

## Ship execution (as reported; inadmissible)

The parent session relayed Ship's report. Ship's own durable evidence does not
exist.

| Item | Reported fact |
|---|---|
| HEAD at dispatch | `a0079ac0`, one worktree, `git status` clean (as reported and as re-observed by Stage at authoring) |
| Pre-write gates | Ship reported P-001, P-002, P-011 and P-016 satisfied. No backlog claim and no source or plan mutation |
| Fixture | One file, `proof_e_state_machine.py`, 17,531 bytes, SHA-256 `49594c8d3d1ae3cd82a06a406a82b8aaf275cc8dad0642a75fbaff285967dcea` |
| Fixture location | `.copilot\session-state\c5bdf9cb-7e6f-4018-b3f9-7d5b79db5faa\files\proof-e\proof_e_state_machine.py`. This is inside the repository and is git-ignored by `.gitignore:4` (`*.copilot`, checked by Stage with `git check-ignore -v`). It is **not** the `.proof-scratch/{proof}-{YYYYMMDD-HHMMSS}/` directory that section 6.1 requires |
| Host | Windows 11, Python 3.14.3 |
| Execution 1 | Exit 2. The fixture compared CRLF working-tree bytes with LF Git blob bytes. This is a defect in the fixture itself |
| Execution 2 (corrected) | Exit 0. Ship reported: the canonical trace accepted under the Reading V selection interpretation; N1-N5 mis-orderings rejected; the early-`resolve_checkpoint` (Reading S) interpretation rejected |
| Ship's conclusion | The current template and mirror cannot express the same machine without edits. Ship suggested `FAIL` |
| Output time and duration | Output at 2026-09-24T00:57:43-07:00. Ship segment about 6m41s |
| Cleanup | The parent verified the exact path, content and hash, then removed only that fixture and the now-empty `proof-e` subdirectory at 2026-09-24T00:59:20-07:00. No fixture file remains. §6.1 assigns cleanup to Ship after path verification, so this is recorded as a parent-performed deviation (Proof D run 2 precedent) |
| Not in durable evidence | The 12-state event list, the exact N1-N5 trace definitions, each command verbatim, raw stdout, stderr or their SHA-256, the recorded scratch path before first write, per-invocation P-010 self-check records, the `git worktree list --porcelain` listings, and the before/after `git status --porcelain` safety statement |

**Why the execution is inadmissible.** Section 6.1 requires Ship to write only
inside `.proof-scratch/{proof}-{YYYYMMDD-HHMMSS}/` and to record its resolved
path before the first write. Ship wrote outside that directory. Section 6.1
also requires an evidence handoff, and `PE-EVIDENCE-01` requires it in this
artifact, but most of that handoff is missing, and Stage cannot reconstruct
it from a summary without inventing facts. As with Proof A invocation 2 (a
gate-invalid positive run), the run is illustrative only. It supports neither
`PASS` nor `FAIL`. Whether it is also a `PE-AUTH-01` (`P0`) violation depends
on whether Ship recorded that path as its scratch directory before writing.
No durable record answers this, so it goes to the operator and is not
asserted either way.

## Why not FAIL on static evidence alone

The `FAIL` clause is "no single state machine satisfies both files *without
contradicting retained text*". Stage checked whether the anchors alone meet
it. They do not, with enough certainty to record `FAIL`:

1. **Current text does not settle it.** The charter's mis-ordering list
   already names "harness invoked once before the loop". The anchor bullet
   also requires "the insertion anchor it implies for each file". So the
   charter expected the current template to encode a rejected ordering and
   the mirror to lack a harness step. Ship's ground, that the unedited files
   cannot express the machine, is true, but it restates the known asymmetry.
   It is not the fail test.
2. **"Retained text" is undefined.** If it means everything outside the
   insertion anchors (Reading R1), the template's "runs once, up front — not
   in a loop" sentence and its batch Step 2 are replaced at activation.
   Nothing retained contradicts the per-task machine that Stage found
   statically. If it means all current text (Reading R2), `FAIL` follows
   statically and was fixed in advance by the charter's own anchors. Stage
   reads R1, because the charter asks for insertion anchors and treats
   activation as one template, mirror and manifest commit
   (`PE-ACTIVATE-02`). The charter does not settle this.
3. **The checkpoint half fits under Reading V.** Both retained recovery
   protocols express selection and owner validation before restore, and
   resolution after resume, so no contradiction exists under Reading V. Only
   Reading S produces a contradiction.

Under R1 and V, a single machine appears expressible. Under R2 or S, `FAIL`
follows. An admissible fixture cannot settle which pair the charter intends.
That is an operator interpretation, so the correct verdict is `BLOCKED`, not
a Stage-chosen `FAIL` or `PASS`.

## PE-ACTIVATE-01 - separate P0 activation risk (charter not adjusted)

| Field | Value |
|---|---|
| Row | `PE-ACTIVATE-01` (`P0`, `not-deferrable`): "Both Ship surfaces and the manifest are byte-identical to `082df7b2` at proof exit" |
| Observation (`git diff 082df7b2 HEAD`) | `templates/agents/_ship.agent.md.tmpl`: no diff. `.github/agents/_ship.agent.md`: frontmatter only (`reasoning_effort` high to xhigh, `model_provider` anthropic to openai, `model_family` claude-sonnet-5 to gpt-6-luna). `.autoharness/harness-manifest.yaml`: four checksum lines (entries at lines 107-133) |
| Cause | Commit `5bcb00e5` "chore: preserve approved workspace configuration and memory" (2026-09-23 22:15:47 -0700), a descendant of `082df7b2`, relayed to Stage as operator-approved |
| Consequence | Byte identity to `082df7b2` is now unsatisfiable at proof exit for two of the three paths, whatever the Proof E verdict. This is not an activation of the per-task lifecycle, since the template is unchanged and the mirror body is unchanged, but the row as written cannot pass |
| Disposition | Recorded as an open `P0` activation risk for the operator. Stage does not rebaseline the row, reinterpret "byte-identical" or defer it (the row is `not-deferrable`). Any change of baseline needs an operator decision and a charter version bump |

## Carried-forward verdicts (unchanged)

| Proof | Verdict | Matrix |
|---|---|---|
| A | `BLOCKED` | PE-1.1 |
| D run 1 | `FAIL` | PE-1.1 |
| D run 2 | `PASS` (synthetic contract only) | PE-1.2 |
| F | `PASS` | PE-1.1 |
| E | `BLOCKED` (this artifact) | PE-1.2 |

B, C and G have not been run.

## Matrix rows

| Row | Status after this artifact |
|---|---|
| `PE-FLOW-03` | Not satisfied. Proof E is `BLOCKED` |
| `PE-ACTIVATE-01` | Open `P0` risk (above). Not satisfiable as written |
| `PE-AUTH-01` | Stage side satisfied: this commit changes only this `docs/decisions/*-spike.md` file, and Stage ran no fixture, build, test or lint. Ship side is undetermined for the scratch location (see "Why the execution is inadmissible"), and goes to the operator |
| `PE-AUTH-02` | Ship reported P-001, P-002, P-011 and P-016 satisfied. Per-invocation records are not durable. Stage observed exactly one worktree at authoring |
| `PE-EVIDENCE-01` | Not satisfied for the Ship execution (missing fields listed above) |
| `PE-EVIDENCE-05` | Recorded below |
| `PE-SCOPE-07` | Time and file bounds met (below) |
| `PE-ACTIVATE-03` | No publication or claim readiness asserted |

## Bounds, time, scope and tools

| Item | Value |
|---|---|
| Time bound | 60m, covering Stage analysis and Ship execution together |
| Elapsed (conservative upper bound) | From the operator directive at 2026-09-24T00:27:37.827-07:00, before any Proof E work, to the end of authoring, capped at 2026-09-24T01:15:00-07:00. At most 47m23s, which meets the bound. The earlier read-only anchor analysis falls inside this window |
| File bound | 2 disposable. Used 1 (the single fixture). Met |
| Stage actions | Read-only `git status`, `log`, `diff`, `worktree list`, `check-ignore` and `merge-base`, plus file views. No fixture, build, test or lint. No edits to source, templates, agents, config, manifest, backlog, reviews, plans or the charter. No claim, PR or push. No extra worktree |
| Tool states | engram: circuit-open (degraded). agent-intercom: unavailable. graphtor-docs: unavailable. backlogit: not probed in this segment, and no backlog operation performed. Stage route: claude-opus-5.5 / anthropic / high |

## Next Steps

Nothing retries automatically. The next permitted attempt needs operator
authorization. It may run under PE-1.2 with no version bump (`PE-FLOW-04`
covers `FAIL` only), with its own 60m and two-file bound unless the operator
rules otherwise. It must meet all of the following:

1. **Interpretation first.** Before dispatch, the operator confirms or
   replaces Stage's readings: R1 for "retained text" and V for
   "validate-and-resolve". If the operator adopts R2 or S, Proof E is
   recorded `FAIL` statically and routes to the activation design with no
   fixture run.
2. **Scratch.** Ship records the resolved path
   `.proof-scratch/E-{YYYYMMDD-HHMMSS}/` inside the current working directory
   before the first write, and writes nowhere else. `.proof-scratch/` is not
   git-ignored (checked with `git check-ignore`), so the before/after
   `git status --porcelain` safety statement must show only that untracked
   directory, and it is never staged. Ship performs cleanup itself, after
   path verification and handoff approval.
3. **Anchor reading.** The fixture reads anchor bytes from Git blobs
   (`git show a0079ac0:<path>`) or normalizes line endings explicitly, and
   discloses which. This avoids the CRLF/LF defect of execution 1.
4. **Canonical trace.** Ship records the full state list and the canonical
   trace verbatim in its evidence, derived from the frozen plan revision 12
   and the section 6.7 anchors under the confirmed readings.
5. **Negative traces, each required to reject:**
   * N1: the harness is invoked once, up front, over the batch before the loop
     (the current template Step 2 shape);
   * N2-V: the cursor is restored (`get_checkpoint`, resume) before the unique
     explicit selection and the `agent == ship` owner validation;
   * N2-S: `resolve_checkpoint` runs before a confirmed successful resume,
     including on ambiguous or torn state;
   * N3: the harness step runs before checkpoint validation;
   * N4: the consumer proceeds on process status without a validated document;
   * N5: harness placement diverges between the template and the mirror
     models.

   The canonical trace must be accepted, and its recovery segment must place
   selection and owner validation before restore and `resolve_checkpoint`
   after resume. This is the positive control for both N2 readings.
6. **Evidence handoff.** Ship provides the complete section 6.1 and
   `PE-EVIDENCE-01` handoff: each command verbatim; raw stdout, stderr and
   exit status, or their SHA-256; host OS, version and filesystem; the
   interpreter; the fixture listing with a SHA-256 per file; the per-trace
   accept or reject table; elapsed time; the P-010, P-001, P-002, P-011 and
   P-016 records; `git worktree list --porcelain`; and the before/after
   status.

Open operator decisions:

* the R1/R2 and V/S interpretations above;
* whether the session-state write is a `PE-AUTH-01` violation;
* whether an inadmissible run consumes Proof E's time bound (the same
  question is still open for Proof A);
* the `PE-ACTIVATE-01` baseline drift from `5bcb00e5`.

## Cross-references

* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (sections 6.1, 6.7, 7.4, 7.10)
* Proof A precedent: `docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md`
* Proof D run 1 / run 2: `docs/decisions/2026-09-23-read-budget-proof-d-spike.md`, `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md`
* Proof F: `docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md`
* Ship surfaces: `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`
* Manifest: `.autoharness/harness-manifest.yaml`
* Frozen plan: `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` (revision 12)
* Governing decision: `docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md` (revision 9)
* Backlogit prune-on-restore protocol: `.github/instructions/backlogit.instructions.md`
* Role enforcement: `.github/instructions/role-enforcement.instructions.md`
* Skill: `.github/skills/spike/SKILL.md`
