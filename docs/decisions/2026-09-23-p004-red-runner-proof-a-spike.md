---
title: "Proof A - live P-004 RED conformance: runner findings (BLOCKED)"
source: "docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md"
doc_type: decision
description: "Stage-authored Proof A findings under charter PE-1.1 section 6.3. Ship's runner observations are recorded apart from the written P-004 and harness-architect contract text. Proof A is BLOCKED: no Ship invocation produced a gate-valid, charter-complete positive observation. The first run had two roster tests instead of three. The second run broke the P-011 clean-worktree precondition and put its markers in tests rather than production stubs, so it is illustrative only. The third handoff stopped before creating any scratch. How 'canonical output alone' should be read is routed to a Phase 0 decision."
docline:
  type: spike
  date: 2026-09-23
  time_box: "1h"
  conclusion: "defer"
  confidence: "medium"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "p-004"
    - "red-phase"
    - "unittest"
    - "proof-entry"
    - "ship-lifecycle"
proof: A
proof_verdict: BLOCKED
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.1"
matrix_id: PE-1.1
matrix_rows: [PE-EVIDENCE-03, PE-FLOW-02]
branch: chore/stage-176-s-workflow-defects
head_at_authoring: 89b0db6d
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
actor_invoked: false
p004_gate_evidence_for_any_task: false
review_scheduled: false
backlog_item_created: false
---

# Proof A findings - live P-004 RED conformance

## Verdict

| Field | Value |
|---|---|
| Proof | A - live P-004 RED conformance ([charter](2026-09-23-lifecycle-proof-entry-charter.md) section 6.3) |
| Matrix rows | `PE-EVIDENCE-03`, `PE-FLOW-02` |
| Verdict | **`BLOCKED`** |
| Why | No Ship invocation produced a positive observation that was both gate-valid and complete against the charter |
| Not `PASS` | The only three-roster run (invocation 2) is inadmissible. A `BLOCKED` result is never converted into `PASS` (charter section 6.1) |
| Not `FAIL` | No required rejection was observed to qualify under the written contract, and no runner classification contradicts the P-004 wording. A missing third roster test is a procedure error, not a failed proof question |
| Route | Operator. The open reading of "canonical output alone" goes to a Phase 0 decision |
| Re-execution | Allowed without a charter version bump, because `PE-FLOW-04` covers `FAIL` only. It is gated as described under Next Steps. No further automatic Proof A retry takes place in this session |

This artifact does not state that the harness-architect actor accepted or
refused any fixture. The actor was not invoked. It presents no scratch result
as P-004 gate evidence for any task, and it asserts no red-phase
confirmation, `harness-ready` state, claim readiness or publication
readiness. `187-S` remains `queued` and is not claim-ready.

## Goal

What evidence shape does the live P-004 contract accept when the canonical
whole-suite command `PYTHONPATH=src python -m unittest discover -s tests` runs
over generated tests whose production stubs each raise a distinct
`NotImplementedError` marker? Is every rejected outcome that P-004 lists
refused?

## Success Criteria

These are taken from charter section 6.3 and are not amended here:

* **A-runner (Ship, executed).** The run exits non-zero. Each of the **three**
  roster tests can be identified individually in the output with its own
  marker. The unrelated passing test does not affect the verdict. The
  characterization test does not contaminate roster attribution. The output
  shows how unittest classifies an uncaught `NotImplementedError`.
* **A-static (Stage, read-only).** That classification is consistent with
  P-004's wording, "fails with its own expected marker".
* **Required rejections.** Nine outcomes are each refused as RED evidence:
  a marker-bearing `AssertionError`, a pass, a skip, `expectedFailure`,
  `unexpectedSuccess`, a wrong marker, a cross-test marker, zero discovery of
  a roster test, and a collection or import error in a roster module.
* **Gates.** Every Ship invocation records its P-010 self-check and its P-001,
  P-002, P-011 and P-016 results. Any rejection halts execution (charter
  section 6.1; `PE-AUTH-02`).

## Scope Constraints

* **Stage did only read-only work.** Stage read the charter, the P-004, P-001
  and P-011 policy text, harness-architect Step 4 item 3 and Step 5.2, manifest
  `variables_used` lines 472-473, compound `097-S`, the Stage Role Boundary and
  one existing source test file. Stage ran no fixture command, test suite,
  build or linter. It wrote no source, template, test or configuration file,
  and it used no additional worktree. The P-016 spike-worktree exception was
  not used.
* **Stage did not re-execute anything.** Every runner fact below is Ship's
  reported observation as it was relayed to Stage. Stage did not reproduce any
  of them.
* **Stage made no mutations.** It changed no backlog item, carrier, shipment,
  stash, review, plan, configuration or `harness-ready` label. It did not
  create attempt 12 or revision 13, open a pull request or push. The two P-004
  observation-gate locks under `docs/plans/` and `docs/reviews/` were left
  untouched. Both were zero bytes when observed at session start.
* **Stage created one artifact: this file.** It was locked individually through
  the file-lock skill with a capability token and committed alone.

## Session and Tool State

| Surface | State | Note |
|---|---|---|
| agent-engram | `ENGRAM_DEGRADED` (circuit-open) | Not retried, as the operator directed. Bounded exact file reads were used instead |
| agent-intercom | `INTERCOM_DEGRADED` (unavailable) | No broadcast was possible. The P-005 record is carried in this artifact and in the session output |
| graphtor-docs | `GRAPHTOR_UNAVAILABLE` | The pack's instruction file is installed, but no server tool was exposed in this session. Stage searched no documentation |
| backlogit | `TOOL_OK` | Read-only `backlogit_get_version` probe with the update check skipped |
| Index sync (Stage Step 0.1) | Skipped | The operator scoped this session to no backlog mutation, and Stage made no semantic backlog read, stash query or shipment lookup. This is an operator-scoped deviation, not a claim that sync is unnecessary |
| Git at authoring | Clean | `git status --porcelain` was empty before writing. Branch `chore/stage-176-s-workflow-defects`, HEAD `89b0db6d`, one worktree |

## Investigation Approach

1. Scope Proof A against charter section 6.3 and matrix rows `PE-EVIDENCE-03`
   and `PE-FLOW-02`.
2. Read the normative inputs verbatim: P-004; harness-architect Step 4 item 3
   and Step 5.2; manifest `TEST_COMMAND` and `UNIMPLEMENTED_MARKER`; compound
   `097-S`.
3. Check each Ship invocation for admissibility: per-invocation gates and
   conformance to the section 6.3 setup.
4. Record runner behavior (A-runner) separately from the written-contract
   comparison (A-static).
5. List the proof obligations that are still unobserved, with the evidence
   gaps and the bounds.

## Findings

### Evidence Provenance and Admissibility

| Ref | HEAD | Preflight | Setup | Result reported by Ship | Admissibility |
|---|---|---|---|---|---|
| Invocation 1 | `5bcb00e5` | Clean | Two generated tests backed by stubs, each with a distinct `NotImplementedError` marker. One unrelated test and one characterization test, both passing | Exact canonical command, no `-v`. Exit 1. `Ran 4 tests` and `FAILED (errors=2)`. Both generated tests were named `ERROR` with matching markers. Nine rejection variants were also run (see below) | **Admissible as runner-behavior observation.** **Incomplete against the charter** for the positive case: section 6.3 requires three roster tests, and this run had two |
| Invocation 2 | Pre-`89b0db6d` | **Dirty**: `M .autoharness/config.yaml` | Three generated tests and two passing tests. The marker raises were in the test bodies, and `src/` was empty | Exact command. Exit 1. `Ran 5 tests` and `FAILED (errors=3)`. All three were named `ERROR` with test IDs and distinct markers | **Inadmissible. Illustrative only.** The P-011 precondition failed (see the next section). The setup also departs from section 6.3, which requires `src/` production stubs raising the markers |
| Invocation 3 | `89b0db6d` | Not reached | None | Ship stopped before creating any scratch. It believed P-001 could not be checked because it assumed Ship would have to run backlogit index sync, which is a mutation Ship may not perform | **No evidence.** This is a procedure halt, not a pass and not a fail |
| Orchestrator observation | `89b0db6d` | n/a | n/a | At 2026-09-23T22:34:50-07:00: `backlogit shipment list --status active --format json --no-update-check` returned native exit 0 and output `[]` | Shows no active shipment at that moment, and shows that a read-only P-001 input exists without an index sync. It does not turn invocation 3 into an executed proof |

Only the no-verbosity reruns count. Ship's earlier `-v` runs were superseded,
because section 6.3 forbids a verbosity flag and P-004 forbids substituting
the resolved command.

### Policy Violation Record (P-011, P-005)

* **What happened.** Invocation 2 wrote its scratch workspace even though its
  preflight showed `M .autoharness/config.yaml`. P-011's precondition requires
  "the current worktree is clean before the first mutation", and a scratch
  write is a workspace file write. The P-011 Violation Action is to record the
  violation through P-005 telemetry and halt. Ship proceeded instead.
* **Classification.** A **P-011 violation**, with its **P-005 recording
  obligation**. It also **contravenes `PE-AUTH-02`**, which requires any
  gate rejection to halt execution.
* **No exemption applies.** Charter section 6.1 states that no exemption from
  any policy is assumed. Neither the verification-only nature of the run nor
  the absence of a task claim exempts it from P-011.
* **State after the event.** Ship removed its scratch and did not modify the
  original configuration. The operator then committed the routing change as
  `89b0db6d`, and `git status` is clean at this authoring.
* **How it is recorded.** Intercom is unavailable, so no P-005 broadcast was
  made. No backlog telemetry write was made either, because the operator
  scoped this session to no backlog mutation. This artifact and the session
  output are the record. The final disposition of `PE-AUTH-02` belongs to the
  proof-exit report and the operator.

### Runner Behavior Observed (A-runner)

All rows come from invocation 1's exact no-verbosity runs unless marked
otherwise. Stage re-executed none of them.

| Case | What unittest emitted (default output, no `-v`) |
|---|---|
| Roster test reaching a stub that raises its own marker | A named `ERROR` entry with the test ID, whose traceback carries the marker. Exit 1 |
| Uncaught `NotImplementedError` in general | Classified as **`ERROR`**, not `FAIL` |
| Unrelated established passing test | Counted in `Ran N tests`. Not named. Did not change the exit status, which the errors already set |
| Characterization test outside the roster, passing | Counted, not named. It did not appear in the roster attribution |
| Wrong marker | A named `ERROR`. The same classification as a correct marker; only the traceback text differs |
| Cross-test marker | A named `ERROR`. The same classification; only the traceback text differs |
| Marker-bearing `AssertionError` | A named **`FAIL`** |
| Generated test passes | Only an anonymous `.`. No test name appears |
| Generated test skipped | Only an anonymous `s`. No test name appears |
| Generated test `expectedFailure` | Only an anonymous `x`. No test name appears |
| Generated test `unexpectedSuccess` | Named in the output |
| Collection syntax error in a roster module | A loader-synthesized `_FailedTest` entry instead of the roster test's identity |
| Zero discovery of the generated tests | Exit 0, `Ran 2 tests` and `OK` |
| Three roster tests (invocation 2, illustrative only) | Exit 1, `FAILED (errors=3)`, three named `ERROR` IDs with distinct markers |

### Written-Contract Comparison (A-static)

The contract is the text as written: P-004 in
[`workflow-policies.md`](../../.github/policies/workflow-policies.md);
harness-architect Step 4 item 3 and Step 5.2 in
[`SKILL.md`](../../.github/skills/harness-architect/SKILL.md); and
manifest `UNIMPLEMENTED_MARKER` = `raise NotImplementedError("...")` in
[`harness-manifest.yaml`](../../.autoharness/harness-manifest.yaml).
The actor's behavior is not in evidence.

| Case | Status under the written contract | Clause | Can it be attributed from raw output? |
|---|---|---|---|
| Own marker, reported as `ERROR` | Qualifies for that test | P-004 precondition 3; Step 5.2 | Yes. The entry names the test and the traceback carries the marker |
| `AssertionError` carrying marker text | Refused | Step 5.2 "wrong-reason failure" (a different exception type). The marker is defined as the `NotImplementedError` raise | Yes. It is reported as `FAIL`, not `ERROR` |
| Wrong marker | Refused | P-004 "missing, wrong, or cross-test markers"; Step 5.2 "different ... message" | Only when compared with the roster's test-to-marker mapping, because the classification matches a valid case |
| Cross-test marker | Refused | P-004 "credited with a different test's marker" | Only when compared with the roster mapping |
| Pass | Refused | P-004 "pass ... counts as no red-phase observation"; Step 5.2 "false positive" | Only as a roster test missing from the named `ERROR` set. The runner prints just `.` |
| Skip | Refused | P-004; Step 5.2 "skip" | Only as a roster test missing from the named set (`s`) |
| `expectedFailure` | Refused | P-004; Step 5.2 "expected-failure (xfail)" | Only as a roster test missing from the named set (`x`) |
| `unexpectedSuccess` | Refused | P-004; Step 5.2 "Pass or unexpectedSuccess" | Named in the output |
| Collection or import error | Refused | P-004 "collection/import/syntax errors"; Step 5.2 | Superficially red: the run reports an `ERROR` and exits non-zero. It is refused because the entry is a `_FailedTest` rather than a roster test ID |
| Zero discovery | Refused | P-004 precondition 2 (must exit non-zero) and the zero-discovery clause | Yes when every roster test is undiscovered: exit 0 and `OK` |

**Error versus failure.** unittest reports an uncaught `NotImplementedError`
as `ERROR`. Neither P-004 nor Step 5.2 uses unittest's `ERROR`/`FAIL`
categories. Both say a generated test "fails with its own expected failure
marker", and both define that marker as the `NotImplementedError` raise.
Stage reads "fails" as the generic non-passing outcome attributed to that
marker, so the `ERROR` classification is consistent with the wording. A
marker-bearing `AssertionError` (`FAIL`) is not. Stage found no
contradiction. As a `P3` observation, the written text never names the
`ERROR` category explicitly. This is recorded only; it is not a rewording
request.

**Written-contract gaps (observation only).** Step 5.2 says to run the
canonical command "for the harness tests", while also requiring "no runner
substitution". P-004 precondition 2 excludes any scoped or targeted subset.
Both texts agree on the exact whole-suite command. Neither says how discovery
of a generated test is shown when its outcome is anonymous in default output.

### Canonical Output Alone (Unresolved Interpretation)

The charter's Fail clause includes: "any roster test cannot be individually
attributed from canonical output alone". The observations above divide the
cases:

* **Positive RED case.** Every roster test ends in a named `ERROR` whose
  traceback carries its marker. This was observed for two tests in
  invocation 1 and, illustratively, for three in invocation 2. Here the raw
  output identifies each roster test individually.
* **Rejection cases.** These are a pass, a skip, `expectedFailure`, partial
  non-discovery, and wrong or cross-test markers. The default output either
  does not name the test or cannot tell its marker apart from a valid one. To
  refuse these cases, the evaluator compares the named `ERROR` set and its
  markers with the **known roster**. That roster is metadata in addition to
  the raw runner output.

Two readings are possible. Stage does not choose between them:

* **R1 (strict).** "Canonical output alone" excludes roster metadata. Anonymous
  outcomes then cannot be attributed to a specific roster test, and the Fail
  clause would be triggered.
* **R2 (roster-relative).** The roster is already an input to the contract.
  P-004 quantifies over "every generated harness test for the current task".
  Under R2, a roster test absent from the named `ERROR` set, or named with a
  mismatched marker, is refused fail-closed, and the anonymous outcome never
  needs to be identified.

Charter section 2 forbids a proof author from settling this by choosing the
more convenient reading. **This is routed to the operator as a Phase 0
decision:** either a charter interpretation or an operator-approved version
bump. The frozen PE-1.1 matrix is not weakened. A verbosity flag is not an
available workaround, because section 6.3 forbids one and P-004 forbids
substituting the resolved command. Until the decision is made, even a
gate-valid, complete positive run could not be judged `PASS` or `FAIL` on this
clause.

### Required Proof Still Unobserved

* **A gate-valid, charter-complete positive run.** It needs:
  * three roster tests, each reaching a production stub under `src/` that
    raises a distinct marker;
  * one unrelated passing test and one characterization test outside the
    roster;
  * the exact command with no verbosity flag;
  * a record of the Windows environment-assignment method;
  * P-010 self-check, P-001, P-002, P-011 (clean before first write) and
    P-016 results, all recorded.
* **Per-test partial non-discovery.** Invocation 1 observed only the case where
  every generated test went undiscovered (exit 0). The charter wording, "zero
  discovery of a roster test", also covers one roster test going undiscovered
  while its siblings `ERROR`. The exit status would then still be non-zero,
  and only a roster comparison would catch it. This variant has not been
  observed.
* **Import error.** Only the syntax-error form of a collection failure was
  reported. The import-error form named in section 6.3 was not reported
  separately.
* **Fields missing for `PE-EVIDENCE-01`.** Ship's relayed evidence does not
  include the fields listed below. Stage did not reconstruct any of them.
  * the recorded scratch path;
  * host OS and version, filesystem and interpreter version;
  * raw stdout and stderr, or their SHA-256;
  * the fixture listing with a SHA-256 for each file;
  * elapsed time and file count;
  * per-invocation gate records;
  * the before-and-after `git status --porcelain` safety statement.

### Time and File Bounds

| Bound | Charter value | Recorded |
|---|---|---|
| Time (Stage analysis and Ship execution together) | 60 minutes | Stage analysis ran from 2026-09-23T22:35:30-07:00 to about 22:50-07:00 when this artifact was written. This artifact's commit timestamp is the authoritative end. Ship's elapsed time was **not reported** for any invocation |
| Files | 3 disposable | **Not reported** for any invocation |

`PE-SCOPE-07` therefore cannot be evaluated from the available evidence, and
it is not recorded as met. Two accounting questions are open, and both go to
the operator with the Phase 0 decision:

* whether aborted or inadmissible invocations consume Proof A's 60-minute
  bound;
* how the three-file bound counts a setup of three roster tests, one unrelated
  test, one characterization test and `src/` stubs, plus the nine rejection
  variants.

Stage does not assert that any overrun occurred.

### Matrix Row Status (Proof A Only; Not a Proof-Exit Audit)

| Row | Status from this artifact |
|---|---|
| `PE-EVIDENCE-03` | Not met. The runner half has no gate-valid, charter-complete positive observation. The static half is recorded above |
| `PE-FLOW-02` | Proof A is `BLOCKED`, which is neither `PASS` nor operator-deferred. No Phase 2 artifact exists |
| `PE-AUTH-02` | Contravened by invocation 2, which did not halt at the P-011 gate. Disposition is left to the proof-exit report |
| `PE-AUTH-03`, `PE-ACTIVATE-03` | This artifact asserts no P-004 red, claim, `harness-ready` or publication authority |
| `PE-EVIDENCE-01` | Incomplete; see the missing fields above |
| `PE-EVIDENCE-05` | Recorded under Session and Tool State |
| `PE-SCOPE-06` | Stage did not touch either lock |
| `PE-SCOPE-07` | Cannot be evaluated |
| `PE-FLOW-04` | Not engaged, because the verdict is not `FAIL` |

### What Was Tried and Failed

* **Invocation 1** was gate-valid but had two roster tests instead of three.
  This is a procedure error.
* **Invocation 2** reached three roster tests but ran on a dirty worktree
  (P-011) with its markers in the tests. It is inadmissible.
* **Invocation 3** halted before any write, on the mistaken premise that
  checking P-001 requires Ship to sync the index. The Orchestrator's read-only
  CLI observation shows that premise was unnecessary. As P-001 is written, its
  precondition also covers `Active` tasks under other top-level items and any
  pending post-merge closure, so the active-shipment listing is one part of
  that input. The registered read-only task listing (`backlogit list` with
  `--status active`) covers the task half. Stage ran neither command.
* **The `-v` runs** were superseded by the exact no-verbosity reruns.

### Remaining Unknowns

* Whether R1 or R2 is the reading of "canonical output alone" (Phase 0).
* The per-test partial non-discovery and import-error variants.
* How the time and file bounds are counted for the next execution.
* The host facts and hashes for every invocation already run.

## Recommendation

**Conclusion**: defer
**Confidence**: medium

Defer Proof A pending operator action. The verdict is `BLOCKED`, not `FAIL`.
The runner behavior already observed is consistent with the written contract:
an own-marker `NotImplementedError` is a named `ERROR`, and every listed
rejection is refused under the written text. What is missing is a gate-valid,
complete positive observation and a decision on the "canonical output alone"
reading. Confidence is medium rather than high for three reasons: the runner
facts are relayed rather than hashed, several evidence fields are missing, and
the R1/R2 reading could turn a future complete run into `FAIL` rather than
`PASS`.

## Next Steps

1. **Operator, Phase 0.** Decide the "canonical output alone" reading (R1 or
   R2) and the time and file-bound accounting. Record the decision as a
   charter interpretation or as a version bump. Stage does not make either
   decision and does not amend PE-1.1.
2. **Next Ship execution.** It may run only after the operator directs it. In
   the same invocation, and immediately before its first scratch write, Ship
   must record:
   * a fresh P-010 self-check;
   * a fresh read-only P-001 CLI check (active shipments and active tasks);
   * P-002;
   * P-011, with `git status --porcelain` clean;
   * P-016, with `git worktree list --porcelain` showing exactly the current
     worktree;
   * the recorded scratch path.

   If any check fails, Ship halts and writes nothing. The run should carry the
   complete positive setup, the rejection variants (including per-test partial
   non-discovery and an import error), and every `PE-EVIDENCE-01` field.
3. **No further automatic Proof A retry** in this session.
4. **Stage** records any later evidence in a new findings artifact that
   cross-references this one. This artifact is not edited.
5. **Nothing is scheduled or created.** There is no review, backlog item,
   shipment action, attempt 12 or revision 13. `187-S` stays `queued`.

## References

* Charter: [2026-09-23-lifecycle-proof-entry-charter.md](2026-09-23-lifecycle-proof-entry-charter.md), sections 2, 6.1, 6.2, 6.3, 7 (commit `1ad7c03a`)
* Parent decision: [2026-09-23-lifecycle-review-convergence-reset-deliberation.md](2026-09-23-lifecycle-review-convergence-reset-deliberation.md)
* Related decision: [2026-09-20-pr457-bounded-review-convergence-deliberation.md](2026-09-20-pr457-bounded-review-convergence-deliberation.md)
* Policies (P-001, P-004, P-005, P-011): [workflow-policies.md](../../.github/policies/workflow-policies.md)
* Actor: [harness-architect SKILL.md](../../.github/skills/harness-architect/SKILL.md), Step 4 item 3 and Step 5.2
* Manifest: [harness-manifest.yaml](../../.autoharness/harness-manifest.yaml), `variables_used.TEST_COMMAND` and `variables_used.UNIMPLEMENTED_MARKER` (lines 472-473)
* Compound: [097-S-canonical-unittest-gate.md](../compound/097-S-canonical-unittest-gate.md)
* Stage Role Boundary: [_stage.agent.md](../../.github/agents/_stage.agent.md)
* Spike skill: [spike SKILL.md](../../.github/skills/spike/SKILL.md)
* File-lock skill: [file-lock SKILL.md](../../.github/skills/file-lock/SKILL.md)
* Existing text-contract tests (read, not run): [test_harness_architect_p004_contract.py](../../tests/test_harness_architect_p004_contract.py), `RedEvidenceMarkerCorrelationTests` and `PolicyQuantifierCoherenceTests`. These assert the presence of policy and actor text only. They do not exercise runner behavior and are not Proof A evidence
