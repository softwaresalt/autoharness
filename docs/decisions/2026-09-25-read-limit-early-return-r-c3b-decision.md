---
title: "R-C3b decided: the harness-surface resolver stops at the first read-limit error (early return); class 1 still dominates only for a disagreement already observed"
source: "docs/decisions/2026-09-25-read-limit-early-return-r-c3b-decision.md"
doc_type: decision
description: "Architecture decision that closes OD-10, decides IM-16 and settles R-C3b. The question: in the harness-surface resolver, a read-limit error (FILE_COUNT_LIMIT, TOTAL_SIZE_LIMIT or FILE_SIZE_LIMIT) occurs first, and a later recheck would complete with a disagreement. Which reason code is reported? Decision: early return. On the first read-limit error, at any ReadStage and in deterministic generation order, the resolver issues no further read or recheck request and returns UNRESOLVED / 2 with that ReadErrorCode as reason_code, and the diagnostics keep the native ReadErrorCode and ReadStage (Decision 2 item 4 of the 2026-09-24 read-budget decision). This closes, for the resolver, the part that Decision 2 item 5 left open. Class 1 still dominates class 1b as Decision 2 item 2 says, but only for what was already observed: a recheck that completed with a disagreement before the first read-limit error gives INPUT_CHANGED_DURING_RESOLUTION. Because no recheck can complete after a read-limit error, the R-C3b variant (read-limit error first, later completed disagreeing recheck) cannot be reached by construction, and its outcome is the read-limit code. Both outcomes are UNRESOLVED / 2, so safety is unchanged. No code, class, state, exit or schema is added or changed, and the OD-11-ratified 47-code list and precedence stand. The decision was made by the Orchestrator under the operator's explicit assignment (2026-09-25T18:12:40-07:00) and is recorded by Stage. The operator may veto it. Tests of both orders are an implementation obligation (Phase 2, P-002/P-004), not a new proof run. IM-03 can now be frozen once those tests exist. No proof-entry row changes (30 MET, 0 MET-COND, 7 Windows-met with Linux PENDING, 3 deferred, 40)."
date: 2026-09-25
created: 2026-09-25
status: decided
decision_status: decided
deciders: Orchestrator (under the operator's explicit assignment)
recorded_by: Stage
operator_authorization: "2026-09-25T18:12:40-07:00 - operator, verbatim: 'OD-10: I'm assigning you the architecture decision.' ('you' is the Orchestrator). The Orchestrator made the decision and Stage records it. The operator may veto it"
operator_assignment_at: "2026-09-25T18:12:40-07:00"
operator_assignment_relayed_by: Orchestrator
operator_may_veto: true
docline:
  type: decision
  date: 2026-09-25
  conclusion: "r-c3b-decided-early-return-on-first-read-limit-error-class-1-dominates-only-for-already-observed-disagreement-od-10-closed-im-16-decided-im-03-freezable-after-tests"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "read-budget"
    - "reducer"
    - "reason-taxonomy"
    - "resolver-contract"
    - "ship-lifecycle"
resolves:
  - "OD-10 (architecture decision assigned by the operator to the Orchestrator)"
  - "IM-16 decision part (R-C3b); the tests of both orders stay an implementation obligation"
  - "R-C3b (Proof C run 4: DISPUTED_NOT_ASSUMED)"
amends:
  - {path: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md, commit: 286aa4af, section: "Decision 2 item 5", effect: "closes, for the resolver, the question it left open: after the first read-limit error the resolver issues no further read or recheck request. The file is not edited"}
relates:
  - {path: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md, commit: 286aa4af, section: "Decision 2 item 2", relation: "unchanged; class 1 still dominates class 1b for a disagreement already observed on a completed recheck. Early return decides which observations can exist"}
  - {path: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md, commit: 286aa4af, section: "Decision 2 items 1, 3 and 4", relation: "unchanged and relied on"}
  - {path: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md, commit: e65887d8, section: "6.5", relation: "governing reason set and ratified candidate unchanged; class 1b first-occurrence rule kept. The file is not edited"}
  - {path: docs/decisions/2026-09-24-surface-taxonomy-proof-c-run4-spike.md, commit: 4c6e2701, relation: "raised R-C3b as DISPUTED_NOT_ASSUMED; its read_limit_first_variant (FILE_COUNT_LIMIT) is the outcome chosen here"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md, commit: a04dea18, relation: "IM-16 row, OD-10 row, IM-03 row, PE-DATA-01 R-C3b note"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-3.md, commit: 347771bd, relation: "OD-10 routed to an architecture decision; IM-16 route"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-4.md, commit: b8a7b100, relation: "OD-11 ratified; IM-17 closed; IM-03 finality depends only on IM-16; row counts checked against it"}
parent_decision: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.7"
charter_commit: e65887d8
charter_edited: false
prior_decision_edited: false
matrix_id: PE-1.7
head_at_authoring: b8a7b1003e6d33a6ab2f8445a01ccbf4748daf83
branch: chore/stage-176-s-workflow-defects
worktrees: 1
r_c3b:
  before: DISPUTED_NOT_ASSUMED
  after: DECIDED
  outcome: "early return: the first read-limit ReadErrorCode, UNRESOLVED / 2"
  rejected: "continue after a read-limit error and let a later completed disagreeing recheck report INPUT_CHANGED_DURING_RESOLUTION"
im_16: {decision: decided, tests: "implementation obligation (Phase 2, P-002/P-004), carried into the rebaselined plan", proof_c_rerun_needed: false}
im_03: {finality: "freezable; remaining obligation is the IM-16 tests at implementation, not a further decision"}
od_10: closed
new_reason_codes: []
new_reducer_classes: []
new_states: []
new_exit_codes: []
schema_changed: false
ratified_candidate_changed: false
public_contract_change: false
public_contract_note: "No code, class, state, exit or schema changes. The decision fixes, before the contract is frozen, which of two existing UNRESOLVED / 2 codes is reported, and bounds the resolver's reads after a read-limit error"
matrix_row_counts:
  total: 40
  met: 30
  met_conditional: 0
  open_evidence: 0
  unsatisfied: 0
  windows_met_linux_pending: 7
  deferred_to_implementation_matrix: 3
rows_changed: []
proof_verdicts_changed: false
proof_run_performed: false
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
backlog_item_created: false
plan_changed: false
implementation_ready: false
authorizes: none
promoted_to: none
tags:
  - read-budget
  - file-count-limit
  - reducer
  - reason-taxonomy
  - resolver-contract
  - ship-lifecycle
---

# R-C3b decided: stop at the first read-limit error

## Bottom Line

| Question | Answer |
|---|---|
| What is decided? | **Early return.** On the first read-limit error, the resolver issues **no further read or recheck request** and returns `UNRESOLVED / 2` with that `ReadErrorCode` as `reason_code` |
| Does class 1 still beat class 1b? | **Yes, for what was already observed.** A recheck that **completed with a disagreement before** the first read-limit error gives `INPUT_CHANGED_DURING_RESOLUTION`, as Decision 2 item 2 says |
| What about R-C3b's variant (read-limit error first, a later recheck disagrees)? | **It cannot happen, by construction.** No recheck runs after a read-limit error, so the outcome is the read-limit code |
| Is it safe? | Both outcomes are `UNRESOLVED / 2`. Neither can give `NO_HARNESS` or `HARNESS_READY`. Decision 2 items 1 to 3 are untouched |
| What changes in the contract? | **No code, class, state, exit or schema.** The OD-11-ratified 47-code list and its precedence stand |
| Who decided? | The **Orchestrator**, under the operator's explicit assignment. **Stage records it.** The operator may veto it |
| What remains? | The **tests of both orders** (IM-16), as implementation tests in Phase 2. They are not a new proof run |
| Effect | R-C3b `DISPUTED_NOT_ASSUMED` to **`DECIDED`**. **OD-10 closed.** **IM-16 decided.** **IM-03 can be frozen** once the tests exist. **No row status changes** |

## Context

### The Question

R-C3b comes from Proof C run 4 (`4c6e2701`). IM-16 in the refresh report
(`a04dea18`) states it: "A read-limit error occurs first, and a later recheck
completes with a disagreement. Does the resolver report the read-limit code
(early return) or `INPUT_CHANGED_DURING_RESOLUTION`? Both are
`UNRESOLVED / 2`, and only the reason code differs."

A **read-limit error** is a `ReadErrorCode` of `FILE_COUNT_LIMIT`,
`TOTAL_SIZE_LIMIT` or `FILE_SIZE_LIMIT` (Decision 2 of
`docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`,
`286aa4af`).

### Why It Was Open

Two items of that Decision 2 meet here, and neither settles the case:

* **Item 2** puts class 1b (read-limit error) directly after class 1
  (mutation) and says: "A disagreement already observed on a completed
  recheck still dominates as `INPUT_CHANGED_DURING_RESOLUTION`, unchanged."
* **Item 5** says: "Whether the resolver issues further requests after the
  first read-limit error is not decided here, except that it cannot change
  the class, the exit code or the reason code."

So the order of classes 1 and 1b was fixed, but not whether a recheck could
still run, and complete, after a read-limit error. The refresh report put it
the same way under `PE-DATA-01`: "What is undecided is whether the recheck
runs at all after a read-limit error (Decision 2 items 2 and 5)."

Proof C run 4 kept the case apart and assumed neither answer:
`"read_limit_first_variant":"FILE_COUNT_LIMIT"`,
`"later_completed_recheck_O":"INPUT_CHANGED_DURING_RESOLUTION"`,
`"status":"DISPUTED_NOT_ASSUMED"`. Charter section 6.5 does not decide it.
Its class 1b rule covers only the first occurrence among the three read-limit
codes.

### Route and Assignment

* The refresh report opened OD-10: "Rule on R-C3b (Decision 2 items 2 and 5),
  or route it to an architecture decision".
* The third rulings record (`347771bd`) recorded the operator's answer,
  "Refer to architecture decision". The form, an amendment of Decision 2 or a
  new record, was left to that decision.
* The fourth rulings record (`b8a7b100`) ratified the 47-code list (OD-11),
  closed IM-17, and left IM-03's finality depending only on IM-16.
* At **2026-09-25T18:12:40-07:00** the operator ruled, verbatim:

  > OD-10: I'm assigning you the architecture decision.

  "You" is the Orchestrator. The Orchestrator made the decision below. Stage
  records it as a new record, which the `347771bd` route allows. Stage does
  not edit the 2026-09-24 decision or the charter.

## Decision

### 1. Early Return on the First Read-Limit Error

When the resolver gets its **first** read-limit error, it stops. This holds
at any `ReadStage` and is judged in deterministic generation order.

* It issues **no further read request and no further recheck request.**
* It returns **`UNRESOLVED / 2`**, with that `ReadErrorCode` as
  `reason_code`.
* The diagnostics keep the native `ReadErrorCode` and the `ReadStage`, as
  Decision 2 item 4 requires.

The `ReadStage` values are those listed in Decision 2 item 1: shipment queue
or archive candidate, member queue or archive candidate, manifest read,
template read, installed-file read, candidate ledger recheck, and surface
recheck.

This closes, **for the resolver**, the part that Decision 2 item 5 left open.
It also keeps item 5's limit: the class, the exit code and the reason code are
the ones Decision 2 items 1, 2 and 4 already give.

### 2. Class 1 Dominates Only What Was Already Observed

* A recheck that **completed** with a disagreement **before** the first
  read-limit error, in deterministic generation order, gives
  **`INPUT_CHANGED_DURING_RESOLUTION` (class 1)**. This is Decision 2 item 2,
  unchanged.
* Because of early return, **no recheck can complete after a read-limit
  error.** So the R-C3b variant, a read-limit error first and then a later
  completed disagreeing recheck, **cannot be reached by construction.** The
  resolver's outcome is the read-limit code.

**What "completed" means (Stage refinement, consistent with the decision).**
A recheck is one recheck request, which Decision 1 of the 2026-09-24 decision
counts as "a new non-refundable claim". It completes when its read returns
bytes or stable absence and the comparison with the earlier observation is
made. A recheck whose own read ends in a read-limit error has **not**
completed. Decision 2 item 3 already says it is never treated as agreement.
Under this decision it is not treated as a disagreement either: it is the
first read-limit error, and the result is that `ReadErrorCode`.

### 3. What Stays the Same

* **Classes, codes and states.** No new reason code, reducer class, state or
  exit code. No schema change. The OD-11-ratified candidate (charter
  section 6.5, hash-pinned at `52c985cb` and byte-identical at `e65887d8`)
  and the governing reason set are unchanged.
* **Precedence.** Class 1, then 1b, then 2 to 8. It stays a strict total
  order apart from class 1b's first-occurrence rule.
* **Class 1b first occurrence.** Unchanged. Under early return, a second
  read-limit error is never produced by the resolver, so "the one that
  occurred first" is always the only one. The charter 6.5 pass check "Two
  read-limit errors, injected in both orders, yield the first-occurring code"
  still holds for the reducer.
* **Safety.** Decision 2 items 1 to 3 are untouched. A read-limit error is
  never recorded as stable absence and never classifies a surface. It never
  gives `NO_HARNESS / 1` or `HARNESS_READY / 0`.
* **Other callers.** This decision covers the harness-surface resolver only.
  It decides nothing about any other reader's behavior after a read-limit
  error.

## Rationale

1. **The bound means stop.** A read-limit error means the read budget or a
   read bound is exhausted or violated. Reading on defeats the purpose of the
   bound. For `FILE_COUNT_LIMIT` and `TOTAL_SIZE_LIMIT`, a later recheck
   would need reads beyond a budget that is already exhausted: every recheck
   is a new non-refundable claim, and each regular-file read reserves bytes
   that are never refunded (Decision 1 and "Byte budget" of the 2026-09-24
   decision). So continuing is possible, if at all, only after
   `FILE_SIZE_LIMIT`. Early return is the only rule that is the same for all
   three codes.
2. **Safety is identical.** Both candidate outcomes are `UNRESOLVED / 2`.
   Neither can give `NO_HARNESS` or `HARNESS_READY`. Decision 2 items 1 to 3
   are untouched. The choice is about which reason is reported, not about
   whether the result is safe.
3. **The stable cause is more useful.** A read-limit condition is
   deterministic and recurs on a rerun over the same inputs.
   `INPUT_CHANGED_DURING_RESOLUTION` invites a retry, and the retry would hit
   the same limit. Reporting the read-limit code tells the operator what to
   fix.
4. **Bounded, predictable I/O and a smaller test surface.** Nothing is read
   after the first read-limit error. The implementation and its tests are
   simpler. The precedence stays a strict total order apart from class 1b's
   first-occurrence rule, which Proof C run 4 proved (criterion 3).
5. **Nothing new.** No code, class, state or exit is added. The 47-code list
   and precedence ratified under OD-11 (`b8a7b100`) are unchanged, as
   `b8a7b100` expected: "the OD-10 decision cannot add or remove a code".

## Rejected Alternative

| Alternative | Why rejected |
|---|---|
| **Continue after a read-limit error**, and let a later recheck that completes with a disagreement report `INPUT_CHANGED_DURING_RESOLUTION` | It spends reads past a bound that is already exhausted. It can work only after `FILE_SIZE_LIMIT`, because a recheck after `FILE_COUNT_LIMIT` or `TOTAL_SIZE_LIMIT` needs budget that no longer exists, so it cannot be one rule for all three codes. It reports a less useful code, since a retry hits the same limit. It gains no safety: both outcomes are `UNRESOLVED / 2` |

## Tests Required (IM-16, "test both orders")

These tests belong to the resolver implementation's own test suite. They are
Phase 2 build work under P-002 and P-004 (a failing test first, then the
implementation). They are **not** a new proof run. They are carried into the
rebaselined plan and the implementation matrix as IM-16's remaining
obligation.

| Test | Arrangement | Required result |
|---|---|---|
| **(a) Disagreement first** | A recheck completes with a disagreement. A read-limit error comes later in generation order | `INPUT_CHANGED_DURING_RESOLUTION`, `UNRESOLVED / 2` |
| **(b) Read-limit error first** | A read-limit error occurs first. The fixture is arranged so that a later recheck **would** disagree if it ran | The read-limit `ReadErrorCode`, `UNRESOLVED / 2`, with the native `ReadErrorCode` and `ReadStage` in the diagnostics. **And** the test asserts that **zero** read or recheck requests are issued after the first read-limit error |

**Coverage.** Test (b) covers each of the three read-limit codes. It covers
each `ReadStage` where that is feasible, for example by counting or
recording requests through the read-budget seam. A stage at which a given
code cannot be arranged is recorded as infeasible, with the reason. Test (a)
covers at least one read-limit code after a completed disagreeing ledger
recheck and one after a completed disagreeing surface recheck, where both
recheck kinds exist in the implementation.

**No Proof C re-run.** `b8a7b100` left open whether this decision needs a
Proof C re-run beyond the tests of both orders. It does not:

* Proof C run 4 reported R-C3b outside the section 6.5 pass list, did not
  count it as a failure and assumed neither answer.
* Its early-return variant already gives the outcome chosen here
  (`FILE_COUNT_LIMIT`).
* Its oracle value `later_completed_recheck_O`
  (`INPUT_CHANGED_DURING_RESOLUTION`) describes a set of observations that
  the resolver can no longer produce. It is not adopted as contract. The
  frozen fixture and its scratch evidence are not edited (OD-6).
* The list, classes and precedence it proved are unchanged.

## Consequences

| Item | Before (`b8a7b100`) | Now |
|---|---|---|
| R-C3b | `DISPUTED_NOT_ASSUMED` | **`DECIDED`** (early return) |
| OD-10 | Routed to an architecture decision; the decision was open | **Closed** by this record |
| IM-16 | Not ratified. Open on OD-10 | **Decided.** The tests of both orders stay an implementation obligation and are carried into the rebaselined plan |
| IM-03 (resolver result contract) | Ratified as proof-backed. Finality open on IM-16 | **Final and freezable.** Its remaining obligation is the IM-16 tests at implementation, not a further decision |
| Resolver contract or API freeze | Blocked on OD-10's decision and tests of both orders | **No decision blocks it.** The IM-16 tests must exist and pass in the implementation |
| Decision 2 item 5 (2026-09-24) | Open on further requests after a read-limit error | **Closed for the resolver** by this record. The 2026-09-24 file is not edited |
| Charter, ratified candidate, Proof C evidence | Unchanged | **Unchanged** |

The rebaselined plan and the implementation matrix drafted for Phase 2 must
carry: the early-return rule, the class 1 rule for an already observed
disagreement, the meaning of "completed" above, and the IM-16 tests.

## Row-Status Consequences

**No row status changes.** OD-10 and IM-16 condition IM-03's finality, not a
proof-entry row (`a04dea18`, OD-10 row; `347771bd`; `b8a7b100`). `PE-DATA-01`
and `PE-DATA-02` were already `MET`, and their pass criteria never depended on
R-C3b.

Counts, checked against the `b8a7b100` table:

| Status | Rows |
|---|---|
| `MET` | 30 |
| `MET-COND` | 0 |
| `OPEN-EVIDENCE` | 0 |
| `UNSATISFIED` | 0 |
| `WIN-MET / LINUX-PENDING` | 7 (SAFETY-01, 02, 03, 04, 05, 07, EVIDENCE-02) |
| `DEFERRED` | 3 (INTERFACE-01, TASK-02, ACTIVATE-02) |
| **Total** | **40** |

This commit adds one `docs/decisions/` file and nothing else. So
`PE-ACTIVATE-01` (template, mirror, manifest and config blobs as at
`08787a4b`) and `PE-SCOPE-01` to `07` (no plan, review, shipment or lock file
change, and no harvest) are unaffected. The 7 Linux-`PENDING` rows stay
pending until IM-01 runs on Linux. No one can waive that gate.

## Remaining Open Items

| Item | Status | Affects |
|---|---|---|
| IM-16 tests of both orders | Implementation obligation, Phase 2 (P-002/P-004) | IM-03 freeze in practice |
| Operator veto of this decision | Open. If vetoed, R-C3b returns to `DISPUTED_NOT_ASSUMED` and IM-03's finality again depends on IM-16 | R-C3b, IM-16, IM-03 |
| Section 9 governance defaults | Need ratification before the next review epoch opens, except the `P2` publication rule (`347771bd`) | Review epoch |
| Linux-native run (IM-01) | Not executed. Non-waivable | 7 Linux-`PENDING` rows |
| `187-S` retirement mechanics (C3) | Approved, not executed; to be checked against the installed backlogit version, never as a Ship claim | Phase 2 re-slice |
| IM-10 reconciliation of the `harness-architect` render mismatch (stash `9144435A`) | Needs triage and its own release unit | IM-10 |
| Scratch cleanup | Withheld under OD-6 | Hygiene |
| Publication | Not ready. Pushing is an operator action | Publication |

## Scope and Method

* **Actor.** Stage, directed by the Orchestrator, wrote this one file. It ran
  no proof, fixture, build, test suite or linter other than a Markdown lint
  of this file. It made no push, branch, worktree or pull request, and did
  not touch any `git stash` entry. It did not read or touch `187-S`.
* **Sources read.** The 2026-09-24 read-budget decision (`286aa4af`), charter
  section 6.5 (`e65887d8`), the Proof C run 4 findings (`4c6e2701`), the
  refresh report (`a04dea18`: IM-03, IM-16, OD-10, `PE-DATA-01`), and the
  third and fourth rulings records (`347771bd`, `b8a7b100`). No source makes
  the decision unsafe or contradicts it.
* **Session state.** backlogit MCP `get_version` (update check skipped)
  returned `1.10.1-0.20260823032255-b07729386a31+dirty` (`TOOL_OK`). Index
  sync was not run, as in the earlier addenda (`INDEX_SYNC_SKIPPED`).
  Checkpoint recovery: `list_checkpoints` with `consumer_id: stage` and no
  status or agent filter returned 67 records, all `stage`/`resolved`, with
  `needs_quarantine` 0 and `quarantined` 0, which is a normal zero-candidate
  startup. The host tool wrapper spooled that read-only output to OS Temp;
  Stage read it read-only. Engram, intercom and graphtor-docs expose no tools
  here (`ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`).

## What This Record Does Not Do

It does **not edit** the 2026-09-24 decision, the charter, the Proof C
evidence or any earlier record. It **authorizes no** plan, plan revision,
harvest, backlog item, shipment change, `187-S` retirement step, review
epoch, activation, claim, configuration change, proof run, implementation,
scratch cleanup, push or pull request. It **does not ratify** the section 9
defaults. `187-S` stays `queued` and frozen until Phase 2 is routed.

## References

* `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md` (`286aa4af`), Decision 1, "Byte budget", and Decision 2 items 1 to 5 (not edited)
* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md`, section 6.5 (`e65887d8`, PE-1.7; candidate at `52c985cb`, PE-1.4) (not edited)
* `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run4-spike.md` (`4c6e2701`), R-C3b note and Routing item 2
* `docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md` (`a04dea18`), IM-03, IM-16, OD-10 and `PE-DATA-01`
* `docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-3.md` (`347771bd`), "OD-10: The Route for R-C3b"
* `docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-4.md` (`b8a7b100`), "Consequences" and "Updated Counts"
* `.github/policies/workflow-policies.md` (P-002, P-004, P-010)
