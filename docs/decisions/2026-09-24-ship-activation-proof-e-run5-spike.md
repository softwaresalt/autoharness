---
title: "Proof E run 5 (PE-1.5) - Ship per-task actor and checkpoint-first state machine: findings (PASS, synthetic state-machine model)"
source: "docs/decisions/2026-09-24-ship-activation-proof-e-run5-spike.md"
doc_type: decision
description: "Stage's formal findings for Proof E run 5 under charter PE-1.5, section 6.7 (with the PE-1.5 retained-text replacement set, post-activation restore contract and restore-mis-ordering scope) and section 6.1. The execution was admissible. In the one current worktree at HEAD d31d7b42, Ship ran its CLI index refresh (exit 0, stdout 23 B). Only ignored backlog db, wal and shm cache changed. Ship then wrote one new ignored fixture, .proof-scratch/E-run5-20260924-173853/proof_e_state_machine.py (20988 B, 28ce5fc5...8d893), and kept the run 4 fixture unchanged (15043 B, 33cd01f4...270dc). Stage re-hashed both read-only and read run 5 fully. One fixture invocation exited 0 and printed 17 cases, all passed, with 0 failed, across 2 surfaces: C1 and C2 accepted; the 13 run 4 negatives rejected for their intended reasons; the new N8 rejected as memory_restore_before_checkpoint_validation and the new N9 as context_overflow_resume_without_validation_confirmation. Without running the fixture, Stage predicted the exact stdout bytes from the source (1317 B CRLF, e4dc54ca...2fc0), which equals Ship's relay. Grading now uses exact reason equality, and the checker never sees expected values. The fixture excludes exactly the two PE-1.5 template spans (lines 1004-1006 and 1103-1107 at HEAD, which equals 4acba14a) and checks the ten ordered recovery keys on the retained text of both surfaces. Stage's own retained-text audit finds no other memory, cursor, phase or next-action restore path in either surface. So the section 6.7 pass criterion is met and the fail clause is not established. The verdict is PASS for PE-FLOW-03, scoped to a synthetic state-machine model over raw HEAD blobs. It is not activation evidence. Limitations L1-L7 are recorded. Runs 1-4 stay BLOCKED as recorded. No production, charter, backlog or Ship-source edit. No claim authority. 187-S stays queued and frozen."
docline:
  type: spike
  date: 2026-09-24
  time_box: "60m"
  conclusion: "proceed"
  confidence: "high"
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
proof_run: 5
proof_verdict: PASS
proof_verdict_basis: "section 6.7 (PE-1.5) pass criterion met by a synthetic state machine over raw HEAD blobs of both Ship surfaces, with the two PE-1.5 template spans excluded as planned replacements; fail clause not established; Stage retained-text audit clean"
proof_verdict_scope: "synthetic trace model; surfaces used as existence and order preconditions only; not runtime, activation or claim evidence"
fixture_execution_admissible: true
fixture_pass_criterion_met_over_modeled_text: true
fail_clause_established: false
behavior_disproven: false
prior_run_artifacts:
  - {run: 1, path: docs/decisions/2026-09-24-ship-activation-proof-e-spike.md, commit: a04e1e5a, verdict: BLOCKED, matrix: PE-1.2, changed: false}
  - {run: 2, path: docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md, commit: 6ee65c4a, verdict: BLOCKED, matrix: PE-1.3, changed: false}
  - {run: 3, path: docs/decisions/2026-09-24-ship-activation-proof-e-run3-spike.md, commit: 383ae6be, verdict: BLOCKED, matrix: PE-1.3, changed: false}
  - {run: 4, path: docs/decisions/2026-09-24-ship-activation-proof-e-run4-spike.md, commit: 945a224e, verdict: BLOCKED, matrix: PE-1.4, changed: false}
prior_run_verdicts_changed: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.5"
charter_commit: d31d7b42
matrix_id: PE-1.5
charter_sections: ["2", "3.4", "6.1", "6.7"]
matrix_rows: [PE-FLOW-03, PE-ACTIVATE-01]
evidence_rows_assessed: [PE-EVIDENCE-01, PE-EVIDENCE-05, PE-AUTH-01, PE-AUTH-02, PE-AUTH-03, PE-SCOPE-07, PE-ACTIVATE-03]
scratch_path: ".proof-scratch\\E-run5-20260924-173853\\"
fixture_files:
  - {name: proof_e_state_machine.py, bytes: 20988, sha256: 28ce5fc5a8ce2ed8784c14df89b263196248bbe84178442b7c937aa28c28d893, stage_verified: true, git_ignored_by: ".gitignore:10 .proof-scratch/"}
historical_fixture_preserved:
  - {path: ".proof-scratch\\E-run4-20260924-170243\\proof_e_state_machine.py", bytes: 15043, sha256: 33cd01f4221b00ddc3e9d44ea381d79f0f608afa334d1457dde6a18e169270dc, stage_verified: true}
fixture_command: "C:\\Python\\Python314\\python.exe -B .proof-scratch\\E-run5-20260924-173853\\proof_e_state_machine.py"
invocations:
  - {n: 1, native_exit: 0, stdout_bytes: 1317, stdout_sha256: e4dc54ca55a261149862b937e9b11b9ddd16c11353f56a911f6674726be42fc0, stdout_stage_reproduced_from_source: true, stderr_bytes: 0, stderr_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855}
non_fixture_events: ["one PowerShell copy guard failed before any write; a later safe copy succeeded; not a fixture invocation"]
cases_total: 17
cases_passed: 17
cases_accept: [C1, C2]
cases_reject: [N1, N2-V, N3, N4-DOC, N4-RED, N4-E1, N4-E2, N5-DIV, N5-AFTER, N2-S, N6-AUTO, N6-NONE, N7, N8, N9]
grading: "exact reason equality"
checker_receives_expected: false
host: {os: "Windows 11", filesystem: NTFS, interpreter: "Python 3.14.3"}
index_refresh: {transport: CLI, command: "backlogit sync", native_exit: 0, stdout_bytes: 23, stdout_sha256_relayed_prefix: "cf46e51", stderr: "not relayed", changed: ["backlog db (ignored)", "backlog db-wal (ignored)", "backlog db-shm (ignored)"]}
checkpoint_scan: {filter: none, total: 71, resolved: 70, abandoned: 1, quarantined: 0, active: 0, official_get_valid: true, source: "Ship relay"}
p001_active_counts: {work: 0, source: "Ship relay"}
activation_check: {row: PE-ACTIVATE-01, comparator: 4acba14a, head: d31d7b42, blobs_equal: true, tracked_diff_empty: true, porcelain_empty: true, stage_verified: true, recheck_required_at_proof_exit: true}
branch: chore/stage-176-s-workflow-defects
head_at_ship_execution: d31d7b42
head_at_authoring: d31d7b42286ccce005d7f46f444bc5ded9b94443
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
operator_decision_required: none
time_bound_status: met
file_bound_status: "met (1 of 2 disposable files in the run 5 scratch directory)"
scratch_cleanup_status: "retained; Stage deleted nothing"
stage_model_route: "claude-opus-5.5/anthropic/high requested; unverified by Stage (route not self-verifiable)"
---

# Proof E run 5 findings (PE-1.5): Ship per-task actor and checkpoint-first state machine

## Verdict

| Field | Value |
|---|---|
| Proof | E, run 5 ([charter](2026-09-23-lifecycle-proof-entry-charter.md) section 6.7 as of PE-1.5; section 6.1) |
| Matrix rows | `PE-FLOW-03` (the Proof E verdict); `PE-ACTIVATE-01` (a separate check, below) |
| Verdict | **`PASS`**, scoped to a synthetic state-machine model over raw HEAD blobs of both Ship surfaces |
| What passed | The execution was admissible, with exactly one fixture invocation. The fixture is sound: it hardcodes no expected result, and it grades by exact reason equality. All 17 cases were really evaluated, and each produced its intended outcome and reason. Stage reproduced Ship's stdout bytes from the source without running it |
| Why the run 4 blocker is closed | PE-1.5 moved template lines 1004-1006 and 1103-1107 into the planned replacements. The fixture excludes exactly those spans from retained text (F3). N8 and N9 reject the two restore paths that PE-1.5 brought into scope (F2). Stage's retained-text audit finds no other restore path in either surface (F4) |
| Why not `FAIL` | One shared checker accepts C1 and C2 on both surfaces and rejects every chartered mis-ordering on both. No retained text contradicts it (F4). The fail clause is not established |
| Scope limit | The surfaces act only as existence and order preconditions. This is not evidence of runtime agent behavior, of the activation wording, or of claim readiness (limitations L1-L7) |

This artifact asserts no activation, claim readiness, publication readiness,
`harness-ready` state or P-004 red confirmation (`PE-ACTIVATE-03`,
`PE-AUTH-03`). The harness-architect actor was not invoked. `187-S` is not
claim-ready and remains queued and frozen. The run 1-4 artifacts are unchanged.

## Goal

Charter section 6.7 asks where exactly the per-task harness call sits, and
whether one state machine is consistent with both the exact template and the
exact installed mirror. PE-1.5 adds the Session start memory restore and the
`context-overflow` Resumption Protocol to the template's planned replacements.
It also extends the mis-ordering "cursor restore before checkpoint
validate-and-resolve" to memory-context, phase and next-action restore from any
source.

## Success Criteria (section 6.7, PE-1.5; pass criterion text unchanged)

* **Pass.** The fixture accepts exactly the canonical trace and rejects each
  of these mis-orderings:
  * the harness invoked once before the loop instead of per task;
  * a restore before validate-and-resolve, now including a docs-memory or
    `context-overflow` restore before contract rule 1, or a memory-checkpoint
    resume that bypasses it;
  * the harness before checkpoint validation;
  * proceeding on process status without a validated document;
  * divergent template/mirror placement;
  * a resolve before a confirmed resume, or on ambiguous state.
* **Fail.** No single state machine satisfies both files without contradicting
  retained text.
* **Boundary.** Neither file is edited.

## Scope Constraints

Stage did read-only analysis only:

* `git rev-parse`, `git cat-file blob`, `git show` and `git diff --no-index` of
  the two scratch fixtures;
* in-process SHA-256 and line counts over raw HEAD blobs;
* reading the fixture source, and computing the predicted stdout bytes from a
  hand-built string.

Stage did not run the fixture, any test, build or lint. It did not refresh the
index, call any backlog CLI or MCP operation, or create a worktree (section
6.1; `PE-AUTH-01`). Stage's usual Step 0.1 index sync is deliberately not run,
because the charter reserves the refresh to Ship during proofs. Compound
consulted, as in run 4:
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`.
Its lesson prompted the whole-surface retained-text audit in F4.

## Ship execution (as relayed to Stage)

| Item | Relayed result |
|---|---|
| Worktree | One worktree, at HEAD `d31d7b42` on `chore/stage-176-s-workflow-defects`. Clean. No active work |
| Index refresh | CLI `backlogit sync`, exit 0. Stdout 23 B, SHA-256 relayed with prefix `cf46e51` (the same length and prefix as run 4's `cf46e51c...e873`). Stderr was not relayed. Only the ignored backlog db, wal and shm cache changed |
| Checkpoint scan | Unfiltered: 71 checkpoints, 70 resolved and 1 abandoned. 0 quarantined and 0 active. The official get validated as `true`. No recovery was triggered |
| Protected surfaces | The template, mirror and manifest Git blobs equal the `PE-ACTIVATE-01` baseline `4acba14a`, before and after execution |
| Pre-write event | One PowerShell copy guard, not a fixture invocation, failed before any write. A later safe copy succeeded. No write happened under the failed guard |
| Scratch | `.proof-scratch\E-run5-20260924-173853\`. One file, no `__pycache__` (`-B`). Git-ignored via `.gitignore:10`. The run 4 scratch directory was preserved |
| Invocation | `C:\Python\Python314\python.exe -B .proof-scratch\E-run5-20260924-173853\proof_e_state_machine.py`. Exactly one invocation. Exit 0. Stdout 1317 B, `e4dc54ca55a261149862b937e9b11b9ddd16c11353f56a911f6674726be42fc0`. Stderr 0 B (the SHA-256 of empty input) |
| Summary | 17 cases, 17 passed and 0 failed, across 2 surfaces |
| Host | Windows 11, NTFS, Python 3.14.3 |
| Authority | Ship did not claim or edit any backlog item, and made no commit, PR or push |

## Findings

### What Was Discovered

**F1 - The fixture is what Ship reported, and run 4 was preserved.** Stage's
own reading shows 20988 B, SHA-256 `28ce5fc5...8d893`, one file, and
Git-ignored. The run 4 fixture still reads 15043 B, `33cd01f4...270dc`. A
read-only diff shows 107 lines added and 6 removed. The additions are:

* the two template replacement spans and their anchor checks;
* the mirror guard;
* `memory_restore_violation`, called first in `check`;
* cases N8 and N9;
* the `ANCHORS` line;
* exact reason equality in grading, where run 4 used a substring match.

The rest of `check` is unchanged from run 4, so the run 4 cases keep their
run 4 logic.

**F2 - Byte-exact reproduction and case logic.** The predicted stdout has 19
lines: the `ANCHORS` line, one `{id} EXPECTED={X} ACTUAL={X} reason={r}` line
per case, and `SUMMARY cases=17 passed=17 failed=0 surfaces=2`. Windows
text-mode stdout writes CRLF.

* Predicted CRLF: 1317 B, `e4dc54ca...2fc0`. This equals Ship's relay.
* The LF form would be 1298 B, `dae51e4f...de4e`, and does not match.

By manual trace, each case reaches its intended branch first:

* C1, C2 and the 13 run 4 negatives contain no memory events. So
  `memory_restore_violation` returns `None`, and each case reaches the same
  run 4 branch and reason (run 4 F2).
* **N8** starts with a docs-memory `memory_restore`, followed by a
  `next_action_restore`, before enumeration. It is rejected at event 0 as
  `memory_restore_before_checkpoint_validation`.
* **N9** runs enumerate, anomaly and partition with one active `ship`
  candidate, then a `context_overflow_resume` with no select, owner or
  confirm. It is rejected as
  `context_overflow_resume_without_validation_confirmation`.

`check(trace, surf, override)` never receives the case ID, the `expected`
flag or the wanted reason, as in run 4. Grading now requires
`reason == want_reason`. So a negative rejected for any other reason would
count as a failure.

**F3 - The anchor scope matches PE-1.5 exactly.** At HEAD, the template has
1136 lines, LF only (106843 B, `a2451b35...cbeb`). The mirror has 842 lines,
LF only (78902 B, `250fc87a...8a38`). For both, Python `splitlines()` agrees
with the LF count, so the fixture's 0-based indexes map directly to file
lines.

| Surface | Excluded as planned replacement | Charter PE-1.5 at `4acba14a` | Retained halt text |
|---|---|---|---|
| Template | `session_memory_restore` = indexes 1003 to 1006 exclusive = lines 1004-1006 (scan, restore, recovery transition) | Lines 1004-1006 | - |
| Template | `context_overflow_resume` = heading 1103 through line 1107 | Lines 1103-1107 | Lines 1099-1101 ("record the checkpoint path as the resumption point") stay retained, as contract rule 2 requires |
| Mirror | Nothing. The fixture aborts if the mirror contains `{{DOCS_MEMORY}}/`, a `### Resumption Protocol` heading or `context-overflow` | No matching passage | - |

Each anchor must be unique and in order, or the fixture exits 2. The spans may
not overlap. `recovery_contract` then runs on the retained lines. Stage
independently confirmed the following for both surfaces:

* Each of the ten ordered recovery keys occurs exactly once in the recovery
  section, in checker order. The section is template lines 1008-1046 and
  mirror lines 172-210.
* "no automatic resume under any condition" is retained at template line 1034
  and mirror line 198.
* There are 6 `harness-architect` lines in the template and 0 in the mirror.

The `ANCHORS` line is a literal string. It is printed only after
`main` confirms these facts: the template has 2 replacement spans, the mirror
has none, and both recovery contracts are retained. So it certifies a guard;
it is not a computed count (L2).

**F4 - Stage's retained-text audit is clean.** Stage searched both raw HEAD
blobs for `DOCS_MEMORY`, `docs/memory`, `context-overflow`, `restore`,
`resum` and `Session start`.

* **Template.** Outside the two excluded spans and the retained recovery
  protocol, every `{{DOCS_MEMORY}}/` hit is a write, not a restore: lines 560,
  578, 958 and 964, 1062, 1084, and 1095-1101. Every other `restore` hit is a
  scoped `git restore` of archive files (836-856), or text about a resumed
  manifest (279) or an escalation payload reference (922).
* **Mirror.** Every `docs/memory/` hit is a write or a permission row: lines
  53, 730, 832 and 835. There is no session-start restore, no Resumption
  Protocol and no `context-overflow`. Other hits are the intercom restore at
  153, a resumed manifest at 327 and the payload reference at 795.
* **Contract rule 3 still holds in retained text.** The retained recovery
  introduction says Ship applies the lifecycle "before shipment validation"
  (template lines 1010-1012, mirror lines 174-176).

So no retained text restores memory context, cursor, phase or next-action
intent before the recovery state machine, and none resumes around it. One
machine fits both surfaces.

### What Was Tried and Failed

Nothing in the fixture failed. The copy guard's failure was a non-fixture
pre-write step that wrote nothing. It is recorded and not adjudicated.

### Limitations (recorded, `P3`; not grounds to change this verdict)

| ID | Limitation |
|---|---|
| L1 | The mirror guard's `{{DOCS_MEMORY}}/` test can never match a rendered mirror, which says `docs/memory/`. Only the heading and `context-overflow` tests are independent of rendering. Stage's `docs/memory` audit (F4) closes the gap for this HEAD. A future fixture should test the rendered form |
| L2 | `ANCHORS ... mirror_matches=0 excluded=2` is a guarded literal, not a printed measurement (F3) |
| L3 | The event vocabulary is closed. `check` ignores unknown event types. So a docs-memory `phase_restore` or `cursor_restore` event would be accepted silently. Phase and cursor restore are modeled only as the CheckpointV1 `restore` event (N2-V). Memory-source restore is modeled only as `memory_restore`, `next_action_restore` and `context_overflow_resume` |
| L4 | Branch coverage is partial. N8 exercises only the "before enumerate or anomaly" branch. Two memory branches are not executed: a candidate present without select, owner and confirm; and the post-validation next-action branch (a `next_action_restore` event or `restores_next_action: true`). N9 exercises only "missing select, owner or confirm". The invalid-selection branch and `context_overflow_memory_cursor_forbidden` are not executed. No positive case exercises an allowed post-validation `memory_restore` |
| L5 | A `context_overflow_resume` that comes after a full valid recovery, and that restores no next action, is accepted: `memory_restore_violation` returns `None`, and `check` ignores the event. It restores nothing, so it does not break contract rule 2, but no case exercises it. With zero candidates, any `context_overflow_resume` is rejected. That is stricter than rule 3 requires, and it is fail-closed |
| L6 | Replacement is modeled as exclusion only. The fixture does not model the `PE-ACTIVATE-02` replacement wording, which the charter leaves to the activation task. That wording must keep a session-start invocation of the recovery machine before shipment validation (rule 3), because excluded line 1006 is the template's Session start pointer to it |
| L7 | Carried from run 4: O1 (a valid unique selection among several candidates is not modeled; the rule `len(candidates) != 1` is stricter), O2 (the correct terminal mappings for exits 1 and 2 are accepted in source but not exercised), O3 (an API-level `filters != []` is not exercised) and O4 (the retained C1-C6 wiring note for `PE-ACTIVATE-02`) |

None of L1-L7 shows retained text that contradicts the machine, or a
chartered mis-ordering that is accepted. Each one narrows what this `PASS`
proves. None reverses it.

## PE-ACTIVATE-01 (separate row; Stage verified read-only at HEAD `d31d7b42`)

| Path | Blob at HEAD = `4acba14a` | Raw-blob SHA-256 | CRLF |
|---|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | `4ccd7fdc2d134de485487acd75bfbc105d6f40ee` (equal) | `a2451b355d27203db51515c9f72289a59a2e11af06d2910fd934fef489f4cbeb` | 0 |
| `.github/agents/_ship.agent.md` | `e22916b62f36f1c25c421882a05f4049f1862c02` (equal) | `250fc87a4275a5b7c1a5a143b6c2d7d9b97c50db1b465a84157c3c891c4c8a38` | 0 |
| `.autoharness/harness-manifest.yaml` | `251f46e8c95703ed65e421210d3b08682d79d8bc` (equal) | unchanged from run 4 | 0 |

`git diff 4acba14a HEAD --` is empty for the three paths, and
`git status --porcelain` is empty. The row is satisfied at `d31d7b42` only and
must be rechecked at proof exit. It does not substitute for `PE-FLOW-03`.

## Matrix rows

| Row | Status after run 5 |
|---|---|
| `PE-FLOW-03` | **Satisfied** (`PASS`, synthetic model; L1-L7) |
| `PE-ACTIVATE-01` | Satisfied at `d31d7b42` only. Recheck at proof exit |
| `PE-EVIDENCE-01` | Substantially complete: the question, host, filesystem, interpreter, command, stdout and stderr bytes and hashes, the fixture SHA-256, per-case verdicts, file count, scratch path, gates, the refresh result and the safety statement. Recorded gaps: Ship's elapsed time and the refresh stderr were not relayed, and the refresh stdout hash was relayed only as a prefix. The refresh itself is verified by its exit 0 and the ignored-cache-only change, so the `BLOCKED` refresh clause does not apply |
| `PE-AUTH-01` | Met. Ship wrote only scratch and the ignored cache. This Stage commit changes only this findings file |
| `PE-AUTH-02` | Met. One worktree. P-001 was taken after a successful refresh |
| `PE-AUTH-03` and `PE-ACTIVATE-03` | Met. No authorization or claim readiness is asserted |
| `PE-SCOPE-07` | Met (see Bounds) |

## Carried-forward verdicts (unchanged)

Proof E runs 1 to 4 remain `BLOCKED` at `a04e1e5a`, `6ee65c4a`, `383ae6be`
and `945a224e`, each under the version it was recorded against. None is
relabelled. Run 4's modeled result is not turned into a `PASS`. This `PASS`
belongs to run 5 alone, under PE-1.5, and uses run 5's own section 6.2
budget.

## Bounds, time, safety and tools

* **Time (60m).** Ship's scratch directory is stamped 17:38:53 (-07:00). The
  task reached Stage at 17:45:12, and this commit follows within the same
  hour. **Met.**
* **Files.** 1 of 2 disposable files in the run 5 scratch directory. **Met.**
* **Safety.** Stage wrote only this artifact. Both scratch directories are
  retained. Stage deleted nothing and modified no fixture, test, source,
  charter, manifest, backlog item or Ship surface.
* **Tools (P-012 and `PE-EVIDENCE-05`).** Stage made no backlogit call and ran
  no refresh (section 6.1). Backlog and checkpoint facts come from Ship's
  relay. Engram, agent-intercom and graphtor-docs were not probed, and no
  broadcast was made. Stage used raw Git-blob reads instead.

## Recommendation

**Conclusion:** `proceed` (verdict `PASS` for `PE-FLOW-03`), confidence
`high` on fixture soundness, byte reproduction, anchor scope and the
retained-text audit. The limitations bound the claim to the synthetic model.

## Next Steps

1. Record Proof E run 5 `PASS` in the proof-exit accounting under PE-1.5.
   Proof exit still depends on every other section 8 condition, including
   Proof G's Linux evidence.
2. At activation (`PE-ACTIVATE-02`), write the replacement wording for both
   template spans to the post-activation restore contract. Keep the
   session-start recovery invocation (L6) and the C1-C6 wiring (O4).
3. When the post-activation fixture is built, close L1, L3, L4 and L5 (the
   rendered mirror form, an open event vocabulary that fails closed, and the
   branches not yet exercised).
4. Recheck `PE-ACTIVATE-01` at proof exit. Nothing here authorizes a claim,
   an activation or a harvest.

## References

* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (sections 2, 3.4, 6.1, 6.2, 6.7, 7.4, 7.9, 7.10)
* Prior runs: `docs/decisions/2026-09-24-ship-activation-proof-e-spike.md`, `docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md`, `docs/decisions/2026-09-24-ship-activation-proof-e-run3-spike.md`, `docs/decisions/2026-09-24-ship-activation-proof-e-run4-spike.md`
* Surfaces: `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`; manifest `.autoharness/harness-manifest.yaml`
* Compound: `docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`
* Skill: `.github/skills/spike/SKILL.md`
