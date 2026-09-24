---
title: "Proof E run 2 - Ship per-task actor and checkpoint-first state machine: findings (BLOCKED, projection incomplete)"
source: "docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md"
doc_type: decision
description: "Stage-authored findings for Proof E run 2 under charter PE-1.3 section 6.7. The run 1 PE-1.2 BLOCKED artifact stays unchanged. Ship passed the P-001, P-002, P-010, P-011 and P-016 gates before its first write. It wrote one disposable script, only at the charter-compliant path .proof-scratch/E-20260924-011528/, and ran it twice on Windows 11 with Python 3.14.3 on NTFS. Both runs exited 1. Run 1 failed on the fixture's own parsing of the canonical checkpoint selection token. Run 2 aborted inside the fixture with 'FIXTURE_ERROR RuntimeError: checkpoint protocol anchor missing or duplicated'. Before that abort, run 2 accepted the canonical zero-candidate trace and the resumed active-cursor trace, and it rejected N1 (harness only up front), N2-V (restore before selection), N3 (harness before validation) and N4 (proceeding on process status without a validated document). It never executed N5 (placement diverging between template and mirror), N2-S (resolve before a confirmed resume), or the quarantine and ambiguous-selection negatives. Section 6.7 requires every listed mis-ordering to be rejected, so the pass criterion is not met. The partial synthetic evidence does not prove the fail clause either. The raw stdout, stderr and their SHA-256 values were not handed to Stage, so PE-EVIDENCE-01 is also incomplete. Verdict: BLOCKED, not PASS and not FAIL. At the observed HEAD 7f833cb8, Stage found that the raw Git blobs for PE-ACTIVATE-01 equal 5bcb00e5 for all three paths. The row must be rechecked at proof exit, and it does not make up for PE-FLOW-03. Time is within 60 minutes, counted from Stage analysis and Ship start (about 01:04). The conservative 00:27 directive bound is not claimed. Files: 1 of 2 disposable. The next attempt is counted attempt 3 and falls under the circuit breaker."
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
proof_run: 2
proof_verdict: BLOCKED
proof_verdict_basis: required-negatives-and-projection-not-completed
prior_run_artifact: docs/decisions/2026-09-24-ship-activation-proof-e-spike.md
prior_run_verdict: BLOCKED
prior_run_matrix: PE-1.2
prior_run_verdict_changed: false
fixture_admissible_scratch: true
scratch_path: ".proof-scratch/E-20260924-011528/"
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.3"
matrix_id: PE-1.3
charter_section: "6.7 (PE-1.3)"
matrix_rows: [PE-FLOW-03, PE-ACTIVATE-01]
activation_check: {row: PE-ACTIVATE-01, status: satisfied-at-observed-head-only, observed_head: 7f833cb8, baseline: 5bcb00e5, recheck_required_at_proof_exit: true}
branch: chore/stage-176-s-workflow-defects
head_at_ship_dispatch: 7f833cb8
head_at_authoring: 7f833cb8
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
publication_eligible: false
actor_invoked: false
review_scheduled: false
backlog_item_created: false
plan_changed: false
charter_changed: false
fail_route: none
counted_same_operation_failures: 2
next_attempt_counted_as: 3
time_bound_status: met-from-stage-analysis-and-ship-start
file_bound_status: met
scratch_cleanup_status: removed-by-parent-after-verification
carried_forward_verdicts:
  proof_a: {verdict: BLOCKED, matrix: PE-1.1, artifact: docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md}
  proof_d_run_1: {verdict: FAIL, matrix: PE-1.1, artifact: docs/decisions/2026-09-23-read-budget-proof-d-spike.md}
  proof_d_run_2: {verdict: PASS, scope: synthetic-contract-only, matrix: PE-1.2, artifact: docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md}
  proof_e_run_1: {verdict: BLOCKED, matrix: PE-1.2, artifact: docs/decisions/2026-09-24-ship-activation-proof-e-spike.md}
  proof_f: {verdict: PASS, matrix: PE-1.1, artifact: docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md}
---

# Proof E run 2 findings - Ship per-task actor and checkpoint-first state machine

## Verdict

| Field | Value |
|---|---|
| Proof | E, run 2. Ship per-task actor and checkpoint-first state machine ([charter](2026-09-23-lifecycle-proof-entry-charter.md) section 6.7, PE-1.3) |
| Matrix rows | `PE-FLOW-03` (the Proof E verdict) and `PE-ACTIVATE-01` (a separate check, below) |
| Verdict | **`BLOCKED`** |
| Why | The fixture's projection stopped at its own anchor assertion before it ran every mis-ordering that section 6.7 requires. N5 and N2-S were not executed, and neither were the additional quarantine and ambiguous-selection negatives. The `PE-EVIDENCE-01` handoff is also incomplete, because the raw outputs and their SHA-256 values were not provided |
| Not `PASS` | Section 6.7 requires the fixture to reject *each* listed mis-ordering, and N5 was never run. There is no partial pass (section 6.1). A `BLOCKED` result is never converted into `PASS` |
| Not `FAIL` | Nothing that was executed shows that no single state machine can satisfy both files without contradicting retained text (PE-1.3 term). A fixture defect that stops the run is not evidence against the design |
| Route | Operator. The next attempt is gated as described under Next Steps. Nothing retries in this session |
| Re-execution | Allowed without a charter version bump, because `PE-FLOW-04` covers `FAIL` only. The circuit breaker limit applies (see Next Steps) |

This artifact asserts none of the following: activation, claim readiness,
publication readiness, a `harness-ready` state, or P-004 red confirmation. The
harness-architect actor was not invoked. `187-S` is not claim-ready. The run 1
artifact (`docs/decisions/2026-09-24-ship-activation-proof-e-spike.md`,
PE-1.2 `BLOCKED`) is immutable and is not edited, superseded or re-labelled
here.

## Goal

Charter section 6.7 asks where exactly the per-task harness call sits, and
whether a single state machine can be consistent with both the exact template
and the exact installed mirror. Run 2 is judged against the PE-1.3 terms:

* **Checkpoint validate-and-resolve** means unique operator selection, then the
  anomaly, CheckpointV1 schema and `agent == ship` owner validation, then
  operator confirmation, all before restore. `resolve_checkpoint` runs only
  after a confirmed successful resume.
* **Retained text** means the text that remains after the planned activation
  edits (`PE-ACTIVATE-02`), not the current text.

## Success Criteria (charter section 6.7, PE-1.3, not amended)

* **Pass.** The fixture accepts exactly the canonical trace and rejects each of
  these mis-ordered traces:
  * the harness invoked once before the loop instead of per task;
  * the cursor restored before checkpoint validate-and-resolve;
  * the harness step before checkpoint validation;
  * the consumer proceeding on process status without a validated document;
  * placement that diverges between template and mirror.
* **Fail.** No single state machine satisfies both files without
  contradicting retained text.
* **Boundary.** Neither file is edited.

## Ship execution (as reported by Ship and relayed to Stage)

### Gates and scratch

| Item | Reported result |
|---|---|
| Gates before first write | P-001, P-002, P-010, P-011 and P-016 passed. There was no active shipment, task, feature or chore. The P-011 branch state was clean. `git worktree list --porcelain` showed one worktree |
| Branch and HEAD | `chore/stage-176-s-workflow-defects` at `7f833cb8`. No branch was created or switched |
| Scratch path | `.proof-scratch\E-20260924-011528\` inside the current working directory. This is the section 6.1 form, unlike run 1, which wrote under `.copilot/` |
| Fixture listing | One file: `.proof-scratch\E-20260924-011528\proof_e_state_machine.py`, 25,109 bytes, SHA-256 `041882ef99cc02559d50840c1c22cbe049c8ae58feff63e3060aaa151edcb11b` |
| File bound | 1 of 2 disposable files |
| Host | Windows 11, Python 3.14.3, NTFS |
| Host execution segment | 01:09:48 to 01:19:47 (-07:00), under 15 minutes |
| Cleanup | The parent verified the exact scratch fixture and removed it at 2026-09-24T01:21:20-07:00. Afterwards `git status` was clean |

### Commands and exit status

| Invocation | Command (verbatim) | Native exit | Reported cause |
|---|---|---|---|
| 1 | `python .proof-scratch\E-20260924-011528\proof_e_state_machine.py` | 1 | The fixture could not parse the canonical checkpoint selection token (a defect in the fixture) |
| 2 (corrected script) | `python .proof-scratch\E-20260924-011528\proof_e_state_machine.py` | 1 | `FIXTURE_ERROR RuntimeError: checkpoint protocol anchor missing or duplicated` |

Stage did not receive the raw stdout and stderr of either invocation, or their
SHA-256 values. Stage does not reconstruct them. The fixture SHA-256 above
belongs to the corrected script. Ship did not report a separate hash for the
invocation 1 script.

### Per-trace outcome (invocation 2)

| Trace | Required | Reported outcome |
|---|---|---|
| Canonical, zero-candidate startup | accept | Accepted |
| Canonical, resumed active cursor | accept | Accepted |
| N1: harness invoked once, up front, before the loop | reject | Rejected |
| N2-V: restore before unique selection and owner validation | reject | Rejected |
| N3: harness step before checkpoint validation | reject | Rejected |
| N4: consumer proceeds on process status without a validated document | reject | Rejected |
| N5: placement diverges between template and mirror | reject | **Not executed.** The projection aborted at the anchor assertion |
| N2-S: `resolve_checkpoint` before a confirmed successful resume | reject | **Not executed** |
| Quarantine or anomaly not failing closed | reject | **Not executed** |
| Ambiguous or non-unique selection | reject | **Not executed** |

Ship gave the parent ordered event lists for the canonical traces and for N1
to N4. They are summarized above and not reproduced verbatim. No output exists
for N5 or for the other traces that were not executed, and none is inferred
here.

### Safety statement (as relayed)

Before the first write, the tree was clean and one worktree existed. After the
parent removed the scratch directory, `git status` was clean. Nothing was
staged or committed from scratch. The relay did not include a `git status
--porcelain` listing taken while the scratch directory still existed.

## Stage read-only observations at `7f833cb8`

Stage read the Git blobs (`git show HEAD:<path>`) to guide the next attempt.
Stage ran no fixture.

* The exact heading line `### Crash-Resumption / Startup Recovery Protocol
  (fail-closed, owner-exclusive)` occurs exactly once in each Ship surface: at
  line 1006 of `templates/agents/_ship.agent.md.tmpl` and at line 170 of
  `.github/agents/_ship.agent.md`. These line numbers match the section 6.7
  anchors.
* In each blob, a case-insensitive substring match on `crash-resumption` hits
  three lines: the heading, plus two prose lines immediately after it
  (template lines 1010-1011, mirror lines 174-175).
* Stage records this only as a candidate reason for a "missing or duplicated"
  assertion. It is **not** a confirmed root cause, because Stage did not see
  the fixture source or its raw output.

## PE-ACTIVATE-01 (separate row, observed HEAD only)

Ship compared the raw LF Git blobs separately (exit 0). Stage then re-checked
them read-only with `git rev-parse`, `git cat-file blob` and SHA-256:

| Path | Blob at `5bcb00e5` | Blob at `7f833cb8` | Raw-blob SHA-256 | Equal |
|---|---|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | `a3407080665c874e6db742a467bcd79ce97d2666` | `a3407080665c874e6db742a467bcd79ce97d2666` | `7f2ddef1ada977fbb0d06a3f83587b1151acde297148a0847e1b0145d5595db2` | Yes |
| `.github/agents/_ship.agent.md` | `5f397d0f1f2c8ce8dcded360a73a2a0d120ffc3a` | `5f397d0f1f2c8ce8dcded360a73a2a0d120ffc3a` | `83f9e73520f5d88708738f6bdbfc849377e9d1705366120cb49c1dc6b72ff81c` | Yes |
| `.autoharness/harness-manifest.yaml` | `17ae787d492fe06788ce21ae6fab29a26b3c4139` | `17ae787d492fe06788ce21ae6fab29a26b3c4139` | `10c0fa89e08c325c099d0332e35b01008e85a26d3ffc76cc765e8cff052addb8` | Yes |

`git diff 5bcb00e5 7f833cb8 --` for the three paths is empty, and `git status
--porcelain` for the three paths is empty. The SHA-256 values match charter
section 3.2.

**Status:** satisfied at the observed HEAD `7f833cb8` **only**. The row names
the proof-exit commit as its comparator, so it must be rechecked at proof
exit. It does not make up for the incomplete `PE-FLOW-03`.

## Matrix rows

| Row | Status after run 2 |
|---|---|
| `PE-FLOW-03` | Not satisfied. `BLOCKED`, because the required negatives and the projection were not completed |
| `PE-ACTIVATE-01` | Satisfied at `7f833cb8` only. Must be rechecked at proof exit |
| `PE-EVIDENCE-01` | Incomplete for this run: raw stdout, stderr and their SHA-256 are missing, as is the during-run porcelain listing |
| `PE-AUTH-02` | One worktree and per-invocation gates, as reported |
| `PE-EVIDENCE-05` | See tool states below |

## Carried-forward verdicts (unchanged)

| Proof | Verdict | Artifact |
|---|---|---|
| A | `BLOCKED` (PE-1.1) | `docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md` |
| D run 1 | `FAIL` (PE-1.1) | `docs/decisions/2026-09-23-read-budget-proof-d-spike.md` |
| D run 2 | `PASS`, synthetic contract only (PE-1.2) | `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md` |
| E run 1 | `BLOCKED` (PE-1.2), immutable | `docs/decisions/2026-09-24-ship-activation-proof-e-spike.md` |
| F | `PASS` (PE-1.1) | `docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md` |

Proofs B, C and G have not been run.

## Bounds, time, scope and tools

* **Time.** The bound is 60 minutes (section 6.2). This run is counted from the
  start of Stage's read-only analysis and Ship's start (about 01:04 -07:00) to
  this authoring (about 01:25 -07:00), which is within 60 minutes. The
  conservative bound from the operator directive at 00:27 would pass 60
  minutes by commit time, so **it is not claimed**. Whether run 1 consumed
  Proof E's time bound is still an open question.
* **Files.** 1 of 2 disposable files.
* **Scope.** No claim was made, and no production file, template, mirror,
  manifest, review, plan, backlog item or charter was edited. This artifact is
  the only file committed.
* **Tools (P-012).**
  * Engram: circuit-open, so Stage fell back to reading Git blobs.
  * Agent-intercom: unavailable, so no broadcasts were made.
  * Graphtor-docs: unavailable.
  * Backlogit: Ship's gate queries reported no active shipment, task, feature
    or chore. Stage did not probe it again for this authoring step.

## Next Steps

Nothing retries automatically. A third attempt needs operator authorization,
under PE-1.3 with no version bump. It must do all of the following:

1. **Anchor detector.** Replace the brittle checkpoint-protocol anchor
   detector. It should match the exact two known unique heading lines (the
   full-line text above, at template line 1006 and mirror line 170, read from
   Git blobs) and assert exactly one occurrence per file. It should not match
   on a substring.
2. **Full negative set.** Execute and record every trace. Each of the
   following must be rejected:
   * N1, N2-V, N2-S, N3 and N4;
   * N5 (divergent template and mirror placement);
   * quarantine or anomaly failing to fail closed;
   * ambiguous or non-unique selection.

   Both canonical traces must also be accepted.
3. **Full section 6.1 evidence.** Hand over the complete `PE-EVIDENCE-01`
   evidence:
   * each command verbatim;
   * raw stdout, stderr and exit status, or their SHA-256;
   * the fixture listing with a SHA-256 per file;
   * the per-trace table with verbatim event lists;
   * host facts and elapsed time;
   * the per-invocation gate records;
   * `git worktree list --porcelain`;
   * the before, during and after `git status --porcelain`.
4. **Fresh preflight.** Record a new scratch path before the first write, and
   run the P-001, P-002, P-010, P-011 and P-016 gates again.
5. **Circuit breaker.** Both invocations of this operation failed with a
   non-zero native exit, so both are counted. The next execution is **counted
   attempt 3**, even with a new scratch timestamp or a corrected script. If the
   anchor error recurs on attempt 3, the universal breaker trips: stop, log,
   escalate, with no fourth attempt. Stage counts the two distinct errors
   conservatively and does not claim that either one resets the count.
6. **Proof exit.** Recheck `PE-ACTIVATE-01` at the proof-exit commit.

Stage does not execute any of these steps, and cannot write scratch or rerun
the fixture (P-010). Nothing here is `PASS`.

## Cross-references

* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (sections 3.2, 6.1, 6.7, 7.4, 7.9, 7.10, 10)
* Proof E run 1: `docs/decisions/2026-09-24-ship-activation-proof-e-spike.md`
* Proof A: `docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md`
* Proof D run 1 and run 2: `docs/decisions/2026-09-23-read-budget-proof-d-spike.md`, `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md`
* Proof F: `docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md`
* Ship surfaces: `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`
* Manifest: `.autoharness/harness-manifest.yaml`
* Circuit breaker: `.github/instructions/circuit-breaker.instructions.md`
* Skill: `.github/skills/spike/SKILL.md`
