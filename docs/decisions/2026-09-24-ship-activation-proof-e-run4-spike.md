---
title: "Proof E run 4 (PE-1.4) - Ship per-task actor and checkpoint-first state machine: findings (BLOCKED, retained-text reading fork routed to operator)"
source: "docs/decisions/2026-09-24-ship-activation-proof-e-run4-spike.md"
doc_type: decision
description: "Stage's formal findings for Proof E run 4 under charter PE-1.4, section 6.7 (unchanged since PE-1.3) and the PE-1.4 section 6.1 evidence handoff. The execution was admissible. In the one current worktree at HEAD 6920cb7c, Ship ran a same-invocation CLI refresh (backlogit sync: exit 0, stdout 23 B cf46e51c...e873, stderr 487 B 9f9f8bbb...994b). Only the ignored .backlogit db and wal changed. Ship then wrote one ignored fixture, .proof-scratch/E-run4-20260924-170243/proof_e_state_machine.py (15043 B, 33cd01f4...270dc). Stage re-hashed it read-only and read it fully. The fixture reads both Ship surfaces from HEAD raw blobs and drives one trace set through one shared checker for both surfaces. Invocation 1 exited 2 (KeyError:1). Invocation 2 exited 0 and printed 15 cases, all passed, with 0 failed: C1 and C2 accepted, and all 13 negatives rejected, each for its intended reason. Without running the fixture, Stage predicted the exact stdout bytes from the source (1052 B CRLF, SHA-256 fa659428...035d) and the invocation 1 stderr bytes (26 B, 4246c3ac...a6d7). Both match Ship's relay. The checker never sees the expected values, so no expected outcome is hardcoded into it. The fixture therefore meets the section 6.7 pass criterion over the anchored text it models. But Stage's own retained-text audit found template-only retained text that the fixture does not model and that the section 6.7 replacement list does not remove. Session start lines 1004-1006 restore memory context before the recovery state machine runs. The Resumption Protocol at lines 1103-1107 resumes from a context-overflow memory checkpoint with no selection, validation or confirmation. The installed mirror has neither passage. Frozen plan revision 12 line 229 calls line 1005 an early restore that happens before checkpoint validation and requires its removal. Whether this text contradicts checkpoint-first restore depends on a reading the charter does not settle: scoped to backlogit CheckpointV1 cursors (PASS) or unscoped (FAIL). Charter section 2 forbids a proof author from picking the more convenient reading. Following the run 1 precedent, the verdict is BLOCKED and the choice goes to the operator as a charter change. The verdict is not PASS and not FAIL. Runs 1-3 stay as recorded. No production, charter, backlog or Ship-source edit. No claim authority. 187-S stays queued and frozen."
docline:
  type: spike
  date: 2026-09-24
  time_box: "60m"
  conclusion: "defer"
  confidence: "medium"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "ship-lifecycle"
    - "harness-placement"
    - "checkpoint-recovery"
    - "state-machine"
    - "retained-text"
    - "proof-entry"
proof: E
proof_run: 4
proof_verdict: BLOCKED
proof_verdict_basis: "charter-reading-fork (section 2 routing): template-only retained text at lines 1004-1006 and 1103-1107 (outside the section 6.7 replacement list, not modeled by the fixture) contradicts checkpoint-first restore under one reading and not under the other; not an execution defect"
fixture_execution_admissible: true
fixture_pass_criterion_met_over_modeled_text: true
fail_clause_established: false
behavior_disproven: false
prior_run_artifacts:
  - {run: 1, path: docs/decisions/2026-09-24-ship-activation-proof-e-spike.md, commit: a04e1e5a, verdict: BLOCKED, matrix: PE-1.2, changed: false}
  - {run: 2, path: docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md, commit: 6ee65c4a, verdict: BLOCKED, matrix: PE-1.3, changed: false}
  - {run: 3, path: docs/decisions/2026-09-24-ship-activation-proof-e-run3-spike.md, commit: 383ae6be, verdict: BLOCKED, matrix: PE-1.3, changed: false}
prior_run_verdicts_changed: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.4"
matrix_id: PE-1.4
charter_sections: ["2", "3.3", "6.1", "6.7"]
matrix_rows: [PE-FLOW-03, PE-ACTIVATE-01]
evidence_rows_assessed: [PE-EVIDENCE-01, PE-EVIDENCE-05, PE-AUTH-01, PE-AUTH-02, PE-AUTH-03, PE-SCOPE-07, PE-ACTIVATE-03]
scratch_path: ".proof-scratch\\E-run4-20260924-170243\\"
fixture_files:
  - {name: proof_e_state_machine.py, bytes: 15043, sha256: 33cd01f4221b00ddc3e9d44ea381d79f0f608afa334d1457dde6a18e169270dc, stage_verified: true, git_ignored_by: ".gitignore:10 .proof-scratch/"}
fixture_command: "python -B .proof-scratch\\E-run4-20260924-170243\\proof_e_state_machine.py"
invocations:
  - {n: 1, native_exit: 2, stdout_bytes: 0, stderr_bytes: 26, stderr_sha256: 4246c3ac20cb24e38a0265ccc6b038d3862f2b7342c68c2ec8634dffe64ca6d7, stderr_text_stage_reproduced: "FIXTURE_ERROR=KeyError:1 (CRLF)", script_sha256_relayed: false}
  - {n: 2, native_exit: 0, stdout_bytes: 1052, stdout_sha256: fa65942802292fe0edb89ee5e5c2cefc7d09cb3bf918d2ac8102a83b907a035d, stdout_stage_reproduced_from_source: true, stderr_bytes: 0}
cases_total: 15
cases_passed: 15
cases_accept: [C1, C2]
cases_reject: [N1, N2-V, N3, N4-DOC, N4-RED, N4-E1, N4-E2, N5-DIV, N5-AFTER, N2-S, N6-AUTO, N6-NONE, N7]
checker_receives_expected: false
host: {os: "Windows 11 (NT 10.0.26200)", filesystem: NTFS, interpreter: "Python 3.14.3"}
index_refresh: {transport: CLI, command: "backlogit sync", native_exit: 0, stdout_bytes: 23, stdout_sha256: cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873, stderr_bytes: 487, stderr_sha256: 9f9f8bbbce862c41270273712641d5f81e88798f7ee060f65f1a113c687b994b, changed: [".backlogit db (ignored)", ".backlogit db-wal (ignored)"]}
checkpoint_scan: {filter: none, total: 71, resolved: 70, abandoned: 1, quarantined: 0, active: 0, official_get_valid: true}
p001_active_counts: {task: 0, feature: 0, chore: 0, shipment: 0}
activation_check: {row: PE-ACTIVATE-01, comparator: 4acba14a, head: 6920cb7c, blobs_equal: true, tracked_diff_empty: true, porcelain_empty: true, stage_verified: true, recheck_required_at_proof_exit: true}
branch: chore/stage-176-s-workflow-defects
head_at_ship_execution: 6920cb7c
head_at_authoring: 6920cb7c73ccbac44d993dd79a29ccccdd8aac39
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_authoring: "queued, frozen (Ship-reported; not re-read by Stage)"
shipment_claim_ready: false
publication_eligible: false
backlog_item_created: false
plan_changed: false
charter_changed: false
fail_route: none
reopened_decision: none
operator_decision_required: "Fix the section 6.7 retained-text scope for template lines 1004-1006 and 1103-1107 (see Next Steps)"
time_bound_status: met
file_bound_status: "met (1 of 2 disposable files)"
scratch_cleanup_status: "retained; Stage deleted nothing"
stage_model_route: "claude-opus-5.5/anthropic/high requested; unverified by Stage (route not self-verifiable)"
---

# Proof E run 4 findings (PE-1.4): Ship per-task actor and checkpoint-first state machine

## Verdict

| Field | Value |
|---|---|
| Proof | E, run 4 ([charter](2026-09-23-lifecycle-proof-entry-charter.md) section 6.7, unchanged since PE-1.3; section 6.1 as of PE-1.4) |
| Matrix rows | `PE-FLOW-03` (the Proof E verdict); `PE-ACTIVATE-01` (a separate check, below) |
| Verdict | **`BLOCKED`**. A charter reading fork, routed to the operator under section 2. This is not an execution defect |
| What passed | The execution was admissible. The fixture is sound (it hardcodes no expected results). All 15 cases were really evaluated, and each produced its intended outcome. The fixture meets the section 6.7 pass criterion over the anchored text it models. Stage reproduced Ship's stdout and stderr bytes from the fixture source without running it |
| Why not `PASS` | Stage's retained-text audit found template-only retained text that no fixture trace models. It is template Session start lines 1004-1006, which restore memory context before the recovery state machine, and the Resumption Protocol at lines 1103-1107, which resumes from a `context-overflow` memory checkpoint with no selection, validation or confirmation. The mirror has neither passage. Under the unscoped reading, which frozen plan revision 12 line 229 takes, the fixture's machine contradicts template retained text. It also cannot be made permissive without accepting a restore before validate-and-resolve. Choosing the scoped reading to reach `PASS` is the convenience choice that section 2 forbids |
| Why not `FAIL` | Under the scoped reading, the fixture's machine is a valid single-machine witness for both surfaces. That reading limits "cursor restore" to the backlogit CheckpointV1 cursor, which is the recovery protocol's stated scope (its "OWN (`agent: ship`) checkpoints"). Docs-memory context stays outside that cursor. So `FAIL` is not established either |
| No partial pass | The per-task placement half would pass by itself. But `PE-FLOW-03` covers both halves, and section 6.1 allows no partial pass |
| Route | Operator, as a charter change (section 2; run 1 precedent, which became PE-1.3). `BLOCKED` is never converted into `PASS`. See Next Steps |

This artifact asserts no activation, claim readiness, publication readiness,
`harness-ready` state or P-004 red confirmation (`PE-ACTIVATE-03`,
`PE-AUTH-03`). The harness-architect actor was not invoked. `187-S` is not
claim-ready and remains queued and frozen. The run 1-3 artifacts are unchanged.

## Goal

Charter section 6.7 asks where exactly the per-task harness call sits, and
whether one state machine is consistent with both the exact template and the
exact installed mirror. Retained text is judged under Reading R1: text that
remains after the planned activation replacements. Checkpoint
validate-and-resolve is judged under Reading V: before restore, a unique
explicit operator selection, then owner and schema validation, then
confirmation; `resolve_checkpoint` only after a confirmed successful resume.

## Success Criteria (section 6.7, not amended)

* **Pass.** The fixture accepts exactly the canonical trace and rejects each of these mis-orderings:
  * the harness invoked once before the loop instead of per task;
  * a restore before validate-and-resolve;
  * the harness before checkpoint validation;
  * proceeding on process status without a validated document;
  * divergent template/mirror placement;
  * a resolve before a confirmed resume, or a resolve on ambiguous state.
* **Fail.** No single state machine satisfies both files without contradicting retained text.
* **Boundary.** Neither file is edited.

## Scope Constraints

Stage did read-only analysis only: `git rev-parse`, `git cat-file blob` and
in-process SHA-256; reading the fixture source; and computing predicted
bytes. Stage did not run the fixture, any test, build or lint. It did not
refresh the index, run any backlog CLI or MCP mutation, or create any
worktree (P-010; section 6.1). Compound consulted:
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`.
Its lesson is that a locally correct clause is not global correctness, so the
composition must be checked against the whole surface. That lesson prompted
the full-surface retained-text audit below.
`docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md`
supports treating the C1-C6 derived set as the actual loop membership.

## Ship execution (as relayed to Stage)

| Item | Relayed result |
|---|---|
| Session | 16:55:27 to 17:06:51 (-07:00), 11m24s |
| Pre-write gates | P-010: scratch and cache writes only. P-002: no claim. P-011 and P-016: clean, with one worktree at HEAD `6920cb7c` on `chore/stage-176-s-workflow-defects`. P-001 was checked after the refresh: 0 active tasks, features, chores and shipments. The `PE-ACTIVATE-01` blobs at HEAD equal `4acba14a`, with no tracked diffs. `173-S` closure is READY, and compaction is done |
| Pre-write helper defect | The first pre-write helper inverted the clean-status check. It reported a false `BLOCKED` before any write and was corrected. Stage independently confirms the tree is clean (`git status --porcelain` is empty, and one worktree exists). No write occurred under the false result |
| Index refresh | CLI `backlogit sync`, native exit 0. Stdout: 23 B, `cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873`. Stderr: 487 B, `9f9f8bbbce862c41270273712641d5f81e88798f7ee060f65f1a113c687b994b`. Stderr was not empty, and this artifact does not claim that it was. Only the ignored db and wal changed |
| Checkpoint scan | Unfiltered: 71 checkpoints, 70 resolved and 1 abandoned. 0 quarantined and 0 active. The official get validated as `true`. So no recovery was triggered |
| Scratch | `.proof-scratch\E-run4-20260924-170243\`. One file, no `__pycache__` (`-B`). Git-ignored via `.gitignore:10` |
| Invocation 1 | Exit 2. Stdout empty. Stderr 26 B, `4246c3ac20cb24e38a0265ccc6b038d3862f2b7342c68c2ec8634dffe64ca6d7`. The script hash for this invocation was not relayed |
| Invocation 2 | `python -B .proof-scratch\E-run4-20260924-170243\proof_e_state_machine.py`, run on the corrected script. Exit 0. Stdout 1052 B, `fa65942802292fe0edb89ee5e5c2cefc7d09cb3bf918d2ac8102a83b907a035d`. Stderr 0 B. The output is under 2 KiB, and no raw spool was made |
| Summary | 15 cases, 15 passed and 0 failed, across 2 surfaces |

## Findings

### What Was Discovered

**F1 - The fixture is what Ship reported.** Stage's own reading shows 15043 B,
SHA-256 `33cd01f4...270dc`, one file, and Git-ignored.

**F2 - Byte-exact reproduction without execution.** From a manual trace of the
source, Stage built the predicted stdout: one line per case, of the form
`{id} EXPECTED={X} ACTUAL={X} reason={r}`, followed by
`SUMMARY cases=15 passed=15 failed=0 surfaces=2`. Windows text-mode
`sys.stdout` writes CRLF.

* Predicted stdout: 1052 B, SHA-256 `fa659428...035d`. This equals invocation 2.
* The LF form would be 1036 B, `1f2d4c19...a8fe`, and does not match.
* Predicted invocation 1 stderr: `FIXTURE_ERROR=KeyError:1\r\n`, 26 B, `4246c3ac...a6d7`. This equals the relay.

The predicted reasons were:

| Case | Outcome | Reason |
|---|---|---|
| C1, C2 | Accepted | `canonical` |
| N1 | Rejected | `harness_not_per_task` |
| N2-V | Rejected | `restore_before_validation_confirmation` |
| N3 | Rejected | `checkpoint_validation_before_task` |
| N4-DOC | Rejected | `exit0_requires_one_schema_valid_document` |
| N4-RED | Rejected | `wrong_task_marker` |
| N4-E1 | Rejected | `exit1_outcome_collapse` |
| N4-E2 | Rejected | `exit2_outcome_collapse` |
| N5-DIV | Rejected | `mirror:after_claim` |
| N5-AFTER | Rejected | `after_claim` |
| N2-S | Rejected | `resolve_before_resume_success` |
| N6-AUTO | Rejected | `selection_not_operator_unique` |
| N6-NONE | Rejected | `selection_required` |
| N7 | Rejected | `anomaly_before_filter` |

**F3 - The fixture does not cheat on expected outcomes.** `check(trace, surf,
override)` never receives the case ID, the `expected` flag or `want_reason`.
Those values are used only after `check` returns, to grade its result:
`ok = actual == expected and want_reason in reason`. Because the reason is
graded too, a negative that is rejected for an unintended, earlier reason
counts as a failure. By manual trace, each negative reaches its intended
branch first. `SUMMARY` counts the graded comparisons, and exit 0 only when
all 15 match. Every trace runs against both surfaces through the same
`check`.

**F4 - Coverage of the contract points the operator asked about:**

| Point | How it is checked |
|---|---|
| Per-task T1, T2, T3 and Claim | Each task needs exactly one actor event (T1), one harness event (T2), one red event (T3) and one claim event, in the order T1, T2, T3, Claim. Tasks may not interleave. No batch (`*`) task is allowed. No extra task events are allowed |
| Exit 0 needs one schema-valid document | Checked, and N4-DOC rejects a violation. The document is modeled as `doc_count == 1` plus a `schema_valid` flag. Real JSON validation belongs to Proof B |
| Exit 1 `NO_HARNESS` and exit 2 `UNRESOLVED` stay distinct | Shown by rejecting swaps in both directions (N4-E1, N4-E2). A collapsed mapping would make one of them accept |
| Each task needs its own RED marker | N4-RED rejects a marker that belongs to another task |
| Enumerate everything; no filter before the anomaly scan | Enumeration must be the first event, with `filters == []`. The anomaly scan must run on `scope == "all"` before any filter (N7). Any invalid or quarantined row rejects. Partition must come after the anomaly scan and match the active `ship` count |
| Explicit, unique selection of a `ship` checkpoint | The selection mode must be `operator`, with `explicit` true and `count == 1`, and it must match the candidate (N6-AUTO, N6-NONE) |
| Owner and schema validation | The owner must be `agent == ship` with `schema_valid` true |
| Operator confirmation | Required |
| Recovery order | Select, owner, confirm, restore, prune, resume, confirmed resume success, then resolve. Each step occurs exactly once, in order. N2-V rejects a restore before validation and confirmation. N2-S rejects a resolve before resume success. Every step must refer to the selected checkpoint |
| No task before validation | N3 |
| Placement divergence | N5-DIV sends the same trace to both surfaces, with the mirror overridden to after-claim. The template accepts it and the mirror rejects it, so the case rejects. N5-AFTER rejects harness and red placed after the claim |

**F5 - The fixture's anchors match Stage's anchor matrix at HEAD
`6920cb7c`.** All anchors are two lines below the section 6.7 citations at
`082df7b2`, as section 3.3 states.

| Surface | Replaced (planned) | Retained | Insertion slot | Recovery |
|---|---|---|---|---|
| Template (1136 lines, 6 `harness-architect` lines) | Step 2 "Harness Generation" (328-345, "runs once, up front - not in a loop"). Step 3 `harness-ready` prefilter (347, filter at 374, with premise lines 349 and 381) | Step 3 item 1, the C1-C6 derivation (351-373). The Step 4 loop and Claim | Between "For each task in the ready queue:" (387) and "#### Step 4.1: Claim Task" (389) | 1008-1046 |
| Mirror (842 lines, 0 `harness-architect`) | Nothing (insertion only) | The C1-C6 derivation (340-355). The Step 2 loop and Claim | Between "For each task in the derived executable task set:" (357) and "1. **Claim**:" (359) | 172-210 |

The fixture detects the recovery section from its heading line up to the
next `### ` heading. That excludes the session-end `resolve_checkpoint`, so
the file has 2 occurrences and the section has 1. Stage confirmed that each of
the 10 ordered recovery keys occurs exactly once in each whole file, in the
same order as the checker's event order.

A diff of the two recovery sections differs only in template variables
(`{{OP_*_CHECKPOINT_MCP}}`), one Orchestrator cross-reference wording, and
"(Step 0.5 below)". So one recovery machine governs both.

**F6 - What the surface geometry actually proves (limit).** The model uses
the surface only as a set of existence and order preconditions:

* unique anchors;
* `loop < claim`;
* the template's "runs once" and `harness-ready` text present;
* the mirror's `harness-architect` count equal to 0;
* the recovery keys in order.

A failed precondition would abort with exit 2; it is not a reason code. The
pre-claim position is always `claim - 0.5`, so it lies inside the loop by
construction. N1 is rejected by its batch marker, not by the template's
up-front position, so the `upfront` geometry branch never runs. The machine is
genuinely shared. Divergence enters only through the modeled override in
N5-DIV.

**F7 - Template-only retained text outside the model (the blocker).** The
retained-text term covers the whole of each surface after the section 6.7
planned replacements. Those replacements are only template Steps 2 and 3, plus
the mirror insertion. Two template passages survive them, exist at both
`082df7b2` and `4acba14a`, and have no counterpart in the mirror:

* **Template lines 1004-1006 (Session start).** Line 1004: "Scan
  `{{DOCS_MEMORY}}/` for the most recent memory or checkpoint file ...".
  Line 1005: "If a relevant memory file exists, restore context: completed
  items, branch context, PR status, and prior build decisions." Line 1006:
  "... run the recovery state machine below before shipment validation."
  Together these place a context restore *before* the checkpoint enumeration
  and validation. Frozen plan revision 12, line 229, describes this exact
  sentence as "the template's current early sentence that restores memory
  context before checkpoint validation" and requires its removal. The
  section 6.7 replacement list does not include it.
* **Template lines 1103-1107 (Resumption Protocol).** "On session start,
  check `{{DOCS_MEMORY}}/` for a checkpoint with status `context-overflow`. If
  found, restore context from that checkpoint and resume from the recorded
  next step". This path has no operator selection, validation or
  confirmation. The same template's retained recovery protocol says "There is
  no automatic resume under any condition" (line 1034).

The fixture starts its recovery scan at the heading line 1008 and requires
enumeration as event 0. So it models neither passage. That is the correct
behavior for checkpoint-first restore, but it is silent on this text.

**F8 - The fork.**

* **Scoped reading.** "Cursor restore" means the backlogit CheckpointV1
  cursor, which is the recovery protocol's stated scope ("its OWN
  (`agent: ship`) checkpoints", with `backlogit_list_checkpoints`). Docs-memory
  context is non-authoritative, and the `context-overflow` file is a
  different artifact. Under this reading, one machine fits both surfaces: the
  fixture's machine plus an optional non-cursor memory preamble that only the
  template emits. The result is `PASS`.
* **Unscoped reading (plan revision 12's reading).** Line 1005 is a restore
  before validate-and-resolve, and lines 1103-1107 are an automatic resume
  bypass. The strict machine then contradicts template retained text. A
  permissive machine contradicts line 1034 and accepts a mis-ordering that the
  pass criterion requires it to reject. The result is `FAIL`, which reopens
  the section 6.7 activation replacement list.

The charter does not settle this fork. Section 2 says a defect is "never
resolved by a proof author choosing the more convenient reading", and run 1
set the precedent of recording `BLOCKED` in this situation.

### What Was Tried and Failed

* Invocation 1 aborted inside the fixture with `KeyError:1`. This was a
  fixture defect, and its script hash was not relayed. The corrected script
  (F1) is the one adjudicated.
* The pre-write helper's inverted clean-status check produced a false
  `BLOCKED` before any write. It was corrected and was not a gate rejection.
  The circuit breaker has not tripped: the errors differ, and Proof E stops
  here.

### Remaining Unknowns (recorded, `P3`; not grounds for this verdict)

| ID | Observation |
|---|---|
| O1 | Not modeled: multiple ship candidates with a valid explicit unique selection. The rule `len(candidates) != 1` makes the machine stricter than retained text, which allows the operator to choose one of several. The machine errs toward failing closed. No canonical trace needs this case |
| O2 | The correct terminal mappings (exit 1 to `NO_HARNESS`, exit 2 to `UNRESOLVED`) are accepted in the source, but no executed case exercises that acceptance |
| O3 | Not exercised: an API-level filter on the enumerate event (`filters != []`). N7 covers a filter after enumeration and before the anomaly scan |
| O4 | Activation note (`PE-ACTIVATE-02`): the retained C1-C6 text says the derived set "is wired into item 2's ready queue". The replacement for item 2 must keep that reference resolvable. Template line 443 (`harness_cmd` from "harness-ready metadata") and line 1064 (a checkpoint when "harness generation completes") are compatible with per-task T2 |

## PE-ACTIVATE-01 (separate row; Stage verified read-only at HEAD `6920cb7c`)

| Path | Blob at HEAD = `4acba14a` | Raw-blob SHA-256 | CRLF |
|---|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | `4ccd7fdc2d134de485487acd75bfbc105d6f40ee` (equal) | `a2451b355d27203db51515c9f72289a59a2e11af06d2910fd934fef489f4cbeb` | 0 |
| `.github/agents/_ship.agent.md` | `e22916b62f36f1c25c421882a05f4049f1862c02` (equal) | `250fc87a4275a5b7c1a5a143b6c2d7d9b97c50db1b465a84157c3c891c4c8a38` | 0 |
| `.autoharness/harness-manifest.yaml` | `251f46e8c95703ed65e421210d3b08682d79d8bc` (equal) | `e3ddbac3e4648c06442de42e2f0ecc05c5dbee645cdb9e58760b5bdd010425d0` | 0 |

`git diff 4acba14a HEAD --` is empty for the three paths, and
`git status --porcelain` is empty for them. These values match section 3.3.
The row is satisfied at `6920cb7c` only and must be rechecked at proof exit.
It does not make up for `PE-FLOW-03`.

## Matrix rows

| Row | Status after run 4 |
|---|---|
| `PE-FLOW-03` | Not satisfied. `BLOCKED` on the section 2 reading fork (F7, F8). The modeled pass criterion is met |
| `PE-ACTIVATE-01` | Satisfied at `6920cb7c` only. Recheck at proof exit |
| `PE-EVIDENCE-01` | Complete for invocation 2: the question, host, filesystem, interpreter, command, stdout and stderr hashes, fixture SHA-256, the per-case verdicts, elapsed time, file count, scratch path, gates, the refresh record and the safety statement. Invocation 1's script hash was not relayed (recorded gap; invocation 1 is not adjudicated) |
| `PE-AUTH-01` | Met. Ship wrote only scratch and the ignored cache. This Stage commit changes only this findings file |
| `PE-AUTH-02` | Met. One worktree. P-001 was taken after a successful same-invocation refresh |
| `PE-AUTH-03` and `PE-ACTIVATE-03` | Met. No authorization or claim readiness is asserted |
| `PE-SCOPE-07` | Met (see Bounds) |

## Carried-forward verdicts (unchanged)

The Proof E runs 1 to 3 remain `BLOCKED`, at `a04e1e5a`, `6ee65c4a` and
`383ae6be`. None is relabeled. This run consumes its own section 6.2 budget.

## Bounds, time, safety and tools

* **Time (60m).** Ship took 11m24s (16:55:27 to 17:06:51). There was a gap
  of 1m41s. Stage analysis ran from 17:08:32 to about 17:30, which is at most
  48m. The whole span from 16:55:27 to this commit is under 60m. **Met.**
* **Files.** 1 of 2 disposable files. **Met.**
* **Safety.** Stage wrote only this artifact. The scratch directory is
  retained. Stage deleted nothing and modified no fixture, test, source,
  charter, backlog item or Ship surface.
* **Tools (P-012 and `PE-EVIDENCE-05`).**
  * Engram, agent-intercom and graphtor-docs: the pack instructions are
    present, but Stage did not probe them this session and made no broadcast.
    Stage used Git-blob reads instead.
  * Backlogit: Stage made no call. Stage never refreshes the index
    (section 6.1), and the operator prohibited a sync. Backlog facts come from
    Ship's relay.

## Recommendation

**Conclusion:** `defer` (verdict `BLOCKED`), confidence `medium`. Confidence
is high on fixture soundness and byte reproduction. It is medium overall
because the verdict depends on an operator reading.

## Next Steps

1. **Operator decides the fork, as a charter change (PE-1.5, section 6.7
   only).** There are two options:
   * **Option A:** add template lines 1004-1006 (the memory-context restore
     before recovery) and lines 1103-1107 (the `context-overflow` automatic
     resume) to the section 6.7 planned replacements. This matches frozen plan
     revision 12 line 229 and makes them non-retained. It would also mean the
     chartered activation design changes, and the change is recorded under
     that design.
   * **Option B:** state that "cursor restore" is limited to the backlogit
     CheckpointV1 cursor, and that docs-memory context is non-authoritative
     and never drives the task cursor.
2. **Fresh admissible Ship run 5** under the fixed reading. The byte-identical
   fixture can be reused. Under Option B, add one template trace with a
   non-cursor memory preamble, which must be accepted, and one with memory
   resume, which must be rejected. Optionally close O1 to O3.
3. Recheck `PE-ACTIVATE-01` at proof exit. Nothing here authorizes a claim,
   an activation or a harvest.

## References

* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (sections 2, 3.2, 3.3, 6.1, 6.2, 6.7, 7.4, 7.9, 7.10)
* Prior runs: `docs/decisions/2026-09-24-ship-activation-proof-e-spike.md`, `docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md`, `docs/decisions/2026-09-24-ship-activation-proof-e-run3-spike.md`
* Frozen plan revision 12: `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` (lines 225-229; diagnostic input only)
* Surfaces: `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`; manifest `.autoharness/harness-manifest.yaml`
* Compound: `docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`, `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md`
* Skill: `.github/skills/spike/SKILL.md`
